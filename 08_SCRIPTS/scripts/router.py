from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os, hashlib, datetime, difflib, json

router = APIRouter()

SNAP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/snapshots"))
DIFF_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../storage/diffs"))
os.makedirs(SNAP_DIR, exist_ok=True)
os.makedirs(DIFF_DIR, exist_ok=True)

def _hash(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

@router.post("/scan")
def scan_rules():
    """
    Snapshot-and-diff pipeline (scaffold):
    - Reads any .txt files in storage/snapshots/sources
    - Creates a timestamped consolidated snapshot
    - Diffs against previous snapshot and writes a redline .diff
    """
    sources_dir = os.path.join(SNAP_DIR, "sources")
    os.makedirs(sources_dir, exist_ok=True)
    # Aggregate any source texts (user drops files here)
    texts = []
    for name in sorted(os.listdir(sources_dir)):
        if name.lower().endswith(".txt"):
            with open(os.path.join(sources_dir, name), "r", encoding="utf-8") as f:
                texts.append(f"===== {name} =====\n" + f.read() + "\n")
    merged = "\n".join(texts) if texts else "NO_SOURCES\n"
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_path = os.path.join(SNAP_DIR, f"rules_snapshot_{ts}.txt")
    with open(snap_path, "w", encoding="utf-8") as f:
        f.write(merged)
    # Find previous snapshot
    prev = None
    snaps = sorted([s for s in os.listdir(SNAP_DIR) if s.startswith("rules_snapshot_") and s.endswith(".txt")])
    if len(snaps) >= 2:
        prev = os.path.join(SNAP_DIR, snaps[-2])
    if prev:
        with open(prev, "r", encoding="utf-8") as f:
            old = f.readlines()
        new = merged.splitlines(keepends=True)
        diff = difflib.unified_diff(old, new, fromfile=prev, tofile=snap_path, lineterm="")
        diff_text = "\n".join(diff)
        diff_path = os.path.join(DIFF_DIR, f"rules_redline_{ts}.diff")
        with open(diff_path, "w", encoding="utf-8") as f:
            f.write(diff_text)
    else:
        diff_path = None
    return JSONResponse({"snapshot": snap_path, "redline": diff_path})
