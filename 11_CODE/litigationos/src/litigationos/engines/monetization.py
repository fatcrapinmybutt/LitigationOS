"""Monetization infrastructure for LitigationOS.

Provides subscription management, usage tracking, tier-based feature gating,
and payment integration stubs for Stripe. This module handles the business
logic for Free/Pro/Enterprise tiers and per-filing charges.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


# ── Subscription tiers ───────────────────────────────────────────────────────

class SubscriptionTier(str, Enum):
    """Available subscription tiers."""

    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


TIER_LIMITS = {
    SubscriptionTier.FREE: {
        "cases": 2,
        "filings_per_month": 5,
        "evidence_items": 100,
        "ai_queries_per_day": 20,
        "jurisdictions": 1,
        "export_pdf": False,
        "api_access": False,
        "white_label": False,
        "price_monthly": 0,
        "price_annual": 0,
    },
    SubscriptionTier.PRO: {
        "cases": 25,
        "filings_per_month": 100,
        "evidence_items": 10_000,
        "ai_queries_per_day": 500,
        "jurisdictions": 5,
        "export_pdf": True,
        "api_access": True,
        "white_label": False,
        "price_monthly": 49_00,  # cents
        "price_annual": 470_00,
    },
    SubscriptionTier.ENTERPRISE: {
        "cases": -1,  # unlimited
        "filings_per_month": -1,
        "evidence_items": -1,
        "ai_queries_per_day": -1,
        "jurisdictions": -1,
        "export_pdf": True,
        "api_access": True,
        "white_label": True,
        "price_monthly": 199_00,
        "price_annual": 1990_00,
    },
}


# ── Models ───────────────────────────────────────────────────────────────────

class Subscription(BaseModel):
    """A user's active subscription."""

    id: Optional[int] = None
    user_id: int
    tier: SubscriptionTier = SubscriptionTier.FREE
    status: str = "active"  # active, cancelled, past_due, trialing
    started_at: Optional[datetime] = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @property
    def is_active(self) -> bool:
        if self.status != "active":
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

    @property
    def limits(self) -> dict:
        return TIER_LIMITS[self.tier]


class UsageRecord(BaseModel):
    """Track feature usage for billing and limit enforcement."""

    user_id: int
    feature: str  # cases, filings, ai_queries, evidence
    count: int = 0
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FilingCharge(BaseModel):
    """Per-filing charge for premium filing types."""

    filing_id: int
    user_id: int
    amount_cents: int
    description: str
    charged: bool = False
    stripe_charge_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ── Monetization Engine ──────────────────────────────────────────────────────

class MonetizationEngine:
    """Manages subscriptions, usage tracking, and feature gating."""

    TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tier TEXT NOT NULL DEFAULT 'free',
        status TEXT NOT NULL DEFAULT 'active',
        started_at TEXT NOT NULL DEFAULT (datetime('now')),
        expires_at TEXT,
        stripe_customer_id TEXT,
        stripe_subscription_id TEXT,
        UNIQUE(user_id)
    );
    CREATE TABLE IF NOT EXISTS usage_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        feature TEXT NOT NULL,
        count INTEGER NOT NULL DEFAULT 0,
        period_start TEXT NOT NULL,
        period_end TEXT NOT NULL,
        UNIQUE(user_id, feature, period_start)
    );
    CREATE TABLE IF NOT EXISTS filing_charges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filing_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        amount_cents INTEGER NOT NULL,
        description TEXT,
        charged INTEGER NOT NULL DEFAULT 0,
        stripe_charge_id TEXT,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """

    def __init__(self, db: "DatabaseManager"):
        self._db = db
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        for stmt in self.TABLE_DDL.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    self._db.execute(stmt)
                except Exception:
                    pass  # tables may exist

    # ── Subscription management ──────────────────────────────────────────────

    def get_subscription(self, user_id: int) -> Subscription:
        """Get or create a subscription for a user (defaults to FREE)."""
        row = self._db.fetchone(
            "SELECT * FROM subscriptions WHERE user_id = ?", (user_id,),
        )
        if row:
            data = dict(row)
            data["tier"] = SubscriptionTier(data["tier"])
            return Subscription(**data)

        # Auto-create free tier
        sub = Subscription(user_id=user_id, tier=SubscriptionTier.FREE)
        self._db.execute(
            "INSERT INTO subscriptions (user_id, tier, status) VALUES (?, ?, ?)",
            (user_id, sub.tier.value, sub.status),
        )
        logger.info("Created FREE subscription for user %d", user_id)
        return sub

    def upgrade_tier(self, user_id: int, new_tier: SubscriptionTier) -> Subscription:
        """Upgrade a user's subscription tier."""
        self._db.execute(
            "UPDATE subscriptions SET tier = ?, status = 'active', "
            "started_at = datetime('now') WHERE user_id = ?",
            (new_tier.value, user_id),
        )
        logger.info("Upgraded user %d to %s", user_id, new_tier.value)
        return self.get_subscription(user_id)

    def cancel_subscription(self, user_id: int) -> None:
        """Cancel a subscription (reverts to FREE at period end)."""
        self._db.execute(
            "UPDATE subscriptions SET status = 'cancelled' WHERE user_id = ?",
            (user_id,),
        )
        logger.info("Cancelled subscription for user %d", user_id)

    # ── Feature gating ───────────────────────────────────────────────────────

    def check_limit(self, user_id: int, feature: str) -> dict:
        """Check if a user is within their tier limits for a feature.

        Returns: {allowed: bool, current: int, limit: int, tier: str}
        """
        sub = self.get_subscription(user_id)
        limits = sub.limits
        limit_value = limits.get(feature, 0)

        # Unlimited
        if limit_value == -1:
            return {"allowed": True, "current": 0, "limit": -1, "tier": sub.tier.value}

        # Boolean features
        if isinstance(limit_value, bool):
            return {"allowed": limit_value, "current": 0, "limit": 0, "tier": sub.tier.value}

        # Count-based features
        current = self._get_usage_count(user_id, feature)
        allowed = current < limit_value

        if not allowed:
            logger.warning(
                "User %d hit %s limit: %d/%d (%s tier)",
                user_id, feature, current, limit_value, sub.tier.value,
            )

        return {
            "allowed": allowed,
            "current": current,
            "limit": limit_value,
            "tier": sub.tier.value,
        }

    def increment_usage(self, user_id: int, feature: str, amount: int = 1) -> None:
        """Record usage of a feature."""
        now = datetime.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0).isoformat()
        period_end = (now.replace(day=1) + timedelta(days=32)).replace(day=1).isoformat()

        existing = self._db.fetchone(
            "SELECT * FROM usage_records WHERE user_id = ? AND feature = ? AND period_start = ?",
            (user_id, feature, period_start),
        )
        if existing:
            self._db.execute(
                "UPDATE usage_records SET count = count + ? "
                "WHERE user_id = ? AND feature = ? AND period_start = ?",
                (amount, user_id, feature, period_start),
            )
        else:
            self._db.execute(
                "INSERT INTO usage_records (user_id, feature, count, period_start, period_end) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, feature, amount, period_start, period_end),
            )

    def _get_usage_count(self, user_id: int, feature: str) -> int:
        """Get current period usage count."""
        period_start = datetime.now().replace(day=1, hour=0, minute=0, second=0).isoformat()
        row = self._db.fetchone(
            "SELECT count FROM usage_records "
            "WHERE user_id = ? AND feature = ? AND period_start = ?",
            (user_id, feature, period_start),
        )
        return dict(row)["count"] if row else 0

    # ── Per-filing charges ───────────────────────────────────────────────────

    def create_filing_charge(
        self, filing_id: int, user_id: int, amount_cents: int, description: str
    ) -> int:
        """Create a per-filing charge (e.g., $5 for premium filing generation)."""
        cursor = self._db.execute(
            "INSERT INTO filing_charges (filing_id, user_id, amount_cents, description) "
            "VALUES (?, ?, ?, ?)",
            (filing_id, user_id, amount_cents, description),
        )
        logger.info("Created $%.2f charge for filing %d", amount_cents / 100, filing_id)
        return cursor.lastrowid

    def get_pending_charges(self, user_id: int) -> list[dict]:
        """Get all uncharged filing charges for a user."""
        rows = self._db.fetchall(
            "SELECT * FROM filing_charges WHERE user_id = ? AND charged = 0",
            (user_id,),
        )
        return [dict(r) for r in rows]

    def get_revenue_summary(self) -> dict:
        """Get total revenue summary across all users."""
        row = self._db.fetchone("""
            SELECT
                (SELECT COUNT(*) FROM subscriptions WHERE status = 'active') as active_subs,
                (SELECT COUNT(*) FROM subscriptions WHERE tier = 'pro') as pro_count,
                (SELECT COUNT(*) FROM subscriptions WHERE tier = 'enterprise') as enterprise_count,
                (SELECT COALESCE(SUM(amount_cents), 0) FROM filing_charges WHERE charged = 1) as total_charges,
                (SELECT COUNT(*) FROM filing_charges WHERE charged = 0) as pending_charges
        """)
        return dict(row) if row else {}

    # ── Stripe integration stubs ─────────────────────────────────────────────

    def create_stripe_checkout(self, user_id: int, tier: SubscriptionTier) -> str:
        """Create a Stripe checkout session URL (stub — returns placeholder)."""
        logger.info("Stripe checkout requested for user %d, tier %s", user_id, tier.value)
        price = TIER_LIMITS[tier]["price_monthly"]
        return f"https://checkout.stripe.com/placeholder?user={user_id}&tier={tier.value}&price={price}"

    def handle_stripe_webhook(self, event_type: str, payload: dict) -> None:
        """Handle incoming Stripe webhook events (stub)."""
        logger.info("Stripe webhook received: %s", event_type)
        # Future: process checkout.session.completed, invoice.paid, etc.

    # ── Tier comparison for UI ───────────────────────────────────────────────

    @staticmethod
    def get_tier_comparison() -> list[dict]:
        """Return tier comparison data for pricing page."""
        features = [
            ("Active Cases", "cases"),
            ("Filings per Month", "filings_per_month"),
            ("Evidence Items", "evidence_items"),
            ("AI Queries per Day", "ai_queries_per_day"),
            ("Jurisdictions", "jurisdictions"),
            ("PDF Export", "export_pdf"),
            ("API Access", "api_access"),
            ("White Label", "white_label"),
        ]
        comparison = []
        for label, key in features:
            row = {"feature": label}
            for tier in SubscriptionTier:
                val = TIER_LIMITS[tier][key]
                if val == -1:
                    row[tier.value] = "Unlimited"
                elif isinstance(val, bool):
                    row[tier.value] = "✅" if val else "❌"
                else:
                    row[tier.value] = str(val)
            comparison.append(row)
        return comparison
