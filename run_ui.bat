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
    echo  1. I am opening the Python download page for you.
    echo  2. Download and run the "Windows Installer".
    echo  3. CRITICAL: Check the box "Add Python.exe to PATH"!
    echo.
    echo  NOTE: Windows cannot see the new Python installation
    echo        until you restart this launcher.
    echo.
    echo  >>> PLEASE RESTART THIS FILE AFTER INSTALLATION. <<<
    echo.
    timeout /t 5 >nul
    start https://www.python.org/downloads/
    pause
    exit /b
)

:: 2. If Python is good, run the seamless launcher
python launcher.py

:: 3. Catch crashes
if %errorlevel% neq 0 (
    echo.
    echo The app closed with an error.
    pause
)
