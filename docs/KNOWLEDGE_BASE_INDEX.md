# LitigationOS — Knowledge Base Index

> **Master index of all documentation, references, and knowledge sources.**
> Last updated: 2026-02-28 | System: LitigationOS v0.2.0 (Event Horizon Δ∞)

---

## 📍 Quick Navigation

| Section | What You'll Find |
|---------|-----------------|
| [Getting Started](#getting-started) | First-time setup, orientation, quickstart |
| [Architecture & Design](#architecture--design) | System architecture, data flow, pipelines |
| [Operations](#operations) | Pipeline runs, agent fleet, MCP server, runbooks |
| [Legal Reference](#legal-reference) | Michigan law, court rules, glossary, case lanes |
| [API & Tool Reference](#api--tool-reference) | MCP tools, Control Plane API, CLI commands |
| [Contributing & Development](#contributing--development) | Code standards, testing, changelogs |
| [Agent & Copilot Instructions](#agent--copilot-instructions) | Agent configuration, shell management, EAGAIN prevention |

---

## Getting Started

| Document | Path | Description |
|----------|------|-------------|
| **README** | [`README.md`](../README.md) | Project overview, system architecture, key components |
| **Start Here** | [`00_START_HERE/README.md`](../00_START_HERE/README.md) | First-time orientation and step-by-step instructions |
| **Start Here (Alt)** | [`00_START_HERE/START_HERE.md`](../00_START_HERE/START_HERE.md) | Alternate getting-started guide |
| **Step-by-Step Instructions** | [`00_START_HERE/INSTRUCTIONS_STEP_BY_STEP.txt`](../00_START_HERE/INSTRUCTIONS_STEP_BY_STEP.txt) | Detailed walkthrough for initial setup |
| **System Sequencer** | [`00_START_HERE/SYSTEM_SEQUENCER_CYCLE0009.md`](../00_START_HERE/SYSTEM_SEQUENCER_CYCLE0009.md) | System bootstrap sequencing for Cycle 9 |
| **ReadMe (Legacy)** | [`00_ReadMe/README.txt`](../00_ReadMe/README.txt) | Legacy README text |
| **Quickstart Runbook** | [`docs/RUNBOOK_QUICKSTART.md`](RUNBOOK_QUICKSTART.md) | Quick setup: init config → harvest → merge → query |
| **Warchest Quickstart v9** | [`docs/WARCHEST_v9_QuickStart.md`](WARCHEST_v9_QuickStart.md) | Warchest bundle quickstart guide |

---

## Architecture & Design

### Core Architecture

| Document | Path | Description |
|----------|------|-------------|
| **Architecture Diagrams** | [`docs/Architecture.md`](Architecture.md) | Mermaid diagrams: data flow, pipeline, AI stack, case lanes |
| **Event Horizon Architecture** | [`docs/ARCHITECTURE_EVENT_HORIZON.md`](ARCHITECTURE_EVENT_HORIZON.md) | Event Horizon factory: closed-loop filing generation |
| **Delta Infinity Blueprint** | [`docs/DELTA_INFINITY_BLUEPRINT.md`](DELTA_INFINITY_BLUEPRINT.md) | Long-term architectural blueprint for Delta∞ convergence |
| **Folder Planes** | [`docs/FOLDER_PLANES_v2.md`](FOLDER_PLANES_v2.md) | Directory structure design and folder plane organization |
| **Path Stability** | [`docs/PATH_STABILITY.md`](PATH_STABILITY.md) | Canonical path conventions and stability guarantees |
| **Integration Spec** | [`docs/Integration_Spec.md`](Integration_Spec.md) | Integration specifications for subsystem connections |
| **HF Components** | [`docs/HF_COMPONENTS.md`](HF_COMPONENTS.md) | High-frequency component inventory |

### PASS Gates & Quality

| Document | Path | Description |
|----------|------|-------------|
| **PASS Gates** | [`docs/PASS_GATES.md`](PASS_GATES.md) | Coverage, OCR, requirements, stack, MiFILE/MCR, export gates |
| **HYPERPIN Architect** | [`docs/HYPERPIN_ARCHITECT_v2.md`](HYPERPIN_ARCHITECT_v2.md) | HYPERPIN filing architecture and command center design |
| **HYPERPIN Executor** | [`docs/HYPERPIN_EXECUTOR_v2.md`](HYPERPIN_EXECUTOR_v2.md) | HYPERPIN execution engine specification |

### Delta Changelogs (Architecture Evolution)

| Document | Path | Description |
|----------|------|-------------|
| **Delta 7** | [`docs/DELTA7_APPEND_PACK_README.md`](DELTA7_APPEND_PACK_README.md) | Event Horizon Delta 7 append superprompt |
| **Delta 10** | [`docs/DELTA10_APPEND_NOTES.md`](DELTA10_APPEND_NOTES.md) | Main UI integration append |
| **Delta 11** | [`docs/DELTA11_APPEND_NOTES.md`](DELTA11_APPEND_NOTES.md) | Order/evidence lineage append |
| **Delta 12** | [`docs/DELTA12_APPEND_NOTES.md`](DELTA12_APPEND_NOTES.md) | Transcript quote-lock append |
| **Delta 13** | [`docs/DELTA13_APPEND_NOTES.md`](DELTA13_APPEND_NOTES.md) | Service/docket append |
| **Delta 19** | [`docs/DELTA19_APPEND_NOTES.md`](DELTA19_APPEND_NOTES.md) | Latest delta append notes |
| **Changelog Delta 11** | [`docs/CHANGELOG_DELTA11.md`](CHANGELOG_DELTA11.md) | Detailed changelog for Delta 11 |
| **Changelog Delta 12** | [`docs/CHANGELOG_DELTA12.md`](CHANGELOG_DELTA12.md) | Detailed changelog for Delta 12 |
| **Changelog Delta 13** | [`docs/CHANGELOG_DELTA13.md`](CHANGELOG_DELTA13.md) | Detailed changelog for Delta 13 |

---

## Operations

### Runbooks & Procedures

| Document | Path | Description |
|----------|------|-------------|
| **Operations Runbook** | [`docs/RUNBOOK.md`](RUNBOOK.md) | ⭐ Consolidated operations runbook (daily ops, emergency, recovery) |
| **Ops Runbook (EH)** | [`docs/OPERATIONS_RUNBOOK.md`](OPERATIONS_RUNBOOK.md) | Event Horizon operations: first boot, routine cycle, disaster recovery |
| **Quickstart Runbook** | [`docs/RUNBOOK_QUICKSTART.md`](RUNBOOK_QUICKSTART.md) | Fast-track: init → harvest → merge → query |
| **AutoHarvest Runbook v2** | [`docs/UNIFIED_AutoHarvest_Runbook_v2.0.md`](UNIFIED_AutoHarvest_Runbook_v2.0.md) | Unified auto-harvest workflow documentation |
| **Upgrade Playbook v11** | [`docs/NEXT_UPGRADE_PLAYBOOK_v11.md`](NEXT_UPGRADE_PLAYBOOK_v11.md) | System upgrade planning and execution guide |

### Pipeline Operations

| Document | Path | Description |
|----------|------|-------------|
| **Pipeline Operations** | [`docs/PIPELINE_OPERATIONS.md`](PIPELINE_OPERATIONS.md) | 24-phase pipeline reference: phases, agents, CLI commands |
| **Pipeline Runner** | [`00_SYSTEM/pipeline/run_omega_pipeline.py`](../00_SYSTEM/pipeline/run_omega_pipeline.py) | Main pipeline entry point (see `--help` for args) |

### Agent Fleet

| Document | Path | Description |
|----------|------|-------------|
| **AGENTS.md** | [`AGENTS.md`](../AGENTS.md) | Agent-specific repository instructions, mission, workflow |
| **Agent HQ README** | [`docs/AGENT_HQ_README.md`](AGENT_HQ_README.md) | Agent headquarters: fleet overview, tier structure |
| **Agent Migration Notes** | [`docs/AGENT_MIGRATION_NOTES_v10.md`](AGENT_MIGRATION_NOTES_v10.md) | Agent migration guide for v10 fleet updates |
| **Job System** | [`docs/JOB_SYSTEM.md`](JOB_SYSTEM.md) | Background job queue architecture and management |

### MCP Server

| Document | Path | Description |
|----------|------|-------------|
| **MCP Setup** | [`docs/MCP_SETUP.md`](MCP_SETUP.md) | MCP server configuration for VS Code |
| **MCP Tool Reference** | [`docs/MCP_TOOL_REFERENCE.md`](MCP_TOOL_REFERENCE.md) | All 47 MCP tools: names, categories, descriptions |
| **MCP Security** | [`docs/MCP_SECURITY_HARDENING.md`](MCP_SECURITY_HARDENING.md) | MCP server security hardening guide |

---

## Legal Reference

### Michigan Law & Court Rules

| Document | Path | Description |
|----------|------|-------------|
| **MI Rules (Loadbearing)** | [`docs/MI_RULES_LOADBEARING.md`](MI_RULES_LOADBEARING.md) | Critical Michigan Court Rules used in filings |
| **Authority Acquisition** | [`docs/Authority_Acquisition_and_Coverage.md`](Authority_Acquisition_and_Coverage.md) | Legal authority sourcing and coverage tracking |
| **AUTHLOCK Packs** | [`docs/AUTHLOCK_expert_knowledge_pack_*.md`](.) | Expert knowledge packs for authority locking |
| **Open Access Law Books** | [`Open-Access-Law-Books-main/`](../Open-Access-Law-Books-main/) | Open-access legal reference collection |

### Glossary & Terminology

| Document | Path | Description |
|----------|------|-------------|
| **Glossary Index** | [`glossary/GLOSSARY_INDEX.md`](../glossary/GLOSSARY_INDEX.md) | Term frequency index with evidence atom links |
| **Glossary Blueprint** | [`glossary/GLOSSARY_BLUEPRINT.pdf`](../glossary/GLOSSARY_BLUEPRINT.pdf) | Visual glossary blueprint |
| **Glossary Blueprint Edge** | [`glossary/GLOSSARY_BLUEPRINT_EDGE.pdf`](../glossary/GLOSSARY_BLUEPRINT_EDGE.pdf) | Extended glossary with edge-case terms |

### Case Lane Documentation

| Lane | Subject | Key Case Numbers |
|------|---------|-----------------|
| **A** — Custody | Watson custody | 2024-001507-DC, 2023-5907-PP |
| **B** — Housing | Shady Oaks | 2025-002760-CZ |
| **C** — Convergence | Cross-lane | Multi-lane |
| **D** — PPO | Protection Orders | 2024-001507-DC, 2023-5907-PP |
| **E** — Misconduct | JTC / McNeill | 2024-001507-DC |
| **F** — Appellate | COA/MSC | COA 366810 |

Case-specific filing directories: `01_COA_366810/`, `02_TRIAL_14TH/`, `03_FEDERAL_1983/`, `04_JTC_MCNEILL/`

---

## API & Tool Reference

| Document | Path | Description |
|----------|------|-------------|
| **MCP Tool Reference** | [`docs/MCP_TOOL_REFERENCE.md`](MCP_TOOL_REFERENCE.md) | 47 MCP tools across 9 categories |
| **Control Plane API** | [`docs/CONTROL_PLANE_API.md`](CONTROL_PLANE_API.md) | REST API: /configure, /health, /forms, /coverage, /jobs |
| **Copilot Instructions** | [`copilot-instructions.md`](../copilot-instructions.md) | Full Copilot integration spec (v18.0 Convergence) |
| **MANBEARPIG Engine** | [`00_SYSTEM/local_model/inference_engine.py`](../00_SYSTEM/local_model/inference_engine.py) | 50 skills, 140+ JSON-RPC methods, CLI + pipe mode |
| **Desktop Ingest** | [`docs/DESKTOP_INGEST_SUMMARY.md`](DESKTOP_INGEST_SUMMARY.md) | Desktop ingestion workflow summary |
| **ChatGPT Export Ingest** | [`docs/ChatGPT_Export_Ingest.md`](ChatGPT_Export_Ingest.md) | ChatGPT conversation export ingestion |
| **Download Link Reliability** | [`docs/DOWNLOAD_LINK_RELIABILITY.md`](DOWNLOAD_LINK_RELIABILITY.md) | Link reliability and provenance notes |

---

## Contributing & Development

| Document | Path | Description |
|----------|------|-------------|
| **Contributing Guide** | [`CONTRIBUTING.md`](../CONTRIBUTING.md) | Fork → Clone → Branch → PR workflow, code standards |
| **Code of Conduct** | [`CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md) | Contributor Covenant Code of Conduct |
| **Changelog** | [`CHANGELOG.md`](../CHANGELOG.md) | Version history (v1.0.0 initial release) |
| **License** | [`LICENSE`](../LICENSE) | Project license |
| **Security Keys** | [`docs/SECURITY_KEYS.md`](SECURITY_KEYS.md) | API key management policy (never commit secrets) |
| **VS Code Profile** | [`docs/VSCODE_PROFILE.md`](VSCODE_PROFILE.md) | VS Code configuration and profile setup |
| **Product App Tests** | [`11_CODE/litigationos/tests/`](../11_CODE/litigationos/tests/) | 266 pytest tests for the product app |

---

## Agent & Copilot Instructions

### Instruction Files (`.github/instructions/`)

| Document | Path | Description |
|----------|------|-------------|
| **EAGAIN Prevention** | [`.github/instructions/eagain-prevention.instructions.md`](../.github/instructions/eagain-prevention.instructions.md) | Master EAGAIN/pipe overflow prevention protocol |
| **Shell Management** | [`.github/instructions/shell-management.instructions.md`](../.github/instructions/shell-management.instructions.md) | PowerShell session lifecycle rules |
| **Agent Activation** | [`.github/instructions/agent-activation.instructions.md`](../.github/instructions/agent-activation.instructions.md) | Agent activation matrix and routing rules |
| **SQLite Memory** | [`.github/instructions/sqlite-memory.instructions.md`](../.github/instructions/sqlite-memory.instructions.md) | SQLite performance patterns for 10 GB+ database |

### System Documentation (`00_SYSTEM/`)

| Document | Path | Description |
|----------|------|-------------|
| **Startup Hook** | [`00_SYSTEM/local_model/copilot_startup_hook.py`](../00_SYSTEM/local_model/copilot_startup_hook.py) | Generates STARTUP_REPORT.md on every session |
| **Session Recall** | [`00_SYSTEM/local_model/session_recall.py`](../00_SYSTEM/local_model/session_recall.py) | Cross-session memory recall |
| **Safe Shell Toolkit** | [`00_SYSTEM/tools/safe_shell.py`](../00_SYSTEM/tools/safe_shell.py) | Safe Python execution (check, run, env-check, shadow-audit) |
| **Agent Profile** | [`00_SYSTEM/tools/agent_profile.ps1`](../00_SYSTEM/tools/agent_profile.ps1) | PowerShell agent profile with safe wrappers (sspy, srun, spy) |

---

## ADR (Architecture Decision Records)

| Location | Description |
|----------|-------------|
| [`docs/adr/`](adr/) | Architecture Decision Records directory |

---

## Document Naming Conventions

- **`(1)`, `(2)` suffixes** — Duplicate/backup copies (content-based dedup pending)
- **`DELTA{N}_APPEND_NOTES`** — Incremental architecture change documentation
- **`HYPERPIN_CMDCTR_DELTA{N}_*`** — Command center integration notes per delta
- **`AUTHLOCK_*`** — Authority-locked knowledge packs (version-controlled legal knowledge)
- **`WEB_SOURCES_provenance_*`** — Web source provenance tracking

---

## Database Documentation

| Database | Path | Description |
|----------|------|-------------|
| **Central DB** | `litigation_context.db` | 694 tables, 10.22 GB — main pipeline output |
| **Master Index** | `agents/master_index.db` | Agent fleet data (files, queues, clusters, atoms) |
| **MEEK Index** | `MEEK_index.db` | MEEK signal detection index |
| **Drive Inventory** | `drive_inventory.db` | Multi-drive file inventory |
| **MCR Rules** | `mcr_rules.db` | Michigan Court Rules database |
| **Lane DBs** | `lane_{A-F}_*.db` | Per-lane isolated databases |

---

*This index is auto-maintained. When adding new documentation, add an entry to the appropriate section above.*
