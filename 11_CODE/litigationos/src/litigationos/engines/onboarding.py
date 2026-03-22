"""Onboarding engine — guided user setup and checklist management.

Manages the first-run onboarding workflow for LitigationOS, including
step tracking, checklist generation, and progress persistence.

Usage::

    from litigationos.engines.onboarding import OnboardingEngine

    engine = OnboardingEngine()
    status = engine.get_onboarding_status()
    engine.complete_step("connect_database")
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# -- Constants ----------------------------------------------------------------

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[5] / "litigation_context.db"

_SQLITE_PRAGMAS = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA synchronous=NORMAL",
)

_DEFAULT_STEPS: list[dict[str, Any]] = [
    {
        "step_id": "connect_database",
        "title": "Connect litigation database",
        "description": "Point LitigationOS at your litigation_context.db",
        "order": 1,
        "required": True,
    },
    {
        "step_id": "scan_drives",
        "title": "Scan evidence drives",
        "description": "Run the drive scanner to index evidence across all drives",
        "order": 2,
        "required": True,
    },
    {
        "step_id": "set_case_info",
        "title": "Enter case information",
        "description": "Configure case numbers, court, and party details",
        "order": 3,
        "required": True,
    },
    {
        "step_id": "configure_lanes",
        "title": "Configure case lanes",
        "description": "Set up the six case lanes (A through F) for routing",
        "order": 4,
        "required": False,
    },
    {
        "step_id": "import_deadlines",
        "title": "Import deadlines",
        "description": "Import existing deadlines from the database or calendar",
        "order": 5,
        "required": False,
    },
    {
        "step_id": "review_filings",
        "title": "Review filing readiness",
        "description": "Check the filing readiness dashboard for pending vehicles",
        "order": 6,
        "required": False,
    },
]


# -- Models -------------------------------------------------------------------


class OnboardingStep(BaseModel):
    """A single onboarding step."""

    step_id: str = ""
    title: str = ""
    description: str = ""
    order: int = 0
    required: bool = False
    completed: bool = False
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingStatus(BaseModel):
    """Overall onboarding progress."""

    is_complete: bool = False
    steps_total: int = 0
    steps_completed: int = 0
    required_remaining: int = 0
    progress_pct: float = 0.0
    steps: list[OnboardingStep] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# -- Engine -------------------------------------------------------------------


class OnboardingEngine:
    """User onboarding flow engine.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to ``litigation_context.db``.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        self._completed: set[str] = set()
        logger.info("OnboardingEngine initialized — db=%s", self._db_path)

    def _build_steps(self) -> list[OnboardingStep]:
        """Build the step list with current completion state."""
        steps: list[OnboardingStep] = []
        for defn in _DEFAULT_STEPS:
            step = OnboardingStep(
                step_id=defn["step_id"],
                title=defn["title"],
                description=defn["description"],
                order=defn["order"],
                required=defn["required"],
                completed=defn["step_id"] in self._completed,
            )
            steps.append(step)
        return steps

    def get_onboarding_status(self) -> OnboardingStatus:
        """Return the current onboarding progress."""
        steps = self._build_steps()
        completed = sum(1 for s in steps if s.completed)
        required_remaining = sum(1 for s in steps if s.required and not s.completed)
        total = len(steps)
        return OnboardingStatus(
            is_complete=required_remaining == 0,
            steps_total=total,
            steps_completed=completed,
            required_remaining=required_remaining,
            progress_pct=round(completed / total * 100, 1) if total else 0.0,
            steps=steps,
        )

    def complete_step(self, step_id: str) -> OnboardingStep | None:
        """Mark a step as completed.  Returns the step or ``None``."""
        valid_ids = {d["step_id"] for d in _DEFAULT_STEPS}
        if step_id not in valid_ids:
            logger.warning("Unknown onboarding step: %s", step_id)
            return None
        self._completed.add(step_id)
        for defn in _DEFAULT_STEPS:
            if defn["step_id"] == step_id:
                return OnboardingStep(
                    step_id=step_id,
                    title=defn["title"],
                    description=defn["description"],
                    order=defn["order"],
                    required=defn["required"],
                    completed=True,
                    completed_at=datetime.now(),
                )
        return None

    def get_checklist(self) -> list[OnboardingStep]:
        """Return the full ordered checklist."""
        return sorted(self._build_steps(), key=lambda s: s.order)

    def reset_onboarding(self) -> OnboardingStatus:
        """Reset all onboarding progress."""
        self._completed.clear()
        logger.info("Onboarding progress reset")
        return self.get_onboarding_status()
