---
name: litigation-skill-auditor
description: >-
  Use when auditing the litigation skill fleet for compliance, validating cross-reference integrity, checking trigger coverage, or maintaining fleet health.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: audit, validate, compliance, fleet, skill health
---

# litigation-skill-auditor

## Metadata

```yaml
name: litigation-skill-auditor
version: 2.0.0
category: discipline
tier: 2
description: >
  Use when auditing the litigation skill fleet for writing-skills compliance,
  validating cross-reference integrity between skills, checking trigger
  coverage across the fleet, verifying anti-rationalization table effectiveness,
  or maintaining the master fleet manifest.
metadata:
  triggers:
    - skill audit
    - fleet compliance
    - writing-skills validation
    - trigger coverage
    - cross-reference integrity
    - anti-rationalization check
    - fleet manifest
    - skill health check
    - meta-audit
  lanes:
    - A: Watson/Custody (2024-001507-DC, 2023-5907-PP, Judge McNeill)
    - B: Shady Oaks/Housing (2025-002760-CZ, Judge Hoopes)
    - C: Convergence/County (Muskegon County, 14th Circuit)
  court: 14th Judicial Circuit, Muskegon County
  case: Pigors v Watson
  fleet_size: 25
  dependencies: []  # Meta-auditor has no skill dependencies — it audits them all
```

---

## Purpose

A fleet of 25 litigation skills is only as strong as its weakest member. Skill
rot — degraded compliance, stale cross-references, missing triggers, weak
anti-rationalization tables — accumulates silently and manifests as courtroom
failures. This meta-auditor skill enforces fleet-wide quality standards,
validates every skill against the writing-skills specification, and maintains
the authoritative fleet manifest.

---

## Decision Tree

```
ENTRY: Audit request received
│
├─ Q1: What type of audit?
│   ├─ FULL FLEET AUDIT ──────── → BRANCH A: Complete Fleet Scan
│   ├─ SINGLE SKILL AUDIT ────── → BRANCH B: Individual Skill Deep Dive
│   ├─ CROSS-REFERENCE AUDIT ── → BRANCH C: Dependency Integrity Check
│   ├─ TRIGGER COVERAGE AUDIT → → BRANCH D: Trigger Gap Analysis
│   └─ MANIFEST UPDATE ────────── → BRANCH E: Fleet Manifest Refresh
│
├─ BRANCH A: Complete Fleet Scan
│   ├─ Step 1: Enumerate all 25 skills from fleet manifest
│   ├─ Step 2: For each skill, run BRANCH B checks
│   ├─ Step 3: Aggregate compliance scores
│   ├─ Step 4: Identify fleet-wide patterns
│   ├─ Step 5: Generate fleet_audit_report
│   └─ OUTPUT: fleet_audit_report
│
├─ BRANCH B: Individual Skill Deep Dive
│   ├─ Step 1: Verify SKILL.md exists (ALL CAPS filename)
│   ├─ Step 2: Parse metadata block
│   │   ├─ name matches directory name (kebab-case)
│   │   ├─ description starts with "Use when..."
│   │   ├─ category is "discipline"
│   │   ├─ triggers has 3+ keywords
│   │   └─ version follows semver
│   ├─ Step 3: Verify SKILL.md < 500 lines
│   ├─ Step 4: Check for decision tree presence
│   ├─ Step 5: Check for output contract presence
│   ├─ Step 6: Verify gotchas.md exists with anti-rationalization table
│   ├─ Step 7: Validate anti-rationalization table has 5+ rows
│   ├─ Step 8: Check references/ directory has required files
│   ├─ Step 9: Verify all cross-references resolve to real skills
│   ├─ Step 10: Score compliance (0-100)
│   └─ OUTPUT: skill_audit_result
│
├─ BRANCH C: Dependency Integrity Check
│   ├─ Step 1: Build full dependency graph from all skills
│   ├─ Step 2: Check for circular dependencies
│   ├─ Step 3: Verify all referenced skills exist
│   ├─ Step 4: Check for orphaned skills (no dependents/dependencies)
│   ├─ Step 5: Validate integration point claims
│   └─ OUTPUT: dependency_integrity_report
│
├─ BRANCH D: Trigger Gap Analysis
│   ├─ Step 1: Collect all triggers from all skills
│   ├─ Step 2: Build trigger → skill mapping
│   ├─ Step 3: Identify uncovered litigation scenarios
│   ├─ Step 4: Detect trigger overlaps (multiple skills, same trigger)
│   ├─ Step 5: Score trigger coverage completeness
│   └─ OUTPUT: trigger_coverage_report
│
└─ BRANCH E: Fleet Manifest Refresh
    ├─ Step 1: Scan skill directory for all skills
    ├─ Step 2: Extract metadata from each SKILL.md
    ├─ Step 3: Build/update fleet manifest
    ├─ Step 4: Validate manifest against filesystem
    ├─ Step 5: Commit updated manifest
    └─ OUTPUT: updated_fleet_manifest
```

---

## Writing-Skills Compliance Checklist

| # | Check | Required | Severity |
|---|-------|----------|----------|
| 1 | SKILL.md filename is ALL CAPS | YES | CRITICAL |
| 2 | name field matches directory name | YES | CRITICAL |
| 3 | name is kebab-case | YES | CRITICAL |
| 4 | description starts with "Use when..." | YES | HIGH |
| 5 | category is "discipline" | YES | HIGH |
| 6 | triggers has 3+ keywords | YES | HIGH |
| 7 | SKILL.md is < 500 lines | YES | MEDIUM |
| 8 | Decision tree present | YES | HIGH |
| 9 | Output contract present | YES | HIGH |
| 10 | gotchas.md exists | YES | HIGH |
| 11 | Anti-rationalization table in gotchas.md | YES | CRITICAL |
| 12 | Anti-rationalization table has 5+ rows | YES | HIGH |
| 13 | references/ directory exists | YES | MEDIUM |
| 14 | references/ has 2+ files | YES | MEDIUM |
| 15 | Each reference file has 50+ lines | RECOMMENDED | LOW |
| 16 | Lane assignments present | YES | HIGH |
| 17 | Court/case metadata present | YES | HIGH |
| 18 | Dependencies listed | YES | MEDIUM |
| 19 | Version follows semver | YES | LOW |
| 20 | No broken cross-references | YES | CRITICAL |

---

## Compliance Scoring

```
compliance_score = (
    critical_checks_passed / critical_checks_total × 40 +
    high_checks_passed / high_checks_total × 35 +
    medium_checks_passed / medium_checks_total × 15 +
    low_checks_passed / low_checks_total × 10
)
```

| Score | Rating | Action |
|-------|--------|--------|
| 95-100 | EXEMPLARY | No action needed |
| 85-94 | COMPLIANT | Minor polish recommended |
| 70-84 | NEEDS WORK | Remediation within 48 hours |
| 50-69 | NON-COMPLIANT | Remediation within 24 hours |
| < 50 | FAILING | Immediate remediation required |

---

## Cross-Reference Integrity Rules

```
RULE 1: Every skill listed in "dependencies" MUST exist in the fleet
RULE 2: Every skill referenced in "Integration Points" MUST exist
RULE 3: Circular dependencies are FORBIDDEN
RULE 4: Orphan skills (no references in or out) require justification
RULE 5: A skill cannot depend on a skill of lower tier
RULE 6: All dependency skill names MUST match actual directory names
RULE 7: Integration claims must be bidirectional (A references B → B references A)
```

---

## Anti-Rationalization Audit Protocol

For each skill's gotchas.md anti-rationalization table:

```
1. Count rows — must be ≥ 5
2. Check excuse column — each must be a real excuse agents/attorneys use
3. Check reality column — each must be a factual, specific rebuttal
4. Check consequence column — each must state actual litigation harm
5. Verify no duplicate excuses
6. Verify excuses cover the skill's specific failure modes
7. Score table effectiveness (0-10)
```

### Table Effectiveness Criteria
- **Specificity**: Excuses must be concrete, not vague
- **Realism**: Excuses must be ones that actually get used
- **Severity**: Consequences must reflect actual litigation harm
- **Coverage**: Table must cover the skill's top failure modes
- **Actionability**: Reality column must give clear corrective action

---

## Fleet Manifest Schema

```yaml
fleet_manifest:
  version: string
  last_audit: ISO-8601
  total_skills: integer
  skills:
    - name: string
      tier: integer
      version: string
      category: string
      compliance_score: float
      last_audited: ISO-8601
      status: enum [active, degraded, non-compliant, retired]
      file_count: integer
      trigger_count: integer
      dependency_count: integer
      lanes: list[string]
  fleet_health:
    avg_compliance: float
    skills_compliant: integer
    skills_non_compliant: integer
    trigger_coverage: float
    cross_ref_integrity: boolean
    last_full_audit: ISO-8601
```

---

## Output Contract

```yaml
audit_report:
  audit_type: enum [full_fleet, single_skill, cross_ref, trigger, manifest]
  timestamp: ISO-8601
  auditor: "litigation-skill-auditor v2.0.0"
  results:
    skills_audited: integer
    avg_compliance_score: float
    critical_failures: integer
    high_failures: integer
    medium_failures: integer
    low_failures: integer
  per_skill:
    - name: string
      compliance_score: float
      checks_passed: integer
      checks_failed: integer
      failures: list[check_failure]
      recommendations: list[string]
  cross_references:
    total_references: integer
    broken_references: integer
    circular_dependencies: integer
    orphan_skills: integer
  trigger_coverage:
    total_triggers: integer
    unique_triggers: integer
    overlapping_triggers: integer
    coverage_gaps: list[string]
  action_items:
    - skill: string
      action: string
      severity: enum [critical, high, medium, low]
      deadline: string
```

---

## Audit Scheduling

```
FULL FLEET AUDIT:        Weekly (or after any skill modification)
SINGLE SKILL AUDIT:      After any edit to a skill's files
CROSS-REFERENCE AUDIT:   After any skill added or removed
TRIGGER COVERAGE AUDIT:  Monthly (or after fleet composition change)
MANIFEST UPDATE:         After every audit of any type
```

---

## Remediation Workflow

```
1. AUDIT detects failure(s)
2. CLASSIFY failures by severity
3. ASSIGN to skill owner (or self for meta-issues)
4. SET deadline based on severity
5. TRACK remediation progress
6. RE-AUDIT after remediation
7. VERIFY all failures resolved
8. UPDATE fleet manifest with new compliance scores
9. LOG audit cycle completion
```

## Related Skills

- [litigation-convergence-orchestrator](skill://litigation-convergence-orchestrator) — Orchestrates convergence quality cycles
- [litigation-pro-se-guardian](skill://litigation-pro-se-guardian) — Guides pro se court navigation


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
| Custody Modification | 65/100 | A,B,C,E | Verified |
| Emergency Custody | 55/100 | A,B,C,E | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,E | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,E | Verified |
| Contempt | 70/100 | A,B,C,E | Verified |
| Judicial Disqualification | 75/100 | A,B,C,E | Verified |
| Default Judgment | 60/100 | A,B,C,E | Verified |
| TRO Application | 60/100 | A,B,C,E | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,E | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,E | Verified |

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
