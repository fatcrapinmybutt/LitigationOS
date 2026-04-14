#!/usr/bin/env python3
"""Tests for Neo4j Import Sanitization Utilities."""

import tempfile
from pathlib import Path

import pytest

from src.neo4j_sanitizer import (
    CSVInjectionError,
    FileSizeError,
    InvalidFilenameError,
    InvalidHeaderError,
    PathTraversalError,
    SanitizationError,
    prevent_csv_injection,
    safe_read_bytes,
    safe_read_text,
    sanitize_csv_row,
    sanitize_filename,
    sanitize_path,
    validate_csv_headers,
    validate_directory_structure,
    validate_file_size,
    validate_graph_extension,
    validate_neo4j_header,
)


class TestSanitizePath:
    def test_valid_path(self):
        path = sanitize_path("test.csv")
        assert isinstance(path, Path)

    def test_empty_path(self):
        with pytest.raises(SanitizationError, match="cannot be empty"):
            sanitize_path("")

    def test_parent_directory_traversal(self):
        with pytest.raises(PathTraversalError, match="blocked pattern"):
            sanitize_path("../etc/passwd")

    def test_absolute_path(self, tmp_path):
        test_file = tmp_path / "test.csv"
        test_file.touch()
        path = sanitize_path(str(test_file))
        assert path.exists()

    def test_path_with_base_dir(self, tmp_path):
        test_file = tmp_path / "test.csv"
        test_file.touch()
        path = sanitize_path(test_file, base_dir=tmp_path)
        assert path.exists()

    def test_path_outside_base_dir(self, tmp_path):
        base = tmp_path / "subdir"
        base.mkdir()
        with pytest.raises(PathTraversalError, match="outside base directory"):
            sanitize_path(str(tmp_path), base_dir=base)

    def test_max_path_length(self):
        long_path = "a" * 5000
        with pytest.raises(SanitizationError, match="exceeds maximum length"):
            sanitize_path(long_path)

    def test_tilde_blocked(self):
        with pytest.raises(PathTraversalError, match="blocked pattern"):
            sanitize_path("~/private/data")

    def test_double_slash_blocked(self):
        with pytest.raises(PathTraversalError, match="blocked pattern"):
            sanitize_path("//etc/passwd")


class TestSanitizeFilename:
    def test_valid_filename(self):
        result = sanitize_filename("nodes.csv")
        assert result == "nodes.csv"

    def test_empty_filename(self):
        with pytest.raises(InvalidFilenameError, match="cannot be empty"):
            sanitize_filename("")

    def test_dangerous_chars_replaced(self):
        result = sanitize_filename("file<>name.csv")
        assert "<" not in result
        assert ">" not in result

    def test_long_filename(self):
        long_name = "a" * 300 + ".csv"
        with pytest.raises(InvalidFilenameError, match="exceeds maximum length"):
            sanitize_filename(long_name)

    def test_reserved_windows_names(self):
        result = sanitize_filename("CON.csv")
        assert result.startswith("_")

    def test_unicode_allowed_by_default(self):
        result = sanitize_filename("données.csv")
        assert result == "données.csv"


class TestPreventCSVInjection:
    def test_safe_value(self):
        result = prevent_csv_injection("Hello, World!")
        assert result == "Hello, World!"

    def test_equals_prefix_escape(self):
        result = prevent_csv_injection("=CMD|' /C calc'!A0")
        assert result.startswith('"')

    def test_plus_prefix_escape(self):
        result = prevent_csv_injection("+1234567890")
        assert result.startswith('"')

    def test_strip_mode(self):
        result = prevent_csv_injection("=dangerous", mode="strip")
        assert not result.startswith("=")

    def test_strict_mode_raises(self):
        with pytest.raises(CSVInjectionError):
            prevent_csv_injection("=dangerous", mode="strict")

    def test_empty_value(self):
        result = prevent_csv_injection("")
        assert result == ""

    def test_at_prefix(self):
        result = prevent_csv_injection("@SUM(1+1)=1+1")
        assert result.startswith('"')


class TestValidateNeo4jHeader:
    def test_special_id_header(self):
        name, suffix = validate_neo4j_header(":ID")
        assert name == ":ID"
        assert suffix is None

    def test_property_string_type(self):
        name, suffix = validate_neo4j_header("name:string")
        assert name == "name"
        assert suffix == ":string"

    def test_property_int_type(self):
        name, suffix = validate_neo4j_header("age:int")
        assert name == "age"
        assert suffix == ":int"

    def test_plain_property(self):
        name, suffix = validate_neo4j_header("description")
        assert name == "description"
        assert suffix is None

    def test_invalid_type_suffix(self):
        with pytest.raises(InvalidHeaderError, match="Invalid Neo4j type suffix"):
            validate_neo4j_header("name:invalidtype")

    def test_empty_header(self):
        with pytest.raises(InvalidHeaderError, match="cannot be empty"):
            validate_neo4j_header("")

    def test_label_header(self):
        name, suffix = validate_neo4j_header(":LABEL")
        assert name == ":LABEL"


class TestValidateCSVHeaders:
    def test_valid_node_headers(self):
        result = validate_csv_headers([":ID", "name:string", "age:int"])
        assert result["valid"] is True
        assert ":ID" in result["special_headers"]

    def test_missing_id_header(self):
        with pytest.raises(InvalidHeaderError, match="Missing required :ID"):
            validate_csv_headers(["name:string"], require_id=True)

    def test_no_id_required(self):
        result = validate_csv_headers([":START_ID", ":END_ID", ":TYPE"], require_id=False)
        assert result["valid"] is True

    def test_duplicate_property(self):
        with pytest.raises(InvalidHeaderError, match="Duplicate property"):
            validate_csv_headers([":ID", "name:string", "name:int"])

    def test_empty_headers(self):
        with pytest.raises(InvalidHeaderError, match="cannot be empty"):
            validate_csv_headers([])


class TestValidateFileSize:
    def test_small_file_passes(self, tmp_path):
        f = tmp_path / "small.csv"
        f.write_bytes(b"hello")
        assert validate_file_size(f) is True

    def test_missing_file_raises(self, tmp_path):
        missing = tmp_path / "nope.csv"
        with pytest.raises(SanitizationError, match="does not exist"):
            validate_file_size(missing)

    def test_oversized_file_raises(self, tmp_path):
        f = tmp_path / "big.csv"
        f.write_bytes(b"x" * 100)
        with pytest.raises(FileSizeError, match="exceeds limit"):
            validate_file_size(f, max_size_mb=0)  # 0 MB limit


class TestValidateGraphExtension:
    def test_csv_valid(self):
        assert validate_graph_extension("nodes.csv") is True

    def test_json_valid(self):
        assert validate_graph_extension("graph.json") is True

    def test_py_invalid(self):
        assert validate_graph_extension("script.py") is False

    def test_txt_invalid(self):
        assert validate_graph_extension("readme.txt") is False


class TestSanitizeCSVRow:
    def test_safe_row(self):
        row = ["Alice", "30", "Engineer"]
        result = sanitize_csv_row(row)
        assert result == row

    def test_injection_in_row(self):
        row = ["=CMD", "safe", "@bad"]
        result = sanitize_csv_row(row, injection_mode="escape")
        assert result[0].startswith('"')
        assert result[2].startswith('"')


class TestSafeReadText:
    def test_reads_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world", encoding="utf-8")
        content = safe_read_text(f)
        assert content == "hello world"

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(SanitizationError):
            safe_read_text(tmp_path / "missing.txt")


class TestSafeReadBytes:
    def test_reads_file(self, tmp_path):
        f = tmp_path / "test.bin"
        f.write_bytes(b"\x00\x01\x02")
        content = safe_read_bytes(f)
        assert content == b"\x00\x01\x02"

    def test_max_bytes_param(self, tmp_path):
        f = tmp_path / "test.bin"
        f.write_bytes(b"abcdef")
        content = safe_read_bytes(f, max_bytes=3)
        assert content == b"abc"


class TestValidateDirectoryStructure:
    def test_existing_subdirs(self, tmp_path):
        (tmp_path / "nodes").mkdir()
        (tmp_path / "edges").mkdir()
        result = validate_directory_structure(tmp_path, ["nodes", "edges"])
        assert result["nodes"] is True
        assert result["edges"] is True

    def test_missing_subdirs(self, tmp_path):
        result = validate_directory_structure(tmp_path, ["missing"])
        assert result["missing"] is False

    def test_invalid_base_dir(self, tmp_path):
        missing = tmp_path / "nope"
        with pytest.raises(SanitizationError, match="does not exist"):
            validate_directory_structure(missing, ["sub"])
