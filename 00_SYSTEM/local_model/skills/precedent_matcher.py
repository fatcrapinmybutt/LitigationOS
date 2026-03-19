"""
MBP LitigationOS — Michigan Case-Law Precedent Matcher
=======================================================
Searches litigation_context.db across master_citations, auth_authority_passages,
legal_reference_docs, research_summaries, and the authority graph to find,
rank, and chain Michigan legal precedents for any legal issue.

CLI:  python precedent_matcher.py "judicial disqualification ex parte contact"
"""
from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import sys
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Optional: sklearn TF-IDF for better ranking; falls back to term-frequency
# ---------------------------------------------------------------------------
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

sys.path.insert(0, str(Path(__file__).resolve().parent.parent if 'skills' in str(Path(__file__)) else Path(__file__).resolve().parent))
try:
    from cycle_method import cycle_json, cycle_print
except ImportError:
    cycle_json = lambda obj, **kw: print(json.dumps(obj, default=str))
    cycle_print = print

DB_PATH = os.environ.get(
    "LITIGATION_DB",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class PrecedentResult:
    citation: str
    context: str
    relevance_score: float
    source_table: str
    cite_type: str = ""
    which_side_it_helps: str = "neutral"
    rule_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "citation": self.citation,
            "context": self.context[:500],
            "relevance_score": round(self.relevance_score, 4),
            "source_table": self.source_table,
            "cite_type": self.cite_type,
            "which_side_it_helps": self.which_side_it_helps,
            "rule_refs": self.rule_refs,
        }


@dataclass
class AuthorityChainNode:
    node_id: str
    label: str
    node_type: str
    children: List["AuthorityChainNode"] = field(default_factory=list)
    cases_citing: List[PrecedentResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "label": self.label,
            "node_type": self.node_type,
            "cases_citing": [c.to_dict() for c in self.cases_citing],
            "children": [ch.to_dict() for ch in self.children],
        }


# ---------------------------------------------------------------------------
# Keyword / NLP helpers
# ---------------------------------------------------------------------------

_STOP = set(
    "a an the and or but in on of to for with is are was were be been "
    "being have has had do does did will shall should would could may might "
    "can this that these those it its at by from as not no nor so if".split()
)

_LEGAL_SYNONYMS: Dict[str, List[str]] = {
    "custody": ["custody", "custodial", "parenting time", "parental rights"],
    "disqualification": ["disqualification", "disqualify", "recusal", "recuse"],
    "bias": ["bias", "prejudice", "impartiality", "partial", "impartial"],
    "ex parte": ["ex parte", "one-sided", "without notice"],
    "alienation": ["alienation", "alienate", "alienating", "parental alienation"],
    "best interest": ["best interest", "best interests", "child welfare"],
    "ppo": ["ppo", "personal protection order", "protective order", "restraining"],
    "stalking": ["stalking", "harassment", "stalk", "harass"],
    "misconduct": ["misconduct", "judicial misconduct", "abuse of discretion"],
    "modification": ["modification", "modify", "change", "changed circumstances"],
    "due process": ["due process", "procedural due process", "substantive due process"],
    "contempt": ["contempt", "violation of order"],
    "foc": ["foc", "friend of the court", "friend of court"],
    "domestic violence": ["domestic violence", "dv", "abuse"],
}

# Lane keyword mappings
_LANE_KEYWORDS: Dict[str, List[str]] = {
    "MEEK1": [
        "custody", "custodial", "parenting time", "best interest", "child",
        "modification", "established custodial environment", "ECE",
        "MCL 722", "Vodvarka", "Shade", "changed circumstances",
    ],
    "MEEK2": [
        "PPO", "personal protection order", "stalking", "harassment",
        "MCL 600.2950", "domestic violence", "restraining", "Hayford",
    ],
    "MEEK3": [
        "convergence", "consolidation", "judicial economy", "related cases",
        "MCR 2.505", "joinder", "merger",
    ],
    "MEEK4": [
        "judicial misconduct", "disqualification", "recusal", "bias",
        "ex parte", "canon", "JTC", "Caperton", "Cain", "due process",
        "MCR 2.003", "impartiality", "prejudice",
    ],
}

# Counter-argument signals
_COUNTER_SIGNALS = [
    "however", "but see", "cf.", "contra", "distinguished", "overruled",
    "limitation", "exception", "narrow", "inapplicable", "does not apply",
    "rejected", "declined", "reversed", "vacated", "abrogated",
    "notwithstanding", "absent", "insufficient", "failed to show",
    "failed to demonstrate", "harmless error", "discretion", "deference",
    "presumption", "burden", "waived", "forfeited",
]


def _extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords, expanding legal synonyms."""
    tokens = re.findall(r"[a-z][a-z']+", text.lower())
    keywords = [t for t in tokens if t not in _STOP and len(t) > 2]
    expanded: List[str] = list(keywords)
    for kw in keywords:
        for root, syns in _LEGAL_SYNONYMS.items():
            if kw in root or root in kw or kw in syns:
                expanded.extend(syns)
    # Also preserve multi-word phrases from input
    lower = text.lower()
    for root, syns in _LEGAL_SYNONYMS.items():
        for phrase in syns:
            if phrase in lower and phrase not in expanded:
                expanded.append(phrase)
    return list(dict.fromkeys(expanded))  # dedupe, preserve order


def _extract_case_citation(text: str) -> Optional[str]:
    """Pull a Michigan case cite from a string (e.g. '259 Mich App 499')."""
    m = re.search(r"\d{1,3}\s+Mich(?:\s+App)?\s+\d{1,4}", text)
    return m.group(0) if m else None


def _extract_rule_cite(text: str) -> Optional[str]:
    """Pull MCR or MCL cite."""
    m = re.search(r"(MCR|MCL)\s+[\d.]+", text)
    return m.group(0) if m else None


# ---------------------------------------------------------------------------
# Simple TF-IDF fallback when sklearn is unavailable
# ---------------------------------------------------------------------------

def _simple_tf_score(query_kws: List[str], document: str) -> float:
    """Weighted term-frequency score with positional bonus."""
    if not document:
        return 0.0
    doc_lower = document.lower()
    doc_tokens = re.findall(r"[a-z][a-z']+", doc_lower)
    if not doc_tokens:
        return 0.0
    tf = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    score = 0.0
    for kw in query_kws:
        if " " in kw:  # phrase match bonus
            if kw in doc_lower:
                score += 3.0
        elif kw in tf:
            score += (1 + math.log(tf[kw])) / math.log(doc_len + 1)
    return score


def _classify_side(context: str, is_counter_search: bool = False) -> str:
    """Heuristic: does this help movant, respondent, or neutral?"""
    lower = context.lower()
    counter_hits = sum(1 for sig in _COUNTER_SIGNALS if sig in lower)
    movant_signals = [
        "must", "shall", "required", "violated", "denied",
        "reversible error", "abuse of discretion", "due process",
    ]
    movant_hits = sum(1 for sig in movant_signals if sig in lower)
    if is_counter_search:
        if counter_hits >= 2:
            return "opposing_side"
        return "potentially_opposing"
    if counter_hits > movant_hits:
        return "opposing_side"
    if movant_hits > counter_hits:
        return "movant"
    return "neutral"


# ---------------------------------------------------------------------------
# PrecedentMatcher
# ---------------------------------------------------------------------------

class PrecedentMatcher:
    """Michigan case-law precedent matcher against litigation_context.db."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # -- connection management ------------------------------------------------

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    # -- internal search helpers ----------------------------------------------

    def _search_master_citations(
        self, keywords: List[str], limit: int = 50
    ) -> List[PrecedentResult]:
        """Search master_citations using FTS-like LIKE queries + scoring."""
        results: List[PrecedentResult] = []
        cur = self.conn.cursor()
        # Build OR clauses for the most important keywords (cap at 12)
        top_kws = keywords[:12]
        where_clauses = []
        params: list = []
        for kw in top_kws:
            where_clauses.append("(context LIKE ? OR citation LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])
        if not where_clauses:
            return results
        sql = (
            f"SELECT source_file, directory, cite_type, citation, "
            f"line_number, context FROM master_citations "
            f"WHERE ({' OR '.join(where_clauses)}) "
            f"AND cite_type IN ('MCR','MCL','CASE_LAW','CANON') "
            f"LIMIT {limit * 3}"
        )
        cur.execute(sql, params)
        for row in cur.fetchall():
            ctx = row["context"] or ""
            score = _simple_tf_score(keywords, ctx + " " + (row["citation"] or ""))
            results.append(
                PrecedentResult(
                    citation=row["citation"] or "",
                    context=ctx,
                    relevance_score=score,
                    source_table="master_citations",
                    cite_type=row["cite_type"] or "",
                )
            )
        return results

    def _search_fts_auth_passages(
        self, keywords: List[str], limit: int = 30
    ) -> List[PrecedentResult]:
        """Search auth_passages_fts (FTS5)."""
        results: List[PrecedentResult] = []
        cur = self.conn.cursor()
        # Build FTS match expression
        fts_terms = [kw for kw in keywords if " " not in kw][:10]
        if not fts_terms:
            return results
        match_expr = " OR ".join(fts_terms)
        try:
            cur.execute(
                "SELECT rule_id, passage_text, section "
                "FROM auth_passages_fts WHERE auth_passages_fts MATCH ? "
                f"LIMIT {limit}",
                (match_expr,),
            )
            for row in cur.fetchall():
                txt = row["passage_text"] or ""
                score = _simple_tf_score(keywords, txt)
                cite = _extract_rule_cite(txt) or row["rule_id"] or ""
                results.append(
                    PrecedentResult(
                        citation=cite,
                        context=txt[:600],
                        relevance_score=score,
                        source_table="auth_authority_passages",
                        cite_type="MCR",
                    )
                )
        except sqlite3.OperationalError:
            pass
        return results

    def _search_fts_auth_rules(
        self, keywords: List[str], limit: int = 30
    ) -> List[PrecedentResult]:
        """Search auth_rules_fts (FTS5)."""
        results: List[PrecedentResult] = []
        cur = self.conn.cursor()
        fts_terms = [kw for kw in keywords if " " not in kw][:10]
        if not fts_terms:
            return results
        match_expr = " OR ".join(fts_terms)
        try:
            cur.execute(
                "SELECT id, rule_number, title, full_text, summary "
                "FROM auth_rules_fts WHERE auth_rules_fts MATCH ? "
                f"LIMIT {limit}",
                (match_expr,),
            )
            for row in cur.fetchall():
                txt = (row["full_text"] or "") + " " + (row["summary"] or "")
                score = _simple_tf_score(keywords, txt)
                cite = f"MCR {row['rule_number']}" if row["rule_number"] else row["id"]
                results.append(
                    PrecedentResult(
                        citation=cite,
                        context=(row["title"] or "") + " — " + txt[:500],
                        relevance_score=score,
                        source_table="auth_rules",
                        cite_type="MCR",
                    )
                )
        except sqlite3.OperationalError:
            pass
        return results

    def _search_legal_ref_docs(
        self, keywords: List[str], limit: int = 20
    ) -> List[PrecedentResult]:
        """Search legal_reference_docs.body with keyword matching."""
        results: List[PrecedentResult] = []
        cur = self.conn.cursor()
        top_kws = keywords[:8]
        where_clauses = [f"body LIKE ?" for _ in top_kws]
        params = [f"%{kw}%" for kw in top_kws]
        if not where_clauses:
            return results
        sql = (
            f"SELECT section_id, heading_level, heading, body, source_file "
            f"FROM legal_reference_docs "
            f"WHERE {' OR '.join(where_clauses)} LIMIT {limit * 2}"
        )
        cur.execute(sql, params)
        for row in cur.fetchall():
            body = row["body"] or ""
            score = _simple_tf_score(keywords, body + " " + (row["heading"] or ""))
            cite = _extract_rule_cite(body) or _extract_case_citation(body) or row["heading"] or ""
            results.append(
                PrecedentResult(
                    citation=cite,
                    context=(row["heading"] or "") + " — " + body[:500],
                    relevance_score=score,
                    source_table="legal_reference_docs",
                )
            )
        return results

    def _search_research_summaries(
        self, keywords: List[str], lane: Optional[str] = None, limit: int = 20
    ) -> List[PrecedentResult]:
        """Search research_summaries."""
        results: List[PrecedentResult] = []
        cur = self.conn.cursor()
        top_kws = keywords[:8]
        clauses = ["(key_points LIKE ? OR practical_notes LIKE ? OR topic LIKE ?)" for _ in top_kws]
        params: list = []
        for kw in top_kws:
            params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])
        where = " OR ".join(clauses) if clauses else "1=1"
        if lane:
            where = f"({where}) AND case_lane = ?"
            params.append(lane)
        sql = (
            f"SELECT id, topic, subtopic, rule_refs, key_points, "
            f"practical_notes, case_lane FROM research_summaries "
            f"WHERE {where} LIMIT {limit}"
        )
        cur.execute(sql, params)
        for row in cur.fetchall():
            combined = " ".join(
                filter(None, [row["key_points"], row["practical_notes"]])
            )
            score = _simple_tf_score(keywords, combined)
            cite = _extract_rule_cite(combined) or row["subtopic"] or ""
            results.append(
                PrecedentResult(
                    citation=cite,
                    context=combined[:600],
                    relevance_score=score,
                    source_table="research_summaries",
                    cite_type="research",
                    rule_refs=[row["rule_refs"]] if row["rule_refs"] else [],
                )
            )
        return results

    def _search_md_sections_fts(
        self, keywords: List[str], limit: int = 20
    ) -> List[PrecedentResult]:
        """Search md_sections_fts for broader coverage."""
        results: List[PrecedentResult] = []
        cur = self.conn.cursor()
        fts_terms = [kw for kw in keywords if " " not in kw][:8]
        if not fts_terms:
            return results
        match_expr = " OR ".join(fts_terms)
        try:
            cur.execute(
                "SELECT section_title, content, section_path "
                "FROM md_sections_fts WHERE md_sections_fts MATCH ? "
                f"LIMIT {limit}",
                (match_expr,),
            )
            for row in cur.fetchall():
                txt = row["content"] or ""
                score = _simple_tf_score(keywords, txt)
                cite = (
                    _extract_case_citation(txt)
                    or _extract_rule_cite(txt)
                    or row["section_title"]
                    or ""
                )
                # Only keep if contains an actual legal citation
                if _extract_case_citation(txt) or _extract_rule_cite(txt):
                    results.append(
                        PrecedentResult(
                            citation=cite,
                            context=(row["section_title"] or "") + " — " + txt[:500],
                            relevance_score=score,
                            source_table="md_sections",
                        )
                    )
        except sqlite3.OperationalError:
            pass
        return results

    # -- sklearn reranker ----------------------------------------------------

    def _rerank_sklearn(
        self, query: str, results: List[PrecedentResult]
    ) -> List[PrecedentResult]:
        """Rerank results using sklearn TF-IDF cosine similarity."""
        if not HAS_SKLEARN or len(results) < 2:
            return results
        corpus = [r.context for r in results]
        vectorizer = TfidfVectorizer(
            stop_words="english", max_features=5000, ngram_range=(1, 2)
        )
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus + [query])
            query_vec = tfidf_matrix[-1]
            doc_vecs = tfidf_matrix[:-1]
            sims = cosine_similarity(query_vec, doc_vecs).flatten()
            for i, r in enumerate(results):
                # Blend original keyword score with TF-IDF cosine similarity
                r.relevance_score = 0.4 * r.relevance_score + 0.6 * float(sims[i]) * 10
        except Exception:
            pass
        return results

    # -- deduplication -------------------------------------------------------

    @staticmethod
    def _deduplicate(results: List[PrecedentResult]) -> List[PrecedentResult]:
        """Deduplicate by normalized citation string, keeping highest-scored."""
        best: Dict[str, PrecedentResult] = {}
        for r in results:
            key = re.sub(r"\s+", " ", r.citation.strip().upper())
            if not key or key in ("NO", "YES", ""):
                continue
            if key not in best or r.relevance_score > best[key].relevance_score:
                best[key] = r
        return sorted(best.values(), key=lambda x: x.relevance_score, reverse=True)

    # ======================================================================
    # PUBLIC API
    # ======================================================================

    def find_precedents(
        self,
        issue: str,
        limit: int = 10,
        lane: Optional[str] = None,
        counter: bool = False,
    ) -> List[PrecedentResult]:
        """Find precedents for a legal issue string, ranked by relevance."""
        keywords = _extract_keywords(issue)
        if not keywords:
            return []

        # Gather from all sources
        all_results: List[PrecedentResult] = []
        all_results.extend(self._search_master_citations(keywords, limit * 5))
        all_results.extend(self._search_fts_auth_passages(keywords, limit * 3))
        all_results.extend(self._search_fts_auth_rules(keywords, limit * 3))
        all_results.extend(self._search_legal_ref_docs(keywords, limit * 2))
        all_results.extend(self._search_research_summaries(keywords, lane, limit * 2))
        all_results.extend(self._search_md_sections_fts(keywords, limit * 2))

        # Classify which side each result helps
        for r in all_results:
            r.which_side_it_helps = _classify_side(r.context, counter)

        # Rerank with sklearn if available
        all_results = self._rerank_sklearn(issue, all_results)

        # Deduplicate and return top N
        deduped = self._deduplicate(all_results)
        return deduped[:limit]

    def find_for_rule(self, rule_number: str, limit: int = 20) -> List[PrecedentResult]:
        """Find all cases / contexts citing a specific MCR/MCL rule."""
        cur = self.conn.cursor()
        results: List[PrecedentResult] = []
        # Normalize: accept "MCR 2.003" or "2.003"
        clean = rule_number.strip()
        pattern = f"%{clean}%"

        cur.execute(
            "SELECT source_file, cite_type, citation, context "
            "FROM master_citations "
            "WHERE citation LIKE ? OR context LIKE ? "
            "LIMIT ?",
            (pattern, pattern, limit * 3),
        )
        for row in cur.fetchall():
            ctx = row["context"] or ""
            results.append(
                PrecedentResult(
                    citation=row["citation"] or clean,
                    context=ctx[:600],
                    relevance_score=_simple_tf_score([clean.lower()], ctx),
                    source_table="master_citations",
                    cite_type=row["cite_type"] or "",
                    which_side_it_helps=_classify_side(ctx),
                )
            )

        # Also search auth_rules
        cur.execute(
            "SELECT id, rule_type, rule_number, title, full_text "
            "FROM auth_rules WHERE rule_number LIKE ? LIMIT 10",
            (pattern,),
        )
        for row in cur.fetchall():
            txt = row["full_text"] or ""
            results.append(
                PrecedentResult(
                    citation=f"{row['rule_type']} {row['rule_number']}",
                    context=(row["title"] or "") + " — " + txt[:500],
                    relevance_score=5.0,  # direct rule match
                    source_table="auth_rules",
                    cite_type=row["rule_type"] or "",
                )
            )

        return self._deduplicate(results)[:limit]

    def build_authority_chain(
        self, issue: str, depth: int = 2
    ) -> List[AuthorityChainNode]:
        """Build a tree of authorities: rule → interpreting cases → citing cases."""
        keywords = _extract_keywords(issue)
        cur = self.conn.cursor()
        chains: List[AuthorityChainNode] = []

        # Step 1: find the most relevant rules via auth_rules_fts
        fts_terms = [kw for kw in keywords if " " not in kw][:8]
        if not fts_terms:
            return chains
        match_expr = " OR ".join(fts_terms)

        root_rules: List[Tuple[str, str, str]] = []  # (id, rule_number, title)
        try:
            cur.execute(
                "SELECT id, rule_number, title FROM auth_rules_fts "
                "WHERE auth_rules_fts MATCH ? LIMIT 5",
                (match_expr,),
            )
            root_rules = [(r["id"], r["rule_number"], r["title"]) for r in cur.fetchall()]
        except sqlite3.OperationalError:
            # Fallback to LIKE
            for kw in keywords[:3]:
                cur.execute(
                    "SELECT id, rule_number, title FROM auth_rules "
                    "WHERE title LIKE ? OR full_text LIKE ? LIMIT 3",
                    (f"%{kw}%", f"%{kw}%"),
                )
                root_rules.extend(
                    [(r["id"], r["rule_number"], r["title"]) for r in cur.fetchall()]
                )

        seen_rules = set()
        for rule_id, rule_num, title in root_rules:
            if rule_num in seen_rules:
                continue
            seen_rules.add(rule_num)
            node = AuthorityChainNode(
                node_id=rule_id, label=f"MCR {rule_num}", node_type="rule"
            )
            # Step 2: cases interpreting this rule
            cases = self.find_for_rule(rule_num, limit=5)
            node.cases_citing = cases

            # Step 3: follow graph edges from this rule (depth 1)
            if depth > 0:
                cur2 = self.conn.cursor()
                cur2.execute(
                    "SELECT target_id, edge_type FROM auth_authority_edges "
                    "WHERE source_id LIKE ? LIMIT 20",
                    (f"%{rule_num}%",),
                )
                for edge in cur2.fetchall():
                    target = edge["target_id"]
                    child_node = AuthorityChainNode(
                        node_id=target,
                        label=target,
                        node_type="cross_ref",
                    )
                    # Find cases for the child rule
                    child_rule = re.search(r"[\d.]+", target)
                    if child_rule:
                        child_cases = self.find_for_rule(child_rule.group(0), limit=3)
                        child_node.cases_citing = child_cases
                    node.children.append(child_node)
                    if len(node.children) >= 5:
                        break

            chains.append(node)
            if len(chains) >= 3:
                break

        return chains

    def find_opposing_authority(
        self, issue: str, limit: int = 10
    ) -> List[PrecedentResult]:
        """Find authorities the opposing side might use."""
        # Search with counter-argument signals injected
        counter_issue = issue + " " + " ".join(_COUNTER_SIGNALS[:8])
        results = self.find_precedents(counter_issue, limit=limit * 2, counter=True)

        # Also search for results with explicit counter-language
        keywords = _extract_keywords(issue)
        extra: List[PrecedentResult] = []
        cur = self.conn.cursor()
        for sig in ["harmless error", "deference", "discretion", "burden of proof", "waived"]:
            for kw in keywords[:3]:
                cur.execute(
                    "SELECT citation, context, cite_type FROM master_citations "
                    "WHERE context LIKE ? AND context LIKE ? "
                    "AND cite_type IN ('MCR','MCL','CASE_LAW','CANON') LIMIT 5",
                    (f"%{kw}%", f"%{sig}%"),
                )
                for row in cur.fetchall():
                    ctx = row["context"] or ""
                    extra.append(
                        PrecedentResult(
                            citation=row["citation"] or "",
                            context=ctx[:500],
                            relevance_score=_simple_tf_score(keywords, ctx),
                            source_table="master_citations",
                            cite_type=row["cite_type"] or "",
                            which_side_it_helps="opposing_side",
                        )
                    )
                    if len(extra) >= limit:
                        break

        combined = results + extra
        for r in combined:
            if r.which_side_it_helps == "neutral":
                r.which_side_it_helps = "potentially_opposing"
        return self._deduplicate(combined)[:limit]

    def match_to_case_lane(
        self, lane: str, limit: int = 15
    ) -> List[PrecedentResult]:
        """Find all precedents relevant to a specific case lane."""
        lane = lane.upper()
        if lane not in _LANE_KEYWORDS:
            raise ValueError(f"Unknown lane: {lane}. Valid: {list(_LANE_KEYWORDS)}")

        kw_list = _LANE_KEYWORDS[lane]
        issue_str = " ".join(kw_list)
        results = self.find_precedents(issue_str, limit=limit, lane=lane)

        # Also pull research_summaries filtered by lane
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, topic, subtopic, rule_refs, key_points, practical_notes "
            "FROM research_summaries WHERE case_lane = ?",
            (lane,),
        )
        for row in cur.fetchall():
            combined = " ".join(filter(None, [row["key_points"], row["practical_notes"]]))
            cite = _extract_rule_cite(combined) or row["subtopic"] or row["topic"]
            results.append(
                PrecedentResult(
                    citation=cite,
                    context=combined[:600],
                    relevance_score=_simple_tf_score(kw_list, combined),
                    source_table="research_summaries",
                    cite_type="research",
                    which_side_it_helps="movant",
                    rule_refs=[row["rule_refs"]] if row["rule_refs"] else [],
                )
            )

        return self._deduplicate(results)[:limit]

    # -- reporting -----------------------------------------------------------

    def generate_report(
        self, queries: List[str], output_path: Optional[str] = None
    ) -> str:
        """Run multiple queries and produce a Markdown report."""
        lines: List[str] = [
            "# Michigan Precedent Analysis Report",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Database**: `{self.db_path}`",
            f"**Ranking engine**: {'sklearn TF-IDF' if HAS_SKLEARN else 'term-frequency fallback'}",
            "",
        ]

        for q in queries:
            lines.append(f"---\n## Query: *{q}*\n")

            # Main precedent search
            results = self.find_precedents(q, limit=10)
            lines.append("### Top Precedents\n")
            lines.append("| # | Citation | Score | Type | Side | Source |")
            lines.append("|---|----------|-------|------|------|--------|")
            for i, r in enumerate(results, 1):
                ctx_short = r.context[:120].replace("|", "\\|").replace("\n", " ")
                lines.append(
                    f"| {i} | {r.citation} | {r.relevance_score:.3f} | "
                    f"{r.cite_type} | {r.which_side_it_helps} | {r.source_table} |"
                )
            lines.append("")

            # Top 3 context snippets
            lines.append("### Key Holdings / Context\n")
            for i, r in enumerate(results[:3], 1):
                ctx = r.context[:300].replace("\n", " ").strip()
                lines.append(f"**{i}. {r.citation}**\n> {ctx}\n")

            # Opposing authority
            opp = self.find_opposing_authority(q, limit=5)
            if opp:
                lines.append("### Potential Opposing Authority\n")
                for i, r in enumerate(opp[:5], 1):
                    ctx = r.context[:200].replace("\n", " ").strip()
                    lines.append(f"{i}. **{r.citation}** ({r.relevance_score:.3f}) — {ctx}\n")
            lines.append("")

        # Lane analysis
        lines.append("---\n## Case Lane Analysis\n")
        for lane in ["MEEK1", "MEEK2", "MEEK3", "MEEK4"]:
            lines.append(f"### {lane}\n")
            lane_results = self.match_to_case_lane(lane, limit=8)
            for i, r in enumerate(lane_results[:8], 1):
                lines.append(f"{i}. **{r.citation}** (score {r.relevance_score:.3f}) — {r.context[:150].strip()}")
            lines.append("")

        report = "\n".join(lines)
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
        return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Michigan Case-Law Precedent Matcher — MBP LitigationOS"
    )
    parser.add_argument("issue", nargs="?", help="Legal issue to search")
    parser.add_argument("--rule", help="Find cases for a specific MCR/MCL rule")
    parser.add_argument("--lane", help="Match to case lane (MEEK1-4)")
    parser.add_argument("--chain", action="store_true", help="Build authority chain")
    parser.add_argument("--opposing", action="store_true", help="Find opposing authority")
    parser.add_argument("--limit", type=int, default=10, help="Max results")
    parser.add_argument("--report", help="Generate full report to file")
    parser.add_argument("--db", default=DB_PATH, help="Database path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    pm = PrecedentMatcher(db_path=args.db)

    try:
        if args.report:
            queries = [args.issue] if args.issue else [
                "custody modification changed circumstances",
                "judicial disqualification bias",
                "parental alienation best interest",
                "PPO stalking harassment",
            ]
            report = pm.generate_report(queries, output_path=args.report)
            print(f"Report saved to {args.report}")
            print(f"({len(report)} characters)")
            return

        if args.rule:
            results = pm.find_for_rule(args.rule, limit=args.limit)
        elif args.lane:
            results = pm.match_to_case_lane(args.lane, limit=args.limit)
        elif args.chain and args.issue:
            chains = pm.build_authority_chain(args.issue)
            if args.json:
                cycle_json([c.to_dict() for c in chains])
            else:
                for chain in chains:
                    print(f"\n{'='*60}")
                    print(f"ROOT: {chain.label} ({chain.node_type})")
                    for c in chain.cases_citing[:5]:
                        print(f"  +-- {c.citation} (score {c.relevance_score:.3f})")
                        print(f"  |   {c.context[:120]}")
                    for child in chain.children[:5]:
                        print(f"  \\-- {child.label}")
                        for cc in child.cases_citing[:3]:
                            print(f"       +-- {cc.citation} (score {cc.relevance_score:.3f})")
            return
        elif args.opposing and args.issue:
            results = pm.find_opposing_authority(args.issue, limit=args.limit)
        elif args.issue:
            results = pm.find_precedents(args.issue, limit=args.limit)
        else:
            parser.print_help()
            return

        if args.json:
            cycle_json([r.to_dict() for r in results])
        else:
            print(f"\n{'='*70}")
            print(f" Michigan Precedent Matcher — {len(results)} results")
            print(f"{'='*70}")
            for i, r in enumerate(results, 1):
                print(f"\n[{i}] {r.citation}")
                print(f"    Score: {r.relevance_score:.4f} | Type: {r.cite_type} | Side: {r.which_side_it_helps}")
                print(f"    Source: {r.source_table}")
                ctx = r.context[:200].replace("\n", " ").strip()
                print(f"    Context: {ctx}")

    finally:
        pm.close()


if __name__ == "__main__":
    main()
