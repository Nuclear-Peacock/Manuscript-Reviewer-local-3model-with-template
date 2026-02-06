# Local Manuscript Reviewer - Robust Windows Launcher (PowerShell)
# - No batch parser issues
# - Always prints the exact failure point
# - Always stays open at the end
# - Writes a log to outputs\launcher.log

$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

if (!(Test-Path "outputs")) { New-Item -ItemType Directory -Path "outputs" | Out-Null }
$log = Join-Path $PSScriptRoot "outputs\launcher.log"

"==========================================================" | Out-File -FilePath $log -Encoding utf8
"Launcher Log"                                               | Out-File -FilePath $log -Append -Encoding utf8
("{0} {1}" -f (Get-Date).ToShortDateString(), (Get-Date).ToLongTimeString()) | Out-File -FilePath $log -Append -Encoding utf8
("Folder: {0}" -f (Get-Location))                            | Out-File -FilePath $log -Append -Encoding utf8
"==========================================================" | Out-File -FilePath $log -Append -Encoding utf8
""                                                           | Out-File -FilePath $log -Append -Encoding utf8

function Log([string]$s) {
  $s | Out-File -FilePath $log -Append -Encoding utf8
}

function Step([string]$s) {
  Write-Host $s
  Log $s
}

function Fail([string]$s) {
  Write-Host $s -ForegroundColor Red
  Log $s
  throw $s
}

try {
  Step "=========================================================="
  Step "  Local Manuscript Reviewer - One-Click Launcher (Windows)"
  Step "=========================================================="
  Step ("Log file: {0}" -f $log)
  Step ""

  Step "[STEP 1] Checking Python..."
  $py = Get-Command python -ErrorAction SilentlyContinue
  if (-not $py) { Fail "[ERROR] Python not found in PATH. Install Python 3.10+ and check 'Add to PATH'." }

  $pyver = & python --version 2>&1
  Log $pyver
  Step ("[OK] {0}" -f $pyver)

  Step "[STEP 1b] Checking Python >= 3.10..."
  $okver = & python -c "import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)" 2>&1
  if ($LASTEXITCODE -ne 0) { Fail "[ERROR] Python must be 3.10+. Install a newer Python." }
  Step "[OK] Version OK"
  Step ""

  Step "[STEP 2] Creating venv if needed..."
  $venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
  if (!(Test-Path $venvPy)) {
    Log "Creating venv..."
    & python -m venv .venv 2>&1 | ForEach-Object { Log $_ }
    if ($LASTEXITCODE -ne 0 -or !(Test-Path $venvPy)) { Fail "[ERROR] Failed to create .venv." }
  }
  Step "[OK] venv exists"
  Step ""

  Step "[STEP 3] Installing dependencies..."
  & $venvPy -m pip install --upgrade pip 2>&1 | ForEach-Object { Log $_ }
  & $venvPy -m pip install -r requirements.txt 2>&1 | ForEach-Object { Log $_ }
  if ($LASTEXITCODE -ne 0) { Fail "[ERROR] pip install failed. See outputs\launcher.log" }

  & $venvPy -c "import streamlit" 2>$null
  if ($LASTEXITCODE -ne 0) {
    Step "[INFO] Installing Streamlit..."
    & $venvPy -m pip install streamlit 2>&1 | ForEach-Object { Log $_ }
    if ($LASTEXITCODE -ne 0) { Fail "[ERROR] Streamlit install failed. See outputs\launcher.log" }
  }
  Step "[OK] Dependencies installed"
  Step ""

  Step "[STEP 4] Checking Ollama..."
  $ollama = Get-Command ollama -ErrorAction SilentlyContinue
  if (-not $ollama) { Fail "[ERROR] Ollama not found. Install Ollama and ensure it's in PATH." }

  # Check Ollama server reachable
  try {
    $null = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 3
  } catch {
    Fail "[ERROR] Ollama is not reachable at http://localhost:11434. Start Ollama and try again."
  }
  Step "[OK] Ollama running"
  Step ""

  Step "[STEP 5] Ensuring folders..."
  if (!(Test-Path "private_inputs")) { New-Item -ItemType Directory -Path "private_inputs" | Out-Null }
  if (!(Test-Path "outputs")) { New-Item -ItemType Directory -Path "outputs" | Out-Null }
  Step "[OK] folders ready"
  Step ""

  Step "[STEP 6] Checking required models (Balanced)..."
  $required = @("deepseek-r1:32b", "llama3.3:70b", "qwen2.5vl:7b")
  $missing = @()

  foreach ($m in $required) {
    & ollama show $m *> $null
    if ($LASTEXITCODE -ne 0) {
      Step ("[MISSING] {0}" -f $m)
      $missing += $m
    } else {
      Step ("[OK]      {0}" -f $m)
    }
  }

  if ($missing.Count -gt 0) {
    Step ""
    Step "[ERROR] One or more required models are missing (or tag names differ)."
    Step "Run setup_models.bat (option 1) or run: ollama list"
    Step ""
    & ollama list | ForEach-Object { Step $_ }
    Fail "[ERROR] Missing models: $($missing -join ', ')"
  }

  Step ""
  Step "[STEP 7] Launching Streamlit UI..."
  if (!(Test-Path "app.py")) { Fail "[ERROR] app.py not found in this folder." }

  Start-Process "http://127.0.0.1:8501" | Out-Null
  & $venvPy -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 2>&1 | ForEach-Object {
    # streamlit output goes to console and log
    Write-Host $_
    Log $_
  }

  Step ""
  Step ("[INFO] Streamlit exited with code {0}" -f $LASTEXITCODE)
  Log ("Streamlit exit code: {0}" -f $LASTEXITCODE)

} catch {
  Step ""
  Step "=========================================================="
  Step "[FAILED] See log: outputs\launcher.log"
  Step "=========================================================="
  Step ""
  Step $_.Exception.Message
} finally {
  Step ""
  Step "Press Enter to close..."
  Read-Host | Out-Null
}
