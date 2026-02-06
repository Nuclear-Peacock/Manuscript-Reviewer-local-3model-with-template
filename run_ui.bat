@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

echo ==========================================================
echo   Local Manuscript Reviewer - One-Click Launcher (Windows)
echo   Localhost only (no tunnel). Manuscripts stay on your PC.
echo ==========================================================
echo.

REM -------------------------
REM 1) Check Python
REM -------------------------
python --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found.
  echo         Install Python 3.10+ and be sure "Add Python to PATH" is checked.
  echo         Then re-run this file.
  echo.
  pause
  exit /b 1
)

REM -------------------------
REM 2) Create / activate venv
REM -------------------------
if not exist .venv\Scripts\python.exe (
  echo [INFO] Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create venv.
    pause
    exit /b 1
  )
)

call .venv\Scripts\activate.bat

REM -------------------------
REM 3) Install deps (idempotent)
REM -------------------------
echo [INFO] Installing/updating Python dependencies (first run may take a few minutes)...
pip install -r requirements.txt >nul
if errorlevel 1 (
  echo [ERROR] pip install -r requirements.txt failed.
  echo         Try: pip install --upgrade pip
  pause
  exit /b 1
)

pip show streamlit >nul 2>&1
if errorlevel 1 (
  echo [INFO] Installing Streamlit...
  pip install streamlit >nul
)

REM -------------------------
REM 4) Check Ollama running
REM -------------------------
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Ollama is not reachable at http://localhost:11434
  echo         - Install Ollama (if needed)
  echo         - Start Ollama
  echo         - Then re-run this file
  echo.
  pause
  exit /b 1
)

REM -------------------------
REM 5) Check models installed; offer to install if missing
REM -------------------------
set NEED_MODELS=deepseek-r1:70b deepseek-r1:32b deepseek-r1:14b llama3.3:70b llama3.3:32b qwen2.5vl:7b
set MISSING_ANY=0

REM capture installed model names (first token per line)
if exist "%TEMP%\ollama_models_ui.txt" del "%TEMP%\ollama_models_ui.txt" >nul 2>&1
for /f "delims=" %%A in ('ollama list 2^>nul') do (
  echo %%A | findstr /i /c:"NAME" >nul
  if errorlevel 1 (
    for /f "tokens=1" %%X in ("%%A") do echo %%X>> "%TEMP%\ollama_models_ui.txt"
  )
)
if not exist "%TEMP%\ollama_models_ui.txt" type nul > "%TEMP%\ollama_models_ui.txt"

echo [INFO] Checking required local models...
for %%M in (%NEED_MODELS%) do (
  set FOUND=0
  for /f "delims=" %%X in (%TEMP%\ollama_models_ui.txt) do (
    if /I "%%X"=="%%M" set FOUND=1
  )
  if "!FOUND!"=="0" (
    echo   - Missing: %%M
    set MISSING_ANY=1
  )
)

del "%TEMP%\ollama_models_ui.txt" >nul 2>&1

if "%MISSING_ANY%"=="1" (
  echo.
  echo [ACTION] Some required models are missing.
  echo         This is normal on first setup.
  echo.
  choice /c YN /m "Install missing models now? (recommended)"
  if errorlevel 2 (
    echo [INFO] Skipping model install. The app may fail until models are installed.
  ) else (
    if exist setup_models.bat (
      call setup_models.bat
    ) else (
      echo [ERROR] setup_models.bat not found in this folder.
      pause
      exit /b 1
    )
  )
)

REM -------------------------
REM 6) Ensure private_inputs exists
REM -------------------------
if not exist private_inputs (
  mkdir private_inputs >nul 2>&1
)

REM -------------------------
REM 7) Launch local-only UI
REM -------------------------
echo.
echo [INFO] Starting UI (localhost
