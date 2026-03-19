#!/usr/bin/env python3
"""
Tool #213 — Witness List Compiler
Compiles a comprehensive witness list from litigation_context.db.
Includes verified parties, DB-discovered witnesses, testimony summaries,
subpoena info, and hostile/friendly designations.
Output: WITNESS_LIST.md + WITNESS_LIST.json
"""
import sys, os, json, sqlite3, re
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

TOOLS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO = TOOLS_DIR.parent.parent
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR = TOOLS_DIR.parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# === Verified Witness List (from confirmed identity table) ===
KNOWN_WITNESSES = [
    {
        "name": "Andrew James Pigors",
        "role": "Plaintiff / Father",
        "designation": "Friendly",
        "contact": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445 | (231) 903-5690",
        "subpoena_required": False,
        "expected_testimony": [
            "Parenting history and relationship with L.D.W.",
            "Interference with parenting time by Defendant",
            "False allegations made against him",
            "Impact of ex parte orders on parent-child relationship",
            "Evidence of Defendant's perjury (straw incident, staged photos)",
            "Ronald Berry's unauthorized practice of law activities",
        ],
    },
    {
        "name": "Emily A. Watson",
        "role": "Defendant / Mother",
        "designation": "Hostile",
        "contact": "2160 Garland Drive, Norton Shores, MI 49441",
        "subpoena_required": False,
        "expected_testimony": [
            "Basis for allegations against Plaintiff",
            "Circumstances of straw incident and photograph evidence",
            "Relationship with Ronald Berry and his involvement in litigation",
            "Communications with Jennifer Barnes regarding withdrawal",
            "Compliance with court-ordered parenting time",
            "Financial circumstances and support arrangements",
        ],
    },
    {
        "name": "Ronald Berry",
        "role": "Emily's boyfriend / domestic partner (NON-ATTORNEY)",
        "designation": "Hostile",
        "contact": "[VERIFY — believed to reside with Emily Watson at Garland Drive address]",
        "subpoena_required": True,
        "expected_testimony": [
            "Involvement in preparing court filings (UPL evidence)",
            "Legal coaching and advice given to Emily Watson",
            "Courthouse appearances on behalf of Emily Watson",
            "Communications with Emily Watson about litigation strategy",
            "Role in the household and relationship with L.D.W.",
        ],
    },
    {
        "name": "Pamela Rusco",
        "role": "Friend of the Court (FOC)",
        "designation": "Neutral / Potentially Hostile",
        "contact": "990 Terrace St, Muskegon, MI 49442",
        "subpoena_required": True,
        "expected_testimony": [
            "FOC recommendations regarding custody and parenting time",
            "Warrant email and enforcement actions",
            "Investigation findings and reports",
            "Basis for any recommendations adverse to Plaintiff",
        ],
    },
    {
        "name": "Jennifer Barnes (P55406)",
        "role": "Former Attorney for Defendant (WITHDREW)",
        "designation": "Neutral",
        "contact": "Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440",
        "subpoena_required": True,
        "expected_testimony": [
            "Circumstances of withdrawal from representation",
            "Knowledge of Ronald Berry's involvement in case",
            "Awareness of false allegations or perjury by client",
            "Communications regarding litigation strategy (to extent not privileged)",
        ],
    },
    {
        "name": "HealthWest Caseworker(s)",
        "role": "Mental health evaluator(s)",
        "designation": "Neutral",
        "contact": "[VERIFY — HealthWest, Muskegon County]",
        "subpoena_required": True,
        "expected_testimony": [
            "Mental health evaluations of parties and/or L.D.W.",
            "Clinical observations and recommendations",
            "Compliance with treatment recommendations",
        ],
    },
]

PERSON_PATTERNS = [
    (re.compile(r'\b(officer|deputy|detective|sgt|sergeant|lt|lieutenant|captain)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', re.I), "Law Enforcement"),
    (re.compile(r'\b(dr|doctor|md|therapist|counselor|psychologist|psychiatrist)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', re.I), "Medical/Mental Health"),
    (re.compile(r'\b(caseworker|social worker|investigator)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', re.I), "CPS/Social Services"),
    (re.compile(r'\b(teacher|principal|school)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', re.I), "Education"),
]

EXCLUDE_NAMES = {"andrew", "pigors", "emily", "watson", "berry", "ronald", "barnes", "jennifer",
                 "mcneill", "rusco", "pamela", "ldw", "l.d.w.", "the", "court", "judge"}


def get_db_connection():
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn


def get_tables(conn):
    return [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE '%_fts_%'").fetchall()]


def discover_witnesses_from_db(conn, tables):
    """Mine DB for potential witnesses mentioned in evidence."""
    discovered = defaultdict(lambda: {"mentions": 0, "contexts": [], "source_tables": set()})

    # Search evidence_quotes for speaker names
    if "evidence_quotes" in tables:
        rows = conn.execute("""
            SELECT speaker, quote_text, evidence_category, date_ref
            FROM evidence_quotes
            WHERE speaker IS NOT NULL AND speaker != ''
            LIMIT 2000
        """).fetchall()
        for r in rows:
            speaker = str(r[0]).strip()
            if len(speaker) < 3 or speaker.lower() in EXCLUDE_NAMES:
                continue
            discovered[speaker]["mentions"] += 1
            discovered[speaker]["source_tables"].add("evidence_quotes")
            if r[1]:
                discovered[speaker]["contexts"].append(str(r[1])[:200])

    # Search for person names in text fields across tables
    text_tables = ["evidence_quotes", "impeachment_items", "contradiction_map", "master_csv_data"]
    for table in text_tables:
        if table not in tables:
            continue
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        text_cols = [c for c in cols if any(t in c.lower() for t in ["text", "content", "description", "note", "detail", "quote"])]
        if not text_cols:
            continue
        for tc in text_cols[:2]:
            try:
                rows = conn.execute(f'SELECT "{tc}" FROM "{table}" WHERE "{tc}" IS NOT NULL LIMIT 500').fetchall()
            except Exception:
                continue
            for row in rows:
                text = str(row[0])
                for pattern, role_type in PERSON_PATTERNS:
                    for match in pattern.finditer(text):
                        title = match.group(1)
                        name = match.group(2).strip()
                        full = f"{title} {name}".strip()
                        if name.lower() not in EXCLUDE_NAMES and len(name) > 2:
                            discovered[full]["mentions"] += 1
                            discovered[full]["source_tables"].add(table)
                            discovered[full]["role_type"] = role_type
                            discovered[full]["contexts"].append(text[:200])

    return discovered


def main():
    print("=" * 70)
    print("TOOL #213 — Witness List Compiler")
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 70)

    conn = get_db_connection()
    discovered_witnesses = {}
    db_stats = {}
    if conn:
        tables = get_tables(conn)
        discovered_witnesses = discover_witnesses_from_db(conn, tables)
        # Count evidence_quotes speakers
        try:
            speaker_count = conn.execute(
                "SELECT COUNT(DISTINCT speaker) FROM evidence_quotes WHERE speaker IS NOT NULL AND speaker != ''"
            ).fetchone()[0]
        except Exception:
            speaker_count = 0
        db_stats = {"tables": len(tables), "distinct_speakers": speaker_count,
                    "discovered_witnesses": len(discovered_witnesses)}
        conn.close()
        print(f"[DB] {db_stats['tables']} tables. {speaker_count} distinct speakers. {len(discovered_witnesses)} potential witnesses discovered.")
    else:
        print("[WARN] DB not found — using known witnesses only.")

    # Build discovered witness entries
    db_witnesses = []
    for name, info in sorted(discovered_witnesses.items(), key=lambda x: -x[1]["mentions"]):
        if info["mentions"] < 2:
            continue
        db_witnesses.append({
            "name": name,
            "role": info.get("role_type", "Witness (DB-discovered)"),
            "designation": "Unknown — requires investigation",
            "contact": "[VERIFY — discovered from database evidence]",
            "subpoena_required": True,
            "mentions_in_db": info["mentions"],
            "source_tables": list(info["source_tables"]),
            "sample_context": info["contexts"][:3] if info["contexts"] else [],
            "expected_testimony": [f"Testimony regarding matters referenced in {', '.join(info['source_tables'])}"],
        })

    all_witnesses = KNOWN_WITNESSES + db_witnesses[:20]

    # JSON report
    report = {
        "tool": "#213 — Witness List Compiler",
        "generated": datetime.now().isoformat(),
        "case_numbers": ["2024-001507-DC", "2023-5907-PP"],
        "court": "14th Circuit Court, Family Division, Muskegon County",
        "total_witnesses": len(all_witnesses),
        "known_witnesses": len(KNOWN_WITNESSES),
        "db_discovered_witnesses": len(db_witnesses),
        "db_stats": db_stats,
        "witnesses": all_witnesses,
    }
    json_path = REPORTS_DIR / "WITNESS_LIST.json"
    json_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"[OK] JSON: {json_path}")

    # MD report
    md = []
    md.append("# WITNESS LIST — Pigors v. Watson")
    md.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    md.append(f"**Case Numbers:** 2024-001507-DC, 2023-5907-PP")
    md.append(f"**Court:** 14th Circuit Court, Family Division, Muskegon County")
    md.append(f"**Total Witnesses:** {len(all_witnesses)}")
    md.append("")

    md.append("## Summary")
    md.append("")
    md.append("| # | Witness | Role | Designation | Subpoena? |")
    md.append("|---|---------|------|-------------|-----------|")
    for i, w in enumerate(all_witnesses, 1):
        md.append(f"| {i} | {w['name']} | {w['role']} | {w['designation']} | {'Yes' if w.get('subpoena_required') else 'No'} |")
    md.append("")

    md.append("---")
    md.append("\n## Detailed Witness Profiles")
    md.append("")
    for i, w in enumerate(all_witnesses, 1):
        md.append(f"### {i}. {w['name']}")
        md.append(f"- **Role:** {w['role']}")
        md.append(f"- **Designation:** {w['designation']}")
        md.append(f"- **Contact:** {w.get('contact', '[VERIFY]')}")
        md.append(f"- **Subpoena Required:** {'Yes' if w.get('subpoena_required') else 'No (party to the action)'}")
        if w.get("mentions_in_db"):
            md.append(f"- **DB Mentions:** {w['mentions_in_db']}")
            md.append(f"- **Source Tables:** {', '.join(w.get('source_tables', []))}")
        md.append(f"- **Expected Testimony:**")
        for t in w.get("expected_testimony", []):
            md.append(f"  - {t}")
        if w.get("sample_context"):
            md.append(f"- **Sample Context from DB:**")
            for ctx in w["sample_context"][:2]:
                md.append(f'  > "{ctx[:150]}..."')
        md.append("")

    md.append("---")
    md.append("\n## Subpoena Requirements")
    md.append("")
    subpoena_witnesses = [w for w in all_witnesses if w.get("subpoena_required")]
    md.append(f"**{len(subpoena_witnesses)} witnesses require subpoenas:**")
    md.append("")
    for w in subpoena_witnesses:
        md.append(f"- [ ] {w['name']} — {w.get('contact', '[VERIFY ADDRESS]')}")
    md.append("")
    md.append("> Subpoenas governed by MCR 2.506. Must be served at least 2 days before trial.")
    md.append("> Consider MCR 2.506(G) for subpoena of documents (subpoena duces tecum).")

    md.append("\n---")
    md.append(f"\n*Tool #213 — Witness List Compiler — {datetime.now().isoformat()}*")

    md_path = REPORTS_DIR / "WITNESS_LIST.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    print(f"[OK] MD:   {md_path}")
    print(f"\n[SUMMARY] {len(all_witnesses)} witnesses compiled ({len(KNOWN_WITNESSES)} known + {len(db_witnesses)} DB-discovered)")
    print(f"  Subpoena required: {len(subpoena_witnesses)}")
    print("[DONE] Tool #213 complete.")


if __name__ == "__main__":
    main()
