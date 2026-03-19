"""Document chunking with overlapping windows and metadata preservation.

Splits raw text into overlapping token-level chunks, each tagged with
provenance metadata (file path, page number, lane, case number).
Uses whitespace tokenisation — no external tokeniser required.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from .config import CHUNK_OVERLAP, CHUNK_SIZE

log = logging.getLogger(__name__)

# Sentence boundary heuristic: split after `. `, `? `, `! ` followed by
# an uppercase letter or end-of-string.
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z]|\Z)")


@dataclass(frozen=True, slots=True)
class Chunk:
    """An individual text chunk with source provenance."""

    text: str
    start_offset: int          # character offset in the original text
    end_offset: int            # character offset (exclusive) in original text
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentChunker:
    """Split text into overlapping, metadata-tagged chunks."""

    def __init__(
        self,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be < chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chunk_text(
        self,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """Split *text* into overlapping chunks.

        Parameters
        ----------
        text:
            The raw document / page text.
        metadata:
            Provenance info attached to every chunk (file_path, page_number,
            lane, case_number …).

        Returns
        -------
        list[Chunk]
            Ordered list of chunks with character offsets.
        """
        if metadata is None:
            metadata = {}

        if not text or not text.strip():
            return []

        tokens = self._tokenise(text)
        if not tokens:
            return []

        # If the whole text fits in one chunk, return as-is.
        if len(tokens) <= self.chunk_size:
            return [Chunk(
                text=text.strip(),
                start_offset=0,
                end_offset=len(text),
                metadata=dict(metadata),
            )]

        step = self.chunk_size - self.chunk_overlap
        chunks: list[Chunk] = []

        for start_idx in range(0, len(tokens), step):
            end_idx = min(start_idx + self.chunk_size, len(tokens))
            span_tokens = tokens[start_idx:end_idx]

            # Recover character offsets from the first/last token.
            char_start = span_tokens[0][1]
            char_end = span_tokens[-1][2]

            chunk_text = text[char_start:char_end].strip()
            if not chunk_text:
                continue

            # Try snapping to sentence boundary at the end.
            chunk_text = self._snap_sentence_boundary(chunk_text)

            chunks.append(Chunk(
                text=chunk_text,
                start_offset=char_start,
                end_offset=char_end,
                metadata=dict(metadata),
            ))

            if end_idx >= len(tokens):
                break

        log.debug("Chunked text (%d chars) into %d chunks", len(text), len(chunks))
        return chunks

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenise(text: str) -> list[tuple[str, int, int]]:
        """Return list of (token, char_start, char_end) tuples."""
        result: list[tuple[str, int, int]] = []
        for m in re.finditer(r"\S+", text):
            result.append((m.group(), m.start(), m.end()))
        return result

    @staticmethod
    def _snap_sentence_boundary(text: str) -> str:
        """If the text ends mid-sentence, try to snap back to the last
        sentence boundary so chunks read more naturally.  If no boundary
        is found, return the original text."""
        sentences = _SENTENCE_RE.split(text)
        if len(sentences) <= 1:
            return text
        # Keep all but the (possibly truncated) last fragment.
        rejoined = text[: text.rfind(sentences[-1])].rstrip()
        return rejoined if rejoined else text
