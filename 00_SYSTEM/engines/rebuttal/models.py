"""Data models for judicial rebuttals."""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


class RebuttalSeverity(enum.StrEnum):
    """Severity of the false judicial finding."""
    CRITICAL = "CRITICAL"  # Directly caused custody/PT deprivation
    HIGH = "HIGH"          # Significantly prejudiced case outcome
    MEDIUM = "MEDIUM"      # Contributed to negative perception
    LOW = "LOW"            # Minor mischaracterization


class StatementCategory(enum.StrEnum):
    """Category of the false judicial statement."""
    VIOLENCE = "violence"
    CREDIBILITY = "credibility"
    FITNESS = "fitness"
    NEGLECT = "neglect"
    CUSTODY_RULING = "custody_ruling"
    PARENTING_TIME = "parenting_time"
    FACTOR_FINDING = "factor_finding"
    DUE_PROCESS = "due_process"
    PROCEDURAL = "procedural"
    EX_PARTE = "ex_parte"
    PPO = "ppo"
    ALIENATION = "alienation"
    GENERAL = "general"


SEVERITY_RANK = {
    RebuttalSeverity.CRITICAL: 4,
    RebuttalSeverity.HIGH: 3,
    RebuttalSeverity.MEDIUM: 2,
    RebuttalSeverity.LOW: 1,
}

LAST_CONTACT = date(2025, 7, 29)


@dataclass(frozen=True, slots=True)
class JudicialRebuttal:
    """A single rebuttal to a false judicial finding."""
    id: int
    order_date: Optional[str]
    order_description: Optional[str]
    false_statement: str
    statement_context: Optional[str]
    statement_category: str
    truth: str
    rebuttal_narrative: Optional[str]
    evidence_refs: Optional[str]
    legal_basis: Optional[str]
    standard_of_review: Optional[str]
    appellate_argument: Optional[str]
    severity: str
    best_interest_factor: Optional[str]
    lane: str
    filing_use: Optional[str]
    tags: Optional[str]
    source_table: Optional[str]
    source_id: Optional[int]
    created_at: Optional[str] = None
    is_active: int = 1

    @property
    def severity_rank(self) -> int:
        try:
            return SEVERITY_RANK[RebuttalSeverity(self.severity)]
        except (ValueError, KeyError):
            return 0

    @property
    def separation_days(self) -> int:
        return (date.today() - LAST_CONTACT).days

    def to_irac(self) -> str:
        """Format as IRAC paragraph for filing."""
        parts = []
        stmt_excerpt = self.false_statement[:200]
        parts.append(
            f'ISSUE: Whether the trial court\'s finding that '
            f'"{stmt_excerpt}..." constitutes clear error.'
        )
        parts.append("")
        basis = self.legal_basis or "MCR 2.613(C) -- clear error standard"
        parts.append(f"RULE: {basis}")
        parts.append("")
        parts.append(f"APPLICATION: {self.truth}")
        if self.evidence_refs:
            parts.append(f"(See {self.evidence_refs})")
        parts.append("")
        parts.append(f"CONCLUSION: The trial court's finding was clearly erroneous "
                     f"and should be reversed.")
        return "\n".join(parts)
