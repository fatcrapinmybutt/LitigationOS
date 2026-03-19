
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Optional, Sequence
import numpy as np

class Embedder:
    def embed(self, texts: Sequence[str]) -> np.ndarray:
        raise NotImplementedError

class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        # normalize_embeddings improves cosine behavior
        vecs = self.model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vecs, dtype=np.float32)

class OllamaEmbedder(Embedder):
    def __init__(self, model: str, url: str = "http://127.0.0.1:11434/api/embed"):
        self.model = model
        self.url = url

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        import requests
        payload = {"model": self.model, "input": list(texts)}
        r = requests.post(self.url, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        # Ollama returns {"embeddings":[[...],[...]]} on /api/embed
        vecs = data.get("embeddings") or data.get("embedding") or []
        return np.asarray(vecs, dtype=np.float32)

def make_embedder(backend: str, model: str, ollama_url: str, ollama_model: str) -> Embedder:
    b = (backend or "").lower()
    if b == "ollama":
        return OllamaEmbedder(model=ollama_model, url=ollama_url)
    return SentenceTransformerEmbedder(model_name=model)
