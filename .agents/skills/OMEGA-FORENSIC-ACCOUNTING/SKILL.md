---
name: OMEGA-FORENSIC-ACCOUNTING
description: >-
  Financial forensics for Michigan family law and civil litigation. Covers hidden income
  detection, asset tracing, property valuation, child support calculation, damage
  quantification, Shady Oaks financial analysis, rent ledger forensics, title chain
  analysis, and forensic accounting exhibit preparation. Integrates with OMEGA-EVIDENCE
  for financial document processing and OMEGA-LITIGATION-SUPREME for filing.
category: litigation
version: "1.0.0"
triggers:
  - forensic accounting
  - hidden income
  - asset tracing
  - property valuation
  - child support calculation
  - damages
  - financial analysis
  - rent ledger
  - title chain
  - equitable distribution
  - Shady Oaks financial
  - utility
  - escrow
  - mortgage
lanes:
  - "A: Watson/Custody (child support)"
  - "B: Shady Oaks/Housing (property, rent, title)"
  - "C: Convergence (cross-lane financial)"
court: "14th Judicial Circuit, Muskegon County"
case: Pigors v Watson
metadata:
  tier: "1 (Litigation Core)"
  author: andrew-pigors + copilot-omega
  jurisdiction: Michigan
---

# 💰 OMEGA-FORENSIC-ACCOUNTING v1.0

> **Financial Forensics for Michigan Family Law & Civil Litigation**
> Hidden Income · Asset Tracing · Property Valuation · Damage Quantification
> Case: Pigors v Watson · Shady Oaks Housing · Lanes A, B, C

## Module FA1: Hidden Income Detection

### Michigan Child Support Framework
- **Michigan Child Support Formula** (MCL 552.605, MCSF 2021)
- Income includes: wages, salaries, commissions, bonuses, overtime, tips, self-employment
- Imputed income for voluntarily unemployed/underemployed (MCL 552.605(2))

### Detection Methods
```
Lifestyle Analysis:
  ├─ Compare reported income vs. actual spending
  ├─ Bank deposits exceeding reported income
  ├─ Cash-intensive business revenue suppression
  ├─ Unreported gifts, inheritances, or transfers
  └─ New assets inconsistent with income

Document Trail:
  ├─ Tax returns (3-5 years) — look for Schedule C, K-1
  ├─ Bank statements — unexplained deposits
  ├─ Credit card statements — lifestyle indicators
  ├─ Mortgage/loan applications — stated income
  └─ Social media — lifestyle inconsistencies
```

### Key Michigan Authorities
| Authority | Application |
|-----------|------------|
| MCL 552.605 | Income definition for child support |
| Ghidotti v Barber, 459 Mich 189 (1998) | Imputing income |
| Stallworth v Stallworth, 275 Mich App 282 (2007) | Self-employment income |
| Loutts v Loutts, 298 Mich App 21 (2012) | Voluntary reduction of income |

## Module FA2: Asset Tracing (Shady Oaks & Watson)

### Shady Oaks Entity Structure
```
Key entities to trace:
  ├─ Shady Oaks MHP (mobile home park)
  ├─ Homes of America LLC (registered: CT Corp, Plymouth MI)
  ├─ Cricklewood MHP LLC (registered: CT Corp, Plymouth MI)
  ├─ Albert Watson / Lori Watson (1143 E Norton Ave)
  ├─ Cody Watson / Emily Watson (2160 Garland Dr)
  └─ Related LLCs or DBAs

Asset tracing steps:
  1. Pull LARA records for all entities
  2. Pull Register of Deeds records (Muskegon County)
  3. Pull tax assessor records for all properties
  4. Map ownership transfers and timing
  5. Identify commingled personal/business assets
  6. Trace rent payments vs. reported revenue
```

### Title Chain Analysis
```
For each property:
  ├─ Deed history (quitclaim, warranty, land contract)
  ├─ Mortgage/lien records
  ├─ Tax lien status
  ├─ Foreclosure proceedings
  ├─ Transfer timing relative to litigation events
  └─ Fraudulent transfer indicators (MCL 566.34)
```

### Michigan Fraudulent Transfer Act (MUFTA — MCL 566.31+)
- Transfers made with intent to hinder, delay, or defraud creditors
- Transfers for less than reasonably equivalent value while insolvent
- Badge of fraud indicators (MCL 566.34(2)):
  - Transfer to insider
  - Debtor retained control
  - Transfer concealed
  - Debtor was sued or threatened
  - Transfer of substantially all assets
  - Debtor absconded

## Module FA3: Rent Ledger Forensics

### Common Manipulation Patterns
```
Detection checklist:
  □ Missing entries (gaps in chronological ledger)
  □ Retroactive entries (dates that don't match records)
  □ Round-number-only payments (suggests cash without documentation)
  □ Payments attributed to wrong tenant
  □ Credits/adjustments without documentation
  □ Discrepancy between ledger and bank deposits
  □ Multiple versions of same ledger (inconsistent)
  □ Handwritten alterations without initialing
```

### Shady Oaks Specific Analysis
```
Compare:
  1. Rent ledger entries vs. bank deposit records
  2. Lease terms vs. actual charges
  3. Late fees assessed vs. late fee policy
  4. Maintenance charges vs. actual work performed
  5. Security deposit handling vs. MCL 554.602-614
  6. Utility charges vs. actual utility bills
  7. Lot rent increases vs. MHCA requirements
```

## Module FA4: Child Support Calculation

### Michigan Child Support Formula
```
Inputs:
  ├─ Both parents' gross income
  ├─ Number of overnights (each parent)
  ├─ Health insurance costs
  ├─ Childcare costs
  ├─ Other children supported
  ├─ Tax filing status
  └─ Extraordinary expenses

Key adjustments:
  ├─ Imputed income if voluntarily unemployed
  ├─ Self-employment deductions (legitimate vs. personal)
  ├─ Overtime (regular vs. voluntary)
  ├─ Second household income (new partner)
  └─ Military/government benefits
```

### FOC (Friend of the Court) Integration
- FOC: Pamela Rusco, 990 Terrace St, Muskegon MI 49442
- FOC calculates support using MCSF software
- Challenge FOC calculation: MCL 552.517b — deviation from formula
- Grounds for deviation: MCL 552.605d

## Module FA5: Damage Quantification

### Economic Damages Categories (Pigors v Watson)
```
Lane A (Custody):
  ├─ Lost wages due to court appearances
  ├─ Attorney fees (if applicable)
  ├─ Psychological counseling costs
  ├─ Transportation costs for supervised visits
  └─ Impact on earning capacity

Lane B (Housing/Shady Oaks):
  ├─ Wrongful eviction damages (MCL 600.2918)
  ├─ Moving/relocation costs
  ├─ Lost personal property value
  ├─ Temporary housing costs
  ├─ Security deposit wrongfully withheld
  ├─ Utility overcharges/shutoff damages
  └─ Property damage/destruction

Lane D (PPO):
  ├─ Wrongful PPO damages (MCL 600.2950)
  ├─ Lost employment opportunities
  ├─ Reputational harm
  └─ Wrongful incarceration (per diem damages)

Cross-Lane (§1983):
  ├─ 42 USC §1983 compensatory damages
  ├─ Punitive damages (if malice/reckless indifference)
  ├─ Attorney fees (42 USC §1988)
  └─ Injunctive relief costs
```

### Per Diem Calculation (Wrongful Incarceration)
```
Days incarcerated: [VERIFY — count from DB]
Daily rate methodology:
  ├─ Lost daily income: [annual income / 365]
  ├─ Pain and suffering: $100-500/day (jury discretion)
  ├─ Loss of liberty: valued per Michigan wrongful imprisonment law
  └─ Total per diem × days = base damages
```

## Module FA6: Forensic Exhibit Preparation

### Financial Exhibit Types
| Exhibit | Purpose | Source Documents |
|---------|---------|-----------------|
| Income Comparison Chart | Show income discrepancy | Tax returns, bank statements |
| Asset Timeline | Show transfer patterns | Deeds, LARA records |
| Rent Ledger Analysis | Show manipulation | Ledger, bank records |
| Damage Summary | Quantify total damages | Receipts, estimates, per diem |
| Entity Ownership Map | Show corporate structure | LARA, Secretary of State |

### Exhibit Formatting Standards
- Title: "EXHIBIT [X] — [DESCRIPTION]"
- Bates stamp every page
- Source documents clearly identified
- Calculations shown with methodology
- Summary charts with supporting detail attached
- Authentication affidavit per MRE 901/902

## Global Rules

### Anti-Hallucination
- NEVER fabricate financial figures — use [AMOUNT — VERIFY] placeholders
- NEVER invent account numbers, tax IDs, or transaction records
- All calculations must show formula and source data
- Party names: Andrew James Pigors, Emily A. Watson, L.D.W.

### DB-First
- Query litigation_context.db for existing financial evidence
- Check evidence_quotes for financial document references
- Check d_drive_evidence and downloads_inventory for financial files

### Integration Points
- Filing damages claims → OMEGA-LITIGATION-SUPREME M4
- Evidence processing → OMEGA-EVIDENCE
- Housing analysis → Lane B specialist agents
- Child support → FOC procedures via OMEGA-RESEARCH
