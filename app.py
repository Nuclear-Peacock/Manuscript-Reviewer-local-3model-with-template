import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

import streamlit as st

# ==========================================================
# Local Manuscript Reviewer — Streamlit UI (Localhost Only)
# ==========================================================

REPO_ROOT = Path(__file__).resolve().parent
PRIVATE_DIR = REPO_ROOT / "private_inputs"
OUTPUTS_DIR = REPO_ROOT / "outputs"
DEFAULT_RUBRIC = "config/rubrics/core_rubric.json"

PHASES = [
    "Preparing",
    "Extracting text",
    "Checking figures/tables",
    "Critic pass (issues + questions)",
    "Writer pass (structured review)",
    "Saving outputs",
    "Done",
]

# ---------------------------
# Model presets (user-facing)
# ---------------------------
PRESETS = {
    "High quality, Low speed": {
        "help": "Best quality. Slowest and uses the most GPU/VRAM.",
        "critic": "deepseek-r1:70b",
        "writer": "llama3.3:70b",
        "vlm": "qwen2.5vl:7b",
        "num_ctx": 16384,
    },
    "Medium quality, Medium speed": {
        "help": "Recommended for most manuscripts (best overall balance).",
        "critic": "deepseek-r1:32b",
        "writer": "llama3.3:70b",
        "vlm": "qwen2.5vl:7b",
        "num_ctx": 12288,
    },
    "Low quality, High speed": {
        "help": "Fastest quick pass for screening.",
        "critic": "deepseek-r1:14b",
        "writer": "llama3.1:8b",
        "vlm": "qwen2.5vl:7b",
        "num_ctx": 8192,
    },
}

# ---------------------------
# Manuscript categories (3)
# ---------------------------
MANUSCRIPT_BUTTONS = [
    ("Original Research", "original_research"),
    ("Review Article", "review_article"),
    ("Other", "other"),
]

# For original research only:
STUDY_DESIGNS = {
    "Diagnostic accuracy": "diagnostic_accuracy",
    "Prediction model": "prediction_model",
    "Interventional": "interventional",
    "Educational intervention": "educational_intervention",
    "Other": "other",
}


# ---------------------------
# Helpers
# ---------------------------
def safe_filename(name: str) -> str:
    name = name.strip()
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:120] if len(name) > 120 else name


def ensure_dirs():
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)


def save_upload(uploaded_file) -> Path:
    ensure_dirs()
    original = safe_filename(uploaded_file.name)
    dest = PRIVATE_DIR / original
    if dest.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = PRIVATE_DIR / f"{dest.stem}_{stamp}{dest.suffix}"
    dest.write_bytes(uploaded_file.getbuffer())
    return dest


def file_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def reviewer_cli_exists() -> bool:
    return (REPO_ROOT / "reviewer" / "cli.py").exists()


def ollama_ok() -> bool:
    try:
        r = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            text=True,
            check=False,
        )
        return r.returncode == 0
    except Exception:
        return False


def ollama_has_model(tag: str) -> bool:
    try:
        r = subprocess.run(["ollama", "show", tag], capture_output=True, text=True)
        return r.returncode == 0
    except Exception:
        return False


def run_pipeline(
    pdf_path: Path,
    out_md: Path,
    preset: dict,
    manuscript_type: str,
    study_design: str,
    has_ai: bool,
    image_clarity: int,
    max_pages_to_images: int,
    fallback_choice: str,
    temperature: float,
    show_live_log: bool,
) -> int:
    cmd = [
        "python",
        "-m",
        "reviewer.cli",
        "--input",
        str(pdf_path),
        "--out",
        str(out_md),
        "--rubric",
        DEFAULT_RUBRIC,
        "--manuscript_type",
        manuscript_type,
        "--study_design",
        study_design,
        "--critic_model",
        preset["critic"],
        "--writer_model",
        preset["writer"],
        "--vlm_model",
        preset["vlm"],
        "--num_ctx",
        str(preset["num_ctx"]),
        "--temperature",
        str(temperature),
        "--fig_dpi",
        str(image_clarity),  # CLI flag name kept for compatibility
        "--fig_max_pages",
        str(max_pages_to_images),
        "--fig_fallback",
        fallback_choice,  # first_last / all / none
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

    live_lines = []
    log_box = st.empty() if show_live_log else None

    phase_idx = 0
    progress = st.progress(0
