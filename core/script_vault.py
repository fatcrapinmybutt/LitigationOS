"""
ScriptVault — Persistent Script Management for LitigationOS
============================================================
Dedicated SQLite database that catalogs every script Copilot agents create.
Scripts are versioned, tagged, and searchable so agents NEVER recreate from scratch.

Usage by Copilot agents:
    from core.script_vault import ScriptVault
    vault = ScriptVault()

    # Find an existing script before writing a new one
    results = vault.find("evidence mining")
    if results:
        script = vault.load(results[0]['script_id'])
        # Modify and upgrade in place
        vault.upgrade(script['script_id'], new_code, "Added Watson family patterns")
    else:
        vault.register("mine_evidence.py", code, category="mining",
                       description="Mines harvest texts for actionable evidence",
                       tags=["evidence", "mining", "torts", "harvest"])

    # Run and log execution
    vault.run("mine_evidence", args=["--adversary", "McNeill"])

    # List all scripts
    vault.list_scripts(category="mining")
"""
import sqlite3
import hashlib
import os
import sys
import time
import json
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

# Vault lives next to litigation_context.db
VAULT_DB_PATH = Path(r"C:\Users\andre\LitigationOS\script_vault.db")
VAULT_SCRIPTS_DIR = Path(r"C:\Users\andre\LitigationOS\08_SCRIPTS\vault")
VAULT_ARCHIVE_DIR = VAULT_SCRIPTS_DIR / "_archive"

# Categories for organizing scripts
CATEGORIES = [
    "mining",       # Evidence mining, text extraction, pattern matching
    "ingestion",    # DB ingestion, loading data
    "analysis",     # Analysis engines, cross-referencing, scoring
    "dedup",        # Deduplication, consolidation
    "filing",       # Filing preparation, court form generation
    "query",        # DB queries, reports, dashboards
    "qa",           # Quality assurance, validation, pre-filing checks
    "utility",      # General utilities, helpers
    "pipeline",     # Pipeline phases, orchestration
    "maintenance",  # Cleanup, backup, health checks
]


class ScriptVault:
    """Persistent script catalog and version manager for Copilot agents."""

    def __init__(self, db_path=None, scripts_dir=None):
        self.db_path = Path(db_path) if db_path else VAULT_DB_PATH
        self.scripts_dir = Path(scripts_dir) if scripts_dir else VAULT_SCRIPTS_DIR
        self.archive_dir = self.scripts_dir / "_archive"
        self._ensure_dirs()
        self._ensure_db()

    def _ensure_dirs(self):
        self.scripts_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        for cat in CATEGORIES:
            (self.scripts_dir / cat).mkdir(exist_ok=True)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(str(self.db_path), timeout=60)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -8000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS scripts (
                    script_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    tags TEXT,
                    current_version INTEGER DEFAULT 1,
                    file_path TEXT NOT NULL,
                    code_hash TEXT,
                    lines_of_code INTEGER,
                    dependencies TEXT,
                    input_tables TEXT,
                    output_tables TEXT,
                    run_count INTEGER DEFAULT 0,
                    last_run_at TEXT,
                    last_run_status TEXT,
                    last_run_duration_s REAL,
                    avg_run_duration_s REAL,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now')),
                    created_by TEXT DEFAULT 'copilot',
                    status TEXT DEFAULT 'active'
                );

                CREATE TABLE IF NOT EXISTS script_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_id TEXT NOT NULL REFERENCES scripts(script_id),
                    version INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    code_hash TEXT NOT NULL,
                    lines_of_code INTEGER,
                    change_summary TEXT,
                    created_at TEXT DEFAULT (datetime('now')),
                    UNIQUE(script_id, version)
                );

                CREATE TABLE IF NOT EXISTS script_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_id TEXT NOT NULL REFERENCES scripts(script_id),
                    version INTEGER,
                    started_at TEXT DEFAULT (datetime('now')),
                    completed_at TEXT,
                    duration_s REAL,
                    exit_code INTEGER,
                    status TEXT,
                    args TEXT,
                    stdout_tail TEXT,
                    stderr_tail TEXT,
                    rows_affected INTEGER,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS script_dependencies (
                    script_id TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'uses',
                    PRIMARY KEY (script_id, depends_on)
                );

                CREATE INDEX IF NOT EXISTS idx_scripts_category ON scripts(category);
                CREATE INDEX IF NOT EXISTS idx_scripts_tags ON scripts(tags);
                CREATE INDEX IF NOT EXISTS idx_scripts_status ON scripts(status);
                CREATE INDEX IF NOT EXISTS idx_sv_script ON script_versions(script_id);
                CREATE INDEX IF NOT EXISTS idx_sr_script ON script_runs(script_id);

                CREATE VIRTUAL TABLE IF NOT EXISTS scripts_fts USING fts5(
                    script_id, filename, description, tags, category,
                    content=scripts, content_rowid=rowid
                );
            """)

    # ─── CORE API ────────────────────────────────────────────────────────

    def register(self, filename, code, category="utility", description="",
                 tags=None, input_tables=None, output_tables=None,
                 dependencies=None):
        """Register a new script or return existing if duplicate code."""
        script_id = Path(filename).stem  # e.g., "mine_evidence" from "mine_evidence.py"
        code_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()[:16]
        loc = len(code.strip().split('\n'))
        tags_str = ', '.join(tags) if tags else ''
        inputs_str = ', '.join(input_tables) if input_tables else ''
        outputs_str = ', '.join(output_tables) if output_tables else ''
        deps_str = ', '.join(dependencies) if dependencies else ''

        # Place in category subdirectory
        file_path = self.scripts_dir / category / filename
        file_path.write_text(code, encoding='utf-8')

        with self._conn() as conn:
            existing = conn.execute(
                "SELECT script_id, code_hash, current_version FROM scripts WHERE script_id = ?",
                (script_id,)
            ).fetchone()

            if existing:
                if existing['code_hash'] == code_hash:
                    return {"action": "unchanged", "script_id": script_id,
                            "version": existing['current_version']}
                # Auto-upgrade
                return self.upgrade(script_id, code, "Auto-upgrade on re-register")

            conn.execute("""
                INSERT INTO scripts (script_id, filename, category, description, tags,
                    file_path, code_hash, lines_of_code, dependencies,
                    input_tables, output_tables)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (script_id, filename, category, description, tags_str,
                  str(file_path), code_hash, loc, deps_str, inputs_str, outputs_str))

            conn.execute("""
                INSERT INTO script_versions (script_id, version, code, code_hash,
                    lines_of_code, change_summary)
                VALUES (?, 1, ?, ?, ?, 'Initial registration')
            """, (script_id, code, code_hash, loc))

            # Update FTS
            conn.execute("""
                INSERT INTO scripts_fts (script_id, filename, description, tags, category)
                VALUES (?, ?, ?, ?, ?)
            """, (script_id, filename, description, tags_str, category))

        return {"action": "registered", "script_id": script_id, "version": 1,
                "path": str(file_path)}

    def upgrade(self, script_id, new_code, change_summary="Upgraded"):
        """Create a new version of an existing script."""
        code_hash = hashlib.sha256(new_code.encode('utf-8')).hexdigest()[:16]
        loc = len(new_code.strip().split('\n'))

        with self._conn() as conn:
            script = conn.execute(
                "SELECT * FROM scripts WHERE script_id = ?", (script_id,)
            ).fetchone()
            if not script:
                raise ValueError(f"Script '{script_id}' not found in vault")

            new_version = script['current_version'] + 1

            # Archive old version file
            old_path = Path(script['file_path'])
            if old_path.exists():
                archive_name = f"{script_id}_v{script['current_version']}.py"
                shutil.copy2(str(old_path), str(self.archive_dir / archive_name))

            # Write new version
            old_path.write_text(new_code, encoding='utf-8')

            conn.execute("""
                UPDATE scripts SET current_version = ?, code_hash = ?,
                    lines_of_code = ?, updated_at = datetime('now')
                WHERE script_id = ?
            """, (new_version, code_hash, loc, script_id))

            conn.execute("""
                INSERT INTO script_versions (script_id, version, code, code_hash,
                    lines_of_code, change_summary)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (script_id, new_version, new_code, code_hash, loc, change_summary))

        return {"action": "upgraded", "script_id": script_id,
                "version": new_version, "change": change_summary}

    def find(self, query, category=None, limit=10):
        """Search scripts by description, tags, or name. Returns matches."""
        with self._conn() as conn:
            # Try FTS first
            try:
                fts_results = conn.execute("""
                    SELECT script_id, rank FROM scripts_fts
                    WHERE scripts_fts MATCH ? ORDER BY rank LIMIT ?
                """, (query, limit)).fetchall()
                if fts_results:
                    ids = [r['script_id'] for r in fts_results]
                    placeholders = ','.join('?' * len(ids))
                    sql = f"""SELECT * FROM scripts WHERE script_id IN ({placeholders})
                              AND status = 'active'"""
                    if category:
                        sql += f" AND category = '{category}'"
                    return [dict(r) for r in conn.execute(sql, ids).fetchall()]
            except Exception:
                pass

            # Fallback to LIKE
            sql = """SELECT * FROM scripts WHERE status = 'active' AND (
                        description LIKE ? OR tags LIKE ? OR filename LIKE ? OR script_id LIKE ?)"""
            params = [f'%{query}%'] * 4
            if category:
                sql += " AND category = ?"
                params.append(category)
            sql += f" LIMIT {limit}"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def load(self, script_id, version=None):
        """Load a script's code (latest or specific version)."""
        with self._conn() as conn:
            if version:
                row = conn.execute("""
                    SELECT * FROM script_versions
                    WHERE script_id = ? AND version = ?
                """, (script_id, version)).fetchone()
            else:
                row = conn.execute("""
                    SELECT * FROM script_versions
                    WHERE script_id = ? ORDER BY version DESC LIMIT 1
                """, (script_id,)).fetchone()
            if row:
                return dict(row)
            return None

    def run(self, script_id, args=None, timeout=600):
        """Execute a script and log the run."""
        with self._conn() as conn:
            script = conn.execute(
                "SELECT * FROM scripts WHERE script_id = ?", (script_id,)
            ).fetchone()
            if not script:
                raise ValueError(f"Script '{script_id}' not found")

            file_path = script['file_path']
            version = script['current_version']

        cmd = [sys.executable, file_path] + (args or [])
        env = os.environ.copy()
        env['PYTHONUTF8'] = '1'
        # Run from script's own directory to avoid shadow modules
        cwd = str(Path(file_path).parent)

        t0 = time.time()
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                cwd=cwd, env=env
            )
            duration = time.time() - t0
            status = "success" if result.returncode == 0 else "failed"

            with self._conn() as conn:
                conn.execute("""
                    INSERT INTO script_runs
                    (script_id, version, completed_at, duration_s, exit_code,
                     status, args, stdout_tail, stderr_tail)
                    VALUES (?, ?, datetime('now'), ?, ?, ?, ?, ?, ?)
                """, (script_id, version, duration, result.returncode, status,
                      json.dumps(args), result.stdout[-2000:] if result.stdout else '',
                      result.stderr[-1000:] if result.stderr else ''))

                # Update script stats
                conn.execute("""
                    UPDATE scripts SET run_count = run_count + 1,
                        last_run_at = datetime('now'), last_run_status = ?,
                        last_run_duration_s = ?,
                        avg_run_duration_s = COALESCE(
                            (avg_run_duration_s * run_count + ?) / (run_count + 1),
                            ?
                        )
                    WHERE script_id = ?
                """, (status, duration, duration, duration, script_id))

            return {"status": status, "exit_code": result.returncode,
                    "duration_s": round(duration, 1),
                    "stdout": result.stdout[-2000:], "stderr": result.stderr[-1000:]}

        except subprocess.TimeoutExpired:
            duration = time.time() - t0
            with self._conn() as conn:
                conn.execute("""
                    INSERT INTO script_runs
                    (script_id, version, completed_at, duration_s, status, args, notes)
                    VALUES (?, ?, datetime('now'), ?, 'timeout', ?, ?)
                """, (script_id, version, duration, json.dumps(args),
                      f"Timed out after {timeout}s"))
            return {"status": "timeout", "duration_s": round(duration, 1)}

    def list_scripts(self, category=None, status='active'):
        """List all registered scripts."""
        with self._conn() as conn:
            sql = "SELECT * FROM scripts WHERE status = ?"
            params = [status]
            if category:
                sql += " AND category = ?"
                params.append(category)
            sql += " ORDER BY category, script_id"
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def get_stats(self):
        """Get vault-wide statistics."""
        with self._conn() as conn:
            row = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM scripts WHERE status='active') as total_scripts,
                    (SELECT COUNT(*) FROM script_versions) as total_versions,
                    (SELECT COUNT(*) FROM script_runs) as total_runs,
                    (SELECT COUNT(*) FROM script_runs WHERE status='success') as successful_runs,
                    (SELECT SUM(lines_of_code) FROM scripts WHERE status='active') as total_loc,
                    (SELECT COUNT(DISTINCT category) FROM scripts) as categories_used
            """).fetchone()
            return dict(row)

    def history(self, script_id, limit=10):
        """Get version history for a script."""
        with self._conn() as conn:
            return [dict(r) for r in conn.execute("""
                SELECT version, change_summary, lines_of_code, created_at
                FROM script_versions WHERE script_id = ?
                ORDER BY version DESC LIMIT ?
            """, (script_id, limit)).fetchall()]

    def deprecate(self, script_id, reason=""):
        """Mark a script as deprecated (never delete)."""
        with self._conn() as conn:
            conn.execute("""
                UPDATE scripts SET status = 'deprecated',
                    description = description || ' [DEPRECATED: ' || ? || ']',
                    updated_at = datetime('now')
                WHERE script_id = ?
            """, (reason, script_id))
        return {"action": "deprecated", "script_id": script_id}


# ─── CLI INTERFACE ──────────────────────────────────────────────────────
def main():
    """CLI for ScriptVault management."""
    import argparse
    parser = argparse.ArgumentParser(description="ScriptVault — Script Management for LitigationOS")
    sub = parser.add_subparsers(dest='command')

    sub.add_parser('stats', help='Show vault statistics')
    sub.add_parser('list', help='List all scripts').add_argument('--category', '-c')

    find_p = sub.add_parser('find', help='Search scripts')
    find_p.add_argument('query')

    hist_p = sub.add_parser('history', help='Version history')
    hist_p.add_argument('script_id')

    run_p = sub.add_parser('run', help='Run a script')
    run_p.add_argument('script_id')
    run_p.add_argument('args', nargs='*')

    args = parser.parse_args()
    vault = ScriptVault()

    if args.command == 'stats':
        stats = vault.get_stats()
        print(f"ScriptVault Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")

    elif args.command == 'list':
        scripts = vault.list_scripts(category=getattr(args, 'category', None))
        print(f"{'ID':30s} {'CAT':12s} {'VER':>4s} {'RUNS':>5s} {'LOC':>5s} {'STATUS':>8s}")
        print("-" * 70)
        for s in scripts:
            print(f"{s['script_id']:30s} {s['category']:12s} v{s['current_version']:>3d} "
                  f"{s['run_count']:>5d} {s['lines_of_code']:>5d} {s['last_run_status'] or '-':>8s}")

    elif args.command == 'find':
        results = vault.find(args.query)
        for r in results:
            print(f"  {r['script_id']:30s} [{r['category']}] {r['description'][:60]}")

    elif args.command == 'history':
        versions = vault.history(args.script_id)
        for v in versions:
            print(f"  v{v['version']} ({v['created_at']}): {v['change_summary']} [{v['lines_of_code']} LOC]")

    elif args.command == 'run':
        result = vault.run(args.script_id, args=args.args)
        print(f"  Status: {result['status']} ({result['duration_s']}s)")
        if result.get('stdout'):
            print(result['stdout'][-500:])

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
