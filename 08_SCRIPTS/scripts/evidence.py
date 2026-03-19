import os, json, hashlib, datetime
from typing import List, Dict, Any

class EvidenceManifest:
    """
    Builds a Bates-numbered manifest from evidence_index.json.
    - Reads backend/data/evidence_index.json (created by IngestEngine / DrivePuller)
    - Generates manifest JSON and CSV under backend/data/manifests/
    - Bates format: <prefix>-<YYYYMMDD>-<NNNNNN>
    """
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data")
        self.index_path = os.path.join(self.data_dir, "evidence_index.json")
        self.out_dir = os.path.join(self.data_dir, "manifests")
        os.makedirs(self.out_dir, exist_ok=True)

    def _calc_sha256(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def build(self, prefix: str = "AJB", start: int = 1) -> Dict[str, Any]:
        if os.path.exists(self.index_path):
            idx = json.load(open(self.index_path, "r", encoding="utf-8"))
            files = idx.get("files", [])
        else:
            files = []
        today = datetime.date.today().strftime("%Y%m%d")
        rows = []
        n = start
        for rec in files:
            path = rec.get("path")
            try:
                sz = rec.get("size", os.path.getsize(path) if path and os.path.exists(path) else None)
            except Exception:
                sz = None
            sha = rec.get("sha256")
            # If sha missing, try compute (best-effort)
            if not sha and path and os.path.exists(path):
                try:
                    sha = self._calc_sha256(path)
                except Exception:
                    sha = None
            bates = f"{prefix}-{today}-{n:06d}"
            rows.append({
                "bates": bates,
                "path": path,
                "size": sz,
                "sha256": sha
            })
            n += 1
        manifest = {
            "built_at": datetime.datetime.now().isoformat(),
            "prefix": prefix,
            "start": start,
            "count": len(rows),
            "rows": rows
        }
        # Write JSON/CSV
        out_json = os.path.join(self.out_dir, f"manifest_{prefix}_{today}.json")
        out_csv = os.path.join(self.out_dir, f"manifest_{prefix}_{today}.csv")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        import csv
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["bates","path","size","sha256"])
            w.writeheader()
            for r in rows:
                w.writerow(r)
        return {"ok": True, "json": out_json, "csv": out_csv, "count": len(rows)}
