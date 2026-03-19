# Damages Calculation Methodology — evidence-intelligence-nexus

## Overview

Michigan damages must be calculated using documented methodologies — NEVER estimated
or approximated based on "comparable cases." This reference covers the damages framework
for each case lane in Pigors v Watson.

---

## Economic vs Non-Economic Damages

### Economic Damages (Special Damages)
Documented, quantifiable out-of-pocket losses:
- Lost wages and earning capacity
- Medical expenses (physical and mental health)
- Legal fees and costs
- Housing costs (relocation, temporary housing)
- Travel costs (parenting time enforcement)
- Child-related expenses (childcare, education, medical)

**Requirement**: Must be proven with specificity. Receipts, invoices, pay stubs,
tax returns, bank statements. General estimates are insufficient.

### Non-Economic Damages (General Damages)
Subjective, non-quantifiable harms:
- Pain and suffering
- Emotional distress
- Loss of companionship / consortium
- Loss of enjoyment of life
- Reputational harm

**Requirement**: Typically proven through testimony (plaintiff, family, experts).
Michigan has tort reform caps for non-economic damages in certain contexts
(MCL 600.1483) but these vary by claim type.

---

## Lane-Specific Damages Frameworks

### Lane A: Watson/Custody (2024-001507-DC)

**Claim: Parenting Time Interference**
- Economic: Travel costs for wasted trips, attorney fees for enforcement motions
- Non-economic: Emotional distress from parent-child separation
- Statutory: MCL 722.27a(7) — makeup parenting time, reasonable expenses
- Calculation: Document each interference incident with date, cost, DB reference

**Claim: Custody Modification**
- Not a damages claim per se — remedy is change of custody
- BUT: attorney fees may be recoverable under MCL 722.27a(7) if interference proven
- Document: hours spent, filing fees, service costs

### Lane B: Shady Oaks/Housing (2025-002760-CZ)

**Claim: Michigan Truth in Housing Act (MTHA)**
- Statutory damages: MCL 125.1509
- Economic: Actual damages from housing defects (repair costs, relocation)
- May include: security deposit violations (MCL 554.613 — double damages)
- Treble damages: Available under consumer protection (MCL 445.911)

**Calculation methodology**:
1. Document all repair costs with invoices/receipts
2. Document any habitability issues with photos, inspection reports
3. Calculate any rent overpayment during defective period
4. Apply treble damages multiplier if qualifying under MCPA

### Lane C: Federal §1983 (USDC WDMI)

**42 USC §1983 Damages Framework**:
- **Compensatory damages**: Actual losses caused by the constitutional violation
  - Economic: documented losses (same as above)
  - Non-economic: emotional distress, humiliation, reputational harm
- **Punitive damages**: Available against individual defendants (NOT municipalities)
  - Standard: defendant acted with "reckless or callous indifference" to rights
  - *Smith v Wade*, 461 US 30 (1983)
- **Nominal damages**: $1 if constitutional violation proven but no actual damages
  - Still sufficient to support attorney fee award
- **Attorney fees**: 42 USC §1988 — prevailing party may recover reasonable fees
  - *Hensley v Eckerhart*, 461 US 424 (1983) — lodestar method

**Qualified immunity analysis** (must address before damages):
- Did defendant violate a constitutional right?
- Was the right clearly established at the time?
- *Saucier v Katz*, 533 US 194 (2001)

### Lane D: PPO (2023-5907-PP)

**PPO Violation Damages**:
- Criminal contempt: MCL 600.2950(23) — up to 93 days jail, $500 fine
- Civil contempt: purge conditions to compel compliance
- Actual damages: documented losses from PPO violations
- Attorney fees: recoverable in enforcement proceedings

### Lane E: Judicial Misconduct/JTC

**JTC complaints do not award monetary damages to the complainant.**
- Remedy: judicial discipline (censure, suspension, removal)
- BUT: documented misconduct supports §1983 claims (Lane C)
- AND: misconduct evidence supports appellate arguments (Lane F)

---

## Treble Damages Analysis

### When Available
| Statute | Claim Type | Multiplier | Requirements |
|---------|-----------|------------|--------------|
| MCL 600.2919a | Conversion | 3x | Trespass or conversion proven |
| MCL 445.911 | Consumer Protection (MCPA) | 3x | Unfair/deceptive practice proven |
| MCL 554.613 | Security Deposit | 2x | Wrongful retention of deposit |
| 42 USC §1983 | Civil Rights (punitive) | Varies | Reckless/callous indifference |

### Calculation Method
```
Treble damages = Actual documented damages × 3
NOT: estimated damages × 3
NOT: estimated damages × 3 + punitive "bonus"

Steps:
1. Calculate actual economic damages with documentation
2. Calculate actual non-economic damages with testimony basis
3. Apply multiplier to the documented base amount
4. Document: "$X actual × 3 = $Y treble per MCL [section]"
```

---

## Damages Documentation Requirements

### For Every Damages Claim:
```
□ Type identified (economic / non-economic / statutory / punitive)
□ Legal basis cited (specific MCL, USC, or common law authority)
□ Calculation methodology stated
□ Supporting documentation listed (receipts, records, testimony)
□ Amount computed with showing of work
□ DB query for evidence support documented
□ Lane tag assigned
□ Opposing arguments anticipated (mitigation, caps, immunity)
```

### Evidence-to-Damages Mapping
For each claimed damage, link to specific evidence:
```
Damage: $X lost wages (3 days missed work for court appearances)
Evidence: Pay stubs (Exhibit A), employer letter (Exhibit B)
DB Query: SELECT * FROM evidence_quotes WHERE claim_type = 'economic_damages' AND subcategory = 'lost_wages'
Lane: A (Custody)
```

---

## Common Damages Errors

1. **Estimating instead of documenting** — every dollar must have a receipt or record
2. **Double-counting across lanes** — the same expense can only be claimed once
3. **Ignoring mitigation duty** — plaintiff must mitigate damages where reasonable
4. **Forgetting statutory caps** — some damages categories have caps
5. **Claiming punitive damages against municipality** — not available under §1983
   (*City of Newport v Fact Concerts*, 453 US 247 (1981))
6. **Inflating non-economic damages without basis** — must have testimony support
7. **Applying wrong multiplier** — treble = 3x total, not 3x + base (which would be 4x)
