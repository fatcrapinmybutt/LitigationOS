# ADR-001: FINAL ARCHITECTURE DECISION — Multi-Agent Review Integration

**Status:** APPROVED  
**Date:** 2025-06-24  
**Reviewers:** Skeptic, Guardian, Advocate  
**Integrator Decision:** APPROVED WITH MODIFICATIONS  
**Build Scope:** 4 approved, 2 deferred, 2 rejected

---

## EXECUTIVE SUMMARY

After synthesizing three independent reviews against the **actual codebase** (56+ agents across 7 tiers, Agent9999 base class, existing EventBridge message bus, QualityScore system, F01-F09 convergence pipeline), I approve 4 finalists with modifications, defer 2, and reject 2. A **critical prerequisite** (dashboard fix) must precede all finalist work — without it, we cannot measure whether anything we build actually works.

**Key integration finding:** The codebase already has 80% of the infrastructure these finalists propose. The winning approach is surgical extension, not greenfield construction.

---

## PART 1: CRITICAL PRE-REQUISITE — FIX THE DASHBOARD

### The Problem (Advocate was right)

Investigation confirms the Advocate's finding is **worse than reported**. Not 5/6 — **all 6 critical dashboard queries fail**:

| Query | Failure Mode |
|-------|-------------|
| `v_case_health` | VIEW DOES NOT EXIST |
| `v_filing_pipeline` | VIEW DOES NOT EXIST |
| `v_adversary_threats` | VIEW DOES NOT EXIST |
| `v_drive_summary` | VIEW DOES NOT EXIST |
| `irac_analysis` by filing | COLUMN MISMATCH (`filing_ids` TEXT vs expected `filing_id` FK) |
| `damages_calculation` | COLUMN MISMATCH (`conservative_amount` vs expected `amount_low`) |
| `pipeline_runs` | TABLE EXISTS BUT EMPTY SCHEMA (zero columns) |
| `filing_fees` | TABLE DOES NOT EXIST |

### Why This Blocks Everything

Without a working dashboard:
- **Clearance Protocol** can't read quality scores to gate filings
- **One-Shot Filing** can't display filing readiness to the user
- **Deadline Autopilot** can't surface urgency data
- We have **no baseline** to measure canary success for any finalist

### Pre-Req Fix: `PHASE-0-DASHBOARD-REPAIR`

**Scope:** ~150 lines SQL + ~50 lines Python fixes

```
PHASE-0a: Create 4 missing views in litigation_context.db
  - v_case_health (aggregate from evidence_quotes, impeachment_matrix, etc.)
  - v_filing_pipeline (join filing_readiness + action_scores + deadlines)
  - v_adversary_threats (aggregate from impeachment_matrix + judicial_bias_chronology)
  - v_drive_summary (aggregate from canonical_files)

PHASE-0b: Fix column references in dashboard.py
  - irac_analysis: filing_ids → parse as JSON list, strength_score not score
  - damages_calculation: conservative_amount/aggressive_amount not amount_low/high
  - authority_chain_summary: use correct column name

PHASE-0c: Create missing tables with correct schemas
  - filing_fees (filing_id TEXT, description TEXT, amount REAL, paid INTEGER DEFAULT 0)
  - pipeline_runs (id INTEGER PK, tier TEXT, status TEXT, agents_run INTEGER,
    agents_passed INTEGER, timestamp TEXT DEFAULT datetime('now'))

PHASE-0d: Populate pipeline_runs from agent_log history (backfill)
```

**Kill switch:** `LITIGOS_SKIP_VIEW_REPAIR=1`  
**Success criteria:** All 6 MCP dashboard endpoints return valid data  
**Estimated scope:** 4 files, ~200 lines  
**Timeline:** Must complete BEFORE any finalist work begins

---

## PART 2: APPROVED FINALISTS

### FINALIST #4: ONE-SHOT FILING (Priority 1)

**All three reviewers agree: build this first.**

| Reviewer | Verdict | Key Requirement |
|----------|---------|----------------|
| Skeptic | APPROVED | Transactional staging, pre-flight |
| Guardian | CLEARED (LOW risk) | DB writes through managed pattern |
| Advocate | ESSENTIAL (10/10) | Build FIRST, bake #5 into it |

**Decision:** APPROVED. Merge with Clearance Protocol (#5) per Advocate's recommendation.

#### Architecture Specification

**Module:** `00_SYSTEM/pipeline/agents/convergence/f10_oneshot_filer.py`  
**Class:** `OneShotFiler(Agent9999)` with `agent_id = "F10-ONESHOT"`

**Input contract:**
```python
{
    "filing_id": str,        # F1-F10 identifier
    "lane": str,             # A-F lane code
    "main_document": str,    # Path to markdown or PDF
    "exhibits": list[dict],  # [{label, title, path}]
    "serve_parties": list,   # Party service list
}
```

**Output contract:**
```python
{
    "package_path": str,      # Path to assembled court package
    "bates_range": str,       # e.g., "PIGORS-000001 to PIGORS-000047"
    "page_count": int,
    "preflight_result": dict, # Clearance Protocol output (see #5)
    "status": str,            # READY | BLOCKED | NEEDS_REVIEW
    "manifest": dict,         # Full filing manifest
}
```

**Dependencies:**
- PHASE-0 dashboard repair (reads filing_readiness, action_scores)
- Existing: F07 filing_packager.py (reuse assembly logic)
- Existing: F08 citation_shepherd.py (reuse citation validation)
- Existing: F06 convergence_certifier.py (reuse certification logic)

**Implementation approach:**
- Compose from existing F06/F07/F08 — don't duplicate
- `_get_work_items()`: Query `filing_readiness WHERE status = 'pending_review'`
- `_process_item()`: Sequential pipeline:
  1. Pre-flight clearance check (inline #5)
  2. Citation validation (delegate to F08 logic)
  3. Transactional staging (write to staging table, not production)
  4. Assembly (delegate to F07 logic)
  5. Certification (delegate to F06 logic)
  6. Atomic commit (move staging → production)

**Guardian conditions (mandatory):**
- All DB writes through `self._db_execute()` (Agent9999 managed pattern)
- Staging table: `oneshot_staging` (separate from production `filing_packages`)
- Atomic commit: single transaction for staging → production promotion
- Kill switch: `LITIGOS_DISABLE_ONESHOT=1`
- Canary: First 2 filings require `LITIGOS_ONESHOT_APPROVE=1` manual gate

**Success criteria:**
- End-to-end: markdown input → court-ready PDF package in single invocation
- Pre-flight catches 100% of issues that F05/F06 currently catch
- Zero data loss: failed assembly never corrupts production tables
- Latency: < 30 seconds for typical 20-page filing with 5 exhibits

**Estimated scope:** ~250 lines new code, ~50 lines modifications to orchestrator  
**Files touched:** 3 new, 2 modified  

---

### FINALIST #5: CLEARANCE PROTOCOL (Priority 1 — merged into #4)

**All three reviewers approve, but disagree on form:**

| Reviewer | Verdict | Key Requirement |
|----------|---------|----------------|
| Skeptic | REVISE → 3-line change using existing QualityScore | Use soft gates |
| Guardian | CLEARED (ZERO risk) | Simplest possible implementation |
| Advocate | ESSENTIAL (bake into #4) | Don't build separately |

**Decision:** APPROVED as embedded pre-flight inside One-Shot Filing. Skeptic is right — this is a 3-line integration, not a standalone module.

#### Architecture Specification

**Module:** Inline function in `f10_oneshot_filer.py`, NOT a separate agent  
**Function:** `_preflight_clearance(filing_id: str) -> dict`

**Implementation (the "3-line change" Skeptic identified):**
```python
def _preflight_clearance(self, filing_id: str) -> dict:
    """Soft gate using existing QualityScore infrastructure."""
    cert = self._db_execute(
        "SELECT readiness_score, evidence_count, citation_count "
        "FROM filing_readiness WHERE filing_id = ?", (filing_id,)
    ).fetchone()

    if not cert:
        return {"status": "BLOCKED", "reason": "No readiness data"}

    score = cert["readiness_score"]
    threshold = float(os.environ.get("LITIGOS_CLEARANCE_THRESHOLD", "0.65"))

    if score >= threshold:
        return {"status": "CLEARED", "score": score}
    else:
        return {"status": "NEEDS_REVIEW", "score": score,
                "reason": f"Score {score:.2f} < threshold {threshold:.2f}"}
```

**Soft gate behavior (Skeptic's requirement):**
- Score >= threshold → auto-proceed
- Score < threshold → flag NEEDS_REVIEW (don't hard-block)
- Threshold configurable via `LITIGOS_CLEARANCE_THRESHOLD` env var
- Override: `LITIGOS_CLEARANCE_OVERRIDE=1` bypasses all checks

**Estimated scope:** ~30 lines inside f10_oneshot_filer.py  

---

### FINALIST #6: DEADLINE AUTOPILOT (Priority 2)

| Reviewer | Verdict | Key Requirement |
|----------|---------|----------------|
| Skeptic | REVISE | Extend autopilot.py, dependency graph, event-triggered |
| Guardian | CONDITIONAL (MEDIUM risk) | Kill switch, no schema changes |
| Advocate | ESSENTIAL (8/10) | User needs "what should I file next?" |

**Decision:** APPROVED with Skeptic's modifications. Extend existing `autopilot.py`, don't create new system.

#### Architecture Specification

**Module:** `00_SYSTEM/pipeline/autopilot.py` (EXTEND existing 78-line file)  
**New function:** `deadline_driven_priority() -> list[dict]`

**Input contract:** Reads from existing tables:
- `deadlines` (13 rows, has `due_date`)
- `filing_readiness` (has `readiness_score`)
- `action_scores` (has `composite_score`)

**Output contract:**
```python
[
    {
        "filing_id": "F1",
        "deadline": "2026-03-10",
        "days_remaining": 7,
        "urgency": "CRITICAL",          # CRITICAL/HIGH/MEDIUM/LOW
        "readiness_score": 0.82,
        "recommendation": "FILE NOW",   # FILE NOW / PREPARE / DEFER / BLOCKED
        "blockers": [],
    },
    # ... sorted by urgency DESC, days_remaining ASC
]
```

**Implementation approach:**
- Extend `autopilot.py` with ~100 new lines
- Reuse F09's MCR-compliant deadline math (import, don't copy)
- Recommendation engine:
  - CRITICAL + readiness >= 0.65 → "FILE NOW"
  - CRITICAL + readiness < 0.65 → "PREPARE" (list gaps)
  - HIGH + readiness >= 0.65 → "PREPARE"
  - LOW or no deadline → "DEFER"
  - Missing preconditions → "BLOCKED"

**Dependency graph (Skeptic's requirement):**
```python
FILING_DEPENDENCIES = {
    "F1": [],                    # Emergency TRO — no deps
    "F3": [],                    # Disqualification — no deps
    "F4": ["F3"],                # Federal 1983 — after disqualification
    "F7": ["F1"],                # Custody modification — after TRO
    "F9": ["F3", "F7"],          # COA Brief — after trial filings
    "F10": ["F9"],               # COA Emergency — after brief
}
```

**Guardian conditions (mandatory):**
- Kill switch: `LITIGOS_DISABLE_DEADLINE_AUTOPILOT=1`
- Read-only queries against production tables (no schema changes)
- No automatic filing — only generates recommendations
- Canary: First run outputs report only, requires `LITIGOS_AUTOPILOT_EXECUTE=1` to feed into One-Shot

**Success criteria:**
- Correctly prioritizes all 10 filings by urgency x readiness
- Identifies dependency chains (F4 blocked until F3 complete)
- Matches F09 deadline calculations exactly (no divergence)

**Estimated scope:** ~120 lines added to autopilot.py, ~20 lines config  
**Files touched:** 1 modified, 0 new  

---

### FINALIST #2: PHOENIX BOOTSTRAP (Priority 3)

| Reviewer | Verdict | Key Requirement |
|----------|---------|----------------|
| Skeptic | REVISE | Kill-before-respawn, error classification, coordinate retry |
| Guardian | CONDITIONAL (HIGH risk) | Agent ceiling hard gate |
| Advocate | VALUABLE (4/10) | Not essential but useful |

**Decision:** APPROVED with heavy constraints. The codebase has checkpoint-resume but no auto-respawn. This fills a real gap.

#### Architecture Specification

**Module:** `00_SYSTEM/pipeline/phoenix_bootstrap.py` (NEW file)  
**Class:** `PhoenixBootstrap` (NOT an Agent9999 subclass — orchestrator extension)

**Input contract:**
```python
{
    "failed_results": list[AgentResult],  # From run_tier() failures
    "tier": str,                           # Which tier failed
    "max_respawn_attempts": int,           # Default: 2
}
```

**Output contract:**
```python
{
    "respawned": list[str],     # Agent IDs respawned
    "recovered": list[str],     # Agent IDs that succeeded on retry
    "abandoned": list[str],     # Agent IDs that failed all retries
    "error_classes": dict,      # {agent_id: "transient"|"persistent"|"fatal"}
}
```

**Error classification (Skeptic's requirement):**
```python
def classify_error(result: AgentResult) -> str:
    if "locked" in str(result.error) or "timeout" in str(result.error):
        return "transient"      # Safe to retry
    if "schema" in str(result.error) or "missing table" in str(result.error):
        return "persistent"     # Fix root cause first
    return "fatal"              # Don't retry
```

**Guardian conditions (mandatory — NON-NEGOTIABLE):**
- Agent ceiling: `LITIGOS_MAX_AGENT_INSTANCES=56`. Phoenix CANNOT exceed this.
- Kill switch: `LITIGOS_DISABLE_PHOENIX=1`
- Maximum 2 respawn attempts per agent per tier run (hardcoded)
- Only retry `transient` errors — never `persistent` or `fatal`
- All respawn events logged to `agent_log` with level `PHOENIX`
- Canary: convergence tier only (gate other tiers behind env var)

**Success criteria:**
- Recovers transient DB lock errors without human intervention
- Never spawns agents beyond ceiling
- Zero false-positive retries on persistent errors
- Reduces manual intervention for "database is locked" by >80%

**Estimated scope:** ~150 lines new, ~30 lines orchestrator integration  
**Files touched:** 1 new, 1 modified  

---

## PART 3: DEFERRED FINALISTS

### FINALIST #3: INTELLIGENCE CACHE — DEFERRED

| Reviewer | Verdict |
|----------|---------|
| Skeptic | REVISE (write-through, staleness watermark) |
| Guardian | CONDITIONAL (MEDIUM risk) |
| Advocate | PREMATURE (3/10) |

**Decision:** DEFER. Advocate wins this conflict.

**Rationale:** The codebase already has 4 cache layers (SQLite PRAGMA 32MB, extracted_text table, checkpoint files, in-memory agent caches). The 92,246-row evidence_quotes table queries in <100ms via FTS5. There is no measured performance problem to solve.

**Activation trigger:** Query latency >2s on critical path AND fleet exceeds 100 agents AND cross-lane queries become measured bottleneck.

---

### FINALIST #1: GHOST TRACER — DEFERRED

| Reviewer | Verdict |
|----------|---------|
| Skeptic | REVISE (dedicated DB, batch writes) |
| Guardian | CONDITIONAL (LOW risk) |
| Advocate | LOW VALUE (2/10) |

**Decision:** DEFER. Advocate wins again.

**Rationale:** Existing `agent_log` + `AgentStats` + `agent_xp` + `_quality_history` provides sufficient observability for 56 single-machine agents. Distributed tracing is premature.

**Activation trigger:** Phoenix Bootstrap deployed AND cross-tier failure debugging needed, OR fleet moves to multi-machine.

---

## PART 4: REJECTED FINALISTS

### FINALIST #7: SYNAPSE BUS — REJECTED

**Rationale:** The codebase already has a fully functional inter-agent message bus: `AgentMessage` class, `send_message()`/`receive_messages()`/`deliver_messages()` in Agent9999, `route_messages()` in orchestrator with stats tracking, broadcast support, and thread-safe inboxes. Building Synapse Bus would create a competing duplicate.

### FINALIST #8: VAPOR POOL — REJECTED

**Rationale:** Agent9999 already supports single-item processing, zero-config instantiation, and auto-cleanup. Its `__init__` takes <1ms. The "heavyweight" perception is not measured. A separate lightweight class would fork the inheritance hierarchy and lose all Agent9999 guarantees.

---

## PART 5: FINAL BUILD ORDER

```
PHASE 0: Dashboard Repair                    [~200 LOC, 2-3 hours]
  |- 0a: Create 4 missing SQL views
  |- 0b: Fix column references in dashboard.py
  |- 0c: Create missing tables (filing_fees, pipeline_runs)
  |- 0d: Backfill pipeline_runs from agent_log
  GATE: All 6 MCP dashboard endpoints return valid data

PHASE 1: One-Shot Filing + Clearance         [~280 LOC, 4-6 hours]
  |- 1a: Create f10_oneshot_filer.py with Agent9999 base
  |- 1b: Implement _preflight_clearance() inline
  |- 1c: Compose from F06/F07/F08 (don't duplicate)
  |- 1d: Transactional staging table + atomic commit
  |- 1e: Wire into orchestrator get_tier_agents("convergence")
  |- 1f: Canary: manual gate for first 2 filings
  GATE: Single command produces court-ready PDF package

PHASE 2: Deadline Autopilot                  [~140 LOC, 2-3 hours]
  |- 2a: Add deadline_driven_priority() to autopilot.py
  |- 2b: Implement filing dependency graph
  |- 2c: Recommendation engine
  |- 2d: CLI flag: --deadlines
  |- 2e: Output deadline_priority_report.json
  GATE: Correctly prioritizes all 10 filings

PHASE 3: Phoenix Bootstrap                   [~180 LOC, 3-4 hours]
  |- 3a: Create phoenix_bootstrap.py
  |- 3b: Error classification
  |- 3c: Kill-before-respawn with ceiling
  |- 3d: Replace orchestrator retry loop
  |- 3e: Canary: convergence tier only
  GATE: Recovers transient errors without human intervention
```

**Total:** ~800 LOC, 6 files touched, 2 new files, 12-16 hours

---

## PART 6: ENVIRONMENT VARIABLES REGISTRY

| Env Var | Default | Purpose |
|---------|---------|---------|
| `LITIGOS_SKIP_VIEW_REPAIR` | `0` | Skip PHASE-0 view creation |
| `LITIGOS_DISABLE_ONESHOT` | `0` | Disable One-Shot Filing agent |
| `LITIGOS_ONESHOT_APPROVE` | `0` | Manual gate for canary filings |
| `LITIGOS_CLEARANCE_THRESHOLD` | `0.65` | QualityScore threshold for auto-clear |
| `LITIGOS_CLEARANCE_OVERRIDE` | `0` | Bypass clearance check |
| `LITIGOS_DISABLE_DEADLINE_AUTOPILOT` | `0` | Disable deadline priority engine |
| `LITIGOS_AUTOPILOT_EXECUTE` | `0` | Allow autopilot to feed One-Shot |
| `LITIGOS_DISABLE_PHOENIX` | `0` | Disable Phoenix auto-respawn |
| `LITIGOS_MAX_AGENT_INSTANCES` | `56` | Hard ceiling on agent count |

---

## PART 7: RISK MATRIX

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Dashboard fix breaks existing queries | LOW | Views are additive (CREATE VIEW IF NOT EXISTS) |
| One-Shot corrupts production data | MEDIUM | Staging table + atomic commit |
| Clearance threshold too strict | LOW | Configurable env var, soft gate |
| Deadline gives wrong recommendation | MEDIUM | Read-only, report-only, explicit execute flag |
| Phoenix respawns too aggressively | HIGH | 2-attempt ceiling, transient-only, agent count gate |
| Phoenix masks persistent errors | HIGH | Error classification; persistent/fatal never retried |

---

## VERDICT: APPROVED

This architecture is approved for implementation in the specified build order.

The 4 approved finalists represent ~800 lines of surgical additions to an already-robust 56-agent pipeline. No greenfield systems. No competing infrastructure. Every addition composes with existing Agent9999, QualityScore, and message bus primitives.

The critical insight: **fix the dashboard first, then build the filing pipeline, then add intelligence on top.** This is the only order that satisfies all three reviewers:
- **Guardian** gets a measurable baseline before any new agent deploys
- **Advocate** gets the highest-value feature (#4) as the first deliverable
- **Skeptic** gets surgical extensions to existing systems, not new ones
