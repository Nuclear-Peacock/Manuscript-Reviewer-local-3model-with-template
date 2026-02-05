# Local Manuscript Reviewer (Radiology / Nuclear Medicine / MedEd / AI)
**DeepSeek-R1 (Critic) → Llama 3.3 (Writer) + Qwen2.5-VL (Figures/Tables)**  
Privacy-first, two-pass peer review workflow designed to behave like a **human reviewer** (not a question-by-question form).

---

## What this is
A local tool that helps you perform an initial expert-style peer review of manuscripts in:
- Radiology & Nuclear Medicine
- Medical Education
- AI in Radiology / AI in Medical Education

It produces:
- A **PASS 1 Critic Issue Log** (DeepSeek-R1) with severity tags (Fatal/Major/Moderate/Minor)
- A **PASS 2 Final Review** (Llama 3.3) in a structured reviewer format:
  - Synopsis (3–4 sentences)
  - Overall recommendation (Accept/Minor/Major/Reject)
  - Key Details for Original Research
  - Required Revisions (Major / Minor)
  - Section-by-section notes (Abstract → References)
  - Reporting Guideline Checklist Gaps (EQUATOR-guided)
  - Ethics / Bias / Reproducibility
- Optional **FIGURE NOTES** (Qwen2.5-VL) with severity tags for figures/tables provided as images
- Optional **novelty/reference check** using minimal disclosure inputs (keywords + DOIs/PMIDs only)

> Important: Output is intentionally **not** a checklist Q&A. The reviewer template is used as an internal reasoning scaffold.

---

## Privacy & confidentiality (core design goal)
- Runs **locally** (models hosted on your machine via Ollama).
- No manuscript text is sent to remote LLMs.
- Novelty/reference search uses **keywords + DOIs/PMIDs + paraphrased novelty claims only** (no manuscript excerpts).
- Outputs go to `outputs/` (gitignored).
- Put real manuscripts in `private_inputs/` (gitignored).

This repo includes a **synthetic demo manuscript** only—safe to share.

---

## Quickstart (synthetic demo)
After setup, run the included synthetic demo:
```bash
python -m reviewer.cli --input demo/synthetic_manuscript.pdf \
  --rubric config/rubrics/core_rubric.json \
  --out outputs/demo_review.md \
  --manuscript_type original_research \
  --study_design diagnostic_accuracy \
  --has_ai \
  --figure_images demo/figures/fig1.png demo/figures/fig2.png
```

Outputs:
- `outputs/demo_review.md`
- `outputs/critic_issue_log.md`
- `outputs/figure_notes.txt`

---

## Requirements
- Python 3.10+
- A local GPU is recommended for 70B models (but smaller variants can work)
- Ollama installed and running

---

## Install
### 1) Create and activate a virtual environment
**macOS/Linux**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2) Install Python dependencies
```bash
pip install -r requirements.txt
```

---

## Models (Ollama)
Recommended stack:
- Critic: `deepseek-r1:70b`
- Writer: `llama3.3:70b`
- Vision: `qwen2.5-vl:7b` (or larger if you have it)

Pull models:
```bash
ollama pull deepseek-r1:70b
ollama pull llama3.3:70b
ollama pull qwen2.5-vl:7b
```

---

## Run on your own manuscript (local only)
Put manuscripts in `private_inputs/` (ignored by git), then:

```bash
python -m reviewer.cli --input private_inputs/manuscript.pdf \
  --rubric config/rubrics/core_rubric.json \
  --out outputs/review.md \
  --manuscript_type original_research \
  --study_design diagnostic_accuracy \
  --has_ai \
  --critic_model deepseek-r1:70b \
  --writer_model llama3.3:70b
```

### Add figures/tables (as images)
Export or screenshot figures/tables to images and run:
```bash
python -m reviewer.cli --input private_inputs/manuscript.pdf \
  --rubric config/rubrics/core_rubric.json \
  --out outputs/review.md \
  --study_design diagnostic_accuracy \
  --figure_images private_inputs/fig1.png private_inputs/fig2.png \
  --vlm_model qwen2.5-vl:7b
```

### Add novelty/reference check (minimal disclosure)
```bash
python -m reviewer.cli --input private_inputs/manuscript.pdf \
  --rubric config/rubrics/core_rubric.json \
  --out outputs/review.md \
  --study_design prediction_model \
  --keywords "FDG PET lymphoma radiomics" \
  --novelty_claim "Paraphrase the manuscript's novelty claim" \
  --dois 10.1234/abcd,10.5555/efgh
```

---

## EQUATOR guideline metadata cache (optional)
This fetches guideline metadata (titles/acronyms/URLs) and saves a local index (no manuscript text involved):
```bash
python -m reviewer.equator_cache --out cache/equator_index.json
```

---

## Configuration & customization
### Prompts (behavior)
- `config/prompts/critic_prompt.txt` — DeepSeek-R1 (PASS 1)
- `config/prompts/writer_prompt.txt` — Llama 3.3 (PASS 2)
- `config/prompts/vlm_prompt.txt` — Qwen2.5-VL figure/table notes
- `config/prompts/reviewer_template_original_research.txt` — reviewer template scaffold (internal use only)
- `config/prompts/nuclear_nomenclature_guide.txt` — nuclear medicine nomenclature scaffold

### Reporting guideline resolver defaults
- `config/guidelines/equator_mapping.json`

### Rubrics (evidence retrieval)
- `config/rubrics/core_rubric.json`  
You can add more rubric JSON files and pass multiple `--rubric ...` args.

---

## “Not Q&A” guarantee
This project is designed to write like a **human peer reviewer**:
- The template is used internally as a reasoning scaffold.
- The outputs are not a question-by-question checklist.
- Questions (when needed) are surfaced only as targeted **Missing Info Requests**.

---

## License
MIT License (see `LICENSE`).

---

## Disclaimer
This tool is an assistive reviewer-in-the-loop system and does not replace expert judgment, journal policies, or ethical/legal requirements.
