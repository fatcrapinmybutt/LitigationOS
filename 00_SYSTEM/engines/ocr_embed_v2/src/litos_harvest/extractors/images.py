
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from PIL import Image
import pytesseract
from .base import Extractor, ExtractResult

class ImageOCRExtractor(Extractor):
    def __init__(self, lang: str = "eng"):
        self.lang = lang

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}

    def extract(self, path: Path) -> ExtractResult:
        try:
            img = Image.open(str(path))
        except Exception as e:
            return ExtractResult(text="", meta={"type":"image","error":str(e)}, quotes=[])
        text = ""
        try:
            text = pytesseract.image_to_string(img, lang=self.lang)
        except Exception as e:
            return ExtractResult(text="", meta={"type":"image","ocr_error":str(e)}, quotes=[])
        meta = {"type":"image", "ocr": True, "lang": self.lang}
        quotes: List[Dict[str, Any]] = []
        return ExtractResult(text=text or "", meta=meta, quotes=quotes)
