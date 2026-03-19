"""
Adversarial Prediction Engine — LitigationOS 2026
==================================================
THE MANBEARPIG — Predict and prepare rebuttals for opposing counsel's
arguments in Pigors v. Watson.

Queries adversary_models, claims, auth_rules, evidence_quotes, and
risk_events to build attack trees, vulnerability scans, and anticipatory
response sections for court filings.

Usage:
    from adversarial_engine import AdversarialEngine
    engine = AdversarialEngine()
    attacks = engine.predict_attacks("motion")
    rebuttals = engine.generate_rebuttals(attacks)
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# Case lane reference for risk assessment
LANE_MAP: Dict[str, Dict[str, str]] = {
    "A": {"name": "Watson Custody", "case_no": "2024-001507-DC", "court": "14th Circuit"},
    "B": {"name": "Shady Oaks Housing", "case_no": "", "court": "Related"},
    "C": {"name": "Convergence", "case_no": "MULTI", "court": "Cross-lane"},
    "D": {"name": "PPO", "case_no": "2023-5907-PP", "court": "14th Circuit"},
    "E": {"name": "Judicial Misconduct", "case_no": "MULTI", "court": "JTC / MSC"},
    "F": {"name": "Appellate", "case_no": "COA 366810", "court": "Michigan COA"},
}

# Default family-law attack patterns when adversary_models is empty
DEFAULT_ATTACKS: List[Dict[str, str]] = [
    {
        "attack_type": "BEST_INTEREST_FACTORS",
        "attack_description": "Argue best-interest factors weigh against movant",
        "rebuttal_strategy": "Demonstrate favorable findings under MCL 722.23(a)-(l)",
        "rebuttal_authority": "MCL 722.23; Berger v Berger, 277 Mich App 700 (2008)",
        "risk_level": "HIGH",
    },
    {
        "attack_type": "ESTABLISHED_CUSTODIAL_ENVIRONMENT",
        "attack_description": "Claim established custodial environment should not be disrupted",
        "rebuttal_strategy": "Show change of circumstances warrants re-evaluation per Vodvarka",
        "rebuttal_authority": "MCL 722.27(1)(c); Vodvarka v Grasher, 259 Mich App 1 (2003)",
        "risk_level": "HIGH",
    },
    {
        "attack_type": "TIMELINESS",
        "attack_description": "Motion is untimely or waived by delay",
        "rebuttal_strategy": "Filing made as soon as grounds became known; no prejudice to opposing party",
        "rebuttal_authority": "MCR 2.003(D)(1)",
        "risk_level": "MEDIUM",
    },
    {
        "attack_type": "INSUFFICIENT_EVIDENCE",
        "attack_description": "Movant lacks sufficient evidentiary support",
        "rebuttal_strategy": "Present documented evidence from record and sworn testimony",
        "rebuttal_authority": "MRE 801; MCR 2.116(G)(6)",
        "risk_level": "MEDIUM",
    },
    {
        "attack_type": "PARENTAL_ALIENATION_DEFENSE",
        "attack_description": "Accuse movant of alienating behaviour under Factor J",
        "rebuttal_strategy": "Record shows consistent facilitation; opposing party obstructed parenting time",
        "rebuttal_authority": "MCL 722.23(j); Demski v Petlick, 309 Mich App 404 (2015)",
        "risk_level": "HIGH",
    },
]


class AdversarialEngine:
    """Predict opposing counsel attacks and generate pre-emptive rebuttals."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self._error_log: List[Dict[str, Any]] = []

    # ── DB helpers ──────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA query_only=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a read query with retry logic."""
        last_err: Optional[Exception] = None
        for attempt in range(3):
            try:
                conn = self._connect()
                try:
                    rows = conn.execute(sql, params).fetchall()
                    return [dict(r) for r in rows]
                finally:
                    conn.close()
            except sqlite3.Error as exc:
                last_err = exc
                self._error_log.append({
                    "ts": datetime.now().isoformat(),
                    "sql": sql[:200],
                    "attempt": attempt + 1,
                    "error": str(exc),
                })
                import time
                time.sleep(min(2 ** attempt, 4))
        # All retries exhausted
        self._error_log.append({
            "ts": datetime.now().isoformat(),
            "sql": sql[:200],
            "error": f"All retries failed: {last_err}",
        })
        return []

    def _table_exists(self, table: str) -> bool:
        rows = self._query(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        return len(rows) > 0

    # ── Core: predict_attacks ───────────────────────────────────────

    def predict_attacks(
        self,
        filing_type: str,
        claims_list: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Predict opposing counsel attacks for a given filing type.

        Returns ranked list of predicted attacks with likelihood scores,
        target claims, rebuttals, and authority.
        """
        # Load adversary models
        models = self._query(
            "SELECT attack_type, attack_description, weakness_exploited, "
            "rebuttal_strategy, rebuttal_authority, rebuttal_evidence, "
            "risk_level, filing_vehicle "
            "FROM adversary_models WHERE LOWER(filing_vehicle) LIKE ?",
            (f"%{filing_type.lower()}%",),
        )
        if not models:
            # Broaden: try all models
            models = self._query(
                "SELECT attack_type, attack_description, weakness_exploited, "
                "rebuttal_strategy, rebuttal_authority, rebuttal_evidence, "
                "risk_level, filing_vehicle FROM adversary_models"
            )
        if not models:
            # Fallback to defaults
            models = DEFAULT_ATTACKS

        # Load claims for mapping
        claims = []
        if claims_list:
            placeholders = ",".join("?" for _ in claims_list)
            claims = self._query(
                f"SELECT classification, actor, proposition, status "
                f"FROM claims WHERE classification IN ({placeholders})",
                tuple(claims_list),
            )
        if not claims:
            claims = self._query(
                "SELECT classification, actor, proposition, status "
                "FROM claims WHERE LOWER(status) != 'dismissed' LIMIT 50"
            )

        # Score attacks by frequency of attack_type
        type_counts: Counter = Counter(m.get("attack_type", "") for m in models)
        total = max(len(models), 1)

        # Map attacks to claims
        claim_lookup: Dict[str, Dict[str, Any]] = {}
        for c in claims:
            key = (c.get("classification") or "").lower()
            if key and key not in claim_lookup:
                claim_lookup[key] = c

        seen_types: set = set()
        results: List[Dict[str, Any]] = []
        for m in models:
            atype = m.get("attack_type", "UNKNOWN")
            if atype in seen_types:
                continue
            seen_types.add(atype)

            freq = type_counts.get(atype, 1)
            likelihood = round(min(freq / total, 1.0), 3)

            risk = (m.get("risk_level") or "MEDIUM").upper()
            risk_weight = {"CRITICAL": 1.0, "HIGH": 0.8, "MEDIUM": 0.5, "LOW": 0.2}.get(risk, 0.5)
            score = round(likelihood * 0.4 + risk_weight * 0.6, 3)

            target = self._match_claim(atype, m.get("weakness_exploited", ""), claim_lookup)

            results.append({
                "attack_type": atype,
                "description": m.get("attack_description", ""),
                "likelihood": likelihood,
                "risk_level": risk,
                "score": score,
                "target_claim": target,
                "our_rebuttal": m.get("rebuttal_strategy", ""),
                "authority": m.get("rebuttal_authority", ""),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def _match_claim(
        self,
        attack_type: str,
        weakness: str,
        claim_lookup: Dict[str, Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Best-effort match an attack to a claim."""
        search = (attack_type + " " + weakness).lower()
        best_match: Optional[Dict[str, Any]] = None
        best_score = 0
        for key, claim in claim_lookup.items():
            prop = (claim.get("proposition") or "").lower()
            overlap = len(set(search.split()) & set(prop.split()))
            if overlap > best_score:
                best_score = overlap
                best_match = claim
        return best_match

    # ── Core: generate_rebuttals ────────────────────────────────────

    def generate_rebuttals(
        self, attacks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate IRAC-structured rebuttals for each predicted attack."""
        rebuttals: List[Dict[str, Any]] = []
        for atk in attacks:
            atype = atk.get("attack_type", "")
            authority = self._find_authority(atype, atk.get("authority", ""))
            evidence = self._find_evidence(atype, atk.get("description", ""))

            issue = f"Whether Defendant's {atype.lower().replace('_', ' ')} argument defeats Plaintiff's position."
            rule = authority.get("text", atk.get("authority", "No authority located in DB."))
            rule_cite = authority.get("cite", atk.get("authority", ""))

            application = (
                f"Defendant may argue that {atk.get('description', 'this objection applies')}. "
                f"However, {atk.get('our_rebuttal', 'this argument fails on the merits')}."
            )
            if evidence.get("quote"):
                application += (
                    f" The record confirms: \"{evidence['quote'][:300]}\" "
                    f"(Evidence ID {evidence.get('id', 'N/A')})."
                )

            conclusion = (
                f"Defendant's {atype.lower().replace('_', ' ')} attack lacks merit. "
                f"This Court should reject this argument under {rule_cite}."
            )

            rebuttals.append({
                "attack_type": atype,
                "irac": {
                    "issue": issue,
                    "rule": f"{rule_cite}: {rule[:500]}",
                    "application": application,
                    "conclusion": conclusion,
                },
                "authority_cite": rule_cite,
                "evidence_id": evidence.get("id"),
                "evidence_quote": (evidence.get("quote") or "")[:300],
                "anticipatory_text": (
                    f"Defendant may argue {atk.get('description', '')}. "
                    f"However, {atk.get('our_rebuttal', 'this argument fails')}. "
                    f"See {rule_cite}."
                ),
            })
        return rebuttals

    def _find_authority(self, attack_type: str, fallback_cite: str) -> Dict[str, str]:
        """Search auth_rules for authority supporting our position."""
        keywords = attack_type.lower().replace("_", " ")
        # Try FTS first
        rows = self._query(
            "SELECT rule_number, title, full_text FROM auth_rules "
            "WHERE id IN (SELECT rowid FROM auth_rules_fts WHERE auth_rules_fts MATCH ?) "
            "LIMIT 3",
            (keywords,),
        )
        if not rows:
            # Fallback: LIKE search
            rows = self._query(
                "SELECT rule_number, title, full_text FROM auth_rules "
                "WHERE LOWER(title) LIKE ? OR LOWER(full_text) LIKE ? LIMIT 3",
                (f"%{keywords[:30]}%", f"%{keywords[:30]}%"),
            )
        if rows:
            r = rows[0]
            return {
                "cite": r.get("rule_number", fallback_cite),
                "text": (r.get("full_text") or r.get("title") or "")[:500],
            }
        return {"cite": fallback_cite, "text": ""}

    def _find_evidence(self, attack_type: str, description: str) -> Dict[str, Any]:
        """Search evidence_quotes for evidence contradicting the attack."""
        search_terms = re.sub(r"[^a-z0-9 ]", "", (attack_type + " " + description).lower())
        words = search_terms.split()[:4]
        if not words:
            return {}
        # Try FTS
        fts_query = " OR ".join(words)
        rows = self._query(
            "SELECT id, quote_text, legal_significance FROM evidence_quotes "
            "WHERE id IN (SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?) "
            "LIMIT 3",
            (fts_query,),
        )
        if not rows:
            # Fallback: LIKE on first keyword
            rows = self._query(
                "SELECT id, quote_text, legal_significance FROM evidence_quotes "
                "WHERE LOWER(quote_text) LIKE ? LIMIT 3",
                (f"%{words[0]}%",),
            )
        if rows:
            r = rows[0]
            return {
                "id": r.get("id"),
                "quote": r.get("quote_text", ""),
                "significance": r.get("legal_significance", ""),
            }
        return {}

    # ── Core: vulnerability_scan ────────────────────────────────────

    def vulnerability_scan(self, document_text: str) -> List[Dict[str, Any]]:
        """Scan a draft filing for legal and procedural vulnerabilities.

        Categories:
        - citation_gap: assertions without supporting citations
        - evidence_gap: factual claims without evidence references
        - objection_risk: arguments weak to standard objections
        - procedural_defect: wrong rule cited, deadline issues
        """
        vulns: List[Dict[str, Any]] = []
        paragraphs = self._split_paragraphs(document_text)

        # Citation patterns
        cite_pat = re.compile(
            r"MCR \d+\.\d+|MCL \d+\.\d+|MRE \d+|"
            r"\d+ Mich App \d+|\d+ Mich \d+|\d+ NW2d \d+",
            re.IGNORECASE,
        )
        # Legal assertion indicators
        assertion_pat = re.compile(
            r"\b(must|shall|requires?|mandates?|prohibits?|violat|"
            r"the court (is|was) (required|obligated)|"
            r"under Michigan law|pursuant to)\b",
            re.IGNORECASE,
        )
        # Evidence reference indicators
        evidence_pat = re.compile(
            r"\b(exhibit|transcript|deposition|record|testimony|"
            r"affidavit|declaration|stipulat)\b",
            re.IGNORECASE,
        )
        # Factual assertion indicators
        fact_pat = re.compile(
            r"\b(on or about|approximately|defendant (did|said|failed)|"
            r"plaintiff (was|has been)|the child|"
            r"\d+ days|since \w+ \d{4})\b",
            re.IGNORECASE,
        )

        for i, para in enumerate(paragraphs, 1):
            stripped = para.strip()
            if len(stripped) < 20:
                continue

            has_cite = bool(cite_pat.search(stripped))
            has_assertion = bool(assertion_pat.search(stripped))
            has_evidence_ref = bool(evidence_pat.search(stripped))
            has_fact = bool(fact_pat.search(stripped))

            # Citation gap: legal assertion without citation
            if has_assertion and not has_cite:
                vulns.append({
                    "type": "citation_gap",
                    "severity": "high",
                    "paragraph": i,
                    "text_excerpt": stripped[:150],
                    "issue": "Legal assertion without supporting citation",
                    "fix": "Add MCR/MCL/case law citation supporting this assertion",
                })

            # Evidence gap: factual claim without evidence reference
            if has_fact and not has_evidence_ref and not has_cite:
                vulns.append({
                    "type": "evidence_gap",
                    "severity": "medium",
                    "paragraph": i,
                    "text_excerpt": stripped[:150],
                    "issue": "Factual assertion without evidence reference",
                    "fix": "Reference exhibit, transcript, or affidavit supporting this fact",
                })

        # Check cited rules exist in DB
        all_cites = cite_pat.findall(document_text)
        for cite in set(all_cites):
            cite_clean = cite.strip()
            rows = self._query(
                "SELECT rule_number FROM auth_rules WHERE rule_number LIKE ? LIMIT 1",
                (f"%{cite_clean}%",),
            )
            if not rows and cite_clean.upper().startswith("MCR"):
                vulns.append({
                    "type": "procedural_defect",
                    "severity": "high",
                    "paragraph": 0,
                    "text_excerpt": cite_clean,
                    "issue": f"Cited rule '{cite_clean}' not found in authority database",
                    "fix": "Verify rule number is correct; check auth_rules table",
                })

        # Check for objection-risk patterns
        weak_patterns = [
            (r"\b(clearly|obviously|undeniably)\b", "Rhetorical overstatement invites objection"),
            (r"\b(never|always|every single)\b", "Absolute language vulnerable to counter-example"),
            (r"\b(bad faith|unconscionable|outrageous)\b", "Inflammatory language without legal standard"),
        ]
        for pat_str, issue in weak_patterns:
            pat = re.compile(pat_str, re.IGNORECASE)
            for match in pat.finditer(document_text):
                start = max(0, match.start() - 50)
                end = min(len(document_text), match.end() + 50)
                vulns.append({
                    "type": "objection_risk",
                    "severity": "low",
                    "paragraph": 0,
                    "text_excerpt": document_text[start:end].strip(),
                    "issue": issue,
                    "fix": "Replace with precise legal terminology or remove qualifier",
                })

        # Sort by severity
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        vulns.sort(key=lambda v: sev_order.get(v.get("severity", "low"), 9))
        return vulns

    @staticmethod
    def _split_paragraphs(text: str) -> List[str]:
        """Split document into paragraph-like chunks."""
        # Split on double newlines or numbered paragraphs
        parts = re.split(r"\n\s*\n|\n\s*\d+\.\s+", text)
        return [p.strip() for p in parts if p.strip()]

    # ── Core: build_attack_tree ─────────────────────────────────────

    def build_attack_tree(self, claim: str) -> Dict[str, Any]:
        """Build a three-level attack tree for a legal claim.

        Level 1: Direct attacks on the claim
        Level 2: Attacks on our evidence
        Level 3: Procedural attacks (standing, timeliness, preservation)
        """
        tree: Dict[str, Any] = {
            "claim": claim,
            "generated_at": datetime.now().isoformat(),
            "levels": [],
        }

        # Level 1: direct attacks from adversary_models
        direct = self._query(
            "SELECT attack_type, attack_description, rebuttal_strategy, "
            "rebuttal_authority, risk_level "
            "FROM adversary_models "
            "WHERE LOWER(attack_description) LIKE ? OR LOWER(weakness_exploited) LIKE ?",
            (f"%{claim.lower()[:40]}%", f"%{claim.lower()[:40]}%"),
        )
        if not direct:
            direct = self._query(
                "SELECT attack_type, attack_description, rebuttal_strategy, "
                "rebuttal_authority, risk_level FROM adversary_models LIMIT 10"
            )
        if not direct:
            direct = DEFAULT_ATTACKS

        level1: List[Dict[str, Any]] = []
        for d in direct[:5]:
            level1.append({
                "level": 1,
                "attack_type": d.get("attack_type", "UNKNOWN"),
                "description": d.get("attack_description", ""),
                "our_defense": d.get("rebuttal_strategy", ""),
                "authority": d.get("rebuttal_authority", ""),
                "confidence": self._risk_to_confidence(d.get("risk_level", "MEDIUM")),
            })
        tree["levels"].append({"level": 1, "name": "Direct attacks", "nodes": level1})

        # Level 2: attacks on our evidence
        evidence_rows = self._query(
            "SELECT id, quote_text, evidence_category, legal_significance "
            "FROM evidence_quotes "
            "WHERE LOWER(legal_significance) LIKE ? LIMIT 5",
            (f"%{claim.lower()[:30]}%",),
        )
        level2: List[Dict[str, Any]] = []
        evidence_attacks = [
            ("HEARSAY", "Object to evidence as hearsay", "Establish hearsay exception under MRE 803/804", "MRE 801, 803, 804"),
            ("AUTHENTICATION", "Challenge authenticity of documents", "Authenticate through testimony or self-authentication", "MRE 901, 902"),
            ("RELEVANCE", "Object to relevance of evidence", "Demonstrate logical relevance to best-interest factors", "MRE 401, 402"),
        ]
        for atype, desc, defense, auth in evidence_attacks:
            node: Dict[str, Any] = {
                "level": 2,
                "attack_type": atype,
                "description": desc,
                "our_defense": defense,
                "authority": auth,
                "confidence": 0.6,
            }
            if evidence_rows:
                node["target_evidence_id"] = evidence_rows[0].get("id")
            level2.append(node)
        tree["levels"].append({"level": 2, "name": "Evidence attacks", "nodes": level2})

        # Level 3: procedural attacks
        procedural_attacks = [
            ("STANDING", "Challenge standing to bring claim", "Demonstrate direct stake as parent", "MCL 722.26a; MCR 3.211"),
            ("TIMELINESS", "Argue motion is untimely", "Filed within rule window; equitable tolling applies", "MCR 2.108; MCR 7.204(A)"),
            ("PRESERVATION", "Argue issue not preserved below", "Issue raised at trial-court level; plain error review applies", "MCR 2.517; MRE 103(a)"),
            ("MOOTNESS", "Argue issue is moot", "Capable-of-repetition-yet-evading-review exception applies", "In re Contempt of Dougherty, 429 Mich 81 (1987)"),
        ]
        level3: List[Dict[str, Any]] = []
        for atype, desc, defense, auth in procedural_attacks:
            level3.append({
                "level": 3,
                "attack_type": atype,
                "description": desc,
                "our_defense": defense,
                "authority": auth,
                "confidence": 0.5,
            })
        tree["levels"].append({"level": 3, "name": "Procedural attacks", "nodes": level3})

        return tree

    @staticmethod
    def _risk_to_confidence(risk_level: str) -> float:
        return {
            "CRITICAL": 0.95,
            "HIGH": 0.8,
            "MEDIUM": 0.6,
            "LOW": 0.3,
        }.get((risk_level or "MEDIUM").upper(), 0.5)

    # ── Core: assess_litigation_risk ────────────────────────────────

    def assess_litigation_risk(
        self, lane: Optional[str] = None
    ) -> Dict[str, Any]:
        """Overall risk assessment for a case lane (A-F) or all lanes."""
        result: Dict[str, Any] = {
            "assessed_at": datetime.now().isoformat(),
            "lanes": {},
        }

        lanes_to_check = [lane.upper()] if lane else list(LANE_MAP.keys())

        for ln in lanes_to_check:
            lane_info = LANE_MAP.get(ln, {"name": f"Lane {ln}", "case_no": ""})

            # Load risk events — track may match lane letter or '*' for global
            risks = self._query(
                "SELECT risk_class, severity, title, cure_deadline_clock, "
                "authority_refs_json, cure_packet_json "
                "FROM risk_events WHERE track = ? OR track = '*'",
                (ln,),
            )

            # Load adversary models for this lane's filings
            adv_models = self._query(
                "SELECT attack_type, risk_level, filing_vehicle "
                "FROM adversary_models LIMIT 20"
            )

            # Compute composite score
            if risks:
                severities = [r.get("severity", 50) for r in risks]
                # Numeric severity: use as-is. String: map.
                numeric = []
                for s in severities:
                    if isinstance(s, (int, float)):
                        numeric.append(float(s))
                    else:
                        numeric.append({"critical": 95, "high": 75, "medium": 50, "low": 25}.get(
                            str(s).lower(), 50
                        ))
                composite = round(sum(numeric) / len(numeric), 1)
                max_risk = round(max(numeric), 1)
            else:
                composite = 0.0
                max_risk = 0.0

            # Adversary threat multiplier
            high_attacks = sum(
                1 for a in adv_models
                if (a.get("risk_level") or "").upper() in ("HIGH", "CRITICAL")
            )
            threat_multiplier = min(1.0 + (high_attacks * 0.05), 1.5)
            adjusted_score = round(min(composite * threat_multiplier, 100), 1)

            # Top 3 risks
            sorted_risks = sorted(
                risks,
                key=lambda r: r.get("severity", 0) if isinstance(r.get("severity"), (int, float)) else 50,
                reverse=True,
            )
            top_risks: List[Dict[str, Any]] = []
            for risk in sorted_risks[:3]:
                mitigation = "Review cure packet and address before deadline"
                cure_json = risk.get("cure_packet_json")
                if cure_json:
                    try:
                        cure = json.loads(cure_json) if isinstance(cure_json, str) else cure_json
                        if isinstance(cure, dict):
                            mitigation = cure.get("strategy", mitigation)
                        elif isinstance(cure, list) and cure:
                            mitigation = str(cure[0])
                    except (json.JSONDecodeError, TypeError):
                        pass

                top_risks.append({
                    "title": risk.get("title", "Unknown risk"),
                    "risk_class": risk.get("risk_class", "unknown"),
                    "severity": risk.get("severity", "unknown"),
                    "cure_deadline": risk.get("cure_deadline_clock", "unknown"),
                    "mitigation": mitigation,
                })

            result["lanes"][ln] = {
                "lane_name": lane_info["name"],
                "case_number": lane_info["case_no"],
                "composite_risk_score": adjusted_score,
                "max_single_risk": max_risk,
                "risk_count": len(risks),
                "high_attack_threats": high_attacks,
                "top_risks": top_risks,
                "risk_level": (
                    "CRITICAL" if adjusted_score >= 80 else
                    "HIGH" if adjusted_score >= 60 else
                    "MEDIUM" if adjusted_score >= 40 else
                    "LOW"
                ),
            }

        return result

    # ── Core: generate_anticipatory_section ──────────────────────────

    def generate_anticipatory_section(self, filing_type: str) -> str:
        """Generate an 'Anticipatory Response' section for a court filing.

        Returns formatted text with 3-5 pre-emptive rebuttals.
        """
        attacks = self.predict_attacks(filing_type)
        rebuttals = self.generate_rebuttals(attacks[:5])

        lines: List[str] = []
        lines.append("ANTICIPATORY RESPONSE TO EXPECTED ARGUMENTS")
        lines.append("=" * 50)
        lines.append("")
        lines.append(
            "Plaintiff anticipates that Defendant may raise the following "
            "arguments and responds pre-emptively to each:"
        )
        lines.append("")

        for idx, reb in enumerate(rebuttals[:5], 1):
            irac = reb.get("irac", {})
            lines.append(f"{idx}. {reb.get('attack_type', 'ARGUMENT').replace('_', ' ')}")
            lines.append("-" * 40)
            lines.append("")
            lines.append(f"Issue: {irac.get('issue', '')}")
            lines.append("")
            lines.append(f"Rule: {irac.get('rule', '')}")
            lines.append("")
            lines.append(f"Application: {irac.get('application', '')}")
            lines.append("")
            lines.append(f"Conclusion: {irac.get('conclusion', '')}")
            lines.append("")
            if reb.get("evidence_quote"):
                lines.append(
                    f'Supporting Evidence: "{reb["evidence_quote"][:200]}" '
                    f'(Evidence ID {reb.get("evidence_id", "N/A")})'
                )
                lines.append("")
            lines.append("")

        return "\n".join(lines)

    # ── Core: get_risk_dashboard ────────────────────────────────────

    def get_risk_dashboard(self) -> Dict[str, Any]:
        """Summary dashboard of litigation risks across all lanes."""
        assessment = self.assess_litigation_risk()
        lanes_data = assessment.get("lanes", {})

        # Aggregate
        all_scores = [v.get("composite_risk_score", 0) for v in lanes_data.values()]
        all_risk_counts = [v.get("risk_count", 0) for v in lanes_data.values()]
        critical_lanes = [
            k for k, v in lanes_data.items()
            if v.get("risk_level") in ("CRITICAL", "HIGH")
        ]

        # Collect all top risks across lanes
        all_top_risks: List[Dict[str, Any]] = []
        for ln, data in lanes_data.items():
            for risk in data.get("top_risks", []):
                risk_copy = dict(risk)
                risk_copy["lane"] = ln
                risk_copy["lane_name"] = data.get("lane_name", "")
                all_top_risks.append(risk_copy)

        all_top_risks.sort(
            key=lambda r: r.get("severity", 0) if isinstance(r.get("severity"), (int, float)) else 50,
            reverse=True,
        )

        dashboard: Dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "overall_risk_level": (
                "CRITICAL" if any(s >= 80 for s in all_scores) else
                "HIGH" if any(s >= 60 for s in all_scores) else
                "MEDIUM" if any(s >= 40 for s in all_scores) else
                "LOW"
            ),
            "average_risk_score": round(sum(all_scores) / max(len(all_scores), 1), 1),
            "total_risk_events": sum(all_risk_counts),
            "critical_lanes": critical_lanes,
            "lane_summary": {
                ln: {
                    "name": data.get("lane_name"),
                    "score": data.get("composite_risk_score"),
                    "level": data.get("risk_level"),
                    "top_risk": data["top_risks"][0]["title"] if data.get("top_risks") else "None",
                }
                for ln, data in lanes_data.items()
            },
            "top_5_risks": all_top_risks[:5],
            "days_separated": "329+",
            "urgency_note": (
                "329+ days of parent-child separation. "
                "Every procedural delay compounds constitutional harm."
            ),
        }
        return dashboard


# ── CLI / smoke test ────────────────────────────────────────────────

def _smoke_test() -> None:
    """Quick validation that the engine loads and key methods work."""
    print("=" * 60)
    print("ADVERSARIAL ENGINE — Smoke Test")
    print("=" * 60)

    engine = AdversarialEngine()

    # 1. predict_attacks
    print("\n[1] predict_attacks('motion')...")
    attacks = engine.predict_attacks("motion")
    print(f"    Predicted {len(attacks)} attack(s)")
    if attacks:
        top = attacks[0]
        print(f"    Top attack: {top['attack_type']} (score={top['score']}, risk={top['risk_level']})")

    # 2. generate_rebuttals
    print("\n[2] generate_rebuttals (top 3)...")
    rebuttals = engine.generate_rebuttals(attacks[:3])
    print(f"    Generated {len(rebuttals)} rebuttal(s)")
    if rebuttals:
        print(f"    First rebuttal authority: {rebuttals[0].get('authority_cite', 'N/A')}")

    # 3. vulnerability_scan
    print("\n[3] vulnerability_scan (sample text)...")
    sample = (
        "The Court must grant this motion. Defendant's behavior was clearly outrageous. "
        "On or about January 2024, defendant failed to comply. "
        "MCR 2.116(C)(10) requires summary disposition. "
        "Plaintiff has always been the primary caregiver."
    )
    vulns = engine.vulnerability_scan(sample)
    print(f"    Found {len(vulns)} vulnerability(ies)")
    for v in vulns[:3]:
        print(f"    - [{v['severity']}] {v['type']}: {v['issue']}")

    # 4. build_attack_tree
    print("\n[4] build_attack_tree('custody modification')...")
    tree = engine.build_attack_tree("custody modification")
    for level in tree.get("levels", []):
        print(f"    Level {level['level']} ({level['name']}): {len(level['nodes'])} node(s)")

    # 5. assess_litigation_risk (Lane A)
    print("\n[5] assess_litigation_risk(lane='A')...")
    risk = engine.assess_litigation_risk(lane="A")
    lane_a = risk.get("lanes", {}).get("A", {})
    print(f"    Score: {lane_a.get('composite_risk_score', 'N/A')}, Level: {lane_a.get('risk_level', 'N/A')}")

    # 6. get_risk_dashboard
    print("\n[6] get_risk_dashboard()...")
    dash = engine.get_risk_dashboard()
    print(f"    Overall: {dash.get('overall_risk_level', 'N/A')}, Avg score: {dash.get('average_risk_score', 'N/A')}")
    print(f"    Critical lanes: {dash.get('critical_lanes', [])}")

    # 7. generate_anticipatory_section
    print("\n[7] generate_anticipatory_section('brief')...")
    section = engine.generate_anticipatory_section("brief")
    line_count = len(section.strip().split("\n"))
    print(f"    Generated {line_count} lines of anticipatory text")

    # Error log check
    if engine._error_log:
        print(f"\n[WARN] {len(engine._error_log)} DB error(s) during smoke test:")
        for e in engine._error_log[:3]:
            print(f"    {e['error'][:100]}")

    print("\n" + "=" * 60)
    print("SMOKE TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    _smoke_test()
