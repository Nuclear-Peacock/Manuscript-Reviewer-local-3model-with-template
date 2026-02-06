@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   Local Manuscript Reviewer - One-Click Launcher (Windows)
echo   Localhost only (no tunnel). Manuscripts stay on your PC.
echo ==========================================================
echo.

REM -------------------------
REM 1) Check Python exists
REM -------------------------
python --version >nul 2>&1
if errorlevel 1 goto PY_MISSING

REM -------------------------
REM 2) Check Python version >= 3.10 (using Python, no batch parsing)
REM -------------------------
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto PY_OLD

echo [OK] Python is installed and compatible.
echo.

REM -------------------------
REM 3) Create venv if needed
REM -------------------------
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto VENV_FAIL
)

call ".venv\Scripts\activate.bat"

REM -------------------------
REM 4) Install dependencies (first run may take a few minutes)
REM -------------------------
echo [INFO] Installing/updating dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 goto PIP_FAIL

REM Ensure Streamlit is installed
pip show streamlit >nul 2>&1
if errorlevel 1 (
  echo [INFO] Installing Streamlit...
  pip install streamlit
  if errorlevel 1 goto PIP_FAIL
)

REM -------------------------
REM 5) Check Ollama is running
REM -------------------------
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto OLLAMA_DOWN

echo [OK] Ollama is running.
echo.

REM -------------------------
REM 6) Check required models; offer to install missing ones
REM -------------------------
set "MISSING=0"
echo [INFO] Checking required local models...
call :CHECK_MODEL "deepseek-r1:70b"
call :CHECK_MODEL "deepseek-r1:32b"
call :CHECK_MODEL "deepseek-r1:14b"
call :CHECK_MODEL "llama3.3:70b"
call :CHECK_MODEL "llama3.3:32b"
call :CHECK_MODEL "qwen2.5vl:7b"

if "%MISSING%"=="1" (
  echo.
  choice /c YN /m "Some models are missing. Install missing models now? (recommended)"
  if errorlevel 2 goto START_UI
  if exist "setup_models.bat" (
    call "setup_models.bat"
  ) else (
    echo [ERROR] setup_models.bat not found in this folder.
    pause
    exit /b 1
  )
)

REM -------------------------
REM 7) Ensure private_inputs folder exists
REM -------------------------
if not exist "private_inputs" mkdir "private_inputs" >nul 2>&1

REM -------------------------
REM 8) Auto-open browser + start UI (localhost only)
REM -------------------------
:START_UI
echo.
echo [INFO] Starting UI (localhost only)...
echo       Opening: http://127.0.0.1:8501
start "" "http://127.0.0.1:8501"
streamlit run app.py --server.address 127.0.0.1 --server.port 8501
exit /b 0

REM -------------------------
REM Subroutine: model check
REM -------------------------
:CHECK_MODEL
REM Finds model name at start of a line from `ollama list`
ollama list | findstr /i /r "^%~1[ ]" >nul 2>&1
if errorlevel 1 (
  echo [MISSING] %~1
  set "MISSING=1"
) else (
  echo [OK]      %~1
)
exit /b 0

REM -------------------------
REM Errors
REM -------------------------
:PY_MISSING
echo [ERROR] Python not found.
echo         Please install Python 3.10+ and check "Add Python to PATH".
echo         Then run run_ui.bat again.
pause
exit /b 1

:PY_OLD
echo [ERROR] Python is installed but older than 3.10.
echo         Please install Python 3.10+ and run run_ui.bat again.
pause
exit /b 1

:VENV_FAIL
echo [ERROR] Failed to create the virtual environment.
pause
exit /b 1

:PIP_FAIL
echo [ERROR] Failed to install Python dependencies.
echo         Check your internet connection and try again.
pause
exit /b 1

:OLLAMA_DOWN
echo [ERROR] Ollama is not reachable at http://localhost:11434
echo         Start Ollama, then run run_ui.bat again.
pause
exit /b 1
