from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
from .rubric import Rubric
from .splitter import SentenceUnit

@dataclass
class Evidence:
    item_id: str
    label: str
    severity: str
    score: float
    snippets: list[str]

class EvidenceExtractor:
    def __init__(self, model_name: str = "allenai/scibert_scivocab_uncased", device: str | None = None):
        self.model = SentenceTransformer(model_name, device=device)

    @staticmethod
    def _cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
        b = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
        return a @ b.T

    def extract(self, sentences: list[SentenceUnit], rubric: Rubric, top_k: int = 7) -> list[Evidence]:
        sent_texts = [s.text for s in sentences]
        sent_emb = self.model.encode(sent_texts, convert_to_numpy=True, show_progress_bar=False)
        out: list[Evidence] = []
        for item in rubric.items:
            probe_emb = self.model.encode(item.probes, convert_to_numpy=True, show_progress_bar=False)
            sims = self._cosine(probe_emb, sent_emb)
            best = sims.max(axis=0)
            idx = np.argsort(-best)[:top_k]
            snippets = [f"{sentences[i].pointer} {sent_texts[i][:320].replace('\n',' ')}" for i in idx]
            score = float(best[idx[0]]) if len(idx) else 0.0
            out.append(Evidence(item_id=item.id, label=item.label, severity=item.severity, score=score, snippets=snippets))
        return out

def build_evidence_block(evidence: list[Evidence]) -> str:
    lines: list[str] = []
    for e in evidence:
        lines.append(f"- [{e.severity.upper()}] {e.label} | score={e.score:.2f}")
        for snip in e.snippets:
            lines.append(f"  • {snip}")
    return "\n".join(lines)
