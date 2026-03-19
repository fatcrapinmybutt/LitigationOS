#!/usr/bin/env python3
"""
Delta999 Discovery Agent -- Discovery request generator.

Interrogatories (MCR 2.309), document requests (MCR 2.310),
requests for admission (MCR 2.312), deposition notices (MCR 2.306).
Targeted per adversary per claim with DB-backed evidence.

CLI:
    python delta999_discovery_agent.py --action generate_interrogatories --adversary "FOC" --claim "custody interference"
    python delta999_discovery_agent.py --action generate_doc_requests --adversary "Macomb County" --claim "due process"
    python delta999_discovery_agent.py --action generate_admissions --adversary "FOC" --claim "ex parte orders"
    python delta999_discovery_agent.py --action generate_depo_notices --witness "FOC Caseworker"
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
AGENT_NAME = 'delta999_discovery_agent'

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


# -- Discovery Rule References ---------------------------------------------

DISCOVERY_RULES = {
    'interrogatories': {
        'rule': 'MCR 2.309',
        'limit': 'No more than 20 interrogatories (including subparts) without leave of court',
        'response_time': '28 days after service',
        'objections': 'Must state specific objection; blanket objections prohibited',
        'scao_form': 'CC 382a',
    },
    'document_requests': {
        'rule': 'MCR 2.310',
        'scope': 'Documents in the possession, custody, or control of the party',
        'response_time': '28 days after service',
        'format': 'Produce in form kept in usual course of business or organized by request',
        'scao_form': 'CC 383',
    },
    'admissions': {
        'rule': 'MCR 2.312',
        'effect': 'Deemed admitted if no response within 28 days',
        'response_time': '28 days -- CRITICAL: failure = automatic admission',
        'scope': 'Facts, application of law to fact, opinions, genuineness of documents',
        'scao_form': 'CC 384',
    },
    'depositions': {
        'rule': 'MCR 2.306',
        'notice': 'Reasonable notice (generally 7+ days)',
        'scope': 'Any person having knowledge of discoverable matter',
        'duration': '1 day of 7 hours unless otherwise agreed or ordered',
    },
}


# -- Helper: gather adversary evidence -------------------------------------

def _gather_adversary_data(adversary: str, claim: str = '') -> dict:
    """Gather all adversary-related evidence from DB."""
    conn = get_conn()
    data = {'assertions': [], 'evidence': [], 'harms': [], 'timeline': []}

    # Adversary assertions
    try:
        rows = conn.execute(
            "SELECT * FROM adversary_assertions_fts WHERE adversary_assertions_fts MATCH ? "
            "ORDER BY rank LIMIT 20",
            (adversary,)
        ).fetchall()
        data['assertions'] = [dict(r) for r in rows]
    except Exception:
        pass

    # Evidence quotes
    search_term = f"{adversary} {claim}" if claim else adversary
    try:
        rows = conn.execute(
            "SELECT * FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ? "
            "ORDER BY rank LIMIT 25",
            (search_term,)
        ).fetchall()
        data['evidence'] = [dict(r) for r in rows]
    except Exception:
        pass

    # Extracted harms
    try:
        rows = conn.execute(
            "SELECT * FROM extracted_harms_fts WHERE extracted_harms_fts MATCH ? "
            "ORDER BY rank LIMIT 15",
            (search_term,)
        ).fetchall()
        data['harms'] = [dict(r) for r in rows]
    except Exception:
        pass

    # Timeline events
    try:
        rows = conn.execute(
            "SELECT * FROM master_chronological_timeline WHERE "
            "description LIKE ? OR event_type LIKE ? LIMIT 20",
            (f'%{adversary}%', f'%{adversary}%')
        ).fetchall()
        data['timeline'] = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()
    return data


# -- Core functions --------------------------------------------------------

def generate_interrogatories(adversary: str, claim: str = '') -> dict:
    """Generate targeted interrogatories per MCR 2.309."""
    adv_data = _gather_adversary_data(adversary, claim)
    rule = DISCOVERY_RULES['interrogatories']

    # LLM-generated interrogatories
    try:
        interrogatories = llm_ask(
            f"Generate interrogatories (MCR 2.309) directed to: '{adversary}'\n"
            f"Regarding claim: '{claim or 'all claims'}'\n\n"
            f"Adversary assertions ({len(adv_data['assertions'])}):\n"
            f"{json.dumps(adv_data['assertions'][:5], default=str)[:600]}\n\n"
            f"Evidence against them ({len(adv_data['evidence'])}):\n"
            f"{json.dumps(adv_data['evidence'][:5], default=str)[:600]}\n\n"
            f"Documented harms ({len(adv_data['harms'])}):\n"
            f"{json.dumps(adv_data['harms'][:3], default=str)[:400]}\n\n"
            f"Rules:\n"
            f"- Maximum 20 interrogatories including subparts\n"
            f"- Must be relevant, proportional, and specific\n"
            f"- Include definition/instruction section\n"
            f"- Each interrogatory must target a specific factual issue\n\n"
            f"Generate 15-20 interrogatories that:\n"
            f"1. Pin down adversary's factual claims\n"
            f"2. Expose inconsistencies\n"
            f"3. Establish timeline of conduct\n"
            f"4. Identify other witnesses/documents\n"
            f"5. Lay foundation for admissions",
            system_prompt=(
                "You are a Michigan litigation discovery specialist. "
                "Draft interrogatories under MCR 2.309 in proper format. "
                "Number each interrogatory. Be specific and tactical."
            )
        )
    except Exception as e:
        interrogatories = f"LLM unavailable: {e}"

    result = {
        'adversary': adversary,
        'claim': claim or 'all claims',
        'rule': rule,
        'evidence_basis': {
            'assertions': len(adv_data['assertions']),
            'evidence_quotes': len(adv_data['evidence']),
            'harms': len(adv_data['harms']),
        },
        'interrogatories': interrogatories,
    }
    log_activity(f'interrogatories:{adversary[:30]}', json.dumps(result, default=str)[:2000])
    return result


def generate_doc_requests(adversary: str, claim: str = '') -> dict:
    """Generate document requests per MCR 2.310."""
    adv_data = _gather_adversary_data(adversary, claim)
    rule = DISCOVERY_RULES['document_requests']

    try:
        doc_requests = llm_ask(
            f"Generate document requests (MCR 2.310) directed to: '{adversary}'\n"
            f"Regarding claim: '{claim or 'all claims'}'\n\n"
            f"Known evidence ({len(adv_data['evidence'])}):\n"
            f"{json.dumps(adv_data['evidence'][:5], default=str)[:600]}\n\n"
            f"Timeline events ({len(adv_data['timeline'])}):\n"
            f"{json.dumps(adv_data['timeline'][:5], default=str)[:600]}\n\n"
            f"Generate comprehensive document requests that seek:\n"
            f"1. All communications regarding plaintiff\n"
            f"2. All internal memoranda, emails, reports\n"
            f"3. All records of ex parte communications\n"
            f"4. All policies and procedures relevant to the claim\n"
            f"5. All documents supporting adversary's assertions\n"
            f"6. Training records and qualification documents\n"
            f"7. Any documents referenced in adversary's filings\n"
            f"8. Electronic records including metadata",
            system_prompt=(
                "You are a Michigan litigation discovery specialist. "
                "Draft document requests under MCR 2.310 in proper format. "
                "Number each request. Include definitions section."
            )
        )
    except Exception as e:
        doc_requests = f"LLM unavailable: {e}"

    result = {
        'adversary': adversary,
        'claim': claim or 'all claims',
        'rule': rule,
        'document_requests': doc_requests,
    }
    log_activity(f'doc_requests:{adversary[:30]}', json.dumps(result, default=str)[:2000])
    return result


def generate_admissions(adversary: str, claim: str = '') -> dict:
    """Generate requests for admission per MCR 2.312."""
    adv_data = _gather_adversary_data(adversary, claim)
    rule = DISCOVERY_RULES['admissions']

    try:
        admissions = llm_ask(
            f"Generate requests for admission (MCR 2.312) directed to: '{adversary}'\n"
            f"Regarding claim: '{claim or 'all claims'}'\n\n"
            f"Adversary assertions to pin down ({len(adv_data['assertions'])}):\n"
            f"{json.dumps(adv_data['assertions'][:5], default=str)[:600]}\n\n"
            f"Evidence supporting our position ({len(adv_data['evidence'])}):\n"
            f"{json.dumps(adv_data['evidence'][:5], default=str)[:600]}\n\n"
            f"CRITICAL: Under MCR 2.312, failure to respond within 28 days = automatic admission.\n\n"
            f"Generate requests that:\n"
            f"1. Establish undeniable facts (dates, events, actions)\n"
            f"2. Pin down authenticity of key documents\n"
            f"3. Admit specific conduct (ex parte contacts, denial of notice)\n"
            f"4. Admit application of law to fact\n"
            f"5. Eliminate factual disputes for summary disposition\n"
            f"6. Force adversary into contradictions with other evidence",
            system_prompt=(
                "You are a Michigan litigation discovery specialist. "
                "Draft requests for admission under MCR 2.312. "
                "Each admission should be a simple, declarative statement. "
                "The adversary must admit or deny each one specifically."
            )
        )
    except Exception as e:
        admissions = f"LLM unavailable: {e}"

    result = {
        'adversary': adversary,
        'claim': claim or 'all claims',
        'rule': rule,
        'admissions': admissions,
        'warning': 'Failure to respond within 28 days --> matters deemed ADMITTED',
    }
    log_activity(f'admissions:{adversary[:30]}', json.dumps(result, default=str)[:2000])
    return result


def generate_depo_notices(witness: str, case_number: str = '') -> dict:
    """Generate deposition notice per MCR 2.306."""
    conn = get_conn()
    rule = DISCOVERY_RULES['depositions']

    # Gather info about witness
    witness_data = []
    for fts in ['adversary_assertions_fts', 'evidence_quotes_fts', 'extracted_harms_fts']:
        try:
            rows = conn.execute(
                f"SELECT * FROM [{fts}] WHERE [{fts}] MATCH ? ORDER BY rank LIMIT 10",
                (witness,)
            ).fetchall()
            witness_data.extend([dict(r) for r in rows])
        except Exception:
            pass

    conn.close()

    depo_date = (date.today() + timedelta(days=21)).isoformat()

    notice_text = (
        f"STATE OF MICHIGAN\n"
        f"IN THE CIRCUIT COURT FOR THE COUNTY OF MACOMB\n"
        f"14TH JUDICIAL CIRCUIT\n"
        f"{'=' * 50}\n\n"
        f"NOTICE OF TAKING DEPOSITION\n"
        f"(MCR 2.306)\n\n"
        f"Case No.: {case_number or '[CASE NUMBER]'}\n\n"
        f"TO: {witness}\n"
        f"    [ADDRESS]\n\n"
        f"PLEASE TAKE NOTICE that Plaintiff Andre Watson will take the\n"
        f"deposition of {witness} upon oral examination, pursuant to\n"
        f"MCR 2.306, at the following time and place:\n\n"
        f"    Date: {depo_date}\n"
        f"    Time: 10:00 AM\n"
        f"    Location: [LOCATION]\n\n"
        f"The deposition will be recorded by stenographic means and may\n"
        f"also be recorded by audio/video.\n\n"
        f"The deposition shall not exceed one day of seven hours,\n"
        f"pursuant to MCR 2.306(A)(2).\n\n"
        f"Date: {date.today().isoformat()}\n\n"
        f"Respectfully submitted,\n"
        f"/s/ Andre Watson\n"
        f"Andre Watson, Pro Se Plaintiff\n"
    )

    # LLM deposition topics
    try:
        topics = llm_ask(
            f"Generate deposition topics/outline for witness: '{witness}'\n\n"
            f"Evidence related to this witness ({len(witness_data)}):\n"
            f"{json.dumps(witness_data[:5], default=str)[:800]}\n\n"
            f"Create a deposition outline covering:\n"
            f"1. Background and qualifications\n"
            f"2. Role in events at issue\n"
            f"3. Key factual areas to probe\n"
            f"4. Areas of potential impeachment\n"
            f"5. Documents to confront witness with",
            system_prompt=(
                "You are a Michigan deposition specialist. "
                "Create a tactical deposition outline. "
                "Focus on areas where the witness is most vulnerable."
            )
        )
    except Exception as e:
        topics = f"LLM unavailable: {e}"

    result = {
        'witness': witness,
        'rule': rule,
        'notice': notice_text,
        'deposition_topics': topics,
        'witness_data_found': len(witness_data),
    }
    log_activity(f'depo_notice:{witness[:30]}', json.dumps(result, default=str)[:2000])
    return result


# -- CLI -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Delta999 Discovery Agent -- Discovery Request Generator')
    parser.add_argument('--action', required=True,
                        choices=['generate_interrogatories', 'generate_doc_requests',
                                 'generate_admissions', 'generate_depo_notices'],
                        help='Action to perform')
    parser.add_argument('--adversary', type=str, help='Target adversary')
    parser.add_argument('--claim', type=str, default='', help='Specific claim')
    parser.add_argument('--witness', type=str, help='Deposition witness')
    parser.add_argument('--case-number', type=str, default='', help='Case number')
    args = parser.parse_args()

    if args.action == 'generate_interrogatories':
        if not args.adversary:
            parser.error('--adversary required')
        result = generate_interrogatories(args.adversary, args.claim)
    elif args.action == 'generate_doc_requests':
        if not args.adversary:
            parser.error('--adversary required')
        result = generate_doc_requests(args.adversary, args.claim)
    elif args.action == 'generate_admissions':
        if not args.adversary:
            parser.error('--adversary required')
        result = generate_admissions(args.adversary, args.claim)
    elif args.action == 'generate_depo_notices':
        if not args.witness:
            parser.error('--witness required')
        result = generate_depo_notices(args.witness, args.case_number)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
