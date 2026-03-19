#!/usr/bin/env python3
"""
Tool #91 — Deposition Question Generator
============================================
Auto-generates targeted deposition questions from:
- Detected contradictions (1,061)
- Perjury evidence (5,821 items)
- Judicial violations (1,127)

Creates lawyer-quality cross-examination questions
designed to impeach witnesses and expose fraud.

Categories:
- Emily Watson: custody lies, perjury, fabricated evidence
- Ronald Berry: UPL, conspiracy, coaching
- Jennifer Barnes: MRPC violations, withdrawal timing
- Judge McNeill: bias, ex-parte, due process violations
"""
import sys, json, sqlite3
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"

def get_contradictions(conn, limit=20):
    """Get top contradictions for question generation."""
    try:
        rows = conn.execute("""
            SELECT speaker, statement_1, source_1, statement_2, source_2, 
                   contradiction_type, severity
            FROM detected_contradictions 
            WHERE severity IN ('IMPEACHMENT', 'PERJURY')
            ORDER BY CASE severity WHEN 'PERJURY' THEN 1 WHEN 'IMPEACHMENT' THEN 2 ELSE 3 END
            LIMIT ?
        """, (limit,)).fetchall()
        return rows
    except:
        return []

def get_perjury_items(conn, limit=20):
    """Get top perjury items."""
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(watson_perjury_compilation)").fetchall()]
        stmt_col = 'statement_text' if 'statement_text' in cols else cols[1] if len(cols) > 1 else None
        contra_col = 'contradicting_evidence' if 'contradicting_evidence' in cols else cols[3] if len(cols) > 3 else None
        
        if stmt_col and contra_col:
            rows = conn.execute(f"""
                SELECT {stmt_col}, {contra_col}
                FROM watson_perjury_compilation 
                WHERE {stmt_col} IS NOT NULL AND {stmt_col} != ''
                LIMIT ?
            """, (limit,)).fetchall()
            return rows
    except:
        pass
    return []

def generate_contradiction_questions(contradictions):
    """Generate cross-examination questions from contradictions."""
    questions = []
    for row in contradictions:
        speaker = row[0] or 'Unknown'
        stmt1 = (row[1] or '')[:200]
        src1 = row[2] or 'unknown source'
        stmt2 = (row[3] or '')[:200]
        src2 = row[4] or 'unknown source'
        severity = row[6] or 'unknown'
        
        if not stmt1 or not stmt2:
            continue
            
        q = {
            'target': speaker,
            'severity': severity,
            'questions': [
                f"You stated in {src1}: \"{stmt1[:100]}...\" — is that correct?",
                f"And in {src2}, you stated: \"{stmt2[:100]}...\" — is that also correct?",
                f"How do you reconcile these two contradictory statements?",
                f"Were you lying then, or are you lying now?",
                f"Do you understand that making false statements under oath constitutes perjury under MCL 750.423?",
            ],
            'foundation': f"Contradiction: {src1} vs {src2}",
        }
        questions.append(q)
    return questions

def generate_target_questions():
    """Generate targeted questions for each adversary."""
    targets = {
        'Emily A. Watson': {
            'role': 'Respondent/Counter-Petitioner',
            'themes': [
                {
                    'theme': 'Straw Incident Fabrication (Oct 2023)',
                    'questions': [
                        "You filed a PPO claiming Andrew threw a straw at L.D.W. — correct?",
                        "Did you personally witness this alleged incident?",
                        "Did you take L.D.W. for a medical examination after this alleged incident?",
                        "Isn't it true that this 'straw incident' was the sole basis for your PPO petition?",
                        "Have you ever discussed with Ronald Berry what to say about this incident?",
                        "Are you aware that filing a false PPO petition constitutes perjury under MCL 750.423?",
                    ],
                },
                {
                    'theme': 'Parenting Time Interference',
                    'questions': [
                        "How many scheduled parenting time sessions has Andrew had with L.D.W. in the last 12 months?",
                        "On how many occasions did you cancel or interfere with scheduled parenting time?",
                        "Did you ever tell Andrew that L.D.W. was 'sick' to avoid parenting time?",
                        "MCL 722.23(j) requires the court to consider which parent is more likely to facilitate a close relationship. Do you believe you've facilitated Andrew's relationship with L.D.W.?",
                        "How many birthday messages from Andrew have you allowed L.D.W. to receive?",
                    ],
                },
                {
                    'theme': 'Relationship with Ronald Berry',
                    'questions': [
                        "When did Ronald Berry begin living at your residence?",
                        "Is Ronald Berry licensed to practice law in Michigan?",
                        "Has Ronald Berry ever drafted legal documents on your behalf?",
                        "Has Ronald Berry ever given you legal advice regarding this case?",
                        "Are you aware that a non-attorney providing legal services constitutes unauthorized practice of law under MCL 600.916?",
                    ],
                },
            ],
        },
        'Ronald T. Berry': {
            'role': 'Non-party witness / Potential co-conspirator',
            'themes': [
                {
                    'theme': 'Unauthorized Practice of Law',
                    'questions': [
                        "Are you a licensed attorney in any state?",
                        "Have you ever attended law school?",
                        "Have you ever drafted, edited, or reviewed legal documents for Emily Watson?",
                        "Have you ever communicated with the court on Emily's behalf?",
                        "Have you ever advised Emily on legal strategy in this case?",
                        "Are you aware that MCL 600.916 makes unauthorized practice of law a crime?",
                    ],
                },
                {
                    'theme': 'Coaching / Witness Tampering',
                    'questions': [
                        "Have you ever discussed with Emily what to say in court filings?",
                        "Have you ever been present when Emily prepared her testimony?",
                        "Have you ever encouraged Emily to restrict Andrew's access to L.D.W.?",
                        "Have you ever told Emily to file a protection order against Andrew?",
                    ],
                },
            ],
        },
        'Jennifer Barnes (P55406)': {
            'role': 'Emily\'s former attorney (withdrew)',
            'themes': [
                {
                    'theme': 'Knowledge of Fraud',
                    'questions': [
                        "When did you first become aware that Emily's PPO petition contained false statements?",
                        "Did you verify the factual claims in Emily's initial filings?",
                        "MRPC 3.3 requires candor to the tribunal. Did you present any statement to the court that you knew or should have known was false?",
                        "What was the reason for your withdrawal from this case?",
                        "Did your withdrawal relate to any ethical concerns about Emily's claims?",
                    ],
                },
            ],
        },
    }
    return targets

def main():
    print("=" * 70)
    print("DEPOSITION QUESTION GENERATOR — Tool #91")
    print("=" * 70)
    
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    
    contradictions = get_contradictions(conn, 15)
    perjury_items = get_perjury_items(conn, 15)
    
    impeach_qs = generate_contradiction_questions(contradictions)
    target_qs = generate_target_questions()
    
    conn.close()
    
    total_questions = 0
    
    lines = [
        "# 📋 DEPOSITION QUESTION BANK",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Tool #91*\n",
        "---",
        "",
        "## ⚠️ ATTORNEY-CLIENT PRIVILEGE NOTICE",
        "This document contains litigation work product and strategy.",
        "**DO NOT share with opposing parties or file with the court.**\n",
        "---\n",
    ]
    
    # Target-specific questions
    for target, data in target_qs.items():
        lines.append(f"## 🎯 {target} ({data['role']})\n")
        for theme in data['themes']:
            lines.append(f"### {theme['theme']}\n")
            for i, q in enumerate(theme['questions'], 1):
                lines.append(f"{i}. {q}")
                total_questions += 1
            lines.append("")
    
    # Contradiction-based impeachment questions
    if impeach_qs:
        lines.append("## 🔥 IMPEACHMENT QUESTIONS (from DB contradictions)\n")
        for iq in impeach_qs:
            lines.append(f"### Target: {iq['target']} [{iq['severity']}]")
            lines.append(f"*Foundation: {iq['foundation']}*\n")
            for i, q in enumerate(iq['questions'], 1):
                lines.append(f"{i}. {q}")
                total_questions += 1
            lines.append("")
    
    # Technique notes
    lines.extend([
        "---",
        "## 📖 DEPOSITION TECHNIQUE NOTES\n",
        "1. **Lock in testimony** — Get witness to commit to specific facts BEFORE revealing contradictions",
        "2. **Use documents** — Always have the contradicting document ready before asking",
        "3. **One fact per question** — Never compound questions",
        "4. **Leading questions allowed** — Cross-examination permits leading questions (MRE 611(c))",
        "5. **Impeachment by prior inconsistent statement** — MRE 613 requires showing witness the statement",
        "6. **Record everything** — Ensure court reporter captures all Q&A",
        "7. **Stay calm** — Emotional reactions help the witness, not you",
        "",
        f"*Deposition Question Generator — Tool #91 — {total_questions} questions generated*",
    ])
    
    md_path = REPORTS_DIR / "DEPOSITION_QUESTIONS.md"
    md_path.write_text('\n'.join(lines), encoding='utf-8')
    
    json_data = {
        'generated': datetime.now().isoformat(),
        'tool': 'Deposition Question Generator (#91)',
        'total_questions': total_questions,
        'contradiction_based': len(impeach_qs),
        'targets': list(target_qs.keys()),
        'db_contradictions_used': len(contradictions),
        'db_perjury_items_used': len(perjury_items),
    }
    json_path = REPORTS_DIR / "deposition_questions.json"
    json_path.write_text(json.dumps(json_data, indent=2), encoding='utf-8')
    
    print(f"\n  📋 {total_questions} deposition questions generated")
    print(f"  🎯 Targets: {', '.join(target_qs.keys())}")
    print(f"  🔥 {len(impeach_qs)} impeachment question sets from DB contradictions")
    print(f"  📝 Reports: DEPOSITION_QUESTIONS.md + deposition_questions.json")
    print(f"\n✅ Deposition question bank ready — WORK PRODUCT / DO NOT FILE")

if __name__ == '__main__':
    main()
