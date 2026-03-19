\
from __future__ import annotations
from pathlib import Path
from typing import Tuple, List

def extract_text_generic(path: Path) -> Tuple[str, str, List[str]]:
    warnings: List[str] = []
    ext = path.suffix.lower()

    if ext in {".txt", ".md", ".json", ".jsonc", ".yaml", ".yml", ".log", ".csv"}:
        try:
            return "txt", path.read_text(encoding="utf-8", errors="ignore"), warnings
        except Exception as e:
            warnings.append(f"text_read_error:{e}")
            return "txt", "", warnings

    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(str(path))
            return "docx", "\n".join(p.text for p in doc.paragraphs), warnings
        except Exception as e:
            warnings.append(f"docx_extract_error:{e}")
            return "docx", "", warnings

    if ext == ".pdf":
        try:
            from pypdf import PdfReader  # optional
            reader = PdfReader(str(path))
            parts = []
            for i, page in enumerate(reader.pages, start=1):
                try:
                    parts.append(f"\\n\\n[PAGE {i}]\\n" + (page.extract_text() or ""))
                except Exception as pe:
                    warnings.append(f"pdf_page_extract_error:p{i}:{pe}")
            return "pdf_text", "".join(parts), warnings
        except Exception as e:
            warnings.append(f"pdf_no_extractor:{e}")
            return "pdf_text", "", warnings

    warnings.append("unsupported_extension")
    return "other", "", warnings
