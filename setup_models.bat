@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

REM ---- Config: list the models you support in the UI ----
set MODELS=deepseek-r1:70b deepseek-r1:32b deepseek-r1:14b llama3.3:70b llama3.3:32b qwen2.5vl:7b

REM ---- Check Ollama running ----
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Ollama is not reachable at http://localhost:11434
  echo         1) Install Ollama (if needed)
  echo         2) Start Ollama
  echo         3) Re-run setup_models.bat
  pause
  exit /b 1
)

echo [INFO] Ollama is running.
echo.

REM ---- Get list of installed models ----
for /f "delims=" %%A in ('ollama list 2^>nul') do (
  echo %%A | findstr /i /c:"NAME" >nul
  if errorlevel 1 (
    REM store installed model names in a temp file
    echo %%A>> "%TEMP%\ollama_models_tmp.txt"
  )
)

REM If the temp file doesn't exist or is empty, we still proceed to pulls
if not exist "%TEMP%\ollama_models_tmp.txt" (
  type nul > "%TEMP%\ollama_models_tmp.txt"
)

echo [INFO] Checking required models...
echo.

REM ---- Function-like: check if a model is installed (by exact prefix match) ----
REM We'll parse "ollama list" lines; the model name is the first token on each line.
REM Example line: llama3.3:70b   123abc...   42 GB   2 days ago

set MISSING=0

for %%M in (%MODELS%) do (
  set FOUND=0
  for /f "tokens=1" %%X in (%TEMP%\ollama_models_tmp.txt) do (
    if /I "%%X"=="%%M" set FOUND=1
  )

  if "!FOUND!"=="1" (
    echo [OK]    %%M (already installed)
  ) else (
    echo [PULL]  %%M (not installed)
    set /a MISSING+=1
    ollama pull %%M
    if errorlevel 1 (
      echo [ERROR] Failed to pull %%M
      echo         You may be out of disk space, offline, or the model name may be unavailable.
      del "%TEMP%\ollama_models_tmp.txt" >nul 2>&1
      pause
      exit /b 1
    )
  )
)

del "%TEMP%\ollama_models_tmp.txt" >nul 2>&1

echo.
if "%MISSING%"=="0" (
  echo [DONE] All models were already installed.
) else (
  echo [DONE] Pulled %MISSING% missing model(s).
)
echo.
echo You can now run: run_ui.bat
pause
