#!/usr/bin/env python3
"""
build_lane_c_db.py — Create lane_C_convergence.db for cross-lane evidence linking
=================================================================================
Creates the convergence database with:
- cross_lane_evidence, convergence_links, satisfaction_map, lane_routing tables
- Indexes on key columns
- WAL mode + Tier-2 PRAGMAs
"""

import sqlite3
import sys
import os
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "databases" / "lane_C_convergence.db"


def build():
    # Remove empty file if exists
    if DB_PATH.exists() and os.path.getsize(str(DB_PATH)) == 0:
        os.remove(str(DB_PATH))

    conn = sqlite3.connect(str(DB_PATH))

    # Tier-2 PRAGMAs
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS cross_lane_evidence (
            evidence_id TEXT PRIMARY KEY,
            source_lane TEXT NOT NULL,
            target_lanes TEXT NOT NULL,
            atom_id TEXT,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS convergence_links (
            link_id TEXT PRIMARY KEY,
            lane_a_ref TEXT NOT NULL,
            lane_b_ref TEXT NOT NULL,
            relationship_type TEXT NOT NULL,
            strength REAL DEFAULT 0.5,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS satisfaction_map (
            sat_id TEXT PRIMARY KEY,
            requirement_id TEXT NOT NULL,
            evidence_id TEXT NOT NULL,
            satisfaction_level REAL DEFAULT 0.0,
            verified INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS lane_routing (
            route_id TEXT PRIMARY KEY,
            evidence_hash TEXT,
            detected_lanes TEXT NOT NULL,
            primary_lane TEXT NOT NULL,
            routing_reason TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        -- Indexes for cross_lane_evidence
        CREATE INDEX IF NOT EXISTS idx_cle_source_lane ON cross_lane_evidence(source_lane);
        CREATE INDEX IF NOT EXISTS idx_cle_target_lanes ON cross_lane_evidence(target_lanes);
        CREATE INDEX IF NOT EXISTS idx_cle_evidence_id ON cross_lane_evidence(evidence_id);
        CREATE INDEX IF NOT EXISTS idx_cle_atom_id ON cross_lane_evidence(atom_id);

        -- Indexes for convergence_links
        CREATE INDEX IF NOT EXISTS idx_cl_lane_a ON convergence_links(lane_a_ref);
        CREATE INDEX IF NOT EXISTS idx_cl_lane_b ON convergence_links(lane_b_ref);
        CREATE INDEX IF NOT EXISTS idx_cl_relationship ON convergence_links(relationship_type);

        -- Indexes for satisfaction_map
        CREATE INDEX IF NOT EXISTS idx_sm_requirement ON satisfaction_map(requirement_id);
        CREATE INDEX IF NOT EXISTS idx_sm_evidence ON satisfaction_map(evidence_id);
        CREATE INDEX IF NOT EXISTS idx_sm_verified ON satisfaction_map(verified);

        -- Indexes for lane_routing
        CREATE INDEX IF NOT EXISTS idx_lr_primary_lane ON lane_routing(primary_lane);
        CREATE INDEX IF NOT EXISTS idx_lr_evidence_hash ON lane_routing(evidence_hash);
    """)

    conn.commit()

    # Verify
    tables = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
    ).fetchone()[0]
    indexes = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
    ).fetchone()[0]
    conn.close()
    return tables, indexes


if __name__ == "__main__":
    print(f"Building lane_C_convergence.db at: {DB_PATH}")
    tables, indexes = build()
    print(f"  Tables: {tables}")
    print(f"  Indexes: {indexes}")
    size_kb = os.path.getsize(str(DB_PATH)) // 1024
    print(f"  Size: {size_kb} KB")
    print("Done.")
