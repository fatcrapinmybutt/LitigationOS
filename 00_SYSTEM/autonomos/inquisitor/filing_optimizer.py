"""
DELTA99 Ω∞ — Strategic Filing Queue Optimizer
===============================================
Analyzes filing readiness, deadline urgency, evidence strength, and adversary
predicted reactions to determine optimal filing order.

Uses: omega_legal_actions(19), omega_scores(14), omega_predictions(19),
      omega_court_assessment(19), filing_readiness(24), deadlines
"""
import sys
import sqlite3
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

OPTIMIZER_DB = Path(__file__).parent / "filing_optimizer.db"

# ── Filing Priority Weights ────────────────────────────────────────
W_DEADLINE = 0.30   # Deadline urgency (30%)
W_READINESS = 0.25  # Filing readiness score (25%)
W_IMPACT = 0.25     # Strategic impact / OMEGA score (25%)
W_EVIDENCE = 0.15   # Evidence strength (15%)
W_SURPRISE = 0.05   # Adversary surprise factor (5%)


def _init_db() -> sqlite3.Connection:
    OPTIMIZER_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(OPTIMIZER_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS optimization_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filings_analyzed INTEGER DEFAULT 0,
            optimal_sequence TEXT DEFAULT '[]',
            total_score REAL DEFAULT 0.0,
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS filing_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            vehicle_name TEXT NOT NULL,
            forum TEXT DEFAULT '',
            deadline_score REAL DEFAULT 0.0,
            readiness_score REAL DEFAULT 0.0,
            impact_score REAL DEFAULT 0.0,
            evidence_score REAL DEFAULT 0.0,
            surprise_score REAL DEFAULT 0.0,
            composite_score REAL DEFAULT 0.0,
            recommended_order INTEGER DEFAULT 0,
            notes TEXT DEFAULT ''
        );
    """)
    conn.commit()
    return conn


@dataclass
class FilingScore:
    vehicle_name: str
    forum: str = ""
    deadline_score: float = 0.0
    readiness_score: float = 0.0
    impact_score: float = 0.0
    evidence_score: float = 0.0
    surprise_score: float = 0.0
    composite_score: float = 0.0
    notes: list = field(default_factory=list)


def _calc_deadline_urgency(central: sqlite3.Connection, vehicle: str) -> float:
    """Score based on how close the filing deadline is (1.0 = past due, 0.0 = no deadline)."""
    try:
        row = central.execute("""
            SELECT due_date_iso FROM deadlines
            WHERE description LIKE ? AND due_date_iso >= date('now', '-30 days')
            ORDER BY due_date_iso ASC LIMIT 1
        """, (f"%{vehicle[:30]}%",)).fetchone()
    except sqlite3.Error:
        return 0.0

    if not row or not row[0]:
        return 0.3  # No deadline = moderate priority

    try:
        deadline = datetime.fromisoformat(str(row[0]).split("T")[0])
        days_left = (deadline - datetime.now()).days
        if days_left <= 0:
            return 1.0   # Past due
        elif days_left <= 7:
            return 0.95
        elif days_left <= 14:
            return 0.8
        elif days_left <= 21:
            return 0.6
        elif days_left <= 30:
            return 0.4
        else:
            return 0.2
    except (ValueError, TypeError):
        return 0.3


def _calc_readiness(central: sqlite3.Connection, vehicle: str) -> float:
    """Get filing readiness score from filing_readiness table."""
    try:
        row = central.execute("""
            SELECT readiness_score FROM filing_readiness
            WHERE vehicle_name LIKE ? LIMIT 1
        """, (f"%{vehicle[:30]}%",)).fetchone()
        if row and row[0]:
            return min(float(row[0]) / 100.0, 1.0)
    except sqlite3.Error:
        pass
    return 0.0


def _calc_impact(central: sqlite3.Connection, vehicle: str) -> float:
    """Calculate strategic impact from OMEGA scores."""
    try:
        row = central.execute("""
            SELECT composite_score FROM omega_scores
            WHERE action_name LIKE ? LIMIT 1
        """, (f"%{vehicle[:30]}%",)).fetchone()
        if row and row[0]:
            return min(float(row[0]) / 100.0, 1.0)
    except sqlite3.Error:
        pass

    # Fallback to omega_legal_actions
    try:
        row = central.execute("""
            SELECT priority_score FROM omega_legal_actions
            WHERE action_name LIKE ? LIMIT 1
        """, (f"%{vehicle[:30]}%",)).fetchone()
        if row and row[0]:
            return min(float(row[0]) / 100.0, 1.0)
    except sqlite3.Error:
        pass
    return 0.5  # Default moderate impact


def _calc_evidence_strength(central: sqlite3.Connection, vehicle: str) -> float:
    """Calculate evidence strength from claim_evidence_links density."""
    try:
        row = central.execute("""
            SELECT COUNT(*) FROM claim_evidence_links cel
            JOIN claims c ON cel.claim_id = c.claim_id
            WHERE c.proposition LIKE ?
        """, (f"%{vehicle[:20]}%",)).fetchone()
        if row and row[0]:
            count = row[0]
            if count > 50:
                return 1.0
            elif count > 20:
                return 0.8
            elif count > 5:
                return 0.6
            else:
                return 0.3
    except sqlite3.Error:
        pass
    return 0.5


def _calc_surprise(central: sqlite3.Connection, vehicle: str) -> float:
    """Estimate adversary surprise factor based on prediction models."""
    try:
        row = central.execute("""
            SELECT success_probability FROM omega_predictions
            WHERE action_name LIKE ? LIMIT 1
        """, (f"%{vehicle[:30]}%",)).fetchone()
        if row and row[0]:
            prob = float(row[0])
            # Higher success prob = lower surprise needed
            return max(0.0, 1.0 - prob / 100.0)
    except sqlite3.Error:
        pass
    return 0.5


def optimize_filing_queue() -> dict:
    """Calculate optimal filing order based on multi-factor scoring."""
    start = time.time()
    opt_db = _init_db()

    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    # Get all filing vehicles
    vehicles = []
    try:
        rows = central.execute("""
            SELECT vehicle_name, forum FROM filing_readiness
        """).fetchall()
        vehicles = [(r[0], r[1] or "") for r in rows]
    except sqlite3.Error:
        try:
            rows = central.execute("""
                SELECT action_name, forum FROM omega_legal_actions
            """).fetchall()
            vehicles = [(r[0], r[1] or "") for r in rows]
        except sqlite3.Error:
            pass

    # Score each vehicle
    scores: list[FilingScore] = []
    for name, forum in vehicles:
        fs = FilingScore(vehicle_name=name, forum=forum)
        fs.deadline_score = _calc_deadline_urgency(central, name)
        fs.readiness_score = _calc_readiness(central, name)
        fs.impact_score = _calc_impact(central, name)
        fs.evidence_score = _calc_evidence_strength(central, name)
        fs.surprise_score = _calc_surprise(central, name)

        fs.composite_score = round(
            fs.deadline_score * W_DEADLINE +
            fs.readiness_score * W_READINESS +
            fs.impact_score * W_IMPACT +
            fs.evidence_score * W_EVIDENCE +
            fs.surprise_score * W_SURPRISE,
            4
        )

        # Notes
        if fs.deadline_score >= 0.95:
            fs.notes.append("URGENT: deadline imminent")
        if fs.readiness_score < 0.5:
            fs.notes.append("WARN: readiness below 50%")
        if fs.evidence_score < 0.3:
            fs.notes.append("WARN: weak evidence support")

        scores.append(fs)

    # Sort by composite score descending
    scores.sort(key=lambda x: x.composite_score, reverse=True)

    # Persist
    run_id = opt_db.execute("""
        INSERT INTO optimization_runs (filings_analyzed, optimal_sequence, total_score, duration_s)
        VALUES (?, ?, ?, ?)
    """, (
        len(scores),
        json.dumps([s.vehicle_name for s in scores]),
        sum(s.composite_score for s in scores),
        round(time.time() - start, 2),
    )).lastrowid
    opt_db.commit()

    for i, fs in enumerate(scores):
        opt_db.execute("""
            INSERT INTO filing_scores
            (run_id, vehicle_name, forum, deadline_score, readiness_score,
             impact_score, evidence_score, surprise_score, composite_score,
             recommended_order, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (run_id, fs.vehicle_name, fs.forum,
              fs.deadline_score, fs.readiness_score,
              fs.impact_score, fs.evidence_score,
              fs.surprise_score, fs.composite_score,
              i + 1, "; ".join(fs.notes)))
    opt_db.commit()

    central.close()
    opt_db.close()
    duration = round(time.time() - start, 2)

    return {
        "filings_analyzed": len(scores),
        "optimal_sequence": [
            {
                "order": i + 1,
                "vehicle": s.vehicle_name,
                "forum": s.forum,
                "score": s.composite_score,
                "deadline": s.deadline_score,
                "readiness": s.readiness_score,
                "impact": s.impact_score,
                "evidence": s.evidence_score,
                "notes": s.notes,
            }
            for i, s in enumerate(scores)
        ],
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = optimize_filing_queue()
    print(json.dumps(result, indent=2, default=str))
