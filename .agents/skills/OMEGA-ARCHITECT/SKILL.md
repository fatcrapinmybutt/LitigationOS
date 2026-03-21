---
name: OMEGA-ARCHITECT
description: >-
  Use when making system design decisions, evolving architecture, creating or modifying agents,
  designing MCP tools, optimizing the 16-phase pipeline, managing database schema evolution,
  or coordinating cross-skill fusion across the OMEGA system. This is the strategic leadership
  skill for all non-litigation structural decisions in LitigationOS — the blueprint authority
  that shapes how every subsystem connects, communicates, and evolves.
category: discipline
version: "2.0.0"
triggers:
  - system design
  - architecture
  - agent design
  - MCP tools
  - fleet optimization
  - orchestration
  - agent improvement
  - system evolution
  - pipeline design
  - schema design
  - module boundaries
  - data flow
  - knowledge architecture
  - skill fusion
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: Pigors v Watson
dependencies:
  - OMEGA-LITIGATION-SUPREME
  - OMEGA-ENGINEER
  - OMEGA-SENTINEL
metadata:
  tier: META
  fused_skills: 51
  author: andrew-pigors + copilot-omega
  forge_date: 2026-03-21
---

# 🏛️ OMEGA-ARCHITECT — Strategic System Leadership

> **META TIER** — Coordinates OMEGA-AGENT-ARCHITECT, OMEGA-ORCHESTRATOR, and OMEGA-MCP
> **Domain:** System design, agent fleet evolution, pipeline architecture, knowledge modeling
> **Scope:** Every structural decision in LitigationOS flows through this skill
> **Principle:** Build systems that are local-first, deterministic, append-only, and self-healing

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        OMEGA-ARCHITECT v2.0                                 ║
║              51 Skills → 7 Strategic Areas → 1 Blueprint Authority          ║
║                                                                             ║
║  SA1  System Architecture ──────┐                                           ║
║  SA2  Agent Fleet Design ───────┤                                           ║
║  SA3  MCP Tool Design ──────────┤→ UNIFIED ARCHITECTURE VISION              ║
║  SA4  Pipeline Architecture ────┤        ↓                                  ║
║  SA5  Knowledge Architecture ───┤   IMPLEMENTATION                          ║
║  SA6  Evolution Strategy ───────┤        ↓                                  ║
║  SA7  Cross-Skill Fusion ───────┘   VALIDATION → FEEDBACK                   ║
║                                                                             ║
║  Subordinates: OMEGA-AGENT-ARCHITECT · OMEGA-ORCHESTRATOR · OMEGA-MCP       ║
║  Peers:        OMEGA-ENGINEER · OMEGA-SENTINEL                              ║
║  Reports to:   OMEGA-LITIGATION-SUPREME (litigation domain authority)        ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Strategic Leadership Mission

OMEGA-ARCHITECT is the **blueprint authority** for LitigationOS. Every structural decision —
from adding a new database table to redesigning agent communication patterns — passes through
this skill's decision framework. The architect does not write every line of code; instead, it
**designs the spaces in which code is written**, ensuring that 155+ agents, 790+ DB tables,
16 pipeline phases, and 45+ MCP tools evolve coherently rather than drifting into entropy.

The architect's ultimate deliverable is **structural clarity**: any developer, agent, or future
version of Copilot should be able to look at LitigationOS and understand *why* each piece exists,
*how* it connects to other pieces, and *where* new functionality belongs.

---

## When to Apply

Use OMEGA-ARCHITECT when:

- **Adding new agents** — Where does it fit in the tier structure? What's its contract?
- **Creating new DB tables** — Does the schema follow existing conventions? Indexes?
- **Modifying the pipeline** — Will phase dependencies remain acyclic? What breaks?
- **Designing MCP tools** — Does the tool schema follow existing patterns? Naming?
- **Refactoring modules** — Are module boundaries clean? Import direction correct?
- **Adding new skills** — Does it belong in an existing OMEGA or need a new one?
- **Cross-cutting changes** — Changes that touch 3+ subsystems need architectural review
- **Performance decisions** — Connection pooling, caching strategy, index design
- **Evolution proposals** — Self-evolving patterns, A/B testing agent configs, quality metrics

Do NOT use OMEGA-ARCHITECT when:
- Writing litigation filings → use OMEGA-LITIGATION-SUPREME
- Fixing a specific bug → use OMEGA-ENGINEER
- Checking system health → use OMEGA-SENTINEL
- Pure code review → use OMEGA-ENGINEER

---

## Decision Tree

```
                         ┌─────────────────────┐
                         │  Architectural Need  │
                         │     Detected         │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌──────────┐   ┌──────────────┐  ┌───────────┐
            │ New Agent │   │ Schema/Data  │  │ Pipeline  │
            │ or Skill? │   │   Change?    │  │  Change?  │
            └─────┬────┘   └──────┬───────┘  └─────┬─────┘
                  │               │                 │
                  ▼               ▼                 ▼
          ┌──────────────┐ ┌────────────┐  ┌──────────────┐
          │ SA2: Fleet   │ │ SA5: Know- │  │ SA4: Pipeline│
          │   Design     │ │   ledge    │  │  Architecture│
          └──────┬───────┘ └─────┬──────┘  └──────┬───────┘
                 │               │                 │
                 ▼               ▼                 ▼
          ┌──────────────┐ ┌────────────┐  ┌──────────────┐
          │ Tier assign? │ │ Index plan?│  │ Phase deps   │
          │ Contract OK? │ │ FK design? │  │ still acyclic│
          │ Messaging?   │ │ Migration? │  │ after change?│
          └──────┬───────┘ └─────┬──────┘  └──────┬───────┘
                 │               │                 │
                 └───────────────┼─────────────────┘
                                 ▼
                    ┌────────────────────────┐
                    │  SA1: System-Wide      │
                    │  Impact Assessment     │
                    └───────────┬────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              ┌──────────┐ ┌────────┐ ┌─────────┐
              │ Approve  │ │Escalate│ │ Reject  │
              │ & Guide  │ │to Human│ │ & Offer │
              │ Impl.    │ │Review  │ │ Alt.    │
              └──────────┘ └────────┘ └─────────┘
```

---

## SA1: System Architecture — The Master Blueprint

### Core Architecture Principles (IMMUTABLE)

1. **Local-First** — Zero network dependencies, zero API keys, zero cloud services.
   Everything runs on Windows with SQLite + Python. MANBEARPIG inference engine
   is TF-IDF + Naive Bayes + BM25 — no LLM API calls.

2. **Append-Only Evidence** — Original files are NEVER modified or deleted.
   New versions, new rows, new entries — always additive. Move to `I:\` for dedup,
   never `rm` or `del`. This is a legal requirement for chain of custody.

3. **Deterministic Provenance** — SHA-256 hashes on every file, every pipeline
   output, every evidence artifact. Stable IDs (not random UUIDs). Every output
   traces back to its inputs through a verifiable chain.

4. **Six Lane Isolation** — Lanes A through F are firewalled. Evidence from Lane B
   (housing) NEVER contaminates Lane A (custody). `LaneCrossContaminationError`
   is a non-fatal skip — but it means the routing is wrong.

5. **EAGAIN Prevention** — Pipe-free-first architecture. MCP commands and task
   agents over PowerShell shells. Max 2 shared-pipe shells, max 4 isolated-pipe
   agents. See `eagain-prevention.instructions.md` for the full protocol.

### Module Boundary Rules

```
ALLOWED import direction:

  App Layer (11_CODE/litigationos/)
    ↓ imports from
  MCP Server (00_SYSTEM/mcp_server/)
    ↓ imports from
  Pipeline (00_SYSTEM/pipeline/)
    ↓ imports from
  Agents (00_SYSTEM/pipeline/agents/)
    ↓ imports from
  Core Libraries (00_SYSTEM/local_model/, tools/)

NEVER import upward. NEVER import across peer modules at the same layer.
```

### Data Flow Architecture

```
Raw Files (6 drives: C, D, F, G, H, I)
  │
  ▼ Phase 0: Safety Snapshot (SHA-256 manifest + full backup)
  ▼ Phase 1: Inventory (scan all drives, register in master_index.db)
  ▼ Phase 2: Dedup (content-based comparison — peek inside, not just hash)
  ▼ Phase 3: Classify (MEEK signal detection → lane assignment)
  │
  ▼ Phases 4a-4e: Extract (PDF, DOCX, structured, atomize, archive)
  ▼ Phase 5: LEXOS Brain Feed (50 micro-brains, 8 categories)
  ▼ Phase 6: Gap Analysis (EGCP scoring per legal action)
  │
  ▼ Phases 7a-7c: Graph Delta → Synthesis → Knowledge Merge
  ▼ Phase 8: Litigation Refresh
  ▼ Phase 9: MCP Ingest
  │
  ▼ Phases 10-12: Judicial Analysis → Legal Action Discovery → Rule Audit
  ▼ Phases 13-16: Refinement → Finalization → Validation → Desktop Offload
  │
  ▼ Court-ready filings (via Event Horizon Factory)
```

### When Reviewing Architectural Changes

Before approving ANY structural change, verify:

- [ ] Module boundary rules are not violated (no upward imports)
- [ ] Lane isolation is preserved (no cross-contamination paths)
- [ ] New DB tables follow naming conventions (`snake_case`, meaningful prefixes)
- [ ] New tables have appropriate indexes for expected query patterns
- [ ] Pipeline phase dependencies remain a DAG (no cycles)
- [ ] Agent contracts are honored (`run() → AgentResult`)
- [ ] EAGAIN budget is not exceeded by the change
- [ ] SHA-256 provenance chain is maintained for evidence paths

---

## SA2: Agent Fleet Design — 155+ Agent Orchestration

### Agent Contract (MANDATORY for all agents)

```python
class AgentNNNN(Agent9999):
    """Every agent inherits from Agent9999 in agents/agent_base.py."""

    def run(self) -> AgentResult:
        """
        Returns: AgentResult(agent_id, status, stats)
        Status values: SUCCESS | FATAL | CRASH
        """
        ...
```

### Tier Structure

| Tier | Agents | Role | Pipeline Phases |
|------|--------|------|-----------------|
| **1-3 (I/O)** | A01-A12 | Indexing, dedup, extraction | 1-4e |
| **J/K/L (Intelligence)** | J01-L08 | Judicial profiling, case intel, legal analysis | 10-12 |
| **F (Convergence)** | F01-F06 | Filing assembly, brain feed, graph build | 5-9, 13-16 |
| **Delta999** | 12 engines | Classifier, validator, brief, opposing, settlement | Cross-phase |
| **Copilot** | 64 agents | Specialized Copilot sub-agents | On-demand |
| **Superpower** | 13 agents | Cross-cutting orchestration, governance | Meta-level |
| **Convergence** | 10 agents | Phase 5-6 hardening, filing workflow | 5-6 focus |

### Agent Design Checklist (for new agents)

When creating a new agent, verify:

1. **Tier assignment** — Which tier does it belong to? I/O, Intelligence, or Convergence?
2. **Phase mapping** — Which pipeline phase(s) does it serve?
3. **Lane awareness** — Does it need MEEK signal detection? Which lanes?
4. **DB tables** — What tables does it read/write? Create on init if new.
5. **Error protocol** — All 7 layers implemented (try → catch → broad → checkpoint → deadman → retry → fallback)
6. **Inter-agent messaging** — Does it produce data for other agents? Through DB or direct?
7. **Idempotency** — Can it run twice on the same input without corruption?
8. **Resource budget** — DB connections via `managed_db()`, respect EAGAIN limits.

### Agent Communication Patterns

```
PATTERN 1: DB-mediated (preferred)
  Agent A writes to table_x → Agent B reads from table_x
  Pro: Decoupled, crash-resilient, auditable
  Con: Latency (milliseconds, acceptable)

PATTERN 2: Queue-mediated
  Agent A writes to ready_queue → Orchestrator assigns to Agent B
  Pro: Load balancing, priority control
  Con: Orchestrator is single point of coordination

PATTERN 3: Direct result passing (pipeline phases only)
  Phase N returns results → Phase N+1 receives as input
  Pro: Zero latency within a phase
  Con: Tight coupling — only for sequential phases
```

---

## SA3: MCP Tool Design — litigation-context MCP Server

### Tool Naming Convention

All tools are prefixed with `litigation_`. Categories:

| Category | Prefix | Examples |
|----------|--------|---------|
| Core | `litigation_` | `search`, `list_documents`, `get_stats` |
| Filing | `litigation_filing_` | `readiness`, `validate`, `assemble` |
| Evidence | `litigation_evidence_` | `chain`, `gaps`, `link`, `authenticate` |
| Deadline | `litigation_deadline_` | `dashboard`, `urgency`, `add` |
| Analysis | `litigation_` | `authority_index`, `citation_graph` |
| QA | `litigation_` | `prefiling_qa`, `qa_sweep` |
| Backup | `litigation_backup_` | `create`, `version`, `report` |
| System | `litigation_system_` | `health` |

### Tool Schema Design Rules

1. **Descriptive parameter names** — `vehicle_name` not `v`, `claim_id` not `cid`
2. **Optional parameters have defaults** — Never require parameters that can be inferred
3. **Return structured JSON** — Every tool returns `{"status": "ok"|"error", "data": ...}`
4. **Include counts** — When returning lists, always include `total_count`
5. **Pagination** — Tools returning >100 items MUST support `limit` and `offset`
6. **Error messages** — Human-readable, include the parameter that caused the error

### Adding New MCP Tools

```
Step 1: Define tool in 00_SYSTEM/mcp_server/tools/
Step 2: Register in tool registry with category prefix
Step 3: Add Pydantic model for input validation
Step 4: Write unit test (mock DB, verify output schema)
Step 5: Add to system_health tool count
Step 6: Update README tool table
```

---

## SA4: Pipeline Architecture — 16-Phase Design

### Phase Dependency Graph (MUST remain a DAG)

```
Phase 0 (Safety) → Phase 1 (Inventory) → Phase 2 (Dedup) → Phase 3 (Classify)
                                                                     │
                    ┌────────────────────────────────────────────────┘
                    ▼
            Phases 4a → 4b → 4c → 4d → 4e (Extract chain)
                                            │
                    ┌───────────────────────┘
                    ▼
            Phase 5 (Brain Feed) → Phase 6 (Gap Analysis)
                    │                       │
                    ▼                       ▼
            Phase 7a (Graph) → 7b (Synth) → 7c (Knowledge)
                                             │
                    ┌───────────────────────┘
                    ▼
            Phase 8 (Refresh) → Phase 9 (MCP Ingest)
                    │
                    ▼
            Phase 10 (Judicial) → Phase 11 (Actions) → Phase 12 (Rules)
                                                         │
                    ┌───────────────────────────────────┘
                    ▼
            Phase 13 (Refine) → Phase 14 (Finalize) → Phase 15 (Validate) → Phase 16 (Offload)
```

### Pipeline Modification Rules

- **Never create circular dependencies** between phases
- **Never skip Phase 0** (safety snapshot) — it's the recovery point
- **Phase idempotency** — Every phase can be re-run without corruption
- **Checkpoint between phases** — If Phase N crashes, Phase N-1 output is intact
- **Dry-run support** — Every phase must support `--dry-run` flag

---

## SA5: Knowledge Architecture — 790+ Table Database

### Schema Design Conventions

```sql
-- Table naming: snake_case, descriptive, prefixed by domain
CREATE TABLE IF NOT EXISTS evidence_quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_name TEXT NOT NULL,          -- lane identifier
    claim_id TEXT,                        -- FK to claims table
    quote_text TEXT NOT NULL,
    source_file TEXT,
    page_number INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(vehicle_name, quote_text, source_file)
);

-- Always create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_evidence_quotes_vehicle
    ON evidence_quotes(vehicle_name);
CREATE INDEX IF NOT EXISTS idx_evidence_quotes_vehicle_claim
    ON evidence_quotes(vehicle_name, claim_id);
```

### Schema Evolution Rules

1. **Never DROP columns** in production tables — add new columns, deprecate old ones
2. **Always use IF NOT EXISTS** for CREATE TABLE and CREATE INDEX
3. **Always verify schema** with `PRAGMA table_info()` before querying
4. **Composite indexes** — Match the WHERE clause column order
5. **FTS5 for text search** — Never use `LIKE '%term%'` on large tables
6. **WAL mode mandatory** — `PRAGMA journal_mode=WAL` on every connection

---

## SA6: Evolution Strategy — Self-Improving Architecture

### Quality Scoring Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pipeline completion rate | >95% | Phases completed / phases attempted |
| Agent success rate | >90% | SUCCESS / (SUCCESS + FATAL + CRASH) |
| Filing QA pass rate | >85% | Pre-filing QA passes / total filings |
| DB query performance | <100ms p95 | Query timing logs |
| Dedup accuracy | >98% | Content-verified matches / flagged matches |
| Lane accuracy | >99% | Correct lane / total classified |

### A/B Testing Agent Configurations

When testing agent improvements:
1. Run both old and new agent on same input set
2. Compare `AgentResult.stats` for accuracy and performance
3. Verify new agent doesn't regress on edge cases
4. Only promote if ALL metrics improve or hold steady

---

## SA7: Cross-Skill Fusion — Managing the OMEGA Ecosystem

### Current OMEGA Skill Map

| OMEGA Skill | Skills Fused | Domain |
|-------------|-------------|--------|
| OMEGA-LITIGATION-SUPREME | 67 | All litigation (supreme tier) |
| OMEGA-AGENT-ARCHITECT | 21 | Agent design, multi-agent patterns |
| OMEGA-ORCHESTRATOR | 17 | Workflow execution, task decomposition |
| OMEGA-MEMORY | 13 | Memory systems, cross-session recall |
| OMEGA-CODE | 41 | Python, clean code, TDD, debugging |
| OMEGA-DATA | 13 | SQLite, queries, schema management |
| OMEGA-MCP | 13 | MCP servers, tool design, FastMCP |
| OMEGA-SECURITY | 29 | Security audit, OWASP, PII protection |
| OMEGA-DEVOPS | 23 | Git, CI/CD, backup, system health |
| OMEGA-WRITING | 17 | Documentation, README, reports |
| OMEGA-EVIDENCE | 10 | Evidence processing, exhibits |
| OMEGA-RESEARCH | 12 | Legal research, RAG, citations |

### Fusion Decision Criteria

Create a new OMEGA skill when:
- 5+ related individual skills exist without an OMEGA umbrella
- Cross-skill interactions are frequent (>3 per session average)
- A domain expert would naturally group these capabilities together
- The fusion reduces cognitive load for skill selection

Do NOT fuse when:
- Skills serve completely different domains
- Fusion would create a >100-skill mega-skill (too broad)
- Individual skills need independent versioning

---

## IQ Boost Patterns (MANDATORY for all architectural work)

### 1. Chain-of-Thought

Before any architectural decision:
```
THINK: What is the current state?
THINK: What change is proposed?
THINK: What are the dependencies?
THINK: What could break?
THINK: What's the migration path?
DECIDE: Approve / Modify / Reject
```

### 2. Self-Reflection

After proposing any architecture change:
```
CHECK: Does this violate any of the 5 core principles?
CHECK: Does this increase or decrease system complexity?
CHECK: Can a new developer understand this without context?
CHECK: Does this create new single points of failure?
CHECK: Is this change reversible if it fails?
```

### 3. Anti-Hallucination

Every architectural claim must be grounded:
```
VERIFY: Run PRAGMA table_info() before assuming schema
VERIFY: Check file existence before referencing modules
VERIFY: Query DB for counts instead of citing from memory
VERIFY: Confirm agent exists in fleet before referencing
```

### 4. Cross-Skill Fusion

When a task crosses architectural boundaries:
```
DETECT: Does this touch agent design? → Invoke OMEGA-AGENT-ARCHITECT
DETECT: Does this touch pipeline phases? → Invoke OMEGA-ORCHESTRATOR
DETECT: Does this touch MCP tools? → Invoke OMEGA-MCP
DETECT: Does this touch code quality? → Delegate to OMEGA-ENGINEER
DETECT: Does this touch monitoring? → Delegate to OMEGA-SENTINEL
```

### 5. Adaptive Depth

Scale architectural guidance to task complexity:
```
SIMPLE (add a column): Brief guidance, reference conventions, done.
MEDIUM (new agent): Full checklist, tier assignment, contract review.
COMPLEX (new pipeline phase): Full impact assessment, dependency analysis,
  migration plan, rollback strategy, multi-agent coordination.
```

---

## Subordinate Skills Coordinated

### Direct Reports (OMEGA-ARCHITECT coordinates these)

| Skill | Source Skills | When Invoked |
|-------|-------------|--------------|
| **OMEGA-AGENT-ARCHITECT** | ai-agent-architect-omega, agent-orchestration-*, agent-tool-builder, agent-evaluation, multi-agent-*, autonomous-agent-patterns | Agent creation, fleet changes, evaluation framework |
| **OMEGA-ORCHESTRATOR** | executing-plans, workflow-*, conductor-*, context-*, parallel-agents, dispatching-parallel-agents | Workflow design, task decomposition, checkpoint/resume |
| **OMEGA-MCP** | mcp-builder, *-mcp-server-generator, tool-design, local-agent-sdk | MCP tool creation, server evolution, tool schema design |

### Peer Coordination

| Peer Skill | Coordination Pattern |
|------------|---------------------|
| **OMEGA-ENGINEER** | Architect designs → Engineer implements. Engineer reports technical debt → Architect prioritizes. |
| **OMEGA-SENTINEL** | Architect designs health checks → Sentinel implements monitoring. Sentinel reports anomalies → Architect assesses structural causes. |
| **OMEGA-LITIGATION-SUPREME** | Supreme defines litigation requirements → Architect designs systems to meet them. Architect never overrides litigation domain decisions. |

---

## Architecture Review Checklist (use before approving any structural change)

```
□ Core principles preserved (local-first, append-only, deterministic, lane-isolated, EAGAIN-safe)
□ Module boundaries respected (no upward imports, no cross-peer imports)
□ Pipeline DAG maintained (no circular phase dependencies)
□ Agent contract honored (run() → AgentResult with SUCCESS/FATAL/CRASH)
□ DB conventions followed (snake_case, IF NOT EXISTS, indexes, WAL mode)
□ MCP tool naming consistent (litigation_ prefix, category grouping)
□ EAGAIN budget within limits (max 2 shells + 4 agents)
□ SHA-256 provenance chain unbroken for evidence paths
□ Migration path defined (how to get from current state to proposed state)
□ Rollback plan exists (what happens if the change fails)
□ Documentation updated (README, architecture docs, changelog)
□ Tests added or updated for new functionality
```
