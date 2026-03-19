import os
from .ingest import IngestEngine

class DrivePuller:
    """
    Treats any mounted path (e.g., rclone WinFSP mount like X:\\) as an ingest root.
    """
    def __init__(self):
        self.ingest = IngestEngine()

    def ingest_path(self, path: str, exts = None):
        exts = exts or [".pdf",".docx",".txt",".csv",".json",".png",".jpg"]
        exists = os.path.exists(path)
        if not exists:
            return {"ok": False, "error": f"Path not found: {path}"}
        res = self.ingest.run(paths=[path], exts=exts)
        return {"ok": True, "indexed": res.get("indexed", 0), "index_path": res.get("index_path"), "path": path}
