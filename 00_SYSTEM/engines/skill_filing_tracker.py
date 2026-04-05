#!/usr/bin/env python3
"""
skill_filing_tracker.py -- Filing Status Tracker

Tracks all filings across all courts. Status: drafted, reviewed, filed,
served, response_received. Deadline calculator per filing.
Court-specific filing requirements.
"""
import sys, sqlite3, json
from datetime import datetime, date, timedelta
from pathlib import Path
try:
    sys.stdout.reconfigure(encoding='utf-8')
except (AttributeError, OSError):
    pass

DB = str(Path(__file__).resolve().parents[2] / "litigation_context.db")

def _connect():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn

def _init_table():
    """Create filing_tracker table if it doesn't exist."""
    conn = _connect()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS filing_tracker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filing_title TEXT NOT NULL,
        filing_type TEXT,
        court TEXT,
        case_number TEXT,
        status TEXT DEFAULT 'drafted' CHECK(status IN ('drafted','reviewed','filed','served','response_received','closed')),
        filed_date TEXT,
        service_date TEXT,
        response_deadline TEXT,
        response_received_date TEXT,
        scao_form TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()

# -- Court-specific requirements -------------------------------------------

COURT_REQUIREMENTS = {
    'macomb_circuit': {
        'court_name': 'Macomb County Circuit Court -- 16th Judicial Circuit',
        'efiling': 'MiFILE required',
        'format': 'PDF, max 25MB, double-spaced body text',
        'cover_sheet': 'Required for new cases',
        'filing_fee': 'Per MCL 600.2529 schedule (or MC 20 fee waiver)',
        'local_rules': 'Macomb County Local Administrative Order',
    },
    '14th_circuit': {
        'court_name': '14th Judicial Circuit',
        'efiling': 'MiFILE required',
        'format': 'PDF, standard margins, 12pt font',
        'filing_fee': 'Per fee schedule',
    },
    'michigan_coa': {
        'court_name': 'Michigan Court of Appeals',
        'efiling': 'TrueFiling system',
        'format': 'MCR 7.212 format requirements',
        'page_limits': 'Brief: 50 pages; Reply: 25 pages',
        'appendix': 'Required -- lower court record excerpts',
        'filing_fee': '$375 or fee waiver',
    },
    'federal_ed_mi': {
        'court_name': 'US District Court, Eastern District of Michigan',
        'efiling': 'CM/ECF',
        'format': 'Local Rule 5.1 formatting',
        'brief_limits': '25 pages for motions; 35 pages for dispositive motions',
    },
}

RESPONSE_DEADLINES = {
    'motion': 7,
    'complaint': 21,
    'summary_disposition': 21,
    'discovery': 28,
    'admissions': 28,
    'appeal': 21,
    'show_cause': 14,
    'default': 14,
}


def get_filing_status(filing_id: int = None) -> dict:
    """Get status of a specific filing or all filings."""
    _init_table()
    conn = _connect()

    if filing_id:
        rows = conn.execute(
            "SELECT * FROM filing_tracker WHERE id = ?", (filing_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM filing_tracker ORDER BY created_at DESC LIMIT 50"
        ).fetchall()

    filings = [dict(r) for r in rows]

    # Also pull from apex_filing_stack_index for comprehensive view
    stack_filings = []
    try:
        stack_rows = conn.execute(
            "SELECT * FROM apex_filing_stack_index ORDER BY rowid DESC LIMIT 30"
        ).fetchall()
        stack_filings = [dict(r) for r in stack_rows]
    except Exception:
        pass

    conn.close()

    return {
        'tracked_filings': len(filings),
        'filings': filings,
        'stack_filings': len(stack_filings),
        'stack_preview': stack_filings[:10],
        'status_summary': {
            status: len([f for f in filings if f.get('status') == status])
            for status in ['drafted', 'reviewed', 'filed', 'served', 'response_received', 'closed']
        },
    }


def update_status(filing_id: int, new_status: str, notes: str = '') -> dict:
    """Update status of a filing."""
    _init_table()
    conn = _connect()

    valid_statuses = ['drafted', 'reviewed', 'filed', 'served', 'response_received', 'closed']
    if new_status not in valid_statuses:
        return {'error': f'Invalid status. Must be one of: {valid_statuses}'}

    updates = {"status": new_status, "updated_at": datetime.now().isoformat()}
    if new_status == 'filed':
        updates['filed_date'] = date.today().isoformat()
    elif new_status == 'served':
        updates['service_date'] = date.today().isoformat()
    elif new_status == 'response_received':
        updates['response_received_date'] = date.today().isoformat()

    set_clause = ', '.join(f"{k} = ?" for k in updates)
    params = list(updates.values()) + [filing_id]

    try:
        conn.execute(f"UPDATE filing_tracker SET {set_clause} WHERE id = ?", params)
        if notes:
            conn.execute(
                "UPDATE filing_tracker SET notes = COALESCE(notes, '') || ? WHERE id = ?",
                (f'\n[{datetime.now().isoformat()}] {notes}', filing_id)
            )
        conn.commit()
    except Exception as e:
        conn.close()
        return {'error': str(e)}

    # Fetch updated record
    row = conn.execute("SELECT * FROM filing_tracker WHERE id = ?", (filing_id,)).fetchone()
    conn.close()

    return {
        'filing_id': filing_id,
        'new_status': new_status,
        'updated': dict(row) if row else {},
    }


def next_deadlines(days_ahead: int = 30) -> dict:
    """Get all upcoming deadlines within specified days."""
    _init_table()
    conn = _connect()
    today = date.today()
    cutoff = (today + timedelta(days=days_ahead)).isoformat()

    # From filing_tracker
    tracker_deadlines = []
    try:
        rows = conn.execute(
            "SELECT * FROM filing_tracker WHERE response_deadline IS NOT NULL "
            "AND response_deadline <= ? AND status NOT IN ('response_received','closed') "
            "ORDER BY response_deadline",
            (cutoff,)
        ).fetchall()
        tracker_deadlines = [dict(r) for r in rows]
    except Exception:
        pass

    # From litigation_deadlines
    lit_deadlines = []
    try:
        rows = conn.execute(
            "SELECT * FROM litigation_deadlines WHERE due_date IS NOT NULL "
            "AND due_date <= ? AND status IN ('upcoming','overdue') "
            "ORDER BY due_date",
            (cutoff,)
        ).fetchall()
        lit_deadlines = [dict(r) for r in rows]
    except Exception:
        pass

    # Combine and sort
    all_deadlines = []
    for td in tracker_deadlines:
        all_deadlines.append({
            'source': 'filing_tracker',
            'title': td.get('filing_title', ''),
            'deadline': td.get('response_deadline', ''),
            'status': td.get('status', ''),
            'court': td.get('court', ''),
        })
    for ld in lit_deadlines:
        all_deadlines.append({
            'source': 'litigation_deadlines',
            'title': ld.get('filing_type', ld.get('case_name', '')),
            'deadline': ld.get('due_date', ''),
            'status': ld.get('status', ''),
            'priority': ld.get('priority', ''),
        })

    all_deadlines.sort(key=lambda d: d.get('deadline', '9999'))

    # Flag overdue
    for dl in all_deadlines:
        try:
            dl_date = datetime.strptime(dl['deadline'][:10], '%Y-%m-%d').date()
            dl['days_remaining'] = (dl_date - today).days
            dl['overdue'] = dl['days_remaining'] < 0
        except (ValueError, TypeError):
            dl['days_remaining'] = None
            dl['overdue'] = False

    conn.close()

    return {
        'as_of': today.isoformat(),
        'days_ahead': days_ahead,
        'total_deadlines': len(all_deadlines),
        'overdue': len([d for d in all_deadlines if d.get('overdue')]),
        'deadlines': all_deadlines[:30],
        'court_requirements': COURT_REQUIREMENTS,
    }


# -- CLI -------------------------------------------------------------------

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Filing Status Tracker')
    parser.add_argument('--action', default='status',
                        choices=['status', 'update', 'deadlines'])
    parser.add_argument('--filing-id', type=int, help='Filing ID')
    parser.add_argument('--new-status', type=str, help='New status')
    parser.add_argument('--notes', type=str, default='', help='Notes')
    parser.add_argument('--days', type=int, default=30, help='Days ahead for deadlines')
    args = parser.parse_args()

    if args.action == 'status':
        result = get_filing_status(args.filing_id)
    elif args.action == 'update':
        if not args.filing_id or not args.new_status:
            parser.error('--filing-id and --new-status required')
        result = update_status(args.filing_id, args.new_status, args.notes)
    else:
        result = next_deadlines(args.days)

    print(json.dumps(result, indent=2, default=str))
