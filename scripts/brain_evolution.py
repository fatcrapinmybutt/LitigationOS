#!/usr/bin/env python
"""THEMANBEARPIG Legal Brain — Self-Evolution Engine.

Autonomously improves the graph: discovers connections, re-scores chains,
resolves gaps, manages versions, and optimizes parameters.

Usage:
    python -I scripts/brain_evolution.py                # Full evolution cycle
    python -I scripts/brain_evolution.py --health       # Health check only
    python -I scripts/brain_evolution.py --discover     # Find new connections
    python -I scripts/brain_evolution.py --rescore      # Re-score chains
    python -I scripts/brain_evolution.py --gaps         # Check gap resolution
    python -I scripts/brain_evolution.py --version      # Create version snapshot
    python -I scripts/brain_evolution.py --optimize     # Parameter analysis
    python -I scripts/brain_evolution.py --stats        # Print brain stats
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
import shutil
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────────

REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
BRAIN_DB = REPO_ROOT / "mbp_brain.db"
LOG_DIR = REPO_ROOT / "logs"
SNAPSHOT_DIR = LOG_DIR / "brain_snapshots"
LOG_FILE = LOG_DIR / "brain_evolution.log"

LANE_KEYWORDS: dict[str, list[str]] = {
    "A": ["custody", "parenting", "001507", "child", "visitation", "foc",
          "best interest", "722.23", "parenting time"],
    "B": ["shady oaks", "eviction", "housing", "trailer", "002760",
          "habitability", "mobile home", "whitehall"],
    "C": ["federal", "1983", "constitutional", "civil rights",
          "qualified immunity", "monell", "1343"],
    "D": ["ppo", "protection order", "5907", "contempt", "stalking",
          "harassment", "personal protection"],
    "E": ["mcneill", "judicial", "bias", "jtc", "canon", "misconduct",
          "benchbook", "ex parte", "recusal"],
    "F": ["coa", "366810", "appeal", "appellant", "appellee",
          "brief", "appendix", "7.212"],
}

BINDING_MULTIPLIERS: dict[str | None, float] = {
    "mandatory": 1.0,
    "persuasive": 0.7,
    "informative": 0.4,
    None: 0.5,
}

# ── Logging ────────────────────────────────────────────────────────────


def _setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fmt = "%(asctime)s | %(levelname)-7s | %(funcName)-25s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logger = logging.getLogger("brain_evolution")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    logger.addHandler(ch)

    fh = logging.FileHandler(str(LOG_FILE), encoding="utf-8")
    fh.setFormatter(logging.Formatter(fmt, datefmt=datefmt))
    logger.addHandler(fh)

    return logger


log = _setup_logging()

# ── DB Connection ──────────────────────────────────────────────────────


def get_brain_conn(readonly: bool = False) -> sqlite3.Connection:
    """Open mbp_brain.db with production PRAGMAs."""
    if not BRAIN_DB.exists():
        log.error("Brain DB not found: %s", BRAIN_DB)
        sys.exit(1)

    if readonly:
        uri = f"file:///{BRAIN_DB.as_posix()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
    else:
        conn = sqlite3.connect(str(BRAIN_DB))

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA temp_store = MEMORY")
    return conn


def _log_operation(
    conn: sqlite3.Connection,
    operation: str,
    input_params: dict,
    output_summary: str,
    nodes_touched: int,
    edges_traversed: int,
    duration_ms: float,
) -> None:
    """Record an operation in brain_ops for auditing."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(brain_ops)")}
    if "created_at" in cols:
        conn.execute(
            "INSERT INTO brain_ops (operation, input_params, output_summary,"
            " nodes_touched, edges_traversed, duration_ms, created_at)"
            " VALUES (?,?,?,?,?,?,datetime('now'))",
            (operation, json.dumps(input_params), output_summary,
             nodes_touched, edges_traversed, duration_ms),
        )
    else:
        conn.execute(
            "INSERT INTO brain_ops (operation, input_params, output_summary,"
            " nodes_touched, edges_traversed, duration_ms)"
            " VALUES (?,?,?,?,?,?)",
            (operation, json.dumps(input_params), output_summary,
             nodes_touched, edges_traversed, duration_ms),
        )
    conn.commit()


def _parse_chain_path(raw: str | None) -> list[str]:
    """Robustly parse a chain_path stored as JSON array, pipe, or CSV."""
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except (json.JSONDecodeError, TypeError):
            pass
    if "|" in raw:
        return [p.strip() for p in raw.split("|") if p.strip()]
    if "," in raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    return [raw] if raw else []


# ── 1. Connection Discovery ───────────────────────────────────────────


def find_new_connections(conn: sqlite3.Connection) -> list[tuple]:
    """Scan the graph for potential new edges using text matching.

    Returns a list of (source_id, target_id, edge_type, weight, evidence_note).
    """
    t0 = time.perf_counter()
    new_edges: list[tuple] = []

    # Pre-load existing edge triplets for the types we create
    existing_triplets: set[tuple[str, str, str]] = set()
    for row in conn.execute(
        "SELECT source_id, target_id, edge_type FROM edges"
        " WHERE edge_type IN ('RELATED','TEMPORALLY_PROXIMATE','CITES',"
        "'COMMITTED_BY','SUFFERED_BY')"
    ):
        existing_triplets.add((row[0], row[1], row[2]))

    def _already_exists(s: str, t: str, et: str) -> bool:
        return (s, t, et) in existing_triplets or (t, s, et) in existing_triplets

    # ── 1a. Cross-lane connections ─────────────────────────────────────
    log.info("Scanning for cross-lane connections...")
    evidence_rows = conn.execute(
        "SELECT id, lane, label, description FROM nodes"
        " WHERE layer = 'EVIDENCE' AND description IS NOT NULL"
        " AND description != '' AND lane IS NOT NULL"
    ).fetchall()

    cross_count = 0
    for node in evidence_rows:
        node_lane = node["lane"]
        text_lower = ((node["label"] or "") + " " + (node["description"] or "")).lower()

        for other_lane, keywords in LANE_KEYWORDS.items():
            if other_lane == node_lane:
                continue
            for kw in keywords:
                if kw in text_lower:
                    target = conn.execute(
                        "SELECT id FROM nodes WHERE lane = ? AND label LIKE ?"
                        " LIMIT 1",
                        (other_lane, f"%{kw}%"),
                    ).fetchone()
                    if target and not _already_exists(node["id"], target["id"], "RELATED"):
                        new_edges.append((
                            node["id"], target["id"], "RELATED", 0.4,
                            f"cross-lane:{node_lane}->{other_lane} kw:{kw}",
                        ))
                        existing_triplets.add((node["id"], target["id"], "RELATED"))
                        cross_count += 1
                    break  # one match per target lane per node
    log.info("  Cross-lane candidates: %d", cross_count)

    # ── 1b. Temporal proximity (events within 7 days, different lanes) ─
    log.info("Scanning for temporal proximity connections...")
    temporal_pairs = conn.execute(
        "SELECT a.id AS a_id, b.id AS b_id,"
        " ABS(julianday(a.date_start) - julianday(b.date_start)) AS day_diff"
        " FROM nodes a JOIN nodes b ON a.id < b.id"
        " WHERE a.date_start IS NOT NULL AND b.date_start IS NOT NULL"
        " AND a.date_start != '' AND b.date_start != ''"
        " AND ABS(julianday(a.date_start) - julianday(b.date_start)) <= 7"
        " AND a.layer = b.layer AND a.lane != b.lane"
        " LIMIT 500"
    ).fetchall()

    temporal_count = 0
    for pair in temporal_pairs:
        if not _already_exists(pair["a_id"], pair["b_id"], "TEMPORALLY_PROXIMATE"):
            weight = max(0.3, 1.0 - (pair["day_diff"] / 7.0) * 0.7)
            new_edges.append((
                pair["a_id"], pair["b_id"], "TEMPORALLY_PROXIMATE",
                round(weight, 4),
                f"temporal:{pair['day_diff']:.1f}d",
            ))
            existing_triplets.add((pair["a_id"], pair["b_id"], "TEMPORALLY_PROXIMATE"))
            temporal_count += 1
    log.info("  Temporal proximity candidates: %d", temporal_count)

    # ── 1c. Citation completeness ──────────────────────────────────────
    log.info("Scanning for missing citation edges...")
    authority_rows = conn.execute(
        "SELECT id, label, description FROM nodes"
        " WHERE layer = 'AUTHORITY' AND (label IS NOT NULL OR description IS NOT NULL)"
    ).fetchall()

    rule_re = re.compile(r"MC[RL]\s*\d+\.\d+", re.IGNORECASE)
    rule_to_nodes: dict[str, list[str]] = defaultdict(list)
    for node in authority_rows:
        text = (node["label"] or "") + " " + (node["description"] or "")
        for match in rule_re.findall(text):
            normalized = match.upper().replace(" ", "")
            rule_to_nodes[normalized].append(node["id"])

    cite_count = 0
    for _rule, node_ids in rule_to_nodes.items():
        if len(node_ids) < 2:
            continue
        for i in range(len(node_ids)):
            for j in range(i + 1, min(i + 5, len(node_ids))):
                if not _already_exists(node_ids[i], node_ids[j], "CITES"):
                    new_edges.append((
                        node_ids[i], node_ids[j], "CITES", 0.6,
                        f"shared_citation:{_rule}",
                    ))
                    existing_triplets.add((node_ids[i], node_ids[j], "CITES"))
                    cite_count += 1
    log.info("  Citation completeness candidates: %d", cite_count)

    # ── 1d. Actor-violation linking ────────────────────────────────────
    log.info("Scanning for actor-violation links...")
    actors = conn.execute(
        "SELECT id, label FROM nodes WHERE layer = 'ACTOR' AND label IS NOT NULL"
    ).fetchall()
    violations = conn.execute(
        "SELECT id, description FROM nodes"
        " WHERE layer = 'VIOLATION' AND description IS NOT NULL AND description != ''"
    ).fetchall()

    actor_viol_count = 0
    for actor in actors:
        name = actor["label"].strip()
        if len(name) < 3:
            continue
        name_lower = name.lower()
        for viol in violations:
            if name_lower in (viol["description"] or "").lower():
                if not _already_exists(viol["id"], actor["id"], "COMMITTED_BY"):
                    new_edges.append((
                        viol["id"], actor["id"], "COMMITTED_BY", 0.5,
                        f"actor_mention:{name}",
                    ))
                    existing_triplets.add((viol["id"], actor["id"], "COMMITTED_BY"))
                    actor_viol_count += 1
    log.info("  Actor-violation candidates: %d", actor_viol_count)

    elapsed = time.perf_counter() - t0
    log.info("Connection discovery complete: %d candidates in %.1fs",
             len(new_edges), elapsed)

    _log_operation(
        conn, "find_new_connections",
        {"cross_lane": cross_count, "temporal": temporal_count,
         "citation": cite_count, "actor_viol": actor_viol_count},
        f"{len(new_edges)} candidates found",
        len(evidence_rows) + len(authority_rows) + len(actors) + len(violations),
        0, elapsed * 1000,
    )
    return new_edges


def insert_new_edges(
    conn: sqlite3.Connection,
    new_edges: list[tuple],
) -> int:
    """Insert discovered edges, skipping duplicates. Returns count inserted."""
    if not new_edges:
        log.info("No new edges to insert.")
        return 0

    # Verify schema
    cols = {r[1] for r in conn.execute("PRAGMA table_info(edges)")}
    has_evidence = "evidence" in cols

    inserted = 0
    for src, tgt, etype, weight, evidence_note in new_edges:
        existing = conn.execute(
            "SELECT 1 FROM edges WHERE source_id = ? AND target_id = ?"
            " AND edge_type = ?",
            (src, tgt, etype),
        ).fetchone()
        if existing:
            continue

        if has_evidence:
            conn.execute(
                "INSERT INTO edges (source_id, target_id, edge_type, weight,"
                " evidence, source_table) VALUES (?,?,?,?,?,?)",
                (src, tgt, etype, weight, evidence_note, "brain_evolution"),
            )
        else:
            conn.execute(
                "INSERT INTO edges (source_id, target_id, edge_type, weight,"
                " source_table) VALUES (?,?,?,?,?)",
                (src, tgt, etype, weight, "brain_evolution"),
            )
        inserted += 1

        if inserted % 500 == 0:
            conn.commit()

    conn.commit()
    log.info("Edges inserted: %d / %d candidates", inserted, len(new_edges))
    return inserted


# ── 2. Chain Re-scoring ───────────────────────────────────────────────


def rescore_chains(conn: sqlite3.Connection) -> dict:
    """Re-compute chain strength scores from current edge weights and node attributes."""
    t0 = time.perf_counter()
    chains = conn.execute(
        "SELECT id, chain_path, strength_score FROM chains"
    ).fetchall()
    log.info("Re-scoring %d chains...", len(chains))

    improved = degraded = unchanged = 0

    for chain in chains:
        chain_id = chain["id"]
        old_score = chain["strength_score"] or 0.0
        path = _parse_chain_path(chain["chain_path"])

        if len(path) < 2:
            unchanged += 1
            continue

        edge_weight_product = 1.0
        max_severity = 0.0
        max_confidence = 0.0
        best_binding = 0.5

        for i in range(len(path) - 1):
            edge = conn.execute(
                "SELECT weight FROM edges"
                " WHERE source_id = ? AND target_id = ?"
                " ORDER BY weight DESC LIMIT 1",
                (path[i], path[i + 1]),
            ).fetchone()
            if not edge:
                edge = conn.execute(
                    "SELECT weight FROM edges"
                    " WHERE source_id = ? AND target_id = ?"
                    " ORDER BY weight DESC LIMIT 1",
                    (path[i + 1], path[i]),
                ).fetchone()
                if edge:
                    w = (edge["weight"] if edge["weight"] else 0.5) * 0.9
                else:
                    w = 0.1
            else:
                w = edge["weight"] if edge["weight"] else 0.5
            edge_weight_product *= w

        for node_id in path:
            node = conn.execute(
                "SELECT severity, confidence, binding_strength"
                " FROM nodes WHERE id = ?",
                (node_id,),
            ).fetchone()
            if not node:
                continue
            sev = node["severity"] or 0
            conf = node["confidence"] or 0
            bs = node["binding_strength"]
            if sev > max_severity:
                max_severity = sev
            if conf > max_confidence:
                max_confidence = conf
            mult = BINDING_MULTIPLIERS.get(bs, 0.5)
            if mult > best_binding:
                best_binding = mult

        severity_factor = max_severity / 10.0 if max_severity > 0 else 0.5
        confidence_factor = max_confidence if max_confidence > 0 else 0.5

        new_score = (
            edge_weight_product
            * severity_factor
            * best_binding
            * confidence_factor
        )
        new_score = min(1.0, max(0.0, new_score))

        conn.execute(
            "UPDATE chains SET strength_score = ?, total_weight = ? WHERE id = ?",
            (round(new_score, 6), round(edge_weight_product, 6), chain_id),
        )

        delta = new_score - old_score
        if delta > 0.001:
            improved += 1
        elif delta < -0.001:
            degraded += 1
        else:
            unchanged += 1

    conn.commit()
    elapsed = time.perf_counter() - t0
    log.info(
        "Chains re-scored: improved=%d degraded=%d unchanged=%d (%.1fs)",
        improved, degraded, unchanged, elapsed,
    )

    _log_operation(
        conn, "rescore_chains",
        {"total_chains": len(chains)},
        f"improved={improved}, degraded={degraded}, unchanged={unchanged}",
        0, 0, elapsed * 1000,
    )
    return {
        "total": len(chains),
        "improved": improved,
        "degraded": degraded,
        "unchanged": unchanged,
    }


# ── 3. Gap Resolution Tracking ────────────────────────────────────────


_GAP_QUERIES: dict[str, str] = {
    "VIOLATION_NO_EVIDENCE": (
        "SELECT 1 FROM edges WHERE target_id = ? AND edge_type = 'PROVES' LIMIT 1"
    ),
    "VIOLATION_NO_AUTHORITY": (
        "SELECT 1 FROM edges WHERE source_id = ? AND edge_type = 'GOVERNED_BY' LIMIT 1"
    ),
    "FILING_NO_EXHIBIT": (
        "SELECT 1 FROM edges"
        " WHERE (source_id = ? OR target_id = ?)"
        " AND edge_type IN ('PROVES','RELATED','ASSIGNED_TO') LIMIT 1"
    ),
    "VIOLATION_UNREACHABLE": (
        "SELECT 1 FROM edges WHERE source_id = ? OR target_id = ? LIMIT 1"
    ),
}


def check_gaps(conn: sqlite3.Connection) -> dict:
    """Check if any unresolved gaps have been satisfied by new data."""
    t0 = time.perf_counter()
    unresolved = conn.execute(
        "SELECT id, gap_type, node_id FROM gaps WHERE resolved = 0"
    ).fetchall()
    log.info("Checking %d unresolved gaps...", len(unresolved))

    resolved_count = 0
    for gap in unresolved:
        gap_type = gap["gap_type"]
        node_id = gap["node_id"]
        is_resolved = False

        query = _GAP_QUERIES.get(gap_type)
        if query:
            param_count = query.count("?")
            params = (node_id,) * param_count
            is_resolved = conn.execute(query, params).fetchone() is not None
        else:
            # Generic fallback: does the node have >=2 edges now?
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM edges"
                " WHERE source_id = ? OR target_id = ?",
                (node_id, node_id),
            ).fetchone()
            is_resolved = (row["c"] or 0) >= 2

        if is_resolved:
            conn.execute("UPDATE gaps SET resolved = 1 WHERE id = ?", (gap["id"],))
            resolved_count += 1

    conn.commit()
    remaining = conn.execute(
        "SELECT COUNT(*) AS c FROM gaps WHERE resolved = 0"
    ).fetchone()["c"]
    elapsed = time.perf_counter() - t0

    log.info("Gaps resolved: %d, remaining: %d (%.1fs)",
             resolved_count, remaining, elapsed)

    _log_operation(
        conn, "check_gaps",
        {"checked": len(unresolved)},
        f"resolved={resolved_count}, remaining={remaining}",
        0, 0, elapsed * 1000,
    )
    return {
        "checked": len(unresolved),
        "resolved": resolved_count,
        "remaining": remaining,
    }


# ── 4. Version Management ─────────────────────────────────────────────


def create_version(conn: sqlite3.Connection) -> dict:
    """Create a new version record; snapshot brain DB every 10 versions."""
    t0 = time.perf_counter()

    stats = conn.execute(
        "SELECT"
        " (SELECT COUNT(*) FROM nodes)              AS nc,"
        " (SELECT COUNT(*) FROM edges)              AS ec,"
        " (SELECT COUNT(*) FROM chains)             AS cc,"
        " (SELECT COUNT(*) FROM gaps WHERE resolved = 0) AS gc"
    ).fetchone()
    nc, ec, cc, gc = stats["nc"], stats["ec"], stats["cc"], stats["gc"]

    last = conn.execute(
        "SELECT version, node_count, edge_count, chain_count"
        " FROM versions ORDER BY version DESC LIMIT 1"
    ).fetchone()

    if last:
        mutations = {
            "nodes_delta": nc - (last["node_count"] or 0),
            "edges_delta": ec - (last["edge_count"] or 0),
            "chains_delta": cc - (last["chain_count"] or 0),
            "previous_version": last["version"],
        }
        next_ver = last["version"] + 1
    else:
        mutations = {
            "nodes_delta": nc,
            "edges_delta": ec,
            "chains_delta": cc,
            "previous_version": 0,
        }
        next_ver = 1

    # Snapshot every 10 versions
    snapshot_path = None
    if next_ver % 10 == 0:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        dest = SNAPSHOT_DIR / f"mbp_brain_v{next_ver}.db"
        log.info("Creating snapshot -> %s", dest)
        conn.commit()
        try:
            shutil.copy2(str(BRAIN_DB), str(dest))
            snapshot_path = str(dest)
            log.info("Snapshot saved: %.1f MB",
                     dest.stat().st_size / (1024 * 1024))
        except OSError as exc:
            log.warning("Snapshot failed: %s", exc)

    # Adaptive INSERT (gap_count column may or may not exist)
    ver_cols = {r[1] for r in conn.execute("PRAGMA table_info(versions)")}
    if "gap_count" in ver_cols:
        conn.execute(
            "INSERT INTO versions"
            " (node_count, edge_count, chain_count, gap_count,"
            "  mutations, snapshot_path)"
            " VALUES (?,?,?,?,?,?)",
            (nc, ec, cc, gc, json.dumps(mutations), snapshot_path),
        )
    else:
        conn.execute(
            "INSERT INTO versions"
            " (node_count, edge_count, chain_count, mutations, snapshot_path)"
            " VALUES (?,?,?,?,?)",
            (nc, ec, cc, json.dumps(mutations), snapshot_path),
        )
    conn.commit()

    elapsed = time.perf_counter() - t0
    log.info("Version v%d created: nodes=%d edges=%d chains=%d gaps=%d (%.1fs)",
             next_ver, nc, ec, cc, gc, elapsed)

    return {
        "version": next_ver,
        "node_count": nc,
        "edge_count": ec,
        "chain_count": cc,
        "gap_count": gc,
        "mutations": mutations,
        "snapshot_path": snapshot_path,
    }


# ── 5. Parameter Optimization ─────────────────────────────────────────


def optimize_params(conn: sqlite3.Connection) -> dict:
    """Analyze which edge types and evidence categories drive strong chains."""
    t0 = time.perf_counter()
    log.info("Analyzing parameter effectiveness...")

    chains = conn.execute(
        "SELECT id, chain_path, strength_score FROM chains"
        " ORDER BY strength_score DESC"
    ).fetchall()

    strong_chains = [c for c in chains if (c["strength_score"] or 0) >= 0.5]
    weak_chains = [c for c in chains if (c["strength_score"] or 0) < 0.2]

    def _edge_types_in_chain(chain_row: sqlite3.Row) -> set[str]:
        path = _parse_chain_path(chain_row["chain_path"])
        types: set[str] = set()
        for i in range(len(path) - 1):
            for row in conn.execute(
                "SELECT edge_type FROM edges"
                " WHERE (source_id = ? AND target_id = ?)"
                "    OR (source_id = ? AND target_id = ?)",
                (path[i], path[i + 1], path[i + 1], path[i]),
            ):
                types.add(row["edge_type"])
        return types

    et_strong: dict[str, int] = defaultdict(int)
    et_weak: dict[str, int] = defaultdict(int)

    for ch in strong_chains:
        for et in _edge_types_in_chain(ch):
            et_strong[et] += 1
    for ch in weak_chains:
        for et in _edge_types_in_chain(ch):
            et_weak[et] += 1

    # Edge weight statistics
    edge_stats = conn.execute(
        "SELECT edge_type,"
        " COUNT(*) AS cnt, AVG(weight) AS avg_w,"
        " MIN(weight) AS min_w, MAX(weight) AS max_w"
        " FROM edges GROUP BY edge_type ORDER BY cnt DESC"
    ).fetchall()

    # Evidence categories in chains
    evidence_in_chains = conn.execute(
        "SELECT n.node_type, COUNT(DISTINCT c.id) AS chain_cnt,"
        " AVG(c.strength_score) AS avg_str"
        " FROM chains c, nodes n"
        " WHERE c.evidence_ids LIKE '%' || n.id || '%'"
        " AND n.layer = 'EVIDENCE'"
        " GROUP BY n.node_type ORDER BY avg_str DESC"
    ).fetchall()

    # Build suggestions
    suggestions: list[str] = []
    for row in edge_stats:
        et = row["edge_type"]
        avg_w = row["avg_w"] or 0
        s_cnt = et_strong.get(et, 0)
        w_cnt = et_weak.get(et, 0)
        if avg_w < 0.3 and s_cnt == 0:
            suggestions.append(
                f"BOOST: '{et}' avg weight {avg_w:.2f}, "
                f"appears in 0 strong chains"
            )
        elif s_cnt > 0 and w_cnt == 0:
            suggestions.append(
                f"STRONG: '{et}' exclusive to strong chains ({s_cnt}×)"
            )
        elif w_cnt > s_cnt * 2 and w_cnt > 2:
            suggestions.append(
                f"REVIEW: '{et}' 2× more in weak ({w_cnt}) than strong ({s_cnt})"
            )

    elapsed = time.perf_counter() - t0

    # Print report
    log.info("─── Parameter Optimization Report ───")
    log.info("Strong chains (>= 0.5): %d", len(strong_chains))
    log.info("Weak   chains (< 0.2): %d", len(weak_chains))
    log.info("")
    log.info("Edge type in strong vs weak chains:")
    all_types = sorted(set(et_strong) | set(et_weak))
    for et in all_types:
        log.info("  %-25s  strong=%3d  weak=%3d",
                 et, et_strong.get(et, 0), et_weak.get(et, 0))

    log.info("")
    log.info("Edge weight statistics:")
    log.info("  %-25s  %8s  %8s  %8s  %8s",
             "Type", "Count", "Avg", "Min", "Max")
    for r in edge_stats:
        log.info("  %-25s  %8d  %8.3f  %8.3f  %8.3f",
                 r["edge_type"], r["cnt"],
                 r["avg_w"] or 0, r["min_w"] or 0, r["max_w"] or 0)

    if evidence_in_chains:
        log.info("")
        log.info("Evidence categories by chain strength:")
        for r in evidence_in_chains:
            log.info("  %-25s  chains=%3d  avg_str=%.3f",
                     r["node_type"] or "unknown",
                     r["chain_cnt"], r["avg_str"] or 0)

    log.info("")
    for s in suggestions:
        log.info("  -> %s", s)
    if not suggestions:
        log.info("  -> No immediate optimization suggestions.")

    _log_operation(
        conn, "optimize_params",
        {"strong_chains": len(strong_chains), "weak_chains": len(weak_chains)},
        json.dumps({"suggestions": suggestions}),
        0, 0, elapsed * 1000,
    )
    return {
        "strong": len(strong_chains),
        "weak": len(weak_chains),
        "suggestions": suggestions,
    }


# ── 6. Health Check ───────────────────────────────────────────────────


def health_check(conn: sqlite3.Connection) -> dict:
    """Run comprehensive diagnostics on the brain graph."""
    t0 = time.perf_counter()
    log.info("Running brain health check...")
    report: dict = {}

    # ── Orphan nodes ───────────────────────────────────────────────────
    orphans = conn.execute(
        "SELECT n.layer, COUNT(*) AS cnt FROM nodes n"
        " WHERE NOT EXISTS ("
        "   SELECT 1 FROM edges e"
        "   WHERE e.source_id = n.id OR e.target_id = n.id"
        " ) GROUP BY n.layer ORDER BY cnt DESC"
    ).fetchall()

    total_orphans = sum(r["cnt"] for r in orphans)
    report["orphan_nodes"] = {r["layer"]: r["cnt"] for r in orphans}
    report["total_orphans"] = total_orphans

    log.info("Orphan nodes (no edges): %d total", total_orphans)
    for r in orphans:
        log.info("  %-15s %6d", r["layer"], r["cnt"])

    # ── Connectivity ───────────────────────────────────────────────────
    total_nodes = conn.execute(
        "SELECT COUNT(*) AS c FROM nodes"
    ).fetchone()["c"]
    connected_nodes = conn.execute(
        "SELECT COUNT(*) AS c FROM nodes n"
        " WHERE EXISTS ("
        "   SELECT 1 FROM edges e"
        "   WHERE e.source_id = n.id OR e.target_id = n.id"
        " )"
    ).fetchone()["c"]

    report["total_nodes"] = total_nodes
    report["connected_nodes"] = connected_nodes
    report["isolated_nodes"] = total_nodes - connected_nodes
    conn_pct = (connected_nodes / total_nodes * 100) if total_nodes else 0
    log.info("Connectivity: %d / %d nodes connected (%.1f%%)",
             connected_nodes, total_nodes, conn_pct)

    # ── Edge weight distribution ───────────────────────────────────────
    edge_dist = conn.execute(
        "SELECT edge_type, COUNT(*) AS cnt,"
        " ROUND(AVG(weight),4)  AS avg_w,"
        " ROUND(MIN(weight),4)  AS min_w,"
        " ROUND(MAX(weight),4)  AS max_w,"
        " ROUND(AVG(weight*weight)-AVG(weight)*AVG(weight),6) AS var_w"
        " FROM edges GROUP BY edge_type ORDER BY cnt DESC"
    ).fetchall()

    report["edge_distribution"] = []
    log.info("Edge weight distribution:")
    log.info("  %-25s %8s %8s %8s %8s %8s",
             "Type", "Count", "Avg", "Min", "Max", "StdDev")
    for r in edge_dist:
        var = r["var_w"] or 0
        sd = math.sqrt(max(0.0, var))
        report["edge_distribution"].append({
            "type": r["edge_type"], "count": r["cnt"],
            "avg": r["avg_w"], "min": r["min_w"],
            "max": r["max_w"], "stddev": round(sd, 4),
        })
        log.info("  %-25s %8d %8.4f %8.4f %8.4f %8.4f",
                 r["edge_type"], r["cnt"],
                 r["avg_w"] or 0, r["min_w"] or 0,
                 r["max_w"] or 0, sd)

    # ── Chain coverage ─────────────────────────────────────────────────
    violation_count = conn.execute(
        "SELECT COUNT(*) AS c FROM nodes WHERE layer = 'VIOLATION'"
    ).fetchone()["c"]
    evidence_count = conn.execute(
        "SELECT COUNT(*) AS c FROM nodes WHERE layer = 'EVIDENCE'"
    ).fetchone()["c"]

    violations_in_chains = conn.execute(
        "SELECT COUNT(DISTINCT n.id) AS c FROM nodes n, chains ch"
        " WHERE n.layer = 'VIOLATION'"
        " AND ch.chain_path LIKE '%' || n.id || '%'"
    ).fetchone()["c"]
    evidence_in_chains = conn.execute(
        "SELECT COUNT(DISTINCT n.id) AS c FROM nodes n, chains ch"
        " WHERE n.layer = 'EVIDENCE'"
        " AND (ch.evidence_ids LIKE '%' || n.id || '%'"
        "  OR ch.chain_path LIKE '%' || n.id || '%')"
    ).fetchone()["c"]

    viol_pct = (violations_in_chains / violation_count * 100) if violation_count else 0
    evid_pct = (evidence_in_chains / evidence_count * 100) if evidence_count else 0

    report["chain_coverage"] = {
        "violations_total": violation_count,
        "violations_in_chains": violations_in_chains,
        "violations_pct": round(viol_pct, 1),
        "evidence_total": evidence_count,
        "evidence_in_chains": evidence_in_chains,
        "evidence_pct": round(evid_pct, 1),
    }
    log.info("Chain coverage:")
    log.info("  Violations in chains: %d / %d (%.1f%%)",
             violations_in_chains, violation_count, viol_pct)
    log.info("  Evidence in chains:   %d / %d (%.1f%%)",
             evidence_in_chains, evidence_count, evid_pct)

    # ── Lane balance ───────────────────────────────────────────────────
    lane_nodes = conn.execute(
        "SELECT lane, COUNT(*) AS cnt FROM nodes"
        " WHERE lane IS NOT NULL GROUP BY lane ORDER BY cnt DESC"
    ).fetchall()
    lane_edges = conn.execute(
        "SELECT n.lane, COUNT(*) AS cnt"
        " FROM edges e JOIN nodes n ON e.source_id = n.id"
        " WHERE n.lane IS NOT NULL GROUP BY n.lane ORDER BY cnt DESC"
    ).fetchall()

    ln_map = {r["lane"]: r["cnt"] for r in lane_nodes}
    le_map = {r["lane"]: r["cnt"] for r in lane_edges}
    report["lane_balance"] = {"nodes": dict(ln_map), "edges": dict(le_map)}

    log.info("Lane balance:")
    for lane in sorted(set(ln_map) | set(le_map)):
        log.info("  Lane %-3s  nodes=%7d  edges=%7d",
                 lane, ln_map.get(lane, 0), le_map.get(lane, 0))

    # ── Staleness ──────────────────────────────────────────────────────
    seven_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    stale_nodes = conn.execute(
        "SELECT COUNT(*) AS c FROM nodes n"
        " WHERE n.created_at < ?"
        " AND NOT EXISTS ("
        "   SELECT 1 FROM edges e"
        "   WHERE (e.source_id = n.id OR e.target_id = n.id)"
        "     AND e.rowid > (SELECT MAX(rowid) - 50000 FROM edges)"
        " )",
        (seven_ago,),
    ).fetchone()["c"]

    report["stale_nodes"] = stale_nodes
    log.info("Stale nodes (no recent edge activity): %d", stale_nodes)

    # ── Composite health score ─────────────────────────────────────────
    connectivity_score = min(1.0, conn_pct / 100.0)
    chain_score = (viol_pct + evid_pct) / 200.0
    orphan_score = 1.0 - min(1.0, total_orphans / max(1, total_nodes))

    # Normalize edge weights: cap at 1.0 (some types like PROVES use 0-100 scale)
    avg_weights = [
        min(1.0, r["avg_w"]) for r in edge_dist if r["avg_w"] is not None
    ]
    edge_quality = sum(avg_weights) / len(avg_weights) if avg_weights else 0.5

    lane_counts = [r["cnt"] for r in lane_nodes]
    if len(lane_counts) >= 2:
        balance_score = min(lane_counts) / max(lane_counts)
    else:
        balance_score = 1.0 if lane_counts else 0.0

    health = (
        connectivity_score * 0.30
        + chain_score * 0.25
        + orphan_score * 0.20
        + edge_quality * 0.15
        + balance_score * 0.10
    )
    report["health_score"] = round(health * 100, 1)

    elapsed = time.perf_counter() - t0
    log.info("Health score: %.1f%% (%.1fs)", report["health_score"], elapsed)

    _log_operation(
        conn, "health_check", {},
        json.dumps({
            "health_score": report["health_score"],
            "orphans": total_orphans,
            "connectivity_pct": round(conn_pct, 1),
        }),
        total_nodes, 0, elapsed * 1000,
    )
    return report


# ── 7. Full Evolution Cycle ───────────────────────────────────────────


def evolve(conn: sqlite3.Connection) -> dict:
    """Run the complete autonomous improvement cycle."""
    log.info("=" * 60)
    log.info("  BRAIN EVOLUTION CYCLE — Starting")
    log.info("=" * 60)
    t0 = time.perf_counter()

    log.info("\n[1/7] Health check (baseline)...")
    health = health_check(conn)

    log.info("\n[2/7] Discovering new connections...")
    new_edges = find_new_connections(conn)

    log.info("\n[3/7] Inserting new edges...")
    inserted = insert_new_edges(conn, new_edges)

    log.info("\n[4/7] Re-scoring chains...")
    chain_results = rescore_chains(conn)

    log.info("\n[5/7] Checking gap resolution...")
    gap_results = check_gaps(conn)

    log.info("\n[6/7] Analyzing parameters...")
    opt_results = optimize_params(conn)

    log.info("\n[7/7] Creating version snapshot...")
    version = create_version(conn)

    total_elapsed = time.perf_counter() - t0

    print()
    print("=" * 60)
    print("  BRAIN EVOLUTION CYCLE — Results")
    print("=" * 60)
    print(f"  New connections discovered:  {len(new_edges):>8,}")
    print(f"  New edges inserted:          {inserted:>8,}")
    print(f"  Chains re-scored:            {chain_results['total']:>8,}")
    print(f"  Chains improved:             {chain_results['improved']:>8,}")
    print(f"  Chains degraded:             {chain_results['degraded']:>8,}")
    print(f"  Gaps resolved:               {gap_results['resolved']:>8,}")
    print(f"  Gaps remaining:              {gap_results['remaining']:>8,}")
    print(f"  Health score:                {health['health_score']:>7.1f}%")
    print(f"  Optimizations:               {len(opt_results['suggestions']):>8,}")
    print(f"  Version:                      v{version['version']}")
    print(f"  Duration:                    {total_elapsed:>7.1f}s")
    if version.get("snapshot_path"):
        print(f"  Snapshot:  {version['snapshot_path']}")
    print("=" * 60)

    return {
        "new_connections": len(new_edges),
        "edges_inserted": inserted,
        "chains": chain_results,
        "gaps": gap_results,
        "health_score": health["health_score"],
        "version": version["version"],
        "duration_s": round(total_elapsed, 1),
    }


# ── 8. Stats ──────────────────────────────────────────────────────────


def print_stats(conn: sqlite3.Connection) -> None:
    """Print current brain statistics dashboard."""
    stats = conn.execute(
        "SELECT"
        " (SELECT COUNT(*) FROM nodes)  AS nodes,"
        " (SELECT COUNT(*) FROM edges)  AS edges,"
        " (SELECT COUNT(*) FROM chains) AS chains,"
        " (SELECT COUNT(*) FROM gaps WHERE resolved = 0) AS open_gaps,"
        " (SELECT COUNT(*) FROM gaps WHERE resolved = 1) AS resolved_gaps,"
        " (SELECT COUNT(*) FROM versions)   AS versions,"
        " (SELECT COUNT(*) FROM brain_ops)  AS ops,"
        " (SELECT COUNT(*) FROM ingest_queue WHERE status = 'pending')"
        "   AS pending_ingest,"
        " (SELECT COUNT(*) FROM court_feed  WHERE is_processed = 0)"
        "   AS unprocessed_feed"
    ).fetchone()

    layers = conn.execute(
        "SELECT layer, COUNT(*) AS cnt FROM nodes"
        " GROUP BY layer ORDER BY cnt DESC"
    ).fetchall()
    etypes = conn.execute(
        "SELECT edge_type, COUNT(*) AS cnt FROM edges"
        " GROUP BY edge_type ORDER BY cnt DESC"
    ).fetchall()
    chain_dist = conn.execute(
        "SELECT"
        " SUM(CASE WHEN strength_score >= 0.7 THEN 1 ELSE 0 END) AS strong,"
        " SUM(CASE WHEN strength_score >= 0.3"
        "          AND strength_score < 0.7 THEN 1 ELSE 0 END) AS medium,"
        " SUM(CASE WHEN strength_score < 0.3 THEN 1 ELSE 0 END)  AS weak"
        " FROM chains"
    ).fetchone()
    last_ver = conn.execute(
        "SELECT version, created_at FROM versions"
        " ORDER BY version DESC LIMIT 1"
    ).fetchone()

    print()
    print("=" * 60)
    print("  THEMANBEARPIG LEGAL BRAIN — Statistics")
    print("=" * 60)
    print(f"  Nodes:            {stats['nodes']:>10,}")
    print(f"  Edges:            {stats['edges']:>10,}")
    print(f"  Chains:           {stats['chains']:>10,}")
    print(f"  Open gaps:        {stats['open_gaps']:>10,}")
    print(f"  Resolved gaps:    {stats['resolved_gaps']:>10,}")
    print(f"  Versions:         {stats['versions']:>10,}")
    print(f"  Operations:       {stats['ops']:>10,}")
    print(f"  Pending ingest:   {stats['pending_ingest']:>10,}")
    print(f"  Unprocessed feed: {stats['unprocessed_feed']:>10,}")
    print()
    print("  Layers:")
    for r in layers:
        print(f"    {r['layer']:<15} {r['cnt']:>8,}")
    print()
    print("  Edge types:")
    for r in etypes:
        print(f"    {r['edge_type']:<25} {r['cnt']:>8,}")
    print()
    print("  Chain strength distribution:")
    print(f"    Strong  (>= 0.7): {chain_dist['strong'] or 0:>6,}")
    print(f"    Medium  (0.3-0.7):{chain_dist['medium'] or 0:>6,}")
    print(f"    Weak    (< 0.3):  {chain_dist['weak'] or 0:>6,}")
    if last_ver:
        print(f"\n  Latest version: v{last_ver['version']}"
              f"  ({last_ver['created_at']})")
    print("=" * 60)


# ── CLI ────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="THEMANBEARPIG Legal Brain — Self-Evolution Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -I scripts/brain_evolution.py              "
            "Full evolution cycle\n"
            "  python -I scripts/brain_evolution.py --health     "
            "Health check only\n"
            "  python -I scripts/brain_evolution.py --discover   "
            "Find new connections\n"
            "  python -I scripts/brain_evolution.py --rescore    "
            "Re-score chains\n"
            "  python -I scripts/brain_evolution.py --gaps       "
            "Check gap resolution\n"
            "  python -I scripts/brain_evolution.py --version    "
            "Create version snapshot\n"
            "  python -I scripts/brain_evolution.py --optimize   "
            "Parameter analysis\n"
            "  python -I scripts/brain_evolution.py --stats      "
            "Print brain stats"
        ),
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--health", action="store_true",
                       help="Run health check only")
    group.add_argument("--discover", action="store_true",
                       help="Find new connections only")
    group.add_argument("--rescore", action="store_true",
                       help="Re-score chains only")
    group.add_argument("--gaps", action="store_true",
                       help="Check gap resolution only")
    group.add_argument("--version", action="store_true",
                       help="Create version snapshot only")
    group.add_argument("--optimize", action="store_true",
                       help="Parameter analysis only")
    group.add_argument("--stats", action="store_true",
                       help="Print brain stats only")

    args = parser.parse_args()
    conn = get_brain_conn()

    try:
        if args.health:
            health_check(conn)
        elif args.discover:
            edges = find_new_connections(conn)
            n = insert_new_edges(conn, edges)
            print(f"\nDiscovered {len(edges)} candidates, "
                  f"inserted {n} new edges.")
        elif args.rescore:
            r = rescore_chains(conn)
            print(f"\nRe-scored {r['total']} chains: "
                  f"{r['improved']} improved, {r['degraded']} degraded.")
        elif args.gaps:
            r = check_gaps(conn)
            print(f"\nChecked {r['checked']} gaps: "
                  f"{r['resolved']} resolved, {r['remaining']} remaining.")
        elif args.version:
            v = create_version(conn)
            print(f"\nVersion v{v['version']}: "
                  f"{v['node_count']} nodes, {v['edge_count']} edges.")
        elif args.optimize:
            optimize_params(conn)
        elif args.stats:
            print_stats(conn)
        else:
            evolve(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
