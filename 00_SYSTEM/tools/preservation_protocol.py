#!/usr/bin/env python3
"""
Tool #134 — Evidence Preservation Protocol
=================================================
🆕 NOVEL TOOL — Ensures ALL evidence is properly preserved
with chain of custody documentation for court admissibility.

Spoilation of evidence = sanctions. This tool prevents that.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

PRESERVATION_CATEGORIES = [
    {
        'category': 'Digital Communications',
        'items': [
            'Text messages (screenshots + carrier records)',
            'Emails (forwarded to permanent email + exported as EML)',
            'Social media posts (screenshots with URL + timestamp)',
            'ChatGPT conversations (exported JSON + screenshots)',
            'Voicemails (saved as audio files + transcribed)',
        ],
        'preservation_method': 'Multiple backups: local drive + cloud + USB + printed',
        'legal_note': 'MRE 901(b)(1) — testimony of witness with knowledge of authenticity',
    },
    {
        'category': 'Court Documents',
        'items': [
            'All filed motions and responses',
            'Court orders (signed originals)',
            'Hearing transcripts (order from court reporter)',
            'Docket sheets and register of actions',
            'Proof of service filings',
        ],
        'preservation_method': 'Official court copies + personal copies in organized binder',
        'legal_note': 'Self-authenticating under MRE 902(4) (certified copies)',
    },
    {
        'category': 'Financial Records',
        'items': [
            'Bank statements showing support payments',
            'Employment records and pay stubs',
            'Tax returns',
            'Receipts for child-related expenses',
            'Litigation cost receipts (Tool #108)',
        ],
        'preservation_method': 'Original + digital scan + organized by date',
        'legal_note': 'MRE 803(6) — business records exception to hearsay',
    },
    {
        'category': 'Photographs / Video',
        'items': [
            'Photos of L.D.W. with Andrew',
            'Photos of Andrew\'s home environment',
            'Any video evidence of interactions',
            'Screenshots of denied communications',
        ],
        'preservation_method': 'Original files with EXIF data intact + cloud backup',
        'legal_note': 'MRE 901(b)(1) + MRE 1001-1003 (original document rule)',
    },
    {
        'category': 'Third-Party Records',
        'items': [
            'Medical records for L.D.W.',
            'School/daycare records',
            'Police reports (if any)',
            'CPS records (if any)',
            'FOC reports and recommendations',
        ],
        'preservation_method': 'Subpoena originals + request certified copies',
        'legal_note': 'May need subpoena duces tecum (MC 11a) for third-party records',
    },
]

LITIGATION_HOLD = {
    'notice': 'All parties have an obligation to preserve relevant evidence once litigation is anticipated or filed.',
    'obligations': [
        'Do NOT delete any text messages, emails, or digital communications',
        'Do NOT alter any documents, photos, or recordings',
        'Do NOT discard any physical evidence (letters, notes, items)',
        'Do NOT clear browser history or social media posts',
        'Do NOT factory-reset phones or computers',
    ],
    'spoilation_consequences': [
        'Adverse inference instruction (jury told missing evidence was unfavorable)',
        'Sanctions (monetary penalties)',
        'Default judgment in extreme cases',
        'Criminal contempt',
    ],
}

def main():
    print("=" * 70)
    print("EVIDENCE PRESERVATION PROTOCOL — Tool #134")
    print("=" * 70)
    
    # Count evidence in DB
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    
    try:
        total_evidence = conn.execute(
            "SELECT (SELECT COUNT(*) FROM evidence_quotes) + (SELECT COUNT(*) FROM chatgpt_evidence)"
        ).fetchone()[0]
    except:
        total_evidence = 0
    conn.close()
    
    total_items = sum(len(c['items']) for c in PRESERVATION_CATEGORIES)
    
    lines = [
        "# 🔒 EVIDENCE PRESERVATION PROTOCOL",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #134*",
        f"*{total_evidence:,} evidence items in database — ALL must be preserved*\n",
        "---\n",
        "## ⚠️ LITIGATION HOLD NOTICE\n",
        f"**{LITIGATION_HOLD['notice']}**\n",
        "### YOU MUST NOT:",
    ]
    
    for o in LITIGATION_HOLD['obligations']:
        lines.append(f"- ❌ {o}")
    
    lines.extend(["\n### Consequences of Spoilation:"])
    for c in LITIGATION_HOLD['spoilation_consequences']:
        lines.append(f"- ⚠️ {c}")
    
    lines.extend(["", "---\n"])
    
    for cat in PRESERVATION_CATEGORIES:
        lines.append(f"## {cat['category']}\n")
        lines.append("**Items to Preserve:**")
        for item in cat['items']:
            lines.append(f"- ✅ {item}")
        lines.append(f"\n**Method:** {cat['preservation_method']}")
        lines.append(f"**Legal Basis:** {cat['legal_note']}\n")
        lines.append("---\n")
        print(f"  🔒 {cat['category']}: {len(cat['items'])} items")
    
    lines.extend([
        "## BACKUP STRATEGY (3-2-1 Rule)\n",
        "The 3-2-1 rule: 3 copies, on 2 different media, with 1 offsite.\n",
        "| Copy | Location | Medium |",
        "|------|----------|--------|",
        "| Primary | C:\\ drive (LitigationOS) | SSD |",
        "| Secondary | External drives (F:\\, G:\\, I:\\) | HDD |",
        "| Offsite | Cloud backup or USB in safe location | Cloud/USB |",
        "",
        f"*{total_items} items across {len(PRESERVATION_CATEGORIES)} categories · {total_evidence:,} DB records*",
    ])
    
    md_path = REPORTS_DIR / "PRESERVATION_PROTOCOL.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "preservation_protocol.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Evidence Preservation Protocol (#134)',
        'categories': len(PRESERVATION_CATEGORIES),
        'total_items': total_items,
        'db_evidence_count': total_evidence,
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total_items} items across {len(PRESERVATION_CATEGORIES)} categories")
    print(f"   {total_evidence:,} DB evidence records to preserve")
    print(f"   Reports: PRESERVATION_PROTOCOL.md + preservation_protocol.json")

if __name__ == '__main__':
    main()
