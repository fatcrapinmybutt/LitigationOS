#!/usr/bin/env python3
"""Tool #248: Witness List & Subpoena Generator
Identifies all potential witnesses from the evidence database, generates witness lists
categorized by type, and creates subpoena templates with specific testimony targets.
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
    print("TOOL #248: WITNESS LIST & SUBPOENA GENERATOR")
    print("=" * 70)

    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]

    witnesses = {}

    def add_witness(name, category, testimony_topics, evidence_count=0, priority="MEDIUM"):
        key = s(name).strip()
        if not key or len(key) < 3:
            return
        if key not in witnesses:
            witnesses[key] = {
                "name": name.strip(),
                "category": category,
                "testimony_topics": [],
                "evidence_count": 0,
                "priority": priority,
                "subpoena_needed": True,
                "documents_to_produce": []
            }
        witnesses[key]["testimony_topics"].extend(testimony_topics if isinstance(testimony_topics, list) else [testimony_topics])
        witnesses[key]["evidence_count"] += evidence_count
        # Upgrade priority
        pri_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        if pri_order.get(priority, 0) > pri_order.get(witnesses[key]["priority"], 0):
            witnesses[key]["priority"] = priority

    # --- Known key witnesses ---
    print("\n[1/5] Adding known witnesses...")
    add_witness("Emily A. Watson", "Adverse Party", [
        "Custody interference patterns",
        "PPO filing basis and truthfulness",
        "Ronald Berry's involvement in legal proceedings",
        "Withholding of L.D.W. from Andrew Pigors",
        "Communications with FOC/Rusco",
        "Ex parte order of August 2025"
    ], priority="CRITICAL")

    add_witness("Ronald T. Berry", "Adverse Witness", [
        "Unauthorized practice of law (MCL 600.916)",
        "Drafting legal documents for Emily Watson",
        "Communications with court/FOC on Emily's behalf",
        "Albert Watson statement about premeditated ex parte",
        "Presence in home during custody periods",
        "Conspiracy to deprive parental rights"
    ], priority="CRITICAL")

    add_witness("Pamela Rusco", "FOC Representative", [
        "Ex parte communications with Emily Watson/Ronald Berry",
        "HealthWest evaluation referral process",
        "Basis for FOC recommendations",
        "Communications with Judge McNeill outside hearings",
        "Compliance with MCR 3.224 procedures"
    ], priority="CRITICAL")

    add_witness("Jennifer Barnes", "Former Attorney (P55406)", [
        "Withdrawal from representation",
        "Knowledge of fraudulent filings",
        "Ronald Berry's role during her representation",
        "Communications with FOC on Emily's behalf"
    ], priority="HIGH")

    add_witness("Albert Watson", "Fact Witness", [
        "Statement NS2505044 about premeditated ex parte",
        "Knowledge of Emily and Berry's plan to obtain ex parte order",
        "Observations of Berry's control over legal proceedings"
    ], priority="CRITICAL")

    # --- Mine speakers from evidence_quotes ---
    print("[2/5] Mining witnesses from evidence quotes...")
    if 'evidence_quotes' in tables:
        eq_cols = [r[1] for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()]
        if 'speaker' in eq_cols:
            speakers = conn.execute("""
                SELECT speaker, COUNT(*) as cnt FROM evidence_quotes
                WHERE speaker IS NOT NULL AND speaker != ''
                GROUP BY speaker HAVING cnt >= 3
                ORDER BY cnt DESC LIMIT 50
            """).fetchall()
            for sp in speakers:
                d = dict(sp)
                name = str(d.get('speaker', ''))
                cnt = d.get('cnt', 0)
                if any(skip in s(name) for skip in ['unknown', 'n/a', 'system', 'court', 'record']):
                    continue
                cat = "Fact Witness"
                if 'watson' in s(name) or 'emily' in s(name):
                    cat = "Adverse Party"
                elif 'rusco' in s(name) or 'foc' in s(name):
                    cat = "FOC Representative"
                elif 'berry' in s(name) or 'ronald' in s(name):
                    cat = "Adverse Witness"
                elif 'barnes' in s(name) or 'attorney' in s(name):
                    cat = "Former Attorney"
                elif 'mcneill' in s(name) or 'judge' in s(name):
                    continue  # Can't subpoena the judge
                elif 'pigors' in s(name) or 'andrew' in s(name):
                    continue  # That's us
                add_witness(name, cat, [f"Testimony regarding {cnt} evidence items"], evidence_count=cnt, priority="HIGH" if cnt > 20 else "MEDIUM")

    # --- Mine from d_drive_events actors ---
    print("[3/5] Mining witnesses from D drive events...")
    if 'd_drive_events' in tables:
        de_cols = [r[1] for r in conn.execute("PRAGMA table_info(d_drive_events)").fetchall()]
        if 'actors' in de_cols:
            actors = conn.execute("""
                SELECT actors, COUNT(*) as cnt FROM d_drive_events
                WHERE actors IS NOT NULL AND actors != ''
                GROUP BY actors ORDER BY cnt DESC LIMIT 30
            """).fetchall()
            for ac in actors:
                d = dict(ac)
                actor_str = str(d.get('actors', ''))
                cnt = d.get('cnt', 0)
                for actor in actor_str.split(','):
                    actor = actor.strip()
                    if actor and len(actor) > 2:
                        if any(skip in s(actor) for skip in ['andrew', 'pigors', 'mcneill', 'judge', 'court']):
                            continue
                        add_witness(actor, "Fact Witness", [f"Witnessed {cnt} documented events"], evidence_count=cnt)

    # --- Expert witnesses needed ---
    print("[4/5] Identifying expert witnesses needed...")
    expert_witnesses = [
        {
            "name": "Forensic Psychologist (TBD)",
            "category": "Expert Witness",
            "purpose": "Rebut HealthWest evaluation; testify on parental alienation patterns; evaluate Emily's pattern of false allegations",
            "testimony_topics": ["HealthWest evaluation methodology flaws", "Parental alienation indicators", "Child's best interest factors"],
            "priority": "CRITICAL",
            "subpoena_needed": False,
            "retained": False
        },
        {
            "name": "HealthWest Evaluator (Records Custodian)",
            "category": "Expert/Custodian",
            "purpose": "Produce raw evaluation data; testify on 7-day diagnostic reversal; disclose communications with FOC",
            "testimony_topics": ["Evaluation methodology", "Basis for diagnostic change", "Communications with Rusco/FOC"],
            "priority": "CRITICAL",
            "subpoena_needed": True,
            "retained": False
        },
        {
            "name": "UPL Expert (Michigan State Bar)",
            "category": "Expert Witness",
            "purpose": "Testify that Berry's actions constitute unauthorized practice of law under MCL 600.916",
            "testimony_topics": ["Definition of practicing law in Michigan", "Berry's actions as UPL"],
            "priority": "HIGH",
            "subpoena_needed": False,
            "retained": False
        }
    ]

    # --- Subpoena templates ---
    print("[5/5] Generating subpoena templates...")
    subpoenas = []
    for key, w in witnesses.items():
        if w.get("subpoena_needed", True) and w["priority"] in ("CRITICAL", "HIGH"):
            # Deduplicate topics
            topics = list(set(w["testimony_topics"]))[:10]
            subpoenas.append({
                "witness": w["name"],
                "category": w["category"],
                "priority": w["priority"],
                "testimony_topics": topics,
                "evidence_count": w["evidence_count"],
                "documents_to_produce": [
                    f"All documents relating to {t}" for t in topics[:5]
                ],
                "service_method": "Personal service per MCR 2.105",
                "form": "MC 11 (Subpoena)" if w["category"] != "Expert/Custodian" else "MC 11 + MC 13 (Subpoena Duces Tecum)"
            })

    results = {
        "tool": "#248 Witness List & Subpoena Generator",
        "generated": datetime.now().isoformat(),
        "witnesses": list(witnesses.values()),
        "expert_witnesses_needed": expert_witnesses,
        "subpoenas": subpoenas,
        "totals": {
            "fact_witnesses": sum(1 for w in witnesses.values() if w["category"] == "Fact Witness"),
            "adverse_parties": sum(1 for w in witnesses.values() if w["category"] in ("Adverse Party", "Adverse Witness")),
            "officials": sum(1 for w in witnesses.values() if "FOC" in w["category"] or "Attorney" in w["category"]),
            "experts_needed": len(expert_witnesses),
            "subpoenas_needed": len(subpoenas),
            "total_witnesses": len(witnesses) + len(expert_witnesses)
        }
    }

    # --- Reports ---
    md_lines = [
        "# Tool #248: Witness List & Subpoena Generator",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## Summary",
        f"- **Total Witnesses Identified**: {len(witnesses)}",
        f"- **Expert Witnesses Needed**: {len(expert_witnesses)}",
        f"- **Subpoenas to Issue**: {len(subpoenas)}",
        "",
        "## Witness Categories",
        f"- Fact Witnesses: {results['totals']['fact_witnesses']}",
        f"- Adverse Parties/Witnesses: {results['totals']['adverse_parties']}",
        f"- Officials: {results['totals']['officials']}",
        f"- Experts: {results['totals']['experts_needed']}",
        "",
        "---",
        "## CRITICAL Priority Witnesses",
        ""
    ]
    for key, w in sorted(witnesses.items(), key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x[1]["priority"], 4)):
        if w["priority"] == "CRITICAL":
            topics = list(set(w["testimony_topics"]))
            md_lines.append(f"### {w['name']} ({w['category']})")
            md_lines.append(f"- Evidence items: {w['evidence_count']}")
            md_lines.append(f"- Testimony topics:")
            for t in topics[:8]:
                md_lines.append(f"  - {t}")
            md_lines.append("")

    md_lines.append("\n## HIGH Priority Witnesses\n")
    for key, w in sorted(witnesses.items(), key=lambda x: -x[1]["evidence_count"]):
        if w["priority"] == "HIGH":
            md_lines.append(f"### {w['name']} ({w['category']})")
            md_lines.append(f"- Evidence items: {w['evidence_count']}")
            md_lines.append("")

    md_lines.append("\n## Expert Witnesses Needed\n")
    for ew in expert_witnesses:
        md_lines.append(f"### {ew['name']}")
        md_lines.append(f"- **Purpose**: {ew['purpose']}")
        md_lines.append(f"- **Priority**: {ew['priority']}")
        md_lines.append(f"- **Retained**: {'Yes' if ew.get('retained') else 'No — needs retention'}")
        md_lines.append("")

    md_lines.append(f"\n## Subpoenas Required ({len(subpoenas)})\n")
    for sub in subpoenas:
        md_lines.append(f"### Subpoena: {sub['witness']}")
        md_lines.append(f"- **Form**: {sub['form']}")
        md_lines.append(f"- **Service**: {sub['service_method']}")
        md_lines.append(f"- **Testimony Topics**: {', '.join(sub['testimony_topics'][:5])}")
        md_lines.append("")

    md_path = os.path.join(report_dir, "tool_248_witness_subpoena.md")
    json_path = os.path.join(report_dir, "tool_248_witness_subpoena.json")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  MD:   {md_path}")
    print(f"  JSON: {json_path}")

    conn.close()
    print(f"\n{'='*70}")
    print(f"WITNESSES: {len(witnesses)} | EXPERTS: {len(expert_witnesses)} | SUBPOENAS: {len(subpoenas)}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
