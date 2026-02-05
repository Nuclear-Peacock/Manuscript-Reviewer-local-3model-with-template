from __future__ import annotations
import argparse
from pathlib import Path
from rich import print
import json

from .ingest import load_manuscript
from .splitter import split_to_sentences
from .rubric import load_rubrics
from .bert_evidence import EvidenceExtractor, build_evidence_block
from .ollama import OllamaText, OllamaVLM
from .prompting import load_text, excerpt
from .novelty_search import novelty_bundle, format_novelty_block

def select_guidelines(study_design: str, has_ai: bool, is_education: bool) -> tuple[str, str]:
    m = json.loads(load_text("config/guidelines/equator_mapping.json"))
    item = m.get(study_design) or {"primary":"(unknown)", "extensions":[], "notes":[]}
    primary = item.get("primary")
    exts = list(item.get("extensions") or [])
    if has_ai and not any("AI" in x for x in exts):
        exts.append("AI/ML domains: splits/leakage, external validation, calibration, subgroup performance")
    if is_education and not any("Education" in x for x in exts):
        exts.append("Education overlay: learner level/context, outcomes framework, validity evidence, fidelity")
    selected = f"Primary: {primary}\nExtensions/Overlays: " + (", ".join(exts) if exts else "(none)")
    grid = "\n".join([
        "- Study design & participants: Present/Partial/Missing",
        "- Outcomes & reference standard: Present/Partial/Missing",
        "- Sample size & missing data: Present/Partial/Missing",
        "- Analysis/statistics: Present/Partial/Missing",
        "- AI specifics (if any): Present/Partial/Missing",
        "- Reproducibility: Present/Partial/Missing",
    ])
    return selected, grid

def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

def main() -> None:
    ap = argparse.ArgumentParser(description="Local 3-model reviewer: DeepSeek-R1 critic + Llama 3.3 writer + Qwen2.5-VL multimodal")
    ap.add_argument("--input", required=True, help="Manuscript PDF/DOCX/TXT")
    ap.add_argument("--rubric", required=True, action="append", help="Rubric JSON (repeatable)")
    ap.add_argument("--out", default="outputs/review.md")

    ap.add_argument("--manuscript_type", default="original_research")
    ap.add_argument("--study_design", default="diagnostic_accuracy")
    ap.add_argument("--domain", default="radiology/nuclear medicine/med ed/AI")
    ap.add_argument("--has_ai", action="store_true")
    ap.add_argument("--is_education", action="store_true")

    ap.add_argument("--embed_model", default="allenai/scibert_scivocab_uncased")
    ap.add_argument("--top_k", type=int, default=7)
    ap.add_argument("--max_sentences", type=int, default=30000)

    ap.add_argument("--critic_model", default="deepseek-r1:70b")
    ap.add_argument("--writer_model", default="llama3.3:70b")
    ap.add_argument("--vlm_model", default="qwen2.5-vl:7b")
    ap.add_argument("--ollama_url", default="http://localhost:11434")
    ap.add_argument("--num_ctx", type=int, default=16384)
    ap.add_argument("--temperature", type=float, default=0.2)

    ap.add_argument("--keywords", default="", help="Space-separated keywords (minimal disclosure)")
    ap.add_argument("--novelty_claim", default="", help="Paraphrased novelty claim")
    ap.add_argument("--dois", default="", help="Comma-separated DOIs/PMIDs")

    ap.add_argument("--figure_images", nargs="*", default=[], help="Figure/table image paths (png/jpg)")

    args = ap.parse_args()

    ms = load_manuscript(args.input)
    print(f"[green]Loaded[/green] {Path(args.input).name} units={len(ms.units)}")
    sents = split_to_sentences(ms.units, max_sentences=args.max_sentences)
    print(f"[green]Sentences[/green] n={len(sents)}")

    rubric = load_rubrics(args.rubric)
    extractor = EvidenceExtractor(model_name=args.embed_model)
    evidence = extractor.extract(sents, rubric=rubric, top_k=args.top_k)
    evidence_block = build_evidence_block(evidence)

    guidelines_selected, methods_grid = select_guidelines(args.study_design, args.has_ai, args.is_education)

    kw = [k for k in args.keywords.split() if k.strip()]
    keyrefs = [x.strip() for x in args.dois.split(",") if x.strip()]
    novelty_block = "(none)"
    if kw:
        bundle = novelty_bundle(kw)
        novelty_block = format_novelty_block(bundle, claimed_novelty=args.novelty_claim.strip() or None, key_refs=keyrefs or None)

    figure_notes = "(none)"
    if args.figure_images:
        vlm_prompt = load_text("config/prompts/vlm_prompt.txt")
        vlm = OllamaVLM(model=args.vlm_model, base_url=args.ollama_url, temperature=args.temperature, num_ctx=min(args.num_ctx, 8192))
        figure_notes = vlm.analyze_images(vlm_prompt, args.figure_images)

    nomen = load_text("config/prompts/nuclear_nomenclature_guide.txt")
    nomen_excerpt = excerpt(nomen, 1200)

    reviewer_template = load_text("config/prompts/reviewer_template_original_research.txt")
    reviewer_template_excerpt = excerpt(reviewer_template, 1600)

    intake = "\n".join([
        f"- Manuscript type: {args.manuscript_type}",
        f"- Study design: {args.study_design}",
        f"- Domain lens: {args.domain}",
        f"- AI component: {args.has_ai}",
        f"- Education component: {args.is_education}",
    ])

    canvas_core = load_text("config/prompts/canvas_core.txt")
    critic_tpl = load_text("config/prompts/critic_prompt.txt")
    writer_tpl = load_text("config/prompts/writer_prompt.txt")

    critic_prompt = critic_tpl.format(
        canvas_core=canvas_core,
        intake=intake,
        guidelines_selected=guidelines_selected,
        methods_grid=methods_grid,
        evidence=evidence_block,
        novelty_block=novelty_block,
        figure_notes=figure_notes,
        nomen_guide_excerpt=nomen_excerpt,
        reviewer_template_excerpt=reviewer_template_excerpt,
    )

    critic = OllamaText(model=args.critic_model, base_url=args.ollama_url, temperature=args.temperature, num_ctx=args.num_ctx, num_predict=3500)
    print("[yellow]Running PASS 1 critic...[/yellow]")
    issue_log = critic.generate(critic_prompt)

    writer_prompt = writer_tpl.format(
        canvas_core=canvas_core,
        intake=intake,
        issue_log=issue_log,
        guidelines_selected=guidelines_selected,
        novelty_block=novelty_block,
        figure_notes=figure_notes,
        reviewer_template_excerpt=reviewer_template_excerpt,
    )

    writer = OllamaText(model=args.writer_model, base_url=args.ollama_url, temperature=args.temperature, num_ctx=args.num_ctx, num_predict=3500)
    print("[yellow]Running PASS 2 writer...[/yellow]")
    review_md = writer.generate(writer_prompt)

    out_path = Path(args.out)
    ensure_dir(out_path)
    out_path.write_text(review_md, encoding="utf-8")

    # side artifacts
    out_dir = out_path.parent
    (out_dir/"critic_issue_log.md").write_text(issue_log, encoding="utf-8")
    (out_dir/"novelty_check.txt").write_text(novelty_block, encoding="utf-8")
    if args.figure_images:
        (out_dir/"figure_notes.txt").write_text(figure_notes, encoding="utf-8")

    print(f"[cyan]Wrote[/cyan] {out_path.resolve()}")

if __name__ == "__main__":
    main()
