import os, json
from typing import Dict, Any

try:
    import PyPDF2
except Exception:
    PyPDF2 = None

class ComplianceValidator:
    """
    Lightweight checks for filing bundle:
    - Page counts present
    - Signature indicator '/s/' found in Main Filing
    - Proof of Service exists
    - Basic margin heuristic (skipped without text coordinates)
    """
    def _pdf_pages(self, path: str) -> int:
        if PyPDF2 is None or not os.path.exists(path):
            return 0
        try:
            r = PyPDF2.PdfReader(open(path, "rb"))
            return len(r.pages)
        except Exception:
            return 0

    def _has_signature_hint(self, path: str) -> bool:
        if PyPDF2 is None or not os.path.exists(path):
            return False
        try:
            r = PyPDF2.PdfReader(open(path, "rb"))
            for p in r.pages[:3]:
                txt = (p.extract_text() or "").lower()
                if "/s/" in txt or "signed" in txt:
                    return True
        except Exception:
            pass
        return False

    def validate(self, filing_pdf: str, order_pdf: str, pos_pdf: str) -> Dict[str, Any]:
        pages_main = self._pdf_pages(filing_pdf)
        pages_order = self._pdf_pages(order_pdf)
        pages_pos = self._pdf_pages(pos_pdf)
        sig = self._has_signature_hint(filing_pdf)
        checks = {
            "main_present": pages_main > 0,
            "order_present": pages_order > 0,
            "pos_present": pages_pos > 0,
            "signature_hint": sig
        }
        failures = [k for k, ok in checks.items() if not ok]
        return {"checks": checks, "pass": len(failures) == 0, "failures": failures}
