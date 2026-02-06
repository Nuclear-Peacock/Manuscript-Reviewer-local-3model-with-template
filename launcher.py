import sys
import subprocess
import time
import shutil
import urllib.request
import urllib.error
import json
import webbrowser
from pathlib import Path

# --- Configuration ---
REQUIRED_MODELS = [
    "qwen2.5vl:7b",
    "deepseek-r1:32b",
    "llama3.3",
]

REPO_ROOT = Path(__file__).resolve().parent

def log(msg, color="white"):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def is_ollama_running():
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as response:
            return response.status == 200
    except urllib.error.URLError:
        return False

def wait_for_ollama_seamlessly():
    if is_ollama_running():
        return

    log("❌ Ollama is not reachable.")
    log("Attempting to open download page...", color="yellow")
    webbrowser.open("https://ollama.com/download")
    
    print("\n" + "="*50)
    print(" WAITING FOR OLLAMA...")
    print(" 1. Please download/install Ollama.")
    print(" 2. Open the 'Ollama' app.")
    print(" 3. This script will resume AUTOMATICALLY once it connects.")
    print("="*50 + "\n")

    while not is_ollama_running():
        time.sleep(3)
        print(".", end="", flush=True)
    
    print("") 
    log("✅ Ollama detected! Resuming...")

def check_and_pull_models():
    log("Checking AI models...")
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags") as response:
            data = json.loads(response.read().decode())
            installed_tags = [m["name"] for m in data.get("models", [])]
    except Exception as e:
        log(f"Error talking to Ollama: {e}")
        return

    for model in REQUIRED_MODELS:
        found = any(model in tag for tag in installed_tags)
        if not found:
            log(f"Model '{model}' is missing. Pulling now (this may take a while)...")
            try:
                subprocess.run(["ollama", "pull", model], check=True)
                log(f"Successfully pulled {model}.")
            except subprocess.CalledProcessError:
                log(f"FAILED to pull {model}. Check your internet connection or model name.")
        else:
            log(f"Model '{model}' is ready.")

def check_scibert_download():
    """
    Checks if SciBERT is cached. If not, downloads it visibly in this window
    so the user doesn't think the app is frozen.
    """
    log("Checking SciBERT (Medical AI Brain)...")
    
    # We run a tiny python script in a subprocess to check/download
    check_script = """
import sys
try:
    from sentence_transformers import SentenceTransformer
    # This will download if missing, or return instantly if cached
    model = SentenceTransformer('allenai/scibert_scivocab_uncased')
except Exception as e:
    sys.exit(1)
"""
    try:
        # Run the check. If it takes time, the user sees "Checking..."
        # We capture output to keep it clean, unless it fails.
        subprocess.run([sys.executable, "-c", check_script], check=True)
        log("✅ SciBERT is ready.")
    except subprocess.CalledProcessError:
        log("⚠️ SciBERT missing. Downloading now (approx 440MB)...")
        try:
            # Re-run with output visible so they see progress if possible
            subprocess.run([sys.executable, "-c", check_script], check=True)
            log("✅ SciBERT download complete.")
        except:
            log("❌ Failed to download SciBERT. The app might crash later.")

def main():
    log("--- Local Manuscript Reviewer Launcher ---")

# 1. Check Python Dependencies
    try:
        import streamlit
        import fitz  # pymupdf
        import docx  # <--- ADD THIS LINE (this triggers the check)
    except ImportError:
        log("Installing missing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # 2. Check SciBERT (The "Fix" is now here)
    check_scibert_download()

    # 3. Check Ollama (Seamless)
    wait_for_ollama_seamlessly()

    # 4. Check Models (Auto-Setup)
    check_and_pull_models()

    # 5. Run App (Auto-Launch Browser)
    log("🚀 Starting User Interface...")
    app_path = REPO_ROOT / "app.py"
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.headless", "false"
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        log("App stopped by user.")
    except Exception as e:
        log(f"Error launching app: {e}")
        input("Press Enter to close...")

if __name__ == "__main__":
    main()
