#!/usr/bin/env python3
"""
Tool #236 — Constitutional Violation Mapper
============================================
Maps ALL constitutional violations across the case:
- 1st Amendment: Retaliation for filing motions/complaints (Thaddeus-X v Blatter)
- 4th Amendment: Unreasonable seizure of child
- 14th Amendment Due Process: Parental liberty (Troxel v Granville), void orders
- 14th Amendment Equal Protection: Gender bias in custody
- Michigan Constitution Art 1 §17: Right to petition government

Cross-references with authority_chains for supporting case law.
Outputs: MD report + JSON to reports dir
LitigationOS — Pigors v. Watson (14th Circuit Court, Muskegon County)
"""
import sys
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO = SCRIPT_DIR.parent.parent
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def get_conn():
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def safe_trunc(text, maxlen=250):
    if not text:
        return ""
    text = str(text).replace('\n', ' ').replace('\r', '').strip()
    return text[:maxlen] + "..." if len(text) > maxlen else text


def table_exists(conn, name):
    return conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()[0] > 0


# ── Constitutional framework ────────────────────────────────────────────
AMENDMENTS = {
    "1st_Amendment": {
        "name": "First Amendment — Right to Petition / Retaliation",
        "text": "Congress shall make no law abridging the right of the people to petition "
                "the Government for a redress of grievances.",
        "test": "Thaddeus-X v. Blatter, 175 F.3d 378 (6th Cir. 1999) — three-part test: "
                "(1) protected conduct, (2) adverse action, (3) causal connection",
        "keywords": ["retaliat", "petition", "first amendment", "1st amendment",
                     "filing motions", "punish", "complaint"],
        "severity_weight": 4,
    },
    "4th_Amendment": {
        "name": "Fourth Amendment — Unreasonable Seizure of Child",
        "text": "The right of the people to be secure in their persons against unreasonable "
                "seizures shall not be violated.",
        "test": "Kovacic v. Cuyahoga County, 724 F.3d 687 (6th Cir. 2013) — removal of child "
                "from parent constitutes seizure under 4th Amendment",
        "keywords": ["seizure", "4th amendment", "fourth amendment", "removal",
                     "unreasonable", "taken", "removed child"],
        "severity_weight": 5,
    },
    "14th_Due_Process": {
        "name": "Fourteenth Amendment — Due Process (Parental Liberty)",
        "text": "No State shall deprive any person of life, liberty, or property, without "
                "due process of law.",
        "test": "Troxel v. Granville, 530 U.S. 57 (2000) — fundamental right to parent; "
                "Mathews v. Eldridge, 424 U.S. 319 (1976) — procedural due process balancing",
        "keywords": ["due process", "14th amendment", "parental", "liberty",
                     "without hearing", "ex parte", "void order", "no notice",
                     "parenting time", "suspended"],
        "severity_weight": 5,
    },
    "14th_Equal_Protection": {
        "name": "Fourteenth Amendment — Equal Protection (Gender Bias)",
        "text": "No State shall deny to any person within its jurisdiction the equal "
                "protection of the laws.",
        "test": "Craig v. Boren, 429 U.S. 190 (1976) — intermediate scrutiny for gender; "
                "Mississippi Univ. for Women v. Hogan, 458 U.S. 718 (1982)",
        "keywords": ["equal protection", "gender bias", "discrimination",
                     "disparate treatment", "father", "mother", "preferential"],
        "severity_weight": 4,
    },
    "MI_Art1_Sec17": {
        "name": "Michigan Constitution Art 1 §17 — Right to Petition",
        "text": "Every person has a right to petition the government for a redress of "
                "grievances. No person shall be penalized for exercising this right.",
        "test": "Self-executing provision — broader than federal 1st Amendment. "
                "Includes right to file court motions without judicial retaliation.",
        "keywords": ["petition", "art 1", "section 17", "michigan constitution",
                     "redress", "grievance", "retaliation for filing"],
        "severity_weight": 4,
    },
}


def query_constitutional_violations_table(conn):
    """Pull from dedicated constitutional_violations table."""
    print("  [1/7] Querying constitutional_violations table...")
    results = []
    if not table_exists(conn, 'constitutional_violations'):
        print("    Table not found")
        return results
    try:
        rows = conn.execute("""
            SELECT id, amendment, clause, violation_type, description,
                   incident_date, actors, evidence_ref, controlling_caselaw,
                   michigan_authority, damages_link, filing_target, severity
            FROM constitutional_violations
            ORDER BY CASE severity
                WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3 ELSE 4 END
        """).fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "amendment": r["amendment"],
                "clause": r["clause"],
                "violation_type": r["violation_type"],
                "description": safe_trunc(r["description"], 400),
                "incident_date": r["incident_date"],
                "actors": r["actors"],
                "evidence_ref": safe_trunc(r["evidence_ref"], 200),
                "caselaw": safe_trunc(r["controlling_caselaw"], 300),
                "michigan_authority": safe_trunc(r["michigan_authority"], 200),
                "damages": r["damages_link"],
                "filing_target": r["filing_target"],
                "severity": r["severity"],
            })
        print(f"    Found {len(results)} constitutional violations")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_constitutional_rights_tracker(conn):
    """Pull from constitutional_rights_tracker for aggregated counts."""
    print("  [2/7] Querying constitutional_rights_tracker...")
    results = []
    if not table_exists(conn, 'constitutional_rights_tracker'):
        print("    Table not found")
        return results
    try:
        rows = conn.execute("""
            SELECT id, right, amendment, provision_text, violation_description,
                   violation_count, evidence_sources, remedy, filing_where_raised
            FROM constitutional_rights_tracker
            ORDER BY violation_count DESC
        """).fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "right": r["right"],
                "amendment": r["amendment"],
                "provision": safe_trunc(r["provision_text"], 200),
                "description": safe_trunc(r["violation_description"], 300),
                "violation_count": r["violation_count"],
                "evidence_sources": r["evidence_sources"],
                "remedy": safe_trunc(r["remedy"], 250),
                "filing": r["filing_where_raised"],
            })
        print(f"    Found {len(results)} rights tracker entries")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_constitutional_brief_sections(conn):
    """Pull IRAC brief sections for constitutional arguments."""
    print("  [3/7] Querying constitutional_brief_sections...")
    results = []
    if not table_exists(conn, 'constitutional_brief_sections'):
        print("    Table not found")
        return results
    try:
        rows = conn.execute("SELECT * FROM constitutional_brief_sections ORDER BY id").fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "right_name": r["right_name"],
                "issue": safe_trunc(r["issue_text"], 300),
                "rule": safe_trunc(r["rule_text"], 300),
                "application": safe_trunc(r["application_text"], 300),
                "conclusion": safe_trunc(r["conclusion_text"], 300),
                "citations": safe_trunc(r["key_citations"], 300),
            })
        print(f"    Found {len(results)} brief sections")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_judicial_violations_constitutional(conn):
    """Pull judicial violations with constitutional implications."""
    print("  [4/7] Querying judicial_violations for constitutional patterns...")
    results = []
    try:
        rows = conn.execute("""
            SELECT violation_id, judge_name, canon_number, violation_description,
                   evidence_refs, severity
            FROM judicial_violations
            WHERE violation_description LIKE '%constitution%'
               OR violation_description LIKE '%due process%'
               OR violation_description LIKE '%equal protection%'
               OR violation_description LIKE '%amendment%'
               OR violation_description LIKE '%ex parte%'
               OR violation_description LIKE '%without hearing%'
               OR violation_description LIKE '%without notice%'
               OR violation_description LIKE '%parenting time%'
               OR violation_description LIKE '%retaliat%'
            ORDER BY CASE severity
                WHEN 'critical' THEN 1 WHEN 'high' THEN 2
                WHEN 'medium' THEN 3 ELSE 4 END
        """).fetchall()
        for r in rows:
            amendment = classify_amendment(r["violation_description"] or "")
            results.append({
                "violation_id": r["violation_id"],
                "judge": r["judge_name"],
                "canon": r["canon_number"],
                "description": safe_trunc(r["violation_description"], 350),
                "evidence_refs": r["evidence_refs"],
                "severity": r["severity"],
                "amendment_classification": amendment,
            })
        print(f"    Found {len(results)} constitutional-relevant judicial violations")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_claims_constitutional(conn):
    """Pull claims with constitutional dimensions."""
    print("  [5/7] Querying claims for constitutional issues...")
    results = []
    try:
        rows = conn.execute("""
            SELECT claim_id, issue_id, classification, actor, proposition,
                   evidence_targets, status
            FROM claims
            WHERE issue_id LIKE '%CONSTITUTION%'
               OR issue_id LIKE '%DUE_PROCESS%'
               OR issue_id LIKE '%EX_PARTE%'
               OR issue_id LIKE '%EQUAL_PROTECTION%'
               OR proposition LIKE '%due process%'
               OR proposition LIKE '%constitutional%'
               OR proposition LIKE '%retaliat%'
            ORDER BY status DESC
        """).fetchall()
        for r in rows:
            results.append({
                "claim_id": r["claim_id"],
                "issue_id": r["issue_id"],
                "classification": r["classification"],
                "actor": r["actor"],
                "proposition": safe_trunc(r["proposition"], 250),
                "evidence_targets": r["evidence_targets"],
                "status": r["status"],
            })
        print(f"    Found {len(results)} constitutional claims")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_authority_chains(conn):
    """Pull authority chains for constitutional case law."""
    print("  [6/7] Querying authority_chains for constitutional authorities...")
    results = []
    try:
        rows = conn.execute("""
            SELECT id, filing_vehicle, fact_claim, authority_cite, authority_type,
                   elements, evidence_quote, chain_complete, gap_description
            FROM authority_chains
            ORDER BY chain_complete DESC, filing_vehicle
        """).fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "vehicle": r["filing_vehicle"],
                "claim": r["fact_claim"],
                "cite": r["authority_cite"],
                "type": r["authority_type"],
                "elements": safe_trunc(r["elements"], 200),
                "evidence": safe_trunc(r["evidence_quote"], 200),
                "complete": bool(r["chain_complete"]),
                "gap": r["gap_description"],
            })
        print(f"    Found {len(results)} authority chains")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_evidence_quotes_constitutional(conn):
    """Pull evidence quotes with constitutional relevance."""
    print("  [7/7] Querying evidence_quotes for constitutional references...")
    results = []
    try:
        rows = conn.execute("""
            SELECT id, document_id, page_number, quote_text, speaker,
                   date_ref, legal_significance, source_type
            FROM evidence_quotes
            WHERE quote_text LIKE '%due process%'
               OR quote_text LIKE '%equal protection%'
               OR quote_text LIKE '%retaliat%'
               OR quote_text LIKE '%constitutional%'
               OR quote_text LIKE '%amendment%'
               OR quote_text LIKE '%seizure%'
               OR quote_text LIKE '%petition%right%'
            LIMIT 100
        """).fetchall()
        for r in rows:
            amendment = classify_amendment(r["quote_text"] or "")
            results.append({
                "id": r["id"],
                "text": safe_trunc(r["quote_text"], 300),
                "speaker": r["speaker"],
                "date_ref": r["date_ref"],
                "source_type": r["source_type"],
                "amendment_classification": amendment,
            })
        print(f"    Found {len(results)} constitutional evidence quotes")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def classify_amendment(text):
    """Classify text into applicable amendment category."""
    t = text.lower()
    matches = []
    for key, amend in AMENDMENTS.items():
        for kw in amend["keywords"]:
            if kw in t:
                matches.append(key)
                break
    return matches if matches else ["UNCLASSIFIED"]


def compute_severity_score(amendment_key, item):
    """Compute severity score 1-5 based on amendment weight and item severity."""
    base = AMENDMENTS.get(amendment_key, {}).get("severity_weight", 3)
    sev_str = str(item.get("severity", "")).upper()
    sev_map = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "MINIMAL": 1}
    item_sev = sev_map.get(sev_str, 3)
    return min(5, max(1, (base + item_sev) // 2))


def build_per_amendment_analysis(cv_table, rights_tracker, jv_const, claims, eq_const):
    """Build per-amendment violation analysis."""
    analysis = {}
    for key, amend in AMENDMENTS.items():
        analysis[key] = {
            "name": amend["name"],
            "test": amend["test"],
            "direct_violations": [],
            "judicial_violations": [],
            "claims": [],
            "evidence_quotes": [],
            "total_count": 0,
            "max_severity": 0,
        }

    # Map constitutional_violations table
    for cv in cv_table:
        amend_text = (cv.get("amendment") or "").lower()
        clause_text = (cv.get("clause") or "").lower()
        combined = amend_text + " " + clause_text + " " + (cv.get("description") or "").lower()
        matched = False
        for key in AMENDMENTS:
            for kw in AMENDMENTS[key]["keywords"]:
                if kw in combined:
                    analysis[key]["direct_violations"].append(cv)
                    analysis[key]["total_count"] += 1
                    sev = compute_severity_score(key, cv)
                    analysis[key]["max_severity"] = max(analysis[key]["max_severity"], sev)
                    matched = True
                    break
            if matched:
                break
        if not matched:
            # Default to 14th Due Process for unmatched
            if "due process" in combined or "ex parte" in combined:
                analysis["14th_Due_Process"]["direct_violations"].append(cv)
                analysis["14th_Due_Process"]["total_count"] += 1

    # Map rights tracker
    for rt in rights_tracker:
        right_text = (rt.get("right") or "").lower()
        for key in AMENDMENTS:
            for kw in AMENDMENTS[key]["keywords"]:
                if kw in right_text:
                    analysis[key]["total_count"] += rt.get("violation_count", 0)
                    break

    # Map judicial violations
    for jv in jv_const:
        for akey in jv.get("amendment_classification", []):
            if akey in analysis:
                analysis[akey]["judicial_violations"].append(jv)
                analysis[akey]["total_count"] += 1

    # Map claims
    for cl in claims:
        combined = ((cl.get("issue_id") or "") + " " + (cl.get("proposition") or "")).lower()
        for key in AMENDMENTS:
            for kw in AMENDMENTS[key]["keywords"]:
                if kw in combined:
                    analysis[key]["claims"].append(cl)
                    analysis[key]["total_count"] += 1
                    break

    # Map evidence quotes
    for eq in eq_const:
        for akey in eq.get("amendment_classification", []):
            if akey in analysis:
                analysis[akey]["evidence_quotes"].append(eq)

    return analysis


def build_caselaw_mapping(authority_chains, cv_table, brief_sections):
    """Build case law mapping for constitutional arguments."""
    caselaw = {
        "controlling_federal": [],
        "controlling_michigan": [],
        "authority_chain_coverage": [],
    }

    # From constitutional_violations table
    seen_cases = set()
    for cv in cv_table:
        cl_text = cv.get("caselaw") or ""
        if cl_text and cl_text not in seen_cases:
            seen_cases.add(cl_text[:100])
            caselaw["controlling_federal"].append({
                "source": f"CV-{cv['id']}",
                "amendment": cv["amendment"],
                "caselaw": cl_text,
            })
        mi_text = cv.get("michigan_authority") or ""
        if mi_text and mi_text not in seen_cases:
            seen_cases.add(mi_text[:100])
            caselaw["controlling_michigan"].append({
                "source": f"CV-{cv['id']}",
                "amendment": cv["amendment"],
                "authority": mi_text,
            })

    # From brief sections
    for bs in brief_sections:
        cites = bs.get("citations") or ""
        if cites:
            caselaw["controlling_federal"].append({
                "source": f"Brief-{bs['id']}",
                "right": bs["right_name"],
                "caselaw": cites,
            })

    # Authority chain coverage
    for ac in authority_chains:
        caselaw["authority_chain_coverage"].append({
            "vehicle": ac["vehicle"],
            "claim": ac["claim"],
            "cite": ac["cite"],
            "complete": ac["complete"],
            "gap": ac.get("gap"),
        })

    return caselaw


def main():
    ts = datetime.now()
    print("=" * 70)
    print("  TOOL #236 — CONSTITUTIONAL VIOLATION MAPPER")
    print(f"  Pigors v. Watson | {ts.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    conn = get_conn()

    # ── Gather data ──
    cv_table = query_constitutional_violations_table(conn)
    rights_tracker = query_constitutional_rights_tracker(conn)
    brief_sections = query_constitutional_brief_sections(conn)
    jv_const = query_judicial_violations_constitutional(conn)
    claims = query_claims_constitutional(conn)
    authority_chains = query_authority_chains(conn)
    eq_const = query_evidence_quotes_constitutional(conn)

    conn.close()

    # ── Analysis ──
    print("\n  Building per-amendment analysis...")
    amendment_analysis = build_per_amendment_analysis(
        cv_table, rights_tracker, jv_const, claims, eq_const
    )

    print("  Building case law mapping...")
    caselaw_map = build_caselaw_mapping(authority_chains, cv_table, brief_sections)

    # ── JSON output ──
    json_data = {
        "tool": "#236 — Constitutional Violation Mapper",
        "generated": ts.isoformat(),
        "case": "Pigors v. Watson (2024-001507-DC)",
        "summary": {
            "constitutional_violations_table": len(cv_table),
            "rights_tracker_entries": len(rights_tracker),
            "brief_sections": len(brief_sections),
            "judicial_violations_constitutional": len(jv_const),
            "constitutional_claims": len(claims),
            "authority_chains": len(authority_chains),
            "evidence_quotes_constitutional": len(eq_const),
        },
        "per_amendment_analysis": {},
        "caselaw_mapping": caselaw_map,
        "brief_sections_detail": brief_sections,
        "authority_chains_detail": authority_chains,
    }

    # Serialize amendment analysis
    for key, data in amendment_analysis.items():
        json_data["per_amendment_analysis"][key] = {
            "name": data["name"],
            "test": data["test"],
            "total_count": data["total_count"],
            "max_severity": data["max_severity"],
            "direct_violations_count": len(data["direct_violations"]),
            "judicial_violations_count": len(data["judicial_violations"]),
            "claims_count": len(data["claims"]),
            "evidence_quotes_count": len(data["evidence_quotes"]),
            "direct_violations": data["direct_violations"][:10],
            "judicial_violations": data["judicial_violations"][:10],
            "claims": data["claims"][:10],
            "evidence_quotes": data["evidence_quotes"][:10],
        }

    json_path = REPORTS_DIR / "tool_236_constitutional_violation_mapper.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n  JSON → {json_path}")

    # ── MD report ──
    md_path = REPORTS_DIR / "tool_236_constitutional_violation_mapper.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Tool #236 — Constitutional Violation Mapper\n\n")
        f.write(f"**Generated:** {ts.strftime('%Y-%m-%d %H:%M')}  \n")
        f.write("**Case:** Pigors v. Watson (2024-001507-DC)  \n")
        f.write("**Court:** 14th Circuit Court, Family Division, Muskegon County  \n\n")

        # Summary table
        f.write("---\n\n## Violation Summary by Amendment\n\n")
        f.write("| Amendment | Violations | Direct | Judicial | Claims | Evidence | Severity |\n")
        f.write("|-----------|-----------|--------|----------|--------|----------|----------|\n")
        total_all = 0
        for key, data in amendment_analysis.items():
            sev_label = {5: "CRITICAL", 4: "HIGH", 3: "MEDIUM", 2: "LOW", 1: "MINIMAL"}.get(
                data["max_severity"], "N/A")
            f.write(f"| {data['name'][:50]} | {data['total_count']} | "
                    f"{len(data['direct_violations'])} | {len(data['judicial_violations'])} | "
                    f"{len(data['claims'])} | {len(data['evidence_quotes'])} | {sev_label} |\n")
            total_all += data['total_count']
        f.write(f"| **TOTAL** | **{total_all}** | | | | | |\n\n")

        # Per-amendment detailed sections
        for key, data in amendment_analysis.items():
            f.write(f"---\n\n## {data['name']}\n\n")
            f.write(f"**Constitutional Text:** {AMENDMENTS[key]['text']}  \n\n")
            f.write(f"**Controlling Test:** {data['test']}  \n\n")
            f.write(f"**Total Violations:** {data['total_count']}  \n")
            f.write(f"**Maximum Severity:** {data['max_severity']}/5  \n\n")

            # Direct violations
            if data["direct_violations"]:
                f.write("### Direct Constitutional Violations\n\n")
                for i, dv in enumerate(data["direct_violations"][:5], 1):
                    f.write(f"**{i}. [{dv.get('violation_type', 'N/A')}]** — "
                            f"{dv.get('incident_date', 'N/A')}  \n")
                    f.write(f"> {dv.get('description', 'N/A')}  \n")
                    f.write(f"Actors: {dv.get('actors', 'N/A')} | "
                            f"Severity: {dv.get('severity', 'N/A')}  \n")
                    if dv.get("caselaw"):
                        f.write(f"Case Law: {dv['caselaw']}  \n")
                    f.write("\n")

            # Judicial violations
            if data["judicial_violations"]:
                f.write("### Related Judicial Violations\n\n")
                for i, jv in enumerate(data["judicial_violations"][:5], 1):
                    f.write(f"**{i}.** [{jv.get('canon', 'N/A')}] — {jv.get('severity', 'N/A')}  \n")
                    f.write(f"> {jv.get('description', 'N/A')}  \n\n")

            # Claims
            if data["claims"]:
                f.write("### Supporting Claims\n\n")
                for i, cl in enumerate(data["claims"][:5], 1):
                    f.write(f"**{i}.** [{cl.get('issue_id', 'N/A')}] {cl.get('proposition', 'N/A')}  \n")
                    f.write(f"   Status: {cl.get('status', 'N/A')}  \n\n")

        # Case law mapping
        f.write("---\n\n## Case Law Mapping\n\n")
        f.write("### Controlling Federal Authority\n\n")
        for cl in caselaw_map["controlling_federal"][:10]:
            f.write(f"- **{cl.get('amendment') or cl.get('right', 'N/A')}**: "
                    f"{safe_trunc(cl.get('caselaw', ''), 200)}  \n")
        f.write("\n### Controlling Michigan Authority\n\n")
        for cl in caselaw_map["controlling_michigan"][:10]:
            f.write(f"- **{cl.get('amendment', 'N/A')}**: "
                    f"{safe_trunc(cl.get('authority', ''), 200)}  \n")

        # Authority chain coverage
        f.write("\n### Authority Chain Coverage\n\n")
        f.write("| Vehicle | Claim | Citation | Complete | Gap |\n")
        f.write("|---------|-------|----------|----------|-----|\n")
        for ac in authority_chains:
            gap = safe_trunc(ac.get("gap") or "None", 80).replace('|', '/')
            f.write(f"| {ac['vehicle']} | {safe_trunc(ac['claim'], 40)} | "
                    f"{ac['cite']} | {'✅' if ac['complete'] else '❌'} | {gap} |\n")

        # Brief sections
        if brief_sections:
            f.write("\n---\n\n## IRAC Brief Sections (Pre-Built)\n\n")
            for bs in brief_sections:
                f.write(f"### {bs['right_name']}\n\n")
                f.write(f"**Issue:** {bs['issue']}  \n\n")
                f.write(f"**Rule:** {bs['rule']}  \n\n")
                f.write(f"**Application:** {bs['application']}  \n\n")
                f.write(f"**Conclusion:** {bs['conclusion']}  \n\n")
                f.write(f"**Key Citations:** {bs['citations']}  \n\n")

        f.write("\n---\n*Generated by LitigationOS Tool #236*\n")

    print(f"  MD  → {md_path}")

    # ── Console summary ──
    print("\n" + "=" * 70)
    print("  CONSTITUTIONAL VIOLATION SUMMARY")
    print("=" * 70)
    for key, data in amendment_analysis.items():
        count = data["total_count"]
        sev = data["max_severity"]
        indicator = "🔴" if sev >= 4 else "🟡" if sev >= 2 else "⚪"
        print(f"  {indicator} {data['name'][:55]:55s} | {count:>6} violations | severity {sev}/5")
    print(f"\n  Total constitutional violations: {total_all}")
    print(f"  Authority chains: {len(authority_chains)} ({sum(1 for a in authority_chains if a['complete'])} complete)")
    print(f"  IRAC brief sections ready: {len(brief_sections)}")
    print("=" * 70)
    print("  COMPLETE")


if __name__ == "__main__":
    main()
