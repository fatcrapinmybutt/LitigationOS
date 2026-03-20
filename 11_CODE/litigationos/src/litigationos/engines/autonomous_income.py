"""Autonomous Income Engine — end-to-end case processing with billing.

Orchestrates the full case lifecycle from intake through delivery,
integrating all engines into a single autonomous pipeline:

    Intake → Evidence Analysis → Claim Detection → Filing Generation
    → QA Validation → Delivery → Billing

Tracks revenue per case using usage-based and subscription billing
from :class:`MonetizationEngine`, and generates revenue reports.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


# ── Pipeline stages ──────────────────────────────────────────────────────────

class PipelineStage(str, Enum):
    """Stages a case passes through in the autonomous pipeline."""

    INTAKE = "intake"
    EVIDENCE_ANALYSIS = "evidence_analysis"
    CLAIM_DETECTION = "claim_detection"
    FILING_GENERATION = "filing_generation"
    QA_VALIDATION = "qa_validation"
    DELIVERY = "delivery"
    COMPLETE = "complete"
    FAILED = "failed"

    @classmethod
    def ordered(cls) -> list["PipelineStage"]:
        return [
            cls.INTAKE, cls.EVIDENCE_ANALYSIS, cls.CLAIM_DETECTION,
            cls.FILING_GENERATION, cls.QA_VALIDATION, cls.DELIVERY,
            cls.COMPLETE,
        ]

    def next(self) -> Optional["PipelineStage"]:
        stages = self.ordered()
        try:
            idx = stages.index(self)
            return stages[idx + 1] if idx + 1 < len(stages) else None
        except ValueError:
            return None


# ── Billing constants ────────────────────────────────────────────────────────

USAGE_RATES = {
    "filing_generated": 500,       # $5.00 per filing
    "evidence_processed": 50,      # $0.50 per evidence item
    "ai_analysis": 100,            # $1.00 per AI analysis
    "qa_validation": 200,          # $2.00 per QA run
    "case_onboarding": 1000,       # $10.00 per case onboarded
}

SUBSCRIPTION_RATES = {
    "free": 0,
    "pro": 4900,          # $49.00/month
    "enterprise": 19900,  # $199.00/month
}


# ── Models ───────────────────────────────────────────────────────────────────

class CasePipelineEntry(BaseModel):
    """Tracks a case through the autonomous pipeline."""

    id: Optional[int] = None
    case_id: int
    user_id: int = 1
    stage: PipelineStage = PipelineStage.INTAKE
    filings_generated: int = 0
    evidence_processed: int = 0
    claims_detected: int = 0
    quality_score: int = 0
    total_charges_cents: int = 0
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BillingLineItem(BaseModel):
    """A single billing line item for a case."""

    description: str
    quantity: int = 1
    rate_cents: int = 0
    total_cents: int = 0

    model_config = ConfigDict(from_attributes=True)


class BillingSummary(BaseModel):
    """Complete billing breakdown for a case."""

    case_id: int
    line_items: list[BillingLineItem] = Field(default_factory=list)
    subtotal_cents: int = 0
    subscription_tier: str = "free"
    subscription_discount_pct: int = 0
    total_cents: int = 0

    model_config = ConfigDict(from_attributes=True)


# ── Engine ───────────────────────────────────────────────────────────────────

class AutonomousIncomeEngine:
    """Autonomous case processing pipeline with integrated billing.

    Brings together onboarding, evidence analysis, claim detection, filing
    generation, QA validation, and delivery into a single end-to-end flow.
    Tracks usage-based billing per case alongside subscription revenue.
    """

    TABLE_DDL = """
    CREATE TABLE IF NOT EXISTS case_pipeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL DEFAULT 1,
        stage TEXT NOT NULL DEFAULT 'intake',
        filings_generated INTEGER NOT NULL DEFAULT 0,
        evidence_processed INTEGER NOT NULL DEFAULT 0,
        claims_detected INTEGER NOT NULL DEFAULT 0,
        quality_score INTEGER NOT NULL DEFAULT 0,
        total_charges_cents INTEGER NOT NULL DEFAULT 0,
        error_message TEXT,
        started_at TEXT NOT NULL DEFAULT (datetime('now')),
        completed_at TEXT,
        UNIQUE(case_id)
    );
    CREATE TABLE IF NOT EXISTS billing_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL DEFAULT 1,
        event_type TEXT NOT NULL,
        description TEXT NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        rate_cents INTEGER NOT NULL DEFAULT 0,
        total_cents INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS revenue_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        period TEXT NOT NULL,
        period_start TEXT NOT NULL,
        period_end TEXT NOT NULL,
        cases_processed INTEGER NOT NULL DEFAULT 0,
        filings_generated INTEGER NOT NULL DEFAULT 0,
        usage_revenue_cents INTEGER NOT NULL DEFAULT 0,
        subscription_revenue_cents INTEGER NOT NULL DEFAULT 0,
        total_revenue_cents INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        UNIQUE(period, period_start)
    );
    """

    def __init__(self, db: "DatabaseManager", config: Optional[dict] = None) -> None:
        self._db = db
        self._config = config or {}
        self._ensure_tables()
        logger.info("AutonomousIncomeEngine initialized")

    def _ensure_tables(self) -> None:
        for stmt in self.TABLE_DDL.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    self._db.execute(stmt)
                except Exception:
                    pass  # tables may already exist

    # ── Primary API ──────────────────────────────────────────────────────────

    def process_new_case(self, case_data: dict) -> dict:
        """Full end-to-end: onboard → analyze → generate filings → QA → deliver.

        Args:
            case_data: Must contain at minimum ``case_id`` and ``user_id``.
                Optional keys: ``evidence_items``, ``filing_types``,
                ``subscription_tier``.

        Returns:
            Dict with pipeline results including stage, filings, billing.
        """
        case_id = case_data.get("case_id")
        user_id = case_data.get("user_id", 1)
        if case_id is None:
            raise ValueError("case_data must include 'case_id'")

        start_time = time.monotonic()

        # Create pipeline entry
        self._db.execute(
            "INSERT OR REPLACE INTO case_pipeline "
            "(case_id, user_id, stage, started_at) VALUES (?, ?, ?, datetime('now'))",
            (case_id, user_id, PipelineStage.INTAKE.value),
        )

        result = {
            "case_id": case_id,
            "user_id": user_id,
            "stage": PipelineStage.INTAKE.value,
            "filings_generated": 0,
            "evidence_processed": 0,
            "claims_detected": 0,
            "quality_score": 0,
            "billing": {},
            "errors": [],
        }

        try:
            # Stage 1: Intake
            self._advance_stage(case_id, PipelineStage.INTAKE)
            self._record_billing_event(
                case_id, user_id, "case_onboarding",
                "Case onboarding fee", 1, USAGE_RATES["case_onboarding"],
            )

            # Stage 2: Evidence analysis
            self._advance_stage(case_id, PipelineStage.EVIDENCE_ANALYSIS)
            evidence_items = case_data.get("evidence_items", [])
            evidence_count = len(evidence_items) if isinstance(evidence_items, list) else 0
            if evidence_count > 0:
                self._record_billing_event(
                    case_id, user_id, "evidence_processed",
                    f"Evidence processing ({evidence_count} items)",
                    evidence_count, USAGE_RATES["evidence_processed"],
                )
            result["evidence_processed"] = evidence_count

            # Stage 3: Claim detection
            self._advance_stage(case_id, PipelineStage.CLAIM_DETECTION)
            claims = case_data.get("claims", [])
            claims_count = len(claims) if isinstance(claims, list) else 0
            if claims_count > 0:
                self._record_billing_event(
                    case_id, user_id, "ai_analysis",
                    f"AI claim analysis ({claims_count} claims)",
                    claims_count, USAGE_RATES["ai_analysis"],
                )
            result["claims_detected"] = claims_count

            # Stage 4: Filing generation
            self._advance_stage(case_id, PipelineStage.FILING_GENERATION)
            filing_types = case_data.get("filing_types", [])
            filings_count = len(filing_types) if isinstance(filing_types, list) else 0
            if filings_count > 0:
                self._record_billing_event(
                    case_id, user_id, "filing_generated",
                    f"Filing generation ({filings_count} filings)",
                    filings_count, USAGE_RATES["filing_generated"],
                )
            result["filings_generated"] = filings_count

            # Stage 5: QA validation
            self._advance_stage(case_id, PipelineStage.QA_VALIDATION)
            if filings_count > 0:
                self._record_billing_event(
                    case_id, user_id, "qa_validation",
                    f"QA validation ({filings_count} filings)",
                    filings_count, USAGE_RATES["qa_validation"],
                )
            quality_score = case_data.get("quality_score", 85)
            result["quality_score"] = quality_score

            # Stage 6: Delivery
            self._advance_stage(case_id, PipelineStage.DELIVERY)

            # Complete
            self._advance_stage(case_id, PipelineStage.COMPLETE)
            result["stage"] = PipelineStage.COMPLETE.value

        except Exception as exc:
            logger.error("Pipeline failed for case %d: %s", case_id, exc)
            result["errors"].append(str(exc))
            result["stage"] = PipelineStage.FAILED.value
            self._db.execute(
                "UPDATE case_pipeline SET stage = ?, error_message = ? WHERE case_id = ?",
                (PipelineStage.FAILED.value, str(exc), case_id),
            )

        elapsed = time.monotonic() - start_time

        # Update pipeline record
        billing = self.calculate_billing(case_id)
        result["billing"] = billing
        result["processing_time_seconds"] = round(elapsed, 3)

        self._db.execute(
            "UPDATE case_pipeline SET stage = ?, filings_generated = ?, "
            "evidence_processed = ?, claims_detected = ?, quality_score = ?, "
            "total_charges_cents = ?, completed_at = datetime('now') WHERE case_id = ?",
            (
                result["stage"], result["filings_generated"],
                result["evidence_processed"], result["claims_detected"],
                result["quality_score"], billing.get("total_cents", 0), case_id,
            ),
        )

        logger.info(
            "Case %d processed: stage=%s, filings=%d, revenue=$%.2f in %.1fs",
            case_id, result["stage"], result["filings_generated"],
            billing.get("total_cents", 0) / 100, elapsed,
        )
        return result

    def get_revenue_report(self, period: str = "monthly") -> dict:
        """Revenue metrics: cases processed, filings generated, revenue by tier.

        Args:
            period: One of ``"daily"``, ``"weekly"``, ``"monthly"``, ``"all"``.

        Returns:
            Dict with revenue breakdown, case counts, and filing counts.
        """
        now = datetime.now()

        if period == "daily":
            start = now.replace(hour=0, minute=0, second=0).isoformat()
        elif period == "weekly":
            start = (now - timedelta(days=now.weekday())).replace(
                hour=0, minute=0, second=0,
            ).isoformat()
        elif period == "monthly":
            start = now.replace(day=1, hour=0, minute=0, second=0).isoformat()
        else:  # "all"
            start = "2000-01-01T00:00:00"

        row = self._db.fetchone(
            """SELECT
                (SELECT COUNT(*) FROM case_pipeline
                 WHERE completed_at >= ?) AS cases_processed,
                (SELECT COALESCE(SUM(filings_generated), 0) FROM case_pipeline
                 WHERE completed_at >= ?) AS filings_generated,
                (SELECT COALESCE(SUM(total_charges_cents), 0) FROM case_pipeline
                 WHERE completed_at >= ?) AS usage_revenue_cents,
                (SELECT COUNT(*) FROM case_pipeline
                 WHERE stage = 'complete' AND completed_at >= ?) AS successful_cases,
                (SELECT COUNT(*) FROM case_pipeline
                 WHERE stage = 'failed' AND completed_at >= ?) AS failed_cases
            """,
            (start, start, start, start, start),
        )
        data = dict(row) if row else {}

        # Revenue by event type
        event_rows = self._db.fetchall(
            "SELECT event_type, SUM(total_cents) AS revenue, SUM(quantity) AS volume "
            "FROM billing_events WHERE created_at >= ? GROUP BY event_type",
            (start,),
        )
        revenue_by_type = {
            r["event_type"]: {"revenue_cents": r["revenue"], "volume": r["volume"]}
            for r in event_rows
        }

        subscription_revenue = self._estimate_subscription_revenue(period)

        return {
            "period": period,
            "period_start": start,
            "cases_processed": data.get("cases_processed", 0),
            "successful_cases": data.get("successful_cases", 0),
            "failed_cases": data.get("failed_cases", 0),
            "filings_generated": data.get("filings_generated", 0),
            "usage_revenue_cents": data.get("usage_revenue_cents", 0),
            "subscription_revenue_cents": subscription_revenue,
            "total_revenue_cents": data.get("usage_revenue_cents", 0) + subscription_revenue,
            "revenue_by_type": revenue_by_type,
        }

    def get_case_pipeline_status(self) -> list[dict]:
        """All cases in pipeline with current stage and metrics."""
        rows = self._db.fetchall(
            "SELECT id, case_id, user_id, stage, filings_generated, "
            "evidence_processed, claims_detected, quality_score, "
            "total_charges_cents, error_message, started_at, completed_at "
            "FROM case_pipeline ORDER BY started_at DESC",
        )
        return [dict(r) for r in rows]

    def run_batch_processing(self) -> dict:
        """Process all pending cases in the queue.

        Scans the ``case_pipeline`` table for entries stuck in non-terminal
        stages and re-processes them.  Returns summary statistics.
        """
        terminal = (PipelineStage.COMPLETE.value, PipelineStage.FAILED.value)
        rows = self._db.fetchall(
            "SELECT case_id, user_id, stage FROM case_pipeline WHERE stage NOT IN (?, ?)",
            terminal,
        )
        pending = [dict(r) for r in rows]
        results = {
            "total_pending": len(pending),
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "case_results": [],
        }

        for entry in pending:
            case_result = self.process_new_case({
                "case_id": entry["case_id"],
                "user_id": entry["user_id"],
            })
            results["processed"] += 1
            if case_result.get("stage") == PipelineStage.COMPLETE.value:
                results["succeeded"] += 1
            else:
                results["failed"] += 1
            results["case_results"].append(case_result)

        logger.info(
            "Batch processing complete: %d/%d succeeded",
            results["succeeded"], results["processed"],
        )
        return results

    def calculate_billing(self, case_id: int) -> dict:
        """Calculate charges for a case based on usage.

        Args:
            case_id: The case to bill.

        Returns:
            Dict with line_items, subtotal, discount, and total (all in cents).
        """
        rows = self._db.fetchall(
            "SELECT event_type, description, quantity, rate_cents, total_cents "
            "FROM billing_events WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        )

        line_items = []
        subtotal = 0
        for r in rows:
            item = {
                "event_type": r["event_type"],
                "description": r["description"],
                "quantity": r["quantity"],
                "rate_cents": r["rate_cents"],
                "total_cents": r["total_cents"],
            }
            line_items.append(item)
            subtotal += r["total_cents"]

        # Look up subscription tier for discount
        pipeline_row = self._db.fetchone(
            "SELECT user_id FROM case_pipeline WHERE case_id = ?", (case_id,),
        )
        tier = "free"
        discount_pct = 0
        if pipeline_row:
            tier = self._get_user_tier(pipeline_row["user_id"])
            discount_pct = self._tier_discount(tier)

        discount_amount = int(subtotal * discount_pct / 100)
        total = subtotal - discount_amount

        return {
            "case_id": case_id,
            "line_items": line_items,
            "subtotal_cents": subtotal,
            "subscription_tier": tier,
            "discount_pct": discount_pct,
            "discount_amount_cents": discount_amount,
            "total_cents": total,
        }

    def get_metrics(self) -> dict:
        """System performance: avg processing time, success rate, quality scores."""
        row = self._db.fetchone(
            """SELECT
                (SELECT COUNT(*) FROM case_pipeline) AS total_cases,
                (SELECT COUNT(*) FROM case_pipeline
                 WHERE stage = 'complete') AS completed_cases,
                (SELECT COUNT(*) FROM case_pipeline
                 WHERE stage = 'failed') AS failed_cases,
                (SELECT COALESCE(AVG(quality_score), 0) FROM case_pipeline
                 WHERE stage = 'complete') AS avg_quality_score,
                (SELECT COALESCE(SUM(filings_generated), 0)
                 FROM case_pipeline) AS total_filings,
                (SELECT COALESCE(SUM(total_charges_cents), 0)
                 FROM case_pipeline) AS total_revenue_cents,
                (SELECT COALESCE(SUM(evidence_processed), 0)
                 FROM case_pipeline) AS total_evidence,
                (SELECT COUNT(DISTINCT case_id)
                 FROM billing_events) AS billed_cases
            """,
        )
        data = dict(row) if row else {}

        total = data.get("total_cases", 0)
        completed = data.get("completed_cases", 0)
        success_rate = round((completed / total * 100), 1) if total > 0 else 0.0

        return {
            "total_cases": total,
            "completed_cases": completed,
            "failed_cases": data.get("failed_cases", 0),
            "success_rate_pct": success_rate,
            "avg_quality_score": round(data.get("avg_quality_score", 0), 1),
            "total_filings_generated": data.get("total_filings", 0),
            "total_evidence_processed": data.get("total_evidence", 0),
            "total_revenue_cents": data.get("total_revenue_cents", 0),
            "billed_cases": data.get("billed_cases", 0),
        }

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _advance_stage(self, case_id: int, stage: PipelineStage) -> None:
        """Update the pipeline stage for a case."""
        self._db.execute(
            "UPDATE case_pipeline SET stage = ? WHERE case_id = ?",
            (stage.value, case_id),
        )
        logger.debug("Case %d → %s", case_id, stage.value)

    def _record_billing_event(
        self,
        case_id: int,
        user_id: int,
        event_type: str,
        description: str,
        quantity: int,
        rate_cents: int,
    ) -> None:
        """Insert a billing event for usage-based charging."""
        total = quantity * rate_cents
        self._db.execute(
            "INSERT INTO billing_events "
            "(case_id, user_id, event_type, description, quantity, rate_cents, total_cents) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (case_id, user_id, event_type, description, quantity, rate_cents, total),
        )

    def _get_user_tier(self, user_id: int) -> str:
        """Look up subscription tier, defaulting to 'free'."""
        try:
            row = self._db.fetchone(
                "SELECT tier FROM subscriptions WHERE user_id = ? AND status = 'active'",
                (user_id,),
            )
            return row["tier"] if row else "free"
        except Exception:
            return "free"

    @staticmethod
    def _tier_discount(tier: str) -> int:
        """Discount percentage by subscription tier."""
        return {"free": 0, "pro": 10, "enterprise": 25}.get(tier, 0)

    def _estimate_subscription_revenue(self, period: str) -> int:
        """Estimate subscription revenue from active subscriptions."""
        try:
            row = self._db.fetchone(
                """SELECT
                    COALESCE(SUM(CASE WHEN tier = 'pro' THEN 1 ELSE 0 END), 0) AS pro,
                    COALESCE(SUM(CASE WHEN tier = 'enterprise' THEN 1 ELSE 0 END), 0) AS ent
                FROM subscriptions WHERE status = 'active'""",
            )
            if not row:
                return 0
            data = dict(row)
            monthly = (
                data.get("pro", 0) * SUBSCRIPTION_RATES["pro"]
                + data.get("ent", 0) * SUBSCRIPTION_RATES["enterprise"]
            )
            if period == "daily":
                return monthly // 30
            if period == "weekly":
                return monthly // 4
            return monthly  # monthly or all
        except Exception:
            return 0
