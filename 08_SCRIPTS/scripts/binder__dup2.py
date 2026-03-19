import os, json, zipfile, datetime

class Binderizer:
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data")
        os.makedirs(self.data_dir, exist_ok=True)

    def build(self, action: str) -> str:
        manifest = {"built_at": datetime.datetime.now().isoformat(),"action": action,"items": ["evidence_index.json"]}
        out_zip = os.path.join(self.data_dir, f"binder_{action}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            idx = os.path.join(self.data_dir, "evidence_index.json")
            if os.path.exists(idx): z.write(idx, "evidence_index.json")
        return out_zip
