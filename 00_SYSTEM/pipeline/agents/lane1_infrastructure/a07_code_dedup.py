"""
A07-CODE-DEDUP — SHA-256 hash code files, mark duplicates (NEVER delete).
DELTA9 Fleet · Tier 2 · Lane 1 Infrastructure

IMPORTANT: ALL code files are kept. Duplicates are marked, never removed.
Pipeline/* → category='PIPELINE', framework files → 'FRAMEWORK'.
"""
import hashlib
import os

from ..agent_base import Agent9999
from ..agent_models import (
    SkipItemError, FatalAgentError, MASTER_INDEX_DB,
    LEGAL_EXTENSIONS, DATA_EXTENSIONS, CODE_EXTENSIONS,
    ARCHIVE_EXTENSIONS, SKIP_EXTENSIONS, CANONICAL_PRIORITY
)

CHUNK_SIZE = 65536


class CodeDedup(Agent9999):
    """Hash code files, mark duplicates — never delete. Tag pipeline/framework."""

    def __init__(self):
        super().__init__(agent_id="A07-CODE-DEDUP")
        self._clusters_found = 0
        self._space_saved = 0
        self._canonical_count = 0
        self._pipeline_count = 0
        self._framework_count = 0

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
        placeholders = ",".join("?" for _ in CODE_EXTENSIONS)
        row = self._db_execute(
            f"SELECT COUNT(*) AS cnt FROM files WHERE extension IN ({placeholders})",
            tuple(CODE_EXTENSIONS)
        ).fetchone()
        if not row or row["cnt"] == 0:
            raise FatalAgentError("No code-extension files in files table")

    # ------------------------------------------------------------------
    # Work items
    # ------------------------------------------------------------------
    def _get_work_items(self) -> list:
        placeholders = ",".join("?" for _ in CODE_EXTENSIONS)
        rows = self._db_execute(
            f"""SELECT id, full_path, file_name, extension, size_bytes
                FROM files
                WHERE extension IN ({placeholders}) AND sha256 IS NULL
                ORDER BY size_bytes ASC""",
            tuple(CODE_EXTENSIONS)
        ).fetchall()
        return rows

    # ------------------------------------------------------------------
    # Process: hash one file + categorize
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

        category = self._classify_code(raw_path)
        self._db_execute(
            "UPDATE files SET sha256 = ?, category = ? WHERE id = ?",
            (sha, category, file_id)
        )
        self.db.commit()

        if category == "PIPELINE":
            self._pipeline_count += 1
        elif category == "FRAMEWORK":
            self._framework_count += 1

    # ------------------------------------------------------------------
    # Finalize: cluster duplicates, elect canonicals (keep all files)
    # ------------------------------------------------------------------
    def _finalize(self):
        placeholders = ",".join("?" for _ in CODE_EXTENSIONS)
        clusters = self._db_execute(
            f"""SELECT sha256, COUNT(*) AS cnt
                FROM files
                WHERE extension IN ({placeholders}) AND sha256 IS NOT NULL
                GROUP BY sha256 HAVING cnt > 1""",
            tuple(CODE_EXTENSIONS)
        ).fetchall()

        for cluster in clusters:
            sha = cluster["sha256"]
            members = self._db_execute(
                "SELECT id, full_path, size_bytes FROM files WHERE sha256 = ?",
                (sha,)
            ).fetchall()

            canonical = self._elect_canonical(members)
            # Mark canonical — all files kept, dupes just flagged
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
            for m in members:
                if m["id"] != canonical["id"]:
                    self._space_saved += (m["size_bytes"] or 0)

        self.db.commit()

        # Mark unique code files as canonical too
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
            tuple(CODE_EXTENSIONS) + tuple(CODE_EXTENSIONS)
        ).rowcount
        self.db.commit()
        self._canonical_count += unique_marked

        saved_mb = self._space_saved / (1024 * 1024)
        self._log("SUMMARY",
                  f"Clusters: {self._clusters_found} | "
                  f"Canonicals: {self._canonical_count} (incl {unique_marked} unique) | "
                  f"PIPELINE tagged: {self._pipeline_count} | "
                  f"FRAMEWORK tagged: {self._framework_count} | "
                  f"Dupe space (kept): {saved_mb:.1f} MB")

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
    def _classify_code(full_path: str) -> str:
        """Classify code file by path segments."""
        normalized = full_path.replace("\\", "/").lower()
        if "/pipeline/" in normalized or "\\pipeline\\" in normalized.replace("/", "\\"):
            return "PIPELINE"
        framework_signals = (
            "/framework/", "/lib/", "/src/", "/core/",
            "/utils/", "/helpers/", "/common/"
        )
        for sig in framework_signals:
            if sig in normalized:
                return "FRAMEWORK"
        return "CODE"

    @staticmethod
    def _elect_canonical(members) -> dict:
        def score(m):
            parts = m["full_path"].replace("\\", "/").split("/")
            priority = max(
                (CANONICAL_PRIORITY.get(seg, 0) for seg in parts), default=0
            )
            depth = len(parts)
            return (-priority, depth)

        return min(members, key=score)
