#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass

from .embedding_engine import EmbedConfig, embed_texts, cosine

@dataclass
class Suggestion:
    label: str
    score: float

def suggest_best_labels(texts: list[str], labels: list[str], cfg: EmbedConfig, top_k: int = 3) -> list[list[Suggestion]]:
    """
    For each text, compute similarity against label strings and return top_k labels.
    """
    if not texts:
        return []
    if not labels:
        return [[] for _ in texts]

    emb_text = embed_texts(texts, cfg)
    emb_lbl = embed_texts(labels, cfg)

    out: list[list[Suggestion]] = []
    for i in range(len(texts)):
        sims = []
        for j in range(len(labels)):
            sims.append((labels[j], cosine(emb_text[i], emb_lbl[j])))
        sims.sort(key=lambda x: x[1], reverse=True)
        out.append([Suggestion(label=s[0], score=float(s[1])) for s in sims[:top_k]])
    return out
