@echo off
title Manuscript Reviewer Launcher
echo Starting Launcher...

:: Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in your PATH.
    echo Please install Python 3.10+ and check "Add to PATH" during installation.
    pause
    exit /b
)

:: Run the robust launcher
python launcher.py

:: If launcher exits abnormally, pause so user can see why
if %errorlevel% neq 0 (
    echo.
    echo The app closed with an error.
    pause
)
