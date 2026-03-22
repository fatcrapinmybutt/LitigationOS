# Ω8 Financial & Damages Brain — OMEGA-INFINITY Reference
> Module 8 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose

Centralize all financial intelligence — damages quantification, litigation cost tracking, child support analysis, fee waiver eligibility, and per-lane damages documentation — into a single brain that feeds Modules M4 (Filing Factory), M5 (Strategic Command), and M6 (Domain Specialists).

---

## 1. Damages Database

### 1.1 Primary Table: `damages_calculation`

```sql
PRAGMA table_info(damages_calculation);
-- id (INTEGER), lane (TEXT), category (TEXT), description (TEXT),
-- conservative_amount (REAL), aggressive_amount (REAL), basis (TEXT),
-- evidence_source (TEXT), is_summary (INTEGER), overlap_note (TEXT),
-- created_at (TIMESTAMP)
```

**Live count:** `SELECT COUNT(*) FROM damages_calculation;`

**Full damages inventory:**

```sql
SELECT id, lane, category, description,
       conservative_amount, aggressive_amount, basis, evidence_source
FROM damages_calculation
WHERE is_summary = 0
ORDER BY lane, category;
```

**Summary rows (aggregated per lane):**

```sql
SELECT lane, category, conservative_amount, aggressive_amount, description
FROM damages_calculation
WHERE is_summary = 1
ORDER BY lane;
```

### 1.2 Damages by Lane — Overview Query

```sql
SELECT lane, COUNT(*) as line_items,
       SUM(conservative_amount) as conservative_total,
       SUM(aggressive_amount) as aggressive_total
FROM damages_calculation
WHERE is_summary = 0
GROUP BY lane
ORDER BY lane;
```

---

## 2. Lane-by-Lane Damages Categories

### 2.1 Lane A — Custody (Watson / Parenting Time)

**Case Numbers:** 2024-001507-DC, 2023-5907-PP

| Category | Description | Basis | Evidence Path |
|----------|-------------|-------|--------------|
| **Custody deprivation (per-day)** | Compensatory damages for each day parenting time denied | *Weller v. Dept of Social Services*; *Malik v. Arapahoe County*; §1983 range $100-$500/day | `alienation_timeline WHERE withholding_episode = 1`; compute `MAX(cumulative_days_withheld)` |
| **Lost employment** | Income lost from 4 jobs due to litigation, incarceration, court appearances | MI minimum wage / manufacturing median; pro-rated for separation period | `evidence_quotes WHERE category = 'financial' AND quote_text LIKE '%employ%'` |
| **Lost housing** | 2 homes lost during litigation; security deposits, moving costs, temporary housing | Actual costs per Andrew's records | `evidence_quotes WHERE category = 'housing'` |
| **Emotional distress** | Severe emotional distress from parental alienation, incarceration, false accusations | General tort damages; severity of conduct | `false_allegations` (7 debunked); `alienation_timeline` |
| **Attorney/legal fees** | Pro se litigation costs (filing fees, copies, service, mileage, research) | Actual costs tracked | Compute from filing fee schedule + mileage log |

**Lane A damages query:**

```sql
SELECT category, description, conservative_amount, aggressive_amount, basis, evidence_source
FROM damages_calculation
WHERE lane = 'A' AND is_summary = 0
ORDER BY conservative_amount DESC;
```

**Parenting time deprivation calculation:**

```sql
-- Get total days withheld
SELECT MAX(cumulative_days_withheld) as total_days_withheld
FROM alienation_timeline;

-- Per-day calculation: multiply by per-day rate
-- Conservative: $100/day → total_days × 100
-- Aggressive: $500/day → total_days × 500
-- The DB stores pre-calculated amounts — always verify against live alienation_timeline
```

### 2.2 Lane B — Housing (Shady Oaks / Property)

**Case Number:** 2025-002760-CZ

| Category | Description | Basis | Evidence Path |
|----------|-------------|-------|--------------|
| **Property loss** | Personal property removed from Shady Oaks residence | Replacement value of items | `evidence_quotes WHERE category = 'housing' AND quote_text LIKE '%property%'` |
| **Moving costs** | Forced relocation expenses | Actual receipts | Andrew's records |
| **Utility shutoff damages** | Water shutoff, sewage issues at Shady Oaks | Habitability / health code violations | `evidence_quotes WHERE quote_text LIKE '%water%' OR quote_text LIKE '%sewage%'` |
| **Property removal/destruction** | Belongings removed or destroyed during lockout | Item inventory with fair market values | `evidence_quotes WHERE quote_text LIKE '%Shady Oaks%'` |
| **Title interference** | Interference with property ownership/title transfer | Lost equity, legal costs to clear title | `case_timeline WHERE lane = 'B'` |
| **Sale interference** | Obstruction of legitimate property sale | Lost sale proceeds, carrying costs | Housing evidence cluster |

**Lane B damages query:**

```sql
SELECT category, description, conservative_amount, aggressive_amount, basis, evidence_source
FROM damages_calculation
WHERE lane = 'B' AND is_summary = 0
ORDER BY conservative_amount DESC;
```

### 2.3 Lane C — Convergence / §1983 Civil Rights

| Category | Description | Basis | Evidence Path |
|----------|-------------|-------|--------------|
| **Compensatory damages (§1983)** | Constitutional deprivation — due process, parental rights | 42 USC §1983; *Monroe v. Pape*; fundamental liberty interest in parental rights | `judicial_violations` (full set); due process violations |
| **Punitive damages (§1983)** | Punitive for willful/malicious deprivation | *Smith v. Wade*, 461 U.S. 30 (1983) — reckless/callous disregard | High-severity violations: `judicial_violations WHERE severity >= 7` |
| **Attorney fees (§1988)** | Prevailing party attorney fees in civil rights cases | 42 USC §1988 — mandatory for prevailing §1983 plaintiffs | Computed at hourly rate × hours (even pro se: *Kay v. Ehrler* limitations) |
| **Injunctive relief** | Prospective relief against ongoing violations | *Ex parte Young* doctrine for state officers | Pattern evidence from `judicial_violations` |

**CRITICAL — Judicial Immunity Analysis:**

Judges have absolute immunity from §1983 damages for acts performed in their judicial capacity with jurisdiction. Exceptions:

- Acts taken in clear absence of all jurisdiction
- Non-judicial acts (administrative, personal)
- Injunctive relief is available despite immunity (*Pulliam v. Allen*, narrowed by statute)

Query violations that may fall outside immunity:

```sql
SELECT id, violation_type, description, date_occurred, mcr_rule
FROM judicial_violations
WHERE violation_type IN ('ex_parte', 'due_process')
  AND (description LIKE '%without jurisdiction%'
       OR description LIKE '%outside%'
       OR description LIKE '%administrative%')
ORDER BY date_occurred ASC;
```

**Lane C damages query:**

```sql
SELECT category, description, conservative_amount, aggressive_amount, basis, evidence_source
FROM damages_calculation
WHERE lane = 'C' AND is_summary = 0
ORDER BY conservative_amount DESC;
```

### 2.4 Lane D — PPO / Protection Orders

| Category | Description | Basis | Evidence Path |
|----------|-------------|-------|--------------|
| **PPO abuse damages** | Damages from weaponized PPO — false basis, ex parte issuance | Abuse of process; malicious prosecution elements | `false_allegations WHERE status = 'debunked'`; PPO docket entries |
| **Wrongful arrest/incarceration** | Damages from arrest and jail time based on invalid PPO | False imprisonment; §1983 if state actors involved | `case_timeline WHERE description LIKE '%arrest%' OR description LIKE '%jail%'` |
| **Lost employment (PPO-caused)** | Jobs lost due to PPO restrictions or arrest record | Lost wages for period of unemployment | Employment evidence in `evidence_quotes` |
| **Stigma damages** | Reputational harm from false accusations in PPO proceedings | Defamation per se (false criminal accusations) | `false_allegations` — allegations of sexual assault, drug use |

**Lane D damages query:**

```sql
SELECT category, description, conservative_amount, aggressive_amount, basis, evidence_source
FROM damages_calculation
WHERE lane = 'D' AND is_summary = 0
ORDER BY conservative_amount DESC;
```

### 2.5 Lane E — Judicial Misconduct / JTC

**No direct monetary damages.** JTC complaints are discipline-based, not damages-based.

| Remedy Type | Description | Mechanism |
|-------------|-------------|-----------|
| **Censure** | Public reprimand of judicial conduct | MCR 9.206(2) |
| **Suspension** | Temporary removal from bench | MCR 9.206(3) |
| **Removal** | Permanent removal from bench | MCR 9.206(4) |
| **Conditional discipline** | Requirements (training, counseling) | MCR 9.206(5) |

Financial impact of Lane E is INDIRECT — successful JTC action strengthens Lane C (§1983) and Lane F (appellate) arguments by establishing judicial misconduct as an adjudicated fact.

### 2.6 Lane F — Appellate (COA / MSC)

| Cost Category | Description | Typical Range |
|---------------|-------------|---------------|
| **Filing fees** | COA filing fee; MSC application fee | $375 COA; $375 MSC (verify current schedule) |
| **Transcript fees** | Court reporter transcript costs | $3.00-$4.50/page (verify with reporter) |
| **Brief preparation** | Copying, binding, service costs | $50-$500 per brief |
| **Record preparation** | Lower court record compilation | Variable — depends on record size |
| **Motion fees** | Various motion filing fees | $20-$50 per motion |

**Fee waiver applies** — see §4 below.

---

## 3. Child Support Analysis

### 3.1 Michigan Child Support Framework

| Authority | Subject |
|-----------|---------|
| **MCL 552.605** | Child support formula; deviation factors |
| **MCL 552.602** | Definitions (income, expenses) |
| **MCL 552.517** | Child support orders generally |
| **MCSF 2021** | Michigan Child Support Formula manual |

### 3.2 Child Support Calculation Inputs

| Input | Description | Source |
|-------|-------------|--------|
| **Father's income** | Andrew's gross income | Tax returns, pay stubs — query Andrew for current |
| **Mother's income** | Emily's gross income | Discovery request; imputed if unemployed voluntarily |
| **Overnights** | Parenting time overnights per year per parent | Court order; actual (if different from order) |
| **Healthcare costs** | Child's insurance premium, uncovered medical | Insurance records |
| **Childcare costs** | Daycare, after-school care | Receipts |
| **Other children** | Support obligations for other children | Court orders |

### 3.3 FOC Role

**Friend of the Court:** Pamela Rusco, 990 Terrace St, Muskegon, MI 49442

The FOC calculates child support recommendations. Query FOC-related evidence:

```sql
SELECT id, quote_text, source_file, category
FROM evidence_quotes
WHERE quote_text LIKE '%Rusco%' OR quote_text LIKE '%FOC%' OR quote_text LIKE '%Friend of the Court%'
ORDER BY id;
```

### 3.4 Child Support Deviation Factors (MCL 552.605(2))

Courts may deviate from the formula if application would be "unjust or inappropriate." Factors:

- Special needs of the child
- Educational expenses
- Parental assets and liabilities
- Extraordinary travel expenses for parenting time
- Whether a parent has voluntarily reduced income
- Impact of tax consequences

**Strategic note:** If Emily has voluntarily reduced income or failed to seek employment, imputation of income is appropriate under MCSF §2.01(G).

---

## 4. Fee Waiver Eligibility

### 4.1 Michigan Fee Waiver — MC 20

**Form:** MC 20 — Affidavit of Indigency and Waiver of Fees

**Eligibility criteria:**

| Ground | Description | Evidence Needed |
|--------|-------------|-----------------|
| **Public assistance** | Currently receiving public assistance (TANF, SSI, food stamps) | Agency benefit letter |
| **Income below 125% FPL** | Household income below 125% of federal poverty level | Pay stubs, tax returns, bank statements |
| **Unable to pay** | Payment would deprive necessities of life | Detailed expense affidavit |

### 4.2 Fee Waiver Query

```sql
-- Check if fee waiver evidence exists in the DB
SELECT id, quote_text, source_file, category
FROM evidence_quotes
WHERE quote_text LIKE '%fee waiver%' OR quote_text LIKE '%indigency%'
  OR quote_text LIKE '%MC 20%' OR quote_text LIKE '%waiver%'
ORDER BY id;
```

### 4.3 Fees Waived

If MC 20 is granted, the following are waived:

- Filing fees (all courts)
- Motion fees
- Jury fees
- Transcript fees (may be reduced, not always fully waived)
- Service fees (for process server)
- Appeal filing fees

**Check filing_readiness for fee waiver status:**

```sql
SELECT vehicle_name, status, readiness_score, blockers
FROM filing_readiness
WHERE vehicle_name LIKE '%fee%' OR blockers LIKE '%fee%' OR vehicle_name LIKE '%MC 20%';
```

---

## 5. Litigation Cost Tracking

### 5.1 Filing Fees by Court

| Court | Filing Type | Fee | Authority |
|-------|-----------|-----|-----------|
| **14th Circuit** | New civil case | $175 | MCL 600.8371 |
| **14th Circuit** | Motion | $20 | MCL 600.8371 |
| **14th Circuit** | Jury demand | $50-$100 | MCL 600.8371 |
| **60th District** | Civil filing | $65 | MCL 600.8371 |
| **COA** | Claim of appeal | $375 | MCL 600.8371 |
| **COA** | Application for leave | $375 | MCL 600.8371 |
| **MSC** | Application for leave | $375 | MCL 600.8371 |
| **JTC** | Complaint | $0 (no fee) | MCR 9.202 |

**Note:** Verify current fee schedules — amounts may change. Check the Michigan One Court of Justice fee schedule for current rates.

### 5.2 Service Costs

| Method | Cost | Authority |
|--------|------|-----------|
| **Personal service (process server)** | $25-$75 per service | MCR 2.103 |
| **Certified mail** | $7-$15 per service | MCR 2.105 |
| **Publication** | $50-$200 per publication | MCR 2.106 |
| **Sheriff service** | $30-$50 per service | County schedule |

### 5.3 Copy and Transcript Costs

| Item | Cost |
|------|------|
| **Court copies** | $1.00/page (certified) |
| **Regular copies** | $0.10-$0.25/page |
| **Court reporter transcript** | $3.00-$4.50/page (varies by reporter) |
| **Expedited transcript** | Up to $6.00/page |
| **Audio recording copy** | $20-$50 per hearing |

### 5.4 Mileage

| Rate | Amount | Authority |
|------|--------|-----------|
| **IRS standard mileage (2025)** | $0.70/mile (verify current year) | IRS Rev. Proc. |
| **Andrew's address** | 1977 Whitehall Road, Lot 17, North Muskegon, MI 49445 | — |
| **14th Circuit Court** | 990 Terrace St, Muskegon, MI 49442 | — |
| **Approximate round-trip** | ~10-15 miles (verify with mapping) | — |

### 5.5 Cost Tracking Query Template

No dedicated `filing_fees` or `costs` table currently exists. Track costs via:

```sql
-- Check if any cost data exists in evidence_quotes
SELECT id, quote_text, source_file, category
FROM evidence_quotes
WHERE category = 'financial'
  AND (quote_text LIKE '%fee%' OR quote_text LIKE '%cost%'
       OR quote_text LIKE '%mileage%' OR quote_text LIKE '%receipt%')
LIMIT 50;
```

**Recommendation:** Create a dedicated `litigation_costs` table if one does not exist:

```sql
CREATE TABLE IF NOT EXISTS litigation_costs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  lane TEXT,
  category TEXT NOT NULL, -- 'filing_fee', 'service', 'copies', 'mileage', 'transcript', 'other'
  description TEXT,
  amount REAL NOT NULL,
  receipt_path TEXT,
  reimbursable INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Damages Documentation Requirements

### 6.1 Per-Category Documentation

| Damages Category | Required Documentation | Michigan Authority |
|-----------------|----------------------|-------------------|
| **Lost wages** | Pay stubs, W-2s, tax returns, termination letters | MPC §§ 2920-2921 |
| **Lost property** | Inventory list, photos, appraisals, receipts | MCL 600.2919a |
| **Medical/emotional** | Medical records, therapy records, expert testimony | MCL 600.2945a |
| **Per-day custody deprivation** | Calendar of days withheld, court orders, evidence of denial | §1983 case law |
| **Moving costs** | Receipts, moving company invoices, utility deposits | Direct evidence |
| **Attorney fees (§1988)** | Time records, hourly rate justification, prevailing market rate | *Hensley v. Eckerhart* factors |
| **Punitive damages** | Evidence of willful/reckless conduct | *Smith v. Wade* standard |

### 6.2 Evidence Strength Assessment

Query evidence density supporting each damages category:

```sql
SELECT category, COUNT(*) as evidence_count
FROM evidence_quotes
WHERE category IN ('financial', 'housing', 'custody', 'custody_interference',
                   'alienation', 'ppo', 'medical')
GROUP BY category
ORDER BY evidence_count DESC;
```

### 6.3 Damages-to-Evidence Binding

For each damages line item, verify supporting evidence exists:

```sql
SELECT dc.id, dc.lane, dc.category, dc.description,
       dc.conservative_amount, dc.evidence_source
FROM damages_calculation dc
WHERE dc.is_summary = 0
ORDER BY dc.lane, dc.id;
```

Cross-reference `evidence_source` field with actual DB queries to confirm evidence is retrievable.

---

## 7. Key DB Queries — Ready to Run

### Query 1: Complete Damages Summary

```sql
SELECT lane, SUM(conservative_amount) as conservative, SUM(aggressive_amount) as aggressive,
       COUNT(*) as line_items
FROM damages_calculation
WHERE is_summary = 0
GROUP BY lane
ORDER BY lane;
```

### Query 2: Highest-Value Damages Items

```sql
SELECT lane, category, description, conservative_amount, aggressive_amount
FROM damages_calculation
WHERE is_summary = 0
ORDER BY aggressive_amount DESC
LIMIT 10;
```

### Query 3: Evidence Density per Damages Category

```sql
SELECT dc.lane, dc.category, dc.conservative_amount,
       (SELECT COUNT(*) FROM evidence_quotes eq
        WHERE eq.lane = dc.lane
          AND eq.category LIKE '%' || LOWER(SUBSTR(dc.category, 1, 5)) || '%') as supporting_evidence
FROM damages_calculation dc
WHERE dc.is_summary = 0
ORDER BY dc.lane;
```

### Query 4: Parenting Time Loss Calculation Base

```sql
SELECT
  (SELECT MAX(cumulative_days_withheld) FROM alienation_timeline) as total_days_withheld,
  (SELECT COUNT(*) FROM alienation_timeline) as total_alienation_events,
  (SELECT COUNT(*) FROM alienation_timeline WHERE withholding_episode = 1) as withholding_episodes;
```

### Query 5: Financial Evidence Inventory

```sql
SELECT category, COUNT(*) as cnt
FROM evidence_quotes
WHERE category = 'financial'
  OR (category IN ('housing', 'custody', 'ppo') AND quote_text LIKE '%cost%')
GROUP BY category
ORDER BY cnt DESC;
```

---

## 8. Cross-Wiring Points

| Target Brain | Connection | Data Flow |
|-------------|------------|-----------|
| **Ω5-adversary-brain** | Adversary actions cause damages | Each adversary pattern (PPO abuse, alienation, incarceration, property removal) maps to a damages line item |
| **Ω6-timeline-brain** | Damages require date-bounded calculation | `alienation_timeline.cumulative_days_withheld` → per-day custody deprivation; employment loss dates → lost income window |
| **Ω7-judicial-brain** | Judicial violations → §1983 damages | Due process violations in `judicial_violations` support Lane C constitutional damages (subject to immunity) |
| **Ω3-authority-brain** | Legal authority supports damages claims | §1983 case law, MCL tort statutes, child support formula citations validate each damages category |
| **Ω4-filing-brain** | Damages drive filing content | Fee petition (42 USC §1988), damages schedule (complaint attachment), child support modification (MC form) |
| **Ω1-evidence-brain** | Evidence proves damages | `evidence_quotes` filtered by financial/housing/custody categories provides exhibit binding for damages schedule |

---

## 9. Operational Directives

1. **Never hardcode damages amounts.** Always query `damages_calculation` for live numbers. The amounts change as evidence is refined.
2. **Conservative vs. aggressive is a strategic choice.** Use conservative amounts in initial filings; aggressive amounts only if evidence fully supports and the forum is favorable.
3. **Verify all ACTUAL costs with Andrew.** The DB contains estimated ranges. Actual amounts (lost wages, moving costs, deposits) require Andrew's records. Insert `[VERIFY_WITH_ANDREW]` placeholder where actual figures are needed.
4. **Overlap analysis is mandatory.** The `overlap_note` column in `damages_calculation` flags potential double-counting. Never sum lanes without checking for overlap (e.g., lost employment may appear in both Lane A and Lane D).
5. **Fee waiver first.** Before computing filing costs, check MC 20 eligibility. If fee waiver is granted, filing fees are $0.
6. **§1983 immunity gate.** Before including judicial conduct damages in any filing, run the immunity analysis (Lane C §2.3). Absolute immunity defeats most damages claims against judges — focus on injunctive relief and acts outside jurisdiction.
7. **Child support is a separate track.** Child support calculations follow the MCSF formula, not tort damages principles. Do not mix child support with damages claims.
8. **Track ALL costs.** Even small costs (copies, postage, mileage) aggregate to significant amounts over multi-year litigation. Create and maintain the `litigation_costs` table if it does not exist.
9. **Evidence density matters.** Damages categories with fewer than 10 supporting `evidence_quotes` entries are under-documented. Prioritize evidence harvesting for thin categories.
10. **Restitution vs. damages.** Criminal case restitution (Lane D) follows different rules than civil damages. MCL 780.766 governs criminal restitution orders.
