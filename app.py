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
# Local folders (idiot-proof)
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
  border:
