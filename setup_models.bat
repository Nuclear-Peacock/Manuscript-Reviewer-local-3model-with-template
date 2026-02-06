@echo off
setlocal
cd /d "%~dp0"

REM ==========================================================
REM Model Setup - Local Manuscript Reviewer (Ollama)
REM - Menu mode (double-click)
REM - Non-interactive mode (called from run_ui.bat):
REM     setup_models.bat recommended
REM     setup_models.bat best
REM     setup_models.bat fast
REM     setup_models.bat all
REM     setup_models.bat list
REM ==========================================================

REM ---- Non-interactive modes ----
if /I "%~1"=="recommended" goto RECOMMENDED
if /I "%~1"=="best"        goto BEST
if /I "%~1"=="fast"        goto FAST
if /I "%~1"=="all"         goto ALL
if /I "%~1"=="list"        goto LIST

goto MENU


:MENU
cls
echo ==========================================================
echo   Model Setup - Local Manuscript Reviewer (Ollama)
echo ==========================================================
echo.
echo This installs local models for the app. Safe to re-run.
echo Nothing is uploaded; models are downloaded to your computer.
echo.
echo  1) Recommended (Balanced) - deepseek-r1:32b + llama3.3:70b + qwen2.5vl:7b
echo  2) Best Quality           - deepseek-r1:70b + llama3.3:70b + qwen2.5vl:7b (very large)
echo  3) Fast (Smaller)         - deepseek-r1:14b + llama3.1:8b  + qwen2.5vl:7b
echo  4) Install Everything     - all presets (largest)
echo  5) Show installed models
echo  6) Exit
echo.

call :CHECK_OLLAMA
if errorlevel 1 (
  pause
  exit /b 1
)

set /p CHOICE=Select an option (1-6): 

if "%CHOICE%"=="1" goto RECOMMENDED
if "%CHOICE%"=="2" goto BEST
if "%CHOICE%"=="3" goto FAST
if "%CHOICE%"=="4" goto ALL
if "%CHOICE%"=="5" goto LIST
if "%CHOICE%"=="6" goto END

echo.
echo Invalid choice. Please enter 1-6.
pause
goto MENU


:RECOMMENDED
echo.
echo [INFO] Installing Recommended (Balanced) models...
echo.
set MODELS=deepseek-r1:32b llama3.3:70b qwen2.5vl:7b
goto INSTALL


:BEST
echo.
echo [INFO] Installing Best Quality models...
echo       Warning: very large downloads. Needs lots of disk and a strong GPU for speed.
echo.
set MODELS=deepseek-r1:70b llama3.3:70b qwen2.5vl:7b
goto INSTALL


:FAST
echo.
echo [INFO] Installing Fast (Smaller) models...
echo       This is the most compatible preset for many machines.
echo.
set MODELS=deepseek-r1:14b llama3.1:8b qwen2.5vl:7b
goto INSTALL


:ALL
echo.
echo [INFO] Installing EVERYTHING (largest)...
echo       This pulls Balanced + Best + Fast models.
echo.
set MODELS=deepseek-r1:70b deepseek-r1:32b deepseek-r1:14b llama3.3:70b llama3.1:8b qwen2.5vl:7b
goto INSTALL


:LIST
echo.
call :CHECK_OLLAMA
if errorlevel 1 (
  if "%~1"=="" pause
  exit /b 1
)
echo [INFO] Installed models:
echo.
ollama list
echo.
if "%~1"=="" pause
exit /b 0


:INSTALL
call :CHECK_OLLAMA
if errorlevel 1 (
  if "%~1"=="" pause
  exit /b 1
)

echo This will install only missing models. Safe to re-run.
echo.

for %%M in (%MODELS%) do (
  call :ENSURE_MODEL "%%M"
  if errorlevel 1 (
    if "%~1"=="" pause
    exit /b 1
  )
)

echo.
echo [DONE] Model setup complete.
echo You can now run: run_ui.bat
echo.
if "%~1"=="" (
  pause
  goto MENU
)
exit /b 0


:ENSURE_MODEL
set "MODEL=%~1"

REM Check if installed (model name at start of line in `ollama list`)
ollama list | findstr /i /r "^%MODEL%[ ]" >nul 2>&1
if errorlevel 1 (
  echo [PULL] %MODEL%
  ollama pull %MODEL%
  if errorlevel 1 (
    echo.
    echo [ERROR] Failed to pull %MODEL%
    echo         - Check internet connection
    echo         - Check free disk space
    echo         - The model tag may differ in your Ollama version
    echo.
    exit /b 1
  )
) else (
  echo [OK]   %MODEL% (already installed)
)

exit /b 0


:CHECK_OLLAMA
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo.
  echo [ERROR] Ollama is not reachable at http://localhost:11434
  echo         Start Ollama, then run setup_models.bat again.
  echo.
  exit /b 1
)
exit /b 0


:END
exit /b 0

