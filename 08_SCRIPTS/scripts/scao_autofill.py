import os, json, datetime

class ScaoAutofill:
    """
    Generates FDF sidecars for AcroForm PDFs and JSON snapshots for downstream tools (e.g., pdftk).
    Place SCAO form PDFs in backend/templates/scao_forms/<FORM_ID>.pdf
    Supported IDs: MC01, MC12, FOC65, FOC88
    """
    FORM_MAP = {
        "MC01": {"fields": ["plaintiff_name", "defendant_name", "court_name", "case_number", "venue_county", "date"]},
        "MC12": {"fields": ["plaintiff_name", "defendant_name", "court_name", "case_number", "service_method", "date"]},
        "FOC65": {"fields": ["party_name", "case_number", "court_name", "requested_relief", "date"]},
        "FOC88": {"fields": ["party_name", "case_number", "court_name", "order_terms", "date"]}
    }

    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.templates = os.path.join(self.root, "..", "..", "templates", "scao_forms")
        os.makedirs(self.templates, exist_ok=True)

    def _make_values(self, profile: dict, action: str) -> dict:
        # derive generic values
        court_name = (profile.get("court") or {}).get("name", "")
        case_number = profile.get("case_number", "")
        parties = profile.get("parties", {})
        p_name = (parties.get("plaintiff") or [{}])[0].get("name", "")
        d_name = (parties.get("defendant") or [{}])[0].get("name", "")
        venue = (profile.get("venue") or {}).get("county", "")
        svc_method = (profile.get("service") or {}).get("method", "")
        today = datetime.date.today().strftime("%Y-%m-%d")
        return {
            "plaintiff_name": p_name,
            "defendant_name": d_name,
            "party_name": p_name or d_name,
            "court_name": court_name,
            "case_number": case_number,
            "venue_county": venue,
            "service_method": svc_method,
            "requested_relief": action,
            "order_terms": f"Pending Court approval re: {action}",
            "date": today
        }

    def _write_fdf(self, fields: dict, out_path: str):
        # Minimal FDF writer
        def esc(s): return s.replace("(", r"\(").replace(")", r"\)")
        fdf = ["%FDF-1.2", "1 0 obj", "<< /FDF << /Fields ["]
        for k, v in fields.items():
            fdf.append(f"<< /T ({esc(k)}) /V ({esc(str(v))}) >>")
        fdf += ["] >> >>", "endobj", "trailer", "<< /Root 1 0 R >>", "%%EOF"]
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(fdf))

    def generate_for(self, form_id: str, profile: dict, action: str, out_dir: str) -> dict:
        form_id = form_id.upper()
        spec = self.FORM_MAP.get(form_id)
        if not spec:
            return {"ok": False, "error": f"unsupported_form:{form_id}"}
        values = self._make_values(profile, action)
        fields = {k: values.get(k, "") for k in spec["fields"]}
        pdf_path = os.path.join(self.templates, f"{form_id}.pdf")
        os.makedirs(out_dir, exist_ok=True)
        json_path = os.path.join(out_dir, f"{form_id}_fields.json")
        fdf_path = os.path.join(out_dir, f"{form_id}_fields.fdf")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(fields, f, ensure_ascii=False, indent=2)
        self._write_fdf(fields, fdf_path)
        return {"ok": True, "form_id": form_id, "pdf_template": pdf_path, "json": json_path, "fdf": fdf_path}
