"""
Test suite for shared hashing utilities.
"""

import tempfile
from pathlib import Path

import pytest

from src.utils.hashing import hash_file, hash_file_chunked


def test_hash_file_simple():
    """Test basic hash_file functionality."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        result = hash_file(temp_path)
        # SHA-256 of "test content"
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        assert result == expected
    finally:
        temp_path.unlink()


def test_hash_file_chunked_simple():
    """Test basic hash_file_chunked functionality."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)
    
    try:
        result = hash_file_chunked(temp_path)
        # SHA-256 of "test content"
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        assert result == expected
    finally:
        temp_path.unlink()


def test_hash_file_consistency():
    """Test that hash_file and hash_file_chunked produce same results."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content for consistency check")
        temp_path = Path(f.name)
    
    try:
        result1 = hash_file(temp_path)
        result2 = hash_file_chunked(temp_path)
        assert result1 == result2
    finally:
        temp_path.unlink()


def test_hash_file_large_content():
    """Test hash_file_chunked with content larger than chunk size."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        # Write 200KB of data
        data = b"x" * (200 * 1024)
        f.write(data)
        temp_path = Path(f.name)
    
    try:
        result = hash_file_chunked(temp_path, chunk_size=65536)
        assert len(result) == 64  # SHA-256 produces 64 hex characters
        assert isinstance(result, str)
    finally:
        temp_path.unlink()


def test_hash_file_empty():
    """Test hashing an empty file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        temp_path = Path(f.name)
    
    try:
        result = hash_file(temp_path)
        # SHA-256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert result == expected
    finally:
        temp_path.unlink()


def test_hash_file_nonexistent():
    """Test that hashing a nonexistent file raises appropriate error."""
    with pytest.raises(FileNotFoundError):
        hash_file(Path("/nonexistent/file/path.txt"))


def test_hash_file_chunked_nonexistent():
    """Test that chunked hashing a nonexistent file raises appropriate error."""
    with pytest.raises(FileNotFoundError):
        hash_file_chunked(Path("/nonexistent/file/path.txt"))
