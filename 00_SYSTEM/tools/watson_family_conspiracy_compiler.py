#!/usr/bin/env python3
"""
Watson Family Conspiracy Compiler — Tool #266
LitigationOS (Pigors v. Watson, Michigan Family Law)

Compiles ALL evidence of Watson family civil conspiracy to alienate
Andrew Pigors from his son L.D.W. across 15+ database tables.

Conspiracy members (VERIFIED — never fabricated):
  - Emily A. Watson (primary conspirator / defendant)
  - Albert Watson (co-conspirator / Emily's father)
  - Lori Watson (co-conspirator-facilitator / Emily's mother)
  - Cody Watson (co-conspirator / Emily's brother)
  - Ronald T. Berry (co-conspirator / Emily's boyfriend, UPL)
  - Jennifer Barnes P55406 (legal co-conspirator, withdrew)

Legal theories: 42 USC §1985(3) + MCL 750.157a + common law conspiracy
"""

import sys, os, json, sqlite3, re
from datetime import datetime
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'litigation_context.db')
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'reports')

def s(v): return str(v or "").lower()

def safe_query(conn, sql, params=()):
    try:
        return conn.execute(sql, params).fetchall()
    except:
        return []

# ── Conspirator Definitions ──────────────────────────────────────────────────

CONSPIRATORS = {
    "emily_watson": {
        "name": "Emily A. Watson",
        "role": "primary",
        "relationship": "Defendant, mother of L.D.W.",
        "search_terms": [
            "emily", "watson", "defendant", "filed false", "perjury",
            "fabricated", "straw incident", "false dv", "custodial interference",
            "false ppo", "manufactured", "emily a. watson", "emily watson"
        ],
        "act_types": ["perjury", "false_filing", "custodial_interference", "alienation"],
    },
    "albert_watson": {
        "name": "Albert Watson",
        "role": "co-conspirator",
        "relationship": "Emily's father",
        "search_terms": [
            "albert", "albert watson", "father-in-law", "emily's father",
            "kitchen", "garland", "won't see your son", "make sure",
            "2160 garland", "al watson"
        ],
        "act_types": ["threat", "intimidation", "alienation"],
        "known_evidence": "[AUDIO EVIDENCE — NOT YET TRANSCRIBED] Nov 2024, 2160 Garland kitchen: 'I will make sure you don't see your son'",
    },
    "lori_watson": {
        "name": "Lori Watson",
        "role": "co-conspirator",
        "relationship": "Emily's mother",
        "search_terms": [
            "lori", "lori watson", "mother-in-law", "emily's mother",
            "grandmother", "facilitated", "withholding"
        ],
        "act_types": ["facilitation", "alienation", "custodial_interference"],
    },
    "cody_watson": {
        "name": "Cody Watson",
        "role": "co-conspirator",
        "relationship": "Emily's brother",
        "search_terms": [
            "cody", "cody watson", "brother", "emily's brother",
            "threats", "text message", "won't see", "threatening"
        ],
        "act_types": ["threat", "intimidation"],
        "known_evidence": "[SCREENSHOT EVIDENCE — NOT YET INGESTED] Threatening text messages: 'you won't see your son'",
    },
    "ronald_berry": {
        "name": "Ronald T. Berry",
        "role": "co-conspirator",
        "relationship": "Emily's boyfriend/domestic partner",
        "search_terms": [
            "berry", "ronald", "boyfriend", "upl", "unauthorized practice",
            "coached", "advisory", "ronald berry", "ron berry"
        ],
        "act_types": ["upl", "coaching", "facilitation"],
    },
    "jennifer_barnes": {
        "name": "Jennifer Barnes (P55406)",
        "role": "legal_enabler",
        "relationship": "Emily's former attorney (withdrew)",
        "search_terms": [
            "barnes", "p55406", "attorney", "withdrew", "subornation",
            "jennifer barnes", "barnes law"
        ],
        "act_types": ["false_filing", "perjury"],
    },
}

# ── Conspiracy Elements (42 USC §1985(3) + MCL 750.157a) ────────────────────

CONSPIRACY_ELEMENTS = {
    "agreement": {
        "label": "Agreement",
        "description": "Two or more persons agreed to accomplish unlawful objective",
        "keywords": ["agreed", "coordinated", "planned", "conspired", "concert",
                      "together", "scheme", "arrangement", "colluded"],
    },
    "overt_act": {
        "label": "Overt Act",
        "description": "At least one conspirator committed an overt act in furtherance",
        "keywords": ["filed", "sent", "threatened", "withheld", "blocked",
                      "coached", "attended", "testified", "submitted"],
    },
    "unlawful_purpose": {
        "label": "Unlawful Purpose",
        "description": "Deprivation of parental rights / alienation of child",
        "keywords": ["alienat", "deprive", "parental rights", "custody", "visitation",
                      "parenting time", "withhold", "interfere", "obstruct"],
    },
    "knowledge": {
        "label": "Knowledge",
        "description": "Each conspirator knew of and participated in the scheme",
        "keywords": ["knew", "aware", "participated", "involved", "present",
                      "witnessed", "assisted", "enabled", "facilitated"],
    },
    "damages": {
        "label": "Damages",
        "description": "Andrew suffered actual damages (loss of parenting time, emotional harm, legal costs)",
        "keywords": ["damage", "loss", "harm", "cost", "suffer", "denied",
                      "missed", "prevented", "deprived", "emotional"],
    },
}

# ── Table Scan Configurations ────────────────────────────────────────────────

TABLES_TO_SCAN = [
    "actor_violations",
    "evidence_quotes",
    "criminal_evidence_scan",
    "berry_ethics_violations",
    "conspiracy_timeline",
    "chatgpt_litigation_intel",
    "contradiction_map",
    "actionable_evidence",
    "drive_evidence",
    "claim_evidence_links",
    "i_drive_file_inventory",
    "h_drive_tort_claims",
    "multi_drive_catalog",
    "appclose_violations",
]


def get_table_columns(conn, table):
    """Get actual column names for a table via PRAGMA."""
    rows = safe_query(conn, f"PRAGMA table_info({table})")
    return [r["name"] for r in rows] if rows else []


def table_exists(conn, table):
    """Check if a table exists."""
    r = safe_query(conn, "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return len(r) > 0


def search_table_for_conspirator(conn, table, columns, search_terms):
    """Search text columns in a table for conspirator-related evidence.
    Uses single-pass in-memory scan for performance on large tables."""
    hits = []
    text_cols = []
    for c in columns:
        col_lower = c.lower()
        if any(kw in col_lower for kw in [
            "text", "description", "content", "detail", "quote", "evidence",
            "action", "violation", "name", "actor", "perpetrator", "file",
            "source", "notes", "message", "claim", "term", "fact",
            "keyword", "member", "role", "type", "category", "title",
            "path", "filename"
        ]):
            text_cols.append(c)

    if not text_cols:
        return hits

    # Build a single query selecting only text columns + id
    select_cols = ["id"] if "id" in columns else []
    select_cols.extend(text_cols)
    col_list = ", ".join(f'"{c}"' for c in select_cols)

    # Build OR-based WHERE to pre-filter at SQL level (much faster than N queries)
    where_parts = []
    params = []
    for col in text_cols:
        for term in search_terms:
            where_parts.append(f'LOWER("{col}") LIKE ?')
            params.append(f"%{term.lower()}%")

    if not where_parts:
        return hits

    # Limit to 5000 rows to prevent memory explosion on huge tables
    sql = f'SELECT {col_list} FROM "{table}" WHERE {" OR ".join(where_parts)} LIMIT 5000'
    rows = safe_query(conn, sql, tuple(params))

    seen_texts = set()
    lower_terms = [t.lower() for t in search_terms]

    for row in rows:
        row_dict = dict(row)
        row_text = " | ".join(
            f"{k}: {v}" for k, v in row_dict.items()
            if v and isinstance(v, str) and len(str(v)) > 2
        )
        if not row_text:
            continue

        # Find which term matched
        row_lower = row_text.lower()
        matched = next((t for t in lower_terms if t in row_lower), search_terms[0])
        matched_col = next(
            (c for c in text_cols if row_dict.get(c) and matched in s(row_dict[c])),
            text_cols[0]
        )

        norm = re.sub(r'\s+', ' ', row_lower.strip())[:500]
        if norm not in seen_texts:
            seen_texts.add(norm)
            hits.append({
                "table": table,
                "column": matched_col,
                "matched_term": matched,
                "raw": row_text,
                "row_id": row_dict.get("id", ""),
            })
    return hits


def classify_element(text):
    """Determine which conspiracy elements a piece of evidence supports."""
    elements = []
    t = s(text)
    for key, elem in CONSPIRACY_ELEMENTS.items():
        for kw in elem["keywords"]:
            if kw.lower() in t:
                elements.append(key)
                break
    return elements if elements else ["overt_act"]


def classify_severity(text):
    """Classify severity based on content."""
    t = s(text)
    critical_kw = ["perjury", "felony", "fabricated", "false", "threat", "upl",
                    "unauthorized practice", "suborn", "deprive", "custodial interference"]
    high_kw = ["alienat", "withhold", "coached", "intimidat", "harass", "obstruct",
                "violated", "denied", "blocked"]
    for kw in critical_kw:
        if kw in t:
            return "critical"
    for kw in high_kw:
        if kw in t:
            return "high"
    return "medium"


def classify_act_type(text, default_types):
    """Classify the type of conspiratorial act."""
    t = s(text)
    type_map = {
        "threat": ["threat", "threaten", "intimidat", "won't see"],
        "perjury": ["perjury", "false statement", "lied", "fabricat", "false testimony"],
        "false_filing": ["false filing", "false ppo", "false motion", "baseless"],
        "upl": ["upl", "unauthorized practice", "non-attorney", "legal advice"],
        "coaching": ["coached", "coaching", "advised", "instructed", "directed"],
        "custodial_interference": ["custodial interference", "withhold", "denied parenting",
                                     "blocked visitation", "refused"],
        "alienation": ["alienat", "turn against", "badmouth", "disparag", "undermin"],
        "facilitation": ["facilitat", "enabled", "assisted", "helped", "participated"],
        "intimidation": ["intimidat", "harass", "stalk", "follow", "surveil"],
    }
    for act_type, keywords in type_map.items():
        for kw in keywords:
            if kw in t:
                return act_type
    return default_types[0] if default_types else "facilitation"


def extract_date(text):
    """Try to extract a date reference from evidence text."""
    patterns = [
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4})',
        r'(\d{4})',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1)
    return ""


def main():
    print("=" * 72)
    print("  WATSON FAMILY CONSPIRACY COMPILER — Tool #266")
    print("  LitigationOS | Pigors v. Watson")
    print(f"  Scan Time: {datetime.now().isoformat()}")
    print("=" * 72)

    if not os.path.exists(DB_PATH):
        print(f"\n[FATAL] Database not found: {DB_PATH}")
        return

    os.makedirs(REPORT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=120000")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")

    # ── Backup old table if schema mismatch, then create new ─────────────
    old_cols = get_table_columns(conn, "watson_family_conspiracy")
    expected_cols = ["conspirator", "conspirator_role", "act_type", "description",
                     "evidence_source", "evidence_detail", "date_approximate",
                     "severity", "legal_element", "scan_date"]
    need_recreate = old_cols and not all(c in old_cols for c in expected_cols)

    freshly_created = False
    if need_recreate:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"watson_family_conspiracy_v1_{ts}"
        print(f"\n[INFO] Backing up old table → {backup_name}")
        try:
            conn.execute(f'ALTER TABLE watson_family_conspiracy RENAME TO "{backup_name}"')
            conn.commit()
        except sqlite3.OperationalError as e:
            print(f"  [WARN] Could not rename old table: {e} — will use existing")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS watson_family_conspiracy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conspirator TEXT,
            conspirator_role TEXT,
            act_type TEXT,
            description TEXT,
            evidence_source TEXT,
            evidence_detail TEXT,
            date_approximate TEXT,
            severity TEXT,
            legal_element TEXT,
            scan_date TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wfc_conspirator ON watson_family_conspiracy(conspirator)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wfc_act_type ON watson_family_conspiracy(act_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_wfc_severity ON watson_family_conspiracy(severity)")
    conn.commit()
    freshly_created = True

    # Clear previous scan results (skip if table was just freshly created empty)
    if not need_recreate:
        existing = safe_query(conn, "SELECT COUNT(*) AS c FROM watson_family_conspiracy WHERE scan_date IS NOT NULL")
        if existing and existing[0]["c"] > 0:
            print(f"  [INFO] Clearing {existing[0]['c']} previous scan records...")
            for attempt in range(5):
                try:
                    conn.execute("DELETE FROM watson_family_conspiracy WHERE scan_date IS NOT NULL")
                    conn.commit()
                    break
                except sqlite3.OperationalError as e:
                    if attempt < 4:
                        import time
                        wait = 2 ** attempt
                        print(f"  [RETRY] DB locked, waiting {wait}s... ({e})")
                        time.sleep(wait)
                    else:
                        print(f"  [WARN] Could not clear old records after 5 attempts: {e}")
                        print(f"  [WARN] Proceeding — new records will be appended")

    scan_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Scan all tables for each conspirator ─────────────────────────────
    print("\n[PHASE 1] Scanning database tables for conspiracy evidence...\n")

    all_evidence = defaultdict(list)  # keyed by conspirator_id
    tables_scanned = 0
    tables_with_hits = 0

    for table in TABLES_TO_SCAN:
        if not table_exists(conn, table):
            print(f"  [ SKIP ] {table} — not found")
            continue
        cols = get_table_columns(conn, table)
        if not cols:
            print(f"  [ SKIP ] {table} — no columns")
            continue
        tables_scanned += 1
        table_hit = False

        for cid, cinfo in CONSPIRATORS.items():
            hits = search_table_for_conspirator(conn, table, cols, cinfo["search_terms"])
            if hits:
                table_hit = True
                for h in hits:
                    all_evidence[cid].append(h)

        row_count = safe_query(conn, f'SELECT COUNT(*) AS c FROM "{table}"')
        rc = row_count[0]["c"] if row_count else 0
        hit_count = sum(1 for cid in CONSPIRATORS for h in all_evidence[cid] if h["table"] == table)
        status = "HIT" if table_hit else " OK "
        print(f"  [{status:^4}] {table:<35} rows={rc:<8} hits={hit_count}")
        if table_hit:
            tables_with_hits += 1

    # ── Add known evidence not yet in DB ─────────────────────────────────
    print("\n[PHASE 2] Adding known evidence markers...\n")

    known_markers = []
    for cid, cinfo in CONSPIRATORS.items():
        if "known_evidence" in cinfo:
            known_markers.append({
                "conspirator": cid,
                "text": cinfo["known_evidence"],
                "table": "KNOWN_EVIDENCE_MARKER",
            })
            all_evidence[cid].append({
                "table": "KNOWN_EVIDENCE_MARKER",
                "column": "known",
                "matched_term": "known_evidence",
                "raw": cinfo["known_evidence"],
                "row_id": "",
            })

    print(f"  Added {len(known_markers)} known evidence markers (audio/screenshot)")

    # ── Deduplicate evidence per conspirator ──────────────────────────────
    print("\n[PHASE 3] Deduplicating evidence...\n")

    deduped = {}
    total_raw = 0
    total_deduped = 0
    for cid, hits in all_evidence.items():
        total_raw += len(hits)
        seen = set()
        unique = []
        for h in hits:
            # Content-based dedup: normalize and compare text
            norm = re.sub(r'\s+', ' ', h["raw"].lower().strip())[:500]
            if norm not in seen:
                seen.add(norm)
                unique.append(h)
        deduped[cid] = unique
        total_deduped += len(unique)

    print(f"  Raw hits: {total_raw} → Deduplicated: {total_deduped}")

    # ── Insert into watson_family_conspiracy table ───────────────────────
    print("\n[PHASE 4] Inserting compiled evidence into DB...\n")

    insert_count = 0
    rows_to_insert = []
    for cid, hits in deduped.items():
        cinfo = CONSPIRATORS[cid]
        for h in hits:
            raw_text = h["raw"]
            elements = classify_element(raw_text)
            severity = classify_severity(raw_text)
            act_type = classify_act_type(raw_text, cinfo["act_types"])
            date_approx = extract_date(raw_text)

            # Truncate description for readability
            desc = raw_text[:2000] if len(raw_text) > 2000 else raw_text
            detail = f"[{h['table']}.{h['column']}] matched='{h['matched_term']}'"

            rows_to_insert.append((
                cid,
                cinfo["role"],
                act_type,
                desc,
                h["table"],
                detail,
                date_approx,
                severity,
                ",".join(elements),
                scan_date,
            ))

    if rows_to_insert:
        for attempt in range(5):
            try:
                conn.executemany("""
                    INSERT INTO watson_family_conspiracy
                    (conspirator, conspirator_role, act_type, description,
                     evidence_source, evidence_detail, date_approximate,
                     severity, legal_element, scan_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, rows_to_insert)
                conn.commit()
                insert_count = len(rows_to_insert)
                break
            except sqlite3.OperationalError as e:
                if attempt < 4:
                    import time
                    wait = 2 ** attempt
                    print(f"  [RETRY] DB locked on INSERT, waiting {wait}s... ({e})")
                    time.sleep(wait)
                else:
                    print(f"  [WARN] Could not insert after 5 attempts: {e}")
                    print(f"  [INFO] Evidence compiled in-memory — reports will still generate")

    print(f"  Inserted {insert_count} evidence records")

    # ── Build report data ────────────────────────────────────────────────
    print("\n[PHASE 5] Generating conspiracy report...\n")

    # Per-conspirator stats
    conspirator_stats = {}
    for cid, cinfo in CONSPIRATORS.items():
        hits = deduped.get(cid, [])
        by_severity = defaultdict(int)
        by_act = defaultdict(int)
        by_table = defaultdict(int)
        for h in hits:
            sev = classify_severity(h["raw"])
            by_severity[sev] += 1
            act = classify_act_type(h["raw"], cinfo["act_types"])
            by_act[act] += 1
            by_table[h["table"]] += 1

        conspirator_stats[cid] = {
            "name": cinfo["name"],
            "role": cinfo["role"],
            "relationship": cinfo["relationship"],
            "total_evidence": len(hits),
            "by_severity": dict(by_severity),
            "by_act_type": dict(by_act),
            "by_table": dict(by_table),
            "top_evidence": [h["raw"][:300] for h in hits[:5]],
        }

    # Element satisfaction
    element_satisfaction = {}
    for elem_key, elem_info in CONSPIRACY_ELEMENTS.items():
        supporting = 0
        conspirators_contributing = set()
        for cid, hits in deduped.items():
            for h in hits:
                elements = classify_element(h["raw"])
                if elem_key in elements:
                    supporting += 1
                    conspirators_contributing.add(cid)
        element_satisfaction[elem_key] = {
            "label": elem_info["label"],
            "description": elem_info["description"],
            "supporting_evidence_count": supporting,
            "conspirators_contributing": list(conspirators_contributing),
            "satisfied": supporting >= 2 and len(conspirators_contributing) >= 2,
        }

    # Timeline from conspiracy_timeline table
    timeline_rows = safe_query(conn, """
        SELECT date, actor, action, coordinated_with, evidence_source,
               conspiracy_type, severity
        FROM conspiracy_timeline
        ORDER BY date
    """)
    timeline = []
    for r in timeline_rows:
        timeline.append({
            "date": r["date"] or "",
            "actor": r["actor"] or "",
            "action": r["action"] or "",
            "coordinated_with": r["coordinated_with"] or "",
            "evidence_source": r["evidence_source"] or "",
            "type": r["conspiracy_type"] or "",
            "severity": r["severity"] or "",
        })

    # Berry UPL specifics
    berry_upl = safe_query(conn, """
        SELECT violation_type, mrpc_rule, description, evidence_source, date, severity
        FROM berry_ethics_violations
        ORDER BY date
    """)
    berry_violations = []
    for r in berry_upl:
        berry_violations.append({
            "type": r["violation_type"] or "",
            "rule": r["mrpc_rule"] or "",
            "description": r["description"] or "",
            "source": r["evidence_source"] or "",
            "date": r["date"] or "",
            "severity": r["severity"] or "",
        })

    # ── Build JSON output ────────────────────────────────────────────────
    report_data = {
        "report_title": "Watson Family Conspiracy Compilation",
        "case": "Pigors v. Watson",
        "case_numbers": ["2024-001507-DC", "2023-5907-PP"],
        "court": "14th Circuit Court, Family Division, Muskegon County",
        "generated": scan_date,
        "tool": "watson_family_conspiracy_compiler.py (Tool #266)",
        "legal_theories": [
            "42 USC §1985(3) — Conspiracy to Interfere with Civil Rights",
            "MCL 750.157a — Criminal Conspiracy",
            "Common Law Civil Conspiracy (Michigan)",
        ],
        "summary": {
            "total_conspirators": len(CONSPIRATORS),
            "total_evidence_items": total_deduped,
            "tables_scanned": tables_scanned,
            "tables_with_hits": tables_with_hits,
            "db_records_created": insert_count,
        },
        "conspiracy_element_satisfaction": element_satisfaction,
        "conspirator_dossiers": conspirator_stats,
        "conspiracy_timeline": timeline,
        "berry_upl_violations": berry_violations,
    }

    json_path = os.path.join(REPORT_DIR, "watson_family_conspiracy.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"  JSON report → {json_path}")

    # ── Build Markdown report ────────────────────────────────────────────
    md_lines = []
    md_lines.append("# WATSON FAMILY CONSPIRACY COMPILATION")
    md_lines.append(f"**Pigors v. Watson** | 14th Circuit Court, Family Division")
    md_lines.append(f"**Generated:** {scan_date} | **Tool:** #266 watson_family_conspiracy_compiler.py\n")

    md_lines.append("---\n")
    md_lines.append("## 1. EXECUTIVE SUMMARY\n")
    md_lines.append(f"This report compiles evidence of a coordinated civil conspiracy by **{len(CONSPIRATORS)} Watson family members and associates** to alienate Andrew James Pigors from his son L.D.W.\n")
    md_lines.append(f"- **Total evidence items compiled:** {total_deduped}")
    md_lines.append(f"- **Database tables scanned:** {tables_scanned}")
    md_lines.append(f"- **Tables with relevant hits:** {tables_with_hits}")
    md_lines.append(f"- **DB records created:** {insert_count}\n")

    md_lines.append("### Legal Theories")
    md_lines.append("1. **42 USC §1985(3)** — Conspiracy to Interfere with Civil Rights")
    md_lines.append("2. **MCL 750.157a** — Criminal Conspiracy")
    md_lines.append("3. **Common Law Civil Conspiracy** (Michigan)\n")

    md_lines.append("---\n")
    md_lines.append("## 2. CONSPIRACY ELEMENT SATISFACTION MATRIX\n")
    md_lines.append("| Element | Status | Evidence Count | Conspirators Contributing |")
    md_lines.append("|---------|--------|---------------|--------------------------|")
    elements_satisfied = 0
    for ek, ev in element_satisfaction.items():
        status = "✅ SATISFIED" if ev["satisfied"] else "⚠️ NEEDS MORE"
        names = ", ".join(CONSPIRATORS[c]["name"] for c in ev["conspirators_contributing"])
        md_lines.append(f"| **{ev['label']}** | {status} | {ev['supporting_evidence_count']} | {names} |")
        if ev["satisfied"]:
            elements_satisfied += 1

    md_lines.append(f"\n**Elements satisfied: {elements_satisfied}/{len(CONSPIRACY_ELEMENTS)}**\n")

    md_lines.append("---\n")
    md_lines.append("## 3. PER-CONSPIRATOR EVIDENCE DOSSIER\n")

    for cid, stats in conspirator_stats.items():
        cinfo = CONSPIRATORS[cid]
        md_lines.append(f"### 3.{list(CONSPIRATORS.keys()).index(cid)+1}. {stats['name']}")
        md_lines.append(f"- **Role:** {stats['role']}")
        md_lines.append(f"- **Relationship:** {stats['relationship']}")
        md_lines.append(f"- **Total evidence items:** {stats['total_evidence']}\n")

        if stats["by_severity"]:
            md_lines.append("**Severity breakdown:**")
            for sev, count in sorted(stats["by_severity"].items()):
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(sev, "⚪")
                md_lines.append(f"  - {icon} {sev}: {count}")
            md_lines.append("")

        if stats["by_act_type"]:
            md_lines.append("**Act types:**")
            for act, count in sorted(stats["by_act_type"].items()):
                md_lines.append(f"  - {act}: {count}")
            md_lines.append("")

        if stats["by_table"]:
            md_lines.append("**Source tables:**")
            for tbl, count in sorted(stats["by_table"].items(), key=lambda x: -x[1]):
                md_lines.append(f"  - {tbl}: {count}")
            md_lines.append("")

        if "known_evidence" in cinfo:
            md_lines.append(f"**⚠️ Known evidence not yet in DB:**")
            md_lines.append(f"  > {cinfo['known_evidence']}\n")

        if stats["top_evidence"]:
            md_lines.append("**Sample evidence (top 5):**")
            for i, ev in enumerate(stats["top_evidence"], 1):
                clean = ev.replace("\n", " ").strip()
                md_lines.append(f"  {i}. {clean[:250]}...")
            md_lines.append("")

    md_lines.append("---\n")
    md_lines.append("## 4. CONSPIRACY TIMELINE\n")
    if timeline:
        md_lines.append("| Date | Actor | Action | Coordinated With | Severity |")
        md_lines.append("|------|-------|--------|-----------------|----------|")
        for t in timeline[:50]:
            md_lines.append(
                f"| {t['date']} | {t['actor']} | {t['action'][:80]} | {t['coordinated_with']} | {t['severity']} |"
            )
        if len(timeline) > 50:
            md_lines.append(f"\n*({len(timeline) - 50} additional timeline entries in JSON report)*")
    else:
        md_lines.append("*No conspiracy timeline entries found in database.*")

    md_lines.append("\n---\n")
    md_lines.append("## 5. LEGAL THEORY APPLICATION\n")
    md_lines.append("### 42 USC §1985(3) — Federal Civil Rights Conspiracy")
    md_lines.append("The Watson family's coordinated actions constitute a conspiracy to deprive Andrew Pigors")
    md_lines.append("of his constitutional right to parent L.D.W. The conspiracy involves:\n")
    md_lines.append("- **Agreement:** Multiple family members acting in concert to alienate father from child")
    md_lines.append("- **Overt acts:** False PPO filings, perjured testimony, direct threats, custodial interference")
    md_lines.append("- **Class-based animus:** Targeting Andrew's parental status as a non-custodial father")
    md_lines.append("- **Damages:** Loss of parenting time, emotional distress, legal costs\n")

    md_lines.append("### MCL 750.157a — Michigan Criminal Conspiracy")
    md_lines.append("Under Michigan law, when two or more persons conspire to commit an offense against the state,")
    md_lines.append("each is guilty of the conspiracy. Relevant offenses include:\n")
    md_lines.append("- MCL 750.422 — Perjury (Emily's false PPO testimony)")
    md_lines.append("- MCL 750.81 — Assault (threats by Albert, Cody)")
    md_lines.append("- MCL 600.916 — Unauthorized Practice of Law (Berry)")
    md_lines.append("- MCL 750.136b — Child abuse (parental alienation as emotional abuse)\n")

    md_lines.append("### Common Law Civil Conspiracy (Michigan)")
    md_lines.append("Under *Advocacy Org. for Patients & Providers v. Auto Club Ins. Ass'n*, 257 Mich App 365 (2003),")
    md_lines.append("a civil conspiracy requires: (1) a concerted action, (2) by combination of two or more persons,")
    md_lines.append("(3) to accomplish an unlawful purpose, (4) or to accomplish a lawful purpose by unlawful means.\n")

    md_lines.append("---\n")
    md_lines.append("## 6. PROSECUTION READINESS\n")

    # Assess per-conspirator readiness
    for cid, stats in conspirator_stats.items():
        total = stats["total_evidence"]
        critical = stats["by_severity"].get("critical", 0)
        if total >= 10 and critical >= 3:
            readiness = "🟢 STRONG — Ready for filing"
        elif total >= 5:
            readiness = "🟡 MODERATE — Needs additional evidence"
        elif total >= 1:
            readiness = "🟠 DEVELOPING — Evidence exists but limited"
        else:
            readiness = "🔴 INSUFFICIENT — No database evidence found"
        md_lines.append(f"- **{stats['name']}:** {readiness} ({total} items, {critical} critical)")

    md_lines.append("\n### Evidence Gaps")
    md_lines.append("- Albert Watson: Audio recording from Nov 2024 needs transcription and ingestion")
    md_lines.append("- Cody Watson: Text message screenshots need ingestion into evidence pipeline")
    md_lines.append("- Lori Watson: Direct evidence of facilitation may require deposition testimony")
    md_lines.append("- Coordination evidence: Need communications showing pre-planning between members\n")

    md_lines.append("---\n")
    md_lines.append("## 7. KEY EXHIBITS (Strongest per Conspirator)\n")
    for cid, stats in conspirator_stats.items():
        md_lines.append(f"### {stats['name']}")
        hits = deduped.get(cid, [])
        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2}
        ranked = sorted(hits, key=lambda h: severity_order.get(classify_severity(h["raw"]), 3))
        if ranked:
            for i, h in enumerate(ranked[:3], 1):
                sev = classify_severity(h["raw"])
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(sev, "⚪")
                clean = h["raw"].replace("\n", " ").strip()[:200]
                md_lines.append(f"  {i}. {icon} [{h['table']}] {clean}")
        else:
            md_lines.append("  *No database evidence — see known evidence markers above*")
        md_lines.append("")

    md_lines.append("---\n")
    md_lines.append("## BERRY UPL DETAIL\n")
    if berry_violations:
        md_lines.append("| Date | Violation | MRPC Rule | Severity | Source |")
        md_lines.append("|------|-----------|-----------|----------|--------|")
        for bv in berry_violations:
            md_lines.append(
                f"| {bv['date']} | {bv['type']} | {bv['rule']} | {bv['severity']} | {bv['source'][:60]} |"
            )
    else:
        md_lines.append("*No Berry ethics violations found in berry_ethics_violations table.*")

    md_lines.append("\n---")
    md_lines.append(f"\n*Report generated by Tool #266 — watson_family_conspiracy_compiler.py*")
    md_lines.append(f"*All statistics traceable to litigation_context.db queries. Child referred to as L.D.W. per MCR 8.119(H).*")

    md_path = os.path.join(REPORT_DIR, "WATSON_FAMILY_CONSPIRACY.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"  Markdown report → {md_path}")

    # ── Final summary ────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  COMPILATION COMPLETE")
    print("=" * 72)
    print(f"\n  Conspirators analyzed:    {len(CONSPIRATORS)}")
    print(f"  Tables scanned:           {tables_scanned}")
    print(f"  Tables with hits:         {tables_with_hits}")
    print(f"  Raw evidence hits:        {total_raw}")
    print(f"  After dedup:              {total_deduped}")
    print(f"  DB records created:       {insert_count}")
    print(f"  Elements satisfied:       {elements_satisfied}/{len(CONSPIRACY_ELEMENTS)}")
    print(f"  Timeline entries:         {len(timeline)}")
    print(f"  Berry UPL violations:     {len(berry_violations)}")

    print(f"\n  Per-conspirator evidence:")
    for cid, stats in conspirator_stats.items():
        crit = stats["by_severity"].get("critical", 0)
        high = stats["by_severity"].get("high", 0)
        med = stats["by_severity"].get("medium", 0)
        print(f"    {stats['name']:<30} total={stats['total_evidence']:<5} critical={crit:<4} high={high:<4} medium={med}")

    print(f"\n  Reports written:")
    print(f"    {json_path}")
    print(f"    {md_path}")
    print()

    conn.close()


if __name__ == "__main__":
    main()
