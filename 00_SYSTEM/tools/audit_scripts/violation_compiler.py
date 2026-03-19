#!/usr/bin/env python3
"""
VIOLATION COMPILATION REPORT GENERATOR
Queries litigation_context.db for all violations by:
  Emily Watson, Ronald Berry, Jennifer Barnes, Judge McNeill
Outputs structured Markdown report.
"""
import sys, os, sqlite3, textwrap
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB = r'C:\Users\andre\LitigationOS\litigation_context.db'
OUT = r'C:\Users\andre\LitigationOS\temp\VIOLATION_COMPILATION.md'

def get_conn():
    conn = sqlite3.connect(DB, timeout=120)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def safe_query(conn, sql, params=(), label="query"):
    try:
        rows = conn.execute(sql, params).fetchall()
        return rows
    except Exception as e:
        print(f"  [WARN] {label}: {e}")
        return []

def truncate(text, maxlen=300):
    if not text:
        return ""
    text = str(text).replace('\n', ' ').strip()
    if len(text) > maxlen:
        return text[:maxlen] + "..."
    return text

def main():
    conn = get_conn()
    report_lines = []
    summary_counts = {}

    def w(line=""):
        report_lines.append(line)

    w(f"# VIOLATION COMPILATION REPORT")
    w(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    w(f"**Database:** litigation_context.db")
    w(f"**Case:** Pigors v. Watson (2024-001507-DC)")
    w()
    w("---")
    w()

    # =========================================================================
    # SECTION 1: EMILY WATSON VIOLATIONS
    # =========================================================================
    w("# 1. EMILY A. WATSON — Violations")
    w()

    # 1a. adversary_assertions
    w("## 1.1 False Assertions / Adversary Claims")
    w()
    rows = safe_query(conn, """
        SELECT assertion_text, file_name, assertion_type, severity, rebuttal_evidence, speaker
        FROM adversary_assertions
        WHERE assertion_text LIKE '%Emily%' OR assertion_text LIKE '%Watson%'
           OR speaker LIKE '%Emily%' OR speaker LIKE '%Watson%'
        ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END
        LIMIT 150
    """, label="emily_assertions")
    emily_assert_count = len(rows)
    summary_counts['emily_assertions'] = emily_assert_count
    
    # Group by severity
    by_severity = {}
    for r in rows:
        sev = r['severity'] or 'UNRATED'
        by_severity.setdefault(sev, []).append(r)
    
    for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'UNRATED']:
        if sev not in by_severity:
            continue
        items = by_severity[sev]
        w(f"### Severity: {sev} ({len(items)} assertions)")
        w()
        for r in items[:30]:
            w(f"- **[{r['assertion_type'] or 'N/A'}]** {truncate(r['assertion_text'])}")
            if r['rebuttal_evidence']:
                w(f"  - *Rebuttal:* {truncate(r['rebuttal_evidence'], 200)}")
            w(f"  - *Source:* {r['file_name'] or 'N/A'} | *Speaker:* {r['speaker'] or 'N/A'}")
            w()
        if len(items) > 30:
            w(f"  *...and {len(items) - 30} more {sev} assertions*")
            w()

    # 1b. actor_violations for Emily/Watson
    w("## 1.2 Actor Violations (Emily Watson)")
    w()
    rows = safe_query(conn, """
        SELECT actor, violation_type, description, date, evidence_source, severity, linked_actors
        FROM actor_violations
        WHERE actor LIKE '%Emily%' OR actor LIKE '%Watson%'
        ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END
        LIMIT 200
    """, label="emily_actor_violations")
    emily_actor_count = len(rows)
    summary_counts['emily_actor_violations'] = emily_actor_count

    by_type = {}
    for r in rows:
        vtype = r['violation_type'] or 'UNCLASSIFIED'
        by_type.setdefault(vtype, []).append(r)

    for vtype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        w(f"### {vtype} ({len(items)} violations)")
        w()
        for r in items[:15]:
            w(f"- **[{r['severity'] or 'N/A'}]** {truncate(r['description'])}")
            w(f"  - *Date:* {r['date'] or 'N/A'} | *Source:* {truncate(r['evidence_source'], 100)}")
            if r['linked_actors']:
                w(f"  - *Linked actors:* {r['linked_actors']}")
            w()
        if len(items) > 15:
            w(f"  *...and {len(items) - 15} more {vtype} violations*")
            w()

    # 1c. watson_perjury_compilation
    w("## 1.3 Perjury Compilation (Emily Watson)")
    w()
    rows = safe_query(conn, """
        SELECT * FROM watson_perjury_compilation
        WHERE rowid IN (
            SELECT rowid FROM watson_perjury_compilation LIMIT 5
        )
    """, label="perjury_schema_check")
    # Get column names
    try:
        perjury_cols = [d[1] for d in conn.execute("PRAGMA table_info(watson_perjury_compilation)").fetchall()]
        print(f"  watson_perjury_compilation columns: {perjury_cols}")
    except:
        perjury_cols = []

    if perjury_cols:
        # Build dynamic query based on actual columns
        actor_col = next((c for c in perjury_cols if c.lower() in ('actor', 'speaker', 'person', 'name', 'party')), None)
        text_col = next((c for c in perjury_cols if 'text' in c.lower() or 'statement' in c.lower() or 'description' in c.lower() or 'assertion' in c.lower()), None)
        source_col = next((c for c in perjury_cols if 'source' in c.lower() or 'file' in c.lower() or 'document' in c.lower()), None)
        sev_col = next((c for c in perjury_cols if 'sever' in c.lower() or 'level' in c.lower()), None)
        type_col = next((c for c in perjury_cols if 'type' in c.lower() or 'category' in c.lower()), None)

        select_parts = []
        if actor_col: select_parts.append(actor_col)
        if text_col: select_parts.append(text_col)
        if source_col: select_parts.append(source_col)
        if sev_col: select_parts.append(sev_col)
        if type_col: select_parts.append(type_col)

        if not select_parts:
            select_parts = perjury_cols[:6]

        where_clauses = []
        if actor_col:
            where_clauses.append(f"{actor_col} LIKE '%Emily%' OR {actor_col} LIKE '%Watson%'")
        elif text_col:
            where_clauses.append(f"{text_col} LIKE '%Emily%' OR {text_col} LIKE '%Watson%'")
        else:
            where_clauses.append("1=1")

        sql = f"SELECT {', '.join(select_parts)} FROM watson_perjury_compilation WHERE {' OR '.join(where_clauses)} LIMIT 100"
        rows = safe_query(conn, sql, label="emily_perjury")
        emily_perjury_count = len(rows)
        summary_counts['emily_perjury'] = emily_perjury_count

        for r in rows[:50]:
            parts = [f"{select_parts[i]}: {truncate(str(r[i]), 200)}" for i in range(len(select_parts)) if r[i]]
            w(f"- " + " | ".join(parts))
            w()
        if emily_perjury_count > 50:
            w(f"*...and {emily_perjury_count - 50} more perjury entries*")
            w()
    else:
        w("*watson_perjury_compilation table not accessible*")
        w()

    # 1d. PPO Violations (Emily)
    w("## 1.4 PPO Violations (Emily Watson)")
    w()
    ppo_cols_raw = safe_query(conn, "PRAGMA table_info(ppo_violations)", label="ppo_schema")
    ppo_cols = [r['name'] for r in ppo_cols_raw]
    print(f"  ppo_violations columns: {ppo_cols}")
    
    if ppo_cols:
        text_col = next((c for c in ppo_cols if 'text' in c.lower() or 'description' in c.lower() or 'detail' in c.lower()), ppo_cols[1] if len(ppo_cols) > 1 else ppo_cols[0])
        rows = safe_query(conn, f"""
            SELECT * FROM ppo_violations LIMIT 100
        """, label="ppo_violations")
        emily_ppo_count = len(rows)
        summary_counts['emily_ppo'] = emily_ppo_count
        
        for r in rows[:40]:
            parts = [f"**{ppo_cols[i]}:** {truncate(str(r[i]), 150)}" for i in range(min(len(ppo_cols), 6)) if r[i]]
            w(f"- " + " | ".join(parts))
            w()
        if emily_ppo_count > 40:
            w(f"*...and {emily_ppo_count - 40} more PPO violations*")
            w()

    # 1e. Statute mapping for Emily
    w("## 1.5 Criminal Statute Mapping (Emily Watson)")
    w()
    w("| Statute | Description | Applicable Violations |")
    w("|---------|-------------|----------------------|")
    
    # Count perjury-type assertions
    perjury_count = safe_query(conn, """
        SELECT COUNT(*) as cnt FROM adversary_assertions 
        WHERE (assertion_text LIKE '%Emily%' OR assertion_text LIKE '%Watson%' OR speaker LIKE '%Emily%' OR speaker LIKE '%Watson%')
        AND (is_false = 1 OR assertion_type LIKE '%false%' OR assertion_type LIKE '%perjur%' OR assertion_type LIKE '%lie%')
    """, label="emily_perjury_count")
    pc = perjury_count[0]['cnt'] if perjury_count else 0
    w(f"| MCL 750.423 | Perjury | {pc} false sworn statements identified |")

    conspiracy_count = safe_query(conn, """
        SELECT COUNT(*) as cnt FROM conspiracy_timeline 
        WHERE actor LIKE '%Emily%' OR actor LIKE '%Watson%' OR coordinated_with LIKE '%Emily%' OR coordinated_with LIKE '%Watson%'
    """, label="emily_conspiracy_count")
    cc = conspiracy_count[0]['cnt'] if conspiracy_count else 0
    w(f"| MCL 750.157a | Conspiracy | {cc} coordinated actions documented |")

    w(f"| MCL 750.136b | Child abuse (emotional) | See parental alienation/interference in actor_violations |")
    w(f"| MCL 750.218 | False pretenses | False court representations documented in assertions |")
    w(f"| MCR 2.114(D) | Frivolous filings | Frivolous motions/claims documented |")
    w()

    # =========================================================================
    # SECTION 2: RONALD BERRY VIOLATIONS
    # =========================================================================
    w("# 2. RONALD BERRY — Violations")
    w("*Note: Ronald Berry is a NON-ATTORNEY. He is Emily Watson's boyfriend/domestic partner. No bar number.*")
    w()

    # 2a. adversary_assertions
    w("## 2.1 False Assertions (Ronald Berry)")
    w()
    rows = safe_query(conn, """
        SELECT assertion_text, file_name, assertion_type, severity, rebuttal_evidence, speaker
        FROM adversary_assertions
        WHERE assertion_text LIKE '%Berry%' OR assertion_text LIKE '%Ronald%'
           OR speaker LIKE '%Berry%' OR speaker LIKE '%Ronald%'
        ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END
        LIMIT 100
    """, label="berry_assertions")
    berry_assert_count = len(rows)
    summary_counts['berry_assertions'] = berry_assert_count

    for r in rows[:50]:
        w(f"- **[{r['severity'] or 'N/A'} | {r['assertion_type'] or 'N/A'}]** {truncate(r['assertion_text'])}")
        if r['rebuttal_evidence']:
            w(f"  - *Rebuttal:* {truncate(r['rebuttal_evidence'], 200)}")
        w(f"  - *Source:* {r['file_name'] or 'N/A'}")
        w()
    if berry_assert_count > 50:
        w(f"*...and {berry_assert_count - 50} more Berry assertions*")
        w()

    # 2b. berry_ethics_violations (dedicated table!)
    w("## 2.2 Ethics Violations (Ronald Berry)")
    w()
    berry_eth_cols = [r['name'] for r in safe_query(conn, "PRAGMA table_info(berry_ethics_violations)", label="berry_eth_schema")]
    print(f"  berry_ethics_violations columns: {berry_eth_cols}")
    
    rows = safe_query(conn, """
        SELECT * FROM berry_ethics_violations 
        ORDER BY rowid
        LIMIT 178
    """, label="berry_ethics")
    berry_ethics_count = len(rows)
    summary_counts['berry_ethics'] = berry_ethics_count

    for r in rows[:60]:
        parts = [f"**{berry_eth_cols[i]}:** {truncate(str(r[i]), 150)}" for i in range(min(len(berry_eth_cols), 6)) if r[i]]
        w(f"- " + " | ".join(parts))
        w()
    if berry_ethics_count > 60:
        w(f"*...and {berry_ethics_count - 60} more ethics violations*")
        w()

    # 2c. actor_violations for Berry
    w("## 2.3 Actor Violations (Ronald Berry)")
    w()
    rows = safe_query(conn, """
        SELECT actor, violation_type, description, date, evidence_source, severity, linked_actors
        FROM actor_violations
        WHERE actor LIKE '%Berry%' OR actor LIKE '%Ronald%'
        ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END
        LIMIT 200
    """, label="berry_actor_violations")
    berry_actor_count = len(rows)
    summary_counts['berry_actor_violations'] = berry_actor_count

    by_type = {}
    for r in rows:
        vtype = r['violation_type'] or 'UNCLASSIFIED'
        by_type.setdefault(vtype, []).append(r)

    for vtype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        w(f"### {vtype} ({len(items)} violations)")
        for r in items[:10]:
            w(f"- **[{r['severity']}]** {truncate(r['description'])}")
            w(f"  - *Date:* {r['date'] or 'N/A'} | *Source:* {truncate(r['evidence_source'], 100)}")
            w()
        if len(items) > 10:
            w(f"  *...and {len(items) - 10} more*")
        w()

    # 2d. Statute mapping for Berry
    w("## 2.4 Criminal Statute Mapping (Ronald Berry)")
    w()
    w("| Statute | Description | Applicable Violations |")
    w("|---------|-------------|----------------------|")
    w(f"| MCL 750.423 | Perjury | False statements in court proceedings |")
    w(f"| MCL 750.424 | Subornation of perjury | Coaching/encouraging false statements |")
    w(f"| MCL 750.157a | Conspiracy | Coordinated actions with Emily Watson |")
    w(f"| MCL 750.136b | Child abuse (emotional) | Role in parental alienation |")
    w(f"| MCL 750.539d | Eavesdropping | Potential recording violations |")
    w()

    # =========================================================================
    # SECTION 3: JENNIFER BARNES (P55406) VIOLATIONS
    # =========================================================================
    w("# 3. JENNIFER BARNES (P55406) — Violations")
    w("*Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440 — WITHDREW*")
    w()

    # 3a. adversary_assertions
    w("## 3.1 False Assertions / Representations (Barnes)")
    w()
    rows = safe_query(conn, """
        SELECT assertion_text, file_name, assertion_type, severity, rebuttal_evidence, speaker
        FROM adversary_assertions
        WHERE assertion_text LIKE '%Barnes%' OR assertion_text LIKE '%Jennifer%'
           OR assertion_text LIKE '%P55406%'
           OR speaker LIKE '%Barnes%' OR speaker LIKE '%P55406%'
        ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END
        LIMIT 100
    """, label="barnes_assertions")
    barnes_assert_count = len(rows)
    summary_counts['barnes_assertions'] = barnes_assert_count

    for r in rows[:50]:
        w(f"- **[{r['severity'] or 'N/A'} | {r['assertion_type'] or 'N/A'}]** {truncate(r['assertion_text'])}")
        if r['rebuttal_evidence']:
            w(f"  - *Rebuttal:* {truncate(r['rebuttal_evidence'], 200)}")
        w(f"  - *Source:* {r['file_name'] or 'N/A'}")
        w()
    if barnes_assert_count > 50:
        w(f"*...and {barnes_assert_count - 50} more Barnes assertions*")
        w()

    # 3b. actor_violations for Barnes
    w("## 3.2 Actor Violations (Jennifer Barnes)")
    w()
    rows = safe_query(conn, """
        SELECT actor, violation_type, description, date, evidence_source, severity, linked_actors
        FROM actor_violations
        WHERE actor LIKE '%Barnes%' OR actor LIKE '%Jennifer%' OR actor LIKE '%P55406%'
        ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END
        LIMIT 200
    """, label="barnes_actor_violations")
    barnes_actor_count = len(rows)
    summary_counts['barnes_actor_violations'] = barnes_actor_count

    by_type = {}
    for r in rows:
        vtype = r['violation_type'] or 'UNCLASSIFIED'
        by_type.setdefault(vtype, []).append(r)

    for vtype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        w(f"### {vtype} ({len(items)} violations)")
        for r in items[:10]:
            w(f"- **[{r['severity']}]** {truncate(r['description'])}")
            w(f"  - *Date:* {r['date'] or 'N/A'} | *Source:* {truncate(r['evidence_source'], 100)}")
            if r['linked_actors']:
                w(f"  - *Linked actors:* {r['linked_actors']}")
            w()
        if len(items) > 10:
            w(f"  *...and {len(items) - 10} more*")
        w()

    # 3c. Statute mapping for Barnes
    w("## 3.3 Professional & Criminal Statute Mapping (Jennifer Barnes)")
    w()
    w("| Statute | Description | Applicable Violations |")
    w("|---------|-------------|----------------------|")
    w(f"| MCR 2.114(D) | Frivolous filings | Filing without factual basis |")
    w(f"| MRPC 3.1 | Meritorious claims/contentions | Advancing frivolous positions |")
    w(f"| MRPC 3.3 | Candor toward tribunal | Misrepresentations to court |")
    w(f"| MRPC 3.4 | Fairness to opposing party | Obstruction, evidence concealment |")
    w(f"| MRPC 8.4 | Attorney misconduct | General professional misconduct |")
    w(f"| MCL 750.423 | Perjury | False representations in signed filings |")
    w()

    # =========================================================================
    # SECTION 4: JUDGE McNEILL VIOLATIONS
    # =========================================================================
    w("# 4. HON. JENNY L. McNEILL — Violations")
    w("*14th Circuit Court, Family Division*")
    w()

    # 4a. judicial_violations (primary table)
    w("## 4.1 Judicial Canon Violations")
    w()
    rows = safe_query(conn, """
        SELECT violation_id, canon_number, canon_text, violation_description, evidence_refs, severity, jtc_exhibit_id
        FROM judicial_violations
        ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END
        LIMIT 500
    """, label="judicial_violations")
    jv_count = len(rows)
    summary_counts['judicial_violations'] = jv_count

    by_canon = {}
    for r in rows:
        canon = r['canon_number'] or 'UNCLASSIFIED'
        by_canon.setdefault(canon, []).append(r)

    for canon, items in sorted(by_canon.items()):
        sev_counts = {}
        for r in items:
            s = r['severity'] or 'UNRATED'
            sev_counts[s] = sev_counts.get(s, 0) + 1
        sev_str = ", ".join(f"{k}: {v}" for k, v in sorted(sev_counts.items()))
        w(f"### Canon/Rule: {canon} ({len(items)} violations — {sev_str})")
        if items[0]['canon_text']:
            w(f"*{truncate(items[0]['canon_text'], 200)}*")
        w()
        for r in items[:10]:
            w(f"- **[{r['severity']}]** {truncate(r['violation_description'])}")
            if r['evidence_refs']:
                w(f"  - *Evidence:* {truncate(r['evidence_refs'], 150)}")
            if r['jtc_exhibit_id']:
                w(f"  - *JTC Exhibit:* {r['jtc_exhibit_id']}")
            w()
        if len(items) > 10:
            w(f"  *...and {len(items) - 10} more violations under {canon}*")
            w()

    # 4b. forensic_judicial_analysis
    w("## 4.2 Forensic Judicial Analysis")
    w()
    rows = safe_query(conn, """
        SELECT finding_id, category, severity, description, evidence_citations, mcr_violations, date_iso
        FROM forensic_judicial_analysis
        ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END
        LIMIT 200
    """, label="forensic_judicial")
    fja_count = len(rows)
    summary_counts['forensic_judicial_analysis'] = fja_count

    by_cat = {}
    for r in rows:
        cat = r['category'] or 'UNCATEGORIZED'
        by_cat.setdefault(cat, []).append(r)

    for cat, items in sorted(by_cat.items(), key=lambda x: -len(x[1])):
        w(f"### Category: {cat} ({len(items)} findings)")
        w()
        for r in items[:8]:
            w(f"- **[{r['severity']}]** {truncate(r['description'])}")
            if r['mcr_violations']:
                w(f"  - *MCR Violations:* {truncate(r['mcr_violations'], 150)}")
            if r['evidence_citations']:
                w(f"  - *Citations:* {truncate(r['evidence_citations'], 150)}")
            w()
        if len(items) > 8:
            w(f"  *...and {len(items) - 8} more {cat} findings*")
            w()

    # 4c. actor_violations for McNeill
    w("## 4.3 Actor Violations (McNeill)")
    w()
    rows = safe_query(conn, """
        SELECT violation_type, description, date, evidence_source, severity, linked_actors
        FROM actor_violations
        WHERE actor LIKE '%McNeill%' OR actor LIKE '%Mcneill%' OR actor LIKE '%mcneill%'
        ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END
        LIMIT 300
    """, label="mcneill_actor_violations")
    mcneill_actor_count = len(rows)
    summary_counts['mcneill_actor_violations'] = mcneill_actor_count

    by_type = {}
    for r in rows:
        vtype = r['violation_type'] or 'UNCLASSIFIED'
        by_type.setdefault(vtype, []).append(r)

    for vtype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        w(f"### {vtype} ({len(items)} violations)")
        for r in items[:8]:
            w(f"- **[{r['severity']}]** {truncate(r['description'])}")
            w(f"  - *Date:* {r['date'] or 'N/A'} | *Source:* {truncate(r['evidence_source'], 100)}")
            w()
        if len(items) > 8:
            w(f"  *...and {len(items) - 8} more*")
        w()

    # 4d. constitutional_violations (McNeill involvement)
    w("## 4.4 Constitutional Violations")
    w()
    rows = safe_query(conn, """
        SELECT amendment, clause, violation_type, description, incident_date, actors, evidence_ref, 
               controlling_caselaw, michigan_authority, severity
        FROM constitutional_violations
        ORDER BY severity
    """, label="constitutional_violations")
    const_count = len(rows)
    summary_counts['constitutional_violations'] = const_count

    for r in rows:
        w(f"### {r['amendment']} — {r['clause']}")
        w(f"- **Type:** {r['violation_type']}")
        w(f"- **Severity:** {r['severity']}")
        w(f"- **Description:** {truncate(r['description'], 500)}")
        w(f"- **Date:** {r['incident_date'] or 'N/A'}")
        w(f"- **Actors:** {r['actors'] or 'N/A'}")
        w(f"- **Evidence:** {truncate(r['evidence_ref'], 200)}")
        w(f"- **Controlling Caselaw:** {truncate(r['controlling_caselaw'], 200)}")
        w(f"- **Michigan Authority:** {truncate(r['michigan_authority'], 200)}")
        w()

    # 4e. violation_patterns
    w("## 4.5 Violation Patterns (Systemic)")
    w()
    rows = safe_query(conn, """
        SELECT pattern_name, description, frequency, first_occurrence, last_occurrence, 
               actors_involved, severity, evidence_strength
        FROM violation_patterns
        ORDER BY frequency DESC
        LIMIT 59
    """, label="violation_patterns")
    vp_count = len(rows)
    summary_counts['violation_patterns'] = vp_count

    w("| Pattern | Frequency | Severity | Evidence | Actors | Time Span |")
    w("|---------|-----------|----------|----------|--------|-----------|")
    for r in rows:
        w(f"| {r['pattern_name']} | {r['frequency']} | {r['severity']} | {r['evidence_strength'] or 'N/A'} | {truncate(r['actors_involved'], 80)} | {r['first_occurrence'] or '?'} → {r['last_occurrence'] or '?'} |")
    w()

    # 4f. McNeill statute mapping
    w("## 4.6 Judicial Statute / Canon Mapping (McNeill)")
    w()
    w("| Authority | Description | Documented Violations |")
    w("|-----------|-------------|----------------------|")
    
    # Count by canon
    canon_counts = safe_query(conn, """
        SELECT canon_number, COUNT(*) as cnt FROM judicial_violations
        GROUP BY canon_number ORDER BY cnt DESC
    """, label="canon_counts")
    for r in canon_counts:
        w(f"| {r['canon_number']} | Judicial Canon | {r['cnt']} documented violations |")

    w(f"| MCR 2.003 | Disqualification | See Canon violations above |")
    w(f"| Const. Art. VI §5 | Judicial oath | Oath violations documented |")
    w()

    # =========================================================================
    # SECTION 5: CONSPIRACY (Coordinated Actions)
    # =========================================================================
    w("# 5. CONSPIRACY — Coordinated Actions")
    w()

    # 5a. conspiracy_timeline
    w("## 5.1 Conspiracy Timeline")
    w()
    rows = safe_query(conn, """
        SELECT date, actor, action, coordinated_with, evidence_source, conspiracy_type, severity
        FROM conspiracy_timeline
        ORDER BY date, CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END
        LIMIT 300
    """, label="conspiracy_timeline")
    conspiracy_count = len(rows)
    summary_counts['conspiracy_timeline'] = conspiracy_count

    by_type = {}
    for r in rows:
        ctype = r['conspiracy_type'] or 'UNCLASSIFIED'
        by_type.setdefault(ctype, []).append(r)

    for ctype, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        w(f"### Conspiracy Type: {ctype} ({len(items)} events)")
        w()
        w("| Date | Actor | Action | Coordinated With | Severity | Source |")
        w("|------|-------|--------|-----------------|----------|--------|")
        for r in items[:30]:
            w(f"| {r['date'] or 'N/A'} | {r['actor'] or 'N/A'} | {truncate(r['action'], 120)} | {r['coordinated_with'] or 'N/A'} | {r['severity'] or 'N/A'} | {truncate(r['evidence_source'], 80)} |")
        if len(items) > 30:
            w(f"*...and {len(items) - 30} more events*")
        w()

    # 5b. watson_family_conspiracy
    w("## 5.2 Watson Family Conspiracy")
    w()
    rows = safe_query(conn, """
        SELECT family_member, role_in_scheme, evidence_file, evidence_text, strength, 
               connection_to_emily, tort_claim
        FROM watson_family_conspiracy
        ORDER BY CASE strength WHEN 'STRONG' THEN 1 WHEN 'MODERATE' THEN 2 ELSE 3 END
        LIMIT 200
    """, label="watson_conspiracy")
    watson_conspiracy_count = len(rows)
    summary_counts['watson_family_conspiracy'] = watson_conspiracy_count

    by_member = {}
    for r in rows:
        member = r['family_member'] or 'UNKNOWN'
        by_member.setdefault(member, []).append(r)

    for member, items in sorted(by_member.items(), key=lambda x: -len(x[1])):
        w(f"### {member} ({len(items)} entries)")
        w()
        for r in items[:15]:
            w(f"- **[{r['strength']}]** Role: {r['role_in_scheme'] or 'N/A'}")
            w(f"  - *Evidence:* {truncate(r['evidence_text'], 200)}")
            w(f"  - *Connection to Emily:* {r['connection_to_emily'] or 'N/A'}")
            w(f"  - *Tort Claim:* {r['tort_claim'] or 'N/A'}")
            w(f"  - *Source:* {r['evidence_file'] or 'N/A'}")
            w()
        if len(items) > 15:
            w(f"  *...and {len(items) - 15} more entries*")
            w()

    # =========================================================================
    # SECTION 6: MASTER VIOLATIONS CROSS-REFERENCE
    # =========================================================================
    w("# 6. MASTER VIOLATIONS — Cross-Reference Summary")
    w()

    # Check master_violations_parsed schema
    mvp_cols = [r['name'] for r in safe_query(conn, "PRAGMA table_info(master_violations_parsed)", label="mvp_schema")]
    print(f"  master_violations_parsed columns: {mvp_cols}")

    if mvp_cols:
        actor_col = next((c for c in mvp_cols if c.lower() in ('actor', 'violator', 'party', 'person', 'name')), None)
        type_col = next((c for c in mvp_cols if 'type' in c.lower() or 'category' in c.lower()), None)
        desc_col = next((c for c in mvp_cols if 'desc' in c.lower() or 'text' in c.lower() or 'detail' in c.lower()), None)
        sev_col = next((c for c in mvp_cols if 'sever' in c.lower()), None)

        if actor_col:
            # Get counts per actor for our 4 targets
            for name_pattern, label in [
                ('%Emily%', 'Emily Watson'), ('%Watson%', 'Watson (all)'),
                ('%Berry%', 'Ronald Berry'), ('%Barnes%', 'Jennifer Barnes'),
                ('%McNeill%', 'Judge McNeill'), ('%mcneill%', 'McNeill (lowercase)')
            ]:
                count = safe_query(conn, f"SELECT COUNT(*) as cnt FROM master_violations_parsed WHERE {actor_col} LIKE ?", (name_pattern,), label=f"mvp_{label}")
                if count:
                    w(f"- **{label}:** {count[0]['cnt']} violations in master_violations_parsed")
            w()

            # Top violation types per actor
            for actor_pattern, label in [('%Watson%', 'Watson'), ('%Berry%', 'Berry'), ('%Barnes%', 'Barnes'), ('%McNeill%', 'McNeill')]:
                if type_col:
                    rows = safe_query(conn, f"""
                        SELECT {type_col}, COUNT(*) as cnt FROM master_violations_parsed
                        WHERE {actor_col} LIKE ?
                        GROUP BY {type_col} ORDER BY cnt DESC LIMIT 15
                    """, (actor_pattern,), label=f"mvp_types_{label}")
                    if rows:
                        w(f"### {label} — Top Violation Types (master_violations_parsed)")
                        w()
                        w("| Type | Count |")
                        w("|------|-------|")
                        for r in rows:
                            w(f"| {r[type_col]} | {r['cnt']} |")
                        w()
        else:
            w(f"*master_violations_parsed columns: {mvp_cols} — no actor column identified. Showing first 5 cols for manual review.*")
            rows = safe_query(conn, f"SELECT {', '.join(mvp_cols[:5])} FROM master_violations_parsed LIMIT 5", label="mvp_sample")
            for r in rows:
                w(f"- {dict(r)}")
            w()

    # =========================================================================
    # SECTION 7: SUMMARY COUNTS
    # =========================================================================
    w("# 7. SUMMARY — Total Violation Counts")
    w()
    w("## By Party")
    w()
    w("| Party | Table | Count |")
    w("|-------|-------|-------|")
    for key, val in sorted(summary_counts.items()):
        party = "Emily Watson" if "emily" in key else "Ronald Berry" if "berry" in key else "Jennifer Barnes" if "barnes" in key else "Judge McNeill" if "mcneill" in key or "judicial" in key or "forensic" in key else "Multi-Party"
        w(f"| {party} | {key} | {val} |")
    w()

    # Grand totals
    total_emily = sum(v for k, v in summary_counts.items() if 'emily' in k)
    total_berry = sum(v for k, v in summary_counts.items() if 'berry' in k)
    total_barnes = sum(v for k, v in summary_counts.items() if 'barnes' in k)
    total_mcneill = sum(v for k, v in summary_counts.items() if 'mcneill' in k or 'judicial' in k or 'forensic' in k)
    total_conspiracy = sum(v for k, v in summary_counts.items() if 'conspir' in k or 'watson_family' in k)

    w("## Grand Totals (queried records)")
    w()
    w(f"| Party | Total Records |")
    w(f"|-------|---------------|")
    w(f"| Emily Watson | {total_emily} |")
    w(f"| Ronald Berry | {total_berry} |")
    w(f"| Jennifer Barnes | {total_barnes} |")
    w(f"| Judge McNeill | {total_mcneill} |")
    w(f"| Conspiracy (cross-party) | {total_conspiracy} |")
    w(f"| **GRAND TOTAL** | **{total_emily + total_berry + total_barnes + total_mcneill + total_conspiracy}** |")
    w()

    w("---")
    w(f"*Report generated from {DB}*")
    w(f"*Tables queried: adversary_assertions, actor_violations, judicial_violations, forensic_judicial_analysis,*")
    w(f"*constitutional_violations, violation_patterns, conspiracy_timeline, watson_family_conspiracy,*")
    w(f"*watson_perjury_compilation, berry_ethics_violations, ppo_violations, master_violations_parsed*")
    w(f"*Total tables: 12 primary sources*")

    conn.close()

    # Write report
    report_text = "\n".join(report_lines)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"\n{'='*60}")
    print(f"REPORT WRITTEN: {OUT}")
    print(f"Report size: {len(report_text):,} characters, {len(report_lines):,} lines")
    print(f"{'='*60}")
    print(f"\nSummary counts:")
    for k, v in sorted(summary_counts.items()):
        print(f"  {k}: {v}")
    print(f"\nGrand totals:")
    print(f"  Emily Watson:     {total_emily}")
    print(f"  Ronald Berry:     {total_berry}")
    print(f"  Jennifer Barnes:  {total_barnes}")
    print(f"  Judge McNeill:    {total_mcneill}")
    print(f"  Conspiracy:       {total_conspiracy}")
    print(f"  GRAND TOTAL:      {total_emily + total_berry + total_barnes + total_mcneill + total_conspiracy}")

if __name__ == '__main__':
    main()
