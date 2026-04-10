"""
Court-ready output formatter for the Chronological Narrative Engine.

Produces Statement of Facts sections formatted for:
  - Michigan Circuit Court
  - Michigan Court of Appeals / Supreme Court
  - Federal District Court (42 USC § 1983)
  - Emergency motions
"""

import logging
from datetime import date
from typing import List, Optional

from .models import NarrativeEvent, SEPARATION_DATE

logger = logging.getLogger(__name__)


class NarrativeFormatter:
    """Formats narrative output for different court filings."""

    # ------------------------------------------------------------------
    # Michigan Circuit Court
    # ------------------------------------------------------------------

    def format_circuit_court(
        self,
        narrative_events: List[NarrativeEvent],
        title: str = "STATEMENT OF FACTS",
    ) -> str:
        """Michigan Circuit Court format: numbered paragraphs, record citations."""
        if not narrative_events:
            return f"{title}\n\n    No events to present.\n"

        sep_days = (date.today() - SEPARATION_DATE).days
        lines: list[str] = [title, ""]

        for idx, ev in enumerate(narrative_events, start=1):
            para = self._build_paragraph(idx, ev)
            lines.append(para)
            lines.append("")

        lines.append(self._separation_paragraph(sep_days))
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Michigan Court of Appeals / Supreme Court
    # ------------------------------------------------------------------

    def format_appellate(
        self,
        narrative_events: List[NarrativeEvent],
        title: str = "STATEMENT OF FACTS",
    ) -> str:
        """COA/MSC format: record page citations required.

        Each factual assertion includes a lower court record reference
        in the form (Record, p XX) or (Exhibit X, p XX).
        """
        if not narrative_events:
            return f"{title}\n\n    No events to present.\n"

        sep_days = (date.today() - SEPARATION_DATE).days
        lines: list[str] = [title, ""]

        for idx, ev in enumerate(narrative_events, start=1):
            text = ev.detailed_narrative or ev.event_summary

            # Build record citation
            record_cite = self._record_citation(ev)
            para = f"    {idx}. {text} {record_cite}"
            lines.append(para)
            lines.append("")

        lines.append(
            f"    As of the date of this filing, Appellant-Father has been "
            f"completely separated from the minor child, L.D.W., for "
            f"{sep_days} consecutive days, commencing July 29, 2025. "
            f"(Record, Emergency Motion, filed March 25, 2026.)"
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Federal District Court
    # ------------------------------------------------------------------

    def format_federal(
        self,
        narrative_events: List[NarrativeEvent],
        title: str = "FACTUAL ALLEGATIONS",
    ) -> str:
        """Federal complaint format: numbered paragraphs written to satisfy
        the Iqbal/Twombly plausibility standard.  Each paragraph begins with
        the date and names the actor whose conduct is challenged.
        """
        if not narrative_events:
            return f"{title}\n\n    No factual allegations to present.\n"

        sep_days = (date.today() - SEPARATION_DATE).days

        # Federal complaints use a running paragraph counter that
        # continues from the preceding sections, but here we start at 1
        # and the caller can offset.
        lines: list[str] = [title, ""]

        for idx, ev in enumerate(narrative_events, start=1):
            text = ev.detailed_narrative or ev.event_summary

            # Federal style: date-actor-conduct
            actor_str = ", ".join(ev.actors) if ev.actors else "Defendant"
            para = (
                f"    {idx}. On or about {self._fmt_date(ev.event_date)}, "
                f"{actor_str} {self._lowercase_first(text)}"
            )
            if ev.exhibit_refs:
                refs_str = "; ".join(ev.exhibit_refs)
                para += f" (See {refs_str}.)"
            elif not para.rstrip().endswith("."):
                para += "."
            lines.append(para)
            lines.append("")

        lines.append(
            f"    {len(narrative_events) + 1}. As a direct and proximate "
            f"result of the above actions, Plaintiff has been deprived of "
            f"all contact with his minor child, L.D.W., for {sep_days} "
            f"consecutive days as of the date of this Complaint, in "
            f"violation of the Fourteenth Amendment to the United States "
            f"Constitution."
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Emergency Motion
    # ------------------------------------------------------------------

    def format_emergency(
        self,
        narrative_events: List[NarrativeEvent],
        title: str = "VERIFIED STATEMENT OF FACTS",
    ) -> str:
        """Emergency motion format: concise, urgency-focused, separation counter.

        Leads with the current separation count, then presents facts in
        tight numbered paragraphs emphasizing irreparable harm.
        """
        if not narrative_events:
            return f"{title}\n\n    No events to present.\n"

        sep_days = (date.today() - SEPARATION_DATE).days
        lines: list[str] = [title, ""]

        # Urgency header
        lines.append(
            f"    1. THIS IS AN EMERGENCY. Plaintiff-Father, Andrew James "
            f"Pigors, appearing pro se, has had zero contact with his minor "
            f"child, L.D.W. (DOB: November 9, 2022), for {sep_days} "
            f"consecutive days — since July 29, 2025. Each passing day "
            f"inflicts irreparable harm on the parent-child bond."
        )
        lines.append("")

        for idx, ev in enumerate(narrative_events, start=2):
            text = ev.detailed_narrative or ev.event_summary
            severity_marker = " [CRITICAL]" if ev.severity == "critical" else ""
            para = f"    {idx}. {text}{severity_marker}"
            if ev.exhibit_refs:
                refs_str = "; ".join(ev.exhibit_refs)
                para += f" ({refs_str}.)"
            lines.append(para)
            lines.append("")

        closing_idx = len(narrative_events) + 2
        lines.append(
            f"    {closing_idx}. Plaintiff, appearing pro se, respectfully "
            f"states under penalty of perjury that the foregoing facts are "
            f"true and correct to the best of his knowledge, information, "
            f"and belief."
        )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _separation_paragraph(sep_days: int) -> str:
        """Build the closing separation counter paragraph."""
        return (
            f"    As of the date of this filing, Plaintiff-Father has been "
            f"completely separated from the minor child, L.D.W., for "
            f"{sep_days} consecutive days — since July 29, 2025."
        )

    @staticmethod
    def _build_paragraph(idx: int, ev: NarrativeEvent) -> str:
        """Build a numbered paragraph for circuit court format."""
        text = ev.detailed_narrative or ev.event_summary
        para = f"    {idx}. {text}"
        if ev.exhibit_refs:
            refs_str = "; ".join(ev.exhibit_refs)
            para += f" ({refs_str}.)"
        return para

    @staticmethod
    def _record_citation(ev: NarrativeEvent) -> str:
        """Build a lower court record citation for appellate format."""
        parts: list[str] = []
        if ev.exhibit_refs:
            for ref in ev.exhibit_refs[:2]:
                parts.append(ref)
        if ev.timeline_event_ids:
            parts.append(f"Timeline ID{'s' if len(ev.timeline_event_ids) > 1 else ''} "
                         f"{', '.join(ev.timeline_event_ids[:3])}")
        if parts:
            return f"({'; '.join(parts)}.)"
        return "(Record citation to be supplemented.)"

    @staticmethod
    def _fmt_date(iso_date: str) -> str:
        """Format ISO date as 'Month Day, Year'."""
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ]
        try:
            parts = iso_date[:10].split("-")
            y, m, d = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{months[m - 1]} {d}, {y}"
        except (ValueError, IndexError):
            return iso_date

    @staticmethod
    def _lowercase_first(text: str) -> str:
        """Lowercase the first character only if the text doesn't start
        with a proper noun indicator (uppercase + lowercase pattern)."""
        if not text:
            return text
        # Keep uppercase if it looks like a proper noun / acronym
        if len(text) > 1 and text[0].isupper() and text[1].islower():
            # Likely a sentence start — leave as-is for readability
            return text
        return text
