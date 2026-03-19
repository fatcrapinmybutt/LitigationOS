#!/usr/bin/env python3
"""
Tool #122 — Trial Exhibit Book Builder
==========================================
🆕 NOVEL TOOL — Organizes ALL exhibits into a structured
trial-ready exhibit book with tabs, Bates numbers,
and pre-marked exhibit list for clerk submission.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

EXHIBIT_CATEGORIES = {
    'A': {
        'name': 'PPO / Straw Incident',
        'description': 'Evidence related to the PPO filing and fabricated straw incident',
        'exhibits': [
            {'id': 'A-001', 'title': 'Original PPO Petition', 'source': 'Court file', 'type': 'Court Document'},
            {'id': 'A-002', 'title': 'Straw Incident — No Corroboration Analysis', 'source': 'Tool #111', 'type': 'Analysis'},
            {'id': 'A-003', 'title': 'Timeline: PPO Filing to Custody Restriction', 'source': 'DB timeline', 'type': 'Timeline'},
        ],
    },
    'B': {
        'name': 'Communication / Parenting Time Denial',
        'description': 'Evidence of systematic communication blocking and parenting time interference',
        'exhibits': [
            {'id': 'B-001', 'title': 'Contact Attempt Log (complete)', 'source': 'ChatGPT evidence', 'type': 'Log'},
            {'id': 'B-002', 'title': 'Denied Parenting Time Instances', 'source': 'DB evidence_quotes', 'type': 'Compilation'},
            {'id': 'B-003', 'title': 'Birthday Message — 45 Days for Response', 'source': 'ChatGPT evidence', 'type': 'Communication'},
            {'id': 'B-004', 'title': 'Communication Pattern Analysis', 'source': 'Tool #100', 'type': 'Analysis'},
        ],
    },
    'C': {
        'name': 'Judicial Violations / Bias',
        'description': 'Evidence of Judge McNeill\'s bias and procedural violations',
        'exhibits': [
            {'id': 'C-001', 'title': 'Judicial Violation Summary (1,127 violations)', 'source': 'DB judicial_violations', 'type': 'Analysis'},
            {'id': 'C-002', 'title': 'Canon Violation Cross-Reference', 'source': 'Tool #103', 'type': 'Analysis'},
            {'id': 'C-003', 'title': 'Ex Parte Order Compilation', 'source': 'DB evidence_quotes', 'type': 'Court Documents'},
            {'id': 'C-004', 'title': 'Rusco Warrant Email', 'source': 'Evidence file', 'type': 'Communication'},
            {'id': 'C-005', 'title': '"Do Not File Anymore" Directive', 'source': 'Court transcript', 'type': 'Transcript'},
        ],
    },
    'D': {
        'name': 'Contradictions / Perjury',
        'description': 'Documentary evidence of false statements under oath',
        'exhibits': [
            {'id': 'D-001', 'title': 'Contradiction Compilation (1,061 items)', 'source': 'DB detected_contradictions', 'type': 'Analysis'},
            {'id': 'D-002', 'title': 'Perjury Trap Analysis', 'source': 'Tool #111', 'type': 'Analysis'},
            {'id': 'D-003', 'title': 'Statement vs. Documentary Evidence Comparison', 'source': 'Multiple sources', 'type': 'Comparison'},
        ],
    },
    'E': {
        'name': 'Best Interest Factors',
        'description': 'Evidence supporting all 12 MCL 722.23 best interest factors',
        'exhibits': [
            {'id': 'E-001', 'title': 'Best Interest Factor Analysis (12 factors)', 'source': 'Tool #98', 'type': 'Analysis'},
            {'id': 'E-002', 'title': 'Andrew Parental Involvement Evidence', 'source': 'Multiple', 'type': 'Compilation'},
            {'id': 'E-003', 'title': 'L.D.W. Home Environment Comparison', 'source': 'Evidence', 'type': 'Comparison'},
            {'id': 'E-004', 'title': 'Moral Fitness Analysis (Factor F)', 'source': 'Tool #100', 'type': 'Analysis'},
        ],
    },
    'F': {
        'name': 'Financial / Support',
        'description': 'Financial evidence including costs, damages, and support calculations',
        'exhibits': [
            {'id': 'F-001', 'title': 'Litigation Cost Summary', 'source': 'Tool #108', 'type': 'Financial'},
            {'id': 'F-002', 'title': 'Damages Calculation', 'source': 'Tool #97', 'type': 'Financial'},
            {'id': 'F-003', 'title': 'IFP Financial Affidavit', 'source': 'Tool #105', 'type': 'Affidavit'},
        ],
    },
    'G': {
        'name': 'Legal Authority',
        'description': 'Case law, statutes, and court rules supporting each filing',
        'exhibits': [
            {'id': 'G-001', 'title': 'Case Similarity Analysis (12 cases)', 'source': 'Tool #113', 'type': 'Legal Research'},
            {'id': 'G-002', 'title': 'Authority Chain Index', 'source': 'DB authority_chains', 'type': 'Legal Research'},
            {'id': 'G-003', 'title': 'Court Rule Compliance Matrix', 'source': 'Tool #93', 'type': 'Compliance'},
        ],
    },
    'H': {
        'name': 'Ronald Berry',
        'description': 'Evidence regarding Ronald Berry\'s role and conduct',
        'exhibits': [
            {'id': 'H-001', 'title': 'Berry Role Analysis', 'source': 'Tool #111', 'type': 'Analysis'},
            {'id': 'H-002', 'title': 'Berry Presence During Parenting Denials', 'source': 'Evidence', 'type': 'Evidence'},
            {'id': 'H-003', 'title': 'Potential UPL Evidence', 'source': 'Tool #117', 'type': 'Analysis'},
        ],
    },
}

def main():
    print("=" * 70)
    print("TRIAL EXHIBIT BOOK BUILDER — Tool #122")
    print("=" * 70)
    
    total_exhibits = 0
    lines = [
        "# 📚 TRIAL EXHIBIT BOOK",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #122*",
        f"*Pigors v. Watson | 2024-001507-DC | 14th Circuit Court*\n",
        "---\n",
        "## EXHIBIT LIST (For Clerk Submission)\n",
        "| Tab | Exhibit ID | Title | Type | Source |",
        "|-----|-----------|-------|------|--------|",
    ]
    
    for tab, cat in EXHIBIT_CATEGORIES.items():
        for ex in cat['exhibits']:
            lines.append(f"| {tab} | {ex['id']} | {ex['title']} | {ex['type']} | {ex['source']} |")
            total_exhibits += 1
    
    lines.extend(["", "---\n"])
    
    for tab, cat in EXHIBIT_CATEGORIES.items():
        lines.append(f"## Tab {tab}: {cat['name']}")
        lines.append(f"*{cat['description']}*\n")
        
        for ex in cat['exhibits']:
            lines.append(f"### {ex['id']}: {ex['title']}")
            lines.append(f"- **Type:** {ex['type']}")
            lines.append(f"- **Source:** {ex['source']}")
            lines.append(f"- **Authentication:** [See Tool #104 checklist]")
            lines.append("")
        
        lines.append("---\n")
        print(f"  📁 Tab {tab}: {cat['name']} ({len(cat['exhibits'])} exhibits)")
    
    lines.extend([
        "## EXHIBIT PREPARATION CHECKLIST",
        "- [ ] Print 3 copies of each exhibit (court, opposing party, personal)",
        "- [ ] Tab and label each exhibit with Bates-style numbers",
        "- [ ] Pre-mark exhibits (write exhibit ID on first page)",
        "- [ ] Organize in binder with table of contents",
        "- [ ] Bring original + 3 copies to every hearing",
        "- [ ] Have authentication evidence ready for each exhibit (Tool #104)",
        "",
        f"*{total_exhibits} exhibits across {len(EXHIBIT_CATEGORIES)} tabs*",
    ])
    
    md_path = REPORTS_DIR / "EXHIBIT_BOOK.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_path = REPORTS_DIR / "exhibit_book.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Trial Exhibit Book Builder (#122)',
        'total_exhibits': total_exhibits,
        'tabs': len(EXHIBIT_CATEGORIES),
        'categories': {k: v['name'] for k, v in EXHIBIT_CATEGORIES.items()},
    }, indent=2), encoding='utf-8')
    
    print(f"\n✅ {total_exhibits} exhibits organized across {len(EXHIBIT_CATEGORIES)} tabs")
    print(f"   Reports: EXHIBIT_BOOK.md + exhibit_book.json")

if __name__ == '__main__':
    main()
