
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Iterable

@dataclass
class Chunk:
    chunk_id: str
    text: str
    start: int
    end: int

def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> List[Chunk]:
    """
    Simple token-agnostic chunking by characters with overlap.
    Deterministic chunk_id is assigned by caller (hash of content+span).
    """
    text = text or ""
    n = len(text)
    chunks: List[Chunk] = []
    i = 0
    while i < n:
        j = min(n, i + chunk_size)
        chunk = text[i:j].strip()
        if chunk:
            chunks.append(Chunk(chunk_id="", text=chunk, start=i, end=j))
        if j == n:
            break
        i = max(0, j - overlap)
    return chunks

