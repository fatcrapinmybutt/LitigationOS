#!/usr/bin/env python3
"""Tests for Neo4j Import Hygiene Module."""

import csv
from datetime import datetime
from pathlib import Path

import pytest

from src.neo4j_import_hygiene import (
    ImportStats,
    Neo4jImportLogger,
    Neo4jImportValidator,
    ValidationResult,
    compute_file_checksum,
    create_backup,
    create_import_manifest,
    extract_node_ids_from_csv,
    generate_import_summary,
    merge_csv_files,
    sanitize_csv_for_import,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_nodes_csv(path: Path, rows: list) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([":ID", "name:string", "age:int"])
        writer.writerows(rows)


def _write_edges_csv(path: Path, rows: list) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([":START_ID", ":END_ID", ":TYPE"])
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# ImportStats
# ---------------------------------------------------------------------------


class TestImportStats:
    def test_initial_stats(self):
        stats = ImportStats()
        assert stats.nodes_processed == 0
        assert stats.errors == 0

    def test_to_dict(self):
        stats = ImportStats(nodes_processed=10, edges_processed=20)
        d = stats.to_dict()
        assert d["nodes_processed"] == 10
        assert d["edges_processed"] == 20

    def test_duration_calculation(self):
        stats = ImportStats(
            start_time=datetime(2024, 1, 1, 12, 0, 0),
            end_time=datetime(2024, 1, 1, 12, 1, 30),
        )
        assert stats.duration_seconds == 90.0

    def test_duration_without_times(self):
        stats = ImportStats()
        assert stats.duration_seconds == 0.0


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_initial_valid(self):
        result = ValidationResult(valid=True, errors=[], warnings=[], stats={})
        assert result.valid

    def test_add_error_invalidates(self):
        result = ValidationResult(valid=True, errors=[], warnings=[], stats={})
        result.add_error("oops")
        assert not result.valid
        assert "oops" in result.errors

    def test_add_warning_keeps_valid(self):
        result = ValidationResult(valid=True, errors=[], warnings=[], stats={})
        result.add_warning("heads up")
        assert result.valid
        assert "heads up" in result.warnings


# ---------------------------------------------------------------------------
# Neo4jImportValidator — nodes
# ---------------------------------------------------------------------------


class TestNeo4jImportValidatorNodes:
    def test_valid_nodes_csv(self, tmp_path):
        csv_file = tmp_path / "nodes.csv"
        _write_nodes_csv(csv_file, [["1", "Alice", "30"], ["2", "Bob", "25"]])
        validator = Neo4jImportValidator()
        result = validator.validate_nodes_csv(csv_file)
        assert result.valid
        assert result.stats["row_count"] == 2
        assert result.stats["unique_ids"] == 2

    def test_missing_id_value(self, tmp_path):
        csv_file = tmp_path / "nodes.csv"
        _write_nodes_csv(csv_file, [["", "Alice", "30"]])
        validator = Neo4jImportValidator()
        result = validator.validate_nodes_csv(csv_file)
        assert not result.valid
        assert any("Missing :ID" in e for e in result.errors)

    def test_duplicate_id_warns(self, tmp_path):
        csv_file = tmp_path / "nodes.csv"
        _write_nodes_csv(csv_file, [["1", "Alice", "30"], ["1", "Bob", "25"]])
        validator = Neo4jImportValidator()
        result = validator.validate_nodes_csv(csv_file)
        assert any("Duplicate :ID" in w for w in result.warnings)

    def test_max_rows_limit(self, tmp_path):
        csv_file = tmp_path / "nodes.csv"
        rows = [[str(i), f"User{i}", str(i)] for i in range(1, 11)]
        _write_nodes_csv(csv_file, rows)
        validator = Neo4jImportValidator()
        result = validator.validate_nodes_csv(csv_file, max_rows=5)
        assert result.stats["row_count"] <= 5

    def test_nonexistent_file(self, tmp_path):
        validator = Neo4jImportValidator()
        result = validator.validate_nodes_csv(tmp_path / "missing.csv")
        assert not result.valid


# ---------------------------------------------------------------------------
# Neo4jImportValidator — edges
# ---------------------------------------------------------------------------


class TestNeo4jImportValidatorEdges:
    def test_valid_edges_csv(self, tmp_path):
        csv_file = tmp_path / "edges.csv"
        _write_edges_csv(csv_file, [["1", "2", "KNOWS"], ["2", "3", "LIKES"]])
        validator = Neo4jImportValidator()
        result = validator.validate_edges_csv(csv_file)
        assert result.valid
        assert result.stats["row_count"] == 2

    def test_missing_start_id_header(self, tmp_path):
        csv_file = tmp_path / "edges.csv"
        with csv_file.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([":END_ID", ":TYPE"])
            writer.writerow(["2", "KNOWS"])
        validator = Neo4jImportValidator()
        result = validator.validate_edges_csv(csv_file)
        assert not result.valid
        assert any(":START_ID" in e for e in result.errors)

    def test_invalid_node_refs_warn(self, tmp_path):
        csv_file = tmp_path / "edges.csv"
        _write_edges_csv(csv_file, [["999", "888", "KNOWS"]])
        validator = Neo4jImportValidator()
        result = validator.validate_edges_csv(csv_file, valid_node_ids={"1", "2"})
        assert any("not found in nodes" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Neo4jImportLogger
# ---------------------------------------------------------------------------


class TestNeo4jImportLogger:
    def test_creates_log_files(self, tmp_path):
        log_dir = tmp_path / "logs"
        logger = Neo4jImportLogger(log_dir)
        logger.log_event("test_event", {"key": "value"})
        assert logger.audit_log.exists()

    def test_error_event_writes_error_log(self, tmp_path):
        log_dir = tmp_path / "logs"
        logger = Neo4jImportLogger(log_dir)
        logger.log_event("critical_event", {"msg": "oops"}, level="ERROR")
        assert logger.error_log.exists()
        content = logger.error_log.read_text(encoding="utf-8")
        assert "critical_event" in content

    def test_log_validation_result(self, tmp_path):
        log_dir = tmp_path / "logs"
        logger = Neo4jImportLogger(log_dir)
        result = ValidationResult(
            valid=True, errors=[], warnings=["heads up"], stats={"type": "nodes"}
        )
        logger.log_validation(result)
        content = logger.audit_log.read_text(encoding="utf-8")
        assert "validation" in content

    def test_log_import_stats(self, tmp_path):
        log_dir = tmp_path / "logs"
        logger = Neo4jImportLogger(log_dir)
        stats = ImportStats(nodes_processed=5, edges_processed=10)
        logger.log_import_stats(stats)
        content = logger.audit_log.read_text(encoding="utf-8")
        assert "import_stats" in content


# ---------------------------------------------------------------------------
# Standalone utilities
# ---------------------------------------------------------------------------


class TestComputeFileChecksum:
    def test_sha256_checksum(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_bytes(b"hello world")
        checksum = compute_file_checksum(f)
        assert len(checksum) == 64  # SHA-256 hex digest

    def test_md5_checksum(self, tmp_path):
        f = tmp_path / "data.csv"
        f.write_bytes(b"hello")
        checksum = compute_file_checksum(f, algorithm="md5")
        assert len(checksum) == 32  # MD5 hex digest

    def test_same_content_same_checksum(self, tmp_path):
        f1 = tmp_path / "a.csv"
        f2 = tmp_path / "b.csv"
        f1.write_bytes(b"same")
        f2.write_bytes(b"same")
        assert compute_file_checksum(f1) == compute_file_checksum(f2)


class TestCreateImportManifest:
    def test_manifest_created(self, tmp_path):
        nodes = tmp_path / "nodes.csv"
        edges = tmp_path / "edges.csv"
        nodes.write_bytes(b":ID,name\n1,Alice\n")
        edges.write_bytes(b":START_ID,:END_ID,:TYPE\n1,2,KNOWS\n")
        manifest_path = tmp_path / "manifest.json"
        create_import_manifest(nodes, edges, manifest_path)
        assert manifest_path.exists()
        import json

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert "files" in manifest
        assert "nodes" in manifest["files"]
        assert "checksum" in manifest["files"]["nodes"]


class TestSanitizeCSVForImport:
    def test_sanitizes_injection(self, tmp_path):
        infile = tmp_path / "in.csv"
        outfile = tmp_path / "out.csv"
        with infile.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([":ID", "formula"])
            writer.writerow(["1", "=CMD|evil"])
        count = sanitize_csv_for_import(infile, outfile)
        assert count == 2  # header + data row


class TestMergeCSVFiles:
    def test_merge_two_files(self, tmp_path):
        f1 = tmp_path / "a.csv"
        f2 = tmp_path / "b.csv"
        _write_nodes_csv(f1, [["1", "Alice", "30"]])
        _write_nodes_csv(f2, [["2", "Bob", "25"]])
        out = tmp_path / "merged.csv"
        total_rows, files_merged = merge_csv_files([f1, f2], out)
        assert files_merged == 2
        assert total_rows >= 3  # 1 header + 2 data rows


class TestCreateBackup:
    def test_backup_created(self, tmp_path):
        source = tmp_path / "nodes.csv"
        source.write_bytes(b"data")
        backup_dir = tmp_path / "backups"
        backup_path = create_backup(source, backup_dir)
        assert backup_path.exists()
        assert backup_dir.exists()
        assert backup_path.read_bytes() == b"data"


class TestExtractNodeIdsFromCSV:
    def test_extracts_ids(self, tmp_path):
        csv_file = tmp_path / "nodes.csv"
        _write_nodes_csv(csv_file, [["1", "Alice", "30"], ["2", "Bob", "25"]])
        ids = extract_node_ids_from_csv(csv_file)
        assert ids == {"1", "2"}

    def test_empty_csv_returns_empty_set(self, tmp_path):
        csv_file = tmp_path / "nodes.csv"
        _write_nodes_csv(csv_file, [])
        ids = extract_node_ids_from_csv(csv_file)
        assert ids == set()


class TestGenerateImportSummary:
    def test_summary_written(self, tmp_path):
        result = ValidationResult(
            valid=True, errors=[], warnings=["warn1"], stats={"type": "nodes", "path": "test.csv"}
        )
        stats = ImportStats(nodes_processed=10, edges_processed=5)
        output = tmp_path / "summary.txt"
        generate_import_summary([result], stats, output)
        content = output.read_text(encoding="utf-8")
        assert "Neo4j Import Summary" in content
        assert "nodes_processed" in content.lower() or "Nodes processed" in content
