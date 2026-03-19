"""
APEX Fine-Tuning Pipeline — Fine-tune legal-BERT on case-specific data.

Shadow-programmed: only runs when APEX_LLM_ENABLED=true AND training data available.
When disabled: reports readiness status without running training.
"""
from __future__ import annotations

import json
import logging
import math
import os
import random
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("apex.fine_tune_pipeline")

APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
_DB_DIR = _MODULE_DIR / "model_data"
_MODELS_DIR = _MODULE_DIR / "models"
_PROJECT_ROOT = _MODULE_DIR.parent.parent

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

_PRAGMA_INIT = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA temp_store=MEMORY",
)


def _open_db(path: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), check_same_thread=False)
    for p in _PRAGMA_INIT:
        conn.execute(p)
    return conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ft_runs (
            run_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at  TEXT NOT NULL,
            finished_at TEXT,
            epochs      INTEGER,
            batch_size  INTEGER,
            train_size  INTEGER,
            val_size    INTEGER,
            test_size   INTEGER,
            final_loss  REAL,
            final_acc   REAL,
            model_path  TEXT,
            status      TEXT DEFAULT 'running'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ft_data (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            split       TEXT NOT NULL,
            input_text  TEXT NOT NULL,
            label       TEXT NOT NULL,
            source      TEXT,
            quality     REAL DEFAULT 1.0,
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ft_metrics (
            run_id      INTEGER,
            epoch       INTEGER,
            train_loss  REAL,
            val_loss    REAL,
            val_acc     REAL,
            timestamp   TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (run_id, epoch)
        )
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# Safe imports for ML libraries (may not be installed)
# ---------------------------------------------------------------------------

_HAS_TORCH = False
_HAS_TRANSFORMERS = False
_HAS_SKLEARN = False

try:
    import torch  # type: ignore[import-untyped]
    _HAS_TORCH = True
except ImportError:
    pass

try:
    import transformers  # type: ignore[import-untyped]
    _HAS_TRANSFORMERS = True
except ImportError:
    pass

try:
    from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]
    from sklearn.metrics import accuracy_score, f1_score, classification_report  # type: ignore[import-untyped]
    _HAS_SKLEARN = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Training data loader
# ---------------------------------------------------------------------------

def _load_harvester_data(source_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load training data from training_harvester output."""
    data: List[Dict[str, Any]] = []

    # Try training_harvester module
    try:
        from .training_harvester import TrainingHarvester  # type: ignore[import-untyped]
        harvester = TrainingHarvester()
        if hasattr(harvester, "harvest"):
            raw = harvester.harvest()
            if isinstance(raw, list):
                data.extend(raw)
    except Exception as exc:
        logger.debug("TrainingHarvester import/run failed: %s", exc)

    # Try JSON file
    if source_path:
        try:
            path = Path(source_path)
            if path.exists():
                content = path.read_text(encoding="utf-8", errors="replace")
                loaded = json.loads(content)
                if isinstance(loaded, list):
                    data.extend(loaded)
        except Exception as exc:
            logger.debug("JSON training data load failed: %s", exc)

    # Try default locations
    for candidate in [
        _DB_DIR / "training_data.json",
        _MODULE_DIR / "training_data.json",
        _PROJECT_ROOT / "data" / "training_data.json",
    ]:
        if candidate.exists() and not data:
            try:
                content = candidate.read_text(encoding="utf-8", errors="replace")
                loaded = json.loads(content)
                if isinstance(loaded, list):
                    data.extend(loaded)
            except Exception:
                pass

    return data


def _split_data(data: List[Dict[str, Any]],
                train_ratio: float = 0.8,
                val_ratio: float = 0.1) -> Tuple[list, list, list]:
    """Split data into train / val / test sets."""
    if not data:
        return [], [], []
    random.shuffle(data)
    n = len(data)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    return data[:train_end], data[train_end:val_end], data[val_end:]


# ---------------------------------------------------------------------------
# Lightweight NB-based fine-tuning (always available)
# ---------------------------------------------------------------------------

def _nb_fine_tune(train: list, val: list) -> Dict[str, Any]:
    """Fine-tune using scikit-learn Naive Bayes as a lightweight fallback."""
    if not _HAS_SKLEARN or not train:
        return {"status": "sklearn_unavailable", "accuracy": 0.0}

    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore[import-untyped]
    from sklearn.naive_bayes import MultinomialNB  # type: ignore[import-untyped]
    from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]

    try:
        X_train = [d.get("input", "") for d in train]
        y_train = [d.get("output", d.get("label", "unknown")) for d in train]
        X_val = [d.get("input", "") for d in val]
        y_val = [d.get("output", d.get("label", "unknown")) for d in val]

        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(max_features=10000, ngram_range=(1, 2))),
            ("nb", MultinomialNB(alpha=0.1)),
        ])
        pipe.fit(X_train, y_train)

        if X_val:
            preds = pipe.predict(X_val)
            acc = accuracy_score(y_val, preds)
            f1 = f1_score(y_val, preds, average="weighted", zero_division=0)
        else:
            acc = 0.0
            f1 = 0.0

        # Save model
        import pickle
        model_path = _MODELS_DIR / "fine_tuned_nb.pkl"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, "wb") as f:
            pickle.dump(pipe, f)

        return {
            "status": "complete",
            "accuracy": round(acc, 4),
            "f1": round(f1, 4),
            "model_path": str(model_path),
            "method": "naive_bayes",
            "train_size": len(train),
            "val_size": len(val),
        }
    except Exception as exc:
        logger.error("NB fine-tune failed: %s", exc)
        return {"status": "error", "error": str(exc), "method": "naive_bayes"}


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class FineTunePipeline:
    """Fine-tuning pipeline for legal-BERT on case-specific data."""

    def __init__(self, db_path: Optional[str | Path] = None) -> None:
        self._lock = threading.Lock()
        self._db_path = Path(db_path) if db_path else _DB_DIR / "fine_tune.db"
        self._init_db()

    def _init_db(self) -> None:
        try:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = _open_db(self._db_path)
            _ensure_tables(conn)
            conn.close()
        except Exception as exc:
            logger.warning("Fine-tune DB init failed: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def prepare_data(self, source_path: Optional[str] = None) -> dict:
        """Prepare training data from training_harvester output.

        Returns ``{train: int, val: int, test: int, total: int}``.
        """
        try:
            raw = _load_harvester_data(source_path)
            if not raw:
                return {"train": 0, "val": 0, "test": 0, "total": 0,
                        "status": "no_data_found"}

            train, val, test = _split_data(raw)

            # Persist to DB
            conn = _open_db(self._db_path)
            _ensure_tables(conn)
            # Clear old data
            conn.execute("DELETE FROM ft_data")
            rows: List[Tuple[str, str, str, str, float]] = []
            for split_name, split_data in [("train", train), ("val", val), ("test", test)]:
                for d in split_data:
                    rows.append((
                        split_name,
                        str(d.get("input", ""))[:5000],
                        str(d.get("output", d.get("label", "unknown")))[:1000],
                        str(d.get("source", ""))[:200],
                        float(d.get("quality", 1.0)),
                    ))
            conn.executemany(
                "INSERT INTO ft_data (split, input_text, label, source, quality) VALUES (?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
            conn.close()

            return {
                "train": len(train),
                "val": len(val),
                "test": len(test),
                "total": len(raw),
                "status": "prepared",
            }
        except Exception as exc:
            logger.error("Data preparation failed: %s", exc)
            return {"train": 0, "val": 0, "test": 0, "total": 0,
                    "status": "error", "error": str(exc)}

    def train(self, epochs: int = 3, batch_size: int = 8) -> dict:
        """Fine-tune model on prepared data.

        Returns ``{loss: float, accuracy: float, saved_to: str, method: str}``.
        """
        if not APEX_LLM_ENABLED:
            return self._train_lightweight(epochs, batch_size)

        # Full training path (requires torch + transformers)
        if _HAS_TORCH and _HAS_TRANSFORMERS:
            return self._train_transformer(epochs, batch_size)

        # Fallback to lightweight
        return self._train_lightweight(epochs, batch_size)

    def _train_lightweight(self, epochs: int, batch_size: int) -> dict:
        """Lightweight NB-based training (always available)."""
        run_id = self._start_run(epochs, batch_size)
        try:
            conn = _open_db(self._db_path)
            train_rows = conn.execute(
                "SELECT input_text, label FROM ft_data WHERE split = 'train'"
            ).fetchall()
            val_rows = conn.execute(
                "SELECT input_text, label FROM ft_data WHERE split = 'val'"
            ).fetchall()
            conn.close()

            train = [{"input": r[0], "output": r[1]} for r in train_rows]
            val = [{"input": r[0], "output": r[1]} for r in val_rows]

            if not train:
                self._finish_run(run_id, 0.0, 0.0, "", "no_data")
                return {"loss": 0.0, "accuracy": 0.0, "saved_to": "",
                        "method": "no_data", "run_id": run_id}

            result = _nb_fine_tune(train, val)
            acc = result.get("accuracy", 0.0)
            model_path = result.get("model_path", "")
            self._finish_run(run_id, 0.0, acc, model_path, "complete")

            return {
                "loss": 0.0,
                "accuracy": acc,
                "f1": result.get("f1", 0.0),
                "saved_to": model_path,
                "method": "naive_bayes",
                "run_id": run_id,
                "train_size": len(train),
                "val_size": len(val),
            }
        except Exception as exc:
            logger.error("Lightweight training failed: %s", exc)
            self._finish_run(run_id, 0.0, 0.0, "", "error")
            return {"loss": 0.0, "accuracy": 0.0, "saved_to": "",
                    "method": "error", "error": str(exc), "run_id": run_id}

    def _train_transformer(self, epochs: int, batch_size: int) -> dict:
        """Full transformer-based training (requires torch + transformers)."""
        run_id = self._start_run(epochs, batch_size)
        try:
            conn = _open_db(self._db_path)
            train_rows = conn.execute(
                "SELECT input_text, label FROM ft_data WHERE split = 'train'"
            ).fetchall()
            val_rows = conn.execute(
                "SELECT input_text, label FROM ft_data WHERE split = 'val'"
            ).fetchall()
            conn.close()

            if not train_rows:
                self._finish_run(run_id, 0.0, 0.0, "", "no_data")
                return {"loss": 0.0, "accuracy": 0.0, "saved_to": "",
                        "method": "no_data", "run_id": run_id}

            # Build label map
            all_labels = sorted(set(r[1] for r in train_rows + val_rows))
            label2id = {l: i for i, l in enumerate(all_labels)}
            num_labels = len(all_labels)

            # Check for pre-downloaded model or use base
            model_name = "nlpaueb/legal-bert-base-uncased"
            local_model = _MODELS_DIR / "legal-bert-base"
            if local_model.exists():
                model_name = str(local_model)

            import torch  # type: ignore[import-untyped]
            from transformers import (  # type: ignore[import-untyped]
                AutoTokenizer, AutoModelForSequenceClassification,
                TrainingArguments, Trainer
            )
            from torch.utils.data import Dataset  # type: ignore[import-untyped]

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(
                model_name, num_labels=num_labels
            )

            class LegalDataset(Dataset):  # type: ignore[type-arg]
                def __init__(self, rows: list, tok: Any, l2id: dict) -> None:
                    self.rows = rows
                    self.tok = tok
                    self.l2id = l2id
                def __len__(self) -> int:
                    return len(self.rows)
                def __getitem__(self, idx: int) -> dict:
                    text, label = self.rows[idx]
                    enc = self.tok(text, truncation=True, padding="max_length",
                                   max_length=256, return_tensors="pt")
                    item = {k: v.squeeze(0) for k, v in enc.items()}
                    item["labels"] = torch.tensor(self.l2id.get(label, 0))
                    return item

            train_ds = LegalDataset(train_rows, tokenizer, label2id)
            val_ds = LegalDataset(val_rows, tokenizer, label2id)

            output_dir = str(_MODELS_DIR / f"fine_tuned_run_{run_id}")
            training_args = TrainingArguments(
                output_dir=output_dir,
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                per_device_eval_batch_size=batch_size,
                evaluation_strategy="epoch",
                save_strategy="epoch",
                logging_steps=50,
                load_best_model_at_end=True,
                metric_for_best_model="accuracy",
                report_to="none",
            )

            def compute_metrics(eval_pred: Any) -> dict:
                preds = eval_pred.predictions.argmax(-1)
                labels = eval_pred.label_ids
                acc = (preds == labels).mean()
                return {"accuracy": float(acc)}

            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=train_ds,
                eval_dataset=val_ds,
                compute_metrics=compute_metrics,
            )
            trainer.train()

            eval_result = trainer.evaluate()
            acc = eval_result.get("eval_accuracy", 0.0)
            loss = eval_result.get("eval_loss", 0.0)

            # Save
            trainer.save_model(output_dir)
            tokenizer.save_pretrained(output_dir)

            # Save label map
            label_map_path = Path(output_dir) / "label_map.json"
            label_map_path.write_text(json.dumps(label2id, indent=2))

            self._finish_run(run_id, loss, acc, output_dir, "complete")

            return {
                "loss": round(loss, 4),
                "accuracy": round(acc, 4),
                "saved_to": output_dir,
                "method": "transformer",
                "run_id": run_id,
                "num_labels": num_labels,
                "train_size": len(train_rows),
                "val_size": len(val_rows),
            }

        except Exception as exc:
            logger.error("Transformer training failed: %s", exc)
            self._finish_run(run_id, 0.0, 0.0, "", "error")
            # Fallback to lightweight
            logger.info("Falling back to NB fine-tuning")
            return self._train_lightweight(epochs, batch_size)

    def evaluate(self, test_data: Optional[list] = None) -> dict:
        """Evaluate fine-tuned model.

        Returns ``{accuracy, f1, per_class, total_tested}``.
        """
        try:
            if test_data is None:
                conn = _open_db(self._db_path)
                rows = conn.execute(
                    "SELECT input_text, label FROM ft_data WHERE split = 'test'"
                ).fetchall()
                conn.close()
                test_data = [{"input": r[0], "label": r[1]} for r in rows]

            if not test_data:
                return {"accuracy": 0.0, "f1": 0.0, "per_class": {},
                        "total_tested": 0, "status": "no_test_data"}

            # Try loading fine-tuned NB model
            nb_path = _MODELS_DIR / "fine_tuned_nb.pkl"
            if nb_path.exists() and _HAS_SKLEARN:
                import pickle
                with open(nb_path, "rb") as f:
                    pipe = pickle.load(f)
                X_test = [d.get("input", "") for d in test_data]
                y_test = [d.get("label", d.get("output", "unknown")) for d in test_data]
                preds = pipe.predict(X_test)
                acc = accuracy_score(y_test, preds)
                f1 = f1_score(y_test, preds, average="weighted", zero_division=0)

                per_class: Dict[str, Any] = {}
                try:
                    report = classification_report(y_test, preds, output_dict=True, zero_division=0)
                    per_class = {k: v for k, v in report.items()
                                 if isinstance(v, dict)}
                except Exception:
                    pass

                return {
                    "accuracy": round(acc, 4),
                    "f1": round(f1, 4),
                    "per_class": per_class,
                    "total_tested": len(test_data),
                    "method": "naive_bayes",
                }

            return {"accuracy": 0.0, "f1": 0.0, "per_class": {},
                    "total_tested": len(test_data), "status": "no_model_available"}

        except Exception as exc:
            logger.error("Evaluation failed: %s", exc)
            return {"accuracy": 0.0, "f1": 0.0, "per_class": {},
                    "total_tested": 0, "status": "error", "error": str(exc)}

    def deploy(self) -> bool:
        """Deploy fine-tuned model as default for neural_intent + reranker.

        Returns True if deployment succeeded.
        """
        try:
            # Check for any fine-tuned model
            nb_path = _MODELS_DIR / "fine_tuned_nb.pkl"
            if nb_path.exists():
                deploy_marker = _MODELS_DIR / "deployed_model.json"
                deploy_info = {
                    "model_path": str(nb_path),
                    "method": "naive_bayes",
                    "deployed_at": datetime.now(timezone.utc).isoformat(),
                }
                deploy_marker.write_text(json.dumps(deploy_info, indent=2))
                logger.info("Deployed NB model: %s", nb_path)
                return True

            # Check for transformer models
            for p in sorted(_MODELS_DIR.glob("fine_tuned_run_*"), reverse=True):
                if (p / "config.json").exists():
                    deploy_marker = _MODELS_DIR / "deployed_model.json"
                    deploy_info = {
                        "model_path": str(p),
                        "method": "transformer",
                        "deployed_at": datetime.now(timezone.utc).isoformat(),
                    }
                    deploy_marker.write_text(json.dumps(deploy_info, indent=2))
                    logger.info("Deployed transformer model: %s", p)
                    return True

            logger.warning("No fine-tuned model found to deploy")
            return False
        except Exception as exc:
            logger.error("Deployment failed: %s", exc)
            return False

    def status(self) -> dict:
        """Check fine-tuning readiness.

        Returns ``{data_available, model_available, gpu_available,
                   torch_available, transformers_available, sklearn_available,
                   apex_enabled, last_run}``.
        """
        info: Dict[str, Any] = {
            "apex_enabled": APEX_LLM_ENABLED,
            "torch_available": _HAS_TORCH,
            "transformers_available": _HAS_TRANSFORMERS,
            "sklearn_available": _HAS_SKLEARN,
            "gpu_available": False,
            "data_available": False,
            "model_available": False,
            "last_run": None,
        }

        # GPU check
        if _HAS_TORCH:
            try:
                import torch  # type: ignore[import-untyped]
                info["gpu_available"] = torch.cuda.is_available()
                if info["gpu_available"]:
                    info["gpu_name"] = torch.cuda.get_device_name(0)
            except Exception:
                pass

        # Data check
        try:
            conn = _open_db(self._db_path)
            row = conn.execute("SELECT COUNT(*) FROM ft_data WHERE split = 'train'").fetchone()
            info["data_available"] = (row[0] > 0) if row else False
            info["train_samples"] = row[0] if row else 0
            conn.close()
        except Exception:
            pass

        # Model check
        nb_path = _MODELS_DIR / "fine_tuned_nb.pkl"
        info["model_available"] = nb_path.exists()
        if not info["model_available"]:
            info["model_available"] = any(
                (p / "config.json").exists()
                for p in _MODELS_DIR.glob("fine_tuned_run_*")
            ) if _MODELS_DIR.exists() else False

        # Last run
        try:
            conn = _open_db(self._db_path)
            row = conn.execute("""
                SELECT run_id, finished_at, final_acc, status
                FROM ft_runs ORDER BY run_id DESC LIMIT 1
            """).fetchone()
            if row:
                info["last_run"] = {
                    "run_id": row[0], "finished_at": row[1],
                    "accuracy": row[2], "status": row[3],
                }
            conn.close()
        except Exception:
            pass

        return info

    # ------------------------------------------------------------------
    # Run tracking
    # ------------------------------------------------------------------

    def _start_run(self, epochs: int, batch_size: int) -> Optional[int]:
        with self._lock:
            try:
                conn = _open_db(self._db_path)
                cur = conn.execute("""
                    INSERT INTO ft_runs (started_at, epochs, batch_size)
                    VALUES (?, ?, ?)
                """, (datetime.now(timezone.utc).isoformat(), epochs, batch_size))
                run_id = cur.lastrowid
                conn.commit()
                conn.close()
                return run_id
            except Exception:
                return None

    def _finish_run(self, run_id: Optional[int], loss: float, acc: float,
                    model_path: str, status: str) -> None:
        if run_id is None:
            return
        try:
            conn = _open_db(self._db_path)
            conn.execute("""
                UPDATE ft_runs
                SET finished_at = ?, final_loss = ?, final_acc = ?,
                    model_path = ?, status = ?
                WHERE run_id = ?
            """, (
                datetime.now(timezone.utc).isoformat(),
                loss, acc, model_path, status, run_id,
            ))
            conn.commit()
            conn.close()
        except Exception:
            pass
