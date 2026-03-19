"""Generate court-ready contradiction reports."""
from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import asdict
from datetime import datetime
from typing import Optional

from . import config
from .scorer import ScoredContradiction

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# SQL — report table
# ---------------------------------------------------------------------------
_CREATE_TABLE_SQL = """\
CREATE TABLE IF NOT EXISTS contradiction_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_a_source TEXT,
    statement_a_text TEXT,
    statement_a_date TEXT,
    statement_b_source TEXT,
    statement_b_text TEXT,
    statement_b_date TEXT,
    speaker TEXT,
    contradiction_type TEXT,
    severity TEXT,
    severity_score REAL,
    impeachment_value TEXT,
    lane TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


class ContradictionReport:
    """Render scored contradictions into markdown, JSON, or HTML reports."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        contradictions: list[ScoredContradiction],
        fmt: str = "markdown",
    ) -> str:
        """Return a formatted report string.

        Parameters
        ----------
        contradictions:
            Scored contradiction list, sorted by severity (caller decides).
        fmt:
            ``"markdown"`` | ``"json"`` | ``"html"``
        """
        sorted_cs = sorted(
            contradictions, key=lambda c: c.severity_score, reverse=True,
        )
        if fmt == "json":
            return self._render_json(sorted_cs)
        if fmt == "html":
            return self._render_html(sorted_cs)
        return self._render_markdown(sorted_cs)

    def generate_exhibit(self, contradiction: ScoredContradiction) -> dict:
        """Return a dict suitable for inclusion as a court exhibit."""
        a_orig = contradiction.statement_a.original
        b_orig = contradiction.statement_b.original
        return {
            "exhibit_type": "CONTRADICTION",
            "contradiction_type": contradiction.contradiction_type,
            "severity": contradiction.severity,
            "severity_score": contradiction.severity_score,
            "impeachment_value": contradiction.impeachment_value,
            "statement_a": {
                "text": a_orig.text,
                "speaker": a_orig.speaker,
                "source": a_orig.source_file,
                "page": a_orig.page_number,
                "date": contradiction.statement_a.date_normalized,
            },
            "statement_b": {
                "text": b_orig.text,
                "speaker": b_orig.speaker,
                "source": b_orig.source_file,
                "page": b_orig.page_number,
                "date": contradiction.statement_b.date_normalized,
            },
            "explanation": contradiction.explanation,
            "citations": contradiction.evidence_citations,
            "generated_at": datetime.now().isoformat(),
        }

    def store_to_db(
        self,
        contradictions: list[ScoredContradiction],
        lane: str = "",
        db_path: Optional[str] = None,
    ) -> int:
        """Persist contradictions to the ``contradiction_reports`` table.

        Returns the number of rows inserted.
        """
        path = db_path or config.DB_PATH
        conn = sqlite3.connect(path)
        try:
            for pragma in config.DB_PRAGMAS:
                conn.execute(pragma)
            conn.execute(_CREATE_TABLE_SQL)

            rows = []
            for c in contradictions:
                a_orig = c.statement_a.original
                b_orig = c.statement_b.original
                rows.append((
                    a_orig.source_file,
                    a_orig.text,
                    c.statement_a.date_normalized,
                    b_orig.source_file,
                    b_orig.text,
                    c.statement_b.date_normalized,
                    a_orig.speaker,
                    c.contradiction_type,
                    c.severity,
                    c.severity_score,
                    c.impeachment_value,
                    lane,
                ))

            conn.executemany(
                "INSERT INTO contradiction_reports "
                "(statement_a_source, statement_a_text, statement_a_date, "
                " statement_b_source, statement_b_text, statement_b_date, "
                " speaker, contradiction_type, severity, severity_score, "
                " impeachment_value, lane) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                rows,
            )
            conn.commit()
            logger.info("Stored %d contradiction reports to %s", len(rows), path)
            return len(rows)
        finally:
            conn.close()

    def summary_stats(
        self, contradictions: list[ScoredContradiction],
    ) -> dict:
        """Return summary statistics dict."""
        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_speaker: dict[str, int] = {}

        for c in contradictions:
            by_type[c.contradiction_type] = by_type.get(c.contradiction_type, 0) + 1
            by_severity[c.severity] = by_severity.get(c.severity, 0) + 1
            speaker = c.statement_a.original.speaker
            by_speaker[speaker] = by_speaker.get(speaker, 0) + 1

        return {
            "total": len(contradictions),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_speaker": by_speaker,
            "avg_severity_score": (
                sum(c.severity_score for c in contradictions) / len(contradictions)
                if contradictions else 0.0
            ),
        }

    # ------------------------------------------------------------------
    # Markdown renderer
    # ------------------------------------------------------------------

    def _render_markdown(self, cs: list[ScoredContradiction]) -> str:
        parts: list[str] = []
        parts.append("# Contradiction Analysis Report")
        parts.append(f"*Generated: {datetime.now().isoformat()}*\n")

        # Summary
        stats = self.summary_stats(cs)
        parts.append("## Summary")
        parts.append(f"- **Total contradictions:** {stats['total']}")
        parts.append(f"- **Average severity score:** {stats['avg_severity_score']:.1f}")
        for sev, cnt in sorted(stats["by_severity"].items()):
            parts.append(f"- {sev}: {cnt}")
        parts.append("")

        # Individual contradictions
        for idx, c in enumerate(cs, start=1):
            a = c.statement_a.original
            b = c.statement_b.original
            parts.append(f"## Contradiction #{idx} [{c.severity}]")
            parts.append("")
            parts.append("```")
            parts.append(
                f"┌{'─' * 40}┬{'─' * 40}┐"
            )
            parts.append(
                f"│ {'Statement A':<38} │ {'Statement B':<38} │"
            )
            parts.append(
                f"│ Source: {(a.source_file or 'N/A')[:30]:<30} │ "
                f"Source: {(b.source_file or 'N/A')[:30]:<30} │"
            )
            parts.append(
                f"│ Date: {(c.statement_a.date_normalized or 'N/A'):<32} │ "
                f"Date: {(c.statement_b.date_normalized or 'N/A'):<32} │"
            )
            # Wrap text to ~36 chars
            a_text = self._wrap(a.text, 36)
            b_text = self._wrap(b.text, 36)
            max_lines = max(len(a_text), len(b_text))
            for line_i in range(max_lines):
                left = a_text[line_i] if line_i < len(a_text) else ""
                right = b_text[line_i] if line_i < len(b_text) else ""
                parts.append(f"│ \"{left:<36}\" │ \"{right:<36}\" │")
            parts.append(
                f"└{'─' * 40}┴{'─' * 40}┘"
            )
            parts.append("```")
            parts.append(
                f"**Type:** {c.contradiction_type} | "
                f"**Impeachment Value:** {c.impeachment_value} | "
                f"**Score:** {c.severity_score}"
            )
            parts.append(f"**Explanation:** {c.explanation}")
            parts.append("")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # JSON renderer
    # ------------------------------------------------------------------

    def _render_json(self, cs: list[ScoredContradiction]) -> str:
        out: list[dict] = []
        for c in cs:
            out.append(self.generate_exhibit(c))
        return json.dumps(
            {"report": out, "stats": self.summary_stats(cs)},
            indent=2, default=str,
        )

    # ------------------------------------------------------------------
    # HTML renderer
    # ------------------------------------------------------------------

    def _render_html(self, cs: list[ScoredContradiction]) -> str:
        stats = self.summary_stats(cs)
        rows_html: list[str] = []
        for idx, c in enumerate(cs, start=1):
            a = c.statement_a.original
            b = c.statement_b.original
            color = {"CRITICAL": "#ff4444", "MAJOR": "#ff8800", "MINOR": "#ffcc00"}.get(
                c.severity, "#cccccc",
            )
            rows_html.append(
                f"<tr style='border-left:4px solid {color}'>"
                f"<td>{idx}</td>"
                f"<td>{c.severity} ({c.severity_score})</td>"
                f"<td>{a.text[:80]}…</td>"
                f"<td>{b.text[:80]}…</td>"
                f"<td>{c.contradiction_type}</td>"
                f"<td>{c.impeachment_value}</td>"
                f"</tr>"
            )
        return (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            "<title>Contradiction Report</title>"
            "<style>body{font-family:sans-serif;margin:20px}"
            "table{border-collapse:collapse;width:100%}"
            "th,td{padding:8px;border:1px solid #ddd;text-align:left}"
            "th{background:#333;color:#fff}</style></head><body>"
            f"<h1>Contradiction Report</h1>"
            f"<p>Total: {stats['total']} | "
            f"Avg Score: {stats['avg_severity_score']:.1f}</p>"
            "<table><tr><th>#</th><th>Severity</th>"
            "<th>Statement A</th><th>Statement B</th>"
            "<th>Type</th><th>Impeachment</th></tr>"
            + "\n".join(rows_html)
            + "</table></body></html>"
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        """Wrap text to *width* chars per line."""
        words = text.split()
        lines: list[str] = []
        current = ""
        for w in words:
            if len(current) + len(w) + 1 > width:
                lines.append(current)
                current = w
            else:
                current = f"{current} {w}" if current else w
        if current:
            lines.append(current)
        return lines or [""]
