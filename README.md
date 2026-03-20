# ⚖️ LitigationOS

**A local-first, AI-powered litigation intelligence system for Michigan family law.**

LitigationOS is a self-contained command center that processes raw evidence across multiple drives, maintains a structured litigation database, and produces complete court-ready filing packages — all without sending a single byte to the cloud. Built and operated by Andrew Pigors (pro se litigant) in *Pigors v. Watson*, consolidated Muskegon County proceedings.

---

## Table of Contents

- [Overview](#overview)
- [Key Capabilities](#key-capabilities)
- [Architecture](#architecture)
- [Repository Layout](#repository-layout)
- [Agent Fleet](#agent-fleet)
- [The MANBEARPIG Inference Engine](#the-manbearpig-inference-engine)
- [MCP Server](#mcp-server)
- [Six Case Lanes](#six-case-lanes)
- [Filing Pipeline](#filing-pipeline)
- [Database](#database)
- [Getting Started](#getting-started)
- [Security & Privacy](#security--privacy)

---

## Overview

| Property | Value |
|----------|-------|
| **Version** | Golden Master v0.9.0 |
| **Platform** | Windows 10/11, Python ≥ 3.12 |
| **Network policy** | **Zero external API calls** — all AI inference is local |
| **Central database** | SQLite WAL, 782+ tables, ~11.5 GB, FTS5 full-text search *(run `SELECT COUNT(*) FROM sqlite_master WHERE type='table'` for live count)* |
| **Agent fleet** | 155+ specialized agents (Delta9, Delta999, Copilot, Superpower, Convergence) |
| **Filing vehicles** | 24 tracked across 6 case lanes, 7 clerk-ready packages |

---

## Key Capabilities

### 🔍 Evidence Intelligence
- Scans 6 drives (C, D, F, G, H, I) for PDFs, images, audio, and documents
- Content-based deduplication — never relies on file hashes alone
- Extracts and atomises evidence into structured `EvidenceAtom` records
- Hybrid semantic + BM25 keyword search across ~308,704 indexed evidence quotes *(live: `SELECT COUNT(*) FROM evidence_quotes`)*
- Contradiction detector cross-references witness statements and prior sworn testimony
- ~15,171 impeachment items catalogued; ~10,672 contradictions mapped *(run startup hook for current counts)*

### 📋 Filing Factory
- Generates complete court packages: motion + brief + proposed order + affidavit + exhibit index + proof of service
- Auto-fills Michigan SCAO forms (39 forms, 31 mappings) from database values
- Citation validator checks every authority reference before assembly
- Pre-filing QA engine issues GO / NO-GO decisions with gap analysis
- Bates-stamps exhibits and produces a master exhibit index
- Supports MiFILE, TrueFiling, PACER/CM-ECF, and mail filing workflows

### 🧠 Local AI (MANBEARPIG)
- TF-IDF + Naive Bayes + BM25 + cosine similarity — 30 legal skills, 140+ JSON-RPC methods
- Covers 5 jurisdictions: MI Circuit, COA, MSC, Federal (WDMI), JTC
- No Ollama, no OpenAI, no remote provider of any kind
- Self-evolves via `self_evolve_v2.py`; retrains in ~60 seconds

### ⏱️ Deadline & Docket Tracking
- 23 active deadlines with statutory authority citations
- Escalating alerts at 90 / 60 / 30 / 14 / 7 / 3 / 1 day marks
- ICS calendar export; MCP tool `litigation_upcoming_deadlines`

### 🔒 Data Safety
- Phase 0 safety snapshot (SHA-256 manifest) before any destructive operation
- No hard deletions — files moved to `I:\` recycle area
- All DB writes use WAL mode + `busy_timeout = 60 000 ms`

---

## Architecture

```
Raw Files (C:\, D:\, F:\, G:\, H:\, I:\)
  │
  ├─ Phase 0  ─── Safety snapshot (SHA-256 manifest)
  ├─ Phase 1  ─── Drive inventory
  ├─ Phase 2  ─── Content-based deduplication
  ├─ Phase 3  ─── Lane classification (MEEK signals)
  ├─ Phases 4a-4e ─ Extraction (PDF / DOCX / structured / atomise / archive)
  ├─ Phase 5  ─── MANBEARPIG brain feed (50 micro-brains, 8 categories)
  ├─ Phase 6  ─── Gap analysis (EGCP scoring per legal action)
  ├─ Phases 7a-7c ─ Graph delta → synthesis merge → knowledge merge
  ├─ Phase 8  ─── Litigation refresh
  ├─ Phase 9  ─── MCP ingest
  ├─ Phases 10-12 ─ Judicial analysis → legal action discovery → rule audit
  ├─ Phases 13-16 ─ Refinement → finalization → validation → desktop offload
  │
  └─ Court-ready filing packages
```

### Core Subsystems

| Subsystem | Location | Purpose |
|-----------|----------|---------|
| Pipeline (16 phases) | `00_SYSTEM/pipeline/` | End-to-end data processing |
| Agent fleet (155+) | `agents/`, `00_SYSTEM/pipeline/agents/` | Specialised processing units |
| MANBEARPIG | `00_SYSTEM/local_model/` | Local ML inference engine |
| Filing Factory | `00_SYSTEM/pipeline/filing_factory.py` | Court-ready package generation |
| MCP Server | `00_SYSTEM/mcp_server/` | Tool API for Copilot integrations |
| Engines (Phase 5-6) | `00_SYSTEM/engines/` | Standalone production engines |
| Scripts / Tools | `00_SYSTEM/tools/`, `08_TOOLS/` | 40+ utility scripts |
| Filings | `01_FILINGS/` | All draft and clerk-ready packages |
| Evidence | `03_EVIDENCE/` | Scanned and classified evidence |

---

## Repository Layout

```
LitigationOS/
├── 00_SYSTEM/
│   ├── pipeline/           # 16-phase processing pipeline + agents
│   │   ├── filing_factory.py
│   │   ├── semantic_search.py
│   │   ├── connection_multiplexer.py
│   │   └── agents/         # Delta9 + Delta999 fleet
│   ├── local_model/        # MANBEARPIG inference engine
│   │   ├── inference_engine.py
│   │   ├── train_model.py
│   │   └── self_evolve_v2.py
│   ├── mcp_server/         # MCP server (litigation-context-mcp)
│   │   └── litigation_context_mcp/
│   ├── engines/            # Phase 5-6 production engines
│   ├── reports/            # Generated analysis reports
│   ├── scripts/            # Utility scripts
│   └── tools/              # 40+ litigation tools
├── 01_FILINGS/
│   ├── CLERK_READY/        # Finalised, clerk-ready packages
│   ├── COA_366810/         # Court of Appeals brief + motions
│   ├── TRIAL_14TH/         # 14th Circuit trial motions
│   ├── MSC_ACTION/         # Michigan Supreme Court original action
│   ├── FEDERAL_1983/       # 42 USC §1983 federal complaint
│   ├── SHADY_OAKS_CIRCUIT/ # Housing circuit court complaint
│   ├── SHADY_OAKS_FEDERAL/ # Housing federal complaint
│   └── DISQUALIFICATION/   # Judicial disqualification motion
├── 03_EVIDENCE/            # Classified evidence files
├── agents/                 # Orchestrator + specialized agents
│   ├── orchestrator.py
│   ├── evidence_agent.py
│   ├── chronology_agent.py
│   ├── filing_agent.py
│   └── authority_agent.py
├── core/                   # Shared utilities
├── docs/                   # Legal analysis documents
├── skills/                 # OMEGA skill definitions
└── temp/                   # Scratch / working area (not committed)
```

---

## Agent Fleet

All agents implement the `Agent9999` base contract: `run() → AgentResult(agent_id, status, stats)` with three possible statuses: `SUCCESS | FATAL | CRASH`.

| Fleet | Count | Role |
|-------|-------|------|
| **Delta9** (A01–L08) | 56 | Core pipeline — indexing, dedup, extraction, intelligence |
| **Delta999** | 12 | Advanced engines — classifier, validator, brief, assembly, deadline, DB lock |
| **Copilot agents** | 64 | Specialised Copilot sub-agents |
| **Superpower agents** | 13 | Cross-cutting orchestration and governance |
| **Convergence agents** | 10 | Filing workflow, complaint prep, MCP v2 |

### Seven-Layer Error Protocol (every agent)

1. Try operation
2. Specific exception catch → targeted recovery
3. Broad exception catch → log + skip + continue
4. Checkpoint every N items → crash-resume
5. Deadman switch (120 s no progress → self-diagnose)
6. Agent retry (3× exponential back-off)
7. Tier fallback → orchestrator flags + continues

### Running the Fleet

```powershell
# Full fleet run
python -m agents.agent_orchestrator

# Single tier
python -m agents.agent_orchestrator --tier J

# Single agent
python -m agents.agent_orchestrator --agent J01

# Dry run
python -m agents.agent_orchestrator --dry-run
```

---

## The MANBEARPIG Inference Engine

> **100% local. 100% offline. Zero API keys required.**

`00_SYSTEM/local_model/inference_engine.py` — the primary AI brain for legal analysis.

**Capabilities:**
- TF-IDF + Naive Bayes text classification (200K docs, 50K features)
- BM25 full-text retrieval via SQLite FTS5
- Cosine similarity over dense embeddings (384-dim, `sqlite-vec`)
- 30 legal skills covering Michigan Circuit, COA, MSC, Federal WDMI, and JTC
- 140+ JSON-RPC methods exposed over stdin/stdout pipe
- 29 legal concepts, 9 MSC action types

**Usage:**

```bash
# Python API
from inference_engine import MichiganLegalModel
model = MichiganLegalModel()
result = model.query("What does MCR 2.003 say about disqualification?")

# CLI
python 00_SYSTEM/local_model/inference_engine.py "your question here"

# JSON-RPC pipe mode (for JS / MCP integration)
python 00_SYSTEM/local_model/inference_engine.py --pipe

# Train / retrain (≈60 seconds)
python 00_SYSTEM/local_model/train_model.py

# Self-evolution cycle
python 00_SYSTEM/local_model/self_evolve_v2.py
```

---

## MCP Server

`00_SYSTEM/mcp_server/litigation_context_mcp/` — the `litigation-context-mcp` server exposes the litigation database and filing tools to Copilot and other MCP-compatible clients.

**Install and run:**

```bash
cd 00_SYSTEM/mcp_server
pip install -e .
litigation-context-mcp
```

**Tool categories (45 tools total):**

| Category | Example Tools |
|----------|--------------|
| Core | `search`, `list_documents`, `get_document`, `get_stats` |
| Filing | `filing_readiness`, `filing_assemble`, `efiling_prep`, `prefiling_qa` |
| Evidence | `evidence_chain`, `evidence_gaps`, `bates_assign`, `exhibit_index` |
| Deadline | `deadline_dashboard`, `deadline_ics`, `deadline_urgency` |
| Analysis | `authority_index`, `citation_graph`, `impeachment_search`, `contradiction_find` |
| QA | `prefiling_qa`, `qa_sweep`, `signature_check`, `service_check` |
| Backup | `backup_create`, `backup_version`, `backup_report` |
| System | `system_health` |

All tools are prefixed `litigation_` (e.g. `litigation_deadline_dashboard`).

---

## Six Case Lanes

Evidence and filings are strictly segregated by case lane — cross-contamination raises a `LaneCrossContaminationError`.

| Lane | Subject | Case Numbers | Court |
|------|---------|-------------|-------|
| **A** | Watson custody | 2024-001507-DC | 14th Circuit Court, Muskegon County |
| **B** | Shady Oaks housing | 2025-002760-CZ | Van Buren County Circuit |
| **C** | Convergence (cross-lane) | Multi | Various |
| **D** | PPO / protection orders | 2023-5907-PP | 14th Circuit Court, Muskegon County |
| **E** | Judicial misconduct / JTC | Multi | JTC / Michigan Supreme Court |
| **F** | Appellate (COA / MSC) | COA 366810 | Michigan Court of Appeals |

Detection priority: **E → D → F → C → A → B**

---

## Filing Pipeline

The full path from evidence to clerk-ready package:

```
1.  Draft complaint / motion (filing_factory.py or agent)
2.  Auto-fill SCAO forms from litigation_context.db
3.  Run brief compliance check (MCR 2.113 / 7.212)
4.  Run pre-filing QA → GO / NO-GO verdict
5.  Resolve remaining placeholders (placeholder_resolver)
6.  Assemble e-filing packet (efiling_prep_engine.py)
7.  Review EFILING_CHECKLIST.md
8.  Convert MD → PDF (pandoc / doc_assembly_engine.py)
9.  Upload to e-filing system (MiFILE / TrueFiling / PACER)
10. Record proof of service
```

### Supported Courts

| Court | E-Filing System | Key Authority |
|-------|----------------|--------------|
| 14th Circuit Court | MiFILE | MCR 2.113 |
| Michigan Court of Appeals | TrueFiling | MCR 7.212 |
| Michigan Supreme Court | TrueFiling | MCR 7.305 |
| USDC Western District of Michigan | PACER / CM-ECF | 42 USC §1983 |
| Judicial Tenure Commission | Mail only | MCR 9.200 |

### Current Filing Readiness (top vehicles)

| Vehicle | Score | Status |
|---------|-------|--------|
| Judicial Disqualification | 97 / 100 | Evidence Ready |
| Contempt Show Cause | 97 / 100 | Evidence Ready |
| Modify / Terminate PPO | 95 / 100 | Evidence Ready |
| Emergency Motion — Restore Parenting Time | 94 / 100 | Evidence Ready |
| COA Appellant Brief 366810 | 84 / 100 | Ready (due Apr 15) |
| MSC Superintending Control | 82 / 100 | Ready |
| JTC Complaint | 80 / 100 | Evidence Ready |
| 42 USC §1983 Federal Complaint | 78 / 100 | Ready |

---

## Database

The central SQLite database `litigation_context.db` is the single source of truth. Statistics below are approximate — always query the live database for current counts (run `python 00_SYSTEM/local_model/copilot_startup_hook.py --file` for a full runtime report).

| Metric | Approximate Value | Live Query |
|--------|-------------------|-----------|
| Tables | 782+ | `SELECT COUNT(*) FROM sqlite_master WHERE type='table'` |
| Size | ~11.5 GB | `SELECT (page_count * page_size) / (1024*1024*1024.0) FROM pragma_page_count(), pragma_page_size()` |
| Journal mode | WAL | `PRAGMA journal_mode` |
| Full-text search | 70+ FTS5 indexes | — |
| Evidence quotes | ~308,704 | `SELECT COUNT(*) FROM evidence_quotes` |
| Judicial violations | ~1,127 (377 critical) | `SELECT COUNT(*) FROM judicial_violations` |
| Impeachment items | ~15,171 | `SELECT COUNT(*) FROM impeachment_items` |
| Contradictions mapped | ~10,672 | `SELECT COUNT(*) FROM contradiction_map` |
| Active legal claims | ~653 | `SELECT COUNT(*) FROM claims` |
| Active deadlines | 23 | `SELECT COUNT(*) FROM deadlines` |

### Connection requirements (all tiers)

```python
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;   -- 32 MB
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
```

Use `managed_db()` from `db_lock_manager.py` for all database access — it enforces the 3-connection cap and handles lock contention automatically.

---

## Getting Started

### Prerequisites

- Python ≥ 3.12
- Windows 10 / 11 (pipeline uses Windows paths; agents are cross-platform)
- SQLite ≥ 3.39 (WAL mode, FTS5 support)

### Install dependencies

```bash
# Core pipeline + agents
pip install -r requirements.txt   # if present, or install per module

# Product app (CustomTkinter GUI)
cd 11_CODE/litigationos
pip install -e ".[dev]"

# MCP server
cd 00_SYSTEM/mcp_server
pip install -e .
```

### Run the pipeline

```powershell
cd 00_SYSTEM/pipeline

# Full 16-phase run
python run_omega_pipeline.py

# Phase range
python run_omega_pipeline.py --start-phase 4a --end-phase 7c

# Dry run with snapshot
python run_omega_pipeline.py --dry-run --create-snapshot

# List available phases
python run_omega_pipeline.py --list-phases
```

### Query the inference engine

```bash
python 00_SYSTEM/local_model/inference_engine.py "MCR 2.003 disqualification requirements"
```

### Run tests

```bash
cd 11_CODE/litigationos
python -m pytest tests/ -q
```

---

## Security & Privacy

- **No cloud connectivity** — all inference, storage, and processing is local
- **No secrets in source** — API keys, credentials, and PII are never committed
- **Evidence integrity** — SHA-256 manifests guard against tampering; no stats are hard-coded (always queried live from the DB to prevent stale/inflated figures)
- **PII protection** — minor child referenced by initials only (MCR 8.119(H)); `redaction_agent` auto-redacts PII before e-filing
- **Backup-before-write** — Phase 0 snapshot is mandatory before any destructive pipeline operation
- **WAL + busy timeout** — prevents database corruption under concurrent agent load

---

*LitigationOS is a personal legal intelligence tool. Nothing in this repository constitutes legal advice.*
