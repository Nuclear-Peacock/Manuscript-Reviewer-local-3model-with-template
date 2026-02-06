@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

REM Check Python (optional if already installed)
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found. Install Python 3.10+ or add it to PATH, then re-run.
  pause
  exit /b 1
)

REM Create venv if needed
if not exist .venv\Scripts\python.exe (
  echo [INFO] Creating virtual environment...
  python -m venv .venv
)

call .venv\Scripts\activate.bat

REM Install deps (idempotent)
echo [INFO] Installing/updating dependencies...
pip install -r requirements.txt
pip install streamlit

REM Check Ollama (optional if already installed/running)
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Ollama is not reachable at http://localhost:11434
  echo         Please install/start Ollama, then re-run.
  pause
  exit /b 1
)

echo [INFO] Starting UI (localhost only)...
streamlit run app.py --server.address 127.0.0.1 --server.port 8501
