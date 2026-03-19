"""
LitigationOS Error Prevention Module
=====================================
Loaded by all scripts to prevent recurring issues.
Created: 2026-02-26
"""

import sys
import os
import sqlite3

# ── FIX: Python encoding (cp1252 crashes on Unicode) ──
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
os.environ['PYTHONIOENCODING'] = 'utf-8'

# ── FIX: Database connection helper with retry ──
DB_PATH = r"C:\Users\andre\litigation_context.db"

def get_db(path=None, retries=3):
    """Connect to litigation DB with auto-retry and WAL mode."""
    p = path or DB_PATH
    for attempt in range(retries):
        try:
            conn = sqlite3.connect(p, timeout=30)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            return conn
        except sqlite3.OperationalError as e:
            if attempt == retries - 1:
                raise
            import time
            time.sleep(2 ** attempt)
    return None

def safe_insert(conn, table, data_dict, on_conflict='IGNORE'):
    """Insert with automatic column matching and conflict handling."""
    cols = [c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    matched = {k: v for k, v in data_dict.items() if k in cols}
    if not matched:
        return False
    col_str = ', '.join(matched.keys())
    val_str = ', '.join(['?'] * len(matched))
    sql = f"INSERT OR {on_conflict} INTO {table} ({col_str}) VALUES ({val_str})"
    conn.execute(sql, list(matched.values()))
    return True

def log_error(conn, error_type, error_msg, context=''):
    """Log error to error_telemetry table."""
    try:
        conn.execute("""
            INSERT INTO error_telemetry (error_type, error_message, context, created_at)
            VALUES (?, ?, ?, datetime('now'))
        """, (error_type, str(error_msg)[:1000], context))
        conn.commit()
    except:
        pass  # Don't fail on logging failure

# ── FIX: Schema knowledge (prevents wrong column names) ──
SCHEMA_NOTES = {
    'chatgpt_conversations': {
        'role_column': 'message_role',  # NOT 'role'
        'time_column': 'created_at',    # NOT 'create_time'
    },
    'judicial_violations': {
        'pk': 'violation_id (TEXT, not autoincrement)',
        'severity_check': "IN ('low','medium','high','critical')",
    },
    'case_strength_scores': {
        'columns': 'id,lane,lane_name,authority_score,evidence_score,impeachment_score,timeline_score,total_score,grade,authority_count,evidence_count,impeachment_count,contradiction_count,timeline_count,testimony_count,filing_bundle_count,strengths,weaknesses,critical_gaps,next_action,scored_at',
        'no_compliance_score': True,  # compliance_score does NOT exist
    },
}

def get_columns(conn, table):
    """Get actual column names for a table."""
    return [c[1] for c in conn.execute(f"PRAGMA table_info({table})").fetchall()]

# ── FIX: Agent limitation awareness ──
AGENT_NOTES = {
    'explore': 'Can ONLY use glob, grep, view. CANNOT run Python/PowerShell.',
    'task': 'Can ONLY run commands. CANNOT access DB directly.',
    'general-purpose': 'Full capability but separate context.',
}
