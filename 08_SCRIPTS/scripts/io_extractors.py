from __future__ import annotations
from pathlib import Path
import json
import re

def _safe_decode(raw: bytes) -> str:
    for enc in ("utf-8","utf-16","latin-1"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", errors="ignore")

def extract_text_pages(path: Path) -> list[dict]:
    suffix = path.suffix.lower()
    try:
        if suffix in {".txt",".md",".csv",".tsv",".log",".json"}:
            txt = path.read_text(encoding="utf-8", errors="ignore")
            if suffix == ".json":
                try:
                    obj = json.loads(txt)
                    txt = json.dumps(obj, indent=2)
                except Exception:
                    pass
            return [{"page": 1, "text": txt}]
        if suffix == ".docx":
            try:
                from docx import Document  # type: ignore
                doc = Document(str(path))
                txt = "\n".join(p.text for p in doc.paragraphs)
                return [{"page": 1, "text": txt}]
            except Exception as exc:
                return [{"page": 1, "text": f"[DOCX_PARSE_ERROR] {exc}"}]
        if suffix == ".pdf":
            # Prefer pypdf; preserve per-page grouping for page-line quote previews
            try:
                from pypdf import PdfReader  # type: ignore
            except Exception:
                try:
                    from PyPDF2 import PdfReader  # type: ignore
                except Exception:
                    PdfReader = None
            pages = []
            if PdfReader:
                try:
                    reader = PdfReader(str(path))
                    for i, pg in enumerate(reader.pages, start=1):
                        txt = pg.extract_text() or ""
                        pages.append({"page": i, "text": txt})
                    if pages:
                        return pages
                except Exception as exc:
                    pages = [{"page": 1, "text": f"[PDF_PARSE_ERROR] {exc}"}]
                    return pages
            # Fallback binary decode (not ideal but better than nothing)
            raw = path.read_bytes()
            txt = _safe_decode(raw)
            return [{"page": 1, "text": txt}]
        raw = path.read_bytes()
        txt = _safe_decode(raw)
        return [{"page": 1, "text": txt}]
    except Exception as exc:
        return [{"page": 1, "text": f"[FILE_READ_ERROR] {exc}"}]

def iter_line_records(path: Path) -> list[dict]:
    rows = []
    for page_obj in extract_text_pages(path):
        page_no = int(page_obj.get("page", 1))
        txt = str(page_obj.get("text",""))
        lines = [ln.rstrip() for ln in txt.splitlines()]
        # If PDF extraction has big blocks, split further on sentence boundaries if no line breaks
        if len(lines) <= 2 and len(txt) > 300:
            lines = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\[])",
                             txt.replace("\r"," ").replace("\n"," "))
        for line_no, line in enumerate(lines, start=1):
            clean = line.strip()
            if not clean:
                continue
            rows.append({
                "page": page_no,
                "line": line_no,
                "text": clean,
            })
    return rows
