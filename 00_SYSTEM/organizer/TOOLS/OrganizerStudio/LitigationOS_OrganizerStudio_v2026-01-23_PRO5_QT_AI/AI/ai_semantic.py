#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

@dataclass
class Suggestion:
    label: str
    score: float

def available() -> bool:
    try:
        import sentence_transformers  # noqa
        return True
    except Exception:
        return False

def suggest_categories(texts: list[str], candidate_labels: list[str], top_k: int = 3) -> list[list[Suggestion]]:
    """
    Lightweight semantic suggestion engine using sentence-transformers when available.
    If unavailable, returns empty suggestions.
    """
    if not available():
        return [[] for _ in texts]
    from sentence_transformers import SentenceTransformer, util
    model = SentenceTransformer("intfloat/e5-small-v2")
    emb_t = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    emb_l = model.encode(candidate_labels, normalize_embeddings=True, show_progress_bar=False)
    sims = util.cos_sim(emb_t, emb_l)
    out: list[list[Suggestion]] = []
    for i in range(sims.shape[0]):
        row = sims[i].tolist()
        idx = sorted(range(len(row)), key=lambda j: row[j], reverse=True)[:top_k]
        out.append([Suggestion(candidate_labels[j], float(row[j])) for j in idx])
    return out
