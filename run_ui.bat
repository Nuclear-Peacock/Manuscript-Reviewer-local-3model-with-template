@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   Local Manuscript Reviewer - One-Click Launcher (Windows)
echo ==========================================================
echo Localhost only. Manuscripts stay on your PC.
echo.

REM 1) Python exists?
python --version >nul 2>&1
if errorlevel 1 goto PY_MISSING

REM 2) Python >= 3.10?
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto PY_OLD

echo OK: Python found.
echo.

REM 3) Create venv if needed
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto VENV_FAIL
)

call ".venv\Scripts\activate.bat"

REM 4) Install deps
echo Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 goto PIP_FAIL

pip show streamlit >nul 2>&1
if errorlevel 1 (
  pip install streamlit
  if errorlevel 1 goto PIP_FAIL
)

REM 5) Ollama running?
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto OLLAMA_DOWN

echo OK: Ollama running.
echo.

REM 6) Ensure folders exist
if not exist "private_inputs" mkdir "private_inputs" >nul 2>&1
if not exist "outputs" mkdir "outputs" >nul 2>&1

REM 7) Check required models for Balanced (recommended)
set "MISSING=0"
echo Checking required models (Balanced)...
call :CHECK_MODEL "deepseek-r1:32b"
call :CHECK_MODEL "llama3.3:70b"
call :CHECK_MODEL "qwen2.5vl:7b"

REM LOOP BREAKER:
REM If setup_models launched us, it sets SKIP_MODEL_SETUP=1
REM In that case we must NOT call setup_models again.
if "%SKIP_MODEL_SETUP%"=="1" (
  if "%MISSING%"=="1" (
    echo.
    echo ERROR: Required models are still missing.
    echo Please run setup_models.bat and install the Recommended set.
    pause
    exit /b 1
  )
  goto START_UI
)

REM If missing and NOT skipping, offer to install
if "%MISSING%"=="1" (
  echo.
  echo Some required models are missing (or not detectable).
  echo.
  choice /c YN /m "Install recommended models now?"
  if errorlevel 2 (
    echo Skipping install. App may fail until models exist.
  ) else (
    if not exist "setup_models.bat" (
      echo ERROR: setup_models.bat not found.
      pause
      exit /b 1
    )

    call "setup_models.bat" recommended
    if errorlevel 1 (
      echo ERROR: model install failed.
      pause
      exit /b 1
    )

    set "MISSING=0"
    echo Re-checking required models...
    call :CHECK_MODEL "deepseek-r1:32b"
    call :CHECK_MODEL "llama3.3:70b"
    call :CHECK_MODEL "qwen2.5vl:7b"

    if "%MISSING%"=="1" (
      echo.
      echo ERROR: Models still not detected.
      echo Run: ollama list
      echo And confirm those exact tags exist:
      echo   deepseek-r1:32b
      echo   llama3.3:70b
      echo   qwen2.5vl:7b
      pause
      exit /b 1
    )
  )
)

:START_UI
echo.
echo Starting UI at http://127.0.0.1:8501
start "" "http://127.0.0.1:8501"
streamlit run app.py --server.address 127.0.0.1 --server.port 8501
exit /b 0


:CHECK_MODEL
REM Robust check: ollama show returns 0 if model exists locally
ollama show %~1 >nul 2>&1
if errorlevel 1 (
  echo MISSING: %~1
  set "MISSING=1"
) else (
  echo OK:      %~1
)
exit /b 0


:PY_MISSING
echo ERROR: Python not found.
echo Install Python 3.10+ and check "Add Python to PATH".
pause
exit /b 1

:PY_OLD
echo ERROR: Python is older than 3.10.
echo Install Python 3.10+.
pause
exit /b 1

:VENV_FAIL
echo ERROR: Could not create .venv
pause
exit /b 1

:PIP_FAIL
echo ERROR: Python dependency install failed.
pause
exit /b 1

:OLLAMA_DOWN
echo ERROR: Ollama not reachable at http://localhost:11434
echo Start Ollama and try again.
pause
exit /b 1

