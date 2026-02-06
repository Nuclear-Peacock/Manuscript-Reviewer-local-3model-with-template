# Local Manuscript Reviewer (Radiology / Nuclear Medicine / MedEd / AI)

A privacy-first, **local** manuscript review assistant that runs on your computer.

You upload a manuscript PDF, click **Run Review**, and the tool produces:

* a structured peer-review report (ready to paste into a journal portal)
* a critic issue log (what to fix, prioritized)
* figure/table notes (from the PDF page images)

This project is designed for expert review in **radiology, nuclear medicine, medical education, and AI in these domains**.

---

## What this tool does (in plain language)

When you run a review, it performs three passes locally:

1. **Critic pass**: finds problems and missing information (methods, statistics, reporting gaps, nomenclature)
2. **Figure/Table pass**: reviews figures/tables by looking at rendered PDF page images
3. **Writer pass**: produces a polished, structured reviewer report

You pick a **Quality preset** (Best / Balanced / Fast) depending on your computer.

---

## Privacy and confidentiality

* The app runs **only on your computer**.
* The user interface opens at **[http://127.0.0.1:8501](http://127.0.0.1:8501)** (your own machine only).
* Manuscripts are saved to a local folder: **private_inputs/**
* Outputs are saved locally to: **outputs/**
* Nothing is automatically uploaded to the internet.

**Important:** This repo is public. Do **not** commit manuscripts or outputs to GitHub.

---

## What you need (only if you don’t already have it)

You may already have these installed. If so, you can skip installation.

1. **Python 3.10 or newer**
2. **Ollama** (runs the local language models)

That’s it.

---

## Quickstart (Windows — no VS Code required)

These steps are written for people who are not programmers.

### Step 1 — Download the project

1. Open the GitHub page for this project.
2. Click the green **Code** button.
3. Click **Download ZIP**.
4. Unzip it somewhere easy to find (for example: `Documents\\ManuscriptReviewer`).

### Step 2 — Start Ollama (if you use it already, just make sure it’s running)

1. Open **Ollama**.
2. Make sure it is running in the background.

### Step 3 — One-click start

1. In the project folder, double-click **run_ui.bat**.
2. The first run may take a few minutes.
3. Your web browser should open automatically.

If the tool says some models are missing, choose **Yes** to install them.

### Step 4 — Run a review

1. In the browser page, click **Upload PDF** and choose the manuscript.
2. Choose a **Quality preset**:

   * **Best**: highest quality, needs a strong GPU
   * **Balanced**: great quality, faster for many GPUs
   * **Fast**: for broader hardware compatibility
3. Choose the manuscript type and study design.
4. Click **Run review**.

### Step 5 — Find your files

* Your manuscript copy is saved in: **private_inputs/**
* Your review outputs are saved in: **outputs/**

---

## Using the Quality preset dropdown

* **Best (Max quality; high VRAM)**

  * Slowest but strongest. Recommended for final, high-stakes reviews.

* **Balanced (Great quality; faster)**

  * Usually the best everyday option.

* **Fast (Good quality; widest hardware)**

  * Useful for laptops / smaller GPUs.

Tip: If the review feels slow, switch from **Best → Balanced**.

---

## Troubleshooting (common issues)

### “Python not found”

* Install Python 3.10+.
* During installation, ensure **“Add Python to PATH”** is checked.
* Then run **run_ui.bat** again.

### “Ollama is not reachable”

* Start the Ollama application.
* Then run **run_ui.bat** again.

### The first review takes a long time

* The first run may download and set up models.
* After that, reviews are faster.
* If it is still too slow, choose **Balanced**.

### Where are my results?

* Reviews are in **outputs/**
* Uploaded manuscripts are in **private_inputs/**

---

## For advanced users

* CLI is available via `python -m reviewer.cli ...`
* The local UI is `app.py` (Streamlit, localhost-only)

---

## License

MIT License
