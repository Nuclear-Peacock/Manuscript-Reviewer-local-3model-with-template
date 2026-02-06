import sys
import subprocess
import time
import shutil
import urllib.request
import urllib.error
import json
from pathlib import Path

# --- Configuration ---
REQUIRED_MODELS = [
    "deepseek-r1",
    "llama3.3",
    "qwen2.5-vl"
]

REPO_ROOT = Path(__file__).resolve().parent

def log(msg, color="white"):
    """Simple logger with minimal ANSI colors for terminals that support it."""
    # Windows cmd.exe often handles ANSI poorly without config, so we keep it simple or use colorama if available.
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def is_ollama_running():
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2) as response:
            return response.status == 200
    except urllib.error.URLError:
        return False

def check_and_pull_models():
    """Checks for models and pulls them if missing."""
    log("Checking AI models...")
    
    # Get installed models
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags") as response:
            data = json.loads(response.read().decode())
            installed_tags = [m["name"] for m in data.get("models", [])]
    except Exception as e:
        log(f"Error talking to Ollama: {e}")
        return

    for model in REQUIRED_MODELS:
        # Check if model (or a specific tag version of it) exists
        # We look for partial match because 'deepseek-r1' might be 'deepseek-r1:latest'
        found = any(model in tag for tag in installed_tags)
        
        if not found:
            log(f"Model '{model}' is missing. Pulling now (this may take a while)...")
            try:
                # We use subprocess to allow the user to see the Ollama progress bar
                subprocess.run(["ollama", "pull", model], check=True)
                log(f"Successfully pulled {model}.")
            except subprocess.CalledProcessError:
                log(f"FAILED to pull {model}. Check your internet connection.")
        else:
            log(f"Model '{model}' is ready.")

def main():
    log("--- Local Manuscript Reviewer Launcher ---")

    # 1. Check Python Dependencies
    # We assume if they are running this, they have python. 
    # But we can check for streamlit.
    try:
        import streamlit
    except ImportError:
        log("Streamlit is missing. Installing requirements...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

    # 2. Check Ollama
    if not is_ollama_running():
        log("❌ ERROR: Ollama is not running.")
        log("Please open the 'Ollama' application on your computer.")
        log("Waiting for Ollama to start...", color="yellow")
        
        while not is_ollama_running():
            time.sleep(2)
            print(".", end="", flush=True)
        print("") # Newline
        log("✅ Ollama detected!")

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
