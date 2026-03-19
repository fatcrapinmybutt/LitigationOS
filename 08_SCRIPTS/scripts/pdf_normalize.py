import os, subprocess, shutil

class PdfNormalizer:
    """
    OCR + PDF/A normalization using ocrmypdf when available.
    - If ocrmypdf exists, runs: ocrmypdf --optimize 3 --output-type pdfa src out.pdf
    - Otherwise, copies src to out and sets a warning flag.
    """
    def __init__(self):
        pass

    def _which(self, exe: str) -> str | None:
        for p in os.environ.get("PATH", "").split(os.pathsep):
            cand = os.path.join(p, exe)
            if os.path.isfile(cand):
                return cand
            if os.name == "nt" and os.path.isfile(cand + ".exe"):
                return cand + ".exe"
        return None

    def normalize(self, src_pdf: str, out_pdf: str) -> dict:
        ocrmypdf = self._which("ocrmypdf")
        ok = False
        warnings = []
        if ocrmypdf and os.path.exists(src_pdf):
            try:
                subprocess.run([ocrmypdf, "--optimize", "3", "--output-type", "pdfa", "--force-ocr", src_pdf, out_pdf],
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                ok = True
            except Exception as e:
                warnings.append(f"ocrmypdf_failed:{e}")
        if not ok:
            try:
                shutil.copyfile(src_pdf, out_pdf)
            except Exception as e:
                warnings.append(f"copy_failed:{e}")
        return {"ok": ok, "warnings": warnings, "out_pdf": out_pdf}
