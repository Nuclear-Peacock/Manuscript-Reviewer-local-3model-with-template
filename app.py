import os
import re
import sys
import time
import json
import shutil
import hashlib
import textwrap
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import streamlit as st

# ----------------------------
# Local folders (idiot-proof)
# ----------------------------
REPO_ROOT = Path(__file__).resolve().parent
PRIVATE_INPUTS = REPO_ROOT / "private_inputs"
OUTPUTS_ROOT = REPO_ROOT / "outputs"
PRIVATE_INPUTS.mkdir(parents=True, exist_ok=True)
OUTPUTS_ROOT.mkdir(parents=True, exist_ok=True)

APP_TITLE = "Local Manuscript Reviewer"
APP_SUBTITLE = "Radiology • Nuclear Medicine • Medical Education • AI-in-Radiology/Education"

# ----------------------------
# UI wording (your preferences)
# ----------------------------
MANUSCRIPT_CATEGORIES = ["Original Research", "Review Article", "Other"]

# Optional study design list (kept simple + editable)
STUDY_DESIGNS = [
    "Not specified",
    "Prospective cohort",
    "Retrospective cohort",
    "Case-control",
    "Cross-sectional",
    "Randomized controlled trial",
    "Non-randomized interventional",
    "Diagnostic accuracy",
    "Systematic review / meta-analysis",
    "Phantom / simulation study",
    "Technical development / validation",
    "Quality improvement / audit",
    "Educational intervention",
]

PRESETS = {
    "High quality, Low speed": {
        "critic_model": "deepseek-r1",
        "writer_model": "llama3.3",
        "vision_model": "qwen2.5-vl",
        "image_clarity": 260,
        "deliberate_random": 0.25,  # more deliberate
    },
    "Medium quality, Medium speed": {
        "critic_model": "deepseek-r1",
        "writer_model": "llama3.3",
        "vision_model": "qwen2.5-vl",
        "image_clarity": 220,
        "deliberate_random": 0.45,
    },
    "Low quality, High speed": {
        "critic_model": "deepseek-r1",
        "writer_model": "llama3.3",
        "vision_model": "qwen2.5-vl",
        "image_clarity": 180,
        "deliberate_random": 0.65,  # more random
    },
}


# ----------------------------
# Minimal styling (clean + airy)
# ----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="🧾", layout="wide")
st.markdown(
    """
<style>
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; }
h1, h2, h3 { letter-spacing: -0.02em; }
.small-note { color: rgba(250,250,250,0.75); font-size: 0.92rem; }
.card {
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  padding: 14px 16px;
  background: rgba(255,255,255,0.03);
}
hr { border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 1.1rem 0; }
</style>
""",
    unsafe_allow_html=True,
)


# ----------------------------
# Helpers
# ----------------------------
def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _safe_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    name = re.sub(r"[^A-Za-z0-9._-]", "", name)
    return name or f"manuscript_{_now_stamp()}.pdf"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def _run(cmd: List[str], cwd: Optional[Path] = None, timeout: Optional[int] = None) -> Tuple[int, str]:
    """Run command, return (returncode, combined_output)."""
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
        )
        return p.returncode, p.stdout
    except Exception as e:
        return 999, f"[Error] Failed to run command: {e}"


@st.cache_data(show_spinner=False)
def discover_cli_flags() -> Set[str]:
    """
    Ask reviewer.cli what flags it supports by calling '--help'.
    Then we only pass flags that exist, which makes the UI robust.
    """
    cmd = [sys.executable, "-m", "reviewer.cli", "--help"]
    code, out = _run(cmd, cwd=REPO_ROOT, timeout=25)
    if code != 0 and "No module named" in out:
        # If module isn't importable, return empty; UI will show a helpful error.
        return set()

    flags = set(re.findall(r"(--[A-Za-z0-9][A-Za-z0-9_-]*)", out))
    # Also accept short flags like -i, -o if present (rare but possible)
    flags.update(re.findall(r"(\-[A-Za-z])\b", out))
    return flags


def pick_first_existing_flag(existing: Set[str], candidates: List[str]) -> Optional[str]:
    for c in candidates:
        if c in existing:
            return c
    return None


def build_cli_command(
    existing_flags: Set[str],
    pdf_path: Path,
    output_dir: Path,
    manuscript_category: str,
    study_design: Optional[str],
    critic_model: str,
    writer_model: str,
    vision_model: str,
    image_clarity: int,
    deliberate_random: float,
) -> Tuple[List[str], Dict[str, str]]:
    """
    Build a 'python -m reviewer.cli ...' command.
    Only includes args that exist in the real CLI.
    Returns (cmd, arg_debug_map).
    """
    cmd = [sys.executable, "-m", "reviewer.cli"]
    debug = {}

    # Input PDF flag (try common names)
    pdf_flag = pick_first_existing_flag(
        existing_flags,
        ["--pdf", "--pdf_path", "--input_pdf", "--input", "--manuscript_pdf", "-i"],
    )
    if pdf_flag:
        cmd += [pdf_flag, str(pdf_path)]
        debug["pdf"] = f"{pdf_flag} {pdf_path}"
    else:
        # Fallback: last resort positional (some CLIs accept it)
        cmd += [str(pdf_path)]
        debug["pdf"] = f"(positional) {pdf_path}"

    # Output directory flag (try common names)
    out_flag = pick_first_existing_flag(
        existing_flags,
        ["--output_dir", "--out_dir", "--output", "--outputs", "-o"],
    )
    if out_flag:
        cmd += [out_flag, str(output_dir)]
        debug["output"] = f"{out_flag} {output_dir}"
    else:
        debug["output"] = "(no output flag detected; CLI default will be used)"

    # Manuscript category (your CLI arg mentioned as --manuscript_type)
    # We'll pass a normalized string but keep it human-safe.
    # Examples: original_research, review_article, other
    category_map = {
        "Original Research": "original_research",
        "Review Article": "review_article",
        "Other": "other",
    }
    cat_value = category_map.get(manuscript_category, "other")

    cat_flag = pick_first_existing_flag(existing_flags, ["--manuscript_type", "--manuscript_category", "--type"])
    if cat_flag:
        cmd += [cat_flag, cat_value]
        debug["manuscript_type"] = f"{cat_flag} {cat_value}"
    else:
        debug["manuscript_type"] = "(no manuscript type flag detected)"

    # Study design (optional)
    if study_design and study_design != "Not specified":
        design_flag = pick_first_existing_flag(existing_flags, ["--study_design", "--design"])
        if design_flag:
            cmd += [design_flag, study_design]
            debug["study_design"] = f"{design_flag} {study_design}"
        else:
            debug["study_design"] = "(no study design flag detected)"

    # Models
    critic_flag = pick_first_existing_flag(existing_flags, ["--critic_model", "--critic"])
    if critic_flag:
        cmd += [critic_flag, critic_model]
        debug["critic_model"] = f"{critic_flag} {critic_model}"

    writer_flag = pick_first_existing_flag(existing_flags, ["--writer_model", "--writer"])
    if writer_flag:
        cmd += [writer_flag, writer_model]
        debug["writer_model"] = f"{writer_flag} {writer_model}"

    vision_flag = pick_first_existing_flag(existing_flags, ["--vision_model", "--vision"])
    if vision_flag:
        cmd += [vision_flag, vision_model]
        debug["vision_model"] = f"{vision_flag} {vision_model}"

    # Image clarity (your “DPI” rename)
    dpi_flag = pick_first_existing_flag(existing_flags, ["--dpi", "--image_dpi", "--render_dpi", "--page_dpi"])
    if dpi_flag:
        cmd

