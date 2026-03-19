# LITIGATIONOS ORCHESTRATION & MCP INFRASTRUCTURE
## Complete Exploration Results — Generated 2026-03-15 12:27:15

---

## 📋 DELIVERABLES (3 Documents)

### 1. **ORCHESTRATION_AND_MCP_SUMMARY.md** (13 KB)
   - Complete infrastructure analysis (10 sections)
   - All 54 MCP tools detailed by category
   - Orchestration architecture (156+ agents, dual-lane execution)
   - 16-phase data pipeline with checkpoint recovery
   - System configuration (4 documents analyzed)
   - Copilot agent instructions (v18.0 CONVERGENCE)
   - Master system architecture (50 core systems, 8 tiers)
   - Infrastructure utilities and integration patterns
   - **READ THIS FIRST for comprehensive understanding**

### 2. **QUICK_REFERENCE_ORCHESTRATION.md** (7 KB)
   - Quick stats (54 tools, 155+ agents, 16 phases, 50 systems)
   - Key files with locations (5 MCP servers, 4 config files)
   - Orchestration flow diagram
   - 54 tools categorized and listed
   - Non-negotiable rules (EAGAIN, data mgmt, party identity, DB-first)
   - 6 case lanes with detection priority
   - Improvement opportunities
   - Startup protocol
   - **USE FOR QUICK LOOKUPS AND REFERENCE**

### 3. **INDEX_ORCHESTRATION_EXPLORATION.md** (THIS FILE)
   - Navigation guide to all findings
   - File locations and purposes
   - Quick access to key information
   - Summary of exploration methodology

---

## 🔍 EXPLORATION METHODOLOGY

1. **Globbed for MCP server files** across mcp_servers\ and 00_SYSTEM\mcp_server\
2. **Read server.py** (54 tools across FastMCP decorators)
3. **Analyzed tool bridges** (v3_bridge.py, v4_bridge.py with 9 + 7 tools)
4. **Examined orchestrator** (agent_orchestrator.py: 56 Delta9 agents, dual-lane)
5. **Reviewed configurations** (5 YAML/JSON files: lanes, priorities, recipes)
6. **Read Copilot instructions** (v18.0 CONVERGENCE: 250 KB, 18 sections)
7. **Reviewed architecture** (MASTER_SYSTEM_ARCHITECTURE.md: 50 systems, 8 tiers)
8. **Cataloged all findings** into structured summaries

---

## 📊 KEY FINDINGS AT A GLANCE

### MCP Infrastructure
| Metric | Value |
|--------|-------|
| Total Tools | **54** |
| Tool Categories | **11** |
| Framework | FastMCP (async, Pydantic, error handling) |
| Response Formats | JSON + Markdown |
| Primary Server | 00_SYSTEM/mcp_server/litigation_context_mcp/server.py |
| Secondary Server | mcp_servers/litigationos_mcp_server.py (7 tools) |

### Orchestration
| Metric | Value |
|--------|-------|
| Total Agents | **155+** |
| Delta9 (Core Pipeline) | 56 |
| Delta999 (Advanced) | 12 |
| Copilot Agents | 64 |
| Superpower Agents | 13 |
| Convergence Agents | 10 |
| Execution Model | Dual-lane parallel (I/O ∥ AI) |
| Error Protocol | 7-layer (try/catch/broad/checkpoint/deadman/retry/fallback) |
| Concurrency Limit | Max 3 agents (HARD LIMIT) |

### Pipeline
| Metric | Value |
|--------|-------|
| Total Phases | **16** |
| Checkpoint Recovery | YES (phases 0-16) |
| Output | Court-ready filings (SCAO/MC/FOC) |
| Master DB | master_index.db (WAL mode) |

### Case Management
| Metric | Value |
|--------|-------|
| Case Lanes | **6** (A, B, C, D, E, F) |
| Lane Separation | STRICT (no cross-contamination) |
| MEEK Signals | E→D→F→C→A→B (detection priority) |
| Per-Lane Databases | 6 separate SQLite files |

### System Architecture
| Metric | Value |
|--------|-------|
| Core Systems Documented | **50** |
| System Tiers | **8** (core, evidence, filing, strategy, infra, case-specific, automation, protocols) |
| Conversations Analyzed | 1,710 |
| ChatGPT Messages | 139,693 |
| Database Tables | 85+ |
| FTS5 Indexes | 7 |

---

## 📂 KEY FILES LOCATION REFERENCE

### MCP Servers
`
mcp_servers/
  └── litigationos_mcp_server.py                    (7 tools: lightweight)

00_SYSTEM/mcp_server/
  ├── litigation_context_mcp/
  │   ├── server.py                                  (54 tools: FastMCP main)
  │   ├── tools_v3.py                               (9 tools: dashboard/ops)
  │   ├── tools_v3_bridge.py                        (bridge registration)
  │   ├── tools_v4.py                               (7 tools: convergence/combat)
  │   ├── tools_v4_bridge.py                        (bridge registration)
  │   ├── db.py                                      (database layer, error handling)
  │   ├── pdf_extractor.py                          (PyMuPDF integration)
  │   └── __init__.py
  ├── tools_v3.py                                    (v3 tool implementations)
  ├── tools_v4.py                                    (v4 tool implementations)
  ├── tools_v3_bridge.py                            (alternative v3 bridge)
  ├── tools_v4_bridge.py                            (alternative v4 bridge)
  └── command_runner.py                             (5 exec tools)
`

### Orchestration
`
00_SYSTEM/pipeline/agents/
  ├── agent_orchestrator.py                         (56 Delta9 agents, dual-lane)
  ├── agent_models.py                               (AgentResult, schema)
  ├── agent_base.py                                 (Agent9999 base class)
  ├── checkpoints/                                  (phase recovery)
  └── convergence/                                  (convergence cycle outputs)
`

### Configuration
`
litigationos.config.jsonc                           (V11 HyperAccel: lanes, recipes)
configs/
  ├── LITIGATION_OS.master.yaml                     (profile, invariants, modules)
  ├── rules_sources.json
  ├── default_rules.yaml
  ├── gemini_settings_example.json
  └── ...
config/
  ├── agent_default.yaml                           (lanes, priority, vehicles)
  ├── litigationos.config.jsonc                    (alternate location)
  ├── paths.yaml
  ├── launch_config.json
  ├── scoring_weights.json
  └── ...
`

### Documentation
`
MASTER_SYSTEM_ARCHITECTURE.md                       (50 systems, 8 tiers, 315+ lines)
.github/
  └── copilot-instructions.md                      (v18.0 CONVERGENCE, 250+ KB)

# Generated by this exploration:
ORCHESTRATION_AND_MCP_SUMMARY.md                    (13 KB, comprehensive)
QUICK_REFERENCE_ORCHESTRATION.md                    (7 KB, quick lookup)
INDEX_ORCHESTRATION_EXPLORATION.md                  (this file)
`

### Utilities
`
00_SYSTEM/tools/
  ├── docmind-ai-llm/                              (100+ files)
  │   ├── src/agents/
  │   │   ├── agent_coordinator.py
  │   │   ├── supervisor_graph.py
  │   │   ├── tool_factory.py
  │   │   └── ...
  │   ├── src/agents/tools/
  │   │   ├── memory.py
  │   │   ├── planning.py
  │   │   ├── retrieval.py
  │   │   ├── synthesis.py
  │   │   └── ...
  │   ├── src/agents/registry/
  │   │   ├── tool_registry.py
  │   │   └── llamaindex_llm_client.py
  │   └── ...
  └── ... (other utilities)

00_SYSTEM/local_model/
  ├── copilot_startup_hook.py
  ├── session_recall.py
  ├── inference_engine.py (THE MANBEARPIG v9.0)
  └── context_manager.py

00_SYSTEM/legal_ai/
  ├── context_orchestrator.py
  ├── workflow_automation_engine.py
  └── tests/
`

---

## 🎯 HOW TO USE THESE DOCUMENTS

### For Quick Lookups
→ Use **QUICK_REFERENCE_ORCHESTRATION.md**
- Find tool names and categories
- Check case lane assignments
- Verify non-negotiable rules
- Copy startup protocol

### For Comprehensive Understanding
→ Read **ORCHESTRATION_AND_MCP_SUMMARY.md** (in order)
1. Section 1: MCP Server Files (understand tool ecosystem)
2. Section 2: Orchestration Architecture (dual-lane, agents, protocols)
3. Section 3: 16-Phase Pipeline (data flow, checkpoints)
4. Section 4: Configuration (lanes, recipes, invariants)
5. Section 5: Copilot Instructions (rules, party identity, DB-first)
6. Section 6: Master Architecture (50 systems, 8 tiers)
7. Section 7: Infrastructure (utilities, tools)
8. Section 8: Integration Patterns (MCP ↔ Pipeline ↔ Agents)
9. Section 9: Current State & Improvements (opportunity list)

### For Navigation
→ Use **INDEX_ORCHESTRATION_EXPLORATION.md** (this file)
- Locate files by purpose
- Find key metrics
- Understand exploration methodology

---

## 🔄 INTEGRATION OVERVIEW

`
Copilot Agent (instructions.md)
    ↓ (uses)
MCP Server (litigation_context_mcp, 54 tools)
    ↓ (reads/writes)
Central DB (litigation_context.db: 85+ tables)
    ↓ (triggers)
Pipeline Phases (16 phases via Delta9 orchestrator)
    ↓ (runs)
Agent Fleet (155+ agents: dual-lane + convergence)
    ↓ (produces)
Convergence Cycle (filing readiness + EGCP scoring)
    ↓ (outputs)
Court-ready Filings (SCAO/MC/FOC forms)
`

---

## 💡 IMPROVEMENT OPPORTUNITIES

1. **Tool Versioning** → Add explicit version/deprecation tracking to all 54 tools
2. **Runtime Dashboard** → Live orchestrator visibility (lane status, agent health, phase progress)
3. **Auto-Resume** → Smart checkpoint reading from PROGRESS_LOG.md
4. **Config Schema** → Single unified schema with inheritance (combine 5 YAML files)
5. **Tool Discovery** → Dynamic tool registry + manifest (auto-list all 54 tools)
6. **Metrics** → Collect phase timing, agent success rates, lane utilization
7. **Convergence Visibility** → Real-time EGCP scoring dashboard

---

## 📞 REFERENCE COMMANDS

### Generate Startup Report (Every Session)
\\\powershell
python C:\Users\andre\LitigationOS\00_SYSTEM\local_model\copilot_startup_hook.py --file
cat C:\Users\andre\LitigationOS\00_SYSTEM\STARTUP_REPORT.md
\\\

### Run Orchestrator (Manual)
\\\powershell
cd C:\Users\andre\LitigationOS
python -m agents.agent_orchestrator --help
python -m agents.agent_orchestrator [--dry-run] [--tier TIER] [--agent AGENT_ID]
\\\

### Check MCP Tools Available
\\\powershell
# All 54 tools available via:
python -c "from mcp_servers.litigationos_mcp_server import mcp; print([t for t in dir(mcp) if not t.startswith('_')])"

# Via FastMCP in server.py:
# All @mcp.tool() decorated functions are exposed
\\\

### Query Central Database
\\\powershell
sqlite3 C:\Users\andre\LitigationOS\litigation_context.db
  # Get table count:
  SELECT COUNT(*) FROM sqlite_master WHERE type='table';
  
  # Get master systems:
  SELECT * FROM master_systems WHERE tier = 'TIER_1_CORE';
  
  # Full-text search in master_systems:
  SELECT * FROM master_systems_fts WHERE master_systems_fts MATCH 'canon';
\\\

---

## 🔐 CRITICAL LIMITS (Never Exceed)

| Limit | Value | Violation |
|-------|-------|-----------|
| Concurrent Background Agents | 3 | EAGAIN, SQLITE_BUSY |
| Async Shell Sessions | 3 | Resource pool exhaustion |
| DB Connection Timeout | 60,000 ms | Queries fail |
| File Dedup | CONTENT-BASED | Incomplete dedup |
| Hard Deletions | ZERO | Data loss |
| Placeholder Insertion | DB-FIRST | Hallucinated stats |
| System Shellids per Session | 50 max | Session instability |

---

## ✅ CHECKLIST FOR IMPROVEMENTS

- [ ] Review all 54 tools for versioning candidates
- [ ] Design runtime orchestration dashboard (sketch UI)
- [ ] Create tool registry JSON (all 54 tools + metadata)
- [ ] Consolidate 5 config files into single schema
- [ ] Implement auto-resume from PROGRESS_LOG.md
- [ ] Add phase timing metrics (SQLite tracking)
- [ ] Build EGCP scoring real-time dashboard
- [ ] Create tool deprecation policy
- [ ] Document tool API versioning strategy
- [ ] Test improvement on non-critical lane first

---

## 📌 QUICK STATS

**Numbers:**
- 54 MCP tools
- 155+ agents
- 16 pipeline phases
- 50 core systems
- 8 system tiers
- 6 case lanes
- 85+ database tables
- 1,710 conversations analyzed
- 139,693 ChatGPT messages
- 7 FTS5 indexes

**Limits:**
- Max 3 concurrent agents
- Max 3 concurrent shells
- 60,000 ms DB timeout
- 512 KB max file for MCP resources
- No remote network access (locked)

**Must-Know:**
- EAGAIN = max 3 agents running
- CONTENT-BASED DEDUP = peek inside files
- DB-FIRST = query before placeholders
- TRACEABLE STATS = every count has a SELECT query
- PARTY IDENTITY = never fabricate names/bar numbers

---

*Generated: 2026-03-15 12:27:15*
*Source: Comprehensive exploration of C:\Users\andre\LitigationOS*
*Exploration Scope: 10 parallel glob + grep searches + 10 file reads + 16 orchestration files analyzed*
