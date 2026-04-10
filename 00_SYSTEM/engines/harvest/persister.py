"""
Harvest Engine — Multi-Table Persister v1.0
Batch INSERT into evidence_quotes, timeline_events, impeachment_matrix,
harvest_evidence, harvest_files, documents. Schema-adaptive (Rule 16).
FTS5 rebuild after bulk inserts. Dedup check before insert.
"""

import sqlite3
import hashlib
import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class PersistResult:
    """Result of a persistence operation."""
    __slots__ = (
        'evidence_inserted', 'timeline_inserted', 'impeachment_inserted',
        'files_inserted', 'documents_inserted', 'duplicates_skipped',
        'errors', 'tables_written'
    )

    def __init__(self):
        self.evidence_inserted = 0
        self.timeline_inserted = 0
        self.impeachment_inserted = 0
        self.files_inserted = 0
        self.documents_inserted = 0
        self.duplicates_skipped = 0
        self.errors = []
        self.tables_written = []


def _get_table_columns(conn: sqlite3.Connection, table: str) -> set:
    """Schema-verify per Rule 16: PRAGMA table_info before querying."""
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        return {row[1] for row in rows}
    except sqlite3.OperationalError:
        return set()


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    """Check if table exists."""
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone()
    return row[0] > 0


def _sanitize_fts5(query: str) -> str:
    """FTS5 safety per Rule 15."""
    return re.sub(r'[^\w\s*"]', ' ', query).strip()


def _check_duplicate(conn: sqlite3.Connection, quote_text: str,
                     source_file: str) -> bool:
    """Check if this quote+source combo already exists in evidence_quotes."""
    if not _table_exists(conn, 'evidence_quotes'):
        return False
    cols = _get_table_columns(conn, 'evidence_quotes')
    if 'quote_text' not in cols or 'source_file' not in cols:
        return False
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM evidence_quotes "
            "WHERE quote_text = ? AND source_file = ?",
            (quote_text, source_file)
        ).fetchone()
        return row[0] > 0
    except sqlite3.OperationalError:
        return False


def _check_harvest_duplicate(conn: sqlite3.Connection, quote_text: str,
                             source_file: str) -> bool:
    """Check if this quote+source combo already exists in harvest_evidence."""
    if not _table_exists(conn, 'harvest_evidence'):
        return False
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM harvest_evidence "
            "WHERE quote_text = ? AND source_file = ?",
            (quote_text, source_file)
        ).fetchone()
        return row[0] > 0
    except sqlite3.OperationalError:
        return False


def persist_evidence_batch(conn: sqlite3.Connection,
                           evidence_rows: List[Dict[str, Any]],
                           dedup: bool = True) -> PersistResult:
    """
    Batch-persist evidence atoms to multiple tables.

    Each row dict should contain:
        quote_text, source_file, page_number, lane, category,
        actors (list), doc_type, authorities (list), dates (list),
        impeachment_value (1-10), cross_exam_questions (list),
        harm_categories (list), sha256
    """
    result = PersistResult()
    if not evidence_rows:
        return result

    # Schema-verify target tables (Rule 16)
    eq_cols = _get_table_columns(conn, 'evidence_quotes')
    he_cols = _get_table_columns(conn, 'harvest_evidence')
    te_cols = _get_table_columns(conn, 'timeline_events')
    im_cols = _get_table_columns(conn, 'impeachment_matrix')

    has_evidence_quotes = bool(eq_cols)
    has_harvest_evidence = bool(he_cols)
    has_timeline = bool(te_cols)
    has_impeachment = bool(im_cols)

    # Prepare batch lists
    eq_batch = []
    he_batch = []
    te_batch = []
    im_batch = []

    for row in evidence_rows:
        quote = row.get('quote_text', '').strip()
        source = row.get('source_file', '').strip()
        if not quote or not source:
            continue

        # Dedup check
        if dedup:
            if _check_duplicate(conn, quote, source):
                result.duplicates_skipped += 1
                continue
            if _check_harvest_duplicate(conn, quote, source):
                result.duplicates_skipped += 1
                continue

        lane = row.get('lane', 'UNCLASSIFIED')
        category = row.get('category', 'general')
        page = row.get('page_number', 0)
        actors = ','.join(row.get('actors', []))
        doc_type = row.get('doc_type', 'unknown')
        authorities = ','.join(row.get('authorities', []))
        dates_str = ','.join(row.get('dates', []))
        sha256 = row.get('sha256', '')
        imp_value = row.get('impeachment_value', 0)
        xq = row.get('cross_exam_questions', [])
        harms = row.get('harm_categories', [])
        now = datetime.now().isoformat()

        # evidence_quotes INSERT
        if has_evidence_quotes:
            # Build adaptive INSERT based on available columns
            insert_cols = []
            insert_vals = []
            col_map = {
                'quote_text': quote,
                'source_file': source,
                'page_number': page,
                'lane': lane,
                'category': category,
                'is_duplicate': 0,
            }
            # Optional columns
            if 'actors' in eq_cols:
                col_map['actors'] = actors
            if 'doc_type' in eq_cols:
                col_map['doc_type'] = doc_type
            if 'authorities' in eq_cols:
                col_map['authorities'] = authorities
            if 'dates_found' in eq_cols:
                col_map['dates_found'] = dates_str
            if 'sha256' in eq_cols:
                col_map['sha256'] = sha256
            if 'impeachment_value' in eq_cols:
                col_map['impeachment_value'] = imp_value
            if 'created_at' in eq_cols:
                col_map['created_at'] = now
            if 'source' in eq_cols and 'source_file' not in eq_cols:
                col_map['source'] = source

            for c, v in col_map.items():
                if c in eq_cols:
                    insert_cols.append(c)
                    insert_vals.append(v)

            if insert_cols:
                eq_batch.append(tuple(insert_vals))

        # harvest_evidence INSERT
        if has_harvest_evidence:
            he_batch.append((
                quote, source, page, lane, category,
                actors, doc_type, authorities, dates_str,
                imp_value, sha256, now
            ))

        # timeline_events — only if we found dates
        if has_timeline and row.get('dates'):
            for d in row['dates'][:3]:  # max 3 events per quote
                te_entry = (d, quote[:500], source, lane, actors, now)
                te_batch.append(te_entry)

        # impeachment_matrix — only high-value items
        if has_impeachment and imp_value >= 5:
            xq_text = ' | '.join(xq[:3]) if xq else ''
            harms_text = ','.join(harms[:5]) if harms else ''
            im_batch.append((
                category, quote[:1000], source, quote[:500],
                imp_value, xq_text, lane, now
            ))

    # Execute batch INSERTs
    try:
        if eq_batch and has_evidence_quotes:
            # Build the INSERT statement from first batch
            insert_cols_list = []
            col_map_keys = [
                'quote_text', 'source_file', 'page_number', 'lane',
                'category', 'is_duplicate', 'actors', 'doc_type',
                'authorities', 'dates_found', 'sha256',
                'impeachment_value', 'created_at', 'source'
            ]
            for c in col_map_keys:
                if c in eq_cols:
                    insert_cols_list.append(c)

            if insert_cols_list:
                placeholders = ','.join(['?'] * len(insert_cols_list))
                cols_str = ','.join(insert_cols_list)
                conn.executemany(
                    f"INSERT OR IGNORE INTO evidence_quotes ({cols_str}) "
                    f"VALUES ({placeholders})",
                    eq_batch
                )
                result.evidence_inserted = len(eq_batch)
                result.tables_written.append('evidence_quotes')
    except sqlite3.OperationalError as e:
        result.errors.append(f"evidence_quotes: {e}")
        logger.error("evidence_quotes batch insert failed: %s", e)

    try:
        if he_batch and has_harvest_evidence:
            conn.executemany(
                "INSERT OR IGNORE INTO harvest_evidence "
                "(quote_text, source_file, page_number, lane, category, "
                "actors, doc_type, authorities, dates_found, "
                "impeachment_value, sha256, created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                he_batch
            )
            result.tables_written.append('harvest_evidence')
    except sqlite3.OperationalError as e:
        result.errors.append(f"harvest_evidence: {e}")
        logger.error("harvest_evidence batch insert failed: %s", e)

    try:
        if te_batch and has_timeline:
            # Adaptive columns for timeline_events
            te_cols_available = _get_table_columns(conn, 'timeline_events')
            if 'event_date' in te_cols_available and 'event_text' in te_cols_available:
                te_insert_cols = ['event_date', 'event_text', 'source_file']
                if 'lane' in te_cols_available:
                    te_insert_cols.append('lane')
                if 'actors' in te_cols_available:
                    te_insert_cols.append('actors')
                if 'created_at' in te_cols_available:
                    te_insert_cols.append('created_at')

                # Trim batches to match column count
                trimmed = []
                for row in te_batch:
                    t = list(row[:3])  # date, text, source
                    if 'lane' in te_insert_cols:
                        t.append(row[3] if len(row) > 3 else '')
                    if 'actors' in te_insert_cols:
                        t.append(row[4] if len(row) > 4 else '')
                    if 'created_at' in te_insert_cols:
                        t.append(row[5] if len(row) > 5 else '')
                    trimmed.append(tuple(t))

                placeholders = ','.join(['?'] * len(te_insert_cols))
                cols_str = ','.join(te_insert_cols)
                conn.executemany(
                    f"INSERT OR IGNORE INTO timeline_events ({cols_str}) "
                    f"VALUES ({placeholders})",
                    trimmed
                )
                result.timeline_inserted = len(trimmed)
                result.tables_written.append('timeline_events')
    except sqlite3.OperationalError as e:
        result.errors.append(f"timeline_events: {e}")
        logger.error("timeline_events batch insert failed: %s", e)

    try:
        if im_batch and has_impeachment:
            im_cols_available = _get_table_columns(conn, 'impeachment_matrix')
            # Adaptive insert for impeachment_matrix
            im_insert_cols = []
            for c in ['category', 'evidence_summary', 'source_file',
                       'quote_text', 'impeachment_value',
                       'cross_exam_question', 'filing_relevance', 'event_date']:
                if c in im_cols_available:
                    im_insert_cols.append(c)

            if im_insert_cols:
                trimmed = []
                for row in im_batch:
                    t = []
                    for i, c in enumerate(
                        ['category', 'evidence_summary', 'source_file',
                         'quote_text', 'impeachment_value',
                         'cross_exam_question', 'filing_relevance',
                         'event_date']
                    ):
                        if c in im_insert_cols:
                            t.append(row[i] if i < len(row) else '')
                    trimmed.append(tuple(t))

                placeholders = ','.join(['?'] * len(im_insert_cols))
                cols_str = ','.join(im_insert_cols)
                conn.executemany(
                    f"INSERT OR IGNORE INTO impeachment_matrix ({cols_str}) "
                    f"VALUES ({placeholders})",
                    trimmed
                )
                result.impeachment_inserted = len(trimmed)
                result.tables_written.append('impeachment_matrix')
    except sqlite3.OperationalError as e:
        result.errors.append(f"impeachment_matrix: {e}")
        logger.error("impeachment_matrix batch insert failed: %s", e)

    conn.commit()
    return result


def persist_file_record(conn: sqlite3.Connection,
                        file_info: Dict[str, Any]) -> bool:
    """Persist a single file processing record to harvest_files."""
    if not _table_exists(conn, 'harvest_files'):
        return False

    try:
        conn.execute(
            "INSERT OR REPLACE INTO harvest_files "
            "(file_path, file_name, file_size, sha256, file_type, "
            "lane, doc_type, actors, authorities, dates_found, "
            "page_count, processed_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                file_info.get('file_path', ''),
                file_info.get('file_name', ''),
                file_info.get('file_size', 0),
                file_info.get('sha256', ''),
                file_info.get('file_type', ''),
                file_info.get('lane', 'UNCLASSIFIED'),
                file_info.get('doc_type', 'unknown'),
                ','.join(file_info.get('actors', [])),
                ','.join(file_info.get('authorities', [])),
                ','.join(file_info.get('dates', [])),
                file_info.get('page_count', 0),
                datetime.now().isoformat()
            )
        )
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        logger.error("harvest_files insert failed: %s", e)
        return False


def persist_document_record(conn: sqlite3.Connection,
                            doc_info: Dict[str, Any]) -> bool:
    """Persist a document to the documents table (if it exists)."""
    if not _table_exists(conn, 'documents'):
        return False

    cols = _get_table_columns(conn, 'documents')

    # Adaptive insert based on actual schema
    insert_map = {}
    if 'file_path' in cols:
        insert_map['file_path'] = doc_info.get('file_path', '')
    if 'file_name' in cols:
        insert_map['file_name'] = doc_info.get('file_name', '')
    if 'title' in cols:
        insert_map['title'] = doc_info.get('file_name', '')
    if 'file_size' in cols:
        insert_map['file_size'] = doc_info.get('file_size', 0)
    if 'file_size_bytes' in cols:
        insert_map['file_size_bytes'] = doc_info.get('file_size', 0)
    if 'sha256' in cols:
        insert_map['sha256'] = doc_info.get('sha256', '')
    if 'sha256_hash' in cols:
        insert_map['sha256_hash'] = doc_info.get('sha256', '')
    if 'page_count' in cols:
        insert_map['page_count'] = doc_info.get('page_count', 0)
    if 'doc_type' in cols:
        insert_map['doc_type'] = doc_info.get('doc_type', 'unknown')
    if 'content_preview' in cols:
        insert_map['content_preview'] = doc_info.get('content_preview', '')[:500]

    if not insert_map:
        return False

    try:
        col_names = ','.join(insert_map.keys())
        placeholders = ','.join(['?'] * len(insert_map))
        conn.execute(
            f"INSERT OR IGNORE INTO documents ({col_names}) "
            f"VALUES ({placeholders})",
            tuple(insert_map.values())
        )
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        logger.error("documents insert failed: %s", e)
        return False


def rebuild_fts5_indexes(conn: sqlite3.Connection) -> List[str]:
    """Rebuild FTS5 indexes after bulk inserts. Returns list of rebuilt indexes."""
    rebuilt = []
    fts_tables = ['evidence_fts', 'timeline_fts', 'md_sections_fts']

    for fts in fts_tables:
        if _table_exists(conn, fts):
            try:
                conn.execute(
                    f"INSERT INTO {fts}({fts}) VALUES('rebuild')"
                )
                rebuilt.append(fts)
            except sqlite3.OperationalError as e:
                logger.warning("FTS5 rebuild failed for %s: %s", fts, e)

    if rebuilt:
        conn.commit()
    return rebuilt


def get_persistence_stats(conn: sqlite3.Connection) -> Dict[str, int]:
    """Get row counts for all persistence targets."""
    stats = {}
    tables = [
        'evidence_quotes', 'harvest_evidence', 'harvest_files',
        'timeline_events', 'impeachment_matrix', 'documents',
        'contradiction_map', 'judicial_violations', 'authority_chains_v2'
    ]
    for t in tables:
        if _table_exists(conn, t):
            try:
                row = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()
                stats[t] = row[0]
            except sqlite3.OperationalError:
                stats[t] = -1
        else:
            stats[t] = 0
    return stats
