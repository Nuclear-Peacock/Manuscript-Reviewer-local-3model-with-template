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
# We ONLY auto-download the "Medium" set to save time/disk space.
REQUIRED_MODELS = [
    # Vision (Shared by all)
    "qwen2.5-vl:7b",
    
    # Medium Set (The Default)
    "deepseek-r1:32b",
    "llama3.3",
    
    # OPTIONAL: Uncomment these if you want to force-download them too.
    # "deepseek-r1:14b", # Fast Critic
    # "llama3.1:8b",     # Fast Writer
    # "deepseek-r1:70b"  # Accurate Critic
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
    """
    Opens the download page once, then polls silently until Ollama appears.
    """
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

    # Seamless Loop: Check every 3 seconds
    while not is_ollama_running():
        time.sleep(3)
        print(".", end="", flush=True)
    
    print("") # Newline
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
                log(f"FAILED to pull {model}. Check your internet connection.")
        else:
            log(f"Model '{model}' is ready.")

def main():
    log("--- Local Manuscript Reviewer Launcher ---")

    # 1. Check Python Dependencies
    try:
        import streamlit
    except ImportError:
        log("Streamlit is missing. Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # 2. Check Ollama (Seamless)
    wait_for_ollama_seamlessly()

    # 3. Check Models (Auto-Setup)
    check_and_pull_models()

    # 4. Run App
    log("🚀 Starting User Interface...")
    app_path = REPO_ROOT / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        log("App stopped by user.")
    except Exception as e:
        log(f"Error launching app: {e}")
        input("Press Enter to close...")

if __name__ == "__main__":
    main()
