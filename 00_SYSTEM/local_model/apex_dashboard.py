#!/usr/bin/env python3
"""
APEX Dashboard — Terminal UI for full APEX system health monitoring.

Shows: model fleet status, DB health, quality trends, active tasks,
learning stats, resource usage.

Run::

    python apex_dashboard.py            # full dashboard
    python apex_dashboard.py models     # model fleet only
    python apex_dashboard.py db         # database health only
    python apex_dashboard.py quality    # quality summary only
    python apex_dashboard.py learning   # learning loop only
    python apex_dashboard.py resources  # CPU / RAM only

Thread-safe, UTF-8 safe, never crashes.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Shadow LLM gate
# ---------------------------------------------------------------------------
APEX_LLM_ENABLED: bool = (
    os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("apex.dashboard")

# ---------------------------------------------------------------------------
# Paths (never CWD — always relative to *this* file)
# ---------------------------------------------------------------------------
_HERE = Path(__file__).parent
_ROOT = _HERE.parent.parent  # LitigationOS root

# ---------------------------------------------------------------------------
# Mandatory DB PRAGMAs
# ---------------------------------------------------------------------------
_DB_PRAGMAS: str = """
PRAGMA busy_timeout  = 60000;
PRAGMA journal_mode  = WAL;
PRAGMA cache_size    = -32000;
PRAGMA temp_store    = MEMORY;
PRAGMA synchronous   = NORMAL;
"""

# ---------------------------------------------------------------------------
# Model fleet definitions
# ---------------------------------------------------------------------------
_MODEL_FLEET: list[dict[str, str]] = [
    {"name": "saul-legal",   "size": "5.1 GB", "role": "Legal reasoning",       "type": "shadow"},
    {"name": "qwen-fast",    "size": "1.1 GB", "role": "Classification",        "type": "shadow"},
    {"name": "nomic-embed",  "size": "0.3 GB", "role": "Embeddings",            "type": "shadow"},
    {"name": "manbearpig",   "size": "0.3 GB", "role": "TF-IDF + NB + BM25",   "type": "active"},
    {"name": "legal-bert",   "size": "0.5 GB", "role": "NER + Reranking",       "type": "cached"},
    {"name": "bert-ner",     "size": "0.5 GB", "role": "Entity Recognition",    "type": "cached"},
    {"name": "minilm",       "size": "0.1 GB", "role": "Semantic Embeddings",   "type": "cached"},
]

# ---------------------------------------------------------------------------
# Known databases to probe
# ---------------------------------------------------------------------------
_KNOWN_DBS: list[dict[str, str]] = [
    {"name": "litigation_context.db", "category": "core"},
    {"name": "master_index.db",       "category": "core"},
    {"name": "omega_dedup.db",        "category": "core"},
    {"name": "lane_A_custody.db",     "category": "lane"},
    {"name": "lane_B_housing.db",     "category": "lane"},
    {"name": "lane_C_convergence.db", "category": "lane"},
    {"name": "lane_D_ppo.db",         "category": "lane"},
    {"name": "lane_E_misconduct.db",  "category": "lane"},
    {"name": "lane_F_appellate.db",   "category": "lane"},
    {"name": "learning_metrics.db",   "category": "apex"},
    {"name": "mcr_rules.db",          "category": "rules"},
    {"name": "document_fulltext.db",  "category": "fts"},
    {"name": "drive_inventory.db",    "category": "inventory"},
    {"name": "file_catalog.db",       "category": "inventory"},
    {"name": "failsafe_incidents.db", "category": "ops"},
    {"name": "test_litigation_os.db", "category": "test"},
    {"name": "MEEK_index.db",         "category": "meek"},
]

# ---------------------------------------------------------------------------
# Box-drawing characters
# ---------------------------------------------------------------------------
_TL = "\u2554"   # ╔
_TR = "\u2557"   # ╗
_BL = "\u255a"   # ╚
_BR = "\u255d"   # ╝
_H  = "\u2550"   # ═
_V  = "\u2551"   # ║
_ML = "\u2560"   # ╠
_MR = "\u2563"   # ╣
_WIDTH = 62


def _box_top() -> str:
    return f"{_TL}{_H * _WIDTH}{_TR}"


def _box_bot() -> str:
    return f"{_BL}{_H * _WIDTH}{_BR}"


def _box_mid() -> str:
    return f"{_ML}{_H * _WIDTH}{_MR}"


def _box_line(text: str) -> str:
    return f"{_V} {text:<{_WIDTH - 1}}{_V}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_connect(db_path: Path) -> Optional[sqlite3.Connection]:
    try:
        if not db_path.exists():
            return None
        conn = sqlite3.connect(str(db_path), timeout=10, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.executescript(_DB_PRAGMAS)
        return conn
    except Exception:  # noqa: BLE001
        return None


def _file_size_str(path: Path) -> str:
    """Human-readable file size."""
    try:
        size = path.stat().st_size
        if size >= 1_073_741_824:
            return f"{size / 1_073_741_824:.2f} GB"
        if size >= 1_048_576:
            return f"{size / 1_048_576:.1f} MB"
        if size >= 1024:
            return f"{size / 1024:.0f} KB"
        return f"{size} B"
    except Exception:  # noqa: BLE001
        return "? B"


def _table_count(conn: sqlite3.Connection) -> int:
    """Count user tables in a connection."""
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchone()
        return row["n"] if row else 0
    except Exception:  # noqa: BLE001
        return 0


# ---------------------------------------------------------------------------
# Lazy loaders for sibling modules (never crash on import failure)
# ---------------------------------------------------------------------------
def _get_learning_loop():
    try:
        from learning_loop import get_learning_loop
        return get_learning_loop()
    except Exception:  # noqa: BLE001
        return None


def _get_quality_feedback():
    try:
        from quality_feedback import get_quality_feedback
        return get_quality_feedback()
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# APEXDashboard
# ---------------------------------------------------------------------------
class APEXDashboard:
    """Terminal-UI dashboard for APEX_MANBEARPIG_LITIGATIONOS health."""

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self._root = root_dir or _ROOT

    # ------------------------------------------------------------------
    # Full render
    # ------------------------------------------------------------------
    def render(self) -> str:
        """Render the complete dashboard as a formatted string."""
        try:
            parts: list[str] = []
            parts.append(_box_top())
            parts.append(_box_line("     APEX_MANBEARPIG_LITIGATIONOS v1.0"))
            parts.append(_box_line("     System Health Dashboard"))
            parts.append(_box_mid())

            # Model fleet
            parts.append(self.model_status())
            parts.append(_box_mid())

            # Database health
            parts.append(self.database_health())
            parts.append(_box_mid())

            # Skills & agents
            parts.append(self._skills_agents_line())

            # Quality summary
            parts.append(self.quality_summary())

            # Learning summary
            parts.append(self.learning_summary())

            parts.append(_box_bot())
            return "\n".join(parts)
        except Exception as exc:  # noqa: BLE001
            return f"[Dashboard render error: {exc}]"

    # ------------------------------------------------------------------
    # Model fleet status
    # ------------------------------------------------------------------
    def model_status(self) -> str:
        """Render model fleet status section."""
        lines: list[str] = []
        try:
            lines.append(_box_line("MODEL FLEET"))

            # Check MANBEARPIG availability
            manbearpig_ok = False
            try:
                ie_path = _HERE / "inference_engine.py"
                manbearpig_ok = ie_path.exists()
            except Exception:  # noqa: BLE001
                pass

            for m in _MODEL_FLEET:
                tag = m["type"].upper()
                if m["name"] == "manbearpig" and manbearpig_ok:
                    tag = "ACTIVE"
                elif m["type"] == "shadow" and not APEX_LLM_ENABLED:
                    tag = "SHADOW"
                elif m["type"] == "cached":
                    # Check if model file or module exists
                    tag = "CACHED"

                line = f"  {m['name']:<14s} {m['size']:>7s}  [{tag:<6s}]  {m['role']}"
                lines.append(_box_line(line))

            llm_label = "ENABLED" if APEX_LLM_ENABLED else "DISABLED (set APEX_LLM_ENABLED=true)"
            lines.append(_box_line(f"  LLM Status: {llm_label}"))
        except Exception as exc:  # noqa: BLE001
            lines.append(_box_line(f"  [model status error: {exc}]"))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Database health
    # ------------------------------------------------------------------
    def database_health(self) -> str:
        """Render database health section."""
        lines: list[str] = []
        try:
            total_size = 0
            total_tables = 0
            ok_count = 0
            err_count = 0
            db_lines: list[str] = []

            # Search multiple directories for DBs
            search_dirs = [self._root, _HERE, self._root / "00_SYSTEM" / "pipeline"]

            found_dbs: dict[str, Path] = {}
            for db_def in _KNOWN_DBS:
                for d in search_dirs:
                    candidate = d / db_def["name"]
                    if candidate.exists():
                        found_dbs[db_def["name"]] = candidate
                        break

            # Also scan for extra .db files in root
            try:
                for p in self._root.glob("*.db"):
                    if p.name not in found_dbs:
                        found_dbs[p.name] = p
            except Exception:  # noqa: BLE001
                pass

            for name, path in sorted(found_dbs.items()):
                try:
                    size = path.stat().st_size
                    total_size += size
                    conn = _safe_connect(path)
                    if conn:
                        tables = _table_count(conn)
                        total_tables += tables
                        conn.close()
                        ok_count += 1
                        size_str = _file_size_str(path)
                        db_lines.append(f"  {name:<28s} {size_str:>9s} {tables:>4d} tables  [OK]")
                    else:
                        err_count += 1
                        db_lines.append(f"  {name:<28s}     ?         ?        [ERR]")
                except Exception:  # noqa: BLE001
                    err_count += 1

            total_str = _file_size_str(Path("x"))  # placeholder
            # Compute total size string manually
            if total_size >= 1_073_741_824:
                total_str = f"{total_size / 1_073_741_824:.2f} GB"
            elif total_size >= 1_048_576:
                total_str = f"{total_size / 1_048_576:.1f} MB"
            else:
                total_str = f"{total_size / 1024:.0f} KB"

            total_db_count = ok_count + err_count
            lines.append(_box_line(f"DATABASES ({total_db_count} found, {total_str})"))

            # Show top DBs by size (limit display to 8)
            for dl in db_lines[:8]:
                lines.append(_box_line(dl))
            if len(db_lines) > 8:
                lines.append(_box_line(f"  ... and {len(db_lines) - 8} more databases"))

            if err_count:
                lines.append(_box_line(f"  ⚠ {err_count} database(s) could not be opened"))
        except Exception as exc:  # noqa: BLE001
            lines.append(_box_line(f"DATABASES"))
            lines.append(_box_line(f"  [database health error: {exc}]"))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Skills & agents summary line
    # ------------------------------------------------------------------
    def _skills_agents_line(self) -> str:
        """Single line for skills + agents count."""
        try:
            # Count skill directories
            skills_dir = self._root / "skills"
            skill_count = 0
            if skills_dir.exists():
                skill_count = sum(1 for p in skills_dir.iterdir() if p.is_dir() or p.suffix in (".py", ".md"))

            # Count agent directories
            agents_dir = self._root / "agents"
            agent_count = 0
            if agents_dir.exists():
                agent_count = sum(1 for p in agents_dir.iterdir() if p.suffix == ".py")

            copilot_agents_dir = self._root / ".copilot" / "agents"
            copilot_count = 0
            if copilot_agents_dir.exists():
                copilot_count = sum(1 for p in copilot_agents_dir.iterdir() if p.suffix == ".md")

            lines = []
            lines.append(_box_line(f"SKILLS: {skill_count} registered"))
            lines.append(_box_line(f"AGENTS: {agent_count} pipeline + {copilot_count} Copilot = {agent_count + copilot_count} total"))
            return "\n".join(lines)
        except Exception as exc:  # noqa: BLE001
            return _box_line(f"SKILLS/AGENTS: [error: {exc}]")

    # ------------------------------------------------------------------
    # Quality summary
    # ------------------------------------------------------------------
    def quality_summary(self) -> str:
        """Render quality metrics section."""
        lines: list[str] = []
        try:
            qf = _get_quality_feedback()
            if qf is None:
                lines.append(_box_line("QUALITY: N/A (quality_feedback module unavailable)"))
                return "\n".join(lines)

            dash = qf.get_dashboard()
            if dash.get("status") != "ok" or dash.get("total_scores", 0) == 0:
                lines.append(_box_line("QUALITY: N/A (no tasks recorded yet)"))
                return "\n".join(lines)

            avg = dash.get("avg_score", 0)
            total = dash.get("total_scores", 0)
            alerts = dash.get("open_alerts", 0)
            status_icon = "\u2714" if avg >= 70 else "\u26a0"  # ✔ or ⚠

            lines.append(_box_line(f"QUALITY: avg {avg:.1f}/100 ({total} scores) {status_icon}"))
            if alerts > 0:
                lines.append(_box_line(f"  \u26a0 {alerts} open quality alert(s)"))

            # Top/bottom models
            rankings = qf.get_model_rankings()
            if rankings:
                best = rankings[0]
                lines.append(_box_line(f"  Best: {best['model']} ({best['avg_score']:.1f})"))
                if len(rankings) > 1:
                    worst = rankings[-1]
                    lines.append(_box_line(f"  Needs work: {worst['model']} ({worst['avg_score']:.1f})"))
        except Exception as exc:  # noqa: BLE001
            lines.append(_box_line(f"QUALITY: [error: {exc}]"))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Learning summary
    # ------------------------------------------------------------------
    def learning_summary(self) -> str:
        """Render learning loop section."""
        lines: list[str] = []
        try:
            ll = _get_learning_loop()
            if ll is None:
                lines.append(_box_line("LEARNING: N/A (learning_loop module unavailable)"))
                return "\n".join(lines)

            s = ll.summary()
            if s.get("status") != "ok":
                lines.append(_box_line("LEARNING: N/A (no data yet)"))
                return "\n".join(lines)

            total = s.get("total_tasks", 0)
            patterns = s.get("patterns_found", 0)
            avg_q = s.get("avg_quality", 0)
            sr = s.get("success_rate", 0)
            drift = s.get("drift_alerts", [])

            if total == 0:
                lines.append(_box_line(f"LEARNING: 0 patterns, 0 outcomes recorded"))
            else:
                lines.append(_box_line(f"LEARNING: {total} outcomes, {patterns} patterns, avg quality {avg_q:.1f}"))
                lines.append(_box_line(f"  Success rate: {sr:.1f}%  |  Models tracked: {s.get('models_tracked', 0)}"))
                if drift:
                    lines.append(_box_line(f"  \u26a0 {len(drift)} quality drift alert(s)"))
        except Exception as exc:  # noqa: BLE001
            lines.append(_box_line(f"LEARNING: [error: {exc}]"))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Resource usage
    # ------------------------------------------------------------------
    def resource_usage(self) -> str:
        """CPU/RAM usage report."""
        lines: list[str] = []
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self._root))

            lines.append(_box_line("RESOURCES"))
            lines.append(_box_line(f"  CPU: {cpu:.1f}%"))
            lines.append(_box_line(
                f"  RAM: {mem.used / 1_073_741_824:.1f} / {mem.total / 1_073_741_824:.1f} GB "
                f"({mem.percent:.0f}%)"
            ))
            lines.append(_box_line(
                f"  Disk: {disk.used / 1_073_741_824:.1f} / {disk.total / 1_073_741_824:.1f} GB "
                f"({disk.percent:.0f}%)"
            ))
        except ImportError:
            lines.append(_box_line("RESOURCES"))
            lines.append(_box_line("  [psutil not installed — pip install psutil]"))
        except Exception as exc:  # noqa: BLE001
            lines.append(_box_line("RESOURCES"))
            lines.append(_box_line(f"  [resource check error: {exc}]"))
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_instance_lock = threading.Lock()
_instance: Optional[APEXDashboard] = None


def get_dashboard() -> APEXDashboard:
    """Thread-safe lazy singleton."""
    global _instance  # noqa: PLW0603
    if _instance is None:
        with _instance_lock:
            if _instance is None:
                _instance = APEXDashboard()
    return _instance


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
def _cli_main() -> None:
    """Run dashboard from command line."""
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

    dash = get_dashboard()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "full"

    section_map = {
        "models": dash.model_status,
        "db": dash.database_health,
        "quality": dash.quality_summary,
        "learning": dash.learning_summary,
        "resources": dash.resource_usage,
    }

    if cmd == "full":
        print(dash.render())
    elif cmd in section_map:
        print(_box_top())
        print(section_map[cmd]())
        print(_box_bot())
    elif cmd == "json":
        # Machine-readable JSON output
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "llm_enabled": APEX_LLM_ENABLED,
        }
        ll = _get_learning_loop()
        qf = _get_quality_feedback()
        if ll:
            result["learning"] = ll.summary()
        if qf:
            result["quality"] = qf.get_dashboard()
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    else:
        print(f"Usage: python apex_dashboard.py [full|models|db|quality|learning|resources|json]")


if __name__ == "__main__":
    _cli_main()
