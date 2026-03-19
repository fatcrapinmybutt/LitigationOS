import os, shutil, uuid
from typing import Optional
from fastapi import UploadFile

class GraphEngine:
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data", "graph_runs")
        os.makedirs(self.data_dir, exist_ok=True)

    def save_run(self, nodes: UploadFile, edges: UploadFile, run_id: Optional[str] = None) -> str:
        rid = run_id or uuid.uuid4().hex[:12]
        run_dir = os.path.join(self.data_dir, rid)
        os.makedirs(run_dir, exist_ok=True)

        with open(os.path.join(run_dir, "nodes.csv"), "wb") as f:
            f.write(nodes.file.read())
        with open(os.path.join(run_dir, "edges.csv"), "wb") as f:
            f.write(edges.file.read())
        return rid
