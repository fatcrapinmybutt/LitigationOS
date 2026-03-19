import os, json
from .drivepuller import DrivePuller

class DrivePullerBulk:
    """
    Bulk ingest a list of paths; returns per-path status.
    """
    def run(self, paths, exts=None):
        dp = DrivePuller()
        results = []
        for p in paths or []:
            results.append(dp.ingest_path(p, exts=exts))
        return {"count": len(results), "results": results}
