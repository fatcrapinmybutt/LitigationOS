#!/usr/bin/env python3
"""
Delta999 Service Agent -- MCR 2.105/2.107 service calculator.

Auto-calculates service deadlines for each filing type.
Generates proof of service documents and service tracking log.
Handles: personal, mail, electronic, substitute service methods.

CLI:
    python delta999_service_agent.py --action calculate_deadline --filing-type "motion" --service-method "mail"
    python delta999_service_agent.py --action generate_proof --filing-type "motion" --served-party "FOC"
    python delta999_service_agent.py --action track_service
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path

# -- paths -----------------------------------------------------------------
AGENT_DIR = Path(__file__).parent
ENGINE_DIR = AGENT_DIR.parent
sys.path.insert(0, str(ENGINE_DIR))

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'
AGENT_NAME = 'delta999_service_agent'

from llm_bridge import llm_ask, llm_analyze_legal


# -- DB helpers ------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB, timeout=120)
    conn.execute('PRAGMA busy_timeout=60000')
    conn.execute('PRAGMA journal_mode=WAL')
    conn.row_factory = sqlite3.Row
    return conn


def log_activity(action, result):
    try:
        conn = get_conn()
        conn.execute(
            'INSERT INTO agent_activity_log (agent_name, action, result) VALUES (?,?,?)',
            (AGENT_NAME, action, str(result)[:2000])
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def _init_service_table():
    """Create service_tracking table if it does not exist."""
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS service_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filing_type TEXT NOT NULL,
        document_title TEXT,
        served_party TEXT,
        service_method TEXT,
        service_date TEXT,
        deadline_date TEXT,
        status TEXT DEFAULT 'pending',
        proof_generated INTEGER DEFAULT 0,
        case_number TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    );
    """)
    conn.commit()
    conn.close()


# -- Service Rules ---------------------------------------------------------

SERVICE_METHODS = {
    'personal': {
        'rule': 'MCR 2.105(A)',
        'description': 'Personal service on the individual',
        'add_days': 0,
        'requirements': [
            'Delivered to the party personally',
            'Server must be 18+ and not a party',
            'Proof of service filed with court',
        ],
    },
    'mail': {
        'rule': 'MCR 2.107(C)(3)',
        'description': 'First-class mail, postage prepaid',
        'add_days': 3,
        'requirements': [
            'Sent to last known address',
            'First-class mail with postage prepaid',
            'Add 3 days to response deadline for mailing',
            'Certificate of mailing required',
        ],
    },
    'electronic': {
        'rule': 'MCR 2.107(C)(4)',
        'description': 'Electronic service (email or e-filing system)',
        'add_days': 1,
        'requirements': [
            'Parties must consent to electronic service',
            'Email to address designated for service',
            'MiFILE notification alone is NOT service',
            'Add 1 day to response deadline',
        ],
    },
    'substitute': {
        'rule': 'MCR 2.105(A)(2)',
        'description': 'Service at dwelling with person of suitable age',
        'add_days': 0,
        'requirements': [
            'Left at dwelling house with person of suitable age and discretion',
            'Person must reside at the dwelling',
            'Copy also mailed to last known address',
        ],
    },
}

FILING_DEADLINES = {
    'motion': {
        'notice_days': 9,
        'rule': 'MCR 2.119(C)(1)',
        'note': '9 days before hearing (+ mail days)',
    },
    'response_to_motion': {
        'notice_days': 7,
        'rule': 'MCR 2.119(C)(2)',
        'note': '7 days before hearing (or as ordered)',
    },
    'reply_brief': {
        'notice_days': 3,
        'rule': 'MCR 2.119(C)(2)',
        'note': '3 days before hearing',
    },
    'answer_to_complaint': {
        'notice_days': 21,
        'rule': 'MCR 2.108(A)(1)',
        'note': '21 days after service of summons and complaint',
    },
    'summary_disposition': {
        'notice_days': 21,
        'rule': 'MCR 2.116(B)(1)',
        'note': '21 days before hearing',
    },
    'discovery_response': {
        'notice_days': 28,
        'rule': 'MCR 2.309(B)',
        'note': '28 days after service of interrogatories',
    },
    'request_for_admissions': {
        'notice_days': 28,
        'rule': 'MCR 2.312(B)',
        'note': '28 days -- deemed admitted if no response',
    },
    'appeal_claim': {
        'notice_days': 21,
        'rule': 'MCR 7.204(A)',
        'note': '21 days from entry of order (Court of Appeals)',
    },
    'appeal_application': {
        'notice_days': 21,
        'rule': 'MCR 7.205(A)',
        'note': '21 days from entry of order (leave to appeal)',
    },
}


# -- Core functions --------------------------------------------------------

def calculate_deadline(filing_type: str, service_method: str = 'mail',
                       filing_date: str = '') -> dict:
    """Calculate service and response deadlines."""
    if not filing_date:
        filing_date = date.today().isoformat()

    try:
        base_date = datetime.strptime(filing_date, '%Y-%m-%d').date()
    except ValueError:
        return {'error': f'Invalid date format: {filing_date}. Use YYYY-MM-DD.'}

    method_info = SERVICE_METHODS.get(service_method, SERVICE_METHODS['mail'])
    filing_info = FILING_DEADLINES.get(
        filing_type.lower().replace(' ', '_').replace('-', '_'),
        {'notice_days': 9, 'rule': 'MCR 2.119(C)(1)', 'note': 'Default motion timeline'}
    )

    # Calculate deadline
    base_days = filing_info['notice_days']
    mail_add = method_info['add_days']
    total_days = base_days + mail_add
    deadline = base_date + timedelta(days=total_days)

    # Adjust for weekends
    while deadline.weekday() >= 5:
        deadline += timedelta(days=1)

    result = {
        'filing_type': filing_type,
        'service_method': service_method,
        'filing_date': filing_date,
        'base_notice_days': base_days,
        'mail_add_days': mail_add,
        'total_days': total_days,
        'deadline_date': deadline.isoformat(),
        'deadline_day': deadline.strftime('%A'),
        'service_rule': method_info['rule'],
        'filing_rule': filing_info['rule'],
        'note': filing_info['note'],
        'service_requirements': method_info['requirements'],
    }
    log_activity(f'deadline:{filing_type}', json.dumps(result, default=str)[:2000])
    return result


def generate_proof(filing_type: str, served_party: str,
                   service_method: str = 'mail', document_title: str = '',
                   case_number: str = '') -> dict:
    """Generate proof of service document."""
    _init_service_table()
    method_info = SERVICE_METHODS.get(service_method, SERVICE_METHODS['mail'])
    today = date.today().isoformat()

    if not document_title:
        document_title = filing_type.title()

    proof_text = (
        f"STATE OF MICHIGAN\n"
        f"IN THE CIRCUIT COURT FOR THE COUNTY OF MACOMB\n"
        f"14TH JUDICIAL CIRCUIT\n"
        f"{'=' * 50}\n\n"
        f"PROOF OF SERVICE\n\n"
        f"Case No.: {case_number or '[CASE NUMBER]'}\n\n"
        f"I, Andre Watson, certify that on {today}, I served a true copy of:\n\n"
        f"    {document_title}\n\n"
        f"upon the following party/parties:\n\n"
        f"    {served_party}\n"
        f"    [ADDRESS]\n\n"
        f"Method of Service: {method_info['description']}\n"
        f"Rule: {method_info['rule']}\n\n"
    )

    if service_method == 'mail':
        proof_text += (
            f"Service was made by depositing a true copy in a sealed envelope\n"
            f"with first-class postage prepaid, in the United States mail,\n"
            f"addressed to the party at their last known address.\n\n"
        )
    elif service_method == 'personal':
        proof_text += (
            f"Service was made by delivering a true copy directly to the\n"
            f"above-named party.\n\n"
        )
    elif service_method == 'electronic':
        proof_text += (
            f"Service was made by electronic transmission to the party's\n"
            f"designated email address, with the party's prior consent.\n\n"
        )

    proof_text += (
        f"I declare under the penalty of perjury that the foregoing is true\n"
        f"and correct.\n\n"
        f"Date: {today}\n\n"
        f"Signature: /s/ Andre Watson\n"
        f"Andre Watson, Pro Se Plaintiff\n"
    )

    # Log to service_tracking table
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO service_tracking "
            "(filing_type, document_title, served_party, service_method, "
            "service_date, status, proof_generated, case_number) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (filing_type, document_title, served_party, service_method,
             today, 'served', 1, case_number)
        )
        conn.commit()
    except Exception:
        pass
    conn.close()

    result = {
        'filing_type': filing_type,
        'served_party': served_party,
        'service_method': service_method,
        'service_date': today,
        'proof_of_service': proof_text,
        'requirements_met': method_info['requirements'],
    }
    log_activity(f'generate_proof:{served_party[:30]}', json.dumps(result, default=str)[:2000])
    return result


def track_service() -> dict:
    """Get full service tracking log."""
    _init_service_table()
    conn = get_conn()

    records = []
    try:
        rows = conn.execute(
            "SELECT * FROM service_tracking ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
        records = [dict(r) for r in rows]
    except Exception:
        pass

    # Pending items (no proof generated)
    pending = [r for r in records if not r.get('proof_generated')]

    # Upcoming deadlines from litigation_deadlines
    deadlines = []
    try:
        rows = conn.execute(
            "SELECT * FROM litigation_deadlines WHERE status IN ('upcoming','overdue') "
            "ORDER BY due_date LIMIT 20"
        ).fetchall()
        deadlines = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    result = {
        'total_tracked': len(records),
        'pending_service': len(pending),
        'recent_records': records[:20],
        'pending_items': pending[:10],
        'upcoming_deadlines': deadlines[:10],
    }
    log_activity('track_service', json.dumps(result, default=str)[:2000])
    return result


# -- CLI -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Delta999 Service Agent -- MCR 2.105/2.107 Service Calculator')
    parser.add_argument('--action', required=True,
                        choices=['calculate_deadline', 'generate_proof', 'track_service'],
                        help='Action to perform')
    parser.add_argument('--filing-type', type=str, help='Filing type')
    parser.add_argument('--service-method', type=str, default='mail',
                        choices=['personal', 'mail', 'electronic', 'substitute'],
                        help='Service method')
    parser.add_argument('--served-party', type=str, help='Party being served')
    parser.add_argument('--filing-date', type=str, default='', help='Filing date (YYYY-MM-DD)')
    parser.add_argument('--document-title', type=str, default='', help='Document title')
    parser.add_argument('--case-number', type=str, default='', help='Case number')
    args = parser.parse_args()

    if args.action == 'calculate_deadline':
        if not args.filing_type:
            parser.error('--filing-type required')
        result = calculate_deadline(args.filing_type, args.service_method, args.filing_date)
    elif args.action == 'generate_proof':
        if not args.filing_type or not args.served_party:
            parser.error('--filing-type and --served-party required')
        result = generate_proof(
            args.filing_type, args.served_party, args.service_method,
            args.document_title, args.case_number
        )
    elif args.action == 'track_service':
        result = track_service()
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
