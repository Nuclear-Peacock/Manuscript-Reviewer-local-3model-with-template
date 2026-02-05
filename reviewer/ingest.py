from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import fitz  # pymupdf
from docx import Document

@dataclass
class TextUnit:
    pointer: str
    text: str

@dataclass
class Manuscript:
    path: Path
    units: list[TextUnit]

def _clean(s: str) -> str:
    return " ".join(s.replace("\x00", " ").split())

def load_manuscript(path: str | Path) -> Manuscript:
    p = Path(path).expanduser().resolve()
    suf = p.suffix.lower()
    units: list[TextUnit] = []
    if suf == ".pdf":
        doc = fitz.open(p)
        for i, page in enumerate(doc):
            txt = _clean(page.get_text("text") or "")
            if txt:
                units.append(TextUnit(pointer=f"[p{i+1}]", text=txt))
    elif suf == ".docx":
        doc = Document(str(p))
        paras = [x.text for x in doc.paragraphs if x.text and x.text.strip()]
        for i, t in enumerate(paras):
            units.append(TextUnit(pointer=f"[para{i+1}]", text=_clean(t)))
    elif suf in {".txt", ".md"}:
        txt = _clean(p.read_text(encoding="utf-8", errors="ignore"))
        if txt:
            units.append(TextUnit(pointer="[full]", text=txt))
    else:
        raise ValueError(f"Unsupported file type: {suf}")
    return Manuscript(path=p, units=units)
