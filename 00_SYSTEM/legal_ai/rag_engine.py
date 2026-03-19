"""
Legal RAG Engine — LitigationOS Legal AI
==========================================
Evidence-aware Retrieval-Augmented Generation with corrective loops,
source grounding verification, and lane-aware retrieval.

Pipeline (100 % local, zero LLM):
  1. Detect case lane (A–F) from query
  2. Retrieve evidence via CrossBrainOptimizer + direct FTS5
  3. Generate extractive answer (TF-IDF sentence ranking)
  4. Verify every answer sentence is grounded in evidence
  5. If confidence < threshold → expand query → re-retrieve → re-generate

Usage:
    from legal_ai.rag_engine import LegalRAGEngine
    rag = LegalRAGEngine()
    response = rag.query("What MCR governs judicial disqualification?")
    print(response.answer)
    print(f"Grounding: {response.grounding_rate:.0%}")
"""

from __future__ import annotations

import logging
import math
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.rag_engine")

_HERE = Path(__file__).parent
_REPO = _HERE.parent.parent

# ── Lazy imports ─────────────────────────────────────────────────
# BrainManager and CrossBrainOptimizer are imported lazily inside __init__
# to avoid hanging at module load (brain_manager.py performs I/O on import).


# ── Data Models ──────────────────────────────────────────────────

@dataclass
class RetrievedEvidence:
    """A single piece of evidence retrieved for a query."""
    text: str
    source: str
    brain_name: str = ""
    table_name: str = ""
    score: float = 0.0
    method: str = "fts5"        # bm25 / fts5 / brain_fts / rrf
    lane: str = ""
    evidence_strength: str = "unknown"   # strong / moderate / weak / unknown
    citations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroundedClaim:
    """An answer sentence with its source backing."""
    claim_text: str
    supporting_sources: List[str] = field(default_factory=list)
    citation_refs: List[str] = field(default_factory=list)
    grounded: bool = False
    confidence: float = 0.0


@dataclass
class RAGResponse:
    """Complete response from the RAG pipeline."""
    query: str = ""
    answer: str = ""
    grounded_claims: List[GroundedClaim] = field(default_factory=list)
    retrieved_evidence: List[RetrievedEvidence] = field(default_factory=list)
    retrieval_count: int = 0
    correction_cycles: int = 0
    final_confidence: float = 0.0
    lane_detected: str = ""
    query_time_ms: float = 0.0
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    total_time_ms: float = 0.0
    grounding_rate: float = 0.0
    warnings: List[str] = field(default_factory=list)


# ── Constants ────────────────────────────────────────────────────

EVIDENCE_WEIGHTS: Dict[str, float] = {
    "RECORD_FACT": 1.00,
    "SWORN_FACT": 0.95,
    "EVIDENCE_FACT": 0.85,
    "ALLEGATION": 0.60,
    "INFERENCE": 0.40,
    "UNKNOWN": 0.50,
}

EVIDENCE_STRENGTH_MAP: Dict[str, str] = {
    "RECORD_FACT": "strong",
    "SWORN_FACT": "strong",
    "EVIDENCE_FACT": "moderate",
    "ALLEGATION": "weak",
    "INFERENCE": "weak",
    "UNKNOWN": "unknown",
}

LANE_PATTERNS: Dict[str, "re.Pattern[str]"] = {
    "A": re.compile(
        r"custody|parenting|visitation|child|best\s+interest|722\.23|domicile", re.I
    ),
    "B": re.compile(
        r"housing|eviction|landlord|tenant|shady\s+oaks|mobile\s+home|habitability|rent", re.I
    ),
    "C": re.compile(
        r"convergence|cross.?lane|multi.?case|pattern|systemic", re.I
    ),
    "D": re.compile(
        r"PPO|protection\s+order|stalking|harassment|domestic\s+violence", re.I
    ),
    "E": re.compile(
        r"judicial|misconduct|disqualification|bias|mcneill|JTC|2\.003", re.I
    ),
    "F": re.compile(
        r"appell|COA|MSC|366810|brief|standard\s+of\s+review", re.I
    ),
}

LEGAL_THESAURUS: Dict[str, List[str]] = {
    "custody": ["parenting time", "visitation", "placement", "physical custody", "legal custody"],
    "abuse": ["domestic violence", "assault", "harm", "endangerment", "maltreatment"],
    "bias": ["prejudice", "impartiality", "ex parte", "favoritism", "discrimination"],
    "eviction": ["unlawful detainer", "summary proceedings", "forcible entry", "possession"],
    "damages": ["compensation", "restitution", "treble damages", "punitive damages", "remedy"],
    "contempt": ["violation", "noncompliance", "willful disobedience", "sanctions"],
}

# Regex to split text into sentences
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


# ── Main Class ───────────────────────────────────────────────────

class LegalRAGEngine:
    """
    Evidence-aware corrective RAG pipeline for Michigan litigation.

    Retrieves evidence from the multi-brain architecture, generates
    extractive answers via TF-IDF sentence ranking, then verifies
    every claim is traceable to source material.  Runs corrective
    loops when grounding falls below the confidence threshold.

    Works with or without BrainManager / CrossBrainOptimizer — gracefully
    degrades to empty results when dependencies are unavailable.
    """

    def __init__(
        self,
        brain_manager: Optional[Any] = None,
        cross_brain_optimizer: Optional[Any] = None,
        max_corrections: int = 2,
        min_confidence: float = 0.4,
    ) -> None:
        """
        Args:
            brain_manager:        Optional BrainManager instance.
            cross_brain_optimizer: Optional CrossBrainOptimizer instance.
            max_corrections:      Maximum corrective retrieval/generation cycles.
            min_confidence:       Minimum grounding confidence to accept an answer.
        """
        # Brain manager (lazy import)
        self._bm = brain_manager
        if self._bm is None:
            try:
                _parent = str(Path(__file__).parent.parent)
                if _parent not in sys.path:
                    sys.path.insert(0, _parent)
                from brains.brain_manager import BrainManager  # type: ignore
                self._bm = BrainManager()
            except Exception as exc:
                logger.debug("Could not initialise BrainManager: %s", exc)

        # Cross-brain optimizer (lazy import to avoid circular dependency)
        self._optimizer = cross_brain_optimizer
        if self._optimizer is None:
            try:
                from legal_ai.cross_brain_optimizer import CrossBrainOptimizer
                self._optimizer = CrossBrainOptimizer(brain_manager=self._bm)
            except Exception as exc:
                logger.debug("Could not initialise CrossBrainOptimizer: %s", exc)

        self._max_corrections = max(max_corrections, 0)
        self._min_confidence = min_confidence

        # Counters
        self._total_queries: int = 0
        self._total_retrievals: int = 0
        self._total_corrections: int = 0
        self._total_grounding_sum: float = 0.0

    # ── Full Pipeline ────────────────────────────────────────────

    def query(
        self, query: str, lane: Optional[str] = None, top_k: int = 15
    ) -> RAGResponse:
        """
        Execute the full RAG pipeline: retrieve → generate → verify → correct.

        Args:
            query: Natural-language legal query.
            lane:  Optional case lane override (A–F).
            top_k: Number of evidence passages to retrieve.

        Returns:
            RAGResponse with answer, grounded claims, evidence, and metrics.
        """
        t0 = time.perf_counter()
        self._total_queries += 1
        warnings: List[str] = []

        # ── Lane detection ───────────────────────────────────────
        detected_lane = lane or self.detect_lane(query)

        # ── Retrieve ─────────────────────────────────────────────
        t_ret_0 = time.perf_counter()
        evidence = self.retrieve(query, lane=detected_lane, top_k=top_k)
        retrieval_ms = (time.perf_counter() - t_ret_0) * 1000

        if not evidence:
            warnings.append("No evidence retrieved — answer will be empty")
            elapsed = (time.perf_counter() - t0) * 1000
            return RAGResponse(
                query=query,
                answer="No relevant evidence found for this query.",
                lane_detected=detected_lane,
                retrieval_time_ms=retrieval_ms,
                total_time_ms=elapsed,
                warnings=warnings,
            )

        # ── Generate ─────────────────────────────────────────────
        t_gen_0 = time.perf_counter()
        answer = self.generate(query, evidence)
        generation_ms = (time.perf_counter() - t_gen_0) * 1000

        # ── Verify ───────────────────────────────────────────────
        confidence, grounded_claims = self.verify_grounding(answer, evidence)
        correction_cycles = 0

        # ── Corrective loop ──────────────────────────────────────
        while confidence < self._min_confidence and correction_cycles < self._max_corrections:
            correction_cycles += 1
            self._total_corrections += 1
            try:
                answer, evidence, confidence = self.correct(
                    query, evidence, answer, confidence
                )
                _, grounded_claims = self.verify_grounding(answer, evidence)
            except Exception as exc:
                warnings.append(f"Correction cycle {correction_cycles} failed: {exc}")
                logger.warning("Correction cycle %d failed: %s", correction_cycles, exc)
                break

        # ── Assemble response ────────────────────────────────────
        grounded_count = sum(1 for gc in grounded_claims if gc.grounded)
        grounding_rate = (
            grounded_count / len(grounded_claims)
            if grounded_claims
            else 0.0
        )
        self._total_grounding_sum += grounding_rate

        total_ms = (time.perf_counter() - t0) * 1000

        return RAGResponse(
            query=query,
            answer=answer,
            grounded_claims=grounded_claims,
            retrieved_evidence=evidence,
            retrieval_count=len(evidence),
            correction_cycles=correction_cycles,
            final_confidence=round(confidence, 4),
            lane_detected=detected_lane,
            query_time_ms=round(total_ms, 2),
            retrieval_time_ms=round(retrieval_ms, 2),
            generation_time_ms=round(generation_ms, 2),
            total_time_ms=round(total_ms, 2),
            grounding_rate=round(grounding_rate, 4),
            warnings=warnings,
        )

    # ── Retrieval ────────────────────────────────────────────────

    def retrieve(
        self, query: str, lane: Optional[str] = None, top_k: int = 15
    ) -> List[RetrievedEvidence]:
        """
        Multi-source retrieval via CrossBrainOptimizer (preferred) or
        direct BrainManager FTS5 fallback.

        Args:
            query: Search query.
            lane:  Optional case lane to hint brain selection.
            top_k: Maximum results.

        Returns:
            Evidence passages ranked by relevance and strength.
        """
        self._total_retrievals += 1
        evidence: List[RetrievedEvidence] = []

        # ── CrossBrainOptimizer path ─────────────────────────────
        if self._optimizer is not None:
            try:
                search_result = self._optimizer.search(query, top_k=top_k)
                for r in search_result.results:
                    ev = RetrievedEvidence(
                        text=r.text,
                        source=f"{r.brain_name}.{r.table_name}",
                        brain_name=r.brain_name,
                        table_name=r.table_name,
                        score=r.score,
                        method="rrf",
                        lane=lane or "",
                        evidence_strength=self._infer_strength(r.table_name),
                        citations=self._extract_citations(r.text),
                        metadata=r.metadata,
                    )
                    evidence.append(ev)
            except Exception as exc:
                logger.warning("CrossBrainOptimizer retrieval failed: %s", exc)

        # ── Direct BrainManager fallback ─────────────────────────
        if not evidence and self._bm is not None:
            try:
                raw_results = self._bm.search_all_brains(query)
                for brain_hit in raw_results:
                    brain = brain_hit.get("brain", "") if isinstance(brain_hit, dict) else ""
                    fts_table = brain_hit.get("fts_table", "") if isinstance(brain_hit, dict) else ""
                    rows = brain_hit.get("results", []) if isinstance(brain_hit, dict) else []
                    for row in rows[:top_k]:
                        text = self._row_text(row)
                        if text:
                            evidence.append(RetrievedEvidence(
                                text=text,
                                source=f"{brain}.{fts_table}",
                                brain_name=brain,
                                table_name=fts_table,
                                score=abs(float(row.get("rank", 0))) if isinstance(row, dict) else 0.0,
                                method="brain_fts",
                                lane=lane or "",
                                evidence_strength=self._infer_strength(fts_table),
                                citations=self._extract_citations(text),
                            ))
            except Exception as exc:
                logger.warning("BrainManager search fallback failed: %s", exc)

        # Weight and sort
        evidence = self.weight_by_evidence_strength(evidence)
        return evidence[:top_k]

    # ── Extractive Generation ────────────────────────────────────

    def generate(self, query: str, evidence: List[RetrievedEvidence]) -> str:
        """
        TF-IDF extractive generation: rank evidence sentences by cosine
        similarity to the query and compose an attributed answer.

        100 % local — no LLM, no API calls.

        Args:
            query:    The user query.
            evidence: Retrieved evidence passages.

        Returns:
            Composed answer string with source attributions.
        """
        if not evidence:
            return "No evidence available to answer this query."

        # ── Collect sentences with source tags ───────────────────
        tagged_sentences: List[Tuple[str, str]] = []   # (sentence, source_label)
        for ev in evidence:
            sentences = _SENT_SPLIT.split(ev.text.strip())
            for sent in sentences:
                sent = sent.strip()
                if len(sent) >= 20:
                    tagged_sentences.append((sent, ev.source))

        if not tagged_sentences:
            # Fallback: use raw evidence texts
            for ev in evidence[:5]:
                if ev.text.strip():
                    tagged_sentences.append((ev.text.strip()[:500], ev.source))

        if not tagged_sentences:
            return "Retrieved evidence could not be parsed into sentences."

        # ── Build TF-IDF vocabulary ──────────────────────────────
        all_docs = [query] + [s for s, _ in tagged_sentences]
        vocab = self._build_vocab(all_docs)
        query_vec = self._tfidf_vector(query, vocab, all_docs)
        if not any(query_vec.values()):
            # Empty query vector — return top evidence by retrieval score
            top_sents = tagged_sentences[:5]
            lines = [f"Per {src}: {sent}" for sent, src in top_sents]
            return "\n\n".join(lines)

        # ── Rank sentences ───────────────────────────────────────
        scored: List[Tuple[float, str, str]] = []
        for sent, src in tagged_sentences:
            sent_vec = self._tfidf_vector(sent, vocab, all_docs)
            sim = self._cosine_sim(query_vec, sent_vec)
            scored.append((sim, sent, src))
        scored.sort(key=lambda x: x[0], reverse=True)

        # ── Compose answer (top N sentences) ─────────────────────
        seen_sents: Set[str] = set()
        answer_lines: List[str] = []
        for sim, sent, src in scored:
            normalised = " ".join(sent.lower().split())
            if normalised in seen_sents:
                continue
            seen_sents.add(normalised)
            answer_lines.append(f"Per {src}: {sent}")
            if len(answer_lines) >= 5:
                break

        return "\n\n".join(answer_lines) if answer_lines else "Unable to compose answer from evidence."

    # ── Grounding Verification ───────────────────────────────────

    def verify_grounding(
        self, answer: str, evidence: List[RetrievedEvidence]
    ) -> Tuple[float, List[GroundedClaim]]:
        """
        Verify that each sentence in *answer* can be traced to at least
        one evidence passage via token overlap.

        Args:
            answer:   Generated answer text.
            evidence: Evidence used to generate the answer.

        Returns:
            Tuple of (overall confidence, list of GroundedClaim).
        """
        if not answer or not evidence:
            return (0.0, [])

        evidence_tokens_map: Dict[str, Set[str]] = {}
        for ev in evidence:
            tokens = set(self._tokenize(ev.text))
            evidence_tokens_map[ev.source] = tokens

        sentences = _SENT_SPLIT.split(answer.strip())
        claims: List[GroundedClaim] = []

        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 10:
                continue

            sent_tokens = set(self._tokenize(sent))
            if not sent_tokens:
                claims.append(GroundedClaim(claim_text=sent, grounded=False, confidence=0.0))
                continue

            best_overlap = 0.0
            supporting: List[str] = []
            citation_refs: List[str] = []

            for src, ev_tokens in evidence_tokens_map.items():
                if not ev_tokens:
                    continue
                overlap = len(sent_tokens & ev_tokens) / len(sent_tokens)
                if overlap > 0.3:
                    supporting.append(src)
                    # Pull citations from matching evidence
                    for ev in evidence:
                        if ev.source == src:
                            citation_refs.extend(ev.citations)
                if overlap > best_overlap:
                    best_overlap = overlap

            grounded = best_overlap >= 0.3
            claims.append(GroundedClaim(
                claim_text=sent,
                supporting_sources=supporting,
                citation_refs=list(set(citation_refs)),
                grounded=grounded,
                confidence=round(best_overlap, 4),
            ))

        if not claims:
            return (0.0, [])

        avg_conf = sum(c.confidence for c in claims) / len(claims)
        return (round(avg_conf, 4), claims)

    # ── Corrective Loop ──────────────────────────────────────────

    def correct(
        self,
        query: str,
        evidence: List[RetrievedEvidence],
        answer: str,
        confidence: float,
    ) -> Tuple[str, List[RetrievedEvidence], float]:
        """
        Expand the query using the legal thesaurus, re-retrieve, and
        re-generate to improve grounding.

        Args:
            query:      Original query.
            evidence:   Current evidence set.
            answer:     Current answer.
            confidence: Current grounding confidence.

        Returns:
            Tuple of (new_answer, expanded_evidence, new_confidence).
        """
        expanded = self._expand_query(query)
        if expanded == query:
            # No expansion possible — widen search
            expanded = query + " evidence record order"

        new_evidence = self.retrieve(expanded, top_k=20)

        # Merge new evidence with existing (deduplicate by text)
        seen_texts: Set[str] = {ev.text[:200] for ev in evidence}
        merged = list(evidence)
        for ev in new_evidence:
            if ev.text[:200] not in seen_texts:
                merged.append(ev)
                seen_texts.add(ev.text[:200])

        new_answer = self.generate(query, merged)
        new_conf, _ = self.verify_grounding(new_answer, merged)
        return (new_answer, merged, new_conf)

    # ── Lane Detection ───────────────────────────────────────────

    def detect_lane(self, query: str) -> str:
        """
        Classify a query into one of the six case lanes (A–F).

        Detection priority mirrors MEEK signal priority: E → D → F → C → A → B.

        Args:
            query: Input text.

        Returns:
            Lane letter (A–F) or empty string if unclassified.
        """
        priority_order = ["E", "D", "F", "C", "A", "B"]
        for lane in priority_order:
            pattern = LANE_PATTERNS.get(lane)
            if pattern and pattern.search(query):
                return lane
        return ""

    # ── Evidence Weighting ───────────────────────────────────────

    def weight_by_evidence_strength(
        self, results: List[RetrievedEvidence]
    ) -> List[RetrievedEvidence]:
        """
        Adjust scores based on evidence strength classifications.

        Strong evidence (record facts, sworn testimony) gets boosted;
        weak evidence (inferences, allegations) gets reduced.

        Args:
            results: Evidence list to re-weight.

        Returns:
            Re-sorted evidence list.
        """
        for ev in results:
            weight = EVIDENCE_WEIGHTS.get(
                ev.evidence_strength.upper() if ev.evidence_strength else "UNKNOWN",
                EVIDENCE_WEIGHTS["UNKNOWN"],
            )
            ev.score = ev.score * weight

        results.sort(key=lambda e: e.score, reverse=True)
        return results

    # ── Statistics ───────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Return engine status and capabilities."""
        avg_grounding = (
            round(self._total_grounding_sum / self._total_queries, 4)
            if self._total_queries > 0
            else 0.0
        )
        return {
            "version": "1.0.0",
            "brain_manager_available": self._bm is not None,
            "cross_brain_optimizer_available": self._optimizer is not None,
            "max_corrections": self._max_corrections,
            "min_confidence": self._min_confidence,
            "lane_patterns": list(LANE_PATTERNS.keys()),
            "thesaurus_terms": len(LEGAL_THESAURUS),
            "evidence_strength_levels": list(EVIDENCE_WEIGHTS.keys()),
            "total_queries": self._total_queries,
            "total_retrievals": self._total_retrievals,
            "total_corrections": self._total_corrections,
            "avg_grounding_rate": avg_grounding,
        }

    # ── Private Helpers ──────────────────────────────────────────

    def _expand_query(self, query: str) -> str:
        """Expand query terms using the legal thesaurus."""
        tokens = query.lower().split()
        additions: List[str] = []
        for token in tokens:
            synonyms = LEGAL_THESAURUS.get(token, [])
            if synonyms:
                additions.extend(synonyms[:2])
        if additions:
            return query + " " + " ".join(additions)
        return query

    def _infer_strength(self, table_name: str) -> str:
        """Infer evidence strength from the FTS table name."""
        strong_tables = {"court_rules_fts", "statutes_fts", "case_law_fts", "evidence_rules_fts"}
        moderate_tables = {"orders_fts", "testimony_fts", "police_fts", "benchbook_fts"}
        weak_tables = {"drafts_fts", "applications_fts", "communications_fts"}
        if table_name in strong_tables:
            return "strong"
        if table_name in moderate_tables:
            return "moderate"
        if table_name in weak_tables:
            return "weak"
        return "unknown"

    def _extract_citations(self, text: str) -> List[str]:
        """Extract legal citations from text via simple regex."""
        patterns = [
            r"MCR\s+\d+\.\d+(?:\([A-Z]\))?(?:\(\d+\))?",
            r"MCL\s+\d+\.\d+[a-z]?(?:\(\d+\))?",
            r"MRE\s+\d+",
            r"\d+\s+(?:Mich|Mich\s+App)\s+\d+",
            r"\d+\s+USC?\s+§?\s*\d+",
        ]
        found: List[str] = []
        for pat in patterns:
            found.extend(re.findall(pat, text, re.I))
        return list(set(found))

    def _row_text(self, row: Any) -> str:
        """Extract text content from a database row."""
        if isinstance(row, dict):
            for col in ("content", "text", "full_text", "body", "rule_text",
                        "summary", "description", "excerpt", "title"):
                val = row.get(col)
                if val and isinstance(val, str):
                    return val[:2000]
        return str(row)[:500] if row else ""

    def _tokenize(self, text: str) -> List[str]:
        """Simple whitespace + lowering tokenizer, filtering short tokens."""
        return [
            t for t in re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower()).split()
            if len(t) >= 2
        ]

    def _build_vocab(self, docs: List[str]) -> Dict[str, int]:
        """Build vocabulary mapping token → document frequency."""
        df: Counter = Counter()
        for doc in docs:
            tokens = set(self._tokenize(doc))
            for t in tokens:
                df[t] += 1
        return dict(df)

    def _tfidf_vector(
        self, text: str, vocab: Dict[str, int], corpus: List[str]
    ) -> Dict[str, float]:
        """Compute TF-IDF vector for a text against the given vocabulary."""
        tokens = self._tokenize(text)
        tf: Counter = Counter(tokens)
        n_docs = len(corpus)
        vec: Dict[str, float] = {}
        for token, count in tf.items():
            df = vocab.get(token, 0)
            if df == 0:
                continue
            idf = math.log((n_docs + 1) / (df + 1)) + 1.0
            vec[token] = (count / max(len(tokens), 1)) * idf
        return vec

    def _cosine_sim(self, a: Dict[str, float], b: Dict[str, float]) -> float:
        """Cosine similarity between two sparse vectors."""
        if not a or not b:
            return 0.0
        common = set(a.keys()) & set(b.keys())
        dot = sum(a[k] * b[k] for k in common)
        mag_a = math.sqrt(sum(v * v for v in a.values()))
        mag_b = math.sqrt(sum(v * v for v in b.values()))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)
