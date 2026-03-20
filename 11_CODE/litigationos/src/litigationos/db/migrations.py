"""Data migration tool — migrate records from the legacy 658-table litigation_context.db
into the clean LitigationOS product schema.

Usage::

    from litigationos.db.connection import DatabaseManager
    from litigationos.db.migrations import MigrationManager

    source = DatabaseManager(r"C:\\Users\\andre\\LitigationOS\\litigation_context.db")
    target = DatabaseManager("litigationos.db")
    target.initialize()

    mgr = MigrationManager(source, target)
    mgr.migrate_all()
    print(mgr.get_status())

The source database is NEVER written to — all operations are read-only.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from typing import Any

from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    """Return ``True`` if *name* exists as a table in *conn*."""
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def _count(conn: sqlite3.Connection, table: str) -> int:
    """Return the row count for *table*, or 0 if it doesn't exist."""
    if not _table_exists(conn, table):
        return 0
    return conn.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]


class MigrationManager:
    """Orchestrates data migration from the legacy ``litigation_context.db``
    into the clean product database.

    Parameters
    ----------
    source : DatabaseManager
        Connection manager pointing at the legacy DB (read-only).
    target : DatabaseManager
        Connection manager pointing at the product DB.
    """

    # Ordered list of (method_name, description) for migrate_all()
    _STEPS: list[tuple[str, str]] = [
        ("migrate_cases", "Cases"),
        ("migrate_parties", "Parties"),
        ("migrate_claims", "Claims"),
        ("migrate_filings", "Filings"),
        ("migrate_deadlines", "Deadlines"),
        ("migrate_evidence", "Evidence"),
        ("migrate_timeline", "Timeline events"),
        ("migrate_court_rules", "Court rules (MCR)"),
    ]

    def __init__(self, source: DatabaseManager, target: DatabaseManager) -> None:
        self._source = source
        self._target = target
        self._results: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def migrate_all(self) -> dict[str, dict[str, Any]]:
        """Run every migration step in dependency order.

        Returns
        -------
        dict
            Mapping of step name → ``{"migrated": int, "skipped": bool, "error": str|None}``.
        """
        logger.info("=== Starting full migration ===")
        for method_name, label in self._STEPS:
            logger.info("--- %s ---", label)
            try:
                getattr(self, method_name)()
            except Exception:
                logger.exception("Migration step '%s' failed", method_name)
        logger.info("=== Migration complete ===")
        return dict(self._results)

    # ------------------------------------------------------------------
    # Cases
    # ------------------------------------------------------------------

    def migrate_cases(self) -> int:
        """Extract cases from ``filing_stack_scores`` and ``convergence_filing_stacks``.

        Each unique ``(stack_name, court, jurisdiction)`` becomes a case.

        Returns the number of cases inserted.
        """
        src = self._source.connect()
        tgt = self._target.connect()
        count = 0
        try:
            if not _table_exists(src, "filing_stack_scores"):
                self._record("migrate_cases", 0, skipped=True, reason="source table missing")
                return 0

            rows = src.execute(
                "SELECT stack_id, stack_name, court, jurisdiction, scored_at "
                "FROM filing_stack_scores ORDER BY scored_at"
            ).fetchall()

            # Ensure MI jurisdiction exists
            tgt.execute(
                "INSERT OR IGNORE INTO jurisdictions (id, name, state_code, rules_version, enabled) "
                "VALUES ('MI', 'Michigan', 'MI', '2024', 1)"
            )

            for row in rows:
                case_type = self._infer_case_type(row["stack_name"], row["jurisdiction"])
                court_id = self._ensure_court(tgt, row["court"], row["jurisdiction"])
                tgt.execute(
                    "INSERT INTO cases (case_number, court_id, case_type, title, filed_date, status) "
                    "VALUES (?, ?, ?, ?, ?, 'active')",
                    (
                        row["stack_id"],
                        court_id,
                        case_type,
                        row["stack_name"],
                        row["scored_at"],
                    ),
                )
                count += 1

            tgt.commit()
            logger.info("Migrated %d cases", count)
            self._record("migrate_cases", count)
        except Exception as exc:
            tgt.rollback()
            logger.exception("migrate_cases failed")
            self._record("migrate_cases", count, error=str(exc))
            raise
        finally:
            src.close()
            tgt.close()
        return count

    # ------------------------------------------------------------------
    # Parties
    # ------------------------------------------------------------------

    def migrate_parties(self) -> int:
        """Extract parties from ``party_contacts`` and ``adversary_models``.

        Returns the number of parties inserted.
        """
        src = self._source.connect()
        tgt = self._target.connect()
        count = 0
        try:
            # Get the first case id (default fallback)
            default_case = tgt.execute("SELECT id FROM cases LIMIT 1").fetchone()
            default_case_id = default_case["id"] if default_case else None

            # --- party_contacts ---
            if _table_exists(src, "party_contacts"):
                rows = src.execute("SELECT * FROM party_contacts").fetchall()
                for row in rows:
                    role = self._normalise_role(row["role"])
                    # Link to all cases (pro se litigant appears in every case)
                    case_ids = [r["id"] for r in tgt.execute("SELECT id FROM cases").fetchall()]
                    if not case_ids and default_case_id:
                        case_ids = [default_case_id]
                    for cid in case_ids[:1]:  # Primary case link
                        tgt.execute(
                            "INSERT INTO parties (case_id, name, role, party_type, bar_number, email, phone, address) "
                            "VALUES (?, ?, ?, 'individual', ?, ?, ?, ?)",
                            (
                                cid,
                                row["party_name"],
                                role,
                                row["bar_number"],
                                row["email"],
                                row["phone"],
                                row["address"],
                            ),
                        )
                        count += 1
                logger.info("Migrated %d parties from party_contacts", len(rows))
            else:
                logger.info("party_contacts table not found — skipping")

            # --- adversary_models (extract unique filing vehicles as context) ---
            if _table_exists(src, "adversary_models"):
                adversary_count = _count(src, "adversary_models")
                logger.info(
                    "adversary_models has %d rows (stored as case notes, not parties)",
                    adversary_count,
                )

            tgt.commit()
            self._record("migrate_parties", count)
        except Exception as exc:
            tgt.rollback()
            logger.exception("migrate_parties failed")
            self._record("migrate_parties", count, error=str(exc))
            raise
        finally:
            src.close()
            tgt.close()
        return count

    # ------------------------------------------------------------------
    # Claims
    # ------------------------------------------------------------------

    def migrate_claims(self) -> int:
        """Extract claims from ``extracted_harms``, ``claims``, and ``tort_claims``.

        Returns the number of claims inserted.
        """
        src = self._source.connect()
        tgt = self._target.connect()
        count = 0
        try:
            default_case = tgt.execute("SELECT id FROM cases LIMIT 1").fetchone()
            default_case_id = default_case["id"] if default_case else None

            # --- extracted_harms (26K+ records — de-duplicate by category) ---
            if _table_exists(src, "extracted_harms"):
                rows = src.execute(
                    "SELECT category, subcategory, description, "
                    "constitutional_violation, mcr_violation, severity, adversary "
                    "FROM extracted_harms "
                    "GROUP BY category, subcategory "
                    "ORDER BY MAX(severity) DESC"
                ).fetchall()
                for idx, row in enumerate(rows, start=1):
                    title = f"{row['category']}: {row['subcategory'] or 'General'}"
                    legal_basis_parts = []
                    if row["constitutional_violation"]:
                        legal_basis_parts.append(row["constitutional_violation"])
                    if row["mcr_violation"]:
                        legal_basis_parts.append(row["mcr_violation"])
                    legal_basis = "; ".join(legal_basis_parts) or None

                    tgt.execute(
                        "INSERT INTO claims (case_id, count_number, title, legal_basis, status, notes) "
                        "VALUES (?, ?, ?, ?, 'active', ?)",
                        (
                            default_case_id,
                            idx,
                            title[:500],
                            legal_basis,
                            (row["description"] or "")[:2000],
                        ),
                    )
                    count += 1
                logger.info("Migrated %d claim groups from extracted_harms", len(rows))

            # --- tort_claims ---
            if _table_exists(src, "tort_claims"):
                tort_rows = src.execute(
                    "SELECT id, tort_type, defendant, elements_met, evidence_refs, "
                    "strength_score, status FROM tort_claims"
                ).fetchall()
                for row in tort_rows:
                    tgt.execute(
                        "INSERT INTO claims (case_id, title, legal_basis, status, damages_sought, notes) "
                        "VALUES (?, ?, ?, ?, NULL, ?)",
                        (
                            default_case_id,
                            f"Tort: {row['tort_type']}",
                            row["elements_met"],
                            row["status"] or "active",
                            f"Defendant: {row['defendant']}; Evidence: {row['evidence_refs']}",
                        ),
                    )
                    count += 1
                logger.info("Migrated %d rows from tort_claims", len(tort_rows))

            # --- claims table (legacy classifier output) ---
            if _table_exists(src, "claims"):
                legacy_rows = src.execute(
                    "SELECT claim_id, classification, actor, proposition, status "
                    "FROM claims LIMIT 500"
                ).fetchall()
                for row in legacy_rows:
                    tgt.execute(
                        "INSERT INTO claims (case_id, title, legal_basis, status, notes) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (
                            default_case_id,
                            (row["proposition"] or row["classification"] or "Unnamed claim")[:500],
                            row["classification"],
                            row["status"] or "active",
                            f"Actor: {row['actor']}",
                        ),
                    )
                    count += 1
                logger.info("Migrated %d rows from legacy claims", len(legacy_rows))

            tgt.commit()
            self._record("migrate_claims", count)
        except Exception as exc:
            tgt.rollback()
            logger.exception("migrate_claims failed")
            self._record("migrate_claims", count, error=str(exc))
            raise
        finally:
            src.close()
            tgt.close()
        return count

    # ------------------------------------------------------------------
    # Filings
    # ------------------------------------------------------------------

    def migrate_filings(self) -> int:
        """Extract filings from ``master_filing_index`` and ``convergence_filing_stacks``.

        Returns the number of filings inserted.
        """
        src = self._source.connect()
        tgt = self._target.connect()
        count = 0
        try:
            # Build a case-number → case-id lookup from target
            case_map: dict[str, int] = {}
            for row in tgt.execute("SELECT id, case_number FROM cases").fetchall():
                if row["case_number"]:
                    case_map[row["case_number"]] = row["id"]
            default_case = tgt.execute("SELECT id FROM cases LIMIT 1").fetchone()
            default_case_id = default_case["id"] if default_case else None

            # --- master_filing_index ---
            if _table_exists(src, "master_filing_index"):
                rows = src.execute(
                    "SELECT filename, path, size, stack_name, court, jurisdiction, "
                    "doc_type, word_count, readiness_score, created_at "
                    "FROM master_filing_index ORDER BY created_at"
                ).fetchall()

                for row in rows:
                    case_id = self._resolve_case_id(case_map, row["stack_name"], default_case_id)
                    filing_type = self._normalise_filing_type(row["doc_type"])
                    status = "filed" if (row["readiness_score"] or 0) > 0.8 else "draft"
                    tgt.execute(
                        "INSERT INTO filings (case_id, title, filing_type, status, file_path, "
                        "filed_date, compliance_score, word_count, notes) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            case_id,
                            row["filename"] or "Untitled",
                            filing_type,
                            status,
                            row["path"],
                            row["created_at"],
                            row["readiness_score"],
                            row["word_count"],
                            f"Source: master_filing_index; Court: {row['court']}",
                        ),
                    )
                    count += 1
                logger.info("Migrated %d filings from master_filing_index", len(rows))

            # --- convergence_filing_stacks (additional files linked to stacks) ---
            if _table_exists(src, "convergence_filing_stacks"):
                cfs_rows = src.execute(
                    "SELECT file_name, file_path, stack_name, doc_type, "
                    "court_action, created_at "
                    "FROM convergence_filing_stacks ORDER BY created_at"
                ).fetchall()
                for row in cfs_rows:
                    case_id = self._resolve_case_id(case_map, row["stack_name"], default_case_id)
                    filing_type = self._normalise_filing_type(row["doc_type"])
                    tgt.execute(
                        "INSERT INTO filings (case_id, title, filing_type, status, file_path, "
                        "filed_date, notes) "
                        "VALUES (?, ?, ?, 'draft', ?, ?, ?)",
                        (
                            case_id,
                            row["file_name"] or "Untitled",
                            filing_type,
                            row["file_path"],
                            row["created_at"],
                            f"Court action: {row['court_action']}",
                        ),
                    )
                    count += 1
                logger.info("Migrated %d filings from convergence_filing_stacks", len(cfs_rows))

            tgt.commit()
            self._record("migrate_filings", count)
        except Exception as exc:
            tgt.rollback()
            logger.exception("migrate_filings failed")
            self._record("migrate_filings", count, error=str(exc))
            raise
        finally:
            src.close()
            tgt.close()
        return count

    # ------------------------------------------------------------------
    # Deadlines
    # ------------------------------------------------------------------

    def migrate_deadlines(self) -> int:
        """Extract deadlines from ``litigation_deadlines``.

        Returns the number of deadlines inserted.
        """
        src = self._source.connect()
        tgt = self._target.connect()
        count = 0
        try:
            if not _table_exists(src, "litigation_deadlines"):
                self._record("migrate_deadlines", 0, skipped=True, reason="source table missing")
                return 0

            default_case = tgt.execute("SELECT id FROM cases LIMIT 1").fetchone()
            default_case_id = default_case["id"] if default_case else None

            rows = src.execute(
                "SELECT deadline_id, case_name, court, filing_type, due_date, "
                "priority, status, basis, authority, notes "
                "FROM litigation_deadlines ORDER BY due_date"
            ).fetchall()

            for row in rows:
                priority = (row["priority"] or "normal").lower()
                if priority not in ("critical", "high", "normal", "low"):
                    priority = "normal"
                status = (row["status"] or "pending").lower()
                if status not in ("pending", "extended", "met", "missed"):
                    status = "pending"

                rule_basis = " — ".join(
                    p for p in [row["basis"], row["authority"]] if p
                ) or None

                tgt.execute(
                    "INSERT INTO deadlines (case_id, title, due_date, rule_basis, status, priority, notes) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        default_case_id,
                        f"{row['filing_type'] or 'Deadline'} — {row['case_name'] or ''}".strip(" —"),
                        row["due_date"],
                        rule_basis,
                        status,
                        priority,
                        row["notes"],
                    ),
                )
                count += 1

            tgt.commit()
            logger.info("Migrated %d deadlines", count)
            self._record("migrate_deadlines", count)
        except Exception as exc:
            tgt.rollback()
            logger.exception("migrate_deadlines failed")
            self._record("migrate_deadlines", count, error=str(exc))
            raise
        finally:
            src.close()
            tgt.close()
        return count

    # ------------------------------------------------------------------
    # Evidence
    # ------------------------------------------------------------------

    def migrate_evidence(self) -> int:
        """Extract evidence from ``evidence_quotes``, ``exhibit_authentication``,
        and ``court_document_catalog``.

        Returns the number of evidence records inserted.
        """
        src = self._source.connect()
        tgt = self._target.connect()
        count = 0
        try:
            default_case = tgt.execute("SELECT id FROM cases LIMIT 1").fetchone()
            default_case_id = default_case["id"] if default_case else None

            # --- court_document_catalog (438 rows — primary documents) ---
            if _table_exists(src, "court_document_catalog"):
                rows = src.execute(
                    "SELECT id, filename, filepath, doc_type, case_number, "
                    "first_page_text, page_count, modified "
                    "FROM court_document_catalog ORDER BY id"
                ).fetchall()
                for row in rows:
                    file_type = self._normalise_file_type(row["filepath"])
                    tgt.execute(
                        "INSERT INTO evidence (case_id, title, description, file_path, "
                        "file_type, source, date_created, notes) "
                        "VALUES (?, ?, ?, ?, ?, 'court_document_catalog', ?, ?)",
                        (
                            default_case_id,
                            (row["filename"] or "Untitled")[:500],
                            (row["first_page_text"] or "")[:2000],
                            row["filepath"],
                            file_type,
                            row["modified"],
                            f"Pages: {row['page_count']}; Case#: {row['case_number']}",
                        ),
                    )
                    count += 1
                logger.info("Migrated %d evidence from court_document_catalog", len(rows))

            # --- exhibit_authentication (18K+ — authentication metadata) ---
            if _table_exists(src, "exhibit_authentication"):
                rows = src.execute(
                    "SELECT exhibit_description, category, auth_method, "
                    "mre_rule, foundation_witness, admissible, created_at "
                    "FROM exhibit_authentication "
                    "GROUP BY exhibit_description "
                    "ORDER BY created_at"
                ).fetchall()
                for row in rows:
                    auth_method = (row["auth_method"] or "")[:100]
                    tgt.execute(
                        "INSERT INTO evidence (case_id, title, description, file_type, "
                        "source, authentication_method, foundation_witness, "
                        "tags, notes) "
                        "VALUES (?, ?, ?, 'document', 'exhibit_authentication', ?, ?, ?, ?)",
                        (
                            default_case_id,
                            (row["exhibit_description"] or "Exhibit")[:500],
                            f"Category: {row['category']}",
                            auth_method,
                            row["foundation_witness"],
                            json.dumps([row["category"]]) if row["category"] else None,
                            f"MRE: {row['mre_rule']}; Admissible: {row['admissible']}",
                        ),
                    )
                    count += 1
                logger.info("Migrated %d evidence from exhibit_authentication", len(rows))

            # --- evidence_quotes (308K+ — sample top quotes by significance) ---
            if _table_exists(src, "evidence_quotes"):
                rows = src.execute(
                    "SELECT evidence_category, quote_text, quote_type, "
                    "speaker, date_ref, legal_significance, source_type, created_at "
                    "FROM evidence_quotes "
                    "WHERE legal_significance IS NOT NULL "
                    "ORDER BY created_at "
                    "LIMIT 5000"
                ).fetchall()
                for row in rows:
                    tgt.execute(
                        "INSERT INTO evidence (case_id, title, description, file_type, "
                        "source, date_created, tags, notes) "
                        "VALUES (?, ?, ?, 'text', 'evidence_quotes', ?, ?, ?)",
                        (
                            default_case_id,
                            f"Quote: {(row['evidence_category'] or 'General')[:100]}",
                            (row["quote_text"] or "")[:2000],
                            row["date_ref"],
                            json.dumps([row["evidence_category"], row["quote_type"]])
                            if row["evidence_category"]
                            else None,
                            f"Speaker: {row['speaker']}; Significance: {row['legal_significance']}",
                        ),
                    )
                    count += 1
                logger.info("Migrated %d key evidence quotes", len(rows))

            tgt.commit()
            self._record("migrate_evidence", count)
        except Exception as exc:
            tgt.rollback()
            logger.exception("migrate_evidence failed")
            self._record("migrate_evidence", count, error=str(exc))
            raise
        finally:
            src.close()
            tgt.close()
        return count

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------

    def migrate_timeline(self) -> int:
        """Extract timeline events from ``master_chronological_timeline`` (14K+ events).

        Returns the number of timeline events inserted.
        """
        src = self._source.connect()
        tgt = self._target.connect()
        count = 0
        try:
            if not _table_exists(src, "master_chronological_timeline"):
                self._record("migrate_timeline", 0, skipped=True, reason="source table missing")
                return 0

            default_case = tgt.execute("SELECT id FROM cases LIMIT 1").fetchone()
            default_case_id = default_case["id"] if default_case else None

            batch_size = 1000
            offset = 0

            while True:
                rows = src.execute(
                    "SELECT event_date, title, description, event_type, actor, "
                    "harm_to_andrew, authority_violated, evidence_refs "
                    "FROM master_chronological_timeline "
                    "ORDER BY event_date, id "
                    "LIMIT ? OFFSET ?",
                    (batch_size, offset),
                ).fetchall()

                if not rows:
                    break

                for row in rows:
                    event_type = self._normalise_event_type(row["event_type"])
                    importance = "normal"
                    if row["harm_to_andrew"] or row["authority_violated"]:
                        importance = "high"

                    description_parts = [row["description"] or ""]
                    if row["actor"]:
                        description_parts.append(f"Actor: {row['actor']}")
                    if row["harm_to_andrew"]:
                        description_parts.append(f"Harm: {row['harm_to_andrew']}")
                    if row["authority_violated"]:
                        description_parts.append(f"Authority: {row['authority_violated']}")

                    evidence_ids = None
                    if row["evidence_refs"]:
                        try:
                            evidence_ids = row["evidence_refs"] if row["evidence_refs"].startswith("[") else json.dumps([row["evidence_refs"]])
                        except Exception:
                            evidence_ids = json.dumps([str(row["evidence_refs"])])

                    tgt.execute(
                        "INSERT INTO timeline_events (case_id, event_date, title, description, "
                        "event_type, evidence_ids, importance) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            default_case_id,
                            row["event_date"] or "Unknown",
                            (row["title"] or "Untitled")[:500],
                            " | ".join(p for p in description_parts if p)[:2000],
                            event_type,
                            evidence_ids,
                            importance,
                        ),
                    )
                    count += 1

                offset += batch_size
                if count % 5000 == 0:
                    logger.info("Timeline migration progress: %d events", count)

            tgt.commit()
            logger.info("Migrated %d timeline events", count)
            self._record("migrate_timeline", count)
        except Exception as exc:
            tgt.rollback()
            logger.exception("migrate_timeline failed")
            self._record("migrate_timeline", count, error=str(exc))
            raise
        finally:
            src.close()
            tgt.close()
        return count

    # ------------------------------------------------------------------
    # Court Rules
    # ------------------------------------------------------------------

    def migrate_court_rules(self) -> int:
        """Extract court rules from ``mcr_encyclopedia`` (627 Michigan Court Rules).

        Returns the number of rules inserted.
        """
        src = self._source.connect()
        tgt = self._target.connect()
        count = 0
        try:
            if not _table_exists(src, "mcr_encyclopedia"):
                self._record("migrate_court_rules", 0, skipped=True, reason="source table missing")
                return 0

            rows = src.execute(
                "SELECT rule_number, rule_title, chapter, full_text, "
                "summary, filing_types, last_updated "
                "FROM mcr_encyclopedia ORDER BY rule_number"
            ).fetchall()

            for row in rows:
                category = self._infer_rule_category(
                    row["chapter"], row["rule_number"], row["filing_types"]
                )
                tgt.execute(
                    "INSERT INTO court_rules (jurisdiction_id, rule_number, title, "
                    "full_text, category, effective_date) "
                    "VALUES ('MI', ?, ?, ?, ?, ?)",
                    (
                        row["rule_number"],
                        row["rule_title"],
                        row["full_text"],
                        category,
                        row["last_updated"],
                    ),
                )
                count += 1

            tgt.commit()
            logger.info("Migrated %d court rules from mcr_encyclopedia", count)
            self._record("migrate_court_rules", count)
        except Exception as exc:
            tgt.rollback()
            logger.exception("migrate_court_rules failed")
            self._record("migrate_court_rules", count, error=str(exc))
            raise
        finally:
            src.close()
            tgt.close()
        return count

    # ------------------------------------------------------------------
    # Status & Rollback
    # ------------------------------------------------------------------

    def get_status(self) -> dict[str, dict[str, Any]]:
        """Return a summary of what has and hasn't been migrated.

        Returns
        -------
        dict
            Keyed by migration step name with counts, skip/error info, and
            current target-table row counts.
        """
        tgt = self._target.connect()
        try:
            target_counts = {}
            for table in (
                "cases", "parties", "claims", "filings",
                "deadlines", "evidence", "timeline_events", "court_rules",
            ):
                target_counts[table] = _count(tgt, table)
        finally:
            tgt.close()

        status: dict[str, dict[str, Any]] = {}
        for method_name, label in self._STEPS:
            result = self._results.get(method_name, {"migrated": 0, "status": "not_run"})
            status[method_name] = {
                "label": label,
                **result,
            }
        status["target_counts"] = target_counts  # type: ignore[assignment]
        return status

    def rollback(self) -> None:
        """Drop all data in the target database and re-run all migrations.

        .. warning:: This **deletes** all rows in the target product tables.
        """
        logger.warning("Rolling back — clearing all target data")
        tgt = self._target.connect()
        try:
            # Delete in reverse-FK order
            for table in (
                "timeline_events", "documents", "filings", "deadlines",
                "evidence", "claims", "parties", "court_rules",
                "scao_forms", "templates", "courts", "cases",
            ):
                tgt.execute(f"DELETE FROM [{table}]")
            tgt.commit()
            logger.info("Target tables cleared")
        finally:
            tgt.close()

        self._results.clear()
        self.migrate_all()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record(
        self,
        step: str,
        migrated: int,
        *,
        skipped: bool = False,
        reason: str | None = None,
        error: str | None = None,
    ) -> None:
        """Store migration result for ``get_status``."""
        self._results[step] = {
            "migrated": migrated,
            "skipped": skipped,
            "reason": reason,
            "error": error,
            "status": "error" if error else ("skipped" if skipped else "done"),
            "completed_at": datetime.now().isoformat(),
        }

    def _ensure_court(
        self,
        tgt: sqlite3.Connection,
        court_name: str | None,
        jurisdiction: str | None,
    ) -> int | None:
        """Get or create a court record in the target DB, return its id."""
        if not court_name:
            return None

        existing = tgt.execute(
            "SELECT id FROM courts WHERE name = ?", (court_name,)
        ).fetchone()
        if existing:
            return existing["id"]

        court_type = "circuit"
        name_lower = (court_name or "").lower()
        if "appeals" in name_lower or "coa" in name_lower:
            court_type = "coa"
        elif "supreme" in name_lower:
            court_type = "supreme"
        elif "probate" in name_lower:
            court_type = "probate"
        elif "district" in name_lower and "federal" not in (jurisdiction or "").lower():
            court_type = "district"
        elif "federal" in (jurisdiction or "").lower():
            court_type = "federal_district"

        jid = "MI"
        if jurisdiction and "federal" in jurisdiction.lower():
            jid = "US"
            tgt.execute(
                "INSERT OR IGNORE INTO jurisdictions (id, name, state_code, enabled) "
                "VALUES ('US', 'Federal', 'US', 1)"
            )

        cursor = tgt.execute(
            "INSERT INTO courts (jurisdiction_id, name, type) VALUES (?, ?, ?)",
            (jid, court_name, court_type),
        )
        return cursor.lastrowid

    @staticmethod
    def _infer_case_type(stack_name: str | None, jurisdiction: str | None) -> str:
        """Guess the case type from stack/jurisdiction text."""
        sn = (stack_name or "").lower()
        jr = (jurisdiction or "").lower()
        if "tort" in sn or "complaint" in sn:
            return "civil"
        if "appeal" in sn or "coa" in sn or "brief" in sn:
            return "appellate"
        if "scotus" in sn or "federal" in jr:
            return "federal"
        if "custody" in sn or "family" in sn or "watson" in sn:
            return "family"
        return "family"  # default for this litigation

    @staticmethod
    def _normalise_role(raw: str | None) -> str:
        """Map legacy role text to the product schema enum."""
        if not raw:
            return "plaintiff"
        r = raw.lower()
        if "plaintiff" in r or "appellant" in r or "petitioner" in r:
            return "plaintiff"
        if "defendant" in r or "appellee" in r or "respondent" in r:
            return "defendant"
        if "judge" in r:
            return "judge"
        if "attorney" in r:
            return "attorney"
        return "plaintiff"

    @staticmethod
    def _normalise_filing_type(raw: str | None) -> str | None:
        """Map legacy doc_type to the filings.filing_type enum."""
        if not raw:
            return None
        r = raw.lower()
        mapping = {
            "motion": "motion",
            "brief": "brief",
            "complaint": "complaint",
            "response": "response",
            "reply": "reply",
            "order": "order",
            "notice": "notice",
            "affidavit": "motion",
            "petition": "complaint",
            "memorandum": "brief",
        }
        for keyword, ftype in mapping.items():
            if keyword in r:
                return ftype
        return "motion"  # fallback

    @staticmethod
    def _normalise_event_type(raw: str | None) -> str | None:
        """Map legacy event_type to timeline_events.event_type enum."""
        if not raw:
            return None
        r = raw.lower()
        mapping = {
            "filing": "filing",
            "hearing": "hearing",
            "order": "order",
            "communication": "communication",
            "incident": "incident",
            "deadline": "deadline",
            "motion": "filing",
            "ruling": "order",
            "email": "communication",
            "phone": "communication",
            "visitation": "incident",
            "custody": "incident",
        }
        for keyword, etype in mapping.items():
            if keyword in r:
                return etype
        return "incident"

    @staticmethod
    def _normalise_file_type(filepath: str | None) -> str:
        """Infer file type from the file extension."""
        if not filepath:
            return "document"
        ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""
        mapping = {
            "pdf": "pdf",
            "png": "image",
            "jpg": "image",
            "jpeg": "image",
            "txt": "text",
            "eml": "email",
            "msg": "email",
            "doc": "document",
            "docx": "document",
        }
        return mapping.get(ext, "document")

    @staticmethod
    def _infer_rule_category(
        chapter: str | None, rule_number: str | None, filing_types: str | None
    ) -> str | None:
        """Guess a court_rules.category value from rule metadata."""
        text = " ".join(p for p in [chapter, rule_number, filing_types] if p).lower()
        if "appeal" in text:
            return "appeal"
        if "discovery" in text or "interrogator" in text or "deposition" in text:
            return "discovery"
        if "evidence" in text or "mre" in text:
            return "evidence"
        if "motion" in text:
            return "motion"
        if "service" in text or "summons" in text:
            return "service"
        if "format" in text or "caption" in text or "form" in text:
            return "format"
        return None

    def _resolve_case_id(
        self,
        case_map: dict[str, int],
        stack_name: str | None,
        default: int | None,
    ) -> int | None:
        """Find the best matching case_id for a stack_name."""
        if not stack_name:
            return default
        # Exact match on case_number (which is stack_id)
        for key, cid in case_map.items():
            if key and stack_name.lower() in key.lower():
                return cid
        return default
