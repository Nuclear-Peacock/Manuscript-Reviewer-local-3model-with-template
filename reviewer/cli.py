import argparse
import logging
import sys
import os
from pathlib import Path
import fitz  # PyMuPDF

# Add repo root to path to find sibling modules
sys.path.append(str(Path(__file__).parent.parent))

# --- IMPORT YOUR CUSTOM BRAINS ---
try:
    from reviewer.ollama import OllamaText, OllamaVLM
    from reviewer.ingest import load_manuscript
except ImportError as e:
    print(f"❌ CRITICAL IMPORT ERROR: {e}")
    print("Ensure 'ollama.py' and 'ingest.py' are in the 'reviewer' folder.")
    sys.exit(1)

def setup_logging(output_dir: Path):
    log_file = output_dir / "run_log.txt"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def extract_images_local(pdf_path: Path, output_dir: Path, dpi=200):
    """Fallback image extractor if pdf_images.py is not configured"""
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_paths = []
    
    # Scan first 10 pages to save time
    for i, page in enumerate(doc):
        if i >= 10: break
        # Render page as image (simpler than object extraction for Vision models)
        pix = page.get_pixmap(dpi=dpi)
        out_path = output_dir / f"page_{i+1}.png"
        pix.save(out_path)
        image_paths.append(str(out_path))
    return image_paths

def load_template(name: str) -> str:
    """Finds and loads a template from config/prompts"""
    # Look in ../config/prompts relative to this file
    base = Path(__file__).parent.parent
    prompt_path = base / "config" / "prompts" / f"{name}.txt"
    
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    
    # Fallback default if file is missing
    logging.warning(f"⚠️ Template {name}.txt not found. Using default.")
    return f"Please review the following input based on {name}."

def main():
    parser = argparse.ArgumentParser(description="Custom Manuscript Reviewer CLI")
    
    # Core Arguments
    parser.add_argument("--input", required=True, type=str)
    parser.add_argument("--out", required=True, type=str)
    
    # Metadata passed from UI
    parser.add_argument("--manuscript_type", type=str, default="Original Research")
    parser.add_argument("--study_design", type=str, default="Not specified")
    parser.add_argument("--has_ai", action="store_true")
    
    # Model Config
    parser.add_argument("--critic_model", required=True, type=str)
    parser.add_argument("--writer_model", required=True, type=str)
    parser.add_argument("--vlm_model", type=str, default=None)
    parser.add_argument("--fig_dpi", type=int, default=200)
    parser.add_argument("--temperature", type=float, default=0.2)

    args = parser.parse_args()
    
    pdf_path = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(out_dir)

    logging.info(f"Starting review using custom logic for: {pdf_path.name}")

    # 1. INGEST (Using your code)
    print("[1/5] Extracting PDF text (Custom Ingest)...")
    try:
        manuscript = load_manuscript(pdf_path)
        # Combine all text units into one string
        full_text = "\n\n".join([unit.text for unit in manuscript.units])
        logging.info(f"Extracted {len(full_text)} characters.")
    except Exception as e:
        logging.error(f"Ingest failed: {e}")
        sys.exit(1)

    # 2. VISION (Optional)
    vision_context = ""
    if args.vlm_model:
        print(f"[3/5] Running Vision Analysis ({args.vlm_model})...")
        try:
            img_dir = out_dir / "figures"
            image_paths = extract_images_local(pdf_path, img_dir, dpi=args.fig_dpi)
            
            if image_paths:
                vlm = OllamaVLM(model=args.vlm_model, temperature=args.temperature)
                # Load vision prompt template if exists, else default
                vlm_prompt = load_template("vlm_prompt") or "Describe these figures in detail, noting any errors."
                vision_context = vlm.analyze_images(vlm_prompt, image_paths)
                logging.info("Vision analysis complete.")
            else:
                vision_context = "No images found."
        except Exception as e:
            logging.error(f"Vision analysis failed: {e}")
            vision_context = "Vision analysis skipped due to error."
    else:
        print("[3/5] Skipping Vision (User disabled).")

    # 3. CRITIC (Using your OllamaText class)
    print(f"[4/5] Running Critic ({args.critic_model})...")
    critic = OllamaText(model=args.critic_model, temperature=args.temperature)
    
    # Load your specific template
    critic_template = load_template("critic_prompt")
    
    # Construct prompt by injecting variables (Robust handling)
    # We append text if {{TEXT}} placeholder isn't found
    if "{{TEXT}}" in critic_template:
        critic_input = critic_template.replace("{{TEXT}}", full_text)
    else:
        critic_input = f"{critic_template}\n\n### MANUSCRIPT ###\n{full_text}"
        
    # Inject Metadata
    meta_str = f"Type: {args.manuscript_type}\nDesign: {args.study_design}\nAI Study: {args.has_ai}"
    critic_input = critic_input.replace("{{METADATA}}", meta_str)
    
    # Inject Vision
    critic_input = critic_input.replace("{{VISION}}", vision_context)

    # Generate
    critique = critic.generate(critic_input)
    (out_dir / "critique_debug.md").write_text(critique, encoding="utf-8")

    # 4. WRITER (Using your OllamaText class)
    print(f"[5/5] Running Writer ({args.writer_model})...")
    writer = OllamaText(model=args.writer_model, temperature=args.temperature)
    
    writer_template = load_template("writer_prompt")
    
    if "{{CRITIQUE}}" in writer_template:
        writer_input = writer_template.replace("{{CRITIQUE}}", critique)
    else:
        writer_input = f"{writer_template}\n\n### CRITIQUE NOTES ###\n{critique}"

    final_review = writer.generate(writer_input)

    # 5. Save
    safe_name = pdf_path.stem.replace(" ", "_")
    final_path = out_dir / f"Review_{safe_name}.md"
    final_path.write_text(final_review, encoding="utf-8")
    
    print("Review completed successfully.")
    logging.info(f"Saved to {final_path}")

if __name__ == "__main__":
    main()
