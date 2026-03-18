---
name: litigation-fee-petition-engine
description: >-
  Use when preparing attorney fee petitions, calculating lodestar amounts,
  analyzing fee-shifting statutes, preparing cost bills, calculating
  pro se litigant fee recovery, or analyzing fee entitlement under
  MCR 2.403(O), MCR 2.625, MCL 600.2405, or 42 USC §1988.
metadata:
  category: financial
  author: andrew-pigors
  version: "1.0.0"
  triggers: >-
    attorney fees, fee petition, lodestar, fee shifting, cost bill,
    MCR 2.403(O), MCR 2.625, MCL 600.2405, 42 USC 1988, taxable costs,
    pro se fees, case evaluation, sanctions, fee recovery,
    prevailing party, reasonable fees, hourly rate
---

# litigation-fee-petition-engine

> **Tier:** 2 — Financial Specialist
> **Category:** financial
> **Version:** 1.0.0
> **Lane:** ALL (A through F)

## Description

Attorney fee petition and cost recovery specialist for Michigan and
federal litigation. Performs lodestar calculations (reasonable hours ×
reasonable rate), analyzes fee-shifting statute applicability, prepares
detailed cost bills, and uniquely addresses pro se litigant fee recovery
analysis — a critical issue for Andrew James Pigors who litigates
without counsel.

**Case Context:**

| Field | Value |
|-------|-------|
| Plaintiff | Andrew James Pigors (Pro Se) |
| Defendant | Emily A. Watson |
| Child | L.D.W. per MCR 8.119(H) — MALE |
| Judge | Hon. Jenny L. McNeill — 14th Circuit Court |
| Case Nos. | 2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, COA 366810 |
| Lanes | ALL |

## Triggers

- User preparing fee petition after favorable ruling
- User calculating lodestar for fee application
- User analyzing fee-shifting statute applicability
- User preparing cost bill per MCR 2.625
- User evaluating pro se fee recovery options
- User responding to case evaluation and MCR 2.403(O) sanctions risk
- User seeking sanctions-based fee recovery under MCR 2.313

## Michigan Rules — Fee Recovery

### MCR 2.403(O) — Case Evaluation Sanctions

If a party rejects case evaluation and the verdict is more favorable to
the other party than the case evaluation:

- The rejecting party must pay the other party's **actual costs** from
  the date case evaluation was rejected
- "Actual costs" includes reasonable attorney fees (but see pro se issue)
- Does NOT include filing fees or discovery costs before rejection

### MCR 2.625 — Taxable Costs

**(A) Right to Costs:**
- Prevailing party is entitled to taxable costs unless the court orders
  otherwise

**(B) Taxable Items Include:**
- Filing fees
- Service fees
- Witness fees ($12/day + mileage at IRS rate)
- Deposition transcript costs
- Copy costs (reasonable)
- Mediation fees
- Expert witness fees (if court-ordered)

**(C) Bill of Costs:**
- Must be filed within 28 days of entry of judgment
- Must be verified by affidavit
- Must itemize each cost

### MCL 600.2405 — Interest on Judgments

Interest accrues from the date of filing the complaint at the statutory
rate. Calculated on the judgment amount.

### 42 USC § 1988 — Federal Fee Shifting (§ 1983 Claims)

**(b) Attorney's fees:**
- Court may allow the prevailing party in a § 1983 action reasonable
  attorney's fees as part of the costs
- Pro se litigants generally CANNOT recover attorney's fees under § 1988
  (*Kay v Ehrler*, 499 U.S. 432 (1991))
- BUT may recover costs and expert fees

## Lodestar Calculation Method

### Step 1: Reasonable Hours

| Task Category | Description | Time Tracking Method |
|--------------|-------------|---------------------|
| Legal Research | Statute, case law, rules research | Contemporaneous logs |
| Drafting | Motions, briefs, discovery | Per-document time |
| Court Appearances | Hearings, conferences | Court records |
| Discovery | Propounding, responding, conferring | Per-request time |
| Case Management | Filing, service, organization | Aggregate |
| Trial Preparation | Exhibits, witnesses, instructions | Per-activity |

### Step 2: Reasonable Rate

Michigan factors for determining reasonable hourly rate:

1. Professional standing and experience of the attorney
2. Skill, time, and labor involved
3. Difficulty of the case
4. Fee customarily charged in the locality
5. Amount in question and results obtained
6. Time limitations imposed
7. Professional relationship with the client
8. Experience and ability of the attorney

**Pro Se Adjustment:** Under Michigan law, pro se litigants generally
cannot recover "attorney fees" because they have no attorney. However:
- *Pirgu v United Servs Auto Ass'n*, 499 Mich 269 (2016) — Pro se
  litigants may recover case evaluation sanctions under MCR 2.403(O)
  only if they are licensed attorneys
- Non-attorney pro se litigants: focus on **cost recovery**, not fees

### Step 3: Lodestar Adjustments

| Factor | Adjustment | Basis |
|--------|-----------|-------|
| Excellent result | Up to 2× multiplier | *Smith v Khouri*, 481 Mich 519 (2008) |
| Partial success | Reduce proportionally | *Hensley v Eckerhart*, 461 US 424 (1983) |
| Delay in payment | Enhance for inflation | Johnson factors |
| Contingency risk | May enhance | Rare in Michigan |

## Patterns

### Pattern 1: Cost Bill Preparation (MCR 2.625)

**Context:** Plaintiff prevailed and needs to recover costs.

**Steps:**
1. Inventory all litigation expenses since filing
2. Categorize by MCR 2.625(B) taxable items
3. Gather receipts and documentation for each item
4. Prepare itemized cost bill
5. Prepare supporting affidavit
6. File within 28 days of judgment entry

**Michigan basis:** MCR 2.625

```python
from legal_ai.fee_petition_engine import FeePetitionEngine

fpe = FeePetitionEngine()
cost_bill = fpe.prepare_cost_bill(
    filing_fees=[20.00, 20.00, 375.00],
    service_costs=[7.50, 7.50, 7.50],
    copy_costs=45.00,
    witness_fees=[24.00],
    deposition_costs=[350.00],
)
total = fpe.calculate_total(cost_bill)
```

### Pattern 2: Case Evaluation Sanctions Analysis

**Context:** Opposing party rejected case evaluation; verdict exceeds evaluation.

**Steps:**
1. Confirm case evaluation amount and rejection date
2. Calculate actual costs incurred since rejection date
3. Itemize by category: attorney fees (if applicable), filing fees,
   expert fees, deposition costs, etc.
4. Apply MCR 2.403(O) framework
5. File motion for case evaluation sanctions with supporting documentation

**Michigan basis:** MCR 2.403(O), *Smith v Khouri*, 481 Mich 519 (2008)

### Pattern 3: Pro Se Cost Recovery Strategy

**Context:** Pro se litigant seeking maximum cost recovery.

**Steps:**
1. Accept that attorney fees are generally not recoverable pro se
2. Focus on taxable costs under MCR 2.625
3. Document ALL out-of-pocket expenses meticulously
4. Include filing fees, service costs, copies, transcripts
5. If § 1983 claim: seek expert fees and non-attorney costs
6. If sanctions: seek expenses caused by opposing party's misconduct

**Michigan basis:** MCR 2.625, *Pirgu*, 499 Mich 269 (2016)

### Pattern 4: Sanctions-Based Fee Recovery

**Context:** Opposing party engaged in sanctionable conduct.

**Steps:**
1. Document the sanctionable conduct (MCR 2.313, MCR 2.114)
2. Calculate expenses caused by the conduct
3. Include time spent on motion, travel, copies
4. File sanctions motion with expense documentation
5. Request specific dollar amount with itemization

**Michigan basis:** MCR 2.313(B)(2), MCR 2.114(E)

## Anti-Patterns

### Anti-Pattern 1: Claiming Attorney Fees as Pro Se Non-Attorney

❌ Seeking "attorney fees" when litigating pro se without a law license.
**Why it fails:** *Kay v Ehrler*, 499 U.S. 432 (1991) — pro se non-attorney
litigants cannot recover attorney fees under fee-shifting statutes.
Michigan follows this rule: *Pirgu v United Servs Auto Ass'n*, 499 Mich 269.
**Fix:** Focus exclusively on taxable costs (MCR 2.625) and out-of-pocket
expenses. Never label time spent as "attorney fees."

### Anti-Pattern 2: Filing Cost Bill Late

❌ Missing the 28-day deadline after judgment for cost bill filing.
**Why it fails:** MCR 2.625(F) imposes a strict 28-day deadline. Late
filings are barred.
**Fix:** Calendar the deadline immediately upon judgment entry. Prepare
the cost bill in advance of favorable rulings.

### Anti-Pattern 3: Failing to Document Expenses Contemporaneously

❌ Reconstructing expenses from memory months after incurring them.
**Why it fails:** Courts scrutinize fee petitions for contemporaneous
documentation. Reconstructed records are given less weight.
**Fix:** Maintain a running expense log from day one of litigation.
Save all receipts. Record time daily.

## Cost Tracking Template

| Date | Category | Description | Amount | Receipt |
|------|----------|-------------|--------|---------|
| YYYY-MM-DD | Filing fee | Motion to Compel | $20.00 | ✓ |
| YYYY-MM-DD | Service | Certified mail to Watson | $7.50 | ✓ |
| YYYY-MM-DD | Copies | Trial exhibits (100 pages) | $25.00 | ✓ |
| YYYY-MM-DD | Transcript | Hearing 2024-11-15 | $150.00 | ✓ |

## Integration Points

### Upstream Skills
- `litigation-case-strategy-architect` — Strategic decisions on cost exposure
- `litigation-sanctions-engine` — Sanctions as fee recovery mechanism
- `litigation-settlement-analyzer` — Settlement value including fee recovery

### Downstream Skills
- `litigation-filing-architect` — Filing the cost bill / fee petition
- `litigation-brief-writer` — Brief supporting fee petition
- `litigation-record-builder` — Expense documentation organization


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
| D (PPO (Protection Orders)) | A | PPO proceedings → false allegation pattern (factor j) |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
| E (Judicial Misconduct (JTC)) | F | Misconduct findings → appellate arguments |

### OMEGA Pipeline Phase Mapping
```
This skill operates across these pipeline phases:
  Ω-3 Evidence Harvest → Ω-5 Claim Mapping → Ω-6 Contradiction Detection
  Ω-9 Gap Analysis → Ω-11 Risk Assessment → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| PPO Modification/Termination | 60/100 | D,E,F | Verified |
| Judicial Disqualification | 75/100 | D,E,F | Verified |
| Appeal Brief | 70/100 | D,E,F | Verified |
| Leave Application (MSC) | 80/100 | D,E,F | Verified |
| JTC Formal Complaint | 75/100 | D,E,F | Verified |

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
