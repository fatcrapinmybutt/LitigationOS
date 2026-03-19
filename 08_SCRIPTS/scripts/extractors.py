from __future__ import annotations
from pathlib import Path
from typing import Tuple, List
import re

def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def extract_text_generic(path: Path) -> Tuple[str, str, List[str]]:
    warnings: List[str] = []
    ext = path.suffix.lower()

    if ext in {".txt", ".md", ".json", ".jsonc", ".yaml", ".yml", ".log", ".csv"}:
        try:
            return "txt", _read_text(path), warnings
        except Exception as e:
            warnings.append(f"text_read_error:{e}")
            return "txt", "", warnings

    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(str(path))
            parts = []
            for i, p in enumerate(doc.paragraphs, start=1):
                t = (p.text or "").strip()
                if t:
                    parts.append(f"[PARA {i}] {t}")
            return "docx", "\n".join(parts), warnings
        except Exception as e:
            warnings.append(f"docx_extract_error:{e}")
            return "docx", "", warnings

    if ext == ".pdf":
        # Optional PDF extraction; fail-soft if no extractor installed.
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            pages = []
            for i, page in enumerate(reader.pages, start=1):
                try:
                    txt = page.extract_text() or ""
                    pages.append(f"\n[PAGE {i}]\n{txt}")
                except Exception as pe:
                    warnings.append(f"pdf_page_extract_error:p{i}:{pe}")
            return "pdf_text", "\n".join(pages), warnings
        except Exception as e:
            warnings.append(f"pdf_no_extractor:{e}")
            return "pdf_text", "", warnings

    warnings.append("unsupported_extension")
    return "other", "", warnings
