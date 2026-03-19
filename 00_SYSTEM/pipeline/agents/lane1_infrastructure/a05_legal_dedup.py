"""
A05-LEGAL-DEDUP — SHA-256 hash legal files, identify duplicates, elect canonicals.
DELTA9 Fleet · Tier 2 · Lane 1 Infrastructure
"""
import hashlib
import os
from collections import defaultdict

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LEGAL_EXTENSIONS, DATA_EXTENSIONS, CODE_EXTENSIONS,
    ARCHIVE_EXTENSIONS, SKIP_EXTENSIONS, CANONICAL_PRIORITY
)

CHUNK_SIZE = 65536  # 64KB streaming hash


class LegalDedup(Agent9999):
    """Hash legal files, cluster duplicates, elect canonical per cluster."""

    def __init__(self):
        super().__init__(agent_id="A05-LEGAL-DEDUP")
        self._clusters_found = 0
        self._space_saved = 0
        self._canonical_count = 0

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _ensure_tables(self):
        # dedup_clusters already created by orchestrator — no-op
        pass

    # ------------------------------------------------------------------
    # Preconditions
    # ------------------------------------------------------------------
    def _validate_preconditions(self):
        placeholders = ",".join("?" for _ in LEGAL_EXTENSIONS)
        row = self._db_execute(
            f"SELECT COUNT(*) AS cnt FROM files WHERE extension IN ({placeholders})",
            tuple(LEGAL_EXTENSIONS)
        ).fetchone()
        if not row or row["cnt"] == 0:
            raise FatalAgentError("No legal-extension files in files table")

    # ------------------------------------------------------------------
    # Work items: legal files without a hash yet
    # ------------------------------------------------------------------
    def _get_work_items(self) -> list:
        placeholders = ",".join("?" for _ in LEGAL_EXTENSIONS)
        rows = self._db_execute(
            f"""SELECT id, full_path, extension, size_bytes
                FROM files
                WHERE extension IN ({placeholders}) AND sha256 IS NULL
                ORDER BY size_bytes ASC""",
            tuple(LEGAL_EXTENSIONS)
        ).fetchall()
        return rows

    # ------------------------------------------------------------------
    # Process: hash one file
    # ------------------------------------------------------------------
    def _process_item(self, row) -> None:
        file_id = row["id"]
        raw_path = row["full_path"]
        path = self.long_path(raw_path)

        if not os.path.exists(path):
            raise SkipItemError(f"File gone: {raw_path}")

        try:
            sha = self._hash_file(path)
        except PermissionError:
            raise SkipItemError(f"Permission denied: {raw_path}")
        except FileNotFoundError:
            raise SkipItemError(f"File not found during read: {raw_path}")
        except OSError as e:
            raise SkipItemError(f"OS error hashing {raw_path}: {e}")

        self._db_execute(
            "UPDATE files SET sha256 = ? WHERE id = ?", (sha, file_id)
        )
        self.db.commit()

    # ------------------------------------------------------------------
    # Finalize: cluster duplicates, elect canonicals
    # ------------------------------------------------------------------
    def _finalize(self):
        placeholders = ",".join("?" for _ in LEGAL_EXTENSIONS)
        clusters = self._db_execute(
            f"""SELECT sha256, COUNT(*) AS cnt
                FROM files
                WHERE extension IN ({placeholders}) AND sha256 IS NOT NULL
                GROUP BY sha256 HAVING cnt > 1""",
            tuple(LEGAL_EXTENSIONS)
        ).fetchall()

        for cluster in clusters:
            sha = cluster["sha256"]
            members = self._db_execute(
                "SELECT id, full_path, size_bytes FROM files WHERE sha256 = ?",
                (sha,)
            ).fetchall()

            canonical = self._elect_canonical(members)
            self._db_execute(
                "UPDATE files SET is_canonical = 1 WHERE id = ?",
                (canonical["id"],)
            )
            self._db_execute(
                """INSERT OR REPLACE INTO dedup_clusters (cluster_sha256, file_count, canonical_id, space_saved_bytes)
                   VALUES (?, ?, ?, ?)""",
                (sha, len(members), canonical["id"],
                 sum((m["size_bytes"] or 0) for m in members if m["id"] != canonical["id"]))
            )
            self._clusters_found += 1
            self._canonical_count += 1
            # Space saved = sum of non-canonical sizes
            for m in members:
                if m["id"] != canonical["id"]:
                    self._space_saved += (m["size_bytes"] or 0)

        self.db.commit()

        # Also mark UNIQUE files (no dupes) as canonical — they're the only copy
        unique_marked = self._db_execute(
            f"""UPDATE files SET is_canonical = 1
                WHERE extension IN ({placeholders})
                  AND sha256 IS NOT NULL
                  AND is_canonical = 0
                  AND sha256 NOT IN (
                      SELECT sha256 FROM files
                      WHERE extension IN ({placeholders}) AND sha256 IS NOT NULL
                      GROUP BY sha256 HAVING COUNT(*) > 1
                  )""",
            tuple(LEGAL_EXTENSIONS) + tuple(LEGAL_EXTENSIONS)
        ).rowcount
        self.db.commit()
        self._canonical_count += unique_marked

        saved_mb = self._space_saved / (1024 * 1024)
        self._log("SUMMARY",
                  f"Clusters: {self._clusters_found} | "
                  f"Canonicals: {self._canonical_count} (incl {unique_marked} unique) | "
                  f"Space saved: {saved_mb:.1f} MB")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _hash_file(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _elect_canonical(members) -> dict:
        """Pick canonical: highest CANONICAL_PRIORITY segment, then shallowest path."""
        def score(m):
            parts = m["full_path"].replace("\\", "/").split("/")
            priority = max(
                (CANONICAL_PRIORITY.get(seg, 0) for seg in parts), default=0
            )
            depth = len(parts)
            return (-priority, depth)  # lower is better

        return min(members, key=score)
