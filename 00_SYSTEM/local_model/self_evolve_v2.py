#!/usr/bin/env python3
"""
THE MANBEARPIG — Self-Evolving Intelligence Engine v2.0
=======================================================
Production-grade autonomous self-improvement for the Michigan Legal
Language Model.  Analyzes performance, retrains classifiers, discovers
patterns, optimizes retrieval weights, and logs every cycle.

DB  : litigation_context.db (1.18 GB, 85+ tables)
Model: model_data/ (TF-IDF, Naive Bayes, BM25, semantic indexes)

Usage:
    python self_evolve_v2.py                # Full auto-improve cycle
    python self_evolve_v2.py --report       # Print last improvement report
    python self_evolve_v2.py --retrain      # Force retrain classifiers
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import sqlite3
import sys
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Optional heavy imports — graceful fallback
# ---------------------------------------------------------------------------
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore[assignment]
    HAS_NUMPY = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    from sklearn.model_selection import cross_val_score
    from sklearn.preprocessing import LabelEncoder
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import pickle
except ImportError:
    pickle = None  # type: ignore[assignment]

try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------
_DIR = Path(__file__).parent
_DEFAULT_DB = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)
_DEFAULT_MODEL_DIR = _DIR / "model_data"
_EVOLVE_LOG = _DIR / "evolution_log.json"

_MAX_TRAINING_SAMPLES = 200_000
_TFIDF_MAX_FEATURES = 50_000
_PLATEAU_STREAK_THRESHOLD = 3  # consecutive identical cycles to trigger adjustment

# Param grids for plateau-busting rotations
_NGRAM_OPTIONS = [(1, 2), (1, 3), (2, 3)]
_MIN_DF_OPTIONS = [1, 2, 3]
_MAX_DF_OPTIONS = [0.90, 0.93, 0.95, 0.98]
_NB_ALPHA_OPTIONS = [0.01, 0.1, 0.5, 1.0]

logger = logging.getLogger("LitigationOS.SelfEvolveV2")

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def _ts() -> str:
    """ISO-8601 UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _safe_log(msg: str) -> None:
    safe = str(msg).encode("ascii", errors="replace").decode("ascii")
    try:
        print(f"[EVOLVE-v2] {safe}", flush=True)
    except (BlockingIOError, BrokenPipeError, OSError):
        pass


def _get_db(db_path: str, readonly: bool = True) -> sqlite3.Connection | None:
    """Open DB with retry + WAL.  Returns None on total failure."""
    for attempt in range(3):
        try:
            conn = sqlite3.connect(db_path, timeout=60)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-131072")
            conn.execute("PRAGMA temp_store=MEMORY")
            if readonly:
                conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as exc:
            _safe_log(f"DB connect attempt {attempt + 1}/3: {exc}")
            time.sleep(2 ** attempt)
    return None


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    try:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        return row is not None
    except Exception:
        return False


def _safe_query(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list:
    """Execute query, return list of Row; empty list on error."""
    try:
        return conn.execute(sql, params).fetchall()
    except Exception as exc:
        _safe_log(f"Query error ({sql[:60]}...): {exc}")
        return []


def _load_pickle(path: Path):
    """Load a pickle/joblib file."""
    if not path.exists():
        return None
    try:
        if HAS_JOBLIB:
            return joblib.load(path)
        if pickle is not None:
            with open(path, "rb") as fh:
                return pickle.load(fh)
    except Exception as exc:
        _safe_log(f"Failed to load {path.name}: {exc}")
    return None


def _save_pickle(obj, path: Path) -> bool:
    """Save object via pickle."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if pickle is not None:
            with open(path, "wb") as fh:
                pickle.dump(obj, fh, protocol=4)
            return True
    except Exception as exc:
        _safe_log(f"Failed to save {path.name}: {exc}")
    return False


# ===================================================================
# SelfEvolver — main class
# ===================================================================
class SelfEvolver:
    """Autonomous self-improvement engine for the MANBEARPIG MLLM."""

    def __init__(
        self,
        db_path: str = _DEFAULT_DB,
        model_data_dir: str | Path = _DEFAULT_MODEL_DIR,
    ):
        self.db_path = str(db_path)
        self.model_dir = Path(model_data_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._cycle_start: float = 0.0
        _safe_log(f"SelfEvolver v2 init — DB={self.db_path}")
        _safe_log(f"  model_dir={self.model_dir}")
        _safe_log(f"  sklearn={HAS_SKLEARN}  numpy={HAS_NUMPY}  joblib={HAS_JOBLIB}")

    # ------------------------------------------------------------------
    # 1. Analyze Query Performance
    # ------------------------------------------------------------------
    def analyze_query_performance(self) -> dict:
        """Analyze query logs / engine metrics to find weak and strong areas.

        Checks memory_store (from persistent_memory.py) first, then
        engine_metrics, then falls back to a synthetic baseline from
        mllm_improvement_cycles.
        """
        _safe_log("Analyzing query performance ...")
        result: dict = {"weak_areas": [], "strong_areas": [], "recommendations": []}
        conn = _get_db(self.db_path)
        if conn is None:
            result["recommendations"].append("DB unavailable — cannot analyze")
            return result

        try:
            query_data: list[dict] = []

            # Source 1: memory_store (persistent_memory.py)
            if _table_exists(conn, "memory_store"):
                rows = _safe_query(
                    conn,
                    "SELECT key, value FROM memory_store "
                    "WHERE key LIKE '%query%' OR key LIKE '%perf%' LIMIT 500",
                )
                for r in rows:
                    try:
                        val = json.loads(r["value"]) if r["value"] else {}
                        query_data.append({"source": "memory_store", **val})
                    except (json.JSONDecodeError, TypeError):
                        query_data.append({"source": "memory_store", "raw": r["value"]})

            # Source 2: engine_metrics
            if _table_exists(conn, "engine_metrics"):
                rows = _safe_query(
                    conn,
                    "SELECT * FROM engine_metrics ORDER BY rowid DESC LIMIT 200",
                )
                for r in rows:
                    query_data.append(dict(r))

            # Source 3: audit_metrics
            if _table_exists(conn, "audit_metrics"):
                rows = _safe_query(
                    conn,
                    "SELECT metric_name, metric_value, detail, measured_at "
                    "FROM audit_metrics ORDER BY measured_at DESC LIMIT 200",
                )
                for r in rows:
                    query_data.append(dict(r))

            # Source 4: mllm_improvement_cycles (fallback / trend)
            cycle_rows = _safe_query(
                conn,
                "SELECT cycle_num, pass_rate, intent_accuracy, avg_confidence, "
                "avg_latency_ms, failures_json, category_scores_json "
                "FROM mllm_improvement_cycles ORDER BY id DESC LIMIT 20",
            )

            # --- Analyze cycles for trends ---
            if cycle_rows:
                pass_rates = [r["pass_rate"] for r in cycle_rows if r["pass_rate"] is not None]
                latencies = [r["avg_latency_ms"] for r in cycle_rows if r["avg_latency_ms"] is not None]
                accuracies = [r["intent_accuracy"] for r in cycle_rows if r["intent_accuracy"] is not None]

                # Normalize: if values > 1 assume percentage (0-100 scale)
                if pass_rates and max(pass_rates) > 1.0:
                    pass_rates = [p / 100.0 for p in pass_rates]
                if accuracies and max(accuracies) > 1.0:
                    accuracies = [a / 100.0 for a in accuracies]

                if pass_rates:
                    avg_pass = sum(pass_rates) / len(pass_rates)
                    if avg_pass < 0.7:
                        result["weak_areas"].append(
                            f"Low avg pass rate: {avg_pass:.1%} over last {len(pass_rates)} cycles"
                        )
                    else:
                        result["strong_areas"].append(
                            f"Pass rate healthy: {avg_pass:.1%}"
                        )
                    # Trend: improving or degrading?
                    if len(pass_rates) >= 3:
                        recent = sum(pass_rates[:3]) / 3
                        older = sum(pass_rates[-3:]) / 3
                        if recent < older - 0.05:
                            result["weak_areas"].append(
                                f"Pass rate declining: {older:.1%} → {recent:.1%}"
                            )
                            result["recommendations"].append(
                                "Retrain classifier — pass rate is degrading"
                            )

                if latencies:
                    avg_lat = sum(latencies) / len(latencies)
                    if avg_lat > 500:
                        result["weak_areas"].append(
                            f"High avg latency: {avg_lat:.0f}ms"
                        )
                        result["recommendations"].append(
                            "Optimize retrieval — latency exceeding 500ms target"
                        )
                    else:
                        result["strong_areas"].append(
                            f"Latency acceptable: {avg_lat:.0f}ms"
                        )

                if accuracies:
                    avg_acc = sum(accuracies) / len(accuracies)
                    if avg_acc < 0.8:
                        result["weak_areas"].append(
                            f"Intent accuracy below threshold: {avg_acc:.1%}"
                        )
                        result["recommendations"].append(
                            "Add more training data for intent classification"
                        )
                    else:
                        result["strong_areas"].append(
                            f"Intent accuracy: {avg_acc:.1%}"
                        )

                # Parse category scores from latest cycle
                latest = cycle_rows[0]
                if latest["category_scores_json"]:
                    try:
                        cat_scores = json.loads(latest["category_scores_json"])
                        for cat, score in cat_scores.items():
                            score_val = float(score) if not isinstance(score, (int, float)) else score
                            # Normalize: if value > 1 assume percentage (0-100)
                            if score_val > 1.0:
                                score_val = score_val / 100.0
                            if score_val < 0.6:
                                result["weak_areas"].append(
                                    f"Category '{cat}' weak: {score_val:.1%}"
                                )
                            elif score_val >= 0.9:
                                result["strong_areas"].append(
                                    f"Category '{cat}' excellent: {score_val:.1%}"
                                )
                    except (json.JSONDecodeError, TypeError, ValueError):
                        pass

                # Parse failures
                if latest["failures_json"]:
                    try:
                        failures = json.loads(latest["failures_json"])
                        if isinstance(failures, list) and len(failures) > 3:
                            result["recommendations"].append(
                                f"{len(failures)} test failures in last cycle — review test suite"
                            )
                    except (json.JSONDecodeError, TypeError):
                        pass

            # If we had NO data at all, build synthetic baseline
            if not cycle_rows and not query_data:
                result["weak_areas"].append("No performance data found — cold start")
                result["recommendations"].append(
                    "Run enhancement_cycle.py to generate baseline metrics"
                )
                result["recommendations"].append(
                    "Run train_model.py or retrain_v5.py to build initial model"
                )
        except Exception as exc:
            _safe_log(f"analyze_query_performance error: {exc}")
            result["recommendations"].append(f"Analysis error: {exc}")
        finally:
            conn.close()

        _safe_log(
            f"  weak={len(result['weak_areas'])} strong={len(result['strong_areas'])} "
            f"recs={len(result['recommendations'])}"
        )
        return result

    # ------------------------------------------------------------------
    # 2. Retrain Classifier
    # ------------------------------------------------------------------
    def retrain_classifier(self, force: bool = False) -> dict:
        """Retrain TF-IDF + Naive Bayes on current DB data.

        Only saves new model if accuracy improves (or force=True).
        """
        _safe_log(f"Retrain classifier (force={force}) ...")
        report: dict = {
            "old_accuracy": 0.0,
            "new_accuracy": 0.0,
            "improved": False,
            "samples_used": 0,
            "error": None,
        }

        if not HAS_SKLEARN:
            report["error"] = "sklearn not available — cannot retrain"
            _safe_log(report["error"])
            return report

        conn = _get_db(self.db_path)
        if conn is None:
            report["error"] = "DB unavailable"
            return report

        try:
            texts: list[str] = []
            labels: list[str] = []

            # --- Collect training data ---
            # evidence_quotes: quote_text → evidence_category
            if _table_exists(conn, "evidence_quotes"):
                rows = _safe_query(
                    conn,
                    "SELECT quote_text, evidence_category FROM evidence_quotes "
                    "WHERE quote_text IS NOT NULL AND evidence_category IS NOT NULL "
                    f"LIMIT {_MAX_TRAINING_SAMPLES}",
                )
                for r in rows:
                    t = (r["quote_text"] or "").strip()
                    lbl = (r["evidence_category"] or "").strip()
                    if len(t) > 20 and lbl:
                        texts.append(t[:2000])
                        labels.append(lbl)
                _safe_log(f"  evidence_quotes: {len(rows)} rows")

            # auth_rules: full_text → rule_type
            if _table_exists(conn, "auth_rules"):
                rows = _safe_query(
                    conn,
                    "SELECT full_text, rule_type FROM auth_rules "
                    "WHERE full_text IS NOT NULL AND rule_type IS NOT NULL "
                    f"LIMIT {_MAX_TRAINING_SAMPLES}",
                )
                for r in rows:
                    t = (r["full_text"] or "").strip()
                    lbl = (r["rule_type"] or "").strip()
                    if len(t) > 20 and lbl:
                        texts.append(t[:2000])
                        labels.append(f"rule:{lbl}")
                _safe_log(f"  auth_rules: {len(rows)} rows")

            # claims: proposition → classification
            if _table_exists(conn, "claims"):
                rows = _safe_query(
                    conn,
                    "SELECT proposition, classification FROM claims "
                    "WHERE proposition IS NOT NULL AND classification IS NOT NULL "
                    f"LIMIT {_MAX_TRAINING_SAMPLES}",
                )
                for r in rows:
                    t = (r["proposition"] or "").strip()
                    lbl = (r["classification"] or "").strip()
                    if len(t) > 10 and lbl:
                        texts.append(t[:2000])
                        labels.append(f"claim:{lbl}")
                _safe_log(f"  claims: {len(rows)} rows")

            report["samples_used"] = len(texts)

            if len(texts) < 50:
                report["error"] = f"Insufficient training data: {len(texts)} samples"
                _safe_log(report["error"])
                conn.close()
                return report

            _safe_log(f"  Total training samples: {len(texts)}")

            # --- Load existing model for baseline accuracy ---
            old_vectorizer = _load_pickle(self.model_dir / "vectorizer.pkl")
            old_clf = _load_pickle(self.model_dir / "doctype_clf.pkl")

            if old_vectorizer is not None and old_clf is not None:
                try:
                    le_old = LabelEncoder()
                    y_old = le_old.fit_transform(labels)
                    X_old = old_vectorizer.transform(texts)
                    old_preds = old_clf.predict(X_old)
                    if HAS_NUMPY:
                        report["old_accuracy"] = float(np.mean(old_preds == y_old))
                    else:
                        correct = sum(1 for p, a in zip(old_preds, y_old) if p == a)
                        report["old_accuracy"] = correct / len(y_old) if y_old.size else 0.0
                    _safe_log(f"  Old model accuracy: {report['old_accuracy']:.3f}")
                except Exception as exc:
                    _safe_log(f"  Old model eval failed (schema drift?): {exc}")
                    report["old_accuracy"] = 0.0

            # --- Train new model ---
            le = LabelEncoder()
            y = le.fit_transform(labels)

            n_classes = len(set(y))
            if n_classes < 2:
                report["error"] = f"Need >=2 classes, got {n_classes}"
                conn.close()
                return report

            vectorizer = TfidfVectorizer(
                max_features=_TFIDF_MAX_FEATURES,
                ngram_range=getattr(self, "_tfidf_ngram_range", (1, 2)),
                min_df=getattr(self, "_tfidf_min_df", 2),
                max_df=getattr(self, "_tfidf_max_df", 0.95),
                sublinear_tf=True,
            )
            X = vectorizer.fit_transform(texts)

            clf = MultinomialNB(alpha=getattr(self, "_nb_alpha", 0.1))
            clf.fit(X, y)

            # Cross-validation accuracy
            cv_folds = min(5, n_classes, len(texts) // 10)
            if cv_folds >= 2:
                scores = cross_val_score(clf, X, y, cv=cv_folds, scoring="accuracy")
                report["new_accuracy"] = float(scores.mean())
            else:
                # Fallback: training accuracy
                preds = clf.predict(X)
                if HAS_NUMPY:
                    report["new_accuracy"] = float(np.mean(preds == y))
                else:
                    correct = sum(1 for p, a in zip(preds, y) if p == a)
                    report["new_accuracy"] = correct / len(y)

            _safe_log(f"  New model accuracy: {report['new_accuracy']:.3f}")
            report["improved"] = report["new_accuracy"] > report["old_accuracy"]

            # --- Save if improved or forced ---
            if report["improved"] or force:
                saved_vec = _save_pickle(vectorizer, self.model_dir / "vectorizer.pkl")
                saved_clf = _save_pickle(clf, self.model_dir / "doctype_clf.pkl")
                # Save label encoder for inference
                _save_pickle(le, self.model_dir / "label_encoder.pkl")
                if saved_vec and saved_clf:
                    _safe_log("  New model SAVED")
                    # Update manifest
                    manifest_path = self.model_dir / "manifest.json"
                    manifest: dict = {}
                    if manifest_path.exists():
                        try:
                            with open(manifest_path) as fh:
                                manifest = json.load(fh)
                        except Exception:
                            pass
                    manifest["last_retrain"] = _ts()
                    manifest["retrain_samples"] = len(texts)
                    manifest["retrain_accuracy"] = report["new_accuracy"]
                    manifest["retrain_classes"] = n_classes
                    try:
                        with open(manifest_path, "w") as fh:
                            json.dump(manifest, fh, indent=2)
                    except Exception:
                        pass
                else:
                    _safe_log("  WARNING: Model save failed")
            else:
                _safe_log("  New model NOT better — keeping old")

        except Exception as exc:
            report["error"] = str(exc)
            _safe_log(f"  Retrain error: {exc}")
        finally:
            conn.close()

        return report

    # ------------------------------------------------------------------
    # 3. Discover New Patterns
    # ------------------------------------------------------------------
    def discover_new_patterns(self) -> dict:
        """Scan contradiction_map, impeachment_items, evidence_quotes
        for new patterns and high-value cross-claim evidence."""
        _safe_log("Discovering new patterns ...")
        result: dict = {
            "new_patterns": [],
            "high_value_evidence": [],
            "gaps_found": [],
        }

        conn = _get_db(self.db_path)
        if conn is None:
            return result

        try:
            # --- Contradiction patterns ---
            if _table_exists(conn, "contradiction_map"):
                type_counts = _safe_query(
                    conn,
                    "SELECT contradiction_type, COUNT(*) as cnt, "
                    "AVG(CASE severity "
                    "  WHEN 'critical' THEN 4 WHEN 'high' THEN 3 "
                    "  WHEN 'medium' THEN 2 ELSE 1 END) as avg_sev "
                    "FROM contradiction_map "
                    "GROUP BY contradiction_type ORDER BY cnt DESC",
                )
                known_types = {
                    "factual", "temporal", "procedural", "legal",
                    "testimonial", "documentary",
                }
                for r in type_counts:
                    ct = (r["contradiction_type"] or "").strip().lower()
                    if ct and ct not in known_types:
                        result["new_patterns"].append({
                            "type": "contradiction",
                            "subtype": r["contradiction_type"],
                            "count": r["cnt"],
                            "avg_severity": round(r["avg_sev"], 2) if r["avg_sev"] else 0,
                        })

                # High-severity contradictions
                high_sev = _safe_query(
                    conn,
                    "SELECT source_a_text, source_b_text, contradiction_type, severity "
                    "FROM contradiction_map WHERE severity IN ('critical','high') "
                    "ORDER BY rowid DESC LIMIT 10",
                )
                for r in high_sev:
                    result["new_patterns"].append({
                        "type": "high_severity_contradiction",
                        "contradiction_type": r["contradiction_type"],
                        "severity": r["severity"],
                        "snippet_a": (r["source_a_text"] or "")[:120],
                        "snippet_b": (r["source_b_text"] or "")[:120],
                    })

            # --- Impeachment vectors ---
            if _table_exists(conn, "impeachment_items"):
                imp_types = _safe_query(
                    conn,
                    "SELECT item_type, COUNT(*) as cnt "
                    "FROM impeachment_items GROUP BY item_type ORDER BY cnt DESC",
                )
                known_imp = {"prior_inconsistent", "bias", "character", "contradiction"}
                for r in imp_types:
                    it = (r["item_type"] or "").strip().lower()
                    if it and it not in known_imp:
                        result["new_patterns"].append({
                            "type": "impeachment_vector",
                            "subtype": r["item_type"],
                            "count": r["cnt"],
                        })

            # --- High-value evidence (supports multiple claims) ---
            if _table_exists(conn, "evidence_quotes") and _table_exists(conn, "claims"):
                # Find evidence quotes referenced in multiple claim evidence_targets
                multi_claim = _safe_query(
                    conn,
                    "SELECT eq.id, eq.quote_text, eq.evidence_category, "
                    "eq.legal_significance, COUNT(DISTINCT c.claim_id) as claim_count "
                    "FROM evidence_quotes eq "
                    "JOIN claims c ON c.evidence_targets LIKE '%' || eq.id || '%' "
                    "GROUP BY eq.id HAVING claim_count > 1 "
                    "ORDER BY claim_count DESC LIMIT 20",
                )
                for r in multi_claim:
                    result["high_value_evidence"].append({
                        "evidence_id": r["id"],
                        "category": r["evidence_category"],
                        "claims_supported": r["claim_count"],
                        "significance": (r["legal_significance"] or "")[:150],
                        "snippet": (r["quote_text"] or "")[:150],
                    })

            # --- Underutilized evidence (no claims reference it) ---
            if _table_exists(conn, "evidence_quotes"):
                cat_counts = _safe_query(
                    conn,
                    "SELECT evidence_category, COUNT(*) as cnt "
                    "FROM evidence_quotes WHERE evidence_category IS NOT NULL "
                    "GROUP BY evidence_category ORDER BY cnt DESC",
                )
                total_evidence = sum(r["cnt"] for r in cat_counts) if cat_counts else 0
                for r in cat_counts:
                    if r["cnt"] < max(3, total_evidence * 0.01):
                        result["gaps_found"].append({
                            "type": "underutilized_evidence_category",
                            "category": r["evidence_category"],
                            "count": r["cnt"],
                            "pct_of_total": round(100 * r["cnt"] / max(total_evidence, 1), 2),
                        })

            # --- Gap: claims without evidence ---
            if _table_exists(conn, "claims"):
                unsupported = _safe_query(
                    conn,
                    "SELECT COUNT(*) as cnt FROM claims "
                    "WHERE (evidence_targets IS NULL OR evidence_targets = '')",
                )
                if unsupported and unsupported[0]["cnt"] > 0:
                    result["gaps_found"].append({
                        "type": "unsupported_claims",
                        "count": unsupported[0]["cnt"],
                        "recommendation": "Link evidence to claims via evidence_targets",
                    })

        except Exception as exc:
            _safe_log(f"discover_new_patterns error: {exc}")
        finally:
            conn.close()

        _safe_log(
            f"  patterns={len(result['new_patterns'])} "
            f"high_value={len(result['high_value_evidence'])} "
            f"gaps={len(result['gaps_found'])}"
        )
        return result

    # ------------------------------------------------------------------
    # 4. Optimize Engine Weights
    # ------------------------------------------------------------------
    def optimize_engine_weights(self) -> dict:
        """Evaluate BM25, Semantic, FTS5 on sample queries; suggest RRF weights."""
        _safe_log("Optimizing engine weights ...")
        result: dict = {
            "current_weights": {"bm25": 1.0, "semantic": 1.0, "fts5": 1.0},
            "recommended_weights": {"bm25": 1.0, "semantic": 1.0, "fts5": 1.0},
            "improvement_estimate": 0.0,
            "engine_scores": {},
            "error": None,
        }

        # Sample queries covering ALL MEEK lanes (30+)
        sample_queries = [
            # --- Lane A: Custody (MEEK2) ---
            {"query": "MCR 2.003 disqualification bias", "expect": ["2.003", "disqualif"]},
            {"query": "MCL 722.23 best interest factors", "expect": ["722.23", "best interest"]},
            {"query": "parental alienation factor j", "expect": ["alienat", "factor"]},
            {"query": "established custodial environment ECE", "expect": ["custodial", "environment"]},
            {"query": "friend of court FOC recommendation", "expect": ["friend", "court"]},
            {"query": "MCL 722.27a change of domicile", "expect": ["722.27", "domicile"]},
            {"query": "child support deviation factors", "expect": ["support", "deviation"]},
            {"query": "parenting time modification", "expect": ["parenting", "modif"]},
            # --- Lane B: Housing / Shady Oaks (MEEK1) ---
            {"query": "MCL 600.5714 summary proceedings landlord tenant", "expect": ["600.5714", "landlord"]},
            {"query": "MCL 554.601a habitability warranty", "expect": ["554.601", "habitab"]},
            {"query": "mobile home park tenant rights", "expect": ["mobile", "tenant"]},
            {"query": "MCL 125.530 park closure", "expect": ["125.530", "park"]},
            {"query": "rent escrow uninhabitable conditions", "expect": ["escrow", "condition"]},
            # --- Lane C: Convergence ---
            {"query": "MCR 2.612 relief from judgment fraud", "expect": ["2.612", "judgment"]},
            {"query": "MCR 2.116 summary disposition standard", "expect": ["2.116", "summary"]},
            {"query": "due process fundamental rights", "expect": ["due process", "right"]},
            {"query": "equal protection fourteenth amendment", "expect": ["equal", "protection"]},
            # --- Lane D: PPO (MEEK3) ---
            {"query": "personal protection order PPO", "expect": ["protect", "PPO"]},
            {"query": "contempt of court sanctions", "expect": ["contempt", "sanction"]},
            {"query": "MCL 600.2950 domestic PPO", "expect": ["600.2950", "PPO"]},
            {"query": "show cause contempt hearing", "expect": ["show cause", "contempt"]},
            # --- Lane E: Judicial Misconduct (MEEK4) ---
            {"query": "MCR 9.116 judicial tenure commission", "expect": ["9.116", "judicial"]},
            {"query": "canon 2 impropriety appearance", "expect": ["canon", "impropriety"]},
            {"query": "judicial disqualification recusal", "expect": ["disqualif", "recusal"]},
            {"query": "code of judicial conduct bias", "expect": ["judicial", "bias"]},
            # --- Lane F: Appellate (MEEK5) ---
            {"query": "appeal of right claim of appeal", "expect": ["7.204", "appeal"]},
            {"query": "MCR 7.212 brief requirements appellate", "expect": ["7.212", "brief"]},
            {"query": "MCR 7.215 court of appeals opinion", "expect": ["7.215", "opinion"]},
            {"query": "MCR 7.305 supreme court application", "expect": ["7.305", "supreme"]},
            # --- General legal/discovery ---
            {"query": "discovery motion to compel", "expect": ["discovery", "compel"]},
            {"query": "MCR 2.313 discovery sanctions failure", "expect": ["2.313", "sanction"]},
            {"query": "MRE 803 hearsay exception records", "expect": ["803", "hearsay"]},
        ]

        conn = _get_db(self.db_path)
        if conn is None:
            result["error"] = "DB unavailable"
            return result

        try:
            engine_hits: dict[str, list[float]] = {
                "bm25": [],
                "semantic": [],
                "fts5": [],
            }

            # --- FTS5 evaluation (always available) ---
            fts_tables = [
                ("evidence_quotes_fts", "quote_text"),
                ("auth_rules_fts", "full_text"),
                ("rules_text_fts", "context"),
            ]
            for sq in sample_queries:
                # Build safe FTS query
                tokens = []
                for word in sq["query"].split():
                    cleaned = "".join(ch for ch in word if ch.isalnum() or ch in "._-")
                    if cleaned:
                        tokens.append(f'"{cleaned}"')
                if not tokens:
                    continue
                fts_q = " OR ".join(tokens)

                fts_hits = 0
                fts_total = 0
                for tbl, col in fts_tables:
                    if not _table_exists(conn, tbl):
                        continue
                    rows = _safe_query(
                        conn,
                        f"SELECT {col} FROM {tbl} WHERE {tbl} MATCH ? LIMIT 5",
                        (fts_q,),
                    )
                    for r in rows:
                        text_lower = (r[col] or "").lower()
                        hit = sum(1 for kw in sq["expect"] if kw.lower() in text_lower)
                        fts_hits += hit
                        fts_total += len(sq["expect"])

                score = fts_hits / max(fts_total, 1)
                engine_hits["fts5"].append(score)

            # --- BM25 / Semantic evaluation via proxy ---
            # Use inverted_index or pages_fts as BM25 proxy
            for sq in sample_queries:
                # BM25 proxy: raw term frequency in pages
                bm25_score = 0.0
                if _table_exists(conn, "pages_fts"):
                    tokens = []
                    for word in sq["query"].split():
                        cleaned = "".join(ch for ch in word if ch.isalnum())
                        if cleaned:
                            tokens.append(f'"{cleaned}"')
                    if tokens:
                        fts_q = " OR ".join(tokens)
                        rows = _safe_query(
                            conn,
                            "SELECT text_content FROM pages_fts WHERE pages_fts MATCH ? LIMIT 5",
                            (fts_q,),
                        )
                        for r in rows:
                            text_lower = (r["text_content"] or "").lower()
                            hit = sum(1 for kw in sq["expect"] if kw.lower() in text_lower)
                            bm25_score += hit / max(len(sq["expect"]), 1)
                        bm25_score /= max(len(rows), 1)
                engine_hits["bm25"].append(bm25_score)

                # Semantic proxy: md_sections keyword overlap
                sem_score = 0.0
                if _table_exists(conn, "md_sections_fts"):
                    tokens = []
                    for word in sq["query"].split():
                        cleaned = "".join(ch for ch in word if ch.isalnum())
                        if cleaned:
                            tokens.append(f'"{cleaned}"')
                    if tokens:
                        fts_q = " OR ".join(tokens)
                        rows = _safe_query(
                            conn,
                            "SELECT content FROM md_sections_fts "
                            "WHERE md_sections_fts MATCH ? LIMIT 5",
                            (fts_q,),
                        )
                        for r in rows:
                            text_lower = (r["content"] or "").lower()
                            hit = sum(1 for kw in sq["expect"] if kw.lower() in text_lower)
                            sem_score += hit / max(len(sq["expect"]), 1)
                        sem_score /= max(len(rows), 1)
                engine_hits["semantic"].append(sem_score)

            # --- Compute average scores and recommended weights ---
            for engine, scores in engine_hits.items():
                if scores:
                    avg = sum(scores) / len(scores)
                    result["engine_scores"][engine] = round(avg, 4)
                else:
                    result["engine_scores"][engine] = 0.0

            total_score = sum(result["engine_scores"].values())
            if total_score > 0:
                for engine in result["recommended_weights"]:
                    raw = result["engine_scores"].get(engine, 0.0)
                    # Normalize so weights sum to 3.0 (same total as equal weights)
                    result["recommended_weights"][engine] = round(
                        3.0 * raw / total_score, 3
                    )

            # Estimate improvement from reweighting
            current_uniform = sum(result["engine_scores"].values()) / 3
            weighted_sum = sum(
                result["engine_scores"].get(e, 0) * result["recommended_weights"].get(e, 1)
                for e in result["engine_scores"]
            )
            weighted_avg = weighted_sum / max(sum(result["recommended_weights"].values()), 1)
            result["improvement_estimate"] = round(
                max(0, weighted_avg - current_uniform), 4
            )

        except Exception as exc:
            result["error"] = str(exc)
            _safe_log(f"optimize_engine_weights error: {exc}")
        finally:
            conn.close()

        _safe_log(f"  scores={result['engine_scores']}")
        _safe_log(f"  recommended={result['recommended_weights']}")
        return result

    # ------------------------------------------------------------------
    # 5. Track Accuracy
    # ------------------------------------------------------------------
    def track_accuracy(self, predictions: list, actuals: list) -> dict:
        """Store prediction-vs-actual accuracy to audit_metrics."""
        _safe_log(f"Tracking accuracy — {len(predictions)} predictions ...")
        if len(predictions) != len(actuals):
            return {"error": "predictions and actuals must be same length"}

        correct = sum(1 for p, a in zip(predictions, actuals) if p == a)
        total = len(predictions)
        accuracy = correct / max(total, 1)

        conn = _get_db(self.db_path, readonly=False)
        if conn is None:
            return {"accuracy": accuracy, "stored": False}

        try:
            if not _table_exists(conn, "audit_metrics"):
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS audit_metrics ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "metric_name TEXT, metric_value REAL, "
                    "detail TEXT, measured_at TEXT DEFAULT (datetime('now')))"
                )
            conn.execute(
                "INSERT INTO audit_metrics (metric_name, metric_value, detail) "
                "VALUES (?, ?, ?)",
                (
                    "prediction_accuracy",
                    accuracy,
                    json.dumps({
                        "correct": correct,
                        "total": total,
                        "timestamp": _ts(),
                    }),
                ),
            )
            conn.commit()
            _safe_log(f"  Accuracy: {accuracy:.3f} ({correct}/{total})")
            return {"accuracy": accuracy, "correct": correct, "total": total, "stored": True}
        except Exception as exc:
            _safe_log(f"track_accuracy error: {exc}")
            return {"accuracy": accuracy, "stored": False, "error": str(exc)}
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 6. Evolve Thesaurus
    # ------------------------------------------------------------------
    def evolve_thesaurus(self) -> dict:
        """Analyze query patterns and evidence to suggest thesaurus additions."""
        _safe_log("Evolving thesaurus ...")
        result: dict = {
            "current_size": 0,
            "suggested_additions": [],
            "estimated_improvement": 0.0,
        }

        # Load current thesaurus from query_expander.py
        current_thesaurus: dict = {}
        try:
            qe_path = _DIR / "query_expander.py"
            if qe_path.exists():
                sys.path.insert(0, str(_DIR))
                try:
                    from query_expander import QueryExpander
                    qe = QueryExpander.__new__(QueryExpander)
                    current_thesaurus = QueryExpander._build_thesaurus()
                except Exception as exc:
                    _safe_log(f"  Could not load QueryExpander: {exc}")
        except Exception:
            pass

        all_terms: set[str] = set()
        for key, synonyms in current_thesaurus.items():
            all_terms.add(key.lower())
            for s in synonyms:
                all_terms.add(s.lower())
        result["current_size"] = len(all_terms)

        conn = _get_db(self.db_path)
        if conn is None:
            return result

        try:
            # --- Mine frequent terms from evidence_quotes ---
            term_freq: Counter = Counter()

            if _table_exists(conn, "evidence_quotes"):
                rows = _safe_query(
                    conn,
                    "SELECT quote_text FROM evidence_quotes "
                    "WHERE quote_text IS NOT NULL LIMIT 10000",
                )
                for r in rows:
                    text = (r["quote_text"] or "").lower()
                    # Extract multi-word legal phrases (2-3 word ngrams)
                    words = re.findall(r"[a-z]+(?:\s+[a-z]+){1,2}", text)
                    for phrase in words:
                        phrase = phrase.strip()
                        if len(phrase) > 5 and phrase not in all_terms:
                            term_freq[phrase] += 1

            # --- Mine from auth_rules titles ---
            if _table_exists(conn, "auth_rules"):
                rows = _safe_query(
                    conn,
                    "SELECT DISTINCT title FROM auth_rules WHERE title IS NOT NULL LIMIT 500",
                )
                for r in rows:
                    title = (r["title"] or "").lower().strip()
                    if title and title not in all_terms and len(title) > 3:
                        term_freq[title] += 5  # Boost authority titles

            # --- Mine from master_citations context ---
            if _table_exists(conn, "master_citations"):
                rows = _safe_query(
                    conn,
                    "SELECT citation, cite_type FROM master_citations "
                    "WHERE citation IS NOT NULL LIMIT 5000",
                )
                citation_types: Counter = Counter()
                for r in rows:
                    ct = (r["cite_type"] or "").lower().strip()
                    if ct:
                        citation_types[ct] += 1
                # Suggest under-represented citation types
                for ct, cnt in citation_types.items():
                    if ct not in all_terms and cnt >= 3:
                        term_freq[ct] += cnt

            # --- Filter to high-frequency unknown terms ---
            suggestions: list[dict] = []
            for term, freq in term_freq.most_common(50):
                if freq >= 3:
                    # Find which existing thesaurus group it might belong to
                    best_group = None
                    best_overlap = 0
                    term_words = set(term.split())
                    for key, synonyms in current_thesaurus.items():
                        group_words = set(key.lower().split())
                        for s in synonyms:
                            group_words.update(s.lower().split())
                        overlap = len(term_words & group_words)
                        if overlap > best_overlap:
                            best_overlap = overlap
                            best_group = key

                    suggestions.append({
                        "term": term,
                        "frequency": freq,
                        "suggested_group": best_group,
                        "overlap_score": best_overlap,
                    })

            result["suggested_additions"] = suggestions[:30]
            if result["current_size"] > 0 and suggestions:
                result["estimated_improvement"] = round(
                    min(0.15, len(suggestions) / max(result["current_size"], 1)), 4
                )

        except Exception as exc:
            _safe_log(f"evolve_thesaurus error: {exc}")
        finally:
            conn.close()

        _safe_log(f"  current={result['current_size']} suggestions={len(result['suggested_additions'])}")
        return result

    # ------------------------------------------------------------------
    # 7. Evolve Entity Aliases
    # ------------------------------------------------------------------
    def evolve_entity_aliases(self) -> dict:
        """Find new name variants in documents not yet in entity_resolver aliases."""
        _safe_log("Evolving entity aliases ...")
        result: dict = {"current_aliases": 0, "suggestions": []}

        # Load current aliases
        known_aliases: dict[str, list[str]] = {}
        try:
            sys.path.insert(0, str(_DIR))
            try:
                from entity_resolver import EntityResolver
                er = EntityResolver.__new__(EntityResolver)
                known_aliases = EntityResolver._build_canonical_map(er)
            except Exception as exc:
                _safe_log(f"  Could not load EntityResolver: {exc}")
        except Exception:
            pass

        all_known: set[str] = set()
        for canonical, aliases in known_aliases.items():
            all_known.add(canonical.lower())
            for a in aliases:
                all_known.add(a.lower())
        result["current_aliases"] = len(all_known)

        conn = _get_db(self.db_path)
        if conn is None:
            return result

        try:
            # Key entities to look for new variants of
            target_entities = {
                "Andrew Pigors": ["pigors", "andrew"],
                "Tiffany Watson": ["watson", "tiffany"],
                "Judge McNeill": ["mcneill", "jenny"],
                "Friend of the Court": ["foc", "friend"],
            }

            name_variants: Counter = Counter()

            # Scan evidence_quotes speaker field
            if _table_exists(conn, "evidence_quotes"):
                rows = _safe_query(
                    conn,
                    "SELECT DISTINCT speaker FROM evidence_quotes "
                    "WHERE speaker IS NOT NULL LIMIT 1000",
                )
                for r in rows:
                    speaker = (r["speaker"] or "").strip()
                    if speaker and speaker.lower() not in all_known and len(speaker) > 2:
                        name_variants[speaker] += 1

            # Scan pages for name-like patterns near known entities
            if _table_exists(conn, "pages"):
                for canonical, keywords in target_entities.items():
                    kw_pattern = "|".join(keywords)
                    rows = _safe_query(
                        conn,
                        "SELECT substr(text_content, 1, 500) as snippet FROM pages "
                        "WHERE text_content LIKE ? LIMIT 200",
                        (f"%{keywords[0]}%",),
                    )
                    for r in rows:
                        snippet = r["snippet"] or ""
                        # Extract capitalized name patterns near keywords
                        names = re.findall(
                            r"\b([A-Z][a-z]+(?:\s+[A-Z]\.?\s+)?[A-Z][a-z]+)\b",
                            snippet,
                        )
                        for name in names:
                            name_clean = name.strip()
                            if name_clean.lower() not in all_known and len(name_clean) > 4:
                                # Check if it contains a keyword for this entity
                                if any(kw in name_clean.lower() for kw in keywords):
                                    name_variants[name_clean] += 1

            # Build suggestions
            for variant, count in name_variants.most_common(30):
                if count < 2:
                    continue
                # Find best matching canonical entity
                best_match = None
                for canonical, keywords in target_entities.items():
                    if any(kw in variant.lower() for kw in keywords):
                        best_match = canonical
                        break

                result["suggestions"].append({
                    "variant": variant,
                    "occurrences": count,
                    "suggested_canonical": best_match,
                })

        except Exception as exc:
            _safe_log(f"evolve_entity_aliases error: {exc}")
        finally:
            conn.close()

        _safe_log(f"  current={result['current_aliases']} suggestions={len(result['suggestions'])}")
        return result

    # ------------------------------------------------------------------
    # 8. Get Evolution Log
    # ------------------------------------------------------------------
    def get_evolution_log(self) -> list[dict]:
        """Return history of all improvement cycles from DB and log file."""
        _safe_log("Loading evolution log ...")
        entries: list[dict] = []

        # DB source
        conn = _get_db(self.db_path)
        if conn is not None:
            try:
                if _table_exists(conn, "mllm_improvement_cycles"):
                    rows = _safe_query(
                        conn,
                        "SELECT id, cycle_num, timestamp, pass_rate, intent_accuracy, "
                        "avg_confidence, avg_latency_ms, improvements_json "
                        "FROM mllm_improvement_cycles ORDER BY id DESC LIMIT 50",
                    )
                    for r in rows:
                        entry = {
                            "source": "db",
                            "cycle_id": r["id"],
                            "cycle_num": r["cycle_num"],
                            "timestamp": r["timestamp"],
                            "pass_rate": r["pass_rate"],
                            "intent_accuracy": r["intent_accuracy"],
                            "avg_confidence": r["avg_confidence"],
                            "avg_latency_ms": r["avg_latency_ms"],
                        }
                        if r["improvements_json"]:
                            try:
                                entry["improvements"] = json.loads(r["improvements_json"])
                            except (json.JSONDecodeError, TypeError):
                                entry["improvements"] = r["improvements_json"]
                        entries.append(entry)
            except Exception as exc:
                _safe_log(f"get_evolution_log DB error: {exc}")
            finally:
                conn.close()

        # File source
        if _EVOLVE_LOG.exists():
            try:
                with open(_EVOLVE_LOG, encoding="utf-8") as fh:
                    file_data = json.load(fh)
                if isinstance(file_data, list):
                    for item in file_data[-50:]:
                        item["source"] = "file"
                        entries.append(item)
                elif isinstance(file_data, dict):
                    file_data["source"] = "file"
                    entries.append(file_data)
            except Exception:
                pass

        _safe_log(f"  {len(entries)} log entries found")
        return entries

    # ------------------------------------------------------------------
    # 9. Generate Improvement Report
    # ------------------------------------------------------------------
    def generate_improvement_report(
        self,
        perf: dict | None = None,
        patterns: dict | None = None,
        retrain: dict | None = None,
        weights: dict | None = None,
        thesaurus: dict | None = None,
        aliases: dict | None = None,
    ) -> str:
        """Generate a human-readable improvement report."""
        lines: list[str] = []
        lines.append("=" * 70)
        lines.append("  MANBEARPIG Self-Evolution Report v2.0")
        lines.append(f"  Generated: {_ts()}")
        lines.append("=" * 70)
        lines.append("")

        # --- System Status ---
        lines.append("## System Status")
        lines.append(f"  DB: {self.db_path}")
        lines.append(f"  Model dir: {self.model_dir}")
        lines.append(f"  sklearn: {'YES' if HAS_SKLEARN else 'NO'}")
        lines.append(f"  numpy: {'YES' if HAS_NUMPY else 'NO'}")
        lines.append("")

        # --- Performance ---
        if perf:
            lines.append("## Query Performance")
            if perf.get("strong_areas"):
                lines.append("  Strengths:")
                for s in perf["strong_areas"]:
                    lines.append(f"    + {s}")
            if perf.get("weak_areas"):
                lines.append("  Weaknesses:")
                for w in perf["weak_areas"]:
                    lines.append(f"    - {w}")
            if perf.get("recommendations"):
                lines.append("  Recommendations:")
                for r in perf["recommendations"]:
                    lines.append(f"    > {r}")
            lines.append("")

        # --- Patterns ---
        if patterns:
            lines.append("## Pattern Discovery")
            lines.append(f"  New patterns: {len(patterns.get('new_patterns', []))}")
            lines.append(f"  High-value evidence: {len(patterns.get('high_value_evidence', []))}")
            lines.append(f"  Gaps found: {len(patterns.get('gaps_found', []))}")
            for g in patterns.get("gaps_found", [])[:5]:
                lines.append(f"    GAP: {g.get('type', '?')} — {g.get('count', '?')} items")
            lines.append("")

        # --- Retrain ---
        if retrain:
            lines.append("## Classifier Retrain")
            lines.append(f"  Old accuracy: {retrain.get('old_accuracy', 0):.3f}")
            lines.append(f"  New accuracy: {retrain.get('new_accuracy', 0):.3f}")
            lines.append(f"  Improved: {retrain.get('improved', False)}")
            lines.append(f"  Samples: {retrain.get('samples_used', 0)}")
            if retrain.get("error"):
                lines.append(f"  ERROR: {retrain['error']}")
            lines.append("")

        # --- Weights ---
        if weights:
            lines.append("## Engine Weight Optimization")
            lines.append(f"  Current: {weights.get('current_weights', {})}")
            lines.append(f"  Recommended: {weights.get('recommended_weights', {})}")
            lines.append(f"  Est. improvement: {weights.get('improvement_estimate', 0):.4f}")
            if weights.get("engine_scores"):
                lines.append("  Per-engine scores:")
                for eng, sc in weights["engine_scores"].items():
                    lines.append(f"    {eng}: {sc:.4f}")
            lines.append("")

        # --- Thesaurus ---
        if thesaurus:
            lines.append("## Thesaurus Evolution")
            lines.append(f"  Current terms: {thesaurus.get('current_size', 0)}")
            lines.append(f"  Suggestions: {len(thesaurus.get('suggested_additions', []))}")
            for s in thesaurus.get("suggested_additions", [])[:5]:
                lines.append(f"    + '{s['term']}' (freq={s['frequency']}, group={s.get('suggested_group', '?')})")
            lines.append("")

        # --- Entity Aliases ---
        if aliases:
            lines.append("## Entity Alias Evolution")
            lines.append(f"  Current aliases: {aliases.get('current_aliases', 0)}")
            lines.append(f"  Suggestions: {len(aliases.get('suggestions', []))}")
            for s in aliases.get("suggestions", [])[:5]:
                lines.append(
                    f"    + '{s['variant']}' -> {s.get('suggested_canonical', '?')} "
                    f"(n={s['occurrences']})"
                )
            lines.append("")

        lines.append("=" * 70)
        lines.append("  End of report")
        lines.append("=" * 70)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 10. Auto-Improve Cycle
    # ------------------------------------------------------------------
    def auto_improve_cycle(self) -> dict:
        """Run full self-improvement cycle and log results."""
        self._cycle_start = time.time()
        _safe_log("=" * 50)
        _safe_log("STARTING AUTO-IMPROVE CYCLE")
        _safe_log("=" * 50)

        report: dict = {
            "timestamp": _ts(),
            "steps": {},
            "duration_s": 0,
            "overall_status": "success",
            "plateau_detected": False,
            "adjustment_applied": None,
        }

        # --- Plateau detection: read last N entries from evolution log ---
        plateau_detected = False
        plateau_streak = 0
        try:
            if _EVOLVE_LOG.exists():
                with open(_EVOLVE_LOG, encoding="utf-8") as fh:
                    log_data = json.load(fh) if _EVOLVE_LOG.stat().st_size > 2 else []
                if isinstance(log_data, list) and len(log_data) >= _PLATEAU_STREAK_THRESHOLD:
                    recent = log_data[-_PLATEAU_STREAK_THRESHOLD:]
                    # Check if all recent entries have identical metrics
                    ref = recent[0]
                    all_same = True
                    for entry in recent[1:]:
                        if (entry.get("retrain_accuracy") != ref.get("retrain_accuracy")
                                or entry.get("engine_scores") != ref.get("engine_scores")
                                or entry.get("patterns_found") != ref.get("patterns_found")):
                            all_same = False
                            break
                    if all_same:
                        # Count how many consecutive identical entries from the end
                        streak = 1
                        for i in range(len(log_data) - 2, -1, -1):
                            e = log_data[i]
                            if (e.get("retrain_accuracy") == ref.get("retrain_accuracy")
                                    and e.get("engine_scores") == ref.get("engine_scores")
                                    and e.get("patterns_found") == ref.get("patterns_found")):
                                streak += 1
                            else:
                                break
                        plateau_streak = streak
                        plateau_detected = True
                        _safe_log(f"  ⚠ PLATEAU DETECTED: {plateau_streak} consecutive identical cycles")
        except Exception as exc:
            _safe_log(f"  Plateau detection failed (non-fatal): {exc}")

        report["plateau_detected"] = plateau_detected
        report["plateau_streak"] = plateau_streak

        # --- If plateau detected, rotate hyperparameters before retraining ---
        adjustment_applied = None
        if plateau_detected:
            import random
            # Rotate TF-IDF and NB params to break out of local optimum
            new_ngram = random.choice(_NGRAM_OPTIONS)
            new_min_df = random.choice(_MIN_DF_OPTIONS)
            new_max_df = random.choice(_MAX_DF_OPTIONS)
            new_alpha = random.choice(_NB_ALPHA_OPTIONS)
            self._tfidf_ngram_range = new_ngram
            self._tfidf_min_df = new_min_df
            self._tfidf_max_df = new_max_df
            self._nb_alpha = new_alpha
            adjustment_applied = {
                "ngram_range": list(new_ngram),
                "min_df": new_min_df,
                "max_df": new_max_df,
                "nb_alpha": new_alpha,
            }
            report["adjustment_applied"] = adjustment_applied
            _safe_log(f"  → Rotating params: {adjustment_applied}")

        # Step 1: Analyze performance
        try:
            _safe_log("[Step 1/6] Analyze query performance")
            report["steps"]["performance"] = self.analyze_query_performance()
        except Exception as exc:
            report["steps"]["performance"] = {"error": str(exc)}
            _safe_log(f"Step 1 failed: {exc}")

        # Step 2: Discover patterns
        try:
            _safe_log("[Step 2/6] Discover new patterns")
            report["steps"]["patterns"] = self.discover_new_patterns()
        except Exception as exc:
            report["steps"]["patterns"] = {"error": str(exc)}
            _safe_log(f"Step 2 failed: {exc}")

        # Step 3: Check if retrain needed
        try:
            _safe_log("[Step 3/6] Evaluate classifier retrain")
            needs_retrain = False
            # Force retrain on plateau detection
            if plateau_detected:
                needs_retrain = True
                _safe_log("  Retrain forced by plateau detection (params rotated)")
            perf = report["steps"].get("performance", {})
            # Retrain if accuracy is low or declining
            for wa in perf.get("weak_areas", []):
                if "accuracy" in wa.lower() or "declining" in wa.lower():
                    needs_retrain = True
                    break
            for rec in perf.get("recommendations", []):
                if "retrain" in rec.lower():
                    needs_retrain = True
                    break

            # Also check if model_data manifest is stale
            manifest_path = self.model_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path) as fh:
                        manifest = json.load(fh)
                    last_train = manifest.get("last_retrain", "")
                    if last_train:
                        # Parse and check age
                        try:
                            last_dt = datetime.fromisoformat(
                                last_train.replace("Z", "+00:00")
                            )
                            age_days = (
                                datetime.now(timezone.utc) - last_dt
                            ).total_seconds() / 86400
                            if age_days > 7:
                                needs_retrain = True
                                _safe_log(f"  Model is {age_days:.1f} days old — retrain triggered")
                        except (ValueError, TypeError):
                            needs_retrain = True
                except Exception:
                    needs_retrain = True
            else:
                needs_retrain = True

            if needs_retrain:
                report["steps"]["retrain"] = self.retrain_classifier(force=False)
            else:
                report["steps"]["retrain"] = {
                    "skipped": True,
                    "reason": "Model is fresh and performing well",
                }
        except Exception as exc:
            report["steps"]["retrain"] = {"error": str(exc)}
            _safe_log(f"Step 3 failed: {exc}")

        # Step 4: Optimize engine weights
        try:
            _safe_log("[Step 4/6] Optimize engine weights")
            report["steps"]["weights"] = self.optimize_engine_weights()
        except Exception as exc:
            report["steps"]["weights"] = {"error": str(exc)}
            _safe_log(f"Step 4 failed: {exc}")

        # Step 5: Evolve thesaurus + aliases
        try:
            _safe_log("[Step 5/6] Evolve thesaurus and entity aliases")
            report["steps"]["thesaurus"] = self.evolve_thesaurus()
            report["steps"]["aliases"] = self.evolve_entity_aliases()
        except Exception as exc:
            report["steps"]["thesaurus"] = {"error": str(exc)}
            report["steps"]["aliases"] = {"error": str(exc)}
            _safe_log(f"Step 5 failed: {exc}")

        # Step 6: Generate report and log
        try:
            _safe_log("[Step 6/6] Generate report and log cycle")
            report["human_report"] = self.generate_improvement_report(
                perf=report["steps"].get("performance"),
                patterns=report["steps"].get("patterns"),
                retrain=report["steps"].get("retrain"),
                weights=report["steps"].get("weights"),
                thesaurus=report["steps"].get("thesaurus"),
                aliases=report["steps"].get("aliases"),
            )
            self._log_cycle_to_db(report)
        except Exception as exc:
            _safe_log(f"Step 6 failed: {exc}")
            report["overall_status"] = "partial"

        report["duration_s"] = round(time.time() - self._cycle_start, 2)

        # Check for any step errors
        for step_name, step_data in report["steps"].items():
            if isinstance(step_data, dict) and step_data.get("error"):
                report["overall_status"] = "partial"
                break

        _safe_log(f"Cycle complete in {report['duration_s']}s — status={report['overall_status']}")
        return report

    # ------------------------------------------------------------------
    # Internal: Log cycle to DB
    # ------------------------------------------------------------------
    def _log_cycle_to_db(self, report: dict) -> None:
        """Persist cycle results to mllm_improvement_cycles table."""
        conn = _get_db(self.db_path, readonly=False)
        if conn is None:
            _safe_log("Cannot log cycle — DB unavailable")
            return

        try:
            # Ensure table exists
            if not _table_exists(conn, "mllm_improvement_cycles"):
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS mllm_improvement_cycles ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "cycle_num INTEGER, "
                    "timestamp TEXT DEFAULT (datetime('now')), "
                    "pass_rate REAL, "
                    "intent_accuracy REAL, "
                    "avg_confidence REAL, "
                    "avg_latency_ms REAL, "
                    "failures_json TEXT, "
                    "improvements_json TEXT, "
                    "category_scores_json TEXT)"
                )

            # Get next cycle number
            row = conn.execute(
                "SELECT MAX(cycle_num) FROM mllm_improvement_cycles"
            ).fetchone()
            next_num = (row[0] or 0) + 1 if row else 1

            # Extract metrics from report
            retrain = report.get("steps", {}).get("retrain", {})
            perf = report.get("steps", {}).get("performance", {})
            weights = report.get("steps", {}).get("weights", {})

            pass_rate = retrain.get("new_accuracy") or retrain.get("old_accuracy")
            intent_accuracy = pass_rate  # Same proxy for now

            improvements = {
                "v2_cycle": True,
                "duration_s": report.get("duration_s"),
                "status": report.get("overall_status"),
                "patterns_found": len(
                    report.get("steps", {}).get("patterns", {}).get("new_patterns", [])
                ),
                "gaps_found": len(
                    report.get("steps", {}).get("patterns", {}).get("gaps_found", [])
                ),
                "thesaurus_suggestions": len(
                    report.get("steps", {}).get("thesaurus", {}).get("suggested_additions", [])
                ),
                "alias_suggestions": len(
                    report.get("steps", {}).get("aliases", {}).get("suggestions", [])
                ),
                "retrain_improved": retrain.get("improved", False),
                "weight_improvement": weights.get("improvement_estimate", 0),
            }

            category_scores = weights.get("engine_scores", {})

            conn.execute(
                "INSERT INTO mllm_improvement_cycles "
                "(cycle_num, pass_rate, intent_accuracy, avg_confidence, "
                "avg_latency_ms, failures_json, improvements_json, category_scores_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    next_num,
                    pass_rate,
                    intent_accuracy,
                    None,
                    None,
                    json.dumps(perf.get("weak_areas", [])),
                    json.dumps(improvements),
                    json.dumps(category_scores),
                ),
            )
            conn.commit()
            _safe_log(f"  Cycle #{next_num} logged to DB")

        except Exception as exc:
            _safe_log(f"_log_cycle_to_db error: {exc}")
        finally:
            conn.close()

        # Also append to evolution_log.json
        try:
            existing: list = []
            if _EVOLVE_LOG.exists():
                try:
                    with open(_EVOLVE_LOG, encoding="utf-8") as fh:
                        data = json.load(fh)
                    if isinstance(data, list):
                        existing = data
                except Exception:
                    pass

            # Keep only essential fields (avoid bloating the file)
            log_entry = {
                "timestamp": report.get("timestamp"),
                "duration_s": report.get("duration_s"),
                "status": report.get("overall_status"),
                "retrain_accuracy": retrain.get("new_accuracy"),
                "patterns_found": len(
                    report.get("steps", {}).get("patterns", {}).get("new_patterns", [])
                ),
                "engine_scores": weights.get("engine_scores", {}),
                "plateau_detected": report.get("plateau_detected", False),
                "plateau_streak": report.get("plateau_streak", 0),
                "adjustment_applied": report.get("adjustment_applied"),
            }

            # Compute quality_delta from previous entry
            if existing:
                prev = existing[-1]
                prev_acc = prev.get("retrain_accuracy") or 0
                cur_acc = log_entry.get("retrain_accuracy") or 0
                log_entry["quality_delta"] = round(cur_acc - prev_acc, 6)
                prev_scores = prev.get("engine_scores", {})
                cur_scores = log_entry.get("engine_scores", {})
                log_entry["engine_score_deltas"] = {
                    k: round(cur_scores.get(k, 0) - prev_scores.get(k, 0), 6)
                    for k in set(list(prev_scores.keys()) + list(cur_scores.keys()))
                }
            else:
                log_entry["quality_delta"] = 0.0
                log_entry["engine_score_deltas"] = {}

            existing.append(log_entry)

            # Cap at 200 entries
            if len(existing) > 200:
                existing = existing[-200:]

            with open(_EVOLVE_LOG, "w", encoding="utf-8") as fh:
                json.dump(existing, fh, indent=2)
        except Exception as exc:
            _safe_log(f"evolution_log.json write error: {exc}")


# ===================================================================
# CLI entry point
# ===================================================================
def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="MANBEARPIG Self-Evolving Intelligence Engine v2.0"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Print last evolution log entries",
    )
    parser.add_argument(
        "--retrain", action="store_true",
        help="Force retrain classifiers",
    )
    parser.add_argument(
        "--db", default=_DEFAULT_DB,
        help="Path to litigation_context.db",
    )
    parser.add_argument(
        "--model-dir", default=str(_DEFAULT_MODEL_DIR),
        help="Path to model_data directory",
    )
    args = parser.parse_args()

    evolver = SelfEvolver(db_path=args.db, model_data_dir=args.model_dir)

    if args.report:
        log_entries = evolver.get_evolution_log()
        if log_entries:
            for entry in log_entries[:10]:
                _safe_log(json.dumps(entry, indent=2, default=str))
        else:
            _safe_log("No evolution log entries found.")
        return

    if args.retrain:
        result = evolver.retrain_classifier(force=True)
        _safe_log(json.dumps(result, indent=2, default=str))
        return

    # Default: full auto-improve cycle
    report = evolver.auto_improve_cycle()
    text = report.get("human_report", "No report generated")
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


if __name__ == "__main__":
    main()
