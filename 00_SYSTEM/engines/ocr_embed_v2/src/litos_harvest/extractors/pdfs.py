
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from pypdf import PdfReader
from pdfminer.high_level import extract_text as pdfminer_extract_text
import pypdfium2 as pdfium
from PIL import Image
import pytesseract

from .base import Extractor, ExtractResult

class PDFExtractor(Extractor):
    def __init__(
        self,
        ocr_enabled: bool,
        ocr_lang: str,
        min_chars_to_accept_text_layer: int,
        render_dpi: int,
        max_pages_for_ocr: int,
    ):
        self.ocr_enabled = ocr_enabled
        self.ocr_lang = ocr_lang
        self.min_chars = min_chars_to_accept_text_layer
        self.render_dpi = render_dpi
        self.max_pages_for_ocr = max_pages_for_ocr

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def _extract_text_pypdf(self, path: Path) -> str:
        try:
            r = PdfReader(str(path))
            out = []
            for i, page in enumerate(r.pages):
                try:
                    t = page.extract_text() or ""
                except Exception:
                    t = ""
                if t:
                    out.append(f"[PAGE {i+1}]\n{t}")
            return "\n\n".join(out)
        except Exception:
            return ""

    def _extract_text_pdfminer(self, path: Path) -> str:
        try:
            return pdfminer_extract_text(str(path)) or ""
        except Exception:
            return ""

    def _render_page(self, pdf: pdfium.PdfDocument, page_index: int) -> Image.Image:
        page = pdf.get_page(page_index)
        scale = self.render_dpi / 72.0
        bitmap = page.render(scale=scale)
        pil = bitmap.to_pil()
        page.close()
        return pil

    def _ocr_pdf(self, path: Path) -> str:
        text_parts: List[str] = []
        try:
            pdf = pdfium.PdfDocument(str(path))
        except Exception:
            return ""
        n = len(pdf)
        n_ocr = min(n, self.max_pages_for_ocr)
        for i in range(n_ocr):
            try:
                img = self._render_page(pdf, i)
                t = pytesseract.image_to_string(img, lang=self.ocr_lang) or ""
                if t.strip():
                    text_parts.append(f"[OCR PAGE {i+1}]\n{t}")
            except Exception:
                continue
        return "\n\n".join(text_parts)

    def extract(self, path: Path) -> ExtractResult:
        text_a = self._extract_text_pypdf(path)
        text_b = self._extract_text_pdfminer(path)
        text = text_a if len(text_a) >= len(text_b) else text_b
        used_ocr = False
        if self.ocr_enabled and len((text or "").strip()) < self.min_chars:
            ocr_text = self._ocr_pdf(path)
            if ocr_text and len(ocr_text.strip()) > len((text or "").strip()):
                text = ocr_text
                used_ocr = True
        meta = {
            "type": "pdf",
            "ocr_used": used_ocr,
            "text_chars": len(text or ""),
            "render_dpi": self.render_dpi if used_ocr else None
        }
        quotes: List[Dict[str, Any]] = []
        return ExtractResult(text=text or "", meta=meta, quotes=quotes)
