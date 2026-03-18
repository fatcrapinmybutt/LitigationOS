---
name: litigation-case-strategy-architect
description: >-
  Use when developing case-wide litigation strategy, coordinating actions
  across multiple lanes (A-F), phase planning, resource allocation,
  priority sequencing, risk assessment, and game theory analysis for
  multi-defendant or multi-claim litigation scenarios.
metadata:
  category: strategy
  author: andrew-pigors
  version: "1.0.0"
  triggers: >-
    case strategy, litigation plan, multi-lane coordination, phase planning,
    resource allocation, priority sequencing, game theory, multi-defendant,
    cross-lane, strategic planning, case architecture, litigation roadmap,
    case timeline planning, settlement leverage
---

# litigation-case-strategy-architect

> **Tier:** 1 — Strategic Command
> **Category:** strategy
> **Version:** 1.0.0
> **Lane:** C (Convergence — Cross-Lane)

## Description

Case-wide litigation strategy planner and coordinator for the Pigors v.
Watson multi-lane litigation system. Architects comprehensive strategies
spanning all six case lanes, performs game-theory analysis for
multi-party scenarios, sequences filing priorities across courts, manages
resource allocation for a pro se litigant, and identifies leverage
points, dependencies, and critical-path actions.

**Case Context:**

| Field | Value |
|-------|-------|
| Plaintiff | Andrew James Pigors (Pro Se) |
| Defendant | Emily A. Watson |
| Child | L.D.W. per MCR 8.119(H) — MALE |
| Judge | Hon. Jenny L. McNeill — 14th Circuit Court |
| Lanes | A (Custody), B (Housing), C (Convergence), D (PPO), E (Misconduct), F (Appellate) |

## Triggers

- User needs a litigation roadmap or strategic plan
- User asks "what should I file next?" or "what's the priority?"
- User needs to coordinate actions across multiple case lanes
- User evaluating settlement vs. trial strategy
- User planning resource allocation (time, copies, filing fees)
- User needs game-theory analysis for opposing party moves
- User planning phase sequence for multi-court actions

## Six-Lane Architecture

### Lane Dependency Graph

```
Lane E (Misconduct) ──► Lane F (Appellate) ──► Lane A (Custody)
                                                    │
Lane D (PPO) ─────────────────────────────────► Lane A
                                                    │
Lane B (Housing) ◄──── Lane C (Convergence) ◄──────┘
```

### Lane Priorities (Default Ordering)

| Priority | Lane | Rationale |
|----------|------|-----------|
| 1 | E — Misconduct | Judicial disqualification unlocks all other lanes |
| 2 | D — PPO | Safety-first; affects custody calculus |
| 3 | F — Appellate | Preserves rights; time-sensitive deadlines |
| 4 | A — Custody | Primary objective; depends on E/D outcomes |
| 5 | B — Housing | Quality of life factor for best-interest analysis |
| 6 | C — Convergence | Cross-lane synthesis; always active |

## Michigan Rules — Strategic Framework

### Filing Priority Rules

- **MCR 2.119(C)(1)** — Motions must be filed ≥9 days before hearing
- **MCR 7.205(A)** — Application for leave to appeal within 21 days
- **MCR 7.305** — Application to Supreme Court within 42 days of COA decision
- **MCR 2.116(C)(10)** — Summary disposition as strategic option
- **MCR 3.211** — Friend of the court report timeline

### Strategic Timing Rules

- **MCR 2.401** — Pretrial conference scheduling
- **MCR 2.501** — Trial scheduling and readiness
- **MCR 3.210** — Domestic relations hearing procedures
- **MCL 722.27** — Custody modification threshold (proper cause / change in circumstances)
- **MCL 722.23** — Best-interest factors (12 factors a-l)

### Discovery as Strategy

- **MCR 2.309** — Interrogatories (28-day window as pressure tool)
- **MCR 2.313** — Motion to compel (sanctions leverage)
- **MCR 2.302(B)(4)** — Expert discovery coordination

## Strategy Patterns

### Pattern 1: Layered Filing Pressure

**Context:** Pro se litigant needs to maximize impact of limited resources.

**Strategy:**
1. Identify the single highest-leverage filing across all lanes
2. Draft and file it with complete supporting evidence
3. Use the filing to create obligations on opposing party
4. File discovery targeting the gaps the filing exposes
5. Prepare the next filing while awaiting responses

**Michigan basis:** MCR 2.119, MCR 2.309, MCR 2.313

```python
from legal_ai.case_strategy_architect import CaseStrategyArchitect

csa = CaseStrategyArchitect()
plan = csa.build_strategic_plan(
    active_lanes=["A", "D", "E"],
    current_phase="discovery",
    objectives=["custody modification", "judicial accountability"],
)
priorities = csa.sequence_filings(plan)
```

### Pattern 2: Cross-Lane Evidence Amplification

**Context:** Evidence in one lane strengthens claims in another.

**Strategy:**
1. Catalog all evidence across all lanes
2. Map evidence to claims in each lane
3. Identify cross-lane amplification opportunities
4. File in the lane where evidence is strongest first
5. Use the record from that lane to support filings in others

**Michigan basis:** MRE 401-403, MCL 722.23

### Pattern 3: Game Theory — Opposing Party Response Prediction

**Context:** Multi-defendant scenario or adversarial co-parent.

**Strategy:**
1. Model opposing party's likely responses to each filing option
2. Identify dominant strategies (actions good regardless of response)
3. Calculate payoff matrix for each filing combination
4. Choose the filing sequence that maximizes worst-case outcome
5. Prepare contingency plans for each opposing response

## Anti-Patterns

### Anti-Pattern 1: Scatter-Shot Filing

❌ Filing in all lanes simultaneously without strategic sequencing.
**Why it fails:** Overwhelms pro se resources, creates conflicting deadlines,
and allows opposing party to exploit inconsistencies across filings.
**Fix:** Use the priority ordering above. One lane at a time, with
cross-lane awareness.

### Anti-Pattern 2: Ignoring Lane Dependencies

❌ Filing for custody modification (Lane A) before addressing judicial bias
(Lane E).
**Why it fails:** If the judge is biased, even a perfect custody motion
gets an unfavorable ruling. The disqualification must come first.
**Fix:** Always check the dependency graph before filing.

### Anti-Pattern 3: Reactive Rather Than Proactive

❌ Only responding to opposing party filings without affirmative strategy.
**Why it fails:** Cedes initiative; opponent controls the narrative.
**Fix:** Maintain a proactive filing calendar. Every response should also
advance an affirmative claim.

### Anti-Pattern 4: Settlement Blindness

❌ Refusing to evaluate settlement at each phase.
**Why it fails:** Litigation is expensive (even pro se); settlement may
achieve objectives faster.
**Fix:** Run settlement analysis at each strategic checkpoint using the
litigation-settlement-analyzer skill.

## Resource Allocation Model

### Pro Se Time Budget

| Activity | Hours/Week | Priority |
|----------|-----------|----------|
| Legal research | 4 | High |
| Drafting filings | 6 | High |
| Evidence organization | 3 | Medium |
| Court appearances | 2 | Critical |
| Discovery compliance | 3 | Medium |
| Strategic planning | 2 | High |

### Filing Cost Tracking

| Item | Cost | MCR Reference |
|------|------|---------------|
| Motion filing | $20.00 | MCR 2.119 |
| Appeal filing (COA) | $375.00 | MCR 7.204 |
| Copies (per page) | $0.25 | Local rule |
| Service (certified mail) | $7.50 | MCR 2.107 |

## Integration Points

### Upstream Skills
- `litigation-evidence-harvester` — Evidence catalog for strategy input
- `litigation-timeline-forensics` — Event chronology for planning
- `litigation-judicial-analyst` — Judge behavior patterns

### Downstream Skills
- `litigation-filing-architect` — Executes the filing plan
- `litigation-brief-writer` — Drafts the prioritized filings
- `litigation-discovery-warfare` — Executes discovery strategy
- `litigation-settlement-analyzer` — Evaluates settlement options

### Lane-Specific Skills
- Lane A: `litigation-custody-specialist`
- Lane B: `litigation-complaint-drafter`
- Lane D: `litigation-ppo-specialist`
- Lane E: `litigation-judicial-recusal-engine`
- Lane F: `litigation-appellate-strategist`

## Checklist — Strategic Plan Development

- [ ] Inventory all active claims across all lanes
- [ ] Map evidence to claims (cross-lane matrix)
- [ ] Identify deadline constraints (MCR timelines)
- [ ] Assess judicial posture (Lane E analysis)
- [ ] Model opposing party responses (game theory)
- [ ] Sequence filings by priority and dependency
- [ ] Allocate resources (time, cost) per filing
- [ ] Set checkpoints for strategy reassessment
- [ ] Document strategic rationale for each decision
- [ ] Review settlement posture at each checkpoint


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
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |
| MCR 2.113 | 756 | 🆕 Verify & integrate |
| MCR 2.302 | 698 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'custody AND best AND interest';
SELECT * FROM evidence_quotes WHERE legal_significance LIKE '%722.23%';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'habitability OR housing OR landlord';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'protection AND order';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'appeal AND error AND preserved';
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
  Ω-12 Filing Readiness → Ω-13 Document Generation → Ω-14 Red Team
  Ω-15 Validation → Ω-16 Deployment
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Custody Modification | 65/100 | A,B,C,D,E,F | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E,F | Verified |
| Contempt | 70/100 | A,B,C,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E,F | Verified |
| Appeal Brief | 70/100 | A,B,C,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,B,C,D,E,F | Verified |
| Default Judgment | 60/100 | A,B,C,D,E,F | Verified |
| TRO Application | 60/100 | A,B,C,D,E,F | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E,F | Verified |

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

**Lane F: Appellate (COA/MSC)**
- Case: COA 366810
- Court: Michigan Court of Appeals / Supreme Court
- Judge: Panel TBD
- Key Statutes: MCL 722.28, MCL 600.308
- Key Rules: MCR 7.203-7.305
- Critical Evidence: Preserved errors, constitutional violations, due process denial

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
