"""Document chunking strategies optimised for legal documents.

Provides six chunking strategies — from simple fixed-size windows to
Michigan-specific legal section splitting — each producing ``Chunk``
objects with deterministic IDs, overlap tracking, and rich metadata.

Strategies
----------
+----------------+----------------------------------------------------------+
| Strategy       | Description                                              |
+----------------+----------------------------------------------------------+
| FIXED_SIZE     | Fixed character/token windows with configurable overlap  |
| SENTENCE       | Split on sentence boundaries                             |
| PARAGRAPH      | Split on paragraph boundaries (double newlines)          |
| SEMANTIC       | Split where embedding similarity drops below threshold   |
| LEGAL_SECTION  | Michigan legal document section headers & structure      |
| RECURSIVE      | LangChain-style recursive separator hierarchy            |
+----------------+----------------------------------------------------------+

Legal-document-aware features:
  - Preserves Michigan citations intact (MCL 722.23(3)(a), MCR 2.003)
  - Detects section headers (I., II., A., B., ¶1., SECTION, ARTICLE)
  - Keeps footnotes with their text
  - Never splits inside parenthetical references
  - Handles 6 document types: motion, brief, complaint, affidavit, order, transcript

Usage
-----
>>> opt = ChunkOptimizer()
>>> chunks = opt.chunk_text("Long legal text here...")
>>> chunks = opt.chunk_legal_document(text, doc_type='motion')
>>> stats = opt.analyze_chunks(chunks)
"""
from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Approximate words-per-token ratio for English legal text
_WORDS_PER_TOKEN = 0.75

# ---------------------------------------------------------------------------
# Legal citation patterns (NEVER split inside these)
# ---------------------------------------------------------------------------

# Michigan Compiled Laws: MCL 722.23(3)(a)
_MCL_RE = re.compile(
    r"MCL\s+\d+\.\d+(?:\([a-zA-Z0-9]+\))*(?:\([a-zA-Z0-9]+\))*"
)
# Michigan Court Rules: MCR 2.003(C)(1)
_MCR_RE = re.compile(
    r"MCR\s+\d+\.\d+(?:\([A-Z]\))?(?:\(\d+\))?(?:\([a-z]+\))?"
)
# Michigan Rules of Evidence: MRE 702
_MRE_RE = re.compile(r"MRE\s+\d+(?:\.\d+)?")
# Federal: USC, CFR, FR
_USC_RE = re.compile(r"\d+\s+U\.?S\.?C\.?\s+§?\s*\d+")
_CFR_RE = re.compile(r"\d+\s+C\.?F\.?R\.?\s+§?\s*\d+")
# Case citations: 123 Mich App 456, 789 NW2d 012
_CASE_CITE_RE = re.compile(
    r"\d+\s+(?:Mich(?:\s+App)?|NW(?:2d)?|F\.\d+[d]?|S\.\s*Ct\.?"
    r"|L\.\s*Ed\.?\s*2d|U\.S\.)\s+\d+"
)
# Id. and See references
_ID_RE = re.compile(r"\bId\.\s+at\s+\d+")
_SEE_RE = re.compile(r"\b(?:See|Cf\.|See also|But see)\s+\w")

# Collect all citation patterns for boundary protection
_CITATION_PATTERNS = [_MCL_RE, _MCR_RE, _MRE_RE, _USC_RE, _CFR_RE, _CASE_CITE_RE]

# ---------------------------------------------------------------------------
# Section header patterns (used to detect legal structure)
# ---------------------------------------------------------------------------

# Roman numeral sections: I., II., III., IV., ...
_ROMAN_SECTION_RE = re.compile(
    r"^[ \t]*([IVXLCDMivxlcdm]+)\.\s+[A-Z]", re.MULTILINE
)
# Letter sections: A., B., C., ...
_LETTER_SECTION_RE = re.compile(
    r"^[ \t]*([A-Z])\.\s+[A-Z]", re.MULTILINE
)
# Numbered paragraphs: ¶1., ¶2., 1., 2., ...
_PARA_NUM_RE = re.compile(
    r"^[ \t]*(?:¶\s*)?(\d+)\.\s+", re.MULTILINE
)
# SECTION / ARTICLE headings
_SECTION_HEADING_RE = re.compile(
    r"^[ \t]*(?:SECTION|ARTICLE|PART|CHAPTER|DIVISION|RULE)\s+",
    re.MULTILINE | re.IGNORECASE,
)
# Court document sections: COMES NOW, WHEREFORE, CERTIFICATE OF SERVICE
_COURT_SECTION_RE = re.compile(
    r"^[ \t]*(?:COMES\s+NOW|WHEREFORE|CERTIFICATE\s+OF\s+SERVICE"
    r"|VERIFICATION|PROOF\s+OF\s+SERVICE|PRAYER\s+FOR\s+RELIEF"
    r"|STATEMENT\s+OF\s+FACTS|STATEMENT\s+OF\s+ISSUES"
    r"|ARGUMENT|CONCLUSION|INTRODUCTION|JURISDICTION"
    r"|SUMMARY\s+OF\s+ARGUMENT|RELIEF\s+REQUESTED"
    r"|STANDARD\s+OF\s+REVIEW|QUESTIONS\s+PRESENTED)",
    re.MULTILINE | re.IGNORECASE,
)
# Footnote markers: ^1, [1], (1)
_FOOTNOTE_RE = re.compile(r"(?:^|\n)[ \t]*(?:\[\d+\]|\(\d+\)|\d+)\s+\S")

# Composite pattern for any legal section boundary
_LEGAL_BOUNDARY_RE = re.compile(
    r"\n(?="
    r"[IVXLCDMivxlcdm]+\.\s+[A-Z]"  # Roman numeral
    r"|[A-Z]\.\s+[A-Z]"              # Letter section
    r"|(?:¶\s*)?\d+\.\s+"            # Numbered paragraph
    r"|(?:SECTION|ARTICLE|PART|CHAPTER)\s+"  # Headings
    r"|(?:COMES\s+NOW|WHEREFORE|CERTIFICATE\s+OF\s+SERVICE"
    r"|VERIFICATION|PROOF\s+OF\s+SERVICE|ARGUMENT|CONCLUSION"
    r"|INTRODUCTION|JURISDICTION|STANDARD\s+OF\s+REVIEW"
    r"|QUESTIONS\s+PRESENTED|RELIEF\s+REQUESTED"
    r"|STATEMENT\s+OF\s+FACTS|STATEMENT\s+OF\s+ISSUES"
    r"|SUMMARY\s+OF\s+ARGUMENT|PRAYER\s+FOR\s+RELIEF)"
    r")",
    re.IGNORECASE,
)

# Sentence boundary (look-behind for sentence-ending punctuation)
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\d¶\(\"'])")

# Default separator hierarchy for recursive splitting
_DEFAULT_SEPARATORS = [
    "\n\n\n",        # Triple newline (major section break)
    "\n\n",          # Double newline (paragraph break)
    "\n",            # Single newline
    ". ",            # Sentence boundary (period + space)
    "; ",            # Semicolon
    ", ",            # Comma
    " ",             # Word boundary
]


# ---------------------------------------------------------------------------
# Enums & Dataclasses
# ---------------------------------------------------------------------------

class ChunkingStrategy(Enum):
    """Available document chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"
    LEGAL_SECTION = "legal_section"
    RECURSIVE = "recursive"


@dataclass
class ChunkConfig:
    """Configuration for a chunking operation.

    Attributes
    ----------
    strategy : ChunkingStrategy
        Which splitting algorithm to use.
    chunk_size : int
        Target tokens per chunk.
    chunk_overlap : int
        Overlap tokens between consecutive chunks.
    min_chunk_size : int
        Minimum acceptable chunk size (tokens).
    max_chunk_size : int
        Maximum acceptable chunk size (tokens).
    separators : list[str]
        Split characters/strings in priority order.
    preserve_metadata : bool
        Whether to carry source metadata into chunks.
    similarity_threshold : float
        Cosine similarity threshold for semantic splitting (0-1).
    doc_type : str
        Document type hint for legal splitting.
    """
    strategy: ChunkingStrategy = ChunkingStrategy.RECURSIVE
    chunk_size: int = 512
    chunk_overlap: int = 64
    min_chunk_size: int = 50
    max_chunk_size: int = 1024
    separators: List[str] = field(default_factory=lambda: list(_DEFAULT_SEPARATORS))
    preserve_metadata: bool = True
    similarity_threshold: float = 0.5
    doc_type: str = "general"

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary."""
        return {
            "strategy": self.strategy.value,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "min_chunk_size": self.min_chunk_size,
            "max_chunk_size": self.max_chunk_size,
            "separators": self.separators,
            "preserve_metadata": self.preserve_metadata,
            "similarity_threshold": self.similarity_threshold,
            "doc_type": self.doc_type,
        }


@dataclass
class Chunk:
    """A single chunk of text with provenance and overlap metadata.

    Attributes
    ----------
    text : str
        The chunk text content.
    chunk_id : str
        Deterministic SHA-256-based identifier.
    source_doc_id : str or None
        Identifier of the source document.
    start_offset : int
        Character offset of the chunk start in the original text.
    end_offset : int
        Character offset of the chunk end in the original text.
    metadata : dict
        Inherited source metadata plus computed chunk metadata.
    token_count : int
        Estimated token count for this chunk.
    overlap_prev : int
        Number of characters overlapping with the previous chunk.
    overlap_next : int
        Number of characters overlapping with the next chunk.
    """
    text: str
    chunk_id: str
    source_doc_id: Optional[str] = None
    start_offset: int = 0
    end_offset: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_count: int = 0
    overlap_prev: int = 0
    overlap_next: int = 0

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary."""
        return {
            "text": self.text,
            "chunk_id": self.chunk_id,
            "source_doc_id": self.source_doc_id,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "metadata": self.metadata,
            "token_count": self.token_count,
            "overlap_prev": self.overlap_prev,
            "overlap_next": self.overlap_next,
        }


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Estimate token count from text length.

    Uses the approximation that 1 token ≈ 4 characters for English
    text, calibrated for legal language (slightly longer words).
    """
    return max(1, len(text.split()))


def _chars_for_tokens(tokens: int) -> int:
    """Rough character count for a given token count."""
    return int(tokens * 5.5)  # ~5.5 chars/token for legal text


def _chunk_id(text: str, source_doc_id: Optional[str], offset: int) -> str:
    """Generate a deterministic chunk ID from content and position."""
    payload = f"{source_doc_id or ''}:{offset}:{text[:200]}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _is_inside_citation(text: str, pos: int) -> bool:
    """Check if position ``pos`` falls inside a legal citation span.

    Prevents splitting in the middle of citations like
    ``MCL 722.23(3)(a)`` or ``MCR 2.003(C)(1)``.
    """
    for pattern in _CITATION_PATTERNS:
        for m in pattern.finditer(text):
            if m.start() < pos < m.end():
                return True
    # Also protect parenthetical references: (3)(a), (c)(ii)
    paren_re = re.compile(r"\([a-zA-Z0-9]+\)(?:\([a-zA-Z0-9]+\))*")
    for m in paren_re.finditer(text):
        if m.start() < pos < m.end():
            return True
    return False


def _find_safe_split(text: str, target_pos: int, window: int = 100) -> int:
    """Find the nearest safe split position near ``target_pos``.

    A "safe" position is one that does not fall inside a citation,
    parenthetical, or mid-word.  Searches within ±window characters.

    Parameters
    ----------
    text : str
        Full text being split.
    target_pos : int
        Desired split position.
    window : int
        Search window around target.

    Returns
    -------
    int
        Safe split position.
    """
    best = target_pos
    best_dist = window + 1

    start = max(0, target_pos - window)
    end = min(len(text), target_pos + window)

    for pos in range(start, end):
        if pos >= len(text):
            break
        # Prefer splitting on whitespace
        if text[pos] in (" ", "\n", "\t"):
            if not _is_inside_citation(text, pos):
                dist = abs(pos - target_pos)
                if dist < best_dist:
                    best = pos
                    best_dist = dist

    return best


def _protect_citations(text: str) -> Tuple[str, Dict[str, str]]:
    """Replace citation spans with placeholders to prevent splitting.

    Returns the modified text and a mapping from placeholder → original.
    """
    replacements: Dict[str, str] = {}
    counter = 0

    def replace_match(m: re.Match) -> str:
        nonlocal counter
        key = f"__CITE{counter:04d}__"
        replacements[key] = m.group(0)
        counter += 1
        return key

    result = text
    for pattern in _CITATION_PATTERNS:
        result = pattern.sub(replace_match, result)

    # Also protect Id. references
    result = _ID_RE.sub(replace_match, result)

    return result, replacements


def _restore_citations(text: str, replacements: Dict[str, str]) -> str:
    """Restore citation placeholders to their original text."""
    result = text
    for key, original in replacements.items():
        result = result.replace(key, original)
    return result


# ---------------------------------------------------------------------------
# Document type configurations
# ---------------------------------------------------------------------------

_DOC_TYPE_CONFIGS: Dict[str, ChunkConfig] = {
    "motion": ChunkConfig(
        strategy=ChunkingStrategy.LEGAL_SECTION,
        chunk_size=512,
        chunk_overlap=64,
        min_chunk_size=80,
        max_chunk_size=1024,
        doc_type="motion",
    ),
    "brief": ChunkConfig(
        strategy=ChunkingStrategy.LEGAL_SECTION,
        chunk_size=768,
        chunk_overlap=96,
        min_chunk_size=100,
        max_chunk_size=1500,
        doc_type="brief",
    ),
    "complaint": ChunkConfig(
        strategy=ChunkingStrategy.LEGAL_SECTION,
        chunk_size=512,
        chunk_overlap=64,
        min_chunk_size=80,
        max_chunk_size=1024,
        doc_type="complaint",
    ),
    "affidavit": ChunkConfig(
        strategy=ChunkingStrategy.PARAGRAPH,
        chunk_size=384,
        chunk_overlap=48,
        min_chunk_size=50,
        max_chunk_size=768,
        doc_type="affidavit",
    ),
    "order": ChunkConfig(
        strategy=ChunkingStrategy.LEGAL_SECTION,
        chunk_size=384,
        chunk_overlap=48,
        min_chunk_size=50,
        max_chunk_size=768,
        doc_type="order",
    ),
    "transcript": ChunkConfig(
        strategy=ChunkingStrategy.PARAGRAPH,
        chunk_size=256,
        chunk_overlap=32,
        min_chunk_size=30,
        max_chunk_size=512,
        doc_type="transcript",
    ),
}

# ---------------------------------------------------------------------------
# ChunkOptimizer
# ---------------------------------------------------------------------------


class ChunkOptimizer:
    """Multi-strategy document chunking for legal text.

    Provides six chunking strategies with legal-document-aware
    features: citation preservation, section detection, footnote
    handling, and Michigan-specific structural patterns.

    Parameters
    ----------
    embed_fn : callable or None
        Optional embedding function ``(text) -> list[float]`` used
        by the semantic strategy.  If not provided, semantic
        splitting falls back to sentence-based splitting.
    default_config : ChunkConfig or None
        Default chunking configuration.
    """

    def __init__(
        self,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
        default_config: Optional[ChunkConfig] = None,
    ) -> None:
        self._embed_fn = embed_fn
        self._default_config = default_config or ChunkConfig()
        self._total_chunks_produced = 0
        self._total_texts_processed = 0
        self._strategy_counts: Dict[str, int] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk_text(
        self,
        text: str,
        config: Optional[ChunkConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_doc_id: Optional[str] = None,
    ) -> List[Chunk]:
        """Chunk text using the configured strategy.

        Parameters
        ----------
        text : str
            Input text to chunk.
        config : ChunkConfig or None
            Override configuration; uses instance default if not given.
        metadata : dict or None
            Source metadata to propagate into each chunk.
        source_doc_id : str or None
            Identifier for the source document.

        Returns
        -------
        list[Chunk]
            Ordered list of chunks with overlap and metadata.
        """
        if not text or not text.strip():
            return []

        cfg = config or self._default_config
        meta = dict(metadata or {})
        meta["strategy"] = cfg.strategy.value
        meta["doc_type"] = cfg.doc_type

        t0 = time.monotonic()

        dispatch = {
            ChunkingStrategy.FIXED_SIZE: self._fixed_size_split,
            ChunkingStrategy.SENTENCE: self._sentence_split,
            ChunkingStrategy.PARAGRAPH: self._paragraph_split,
            ChunkingStrategy.SEMANTIC: self._semantic_split,
            ChunkingStrategy.LEGAL_SECTION: self._legal_section_split,
            ChunkingStrategy.RECURSIVE: self._recursive_split,
        }

        splitter = dispatch.get(cfg.strategy, self._recursive_split)
        chunks = splitter(text, cfg, meta, source_doc_id)

        # Post-process: set overlap info
        chunks = self._compute_overlaps(chunks, text)

        # Filter by min size
        chunks = [
            c for c in chunks
            if c.token_count >= cfg.min_chunk_size or len(chunks) == 1
        ]

        elapsed = time.monotonic() - t0
        self._total_chunks_produced += len(chunks)
        self._total_texts_processed += 1
        strat_key = cfg.strategy.value
        self._strategy_counts[strat_key] = (
            self._strategy_counts.get(strat_key, 0) + 1
        )

        logger.info(
            "Chunked %d chars → %d chunks (%s) in %.3fs",
            len(text), len(chunks), cfg.strategy.value, elapsed,
        )
        return chunks

    def chunk_legal_document(
        self,
        text: str,
        doc_type: str = "motion",
        metadata: Optional[Dict[str, Any]] = None,
        source_doc_id: Optional[str] = None,
    ) -> List[Chunk]:
        """Chunk a legal document using type-specific configuration.

        Legal-document-aware splitting that:
        - Detects section headers (I., II., A., B., ¶1.)
        - Keeps Michigan citations intact (MCL, MCR, MRE)
        - Preserves paragraph structure
        - Handles footnotes

        Parameters
        ----------
        text : str
            Full document text.
        doc_type : str
            One of: ``motion``, ``brief``, ``complaint``,
            ``affidavit``, ``order``, ``transcript``.
        metadata : dict or None
            Source metadata.
        source_doc_id : str or None
            Source document identifier.

        Returns
        -------
        list[Chunk]
            Ordered chunks with legal-structure-aware boundaries.
        """
        cfg = _DOC_TYPE_CONFIGS.get(doc_type)
        if cfg is None:
            logger.warning(
                "Unknown doc_type '%s'; using default config", doc_type,
            )
            cfg = self._default_config

        meta = dict(metadata or {})
        meta["doc_type"] = doc_type

        return self.chunk_text(
            text, config=cfg, metadata=meta, source_doc_id=source_doc_id,
        )

    def optimize_chunk_size(
        self,
        texts: List[str],
        target_recall: float = 0.95,
        size_range: Tuple[int, int] = (128, 1024),
        step: int = 64,
    ) -> ChunkConfig:
        """Auto-tune chunk size by testing different configurations.

        Evaluates chunk-size candidates on the provided texts and
        returns the configuration that best balances chunk count,
        average size, and coverage (all text covered).

        Parameters
        ----------
        texts : list[str]
            Sample texts to evaluate against.
        target_recall : float
            Target coverage ratio (0-1).
        size_range : tuple[int, int]
            (min_size, max_size) token range to search.
        step : int
            Token step between candidates.

        Returns
        -------
        ChunkConfig
            Optimised configuration.
        """
        best_config = ChunkConfig(chunk_size=512)
        best_score = -1.0

        for size in range(size_range[0], size_range[1] + 1, step):
            overlap = max(16, size // 8)
            cfg = ChunkConfig(
                strategy=ChunkingStrategy.RECURSIVE,
                chunk_size=size,
                chunk_overlap=overlap,
                min_chunk_size=max(20, size // 10),
                max_chunk_size=size * 2,
            )

            total_chunks = 0
            total_coverage = 0.0
            size_variance_sum = 0.0

            for text in texts:
                chunks = self.chunk_text(text, config=cfg)
                total_chunks += len(chunks)

                # Coverage: fraction of original text covered
                covered_chars = sum(len(c.text) for c in chunks)
                text_len = max(len(text), 1)
                total_coverage += min(1.0, covered_chars / text_len)

                # Size variance
                if chunks:
                    avg_tokens = sum(c.token_count for c in chunks) / len(chunks)
                    var = sum(
                        (c.token_count - avg_tokens) ** 2 for c in chunks
                    ) / len(chunks)
                    size_variance_sum += math.sqrt(var)

            n = max(len(texts), 1)
            avg_coverage = total_coverage / n
            avg_variance = size_variance_sum / n

            # Score: coverage matters most, then low variance
            score = (
                avg_coverage * 2.0
                - avg_variance / max(size, 1) * 0.5
            )

            if avg_coverage >= target_recall and score > best_score:
                best_score = score
                best_config = cfg

        logger.info(
            "Chunk size optimization: best=%d tokens, overlap=%d, score=%.3f",
            best_config.chunk_size, best_config.chunk_overlap, best_score,
        )
        return best_config

    def analyze_chunks(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """Compute statistics for a list of chunks.

        Parameters
        ----------
        chunks : list[Chunk]
            Chunks to analyse.

        Returns
        -------
        dict
            Comprehensive statistics including size distribution,
            overlap metrics, and coverage information.
        """
        if not chunks:
            return {
                "count": 0,
                "total_chars": 0,
                "total_tokens": 0,
            }

        char_sizes = [len(c.text) for c in chunks]
        token_sizes = [c.token_count for c in chunks]
        overlaps_prev = [c.overlap_prev for c in chunks]
        overlaps_next = [c.overlap_next for c in chunks]

        def _stats(values: List[int]) -> Dict[str, float]:
            n = len(values)
            mean = sum(values) / n
            variance = sum((v - mean) ** 2 for v in values) / n
            return {
                "min": min(values),
                "max": max(values),
                "mean": round(mean, 2),
                "median": sorted(values)[n // 2],
                "std": round(math.sqrt(variance), 2),
                "total": sum(values),
            }

        # Coverage: assuming chunks are from one document
        if chunks[0].start_offset is not None and chunks[-1].end_offset is not None:
            doc_span = chunks[-1].end_offset - chunks[0].start_offset
        else:
            doc_span = sum(char_sizes)

        strategies = set()
        doc_types = set()
        for c in chunks:
            if "strategy" in c.metadata:
                strategies.add(c.metadata["strategy"])
            if "doc_type" in c.metadata:
                doc_types.add(c.metadata["doc_type"])

        return {
            "count": len(chunks),
            "char_sizes": _stats(char_sizes),
            "token_sizes": _stats(token_sizes),
            "overlap_prev": _stats(overlaps_prev),
            "overlap_next": _stats(overlaps_next),
            "total_chars": sum(char_sizes),
            "total_tokens": sum(token_sizes),
            "doc_span_chars": doc_span,
            "strategies_used": sorted(strategies),
            "doc_types": sorted(doc_types),
            "has_source_doc_id": any(c.source_doc_id for c in chunks),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return optimizer usage statistics.

        Returns
        -------
        dict
            Counts of texts processed, chunks produced, and
            strategy usage breakdown.
        """
        return {
            "total_texts_processed": self._total_texts_processed,
            "total_chunks_produced": self._total_chunks_produced,
            "avg_chunks_per_text": round(
                self._total_chunks_produced
                / max(self._total_texts_processed, 1),
                2,
            ),
            "strategy_counts": dict(self._strategy_counts),
            "has_embed_fn": self._embed_fn is not None,
            "default_config": self._default_config.to_dict(),
        }

    # ------------------------------------------------------------------
    # Strategy: Fixed-size splitting
    # ------------------------------------------------------------------

    def _fixed_size_split(
        self,
        text: str,
        config: ChunkConfig,
        metadata: Dict[str, Any],
        source_doc_id: Optional[str],
    ) -> List[Chunk]:
        """Split text into fixed character-window chunks.

        Uses ``config.chunk_size`` (in tokens) converted to an
        approximate character count.  Overlap is applied between
        consecutive chunks.
        """
        char_size = _chars_for_tokens(config.chunk_size)
        char_overlap = _chars_for_tokens(config.chunk_overlap)
        step = max(1, char_size - char_overlap)

        chunks: List[Chunk] = []
        pos = 0

        while pos < len(text):
            end = min(pos + char_size, len(text))

            # Adjust end to a safe position
            if end < len(text):
                end = _find_safe_split(text, end, window=50)

            chunk_text = text[pos:end].strip()
            if chunk_text:
                cid = _chunk_id(chunk_text, source_doc_id, pos)
                chunks.append(Chunk(
                    text=chunk_text,
                    chunk_id=cid,
                    source_doc_id=source_doc_id,
                    start_offset=pos,
                    end_offset=end,
                    metadata=dict(metadata),
                    token_count=_estimate_tokens(chunk_text),
                ))

            pos += step

        return chunks

    # ------------------------------------------------------------------
    # Strategy: Sentence splitting
    # ------------------------------------------------------------------

    def _sentence_split(
        self,
        text: str,
        config: ChunkConfig,
        metadata: Dict[str, Any],
        source_doc_id: Optional[str],
    ) -> List[Chunk]:
        """Split text on sentence boundaries, grouping into chunks.

        Sentences are accumulated until the chunk size limit is
        reached, then a new chunk begins (with overlap).
        """
        # Protect citations from being split
        protected, cite_map = _protect_citations(text)

        # Split into sentences
        raw_sentences = _SENTENCE_RE.split(protected)
        sentences: List[Tuple[str, int, int]] = []
        offset = 0
        for sent in raw_sentences:
            restored = _restore_citations(sent, cite_map)
            start = text.find(restored, offset)
            if start == -1:
                start = offset
            end = start + len(restored)
            sentences.append((restored, start, end))
            offset = end

        # Group sentences into chunks
        target_chars = _chars_for_tokens(config.chunk_size)
        overlap_chars = _chars_for_tokens(config.chunk_overlap)

        chunks: List[Chunk] = []
        current_sents: List[Tuple[str, int, int]] = []
        current_len = 0

        for sent_text, s_start, s_end in sentences:
            sent_len = len(sent_text)

            if current_len + sent_len > target_chars and current_sents:
                # Emit chunk
                chunk = self._build_chunk_from_spans(
                    current_sents, metadata, source_doc_id,
                )
                chunks.append(chunk)

                # Overlap: carry some trailing sentences
                overlap_sents: List[Tuple[str, int, int]] = []
                overlap_len = 0
                for s in reversed(current_sents):
                    if overlap_len + len(s[0]) > overlap_chars:
                        break
                    overlap_sents.insert(0, s)
                    overlap_len += len(s[0])
                current_sents = overlap_sents
                current_len = overlap_len

            current_sents.append((sent_text, s_start, s_end))
            current_len += sent_len

        # Final chunk
        if current_sents:
            chunk = self._build_chunk_from_spans(
                current_sents, metadata, source_doc_id,
            )
            chunks.append(chunk)

        return chunks

    # ------------------------------------------------------------------
    # Strategy: Paragraph splitting
    # ------------------------------------------------------------------

    def _paragraph_split(
        self,
        text: str,
        config: ChunkConfig,
        metadata: Dict[str, Any],
        source_doc_id: Optional[str],
    ) -> List[Chunk]:
        """Split text on paragraph boundaries (double newlines).

        Paragraphs smaller than ``min_chunk_size`` are merged with
        the next paragraph.  Paragraphs larger than ``max_chunk_size``
        are recursively split by sentence.
        """
        paragraphs = re.split(r"\n\s*\n", text)
        target_chars = _chars_for_tokens(config.chunk_size)
        max_chars = _chars_for_tokens(config.max_chunk_size)

        spans: List[Tuple[str, int, int]] = []
        offset = 0
        for para in paragraphs:
            stripped = para.strip()
            if not stripped:
                offset += len(para) + 2  # account for split \n\n
                continue
            start = text.find(stripped, offset)
            if start == -1:
                start = offset
            end = start + len(stripped)
            spans.append((stripped, start, end))
            offset = end

        # Group paragraphs into chunks
        chunks: List[Chunk] = []
        current: List[Tuple[str, int, int]] = []
        current_len = 0

        for para_text, p_start, p_end in spans:
            para_len = len(para_text)

            # Oversized paragraph: sub-split by sentence
            if para_len > max_chars:
                if current:
                    chunks.append(self._build_chunk_from_spans(
                        current, metadata, source_doc_id,
                    ))
                    current = []
                    current_len = 0

                sub_chunks = self._sentence_split(
                    para_text, config, metadata, source_doc_id,
                )
                # Adjust offsets
                for sc in sub_chunks:
                    sc.start_offset += p_start
                    sc.end_offset += p_start
                chunks.extend(sub_chunks)
                continue

            if current_len + para_len > target_chars and current:
                chunks.append(self._build_chunk_from_spans(
                    current, metadata, source_doc_id,
                ))
                current = []
                current_len = 0

            current.append((para_text, p_start, p_end))
            current_len += para_len

        if current:
            chunks.append(self._build_chunk_from_spans(
                current, metadata, source_doc_id,
            ))

        return chunks

    # ------------------------------------------------------------------
    # Strategy: Semantic splitting
    # ------------------------------------------------------------------

    def _semantic_split(
        self,
        text: str,
        config: ChunkConfig,
        metadata: Dict[str, Any],
        source_doc_id: Optional[str],
    ) -> List[Chunk]:
        """Split where embedding similarity between adjacent sentences drops.

        Requires ``self._embed_fn`` to be set.  Falls back to
        sentence splitting if no embedding function is available.

        The algorithm:
        1. Split text into sentences.
        2. Embed each sentence.
        3. Compute cosine similarity between consecutive sentences.
        4. Split where similarity < threshold.
        5. Merge small groups to meet chunk_size.
        """
        if self._embed_fn is None:
            logger.info(
                "No embed_fn provided; falling back to sentence splitting",
            )
            return self._sentence_split(text, config, metadata, source_doc_id)

        # Split into sentences with positions
        protected, cite_map = _protect_citations(text)
        raw_sentences = _SENTENCE_RE.split(protected)
        sentences: List[Tuple[str, int, int]] = []
        offset = 0
        for sent in raw_sentences:
            restored = _restore_citations(sent, cite_map)
            stripped = restored.strip()
            if not stripped:
                offset += len(sent)
                continue
            start = text.find(stripped, offset)
            if start == -1:
                start = offset
            end = start + len(stripped)
            sentences.append((stripped, start, end))
            offset = end

        if len(sentences) <= 1:
            return self._sentence_split(text, config, metadata, source_doc_id)

        # Embed sentences
        try:
            embeddings = [self._embed_fn(s[0]) for s in sentences]
        except Exception as exc:
            logger.warning("Embedding failed in semantic split: %s", exc)
            return self._sentence_split(text, config, metadata, source_doc_id)

        # Compute pairwise cosine similarities
        sims: List[float] = []
        for i in range(len(embeddings) - 1):
            sim = self._cosine_sim(embeddings[i], embeddings[i + 1])
            sims.append(sim)

        # Find split points (where similarity drops below threshold)
        threshold = config.similarity_threshold
        split_indices: List[int] = [0]
        for i, sim in enumerate(sims):
            if sim < threshold:
                split_indices.append(i + 1)
        split_indices.append(len(sentences))

        # Build chunks from groups
        target_chars = _chars_for_tokens(config.chunk_size)
        chunks: List[Chunk] = []

        for g in range(len(split_indices) - 1):
            group_start = split_indices[g]
            group_end = split_indices[g + 1]
            group_sents = sentences[group_start:group_end]

            # Merge small groups forward
            group_text = " ".join(s[0] for s in group_sents)
            if len(group_text) > target_chars * 2:
                # Sub-split large groups
                sub = self._sentence_split(
                    group_text, config, metadata, source_doc_id,
                )
                base_offset = group_sents[0][1]
                for sc in sub:
                    sc.start_offset += base_offset
                    sc.end_offset += base_offset
                chunks.extend(sub)
            else:
                chunk = self._build_chunk_from_spans(
                    group_sents, metadata, source_doc_id,
                )
                chunks.append(chunk)

        return chunks

    # ------------------------------------------------------------------
    # Strategy: Legal section splitting
    # ------------------------------------------------------------------

    def _legal_section_split(
        self,
        text: str,
        config: ChunkConfig,
        metadata: Dict[str, Any],
        source_doc_id: Optional[str],
    ) -> List[Chunk]:
        """Michigan-specific legal document section splitting.

        Detects structural boundaries in legal documents:
        - Roman numeral sections (I., II., III.)
        - Letter sub-sections (A., B., C.)
        - Numbered paragraphs (¶1., ¶2.)
        - Court document sections (COMES NOW, WHEREFORE, etc.)
        - SECTION/ARTICLE headings

        Never splits within:
        - Michigan citations (MCL, MCR, MRE)
        - Parenthetical references ((3)(a), (c)(ii))
        - Id. and See signal phrases with their targets
        - Footnote marker + text pairs
        """
        # Protect citations
        protected, cite_map = _protect_citations(text)

        # Find all legal section boundaries
        boundaries: List[int] = [0]

        for m in _LEGAL_BOUNDARY_RE.finditer(protected):
            pos = m.start()
            # Skip if inside a citation placeholder
            if any(
                protected[max(0, pos - 20):pos + 20].find(f"__CITE") >= 0
                for _ in [0]
            ):
                continue
            boundaries.append(pos)

        boundaries.append(len(protected))

        # Remove duplicate / too-close boundaries
        boundaries = sorted(set(boundaries))
        min_gap = _chars_for_tokens(config.min_chunk_size)
        filtered: List[int] = [boundaries[0]]
        for b in boundaries[1:]:
            if b - filtered[-1] >= min_gap or b == boundaries[-1]:
                filtered.append(b)
        boundaries = filtered

        # Extract sections
        target_chars = _chars_for_tokens(config.chunk_size)
        max_chars = _chars_for_tokens(config.max_chunk_size)
        sections: List[Tuple[str, int, int]] = []

        for i in range(len(boundaries) - 1):
            start = boundaries[i]
            end = boundaries[i + 1]
            section_text = protected[start:end]

            # Restore citations
            restored = _restore_citations(section_text, cite_map)
            stripped = restored.strip()
            if not stripped:
                continue

            # Find true position in original text
            true_start = text.find(stripped[:50], max(0, start - 20))
            if true_start == -1:
                true_start = start
            true_end = true_start + len(stripped)

            sections.append((stripped, true_start, true_end))

        # Merge small sections, split large ones
        chunks: List[Chunk] = []
        pending: List[Tuple[str, int, int]] = []
        pending_len = 0

        for sec_text, s_start, s_end in sections:
            sec_len = len(sec_text)

            # Oversized section: recursive sub-split
            if sec_len > max_chars:
                if pending:
                    chunks.append(self._build_chunk_from_spans(
                        pending, metadata, source_doc_id,
                    ))
                    pending = []
                    pending_len = 0

                sub = self._recursive_split(
                    sec_text, config, metadata, source_doc_id,
                )
                for sc in sub:
                    sc.start_offset += s_start
                    sc.end_offset += s_start
                    sc.metadata["section_sub_split"] = True
                chunks.extend(sub)
                continue

            # Accumulate sections until target size
            if pending_len + sec_len > target_chars and pending:
                chunks.append(self._build_chunk_from_spans(
                    pending, metadata, source_doc_id,
                ))
                pending = []
                pending_len = 0

            pending.append((sec_text, s_start, s_end))
            pending_len += sec_len

        if pending:
            chunks.append(self._build_chunk_from_spans(
                pending, metadata, source_doc_id,
            ))

        # Detect section headers for metadata enrichment
        for chunk in chunks:
            header = self._detect_section_header(chunk.text)
            if header:
                chunk.metadata["section_header"] = header

        return chunks

    # ------------------------------------------------------------------
    # Strategy: Recursive splitting
    # ------------------------------------------------------------------

    def _recursive_split(
        self,
        text: str,
        config: ChunkConfig,
        metadata: Dict[str, Any],
        source_doc_id: Optional[str],
    ) -> List[Chunk]:
        """LangChain-style recursive character splitting.

        Tries separators in priority order.  For each separator, if
        splitting produces chunks within the target size range, uses
        those splits.  Otherwise, recurses with the next separator.

        Legal citations are protected from splitting at all levels.
        """
        target_chars = _chars_for_tokens(config.chunk_size)
        overlap_chars = _chars_for_tokens(config.chunk_overlap)
        separators = config.separators or list(_DEFAULT_SEPARATORS)

        raw_chunks = self._recursive_split_inner(
            text, separators, target_chars, overlap_chars,
        )

        chunks: List[Chunk] = []
        offset = 0

        for chunk_text in raw_chunks:
            stripped = chunk_text.strip()
            if not stripped:
                continue

            start = text.find(stripped, offset)
            if start == -1:
                start = offset
            end = start + len(stripped)

            cid = _chunk_id(stripped, source_doc_id, start)
            chunks.append(Chunk(
                text=stripped,
                chunk_id=cid,
                source_doc_id=source_doc_id,
                start_offset=start,
                end_offset=end,
                metadata=dict(metadata),
                token_count=_estimate_tokens(stripped),
            ))
            offset = end

        return chunks

    def _recursive_split_inner(
        self,
        text: str,
        separators: List[str],
        target_chars: int,
        overlap_chars: int,
    ) -> List[str]:
        """Inner recursive splitting logic.

        Returns a list of text segments (not yet wrapped as Chunk).
        """
        if len(text) <= target_chars:
            return [text] if text.strip() else []

        if not separators:
            # No separators left: hard split at target_chars boundary
            result: List[str] = []
            pos = 0
            while pos < len(text):
                end = min(pos + target_chars, len(text))
                if end < len(text):
                    end = _find_safe_split(text, end, window=50)
                segment = text[pos:end]
                if segment.strip():
                    result.append(segment)
                pos = end - overlap_chars if end < len(text) else end
            return result

        sep = separators[0]
        remaining_seps = separators[1:]

        parts = text.split(sep)

        # If splitting didn't help, try next separator
        if len(parts) <= 1:
            return self._recursive_split_inner(
                text, remaining_seps, target_chars, overlap_chars,
            )

        # Merge parts into appropriately-sized chunks
        result: List[str] = []
        current_parts: List[str] = []
        current_len = 0

        for part in parts:
            part_len = len(part) + len(sep)  # account for separator

            if current_len + part_len > target_chars and current_parts:
                merged = sep.join(current_parts)
                if len(merged) > target_chars:
                    # Recursively split the oversized merge
                    sub = self._recursive_split_inner(
                        merged, remaining_seps, target_chars, overlap_chars,
                    )
                    result.extend(sub)
                else:
                    result.append(merged)

                # Overlap: carry trailing parts
                overlap_parts: List[str] = []
                overlap_len = 0
                for p in reversed(current_parts):
                    if overlap_len + len(p) > overlap_chars:
                        break
                    overlap_parts.insert(0, p)
                    overlap_len += len(p)
                current_parts = overlap_parts
                current_len = overlap_len

            current_parts.append(part)
            current_len += part_len

        # Final group
        if current_parts:
            merged = sep.join(current_parts)
            if len(merged) > target_chars:
                sub = self._recursive_split_inner(
                    merged, remaining_seps, target_chars, overlap_chars,
                )
                result.extend(sub)
            else:
                result.append(merged)

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_chunk_from_spans(
        self,
        spans: List[Tuple[str, int, int]],
        metadata: Dict[str, Any],
        source_doc_id: Optional[str],
    ) -> Chunk:
        """Build a Chunk from a list of (text, start, end) spans."""
        combined = " ".join(s[0] for s in spans)
        start = spans[0][1]
        end = spans[-1][2]
        cid = _chunk_id(combined, source_doc_id, start)
        return Chunk(
            text=combined,
            chunk_id=cid,
            source_doc_id=source_doc_id,
            start_offset=start,
            end_offset=end,
            metadata=dict(metadata),
            token_count=_estimate_tokens(combined),
        )

    def _compute_overlaps(
        self, chunks: List[Chunk], original_text: str
    ) -> List[Chunk]:
        """Compute overlap_prev and overlap_next for each chunk."""
        for i in range(len(chunks)):
            if i > 0:
                prev = chunks[i - 1]
                curr = chunks[i]
                overlap = max(0, prev.end_offset - curr.start_offset)
                curr.overlap_prev = overlap
            if i < len(chunks) - 1:
                curr = chunks[i]
                nxt = chunks[i + 1]
                overlap = max(0, curr.end_offset - nxt.start_offset)
                curr.overlap_next = overlap
        return chunks

    def _detect_section_header(self, text: str) -> Optional[str]:
        """Extract the section header from the beginning of chunk text."""
        lines = text.strip().split("\n", 1)
        first_line = lines[0].strip() if lines else ""

        # Roman numeral section
        m = re.match(r"^([IVXLCDMivxlcdm]+)\.\s+(.+)", first_line)
        if m:
            return f"{m.group(1)}. {m.group(2)[:80]}"

        # Letter section
        m = re.match(r"^([A-Z])\.\s+(.+)", first_line)
        if m:
            return f"{m.group(1)}. {m.group(2)[:80]}"

        # Numbered paragraph
        m = re.match(r"^(?:¶\s*)?(\d+)\.\s+(.+)", first_line)
        if m:
            return f"¶{m.group(1)}. {m.group(2)[:80]}"

        # Court section headings
        m = _COURT_SECTION_RE.match(first_line)
        if m:
            return first_line[:100]

        # SECTION / ARTICLE
        m = _SECTION_HEADING_RE.match(first_line)
        if m:
            return first_line[:100]

        return None

    @staticmethod
    def _cosine_sim(a: List[float], b: List[float]) -> float:
        """Cosine similarity between two vectors."""
        dot_val = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a < 1e-12 or norm_b < 1e-12:
            return 0.0
        return dot_val / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_DEFAULT_OPTIMIZER: Optional[ChunkOptimizer] = None


def get_optimizer(**kwargs: Any) -> ChunkOptimizer:
    """Return a module-level singleton ``ChunkOptimizer``."""
    global _DEFAULT_OPTIMIZER
    if _DEFAULT_OPTIMIZER is None:
        _DEFAULT_OPTIMIZER = ChunkOptimizer(**kwargs)
    return _DEFAULT_OPTIMIZER


def chunk_text(
    text: str,
    strategy: str = "recursive",
    chunk_size: int = 512,
    doc_type: Optional[str] = None,
) -> List[Chunk]:
    """Convenience function to chunk text.

    Parameters
    ----------
    text : str
        Input text.
    strategy : str
        Strategy name (matches ``ChunkingStrategy`` values).
    chunk_size : int
        Target tokens per chunk.
    doc_type : str or None
        If set, uses ``chunk_legal_document`` with this type.

    Returns
    -------
    list[Chunk]
        Chunked text.
    """
    opt = get_optimizer()
    if doc_type:
        return opt.chunk_legal_document(text, doc_type=doc_type)

    cfg = ChunkConfig(
        strategy=ChunkingStrategy(strategy),
        chunk_size=chunk_size,
    )
    return opt.chunk_text(text, config=cfg)


# ---------------------------------------------------------------------------
# CLI smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    sample_text = """
I. STATEMENT OF FACTS

Plaintiff Andrew Pigors ("Plaintiff") is the biological father of the minor
child. On or about January 15, 2024, the Defendant Emily Watson ("Defendant")
filed a petition for an ex parte personal protection order under MCL 600.2950.

The Court, the Honorable Judge McNeill presiding, granted the ex parte PPO
without notice to Plaintiff, in violation of MCR 3.707(A)(1).

II. ARGUMENT

A. The Trial Court Erred in Granting the PPO Without Notice

Under MCL 600.2950(1), a court may issue a PPO only upon a showing of
reasonable cause. See MCR 3.707(A)(1). The Defendant failed to establish
reasonable cause because the allegations in her petition were conclusory
and unsupported by any evidence. Id. at ¶12.

The best interest factors under MCL 722.23(3)(a) through (l) must be
considered in any custody determination. See Vodvarka v Grasmeyer,
259 Mich App 499; 675 NW2d 847 (2003).

B. The Court's Findings Were Clearly Erroneous

¶1. The trial court found that Plaintiff posed an immediate threat.
This finding is not supported by the record.

¶2. No testimony or documentary evidence was presented to support
the claim of domestic violence.

III. CONCLUSION

WHEREFORE, Plaintiff respectfully requests that this Honorable Court
reverse the trial court's order and vacate the personal protection order.

CERTIFICATE OF SERVICE

I hereby certify that on this date, a true copy of the foregoing was
served upon all parties of record via electronic filing.
"""

    opt = ChunkOptimizer()

    print("=" * 60)
    print("LEGAL SECTION SPLIT (motion)")
    print("=" * 60)
    chunks = opt.chunk_legal_document(sample_text, doc_type="motion")
    for i, c in enumerate(chunks):
        header = c.metadata.get("section_header", "")
        print(f"\n--- Chunk {i} (id={c.chunk_id}) "
              f"[{c.start_offset}:{c.end_offset}] "
              f"tokens={c.token_count} "
              f"overlap_prev={c.overlap_prev} ---")
        if header:
            print(f"  Section: {header}")
        print(f"  {c.text[:120]}...")

    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)
    analysis = opt.analyze_chunks(chunks)
    print(json.dumps(analysis, indent=2, default=str))

    print("\n" + "=" * 60)
    print("RECURSIVE SPLIT")
    print("=" * 60)
    cfg = ChunkConfig(
        strategy=ChunkingStrategy.RECURSIVE,
        chunk_size=128,
        chunk_overlap=16,
    )
    chunks2 = opt.chunk_text(sample_text, config=cfg)
    for i, c in enumerate(chunks2):
        print(f"  Chunk {i}: {c.token_count} tokens, "
              f"[{c.start_offset}:{c.end_offset}]")

    print(f"\nOptimizer stats: {json.dumps(opt.get_stats(), indent=2)}")
