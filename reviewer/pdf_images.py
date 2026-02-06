from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import fitz  # PyMuPDF


@dataclass
class PdfImageExtractConfig:
    dpi: int = 200
    max_pages: int = 12
    fallback_mode: str = "first_last"  # "first_last" | "all" | "none"
    prefer_pages_with_embedded_images: bool = True


def _safe_stem(path: Path) -> str:
    s = path.stem
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", s)
    return s[:80] if len(s) > 80 else s


def pages_with_embedded_images(doc: fitz.Document) -> list[int]:
    pages = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        imgs = page.get_images(full=True)
        if imgs and len(imgs) > 0:
            pages.append(i)
    return pages


def fallback_pages(doc: fitz.Document, mode: str) -> list[int]:
    n = doc.page_count
    if n == 0:
        return []
    if mode == "none":
        return []
    if mode == "all":
        return list(range(n))
    # default: "first_last"
    if n == 1:
        return [0]
    return [0, n - 1]


def render_pages_to_png(
    pdf_path: Path,
    out_dir: Path,
    cfg: PdfImageExtractConfig,
) -> tuple[list[Path], list[int], str]:
    """
    Returns: (image_paths, page_indices_0based, reason)
    """
    pdf_path = pdf_path.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(pdf_path)
    zoom = cfg.dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    chosen: list[int] = []
    reason = ""

    if cfg.prefer_pages_with_embedded_images:
        embedded = pages_with_embedded_images(doc)
        if embedded:
            chosen = embedded
            reason = "embedded_images"
        else:
            chosen = fallback_pages(doc, cfg.fallback_mode)
            reason = f"fallback_{cfg.fallback_mode}"
    else:
        chosen = fallback_pages(doc, cfg.fallback_mode)
        reason = f"fallback_{cfg.fallback_mode}"

    # Cap pages for speed
    chosen = chosen[: cfg.max_pages]

    image_paths: list[Path] = []
    for i in chosen:
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_file = out_dir / f"page_{i+1:03d}.png"
        pix.save(out_file.as_posix())
        image_paths.append(out_file)

    doc.close()
    return image_paths, chosen, reason


def default_cache_dir(outputs_dir: Path, pdf_path: Path) -> Path:
    return outputs_dir / "_figcache" / _safe_stem(pdf_path)
