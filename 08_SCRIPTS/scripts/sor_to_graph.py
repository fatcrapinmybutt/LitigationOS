from pathlib import Path
import zipfile, textwrap, hashlib, json

base_dir = Path("/mnt/data/LITIGATION_OS_GUI_BUNDLE_v1")
base_dir.mkdir(parents=True, exist_ok=True)

# ------------------ sor_to_graph.py ------------------
sor_to_graph_py = textwrap.dedent(r'''
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set


@dataclass
class GraphConfig:
    sor_csv: Path
    out_dir: Path
    max_docs: Optional[int] = None


def load_sor_rows(csv_path: Path, max_docs: Optional[int] = None) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            if max_docs is not None and len(rows) >= max_docs:
                break
    return rows


def build_graph(config: GraphConfig) -> Dict[str, Any]:
    rows = load_sor_rows(config.sor_csv, config.max_docs)
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    node_ids: Set[str] = set()

    def add_node(node_id: str, label: str, **attrs: Any) -> None:
        if node_id in node_ids:
            return
        node_ids.add(node_id)
        node = {"id": node_id, "label": label}
        node.update(attrs)
        nodes.append(node)

    def add_edge(source: str, target: str, label: str, **attrs: Any) -> None:
        edge = {"source": source, "target": target, "label": label}
        edge.update(attrs)
        edges.append(edge)

    for row in rows:
        doc_id = row.get("doc_id") or ""
        file_path = row.get("file_path") or ""
        file_type = row.get("file_type") or ""
        file_role = row.get("file_role") or ""
        case_hint = row.get("case_hint") or ""
        modified_at = row.get("modified_at") or ""
        size_bytes = row.get("size_bytes") or ""

        doc_node_id = f"doc:{doc_id}"
        add_node(
            doc_node_id,
            "Document",
            doc_id=doc_id,
            path=file_path,
            file_type=file_type,
            file_role=file_role,
            case_hint=case_hint,
            modified_at=modified_at,
            size_bytes=size_bytes,
        )

        if case_hint:
            case_node_id = f"case:{case_hint}"
            add_node(case_node_id, "Case", case_hint=case_hint)
            add_edge(doc_node_id, case_node_id, "BELONGS_TO")

        if file_role:
            role_node_id = f"role:{file_role}"
            add_node(role_node_id, "Role", role=file_role)
            add_edge(doc_node_id, role_node_id, "HAS_ROLE")

        if file_type:
            type_node_id = f"type:{file_type}"
            add_node(type_node_id, "Type", file_type=file_type)
            add_edge(doc_node_id, type_node_id, "HAS_TYPE")

    config.out_dir.mkdir(parents=True, exist_ok=True)
    graph = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_csv": str(config.sor_csv),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
    }

    out_path = config.out_dir / "sor_graph.json"
    out_path.write_text(json.dumps(graph, indent=2), encoding="utf-8")

    # Also write a compact index by case
    case_index: Dict[str, Dict[str, Any]] = {}
    for node in nodes:
        if node.get("label") == "Document":
            case_hint = node.get("case_hint") or ""
            if not case_hint:
                continue
            case_entry = case_index.setdefault(case_hint, {"case_hint": case_hint, "doc_ids": []})
            case_entry["doc_ids"].append(node.get("doc_id"))

    index_path = config.out_dir / "case_index.json"
    index_path.write_text(json.dumps(case_index, indent=2), encoding="utf-8")

    return graph


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert SOR_OUT/sor_files.csv into a simple JSON graph structure "
            "for Neo4j/graph tooling, with nodes for documents, cases, roles, and types."
        )
    )
    parser.add_argument(
        "--sor-csv",
        type=str,
        default="SOR_OUT/sor_files.csv",
        help="Path to sor_files.csv (default: SOR_OUT/sor_files.csv).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="GRAPH_OUT",
        help="Directory to write sor_graph.json and case_index.json (default: GRAPH_OUT).",
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=None,
        help="Optional cap on documents processed (for testing).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    sor_csv = Path(args.sor_csv)
    if not sor_csv.exists():
        print(f"ERROR: SoR CSV not found at {sor_csv}")
        raise SystemExit(1)

    out_dir = Path(args.out_dir)
    config = GraphConfig(sor_csv=sor_csv, out_dir=out_dir, max_docs=args.max_docs)

    graph = build_graph(config)
    print("Graph build complete.")
    print(f"Nodes: {graph['node_count']}, edges: {graph['edge_count']}")
    print(f"Graph JSON: {out_dir / 'sor_graph.json'}")
    print(f"Case index: {out_dir / 'case_index.json'}")


if __name__ == "__main__":
    main()
''').strip()

(base_dir / "sor_to_graph.py").write_text(sor_to_graph_py, encoding="utf-8")


# ------------------ timeline_builder.py ------------------
timeline_builder_py = textwrap.dedent(r'''
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class TimelineConfig:
    sor_csv: Path
    out_dir: Path
    max_docs: Optional[int] = None


def load_sor_rows(csv_path: Path, max_docs: Optional[int] = None) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            if max_docs is not None and len(rows) >= max_docs:
                break
    return rows


def build_timelines(config: TimelineConfig) -> Dict[str, Any]:
    rows = load_sor_rows(config.sor_csv, config.max_docs)
    buckets: Dict[str, List[Dict[str, str]]] = defaultdict(list)

    for r in rows:
        case_hint = (r.get("case_hint") or "").strip()
        if not case_hint:
            continue
        buckets[case_hint].append(r)

    config.out_dir.mkdir(parents=True, exist_ok=True)
    index: Dict[str, Any] = {}

    for case_hint, docs in buckets.items():
        def parse_ts(ts: str) -> datetime:
            try:
                return datetime.fromisoformat(ts)
            except Exception:
                return datetime.min

        docs_sorted = sorted(docs, key=lambda r: parse_ts(r.get("modified_at", "")))

        csv_name = f"{case_hint.replace('/', '_').replace(':', '_')}_timeline.csv"
        out_path = config.out_dir / csv_name

        fieldnames = [
            "event_id",
            "doc_id",
            "case_hint",
            "modified_at",
            "file_role",
            "file_type",
            "file_path",
        ]

        with out_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for idx, r in enumerate(docs_sorted, start=1):
                writer.writerow({
                    "event_id": idx,
                    "doc_id": r.get("doc_id", ""),
                    "case_hint": case_hint,
                    "modified_at": r.get("modified_at", ""),
                    "file_role": r.get("file_role", ""),
                    "file_type": r.get("file_type", ""),
                    "file_path": r.get("file_path", ""),
                })

        index[case_hint] = {
            "case_hint": case_hint,
            "timeline_csv": str(out_path),
            "event_count": len(docs_sorted),
        }

    index_path = config.out_dir / "timeline_index.json"
    index_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_csv": str(config.sor_csv),
        "cases": list(index.values()),
    }
    index_path.write_text(json.dumps(index_payload, indent=2), encoding="utf-8")

    return index_payload


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build per-case chronological timelines from SOR_OUT/sor_files.csv. "
            "Each case_hint gets its own *_timeline.csv with events sorted by modified_at."
        )
    )
    parser.add_argument(
        "--sor-csv",
        type=str,
        default="SOR_OUT/sor_files.csv",
        help="Path to sor_files.csv (default: SOR_OUT/sor_files.csv).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="TIMELINES_OUT",
        help="Directory to write timeline CSVs and timeline_index.json (default: TIMELINES_OUT).",
    )
    parser.add_argument(
        "--max-docs",
        type=int,
        default=None,
        help="Optional cap on documents processed (for testing).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    sor_csv = Path(args.sor_csv)
    if not sor_csv.exists():
        print(f"ERROR: SoR CSV not found at {sor_csv}")
        raise SystemExit(1)

    out_dir = Path(args.out_dir)
    config = TimelineConfig(sor_csv=sor_csv, out_dir=out_dir, max_docs=args.max_docs)
    index = build_timelines(config)

    print("Timeline build complete.")
    print(f"Cases with timelines: {len(index.get('cases', []))}")
    print(f"Index: {out_dir / 'timeline_index.json'}")


if __name__ == "__main__":
    main()
''').strip()

(base_dir / "timeline_builder.py").write_text(timeline_builder_py, encoding="utf-8")


# ------------------ engine_diagnostics.py ------------------
engine_diag_py = textwrap.dedent(r'''
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class PathCheck:
    path: str
    exists: bool
    is_file: bool
    is_dir: bool


@dataclass
class DiagnosticsReport:
    root: str
    generated_at: str
    scripts: List[PathCheck]
    folders: List[PathCheck]
    sor_present: bool
    packs_present: bool
    graph_present: bool
    timelines_present: bool


def check_path(p: Path) -> PathCheck:
    return PathCheck(
        path=str(p),
        exists=p.exists(),
        is_file=p.is_file(),
        is_dir=p.is_dir(),
    )


def run_diagnostics(root: Path) -> DiagnosticsReport:
    scripts_to_check = [
        "autopilot.py",
        "bucket_organizer_omni.py",
        "build_nucleus_wheel_v3.py",
        "omni_allinone_runner_v3_6.py",
        "omni_echelon_builder.py",
        "omni_echelon_v3_upgrade.py",
        "bootstrap_mindseye2_graph_core_os.py",
        "gui_main.py",
        "litigation_sor_entrypoint.py",
        "pack_builder.py",
        "query_sor.py",
        "sor_to_graph.py",
        "timeline_builder.py",
    ]

    folders_to_check = [
        "config",
        "graph_data",
        "logs",
        "logs_templates",
        "neo4j",
        "scripts",
        "state",
        "ui",
        "SOR_OUT",
        "PACKS",
        "GRAPH_OUT",
        "TIMELINES_OUT",
        "DIAGNOSTICS_OUT",
    ]

    script_checks = [check_path(root / s) for s in scripts_to_check]
    folder_checks = [check_path(root / d) for d in folders_to_check]

    sor_csv = root / "SOR_OUT" / "sor_files.csv"
    packs_dir = root / "PACKS"
    graph_json = root / "GRAPH_OUT" / "sor_graph.json"
    timeline_index = root / "TIMELINES_OUT" / "timeline_index.json"

    report = DiagnosticsReport(
        root=str(root),
        generated_at=datetime.now().isoformat(timespec="seconds"),
        scripts=script_checks,
        folders=folder_checks,
        sor_present=sor_csv.exists(),
        packs_present=packs_dir.exists(),
        graph_present=graph_json.exists(),
        timelines_present=timeline_index.exists(),
    )

    out_dir = root / "DIAGNOSTICS_OUT"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "engine_status.json"
    json_path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")

    # Human-readable summary
    lines: List[str] = []
    lines.append(f"Diagnostics for root: {root}")
    lines.append(f"Generated at: {report.generated_at}")
    lines.append("")
    lines.append("Scripts:")
    for s in script_checks:
        status = "OK" if s.exists and s.is_file else "MISSING"
        lines.append(f"  - {s.path}: {status}")
    lines.append("")
    lines.append("Folders:")
    for d in folder_checks:
        status = "OK" if d.exists and d.is_dir else "MISSING"
        lines.append(f"  - {d.path}: {status}")
    lines.append("")
    lines.append(f"SoR present: {report.sor_present}")
    lines.append(f"Packs present: {report.packs_present}")
    lines.append(f"Graph present: {report.graph_present}")
    lines.append(f"Timelines present: {report.timelines_present}")

    txt_path = out_dir / "engine_status.txt"
    txt_path.write_text("\n".join(lines), encoding="utf-8")

    return report


def main() -> None:
    root = Path(__file__).resolve().parent
    report = run_diagnostics(root)
    print("Diagnostics complete.")
    print(f"Root: {report.root}")
    print(f"SoR present: {report.sor_present}")
    print(f"Packs present: {report.packs_present}")
    print(f"Graph present: {report.graph_present}")
    print(f"Timelines present: {report.timelines_present}")
    print(f"See DIAGNOSTICS_OUT/engine_status.json and engine_status.txt for details.")


if __name__ == "__main__":
    main()
''').strip()

(base_dir / "engine_diagnostics.py").write_text(engine_diag_py, encoding="utf-8")


# ------------------ pack_to_zip.py ------------------
pack_to_zip_py = textwrap.dedent(r'''
from __future__ import annotations

import argparse
import zipfile
from pathlib import Path
from typing import Optional


def build_pack_zip(root: Path, case_id: str, pack_type: str, out_dir: Optional[Path] = None) -> Path:
    packs_dir = root / "PACKS" / case_id / pack_type.lower()
    if not packs_dir.exists() or not packs_dir.is_dir():
        raise FileNotFoundError(f"Pack directory not found: {packs_dir}")

    out_dir = out_dir or (root / "PACKS_ZIP")
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_case = case_id.replace("/", "_").replace(":", "_")
    zip_name = f"{safe_case}_{pack_type.lower()}.zip"
    zip_path = out_dir / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in packs_dir.rglob("*"):
            if p.is_file():
                rel = p.relative_to(root)
                zf.write(p, rel.as_posix())

    return zip_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Zip an existing PACKS/<case_id>/<pack_type> folder into PACKS_ZIP/<case_id>_<pack_type>.zip"
    )
    parser.add_argument("--case-id", type=str, required=True, help="Case identifier (e.g., 2024-001507-DC)")
    parser.add_argument("--pack-type", type=str, required=True, help="Pack type (e.g., all, ppo, coa, housing)")
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Optional engine root (default: directory of this script).",
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default=None,
        help="Optional output dir for the ZIP (default: <root>/PACKS_ZIP).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root) if args.root else Path(__file__).resolve().parent
    out_dir = Path(args.out_dir) if args.out_dir else None

    try:
        zip_path = build_pack_zip(root=root, case_id=args.case_id, pack_type=args.pack_type, out_dir=out_dir)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)

    print("Pack ZIP created.")
    print(f"ZIP path: {zip_path}")


if __name__ == "__main__":
    main()
''').strip()

(base_dir / "pack_to_zip.py").write_text(pack_to_zip_py, encoding="utf-8")


# ------------------ build_structures.bat ------------------
build_structures_bat = textwrap.dedent(r'''
@echo off
setlocal
cd /d "%~dp0"

if not exist "logs" (
    mkdir "logs"
)

echo Running SoR + Graph + Timelines + Diagnostics pipeline...

echo [1/4] Building SoR snapshot...
python "%~dp0litigation_sor_entrypoint.py" --roots F:\ D:\ G:\ > "logs\build_sor.log" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo SoR build encountered errors. See logs\build_sor.log
    goto :end
)

echo [2/4] Building graph from SoR...
python "%~dp0sor_to_graph.py" > "logs\build_graph.log" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Graph build encountered errors. See logs\build_graph.log
    goto :end
)

echo [3/4] Building timelines from SoR...
python "%~dp0timeline_builder.py" > "logs\build_timelines.log" 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Timeline build encountered errors. See logs\build_timelines.log
    goto :end
)

echo [4/4] Running engine diagnostics...
python "%~dp0engine_diagnostics.py" > "logs\engine_diagnostics.log" 2>&1

echo Pipeline completed. Check:
echo   SOR_OUT\         for SoR snapshot
echo   GRAPH_OUT\       for sor_graph.json + case_index.json
echo   TIMELINES_OUT\   for per-case timelines
echo   DIAGNOSTICS_OUT\ for engine_status.json and engine_status.txt
echo   logs\*.log       for per-step logs

:end
endlocal
''').lstrip()

(base_dir / "build_structures.bat").write_text(build_structures_bat, encoding="utf-8")


# ------------------ Update README & MANIFEST to mention new modules ------------------
readme_path = base_dir / "README.txt"
readme_text = readme_path.read_text(encoding="utf-8")
append_block_readme = ""

if "sor_to_graph.py" not in readme_text:
    append_block_readme += textwrap.dedent(r'''


