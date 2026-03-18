---
name: litigation-authority-validator
description: >-
  Use when verifying MCR/MCL/MRE citations, validating case authority chains, checking citation currency, or auditing brief authority sections for completeness.
metadata:
  category: discipline
  author: andrew-pigors
  version: "2.2.0"
  triggers: citation, authority, validate, MCR, MCL, chain
  changelog:
    v2.2.0: |
      - Cross-filing audit: 27 citations validated across 3 clerk-ready filings
      - Avg chain scores: Emergency PT 4.7, Disqualification 4.7, Contempt 3.8
      - Cycle 6 integration: 11,188 unique citations (8,394 MCR + 2,794 MCL)
      - 16,154 mined docs with citation extraction in mined_documents table
      - Known issue: Vodvarka needs pinpoint + NW2d parallel cite
      - Known issue: Caperton needs pinpoint citation
      - Contempt motion needs more case law (target chain score 4.5+)
---

# litigation-authority-validator

## Metadata

```yaml
name: litigation-authority-validator
version: 2.0.0
category: discipline
tier: 2
description: >
  Use when verifying MCR/MCL/MRE citations, validating case authority chains,
  checking citation currency, or auditing brief/motion authority sections for
  completeness and accuracy in Michigan litigation.
metadata:
  triggers:
    - citation verification
    - authority validation
    - MCR citation check
    - MCL verification
    - case law currency
    - authority chain audit
    - citation format
    - Shepardize
  lanes:
    - A: Watson/Custody (2024-001507-DC, 2023-5907-PP, Judge McNeill)
    - B: Shady Oaks/Housing (2025-002760-CZ, Judge Hoopes)
    - C: Convergence/County (Muskegon County, 14th Circuit)
  court: 14th Judicial Circuit, Muskegon County
  case: Pigors v Watson
  dependencies:
    - litigation-brain-spec
    - litigation-filing-packager
```

---

## Purpose

Authority validation is the single most career-ending failure mode in litigation.
A reversed citation, an overruled case cited as good law, or a missing pinpoint
cite can result in sanctions, malpractice claims, and case dismissal. This skill
enforces zero-tolerance authority hygiene across all three case lanes.

---

## Decision Tree

```
ENTRY: Authority validation request received
│
├─ Q1: What type of authority?
│   ├─ Statute (MCL) ────────────────── → BRANCH A: Statute Validation
│   ├─ Court Rule (MCR/MRE) ─────────── → BRANCH B: Rule Validation
│   ├─ Case Law ─────────────────────── → BRANCH C: Case Validation
│   └─ Secondary (treatise/law review) → BRANCH D: Secondary Validation
│
├─ BRANCH A: Statute Validation
│   ├─ Step 1: Parse MCL number format (MCL §XXX.XXXX)
│   ├─ Step 2: Verify section exists in current compiled laws
│   ├─ Step 3: Check for amendments post-filing date
│   ├─ Step 4: Verify subsection/paragraph pinpoint accuracy
│   ├─ Step 5: Check for companion sections cited together
│   └─ OUTPUT: statute_validation_result
│
├─ BRANCH B: Rule Validation
│   ├─ Step 1: Parse rule number (MCR X.XXX or MRE XXX)
│   ├─ Step 2: Verify rule exists and is current
│   ├─ Step 3: Check for administrative orders modifying rule
│   ├─ Step 4: Verify subrule pinpoint (e.g., MCR 2.116(C)(10))
│   ├─ Step 5: Cross-check with local court rules (14th Circuit)
│   └─ OUTPUT: rule_validation_result
│
├─ BRANCH C: Case Validation
│   ├─ Step 1: Parse citation format (Michigan or federal)
│   ├─ Step 2: Verify case exists at cited reporter/page
│   ├─ Step 3: Check subsequent history (reversed? overruled?)
│   ├─ Step 4: Verify pinpoint page accuracy
│   ├─ Step 5: Confirm proposition matches cited holding
│   ├─ Step 6: Check if binding or persuasive in 14th Circuit
│   └─ OUTPUT: case_validation_result
│
└─ BRANCH D: Secondary Validation
    ├─ Step 1: Verify publication exists
    ├─ Step 2: Check edition currency
    ├─ Step 3: Confirm page/section reference
    └─ OUTPUT: secondary_validation_result
```

---

## Authority Chain Completeness Protocol

Every legal proposition in a filing MUST have a complete authority chain:

```
PROPOSITION
  └─ Primary Authority (binding case or statute)
       └─ Supporting Authority (additional cases)
            └─ Pinpoint Citation (exact page/paragraph)
                 └─ Parenthetical (holding summary)
                      └─ Currency Verification (still good law)
```

### Chain Completeness Score

| Score | Meaning | Action |
|-------|---------|--------|
| 5/5 | Complete chain | PASS — ready for filing |
| 4/5 | Minor gap | WARNING — fix before filing |
| 3/5 | Significant gap | BLOCK — must remediate |
| 2/5 | Major deficiency | REJECT — rewrite section |
| 1/5 | No real authority | CRITICAL — section unsupported |

---

## Michigan Citation Format Reference

### Statute Format
```
MCL § 722.23         — Child custody factors (Lane A)
MCL § 600.2918       — Housing/contract claims (Lane B)
MCL § 125.534        — Housing code violations (Lane B)
```

### Court Rule Format
```
MCR 2.116(C)(10)     — Summary disposition
MCR 3.210            — Child custody proceedings (Lane A)
MCR 7.201-7.215      — Court of Appeals rules
MRE 801-807           — Hearsay rules
```

### Case Law Format
```
Michigan Supreme Court:    Smith v Jones, 500 Mich 123, 130; 900 NW2d 456 (2023)
Michigan Court of Appeals: Smith v Jones, 340 Mich App 123, 130; 900 NW2d 456 (2023)
Unpublished COA:          Smith v Jones, unpublished per curiam opinion of the
                          Court of Appeals, issued January 15, 2024
                          (Docket No. 365432)
```

---

## Lane-Specific Authority Requirements

### Lane A: Watson/Custody
- **Mandatory statutes**: MCL 722.21-722.31 (Child Custody Act)
- **Key rules**: MCR 3.210-3.218 (domestic relations)
- **Best interest factors**: MCL 722.23(a)-(l) — ALL twelve must be addressed
- **Change of custody**: MCL 722.27, Vodvarka v Grasmeyer, 259 Mich App 499 (2003)
- **PPO matters**: MCL 600.2950, MCR 3.701-3.745

### Lane B: Shady Oaks/Housing
- **Housing codes**: MCL 125.401 et seq, MCL 554.139
- **Contract claims**: MCL 600.5801 et seq (statute of limitations)
- **Consumer protection**: MCL 445.901 et seq (MCPA)
- **Warranty of habitability**: MCL 554.139, Allison v AEW Capital Mgmt

### Lane C: Convergence/County
- **Cross-lane authority**: Authorities that bridge Lane A and Lane B
- **County-specific**: 14th Circuit local rules, Muskegon County procedures
- **Federal overlay**: 42 USC § 1983 (if constitutional claims raised)

---

## Output Contract

```yaml
authority_validation_report:
  filing_id: string          # e.g., "LANE_A_MOTION_MODIFY_PPO"
  total_citations: integer
  validated: integer
  warnings: integer
  failures: integer
  chain_completeness_avg: float  # 0.0 - 5.0
  details:
    - citation: string
      type: enum [statute, rule, case, secondary]
      format_valid: boolean
      exists: boolean
      current: boolean
      pinpoint_accurate: boolean
      chain_complete: boolean
      lane: enum [A, B, C]
      notes: string
  blocking_issues: list[string]
  timestamp: ISO-8601
```

---

## Validation Workflow

```
1. INTAKE: Receive filing/brief for authority audit
2. EXTRACT: Parse all citations from document
3. CLASSIFY: Sort by type (statute/rule/case/secondary)
4. VALIDATE: Run each through appropriate branch
5. CHAIN-CHECK: Verify authority chain completeness
6. CURRENCY: Check all authorities for current status
7. CROSS-REF: Verify citations match propositions
8. REPORT: Generate authority_validation_report
9. REMEDIATE: Flag all failures for correction
10. RE-VALIDATE: Confirm fixes resolve all issues
```

---

## Red Flags — Automatic Failure

| Red Flag | Consequence |
|----------|-------------|
| Overruled case cited as good law | CRITICAL — sanctions risk |
| Wrong reporter volume/page | CRITICAL — credibility loss |
| Statute repealed or amended | CRITICAL — argument void |
| Missing pinpoint citation | WARNING — fix required |
| Unpublished case cited without disclaimer | WARNING — MCR 7.215(C) |
| Federal authority when state controls | WARNING — wrong jurisdiction |
| String citation without parenthetical | MINOR — add for clarity |

---

## Integration Points

- **litigation-brain-spec**: Supplies authority requirements per filing
- **litigation-filing-packager**: Receives validated authority lists
- **litigation-convergence-orchestrator**: Reports authority gaps as DNEW items
- **litigation-appellate-strategist**: Critical for appellate brief authority
- **litigation-skill-auditor**: Audits this skill's compliance

---

## Escalation Protocol

```
IF validation_failures > 0:
  BLOCK filing until all CRITICAL items resolved
  WARN on all WARNING items with 24-hour fix deadline
  LOG all MINOR items for batch cleanup

IF chain_completeness_avg < 3.0:
  ESCALATE to manual attorney review
  DO NOT auto-clear — human must verify

IF currency_check_unavailable:
  FLAG as UNVERIFIED — do not certify
  NOTE: "Currency check pending — do not file without verification"
```

## Related Skills

- [litigation-brief-writer](skill://litigation-brief-writer) — Drafts court-ready legal briefs
- [litigation-record-builder](skill://litigation-record-builder) — Builds appellate record and exhibits

## Self-Improvement Log

### v2.1 (2026-03-11) — Session-Learned Enhancements

**Known-Real Citations Database**: Maintain a verified-real citation list to prevent hallucination:
- Troxel v Granville, 530 US 57 (2000) — parental liberty
- Vodvarka v Grasmeyer, 259 Mich App 499 (2003) — parenting time modification
- Cain v Dep't of Corrections, 451 Mich 470 (1996) — disqualification
- Armstrong v Ypsilanti Township, 248 Mich App 573 (2001) — judicial bias
- In re Contempt of Dougherty, 429 Mich 81 (1987) — contempt power
- Mathews v Eldridge, 424 US 319 (1976) — due process
- Monell v Dept of Social Services, 436 US 658 (1978) — municipal liability
- Boddie v Connecticut, 401 US 371 (1971) — access to courts
- M.L.B. v S.L.J., 519 US 102 (1996) — parental rights + indigency
- Turner v Rogers, 564 US 431 (2011) — civil contempt safeguards
- Friedman v Dozorc, 412 Mich 1 (1981) — abuse of process

**Known-Hallucinated Citations (REJECT ON SIGHT)**:
- McCraney v Ford Motor Co 282 Mich App 647 (2009) — DOES NOT EXIST
- Any citation AI cannot trace to a real source → flag as [VERIFY]

**Cross-Filing Citation Consistency**: When the same case is cited in multiple filings, verify the citation format is IDENTICAL across all documents. Different page numbers, different years, or different reporter volumes across filings = credibility destruction.

**MCR/MCL Version Currency**: Michigan court rules are amended regularly. Before certifying any MCR citation, check the effective date. MCR 3.206 was amended in 2025 (electronic service default). MCR 3.207 proposed amendments may affect ex parte standards.


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
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |

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
