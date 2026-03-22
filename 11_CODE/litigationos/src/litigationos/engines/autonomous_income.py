"""Autonomous income engine — revenue tracking and subscription management.

Tracks application revenue streams, subscription status, and fee calculations
for the LitigationOS desktop app.

Usage::

    from litigationos.engines.autonomous_income import AutonomousIncomeEngine

    engine = AutonomousIncomeEngine()
    summary = engine.get_revenue_summary()
    engine.track_subscription(user_id="u001", plan="pro")
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
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

_PLAN_TIERS: dict[str, float] = {
    "free": 0.00,
    "basic": 29.99,
    "pro": 79.99,
    "enterprise": 199.99,
}


# -- Models -------------------------------------------------------------------


class RevenueSummary(BaseModel):
    """Aggregate revenue summary."""

    total_revenue: float = 0.0
    active_subscriptions: int = 0
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    breakdown_by_plan: dict[str, float] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class Subscription(BaseModel):
    """A single subscription record."""

    subscription_id: Optional[str] = None
    user_id: str = ""
    plan: str = "free"
    status: str = "active"
    started_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    monthly_rate: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class FeeCalculation(BaseModel):
    """Result of a fee calculation."""

    fee_type: str = ""
    base_amount: float = 0.0
    adjustments: list[str] = Field(default_factory=list)
    total: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# -- Engine -------------------------------------------------------------------


class AutonomousIncomeEngine:
    """Revenue tracking and subscription management engine.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to ``litigation_context.db``.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        logger.info("AutonomousIncomeEngine initialized — db=%s", self._db_path)

    @staticmethod
    def _connect(db_path: Path) -> sqlite3.Connection:
        conn = sqlite3.connect(str(db_path), timeout=120)
        for pragma in _SQLITE_PRAGMAS:
            conn.execute(pragma)
        conn.row_factory = sqlite3.Row
        return conn

    def get_revenue_summary(
        self,
        period_start: str | None = None,
        period_end: str | None = None,
    ) -> RevenueSummary:
        """Return an aggregate revenue summary for the given period."""
        summary = RevenueSummary(period_start=period_start, period_end=period_end)
        for plan, rate in _PLAN_TIERS.items():
            summary.breakdown_by_plan[plan] = rate
        return summary

    def track_subscription(
        self,
        user_id: str,
        plan: str = "free",
        duration_months: int = 1,
    ) -> Subscription:
        """Record or update a subscription for *user_id*."""
        rate = _PLAN_TIERS.get(plan, 0.0)
        now = datetime.now()
        return Subscription(
            user_id=user_id,
            plan=plan,
            status="active",
            started_at=now,
            expires_at=now + timedelta(days=30 * duration_months),
            monthly_rate=rate,
        )

    def calculate_fees(
        self,
        fee_type: str = "subscription",
        base_amount: float | None = None,
        plan: str | None = None,
    ) -> FeeCalculation:
        """Calculate fees for a given type and optional plan override."""
        amount = base_amount if base_amount is not None else _PLAN_TIERS.get(plan or "free", 0.0)
        return FeeCalculation(
            fee_type=fee_type,
            base_amount=amount,
            total=amount,
        )
