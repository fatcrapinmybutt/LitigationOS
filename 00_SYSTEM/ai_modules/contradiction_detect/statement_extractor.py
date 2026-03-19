"""Extract attributed statements from litigation documents."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

from . import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Statement:
    """A single attributed statement extracted from a document."""

    text: str
    speaker: str
    date: Optional[str] = None
    source_file: str = ""
    page_number: int = 0
    line_number: int = 0
    context: str = ""
    is_sworn: bool = False

    def __hash__(self) -> int:
        return hash((self.text, self.speaker, self.source_file, self.page_number))


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------

class StatementExtractor:
    """Scan raw text and pull out speaker-attributed statements."""

    def __init__(self) -> None:
        self._marker_re = config.STATEMENT_MARKERS[0]
        self._date_patterns = config.DATE_PATTERNS
        self._party_patterns = config.PARTY_PATTERNS
        self._sworn_patterns = config.SWORN_INDICATORS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_statements(
        self,
        text: str,
        source_metadata: Optional[dict] = None,
    ) -> list[Statement]:
        """Return every attributed statement found in *text*.

        Parameters
        ----------
        text:
            Full document text (may span many pages).
        source_metadata:
            Optional dict with keys like ``file_path``, ``page_number``,
            ``date``, etc.
        """
        if not text:
            return []

        meta = source_metadata or {}
        statements: list[Statement] = []
        lines = text.splitlines()

        for line_idx, line in enumerate(lines, start=1):
            if len(line.strip()) < config.MIN_STATEMENT_LENGTH:
                continue

            for match in self._marker_re.finditer(line):
                stmt = self._build_statement(
                    line, match, line_idx, lines, meta,
                )
                if stmt is not None:
                    statements.append(stmt)

        logger.debug("Extracted %d statements from source %s",
                      len(statements), meta.get("file_path", "<inline>"))
        return statements

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_statement(
        self,
        line: str,
        marker_match: re.Match,
        line_number: int,
        all_lines: list[str],
        meta: dict,
    ) -> Optional[Statement]:
        """Build a *Statement* from a marker match inside a line."""
        # Grab the sentence containing the marker
        sent = self._extract_sentence(line, marker_match.start())
        if len(sent.strip()) < config.MIN_STATEMENT_LENGTH:
            return None

        speaker = self._identify_speaker(line, marker_match.start(), all_lines, line_number)
        date = self._extract_date(line, meta)
        context = self._get_context(all_lines, line_number, window=2)
        is_sworn = self._check_sworn(context)

        return Statement(
            text=sent.strip(),
            speaker=speaker,
            date=date,
            source_file=meta.get("file_path", ""),
            page_number=meta.get("page_number", 0),
            line_number=line_number,
            context=context,
            is_sworn=is_sworn,
        )

    @staticmethod
    def _extract_sentence(line: str, pos: int) -> str:
        """Return the sentence surrounding *pos* in *line*."""
        # Walk backwards to sentence start
        start = pos
        while start > 0 and line[start - 1] not in ".!?\n":
            start -= 1
        # Walk forwards to sentence end
        end = pos
        while end < len(line) and line[end] not in ".!?\n":
            end += 1
        # Include the trailing punctuation
        if end < len(line):
            end += 1
        return line[start:end]

    def _identify_speaker(
        self,
        line: str,
        marker_pos: int,
        all_lines: list[str],
        line_number: int,
    ) -> str:
        """Identify who is speaking.

        Strategy: look in the *line* text before the marker for a party
        name.  If none found, scan surrounding context lines.
        """
        before_marker = line[:marker_pos]
        speaker = self._match_party(before_marker)
        if speaker != "Unknown":
            return speaker

        # Broaden search to the full line
        speaker = self._match_party(line)
        if speaker != "Unknown":
            return speaker

        # Scan nearby lines (2 above, 2 below)
        context = self._get_context(all_lines, line_number, window=2)
        return self._match_party(context)

    def _match_party(self, text: str) -> str:
        """Return the first matching party name in *text*."""
        for name, pattern in self._party_patterns.items():
            if pattern.search(text):
                return name
        return "Unknown"

    def _extract_date(self, line: str, meta: dict) -> Optional[str]:
        """Extract the most likely date from the line or metadata."""
        for pat in self._date_patterns:
            m = pat.search(line)
            if m:
                return m.group(0)
        return meta.get("date")

    @staticmethod
    def _get_context(
        lines: list[str], line_number: int, window: int = 2,
    ) -> str:
        """Return surrounding lines as a single context string."""
        start = max(0, line_number - 1 - window)
        end = min(len(lines), line_number + window)
        return " ".join(lines[start:end])

    def _check_sworn(self, text: str) -> bool:
        """Return ``True`` if the context indicates sworn testimony."""
        return any(p.search(text) for p in self._sworn_patterns)
