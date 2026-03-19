#!/usr/bin/env python3
"""
Tool #211 — Discovery Request Generator
Generates targeted discovery requests (interrogatories, production requests,
admissions) against Emily A. Watson, Ronald Berry, and Jennifer Barnes P55406.
Cites MCR 2.309, MCR 2.310, MCR 2.312.
Output: DISCOVERY_REQUESTS.md + DISCOVERY_REQUESTS.json
"""
import sys, os, json, sqlite3, re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

TOOLS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO = TOOLS_DIR.parent.parent
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = TOOLS_DIR.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# === Verified Party Identity (NEVER fabricate) ===
PARTIES = {
    "plaintiff": {"name": "Andrew James Pigors", "role": "Plaintiff/Father"},
    "defendant": {"name": "Emily A. Watson", "role": "Defendant/Mother",
                  "address": "2160 Garland Drive, Norton Shores, MI 49441"},
    "berry": {"name": "Ronald Berry", "role": "Non-Attorney / Emily's domestic partner"},
    "barnes": {"name": "Jennifer Barnes", "bar": "P55406", "role": "Former Attorney (WITHDREW)",
               "firm": "Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440"},
    "child": {"name": "L.D.W.", "note": "Initials only per MCR 8.119(H)"},
    "judge": {"name": "Hon. Jenny L. McNeill", "court": "14th Circuit Court, Family Division"},
    "foc": {"name": "Pamela Rusco", "address": "990 Terrace St, Muskegon, MI 49442"},
}

CASE_NUMBERS = ["2024-001507-DC", "2023-5907-PP"]


def get_db_connection():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def get_tables(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '%_fts_%'").fetchall()
    return [r[0] for r in rows]


def mine_evidence_for_discovery(conn, tables):
    """Mine DB for evidence supporting discovery requests."""
    evidence = {"watson": [], "berry": [], "barnes": [], "communications": [], "general": []}

    # Mine evidence_quotes for relevant testimony/evidence
    if "evidence_quotes" in tables:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
        rows = conn.execute("""
            SELECT quote_text, evidence_category, speaker, date_ref, legal_significance
            FROM evidence_quotes
            WHERE quote_text IS NOT NULL
            LIMIT 2000
        """).fetchall()
        for r in rows:
            text = (r[0] or "").lower()
            cat = r[1] or ""
            speaker = r[2] or ""
            sig = r[4] or ""
            entry = {"text": r[0][:200], "category": cat, "speaker": speaker,
                     "date": r[3], "significance": sig}
            if any(w in text for w in ["watson", "emily", "mother", "defendant"]):
                evidence["watson"].append(entry)
            if any(w in text for w in ["berry", "ronald", "boyfriend"]):
                evidence["berry"].append(entry)
            if any(w in text for w in ["barnes", "attorney", "withdrawal", "withdrew"]):
                evidence["barnes"].append(entry)
            if any(w in text for w in ["communication", "text message", "email", "conspir"]):
                evidence["communications"].append(entry)

    # Mine impeachment_items
    if "impeachment_items" in tables:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(impeachment_items)").fetchall()]
        rows = conn.execute("SELECT * FROM impeachment_items LIMIT 500").fetchall()
        for r in rows:
            d = dict(r)
            text_fields = " ".join(str(v) for v in d.values() if v).lower()
            entry = {"source": "impeachment_items", "data": {k: str(v)[:150] for k, v in d.items() if v}}
            if any(w in text_fields for w in ["watson", "emily", "perjury", "false"]):
                evidence["watson"].append(entry)
            if any(w in text_fields for w in ["berry", "upl", "unauthorized"]):
                evidence["berry"].append(entry)

    # Mine contradiction_map
    if "contradiction_map" in tables:
        rows = conn.execute("SELECT * FROM contradiction_map LIMIT 500").fetchall()
        for r in rows:
            d = dict(r)
            evidence["general"].append({"source": "contradiction_map",
                                        "data": {k: str(v)[:150] for k, v in d.items() if v}})

    # Mine adversary_models
    if "adversary_models" in tables:
        rows = conn.execute("SELECT * FROM adversary_models LIMIT 100").fetchall()
        for r in rows:
            d = dict(r)
            evidence["general"].append({"source": "adversary_models",
                                        "data": {k: str(v)[:150] for k, v in d.items() if v}})

    return evidence


def build_interrogatories():
    """MCR 2.309 — Interrogatories to parties."""
    return {
        "rule": "MCR 2.309",
        "title": "Interrogatories to Parties",
        "targets": {
            "Emily A. Watson": [
                {
                    "number": 1,
                    "topic": "Perjury — Straw Incident",
                    "text": "Describe in detail the incident you reported involving a straw, including the exact date, time, location, all persons present, and whether any photographs or video recordings were taken at the time of the alleged incident.",
                },
                {
                    "number": 2,
                    "topic": "Staged Photographs",
                    "text": "Identify all photographs you have submitted or intend to submit as evidence in this case. For each photograph, state: (a) the date taken, (b) the device used, (c) who took the photograph, (d) whether the photograph was edited or altered in any way, and (e) the circumstances depicted.",
                },
                {
                    "number": 3,
                    "topic": "False Allegations",
                    "text": "List every allegation you have made against Plaintiff Andrew James Pigors to any court, law enforcement agency, CPS, or other governmental body. For each allegation, state: (a) the date made, (b) the agency or court to which it was made, (c) the substance of the allegation, and (d) the outcome or disposition.",
                },
                {
                    "number": 4,
                    "topic": "Ronald Berry's Role",
                    "text": "Describe the nature of your relationship with Ronald Berry, including: (a) when the relationship began, (b) whether he resides at your address, (c) what role, if any, he plays in the care of the minor child L.D.W., and (d) whether he has provided you legal advice or assisted in preparing any court filings.",
                },
                {
                    "number": 5,
                    "topic": "Communications Regarding Litigation",
                    "text": "Identify all communications between you and Ronald Berry regarding this litigation, including text messages, emails, letters, and verbal conversations where litigation strategy was discussed. State the date, medium, and substance of each.",
                },
                {
                    "number": 6,
                    "topic": "Attorney Barnes Withdrawal",
                    "text": "Describe the circumstances surrounding the withdrawal of your attorney Jennifer Barnes (P55406). State: (a) who initiated the withdrawal, (b) the reasons given, (c) whether any disagreement over litigation strategy preceded the withdrawal, and (d) whether Ronald Berry assumed any advisory role after the withdrawal.",
                },
                {
                    "number": 7,
                    "topic": "Financial Disclosures",
                    "text": "State your current income from all sources, including employment, government assistance, and financial support from Ronald Berry or any other person. Identify all bank accounts in your name or to which you have access.",
                },
                {
                    "number": 8,
                    "topic": "Parenting Time Interference",
                    "text": "For each instance in which Plaintiff's scheduled parenting time did not occur as ordered, state: (a) the date, (b) the reason parenting time did not occur, (c) who made the decision, and (d) whether the court was notified.",
                },
            ],
            "Ronald Berry": [
                {
                    "number": 1,
                    "topic": "Unauthorized Practice of Law",
                    "text": "State whether you have ever: (a) drafted or assisted in drafting any court filing in this case, (b) provided legal advice to Emily A. Watson regarding this case, (c) appeared at the courthouse on behalf of Emily A. Watson, or (d) communicated with any attorney regarding litigation strategy for this case.",
                },
                {
                    "number": 2,
                    "topic": "Courthouse Appearances",
                    "text": "List every date on which you appeared at the Muskegon County courthouse in connection with any case involving Emily A. Watson. For each appearance, state your purpose and what actions you took.",
                },
                {
                    "number": 3,
                    "topic": "Document Preparation",
                    "text": "Identify every legal document you have prepared, edited, reviewed, or assisted in preparing for filing in any court case involving Emily A. Watson. Include motions, responses, affidavits, and any other filings.",
                },
                {
                    "number": 4,
                    "topic": "Legal Coaching",
                    "text": "Describe any instance in which you advised Emily A. Watson on how to respond to interrogatories, what testimony to give, or how to present evidence in court proceedings.",
                },
            ],
        },
    }


def build_production_requests():
    """MCR 2.310 — Requests for Production of Documents."""
    return {
        "rule": "MCR 2.310",
        "title": "Requests for Production of Documents and Things",
        "targets": {
            "Emily A. Watson": [
                {
                    "number": 1,
                    "text": "All text messages, emails, and electronic communications between you and Ronald Berry from January 1, 2023 to the present, including messages on any platform (SMS, iMessage, Facebook Messenger, WhatsApp, etc.).",
                },
                {
                    "number": 2,
                    "text": "All photographs submitted or intended to be submitted as evidence, together with the original digital files including EXIF metadata.",
                },
                {
                    "number": 3,
                    "text": "All communications with Jennifer Barnes (P55406) regarding her withdrawal as your attorney, including engagement letters, billing statements, and correspondence.",
                },
                {
                    "number": 4,
                    "text": "All documents, notes, or records created by or with the assistance of Ronald Berry relating to this litigation.",
                },
                {
                    "number": 5,
                    "text": "All CPS reports, complaints, or referrals made by you or on your behalf concerning Andrew James Pigors, including the agency response or outcome for each.",
                },
                {
                    "number": 6,
                    "text": "All records from HealthWest or any mental health provider relating to evaluations or treatment of L.D.W., to the extent not protected by privilege.",
                },
                {
                    "number": 7,
                    "text": "All financial records, including bank statements, pay stubs, tax returns, and records of support received from Ronald Berry, for the period January 1, 2023 to the present.",
                },
            ],
            "Ronald Berry": [
                {
                    "number": 1,
                    "text": "All documents you have drafted, edited, or assisted in preparing for filing in any case involving Emily A. Watson, including drafts, notes, and final versions.",
                },
                {
                    "number": 2,
                    "text": "All electronic communications between you and Emily A. Watson discussing litigation strategy, court filings, or legal proceedings, from January 1, 2023 to the present.",
                },
                {
                    "number": 3,
                    "text": "Any legal research materials, templates, or form documents you obtained or used in connection with this litigation.",
                },
            ],
            "Jennifer Barnes P55406": [
                {
                    "number": 1,
                    "text": "The complete client file for Emily A. Watson, to the extent disclosure is permitted, including all communications, work product, and billing records.",
                },
                {
                    "number": 2,
                    "text": "All documents relating to your withdrawal as counsel, including any motion to withdraw, correspondence with the court, and internal memoranda regarding the decision.",
                },
                {
                    "number": 3,
                    "text": "Any communications between you and Ronald Berry regarding this case.",
                },
            ],
        },
    }


def build_admissions():
    """MCR 2.312 — Requests for Admission."""
    return {
        "rule": "MCR 2.312",
        "title": "Requests for Admission",
        "target": "Emily A. Watson",
        "requests": [
            {"number": 1, "text": "Admit that Ronald Berry has assisted you in preparing court filings in this case."},
            {"number": 2, "text": "Admit that Ronald Berry is not a licensed attorney in the State of Michigan."},
            {"number": 3, "text": "Admit that Ronald Berry has accompanied you to the Muskegon County courthouse in connection with this case."},
            {"number": 4, "text": "Admit that you communicated with Ronald Berry about litigation strategy in this case."},
            {"number": 5, "text": "Admit that photographs you submitted as evidence were taken at your direction or request."},
            {"number": 6, "text": "Admit that Jennifer Barnes (P55406) withdrew as your attorney prior to the conclusion of this case."},
            {"number": 7, "text": "Admit that you have made reports to CPS regarding Andrew James Pigors."},
            {"number": 8, "text": "Admit that there were occasions when Plaintiff's court-ordered parenting time did not occur."},
            {"number": 9, "text": "Admit that Ronald Berry has provided you with legal advice regarding this case."},
            {"number": 10, "text": "Admit that you have communicated with Ronald Berry by text message about this case."},
        ],
    }


def main():
    print("=" * 70)
    print("TOOL #211 — Discovery Request Generator")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)

    # Connect to DB
    conn = get_db_connection()
    db_evidence = {}
    db_stats = {}
    if conn:
        tables = get_tables(conn)
        db_evidence = mine_evidence_for_discovery(conn, tables)
        db_stats = {
            "tables_available": len(tables),
            "watson_evidence_count": len(db_evidence.get("watson", [])),
            "berry_evidence_count": len(db_evidence.get("berry", [])),
            "barnes_evidence_count": len(db_evidence.get("barnes", [])),
            "communications_count": len(db_evidence.get("communications", [])),
            "general_evidence_count": len(db_evidence.get("general", [])),
        }
        conn.close()
        print(f"[DB] Connected. {db_stats['tables_available']} tables found.")
        print(f"[DB] Watson evidence items: {db_stats['watson_evidence_count']}")
        print(f"[DB] Berry evidence items: {db_stats['berry_evidence_count']}")
        print(f"[DB] Barnes evidence items: {db_stats['barnes_evidence_count']}")
        print(f"[DB] Communications items: {db_stats['communications_count']}")
    else:
        print("[WARN] DB not found — generating template requests without DB evidence.")

    interrogatories = build_interrogatories()
    production = build_production_requests()
    admissions = build_admissions()

    # Build JSON report
    report = {
        "tool": "#211 — Discovery Request Generator",
        "generated": datetime.now().isoformat(),
        "case_numbers": CASE_NUMBERS,
        "court": "14th Circuit Court, Family Division, Muskegon County",
        "judge": PARTIES["judge"]["name"],
        "parties": PARTIES,
        "db_stats": db_stats,
        "interrogatories": interrogatories,
        "production_requests": production,
        "admissions": admissions,
        "db_evidence_summary": {k: len(v) for k, v in db_evidence.items()},
    }

    json_path = REPORTS_DIR / "DISCOVERY_REQUESTS.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"[OK] JSON report: {json_path}")

    # Build MD report
    md = []
    md.append("# DISCOVERY REQUESTS — Pigors v. Watson")
    md.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"**Case Numbers:** {', '.join(CASE_NUMBERS)}")
    md.append(f"**Court:** 14th Circuit Court, Family Division, Muskegon County")
    md.append(f"**Judge:** {PARTIES['judge']['name']}")
    md.append(f"**Plaintiff:** {PARTIES['plaintiff']['name']}")
    md.append(f"**Defendant:** {PARTIES['defendant']['name']}")
    md.append("")

    # Interrogatories
    md.append("---")
    md.append(f"\n## I. INTERROGATORIES — {interrogatories['rule']}")
    md.append("")
    for target, questions in interrogatories["targets"].items():
        md.append(f"### To: {target}")
        md.append("")
        for q in questions:
            md.append(f"**Interrogatory No. {q['number']}** ({q['topic']})")
            md.append(f"> {q['text']}")
            md.append("")

    # Production Requests
    md.append("---")
    md.append(f"\n## II. REQUESTS FOR PRODUCTION — {production['rule']}")
    md.append("")
    for target, reqs in production["targets"].items():
        md.append(f"### To: {target}")
        md.append("")
        for r in reqs:
            md.append(f"**Request No. {r['number']}**")
            md.append(f"> {r['text']}")
            md.append("")

    # Admissions
    md.append("---")
    md.append(f"\n## III. REQUESTS FOR ADMISSION — {admissions['rule']}")
    md.append(f"\n### To: {admissions['target']}")
    md.append("")
    for r in admissions["requests"]:
        md.append(f"**Admission No. {r['number']}**")
        md.append(f"> {r['text']}")
        md.append("")

    # DB Evidence Summary
    if db_stats:
        md.append("---")
        md.append("\n## IV. DATABASE EVIDENCE SUPPORTING DISCOVERY")
        md.append(f"\n- Watson-related evidence items: **{db_stats.get('watson_evidence_count', 0)}**")
        md.append(f"- Berry-related evidence items: **{db_stats.get('berry_evidence_count', 0)}**")
        md.append(f"- Barnes-related evidence items: **{db_stats.get('barnes_evidence_count', 0)}**")
        md.append(f"- Communications evidence: **{db_stats.get('communications_count', 0)}**")
        md.append(f"- General evidence items: **{db_stats.get('general_evidence_count', 0)}**")
        md.append("")

    md.append("---")
    md.append(f"\n*Tool #211 — Discovery Request Generator — {datetime.now().isoformat()}*")

    md_path = REPORTS_DIR / "DISCOVERY_REQUESTS.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] MD report:   {md_path}")

    total_requests = (
        sum(len(v) for v in interrogatories["targets"].values())
        + sum(len(v) for v in production["targets"].values())
        + len(admissions["requests"])
    )
    print(f"\n[SUMMARY] {total_requests} total discovery requests generated:")
    print(f"  Interrogatories: {sum(len(v) for v in interrogatories['targets'].values())}")
    print(f"  Production Requests: {sum(len(v) for v in production['targets'].values())}")
    print(f"  Admissions: {len(admissions['requests'])}")
    print("[DONE] Tool #211 complete.")


if __name__ == "__main__":
    main()
