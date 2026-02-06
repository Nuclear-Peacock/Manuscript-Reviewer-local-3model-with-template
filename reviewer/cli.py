import argparse
import logging
import sys
import os
from pathlib import Path
import json

# Ensure we can find the modules in this package
sys.path.append(str(Path(__file__).parent.parent))

# Import fitz (PyMuPDF) safely
try:
    import fitz
except ImportError:
    print("CRITICAL ERROR: 'pymupdf' is not installed.")
    print("Please run: pip install pymupdf")
    sys.exit(1)

# Import internal modules (assuming standard structure for this tool)
# We use try/except to handle potential structure variations cleanly
try:
    from reviewer.agents import CriticAgent, WriterAgent, VisionAgent
    from reviewer.utils import load_pdf_text, extract_images_from_pdf
except ImportError:
    # Fallback if run directly
    from agents import CriticAgent, WriterAgent, VisionAgent
    from utils import load_pdf_text, extract_images_from_pdf

def setup_logging(output_dir: Path):
    log_file = output_dir / "debug_log.txt"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    parser = argparse.ArgumentParser(description="Local Manuscript Reviewer CLI")
    
    # Inputs
    parser.add_argument("--input", required=True, type=str, help="Path to PDF")
    parser.add_argument("--out", required=True, type=str, help="Output directory")
    
    # Metadata
    parser.add_argument("--manuscript_type", type=str, default="original_research")
    parser.add_argument("--study_design", type=str, default="Not specified")
    parser.add_argument("--has_ai", action="store_true", help="Flag if manuscript includes AI/ML")

    # Models
    parser.add_argument("--critic_model", required=True, type=str)
    parser.add_argument("--writer_model", required=True, type=str)
    parser.add_argument("--vlm_model", type=str, default=None, help="Vision model (Optional)")
    
    # Config
    parser.add_argument("--fig_dpi", type=int, default=200)
    parser.add_argument("--temperature", type=float, default=0.3)

    args = parser.parse_args()
    
    # Setup
    pdf_path = Path(args.input)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(out_dir)

    logging.info(f"Starting review for: {pdf_path.name}")
    logging.info(f"Type: {args.manuscript_type}, AI Study: {args.has_ai}")

    # 1. Text Extraction
    print("[1/5] Extracting PDF text...")
    try:
        full_text = load_pdf_text(pdf_path)
    except Exception as e:
        logging.error(f"Failed to extract text: {e}")
        sys.exit(1)

    # 2. Vision Analysis (OPTIONAL)
    vision_feedback = "No figure analysis requested (Fast Mode)."
    
    if args.vlm_model:
        print(f"[3/5] Rendering PDF pages for figure/table review (VLM)...")
        print(f"[auto_figures] reason=standard pages=all images=scan dpi={args.fig_dpi}")
        
        try:
            # Initialize Vision Agent
            vision_agent = VisionAgent(model_name=args.vlm_model, temperature=args.temperature)
            
            # Extract images (using the utility from your repo)
            image_paths = extract_images_from_pdf(pdf_path, out_dir / "figures", dpi=args.fig_dpi)
            
            if image_paths:
                print(f"[3/5] Vision Agent: Analyzing {len(image_paths)} images...")
                vision_feedback = vision_agent.analyze_figures(image_paths)
            else:
                vision_feedback = "No images found in manuscript."
                
        except Exception as e:
            logging.error(f"Vision analysis failed: {e}")
            vision_feedback = "Vision analysis failed due to an error."
    else:
        print("[3/5] Skipping Vision Analysis (User requested)...")

    # 3. Critic Agent
    print(f"[4/5] Running critic ({args.critic_model})...")
    critic = CriticAgent(model_name=args.critic_model, temperature=args.temperature)
    
    # Pass all context to the critic
    critique = critic.review_manuscript(
        text=full_text,
        vision_context=vision_feedback,
        manuscript_type=args.manuscript_type,
        study_design=args.study_design,
        has_ai=args.has_ai
    )
    
    (out_dir / "critique_debug.md").write_text(critique, encoding="utf-8")

    # 4. Writer Agent
    print(f"[5/5] Running writer ({args.writer_model})...")
    writer = WriterAgent(model_name=args.writer_model, temperature=args.temperature)
    
    final_review = writer.draft_review(
        critique=critique,
        manuscript_type=args.manuscript_type
    )

    # Save
    final_path = out_dir / f"Review_{pdf_path.stem}.md"
    final_path.write_text(final_review, encoding="utf-8")
    
    print("Review completed.")
    logging.info(f"Saved to {final_path}")

if __name__ == "__main__":
    main()
