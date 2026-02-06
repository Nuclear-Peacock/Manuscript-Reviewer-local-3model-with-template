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
    "deepseek-r1",
    "llama3.3",
    "qwen2.5-vl"
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

    # 2. Check Ollama (and direct to install if missing)
    if not is_ollama_running():
        log("❌ Ollama is not reachable.")
        log("It might be closed, or not installed.")
        log("Attempting to open download page...", color="yellow")
        
        # Open the browser to the download page
        webbrowser.open("https://ollama.com/download")
        
        print("\n" + "="*50)
        print(" INSTRUCTIONS:")
        print(" 1. If you haven't installed Ollama, download and install it now.")
        print(" 2. Open the 'Ollama' application from your Start Menu.")
        print(" 3. When you see the little Ollama icon in your taskbar, come back here.")
        print("="*50 + "\n")
        
        input("Press Enter once Ollama is running to continue...")
        
        # Re-check loop
        while not is_ollama_running():
            log("Still cannot connect to Ollama. Is the app running?")
            input("Press Enter to try again...")
            
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
