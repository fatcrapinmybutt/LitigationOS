"""MANBEARPIG v10 — AI Legal Brain inference engine.

Production-grade, fully-offline legal AI layer for LitigationOS.  Provides
document classification, entity extraction, evidence scoring, lane detection,
citation parsing, and argument drafting using TF-IDF, BM25, regex, and
keyword-matching techniques.  Zero network dependencies.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic result models
# ---------------------------------------------------------------------------


class ClassificationResult(BaseModel):
    """Result of document classification."""

    doc_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    runner_up: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExtractedEntity(BaseModel):
    """A single entity extracted from text."""

    entity_type: str  # party, judge, date, amount, case_number
    value: str
    span_start: Optional[int] = None
    span_end: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class EvidenceScore(BaseModel):
    """Composite evidence quality score."""

    relevance: float = Field(ge=0.0, le=100.0)
    admissibility: float = Field(ge=0.0, le=100.0)
    impeachment: float = Field(ge=0.0, le=100.0)
    composite: float = Field(ge=0.0, le=100.0)
    factors: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class LaneDetection(BaseModel):
    """Case lane detection result."""

    lane: str  # A-F
    lane_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    signals: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class Citation(BaseModel):
    """A parsed legal citation."""

    raw: str
    citation_type: str  # mcr, mcl, mre, usc, frcp, case_law
    normalized: Optional[str] = None
    valid: bool = True
    fix_suggestion: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class StrengthAssessment(BaseModel):
    """Claim strength assessment."""

    score: float = Field(ge=0.0, le=100.0)
    grade: str  # A-F
    reasoning: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AuthoritySuggestion(BaseModel):
    """Recommended legal authority."""

    citation: str
    relevance: float = Field(ge=0.0, le=1.0)
    description: str

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Constants — document types, lane definitions, citation patterns
# ---------------------------------------------------------------------------

DOCUMENT_TYPES: dict[str, list[str]] = {
    "motion": [
        "motion", "move", "moves this court", "respectfully requests",
        "relief", "hereby moves", "order to show cause",
    ],
    "brief": [
        "brief", "argument", "appellee", "appellant", "amicus",
        "statement of facts", "table of authorities",
    ],
    "complaint": [
        "complaint", "plaintiff alleges", "cause of action", "count",
        "prayer for relief", "demand for jury", "wherefore",
    ],
    "response": [
        "response", "answer", "admits", "denies", "affirmative defense",
        "reply", "opposition",
    ],
    "affidavit": [
        "affidavit", "sworn", "under oath", "notarized", "affiant",
        "subscribed and sworn", "penalty of perjury",
    ],
    "order": [
        "order", "it is ordered", "it is hereby ordered", "the court orders",
        "court finds", "so ordered", "entered",
    ],
    "declaration": [
        "declaration", "declare under penalty", "certify", "attest",
    ],
    "exhibit": [
        "exhibit", "attached hereto", "bates", "marked as",
    ],
    "notice": [
        "notice", "hereby notifies", "take notice", "notice of hearing",
        "notice of filing",
    ],
    "subpoena": [
        "subpoena", "commanded to appear", "duces tecum", "you are commanded",
    ],
    "transcript": [
        "transcript", "proceedings", "q.", "a.", "the court:",
        "direct examination", "cross-examination",
    ],
}

CASE_LANES: dict[str, dict[str, Any]] = {
    "A": {
        "name": "Custody",
        "meek": "MEEK2",
        "keywords": [
            "custody", "parenting", "visitation", "child", "minor",
            "best interest", "parenting time", "guardian ad litem",
            "friend of court", "foc",
        ],
    },
    "B": {
        "name": "Housing",
        "meek": "MEEK1",
        "keywords": [
            "housing", "hoa", "habitability", "landlord", "tenant",
            "shady oaks", "lease", "eviction", "habitability",
        ],
    },
    "C": {
        "name": "Convergence",
        "meek": "",
        "keywords": [
            "convergence", "cross-lane", "multi-case", "consolidated",
        ],
    },
    "D": {
        "name": "PPO",
        "meek": "MEEK3",
        "keywords": [
            "ppo", "protection order", "personal protection",
            "stalking", "harassment", "domestic violence",
        ],
    },
    "E": {
        "name": "Misconduct",
        "meek": "MEEK4",
        "keywords": [
            "misconduct", "jtc", "judicial", "bias", "recusal",
            "disqualification", "mcneill", "canon", "code of conduct",
        ],
    },
    "F": {
        "name": "Appellate",
        "meek": "MEEK5",
        "keywords": [
            "appeal", "appellate", "coa", "msc", "supreme court",
            "claim of appeal", "leave to appeal", "court of appeals",
        ],
    },
}

LANE_PRIORITY: tuple[str, ...] = ("E", "D", "F", "C", "A", "B")

# ---------------------------------------------------------------------------
# Citation regex patterns
# ---------------------------------------------------------------------------

_CITATION_PATTERNS: dict[str, re.Pattern[str]] = {
    "mcr": re.compile(
        r"\bMCR\s*(\d{1,2}\.\d{2,4}(?:\([A-Za-z0-9]+\))*)", re.IGNORECASE,
    ),
    "mcl": re.compile(
        r"\bMCL\s*(\d{2,4}\.\d{1,6}[a-z]?(?:\([0-9a-z]+\))*)", re.IGNORECASE,
    ),
    "mre": re.compile(
        r"\bMRE\s*(\d{3,4}(?:\([a-z0-9]+\))*)", re.IGNORECASE,
    ),
    "usc": re.compile(
        r"\b(\d{1,2})\s*U\.?S\.?C\.?\s*[§]?\s*(\d{1,6})", re.IGNORECASE,
    ),
    "frcp": re.compile(
        r"\b(?:FRCP|Fed\.?\s*R\.?\s*Civ\.?\s*P\.?)\s*(?:Rule\s*)?(\d{1,3}(?:\([a-z0-9]+\))*)",
        re.IGNORECASE,
    ),
    "case_mich": re.compile(
        r"(\d{1,3})\s+Mich(?:\s+App)?\s+(\d{1,4})", re.IGNORECASE,
    ),
    "case_federal": re.compile(
        r"(\d{1,4})\s+F\.(?:2d|3d|4th|Supp(?:\.\s*[23]d)?)\s+(\d{1,4})",
        re.IGNORECASE,
    ),
    "case_us": re.compile(
        r"(\d{1,3})\s+U\.?\s*S\.?\s+(\d{1,4})", re.IGNORECASE,
    ),
    "case_name": re.compile(
        r"([A-Z][A-Za-z'\-]+)\s+v\.\s+([A-Z][A-Za-z'\-]+)", 0,
    ),
}

# ---------------------------------------------------------------------------
# Admissibility keywords (hearsay, authentication, etc.)
# ---------------------------------------------------------------------------

_HEARSAY_INDICATORS = [
    "told me", "he said", "she said", "they said", "informed me",
    "reported that", "according to", "i heard", "i was told",
]

_AUTHENTICATION_INDICATORS = [
    "screenshot", "printout", "certified copy", "original",
    "business record", "public record", "self-authenticating",
    "902", "901", "notarized", "attestation",
]

_IMPEACHMENT_INDICATORS = [
    "inconsistent", "contradiction", "previously stated", "prior statement",
    "lied", "false", "perjury", "changed story", "recanted", "sworn",
]

# ---------------------------------------------------------------------------
# Michigan authority knowledge base (built-in)
# ---------------------------------------------------------------------------

_AUTHORITY_KB: dict[str, list[dict[str, str]]] = {
    "custody": [
        {"citation": "MCL 722.23", "desc": "Best interest of the child factors (a)-(l)"},
        {"citation": "MCL 722.27", "desc": "Court powers to modify custody orders"},
        {"citation": "MCL 722.27a", "desc": "Parenting time presumption and factors"},
        {"citation": "MCR 3.210", "desc": "Custody proceedings — general provisions"},
        {"citation": "MCR 3.211", "desc": "Custody determination procedures"},
    ],
    "protection_order": [
        {"citation": "MCL 600.2950", "desc": "Personal protection orders — domestic"},
        {"citation": "MCL 600.2950a", "desc": "PPO — stalking and harassment"},
        {"citation": "MCR 3.705", "desc": "Personal protection order proceedings"},
        {"citation": "MCR 3.706", "desc": "PPO modification and rescission"},
    ],
    "disqualification": [
        {"citation": "MCR 2.003", "desc": "Disqualification of judges"},
        {"citation": "MCL 600.151", "desc": "Disqualification and assignment of judges"},
        {"citation": "28 USC § 455", "desc": "Federal judicial disqualification"},
        {"citation": "Canon 2", "desc": "Michigan Code of Judicial Conduct — impartiality"},
    ],
    "evidence": [
        {"citation": "MRE 401", "desc": "Relevance — definition"},
        {"citation": "MRE 402", "desc": "Relevance — admissibility"},
        {"citation": "MRE 403", "desc": "Exclusion of relevant evidence (prejudice)"},
        {"citation": "MRE 801", "desc": "Hearsay — definitions"},
        {"citation": "MRE 803", "desc": "Hearsay exceptions — availability immaterial"},
        {"citation": "MRE 901", "desc": "Authentication and identification"},
        {"citation": "MRE 902", "desc": "Self-authentication"},
    ],
    "civil_rights": [
        {"citation": "42 USC § 1983", "desc": "Civil action for deprivation of rights"},
        {"citation": "42 USC § 1985", "desc": "Conspiracy to interfere with civil rights"},
        {"citation": "42 USC § 1988", "desc": "Attorney fees in civil rights cases"},
    ],
    "appeal": [
        {"citation": "MCR 7.204", "desc": "Filing claim of appeal — procedure"},
        {"citation": "MCR 7.205", "desc": "Application for leave to appeal"},
        {"citation": "MCR 7.212", "desc": "Briefs — form and content requirements"},
        {"citation": "MCR 7.215", "desc": "Court of Appeals opinions and orders"},
        {"citation": "MCR 7.305", "desc": "Supreme Court application for leave"},
    ],
    "sanctions": [
        {"citation": "MCR 2.114", "desc": "Signatures and sanctions (Rule 11 equiv)"},
        {"citation": "MCR 2.313", "desc": "Discovery sanctions"},
        {"citation": "MCL 600.2591", "desc": "Frivolous civil actions — costs and fees"},
    ],
}

# ---------------------------------------------------------------------------
# TF-IDF helpers (lightweight, no external deps)
# ---------------------------------------------------------------------------

_STOP_WORDS: frozenset[str] = frozenset(
    "the a an and or but in on of to for is it that this with as at by from "
    "be was were been are have has had do does did will would shall should may "
    "might can could not no its he she they them their his her we our your i "
    "me my you all any each every some such into than too very just about more".split()
)


def _tokenize(text: str) -> list[str]:
    """Lowercase tokenization with stop-word removal."""
    return [
        w for w in re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower())
        if w not in _STOP_WORDS and len(w) > 1
    ]


def _term_freq(tokens: list[str]) -> dict[str, float]:
    """Normalized term frequency."""
    counts = Counter(tokens)
    total = len(tokens) or 1
    return {t: c / total for t, c in counts.items()}


def _idf(term: str, corpus_tfs: Sequence[dict[str, float]]) -> float:
    """Inverse document frequency for *term* across corpus."""
    n = len(corpus_tfs) or 1
    df = sum(1 for tf in corpus_tfs if term in tf)
    return math.log((n + 1) / (df + 1)) + 1.0


def _tfidf_vector(
    tf: dict[str, float],
    corpus_tfs: Sequence[dict[str, float]],
) -> dict[str, float]:
    """TF-IDF vector for a single document."""
    return {t: freq * _idf(t, corpus_tfs) for t, freq in tf.items()}


def _cosine_sim(a: dict[str, float], b: dict[str, float]) -> float:
    """Cosine similarity between two sparse vectors."""
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    mag_a = math.sqrt(sum(v * v for v in a.values())) or 1e-9
    mag_b = math.sqrt(sum(v * v for v in b.values())) or 1e-9
    return dot / (mag_a * mag_b)


# ---------------------------------------------------------------------------
# BM25 scorer (lightweight)
# ---------------------------------------------------------------------------

@dataclass
class _BM25:
    """Lightweight BM25 scorer for evidence ranking."""

    k1: float = 1.5
    b: float = 0.75
    corpus_tokens: list[list[str]] = field(default_factory=list)
    avgdl: float = 0.0
    doc_freqs: dict[str, int] = field(default_factory=dict)
    n_docs: int = 0

    def fit(self, documents: Sequence[str]) -> _BM25:
        """Index a corpus of documents."""
        self.corpus_tokens = [_tokenize(d) for d in documents]
        self.n_docs = len(self.corpus_tokens)
        self.avgdl = (
            sum(len(t) for t in self.corpus_tokens) / max(self.n_docs, 1)
        )
        df: dict[str, int] = {}
        for tokens in self.corpus_tokens:
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1
        self.doc_freqs = df
        return self

    def score(self, query: str, doc_idx: int) -> float:
        """BM25 score for *query* against document at *doc_idx*."""
        q_tokens = _tokenize(query)
        doc_tokens = self.corpus_tokens[doc_idx]
        doc_len = len(doc_tokens)
        tf_doc = Counter(doc_tokens)
        score = 0.0
        for term in q_tokens:
            if term not in tf_doc:
                continue
            f = tf_doc[term]
            df = self.doc_freqs.get(term, 0)
            idf_val = math.log((self.n_docs - df + 0.5) / (df + 0.5) + 1.0)
            numerator = f * (self.k1 + 1)
            denominator = f + self.k1 * (1 - self.b + self.b * doc_len / max(self.avgdl, 1e-9))
            score += idf_val * numerator / denominator
        return score

    def rank(self, query: str) -> list[tuple[int, float]]:
        """Rank all documents by descending BM25 score."""
        scores = [
            (i, self.score(query, i)) for i in range(self.n_docs)
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores


# ---------------------------------------------------------------------------
# LegalAIBrain — the unified inference router
# ---------------------------------------------------------------------------

class LegalAIBrain:
    """MANBEARPIG v10 — offline legal AI inference engine.

    Provides document classification, entity extraction, evidence scoring,
    lane detection, citation parsing, authority suggestions, and argument
    drafting.  All inference is local — no network calls, no API keys.

    Parameters
    ----------
    db : DatabaseManager, optional
        If provided, enables FTS5 authority search against the litigation DB.
    """

    VERSION = "10.0.0"

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self._db = db
        # Pre-compile lane regex patterns for fast detection
        self._lane_patterns: dict[str, re.Pattern[str]] = {
            lane_id: re.compile(
                "|".join(re.escape(k) for k in info["keywords"]),
                re.IGNORECASE,
            )
            for lane_id, info in CASE_LANES.items()
        }
        # Build TF-IDF corpus for document-type classification
        self._doc_corpus_tfs: list[dict[str, float]] = []
        self._doc_corpus_labels: list[str] = []
        for label, keywords in DOCUMENT_TYPES.items():
            tokens = _tokenize(" ".join(keywords))
            self._doc_corpus_tfs.append(_term_freq(tokens))
            self._doc_corpus_labels.append(label)

        logger.info("LegalAIBrain v%s initialised (db=%s)", self.VERSION, db is not None)

    # -- Document classification -----------------------------------------------

    def classify_document(self, text: str) -> ClassificationResult:
        """Classify *text* into a document type using TF-IDF similarity.

        Returns the best-match type with confidence and runner-up.
        """
        if not text or not text.strip():
            return ClassificationResult(doc_type="unknown", confidence=0.0)

        input_tf = _term_freq(_tokenize(text[:5000]))
        input_vec = _tfidf_vector(input_tf, self._doc_corpus_tfs)

        scores: list[tuple[str, float]] = []
        for i, corpus_tf in enumerate(self._doc_corpus_tfs):
            vec = _tfidf_vector(corpus_tf, self._doc_corpus_tfs)
            sim = _cosine_sim(input_vec, vec)
            scores.append((self._doc_corpus_labels[i], sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        best_label, best_score = scores[0]
        runner_up = scores[1][0] if len(scores) > 1 else None

        confidence = min(best_score, 1.0)
        logger.debug("classify_document → %s (%.3f)", best_label, confidence)
        return ClassificationResult(
            doc_type=best_label,
            confidence=round(confidence, 4),
            runner_up=runner_up,
        )

    # -- Entity extraction -----------------------------------------------------

    _ENTITY_PATTERNS: dict[str, re.Pattern[str]] = {
        "case_number": re.compile(
            r"\b(\d{4}[\-–]\d{4,7}[\-–][A-Z]{2,3})\b"
            r"|\b(Case\s+No\.?\s*[\d\-–]+)",
            re.IGNORECASE,
        ),
        "date": re.compile(
            r"\b(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})\b"
            r"|\b((?:January|February|March|April|May|June|July|August"
            r"|September|October|November|December)\s+\d{1,2},?\s*\d{4})\b",
            re.IGNORECASE,
        ),
        "amount": re.compile(
            r"\$\s?([\d,]+(?:\.\d{2})?)", 0,
        ),
        "judge": re.compile(
            r"(?:Judge|Hon\.|Honorable|Justice)\s+"
            r"([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,2})",
            0,
        ),
        "party": re.compile(
            r"(?:Plaintiff|Defendant|Petitioner|Respondent|Appellant|Appellee)"
            r"\s+([A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z'\-]+){0,2})",
            0,
        ),
    }

    def extract_entities(self, text: str) -> list[ExtractedEntity]:
        """Extract legal entities (parties, judges, dates, amounts, case numbers)."""
        entities: list[ExtractedEntity] = []
        if not text:
            return entities

        for entity_type, pattern in self._ENTITY_PATTERNS.items():
            for match in pattern.finditer(text[:10000]):
                value = next((g for g in match.groups() if g is not None), match.group(0))
                entities.append(ExtractedEntity(
                    entity_type=entity_type,
                    value=value.strip(),
                    span_start=match.start(),
                    span_end=match.end(),
                ))

        logger.debug("extract_entities → %d entities found", len(entities))
        return entities

    # -- Evidence scoring ------------------------------------------------------

    def score_evidence(self, text: str, claim: str) -> EvidenceScore:
        """Score evidence *text* for relevance and quality against *claim*.

        Returns a composite 0-100 score factoring in relevance, admissibility,
        and impeachment value.
        """
        if not text or not claim:
            return EvidenceScore(
                relevance=0, admissibility=0, impeachment=0, composite=0,
                factors=["Insufficient text or claim"],
            )

        factors: list[str] = []
        text_lower = text.lower()

        # --- Relevance (TF-IDF cosine similarity, scaled to 0-100) ---
        claim_tokens = _tokenize(claim)
        text_tokens = _tokenize(text[:8000])
        claim_tf = _term_freq(claim_tokens)
        text_tf = _term_freq(text_tokens)
        corpus = [claim_tf, text_tf]
        claim_vec = _tfidf_vector(claim_tf, corpus)
        text_vec = _tfidf_vector(text_tf, corpus)
        relevance_raw = _cosine_sim(claim_vec, text_vec) * 100
        # Boost if many claim keywords appear directly
        keyword_hits = sum(1 for t in claim_tokens if t in text_lower)
        keyword_boost = min(keyword_hits * 5, 25)
        relevance = min(relevance_raw + keyword_boost, 100.0)
        factors.append(f"Keyword overlap: {keyword_hits}/{len(claim_tokens)} terms")

        # --- Admissibility (hearsay / authentication heuristic) ---
        hearsay_count = sum(1 for h in _HEARSAY_INDICATORS if h in text_lower)
        auth_count = sum(1 for a in _AUTHENTICATION_INDICATORS if a in text_lower)
        admissibility = 70.0  # baseline
        admissibility -= hearsay_count * 10
        admissibility += auth_count * 8
        admissibility = max(0.0, min(admissibility, 100.0))
        if hearsay_count:
            factors.append(f"Hearsay indicators: {hearsay_count}")
        if auth_count:
            factors.append(f"Authentication indicators: {auth_count}")

        # --- Impeachment value ---
        imp_count = sum(1 for imp in _IMPEACHMENT_INDICATORS if imp in text_lower)
        impeachment = min(imp_count * 15, 100.0)
        if imp_count:
            factors.append(f"Impeachment indicators: {imp_count}")

        # --- Composite (weighted) ---
        composite = (relevance * 0.50) + (admissibility * 0.30) + (impeachment * 0.20)
        composite = round(min(composite, 100.0), 2)

        logger.debug(
            "score_evidence → composite=%.1f (rel=%.1f, adm=%.1f, imp=%.1f)",
            composite, relevance, admissibility, impeachment,
        )
        return EvidenceScore(
            relevance=round(relevance, 2),
            admissibility=round(admissibility, 2),
            impeachment=round(impeachment, 2),
            composite=composite,
            factors=factors,
        )

    # -- Lane detection --------------------------------------------------------

    def detect_lane(self, text: str) -> LaneDetection:
        """Detect which case lane (A-F) *text* belongs to.

        Uses risk-ordered priority: E → D → F → C → A → B.
        """
        if not text:
            return LaneDetection(lane="A", lane_name="Custody", confidence=0.0)

        text_lower = text.lower()
        best_lane = "A"
        best_score = 0
        best_signals: list[str] = []

        for lane_id in LANE_PRIORITY:
            info = CASE_LANES[lane_id]
            matches = [kw for kw in info["keywords"] if kw in text_lower]
            score = len(matches)
            if score > best_score:
                best_score = score
                best_lane = lane_id
                best_signals = matches

        total_kw = max(len(CASE_LANES[best_lane]["keywords"]), 1)
        confidence = min(best_score / total_kw, 1.0)

        logger.debug("detect_lane → %s (%s, %.3f)", best_lane, CASE_LANES[best_lane]["name"], confidence)
        return LaneDetection(
            lane=best_lane,
            lane_name=CASE_LANES[best_lane]["name"],
            confidence=round(confidence, 4),
            signals=best_signals,
        )

    # -- Summarization ---------------------------------------------------------

    def summarize(self, text: str, max_words: int = 100) -> str:
        """Generate a concise extractive summary of *text*.

        Ranks sentences by keyword density and selects the top ones up to
        *max_words*.
        """
        if not text or not text.strip():
            return ""

        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        if not sentences:
            return ""

        all_tokens = _tokenize(text)
        freq = Counter(all_tokens)

        scored: list[tuple[float, str]] = []
        for sent in sentences:
            tokens = _tokenize(sent)
            if not tokens:
                continue
            sent_score = sum(freq.get(t, 0) for t in tokens) / len(tokens)
            scored.append((sent_score, sent))

        scored.sort(key=lambda x: x[0], reverse=True)

        summary_parts: list[str] = []
        word_count = 0
        for _, sent in scored:
            words_in_sent = len(sent.split())
            if word_count + words_in_sent > max_words:
                break
            summary_parts.append(sent)
            word_count += words_in_sent

        # Restore original order
        ordered = [s for _, s in scored if s in summary_parts]
        for sent in sentences:
            if sent in summary_parts and sent not in ordered:
                ordered.append(sent)

        result = " ".join(summary_parts)
        logger.debug("summarize → %d words", len(result.split()))
        return result

    # -- Citation extraction & validation --------------------------------------

    def find_citations(self, text: str) -> list[Citation]:
        """Extract all legal citations from *text*."""
        citations: list[Citation] = []
        if not text:
            return citations

        seen: set[str] = set()

        for ctype, pattern in _CITATION_PATTERNS.items():
            for match in pattern.finditer(text):
                raw = match.group(0).strip()
                if raw in seen:
                    continue
                seen.add(raw)

                normalized = self._normalize_citation(raw, ctype)
                citations.append(Citation(
                    raw=raw,
                    citation_type=ctype,
                    normalized=normalized,
                    valid=True,
                ))

        logger.debug("find_citations → %d citations", len(citations))
        return citations

    @staticmethod
    def _normalize_citation(raw: str, ctype: str) -> str:
        """Normalize a citation to a canonical form."""
        text = re.sub(r"\s+", " ", raw.strip())
        if ctype == "mcr":
            return re.sub(r"(?i)\bmcr\b", "MCR", text)
        if ctype == "mcl":
            return re.sub(r"(?i)\bmcl\b", "MCL", text)
        if ctype == "mre":
            return re.sub(r"(?i)\bmre\b", "MRE", text)
        if ctype == "usc":
            return text.replace("U.S.C", "USC").replace("U.S.C.", "USC")
        return text

    def check_citation_format(self, citation: str) -> Citation:
        """Validate a single citation string and suggest fixes."""
        citation = citation.strip()
        if not citation:
            return Citation(
                raw=citation, citation_type="unknown", valid=False,
                fix_suggestion="Empty citation",
            )

        for ctype, pattern in _CITATION_PATTERNS.items():
            if pattern.search(citation):
                normalized = self._normalize_citation(citation, ctype)
                fix = None if normalized == citation else normalized
                return Citation(
                    raw=citation,
                    citation_type=ctype,
                    normalized=normalized,
                    valid=True,
                    fix_suggestion=fix,
                )

        # Not matched — attempt fuzzy suggestion
        fix = None
        lower = citation.lower()
        if "mcr" in lower or "court rule" in lower:
            fix = "Format as: MCR X.XXX (e.g., MCR 2.003)"
        elif "mcl" in lower or "compiled law" in lower:
            fix = "Format as: MCL XXX.XX (e.g., MCL 722.23)"
        elif "mre" in lower or "evidence" in lower:
            fix = "Format as: MRE XXX (e.g., MRE 803)"
        elif "usc" in lower:
            fix = "Format as: XX USC § XXXX (e.g., 42 USC § 1983)"

        return Citation(
            raw=citation,
            citation_type="unknown",
            valid=False,
            fix_suggestion=fix or "Unrecognised citation format",
        )

    # -- Authority suggestion --------------------------------------------------

    def suggest_authority(
        self,
        claim_type: str,
        jurisdiction: str = "MI",
    ) -> list[AuthoritySuggestion]:
        """Suggest relevant legal authorities for a claim type.

        Uses the built-in Michigan knowledge base, with optional FTS5
        search if a database is connected.
        """
        suggestions: list[AuthoritySuggestion] = []
        claim_lower = claim_type.lower()

        # Search the built-in KB
        for category, authorities in _AUTHORITY_KB.items():
            if category in claim_lower or claim_lower in category:
                for auth in authorities:
                    suggestions.append(AuthoritySuggestion(
                        citation=auth["citation"],
                        relevance=0.9,
                        description=auth["desc"],
                    ))

        # Keyword fallback: scan all categories for partial matches
        if not suggestions:
            claim_tokens = set(_tokenize(claim_type))
            for category, authorities in _AUTHORITY_KB.items():
                cat_tokens = set(_tokenize(category))
                overlap = claim_tokens & cat_tokens
                if overlap:
                    for auth in authorities:
                        suggestions.append(AuthoritySuggestion(
                            citation=auth["citation"],
                            relevance=round(len(overlap) / max(len(claim_tokens), 1), 2),
                            description=auth["desc"],
                        ))

        # FTS5 database search if available
        if self._db and not suggestions:
            suggestions.extend(self._search_authorities_db(claim_type))

        suggestions.sort(key=lambda s: s.relevance, reverse=True)
        logger.debug("suggest_authority(%s) → %d results", claim_type, len(suggestions))
        return suggestions

    def _search_authorities_db(self, query: str) -> list[AuthoritySuggestion]:
        """Search the litigation DB for authorities via FTS5."""
        results: list[AuthoritySuggestion] = []
        if not self._db:
            return results
        try:
            conn = self._db.connect()
            try:
                rows = conn.execute(
                    "SELECT citation, description, rank "
                    "FROM authority_index WHERE authority_index MATCH ? "
                    "ORDER BY rank LIMIT 10",
                    (query,),
                ).fetchall()
                for row in rows:
                    results.append(AuthoritySuggestion(
                        citation=row["citation"],
                        relevance=min(abs(row["rank"]) / 10, 1.0),
                        description=row["description"],
                    ))
            finally:
                conn.close()
        except Exception:
            logger.debug("FTS5 authority search unavailable", exc_info=True)
        return results

    # -- Search authorities (public API for DB queries) ------------------------

    def search_authorities(self, query: str) -> list[AuthoritySuggestion]:
        """Search for authorities matching *query*.

        Combines built-in KB with FTS5 database search when available.
        """
        # Built-in search via keyword overlap
        results: list[AuthoritySuggestion] = []
        query_tokens = set(_tokenize(query))

        for category, authorities in _AUTHORITY_KB.items():
            for auth in authorities:
                combined = category + " " + auth["desc"]
                auth_tokens = set(_tokenize(combined))
                overlap = query_tokens & auth_tokens
                if overlap:
                    relevance = len(overlap) / max(len(query_tokens), 1)
                    results.append(AuthoritySuggestion(
                        citation=auth["citation"],
                        relevance=round(min(relevance, 1.0), 2),
                        description=auth["desc"],
                    ))

        # Augment with DB search
        results.extend(self._search_authorities_db(query))

        # Deduplicate by citation
        seen: set[str] = set()
        deduped: list[AuthoritySuggestion] = []
        for r in sorted(results, key=lambda x: x.relevance, reverse=True):
            if r.citation not in seen:
                seen.add(r.citation)
                deduped.append(r)

        return deduped

    # -- Strength assessment ---------------------------------------------------

    def assess_strength(
        self,
        claim: str,
        evidence_list: Sequence[str],
    ) -> StrengthAssessment:
        """Assess claim strength given a list of evidence texts.

        Returns a 0-100 score with letter grade and reasoning.
        """
        if not claim:
            return StrengthAssessment(
                score=0, grade="F",
                reasoning=["No claim provided"],
                weaknesses=["Claim text is empty"],
            )

        reasoning: list[str] = []
        weaknesses: list[str] = []

        # Score each piece of evidence
        evidence_scores: list[float] = []
        for ev_text in evidence_list:
            ev_score = self.score_evidence(ev_text, claim)
            evidence_scores.append(ev_score.composite)

        # Factor 1: Evidence coverage (0-40 points)
        if not evidence_scores:
            coverage_score = 0.0
            weaknesses.append("No supporting evidence provided")
        else:
            avg_score = sum(evidence_scores) / len(evidence_scores)
            coverage_score = (avg_score / 100) * 40
            reasoning.append(
                f"Average evidence score: {avg_score:.1f}/100 "
                f"across {len(evidence_scores)} items"
            )
            if avg_score < 30:
                weaknesses.append("Evidence relevance is weak")

        # Factor 2: Evidence quantity (0-20 points)
        qty_score = min(len(evidence_scores) * 5, 20.0)
        reasoning.append(f"Evidence quantity: {len(evidence_scores)} items")
        if len(evidence_scores) < 3:
            weaknesses.append("Insufficient quantity of evidence (need 3+)")

        # Factor 3: Citation support (0-20 points)
        claim_citations = self.find_citations(claim)
        cit_score = min(len(claim_citations) * 7, 20.0)
        if claim_citations:
            reasoning.append(f"Legal citations in claim: {len(claim_citations)}")
        else:
            weaknesses.append("No legal citations in claim text")

        # Factor 4: Claim specificity (0-20 points)
        claim_entities = self.extract_entities(claim)
        spec_score = min(len(claim_entities) * 4, 20.0)
        if claim_entities:
            reasoning.append(f"Claim specificity: {len(claim_entities)} entities identified")
        else:
            weaknesses.append("Claim lacks specific dates, amounts, or party names")

        total = coverage_score + qty_score + cit_score + spec_score
        total = round(min(total, 100.0), 2)

        # Letter grade
        if total >= 90:
            grade = "A"
        elif total >= 80:
            grade = "B"
        elif total >= 70:
            grade = "C"
        elif total >= 60:
            grade = "D"
        else:
            grade = "F"

        logger.debug("assess_strength → %.1f (%s)", total, grade)
        return StrengthAssessment(
            score=total,
            grade=grade,
            reasoning=reasoning,
            weaknesses=weaknesses,
        )

    # -- Argument drafting -----------------------------------------------------

    def draft_argument(
        self,
        claim: str,
        evidence: Sequence[str],
        authorities: Sequence[str] | None = None,
    ) -> str:
        """Draft an argument paragraph for a claim.

        Combines claim statement, evidence highlights, and legal authority
        citations into a structured argument.  This is a template-based
        drafter — not a generative LLM.
        """
        if not claim:
            return ""

        parts: list[str] = []

        # Opening assertion
        parts.append(f"The evidence establishes that {claim.rstrip('.')}.")

        # Evidence support
        if evidence:
            parts.append(
                f"This is supported by {len(evidence)} item(s) of evidence."
            )
            # Pull best evidence snippet (first sentence of highest-scored)
            scored = []
            for ev in evidence:
                sc = self.score_evidence(ev, claim)
                first_sent = re.split(r'[.!?]', ev[:500])[0].strip()
                scored.append((sc.composite, first_sent))
            scored.sort(key=lambda x: x[0], reverse=True)
            top = scored[:3]
            for _, snippet in top:
                if snippet:
                    parts.append(f'Specifically, "{snippet}."')

        # Legal authority
        if authorities:
            auth_str = "; ".join(authorities)
            parts.append(f"This claim is supported by {auth_str}.")
        else:
            suggestions = self.suggest_authority(claim)
            if suggestions:
                auto_auth = "; ".join(s.citation for s in suggestions[:3])
                parts.append(f"See {auto_auth}.")

        # Closing
        parts.append("Accordingly, the claim is meritorious and should be sustained.")

        result = " ".join(parts)
        logger.debug("draft_argument → %d chars", len(result))
        return result

    # -- Rule and deadline helpers (delegate to DB if available) ----------------

    def get_rule(self, rule_number: str) -> Optional[dict[str, str]]:
        """Look up a court rule by number (e.g., '2.003').

        Returns dict with 'number', 'title', 'text' if found, else None.
        """
        if not self._db:
            return None
        try:
            conn = self._db.connect()
            try:
                row = conn.execute(
                    "SELECT rule_number, title, full_text FROM court_rules "
                    "WHERE rule_number = ? LIMIT 1",
                    (rule_number,),
                ).fetchone()
                if row:
                    return {
                        "number": row["rule_number"],
                        "title": row["title"],
                        "text": row["full_text"],
                    }
            finally:
                conn.close()
        except Exception:
            logger.debug("get_rule(%s) — DB lookup failed", rule_number, exc_info=True)
        return None

    def get_deadline_rule(self, filing_type: str) -> Optional[dict[str, Any]]:
        """Look up deadline rules for a filing type.

        Returns dict with 'days', 'rule_basis', 'description' if found.
        """
        if not self._db:
            return None
        try:
            conn = self._db.connect()
            try:
                row = conn.execute(
                    "SELECT days, rule_basis, description FROM deadline_rules "
                    "WHERE filing_type = ? LIMIT 1",
                    (filing_type,),
                ).fetchone()
                if row:
                    return dict(row)
            finally:
                conn.close()
        except Exception:
            logger.debug("get_deadline_rule(%s) — DB lookup failed", filing_type, exc_info=True)
        return None

    # -- Repr / debug ----------------------------------------------------------

    def __repr__(self) -> str:
        return f"<LegalAIBrain v{self.VERSION} db={self._db is not None}>"
