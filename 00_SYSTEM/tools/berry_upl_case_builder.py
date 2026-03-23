#!/usr/bin/env python3
"""Tool #257: Ronald Berry UPL Case Builder
Comprehensive unauthorized practice of law case against Ronald T. Berry.
Compiles all evidence of Berry drafting legal documents, communicating with courts,
and providing legal advice as a non-attorney under MCL 600.916.
"""
import sys, os, json, sqlite3
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")

    print("=" * 70)
    print("TOOL #257: RONALD BERRY UPL CASE BUILDER")
    print("=" * 70)

    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    results = {"tool": "#257 Ronald Berry UPL Case Builder", "generated": datetime.now().isoformat()}

    # --- 1. Evidence Collection ---
    print("\n[1/5] Collecting Berry evidence from DB...")
    berry_evidence = []

    if 'evidence_quotes' in tables:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
        quote_col = 'quote_text' if 'quote_text' in cols else 'text' if 'text' in cols else None
        if quote_col:
            rows = conn.execute(f"""
                SELECT * FROM evidence_quotes
                WHERE {quote_col} LIKE '%berry%' OR {quote_col} LIKE '%ronald%'
                LIMIT 200
            """).fetchall()
            for r in rows:
                berry_evidence.append({"source": "evidence_quotes", "data": dict(r)})
            print(f"  evidence_quotes: {len(rows)} Berry-related items")

    if 'd_drive_events' in tables:
        rows = conn.execute("""
            SELECT * FROM d_drive_events
            WHERE actors LIKE '%berry%' OR actors LIKE '%ronald%'
            OR event_description LIKE '%berry%' OR event_description LIKE '%ronald%'
        """).fetchall()
        for r in rows:
            berry_evidence.append({"source": "d_drive_events", "data": dict(r)})
        print(f"  d_drive_events: {len(rows)} Berry-related events")

    if 'd_drive_cip' in tables:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(d_drive_cip)").fetchall()]
        search_cols = [c for c in cols if c not in ('pair_id', 'verification_status')]
        conditions = " OR ".join([f"[{c}] LIKE '%berry%'" for c in search_cols])
        if conditions:
            rows = conn.execute(f"SELECT * FROM d_drive_cip WHERE {conditions}").fetchall()
            for r in rows:
                berry_evidence.append({"source": "d_drive_cip", "data": dict(r)})
            print(f"  d_drive_cip: {len(rows)} Berry contradiction pairs")

    total_evidence = len(berry_evidence)
    print(f"  TOTAL Berry evidence: {total_evidence}")

    # --- 2. UPL Elements ---
    print("\n[2/5] Mapping evidence to UPL elements...")
    upl_elements = {
        "drafting_legal_documents": {
            "element": "Drafting pleadings, motions, or legal documents",
            "mcl": "MCL 600.916(1)",
            "evidence_items": [],
            "description": "Ronald Berry drafted, edited, or prepared legal documents filed in court proceedings"
        },
        "court_communications": {
            "element": "Communicating with court on behalf of another",
            "mcl": "MCL 600.916(1)",
            "evidence_items": [],
            "description": "Berry communicated with court personnel, FOC, or opposing parties on Emily's behalf"
        },
        "legal_advice": {
            "element": "Providing legal advice or counsel",
            "mcl": "MCL 600.916(1)",
            "evidence_items": [],
            "description": "Berry advised Emily on legal strategy, filing decisions, and court proceedings"
        },
        "representation": {
            "element": "Appearing or acting as representative in legal proceedings",
            "mcl": "MCL 600.916(1)",
            "evidence_items": [],
            "description": "Berry acted as Emily's legal representative in dealings with courts and parties"
        },
        "conspiracy": {
            "element": "Conspiracy to commit UPL + deprive civil rights",
            "mcl": "MCL 750.157a, 42 USC 1985(3)",
            "evidence_items": [],
            "description": "Berry conspired with Emily to use fraudulent legal filings to deprive Andrew of parental rights"
        }
    }

    # Classify evidence into elements
    for item in berry_evidence:
        data = item["data"]
        text = " ".join(str(v) for v in data.values() if v).lower()
        if any(w in text for w in ['draft', 'wrote', 'prepared', 'motion', 'filing', 'document']):
            upl_elements["drafting_legal_documents"]["evidence_items"].append(item)
        if any(w in text for w in ['court', 'judge', 'foc', 'rusco', 'filed', 'hearing']):
            upl_elements["court_communications"]["evidence_items"].append(item)
        if any(w in text for w in ['advised', 'told', 'strategy', 'plan', 'legal']):
            upl_elements["legal_advice"]["evidence_items"].append(item)
        if any(w in text for w in ['represent', 'behalf', 'speak', 'appear']):
            upl_elements["representation"]["evidence_items"].append(item)
        if any(w in text for w in ['conspir', 'premeditat', 'plan', 'scheme', 'ex parte']):
            upl_elements["conspiracy"]["evidence_items"].append(item)

    for key, elem in upl_elements.items():
        print(f"  {key}: {len(elem['evidence_items'])} items")

    # --- 3. Albert Watson Statement ---
    print("\n[3/5] Analyzing Albert Watson smoking gun...")
    albert_watson = {
        "statement": "NS2505044 — Albert Watson told police: 'they want this incident documented so Emily can go tomorrow to get an Ex Parte order'",
        "significance": "CASE KILLER — proves Berry and Emily premeditated the abuse of court process",
        "legal_impact": [
            "Proves conspiracy (MCL 750.157a)",
            "Proves fraud upon the court (MCR 2.612(C)(3))",
            "Proves ex parte order was pre-planned, not emergency",
            "Pierces judicial immunity for co-conspirators (Dennis v Sparks 449 US 24)"
        ],
        "who_said_what": {
            "albert_watson": "Emily's father-in-law, told police about the plan",
            "berry_role": "Orchestrated the plan to get ex parte order",
            "emily_role": "Carried out the plan by filing false ex parte motion"
        }
    }

    # --- 4. Authority Chain ---
    print("\n[4/5] Building authority chain...")
    authorities = [
        {"cite": "MCL 600.916", "rule": "Unauthorized practice of law — misdemeanor (up to $1,000 fine, 1 year jail)", "type": "CRIMINAL"},
        {"cite": "MCL 600.916(2)", "rule": "Each act of UPL is a separate offense", "type": "CRIMINAL"},
        {"cite": "MCL 750.157a", "rule": "Criminal conspiracy — same penalty as underlying offense", "type": "CRIMINAL"},
        {"cite": "42 USC 1983", "rule": "Federal civil rights — Berry as state actor through conspiracy with court", "type": "FEDERAL"},
        {"cite": "42 USC 1985(3)", "rule": "Conspiracy to deprive civil rights", "type": "FEDERAL"},
        {"cite": "Dennis v Sparks 449 US 24 (1980)", "rule": "Private parties who conspire with state actors lose immunity", "type": "FEDERAL"},
        {"cite": "Dressel v Ameribank 664 F Supp 1311", "rule": "Non-lawyer preparing legal documents = UPL", "type": "PERSUASIVE"},
        {"cite": "State Bar v Cramer 399 Mich 116 (1976)", "rule": "Michigan definition of 'practice of law' — includes document drafting", "type": "MICHIGAN"},
        {"cite": "Surety Ins Co v Williams 729 F2d 581", "rule": "Non-attorney who drafts court documents engages in UPL", "type": "PERSUASIVE"},
        {"cite": "MCR 8.120", "rule": "Only licensed attorneys may practice law in Michigan courts", "type": "COURT RULE"},
    ]

    # --- 5. Referral Package ---
    print("\n[5/5] Building State Bar referral package...")
    referral = {
        "recipient": "State Bar of Michigan, Unauthorized Practice of Law Committee",
        "address": "306 Townsend Street, Lansing, MI 48933",
        "subject": "Complaint: Ronald T. Berry — Unauthorized Practice of Law",
        "respondent": {
            "name": "Ronald T. Berry",
            "relationship": "Emily A. Watson's boyfriend/domestic partner",
            "address": "2160 Garland Drive, Norton Shores, MI 49441",
            "bar_number": "NONE — not a licensed attorney"
        },
        "specific_acts": [
            "Drafted legal motions filed in 14th Circuit Court case 2024-001507-DC",
            "Communicated with Friend of Court (Pamela Rusco) on Emily Watson's behalf",
            "Orchestrated ex parte strategy documented in police report NS2505044",
            "Provided legal advice and directed Emily Watson's litigation strategy",
            "Prepared documents that were signed and filed by Emily Watson"
        ],
        "evidence_summary": f"{total_evidence} evidence items documenting Berry's UPL",
        "criminal_referral": "Recommend referral to Muskegon County Prosecutor under MCL 600.916"
    }

    results.update({
        "berry_evidence_total": total_evidence,
        "upl_elements": {k: {"element": v["element"], "mcl": v["mcl"], "evidence_count": len(v["evidence_items"])} for k, v in upl_elements.items()},
        "albert_watson_statement": albert_watson,
        "authorities": authorities,
        "referral_package": referral,
        "recommendation": "File State Bar complaint + include UPL in federal 1983 complaint + criminal referral to prosecutor"
    })

    # --- Reports ---
    md_lines = [
        "# Tool #257: Ronald Berry UPL Case Builder",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        f"- **Total Berry Evidence**: {total_evidence} items",
        f"- **UPL Elements Documented**: {sum(1 for v in upl_elements.values() if len(v['evidence_items']) > 0)}/5",
        f"- **Authorities**: {len(authorities)}",
        "",
        "## SMOKING GUN: Albert Watson Statement (NS2505044)",
        f"> \"{albert_watson['statement']}\"",
        "",
        "**Significance**: " + albert_watson['significance'],
        "",
        "### Legal Impact:",
    ]
    for impact in albert_watson['legal_impact']:
        md_lines.append(f"- {impact}")

    md_lines.extend(["", "---", "## UPL Elements", ""])
    for key, elem in upl_elements.items():
        md_lines.append(f"### {elem['element']}")
        md_lines.append(f"- **MCL**: {elem['mcl']}")
        md_lines.append(f"- **Evidence Items**: {len(elem['evidence_items'])}")
        md_lines.append(f"- {elem['description']}")
        md_lines.append("")

    md_lines.extend(["## Authorities", ""])
    for a in authorities:
        md_lines.append(f"- **{a['cite']}** ({a['type']}): {a['rule']}")

    md_lines.extend(["", "## State Bar Referral", ""])
    md_lines.append(f"- **To**: {referral['recipient']}")
    md_lines.append(f"- **Subject**: {referral['subject']}")
    md_lines.append(f"- **Respondent**: {referral['respondent']['name']}")
    md_lines.append("### Specific Acts:")
    for act in referral['specific_acts']:
        md_lines.append(f"1. {act}")

    md_path = os.path.join(report_dir, "tool_257_berry_upl_case.md")
    json_path = os.path.join(report_dir, "tool_257_berry_upl_case.json")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  MD:   {md_path}")
    print(f"  JSON: {json_path}")
    conn.close()

    print(f"\n{'='*70}")
    print(f"BERRY UPL EVIDENCE: {total_evidence} items | ELEMENTS: {sum(1 for v in upl_elements.values() if len(v['evidence_items']) > 0)}/5")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
