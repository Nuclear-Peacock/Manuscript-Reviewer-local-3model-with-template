@echo off
setlocal
cd /d "%~dp0"

echo ==========================================================
echo   Model Setup - Local Manuscript Reviewer (Ollama)
echo ==========================================================
echo.

REM 1) Verify Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Ollama is not reachable at http://localhost:11434
  echo         Please start Ollama, then run setup_models.bat again.
  pause
  exit /b 1
)

echo [OK] Ollama is running.
echo.

REM 2) List of models used by the UI presets
set MODELS=deepseek-r1:70b deepseek-r1:32b deepseek-r1:14b llama3.3:70b llama3.3:32b qwen2.5vl:7b

echo This will install only missing models. Safe to re-run.
echo.

REM 3) Pull missing models (simple and reliable)
for %%M in (%MODELS%) do (
  call :ENSURE_MODEL "%%M"
)

echo.
echo [DONE] Model setup complete.
echo You can now run: run_ui.bat
pause
exit /b 0


:ENSURE_MODEL
set "MODEL=%~1"

REM Check if model exists (matches beginning of line in 'ollama list')
ollama list | findstr /i /r "^%MODEL%[ ]" >nul 2>&1
if errorlevel 1 (
  echo [PULL] %MODEL%
  ollama pull %MODEL%
  if errorlevel 1 (
    echo [ERROR] Failed to pull %MODEL%
    echo         Check internet, disk space, or model name availability.
    pause
    exit /b 1
  )
) else (
  echo [OK]   %MODEL% (already installed)
)

exit /b 0
