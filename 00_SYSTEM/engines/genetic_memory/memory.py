"""GeneticMemory — Cross-session learning with confidence evolution.

Stores knowledge as 'genes' — facts, patterns, strategies, and heuristics
that evolve over time. Each gene has a confidence score that increases
with validation and decreases with invalidation or disuse.

Table schema (created on first use):
    gene_id         TEXT PRIMARY KEY  (UUID)
    gene_type       TEXT              (fact, pattern, strategy, heuristic, preference)
    content         TEXT NOT NULL     (the knowledge itself)
    confidence      REAL DEFAULT 0.5  (0.0–1.0)
    validations     INTEGER DEFAULT 0
    invalidations   INTEGER DEFAULT 0
    parent_id       TEXT              (lineage — gene this was derived from)
    lane            TEXT              (case lane A-F, CRIMINAL)
    tags            TEXT              (comma-separated tags)
    status          TEXT DEFAULT 'active'  (active, archived, superseded)
    created_at      TEXT
    updated_at      TEXT
"""

import sys
import os
import re
import uuid
import sqlite3
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.insert(0, r"C:\Users\andre\LitigationOS")

logger = logging.getLogger(__name__)

# ── Schema ────────────────────────────────────────────────────────────────

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS genetic_memory (
    gene_id       TEXT PRIMARY KEY,
    gene_type     TEXT NOT NULL,
    content       TEXT NOT NULL,
    confidence    REAL DEFAULT 0.5,
    validations   INTEGER DEFAULT 0,
    invalidations INTEGER DEFAULT 0,
    parent_id     TEXT,
    lane          TEXT DEFAULT '',
    tags          TEXT DEFAULT '',
    status        TEXT DEFAULT 'active',
    created_at    TEXT,
    updated_at    TEXT
)
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_gm_type_status
    ON genetic_memory(gene_type, status)
"""

_CREATE_CONFIDENCE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_gm_confidence
    ON genetic_memory(confidence DESC)
"""


# ── Core Class ────────────────────────────────────────────────────────────

class GeneticMemory:
    """Cross-session genetic memory with confidence evolution.

    Genes are units of knowledge that evolve through:
        - validate(): increases confidence (diminishing returns)
        - invalidate(): decreases confidence
        - evolve(): decay inactive genes, archive dead ones
    """

    VALID_TYPES = frozenset({"fact", "pattern", "strategy", "heuristic", "preference"})
    VALID_STATUSES = frozenset({"active", "archived", "superseded"})
    ARCHIVE_THRESHOLD = 0.1
    DECAY_RATE = 0.01

    def __init__(self, db_path: Optional[str] = None):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ── Lazy Connection ───────────────────────────────────────────────

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = self._connect()
            self._ensure_schema()
        return self._conn

    def _connect(self) -> sqlite3.Connection:
        """Open connection with standard PRAGMAs."""
        if self._db_path:
            path = self._db_path
        else:
            try:
                from shared import get_db_path
                path = str(get_db_path("litigation_context"))
            except ImportError:
                path = os.path.join(
                    r"C:\Users\andre\LitigationOS", "litigation_context.db"
                )
        conn = sqlite3.connect(path, timeout=60)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _ensure_schema(self) -> None:
        """Create tables and indexes if they don't exist."""
        self.conn.execute(_CREATE_TABLE)
        self.conn.execute(_CREATE_INDEX)
        self.conn.execute(_CREATE_CONFIDENCE_INDEX)
        self.conn.commit()
        logger.debug("genetic_memory schema ensured")

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ── Store ─────────────────────────────────────────────────────────

    def store_gene(
        self,
        gene_type: str,
        content: str,
        confidence: float = 0.5,
        parent_id: Optional[str] = None,
        lane: str = "",
        tags: str = "",
    ) -> str:
        """Store a new gene. Returns the gene_id (UUID).

        Args:
            gene_type: One of 'fact', 'pattern', 'strategy', 'heuristic', 'preference'
            content: The knowledge content
            confidence: Initial confidence score 0.0-1.0
            parent_id: Optional parent gene ID for lineage
            lane: Case lane (A-F, CRIMINAL)
            tags: Comma-separated tags

        Returns:
            gene_id: UUID string
        """
        if gene_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid gene_type '{gene_type}'. Must be one of: {self.VALID_TYPES}"
            )
        confidence = max(0.0, min(1.0, confidence))
        gene_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        self.conn.execute(
            """INSERT INTO genetic_memory
               (gene_id, gene_type, content, confidence, validations,
                invalidations, parent_id, lane, tags, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, 0, 0, ?, ?, ?, 'active', ?, ?)""",
            (gene_id, gene_type, content, confidence, parent_id,
             lane, tags, now, now),
        )
        self.conn.commit()
        logger.info("Stored gene %s (type=%s, conf=%.2f)", gene_id[:8], gene_type, confidence)
        return gene_id

    # ── Recall ────────────────────────────────────────────────────────

    def recall_genes(
        self,
        gene_type: Optional[str] = None,
        min_confidence: float = 0.0,
        lane: Optional[str] = None,
        status: str = "active",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Recall genes matching filters, ordered by confidence descending.

        Args:
            gene_type: Filter by type (None = all types)
            min_confidence: Minimum confidence threshold
            lane: Filter by lane
            status: Filter by status (default 'active')
            limit: Max results

        Returns:
            List of gene dicts
        """
        clauses = ["status = ?"]
        params: list = [status]

        if gene_type:
            clauses.append("gene_type = ?")
            params.append(gene_type)
        if min_confidence > 0:
            clauses.append("confidence >= ?")
            params.append(min_confidence)
        if lane:
            clauses.append("lane = ?")
            params.append(lane)

        params.append(limit)
        where = " AND ".join(clauses)

        rows = self.conn.execute(
            f"""SELECT * FROM genetic_memory
                WHERE {where}
                ORDER BY confidence DESC
                LIMIT ?""",
            params,
        ).fetchall()

        return [dict(r) for r in rows]

    def recall_by_id(self, gene_id: str) -> Optional[Dict[str, Any]]:
        """Recall a single gene by ID."""
        row = self.conn.execute(
            "SELECT * FROM genetic_memory WHERE gene_id = ?", (gene_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Search ────────────────────────────────────────────────────────

    def search_genes(
        self,
        query: str,
        min_confidence: float = 0.0,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """Search genes by content using LIKE (table is small, no FTS5 needed).

        Args:
            query: Search terms (spaces become AND conditions)
            min_confidence: Minimum confidence threshold
            limit: Max results
        """
        # Sanitize
        clean = re.sub(r'[^\w\s*"]', ' ', query).strip()
        if not clean:
            return []

        terms = clean.split()
        clauses = ["status = 'active'"]
        params: list = []

        for term in terms:
            clauses.append("content LIKE ?")
            params.append(f"%{term}%")

        if min_confidence > 0:
            clauses.append("confidence >= ?")
            params.append(min_confidence)

        params.append(limit)
        where = " AND ".join(clauses)

        rows = self.conn.execute(
            f"""SELECT * FROM genetic_memory
                WHERE {where}
                ORDER BY confidence DESC
                LIMIT ?""",
            params,
        ).fetchall()

        return [dict(r) for r in rows]

    # ── Validation / Invalidation ─────────────────────────────────────

    def validate(self, gene_id: str) -> Optional[float]:
        """Validate a gene — increases confidence with diminishing returns.

        Formula: confidence += (1 - confidence) * 0.1
        Returns the new confidence, or None if gene not found.
        """
        gene = self.recall_by_id(gene_id)
        if not gene or gene["status"] != "active":
            return None

        old_conf = gene["confidence"]
        new_conf = min(1.0, old_conf + (1.0 - old_conf) * 0.1)
        new_validations = gene["validations"] + 1

        self.conn.execute(
            """UPDATE genetic_memory
               SET confidence = ?, validations = ?, updated_at = ?
               WHERE gene_id = ?""",
            (new_conf, new_validations, datetime.utcnow().isoformat(), gene_id),
        )
        self.conn.commit()
        logger.debug("Validated gene %s: %.3f → %.3f", gene_id[:8], old_conf, new_conf)
        return new_conf

    def invalidate(self, gene_id: str) -> Optional[float]:
        """Invalidate a gene — decreases confidence.

        Formula: confidence -= confidence * 0.15
        Returns the new confidence, or None if gene not found.
        Auto-archives if confidence drops below ARCHIVE_THRESHOLD.
        """
        gene = self.recall_by_id(gene_id)
        if not gene or gene["status"] != "active":
            return None

        old_conf = gene["confidence"]
        new_conf = max(0.0, old_conf - old_conf * 0.15)
        new_invalidations = gene["invalidations"] + 1
        now = datetime.utcnow().isoformat()

        new_status = "active"
        if new_conf < self.ARCHIVE_THRESHOLD:
            new_status = "archived"
            logger.info("Gene %s archived (confidence %.3f < %.2f)",
                        gene_id[:8], new_conf, self.ARCHIVE_THRESHOLD)

        self.conn.execute(
            """UPDATE genetic_memory
               SET confidence = ?, invalidations = ?, status = ?, updated_at = ?
               WHERE gene_id = ?""",
            (new_conf, new_invalidations, new_status, now, gene_id),
        )
        self.conn.commit()
        logger.debug("Invalidated gene %s: %.3f → %.3f", gene_id[:8], old_conf, new_conf)
        return new_conf

    # ── Evolution ─────────────────────────────────────────────────────

    def evolve(self) -> Dict[str, int]:
        """Run one evolution cycle: decay and archive low-confidence genes.

        All active genes lose DECAY_RATE confidence per cycle.
        Genes dropping below ARCHIVE_THRESHOLD are archived.

        Returns:
            Dict with 'decayed' and 'archived' counts.
        """
        now = datetime.utcnow().isoformat()

        # Decay all active genes
        self.conn.execute(
            """UPDATE genetic_memory
               SET confidence = MAX(0.0, confidence - ?),
                   updated_at = ?
               WHERE status = 'active'""",
            (self.DECAY_RATE, now),
        )

        # Archive genes below threshold
        cursor = self.conn.execute(
            """UPDATE genetic_memory
               SET status = 'archived', updated_at = ?
               WHERE status = 'active' AND confidence < ?""",
            (now, self.ARCHIVE_THRESHOLD),
        )
        archived = cursor.rowcount

        # Count active genes that were decayed
        row = self.conn.execute(
            "SELECT COUNT(*) FROM genetic_memory WHERE status = 'active'"
        ).fetchone()
        decayed = row[0] if row else 0

        self.conn.commit()
        logger.info("Evolution cycle: decayed=%d active genes, archived=%d", decayed, archived)
        return {"decayed": decayed, "archived": archived}

    # ── Lineage ───────────────────────────────────────────────────────

    def get_lineage(self, gene_id: str) -> List[Dict[str, Any]]:
        """Trace the ancestry of a gene back to its root.

        Returns a list of genes from root to the given gene.
        """
        chain: List[Dict[str, Any]] = []
        visited = set()
        current_id = gene_id

        while current_id and current_id not in visited:
            visited.add(current_id)
            gene = self.recall_by_id(current_id)
            if not gene:
                break
            chain.append(gene)
            current_id = gene.get("parent_id")

        chain.reverse()
        return chain

    def get_children(self, gene_id: str) -> List[Dict[str, Any]]:
        """Get all genes directly derived from this gene."""
        rows = self.conn.execute(
            """SELECT * FROM genetic_memory
               WHERE parent_id = ?
               ORDER BY confidence DESC""",
            (gene_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Supersede ─────────────────────────────────────────────────────

    def supersede(
        self,
        old_gene_id: str,
        new_content: str,
        confidence: Optional[float] = None,
    ) -> Optional[str]:
        """Replace a gene with an updated version, preserving lineage.

        Marks the old gene as 'superseded' and creates a new gene
        with the old one as parent. Inherits confidence if not specified.

        Returns: new gene_id, or None if old gene not found.
        """
        old_gene = self.recall_by_id(old_gene_id)
        if not old_gene:
            return None

        # Mark old gene as superseded
        self.conn.execute(
            """UPDATE genetic_memory
               SET status = 'superseded', updated_at = ?
               WHERE gene_id = ?""",
            (datetime.utcnow().isoformat(), old_gene_id),
        )

        # Create new gene inheriting from old
        new_conf = confidence if confidence is not None else old_gene["confidence"]
        new_id = self.store_gene(
            gene_type=old_gene["gene_type"],
            content=new_content,
            confidence=new_conf,
            parent_id=old_gene_id,
            lane=old_gene["lane"],
            tags=old_gene["tags"],
        )
        logger.info("Superseded gene %s → %s", old_gene_id[:8], new_id[:8])
        return new_id

    # ── Statistics ────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Return summary statistics about the genetic memory.

        Returns counts by status, type, and confidence distribution.
        """
        row = self.conn.execute(
            """SELECT
                (SELECT COUNT(*) FROM genetic_memory) AS total,
                (SELECT COUNT(*) FROM genetic_memory WHERE status='active') AS active,
                (SELECT COUNT(*) FROM genetic_memory WHERE status='archived') AS archived,
                (SELECT COUNT(*) FROM genetic_memory WHERE status='superseded') AS superseded,
                (SELECT AVG(confidence) FROM genetic_memory WHERE status='active') AS avg_confidence,
                (SELECT MAX(confidence) FROM genetic_memory WHERE status='active') AS max_confidence,
                (SELECT MIN(confidence) FROM genetic_memory WHERE status='active') AS min_confidence
            """
        ).fetchone()

        type_rows = self.conn.execute(
            """SELECT gene_type, COUNT(*) as cnt
               FROM genetic_memory
               WHERE status = 'active'
               GROUP BY gene_type
               ORDER BY cnt DESC"""
        ).fetchall()

        return {
            "total": row[0] or 0,
            "active": row[1] or 0,
            "archived": row[2] or 0,
            "superseded": row[3] or 0,
            "avg_confidence": round(row[4] or 0, 3),
            "max_confidence": round(row[5] or 0, 3),
            "min_confidence": round(row[6] or 0, 3),
            "by_type": {r[0]: r[1] for r in type_rows},
        }
