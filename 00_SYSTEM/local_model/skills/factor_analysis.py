"""
MCL 722.23 Best-Interest Factor Analyzer
=========================================
LitigationOS Analytical Skill — Factor Analysis for Custody Modification

Analyzes all 12 best-interest factors (a–l) against the litigation database,
mapping evidence, forensic findings, timeline events, and impeachment items
to each factor.  Produces scored assessments and a comprehensive markdown report.

Case: Andrew Pigors (Father/Plaintiff) v. Haley Watson (Mother/Defendant)
"""

from __future__ import annotations

import sqlite3
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ── Constants ────────────────────────────────────────────────────────────────

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
REPORT_PATH = Path(
    r"C:\Users\andre\LitigationOS\06_ANALYSIS\best_interest_factor_analysis.md"
)


class FactorScore(str, Enum):
    STRONGLY_FAVORS_FATHER = "STRONGLY_FAVORS_FATHER"
    FAVORS_FATHER = "FAVORS_FATHER"
    NEUTRAL = "NEUTRAL"
    FAVORS_MOTHER = "FAVORS_MOTHER"
    STRONGLY_FAVORS_MOTHER = "STRONGLY_FAVORS_MOTHER"


# ── Factor Definitions ──────────────────────────────────────────────────────

@dataclass
class FactorDefinition:
    letter: str
    title: str
    mcl_text: str
    keywords: List[str]
    evidence_categories: List[str]       # evidence_quotes.evidence_category
    forensic_categories: List[str]       # forensic_judicial_analysis.category
    timeline_categories: List[str]       # master_timeline.category
    impeachment_types: List[str]         # impeachment_items.item_type


FACTORS: Dict[str, FactorDefinition] = {
    "a": FactorDefinition(
        letter="a",
        title="Love, Affection, and Emotional Ties",
        mcl_text=(
            "The love, affection, and other emotional ties existing between "
            "the parties involved and the child."
        ),
        keywords=[
            "love", "affection", "bond", "attachment", "emotional",
            "relationship", "close", "nurtur", "caring", "warmth",
            "comfort", "parent-child", "miss", "want to see",
        ],
        evidence_categories=["TRANSCRIPT", "CUSTODY_ORDER"],
        forensic_categories=[
            "CHILD_WELFARE_HARM", "ALIENATION_ENABLEMENT",
            "ALIENATION_TACTIC", "BEST_INTEREST_ANALYSIS",
        ],
        timeline_categories=["communication", "incident", "evidence"],
        impeachment_types=["BEST_INTEREST_FACTOR"],
    ),
    "b": FactorDefinition(
        letter="b",
        title="Capacity for Love, Affection, Guidance; Continuation of Education",
        mcl_text=(
            "The capacity and disposition of the parties involved to give the "
            "child love, affection, and guidance and to continue the education "
            "and raising of the child in his or her religion or creed, if any."
        ),
        keywords=[
            "capacity", "guidance", "education", "school", "raising",
            "parenting", "discipline", "structure", "routine", "values",
            "religion", "creed", "teach", "mentor", "support",
        ],
        evidence_categories=["TRANSCRIPT", "CUSTODY_ORDER"],
        forensic_categories=[
            "CHILD_WELFARE_HARM", "BEST_INTEREST_ANALYSIS",
            "CREDIBILITY_FAILURE",
        ],
        timeline_categories=["evidence", "communication"],
        impeachment_types=["BEST_INTEREST_FACTOR"],
    ),
    "c": FactorDefinition(
        letter="c",
        title="Capacity to Provide Food, Clothing, Medical Care",
        mcl_text=(
            "The capacity and disposition of the parties involved to provide "
            "the child with food, clothing, medical care or other remedial "
            "care recognized and permitted under the laws of this state in "
            "place of medical care, and other material needs."
        ),
        keywords=[
            "food", "clothing", "medical", "health care", "insurance",
            "financial", "income", "employment", "housing", "provide",
            "material", "necessit", "doctor", "medication", "shelter",
            "stable home",
        ],
        evidence_categories=["TRANSCRIPT", "CUSTODY_ORDER"],
        forensic_categories=["CHILD_WELFARE_HARM", "BEST_INTEREST_ANALYSIS"],
        timeline_categories=["financial", "evidence"],
        impeachment_types=["BEST_INTEREST_FACTOR"],
    ),
    "d": FactorDefinition(
        letter="d",
        title="Length of Time in Stable, Satisfactory Environment",
        mcl_text=(
            "The length of time the child has lived in a stable, satisfactory "
            "environment, and the desirability of maintaining continuity."
        ),
        keywords=[
            "stable", "environment", "continuity", "established custodial",
            "custodial environment", "ECE", "length of time", "lived with",
            "residence", "settled", "disruption", "separation", "uprooted",
            "329 days", "parent-child separation",
        ],
        evidence_categories=["TRANSCRIPT", "CUSTODY_ORDER"],
        forensic_categories=[
            "CHILD_WELFARE_HARM", "BEST_INTEREST_ANALYSIS",
            "ALIENATION_ENABLEMENT",
        ],
        timeline_categories=["order", "incident", "evidence"],
        impeachment_types=["ECE_REFERENCE", "BEST_INTEREST_FACTOR"],
    ),
    "e": FactorDefinition(
        letter="e",
        title="Permanence as Family Unit",
        mcl_text=(
            "The permanence, as a family unit, of the existing or proposed "
            "custodial home or homes."
        ),
        keywords=[
            "permanence", "family unit", "custodial home", "stability",
            "household", "consistent", "family structure", "cohabit",
            "step-parent", "partner", "move", "relocation",
        ],
        evidence_categories=["TRANSCRIPT", "CUSTODY_ORDER"],
        forensic_categories=["BEST_INTEREST_ANALYSIS", "CHILD_WELFARE_HARM"],
        timeline_categories=["evidence", "general"],
        impeachment_types=["BEST_INTEREST_FACTOR"],
    ),
    "f": FactorDefinition(
        letter="f",
        title="Moral Fitness of the Parties",
        mcl_text="The moral fitness of the parties involved.",
        keywords=[
            "moral", "fitness", "character", "credibility", "honesty",
            "integrity", "false", "lie", "deceiv", "manipulat", "fraud",
            "perjur", "misconduct", "drug", "alcohol", "substance",
            "criminal", "arrest", "conviction", "truthful",
        ],
        evidence_categories=["TRANSCRIPT", "CUSTODY_ORDER", "PPO"],
        forensic_categories=[
            "CREDIBILITY_FAILURE", "FALSE_ALLEGATIONS",
            "PPO_WEAPONIZATION", "BEST_INTEREST_ANALYSIS",
        ],
        timeline_categories=["violation", "incident", "evidence"],
        impeachment_types=[
            "EX_PARTE_COMMUNICATION", "BEST_INTEREST_FACTOR",
            "ABSOLUTE_LANGUAGE",
        ],
    ),
    "g": FactorDefinition(
        letter="g",
        title="Mental and Physical Health of the Parties",
        mcl_text="The mental and physical health of the parties involved.",
        keywords=[
            "mental health", "physical health", "assessment", "evaluation",
            "psychological", "therapy", "counseling", "diagnos",
            "medication", "disability", "fitness", "wellness", "treatment",
            "substance abuse", "depression", "anxiety",
        ],
        evidence_categories=["TRANSCRIPT", "CUSTODY_ORDER"],
        forensic_categories=[
            "BEST_INTEREST_ANALYSIS", "CHILD_WELFARE_HARM",
            "CREDIBILITY_FAILURE",
        ],
        timeline_categories=["evidence", "order"],
        impeachment_types=["BEST_INTEREST_FACTOR", "NO_HEARING"],
    ),
    "h": FactorDefinition(
        letter="h",
        title="Home, School, and Community Record",
        mcl_text=(
            "The home, school, and community record of the child."
        ),
        keywords=[
            "school", "community", "home record", "grades", "attendance",
            "teacher", "friends", "activities", "sports", "church",
            "neighbors", "daycare", "extracurricular",
        ],
        evidence_categories=["TRANSCRIPT", "CUSTODY_ORDER"],
        forensic_categories=["BEST_INTEREST_ANALYSIS", "CHILD_WELFARE_HARM"],
        timeline_categories=["evidence", "communication"],
        impeachment_types=["BEST_INTEREST_FACTOR"],
    ),
    "i": FactorDefinition(
        letter="i",
        title="Reasonable Preference of the Child",
        mcl_text=(
            "The reasonable preference of the child, if the court considers "
            "the child to be of sufficient age to express preference."
        ),
        keywords=[
            "preference", "child's wish", "wants to live", "choose",
            "express", "old enough", "sufficient age", "child said",
            "child told", "child wants",
        ],
        evidence_categories=["TRANSCRIPT", "CUSTODY_ORDER"],
        forensic_categories=["BEST_INTEREST_ANALYSIS", "CHILD_WELFARE_HARM"],
        timeline_categories=["communication", "evidence"],
        impeachment_types=["BEST_INTEREST_FACTOR"],
    ),
    "j": FactorDefinition(
        letter="j",
        title="Willingness to Facilitate Close Relationship with Other Parent",
        mcl_text=(
            "The willingness and ability of each of the parties to facilitate "
            "and encourage a close and continuing parent-child relationship "
            "between the child and the other parent or the child and the parents."
        ),
        keywords=[
            "facilitate", "encourage", "relationship", "alienat",
            "interfere", "obstruct", "deny", "withhold", "parenting time",
            "visitation", "contact", "phone", "communication",
            "co-parent", "cooperation", "gatekeep", "undermine",
            "close and continuing", "parent-child relationship",
            "separation", "denial", "refused", "blocked",
        ],
        evidence_categories=["TRANSCRIPT", "CUSTODY_ORDER", "EX_PARTE_ORDER", "PPO"],
        forensic_categories=[
            "ALIENATION_ENABLEMENT", "ALIENATION_TACTIC",
            "PARENTING_TIME_DENIAL", "PPO_WEAPONIZATION",
            "CHILD_WELFARE_HARM", "BEST_INTEREST_ANALYSIS",
            "FALSE_ALLEGATIONS",
        ],
        timeline_categories=[
            "order", "violation", "incident", "communication", "evidence",
        ],
        impeachment_types=[
            "EX_PARTE_COMMUNICATION", "NO_HEARING",
            "DENIAL_WITHOUT_HEARING", "BEST_INTEREST_FACTOR",
        ],
    ),
    "k": FactorDefinition(
        letter="k",
        title="Domestic Violence",
        mcl_text=(
            "Domestic violence, regardless of whether the violence was "
            "directed against or witnessed by the child."
        ),
        keywords=[
            "domestic violence", "abuse", "assault", "PPO", "protection order",
            "threat", "physical harm", "violence", "battery", "restrain",
            "stalking", "harass", "fear", "coercive control",
            "false allegation", "weaponiz",
        ],
        evidence_categories=["PPO", "TRANSCRIPT", "EX_PARTE_ORDER"],
        forensic_categories=[
            "PPO_WEAPONIZATION", "FALSE_ALLEGATIONS",
            "HARM_VIOLATION", "BEST_INTEREST_ANALYSIS",
        ],
        timeline_categories=["violation", "incident", "order"],
        impeachment_types=[
            "EX_PARTE_COMMUNICATION", "ABSOLUTE_LANGUAGE",
            "BEST_INTEREST_FACTOR",
        ],
    ),
    "l": FactorDefinition(
        letter="l",
        title="Any Other Relevant Factor",
        mcl_text="Any other factor considered by the court to be relevant.",
        keywords=[
            "judicial bias", "due process", "ex parte", "procedural",
            "FOC", "friend of the court", "disqualification",
            "recusal", "constitutional", "equal protection",
            "contempt", "sanctions", "access to justice",
            "329 days", "separation",
        ],
        evidence_categories=[
            "TRANSCRIPT", "CUSTODY_ORDER", "JUDGE_ORDER",
            "EX_PARTE_ORDER", "PPO",
        ],
        forensic_categories=[
            "BENCHBOOK_DEVIATION", "PROCEDURAL_MISCONDUCT",
            "EX_PARTE_VIOLATION", "DUE_PROCESS_VIOLATION",
            "BIAS_INDICATOR", "CONSTITUTIONAL_VIOLATION",
            "MCR_2003_DISQUALIFICATION", "MCJC_CANON_VIOLATION",
            "ACCESS_TO_JUSTICE", "JUDICIAL_ACTION",
        ],
        timeline_categories=[
            "order", "filing", "hearing", "violation", "evidence",
        ],
        impeachment_types=[
            "EX_PARTE_COMMUNICATION", "NO_HEARING",
            "DENIAL_WITHOUT_HEARING", "ABSOLUTE_LANGUAGE",
        ],
    ),
}


# ── Data Containers ─────────────────────────────────────────────────────────

@dataclass
class EvidenceItem:
    source_table: str
    record_id: str
    text: str
    category: str
    severity: Optional[str] = None
    speaker: Optional[str] = None
    date_iso: Optional[str] = None
    direction: str = "supports_father"  # supports_father | supports_mother | neutral


@dataclass
class FactorAnalysis:
    letter: str
    title: str
    mcl_text: str
    score: FactorScore = FactorScore.NEUTRAL
    evidence_for_father: List[EvidenceItem] = field(default_factory=list)
    evidence_for_mother: List[EvidenceItem] = field(default_factory=list)
    evidence_neutral: List[EvidenceItem] = field(default_factory=list)
    narrative: str = ""
    recommended_exhibits: List[str] = field(default_factory=list)
    strength_notes: str = ""
    weakness_notes: str = ""


# ── Analyzer ─────────────────────────────────────────────────────────────────

class BestInterestAnalyzer:
    """MCL 722.23 Best-Interest Factor Analyzer for custody modification."""

    FATHER_NAME = "Andrew Pigors"
    MOTHER_NAME = "Haley Watson"

    # Keywords that tend to indicate evidence favoring father
    FATHER_INDICATORS = [
        "plaintiff", "pigors", "father", "dad", "andrew",
        "denied parenting", "separation", "alienat",
        "false alleg", "weaponiz", "ex parte", "without hearing",
        "bias", "due process", "unconstitutional",
        "no evidence of harm", "no danger", "fit parent",
    ]

    # Keywords that tend to indicate evidence favoring mother
    MOTHER_INDICATORS = [
        "defendant", "watson", "mother", "mom", "haley",
        "primary caregiver", "primary custodial",
        "child's safety", "concern for child",
        "court ordered", "court found",
    ]

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self.results: Dict[str, FactorAnalysis] = {}

    def close(self):
        self.conn.close()

    # ── Internal query helpers ───────────────────────────────────────────

    def _keyword_clause(self, column: str, keywords: List[str]) -> str:
        """Build a SQL WHERE clause matching any keyword (case-insensitive)."""
        conditions = [f"{column} LIKE '%' || ? || '%'" for _ in keywords]
        return " OR ".join(conditions)

    def _search_evidence_quotes(
        self, fdef: FactorDefinition
    ) -> List[EvidenceItem]:
        """Search evidence_quotes for items relevant to this factor."""
        kw = fdef.keywords
        if not kw:
            return []
        where = self._keyword_clause("quote_text", kw)
        cat_placeholders = ",".join("?" for _ in fdef.evidence_categories)
        sql = f"""
            SELECT id, evidence_category, quote_text, speaker, date_ref,
                   legal_significance
            FROM evidence_quotes
            WHERE ({where})
        """
        params: list = list(kw)
        if fdef.evidence_categories:
            sql += f" OR evidence_category IN ({cat_placeholders})"
            params.extend(fdef.evidence_categories)
        sql += " LIMIT 100"
        rows = self.conn.execute(sql, params).fetchall()
        items = []
        for r in rows:
            text = (r["quote_text"] or "")[:500]
            item = EvidenceItem(
                source_table="evidence_quotes",
                record_id=str(r["id"]),
                text=text,
                category=r["evidence_category"] or "",
                speaker=r["speaker"],
                date_iso=r["date_ref"],
            )
            item.direction = self._classify_direction(text)
            items.append(item)
        return items

    def _search_forensic(self, fdef: FactorDefinition) -> List[EvidenceItem]:
        """Search forensic_judicial_analysis for relevant findings."""
        items = []
        # By category
        if fdef.forensic_categories:
            placeholders = ",".join("?" for _ in fdef.forensic_categories)
            sql = f"""
                SELECT finding_id, category, severity, description,
                       evidence_citations, date_iso
                FROM forensic_judicial_analysis
                WHERE category IN ({placeholders})
                LIMIT 80
            """
            rows = self.conn.execute(sql, fdef.forensic_categories).fetchall()
            for r in rows:
                text = (r["description"] or "")[:500]
                item = EvidenceItem(
                    source_table="forensic_judicial_analysis",
                    record_id=r["finding_id"],
                    text=text,
                    category=r["category"],
                    severity=r["severity"],
                    date_iso=r["date_iso"],
                )
                item.direction = self._classify_direction(text)
                items.append(item)
        # By keyword in description
        kw = fdef.keywords[:8]  # limit for performance
        if kw:
            where = self._keyword_clause("description", kw)
            sql = f"""
                SELECT finding_id, category, severity, description, date_iso
                FROM forensic_judicial_analysis
                WHERE {where}
                LIMIT 50
            """
            rows = self.conn.execute(sql, kw).fetchall()
            seen = {i.record_id for i in items}
            for r in rows:
                if r["finding_id"] in seen:
                    continue
                text = (r["description"] or "")[:500]
                item = EvidenceItem(
                    source_table="forensic_judicial_analysis",
                    record_id=r["finding_id"],
                    text=text,
                    category=r["category"],
                    severity=r["severity"],
                    date_iso=r["date_iso"],
                )
                item.direction = self._classify_direction(text)
                items.append(item)
        return items

    def _search_timeline(self, fdef: FactorDefinition) -> List[EvidenceItem]:
        """Search master_timeline for relevant events."""
        items = []
        kw = fdef.keywords[:8]
        if kw:
            where = self._keyword_clause("description", kw)
            sql = f"""
                SELECT event_id, date_iso, description, category, severity
                FROM master_timeline
                WHERE {where}
                LIMIT 50
            """
            rows = self.conn.execute(sql, kw).fetchall()
            for r in rows:
                text = (r["description"] or "")[:500]
                item = EvidenceItem(
                    source_table="master_timeline",
                    record_id=r["event_id"],
                    text=text,
                    category=r["category"] or "",
                    severity=r["severity"],
                    date_iso=r["date_iso"],
                )
                item.direction = self._classify_direction(text)
                items.append(item)
        if fdef.timeline_categories:
            placeholders = ",".join("?" for _ in fdef.timeline_categories)
            where_kw = self._keyword_clause("description", fdef.keywords[:5])
            sql = f"""
                SELECT event_id, date_iso, description, category, severity
                FROM master_timeline
                WHERE category IN ({placeholders})
                  AND ({where_kw})
                LIMIT 30
            """
            params = list(fdef.timeline_categories) + fdef.keywords[:5]
            rows = self.conn.execute(sql, params).fetchall()
            seen = {i.record_id for i in items}
            for r in rows:
                if r["event_id"] in seen:
                    continue
                text = (r["description"] or "")[:500]
                item = EvidenceItem(
                    source_table="master_timeline",
                    record_id=r["event_id"],
                    text=text,
                    category=r["category"] or "",
                    severity=r["severity"],
                    date_iso=r["date_iso"],
                )
                item.direction = self._classify_direction(text)
                items.append(item)
        return items

    def _search_impeachment(
        self, fdef: FactorDefinition
    ) -> List[EvidenceItem]:
        """Search impeachment_items for relevant items."""
        items = []
        if fdef.impeachment_types:
            placeholders = ",".join("?" for _ in fdef.impeachment_types)
            sql = f"""
                SELECT id, item_type, speaker, statement, severity,
                       contradicting_text, legal_hook
                FROM impeachment_items
                WHERE item_type IN ({placeholders})
                LIMIT 40
            """
            rows = self.conn.execute(
                sql, fdef.impeachment_types
            ).fetchall()
            for r in rows:
                text = (r["statement"] or "")[:500]
                item = EvidenceItem(
                    source_table="impeachment_items",
                    record_id=str(r["id"]),
                    text=text,
                    category=r["item_type"],
                    severity=r["severity"],
                    speaker=r["speaker"],
                )
                item.direction = self._classify_direction(text)
                items.append(item)
        return items

    def _search_watson_docs(
        self, fdef: FactorDefinition
    ) -> List[EvidenceItem]:
        """Search watsons_evidence_docs content for relevant material."""
        kw = fdef.keywords[:6]
        if not kw:
            return []
        where = self._keyword_clause("content", kw)
        sql = f"""
            SELECT id, filename, substr(content, 1, 600) as snippet
            FROM watsons_evidence_docs
            WHERE {where}
            LIMIT 20
        """
        rows = self.conn.execute(sql, kw).fetchall()
        items = []
        for r in rows:
            text = (r["snippet"] or "")[:500]
            item = EvidenceItem(
                source_table="watsons_evidence_docs",
                record_id=str(r["id"]),
                text=text,
                category="DOCUMENT",
            )
            item.direction = self._classify_direction(text)
            items.append(item)
        return items

    def _classify_direction(self, text: str) -> str:
        """Heuristic: classify whether text supports father, mother, or neutral."""
        if not text:
            return "neutral"
        lower = text.lower()
        father_score = 0
        mother_score = 0
        for kw in self.FATHER_INDICATORS:
            if kw in lower:
                father_score += 1
        for kw in self.MOTHER_INDICATORS:
            if kw in lower:
                mother_score += 1
        # Specific high-signal patterns
        alienation_signals = [
            "alienat", "denied parenting", "separation",
            "weaponiz", "false alleg", "ex parte",
            "without hearing", "no evidence of harm",
        ]
        for sig in alienation_signals:
            if sig in lower:
                father_score += 2
        obstruction_signals = [
            "refused contact", "blocked", "withheld", "obstruct",
            "interfere", "gatekeep", "denied access",
        ]
        for sig in obstruction_signals:
            if sig in lower:
                father_score += 2
        if father_score > mother_score + 1:
            return "supports_father"
        elif mother_score > father_score + 1:
            return "supports_mother"
        else:
            return "neutral"

    def _score_factor(self, analysis: FactorAnalysis) -> FactorScore:
        """Score a factor based on evidence counts and severity."""
        f_count = len(analysis.evidence_for_father)
        m_count = len(analysis.evidence_for_mother)

        # Weight by severity
        f_weight = 0
        for e in analysis.evidence_for_father:
            sev = (e.severity or "").lower()
            if sev == "critical":
                f_weight += 4
            elif sev == "high":
                f_weight += 3
            elif sev == "medium":
                f_weight += 2
            else:
                f_weight += 1

        m_weight = 0
        for e in analysis.evidence_for_mother:
            sev = (e.severity or "").lower()
            if sev == "critical":
                m_weight += 4
            elif sev == "high":
                m_weight += 3
            elif sev == "medium":
                m_weight += 2
            else:
                m_weight += 1

        ratio = f_weight / max(m_weight, 1)
        if ratio >= 4.0 or (f_count >= 10 and m_count <= 2):
            return FactorScore.STRONGLY_FAVORS_FATHER
        elif ratio >= 2.0 or (f_count >= 5 and m_count <= 3):
            return FactorScore.FAVORS_FATHER
        elif ratio <= 0.25:
            return FactorScore.STRONGLY_FAVORS_MOTHER
        elif ratio <= 0.5:
            return FactorScore.FAVORS_MOTHER
        else:
            return FactorScore.NEUTRAL

    def _generate_narrative(self, analysis: FactorAnalysis) -> str:
        """Generate a narrative summary for a factor analysis."""
        fdef = FACTORS[analysis.letter]
        lines = []
        f_count = len(analysis.evidence_for_father)
        m_count = len(analysis.evidence_for_mother)
        n_count = len(analysis.evidence_neutral)
        total = f_count + m_count + n_count

        lines.append(
            f"**Evidence Volume:** {total} items identified "
            f"({f_count} favoring Father, {m_count} favoring Mother, "
            f"{n_count} neutral)."
        )

        # Highlight critical/high severity items
        critical_items = [
            e for e in analysis.evidence_for_father
            if (e.severity or "").lower() in ("critical", "high")
        ]
        if critical_items:
            lines.append(
                f"\n**Critical/High-Severity Evidence (Father):** "
                f"{len(critical_items)} items, primarily from "
                f"{', '.join(set(e.source_table for e in critical_items[:5]))}."
            )

        # Factor-specific commentary
        commentary = self._factor_commentary(analysis)
        if commentary:
            lines.append(f"\n{commentary}")

        return "\n".join(lines)

    def _factor_commentary(self, analysis: FactorAnalysis) -> str:
        """Generate factor-specific legal commentary."""
        letter = analysis.letter
        f_items = analysis.evidence_for_father

        if letter == "a":
            sep_items = [
                e for e in f_items
                if "separation" in (e.text or "").lower()
                or "denied" in (e.text or "").lower()
            ]
            if sep_items:
                return (
                    "The 329+ day parent-child separation is directly relevant. "
                    "Forced separation damages emotional ties — the very thing "
                    "Factor (a) protects. Evidence shows Father sought to "
                    "maintain the relationship but was blocked by procedural "
                    "barriers and Mother's actions."
                )
        elif letter == "d":
            return (
                "The established custodial environment was disrupted by "
                "the ex parte suspension of Father's parenting time. "
                "The child's stability has been compromised by the "
                "329+ day separation — a judicially imposed disruption, "
                "not a voluntary abandonment."
            )
        elif letter == "f":
            false_allege = [
                e for e in f_items
                if "false" in (e.text or "").lower()
                or "weaponiz" in (e.text or "").lower()
                or "credibility" in (e.category or "").lower()
            ]
            if false_allege:
                return (
                    f"{len(false_allege)} items relate to false allegations "
                    "and/or PPO weaponization. Moral fitness analysis must "
                    "account for the filing of misleading or unsupported "
                    "claims used to obtain ex parte orders."
                )
        elif letter == "j":
            return (
                "**Factor (j) is often the single most decisive factor.** "
                "Michigan courts have repeatedly held that a parent who "
                "actively undermines the child's relationship with the "
                "other parent fails this factor. Evidence of parental "
                "alienation, parenting-time denial, PPO weaponization, "
                "and obstruction of contact is directly relevant. "
                "The 329+ day separation, combined with forensic evidence "
                "of alienation enablement and tactics, strongly implicates "
                "Mother's failure on Factor (j)."
            )
        elif letter == "k":
            return (
                "No credible evidence of domestic violence by Father exists "
                "in the record. However, evidence of PPO weaponization "
                "(using protection orders as tactical custody tools) is "
                "extensive. Courts must distinguish genuine DV from "
                "strategic litigation abuse. See Shady Oaks evidence."
            )
        elif letter == "l":
            return (
                "Factor (l) captures judicial bias, due process violations, "
                "FOC failures, ex parte procedural abuse, and "
                "constitutional violations — all of which are extensively "
                "documented in the forensic record. These systemic issues "
                "are not just procedural defects; they are substantive "
                "factors affecting the child's best interest."
            )
        return ""

    def _recommend_exhibits(self, analysis: FactorAnalysis) -> List[str]:
        """Recommend exhibits for a factor based on evidence found."""
        exhibits = []
        sources = set()
        for e in analysis.evidence_for_father[:20]:
            if e.source_table == "evidence_quotes":
                sources.add(f"Transcript/Document (evidence_quote #{e.record_id})")
            elif e.source_table == "forensic_judicial_analysis":
                sources.add(f"Forensic Finding {e.record_id} ({e.category})")
            elif e.source_table == "impeachment_items":
                sources.add(f"Impeachment Item #{e.record_id} ({e.category})")
            elif e.source_table == "master_timeline":
                sources.add(f"Timeline Event {e.record_id}")
            elif e.source_table == "watsons_evidence_docs":
                sources.add(f"Watson Document #{e.record_id}")
        exhibits = sorted(sources)[:10]
        return exhibits

    # ── Public API ───────────────────────────────────────────────────────

    def find_evidence_for_factor(self, letter: str) -> List[EvidenceItem]:
        """Return all evidence mapped to a specific factor."""
        letter = letter.lower()
        if letter not in FACTORS:
            raise ValueError(f"Invalid factor letter: {letter}. Must be a-l.")
        fdef = FACTORS[letter]
        all_evidence: List[EvidenceItem] = []
        all_evidence.extend(self._search_evidence_quotes(fdef))
        all_evidence.extend(self._search_forensic(fdef))
        all_evidence.extend(self._search_timeline(fdef))
        all_evidence.extend(self._search_impeachment(fdef))
        all_evidence.extend(self._search_watson_docs(fdef))
        return all_evidence

    def analyze_factor(self, letter: str) -> FactorAnalysis:
        """Deep-dive analysis on a single MCL 722.23 factor."""
        letter = letter.lower()
        fdef = FACTORS[letter]
        all_evidence = self.find_evidence_for_factor(letter)

        analysis = FactorAnalysis(
            letter=letter,
            title=fdef.title,
            mcl_text=fdef.mcl_text,
        )

        for e in all_evidence:
            if e.direction == "supports_father":
                analysis.evidence_for_father.append(e)
            elif e.direction == "supports_mother":
                analysis.evidence_for_mother.append(e)
            else:
                analysis.evidence_neutral.append(e)

        analysis.score = self._score_factor(analysis)
        analysis.narrative = self._generate_narrative(analysis)
        analysis.recommended_exhibits = self._recommend_exhibits(analysis)

        # Strength / weakness notes
        if len(analysis.evidence_for_father) > 10:
            analysis.strength_notes = (
                f"Strong evidentiary support with {len(analysis.evidence_for_father)} "
                f"items favoring Father."
            )
        else:
            analysis.weakness_notes = (
                f"Only {len(analysis.evidence_for_father)} evidence items found — "
                f"consider supplementing with additional discovery, affidavits, "
                f"or third-party records."
            )

        return analysis

    def analyze_all_factors(self) -> Dict[str, FactorAnalysis]:
        """Analyze all 12 MCL 722.23 best-interest factors."""
        self.results = {}
        for letter in "abcdefghijkl":
            print(f"  Analyzing Factor ({letter})...", flush=True)
            self.results[letter] = self.analyze_factor(letter)
        return self.results

    def generate_report(self, output_path: Path = REPORT_PATH) -> str:
        """Generate a comprehensive MCL 722.23 analysis report in markdown."""
        if not self.results:
            self.analyze_all_factors()

        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines: List[str] = []

        # ── Header ───────────────────────────────────────────────────
        lines.append("# MCL 722.23 Best-Interest Factor Analysis")
        lines.append(f"**Generated:** {now}")
        lines.append(f"**Case:** Pigors v. Watson — Custody Modification")
        lines.append(f"**Analyst:** LitigationOS BestInterestAnalyzer v1.0")
        lines.append(f"**Database:** `{self.db_path}`")
        lines.append("")
        lines.append("---")
        lines.append("")

        # ── Executive Summary ────────────────────────────────────────
        lines.append("## Executive Summary")
        lines.append("")

        tally: Dict[str, int] = {s.value: 0 for s in FactorScore}
        for a in self.results.values():
            tally[a.score.value] += 1

        lines.append("### Factor Score Tally")
        lines.append("")
        lines.append("| Score | Count | Factors |")
        lines.append("|-------|-------|---------|")
        for score_val, count in tally.items():
            if count > 0:
                factor_letters = [
                    f"({a.letter})" for a in self.results.values()
                    if a.score.value == score_val
                ]
                lines.append(
                    f"| {score_val.replace('_', ' ')} | {count} | "
                    f"{', '.join(factor_letters)} |"
                )
        lines.append("")

        total_father = tally.get("STRONGLY_FAVORS_FATHER", 0) + tally.get(
            "FAVORS_FATHER", 0
        )
        total_mother = tally.get("STRONGLY_FAVORS_MOTHER", 0) + tally.get(
            "FAVORS_MOTHER", 0
        )
        total_neutral = tally.get("NEUTRAL", 0)

        lines.append(
            f"**Overall:** {total_father} factors favor Father, "
            f"{total_mother} favor Mother, {total_neutral} neutral."
        )
        lines.append("")

        if total_father > total_mother:
            lines.append(
                "> **Assessment:** The weight of evidence under MCL 722.23 "
                "supports modification of custody in favor of Father. "
                "The combination of alienation evidence (Factor j), "
                "moral fitness concerns (Factor f), procedural abuse "
                "(Factor l), and the 329+ day parent-child separation "
                "creates a compelling case for change."
            )
        lines.append("")
        lines.append("---")
        lines.append("")

        # ── Factor-by-Factor Breakdown ───────────────────────────────
        lines.append("## Factor-by-Factor Analysis")
        lines.append("")

        for letter in "abcdefghijkl":
            a = self.results[letter]
            score_display = a.score.value.replace("_", " ")
            score_emoji = {
                "STRONGLY_FAVORS_FATHER": "🟢🟢",
                "FAVORS_FATHER": "🟢",
                "NEUTRAL": "⚪",
                "FAVORS_MOTHER": "🔴",
                "STRONGLY_FAVORS_MOTHER": "🔴🔴",
            }.get(a.score.value, "⚪")

            lines.append(f"### Factor ({letter}): {a.title}")
            lines.append("")
            lines.append(f"> *MCL 722.23({letter}):* {a.mcl_text}")
            lines.append("")
            lines.append(
                f"**Score:** {score_emoji} **{score_display}**"
            )
            lines.append("")

            # Narrative
            if a.narrative:
                lines.append(a.narrative)
                lines.append("")

            # Evidence For Father
            if a.evidence_for_father:
                lines.append(
                    f"<details><summary>Evidence Favoring Father "
                    f"({len(a.evidence_for_father)} items)</summary>"
                )
                lines.append("")
                for i, e in enumerate(a.evidence_for_father[:15], 1):
                    snippet = (e.text or "").replace("\n", " ").strip()[:200]
                    sev_tag = f" [{e.severity}]" if e.severity else ""
                    lines.append(
                        f"{i}. **[{e.source_table}#{e.record_id}]**{sev_tag} "
                        f"— {snippet}..."
                    )
                if len(a.evidence_for_father) > 15:
                    lines.append(
                        f"\n*...and {len(a.evidence_for_father) - 15} more items.*"
                    )
                lines.append("")
                lines.append("</details>")
                lines.append("")

            # Evidence For Mother
            if a.evidence_for_mother:
                lines.append(
                    f"<details><summary>Evidence Favoring Mother "
                    f"({len(a.evidence_for_mother)} items)</summary>"
                )
                lines.append("")
                for i, e in enumerate(a.evidence_for_mother[:10], 1):
                    snippet = (e.text or "").replace("\n", " ").strip()[:200]
                    lines.append(
                        f"{i}. **[{e.source_table}#{e.record_id}]** — {snippet}..."
                    )
                lines.append("")
                lines.append("</details>")
                lines.append("")

            # Recommended Exhibits
            if a.recommended_exhibits:
                lines.append("**Recommended Exhibits:**")
                for ex in a.recommended_exhibits[:8]:
                    lines.append(f"- {ex}")
                lines.append("")

            # Strength / Weakness
            if a.strength_notes:
                lines.append(f"✅ **Strength:** {a.strength_notes}")
                lines.append("")
            if a.weakness_notes:
                lines.append(f"⚠️ **Weakness:** {a.weakness_notes}")
                lines.append("")

            lines.append("---")
            lines.append("")

        # ── Strategic Analysis ───────────────────────────────────────
        lines.append("## Strategic Analysis")
        lines.append("")

        # Strongest arguments
        lines.append("### Strongest Arguments for Modification")
        lines.append("")
        strong_factors = [
            a for a in self.results.values()
            if a.score in (
                FactorScore.STRONGLY_FAVORS_FATHER,
                FactorScore.FAVORS_FATHER,
            )
        ]
        strong_factors.sort(
            key=lambda a: len(a.evidence_for_father), reverse=True
        )
        for a in strong_factors:
            lines.append(
                f"- **Factor ({a.letter}) — {a.title}:** "
                f"{len(a.evidence_for_father)} supporting items, "
                f"score = {a.score.value.replace('_', ' ')}"
            )
        lines.append("")

        # Weakest areas
        lines.append("### Areas Needing More Evidence")
        lines.append("")
        weak_factors = [
            a for a in self.results.values()
            if a.score in (FactorScore.NEUTRAL,)
            or len(a.evidence_for_father) < 5
        ]
        for a in weak_factors:
            lines.append(
                f"- **Factor ({a.letter}) — {a.title}:** "
                f"Only {len(a.evidence_for_father)} items. "
                f"{a.weakness_notes or 'Supplement with additional evidence.'}"
            )
        lines.append("")

        # ── Key Exhibits Matrix ──────────────────────────────────────
        lines.append("### Master Exhibit Recommendation Matrix")
        lines.append("")
        lines.append("| Factor | Top Exhibits |")
        lines.append("|--------|-------------|")
        for letter in "abcdefghijkl":
            a = self.results[letter]
            top = ", ".join(a.recommended_exhibits[:3]) or "None identified"
            lines.append(f"| ({letter}) {a.title[:40]} | {top} |")
        lines.append("")

        # ── Statistical Summary ──────────────────────────────────────
        lines.append("## Evidence Statistics")
        lines.append("")
        total_items = 0
        total_father_items = 0
        total_mother_items = 0
        total_neutral_items = 0
        for a in self.results.values():
            total_father_items += len(a.evidence_for_father)
            total_mother_items += len(a.evidence_for_mother)
            total_neutral_items += len(a.evidence_neutral)
        total_items = total_father_items + total_mother_items + total_neutral_items

        lines.append(f"- **Total evidence items analyzed:** {total_items}")
        lines.append(
            f"- **Items favoring Father:** {total_father_items} "
            f"({total_father_items * 100 // max(total_items, 1)}%)"
        )
        lines.append(
            f"- **Items favoring Mother:** {total_mother_items} "
            f"({total_mother_items * 100 // max(total_items, 1)}%)"
        )
        lines.append(
            f"- **Neutral items:** {total_neutral_items} "
            f"({total_neutral_items * 100 // max(total_items, 1)}%)"
        )
        lines.append("")

        lines.append("| Source Table | Count |")
        lines.append("|-------------|-------|")
        source_counts: Dict[str, int] = {}
        for a in self.results.values():
            for e in (
                a.evidence_for_father
                + a.evidence_for_mother
                + a.evidence_neutral
            ):
                source_counts[e.source_table] = (
                    source_counts.get(e.source_table, 0) + 1
                )
        for src, cnt in sorted(
            source_counts.items(), key=lambda x: -x[1]
        ):
            lines.append(f"| {src} | {cnt} |")
        lines.append("")

        # ── Footer ───────────────────────────────────────────────────
        lines.append("---")
        lines.append("")
        lines.append(
            "*This analysis was generated by the LitigationOS "
            "BestInterestAnalyzer. All evidence references correspond "
            "to records in `litigation_context.db`. Verify all citations "
            "against source documents before filing.*"
        )
        lines.append("")
        lines.append(
            "*MCL 722.23 requires the court to consider, evaluate, and "
            "determine each factor. No single factor is dispositive, but "
            "Factor (j) — willingness to facilitate — is frequently the "
            "most heavily weighted in Michigan custody jurisprudence.*"
        )

        report = "\n".join(lines)

        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"\nReport written to: {output_path}")

        return report


# ── CLI Entrypoint ───────────────────────────────────────────────────────────

def main():
    """Run the full MCL 722.23 best-interest factor analysis."""
    print("=" * 70)
    print("MCL 722.23 BEST-INTEREST FACTOR ANALYZER")
    print("Pigors v. Watson — Custody Modification")
    print("=" * 70)
    print()

    analyzer = BestInterestAnalyzer()
    try:
        print("Analyzing all 12 factors...")
        results = analyzer.analyze_all_factors()

        print("\n--- Factor Scores ---")
        for letter in "abcdefghijkl":
            a = results[letter]
            print(
                f"  ({letter}) {a.title[:50]:50s} → {a.score.value}"
            )

        print("\nGenerating comprehensive report...")
        report = analyzer.generate_report()
        print(f"\nReport length: {len(report):,} characters")
        print("Done.")
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
