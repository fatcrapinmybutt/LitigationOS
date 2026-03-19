#!/usr/bin/env python3
"""LitigationOS Revenue Tracker - Metrics, projections, and webhook processing."""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import json
import sqlite3
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class RevenueMetrics:
    """Core SaaS revenue metrics."""
    date: str
    mrr: float = 0.0
    arr: float = 0.0
    active_subscribers: int = 0
    new_subscribers: int = 0
    churned_subscribers: int = 0
    churn_rate: float = 0.0
    ltv: float = 0.0
    cac: float = 0.0
    ltv_cac_ratio: float = 0.0
    net_revenue_retention: float = 100.0
    expansion_mrr: float = 0.0
    contraction_mrr: float = 0.0

    def compute_derived(self):
        self.arr = self.mrr * 12
        if self.active_subscribers > 0:
            self.churn_rate = round(
                (self.churned_subscribers / self.active_subscribers) * 100, 2
            )
        if self.churn_rate > 0:
            avg_monthly_revenue = self.mrr / max(self.active_subscribers, 1)
            self.ltv = round(avg_monthly_revenue / (self.churn_rate / 100), 2)
        if self.cac > 0:
            self.ltv_cac_ratio = round(self.ltv / self.cac, 2)


@dataclass
class MonthlyProjection:
    month: int
    label: str
    subscribers: int
    mrr: float
    arr: float
    cumulative_revenue: float
    churn_rate: float
    net_new: int


# ── Database Setup ───────────────────────────────────────────────────────────

def init_db():
    """Create revenue tables if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS omega_revenue_projections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            month INTEGER NOT NULL,
            label TEXT NOT NULL,
            subscribers INTEGER NOT NULL,
            mrr REAL NOT NULL,
            arr REAL NOT NULL,
            cumulative_revenue REAL NOT NULL,
            churn_rate REAL NOT NULL,
            net_new INTEGER NOT NULL,
            scenario TEXT DEFAULT 'base'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS omega_revenue_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            event_id TEXT UNIQUE,
            customer_id TEXT,
            amount REAL,
            currency TEXT DEFAULT 'usd',
            plan TEXT,
            timestamp TEXT NOT NULL,
            raw_payload TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS omega_daily_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            total_revenue REAL,
            new_subscriptions INTEGER,
            cancellations INTEGER,
            active_subscribers INTEGER,
            mrr REAL,
            notes TEXT
        )
    """)

    conn.commit()
    conn.close()


# ── Stripe Webhook Processor (Mock) ─────────────────────────────────────────

STRIPE_WEBHOOK_SECRET = "whsec_mock_litigationos_dev_key"

MOCK_EVENTS = [
    {
        "id": "evt_1001",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "customer": "cus_alpha_001",
                "plan": {"id": "plan_pro_monthly", "amount": 4900, "currency": "usd"},
                "status": "active",
            }
        },
    },
    {
        "id": "evt_1002",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "customer": "cus_beta_002",
                "plan": {"id": "plan_basic_monthly", "amount": 2900, "currency": "usd"},
                "status": "active",
            }
        },
    },
    {
        "id": "evt_1003",
        "type": "invoice.payment_succeeded",
        "data": {
            "object": {
                "customer": "cus_alpha_001",
                "amount_paid": 4900,
                "currency": "usd",
            }
        },
    },
    {
        "id": "evt_1004",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "customer": "cus_gamma_003",
                "plan": {"id": "plan_enterprise_monthly", "amount": 19900, "currency": "usd"},
                "status": "active",
            }
        },
    },
    {
        "id": "evt_1005",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "customer": "cus_beta_002",
                "plan": {"id": "plan_basic_monthly", "amount": 2900, "currency": "usd"},
                "status": "canceled",
            }
        },
    },
]


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify Stripe webhook signature (mock implementation)."""
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def process_webhook_event(event: dict) -> Optional[dict]:
    """Process a single Stripe webhook event and return extracted data."""
    event_type = event.get("type", "")
    event_id = event.get("id", "")
    obj = event.get("data", {}).get("object", {})
    customer_id = obj.get("customer", "unknown")
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "event_type": event_type,
        "event_id": event_id,
        "customer_id": customer_id,
        "timestamp": now,
        "raw_payload": json.dumps(event),
    }

    if "subscription" in event_type:
        plan = obj.get("plan", {})
        record["amount"] = plan.get("amount", 0) / 100.0
        record["currency"] = plan.get("currency", "usd")
        record["plan"] = plan.get("id", "unknown")
    elif event_type == "invoice.payment_succeeded":
        record["amount"] = obj.get("amount_paid", 0) / 100.0
        record["currency"] = obj.get("currency", "usd")
        record["plan"] = "invoice_payment"
    else:
        record["amount"] = 0
        record["currency"] = "usd"
        record["plan"] = "unknown"

    return record


def ingest_mock_events():
    """Process all mock events and store in database."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    processed = 0

    for event in MOCK_EVENTS:
        record = process_webhook_event(event)
        if record:
            try:
                c.execute("""
                    INSERT OR IGNORE INTO omega_revenue_events
                    (event_type, event_id, customer_id, amount, currency, plan, timestamp, raw_payload)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record["event_type"], record["event_id"], record["customer_id"],
                    record["amount"], record["currency"], record["plan"],
                    record["timestamp"], record["raw_payload"],
                ))
                if c.rowcount > 0:
                    processed += 1
            except sqlite3.Error:
                pass

    conn.commit()
    conn.close()
    return processed


# ── Daily Revenue Summary ────────────────────────────────────────────────────

def generate_daily_summary(target_date: Optional[str] = None) -> dict:
    """Generate a revenue summary for a given date from stored events."""
    if not target_date:
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("""
        SELECT COUNT(*) FROM omega_revenue_events
        WHERE event_type = 'customer.subscription.created'
        AND date(timestamp) <= ?
    """, (target_date,))
    total_created = c.fetchone()[0]

    c.execute("""
        SELECT COUNT(*) FROM omega_revenue_events
        WHERE event_type = 'customer.subscription.deleted'
        AND date(timestamp) <= ?
    """, (target_date,))
    total_canceled = c.fetchone()[0]

    active = total_created - total_canceled

    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM omega_revenue_events
        WHERE event_type = 'customer.subscription.created'
        AND date(timestamp) <= ?
    """, (target_date,))
    mrr_created = c.fetchone()[0]

    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM omega_revenue_events
        WHERE event_type = 'customer.subscription.deleted'
        AND date(timestamp) <= ?
    """, (target_date,))
    mrr_lost = c.fetchone()[0]

    mrr = mrr_created - mrr_lost

    c.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM omega_revenue_events
        WHERE event_type = 'invoice.payment_succeeded'
        AND date(timestamp) <= ?
    """, (target_date,))
    total_collected = c.fetchone()[0]

    summary = {
        "date": target_date,
        "active_subscribers": active,
        "total_revenue_collected": round(total_collected, 2),
        "current_mrr": round(mrr, 2),
        "new_subscriptions": total_created,
        "cancellations": total_canceled,
    }

    c.execute("""
        INSERT OR REPLACE INTO omega_daily_summaries
        (date, total_revenue, new_subscriptions, cancellations, active_subscribers, mrr)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        target_date, total_collected, total_created,
        total_canceled, active, mrr,
    ))

    conn.commit()
    conn.close()
    return summary


# ── Financial Projection Calculator ──────────────────────────────────────────

GROWTH_SCENARIOS = {
    "conservative": {
        "initial_subscribers": 5,
        "monthly_growth_rate": 0.15,
        "avg_revenue_per_user": 49.00,
        "churn_rate": 0.08,
        "cac": 35.00,
    },
    "base": {
        "initial_subscribers": 10,
        "monthly_growth_rate": 0.25,
        "avg_revenue_per_user": 59.00,
        "churn_rate": 0.05,
        "cac": 28.00,
    },
    "aggressive": {
        "initial_subscribers": 20,
        "monthly_growth_rate": 0.40,
        "avg_revenue_per_user": 69.00,
        "churn_rate": 0.03,
        "cac": 22.00,
    },
}


def calculate_projections(scenario: str = "base", months: int = 12) -> list[MonthlyProjection]:
    """Calculate M1-M12 financial projections based on growth scenario."""
    params = GROWTH_SCENARIOS.get(scenario, GROWTH_SCENARIOS["base"])
    projections = []
    subscribers = params["initial_subscribers"]
    cumulative = 0.0

    for m in range(1, months + 1):
        churned = int(subscribers * params["churn_rate"])
        new_organic = max(1, int(subscribers * params["monthly_growth_rate"]))
        net_new = new_organic - churned
        subscribers = max(subscribers + net_new, 1)
        mrr = round(subscribers * params["avg_revenue_per_user"], 2)
        cumulative = round(cumulative + mrr, 2)

        proj = MonthlyProjection(
            month=m,
            label=f"M{m}",
            subscribers=subscribers,
            mrr=mrr,
            arr=round(mrr * 12, 2),
            cumulative_revenue=cumulative,
            churn_rate=params["churn_rate"] * 100,
            net_new=net_new,
        )
        projections.append(proj)

    return projections


def save_projections(scenario: str = "base"):
    """Calculate and save projections to the database."""
    projections = calculate_projections(scenario)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    c.execute("DELETE FROM omega_revenue_projectionsWHERE scenario = ?", (scenario,))

    for p in projections:
        c.execute("""
            INSERT INTO omega_revenue_projections
            (created_at, month, label, subscribers, mrr, arr, cumulative_revenue, churn_rate, net_new, scenario)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, p.month, p.label, p.subscribers, p.mrr, p.arr,
              p.cumulative_revenue, p.churn_rate, p.net_new, scenario))

    conn.commit()
    conn.close()
    return projections


# ── Reporting ────────────────────────────────────────────────────────────────

def print_projection_table(projections: list[MonthlyProjection], scenario: str):
    """Print a formatted projection table."""
    print(f"\n{'=' * 80}")
    print(f"  LITIGATIONOS REVENUE PROJECTIONS - {scenario.upper()} SCENARIO")
    print(f"{'=' * 80}")
    print(f"  {'Month':<8} {'Subs':>6} {'Net New':>8} {'MRR':>12} {'ARR':>14} {'Cumulative':>14}")
    print(f"  {'-' * 70}")

    for p in projections:
        print(
            f"  {p.label:<8} {p.subscribers:>6} {p.net_new:>+8} "
            f"${p.mrr:>10,.2f} ${p.arr:>12,.2f} ${p.cumulative_revenue:>12,.2f}"
        )

    final = projections[-1]
    print(f"  {'-' * 70}")
    print(f"  M12 MRR: ${final.mrr:,.2f}  |  M12 ARR: ${final.arr:,.2f}  |  Total Collected: ${final.cumulative_revenue:,.2f}")
    print()


def print_daily_summary(summary: dict):
    """Print formatted daily summary."""
    print(f"\n{'=' * 60}")
    print(f"  DAILY REVENUE SUMMARY - {summary['date']}")
    print(f"{'=' * 60}")
    print(f"  Active Subscribers:    {summary['active_subscribers']}")
    print(f"  Current MRR:           ${summary['current_mrr']:,.2f}")
    print(f"  Revenue Collected:     ${summary['total_revenue_collected']:,.2f}")
    print(f"  New Subscriptions:     {summary['new_subscriptions']}")
    print(f"  Cancellations:         {summary['cancellations']}")
    print()


def print_metrics_snapshot():
    """Print current key metrics."""
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM omega_revenue_events WHERE event_type = 'customer.subscription.created'")
    created = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM omega_revenue_events WHERE event_type = 'customer.subscription.deleted'")
    deleted = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM omega_revenue_events WHERE event_type LIKE '%created%'")
    mrr_in = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount), 0) FROM omega_revenue_events WHERE event_type LIKE '%deleted%'")
    mrr_out = c.fetchone()[0]

    conn.close()

    active = created - deleted
    mrr = mrr_in - mrr_out
    arr = mrr * 12
    churn = (deleted / created * 100) if created > 0 else 0

    print(f"\n{'=' * 60}")
    print(f"  LITIGATIONOS KEY METRICS SNAPSHOT")
    print(f"{'=' * 60}")
    print(f"  Active Subscribers:    {active}")
    print(f"  MRR:                   ${mrr:,.2f}")
    print(f"  ARR:                   ${arr:,.2f}")
    print(f"  Churn Rate:            {churn:.1f}%")
    print(f"  LTV (est @ 5% churn): ${(mrr / max(active, 1)) / 0.05:,.2f}")
    print(f"  CAC Target:            $28.00")
    print(f"  Events Processed:      {created + deleted}")
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("[*] LitigationOS Revenue Tracker v1.0")
    print("[*] Initializing database...")
    init_db()

    print("[*] Ingesting mock Stripe webhook events...")
    count = ingest_mock_events()
    print(f"[+] Processed {count} new events")

    summary = generate_daily_summary()
    print_daily_summary(summary)
    print_metrics_snapshot()

    for scenario in ("conservative", "base", "aggressive"):
        projections = save_projections(scenario)
        print_projection_table(projections, scenario)

    print("[+] All projections saved to omega_revenue_projections table")
    print(f"[+] Database: {DB_PATH}")
    print("[+] Revenue tracker complete.")


if __name__ == "__main__":
    main()
