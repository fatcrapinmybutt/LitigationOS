# Gotchas — litigation-child-support-analyzer

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The Michigan Child Support Formula (MCSF) is straightforward — just plug in the numbers." | The MCSF involves dozens of variables: gross income, tax deductions, health insurance, child care, overnight counts, multi-family adjustments, and deviation factors. A single incorrect input cascades through the entire formula. MCL 552.517 requires the formula calculation, but MCL 552.605(2) allows deviation — both must be analyzed. | Wrong support amount that either shortchanges L.D.W. or creates an unsustainable obligation. Courts rely heavily on the formula calculation; if your numbers are wrong, the court's order will be wrong. Correcting a support order requires a formal motion and showing changed circumstances under MCL 552.517. |
| 2 | "Income is just wages — the W-2 tells us everything." | MCSF income includes ALL sources: wages, bonuses, overtime, self-employment, rental income, investment income, trust distributions, imputed income, and even in-kind benefits. MCL 552.602(f) defines income broadly. A party working overtime or receiving cash payments will have income beyond the W-2. | Underreported income = too-low support calculation. If Emily A. Watson has unreported income, L.D.W. receives less support than entitled. If Andrew James Pigors' income is overstated by including non-recurring items, support is set too high. Every income source must be verified against multiple documents. |
| 3 | "Deviation from the formula is rare — the court always follows it." | MCL 552.605(2) allows deviation when application of the formula would be "unjust or inappropriate." Courts regularly deviate for: special needs of the child, extraordinary educational expenses, high-income situations, shared custody arrangements, and established lifestyle. Deviation arguments are common in contested cases. | Failing to argue deviation when appropriate means accepting a formula result that may not serve L.D.W.'s best interests. Conversely, failing to anticipate the opposing party's deviation arguments means being unprepared when the court considers them. |
| 4 | "Arrearage calculation is just math — current amount times months missed." | Arrearage calculation must account for: partial payments, payment application order (current vs. arrears), interest accrual, modifications that changed the amount mid-period, abatement for incarceration, and credits for direct payments. MCL 552.603(2) and MCL 552.607 govern arrearage computation. | Incorrect arrearage calculations lead to enforcement actions based on wrong amounts or failure to enforce actual arrearages. A party may claim to be current when they're actually thousands behind, or be accused of arrearages that include credited payments. |
| 5 | "We don't need to worry about imputation — both parties are employed." | Imputation under MCL 552.605(2) applies when a party is VOLUNTARILY underemployed, not just unemployed. A party working part-time when capable of full-time, or in a lower-paying job than their qualifications support, is subject to imputation. The key is "voluntary" — involuntary job loss is treated differently. | Failing to argue imputation when warranted leaves money on the table for L.D.W. If Emily A. Watson is working below capacity, Andrew James Pigors should present imputation evidence. Conversely, if imputation is argued against Pigors, he must demonstrate his employment is not voluntarily reduced. |

---

## Common Failure Modes

### 1. Overnight Count Errors
- **What happens**: Parenting time overnights are miscounted, leading to wrong support calculation (MCSF adjusts for overnight percentages)
- **How to prevent**: Use actual court-ordered parenting time schedule; count overnights per calendar year; account for holidays, school breaks, and summer
- **Lane risk**: HIGH for Lane A — overnight count directly impacts support amount by hundreds per month

### 2. Health Insurance Premium Misallocation
- **What happens**: Health insurance costs for the child are not properly allocated between parties in the MCSF calculation
- **How to prevent**: Obtain actual premium amounts; calculate per-child allocation (total family premium minus adult-only premium, divided by number of children); verify employer contribution
- **Lane risk**: MEDIUM — misallocation shifts costs unfairly between parties

### 3. Income Verification Failure
- **What happens**: Support calculated on self-reported income that differs from actual income
- **How to prevent**: Cross-reference W-2/1099 with tax returns, bank deposits, and employer verification; use MCR 2.305 subpoena to employer if needed
- **Lane risk**: HIGH — every dollar of income error affects the monthly support amount

### 4. Failure to Account for Other Children
- **What happens**: MCSF multi-family adjustment not applied when a party has support obligations for other children
- **How to prevent**: Interrogatory specifically asking about other children and support obligations; MCSF requires adjustment for prior-born children's support
- **Lane risk**: MEDIUM — can significantly change the calculation

### 5. Missing Deviation Arguments
- **What happens**: Formula produces an unjust result but no deviation is argued because the analyzer didn't identify deviation factors
- **How to prevent**: Run deviation factor checklist for every calculation; document any special circumstances; prepare evidence for deviation hearing
- **Lane risk**: HIGH — the formula is a starting point, not always the final answer

---

## Integration Gotchas

- **litigation-asset-discovery-engine** provides the income data — support calculations are only as good as the financial evidence
- **litigation-contempt-specialist** uses support calculations for arrearage-based contempt motions
- **litigation-damages-calculator** tracks support as part of overall financial picture
- **litigation-foc-challenge-engine** handles challenges to FOC support recommendations — the analyzer provides the alternative calculation
- MCSF calculations must be updated whenever there's a change in income, overnights, or other formula inputs
