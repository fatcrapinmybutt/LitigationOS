#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Neo4j Import Sanitization Utilities
=====================================

Comprehensive input validation and sanitization for Neo4j CSV import operations.
Prevents path traversal, CSV injection, and other security vulnerabilities.

Features:
- Path traversal prevention
- Filename sanitization (Windows/Unix compatibility)
- CSV injection prevention
- Neo4j CSV header validation
- Size limits and resource management
- Data quality checks
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Security constants
MAX_PATH_LENGTH = 4096
MAX_FILENAME_LENGTH = 255
MAX_CSV_CELL_LENGTH = 32768  # 32KB per cell
MAX_FILE_SIZE_MB = 1024  # 1GB default limit
BLOCKED_PATH_PATTERNS = [
    r"\.\.",  # Parent directory traversal
    r"~",  # Home directory expansion
    r"\$",  # Environment variable expansion
    r"//",  # Double slashes (potential UNC paths)
    r"\\\\",  # Double backslashes
]

# CSV injection prevention
CSV_INJECTION_PREFIXES = ["=", "+", "-", "@", "\t", "\r"]

# Neo4j reserved CSV headers
NEO4J_NODE_HEADERS = {":ID", ":LABEL", ":START_ID", ":END_ID", ":TYPE"}
NEO4J_PROPERTY_SUFFIXES = {
    ":string",
    ":int",
    ":long",
    ":float",
    ":double",
    ":boolean",
    ":byte",
    ":short",
    ":char",
    ":string[]",
    ":int[]",
    ":long[]",
    ":float[]",
    ":double[]",
    ":boolean[]",
}

# Dangerous characters for filenames
DANGEROUS_FILENAME_CHARS = r'[<>:"|?*\x00-\x1f]'

# Valid file extensions for Neo4j imports
VALID_GRAPH_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".json",
    ".jsonl",
    ".ndjson",
    ".graphml",
    ".gexf",
    ".gml",
    ".dot",
    ".cypher",
}


class SanitizationError(Exception):
    """Base exception for sanitization errors."""


class PathTraversalError(SanitizationError):
    """Raised when path traversal is detected."""


class InvalidFilenameError(SanitizationError):
    """Raised when filename contains invalid characters."""


class CSVInjectionError(SanitizationError):
    """Raised when CSV injection is detected."""


class InvalidHeaderError(SanitizationError):
    """Raised when CSV headers are invalid for Neo4j."""


class FileSizeError(SanitizationError):
    """Raised when file size exceeds limits."""


def sanitize_path(path: "str | Path", base_dir: "Optional[str | Path]" = None) -> Path:
    """Sanitize and validate a file path to prevent path traversal attacks.

    Args:
        path: The path to sanitize
        base_dir: Optional base directory to restrict access to

    Returns:
        Sanitized Path object

    Raises:
        PathTraversalError: If path traversal is detected
        SanitizationError: If path is invalid
    """
    if not path:
        raise SanitizationError("Path cannot be empty")

    path_str = str(path)

    if len(path_str) > MAX_PATH_LENGTH:
        raise SanitizationError(f"Path exceeds maximum length of {MAX_PATH_LENGTH}")

    for pattern in BLOCKED_PATH_PATTERNS:
        if re.search(pattern, path_str):
            raise PathTraversalError(f"Path contains blocked pattern: {pattern}")

    try:
        resolved_path = Path(path).resolve()
    except (OSError, ValueError) as e:
        raise SanitizationError(f"Invalid path: {e}")

    if base_dir:
        try:
            base_resolved = Path(base_dir).resolve()
            try:
                resolved_path.relative_to(base_resolved)
            except ValueError:
                raise PathTraversalError(
                    f"Path {resolved_path} is outside base directory {base_resolved}"
                )
        except (OSError, ValueError) as e:
            raise SanitizationError(f"Invalid base directory: {e}")

    return resolved_path


def sanitize_filename(filename: str, allow_unicode: bool = True) -> str:
    """Sanitize a filename for cross-platform compatibility.

    Args:
        filename: The filename to sanitize
        allow_unicode: Whether to allow Unicode characters

    Returns:
        Sanitized filename

    Raises:
        InvalidFilenameError: If filename is invalid or too long
    """
    if not filename:
        raise InvalidFilenameError("Filename cannot be empty")

    if len(filename) > MAX_FILENAME_LENGTH:
        raise InvalidFilenameError(f"Filename exceeds maximum length of {MAX_FILENAME_LENGTH}")

    sanitized = re.sub(DANGEROUS_FILENAME_CHARS, "_", filename)
    sanitized = sanitized.strip(". ")

    if not allow_unicode:
        sanitized = sanitized.encode("ascii", errors="replace").decode("ascii")

    if not sanitized or sanitized in {".", ".."}:
        raise InvalidFilenameError(f"Invalid filename after sanitization: {filename}")

    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    name_without_ext = sanitized.split(".")[0].upper()
    if name_without_ext in reserved_names:
        sanitized = f"_{sanitized}"

    return sanitized


def prevent_csv_injection(value: str, mode: str = "escape") -> str:
    """Prevent CSV injection attacks by sanitizing cell values.

    Args:
        value: The cell value to sanitize
        mode: Sanitization mode - "escape" (add quotes) or "strip" (remove prefix)

    Returns:
        Sanitized value

    Raises:
        CSVInjectionError: If value contains injection attempt and mode is "strict"
    """
    if not value:
        return value

    if value[0] in CSV_INJECTION_PREFIXES:
        if mode == "escape":
            escaped = value.replace('"', '""')
            return f'"{escaped}"'
        elif mode == "strip":
            return value.lstrip("".join(CSV_INJECTION_PREFIXES))
        elif mode == "strict":
            raise CSVInjectionError(f"CSV injection detected: value starts with {value[0]}")

    return value


def validate_neo4j_header(header: str) -> Tuple[str, Optional[str]]:
    """Validate and parse a Neo4j CSV header.

    Args:
        header: The header string to validate (e.g., "name:string", ":ID")

    Returns:
        Tuple of (property_name, type_suffix)

    Raises:
        InvalidHeaderError: If header format is invalid
    """
    if not header:
        raise InvalidHeaderError("Header cannot be empty")

    if header in NEO4J_NODE_HEADERS:
        return header, None

    parts = header.split(":")
    if len(parts) == 1:
        return parts[0], None
    elif len(parts) == 2:
        prop_name, type_suffix = parts
        full_suffix = f":{type_suffix}"
        if full_suffix not in NEO4J_PROPERTY_SUFFIXES:
            raise InvalidHeaderError(
                f"Invalid Neo4j type suffix: {full_suffix}. "
                f"Valid suffixes: {', '.join(sorted(NEO4J_PROPERTY_SUFFIXES))}"
            )
        return prop_name, full_suffix
    else:
        raise InvalidHeaderError(
            f"Invalid header format: {header}. Expected 'property' or 'property:type'"
        )


def validate_csv_headers(headers: List[str], require_id: bool = True) -> Dict[str, Any]:
    """Validate a list of Neo4j CSV headers.

    Args:
        headers: List of header strings
        require_id: Whether to require an :ID column

    Returns:
        Dictionary with validation results and parsed headers

    Raises:
        InvalidHeaderError: If headers are invalid
    """
    if not headers:
        raise InvalidHeaderError("Headers list cannot be empty")

    parsed = []
    special_headers = set()
    property_names = set()

    for h in headers:
        prop_name, type_suffix = validate_neo4j_header(h)
        parsed.append({"header": h, "property": prop_name, "type": type_suffix})

        if h in NEO4J_NODE_HEADERS:
            special_headers.add(h)
        else:
            if prop_name in property_names:
                raise InvalidHeaderError(f"Duplicate property name: {prop_name}")
            property_names.add(prop_name)

    if require_id and ":ID" not in special_headers:
        raise InvalidHeaderError("Missing required :ID header for node CSV")

    return {
        "valid": True,
        "headers": parsed,
        "special_headers": list(special_headers),
        "property_count": len(property_names),
    }


def validate_file_size(path: Path, max_size_mb: int = MAX_FILE_SIZE_MB) -> bool:
    """Validate that a file size is within acceptable limits.

    Args:
        path: Path to the file
        max_size_mb: Maximum size in megabytes

    Returns:
        True if file size is acceptable

    Raises:
        FileSizeError: If file exceeds size limit
    """
    if not path.exists():
        raise SanitizationError(f"File does not exist: {path}")

    size_bytes = path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    if size_mb > max_size_mb:
        raise FileSizeError(f"File size ({size_mb:.2f} MB) exceeds limit of {max_size_mb} MB")

    return True


def validate_graph_extension(filename: str) -> bool:
    """Validate that a file has a recognized graph data extension.

    Args:
        filename: The filename to check

    Returns:
        True if extension is valid for graph data
    """
    ext = Path(filename).suffix.lower()
    return ext in VALID_GRAPH_EXTENSIONS


def safe_read_text(path: Path, max_size_mb: int = MAX_FILE_SIZE_MB, encoding: str = "utf-8") -> str:
    """Safely read a text file with size validation.

    Args:
        path: Path to the file
        max_size_mb: Maximum size in megabytes
        encoding: Text encoding to use

    Returns:
        File contents as string

    Raises:
        FileSizeError: If file exceeds size limit
        SanitizationError: If file cannot be read
    """
    validate_file_size(path, max_size_mb)

    try:
        return path.read_text(encoding=encoding, errors="replace")
    except Exception as e:
        raise SanitizationError(f"Failed to read file {path}: {e}")


def safe_read_bytes(path: Path, max_size_mb: int = MAX_FILE_SIZE_MB, max_bytes: Optional[int] = None) -> bytes:
    """Safely read a file as bytes with size validation.

    Args:
        path: Path to the file
        max_size_mb: Maximum size in megabytes
        max_bytes: Maximum bytes to read (None = read all)

    Returns:
        File contents as bytes

    Raises:
        FileSizeError: If file exceeds size limit
        SanitizationError: If file cannot be read
    """
    validate_file_size(path, max_size_mb)

    try:
        with path.open("rb") as f:
            if max_bytes:
                return f.read(max_bytes)
            return f.read()
    except Exception as e:
        raise SanitizationError(f"Failed to read file {path}: {e}")


def sanitize_csv_row(row: List[str], injection_mode: str = "escape") -> List[str]:
    """Sanitize all cells in a CSV row.

    Args:
        row: List of cell values
        injection_mode: Mode for CSV injection prevention

    Returns:
        Sanitized row
    """
    return [prevent_csv_injection(cell, mode=injection_mode) for cell in row]


def validate_directory_structure(base_dir: Path, required_subdirs: List[str]) -> Dict[str, bool]:
    """Validate that a directory has the required structure.

    Args:
        base_dir: Base directory to check
        required_subdirs: List of required subdirectory names

    Returns:
        Dictionary mapping subdirectory names to existence status
    """
    if not base_dir.exists():
        raise SanitizationError(f"Base directory does not exist: {base_dir}")

    if not base_dir.is_dir():
        raise SanitizationError(f"Path is not a directory: {base_dir}")

    status = {}
    for subdir in required_subdirs:
        subdir_path = base_dir / subdir
        status[subdir] = subdir_path.exists() and subdir_path.is_dir()

    return status
