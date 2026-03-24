# LitigationOS — Architecture

> Litigation intelligence system for Michigan family law (Pigors v. Watson).
> Converts raw evidence across 6 drives into court-ready filings — fully offline, single Windows machine.

## Three Subsystems

```
┌─────────────────────────────────────────────────────────────┐
│                     LitigationOS                            │
├──────────────────┬──────────────────┬───────────────────────┤
│  16-Phase Data   │  MANBEARPIG v9   │  CustomTkinter        │
│  Pipeline        │  AI Engine       │  Desktop App          │
│  (00_SYSTEM/     │  (00_SYSTEM/     │  (11_CODE/            │
│   pipeline/)     │   local_model/)  │   litigationos/)      │
├──────────────────┴──────────────────┴───────────────────────┤
│              litigation_context.db (central)                 │
└─────────────────────────────────────────────────────────────┘
```

### 1. Data Pipeline (16 phases)

Processes raw files from 6 drives through extraction, classification, analysis, and filing assembly.

| Phase | Name | Description |
|-------|------|-------------|
| 0 | Safety Snapshot | SHA-256 manifest + backup before processing |
| 1–3 | Inventory → Dedup → Classify | Scan, deduplicate, assign to litigation lanes via MEEK signals |
| 4a–4e | Extract | PDF, DOCX, structured data, atomize, archives |
| 5–6 | Brain Feed → Gap Analysis | Feed 50 micro-brains, EGCP scoring per legal action |
| 7a–7c | Graph → Synthesis → Knowledge | Build knowledge graph, merge intelligence |
| 8–9 | Litigation Refresh → MCP Ingest | Refresh litigation state, ingest into MCP tools |
| 10–12 | Judicial → Legal Action → Rule Audit | Judicial analysis, legal action discovery, rule compliance |
| 13–16 | Refine → Finalize → Validate → Offload | Court-ready output production and desktop handoff |

### 2. MANBEARPIG v9 — Local AI Inference Engine

100% offline inference engine. Zero API keys, zero network calls.

| Component | Purpose |
|-----------|---------|
| **TF-IDF** | 50K features, trigram vectorization for document similarity |
| **BM25** | Ranked keyword retrieval across 167+ tables |
| **Naive Bayes** | Document classification into 6 case lanes |
| **Semantic Embeddings** | Dense vector similarity for conceptual search |

Additional engines in the stack:

| Engine | Role |
|--------|------|
| MANBEARPIG | Primary inference (TF-IDF + BM25 + NB + embeddings) |
| NOVEL | Invention and novel argument generation |
| DARWIN | Self-evolution and continuous improvement |
| LEXICON | Michigan court rules and legal rule lookup |
| ORACLE | Prediction and outcome forecasting |

Entry points:
```bash
python 00_SYSTEM/local_model/inference_engine.py "MCR 2.003 disqualification"
python 00_SYSTEM/local_model/inference_engine.py --pipe   # JSON-RPC mode
python 00_SYSTEM/local_model/train_model.py               # Retrain (~60s)
python 00_SYSTEM/local_model/self_evolve_v2.py            # Self-evolution cycle
```

### 3. Desktop Application

Pip-installable Python package (Python ≥3.12). CustomTkinter GUI with 14 screens.

- 9 engines, 9 Pydantic models
- SQLite via `DatabaseManager` from `litigationos.db.connection`
- CLI entry: `litigationos` (via typer)
- Jurisdiction plugins (Michigan)

```bash
cd 11_CODE/litigationos
pip install -e ".[dev]"
python -m litigationos          # GUI launch
python -m pytest tests/ -q      # Test suite
```

---

## Directory Structure

```
LitigationOS/
├── 00_SYSTEM/                     # Command center
│   ├── engines/                   # 87+ Python engines (QA, filing, evidence, compliance)
│   ├── pipeline/                  # 16-phase data pipeline + agent fleet
│   │   ├── run_omega_pipeline.py  # Pipeline entry point
│   │   ├── agents/                # Agent9999-based fleet (56 Delta9 agents)
│   │   └── phase*.py              # Individual phase modules
│   ├── local_model/               # MANBEARPIG inference engine + 55 skills
│   │   ├── inference_engine.py    # Primary inference (TF-IDF+BM25+NB)
│   │   ├── train_model.py         # Model training
│   │   ├── self_evolve_v2.py      # Self-evolution daemon
│   │   ├── session_recall.py      # Cross-session memory
│   │   └── copilot_startup_hook.py # Session bootstrap
│   ├── mcp_server/                # MCP v2 server (45+ tools, 9 categories)
│   ├── calendar/                  # ICS deadlines, countdown dashboard
│   ├── tools/                     # safe_shell.py, agent_profile.ps1
│   ├── scripts/                   # Utility scripts (syntax_check, noreply_pdf)
│   └── backups/                   # SHA-256 manifested snapshots
│
├── 01_FILINGS/                    # Filing drafts and clerk-ready packets
│   ├── COA_366810/                # Court of Appeals brief
│   ├── CRIMINAL_TRIAL/            # Criminal trial prep (60th District)
│   ├── DISQUALIFICATION/          # MCR 2.003 disqualification motion
│   ├── CUSTODY/                   # Custody motions (14th Circuit)
│   ├── PPO/                       # PPO response
│   ├── SHADY_OAKS/                # Housing complaint
│   ├── JTC/                       # Judicial Tenure Commission complaint
│   └── CLERK_READY/               # Final clerk-ready packets
│
├── 03_EVIDENCE/                   # Evidence files, exhibits, chains of custody
├── 09_DATA/                       # Structured data and indexes
│
├── 11_CODE/litigationos/          # Product app (pip-installable)
│   ├── src/litigationos/
│   │   ├── engines/               # 9 product engines
│   │   ├── gui/                   # 14 CustomTkinter screens
│   │   ├── models/                # 9 Pydantic data models
│   │   └── plugins/               # Jurisdiction plugins (Michigan)
│   └── tests/                     # Test suite
│
├── databases/                     # Jurisdiction-specific databases
│   ├── lane_A_custody.db
│   ├── lane_B_housing.db
│   ├── lane_C_convergence.db
│   ├── lane_D_ppo.db
│   ├── lane_E_misconduct.db
│   └── lane_F_appellate.db
│
├── .agents/                       # Copilot agent and skill definitions
│   ├── agents/                    # 28 OMEGA v2.0 agent definitions
│   └── skills/                    # 90+ skill definitions (12 OMEGA fusions)
│
├── spec/                          # 8 engineering specifications
├── plan/                          # Implementation plans
├── docs/                          # Additional documentation
└── tests/                         # Integration and system tests
```

---

## Database Architecture

### Central Database: `litigation_context.db`

The single source of truth for the entire system.

| Metric | Value |
|--------|-------|
| Size | ~12 GB |
| Tables | 167+ (run startup hook for current count) |
| Rows | 1.97M+ |
| FTS5 indexes | 52 full-text search virtual tables |
| Journal mode | WAL (concurrent read/write) |

Key tables:

| Table | Rows | Purpose |
|-------|------|---------|
| `master_citations` | ~3.68M | Citation index across all documents |
| `drive_manifest` | ~948K | File inventory across 6 drives |
| `evidence_quotes` | ~309K | Extracted evidence quotations |
| `mined_documents` | ~25K | Processed document metadata |
| `docket_events` | varies | Court docket entries |
| `claims` | varies | Legal claims by case lane |
| `deadlines` | varies | Filing deadlines with urgency scoring |
| `judicial_violations` | varies | Documented judicial misconduct incidents |

### Court Forms Database: `court_forms.db`

| Metric | Value |
|--------|-------|
| Forms | 25 Michigan SCAO forms |
| Coverage | Family, civil, criminal, appellate divisions |

### Lane Databases (6)

Each case lane has a dedicated database for lane-specific data:

| Database | Lane | Case |
|----------|------|------|
| `lane_A_custody.db` | A — Custody | 2024-001507-DC |
| `lane_B_housing.db` | B — Housing | 2025-002760-CZ |
| `lane_C_convergence.db` | C — Cross-lane | Multi-lane |
| `lane_D_ppo.db` | D — PPO | 2023-5907-PP |
| `lane_E_misconduct.db` | E — Misconduct | JTC |
| `lane_F_appellate.db` | F — Appellate | COA 366810 |

### Connection Requirements

All database connections MUST use these PRAGMAs:

```python
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")
conn.execute("PRAGMA temp_store=MEMORY")
conn.execute("PRAGMA synchronous=NORMAL")
```

---

## Agent Fleet (28 OMEGA v2.0 Agents)

All agents consolidated from 155+ legacy agents into 28 active OMEGA v2.0 agents.

### Filing & Court Operations
| Agent | Purpose |
|-------|---------|
| filing-forge-master | Filing assembly, QA, Bates stamps, service tracking |
| omega-litigation-commander | Multi-step filing workflows, compliance proofs |
| court-form-finder | Michigan SCAO form identification |
| appellate-record-builder | COA/MSC record and appendix assembly |
| contempt-prosecutor | Contempt motions, show cause orders |
| post-judgment-enforcer | Post-judgment enforcement motions |

### Legal Research & Analysis
| Agent | Purpose |
|-------|---------|
| timeline-forensics | Hearing transcripts, chronology construction |
| court-order-tracker | Court order compliance monitoring |
| damages-calculator | Damages, filing fees, costs calculation |
| case-strategy-architect | Litigation strategy and prioritization |

### Evidence & Investigation
| Agent | Purpose |
|-------|---------|
| evidence-warfare-commander | Evidence triage, gap analysis, impeachment |
| evidence-vehicle-scanner | PDF scanning, MEEK lane routing |
| evidence-authentication | Chain of custody, admissibility |
| parental-alienation-detector | Alienation pattern detection |

### Judicial Accountability
| Agent | Purpose |
|-------|---------|
| judicial-accountability-engine | JTC complaints, misconduct documentation |
| judicial-recusal-engine | MCR 2.003 disqualification motions |

### Family Law
| Agent | Purpose |
|-------|---------|
| family-law-guardian | Custody, parenting time, GAL issues |
| affidavit-chronology-builder | Master chronological narrative |
| motion-practice | General motion drafting |

### System & Fleet Management
| Agent | Purpose |
|-------|---------|
| omega-dedup | Content-based dedup (peek inside — no hash-only) |
| self-evolving-fleet-manager | Fleet monitoring and evolution |
| compliance-auditor | PII redaction, filing compliance |

---

## MCP Server v2

`litigation-context-mcp` — 45+ tools across 9 categories. All tools prefixed with `litigation_`.

| Category | Count | Key Tools |
|----------|-------|-----------|
| Core | 10 | `scan_drives`, `search`, `get_stats`, `upcoming_deadlines` |
| Filing | 8 | `filing_readiness`, `filing_validate`, `filing_assemble`, `efiling_prep` |
| Evidence | 7 | `evidence_chain`, `evidence_gaps`, `bates_assign`, `exhibit_index` |
| Deadline | 5 | `deadline_dashboard`, `deadline_urgency`, `deadline_add` |
| Analysis | 5 | `authority_index`, `citation_graph`, `judicial_bias_scan` |
| QA | 4 | `prefiling_qa`, `qa_sweep`, `signature_check` |
| Backup | 3 | `backup_create`, `backup_version`, `backup_report` |
| Calendar | 2 | `calendar_generate`, `calendar_sync` |
| System | 1 | `system_health` |

Install: `pip install -e 00_SYSTEM/mcp_server/`

---

## Six Case Lanes

Evidence and filings are routed to one of six litigation lanes via MEEK signal detection.

| Lane | Subject | MEEK | Case Numbers | Court |
|------|---------|------|-------------|-------|
| **A** | Watson Custody | MEEK2 | 2024-001507-DC, 2023-5907-PP | 14th Circuit, Family Division |
| **B** | Shady Oaks Housing | MEEK1 | 2025-002760-CZ | 14th Circuit, Civil Division |
| **C** | Convergence | — | Multi-lane | Cross-jurisdictional |
| **D** | PPO / Protection Orders | MEEK3 | 2024-001507-DC, 2023-5907-PP | 14th Circuit |
| **E** | Judicial Misconduct | MEEK4 | 2024-001507-DC | Judicial Tenure Commission |
| **F** | Appellate | MEEK5 | COA 366810 | Michigan Court of Appeals |

Detection priority: **E → D → F → C → A → B** (highest-severity lane wins).

A `LaneCrossContaminationError` is raised when evidence from the wrong lane is detected (non-fatal, skip-item).

---

## Build & Test Commands

```bash
# Product app tests
cd 11_CODE/litigationos
pip install -e ".[dev]"
python -m pytest tests/ -q

# Pipeline
cd 00_SYSTEM/pipeline
python run_omega_pipeline.py                          # Full run
python run_omega_pipeline.py --start-phase 4a --end-phase 7c
python run_omega_pipeline.py --dry-run --list-phases

# Agent fleet
cd 00_SYSTEM/pipeline
python -m agents.agent_orchestrator                   # Full fleet
python -m agents.agent_orchestrator --agent J01       # Single agent

# Inference engine
python 00_SYSTEM/local_model/inference_engine.py "query"
python 00_SYSTEM/local_model/train_model.py           # Retrain

# Startup hook (session bootstrap)
python 00_SYSTEM/local_model/copilot_startup_hook.py --file

# Validation
cd 00_SYSTEM/scripts && python syntax_check.py
python integration_test_phase123.py
```

---

## Data Flow (End-to-End)

```
Raw Files (C:\, D:\, F:\, G:\, H:\, I:\)
  → Phase 0: Safety Snapshot (SHA-256 manifest + backup)
  → Phases 1-3: Inventory → Dedup → Classify (MEEK lane assignment)
  → Phases 4a-4e: Extract (PDF/DOCX/structured/atomize/archive)
  → Phase 5: LEXOS Brain Feed (50 micro-brains, 8 categories)
  → Phase 6: Gap Analysis (EGCP scoring per legal action)
  → Phases 7a-7c: Graph Delta → Synthesis Merge → Knowledge Merge
  → Phase 8: Litigation Refresh
  → Phase 9: MCP Ingest
  → Phases 10-12: Judicial Analysis → Legal Action Discovery → Rule Audit
  → Phases 13-16: Refinement → Finalization → Validation → Desktop Offload
  → Court-ready filing packets
```

---

## Error Handling (7-Layer Protocol)

Every agent follows this mandatory error protocol:

1. **Try** — Execute operation
2. **Specific catch** — Targeted recovery for known error types
3. **Broad catch** — Log, skip item, continue processing
4. **Checkpoint** — Save progress every N items for crash-resume
5. **Deadman switch** — 120s no progress → self-diagnose
6. **Agent retry** — 3× exponential backoff
7. **Tier fallback** — Orchestrator flags failure, pipeline continues

---

## Key Design Decisions

- **Local-only**: All AI inference runs locally. No cloud APIs, no network calls. `LLMGuardian` enforces this.
- **Append-only evidence**: Originals are never modified. New versions only. SHA-256 provenance everywhere.
- **Content-based dedup**: Documents are compared by opening and reading content — never hash-only.
- **No hard deletions**: Files moved to `I:\` drive or Recycle Bin, never deleted.
- **WAL mode everywhere**: All SQLite connections use WAL for concurrent access.
- **EAGAIN prevention**: Pipe isolation architecture separates shell pipes (shared) from agent pipes (isolated).

---

*Last updated: Wave 9 autopilot session*
