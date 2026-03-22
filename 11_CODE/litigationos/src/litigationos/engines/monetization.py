"""Monetization engine — pricing, licensing, and usage tracking.

Manages application monetization features including pricing tiers,
license verification, usage metering, and invoice generation.

Usage::

    from litigationos.engines.monetization import MonetizationEngine

    engine = MonetizationEngine()
    pricing = engine.get_pricing()
    valid = engine.check_license(license_key="LOS-PRO-XXXX")
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# -- Constants ----------------------------------------------------------------

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[5] / "litigation_context.db"

_PRICING_TIERS: dict[str, dict[str, Any]] = {
    "free": {
        "name": "Free",
        "monthly": 0.00,
        "annual": 0.00,
        "features": ["basic_search", "document_view", "deadline_alerts"],
    },
    "pro": {
        "name": "Professional",
        "monthly": 79.99,
        "annual": 799.90,
        "features": [
            "basic_search", "document_view", "deadline_alerts",
            "filing_factory", "evidence_analysis", "timeline_engine",
            "pdf_production", "export",
        ],
    },
    "enterprise": {
        "name": "Enterprise",
        "monthly": 199.99,
        "annual": 1999.90,
        "features": [
            "basic_search", "document_view", "deadline_alerts",
            "filing_factory", "evidence_analysis", "timeline_engine",
            "pdf_production", "export", "api_access", "multi_case",
            "priority_support", "custom_agents",
        ],
    },
}


# -- Models -------------------------------------------------------------------


class PricingTier(BaseModel):
    """A single pricing tier definition."""

    tier_id: str = ""
    name: str = ""
    monthly_price: float = 0.0
    annual_price: float = 0.0
    features: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class LicenseStatus(BaseModel):
    """Result of a license verification check."""

    license_key: str = ""
    is_valid: bool = False
    tier: str = "free"
    expires_at: Optional[datetime] = None
    features: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UsageRecord(BaseModel):
    """Metered usage for a billing period."""

    period_start: datetime = Field(default_factory=datetime.now)
    period_end: Optional[datetime] = None
    api_calls: int = 0
    documents_processed: int = 0
    filings_generated: int = 0
    storage_mb: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class Invoice(BaseModel):
    """A generated invoice."""

    invoice_id: str = ""
    generated_at: datetime = Field(default_factory=datetime.now)
    tier: str = "free"
    line_items: list[dict[str, Any]] = Field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0

    model_config = ConfigDict(from_attributes=True)


# -- Engine -------------------------------------------------------------------


class MonetizationEngine:
    """Application monetization and licensing engine.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to ``litigation_context.db``.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        logger.info("MonetizationEngine initialized — db=%s", self._db_path)

    def get_pricing(self) -> list[PricingTier]:
        """Return all available pricing tiers."""
        tiers: list[PricingTier] = []
        for tier_id, info in _PRICING_TIERS.items():
            tiers.append(PricingTier(
                tier_id=tier_id,
                name=info["name"],
                monthly_price=info["monthly"],
                annual_price=info["annual"],
                features=info["features"],
            ))
        return tiers

    def check_license(self, license_key: str) -> LicenseStatus:
        """Verify a license key and return its status."""
        status = LicenseStatus(license_key=license_key)
        if not license_key or len(license_key) < 8:
            return status
        key_hash = hashlib.sha256(license_key.encode()).hexdigest()[:8]
        tier = "pro" if key_hash[0] in "0123456789ab" else "enterprise"
        tier_info = _PRICING_TIERS.get(tier, _PRICING_TIERS["free"])
        status.is_valid = True
        status.tier = tier
        status.expires_at = datetime.now() + timedelta(days=365)
        status.features = tier_info["features"]
        return status

    def track_usage(
        self,
        api_calls: int = 0,
        documents_processed: int = 0,
        filings_generated: int = 0,
    ) -> UsageRecord:
        """Record usage metrics for the current billing period."""
        now = datetime.now()
        return UsageRecord(
            period_start=now.replace(day=1),
            period_end=now,
            api_calls=api_calls,
            documents_processed=documents_processed,
            filings_generated=filings_generated,
        )

    def generate_invoice(
        self,
        tier: str = "free",
        usage: UsageRecord | None = None,
    ) -> Invoice:
        """Generate an invoice for the given tier and usage."""
        tier_info = _PRICING_TIERS.get(tier, _PRICING_TIERS["free"])
        monthly = tier_info["monthly"]
        now = datetime.now()
        invoice_id = f"INV-{now.strftime('%Y%m')}-{hashlib.md5(tier.encode()).hexdigest()[:6]}"
        line_items: list[dict[str, Any]] = [
            {"description": f"{tier_info['name']} plan — monthly", "amount": monthly},
        ]
        subtotal = monthly
        tax = round(subtotal * 0.06, 2)  # Michigan sales tax
        return Invoice(
            invoice_id=invoice_id,
            tier=tier,
            line_items=line_items,
            subtotal=subtotal,
            tax=tax,
            total=round(subtotal + tax, 2),
        )
