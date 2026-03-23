"""Pytest fixtures shared across all LitigationOS tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from litigationos.db.connection import DatabaseManager


@pytest.fixture
def tmp_db(tmp_path: Path) -> DatabaseManager:
    """Create a temporary database with schema initialized."""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(db_path)
    db.initialize()
    return db


@pytest.fixture
def db_conn(tmp_db: DatabaseManager) -> sqlite3.Connection:
    """Get a raw connection to the test database."""
    return tmp_db.connect()


@pytest.fixture
def sample_case(tmp_db: DatabaseManager) -> dict:
    """Insert a test case record and return its data."""
    cursor = tmp_db.execute(
        "INSERT INTO cases (case_number, case_type, title, status) "
        "VALUES (?, ?, ?, ?)",
        ("2025-0001-FC", "family", "Pigors v. Watson", "active"),
    )
    case_id = cursor.lastrowid
    row = tmp_db.fetchone("SELECT * FROM cases WHERE id = ?", (case_id,))
    return dict(row)


@pytest.fixture
def sample_party(tmp_db: DatabaseManager, sample_case: dict) -> list[dict]:
    """Insert petitioner + respondent party records for the sample case."""
    case_id = sample_case["id"]
    parties = [
        (case_id, "Andre Pigors", "petitioner", "individual"),
        (case_id, "Jane Watson", "respondent", "individual"),
    ]
    result = []
    for case_id, name, role, party_type in parties:
        cursor = tmp_db.execute(
            "INSERT INTO parties (case_id, name, role, party_type) VALUES (?, ?, ?, ?)",
            (case_id, name, role, party_type),
        )
        row = tmp_db.fetchone("SELECT * FROM parties WHERE id = ?", (cursor.lastrowid,))
        result.append(dict(row))
    return result


@pytest.fixture
def sample_filing(tmp_db: DatabaseManager, sample_case: dict) -> dict:
    """Insert a test filing record."""
    case_id = sample_case["id"]
    cursor = tmp_db.execute(
        "INSERT INTO filings (case_id, title, filing_type, status) VALUES (?, ?, ?, ?)",
        (case_id, "Motion to Compel Discovery", "motion", "draft"),
    )
    row = tmp_db.fetchone("SELECT * FROM filings WHERE id = ?", (cursor.lastrowid,))
    return dict(row)


@pytest.fixture
def sample_evidence(tmp_db: DatabaseManager, sample_case: dict, tmp_path: Path) -> list[dict]:
    """Insert test evidence records with dummy files on disk."""
    case_id = sample_case["id"]
    result = []
    for i, (title, desc, ftype) in enumerate([
        ("Custody Agreement", "Original custody agreement from 2020", "pdf"),
        ("Text Messages", "Screenshot of text messages from 2024-01-15", "image"),
        ("Financial Records", "Bank statements Jan-Mar 2024", "document"),
    ], start=1):
        # Create a dummy file so file_path references something real
        dummy = tmp_path / f"evidence_{i}.{ftype}"
        dummy.write_text(f"dummy evidence content {i}", encoding="utf-8")
        cursor = tmp_db.execute(
            "INSERT INTO evidence (case_id, title, description, file_path, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (case_id, title, desc, str(dummy), ftype),
        )
        row = tmp_db.fetchone("SELECT * FROM evidence WHERE id = ?", (cursor.lastrowid,))
        result.append(dict(row))
    return result
