#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""litigationos.py — Unified CLI wrapper (v1)

Entry point for:
- harvest
- merge
- query
- route

Path stability:
- Use LITIGATIONOS_HOME env var OR %APPDATA%\LitigationOS\litigationos_paths.json
"""
from __future__ import annotations
import argparse, json, os, sys, subprocess
from pathlib import Path

def _appdata_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    return (Path(appdata) / "LitigationOS") if appdata else (Path.home() / ".config" / "LitigationOS")

def _run(script: Path, args: list[str]) -> int:
    if not script.exists():
        print(f"[ERROR] missing script: {script}", file=sys.stderr)
        return 2
    return subprocess.call([sys.executable, str(script), *args])

def cmd_init(ns: argparse.Namespace) -> int:
    home = Path(ns.home).resolve()
    home.mkdir(parents=True, exist_ok=True)
    cfgdir = _appdata_dir()
    cfgdir.mkdir(parents=True, exist_ok=True)
    cfg = cfgdir / "litigationos_paths.json"
    data = {
        "litigationos_home": str(home),
        "default_out": str(home / "HarvestOut"),
        "default_datastore": str(home / "Datastore"),
        "default_query_out": str(home / "QueryOut"),
        "default_paths_file": str(home / "drivesANDpaths.txt")
    }
    cfg.write_text(json.dumps(data, indent=2), encoding="utf-8")
    marker = home / ".litigationos_root"
    if not marker.exists():
        marker.write_text("LitigationOS root marker\n", encoding="utf-8")
    print(f"[OK] wrote config: {cfg}")
    print(f"[OK] wrote marker: {marker}")
    print(f'Recommended: setx LITIGATIONOS_HOME "{home}"')
    return 0

def cmd_harvest(ns: argparse.Namespace) -> int:
    here = Path(__file__).resolve().parent
    script = here / "HARVEST_ENGINE_FULL_v2.py"
    args = []
    if ns.paths_file: args += ["--paths-file", ns.paths_file]
    if ns.out: args += ["--out", ns.out]
    if ns.pdf_extract: args += ["--pdf-extract"]
    if ns.resume: args += ["--resume"]
    if ns.unzip: args += ["--unzip"]
    return _run(script, args)

def cmd_merge(ns: argparse.Namespace) -> int:
    here = Path(__file__).resolve().parent
    script = here / "merge_cycle_csvs_into_datastore_v2.py"
    args = []
    if ns.out_db: args += ["--out-db", ns.out_db]
    if ns.import_index: args += ["--import-index", ns.import_index]
    if ns.build_fts: args += ["--build-fts"]
    if ns.build_neighbors: args += ["--build-neighbors"]
    return _run(script, args)

def cmd_query(ns: argparse.Namespace) -> int:
    here = Path(__file__).resolve().parent
    script = here / "graphrag_query_v2.py"
    args = ["--query", ns.query]
    if ns.fts: args += ["--fts", ns.fts]
    if ns.neighbors: args += ["--neighbors", ns.neighbors]
    if ns.out_json: args += ["--out-json", ns.out_json]
    if ns.out_md: args += ["--out-md", ns.out_md]
    args += ["--topk", str(ns.topk), "--expand-k", str(ns.expand_k)]
    return _run(script, args)

def cmd_route(ns: argparse.Namespace) -> int:
    here = Path(__file__).resolve().parent
    script = here / "issue_vehicle_router_stub_v2.py"
    args = ["--issue", ns.issue]
    if ns.fts: args += ["--fts", ns.fts]
    if ns.neighbors: args += ["--neighbors", ns.neighbors]
    if ns.out: args += ["--out", ns.out]
    if ns.out_md: args += ["--out-md", ns.out_md]
    return _run(script, args)

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="litigationos", description="Unified LitigationOS CLI wrapper")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("init-config", help="Write config under AppData and root marker")
    a.add_argument("--home", required=True)
    a.set_defaults(func=cmd_init)

    h = sub.add_parser("harvest", help="Run harvest engine")
    h.add_argument("--paths-file")
    h.add_argument("--out")
    h.add_argument("--pdf-extract", action="store_true")
    h.add_argument("--resume", action="store_true")
    h.add_argument("--unzip", action="store_true")
    h.set_defaults(func=cmd_harvest)

    m = sub.add_parser("merge", help="Merge CSVs into datastore")
    m.add_argument("--out-db")
    m.add_argument("--import-index")
    m.add_argument("--build-fts", action="store_true")
    m.add_argument("--build-neighbors", action="store_true")
    m.set_defaults(func=cmd_merge)

    q = sub.add_parser("query", help="GraphRAG query")
    q.add_argument("--fts")
    q.add_argument("--neighbors")
    q.add_argument("--query", required=True)
    q.add_argument("--out-json")
    q.add_argument("--out-md")
    q.add_argument("--topk", type=int, default=25)
    q.add_argument("--expand-k", type=int, default=25)
    q.set_defaults(func=cmd_query)

    r = sub.add_parser("route", help="Issue→Vehicle router stub")
    r.add_argument("--issue", required=True)
    r.add_argument("--fts")
    r.add_argument("--neighbors")
    r.add_argument("--out")
    r.add_argument("--out-md")
    r.set_defaults(func=cmd_route)

    ns = p.parse_args(argv)
    return int(ns.func(ns))

if __name__ == "__main__":
    raise SystemExit(main())
