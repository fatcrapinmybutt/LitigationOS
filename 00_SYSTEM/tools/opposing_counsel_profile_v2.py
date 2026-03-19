#!/usr/bin/env python3
"""Tool #184 — Opposing Counsel Profile v2: Barnes Law Firm.
Analysis of Jennifer Barnes (P55406) patterns, weaknesses,
withdrawal implications, and strategic opportunities."""

import json, os, sys, sqlite3
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB = os.path.join(os.path.dirname(__file__), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')
os.makedirs(REPORT_DIR, exist_ok=True)

def build_counsel_profile():
    profile = {
        "tool_id": 184,
        "version": 2,
        "title": "OPPOSING COUNSEL PROFILE v2 — BARNES LAW FIRM",
        "subject": {
            "name": "Jennifer Barnes",
            "bar_number": "P55406",
            "firm": "Barnes Law Firm PLLC",
            "address": "880 Jefferson St Ste B, Muskegon, MI 49440",
            "status": "WITHDREW from representation",
        },
        "sections": []
    }

    profile["sections"].append({
        "title": "WITHDRAWAL ANALYSIS",
        "significance": "Barnes's withdrawal is a STRATEGIC GIFT to Andrew",
        "points": [
            {"point": "Emily is now PRO SE — she lost her legal advantage", "implication": "Level playing field"},
            {"point": "Withdrawal suggests Barnes recognized ethical problems", "authority": "MRPC 1.16(a)"},
            {"point": "Barnes may have discovered Emily's perjury and refused to suborn it", "authority": "MRPC 3.3(a)(3)"},
            {"point": "Withdrawal does NOT cure prior misconduct", "authority": "MRPC 8.4(c)"},
            {"point": "Emily must file own motions — limited legal sophistication", "note": "Berry may ghost-write = UPL"},
            {"point": "Monitor for Berry drafting Emily's filings", "authority": "MCL 600.916"},
        ]
    })

    profile["sections"].append({
        "title": "POTENTIAL ETHICAL VIOLATIONS",
        "violations": [
            {"rule": "MRPC 3.1", "violation": "Filing PPO based on fabricated allegations"},
            {"rule": "MRPC 3.3(a)", "violation": "Presenting false testimony without correction"},
            {"rule": "MRPC 3.4(a)", "violation": "Obstructing Andrew's access to evidence"},
            {"rule": "MRPC 4.1", "violation": "Material misrepresentations in filings"},
            {"rule": "MRPC 8.4(c)", "violation": "Participating in fraud upon the court"},
            {"rule": "MRPC 8.4(d)", "violation": "Conduct prejudicial to justice"},
        ]
    })

    profile["sections"].append({
        "title": "STRATEGIC OPPORTUNITIES",
        "opportunities": [
            {"action": "File State Bar grievance against Barnes (P55406)", "priority": "HIGH"},
            {"action": "Include Barnes as §1983 co-defendant", "theory": "Dennis v Sparks", "priority": "HIGH"},
            {"action": "Subpoena Barnes's file in federal discovery", "priority": "CRITICAL"},
            {"action": "Motion for sanctions under MCR 2.114(E)", "priority": "MEDIUM"},
            {"action": "Depose Barnes about Berry's role", "priority": "HIGH"},
            {"action": "Monitor post-withdrawal filings for Berry UPL", "priority": "ONGOING"},
        ]
    })

    profile["sections"].append({
        "title": "BERRY UPL RISK",
        "note": "Ronald Berry has NO bar number. NOT an attorney. NEVER was Emily's attorney.",
        "indicators": [
            {"sign": "Berry drafting/ghost-writing filings for Emily", "authority": "MCL 600.916"},
            {"sign": "Berry providing legal strategy direction", "authority": "MCL 600.916"},
            {"sign": "Berry communicating with court on Emily's behalf", "authority": "MCR 2.117"},
            {"sign": "Filing quality change post-Barnes withdrawal", "note": "Compare style before/after"},
        ]
    })

    stats = {"barnes_mentions": 0, "berry_mentions": 0}
    try:
        conn = sqlite3.connect(DB, timeout=30)
        conn.execute("PRAGMA busy_timeout=60000")
        row = conn.execute("""SELECT
            (SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%Barnes%'),
            (SELECT COUNT(*) FROM evidence_quotes WHERE quote_text LIKE '%Berry%')
        """).fetchone()
        if row:
            stats["barnes_mentions"], stats["berry_mentions"] = row
        conn.close()
    except:
        pass

    profile["db_evidence"] = stats
    return profile

def main():
    profile = build_counsel_profile()
    
    md_path = os.path.join(REPORT_DIR, 'OPPOSING_COUNSEL_PROFILE_V2.md')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {profile['title']}\n\n")
        s = profile["subject"]
        f.write(f"**{s['name']}** | Bar #{s['bar_number']} | {s['firm']}\n")
        f.write(f"**Status: {s['status']}**\n\n")
        for sec in profile["sections"]:
            f.write(f"## {sec['title']}\n\n")
            if sec.get("significance"):
                f.write(f"*{sec['significance']}*\n\n")
            if sec.get("note"):
                f.write(f"> ⚠️ {sec['note']}\n\n")
            items = sec.get("points", sec.get("violations", sec.get("opportunities", sec.get("indicators", []))))
            for item in items:
                main_text = item.get("point") or item.get("violation") or item.get("action") or item.get("sign", "")
                extra = item.get("authority") or item.get("rule") or item.get("theory", "")
                f.write(f"- {main_text}")
                if extra:
                    f.write(f" — *{extra}*")
                f.write("\n")
            f.write("\n")
        f.write(f"---\n*DB: {profile['db_evidence']['barnes_mentions']} Barnes, {profile['db_evidence']['berry_mentions']} Berry mentions*\n")

    json_path = os.path.join(REPORT_DIR, 'opposing_counsel_profile_v2.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(profile, f, indent=2)

    print(f"Tool #184 — OPPOSING COUNSEL PROFILE v2")
    print(f"  4 sections | Barnes P55406 | WITHDREW")
    print(f"  DB: {profile['db_evidence']['barnes_mentions']} Barnes, {profile['db_evidence']['berry_mentions']} Berry mentions")
    print(f"  Reports: {md_path}")

if __name__ == '__main__':
    main()
