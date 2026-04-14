#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j Import Hygiene Module
============================

Enhanced utilities for safe, robust Neo4j CSV imports with improved:
- Error handling and recovery
- Transaction safety
- Data quality validation
- Logging and audit trails
- Memory efficiency
- Incremental import support
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from src.neo4j_sanitizer import (
    sanitize_csv_row,
    sanitize_path,
    validate_csv_headers,
    validate_file_size,
)

logger = logging.getLogger(__name__)


@dataclass
class ImportStats:
    """Statistics for an import operation."""

    nodes_processed: int = 0
    edges_processed: int = 0
    nodes_skipped: int = 0
    edges_skipped: int = 0
    errors: int = 0
    warnings: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0


@dataclass
class ValidationResult:
    """Result of data validation."""

    valid: bool
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)


class Neo4jImportValidator:
    """Validator for Neo4j CSV import data."""

    def __init__(self, max_errors: int = 100):
        """Initialize validator.

        Args:
            max_errors: Maximum errors to collect before stopping
        """
        self.max_errors = max_errors

    def validate_nodes_csv(self, csv_path: Path, max_rows: Optional[int] = None) -> ValidationResult:
        """Validate a nodes CSV file.

        Args:
            csv_path: Path to the nodes CSV file
            max_rows: Maximum rows to validate (None = all)

        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            stats={"type": "nodes", "path": str(csv_path)},
        )

        try:
            csv_path = sanitize_path(csv_path)
            validate_file_size(csv_path)

            with csv_path.open("r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames:
                    result.add_error("No headers found in CSV")
                    return result

                try:
                    header_info = validate_csv_headers(list(reader.fieldnames), require_id=True)
                    result.stats["headers"] = header_info
                except Exception as e:
                    result.add_error(f"Invalid headers: {e}")
                    return result

                seen_ids: Set[str] = set()
                row_count = 0

                for i, row in enumerate(reader, start=2):
                    if max_rows and i > max_rows + 1:
                        break

                    row_count += 1

                    node_id = row.get(":ID") or row.get("id:ID")
                    if not node_id:
                        result.add_error(f"Row {i}: Missing :ID value")
                        if len(result.errors) >= self.max_errors:
                            break
                        continue

                    if node_id in seen_ids:
                        result.add_warning(f"Row {i}: Duplicate :ID '{node_id}'")
                    seen_ids.add(node_id)

                    empty_fields = [k for k, v in row.items() if not v and k != ":LABEL"]
                    if empty_fields:
                        result.add_warning(f"Row {i}: Empty fields {empty_fields[:3]}")

                result.stats["row_count"] = row_count
                result.stats["unique_ids"] = len(seen_ids)

        except Exception as e:
            result.add_error(f"Failed to validate CSV: {e}")
            logger.exception("CSV validation error")

        return result

    def validate_edges_csv(
        self,
        csv_path: Path,
        valid_node_ids: Optional[Set[str]] = None,
        max_rows: Optional[int] = None,
    ) -> ValidationResult:
        """Validate an edges CSV file.

        Args:
            csv_path: Path to the edges CSV file
            valid_node_ids: Set of valid node IDs to check references
            max_rows: Maximum rows to validate (None = all)

        Returns:
            ValidationResult with validation details
        """
        result = ValidationResult(
            valid=True,
            errors=[],
            warnings=[],
            stats={"type": "edges", "path": str(csv_path)},
        )

        try:
            csv_path = sanitize_path(csv_path)
            validate_file_size(csv_path)

            with csv_path.open("r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)

                if not reader.fieldnames:
                    result.add_error("No headers found in CSV")
                    return result

                headers = set(reader.fieldnames)
                if ":START_ID" not in headers:
                    result.add_error("Missing :START_ID header")
                if ":END_ID" not in headers:
                    result.add_error("Missing :END_ID header")
                if ":TYPE" not in headers:
                    result.add_error("Missing :TYPE header")

                if result.errors:
                    return result

                row_count = 0
                invalid_refs = 0

                for i, row in enumerate(reader, start=2):
                    if max_rows and i > max_rows + 1:
                        break

                    row_count += 1

                    start_id = row.get(":START_ID")
                    end_id = row.get(":END_ID")
                    edge_type = row.get(":TYPE")

                    if not start_id or not end_id:
                        result.add_error(f"Row {i}: Missing START_ID or END_ID")
                        if len(result.errors) >= self.max_errors:
                            break
                        continue

                    if not edge_type:
                        result.add_warning(f"Row {i}: Missing :TYPE")

                    if valid_node_ids:
                        if start_id not in valid_node_ids:
                            result.add_warning(f"Row {i}: START_ID '{start_id}' not found in nodes")
                            invalid_refs += 1
                        if end_id not in valid_node_ids:
                            result.add_warning(f"Row {i}: END_ID '{end_id}' not found in nodes")
                            invalid_refs += 1

                result.stats["row_count"] = row_count
                result.stats["invalid_refs"] = invalid_refs

        except Exception as e:
            result.add_error(f"Failed to validate CSV: {e}")
            logger.exception("CSV validation error")

        return result


class Neo4jImportLogger:
    """Audit logger for Neo4j import operations."""

    def __init__(self, log_dir: Path):
        """Initialize logger.

        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.audit_log = self.log_dir / f"neo4j_import_{timestamp}.jsonl"
        self.error_log = self.log_dir / f"neo4j_errors_{timestamp}.log"

    def log_event(self, event_type: str, data: Dict[str, Any], level: str = "INFO") -> None:
        """Log an import event.

        Args:
            event_type: Type of event (start, end, error, etc.)
            data: Event data
            level: Log level
        """
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "level": level,
            "data": data,
        }

        with self.audit_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

        if level in ("ERROR", "CRITICAL"):
            with self.error_log.open("a", encoding="utf-8") as f:
                f.write(f"[{event['timestamp']}] {event_type}: {data}\n")

    def log_validation(self, result: ValidationResult) -> None:
        """Log validation results."""
        self.log_event(
            "validation",
            {
                "valid": result.valid,
                "error_count": len(result.errors),
                "warning_count": len(result.warnings),
                "stats": result.stats,
            },
            level="ERROR" if not result.valid else "INFO",
        )

    def log_import_stats(self, stats: ImportStats) -> None:
        """Log import statistics."""
        self.log_event("import_stats", stats.to_dict())


def compute_file_checksum(path: Path, algorithm: str = "sha256") -> str:
    """Compute checksum of a file.

    Args:
        path: Path to file
        algorithm: Hash algorithm to use

    Returns:
        Hexadecimal digest of file
    """
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def create_import_manifest(
    nodes_path: Path,
    edges_path: Path,
    output_path: Path,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Create a manifest file for an import operation."""
    manifest = {
        "version": "1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": {
            "nodes": {
                "path": str(nodes_path),
                "checksum": compute_file_checksum(nodes_path),
                "size_bytes": nodes_path.stat().st_size,
            },
            "edges": {
                "path": str(edges_path),
                "checksum": compute_file_checksum(edges_path),
                "size_bytes": edges_path.stat().st_size,
            },
        },
        "metadata": metadata or {},
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def sanitize_csv_for_import(input_path: Path, output_path: Path, injection_mode: str = "escape") -> int:
    """Sanitize a CSV file for safe import.

    Returns:
        Number of rows processed
    """
    input_path = sanitize_path(input_path)
    validate_file_size(input_path)

    row_count = 0

    with input_path.open("r", encoding="utf-8", errors="replace") as infile:
        reader = csv.reader(infile)

        with output_path.open("w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)

            for row in reader:
                sanitized = sanitize_csv_row(row, injection_mode=injection_mode)
                writer.writerow(sanitized)
                row_count += 1

    return row_count


def merge_csv_files(
    input_paths: List[Path],
    output_path: Path,
    skip_duplicate_headers: bool = True,
) -> Tuple[int, int]:
    """Merge multiple CSV files into one.

    Returns:
        Tuple of (total_rows, files_merged)
    """
    total_rows = 0
    files_merged = 0
    writer = None

    with output_path.open("w", encoding="utf-8", newline="") as outfile:
        for i, input_path in enumerate(input_paths):
            try:
                input_path = sanitize_path(input_path)

                with input_path.open("r", encoding="utf-8", errors="replace") as infile:
                    reader = csv.reader(infile)

                    for j, row in enumerate(reader):
                        if skip_duplicate_headers and i > 0 and j == 0:
                            continue

                        if writer is None:
                            writer = csv.writer(outfile, quoting=csv.QUOTE_MINIMAL)

                        writer.writerow(row)
                        total_rows += 1

                files_merged += 1

            except Exception as e:
                logger.error("Failed to merge %s: %s", input_path, e)

    return total_rows, files_merged


def create_backup(source_path: Path, backup_dir: Path) -> Path:
    """Create a timestamped backup of a file."""
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
    backup_path = backup_dir / backup_name

    shutil.copy2(source_path, backup_path)

    logger.info("Created backup: %s", backup_path)
    return backup_path


def extract_node_ids_from_csv(csv_path: Path) -> Set[str]:
    """Extract all node IDs from a nodes CSV file."""
    node_ids: Set[str] = set()

    csv_path = sanitize_path(csv_path)

    with csv_path.open("r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)

        for row in reader:
            node_id = row.get(":ID") or row.get("id:ID")
            if node_id:
                node_ids.add(node_id)

    return node_ids


def generate_import_summary(
    validation_results: List[ValidationResult],
    import_stats: ImportStats,
    output_path: Path,
) -> None:
    """Generate a human-readable import summary."""
    lines = [
        "Neo4j Import Summary",
        "=" * 50,
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Validation Results:",
        "-" * 50,
    ]

    for i, result in enumerate(validation_results, start=1):
        lines.append(f"\n{i}. {result.stats.get('type', 'unknown').upper()}: {result.stats.get('path', 'N/A')}")
        lines.append(f"   Status: {'PASSED' if result.valid else 'FAILED'}")
        lines.append(f"   Errors: {len(result.errors)}")
        lines.append(f"   Warnings: {len(result.warnings)}")

        if result.errors:
            lines.append("\n   Errors:")
            for error in result.errors[:10]:
                lines.append(f"     - {error}")
            if len(result.errors) > 10:
                lines.append(f"     ... and {len(result.errors) - 10} more")

    lines.extend(
        [
            "",
            "Import Statistics:",
            "-" * 50,
            f"Nodes processed: {import_stats.nodes_processed}",
            f"Edges processed: {import_stats.edges_processed}",
            f"Nodes skipped: {import_stats.nodes_skipped}",
            f"Edges skipped: {import_stats.edges_skipped}",
            f"Errors: {import_stats.errors}",
            f"Warnings: {import_stats.warnings}",
            f"Duration: {import_stats.duration_seconds:.2f} seconds",
            "",
        ]
    )

    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))
