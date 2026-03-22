"""Document management engine — catalog, classify, and search documents.

Manages the ``documents`` table in ``litigation_context.db``, supporting
lane-aware filtering, full-text search, and document classification.

Usage::

    from litigationos.engines.document import DocumentEngine

    engine = DocumentEngine()
    doc = engine.get_document(doc_id=42)
    results = engine.search_documents("motion to compel")
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# -- Constants ----------------------------------------------------------------

_DEFAULT_DB_PATH = Path(__file__).resolve().parents[5] / "litigation_context.db"

_SQLITE_PRAGMAS = (
    "PRAGMA busy_timeout=60000",
    "PRAGMA journal_mode=WAL",
    "PRAGMA cache_size=-32000",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA synchronous=NORMAL",
)

DOCUMENT_TYPES = (
    "motion", "brief", "affidavit", "order", "notice", "complaint",
    "subpoena", "exhibit", "transcript", "correspondence", "report",
)


# -- Models -------------------------------------------------------------------


class Document(BaseModel):
    """A catalogued litigation document."""

    doc_id: Optional[int] = None
    title: str = ""
    doc_type: Optional[str] = None
    lane: Optional[str] = None
    file_path: Optional[str] = None
    description: Optional[str] = None
    date_filed: Optional[str] = None
    classification: Optional[str] = None
    sha256: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(from_attributes=True)


class DocumentSearchResult(BaseModel):
    """Result from a document search query."""

    query: str = ""
    total_results: int = 0
    documents: list[Document] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# -- Engine -------------------------------------------------------------------


class DocumentEngine:
    """Document catalog and search engine.

    Parameters
    ----------
    db_path : str | Path, optional
        Path to ``litigation_context.db``.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        logger.info("DocumentEngine initialized — db=%s", self._db_path)

    @staticmethod
    def _connect(db_path: Path) -> sqlite3.Connection:
        conn = sqlite3.connect(str(db_path), timeout=120)
        for pragma in _SQLITE_PRAGMAS:
            conn.execute(pragma)
        conn.row_factory = sqlite3.Row
        return conn

    def _table_exists(self, conn: sqlite3.Connection, name: str) -> bool:
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None

    def _row_to_document(self, row: sqlite3.Row, cols: Sequence[str]) -> Document:
        """Map a DB row to a :class:`Document`."""
        return Document(
            doc_id=int(row["rowid"]) if "rowid" in cols else None,
            title=str(row["title"]) if "title" in cols else "",
            doc_type=str(row["doc_type"]) if "doc_type" in cols else None,
            lane=str(row["lane"]) if "lane" in cols else None,
            file_path=str(row["file_path"]) if "file_path" in cols else None,
            description=str(row["description"]) if "description" in cols else None,
            classification=str(row["classification"]) if "classification" in cols else None,
        )

    def get_document(self, doc_id: int) -> Document:
        """Retrieve a single document by its primary key."""
        result = Document(doc_id=doc_id)
        if not self._db_path.exists():
            return result
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "documents"):
                return result
            cols = [r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()]
            cols_with_rowid = ["rowid", *cols]
            row = conn.execute("SELECT rowid, * FROM documents WHERE rowid = ?", (doc_id,)).fetchone()
            if row:
                result = self._row_to_document(row, cols_with_rowid)
        finally:
            conn.close()
        return result

    def list_documents(self, lane: str | None = None, limit: int = 100) -> list[Document]:
        """List documents with optional *lane* filter."""
        results: list[Document] = []
        if not self._db_path.exists():
            return results
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "documents"):
                return results
            cols = [r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()]
            cols_with_rowid = ["rowid", *cols]
            query = "SELECT rowid, * FROM documents"
            params: list[Any] = []
            if lane and "lane" in cols:
                query += " WHERE lane = ?"
                params.append(lane)
            query += " LIMIT ?"
            params.append(limit)
            for row in conn.execute(query, params).fetchall():
                results.append(self._row_to_document(row, cols_with_rowid))
        finally:
            conn.close()
        return results

    def search_documents(self, query: str, limit: int = 50) -> DocumentSearchResult:
        """Search documents by keyword across title and description."""
        result = DocumentSearchResult(query=query)
        if not self._db_path.exists():
            return result
        conn = self._connect(self._db_path)
        try:
            if not self._table_exists(conn, "documents"):
                return result
            cols = [r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()]
            cols_with_rowid = ["rowid", *cols]
            clauses: list[str] = []
            if "title" in cols:
                clauses.append("title LIKE ?")
            if "description" in cols:
                clauses.append("description LIKE ?")
            if not clauses:
                return result
            where = " OR ".join(clauses)
            params: list[Any] = [f"%{query}%"] * len(clauses) + [limit]
            for row in conn.execute(
                f"SELECT rowid, * FROM documents WHERE ({where}) LIMIT ?", params,
            ).fetchall():
                result.documents.append(self._row_to_document(row, cols_with_rowid))
            result.total_results = len(result.documents)
        finally:
            conn.close()
        return result

    def classify_document(self, doc_id: int) -> str:
        """Return a best-guess classification for the document."""
        doc = self.get_document(doc_id)
        title_lower = doc.title.lower()
        for dtype in DOCUMENT_TYPES:
            if dtype in title_lower:
                return dtype
        return "unknown"
