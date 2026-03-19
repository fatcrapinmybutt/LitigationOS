"""
filing_receipt_tracker.py — LitigationOS Engine
Tracks filing confirmations, receipts, and status across all courts/forums.
DB table: filing_receipts
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'litigation_context.db')

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS filing_receipts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filing_name TEXT NOT NULL,
    court TEXT,
    case_number TEXT,
    filed_date TEXT,
    confirmation_number TEXT,
    filed_by TEXT DEFAULT 'Andrew Pigors (Pro Se)',
    method TEXT CHECK(method IN ('efiling','mifile','in_person','mail','certified_mail')),
    fee_paid REAL DEFAULT 0.0,
    fee_waived INTEGER DEFAULT 0,
    receipt_path TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending','filed','rejected','accepted','processing')),
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


def _get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table():
    """Create filing_receipts table if it doesn't exist."""
    conn = _get_conn()
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()


def record_filing(filing_name: str, court: str = None, case_number: str = None,
                  filed_date: str = None, confirmation_number: str = None,
                  filed_by: str = 'Andrew Pigors (Pro Se)', method: str = None,
                  fee_paid: float = 0.0, fee_waived: bool = False,
                  receipt_path: str = None, status: str = 'pending',
                  notes: str = None) -> dict:
    """Record a new filing."""
    ensure_table()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO filing_receipts
        (filing_name, court, case_number, filed_date, confirmation_number,
         filed_by, method, fee_paid, fee_waived, receipt_path, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (filing_name, court, case_number,
          filed_date or datetime.now().strftime('%Y-%m-%d'),
          confirmation_number, filed_by, method,
          fee_paid, 1 if fee_waived else 0, receipt_path, status, notes))
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return {'id': row_id, 'filing_name': filing_name, 'status': status, 'recorded': True}


def get_pending_filings() -> list:
    """Get all filings with pending status."""
    ensure_table()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM filing_receipts WHERE status = 'pending' ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_filed_filings() -> list:
    """Get all filings that have been confirmed filed."""
    ensure_table()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM filing_receipts WHERE status IN ('filed','accepted') ORDER BY filed_date DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def generate_filing_status_report() -> dict:
    """Generate a comprehensive filing status report."""
    ensure_table()
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM filing_receipts")
    total = cur.fetchone()[0]

    cur.execute("SELECT status, COUNT(*) FROM filing_receipts GROUP BY status")
    by_status = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("SELECT court, COUNT(*) FROM filing_receipts GROUP BY court")
    by_court = {r[0]: r[1] for r in cur.fetchall()}

    cur.execute("SELECT SUM(fee_paid) FROM filing_receipts WHERE fee_waived = 0")
    total_fees = cur.fetchone()[0] or 0.0

    cur.execute("SELECT COUNT(*) FROM filing_receipts WHERE fee_waived = 1")
    waived_count = cur.fetchone()[0]

    cur.execute("SELECT * FROM filing_receipts ORDER BY created_at DESC LIMIT 10")
    recent = [dict(r) for r in cur.fetchall()]

    conn.close()

    return {
        'generated_at': datetime.now().isoformat(),
        'total_filings': total,
        'by_status': by_status,
        'by_court': by_court,
        'total_fees_paid': total_fees,
        'fee_waivers': waived_count,
        'recent_filings': recent,
    }


# JSON-RPC dispatch
def handle_rpc(method: str, params: dict = None) -> dict:
    """Handle JSON-RPC style calls."""
    params = params or {}
    if method == 'record_filing':
        return record_filing(**params)
    elif method == 'get_pending_filings':
        return get_pending_filings()
    elif method == 'get_filed_filings':
        return get_filed_filings()
    elif method == 'generate_filing_status_report':
        return generate_filing_status_report()
    else:
        return {'error': f'Unknown method: {method}'}


if __name__ == '__main__':
    import sys
    ensure_table()
    report = generate_filing_status_report()
    print(json.dumps(report, indent=2, default=str))
