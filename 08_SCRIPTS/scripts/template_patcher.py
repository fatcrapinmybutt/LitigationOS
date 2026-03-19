import os, json, datetime, re

class TemplatePatcher:
    """
    Applies auto-patches to clause templates based on RulesIntelligenceCore patch log.
    - Reads backend/data/ruleswatch/patch_log.json
    - Applies simple edits to templates under backend/templates/
    """
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data", "ruleswatch")
        self.patch_log = os.path.join(self.data_dir, "patch_log.json")
        self.templates = os.path.join(self.root, "..", "..", "templates")
        os.makedirs(self.templates, exist_ok=True)

    def patch(self) -> dict:
        patches_applied = []
        if os.path.exists(self.patch_log):
            try:
                hist = json.load(open(self.patch_log, "r", encoding="utf-8"))
            except Exception:
                hist = []
        else:
            hist = []
        latest = hist[-1] if hist else {"patches": []}
        # simple rules
        for p in latest.get("patches", []):
            p_low = p.lower()
            if "service" in p_low:
                path = os.path.join(self.templates, "service_clause.txt")
                txt = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else ""
                if "Updated per Rules Watch" not in txt:
                    txt += "\nUpdated per Rules Watch: verify methods, timing, and proof per latest amendments.\n"
                    open(path, "w", encoding="utf-8").write(txt)
                    patches_applied.append("service_clause.txt")
            if "parenting" in p_low:
                path = os.path.join(self.templates, "parenting_time_clause.txt")
                txt = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else ""
                if "Updated per Rules Watch" not in txt:
                    txt += "\nUpdated per Rules Watch: insert current forms and findings standards.\n"
                    open(path, "w", encoding="utf-8").write(txt)
                    patches_applied.append("parenting_time_clause.txt")
            if "mcr 2.119" in p_low or "motion generator" in p_low:
                path = os.path.join(self.templates, "motion_standard.txt")
                txt = open(path, "r", encoding="utf-8").read() if os.path.exists(path) else ""
                if "Updated per Rules Watch" not in txt:
                    txt += "\nUpdated per Rules Watch: amended timing/format per MCR 2.119 changes.\n"
                    open(path, "w", encoding="utf-8").write(txt)
                    patches_applied.append("motion_standard.txt")
        return {"ok": True, "patched_files": patches_applied}
