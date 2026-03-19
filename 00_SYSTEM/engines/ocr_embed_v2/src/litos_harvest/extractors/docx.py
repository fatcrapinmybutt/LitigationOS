
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from docx import Document
from .base import Extractor, ExtractResult

class DocxExtractor(Extractor):
    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".docx"

    def extract(self, path: Path) -> ExtractResult:
        doc = Document(str(path))
        paras = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
        text = "\n".join(paras)
        meta = {"type": "docx", "paragraphs": len(paras)}
        quotes: List[Dict[str, Any]] = []
        return ExtractResult(text=text, meta=meta, quotes=quotes)
