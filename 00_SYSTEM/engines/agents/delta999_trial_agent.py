#!/usr/bin/env python3
"""
Delta999 Trial Agent -- 14th Circuit motion specialist.

MCR 2.119 motion format validator, SCAO form selector (121 forms),
MiFILE submission requirements, caption/certificate/proof-of-service generator.

CLI:
    python delta999_trial_agent.py --action validate_motion --motion-type "summary disposition"
    python delta999_trial_agent.py --action select_scao_form --filing-type "motion to compel"
    python delta999_trial_agent.py --action generate_caption --case-no "24-001234-CZ"
    python delta999_trial_agent.py --action check_mifile --filing-type "brief in support"
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# -- paths -----------------------------------------------------------------
AGENT_DIR = Path(__file__).parent
ENGINE_DIR = AGENT_DIR.parent
sys.path.insert(0, str(ENGINE_DIR))

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'
AGENT_NAME = 'delta999_trial_agent'

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


# -- MCR 2.119 Motion Requirements ----------------------------------------

MCR_2119_REQUIREMENTS = {
    'general': {
        'rule': 'MCR 2.119(A)',
        'requirements': [
            'Written motion stating specific grounds and relief sought',
            'Brief or supporting authorities -- may be filed with motion or within 7 days',
            'Proposed order',
            'Proof of service on all parties',
        ],
    },
    'summary_disposition': {
        'rule': 'MCR 2.116(B)',
        'requirements': [
            'Motion must specify grounds under MCR 2.116(C)(1)-(10)',
            'Brief in support with applicable sub-rule',
            'Affidavits/evidence (if under (C)(10))',
            'Statement of material facts not in dispute',
            'Proposed order',
            'Proof of service -- at least 21 days before hearing',
        ],
    },
    'motion_to_compel': {
        'rule': 'MCR 2.313(A)',
        'requirements': [
            'Certification of good faith attempt to resolve without court action',
            'Statement of specific discovery sought',
            'Basis for compelling production',
            'Proposed order',
            'Proof of service',
        ],
    },
    'motion_for_sanctions': {
        'rule': 'MCR 2.114(E) / MCR 2.313(B)',
        'requirements': [
            'Specific conduct warranting sanctions',
            'Factual basis with evidence',
            'Requested sanction and authority',
            'Proposed order',
            'Proof of service',
        ],
    },
    'motion_to_dismiss': {
        'rule': 'MCR 2.116(C)(8)',
        'requirements': [
            'Specify ground(s) for dismissal',
            'Brief with authority',
            'For (C)(8): accept all well-pleaded facts as true',
            'Proposed order',
            'Proof of service',
        ],
    },
    'ex_parte_motion': {
        'rule': 'MCR 2.119(B)',
        'requirements': [
            'Verified statement of facts showing irreparable harm',
            'Specific facts showing notice is impractical',
            'Proposed ex parte order',
            'Bond (if applicable)',
            'Must be presented to judge directly',
        ],
    },
}

MIFILE_REQUIREMENTS = {
    'accepted_formats': ['PDF', 'PDF/A'],
    'max_file_size_mb': 25,
    'naming_convention': 'CaseNo_DocType_Date.pdf',
    'required_fields': [
        'Case Number', 'Court', 'Filing Party', 'Document Type',
        'Date of Filing',
    ],
    'e_signature': 'Typed /s/ Name permitted under MCR 2.114(C)',
    'service': 'MiFILE sends notification but does NOT constitute service under MCR 2.107',
    'fees': 'Payable via MiFILE e-payment',
    'rejected_reasons': [
        'Incorrect case number', 'Wrong court selected',
        'File exceeds 25 MB', 'Non-PDF format',
        'Missing required fields', 'Illegible scan',
    ],
}


# -- Core functions --------------------------------------------------------

def validate_motion(motion_type: str) -> dict:
    """Validate motion format against MCR 2.119 requirements."""
    conn = get_conn()

    # Normalize motion type
    key = motion_type.lower().replace(' ', '_').replace('-', '_')
    matched = MCR_2119_REQUIREMENTS.get(key, MCR_2119_REQUIREMENTS['general'])

    # Pull any existing motions from DB for context
    existing_motions = []
    try:
        rows = conn.execute(
            "SELECT * FROM apex_filing_stack_index WHERE filing_type LIKE ? LIMIT 10",
            (f'%{motion_type}%',)
        ).fetchall()
        existing_motions = [dict(r) for r in rows]
    except Exception:
        pass

    # Pull court rules from auth_rules
    rules = []
    for fts in ['auth_rules_fts', 'auth_passages_fts']:
        try:
            rows = conn.execute(
                f"SELECT * FROM [{fts}] WHERE [{fts}] MATCH ? ORDER BY rank LIMIT 10",
                (f'MCR 2.119 OR motion OR {motion_type}',)
            ).fetchall()
            rules.extend([dict(r) for r in rows])
        except Exception:
            pass

    conn.close()

    # LLM validation
    try:
        analysis = llm_ask(
            f"Validate the requirements for a '{motion_type}' motion in Michigan Circuit Court.\n\n"
            f"MCR 2.119 requirements for this type:\n{json.dumps(matched, default=str)}\n\n"
            f"Court rules found ({len(rules)}):\n{json.dumps(rules[:3], default=str)[:600]}\n\n"
            f"Provide a checklist of:\n"
            f"1. Required components\n"
            f"2. Timing/service requirements\n"
            f"3. Common deficiencies to avoid\n"
            f"4. Specific MCR citations",
            system_prompt=(
                "You are a Michigan court filing specialist. Rules:\n"
                "1. Cite MCR sections precisely (e.g., MCR 2.119(A)(1))\n"
                "2. Only cite rules present in the provided context — mark others UNVERIFIED\n"
                "3. Flag missing required components as DEFICIENCY\n"
                "4. Note service deadlines with MCR-specific time computations"
            )
        )
    except Exception as e:
        analysis = f"LLM unavailable: {e}"

    result = {
        'motion_type': motion_type,
        'matched_rule': matched['rule'],
        'requirements': matched['requirements'],
        'existing_filings': len(existing_motions),
        'authority_found': len(rules),
        'validation_analysis': analysis,
    }
    log_activity(f'validate_motion:{motion_type[:50]}', json.dumps(result, default=str)[:2000])
    return result


def select_scao_form(filing_type: str) -> dict:
    """Select the appropriate SCAO form from the 121-form catalog."""
    conn = get_conn()

    # Search scao_forms_catalog table
    forms = []
    try:
        rows = conn.execute(
            "SELECT * FROM scao_forms_catalog WHERE "
            "form_title LIKE ? OR form_number LIKE ? OR category LIKE ? "
            "ORDER BY form_number LIMIT 20",
            (f'%{filing_type}%', f'%{filing_type}%', f'%{filing_type}%')
        ).fetchall()
        forms = [dict(r) for r in rows]
    except Exception:
        pass

    # Fallback: FTS search if available
    if not forms:
        try:
            rows = conn.execute(
                "SELECT * FROM scao_forms_catalog_fts WHERE scao_forms_catalog_fts MATCH ? "
                "ORDER BY rank LIMIT 15",
                (filing_type,)
            ).fetchall()
            forms = [dict(r) for r in rows]
        except Exception:
            pass

    # Also check all forms for broader match
    all_count = 0
    try:
        all_count = conn.execute('SELECT COUNT(*) FROM scao_forms_catalog').fetchone()[0]
    except Exception:
        pass

    conn.close()

    # LLM form selection
    try:
        recommendation = llm_ask(
            f"Select the correct SCAO form for filing type: '{filing_type}'\n\n"
            f"Matching forms from catalog ({len(forms)}):\n"
            f"{json.dumps(forms[:10], default=str)[:1200]}\n\n"
            f"Total forms in catalog: {all_count}\n\n"
            f"Recommend the best form and explain why. Include form number and title.",
            system_prompt=(
                "You are a Michigan SCAO forms expert. Rules:\n"
                "1. Recommend the exact form number and title (e.g., CC 79, FOC 114, MC 01)\n"
                "2. Only recommend forms listed in the provided catalog — never guess form numbers\n"
                "3. If multiple forms are needed, list each with its purpose\n"
                "4. Note when a form requires supplemental attachments"
            )
        )
    except Exception as e:
        recommendation = f"LLM unavailable: {e}"

    result = {
        'filing_type': filing_type,
        'matching_forms': forms[:15],
        'total_catalog_forms': all_count,
        'recommendation': recommendation,
    }
    log_activity(f'select_scao:{filing_type[:50]}', json.dumps(result, default=str)[:2000])
    return result


def generate_caption(case_no: str) -> dict:
    """Generate proper court caption, certificate of service, and proof of service."""
    conn = get_conn()

    # Pull case info from DB
    case_info = {}
    try:
        for table in ['case_master', 'case_registry', 'apex_filing_stack_index']:
            rows = conn.execute(
                f"SELECT * FROM [{table}] WHERE case_number LIKE ? OR case_no LIKE ? LIMIT 5",
                (f'%{case_no}%', f'%{case_no}%')
            ).fetchall()
            if rows:
                case_info[table] = [dict(r) for r in rows]
    except Exception:
        pass

    # Pull parties from adversary tables
    parties = []
    try:
        for tbl in ['adversary_profile', 'adversary_assertions']:
            rows = conn.execute(f"SELECT DISTINCT * FROM [{tbl}] LIMIT 20").fetchall()
            parties.extend([dict(r) for r in rows])
    except Exception:
        pass

    conn.close()

    caption_template = (
        "STATE OF MICHIGAN\n"
        "IN THE CIRCUIT COURT FOR THE COUNTY OF MACOMB\n"
        "14TH JUDICIAL CIRCUIT\n"
        "-----------------------------------------------\n"
        "ANDRE WATSON,\n"
        "        Plaintiff,\n"
        f"                                Case No. {case_no}\n"
        "    v.\n"
        "                                Hon. [Judge Name]\n"
        "[DEFENDANT NAME(S)],\n"
        "        Defendant(s).\n"
        "-----------------------------------------------\n"
    )

    certificate_of_service = (
        "CERTIFICATE OF SERVICE\n\n"
        "I hereby certify that on [DATE], I served a copy of the foregoing\n"
        "[DOCUMENT TITLE] on all parties or their attorneys of record by:\n\n"
        "[ ] First-class mail, postage prepaid\n"
        "[ ] Personal delivery\n"
        "[ ] Electronic service via MiFILE\n"
        "[ ] Email (by agreement of parties)\n\n"
        "to the following:\n\n"
        "[PARTY/ATTORNEY NAME]\n"
        "[ADDRESS]\n\n"
        "Date: _______________\n"
        "Signature: /s/ Andre Watson\n"
        "Andre Watson, Pro Se Plaintiff\n"
    )

    proof_of_service = (
        "PROOF OF SERVICE (MCR 2.107)\n\n"
        "Case No.: {case_no}\n"
        "Document Served: [DOCUMENT TITLE]\n"
        "Date of Service: [DATE]\n"
        "Method of Service:\n"
        "  [ ] Personal service (MCR 2.105)\n"
        "  [ ] Mail service (MCR 2.107(C)(3))\n"
        "  [ ] Electronic service (MCR 2.107(C)(4))\n\n"
        "Person(s) Served:\n"
        "  Name: _______________\n"
        "  Address: _______________\n\n"
        "I declare under penalty of perjury that the above is true.\n\n"
        "Date: _______________\n"
        "Signature: /s/ Andre Watson\n"
    )

    result = {
        'case_no': case_no,
        'caption': caption_template,
        'certificate_of_service': certificate_of_service,
        'proof_of_service': proof_of_service,
        'case_info_found': {k: len(v) for k, v in case_info.items()} if case_info else {},
        'parties_found': len(parties),
    }
    log_activity(f'generate_caption:{case_no}', json.dumps(result, default=str)[:2000])
    return result


def check_mifile_reqs(filing_type: str) -> dict:
    """Check MiFILE electronic filing requirements."""
    conn = get_conn()

    # Check for filing-type-specific rules
    rules = []
    try:
        rows = conn.execute(
            "SELECT * FROM auth_rules_fts WHERE auth_rules_fts MATCH ? ORDER BY rank LIMIT 10",
            (f'electronic filing OR MiFILE OR {filing_type}',)
        ).fetchall()
        rules = [dict(r) for r in rows]
    except Exception:
        pass

    conn.close()

    mifile_checklist = {
        'filing_type': filing_type,
        'general_requirements': MIFILE_REQUIREMENTS,
        'pre_submission_checklist': [
            f'Document is in PDF format (PDF/A preferred)',
            f'File size under 25 MB per document',
            f'Case number is correct and matches court records',
            f'All required fields completed in MiFILE form',
            f'e-Signature: /s/ Andre Watson',
            f'Filing fee paid or fee waiver on file (MC 20)',
            f'Proof of service prepared (MiFILE notification != service)',
            f'Certificate of service attached or filed separately',
            f'Document naming follows convention: CaseNo_DocType_Date.pdf',
        ],
        'common_rejections': MIFILE_REQUIREMENTS['rejected_reasons'],
        'authority_found': len(rules),
    }

    log_activity(f'check_mifile:{filing_type[:50]}', json.dumps(mifile_checklist, default=str)[:2000])
    return mifile_checklist


# -- CLI -------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Delta999 Trial Agent -- 14th Circuit Motion Specialist')
    parser.add_argument('--action', required=True,
                        choices=['validate_motion', 'select_scao_form',
                                 'generate_caption', 'check_mifile'],
                        help='Action to perform')
    parser.add_argument('--motion-type', type=str, help='Motion type to validate')
    parser.add_argument('--filing-type', type=str, help='Filing type for SCAO/MiFILE lookup')
    parser.add_argument('--case-no', type=str, help='Case number for caption generation')
    args = parser.parse_args()

    if args.action == 'validate_motion':
        if not args.motion_type:
            parser.error('--motion-type required')
        result = validate_motion(args.motion_type)
    elif args.action == 'select_scao_form':
        if not args.filing_type:
            parser.error('--filing-type required')
        result = select_scao_form(args.filing_type)
    elif args.action == 'generate_caption':
        if not args.case_no:
            parser.error('--case-no required')
        result = generate_caption(args.case_no)
    elif args.action == 'check_mifile':
        if not args.filing_type:
            parser.error('--filing-type required')
        result = check_mifile_reqs(args.filing_type)
    else:
        parser.print_help()
        return

    print(json.dumps(result, indent=2, default=str))


if __name__ == '__main__':
    main()
