"""
Task Handlers — Routes daemon task_queue items to actual processing engines.
============================================================================

This is the bridge between the daemon's task_queue and the intake engine.
Previously this was a TODO stub in core.py line 199.

Each task_type maps to a handler function that does the real work.
Handlers are case-agnostic — they use the file content + case_config.

Task Types:
  auto_classify  → Run full intake pipeline (extract + classify + analyze + route)
  ocr_extract    → Extract text with OCR (handled by intake extractor)
  brain_feed     → Feed analyzed content to brain databases
  add_evidence   → Manually add an evidence file
  check_status   → Return pipeline status for a file
"""

import json
import logging
import os
import re
import sqlite3
from pathlib import Path
from typing import Optional

logger = logging.getLogger("daemon.task_handlers")

# Whitelist of tables that brain_feed / brain_query / brain_search may touch.
# Any table name used in SQL interpolation MUST appear here first.
ALLOWED_BRAIN_TABLES = frozenset({
    # ── Main DB source tables (read by brain_feed routing) ──
    "authority_chains_v2",
    "timeline_events",
    "entities",
    "evidence_quotes",
    "impeachment_matrix",
    "contradiction_map",
    "judicial_violations",
    "police_reports",
    "master_citations",
    # ── authority_brain ──
    "court_rules", "court_rules_fts",
    "statutes", "statutes_fts",
    "case_law", "case_law_fts",
    "evidence_rules", "evidence_rules_fts",
    "benchbook", "benchbook_fts",
    # ── narrative_brain ──
    "timeline", "timeline_fts",
    "extractions", "extractions_fts",
    "orders", "orders_fts",
    "police", "police_fts",
    "testimony", "testimony_fts",
    "communications", "communications_fts",
    # ── entity_brain ──
    "people", "organizations", "courts",
    # ── claims_brain ──
    "claims", "claim_evidence",
    # ── interpretation_brain ──
    "arguments", "arguments_fts",
    "impeachment", "impeachment_fts",
    "drafts", "drafts_fts",
    "applications", "applications_fts",
    # ── cross_brain_index ──
    "cross_references", "universal_search",
    "extraction_queue", "brain_stats", "provenance",
})

# Routing map: main-DB table → list of brain names that should receive copies.
# BrainManager resolves each name to its .db file automatically.
BRAIN_FEED_ROUTES: dict[str, list[str]] = {
    "authority_chains_v2": ["authority_brain"],
    "timeline_events":     ["narrative_brain"],
    "entities":            ["entity_brain"],
    "evidence_quotes":     ["authority_brain", "narrative_brain"],
    "impeachment_matrix":  ["interpretation_brain"],
    "contradiction_map":   ["interpretation_brain", "claims_brain"],
    "judicial_violations": ["authority_brain"],
    "police_reports":      ["narrative_brain"],
}


def get_handler(task_type: str):
    """Return the handler function for a task type."""
    return HANDLER_MAP.get(task_type)


def handle_auto_classify(payload: dict) -> dict:
    """Full intake pipeline: extract → classify → analyze → route to DB."""
    file_path = payload.get("file_path", "")
    if not file_path or not Path(file_path).exists():
        return {"status": "error", "error": f"File not found: {file_path}"}

    try:
        # Lazy import to avoid circular dependencies
        from engines.intake import IntakePipeline, CaseConfig

        # Determine DB path — use payload or default
        db_path = payload.get("db_path") or _default_db_path()

        # Try to load case config from the file's directory
        file_dir = Path(file_path).parent
        case_config = CaseConfig.auto_detect(str(file_dir))

        pipeline = IntakePipeline(
            db_path=db_path,
            case_config=case_config,
            ocr_enabled=True,
        )

        result = pipeline.process_file(file_path)
        pipeline.close()

        return {
            "status": result.status,
            "file_name": result.file_name,
            "doc_type": result.doc_type,
            "lanes": result.lanes,
            "urgency": result.urgency,
            "quotes_inserted": result.quotes_inserted,
            "events_inserted": result.events_inserted,
            "authorities_inserted": result.authorities_inserted,
            "impeachment_inserted": result.impeachment_inserted,
            "entities_inserted": result.entities_inserted,
            "duration_sec": result.duration_sec,
            "error": result.error,
        }

    except Exception as e:
        logger.error(f"auto_classify failed for {file_path}: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def handle_ocr_extract(payload: dict) -> dict:
    """OCR-specific extraction (for image files and image-PDFs)."""
    file_path = payload.get("file_path", "")
    if not file_path or not Path(file_path).exists():
        return {"status": "error", "error": f"File not found: {file_path}"}

    try:
        from engines.intake import TextExtractor
        extractor = TextExtractor(ocr_enabled=True)
        result = extractor.extract(file_path)

        return {
            "status": "completed" if not result.error else "error",
            "file_name": result.file_name,
            "page_count": result.page_count,
            "char_count": result.char_count,
            "extraction_method": result.extraction_method,
            "error": result.error,
        }

    except Exception as e:
        logger.error(f"ocr_extract failed for {file_path}: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def handle_brain_feed(payload: dict) -> dict:
    """Feed analyzed content to ALL brain databases via BrainManager.

    Routes extracted content to the appropriate brain DBs using
    BRAIN_FEED_ROUTES and the BrainManager unified interface.
    Falls back gracefully if individual brains don't exist yet.
    """
    file_path = payload.get("file_path", "")
    if not file_path or not Path(file_path).exists():
        return {"status": "error", "error": f"File not found: {file_path}"}

    try:
        from engines.intake import IntakePipeline, CaseConfig
    except ImportError as e:
        logger.error(f"Cannot import IntakePipeline: {e}", exc_info=True)
        return {"status": "error", "error": f"Missing engine: {e}"}

    try:
        from brains.brain_manager import BrainManager
    except ImportError as e:
        logger.error(f"Cannot import BrainManager: {e}", exc_info=True)
        return {"status": "error", "error": f"Missing BrainManager: {e}"}

    try:
        db_path = payload.get("db_path") or _default_db_path()
        file_dir = Path(file_path).parent
        case_config = CaseConfig.auto_detect(str(file_dir))

        pipeline = IntakePipeline(
            db_path=db_path,
            case_config=case_config,
            ocr_enabled=True,
        )
        result = pipeline.process_file(file_path)
        pipeline.close()

        fed_brains: list[str] = []
        bm = BrainManager()

        # Read rows from main DB once per source table, then fan-out to brains
        with sqlite3.connect(db_path, timeout=30) as main_conn:
            main_conn.execute("PRAGMA journal_mode=WAL")
            main_conn.execute("PRAGMA busy_timeout=30000")
            main_conn.execute("PRAGMA cache_size=-32000")
            main_conn.row_factory = sqlite3.Row

            main_tables = {r[0] for r in main_conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}

            for source_table, target_brains in BRAIN_FEED_ROUTES.items():
                # Validate table against whitelist before any SQL interpolation
                if source_table not in ALLOWED_BRAIN_TABLES:
                    logger.warning(
                        "Blocked brain_feed to disallowed table: %s", source_table
                    )
                    continue
                if source_table not in main_tables:
                    continue

                rows = main_conn.execute(
                    f"SELECT * FROM [{source_table}] ORDER BY rowid DESC LIMIT 500"
                ).fetchall()
                if not rows:
                    continue

                cols = rows[0].keys()
                placeholders = ", ".join(["?"] * len(cols))
                col_names = ", ".join(f"[{c}]" for c in cols)

                for brain_name in target_brains:
                    try:
                        with bm.open_brain(brain_name) as brain_conn:
                            brain_tables = {r[0] for r in brain_conn.execute(
                                "SELECT name FROM sqlite_master WHERE type='table'"
                            ).fetchall()}
                            if source_table not in brain_tables:
                                continue

                            for row in rows:
                                try:
                                    brain_conn.execute(
                                        f"INSERT OR IGNORE INTO [{source_table}] "
                                        f"({col_names}) VALUES ({placeholders})",
                                        tuple(row),
                                    )
                                except sqlite3.OperationalError:
                                    break  # Schema mismatch — skip this brain
                            brain_conn.commit()
                            fed_brains.append(f"{brain_name}.db")
                    except FileNotFoundError:
                        logger.debug("Brain DB not found, skipping: %s", brain_name)
                    except Exception as e:
                        logger.warning("Brain feed failed for %s: %s", brain_name, e)

        return {
            "status": result.status,
            "file_name": result.file_name,
            "doc_type": result.doc_type,
            "brains_fed": fed_brains,
            "quotes_inserted": result.quotes_inserted,
            "events_inserted": result.events_inserted,
            "authorities_inserted": result.authorities_inserted,
            "duration_sec": result.duration_sec,
            "error": result.error,
        }

    except Exception as e:
        logger.error(f"brain_feed failed for {file_path}: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def handle_add_evidence(payload: dict) -> dict:
    """Manually add an evidence file — same as auto_classify but explicit."""
    return handle_auto_classify(payload)


def handle_check_status(payload: dict) -> dict:
    """Check processing status for a file across intake_log and documents tables."""
    file_path = payload.get("file_path", "")
    db_path = payload.get("db_path") or _default_db_path()

    try:
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA cache_size=-32000")
        conn.row_factory = sqlite3.Row

        # Get all table names to avoid querying missing tables
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}

        result = {"status": "not_found", "file_path": file_path}

        # Check intake_log first (most recent processing record)
        if "intake_log" in tables:
            row = conn.execute(
                "SELECT * FROM intake_log WHERE file_path = ? "
                "ORDER BY processed_at DESC LIMIT 1",
                (file_path,)
            ).fetchone()
            if row:
                result = {
                    "status": row["status"],
                    "doc_type": row["doc_type"] if "doc_type" in row.keys() else None,
                    "quotes_inserted": row["quotes_inserted"] if "quotes_inserted" in row.keys() else 0,
                    "events_inserted": row["events_inserted"] if "events_inserted" in row.keys() else 0,
                    "processed_at": row["processed_at"] if "processed_at" in row.keys() else None,
                    "source": "intake_log",
                }

        # Also check documents table for readiness_score
        if "documents" in tables:
            doc = conn.execute(
                "SELECT doc_type, lanes, urgency, readiness_score, ingested_at "
                "FROM documents WHERE file_path = ? LIMIT 1",
                (file_path,)
            ).fetchone()
            if doc:
                result["readiness_score"] = doc["readiness_score"]
                result["ingested_at"] = doc["ingested_at"]
                if result["status"] == "not_found":
                    result["status"] = "ingested"
                    result["doc_type"] = doc["doc_type"]
                    result["source"] = "documents"

        conn.close()
        return result

    except Exception as e:
        return {"status": "error", "error": str(e)}


def handle_filing_scan(payload: dict) -> dict:
    """Run TriggerScanner to find filings that are ready or urgent.

    Payload options:
        db_path (str, optional): Path to litigation DB.
        deadline_days (int, optional): Override deadline scan window.
        readiness_threshold (float, optional): Override EGCP threshold.
        include_separation (bool, optional): Include separation urgency trigger.
    """
    try:
        from engines.filing_engine.triggers import TriggerScanner, TriggerConfig

        db_path = payload.get("db_path") or _default_db_path()

        config_kwargs = {}
        if "deadline_days" in payload:
            config_kwargs["deadline_medium_days"] = int(payload["deadline_days"])
        if "readiness_threshold" in payload:
            config_kwargs["readiness_threshold"] = float(payload["readiness_threshold"])
        config = TriggerConfig(**config_kwargs) if config_kwargs else None

        scanner = TriggerScanner(db_path=db_path, config=config)
        try:
            triggers = scanner.scan_all()

            if payload.get("include_separation", False):
                from datetime import date as _date
                sep_trigger = scanner.scan_separation_urgency(
                    last_contact=_date(2025, 7, 29)
                )
                if sep_trigger:
                    triggers.append(sep_trigger)

            from dataclasses import asdict
            return {
                "status": "completed",
                "trigger_count": len(triggers),
                "triggers": [asdict(t) for t in triggers],
                "report": scanner.to_report(triggers),
            }
        finally:
            scanner.close()

    except Exception as e:
        logger.error(f"filing_scan failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def handle_filing_validate(payload: dict) -> dict:
    """Run FilingValidator on a specific filing_id.

    Payload options:
        filing_id (str, required): Filing identifier (e.g. "F1").
        court_type (str, optional): Court type key (default: "mi_circuit").
        document_text (str, optional): Main document text to validate.
        components (dict, optional): Component flags (has_cos, has_caption, etc.).
    """
    filing_id = payload.get("filing_id", "")
    if not filing_id:
        return {"status": "error", "error": "filing_id is required"}

    try:
        from engines.filing_engine.validator import FilingValidator

        court_type = payload.get("court_type", "mi_circuit")
        document_text = payload.get("document_text", "")
        components = payload.get("components", {})

        validator = FilingValidator(court_type=court_type)
        result = validator.validate_filing(
            filing_id=filing_id,
            document_text=document_text,
            **components,
        )

        return {
            "status": "completed",
            "filing_id": filing_id,
            "court": result.court,
            "passed": result.passed,
            "summary": result.summary,
            "critical_failures": result.critical_failures,
            "warnings": result.warnings,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "severity": c.severity,
                    "message": c.message,
                    "rule": c.rule,
                    "auto_fixable": c.auto_fixable,
                }
                for c in result.checks
            ],
        }

    except Exception as e:
        logger.error(f"filing_validate failed for {filing_id}: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def handle_filing_run(payload: dict) -> dict:
    """Execute the full FilingPipeline for a filing_id.

    Payload options:
        filing_id (str, required): Filing identifier (e.g. "F1").
        db_path (str, optional): Path to litigation DB.
        dry_run (bool, optional): Validate only — default True for safety.
        court_type (str, optional): Court type key (default: "mi_circuit").
        case_number (str, optional): Court case number.
        court (str, optional): Court name.
        document_text (str, optional): Main document text.
        case_info (dict, optional): Caption generation data.
        parties_served (list, optional): COS party list.
        exhibits (list, optional): Exhibit dicts.
        signer_info (dict, optional): Signature block data.
        output_dir (str, optional): Output directory for assembled files.
        components (dict, optional): Component flags for validation.
    """
    filing_id = payload.get("filing_id", "")
    if not filing_id:
        return {"status": "error", "error": "filing_id is required"}

    dry_run = payload.get("dry_run", True)

    try:
        from engines.filing_engine.pipeline import FilingPipeline

        court_type = payload.get("court_type", "mi_circuit")
        pipeline = FilingPipeline(court_type=court_type)

        result = pipeline.run(
            filing_id=filing_id,
            case_number=payload.get("case_number", ""),
            court=payload.get("court", ""),
            dry_run=dry_run,
            trigger_reason=payload.get("trigger_reason", "daemon_dispatch"),
            document_text=payload.get("document_text", ""),
            case_info=payload.get("case_info"),
            parties_served=payload.get("parties_served"),
            exhibits=payload.get("exhibits"),
            signer_info=payload.get("signer_info"),
            output_dir=payload.get("output_dir", ""),
            components=payload.get("components"),
        )

        return result

    except Exception as e:
        logger.error(f"filing_run failed for {filing_id}: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def handle_brain_query(payload: dict) -> dict:
    """Execute a read-only SQL query against a specific brain database.

    Payload keys:
        brain_name (str):  Target brain (e.g. 'authority_brain', 'narrative_brain').
        sql        (str):  SQL query — must start with SELECT or PRAGMA.
        params     (list): Optional positional parameters for the query.
        limit      (int):  Max rows returned (default 100, ceiling 1000).

    Returns dict with status, brain, row_count, and results (list of dicts).
    """
    brain_name = payload.get("brain_name", "")
    sql = payload.get("sql", "")
    params = payload.get("params") or ()
    limit = min(int(payload.get("limit", 100)), 1000)

    if not brain_name:
        return {"status": "error", "error": "brain_name is required"}
    if not sql:
        return {"status": "error", "error": "sql query is required"}

    # Only allow reads — block INSERT / UPDATE / DELETE / DROP / ALTER / CREATE
    sql_upper = sql.strip().upper()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("PRAGMA"):
        return {"status": "error", "error": "Only SELECT and PRAGMA queries are allowed"}

    try:
        from brains.brain_manager import BrainManager
    except ImportError as e:
        logger.error(f"Cannot import BrainManager: {e}", exc_info=True)
        return {"status": "error", "error": f"Missing BrainManager: {e}"}

    try:
        bm = BrainManager()
        # Inject a LIMIT clause if the caller didn't supply one
        if "LIMIT" not in sql_upper:
            sql = f"{sql.rstrip().rstrip(';')} LIMIT {limit}"

        results = bm.query_brain(brain_name, sql, tuple(params))
        return {
            "status": "completed",
            "brain": brain_name,
            "row_count": len(results),
            "results": results,
        }
    except FileNotFoundError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"brain_query failed for {brain_name}: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def handle_brain_search(payload: dict) -> dict:
    """Cross-brain FTS5 search across all (or one) brain databases.

    Payload keys:
        query      (str):  Search term — supports FTS5 syntax (AND, OR, NEAR, *).
        brain_name (str):  Optional — restrict search to a single brain.
        limit      (int):  Max results per FTS table (default 20, ceiling 100).

    Returns dict with status, sanitized query, total_matches, brains_searched,
    and results (list of per-table match groups).
    """
    query = payload.get("query", "")
    brain_filter = payload.get("brain_name", "")
    limit = min(int(payload.get("limit", 20)), 100)

    if not query:
        return {"status": "error", "error": "query is required"}

    # FTS5 sanitize (Rule 5) — strip special chars except word chars, spaces, *, "
    sanitized = re.sub(r'[^\w\s*"]', ' ', query)
    if not sanitized.strip():
        return {"status": "error", "error": "Query empty after sanitization"}

    try:
        from brains.brain_manager import BrainManager, BRAIN_FTS_TABLES
    except ImportError as e:
        logger.error(f"Cannot import BrainManager: {e}", exc_info=True)
        return {"status": "error", "error": f"Missing BrainManager: {e}"}

    try:
        bm = BrainManager()

        if brain_filter:
            # ── Single-brain search ──
            fts_tables = BRAIN_FTS_TABLES.get(brain_filter, [])
            if not fts_tables:
                return {
                    "status": "completed",
                    "query": sanitized,
                    "total_matches": 0,
                    "brains_searched": 0,
                    "results": [],
                }

            all_results: list[dict] = []
            try:
                with bm.open_brain(brain_filter) as conn:
                    for fts_table in fts_tables:
                        try:
                            rows = conn.execute(
                                f"SELECT *, rank FROM [{fts_table}] "
                                f"WHERE [{fts_table}] MATCH ? ORDER BY rank LIMIT ?",
                                (sanitized, limit),
                            ).fetchall()
                            if rows:
                                columns = [
                                    desc[0] for desc in conn.execute(
                                        f"SELECT * FROM [{fts_table}] LIMIT 0"
                                    ).description
                                ] + ["rank"]
                                results = [dict(zip(columns, row)) for row in rows]
                                all_results.append({
                                    "brain": brain_filter,
                                    "fts_table": fts_table,
                                    "match_count": len(results),
                                    "results": results,
                                })
                        except sqlite3.OperationalError:
                            continue
            except FileNotFoundError:
                return {
                    "status": "error",
                    "error": f"Brain not found: {brain_filter}",
                }
        else:
            # ── Cross-brain search via BrainManager ──
            all_results = bm.search_all_brains(sanitized)

        total_matches = sum(r.get("match_count", 0) for r in all_results)
        brains_hit = len({r["brain"] for r in all_results}) if all_results else 0

        return {
            "status": "completed",
            "query": sanitized,
            "total_matches": total_matches,
            "brains_searched": brains_hit,
            "results": all_results,
        }
    except Exception as e:
        logger.error(f"brain_search failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def handle_automation(payload: dict) -> dict:
    """Run an automation script from the omega/utility registry.

    Payload keys:
        task_name : str (required) — key from AUTOMATION_REGISTRY
        target    : str (optional) — folder path for target-based scripts
        **        : any additional kwargs passed through to the entry function
    """
    task_name = payload.get("task_name")
    if not task_name:
        return {"status": "error", "output": "", "errors": "Missing required 'task_name' in payload"}

    logger.info("handle_automation: dispatching %r", task_name)
    try:
        # Lazy import — avoids loading all 13 scripts at daemon startup
        from automation import AUTOMATION_REGISTRY, run_automation

        if task_name not in AUTOMATION_REGISTRY:
            available = ", ".join(sorted(AUTOMATION_REGISTRY))
            return {
                "status": "error",
                "output": "",
                "errors": f"Unknown automation task: {task_name!r}. Available: {available}",
            }

        # Extract known keys; forward the rest as kwargs
        kwargs = {k: v for k, v in payload.items() if k != "task_name"}
        result = run_automation(task_name, **kwargs)
        logger.info(
            "handle_automation: %s finished with status=%s",
            task_name,
            result.get("status"),
        )
        return result

    except Exception as e:
        logger.error("handle_automation failed: %s", e, exc_info=True)
        return {"status": "error", "output": "", "errors": str(e)}


def handle_scheduled_maintenance(payload: dict) -> dict:
    """Run the full scheduled maintenance cycle directly.

    This is a convenience handler — the most common automation task.
    Equivalent to: handle_automation({"task_name": "scheduled_maintenance"})
    but avoids the extra dispatch layer for daemon cron entries.
    """
    logger.info("handle_scheduled_maintenance: starting maintenance cycle")
    try:
        from automation import run_automation

        result = run_automation("scheduled_maintenance")
        logger.info(
            "handle_scheduled_maintenance: finished with status=%s",
            result.get("status"),
        )
        return result

    except Exception as e:
        logger.error("handle_scheduled_maintenance failed: %s", e, exc_info=True)
        return {"status": "error", "output": "", "errors": str(e)}


def handle_legal_ai(payload: dict) -> dict:
    """Dispatch a legal_ai tool via the lazy-loading registry.

    Payload keys:
        tool_name  (str, required): Registry key (e.g. "damages_calculator").
        method     (str, optional): Explicit method name to call on the tool.
                                    Falls back to the registry's recommended method.
        init_kwargs (dict, optional): Override keyword args for the class constructor.
        **         : All other keys are forwarded as keyword arguments to the method.

    Returns dict with status, tool_name, method, and result (or error).
    """
    tool_name = payload.get("tool_name", "")
    if not tool_name:
        return {"status": "error", "error": "tool_name is required"}

    logger.info("handle_legal_ai: dispatching %r", tool_name)

    try:
        from legal_ai.registry import (
            LEGAL_AI_REGISTRY,
            get_legal_ai_tool,
            resolve_method,
        )
    except ImportError as e:
        logger.error("Cannot import legal_ai.registry: %s", e, exc_info=True)
        return {"status": "error", "error": f"Missing legal_ai.registry: {e}"}

    # Validate tool_name before attempting import
    if tool_name not in LEGAL_AI_REGISTRY:
        available = ", ".join(sorted(LEGAL_AI_REGISTRY))
        return {
            "status": "error",
            "error": f"Unknown legal_ai tool: {tool_name!r}. Available: {available}",
        }

    # Instantiate the tool (lazy-imported, cached singleton)
    try:
        init_kwargs = payload.get("init_kwargs")
        tool = get_legal_ai_tool(
            tool_name,
            init_kwargs=init_kwargs if isinstance(init_kwargs, dict) else None,
        )
    except Exception as e:
        logger.error("Failed to instantiate %r: %s", tool_name, e, exc_info=True)
        return {"status": "error", "error": f"Instantiation failed for {tool_name}: {e}"}

    # Resolve which method to call
    explicit_method = payload.get("method", "")
    try:
        method_name = resolve_method(tool, tool_name, explicit_method or None)
    except AttributeError as e:
        logger.error("No method found for %r: %s", tool_name, e, exc_info=True)
        return {"status": "error", "error": str(e)}

    # Build method kwargs — everything except our control keys
    _control_keys = {"tool_name", "method", "init_kwargs"}
    method_kwargs = {k: v for k, v in payload.items() if k not in _control_keys}

    # Call the method
    try:
        fn = getattr(tool, method_name)

        if method_kwargs:
            # Try with kwargs first; fall back to no-arg if signature doesn't match
            try:
                result = fn(**method_kwargs)
            except TypeError:
                logger.debug(
                    "Method %s.%s rejected kwargs, calling with no args",
                    tool_name, method_name,
                )
                result = fn()
        else:
            result = fn()

        # Normalize result to a dict
        if isinstance(result, dict):
            output = result
        elif hasattr(result, "__dict__"):
            output = {
                k: v for k, v in result.__dict__.items()
                if not k.startswith("_")
            }
        elif hasattr(result, "_asdict"):
            output = result._asdict()
        else:
            output = {"result": result}

        return {
            "status": "completed",
            "tool_name": tool_name,
            "method": method_name,
            **output,
        }

    except Exception as e:
        logger.error(
            "handle_legal_ai: %s.%s() failed: %s",
            tool_name, method_name, e, exc_info=True,
        )
        return {
            "status": "error",
            "tool_name": tool_name,
            "method": method_name,
            "error": str(e),
        }


def handle_tool_run(payload: dict) -> dict:
    """Run a standalone tool from the tools/ registry.

    Payload keys:
        tool_name (str, required): Registry key (e.g. "efiling_assembler",
                                   "drive_flattener.scanner").
        **       : All other keys are forwarded as keyword arguments to the
                   tool's main() or run() function.

    The tool's module is lazy-imported via tools.registry.get_tool().
    We look for a callable in this order: main() → run() → execute().
    If the callable returns a dict it is merged into the response;
    otherwise its return value is stored under the "result" key.

    Returns dict with at least {"status": "completed"|"error"}.
    """
    tool_name = payload.get("tool_name", "")
    if not tool_name:
        return {"status": "error", "error": "tool_name is required"}

    logger.info("handle_tool_run: dispatching %r", tool_name)

    # ── Lazy-import the registry (zero cost at daemon startup) ──
    try:
        from tools.registry import get_tool, search_tools
    except ImportError as e:
        logger.error("Cannot import tools.registry: %s", e, exc_info=True)
        return {"status": "error", "error": f"Missing tools.registry: {e}"}

    # ── Resolve tool module ──
    try:
        tool_module = get_tool(tool_name)
    except KeyError:
        # Tool not found — provide helpful suggestions
        suggestions = search_tools(tool_name.split(".")[-1])[:5]
        suggestion_names = [s["name"] for s in suggestions]
        return {
            "status": "error",
            "error": f"Unknown tool: {tool_name!r}",
            "suggestions": suggestion_names,
        }
    except ImportError as e:
        logger.error("Failed to import tool %r: %s", tool_name, e, exc_info=True)
        return {"status": "error", "error": f"Import failed for {tool_name}: {e}"}

    # ── Locate the entry-point function ──
    entry_fn = None
    entry_name = ""
    for candidate in ("main", "run", "execute"):
        fn = getattr(tool_module, candidate, None)
        if callable(fn):
            entry_fn = fn
            entry_name = candidate
            break

    if entry_fn is None:
        return {
            "status": "error",
            "error": (
                f"Tool {tool_name!r} has no main(), run(), or execute() function. "
                f"Available attributes: {[a for a in dir(tool_module) if not a.startswith('_')]}"
            ),
        }

    # ── Build kwargs (everything except control keys) ──
    kwargs = {k: v for k, v in payload.items() if k != "tool_name"}

    # ── Execute ──
    try:
        if kwargs:
            try:
                result = entry_fn(**kwargs)
            except TypeError:
                # Entry function may not accept kwargs — call bare
                logger.debug(
                    "Tool %s.%s() rejected kwargs, calling with no args",
                    tool_name, entry_name,
                )
                result = entry_fn()
        else:
            result = entry_fn()

        # Normalize result
        if isinstance(result, dict):
            output = result
        elif result is None:
            output = {}
        elif hasattr(result, "__dict__"):
            output = {k: v for k, v in result.__dict__.items() if not k.startswith("_")}
        elif hasattr(result, "_asdict"):
            output = result._asdict()
        else:
            output = {"result": result}

        return {
            "status": "completed",
            "tool_name": tool_name,
            "entry_point": entry_name,
            **output,
        }

    except Exception as e:
        logger.error(
            "handle_tool_run: %s.%s() failed: %s",
            tool_name, entry_name, e, exc_info=True,
        )
        return {
            "status": "error",
            "tool_name": tool_name,
            "entry_point": entry_name,
            "error": str(e),
        }


def handle_hydra_health(payload: dict) -> dict:
    """Return HYDRA resilience health snapshot.

    Checks active shards, genetic memory stats, disk usage,
    and protocol status. Safe to call frequently.
    """
    logger.info("handle_hydra_health: building snapshot")
    try:
        from hydra.daemon_bridge import hydra_health_snapshot
    except ImportError as e:
        logger.error("Cannot import hydra.daemon_bridge: %s", e, exc_info=True)
        return {"status": "error", "error": f"Missing hydra.daemon_bridge: {e}"}

    try:
        snapshot = hydra_health_snapshot()
        return {"status": "completed", **snapshot}
    except Exception as e:
        logger.error("handle_hydra_health failed: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}


def handle_hydra_respawn(payload: dict) -> dict:
    """Run a HYDRA check-and-heal cycle.

    Detects stale shards, salvages partial results via PhoenixProtocol,
    and prunes old HYDRA data. Designed to be called every 60-120s
    from the daemon main loop.
    """
    max_stale = payload.get("max_stale_minutes", 10.0)
    prune_hours = payload.get("prune_older_than_hours", 72)

    logger.info(
        "handle_hydra_respawn: max_stale=%.1fmin, prune=%dh",
        max_stale, prune_hours,
    )

    try:
        from hydra.daemon_bridge import check_and_heal
    except ImportError as e:
        logger.error("Cannot import hydra.daemon_bridge: %s", e, exc_info=True)
        return {"status": "error", "error": f"Missing hydra.daemon_bridge: {e}"}

    try:
        result = check_and_heal(
            max_stale_minutes=max_stale,
            prune_older_than_hours=prune_hours,
        )
        return {"status": "completed", **result}
    except Exception as e:
        logger.error("handle_hydra_respawn failed: %s", e, exc_info=True)
        return {"status": "error", "error": str(e)}


def _default_db_path() -> str:
    """Resolve default litigation database path.

    Resolution order:
      1. shared.get_db_path("litigation") — uses DB_REGISTRY
      2. LITIGATION_DB_PATH environment variable
      3. Walk up from this file to find litigation_context.db at repo root
    """
    # Method 1: shared module
    try:
        from shared import get_db_path
        return str(get_db_path("litigation"))
    except (ImportError, KeyError):
        pass

    # Method 2: Environment variable
    env_path = os.environ.get("LITIGATION_DB_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    # Method 3: Walk up from this file to repo root
    current = Path(__file__).resolve().parent
    for _ in range(6):  # Max 6 levels up
        candidate = current / "litigation_context.db"
        if candidate.exists():
            return str(candidate)
        current = current.parent

    # Last resort — log warning but return the expected path
    logger.warning("Could not resolve litigation_context.db — using expected path")
    return str(Path(__file__).resolve().parent.parent.parent / "litigation_context.db")


# ─── Handler Registry ────────────────────────────────────────────
HANDLER_MAP = {
    "auto_classify": handle_auto_classify,
    "ocr_extract": handle_ocr_extract,
    "brain_feed": handle_brain_feed,
    "add_evidence": handle_add_evidence,
    "check_status": handle_check_status,
    "classify_file": handle_auto_classify,  # shell_integration alias
    "filing_scan": handle_filing_scan,
    "filing_validate": handle_filing_validate,
    "filing_run": handle_filing_run,
    "brain_query": handle_brain_query,
    "brain_search": handle_brain_search,
    "automation": handle_automation,
    "scheduled_maintenance": handle_scheduled_maintenance,
    "legal_ai": handle_legal_ai,
    "tool_run": handle_tool_run,
    "hydra_health": handle_hydra_health,
    "hydra_respawn": handle_hydra_respawn,
}
