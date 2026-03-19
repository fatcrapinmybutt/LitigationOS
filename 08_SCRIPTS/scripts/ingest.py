import os, json, hashlib
from datetime import datetime
from typing import List, Dict, Any

class IngestEngine:
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.index_path = os.path.join(self.data_dir, "evidence_index.json")

    def _sha256(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def run(self, paths: List[str], exts: List[str]) -> Dict[str, Any]:
        files = []
        for base in paths:
            if not os.path.exists(base):
                continue
            for root, _, names in os.walk(base):
                for n in names:
                    if any(n.lower().endswith(e.lower()) for e in exts):
                        p = os.path.join(root, n)
                        try:
                            files.append({
                                "path": p,
                                "size": os.path.getsize(p),
                                "sha256": self._sha256(p)
                            })
                        except Exception as e:
                            files.append({"path": p, "error": str(e)})
        index = {"run_at": datetime.now().isoformat(), "files": files}
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
        return {"indexed": len(files), "index_path": self.index_path}


    # Drive hook: if a mount like gdrive:/ is included in paths, we just walk it
    # because rclone/WinFSP exposes it as a filesystem. No special handling needed here.
