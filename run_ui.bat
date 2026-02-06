@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Manuscript Reviewer Launcher

REM Always create outputs folder + log
if not exist "outputs" mkdir "outputs" >nul 2>&1
set "LOG=outputs\launcher.log"

echo ========================================================== > "%LOG%"
echo   Launcher Log                                            >> "%LOG%"
echo   %DATE% %TIME%                                           >> "%LOG%"
echo   Folder: %CD%                                            >> "%LOG%"
echo ========================================================== >> "%LOG%"
echo.                                                          >> "%LOG%"

echo ==========================================================
echo   Local Manuscript Reviewer - One-Click Launcher (Windows)
echo ==========================================================
echo This window WILL stay open when the script finishes.
echo Log file: %LOG%
echo.

set "RC=0"

REM -------------------------
REM 1) Python checks
REM -------------------------
python --version >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found.
  echo [ERROR] Python not found. >> "%LOG%" 2>&1
  set "RC=1"
  goto END
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] Python is older than 3.10.
  echo [ERROR] Python too old. >> "%LOG%" 2>&1
  set "RC=1"
  goto END
)

echo [OK] Python detected.
echo [OK] Python detected. >> "%LOG%" 2>&1
echo.

REM -------------------------
REM 2) Create venv if needed
REM -------------------------
if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  echo Creating venv... >> "%LOG%" 2>&1
  python -m venv .venv >> "%LOG%" 2>&1
  if errorlevel 1 (
    echo [ERROR] Could not create .venv
    echo [ERROR] venv create failed. >> "%LOG%" 2>&1
    set "RC=1"
    goto END
  )
)

REM -------------------------
REM 3) Activate venv
REM -------------------------
call ".venv\Scripts\activate.bat" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] Could not activate .venv
  echo [ERROR] venv activate failed. >> "%LOG%" 2>&1
  set "RC=1"
  goto END
)

REM -------------------------
REM 4) Install deps
REM -------------------------
echo Installing dependencies...
echo Installing dependencies... >> "%LOG%" 2>&1

python -m pip install --upgrade pip >> "%LOG%" 2>&1
python -m pip install -r requirements.txt >> "%LOG%" 2>&1
if errorlevel 1 (
  echo [ERROR] Dependency install failed. See log: %LOG%
  echo [ERROR] pip install -r requirements.txt failed. >> "%LOG%" 2>&1
  set "RC=1"
  goto END
)

python -c "import streamlit" >> "%LOG%" 2>&1
if errorlevel 1 (
  echo Installing Streamlit...
  echo Installing Streamlit... >> "%LOG%" 2>&1
  python -m pip install streamlit >> "%LOG%" 2>&1
  if errorleve

