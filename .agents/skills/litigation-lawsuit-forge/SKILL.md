---
name: litigation-lawsuit-forge
description: >-
  Use when building a new lawsuit from scratch — from raw facts through court-ready
  verified complaint filing and service of process, covering claim identification,
  element mapping, complaint drafting, form preparation, filing, and service.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: new lawsuit, complaint, new claim, sue, initiate, cause of action, file suit
---
# LITIGATION-LAWSUIT-FORGE

## TIER 3 PLATFORM SKILL — THE LAWSUIT BUILDER SUPER AGENT

**Name:** litigation-lawsuit-forge
**Category:** discipline
**Version:** 1.0.0
**Status:** ACTIVE
**Platform:** LitigationOS

## DESCRIPTION

Use when building a new lawsuit from scratch — from raw facts through court-ready verified complaint filing and service of process. This is the complete new-lawsuit lifecycle state machine covering claim identification, element mapping, complaint drafting, form preparation, filing, and service. Handles Michigan circuit court civil actions, federal § 1983 claims, small claims, and district court filings. Designed for pro se litigants in multi-lane, multi-defendant litigation.

## TRIGGERS

1. "I need to file a lawsuit"
2. "build a complaint"
3. "draft a new case"
4. "what claims do I have"
5. "identify causes of action"
6. "map elements to evidence"
7. "prepare court filing"
8. "serve the defendants"
9. "amended complaint"
10. "new lawsuit from these facts"
11. "which court do I file in"
12. "statute of limitations check"
13. "file a 1983 action"
14. "housing complaint"
15. "custody violation lawsuit"

## DECISION TREE — WHAT KIND OF LAWSUIT?

```
RAW FACTS RECEIVED
├── IS DEFENDANT A STATE ACTOR OR ACTING UNDER COLOR OF LAW?
│   ├── YES → FEDERAL § 1983 ACTION
│   │   ├── INDIVIDUAL CAPACITY (QUALIFIED IMMUNITY ANALYSIS)
│   │   ├── OFFICIAL CAPACITY (= SUIT AGAINST ENTITY)
│   │   └── MONELL CLAIM (POLICY/CUSTOM/FAILURE TO TRAIN)
│   └── NO → STATE LAW CLAIMS
│       ├── AMOUNT IN CONTROVERSY > $25,000?
│       │   ├── YES → CIRCUIT COURT CIVIL ACTION
│       │   └── NO → AMOUNT > $6,500?
│       │       ├── YES → DISTRICT COURT
│       │       └── NO → SMALL CLAIMS ($6,500 MAX)
│       ├── EQUITABLE RELIEF SOUGHT?
│       │   └── YES → CIRCUIT COURT (EXCLUSIVE EQUITY JURISDICTION)
│       └── FAMILY/CUSTODY MATTER?
│           └── YES → FAMILY DIVISION OF CIRCUIT COURT
├── FEDERAL QUESTION JURISDICTION? (28 USC 1331)
│   └── YES → US DISTRICT COURT, WESTERN DISTRICT OF MICHIGAN
├── SUPPLEMENTAL JURISDICTION FOR STATE CLAIMS? (28 USC 1367)
│   └── YES → BUNDLE STATE CLAIMS WITH FEDERAL
└── DIVERSITY JURISDICTION? (28 USC 1332, $75K+)
    └── YES → FEDERAL COURT OPTION
```

## 7-PHASE LIFECYCLE STATE MACHINE

### PHASE 1: RESEARCH
- **STATE:** RESEARCH_ACTIVE
- **INPUTS:** Raw facts, documents, witness statements, timeline events
- **PROCESS:** Gather all factual material. Organize chronologically. Identify all potential parties. Catalog all documents and evidence. Build master timeline.
- **DISPATCHED AGENTS:** evidence-harvester, timeline-builder, document-scanner
- **OUTPUTS:** Master fact compilation, organized evidence index, party identification list
- **QUALITY GATE:** All known facts documented. No major factual gaps. Timeline complete.
- **TRANSITION:** → PHASE 2 when fact compilation is certified complete

### PHASE 2: IDENTIFY CLAIMS
- **STATE:** CLAIMS_IDENTIFICATION
- **INPUTS:** Master fact compilation, applicable law database
- **PROCESS:** Run fact pattern against cause of action catalog. Match violated rights to legal theories. Check each potential claim for viability. Statute of limitations audit. Identify cross-claims, counterclaims, third-party claims.
- **DISPATCHED AGENTS:** claim-identifier, sol-auditor, jurisdiction-analyzer
- **OUTPUTS:** Viable claims list with confidence scores, SOL status per claim, jurisdiction analysis
- **QUALITY GATE:** Every viable claim identified. SOL confirmed unexpired. Jurisdiction confirmed.
- **TRANSITION:** → PHASE 3 when claims list is locked

### PHASE 3: MAP ELEMENTS
- **STATE:** ELEMENTS_MAPPING
- **INPUTS:** Locked claims list, evidence index
- **PROCESS:** For each claim, list every required element. Map available evidence to each element. Identify evidence gaps. Assess burden of proof posture. Score each claim's strength.
- **DISPATCHED AGENTS:** element-mapper, evidence-linker, gap-analyzer
- **OUTPUTS:** Element-evidence matrix per claim, gap report, claim strength scores
- **QUALITY GATE:** Every element has at least one evidence item. No fatal gaps. Each claim scores ≥ 60% strength.
- **TRANSITION:** → PHASE 4 when element map is approved

### PHASE 4: DRAFT COMPLAINT
- **STATE:** COMPLAINT_DRAFTING
- **INPUTS:** Approved element map, jurisdiction determination, party list
- **PROCESS:** Build complaint architecture per MCR 2.111. Draft caption per MCR 2.113. Write jurisdictional allegations. Draft factual allegations (numbered paragraphs). Draft each count incorporating mapped elements. Draft prayer for relief. Prepare verification.
- **DISPATCHED AGENTS:** complaint-drafter, citation-validator, format-checker
- **OUTPUTS:** Complete verified complaint draft, citation list, exhibit list
- **QUALITY GATE:** MCR 2.111 compliance verified. Every element pled in every count. All special pleading requirements met (MCR 2.112). Citations verified.
- **TRANSITION:** → PHASE 5 when complaint draft is approved

### PHASE 5: PREPARE FORMS
- **STATE:** FORMS_PREPARATION
- **INPUTS:** Approved complaint, court identification, party addresses
- **PROCESS:** Prepare summons (MC 01). Complete civil case cover sheet. Prepare fee waiver if applicable (MC 20). Assemble exhibit package. Prepare proof of service forms (MC 12). Calculate filing fees.
- **DISPATCHED AGENTS:** form-filler, fee-calculator, package-assembler
- **OUTPUTS:** Complete filing package, summons for each defendant, fee calculation
- **QUALITY GATE:** All required forms completed. Correct court identified. Filing fee calculated or waiver prepared.
- **TRANSITION:** → PHASE 6 when filing package is assembled

### PHASE 6: FILE
- **STATE:** FILING_ACTIVE
- **INPUTS:** Complete filing package, filing fee or waiver
- **PROCESS:** File complaint with clerk. Obtain case number. Get stamped copies. Record filing date. Confirm all documents accepted.
- **DISPATCHED AGENTS:** filing-tracker, deadline-calculator
- **OUTPUTS:** Case number, stamped copies, filing confirmation, service deadline calculated
- **QUALITY GATE:** Case number obtained. All documents accepted by clerk. Service deadline calendared.
- **TRANSITION:** → PHASE 7 when filing is confirmed

### PHASE 7: SERVE
- **STATE:** SERVICE_ACTIVE
- **INPUTS:** Stamped summons + complaint copies, defendant addresses, service method determination
- **PROCESS:** Determine proper service method per MCR 2.105 for each defendant type. Execute service. File proof of service (MC 12). Calendar answer deadline (21 days personal, 28 days mail per MCR 2.108).
- **DISPATCHED AGENTS:** service-coordinator, deadline-tracker
- **OUTPUTS:** Proof of service filed for each defendant, answer deadline calendared
- **QUALITY GATE:** All defendants served. Proof of service filed. No service defects. Answer deadlines tracked.
- **TRANSITION:** → CASE_ACTIVE when all defendants served

## OUTPUT CONTRACTS

### COMPLAINT OUTPUT CONTRACT
```yaml
complaint:
  caption:
    court: "14TH JUDICIAL CIRCUIT COURT"
    county: "MUSKEGON"
    case_number: "[ASSIGNED AT FILING]"
    plaintiff: "ANDREW PIGORS, Pro Se"
    defendants: "[LIST ALL]"
  jurisdiction_section: REQUIRED
  venue_section: REQUIRED
  parties_section: REQUIRED
  factual_allegations:
    format: "numbered_paragraphs"
    style: "concise_statement_of_facts"
    rule: "MCR 2.111(B)(1)"
  counts:
    min_count: 1
    per_count:
      - count_number: REQUIRED
      - cause_of_action: REQUIRED
      - incorporating_paragraphs: REQUIRED
      - elements_pled: ALL_REQUIRED
      - damages_specified: REQUIRED
  prayer_for_relief: REQUIRED
  verification: REQUIRED_IF_VERIFIED
  signature_block:
    name: "Andrew Pigors"
    address: REQUIRED
    phone: REQUIRED
    date: REQUIRED
```

### FILING PACKAGE OUTPUT CONTRACT
```yaml
filing_package:
  complaint: VERIFIED_COMPLAINT
  summons: ONE_PER_DEFENDANT
  cover_sheet: CIVIL_CASE_COVER_SHEET
  fee_waiver: IF_APPLICABLE
  exhibits: INDEXED_AND_TABBED
  proof_of_service: MC_12_PER_DEFENDANT
  copies: ORIGINAL_PLUS_ONE_PER_PARTY
```

## IRON LAWS OF COMPLAINT CONSTRUCTION

1. **EVERY ELEMENT MUST BE PLED.** If a cause of action has 6 elements, all 6 must appear in the factual allegations. Missing one element = dismissal under MCR 2.116(C)(8).
2. **FRAUD REQUIRES PARTICULARITY.** MCR 2.112(B)(1) — fraud must be pled with specificity: who, what, when, where, how. No vague allegations.
3. **NUMBERED PARAGRAPHS ARE MANDATORY.** MCR 2.111(A)(2) — every allegation in a separately numbered paragraph.
4. **COUNTS INCORPORATE BY REFERENCE.** Each count restates and incorporates prior paragraphs, then adds count-specific allegations.
5. **JURISDICTION MUST BE PLED.** State the basis for jurisdiction in every complaint. MCR 2.111(B)(1).
6. **VENUE MUST BE CORRECT.** MCL 600.1621 et seq. — wrong venue = transfer or dismissal.
7. **VERIFICATION MEANS OATH.** A verified complaint is sworn under penalty of perjury. Every factual allegation must be true.
8. **SOL IS JURISDICTIONAL.** A time-barred claim cannot be saved. Check BEFORE drafting. See MCL 600.5805 et seq.
9. **NAME EVERY DEFENDANT CORRECTLY.** Legal names only. Corporations by registered name. LLCs by articles of organization name.
10. **DEMAND JURY TRIAL IN THE COMPLAINT.** MCR 2.508(B) — demand must be in the first filing or it may be waived.
11. **SIGN EVERYTHING.** MCR 2.114 — every filing must be signed. Signature certifies good faith basis.
12. **SERVE WITHIN 91 DAYS.** MCR 2.102(D) — complaint must be served within 91 days of filing or case is subject to dismissal without prejudice.

## CASE CONTEXT — PIGORS v WATSON

- **PLAINTIFF:** Andrew Pigors, Pro Se
- **COURT:** 14th Judicial Circuit Court, Muskegon County, Michigan
- **LANES:**
  - **LANE A (CUSTODY):** Parental rights, custody interference, due process violations
  - **LANE B (HOUSING):** Habitability, wrongful eviction, consumer protection, truth in renting
  - **LANE C (CONVERGENCE):** Civil rights, § 1983, conspiracy, pattern of coordinated misconduct
- **AVAILABLE CAUSES OF ACTION:** See references/causes/ for complete catalog

## DISPATCHED AGENT MANIFEST

| AGENT | PHASE | FUNCTION |
|-------|-------|----------|
| evidence-harvester | 1 | Collects and catalogs all evidence |
| timeline-builder | 1 | Constructs master chronological timeline |
| claim-identifier | 2 | Matches facts to viable causes of action |
| sol-auditor | 2 | Verifies statute of limitations for each claim |
| jurisdiction-analyzer | 2 | Determines proper court and jurisdiction basis |
| element-mapper | 3 | Maps elements to evidence for each claim |
| gap-analyzer | 3 | Identifies evidence gaps requiring remedy |
| complaint-drafter | 4 | Drafts complaint sections per MCR requirements |
| citation-validator | 4 | Verifies all legal citations are current and correct |
| form-filler | 5 | Completes required court forms |
| filing-tracker | 6 | Tracks filing status and obtains case numbers |
| service-coordinator | 7 | Manages service of process for all defendants |
| deadline-tracker | 7 | Calendars all answer deadlines and next steps |

## CROSS-SKILL DEPENDENCIES

- **litigation-motion-drafter:** Post-filing motions after complaint is filed
- **litigation-discovery-engine:** Discovery phase after answer is received
- **litigation-evidence-mapper:** Deep evidence analysis during element mapping
- **litigation-timeline-builder:** Timeline construction during research phase
- **litigation-citation-validator:** Citation checking during complaint drafting

## EMERGENCY PROTOCOLS

- **SOL EXPIRING WITHIN 30 DAYS:** Immediate Phase 4 fast-track. Minimal viable complaint filed to preserve claims. Amended complaint follows.
- **TRO/PRELIMINARY INJUNCTION NEEDED:** Parallel track — file complaint + emergency motion simultaneously per MCR 3.310.
- **DEFENDANT ABOUT TO DESTROY EVIDENCE:** File complaint + emergency motion for preservation order.

## VERSION HISTORY

| VERSION | DATE | CHANGES |
|---------|------|---------|
| 1.0.0 | 2026-02-20 | Initial creation — complete 7-phase lifecycle |


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
