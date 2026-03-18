---
name: litigation-cause-of-action-library
description: >-
  Use when identifying, looking up, or comparing causes of action available under
  Michigan law — including complete elements, burdens of proof, statutes of limitations,
  available remedies, and controlling case law.
metadata:
  category: reference
  author: andrew-pigors
  version: "1.1.0"
  triggers: cause of action, elements, tort, statutory, remedies
  changelog:
    v1.1.0: |
      - Pigors COA mapping complete: 26 causes of action (13 Lane A, 10 Lane B, 1 Lane D, 2 Lane E)
      - Treble-eligible claims identified: Conversion, RICO, MCPA
      - Cycle 6 integration: 14 major claims + 7 viable motions + 6 element satisfaction rates
      - Element satisfaction: MCR 2.313(A) Motion to Compel at 95.3% (strongest)
      - UCCJEA Emergency Jurisdiction (MCL 722.1203) at 87.1% — NEW claim discovered
      - Discovery Violations (MCR 2.313) at 83.7% — NEW claim discovered
      - Objective Bias Standard (MCR 2.003(C)(2)) at 36.4% but 203 supporting facts
      - Best Interest: 9/12 factors favor Father (75%)
---
# litigation-cause-of-action-library

> **Category:** reference
> **Tier:** 2
> **Jurisdiction:** Michigan — 14th Judicial Circuit, Muskegon County
> **Context:** Pigors v Watson, pro se litigation

## Description

Use when you need to identify, look up, or compare causes of action available under Michigan law — including complete elements, burdens of proof, statutes of limitations, available remedies, and controlling case law.

## Triggers

- User asks "what can I sue for" or "what claims do I have"
- User needs elements of a specific cause of action (tort, statutory, constitutional, federal)
- User must compare remedies across multiple potential claims
- User needs statute of limitations for a Michigan cause of action
- User is evaluating whether facts support a particular legal theory
- User needs burden of proof standard for a specific claim

## Classification Schema

All causes of action are organized into four top-level categories:

| Category | Subcategories | Reference File |
|----------|--------------|----------------|
| **Tort Claims** | Intentional torts, negligence torts, dignitary torts, property torts, economic torts | `references/tort-elements.md` |
| **Statutory Claims** | Consumer protection, housing, civil rights, tenant rights | `references/statutory-elements.md` |
| **Constitutional Claims** | 42 USC § 1983, due process, equal protection | `references/statutory-elements.md` (federal section) |
| **Remedies** | Compensatory, punitive, injunctive, declaratory, treble, attorney fees | `references/remedies-matrix.md` |

## Search Protocol

When the user presents facts or asks about potential claims:

### Step 1 — Identify Category
Determine whether the conduct implicates tort, statutory, constitutional, or multiple categories.

### Step 2 — Pull Elements
For each candidate cause of action, retrieve ALL elements from the corresponding reference file. Never state elements from memory — always cite the reference.

### Step 3 — Check SOL
Verify the statute of limitations for each candidate claim. Cross-reference the filing date against the date of the last actionable event.

### Step 4 — Match Remedies
Consult `references/remedies-matrix.md` to identify every available remedy for each viable claim. Flag treble damages, attorney fee provisions, and injunctive relief availability.

### Step 5 — Present Comparison Table
Output a comparison table for the user:

```
| Cause of Action | Elements Met | SOL Status | Top Remedy | Filing Priority |
|-----------------|-------------|------------|------------|-----------------|
| Fraud           | 6/6         | Within     | Treble     | HIGH            |
| MCPA Violation  | 3/3         | Within     | Treble     | HIGH            |
| Negligence      | 4/4         | Within     | Compensatory | MEDIUM        |
```

## Element Verification Rules

1. **Every element must be independently supported** — do not assume an element is met because related elements are met
2. **Quote the element verbatim** from the reference file before analyzing whether facts satisfy it
3. **Distinguish "clearly met" from "arguable"** — mark each element as STRONG, ARGUABLE, or WEAK
4. **Note affirmative defenses** that could defeat each element

## Burden of Proof Standards (Michigan)

| Standard | Applies To | Description |
|----------|-----------|-------------|
| Preponderance of the evidence | Most civil claims | More likely than not (>50%) |
| Clear and convincing evidence | Fraud, reformation, punitive damages | Highly probable, firm belief |
| Beyond reasonable doubt | Criminal contempt only | Near certainty |

## Statute of Limitations Quick Reference

| Claim Type | SOL Period | Authority |
|-----------|-----------|-----------|
| Fraud | 6 years from discovery | MCL 600.5813; MCL 600.5855 |
| Negligence | 3 years | MCL 600.5805(10) |
| Contract (written) | 6 years | MCL 600.5807(8) |
| Contract (oral) | 6 years | MCL 600.5807(8) |
| IIED | 3 years | MCL 600.5805(2) |
| Consumer protection (MCPA) | 6 years | MCL 445.911(7) |
| Habitability | 6 years (contract theory) | MCL 600.5807(8) |
| Section 1983 | 3 years (borrowed MI personal injury) | MCL 600.5805(2); Owens v Okure |
| Property damage | 3 years | MCL 600.5805(2) |
| Conversion | 3 years | MCL 600.5805(2) |
| Malicious prosecution | 3 years | MCL 600.5805(2) |

## Discovery Rule

Michigan applies the discovery rule to fraud and certain concealment-based claims. The SOL begins when the plaintiff discovered or should have discovered the claim. MCL 600.5855. The plaintiff must show:
1. Defendant concealed the cause of action OR
2. Plaintiff could not have reasonably discovered it despite due diligence

## Cross-References

- **Skill 23** (litigation-complaint-drafter): Once claims are identified, draft the complaint
- **Skill 24** (litigation-claim-researcher): For systematic fact-to-claim mapping
- **Skill 6** (litigation-sanctions-engine): For sanctions-eligible misconduct

## Quality Gates

Before presenting any cause of action analysis:
- [ ] All elements quoted verbatim from reference file
- [ ] SOL verified against actual dates
- [ ] Remedies pulled from remedies-matrix.md
- [ ] Burden of proof identified
- [ ] At least one controlling Michigan case cited per claim
- [ ] Affirmative defenses noted

## Related Skills

- [litigation-claim-researcher](skill://litigation-claim-researcher) — Maps facts to viable claims
- [litigation-complaint-drafter](skill://litigation-complaint-drafter) — Drafts verified complaints per MCR


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
| Custody Modification | 65/100 | A,B,D,E,F | Verified |
| Emergency Custody | 55/100 | A,B,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,B,D,E,F | Verified |
| Summary Disposition (C10) | 75/100 | A,B,D,E,F | Verified |
| Summary Disposition (C8) | 70/100 | A,B,D,E,F | Verified |
| Contempt | 70/100 | A,B,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,B,D,E,F | Verified |
| Appeal Brief | 70/100 | A,B,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,B,D,E,F | Verified |
| Default Judgment | 60/100 | A,B,D,E,F | Verified |
| TRO Application | 60/100 | A,B,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,B,D,E,F | Verified |

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
