
import fitz  # PyMuPDF
from pathlib import Path

def load_pdf_text(pdf_path: Path) -> str:
    try:
        doc = fitz.open(pdf_path)
        text = []
        for page in doc:
            text.append(page.get_text())
        return "\n".join(text)
    except Exception as e:
        return f"Error reading PDF: {e}"

def extract_images_from_pdf(pdf_path: Path, output_dir: Path, dpi=200):
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    image_paths = []
    
    # We limit scanning to the first 10 pages to keep it fast
    count = 0
    for i, page in enumerate(doc):
        img_list = page.get_images()
        if not img_list:
            continue
            
        try:
            pix = page.get_pixmap(dpi=dpi)
            out_file = output_dir / f"page_{i+1}.png"
            pix.save(out_file)
            image_paths.append(out_file)
            count += 1
            if count >= 10: break
        except:
            continue
            
    return image_paths
