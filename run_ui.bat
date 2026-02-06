REM -------------------------
REM 6) Check required models; if missing, auto-install recommended and continue
REM -------------------------
set "MISSING=0"
echo [INFO] Checking required local models...
call :CHECK_MODEL "deepseek-r1:32b"
call :CHECK_MODEL "llama3.3:70b"
call :CHECK_MODEL "qwen2.5vl:7b"

if "%MISSING%"=="1" (
  echo.
  echo [ACTION] Required models for the Recommended preset are missing.
  choice /c YN /m "Install the recommended models now and continue automatically?"
  if errorlevel 2 (
    echo [INFO] Skipping model install. The app may fail until models are installed.
  ) else (
    call "setup_models.bat" recommended
    if errorlevel 1 (
      echo [ERROR] Model installation failed.
      pause
      exit /b 1
    )
    REM Re-check after install
    set "MISSING=0"
    echo.
    echo [INFO] Re-checking models after install...
    call :CHECK_MODEL "deepseek-r1:32b"
    call :CHECK_MODEL "llama3.3:70b"
    call :CHECK_MODEL "qwen2.5vl:7b"
    if "%MISSING%"=="1" (
      echo.
      echo [ERROR] Some recommended models are still missing.
      echo         Run setup_models.bat manually and choose Option 1.
      pause
      exit /b 1
    )
  )
)

goto START_UI

