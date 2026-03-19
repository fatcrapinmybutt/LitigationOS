#!/usr/bin/env python3
"""MI Appellate DocForge V8 Orchestrator (skeleton)
Non-destructive scan/extract/index/pack compiler. No SHA-256 default.
"""
from __future__ import annotations
import argparse, json, logging, os, sqlite3, sys, time
from pathlib import Path
from datetime import datetime, timezone

def utcnow():
    return datetime.now(timezone.utc).isoformat()

def setup_logging(log_path: Path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )

def load_config(p: Path) -> dict:
    text = p.read_text(encoding="utf-8")
    # naive JSONC strip (safe enough for controlled config)
    lines = []
    for line in text.splitlines():
        if line.strip().startswith("//"):
            continue
        lines.append(line)
    raw = "\n".join(lines)
    return json.loads(raw)

def init_db(db_path: Path, schema_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    try:
        con.executescript(schema_path.read_text(encoding="utf-8"))
        con.commit()
    finally:
        con.close()

def readonly_walk(roots: list[str]):
    for root in roots:
        p = Path(root)
        if not p.exists():
            logging.warning("ROOT_MISSING %s", root)
            continue
        for dirpath, _, filenames in os.walk(p):
            for fn in filenames:
                yield Path(dirpath) / fn

def identity_record(path: Path) -> dict:
    st = path.stat()
    rec = {
        "source_path_norm": str(path).replace("\\","/"),
        "bytes_size": int(st.st_size),
        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
        "ctime_utc": datetime.fromtimestamp(st.st_ctime, tz=timezone.utc).isoformat(),
        "file_id": None,
        "volume_serial": None,
    }
    # Windows file_id/volume_serial can be added later via ctypes; omitted fail-soft.
    return rec

def cmd_scan(args):
    cfg = load_config(Path(args.config))
    out_dir = Path(cfg["workspace"]["derived_root"]) / "10_LOGS"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    count = 0
    for path in readonly_walk(cfg["workspace"]["roots"]):
        try:
            rec = identity_record(path)
            rec["ext"] = path.suffix.lower()
            rec["discovered_at_utc"] = utcnow()
            rows.append(rec)
            count += 1
            if count % 500 == 0:
                logging.info("SCANNED %s files", count)
        except Exception as e:
            logging.exception("SCAN_FAIL path=%s err=%s", path, e)
    out_json = out_dir / f"scan_inventory_{int(time.time())}.json"
    out_json.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    logging.info("SCAN_DONE files=%s out=%s", count, out_json)

def cmd_initdb(args):
    init_db(Path(args.db), Path(args.schema))
    logging.info("DB_INIT %s", args.db)

def build_parser():
    p = argparse.ArgumentParser(description="MI Appellate DocForge V8")
    sub = p.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("scan", help="Read-only scan roots and emit inventory")
    s1.add_argument("--config", required=True)
    s1.set_defaults(func=cmd_scan)

    s2 = sub.add_parser("initdb", help="Initialize SQLite schema")
    s2.add_argument("--db", required=True)
    s2.add_argument("--schema", required=True)
    s2.set_defaults(func=cmd_initdb)

    return p

def main():
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(Path("./mi_docforge_v8_run.log"))
    try:
        args.func(args)
    except Exception as e:
        logging.exception("FATAL %s", e)
        raise SystemExit(1)

if __name__ == "__main__":
    main()
