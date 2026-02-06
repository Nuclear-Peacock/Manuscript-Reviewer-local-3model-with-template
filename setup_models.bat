@echo off
setlocal
cd /d "%~dp0"

:MENU
cls
echo ==========================================================
echo   Model Setup - Local Manuscript Reviewer (Ollama)
echo ==========================================================
echo.
echo This installs local models for the app. Safe to re-run.
echo.
echo  1) Recommended (Minimal)  - Balanced preset + vision model
echo  2) Best Quality           - Best preset + vision model (very large)
echo  3) Install Everything     - All presets (largest)
echo  4) Show installed models
echo  5) Exit
echo.

REM Verify Ollama is running before doing anything
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Ollama is not reachable at http://localhost:11434
  echo         Start Ollama, then run setup_models.bat again.
  echo.
  pause
  exit /b 1
)

set /p CHOICE=Select an option (1-5): 

if "%CHOICE%"=="1" goto RECOMMENDED
if "%CHOICE%"=="2" goto BEST
if "%CHOICE%"=="3" goto ALL
if "%CHOICE%"=="4" goto LIST
if "%CHOICE%"=="5" goto END

echo.
echo Invalid choice. Please enter 1-5.
pause
goto MENU


:RECOMMENDED
echo.
echo [INFO] Installing Recommended (Minimal) models...
echo       This supports the Balanced preset (and usually runs well on many GPUs).
echo.
set MODELS=deepseek-r1:32b llama3.3:70b qwen2.5vl:7b
goto INSTALL


:BEST
echo.
echo [INFO] Installing Best Quality models...
echo       Warning: this can be very large and may require a strong GPU + lots of disk.
echo.
set MODELS=deepseek-r1:70b llama3.3:70b qwen2.5vl:7b
goto INSTALL


:ALL
echo.
echo [INFO] Installing ALL supported models (largest)...
echo.
set MODELS=deepseek-r1:70b deepseek-r1:32b deepseek-r1:14b llama3.3:70b llama3.3:32b qwen2.5vl:7b
goto INSTALL


:LIST
echo.
echo [INFO] Installed models:
echo.
ollama list
echo.
pause
goto MENU


:INSTALL
REM Pull each model if missing
for %%M in (%MODELS%) do (
  call :ENSURE_MODEL "%%M"
)

echo.
echo [DONE] Model setup complete.
echo You can now run: run_ui.bat
echo.
pause
goto MENU


:ENSURE_MODEL
set "MODEL=%~1"

REM Check if installed
ollama list | findstr /i /r "^%MODEL%[ ]" >nul 2>&1
if errorlevel 1 (
  echo [PULL] %MODEL%
  ollama pull %MODEL%
  if errorlevel 1 (
    echo.
    echo [ERROR] Failed to pull %MODEL%
    echo         - Check internet connection
    echo         - Check free disk space
    echo         - Model name/tag may differ in your Ollama version
    echo.
    pause
    exit /b 1
  )
) else (
  echo [OK]   %MODEL% (already installed)
)

exit /b 0


:END
exit /b 0
