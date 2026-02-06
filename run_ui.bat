@echo off
title Manuscript Reviewer Launcher
echo Checking system requirements...

:: -----------------------------------------------------
:: ATTEMPT 1: Try the standard 'python' command
:: -----------------------------------------------------
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found 'python' command. Launching...
    python launcher.py
    goto :finished
)

:: -----------------------------------------------------
:: ATTEMPT 2: Try the Windows 'py' launcher
:: -----------------------------------------------------
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Found 'py' launcher. Launching...
    py launcher.py
    goto :finished
)

:: -----------------------------------------------------
:: FAILURE: Neither worked
:: -----------------------------------------------------
cls
color 4F
echo ========================================================
echo  ERROR: Python was not detected in your PATH
echo ========================================================
echo.
echo  It looks like Python IS installed, but the command-line
echo  cannot find it. This usually happens if the "Add to PATH"
echo  box was not checked during installation.
echo.
echo  QUICK FIX:
echo  1. Open the "App Execution Aliases" settings in Windows.
echo  2. Ensure "App Installer" (python.exe) is ON.
echo  
echo  OR REINSTALL:
echo  1. Uninstall Python.
echo  2. Reinstall it and check "Add Python to PATH" at the bottom.
echo.
echo  *** PLEASE RESTART THIS FILE AFTER FIXING ***
echo.
pause
exit /b

:finished
:: Catch crashes if the app itself fails
if %errorlevel% neq 0 (
    echo.
    echo The app closed with an error.
    pause
)
