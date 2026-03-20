"""File hashing utilities — SHA-256 integrity verification.

Provides functions for computing file hashes to ensure evidence
integrity and detect file modifications.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(file_path: str | Path, chunk_size: int = 8192) -> str:
    """Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file
        chunk_size: Read buffer size in bytes

    Returns:
        Hex-encoded SHA-256 hash string
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def sha256_string(text: str) -> str:
    """Compute the SHA-256 hash of a string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_file(file_path: str | Path, expected_hash: str) -> bool:
    """Verify a file's integrity against an expected SHA-256 hash.

    Args:
        file_path: Path to the file
        expected_hash: Expected hex-encoded SHA-256 hash

    Returns:
        True if hash matches, False otherwise
    """
    return sha256_file(file_path) == expected_hash.lower()
