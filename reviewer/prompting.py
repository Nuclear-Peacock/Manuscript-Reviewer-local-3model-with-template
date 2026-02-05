from __future__ import annotations
from pathlib import Path

def load_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")

def excerpt(text: str, max_chars: int = 1200) -> str:
    t = " ".join(text.split())
    return (t[:max_chars] + "…") if len(t) > max_chars else t
