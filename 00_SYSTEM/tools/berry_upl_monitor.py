#!/usr/bin/env python3
"""Tool #193 — Berry Unauthorized Practice of Law (UPL) Monitor.
Tracks indicators that Ronald Berry is practicing law without a license."""

import json, os, sys, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_upl_monitor():
    monitor = {
        "tool_id": 193,
        "title": "BERRY UPL MONITOR — UNAUTHORIZED PRACTICE OF LAW",
        "subtitle": "Ronald T. Berry — NOT an attorney, NO bar number",
        "subject": {
            "name": "Ronald T. Berry",
            "status": "NON-ATTORNEY — Emily Watson's boyfriend/domestic partner",
            "bar_number": "NONE — never admitted to Michigan Bar",
            "relationship": "Cohabiting with Emily at 2160 Garland Drive, Norton Shores, MI 49441",
        },
        "legal_framework": {
            "statute": "MCL 600.916 — Unauthorized Practice of Law",
            "penalty": "Misdemeanor for first offense, felony for subsequent",
            "definition": "Practice of law includes: legal advice, drafting legal documents, representing in court, negotiating legal matters",
            "reporting": "Report to State Bar of Michigan UPL Committee + circuit court judge",
        },
        "indicators": [],
        "detection_methods": [],
        "action_plan": [],
    }

    monitor["indicators"] = [
        {"indicator": "Berry drafting or ghost-writing Emily's legal filings", "evidence_type": "Writing style analysis — compare pre/post Barnes withdrawal", "severity": "HIGH"},
        {"indicator": "Berry providing legal strategy to Emily", "evidence_type": "Communications (text, email) showing Berry directing legal decisions", "severity": "HIGH"},
        {"indicator": "Berry communicating with court or court staff", "evidence_type": "Court records showing Berry as contact person", "severity": "CRITICAL"},
        {"indicator": "Berry attending court hearings and advising Emily during proceedings", "evidence_type": "Courtroom observation, transcript references", "severity": "MEDIUM"},
        {"indicator": "Berry researching law and preparing legal arguments for Emily", "evidence_type": "Electronic evidence of legal research on Emily's behalf", "severity": "MEDIUM"},
        {"indicator": "Berry negotiating with Andrew on legal matters on Emily's behalf", "evidence_type": "Communications showing Berry acting as Emily's agent", "severity": "HIGH"},
        {"indicator": "Filing quality increase after Barnes withdrawal", "evidence_type": "Compare complexity of Emily's filings before/after Barnes left", "severity": "MEDIUM"},
        {"indicator": "Berry signing or co-signing legal documents", "evidence_type": "Court filings with Berry's signature or electronic submission", "severity": "CRITICAL"},
    ]

    monitor["detection_methods"] = [
        {"method": "Writing style analysis", "description": "Compare Emily's pre-Barnes and post-Barnes filings. If legal sophistication suddenly increases without attorney, someone is helping.", "tool": "Use linguistic analysis tools — sentence complexity, legal terminology density, citation accuracy"},
        {"method": "Discovery requests", "description": "Serve interrogatories asking Emily: 'Who assisted in preparing this filing?' — she must answer under oath", "authority": "MCR 2.309"},
        {"method": "Court observation", "description": "Note if Berry whispers to Emily during hearings, passes notes, or speaks to court staff", "note": "Document every instance with date/time"},
        {"method": "Electronic evidence", "description": "Subpoena Emily's email/text for communications with Berry about legal matters", "authority": "MCR 2.310"},
        {"method": "Metadata analysis", "description": "If Emily's filings are electronic, check document metadata for author name", "note": "PDF properties often show original author"},
    ]

    monitor["action_plan"] = [
        {"step": 1, "action": "Document every suspected UPL indicator with dates and evidence", "priority": "ONGOING"},
        {"step": 2, "action": "File formal UPL complaint with State Bar of Michigan", "form": "UPL complaint form at michbar.org", "priority": "HIGH"},
        {"step": 3, "action": "Notify circuit court judge of suspected UPL", "authority": "Court has inherent authority to prevent UPL in proceedings", "priority": "HIGH"},
        {"step": 4, "action": "Include UPL in federal §1983 complaint as evidence of conspiracy", "theory": "Berry's UPL shows coordinated effort to deprive Andrew's rights", "priority": "MEDIUM"},
        {"step": 5, "action": "Serve discovery specifically targeting Berry's involvement", "note": "Berry is NOT Emily's attorney — no privilege for Berry communications", "priority": "HIGH"},
    ]

    # DB mentions
    stats = {"berry_mentions": 0}
    try:
        conn = sqlite3.connect(DB, timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        row = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%Berry%'").fetchone()
        if row:
            stats["berry_mentions"] = row[0]
        conn.close()
    except:
        pass

    monitor["db_evidence"] = stats
    return monitor

def main():
    m = build_upl_monitor()
    md_path = os.path.join(REPORT_DIR, 'BERRY_UPL_MONITOR.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {m['title']}\n\n*{m['subtitle']}*\n\n")
        s = m["subject"]
        f.write(f"> ⚠️ **{s['name']}** — {s['status']}\n")
        f.write(f"> Bar Number: {s['bar_number']}\n\n")
        lf = m["legal_framework"]
        f.write(f"## Legal Framework\n- **{lf['statute']}**\n- Penalty: {lf['penalty']}\n- Definition: {lf['definition']}\n\n")
        f.write(f"## UPL Indicators ({len(m['indicators'])})\n\n")
        for ind in m["indicators"]:
            f.write(f"- **[{ind['severity']}]** {ind['indicator']}\n  *Evidence: {ind['evidence_type']}*\n\n")
        f.write(f"## Detection Methods ({len(m['detection_methods'])})\n\n")
        for dm in m["detection_methods"]:
            f.write(f"### {dm['method']}\n{dm['description']}\n\n")
        f.write(f"## Action Plan ({len(m['action_plan'])} steps)\n\n")
        for ap in m["action_plan"]:
            f.write(f"{ap['step']}. **{ap['action']}** [{ap['priority']}]\n")
        f.write(f"\n---\n*DB: {m['db_evidence']['berry_mentions']} Berry mentions*\n")
    json_path = os.path.join(REPORT_DIR, 'berry_upl_monitor.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(m, f, indent=2)
    print(f"Tool #193 — BERRY UPL MONITOR")
    print(f"  {len(m['indicators'])} indicators | {len(m['detection_methods'])} detection methods | {len(m['action_plan'])} actions")
    print(f"  DB: {m['db_evidence']['berry_mentions']} Berry mentions")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
