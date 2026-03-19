"""
Citation Gap Finder — MBP LitigationOS 2026
Find claims without supporting authority, missing citations, and weak authority chains.
"""

import sqlite3
import re
import json
from collections import defaultdict
from datetime import datetime

# Michigan Best Interest Factors MCL 722.23
BIF_FACTORS = {
    "a": "love, affection, and other emotional ties",
    "b": "capacity to give love, affection, and guidance",
    "c": "capacity to provide food, clothing, medical care",
    "d": "length of time in stable, satisfactory environment",
    "e": "permanence as a family unit of existing or proposed custodial home",
    "f": "moral fitness of the parties",
    "g": "mental and physical health of the parties",
    "h": "home, school, and community record of the child",
    "i": "reasonable preference of the child",
    "j": "willingness to facilitate close and continuing parent-child relationship",
    "k": "domestic violence",
    "l": "any other factor considered by the court to be relevant",
}

# Citation regex patterns
CITATION_PATTERNS = {
    "MCR": re.compile(r"MCR\s+\d+\.\d+(?:\([A-Za-z0-9]+\))*"),
    "MCL": re.compile(r"MCL\s+\d+\.\d+(?:\([a-z]\))*"),
    "MRE": re.compile(r"MRE\s+\d+(?:\([a-z0-9]+\))*"),
    "case_law": re.compile(
        r"[A-Z][a-z]+ v [A-Z][a-z]+,?\s*\d+\s*Mich\s*(?:App)?\s*\d+"
    ),
}


def _safe_query(conn, sql, params=(), fallback=None):
    """Execute a query with error handling for missing tables."""
    if fallback is None:
        fallback = []
    try:
        cur = conn.execute(sql, params)
        return cur.fetchall()
    except sqlite3.OperationalError:
        return fallback
    except sqlite3.DatabaseError:
        return fallback


class CitationGapFinder:
    """Finds citation gaps, unsupported claims, and weak authority chains."""

    def __init__(self, db_path=r"C:\Users\andre\LitigationOS\litigation_context.db"):
        self.db_path = db_path
        self._conn = None

    # -- connection management --------------------------------------------------

    def _connect(self):
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # -- core features ---------------------------------------------------------

    def find_unsupported_claims(self):
        """Find claims with no matching citation or authority chain.

        Returns list of dicts with claim info and severity rating.
        """
        conn = self._connect()

        claims = _safe_query(
            conn,
            "SELECT rowid, classification, actor, proposition, status FROM claims",
        )
        if not claims:
            return []

        citations = _safe_query(
            conn,
            "SELECT citation, cite_type, context, source_file FROM master_citations",
        )
        citation_texts = {
            row["citation"].lower() for row in citations if row["citation"]
        }

        chains = _safe_query(conn, "SELECT * FROM authority_chains")
        chain_claim_ids = set()
        for row in chains:
            for key in ("claim_id", "claim", "proposition"):
                try:
                    val = row[key]
                    if val is not None:
                        chain_claim_ids.add(str(val).lower())
                except (IndexError, KeyError):
                    continue

        results = []
        for claim in claims:
            prop = claim["proposition"] or ""
            prop_lower = prop.lower()
            classification = (claim["classification"] or "").lower()

            has_citation = any(ct in prop_lower for ct in citation_texts) or any(
                prop_lower in ct for ct in citation_texts
            )
            has_chain = (
                str(claim["rowid"]) in chain_claim_ids
                or prop_lower in chain_claim_ids
            )

            if has_citation and has_chain:
                continue

            # Severity rating
            severity = "LOW"
            if "722.23" in prop or "best interest" in prop_lower:
                severity = "HIGH"
            elif any(
                kw in prop_lower
                for kw in ("custody", "parenting time", "factor")
            ):
                severity = "HIGH"
            elif any(
                kw in prop_lower for kw in ("mcr", "procedure", "motion", "filing")
            ):
                severity = "MEDIUM"
            elif classification in ("custody", "parenting", "best_interest"):
                severity = "HIGH"

            results.append(
                {
                    "claim_id": claim["rowid"],
                    "classification": claim["classification"],
                    "actor": claim["actor"],
                    "proposition": prop,
                    "status": claim["status"],
                    "has_citation": has_citation,
                    "has_authority_chain": has_chain,
                    "severity": severity,
                }
            )

        results.sort(key=lambda r: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[r["severity"]])
        return results

    def find_citation_gaps_by_topic(self, topic):
        """Analyze citation coverage for a topic.

        Returns dict with rules found, cases found, gaps, and recommendations.
        """
        conn = self._connect()

        # Search master_citations
        citations = _safe_query(
            conn,
            "SELECT citation, cite_type, context, source_file FROM master_citations "
            "WHERE citation LIKE ? OR context LIKE ?",
            (f"%{topic}%", f"%{topic}%"),
        )

        # Search auth_rules via FTS if available, else LIKE fallback
        rules = _safe_query(
            conn,
            "SELECT rule_number, title, full_text, rule_type FROM auth_rules "
            "WHERE rowid IN (SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?)",
            (topic,),
        )
        if not rules:
            rules = _safe_query(
                conn,
                "SELECT rule_number, title, full_text, rule_type FROM auth_rules "
                "WHERE title LIKE ? OR full_text LIKE ?",
                (f"%{topic}%", f"%{topic}%"),
            )

        rules_found = [
            {"rule_number": r["rule_number"], "title": r["title"]} for r in rules
        ]
        cases_found = [
            {"citation": c["citation"], "type": c["cite_type"]}
            for c in citations
            if c["cite_type"] and "case" in (c["cite_type"] or "").lower()
        ]
        statutes_found = [
            {"citation": c["citation"], "type": c["cite_type"]}
            for c in citations
            if c["cite_type"]
            and c["cite_type"].lower() in ("mcr", "mcl", "mre", "statute", "rule")
        ]

        gaps = []
        recommendations = []

        if rules_found and not cases_found:
            gaps.append("Rules cited but no supporting case law found")
            recommendations.append(
                f"Research Michigan case law interpreting {rules_found[0]['rule_number']}"
            )
        if cases_found and not rules_found:
            gaps.append("Case law found but no governing rule citation")
            recommendations.append(
                "Identify the MCR/MCL provision the case law interprets"
            )
        if not rules_found and not cases_found:
            gaps.append(f"No authority found for topic: {topic}")
            recommendations.append(
                f"Conduct full authority search for '{topic}' in Michigan law"
            )
        if rules_found and cases_found and not statutes_found:
            gaps.append("Court rules and cases found but no statutory authority")
            recommendations.append("Search MCL for statutory basis")

        return {
            "topic": topic,
            "rules_found": rules_found,
            "cases_found": cases_found,
            "statutes_found": statutes_found,
            "gaps": gaps,
            "recommendations": recommendations,
        }

    def validate_citations(self, text):
        """Parse text for citations and validate each against the database.

        Returns dict with valid, invalid, and not_found lists.
        """
        conn = self._connect()
        found_citations = {}

        for cite_type, pattern in CITATION_PATTERNS.items():
            for match in pattern.finditer(text):
                cite_str = match.group(0).strip()
                found_citations[cite_str] = cite_type

        valid = []
        invalid = []
        not_found = []

        for cite_str, cite_type in found_citations.items():
            # Check auth_rules for MCR/MCL/MRE
            if cite_type in ("MCR", "MCL", "MRE"):
                # Extract rule number for matching
                num_match = re.search(r"\d+\.\d+", cite_str)
                rule_num = num_match.group(0) if num_match else cite_str

                rows = _safe_query(
                    conn,
                    "SELECT rule_number FROM auth_rules WHERE rule_number LIKE ?",
                    (f"%{rule_num}%",),
                )
                if rows:
                    valid.append(
                        {"citation": cite_str, "type": cite_type, "status": "verified"}
                    )
                    continue

            # Check master_citations
            rows = _safe_query(
                conn,
                "SELECT citation FROM master_citations WHERE citation LIKE ?",
                (f"%{cite_str}%",),
            )
            if rows:
                valid.append(
                    {"citation": cite_str, "type": cite_type, "status": "verified"}
                )
            else:
                not_found.append(
                    {
                        "citation": cite_str,
                        "type": cite_type,
                        "status": "not_in_database",
                    }
                )

        return {"valid": valid, "invalid": invalid, "not_found": not_found}

    def suggest_authorities(self, claim_text):
        """Suggest top 5 authorities matching a claim or argument.

        Uses FTS5 MATCH on auth_rules_fts and master_citations.
        """
        conn = self._connect()

        # Build FTS query: take significant words, join with OR
        words = re.findall(r"[a-zA-Z]{4,}", claim_text)
        stop = {
            "that", "this", "with", "from", "have", "been", "were", "will",
            "shall", "would", "could", "should", "their", "there", "they",
            "which", "where", "when", "what", "does", "into", "also", "each",
            "other", "than", "then", "both", "about", "after", "before",
            "under", "over",
        }
        keywords = [w for w in words if w.lower() not in stop][:10]
        if not keywords:
            return []

        fts_query = " OR ".join(keywords)
        suggestions = []

        # Search auth_rules via FTS
        rule_rows = _safe_query(
            conn,
            "SELECT rule_number, title, full_text FROM auth_rules "
            "WHERE rowid IN (SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?)"
            " LIMIT 10",
            (fts_query,),
        )
        for row in rule_rows:
            text_lower = ((row["full_text"] or "") + " " + (row["title"] or "")).lower()
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            suggestions.append(
                {
                    "authority": row["rule_number"],
                    "title": row["title"],
                    "type": "rule",
                    "relevance_score": score / max(len(keywords), 1),
                }
            )

        # Search master_citations
        like_clauses = " OR ".join(["context LIKE ?" for _ in keywords])
        like_params = [f"%{kw}%" for kw in keywords]
        cite_rows = _safe_query(
            conn,
            f"SELECT citation, cite_type, context FROM master_citations "
            f"WHERE {like_clauses} LIMIT 10",
            like_params,
        )
        for row in cite_rows:
            ctx = (row["context"] or "").lower()
            score = sum(1 for kw in keywords if kw.lower() in ctx)
            suggestions.append(
                {
                    "authority": row["citation"],
                    "title": row["context"][:120] if row["context"] else "",
                    "type": row["cite_type"] or "case_law",
                    "relevance_score": score / max(len(keywords), 1),
                }
            )

        suggestions.sort(key=lambda s: s["relevance_score"], reverse=True)
        return suggestions[:5]

    def build_authority_matrix(self, lane=None):
        """Map each claim to its supporting authorities and compute coverage.

        Returns list of dicts: claim, authorities, coverage_score, gaps.
        """
        conn = self._connect()

        if lane:
            claims = _safe_query(
                conn,
                "SELECT rowid, classification, actor, proposition, status FROM claims "
                "WHERE classification LIKE ?",
                (f"%{lane}%",),
            )
        else:
            claims = _safe_query(
                conn,
                "SELECT rowid, classification, actor, proposition, status FROM claims",
            )
        if not claims:
            return []

        # Build inverted index: keyword -> list of citations (fast lookup)
        all_citations = _safe_query(
            conn,
            "SELECT citation, cite_type, context FROM master_citations",
        )
        keyword_index = defaultdict(list)
        for cite in all_citations:
            cite_entry = {"citation": cite["citation"], "type": cite["cite_type"]}
            for field in (cite["citation"], cite["context"]):
                if not field:
                    continue
                for word in field.lower().split():
                    if len(word) > 4:
                        keyword_index[word].append(cite_entry)

        matrix = []
        total_supported = 0

        for claim in claims:
            prop = claim["proposition"] or ""
            prop_lower = prop.lower()
            seen = set()
            authorities = []

            for kw in prop_lower.split():
                if len(kw) <= 4:
                    continue
                for entry in keyword_index.get(kw, []):
                    cit = entry["citation"]
                    if cit not in seen:
                        seen.add(cit)
                        authorities.append(entry)
                if len(authorities) >= 10:
                    break

            coverage = min(len(authorities) / 3.0, 1.0) if authorities else 0.0
            gaps = []
            if coverage == 0:
                gaps.append("No supporting authority found")
            elif coverage < 0.5:
                gaps.append("Weak authority support — needs additional citations")

            has_rule = any(
                a["type"] in ("MCR", "MCL", "MRE", "rule", "statute")
                for a in authorities
                if a["type"]
            )
            has_case = any(
                a["type"] in ("case", "case_law") for a in authorities if a["type"]
            )
            if has_rule and not has_case:
                gaps.append("Has rule citation but no supporting case law")
            if has_case and not has_rule:
                gaps.append("Has case law but no governing rule citation")

            if coverage >= 0.5:
                total_supported += 1

            matrix.append(
                {
                    "claim_id": claim["rowid"],
                    "classification": claim["classification"],
                    "proposition": prop[:200],
                    "authorities": authorities[:10],
                    "coverage_score": round(coverage, 2),
                    "gaps": gaps,
                }
            )

        matrix.sort(key=lambda m: m["coverage_score"])
        return matrix

    def find_missing_bif_citations(self):
        """Check each Best Interest Factor (a)-(l) for evidence AND authority gaps.

        Returns per-factor analysis with evidence/authority status and gaps.
        """
        conn = self._connect()
        results = []

        for factor_key, factor_desc in BIF_FACTORS.items():
            factor_label = f"MCL 722.23({factor_key})"
            search_terms = [
                f"722.23({factor_key})",
                f"factor {factor_key}",
                factor_desc,
            ]

            # Check for authority
            has_authority = False
            authority_sources = []
            for term in search_terms:
                rows = _safe_query(
                    conn,
                    "SELECT citation, context FROM master_citations "
                    "WHERE citation LIKE ? OR context LIKE ?",
                    (f"%{term}%", f"%{term}%"),
                )
                if rows:
                    has_authority = True
                    authority_sources.extend(
                        [{"citation": r["citation"]} for r in rows[:3]]
                    )

            # Also check auth_rules
            rule_rows = _safe_query(
                conn,
                "SELECT rule_number, title FROM auth_rules "
                "WHERE full_text LIKE ? OR title LIKE ?",
                (f"%722.23%{factor_key}%", f"%factor {factor_key}%"),
            )
            if rule_rows:
                has_authority = True
                authority_sources.extend(
                    [{"rule": r["rule_number"]} for r in rule_rows[:3]]
                )

            # Check for evidence
            has_evidence = False
            evidence_sources = []
            for term in [factor_desc] + factor_desc.split(","):
                term = term.strip()
                if len(term) < 4:
                    continue
                rows = _safe_query(
                    conn,
                    "SELECT quote_text, speaker, evidence_category FROM evidence_quotes "
                    "WHERE quote_text LIKE ? OR evidence_category LIKE ? LIMIT 5",
                    (f"%{term}%", f"%{term}%"),
                )
                if rows:
                    has_evidence = True
                    evidence_sources.extend(
                        [
                            {
                                "quote": (r["quote_text"] or "")[:120],
                                "speaker": r["speaker"],
                            }
                            for r in rows[:3]
                        ]
                    )

            gaps = []
            if not has_authority and not has_evidence:
                gaps.append(f"CRITICAL: No authority or evidence for {factor_label}")
            elif has_evidence and not has_authority:
                gaps.append(f"Evidence exists but no authority cited for {factor_label}")
            elif has_authority and not has_evidence:
                gaps.append(f"Authority cited but no supporting evidence for {factor_label}")

            results.append(
                {
                    "factor": factor_key,
                    "label": factor_label,
                    "description": factor_desc,
                    "has_authority": has_authority,
                    "has_evidence": has_evidence,
                    "authority_sources": authority_sources[:5],
                    "evidence_sources": evidence_sources[:5],
                    "gaps": gaps,
                    "status": (
                        "COMPLETE"
                        if has_authority and has_evidence
                        else "PARTIAL" if has_authority or has_evidence
                        else "MISSING"
                    ),
                }
            )

        return results

    def generate_gap_report(self, lane=None):
        """Complete gap analysis report with priorities and recommendations."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "lane": lane or "ALL",
            "unsupported_claims": {},
            "authority_matrix_summary": {},
            "bif_analysis": {},
            "filing_readiness": {},
            "action_scores": {},
            "recommendations": [],
            "priority_gaps": [],
        }

        conn = self._connect()

        # 1. Unsupported claims
        unsupported = self.find_unsupported_claims()
        high = [c for c in unsupported if c["severity"] == "HIGH"]
        medium = [c for c in unsupported if c["severity"] == "MEDIUM"]
        low = [c for c in unsupported if c["severity"] == "LOW"]
        report["unsupported_claims"] = {
            "total": len(unsupported),
            "high_severity": len(high),
            "medium_severity": len(medium),
            "low_severity": len(low),
            "top_high": high[:10],
        }

        # 2. Authority matrix
        matrix = self.build_authority_matrix(lane=lane)
        if matrix:
            scores = [m["coverage_score"] for m in matrix]
            avg_coverage = sum(scores) / len(scores) if scores else 0
            fully = sum(1 for s in scores if s >= 0.8)
            partial = sum(1 for s in scores if 0.2 <= s < 0.8)
            none_ = sum(1 for s in scores if s < 0.2)
            report["authority_matrix_summary"] = {
                "total_claims": len(matrix),
                "avg_coverage": round(avg_coverage, 2),
                "fully_supported": fully,
                "partially_supported": partial,
                "unsupported": none_,
            }

        # 3. BIF analysis
        bif = self.find_missing_bif_citations()
        complete = sum(1 for f in bif if f["status"] == "COMPLETE")
        partial_bif = sum(1 for f in bif if f["status"] == "PARTIAL")
        missing = sum(1 for f in bif if f["status"] == "MISSING")
        report["bif_analysis"] = {
            "complete": complete,
            "partial": partial_bif,
            "missing": missing,
            "factors": bif,
        }

        # 4. Filing readiness from DB
        readiness = _safe_query(
            conn,
            "SELECT * FROM filing_readiness" + (" WHERE lane = ?" if lane else ""),
            (lane,) if lane else (),
        )
        if readiness:
            report["filing_readiness"] = [dict(r) for r in readiness[:10]]

        # 5. Legal action scores
        actions = _safe_query(
            conn,
            "SELECT action_name, lane, overall_score, gaps FROM legal_action_scores"
            + (" WHERE lane = ?" if lane else ""),
            (lane,) if lane else (),
        )
        if actions:
            report["action_scores"] = [dict(a) for a in actions[:10]]

        # 6. Recommendations
        if report["unsupported_claims"]["high_severity"] > 0:
            report["recommendations"].append(
                "URGENT: Address HIGH-severity unsupported claims — "
                "custody factor arguments without citation are vulnerable to attack"
            )
        if missing > 0:
            factors_missing = [f["label"] for f in bif if f["status"] == "MISSING"]
            report["recommendations"].append(
                f"CRITICAL: BIF factors with no authority or evidence: "
                f"{', '.join(factors_missing)}"
            )
        if partial_bif > 0:
            report["recommendations"].append(
                "Fill partial BIF gaps — factors with evidence but no authority "
                "or vice versa need completion"
            )

        # Priority gaps (sorted by impact)
        for c in high[:5]:
            report["priority_gaps"].append(
                {
                    "type": "unsupported_claim",
                    "severity": "HIGH",
                    "description": c["proposition"][:200],
                }
            )
        for f in bif:
            if f["status"] == "MISSING":
                report["priority_gaps"].append(
                    {
                        "type": "missing_bif_factor",
                        "severity": "CRITICAL",
                        "description": f"No authority or evidence for {f['label']}",
                    }
                )

        return report

    def export_gap_tickets(self):
        """Create/update gap_tickets table entries for each found gap."""
        conn = self._connect()

        # Ensure gap_tickets table exists
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS gap_tickets ("
                "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "  gap_type TEXT,"
                "  description TEXT,"
                "  severity TEXT,"
                "  resolution_status TEXT DEFAULT 'open',"
                "  source TEXT,"
                "  created_at TEXT,"
                "  updated_at TEXT"
                ")"
            )
            conn.commit()
        except sqlite3.OperationalError:
            pass

        now = datetime.now().isoformat()
        tickets_created = 0

        # From unsupported claims
        unsupported = self.find_unsupported_claims()
        for claim in unsupported:
            desc = (
                f"Unsupported claim [{claim['classification']}]: "
                f"{(claim['proposition'] or '')[:300]}"
            )
            # Skip duplicates
            existing = _safe_query(
                conn,
                "SELECT id FROM gap_tickets WHERE description = ? AND resolution_status = 'open'",
                (desc,),
            )
            if not existing:
                try:
                    conn.execute(
                        "INSERT INTO gap_tickets (gap_type, description, severity, "
                        "resolution_status, source, created_at, updated_at) "
                        "VALUES (?, ?, ?, 'open', 'citation_gap_finder', ?, ?)",
                        ("unsupported_claim", desc, claim["severity"], now, now),
                    )
                    tickets_created += 1
                except sqlite3.OperationalError:
                    pass

        # From BIF gaps
        bif = self.find_missing_bif_citations()
        for factor in bif:
            for gap in factor["gaps"]:
                existing = _safe_query(
                    conn,
                    "SELECT id FROM gap_tickets WHERE description = ? AND resolution_status = 'open'",
                    (gap,),
                )
                if not existing:
                    severity = "CRITICAL" if "CRITICAL" in gap else "HIGH"
                    try:
                        conn.execute(
                            "INSERT INTO gap_tickets (gap_type, description, severity, "
                            "resolution_status, source, created_at, updated_at) "
                            "VALUES (?, ?, ?, 'open', 'citation_gap_finder', ?, ?)",
                            ("bif_gap", gap, severity, now, now),
                        )
                        tickets_created += 1
                    except sqlite3.OperationalError:
                        pass

        try:
            conn.commit()
        except sqlite3.OperationalError:
            pass

        return {"tickets_created": tickets_created, "timestamp": now}


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import os

    db_path = r"C:\Users\andre\LitigationOS\litigation_context.db"
    if not os.path.exists(db_path):
        print(f"[SKIP] Database not found at {db_path}")
        raise SystemExit(0)

    finder = CitationGapFinder(db_path)
    try:
        print("=== Citation Gap Finder — Smoke Test ===\n")

        # 1. Unsupported claims
        unsupported = finder.find_unsupported_claims()
        print(f"[1] Unsupported claims: {len(unsupported)}")
        for c in unsupported[:3]:
            print(f"    {c['severity']:6s} | {(c['proposition'] or '')[:80]}")

        # 2. Topic gap analysis
        topic_result = finder.find_citation_gaps_by_topic("custody")
        print(f"\n[2] Topic 'custody': {len(topic_result['rules_found'])} rules, "
              f"{len(topic_result['cases_found'])} cases, "
              f"{len(topic_result['gaps'])} gaps")

        # 3. Validate sample text
        sample = "Under MCR 2.116(C)(10) and MCL 722.23(j), the court must consider..."
        validation = finder.validate_citations(sample)
        print(f"\n[3] Citation validation: {len(validation['valid'])} valid, "
              f"{len(validation['not_found'])} not found")

        # 4. Suggest authorities
        suggestions = finder.suggest_authorities(
            "parental alienation and willingness to facilitate relationship"
        )
        print(f"\n[4] Suggested authorities: {len(suggestions)}")
        for s in suggestions[:3]:
            print(f"    {s['relevance_score']:.2f} | {s['authority']}")

        # 5. Authority matrix
        matrix = finder.build_authority_matrix()
        if matrix:
            scores = [m["coverage_score"] for m in matrix]
            avg = sum(scores) / len(scores)
            print(f"\n[5] Authority matrix: {len(matrix)} claims, avg coverage {avg:.2f}")

        # 6. BIF citations
        bif = finder.find_missing_bif_citations()
        complete = sum(1 for f in bif if f["status"] == "COMPLETE")
        partial = sum(1 for f in bif if f["status"] == "PARTIAL")
        missing = sum(1 for f in bif if f["status"] == "MISSING")
        print(f"\n[6] BIF factors: {complete} complete, {partial} partial, {missing} missing")

        # 7. Gap report
        report = finder.generate_gap_report()
        print(f"\n[7] Gap report: {report['unsupported_claims']['total']} unsupported, "
              f"{len(report['priority_gaps'])} priority gaps")

        # 8. Export tickets
        ticket_result = finder.export_gap_tickets()
        print(f"\n[8] Gap tickets created: {ticket_result['tickets_created']}")

        print("\n=== Smoke test complete ===")
    finally:
        finder.close()
