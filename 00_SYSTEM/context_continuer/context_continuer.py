"""
MBP LitigationOS 2026 — Context Continuer Engine
=================================================
Provides near-infinite context persistence across AI session compactions.

Architecture:
  - Captures full session state into structured "handoff" snapshots
  - Stores snapshots as markdown + JSON on disk and in SQLite
  - Auto-loads latest snapshot at session start
  - Designed for Copilot CLI / LLM session boundaries

Usage:
  python context_continuer.py snapshot              # Take a snapshot now
  python context_continuer.py restore               # Print latest handoff
  python context_continuer.py status                # Show snapshot history
  python context_continuer.py --json                # Output as JSON
"""

import os
import sys
import json
import sqlite3
import hashlib
import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
ROOT = Path(r"C:\Users\andre\LitigationOS")
SYSTEM_DIR = ROOT / "00_SYSTEM"
CC_DIR = SYSTEM_DIR / "context_continuer"
SNAPSHOTS_DIR = CC_DIR / "snapshots"
HANDOFF_FILE = CC_DIR / "context_continuer.md"
DB_PATH = Path(r"C:\Users\andre\litigation_context.db")
CONFIG_PATH = ROOT / "litigationos.config.json"

# Ensure directories exist
CC_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


class ContextContinuer:
    """
    The Context Continuer captures, stores, and restores structured
    session state for AI assistants working on the LitigationOS platform.
    """

    def __init__(self):
        self.db = None
        self._ensure_db_table()

    # ── Database ───────────────────────────────────────────────────────

    def _get_db(self):
        if self.db is None:
            self.db = sqlite3.connect(str(DB_PATH))
            self.db.row_factory = sqlite3.Row
        return self.db

    def _ensure_db_table(self):
        """Create context_snapshots table if it doesn't exist."""
        try:
            db = self._get_db()
            db.execute("""
                CREATE TABLE IF NOT EXISTS context_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    snapshot_hash TEXT UNIQUE,
                    summary_text TEXT,
                    snapshot_json TEXT,
                    platform_status TEXT,
                    active_todos TEXT,
                    decisions_log TEXT,
                    files_changed TEXT,
                    next_actions TEXT,
                    warnings TEXT
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS idx_ctx_snap_ts
                ON context_snapshots(timestamp DESC)
            """)
            db.commit()
        except Exception as e:
            print(f"[context_continuer] DB init warning: {e}", file=sys.stderr)

    # ── State Collection ───────────────────────────────────────────────

    def _collect_identity(self):
        """Collect case identity and separation day count."""
        config = {}
        if CONFIG_PATH.exists():
            try:
                config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except Exception:
                pass

        # Calculate separation days from known date (2025-04-01 approximate)
        sep_start = datetime.date(2025, 4, 1)
        today = datetime.date.today()
        sep_days = (today - sep_start).days

        return {
            "case": "Pigors v. Watson",
            "plaintiff": "Andrew Pigors (pro se)",
            "defendant": "Tiffany Watson (fka Pigors)",
            "judge": "Hon. Jenny L. McNeill",
            "court": "14th Circuit Court, Muskegon County",
            "separation_days": sep_days,
            "lanes": {
                "A": "Watson Custody — 2024-001507-DC",
                "B": "Shady Oaks Housing",
                "C": "Convergence — Multi-lane",
                "D": "PPO — 2023-5907-PP",
                "E": "Judicial Misconduct — JTC/MSC",
                "F": "Appellate — COA 366810"
            },
            "config_loaded": bool(config)
        }

    def _collect_platform_status(self):
        """Collect build/runtime status for each platform."""
        status = {}

        # Desktop app
        desktop_dist = ROOT / "08_APPS" / "desktop" / "frontend" / "dist" / "index.html"
        status["desktop"] = {
            "frontend_built": desktop_dist.exists(),
            "location": "08_APPS/desktop/",
            "tech": "Electron + React 18/Vite + IPC + SQLite"
        }

        # Web app
        web_next = ROOT / "08_APPS" / "web" / ".next"
        status["web"] = {
            "built": web_next.exists(),
            "location": "08_APPS/web/",
            "tech": "Next.js 14 + TypeScript + Tailwind + Three.js"
        }

        # Mobile app
        mob_pkg = ROOT / "08_APPS" / "mobile" / "package.json"
        status["mobile"] = {
            "exists": mob_pkg.exists(),
            "location": "08_APPS/mobile/",
            "tech": "Expo + React Native 0.73 + TypeScript"
        }

        # Core MLLM
        model_dir = SYSTEM_DIR / "local_model" / "model_data"
        status["mllm"] = {
            "trained": model_dir.exists() and any(model_dir.glob("*.pkl")),
            "location": "00_SYSTEM/local_model/",
            "tech": "TF-IDF + Naive Bayes (177K docs, 50K features)"
        }

        # Database
        status["database"] = {
            "exists": DB_PATH.exists(),
            "size_mb": round(DB_PATH.stat().st_size / (1024 * 1024), 1) if DB_PATH.exists() else 0,
            "location": str(DB_PATH)
        }

        return status

    def _collect_db_stats(self):
        """Collect key database statistics."""
        stats = {}
        try:
            db = self._get_db()
            # Table counts for key tables
            key_tables = [
                "auth_rules", "evidence_quotes", "master_citations",
                "impeachment_items", "contradiction_map", "deadlines",
                "docket_events", "vehicles", "judicial_violations",
                "adversary_models", "mllm_improvement_cycles"
            ]
            for table in key_tables:
                try:
                    row = db.execute(f"SELECT COUNT(*) as n FROM [{table}]").fetchone()
                    stats[table] = row["n"] if row else 0
                except Exception:
                    stats[table] = -1  # table doesn't exist
        except Exception as e:
            stats["_error"] = str(e)
        return stats

    def _collect_recent_files(self, hours=24):
        """Find recently modified files in LitigationOS."""
        cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
        recent = []
        for pattern in ["**/*.py", "**/*.js", "**/*.jsx", "**/*.ts", "**/*.tsx", "**/*.json", "**/*.md"]:
            for f in ROOT.glob(pattern):
                try:
                    if "node_modules" in str(f) or ".next" in str(f) or "dist" in str(f):
                        continue
                    mtime = datetime.datetime.fromtimestamp(f.stat().st_mtime)
                    if mtime > cutoff:
                        recent.append({
                            "path": str(f.relative_to(ROOT)),
                            "modified": mtime.isoformat(),
                            "size": f.stat().st_size
                        })
                except Exception:
                    continue
        recent.sort(key=lambda x: x["modified"], reverse=True)
        return recent[:50]  # cap at 50

    # ── Snapshot ───────────────────────────────────────────────────────

    def snapshot(self, session_id=None, todos=None, decisions=None,
                 knowledge=None, next_actions=None, warnings=None):
        """
        Take a full context snapshot.

        Parameters:
            session_id: Copilot session ID (optional)
            todos: List of {id, title, status, description} dicts
            decisions: List of decision strings
            knowledge: List of knowledge strings gained this session
            next_actions: List of prioritized next actions
            warnings: List of critical warnings for next session
        """
        timestamp = datetime.datetime.now().isoformat()

        identity = self._collect_identity()
        platform = self._collect_platform_status()
        db_stats = self._collect_db_stats()
        recent_files = self._collect_recent_files()

        snapshot_data = {
            "timestamp": timestamp,
            "session_id": session_id,
            "identity": identity,
            "platform_status": platform,
            "db_stats": db_stats,
            "active_todos": todos or [],
            "decisions_log": decisions or [],
            "files_changed": recent_files,
            "knowledge_gained": knowledge or [],
            "next_actions": next_actions or [],
            "critical_warnings": warnings or []
        }

        # Generate hash for dedup
        content_str = json.dumps(snapshot_data, sort_keys=True, default=str)
        snap_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]

        # Save to DB
        try:
            db = self._get_db()
            db.execute("""
                INSERT OR IGNORE INTO context_snapshots
                (timestamp, session_id, snapshot_hash, summary_text,
                 snapshot_json, platform_status, active_todos,
                 decisions_log, files_changed, next_actions, warnings)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                session_id,
                snap_hash,
                self._generate_summary(snapshot_data),
                json.dumps(snapshot_data, default=str),
                json.dumps(platform, default=str),
                json.dumps(todos or [], default=str),
                json.dumps(decisions or [], default=str),
                json.dumps(recent_files, default=str),
                json.dumps(next_actions or [], default=str),
                json.dumps(warnings or [], default=str)
            ))
            db.commit()
        except Exception as e:
            print(f"[context_continuer] DB save warning: {e}", file=sys.stderr)

        # Save timestamped JSON snapshot
        snap_file = SNAPSHOTS_DIR / f"snapshot_{timestamp.replace(':', '-').replace('.', '_')}.json"
        try:
            snap_file.write_text(json.dumps(snapshot_data, indent=2, default=str), encoding="utf-8")
        except Exception as e:
            print(f"[context_continuer] File save warning: {e}", file=sys.stderr)

        # Generate and save handoff markdown
        handoff_md = self._generate_handoff_markdown(snapshot_data)
        try:
            HANDOFF_FILE.write_text(handoff_md, encoding="utf-8")
        except Exception as e:
            print(f"[context_continuer] Handoff save warning: {e}", file=sys.stderr)

        return {
            "status": "success",
            "hash": snap_hash,
            "timestamp": timestamp,
            "snapshot_file": str(snap_file),
            "handoff_file": str(HANDOFF_FILE)
        }

    # ── Restore ────────────────────────────────────────────────────────

    def restore(self, as_json=False):
        """
        Load the latest handoff document.
        Returns markdown string or JSON dict.
        """
        # Try DB first (most recent)
        try:
            db = self._get_db()
            row = db.execute("""
                SELECT snapshot_json FROM context_snapshots
                ORDER BY timestamp DESC LIMIT 1
            """).fetchone()
            if row:
                data = json.loads(row["snapshot_json"])
                if as_json:
                    return data
                return self._generate_handoff_markdown(data)
        except Exception:
            pass

        # Fallback: read handoff file
        if HANDOFF_FILE.exists():
            content = HANDOFF_FILE.read_text(encoding="utf-8")
            if as_json:
                return {"raw_markdown": content}
            return content

        return "No context snapshots found. This is a fresh session."

    def restore_primer(self):
        """
        Generate a compact session primer for injection into new sessions.
        Smaller than full handoff — just the critical state needed to resume.
        """
        try:
            db = self._get_db()
            row = db.execute("""
                SELECT snapshot_json FROM context_snapshots
                ORDER BY timestamp DESC LIMIT 1
            """).fetchone()
            if not row:
                return "No prior session context available."
            data = json.loads(row["snapshot_json"])
        except Exception:
            if HANDOFF_FILE.exists():
                return HANDOFF_FILE.read_text(encoding="utf-8")[:3000]
            return "No prior session context available."

        identity = data.get("identity", {})
        platform = data.get("platform_status", {})
        db_stats = data.get("db_stats", {})
        todos = data.get("active_todos", [])
        decisions = data.get("decisions_log", [])
        warnings = data.get("critical_warnings", [])
        next_actions = data.get("next_actions", [])

        lines = [
            "## SESSION PRIMER (auto-restored)",
            f"**Snapshot:** {data.get('timestamp', 'unknown')}",
            f"**Case:** {identity.get('case')} | **Separation:** {identity.get('separation_days', '?')} days",
            f"**Lanes:** A=Custody, B=Housing, C=Convergence, D=PPO, E=Judicial, F=Appellate (COA 366810)",
            "",
            "**Platform:**",
        ]
        for k, v in platform.items():
            built = "BUILT" if v.get("frontend_built") or v.get("built") else "NOT BUILT"
            lines.append(f"  - {k}: {v.get('tech', '?')} [{built}]")

        # DB stats (compact)
        empty_tables = [k for k, v in db_stats.items() if isinstance(v, (int, float)) and v == 0]
        lines.append(f"\n**DB:** {sum(v for v in db_stats.values() if isinstance(v, (int, float)))} total rows")
        if empty_tables:
            lines.append(f"**Empty tables:** {', '.join(empty_tables[:10])}")

        if todos:
            lines.append(f"\n**Active todos ({len(todos)}):**")
            for t in todos[:15]:
                lines.append(f"  - [{t.get('status','?')}] {t.get('title','?')}")

        if warnings:
            lines.append("\n**Warnings:**")
            for w in warnings[:5]:
                lines.append(f"  - ⚠️ {w}")

        if next_actions:
            lines.append("\n**Next actions:**")
            for a in next_actions[:5]:
                lines.append(f"  - → {a}")

        if decisions:
            lines.append("\n**Key decisions:**")
            for d in decisions[:5]:
                lines.append(f"  - {d}")

        return "\n".join(lines)

    def status(self):
        """Show snapshot history."""
        try:
            db = self._get_db()
            rows = db.execute("""
                SELECT id, timestamp, session_id, snapshot_hash, summary_text
                FROM context_snapshots ORDER BY timestamp DESC LIMIT 20
            """).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            return [{"error": str(e)}]

    # ── Markdown Generation ────────────────────────────────────────────

    def _generate_summary(self, data):
        """One-line summary for DB storage."""
        n_todos = len(data.get("active_todos", []))
        n_files = len(data.get("files_changed", []))
        sep = data.get("identity", {}).get("separation_days", "?")
        return f"Snapshot: {n_todos} todos, {n_files} files changed, {sep}+ days separation"

    def _generate_handoff_markdown(self, data):
        """Generate the structured handoff document."""
        lines = []
        ts = data.get("timestamp", "unknown")
        identity = data.get("identity", {})
        platform = data.get("platform_status", {})
        db_stats = data.get("db_stats", {})

        lines.append("# CONTEXT CONTINUER — SESSION HANDOFF")
        lines.append(f"**Generated:** {ts}")
        lines.append(f"**Session:** {data.get('session_id', 'unknown')}")
        lines.append("")

        # 1. IDENTITY
        lines.append("## 1. CASE IDENTITY")
        lines.append(f"- **Case:** {identity.get('case', 'Pigors v. Watson')}")
        lines.append(f"- **Plaintiff:** {identity.get('plaintiff', 'Andrew Pigors')}")
        lines.append(f"- **Defendant:** {identity.get('defendant', 'Tiffany Watson')}")
        lines.append(f"- **Judge:** {identity.get('judge', 'Hon. Jenny L. McNeill')}")
        lines.append(f"- **Court:** {identity.get('court', '14th Circuit, Muskegon')}")
        lines.append(f"- **⚠️ SEPARATION DAYS: {identity.get('separation_days', '329+')}**")
        lines.append("")
        lanes = identity.get("lanes", {})
        if lanes:
            lines.append("### Case Lanes")
            for lane_id, desc in lanes.items():
                lines.append(f"- **Lane {lane_id}:** {desc}")
            lines.append("")

        # 2. PLATFORM STATE
        lines.append("## 2. PLATFORM STATE")
        for name, info in platform.items():
            status_icon = "✅" if info.get("frontend_built") or info.get("built") or info.get("trained") or info.get("exists") else "🔴"
            lines.append(f"- **{name.title()}:** {status_icon} {info.get('tech', '')} — `{info.get('location', '')}`")
        lines.append("")

        # 3. DATABASE STATS
        lines.append("## 3. DATABASE STATS")
        for table, count in db_stats.items():
            if table.startswith("_"):
                continue
            status = "✅" if count > 0 else "⚠️ EMPTY"
            lines.append(f"- `{table}`: {count:,} rows {status if count == 0 else ''}")
        lines.append("")

        # 4. ACTIVE TODOS
        todos = data.get("active_todos", [])
        if todos:
            lines.append("## 4. ACTIVE WORK")
            for t in todos:
                status_icon = {"done": "✅", "in_progress": "🔧", "pending": "⏳", "blocked": "🚫"}.get(
                    t.get("status", "pending"), "⏳")
                lines.append(f"- {status_icon} **{t.get('id', '')}** — {t.get('title', '')} [{t.get('status', 'pending')}]")
                if t.get("description"):
                    lines.append(f"  - {t['description'][:200]}")
            lines.append("")

        # 5. DECISIONS LOG
        decisions = data.get("decisions_log", [])
        if decisions:
            lines.append("## 5. DECISIONS MADE")
            for d in decisions:
                lines.append(f"- {d}")
            lines.append("")

        # 6. FILES CHANGED
        files = data.get("files_changed", [])
        if files:
            lines.append("## 6. RECENTLY MODIFIED FILES")
            for f in files[:30]:
                lines.append(f"- `{f.get('path', '')}` — {f.get('modified', '')}")
            lines.append("")

        # 7. KNOWLEDGE GAINED
        knowledge = data.get("knowledge_gained", [])
        if knowledge:
            lines.append("## 7. KNOWLEDGE GAINED")
            for k in knowledge:
                lines.append(f"- {k}")
            lines.append("")

        # 8. NEXT ACTIONS
        actions = data.get("next_actions", [])
        if actions:
            lines.append("## 8. NEXT ACTIONS (Priority Order)")
            for i, a in enumerate(actions, 1):
                lines.append(f"{i}. {a}")
            lines.append("")

        # 9. WARNINGS
        warnings = data.get("critical_warnings", [])
        if warnings:
            lines.append("## 9. ⚠️ CRITICAL WARNINGS")
            for w in warnings:
                lines.append(f"- **{w}**")
            lines.append("")

        lines.append("---")
        lines.append("*This handoff was auto-generated by the Context Continuer engine.*")
        lines.append(f"*Load with: `python context_continuer.py restore`*")

        return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────

def main():
    cc = ContextContinuer()

    if len(sys.argv) < 2:
        print("Usage: python context_continuer.py [snapshot|restore|status|auto|primer|preconsolidate] [--json]")
        sys.exit(1)

    command = sys.argv[1].lower()
    as_json = "--json" in sys.argv

    if command == "snapshot":
        result = cc.snapshot()
        if as_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"✅ Snapshot saved: {result['hash']}")
            print(f"   File: {result['snapshot_file']}")
            print(f"   Handoff: {result['handoff_file']}")

    elif command == "restore":
        result = cc.restore(as_json=as_json)
        if as_json:
            print(json.dumps(result, indent=2, default=str, ensure_ascii=False))
        else:
            # Handle Windows console encoding
            try:
                print(result)
            except UnicodeEncodeError:
                sys.stdout.buffer.write(result.encode("utf-8", errors="replace"))
                sys.stdout.buffer.write(b"\n")

    elif command == "status":
        history = cc.status()
        if as_json:
            print(json.dumps(history, indent=2, default=str))
        else:
            print(f"Snapshots: {len(history)}")
            for h in history:
                print(f"  [{h.get('id')}] {h.get('timestamp')} — {h.get('summary_text', '')}")

    elif command == "auto":
        # Auto-mode: only snapshot if enough has changed since last snapshot
        history = cc.status()
        should_snapshot = True
        if history:
            last = history[-1]
            last_time = datetime.datetime.fromisoformat(last.get('timestamp', '2000-01-01'))
            elapsed = (datetime.datetime.now() - last_time).total_seconds()
            # Only snapshot if at least 30 minutes have passed
            if elapsed < 1800:
                should_snapshot = False
                if not as_json:
                    print(f"⏳ Last snapshot was {int(elapsed)}s ago — skipping (min 1800s)")
        if should_snapshot:
            result = cc.snapshot()
            if as_json:
                print(json.dumps(result, indent=2))
            else:
                print(f"✅ Auto-snapshot saved: {result['hash']}")

    elif command == "primer":
        # Compact session primer for injection into new sessions
        result = cc.restore_primer()
        try:
            print(result)
        except UnicodeEncodeError:
            sys.stdout.buffer.write(result.encode("utf-8", errors="replace"))
            sys.stdout.buffer.write(b"\n")

    elif command == "preconsolidate":
        # PRE-CONSOLIDATION snapshot: called just before context window compaction.
        # Reads a JSON payload from stdin with session knowledge to preserve.
        # Usage: echo '{"todos":[...], "decisions":[...], ...}' | python context_continuer.py preconsolidate
        payload = {}
        if not sys.stdin.isatty():
            try:
                raw = sys.stdin.read()
                if raw.strip():
                    payload = json.loads(raw)
            except Exception as e:
                print(f"[warn] Could not parse stdin payload: {e}", file=sys.stderr)

        result = cc.snapshot(
            session_id=payload.get("session_id"),
            todos=payload.get("todos"),
            decisions=payload.get("decisions"),
            knowledge=payload.get("knowledge"),
            next_actions=payload.get("next_actions"),
            warnings=payload.get("warnings"),
        )
        if as_json:
            print(json.dumps(result, indent=2))
        else:
            print(f"PRE-CONSOLIDATION snapshot saved: {result['hash']}")
            print(f"   Handoff: {result['handoff_file']}")
            print(f"   Restore with: python context_continuer.py restore")
            print(f"   Primer with:  python context_continuer.py primer")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
