@echo off
setlocal
cd /d "%~dp0"

REM ==========================================================
REM setup_models.bat
REM - Installs missing Ollama models
REM - Auto-launches run_ui.bat ONLY in interactive mode
REM - If called with args (recommended/best/fast/all/list), it does NOT launch UI
REM ==========================================================

REM Argument modes (non-interactive; NO auto-launch):
REM   setup_models.bat recommended
REM   setup_models.bat best
REM   setup_models.bat fast
REM   setup_models.bat all
REM   setup_models.bat list

if /I "%~1"=="recommended" goto RECOMMENDED_ARG
if /I "%~1"=="best" goto BEST_ARG
if /I "%~1"=="fast" goto FAST_ARG
if /I "%~1"=="all" goto ALL_ARG
if /I "%~1"=="list" goto LIST_ARG

goto MENU


:MENU
cls
echo ==========================================================
echo   Model Setup - Local Manuscript Reviewer (Ollama)
echo ==========================================================
echo.
echo This installs models locally (safe to re-run).
echo After installing (or confirming they already exist),
echo it will start the app automatically.
echo.
echo  1) Recommended (Balanced)
echo     deepseek-r1:32b + llama3.3:70b + qwen2.5vl:7b
echo.
echo  2) Best Quality (Very large)
echo     deepseek-r1:70b + llama3.3:70b + qwen2.5vl:7b
echo.
echo  3) Fast (Smaller / most compatible)
echo     deepseek-r1:14b + llama3.1:8b + qwen2.5vl:7b
echo.
echo  4) Install Everything (Largest)
echo.
echo  5) Show installed models
echo  6) Exit
echo.

call :CHECK_OLLAMA
if errorlevel 1 (
  pause
  exit /b 1
)

set /p CHOICE=Select an option (1-6): 

if "%CHOICE%"=="1" goto RECOMMENDED_UI
if "%CHOICE%"=="2" goto BEST_UI
if "%CHOICE%"=="3" goto FAST_UI
if "%CHOICE%"=="4" goto ALL_UI
if "%CHOICE%"=="5" goto LIST_UI
if "%CHOICE%"=="6" goto END

echo.
echo Invalid choice.
pause
goto MENU


REM =========================
REM UI (interactive) routes
REM =========================
:RECOMMENDED_UI
set MODELS=deepseek-r1:32b llama3.3:70b qwen2.5vl:7b
call :INSTALL_MODELS
if errorlevel 1 goto FAIL_UI
goto LAUNCH_UI

:BEST_UI
set MODELS=deepseek-r1:70b llama3.3:70b qwen2.5vl:7b
call :INSTALL_MODELS
if errorlevel 1 goto FAIL_UI
goto LAUNCH_UI

:FAST_UI
set MODELS=deepseek-r1:14b llama3.1:8b qwen2.5vl:7b
call :INSTALL_MODELS
if errorlevel 1 goto FAIL_UI
goto LAUNCH_UI

:ALL_UI
set MODELS=deepseek-r1:70b deepseek-r1:32b deepseek-r1:14b llama3.3:70b llama3.1:8b qwen2.5vl:7b
call :INSTALL_MODELS
if errorlevel 1 goto FAIL_UI
goto LAUNCH_UI

:LIST_UI
call :CHECK_OLLAMA
if errorlevel 1 (
  pause
  exit /b 1
)
echo.
echo Installed models:
echo.
ollama list
echo.
pause
goto LAUNCH_UI


REM =========================
REM ARG (non-interactive) routes
REM (install and EXIT; no launch)
REM =========================
:RECOMMENDED_ARG
set MODELS=deepseek-r1:32b llama3.3:70b qwen2.5vl:7b
call :INSTALL_MODELS
exit /b %errorlevel%

:BEST_ARG
set MODELS=deepseek-r1:70b llama3.3:70b qwen2.5vl:7b
call :INSTALL_MODELS
exit /b %errorlevel%

:FAST_ARG
set MODELS=deepseek-r1:14b llama3.1:8b qwen2.5vl:7b
call :INSTALL_MODELS
exit /b %errorlevel%

:ALL_ARG
set MODELS=deepseek-r1:70b deepseek-r1:32b deepseek-r1:14b llama3.3:70b llama3.1:8b qwen2.5vl:7b
call :INSTALL_MODELS
exit /b %errorlevel%

:LIST_ARG
call :CHECK_OLLAMA
if errorlevel 1 exit /b 1
ollama list
exit /b 0


REM =========================
REM Helpers
REM =========================
:INSTALL_MODELS
call :CHECK_OLLAMA
if errorlevel 1 exit /b 1

echo.
echo Installing models (only missing ones will download):
echo.

for %%M in (%MODELS%) do (
  call :ENSURE_MODEL "%%M"
  if errorlevel 1 exit /b 1
)

echo.
echo DONE. Model setup complete.
echo.
exit /b 0


:ENSURE_MODEL
set "MODEL=%~1"
ollama list | findstr /i /r "^%MODEL%[ ]" >nul 2>&1
if errorlevel 1 (
  echo PULL  %MODEL%
  ollama pull %MODEL%
  if errorlevel 1 (
    echo ERROR pulling %MODEL%
    exit /b 1
  )
) else (
  echo OK    %MODEL%
)
exit /b 0


:CHECK_OLLAMA
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo.
  echo ERROR: Ollama is not reachable at http://localhost:11434
  echo Start Ollama, then re-run.
  echo.
  exit /b 1
)
exit /b 0


:LAUNCH_UI
echo Launching the app now...
echo.

if not exist "run_ui.bat" (
  echo ERROR: run_ui.bat not found in this folder.
  pause
  exit /b 1
)

call "run_ui.bat"

echo.
echo App exited (or you closed it). Press any key to close this window.
pause
exit /b 0


:FAIL_UI
echo.
echo Setup failed. Fix the error above and re-run setup_models.bat.
pause
goto MENU


:END
exit /b 0
