@echo off
setlocal
cd /d "%~dp0"

REM Non-interactive modes:
REM   setup_models.bat recommended
REM   setup_models.bat best
REM   setup_models.bat fast
REM   setup_models.bat all
REM   setup_models.bat list

if /I "%~1"=="recommended" goto RECOMMENDED
if /I "%~1"=="best" goto BEST
if /I "%~1"=="fast" goto FAST
if /I "%~1"=="all" goto ALL
if /I "%~1"=="list" goto LIST

goto MENU


:MENU
cls
echo ==========================================================
echo   Model Setup - Local Manuscript Reviewer (Ollama)
echo ==========================================================
echo.
echo Safe to re-run. Installs only missing models.
echo.
echo  1) Recommended (Balanced)
echo     - deepseek-r1:32b
echo     - llama3.3:70b
echo     - qwen2.5vl:7b
echo.
echo  2) Best Quality (Very large)
echo     - deepseek-r1:70b
echo     - llama3.3:70b
echo     - qwen2.5vl:7b
echo.
echo  3) Fast (Smaller / most compatible)
echo     - deepseek-r1:14b
echo     - llama3.1:8b
echo     - qwen2.5vl:7b
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

if "%CHOICE%"=="1" goto RECOMMENDED
if "%CHOICE%"=="2" goto BEST
if "%CHOICE%"=="3" goto FAST
if "%CHOICE%"=="4" goto ALL
if "%CHOICE%"=="5" goto LIST
if "%CHOICE%"=="6" goto END

echo.
echo Invalid choice.
pause
goto MENU


:RECOMMENDED
set MODELS=deepseek-r1:32b llama3.3:70b qwen2.5vl:7b
goto INSTALL

:BEST
set MODELS=deepseek-r1:70b llama3.3:70b qwen2.5vl:7b
goto INSTALL

:FAST
set MODELS=deepseek-r1:14b llama3.1:8b qwen2.5vl:7b
goto INSTALL

:ALL
set MODELS=deepseek-r1:70b deepseek-r1:32b deepseek-r1:14b llama3.3:70b llama3.1:8b qwen2.5vl:7b
goto INSTALL


:LIST
call :CHECK_OLLAMA
if errorlevel 1 (
  if "%~1"=="" pause
  exit /b 1
)
echo.
echo Installed models:
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

echo.
echo Installing (only missing):
for %%M in (%MODELS%) do (
  call :ENSURE_MODEL "%%M"
  if errorlevel 1 (
    if "%~1"=="" pause
    exit /b 1
  )
)

echo.
echo DONE. Models installed.
echo You can run: run_ui.bat
echo.
if "%~1"=="" (
  pause
  goto MENU
)
exit /b 0


:ENSURE_MODEL
set "MODEL=%~1"
ollama list | findstr /i /r "^%MODEL%[ ]" >nul 2>&1
if errorlevel 1 (
  echo PULL  %MODEL%
  ollama pull %MODEL%
  if errorlevel 1 (
    echo.
    echo ERROR: Failed to pull %MODEL%
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
  echo ERROR: Ollama not reachable at http://localhost:11434
  echo Start Ollama, then re-run.
  echo.
  exit /b 1
)
exit /b 0


:END
exit /b 0
