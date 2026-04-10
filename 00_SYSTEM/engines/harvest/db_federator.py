"""
db_federator.py — Cross-database comparison and federation engine.

Compares external SQLite databases against litigation_context.db,
identifies unique rows, and merges them into the central hub.
Handles: ATTACH DATABASE, schema introspection, diff analysis,
selective row extraction with dedup.

Usage:
    from engines.harvest.db_federator import federate_database
    stats = federate_database("G:\\litigation_context(1).db", central_db_path)
"""

import sqlite3
import os
import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime

try:
    from engines.harvest.config import DRIVES as DRIVE_MAP
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    try:
        from engines.harvest.config import DRIVES as DRIVE_MAP
    except ImportError:
        sys.path.insert(0, str(Path(__file__).parent))
        from config import DRIVES as DRIVE_MAP


# Tables we want to federate FROM external DBs INTO central
PRIORITY_TABLES = [
    'evidence_quotes',
    'timeline_events',
    'impeachment_matrix',
    'contradiction_map',
    'judicial_violations',
    'authority_chains_v2',
    'police_reports',
    'berry_mcneill_intelligence',
    'master_citations',
    'documents',
    'file_inventory',
]

# Tables to skip (internal, system, or FTS shadow tables)
SKIP_TABLES = {
    'sqlite_stat1', 'sqlite_stat4', 'sqlite_sequence',
    'schema_version', 'migration_log',
}

# FTS5 shadow table suffixes
FTS_SUFFIXES = ('_fts', '_content', '_docsize', '_data', '_idx', '_config')


class FederationResult:
    """Results from a database federation operation."""
    __slots__ = (
        'source_path', 'source_tables', 'central_tables',
        'unique_tables', 'common_tables', 'rows_imported',
        'rows_skipped_dedup', 'errors', 'duration_secs',
        'table_details',
    )

    def __init__(self, source_path):
        self.source_path = source_path
        self.source_tables = []
        self.central_tables = []
        self.unique_tables = []
        self.common_tables = []
        self.rows_imported = 0
        self.rows_skipped_dedup = 0
        self.errors = []
        self.duration_secs = 0.0
        self.table_details = {}


def _get_journal_mode(db_path):
    """Determine safe journal mode based on drive filesystem."""
    drive = str(db_path)[:2].upper()
    drive_info = DRIVE_MAP.get(drive.rstrip(':'), {})
    fs_type = drive_info.get('filesystem', 'NTFS')
    if fs_type == 'exFAT':
        return 'DELETE'
    return 'WAL'


def _get_tables(conn, prefix=''):
    """Get all user tables from a connection, with optional schema prefix."""
    if prefix:
        sql = f"SELECT name FROM {prefix}.sqlite_master WHERE type='table' ORDER BY name"
    else:
        sql = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    rows = conn.execute(sql).fetchall()
    tables = []
    for (name,) in rows:
        if name in SKIP_TABLES:
            continue
        if any(name.endswith(s) for s in FTS_SUFFIXES):
            continue
        if name.startswith('sqlite_'):
            continue
        tables.append(name)
    return tables


def _get_columns(conn, table, prefix=''):
    """Get column info for a table."""
    if prefix:
        sql = f"PRAGMA {prefix}.table_info({table})"
    else:
        sql = f"PRAGMA table_info({table})"
    rows = conn.execute(sql).fetchall()
    return [(r[1], r[2]) for r in rows]  # (name, type) tuples


def _get_row_count(conn, table, prefix=''):
    """Get row count for a table."""
    tbl = f"{prefix}.{table}" if prefix else table
    try:
        row = conn.execute(f"SELECT COUNT(*) FROM [{tbl}]").fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        return -1


def _compute_row_hash(row):
    """Compute a content hash for a row tuple for dedup purposes."""
    content = '|'.join(str(v) if v is not None else '' for v in row)
    return hashlib.md5(content.encode('utf-8', errors='replace')).hexdigest()


def introspect_database(db_path):
    """
    Introspect a SQLite database: tables, columns, row counts.
    Returns dict of {table_name: {columns: [...], row_count: N}}
    """
    db_path = str(db_path)
    if not os.path.isfile(db_path):
        return {}

    journal = _get_journal_mode(db_path)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute(f"PRAGMA journal_mode={journal}")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")

    result = {}
    try:
        tables = _get_tables(conn)
        for table in tables:
            cols = _get_columns(conn, table)
            count = _get_row_count(conn, table)
            result[table] = {
                'columns': cols,
                'row_count': count,
            }
    finally:
        conn.close()
    return result


def compare_schemas(source_info, central_info):
    """
    Compare two database schemas.
    Returns: unique_to_source, unique_to_central, common, compatible_common
    """
    src_tables = set(source_info.keys())
    cen_tables = set(central_info.keys())

    unique_to_source = src_tables - cen_tables
    unique_to_central = cen_tables - src_tables
    common = src_tables & cen_tables

    compatible = []
    for table in common:
        src_cols = {c[0] for c in source_info[table]['columns']}
        cen_cols = {c[0] for c in central_info[table]['columns']}
        shared_cols = src_cols & cen_cols
        if shared_cols:
            compatible.append((table, list(shared_cols)))

    return unique_to_source, unique_to_central, common, compatible


def federate_database(source_path, central_path, tables=None, dry_run=False,
                      batch_size=500, verbose=False):
    """
    Federate an external database into the central litigation_context.db.

    Args:
        source_path: Path to external SQLite database
        central_path: Path to central litigation_context.db
        tables: List of specific tables to federate (None = auto-detect priority)
        dry_run: If True, report what would be done without writing
        batch_size: Number of rows per INSERT batch
        verbose: Print progress

    Returns:
        FederationResult with detailed statistics
    """
    start = datetime.now()
    result = FederationResult(str(source_path))

    source_path = str(source_path)
    central_path = str(central_path)

    if not os.path.isfile(source_path):
        result.errors.append(f"Source DB not found: {source_path}")
        return result

    if not os.path.isfile(central_path):
        result.errors.append(f"Central DB not found: {central_path}")
        return result

    # Introspect both databases
    src_info = introspect_database(source_path)
    cen_info = introspect_database(central_path)

    result.source_tables = list(src_info.keys())
    result.central_tables = list(cen_info.keys())

    unique_src, unique_cen, common, compatible = compare_schemas(src_info, cen_info)
    result.unique_tables = list(unique_src)
    result.common_tables = list(common)

    # Determine which tables to federate
    if tables:
        target_tables = [t for t in tables if t in src_info]
    else:
        target_tables = [t for t in PRIORITY_TABLES if t in src_info]
        # Also include unique tables with significant row counts
        for t in unique_src:
            if src_info[t]['row_count'] > 0:
                target_tables.append(t)

    if verbose:
        print(f"Source: {len(src_info)} tables, Central: {len(cen_info)} tables",
              file=sys.stderr)
        print(f"Unique to source: {len(unique_src)}, Common: {len(common)}",
              file=sys.stderr)
        print(f"Target tables: {len(target_tables)}", file=sys.stderr)

    if dry_run:
        for table in target_tables:
            info = src_info.get(table, {})
            result.table_details[table] = {
                'source_rows': info.get('row_count', 0),
                'action': 'would_import',
                'mode': 'merge' if table in common else 'create',
            }
        result.duration_secs = (datetime.now() - start).total_seconds()
        return result

    # Open central DB for writing
    cen_conn = sqlite3.connect(central_path, timeout=60)
    cen_conn.execute("PRAGMA journal_mode=WAL")
    cen_conn.execute("PRAGMA busy_timeout=60000")
    cen_conn.execute("PRAGMA cache_size=-32000")
    cen_conn.execute("PRAGMA temp_store=MEMORY")
    cen_conn.execute("PRAGMA synchronous=NORMAL")

    # ATTACH source database as read-only
    src_journal = _get_journal_mode(source_path)
    try:
        cen_conn.execute(f"ATTACH DATABASE ? AS source", (source_path,))
        if src_journal == 'DELETE':
            cen_conn.execute("PRAGMA source.journal_mode=DELETE")
    except sqlite3.OperationalError as e:
        result.errors.append(f"ATTACH failed: {e}")
        cen_conn.close()
        result.duration_secs = (datetime.now() - start).total_seconds()
        return result

    try:
        for table in target_tables:
            try:
                detail = _federate_table(
                    cen_conn, table,
                    table in common,
                    src_info.get(table, {}),
                    cen_info.get(table, {}),
                    batch_size, verbose
                )
                result.table_details[table] = detail
                result.rows_imported += detail.get('imported', 0)
                result.rows_skipped_dedup += detail.get('skipped_dedup', 0)
            except Exception as e:
                result.errors.append(f"Table {table}: {e}")
                if verbose:
                    print(f"  ERROR on {table}: {e}", file=sys.stderr)

        cen_conn.commit()

    finally:
        try:
            cen_conn.execute("DETACH DATABASE source")
        except Exception:
            pass
        cen_conn.close()

    result.duration_secs = (datetime.now() - start).total_seconds()
    return result


def _federate_table(conn, table, exists_in_central, src_info, cen_info,
                    batch_size, verbose):
    """Federate a single table from source into central."""
    detail = {
        'source_rows': src_info.get('row_count', 0),
        'imported': 0,
        'skipped_dedup': 0,
        'mode': 'merge' if exists_in_central else 'create',
    }

    src_cols = _get_columns(conn, table, 'source')
    src_col_names = [c[0] for c in src_cols]

    if not exists_in_central:
        # Create table in central with same schema
        col_defs = ', '.join(
            f'[{c[0]}] {c[1]}' for c in src_cols
        )
        conn.execute(f"CREATE TABLE IF NOT EXISTS [{table}] ({col_defs})")
        target_cols = src_col_names
    else:
        # Find shared columns
        cen_cols = _get_columns(conn, table, 'main')
        cen_col_names = {c[0] for c in cen_cols}
        target_cols = [c for c in src_col_names if c in cen_col_names]
        if not target_cols:
            detail['mode'] = 'skip_no_shared_columns'
            return detail

    col_list = ', '.join(f'[{c}]' for c in target_cols)
    placeholders = ', '.join('?' * len(target_cols))

    # Build dedup hash set from existing central rows
    existing_hashes = set()
    if exists_in_central:
        try:
            cursor = conn.execute(
                f"SELECT {col_list} FROM main.[{table}] LIMIT 50000"
            )
            for row in cursor:
                existing_hashes.add(_compute_row_hash(row))
        except sqlite3.OperationalError:
            pass

    # Read source rows and insert new ones
    try:
        cursor = conn.execute(f"SELECT {col_list} FROM source.[{table}]")
    except sqlite3.OperationalError as e:
        detail['error'] = str(e)
        return detail

    batch = []
    for row in cursor:
        row_hash = _compute_row_hash(row)
        if row_hash in existing_hashes:
            detail['skipped_dedup'] += 1
            continue

        existing_hashes.add(row_hash)
        batch.append(row)

        if len(batch) >= batch_size:
            conn.executemany(
                f"INSERT OR IGNORE INTO main.[{table}] ({col_list}) VALUES ({placeholders})",
                batch
            )
            detail['imported'] += len(batch)
            batch = []

    if batch:
        conn.executemany(
            f"INSERT OR IGNORE INTO main.[{table}] ({col_list}) VALUES ({placeholders})",
            batch
        )
        detail['imported'] += len(batch)

    if verbose:
        mode = detail['mode']
        imp = detail['imported']
        skip = detail['skipped_dedup']
        print(f"  {table}: {mode} — imported {imp}, dedup-skipped {skip}",
              file=sys.stderr)

    return detail


def generate_federation_report(result):
    """Generate a markdown report from federation results."""
    lines = [
        f"# Database Federation Report",
        f"",
        f"**Source:** `{result.source_path}`",
        f"**Duration:** {result.duration_secs:.1f}s",
        f"**Total Imported:** {result.rows_imported:,} rows",
        f"**Dedup Skipped:** {result.rows_skipped_dedup:,} rows",
        f"",
        f"## Schema Comparison",
        f"- Source tables: {len(result.source_tables)}",
        f"- Central tables: {len(result.central_tables)}",
        f"- Unique to source: {len(result.unique_tables)}",
        f"- Common tables: {len(result.common_tables)}",
        f"",
    ]

    if result.unique_tables:
        lines.append("### Tables Unique to Source")
        for t in sorted(result.unique_tables):
            lines.append(f"- `{t}`")
        lines.append("")

    if result.table_details:
        lines.append("## Table Details")
        lines.append("")
        lines.append("| Table | Mode | Source Rows | Imported | Dedup Skip |")
        lines.append("|-------|------|------------|----------|------------|")
        for table, detail in sorted(result.table_details.items()):
            mode = detail.get('mode', '?')
            src = detail.get('source_rows', 0)
            imp = detail.get('imported', 0)
            skip = detail.get('skipped_dedup', 0)
            lines.append(f"| {table} | {mode} | {src:,} | {imp:,} | {skip:,} |")
        lines.append("")

    if result.errors:
        lines.append("## Errors")
        for err in result.errors:
            lines.append(f"- {err}")
        lines.append("")

    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        description='Database Federation Engine — merge external DBs into central'
    )
    parser.add_argument('source', help='Path to external SQLite database')
    parser.add_argument('--central', default=None,
                        help='Path to central DB (default: auto-detect)')
    parser.add_argument('--tables', nargs='+', default=None,
                        help='Specific tables to federate')
    parser.add_argument('--dry-run', action='store_true',
                        help='Report only, no writes')
    parser.add_argument('--batch-size', type=int, default=500)
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--report', default=None,
                        help='Write markdown report to this path')

    args = parser.parse_args()

    # Auto-detect central DB
    central = args.central
    if not central:
        candidates = [
            Path(__file__).parent.parent.parent.parent / 'litigation_context.db',
            Path('C:/Users/andre/LitigationOS/litigation_context.db'),
        ]
        for c in candidates:
            if c.is_file():
                central = str(c)
                break
    if not central:
        print("ERROR: Could not find central DB. Use --central.", file=sys.stderr)
        sys.exit(1)

    result = federate_database(
        args.source, central,
        tables=args.tables,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        verbose=args.verbose
    )

    report = generate_federation_report(result)
    print(report)

    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(report, encoding='utf-8')
        print(f"\nReport saved to: {args.report}", file=sys.stderr)

    sys.exit(0 if not result.errors else 1)
