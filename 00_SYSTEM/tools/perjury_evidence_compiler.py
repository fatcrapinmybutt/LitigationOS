#!/usr/bin/env python3
"""Tool #192 — Perjury Evidence Compiler.
Systematically identifies and catalogs Emily Watson's false sworn statements
with impeachment-ready evidence packages."""

import json, os, sys, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_perjury_compiler():
    compiler = {
        "tool_id": 192,
        "title": "PERJURY EVIDENCE COMPILER",
        "subtitle": "Emily Watson's False Sworn Statements — Impeachment Ready",
        "legal_standard": {
            "statute": "MCL 750.423 — Perjury",
            "elements": [
                "Oath or affirmation administered",
                "Statement was material to the matter",
                "Statement was false",
                "Defendant knew it was false when made",
            ],
            "penalty": "Felony — up to 15 years imprisonment",
            "civil_use": "MCR 2.612(C)(1)(c) — Relief from judgment for fraud",
        },
        "categories": []
    }

    compiler["categories"].append({
        "category": "VIOLENCE ALLEGATIONS",
        "description": "Emily's sworn claims of violence/threats — contradicted by evidence",
        "instances": [
            {"claim": "Straw incident (Oct 2023) — alleged Andrew was violent/threatening", "contradicted_by": "No police report, no witnesses, no injuries documented", "filing": "PPO petition 2023-5907-PP"},
            {"claim": "Alleged fear for physical safety", "contradicted_by": "Continued voluntary contact with Andrew after alleged incidents", "filing": "PPO petition"},
            {"claim": "Stalking allegations", "contradicted_by": "Andrew visiting child at known locations is parental right, not stalking", "filing": "PPO petition"},
        ]
    })

    compiler["categories"].append({
        "category": "PARENTING FITNESS CLAIMS",
        "description": "Emily's sworn claims about Andrew's unfitness — contradicted by reality",
        "instances": [
            {"claim": "Andrew is unfit/dangerous parent", "contradicted_by": "Andrew was primary caregiver — documented by pediatrician records, daycare records", "filing": "Custody petition 2024-001507-DC"},
            {"claim": "Child is unsafe with Andrew", "contradicted_by": "Zero CPS findings against Andrew, zero police reports of child endangerment", "filing": "Custody proceedings"},
            {"claim": "Andrew does not provide stable environment", "contradicted_by": "Andrew maintained consistent residence at 1977 Whitehall Road throughout", "filing": "Custody proceedings"},
        ]
    })

    compiler["categories"].append({
        "category": "COOPERATION CLAIMS",
        "description": "Emily's claims of cooperating with court — contradicted by actions",
        "instances": [
            {"claim": "Willing to facilitate father-child relationship", "contradicted_by": "Systematically blocked ALL contact since Aug 2025 suspension", "filing": "Best interest factor representations"},
            {"claim": "Following court orders in good faith", "contradicted_by": "Using court orders as weapon to eliminate Andrew's parenting time", "filing": "Various filings"},
        ]
    })

    compiler["categories"].append({
        "category": "FINANCIAL MISREPRESENTATIONS",
        "description": "Emily's financial claims — potentially false for support calculations",
        "instances": [
            {"claim": "Income/expense representations in support proceedings", "contradicted_by": "Discovery needed to verify — motion to compel may reveal discrepancies", "filing": "Support proceedings"},
            {"claim": "Berry's role and household contributions", "contradicted_by": "Berry appears to be cohabiting and contributing — affects support calculation", "filing": "Financial disclosures"},
        ]
    })

    # DB evidence counts
    stats = {"contradiction_quotes": 0, "perjury_indicators": 0}
    try:
        conn = sqlite3.connect(DB, timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        row = conn.execute("""SELECT
            (SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%false%' OR quote_text LIKE '%lie%' OR quote_text LIKE '%perjur%') as perjury,
            (SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%contradict%' OR quote_text LIKE '%inconsisten%') as contra
        """).fetchone()
        if row:
            stats["perjury_indicators"] = row[0]
            stats["contradiction_quotes"] = row[1]
        conn.close()
    except:
        pass

    compiler["db_evidence"] = stats
    compiler["total_instances"] = sum(len(c["instances"]) for c in compiler["categories"])
    compiler["total_categories"] = len(compiler["categories"])

    return compiler

def main():
    c = build_perjury_compiler()
    md_path = os.path.join(REPORT_DIR, 'PERJURY_EVIDENCE_COMPILER.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {c['title']}\n\n*{c['subtitle']}*\n\n")
        ls = c["legal_standard"]
        f.write(f"## Legal Standard: {ls['statute']}\n\n")
        f.write(f"**Elements:**\n")
        for e in ls["elements"]:
            f.write(f"1. {e}\n")
        f.write(f"\n**Penalty:** {ls['penalty']}\n")
        f.write(f"**Civil Use:** {ls['civil_use']}\n\n")
        for cat in c["categories"]:
            f.write(f"## {cat['category']}\n*{cat['description']}*\n\n")
            for inst in cat["instances"]:
                f.write(f"### Sworn Claim: {inst['claim']}\n")
                f.write(f"**Contradicted by:** {inst['contradicted_by']}\n")
                f.write(f"*Source filing: {inst['filing']}*\n\n")
        f.write(f"---\n*DB: {c['db_evidence']['perjury_indicators']} perjury indicators, {c['db_evidence']['contradiction_quotes']} contradiction quotes*\n")
    json_path = os.path.join(REPORT_DIR, 'perjury_evidence_compiler.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(c, f, indent=2)
    print(f"Tool #192 — PERJURY EVIDENCE COMPILER")
    print(f"  {c['total_categories']} categories | {c['total_instances']} instances")
    print(f"  DB: {c['db_evidence']['perjury_indicators']} perjury indicators")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
