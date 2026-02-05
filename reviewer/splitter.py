from __future__ import annotations
from dataclasses import dataclass
import pysbd
from .ingest import TextUnit

@dataclass
class SentenceUnit:
    pointer: str
    text: str

def split_to_sentences(units: list[TextUnit], max_sentences: int = 30000) -> list[SentenceUnit]:
    seg = pysbd.Segmenter(language="en", clean=True)
    out: list[SentenceUnit] = []
    for u in units:
        for j, s in enumerate(seg.segment(u.text), start=1):
            s = s.strip()
            if not s:
                continue
            out.append(SentenceUnit(pointer=f"{u.pointer}s{j}", text=s))
            if len(out) >= max_sentences:
                return out
    return out
