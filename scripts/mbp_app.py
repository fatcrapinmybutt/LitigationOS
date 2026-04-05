#!/usr/bin/env python
"""THEMANBEARPIG V5.0 — Desktop Application (pywebview).

Wraps the D3.js brain visualization in a native desktop window with a
live Python API bridge to mbp_brain.db.

Usage:
    python -I scripts/mbp_app.py              # Launch application
    python -I scripts/mbp_app.py --port 8888  # Custom HTTP server port
    python -I scripts/mbp_app.py --debug      # Enable dev tools
    python -I scripts/mbp_app.py --export     # Re-export graph data first
"""

from __future__ import annotations

import argparse
import functools
import http.server
import json
import mimetypes
import os
import re
import socket
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import date, datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
BRAIN_DB = REPO_ROOT / "mbp_brain.db"
VIS_DIR = REPO_ROOT / "08_MEDIA" / "MANBEARPIG_V5"
GRAPH_JSON = VIS_DIR / "graph_data.json"
EXPORT_SCRIPT = REPO_ROOT / "scripts" / "export_brain_d3.py"
EVOLVE_SCRIPT = REPO_ROOT / "scripts" / "brain_evolution.py"
SEPARATION_ANCHOR = date(2025, 7, 29)

APP_TITLE = "THEMANBEARPIG V5.0 \u2014 Legal Brain"
APP_BG = "#0a0a0f"
APP_WIDTH = 1600
APP_HEIGHT = 900
APP_MIN_W = 1200
APP_MIN_H = 700

# ── Database helpers ───────────────────────────────────────────────────

_PRAGMAS = (
    "PRAGMA busy_timeout = 60000",
    "PRAGMA journal_mode = WAL",
    "PRAGMA cache_size = -32000",
    "PRAGMA synchronous = NORMAL",
    "PRAGMA temp_store = MEMORY",
)


def _connect() -> sqlite3.Connection:
    """Open a WAL-mode connection to mbp_brain.db with safe PRAGMAs."""
    if not BRAIN_DB.exists():
        raise FileNotFoundError(f"Brain database not found: {BRAIN_DB}")
    conn = sqlite3.connect(str(BRAIN_DB), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    for pragma in _PRAGMAS:
        conn.execute(pragma)
    return conn


def _sanitize_fts(query: str) -> str:
    """Strip dangerous FTS5 metacharacters, keep alphanumerics, spaces, * and quotes."""
    return re.sub(r'[^\w\s*"]', " ", query).strip()


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    """Convert sqlite3.Row list to plain dicts for JSON serialisation."""
    return [dict(r) for r in rows]


# ── HTTP server for static files ───────────────────────────────────────

class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Serves VIS_DIR with correct MIME types and suppressed request logs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(VIS_DIR), **kwargs)

    def log_message(self, fmt, *args):  # noqa: ARG002
        pass  # silence per-request noise

    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def guess_type(self, path):
        """Ensure correct MIME for .json, .js, .mjs files."""
        base, ext = os.path.splitext(path)
        overrides = {
            ".json": "application/json",
            ".js": "application/javascript",
            ".mjs": "application/javascript",
            ".woff2": "font/woff2",
        }
        return overrides.get(ext.lower(), super().guess_type(path))


def _find_free_port() -> int:
    """Find an available TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_http_server(port: int) -> http.server.HTTPServer:
    """Start a threaded HTTP server on *port* serving the visualisation directory."""
    server = http.server.HTTPServer(("127.0.0.1", port), _QuietHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


# ── pywebview Python↔JS API ────────────────────────────────────────────

class BrainAPI:
    """Methods exposed to JavaScript via ``window.pywebview.api.*``."""

    def __init__(self, port: int):
        self._port = port

    # -- node details --------------------------------------------------

    def get_node_details(self, node_id: str) -> dict:
        """Return full node row plus adjacent edges from mbp_brain.db."""
        try:
            conn = _connect()
            node = conn.execute(
                "SELECT * FROM nodes WHERE id = ?", (node_id,)
            ).fetchone()
            if node is None:
                return {"error": f"Node '{node_id}' not found"}

            edges = conn.execute(
                """SELECT e.*, 'outgoing' AS direction
                   FROM edges e WHERE e.source_id = ?
                   UNION ALL
                   SELECT e.*, 'incoming' AS direction
                   FROM edges e WHERE e.target_id = ?""",
                (node_id, node_id),
            ).fetchall()

            chains = conn.execute(
                "SELECT id, chain_path, strength_score, lane, filing_id "
                "FROM chains WHERE chain_path LIKE ?",
                (f"%{node_id}%",),
            ).fetchall()

            gaps = conn.execute(
                "SELECT * FROM gaps WHERE node_id = ? AND resolved = 0",
                (node_id,),
            ).fetchall()
            conn.close()

            return {
                "node": dict(node),
                "edges": _rows_to_dicts(edges),
                "chains": _rows_to_dicts(chains),
                "gaps": _rows_to_dicts(gaps),
                "edge_count": len(edges),
                "chain_count": len(chains),
                "gap_count": len(gaps),
            }
        except Exception as exc:
            return {"error": str(exc)}

    # -- chain tracing -------------------------------------------------

    def trace_chain(self, node_id: str) -> dict:
        """Return all chains passing through *node_id*."""
        try:
            conn = _connect()
            chains = conn.execute(
                "SELECT * FROM chains WHERE chain_path LIKE ? "
                "ORDER BY strength_score DESC",
                (f"%{node_id}%",),
            ).fetchall()
            conn.close()

            result = []
            for ch in chains:
                d = dict(ch)
                try:
                    d["path_nodes"] = json.loads(d.get("chain_path", "[]"))
                except (json.JSONDecodeError, TypeError):
                    d["path_nodes"] = []
                result.append(d)

            return {"chains": result, "count": len(result)}
        except Exception as exc:
            return {"error": str(exc)}

    # -- search --------------------------------------------------------

    def search_nodes(self, query: str) -> dict:
        """FTS-style search across node labels.  Falls back to LIKE."""
        if not query or not query.strip():
            return {"results": [], "count": 0, "method": "empty"}

        safe_q = _sanitize_fts(query)
        if not safe_q:
            return {"results": [], "count": 0, "method": "sanitized_empty"}

        try:
            conn = _connect()

            # Check if nodes_fts table exists for FTS5
            fts_exists = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='nodes_fts'"
            ).fetchone()

            if fts_exists:
                try:
                    rows = conn.execute(
                        "SELECT n.* FROM nodes_fts f "
                        "JOIN nodes n ON f.rowid = n.rowid "
                        "WHERE nodes_fts MATCH ? LIMIT 200",
                        (safe_q,),
                    ).fetchall()
                    conn.close()
                    return {
                        "results": _rows_to_dicts(rows),
                        "count": len(rows),
                        "method": "fts5",
                    }
                except sqlite3.OperationalError:
                    pass  # fall through to LIKE

            # LIKE fallback — search label, description, id
            like_pat = f"%{safe_q}%"
            rows = conn.execute(
                "SELECT * FROM nodes "
                "WHERE label LIKE ? OR description LIKE ? OR id LIKE ? "
                "ORDER BY CASE WHEN label LIKE ? THEN 0 ELSE 1 END "
                "LIMIT 200",
                (like_pat, like_pat, like_pat, like_pat),
            ).fetchall()
            conn.close()
            return {
                "results": _rows_to_dicts(rows),
                "count": len(rows),
                "method": "like",
            }
        except Exception as exc:
            return {"error": str(exc), "results": [], "count": 0}

    # -- statistics ----------------------------------------------------

    def get_stats(self) -> dict:
        """Return brain-wide statistics in a single query round-trip."""
        try:
            conn = _connect()
            row = conn.execute(
                """SELECT
                    (SELECT COUNT(*) FROM nodes)              AS node_count,
                    (SELECT COUNT(*) FROM edges)              AS edge_count,
                    (SELECT COUNT(*) FROM chains)             AS chain_count,
                    (SELECT COUNT(*) FROM gaps)               AS gap_total,
                    (SELECT COUNT(*) FROM gaps WHERE resolved = 0) AS gap_open,
                    (SELECT COUNT(*) FROM gaps WHERE priority = 'HIGH' AND resolved = 0) AS gap_high,
                    (SELECT MAX(version) FROM versions)       AS brain_version
                """
            ).fetchone()

            layers = conn.execute(
                "SELECT layer, COUNT(*) AS cnt FROM nodes GROUP BY layer ORDER BY cnt DESC"
            ).fetchall()

            edge_types = conn.execute(
                "SELECT edge_type, COUNT(*) AS cnt FROM edges GROUP BY edge_type ORDER BY cnt DESC"
            ).fetchall()

            lanes = conn.execute(
                "SELECT lane, COUNT(*) AS cnt FROM nodes WHERE lane != '' "
                "GROUP BY lane ORDER BY cnt DESC"
            ).fetchall()

            top_chains = conn.execute(
                "SELECT id, strength_score, lane, filing_id "
                "FROM chains ORDER BY strength_score DESC LIMIT 5"
            ).fetchall()

            conn.close()

            separation_days = (date.today() - SEPARATION_ANCHOR).days

            return {
                "node_count": row["node_count"],
                "edge_count": row["edge_count"],
                "chain_count": row["chain_count"],
                "gap_total": row["gap_total"],
                "gap_open": row["gap_open"],
                "gap_high": row["gap_high"],
                "brain_version": row["brain_version"] or 0,
                "separation_days": separation_days,
                "layers": _rows_to_dicts(layers),
                "edge_types": _rows_to_dicts(edge_types),
                "lanes": _rows_to_dicts(lanes),
                "top_chains": _rows_to_dicts(top_chains),
            }
        except Exception as exc:
            return {"error": str(exc)}

    # -- gaps ----------------------------------------------------------

    def get_gaps(self, priority: str = "") -> dict:
        """Return unresolved gaps, optionally filtered by priority."""
        try:
            conn = _connect()
            if priority and priority.upper() in ("HIGH", "MEDIUM", "LOW"):
                rows = conn.execute(
                    "SELECT * FROM gaps WHERE resolved = 0 AND priority = ? "
                    "ORDER BY created_at DESC LIMIT 500",
                    (priority.upper(),),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM gaps WHERE resolved = 0 "
                    "ORDER BY CASE priority "
                    "  WHEN 'HIGH' THEN 0 WHEN 'MEDIUM' THEN 1 ELSE 2 END, "
                    "created_at DESC LIMIT 500"
                ).fetchall()
            conn.close()

            summary = {}
            for r in rows:
                p = r["priority"] or "UNKNOWN"
                summary[p] = summary.get(p, 0) + 1

            return {
                "gaps": _rows_to_dicts(rows),
                "count": len(rows),
                "by_priority": summary,
            }
        except Exception as exc:
            return {"error": str(exc)}

    # -- evolution trigger ---------------------------------------------

    def run_evolution(self) -> dict:
        """Run brain_evolution.py --stats (safe, read-only) and return summary.

        Full --evolve mutates the DB; we expose --stats by default through
        the GUI.  Call with caution from the desktop app.
        """
        if not EVOLVE_SCRIPT.exists():
            return {"error": f"Evolution script not found: {EVOLVE_SCRIPT}"}
        try:
            result = subprocess.run(
                [sys.executable, "-I", str(EVOLVE_SCRIPT), "--stats"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(REPO_ROOT),
            )
            return {
                "stdout": result.stdout[-4000:] if result.stdout else "",
                "stderr": result.stderr[-2000:] if result.stderr else "",
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": "Evolution script timed out after 120 seconds"}
        except Exception as exc:
            return {"error": str(exc)}

    # -- data refresh --------------------------------------------------

    def refresh_data(self) -> dict:
        """Re-export graph_data.json via export_brain_d3.py, return status."""
        if not EXPORT_SCRIPT.exists():
            return {"error": f"Export script not found: {EXPORT_SCRIPT}"}
        try:
            result = subprocess.run(
                [sys.executable, "-I", str(EXPORT_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(REPO_ROOT),
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[-4000:] if result.stdout else "",
                "stderr": result.stderr[-2000:] if result.stderr else "",
                "returncode": result.returncode,
                "message": "Reload the page to see updated data"
                if result.returncode == 0
                else "Export failed — check stderr",
            }
        except subprocess.TimeoutExpired:
            return {"error": "Export script timed out after 120 seconds"}
        except Exception as exc:
            return {"error": str(exc)}


# ── Console banner ─────────────────────────────────────────────────────

def _print_banner(port: int, stats: dict) -> None:
    sep_days = (date.today() - SEPARATION_ANCHOR).days
    brain_v = stats.get("brain_version", "?")
    nodes = stats.get("node_count", "?")
    edges = stats.get("edge_count", "?")
    chains = stats.get("chain_count", "?")
    gaps = stats.get("gap_open", "?")

    print()
    print("=" * 62)
    print("  THEMANBEARPIG V5.0 — Legal Brain Visualization")
    print("=" * 62)
    print(f"  HTTP server .... http://127.0.0.1:{port}/")
    print(f"  Brain DB ....... {BRAIN_DB}")
    print(f"  Brain version .. v{brain_v}")
    print(f"  Nodes .......... {nodes:,}" if isinstance(nodes, int) else f"  Nodes .......... {nodes}")
    print(f"  Edges .......... {edges:,}" if isinstance(edges, int) else f"  Edges .......... {edges}")
    print(f"  Chains ......... {chains:,}" if isinstance(chains, int) else f"  Chains ......... {chains}")
    print(f"  Open gaps ...... {gaps:,}" if isinstance(gaps, int) else f"  Open gaps ...... {gaps}")
    print(f"  Separation ..... {sep_days} days (since 2025-07-29)")
    print("-" * 62)
    print("  Close window or press Ctrl+C to exit")
    print("=" * 62)
    print()


# ── Data pre-check / export ───────────────────────────────────────────

def _ensure_graph_data(force: bool = False) -> bool:
    """If graph_data.json is missing (or *force*), run the export script."""
    if GRAPH_JSON.exists() and not force:
        return True
    if not EXPORT_SCRIPT.exists():
        print(f"ERROR: Export script not found: {EXPORT_SCRIPT}", file=sys.stderr)
        return False
    print("Exporting graph data from brain database ...")
    result = subprocess.run(
        [sys.executable, "-I", str(EXPORT_SCRIPT)],
        cwd=str(REPO_ROOT),
        timeout=300,
    )
    if result.returncode != 0:
        print("ERROR: graph_data.json export failed.", file=sys.stderr)
        return False
    print(f"Export complete: {GRAPH_JSON}")
    return True


# ── System tray (optional — only if pystray is available) ─────────────

def _try_system_tray(window) -> None:
    """Start a system-tray icon if pystray + Pillow are installed."""
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        return  # silently skip — tray is optional

    def _make_icon() -> Image.Image:
        img = Image.new("RGBA", (64, 64), (10, 10, 15, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill=(77, 150, 255, 220))
        draw.text((20, 18), "M", fill=(255, 255, 255, 255))
        return img

    def _show(icon, item):
        window.show()

    def _hide(icon, item):
        window.hide()

    def _refresh(icon, item):
        api = window._js_api  # noqa: SLF001
        if api:
            api.refresh_data()

    def _evolve(icon, item):
        api = window._js_api  # noqa: SLF001
        if api:
            api.run_evolution()

    def _quit(icon, item):
        icon.stop()
        window.destroy()

    icon = pystray.Icon(
        "THEMANBEARPIG",
        _make_icon(),
        "THEMANBEARPIG V5",
        menu=pystray.Menu(
            pystray.MenuItem("Show", _show, default=True),
            pystray.MenuItem("Hide", _hide),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Re-export data", _refresh),
            pystray.MenuItem("Brain stats", _evolve),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", _quit),
        ),
    )

    tray_thread = threading.Thread(target=icon.run, daemon=True)
    tray_thread.start()


# ── Main ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="THEMANBEARPIG V5.0 — Legal Brain Desktop Application"
    )
    parser.add_argument(
        "--port", type=int, default=0,
        help="HTTP server port (0 = auto-select free port)"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable developer tools in webview window"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Re-export graph_data.json before launching"
    )
    args = parser.parse_args()

    # -- dependency gate -----------------------------------------------
    try:
        import webview  # noqa: E402
    except ImportError:
        print(
            "ERROR: pywebview is not installed.\n"
            "Install it with:  pip install pywebview\n"
            "On Windows you may also need:  pip install pythonnet",
            file=sys.stderr,
        )
        sys.exit(1)

    # -- pre-flight checks ---------------------------------------------
    if not BRAIN_DB.exists():
        print(f"ERROR: Brain database not found at {BRAIN_DB}", file=sys.stderr)
        print("Run:  python -I scripts/build_mbp_brain.py", file=sys.stderr)
        sys.exit(1)

    if not VIS_DIR.exists():
        print(f"ERROR: Visualisation directory not found at {VIS_DIR}", file=sys.stderr)
        sys.exit(1)

    if not _ensure_graph_data(force=args.export):
        sys.exit(1)

    # -- gather stats for banner ---------------------------------------
    api = BrainAPI(port=0)
    stats = api.get_stats()

    # -- start HTTP server ---------------------------------------------
    port = args.port or _find_free_port()
    server = _start_http_server(port)
    api._port = port

    _print_banner(port, stats)

    # -- launch pywebview window ---------------------------------------
    url = f"http://127.0.0.1:{port}/index.html"

    window = webview.create_window(
        APP_TITLE,
        url=url,
        js_api=api,
        width=APP_WIDTH,
        height=APP_HEIGHT,
        min_size=(APP_MIN_W, APP_MIN_H),
        background_color=APP_BG,
        frameless=False,
        easy_drag=False,
        text_select=True,
    )

    _try_system_tray(window)

    webview.start(debug=args.debug)

    # -- cleanup -------------------------------------------------------
    server.shutdown()
    print("THEMANBEARPIG exited.")


if __name__ == "__main__":
    main()
