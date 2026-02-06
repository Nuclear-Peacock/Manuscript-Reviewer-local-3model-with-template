![Security Scan Status](https://github.com/Nuclear-Peacock/Manuscript-Reviewer-local-3model-with-template/actions/workflows/security.yml/badge.svg)
# Local Manuscript Reviewer (Radiology / Nuclear Medicine / Medical Education)

A **local-only** manuscript review assistant that generates structured, human-style peer reviews using AI.

* **Privacy First:** PDFs never leave your computer.
* **No Cloud:** Runs entirely on localhost using Ollama.
* **Multimodal:** Uses Vision AI to check figures and tables.

---

## 🚀 Quick Start (Windows)

1.  **Install Prerequisites:**
    * [Python 3.10+](https://www.python.org/downloads/) (Check **"Add Python to PATH"** during install!)
    * [Ollama](https://ollama.com/)

2.  **Run the App:**
    * Double-click the **`run_ui.bat`** file.
    * *That's it!*

The launcher will automatically:
* ✅ Check if Python and Ollama are running.
* ✅ Download the necessary AI models (if you don't have them).
* ✅ Open the Web UI in your browser.

---

## 🧠 Model Presets

The app comes with three "Personalities" optimized for different hardware:

| Preset | Models Used | Memory Req | Speed |
| :--- | :--- | :--- | :--- |
| **Medium (Recommended)** | `llama3.3` (70B), `deepseek-r1:32b` | 32GB+ RAM | Balanced |
| **Fast** | `llama3.1:8b`, `deepseek-r1:14b` | 16GB RAM | Very Fast |
| **Accurate** | `llama3.3` (70B), `deepseek-r1:70b` | 64GB+ RAM | Slow |

*Note: The first time you select a new preset, the app will need to download those specific models. You can do this directly from the UI sidebar.*

---

## ✨ Features

### 1. Specialized Review
Choose your manuscript type to get tailored feedback:
* **Original Research:** Checks study design (e.g., Randomized Control Trial, Retrospective Cohort).
* **AI/ML Studies:** Check the **"Includes AI/ML?"** box to trigger specific reporting checklist validation (e.g., CLAIM checklist gaps).

### 2. Vision Analysis
The app uses **Qwen2.5-VL** to "look" at your figures and tables, checking for:
* Illegible reporting.
* Missing captions.
* Data inconsistencies between figures and text.

---

## 📂 Folder Structure

* **`private_inputs/`**: Drop PDFs here (or upload via UI). These are **ignored** by git.
* **`outputs/`**: Your generated review reports appear here.

---

## ⚠️ Disclaimer

This tool is for **research and assistance purposes only**. Do not rely solely on AI for medical decisions or final peer review judgments. Always verify AI outputs.
