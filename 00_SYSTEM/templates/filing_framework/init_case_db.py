"""
Case Database Initializer
==========================

Creates a new SQLite case database from the framework schema, pre-populates
Michigan court format specs, and configures the database for performance.

Usage (CLI)::

    python init_case_db.py \\
        --case-number "2024-001234-DC" \\
        --court "14th Judicial Circuit Court" \\
        --judge "Hon. Jane Doe" \\
        --plaintiff "John Smith" \\
        --defendant "Jane Smith" \\
        --db "my_case.db"

Usage (programmatic)::

    from init_case_db import initialize_case_db

    db_path = initialize_case_db(
        db_path="my_case.db",
        case_number="2024-001234-DC",
        court="14th Judicial Circuit Court",
        judge="Hon. Jane Doe",
        plaintiff="John Smith",
        defendant="Jane Smith",
    )
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Allow importing sibling modules when run as a script
_FRAMEWORK_DIR = Path(__file__).resolve().parent
if str(_FRAMEWORK_DIR) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_DIR))

from michigan_format_specs import specs_as_flat_rows  # noqa: E402


def _get_schema_sql() -> str:
    """Read the SQL schema from filing_db_schema.sql."""
    schema_path = _FRAMEWORK_DIR / "filing_db_schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(
            f"Schema file not found: {schema_path}\n"
            f"Ensure filing_db_schema.sql is in the same directory as this script."
        )
    return schema_path.read_text(encoding="utf-8")


def _configure_connection(conn: sqlite3.Connection) -> None:
    """Apply performance and reliability pragmas."""
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")


def _populate_format_specs(conn: sqlite3.Connection) -> int:
    """Insert pre-loaded Michigan format specs into the format_specs table.

    Returns:
        Number of rows inserted.
    """
    rows = specs_as_flat_rows()
    conn.executemany(
        "INSERT OR IGNORE INTO format_specs (court, spec_name, spec_value, authority) "
        "VALUES (:court, :spec_name, :spec_value, :authority)",
        rows,
    )
    conn.commit()
    return len(rows)


def _insert_case(
    conn: sqlite3.Connection,
    case_number: str,
    court: str,
    judge: str = "",
    division: str = "",
    lane: str = "",
) -> int:
    """Insert a case_info row and return its id."""
    cursor = conn.execute(
        "INSERT INTO case_info (case_number, court, judge, division, lane) "
        "VALUES (?, ?, ?, ?, ?)",
        (case_number, court, judge, division, lane),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def _insert_party(
    conn: sqlite3.Connection,
    case_id: int,
    name: str,
    role: str,
    side: str = "",
    pro_se: bool = False,
) -> int:
    """Insert a party row and return its id."""
    notes = "pro se" if pro_se and role == "plaintiff" else ""
    cursor = conn.execute(
        "INSERT INTO parties (case_id, name, role, side, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (case_id, name, role, side, notes),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def initialize_case_db(
    db_path: str,
    case_number: str,
    court: str,
    judge: str = "",
    plaintiff: str = "",
    defendant: str = "",
    division: str = "",
    lane: str = "",
    *,
    overwrite: bool = False,
) -> str:
    """Create and initialize a new case database.

    Args:
        db_path: Path for the new SQLite database file.
        case_number: Case number (e.g., "2024-001234-DC").
        court: Court name (e.g., "14th Judicial Circuit Court").
        judge: Assigned judge.
        plaintiff: Plaintiff's name.
        defendant: Defendant's name.
        division: Division (Family, Civil, Criminal, etc.).
        lane: User-defined lane label.
        overwrite: If True, delete existing DB before creating.

    Returns:
        Absolute path to the created database.

    Raises:
        FileExistsError: If *db_path* exists and *overwrite* is False.
    """
    db_path_abs = os.path.abspath(db_path)

    if os.path.exists(db_path_abs):
        if overwrite:
            os.remove(db_path_abs)
        else:
            raise FileExistsError(
                f"Database already exists: {db_path_abs}\n"
                f"Use --overwrite to replace it."
            )

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(db_path_abs) or ".", exist_ok=True)

    schema_sql = _get_schema_sql()

    conn = sqlite3.connect(db_path_abs)
    try:
        _configure_connection(conn)

        # Apply schema
        conn.executescript(schema_sql)

        # Populate format specs
        spec_count = _populate_format_specs(conn)

        # Insert case
        case_id: Optional[int] = None
        if case_number:
            case_id = _insert_case(conn, case_number, court, judge, division, lane)

        # Insert parties
        if case_id and plaintiff:
            _insert_party(conn, case_id, plaintiff, "plaintiff", "plaintiff_side", pro_se=True)
        if case_id and defendant:
            _insert_party(conn, case_id, defendant, "defendant", "defendant_side")
        if case_id and judge:
            _insert_party(conn, case_id, judge, "judge", "neutral")

        conn.commit()

        # Report
        print(f"Database created: {db_path_abs}")
        print(f"  Schema applied: 15 tables + 2 FTS5 indexes + triggers")
        print(f"  Format specs loaded: {spec_count} rows")
        if case_id:
            print(f"  Case inserted: {case_number} (id={case_id})")
            party_count = conn.execute(
                "SELECT COUNT(*) FROM parties WHERE case_id=?", (case_id,)
            ).fetchone()[0]
            print(f"  Parties inserted: {party_count}")
        print(f"  Pragmas: WAL mode, busy_timeout=60000, cache_size=-32000")

    finally:
        conn.close()

    return db_path_abs


def _interactive_init() -> None:
    """Run an interactive case database initialization."""
    print("=" * 50)
    print("  Case Database Initializer")
    print("=" * 50)
    print()

    db_path = input("Database path [case.db]: ").strip() or "case.db"
    case_number = input("Case number: ").strip()
    court = input("Court name: ").strip()
    judge = input("Judge: ").strip()
    plaintiff = input("Plaintiff name: ").strip()
    defendant = input("Defendant name: ").strip()
    division = input("Division (Family/Civil/Criminal) []: ").strip()
    lane = input("Lane label []: ").strip()

    overwrite = False
    if os.path.exists(db_path):
        resp = input(f"'{db_path}' exists. Overwrite? (y/n) [n]: ").strip().lower()
        overwrite = resp == "y"

    try:
        result = initialize_case_db(
            db_path=db_path,
            case_number=case_number,
            court=court,
            judge=judge,
            plaintiff=plaintiff,
            defendant=defendant,
            division=division,
            lane=lane,
            overwrite=overwrite,
        )
        print(f"\nReady: {result}")
    except (FileExistsError, FileNotFoundError) as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize a new case database from the filing framework schema.",
    )
    parser.add_argument("--db", default="case.db", help="Path for the database file")
    parser.add_argument("--case-number", default="", help="Case number")
    parser.add_argument("--court", default="", help="Court name")
    parser.add_argument("--judge", default="", help="Assigned judge")
    parser.add_argument("--plaintiff", default="", help="Plaintiff name")
    parser.add_argument("--defendant", default="", help="Defendant name")
    parser.add_argument("--division", default="", help="Division (Family/Civil/Criminal)")
    parser.add_argument("--lane", default="", help="Lane label")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing DB")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")

    args = parser.parse_args()

    if args.interactive or (not args.case_number and not args.court):
        _interactive_init()
    else:
        try:
            initialize_case_db(
                db_path=args.db,
                case_number=args.case_number,
                court=args.court,
                judge=args.judge,
                plaintiff=args.plaintiff,
                defendant=args.defendant,
                division=args.division,
                lane=args.lane,
                overwrite=args.overwrite,
            )
        except (FileExistsError, FileNotFoundError) as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
