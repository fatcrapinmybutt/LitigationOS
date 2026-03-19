\
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None
try:
    from PIL import Image
except Exception:
    Image = None
try:
    import pytesseract
except Exception:
    pytesseract = None

from utils import stable_id, expand_placeholders

def embedded_text_density(text: str) -> float:
    if not text:
        return 0.0
    non_ws = sum(1 for c in text if not c.isspace())
    return non_ws / 1000.0

def _as_exe_path_or_none(candidate: Optional[str]) -> Optional[Path]:
    if not candidate:
        return None
    p = Path(candidate)
    try:
        if p.is_file() and p.name.lower() == "tesseract.exe":
            return p
        if p.is_dir():
            direct = p / "tesseract.exe"
            if direct.exists():
                return direct
            for hit in p.rglob("tesseract.exe"):
                return hit
    except Exception:
        return None
    return None

def configure_tesseract(tesseract_cmd_or_dir: Optional[str], config_candidates: List[str]) -> Dict[str, Any]:
    info = {"configured": False, "tesseract_cmd": None, "reason": None}
    if pytesseract is None:
        info["reason"] = "pytesseract_not_installed"
        return info

    candidates: List[str] = []
    if tesseract_cmd_or_dir:
        candidates.append(tesseract_cmd_or_dir)
    env_cmd = os.environ.get("TESSERACT_CMD")
    if env_cmd:
        candidates.append(env_cmd)
    candidates.extend(expand_placeholders(config_candidates))

    try:
        script_dir = Path(__file__).resolve().parent
        candidates.append(str(script_dir / "tesseract.exe"))
        candidates.append(str(script_dir / "Tesseract-OCR"))
        exe_dir = Path(sys.executable).resolve().parent
        candidates.append(str(exe_dir / "tesseract.exe"))
        candidates.append(str(exe_dir / "Tesseract-OCR"))
    except Exception:
        pass

    for c in candidates:
        exe = _as_exe_path_or_none(c)
        if exe and exe.exists():
            try:
                pytesseract.pytesseract.tesseract_cmd = str(exe)
                info["configured"] = True
                info["tesseract_cmd"] = str(exe)
                info["reason"] = "set_pytesseract_cmd"
                return info
            except Exception:
                continue

    info["reason"] = "tesseract_not_found"
    return info

def extract_pdf_text_and_optional_ocr(
    pdf_path: Path,
    out_dir: Path,
    config_candidates: List[str],
    ocr_mode: str = "auto",
    min_density: float = 0.5,
    dpi: int = 200,
    lang: str = "eng",
    tesseract_cmd_or_dir: Optional[str] = None,
) -> Dict[str, Any]:
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) not installed.")
    if ocr_mode not in {"off", "auto", "on"}:
        raise ValueError("ocr_mode must be off|auto|on")

    out_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    tcfg = configure_tesseract(tesseract_cmd_or_dir, config_candidates)

    pages_out: List[Dict[str, Any]] = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        embedded = page.get_text("text") or ""
        dens = embedded_text_density(embedded)
        use_ocr = (ocr_mode == "on") or (ocr_mode == "auto" and dens < min_density)

        ocr_text = None
        used_ocr = False
        if use_ocr:
            if pytesseract is None or Image is None or not tcfg.get("configured"):
                ocr_text = None
            else:
                pix = page.get_pixmap(dpi=dpi)
                img_path = out_dir / f"{pdf_path.stem}__p{i+1:04d}.png"
                pix.save(str(img_path))
                try:
                    img = Image.open(img_path)
                    ocr_text = pytesseract.image_to_string(img, lang=lang)
                    used_ocr = bool(ocr_text and ocr_text.strip())
                except Exception:
                    ocr_text = None
                    used_ocr = False

        pages_out.append({
            "page": i + 1,
            "embedded_text": embedded,
            "embedded_density": dens,
            "used_ocr": used_ocr,
            "ocr_text": ocr_text,
        })

    return {"pdf": str(pdf_path), "tesseract": tcfg, "pages": pages_out}

def build_quote_atoms_from_pages(
    pdf_name: str,
    pages_payload: Dict[str, Any],
    bundle_uid: str,
    entry_path: str
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for p in pages_payload.get("pages", []):
        page_no = int(p["page"])
        text = (p.get("ocr_text") or p.get("embedded_text") or "").strip()
        if not text:
            continue
        qid = f"Quote:{stable_id(pdf_name, str(page_no))}"
        out.append({
            "quote_id": qid,
            "text": text,
            "provenance": {
                "prov_id": f"Prov:{stable_id(pdf_name, str(page_no), 'prov')}",
                "source": {
                    "bundle_uid": bundle_uid,
                    "entry_path": entry_path,
                    "integrity_key": f"IK:{stable_id(bundle_uid, entry_path)}",
                    "locator": f"page={page_no}",
                    "method": "ocr" if p.get("used_ocr") else "embedded_text"
                },
            },
            "span": {"start": 0, "end": max(0, len(text))}
        })
    return out
