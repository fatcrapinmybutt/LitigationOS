"""
Intake Pipeline — The Master Orchestrator
==========================================

Connects: Extractor → Classifier → Analyzer → Router → Database

This is the SINGLE entry point for processing ANY file into
the litigation knowledge base. Supports:

  1. Single file processing:     pipeline.process_file("path/to/doc.pdf")
  2. Folder intake:              pipeline.process_folder("path/to/intake/")
  3. Watched folder (continuous): pipeline.watch("path/to/intake/")

100% case-agnostic. Case context comes from CaseConfig.

Architecture:
  ┌─────────┐   ┌───────────┐   ┌────────────┐   ┌──────────┐   ┌────────┐
  │  FILE   │──▶│ EXTRACTOR │──▶│ CLASSIFIER │──▶│ ANALYZER │──▶│ ROUTER │
  │ (input) │   │ (text/OCR)│   │(type/lanes)│   │(deep NLP)│   │  (DB)  │
  └─────────┘   └───────────┘   └────────────┘   └──────────┘   └────────┘
       │                                                              │
       │              ┌──────────────────┐                            │
       └─────────────▶│  INTAKE LOG      │◀───────────────────────────┘
                      │  (audit trail)   │
                      └──────────────────┘
"""

import logging
import os
import threading
import time
from time import perf_counter_ns
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .extractor import TextExtractor, ExtractionResult
from .classifier import DocumentClassifier, ClassificationResult
from .analyzer import LitigationAnalyzer, AnalysisResult
from .router import DatabaseRouter
from .case_config import CaseConfig

logger = logging.getLogger("intake.pipeline")


@dataclass
class IntakeResult:
    """Result of processing a single file through the pipeline."""
    file_path: str = ""
    file_name: str = ""
    sha256: str = ""
    status: str = "pending"  # pending, processing, completed, skipped, error
    error: Optional[str] = None

    # Extraction
    extraction_method: str = ""
    page_count: int = 0
    char_count: int = 0

    # Classification
    doc_type: str = ""
    lanes: list[str] = field(default_factory=list)
    urgency: str = ""
    legal_topics: list[str] = field(default_factory=list)

    # Analysis
    quotes_found: int = 0
    events_found: int = 0
    authorities_found: int = 0
    impeachment_found: int = 0
    entities_found: int = 0

    # Routing
    document_id: int = 0
    quotes_inserted: int = 0
    events_inserted: int = 0
    authorities_inserted: int = 0
    impeachment_inserted: int = 0
    entities_inserted: int = 0

    # Timing
    duration_sec: float = 0.0
    processed_at: str = ""


@dataclass
class BatchResult:
    """Result of processing a batch of files."""
    total_files: int = 0
    processed: int = 0
    skipped: int = 0
    errors: int = 0
    results: list[IntakeResult] = field(default_factory=list)
    duration_sec: float = 0.0

    # Aggregate counts
    total_quotes: int = 0
    total_events: int = 0
    total_authorities: int = 0
    total_impeachment: int = 0
    total_entities: int = 0


# File extensions the pipeline can process
SUPPORTED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".md",
    ".csv", ".xlsx", ".xls",
    ".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp",
    ".html", ".htm", ".xml", ".rtf",
    ".msg", ".eml", ".odt", ".pptx", ".ppt", ".json",
}


class IntakePipeline:
    """Master orchestrator: File → Extract → Classify → Analyze → Route → Store.

    Usage:
        config = CaseConfig.auto_detect("/path/to/intake")
        pipeline = IntakePipeline(db_path="case.db", case_config=config)
        result = pipeline.process_file("evidence.pdf")
        batch = pipeline.process_folder("/path/to/intake/")
        pipeline.close()
    """

    def __init__(
        self,
        db_path: str | Path = None,
        case_config: CaseConfig = None,
        ocr_enabled: bool = True,
    ):
        self.case_config = case_config or CaseConfig()
        self.extractor = TextExtractor(ocr_enabled=ocr_enabled)
        self.classifier = DocumentClassifier(case_config=self.case_config)
        self.analyzer = LitigationAnalyzer(case_config=self.case_config)
        self.router = DatabaseRouter(db_path=db_path)

        # Connect to DB immediately if path provided
        if db_path:
            self.router.connect(db_path)

    def process_file(self, file_path: str | Path) -> IntakeResult:
        """Process a single file through the full pipeline.

        This is the main entry point for individual files.
        """
        t_start = perf_counter_ns()
        file_path = Path(file_path)
        result = IntakeResult(
            file_path=str(file_path),
            file_name=file_path.name,
            status="processing",
        )

        # Compute correlation ID up front for tracing
        correlation_id = self._quick_hash(file_path)[:12]
        logger.info(
            "pipeline.start",
            extra={"file": file_path.name, "correlation_id": correlation_id},
        )

        stage = "init"
        try:
            # ─── Phase 1: Extract ────────────────────────────────
            stage = "extract"
            t0 = perf_counter_ns()
            extraction = self.extractor.extract(file_path)
            t_extract = (perf_counter_ns() - t0) / 1_000_000

            if extraction.error:
                result.status = "error"
                result.error = f"Extraction: {extraction.error}"
                logger.error(
                    "pipeline.failed",
                    extra={"file": file_path.name, "error": result.error, "stage": stage},
                )
                return result

            logger.info(
                "stage.extract complete in %.2fms chars=%d",
                t_extract,
                extraction.char_count,
            )

            result.sha256 = extraction.sha256
            result.extraction_method = extraction.extraction_method
            result.page_count = extraction.page_count
            result.char_count = extraction.char_count

            # Skip empty files
            if extraction.char_count < 10:
                result.status = "skipped"
                result.error = "Empty or near-empty file"
                return result

            # ─── Phase 2: Classify ───────────────────────────────
            stage = "classify"
            t0 = perf_counter_ns()
            classification = self.classifier.classify(
                extraction.full_text,
                extraction.file_name,
            )
            t_classify = (perf_counter_ns() - t0) / 1_000_000
            logger.info(
                "stage.classify complete in %.2fms type=%s",
                t_classify,
                classification.doc_type,
            )

            result.doc_type = classification.doc_type
            result.lanes = classification.lanes
            result.urgency = classification.urgency
            result.legal_topics = classification.legal_topics

            # ─── Phase 3: Analyze ────────────────────────────────
            stage = "analyze"
            t0 = perf_counter_ns()
            analysis = self.analyzer.analyze(
                extraction.full_text,
                file_name=extraction.file_name,
                lanes=classification.lanes,
                page_texts=extraction.pages,
            )
            t_analyze = (perf_counter_ns() - t0) / 1_000_000
            logger.info(
                "stage.analyze complete in %.2fms quotes=%d events=%d",
                t_analyze,
                len(analysis.evidence_quotes),
                len(analysis.timeline_events),
            )

            result.quotes_found = len(analysis.evidence_quotes)
            result.events_found = len(analysis.timeline_events)
            result.authorities_found = len(analysis.authority_refs)
            result.impeachment_found = len(analysis.impeachment_items)
            result.entities_found = len(analysis.entities)

            # ─── Phase 4: Route to Database ──────────────────────
            stage = "route"
            t0 = perf_counter_ns()
            doc_id = self.router.store_document(
                extraction, classification, analysis
            )
            result.document_id = doc_id

            self.router.store_pages(doc_id, extraction.pages)

            result.quotes_inserted = self.router.store_evidence_quotes(
                analysis.evidence_quotes
            )
            result.events_inserted = self.router.store_timeline_events(
                analysis.timeline_events
            )
            result.authorities_inserted = self.router.store_authority_refs(
                analysis.authority_refs, extraction.file_name
            )
            result.impeachment_inserted = self.router.store_impeachment(
                analysis.impeachment_items
            )
            result.entities_inserted = self.router.store_entities(
                analysis.entities,
                source_file=extraction.file_name,
                lane=classification.lanes[0] if classification.lanes else "",
            )
            t_route = (perf_counter_ns() - t0) / 1_000_000
            logger.info(
                "stage.route complete in %.2fms doc_id=%d",
                t_route,
                doc_id,
            )

            result.status = "completed"

        except Exception as e:
            result.status = "error"
            result.error = f"{type(e).__name__}: {e}"
            logger.error(
                "pipeline.failed",
                extra={"file": result.file_name, "error": str(e), "stage": stage},
                exc_info=True,
            )

        finally:
            elapsed_ms = (perf_counter_ns() - t_start) / 1_000_000
            result.duration_sec = round(elapsed_ms / 1000, 3)
            result.processed_at = datetime.utcnow().isoformat()

            if result.status == "completed":
                logger.info(
                    "pipeline.complete",
                    extra={
                        "file": result.file_name,
                        "correlation_id": correlation_id,
                        "elapsed_ms": round(elapsed_ms, 2),
                        "doc_type": result.doc_type,
                    },
                )

            # Log to intake_log table
            try:
                self.router.log_intake({
                    "file_path": result.file_path,
                    "file_name": result.file_name,
                    "sha256": result.sha256,
                    "doc_type": result.doc_type,
                    "lanes": result.lanes,
                    "quotes_inserted": result.quotes_inserted,
                    "events_inserted": result.events_inserted,
                    "authorities_inserted": result.authorities_inserted,
                    "impeachment_inserted": result.impeachment_inserted,
                    "entities_inserted": result.entities_inserted,
                    "status": result.status,
                    "error": result.error,
                })
            except Exception:
                pass  # Don't fail the pipeline if logging fails

        return result

    def process_folder(
        self,
        folder_path: str | Path,
        recursive: bool = True,
        max_files: int = 0,
        skip_existing: bool = True,
        resume: bool = True,
    ) -> BatchResult:
        """Process all supported files in a folder.

        Args:
            folder_path: Directory to scan
            recursive: Walk subdirectories
            max_files: Limit (0 = unlimited)
            skip_existing: Skip files already in the database (by hash)
            resume: Skip files whose SHA256 already exists in documents table
        """
        t_batch_start = perf_counter_ns()
        folder = Path(folder_path)
        batch = BatchResult()

        if not folder.exists():
            batch.errors = 1
            return batch

        # Collect files
        files = []
        if recursive:
            for root, _, filenames in os.walk(folder):
                for fname in filenames:
                    fpath = Path(root) / fname
                    if fpath.suffix.lower() in SUPPORTED_EXTENSIONS:
                        files.append(fpath)
        else:
            files = [
                f for f in folder.iterdir()
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
            ]

        batch.total_files = len(files)
        if max_files > 0:
            files = files[:max_files]

        logger.info("batch.start files=%d", len(files))

        # Load known hashes for dedup
        known_hashes = set()
        if skip_existing:
            try:
                conn = self.router.get_conn()
                rows = conn.execute(
                    "SELECT sha256 FROM documents WHERE sha256 IS NOT NULL"
                ).fetchall()
                known_hashes = {r["sha256"] for r in rows}
            except Exception as e:
                logger.warning(
                    "batch.dedup_disabled — could not load known hashes: %s. "
                    "Duplicates may be re-ingested.", e
                )

        # Process each file
        processed_files: list[str] = []
        for fpath in files:
            # Resume check — skip files already ingested (by quick hash)
            if resume and self.router:
                try:
                    conn = self.router.get_conn()
                    existing = conn.execute(
                        "SELECT id FROM documents WHERE sha256 = ?",
                        (self._quick_hash(fpath),),
                    ).fetchone()
                    if existing:
                        logger.info("batch.skip already_ingested file=%s", fpath.name)
                        batch.skipped += 1
                        continue
                except Exception:
                    pass  # If resume check fails, proceed with processing

            # Legacy dedup via pre-loaded hash set
            if skip_existing and known_hashes:
                quick_hash = TextExtractor._hash_file(fpath)
                if quick_hash in known_hashes:
                    batch.skipped += 1
                    continue

            result = self.process_file(fpath)
            batch.results.append(result)

            if result.status == "completed":
                batch.processed += 1
                processed_files.append(fpath.name)
                batch.total_quotes += result.quotes_inserted
                batch.total_events += result.events_inserted
                batch.total_authorities += result.authorities_inserted
                batch.total_impeachment += result.impeachment_inserted
                batch.total_entities += result.entities_inserted
            elif result.status == "skipped":
                batch.skipped += 1
            elif result.status == "error":
                batch.errors += 1
                logger.warning("Error processing %s: %s", fpath.name, result.error)

        elapsed = (perf_counter_ns() - t_batch_start) / 1_000_000_000
        batch.duration_sec = round(elapsed, 3)
        logger.info(
            "batch.complete processed=%d skipped=%d failed=%d elapsed=%.1fs",
            batch.processed,
            batch.skipped,
            batch.errors,
            elapsed,
        )
        return batch

    def batch_process(
        self,
        files: list[str | Path],
        resume: bool = True,
    ) -> dict:
        """Process an explicit list of files with resume/checkpoint support.

        Args:
            files: List of file paths to process.
            resume: Skip files whose SHA256 already exists in the documents table.

        Returns:
            Dict with total, processed, skipped, failed, elapsed_s, files_processed.
        """
        t_batch_start = perf_counter_ns()
        processed = 0
        skipped = 0
        failed = 0
        processed_files: list[str] = []

        logger.info("batch.start files=%d", len(files))

        for file_path in files:
            fpath = Path(file_path)

            # Resume check — skip files already ingested
            if resume and self.router:
                try:
                    conn = self.router.get_conn()
                    existing = conn.execute(
                        "SELECT id FROM documents WHERE sha256 = ?",
                        (self._quick_hash(fpath),),
                    ).fetchone()
                    if existing:
                        logger.info("batch.skip already_ingested file=%s", fpath.name)
                        skipped += 1
                        continue
                except Exception:
                    pass  # If resume check fails, proceed with processing

            result = self.process_file(fpath)

            if result.status == "completed":
                processed += 1
                processed_files.append(fpath.name)
            elif result.status == "skipped":
                skipped += 1
            elif result.status == "error":
                failed += 1
                logger.warning("Error processing %s: %s", fpath.name, result.error)

        elapsed = (perf_counter_ns() - t_batch_start) / 1_000_000_000
        logger.info(
            "batch.complete processed=%d skipped=%d failed=%d elapsed=%.1fs",
            processed,
            skipped,
            failed,
            elapsed,
        )

        return {
            "total": len(files),
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "elapsed_s": round(elapsed, 2),
            "files_processed": processed_files,
        }

    def _quick_hash(self, file_path: str | Path) -> str:
        """Compute SHA256 of a file for dedup check without full extraction."""
        import hashlib
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def close(self):
        """Close database connection and clean up."""
        self.stop()
        self.router.close()

    # ── Filesystem watcher ───────────────────────────────────────

    def watch(
        self,
        watch_dir: str | Path,
        poll_interval: float = 1.0,
        debounce_seconds: float = 3.0,
    ) -> None:
        """Monitor *watch_dir* for new files and process them automatically.

        Uses ``watchdog`` to detect created / moved files, filters to
        :data:`SUPPORTED_EXTENSIONS`, debounces duplicates, then feeds each
        file through :meth:`process_file`.

        The call blocks until ``KeyboardInterrupt`` or until :meth:`stop` is
        called from another thread.

        Args:
            watch_dir: Directory to monitor (must exist).
            poll_interval: Seconds between observer poll ticks.
            debounce_seconds: Ignore repeat events for the same path within
                this window.
        """
        from watchdog.observers import Observer
        from watchdog.events import (
            FileSystemEventHandler,
            FileCreatedEvent,
            FileMovedEvent,
        )

        watch_path = Path(watch_dir)
        if not watch_path.is_dir():
            raise NotADirectoryError(f"watch_dir does not exist: {watch_path}")

        debounce_lock = threading.Lock()
        debounce_map: dict[str, float] = {}

        pipeline_ref = self  # capture for inner class

        class _IntakeHandler(FileSystemEventHandler):
            """Handles create / move events for supported file types."""

            def _should_process(self, path: str) -> bool:
                ext = Path(path).suffix.lower()
                if ext not in SUPPORTED_EXTENSIONS:
                    return False
                now = time.time()
                with debounce_lock:
                    last_seen = debounce_map.get(path, 0.0)
                    if now - last_seen < debounce_seconds:
                        return False
                    debounce_map[path] = now
                return True

            def _handle(self, path: str) -> None:
                if not self._should_process(path):
                    return
                logger.info("Watcher detected new file: %s", Path(path).name)
                try:
                    result = pipeline_ref.process_file(path)
                    if result.status == "completed":
                        logger.info(
                            "Processed %s → %d quotes, %d events (%.1fs)",
                            result.file_name,
                            result.quotes_inserted,
                            result.events_inserted,
                            result.duration_sec,
                        )
                    elif result.status == "skipped":
                        logger.debug("Skipped %s: %s", result.file_name, result.error)
                    else:
                        logger.warning(
                            "Error processing %s: %s", result.file_name, result.error
                        )
                except Exception:
                    logger.exception("Unhandled error processing %s", path)

            def on_created(self, event: FileCreatedEvent) -> None:  # type: ignore[override]
                if not event.is_directory:
                    self._handle(event.src_path)

            def on_moved(self, event: FileMovedEvent) -> None:  # type: ignore[override]
                if not event.is_directory:
                    self._handle(event.dest_path)

        observer = Observer()
        observer.schedule(_IntakeHandler(), str(watch_path), recursive=True)
        self._observer = observer
        observer.start()
        logger.info(
            "Watching %s for new files (poll=%.1fs, debounce=%.1fs) …",
            watch_path,
            poll_interval,
            debounce_seconds,
        )

        try:
            while observer.is_alive():
                observer.join(timeout=poll_interval)
        except KeyboardInterrupt:
            logger.info("Watch interrupted — shutting down observer.")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the filesystem observer if one is running."""
        observer = getattr(self, "_observer", None)
        if observer is not None and observer.is_alive():
            observer.stop()
            observer.join(timeout=5)
            logger.info("Observer stopped.")
        self._observer = None
