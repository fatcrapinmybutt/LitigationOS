"""LitigationOS MCP Server v3 Tools — Enhancement Layer

Exposes new DB infrastructure (views, dedup registry, drive org log,
performance benchmarks, agent fleet inventory) as callable tool functions.

Each function returns a dict or list suitable for JSON serialization.
Integration with the FastMCP server is handled via tools_v3_bridge.py.
"""
import glob as _glob
import os
import sqlite3
from datetime import datetime

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)


def get_db():
    """Open a WAL-mode connection with generous busy timeout."""
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


# ── DASHBOARD TOOLS ─────────────────────────────────────────────────

def litigation_case_health() -> dict:
    """Get case health dashboard from v_case_health view.

    Returns counts of quotes, harms, impeachment points, contradictions,
    claims, active deadlines, and past deadlines across all lanes.
    """
    conn = get_db()
    try:
        row = conn.execute("SELECT * FROM v_case_health").fetchone()
        if row:
            return dict(row)
        return {"error": "v_case_health view returned no data"}
    except Exception as e:
        return {"error": f"v_case_health view not available: {e}"}
    finally:
        conn.close()


def litigation_adversary_threats(limit: int = 20) -> list | dict:
    """Get adversary threat matrix from v_adversary_threats view.

    Returns ranked list of adversaries with harm counts, critical counts,
    and category spread.  *limit* caps the result set.
    """
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM v_adversary_threats ORDER BY harm_count DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"error": f"v_adversary_threats view not available: {e}"}
    finally:
        conn.close()


def litigation_filing_pipeline() -> list | dict:
    """Get filing pipeline status from v_filing_pipeline view.

    Returns every filing action with phase, readiness %, risk score, tier,
    gaps filled vs remaining, and sequencing metadata.
    """
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM v_filing_pipeline ORDER BY sequence_order"
        ).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        return {"error": f"v_filing_pipeline query failed: {e}"}
    finally:
        conn.close()


# ── DEDUP TOOLS ─────────────────────────────────────────────────────

def litigation_dedup_status() -> dict:
    """Get deduplication status from content_dedup_registry.

    Returns aggregate counts: total files, unique hashes, exact duplicates,
    near duplicates, pending review items, and drives scanned.
    """
    conn = get_db()
    try:
        stats = conn.execute("""
            SELECT
                COUNT(*)                                              AS total_files,
                COUNT(DISTINCT sha256_hash)                           AS unique_hashes,
                COUNT(CASE WHEN action = 'exact_dup'  THEN 1 END)    AS exact_duplicates,
                COUNT(CASE WHEN action = 'near_dup'   THEN 1 END)    AS near_duplicates,
                COUNT(CASE WHEN action = 'pending'    THEN 1 END)    AS pending_review,
                COUNT(DISTINCT drive_letter)                          AS drives_scanned
            FROM content_dedup_registry
        """).fetchone()
        return dict(stats)
    except Exception:
        return {"total_files": 0, "status": "not yet scanned"}
    finally:
        conn.close()


def litigation_dedup_duplicates(drive: str | None = None, limit: int = 50) -> list:
    """List identified duplicates, optionally filtered by drive letter.

    Each result includes file path, size, SHA-256, the canonical file it
    duplicates, and the current action status.
    """
    conn = get_db()
    try:
        if drive:
            rows = conn.execute("""
                SELECT file_path, file_size, sha256_hash, duplicate_of, action
                FROM content_dedup_registry
                WHERE drive_letter = ? AND duplicate_of IS NOT NULL
                ORDER BY file_size DESC
                LIMIT ?
            """, (drive, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT file_path, file_size, sha256_hash, duplicate_of, action
                FROM content_dedup_registry
                WHERE duplicate_of IS NOT NULL
                ORDER BY file_size DESC
                LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        conn.close()


# ── DRIVE ORGANIZATION TOOLS ────────────────────────────────────────

def litigation_drive_summary() -> list | dict:
    """Get per-drive file summary from v_drive_summary view.

    Each drive shows file count, total bytes, unique names, duplicates
    found, files already moved, and files still pending.
    """
    conn = get_db()
    try:
        rows = conn.execute("SELECT * FROM v_drive_summary").fetchall()
        if rows:
            return [dict(r) for r in rows]
        return {"status": "no drive data yet"}
    except Exception as e:
        return {"status": f"v_drive_summary not available: {e}"}
    finally:
        conn.close()


def litigation_drive_org_log(status: str | None = None, limit: int = 50) -> list:
    """Get drive organization action log.

    Returns recent file-move / reorganization actions recorded in
    drive_organization_log, optionally filtered by *status*.
    """
    conn = get_db()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM drive_organization_log "
                "WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM drive_organization_log "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        conn.close()


# ── PERFORMANCE TOOLS ───────────────────────────────────────────────

def litigation_query_benchmarks(limit: int = 20) -> list:
    """Get recent query performance benchmarks.

    Returns the last *limit* entries from query_performance_log including
    query name, execution time in milliseconds, row count, and timestamp.
    """
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT query_name, execution_time_ms, row_count, timestamp
            FROM query_performance_log
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []
    finally:
        conn.close()


# ── AGENT FLEET TOOLS ──────────────────────────────────────────────

def litigation_agent_inventory() -> dict:
    """List all Copilot agents and skills with coverage metadata.

    Scans the .copilot/agents and .copilot/skills directories for .md
    definition files and returns counts plus a sorted inventory list.
    """
    agent_dir = r"C:\Users\andre\.copilot\agents"
    skill_dir = r"C:\Users\andre\.copilot\skills"
    items: list[dict] = []

    for directory, kind in [(agent_dir, "agent"), (skill_dir, "skill")]:
        if not os.path.isdir(directory):
            continue
        for f in _glob.glob(os.path.join(directory, "*.md")):
            name = os.path.basename(f).replace(".md", "")
            try:
                size = os.path.getsize(f)
            except OSError:
                size = 0
            items.append({"name": name, "type": kind, "size_bytes": size})

    agents = [i for i in items if i["type"] == "agent"]
    skills = [i for i in items if i["type"] == "skill"]

    return {
        "total_agents": len(agents),
        "total_skills": len(skills),
        "inventory": sorted(items, key=lambda x: (x["type"], x["name"])),
    }


# ── TOOL REGISTRY (for programmatic discovery) ─────────────────────

TOOLS_V3 = {
    "litigation_case_health":       litigation_case_health,
    "litigation_adversary_threats":  litigation_adversary_threats,
    "litigation_filing_pipeline":    litigation_filing_pipeline,
    "litigation_dedup_status":       litigation_dedup_status,
    "litigation_dedup_duplicates":   litigation_dedup_duplicates,
    "litigation_drive_summary":      litigation_drive_summary,
    "litigation_drive_org_log":      litigation_drive_org_log,
    "litigation_query_benchmarks":   litigation_query_benchmarks,
    "litigation_agent_inventory":    litigation_agent_inventory,
}
