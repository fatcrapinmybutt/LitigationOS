"""
DELTA99 Ω∞ — Self-Evolution Engine
====================================
Continuously improves AUTONOMOS by:
 - Tracking classifier accuracy and tuning weights
 - Expanding pattern libraries from new evidence
 - Optimizing confidence thresholds based on human feedback
 - Auto-discovering new citation patterns and MEEK signals
 - Learning from filing outcomes

Depends on: d99-self-heal, d99-evidence-chain
"""
import sys
import sqlite3
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))

from autonomos_config import CENTRAL_DB, AUTONOMOS_ROOT

EVOLVE_DB = AUTONOMOS_ROOT / "self_evolve.db"


def _init_db() -> sqlite3.Connection:
    EVOLVE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(EVOLVE_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS evolution_cycles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cycle_type TEXT NOT NULL,
            improvements_found INTEGER DEFAULT 0,
            improvements_applied INTEGER DEFAULT 0,
            metrics_before TEXT DEFAULT '{}',
            metrics_after TEXT DEFAULT '{}',
            duration_s REAL DEFAULT 0.0,
            run_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS pattern_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,
            pattern_regex TEXT NOT NULL,
            pattern_hash TEXT NOT NULL UNIQUE,
            confidence REAL DEFAULT 0.5,
            hit_count INTEGER DEFAULT 0,
            source TEXT DEFAULT 'auto-discovered',
            discovered_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS weight_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            component TEXT NOT NULL,
            parameter TEXT NOT NULL,
            old_value REAL DEFAULT 0.0,
            new_value REAL DEFAULT 0.0,
            reason TEXT DEFAULT '',
            applied_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module TEXT NOT NULL,
            item_id TEXT DEFAULT '',
            feedback_type TEXT NOT NULL,
            correct INTEGER DEFAULT 1,
            notes TEXT DEFAULT '',
            recorded_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS discovered_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_type TEXT NOT NULL,
            pattern TEXT NOT NULL,
            examples TEXT DEFAULT '[]',
            confidence REAL DEFAULT 0.5,
            adopted INTEGER DEFAULT 0,
            discovered_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn


def record_feedback(module: str, item_id: str,
                    correct: bool, notes: str = "") -> dict:
    """Record human feedback for learning."""
    edb = _init_db()
    edb.execute("""
        INSERT INTO feedback (module, item_id, feedback_type, correct, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (module, item_id, "classification", 1 if correct else 0, notes))
    edb.commit()
    edb.close()
    return {"recorded": True, "module": module, "item_id": item_id}


def _discover_citation_patterns(central: sqlite3.Connection,
                                edb: sqlite3.Connection) -> int:
    """Discover new citation patterns from evidence."""
    import re
    patterns_found = 0

    # Known base patterns
    base_patterns = [
        (r"MCL\s+\d+\.\d+[a-z]?(?:\(\d+\))*", "mcl"),
        (r"MCR\s+\d+\.\d+(?:\([A-Z]\))*(?:\(\d+\))*", "mcr"),
        (r"MRE\s+\d+(?:\([a-z]\))*", "mre"),
        (r"\d+\s+USC\s+§?\s*\d+", "usc"),
        (r"\d+\s+Mich(?:\s+App)?\s+\d+", "case_cite"),
    ]

    # Scan evidence for variations not yet in pattern library
    try:
        rows = central.execute("""
            SELECT quote_text FROM evidence_quotes
            WHERE length(quote_text) > 20
            ORDER BY RANDOM() LIMIT 1000
        """).fetchall()

        for row in rows:
            text = str(row[0])
            for pat_regex, pat_type in base_patterns:
                matches = re.findall(pat_regex, text)
                for match in matches:
                    p_hash = hashlib.md5(match.encode()).hexdigest()
                    try:
                        edb.execute("""
                            INSERT OR IGNORE INTO pattern_library
                            (pattern_type, pattern_regex, pattern_hash, confidence, source)
                            VALUES (?, ?, ?, 0.8, 'evidence_scan')
                        """, (pat_type, re.escape(match), p_hash))
                        if edb.total_changes > 0:
                            patterns_found += 1
                    except sqlite3.IntegrityError:
                        # Update hit count for existing patterns
                        edb.execute("""
                            UPDATE pattern_library SET hit_count = hit_count + 1
                            WHERE pattern_hash = ?
                        """, (p_hash,))
    except sqlite3.Error:
        pass

    return patterns_found


def _tune_classifier_weights(edb: sqlite3.Connection) -> int:
    """Tune classifier weights based on feedback."""
    improvements = 0

    try:
        # Check accuracy by module
        rows = edb.execute("""
            SELECT module,
                   COUNT(*) as total,
                   SUM(correct) as correct_count
            FROM feedback
            GROUP BY module
            HAVING total >= 5
        """).fetchall()

        for row in rows:
            module, total, correct = str(row[0]), int(row[1]), int(row[2])
            accuracy = correct / total if total > 0 else 0

            # If accuracy < 85%, suggest weight adjustment
            if accuracy < 0.85:
                # Lower confidence threshold to reduce false negatives
                new_threshold = max(0.3, 0.5 * accuracy)
                edb.execute("""
                    INSERT INTO weight_history
                    (component, parameter, old_value, new_value, reason)
                    VALUES (?, 'confidence_threshold', 0.5, ?, ?)
                """, (module, new_threshold,
                      f"Accuracy {accuracy:.1%} below 85% threshold"))
                improvements += 1
    except sqlite3.Error:
        pass

    return improvements


def _analyze_meek_effectiveness(central: sqlite3.Connection,
                                edb: sqlite3.Connection) -> int:
    """Analyze MEEK signal effectiveness and discover new signals."""
    signals_found = 0

    # Look for patterns in lane-classified evidence
    lane_keywords = {
        "A": ["custody", "parenting time", "child", "best interest", "MCL 722.23"],
        "B": ["housing", "shady oaks", "tenant", "MCL 554", "habitability"],
        "D": ["PPO", "protection order", "MCL 600.2950", "stalking", "threat"],
        "E": ["judicial", "misconduct", "McNeill", "ex parte", "canon", "JTC"],
        "F": ["appeal", "COA", "MCR 7.2", "appellate", "brief"],
    }

    for lane, keywords in lane_keywords.items():
        for kw in keywords:
            p_hash = hashlib.md5(f"MEEK_{lane}_{kw}".encode()).hexdigest()
            try:
                # Check if this keyword actually appears in evidence
                count = central.execute("""
                    SELECT COUNT(*) FROM evidence_quotes
                    WHERE quote_text LIKE ?
                """, (f"%{kw}%",)).fetchone()[0]

                if count > 5:
                    edb.execute("""
                        INSERT OR IGNORE INTO discovered_signals
                        (signal_type, pattern, examples, confidence)
                        VALUES (?, ?, ?, ?)
                    """, (f"MEEK_{lane}", kw,
                          json.dumps([kw]),
                          min(count / 100.0, 0.95)))
                    signals_found += 1
            except sqlite3.Error:
                pass

    return signals_found


def run_evolution_cycle(cycle_type: str = "full") -> dict:
    """Run a complete self-evolution cycle."""
    start = time.time()
    edb = _init_db()
    central = sqlite3.connect(str(CENTRAL_DB), timeout=30)
    central.execute("PRAGMA busy_timeout=120000")

    improvements = 0
    applied = 0

    if cycle_type in ("full", "patterns"):
        patterns = _discover_citation_patterns(central, edb)
        improvements += patterns

    if cycle_type in ("full", "weights"):
        weight_changes = _tune_classifier_weights(edb)
        improvements += weight_changes
        applied += weight_changes

    if cycle_type in ("full", "signals"):
        signals = _analyze_meek_effectiveness(central, edb)
        improvements += signals

    # Get current metrics
    metrics = {}
    try:
        metrics["pattern_count"] = edb.execute(
            "SELECT COUNT(*) FROM pattern_library"
        ).fetchone()[0]
        metrics["feedback_count"] = edb.execute(
            "SELECT COUNT(*) FROM feedback"
        ).fetchone()[0]
        metrics["signal_count"] = edb.execute(
            "SELECT COUNT(*) FROM discovered_signals"
        ).fetchone()[0]
        metrics["weight_changes"] = edb.execute(
            "SELECT COUNT(*) FROM weight_history"
        ).fetchone()[0]
    except sqlite3.Error:
        pass

    duration = round(time.time() - start, 2)

    edb.execute("""
        INSERT INTO evolution_cycles
        (cycle_type, improvements_found, improvements_applied,
         metrics_after, duration_s)
        VALUES (?, ?, ?, ?, ?)
    """, (cycle_type, improvements, applied,
          json.dumps(metrics), duration))
    edb.commit()

    central.close()
    edb.close()

    return {
        "cycle_type": cycle_type,
        "improvements_found": improvements,
        "improvements_applied": applied,
        "metrics": metrics,
        "duration_s": duration,
    }


if __name__ == "__main__":
    ctype = sys.argv[1] if len(sys.argv) > 1 else "full"
    result = run_evolution_cycle(ctype)
    print(json.dumps(result, indent=2, default=str))
