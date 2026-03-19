#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EmbedConfig:
    model_id: str
    cache_dir: str
    batch_size: int = 32

def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def _embed_cache_root(cache_dir: str) -> Path:
    return Path(cache_dir).resolve() / "_embeddings_cache"

def embed_texts(texts: list[str], cfg: EmbedConfig) -> list[list[float]]:
    """
    Embeds texts using sentence-transformers.
    Caches embeddings on disk keyed by model_id and content hash.
    """
    from sentence_transformers import SentenceTransformer

    cache_root = _embed_cache_root(cfg.cache_dir)
    _ensure_dir(cache_root)

    model = SentenceTransformer(cfg.model_id, cache_folder=cfg.cache_dir)

    out: list[list[float]] = []
    for t in texts:
        key = _sha1(cfg.model_id + "\n" + t)
        fp = cache_root / f"{key}.json"
        if fp.exists():
            out.append(json.loads(fp.read_text(encoding="utf-8")))
            continue
        vec = model.encode([t], normalize_embeddings=True, show_progress_bar=False)[0]
        vec_list = [float(x) for x in vec.tolist()]
        fp.write_text(json.dumps(vec_list), encoding="utf-8")
        out.append(vec_list)
    return out

def cosine(a: list[float], b: list[float]) -> float:
    import math
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for i in range(len(a)):
        dot += a[i] * b[i]
        na += a[i] * a[i]
        nb += b[i] * b[i]
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))
