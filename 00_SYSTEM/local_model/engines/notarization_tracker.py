"""
notarization_tracker.py — LitigationOS Engine
Tracks which documents require notarization for Michigan court filings.
- Affidavits: ALL require notarization
- Verified statements: signature under penalty of perjury (MCR 2.114)
- Fee waiver affidavits: require notarization
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'litigation_context.db')

NOTARIZATION_RULES = {
    'affidavit': {
        'requires_notarization': True,
        'authority': 'MCL 600.2922; MCR 2.119(B)',
        'description': 'All affidavits must be notarized with jurat',
    },
    'verified_statement': {
        'requires_notarization': False,
        'requires_verification': True,
        'authority': 'MCR 2.114(A)',
        'description': 'Signed under penalty of perjury — no notary needed but must contain verification language',
    },
    'fee_waiver_affidavit': {
        'requires_notarization': True,
        'authority': 'MCR 2.002; MCL 600.2963',
        'description': 'Fee waiver affidavit must be notarized',
    },
    'motion': {
        'requires_notarization': False,
        'authority': 'MCR 2.119',
        'description': 'Motions require signature but not notarization',
    },
    'brief': {
        'requires_notarization': False,
        'authority': 'MCR 7.212',
        'description': 'Briefs require signature block only',
    },
    'proof_of_service': {
        'requires_notarization': False,
        'requires_verification': True,
        'authority': 'MCR 2.104',
        'description': 'Proof of service signed under oath or verified',
    },
    'complaint': {
        'requires_notarization': False,
        'requires_verification': True,
        'authority': 'MCR 2.114',
        'description': 'Complaints must be verified if containing factual allegations',
    },
    'msc_complaint': {
        'requires_notarization': True,
        'authority': 'MCR 7.306(B)',
        'description': 'MSC original complaint for superintending control — verification/notarization required',
    },
    'jtc_complaint': {
        'requires_notarization': True,
        'authority': 'MCR 9.220',
        'description': 'JTC formal complaint requires notarized affidavit of facts',
    },
}

# Document types that absolutely require notarization
NOTARIZATION_REQUIRED = [k for k, v in NOTARIZATION_RULES.items() if v.get('requires_notarization')]
VERIFICATION_REQUIRED = [k for k, v in NOTARIZATION_RULES.items() if v.get('requires_verification')]


def _get_conn():
    return sqlite3.connect(DB_PATH, timeout=30)


def check_notarization_required(doc_type: str) -> dict:
    """Check if a document type requires notarization."""
    doc_type = doc_type.lower().replace(' ', '_').replace('-', '_')
    if doc_type in NOTARIZATION_RULES:
        return NOTARIZATION_RULES[doc_type]
    return {
        'requires_notarization': False,
        'authority': 'N/A',
        'description': f'Unknown document type: {doc_type}. Check MCR/MCL for requirements.',
    }


def list_unnotarized() -> list:
    """List filing package documents that need notarization but haven't been notarized."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT filing_name, forum, status
            FROM filing_readiness
            WHERE LOWER(filing_name) LIKE '%affidavit%'
               OR LOWER(filing_name) LIKE '%jtc%complaint%'
               OR LOWER(filing_name) LIKE '%msc%complaint%'
               OR LOWER(filing_name) LIKE '%fee waiver%'
        """)
        rows = cur.fetchall()
        results = []
        for row in rows:
            results.append({
                'filing_name': row[0],
                'forum': row[1],
                'status': row[2],
                'notarization_status': 'NEEDED — NOT YET NOTARIZED',
            })
        return results
    except Exception as e:
        return [{'error': str(e)}]
    finally:
        conn.close()


def generate_notarization_checklist() -> dict:
    """Generate a full notarization checklist for all pending filings."""
    checklist = {
        'generated_at': datetime.now().isoformat(),
        'notarization_required_types': NOTARIZATION_REQUIRED,
        'verification_required_types': VERIFICATION_REQUIRED,
        'rules': NOTARIZATION_RULES,
        'action_items': [
            'Locate nearest notary (UPS Store, bank, courthouse)',
            'Bring valid government-issued photo ID',
            'Do NOT sign until in front of notary',
            'Notary completes jurat (signed and sworn before me...)',
            'Get notary seal/stamp on each document',
            'Make copies of notarized originals before filing',
        ],
        'michigan_notes': [
            'MCL 55.285 — notary must verify identity',
            'Remote notarization allowed under MCL 55.286c (COVID extension)',
            'Notary fee max $10 per act per MCL 55.285',
        ],
    }
    unnotarized = list_unnotarized()
    checklist['unnotarized_filings'] = unnotarized
    checklist['total_needing_notarization'] = len(unnotarized)
    return checklist


# JSON-RPC dispatch
def handle_rpc(method: str, params: dict = None) -> dict:
    """Handle JSON-RPC style calls."""
    params = params or {}
    if method == 'check_notarization_required':
        return check_notarization_required(params.get('doc_type', ''))
    elif method == 'list_unnotarized':
        return list_unnotarized()
    elif method == 'generate_notarization_checklist':
        return generate_notarization_checklist()
    else:
        return {'error': f'Unknown method: {method}'}


if __name__ == '__main__':
    import sys
    checklist = generate_notarization_checklist()
    print(json.dumps(checklist, indent=2, default=str))
