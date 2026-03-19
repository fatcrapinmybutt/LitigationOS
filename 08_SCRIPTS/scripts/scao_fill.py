import os, json, datetime, subprocess, shutil
from typing import Dict, Any
from .scao_autofill import ScaoAutofill
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

class ScaoFiller:
    """
    Fills and flattens SCAO PDFs:
    - Loads a mapping from engine/scao_maps/<FORM_ID>.json
    - Generates FDF via ScaoAutofill
    - If `pdftk` exists AND a PDF template resides in templates/scao_forms/<FORM_ID>.pdf:
        runs pdftk fill_form + flatten to produce a filled PDF
    - Returns artifacts + a validation report on required fields
    """
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.maps = os.path.join(self.root, "engine", "scao_maps")
        self.templates = os.path.join(self.root, "..", "..", "templates", "scao_forms")
        os.makedirs(self.templates, exist_ok=True)

    def _which(self, exe: str) -> str | None:
        for p in os.environ.get("PATH", "").split(os.pathsep):
            cand = os.path.join(p, exe)
            if os.path.isfile(cand):
                return cand
            if os.name == "nt" and os.path.isfile(cand + ".exe"):
                return cand + ".exe"
        return None

    def _load_map(self, form_id: str) -> Dict[str, Any]:
        p = os.path.join(self.maps, f"{form_id}.json")
        if not os.path.exists(p):
            return {"ok": False, "error": f"map_not_found:{form_id}"}
        spec = json.load(open(p, "r", encoding="utf-8"))
        return {"ok": True, "spec": spec}

    def fill(self, form_id: str, profile: dict, action: str, out_dir: str) -> Dict[str, Any]:
        form_id = form_id.upper()
        lm = self._load_map(form_id)
        if not lm["ok"]:
            return lm
        spec = lm["spec"]
        sc = ScaoAutofill()
        os.makedirs(out_dir, exist_ok=True)
        # Generate base values JSON+FDF
        base = sc.generate_for(form_id, profile, action, out_dir)
        fields = json.load(open(base["json"], "r", encoding="utf-8"))
        # Validate required fields
        missing = [k for k in spec.get("required_fields", []) if not fields.get(k)]
        map_fields = spec.get("field_map", {})
        # Build FDF for mapped field names
        mapped = {}
        for k, v in map_fields.items():
            vv = v.format(**fields)
            mapped[k] = vv
        # Write mapped FDF
        fdf_path = os.path.join(out_dir, f"{form_id}_mapped.fdf")
        def esc(s): return s.replace("(", r"\(").replace(")", r"\)")
        fdf = ["%FDF-1.2", "1 0 obj", "<< /FDF << /Fields ["]
        for k, v in mapped.items():
            fdf.append(f"<< /T ({esc(k)}) /V ({esc(str(v))}) >>")
        fdf += ["] >> >>", "endobj", "trailer", "<< /Root 1 0 R >>", "%%EOF"]
        with open(fdf_path, "w", encoding="utf-8") as f:
            f.write("\n".join(fdf))

        # Attempt fill+flatten with pdftk if available
        pdftk = self._which("pdftk")
        pdf_template = os.path.join(self.templates, f"{form_id}.pdf")
        filled = None
        cmd_ok = False
        if pdftk and os.path.exists(pdf_template):
            filled = os.path.join(out_dir, f"{form_id}_filled.pdf")
            try:
                subprocess.run([pdftk, pdf_template, "fill_form", fdf_path, "output", filled, "flatten"],
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                cmd_ok = True
            except Exception as e:
                cmd_ok = False

        report = {"required_missing": missing, "mapped_fields_count": len(mapped), "pdftk_used": cmd_ok, "template_exists": os.path.exists(pdf_template)}
        res = {"ok": True, "form_id": form_id, "fields_json": base["json"], "mapped_fdf": fdf_path, "filled_pdf": filled, "report": report}
        return res
