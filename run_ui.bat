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
REM 3) Create venv if needed, then activate
REM -------------------------
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto VENV_FAIL
)

call ".venv\Scripts\activate.bat"

REM -------------------------
REM 4) Install dependencies (idempotent)
REM -------------------------
echo [INFO] Installing/updating dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 goto PIP_FAIL

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
REM 6) Ensure folders exist
REM -------------------------
if not exist "private_inputs" mkdir "private_inputs" >nul 2>&1
if not exist "outputs" mkdir "outputs" >nul 2>&1

REM -------------------------
REM 7) Check REQUIRED models (Recommended / Balanced preset)
REM    If missing, offer to auto-install and then continue
REM -------------------------
set "MISSING=0"
echo [INFO] Checking required models for Recommended (Balanced) preset...
call :CHECK_MODEL "deepseek-r1:32b"
call :CHECK_MODEL "llama3.3:70b"
call :CHECK_MODEL "qwen2.5vl:7b"

if "%MISSING%"=="1" (
  echo.
  echo [ACTION] Required models for Recommended (Balanced) are missing.
  echo         If this is your first run, this is normal.
  echo.
  choice /c YN /m "Install the recommended models now and continue automatically?"
  if errorlevel 2 (
    echo [INFO] Skipping model install. The app may fail until models are installed.
  ) else (
    if not exist "setup_models.bat" (
      echo [ERROR] setup_models.bat not found in this folder.
      pause
      exit /b 1
    )

    REM Non-interactive mode (recommended)
    call "setup_models.bat" recommended
    if errorlevel 1 (
      echo [ERROR] Model installation failed.
      pause
      exit /b 1
    )

    REM Re-check after install
    set "MISSING=0"
    echo.
    echo [INFO] Re-checking required models after install...
    call :CHECK_MODEL "deepseek-r1:32b"
    call :CHECK_MODEL "llama3.3:70b"
    call :CHECK_MODEL "qwen2.5vl:7b"
    if "%MISSING%"=="1" (
      echo.
      echo [ERROR] Some recommended models are still missing.
      echo         Please run setup_models.bat manually and choose Option 1.
      pause
      exit /b 1
    )
  )
)

REM -------------------------
REM 8) OPTIONAL: Check Fast/Best extras (do not block)
REM -------------------------
echo.
echo [INFO] Optional model availability (for dropdown presets):
call :CHECK_MODEL_OPTIONAL "deepseek-r1:14b"
call :CHECK_MODEL_OPTIONAL "llama3.1:8b"
call :CHECK_MODEL_OPTIONAL "deepseek-r1:70b"
echo.

REM -------------------------
REM 9) Auto-open browser + start UI (localhost only)
REM -------------------------
echo [INFO] Starting UI (localhost only)...
echo       Opening: http://127.0.0.1:8501
start "" "http://127.0.0.1:8501"
streamlit run app.py --server.address 127.0.0.1 --server.port 8501
exit /b 0


REM -------------------------
REM Subroutine: required model check
REM -------------------------
:CHECK_MODEL
ollama list | findstr /i /r "^%~1[ ]" >nul 2>&1
if errorlevel 1 (
  echo [MISSING] %~1
  set "MISSING=1"
) else (
  echo [OK]      %~1
)
exit /b 0


REM -------------------------
REM Subroutine: optional model check (does not set MISSING)
REM -------------------------
:CHECK_MODEL_OPTIONAL
ollama list | findstr /i /r "^%~1[ ]" >nul 2>&1
if errorlevel 1 (
  echo [OPTIONAL MISSING] %~1
) else (
  echo [OPTIONAL OK]      %~1
)
exit /b 0


REM -------------------------
REM Errors
REM -------------------------
:PY_MISSING
echo [ERROR] Python not found.
echo         Install Python 3.10+ and check "Add Python to PATH".
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
echo         Check internet access and try again.
pause
exit /b 1

:OLLAMA_DOWN
echo [ERROR] Ollama is not reachable at http://localhost:11434
echo         Start Ollama, then run run_ui.bat again.
pause
exit /b 1

