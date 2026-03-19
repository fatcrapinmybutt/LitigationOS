"""
DELTA99 Ω∞ — Predictive Filing Engine
=======================================
Uses evidence chain strength + filing optimizer scores to predict which
filings will succeed and recommends optimal filing timing based on
Monte Carlo simulations from omega_predictions.

Depends on: d99-evidence-chain, d99-filing-optimizer
Uses: omega_predictions(19), omega_scores(14), omega_court_assessment(19),
      filing_readiness(24), deadlines
"""
import sys
import sqlite3
import json
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB

PREDICT_DB = Path(__file__).parent / "predict_filing.db"

MC_SIMULATIONS = 1000  # Monte Carlo iterations
CONFIDENCE_LEVEL = 0.90


def _init_db() -> sqlite3.Connection:
    PREDICT_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(PREDICT_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS filing_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_name TEXT NOT NULL,
            forum TEXT DEFAULT '',
            success_probability REAL DEFAULT 0.0,
            mc_mean REAL DEFAULT 0.0,
            mc_p5 REAL DEFAULT 0.0,
            mc_p95 REAL DEFAULT 0.0,
            optimal_file_date TEXT DEFAULT '',
            reasoning TEXT DEFAULT '',
            predicted_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS timing_recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_name TEXT NOT NULL,
            recommended_date TEXT DEFAULT '',
            reason TEXT DEFAULT '',
            confidence REAL DEFAULT 0.0,
            factors TEXT DEFAULT '[]'
        );
        CREATE TABLE IF NOT EXISTS prediction_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filings_analyzed INTEGER DEFAULT 0,
            avg_success_prob REAL DEFAULT 0.0,
            best_filing TEXT DEFAULT '',
            worst_filing TEXT DEFAULT '',
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def _get_omega_predictions(central: sqlite3.Connection) -> list[dict]:
    """Pull existing OMEGA predictions."""
    predictions = []
    try:
        rows = central.execute("""
            SELECT action_name, forum, probability, impact, expected_value,
                   risk_score, mc_mean, mc_median, mc_std, mc_p5, mc_p95,
                   sequence_order
            FROM omega_predictions
            ORDER BY expected_value DESC
        """).fetchall()
        for r in rows:
            predictions.append({
                "name": str(r[0]), "forum": str(r[1] or ""),
                "probability": float(r[2] or 0), "impact": float(r[3] or 0),
                "expected_value": float(r[4] or 0),
                "risk": float(r[5] or 0),
                "mc_mean": float(r[6] or 0), "mc_median": float(r[7] or 0),
                "mc_std": float(r[8] or 0),
                "mc_p5": float(r[9] or 0), "mc_p95": float(r[10] or 0),
                "sequence": int(r[11] or 0),
            })
    except sqlite3.Error:
        pass
    return predictions


def _get_readiness(central: sqlite3.Connection) -> dict[str, dict]:
    """Get filing readiness data."""
    readiness = {}
    try:
        rows = central.execute("""
            SELECT action_name, forum, readiness_pct, risk_score, enhanced_omega
            FROM filing_readiness
        """).fetchall()
        for r in rows:
            readiness[str(r[0])] = {
                "forum": str(r[1] or ""), "readiness": int(r[2] or 0),
                "risk": float(r[3] or 0), "omega": float(r[4] or 0),
            }
    except sqlite3.Error:
        pass
    return readiness


def _get_deadlines(central: sqlite3.Connection) -> dict[str, str]:
    """Get filing deadlines."""
    deadlines = {}
    try:
        rows = central.execute("""
            SELECT description, due_date_iso FROM deadlines
            WHERE due_date_iso >= date('now')
            ORDER BY due_date_iso ASC
        """).fetchall()
        for r in rows:
            deadlines[str(r[0])[:50]] = str(r[1])
    except sqlite3.Error:
        pass
    return deadlines


def _monte_carlo_simulate(base_prob: float, risk: float,
                          evidence_strength: float = 0.7,
                          n: int = MC_SIMULATIONS) -> dict:
    """Run Monte Carlo simulation for filing success."""
    results = []
    for _ in range(n):
        # Add noise to base probability
        noise = random.gauss(0, 0.05)
        # Evidence strength bonus
        ev_bonus = (evidence_strength - 0.5) * 0.15
        # Risk penalty
        risk_penalty = risk * 0.1
        # Judge bias (McNeill consistently hostile)
        judge_penalty = random.uniform(0.05, 0.15)  # 14th Circuit penalty
        # Final simulation
        sim_prob = base_prob + noise + ev_bonus - risk_penalty - judge_penalty
        sim_prob = max(0.0, min(1.0, sim_prob))
        results.append(sim_prob)

    results.sort()
    n5 = int(n * 0.05)
    n95 = int(n * 0.95)

    return {
        "mean": round(sum(results) / len(results), 4),
        "median": round(results[len(results) // 2], 4),
        "std": round((sum((x - sum(results)/len(results))**2 for x in results) / len(results))**0.5, 4),
        "p5": round(results[n5], 4),
        "p95": round(results[n95], 4),
        "min": round(results[0], 4),
        "max": round(results[-1], 4),
    }


def _recommend_timing(filing: str, readiness: dict,
                      deadline: str | None) -> dict:
    """Recommend optimal filing date."""
    now = datetime.now()
    factors = []

    ready_pct = readiness.get("readiness", 0)
    risk = readiness.get("risk", 0.5)

    if deadline:
        try:
            dl = datetime.fromisoformat(deadline.split("T")[0])
            days_left = (dl - now).days
            if days_left <= 7:
                factors.append("Deadline imminent — file immediately")
                rec_date = now + timedelta(days=1)
            elif days_left <= 14:
                factors.append(f"Deadline in {days_left} days — file within 5 days")
                rec_date = now + timedelta(days=5)
            else:
                rec_date = dl - timedelta(days=14)
                factors.append(f"Target 14 days before {deadline} deadline")
        except (ValueError, TypeError):
            rec_date = now + timedelta(days=14)
    else:
        rec_date = now + timedelta(days=14)
        factors.append("No deadline — use strategic timing")

    if ready_pct < 60:
        rec_date += timedelta(days=7)
        factors.append(f"Readiness only {ready_pct}% — delay 7 days for preparation")

    if risk > 0.7:
        factors.append("High risk — consider filing in favorable forum first")

    # Strategic considerations
    # Monday filings get more attention than Friday
    while rec_date.weekday() in (5, 6):  # Skip weekends
        rec_date += timedelta(days=1)
    if rec_date.weekday() == 0:
        factors.append("Monday filing — optimal for court attention")

    return {
        "recommended_date": rec_date.strftime("%Y-%m-%d"),
        "factors": factors,
        "confidence": min(ready_pct / 100.0, 0.95),
    }


def run_predictions() -> dict:
    """Run complete filing prediction analysis."""
    start = time.time()
    pdb = _init_db()
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    omega_preds = _get_omega_predictions(central)
    readiness = _get_readiness(central)
    deadlines = _get_deadlines(central)
    central.close()

    predictions = []
    for pred in omega_preds:
        name = pred["name"]
        ready_info = readiness.get(name, {})
        ready_pct = ready_info.get("readiness", 50) / 100.0

        # Monte Carlo simulation
        mc = _monte_carlo_simulate(
            base_prob=pred["probability"] / 100.0,
            risk=pred["risk"],
            evidence_strength=ready_pct,
        )

        # Find deadline
        dl = None
        for dl_key, dl_date in deadlines.items():
            if any(w in dl_key.lower() for w in name.lower().split()[:3]):
                dl = dl_date
                break

        # Timing recommendation
        timing = _recommend_timing(name, ready_info, dl)

        # Reasoning
        reasons = []
        if mc["mean"] > 0.7:
            reasons.append("Strong predicted success")
        elif mc["mean"] > 0.5:
            reasons.append("Moderate predicted success")
        else:
            reasons.append("Below-average success prediction — strengthen before filing")

        if mc["p5"] > 0.4:
            reasons.append("Even worst-case scenario shows reasonable chance")
        if mc["std"] > 0.15:
            reasons.append("High variance — outcome uncertain")

        filing_pred = {
            "name": name,
            "forum": pred["forum"],
            "base_probability": pred["probability"],
            "mc": mc,
            "timing": timing,
            "reasoning": "; ".join(reasons),
        }
        predictions.append(filing_pred)

        pdb.execute("""
            INSERT INTO filing_predictions
            (filing_name, forum, success_probability, mc_mean, mc_p5, mc_p95,
             optimal_file_date, reasoning)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, pred["forum"], mc["mean"],
              mc["mean"], mc["p5"], mc["p95"],
              timing["recommended_date"], "; ".join(reasons)))

        pdb.execute("""
            INSERT INTO timing_recommendations
            (filing_name, recommended_date, reason, confidence, factors)
            VALUES (?, ?, ?, ?, ?)
        """, (name, timing["recommended_date"],
              "; ".join(timing["factors"]),
              timing["confidence"],
              json.dumps(timing["factors"])))

    # Summary stats
    if predictions:
        avg_prob = sum(p["mc"]["mean"] for p in predictions) / len(predictions)
        best = max(predictions, key=lambda p: p["mc"]["mean"])
        worst = min(predictions, key=lambda p: p["mc"]["mean"])
    else:
        avg_prob = 0
        best = {"name": "N/A"}
        worst = {"name": "N/A"}

    duration = round(time.time() - start, 2)
    pdb.execute("""
        INSERT INTO prediction_runs
        (filings_analyzed, avg_success_prob, best_filing, worst_filing, duration_s)
        VALUES (?, ?, ?, ?, ?)
    """, (len(predictions), round(avg_prob, 4),
          best["name"], worst["name"], duration))
    pdb.commit()
    pdb.close()

    return {
        "filings_analyzed": len(predictions),
        "avg_success_probability": round(avg_prob, 4),
        "best_filing": {"name": best["name"], "prob": best.get("mc", {}).get("mean", 0)},
        "worst_filing": {"name": worst["name"], "prob": worst.get("mc", {}).get("mean", 0)},
        "predictions": [
            {"name": p["name"], "forum": p["forum"],
             "success_prob": round(p["mc"]["mean"], 3),
             "range": f"{round(p['mc']['p5'], 3)}-{round(p['mc']['p95'], 3)}",
             "optimal_date": p["timing"]["recommended_date"],
             "reasoning": p["reasoning"][:200]}
            for p in sorted(predictions, key=lambda x: -x["mc"]["mean"])
        ],
        "duration_s": duration,
    }


if __name__ == "__main__":
    result = run_predictions()
    print(json.dumps(result, indent=2, default=str))
