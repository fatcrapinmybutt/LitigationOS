---
name: litigation-convergence-orchestrator
description: >-
  Use when executing convergence cycles, scoring litigation quality, tracking gaps via DNEW/BLOCKERS categories, or detecting emergence patterns across case graphs.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: convergence, cycle, quality, emergence, gap
---

# litigation-convergence-orchestrator

## Metadata

```yaml
name: litigation-convergence-orchestrator
version: 2.0.0
category: discipline
tier: 2
description: >
  Use when executing convergence cycles, scoring litigation quality (0-100),
  tracking gaps via DNEW/BLOCKERS/NEXT_PATCH categories, or detecting emergence
  patterns across case graphs, authority chains, and strategy surfaces in
  Michigan litigation.
metadata:
  triggers:
    - convergence cycle
    - quality scoring
    - gap tracking
    - emergence detection
    - DNEW blocker
    - litigation self-test
    - self-audit
    - convergence status
    - cross-graph pattern
  lanes:
    - A: Watson/Custody (2024-001507-DC, 2023-5907-PP, Judge McNeill)
    - B: Shady Oaks/Housing (2025-002760-CZ, Judge Hoopes)
    - C: Convergence/County (Muskegon County, 14th Circuit)
  court: 14th Judicial Circuit, Muskegon County
  case: Pigors v Watson
  mcp_tools:
    - litigation_self_test()
    - litigation_self_audit()
    - litigation_convergence_status()
  dependencies:
    - litigation-brain-spec
    - litigation-pipeline-commander
    - litigation-authority-validator
```

---

## Purpose

Convergence is the process of iteratively improving litigation quality until
every filing, strategy, and evidence chain meets courtroom-ready standards.
This skill orchestrates the convergence cycle — a structured loop of test,
audit, score, detect emergence, patch gaps, and re-test. Without convergence
discipline, litigation work product drifts, gaps accumulate silently, and
filings go out with hidden defects.

---

## Convergence Cycle Protocol

```
CYCLE START
│
├─ PHASE 1: SELF-TEST
│   ├─ Call litigation_self_test()
│   ├─ Validate all skill outputs against contracts
│   ├─ Check cross-reference integrity
│   └─ Collect test_results[]
│
├─ PHASE 2: SELF-AUDIT
│   ├─ Call litigation_self_audit()
│   ├─ Verify compliance with writing-skills standard
│   ├─ Check anti-rationalization table coverage
│   ├─ Audit authority chain completeness
│   └─ Collect audit_results[]
│
├─ PHASE 3: QUALITY SCORING
│   ├─ Compute quality_score (0-100) from test + audit
│   ├─ Apply lane-specific weights
│   ├─ Compare to previous cycle score
│   └─ Determine trajectory (improving/stalling/regressing)
│
├─ PHASE 4: GAP CLASSIFICATION
│   ├─ DNEW: New gaps discovered this cycle
│   ├─ BLOCKERS: Gaps preventing forward progress
│   ├─ NEXT_PATCH: Gaps scheduled for next cycle
│   └─ Prioritize by: court deadline proximity × severity
│
├─ PHASE 5: EMERGENCE DETECTION
│   ├─ Scan cross-graph patterns (Lane A ↔ B ↔ C)
│   ├─ Detect authority chain completion events
│   ├─ Surface contradiction signals
│   ├─ Identify novel strategy opportunities
│   └─ Log emergence_events[]
│
├─ PHASE 6: PATCH EXECUTION
│   ├─ Resolve BLOCKERS first (mandatory)
│   ├─ Address DNEW items by priority
│   ├─ Queue NEXT_PATCH items
│   └─ Update gap_registry
│
├─ PHASE 7: RE-TEST
│   ├─ Call litigation_self_test() again
│   ├─ Verify patches resolved target gaps
│   ├─ Confirm no regression
│   └─ Update quality_score
│
└─ CYCLE END → Log cycle_report → Schedule next cycle
```

---

## Decision Tree

```
ENTRY: Convergence request received
│
├─ Q1: What is the current quality score?
│   ├─ Score ≥ 90 ──── → MAINTENANCE MODE (light audit, emergence scan only)
│   ├─ Score 70-89 ──── → STANDARD CYCLE (full protocol)
│   ├─ Score 50-69 ──── → INTENSIVE CYCLE (double-pass, extra emergence scan)
│   └─ Score < 50 ────── → EMERGENCY CYCLE (all-hands, blocker-first)
│
├─ Q2: Which lanes need convergence?
│   ├─ Single lane ──── → Lane-specific cycle
│   ├─ Two lanes ─────── → Parallel cycles + cross-lane emergence check
│   └─ All three ─────── → Full convergence with C-lane synthesis
│
├─ Q3: Are there court deadlines within 14 days?
│   ├─ YES ────────────── → DEADLINE MODE (blockers only, skip NEXT_PATCH)
│   └─ NO ─────────────── → STANDARD pacing
│
└─ Q4: Did previous cycle show regression?
    ├─ YES ────────────── → ROOT CAUSE ANALYSIS before new cycle
    └─ NO ─────────────── → Proceed normally
```

---

## Quality Scoring Formula

```
quality_score = (
    authority_completeness   × 0.25 +   # All citations valid and current
    evidence_coverage        × 0.20 +   # All claims supported by evidence
    filing_readiness         × 0.20 +   # Filings meet format/content standards
    strategy_coherence       × 0.15 +   # Strategy consistent across lanes
    cross_lane_integrity     × 0.10 +   # No contradictions between lanes
    emergence_capture        × 0.10     # Novel patterns identified and logged
) × 100
```

### Score Interpretation

| Range | Status | Action |
|-------|--------|--------|
| 95-100 | COURTROOM READY | File with confidence |
| 85-94 | NEAR READY | Minor polish cycle |
| 70-84 | IN PROGRESS | Standard convergence continues |
| 50-69 | SIGNIFICANT GAPS | Intensive remediation needed |
| 25-49 | MAJOR DEFICIENCY | Emergency triage required |
| 0-24 | CRITICAL | Stop all filing — rebuild required |

---

## Gap Tracking System

### DNEW (Discovered New)
Gaps found during the current convergence cycle that did not exist before.

```yaml
dnew_item:
  id: string           # e.g., "DNEW-2026-0042"
  lane: enum [A, B, C]
  category: enum [authority, evidence, filing, strategy]
  severity: enum [critical, high, medium, low]
  description: string
  discovered_in_phase: integer
  deadline_impact: boolean
  assigned_to: string   # skill name responsible for fix
```

### BLOCKERS
Gaps that prevent any forward progress on a lane or filing.

```yaml
blocker_item:
  id: string           # e.g., "BLOCK-2026-0012"
  lane: enum [A, B, C]
  blocking: list[string]  # what is blocked
  root_cause: string
  resolution_path: string
  escalation_needed: boolean
```

### NEXT_PATCH
Gaps acknowledged but deferred to the next convergence cycle.

```yaml
next_patch_item:
  id: string           # e.g., "NPATCH-2026-0088"
  lane: enum [A, B, C]
  reason_deferred: string
  target_cycle: integer
  risk_if_delayed: string
```

---

## Emergence Detection Engine

Emergence = patterns that only become visible when multiple data sources converge.

### Signal Types

| Signal | Description | Example |
|--------|-------------|---------|
| CROSS_GRAPH | Pattern spans Lane A + B or B + C | Same bad actor in custody AND housing |
| CHAIN_COMPLETE | Authority chain reaches full support | All 12 best-interest factors now cited |
| CONTRADICTION | Two lanes assert incompatible facts | Timeline conflict between filings |
| NOVEL_STRATEGY | New legal theory emerges from data | Housing violations as custody evidence |
| WITNESS_OVERLAP | Same witness relevant to multiple lanes | Neighbor testimony for both cases |

### Emergence Detection Protocol

```
FOR EACH convergence cycle:
  1. Build cross-lane entity graph
  2. Compare entity overlap between Lane A ↔ B ↔ C
  3. Run contradiction detector on shared entities
  4. Check authority chains for cross-lane applicability
  5. Score emergence novelty (0-10)
  6. IF novelty ≥ 7: FLAG for attorney review
  7. Log all emergence_events with evidence links
```

---

## MCP Tool Integration

### litigation_self_test()
```
Purpose: Run automated tests against all skill outputs
Returns: test_results[] with pass/fail per test
Frequency: Every convergence cycle, Phase 1 and Phase 7
```

### litigation_self_audit()
```
Purpose: Audit compliance with writing-skills standard
Returns: audit_results[] with compliance scores
Frequency: Every convergence cycle, Phase 2
```

### litigation_convergence_status()
```
Purpose: Report current convergence state across all lanes
Returns: convergence_status with scores, gaps, trajectory
Frequency: On-demand and at cycle boundaries
```

---

## Output Contract

```yaml
convergence_cycle_report:
  cycle_number: integer
  timestamp: ISO-8601
  duration_minutes: integer
  quality_score:
    overall: float        # 0-100
    lane_a: float
    lane_b: float
    lane_c: float
    previous: float
    trajectory: enum [improving, stable, regressing]
  gaps:
    dnew_count: integer
    blocker_count: integer
    next_patch_count: integer
    dnew_items: list[dnew_item]
    blocker_items: list[blocker_item]
    next_patch_items: list[next_patch_item]
  emergence:
    events_detected: integer
    high_novelty_count: integer
    emergence_events: list[emergence_event]
  phases_completed: list[integer]
  regression_detected: boolean
  next_cycle_recommended: ISO-8601
```

---

## Cycle Scheduling

```
IF quality_score < 50:     → Next cycle in 4 hours
IF quality_score 50-69:    → Next cycle in 12 hours
IF quality_score 70-84:    → Next cycle in 24 hours
IF quality_score 85-94:    → Next cycle in 48 hours
IF quality_score ≥ 95:     → Next cycle in 7 days (maintenance)

OVERRIDE: Court deadline within 7 days → cycle every 4 hours regardless
```

---

## Lane-Specific Convergence Weights

### Lane A: Watson/Custody
- Best interest factor coverage: CRITICAL weight
- PPO compliance tracking: HIGH weight
- Parenting time evidence: HIGH weight
- Judge McNeill pattern alignment: MEDIUM weight

### Lane B: Shady Oaks/Housing
- Housing code violation inventory: CRITICAL weight
- Damage calculation completeness: HIGH weight
- Contract clause analysis: HIGH weight
- Judge Hoopes pattern alignment: MEDIUM weight

### Lane C: Convergence/County
- Cross-lane contradiction absence: CRITICAL weight
- Shared entity consistency: HIGH weight
- Timeline alignment: HIGH weight
- 14th Circuit local rule compliance: MEDIUM weight

---

## Escalation Rules

```
IF blocker_count > 3:
  ESCALATE — too many blockers for automated resolution
  NOTIFY with blocker summary and recommended actions

IF regression_detected AND previous_score > 80:
  ESCALATE — significant quality loss
  ROOT CAUSE ANALYSIS required before next cycle

IF emergence_novelty ≥ 9:
  ESCALATE — major strategic discovery
  ATTORNEY REVIEW within 24 hours

IF cross_lane_contradiction detected:
  HALT affected filings
  RESOLVE contradiction before any filing proceeds
```

## Related Skills

- [litigation-pipeline-commander](skill://litigation-pipeline-commander) — Executes OMEGA 16-phase pipeline
- [litigation-skill-auditor](skill://litigation-skill-auditor) — Audits fleet compliance and health


---

## 🔬 Pass 1: Data Intelligence Layer
*Enhanced: 2026-03-12 | Source: mega_file_harvest (53,625 files)*

### Live Database Arsenal
| Table | Records | Intelligence Value |
|-------|--------:|-------------------|
| `mega_file_harvest` | 53,625 | Complete file index with citations and metadata |
| `evidence_quotes` | 308,704 | Extracted evidence passages with legal significance |
| `contradiction_map` | 10,672 | Detected contradictions across all documents |
| `impeachment_items` | 15,171 | Impeachment-ready witness inconsistencies |
| `judicial_violations` | 1,127 | Documented judicial conduct violations |
| `pages` | 472,482 | Raw page text from ingested documents |
| `master_citations` | 3,684,757 | Extracted citations across all sources |
| `claims` | 653 | Active claims matrix with status tracking |
| `vehicles` | 6 | Filing vehicles with readiness scores |
| `authority_chains` | 28 | Authority chains with completeness scoring |
| `filing_readiness` | 24 | Per-vehicle filing readiness assessment |

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| C | 279 | USDC filing pending | U.S. District Court, W.D. Michigan |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 2.107 | 1369 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'habitability OR housing OR landlord';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'protection AND order';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
```

## 🔗 Pass 2: Cross-Skill Integration Matrix
*Enhanced: 2026-03-12 | 71 skills in fleet*

### Direct Integration Points
| Skill | Relationship | Data Flow |
|-------|-------------|-----------|
| `litigation-analysis-engine` | Integration | Bidirectional data exchange |
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |
| `litigation-filing-architect` | Integration | Provides readiness scores → filing decisions |
| `litigation-red-team` | Integration | Receives outputs → adversarial stress testing |

### Cross-Lane Evidence Routing
| Source Lane | Target Lane | Connection Pattern |
|-----------|------------|-------------------|
| A (Custody (Pigors v Watson)) | F | Trial errors → appellate issues |
| A (Custody (Pigors v Watson)) | E | Biased rulings → JTC complaint evidence |
| B (Housing (Shady Oaks)) | A | Unsafe housing → best-interest factor (d) |
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
| A (Custody (Pigors v Watson)) | C | Due process violations → §1983 claims |
| E (Judicial Misconduct (JTC)) | F | Misconduct findings → appellate arguments |

### OMEGA Pipeline Phase Mapping
```
This skill operates across these pipeline phases:
  Ω-5 Claim Mapping → Ω-8 Authority Matching → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,B,C,D,E | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E | Verified |
| Contempt | 70/100 | A,B,C,D,E | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E | Verified |
| Default Judgment | 60/100 | A,B,C,D,E | Verified |
| TRO Application | 60/100 | A,B,C,D,E | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E | Verified |

### Adversarial Defense Matrix
| Attack Vector | Defense | Skill Response |
|-------------|---------|---------------|
| Opposing motion to strike evidence | Pre-authenticate under MRE 901-903 | Run litigation-evidence-authentication |
| Challenge to standing | Verify party status and injury-in-fact | Document concrete harm with citations |
| Laches/statute of limitations | Verify timeliness under MCL/MCR | Check deadline_sentinel calculations |
| Hearsay objection | Map to MRE 801-807 exceptions | Pre-classify all evidence by exception |
| Judicial discretion argument | Identify abuse-of-discretion factors | Score against published standards |
| Mootness challenge | Show continuing controversy or capable-of-repetition | Document ongoing harm pattern |

### Quality Gates (Pre-Output Checklist)
```
□ All citations verified against authority_chains table
□ No hallucinated case names or statute numbers
□ Cross-lane contamination check passed (MEEK signal verified)
□ EGCP score meets filing threshold for target vehicle
□ Pinpoint citations include page + paragraph references
□ Opposing argument anticipated and addressed
□ Party names verified: Andrew J. Pigors, Emily A. Watson, L.D.W.
□ Judge name verified: Hon. Jenny L. McNeill (NOT McNeil)
□ Case numbers verified with leading zeros: 2024-001507-DC
□ No fabricated evidence (CPS = 1 call, NOT 9 investigations)
```

### Case-Specific Intelligence

**Lane A: Custody (Pigors v Watson)**
- Case: 2024-001507-DC
- Court: 14th Circuit, Muskegon County
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 722.23, MCL 722.27, MCL 722.28
- Key Rules: MCR 3.206-3.215
- Critical Evidence: 329+ days separation, 44% ex parte rate, Factor (j) alienation

**Lane B: Housing (Shady Oaks)**
- Case: 2025-002760-CZ
- Court: 14th Circuit, Muskegon County
- Judge: TBD
- Key Statutes: MCL 554.139, MCL 125.534-540, MCL 600.2918
- Key Rules: MCR 2.116, MCR 2.603
- Critical Evidence: 6GB evidence, HOA complaints, LARA registrations, FOIA personnel

**Lane C: Federal Civil Rights (§1983)**
- Case: USDC filing pending
- Court: U.S. District Court, W.D. Michigan
- Judge: TBD
- Key Statutes: 42 USC § 1983, 42 USC § 1985, 42 USC § 1988
- Key Rules: FRCP 8, FRCP 12, FRCP 56
- Critical Evidence: Color of law violations, Monell policy, pattern evidence across lanes

**Lane D: PPO (Protection Orders)**
- Case: 2023-5907-PP
- Court: 14th Circuit
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 600.2950, MCL 750.411h
- Key Rules: MCR 3.705-3.708
- Critical Evidence: False PPO allegations pattern, zero CPS findings after 1 investigation

**Lane E: Judicial Misconduct (JTC)**
- Case: JTC Complaint - McNeill
- Court: Judicial Tenure Commission
- Judge: Target: Hon. Jenny L. McNeill
- Key Statutes: Const 1963 art 6 § 30, MCR 9.104-9.205
- Key Rules: MCR 2.003, Code of Judicial Conduct
- Critical Evidence: 1,127 violations, 44% ex parte rate, muting father 7x in hearing

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
