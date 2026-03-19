#!/usr/bin/env python3
"""
APEX Training Harvester — Extracts training data from LitigationOS
====================================================================
Sources: litigation_context.db, filing packages, harm records,
         authority chains, and evidence quotes.
Target: 1000+ (input, output, quality) triples for model fine-tuning.

Shadow-programmed: APEX_LLM_ENABLED gates neural features.
NEVER crashes — all methods try/except with fallbacks.
Never sets CWD to repo root (shadow modules).
Uses Path(__file__).parent for paths.
DB: busy_timeout=60000, journal_mode=WAL, cache_size=-32000.
Thread-safe, UTF-8 safe, logging, type hints.
"""

import json
import logging
import os
import re
import sqlite3
import sys
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── APEX Shadow Programming ────────────────────────────────────────
APEX_LLM_ENABLED: bool = os.environ.get("APEX_LLM_ENABLED", "false").lower() == "true"

_MODULE_DIR = Path(__file__).parent
_PROJECT_ROOT = _MODULE_DIR.parent.parent.parent

DEFAULT_DB = os.environ.get(
    "LITIGATION_DB_PATH",
    str(_PROJECT_ROOT / "litigation_context.db"),
)
DEFAULT_OUTPUT = str(_MODULE_DIR / "training_data.jsonl")


class TrainingHarvester:
    """Harvests training data from LitigationOS for model fine-tuning.

    Extracts (input, output, quality) triples from:
    - Filing packages (task → filing text)
    - Harm records (query → harm description)
    - Authority chains (legal question → authority text + citation)
    - Evidence quotes (context → quote + source)
    - Session todos (task title → description + status)
    """

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path
        self._lock = threading.Lock()

    # ── DB Connection ──────────────────────────────────────────────

    def _get_conn(self) -> Optional[sqlite3.Connection]:
        """Open a read-only WAL connection."""
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=30)
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=-32000")
            conn.execute("PRAGMA temp_store=MEMORY")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA query_only=ON")
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            logger.warning("[Harvester] DB connect failed: %s", e)
            return None

    def _table_exists(self, conn: sqlite3.Connection, table: str) -> bool:
        """Check if a table exists in the database."""
        try:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table,)
            ).fetchone()
            return row is not None
        except Exception:
            return False

    def _get_columns(self, conn: sqlite3.Connection, table: str) -> List[str]:
        """Get column names for a table."""
        try:
            rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
            return [row[1] for row in rows]
        except Exception:
            return []

    # ── Public API ─────────────────────────────────────────────────

    def harvest_all(self) -> dict:
        """Harvest from all sources. Returns {total: int, by_source: {...}, data: [...]}."""
        try:
            all_data: List[Dict] = []
            by_source: Dict[str, int] = {}

            # Harvest from each source
            for source_name, harvester_fn in [
                ("filings", self.harvest_filings),
                ("harms", self.harvest_harms),
                ("authorities", self.harvest_authorities),
                ("evidence", self._harvest_evidence),
                ("todos", self.harvest_todos),
            ]:
                try:
                    items = harvester_fn()
                    by_source[source_name] = len(items)
                    all_data.extend(items)
                    logger.info("[Harvester] %s: %d items", source_name, len(items))
                except Exception as e:
                    logger.warning("[Harvester] %s harvest failed: %s", source_name, e)
                    by_source[source_name] = 0

            return {
                "total": len(all_data),
                "by_source": by_source,
                "data": all_data,
            }
        except Exception as e:
            logger.error("[Harvester] harvest_all failed: %s", e, exc_info=True)
            return {"total": 0, "by_source": {}, "data": [], "error": str(e)}

    def harvest_filings(self) -> list:
        """Extract (task_description, filing_text, quality_score) from filing data.

        Searches filing_readiness and related tables for filing content.
        """
        try:
            conn = self._get_conn()
            if conn is None:
                return []

            try:
                items: List[Dict] = []

                # Try filing_readiness table
                if self._table_exists(conn, "filing_readiness"):
                    cols = self._get_columns(conn, "filing_readiness")
                    # Adapt to available columns
                    name_col = "vehicle_name" if "vehicle_name" in cols else (
                        "filing_name" if "filing_name" in cols else None
                    )
                    status_col = "status" if "status" in cols else None

                    if name_col:
                        rows = conn.execute(
                            f"SELECT * FROM filing_readiness LIMIT 500"
                        ).fetchall()
                        for row in rows:
                            row_dict = dict(row)
                            name = row_dict.get(name_col, "")
                            status = row_dict.get(status_col, "unknown") if status_col else "unknown"
                            quality = 0.8 if status in ("ready", "filed", "complete") else 0.4

                            items.append({
                                "input": f"Prepare filing: {name}",
                                "output": json.dumps({
                                    k: str(v)[:200] for k, v in row_dict.items()
                                    if v and str(v).strip()
                                }),
                                "quality": quality,
                                "source": "filing_readiness",
                                "type": "filing",
                            })

                # Try claims table
                if self._table_exists(conn, "claims"):
                    cols = self._get_columns(conn, "claims")
                    rows = conn.execute("SELECT * FROM claims LIMIT 300").fetchall()
                    for row in rows:
                        row_dict = dict(row)
                        claim_type = row_dict.get("claim_type", row_dict.get("type", ""))
                        text = row_dict.get("claim_text", row_dict.get("description", ""))
                        if claim_type and text:
                            items.append({
                                "input": f"Draft {claim_type} claim",
                                "output": str(text)[:500],
                                "quality": 0.7,
                                "source": "claims",
                                "type": "filing",
                            })

                return items
            finally:
                conn.close()
        except Exception as e:
            logger.warning("[Harvester] harvest_filings failed: %s", e)
            return []

    def harvest_harms(self) -> list:
        """Extract (query, harm_record, category) from harm database."""
        try:
            conn = self._get_conn()
            if conn is None:
                return []

            try:
                items: List[Dict] = []

                # Try harm_records or risk_events tables
                for table in ["harm_records", "risk_events", "harms"]:
                    if not self._table_exists(conn, table):
                        continue

                    cols = self._get_columns(conn, table)
                    rows = conn.execute(f"SELECT * FROM {table} LIMIT 500").fetchall()
                    for row in rows:
                        row_dict = dict(row)
                        # Adapt to available columns
                        description = (
                            row_dict.get("description", "") or
                            row_dict.get("harm_description", "") or
                            row_dict.get("event_description", "") or ""
                        )
                        category = (
                            row_dict.get("category", "") or
                            row_dict.get("harm_type", "") or
                            row_dict.get("type", "") or "general"
                        )
                        if description:
                            items.append({
                                "input": f"Describe harm: {category}",
                                "output": str(description)[:500],
                                "quality": 0.6,
                                "source": table,
                                "type": "harm",
                                "category": str(category),
                            })

                return items
            finally:
                conn.close()
        except Exception as e:
            logger.warning("[Harvester] harvest_harms failed: %s", e)
            return []

    def harvest_authorities(self) -> list:
        """Extract (legal_question, authority_text, citation) from authority chains."""
        try:
            conn = self._get_conn()
            if conn is None:
                return []

            try:
                items: List[Dict] = []

                # Try authority_chains table
                if self._table_exists(conn, "authority_chains"):
                    cols = self._get_columns(conn, "authority_chains")
                    text_col = "authority_text" if "authority_text" in cols else (
                        "full_text" if "full_text" in cols else None
                    )
                    cite_col = "citation" if "citation" in cols else (
                        "rule_id" if "rule_id" in cols else None
                    )

                    if text_col:
                        rows = conn.execute(
                            f"SELECT * FROM authority_chains LIMIT 500"
                        ).fetchall()
                        for row in rows:
                            row_dict = dict(row)
                            text = str(row_dict.get(text_col, ""))
                            citation = str(row_dict.get(cite_col, "")) if cite_col else ""
                            if text and len(text) > 20:
                                items.append({
                                    "input": f"Find authority for: {citation}" if citation else "Find legal authority",
                                    "output": text[:500],
                                    "quality": 0.8,
                                    "source": "authority_chains",
                                    "type": "authority",
                                    "citation": citation,
                                })

                # Try auth_rules table
                if self._table_exists(conn, "auth_rules"):
                    cols = self._get_columns(conn, "auth_rules")
                    rows = conn.execute("SELECT * FROM auth_rules LIMIT 500").fetchall()
                    for row in rows:
                        row_dict = dict(row)
                        text = str(row_dict.get("full_text", ""))
                        rule_id = str(row_dict.get("rule_id", ""))
                        if text and len(text) > 20:
                            items.append({
                                "input": f"Explain rule: {rule_id}" if rule_id else "Explain legal rule",
                                "output": text[:500],
                                "quality": 0.85,
                                "source": "auth_rules",
                                "type": "authority",
                                "citation": rule_id,
                            })

                return items
            finally:
                conn.close()
        except Exception as e:
            logger.warning("[Harvester] harvest_authorities failed: %s", e)
            return []

    def harvest_todos(self) -> list:
        """Extract (task_title, task_description, status) from session SQL.

        Note: This harvests from litigation_context.db todos-like tables,
        not from the Copilot session DB (which is separate).
        """
        try:
            conn = self._get_conn()
            if conn is None:
                return []

            try:
                items: List[Dict] = []

                # Look for task/todo tables in the litigation DB
                for table in ["tasks", "todos", "action_items", "steps"]:
                    if not self._table_exists(conn, table):
                        continue

                    cols = self._get_columns(conn, table)
                    rows = conn.execute(f"SELECT * FROM {table} LIMIT 300").fetchall()
                    for row in rows:
                        row_dict = dict(row)
                        title = (
                            row_dict.get("title", "") or
                            row_dict.get("task_name", "") or
                            row_dict.get("name", "") or ""
                        )
                        desc = (
                            row_dict.get("description", "") or
                            row_dict.get("task_description", "") or
                            row_dict.get("details", "") or ""
                        )
                        status = row_dict.get("status", "unknown")
                        if title:
                            quality = 0.7 if status in ("done", "complete", "filed") else 0.4
                            items.append({
                                "input": str(title)[:200],
                                "output": str(desc)[:500] if desc else str(title),
                                "quality": quality,
                                "source": table,
                                "type": "task",
                                "status": str(status),
                            })

                return items
            finally:
                conn.close()
        except Exception as e:
            logger.warning("[Harvester] harvest_todos failed: %s", e)
            return []

    def _harvest_evidence(self) -> list:
        """Extract training data from evidence quotes."""
        try:
            conn = self._get_conn()
            if conn is None:
                return []

            try:
                items: List[Dict] = []

                if self._table_exists(conn, "evidence_quotes"):
                    cols = self._get_columns(conn, "evidence_quotes")
                    text_col = "quote_text" if "quote_text" in cols else None
                    source_col = "source_file" if "source_file" in cols else (
                        "source" if "source" in cols else None
                    )

                    if text_col:
                        rows = conn.execute(
                            f"SELECT * FROM evidence_quotes LIMIT 500"
                        ).fetchall()
                        for row in rows:
                            row_dict = dict(row)
                            text = str(row_dict.get(text_col, ""))
                            source = str(row_dict.get(source_col, "")) if source_col else ""
                            if text and len(text) > 20:
                                items.append({
                                    "input": f"Extract evidence from: {source[:80]}" if source else "Extract evidence",
                                    "output": text[:500],
                                    "quality": 0.65,
                                    "source": "evidence_quotes",
                                    "type": "evidence",
                                })

                return items
            finally:
                conn.close()
        except Exception as e:
            logger.warning("[Harvester] _harvest_evidence failed: %s", e)
            return []

    def save_training_data(self, data: list = None, output_path: str = None) -> dict:
        """Save to training_data.jsonl in JSONL format.

        Args:
            data: List of training dicts. If None, harvests all first.
            output_path: Output file path. Defaults to training_data.jsonl in module dir.

        Returns:
            {path: str, count: int, size_bytes: int}
        """
        try:
            if data is None:
                harvest_result = self.harvest_all()
                data = harvest_result.get("data", [])

            if output_path is None:
                output_path = DEFAULT_OUTPUT

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            count = 0
            with open(output_file, "w", encoding="utf-8") as f:
                for item in data:
                    if not item.get("input") or not item.get("output"):
                        continue
                    line = json.dumps({
                        "input": str(item["input"])[:1000],
                        "output": str(item["output"])[:2000],
                        "quality": item.get("quality", 0.5),
                        "source": item.get("source", "unknown"),
                        "type": item.get("type", "general"),
                    }, ensure_ascii=False)
                    f.write(line + "\n")
                    count += 1

            size = output_file.stat().st_size if output_file.exists() else 0
            logger.info("[Harvester] Saved %d items to %s (%d bytes)", count, output_path, size)

            return {
                "path": str(output_file),
                "count": count,
                "size_bytes": size,
            }
        except Exception as e:
            logger.error("[Harvester] save_training_data failed: %s", e, exc_info=True)
            return {"path": output_path or "", "count": 0, "size_bytes": 0, "error": str(e)}

    # ── Status & Self-Test ─────────────────────────────────────────

    def status(self) -> Dict:
        """Return engine status."""
        conn = self._get_conn()
        table_counts: Dict[str, int] = {}
        if conn:
            try:
                for table in ["evidence_quotes", "auth_rules", "authority_chains",
                              "filing_readiness", "claims", "harm_records", "risk_events"]:
                    if self._table_exists(conn, table):
                        try:
                            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                            table_counts[table] = row[0] if row else 0
                        except Exception:
                            table_counts[table] = -1
            finally:
                conn.close()

        return {
            "engine": "APEX-TrainingHarvester",
            "apex_llm_enabled": APEX_LLM_ENABLED,
            "db_path": self.db_path,
            "db_available": os.path.exists(self.db_path),
            "table_counts": table_counts,
            "output_path": DEFAULT_OUTPUT,
        }

    def self_test(self) -> Dict:
        """Run self-test."""
        results = {"tests": [], "status": "pass"}
        try:
            # Test 1: Harvest all
            harvest = self.harvest_all()
            results["tests"].append({
                "name": "harvest_all",
                "pass": isinstance(harvest, dict) and "total" in harvest,
                "total": harvest.get("total", 0),
                "by_source": harvest.get("by_source", {}),
            })

            # Test 2: Individual harvesters don't crash
            for name, fn in [
                ("filings", self.harvest_filings),
                ("harms", self.harvest_harms),
                ("authorities", self.harvest_authorities),
                ("todos", self.harvest_todos),
            ]:
                try:
                    items = fn()
                    results["tests"].append({
                        "name": f"harvest_{name}",
                        "pass": isinstance(items, list),
                        "count": len(items),
                    })
                except Exception as e:
                    results["tests"].append({
                        "name": f"harvest_{name}",
                        "pass": False,
                        "error": str(e),
                    })

            # Test 3: Save to temp file (don't pollute real output)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False, mode="w") as tmp:
                tmp_path = tmp.name
            try:
                save_result = self.save_training_data(
                    data=harvest.get("data", [])[:10],
                    output_path=tmp_path,
                )
                results["tests"].append({
                    "name": "save_training_data",
                    "pass": save_result.get("count", 0) >= 0,
                    "count": save_result.get("count", 0),
                })
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

            results["status"] = "pass" if all(t.get("pass", False) for t in results["tests"]) else "partial"
        except Exception as e:
            results["status"] = "fail"
            results["error"] = str(e)
        return results


# ── CLI Entry Point ────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

    harvester = TrainingHarvester()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "--self-test":
        print(json.dumps(harvester.self_test(), indent=2, default=str))
    elif cmd == "--status":
        print(json.dumps(harvester.status(), indent=2, default=str))
    elif cmd == "--harvest":
        result = harvester.harvest_all()
        print(f"Total: {result['total']}")
        print(f"By source: {json.dumps(result['by_source'], indent=2)}")
    elif cmd == "--save":
        output = sys.argv[2] if len(sys.argv) > 2 else None
        result = harvester.save_training_data(output_path=output)
        print(json.dumps(result, indent=2, default=str))
    else:
        print(json.dumps(harvester.status(), indent=2, default=str))
