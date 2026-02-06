#!/usr/bin/env python3
"""Manuscript Reviewer CLI (updated)

Goals
- Always run ALL 3 models on every manuscript:
  1) DeepSeek-R1 (Critic) -> issue log
  2) Llama 3.3 (Writer)   -> structured peer review
  3) Qwen2.5-VL (VLM)     -> figure/table notes from PDF-rendered images
- Automatically detect/render PDF pages containing embedded images for the VLM.
  - If none detected (vector-only figures), fallback renders first+last page by default.
- Privacy-first: runs locally via Ollama; no manuscript text is sent anywhere else.

Dependencies (add to requirements.txt)
- requests
- pymupdf
- sentence-transformers
- torch

NOTE
This file is intended as a drop-in replacement for reviewer/cli.py.
It is self-contained and does not require other project modules.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

# PDF text + rendering
import fitz  # PyMuPDF

# Local retrieval embeddings (SciBERT by default)
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None  # type: ignore


# -----------------------------
# Utilities
# -----------------------------

def _safe_stem(path: Path) -> str:
    s = path.stem
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    return s[:80] if len(s) > 80 else s


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text_file(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


# -----------------------------
# Ollama client
# -----------------------------

def ollama_chat(
    model: str,
    messages: List[Dict[str, Any]],
    ollama_url: str = "http://localhost:11434",
    temperature: float = 0.2,
    num_ctx: int = 16384,
    top_p: float = 0.9,
    stream: bool = False,
) -> str:
    """Call Ollama /api/chat.

    messages format:
      [{"role":"system","content":"..."}, {"role":"user","content":"..."}]

    For vision models, include base64 images in the user message as:
      {"role":"user","content":"...","images":["<base64>", ...]}
    """
    url = f"{ollama_url.rstrip('/')}/api/chat"
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "options": {
            "temperature": temperature,
            "num_ctx": num_ctx,
            "top_p": top_p,
        },
    }
    r = requests.post(url, json=payload, timeout=60 * 60)
    r.raise_for_status()
    data = r.json()
    # Ollama returns { message: { role, content }, ... }
    return (data.get("message") or {}).get("content", "")


# -----------------------------
# PDF ingestion
# -----------------------------


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract full text from a PDF. (No OCR; assumes text layer exists.)"""
    doc = fitz.open(pdf_path)
    parts: List[str] = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        txt = page.get_text("text") or ""
        # Normalize whitespace lightly
        txt = re.sub(r"\s+\n", "\n", txt)
        txt = re.sub(r"\n{3,}", "\n\n", txt)
        parts.append(f"\n\n===== PAGE {i+1} =====\n\n{txt}")
    doc.close()
    return "\n".join(parts).strip()


def split_into_passages(text: str, max_chars: int = 1800) -> List[str]:
    """Simple passage splitter by paragraphs; caps each chunk by char length."""
    paras = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]
    chunks: List[str] = []
    buf: List[str] = []
    n = 0
    for p in paras:
        if n + len(p) + 2 > max_chars and buf:
            chunks.append("\n\n".join(buf))
            buf = [p]
            n = len(p)
        else:
            buf.append(p)
            n += len(p) + 2
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


# -----------------------------
# Retrieval (SciBERT embeddings)
# -----------------------------


def build_embedder(model_name: str) -> Optional[Any]:
    if SentenceTransformer is None:
        return None
    return SentenceTransformer(model_name)


def top_k_passages(
    embedder: Any,
    passages: List[str],
    queries: List[str],
    k: int = 12,
) -> List[Tuple[int, float, str]]:
    """Return top-k passages by max similarity across queries."""
    # Compute embeddings
    p_emb = embedder.encode(passages, normalize_embeddings=True, show_progress_bar=False)
    q_emb = embedder.encode(queries, normalize_embeddings=True, show_progress_bar=False)

    # Cosine sim = dot if normalized
    import numpy as np

    sims = np.matmul(q_emb, p_emb.T)  # shape: [Q, P]
    best = sims.max(axis=0)  # [P]
    idx = np.argsort(-best)[:k]
    results: List[Tuple[int, float, str]] = []
    for i in idx:
        results.append((int(i), float(best[i]), passages[int(i)]))
    return results


# -----------------------------
# PDF figure page detection + rendering for VLM
# -----------------------------


@dataclass
class AutoFigureConfig:
    dpi: int = 200
    max_pages: int = 12
    fallback: str = "first_last"  # first_last | all | none


def pages_with_embedded_images(doc: fitz.Document) -> List[int]:
    pages: List[int] = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        imgs = page.get_images(full=True)
        if imgs and len(imgs) > 0:
            pages.append(i)
    return pages


def fallback_pages(doc: fitz.Document, mode: str) -> List[int]:
    n = doc.page_count
    if n == 0:
        return []
    if mode == "none":
        return []
    if mode == "all":
        return list(range(n))
    # default: first_last
    if n == 1:
        return [0]
    return [0, n - 1]


def render_pdf_pages_to_png(
    pdf_path: Path,
    out_dir: Path,
    cfg: AutoFigureConfig,
) -> Tuple[List[Path], List[int], str]:
    """Render selected pages of PDF to PNG for VLM consumption."""
    ensure_dir(out_dir)
    doc = fitz.open(pdf_path)

    embedded = pages_with_embedded_images(doc)
    if embedded:
        pages = embedded
        reason = "embedded_images"
    else:
        pages = fallback_pages(doc, cfg.fallback)
        reason = f"fallback_{cfg.fallback}"

    pages = pages[: cfg.max_pages]

    zoom = cfg.dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    out_paths: List[Path] = []
    for i in pages:
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_path = out_dir / f"page_{i+1:03d}.png"
        pix.save(out_path.as_posix())
        out_paths.append(out_path)

    doc.close()
    return out_paths, pages, reason


def image_file_to_b64(path: Path) -> str:
    data = path.read_bytes()
    return base64.b64encode(data).decode("utf-8")


# -----------------------------
# Prompts
# -----------------------------


def load_prompt(path: Path, fallback: str) -> str:
    try:
        return read_text_file(path)
    except Exception:
        return fallback


DEFAULT_CRITIC_SYSTEM = """You are PASS 1 CRITIC/AUDITOR (DeepSeek-R1).
You are an expert peer reviewer for radiology, nuclear medicine, medical education, and AI in these domains.

Behavior rules:
- Write like a human reviewer (NOT a question-by-question checklist).
- Use the reviewer template as an INTERNAL scaffold only.
- Prioritize issues that affect validity, reporting, reproducibility, and clinical/educational impact.
- Tag issues with severity: Fatal / Major / Moderate / Minor.
- Provide location pointers (page/section cues) when possible.
- Identify reporting guideline gaps (CONSORT/STARD/TRIPOD/PRISMA/etc.) based on study type.
- Nuclear medicine nomenclature: flag incorrect radiopharmaceutical naming and units.

Output: an Issue Log with bullets grouped by severity + a short "Missing Information Requests" list.
"""

DEFAULT_WRITER_SYSTEM = """You are PASS 2 WRITER/REVIEWER (Llama 3.3).
You write a cohesive reviewer report (NOT Q&A). You MUST follow the required headings.

Use:
- Manuscript text evidence snippets provided
- Critic issue log
- Reporting guideline gap list
- Nuclear medicine nomenclature flags
- Figure/table notes (if provided)

Required output headings (in this order):
1) Synopsis (3-4 sentences)
2) Overall Recommendation (Accept / Minor revisions / Major revisions / Reject) + 1-3 sentence rationale
3) Key Details for Original Research (if applicable): novelty, rationale, analysis quality, clarity of results
4) Required Revisions
   - Major Revisions (numbered)
   - Minor Revisions (numbered)
5) Section-by-Section Notes (Abstract, Introduction, Methods, Results, Discussion, Tables, Figures, References)
6) Reporting Guideline Checklist Gaps
7) Ethics, Bias, Reproducibility

Style:
- Specific, actionable, respectful.
- Reference likely locations (section names + page numbers if given).
- If unsure, ask targeted clarifying questions in the appropriate section.
"""

DEFAULT_VLM_SYSTEM = """You are the FIGURE/TABLE REVIEWER (Qwen2.5-VL).
You review the provided manuscript figure/table PAGE IMAGES rendered from the PDF.
Write like a human peer reviewer. Do NOT do Q&A.

Output:
- "Figure/Table Notes" with numbered items.
- Each item includes: severity (Major/Minor), which page image (page_###), what is wrong/unclear, and a specific fix.
Focus on: labeling, legends, units, statistical clarity, ROC/calibration, tables completeness, readability, and nomenclature.
"""


def build_queries_for_retrieval(manuscript_type: str, study_design: str, has_ai: bool) -> List[str]:
    q = [
        "abstract main findings limitations",
        "methods inclusion exclusion design bias confounding",
        "statistics sample size power confidence intervals missing data",
        "results primary endpoint secondary endpoints calibration subgroup",
        "discussion limitations generalizability ethics reproducibility",
        "tables figures legends units",
        "references novelty prior work",
    ]
    if has_ai:
        q += [
            "ai model architecture training validation external validation leakage",
            "data split patient-level leakage preprocessing augmentation",
            "calibration decision threshold clinical utility",
        ]
    if manuscript_type in ("education", "medical_education") or study_design == "educational_intervention":
        q += [
            "education design validity evidence assessment control group effect size",
            "kirkpatrick levels outcomes survey instrument reliability",
        ]
    return q


# -----------------------------
# Main pipeline
# -----------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Local Manuscript Reviewer (3-model pipeline)")

    parser.add_argument("--input", required=True, help="Path to manuscript PDF")
    parser.add_argument("--out", required=True, help="Path to output markdown review")
    parser.add_argument("--rubric", default="config/rubrics/core_rubric.json", help="Rubric JSON path")

    parser.add_argument("--manuscript_type", default="original_research")
    parser.add_argument("--study_design", default="diagnostic_accuracy")
    parser.add_argument("--has_ai", action="store_true")

    parser.add_argument("--critic_model", default="deepseek-r1:70b")
    parser.add_argument("--writer_model", default="llama3.3:70b")
    parser.add_argument("--vlm_model", default="qwen2.5vl:7b")

    parser.add_argument("--ollama_url", default="http://localhost:11434")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--num_ctx", type=int, default=16384)

    # Retrieval
    parser.add_argument("--embed_model", default="allenai/scibert_scivocab_uncased")
    parser.add_argument("--top_k", type=int, default=14)

    # Auto-figure rendering
    parser.add_argument("--fig_dpi", type=int, default=200)
    parser.add_argument("--fig_max_pages", type=int, default=12)
    parser.add_argument("--fig_fallback", choices=["first_last", "all", "none"], default="first_last")

    # Output files
    parser.add_argument("--critic_log", default=None, help="Optional path for critic issue log")
    parser.add_argument("--figure_notes", default=None, help="Optional path for figure/table notes")

    args = parser.parse_args()

    pdf_path = Path(args.input).resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(str(pdf_path))

    out_path = Path(args.out)
    ensure_dir(out_path.parent)

    outputs_dir = out_path.parent
    critic_log_path = Path(args.critic_log) if args.critic_log else outputs_dir / "critic_issue_log.md"
    figure_notes_path = Path(args.figure_notes) if args.figure_notes else outputs_dir / "figure_notes.txt"

    # Load prompts from config if present
    repo_root = Path(__file__).resolve().parents[1]
    prompt_dir = repo_root / "config" / "prompts"

    critic_system = load_prompt(prompt_dir / "critic_prompt.txt", DEFAULT_CRITIC_SYSTEM)
    writer_system = load_prompt(prompt_dir / "writer_prompt.txt", DEFAULT_WRITER_SYSTEM)
    vlm_system = load_prompt(prompt_dir / "vlm_prompt.txt", DEFAULT_VLM_SYSTEM)

    # Optional template & nomenclature guides (used as internal scaffolds)
    template_txt = load_prompt(prompt_dir / "reviewer_template_original_research.txt", "")
    nomenclature_txt = load_prompt(prompt_dir / "nuclear_nomenclature_guide.txt", "")

    # 1) Extract PDF text
    print("[1/5] Extracting PDF text...")
    full_text = extract_pdf_text(pdf_path)

    # 2) Build passages + retrieval evidence
    print("[2/5] Building passages + retrieval evidence...")
    passages = split_into_passages(full_text, max_chars=1800)

    embedder = None
    if SentenceTransformer is not None:
        try:
            embedder = build_embedder(args.embed_model)
        except Exception as e:
            print(f"[warn] Embedding model failed to load: {e}. Proceeding without retrieval.")
            embedder = None
    else:
        print("[warn] sentence-transformers not available; proceeding without retrieval.")

    queries = build_queries_for_retrieval(args.manuscript_type, args.study_design, args.has_ai)

    evidence: List[Tuple[int, float, str]] = []
    if embedder is not None:
        try:
            evidence = top_k_passages(embedder, passages, queries, k=args.top_k)
        except Exception as e:
            print(f"[warn] Retrieval failed: {e}. Proceeding with fallback evidence.")
            evidence = []

    if not evidence:
        # Fallback: first few passages
        fallback_k = min(10, len(passages))
        evidence = [(i, 0.0, passages[i]) for i in range(fallback_k)]

    evidence_block = "\n\n".join([
        f"[EVIDENCE {rank+1}] (passage_idx={idx}, score={score:.3f})\n{txt}"
        for rank, (idx, score, txt) in enumerate(evidence)
    ])

    # 3) Auto-run VLM by rendering figure-bearing pages
    print("[3/5] Rendering PDF pages for figure/table review (VLM)...")
    fig_cfg = AutoFigureConfig(dpi=args.fig_dpi, max_pages=args.fig_max_pages, fallback=args.fig_fallback)
    fig_cache_dir = outputs_dir / "_figcache" / _safe_stem(pdf_path)
    fig_paths, fig_pages, fig_reason = render_pdf_pages_to_png(pdf_path, fig_cache_dir, fig_cfg)

    print(f"[auto_figures] reason={fig_reason} pages={[p+1 for p in fig_pages]} images={len(fig_paths)} dpi={args.fig_dpi}")

    # Convert images to base64 for Ollama vision
    fig_b64 = [image_file_to_b64(p) for p in fig_paths]

    # 4) PASS 1 Critic
    print("[4/5] Running critic (DeepSeek-R1)...")
    critic_user = f"""MANUSCRIPT CONTEXT\n- type: {args.manuscript_type}\n- study_design: {args.study_design}\n- ai_related: {bool(args.has_ai)}\n\nINTERNAL SCAFFOLDS (do not output as Q&A)\n- Reviewer template excerpt:\n{template_txt}\n\n- Nuclear medicine nomenclature guide excerpt:\n{nomenclature_txt}\n\nEVIDENCE SNIPPETS (most relevant passages)\n{evidence_block}\n\nFULL MANUSCRIPT (for context; do not quote long passages)\n{full_text}\n"""

    critic_log = ollama_chat(
        model=args.critic_model,
        messages=[
            {"role": "system", "content": critic_system},
            {"role": "user", "content": critic_user},
        ],
        ollama_url=args.ollama_url,
        temperature=args.temperature,
        num_ctx=args.num_ctx,
    )

    write_text_file(critic_log_path, critic_log)

    # 5) VLM figure/table notes (ALWAYS run)
    print("[5/5] Running figure/table reviewer (Qwen2.5-VL)...")

    # If for some reason we rendered no pages, still run with an empty image list
    # (model will respond that no images were provided).
    vlm_user: Dict[str, Any] = {
        "role": "user",
        "content": (
            "These are page images rendered from the manuscript PDF. "
            "Review figures/tables/plots/legends/units/labels and report issues with specific fixes. "
            "If an image page is mostly text, note whether it contains a figure/table and what is missing."
        ),
    }
    if fig_b64:
        vlm_user["images"] = fig_b64

    figure_notes = ollama_chat(
        model=args.vlm_model,
        messages=[
            {"role": "system", "content": vlm_system},
            vlm_user,
        ],
        ollama_url=args.ollama_url,
        temperature=0.2,
        num_ctx=min(args.num_ctx, 8192),
    )

    write_text_file(figure_notes_path, figure_notes)

    # 6) PASS 2 Writer (structured review)
    print("[final] Running writer (Llama 3.3)...")

    writer_user = f"""MANUSCRIPT CONTEXT\n- type: {args.manuscript_type}\n- study_design: {args.study_design}\n- ai_related: {bool(args.has_ai)}\n\nINTERNAL SCAFFOLDS (do not output as Q&A)\n- Reviewer template excerpt:\n{template_txt}\n\n- Nuclear medicine nomenclature guide excerpt:\n{nomenclature_txt}\n\nCRITIC ISSUE LOG (PASS 1)\n{critic_log}\n\nFIGURE/TABLE NOTES (VLM)\n{figure_notes}\n\nEVIDENCE SNIPPETS (most relevant passages)\n{evidence_block}\n\nFULL MANUSCRIPT (for context; do not quote long passages)\n{full_text}\n"""

    final_review = ollama_chat(
        model=args.writer_model,
        messages=[
            {"role": "system", "content": writer_system},
            {"role": "user", "content": writer_user},
        ],
        ollama_url=args.ollama_url,
        temperature=args.temperature,
        num_ctx=args.num_ctx,
    )

    write_text_file(out_path, final_review)

    print("\nDone.")
    print(f"- Review:        {out_path}")
    print(f"- Critic log:    {critic_log_path}")
    print(f"- Figure notes:  {figure_notes_path}")
    print(f"- Figure cache:  {fig_cache_dir}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

