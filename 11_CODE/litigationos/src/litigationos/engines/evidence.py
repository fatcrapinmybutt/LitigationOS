"""Evidence management engine.

Catalogues evidence with SHA-256 hashing, assigns Bates numbers, provides
FTS5 search across descriptions, and generates MRE 901 authentication
declarations and formal exhibit lists for court.
"""

from __future__ import annotations

import hashlib
import json
import logging
import mimetypes
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# -- Constants ----------------------------------------------------------------

VALID_EVIDENCE_TYPES = (
    "document", "photo", "screenshot", "recording", "email",
    "text_message", "court_order", "financial", "declaration",
)

# Map common MIME prefixes / extensions to evidence file_type values
_MIME_TO_FILE_TYPE: dict[str, str] = {
    "application/pdf": "pdf",
    "image/": "image",
    "text/": "text",
    "message/": "email",
    "audio/": "recording",
    "video/": "recording",
}

_EXT_TO_FILE_TYPE: dict[str, str] = {
    ".pdf": "pdf",
    ".doc": "document",
    ".docx": "document",
    ".txt": "text",
    ".eml": "email",
    ".msg": "email",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".bmp": "image",
    ".tiff": "image",
    ".mp3": "recording",
    ".mp4": "recording",
    ".wav": "recording",
    ".mov": "recording",
    ".csv": "document",
    ".xlsx": "financial",
    ".xls": "financial",
}


def _detect_file_type(file_path: Path) -> str:
    """Best-effort detection of the file type for the evidence table."""
    mime, _ = mimetypes.guess_type(str(file_path))
    if mime:
        for prefix, ftype in _MIME_TO_FILE_TYPE.items():
            if mime.startswith(prefix):
                return ftype

    ext = file_path.suffix.lower()
    return _EXT_TO_FILE_TYPE.get(ext, "document")


def _sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# -- Engine -------------------------------------------------------------------

class EvidenceEngine:
    """Manage evidence items with Bates numbering and FTS search."""

    def __init__(self, db: "DatabaseManager"):
        self._db = db

    # -- Cataloguing ----------------------------------------------------------

    def add_evidence(
        self,
        case_id: int,
        file_path: str,
        evidence_type: str,
        description: str,
        *,
        title: Optional[str] = None,
        source: Optional[str] = None,
        date_created: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> int:
        """Catalogue a piece of evidence.

        Auto-detects the file type, generates a SHA-256 hash of the file, and
        stores all metadata in the ``evidence`` table.

        Args:
            case_id: The case this evidence belongs to.
            file_path: Path to the evidence file on disk.
            evidence_type: One of ``VALID_EVIDENCE_TYPES``.
            description: Human-readable description of the evidence.
            title: Short title (defaults to file name).
            source: Where the evidence came from.
            date_created: When the evidence was originally created (ISO-8601).
            tags: Optional list of string tags.

        Returns:
            The new evidence row ID.

        Raises:
            ValueError: If *evidence_type* is not recognised.
            FileNotFoundError: If *file_path* does not exist.
        """
        if evidence_type not in VALID_EVIDENCE_TYPES:
            raise ValueError(
                f"Invalid evidence_type '{evidence_type}'. "
                f"Must be one of {VALID_EVIDENCE_TYPES}"
            )

        fp = Path(file_path)
        if not fp.exists():
            raise FileNotFoundError(f"Evidence file not found: {file_path}")

        file_type = _detect_file_type(fp)
        sha = _sha256(fp)
        if title is None:
            title = fp.name
        tags_json = json.dumps(tags) if tags else None

        conn = self._db.connect()
        try:
            cursor = conn.execute(
                "INSERT INTO evidence "
                "(case_id, title, description, file_path, file_type, source, "
                " date_created, date_imported, authentication_method, tags, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), NULL, ?, ?)",
                (case_id, title, description, str(fp.resolve()), file_type,
                 source, date_created, tags_json, f"sha256:{sha}"),
            )
            conn.commit()
            eid = cursor.lastrowid
            logger.info("Added evidence %d (%s) for case %d [%s]",
                        eid, evidence_type, case_id, sha[:12])
            return eid
        except Exception:
            conn.rollback()
            logger.exception("Failed to add evidence for case %d", case_id)
            raise
        finally:
            conn.close()

    # -- Bates numbering ------------------------------------------------------

    def assign_bates(self, case_id: int, prefix: str = "PIGORS") -> list[dict]:
        """Assign sequential Bates numbers to all un-numbered evidence for a case.

        Format: ``{prefix}-{number:06d}`` (e.g. ``PIGORS-000001``).

        Args:
            case_id: The case whose evidence to number.
            prefix: Bates prefix string.

        Returns:
            List of ``{"evidence_id": int, "bates_number": str}`` for every
            item that was assigned a number.
        """
        conn = self._db.connect()
        try:
            # Get current max number for this prefix
            existing = conn.execute(
                "SELECT bates_number FROM evidence "
                "WHERE case_id = ? AND bates_number IS NOT NULL "
                "AND bates_number LIKE ? ORDER BY bates_number DESC LIMIT 1",
                (case_id, f"{prefix}-%"),
            ).fetchone()

            start_num = 1
            if existing:
                try:
                    start_num = int(existing["bates_number"].split("-")[-1]) + 1
                except (ValueError, IndexError):
                    pass

            # Get un-numbered items ordered by import date
            rows = conn.execute(
                "SELECT id FROM evidence "
                "WHERE case_id = ? AND bates_number IS NULL "
                "ORDER BY date_imported ASC",
                (case_id,),
            ).fetchall()

            assignments: list[dict] = []
            for i, row in enumerate(rows):
                bates = f"{prefix}-{start_num + i:06d}"
                conn.execute(
                    "UPDATE evidence SET bates_number = ? WHERE id = ?",
                    (bates, row["id"]),
                )
                assignments.append({"evidence_id": row["id"], "bates_number": bates})

            conn.commit()
            logger.info("Assigned %d Bates numbers for case %d (prefix=%s)",
                        len(assignments), case_id, prefix)
            return assignments
        except Exception:
            conn.rollback()
            logger.exception("Failed to assign Bates numbers for case %d", case_id)
            raise
        finally:
            conn.close()

    # -- Search ---------------------------------------------------------------

    def search_evidence(self, query: str, case_id: Optional[int] = None) -> list[dict]:
        """Full-text search across evidence descriptions using FTS5.

        Args:
            query: FTS5 search expression.
            case_id: Optional case filter.

        Returns:
            List of matching evidence dicts.
        """
        if case_id is not None:
            rows = self._db.fetchall(
                "SELECT e.* FROM evidence_fts fts "
                "JOIN evidence e ON fts.rowid = e.id "
                "WHERE evidence_fts MATCH ? AND e.case_id = ?",
                (query, case_id),
            )
        else:
            rows = self._db.fetchall(
                "SELECT e.* FROM evidence_fts fts "
                "JOIN evidence e ON fts.rowid = e.id "
                "WHERE evidence_fts MATCH ?",
                (query,),
            )
        return [dict(r) for r in rows]

    # -- Authentication -------------------------------------------------------

    def authenticate(self, evidence_id: int) -> str:
        """Generate an MRE 901 authentication declaration for an evidence item.

        Returns:
            Plain-text declaration suitable for inclusion in a court filing.

        Raises:
            LookupError: If the evidence item does not exist.
        """
        row = self._db.fetchone("SELECT * FROM evidence WHERE id = ?", (evidence_id,))
        if row is None:
            raise LookupError(f"Evidence {evidence_id} not found.")

        ev = dict(row)
        bates = ev.get("bates_number") or f"ID-{evidence_id}"
        title = ev.get("title", "Unknown")
        description = ev.get("description") or "No description provided."
        file_type = ev.get("file_type") or "document"
        source = ev.get("source") or "the records of the party"
        date_created = ev.get("date_created") or "an unknown date"

        declaration = dedent(f"""\
            DECLARATION OF AUTHENTICITY PURSUANT TO MRE 901

            I, the undersigned, declare under penalty of perjury as follows:

            1. I am familiar with the document identified as {bates} ("{title}").

            2. This {file_type} was obtained from {source} and is dated {date_created}.

            3. Description: {description}

            4. Pursuant to MRE 901(a), I have personal knowledge that this exhibit
               is what it purports to be. The document is a true and accurate
               representation of the original.

            5. This exhibit has not been altered, modified, or tampered with in
               any way since it was obtained.

            Dated: {datetime.now().strftime('%B %d, %Y')}

            ________________________________________
            Signature

            ________________________________________
            Printed Name
        """)

        # Update the authentication method in the DB
        self._db.execute(
            "UPDATE evidence SET authentication_method = 'witness_901' WHERE id = ?",
            (evidence_id,),
        )
        logger.info("Generated MRE 901 declaration for evidence %d", evidence_id)
        return declaration

    # -- Listing --------------------------------------------------------------

    def get_evidence(
        self,
        case_id: Optional[int] = None,
        evidence_type: Optional[str] = None,
    ) -> list[dict]:
        """List evidence items with optional filters.

        Args:
            case_id: Filter to a specific case.
            evidence_type: Filter to a specific evidence type.

        Returns:
            List of evidence dicts.
        """
        clauses: list[str] = []
        params: list = []

        if case_id is not None:
            clauses.append("case_id = ?")
            params.append(case_id)
        if evidence_type is not None:
            if evidence_type not in VALID_EVIDENCE_TYPES:
                raise ValueError(
                    f"Invalid evidence_type '{evidence_type}'. "
                    f"Must be one of {VALID_EVIDENCE_TYPES}"
                )
            # Map evidence_type to the file_type stored in the DB
            clauses.append("file_type = ?")
            params.append(evidence_type)

        sql = "SELECT * FROM evidence"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY date_imported ASC"

        rows = self._db.fetchall(sql, tuple(params))
        return [dict(r) for r in rows]

    # -- Exhibit list ---------------------------------------------------------

    def get_exhibit_list(self, case_id: int) -> str:
        """Generate a formal exhibit list for court submission.

        Args:
            case_id: The case to generate the list for.

        Returns:
            Formatted exhibit list as a string.
        """
        rows = self._db.fetchall(
            "SELECT * FROM evidence WHERE case_id = ? ORDER BY bates_number ASC",
            (case_id,),
        )

        # Fetch case info for the header
        case_row = self._db.fetchone("SELECT * FROM cases WHERE id = ?", (case_id,))
        case_title = dict(case_row).get("title", "Unknown") if case_row else "Unknown"

        lines: list[str] = [
            "EXHIBIT LIST",
            f"Case: {case_title}",
            f"Date: {datetime.now().strftime('%B %d, %Y')}",
            "",
            f"{'No.':<8} {'Bates No.':<18} {'Description':<50} {'Type':<12} {'Auth':>6}",
            "-" * 94,
        ]

        for i, row in enumerate(rows, start=1):
            ev = dict(row)
            bates = ev.get("bates_number") or "—"
            desc = (ev.get("description") or ev.get("title", ""))[:50]
            ftype = ev.get("file_type") or "—"
            auth = "Yes" if ev.get("authentication_method") else "No"
            lines.append(f"{i:<8} {bates:<18} {desc:<50} {ftype:<12} {auth:>6}")

        lines.append("-" * 94)
        lines.append(f"Total exhibits: {len(rows)}")

        result = "\n".join(lines)
        logger.info("Generated exhibit list for case %d (%d items)", case_id, len(rows))
        return result

    # -- Gap analysis ---------------------------------------------------------

    def check_gaps(self, case_id: int) -> list[dict]:
        """Identify claims that are missing supporting evidence.

        Cross-references the ``claims`` table against ``evidence`` for the case
        and returns claims that have no evidence linked via timeline events or
        matching description text.

        Args:
            case_id: Case to analyse.

        Returns:
            List of ``{"claim_id", "claim_title", "issue"}`` dicts.
        """
        claims = self._db.fetchall(
            "SELECT * FROM claims WHERE case_id = ? AND status = 'active'",
            (case_id,),
        )
        evidence_rows = self._db.fetchall(
            "SELECT * FROM evidence WHERE case_id = ?", (case_id,),
        )

        # Build a searchable blob of evidence text
        evidence_text = " ".join(
            (dict(e).get("description") or "") + " " + (dict(e).get("title") or "")
            for e in evidence_rows
        ).lower()

        # Check timeline linkages
        timeline_evidence_ids: set[int] = set()
        timeline_rows = self._db.fetchall(
            "SELECT evidence_ids FROM timeline_events WHERE case_id = ? AND evidence_ids IS NOT NULL",
            (case_id,),
        )
        for tr in timeline_rows:
            try:
                ids = json.loads(dict(tr)["evidence_ids"])
                timeline_evidence_ids.update(ids)
            except (json.JSONDecodeError, TypeError):
                pass

        gaps: list[dict] = []
        for claim_row in claims:
            claim = dict(claim_row)
            claim_title = claim.get("title", "").lower()
            # Extract keywords from the claim title
            keywords = [w for w in claim_title.split() if len(w) > 3]

            has_keyword_match = any(kw in evidence_text for kw in keywords)
            has_linked_evidence = len(timeline_evidence_ids) > 0

            if not has_keyword_match and not has_linked_evidence:
                gaps.append({
                    "claim_id": claim["id"],
                    "claim_title": claim.get("title"),
                    "issue": "No supporting evidence found for this claim.",
                })

        logger.info("Gap analysis for case %d: %d claims missing evidence",
                     case_id, len(gaps))
        return gaps
