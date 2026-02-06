import sys
import subprocess

def install_and_download():
    print("--- FIXING SCIBERT DOWNLOAD ---")
    
    # 1. Ensure sentence-transformers is installed
    try:
        import sentence_transformers
    except ImportError:
        print("Installing sentence-transformers...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "sentence-transformers"])

    # 2. Force the download with a visible progress bar
    from sentence_transformers import SentenceTransformer
    
    print("\nDownloading the medical AI brain (SciBERT)...")
    print("Please wait until this finishes (approx 400MB).\n")
    
    # This triggers the download to your local cache
    model = SentenceTransformer('allenai/scibert_scivocab_uncased')
    
    print("\n✅ SUCCESS! The model is saved.")
    print("You can now close this window and run 'run_ui.bat' again.")

if __name__ == "__main__":
    install_and_download()
