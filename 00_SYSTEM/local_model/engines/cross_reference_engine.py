# -*- coding: utf-8 -*-
"""
Cross-Reference Engine — LitigationOS MANBEARPIG v8.0
=======================================================
Cross-reference claims, facts, and evidence across all filings to prevent
inconsistency and strengthen credibility.

Queries:
    claims (653 entries), claim_evidence_links (5,910 entries),
    evidence_quotes (308K), documents, contradiction_map (10,672)

Usage:
    python cross_reference_engine.py
"""

import sys
import os
import io
import sqlite3
import json
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif sys.stdout is None or not hasattr(sys.stdout, "encoding") or sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer if sys.stdout else open(os.devnull, "w"), encoding="utf-8")

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
FILINGS_DIR = r"C:\Users\andre\LitigationOS"
REPORT_PATH = os.path.join(FILINGS_DIR, "CONSISTENCY_REPORT.md")


def _get_db():
    """Get a database connection with row factory."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_query(query: str, params: tuple = (), timeout: int = 30) -> List[Dict]:
    """Execute a query safely with a timeout, returning list of dicts."""
    try:
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database not found: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH, timeout=timeout)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except (sqlite3.OperationalError, FileNotFoundError) as e:
        return [{"error": str(e)}]


# ---------------------------------------------------------------------------
# Core cross-reference functions
# ---------------------------------------------------------------------------

def get_all_claims() -> List[Dict]:
    """Retrieve all claims from the claims table."""
    return _safe_query(
        "SELECT claim_id, issue_id, doc, classification, actor, proposition, "
        "status FROM claims ORDER BY claim_id"
    )


def get_claim_evidence_map() -> Dict[str, List[Dict]]:
    """
    Map each claim to its supporting evidence.
    Uses lightweight query (no JOIN on large evidence_quotes table).

    Returns:
        Dict keyed by claim_id → list of evidence links.
    """
    links = _safe_query(
        "SELECT claim_id, evidence_id, relevance_score, link_method "
        "FROM claim_evidence_links "
        "ORDER BY claim_id, relevance_score DESC"
    )
    if links and "error" in links[0]:
        return {"_error": links}

    result = defaultdict(list)
    for link in links:
        result[link["claim_id"]].append(link)
    return dict(result)


def get_claims_by_document() -> Dict[str, List[Dict]]:
    """
    Group claims by source document.

    Returns:
        Dict keyed by document name → list of claims.
    """
    claims = get_all_claims()
    if claims and "error" in claims[0]:
        return {"_error": claims}

    result = defaultdict(list)
    for c in claims:
        doc = c.get("doc", "unknown")
        result[doc].append(c)
    return dict(result)


def check_consistency(filing_path: Optional[str] = None) -> Dict:
    """
    Check cross-filing consistency of claims and facts.

    Args:
        filing_path: Optional path to a specific filing to check.
                     If None, checks all claims across all filings.

    Returns:
        Dict with consistency analysis results.
    """
    claims = get_all_claims()
    if claims and "error" in claims[0]:
        return {"error": claims[0]["error"], "consistent": False}

    # Group claims by proposition (normalized)
    prop_groups = defaultdict(list)
    for c in claims:
        prop = c.get("proposition", "")
        if not prop:
            continue
        # Normalize: lowercase, strip extra whitespace
        key = re.sub(r'\s+', ' ', prop.lower().strip())
        prop_groups[key].append(c)

    # Find propositions that appear in multiple documents with different statuses
    inconsistencies = []
    for prop_key, claim_list in prop_groups.items():
        if len(claim_list) < 2:
            continue
        docs = set(c.get("doc", "") for c in claim_list)
        statuses = set(c.get("status", "") for c in claim_list)
        if len(docs) > 1 and len(statuses) > 1:
            inconsistencies.append({
                "proposition": claim_list[0].get("proposition", prop_key),
                "documents": list(docs),
                "statuses": list(statuses),
                "claim_ids": [c["claim_id"] for c in claim_list],
                "severity": "HIGH" if "contradicted" in statuses else "MEDIUM",
            })

    # Filter by filing path if specified
    if filing_path:
        filing_name = os.path.basename(filing_path)
        inconsistencies = [
            i for i in inconsistencies
            if any(filing_name.lower() in d.lower() for d in i["documents"])
        ]

    return {
        "consistent": len(inconsistencies) == 0,
        "total_claims": len(claims),
        "inconsistency_count": len(inconsistencies),
        "inconsistencies": inconsistencies[:50],  # Cap output
        "checked_at": datetime.now().isoformat(),
    }


def find_conflicting_claims() -> List[Dict]:
    """
    Find claims that directly conflict with each other using the contradiction_map.

    Returns:
        List of conflicting claim pairs with details.
    """
    # First try contradiction_map table (sample columns to avoid SELECT *)
    contradictions = _safe_query(
        "SELECT rowid, * FROM contradiction_map LIMIT 100"
    )

    if contradictions and "error" not in contradictions[0]:
        return contradictions

    # Fallback: find claims with opposite actors/propositions
    claims = get_all_claims()
    if claims and "error" in claims[0]:
        return claims

    conflicts = []
    claim_list = [c for c in claims if c.get("proposition")]

    # Compare claims pairwise (sampling for performance)
    seen = set()
    for i, c1 in enumerate(claim_list):
        for c2 in claim_list[i + 1:]:
            if c1["doc"] == c2["doc"]:
                continue
            # Check if same issue but different actors with opposing propositions
            if (c1.get("issue_id") == c2.get("issue_id") and
                    c1.get("actor") != c2.get("actor") and
                    c1.get("status") != c2.get("status")):
                pair_key = tuple(sorted([c1["claim_id"], c2["claim_id"]]))
                if pair_key not in seen:
                    seen.add(pair_key)
                    conflicts.append({
                        "claim_1": c1["claim_id"],
                        "claim_1_doc": c1["doc"],
                        "claim_1_prop": c1["proposition"][:100],
                        "claim_2": c2["claim_id"],
                        "claim_2_doc": c2["doc"],
                        "claim_2_prop": c2["proposition"][:100],
                        "issue": c1.get("issue_id", ""),
                    })
            if len(conflicts) >= 50:
                break
        if len(conflicts) >= 50:
            break

    return conflicts


def map_claim_to_filings() -> Dict[str, Dict]:
    """
    Map each claim to all filings where it appears or should appear.

    Returns:
        Dict keyed by claim_id → {claim info, filings, evidence_count}
    """
    claims = get_all_claims()
    evidence_map = get_claim_evidence_map()

    if (claims and "error" in claims[0]):
        return {"_error": claims[0]}

    result = {}
    for c in claims:
        cid = c["claim_id"]
        evidence = evidence_map.get(cid, [])
        result[cid] = {
            "claim_id": cid,
            "proposition": c.get("proposition", "")[:200],
            "source_document": c.get("doc", ""),
            "classification": c.get("classification", ""),
            "status": c.get("status", ""),
            "evidence_count": len(evidence),
            "avg_relevance": (
                sum(e.get("relevance_score", 0) or 0 for e in evidence) / len(evidence)
                if evidence else 0
            ),
        }

    return result


def get_evidence_coverage() -> Dict:
    """
    Analyze evidence coverage: which claims are well-supported vs. unsupported.

    Returns:
        Coverage statistics and lists of under-supported claims.
    """
    evidence_map = get_claim_evidence_map()
    claims = get_all_claims()

    if (claims and "error" in claims[0]):
        return {"error": claims[0]["error"]}

    unsupported = []
    weak = []
    strong = []

    for c in claims:
        cid = c["claim_id"]
        links = evidence_map.get(cid, [])
        count = len(links)

        if count == 0:
            unsupported.append({
                "claim_id": cid,
                "proposition": c.get("proposition", "")[:150],
                "doc": c.get("doc", ""),
            })
        elif count <= 2:
            weak.append({"claim_id": cid, "evidence_count": count})
        else:
            strong.append({"claim_id": cid, "evidence_count": count})

    return {
        "total_claims": len(claims),
        "total_evidence_links": sum(len(v) for v in evidence_map.values()),
        "unsupported_count": len(unsupported),
        "weak_count": len(weak),
        "strong_count": len(strong),
        "coverage_pct": round(
            (len(strong) + len(weak)) / max(len(claims), 1) * 100, 1
        ),
        "unsupported_claims": unsupported[:20],
        "authority": "Every factual assertion must be supported — MRE 602, MRE 901",
    }


def generate_consistency_report() -> str:
    """
    Generate a comprehensive CONSISTENCY_REPORT.md.

    Analyzes all claims, evidence, and cross-filing consistency,
    then writes the report to FILINGS_DIR.

    Returns:
        Path to the generated report.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    consistency = check_consistency()
    conflicts = find_conflicting_claims()
    coverage = get_evidence_coverage()
    claims_by_doc = get_claims_by_document()

    lines = [
        f"# CONSISTENCY REPORT — Pigors v Watson",
        f"",
        f"**Generated:** {now}",
        f"**Engine:** Cross-Reference Engine v8.0 — LitigationOS MANBEARPIG",
        f"**Database:** {DB_PATH}",
        f"",
        f"---",
        f"",
        f"## 1. Overview",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Claims | {consistency.get('total_claims', 'N/A')} |",
        f"| Inconsistencies Found | {consistency.get('inconsistency_count', 'N/A')} |",
        f"| Conflicting Claim Pairs | {len(conflicts) if isinstance(conflicts, list) and (not conflicts or 'error' not in conflicts[0]) else 'DB error'} |",
        f"| Evidence Coverage | {coverage.get('coverage_pct', 'N/A')}% |",
        f"| Unsupported Claims | {coverage.get('unsupported_count', 'N/A')} |",
        f"| Total Evidence Links | {coverage.get('total_evidence_links', 'N/A')} |",
        f"",
        f"## 2. Cross-Filing Consistency",
        f"",
    ]

    if consistency.get("consistent"):
        lines.append("✅ **All claims are consistent across filings.**\n")
    else:
        lines.append(f"⚠️ **{consistency['inconsistency_count']} inconsistencies detected:**\n")
        for i, inc in enumerate(consistency.get("inconsistencies", [])[:20], 1):
            lines.append(f"### Inconsistency #{i} [{inc.get('severity', 'MEDIUM')}]")
            lines.append(f"- **Proposition:** {inc.get('proposition', 'N/A')[:200]}")
            lines.append(f"- **Documents:** {', '.join(inc.get('documents', []))}")
            lines.append(f"- **Statuses:** {', '.join(inc.get('statuses', []))}")
            lines.append(f"- **Claim IDs:** {', '.join(inc.get('claim_ids', []))}")
            lines.append("")

    lines += [
        f"## 3. Conflicting Claims",
        f"",
    ]

    if isinstance(conflicts, list) and conflicts and "error" not in conflicts[0]:
        for i, cf in enumerate(conflicts[:15], 1):
            lines.append(f"### Conflict #{i}")
            if "claim_1" in cf:
                lines.append(f"- **Claim 1** ({cf.get('claim_1_doc', '')}): {cf.get('claim_1_prop', '')}")
                lines.append(f"- **Claim 2** ({cf.get('claim_2_doc', '')}): {cf.get('claim_2_prop', '')}")
            else:
                lines.append(f"- {json.dumps(cf, default=str)[:300]}")
            lines.append("")
    else:
        lines.append("No conflicting claims detected (or contradiction_map query returned data).\n")

    lines += [
        f"## 4. Evidence Coverage",
        f"",
        f"| Category | Count |",
        f"|----------|-------|",
        f"| Strong (3+ evidence links) | {coverage.get('strong_count', 'N/A')} |",
        f"| Weak (1-2 evidence links) | {coverage.get('weak_count', 'N/A')} |",
        f"| Unsupported (0 links) | {coverage.get('unsupported_count', 'N/A')} |",
        f"",
    ]

    unsupported = coverage.get("unsupported_claims", [])
    if unsupported:
        lines.append("### Unsupported Claims (NEED EVIDENCE)")
        lines.append("")
        for u in unsupported[:15]:
            lines.append(f"- **{u.get('claim_id', '')}** ({u.get('doc', '')}): {u.get('proposition', '')}")
        lines.append("")

    lines += [
        f"## 5. Claims by Document",
        f"",
        f"| Document | Claims |",
        f"|----------|--------|",
    ]

    if "_error" not in claims_by_doc:
        for doc, claim_list in sorted(claims_by_doc.items(), key=lambda x: -len(x[1])):
            lines.append(f"| {doc[:50]} | {len(claim_list)} |")
    lines.append("")

    lines += [
        f"## 6. Recommendations",
        f"",
        f"1. Address all HIGH-severity inconsistencies before filing",
        f"2. Obtain evidence for unsupported claims or remove them",
        f"3. Ensure date references are identical across all filings",
        f"4. Cross-check separation day count in all documents",
        f"5. Verify all MCR/MCL citations are consistent",
        f"",
        f"---",
        f"*Report generated by Cross-Reference Engine — LitigationOS MANBEARPIG v8.0*",
    ]

    report_text = "\n".join(lines)

    # Write to file
    try:
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(report_text)
    except OSError as e:
        return f"Error writing report: {e}"

    return REPORT_PATH


def main():
    """CLI test harness."""
    print("=" * 70)
    print("CROSS-REFERENCE ENGINE — LitigationOS MANBEARPIG v8.0")
    print("=" * 70)

    # Test 1: Consistency check
    print("\n[TEST 1] Cross-filing consistency check:")
    result = check_consistency()
    print(f"  Consistent: {result.get('consistent')}")
    print(f"  Total claims: {result.get('total_claims')}")
    print(f"  Inconsistencies: {result.get('inconsistency_count')}")

    # Test 2: Conflicting claims
    print("\n[TEST 2] Conflicting claims (first 5):")
    conflicts = find_conflicting_claims()
    if conflicts and "error" not in conflicts[0]:
        for c in conflicts[:5]:
            if "claim_1" in c:
                print(f"  {c['claim_1']} vs {c['claim_2']} — issue: {c.get('issue', 'N/A')}")
            else:
                keys = list(c.keys())[:4]
                print(f"  {', '.join(f'{k}={c[k]}' for k in keys)}")
    else:
        print(f"  {conflicts[:1]}")

    # Test 3: Evidence coverage
    print("\n[TEST 3] Evidence coverage:")
    cov = get_evidence_coverage()
    for k, v in cov.items():
        if k == "unsupported_claims":
            print(f"  {k}: [{len(v)} claims]")
        else:
            print(f"  {k}: {v}")

    # Test 4: Claims by document
    print("\n[TEST 4] Claims by document (top 5):")
    by_doc = get_claims_by_document()
    if "_error" not in by_doc:
        for doc, claims in sorted(by_doc.items(), key=lambda x: -len(x[1]))[:5]:
            print(f"  {doc[:50]:50s} — {len(claims)} claims")

    # Test 5: Claim-to-filing map (sample)
    print("\n[TEST 5] Claim-to-filing map (first 5):")
    cmap = map_claim_to_filings()
    if "_error" not in cmap:
        for cid, info in list(cmap.items())[:5]:
            print(f"  {cid}: {info['evidence_count']} evidence, status={info['status']}")

    # Test 6: Generate report
    print("\n[TEST 6] Generating CONSISTENCY_REPORT.md:")
    path = generate_consistency_report()
    print(f"  Report written to: {path}")

    print("\n✓ Cross-Reference Engine — all tests complete.")


if __name__ == "__main__":
    main()
