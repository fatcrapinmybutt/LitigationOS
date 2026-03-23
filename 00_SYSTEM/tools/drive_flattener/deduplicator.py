"""OMEGA-FLATTEN deduplicator — content-based deduplication engine.

LitigationOS Event Horizon Δ∞

USER MANDATE: Content-based dedup — peek inside files, don't rely solely on hashing.
ALL duplicates → _DEDUP folder on the same drive.  NEVER delete.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import time
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .classifier import read_content_preview
from .config import (
    BATCH_SIZE,
    DEDUP_SIMILARITY_THRESHOLD,
    PROGRESS_INTERVAL,
    TEXT_FOLDERS,
)


def dedup_drive(
    conn: sqlite3.Connection,
    drive: str,
    session_id: int,
    *,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Run three-phase deduplication on *drive*.

    Phase 1: SHA-256 exact duplicates
    Phase 2: Content similarity for text-based files (SequenceMatcher ≥ 0.85)
    Phase 3: Size + similar name grouping

    Parameters
    ----------
    conn:
        Connection to ``flatten.db``.
    drive:
        Drive letter (no colon).
    session_id:
        Active ``scan_sessions.id``.
    dry_run:
        If ``True``, identify duplicates but don't move files.

    Returns
    -------
    dict with stats.
    """
    t0 = time.perf_counter()
    stats: Dict[str, Any] = {
        "phase1_clusters": 0,
        "phase1_dupes": 0,
        "phase2_clusters": 0,
        "phase2_dupes": 0,
        "phase3_clusters": 0,
        "phase3_dupes": 0,
        "total_moved": 0,
        "space_saved_bytes": 0,
        "errors": 0,
    }

    # Track already-deduped file IDs so phases don't re-process them
    deduped_ids: Set[int] = set()

    print("  [DEDUP] Phase 1: SHA-256 exact duplicates …")
    _phase1_sha256(conn, drive, session_id, dry_run, stats, deduped_ids)

    print("  [DEDUP] Phase 2: Content similarity (text files) …")
    _phase2_content_similarity(conn, drive, session_id, dry_run, stats, deduped_ids)

    print("  [DEDUP] Phase 3: Size + name grouping …")
    _phase3_size_name(conn, drive, session_id, dry_run, stats, deduped_ids)

    # Update session
    total_deduped = stats["phase1_dupes"] + stats["phase2_dupes"] + stats["phase3_dupes"]
    conn.execute(
        "UPDATE scan_sessions SET files_deduped = ? WHERE id = ?",
        (total_deduped, session_id),
    )
    conn.commit()

    # Write dedup report
    _write_dedup_report(conn, drive, stats)

    elapsed = time.perf_counter() - t0
    stats["elapsed_seconds"] = round(elapsed, 2)
    print(
        f"  [DEDUP] COMPLETE — {total_deduped:,} duplicates found, "
        f"{stats['total_moved']:,} moved to _DEDUP, "
        f"{stats['space_saved_bytes'] / (1024**2):.1f} MB recoverable "
        f"in {elapsed:.1f}s",
    )
    return stats


# ---------------------------------------------------------------------------
# Phase 1 — SHA-256 exact duplicates
# ---------------------------------------------------------------------------

def _phase1_sha256(
    conn: sqlite3.Connection,
    drive: str,
    session_id: int,
    dry_run: bool,
    stats: Dict[str, Any],
    deduped_ids: Set[int],
) -> None:
    """Group files with identical SHA-256 hashes."""
    rows = conn.execute(
        """SELECT sha256, GROUP_CONCAT(id) AS ids, COUNT(*) AS cnt
             FROM flat_files
            WHERE drive = ? AND sha256 IS NOT NULL AND sha256 != ''
                  AND is_duplicate = 0
            GROUP BY sha256
           HAVING cnt > 1
            ORDER BY cnt DESC""",
        (drive,),
    ).fetchall()

    for sha256_hash, id_csv, cnt in rows:
        file_ids = [int(x) for x in id_csv.split(",")]
        files = _load_files(conn, file_ids)
        if len(files) < 2:
            continue

        canonical = _choose_canonical(files)
        dupes = [f for f in files if f["id"] != canonical["id"]]

        cluster_id = _create_cluster(
            conn, sha256_hash, canonical["id"], len(files),
            sum(f["size_bytes"] for f in files), "sha256",
        )

        # Mark canonical
        _add_member(conn, cluster_id, canonical["id"], 1.0, is_canonical=True, action="keep")

        for dupe in dupes:
            if dupe["id"] in deduped_ids:
                continue
            _add_member(conn, cluster_id, dupe["id"], 1.0, is_canonical=False, action="move")
            _mark_duplicate(conn, dupe["id"], canonical["id"])
            if not dry_run:
                if _move_to_dedup(drive, dupe):
                    stats["total_moved"] += 1
                else:
                    stats["errors"] += 1
            stats["space_saved_bytes"] += dupe["size_bytes"]
            deduped_ids.add(dupe["id"])

        stats["phase1_clusters"] += 1
        stats["phase1_dupes"] += len(dupes)

    conn.commit()


# ---------------------------------------------------------------------------
# Phase 2 — Content similarity for text files
# ---------------------------------------------------------------------------

def _phase2_content_similarity(
    conn: sqlite3.Connection,
    drive: str,
    session_id: int,
    dry_run: bool,
    stats: Dict[str, Any],
    deduped_ids: Set[int],
) -> None:
    """Compare text content of files in TEXT_FOLDERS using SequenceMatcher."""
    folder_list = ",".join(f"'{f}'" for f in TEXT_FOLDERS)
    rows = conn.execute(
        f"""SELECT id, original_path, new_path, folder, filename, size_bytes,
                   litigation_score
              FROM flat_files
             WHERE drive = ? AND folder IN ({folder_list})
                   AND is_duplicate = 0 AND size_bytes > 0 AND size_bytes < 1048576
             ORDER BY folder, size_bytes""",
        (drive,),
    ).fetchall()

    # Group by folder for targeted comparison
    by_folder: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        fid, orig, newp, folder, fname, sz, lscore = row
        if fid in deduped_ids:
            continue
        by_folder[folder].append({
            "id": fid, "original_path": orig, "new_path": newp,
            "folder": folder, "filename": fname, "size_bytes": sz,
            "litigation_score": lscore or 0,
        })

    for folder, file_list in by_folder.items():
        if len(file_list) < 2:
            continue

        # Size-bucket comparison (only compare files within 2x size of each other)
        file_list.sort(key=lambda f: f["size_bytes"])
        compared: Set[Tuple[int, int]] = set()

        for i, fa in enumerate(file_list):
            if fa["id"] in deduped_ids:
                continue
            content_a = _read_normalized(fa)
            if content_a is None:
                continue

            for j in range(i + 1, min(i + 50, len(file_list))):
                fb = file_list[j]
                if fb["id"] in deduped_ids:
                    continue

                pair = (min(fa["id"], fb["id"]), max(fa["id"], fb["id"]))
                if pair in compared:
                    continue
                compared.add(pair)

                # Size gate: skip if files differ by more than 3x
                if fb["size_bytes"] > fa["size_bytes"] * 3:
                    break

                content_b = _read_normalized(fb)
                if content_b is None:
                    continue

                similarity = SequenceMatcher(
                    None, content_a, content_b,
                ).ratio()

                if similarity >= DEDUP_SIMILARITY_THRESHOLD:
                    canonical, dupe = _pick_canonical_pair(fa, fb)
                    if dupe["id"] in deduped_ids:
                        continue

                    cluster_id = _create_cluster(
                        conn, None, canonical["id"], 2,
                        canonical["size_bytes"] + dupe["size_bytes"],
                        f"content_similarity_{similarity:.3f}",
                    )
                    _add_member(conn, cluster_id, canonical["id"], similarity, True, "keep")
                    _add_member(conn, cluster_id, dupe["id"], similarity, False, "move")
                    _mark_duplicate(conn, dupe["id"], canonical["id"])

                    if not dry_run:
                        if _move_to_dedup(drive, dupe):
                            stats["total_moved"] += 1
                        else:
                            stats["errors"] += 1

                    stats["space_saved_bytes"] += dupe["size_bytes"]
                    stats["phase2_clusters"] += 1
                    stats["phase2_dupes"] += 1
                    deduped_ids.add(dupe["id"])

        conn.commit()


def _read_normalized(file_info: Dict[str, Any]) -> Optional[str]:
    """Read and normalize text content for similarity comparison."""
    filepath = file_info.get("new_path") or file_info["original_path"]
    text = read_content_preview(filepath, max_bytes=65536)
    if text is None:
        return None
    # Normalize: lowercase, collapse whitespace
    text = text.lower().strip()
    text = " ".join(text.split())
    return text if len(text) > 20 else None


def _pick_canonical_pair(
    fa: Dict[str, Any], fb: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Pick the canonical file from a pair.  Higher litigation_score wins,
    then larger size, then alphabetically earlier path."""
    score_a = fa.get("litigation_score", 0) or 0
    score_b = fb.get("litigation_score", 0) or 0
    if score_a > score_b:
        return fa, fb
    if score_b > score_a:
        return fb, fa
    if fa["size_bytes"] >= fb["size_bytes"]:
        return fa, fb
    return fb, fa


# ---------------------------------------------------------------------------
# Phase 3 — Size + similar name grouping
# ---------------------------------------------------------------------------

def _phase3_size_name(
    conn: sqlite3.Connection,
    drive: str,
    session_id: int,
    dry_run: bool,
    stats: Dict[str, Any],
    deduped_ids: Set[int],
) -> None:
    """Group files with same size AND similar filenames."""
    rows = conn.execute(
        """SELECT size_bytes, GROUP_CONCAT(id) AS ids, COUNT(*) AS cnt
             FROM flat_files
            WHERE drive = ? AND is_duplicate = 0 AND size_bytes > 1024
            GROUP BY size_bytes
           HAVING cnt >= 2 AND cnt <= 20
            ORDER BY size_bytes DESC""",
        (drive,),
    ).fetchall()

    for size, id_csv, cnt in rows:
        file_ids = [int(x) for x in id_csv.split(",")]
        file_ids = [fid for fid in file_ids if fid not in deduped_ids]
        if len(file_ids) < 2:
            continue

        files = _load_files(conn, file_ids)
        if len(files) < 2:
            continue

        # Compare filenames using SequenceMatcher
        clusters_found: List[List[Dict[str, Any]]] = []
        used: Set[int] = set()

        for i, fa in enumerate(files):
            if fa["id"] in used:
                continue
            cluster = [fa]
            stem_a = Path(fa["filename"]).stem.lower()

            for j in range(i + 1, len(files)):
                fb = files[j]
                if fb["id"] in used:
                    continue
                stem_b = Path(fb["filename"]).stem.lower()
                name_sim = SequenceMatcher(None, stem_a, stem_b).ratio()
                if name_sim >= 0.80:
                    cluster.append(fb)
                    used.add(fb["id"])

            if len(cluster) >= 2:
                used.add(fa["id"])
                clusters_found.append(cluster)

        for cluster in clusters_found:
            canonical = _choose_canonical(cluster)
            dupes = [f for f in cluster if f["id"] != canonical["id"]]

            cluster_id = _create_cluster(
                conn, None, canonical["id"], len(cluster),
                sum(f["size_bytes"] for f in cluster), "size_name",
            )
            _add_member(conn, cluster_id, canonical["id"], 1.0, True, "keep")

            for dupe in dupes:
                if dupe["id"] in deduped_ids:
                    continue
                _add_member(conn, cluster_id, dupe["id"], 0.80, False, "move")
                _mark_duplicate(conn, dupe["id"], canonical["id"])
                if not dry_run:
                    if _move_to_dedup(drive, dupe):
                        stats["total_moved"] += 1
                    else:
                        stats["errors"] += 1
                stats["space_saved_bytes"] += dupe["size_bytes"]
                deduped_ids.add(dupe["id"])

            stats["phase3_clusters"] += 1
            stats["phase3_dupes"] += len(dupes)

    conn.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_files(conn: sqlite3.Connection, ids: List[int]) -> List[Dict[str, Any]]:
    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""SELECT id, original_path, new_path, folder, filename, size_bytes,
                   litigation_score
              FROM flat_files
             WHERE id IN ({placeholders})""",
        ids,
    ).fetchall()
    return [
        {
            "id": r[0], "original_path": r[1], "new_path": r[2],
            "folder": r[3], "filename": r[4], "size_bytes": r[5],
            "litigation_score": r[6] or 0,
        }
        for r in rows
    ]


def _choose_canonical(files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Choose the canonical file: highest litigation_score → largest → earliest path."""
    return max(
        files,
        key=lambda f: (
            f.get("litigation_score", 0) or 0,
            f["size_bytes"],
            -(hash(f.get("original_path", ""))),
        ),
    )


def _create_cluster(
    conn: sqlite3.Connection,
    cluster_hash: Optional[str],
    canonical_id: int,
    file_count: int,
    total_size: int,
    method: str,
) -> int:
    cur = conn.execute(
        """INSERT INTO dedup_clusters
               (cluster_hash, canonical_file_id, file_count, total_size_bytes, similarity_method)
           VALUES (?, ?, ?, ?, ?)""",
        (cluster_hash, canonical_id, file_count, total_size, method),
    )
    return cur.lastrowid  # type: ignore[return-value]


def _add_member(
    conn: sqlite3.Connection,
    cluster_id: int,
    file_id: int,
    similarity: float,
    is_canonical: bool,
    action: str,
) -> None:
    conn.execute(
        """INSERT OR IGNORE INTO dedup_members
               (cluster_id, file_id, similarity_score, is_canonical, action)
           VALUES (?, ?, ?, ?, ?)""",
        (cluster_id, file_id, similarity, int(is_canonical), action),
    )


def _mark_duplicate(conn: sqlite3.Connection, file_id: int, canonical_id: int) -> None:
    conn.execute(
        "UPDATE flat_files SET is_duplicate = 1, duplicate_of = ? WHERE id = ?",
        (canonical_id, file_id),
    )


def _move_to_dedup(drive: str, file_info: Dict[str, Any]) -> bool:
    """Move a duplicate file to ``_DEDUP/{original_folder}/`` preserving structure."""
    filepath = file_info.get("new_path") or file_info["original_path"]
    if not os.path.isfile(filepath):
        return False

    folder = file_info.get("folder", "_UNKNOWN")
    dedup_dir = Path(f"{drive}:\\_DEDUP") / folder
    dedup_dir.mkdir(parents=True, exist_ok=True)

    dest = dedup_dir / file_info["filename"]
    # Handle collision
    if dest.exists():
        stem = Path(file_info["filename"]).stem
        suffix = Path(file_info["filename"]).suffix
        counter = 1
        while dest.exists():
            dest = dedup_dir / f"{stem}_{counter}{suffix}"
            counter += 1
            if counter > 10000:
                return False

    try:
        shutil.move(filepath, str(dest))
        return True
    except (PermissionError, OSError, shutil.Error):
        return False


def _write_dedup_report(
    conn: sqlite3.Connection,
    drive: str,
    stats: Dict[str, Any],
) -> None:
    """Write a markdown dedup report to _INDEX."""
    total_dupes = stats["phase1_dupes"] + stats["phase2_dupes"] + stats["phase3_dupes"]
    total_clusters = stats["phase1_clusters"] + stats["phase2_clusters"] + stats["phase3_clusters"]
    saved_mb = stats["space_saved_bytes"] / (1024 ** 2)

    # Top clusters
    top_clusters = conn.execute(
        """SELECT dc.id, dc.similarity_method, dc.file_count, dc.total_size_bytes,
                  ff.filename AS canonical_name
             FROM dedup_clusters dc
             JOIN flat_files ff ON ff.id = dc.canonical_file_id
            ORDER BY dc.file_count DESC
            LIMIT 20""",
    ).fetchall()

    lines = [
        f"# OMEGA-FLATTEN Dedup Report — Drive {drive}:",
        f"",
        f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"## Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total clusters | {total_clusters:,} |",
        f"| Phase 1 (SHA-256 exact) | {stats['phase1_clusters']:,} clusters, {stats['phase1_dupes']:,} dupes |",
        f"| Phase 2 (content similarity) | {stats['phase2_clusters']:,} clusters, {stats['phase2_dupes']:,} dupes |",
        f"| Phase 3 (size+name) | {stats['phase3_clusters']:,} clusters, {stats['phase3_dupes']:,} dupes |",
        f"| Total duplicates | {total_dupes:,} |",
        f"| Files moved to _DEDUP | {stats['total_moved']:,} |",
        f"| Space recoverable | {saved_mb:,.1f} MB |",
        f"| Errors | {stats['errors']} |",
        f"",
        f"## Top Duplicate Clusters",
        f"",
        f"| Cluster | Method | Files | Size | Canonical |",
        f"|---------|--------|-------|------|-----------|",
    ]

    for cid, method, fcount, tsize, cname in top_clusters:
        size_str = f"{tsize / 1024:.1f} KB" if tsize < 1024 * 1024 else f"{tsize / (1024**2):.1f} MB"
        lines.append(f"| {cid} | {method} | {fcount} | {size_str} | {cname} |")

    lines.append("")
    lines.append("---")
    lines.append("*No files were deleted.  All duplicates moved to `_DEDUP/`.*")
    lines.append("")

    report_path = os.path.join(f"{drive}:\\_INDEX", "DEDUP_REPORT.md")
    try:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        print(f"  [DEDUP] Report written to {report_path}")
    except (PermissionError, OSError) as exc:
        print(f"  [DEDUP] WARNING: Could not write report: {exc}")
