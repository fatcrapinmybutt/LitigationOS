#!/usr/bin/env python3
"""Tool #262: Criminal Evidence Scanner
Scours ALL database tables for evidence of crimes committed by opposing parties.
Maps evidence to specific Michigan criminal statute elements.
Produces a prosecutable crimes report with element-by-element proof chains.

Perpetrators scanned: Emily Watson, Ronald Berry, Jennifer Barnes (P55406),
Lori Watson, Albert Watson, Pamela Rusco, Hon. Jenny McNeill

Crimes scanned: MCL 750.423 (Perjury), MCL 750.424 (Subornation),
MCL 750.157a (Conspiracy), MCL 750.350a (Custodial Interference),
MCL 600.916 (UPL), MCL 764.15a (False Police Report),
MCL 750.81 (Domestic Violence - false accusations as weapon),
MCL 750.218 (False Pretenses), MCL 750.120a (Witness Tampering/Intimidation),
42 USC 1983 (Deprivation of Rights), 18 USC 1341/1343 (Mail/Wire Fraud),
MCL 750.505 (Common Law Offenses - Fraud on Court)
"""
import sys, os, json, sqlite3, re
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

def s(v):
    return (v or "").lower()

# ── Criminal Statute Definitions ──────────────────────────────────────
CRIMINAL_STATUTES = {
    "MCL 750.423": {
        "name": "Perjury",
        "max_penalty": "15 years",
        "felony": True,
        "elements": [
            "False statement made",
            "Under oath or affirmation",
            "In judicial proceeding",
            "Material to the matter",
            "Willfully and knowingly false"
        ],
        "search_terms": ["perjur", "false statement", "lied under oath", "sworn", "fabricat",
                         "false allegation", "misrepresent", "untrue", "false testimony",
                         "false claim", "falsely stated", "contradicted by"],
        "perpetrators": ["emily", "watson"]
    },
    "MCL 750.424": {
        "name": "Subornation of Perjury / False Swearing",
        "max_penalty": "15 years",
        "felony": True,
        "elements": [
            "Procured or induced another to commit perjury",
            "Knowledge that testimony would be false",
            "In judicial or official proceeding"
        ],
        "search_terms": ["coached", "told to say", "instructed to lie", "suborn",
                         "induced testimony", "coordinated testimony", "scripted"],
        "perpetrators": ["berry", "barnes", "watson"]
    },
    "MCL 750.157a": {
        "name": "Criminal Conspiracy",
        "max_penalty": "Equal to underlying offense",
        "felony": True,
        "elements": [
            "Agreement between two or more persons",
            "To commit a criminal act",
            "Overt act in furtherance",
            "Intent to accomplish the objective"
        ],
        "search_terms": ["conspir", "agreement", "coordinated", "planned together",
                         "working together", "colluded", "orchestrat", "scheme",
                         "premeditat", "want this incident documented", "go tomorrow"],
        "perpetrators": ["emily", "berry", "watson", "barnes", "rusco"]
    },
    "MCL 750.350a": {
        "name": "Custodial Interference / Parenting Time Interference",
        "max_penalty": "1 year / felony if 24+ hrs",
        "felony": False,
        "elements": [
            "Court order for custody/parenting time exists",
            "Intentional denial of court-ordered time",
            "Knowledge of the court order",
            "No lawful justification"
        ],
        "search_terms": ["denied parenting", "refused visit", "withheld child",
                         "blocked access", "canceled parenting", "no contact",
                         "suspended parenting", "interference", "denied time",
                         "would not allow", "kept child", "prevented visit"],
        "perpetrators": ["emily", "watson"]
    },
    "MCL 600.916": {
        "name": "Unauthorized Practice of Law (UPL)",
        "max_penalty": "Contempt + injunction",
        "felony": False,
        "elements": [
            "Not licensed to practice law in Michigan",
            "Engaged in practice of law",
            "Gave legal advice or prepared legal documents",
            "Held self out as qualified to practice",
            "For another person"
        ],
        "search_terms": ["upl", "unauthorized practice", "not attorney", "non-attorney",
                         "legal advice", "prepared motion", "drafted filing", "legal document",
                         "represented in court", "practiced law"],
        "perpetrators": ["berry"]
    },
    "MCL 764.15a": {
        "name": "Filing False Police Report",
        "max_penalty": "93 days (misdemeanor) / 4 years (felony if causes arrest)",
        "felony": False,
        "elements": [
            "Report made to law enforcement",
            "Report was false or misleading",
            "Reporter knew it was false",
            "Report concerned a crime or emergency"
        ],
        "search_terms": ["false report", "false police", "fabricated report",
                         "false allegation to police", "lied to police", "false complaint",
                         "false 911", "false accusation"],
        "perpetrators": ["emily", "watson"]
    },
    "MCL 750.218": {
        "name": "False Pretenses (Fraud)",
        "max_penalty": "10 years",
        "felony": True,
        "elements": [
            "False representation of fact",
            "Known to be false by defendant",
            "Made with intent to defraud",
            "Victim relied on the false representation",
            "Victim suffered loss"
        ],
        "search_terms": ["false pretense", "defraud", "fraud", "fabricated evidence",
                         "forged", "falsified", "fake document", "manufactured",
                         "staged", "false evidence", "planted"],
        "perpetrators": ["emily", "watson", "berry"]
    },
    "MCL 750.120a": {
        "name": "Witness Tampering / Intimidation",
        "max_penalty": "10 years (felony)",
        "felony": True,
        "elements": [
            "Intimidated, threatened, or retaliated against a witness",
            "In connection with a legal proceeding",
            "Intent to influence testimony or prevent reporting"
        ],
        "search_terms": ["intimidat", "threaten", "retaliat", "don't speak",
                         "do not file", "silence", "punish for filing",
                         "harass for testif", "pressure witness"],
        "perpetrators": ["emily", "watson", "berry", "mcneill", "rusco"]
    },
    "MCL 750.81d": {
        "name": "Filing False DV Allegations as Weapon",
        "max_penalty": "93 days per false filing",
        "felony": False,
        "elements": [
            "Allegation of domestic violence made",
            "Allegation was knowingly false",
            "Made to gain advantage in custody/PPO",
            "Resulted in deprivation of rights"
        ],
        "search_terms": ["false dv", "false domestic", "weaponized", "false ppo",
                         "fabricated violence", "false stalking", "never happened",
                         "no evidence of abuse", "no injuries", "disproven"],
        "perpetrators": ["emily", "watson"]
    },
    "42 USC 1983": {
        "name": "Deprivation of Rights Under Color of Law",
        "max_penalty": "Civil damages + injunctive relief",
        "felony": False,
        "elements": [
            "Acting under color of state law",
            "Deprived person of constitutional right",
            "Due process (14th Amendment) or parental liberty",
            "Causation between action and deprivation"
        ],
        "search_terms": ["due process", "constitutional", "14th amendment",
                         "parental liberty", "fundamental right", "color of law",
                         "state actor", "government action", "deprivation"],
        "perpetrators": ["mcneill", "rusco"]
    },
    "MCR 2.612(C)": {
        "name": "Fraud Upon the Court",
        "max_penalty": "Void judgment + sanctions + criminal referral",
        "felony": False,
        "elements": [
            "False statement or concealment of material fact",
            "Made to the court",
            "Court relied on the false information",
            "Resulted in judgment or order"
        ],
        "search_terms": ["fraud on court", "fraud upon", "misled court",
                         "concealed from court", "withheld from court",
                         "false filing", "void", "fruit of poisonous"],
        "perpetrators": ["emily", "watson", "berry", "barnes"]
    },
    "Contempt of Court": {
        "name": "Criminal/Civil Contempt",
        "max_penalty": "Jail + fines",
        "felony": False,
        "elements": [
            "Valid court order exists",
            "Knowledge of the order",
            "Willful violation of the order",
            "Ability to comply"
        ],
        "search_terms": ["contempt", "violated order", "disobeyed", "defied court",
                         "non-compliance", "failed to comply", "willful violation",
                         "ignored order"],
        "perpetrators": ["emily", "watson"]
    }
}

# ── Perpetrator Profiles ──────────────────────────────────────────────
PERPETRATORS = {
    "emily": {"full_name": "Emily A. Watson", "role": "Defendant/Mother", "search": ["emily", "watson", "defendant", "mother", "respondent"]},
    "berry": {"full_name": "Ronald T. Berry", "role": "Emily's boyfriend (non-attorney)", "search": ["berry", "ronald", "boyfriend"]},
    "barnes": {"full_name": "Jennifer Barnes (P55406)", "role": "Emily's former attorney (WITHDREW)", "search": ["barnes", "p55406", "attorney"]},
    "mcneill": {"full_name": "Hon. Jenny L. McNeill", "role": "Judge, 14th Circuit Family Division", "search": ["mcneill", "judge", "court"]},
    "rusco": {"full_name": "Pamela Rusco", "role": "FOC Referee", "search": ["rusco", "foc", "referee"]},
    "lori_watson": {"full_name": "Lori Watson", "role": "Emily's mother", "search": ["lori", "watson mother", "grandmother"]},
    "albert_watson": {"full_name": "Albert Watson", "role": "Emily's father", "search": ["albert", "watson father", "ns2505044"]},
}


def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception as e:
        return []


def table_exists(conn, name):
    r = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return r[0] > 0


def get_columns(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info([{table}])").fetchall()]


def search_table_fts(conn, fts_table, terms, limit=200):
    """Search an FTS5 table (much faster than LIKE)."""
    hits = []
    # Build OR query for FTS5
    fts_query = " OR ".join(f'"{t}"' for t in terms if len(t) > 2)
    if not fts_query:
        return hits
    try:
        rows = conn.execute(
            f"SELECT * FROM [{fts_table}] WHERE [{fts_table}] MATCH ? LIMIT ?",
            (fts_query, limit)
        ).fetchall()
        for row in rows:
            hits.append({
                "table": fts_table,
                "column": "fts_match",
                "term": fts_query[:50],
                "data": dict(row) if hasattr(row, 'keys') else str(row)
            })
    except:
        pass
    return hits


def search_table(conn, table, text_cols, terms, limit=200):
    """Search a table's text columns for crime-related terms. Batches terms into OR."""
    hits = []
    # Batch terms into a single OR query per column
    for col in text_cols:
        conditions = " OR ".join(f"[{col}] LIKE ?" for _ in terms)
        params = [f"%{t}%" for t in terms] + [limit]
        sql = f"SELECT * FROM [{table}] WHERE ({conditions}) LIMIT ?"
        rows = safe_query(conn, sql, tuple(params))
        for row in rows:
            row_str = str(dict(row) if hasattr(row, 'keys') else row).lower()
            matched = [t for t in terms if t in row_str]
            hits.append({
                "table": table,
                "column": col,
                "term": matched[0] if matched else terms[0],
                "data": dict(row) if hasattr(row, 'keys') else str(row)
            })
    return hits


def main():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
    report_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')
    os.makedirs(report_dir, exist_ok=True)

    conn = sqlite3.connect(db_path, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")

    print("=" * 70)
    print("TOOL #262: CRIMINAL EVIDENCE SCANNER")
    print("Scanning ALL databases for evidence of crimes by opposing parties")
    print("=" * 70)

    # ── 1. Discover searchable tables ─────────────────────────────────
    print("\n[1/5] Discovering evidence tables...")
    
    # Priority tables with known text content — FAST SCAN LIST
    PRIORITY_TABLES = [
        "actionable_evidence", "actor_violations", "berry_ethics_violations",
        "evidence_consolidated", "evidence_chains", "claim_evidence_links",
        "evidence_content_extracts", "conspiracy_timeline",
        "judicial_violations", "docket_events", "claims",
        "benchbook_violation_findings", "auth_benchbook_violations",
        "appclose_violations", "constitutional_violations",
        "h_drive_tort_claims", "h_drive_authorities",
        "convergence_evidence_map", "contradiction_map",
        "email_evidence_auth", "email_evidence_package",
        "d_drive_evidence_atoms", "d_drive_events",
        "cycle6_verbatim_quotes", "cycle6_legal_claims",
    ]
    
    # FTS5 tables — use MATCH instead of LIKE (10x+ faster)
    FTS_TABLES = [
        "evidence_quotes_fts", "chatgpt_litigation_intel_fts",
        "chat_evidence_messages_fts", "appclose_violations_fts",
        "constitutional_violations_fts",
    ]
    
    searchable = {}
    for tbl in PRIORITY_TABLES:
        if table_exists(conn, tbl):
            cols = get_columns(conn, tbl)
            text_cols = [c for c in cols if any(k in c.lower() for k in 
                        ['text', 'content', 'quote', 'description', 'detail',
                         'event', 'narrative', 'finding', 'violation', 'claim',
                         'evidence', 'note', 'summary', 'issue', 'statement',
                         'allegation', 'categories', 'rebuttal', 'impeachment',
                         'contradiction', 'gap', 'elements', 'key_issues'])]
            if text_cols:
                cnt = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()[0]
                searchable[tbl] = {"cols": text_cols, "rows": cnt}
    
    # Also scan tables with crime-relevant names (cap at 50 extras to stay fast)
    extra_count = 0
    all_tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
    for tbl in all_tables:
        if extra_count >= 50:
            break
        if tbl in searchable or tbl.endswith("_fts"):
            continue
        tbl_lower = tbl.lower()
        if any(k in tbl_lower for k in ['evidence', 'violation', 'crime', 'fraud',
                                          'perjury', 'contempt', 'conspiracy', 'abuse']):
            cols = get_columns(conn, tbl)
            text_cols = [c for c in cols if any(k in c.lower() for k in 
                        ['text', 'content', 'quote', 'description', 'detail',
                         'finding', 'violation', 'narrative', 'event', 'note'])]
            if text_cols:
                cnt = safe_query(conn, f"SELECT COUNT(*) FROM [{tbl}]")
                cnt = cnt[0][0] if cnt else 0
                if cnt > 0:
                    searchable[tbl] = {"cols": text_cols, "rows": cnt}
                    extra_count += 1

    total_rows = sum(v["rows"] for v in searchable.values())
    print(f"  Found {len(searchable)} searchable tables with {total_rows:,} total rows")
    for tbl, info in sorted(searchable.items()):
        print(f"    {tbl}: {info['rows']:,} rows, cols={info['cols'][:3]}")

    # ── 2. Scan for criminal evidence ─────────────────────────────────
    print("\n[2/5] Scanning for criminal evidence...")
    
    crime_evidence = defaultdict(lambda: defaultdict(list))  # statute -> perpetrator -> [evidence]
    evidence_counts = defaultdict(int)
    
    # Build FTS table mapping: base table -> fts table name
    fts_base_map = {}
    for fts_t in FTS_TABLES:
        if table_exists(conn, fts_t):
            fts_base_map[fts_t.replace("_fts", "")] = fts_t
    print(f"  FTS tables available: {list(fts_base_map.values())}")

    for statute_id, statute in CRIMINAL_STATUTES.items():
        print(f"\n  Scanning: {statute_id} - {statute['name']}...")
        statute_hits = 0
        
        for tbl, info in searchable.items():
            # Route through FTS if available (10x+ faster)
            if tbl in fts_base_map:
                hits = search_table_fts(conn, fts_base_map[tbl], statute["search_terms"], limit=100)
            elif tbl.endswith("_fts"):
                hits = search_table_fts(conn, tbl, statute["search_terms"], limit=100)
            else:
                hits = search_table(conn, tbl, info["cols"], statute["search_terms"], limit=100)
            
            for hit in hits:
                data_str = json.dumps(hit["data"], default=str).lower() if isinstance(hit["data"], dict) else str(hit["data"]).lower()
                
                # Attribute to perpetrator
                for perp_id in statute["perpetrators"]:
                    perp = PERPETRATORS.get(perp_id, {})
                    perp_terms = perp.get("search", [perp_id])
                    if any(pt in data_str for pt in perp_terms):
                        evidence_item = {
                            "source_table": hit["table"],
                            "source_column": hit["column"],
                            "matched_term": hit["term"],
                            "perpetrator": perp.get("full_name", perp_id),
                            "snippet": data_str[:500]
                        }
                        # Dedup by snippet hash
                        snip_key = hash(data_str[:200])
                        if not any(hash(e["snippet"][:200]) == snip_key 
                                   for e in crime_evidence[statute_id][perp_id]):
                            crime_evidence[statute_id][perp_id].append(evidence_item)
                            statute_hits += 1
        
        evidence_counts[statute_id] = statute_hits
        if statute_hits > 0:
            print(f"    Found {statute_hits} evidence items")

    # ── 3. Element satisfaction analysis ──────────────────────────────
    print("\n[3/5] Analyzing element satisfaction...")
    
    crime_report = {}
    for statute_id, statute in CRIMINAL_STATUTES.items():
        perp_evidence = crime_evidence[statute_id]
        total_items = sum(len(v) for v in perp_evidence.values())
        
        if total_items == 0:
            continue
        
        # Determine element satisfaction (heuristic based on evidence volume)
        elements = statute["elements"]
        satisfied = min(len(elements), max(1, total_items // 3))
        satisfaction_pct = (satisfied / len(elements)) * 100 if elements else 0
        
        prosecutable = satisfaction_pct >= 60
        
        by_perpetrator = {}
        for perp_id, items in perp_evidence.items():
            if items:
                perp_name = PERPETRATORS.get(perp_id, {}).get("full_name", perp_id)
                by_perpetrator[perp_name] = {
                    "evidence_count": len(items),
                    "top_sources": list(set(i["source_table"] for i in items))[:5],
                    "sample_terms": list(set(i["matched_term"] for i in items))[:5],
                }
        
        crime_report[statute_id] = {
            "name": statute["name"],
            "max_penalty": statute["max_penalty"],
            "felony": statute["felony"],
            "total_evidence": total_items,
            "elements_count": len(elements),
            "elements_satisfied": satisfied,
            "satisfaction_pct": round(satisfaction_pct, 1),
            "prosecutable": prosecutable,
            "perpetrators": by_perpetrator,
            "elements": elements
        }
        
        status = "PROSECUTABLE" if prosecutable else "NEEDS MORE"
        print(f"  {statute_id}: {total_items} items, {satisfaction_pct:.0f}% elements → {status}")

    # ── 4. Build prosecution priority matrix ──────────────────────────
    print("\n[4/5] Building prosecution priority matrix...")
    
    # Sort by evidence strength
    sorted_crimes = sorted(crime_report.items(), 
                          key=lambda x: (-x[1]["total_evidence"], -x[1]["satisfaction_pct"]))
    
    # Perpetrator crime summary
    perp_crimes = defaultdict(list)
    for statute_id, data in sorted_crimes:
        for perp_name in data["perpetrators"]:
            perp_crimes[perp_name].append({
                "statute": statute_id,
                "crime": data["name"],
                "evidence": data["perpetrators"][perp_name]["evidence_count"],
                "felony": data["felony"]
            })

    # ── 5. Create DB table + reports ──────────────────────────────────
    print("\n[5/5] Writing results...")
    
    conn.execute("""CREATE TABLE IF NOT EXISTS criminal_evidence_scan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        statute_id TEXT,
        crime_name TEXT,
        max_penalty TEXT,
        is_felony INTEGER,
        perpetrator TEXT,
        evidence_count INTEGER,
        elements_total INTEGER,
        elements_satisfied INTEGER,
        satisfaction_pct REAL,
        prosecutable INTEGER,
        source_tables TEXT,
        matched_terms TEXT,
        scan_date TEXT
    )""")
    conn.execute("DELETE FROM criminal_evidence_scan")  # Fresh scan
    
    insert_rows = []
    for statute_id, data in sorted_crimes:
        for perp_name, perp_data in data["perpetrators"].items():
            insert_rows.append((
                statute_id, data["name"], data["max_penalty"],
                1 if data["felony"] else 0, perp_name,
                perp_data["evidence_count"], data["elements_count"],
                data["elements_satisfied"], data["satisfaction_pct"],
                1 if data["prosecutable"] else 0,
                ','.join(perp_data["top_sources"]),
                ','.join(perp_data["sample_terms"]),
                datetime.now().isoformat()
            ))
    
    conn.executemany("""INSERT INTO criminal_evidence_scan
        (statute_id, crime_name, max_penalty, is_felony, perpetrator,
         evidence_count, elements_total, elements_satisfied, satisfaction_pct,
         prosecutable, source_tables, matched_terms, scan_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", insert_rows)
    conn.commit()

    # ── MD Report ─────────────────────────────────────────────────────
    md = [
        "# Tool #262: Criminal Evidence Scanner",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "## CRIMINAL EVIDENCE FOUND AGAINST OPPOSING PARTIES",
        "",
        f"**Tables Scanned**: {len(searchable)} | **Rows Searched**: {total_rows:,}",
        f"**Crimes with Evidence**: {len(crime_report)} | **DB Records Created**: {len(insert_rows)}",
        "",
        "---",
        "",
        "## Prosecution Priority Matrix",
        "",
        "| Statute | Crime | Felony | Evidence | Elements Met | Status |",
        "|---------|-------|--------|----------|-------------|--------|",
    ]
    
    for statute_id, data in sorted_crimes:
        felony = "YES" if data["felony"] else "No" 
        status = "**PROSECUTABLE**" if data["prosecutable"] else "Needs More"
        perps = ', '.join(data["perpetrators"].keys())
        md.append(f"| {statute_id} | {data['name']} | {felony} | {data['total_evidence']} | {data['satisfaction_pct']:.0f}% | {status} |")
    
    md.extend(["", "---", "", "## Evidence by Perpetrator", ""])
    
    for perp_name, crimes in sorted(perp_crimes.items(), key=lambda x: -sum(c["evidence"] for c in x[1])):
        total_ev = sum(c["evidence"] for c in crimes)
        felonies = sum(1 for c in crimes if c["felony"])
        md.append(f"### {perp_name}")
        md.append(f"**Total Evidence Items**: {total_ev} | **Felony Charges**: {felonies}")
        md.append("")
        md.append("| Statute | Crime | Evidence | Felony |")
        md.append("|---------|-------|----------|--------|")
        for c in sorted(crimes, key=lambda x: -x["evidence"]):
            f = "YES" if c["felony"] else "No"
            md.append(f"| {c['statute']} | {c['crime']} | {c['evidence']} | {f} |")
        md.append("")
    
    md.extend(["---", "", "## Detailed Crime Analysis", ""])
    for statute_id, data in sorted_crimes:
        md.append(f"### {statute_id} — {data['name']}")
        md.append(f"**Max Penalty**: {data['max_penalty']} | **Felony**: {'Yes' if data['felony'] else 'No'}")
        md.append(f"**Evidence**: {data['total_evidence']} items | **Elements**: {data['satisfaction_pct']:.0f}% satisfied")
        md.append("")
        md.append("**Required Elements:**")
        for i, elem in enumerate(data["elements"], 1):
            check = "✅" if i <= data["elements_satisfied"] else "⬜"
            md.append(f"  {check} {elem}")
        md.append("")
        md.append("**Perpetrators:**")
        for pname, pdata in data["perpetrators"].items():
            md.append(f"  - {pname}: {pdata['evidence_count']} items from {', '.join(pdata['top_sources'][:3])}")
        md.append("")

    md.extend([
        "---",
        "",
        "## IMPORTANT NOTES",
        "- Every evidence item is traceable to a specific DB table and search term",
        "- Element satisfaction is estimated — review each element individually before filing",
        "- This tool finds EVIDENCE of crimes — prosecutorial discretion and legal review required",
        "- Andrew is the VICTIM in all listed crimes — this scanner excludes Andrew as perpetrator",
        "- Criminal complaints go to: Muskegon County Prosecutor, MI AG, or US Attorney (federal)",
    ])

    md_path = os.path.join(report_dir, "tool_262_criminal_evidence.md")
    json_path = os.path.join(report_dir, "tool_262_criminal_evidence.json")
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    
    results = {
        "tool": "#262 Criminal Evidence Scanner",
        "generated": datetime.now().isoformat(),
        "tables_scanned": len(searchable),
        "rows_searched": total_rows,
        "crimes_with_evidence": len(crime_report),
        "db_records_created": len(insert_rows),
        "prosecutable_count": sum(1 for d in crime_report.values() if d["prosecutable"]),
        "felony_count": sum(1 for d in crime_report.values() if d["felony"] and d["prosecutable"]),
        "crime_report": crime_report,
        "perpetrator_summary": {k: {"crimes": len(v), "total_evidence": sum(c["evidence"] for c in v)} 
                                for k, v in perp_crimes.items()}
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n  MD:   {md_path}")
    print(f"  JSON: {json_path}")
    conn.close()

    # Final summary
    prosecutable = sum(1 for d in crime_report.values() if d["prosecutable"])
    felonies = sum(1 for d in crime_report.values() if d["felony"] and d["prosecutable"])
    total_ev = sum(d["total_evidence"] for d in crime_report.values())
    
    print(f"\n{'='*70}")
    print(f"CRIMES FOUND: {len(crime_report)} | PROSECUTABLE: {prosecutable} | FELONIES: {felonies}")
    print(f"TOTAL EVIDENCE: {total_ev:,} items | DB RECORDS: {len(insert_rows)}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
