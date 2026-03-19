from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os, hashlib, datetime, difflib

router = APIRouter()
SNAP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/snapshots"))
DIFF_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/diffs"))
os.makedirs(SNAP_DIR, exist_ok=True); os.makedirs(DIFF_DIR, exist_ok=True)

@router.post("/scan")
def scan_rules():
    src_dir = os.path.join(SNAP_DIR, "sources"); os.makedirs(src_dir, exist_ok=True)
    texts = []
    for name in sorted(os.listdir(src_dir)):
        if name.lower().endswith(".txt"):
            with open(os.path.join(src_dir, name), "r", encoding="utf-8") as f:
                texts.append(f"===== {name} =====\n{f.read()}\n")
    merged = "\n".join(texts) if texts else "NO_SOURCES\n"
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snap = os.path.join(SNAP_DIR, f"rules_snapshot_{ts}.txt"); open(snap,"w",encoding="utf-8").write(merged)
    prev = None
    snaps = sorted([s for s in os.listdir(SNAP_DIR) if s.startswith("rules_snapshot_") and s.endswith(".txt")])
    if len(snaps)>=2: prev = os.path.join(SNAP_DIR, snaps[-2])
    diff_path=None
    if prev:
        old = open(prev,"r",encoding="utf-8").read().splitlines(keepends=True)
        new = merged.splitlines(keepends=True)
        diff = "\n".join(difflib.unified_diff(old,new,fromfile=prev,tofile=snap,lineterm=""))
        diff_path = os.path.join(DIFF_DIR, f"rules_redline_{ts}.diff"); open(diff_path,"w",encoding="utf-8").write(diff)
    return JSONResponse({"snapshot":snap,"redline":diff_path})
