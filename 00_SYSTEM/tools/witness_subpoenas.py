#!/usr/bin/env python3
"""
Tool #121 — Witness Subpoena Generator
==========================================
🆕 NOVEL TOOL — Auto-generate subpoena lists with
justification for each witness, expected testimony,
and cross-examination preparation notes.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

WITNESSES = [
    {
        'name': 'Emily A. Watson',
        'role': 'Defendant / Respondent',
        'address': '2160 Garland Drive, Norton Shores, MI 49441',
        'subpoena_type': 'Testimony + Documents',
        'filings': ['F1', 'F2', 'F7'],
        'expected_testimony': [
            'PPO basis and straw incident details',
            'Communication denials and parenting time interference',
            'Relationship with Ronald Berry and his role in child care',
            'Financial disclosures and employment history',
        ],
        'documents_to_produce': [
            'All text messages with Andrew Pigors (2022-present)',
            'All communications with Ronald Berry regarding L.D.W.',
            'Employment records and pay stubs (2022-present)',
            'Medical records for L.D.W. (non-privileged)',
        ],
        'cross_exam_notes': 'See Perjury Trap Detector (Tool #111) — 5 traps ready',
    },
    {
        'name': 'Ronald T. Berry',
        'role': 'Third Party / Material Witness',
        'address': '[ANDREW_REQUIRED — need Berry residential address]',
        'subpoena_type': 'Testimony + Documents',
        'filings': ['F1', 'F2', 'F7'],
        'expected_testimony': [
            'Nature and extent of relationship with Emily Watson',
            'Role in daily care and decisions for L.D.W.',
            'Presence during parenting time denials',
            'Any legal advice given to Emily Watson',
        ],
        'documents_to_produce': [
            'All communications with Emily Watson re: L.D.W.',
            'Any documents related to L.D.W. care or custody',
            'Background check / criminal history (if relevant)',
        ],
        'cross_exam_notes': 'Challenge his role — is he making parenting decisions? Unauthorized practice of law?',
    },
    {
        'name': 'Pamela Rusco',
        'role': 'Judicial Secretary to Hon. McNeill',
        'address': '990 Terrace St, Muskegon, MI 49442 (c/o 14th Circuit Court)',
        'subpoena_type': 'Testimony + Documents',
        'filings': ['F3', 'F6'],
        'expected_testimony': [
            'Ex parte communications with Emily Watson or Barnes',
            'Scheduling practices and order-entry procedures',
            'The warrant email incident',
            'Any instructions from Judge McNeill regarding this case',
        ],
        'documents_to_produce': [
            'All emails related to Pigors v. Watson case',
            'Phone logs showing calls from parties or attorneys',
            'Calendar entries for ex parte hearings',
        ],
        'cross_exam_notes': 'Rusco warrant email is a smoking gun — establish chain of custody',
    },
    {
        'name': 'Jennifer Barnes',
        'role': 'Former Attorney for Defendant (P55406) — WITHDRAWN',
        'address': '880 Jefferson St Ste B, Muskegon, MI 49440',
        'subpoena_type': 'Testimony + Documents',
        'filings': ['F2', 'F10'],
        'expected_testimony': [
            'Basis for PPO filing and evidence reviewed',
            'Ex parte communications with court staff',
            'Knowledge of false statements in filings',
            'Reason for withdrawal from case',
        ],
        'documents_to_produce': [
            'Complete case file for Watson representation',
            'All communications with court staff',
            'Billing records showing work performed',
        ],
        'cross_exam_notes': '6 MRPC violations identified (Tool #117). Attorney-client privilege may limit some testimony.',
    },
    {
        'name': 'Law Enforcement Officer (PPO Service)',
        'role': 'Serving Officer',
        'address': '[ANDREW_REQUIRED — identify serving officer from PPO records]',
        'subpoena_type': 'Testimony',
        'filings': ['F1', 'F2'],
        'expected_testimony': [
            'Circumstances of PPO service',
            'Observations at time of service',
            'Any statements made by parties during service',
        ],
        'documents_to_produce': [],
        'cross_exam_notes': 'Establish that service was routine — no threat observed',
    },
    {
        'name': 'Medical Professional (L.D.W. Pediatrician)',
        'role': 'Expert / Fact Witness',
        'address': '[ANDREW_REQUIRED — identify L.D.W. pediatrician]',
        'subpoena_type': 'Testimony + Records',
        'filings': ['F7'],
        'expected_testimony': [
            'L.D.W. health and development status',
            'Any concerns about home environment',
            'Both parents involvement in medical care',
        ],
        'documents_to_produce': [
            'Complete medical records for L.D.W.',
            'Notes on parental involvement',
        ],
        'cross_exam_notes': 'Friendly witness — establish Andrew as involved parent',
    },
]

def main():
    print("=" * 70)
    print("WITNESS SUBPOENA GENERATOR — Tool #121")
    print("=" * 70)
    
    lines = [
        "# 📋 WITNESS SUBPOENA LIST",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #121*",
        f"*Pigors v. Watson | 2024-001507-DC*\n",
        "---\n",
        f"**Total Witnesses: {len(WITNESSES)}**",
        "**Form Required: MC 11 (Subpoena) / MC 11a (Subpoena Duces Tecum)**\n",
    ]
    
    placeholders = 0
    for i, w in enumerate(WITNESSES, 1):
        if '[ANDREW_REQUIRED' in w['address']:
            placeholders += 1
        
        lines.append(f"## Witness {i}: {w['name']}")
        lines.append(f"**Role:** {w['role']}")
        lines.append(f"**Address:** {w['address']}")
        lines.append(f"**Subpoena Type:** {w['subpoena_type']}")
        lines.append(f"**Relevant Filings:** {', '.join(w['filings'])}\n")
        
        lines.append("### Expected Testimony:")
        for t in w['expected_testimony']:
            lines.append(f"- {t}")
        
        if w['documents_to_produce']:
            lines.append("\n### Documents to Produce:")
            for d in w['documents_to_produce']:
                lines.append(f"- {d}")
        
        lines.append(f"\n### Cross-Exam Notes:")
        lines.append(f"{w['cross_exam_notes']}\n")
        lines.append("---\n")
        
        print(f"  👤 Witness {i}: {w['name'][:35]} ({w['subpoena_type']})")
    
    lines.extend([
        "## ⚠️ SUBPOENA PROCEDURE (Michigan)",
        "1. **Obtain blank MC 11 / MC 11a** from court clerk or michiganlegahelp.org",
        "2. **Fill in** witness name, address, court date, documents requested",
        "3. **File with clerk** — get case number stamped",
        "4. **Serve via** process server or sheriff (NOT by you personally)",
        "5. **Service deadline:** At least 2 full days before hearing (MCR 2.506)",
        "6. **Witness fees:** $12/day + $0.10/mile (MCL 600.2552) — pay on service",
        "7. **Keep proof of service** for court file\n",
        f"*{len(WITNESSES)} witnesses | {placeholders} addresses needed from Andrew*",
    ])
    
    md_path = REPORTS_DIR / "WITNESS_SUBPOENAS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "witness_subpoenas.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Witness Subpoena Generator (#121)',
        'total_witnesses': len(WITNESSES),
        'placeholders_needed': placeholders,
        'witnesses': [w['name'] for w in WITNESSES],
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {len(WITNESSES)} witnesses catalogued ({placeholders} addresses needed)")
    print(f"   Reports: WITNESS_SUBPOENAS.md + witness_subpoenas.json")

if __name__ == '__main__':
    main()
