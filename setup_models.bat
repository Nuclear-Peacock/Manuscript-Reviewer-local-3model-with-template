@echo off
setlocal
cd /d "%~dp0"

REM ----------------------------------------------------------
REM Non-interactive modes (called from run_ui.bat)
REM Usage:
REM   setup_models.bat recommended
REM   setup_models.bat best
REM   setup_models.bat all
REM   setup_models.bat list
REM ----------------------------------------------------------

if /I "%~1"=="recommended" goto RECOMMENDED
if /I "%~1"=="best" goto BEST
if /I "%~1"=="all" goto ALL
if /I "%~1"=="list" goto LIST

goto MENU


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

REM Verify Ollama is running
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
if "%CHOICE%"=="5" exit /b 0

echo.
echo Invalid choice. Please enter 1-5.
pause
goto MENU


:RECOMMENDED
echo.
echo [INFO] Installing Recommended (Minimal) models...
echo       Supports the Balanced preset + vision model.
echo.
set MODELS=deepseek-r1:32b llama3.3:70b qwen2.5vl:7b
goto INSTALL


:BEST
echo.
echo [INFO] Installing Best Quality models...
echo       Warning: very large downloads, requires strong GPU + disk.
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
if "%~1"=="" pause
exit /b 0


:INSTALL
REM Verify Ollama is running (again, for safety)
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Ollama is not reachable at http://localhost:11434
  if "%~1"=="" pause
  exit /b 1
)

for %%M in (%MODELS%) do (
  call :ENSURE_MODEL "%%M"
)

echo.
echo [DONE] Model setup complete.
if "%~1"=="" (
  pause
  goto MENU
)
exit /b 0


:ENSURE_MODEL
set "MODEL=%~1"

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
    if "%~1"=="" pause
    exit /b 1
  )
) else (
  echo [OK]   %MODEL% (already installed)
)

exit /b 0
