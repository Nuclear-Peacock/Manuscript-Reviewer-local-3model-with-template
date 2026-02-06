import re
import subprocess
from datetime import datetime
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent
PRIVATE_DIR = REPO_ROOT / "private_inputs"
OUTPUTS_DIR = REPO_ROOT / "outputs"

DEFAULT_RUBRIC = "config/rubrics/core_rubric.json"

MODEL_PRESETS = {
    "Best (max quality; very large)": {
        "critic": "deepseek-r1:70b",
        "writer": "llama3.3:70b",
        "vlm": "qwen2.5vl:7b",
        "num_ctx": 16384,
    },
    "Balanced (recommended)": {
        "critic": "deepseek-r1:32b",
        "writer": "llama3.3:70b",
        "vlm": "qwen2.5vl:7b",
        "num_ctx": 12288,
    },
    "Fast (smaller / most compatible)": {
        "critic": "deepseek-r1:14b",
        "writer": "llama3.1:8b",
        "vlm": "qwen2.5vl:7b",
        "num_ctx": 8192,
    },
}

MANUSCRIPT_TYPES = ["original_research", "education", "ai", "systematic_review", "other"]
STUDY_DESIGNS = ["diagnostic_accuracy", "prediction_model", "interventional", "educational_intervention", "systematic_review", "other"]


def safe_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:120] if len(name) > 120 else name


def save_upload(uploaded_file) -> Path:
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    original = safe_filename(uploaded_file.name)
    dest = PRIVATE_DIR / original
    if dest.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = PRIVATE_DIR / f"{dest.stem}_{stamp}{dest.suffix}"
    dest.write_bytes(uploaded_file.getbuffer())
    return dest


def read_text(p: Path) -> str:
    if p.exists():
        return p.read_text(encoding="utf-8", errors="ignore")
    return ""


def run_review(pdf_path: Path, out_md: Path, preset: dict, manuscript_type: str, study_design: str,
               has_ai: bool, fig_dpi: int, fig_max_pages: int, fig_fallback: str, temperature: float) -> int:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python", "-m", "reviewer.cli",
        "--input", str(pdf_path),
        "--out", str(out_md),
        "--rubric", DEFAULT_RUBRIC,
        "--manuscript_type", manuscript_type,
        "--study_design", study_design,
        "--critic_model", preset["critic"],
        "--writer_model", preset["writer"],
        "--vlm_model", preset["vlm"],
        "--num_ctx", str(preset["num_ctx"]),
        "--temperature", str(temperature),
        "--fig_dpi", str(fig_dpi),
        "--fig_max_pages", str(fig_max_pages),
        "--fig_fallback", fig_fallback,
    ]
    if has_ai:
        cmd.append("--has_ai")

    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    log_lines = []
    placeholder = st.empty()

    assert proc.stdout is not None
    for line in proc.stdout:
        log_lines.append(line.rstrip("\n"))
        placeholder.code("\n".join(log_lines[-220:]), language="text")

    return proc.wait()


st.set_page_config(page_title="Local Manuscript Reviewer", layout="wide")
st.title("Local Manuscript Reviewer")
st.caption("Local-only UI. Uploads saved to private_inputs/. Outputs saved to outputs/.")

left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("Upload manuscript PDF")
    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])

    st.subheader("Settings")
    preset_name = st.selectbox("Quality preset", list(MODEL_PRESETS.keys()), index=1)
    preset = MODEL_PRESETS[preset_name]

    manuscript_type = st.selectbox("Manuscript type", MANUSCRIPT_TYPES, index=0)
    study_design = st.selectbox("Study design", STUDY_DESIGNS, index=0)
    has_ai = st.checkbox("AI-related manuscript", value=True)

    st.subheader("Figures / tables (vision model)")
    fig_dpi = st.slider("Render DPI", 150, 300, 200, 10)
    fig_max_pages = st.slider("Max pages to render", 2, 40, 12, 1)
    fig_fallback = st.selectbox("If no embedded images detected, render:", ["first_last", "all", "none"], index=0)

    st.subheader("Output behavior")
    temperature = st.slider("Temperature", 0.0, 0.6, 0.2, 0.05)

    st.divider()
    run_btn = st.button("Run review", type="primary", use_container_width=True)

with right:
    st.subheader("Run log")
    st.info("You will see progress here (critic → figures → writer).")

    if run_btn:
        if not uploaded_pdf:
            st.error("Please upload a PDF first.")
            st.stop()

        pdf_path = save_upload(uploaded_pdf)
        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

        out_md = OUTPUTS_DIR / f"{pdf_path.stem}_review.md"
        critic_log = OUTPUTS_DIR / "critic_issue_log.md"
        figure_notes = OUTPUTS_DIR / "figure_notes.txt"

        st.write(f"Saved manuscript: `{pdf_path}`")
        st.write(f"Output review: `{out_md}`")

        rc = run_review(
            pdf_path=pdf_path,
            out_md=out_md,
            preset=preset,
            manuscript_type=manuscript_type,
            study_design=study_design,
            has_ai=has_ai,
            fig_dpi=fig_dpi,
            fig_max_pages=fig_max_pages,
            fig_fallback=fig_fallback,
            temperature=temperature,
        )

        if rc == 0:
            st.success("Review complete.")
        else:
            st.error(f"Review exited with code {rc}.")

        st.divider()
        st.subheader("Outputs")

        review_text = read_text(out_md)
        critic_text = read_text(critic_log)
        fig_text = read_text(figure_notes)

        tab1, tab2, tab3 = st.tabs(["Review", "Critic log", "Figure notes"])

        with tab1:
            if review_text:
                st.download_button("Download review.md", review_text, file_name=out_md.name, mime="text/markdown")
                st.text_area("Preview", review_text, height=450)
            else:
                st.info("No review output found.")

        with tab2:
            if critic_text:
                st.download_button("Download critic_issue_log.md", critic_text, file_name=critic_log.name, mime="text/markdown")
                st.text_area("Preview", critic_text, height=450)
            else:
                st.info("No critic log found.")

        with tab3:
            if fig_text:
                st.download_button("Download figure_notes.txt", fig_text, file_name=figure_notes.name, mime="text/plain")
                st.text_area("Preview", fig_text, height=450)
            else:
                st.info("No figure notes found.")

st.divider()
st.subheader("Previously uploaded PDFs (private_inputs/)")
PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
pdfs = sorted(PRIVATE_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
if not pdfs:
    st.caption("No PDFs yet.")
else:
    for p in pdfs[:30]:
        st.caption(f"- {p.name}")
