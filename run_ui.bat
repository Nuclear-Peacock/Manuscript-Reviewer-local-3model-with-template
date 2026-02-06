@echo off
title Manuscript Reviewer Launcher
echo Checking system requirements...

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    cls
    color 4F
    echo ========================================================
    echo  ERROR: Python is not installed (or not in your PATH)
    echo ========================================================
    echo.
    echo  This tool requires Python to run.
    echo  I am opening the download page for you now.
    echo.
    echo  INSTRUCTIONS:
    echo  1. Download the "Windows Installer".
    echo  2. Run the installer.
    echo  3. CRITICAL: Check the box "Add Python.exe to PATH" 
    echo     at the bottom of the first screen!
    echo.
    timeout /t 4 >nul
    start https://www.python.org/downloads/
    pause
    exit /b
)

:: 2. If Python is good, run the robust launcher
python launcher.py

:: 3. Catch crashes
if %errorlevel% neq 0 (
    echo.
    echo The app closed with an error.
    pause
)
