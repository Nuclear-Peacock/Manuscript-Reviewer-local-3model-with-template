import os
import re
import sys
import time
import hashlib
import subprocess
import urllib.request
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Set

import streamlit as st

# ----------------------------
# Local folders
# ----------------------------
REPO_ROOT = Path(__file__).resolve().parent
PRIVATE_INPUTS = REPO_ROOT / "private_inputs"
OUTPUTS_ROOT = REPO_ROOT / "outputs"
PRIVATE_INPUTS.mkdir(parents=True, exist_ok=True)
OUTPUTS_ROOT.mkdir(parents=True, exist_ok=True)

APP_TITLE = "Local Manuscript Reviewer"
APP_SUBTITLE = "Radiology • Nuclear Medicine • Medical Education • AI-in-Radiology/Education"

MANUSCRIPT_CATEGORIES = ["Original Research", "Review Article", "Other"]

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
    "Accurate (Slow)": {
        "critic_model": "deepseek-r1:70b",
        "writer_model": "llama3.3",
        "vision_model": "qwen2.5vl:7b",
        "image_clarity": 260,
        "deliberate_random": 0.25,
    },
    "Medium (Balanced)": {
        "critic_model": "deepseek-r1:32b",
        "writer_model": "llama3.3",
        "vision_model": "qwen2.5vl:7b",
        "image_clarity": 220,
        "deliberate_random": 0.45,
    },
    "Fast (Less Accurate)": {
        "critic_model": "deepseek-r1:14b",
        "writer_model": "llama3.1:8b",
        "vision_model": "qwen2.5vl:7b",
        "image_clarity": 180,
        "deliberate_random": 0.65,
    },
}

# ----------------------------
# Streamlit config + minimal CSS
# ----------------------------
st.set_page_config(page_title=APP_TITLE, page_icon="🧾", layout="wide")
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1200px; }
    h1, h2, h3 { letter-spacing: -0.02em; }
    .card {
      border: 1px solid rgba(255,255,255,0.10);
      border-radius: 14px;
      padding: 14px 16px;
      background: rgba(255,255,255,0.03);
    }
    hr { border: none; border-top: 1px solid rgba(255,255,255,0.10); margin: 1.1rem 0; }
    .small { color: rgba(255,255,255,0.75); font-size: 0.92rem; }
    .stAlert { margin-top: 1rem; }
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

def human_bytes(n: int) -> str:
    x = float(n)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if x < 1024 or unit == "TB":
            return f"{x:.0f} {unit}" if unit == "B" else f"{x:.1f} {unit}"
        x /= 1024
    return f"{x:.1f} TB"

def list_output_files(folder: Path) -> List[Path]:
    if not folder.exists():
        return []
    files = [p for p in folder.rglob("*") if p.is_file()]
    priority_substrings = [
        "_review.md", "review.md", "peer", "critic", "checklist",
        "figure", "table", ".md", ".json", ".txt",
    ]
    def score(p: Path):
        name = p.name.lower()
        pri = next((i for i, s in enumerate(priority_substrings) if s in name), len(priority_substrings))
        return (pri, name)
    return sorted(files, key=score)

def get_installed_models() -> Set[str]:
    """Queries local Ollama instance for installed model tags."""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return {m["name"] for m in data.get("models", [])}
    except Exception:
        pass
    return set()

def check_models_availability(preset_data: dict, installed_tags: Set[str]) -> Tuple[bool, List[str]]:
    """Returns (True/False, list_of_missing_models)."""
    required = [
        preset_data["critic_model"],
        preset_data["writer_model"],
        preset_data["vision_model"]
    ]
    missing = []
    for req in required:
        if not any(req in tag for tag in installed_tags):
            missing.append(req)
    return (len(missing) == 0), missing

def pull_model_with_progress(model_name: str):
    """ Runs 'ollama pull' and shows a spinner. """
    try:
        with st.spinner(f"Downloading {model_name}... (This can take a while for large models)"):
            subprocess.run(["ollama", "pull", model_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        st.success(f"Successfully downloaded {model_name}!")
        time.sleep(1) 
        st.rerun()    
    except subprocess.CalledProcessError:
        st.error(f"Failed to download {model_name}. Check internet connection or model name.")
    except Exception as e:
        st.error(f"An error occurred: {e}")


def build_cli_command(
    pdf_path: Path,
    output_dir: Path,
    manuscript_category: str,
    study_design: Optional[str],
    has_ai: bool,
    critic_model: str,
    writer_model: str,
    vision_model: str,
    image_clarity: int,
    deliberate_random: float,
) -> List[str]:
    category_map = {
        "Original Research": "original_research",
        "Review Article": "review_article",
        "Other": "other",
    }
    cat_value = category_map.get(manuscript_category, "other")

    cmd = [
        sys.executable, "-m", "reviewer.cli",
        "--input", str(pdf_path),
        "--out", str(output_dir),
        "--manuscript_type", cat_value,
        "--critic_model", critic_model,
        "--writer_model", writer_model,
        "--vlm_model", vision_model,
        "--fig_dpi", str(int(image_clarity)),
        "--temperature", str(float(deliberate_random)),
    ]

    if manuscript_category == "Original Research" and study_design and study_design != "Not specified":
        cmd += ["--study_design", study_design]
    
    if has_ai:
        cmd += ["--has_ai"]

    return cmd

# ----------------------------
# Main Application Logic
# ----------------------------
def main():
    st.title(f"🧾 {APP_TITLE}")
    st.caption(APP_SUBTITLE)

    installed_tags = get_installed_models()
    
    # Sidebar settings
    with st.sidebar:
        st.markdown("### Privacy / confidentiality")
        st.markdown(
            """
            <div class="card">
            <b>No deployment needed.</b> This is meant to run only on your computer.<br><br>
            <b>Do not deploy this app.</b><br>
            • Do NOT deploy to any server<br>
            • Do NOT use tunnels (ngrok / Cloudflare Tunnel / Streamlit Cloud)<br>
            • Uploads are saved locally to <code>private_inputs/</code><br>
            • Outputs are saved locally to <code>outputs/</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("### Choose the Critic/Writer Model Quality")
        
        preset_options = list(PRESETS.keys())
        
        def format_preset(name):
            is_ready, _ = check_models_availability(PRESETS[name], installed_tags)
            if is_ready:
                return name
            return f"{name} (Download Required ⬇️)"

        selected_key = st.selectbox(
            "Model preset", 
            preset_options, 
            index=1,
            format_func=format_preset
        )
        
        preset = PRESETS[selected_key]
        is_preset_ready, missing_models = check_models_availability(preset, installed_tags)

        if not is_preset_ready:
            st.warning(f"Missing: {', '.join(missing_models)}")
            if st.button("📥 Download Missing Models", type="primary"):
                for m in missing_models:
                    pull_model_with_progress(m)

        st.markdown("### Advanced settings")
        image_clarity = st.slider(
            "Image clarity (higher = sharper, slower)",
            min_value=120, max_value=320, value=int(preset["image_clarity"]), step=10,
        )

        deliberate_random = st.slider(
            "Deliberate ↔ Random",
            min_value=0.05, max_value=1.00, value=float(preset["deliberate_random"]), step=0.05,
            help="Lower feels more deliberate/consistent. Higher feels more random/creative.",
        )

        with st.expander("Model details"):
            st.text_input("Critic model", value=preset["critic_model"], disabled=True)
            st.text_input("Writer model", value=preset["writer_model"], disabled=True)
            st.text_input("Vision model", value=preset["vision_model"], disabled=True)

        st.markdown("---")
        local_only_confirm = st.checkbox(
            "I confirm I will run this locally only (no deployment, no tunnels).",
            value=False,
        )

    # Main workflow
    st.markdown("## Workflow")
    colA, colB, colC = st.columns([1.2, 1, 1])

    with colA:
        st.markdown("### 1) Upload PDF")
        uploaded = st.file_uploader("Manuscript PDF", type=["pdf"], accept_multiple_files=False)
        st.caption("Saved locally into `private_inputs/` (not uploaded anywhere).")

    with colB:
        st.markdown("### 2) Choose category")
        manuscript_category = st.selectbox("Manuscript category", MANUSCRIPT_CATEGORIES, index=0)
        
        study_design = None
        if manuscript_category == "Original Research":
            study_design = st.selectbox("Study design (optional)", STUDY_DESIGNS, index=0)
            
        st.markdown("---")
        has_ai = st.checkbox("Includes AI/ML components?", value=False, help="Check if the manuscript uses AI/ML. Triggers specific checklists.")

    with colC:
        st.markdown("### 3) Start review")
        st.caption("Runs locally using your local models (Ollama + GPU where configured).")
        
        btn_disabled = (uploaded is None or not local_only_confirm or not is_preset_ready)
        
        run_btn = st.button(
            "Start review",
            type="primary",
            use_container_width=True,
            disabled=btn_disabled,
        )
        
        if not is_preset_ready:
            st.caption("⚠️ Install models in sidebar to start.")
        elif uploaded is None:
            st.caption("Upload a PDF to enable Start.")
        elif not local_only_confirm:
            st.caption("Confirm local-only use in sidebar.")

    st.markdown("---")

    if run_btn and is_preset_ready:
        original_name = _safe_filename(uploaded.name)
        tmp = PRIVATE_INPUTS / f"{_now_stamp()}__{original_name}"
        with open(tmp, "wb") as f:
            f.write(uploaded.getbuffer())

        file_hash = _sha256_file(tmp)
        pdf_path = PRIVATE_INPUTS / f"{tmp.stem}__{file_hash}.pdf"
        tmp.rename(pdf_path)

        run_id = f"{_now_stamp()}__{pdf_path.stem[:48]}"
        output_dir = OUTPUTS_ROOT / run_id
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = build_cli_command(
            pdf_path=pdf_path,
            output_dir=output_dir,
            manuscript_category=manuscript_category,
            study_design=study_design,
            has_ai=has_ai,
            critic_model=preset["critic_model"],
            writer_model=preset["writer_model"],
            vision_model=preset["vision_model"],
            image_clarity=image_clarity,
            deliberate_random=deliberate_random,
        )

        st.markdown("### Review Progress")
        
        prog_bar = st.progress(0, text="Initializing reviewer...")
        with st.expander("See raw technical logs (for debugging)", expanded=False):
            log_box = st.empty()

        start = time.time()
        collected: List[str] = []
        
        try:
            p = subprocess.Popen(
                cmd,
                cwd=str(REPO_ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            while True:
                line = p.stdout.readline() if p.stdout else ""
                if line:
                    text_line = line.strip()
                    collected.append(text_line)

                    lower_line = text_line.lower()
                    if "loading weights" in lower_line or "bertmodel" in lower_line:
                        prog_bar.progress(10, text="⏳ Loading AI models (this may take a moment)...")
                    elif "critic" in lower_line and "start" in lower_line:
                        prog_bar.progress(30, text="🧐 Critic Agent: Reading and analyzing manuscript...")
                    elif "writer" in lower_line and "start" in lower_line:
                        prog_bar.progress(60, text="✍️ Writer Agent: Drafting peer review report...")
                    elif "vision" in lower_line or "figure" in lower_line:
                        prog_bar.progress(80, text="🖼️ Vision Agent: Checking figures and tables...")
                    elif "saving" in lower_line or "completed" in lower_line:
                        prog_bar.progress(95, text="💾 Finalizing and saving reports...")

                    log_box.code("\n".join(collected[-50:]), language="text")

                if p.poll() is not None:
                    if p.stdout:
                        rest = p.stdout.read()
                        if rest:
                            for l in rest.splitlines():
                                collected.append(l.strip())
                    break
                time.sleep(0.01)

        except Exception as e:
            st.error(f"Could not start the review process: {e}")
            st.stop()

        elapsed = time.time() - start
        prog_bar.progress(100, text=f"✅ Complete! (took {elapsed:.1f}s)")
        
        run_log = output_dir / "run_log.txt"
        run_log.write_text("\n".join(collected), encoding="utf-8")

        st.markdown("### Generated Reviews & Reports")
        files = list_output_files(output_dir)
        if not files:
            st.warning("No output files were generated. Check the hidden log above for errors.")
        else:
            for p in files:
                with open(p, "rb") as f:
                    file_data = f.read()
                    
                col_icon, col_details, col_btn = st.columns([0.5, 3, 1])
                with col_icon:
                    st.write("📄")
                with col_details:
                    st.markdown(f"**{p.name}**")
                    st.caption(f"{human_bytes(p.stat().st_size)}")
                with col_btn:
                    st.download_button(
                        label="Download",
                        data=file_data,
                        file_name=p.name,
                        mime="application/octet-stream",
                        key=f"dl_{p.name}"
                    )
        st.markdown("---")

if __name__ == "__main__":
    main()
