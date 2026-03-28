---
name: FORGE-FAMILY-LAW-FORTRESS
description: >-
  Unified Michigan family law defense engine for custody, parenting time, PPO, FOC, GAL,
  best-interest scoring, parental alienation documentation, compliance tracking, and
  separation-harm quantification in Pigors v Watson and similarly structured family cases.
category: litigation
version: "1.0.0"
triggers:
  - best interest factor analysis
  - custody modification motion
  - parenting time enforcement
  - FOC 89 complaint
  - PPO termination motion
  - parental alienation evidence
  - GAL appointment request
  - established custodial environment
  - child support modification
  - makeup parenting time plan
  - Vodvarka proper cause
  - Michigan family law defense
metadata:
  tier: FORGE
  fused_skills: 8
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-03-27
  forge_class: litigation-family-law
  emergent_capability: Michigan family law total defense orchestration across custody, PPO, FOC, alienation, contempt, and quantified child-harm tracking
---

# 🏰 FORGE-FAMILY-LAW-FORTRESS

> **Michigan Family Law Total Defense Engine (Ω-Δ99)**

## Overview

| Attribute | Value |
|---|---|
| Tier | FORGE |
| Domain | Michigan family law litigation, enforcement, and defensive strategy |
| Scope | Custody, parenting time, PPO, FOC, GAL, child support, best-interest scoring, parental alienation, contempt, and quantified separation harms |
| Emergent Capability | Custody-to-filing fortress that converts raw evidence, denied-contact timelines, and FOC/docket signals into hearing-ready Michigan family law outputs |

## Forged from 8 Skills

| Source Skill | Core Contribution | Fortress Upgrade |
|---|---|---|
| child-best-interest | MCL 722.23 factor analysis, scoring, and evidence-weighting across all 12 statutory factors. | Turns factor analysis into a reusable score lattice that feeds modification, contempt, and harm outputs. |
| family-law-guardian | Custody, parenting time, and GAL motion logic with Michigan family court framing. | Expands motion drafting into a threshold-aware custody and GAL architecture specific to Michigan practice. |
| parental-alienation-detector | Baker's 17 strategies mapped to evidence patterns, timelines, and witness narratives. | Elevates incident spotting into Baker-mapped evidentiary pattern proof for hearings and evaluator use. |
| harm-tracker | Separation-day accounting, child harm categorization, and damages-oriented consequence logging. | Transforms separation metrics into factor-linked, damages-aware child harm narratives. |
| contempt-prosecutor | Show-cause logic, contempt drafting, purge conditions, and sanction sequencing. | Adds escalation logic that converts repeated violations into show-cause packages with purge conditions. |
| order-compliance-monitor | Order extraction, obligation tracking, missed-exchange logging, and deviation scoring. | Adds persistent order-state monitoring so every denial and deviation can be tied back to enforceable language. |
| docket-monitor | Hearing tracking, motion status awareness, and calendar-aligned litigation sequencing. | Adds timing intelligence so outputs are filed before hearings, objection windows, or FOC deadlines are missed. |
| foc-specialist | FOC complaint routing, recommendation analysis, objections, and enforcement escalation. | Adds Muskegon-style FOC workflow intelligence and objection strategy to administrative enforcement paths. |

## Architecture

```text
                           ┌───────────────────────────────────────┐
                           │ FORGE-FAMILY-LAW-FORTRESS (Ω-Δ99)    │
                           │ Michigan Family Law Total Defense     │
                           └───────────────────────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
      ┌───────▼────────┐          ┌──────▼───────┐           ┌──────▼────────┐
      │ Evidence Layer │          │ Timing Layer │           │ Order Layer    │
      │ DB + Timeline  │          │ Docket + FOC │           │ Orders + PPO   │
      └───────┬────────┘          └──────┬───────┘           └──────┬────────┘
              │                          │                           │
   ┌──────────▼──────────┐    ┌─────────▼─────────┐      ┌─────────▼─────────┐
   │ FL1 Best Interest   │    │ FL3 Parenting     │      │ FL4 PPO Defense   │
   │ Analyzer            │    │ Time Enforcer     │      │ & Termination     │
   └──────────┬──────────┘    └─────────┬─────────┘      └─────────┬─────────┘
              │                          │                           │
   ┌──────────▼──────────┐    ┌─────────▼─────────┐      ┌─────────▼─────────┐
   │ FL2 Custody         │◄───┤ FL7 FOC           │─────►│ FL6 Contempt      │
   │ Modification Engine │    │ Intelligence      │      │ & Enforcement     │
   └──────────┬──────────┘    └─────────┬─────────┘      └─────────┬─────────┘
              │                          │                           │
       ┌──────▼────────┐        ┌────────▼────────┐          ┌──────▼────────┐
       │ FL5 Parental  │        │ FL8 Separation  │          │ Output Stack  │
       │ Alienation    │        │ Harm Counter    │          │ motions/FOC   │
       │ Documenter    │        │                 │          │ objections/QA │
       └───────────────┘        └─────────────────┘          └───────────────┘
```

## Global Case Context

This forge is anchored to the following Michigan case context and every example in this skill uses that same frame unless explicitly noted otherwise:

- **Case:** Pigors v Watson, No. 2024-001507-DC, 14th Circuit Court, Muskegon County
- **PPO Case:** No. 2023-5907-PP (Lane D)
- **Judge:** Hon. Jenny L. McNeill
- **Child:** L.D.W. (initials only per MCR 8.119(H))
- **Plaintiff/Father:** Andrew James Pigors, pro se
- **Defendant/Mother:** Emily A. Watson, 2160 Garland Dr, Norton Shores, MI 49441
- **FOC:** Pamela Rusco, 990 Terrace St, Muskegon, MI 49442
- **Key facts used across modules:** 230+ days parenting time denied; ex parte orders entered Aug. 8, 2026 without notice; HealthWest evaluation cleared Father; 2,404 documented alienation incidents in the database

## Anti-Hallucination Guardrails

1. Never use any banned names or identifiers: **Jane Berry**, **Patricia Berry**, **P35878**, **91% alienation score**, **Lincoln David Watson**, or **Ron Berry Esq**.
2. All dates in generated examples, outputs, and mock filings must be in **2026**.
3. All statistics must cite or describe the underlying query that produced them; unsupported percentages are prohibited.
4. When presenting alienation totals, use raw incident counts or query-backed rollups, not confidence theater.
5. Always keep the child's name as **L.D.W.** only.
6. When referencing custody burdens, explicitly state whether an established custodial environment exists and what burden follows.
7. Cite Michigan authority accurately: **MCL 722.23**, **MCL 722.25**, **MCL 722.27**, **MCL 722.27a**, **Vodvarka v Grasmeyer, 259 Mich App 499 (2003)**, **Pierron v Pierron, 486 Mich 81 (2010)**, **Brown v Loveman, 260 Mich App 576 (2004)**, **Fletcher v Fletcher, 447 Mich 871 (1994)**, **Shade v Wright, 291 Mich App 17 (2010)**, **MCR 3.707**, and **MCL 764.15b**.

## Operating Philosophy

FORGE-FAMILY-LAW-FORTRESS treats Michigan family litigation as a linked system rather than isolated filings. Parenting-time denial affects best-interest factor scoring. Alienation patterns affect custody modification thresholds. FOC inaction affects contempt timing. PPO weaponization can distort custody perception. Separation days accumulate into child harm, urgency, and even downstream damages analysis. The forge therefore orchestrates each family-law function as a connected pipeline rather than a silo.

## Michigan Family Law Authority Core

- **MCL 722.23** supplies the 12 best-interest factors and remains the merits engine of custody analysis.
- **MCL 722.25** and **MCL 722.27a** anchor parenting-time rights, modification logic, and enforcement framing.
- **MCL 722.27** governs custody modification and requires threshold analysis before the court reopens custody.
- **Vodvarka v Grasmeyer, 259 Mich App 499 (2003)** is the controlling threshold authority for proper cause/change of circumstances in custody modification.
- **Pierron v Pierron, 486 Mich 81 (2010)** reinforces due process concerns when major custody-affecting decisions occur without meaningful notice and opportunity to be heard.
- **Brown v Loveman, 260 Mich App 576 (2004)** is central for parenting-time framing and distinguishes between custody and parenting-time analysis.
- **Fletcher v Fletcher, 447 Mich 871 (1994)** remains foundational for factor-specific best-interest review.
- **Shade v Wright, 291 Mich App 17 (2010)** helps explain lighter threshold dynamics in parenting-time modification compared with custody modification.
- **MCR 3.707** structures PPO hearing, termination, and modification workflows.
- **MCL 764.15b** is relevant when PPO violation allegations become criminal or contempt-adjacent leverage points.

## Module Map

| Module | Name | Primary Product | Core Authority |
|---|---|---|---|
| FL1 | Best Interest Factor Analyzer | Score all 12 MCL 722.23 factors with evidence citations from DB and build hearing-ready factor narratives. | MCL 722.23; Fletcher |
| FL2 | Custody Modification Engine | Run Vodvarka proper cause/change-of-circumstances analysis, determine ECE, and assemble motion-ready custody arguments. | MCL 722.27; Vodvarka; Pierron; Shade |
| FL3 | Parenting Time Enforcer | Convert denied parenting time facts into FOC complaints, makeup requests, and phased restoration plans. | MCL 722.25; MCL 722.27a; Brown |
| FL4 | PPO Defense & Termination | Challenge or modify PPO-related restraints using MCR 3.707, changed circumstances, and misuse evidence. | MCR 3.707; MCL 764.15b |
| FL5 | Parental Alienation Documenter | Map Baker's 17 strategies to evidence clusters and produce expert-ready alienation narratives. | Baker strategies + factor integration |
| FL6 | Contempt & Enforcement | Turn repeated violations into show-cause motions, contempt theories, and purge-condition proposals. | Contempt/show-cause practice anchored to clear order language |
| FL7 | FOC Intelligence Module | Analyze FOC recommendations, complaints, delays, and objection pathways in Muskegon County practice. | FOC complaint and objection workflow |
| FL8 | Separation Harm Counter | Maintain the real-time denied-contact day counter and tie harms to best-interest factors and damages models. | Temporal harm accounting + best-interest linkage |

## FL1: Best Interest Factor Analyzer

**Purpose:** Score all 12 MCL 722.23 factors with evidence citations from DB and build hearing-ready factor narratives.

**Design Pattern:** Evidence-scored decision matrix

### Detailed Description

FL1 operates as the MCL 722.23, Fletcher v Fletcher, and factor-by-factor scoring for L.D.W. using custody-lane evidence. layer inside the fortress. In Pigors v Watson, this module assumes the 14th Circuit record includes denied parenting time, FOC interactions, the Aug. 8, 2026 ex parte orders, and query-accessible evidence collections such as `evidence_quotes`, `best_interest_factors`, and `harm_tracker`.

The module is not a generic family-law checklist. It is designed to transform raw record material into Michigan-specific outputs that can withstand scrutiny by Hon. Jenny L. McNeill while preserving a clean record for appellate or collateral review. Every output must stay query-backed, avoid the banned hallucination set, and preserve L.D.W.'s initials only.

### Key Operations

- Normalize factor labels (a)-(l) and pull all evidence_quote rows tied to each factor.
- Assign provisional score: father+, neutral, mother+, or mixed with weight notes and witness credibility flags.
- Generate factor synopsis with statutes, dates, and contradictions suitable for a motion, trial brief, or hearing binder.
- Export factor grid that can feed FL2 custody modification logic and FL8 harm calculations.

### Michigan Case Example

- Example 1: Factor (j) analysis pulls denied parenting-time incidents, blocked communications, and 2026 exchange failures to argue that Mother is not willing to facilitate a close and continuing relationship between L.D.W. and Father.
- Example 2: Factor (g) analysis references the 2026 HealthWest evaluation clearing Father, preventing stigma-based narratives from substituting for admissible proof.

### Python Code Example

```python
import sqlite3
from collections import defaultdict

conn = sqlite3.connect(r"D:\LITIGATIONOS_DATA\litigation.db")
conn.row_factory = sqlite3.Row

query = """
SELECT factor_code, citation, quote, source_doc, event_date
FROM best_interest_factors
WHERE case_number = '2024-001507-DC'
  AND child_initials = 'L.D.W.'
ORDER BY factor_code, event_date;
"""

factor_map = defaultdict(list)
for row in conn.execute(query):
    factor_map[row["factor_code"]].append(dict(row))

for factor_code, rows in factor_map.items():
    print(f"{factor_code}: {len(rows)} records")
    for item in rows[:3]:
        print("  -", item["event_date"], item["citation"], item["source_doc"])
```

### SQL Query Example

```sql
SELECT factor_code, COUNT(*) AS evidence_count
FROM best_interest_factors
WHERE case_number = '2024-001507-DC'
  AND child_initials = 'L.D.W.'
GROUP BY factor_code
ORDER BY factor_code;
```

### Integration Points

- FL2 uses factor output to argue why modification advances the child's best interests.
- FL5 enriches factors (j) and (k) with alienation and false-allegation patterns.
- FL8 injects separation-day harms into factors (b), (d), (h), and (j).

### Output Contracts

- `factor_grid`: structured scorecard for factors (a)-(l) with evidence count, narrative, and citation anchors.
- `factor_memo`: paragraph-ready factor analysis for motion or brief use.

### Failure Modes and Safeguards

- Do not score factors from assumptions; require query-backed evidence and flag thin factors as underdeveloped.
- Do not collapse factor (j) into every factor; note overlap but preserve factor-specific analysis.

## FL2: Custody Modification Engine

**Purpose:** Run Vodvarka proper cause/change-of-circumstances analysis, determine ECE, and assemble motion-ready custody arguments.

**Design Pattern:** Threshold-gated litigation pipeline

### Detailed Description

FL2 operates as the MCL 722.27, MCL 722.27a, Vodvarka, Pierron, and Shade with hearing sequencing in Pigors v Watson. layer inside the fortress. In Pigors v Watson, this module assumes the 14th Circuit record includes denied parenting time, FOC interactions, the Aug. 8, 2026 ex parte orders, and query-accessible evidence collections such as `evidence_quotes`, `best_interest_factors`, and `harm_tracker`.

The module is not a generic family-law checklist. It is designed to transform raw record material into Michigan-specific outputs that can withstand scrutiny by Hon. Jenny L. McNeill while preserving a clean record for appellate or collateral review. Every output must stay query-backed, avoid the banned hallucination set, and preserve L.D.W.'s initials only.

### Key Operations

- Test threshold evidence for proper cause and change of circumstances under Vodvarka.
- Determine whether an established custodial environment exists with one or both parents and set burden of proof.
- Draft relief options: temporary makeup plan, interim evidentiary hearing, or full custody modification.
- Cross-check notice, due process, and ex parte defects arising from Aug. 8, 2026 orders.

### Michigan Case Example

- Example 1: The 230+ days of denied parenting time in 2026 are treated as more than isolated friction; when paired with alienation evidence and ex parte disruption, they support a Vodvarka threshold argument that the conditions surrounding custody have materially changed.
- Example 2: If the evidence shows L.D.W. previously looked to both parents for guidance, discipline, and comfort before the 2026 separation escalation, FL2 flags a dual established custodial environment issue and raises the burden accordingly.

### Python Code Example

```python
import sqlite3

conn = sqlite3.connect(r"D:\LITIGATIONOS_DATA\litigation.db")
conn.row_factory = sqlite3.Row

vodvarka_query = """
SELECT event_date, category, quote, source_doc
FROM evidence_quotes
WHERE case_number = '2024-001507-DC'
  AND (
       quote LIKE '%parenting time denied%'
       OR quote LIKE '%ex parte%'
       OR quote LIKE '%HealthWest%'
       OR quote LIKE '%alienation%'
  )
  AND event_date >= '2026-01-01'
ORDER BY event_date;
"""

threshold_events = list(conn.execute(vodvarka_query))
print("Threshold event count:", len(threshold_events))
for row in threshold_events[:10]:
    print(row["event_date"], row["category"], row["source_doc"])
```

### SQL Query Example

```sql
SELECT event_date, category, source_doc, quote
FROM evidence_quotes
WHERE case_number = '2024-001507-DC'
  AND event_date >= '2026-01-01'
  AND (quote LIKE '%ex parte%' OR quote LIKE '%parenting time denied%' OR quote LIKE '%HealthWest%')
ORDER BY event_date;
```

### Integration Points

- Consumes FL1 factor scoring as the merits layer after threshold gate is satisfied.
- Consumes FL3 denial logs to prove a durable change affecting the child.
- Consumes FL4 PPO artifacts where PPO weaponization distorted custody outcomes.

### Output Contracts

- `vodvarka_threshold_report`: proper-cause/change-of-circumstances analysis.
- `ece_assessment`: established custodial environment determination and burden summary.

### Failure Modes and Safeguards

- Do not skip the Vodvarka threshold when the requested relief changes custody rather than mere parenting time.
- Do not state a burden of proof without first addressing established custodial environment.

## FL3: Parenting Time Enforcer

**Purpose:** Convert denied parenting time facts into FOC complaints, makeup requests, and phased restoration plans.

**Design Pattern:** Order-to-remedy enforcement loop

### Detailed Description

FL3 operates as the MCL 722.25, MCL 722.27a, Brown v Loveman, and FOC enforcement mechanics for 230+ denied days. layer inside the fortress. In Pigors v Watson, this module assumes the 14th Circuit record includes denied parenting time, FOC interactions, the Aug. 8, 2026 ex parte orders, and query-accessible evidence collections such as `evidence_quotes`, `best_interest_factors`, and `harm_tracker`.

The module is not a generic family-law checklist. It is designed to transform raw record material into Michigan-specific outputs that can withstand scrutiny by Hon. Jenny L. McNeill while preserving a clean record for appellate or collateral review. Every output must stay query-backed, avoid the banned hallucination set, and preserve L.D.W.'s initials only.

### Key Operations

- Extract each denied exchange, identify violated order language, and group by pattern or escalation event.
- Draft FOC 89 complaint packets with exhibits, missed dates, and requested enforcement remedies.
- Generate makeup parenting time calculations and graduated restoration calendars.
- Escalate persistent denial to FL6 contempt when FOC processes are ignored or stalled.

### Michigan Case Example

- Example 1: Each missed exchange in 2026 is logged against the active parenting-time order, grouped into an FOC 89 packet, and paired with requested makeup dates rather than merely recited as grievance history.
- Example 2: The module can generate a graduated restoration proposal: supervised neutral-site exchange for two weeks, then midweek dinner time, then alternating weekends, all keyed to compliance milestones.

### Python Code Example

```python
import sqlite3

conn = sqlite3.connect(r"D:\LITIGATIONOS_DATA\litigation.db")
conn.row_factory = sqlite3.Row

denied_query = """
SELECT event_date, exchange_type, ordered_time, compliance_status, source_doc
FROM harm_tracker
WHERE case_number = '2024-001507-DC'
  AND harm_type = 'denied_parenting_time'
  AND event_date BETWEEN '2026-01-01' AND '2026-12-31'
ORDER BY event_date;
"""

denied_rows = list(conn.execute(denied_query))
print(f"Denied exchanges in 2026: {len(denied_rows)}")
requested_makeup_days = len(denied_rows)
print(f"Suggested minimum makeup periods: {requested_makeup_days}")
```

### SQL Query Example

```sql
SELECT event_date, ordered_time, compliance_status, source_doc
FROM harm_tracker
WHERE case_number = '2024-001507-DC'
  AND harm_type = 'denied_parenting_time'
ORDER BY event_date;
```

### Integration Points

- Feeds denial metrics into FL1 factors (a), (b), (d), (j), and (l).
- Feeds persistent refusal patterns into FL6 contempt pleadings.
- Feeds daily separation totals into FL8 damages and harm models.

### Output Contracts

- `foc89_packet`: denial schedule, exhibits, and requested enforcement action.
- `makeup_schedule`: date-specific restoration plan.

### Failure Modes and Safeguards

- Do not present denied parenting time as an undifferentiated pile of grievances; tie each denial to order language and remedy.
- Do not overpromise FOC relief; preserve a clean escalation path to contempt.

## FL4: PPO Defense & Termination

**Purpose:** Challenge or modify PPO-related restraints using MCR 3.707, changed circumstances, and misuse evidence.

**Design Pattern:** Restraining-order challenge framework

### Detailed Description

FL4 operates as the MCR 3.707 and MCL 764.15b in the context of PPO Case No. 2023-5907-PP and family-court spillover. layer inside the fortress. In Pigors v Watson, this module assumes the 14th Circuit record includes denied parenting time, FOC interactions, the Aug. 8, 2026 ex parte orders, and query-accessible evidence collections such as `evidence_quotes`, `best_interest_factors`, and `harm_tracker`.

The module is not a generic family-law checklist. It is designed to transform raw record material into Michigan-specific outputs that can withstand scrutiny by Hon. Jenny L. McNeill while preserving a clean record for appellate or collateral review. Every output must stay query-backed, avoid the banned hallucination set, and preserve L.D.W.'s initials only.

### Key Operations

- Map PPO allegations to documentary contradictions, cleared evaluations, and timeline anomalies.
- Draft motions to terminate, modify, or narrow PPO restrictions based on changed circumstances in 2026.
- Document weaponization patterns where PPO filings or allegations are leveraged to suppress parenting time.
- Prepare cross-examination tracks separating safety issues from litigation advantage maneuvers.

### Michigan Case Example

- Example 1: FL4 compares PPO allegations against timeline contradictions and the 2026 HealthWest clearance to argue that the continued PPO scope is unsupported or overbroad.
- Example 2: The module documents how the PPO case, No. 2023-5907-PP, may have been used to reinforce parenting-time barriers beyond any legitimate safety need, especially after custody disputes intensified in 2026.

### Python Code Example

```python
import sqlite3

conn = sqlite3.connect(r"D:\LITIGATIONOS_DATA\litigation.db")
conn.row_factory = sqlite3.Row

ppo_query = """
SELECT event_date, quote, source_doc, citation
FROM evidence_quotes
WHERE case_number IN ('2024-001507-DC', '2023-5907-PP')
  AND (
       quote LIKE '%PPO%'
       OR quote LIKE '%HealthWest%'
       OR quote LIKE '%cleared%'
       OR quote LIKE '%no notice%'
  )
ORDER BY event_date;
"""

for row in conn.execute(ppo_query):
    print(row["event_date"], row["source_doc"], row["citation"])
```

### SQL Query Example

```sql
SELECT event_date, source_doc, citation, quote
FROM evidence_quotes
WHERE case_number IN ('2024-001507-DC', '2023-5907-PP')
  AND (quote LIKE '%PPO%' OR quote LIKE '%changed circumstances%' OR quote LIKE '%HealthWest%')
ORDER BY event_date;
```

### Integration Points

- Supplies FL2 with due-process and weaponization evidence affecting custody orders.
- Supplies FL5 with false-allegation nodes that align with alienation strategies.
- Supplies FL6 with criminal or civil contempt escalation points when PPO terms are distorted.

### Output Contracts

- `ppo_changed_circumstances_matrix`: pre/post circumstances table for 2026 motion work.
- `ppo_contradiction_chart`: allegation-to-record conflict sheet.

### Failure Modes and Safeguards

- Do not attack PPOs with rhetoric alone; document changed circumstances and contradictions.
- Do not minimize legitimate safety concerns; separate disproven claims from still-viable restrictions.

## FL5: Parental Alienation Documenter

**Purpose:** Map Baker's 17 strategies to evidence clusters and produce expert-ready alienation narratives.

**Design Pattern:** Pattern-detection and evidentiary clustering

### Detailed Description

FL5 operates as the 2,404 documented alienation incidents, Baker's strategies, and child-centered presentation for L.D.W. layer inside the fortress. In Pigors v Watson, this module assumes the 14th Circuit record includes denied parenting time, FOC interactions, the Aug. 8, 2026 ex parte orders, and query-accessible evidence collections such as `evidence_quotes`, `best_interest_factors`, and `harm_tracker`.

The module is not a generic family-law checklist. It is designed to transform raw record material into Michigan-specific outputs that can withstand scrutiny by Hon. Jenny L. McNeill while preserving a clean record for appellate or collateral review. Every output must stay query-backed, avoid the banned hallucination set, and preserve L.D.W.'s initials only.

### Key Operations

- Tag evidence into Baker strategy buckets such as badmouthing, limiting contact, or creating dependency conflicts.
- Build incident chronologies with severity counts based on DB query output, not unsupported percentages.
- Generate alienation memo sections suitable for GAL, evaluator, or evidentiary hearing review.
- Link each pattern to best-interest harms and parenting-time interference.

### Michigan Case Example

- Example 1: FL5 maps incidents to Baker strategies such as badmouthing, limiting contact, creating the impression of danger, forcing loyalty conflict, and rewarding rejection behavior.
- Example 2: Using the 2,404 documented incidents, the module produces a query-backed incident matrix organized by date, strategy, source, and child-impact note rather than unsupported percentages.

### Python Code Example

```python
import sqlite3

conn = sqlite3.connect(r"D:\LITIGATIONOS_DATA\litigation.db")
conn.row_factory = sqlite3.Row

strategy_query = """
SELECT baker_strategy, COUNT(*) AS incidents
FROM evidence_quotes
WHERE case_number = '2024-001507-DC'
  AND topic = 'parental_alienation'
  AND event_date BETWEEN '2026-01-01' AND '2026-12-31'
GROUP BY baker_strategy
ORDER BY incidents DESC;
"""

for row in conn.execute(strategy_query):
    print(f"{row['baker_strategy']}: {row['incidents']}")
```

### SQL Query Example

```sql
SELECT baker_strategy, COUNT(*) AS incidents
FROM evidence_quotes
WHERE case_number = '2024-001507-DC'
  AND topic = 'parental_alienation'
GROUP BY baker_strategy
ORDER BY incidents DESC;
```

### Integration Points

- Enriches FL1 factors (a), (b), (f), (h), (j), and (k).
- Supports FL2 threshold proof by showing a durable pattern rather than isolated disputes.
- Feeds FL8 with harm categories tied to emotional and developmental injury.

### Output Contracts

- `baker_strategy_matrix`: incidents grouped by strategy with raw counts.
- `alienation_timeline`: date-sorted chronology with source documents.

### Failure Modes and Safeguards

- Do not diagnose; document patterns and behaviors.
- Do not use unsupported percentages or the banned 91% figure.

## FL6: Contempt & Enforcement

**Purpose:** Turn repeated violations into show-cause motions, contempt theories, and purge-condition proposals.

**Design Pattern:** Escalation ladder with cure gates

### Detailed Description

FL6 operates as the Parenting-time contempt, order disobedience, and enforcement sequencing when voluntary compliance fails. layer inside the fortress. In Pigors v Watson, this module assumes the 14th Circuit record includes denied parenting time, FOC interactions, the Aug. 8, 2026 ex parte orders, and query-accessible evidence collections such as `evidence_quotes`, `best_interest_factors`, and `harm_tracker`.

The module is not a generic family-law checklist. It is designed to transform raw record material into Michigan-specific outputs that can withstand scrutiny by Hon. Jenny L. McNeill while preserving a clean record for appellate or collateral review. Every output must stay query-backed, avoid the banned hallucination set, and preserve L.D.W.'s initials only.

### Key Operations

- Identify clear order language, violation dates, notice proof, and available sanctions.
- Draft show-cause motion sections with exhibit index and requested purge conditions.
- Recommend remedies such as makeup time, fee shifting, counseling compliance, or communication protocols.
- Differentiate curable noncompliance from chronic obstruction for judicial framing.

### Michigan Case Example

- Example 1: FL6 uses repeated 2026 violations of parenting-time orders to build a show-cause motion seeking makeup time, precise future exchange rules, and fee-shifting.
- Example 2: When the opposing side claims confusion, FL6 distinguishes accidental noncompliance from a repeated pattern evidenced by multiple denied exchanges, FOC complaints, and ignored restoration efforts.

### Python Code Example

```python
import sqlite3

conn = sqlite3.connect(r"D:\LITIGATIONOS_DATA\litigation.db")
conn.row_factory = sqlite3.Row

contempt_query = """
SELECT event_date, quote, source_doc
FROM evidence_quotes
WHERE case_number = '2024-001507-DC'
  AND topic IN ('order_violation', 'denied_parenting_time', 'foc_noncompliance')
  AND event_date >= '2026-01-01'
ORDER BY event_date;
"""

rows = list(conn.execute(contempt_query))
print("Potential contempt evidence rows:", len(rows))
for row in rows[:8]:
    print(row["event_date"], row["source_doc"])
```

### SQL Query Example

```sql
SELECT event_date, topic, source_doc, quote
FROM evidence_quotes
WHERE case_number = '2024-001507-DC'
  AND topic IN ('order_violation', 'denied_parenting_time', 'foc_noncompliance')
ORDER BY event_date;
```

### Integration Points

- Consumes FL3 logs and FL7 FOC history to show repeated noncompliance.
- Supports FL2 by proving the existing arrangement is unstable and harmful.
- Uses FL8 harm totals to explain urgency and child impact.

### Output Contracts

- `show_cause_packet`: contempt-ready violation bundle.
- `purge_condition_menu`: compliant cure options tied to the violation history.

### Failure Modes and Safeguards

- Do not file contempt without identifying clear order language and notice.
- Do not seek sanctions untethered to achievable purge conditions unless the record warrants stronger relief.

## FL7: FOC Intelligence Module

**Purpose:** Analyze FOC recommendations, complaints, delays, and objection pathways in Muskegon County practice.

**Design Pattern:** Administrative-intelligence feedback loop

### Detailed Description

FL7 operates as the FOC officer Pamela Rusco, recommendation parsing, complaint routing, and objection preservation. layer inside the fortress. In Pigors v Watson, this module assumes the 14th Circuit record includes denied parenting time, FOC interactions, the Aug. 8, 2026 ex parte orders, and query-accessible evidence collections such as `evidence_quotes`, `best_interest_factors`, and `harm_tracker`.

The module is not a generic family-law checklist. It is designed to transform raw record material into Michigan-specific outputs that can withstand scrutiny by Hon. Jenny L. McNeill while preserving a clean record for appellate or collateral review. Every output must stay query-backed, avoid the banned hallucination set, and preserve L.D.W.'s initials only.

### Key Operations

- Catalog all FOC contacts, recommendation dates, and stated reasons for action or inaction.
- Compare FOC outputs against the record, statute, and hearing evidence for omissions or bias.
- Draft objection points, supplementation requests, and hearing issues tied to FOC activity.
- Coordinate with docket data so FOC issues are raised before hearings, not after avoidable delay.

### Michigan Case Example

- Example 1: FL7 catalogues every FOC interaction with Pamela Rusco in 2026, compares stated conclusions with record evidence, and identifies omissions that should be preserved in objections or hearing argument.
- Example 2: It highlights where FOC enforcement mechanisms were invoked but did not restore parenting time, strengthening judicial escalation arguments.

### Python Code Example

```python
import sqlite3

conn = sqlite3.connect(r"D:\LITIGATIONOS_DATA\litigation.db")
conn.row_factory = sqlite3.Row

foc_query = """
SELECT event_date, source_doc, quote
FROM evidence_quotes
WHERE case_number = '2024-001507-DC'
  AND (
       quote LIKE '%Pamela Rusco%'
       OR quote LIKE '%Friend of the Court%'
       OR topic = 'foc_recommendation'
  )
  AND event_date BETWEEN '2026-01-01' AND '2026-12-31'
ORDER BY event_date;
"""

for row in conn.execute(foc_query):
    print(row["event_date"], row["source_doc"])
```

### SQL Query Example

```sql
SELECT event_date, source_doc, quote
FROM evidence_quotes
WHERE case_number = '2024-001507-DC'
  AND (quote LIKE '%Pamela Rusco%' OR quote LIKE '%Friend of the Court%' OR topic = 'foc_recommendation')
ORDER BY event_date;
```

### Integration Points

- Feeds FL3 with complaint status and enforcement track history.
- Feeds FL2 and FL6 with bias, omission, or delay narratives where relevant.
- Feeds FL1 with evidence affecting factors (j) and (l), especially facilitation and stability.

### Output Contracts

- `foc_contact_log`: dated list of FOC actions, statements, and pending items.
- `foc_objection_points`: preserved challenges to recommendations or omissions.

### Failure Modes and Safeguards

- Do not assume FOC neutrality or bias; prove omissions or inconsistencies with specific comparisons.
- Do not lose objection deadlines by separating FOC review from docket monitoring.

## FL8: Separation Harm Counter

**Purpose:** Maintain the real-time denied-contact day counter and tie harms to best-interest factors and damages models.

**Design Pattern:** Temporal harm accumulator

### Detailed Description

FL8 operates as the 230+ denied days baseline, 2026 day counts, and linkage between daily separation and factor-specific harm. layer inside the fortress. In Pigors v Watson, this module assumes the 14th Circuit record includes denied parenting time, FOC interactions, the Aug. 8, 2026 ex parte orders, and query-accessible evidence collections such as `evidence_quotes`, `best_interest_factors`, and `harm_tracker`.

The module is not a generic family-law checklist. It is designed to transform raw record material into Michigan-specific outputs that can withstand scrutiny by Hon. Jenny L. McNeill while preserving a clean record for appellate or collateral review. Every output must stay query-backed, avoid the banned hallucination set, and preserve L.D.W.'s initials only.

### Key Operations

- Calculate separation days from order-violation events through the present motion date in 2026.
- Categorize harms by emotional, developmental, educational, relational, and procedural impact.
- Translate accumulated days into charts usable by damages or urgency-oriented filings.
- Publish factor-specific harm summaries so the counter is not just numeric but legally meaningful.

### Michigan Case Example

- Example 1: FL8 calculates separation days from the most recent enforceable denial sequence and updates the total as of the motion date in 2026.
- Example 2: It links prolonged separation to factors (a), (b), (d), (h), and (j), ensuring the day counter is legally meaningful rather than rhetorical.

### Python Code Example

```python
import sqlite3
from datetime import date

conn = sqlite3.connect(r"D:\LITIGATIONOS_DATA\litigation.db")
conn.row_factory = sqlite3.Row

today = date(2026, 12, 31)
counter_query = """
SELECT MIN(event_date) AS first_denial,
       MAX(event_date) AS last_denial,
       COUNT(*) AS denial_events,
       SUM(CASE WHEN harm_type = 'denied_parenting_time' THEN 1 ELSE 0 END) AS denied_contacts
FROM harm_tracker
WHERE case_number = '2024-001507-DC'
  AND event_date BETWEEN '2026-01-01' AND '2026-12-31';
"""

row = conn.execute(counter_query).fetchone()
print(today.isoformat(), dict(row))
```

### SQL Query Example

```sql
SELECT harm_type, COUNT(*) AS harm_events
FROM harm_tracker
WHERE case_number = '2024-001507-DC'
  AND event_date BETWEEN '2026-01-01' AND '2026-12-31'
GROUP BY harm_type
ORDER BY harm_events DESC;
```

### Integration Points

- Supplies FL1 and FL2 with concrete child-impact evidence.
- Supplies FL3 and FL6 with urgency metrics for enforcement relief.
- Supplies downstream damages calculators with query-backed day counts and harm categories.

### Output Contracts

- `separation_counter`: current denied-contact day total for 2026 calculation windows.
- `harm_map`: harms keyed to best-interest factors and evidence sources.

### Failure Modes and Safeguards

- Do not publish a separation figure without showing the query window or event basis.
- Do not treat day counts as self-executing legal arguments; tie them to factor harms.

## MCL 722.23 Factor-by-Factor Template

Use this template whenever FL1 or FL2 needs a full custody merits section. Populate every field with query-backed evidence. If a factor is thin, say so and identify the next evidence pull rather than speculating.

### Factor (a)

**Statutory Text:** The love, affection, and other emotional ties existing between the parties involved and the child.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Query relationship evidence, denied-contact logs, school/medical interactions, and child statements showing attachment to Father and disruption caused by interference.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (a) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (b)

**Statutory Text:** The capacity and disposition of the parties involved to give the child love, affection, and guidance and to continue the education and raising of the child in the child's religion or creed, if any.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Measure who promotes guidance and who undermines it through blocked calls, missed exchanges, and narrative contamination.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (b) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (c)

**Statutory Text:** The capacity and disposition of the parties involved to provide the child with food, clothing, medical care, and other material needs.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Pull provider evidence, insurance participation, HealthWest compliance, and support for routine appointments.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (c) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (d)

**Statutory Text:** The length of time the child has lived in a stable, satisfactory environment, and the desirability of maintaining continuity.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Compare genuine stability against litigation-created isolation, especially after ex parte orders entered on Aug. 8, 2026.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (d) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (e)

**Statutory Text:** The permanence, as a family unit, of the existing or proposed custodial home or homes.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Review housing continuity, household composition, and reliability of proposed schedules.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (e) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (f)

**Statutory Text:** The moral fitness of the parties involved.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Frame around truthfulness, manipulation, and litigation conduct rather than moralizing irrelevancies.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (f) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (g)

**Statutory Text:** The mental and physical health of the parties involved.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Include HealthWest evaluation results clearing Father, plus any documented stability concerns tied to conduct rather than stigma.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (g) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (h)

**Statutory Text:** The home, school, and community record of the child.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Assess disruption caused by denied parenting time, missed events, and breakdown of father-child community continuity.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (h) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (i)

**Statutory Text:** The reasonable preference of the child, if the court considers the child to be of sufficient age to express preference.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Note sealed/in camera treatment and avoid coaching; preserve only lawful preference handling.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (i) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (j)

**Statutory Text:** The willingness and ability of each of the parties to facilitate and encourage a close and continuing parent-child relationship between the child and the other parent.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Central factor in this case; map denial logs, alienation incidents, and communication obstruction.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (j) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (k)

**Statutory Text:** Domestic violence, regardless of whether the violence was directed against or witnessed by the child.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Separate genuine safety proof from unsupported accusations or weaponized PPO narratives.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (k) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

### Factor (l)

**Statutory Text:** Any other factor considered by the court to be relevant to a particular child custody dispute.

**Template Fields:**

- Father Position:
- Mother Position:
- Key Evidence Citations:
- Credibility Notes:
- Harm Linkage:
- Preliminary Score:
- Hearing Theme:

**How To Populate:** Capture due process defects, ex parte irregularities, FOC omissions, evaluator findings, and extraordinary separation harms.

**Case-Specific Prompt:**

- In Pigors v Watson, evaluate factor (l) using 2026-only evidence, emphasizing the 230+ denied days, Aug. 8, 2026 ex parte orders, HealthWest clearance, and any factor-specific alienation or FOC evidence affecting L.D.W.

## Decision Tree

```text
START
  │
  ├── Is the requested relief changing custody? ── Yes ──► FL2 Vodvarka Threshold
  │                                                 │
  │                                                 ├── Proper cause / change shown? ── No ──► Narrow to parenting-time or evidence development
  │                                                 │
  │                                                 └── Yes ──► ECE analysis ► FL1 merits scoring ► motion drafting
  │
  ├── Is the main injury denied parenting time? ── Yes ──► FL3 enforcement pipeline
  │                                                 │
  │                                                 ├── FOC remedy likely effective? ── Yes ──► FOC 89 / makeup time / restoration plan
  │                                                 │
  │                                                 └── No or failed ──► FL6 contempt escalation
  │
  ├── Is a PPO blocking contact or being used as leverage? ── Yes ──► FL4 PPO review
  │                                                         │
  │                                                         ├── Changed circumstances in 2026? ── Yes ──► modify/terminate under MCR 3.707
  │                                                         │
  │                                                         └── No ──► narrow scope, preserve contradictions, route facts to FL2/FL5
  │
  ├── Is alienation a dominant theme? ── Yes ──► FL5 strategy mapping ► FL1/FL2 integration
  │
  ├── Are FOC recommendations incomplete or biased? ── Yes ──► FL7 objection and comparison workflow
  │
  ├── Need urgency or damages framing? ── Yes ──► FL8 separation harm counter
  │
  └── Final output ► filing stack / hearing memo / cross-exam binder / emergency restoration plan
```

## Cross-Module Integration Patterns

### Threshold-to-Merits Pipeline

FL8 day counts and FL3 denial logs establish durable change; FL5 converts incidents into patterns; FL2 then applies Vodvarka and ECE gates before FL1 presents merits under MCL 722.23.

**Operational Steps:**

1. Pull the smallest query set that proves the event pattern.
2. Validate date range, case number, and child initials.
3. Route evidence to the controlling threshold module first.
4. Promote only threshold-cleared facts into motion or hearing outputs.
5. Preserve objection, docket, and FOC timing dependencies before filing.

### Administrative-to-Judicial Escalation

FL7 tracks FOC inputs, FL3 packages FOC 89 materials, and FL6 escalates repeated noncompliance into show-cause relief with purge conditions.

**Operational Steps:**

1. Pull the smallest query set that proves the event pattern.
2. Validate date range, case number, and child initials.
3. Route evidence to the controlling threshold module first.
4. Promote only threshold-cleared facts into motion or hearing outputs.
5. Preserve objection, docket, and FOC timing dependencies before filing.

### Protection-Order Spillover Control

FL4 isolates PPO facts and changed circumstances so PPO allegations do not silently contaminate custody, parenting-time, or factor scoring analyses.

**Operational Steps:**

1. Pull the smallest query set that proves the event pattern.
2. Validate date range, case number, and child initials.
3. Route evidence to the controlling threshold module first.
4. Promote only threshold-cleared facts into motion or hearing outputs.
5. Preserve objection, docket, and FOC timing dependencies before filing.

### Evidence-to-Damages Bridge

FL8 converts separation time into child-harm metrics, then hands quantified totals to downstream damages workflows while FL1 uses the same harms in factor analysis.

**Operational Steps:**

1. Pull the smallest query set that proves the event pattern.
2. Validate date range, case number, and child initials.
3. Route evidence to the controlling threshold module first.
4. Promote only threshold-cleared facts into motion or hearing outputs.
5. Preserve objection, docket, and FOC timing dependencies before filing.

### Docket-Aware Filing Sequencing

Docket-monitor inputs coordinate hearing dates, motion cutoffs, and FOC windows so each module outputs material in the correct order for the 14th Circuit.

**Operational Steps:**

1. Pull the smallest query set that proves the event pattern.
2. Validate date range, case number, and child initials.
3. Route evidence to the controlling threshold module first.
4. Promote only threshold-cleared facts into motion or hearing outputs.
5. Preserve objection, docket, and FOC timing dependencies before filing.

## Custody-to-Filing Pipeline

1. **Evidence Pull: Query `evidence_quotes`, `best_interest_factors`, and `harm_tracker` for 2026 rows tied to custody, denied parenting time, alienation, FOC, and PPO facts.**
2. **Threshold Classification: Send the issue through FL2 to determine whether it is a custody-modification problem, a parenting-time problem, or both.**
3. **Environment Determination: Run ECE logic before stating a burden of proof.**
4. **Merits Scoring: Use FL1 to score MCL 722.23 factors with precise citations and identified evidentiary gaps.**
5. **Alienation Overlay: Use FL5 to enrich factors (a), (b), (f), (h), (j), and (l) where repeated interference is documented.**
6. **Enforcement Overlay: Use FL3 and FL6 to decide whether the filing should request immediate makeup time, show-cause relief, or both.**
7. **Administrative Overlay: Use FL7 to capture FOC activity, omissions, and objection points.**
8. **Urgency Layer: Use FL8 to quantify separation harms and explain why relief cannot be delayed.**
9. **Final Output: Produce a motion, brief, exhibit list, FOC packet, or hearing outline aligned to the next docket event.**

## Domain Applications

### Emergency Restoration After Ex Parte Disruption

Use FL2 + FL3 + FL8 to show that the Aug. 8, 2026 ex parte orders caused prolonged separation, justify immediate makeup parenting time, and require a noticed evidentiary hearing under Pierron-style due process principles.

**Case Use:**

- Court: 14th Circuit Court, Muskegon County
- Case anchor: Pigors v Watson, No. 2024-001507-DC
- Child reference: L.D.W.
- Year lock: 2026

### Alienation-Focused Custody Modification

Use FL5 to convert 2,404 documented incidents into admissible pattern proof, then feed those results into FL1 and FL2 for a Vodvarka threshold and best-interest argument centered on factor (j).

**Case Use:**

- Court: 14th Circuit Court, Muskegon County
- Case anchor: Pigors v Watson, No. 2024-001507-DC
- Child reference: L.D.W.
- Year lock: 2026

### PPO Narrowing To Remove Litigation Weaponization

Use FL4 with HealthWest-clearing evidence and contradiction mapping to seek modification or termination under MCR 3.707 while preserving child safety and restoring lawful communication channels.

**Case Use:**

- Court: 14th Circuit Court, Muskegon County
- Case anchor: Pigors v Watson, No. 2024-001507-DC
- Child reference: L.D.W.
- Year lock: 2026

### FOC Escalation To Contempt Pipeline

Use FL7 to document FOC complaint history, FL3 to prove continuing denial, and FL6 to escalate to show-cause relief when administrative remedies do not restore parenting time.

**Case Use:**

- Court: 14th Circuit Court, Muskegon County
- Case anchor: Pigors v Watson, No. 2024-001507-DC
- Child reference: L.D.W.
- Year lock: 2026

## Child Support Modification Overlay

Although the fortress is primarily organized around custody, parenting time, PPO, FOC, alienation, and enforcement, it also includes a child-support modification layer. This overlay is triggered when parenting-time restoration, income imputation, or corrected overnight counts materially affect the Michigan Child Support Formula.

- Use parenting-time restoration outputs from FL3 to update overnight assumptions.
- Use FL2 threshold findings to show why support should not be calculated on a distorted custody picture created by denial of contact.
- Use FL7 to inspect whether FOC support recommendations omitted changed income, altered parenting time, or imputation issues.
- Use FL8 to explain how prolonged denial can distort ordinary child-support assumptions by collapsing a parent-child relationship the court should be protecting.

### Child Support Query Example

```sql
SELECT parent_label, reported_income, imputed_income, overnights_assumed, calculation_date
FROM evidence_quotes
WHERE case_number = '2024-001507-DC'
  AND topic = 'child_support_inputs'
  AND event_date BETWEEN '2026-01-01' AND '2026-12-31'
ORDER BY calculation_date;
```

```python
import sqlite3

conn = sqlite3.connect(r"D:\\LITIGATIONOS_DATA\\litigation.db")
conn.row_factory = sqlite3.Row

support_query = """
SELECT parent_label, reported_income, imputed_income, overnights_assumed, calculation_date
FROM evidence_quotes
WHERE case_number = '2024-001507-DC'
  AND topic = 'child_support_inputs'
  AND event_date BETWEEN '2026-01-01' AND '2026-12-31'
ORDER BY calculation_date;
"""

for row in conn.execute(support_query):
    print(dict(row))
```

## GAL Appointment Logic

The fortress includes a GAL request overlay for cases where the child's independent interests are not being adequately surfaced by the current process. In Pigors v Watson, a GAL request may become strategically appropriate if alienation allegations, repeated denied contact, or procedural irregularities create a record where neutral child-focused investigation is necessary.

**Trigger Conditions:**

- Persistent, query-backed conflict over what L.D.W. is being told about Father.
- Repeated denial of contact that ordinary FOC processes have not repaired.
- Need for neutral assessment distinct from party narratives after the Aug. 8, 2026 ex parte disruption.
- Need to evaluate best-interest impacts without public overexposure of the child.

**GAL Motion Elements:**

- Why neutral investigation is necessary
- What questions the GAL should answer
- What evidence the GAL should review
- How the GAL request fits with MCL 722.23 factors and the present custody dispute
- Why lesser mechanisms have not resolved the issue

## Baker's 17 Strategy Mapping Template

### Baker Strategy 1: Badmouthing the targeted parent

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 2: Limiting contact

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 3: Interfering with communication

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 4: Creating the impression the targeted parent is dangerous

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 5: Forcing the child to choose

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 6: Telling the child the targeted parent does not love them

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 7: Confiding in the child about litigation or adult grievances

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 8: Forcing the child to reject the targeted parent

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 9: Asking the child to spy on the targeted parent

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 10: Asking the child to keep secrets from the targeted parent

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 11: Referring to the targeted parent by first name instead of mom/dad role

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 12: Withholding medical, school, or social information

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 13: Changing the child's name or identity cues to weaken parent bond

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 14: Cultivating dependency and loyalty conflict

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 15: Rewarding rejection behavior

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 16: Creating a false narrative of abandonment

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

### Baker Strategy 17: Rewriting family history to marginalize the targeted parent

- Evidence query:
- Source documents:
- Child-impact note:
- Best-interest factor linkage:

## Separation Day Counter to Damages Linkage

The separation counter does not itself award damages, but it generates the metric that downstream damages modules use. Within the family-law context, the counter chiefly explains urgency, child harm, and the relational degradation produced by prolonged denied contact. When paired with separate damages logic, it can also support broader constitutional or tort-adjacent narratives in other lanes.

### Linkage Formula

1. Query denied-contact events from `harm_tracker` for 2026.
2. Convert event clusters into a running total of separation days or denied-contact periods.
3. Map the total to best-interest harms: attachment, guidance, stability, school/community continuity, and facilitation.
4. Export the total with citations so downstream damages modules receive a verified metric, not a floating narrative claim.
5. Preserve the distinction between child-harm description and any separate monetary valuation.

### Damages Bridge Query

```sql
SELECT COUNT(*) AS denied_days,
       MIN(event_date) AS first_denial,
       MAX(event_date) AS last_denial
FROM harm_tracker
WHERE case_number = '2024-001507-DC'
  AND harm_type = 'denied_parenting_time'
  AND event_date BETWEEN '2026-01-01' AND '2026-12-31';
```

### Harm-by-Factor Bridge Query

```sql
SELECT factor_code, COUNT(*) AS hits
FROM best_interest_factors
WHERE case_number = '2024-001507-DC'
  AND event_date BETWEEN '2026-01-01' AND '2026-12-31'
GROUP BY factor_code
ORDER BY factor_code;
```

## Rapid Response Playbooks

### Playbook A: Emergency Parenting-Time Restoration

1. Run FL3 denied-contact query.
2. Update FL8 day count.
3. Check FL7 for pending FOC complaint posture.
4. If ongoing denial persists, build FL6 show-cause request with makeup time and immediate interim relief.

### Playbook B: Full Custody Modification

1. Use FL2 to test Vodvarka threshold.
2. Determine ECE and burden.
3. Run FL1 all-factor analysis.
4. Overlay FL5 alienation evidence and FL8 harms.

### Playbook C: PPO Narrowing or Termination

1. Run FL4 changed-circumstances matrix.
2. Pull HealthWest-clearing evidence.
3. Identify whether PPO restrictions still affect exchange or communication.
4. Package modified-relief proposal under MCR 3.707.

### Playbook D: FOC Recommendation Challenge

1. Use FL7 to compare FOC reasoning to evidence quotes.
2. Preserve omissions and contradictions.
3. Route outcome to FL3 or FL2 depending on whether issue is enforcement or custody merits.
4. Align objections with the next hearing date from docket intelligence.

## Quick Reference Card

```text
+--------------------------------------------------------------------------------------+
|                     FORGE-FAMILY-LAW-FORTRESS QUICK REFERENCE                        |
+--------------------------------------------------------------------------------------+
| INPUTS : orders | evidence_quotes | best_interest_factors | harm_tracker | docket events | FOC outputs |
| CORE   : FL1 factors | FL2 modification | FL3 parenting time | FL4 PPO | FL5 alienation | FL6 contempt | FL7 FOC | FL8 harms |
| KEY LAW: MCL 722.23 | MCL 722.25 | MCL 722.27 | MCL 722.27a | MCR 3.707 | Vodvarka | Pierron | Fletcher | Brown | Shade |
| CASE   : Pigors v Watson, No. 2024-001507-DC | PPO No. 2023-5907-PP | Hon. Jenny L. McNeill | L.D.W. |
| DO NOT : use banned names, unsupported percentages, or non-query-backed statistics   |
| OUTPUT : factor grid | motion logic | FOC 89 packet | contempt stack | PPO motion | alienation memo | harm timeline |
+--------------------------------------------------------------------------------------+
```

## Usage Notes

- Always begin with the controlling legal threshold, not the desired remedy.
- Treat denied parenting time as both an enforcement issue and a best-interest issue when the record supports it.
- Use raw counts, dates, and citations from the database. Avoid unsupported narrative inflation.
- Keep every output safe for court filing by using 2026 dates, accurate captions, and initials-only treatment for L.D.W.
- Preserve appellate-grade records: identify where notice was lacking, where FOC action was incomplete, and where order language was violated.

## Final Forge Doctrine

FORGE-FAMILY-LAW-FORTRESS is designed to function as a total defense engine, not a single-motion writer. Its central doctrine is that Michigan family-law disputes become tractable when each fact is routed through the correct threshold, authority, and evidentiary lens. In Pigors v Watson, that means denied parenting time is never just counted, alienation is never just alleged, PPOs are never just attacked rhetorically, and FOC outputs are never just accepted at face value. Everything is tied back to the statute, the record, the child, and the next procedural move.

## Module Checklists

### FL1 Checklist

- [FL1-01] Confirm Best Interest Factor Analyzer input set item 1 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL1-02] Confirm Best Interest Factor Analyzer input set item 2 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL1-03] Confirm Best Interest Factor Analyzer input set item 3 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL1-04] Confirm Best Interest Factor Analyzer input set item 4 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL1-05] Confirm Best Interest Factor Analyzer input set item 5 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL1-06] Confirm Best Interest Factor Analyzer input set item 6 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.

### FL2 Checklist

- [FL2-01] Confirm Custody Modification Engine input set item 1 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL2-02] Confirm Custody Modification Engine input set item 2 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL2-03] Confirm Custody Modification Engine input set item 3 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL2-04] Confirm Custody Modification Engine input set item 4 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL2-05] Confirm Custody Modification Engine input set item 5 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL2-06] Confirm Custody Modification Engine input set item 6 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.

### FL3 Checklist

- [FL3-01] Confirm Parenting Time Enforcer input set item 1 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL3-02] Confirm Parenting Time Enforcer input set item 2 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL3-03] Confirm Parenting Time Enforcer input set item 3 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL3-04] Confirm Parenting Time Enforcer input set item 4 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL3-05] Confirm Parenting Time Enforcer input set item 5 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL3-06] Confirm Parenting Time Enforcer input set item 6 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.

### FL4 Checklist

- [FL4-01] Confirm PPO Defense & Termination input set item 1 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL4-02] Confirm PPO Defense & Termination input set item 2 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL4-03] Confirm PPO Defense & Termination input set item 3 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL4-04] Confirm PPO Defense & Termination input set item 4 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL4-05] Confirm PPO Defense & Termination input set item 5 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL4-06] Confirm PPO Defense & Termination input set item 6 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.

### FL5 Checklist

- [FL5-01] Confirm Parental Alienation Documenter input set item 1 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL5-02] Confirm Parental Alienation Documenter input set item 2 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL5-03] Confirm Parental Alienation Documenter input set item 3 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL5-04] Confirm Parental Alienation Documenter input set item 4 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL5-05] Confirm Parental Alienation Documenter input set item 5 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL5-06] Confirm Parental Alienation Documenter input set item 6 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.

### FL6 Checklist

- [FL6-01] Confirm Contempt & Enforcement input set item 1 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL6-02] Confirm Contempt & Enforcement input set item 2 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL6-03] Confirm Contempt & Enforcement input set item 3 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL6-04] Confirm Contempt & Enforcement input set item 4 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL6-05] Confirm Contempt & Enforcement input set item 5 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL6-06] Confirm Contempt & Enforcement input set item 6 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.

### FL7 Checklist

- [FL7-01] Confirm FOC Intelligence Module input set item 1 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL7-02] Confirm FOC Intelligence Module input set item 2 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL7-03] Confirm FOC Intelligence Module input set item 3 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL7-04] Confirm FOC Intelligence Module input set item 4 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL7-05] Confirm FOC Intelligence Module input set item 5 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL7-06] Confirm FOC Intelligence Module input set item 6 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.

### FL8 Checklist

- [FL8-01] Confirm Separation Harm Counter input set item 1 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL8-02] Confirm Separation Harm Counter input set item 2 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL8-03] Confirm Separation Harm Counter input set item 3 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL8-04] Confirm Separation Harm Counter input set item 4 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL8-05] Confirm Separation Harm Counter input set item 5 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.
- [FL8-06] Confirm Separation Harm Counter input set item 6 is dated in 2026, linked to Pigors v Watson or PPO No. 2023-5907-PP as appropriate, and supported by a retrievable source.

