@echo off
cd /d "%~dp0"

REM Always run the PowerShell launcher (more reliable than pure .bat)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_ui.ps1"

REM If PowerShell returns, keep this window open so you can read messages
echo.
echo Press any key to close...
pause >nul
