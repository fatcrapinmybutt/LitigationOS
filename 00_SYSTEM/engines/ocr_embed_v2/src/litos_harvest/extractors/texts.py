
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from .base import Extractor, ExtractResult

class TextExtractor(Extractor):
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in {".txt", ".md", ".rtf"}

    def extract(self, path: Path) -> ExtractResult:
        # NOTE: RTF is treated as plain text here; for full fidelity, use an RTF parser later.
        text = path.read_text(encoding="utf-8", errors="ignore")
        meta = {"type": "text"}
        quotes: List[Dict[str, Any]] = []
        return ExtractResult(text=text, meta=meta, quotes=quotes)
