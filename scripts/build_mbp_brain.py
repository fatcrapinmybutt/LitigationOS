#!/usr/bin/env python3
"""
THEMANBEARPIG Legal Brain v5.0 — Build mbp_brain.db
Distills ALL LitigationOS databases into a unified legal reasoning graph.

Chain: EVIDENCE → VIOLATION → AUTHORITY → REMEDY → FILING → EXHIBIT → (loop)

Usage:
    python -I scripts/build_mbp_brain.py [--rebuild] [--phase N]
    
    --rebuild   Drop and recreate mbp_brain.db from scratch
    --phase N   Run only phase N (1=nodes, 2=edges, 3=chains, 4=gaps)
"""

import sqlite3
import os
import sys
import json
import re
import hashlib
import argparse
import logging
from datetime import datetime, date
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
SOURCE_DB = REPO_ROOT / "litigation_context.db"
BRAIN_DB = REPO_ROOT / "mbp_brain.db"
BRAINS_DIR = REPO_ROOT / "00_SYSTEM" / "brains"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(REPO_ROOT / "logs" / "mbp_brain_build.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("mbp_brain")

# --- SCHEMA ---

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 60000;
PRAGMA cache_size = -64000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    layer TEXT NOT NULL,
    label TEXT NOT NULL,
    description TEXT,
    date_start TEXT,
    date_end TEXT,
    severity REAL DEFAULT 0,
    confidence REAL DEFAULT 0,
    readiness REAL DEFAULT 0,
    binding_strength TEXT,
    source_table TEXT,
    source_id TEXT,
    lane TEXT,
    metadata TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    weight REAL DEFAULT 0.5,
    evidence TEXT,
    source_table TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(source_id, target_id, edge_type)
);

CREATE TABLE IF NOT EXISTS chains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chain_path TEXT NOT NULL,
    chain_type TEXT NOT NULL,
    total_weight REAL,
    length INTEGER,
    lane TEXT,
    filing_id TEXT,
    evidence_ids TEXT,
    strength_score REAL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS gaps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gap_type TEXT NOT NULL,
    node_id TEXT,
    description TEXT NOT NULL,
    priority TEXT DEFAULT 'MEDIUM',
    acquisition_task TEXT,
    resolved INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS versions (
    version INTEGER PRIMARY KEY AUTOINCREMENT,
    node_count INTEGER,
    edge_count INTEGER,
    chain_count INTEGER,
    gap_count INTEGER,
    mutations TEXT,
    snapshot_path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS brain_ops (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation TEXT NOT NULL,
    input_params TEXT,
    output_summary TEXT,
    nodes_touched INTEGER,
    edges_traversed INTEGER,
    duration_ms REAL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ingest_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_type TEXT,
    status TEXT DEFAULT 'pending',
    nodes_created INTEGER DEFAULT 0,
    edges_created INTEGER DEFAULT 0,
    detected_at TEXT DEFAULT (datetime('now')),
    processed_at TEXT
);

CREATE TABLE IF NOT EXISTS court_feed (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    title TEXT,
    url TEXT,
    citation TEXT,
    relevance_score REAL DEFAULT 0,
    is_processed INTEGER DEFAULT 0,
    fetched_at TEXT DEFAULT (datetime('now')),
    processed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type);
CREATE INDEX IF NOT EXISTS idx_nodes_layer ON nodes(layer);
CREATE INDEX IF NOT EXISTS idx_nodes_lane ON nodes(lane);
CREATE INDEX IF NOT EXISTS idx_nodes_source ON nodes(source_table, source_id);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(edge_type);
CREATE INDEX IF NOT EXISTS idx_chains_lane ON chains(lane);
CREATE INDEX IF NOT EXISTS idx_chains_filing ON chains(filing_id);
CREATE INDEX IF NOT EXISTS idx_gaps_type ON gaps(gap_type);
CREATE INDEX IF NOT EXISTS idx_gaps_priority ON gaps(priority);
"""


def connect_source():
    """Read-only connection to litigation_context.db."""
    conn = sqlite3.connect(f"file:{SOURCE_DB}?mode=ro", uri=True)
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA cache_size = -32000")
    conn.text_factory = lambda b: b.decode("utf-8", errors="replace")
    conn.row_factory = sqlite3.Row
    return conn


def connect_brain(create=False):
    """Read-write connection to mbp_brain.db."""
    conn = sqlite3.connect(str(BRAIN_DB))
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -64000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")
    if create:
        conn.executescript(SCHEMA_SQL)
    conn.row_factory = sqlite3.Row
    return conn


def get_columns(conn, table):
    """Get column names for a table (Rule 16: schema-verify before query)."""
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def parse_severity(val):
    """Convert severity to float 0-10, handling text and numeric."""
    if val is None:
        return 0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().lower()
    mapping = {"low": 3, "medium": 5, "high": 8, "critical": 10, "severe": 9, "minor": 2, "moderate": 5}
    if s in mapping:
        return mapping[s]
    try:
        return float(s)
    except (ValueError, TypeError):
        return 5


def parse_confidence(val):
    """Convert confidence to float 0-1.0, handling text labels."""
    if val is None:
        return 0.5
    if isinstance(val, (int, float)):
        return min(1.0, max(0, float(val)))
    s = str(val).strip().lower()
    mapping = {"low": 0.3, "medium": 0.5, "high": 0.8, "confirmed": 1.0, "verified": 1.0,
               "suspected": 0.4, "possible": 0.3, "probable": 0.7, "certain": 1.0}
    if s in mapping:
        return mapping[s]
    try:
        return min(1.0, max(0, float(s)))
    except (ValueError, TypeError):
        return 0.5


def safe_float(val, default=0):
    """Convert any value to float safely, returning default on failure."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return default


def safe_text(val, max_len=500):
    """Truncate and clean text for labels."""
    if not val:
        return ""
    t = str(val).replace("\n", " ").replace("\r", "").strip()
    return t[:max_len] if len(t) > max_len else t


def batch_insert_nodes(brain, rows, batch_size=5000):
    """Insert nodes in batches with ON CONFLICT IGNORE."""
    if not rows:
        return 0
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        brain.executemany(
            """INSERT OR IGNORE INTO nodes
               (id, node_type, layer, label, description, date_start, date_end,
                severity, confidence, readiness, binding_strength,
                source_table, source_id, lane, metadata)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            batch,
        )
        total += len(batch)
    brain.commit()
    return total


def batch_insert_edges(brain, rows, batch_size=5000):
    """Insert edges in batches with ON CONFLICT IGNORE."""
    if not rows:
        return 0
    total = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        brain.executemany(
            """INSERT OR IGNORE INTO edges
               (source_id, target_id, edge_type, weight, evidence, source_table)
               VALUES (?,?,?,?,?,?)""",
            batch,
        )
        total += len(batch)
    brain.commit()
    return total


# ============================================================================
# PHASE 1: NODE EXTRACTION
# ============================================================================


def extract_evidence_nodes(src, brain):
    """Extract evidence nodes from evidence_quotes (175K → ~50K deduplicated)."""
    log.info("Extracting evidence nodes from evidence_quotes...")
    cursor = src.execute(
        """SELECT id, source_file, quote_text, page_number, category, lane,
                  relevance_score, filing_refs, tags, created_at, is_duplicate
           FROM evidence_quotes
           WHERE is_duplicate = 0 OR is_duplicate IS NULL"""
    )
    rows = []
    count = 0
    while True:
        batch = cursor.fetchmany(10000)
        if not batch:
            break
        for r in batch:
            node_type = "Quote"
            if r["category"] and "recording" in str(r["category"]).lower():
                node_type = "Recording"
            elif r["category"] and "testimony" in str(r["category"]).lower():
                node_type = "Testimony"
            label = safe_text(r["quote_text"], 200)
            if not label:
                continue
            meta = json.dumps(
                {
                    "source_file": r["source_file"],
                    "page": r["page_number"],
                    "category": r["category"],
                    "filing_refs": r["filing_refs"],
                    "tags": r["tags"],
                },
                default=str,
            )
            rows.append((
                f"ev-{r['id']}",
                node_type,
                "EVIDENCE",
                label,
                safe_text(r["quote_text"]),
                str(r["created_at"]) if r["created_at"] else None,
                None,
                safe_float(r["relevance_score"]),
                safe_float(r["relevance_score"]),
                0,
                None,
                "evidence_quotes",
                str(r["id"]),
                r["lane"],
                meta,
            ))
        count += len(batch)
        if count % 50000 == 0:
            log.info(f"  ...processed {count} evidence_quotes rows")
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Evidence nodes: {inserted} created from {count} source rows")
    return inserted


def extract_timeline_nodes(src, brain):
    """Extract timeline event nodes."""
    log.info("Extracting timeline nodes from timeline_events...")
    cursor = src.execute(
        """SELECT id, event_date, event_description, actors, lane, category,
                  severity, filing_relevance, created_at
           FROM timeline_events"""
    )
    rows = []
    for r in cursor:
        label = safe_text(r["event_description"], 200)
        if not label:
            continue
        meta = json.dumps(
            {"actors": r["actors"], "category": r["category"], "filing_relevance": r["filing_relevance"]},
            default=str,
        )
        rows.append((
            f"tl-{r['id']}",
            "Event",
            "EVIDENCE",
            label,
            safe_text(r["event_description"]),
            r["event_date"],
            None,
            parse_severity(r["severity"]),
            0.8,
            0,
            None,
            "timeline_events",
            str(r["id"]),
            r["lane"],
            meta,
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Timeline nodes: {inserted} created from {len(rows)} rows")
    return inserted


def extract_violation_nodes(src, brain):
    """Extract violation nodes from judicial_violations."""
    log.info("Extracting violation nodes from judicial_violations...")
    cursor = src.execute(
        """SELECT id, violation_type, description, date_occurred, mcr_rule,
                  canon, source_file, source_quote, severity, lane, created_at
           FROM judicial_violations"""
    )
    rows = []
    for r in cursor:
        vtype = str(r["violation_type"] or "").lower()
        if "constitutional" in vtype or "due process" in vtype:
            node_type = "ConstitutionalViolation"
        elif "canon" in vtype or "ethical" in vtype:
            node_type = "EthicalViolation"
        elif "mcr" in vtype or "procedural" in vtype:
            node_type = "ProceduralViolation"
        else:
            node_type = "StatutoryViolation"
        label = safe_text(r["description"], 200)
        if not label:
            label = f"{r['violation_type'] or 'Violation'}"
        meta = json.dumps(
            {
                "mcr_rule": r["mcr_rule"],
                "canon": r["canon"],
                "source_file": r["source_file"],
                "source_quote": safe_text(r["source_quote"], 300),
            },
            default=str,
        )
        rows.append((
            f"vl-{r['id']}",
            node_type,
            "VIOLATION",
            label,
            safe_text(r["description"]),
            r["date_occurred"],
            None,
            parse_severity(r["severity"]),
            0.85,
            0,
            None,
            "judicial_violations",
            str(r["id"]),
            r["lane"],
            meta,
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Violation nodes: {inserted} created from {len(rows)} rows")
    return inserted


def extract_contradiction_nodes(src, brain):
    """Extract contradiction nodes from contradiction_map."""
    log.info("Extracting contradiction nodes from contradiction_map...")
    cols = get_columns(src, "contradiction_map")
    needed = {"id"}
    if not needed.issubset(cols):
        log.warning(f"  contradiction_map missing columns, skipping. Has: {cols}")
        return 0
    select_cols = []
    for c in ["id", "claim_id", "source_a", "source_b", "contradiction_text", "severity", "lane",
              "statement_1", "source_1", "statement_2", "source_2", "actor", "category", "created_at"]:
        if c in cols:
            select_cols.append(c)
    cursor = src.execute(f"SELECT {','.join(select_cols)} FROM contradiction_map")
    rows = []
    for r in cursor:
        rd = dict(r)
        s1 = safe_text(rd.get("contradiction_text") or rd.get("statement_1") or rd.get("source_a") or "", 200)
        s2 = safe_text(rd.get("source_b") or rd.get("statement_2") or "", 200)
        label = f"CONTRADICTION: {s1[:100]}" if s1 else f"Contradiction #{r['id']}"
        sev = parse_severity(dict(r).get("severity", 5))
        rd = dict(r)
        meta = json.dumps({k: safe_text(str(v), 300) for k, v in rd.items() if k != "id"}, default=str)
        rows.append((
            f"ct-{r['id']}",
            "Contradiction",
            "EVIDENCE",
            label,
            f"{s1} VS {s2}",
            rd.get("created_at"),
            None,
            sev,
            0.9,
            0,
            None,
            "contradiction_map",
            str(r["id"]),
            rd.get("lane"),
            meta,
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Contradiction nodes: {inserted} created from {len(rows)} rows")
    return inserted


def extract_impeachment_nodes(src, brain):
    """Extract impeachment pattern nodes from impeachment_matrix."""
    log.info("Extracting impeachment nodes from impeachment_matrix...")
    cursor = src.execute(
        """SELECT id, category, evidence_summary, source_file,
                  quote_text, impeachment_value, cross_exam_question,
                  filing_relevance, source_table, source_id, event_date, created_at
           FROM impeachment_matrix"""
    )
    rows = []
    for r in cursor:
        label = safe_text(r["evidence_summary"] or r["quote_text"] or f"Impeachment #{r['id']}", 200)
        meta = json.dumps(
            {
                "category": r["category"],
                "cross_exam": safe_text(r["cross_exam_question"], 300),
                "filing_relevance": r["filing_relevance"],
                "source_file": r["source_file"],
                "source_table": r["source_table"],
            },
            default=str,
        )
        rows.append((
            f"im-{r['id']}",
            "Pattern",
            "EVIDENCE",
            label,
            safe_text(r["quote_text"]),
            r["event_date"],
            None,
            parse_severity(r["impeachment_value"]),
            0.85,
            0,
            None,
            "impeachment_matrix",
            str(r["id"]),
            None,
            meta,
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Impeachment nodes: {inserted} created from {len(rows)} rows")
    return inserted


def extract_authority_nodes(src, brain):
    """Extract authority nodes from michigan_rules_extracted."""
    log.info("Extracting authority nodes from michigan_rules_extracted...")
    cursor = src.execute(
        """SELECT id, rule_number, rule_type, title, full_text,
                  is_key_rule, extracted_at
           FROM michigan_rules_extracted
           WHERE is_key_rule = 1 OR title IS NOT NULL"""
    )
    rows = []
    for r in cursor:
        rtype = str(r["rule_type"] or "").lower()
        if "mcr" in rtype or "court rule" in rtype:
            node_type = "CourtRule"
        elif "mcl" in rtype or "statute" in rtype:
            node_type = "Statute"
        elif "mre" in rtype or "evidence" in rtype:
            node_type = "EvidenceRule"
        elif "usc" in rtype or "federal" in rtype:
            node_type = "FederalStatute"
        elif "const" in rtype:
            node_type = "Constitution"
        else:
            node_type = "CourtRule"
        label = f"{r['rule_number']}: {r['title'] or ''}"[:200]
        bind = "mandatory" if r["is_key_rule"] else "informative"
        rows.append((
            f"ru-{r['id']}",
            node_type,
            "AUTHORITY",
            label,
            safe_text(r["full_text"], 500),
            None,
            None,
            0,
            1.0,
            0,
            bind,
            "michigan_rules_extracted",
            str(r["id"]),
            None,
            json.dumps({"rule_number": r["rule_number"], "rule_type": r["rule_type"]}, default=str),
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Authority nodes: {inserted} created from {len(rows)} rows")
    return inserted


def extract_citation_nodes(src, brain):
    """Extract case law nodes from master_citations (top citations only)."""
    log.info("Extracting citation nodes from master_citations (frequency >= 2)...")
    cursor = src.execute(
        """SELECT id, citation, source_filing, verified, authority_type,
                  lane, context, frequency
           FROM master_citations
           WHERE frequency >= 2 OR verified = 1"""
    )
    rows = []
    for r in cursor:
        atype = str(r["authority_type"] or "").lower()
        if "case" in atype or "mich" in atype or "us " in atype:
            node_type = "CaseLaw"
        elif "statute" in atype or "mcl" in atype:
            node_type = "Statute"
        elif "rule" in atype or "mcr" in atype:
            node_type = "CourtRule"
        else:
            node_type = "CaseLaw"
        label = safe_text(r["citation"], 200)
        if not label:
            continue
        bind = "binding" if r["verified"] else "persuasive"
        rows.append((
            f"ci-{r['id']}",
            node_type,
            "AUTHORITY",
            label,
            safe_text(r["context"], 500),
            None,
            None,
            0,
            1.0 if r["verified"] else 0.7,
            0,
            bind,
            "master_citations",
            str(r["id"]),
            r["lane"],
            json.dumps({"frequency": r["frequency"], "source_filing": r["source_filing"]}, default=str),
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Citation nodes: {inserted} created from {len(rows)} rows")
    return inserted


def extract_filing_nodes(src, brain):
    """Extract filing nodes from filing_readiness."""
    log.info("Extracting filing nodes from filing_readiness...")
    cursor = src.execute(
        """SELECT vehicle_name, filing_id, status, readiness_score, blockers,
                  placeholder_count, exhibit_count, authority_count, word_count,
                  lane, deadline, updated_at
           FROM filing_readiness"""
    )
    rows = []
    for r in cursor:
        label = r["vehicle_name"] or f"Filing-{r['filing_id']}"
        ftype = "Motion"
        vn = str(r["vehicle_name"] or "").lower()
        if "brief" in vn:
            ftype = "Brief"
        elif "complaint" in vn:
            ftype = "Complaint"
        elif "petition" in vn or "msc" in vn:
            ftype = "Petition"
        elif "affidavit" in vn:
            ftype = "Affidavit"
        meta = json.dumps(
            {
                "status": r["status"],
                "blockers": r["blockers"],
                "placeholder_count": r["placeholder_count"],
                "exhibit_count": r["exhibit_count"],
                "authority_count": r["authority_count"],
                "word_count": r["word_count"],
                "deadline": r["deadline"],
            },
            default=str,
        )
        rows.append((
            f"fi-{r['filing_id'] or label}",
            ftype,
            "FILING",
            label,
            f"{label} — {r['status'] or 'unknown'}",
            r["deadline"],
            None,
            0,
            0,
            safe_float(r["readiness_score"]),
            None,
            "filing_readiness",
            r["filing_id"],
            r["lane"],
            meta,
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Filing nodes: {inserted} created")
    return inserted


def extract_police_nodes(src, brain):
    """Extract police report nodes."""
    log.info("Extracting police report nodes...")
    cursor = src.execute(
        """SELECT id, filename, incident_numbers, dates, officers,
                  allegations, exculpatory, key_quotes, created_at
           FROM police_reports"""
    )
    rows = []
    for r in cursor:
        rid = r['id']
        label = f"Police: {r['filename'] or r['incident_numbers'] or f'Report #{rid}'}"[:200]
        meta = json.dumps(
            {
                "officers": r["officers"],
                "incident_numbers": r["incident_numbers"],
                "allegations": safe_text(r["allegations"], 300),
                "exculpatory": safe_text(r["exculpatory"], 300),
            },
            default=str,
        )
        rows.append((
            f"pr-{r['id']}",
            "Document",
            "EVIDENCE",
            label,
            safe_text(r["key_quotes"], 500),
            r["dates"],
            None,
            7,
            0.95,
            0,
            None,
            "police_reports",
            str(r["id"]),
            None,
            meta,
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Police report nodes: {inserted} created")
    return inserted


def extract_person_nodes(src, brain):
    """Extract person nodes from parties."""
    log.info("Extracting person nodes from parties...")
    cursor = src.execute("SELECT id, name, role, party_type, bar_number, address FROM parties")
    rows = []
    for r in cursor:
        label = r["name"] or f"Party #{r['id']}"
        meta = json.dumps(
            {"role": r["role"], "party_type": r["party_type"], "bar_number": r["bar_number"], "address": r["address"]},
            default=str,
        )
        rows.append((
            f"pe-{r['id']}",
            "Person",
            "ACTOR",
            label,
            f"{r['name']} — {r['role'] or 'unknown role'}",
            None,
            None,
            0,
            1.0,
            0,
            None,
            "parties",
            str(r["id"]),
            None,
            meta,
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Person nodes: {inserted} created")
    return inserted


def extract_intel_nodes(src, brain):
    """Extract intelligence relationship nodes from berry_mcneill_intelligence."""
    log.info("Extracting intel nodes from berry_mcneill_intelligence...")
    cursor = src.execute(
        """SELECT id, connection_type, person_a, person_b, relationship,
                  evidence_source, confidence, notes, discovered_at
           FROM berry_mcneill_intelligence"""
    )
    rows = []
    for r in cursor:
        label = f"{r['person_a']} ↔ {r['person_b']}: {r['relationship'] or r['connection_type']}"[:200]
        meta = json.dumps(
            {
                "connection_type": r["connection_type"],
                "evidence_source": r["evidence_source"],
                "notes": safe_text(r["notes"], 300),
            },
            default=str,
        )
        rows.append((
            f"in-{r['id']}",
            "Relationship",
            "ACTOR",
            label,
            safe_text(r["notes"]),
            r["discovered_at"],
            None,
            0,
            parse_confidence(r["confidence"]),
            0,
            None,
            "berry_mcneill_intelligence",
            str(r["id"]),
            None,
            meta,
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Intel nodes: {inserted} created")
    return inserted


def extract_fact_nodes(src, brain):
    """Extract critical fact nodes."""
    log.info("Extracting fact nodes from critical_facts...")
    cursor = src.execute(
        """SELECT id, fact_type, fact_text, source, verified_by,
                  immutable, lane, created_at, is_duplicate
           FROM critical_facts
           WHERE (is_duplicate = 0 OR is_duplicate IS NULL)"""
    )
    rows = []
    for r in cursor:
        label = safe_text(r["fact_text"], 200)
        if not label:
            continue
        rows.append((
            f"fa-{r['id']}",
            "Fact",
            "EVIDENCE",
            label,
            safe_text(r["fact_text"]),
            r["created_at"],
            None,
            0,
            1.0 if r["immutable"] else 0.7,
            0,
            None,
            "critical_facts",
            str(r["id"]),
            r["lane"],
            json.dumps({"fact_type": r["fact_type"], "source": r["source"], "verified_by": r["verified_by"]}, default=str),
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Fact nodes: {inserted} created")
    return inserted


def create_lane_nodes(brain):
    """Create static lane nodes for case lanes A-F + CRIM."""
    log.info("Creating lane nodes...")
    lanes = [
        ("lane-A", "Custody", "2024-001507-DC", "14th Circuit, Hon. Jenny L. McNeill"),
        ("lane-B", "Housing", "2025-002760-CZ", "14th Circuit, Hon. Kenneth Hoopes — DISMISSED"),
        ("lane-C", "Federal §1983", "Drafting", "USDC Western District MI"),
        ("lane-D", "PPO", "2023-5907-PP", "14th Circuit, Hon. Jenny L. McNeill"),
        ("lane-E", "Judicial Misconduct", "MULTI", "JTC / MSC"),
        ("lane-F", "Appellate", "COA 366810", "MI Court of Appeals"),
        ("lane-CRIM", "Criminal (SEPARATE)", "2025-25245676SM", "60th District, Kostrzewa"),
    ]
    rows = []
    for lid, name, case_num, court in lanes:
        rows.append((
            lid, "Lane", "LANE", f"Lane {lid.split('-')[1]}: {name}",
            f"{name} — {case_num} — {court}",
            None, None, 0, 1.0, 0, None,
            "static", lid, lid.split("-")[1],
            json.dumps({"case_number": case_num, "court": court}),
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Lane nodes: {inserted} created")
    return inserted


def create_remedy_nodes(brain):
    """Create remedy nodes for available legal remedies."""
    log.info("Creating remedy nodes...")
    remedies = [
        ("rem-disqualify", "JudicialRemedy", "Disqualification of Judge", "MCR 2.003 — Remove biased judge from case", "mandatory", 9),
        ("rem-sanctions", "Sanction", "Sanctions Against Party/Counsel", "MCR 2.114 — Sanctions for frivolous filings or misconduct", "mandatory", 7),
        ("rem-contempt", "Sanction", "Contempt of Court", "MCL 600.1701 — Enforce compliance with court orders", "mandatory", 8),
        ("rem-vacatur", "JudicialRemedy", "Vacate Judgment", "MCR 2.612 — Relief from prior judgment", "mandatory", 9),
        ("rem-reversal", "AppellateRemedy", "Appellate Reversal", "MCR 7.212 — COA reversal of trial court", "binding", 10),
        ("rem-superintend", "AppellateRemedy", "MSC Superintending Control", "MCR 7.306 — MSC oversight of lower courts", "mandatory", 10),
        ("rem-mandamus", "AppellateRemedy", "Writ of Mandamus", "MCR 7.306 — Compel judicial action", "mandatory", 9),
        ("rem-habeas", "AppellateRemedy", "Habeas Corpus", "MI Const. art 1 § 12; MCL 600.4301", "constitutional", 10),
        ("rem-damages-comp", "Damages", "Compensatory Damages", "Lost wages, housing, parenting time — $620K-$1.48M", None, 8),
        ("rem-damages-pun", "Damages", "Punitive Damages (§1983)", "42 USC §1983 — $250K-$1M for deliberate violations", None, 9),
        ("rem-injunction", "Injunction", "Injunctive Relief", "Restore parenting time, stop further violations", "mandatory", 10),
        ("rem-jtc-removal", "AdministrativeRemedy", "JTC Judicial Removal", "MI Const. art 6 § 30 — Remove judge from bench", None, 10),
        ("rem-ppo-terminate", "JudicialRemedy", "PPO Termination", "MCR 3.707(B) — Terminate weaponized PPO", "mandatory", 8),
        ("rem-custody-mod", "JudicialRemedy", "Custody Modification", "MCR 3.206 + Vodvarka — Restore parenting time", "mandatory", 10),
    ]
    rows = []
    for rid, rtype, label, desc, bind, sev in remedies:
        rows.append((
            rid, rtype, "REMEDY", label, desc,
            None, None, sev, 0.8, 0, bind,
            "static", rid, None,
            json.dumps({"remedy_type": rtype}),
        ))
    inserted = batch_insert_nodes(brain, rows)
    log.info(f"  Remedy nodes: {inserted} created")
    return inserted


# ============================================================================
# PHASE 2: EDGE CONSTRUCTION
# ============================================================================


def build_edges_from_graph_edges(src, brain):
    """Import edges from the existing graph_edges table (296K)."""
    log.info("Building edges from graph_edges (296K pre-built)...")
    cursor = src.execute(
        """SELECT source_id, target_id, edge_type, data
           FROM graph_edges
           WHERE source_id IS NOT NULL AND target_id IS NOT NULL
           LIMIT 100000"""
    )
    rows = []
    skipped = 0
    for r in cursor:
        sid = str(r["source_id"])
        tid = str(r["target_id"])
        etype = r["edge_type"] or "RELATED"
        weight = 0.5
        data = r["data"]
        if data:
            try:
                d = json.loads(data) if isinstance(data, str) else {}
                weight = float(d.get("weight", d.get("confidence", d.get("strength", 0.5))))
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        rows.append((sid, tid, etype, min(max(weight, 0.01), 1.0), None, "graph_edges"))
    inserted = batch_insert_edges(brain, rows)
    log.info(f"  Graph edges: {inserted} imported (from {len(rows)} candidates)")
    return inserted


def build_authority_chain_edges(src, brain):
    """Build CITES edges from authority_chains_v2 (primary_citation → supporting_citation)."""
    log.info("Building authority chain edges (167K)...")
    cols = get_columns(src, "authority_chains_v2")
    if "primary_citation" not in cols or "supporting_citation" not in cols:
        log.warning("  authority_chains_v2 missing expected columns, skipping")
        return 0

    # Build a lookup: citation text → node_id for fast matching
    brain_cursor = brain.execute("SELECT id, label FROM nodes WHERE layer IN ('AUTHORITY')")
    label_to_id = {}
    for row in brain_cursor:
        lbl = (row["label"] or "").strip().lower()
        if lbl:
            label_to_id[lbl] = row["id"]
            # Also index just the citation/rule number part (before the colon)
            if ":" in lbl:
                prefix = lbl.split(":")[0].strip()
                if prefix and prefix not in label_to_id:
                    label_to_id[prefix] = row["id"]

    cursor = src.execute(
        """SELECT id, primary_citation, supporting_citation, relationship, lane
           FROM authority_chains_v2
           WHERE primary_citation IS NOT NULL AND supporting_citation IS NOT NULL"""
    )
    rows = []
    matched = 0
    for r in cursor:
        prim = (r["primary_citation"] or "").strip().lower()
        supp = (r["supporting_citation"] or "").strip().lower()
        pid = label_to_id.get(prim)
        sid = label_to_id.get(supp)
        if pid and sid and pid != sid:
            rel = r["relationship"] or "CITES"
            rows.append((pid, sid, "CITES", 0.8, rel, "authority_chains_v2"))
            matched += 1
    inserted = batch_insert_edges(brain, rows)
    log.info(f"  Authority chain edges: {inserted} created ({matched} matched from {len(rows)} candidates)")
    return inserted


def build_contradiction_edges(src, brain):
    """Build CONTRADICTS edges from contradiction_map."""
    log.info("Building contradiction edges...")
    cols = get_columns(src, "contradiction_map")
    cursor = src.execute("SELECT id FROM contradiction_map")
    rows = []
    for r in cursor:
        ct_id = f"ct-{r['id']}"
        rows.append((ct_id, ct_id, "CONTRADICTS", 0.9, None, "contradiction_map"))
    inserted = batch_insert_edges(brain, rows)
    log.info(f"  Contradiction edges: {inserted} created")
    return inserted


def build_claim_evidence_edges(src, brain):
    """Build PROVES edges from claim_evidence_links."""
    log.info("Building claim-evidence edges...")
    cursor = src.execute(
        """SELECT id, claim_id, evidence_quote_id, relevance_score
           FROM claim_evidence_links
           WHERE evidence_quote_id IS NOT NULL"""
    )
    rows = []
    for r in cursor:
        eid = f"ev-{r['evidence_quote_id']}"
        rows.append((eid, f"claim-{r['claim_id']}", "PROVES", safe_float(r["relevance_score"], 0.7), None, "claim_evidence_links"))
    inserted = batch_insert_edges(brain, rows)
    log.info(f"  Claim-evidence edges: {inserted} created")
    return inserted


def build_lane_edges(brain):
    """Wire nodes to their lane nodes based on lane column."""
    log.info("Building lane assignment edges...")
    cursor = brain.execute("SELECT id, lane FROM nodes WHERE lane IS NOT NULL AND lane != ''")
    rows = []
    lane_map = {"a": "lane-A", "b": "lane-B", "c": "lane-C", "d": "lane-D", "e": "lane-E", "f": "lane-F", "crim": "lane-CRIM"}
    for r in cursor:
        lane_val = str(r["lane"]).strip().lower()
        lane_id = lane_map.get(lane_val)
        if not lane_id:
            for key, lid in lane_map.items():
                if key in lane_val:
                    lane_id = lid
                    break
        if lane_id:
            rows.append((r["id"], lane_id, "ASSIGNED_TO", 1.0, None, "computed"))
    inserted = batch_insert_edges(brain, rows)
    log.info(f"  Lane edges: {inserted} created")
    return inserted


def build_violation_authority_edges(brain):
    """Wire violations to authority nodes by matching MCR/MCL references."""
    log.info("Building violation → authority edges...")
    violations = brain.execute(
        "SELECT id, label, description, metadata FROM nodes WHERE layer = 'VIOLATION'"
    ).fetchall()
    authorities = brain.execute(
        "SELECT id, label FROM nodes WHERE layer = 'AUTHORITY'"
    ).fetchall()

    auth_index = {}
    for a in authorities:
        label = str(a["label"]).lower()
        for pat in re.findall(r"mcr\s*[\d.]+|mcl\s*[\d.]+|mre\s*[\d.]+", label):
            auth_index.setdefault(pat.replace(" ", ""), []).append(a["id"])

    rows = []
    for v in violations:
        text = f"{v['label']} {v['description'] or ''} {v['metadata'] or ''}".lower()
        for pat in re.findall(r"mcr\s*[\d.]+|mcl\s*[\d.]+|mre\s*[\d.]+", text):
            key = pat.replace(" ", "")
            for aid in auth_index.get(key, []):
                rows.append((v["id"], aid, "GOVERNED_BY", 0.9, pat, "computed"))

    inserted = batch_insert_edges(brain, rows)
    log.info(f"  Violation→Authority edges: {inserted} created")
    return inserted


def build_remedy_authority_edges(brain):
    """Wire remedies to authority nodes."""
    log.info("Building authority → remedy edges...")
    remedies = brain.execute("SELECT id, description FROM nodes WHERE layer = 'REMEDY'").fetchall()
    authorities = brain.execute("SELECT id, label FROM nodes WHERE layer = 'AUTHORITY'").fetchall()

    auth_index = {}
    for a in authorities:
        label = str(a["label"]).lower()
        for pat in re.findall(r"mcr\s*[\d.]+|mcl\s*[\d.]+|42\s*usc|mi\s*const", label):
            auth_index.setdefault(pat.replace(" ", ""), []).append(a["id"])

    rows = []
    for rem in remedies:
        text = str(rem["description"] or "").lower()
        for pat in re.findall(r"mcr\s*[\d.]+|mcl\s*[\d.]+|42\s*usc|mi\s*const", text):
            key = pat.replace(" ", "")
            for aid in auth_index.get(key, []):
                rows.append((aid, rem["id"], "AUTHORIZES", 0.85, pat, "computed"))

    inserted = batch_insert_edges(brain, rows)
    log.info(f"  Authority→Remedy edges: {inserted} created")
    return inserted


def build_filing_remedy_edges(brain):
    """Wire filings to the remedies they execute."""
    log.info("Building remedy → filing edges...")
    filings = brain.execute("SELECT id, label, metadata FROM nodes WHERE layer = 'FILING'").fetchall()
    remedies = brain.execute("SELECT id, label FROM nodes WHERE layer = 'REMEDY'").fetchall()

    filing_remedy_map = {
        "disqualif": "rem-disqualify",
        "sanction": "rem-sanctions",
        "contempt": "rem-contempt",
        "vacat": "rem-vacatur",
        "coa": "rem-reversal",
        "appeal": "rem-reversal",
        "msc": "rem-superintend",
        "mandamus": "rem-mandamus",
        "habeas": "rem-habeas",
        "1983": "rem-damages-pun",
        "federal": "rem-damages-pun",
        "jtc": "rem-jtc-removal",
        "ppo": "rem-ppo-terminate",
        "custody": "rem-custody-mod",
        "parenting": "rem-custody-mod",
        "emergency": "rem-injunction",
    }

    rows = []
    for f in filings:
        text = f"{f['label']} {f['metadata'] or ''}".lower()
        for keyword, rem_id in filing_remedy_map.items():
            if keyword in text:
                rows.append((rem_id, f["id"], "EXECUTED_VIA", 0.9, keyword, "computed"))

    inserted = batch_insert_edges(brain, rows)
    log.info(f"  Remedy→Filing edges: {inserted} created")
    return inserted


# ============================================================================
# PHASE 3: GAP DETECTION
# ============================================================================


def detect_gaps(brain):
    """Find missing links in the reasoning chain."""
    log.info("Running gap detection...")
    gaps = []

    violations_no_evidence = brain.execute("""
        SELECT n.id, n.label FROM nodes n
        WHERE n.layer = 'VIOLATION'
        AND NOT EXISTS (SELECT 1 FROM edges e WHERE e.target_id = n.id AND e.edge_type IN ('PROVES','SUGGESTS','CORROBORATES'))
    """).fetchall()
    for v in violations_no_evidence:
        gaps.append(("VIOLATION_NO_EVIDENCE", v["id"], f"Violation '{v['label'][:100]}' has no supporting evidence", "HIGH",
                      "Search evidence_quotes for supporting quotes, or acquire new evidence"))

    filings_no_exhibit = brain.execute("""
        SELECT n.id, n.label FROM nodes n
        WHERE n.layer = 'FILING'
        AND NOT EXISTS (SELECT 1 FROM edges e WHERE e.source_id = n.id AND e.edge_type = 'REQUIRES_EXHIBIT')
    """).fetchall()
    for f in filings_no_exhibit:
        gaps.append(("FILING_NO_EXHIBIT", f["id"], f"Filing '{f['label'][:100]}' has no linked exhibits", "MEDIUM",
                      "Compile exhibit list from supporting evidence chain"))

    violations_no_authority = brain.execute("""
        SELECT n.id, n.label FROM nodes n
        WHERE n.layer = 'VIOLATION'
        AND NOT EXISTS (SELECT 1 FROM edges e WHERE e.source_id = n.id AND e.edge_type = 'GOVERNED_BY')
    """).fetchall()
    for v in violations_no_authority:
        gaps.append(("VIOLATION_NO_AUTHORITY", v["id"], f"Violation '{v['label'][:100]}' not linked to governing authority", "HIGH",
                      "Search michigan_rules_extracted for applicable MCR/MCL"))

    remedies_no_filing = brain.execute("""
        SELECT n.id, n.label FROM nodes n
        WHERE n.layer = 'REMEDY'
        AND NOT EXISTS (SELECT 1 FROM edges e WHERE e.source_id = n.id AND e.edge_type = 'EXECUTED_VIA')
    """).fetchall()
    for r in remedies_no_filing:
        gaps.append(("REMEDY_NO_FILING", r["id"], f"Remedy '{r['label'][:100]}' has no filing vehicle", "MEDIUM",
                      "Draft a motion or complaint to pursue this remedy"))

    if gaps:
        brain.executemany(
            "INSERT INTO gaps (gap_type, node_id, description, priority, acquisition_task) VALUES (?,?,?,?,?)",
            gaps,
        )
        brain.commit()

    by_priority = defaultdict(int)
    for g in gaps:
        by_priority[g[3]] += 1
    log.info(f"  Gaps detected: {len(gaps)} total — {dict(by_priority)}")
    return len(gaps)


# ============================================================================
# VERSION + STATS
# ============================================================================


def record_version(brain, mutations_desc):
    """Record a new graph version."""
    stats = brain.execute("""
        SELECT
            (SELECT COUNT(*) FROM nodes) as nc,
            (SELECT COUNT(*) FROM edges) as ec,
            (SELECT COUNT(*) FROM chains) as cc,
            (SELECT COUNT(*) FROM gaps WHERE resolved = 0) as gc
    """).fetchone()
    brain.execute(
        "INSERT INTO versions (node_count, edge_count, chain_count, gap_count, mutations) VALUES (?,?,?,?,?)",
        (stats["nc"], stats["ec"], stats["cc"], stats["gc"], mutations_desc),
    )
    brain.commit()
    return stats


def print_summary(brain):
    """Print a summary of the brain database."""
    stats = brain.execute("""
        SELECT
            (SELECT COUNT(*) FROM nodes) as nodes,
            (SELECT COUNT(*) FROM edges) as edges,
            (SELECT COUNT(*) FROM chains) as chains,
            (SELECT COUNT(*) FROM gaps WHERE resolved = 0) as gaps
    """).fetchone()

    layer_counts = brain.execute(
        "SELECT layer, COUNT(*) as cnt FROM nodes GROUP BY layer ORDER BY cnt DESC"
    ).fetchall()

    edge_type_counts = brain.execute(
        "SELECT edge_type, COUNT(*) as cnt FROM edges GROUP BY edge_type ORDER BY cnt DESC LIMIT 15"
    ).fetchall()

    gap_counts = brain.execute(
        "SELECT gap_type, COUNT(*) as cnt FROM gaps WHERE resolved = 0 GROUP BY gap_type ORDER BY cnt DESC"
    ).fetchall()

    sep_days = (date.today() - date(2025, 7, 29)).days

    print("\n" + "=" * 70)
    print("  THEMANBEARPIG LEGAL BRAIN v5.0 — BUILD COMPLETE")
    print("=" * 70)
    print(f"  Separation: {sep_days} days (since Jul 29, 2025)")
    print(f"  Database: {BRAIN_DB}")
    print(f"  Size: {BRAIN_DB.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"\n  TOTALS: {stats['nodes']:,} nodes | {stats['edges']:,} edges | {stats['chains']:,} chains | {stats['gaps']:,} gaps")

    print("\n  NODES BY LAYER:")
    for r in layer_counts:
        print(f"    {r['layer']:20s} {r['cnt']:>8,}")

    print("\n  TOP EDGE TYPES:")
    for r in edge_type_counts:
        print(f"    {r['edge_type']:25s} {r['cnt']:>8,}")

    if gap_counts:
        print("\n  GAPS (unresolved):")
        for r in gap_counts:
            print(f"    {r['gap_type']:30s} {r['cnt']:>6,}")

    print("=" * 70 + "\n")


# ============================================================================
# MAIN
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description="Build THEMANBEARPIG Legal Brain v5.0")
    parser.add_argument("--rebuild", action="store_true", help="Drop and recreate from scratch")
    parser.add_argument("--phase", type=int, help="Run only this phase (1=nodes, 2=edges, 3=gaps)")
    args = parser.parse_args()

    os.makedirs(REPO_ROOT / "logs", exist_ok=True)

    if args.rebuild and BRAIN_DB.exists():
        log.info(f"Removing existing {BRAIN_DB}...")
        os.remove(str(BRAIN_DB))

    log.info(f"Source: {SOURCE_DB} ({SOURCE_DB.stat().st_size / 1024 / 1024:.0f} MB)")
    log.info(f"Target: {BRAIN_DB}")

    src = connect_source()
    brain = connect_brain(create=True)

    run_phase = args.phase

    if run_phase is None or run_phase == 1:
        log.info("\n" + "=" * 50)
        log.info("PHASE 1: NODE EXTRACTION")
        log.info("=" * 50)
        t1 = datetime.now()
        total_nodes = 0
        total_nodes += extract_evidence_nodes(src, brain)
        total_nodes += extract_timeline_nodes(src, brain)
        total_nodes += extract_violation_nodes(src, brain)
        total_nodes += extract_contradiction_nodes(src, brain)
        total_nodes += extract_impeachment_nodes(src, brain)
        total_nodes += extract_authority_nodes(src, brain)
        total_nodes += extract_citation_nodes(src, brain)
        total_nodes += extract_filing_nodes(src, brain)
        total_nodes += extract_police_nodes(src, brain)
        total_nodes += extract_person_nodes(src, brain)
        total_nodes += extract_intel_nodes(src, brain)
        total_nodes += extract_fact_nodes(src, brain)
        total_nodes += create_lane_nodes(brain)
        total_nodes += create_remedy_nodes(brain)
        elapsed = (datetime.now() - t1).total_seconds()
        log.info(f"\nPHASE 1 COMPLETE: {total_nodes:,} nodes in {elapsed:.1f}s")

    if run_phase is None or run_phase == 2:
        log.info("\n" + "=" * 50)
        log.info("PHASE 2: EDGE CONSTRUCTION")
        log.info("=" * 50)
        t2 = datetime.now()
        total_edges = 0
        total_edges += build_edges_from_graph_edges(src, brain)
        total_edges += build_authority_chain_edges(src, brain)
        total_edges += build_contradiction_edges(src, brain)
        total_edges += build_claim_evidence_edges(src, brain)
        total_edges += build_lane_edges(brain)
        total_edges += build_violation_authority_edges(brain)
        total_edges += build_remedy_authority_edges(brain)
        total_edges += build_filing_remedy_edges(brain)
        elapsed = (datetime.now() - t2).total_seconds()
        log.info(f"\nPHASE 2 COMPLETE: {total_edges:,} edges in {elapsed:.1f}s")

    if run_phase is None or run_phase == 3:
        log.info("\n" + "=" * 50)
        log.info("PHASE 3: GAP DETECTION")
        log.info("=" * 50)
        t3 = datetime.now()
        gap_count = detect_gaps(brain)
        elapsed = (datetime.now() - t3).total_seconds()
        log.info(f"\nPHASE 3 COMPLETE: {gap_count} gaps in {elapsed:.1f}s")

    mutations = f"Full build: phases {run_phase or '1-3'}"
    stats = record_version(brain, mutations)
    log.info(f"Version recorded: {stats['nc']:,} nodes, {stats['ec']:,} edges, {stats['gc']:,} gaps")

    print_summary(brain)

    brain.execute("PRAGMA optimize")
    brain.close()
    src.close()
    log.info("Build complete.")


if __name__ == "__main__":
    main()
