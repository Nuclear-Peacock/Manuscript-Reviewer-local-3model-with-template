# Local Manuscript Reviewer (Radiology / Nuclear Medicine / Medical Education)

A **local-only** manuscript review assistant that generates structured, human-style peer reviews using AI.

* **Privacy First:** PDFs never leave your computer.
* **No Cloud:** Runs entirely on localhost using Ollama.
* **Multimodal:** Uses Vision AI to check figures and tables.

---

## 🚀 Quick Start (Windows)

1.  **Install Prerequisites:**
    * [Python 3.10+](https://www.python.org/downloads/) (Make sure to check **"Add Python to PATH"** during install!)
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

*Note: The first time you select a new preset, the app will need to download those specific models. This may take some time.*

---

## 📂 Folder Structure

* **`private_inputs/`**: Drop PDFs here (or upload via UI). These are **ignored** by git.
* **`outputs/`**: Your generated review reports appear here.

---

## ⚠️ Disclaimer

This tool is for **research and assistance purposes only**. Do not rely solely on AI for medical decisions or final peer review judgments. Always verify AI outputs.
