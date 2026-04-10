"""
Rebuttal Formatter — produces court-ready rebuttal sections.

Supports: appellate brief, trial court motion, MSC application, exhibit format.
"""
from __future__ import annotations

from datetime import date
from typing import Optional

from .models import JudicialRebuttal, LAST_CONTACT


class RebuttalFormatter:
    """Formats rebuttals into court-ready document sections."""

    @staticmethod
    def separation_days() -> int:
        return (date.today() - LAST_CONTACT).days

    # ── Appellate Brief Section ─────────────────────────────
    @classmethod
    def appellate_brief_section(
        cls,
        rebuttals: list[JudicialRebuttal],
        section_title: str = "THE TRIAL COURT'S FINDINGS WERE CLEARLY ERRONEOUS",
    ) -> str:
        """Format rebuttals as an appellate brief argument section."""
        lines = [f"## {section_title}", ""]
        lines.append(
            "The trial court's findings of fact are reviewed for clear error. "
            "MCR 2.613(C). A finding is clearly erroneous when, although there "
            "is evidence to support it, the reviewing court is left with a "
            "definite and firm conviction that a mistake has been made. "
            "*Fletcher v Fletcher*, 447 Mich 871, 878 (1994)."
        )
        lines.append("")

        for i, r in enumerate(rebuttals, 1):
            lines.append(f"### {i}. {r.statement_category.replace('_', ' ').title()}"
                        f"{f' — Factor {r.best_interest_factor}' if r.best_interest_factor else ''}")
            lines.append("")
            stmt_text = r.false_statement[:500]
            lines.append(f'**The court found:** "{stmt_text}"')
            lines.append("")
            lines.append(f"**The record shows:** {r.truth}")
            lines.append("")
            if r.evidence_refs:
                lines.append(f"*(See {r.evidence_refs})*")
                lines.append("")
            if r.appellate_argument:
                lines.append(r.appellate_argument)
                lines.append("")
            if r.legal_basis:
                lines.append(f"**Authority:** {r.legal_basis}")
                lines.append("")

        sep = cls.separation_days()
        lines.append(f"As of the date of this filing, Father has been separated "
                     f"from L.D.W. for **{sep} consecutive days** — a deprivation "
                     f"that grows more harmful with each passing day.")
        return "\n".join(lines)

    # ── Trial Court Motion Section ──────────────────────────
    @classmethod
    def motion_section(
        cls,
        rebuttals: list[JudicialRebuttal],
        section_title: str = "FACTUAL ERRORS REQUIRING CORRECTION",
    ) -> str:
        """Format rebuttals as a motion argument section."""
        lines = [f"## {section_title}", ""]
        para = 1
        for r in rebuttals:
            stmt_text = r.false_statement[:400]
            lines.append(
                f'{para}. The Court previously found that '
                f'"{stmt_text}." This finding is '
                f'contradicted by the evidence, which shows: '
                f'{r.truth}'
            )
            if r.evidence_refs:
                lines.append(f"   (See {r.evidence_refs})")
            lines.append("")
            para += 1

        sep = cls.separation_days()
        lines.append(f"{para}. Father has now been denied all contact with "
                     f"L.D.W. for {sep} consecutive days. Each day of continued "
                     f"separation constitutes ongoing, irreparable harm to both "
                     f"Father and child.")
        return "\n".join(lines)

    # ── MSC Application Section ─────────────────────────────
    @classmethod
    def msc_section(
        cls,
        rebuttals: list[JudicialRebuttal],
        section_title: str = "PATTERN OF CLEARLY ERRONEOUS FINDINGS",
    ) -> str:
        """Format rebuttals for MSC superintending control application."""
        lines = [f"## {section_title}", ""]
        lines.append(
            "This Court's superintending control authority under Const 1963, "
            "art 6, § 4 and MCR 7.306 encompasses the power to correct "
            "systematic errors by lower courts. The pattern below demonstrates "
            "not isolated error but systemic bias warranting extraordinary relief."
        )
        lines.append("")

        critical = [r for r in rebuttals if r.severity == "CRITICAL"]
        high = [r for r in rebuttals if r.severity == "HIGH"]
        other = [r for r in rebuttals if r.severity not in ("CRITICAL", "HIGH")]

        if critical:
            lines.append("### Critical Errors (Directly Caused Custody Deprivation)")
            lines.append("")
            for r in critical:
                stmt = r.false_statement[:300]
                lines.append(f'- **Finding:** "{stmt}"')
                lines.append(f"  **Truth:** {r.truth[:300]}")
                if r.legal_basis:
                    lines.append(f"  **Authority:** {r.legal_basis}")
                lines.append("")

        if high:
            lines.append("### High-Impact Errors (Significantly Prejudiced Outcome)")
            lines.append("")
            for r in high:
                stmt = r.false_statement[:300]
                lines.append(f'- **Finding:** "{stmt}"')
                lines.append(f"  **Truth:** {r.truth[:300]}")
                lines.append("")

        sep = cls.separation_days()
        lines.append(f"The cumulative effect of these {len(rebuttals)} erroneous "
                     f"findings has been the complete severance of the father-child "
                     f"relationship for {sep} consecutive days — a deprivation "
                     f"that rises to the level of a constitutional violation.")
        return "\n".join(lines)

    # ── Exhibit Format ──────────────────────────────────────
    @classmethod
    def exhibit_table(cls, rebuttals: list[JudicialRebuttal]) -> str:
        """Format as a tabular exhibit for filing attachment."""
        lines = [
            "# EXHIBIT: JUDICIAL FALSE FINDINGS AND EVIDENCE-BASED REBUTTALS",
            "",
            f"Prepared: {date.today().strftime('%B %d, %Y')}",
            f"Separation from L.D.W.: {cls.separation_days()} days",
            "",
            "| # | Court Finding | Truth (Evidence-Based) | Authority | Factor |",
            "|---|--------------|----------------------|-----------|--------|",
        ]
        for i, r in enumerate(rebuttals, 1):
            stmt = r.false_statement[:120].replace("|", "\\|").replace("\n", " ")
            truth = r.truth[:120].replace("|", "\\|").replace("\n", " ")
            auth = (r.legal_basis or "")[:80].replace("|", "\\|")
            factor = r.best_interest_factor or ""
            lines.append(f"| {i} | {stmt} | {truth} | {auth} | {factor} |")
        return "\n".join(lines)
