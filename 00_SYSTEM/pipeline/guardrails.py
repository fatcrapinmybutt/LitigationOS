#!/usr/bin/env python3
"""
guardrails.py — LitigationOS Pipeline Safety Guardrails
========================================================

Prevents the 7 recurring error categories identified across 14+ days of sessions:

  1. WRONG_DB_PATH      — Connecting to 28KB stub instead of 10GB real DB
  2. SCHEMA_MISMATCH    — INSERT/UPDATE using column names that don't exist
  3. INTEGRITY_HANG     — get_robust_connection() running PRAGMA integrity_check on 10GB DB
  4. DESTRUCTIVE_OP     — DROP TABLE / DELETE without backup verification
  5. COLUMN_HALLUCINATE — Referencing columns from memory instead of live schema
  6. MISSING_NOTNULL    — INSERT missing a NOT NULL column
  7. STALE_REFERENCE    — Using outdated file paths, API signatures, or module names

Usage:
    # Pre-flight check before any pipeline run
    python guardrails.py preflight

    # Validate a specific module's SQL against live schema
    python guardrails.py validate phase0_5_drive_ingest.py

    # Audit all pipeline modules
    python guardrails.py audit

    # Safe DB connection (use instead of sqlite3.connect or get_robust_connection)
    from guardrails import safe_connect, safe_insert, validate_columns

    conn = safe_connect()  # Validates path, sets WAL, skips integrity_check
    safe_insert(conn, 'drive_files', {'file_path': '/x', 'sha256': 'abc'})
"""
import sys
import os
import re
import sqlite3
import hashlib
import json
import time
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

# Ensure UTF-8 output
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

_LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")
_REAL_DB = _LITIGOS_ROOT / "litigation_context.db"
_STUB_DB = Path(r"C:\Users\andre\litigation_context.db")  # 28KB stub — NEVER use
_PIPELINE_DIR = _LITIGOS_ROOT / "00_SYSTEM" / "pipeline"
_SCHEMA_CONTRACT = _PIPELINE_DIR / "schema_contract.yaml"
_GUARDRAIL_LOG = _PIPELINE_DIR / "guardrail_audit.jsonl"
_MIN_DB_SIZE_MB = 100  # Real DB is 10GB+; anything under 100MB is suspect

# Tables managed by pipeline modules
PIPELINE_TABLES = [
    'drive_files', 'file_atoms', 'provenance_refs', 'ingest_logs',
    'gap_tickets', 'evidence_quotes', 'documents', 'pages',
    'claims', 'authority_chains', 'filing_readiness', 'deadlines',
    'vehicles', 'judicial_violations', 'impeachment_items',
    'contradiction_map', 'extracted_harms', 'master_citations',
    'docket_events', 'forensic_findings', 'legal_action_scores',
    'adversary_models', 'scan_inventory',
]

# Known dangerous functions/patterns
DANGEROUS_PATTERNS = [
    (r'(?<!def )get_robust_connection\s*\((?!db_path)', 'INTEGRITY_HANG',
     'get_robust_connection() runs PRAGMA integrity_check on 10GB DB — use safe_connect() instead'),
    (r'DROP\s+TABLE\s+(?!IF\s+EXISTS)', 'DESTRUCTIVE_OP',
     'DROP TABLE without IF EXISTS — use safe_drop_table() instead'),
    (r'DELETE\s+FROM\s+\w+\s*(?:;|$)', 'DESTRUCTIVE_OP',
     'DELETE FROM without WHERE clause — will delete ALL rows'),
    (r'TRUNCATE\s+TABLE', 'DESTRUCTIVE_OP',
     'TRUNCATE TABLE — use safe_truncate() with backup instead'),
    (r'(?:connect|open)\s*\(\s*["\']litigation_context\.db["\']\s*\)', 'WRONG_DB_PATH',
     'Bare DB filename in connect/open — will resolve to CWD, not LitigationOS root'),
    (r'C:\\Users\\andre\\litigation_context', 'WRONG_DB_PATH',
     'Points to 28KB stub at C:\\Users\\andre\\ — use C:\\Users\\andre\\LitigationOS\\'),
    (r'C:/Users/andre/litigation_context\.db', 'WRONG_DB_PATH',
     'Points to 28KB stub — use C:/Users/andre/LitigationOS/litigation_context.db'),
]

# Compiled regex for SQL extraction from Python files
_SQL_PATTERN = re.compile(
    r'(?:"""(.*?)"""|\'\'\'(.*?)\'\'\')',
    re.DOTALL
)
_INSERT_PATTERN = re.compile(
    r'INSERT\s+(?:OR\s+\w+\s+)?INTO\s+(\w+)\s*\(([\w\s,]+)\)',
    re.IGNORECASE
)
_UPDATE_PATTERN = re.compile(
    r'UPDATE\s+(\w+)\s+SET\s+([\w\s,=?]+)',
    re.IGNORECASE
)
_SELECT_PATTERN = re.compile(
    r'SELECT\s+([\w\s,.*()]+?)\s+FROM\s+(\w+)',
    re.IGNORECASE
)
_DROP_PATTERN = re.compile(
    r'DROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?(\w+)',
    re.IGNORECASE
)
_DELETE_PATTERN = re.compile(
    r'DELETE\s+FROM\s+(\w+)',
    re.IGNORECASE
)


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA CACHE
# ═══════════════════════════════════════════════════════════════════════════════

class SchemaCache:
    """Caches live DB schema to avoid repeated PRAGMA calls.
    Refreshes automatically if older than 300 seconds (5 min)."""

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or _REAL_DB
        self._cache: dict[str, dict] = {}
        self._loaded_at: float = 0
        self._ttl = 300.0  # seconds (upgraded from 60s → 300s per Δ∞ tuning)

    def _ensure_loaded(self):
        if time.time() - self._loaded_at > self._ttl:
            self._load()

    def _load(self):
        conn = sqlite3.connect(str(self._db_path), timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")

        # Get all tables
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        self._cache = {}
        for (tbl,) in tables:
            cols = conn.execute(f"PRAGMA table_info({tbl})").fetchall()
            self._cache[tbl] = {
                c[1]: {
                    'type': c[2],
                    'notnull': bool(c[3]),
                    'default': c[4],
                    'pk': bool(c[5]),
                    'cid': c[0],
                }
                for c in cols
            }
        conn.close()
        self._loaded_at = time.time()

    def get_columns(self, table: str) -> dict:
        """Returns {col_name: {type, notnull, default, pk}} for a table."""
        self._ensure_loaded()
        return self._cache.get(table, {})

    def table_exists(self, table: str) -> bool:
        self._ensure_loaded()
        return table in self._cache

    def column_exists(self, table: str, column: str) -> bool:
        cols = self.get_columns(table)
        return column in cols

    def get_notnull_columns(self, table: str) -> list[str]:
        """Returns list of NOT NULL columns without defaults."""
        cols = self.get_columns(table)
        return [
            name for name, info in cols.items()
            if info['notnull'] and info['default'] is None and not info['pk']
        ]

    def validate_columns(self, table: str, columns: list[str]) -> list[str]:
        """Returns list of columns that DON'T exist in the table."""
        real_cols = self.get_columns(table)
        return [c for c in columns if c not in real_cols]

    def all_tables(self) -> list[str]:
        self._ensure_loaded()
        return list(self._cache.keys())


# Global cache instance
_schema_cache = None

def get_schema_cache(db_path: Optional[Path] = None) -> SchemaCache:
    global _schema_cache
    if _schema_cache is None or db_path:
        _schema_cache = SchemaCache(db_path)
    return _schema_cache


# ═══════════════════════════════════════════════════════════════════════════════
# SAFE DB CONNECTION
# ═══════════════════════════════════════════════════════════════════════════════

def safe_connect(db_path: Optional[Path] = None, readonly: bool = False) -> sqlite3.Connection:
    """Safe DB connection that:
    1. Validates the path points to real DB (not 28KB stub)
    2. Sets WAL mode + busy_timeout
    3. NEVER runs PRAGMA integrity_check
    4. Returns Row factory enabled connection
    """
    path = Path(db_path) if db_path else _REAL_DB

    # Guard 1: Reject known stub path
    if path.resolve() == _STUB_DB.resolve():
        raise ValueError(
            f"WRONG_DB_PATH: {path} is the 28KB stub! "
            f"Use {_REAL_DB} instead."
        )

    # Guard 2: Check file exists and size
    if not path.exists():
        raise FileNotFoundError(f"Database not found: {path}")

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb < _MIN_DB_SIZE_MB:
        raise ValueError(
            f"WRONG_DB_PATH: {path} is only {size_mb:.1f}MB. "
            f"Real DB should be {_MIN_DB_SIZE_MB}MB+. "
            f"Expected path: {_REAL_DB}"
        )

    # Guard 3: Connect via multiplexer for mmap + optimal PRAGMAs
    try:
        from connection_multiplexer import get_connection
        conn = get_connection(readonly=readonly, db_path=path)
    except ImportError:
        # Fallback if multiplexer not available
        uri = f"file:{path}?mode=ro" if readonly else str(path)
        conn = sqlite3.connect(uri if readonly else str(path), timeout=120,
                               uri=readonly)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=120000")
        conn.execute("PRAGMA mmap_size=12884901888")
        conn.execute("PRAGMA cache_size=-131072")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.row_factory = sqlite3.Row

    _log_event('SAFE_CONNECT', f"Connected to {path} ({size_mb:.0f}MB, mmap=12GB)")
    return conn


# ═══════════════════════════════════════════════════════════════════════════════
# SAFE INSERT / UPDATE
# ═══════════════════════════════════════════════════════════════════════════════

def safe_insert(conn: sqlite3.Connection, table: str, data: dict,
                or_ignore: bool = False) -> int:
    """INSERT with pre-validation of all column names.

    Args:
        conn: Database connection
        table: Table name
        data: {column_name: value} dict
        or_ignore: If True, uses INSERT OR IGNORE

    Returns:
        lastrowid

    Raises:
        SchemaError: If any column doesn't exist or NOT NULL columns are missing
    """
    cache = get_schema_cache()

    # Validate table exists
    if not cache.table_exists(table):
        raise SchemaError(f"Table '{table}' does not exist in database")

    # Validate all columns exist
    bad_cols = cache.validate_columns(table, list(data.keys()))
    if bad_cols:
        real_cols = list(cache.get_columns(table).keys())
        raise SchemaError(
            f"COLUMN_HALLUCINATE: Table '{table}' has no columns: {bad_cols}\n"
            f"  Actual columns: {real_cols}"
        )

    # Validate NOT NULL columns are present
    required = cache.get_notnull_columns(table)
    missing = [c for c in required if c not in data]
    if missing and not or_ignore:
        raise SchemaError(
            f"MISSING_NOTNULL: Table '{table}' requires columns {missing} "
            f"but they were not provided"
        )

    # Build and execute
    cols = list(data.keys())
    placeholders = ', '.join(['?'] * len(cols))
    col_names = ', '.join(cols)
    ignore = "OR IGNORE " if or_ignore else ""

    cursor = conn.execute(
        f"INSERT {ignore}INTO {table} ({col_names}) VALUES ({placeholders})",
        [data[c] for c in cols]
    )
    return cursor.lastrowid


def safe_update(conn: sqlite3.Connection, table: str, data: dict,
                where: str, where_params: tuple) -> int:
    """UPDATE with pre-validation of column names.

    Returns: number of rows affected
    """
    cache = get_schema_cache()

    if not cache.table_exists(table):
        raise SchemaError(f"Table '{table}' does not exist")

    bad_cols = cache.validate_columns(table, list(data.keys()))
    if bad_cols:
        real_cols = list(cache.get_columns(table).keys())
        raise SchemaError(
            f"COLUMN_HALLUCINATE: '{table}' has no columns: {bad_cols}\n"
            f"  Actual columns: {real_cols}"
        )

    set_clause = ', '.join(f"{c} = ?" for c in data.keys())
    params = list(data.values()) + list(where_params)

    cursor = conn.execute(
        f"UPDATE {table} SET {set_clause} WHERE {where}",
        params
    )
    return cursor.rowcount


def validate_columns(table: str, columns: list[str],
                     db_path: Optional[Path] = None) -> list[str]:
    """Quick check: returns list of invalid column names.
    Empty list = all valid."""
    cache = get_schema_cache(db_path)
    return cache.validate_columns(table, columns)


# ═══════════════════════════════════════════════════════════════════════════════
# SAFE DESTRUCTIVE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

def safe_drop_table(conn: sqlite3.Connection, table: str,
                    require_empty: bool = True,
                    backup_dir: Optional[Path] = None) -> bool:
    """Safe DROP TABLE that:
    1. Checks if table is empty (configurable)
    2. Exports data to JSON backup before dropping
    3. Logs the operation
    """
    cache = get_schema_cache()

    if not cache.table_exists(table):
        _log_event('SAFE_DROP', f"Table '{table}' does not exist — skip")
        return False

    # Check row count
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    if require_empty and count > 0:
        raise DestructiveOpError(
            f"DESTRUCTIVE_OP: Cannot drop '{table}' — has {count} rows. "
            f"Set require_empty=False to override (will backup first)."
        )

    # Backup if has data
    if count > 0:
        bdir = backup_dir or (_PIPELINE_DIR / "backups" / "pre_drop")
        bdir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = bdir / f"{table}_{ts}.json"

        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        cols = [d[0] for d in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        data = [dict(zip([c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()],
                         row)) for row in rows]

        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump({'table': table, 'count': count, 'rows': data,
                       'dropped_at': ts}, f, indent=2, default=str)

        _log_event('BACKUP_BEFORE_DROP',
                   f"Backed up {count} rows from '{table}' to {backup_file}")

    conn.execute(f"DROP TABLE IF EXISTS {table}")
    _log_event('SAFE_DROP', f"Dropped table '{table}' (had {count} rows)")
    return True


def safe_delete(conn: sqlite3.Connection, table: str, where: str,
                where_params: tuple, max_rows: int = 10000) -> int:
    """Safe DELETE that:
    1. Counts rows first and warns if bulk delete
    2. Requires a WHERE clause (no naked DELETE FROM)
    3. Caps maximum rows deleted per call
    """
    if not where or not where.strip():
        raise DestructiveOpError(
            "DESTRUCTIVE_OP: DELETE without WHERE clause. "
            "Use safe_truncate() for full table wipe."
        )

    count = conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {where}", where_params
    ).fetchone()[0]

    if count > max_rows:
        raise DestructiveOpError(
            f"DESTRUCTIVE_OP: DELETE would affect {count} rows "
            f"(max_rows={max_rows}). Increase max_rows or batch the operation."
        )

    cursor = conn.execute(f"DELETE FROM {table} WHERE {where}", where_params)
    _log_event('SAFE_DELETE', f"Deleted {cursor.rowcount} rows from '{table}'")
    return cursor.rowcount


# ═══════════════════════════════════════════════════════════════════════════════
# STATIC SQL VALIDATOR (Pre-flight)
# ═══════════════════════════════════════════════════════════════════════════════

class SQLValidator:
    """Parses Python source files, extracts SQL strings, and validates
    table/column references against the live DB schema."""

    def __init__(self, db_path: Optional[Path] = None):
        self.cache = get_schema_cache(db_path)
        self.findings: list[dict] = []

    def validate_file(self, filepath: Path) -> list[dict]:
        """Validate all SQL in a Python file. Returns list of findings."""
        findings = []

        # Skip self — our own docstrings contain the patterns we detect
        if filepath.name == 'guardrails.py':
            return findings

        try:
            source = filepath.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            findings.append({
                'file': str(filepath),
                'severity': 'ERROR',
                'category': 'FILE_READ',
                'message': f"Cannot read file: {e}",
            })
            return findings

        # Check for dangerous patterns
        for pattern, category, message in DANGEROUS_PATTERNS:
            for match in re.finditer(pattern, source):
                line_num = source[:match.start()].count('\n') + 1
                findings.append({
                    'file': str(filepath.name),
                    'line': line_num,
                    'severity': 'CRITICAL' if category in ('WRONG_DB_PATH', 'DESTRUCTIVE_OP') else 'WARNING',
                    'category': category,
                    'message': message,
                    'match': match.group()[:80],
                })

        # Extract SQL strings and validate
        for match in _SQL_PATTERN.finditer(source):
            sql = match.group(1) or match.group(2)
            if not sql:
                continue

            line_num = source[:match.start()].count('\n') + 1

            # Validate INSERTs
            for ins in _INSERT_PATTERN.finditer(sql):
                table = ins.group(1).strip()
                cols = [c.strip() for c in ins.group(2).split(',')]
                findings.extend(
                    self._check_columns(filepath.name, line_num, 'INSERT',
                                        table, cols)
                )

            # Validate UPDATEs
            for upd in _UPDATE_PATTERN.finditer(sql):
                table = upd.group(1).strip()
                set_clause = upd.group(2)
                cols = re.findall(r'(\w+)\s*=', set_clause)
                findings.extend(
                    self._check_columns(filepath.name, line_num, 'UPDATE',
                                        table, cols)
                )

            # Validate SELECTs (check FROM table exists)
            for sel in _SELECT_PATTERN.finditer(sql):
                table = sel.group(2).strip()
                if table.upper() in ('SELECT', 'WHERE', 'AS', 'JOIN', 'ON',
                                      'GROUP', 'ORDER', 'LIMIT', 'HAVING',
                                      'UNION', 'EXCEPT', 'INTERSECT'):
                    continue
                if not self.cache.table_exists(table):
                    # Could be a subquery alias — only warn
                    pass

            # Check for DROP/DELETE
            for drop in _DROP_PATTERN.finditer(sql):
                table = drop.group(1).strip()
                findings.append({
                    'file': str(filepath.name),
                    'line': line_num,
                    'severity': 'WARNING',
                    'category': 'DESTRUCTIVE_OP',
                    'message': f"DROP TABLE {table} found — ensure backup exists",
                })

            for delete in _DELETE_PATTERN.finditer(sql):
                table = delete.group(1).strip()
                # Check if there's a WHERE clause
                after = sql[delete.end():]
                if not re.match(r'\s+WHERE\b', after, re.IGNORECASE):
                    findings.append({
                        'file': str(filepath.name),
                        'line': line_num,
                        'severity': 'CRITICAL',
                        'category': 'DESTRUCTIVE_OP',
                        'message': f"DELETE FROM {table} without WHERE — will delete ALL rows",
                    })

        self.findings.extend(findings)
        return findings

    def _check_columns(self, filename: str, line: int, op: str,
                       table: str, columns: list[str]) -> list[dict]:
        """Check if columns exist in table."""
        findings = []

        if not self.cache.table_exists(table):
            # Table might be created by the same module — skip
            return findings

        bad = self.cache.validate_columns(table, columns)
        # FTS5 virtual tables always accept 'rowid' even though PRAGMA table_info doesn't list it
        if bad and table.endswith('_fts'):
            bad = [c for c in bad if c != 'rowid']
        if bad:
            real = list(self.cache.get_columns(table).keys())
            findings.append({
                'file': filename,
                'line': line,
                'severity': 'CRITICAL',
                'category': 'SCHEMA_MISMATCH',
                'message': (
                    f"{op} INTO {table}: columns {bad} don't exist.\n"
                    f"         Actual columns: {real}"
                ),
            })

        # Check NOT NULL for INSERTs
        if op == 'INSERT':
            required = self.cache.get_notnull_columns(table)
            missing = [c for c in required if c not in columns]
            if missing:
                findings.append({
                    'file': filename,
                    'line': line,
                    'severity': 'WARNING',
                    'category': 'MISSING_NOTNULL',
                    'message': f"{op} INTO {table}: NOT NULL columns not in INSERT: {missing}",
                })

        return findings

    def validate_directory(self, directory: Path,
                           pattern: str = "*.py") -> list[dict]:
        """Validate all Python files in a directory."""
        all_findings = []
        for pyfile in sorted(directory.glob(pattern)):
            if pyfile.name.startswith('_') and pyfile.name != '__init__.py':
                continue
            findings = self.validate_file(pyfile)
            all_findings.extend(findings)
        return all_findings


# ═══════════════════════════════════════════════════════════════════════════════
# PRE-FLIGHT CHECK
# ═══════════════════════════════════════════════════════════════════════════════

def preflight(verbose: bool = True) -> dict:
    """Run all safety checks before a pipeline execution.

    Returns:
        {
            'status': 'PASS' | 'WARN' | 'FAIL',
            'checks': [...],
            'critical_count': int,
            'warning_count': int,
        }
    """
    checks = []

    # 1. DB path check
    if _REAL_DB.exists():
        size_mb = _REAL_DB.stat().st_size / (1024 * 1024)
        if size_mb > _MIN_DB_SIZE_MB:
            checks.append({
                'name': 'DB_PATH',
                'status': 'PASS',
                'message': f"Real DB found: {size_mb:.0f}MB",
            })
        else:
            checks.append({
                'name': 'DB_PATH',
                'status': 'FAIL',
                'message': f"DB too small ({size_mb:.1f}MB) — may be stub",
            })
    else:
        checks.append({
            'name': 'DB_PATH',
            'status': 'FAIL',
            'message': f"DB not found at {_REAL_DB}",
        })

    # 2. Stub check
    if _STUB_DB.exists():
        stub_size = _STUB_DB.stat().st_size
        checks.append({
            'name': 'STUB_PRESENT',
            'status': 'WARN',
            'message': f"28KB stub exists at {_STUB_DB} ({stub_size} bytes) — potential trap",
        })

    # 3. Static SQL validation
    validator = SQLValidator()
    sql_findings = validator.validate_directory(_PIPELINE_DIR)

    critical = [f for f in sql_findings if f['severity'] == 'CRITICAL']
    warnings = [f for f in sql_findings if f['severity'] == 'WARNING']

    if critical:
        checks.append({
            'name': 'SQL_VALIDATION',
            'status': 'FAIL',
            'message': f"{len(critical)} CRITICAL SQL issues found",
            'details': critical[:10],
        })
    elif warnings:
        checks.append({
            'name': 'SQL_VALIDATION',
            'status': 'WARN',
            'message': f"{len(warnings)} SQL warnings (0 critical)",
            'details': warnings[:5],
        })
    else:
        checks.append({
            'name': 'SQL_VALIDATION',
            'status': 'PASS',
            'message': "All pipeline SQL validated against live schema",
        })

    # 4. Schema contract check
    if _SCHEMA_CONTRACT.exists():
        checks.append({
            'name': 'SCHEMA_CONTRACT',
            'status': 'PASS',
            'message': "Schema contract file present",
        })
    else:
        checks.append({
            'name': 'SCHEMA_CONTRACT',
            'status': 'WARN',
            'message': "No schema_contract.yaml — using live DB only",
        })

    # 5. Backup freshness
    backup_dir = _LITIGOS_ROOT / "00_SYSTEM" / "backups"
    if backup_dir.exists():
        snapshots = sorted(backup_dir.glob("SNAPSHOT_*"), reverse=True)
        if snapshots:
            newest = snapshots[0].name
            checks.append({
                'name': 'BACKUP_FRESHNESS',
                'status': 'PASS',
                'message': f"Latest backup: {newest}",
            })
        else:
            checks.append({
                'name': 'BACKUP_FRESHNESS',
                'status': 'WARN',
                'message': "No snapshots found in backups/",
            })

    # 6. Disk space
    try:
        usage = shutil.disk_usage("C:\\")
        free_gb = usage.free / (1024**3)
        if free_gb < 2.0:
            checks.append({
                'name': 'DISK_SPACE',
                'status': 'FAIL',
                'message': f"Only {free_gb:.1f}GB free on C: — risk of disk I/O errors",
            })
        elif free_gb < 5.0:
            checks.append({
                'name': 'DISK_SPACE',
                'status': 'WARN',
                'message': f"{free_gb:.1f}GB free on C: — low",
            })
        else:
            checks.append({
                'name': 'DISK_SPACE',
                'status': 'PASS',
                'message': f"{free_gb:.1f}GB free on C:",
            })
    except Exception:
        pass

    # Determine overall status
    has_fail = any(c['status'] == 'FAIL' for c in checks)
    has_warn = any(c['status'] == 'WARN' for c in checks)
    overall = 'FAIL' if has_fail else ('WARN' if has_warn else 'PASS')

    result = {
        'status': overall,
        'timestamp': datetime.now().isoformat(),
        'checks': checks,
        'critical_count': len(critical),
        'warning_count': len(warnings),
    }

    if verbose:
        _print_preflight(result)

    _log_event('PREFLIGHT', json.dumps({
        'status': overall,
        'critical': len(critical),
        'warnings': len(warnings),
    }))

    return result


def _print_preflight(result: dict):
    """Pretty-print preflight results."""
    status = result['status']
    icon = '✅' if status == 'PASS' else ('⚠️' if status == 'WARN' else '❌')
    print(f"\n{'='*60}")
    print(f"  PREFLIGHT CHECK: {icon} {status}")
    print(f"{'='*60}")

    for check in result['checks']:
        s = check['status']
        ci = '✅' if s == 'PASS' else ('⚠️' if s == 'WARN' else '❌')
        print(f"  {ci} {check['name']}: {check['message']}")
        if 'details' in check:
            for d in check['details'][:5]:
                print(f"     → {d.get('file', '?')}:{d.get('line', '?')} "
                      f"[{d.get('category', '?')}] {d.get('message', '')[:120]}")

    print(f"\n  SQL: {result['critical_count']} critical, "
          f"{result['warning_count']} warnings")
    print(f"{'='*60}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMA CONTRACT
# ═══════════════════════════════════════════════════════════════════════════════

def generate_schema_contract(db_path: Optional[Path] = None,
                              output: Optional[Path] = None) -> Path:
    """Generate schema_contract.yaml from live DB.
    This becomes the single source of truth for column names."""
    cache = get_schema_cache(db_path)
    out = output or _SCHEMA_CONTRACT

    lines = [
        "# LitigationOS Schema Contract",
        "# Generated: " + datetime.now().isoformat(),
        "# This is the SINGLE SOURCE OF TRUTH for table schemas.",
        "# All pipeline modules MUST match these column names.",
        "# Re-generate: python guardrails.py contract",
        "",
        "tables:",
    ]

    for table in sorted(PIPELINE_TABLES):
        cols = cache.get_columns(table)
        if not cols:
            lines.append(f"  # {table}: NOT IN DATABASE")
            continue

        lines.append(f"  {table}:")
        lines.append(f"    columns:")
        for col_name, info in cols.items():
            notnull = " NOT NULL" if info['notnull'] else ""
            pk = " PK" if info['pk'] else ""
            default = f" DEFAULT {info['default']}" if info['default'] else ""
            lines.append(f"      {col_name}: {info['type']}{pk}{notnull}{default}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"Schema contract written to {out}")
    return out


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT TRAIL
# ═══════════════════════════════════════════════════════════════════════════════

def _log_event(event_type: str, detail: str):
    """Append to guardrail audit log (JSONL)."""
    try:
        entry = {
            'timestamp': datetime.now().isoformat(),
            'event': event_type,
            'detail': detail[:500],
        }
        with open(_GUARDRAIL_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except Exception:
        pass  # Never crash on logging


# ═══════════════════════════════════════════════════════════════════════════════
# EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class SchemaError(Exception):
    """Raised when SQL references non-existent columns or tables."""
    pass

class DestructiveOpError(Exception):
    """Raised when a destructive operation is attempted without safeguards."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="LitigationOS Pipeline Safety Guardrails",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  preflight    Run all safety checks before pipeline execution
  validate     Validate SQL in a specific Python file
  audit        Validate all pipeline modules
  contract     Generate schema_contract.yaml from live DB
  check-db     Verify DB path and size
        """
    )
    parser.add_argument('command', nargs='?', default='preflight',
                        choices=['preflight', 'validate', 'audit', 'contract',
                                 'check-db'])
    parser.add_argument('target', nargs='?', help='File to validate')
    parser.add_argument('--json', action='store_true', help='JSON output')
    args = parser.parse_args()

    if args.command == 'preflight':
        result = preflight(verbose=not args.json)
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        sys.exit(0 if result['status'] != 'FAIL' else 1)

    elif args.command == 'validate':
        if not args.target:
            print("Usage: guardrails.py validate <filename.py>")
            sys.exit(1)
        target = Path(args.target)
        if not target.exists():
            target = _PIPELINE_DIR / args.target
        validator = SQLValidator()
        findings = validator.validate_file(target)
        if findings:
            for f in findings:
                icon = '❌' if f['severity'] == 'CRITICAL' else '⚠️'
                print(f"  {icon} {f['file']}:{f.get('line', '?')} "
                      f"[{f['category']}] {f['message']}")
            crits = sum(1 for f in findings if f['severity'] == 'CRITICAL')
            print(f"\n{len(findings)} findings ({crits} critical)")
            sys.exit(1 if crits > 0 else 0)
        else:
            print(f"✅ {target.name}: No SQL issues found")

    elif args.command == 'audit':
        validator = SQLValidator()
        findings = validator.validate_directory(_PIPELINE_DIR)
        if findings:
            # Group by file
            by_file = {}
            for f in findings:
                by_file.setdefault(f['file'], []).append(f)

            for fname, flist in sorted(by_file.items()):
                crits = sum(1 for f in flist if f['severity'] == 'CRITICAL')
                warns = sum(1 for f in flist if f['severity'] == 'WARNING')
                icon = '❌' if crits else '⚠️'
                print(f"{icon} {fname}: {crits} critical, {warns} warnings")
                for f in flist[:5]:
                    print(f"    L{f.get('line', '?')}: [{f['category']}] "
                          f"{f['message'][:100]}")
                if len(flist) > 5:
                    print(f"    ... and {len(flist) - 5} more")

            total_c = sum(1 for f in findings if f['severity'] == 'CRITICAL')
            total_w = sum(1 for f in findings if f['severity'] == 'WARNING')
            print(f"\nTotal: {len(findings)} findings "
                  f"({total_c} critical, {total_w} warnings)")
            sys.exit(1 if total_c > 0 else 0)
        else:
            print(f"✅ All pipeline modules validated — no SQL issues")

    elif args.command == 'contract':
        generate_schema_contract()

    elif args.command == 'check-db':
        print(f"Expected DB: {_REAL_DB}")
        if _REAL_DB.exists():
            sz = _REAL_DB.stat().st_size / (1024**3)
            print(f"  Size: {sz:.2f} GB ✅")
        else:
            print(f"  NOT FOUND ❌")
        if _STUB_DB.exists():
            sz = _STUB_DB.stat().st_size
            print(f"\nStub at {_STUB_DB}: {sz} bytes ⚠️ (NEVER use this)")


if __name__ == "__main__":
    main()
