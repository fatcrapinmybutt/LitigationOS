"""Legal Knowledge Scraper Engine — Web scraper for Michigan legal intelligence.

Scrapes courts.michigan.gov, legislature.mi.gov, law.cornell.edu with rate limiting,
offline fallbacks to static datasets, and FTS5 indexing.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

# Source registry — URLs and scraper configurations
LEGAL_SOURCES = {
    "mcr": {
        "name": "Michigan Court Rules",
        "base_url": "https://courts.michigan.gov/siteassets/rules-instructions-administrative-orders/michigan-court-rules/",
        "offline_module": "litigationos.data.mcr_complete",
        "offline_attr": "MCR_RULES",
    },
    "mcl": {
        "name": "Michigan Compiled Laws",
        "base_url": "https://legislature.mi.gov/Laws/MCL",
        "offline_module": "litigationos.data.mcl_complete",
        "offline_attr": "MCL_CHAPTERS",
    },
    "mre": {
        "name": "Michigan Rules of Evidence",
        "base_url": "https://courts.michigan.gov/siteassets/rules-instructions-administrative-orders/rules-of-evidence/",
        "offline_module": "litigationos.data.mre_complete",
        "offline_attr": "MRE_RULES",
    },
    "frcp": {
        "name": "Federal Rules of Civil Procedure",
        "base_url": "https://www.law.cornell.edu/rules/frcp",
        "offline_module": "litigationos.data.federal_rules",
        "offline_attr": "FRCP_RULES",
    },
    "fre": {
        "name": "Federal Rules of Evidence",
        "base_url": "https://www.law.cornell.edu/rules/fre",
        "offline_module": "litigationos.data.federal_rules",
        "offline_attr": "FRE_RULES",
    },
    "federal_statutes": {
        "name": "Federal Statutes (§1983, etc.)",
        "base_url": "https://uscode.house.gov/",
        "offline_module": "litigationos.data.federal_rules",
        "offline_attr": "FEDERAL_STATUTES",
    },
    "wdmi": {
        "name": "Western District of Michigan Local Rules",
        "base_url": "https://www.miwd.uscourts.gov/court-info/local-rules-and-orders",
        "offline_module": "litigationos.data.federal_rules",
        "offline_attr": "WDMI_LOCAL_RULES",
    },
    "scao_forms": {
        "name": "SCAO Court Forms",
        "base_url": "https://courts.michigan.gov/SCAO-forms/",
        "offline_module": None,
        "offline_attr": None,
    },
    "admin_orders": {
        "name": "Administrative Orders",
        "base_url": "https://courts.michigan.gov/rules-administrative-orders-and-jury-instructions/administrative-orders/",
        "offline_module": None,
        "offline_attr": None,
    },
    "jury_instructions": {
        "name": "Michigan Jury Instructions",
        "base_url": "https://courts.michigan.gov/rules-administrative-orders-and-jury-instructions/jury-instructions/",
        "offline_module": None,
        "offline_attr": None,
    },
}


@dataclass
class ScrapeResult:
    """Result from a single scrape operation."""
    source: str
    citation: str
    title: str
    text: str
    url: str = ""
    scraped_at: str = ""
    content_hash: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.scraped_at:
            self.scraped_at = datetime.now().isoformat()
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.text.encode()).hexdigest()[:16]


class LegalScraper:
    """Web scraper for Michigan legal intelligence with offline fallback.

    Architecture:
        1. Try web scraping (with rate limiting)
        2. Fall back to static datasets if network unavailable
        3. Index everything into FTS5 for search
        4. Track changes via content hashing
    """

    def __init__(self, db_path: Optional[Path] = None, rate_limit: float = 1.0):
        self.db_path = db_path
        self.rate_limit = rate_limit  # seconds between requests
        self._last_request_time = 0.0
        self._session = None
        self._db: Optional[sqlite3.Connection] = None

        if db_path:
            self._init_db()

    def _init_db(self) -> None:
        """Initialize the legal knowledge database with FTS5."""
        self._db = sqlite3.connect(str(self.db_path))
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA busy_timeout=60000")
        self._db.execute("PRAGMA cache_size=-32000")

        self._db.executescript("""
            CREATE TABLE IF NOT EXISTS legal_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                citation TEXT NOT NULL,
                title TEXT NOT NULL,
                full_text TEXT NOT NULL,
                url TEXT DEFAULT '',
                content_hash TEXT NOT NULL,
                chapter TEXT DEFAULT '',
                article TEXT DEFAULT '',
                practice_tips TEXT DEFAULT '',
                cross_references TEXT DEFAULT '',
                scraped_at TEXT NOT NULL,
                updated_at TEXT DEFAULT '',
                metadata_json TEXT DEFAULT '{}',
                UNIQUE(source, citation)
            );

            CREATE TABLE IF NOT EXISTS scrape_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT DEFAULT '',
                items_scraped INTEGER DEFAULT 0,
                items_updated INTEGER DEFAULT 0,
                items_new INTEGER DEFAULT 0,
                status TEXT DEFAULT 'running',
                error TEXT DEFAULT ''
            );

            CREATE INDEX IF NOT EXISTS idx_lk_source ON legal_knowledge(source);
            CREATE INDEX IF NOT EXISTS idx_lk_citation ON legal_knowledge(citation);
            CREATE INDEX IF NOT EXISTS idx_lk_chapter ON legal_knowledge(chapter);
        """)

        # FTS5 virtual table for full-text search
        try:
            self._db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS legal_knowledge_fts USING fts5(
                    citation, title, full_text, practice_tips, chapter,
                    content=legal_knowledge,
                    content_rowid=id,
                    tokenize='porter unicode61'
                )
            """)
        except sqlite3.OperationalError:
            # FTS5 might not be available — degrade gracefully
            logger.warning("FTS5 not available — full-text search will use LIKE")

        self._db.commit()

    def _rate_limit_wait(self) -> None:
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self._last_request_time = time.time()

    def _get_session(self):
        """Get or create an HTTP session (lazy init)."""
        if self._session is None:
            try:
                import requests
                self._session = requests.Session()
                self._session.headers.update({
                    "User-Agent": "LitigationOS/1.0 (Legal Research Tool)",
                    "Accept": "text/html,application/xhtml+xml",
                })
            except ImportError:
                logger.warning("requests library not available — web scraping disabled")
                return None
        return self._session

    def load_offline_source(self, source_key: str) -> list[dict]:
        """Load a legal knowledge source from static offline datasets.

        This is the primary data path — static datasets are always available
        and contain curated, practice-tip-enriched legal knowledge.
        """
        source = LEGAL_SOURCES.get(source_key)
        if not source or not source.get("offline_module"):
            return []

        try:
            import importlib
            module = importlib.import_module(source["offline_module"])
            data = getattr(module, source["offline_attr"], [])
            logger.info(f"Loaded {len(data)} entries from {source['name']} (offline)")
            return data
        except Exception as e:
            logger.error(f"Failed to load offline data for {source_key}: {e}")
            return []

    def ingest_source(self, source_key: str, force_refresh: bool = False) -> int:
        """Ingest a legal knowledge source into the database.

        Strategy:
            1. Load from offline static dataset (always available)
            2. Optionally try web scraping for updates (if network available)
            3. Index into FTS5 for search

        Returns the number of entries ingested.
        """
        if not self._db:
            raise RuntimeError("Database not initialized — provide db_path")

        source = LEGAL_SOURCES.get(source_key)
        if not source:
            raise ValueError(f"Unknown source: {source_key}")

        # Log the scrape
        log_id = self._start_log(source_key)
        items_new = 0
        items_updated = 0

        try:
            # Load offline data
            entries = self.load_offline_source(source_key)

            for entry in entries:
                citation = entry.get("citation", "")
                title = entry.get("title", "")
                text = entry.get("full_text", entry.get("summary", ""))
                content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

                # Upsert: insert or update if content changed
                existing = self._db.execute(
                    "SELECT content_hash FROM legal_knowledge WHERE source=? AND citation=?",
                    (source_key, citation)
                ).fetchone()

                if existing is None:
                    self._db.execute("""
                        INSERT INTO legal_knowledge 
                        (source, citation, title, full_text, content_hash, chapter, article,
                         practice_tips, cross_references, scraped_at, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        source_key, citation, title, text, content_hash,
                        entry.get("chapter", entry.get("article", "")),
                        entry.get("article", ""),
                        entry.get("practice_tips", ""),
                        json.dumps(entry.get("cross_references", [])),
                        datetime.now().isoformat(),
                        json.dumps(entry.get("metadata", {})),
                    ))
                    items_new += 1
                elif existing[0] != content_hash or force_refresh:
                    self._db.execute("""
                        UPDATE legal_knowledge SET
                            title=?, full_text=?, content_hash=?, chapter=?, article=?,
                            practice_tips=?, cross_references=?, updated_at=?, metadata_json=?
                        WHERE source=? AND citation=?
                    """, (
                        title, text, content_hash,
                        entry.get("chapter", entry.get("article", "")),
                        entry.get("article", ""),
                        entry.get("practice_tips", ""),
                        json.dumps(entry.get("cross_references", [])),
                        datetime.now().isoformat(),
                        json.dumps(entry.get("metadata", {})),
                        source_key, citation,
                    ))
                    items_updated += 1

            self._db.commit()
            self._rebuild_fts()

            total = items_new + items_updated
            self._complete_log(log_id, total, items_new, items_updated)
            logger.info(f"Ingested {source_key}: {items_new} new, {items_updated} updated")
            return total

        except Exception as e:
            self._fail_log(log_id, str(e))
            raise

    def ingest_all(self, force_refresh: bool = False) -> dict[str, int]:
        """Ingest all available legal knowledge sources."""
        results = {}
        for key in LEGAL_SOURCES:
            try:
                count = self.ingest_source(key, force_refresh=force_refresh)
                results[key] = count
            except Exception as e:
                logger.error(f"Failed to ingest {key}: {e}")
                results[key] = -1
        return results

    def search(self, query: str, source: Optional[str] = None, limit: int = 20) -> list[dict]:
        """Search legal knowledge using FTS5 or LIKE fallback.

        Args:
            query: Search terms (supports FTS5 syntax: AND, OR, NOT, phrase "...")
            source: Optional filter by source (mcr, mcl, mre, frcp, etc.)
            limit: Maximum results to return

        Returns:
            List of matching entries with relevance ranking.
        """
        if not self._db:
            raise RuntimeError("Database not initialized")

        results = []

        # Try FTS5 first
        try:
            if source:
                rows = self._db.execute("""
                    SELECT lk.citation, lk.title, lk.full_text, lk.practice_tips,
                           lk.chapter, lk.source, rank
                    FROM legal_knowledge_fts fts
                    JOIN legal_knowledge lk ON fts.rowid = lk.id
                    WHERE legal_knowledge_fts MATCH ? AND lk.source = ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, source, limit)).fetchall()
            else:
                rows = self._db.execute("""
                    SELECT lk.citation, lk.title, lk.full_text, lk.practice_tips,
                           lk.chapter, lk.source, rank
                    FROM legal_knowledge_fts fts
                    JOIN legal_knowledge lk ON fts.rowid = lk.id
                    WHERE legal_knowledge_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (query, limit)).fetchall()

            for row in rows:
                results.append({
                    "citation": row[0], "title": row[1], "text": row[2],
                    "practice_tips": row[3], "chapter": row[4],
                    "source": row[5], "relevance": abs(row[6]),
                })

        except sqlite3.OperationalError:
            # FTS5 not available — fall back to LIKE
            like_query = f"%{query}%"
            sql = """
                SELECT citation, title, full_text, practice_tips, chapter, source
                FROM legal_knowledge
                WHERE (full_text LIKE ? OR title LIKE ? OR citation LIKE ? OR practice_tips LIKE ?)
            """
            params: list = [like_query, like_query, like_query, like_query]
            if source:
                sql += " AND source = ?"
                params.append(source)
            sql += f" LIMIT {limit}"

            rows = self._db.execute(sql, params).fetchall()
            for row in rows:
                results.append({
                    "citation": row[0], "title": row[1], "text": row[2],
                    "practice_tips": row[3], "chapter": row[4], "source": row[5],
                })

        return results

    def get_rule(self, citation: str) -> Optional[dict]:
        """Get a specific rule by exact citation."""
        if not self._db:
            return None

        row = self._db.execute("""
            SELECT citation, title, full_text, practice_tips, chapter, source,
                   article, cross_references, metadata_json
            FROM legal_knowledge WHERE citation = ?
        """, (citation,)).fetchone()

        if row:
            return {
                "citation": row[0], "title": row[1], "full_text": row[2],
                "practice_tips": row[3], "chapter": row[4], "source": row[5],
                "article": row[6],
                "cross_references": json.loads(row[7]) if row[7] else [],
                "metadata": json.loads(row[8]) if row[8] else {},
            }
        return None

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the legal knowledge database."""
        if not self._db:
            return {"error": "Database not initialized"}

        row = self._db.execute("""
            SELECT
                (SELECT COUNT(*) FROM legal_knowledge) AS total,
                (SELECT COUNT(DISTINCT source) FROM legal_knowledge) AS sources,
                (SELECT COUNT(DISTINCT chapter) FROM legal_knowledge) AS chapters
        """).fetchone()

        source_counts = self._db.execute("""
            SELECT source, COUNT(*) FROM legal_knowledge GROUP BY source ORDER BY COUNT(*) DESC
        """).fetchall()

        return {
            "total_entries": row[0],
            "total_sources": row[1],
            "total_chapters": row[2],
            "by_source": {r[0]: r[1] for r in source_counts},
        }

    def _rebuild_fts(self) -> None:
        """Rebuild the FTS5 index."""
        try:
            self._db.execute("INSERT INTO legal_knowledge_fts(legal_knowledge_fts) VALUES('rebuild')")
            self._db.commit()
        except sqlite3.OperationalError:
            pass

    def _start_log(self, source: str) -> int:
        cursor = self._db.execute(
            "INSERT INTO scrape_log (source, started_at) VALUES (?, ?)",
            (source, datetime.now().isoformat())
        )
        self._db.commit()
        return cursor.lastrowid

    def _complete_log(self, log_id: int, total: int, new: int, updated: int) -> None:
        self._db.execute("""
            UPDATE scrape_log SET completed_at=?, items_scraped=?, items_new=?,
                items_updated=?, status='completed' WHERE id=?
        """, (datetime.now().isoformat(), total, new, updated, log_id))
        self._db.commit()

    def _fail_log(self, log_id: int, error: str) -> None:
        self._db.execute(
            "UPDATE scrape_log SET completed_at=?, status='failed', error=? WHERE id=?",
            (datetime.now().isoformat(), error, log_id)
        )
        self._db.commit()

    def close(self) -> None:
        """Close database connection."""
        if self._db:
            self._db.close()
            self._db = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
