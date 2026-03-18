---
name: litigation-filing-architect
description: >-
  Use when producing court-ready filing architecture, generating VehicleMap-driven documents, or drafting motions and briefs for Michigan court filings under MCR 2.113.
metadata:
  category: discipline
  author: andrew-pigors
  version: "2.2.0"
  triggers: filing, motion, brief, court filing, VehicleMap, MCR 2.113
  changelog:
    v2.2.0: |
      - Architecture audit: 28 checks across 3 clerk-ready filings
      - 4 FAILs (Contempt placeholders), 10 WARNINGs resolved
      - Template error flags: 07_COURT_DOCUMENTS uses wrong names (Amber→Emily), wrong court (51st→14th), wrong judge (Matthew→Jenny L.)
      - Filing readiness: Lane E 95%, Lane A 90%, Lane D 85%, Lane F 80%, Lane C 70%
      - 9 court-ready documents tracked (JTC READY, MSC NEAR-READY, 2 briefs COURT-READY)
      - 13,432 evidence_zips files flattened for filing support
      - Cycle 6: 100,995 documented violation instances across 49 types
---

# litigation-filing-architect

## Metadata

```yaml
name: litigation-filing-architect
version: 2.0.0
category: discipline
tier: 2
description: >
  Use when producing court-ready filing architecture from a legal action ID,
  generating VehicleMap-driven documents for Michigan 14th Judicial Circuit
  (Muskegon County) across all three case lanes.
triggers:
  - filing
  - court document
  - motion draft
  - legal action
  - vehicle map
  - document generation
  - court packet
  - filing architecture
```

## Purpose

This skill converts a legal action identifier (A1–A35, B1–B14, C1–C7) into a
complete, court-ready filing package. It applies Michigan Court Rules (MCR),
local administrative orders for the 14th Judicial Circuit, and lane-specific
requirements for Pigors v Watson litigation.

## Case Lane Map

| Lane | Caption | Case Number(s) | Judge | Court |
|------|---------|-----------------|-------|-------|
| A | Watson/Custody | 2024-001507-DC, 2023-5907-PP | McNeill | 14th Circuit, Muskegon County |
| B | Shady Oaks/Housing | 2025-002760-CZ | Hoopes | 14th Circuit, Muskegon County |
| C | Convergence/County | — | Multiple | 14th Circuit / Federal |

## Decision Tree

```
INPUT: Action ID (e.g., A12, B3, C5)
  │
  ├─ Parse lane prefix → A / B / C
  │   ├─ A → Load custody/PPO rule set (MCR 3.200 series)
  │   ├─ B → Load civil/housing rule set (MCR 2.100 series, MCL 600.5714)
  │   └─ C → Load convergence/federal rule set (28 USC § 1983, MCR 7.200)
  │
  ├─ Resolve action number → action definition from master action table
  │   ├─ Retrieve required documents list
  │   ├─ Retrieve applicable court rules
  │   └─ Retrieve deadline calculations
  │
  ├─ Generate VehicleMap
  │   ├─ Primary vehicle (motion, complaint, petition, brief)
  │   ├─ Supporting vehicles (affidavits, exhibits, indexes)
  │   ├─ Service vehicles (proof of service, certificates)
  │   └─ Administrative vehicles (proposed orders, cover sheets)
  │
  ├─ For EACH vehicle in map:
  │   ├─ Select template from form library
  │   ├─ Populate header block (caption, case number, judge)
  │   ├─ Populate body sections from evidence/argument inventory
  │   ├─ Insert citation blocks (statutes, rules, case law)
  │   ├─ Generate certificate of service
  │   └─ Validate against MCR formatting requirements
  │
  ├─ Assemble filing packet
  │   ├─ Order documents per local rule
  │   ├─ Generate table of contents
  │   ├─ Calculate page counts
  │   └─ Generate filing checklist
  │
  └─ OUTPUT: Complete filing architecture + validation report
```

## Mode Switches

### Mode 1: FULL BUILD
Triggered when action ID is provided with no prior partial work.
Produces the complete filing architecture from scratch.

### Mode 2: DELTA BUILD
Triggered when a prior filing exists and amendments are needed.
Generates only changed vehicles, preserving prior work.

### Mode 3: VALIDATION ONLY
Triggered with `--validate` flag. Checks an existing filing packet
against court rules without generating new content.

### Mode 4: TEMPLATE EXPORT
Triggered with `--template` flag. Exports blank templates for the
action ID without populating content.

## Output Contract

```yaml
output:
  filing_packet:
    type: directory
    structure:
      - 00_COVER_SHEET.md
      - 01_PRIMARY_VEHICLE.md        # motion / complaint / petition
      - 02_BRIEF_IN_SUPPORT.md       # if applicable
      - 03_AFFIDAVIT_{name}.md       # one per affiant
      - 04_EXHIBIT_INDEX.md
      - 05_EXHIBITS/                  # subdirectory
      - 06_PROPOSED_ORDER.md
      - 07_PROOF_OF_SERVICE.md
      - 08_FILING_CHECKLIST.md
    metadata:
      case_number: string
      lane: A | B | C
      judge: string
      action_id: string
      generated_at: ISO-8601
      page_count: integer
      filing_deadline: ISO-8601 | null

  validation_report:
    type: object
    fields:
      - rule_compliance: list[{rule, status, note}]
      - missing_elements: list[string]
      - warnings: list[string]
      - ready_to_file: boolean
```

## Lane A: Watson/Custody Actions (A1–A35)

### Key Action Categories
- **A1–A5**: Custody modification motions (MCR 3.210)
- **A6–A10**: PPO modification/termination (MCL 600.2950)
- **A11–A15**: Discovery motions (MCR 2.302–2.313)
- **A16–A20**: Contempt proceedings (MCR 3.606)
- **A21–A25**: Parenting time enforcement (MCL 722.27a)
- **A26–A30**: Judicial misconduct filings (MCR 9.200 series)
- **A31–A35**: Emergency/ex parte motions (MCR 3.207)

### Required Elements — Lane A
1. Verified statement per MCR 3.206(A) for all custody motions
2. Friend of the Court recommendation reference
3. UCCJEA declaration (MCL 722.1209) for jurisdiction
4. Domestic Relations Cover Sheet (SCAO MC 290)

## Lane B: Shady Oaks/Housing Actions (B1–B14)

### Key Action Categories
- **B1–B3**: Breach of warranty / habitability (MCL 554.139)
- **B4–B6**: Consumer Protection Act claims (MCL 445.903)
- **B7–B9**: Discovery and inspection motions
- **B10–B12**: Summary disposition motions (MCR 2.116)
- **B13–B14**: Injunctive relief / TRO (MCR 3.310)

### Required Elements — Lane B
1. Civil filing cover sheet (SCAO MC 01)
2. Summons (SCAO MC 01a) if initiating
3. Affidavit of merit for habitability claims
4. Rent escrow documentation if applicable

## Lane C: Convergence/County Actions (C1–C7)

### Key Action Categories
- **C1–C2**: 42 USC § 1983 federal civil rights complaints
- **C3–C4**: State-level convergence claims
- **C5**: JTC complaint (MCR 9.220)
- **C6**: Mandamus / superintending control (MCR 3.302)
- **C7**: Consolidated record compilation

### Required Elements — Lane C
1. Federal complaint format (FRCP if federal court)
2. Jurisdictional statement
3. Cross-reference table linking Lane A + Lane B evidence
4. Constitutional violation checklist

## VehicleMap Schema

```yaml
vehicle_map:
  primary:
    type: motion | complaint | petition | brief | application
    title: string
    mcr_authority: string
    statutory_authority: string | null
  supporting:
    - type: affidavit | declaration | exhibit_index | memorandum
      title: string
      required: boolean
  service:
    - type: proof_of_service | certificate_of_service
      method: personal | mail | email | efiling
      mcr_rule: MCR 2.105 | MCR 2.107
  administrative:
    - type: proposed_order | cover_sheet | fee_waiver
      scao_form: string | null
```

## Filing Deadline Calculator

```
Motion filing deadlines (MCR 2.119):
  - Motion + brief: ≥ 9 days before hearing (personal service)
  - Motion + brief: ≥ 14 days before hearing (mail service)
  - Response brief: ≥ 7 days before hearing
  - Reply brief: ≥ 3 days before hearing (if permitted)

Ex parte motion deadlines (MCR 3.207):
  - Filed same day or next business day
  - Opposing party notice: as soon as practicable

Discovery deadlines (MCR 2.302):
  - Interrogatories response: 28 days
  - Document production response: 28 days
  - Deposition notice: reasonable time (typically 14 days)
```

## Validation Rules

1. **Caption check**: Case number format matches circuit court pattern
2. **Judge assignment**: Correct judge for lane (McNeill=A, Hoopes=B)
3. **Signature block**: Proper pro se or attorney designation
4. **Certificate of service**: Method matches MCR 2.107 requirements
5. **Page limits**: Briefs ≤ 20 pages unless leave granted (local rule)
6. **Font/margin**: 12pt, double-spaced, 1-inch margins (MCR 2.119(A)(1))
7. **Exhibit labeling**: Sequential, with index cross-reference
8. **Fee waiver**: Included if applicable (MCR 2.002)

## Error Handling

| Error | Response |
|-------|----------|
| Unknown action ID | Return error + list valid IDs for lane |
| Missing evidence for required section | Generate placeholder + WARNING flag |
| Conflicting court rules | Flag conflict + cite both rules + recommend resolution |
| Deadline already passed | Generate filing + URGENT flag + motion for late filing |
| Wrong judge for lane | Auto-correct + log warning |

## Integration Points

- **litigation-red-team**: Send completed filing for adversarial review before submission
- **litigation-judicial-analyst**: Pull judge preferences for formatting/argument style
- **litigation-evidence-harvester**: Pull classified evidence atoms for exhibit population
- **litigation-impeachment-engine**: Pull impeachment packages for cross-examination exhibits

## Usage Examples

```
# Full build for custody motion
invoke litigation-filing-architect --action A3 --mode full

# Validate existing filing
invoke litigation-filing-architect --action B7 --mode validate --path ./COURT_PACKETS_v3/

# Export blank templates for federal complaint
invoke litigation-filing-architect --action C1 --mode template
```

## Related Skills

- [litigation-brief-writer](skill://litigation-brief-writer) — Drafts court-ready legal briefs
- [litigation-record-builder](skill://litigation-record-builder) — Builds appellate record and exhibits

## Self-Improvement Log

### v2.1 (2026-03-11) — Session-Learned Enhancements

**CLERK_READY Directory Convention**: All final, print-ready filings go to `01_FILINGS/CLERK_READY/` with numbered prefixes (01_, 02_, 03_...) matching the priority score order. This separates draft work from court-submission-ready documents.

**Universal Templates Required**: Every filing package MUST include:
1. MC 280 Proof of Service (use template at `01_FILINGS/TEMPLATES/MC280_PROOF_OF_SERVICE.md`)
2. MC 97 Fee Waiver (use template at `01_FILINGS/TEMPLATES/MC97_FEE_WAIVER_APPLICATION.md`)
3. Proposed Order (embedded in the motion or as separate document)
4. Exhibit Index with Bates references

**Multi-Lane Packaging**: When assembling filings, the manifest (`01_FILINGS/MASTER_FILING_MANIFEST.md`) tracks status across ALL lanes. Use it as the source of truth for what exists vs what's needed.

**Fabrication Guardrails** (CRITICAL):
- NEVER use "9 CPS investigations" (fabricated)
- NEVER cite McCraney v Ford Motor Co 282 Mich App 647 (hallucinated)
- Use "305 documented interference incidents" NOT "91% alienation score"
- Use "215+ days" NOT "329+" or "571+"
- Poisoning allegation tested NEGATIVE — never assert it as true
- L.D.W. birthday math: DOB 11/9/2022, so 1st=2023, 2nd=2024, 3rd=2025

**Priority Matrix Integration**: Filing priority scores (from `filing_priority` SQL table) drive the build order. Current top 3: Emergency PT (93.38) > Disqualification (91.24) > JTC (91.14).

**Proof of Service Per Defendant**: Track PoS status in manifest. 583 filings were previously found missing PoS — every new filing MUST have PoS generated.

**8-Jurisdiction Awareness**: Captions differ per court:
- 14th Circuit (Muskegon) — "STATE OF MICHIGAN / IN THE 14TH JUDICIAL CIRCUIT..."
- COA — "STATE OF MICHIGAN / COURT OF APPEALS" + COA case number
- MSC — "STATE OF MICHIGAN / SUPREME COURT" + MSC number
- W.D. Michigan — "UNITED STATES DISTRICT COURT / WESTERN DISTRICT OF MICHIGAN, SOUTHERN DIVISION"
- JTC — "BEFORE THE JUDICIAL TENURE COMMISSION OF MICHIGAN"
- AGC — "ATTORNEY GRIEVANCE COMMISSION" complaint format


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
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.206 | 667 | 🆕 Verify & integrate |
| MCR 8.119 | 643 | 🆕 Verify & integrate |
| MCR 2.003(C)(1)(a) | 641 | 🆕 Verify & integrate |
| MCR 7.212 | 632 | 🆕 Verify & integrate |

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
| `litigation-service-engine` | Integration | Bidirectional data exchange |
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |
| `litigation-record-builder` | Integration | Complementary analysis |
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
