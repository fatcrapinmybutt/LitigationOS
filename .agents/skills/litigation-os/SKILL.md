---
name: litigation-os
description: >-
  Use when processing evidence files, building court filings, running the OMEGA pipeline,
  managing case lanes (Watson/custody, Shady Oaks/housing, convergence/county), querying
  Michigan court rules (MCR/MCL/MRE), operating the litigation_context_mcp server (31 tools),
  orchestrating the 50+ agent swarm, feeding LEXOS brains, running convergence cycles,
  analyzing judicial misconduct, computing deadlines, red-teaming filings, or working with
  BRAIN_SPEC governance. Triggers: litigation, court filing, Michigan, MCR, MCL, MRE,
  evidence, exhibit, custody, parenting time, contempt, PPO, appellate, COA, MSC, JTC,
  VehicleMap, convergence, knowledge graph, OMEGA pipeline, BRAIN_SPEC, LEXOS, atom store,
  case lane, scans, dedup, classify, extract, gap analysis, impeachment, adversary, rollback,
  safety, Shady Oaks, housing, Muskegon, McNeill, Watson, Pigors, pro se, disqualification.
metadata:
  category: discipline
  author: andrew-pigors
  version: "3.1.0"
  changelog:
    v3.1.0: |
      - Cross-skill orchestration: 100+ skills activated this session
      - Cycle 6 integration: 10 new cycle6_* tables in litigation_context.db (166 rows)
      - Mega-mine complete: 16,154 docs in mined_documents table (246M chars, 30.9M words)
      - Harvest 006 ingested: 764 files in harvest_texts table (3.67M chars)
      - Drive inventory: 159,209 files indexed in drive_file_index across 6 drives (32.8 GB)
      - NSPD/evidence tables: nspd_police_reports(26), nspd_officers(9), noreply_ocr_results(7), evidence_timeline(19), subpoena_targets(5)
      - EAGAIN prevention protocol: 5-rule permanent fix memorized and operational
      - 12-wave autonomous execution plan active
  license: PROPRIETARY
  compatibility: copilot-cli
  triggers: litigation, court filing, Michigan, MCR, MCL, custody, PPO, contempt,
    appellate, COA, MSC, JTC, OMEGA pipeline, BRAIN_SPEC, LEXOS, case lane, evidence,
    VehicleMap, convergence, judicial misconduct, scans, atom store, pro se, Muskegon
---

# LitigationOS

Judicial-grade Michigan litigation analysis + evidence distillation + document generation system.
31 MCP tools. 50+ agent swarm. 16-phase OMEGA pipeline. 3 case lanes. 56 legal actions.

## Iron Laws

**1. NEVER mix case lanes.**
Watson/custody evidence stays in Lane A. Shady Oaks/housing stays in Lane B.
They converge ONLY in Lane C (county/judges). Violating the letter IS violating the spirit.

**2. NEVER modify master files without a Phase 0 snapshot.**
`safety.py` runs first. Always. No snapshot = no pipeline. No exceptions.

**3. NEVER write to `scans/`.**
Read-only source. All outputs go to `cyclepacks/` or `LITIGATIONOS_MASTER/`.

**4. Every atom carries evidence posture.**
RECORD_FACT / EVIDENCE_FACT / SWORN_FACT / ALLEGATION / INFERENCE. No untagged data.

Mixed a lane? Skipped a snapshot? Wrote to scans/? **Delete it. Start over.**

## Workflow Decision Tree

### What are you doing?

**Processing evidence?**
→ [OMEGA Pipeline](commands/orchestrate.md) — 16-phase recursive traversal
→ [Safety System](references/pipeline/safety.md) — Snapshot + rollback

**Building a court filing?**
→ [VehicleMap Library](references/michigan-authority/vehicle-library.md) — Relief → Vehicle → Authority
→ [MCR Reference](references/michigan-authority/mcr-reference.md) — Court rules lookup
→ Which case lane? → [Case Lanes](references/case-lanes/README.md)

**Querying the knowledge base?**
→ [MCP Tools](references/mcp-tools/README.md) — 31 tool catalog
→ `litigation_search` (PDF text) or `litigation_search_evolved` (all sources)
→ `litigation_query_graph` (36K+ nodes across 8 knowledge graphs)

**Running analysis?**
→ [Agent Swarm](references/agent-swarm/README.md) — 50+ specialized agents
→ [Convergence Engine](references/convergence/README.md) — Quality cycles + emergence
→ [BRAIN_SPEC](references/brain-spec/README.md) — Governance rules

**Identifying legal actions?**
→ [Lane A: Custody](references/case-lanes/lane-a-custody.md) — 35 actions vs Watson family
→ [Lane B: Housing](references/case-lanes/lane-b-housing.md) — 14 actions vs Shady Oaks
→ [Lane C: Convergence](references/case-lanes/lane-c-convergence.md) — 7 actions vs County

**Checking system health?**
→ `litigation_self_test()` → `litigation_self_audit()` → `litigation_convergence_status()`
→ [Quality Metrics](references/convergence/quality-metrics.md)

## Case Lane Summary

| Lane | Cases | Adversaries | MEEK | Actions |
|------|-------|-------------|------|---------|
| **A: Custody** | 2024-001507-DC, 2023-5907-PP | Watson family, McNeill, Rusco | 2, 3 | A1-A35 |
| **B: Housing** | 2025-002760-CZ | Shady Oaks, Homes of America, Alden | 1 | B1-B14 |
| **C: Convergence** | NEW consolidated | Muskegon County, 14th Circuit | 4, 5 | C1-C7 |

## MCP Tool Categories (31 total)

| Category | Tools | Reference |
|----------|-------|-----------|
| PDF Knowledge Base | 8 | [pdf-knowledge.md](references/mcp-tools/pdf-knowledge.md) |
| Knowledge Graph | 4 | [knowledge-graph.md](references/mcp-tools/knowledge-graph.md) |
| Self-Awareness | 3 | [MCP README](references/mcp-tools/README.md) |
| SUPERPIN | 2 | [MCP README](references/mcp-tools/README.md) |
| Evolution Pipeline | 5 | [evolution.md](references/mcp-tools/evolution.md) |
| Health | 1 | [MCP README](references/mcp-tools/README.md) |
| GOD-Level | 8 | [god-level.md](references/mcp-tools/god-level.md) |

## Output Contracts

All substantive outputs emit machine-grammar blocks:

- `[CS] CASE_STATE` (≤25 lines)
- `[VM] VehicleMap` (relief → vehicle → authority → elements → deadlines → service)
- `[EX] ExhibitMatrix` (fact → evidence atoms → quote refs → MRE hooks)
- `[TL] Timeline` (bi-temporal)
- `[AT] AuthorityTriples` (proposition | authority | pinpoint)
- `[CM] ContradictionMap` (statement vs record conflict grids)
- `[VR] Validation/RedTeam` (structural checks + failure reasons)
- `[SBNA] Single Best Next Action` (2-3 options max)

## Mode Switches

- `MODE:DRAFT` — Analysis + drafting; fail-soft; prioritize speed; label uncertainties
- `MODE:FILE_READY` — No uncertainty; every attachment + service + deadline + cite present
- `MODE:PCG` — Irreversible actions gate; PASS only if core proof + service + deadlines satisfied

## Technical Constraints

- MCP stdio: server NEVER writes to stdout (only stderr)
- PyMuPDF import: `import pymupdf` (not `import fitz`)
- FTS5: porter + unicode61 tokenizer; AND/OR/NOT, "phrases", prefix*
- Windows paths: `\\?\` prefix for depth >260 chars
- Database: journal_mode=WAL, busy_timeout=10000, foreign_keys=ON
- CircuitBreaker: 5 failures → OPEN → 60s cooldown → HALF_OPEN

## Resources

### Commands
- [file.md](commands/file.md) — Filing workflow: action → VehicleMap → draft → package → serve
- [analyze.md](commands/analyze.md) — Deep analysis: person, entity, event, topic, claim
- [converge.md](commands/converge.md) — Convergence cycles + emergence detection
- [red-team.md](commands/red-team.md) — Adversarial stress-testing with 25+ attack vectors
- [orchestrate.md](commands/orchestrate.md) — OMEGA pipeline execution protocol

### References (by topic)
- [case-lanes/](references/case-lanes/README.md) — 3 lanes, 56 legal actions, Iron Rules
- [brain-spec/](references/brain-spec/README.md) — BRAIN_SPEC governance, atoms, scoring
- [mcp-tools/](references/mcp-tools/README.md) — 31 MCP tool API reference
- [pipeline/](references/pipeline/README.md) — OMEGA 16-phase pipeline
- [michigan-authority/](references/michigan-authority/README.md) — Filing lanes, MCR, VehicleMaps
- [agent-swarm/](references/agent-swarm/README.md) — 50+ agent specifications
- [convergence/](references/convergence/README.md) — Convergence + emergence protocol
- [desktop/](references/desktop/README.md) — LitigationOS-Desktop integration
- [fleet/](references/fleet/README.md) — 25-agent fleet architecture + dispatch

### Fleet Skills (25 agents across 3 tiers)

**Tier I — Operational Warfare:**
litigation-filing-architect, litigation-red-team, litigation-judicial-analyst,
litigation-impeachment-engine, litigation-evidence-harvester, litigation-authority-validator,
litigation-convergence-orchestrator, litigation-pipeline-commander, litigation-appellate-strategist,
litigation-skill-auditor

**Tier II — Supreme Domination:**
★ litigation-supreme-court-architect (MSC state machine),
litigation-federal-civil-rights, litigation-discovery-warfare, litigation-sanctions-engine,
litigation-custody-specialist, litigation-ppo-specialist, litigation-harm-quantifier,
litigation-brief-writer, litigation-record-builder, litigation-pro-se-guardian

**Tier III — The Lawsuit Forge:**
★ litigation-lawsuit-forge (new lawsuit lifecycle),
litigation-cause-of-action-library, litigation-complaint-drafter,
litigation-claim-researcher, litigation-service-engine

See [Fleet Dispatch Matrix](references/fleet/dispatch-matrix.md) for routing rules.

### Scripts
- `scripts/convergence_cycle.py` — Run convergence cycle with quality scoring
- `scripts/health_check.py` — Quick health diagnostic
- `scripts/fleet_dispatch.py` — Fleet agent coordination
- `scripts/red_team.py` — Automated adversarial analysis

### Gotchas
- [gotchas.md](gotchas.md) — Common pitfalls + anti-rationalization + fleet coordination


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
  Ω-5 Claim Mapping → Ω-8 Authority Matching → Ω-12 Filing Readiness
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
