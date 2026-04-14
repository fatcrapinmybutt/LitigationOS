"""
Shared hashing utilities for FRED Supreme Litigation System.

Provides consistent SHA-256 hashing functionality across the codebase
for forensic compliance and file integrity verification.
"""

import hashlib
from pathlib import Path


def hash_file(path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        path: Path to the file to hash

    Returns:
        Hexadecimal string representation of the SHA-256 hash

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_file_chunked(path: Path, chunk_size: int = 65536) -> str:
    """
    Compute SHA-256 hash of a file using chunked reading.

    This is more memory-efficient for large files.

    Args:
        path: Path to the file to hash
        chunk_size: Size of chunks to read at a time (default: 64KB)

    Returns:
        Hexadecimal string representation of the SHA-256 hash

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
