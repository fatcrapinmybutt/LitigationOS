---
name: litigation-child-support-analyzer
description: >-
  Use when calculating Michigan child support under the MCSF, analyzing income
  for support purposes, preparing support modification motions under MCL 552.517,
  computing arrearage, preparing income withholding orders per MCL 552.607,
  or addressing deviation from the formula under MCL 552.605(2).
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: >-
    child support, MCSF, Michigan Child Support Formula, MCL 552.605,
    income imputation, support modification, MCL 552.517, arrearage,
    income withholding, MCL 552.607, deviation, medical support,
    MCL 552.601, overnights
---

# litigation-child-support-analyzer

> **Tier:** 2 — Discipline Specialist
> **Category:** discipline
> **Version:** 1.0.0
> **Lane:** A (Custody — 2024-001507-DC)

## Description

Child Support Calculation and Modification Specialist for the Pigors v. Watson
litigation. Implements the Michigan Child Support Formula (MCSF) calculation
methodology, analyzes income verification and imputation, supports deviation
arguments under MCL 552.605(2), computes arrearage, and prepares income
withholding orders. Integrates with custody analysis for overnights-based
support calculations.

**Case Context:**

| Field | Value |
|-------|-------|
| Plaintiff | Andrew James Pigors (Pro Se) |
| Defendant | Emily A. Watson |
| Child | L.D.W. per MCR 8.119(H) — MALE |
| Judge | Hon. Jenny L. McNeill — 14th Circuit Court |
| Case No. | 2024-001507-DC |
| Lane | A (Custody) |
| FOC | Muskegon County Friend of the Court |

## Triggers

- User needs child support calculation under MCSF
- User preparing support modification motion
- User disputing income figures or imputation
- User calculating arrearage or overpayment
- User needs income withholding order
- User arguing for deviation from formula amount
- User addressing medical support obligations
- User responding to FOC support recommendation

## Michigan Child Support Formula (MCSF) Framework

### Overview

The MCSF is the mandatory starting point for all child support calculations
in Michigan. The court MUST apply the formula unless deviation is justified
under MCL 552.605(2).

### Key Formula Components

| Component | Description | Source |
|-----------|-------------|--------|
| **Net income** | Gross income minus allowable deductions | MCSF § 2.01 |
| **Overnights** | Number of overnights per parent per year | Parenting time order |
| **Children** | Number of children of this relationship | Case record |
| **Other children** | Children of other relationships | Disclosure |
| **Child care costs** | Work-related child care | Receipts/estimates |
| **Health care costs** | Insurance premiums for child | Insurance documentation |
| **Ordinary medical** | Annual ordinary medical ($403/child 2024) | MCSF supplement |

### Income Determination (MCSF § 2.01)

#### Gross Income Includes:

| Source | Description |
|--------|-------------|
| Wages/salary | All employment compensation |
| Overtime | Regular or predictable overtime |
| Commissions | Sales or performance bonuses |
| Self-employment | Net business income |
| Rental income | Net rental property income |
| Interest/dividends | Investment income |
| Pension/retirement | Retirement income received |
| Social Security | Disability or retirement benefits |
| Workers' compensation | WC benefits received |
| Unemployment | Unemployment benefits |
| Alimony received | From any source |
| Trust income | Distributions from trusts |
| Annuities | Annuity payments |
| Capital gains | Recurring capital gains |

#### Allowable Deductions:

| Deduction | Description |
|-----------|-------------|
| Federal/state/local taxes | Actual or estimated |
| FICA (Social Security + Medicare) | 7.65% employee share |
| Mandatory retirement contributions | Employer-required only |
| Union dues | If mandatory |
| Prior child support | For other children (actual paid) |
| Alimony paid | Court-ordered alimony to others |
| Health insurance (self) | Employee share for self only |

### Income Imputation (MCSF § 2.01(G))

When a parent is voluntarily unemployed or underemployed, income may be
imputed based on:

| Factor | Analysis |
|--------|----------|
| **Employment history** | Prior jobs, earnings trajectory |
| **Education/skills** | Degrees, certifications, training |
| **Local job market** | Available positions, prevailing wages |
| **Physical/mental capacity** | Health limitations |
| **Child care responsibilities** | Custodial parent's availability |
| **Efforts to find employment** | Job search documentation |

> ⚠️ **CRITICAL**: Imputation must be based on real labor market data,
> not aspirational earning capacity. Request Bureau of Labor Statistics
> or Michigan DTMB data to support or challenge imputation.

### Overnights Calculation

```
Total annual overnights per parent = 365 (or 366 in leap year)

Parent A overnights + Parent B overnights = 365

MCSF overnight threshold for offset:
  - If non-custodial parent has < 128 overnights: Standard formula
  - If non-custodial parent has 128+ overnights: Offset formula applies
  - 128 overnights ≈ 35% parenting time

Offset formula significantly reduces support obligation because both
parents bear direct costs during their parenting time.
```

### Support Calculation Steps

1. **Determine each parent's net income** (gross minus deductions)
2. **Determine total net income** (Parent A + Parent B)
3. **Look up base support obligation** from MCSF schedule (income × children)
4. **Determine each parent's percentage** (individual income ÷ total income)
5. **Apply overnight offset** (if 128+ overnights with non-custodial parent)
6. **Add child care costs** (prorated by income percentage)
7. **Add health care costs** (prorated by income percentage)
8. **Calculate final support amount** per month

### MCSF 2021 Quick Reference Table (1 child)

| Combined Monthly Net Income | Base Support (1 child) |
|----------------------------|----------------------|
| $1,000 | $218 |
| $2,000 | $393 |
| $3,000 | $549 |
| $4,000 | $690 |
| $5,000 | $815 |
| $6,000 | $921 |
| $8,000 | $1,097 |
| $10,000 | $1,237 |

> Note: These are approximations from the 2021 MCSF schedule.
> Always use the current published MCSF schedule for actual calculations.

## Support Modification (MCL 552.517)

### Grounds for Modification

| Ground | Standard | Evidence |
|--------|----------|---------|
| **Change in income** | Substantial and continuing | Pay stubs, tax returns, W-2s |
| **Change in overnights** | Actual parenting time differs from order | Calendar documentation |
| **Change in child care** | Costs increased or decreased substantially | Receipts, provider statements |
| **Change in health insurance** | Cost change or availability change | Insurance documents |
| **Child's needs changed** | Special needs, medical, educational | Medical records, school records |
| **Emancipation** | Child reaches 18 (or 19.5 if in school) | Birth certificate, school records |

### Modification Threshold

The MCSF provides that a modification is appropriate when the recalculated
amount differs from the current order by **10% or more** (MCL 552.517(1)(a))
OR **$50 or more per month** — whichever is greater.

### Motion to Modify Checklist

- [ ] Calculate current support under MCSF with current income
- [ ] Compare to existing order — verify 10% or $50 threshold met
- [ ] Gather income documentation (both parties)
- [ ] Document change in circumstances
- [ ] File motion on SCAO form FOC 50
- [ ] Serve opposing party
- [ ] Serve FOC office
- [ ] File proof of service

## Arrearage Calculation

### Computation Method

```
For each month in arrears:
  Amount owed (per order) - Amount paid = Monthly arrearage
  
Total arrearage = Sum of all monthly arrearages

Interest on arrearage:
  MCL 552.603(2): Surcharge of up to 1% per month on total arrearage
  (Discretionary, not automatic)

Documentation required:
  - Court order specifying support amount
  - Payment records (FOC records, bank statements)
  - Date-by-date calculation spreadsheet
```

### FOC Enforcement Actions (MCL 552.631-652)

| Action | Authority | Trigger |
|--------|-----------|---------|
| Income withholding | MCL 552.607 | Default or court order |
| License suspension | MCL 552.628 | 2+ months arrearage |
| Contempt | MCL 552.636 | Willful failure to pay |
| Tax refund intercept | MCL 552.625f | Arrearage threshold |
| Credit reporting | MCL 552.637 | Reporting to credit agencies |
| Passport denial | 42 USC § 652(k) | $2,500+ arrearage (federal) |

## Deviation from Formula (MCL 552.605(2))

### Requirements for Deviation

The court may deviate from the MCSF amount only if:

1. Application of the formula would be **unjust or inappropriate**
2. The court states **specific reasons** for deviation on the record
3. The deviation serves the **child's best interests**

### Accepted Deviation Factors

| Factor | Direction | Justification |
|--------|-----------|---------------|
| Special needs child | Increase | Additional medical, educational, or therapeutic costs |
| Shared physical custody | Decrease | Both parents bear significant direct costs |
| Extraordinary income | Decrease | Formula amount exceeds child's reasonable needs |
| Low income | Decrease | Payer's income below self-support reserve |
| Third-party income | Varies | New spouse's contribution to household |
| Child's own income | Decrease | Minor child has employment or trust income |
| Tax consequences | Varies | Specific tax impact of support arrangement |

## Income Withholding Order (MCL 552.607)

### Order Components

| Element | Detail |
|---------|--------|
| Current support | Monthly amount per court order |
| Arrearage payment | Additional monthly amount toward arrearage |
| Health insurance | Premium withholding for child's coverage |
| Processing fee | Employer may deduct per MCL 552.607(4) |
| Maximum withholding | Cannot exceed 50% of disposable income (55% if 12+ weeks arrears) |

### SCAO Forms

| Form | Title | Use |
|------|-------|-----|
| FOC 50 | Motion Regarding Support | Modification motion |
| FOC 51 | Response to Motion Regarding Support | Opposition |
| FOC 10 | Uniform Child Support Order | Support order |
| FOC 10a | Uniform Support Order — Addendum | Additional provisions |
| FOC 23 | Verified Statement of Payer | Income disclosure |

## Database Schema

```sql
CREATE TABLE IF NOT EXISTS child_support_calculations (
    calc_id            TEXT PRIMARY KEY,
    case_number        TEXT DEFAULT '2024-001507-DC',
    calc_date          TEXT NOT NULL,
    parent_a_name      TEXT DEFAULT 'Andrew James Pigors',
    parent_b_name      TEXT DEFAULT 'Emily A. Watson',
    parent_a_net_income REAL,
    parent_b_net_income REAL,
    overnights_a       INTEGER,
    overnights_b       INTEGER,
    child_care_monthly REAL DEFAULT 0,
    health_ins_monthly REAL DEFAULT 0,
    formula_amount     REAL,
    deviation_amount   REAL,
    deviation_reason   TEXT,
    arrearage_total    REAL DEFAULT 0,
    effective_date     TEXT,
    lane               TEXT DEFAULT 'A',
    created_at         TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_support_case
    ON child_support_calculations(case_number, calc_date);
```

## Integration

### Companion Skills

- [litigation-custody-specialist](skill://litigation-custody-specialist) — Overnights determination
- [litigation-foc-challenge-engine](skill://litigation-foc-challenge-engine) — FOC recommendation objection
- [litigation-filing-architect](skill://litigation-filing-architect) — Motion filing
- [litigation-harm-quantifier](skill://litigation-harm-quantifier) — Financial harm from support errors
- [litigation-evidence-harvester](skill://litigation-evidence-harvester) — Income evidence gathering

### Companion Agents

- `court-order-tracker` — Track support order modifications
- `filing-countdown` — Support modification deadlines

## Fabrication Warnings

- **DO NOT** fabricate income figures, MCSF schedule amounts, or arrearage calculations.
- **DO NOT** invent statutory provisions or misstate MCL requirements.
- **DO NOT** use "Emily Ann" or "Emily M." — defendant is Emily A. Watson.
- **ALWAYS** use L.D.W. for the child per MCR 8.119(H).
- **ALWAYS** spell Judge McNeill with TWO L's.
- **ALWAYS** reference the current MCSF schedule (2021 edition or later).
- **ALWAYS** verify interest rates and thresholds against current law.

## Output Format

```markdown
## Child Support Analysis — Case [Number]

### Current Order: $[amount]/month | Effective: [Date]

### MCSF Calculation
| Component | Parent A (Pigors) | Parent B (Watson) |
|-----------|-------------------|-------------------|
| Gross income | $[amount] | $[amount] |
| Net income | $[amount] | $[amount] |
| Income % | [X]% | [Y]% |
| Overnights | [N] | [N] |

### Formula Amount: $[amount]/month
### Deviation: [None / $amount — reason]

### Arrearage: $[amount] as of [date]

### Recommended Actions
1. [Action with legal basis]
```


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

### Governing Authority (Verified)
**MCR:** MCR 3.206, MCR 3.211
**MCL:** MCL 552.517, MCL 552.519, MCL 552.605, MCL 552.517e
**Binding Cases:**
- *Ghidotti v Barber, 459 Mich 189*
- *Peterson v Peterson, 272 Mich App 511*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| D | 6,462 | 2023-5907-PP | 14th Circuit |

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
| Custody Modification | 65/100 | A,D | Verified |
| Emergency Custody | 55/100 | A,D | Verified |
| PPO Modification/Termination | 60/100 | A,D | Verified |
| Contempt | 70/100 | A,D | Verified |

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

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
