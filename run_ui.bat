@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

echo ==========================================================
echo   Local Manuscript Reviewer - One-Click Launcher (Windows)
echo   Localhost only (no tunnel). Manuscripts stay on your PC.
echo ==========================================================
echo.

REM -------------------------
REM 1) Check Python exists
REM -------------------------
python --version >nul 2>&1
if errorlevel 1 (
  echo [WARN] Python is not installed (or not on PATH).
  echo.
  echo We can try to install Python automatically using Windows Package Manager (winget).
  echo.
  choice /c YN /m "Install Python 3.11 automatically now? (recommended)"
  if errorlevel 2 (
    echo.
    echo [ACTION NEEDED] Please install Python 3.10 or newer, then re-run run_ui.bat.
    echo Tip: During install, check: "Add Python to PATH".
    pause
    exit /b 1
  )

  winget --version >nul 2>&1
  if errorlevel 1 (
    echo.
    echo [ERROR] winget is not available on this computer.
    echo Please install Python 3.10+ manually, then re-run run_ui.bat.
    echo Tip: During install, check: "Add Python to PATH".
    pause
    exit /b 1
  )

  echo [INFO] Installing Python 3.11 via winget...
  winget install -e --id Python.Python.3.11
  if errorlevel 1 (
    echo.
    echo [ERROR] Automatic install failed (may require admin approval or be blocked).
    echo Please install Python 3.10+ manually, then re-run run_ui.bat.
    pause
    exit /b 1
  )

  echo.
  echo [INFO] Python installed. Please close this window and run run_ui.bat again.
  pause
  exit /b 0
)

REM -------------------------
REM 2) Check Python version >= 3.10
REM -------------------------
for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do set PYVER=%%V
for /f "tokens=1,2 delims=." %%A in ("%PYVER%") do (
  set PYMAJ=%%A
  set PYMIN=%%B
)

if NOT "%PYMAJ%"=="3" (
  echo [ERROR] Python 3.10+ is required. Found: %PYVER%
  pause
  exit /b 1
)

if %PYMIN% LSS 10 (
  echo [WARN] Python 3.10+ is required. Found: %PYVER%
  echo.
  choice /c YN /m "Upgrade Python automatically using winget now? (recommended)"
  if errorlevel 2 (
    echo.
    echo [ACTION NEEDED] Please install Python 3.10+ manually, then re-run run_ui.bat.
    pause
    exit /b 1
  )

  winget --version >nul 2>&1
  if errorlevel 1 (
    echo.
    echo [ERROR] winget is not available on this computer.
    echo Please install Python 3.10+ manually, then re-run run_ui.bat.
    pause
    exit /b 1
  )

  echo [INFO] Upgrading Python via winget...
  winget install -e --id Python.Python.3.11
  if errorlevel 1 (
    echo.
    echo [ERROR] Automatic upgrade failed (may require admin approval or be blocked).
    echo Please install Python 3.10+ manually, then re-run run_ui.bat.
    pause
    exit /b 1
  )

  echo.
  echo [INFO] Python upgraded. Please close this window and run run_ui.bat again.
  pause
  exit /b 0
)

echo [OK] Python %PYVER% detected.
echo.

REM -------------------------
REM 3) Create / activate venv
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
REM 4) Install deps (idempotent)
REM -------------------------
echo [INFO] Installing/updating dependencies (first run may take a few minutes)...
pip install -r requirements.txt >nul
if errorlevel 1 (
  echo [ERROR] pip install failed.
  echo Try running:
  echo   .venv\Scripts\python.exe -m pip install --upgrade pip
  echo Then re-run run_ui.bat
  pause
  exit /b 1
)

pip show streamlit >nul 2>&1
if errorlevel 1 (
  echo [INFO] Installing Streamlit...
  pip install streamlit >nul
)

REM -------------------------
REM 5) Check Ollama
REM -------------------------
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Ollama is not reachable at http://localhost:11434
  echo         Start Ollama, then re-run run_ui.bat
  pause
  exit /b 1
)

REM -------------------------
REM 6) Optional: models check + install (calls setup_models.bat)
REM -------------------------
set NEED_MODELS=deepseek-r1:70b deepseek-r1:32b deepseek-r1:14b llama3.3:70b llama3.3:32b qwen2.5vl:7b
set MISSING_ANY=0

if exist "%TEMP%\ollama_models_ui.txt" del "%TEMP%\ollama_models_ui.txt" >nul 2>&1
for /f "delims=" %%A in ('ollama list 2^>nul') do (
  echo %%A | findstr /i /c:"NAME" >nul
  if errorlevel 1 (
    for /f "tokens=1" %%X in ("%%A") do echo %%X>> "%TEMP%\ollama_models_ui.txt"
  )
)
if not exist "%TEMP%\ollama_models_ui.txt" type nul > "%TEMP%\ollama_models_ui.txt"

echo [INFO] Checking required models...
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
  choice /c YN /m "Install missing models now? (recommended)"
  if errorlevel 1 (
    if exist setup_models.bat (
      call setup_models.bat
    )
  )
)

REM -------------------------
REM 7) Ensure private_inputs exists
REM -------------------------
if not exist private_inputs (
  mkdir private_inputs >nul 2>&1
)

REM -------------------------
REM 8) Auto-open browser + start UI
REM -------------------------
echo.
echo [INFO] Starting UI (localhost only)...
echo       Opening: http://127.0.0.1:8501
start "" "http://127.0.0.1:8501"
streamlit run app.py --server.address 127.0.0.1 --server.port 8501
