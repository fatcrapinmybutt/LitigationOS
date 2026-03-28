---
name: FORGE-DAMAGES-WARFARE
description: >-
  Unified litigation damages, financial analysis, sanctions, settlement, child-support,
  fee recovery, and post-judgment engine for Pigors v Watson. Computes methodology-backed
  constitutional damages under 42 USC §1983, economic loss schedules, emotional distress
  quantification, punitive multipliers, Michigan child-support adjustments, MCR 2.114
  sanctions, settlement decision matrices, garnishment paths, and court-ready exhibits.
  Triggers on damages, fees, support, sanctions, settlement, enforcement, or financial proof.
category: litigation
version: "1.0.0"
triggers:
  - "calculate damages"
  - "damages exhibit"
  - "constitutional damages"
  - "economic loss"
  - "emotional distress"
  - "punitive damages"
  - "child support"
  - "sanctions motion"
  - "settlement evaluation"
  - "fee recovery"
  - "garnishment"
  - "judgment enforcement"
metadata:
  tier: FORGE
  fused_skills: 10
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-03-27
  forge_class: litigation-damages
  emergent_capability: "Transforms harms, cost ledgers, support distortions, sanctions proof, and enforcement logic into a single damages-to-filing warfare pipeline"
---

# 💰 FORGE-DAMAGES-WARFARE
> **Total Damages & Financial Warfare Engine (Ω-Δ99)**

| Field | Value |
| --- | --- |
| Tier | FORGE |
| Domain | Litigation damages, financial analysis, sanctions, settlement, support, enforcement |
| Scope | Constitutional damages, economic exhibits, emotional distress, punitive multipliers, MCSF analysis, sanctions, fee recovery, offers, collections |
| Emergent Capability | Converts the factual record in *Pigors v Watson* into methodology-backed money narratives, filing-ready tables, and enforcement-ready numbers |

All examples below use **Pigors v Watson, No. 2024-001507-DC, 14th Circuit Court, Muskegon County**, before **Hon. Jenny L. McNeill**; the child is **L.D.W. only**; Andrew James Pigors is the pro se plaintiff; Emily A. Watson is the defendant at **2160 Garland Dr, Norton Shores, MI 49441**.
The baseline worked example assumes **233 days of denied parenting time**, **59 incarceration days**, **2 jobs lost**, and **2 homes lost** in 2026. Every figure shows method, rate, duration, or multiplier; no naked round-number demands are used.

## Forged from 10 Skills

| # | Source Skill | Fused Capability | Primary Feed |
| --- | --- | --- | --- |
| 1 | damages-calculator | §1983, emotional, punitive, and economic computation logic | DW1, DW2, DW3, DW4 |
| 2 | financial-analyst | income reconstruction, hidden-asset review, disclosure comparison | DW2, DW5, DW7 |
| 3 | cost-tracker | fee ledgering, mileage, copy and service accounting | DW2, DW6, DW8 |
| 4 | settlement-analyzer | BATNA modeling, expected value, counter-proposal design | DW7 |
| 5 | child-support-specialist | Michigan Child Support Formula framing, overtime and imputation analysis | DW5 |
| 6 | sanctions-motion-generator | MCR 2.114 sanction theory, frivolous-filing records, fee petitions | DW6 |
| 7 | garnishment-specialist | post-judgment collection workflow, wage withholding, levy paths | DW7, DW8 |
| 8 | post-judgment-enforcer | compliance monitoring, execution sequencing, collection pressure | DW7, DW8 |
| 9 | filing-fee-tracker | filing fee schedules, MC 20 waiver logic, recoverable court costs | DW2, DW6 |
| 10 | economic-expert-module | expert-style schedule building, demonstratives, testimony framing | DW2, DW3, DW8 |

```text
+--------------------------------------------------------------------------------------------------+
|                                FORGE-DAMAGES-WARFARE (Ω-Δ99)                                     |
+--------------------------------------------------------------------------------------------------+
|  DW1 Constitutional  --->  DW4 Punitive  ---+                                                    |
|          |                        |          |                                                    |
|          v                        v          |                                                    |
|  DW2 Economic --------->  DW7 Settlement    |                                                    |
|          |                        |          |                                                    |
|          v                        v          v                                                    |
|  DW3 Emotional ------->  DW6 Sanctions ---> DW8 Damages Exhibit Factory ---> Filing / Trial     |
|          |                        ^          ^                                                    |
|          +-------------> DW5 Child Support -+                                                    |
|                                                                                                  |
|  Inputs: evidence quotes, claims tables, costs, income records, dates, orders, sanctions facts   |
|  Outputs: damages schedules, support worksheets, sanctions requests, settlement ranges, exhibits  |
+--------------------------------------------------------------------------------------------------+
```

## DW1: Constitutional Damages Calculator

**Purpose**

Quantify methodology-backed constitutional damages under 42 USC §1983 for denial of parenting time, liberty deprivation, and fundamental-right interference tied to state action in Pigors v Watson.

**Design Pattern**

Rights-to-Rates Engine + Date-Window Aggregator + Evidence-Weighted Schedule Builder

**Detailed Description**

1. DW1 begins with the premise that parental access and family integrity are fundamental liberty interests. In this matter the operative harm is not abstract unfairness; it is measurable deprivation of time, relationship continuity, decision-making access, and bodily liberty during incarceration windows.
2. The module separates constitutional harm into at least three layers: daily deprivation of the parent-child relationship, intensified liberty loss during incarceration, and process corruption indicators that support both liability and an enhanced punitive narrative in DW4.
3. Every calculation is anchored to dates inside 2026. For the core example, denied-parenting days run from **2026-01-01** through **2026-08-21**, inclusive, which yields **233 days**. Incarceration runs from **2026-02-03** through **2026-04-02**, inclusive, which yields **59 days**.
4. DW1 rejects unsupported lump-sum requests. Instead it asks: what daily rate is being used, what fact supports the selected window, what evidence proves causation, and where does each day appear in the timeline?
5. The module treats due-process deprivation and access deprivation as overlapping but not duplicative. It avoids double counting by building a constitutional basket with explicit component lines and evidentiary anchors.
6. Where state action is disputed, DW1 adds a liability-bridge narrative: judicial act, order consequence, incarceration consequence, and parental-separation consequence. That bridge is later consumed by DW4 and settlement analysis in DW7.
7. For pleadings, DW1 can emit a federal complaint damages paragraph, a mediation sheet, or an exhibit row ledger. For trial, it can support expert-style testimony explaining why the methodology is rational, transparent, and reproducible.
8. When the facts support reputational injury from false accusation campaigns, DW1 flags a downstream branch for **MCL 600.2911** review so defamation-adjacent damages are not mixed carelessly into the constitutional bucket.

**Key Operations**

| Operation | Inputs | Output | Evidence Hook |
| --- | --- | --- | --- |
| Inclusive day count | start date + end date | verified deprivation days | timeline, orders, jail records |
| Daily constitutional rate selection | benchmark rate + rationale | per diem schedule | claims table + methodology memo |
| Liberty-loss supplement | incarceration window | enhanced daily schedule | booking/release proof |
| Non-duplication filter | overlapping harm lines | clean compensatory basket | damages_model notes |
| Liability bridge | actor + act + deprivation + causation | §1983-ready narrative | evidence_quotes |
| Complaint paragraph export | schedule totals | pleading language | DW8 exhibit pipeline |

**Code Examples**

### DW1.1 Python Calculation Example

```python
from dataclasses import dataclass
from datetime import date

@dataclass(slots=True)
class ConstitutionalInputs:
    parenting_start: date = date(2026, 1, 1)
    parenting_end: date = date(2026, 8, 21)
    jail_start: date = date(2026, 2, 3)
    jail_end: date = date(2026, 4, 2)
    parenting_rate: float = 412.35
    liberty_rate: float = 188.40

    def parenting_days(self) -> int:
        return (self.parenting_end - self.parenting_start).days + 1

    def jail_days(self) -> int:
        return (self.jail_end - self.jail_start).days + 1

    def total(self) -> float:
        deprivation = self.parenting_days() * self.parenting_rate
        incarceration = self.jail_days() * self.liberty_rate
        return round(deprivation + incarceration, 2)

inputs = ConstitutionalInputs()
deprivation = inputs.parenting_days() * inputs.parenting_rate
incarceration = inputs.jail_days() * inputs.liberty_rate

print({
    "case": "Pigors v Watson, 2024-001507-DC",
    "child": "L.D.W.",
    "parenting_days": inputs.parenting_days(),
    "incarceration_days": inputs.jail_days(),
    "deprivation_component": round(deprivation, 2),
    "incarceration_component": round(incarceration, 2),
    "constitutional_total": inputs.total(),
})
# parenting_days = 233
# incarceration_days = 59
# constitutional_total = $107,193.15
```

### DW1.2 SQL Query Against `claims`, `damages_model`, and `evidence_quotes`

```sql
SELECT
    c.claim_id,
    c.claim_name,
    dm.damage_component,
    dm.methodology,
    dm.daily_rate,
    dm.day_count,
    dm.amount,
    eq.quote_text,
    eq.source_date
FROM claims c
JOIN damages_model dm ON dm.claim_id = c.claim_id
LEFT JOIN evidence_quotes eq ON eq.claim_id = c.claim_id
WHERE c.claim_name = '42 USC §1983 - Due Process / Parenting-Time Deprivation'
  AND dm.damage_component IN ('per_diem_parenting', 'liberty_supplement')
  AND eq.source_date BETWEEN '2026-01-01' AND '2026-08-21'
ORDER BY dm.damage_component, eq.source_date;
```

### DW1.3 Worked Example Table

| Damage Line | Methodology | Amount | Notes |
| --- | --- | ---: | --- |
| Denied parenting time | 233 days × $412.35 | $96,077.55 | Family-integrity per diem tied to 2026 deprivation window |
| Incarceration liberty supplement | 59 days × $188.40 | $11,115.60 | Additional liberty impairment inside the same 2026 record |
| Double-count prevention | Overlap review across timeline atoms | $0.00 | Narrative safeguard rather than a money line |
| Complaint-ready constitutional basket | sum of above lines | $107,193.15 | Primary DW1 export into DW4 and DW8 |

### DW1.4 Integration Points

- Send the constitutional subtotal to **DW4** as the punitive base when deliberate or reckless conduct is evidenced.
- Send the same subtotal to **DW7** for expected-value modeling and minimum acceptable settlement thresholds.
- Send day counts and rates to **DW8** so the exhibit factory can generate a transparent per-diem chart.
- Pair with **DW3** when the same separation window produced severe emotional distress, but preserve line-item separation.
- Pair with **DW6** when sanctions theory overlaps with constitutional process abuse, especially repetitive frivolous filings or abusive process steps.
- Flag **MCL 600.2911** review only when false accusation publications create a separate reputational-harm lane that should not be commingled automatically.

### DW1.5 Operational Guardrails

- Never count days outside 2026 in examples or templates.
- Never assume state action; explicitly state the actor, the act, and the causal path.
- Never merge emotional distress into the constitutional schedule without a distinct label.
- Never demand a lump sum without exposing the daily rate and date interval.
- Never use the child's full name; use **L.D.W.** only.

### DW1.6 Scenario Drill

- If a later 2026 order restores partial parenting time, split the window into pre-restoration and post-restoration slices rather than averaging the rate.
- If incarceration records show a midnight booking problem, count inclusive days using source timestamps and preserve the evidentiary note.
- If defense argues speculative damages, export the line-level calculation and the supporting dates as a rebuttal attachment.
- If a federal complaint is drafted, mirror the line labels used here so DW8 and the pleading stay synchronized.

## DW2: Economic Loss Engine

**Purpose**

Convert lost work, lost housing, legal spend, transportation, and litigation-driven out-of-pocket costs into expert-style economic schedules supported by records and calculation logic.

**Design Pattern**

Ledger Composer + Earnings Reconstruction + Housing Shock Analyzer

**Detailed Description**

1. DW2 treats economic harm as a collection of provable ledgers rather than a single 'hardship' sentence. The goal is to show how parental deprivation, incarceration fallout, and court conflict translated into discrete money losses in 2026.
2. The module breaks the case into wage loss, housing loss, litigation expenditure, and disruption costs. Each line item must answer four questions: what happened, what did it cost, how was the amount derived, and what document proves it?
3. For this matter the core examples are two jobs lost, two homes lost, and a substantial pro se litigation expense trail. Because Andrew James Pigors appears pro se, DW2 carefully distinguishes reimbursable out-of-pocket cost lines from time-value narratives used mainly in settlement or sanctions framing.
4. Housing losses are treated as multi-part events: forfeited deposit, bridge lodging, storage, utility reconnection, and short-notice premium rent. This prevents understatement and also prevents unsupported inflation.
5. DW2 can reconcile pay stubs, bank records, leases, motel receipts, storage invoices, postage logs, mileage sheets, and transcript invoices into a single schedule suitable for exhibit use.
6. Where financial disclosure by the opposing party appears incomplete, DW2 can also generate a discrepancy memo that later supports child-support analysis in DW5 or settlement leverage in DW7.
7. If false statements caused a reputational job-loss event or financial fallout from published accusations, DW2 can create a side note for **MCL 600.2911** analysis without contaminating the core ledger.
8. The output is a court-usable schedule with clean categories, formulas, backup references, and subtotals that can survive cross-examination.

**Key Operations**

| Operation | Inputs | Output | Evidence Hook |
| --- | --- | --- | --- |
| Job-loss reconstruction | weekly pay × missed weeks | lost-income subtotal | pay stubs, tax docs, HR records |
| Housing shock schedule | deposit + lodging + storage + utilities | per-home loss total | leases, receipts, move logs |
| Legal cost ledger | fees + service + copies + mileage + transcripts | taxable / non-taxable cost lines | receipts, mileage log |
| Disclosure discrepancy review | income statements + bank activity | variance memo | financial records |
| Exhibit roll-up | all approved rows | economic damages schedule | DW8 charting |
| Settlement export | subtotals + proof strength | economic floor | DW7 counteroffer math |

**Code Examples**

### DW2.1 Python Calculation Example

```python
from collections import OrderedDict

losses = OrderedDict({
    "job_1_lost_income": 1153.84 * 17,
    "job_2_lost_income": 923.40 * 21,
    "home_1_loss": 1485.50 + (17 * 96.35) + (4 * 182.76) + 212.48,
    "home_2_loss": 2015.25 + (11 * 104.62) + 287.63 + (6 * 128.57) + (4 * 182.76),
    "legal_and_case_costs": 175.00 + 49.88 + (1463 * 0.10) + (782 * 0.67) + (2 * 187.35) + (6 * 9.85) + (7 * 8.50),
})

total = round(sum(losses.values()), 2)
for label, amount in losses.items():
    print(f"{label} = ${amount:,.2f}")
print(f"economic_total = ${total:,.2f}")
# job_1_lost_income = $19,615.28
# job_2_lost_income = $19,391.40
# home_1_loss = $4,066.97
# home_2_loss = $4,956.16
# legal_and_case_costs = $1,388.42
```

### DW2.2 SQL Query Against `claims`, `damages_model`, and `evidence_quotes`

```sql
SELECT
    dm.damage_component,
    dm.methodology,
    dm.amount,
    dm.backup_document,
    eq.quote_text,
    eq.source_date
FROM damages_model dm
LEFT JOIN evidence_quotes eq
  ON eq.damage_component = dm.damage_component
WHERE dm.case_number = '2024-001507-DC'
  AND dm.damage_component IN (
    'job_1_lost_income',
    'job_2_lost_income',
    'home_1_loss',
    'home_2_loss',
    'legal_and_case_costs'
  )
ORDER BY dm.damage_component, eq.source_date;
```

### DW2.3 Worked Example Table

| Damage Line | Methodology | Amount | Notes |
| --- | --- | ---: | --- |
| Job 1 lost income | 17 weeks × $1,153.84 | $19,615.28 | Use payroll evidence, schedule loss from 2026 separation window |
| Job 2 lost income | 21 weeks × $923.40 | $19,391.40 | Second wage stream independently computed |
| Home 1 loss | $1,485.50 + 17×$96.35 + 4×$182.76 + $212.48 | $4,066.97 | Deposit, motel bridge, storage, utility reconnect |
| Home 2 loss | $2,015.25 + 11×$104.62 + $287.63 + 6×$128.57 + 4×$182.76 | $4,956.16 | Second displacement event with premium rent pressure |
| Legal and case costs | $175.00 + $49.88 + 1,463×$0.10 + 782×$0.67 + 2×$187.35 + 6×$9.85 + 7×$8.50 | $1,388.42 | Filing, service, copies, mileage, transcripts, postage, parking |
| Economic subtotal | sum of verified ledgers | $49,418.23 | DW2 output consumed by DW7 and DW8 |

### DW2.4 Integration Points

- Feed all verified ledger rows to **DW8** so the exhibit factory can render court-friendly tables and charts.
- Feed lost-income patterns to **DW5** for child-support imputation and income-capacity arguments.
- Feed out-of-pocket litigation costs to **DW6** for sanctions and fee recovery requests under MCR 2.114 and related cost authority.
- Feed economic subtotal to **DW7** as the floor for any serious settlement discussion.
- Pair with **DW3** to distinguish economic hardship from emotional harm while showing how both arise from the same 2026 events.
- Pair with **DW1** where incarceration fallout created wage loss that follows a constitutional injury window.

### DW2.5 Operational Guardrails

- Separate hard costs from opportunity-cost narratives.
- Use receipts or explain why secondary reconstruction was necessary.
- Do not bury formulas inside prose; show the multiplication or addition directly.
- Keep each home-loss event on its own row cluster to avoid confusion.
- Mark any disclosure-gap estimate as provisional until records close the gap.

### DW2.6 Scenario Drill

- If a motel receipt is missing, reconstruct the stay from bank entries and note the source substitution.
- If a wage period overlaps partial work, prorate using the actual number of missed shifts, not a full week assumption.
- If defense claims mitigation failure, document the actual relocation and job-search actions inside 2026.
- If a mediation brief needs visuals, export the largest three categories first and attach the full ledger as an appendix.

## DW3: Emotional Distress Quantifier

**Purpose**

Translate separation trauma, incarceration-linked distress, counseling records, and narrative evidence into a documented emotional-distress valuation without abandoning evidentiary discipline.

**Design Pattern**

Trauma Index + Evidence Multiplier + Clinical Support Scheduler

**Detailed Description**

1. DW3 is not a free-floating pain-and-suffering demand generator. It turns emotional harm into a documented methodology that can be explained in affidavit form, at mediation, or through an expert witness.
2. In the Pigors v Watson context, the emotional harm narrative centers on prolonged separation from L.D.W., destabilization during incarceration, recurring court-triggered stress, sleep disruption, counseling demand, and impairment in daily functioning.
3. The module uses a mixed model: a daily separation-distress rate, a separate incarceration-trauma increment, counseling-session costs, and a symptom-journal corroboration line. This produces transparency and avoids untestable emotional lump sums.
4. DW3 should always identify the underlying evidence category: therapist notes, counseling invoices, medication records, contemporaneous journals, witness statements, or timeline quotes showing distress reactions in 2026.
5. Because emotional distress can overlap with constitutional and economic harm, DW3 labels every line as emotional only and forbids duplication of wages, lodging, or liberty-loss money already captured elsewhere.
6. Where false accusations or public allegations caused humiliation or reputational pain, DW3 cross-flags **MCL 600.2911** review as a separate legal theory rather than silently inflating the emotional basket.
7. In jury-facing settings DW3 can produce a human-readable explanation: the damage model reflects duration, intensity, treatment effort, and corroboration density. In bench settings it can be collapsed into a concise schedule plus evidentiary notes.
8. The module is designed to survive the common defense objection that emotional-distress numbers are invented. The answer is to show the arithmetic, the dates, the corroboration, and the reason each rate was chosen.

**Key Operations**

| Operation | Inputs | Output | Evidence Hook |
| --- | --- | --- | --- |
| Daily distress valuation | days × distress rate × severity factor | baseline distress line | journals, therapy, witness quotes |
| Incarceration trauma add-on | custody days × trauma rate | acute distress line | booking logs, release records |
| Treatment-cost capture | session count × session rate | direct treatment line | invoices, records |
| Symptom corroboration | journal entries × corroboration unit | support factor | contemporaneous writings |
| Duplication screening | compare DW1 / DW2 lines | clean emotional subtotal | damages_model flags |
| Narrative export | subtotal + evidence density | brief-ready emotional section | DW8 demonstratives |

**Code Examples**

### DW3.1 Python Calculation Example

```python
separation_days = 233
incarceration_days = 59
daily_distress_rate = 137.84
severity_multiplier = 1.35
incarceration_rate = 92.16
counseling_sessions = 12
counseling_rate = 148.25
journal_entries = 41
journal_unit = 28.65

emotional_total = (
    separation_days * daily_distress_rate * severity_multiplier
    + incarceration_days * incarceration_rate
    + counseling_sessions * counseling_rate
    + journal_entries * journal_unit
)

print({
    "separation_component": round(separation_days * daily_distress_rate * severity_multiplier, 2),
    "incarceration_component": round(incarceration_days * incarceration_rate, 2),
    "counseling_component": round(counseling_sessions * counseling_rate, 2),
    "journal_component": round(journal_entries * journal_unit, 2),
    "emotional_total": round(emotional_total, 2),
})
# emotional_total = $51,748.66
```

### DW3.2 SQL Query Against `claims`, `damages_model`, and `evidence_quotes`

```sql
SELECT
    c.claim_id,
    dm.damage_component,
    dm.methodology,
    dm.amount,
    eq.quote_text,
    eq.source_type,
    eq.source_date
FROM claims c
JOIN damages_model dm ON dm.claim_id = c.claim_id
JOIN evidence_quotes eq ON eq.claim_id = c.claim_id
WHERE c.claim_name = 'Emotional Distress - Separation Trauma'
  AND dm.damage_component IN (
    'separation_distress',
    'incarceration_trauma',
    'counseling_costs',
    'journal_corroboration'
  )
  AND eq.source_date BETWEEN '2026-01-01' AND '2026-12-31'
ORDER BY eq.source_date;
```

### DW3.3 Worked Example Table

| Damage Line | Methodology | Amount | Notes |
| --- | --- | ---: | --- |
| Separation distress | 233 × $137.84 × 1.35 severity | $43,357.57 | Long-duration separation from L.D.W. |
| Incarceration trauma | 59 × $92.16 | $5,437.44 | Acute distress during jail period |
| Counseling line | 12 sessions × $148.25 | $1,779.00 | Direct treatment effort in 2026 |
| Journal corroboration | 41 entries × $28.65 | $1,174.65 | Corroborative rather than duplicative factor |
| Emotional subtotal | sum of validated emotional lines | $51,748.66 | Export to DW7 and DW8 |

### DW3.4 Integration Points

- Feed the emotional subtotal to **DW7** for mediation brackets and risk-adjusted settlement analysis.
- Feed line-level emotional proof to **DW8** for timeline overlays that show severity by date cluster.
- Pair with **DW1** when pleading constitutional harm, but keep emotional arithmetic distinct.
- Pair with **DW6** when frivolous filings or abusive motion practice clearly intensified distress.
- Send treatment-cost rows to **DW2** only if a separate economic reimbursement line is needed; otherwise keep them here.
- Flag **MCL 600.2911** review where humiliation traces to provably false published accusations rather than private distress alone.

### DW3.5 Operational Guardrails

- Do not price emotional distress by intuition alone.
- Do not double count therapy invoices in both DW2 and DW3 without a note.
- Use 2026-only source dates in examples and schedules.
- State whether a factor is compensatory, corroborative, or aggravating.
- Keep the child reference anonymized as L.D.W. in every narrative sample.

### DW3.6 Scenario Drill

- If no therapist records exist, rely on journals, witnesses, and crisis-contact logs, but lower the confidence score.
- If distress spikes around a specific hearing, create a sub-window rather than inflating every day equally.
- If a settlement brief needs brevity, present the subtotal and move the factor-by-factor explanation to an exhibit.
- If defense attacks subjectivity, respond with the line-level methodology and the source-density log.

## DW4: Punitive Damages Multiplier

**Purpose**

Model punitive exposure for deliberate or reckless constitutional violations using guidepost logic, multiplier discipline, and filing-ready explanation blocks.

**Design Pattern**

Guidepost Scorer + Ratio Governor + Reprehensibility Matrix

**Detailed Description**

1. DW4 is the bridge from injury to deterrence. It does not simply multiply compensatory damages by an arbitrary number; it scores the conduct and then constrains the result with defensible ratio logic.
2. In a §1983 framing, punitive damages turn on reckless or callous indifference. The module therefore collects proof of deliberate disregard, repeated warnings, duration of harm, vulnerability of the parent-child relationship, and persistence after notice.
3. The worked example below uses a scored multiplier built from four factors: malice/indifference, duration, vulnerability, and concealment or persistence. The combined result is **2.077x** of the compensatory basket.
4. DW4 is especially useful where the defense will attack any punitive request as excessive. By showing the factor inputs first, the module demonstrates that the multiplier is an output of a method rather than a demand plucked from the air.
5. The module can also generate ratio-sensitive alternatives: conservative, balanced, and aggressive punitive requests. That gives DW7 meaningful settlement leverage ranges instead of a single brittle number.
6. If false and reputationally injurious accusations were used as a weapon, DW4 can flag a side-branch for **MCL 600.2911** analysis so the punitive story is harmonized with any defamation-adjacent theory.
7. DW4 should always be tethered to proof. It is strongest when combined with DW1's constitutional day counts, DW6's sanctions pattern log, and DW8's conduct-to-consequence demonstratives.
8. The end product is a deterrence narrative: the amount requested is calibrated to the seriousness and persistence of the conduct, not inflated for theatrics.

**Key Operations**

| Operation | Inputs | Output | Evidence Hook |
| --- | --- | --- | --- |
| Reprehensibility scoring | fact clusters + warning history | factor weights | orders, objections, notices |
| Multiplier synthesis | weighted factors | punitive ratio | damages_model |
| Ratio governance | compensatory total + target ratio | capped punitive request | constitutional due-process check |
| Scenario branching | conservative / balanced / aggressive | three punitive options | settlement packet |
| Jury instruction framing | score explanation + deterrence purpose | argument shell | brief / trial memo |
| Settlement integration | punitive range + collectability | negotiation leverage | DW7 |

**Code Examples**

### DW4.1 Python Calculation Example

```python
compensatory = 208360.04
factors = {
    "malice_or_callous_indifference": 1.30,
    "duration_of_deprivation": 1.22,
    "parent_child_vulnerability": 1.18,
    "persistence_after_notice": 1.11,
}

multiplier = 1.0
for weight in factors.values():
    multiplier *= weight
multiplier = round(min(multiplier, 3.75), 3)
punitive = round(compensatory * multiplier, 2)

print({
    "compensatory": compensatory,
    "multiplier": multiplier,
    "punitive": punitive,
    "ratio_to_compensatory": round(punitive / compensatory, 3),
})
# punitive_total = $432,763.81
```

### DW4.2 SQL Query Against `claims`, `damages_model`, and `evidence_quotes`

```sql
SELECT
    dm.damage_component,
    dm.methodology,
    dm.amount,
    eq.quote_text,
    eq.source_date,
    eq.source_type
FROM damages_model dm
JOIN evidence_quotes eq ON eq.damage_component = dm.damage_component
WHERE dm.case_number = '2024-001507-DC'
  AND dm.damage_component IN (
    'punitive_malice_score',
    'punitive_duration_score',
    'punitive_vulnerability_score',
    'punitive_persistence_score'
  )
ORDER BY eq.source_date;
```

### DW4.3 Worked Example Table

| Damage Line | Methodology | Amount | Notes |
| --- | --- | ---: | --- |
| Compensatory base | DW1 + DW2 + DW3 totals | $208,360.04 | Foundation for punitive modeling |
| Multiplier | 1.30 × 1.22 × 1.18 × 1.11 | 2.077x | Methodology-backed deterrence factor |
| Punitive projection | $208,360.04 × 2.077 | $432,763.81 | Balanced punitive demand scenario |
| Ratio check | $432,763.81 / $208,360.04 | 2.077:1 | Helps discipline excessiveness arguments |

### DW4.4 Integration Points

- Consume the constitutional subtotal from **DW1** and the distress/economic baselines from **DW2** and **DW3**.
- Feed punitive-range outputs to **DW7** so settlement analysis can compare cash offers against realistic litigation upside.
- Feed factor tables to **DW8** for a one-page punitive rationale exhibit.
- Pair with **DW6** when the same record also supports sanctions under MCR 2.114; the sanction ask and punitive ask must be distinct but mutually reinforcing.
- Use DW4's conservative, balanced, and aggressive views when preparing mediation brackets or pre-suit demand letters.
- If defamation-style facts exist, note the possible **MCL 600.2911** intersection without folding the same injury twice into the punitive basket.

### DW4.5 Operational Guardrails

- Do not multiply from emotion alone; score conduct first.
- Do not hide factor weights; disclose the path to the multiplier.
- Keep punitive scenarios separate from sanctions reimbursement.
- Re-check collectability before using the highest number in negotiations.
- Preserve 2026-only date anchors in examples and support tables.

### DW4.6 Scenario Drill

- If discovery produces stronger notice evidence, update the persistence factor rather than rewriting the whole punitive section.
- If a judge is unlikely to entertain aggressive punitive framing early, lead with the balanced scenario and reserve the aggressive model for mediation.
- If compensatory figures change, recompute the punitive schedule automatically; never hand-edit the total.
- If the defense attacks due-process limits, show the factor scorecard and the ratio check side by side.

## DW5: Michigan Child Support Analyzer

**Purpose**

Apply Michigan Child Support Formula concepts, income imputation, and parenting-time distortion analysis to support accurate support calculations and deviation arguments.

**Design Pattern**

Worksheet Mirror + Imputed Income Engine + Overnight Distortion Detector

**Detailed Description**

1. DW5 treats child support as a financial consequence of the custody record, not as a disconnected math exercise. In Pigors v Watson, the key issue is that denied parenting time can distort overnights and therefore distort support outcomes.
2. The module reconstructs income using pay history, expected hours, and documentary proof. It also distinguishes actual temporary earnings collapse from earning capacity when a court needs an imputed-income lens.
3. Because this case involves two lost jobs in 2026, DW5 must decide whether temporary earnings reflect ability or only crisis. That question directly affects both monthly support and any deviation argument.
4. DW5 is built to show two scenarios side by side: the denied-parenting snapshot and the restored-parenting baseline. That side-by-side comparison is usually more persuasive than arguing over a single worksheet cell.
5. The module can also ingest disclosure discrepancies from DW2 if the opposing party's income appears understated. In that posture DW5 becomes both a formula engine and a credibility engine.
6. Support analysis is always tied back to L.D.W.'s best interests, parenting-time equity, and the integrity of the record. A distorted overnight count can itself become a damages and leverage fact for DW7.
7. If false accusations led to financial or reputational effects that influence income evidence, a side note can be generated for **MCL 600.2911** review without corrupting the support worksheet.
8. DW5 outputs worksheet-ready numbers, deviation arguments, and a clean explanation of why a denied-parenting snapshot should not be mistaken for a fair long-term support baseline.

**Key Operations**

| Operation | Inputs | Output | Evidence Hook |
| --- | --- | --- | --- |
| Income reconstruction | historical wages + current capacity | gross monthly figures | pay history, tax returns |
| Imputation analysis | work history + ability + opportunity | imputed earnings | employment records |
| Overnight distortion check | actual vs restored schedule | support delta | orders, calendars |
| Deviation memo | formula result + fairness narrative | brief-ready argument | MCSF concepts |
| Disclosure variance review | declared vs inferred income | credibility note | bank records |
| Exhibit export | worksheet + narrative | support chart | DW8 |

**Code Examples**

### DW5.1 Python Calculation Example

```python
plaintiff_monthly_imputed = 4503.02
defendant_monthly_actual = 4968.84
combined_income = plaintiff_monthly_imputed + defendant_monthly_actual
base_support_obligation = 1126.44

plaintiff_share = plaintiff_monthly_imputed / combined_income
defendant_share = defendant_monthly_actual / combined_income

denied_parenting_transfer = 286.14
restored_parenting_transfer = 74.38
distortion_delta = denied_parenting_transfer - restored_parenting_transfer

print({
    "combined_income": round(combined_income, 2),
    "plaintiff_share": round(plaintiff_share, 4),
    "defendant_share": round(defendant_share, 4),
    "denied_parenting_transfer": denied_parenting_transfer,
    "restored_parenting_transfer": restored_parenting_transfer,
    "distortion_delta": round(distortion_delta, 2),
})
# child_support_delta = $211.76 per month
```

### DW5.2 SQL Query Against `claims`, `damages_model`, and `evidence_quotes`

```sql
SELECT
    c.claim_id,
    dm.damage_component,
    dm.methodology,
    dm.amount,
    eq.quote_text,
    eq.source_date
FROM claims c
JOIN damages_model dm ON dm.claim_id = c.claim_id
LEFT JOIN evidence_quotes eq ON eq.claim_id = c.claim_id
WHERE c.claim_name IN (
    'Child Support - Formula Worksheet',
    'Child Support - Deviation Due To Denied Parenting Time'
)
  AND dm.damage_component IN (
    'plaintiff_imputed_income',
    'defendant_actual_income',
    'denied_parenting_transfer',
    'restored_parenting_transfer'
  )
ORDER BY dm.damage_component, eq.source_date;
```

### DW5.3 Worked Example Table

| Damage Line | Methodology | Amount | Notes |
| --- | --- | ---: | --- |
| Plaintiff monthly imputed income | historical wages reconstructed for 2026 | $4,503.02 | Use when temporary disruption should not freeze support forever |
| Defendant monthly actual income | documented or inferable 2026 income | $4,968.84 | Compare with disclosure packet |
| Denied-parenting scenario | formula result using distorted overnights | $286.14 | Illustrative monthly transfer |
| Restored-parenting scenario | formula result using equitable schedule | $74.38 | Illustrative baseline if parenting time is restored |
| Distortion delta | $286.14 - $74.38 | $211.76 | Monthly distortion attributable to denied parenting time |

### DW5.4 Integration Points

- Pull income history from **DW2** when job-loss records and pay data drive imputation.
- Push support-delta charts into **DW8** for a one-page deviation exhibit.
- Push distorted-support leverage into **DW7** so settlement discussions can account for future support correction.
- Pair with **DW6** when false or frivolous filings distorted parenting time and therefore distorted support.
- Use **DW1** date windows to prove that the overnight distortion arose during the same 2026 deprivation period.
- Flag **MCL 600.2911** review only if false allegations materially affected employability or credibility in support proceedings.

### DW5.5 Operational Guardrails

- Do not pretend the simplified model is the official worksheet; label it as a litigation-facing calculation framework.
- Do not use denied-parenting overnights as if they reflect a fair long-term status quo.
- Keep imputation logic separate from actual temporary hardship.
- State clearly whether a figure is monthly, weekly, or annualized.
- Verify that every date example stays in 2026.

### DW5.6 Scenario Drill

- If equal parenting time is restored mid-year, split the analysis into pre-restoration and post-restoration support periods.
- If defendant income is uncertain, run low, mid, and high scenarios instead of disguising uncertainty.
- If a referee or court asks for a shorter memo, present the delta table first and append the assumptions sheet.
- If support arrears are at issue later, feed the corrected worksheet into DW8 for judgment and enforcement exhibits.

## DW6: Sanctions & Fee Recovery

**Purpose**

Assemble MCR 2.114 sanctions, fee-shifting schedules, vexatious-conduct documentation, and recoverable-cost ledgers into motion-ready packages.

**Design Pattern**

Misconduct Matrix + Fee Petition Ledger + Motion Packet Composer

**Detailed Description**

1. DW6 is the accountability layer. It captures the money spent because litigation conduct crossed the line from adversarial to sanctionable.
2. The engine focuses on MCR 2.114-style certification problems, frivolous filings, unsupported allegations, needless multiplication of proceedings, and cost-causing conduct that forced duplicative work or hearing attendance.
3. For a pro se litigant, DW6 differentiates between recoverable out-of-pocket costs and time-value proxies used to show the burden imposed by misconduct. That distinction is critical to credibility.
4. The module organizes sanctions proof into conduct blocks: what was filed or done, why it lacked support, what cost it caused, and what authority authorizes relief. This becomes the backbone of a sanctions motion or fee request.
5. DW6 is also a pressure tool. Even when a sanctions motion is not filed immediately, the ledger can reshape settlement leverage in DW7 by showing the real cost of misconduct.
6. The same record may also support related statutory fee theories or bad-faith findings. If a false allegation publication caused separate reputational injury, DW6 can note a **MCL 600.2911** branch without duplicating damages.
7. Where the 2026 case record shows repeated unsupported accusations or process abuse, DW6 can export a chronology that meshes cleanly with DW1's process-deprivation story and DW4's punitive scoring.
8. Its output is a motion-ready damages-plus-fees package: totals, dates, authorities, source documents, and a concise explanation of why compensation or deterrence is warranted.

**Key Operations**

| Operation | Inputs | Output | Evidence Hook |
| --- | --- | --- | --- |
| Conduct identification | filings, hearings, statements | sanction events | docket, transcripts, papers |
| Authority mapping | conduct type + authority | motion sections | MCR 2.114 and related law |
| Fee ledger build | hours, costs, lost wages | recoverable amount schedule | receipts, calendars |
| Pro se burden valuation | time spent + lost work value | settlement / sanctions narrative | work logs |
| Chronology export | dated sanction events | motion exhibit timeline | DW8 |
| Negotiation leverage export | sanctions subtotal | demand letter attachment | DW7 |

**Code Examples**

### DW6.1 Python Calculation Example

```python
sanction_components = {
    "hearing_preparation": 12.6 * 46.80,
    "motion_drafting": 9.4 * 46.80,
    "records_assembly": 7.2 * 32.40,
    "hearing_attendance_lost_wages": 14.5 * 28.85,
    "out_of_pocket_costs": 1388.42,
}

total = round(sum(sanction_components.values()), 2)
print(sanction_components)
print({"sanctions_total": total})
# sanctions_total = $3,069.62
```

### DW6.2 SQL Query Against `claims`, `damages_model`, and `evidence_quotes`

```sql
SELECT
    c.claim_id,
    dm.damage_component,
    dm.amount,
    dm.methodology,
    eq.quote_text,
    eq.source_date
FROM claims c
JOIN damages_model dm ON dm.claim_id = c.claim_id
LEFT JOIN evidence_quotes eq ON eq.claim_id = c.claim_id
WHERE c.claim_name = 'Sanctions / Fee Recovery - MCR 2.114'
  AND dm.damage_component IN (
    'hearing_preparation',
    'motion_drafting',
    'records_assembly',
    'hearing_attendance_lost_wages',
    'out_of_pocket_costs'
  )
ORDER BY eq.source_date;
```

### DW6.3 Worked Example Table

| Damage Line | Methodology | Amount | Notes |
| --- | --- | ---: | --- |
| Hearing preparation | 12.6 hours × $46.80 | $589.68 | Work caused by sanctionable conduct |
| Motion drafting | 9.4 hours × $46.80 | $439.92 | Additional response burden |
| Records assembly | 7.2 hours × $32.40 | $233.28 | Document production and organization time |
| Hearing attendance lost wages | 14.5 hours × $28.85 | $418.33 | Court appearance opportunity cost |
| Out-of-pocket costs | carryover from DW2 legal ledger | $1,388.42 | Direct recoverable expenditures |
| Sanctions subtotal | sum of all sanctions components | $3,069.62 | Motion-ready reimbursement ask |

### DW6.4 Integration Points

- Pull documented costs from **DW2** rather than rebuilding them.
- Push the sanction-event chronology into **DW8** for a sanctions exhibit or hearing binder.
- Push the sanctions subtotal into **DW7** to improve negotiation posture.
- Use **DW1** and **DW4** to explain how process abuse caused both compensatory injury and deterrence concerns.
- Use **DW5** if sanctionable conduct distorted support outcomes or overnights.
- Flag **MCL 600.2911** review when knowingly false accusations were published broadly enough to support a separate reputational-harm lane.

### DW6.5 Operational Guardrails

- Do not call every adverse event sanctionable; identify the rule breach and the causation chain.
- Keep pure reimbursements distinct from deterrence-oriented sanctions.
- Preserve receipts and time logs in the same order as the ledger rows.
- Do not inflate pro se time-value figures; explain that they are burden measures, not disguised attorney fees.
- Use 2026 dates for every worked example and chronology snippet.

### DW6.6 Scenario Drill

- If the court dislikes broad sanctions requests, split the motion into direct costs, lost wages, and reserved deterrence arguments.
- If a single filing generated most of the expense, isolate that filing into its own exhibit bundle.
- If mediation is scheduled first, convert the sanctions ledger into a pressure schedule instead of filing immediately.
- If new misconduct occurs, append rows to the ledger and recompute automatically rather than editing totals by hand.

## DW7: Settlement Intelligence

**Purpose**

Evaluate offers, calculate BATNA, price risk, and generate counter-proposals that account for damages, collectability, support distortion, sanctions pressure, and litigation cost.

**Design Pattern**

Expected Value Engine + BATNA Comparator + Negotiation Band Generator

**Detailed Description**

1. DW7 is where all money narratives converge into decision-making. It asks not only what the case is worth in theory, but what range is rational given proof strength, collection reality, and future cost.
2. The engine imports constitutional, economic, emotional, punitive, sanctions, and child-support deltas. It then applies collectability, litigation-cost burn, and outcome probabilities to create usable settlement bands.
3. This matters in Pigors v Watson because a headline damages number alone does not tell Andrew James Pigors whether to reject, hold, or counter an offer. DW7 turns the litigation record into a strategy instrument.
4. The module supports BATNA comparisons, best-day/worst-day scenario ranges, and cash-versus-structured counteroffer design. It can also isolate which components are non-negotiable and which are bargaining chips.
5. If the record includes false accusation exposure that could separately implicate **MCL 600.2911**, DW7 can model whether that additional lane meaningfully changes settlement leverage.
6. DW7 also recognizes that child-support correction can be economically significant even when the immediate money figure seems smaller than the damages headlines. Long-term support distortion often changes the rational floor.
7. In pretrial negotiations the engine can downshift from a maximalist total to a disciplined ask that still preserves leverage. In mediation it can present staged bands tied to proof strength and collection risk.
8. The output is not just a number; it is a settlement posture with floor, target, ceiling, rationale, and fallback path.

**Key Operations**

| Operation | Inputs | Output | Evidence Hook |
| --- | --- | --- | --- |
| Expected value | probability × recovery - future costs | net litigation value | DW1-DW6 outputs |
| BATNA build | best trial alternative | decision floor | cost-to-trial + collectability |
| Counter-proposal generation | target recovery + concessions | offer language | mediation packet |
| Pressure analysis | sanctions + support delta + punitive exposure | negotiation leverage map | DW4-DW6 |
| Collectability screen | judgment size + enforcement path | realistic range | post-judgment planning |
| Range export | floor / target / ceiling | one-page negotiation chart | DW8 |

**Code Examples**

### DW7.1 Python Calculation Example

```python
compensatory = 208360.04
punitive = 432763.81
future_costs = 6842.17
success_probability = 0.64
punitive_collectability = 0.28

expected_value = (
    success_probability * compensatory
    + punitive_collectability * punitive
    - future_costs
)

settlement_floor = 142119.57
counter_proposal = 292029.10

print({
    "expected_value": round(expected_value, 2),
    "settlement_floor": round(settlement_floor, 2),
    "counter_proposal": round(counter_proposal, 2),
    "monthly_support_delta": 211.76,
})
```

### DW7.2 SQL Query Against `claims`, `damages_model`, and `evidence_quotes`

```sql
SELECT
    c.claim_id,
    dm.damage_component,
    dm.amount,
    dm.methodology,
    eq.quote_text,
    eq.source_date
FROM claims c
JOIN damages_model dm ON dm.claim_id = c.claim_id
LEFT JOIN evidence_quotes eq ON eq.claim_id = c.claim_id
WHERE c.claim_name IN (
    'Settlement Range - Federal / Family Overlay',
    'Support Distortion Leverage',
    'Sanctions Pressure'
)
ORDER BY dm.damage_component, eq.source_date;
```

### DW7.3 Worked Example Table

| Damage Line | Methodology | Amount | Notes |
| --- | --- | ---: | --- |
| Compensatory basket | DW1 + DW2 + DW3 | $208,360.04 | Base recovery without punitive overlay |
| Punitive basket | DW4 balanced scenario (2.077x) | $432,763.81 | Used with a discounted collectability factor |
| Projected future litigation cost | briefing, hearing, discovery, preparation | $6,842.17 | Subtract from decision math |
| Settlement floor | 0.70 constitutional + 0.92 economic + 0.55 emotional - future costs | $142,119.57 | Minimum rational negotiation posture |
| Illustrative counter-proposal | 0.82 compensatory + 0.28 punitive | $292,029.10 | Target counteroffer for serious negotiations |
| Monthly support distortion leverage | $286.14 - $74.38 | $211.76 | Child-support correction adds recurring value |

### DW7.4 Integration Points

- Pull compensatory baselines from **DW1**, **DW2**, and **DW3**.
- Pull punitive scenarios from **DW4** for leverage modeling.
- Pull support-delta effects from **DW5** when future support correction influences the rational floor.
- Pull sanctions totals from **DW6** as immediate pressure in negotiations.
- Push settlement bands to **DW8** so mediation packets include clear floor/target/ceiling visuals.
- Coordinate with post-judgment enforcement logic so offers are judged against realistic collectability, not fantasy totals.

### DW7.5 Operational Guardrails

- Do not compare an offer to the gross headline total alone; compare it to expected net value.
- State any collectability discount explicitly.
- Keep monthly support effects separate from one-time damages.
- Recompute the range whenever a major subtotal changes.
- Use 2026 date anchors in offer narratives and comparison charts.

### DW7.6 Scenario Drill

- If the opposing side offers non-monetary parenting relief, value it separately rather than hiding it inside the dollar comparison.
- If a mediation judge wants a narrow bracket, export floor, target, and walk-away points on one page.
- If trial costs spike after new discovery, update BATNA immediately because the negotiation floor may move.
- If collectability is weak, shift emphasis toward support correction, sanctions reimbursement, and near-term cash components.

## DW8: Damages Exhibit Factory

**Purpose**

Generate tables, charts, per-diem schedules, summary exhibits, and court-ready visual materials that carry all prior module outputs into filings, hearings, mediation, and post-judgment enforcement.

**Design Pattern**

Exhibit Builder + Multi-Module Renderer + Court-Format Exporter

**Detailed Description**

1. DW8 is the presentation engine. It does not invent numbers; it renders verified numbers from DW1 through DW7 into persuasive, readable, and traceable exhibits.
2. The module supports single-page summaries, line-item ledgers, per-diem charts, sanctions timelines, support comparison graphics, and settlement-range dashboards. Every visual is sourced back to a calculation row and an evidentiary hook.
3. For Pigors v Watson, DW8 is responsible for turning the raw calculations into documents a judge, mediator, or opposing party can actually understand without re-performing the math at counsel table.
4. The engine is especially important in a pro se case because clarity often substitutes for staffing. A clean exhibit can accomplish what a long oral explanation cannot.
5. DW8 can also emit post-judgment collections schedules, including what portion of a judgment is compensatory, punitive, fee-based, or recurring support-related. That allows enforcement modules to act on the numbers immediately.
6. When reputational or publication-based harm exists, DW8 can tag a separate **MCL 600.2911** schedule so that defamation-adjacent lines remain visible but segregated from the main basket.
7. The module includes formatting rules for child anonymity, date discipline, and category transparency. It is the last anti-hallucination checkpoint before numbers go into a filing.
8. Its core promise is simple: if DW1-DW7 are correct, DW8 makes them intelligible, court-ready, and strategically useful.

**Key Operations**

| Operation | Inputs | Output | Evidence Hook |
| --- | --- | --- | --- |
| Summary sheet rendering | module subtotals | one-page damages table | DW1-DW7 |
| Per-diem chart export | rates + days | constitutional exhibit | DW1 |
| Ledger table export | economic / sanctions rows | cost exhibit | DW2, DW6 |
| Support comparison chart | denied vs restored | deviation exhibit | DW5 |
| Settlement range card | floor / target / ceiling | mediation handout | DW7 |
| Enforcement-ready breakdown | judgment categories | collection worksheet | post-judgment use |

**Code Examples**

### DW8.1 Python Calculation Example

```python
rows = [
    ("Constitutional", 107193.15),
    ("Economic", 49418.23),
    ("Emotional", 51748.66),
    ("Punitive", 432763.81),
    ("Sanctions", 3069.62),
]

markdown = [
    "| Category | Amount |",
    "| --- | ---: |",
]
for label, amount in rows:
    markdown.append(f"| {label} | ${amount:,.2f} |")

print("\n".join(markdown))
# Use the resulting markdown block as the core of Exhibit 8A.
```

### DW8.2 SQL Query Against `claims`, `damages_model`, and `evidence_quotes`

```sql
SELECT
    dm.damage_component,
    dm.amount,
    dm.methodology,
    c.claim_name,
    eq.quote_text,
    eq.source_date
FROM damages_model dm
JOIN claims c ON c.claim_id = dm.claim_id
LEFT JOIN evidence_quotes eq ON eq.claim_id = dm.claim_id
WHERE dm.case_number = '2024-001507-DC'
ORDER BY c.claim_name, dm.damage_component, eq.source_date;
```

### DW8.3 Worked Example Table

| Damage Line | Methodology | Amount | Notes |
| --- | --- | ---: | --- |
| Constitutional summary card | DW1 total | $107,193.15 | Exhibit 8A line 1 |
| Economic summary card | DW2 total | $49,418.23 | Exhibit 8A line 2 |
| Emotional summary card | DW3 total | $51,748.66 | Exhibit 8A line 3 |
| Punitive summary card | DW4 balanced scenario | $432,763.81 | Exhibit 8A line 4 |
| Sanctions summary card | DW6 total | $3,069.62 | Exhibit 8A line 5 |
| Support distortion card | monthly delta = $211.76 | $211.76 | Exhibit 8B deviation support visual |

### DW8.4 Integration Points

- Consume all line-level exports from **DW1** through **DW7**.
- Publish federal complaint exhibits, sanctions schedules, support comparison sheets, and mediation cards from one shared data structure.
- Hand off summary sheets to filing systems so motions, briefs, and proposed orders cite the same totals.
- Hand off enforcement-ready category splits to garnishment and post-judgment workflows.
- Preserve 2026 date annotations and L.D.W. anonymization at render time, not just at calculation time.
- Use DW8 as the final consistency check before any money number appears in court.

### DW8.5 Operational Guardrails

- Never render a number that cannot be traced back to a module and a method.
- Never show full child names in charts or captions.
- Never hide formula notes from the exhibit manifest.
- Keep recurring monthly amounts visually distinct from one-time damages.
- Preserve date discipline: examples and schedules stay in 2026.

### DW8.6 Scenario Drill

- If the court wants a shorter packet, render a one-page damages summary and place detailed ledgers behind it.
- If mediation requires quick comparison, print floor, target, and total-compensatory cards only.
- If a post-judgment collection action begins, export category splits and judgment interest notes in a separate enforcement exhibit.
- If any subtotal changes, regenerate every chart from source values rather than editing the visual manually.

## Decision Tree

```text
Start
  |
  +-- Is there state action causing family-integrity or due-process deprivation in 2026?
  |      |
  |      +-- Yes --> Run DW1 --> Are there deliberate / reckless indicators?
  |      |                       |
  |      |                       +-- Yes --> Add DW4 punitive scoring
  |      |                       +-- No  --> Keep compensatory-only federal basket
  |      |
  |      +-- No --> Skip constitutional basket and start with DW2 / DW3 / DW5 as needed
  |
  +-- Is there measurable lost income, housing loss, or direct spending?
  |      |
  |      +-- Yes --> Run DW2 --> export ledger to DW8 and settlement floor to DW7
  |
  +-- Is there documented trauma, counseling, sleep disruption, or journal proof?
  |      |
  |      +-- Yes --> Run DW3 --> check non-duplication with DW1 / DW2
  |
  +-- Is support distorted by denied parenting time or disputed income?
  |      |
  |      +-- Yes --> Run DW5 --> compare denied-parenting worksheet vs restored schedule
  |
  +-- Is there sanctionable conduct, frivolous filings, or cost-causing abuse?
  |      |
  |      +-- Yes --> Run DW6 --> quantify fee recovery under MCR 2.114
  |
  +-- Are you evaluating an offer or preparing mediation?
  |      |
  |      +-- Yes --> Run DW7 --> set floor / target / ceiling / walk-away
  |
  +-- Need filing-ready visuals, charts, or tables?
         |
         +-- Yes --> Run DW8 --> generate damages summary, support chart, sanctions ledger
```

## Cross-Module Integration Patterns

| Pattern | Trigger | Module Flow | Product |
| --- | --- | --- | --- |
| Federal constitutional complaint | State action + separation + incarceration | DW1 → DW3 → DW4 → DW8 | Complaint damages section plus per-diem exhibit |
| Family-court financial injury packet | Job loss, housing loss, litigation costs | DW2 → DW6 → DW8 | Fee/cost exhibit and supporting ledger |
| Support-distortion proof set | Denied parenting time affects overnights | DW2 → DW5 → DW8 | Side-by-side worksheet and deviation narrative |
| Mediation valuation stack | Offer received or conference scheduled | DW1 + DW2 + DW3 + DW4 + DW5 + DW6 → DW7 → DW8 | Floor/target/ceiling card with rationale |
| Post-judgment collections handoff | Judgment entered or payment default | DW2 + DW6 + DW7 → DW8 | Enforcement-ready category split and collection worksheet |
| Defamation-adjacent branch | False accusation publication with measurable harm | DW2 / DW3 / DW6 + MCL 600.2911 review → DW7 / DW8 | Segregated reputational-harm schedule |

1. **DW1 + DW4 = constitutional deterrence stack.** Use this when the record shows more than harm; it shows disregard. The constitutional subtotal anchors the injury, while the punitive multiplier explains why mere compensation is inadequate.
2. **DW2 + DW6 = reimbursement warfare stack.** This pairing is the fastest route to concrete money because receipts, mileage, transcripts, and documented lost wages often persuade more quickly than abstract narratives.
3. **DW2 + DW5 = support realism stack.** Lost jobs and distorted overnights change support math. Running these together prevents a false status quo from hardening into a worksheet.
4. **DW3 + DW7 = mediation empathy stack.** Emotional distress alone can sound subjective. Emotional distress paired with a disciplined settlement model becomes harder to dismiss because the suffering is translated into decision-grade numbers.
5. **DW6 + DW7 = pressure stack.** A sanctions-ready ledger often shifts negotiations even before a sanctions motion is filed. Opposing parties discount abstract threats; they pay attention to dated and priced misconduct.
6. **DW8 = the convergence checkpoint.** Every module should flow through DW8 before filing so line items, dates, labels, and category boundaries remain consistent across complaint, motion, brief, and exhibit set.
7. **Damages-to-filing pipeline.** Facts and evidence enter DW1-DW7 as calculation inputs, are standardized into line items, then rendered in DW8 into federal complaint sections, state-court motions, mediation cards, and post-judgment worksheets.
8. **Anti-duplication discipline.** If a treatment invoice appears in DW3 as emotional-support proof and in DW2 as direct out-of-pocket loss, add a note or choose one lane. The skill should maximize credibility, not gross totals.
9. **Authority discipline.** Use **42 USC §1983** for constitutional deprivation, **MCR 2.114** for sanctions framing, and invoke **MCL 600.2911** only where the facts support a separate reputational or false-publication branch.
10. **2026-only discipline.** All examples, charts, schedules, and code snippets in this forge use 2026 dates so the generated work product is internally consistent and audit-friendly.

## Domain Applications

### Application 1: Federal §1983 Damages Narrative

Use **DW1**, **DW3**, **DW4**, and **DW8** to build a federal damages section that shows: (a) the 2026 deprivation window, (b) the enhanced liberty loss during the 59-day incarceration period, (c) evidence-backed emotional distress, and (d) a punitive multiplier grounded in deliberate or reckless indifference. The result is a complaint-ready section plus a one-page exhibit that a federal judge can audit line by line.

**Workflow**
- Calculate the constitutional basket in DW1 using 2026 day counts.
- Quantify emotional distress in DW3 with counseling and journal support.
- Score punitive exposure in DW4 using deterrence factors.
- Render the numbers in DW8 as a complaint appendix and hearing demonstrative.

### Application 2: Motion for Sanctions and Fee Recovery

Use **DW2**, **DW6**, and **DW8** to assemble a state-court sanctions packet. The packet can price hearing preparation, motion drafting, records assembly, lost wages from attendance, filing fees, service fees, copy costs, mileage, and transcript expenses while tying each row to MCR 2.114-style misconduct allegations.

**Workflow**
- Pull hard costs and receipts from DW2.
- Convert sanctionable conduct into a priced chronology in DW6.
- Render the packet in DW8 with a summary page and a backup ledger.

### Application 3: Child Support Deviation Brief

Use **DW2**, **DW5**, and **DW8** when denied parenting time has distorted the support picture. The goal is not merely to compute support, but to show how the distorted overnight count and temporary income collapse produce an unfair worksheet if accepted at face value.

**Workflow**
- Reconstruct 2026 income in DW2.
- Run denied-parenting versus restored-parenting support scenarios in DW5.
- Render the monthly distortion delta in DW8 as a side-by-side exhibit.

### Application 4: Mediation / Settlement Counter-Proposal Packet

Use **DW1** through **DW7** together when a real offer arrives or mediation is set. This is the full financial warfare posture: prove the damages, discipline the punitive ask, quantify sanctions pressure, account for support distortion, subtract future litigation cost, then publish a floor, target, and counter-proposal that are rational and hard to dismiss.

**Workflow**
- Import compensatory totals from DW1, DW2, and DW3.
- Add punitive scenarios from DW4 and pressure values from DW6.
- Add support delta from DW5 and compute BATNA in DW7.
- Publish the mediation card and backup schedules in DW8.

## Quick Reference Card

```text
+======================================================================================================+
|                                       FORGE-DAMAGES-WARFARE                                         |
+======================================================================================================+
| Core Case: Pigors v Watson | Child: L.D.W. | Parenting Deprivation: 233 days | Jail: 59 days           |
| DW1 Constitutional: $107,193.15  | DW2 Economic: $49,418.23  | DW3 Emotional: $51,748.66            |
| DW4 Punitive: $432,763.81 @ 2.077x | DW5 Support Delta: $211.76/month               |
| DW6 Sanctions: $3,069.62 | DW7 Settlement Floor: $142,119.57 | Counter: $292,029.10 |
| Authorities: 42 USC §1983 | MCR 2.114 | MCL 600.2911 (only when reputational false-publication facts fit) |
| Outputs: complaint damages sections, sanctions ledgers, support deviation charts, mediation cards, exhibits |
| Discipline: 2026-only examples | L.D.W. initials only | show formulas, rates, dates, and evidence hooks      |
+======================================================================================================+
```
