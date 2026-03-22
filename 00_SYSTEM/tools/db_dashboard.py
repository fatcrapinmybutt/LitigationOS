#!/usr/bin/env python3
"""
db_dashboard.py — Quick visual dashboard for all LitigationOS databases.

Displays a formatted table showing every registered database, its size,
table count, and health status. Zero arguments required.

Usage:
    python db_dashboard.py
    python db_dashboard.py --json
    python db_dashboard.py --sort size
"""

import argparse
import json
import os
import sys

# UTF-8 stdout — mandatory for LitigationOS
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)
sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", errors="replace", closefd=False)

# Import UnifiedHub from the same directory (avoids repo-root shadow modules)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from unified_hub import UnifiedHub


def _status_icon(status: str) -> str:
    """Map status string to a visual indicator."""
    return {
        "healthy": "\u2705 Healthy",
        "missing": "\u274c Missing",
        "warning": "\u26a0\ufe0f Warning",
        "error": "\u274c Error",
    }.get(status, f"? {status}")


def _format_size(size_bytes: int) -> str:
    """Human-readable size with consistent width."""
    if size_bytes == 0:
        return "     0 B"
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            if unit == "B":
                return f"{size_bytes:>6} {unit}"
            return f"{size_bytes:>6.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:>6.1f} TB"


def run_dashboard(base_path: str, output_json: bool = False, sort_by: str = "name"):
    """Collect stats from all databases and display the dashboard."""
    hub = UnifiedHub(base_path=base_path)

    # Gather stats for every registered database
    entries = []
    total_size = 0
    total_tables = 0
    healthy_count = 0
    total_count = 0

    for db_name in sorted(hub.registry):
        path = hub.registry[db_name]
        entry = {"name": db_name, "path": str(path)}

        size = hub._db_size(db_name)
        entry["size_bytes"] = size
        entry["size_human"] = _format_size(size)
        total_size += size

        if not path.exists():
            entry["tables"] = 0
            entry["status"] = "missing"
            total_count += 1
            entries.append(entry)
            continue

        total_count += 1
        try:
            row = hub.query_one(
                db_name,
                "SELECT COUNT(*) AS cnt FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%'",
            )
            tcount = row["cnt"] if row else 0
            entry["tables"] = tcount
            total_tables += tcount

            # Quick integrity check
            qc = hub.query(db_name, "PRAGMA quick_check(1)")
            qc_val = ""
            if qc:
                qc_val = qc[0].get("quick_check", qc[0].get("ok", ""))
            entry["status"] = "healthy" if qc_val == "ok" else "warning"
            if entry["status"] == "healthy":
                healthy_count += 1
        except Exception as e:
            entry["tables"] = "?"
            entry["status"] = "error"
            entry["detail"] = str(e)
        finally:
            hub.close(db_name)

        entries.append(entry)

    hub.close_all()

    # Sort
    if sort_by == "size":
        entries.sort(key=lambda e: e.get("size_bytes", 0), reverse=True)
    elif sort_by == "tables":
        entries.sort(key=lambda e: e.get("tables", 0) if isinstance(e.get("tables"), int) else 0, reverse=True)
    # default: already sorted by name

    # Output
    if output_json:
        data = {
            "databases": entries,
            "summary": {
                "total_databases": total_count,
                "total_size_bytes": total_size,
                "total_size_human": _format_size(total_size),
                "total_tables": total_tables,
                "healthy": healthy_count,
                "unhealthy": total_count - healthy_count,
            },
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    # Pretty dashboard
    name_w = max(len("Database"), max((len(e["name"]) for e in entries), default=10))
    size_w = 10
    tbl_w = 8
    status_w = 14

    border = "+" + "-" * (name_w + 2) + "+" + "-" * (size_w + 2) + "+" + "-" * (tbl_w + 2) + "+" + "-" * (status_w + 2) + "+"
    hdr = (
        "| "
        + "Database".ljust(name_w)
        + " | "
        + "Size".rjust(size_w)
        + " | "
        + "Tables".rjust(tbl_w)
        + " | "
        + "Status".ljust(status_w)
        + " |"
    )

    print()
    print("  LitigationOS Database Dashboard")
    print("  " + "=" * (len(border) - 2))
    print("  " + border)
    print("  " + hdr)
    print("  " + border)

    for e in entries:
        name = e["name"].ljust(name_w)
        size = e["size_human"].rjust(size_w) if e.get("size_human") else "—".rjust(size_w)
        tables = str(e.get("tables", "?")).rjust(tbl_w)
        status = _status_icon(e.get("status", "?"))
        # Truncate status to fit column
        if len(status) > status_w:
            status = status[:status_w]
        status = status.ljust(status_w)
        print(f"  | {name} | {size} | {tables} | {status} |")

    print("  " + border)

    # Summary line
    all_ok = healthy_count == total_count
    summary_status = "All healthy" if all_ok else f"{total_count - healthy_count} issue(s)"
    summary = (
        f"  | {'Total: ' + str(total_count) + ' databases':<{name_w}} "
        f"| {_format_size(total_size):>{size_w}} "
        f"| {str(total_tables):>{tbl_w}} "
        f"| {summary_status:<{status_w}} |"
    )
    print(summary)
    print("  " + border)
    print()


def main():
    parser = argparse.ArgumentParser(description="LitigationOS Database Dashboard")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--sort",
        choices=["name", "size", "tables"],
        default="name",
        help="Sort order (default: name)",
    )
    parser.add_argument(
        "--base-path",
        default=r"C:\Users\andre\LitigationOS",
        help="Repository root path",
    )
    args = parser.parse_args()
    run_dashboard(args.base_path, output_json=args.json, sort_by=args.sort)


if __name__ == "__main__":
    main()
