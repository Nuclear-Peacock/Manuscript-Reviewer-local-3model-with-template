@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ==========================================================
echo   Local Manuscript Reviewer - One-Click Launcher (Windows)
echo ==========================================================
echo This window will NOT auto-close.
echo.

REM --- Python present?
python --version >nul 2>&1
if errorlevel 1 goto PY_MISSING

REM --- Python >= 3.10?
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if errorlevel 1 goto PY_OLD

echo OK: Python detected.
echo.

REM --- Create venv if needed
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
  if errorlevel 1 goto VENV_FAIL
)

REM --- Activate venv
call ".venv\Scripts\activate.bat"
if errorlevel 1 goto VENV_ACTIVATE_FAIL

REM --- Install deps
echo Installing dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 goto PIP_FAIL

REM --- Ensure streamlit exists
python -c "import streamlit" >nul 2>&1
if errorlevel 1 (
  echo Installing Streamlit...
  python -m pip install streamlit
  if errorlevel 1 goto PIP_FAIL
)

REM --- Check Ollama running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 goto OLLAMA_DOWN

echo OK: Ollama running.
echo.

REM --- Ensure folders
if not exist "private_inputs" mkdir "private_inputs" >nul 2>&1
if not exist "outputs" mkdir "outputs" >nul 2>&1

REM --- Check required models (Balanced)
set "MISSING=0"
echo Checking required models (Balanced)...
call :CHECK_MODEL "deepseek-r1:32b"
call :CHECK_MODEL "llama3.3:70b"
call :CHECK_MODEL "qwen2.5vl:7b"

if "%MISSING%"=="1" (
  echo.
  echo Missing required models for the Balanced preset.
  echo You already have them? Then your installed tag names differ.
  echo.
  echo OPTION A (recommended): run setup_models.bat and choose option 1.
  echo OPTION B: run "ollama list" and compare exact tags.
  echo.
  choice /c YN /m "Open the model installer menu now?"
  if errorlevel 2 (
    echo Not opening installer.
  ) else (
    call "setup_models.bat"
  )
  echo.
  echo Re-checking models...
  set "MISSING=0"
  call :CHECK_MODEL "deepseek-r1:32b"
  call :CHECK_MODEL "llama3.3:70b"
  call :CHECK_MODEL "qwen2.5vl:7b"
  if "%MISSING%"=="1" (
    echo.
    echo Still missing. Run this and check the names:
    echo   ollama list
    echo.
    pause
    exit /b 1
  )
)

REM --- Launch Streamlit
if not exist "app.py" goto APP_MISSING

echo.
echo Starting UI at http://127.0.0.1:8501
start "" "http://127.0.0.1:8501"

python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501

echo.
echo App exited (or you closed it). Press any key to close.
pause
exit /b 0


:CHECK_MODEL
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

:VENV_ACTIVATE_FAIL
echo ERROR: Could not activate .venv
pause
exit /b 1

:PIP_FAIL
echo ERROR: Dependency install failed.
echo Try: python -m pip install -r requirements.txt
pause
exit /b 1

:OLLAMA_DOWN
echo ERROR: Ollama not reachable at http://localhost:11434
echo Start Ollama and try again.
pause
exit /b 1

:APP_MISSING
echo ERROR: app.py not found in this folder.
pause
exit /b 1
