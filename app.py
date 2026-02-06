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

# If your repo uses a different rubric path, change this:
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
# Manuscript types (3 buttons)
# ---------------------------
# Note: Your CLI has no choices and only a default, so it should accept these strings.
MANUSCRIPT_BUTTONS = [
    ("Original Research", "original_research"),
    ("Review Article", "review_article"),
    ("Other", "other"),
]

# Original research only:
STUDY_DESIGNS = {
    "Diagnostic accuracy": "diagnostic_accuracy",
    "Prediction model": "prediction_model",
    "Interventional": "interventional",
    "Educational intervention": "educational_intervention",
    "Systematic review": "systematic_review",
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
    """
    Checks if Ollama is reachable at localhost:11434.
    Uses curl because it is commonly present on Windows 10/11.
    """
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


def ui_status_row(preset_key: str):
    st.caption(
        "Runs on **localhost only**. Uploads are saved to `private_inputs/` and outputs to `outputs/`. Nothing is sent to the internet."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("**Ollama**")
        st.success("Running") if ollama_ok() else st.error("Not reachable")
    with col2:
        st.write("**Reviewer engine**")
        st.success("Found") if reviewer_cli_exists() else st.error("Missing `reviewer/cli.py`")
    with col3:
        st.write("**Models for this preset**")
        preset = PRESETS[preset_key]
        ok = all(ollama_has_model(preset[k]) for k in ("critic", "writer", "vlm"))
        st.success("Installed") if ok else st.warning("Missing model(s)")


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
    """
    Runs the local reviewer CLI and optionally streams logs into the UI.
    """

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
        str(image_clarity),       # kept CLI flag name, UI calls it "image clarity"
        "--fig_max_pages",
        str(max_pages_to_images), # UI: "max pages to turn into images"
        "--fig_fallback",
        fallback_choice,          # first_last / all / none
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
    progress = st.progress(0)
    phase_label = st.caption(f"**{PHASES[phase_idx]}**")

    def set_phase(new_idx: int):
        nonlocal phase_idx
        phase_idx = max(phase_idx, min(new_idx, len(PHASES) - 1))
        progress.progress(int((phase_idx / (len(PHASES) - 1)) * 100))
        phase_label.caption(f"**{PHASES[phase_idx]}**")

    assert proc.stdout is not None
    for line in proc.stdout:
        s = line.rstrip("\n")
        low = s.lower()

        # Heuristic phase bumps (non-breaking if logs change)
        if "extract" in low and "text" in low:
            set_phase(1)
        elif "figure" in low or "image" in low or "convert" in low:
            set_phase(2)
        elif "critic" in low:
            set_phase(3)
        elif "writer" in low or "structured" in low:
            set_phase(4)
        elif "saving" in low or "wrote" in low or "output" in low:
            set_phase(5)

        if show_live_log and log_box is not None:
            live_lines.append(s)
            log_box.code("\n".join(live_lines[-250:]), language="text")

    rc = proc.wait()
    set_phase(6)
    return rc


# ==========================================================
# Streamlit UI
# ==========================================================
st.set_page_config(page_title="Local Manuscript Reviewer", layout="wide")
ensure_dirs()

st.title("Local Manuscript Reviewer")

# Idiot-proof privacy banner
st.error(
    "\n".join(
        [
            "⚠️ Privacy / confidentiality (please read)",
            "- This tool runs **only on your computer** (localhost).",
            "- **Do NOT deploy** this app to a server or the public web.",
            "- **Do NOT use tunnels** (ngrok / Cloudflare Tunnel / Streamlit Cloud).",
            "- Uploaded manuscripts are saved in `private_inputs/` on your PC.",
            "- Outputs are saved in `outputs/` on your PC.",
        ]
    )
)
st.caption("No deployment needed: this runs only on your computer (localhost).")

# Model preset selector (your requested header)
preset_key = st.selectbox(
    "Choose the Critic/Writer Model Quality and Performance",
    list(PRESETS.keys()),
    index=1,  # default = Medium quality, Medium speed
    help="Higher quality is slower but usually produces a more thorough review.",
)
st.caption("Tip: Medium quality, Medium speed is recommended for most people.")

ui_status_row(preset_key)
st.divider()

# Step 1 — Upload
st.header("Step 1 — Upload your manuscript (PDF)")
st.caption("Tip: Drag-and-drop the PDF here. Nothing is uploaded to the internet.")

uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"], help="File stays on your PC.")
saved_path = None
if uploaded_pdf:
    saved_path = save_upload(uploaded_pdf)
    st.success(f"Saved to: `private_inputs/{saved_path.name}`")

st.divider()

# Step 2 — Manuscript category (3 buttons)
st.header("Step 2 — Choose what kind of review this is")
st.caption("Choose the closest category. This helps the reviewer focus and format the report correctly.")

btn_cols = st.columns(3)
if "manuscript_choice" not in st.session_state:
    st.session_state.manuscript_choice = "Original Research"

for i, (label, _) in enumerate(MANUSCRIPT_BUTTONS):
    with btn_cols[i]:
        if st.button(label, use_container_width=True):
            st.session_state.manuscript_choice = label

chosen_label = st.session_state.manuscript_choice
chosen_type = next((t for (lbl, t) in MANUSCRIPT_BUTTONS if lbl == chosen_label), "other")

st.success(f"Selected: **{chosen_label}**")
manuscript_type = chosen_type

# Study design only for original research
study_design = "other"
if manuscript_type == "original_research":
    study_label = st.selectbox("Study design (optional)", list(STUDY_DESIGNS.keys()), index=0)
    study_design = STUDY_DESIGNS[study_label]

has_ai = st.toggle("AI-related manuscript", value=True)

st.divider()

# Step 3 — Figures & tables
st.header("Step 3 — Figures & tables")
st.write("The app checks the PDF for embedded figures/images and uses the vision model when needed.")
st.caption(
    "If a PDF does not contain embedded images, the app can **turn selected pages into images** so the vision model can still comment on figures/tables."
)

with st.expander("Optional: figure settings (most people can skip this)"):
    image_clarity = st.slider(
        "Image clarity (higher = sharper, slower)",
        150,
        300,
        200,
        10,
        help="Higher clarity can help with small text in tables, but it takes longer.",
    )
    max_pages_to_images = st.slider(
        "Maximum number of pages to turn into images",
        2,
        40,
        12,
        1,
        help="This limits how many pages are converted into images for the vision model.",
    )
    fallback_label = st.selectbox(
        "If the PDF has no embedded images, what should the app do?",
        [
            "Turn the first and last pages into images (recommended)",
            "Turn all pages into images (slowest)",
            "Do not turn pages into images",
        ],
        index=0,
    )

    if fallback_label.startswith("Turn the first"):
        fallback_choice = "first_last"
    elif fallback_label.startswith("Turn all"):
        fallback_choice = "all"
    else:
        fallback_choice = "none"

# Defaults if expander not opened
if "image_clarity" not in locals():
    image_clarity = 200
    max_pages_to_images = 12
    fallback_choice = "first_last"

st.divider()

# Step 4 — Run
st.header("Step 4 — Run the review")

colA, colB = st.columns([2, 1])
with colA:
    st.write(
        "**What you’ll get**: a structured peer-review report with major/minor revisions, section-by-section notes, and reporting guideline gaps."
    )
with colB:
    show_live_log = st.checkbox(
        "Show live technical log",
        value=False,
        help="Off by default to avoid displaying confidential content.",
    )

temperature = st.slider(
    "Style: Deliberate ↔ Random",
    0.0,
    0.6,
    0.2,
    0.05,
    help="Deliberate = more consistent/structured. Random = more exploratory wording. (Recommended: Deliberate)",
)

# Idiot-proof “local-only” gate
st.markdown("### Before you run")
confirm_local = st.checkbox(
    "I confirm this is running locally on my computer (no deployment, no tunnels).",
    value=False,
)

st.info(
    "How to use this:\n"
    "1) Upload the PDF in Step 1\n"
    "2) Choose the manuscript category\n"
    "3) Click **Start review**\n"
    "4) Download your report in the Results section"
)

run_btn = st.button(
    "Start review",
    type="primary",
    use_container_width=True,
    disabled=not confirm_local,
)

clear_btn = st.button("Clear uploaded PDFs (private_inputs)", use_container_width=True)
if clear_btn:
    for f in PRIVATE_DIR.glob("*.pdf"):
        try:
            f.unlink()
        except Exception:
            pass
    st.success("Cleared uploaded PDFs from private_inputs/")

st.divider()

# Results
st.header("Results")

if run_btn:
    if not uploaded_pdf or saved_path is None:
        st.error("Please upload a PDF in Step 1.")
        st.stop()

    if not ollama_ok():
        st.error("Ollama is not reachable. Start Ollama and try again.")
        st.stop()

    if not reviewer_cli_exists():
        st.error("Reviewer engine not found at `reviewer/cli.py`.")
        st.stop()

    preset = PRESETS[preset_key]
    missing_models = [
        tag for tag in (preset["critic"], preset["writer"], preset["vlm"]) if not ollama_has_model(tag)
    ]
    if missing_models:
        st.error("Missing model(s) for this preset: " + ", ".join(missing_models))
        st.info("Run `setup_models.bat` to install models, then come back and try again.")
        st.stop()

    pdf_path = saved_path
    out_md = OUTPUTS_DIR / f"{pdf_path.stem}_review.md"

    st.info("Running… this can take several minutes depending on preset and PDF size.")

    rc = run_pipeline(
        pdf_path=pdf_path,
        out_md=out_md,
        preset=preset,
        manuscript_type=manuscript_type,
        study_design=study_design,
        has_ai=has_ai,
        image_clarity=image_clarity,
        max_pages_to_images=max_pages_to_images,
        fallback_choice=fallback_choice,
        temperature=temperature,
        show_live_log=show_live_log,
    )

    if rc == 0:
        st.success("Review complete.")
    else:
        st.error(f"Review exited with code {rc}. See the technical log/terminal output for details.")

# Show outputs for the currently uploaded PDF (if any)
if uploaded_pdf and saved_path is not None:
    pdf_path = saved_path
    out_md = OUTPUTS_DIR / f"{pdf_path.stem}_review.md"
    critic_log = OUTPUTS_DIR / "critic_issue_log.md"
    fig_notes = OUTPUTS_DIR / "figure_notes.txt"
    checklist = OUTPUTS_DIR / "reporting_checklist_gaps.json"

    tabs = st.tabs(["Review", "Critic log", "Figure notes", "Checklist gaps"])

    with tabs[0]:
        txt = file_text(out_md)
        if txt:
            st.download_button("Download review.md", txt, file_name=out_md.name, mime="text/markdown")
            st.text_area("Preview", txt, height=450)
        else:
            st.caption("No review output yet.")

    with tabs[1]:
        txt = file_text(critic_log)
        if txt:
            st.download_button("Download critic_issue_log.md", txt, file_name=critic_log.name, mime="text/markdown")
            st.text_area("Preview", txt, height=450)
        else:
            st.caption("No critic log yet.")

    with tabs[2]:
        txt = file_text(fig_notes)
        if txt:
            st.download_button("Download figure_notes.txt", txt, file_name=fig_notes.name, mime="text/plain")
            st.text_area("Preview", txt, height=450)
        else:
            st.caption("No figure notes yet.")

    with tabs[3]:
        if checklist.exists():
            raw = checklist.read_text(encoding="utf-8", errors="ignore")
            st.download_button(
                "Download reporting_checklist_gaps.json",
                raw,
                file_name=checklist.name,
                mime="application/json",
            )
            try:
                st.json(json.loads(raw))
            except Exception:
                st.code(raw, language="json")
        else:
            st.caption("No checklist gaps file yet.")

st.divider()

# Show saved PDFs
st.subheader("Your uploaded PDFs (private_inputs)")
pdfs = sorted(PRIVATE_DIR.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
if not pdfs:
    st.caption("No PDFs saved yet.")
else:
    for p in pdfs[:30]:
        st.caption(f"- {p.name}")
