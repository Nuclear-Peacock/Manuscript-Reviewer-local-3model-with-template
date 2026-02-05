## VS Code local setup

1) Install Python 3.10+ and VS Code + Python extension.
2) Open this folder in VS Code.
3) Create venv:
```bash
python -m venv .venv
```
4) Activate:
- macOS/Linux:
```bash
source .venv/bin/activate
```
- Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```
5) Install deps:
```bash
pip install -r requirements.txt
```
6) Install Ollama and pull models:
```bash
ollama pull deepseek-r1:70b
ollama pull llama3.3:70b
ollama pull qwen2.5-vl:7b
```
7) Run:
```bash
python -m reviewer.cli --input path/to/manuscript.pdf --rubric config/rubrics/core_rubric.json --out outputs/review.md --study_design diagnostic_accuracy --has_ai
```
