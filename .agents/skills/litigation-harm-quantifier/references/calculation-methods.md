# Calculation Methods — Damages Quantification

Detailed calculation frameworks for every damages category in Pigors v Watson. Each method includes formulas, input requirements, and Michigan-specific considerations.

## I. Economic Damages Calculations

### A. Lost Wages — Past

**Formula:**
```
Past Lost Wages = (Hourly Rate × Hours Missed) + (Lost Overtime) + (Lost Benefits Value)
```

**Inputs Required:**
1. Hourly wage or salary rate (from pay stubs, W-2, tax returns)
2. Specific days/hours missed (with reason tied to defendant's conduct)
3. Overtime rate and frequency (if applicable)
4. Benefits value (health insurance premium, retirement match, PTO accrual)

**Day-by-Day Calculation Table:**

| Date | Hours Missed | Reason | Rate | Subtotal |
|---|---|---|---|---|
| [Date] | [Hours] | Court appearance / Moving / Recovery | $[Rate] | $[Amount] |
| ... | ... | ... | ... | ... |
| **TOTAL** | | | | **$[Sum]** |

**Michigan Notes:**
- Use actual wage rate, not minimum wage (unless actual rate is lower)
- Include all forms of compensation: base pay, tips, commissions, bonuses
- For self-employed: use net business income from Schedule C or equivalent
- Document reason for each absence — must connect to defendant's conduct

### B. Lost Wages — Future / Lost Earning Capacity

**Formula:**
```
Future Lost Earnings = Annual Loss × Work Life Expectancy × Present Value Discount Factor
Present Value Factor = 1 / (1 + discount rate)^years
```

**Inputs Required:**
1. Current/projected earnings trajectory
2. Remaining work-life expectancy (Bureau of Labor Statistics tables)
3. Discount rate (typically 2–4% real rate)
4. Impact of harm on earning capacity (partial vs. total)

**Michigan Notes:**
- Expert testimony generally required for future earning capacity claims
- Court uses "reasonable certainty" standard, not mathematical precision
- Consider career advancement trajectory that was disrupted
- Precopio v Detroit, 415 Mich 457 (1982) — future damages must be reasonably certain

### C. Housing Damages — Rent Differential

**Formula:**
```
Rent Differential = (Rent Paid - Fair Market Value of Defective Unit) × Months of Occupancy
```

**Inputs Required:**
1. Monthly rent paid (lease agreement, payment records)
2. Fair market value of unit in defective condition (expert appraisal or comparable units)
3. Duration of occupancy during defective conditions
4. Percentage reduction for specific defects (habitability worksheet below)

**Habitability Reduction Worksheet:**

| Defect Category | Severity (1-5) | % Reduction | Monthly Value | Months | Subtotal |
|---|---|---|---|---|---|
| Heating/cooling failure | | 15-40% | | | |
| Plumbing issues | | 10-30% | | | |
| Electrical hazards | | 10-25% | | | |
| Structural defects | | 20-50% | | | |
| Pest infestation | | 10-30% | | | |
| Mold/moisture | | 15-40% | | | |
| Security deficiencies | | 10-25% | | | |
| Code violations | | 10-30% | | | |
| **Aggregate** | | **(Cap at 100%)** | | | **$[Total]** |

### D. Security Deposit Recovery

**Formula:**
```
Deposit Damages = (Deposit Withheld - Legitimate Deductions) × 2
                  [MCL 554.613 — double deposit for wrongful retention]
```

**Inputs Required:**
1. Original deposit amount (lease, receipt)
2. Landlord's claimed deductions (itemized statement, if any)
3. Move-in / move-out condition documentation
4. Whether landlord provided itemized list within 30 days of move-out (MCL 554.609)

**Michigan Statutory Requirements:**
- Landlord must return deposit or itemized deductions within 30 days of move-out
- Failure to provide itemized statement = forfeit right to retain any portion
- Wrongful retention entitles tenant to double the deposit
- MCL 554.613: "If the landlord fails to comply... the tenant may recover the amount of the security deposit due plus damages in an amount equal to twice the security deposit."

### E. MCPA Treble Damages

**Formula:**
```
MCPA Damages = MAX(Actual Damages × 3, $250) + Reasonable Attorney Costs
[Note: Pro se cannot recover attorney fees per Kay v Ehrler]
```

**Inputs Required:**
1. Actual damages from the unfair/deceptive practice (separate from other tort damages)
2. Evidence of knowing violation (for treble; $250 minimum is automatic)
3. Connection between deceptive practice and actual damages

## II. Non-Economic Damages Calculations

### A. Per Diem Method

**Formula:**
```
Per Diem Damages = Daily Suffering Value × Number of Affected Days
```

**How to Set Daily Value:**
1. **Wage Analogy**: "If [Plaintiff] deserves $[hourly rate] per hour for work, his suffering is worth at least $[amount] per day"
2. **Necessity Analogy**: Compare to daily cost of essentials (housing, food) — suffering is at least as valuable as physical comfort
3. **Reasonable Amount**: $50–$500 per day depending on severity

**Calculation:**

| Harm Phase | Start Date | End Date | Days | Daily Rate | Subtotal |
|---|---|---|---|---|---|
| Acute phase (worst suffering) | | | | $[High] | |
| Moderate phase | | | | $[Medium] | |
| Ongoing/chronic phase | | | | $[Lower] | |
| **TOTAL** | | | **[Days]** | | **$[Sum]** |

**Michigan Notes:**
- Per diem is a persuasion framework, not a legally mandated method
- Michigan courts allow per diem arguments to juries; no prohibition
- Must connect each day to specific, documented suffering
- More persuasive when phases show declining (but ongoing) severity

### B. Multiplier Method

**Formula:**
```
Non-Economic Damages = Economic Damages × Severity Multiplier
```

**Severity Multiplier Scale:**

| Multiplier | When Appropriate | Examples |
|---|---|---|
| 1.0–1.5× | Minor, short-duration harm; full recovery | Brief housing displacement, minor stress |
| 1.5–2.5× | Moderate harm; significant but recoverable | Months of housing defects, moderate anxiety |
| 2.5–3.5× | Serious harm; lasting effects | Prolonged custody interference, depression |
| 3.5–5.0× | Severe harm; permanent or near-permanent effects | Severe alienation, PTSD, total relationship loss |
| 5.0×+ | Catastrophic/egregious; intentional cruelty | Rarely justifiable without extreme facts |

**Michigan Notes:**
- Multipliers are guidelines, not formulas — courts do not mathematically apply them
- Higher multipliers require stronger evidence of severity and duration
- The multiplier communicates proportionality to the judge/jury

### C. Comparable Verdict Analysis

**Method:** Research Michigan verdicts in cases with similar fact patterns to establish a range.

**Search Parameters:**
1. Case type (custody interference, housing, emotional distress)
2. Jurisdiction (Michigan, preferably Western District or nearby circuits)
3. Harm severity (comparable injuries/harms)
4. Verdict year (adjust for inflation using CPI)
5. Plaintiff demographics (similar life circumstances)

**Sources:**
- Michigan Lawyers Weekly verdict reports
- Westlaw/LexisNexis jury verdict databases
- ICLE Michigan verdict summaries
- Published COA opinions discussing damages awards

### D. Hybrid Method (Recommended)

**Formula:**
```
Hybrid Non-Economic = (Per Diem + Multiplier + Comparable Verdict Average) / 3
```

Present all three methods and average them. This approach:
- Demonstrates thoroughness
- Provides a range rather than a single number
- Allows the factfinder to use the method they find most persuasive
- Survives challenge because no single speculative method controls

## III. Custody-Related Damages

### A. Lost Parenting Time Valuation

**Method 1 — Time-Based:**
```
Lost Time Value = (Days Denied) × (Daily Parenting Value)
Daily Parenting Value = [Annual income / 365] or [Set reasonable daily value]
```

**Method 2 — Relationship-Based:**
```
Relationship Harm = (Severity of Interference) × (Duration) × (Child's Age Factor)
Age Factor: Younger children = higher value (developmental impact greater)
```

**Documentation Required:**
- Court order specifying parenting time schedule
- Log of every denied/interfered visit (date, scheduled time, what happened)
- Communications showing interference (texts, emails)
- Impact on children (behavioral changes, school records, therapy notes)

### B. Alienation Damages

Emerging area of law. No settled Michigan formula. Framework:

| Component | Measurement | Evidence |
|---|---|---|
| Therapy costs (past) | Actual bills | Therapist records, invoices |
| Therapy costs (future) | Projected treatment plan | Expert recommendation |
| Lost relationship value | Per diem during alienation period | Behavioral documentation |
| Remediation costs | Reunification therapy estimate | Professional estimate |
| Child's damages (next friend) | Separate claim for child's harm | Child's therapist, school records |

## IV. Present Value Calculation

For any future damages, reduce to present value:

**Formula:**
```
Present Value = Future Amount / (1 + r)^n
Where: r = discount rate (typically 2-3% real rate)
       n = number of years until the future cost is incurred
```

**Table for Quick Reference (3% discount rate):**

| Years Out | Present Value of $1,000 |
|---|---|
| 1 | $970.87 |
| 2 | $942.60 |
| 3 | $915.14 |
| 5 | $862.61 |
| 10 | $744.09 |

## V. Damages Summary Template

Use this format in every filing requesting damages:

| # | Harm | Category | Calculation Method | Amount | Key Evidence |
|---|---|---|---|---|---|
| 1 | [Specific harm] | Economic / Non-Economic | [Method used] | $[Amount] | [Exhibit refs] |
| 2 | ... | ... | ... | ... | ... |
| | **SUBTOTAL Economic** | | | **$[Sum]** | |
| | **SUBTOTAL Non-Economic** | | | **$[Sum]** | |
| | **Statutory Multipliers** | | | **$[Sum]** | |
| | **Punitive (if applicable)** | | | **$[Sum]** | |
| | **TOTAL DAMAGES** | | | **$[Grand Total]** | |
