#!/usr/bin/env python3
"""MCP→NEXUS Capability Absorption — adds 13 missing capabilities to nexus_daemon.py.

Surgical insertion: infrastructure classes + 13 handlers + registration.
Atomic: reads file, validates structure, applies all changes, writes back.
"""

import re
import sys
from pathlib import Path

DAEMON = Path(r"C:\Users\andre\LitigationOS\.github\extensions\singularity\nexus_daemon.py")
BACKUP = Path(r"C:\Users\andre\LitigationOS\scripts\nexus_daemon.py")

# ── Read current daemon ──────────────────────────────────────────────────
src = DAEMON.read_text(encoding="utf-8")
lines = src.split("\n")
print(f"[OK] Read daemon: {len(lines)} lines, {len(src):,} bytes")

# ── Validate expected structure ──────────────────────────────────────────
assert "Actions (46):" in src, "Expected 'Actions (46):' in docstring"
assert "pool = ConnectionPool()" in src, "Expected 'pool = ConnectionPool()'"
assert "# ACTION ROUTER" in src, "Expected '# ACTION ROUTER' section"
assert '"red_team": handle_red_team,' in src, "Expected red_team handler registration"
print("[OK] Structure validated")

# ══════════════════════════════════════════════════════════════════════════
# PART 1: Update docstring action count
# ══════════════════════════════════════════════════════════════════════════
src = src.replace("Actions (46):", "Actions (59):", 1)

# Add new action categories to docstring
old_docstring_end = """  # System & Master Data (NEW)
  stats_extended / self_test / ingest_csv / query_master

Started by extension.mjs on load. Stays alive for entire session."""

new_docstring_end = """  # System & Master Data (NEW)
  stats_extended / self_test / ingest_csv / query_master
  # Advanced Intelligence (NEW)
  vector_search / self_audit / evidence_chain / compute_deadlines / red_team
  # Resilience & Diagnostics (ABSORBED from MCP)
  health / record_error / get_error_summary / check_disk_space / scan_all_systems
  # Document Lifecycle (ABSORBED from MCP)
  document_exists / hash_exists / delete_document / insert_document
  # Evolution Write Pipeline (ABSORBED from MCP)
  evolve_md / evolve_txt / evolve_pages
  # Fleet Dispatch (ABSORBED from MCP)
  dispatch_to_swarm

Started by extension.mjs on load. Stays alive for entire session."""

src = src.replace(old_docstring_end, new_docstring_end, 1)
print("[OK] Docstring updated (59 actions)")

# ══════════════════════════════════════════════════════════════════════════
# PART 2: Add imports
# ══════════════════════════════════════════════════════════════════════════
old_imports = "from datetime import datetime, date, timedelta"
new_imports = """from datetime import datetime, date, timedelta
from enum import Enum
import shutil
import hashlib
import threading"""

src = src.replace(old_imports, new_imports, 1)
print("[OK] Imports added (Enum, shutil, hashlib, threading)")

# ══════════════════════════════════════════════════════════════════════════
# PART 3: Add infrastructure classes after pool = ConnectionPool()
# ══════════════════════════════════════════════════════════════════════════

INFRA_CODE = '''
# ── CircuitBreaker (absorbed from MCP db.py) ──────────────────────────────

class CircuitBreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class CircuitBreaker:
    """Trip after N failures, auto-reset after cooldown.

    States: CLOSED (normal) → OPEN (blocking) → HALF_OPEN (testing).
    Ported from MCP db.py lines 188-238, upgraded with thread safety.
    """

    def __init__(self, failure_threshold=5, reset_timeout=60):
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._last_failure_time = None
        self._lock = threading.Lock()

    def record_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            if self._failure_count >= self._failure_threshold:
                self._state = CircuitBreakerState.OPEN

    def record_success(self):
        with self._lock:
            self._failure_count = 0
            self._state = CircuitBreakerState.CLOSED

    def allow_request(self):
        with self._lock:
            if self._state == CircuitBreakerState.CLOSED:
                return True
            if self._state == CircuitBreakerState.OPEN:
                if self._last_failure_time and \\
                   (datetime.now() - self._last_failure_time).total_seconds() > self._reset_timeout:
                    self._state = CircuitBreakerState.HALF_OPEN
                    return True
                return False
            return True  # HALF_OPEN allows one request

    def reset(self):
        with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None

    @property
    def status(self):
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "threshold": self._failure_threshold,
            "reset_timeout": self._reset_timeout,
            "last_failure": str(self._last_failure_time) if self._last_failure_time else None,
        }


# ── Error Codes + Recovery Hints (absorbed from MCP db.py) ────────────────

class ErrorCode(Enum):
    ERR_DB_CONNECT = "ERR_DB_CONNECT"
    ERR_PDF_PERMISSION = "ERR_PDF_PERMISSION"
    ERR_PDF_TIMEOUT = "ERR_PDF_TIMEOUT"
    ERR_FTS_SYNTAX = "ERR_FTS_SYNTAX"
    ERR_DB_LOCKED = "ERR_DB_LOCKED"
    ERR_PATH_TRAVERSAL = "ERR_PATH_TRAVERSAL"
    ERR_DISK_FULL = "ERR_DISK_FULL"
    ERR_EVOLUTION_FAIL = "ERR_EVOLUTION_FAIL"


_RECOVERY_HINTS = {
    ErrorCode.ERR_DB_CONNECT: "Check DB path exists and is not locked. Verify WAL mode PRAGMAs.",
    ErrorCode.ERR_PDF_PERMISSION: "File may be open in another program. Close it and retry.",
    ErrorCode.ERR_PDF_TIMEOUT: "PDF extraction timed out. Try a smaller file or increase timeout.",
    ErrorCode.ERR_FTS_SYNTAX: "FTS5 query syntax error. Sanitize query and retry with LIKE fallback.",
    ErrorCode.ERR_DB_LOCKED: "Database is locked. Another process may hold a write lock. Wait and retry.",
    ErrorCode.ERR_PATH_TRAVERSAL: "Path is outside allowed directories. Check _SAFE_ROOTS.",
    ErrorCode.ERR_DISK_FULL: "Disk is full or below 1GB free. Free space before proceeding.",
    ErrorCode.ERR_EVOLUTION_FAIL: "Evolution pipeline failed. Check source files and DB schema.",
}


# ── Health Status Singleton (absorbed from MCP db.py) ─────────────────────

class HealthStatus:
    """Singleton tracking system health — startup time, graph status, degradation."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.startup_time = datetime.now()
            cls._instance.graphs_loaded = False
            cls._instance.graph_errors = []
            cls._instance.degraded = False
            cls._instance.circuit_breaker = CircuitBreaker()
        return cls._instance

    @property
    def status(self):
        uptime = (datetime.now() - self.startup_time).total_seconds()
        return {
            "startup_time": str(self.startup_time),
            "uptime_seconds": round(uptime, 1),
            "graphs_loaded": self.graphs_loaded,
            "graph_errors": self.graph_errors[:5],
            "degraded": self.degraded,
            "circuit_breaker": self.circuit_breaker.status,
        }


health = HealthStatus()

# ── Path Traversal Protection (absorbed from MCP db.py) ───────────────────

_SAFE_ROOTS = [
    os.path.normpath("C:\\\\Users\\\\andre\\\\LitigationOS"),
    os.path.normpath("D:\\\\"),
    os.path.normpath("F:\\\\"),
    os.path.normpath("G:\\\\"),
    os.path.normpath("H:\\\\"),
    os.path.normpath("I:\\\\"),
    os.path.normpath("J:\\\\"),
]


def _validate_path(p):
    """Ensure path is under an allowed root. Raises ValueError on traversal."""
    real = os.path.normpath(os.path.realpath(p))
    for root in _SAFE_ROOTS:
        if real.startswith(root):
            return real
    raise ValueError(f"Path traversal blocked: {p} not under any safe root")


# ── Table Existence Check ─────────────────────────────────────────────────

def _table_exists(conn, table_name):
    """Check if a table exists in the database."""
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    ).fetchone()
    return row[0] > 0 if row else False


# ── Evolution Helpers (ported from MCP db.py) ─────────────────────────────

_RE_MD_HEADING = re.compile(r"^(#{1,6})\\s+(.+)$", re.MULTILINE)
_RE_MCR = re.compile(r"MCR\\s+\\d+\\.\\d+[A-Za-z]?(?:\\([^)]+\\))?")
_RE_MCL = re.compile(r"MCL\\s+\\d+\\.\\d+[a-z]?")
_RE_VEHICLE = re.compile(r"\\b(?:motion|petition|complaint|brief|application|order)\\s+(?:for|to|of)\\s+\\w+", re.IGNORECASE)
_RE_AGENT = re.compile(r"AGENT:([A-Z_]+)")
_RE_AUTHORITY = re.compile(r"(?:\\d+\\s+(?:Mich(?:\\s+App)?|US|USC|F\\.?(?:2d|3d|4th))\\s+\\d+)")


def _extract_md_sections(text, source_file, source_path):
    """Parse markdown text into section dicts with heading hierarchy."""
    sections = []
    headings = list(_RE_MD_HEADING.finditer(text))

    if not headings:
        sections.append({
            "level": 0, "title": source_file, "path": source_path,
            "content": text[:50000], "source_file": source_file,
        })
        return sections

    for i, m in enumerate(headings):
        level = len(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        content = text[start:end].strip()[:50000]
        sections.append({
            "level": level, "title": title,
            "path": f"{source_path}#{title.replace(' ', '-').lower()}",
            "content": content, "source_file": source_file,
        })
    return sections


def _extract_cross_refs(text):
    """Extract legal cross-references from text via compiled regex patterns."""
    refs = []
    for m in _RE_MCR.finditer(text):
        refs.append({"ref_type": "rule", "ref_value": m.group(), "confidence": 0.7})
    for m in _RE_MCL.finditer(text):
        refs.append({"ref_type": "rule", "ref_value": m.group(), "confidence": 0.7})
    for m in _RE_VEHICLE.finditer(text):
        refs.append({"ref_type": "vehicle", "ref_value": m.group(), "confidence": 0.5})
    for m in _RE_AGENT.finditer(text):
        refs.append({"ref_type": "agent", "ref_value": m.group(1), "confidence": 0.8})
    for m in _RE_AUTHORITY.finditer(text):
        refs.append({"ref_type": "authority", "ref_value": m.group(), "confidence": 0.6})
    return refs


def _link_ref_to_graph(conn, ref_value):
    """Try to find matching graph_node for a cross-reference value."""
    if not _table_exists(conn, "graph_nodes"):
        return None
    try:
        row = conn.execute(
            "SELECT id, graph_source FROM graph_nodes WHERE label LIKE ? LIMIT 1",
            (f"%{ref_value}%",)
        ).fetchone()
        if row:
            return {"graph_node_id": row[0], "graph_source": row[1]}
    except Exception:
        pass
    return None

'''

# Insert after pool = ConnectionPool() and before STATS_TABLES
old_pool_line = "pool = ConnectionPool()\n\n# ── Stats Tables"
new_pool_line = "pool = ConnectionPool()\n" + INFRA_CODE + "\n# ── Stats Tables"
src = src.replace(old_pool_line, new_pool_line, 1)
print("[OK] Infrastructure classes inserted (CircuitBreaker, HealthStatus, ErrorCode, helpers)")

# ══════════════════════════════════════════════════════════════════════════
# PART 4: Add 13 new handler functions before ACTION ROUTER
# ══════════════════════════════════════════════════════════════════════════

NEW_HANDLERS = '''

# ══════════════════════════════════════════════════════════════════════════
# ABSORBED MCP CAPABILITIES (13 new handlers)
# ══════════════════════════════════════════════════════════════════════════

def handle_health(req):
    """Composite health check: CircuitBreaker + HealthStatus + error summary."""
    reset_cb = req.get("reset_circuit_breaker", False)
    if reset_cb:
        health.circuit_breaker.reset()

    result = health.status
    result["ok"] = True

    # Recent error summary (last 24h)
    try:
        conn = pool.sqlite
        if _table_exists(conn, "error_log"):
            rows = conn.execute(
                """SELECT error_code, tool_name, COUNT(*) as cnt,
                          MAX(created_at) as last_seen
                   FROM error_log
                   WHERE created_at > datetime('now', '-24 hours')
                   GROUP BY error_code, tool_name
                   ORDER BY cnt DESC LIMIT 20"""
            ).fetchall()
            result["recent_errors"] = [dict(r) for r in rows]
        else:
            result["recent_errors"] = []
    except Exception as e:
        result["recent_errors"] = [{"error": str(e)}]

    return result


def handle_record_error(req):
    """Record an error event to the error_log table for telemetry."""
    error_code = req.get("error_code", "UNKNOWN")
    tool_name = req.get("tool_name", "unknown")
    message = req.get("message", "")

    conn = pool.sqlite
    # Ensure error_log table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS error_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_code TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            message TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute(
        "INSERT INTO error_log (error_code, tool_name, message) VALUES (?, ?, ?)",
        (error_code, tool_name, message[:2000])
    )
    conn.commit()

    # Update circuit breaker
    health.circuit_breaker.record_failure()

    return {"ok": True, "action": "error_recorded", "error_code": error_code}


def handle_get_error_summary(req):
    """Error telemetry: group errors by code+tool from error_log."""
    hours = req.get("hours", 24)
    conn = pool.sqlite

    if not _table_exists(conn, "error_log"):
        return {"ok": True, "rows": [], "count": 0, "message": "No error_log table"}

    try:
        rows = conn.execute(
            """SELECT error_code, tool_name, COUNT(*) as cnt,
                      MAX(created_at) as last_seen,
                      MIN(created_at) as first_seen
               FROM error_log
               WHERE created_at > datetime('now', ? || ' hours')
               GROUP BY error_code, tool_name
               ORDER BY cnt DESC LIMIT 50""",
            (f"-{hours}",)
        ).fetchall()
        data = [dict(r) for r in rows]

        # Add recovery hints
        for row in data:
            try:
                code = ErrorCode(row["error_code"])
                row["recovery_hint"] = _RECOVERY_HINTS.get(code, "")
            except ValueError:
                row["recovery_hint"] = ""

        return {"ok": True, "rows": data, "count": len(data), "hours": hours}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def handle_check_disk_space(req):
    """Disk space across all litigation drives using shutil.disk_usage()."""
    drives = req.get("drives", ["C:", "D:", "F:", "G:", "I:", "J:"])
    results = []

    for drive in drives:
        drive_path = drive if drive.endswith("\\\\") else drive + "\\\\"
        try:
            usage = shutil.disk_usage(drive_path)
            results.append({
                "drive": drive,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent_used": round(usage.used * 100 / usage.total, 1) if usage.total else 0,
                "status": "OK" if usage.free > 1024**3 else "LOW" if usage.free > 512*1024**2 else "CRITICAL",
            })
        except OSError:
            results.append({"drive": drive, "status": "UNAVAILABLE"})

    critical = [r for r in results if r.get("status") == "CRITICAL"]
    return {
        "ok": True,
        "drives": results,
        "critical_count": len(critical),
        "warning": "DISK SPACE CRITICAL" if critical else None,
    }


def handle_scan_all_systems(req):
    """Composite system scan: DB integrity, FTS5, disk, connections, circuit breaker."""
    results = {"ok": True, "checks": {}, "pass_count": 0, "fail_count": 0}
    conn = pool.sqlite

    # 1. DB connectivity
    try:
        conn.execute("SELECT 1")
        results["checks"]["db_connect"] = {"status": "PASS"}
        results["pass_count"] += 1
    except Exception as e:
        results["checks"]["db_connect"] = {"status": "FAIL", "error": str(e)}
        results["fail_count"] += 1

    # 2. DB integrity check (quick)
    try:
        row = conn.execute("PRAGMA quick_check(1)").fetchone()
        ok = row[0] == "ok" if row else False
        results["checks"]["db_integrity"] = {"status": "PASS" if ok else "FAIL"}
        results["pass_count" if ok else "fail_count"] += 1
    except Exception as e:
        results["checks"]["db_integrity"] = {"status": "FAIL", "error": str(e)}
        results["fail_count"] += 1

    # 3. FTS5 round-trip
    try:
        if _table_exists(conn, "evidence_fts"):
            conn.execute("SELECT COUNT(*) FROM evidence_fts WHERE evidence_fts MATCH 'test'")
            results["checks"]["fts5"] = {"status": "PASS"}
        else:
            results["checks"]["fts5"] = {"status": "SKIP", "reason": "No evidence_fts table"}
        results["pass_count"] += 1
    except Exception as e:
        results["checks"]["fts5"] = {"status": "FAIL", "error": str(e)}
        results["fail_count"] += 1

    # 4. DuckDB
    if _HAS_DUCKDB and pool.duck:
        try:
            pool.duck.execute("SELECT 1")
            results["checks"]["duckdb"] = {"status": "PASS"}
            results["pass_count"] += 1
        except Exception as e:
            results["checks"]["duckdb"] = {"status": "FAIL", "error": str(e)}
            results["fail_count"] += 1
    else:
        results["checks"]["duckdb"] = {"status": "SKIP", "reason": "Not available"}

    # 5. LanceDB
    if _HAS_LANCEDB and pool.lance_table is not None:
        results["checks"]["lancedb"] = {"status": "PASS"}
        results["pass_count"] += 1
    else:
        results["checks"]["lancedb"] = {"status": "SKIP", "reason": "Not available"}

    # 6. Disk space (C: only for speed)
    try:
        usage = shutil.disk_usage("C:\\\\")
        free_gb = usage.free / (1024**3)
        results["checks"]["disk_c"] = {
            "status": "PASS" if free_gb > 1 else "WARN",
            "free_gb": round(free_gb, 2),
        }
        results["pass_count"] += 1
    except Exception as e:
        results["checks"]["disk_c"] = {"status": "FAIL", "error": str(e)}
        results["fail_count"] += 1

    # 7. Circuit breaker
    cb = health.circuit_breaker
    results["checks"]["circuit_breaker"] = {
        "status": "PASS" if cb.allow_request() else "FAIL",
        **cb.status,
    }
    results["pass_count" if cb.allow_request() else "fail_count"] += 1

    # 8. Health status
    results["health"] = health.status

    return results


def handle_evolve_md(req):
    """Evolve .md files into cross-reference knowledge layer (WRITE operation).

    Walks directory for .md files, extracts sections via headings,
    extracts cross-refs (MCR/MCL/case law), links to graph nodes.
    Inserts to md_sections + md_cross_refs. Skips already-evolved files.
    Ported from MCP db.py evolve_all_md_files (lines 1468-1529).
    """
    directory = req.get("directory", "")
    if not directory:
        return {"ok": False, "error": "No directory provided"}

    try:
        real_dir = _validate_path(directory)
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    if not os.path.isdir(real_dir):
        return {"ok": False, "error": f"Not a directory: {real_dir}"}

    conn = pool.sqlite
    # Ensure tables exist
    conn.execute("""CREATE TABLE IF NOT EXISTS md_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_file TEXT, source_path TEXT, level INTEGER,
        title TEXT, content TEXT, source_type TEXT DEFAULT 'md',
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS md_cross_refs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id INTEGER, ref_type TEXT, ref_value TEXT,
        confidence REAL, graph_node_id TEXT, graph_source TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    # Get already-evolved files
    evolved = set()
    try:
        rows = conn.execute(
            "SELECT DISTINCT source_file FROM md_sections WHERE source_type = 'md'"
        ).fetchall()
        evolved = {r[0] for r in rows}
    except Exception:
        pass

    stats = {"files_found": 0, "files_evolved": 0, "files_skipped": 0,
             "sections_created": 0, "cross_refs_created": 0, "errors": []}

    for root, _, files in os.walk(real_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            stats["files_found"] += 1
            fpath = os.path.join(root, fname)

            if fname in evolved:
                stats["files_skipped"] += 1
                continue

            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read(500000)  # 500KB max

                sections = _extract_md_sections(text, fname, fpath)
                for sec in sections:
                    cur = conn.execute(
                        """INSERT INTO md_sections (source_file, source_path, level, title, content, source_type)
                           VALUES (?, ?, ?, ?, ?, 'md')""",
                        (sec["source_file"], sec["path"], sec["level"], sec["title"], sec["content"])
                    )
                    section_id = cur.lastrowid
                    stats["sections_created"] += 1

                    xrefs = _extract_cross_refs(sec["content"])
                    for xr in xrefs:
                        graph_link = _link_ref_to_graph(conn, xr["ref_value"])
                        gn_id = graph_link["graph_node_id"] if graph_link else None
                        gs = graph_link["graph_source"] if graph_link else None
                        conn.execute(
                            """INSERT INTO md_cross_refs (section_id, ref_type, ref_value, confidence, graph_node_id, graph_source)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (section_id, xr["ref_type"], xr["ref_value"], xr["confidence"], gn_id, gs)
                        )
                        stats["cross_refs_created"] += 1

                stats["files_evolved"] += 1
                evolved.add(fname)

            except Exception as e:
                stats["errors"].append({"file": fname, "error": str(e)[:200]})

    conn.commit()
    return {"ok": True, **stats}


def handle_evolve_txt(req):
    """Evolve .txt files into cross-reference knowledge layer (WRITE operation).

    Each .txt file treated as single section. Extracts cross-refs, links to graph.
    Ported from MCP db.py evolve_all_txt_files (lines 1532-1590).
    """
    directory = req.get("directory", "")
    if not directory:
        return {"ok": False, "error": "No directory provided"}

    try:
        real_dir = _validate_path(directory)
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    if not os.path.isdir(real_dir):
        return {"ok": False, "error": f"Not a directory: {real_dir}"}

    conn = pool.sqlite
    conn.execute("""CREATE TABLE IF NOT EXISTS md_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_file TEXT, source_path TEXT, level INTEGER,
        title TEXT, content TEXT, source_type TEXT DEFAULT 'md',
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS md_cross_refs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id INTEGER, ref_type TEXT, ref_value TEXT,
        confidence REAL, graph_node_id TEXT, graph_source TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    evolved = set()
    try:
        rows = conn.execute(
            "SELECT DISTINCT source_file FROM md_sections WHERE source_type = 'txt'"
        ).fetchall()
        evolved = {r[0] for r in rows}
    except Exception:
        pass

    stats = {"files_found": 0, "files_evolved": 0, "files_skipped": 0,
             "sections_created": 0, "cross_refs_created": 0, "errors": []}

    for root, _, files in os.walk(real_dir):
        for fname in files:
            if not fname.endswith(".txt"):
                continue
            stats["files_found"] += 1
            fpath = os.path.join(root, fname)

            if fname in evolved:
                stats["files_skipped"] += 1
                continue

            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read(500000)

                cur = conn.execute(
                    """INSERT INTO md_sections (source_file, source_path, level, title, content, source_type)
                       VALUES (?, ?, 0, ?, ?, 'txt')""",
                    (fname, fpath, fname, text[:50000])
                )
                section_id = cur.lastrowid
                stats["sections_created"] += 1

                xrefs = _extract_cross_refs(text)
                for xr in xrefs:
                    graph_link = _link_ref_to_graph(conn, xr["ref_value"])
                    gn_id = graph_link["graph_node_id"] if graph_link else None
                    gs = graph_link["graph_source"] if graph_link else None
                    conn.execute(
                        """INSERT INTO md_cross_refs (section_id, ref_type, ref_value, confidence, graph_node_id, graph_source)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (section_id, xr["ref_type"], xr["ref_value"], xr["confidence"], gn_id, gs)
                    )
                    stats["cross_refs_created"] += 1

                stats["files_evolved"] += 1
                evolved.add(fname)

            except Exception as e:
                stats["errors"].append({"file": fname, "error": str(e)[:200]})

    conn.commit()
    return {"ok": True, **stats}


def handle_evolve_pages(req):
    """Evolve ingested PDF pages into cross-reference knowledge layer (WRITE operation).

    Iterates documents→pages, creates sections per page, extracts cross-refs.
    Ported from MCP db.py evolve_from_pages (lines 1593-1662).
    """
    document_id = req.get("document_id")  # None = all documents
    conn = pool.sqlite

    if not _table_exists(conn, "pages"):
        return {"ok": False, "error": "No 'pages' table — ingest PDFs first"}

    conn.execute("""CREATE TABLE IF NOT EXISTS md_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_file TEXT, source_path TEXT, level INTEGER,
        title TEXT, content TEXT, source_type TEXT DEFAULT 'md',
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS md_cross_refs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id INTEGER, ref_type TEXT, ref_value TEXT,
        confidence REAL, graph_node_id TEXT, graph_source TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    # Get already-evolved page sources
    evolved_sources = set()
    try:
        rows = conn.execute(
            "SELECT DISTINCT source_file FROM md_sections WHERE source_type = 'pdf'"
        ).fetchall()
        evolved_sources = {r[0] for r in rows}
    except Exception:
        pass

    # Build document query
    if document_id:
        doc_rows = conn.execute("SELECT id, file_name FROM documents WHERE id = ?", (document_id,)).fetchall()
    else:
        # Adaptive column check
        cols = {r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()}
        name_col = "file_name" if "file_name" in cols else "title" if "title" in cols else "file_path"
        doc_rows = conn.execute(f"SELECT id, {name_col} FROM documents").fetchall()

    stats = {"documents_found": len(doc_rows), "pages_evolved": 0, "pages_skipped": 0,
             "sections_created": 0, "cross_refs_created": 0, "errors": []}

    for doc_id, doc_name in doc_rows:
        source_key = f"pdf:{doc_id}:{doc_name}"
        if source_key in evolved_sources:
            stats["pages_skipped"] += 1
            continue

        try:
            pages = conn.execute(
                "SELECT page_number, text_content FROM pages WHERE document_id = ? ORDER BY page_number",
                (doc_id,)
            ).fetchall()

            for page_num, text in pages:
                if not text or not text.strip():
                    continue

                title = f"{doc_name} — Page {page_num}"
                cur = conn.execute(
                    """INSERT INTO md_sections (source_file, source_path, level, title, content, source_type)
                       VALUES (?, ?, 0, ?, ?, 'pdf')""",
                    (source_key, f"document:{doc_id}/page:{page_num}", title, text[:50000])
                )
                section_id = cur.lastrowid
                stats["sections_created"] += 1

                xrefs = _extract_cross_refs(text)
                for xr in xrefs:
                    graph_link = _link_ref_to_graph(conn, xr["ref_value"])
                    gn_id = graph_link["graph_node_id"] if graph_link else None
                    gs = graph_link["graph_source"] if graph_link else None
                    conn.execute(
                        """INSERT INTO md_cross_refs (section_id, ref_type, ref_value, confidence, graph_node_id, graph_source)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (section_id, xr["ref_type"], xr["ref_value"], xr["confidence"], gn_id, gs)
                    )
                    stats["cross_refs_created"] += 1

                stats["pages_evolved"] += 1

            evolved_sources.add(source_key)

        except Exception as e:
            stats["errors"].append({"document": doc_name, "error": str(e)[:200]})

    conn.commit()
    return {"ok": True, **stats}


def handle_document_exists(req):
    """Check if a document is already indexed (by file_path)."""
    file_path = req.get("file_path", "")
    if not file_path:
        return {"ok": False, "error": "No file_path provided"}

    conn = pool.sqlite
    if not _table_exists(conn, "documents"):
        return {"ok": True, "exists": False, "message": "No documents table"}

    cols = {r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()}
    path_col = "file_path" if "file_path" in cols else "source_path" if "source_path" in cols else None

    if not path_col:
        return {"ok": True, "exists": False, "message": "No path column in documents"}

    row = conn.execute(f"SELECT id FROM documents WHERE {path_col} = ? LIMIT 1", (file_path,)).fetchone()
    return {"ok": True, "exists": row is not None, "document_id": row[0] if row else None}


def handle_hash_exists(req):
    """Check if a document with given SHA-256 hash exists."""
    sha256 = req.get("sha256", "")
    if not sha256:
        return {"ok": False, "error": "No sha256 provided"}

    conn = pool.sqlite
    if not _table_exists(conn, "documents"):
        return {"ok": True, "exists": False}

    cols = {r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()}
    hash_col = "sha256_hash" if "sha256_hash" in cols else "sha256" if "sha256" in cols else None

    if not hash_col:
        return {"ok": True, "exists": False, "message": "No hash column"}

    row = conn.execute(f"SELECT id FROM documents WHERE {hash_col} = ? LIMIT 1", (sha256,)).fetchone()
    return {"ok": True, "exists": row is not None, "document_id": row[0] if row else None}


def handle_delete_document(req):
    """Delete a document and its pages from the knowledge base (WRITE operation)."""
    doc_id = req.get("document_id")
    if not doc_id:
        return {"ok": False, "error": "No document_id provided"}

    conn = pool.sqlite
    if not _table_exists(conn, "documents"):
        return {"ok": False, "error": "No documents table"}

    # Delete pages first (cascade)
    pages_deleted = 0
    if _table_exists(conn, "pages"):
        cur = conn.execute("DELETE FROM pages WHERE document_id = ?", (doc_id,))
        pages_deleted = cur.rowcount

    cur = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    doc_deleted = cur.rowcount
    conn.commit()

    return {
        "ok": True, "action": "deleted",
        "document_id": doc_id, "document_deleted": doc_deleted,
        "pages_deleted": pages_deleted,
    }


def handle_insert_document(req):
    """Insert a new document record (WRITE operation)."""
    file_path = req.get("file_path", "")
    file_name = req.get("file_name", "")
    sha256 = req.get("sha256", "")
    page_count = req.get("page_count", 0)
    file_size = req.get("file_size", 0)

    if not file_path:
        return {"ok": False, "error": "No file_path provided"}

    try:
        _validate_path(file_path)
    except ValueError as e:
        return {"ok": False, "error": str(e)}

    conn = pool.sqlite
    conn.execute("""CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT, file_path TEXT, sha256_hash TEXT,
        page_count INTEGER DEFAULT 0, file_size_bytes INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )""")

    cur = conn.execute(
        """INSERT INTO documents (file_name, file_path, sha256_hash, page_count, file_size_bytes)
           VALUES (?, ?, ?, ?, ?)""",
        (file_name or os.path.basename(file_path), file_path, sha256, page_count, file_size)
    )
    conn.commit()

    return {"ok": True, "action": "inserted", "document_id": cur.lastrowid}


def handle_dispatch_to_swarm(req):
    """Agent routing recommendations based on task description.

    Matches task keywords to agent specializations and returns ranked recommendations.
    """
    task = req.get("task", "")
    if not task:
        return {"ok": False, "error": "No task provided"}

    task_lower = task.lower()

    # Agent capability matrix
    agents = [
        {"name": "filing-forge-master", "keywords": ["filing", "motion", "brief", "packet", "bates", "service", "qa"],
         "role": "Filing packages, QA, Bates stamps, service tracking"},
        {"name": "evidence-warfare-commander", "keywords": ["evidence", "gap", "impeachment", "contradiction", "witness"],
         "role": "Evidence triage, gap analysis, impeachment prep"},
        {"name": "judicial-accountability-engine", "keywords": ["judge", "mcneill", "judicial", "jtc", "misconduct", "bias", "canon"],
         "role": "Judicial misconduct documentation, JTC complaints"},
        {"name": "timeline-forensics", "keywords": ["timeline", "chronology", "transcript", "hearing", "testimony"],
         "role": "Extract testimony/rulings, build timelines"},
        {"name": "appellate-record-builder", "keywords": ["appeal", "coa", "msc", "appendix", "record", "brief"],
         "role": "COA/MSC record assembly, appendices"},
        {"name": "family-law-guardian", "keywords": ["custody", "parenting", "child", "gal", "best interest", "factor"],
         "role": "Custody analysis, MCL 722.23 factors"},
        {"name": "damages-calculator", "keywords": ["damages", "cost", "fee", "mileage", "economic", "punitive"],
         "role": "Calculate damages across all categories"},
        {"name": "case-strategy-architect", "keywords": ["strategy", "plan", "priority", "sequence", "war"],
         "role": "High-level litigation strategy and prioritization"},
        {"name": "compliance-auditor", "keywords": ["redact", "pii", "compliance", "audit", "child name"],
         "role": "Redact PII, audit filing compliance"},
        {"name": "contempt-prosecutor", "keywords": ["contempt", "show cause", "violation", "enforce"],
         "role": "Contempt motions, show cause proceedings"},
        {"name": "federal-1983-specialist", "keywords": ["1983", "federal", "civil rights", "qualified immunity", "monell"],
         "role": "42 USC §1983 claims, federal complaints"},
        {"name": "deep-research", "keywords": ["research", "case law", "statute", "legal theory", "web"],
         "role": "Deep legal and factual research with web search"},
    ]

    scored = []
    for agent in agents:
        score = sum(3 for kw in agent["keywords"] if kw in task_lower)
        if score > 0:
            scored.append({**agent, "relevance_score": score})

    scored.sort(key=lambda x: x["relevance_score"], reverse=True)
    top = scored[:5] if scored else [{"name": "case-strategy-architect", "role": "Default: strategy", "relevance_score": 1}]

    return {
        "ok": True,
        "task": task[:200],
        "recommendations": top,
        "count": len(top),
    }

'''

# Insert before ACTION ROUTER section
old_router = """# ══════════════════════════════════════════════════════════════════════════
# ACTION ROUTER
# ══════════════════════════════════════════════════════════════════════════"""

src = src.replace(old_router, NEW_HANDLERS + "\n" + old_router, 1)
print("[OK] 13 new handler functions inserted")

# ══════════════════════════════════════════════════════════════════════════
# PART 5: Register new handlers in HANDLERS dict
# ══════════════════════════════════════════════════════════════════════════

old_handlers_end = '''    "red_team": handle_red_team,
}'''

new_handlers_end = '''    "red_team": handle_red_team,
    # Resilience & Diagnostics (ABSORBED from MCP)
    "health": handle_health,
    "record_error": handle_record_error,
    "get_error_summary": handle_get_error_summary,
    "check_disk_space": handle_check_disk_space,
    "scan_all_systems": handle_scan_all_systems,
    # Document Lifecycle (ABSORBED from MCP)
    "document_exists": handle_document_exists,
    "hash_exists": handle_hash_exists,
    "delete_document": handle_delete_document,
    "insert_document": handle_insert_document,
    # Evolution Write Pipeline (ABSORBED from MCP)
    "evolve_md": handle_evolve_md,
    "evolve_txt": handle_evolve_txt,
    "evolve_pages": handle_evolve_pages,
    # Fleet Dispatch (ABSORBED from MCP)
    "dispatch_to_swarm": handle_dispatch_to_swarm,
}'''

src = src.replace(old_handlers_end, new_handlers_end, 1)
print("[OK] 13 handlers registered in HANDLERS dict")

# ══════════════════════════════════════════════════════════════════════════
# PART 6: Write modified daemon
# ══════════════════════════════════════════════════════════════════════════

# Validate Python syntax before writing
try:
    compile(src, "<nexus_daemon>", "exec")
    print("[OK] Python syntax validation PASSED")
except SyntaxError as e:
    print(f"[FAIL] Syntax error: {e}")
    sys.exit(1)

# Count handlers
handler_count = src.count('"handle_') + src.count("': handle_")
# Actually count entries in HANDLERS dict
import re as ree
handler_entries = len(ree.findall(r'"[a-z_]+":\s*handle_', src))
print(f"[OK] Handler registrations found: {handler_entries}")

# Write
DAEMON.write_text(src, encoding="utf-8")
new_lines = src.count("\n") + 1
print(f"[OK] Written: {DAEMON} ({new_lines} lines, {len(src):,} bytes)")

# Sync backup
BACKUP.write_text(src, encoding="utf-8")
print(f"[OK] Backup synced: {BACKUP}")

print(f"\n{'='*60}")
print(f"MCP→NEXUS ABSORPTION COMPLETE")
print(f"  Old: 46 handlers, 2,325 lines")
print(f"  New: {handler_entries} handlers, {new_lines} lines")
print(f"  Added: CircuitBreaker, HealthStatus, ErrorCode, path validation")
print(f"  Added: Evolution pipeline (md/txt/pages), document lifecycle")
print(f"  Added: Disk monitoring, system scan, error telemetry, fleet dispatch")
print(f"{'='*60}")
