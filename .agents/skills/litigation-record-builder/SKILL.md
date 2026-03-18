---
name: litigation-record-builder
description: >-
  Use when constructing, designating, or supplementing the record on appeal under
  Michigan Court Rules, ordering transcripts, compiling exhibits for trial or appellate
  proceedings, or preserving the lower court record.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: record, transcript, exhibit, appeal, MCR 7.210
---
# LITIGATION-RECORD-BUILDER

## Metadata

- **name**: litigation-record-builder
- **category**: discipline
- **tier**: 2
- **version**: 1.0.0
- **context**: Pigors v Watson, 14th Judicial Circuit, Muskegon County, MI (Pro Se)
- **depends-on**: litigation-evidence-mapper, litigation-timeline-engine

## Description

Use when constructing, designating, or supplementing the record on appeal under Michigan Court Rules, ordering transcripts from court reporters, compiling and indexing exhibits for trial or appellate proceedings, or preserving the lower court record. This skill covers the complete MCR 7.210 record designation process, transcript ordering logistics, exhibit compilation standards, and record supplementation procedures. Critical for any appeal to the Michigan Court of Appeals or Michigan Supreme Court in Pigors v Watson, and equally applicable to trial-level exhibit organization.

## Triggers

- User is preparing or has filed a claim of appeal and needs to designate the record
- User needs to order transcripts from court reporters in Muskegon County
- User asks how to compile, index, or organize exhibits for trial or appeal
- User needs to supplement or correct the record on appeal
- User asks about MCR 7.210, record designation, or settled statements
- User is preparing exhibit binders, cover pages, or exhibit lists for hearing
- User needs to understand what gets included in the lower court record

## Record on Appeal — Complete Framework

### What Constitutes the Record

Under MCR 7.210(A), the record on appeal consists of:

1. **The original papers filed in the lower court** — all pleadings, motions, responses, orders, judgments
2. **The transcript of proceedings** — or an authorized substitute (settled statement, agreed statement)
3. **The exhibits** — all exhibits admitted or offered at trial/hearing

The record is **not** whatever you want it to be. It is defined by what was actually filed, entered, or offered in the lower court proceedings.

### Record Designation Process

```
Step 1: File Claim of Appeal (MCR 7.204)
        └─ Triggers 21-day transcript ordering deadline
Step 2: Order Transcripts (within 21 days of filing claim)
        └─ File proof of ordering with COA clerk
Step 3: File Transcript Production Order if reporter is late
Step 4: Receive and review transcripts for accuracy
        └─ File corrections under MCR 7.210(B)(2) if needed
Step 5: Designate additional record items if needed
        └─ MCR 7.210(A)(3) — anything not automatically included
Step 6: File Record Appendix with appellant brief
        └─ MCR 7.212(C) — required appendix contents
```

### Automatic vs. Designated Record Items

| Automatically in Record | Must Be Designated |
|---|---|
| All filed pleadings | Unfiled documents referenced at hearing |
| Court orders and judgments | Sealed documents (with motion to unseal) |
| Register of actions | Documents from companion cases |
| Filed exhibits (admitted or offered) | Demonstrative exhibits not formally offered |
| Jury instructions (if jury trial) | Electronic recordings not transcribed |

### The Record Appendix (MCR 7.212(C))

The appellant's brief **must** include an appendix containing:

- The judgment or order appealed from
- Any opinion of the trial court
- The register of actions
- Any jury instructions given and refused (if applicable)
- Any relevant findings of fact and conclusions of law
- Other parts of the record specifically referenced in the brief

**Critical**: Failure to include required appendix items can result in dismissal or striking of the brief.

## Transcript Ordering Logistics

### Muskegon County — 14th Judicial Circuit

**Court Reporter Contact:**
- Muskegon County Circuit Court
- 990 Terrace Street, Muskegon, MI 49442
- Contact court reporter coordinator through clerk's office: (231) 724-6241
- Request by hearing date, case number, and judge name

**Ordering Process:**
1. Identify all hearing dates requiring transcription
2. Contact court reporter assigned to each hearing
3. Request cost estimate (per-page rate, typically $3.25–$4.50/page)
4. Pay deposit if required (commonly 50% upfront)
5. Confirm delivery timeline (standard: 56 days; expedited: 14–28 days for additional fee)
6. File proof of transcript ordering with COA within 21 days of claim of appeal

### Transcript Priorities for Pigors v Watson

Prioritize transcripts in this order:
1. **Dispositive hearings** — custody determination, summary judgment
2. **Evidentiary hearings** — any hearing where testimony was taken
3. **Motion hearings** — where key legal arguments were presented
4. **Status conferences** — only if relevant exchanges occurred on record

### Partial Transcripts

MCR 7.210(B)(1)(b) allows ordering partial transcripts if the entire proceedings are not necessary. The appellant must:
- Describe the portions ordered
- State why the remainder is unnecessary
- Serve the appellee, who may order additional portions

**Danger**: If you omit a portion and the appellee argues it matters, the court may presume the omitted portion supports the lower court's decision.

## Exhibit Compilation Standards

### Trial-Level Exhibit Organization

```
EXHIBIT BINDER STRUCTURE:
├── Cover Page (Case caption, "Plaintiff's Exhibits")
├── Exhibit Index / List
│   ├── Exhibit Number
│   ├── Description
│   ├── Date of Document
│   ├── Number of Pages
│   └── Admitted (Y/N/Offered)
├── Tab Dividers (one per exhibit)
│   ├── Exhibit A / 1 — [Description]
│   ├── Exhibit B / 2 — [Description]
│   └── ...
└── Back Cover
```

### Michigan Exhibit Cover Page Colors

| Party | Cover Color | Tab Color |
|---|---|---|
| Plaintiff | Yellow | Yellow |
| Defendant | Blue | Blue |
| Court Exhibits | White/Green | White/Green |

**Note**: Color conventions vary by county and judge preference. Verify with the 14th Circuit clerk or judge's scheduling clerk before preparing binders.

### Exhibit Numbering Conventions

- **Plaintiff's Exhibits**: Letters (A, B, C...) or Numbers (1, 2, 3...) — confirm with court
- **Defendant's Exhibits**: Typically the opposite system from plaintiff
- **Sub-exhibits**: Use decimals (Ex. A-1, A-2) for multi-page documents or related groups
- **Pre-mark all exhibits**: File exhibit list with court before trial/hearing

### Exhibit Authenticity Requirements

Every exhibit must be authenticatable under MRE 901:
- **Documents**: Testimony identifying the document, or self-authentication (MRE 902)
- **Photographs**: Testimony that the photo fairly and accurately depicts the scene
- **Electronic records**: Business records foundation (MRE 803(6)) or party admission
- **Text messages/emails**: Authentication through testimony + metadata or admission

### Cross-Referencing Exhibits to Brief

Every exhibit referenced in a brief must include:
- The exhibit number/letter
- A parenthetical description
- A pinpoint page reference if the exhibit is multi-page
- Connection to the legal element it supports

**Example**: "(Ex. C, Custody Order dated 01/10/2025, at ¶ 4 [specifying 6:00 PM exchange time].)"

## Record Supplementation

### When the Record Is Incomplete

If the record is missing documents or contains errors:

1. **Motion to Supplement Record** — MCR 7.210(C)(1)
   - File in COA, identify missing items, explain relevance
   - Must show items were part of lower court proceedings

2. **Settled Statement** — MCR 7.210(B)(3)
   - When transcript is unavailable (reporter unavailable, recording lost)
   - Appellant prepares proposed statement of proceedings
   - Serve on appellee, who has 21 days to object or propose amendments
   - Submit to trial court for settlement (approval)

3. **Agreed Statement** — MCR 7.210(B)(4)
   - Parties stipulate to the relevant facts and proceedings
   - Rare in contested cases but available

### Correcting Transcript Errors

Under MCR 7.210(B)(2):
1. Review transcript for accuracy within 21 days of receipt
2. Identify specific errors (wrong words, missing exchanges, inaccurate attributions)
3. File motion in trial court to correct transcript
4. Attach proposed corrections with specific page/line references
5. Court reporter responds; trial judge resolves disputes

## Record Preservation Checklist

```
□  All pleadings filed by all parties — confirmed in register of actions
□  All court orders — signed copies, not just minute entries
□  All transcripts ordered — proof of ordering filed with COA
□  All exhibits — admitted AND offered (even if excluded)
□  Proposed orders — both granted and denied
□  Correspondence filed with court — if any
□  Any sealed materials — with motion to include if needed
□  Register of actions — complete and current
□  Docket entries — cross-checked against personal records
□  Fee waiver orders — if applicable to transcript costs
```

## Output Format

When building record components, produce:

1. **Record Designation Checklist**: Hearing-by-hearing list of what to order
2. **Transcript Order Form**: Pre-filled with hearing dates, case number, reporter info
3. **Exhibit Index**: Formatted table with all exhibits numbered and described
4. **Appendix Contents Page**: MCR 7.212(C) compliant table of contents
5. **Gap Analysis**: Identify any missing record items and remediation steps

## Files

- `gotchas.md` — Anti-rationalization table for record-building pitfalls
- `references/record-designation.md` — MCR 7.210 designation requirements
- `references/transcript-ordering.md` — Court reporter logistics and procedures
- `references/exhibit-compilation.md` — Exhibit organization and indexing standards

## Related Skills

- [litigation-filing-architect](skill://litigation-filing-architect) — Architects court-ready filing packages
- [litigation-appellate-strategist](skill://litigation-appellate-strategist) — Prepares Michigan appellate filings strategy


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
| Custody Modification | 65/100 | A,D,E,F | Verified |
| Emergency Custody | 55/100 | A,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,D,E,F | Verified |
| Contempt | 70/100 | A,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,D,E,F | Verified |
| Appeal Brief | 70/100 | A,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,D,E,F | Verified |

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
