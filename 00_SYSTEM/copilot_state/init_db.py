"""
Copilot State Database — Persistent session state for LitigationOS.
Saves agent fleet config, AI model registry, operation snapshots,
and checkpoints before every multi-phase operation. Persists forever.
"""
import sqlite3
import json
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "copilot_state.db"
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")

SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 60000;
PRAGMA cache_size = -32000;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- Every multi-phase operation is logged here
CREATE TABLE IF NOT EXISTS operations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'planned',  -- planned|running|paused|completed|failed
    total_phases INTEGER DEFAULT 0,
    completed_phases INTEGER DEFAULT 0,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    config_json TEXT  -- full operation config snapshot
);

-- Individual phases within an operation
CREATE TABLE IF NOT EXISTS operation_phases (
    id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL,
    phase_number INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending|running|completed|failed|skipped
    started_at TEXT,
    completed_at TEXT,
    result_json TEXT,  -- output/stats from this phase
    error_text TEXT,
    FOREIGN KEY (operation_id) REFERENCES operations(id)
);

-- Agent fleet registry — every agent definition
CREATE TABLE IF NOT EXISTS agent_registry (
    agent_id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,  -- delta9|delta999|superpower|organization|convergence
    tier TEXT,  -- 1|2|3|J|K|L|F|org
    lane TEXT,  -- 1|2|convergence|org
    name TEXT NOT NULL,
    file_path TEXT,
    description TEXT,
    capabilities TEXT,  -- JSON array
    config_json TEXT,
    status TEXT DEFAULT 'active',  -- active|disabled|deprecated
    registered_at TEXT DEFAULT (datetime('now')),
    last_run_at TEXT
);

-- AI model registry — every loaded model
CREATE TABLE IF NOT EXISTS ai_model_registry (
    model_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    model_type TEXT NOT NULL,  -- gguf|pytorch|sklearn|tfidf|bm25|embedding|ner
    file_path TEXT,
    file_size_mb REAL,
    format TEXT,  -- gguf|pkl|npz|bin|json|safetensors
    capabilities TEXT,  -- JSON array
    status TEXT DEFAULT 'available',  -- available|loaded|error|missing
    last_loaded_at TEXT,
    performance_json TEXT,  -- benchmark results
    registered_at TEXT DEFAULT (datetime('now'))
);

-- Full state snapshot before each operation
CREATE TABLE IF NOT EXISTS state_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT,
    snapshot_type TEXT NOT NULL,  -- pre_operation|checkpoint|post_operation|manual
    drive_space_json TEXT,  -- {C: {free, used}, I: {free, used}, ...}
    file_counts_json TEXT,  -- {total, by_drive, by_extension}
    db_health_json TEXT,  -- {size, tables, wal_size}
    agent_status_json TEXT,  -- {agent_id: status, ...}
    model_status_json TEXT,  -- {model_id: status, ...}
    todo_counts_json TEXT,  -- {pending, in_progress, done, blocked}
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (operation_id) REFERENCES operations(id)
);

-- Granular recovery checkpoints during long operations
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_id TEXT NOT NULL,
    phase_id TEXT,
    checkpoint_number INTEGER NOT NULL,
    items_processed INTEGER DEFAULT 0,
    items_total INTEGER DEFAULT 0,
    state_json TEXT,  -- serialized resumable state
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (operation_id) REFERENCES operations(id)
);

-- Session continuity — links Copilot CLI sessions to operations
CREATE TABLE IF NOT EXISTS session_links (
    session_id TEXT NOT NULL,
    operation_id TEXT,
    session_dir TEXT,
    summary TEXT,
    linked_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (session_id, operation_id),
    FOREIGN KEY (operation_id) REFERENCES operations(id)
);

-- Key-value settings store
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Audit log — every significant action
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    target TEXT,
    details TEXT,
    agent_id TEXT,
    operation_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ops_status ON operations(status);
CREATE INDEX IF NOT EXISTS idx_phases_op ON operation_phases(operation_id);
CREATE INDEX IF NOT EXISTS idx_phases_status ON operation_phases(status);
CREATE INDEX IF NOT EXISTS idx_snapshots_op ON state_snapshots(operation_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_op ON checkpoints(operation_id);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agent_registry(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agent_registry(status);
CREATE INDEX IF NOT EXISTS idx_models_type ON ai_model_registry(model_type);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_op ON audit_log(operation_id);
"""

# Case-intelligence schema — tracks extracted facts, named evidence atoms,
# violations, litigation vehicles, and overall case state.
CASE_INTELLIGENCE_SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 60000;
PRAGMA cache_size = -32000;
PRAGMA synchronous = NORMAL;

-- Extracted facts (FE-XXX)
CREATE TABLE IF NOT EXISTS extracted_facts (
    fact_id           TEXT PRIMARY KEY,   -- e.g. FE-032
    summary           TEXT NOT NULL,
    fact_state        TEXT NOT NULL,      -- UNVERIFIED | VERIFIED | DISPUTED
    proof_needed      TEXT DEFAULT '',
    significance      TEXT DEFAULT '',
    evidence_refs_json TEXT DEFAULT '[]', -- JSON array of EA-XXX IDs
    created_at        TEXT DEFAULT (datetime('now')),
    updated_at        TEXT DEFAULT (datetime('now'))
);

-- Named evidence atoms (EA-XXX) — specific, titled evidence items
CREATE TABLE IF NOT EXISTS named_evidence_atoms (
    atom_id           TEXT PRIMARY KEY,   -- e.g. EA-001
    description       TEXT NOT NULL,
    atom_type         TEXT NOT NULL,      -- DOCUMENT|AUDIO|PHOTO|TEXT_MESSAGE|PUBLIC_RECORD|OTHER
    relevance         TEXT DEFAULT '',
    priority          TEXT NOT NULL,      -- CRITICAL | HIGH | MEDIUM
    preserve_note     TEXT DEFAULT '',
    fact_refs_json    TEXT DEFAULT '[]',  -- JSON array of FE-XXX IDs
    created_at        TEXT DEFAULT (datetime('now')),
    updated_at        TEXT DEFAULT (datetime('now'))
);

-- Violations inventory (V-XXX)
CREATE TABLE IF NOT EXISTS violations_inventory (
    violation_id   TEXT PRIMARY KEY,      -- e.g. V-001
    category       TEXT NOT NULL,         -- JUDICIAL_MISCONDUCT|DUE_PROCESS|ATTORNEY_MISCONDUCT|PPO_FRAUD|ABUSE_OF_PROCESS|CHILD_SAFETY
    summary        TEXT NOT NULL,
    fact_refs_json TEXT DEFAULT '[]',     -- JSON array of FE-XXX IDs
    created_at     TEXT DEFAULT (datetime('now')),
    updated_at     TEXT DEFAULT (datetime('now'))
);

-- Ranked litigation vehicles
CREATE TABLE IF NOT EXISTS litigation_vehicles (
    vehicle_id           TEXT PRIMARY KEY, -- e.g. RANK-01
    rank                 INTEGER NOT NULL,
    tier                 INTEGER NOT NULL, -- 1|2|3|4
    name                 TEXT NOT NULL,
    authority            TEXT DEFAULT '',
    court                TEXT DEFAULT '',
    basis_json           TEXT DEFAULT '[]',
    evidence_needed_json TEXT DEFAULT '[]',
    assurance            INTEGER DEFAULT 0,
    notes                TEXT DEFAULT '',
    created_at           TEXT DEFAULT (datetime('now')),
    updated_at           TEXT DEFAULT (datetime('now'))
);

-- Overall case state (single-row table, id=1)
CREATE TABLE IF NOT EXISTS case_state (
    id                   INTEGER PRIMARY KEY DEFAULT 1,
    assurance            INTEGER NOT NULL,
    assurance_label      TEXT NOT NULL,
    severity             INTEGER NOT NULL,
    days_since_contact   INTEGER NOT NULL,
    last_contact_date    TEXT NOT NULL,
    total_violations     INTEGER NOT NULL,
    total_facts          INTEGER NOT NULL,
    total_evidence_atoms INTEGER NOT NULL,
    sbna                 TEXT DEFAULT '',
    updated_at           TEXT DEFAULT (datetime('now'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_facts_state ON extracted_facts(fact_state);
CREATE INDEX IF NOT EXISTS idx_atoms_priority ON named_evidence_atoms(priority);
CREATE INDEX IF NOT EXISTS idx_violations_cat ON violations_inventory(category);
CREATE INDEX IF NOT EXISTS idx_vehicles_rank ON litigation_vehicles(rank);
CREATE INDEX IF NOT EXISTS idx_vehicles_tier ON litigation_vehicles(tier);
"""


def add_case_intelligence_schema(conn) -> None:
    """Create the case-intelligence tables in *conn* (idempotent).

    Uses ``CREATE TABLE IF NOT EXISTS`` throughout, so it is safe to call
    on an existing database — it will only add tables that are absent.
    """
    conn.executescript(CASE_INTELLIGENCE_SCHEMA)
    conn.commit()


def _current_schema_version(conn) -> str:
    """Return the stored schema_version, or '0.0.0' if not set."""
    try:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'schema_version'"
        ).fetchone()
        return row[0] if row else "0.0.0"
    except Exception:
        return "0.0.0"


def init_db():
    """Initialize the Copilot state database with full schema.

    Idempotent: safe to call on both new and existing databases.
    All DDL uses ``CREATE TABLE IF NOT EXISTS`` / ``CREATE INDEX IF NOT EXISTS``,
    so existing data is never dropped.  The schema_version is bumped to
    ``1.1.0`` only when the current stored version is older.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript(SCHEMA)
    add_case_intelligence_schema(conn)
    existing_version = _current_schema_version(conn)
    # Only update the version tag when we are actually upgrading.
    if existing_version < "1.1.0":
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            ("schema_version", "1.1.0"),
        )
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        ("created_by", "copilot_state_init"),
    )
    conn.commit()
    return conn


def register_agents(conn):
    """Register the full agent fleet into the registry."""
    agents = [
        # Delta9 Lane 1 — I/O Infrastructure
        ("A01", "delta9", "1", "1", "IndexScoutC", "agents/lane1/a01_index_scout_c.py", "Index C: drive files"),
        ("A02", "delta9", "1", "1", "IndexScoutD", "agents/lane1/a02_index_scout_d.py", "Index D: drive files"),
        ("A03", "delta9", "1", "1", "IndexScoutF", "agents/lane1/a03_index_scout_f.py", "Index F: drive files"),
        ("A04", "delta9", "1", "1", "IndexScoutGI", "agents/lane1/a04_index_scout_gi.py", "Index G,H,I: drives"),
        ("A05", "delta9", "2", "1", "LegalDedup", "agents/lane1/a05_legal_dedup.py", "Dedup legal files"),
        ("A06", "delta9", "2", "1", "DataDedup", "agents/lane1/a06_data_dedup.py", "Dedup data files"),
        ("A07", "delta9", "2", "1", "CodeDedup", "agents/lane1/a07_code_dedup.py", "Dedup code files"),
        ("A08", "delta9", "2", "1", "ArchiveCracker", "agents/lane1/a08_archive_cracker.py", "Extract & catalog archives"),
        ("A09", "delta9", "3", "1", "FlattenCommander", "agents/lane1/a09_flatten_commander.py", "Orchestrate file flattening"),
        ("A10", "delta9", "3", "1", "PdfHarvester", "agents/lane1/a10_pdf_harvester.py", "Extract PDF content"),
        ("A11", "delta9", "3", "1", "TextMiner", "agents/lane1/a11_text_miner.py", "Mine text for atoms"),
        ("A12", "delta9", "3", "1", "StructParser", "agents/lane1/a12_struct_parser.py", "Parse structured data"),
        # Delta9 Lane 2 — Intelligence
        ("J01", "delta9", "J", "2", "McNeillProfiler", "agents/lane2/j01_mcneill_profiler.py", "Profile Judge McNeill"),
        ("J02", "delta9", "J", "2", "HoopesProfiler", "agents/lane2/j02_hoopes_profiler.py", "Profile Judge Hoopes"),
        ("J03", "delta9", "J", "2", "BenchbookAuditor", "agents/lane2/j03_benchbook_auditor.py", "Audit benchbook compliance"),
        ("J04", "delta9", "J", "2", "CanonMapper", "agents/lane2/j04_canon_mapper.py", "Map judicial canons"),
        ("J05", "delta9", "J", "2", "JtcCompiler", "agents/lane2/j05_jtc_compiler.py", "Compile JTC standards"),
        ("J06", "delta9", "J", "2", "DisqualificationEngine", "agents/lane2/j06_disqualification.py", "Detect disqualification triggers"),
        ("J07", "delta9", "J", "2", "ExParteDetector", "agents/lane2/j07_exparte_detector.py", "Detect ex parte violations"),
        ("J08", "delta9", "J", "2", "TranscriptImpeacher", "agents/lane2/j08_transcript_impeacher.py", "Find transcript contradictions"),
        ("K01", "delta9", "K", "2", "LaneACustody", "agents/lane2/k01_lane_a_custody.py", "Lane A custody analysis"),
        ("K02", "delta9", "K", "2", "LaneAPpo", "agents/lane2/k02_lane_a_ppo.py", "Lane A PPO analysis"),
        ("K03", "delta9", "K", "2", "LaneBHousing", "agents/lane2/k03_lane_b_housing.py", "Lane B housing analysis"),
        ("K04", "delta9", "K", "2", "LaneCConvergence", "agents/lane2/k04_lane_c_convergence.py", "Lane C cross-lane analysis"),
        ("K05", "delta9", "K", "2", "PersonProfiler", "agents/lane2/k05_person_profiler.py", "Profile case persons"),
        ("K06", "delta9", "K", "2", "TimelineBuilder", "agents/lane2/k06_timeline_builder.py", "Construct event timeline"),
        ("K07", "delta9", "K", "2", "AuthorityHarvester", "agents/lane2/k07_authority_harvester.py", "Extract legal authority"),
        ("K08", "delta9", "K", "2", "ContradictionDetector", "agents/lane2/k08_contradiction_detector.py", "Find contradictions"),
        ("K09", "delta9", "K", "2", "LaneDPPOIntel", "agents/lane2/k09_lane_d_ppo.py", "Lane D PPO intelligence"),
        ("K10", "delta9", "K", "2", "LaneEMisconductIntel", "agents/lane2/k10_lane_e_misconduct.py", "Lane E misconduct intel"),
        ("K11", "delta9", "K", "2", "LaneFAppellateIntel", "agents/lane2/k11_lane_f_appellate.py", "Lane F appellate intel"),
        # Delta9 — Legal Warfare
        ("L01", "delta9", "L", "2", "LaneAScorer", "agents/lane2/l01_lane_a_scorer.py", "Score Lane A evidence"),
        ("L02", "delta9", "L", "2", "LaneBScorer", "agents/lane2/l02_lane_b_scorer.py", "Score Lane B evidence"),
        ("L03", "delta9", "L", "2", "LaneCScorer", "agents/lane2/l03_lane_c_scorer.py", "Score Lane C evidence"),
        ("L04", "delta9", "L", "2", "GapDetector", "agents/lane2/l04_gap_detector.py", "Detect evidence gaps"),
        ("L05", "delta9", "L", "2", "CitationValidator", "agents/lane2/l05_citation_validator.py", "Validate legal citations"),
        ("L06", "delta9", "L", "2", "DamagesCalculator", "agents/lane2/l06_damages_calculator.py", "Calculate damages"),
        ("L07", "delta9", "L", "2", "FilingReadiness", "agents/lane2/l07_filing_readiness.py", "Judge filing readiness"),
        ("L08", "delta9", "L", "2", "RedTeamScanner", "agents/lane2/l08_red_team_scanner.py", "Red-team analysis"),
        ("L09", "delta9", "L", "2", "LaneDScorer", "agents/lane2/l09_lane_d_scorer.py", "Score Lane D evidence"),
        ("L10", "delta9", "L", "2", "LaneEScorer", "agents/lane2/l10_lane_e_scorer.py", "Score Lane E evidence"),
        ("L11", "delta9", "L", "2", "LaneFScorer", "agents/lane2/l11_lane_f_scorer.py", "Score Lane F evidence"),
        # Convergence
        ("F01", "convergence", "F", "convergence", "FilingFactory", "agents/convergence/f01_filing_factory.py", "Assemble court filings"),
        ("F02", "convergence", "F", "convergence", "BrainFeeder", "agents/convergence/f02_brain_feeder.py", "Feed outputs to brain DB"),
        ("F03", "convergence", "F", "convergence", "GraphBuilder", "agents/convergence/f03_graph_builder.py", "Build knowledge graph"),
        ("F04", "convergence", "F", "convergence", "MscArchitect", "agents/convergence/f04_msc_architect.py", "Architect MSC briefs"),
        ("F05", "convergence", "F", "convergence", "TestRunner", "agents/convergence/f05_test_runner.py", "Run validation tests"),
        ("F06", "convergence", "F", "convergence", "ConvergenceCertifier", "agents/convergence/f06_convergence_certifier.py", "Certify filing readiness"),
        # Delta999 Specialist Agents
        ("D999-orch", "delta999", "D999", "specialist", "Delta999Orchestrator", "engines/agents/delta999_orchestrator.py", "Master dispatcher"),
        ("D999-coa", "delta999", "D999", "specialist", "COAAgent", "engines/agents/delta999_coa_agent.py", "Cause of action analysis"),
        ("D999-evidence", "delta999", "D999", "specialist", "EvidenceChainAgent", "engines/agents/delta999_evidence_chain_agent.py", "Evidence chain validation"),
        ("D999-citation", "delta999", "D999", "specialist", "CitationAgent", "engines/agents/delta999_citation_agent.py", "Citation validation"),
        ("D999-compliance", "delta999", "D999", "specialist", "ComplianceAgent", "engines/agents/delta999_compliance_agent.py", "Rule compliance checking"),
        ("D999-damages", "delta999", "D999", "specialist", "DamagesAgent", "engines/agents/delta999_damages_agent.py", "Harm quantification"),
        ("D999-discovery", "delta999", "D999", "specialist", "DiscoveryAgent", "engines/agents/delta999_discovery_agent.py", "FOIA/discovery generation"),
        ("D999-rebuttal", "delta999", "D999", "specialist", "RebuttalAgent", "engines/agents/delta999_rebuttal_agent.py", "Counter-argument analysis"),
        ("D999-redteam", "delta999", "D999", "specialist", "RedTeamAgent", "engines/agents/delta999_redteam_agent.py", "Adversarial testing"),
        ("D999-service", "delta999", "D999", "specialist", "ServiceAgent", "engines/agents/delta999_service_agent.py", "Service of process analysis"),
        ("D999-timeline", "delta999", "D999", "specialist", "TimelineAgent", "engines/agents/delta999_timeline_agent.py", "Event sequencing"),
        ("D999-trial", "delta999", "D999", "specialist", "TrialAgent", "engines/agents/delta999_trial_agent.py", "Trial strategy"),
        # NEW: Organization agents (Omega Plan v5.0)
        ("ORG-intake", "organization", "org", "org", "IntakeWatcher", "org_agents/intake_watcher.py", "Monitor _INBOX, auto-classify & route new files"),
        ("ORG-classifier", "organization", "org", "org", "FileClassifier", "org_agents/file_classifier.py", "AI-classify files: lane, doc_type, parties, dates"),
        ("ORG-dedup", "organization", "org", "org", "ContentDedup", "org_agents/content_dedup.py", "Content-based dedup: SHA256 + text comparison"),
        ("ORG-linker", "organization", "org", "org", "RelationshipLinker", "org_agents/relationship_linker.py", "Link evidence→filings, detect supersession chains"),
        ("ORG-tier", "organization", "org", "org", "TierManager", "org_agents/tier_manager.py", "Promote/demote files between hot C: and cold I:"),
    ]

    for a in agents:
        conn.execute(
            """INSERT OR REPLACE INTO agent_registry 
               (agent_id, agent_type, tier, lane, name, file_path, description)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            a,
        )
    conn.commit()
    return len(agents)


def register_models(conn):
    """Register all known AI models."""
    models = [
        ("saul-instruct-q5", "Saul Instruct v1 Q5_K_M", "gguf", "local_model/saul-instruct-v1.Q5_K_M.gguf", 4893.7, "gguf", '["legal_reasoning","generation","analysis"]'),
        ("qwen25-1.5b-q4", "Qwen 2.5 1.5B Q4_K_M", "gguf", "local_model/qwen2.5-1.5b-instruct-q4_k_m.gguf", 1065.6, "gguf", '["general_reasoning","classification","fast_inference"]'),
        ("legal-bert-small", "Legal-BERT Small Uncased", "pytorch", "local_model/nlpaueb_legal-bert-small-uncased/pytorch_model.bin", 134.9, "bin", '["legal_embeddings","classification"]'),
        ("bert-base-ner", "BERT Base NER", "pytorch", "local_model/dslim_bert-base-NER/pytorch_model.bin", 413.2, "bin", '["entity_extraction","ner"]'),
        ("minilm-l6-v2", "MiniLM-L6-v2 Sentence Transformer", "embedding", "local_model/sentence-transformers_all-MiniLM-L6-v2/pytorch_model.bin", 86.7, "bin", '["semantic_similarity","embeddings"]'),
        ("bm25-index", "BM25 Inverted Index", "bm25", "local_model/inverted_index.pkl", 205.7, "pkl", '["full_text_search","retrieval"]'),
        ("tfidf-matrix", "TF-IDF Sparse Matrix", "tfidf", "local_model/tfidf_matrix.npz", 87.0, "npz", '["vector_retrieval","similarity"]'),
        ("doctype-clf", "Document Type Classifier", "sklearn", "local_model/doctype_clf.pkl", 86.2, "pkl", '["document_classification"]'),
        ("intent-clf", "Legal Intent Classifier", "sklearn", "local_model/intent_clf.pkl", 6.1, "pkl", '["intent_classification"]'),
        ("tfidf-vectorizer", "TF-IDF Vectorizer", "tfidf", "local_model/vectorizer.pkl", 1.9, "pkl", '["text_vectorization"]'),
    ]

    for m in models:
        conn.execute(
            """INSERT OR REPLACE INTO ai_model_registry 
               (model_id, model_name, model_type, file_path, file_size_mb, format, capabilities)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            m,
        )
    conn.commit()
    return len(models)


def take_snapshot(conn, operation_id=None, snapshot_type="manual", notes=""):
    """Capture current system state as a snapshot."""
    import subprocess

    # Drive space
    drive_space = {}
    for letter in ["C", "D", "F", "G", "H", "I"]:
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 f"$d = Get-PSDrive {letter} -ErrorAction SilentlyContinue; "
                 f"if($d){{'{letter}|' + [math]::Round($d.Free/1GB,1).ToString() + '|' + [math]::Round($d.Used/1GB,1).ToString()}}"],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout.strip():
                parts = result.stdout.strip().split("|")
                drive_space[parts[0]] = {"free_gb": float(parts[1]), "used_gb": float(parts[2])}
        except Exception:
            pass

    # DB health
    db_health = {}
    main_db = LITIGOS_ROOT / "litigation_context.db"
    if main_db.exists():
        db_health["size_gb"] = round(main_db.stat().st_size / (1024**3), 2)
        try:
            c = sqlite3.connect(str(main_db))
            tables = c.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
            db_health["tables"] = tables
            c.close()
        except Exception:
            pass

    conn.execute(
        """INSERT INTO state_snapshots 
           (operation_id, snapshot_type, drive_space_json, db_health_json, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (operation_id, snapshot_type, json.dumps(drive_space), json.dumps(db_health), notes),
    )
    conn.commit()
    print(f"  Snapshot saved: {snapshot_type} | Drives: {list(drive_space.keys())}")


def main():
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")
    print("=" * 60)
    print("  COPILOT STATE DATABASE — INITIALIZATION")
    print("=" * 60)

    conn = init_db()
    print(f"\n✅ Database created: {DB_PATH}")
    print(f"   Size: {DB_PATH.stat().st_size / 1024:.1f} KB")

    tables = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    print(f"   Tables: {tables}")

    n_agents = register_agents(conn)
    print(f"\n✅ Agent fleet registered: {n_agents} agents")

    n_models = register_models(conn)
    print(f"✅ AI models registered: {n_models} models")

    # Register OMEGA v5.0 as the first operation
    conn.execute(
        """INSERT OR REPLACE INTO operations 
           (id, name, description, status, total_phases, config_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            "omega-v5.0",
            "OMEGA Organization Plan v5.0",
            "Outside-In: I:\\ first → Clean & organize → Absorb D/F/G/H → Fresh C:\\ analysis",
            "planned",
            4,
            json.dumps({
                "strategy": "outside-in",
                "phases": ["I:\\ Recovery", "I:\\ Organization", "Migrate D/F/G/H", "Fresh C:\\ Analysis"],
                "target_i_free_gb": 80,
                "target_c_free_gb": 70,
            }),
        ),
    )

    # Register phases
    phases = [
        ("omega-v5.0-p1", "omega-v5.0", 1, "I:\\ Deep Analysis + Space Recovery", "Recover 80-120 GB on I:\\ via dedup, git analysis, archive merge"),
        ("omega-v5.0-p2", "omega-v5.0", 2, "I:\\ Organization", "Reorganize I:\\ into EVIDENCE/ARCHIVE/DEDUP/BACKUP structure"),
        ("omega-v5.0-p3", "omega-v5.0", 3, "Migrate D/F/G/H → I:\\", "Consolidate satellite drives onto organized I:\\"),
        ("omega-v5.0-p4", "omega-v5.0", 4, "Fresh C:\\ Analysis + Org", "Clean C:\\ with full context of organized I:\\"),
    ]
    for p in phases:
        conn.execute(
            """INSERT OR REPLACE INTO operation_phases 
               (id, operation_id, phase_number, name, description)
               VALUES (?, ?, ?, ?, ?)""",
            p,
        )

    conn.commit()
    print(f"✅ Operation 'omega-v5.0' registered with {len(phases)} phases")

    # Take initial snapshot
    print("\n📸 Taking initial system snapshot...")
    take_snapshot(conn, "omega-v5.0", "pre_operation", "Initial state before OMEGA v5.0 execution")

    # Link current Copilot session
    session_id = "4e7a9d99-0664-449c-b2ec-00e5cf9867a9"
    conn.execute(
        """INSERT OR REPLACE INTO session_links (session_id, operation_id, summary)
           VALUES (?, ?, ?)""",
        (session_id, "omega-v5.0", "Session that created OMEGA v5.0 plan and initialized state DB"),
    )
    conn.commit()

    # Final report
    print("\n" + "=" * 60)
    agent_counts = conn.execute(
        "SELECT agent_type, count(*) FROM agent_registry GROUP BY agent_type ORDER BY count(*) DESC"
    ).fetchall()
    print("  AGENT FLEET:")
    for t, c in agent_counts:
        print(f"    {t:15s} = {c} agents")

    model_counts = conn.execute(
        "SELECT model_type, count(*) FROM ai_model_registry GROUP BY model_type ORDER BY count(*) DESC"
    ).fetchall()
    print("  AI MODELS:")
    for t, c in model_counts:
        print(f"    {t:15s} = {c} models")

    print("=" * 60)
    print(f"  TOTAL: {sum(c for _, c in agent_counts)} agents + {sum(c for _, c in model_counts)} models")
    print(f"  DB PATH: {DB_PATH}")
    print("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
