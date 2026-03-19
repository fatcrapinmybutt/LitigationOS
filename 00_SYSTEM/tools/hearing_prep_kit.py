#!/usr/bin/env python3
"""
Tool #54 — Hearing Preparation Kit
====================================
Generates court hearing preparation materials for each filing:
- Opening statement outline
- Key evidence to present (with exhibit numbers)
- Anticipated opposing arguments + rebuttals
- Questions for cross-examination
- Legal standards the judge must apply
- Procedural checklist (what to bring, courtroom etiquette)

Critical for a pro se litigant who needs organized materials at hearings.
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
PKG_BASE = Path(r"C:\Users\andre\Desktop\LITIGATION_FILING_PACKAGE")

FILING_HEARING_DATA = {
    'F1': {
        'title': 'Emergency Motion — Parenting Time Restoration',
        'court': '14th Circuit Court, Family Division',
        'hearing_type': 'Emergency Motion Hearing',
        'legal_standards': [
            'MCL 722.27a(3) — Required findings for parenting time suspension',
            'MCL 722.27a(7) — Frequency of parenting time',
            'MCR 3.207(A) — Ex parte orders require specific danger finding',
            'Shade v Wright 291 Mich App 17 — Parenting time modification standard',
        ],
        'key_arguments': [
            'No required findings of harm under MCL 722.27a(3) were made',
            'Child has been denied contact with father for extended period',
            'No evidence of abuse, neglect, or danger to justify suspension',
            'Bond between father and child is being irreparably damaged',
        ],
        'anticipated_opposition': [
            ('Emily claims safety concerns', 'No CPS findings, no police reports substantiating claims. Request court review actual evidence, not allegations.'),
            ('Emily claims child is adjusted', 'Extended separation itself is harmful. Cite attachment theory and MCL 722.23(j) willingness to facilitate.'),
            ('Court defers to status quo', 'Status quo was created by ex parte order without proper findings — it cannot justify its own continuation.'),
        ],
    },
    'F3': {
        'title': 'Motion to Disqualify Judge McNeill',
        'court': '14th Circuit Court',
        'hearing_type': 'Disqualification Hearing (MCR 2.003)',
        'legal_standards': [
            'MCR 2.003(C)(1) — Actual bias or prejudice',
            'Crampton v Dept of State 395 Mich 347 — Objective bias test',
            'Armstrong v Ypsilanti Charter Twp 248 Mich App 573 — Pattern establishes bias',
            'Canon 2 — Appearance of impropriety',
            'Canon 3(A)(4) — Ex parte communications prohibited',
        ],
        'key_arguments': [
            'Pattern of adverse rulings without evidentiary basis',
            'Ex parte communications with opposing party/counsel',
            'Failure to make required statutory findings',
            'Reasonable person would question impartiality',
        ],
        'anticipated_opposition': [
            ('Adverse rulings alone insufficient', 'This is not about individual rulings — it is the pattern and the absence of findings supporting those rulings.'),
            ('Judicial secretary communications are routine', 'Substantive communications about case matters through non-judicial channels violate Canon 3(A)(4).'),
            ('Must show actual bias, not appearance', 'Crampton applies objective test: would reasonable person question impartiality? Pattern evidence satisfies this.'),
        ],
    },
    'F7': {
        'title': 'Motion to Modify Custody and Parenting Time',
        'court': '14th Circuit Court, Family Division',
        'hearing_type': 'Custody Modification Hearing',
        'legal_standards': [
            'MCL 722.23 — Best interest factors (a through l)',
            'MCR 3.210 — Change of circumstances / proper cause required',
            'Vodvarka v Grasmeyer 259 Mich App 499 — Proper cause/change standard',
            'MCL 722.27(1)(c) — Court shall not modify unless proper cause shown',
        ],
        'key_arguments': [
            'Proper cause: extended denial of parenting time without findings',
            'Change of circumstances: child growing up without father relationship',
            'Best interest factor (j): willingness to facilitate — Emily has obstructed',
            'Best interest factor (l): domestic violence — no substantiated findings against father',
        ],
        'anticipated_opposition': [
            ('No proper cause shown', 'Extended unilateral denial of court-ordered parenting time IS proper cause under Vodvarka.'),
            ('Child is thriving in current arrangement', 'Thriving does not mean the current arrangement serves best interests. Factor (j) cooperation weighs heavily.'),
            ('Safety concerns justify restrictions', 'Restrictions require findings under MCL 722.27a(3). No such findings were made.'),
        ],
    },
}

def get_top_evidence(conn, category, limit=5):
    """Get top evidence items for a category."""
    evidence = []
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
        text_col = next((c for c in cols if c in ('quote_text', 'text', 'quote', 'content')), cols[1] if len(cols) > 1 else None)
        source_col = next((c for c in cols if c in ('source', 'source_doc', 'document', 'file_name')), None)
        
        if text_col:
            q = f"SELECT {text_col}"
            if source_col:
                q += f", {source_col}"
            q += f" FROM evidence_quotes LIMIT {limit}"
            
            rows = conn.execute(q).fetchall()
            for r in rows:
                evidence.append({
                    'text': str(r[0])[:200],
                    'source': str(r[1]) if len(r) > 1 else 'DB record',
                })
    except:
        pass
    
    return evidence

def build_hearing_kit(fid, data, evidence):
    """Build a hearing preparation document."""
    lines = [
        f"# HEARING PREPARATION KIT — {fid}",
        f"## {data['title']}",
        f"*Court: {data['court']}*",
        f"*Hearing Type: {data['hearing_type']}*",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        "",
        "---",
        "",
        "## ⚖️ LEGAL STANDARDS (Judge Must Apply)",
        "",
    ]
    
    for i, std in enumerate(data['legal_standards'], 1):
        lines.append(f"{i}. **{std}**")
    
    lines.extend([
        "",
        "## 🎯 KEY ARGUMENTS (Your Presentation)",
        "",
    ])
    
    for i, arg in enumerate(data['key_arguments'], 1):
        lines.append(f"{i}. {arg}")
    
    lines.extend([
        "",
        "## 🛡️ ANTICIPATED OPPOSITION + REBUTTALS",
        "",
    ])
    
    for opp, rebuttal in data['anticipated_opposition']:
        lines.extend([
            f"### They say: *\"{opp}\"*",
            f"**Your response:** {rebuttal}",
            "",
        ])
    
    if evidence:
        lines.extend([
            "## 📋 KEY EVIDENCE TO PRESENT",
            "",
        ])
        for i, ev in enumerate(evidence[:10], 1):
            lines.append(f"{i}. **Exhibit {i}**: {ev['text'][:150]}...")
            lines.append(f"   *Source: {ev['source']}*")
            lines.append("")
    
    lines.extend([
        "## ✅ COURTROOM CHECKLIST",
        "",
        "### Before the Hearing",
        "- [ ] Copies of all filed documents (3 sets: judge, opposing party, yourself)",
        "- [ ] Exhibit binder with numbered tabs",
        "- [ ] Highlighted key authorities (cases, statutes, court rules)",
        "- [ ] This hearing prep kit",
        "- [ ] Notepad and pen for notes",
        "- [ ] Photo ID",
        "",
        "### Courtroom Protocol",
        "- Address judge as \"Your Honor\"",
        "- Stand when speaking",
        "- Do not interrupt — wait for your turn",
        "- Speak clearly and slowly",
        "- Refer to exhibits by number",
        "- If asked a question you don't know: \"I'd like to review the record, Your Honor\"",
        "- NEVER argue with the judge — note objection and move on",
        "",
        "### Opening Statement Template",
        f"\"Your Honor, my name is Andrew Pigors, and I am the Plaintiff appearing",
        f"pro se. This is a hearing on my {data['hearing_type'].lower()}.",
        f"The core issue is [STATE THE ISSUE IN ONE SENTENCE].",
        f"I will demonstrate through [NUMBER] exhibits that [KEY POINT].\"",
        "",
        "### Closing Argument Template",
        "\"Your Honor, the evidence presented today demonstrates that [SUMMARIZE].",
        "Under [CITE KEY STATUTE], the court is required to [STATE STANDARD].",
        "The evidence satisfies this standard because [EXPLAIN WHY].",
        "I respectfully request that the court [STATE SPECIFIC RELIEF].\"",
        "",
        "---",
        "*Review this kit 24 hours before your hearing. Mark key exhibits with sticky tabs.*",
    ])
    
    return '\n'.join(lines)

def main():
    print("=" * 70)
    print("HEARING PREPARATION KIT — Tool #54")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 70)
    
    conn = None
    try:
        conn = sqlite3.connect(str(DB_PATH), timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
    except Exception as e:
        print(f"⚠️ DB connection: {e}")
    
    evidence = []
    if conn:
        evidence = get_top_evidence(conn, 'general', 10)
        print(f"📋 Loaded {len(evidence)} evidence items")
    
    kits_built = 0
    
    for fid, data in FILING_HEARING_DATA.items():
        print(f"\n📝 Building kit for {fid}: {data['title']}")
        
        kit = build_hearing_kit(fid, data, evidence)
        
        # Save to package directory
        pkg_dirs = list(PKG_BASE.glob(f"PKG_{fid}_*"))
        if pkg_dirs:
            kit_path = pkg_dirs[0] / "08_HEARING_PREP_KIT.md"
            kit_path.write_text(kit, encoding='utf-8')
            print(f"  ✅ Saved to {kit_path.name}")
            kits_built += 1
        
        # Also save to reports
        report_path = REPORTS_DIR / f"HEARING_KIT_{fid}.md"
        report_path.write_text(kit, encoding='utf-8')
    
    if conn:
        conn.close()
    
    # Summary report
    json_path = REPORTS_DIR / "hearing_kits.json"
    json_path.write_text(json.dumps({
        'generated': datetime.now().isoformat(),
        'tool': 'Hearing Preparation Kit (#54)',
        'kits_built': kits_built,
        'filings_covered': list(FILING_HEARING_DATA.keys()),
        'evidence_items': len(evidence),
    }, indent=2, default=str), encoding='utf-8')
    
    print(f"\n✅ {kits_built} hearing prep kits built")
    print(f"📂 Saved to PKG directories as 08_HEARING_PREP_KIT.md")

if __name__ == '__main__':
    main()
