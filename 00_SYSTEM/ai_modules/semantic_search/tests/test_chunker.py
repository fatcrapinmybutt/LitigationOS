"""Tests for DocumentChunker."""
from __future__ import annotations

import pytest

from semantic_search.chunker import Chunk, DocumentChunker


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_TEXT = (
    "The court finds that the defendant failed to comply with the order. "
    "Evidence submitted by the plaintiff clearly demonstrates a pattern of "
    "misconduct spanning multiple years. The judge noted that this behaviour "
    "is inconsistent with the standards expected of a licensed professional. "
    "Furthermore, the testimony of three independent witnesses corroborates "
    "the claims made in the original complaint filed on January fifteenth "
    "of two thousand twenty four. The court therefore grants the motion for "
    "summary judgement and orders the defendant to pay restitution in the "
    "amount determined at the subsequent hearing scheduled for March first."
)

SHORT_TEXT = "Short evidence note."

METADATA = {
    "file_path": "/evidence/exhibit_A1.pdf",
    "page_number": 3,
    "lane": "A",
    "case_number": "2024-001507-DC",
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestDocumentChunker:
    """Unit tests for DocumentChunker."""

    def test_basic_chunking_produces_chunks(self) -> None:
        chunker = DocumentChunker(chunk_size=20, chunk_overlap=5)
        chunks = chunker.chunk_text(SAMPLE_TEXT, metadata=METADATA)
        assert len(chunks) > 1
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_overlap_tokens_shared(self) -> None:
        chunker = DocumentChunker(chunk_size=20, chunk_overlap=5)
        chunks = chunker.chunk_text(SAMPLE_TEXT, metadata=METADATA)
        # With overlap, consecutive chunks should share some text
        if len(chunks) >= 2:
            words_0 = set(chunks[0].text.split())
            words_1 = set(chunks[1].text.split())
            overlap = words_0 & words_1
            assert len(overlap) > 0, "Expected overlapping words between consecutive chunks"

    def test_metadata_preserved(self) -> None:
        chunker = DocumentChunker(chunk_size=20, chunk_overlap=5)
        chunks = chunker.chunk_text(SAMPLE_TEXT, metadata=METADATA)
        for chunk in chunks:
            assert chunk.metadata["file_path"] == METADATA["file_path"]
            assert chunk.metadata["lane"] == METADATA["lane"]
            assert chunk.metadata["case_number"] == METADATA["case_number"]

    def test_empty_text_returns_empty(self) -> None:
        chunker = DocumentChunker()
        assert chunker.chunk_text("") == []
        assert chunker.chunk_text("   ") == []
        assert chunker.chunk_text("", metadata=METADATA) == []

    def test_none_metadata_defaults_to_empty_dict(self) -> None:
        chunker = DocumentChunker(chunk_size=20, chunk_overlap=5)
        chunks = chunker.chunk_text(SAMPLE_TEXT)
        assert all(isinstance(c.metadata, dict) for c in chunks)

    def test_short_text_single_chunk(self) -> None:
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        chunks = chunker.chunk_text(SHORT_TEXT, metadata=METADATA)
        assert len(chunks) == 1
        assert chunks[0].text == SHORT_TEXT

    def test_offsets_are_valid(self) -> None:
        chunker = DocumentChunker(chunk_size=20, chunk_overlap=5)
        chunks = chunker.chunk_text(SAMPLE_TEXT, metadata=METADATA)
        for chunk in chunks:
            assert chunk.start_offset >= 0
            assert chunk.end_offset > chunk.start_offset
            assert chunk.end_offset <= len(SAMPLE_TEXT)

    def test_overlap_must_be_less_than_size(self) -> None:
        with pytest.raises(ValueError, match="chunk_overlap must be < chunk_size"):
            DocumentChunker(chunk_size=10, chunk_overlap=10)

    def test_single_word_text(self) -> None:
        chunker = DocumentChunker(chunk_size=10, chunk_overlap=2)
        chunks = chunker.chunk_text("Evidence")
        assert len(chunks) == 1
        assert chunks[0].text == "Evidence"
