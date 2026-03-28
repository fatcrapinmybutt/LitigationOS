---
name: FORGE-IMPEACHMENT-DESTROYER
description: >-
  A FORGE-tier impeachment, deposition, witness profiling, transcript analysis,
  expert challenge, and adversary prediction superskill for Michigan family-law
  litigation. It fuses contradiction detection, MRE 613 charting, cross-
  examination script generation, credibility dossier construction, deposition
  warfare planning, transcript intelligence extraction, MRE 702/703 expert
  reliability attacks, and opponent-response forecasting into one court-focused
  engine for Pigors v Watson and similarly structured custody matters.
category: litigation
version: "1.0.0"
triggers:
  - impeachment chart
  - prior inconsistent statement
  - cross examination script
  - witness credibility dossier
  - deposition outline
  - transcript analysis
  - judicial bias marker
  - contradiction matrix
  - MRE 613 foundation
  - expert witness challenge
  - adversary response prediction
  - Michigan family law impeachment
metadata:
  tier: FORGE
  fused_skills: 8
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-03-27
  forge_class: litigation-impeachment
  emergent_capability: impeachment cascade orchestration across transcripts, witnesses, exhibits, and predicted counters
---

# 💀 FORGE-IMPEACHMENT-DESTROYER
> **Cross-Examination & Credibility Annihilation Engine (Ω-Δ99)**

This FORGE-tier superskill unifies impeachment analysis, cross-examination scripting,
deposition warfare, transcript intelligence, witness credibility modeling, expert
reliability attacks, and adversary prediction for Michigan family-law litigation.
It is designed for high-discipline use in **Pigors v Watson, No. 2024-001507-DC,
14th Circuit Court, Muskegon County**, while remaining reusable across adjacent
custody, parenting-time, and credibility-heavy disputes.
## Overview

| Field | Value |
|---|---|
| Tier | FORGE |
| Domain | Michigan family law litigation / impeachment / cross-examination |
| Scope | Contradictions, MRE 613 charts, cross scripts, dossiers, depositions, transcripts, expert challenges, adversary prediction |
| Emergent Capability | Impeachment cascade orchestration across evidence, testimony, exhibits, and forecasted resistance |
## Michigan Case Context Anchors

| Item | Context |
|---|---|
| Case | Pigors v Watson, No. 2024-001507-DC |
| Court | 14th Circuit Court, Muskegon County |
| Judge | Hon. Jenny L. McNeill |
| Child Reference Rule | Use `L.D.W.` only; never use a full child name per MCR 8.119(H) |
| Plaintiff | Andrew James Pigors (pro se) |
| Defendant | Emily A. Watson, 2160 Garland Dr, Norton Shores, MI 49441 |
| Former Attorney | Jennifer Barnes (P55406) — WITHDRAWN |
| Third-Party Concern | Ronald Berry is a **non-attorney** partner of Emily and is related to the judge's spouse |
| FOC | Pamela Rusco, 990 Terrace St, Muskegon, MI 49442 |
## Anti-Hallucination Guardrails

- Never use the prohibited names or credentials identified in the FORGE request.
- Never write a full child name; use `L.D.W.` only.
- All example dates in this file are set in **2026**.
- Any count, ratio, contradiction score, or trend statement must be tied to an explicit DB query.
- The examples below are **query-driven templates** for `litigation_context.db`; do not convert an illustrative row into a claimed fact without running the shown SQL or Python.
- The presence of a contradiction does not automatically prove admissibility, materiality, or judicial persuasiveness; each module preserves those distinctions.
## Forged from 8 Skills

| # | Source Skill | Core Contribution |
|---|---|---|
| 1 | impeachment-commander | MRE 613 impeachment charts and contradiction mapping |
| 2 | deposition-prep | Topic outlines, sequencing, and impeachment document identification |
| 3 | witness-profiler | Credibility scoring, motive mapping, and prior statement tracking |
| 4 | transcript-analyzer | Testimony, objections, rulings, and bias-marker extraction |
| 5 | hearing-prep | Cross themes, objection hooks, and hearing-day execution logic |
| 6 | evidence-warfare-commander | Evidence triage, gap analysis, and exhibit prioritization |
| 7 | opposing-counsel-intelligence | Adversary filing patterns, argument habits, and weak points |
| 8 | adversary-war-room | Predicted responses, counter-moves, and vulnerability mapping |

## Architecture

```text
                              ┌──────────────────────────────┐
                              │  Evidence / Transcript Feed  │
                              │  evidence_quotes + filings   │
                              └──────────────┬───────────────┘
                                             │
                                             ▼
                     ┌─────────────────────────────────────────────┐
                     │ ID1 CONTRADICTION DETECTION ENGINE          │
                     │ actor resolution • issue tagging • scoring  │
                     └──────────────┬──────────────────────────────┘
                                    │ contradiction bundles
                    ┌───────────────┼───────────────────────┐
                    │               │                       │
                    ▼               ▼                       ▼
     ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
     │ ID2 MRE 613 CHARTS  │  │ ID4 CREDIBILITY     │  │ ID6 TRANSCRIPT      │
     │ foundation matrix   │  │ DOSSIERS            │  │ INTELLIGENCE        │
     └──────────┬──────────┘  └──────────┬──────────┘  └──────────┬──────────┘
                │                        │                        │
                └──────────────┬─────────┴─────────┬──────────────┘
                               │                   │
                               ▼                   ▼
                 ┌────────────────────────┐   ┌────────────────────────┐
                 │ ID3 CROSS SCRIPT       │   │ ID5 DEPOSITION WARFARE │
                 │ COMMIT→PIN→CONFRONT    │   │ topic outlines + traps │
                 │ →EXHIBIT               │   └──────────┬─────────────┘
                 └──────────┬─────────────┘              │
                            │                            │
                            ├──────────────┐             │
                            ▼              ▼             ▼
                   ┌────────────────┐  ┌────────────────────────┐
                   │ ID7 EXPERT     │  │ ID8 ADVERSARY          │
                   │ CHALLENGE      │  │ PREDICTION MATRIX      │
                   └───────┬────────┘  └────────────┬───────────┘
                           │                        │
                           └──────────┬─────────────┘
                                      ▼
                       ┌──────────────────────────────────┐
                       │ Hearing Packet / Deposition Pack │
                       │ Cross scripts • charts • exhibits│
                       │ preservation notes • counters    │
                       └──────────────────────────────────┘
```
## ID1: Contradiction Detection Engine

### Purpose
Cross-reference all witness, party, expert, and transcript statements by actor and issue; locate inconsistencies; assign severity scores; and feed downstream impeachment workflows.

### Design Pattern
Entity-resolution pipeline + temporal contradiction graph + severity scoring rubric.

### Governing Michigan Evidence Focus
MRE 607, MRE 613, and the credibility framing limits of MRE 608/609.

### Detailed Description
- ID1 is the intake valve for the entire FORGE. It takes raw assertions from pleadings, emails, text messages, hearings, depositions, police reports, FOC communications, and expert materials, then normalizes them into actor-action-time-position tuples.
- In Pigors v Watson, the engine should treat Emily A. Watson, Andrew James Pigors, Pamela Rusco, Ronald Berry, retained experts, and Hon. Jenny L. McNeill as distinct actors with role tags and source provenance. The child must always appear as `L.D.W.` only.
- The scoring rubric should elevate contradictions that touch parenting-time denial, safety narratives, gatekeeping, concealment of communications, or procedural irregularities. It should downgrade cosmetic wording differences that do not change the material proposition.
- Every contradiction record should preserve the exact source text, source type, date, author, context, issue label, and whether extrinsic proof is already exhibit-ready.

### Structured Inputs

| Input Channel | Typical Records | Why It Matters |
|---|---|---|
| `evidence_quotes` | messages, transcript extracts, filing quotes, emails | supplies exact language for contradiction and confrontation |
| `contradictions` | normalized conflict pairs | preserves proposition-level inconsistency logic |
| `impeachment_items` | chart rows, exhibit links, use cases | moves analysis into ready-to-use hearing artifacts |
| transcript packets | page/line testimony, objections, rulings | supplies prior statements and preservation hooks |
| hearing notes | objections, judicial concerns, theory notes | sharpens live execution discipline |
### Key Operations
1. Resolve aliases and speaker identity while blocking prohibited hallucinated names.
2. Normalize date references to 2026 format for timeline-safe comparison.
3. Compare statement A and statement B at the proposition level, not keyword level.
4. Tag contradiction type: direct denial, omission, reversal, timing conflict, motive conflict, or expert-method conflict.
5. Score severity on materiality, clarity, corroboration, and hearing usefulness.
6. Link contradictions to available exhibits from evidence_quotes and impeachment_items.
7. Emit witness-specific contradiction bundles for MRE 613 chart generation.
8. Flag contradictions requiring additional foundation before extrinsic proof is used.

### Michigan Family Law Example Threads
- **Example 1.** Example query-driven scenario: a 2026 text extracted into `evidence_quotes` states that Emily A. Watson blocked a parenting exchange, while later testimony denies interference. ID1 should surface both lines side-by-side and classify the conflict as a material parenting-time contradiction.
- **Example 2.** If Ronald Berry appears in a message chain discussing exchange logistics while a witness later minimizes his involvement, ID1 should attach the contradiction to both the third-party influence issue and the bias/motive issue.
- **Example 3.** If the transcript reflects that the court cut off inquiry into Berry-family relationships, ID1 should preserve that as a procedural contradiction input for ID6 and ID8 rather than treating it as ordinary witness inconsistency.
- **Example 4.** When Pamela Rusco's FOC communication differs from a court-record statement about recommendations or notices, ID1 should preserve the divergence as an administrative contradiction with hearing utility notes.

### Code Examples

#### Python Query Example
```python
import sqlite3
from pprint import pprint

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"  # point to litigation_context.db in your deployment
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

actor = "Emily A. Watson"
issue = "parenting time"
sql = '''
SELECT q.id,
       q.source_doc,
       q.event_date,
       q.speaker,
       q.quote_text
FROM evidence_quotes q
WHERE q.speaker = ?
  AND LOWER(q.quote_text) LIKE '%' || LOWER(?) || '%'
  AND q.event_date >= '2026-01-01'
ORDER BY q.event_date, q.id;
'''

rows = conn.execute(sql, (actor, issue)).fetchall()
pprint([dict(r) for r in rows[:10]])
conn.close()
```

#### SQL Query Pack
```sql
-- Detect direct contradictions already captured in the contradictions table.
SELECT c.contradiction_id,
       c.actor_name,
       c.issue_tag,
       c.statement_a,
       c.statement_b,
       c.severity_score,
       c.source_a,
       c.source_b
FROM contradictions c
WHERE c.actor_name IN ('Emily A. Watson', 'Andrew James Pigors', 'Pamela Rusco')
  AND c.issue_tag IN ('parenting_time', 'safety_claim', 'notice', 'gatekeeping')
  AND c.event_date >= '2026-01-01'
ORDER BY c.severity_score DESC, c.contradiction_id;

-- Pull raw statement candidates from evidence_quotes.
SELECT id, source_doc, event_date, speaker, quote_text
FROM evidence_quotes
WHERE speaker = 'Emily A. Watson'
  AND event_date >= '2026-01-01'
  AND (
        LOWER(quote_text) LIKE '%visit%'
     OR LOWER(quote_text) LIKE '%exchange%'
     OR LOWER(quote_text) LIKE '%parenting%'
  )
ORDER BY event_date, id;

-- Join contradictions to prebuilt impeachment items for downstream charting.
SELECT c.contradiction_id,
       i.item_id,
       i.exhibit_label,
       i.foundation_status,
       i.use_case
FROM contradictions c
JOIN impeachment_items i
  ON i.contradiction_id = c.contradiction_id
WHERE c.actor_name = 'Emily A. Watson'
ORDER BY c.severity_score DESC, i.item_id;
```

#### Operational Output Example
```text
CONTRADICTION BUNDLE: 2026 Parenting-Time Denial
Actor: Emily A. Watson
Issue: parenting_time / gatekeeping
Statement A: "I did not stop Andrew from seeing L.D.W."
Statement B: "No visit tonight. Ronald says you are not coming here."
Severity: 92/100 only if supported by the actual DB query output
Use Path: ID1 -> ID2 -> ID3 -> Hearing packet
Foundation Need: confirm authorship, date, recipient, and message extraction source
```

### Failure Modes and Safeguards
- Never report a numeric contradiction count without showing the SQL query used to calculate it.
- Never convert a weak omission into a direct lie without a proposition-level comparison.
- Never use full child names; preserve `L.D.W.` only per MCR 8.119(H).
- Never substitute prohibited names or credentials into actor resolution.

### Integration Points
- Feeds ID2 with clean contradiction pairs and source metadata.
- Feeds ID3 with the precise proposition to lock in during COMMIT and PIN stages.
- Feeds ID4 with reliability and motive indicators.
- Feeds ID5 with topic clusters suitable for deposition chapters.
- Feeds ID6 when a contradiction is revealed by transcript testimony rather than documentary exhibits.
- Feeds ID8 with high-probability defense themes requiring preemptive neutralization.

## ID2: MRE 613 Impeachment Chart Generator

### Purpose
Transform contradiction bundles into courtroom-ready prior inconsistent statement charts that satisfy Michigan foundation requirements and support extrinsic exhibit confrontation.

### Design Pattern
Foundation-first chart builder + source-locking matrix + exhibit escalation ladder.

### Governing Michigan Evidence Focus
MRE 613, with supporting use of MRE 607 and strategic separation from MRE 608/609 impeachment modes.

### Detailed Description
- ID2 converts raw contradiction data into a usable chart format: witness, proposition, prior statement, current statement, source, date, page/line or exhibit citation, foundation questions, denial branch, and extrinsic-proof branch.
- The generator should assume the pro se operator may need one-page hearing charts, fuller deposition binders, and a condensed speaking version for live cross. Each format should be derived from the same underlying contradiction record.
- In Pigors v Watson, charts should be tailored to family-law themes: parenting-time interference, notice manipulation, third-party control, credibility of safety narratives, FOC process irregularity, and expert reliability gaps.
- The chart must distinguish between statements offered merely to impeach and statements that may also qualify through another non-hearsay or hearsay-exception pathway. The skill should warn the operator not to overclaim admissibility under MRE 613 alone.

### Structured Inputs

| Input Channel | Typical Records | Why It Matters |
|---|---|---|
| `evidence_quotes` | messages, transcript extracts, filing quotes, emails | supplies exact language for contradiction and confrontation |
| `contradictions` | normalized conflict pairs | preserves proposition-level inconsistency logic |
| `impeachment_items` | chart rows, exhibit links, use cases | moves analysis into ready-to-use hearing artifacts |
| transcript packets | page/line testimony, objections, rulings | supplies prior statements and preservation hooks |
| hearing notes | objections, judicial concerns, theory notes | sharpens live execution discipline |
### Key Operations
1. Select the strongest contradiction pairs from ID1.
2. Build the exact foundation questions needed to orient the witness to time, place, context, and recipient.
3. Generate a denial branch and an admission branch for each chart row.
4. Attach exhibit references, page numbers, transcript lines, or message metadata.
5. Separate pure impeachment use from substantive-use theories.
6. Provide a hearing-safe short form and a binder-safe long form.
7. Include court-facing notes on MRE 613(b) opportunity-to-explain requirements.
8. Flag when party-opponent pathways may reduce the need for elaborate impeachment framing.

### Michigan Family Law Example Threads
- **Example 1.** Example chart use: if Emily A. Watson testifies on 2026-04-08 that she always encouraged contact, ID2 should pull the prior 2026 message or filing statement, frame the foundation questions, and prepare the exhibit handoff.
- **Example 2.** Example FOC use: if Pamela Rusco made a written recommendation or scheduling statement that differs from hearing testimony, ID2 should build a chart that starts with authorship and role before introducing the inconsistency.
- **Example 3.** Example judicial-control use: if a hearing transcript shows the court limited confrontation before foundation was complete, ID2 should add a bench-note reminding the operator to renew the question sequence cleanly.
- **Example 4.** Example expert use: if an evaluator's report omits a material data source later acknowledged in testimony, ID2 should generate a hybrid chart linking MRE 613 confrontation with ID7 reliability attack notes.

### Code Examples

#### Python Query Example
```python
import sqlite3
from pprint import pprint

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

sql = '''
SELECT i.item_id,
       i.witness_name,
       i.proposition,
       i.prior_statement,
       i.current_statement,
       i.exhibit_label,
       i.foundation_status,
       i.source_reference
FROM impeachment_items i
WHERE i.witness_name = 'Emily A. Watson'
  AND i.rule_tag = 'MRE 613'
  AND i.event_date >= '2026-01-01'
ORDER BY i.priority_score DESC, i.item_id;
'''

chart_rows = conn.execute(sql).fetchall()
pprint([dict(r) for r in chart_rows[:8]])
conn.close()
```

#### SQL Query Pack
```sql
-- Core MRE 613 chart extraction.
SELECT item_id,
       witness_name,
       proposition,
       prior_statement,
       current_statement,
       exhibit_label,
       source_reference,
       foundation_status,
       use_case
FROM impeachment_items
WHERE rule_tag = 'MRE 613'
  AND witness_name IN ('Emily A. Watson', 'Pamela Rusco', 'Ronald Berry')
  AND event_date >= '2026-01-01'
ORDER BY priority_score DESC, item_id;

-- Backfill source text directly from evidence quotes where charts need stronger orientation detail.
SELECT q.id,
       q.source_doc,
       q.event_date,
       q.speaker,
       q.quote_text
FROM evidence_quotes q
WHERE q.speaker = 'Pamela Rusco'
  AND q.event_date >= '2026-01-01'
  AND LOWER(q.quote_text) LIKE '%recommend%'
ORDER BY q.event_date, q.id;

-- Verify contradiction source pairing before finalizing chart language.
SELECT c.contradiction_id,
       c.statement_a,
       c.statement_b,
       c.source_a,
       c.source_b,
       c.severity_score
FROM contradictions c
WHERE c.actor_name = 'Ronald Berry'
  AND c.event_date >= '2026-01-01'
ORDER BY c.severity_score DESC;
```

#### Operational Output Example
```text
MRE 613 CHART ROW
Witness: Emily A. Watson
Proposition: Interference with parenting-time contact
Current Testimony: "I always encouraged contact with L.D.W."
Prior Statement: "No visit tonight."
Source: Exhibit D / extracted text thread / 2026-03-11
Foundation Questions:
  1. You exchanged messages with Andrew James Pigors on 2026-03-11, correct?
  2. You were using your own phone, correct?
  3. You sent a message about that night's visit, correct?
Denial Branch: mark exhibit, authenticate, confront with exact line
Admission Branch: close and move to harm/materiality
```

### Failure Modes and Safeguards
- Do not present the prior statement to the witness before laying orientation unless the strategic context clearly favors immediate confrontation.
- Do not confuse character-for-truthfulness attacks under MRE 608 with statement-to-statement impeachment under MRE 613.
- Do not assign exhibit labels unless the label exists in the case package.
- Do not state that extrinsic evidence is automatically admissible; note the opportunity-to-explain requirement.

### Integration Points
- Consumes ID1 contradiction bundles as the chart substrate.
- Supplies ID3 with exact confrontation language and exhibit timing.
- Supplies ID5 with deposition-ready chart packs arranged by topic.
- Supplies ID6 when transcript line cites are the prior statement source.
- Supplies ID7 when the witness is an expert and the inconsistency undermines methodology.
- Supplies hearing notebooks built under the hearing-prep fusion logic.

## ID3: Cross-Examination Script Builder

### Purpose
Convert charts and contradiction bundles into controlled leading-question scripts using the COMMIT → PIN → CONFRONT → EXHIBIT sequence.

### Design Pattern
Branching finite-state cross engine with exhibit-aware confrontation rails.

### Governing Michigan Evidence Focus
MRE 611 control principles, MRE 613 confrontation mechanics, and selective use of MRE 607/608/609 depending on the witness and proof source.

### Detailed Description
- ID3 is the courtroom language engine. It takes each proposition and turns it into a sequence of short, leading questions that progressively remove wiggle room before the witness sees the impeaching exhibit.
- The COMMIT phase locks the witness into the current version. The PIN phase narrows time, place, person, and scope. The CONFRONT phase shows the inconsistency. The EXHIBIT phase authenticates and lands the proof cleanly.
- In Pigors v Watson, this module should emphasize disciplined language around exchange denials, third-party gatekeeping, notice issues, report omissions, and expert reliability defects. Scripts should avoid argument in the question and save explanation for the closing theme.
- Every script should include denial paths, memory-failure paths, evasive-answer recovery lines, judicial-interruption recovery lines, and a one-sentence theory note for counsel table or pro se podium use.

### Structured Inputs

| Input Channel | Typical Records | Why It Matters |
|---|---|---|
| `evidence_quotes` | messages, transcript extracts, filing quotes, emails | supplies exact language for contradiction and confrontation |
| `contradictions` | normalized conflict pairs | preserves proposition-level inconsistency logic |
| `impeachment_items` | chart rows, exhibit links, use cases | moves analysis into ready-to-use hearing artifacts |
| transcript packets | page/line testimony, objections, rulings | supplies prior statements and preservation hooks |
| hearing notes | objections, judicial concerns, theory notes | sharpens live execution discipline |
### Key Operations
1. Generate the COMMIT question that sounds harmless but binds the witness to a proposition.
2. Generate PIN questions on date, time, document, recipient, role, and circumstances.
3. Generate the CONFRONT question using the exact quote or transcript line.
4. Generate the EXHIBIT handoff phrase for admission or demonstrative use.
5. Add evasive-answer recovery questions that remain leading and narrow.
6. Add judge-interruption recovery notes respectful to Hon. Jenny L. McNeill.
7. Add theory notes explaining why the contradiction matters to custody, parenting time, or reliability.
8. Export versions for hearing, deposition, and witness-prep simulation.

### Michigan Family Law Example Threads
- **Example 1.** Example live script target: Emily A. Watson denies blocking a 2026 exchange. The script first commits her to the 'always encouraged contact' position, pins her to the date and phone, confronts her with the extracted message, and exhibits the message after denial or evasion.
- **Example 2.** Example third-party control script: Ronald Berry denies influencing exchanges. The script pins him to his communications and living arrangement, then confronts him with text references that place him inside the decision loop.
- **Example 3.** Example FOC script: Pamela Rusco is asked about notice, recommendation language, and source documents, then confronted with the written communication if the hearing version shifts.
- **Example 4.** Example expert script: an evaluator claims complete-file review, then is confronted with a missing transcript, omitted text extraction, or unreviewed contradictory source.

### Code Examples

#### Python Query Example
```python
import sqlite3
from pprint import pprint

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

sql = '''
SELECT item_id,
       witness_name,
       proposition,
       prior_statement,
       current_statement,
       exhibit_label
FROM impeachment_items
WHERE witness_name = 'Emily A. Watson'
  AND use_case = 'cross_exam'
  AND event_date >= '2026-01-01'
ORDER BY priority_score DESC
LIMIT 5;
'''

seeds = [dict(r) for r in conn.execute(sql).fetchall()]
pprint(seeds)
conn.close()
```

#### SQL Query Pack
```sql
-- Pull the highest-value cross seeds.
SELECT item_id,
       witness_name,
       proposition,
       prior_statement,
       current_statement,
       exhibit_label,
       priority_score
FROM impeachment_items
WHERE use_case = 'cross_exam'
  AND event_date >= '2026-01-01'
  AND witness_name IN ('Emily A. Watson', 'Ronald Berry', 'Pamela Rusco')
ORDER BY priority_score DESC, item_id;

-- Pull direct contradiction support for the script's theory note.
SELECT contradiction_id,
       actor_name,
       issue_tag,
       severity_score
FROM contradictions
WHERE actor_name = 'Emily A. Watson'
  AND event_date >= '2026-01-01'
ORDER BY severity_score DESC;

-- Pull the exact quote text for exhibit phrasing.
SELECT id, source_doc, event_date, quote_text
FROM evidence_quotes
WHERE speaker = 'Emily A. Watson'
  AND event_date >= '2026-01-01'
  AND LOWER(quote_text) LIKE '%visit%'
ORDER BY event_date;
```

#### Operational Output Example
```text
CROSS SCRIPT: EMILY A. WATSON / 2026-03-11 EXCHANGE
Theory Note: This sequence proves active interference, not mere misunderstanding.

COMMIT
Q1. You told the court you always encouraged Andrew James Pigors to see L.D.W., correct?

PIN
Q2. On 2026-03-11, you were communicating directly with him by text, correct?
Q3. That was your phone and your message thread, correct?
Q4. The topic that night was the scheduled visit, correct?

CONFRONT
Q5. You sent: "No visit tonight," correct?

EXHIBIT
Q6. If showing you Exhibit D refreshes nothing, I am offering Exhibit D to prove the prior inconsistent statement under MRE 613.

RECOVERY
If evasive: "My question was whether you sent those words."
If memory claimed: "Seeing Exhibit D will help you answer accurately, correct?"
```

### Failure Modes and Safeguards
- Questions must remain short and leading; do not narrate evidence inside the question.
- Do not ask a question unless you know the recovery path for denial, nonresponsive answer, or memory claim.
- Do not expose the exhibit too early; preserve the surprise value after the witness is committed.
- Do not let the script drift into argument; reserve argument for theme notes and closing.

### Integration Points
- Consumes ID2 chart rows to create live questioning sequences.
- Consumes ID4 motive and bias notes to choose pressure points.
- Consumes ID6 transcript context to avoid repeating already-sustained objection traps.
- Consumes ID8 predicted defenses to script preemptive follow-ups.
- Feeds ID5 deposition outlines with ready-made trap sequences.
- Feeds hearing-prep packets with anticipated judicial interruption recovery language.

## ID4: Witness Credibility Dossier

### Purpose
Build full witness profiles that combine contradiction history, motive, bias, access to information, prior conduct, reliability signals, and impeachment pathways.

### Design Pattern
Dossier synthesis graph + bias-motive matrix + reliability scorecard.

### Governing Michigan Evidence Focus
MRE 607, MRE 608, MRE 609, MRE 613, and witness-control principles linked to MRE 614 interactions with the court.

### Detailed Description
- ID4 organizes everything known about a witness into a single analytical profile. It does not merely list contradictions; it explains why the witness may shade testimony, what the witness can actually perceive, how the witness's role changes the proof burden, and where the strongest pressure points lie.
- The dossier should separate motive, bias, perception limits, memory reliability, consistency history, relationship map, documentary footprint, and likely courtroom demeanor. This matters because the best cross theme is often not the biggest contradiction but the cleanest pattern of unreliability.
- In Pigors v Watson, dossiers should capture role-driven sensitivities: Emily A. Watson as the opposing parent, Ronald Berry as a non-attorney third-party influence point, Pamela Rusco as FOC staff with administrative authority cues, experts as methodology witnesses, and Hon. Jenny L. McNeill as the judicial decision-maker whose rulings and interruptions matter for preservation analysis rather than conventional impeachment.
- The reliability score must always be query-supported. If the system reports a contradiction count, omission rate, or impeachment inventory size, it must show the SQL used to compute it. No unsupported percentages or folklore metrics are permitted.

### Structured Inputs

| Input Channel | Typical Records | Why It Matters |
|---|---|---|
| `evidence_quotes` | messages, transcript extracts, filing quotes, emails | supplies exact language for contradiction and confrontation |
| `contradictions` | normalized conflict pairs | preserves proposition-level inconsistency logic |
| `impeachment_items` | chart rows, exhibit links, use cases | moves analysis into ready-to-use hearing artifacts |
| transcript packets | page/line testimony, objections, rulings | supplies prior statements and preservation hooks |
| hearing notes | objections, judicial concerns, theory notes | sharpens live execution discipline |
### Key Operations
1. Assemble witness identity, role, and relationship map.
2. Aggregate contradictions, impeachment items, and source density.
3. Score motive, bias, interest, perception, memory, and corroboration.
4. Identify safe themes for live cross versus themes better saved for briefing.
5. Distinguish direct credibility attacks from substantive rebuttal evidence.
6. Create hearing version, deposition version, and appellate-preservation version.
7. Generate risk notes on sympathy, overreach, or judicial backlash.
8. Export summary bullets and full dossier pages.

### Michigan Family Law Example Threads
- **Example 1.** Example dossier for Emily A. Watson: role is defendant/parent, issue clusters include parenting-time control, communications, and narrative consistency; motive analysis focuses on leverage, positioning, and control of information flow.
- **Example 2.** Example dossier for Ronald Berry: role is non-attorney partner and possible third-party influencer; the bias section should note relationship ties and practical influence without inventing legal credentials or titles.
- **Example 3.** Example dossier for Pamela Rusco: reliability analysis should focus on documentation, recommendation history, and consistency between written communications and hearing statements.
- **Example 4.** Example expert dossier: methodology, materials reviewed, omitted materials, alternative explanations considered, and whether the expert can reliably apply principles to the facts of Pigors v Watson.

### Code Examples

#### Python Query Example
```python
import sqlite3
from pprint import pprint

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

witness = "Ronald Berry"
sql = '''
SELECT
    ? AS witness_name,
    (SELECT COUNT(*) FROM contradictions WHERE actor_name = ? AND event_date >= '2026-01-01') AS contradiction_count,
    (SELECT COUNT(*) FROM impeachment_items WHERE witness_name = ? AND event_date >= '2026-01-01') AS impeachment_item_count,
    (SELECT COUNT(*) FROM evidence_quotes WHERE speaker = ? AND event_date >= '2026-01-01') AS quote_count;
'''

profile = conn.execute(sql, (witness, witness, witness, witness)).fetchone()
pprint(dict(profile))
conn.close()
```

#### SQL Query Pack
```sql
-- Dossier counts must be query-supported.
SELECT
    'Emily A. Watson' AS witness_name,
    (SELECT COUNT(*) FROM contradictions WHERE actor_name = 'Emily A. Watson' AND event_date >= '2026-01-01') AS contradiction_count,
    (SELECT COUNT(*) FROM impeachment_items WHERE witness_name = 'Emily A. Watson' AND event_date >= '2026-01-01') AS impeachment_item_count,
    (SELECT COUNT(*) FROM evidence_quotes WHERE speaker = 'Emily A. Watson' AND event_date >= '2026-01-01') AS quote_count;

-- Pull the strongest credibility vectors.
SELECT contradiction_id,
       issue_tag,
       severity_score,
       source_a,
       source_b
FROM contradictions
WHERE actor_name = 'Emily A. Watson'
  AND event_date >= '2026-01-01'
ORDER BY severity_score DESC;

-- Pull dossier-ready impeachment records.
SELECT item_id,
       proposition,
       use_case,
       foundation_status,
       exhibit_label
FROM impeachment_items
WHERE witness_name = 'Emily A. Watson'
  AND event_date >= '2026-01-01'
ORDER BY priority_score DESC, item_id;
```

#### Operational Output Example
```text
WITNESS DOSSIER SNAPSHOT
Witness: Ronald Berry
Role: Non-attorney partner of Emily A. Watson
Relationship Signal: Related to the judge's spouse
Core Risks:
  - Bias toward defendant's litigation position
  - Possible behind-the-scenes influence over exchanges or messaging
  - Potential minimization of involvement
Proof Channels:
  - Text references in evidence_quotes
  - Contradiction rows in contradictions
  - Associated impeachment chart items
Live-Cross Theme:
  "You were more involved in exchange decisions than your testimony admits."
```

### Failure Modes and Safeguards
- Do not overstate bias without record-backed relationship facts.
- Do not import criminal-conviction impeachment unless MRE 609 requirements are independently satisfied.
- Do not treat every inconsistency as deliberate falsehood; perception and memory limits belong in separate fields.
- Do not report unsupported percentages or invented scoring legends.

### Integration Points
- Consumes ID1 and ID2 output to build issue-centered credibility profiles.
- Feeds ID3 with witness-specific tone, sequencing, and pressure points.
- Feeds ID5 with topic ordering based on the witness's weakest zones.
- Feeds ID6 with watchlists for transcript review of future hearings.
- Feeds ID8 with witness-response probability assumptions.
- Feeds expert challenge logic in ID7 when the witness is a retained specialist.

## ID5: Deposition Warfare Module

### Purpose
Build deposition outlines by topic, pair each topic with confrontation documents, and create trap sequences that preserve later hearing impeachment value.

### Design Pattern
Topic-tree deposition planner + staged trap sequencing + exhibit-index coupling.

### Governing Michigan Evidence Focus
MRE 613 for later impeachment, MRE 607 for flexibility, and evidentiary discipline that avoids wasting impeachment value during discovery.

### Detailed Description
- ID5 turns scattered issues into a controlled deposition campaign. Instead of a generic outline, it builds topic modules with objectives, key documents, lock-in questions, impeachment triggers, and follow-up branches tailored for Michigan family-law disputes.
- The module should be especially useful where a witness is likely to give narrative answers, deny document meaning, or blame misunderstandings. It should preserve clean admissions where possible and avoid overplaying exhibits too early unless a trap must close during the deposition itself.
- In Pigors v Watson, deposition topics should include parenting-time communications, role of Ronald Berry, notice mechanics, FOC communications, report omissions, safety-claim specifics, and expert file completeness. Each topic should identify the best exhibit, the best contradiction, and the best fallback.
- The output should distinguish discovery goals from hearing goals. Some questions are asked purely to pin testimony. Others are designed to authenticate later exhibits or expose missing methodology for ID7.

### Structured Inputs

| Input Channel | Typical Records | Why It Matters |
|---|---|---|
| `evidence_quotes` | messages, transcript extracts, filing quotes, emails | supplies exact language for contradiction and confrontation |
| `contradictions` | normalized conflict pairs | preserves proposition-level inconsistency logic |
| `impeachment_items` | chart rows, exhibit links, use cases | moves analysis into ready-to-use hearing artifacts |
| transcript packets | page/line testimony, objections, rulings | supplies prior statements and preservation hooks |
| hearing notes | objections, judicial concerns, theory notes | sharpens live execution discipline |
### Key Operations
1. Group issues into logically sequenced topic chapters.
2. Assign objectives, admissions sought, and must-cover exhibits for each chapter.
3. Create lock-in questions before showing documents.
4. Prepare trap sequences with denial, evasion, and memory branches.
5. Mark what must be preserved for later hearing impeachment.
6. Generate document-checklist and exhibit-order notes.
7. Link each topic to a contradiction cluster and credibility theme.
8. Export condensed and full deposition packets.

### Michigan Family Law Example Threads
- **Example 1.** Example topic 1 for Emily A. Watson: all 2026 parenting-time exchange communications, with goals to lock in authorship, decision-maker identity, and reasons given for denials.
- **Example 2.** Example topic 2 for Ronald Berry: extent of involvement in transportation, communications, or exchange decisions; goal is to pin down practical authority versus later minimization.
- **Example 3.** Example topic 3 for Pamela Rusco: notice flow, records maintained, recommendations issued, and source materials reviewed; goal is to authenticate administrative records and reveal omissions.
- **Example 4.** Example topic 4 for a custody evaluator: materials reviewed, interviews performed, whether texts and transcripts from 2026 were reviewed, and whether omitted evidence changes the opinion.

### Code Examples

#### Python Query Example
```python
import sqlite3
from pprint import pprint

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

sql = '''
SELECT i.witness_name,
       i.proposition,
       i.exhibit_label,
       i.use_case,
       c.issue_tag,
       c.severity_score
FROM impeachment_items i
LEFT JOIN contradictions c
  ON c.contradiction_id = i.contradiction_id
WHERE i.witness_name = 'Pamela Rusco'
  AND i.event_date >= '2026-01-01'
ORDER BY c.severity_score DESC, i.priority_score DESC;
'''

outline_rows = [dict(r) for r in conn.execute(sql).fetchall()]
pprint(outline_rows[:10])
conn.close()
```

#### SQL Query Pack
```sql
-- Topic seed extraction for deposition packets.
SELECT i.item_id,
       i.witness_name,
       i.proposition,
       i.exhibit_label,
       i.use_case,
       c.issue_tag,
       c.severity_score
FROM impeachment_items i
LEFT JOIN contradictions c
  ON c.contradiction_id = i.contradiction_id
WHERE i.witness_name IN ('Emily A. Watson', 'Ronald Berry', 'Pamela Rusco')
  AND i.event_date >= '2026-01-01'
ORDER BY i.witness_name, c.severity_score DESC, i.priority_score DESC;

-- Pull source quotes for document confrontation plans.
SELECT id, speaker, event_date, source_doc, quote_text
FROM evidence_quotes
WHERE event_date >= '2026-01-01'
  AND speaker IN ('Emily A. Watson', 'Ronald Berry', 'Pamela Rusco')
ORDER BY speaker, event_date, id;

-- Count unresolved contradiction gaps by witness.
SELECT actor_name, COUNT(*) AS unresolved_count
FROM contradictions
WHERE event_date >= '2026-01-01'
  AND (resolution_status IS NULL OR resolution_status != 'resolved')
GROUP BY actor_name
ORDER BY unresolved_count DESC;
```

#### Operational Output Example
```text
DEPOSITION CHAPTER: PAMELA RUSCO / NOTICE & RECOMMENDATIONS
Objective: Establish exactly what notice was given, when, and from what records.
Lock-In Questions:
  - You communicated with the parties about scheduling in 2026, correct?
  - You maintain records of those communications, correct?
  - Your testimony today is that notice was properly sent, correct?
Confrontation Documents:
  - Exhibit H: FOC communication log
  - Exhibit I: email or message extraction
Trap Sequence:
  1. Lock timing
  2. Lock recipient identity
  3. Lock claimed notice method
  4. Show missing or contrary record
Preserve For Hearing:
  - exact wording of claimed notice
  - who reviewed the file
  - whether the witness relied on memory or records
```

### Failure Modes and Safeguards
- Do not burn the strongest impeachment exhibit if a lock-in can be obtained first.
- Do not ask open-ended questions when a leading lock-in question is available and more useful.
- Do not end a chapter without securing the witness's definitive position.
- Do not forget to mark authentication points for later exhibit use.

### Integration Points
- Consumes ID2 chart rows and ID4 dossiers to build witness-specific deposition chapters.
- Consumes ID6 transcript flags to avoid previously blocked phrasing.
- Consumes ID8 predicted defenses to ensure each topic has a counter-trap.
- Feeds ID3 with refined live-cross sequences after deposition lock-in is obtained.
- Feeds evidence-war and hearing-prep outputs with exhibit order and gap lists.
- Feeds ID7 when deposition answers reveal expert-method weaknesses.

## ID6: Transcript Intelligence Extractor

### Purpose
Parse hearing transcripts into structured testimony, objections, rulings, preservation events, and judicial bias markers suitable for later impeachment, appellate framing, and hearing strategy.

### Design Pattern
Transcript parser + issue tagger + bias-marker detector + preservation ledger.

### Governing Michigan Evidence Focus
MRE 614 for court questioning, plus downstream use under MRE 613 and cross strategy rules where transcript testimony supplies the prior statement.

### Detailed Description
- ID6 reads transcripts like evidence, not like a diary. It should identify who spoke, what proposition was advanced, which objection was made, how the court ruled, whether a witness answered despite objection, and where the record may show interruption asymmetry or bias markers.
- The bias-marker function must stay disciplined. It should identify patterns such as unequal interruption, refusal to allow foundation completion, differential leniency for narrative testimony, or curtailed inquiry into relevant relationships—but it must preserve exact transcript cites and avoid unsupported conclusions.
- In Pigors v Watson, transcript extraction should focus on parenting-time issues, witness credibility, limitations on confronting prior statements, handling of Ronald Berry-related questioning, treatment of FOC testimony, and management of expert reliability challenges.
- The module should emit both hearing-use extracts and preservation-use extracts. Hearing use supports later witness confrontation. Preservation use supports briefing, motions, or appellate issue framing when the court prevented full impeachment development.

### Structured Inputs

| Input Channel | Typical Records | Why It Matters |
|---|---|---|
| `evidence_quotes` | messages, transcript extracts, filing quotes, emails | supplies exact language for contradiction and confrontation |
| `contradictions` | normalized conflict pairs | preserves proposition-level inconsistency logic |
| `impeachment_items` | chart rows, exhibit links, use cases | moves analysis into ready-to-use hearing artifacts |
| transcript packets | page/line testimony, objections, rulings | supplies prior statements and preservation hooks |
| hearing notes | objections, judicial concerns, theory notes | sharpens live execution discipline |
### Key Operations
1. Split transcript by speaker, line range, and issue cluster.
2. Identify objections, grounds, rulings, and whether answers were given.
3. Extract testimony propositions suitable for ID1 contradiction comparison.
4. Tag possible MRE 614 judicial-questioning events.
5. Tag possible bias markers with citation-only discipline.
6. Build preservation ledger entries for excluded impeachment or expert challenge lines.
7. Summarize testimony chapters for hearing-prep and deposition-prep reuse.
8. Export witness-specific testimony packets.

### Michigan Family Law Example Threads
- **Example 1.** Example transcript task: extract every 2026 hearing segment where Emily A. Watson described exchange efforts, then compare the language to texts and filings.
- **Example 2.** Example bias-marker task: identify whether questioning about Ronald Berry's involvement was interrupted before foundation was complete, preserving page/line cites without editorial overstatement.
- **Example 3.** Example FOC task: extract all rulings and objections around Pamela Rusco's records, recommendations, and notice testimony.
- **Example 4.** Example expert task: isolate every answer showing whether an expert reviewed the full 2026 file, including omitted texts, communications, or prior statements.

### Code Examples

#### Python Query Example
```python
import sqlite3
from pprint import pprint

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

sql = '''
SELECT q.id,
       q.source_doc,
       q.event_date,
       q.speaker,
       q.quote_text
FROM evidence_quotes q
WHERE q.source_doc LIKE '%transcript%'
  AND q.event_date >= '2026-01-01'
  AND (
        LOWER(q.quote_text) LIKE '%objection%'
     OR LOWER(q.quote_text) LIKE '%sustained%'
     OR LOWER(q.quote_text) LIKE '%overruled%'
     OR LOWER(q.quote_text) LIKE '%berry%'
  )
ORDER BY q.event_date, q.id;
'''

transcript_hits = [dict(r) for r in conn.execute(sql).fetchall()]
pprint(transcript_hits[:12])
conn.close()
```

#### SQL Query Pack
```sql
-- Transcript-extracted hearing events.
SELECT id, source_doc, event_date, speaker, quote_text
FROM evidence_quotes
WHERE source_doc LIKE '%transcript%'
  AND event_date >= '2026-01-01'
  AND (
        LOWER(quote_text) LIKE '%objection%'
     OR LOWER(quote_text) LIKE '%sustained%'
     OR LOWER(quote_text) LIKE '%overruled%'
     OR LOWER(quote_text) LIKE '%foundation%'
  )
ORDER BY event_date, id;

-- Pull contradiction candidates sourced from transcript testimony.
SELECT contradiction_id,
       actor_name,
       issue_tag,
       source_a,
       source_b,
       severity_score
FROM contradictions
WHERE event_date >= '2026-01-01'
  AND (LOWER(source_a) LIKE '%transcript%' OR LOWER(source_b) LIKE '%transcript%')
ORDER BY severity_score DESC;

-- Pull transcript-linked impeachment items.
SELECT item_id,
       witness_name,
       proposition,
       source_reference,
       exhibit_label
FROM impeachment_items
WHERE event_date >= '2026-01-01'
  AND LOWER(source_reference) LIKE '%transcript%'
ORDER BY priority_score DESC, item_id;
```

#### Operational Output Example
```text
TRANSCRIPT INTELLIGENCE EXTRACT
Hearing: Pigors v Watson, 14th Circuit Court, Muskegon County
Judge: Hon. Jenny L. McNeill
Marker Type: foundation interruption / possible preservation event
Transcript Event:
  - Question sought to establish Ronald Berry's role in exchange decisions
  - Objection raised before full time-place-person foundation completed
  - Court ruling limited follow-up
Action:
  - route testimony to ID1 for contradiction comparison
  - route ruling to preservation ledger
  - route topic to ID8 for counter-strategy planning
```

### Failure Modes and Safeguards
- Bias markers must always remain cite-bound and described as markers, not conclusions.
- Do not strip context from objections; include question, ground, and ruling together.
- Do not treat every adverse ruling as bias; distinguish legal disagreement from pattern evidence.
- Do not collapse transcript speaker identity when multiple counsel or officers are present.

### Integration Points
- Feeds ID1 with transcript-derived statements for contradiction comparison.
- Feeds ID2 with transcript cites when the prior statement is live testimony.
- Feeds ID3 with language on what already triggered objections.
- Feeds ID5 with deposition topics that cure transcript gaps.
- Feeds ID7 with preserved reliability rulings or exclusions.
- Feeds ID8 with judge-specific handling patterns and interruption risks.

## ID7: Expert Challenge System

### Purpose
Build Daubert-style reliability attacks under Michigan's MRE 702 and MRE 703 framework, supported by omission maps, methodology gaps, and confrontation materials.

### Design Pattern
Qualification audit + methodology-gap detector + omitted-data confrontation package.

### Governing Michigan Evidence Focus
MRE 702, MRE 703, and related witness-control principles, while using MRE 613 where experts make inconsistent statements about methods or materials reviewed.

### Detailed Description
- ID7 is the specialized engine for experts, evaluators, therapists, investigators, and any witness offered for opinion testimony. It asks whether the witness is qualified, whether the principles and methods are reliable, whether they were reliably applied, and whether the data considered were sufficient.
- In family-law cases, many 'expert' issues are really data-integrity issues: omitted communications, unreviewed transcripts, one-sided source selection, or conclusions that outrun the actual file. ID7 should surface those defects cleanly and connect them to admissibility, weight, or both.
- For Pigors v Watson, the module should assume the operator may need to challenge a custody evaluator, therapist, investigator, or any witness presented with specialized authority. It should separate credential issues from methodology issues and from bias issues.
- The output should include a short hearing motion outline, a live-cross package, and a fallback weight-only argument if exclusion is unrealistic. Where possible, it should connect omitted 2026 source materials from evidence_quotes directly to the challenged opinion.

### Structured Inputs

| Input Channel | Typical Records | Why It Matters |
|---|---|---|
| `evidence_quotes` | messages, transcript extracts, filing quotes, emails | supplies exact language for contradiction and confrontation |
| `contradictions` | normalized conflict pairs | preserves proposition-level inconsistency logic |
| `impeachment_items` | chart rows, exhibit links, use cases | moves analysis into ready-to-use hearing artifacts |
| transcript packets | page/line testimony, objections, rulings | supplies prior statements and preservation hooks |
| hearing notes | objections, judicial concerns, theory notes | sharpens live execution discipline |
### Key Operations
1. Audit qualifications, specialized knowledge claims, and role description.
2. List every file, transcript, communication, and dataset reportedly reviewed.
3. Identify omitted materials, especially contradictory communications or transcripts.
4. Assess whether the method is explainable, testable, and appropriately applied under MRE 702.
5. Assess whether the data type used is the kind reasonably relied upon under MRE 703.
6. Generate cross questions for omissions, assumptions, and unsupported leaps.
7. Generate motion language for exclusion, limitation, or reduced weight.
8. Link every attack point to a document or transcript cite.

### Michigan Family Law Example Threads
- **Example 1.** Example evaluator challenge: the expert claims a full review but did not review 2026 transcripts or the text extracts that bear directly on parenting-time interference. ID7 should treat this as both sufficiency-of-data and reliable-application problem.
- **Example 2.** Example therapist challenge: the witness relies heavily on one parent's narrative and lacks independent source validation. ID7 should mark this as source-selection risk and corroboration weakness, not merely a disagreement with conclusions.
- **Example 3.** Example investigator challenge: the witness adopted a recommendation without reviewing the full file. ID7 should pair the missing materials with the exact opinion paragraphs affected.
- **Example 4.** Example hearing tactic: if exclusion is unlikely, use ID7 to reduce the opinion to 'weight only' by showing omitted contradictory source data from litigation_context.db.

### Code Examples

#### Python Query Example
```python
import sqlite3
from pprint import pprint

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

sql = '''
SELECT q.id,
       q.source_doc,
       q.event_date,
       q.speaker,
       q.quote_text
FROM evidence_quotes q
WHERE q.event_date >= '2026-01-01'
  AND (
        LOWER(q.quote_text) LIKE '%reviewed the file%'
     OR LOWER(q.quote_text) LIKE '%complete review%'
     OR LOWER(q.quote_text) LIKE '%considered all materials%'
  )
ORDER BY q.event_date, q.id;
'''

opinion_claims = [dict(r) for r in conn.execute(sql).fetchall()]
pprint(opinion_claims[:10])
conn.close()
```

#### SQL Query Pack
```sql
-- Expert claim statements that may support a qualification or methodology attack.
SELECT id, source_doc, event_date, speaker, quote_text
FROM evidence_quotes
WHERE event_date >= '2026-01-01'
  AND (
        LOWER(quote_text) LIKE '%complete review%'
     OR LOWER(quote_text) LIKE '%all materials%'
     OR LOWER(quote_text) LIKE '%sufficient information%'
  )
ORDER BY event_date, id;

-- Contradictions involving expert file-review claims.
SELECT contradiction_id,
       actor_name,
       issue_tag,
       statement_a,
       statement_b,
       severity_score
FROM contradictions
WHERE event_date >= '2026-01-01'
  AND issue_tag IN ('expert_method', 'expert_file_review', 'expert_bias')
ORDER BY severity_score DESC;

-- Impeachment items prepared for expert confrontation.
SELECT item_id,
       witness_name,
       proposition,
       prior_statement,
       current_statement,
       exhibit_label
FROM impeachment_items
WHERE event_date >= '2026-01-01'
  AND use_case IN ('expert_cross', 'expert_motion')
ORDER BY priority_score DESC, item_id;
```

#### Operational Output Example
```text
EXPERT CHALLENGE PACKET
Target Opinion: Custody-related recommendation affecting L.D.W.
Attack Vector 1: Incomplete data review
Attack Vector 2: Methodology not reliably applied to 2026 communications
Attack Vector 3: Selective source dependence on one parent
Hearing Request:
  - exclude unreliable opinion under MRE 702
  - or limit weight under MRE 703 analysis
Cross Hook:
  "You told the court you reviewed the complete file, but you did not review the 2026 transcript segment on exchange denials, correct?"
```

### Failure Modes and Safeguards
- Do not call a witness an expert unless the record or designation supports that label.
- Do not overuse 'Daubert' shorthand; anchor the challenge in Michigan MRE 702 and 703.
- Do not attack credentials when the stronger issue is omitted data or unreliable application.
- Do not speculate about unseen materials; identify what the DB or transcript actually shows as reviewed or omitted.

### Integration Points
- Consumes ID1 contradictions and ID6 transcript extracts to identify method-related inconsistencies.
- Consumes ID4 dossiers when the expert's bias or source dependence matters.
- Consumes ID5 deposition outputs for prior expert lock-ins.
- Feeds ID2 with expert-specific inconsistency charts.
- Feeds ID3 with live expert cross scripts.
- Feeds hearing-prep and motion-generation logic with admissibility arguments.

## ID8: Adversary Prediction Matrix

### Purpose
Forecast likely witness answers, opposing arguments, objection patterns, and recovery strategies so impeachment can land cleanly even against prepared resistance.

### Design Pattern
Scenario matrix + counter-move library + weakness exploitation planner.

### Governing Michigan Evidence Focus
Strategic application of MRE 607, 613, 614, 702, and 703 with hearing-control awareness.

### Detailed Description
- ID8 fuses adversary-war-room and opposing-counsel-intelligence logic into a practical courtroom predictor. It asks: what will the witness say, what will the other side object to, what will the court likely care about, and what is the shortest path back to the contradiction?
- Prediction is not prophecy. The matrix should score scenarios based on observed filing habits, transcript patterns, witness relationship incentives, and prior objections. Every forecast should identify the evidence it relies on and the branch plan if the prediction is wrong.
- For Pigors v Watson, likely defense themes may include misunderstanding rather than obstruction, memory failure rather than contradiction, harmless procedural irregularity rather than prejudice, or 'best interests' framing that attempts to wash out specific credibility problems. ID8 should prepare counters for each.
- The module should output a matrix: predicted move, probability basis, likely objective, recommended counter, exhibit to have ready, and escalation path if the first counter is blocked.

### Structured Inputs

| Input Channel | Typical Records | Why It Matters |
|---|---|---|
| `evidence_quotes` | messages, transcript extracts, filing quotes, emails | supplies exact language for contradiction and confrontation |
| `contradictions` | normalized conflict pairs | preserves proposition-level inconsistency logic |
| `impeachment_items` | chart rows, exhibit links, use cases | moves analysis into ready-to-use hearing artifacts |
| transcript packets | page/line testimony, objections, rulings | supplies prior statements and preservation hooks |
| hearing notes | objections, judicial concerns, theory notes | sharpens live execution discipline |
### Key Operations
1. Collect prior objection patterns and narrative themes.
2. Predict witness denial, minimization, memory loss, or blame-shifting responses.
3. Predict opposing argument reframing and likely rescue questions.
4. Predict judicial concerns such as relevance, cumulativeness, or wasted time.
5. Map each prediction to a shortest effective counter.
6. Identify backup exhibits and alternate phrasing.
7. Escalate unresolved themes back into deposition or transcript review loops.
8. Produce hearing-day flash cards and scenario grids.

### Michigan Family Law Example Threads
- **Example 1.** Example prediction: Emily A. Watson may shift from direct denial to 'I meant only that night was unsafe.' Counter: use the exact proposition and avoid letting the theory expand beyond the committed answer.
- **Example 2.** Example prediction: Ronald Berry may minimize involvement as merely giving transportation help. Counter: pin down whether he communicated directives or controlled access decisions.
- **Example 3.** Example prediction: an expert may respond that omitted 2026 materials would not change the opinion. Counter: force the witness to admit the opinion was reached before seeing the omitted materials.
- **Example 4.** Example prediction: an objection may claim cumulative impeachment. Counter: explain that the next exhibit addresses a different proposition or a different source, not repetition.

### Code Examples

#### Python Query Example
```python
import sqlite3
from pprint import pprint

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

sql = '''
SELECT actor_name,
       issue_tag,
       COUNT(*) AS contradiction_events,
       AVG(severity_score) AS avg_severity
FROM contradictions
WHERE event_date >= '2026-01-01'
GROUP BY actor_name, issue_tag
ORDER BY contradiction_events DESC, avg_severity DESC;
'''

matrix_inputs = [dict(r) for r in conn.execute(sql).fetchall()]
pprint(matrix_inputs[:12])
conn.close()
```

#### SQL Query Pack
```sql
-- Scenario-frequency inputs by actor and issue.
SELECT actor_name,
       issue_tag,
       COUNT(*) AS contradiction_events,
       AVG(severity_score) AS avg_severity
FROM contradictions
WHERE event_date >= '2026-01-01'
GROUP BY actor_name, issue_tag
ORDER BY contradiction_events DESC, avg_severity DESC;

-- Pull recent impeachment items by use case to forecast likely defense responses.
SELECT witness_name,
       use_case,
       COUNT(*) AS item_count
FROM impeachment_items
WHERE event_date >= '2026-01-01'
GROUP BY witness_name, use_case
ORDER BY item_count DESC;

-- Pull source texts suggesting common rebuttal language.
SELECT speaker, source_doc, event_date, quote_text
FROM evidence_quotes
WHERE event_date >= '2026-01-01'
  AND (
        LOWER(quote_text) LIKE '%misunderstood%'
     OR LOWER(quote_text) LIKE '%safety%'
     OR LOWER(quote_text) LIKE '%best interests%'
     OR LOWER(quote_text) LIKE '%do not recall%'
  )
ORDER BY event_date, id;
```

#### Operational Output Example
```text
ADVERSARY PREDICTION MATRIX ENTRY
Target: Emily A. Watson
Predicted Move: "I did not block parenting time; I was acting for safety."
Probability Basis: prior contradiction cluster + safety-language hits from DB query
Likely Objective: reframe contradiction as protective discretion
Counter:
  1. return to exact message language
  2. isolate absence of immediate emergency action
  3. force admission that access was denied
Backup Exhibit: transcript line or message extraction showing categorical denial
Escalation: if narrative expands, ask to strike as nonresponsive and return to yes/no control
```

### Failure Modes and Safeguards
- Every prediction must identify the record basis that made the forecast plausible.
- Do not present predictions as facts; label them as anticipated moves.
- Do not ignore alternative branches just because one prediction looks likely.
- Do not let the matrix become a substitute for direct proof.

### Integration Points
- Consumes outputs from every other module to predict resistance and route backups.
- Feeds ID3 with recovery branches and counter-objection plans.
- Feeds ID5 with missing deposition lock-ins that would reduce uncertainty.
- Feeds ID6 with watchlists for future transcript extraction.
- Feeds ID7 with likely defenses to expert challenges.
- Acts as the final orchestration layer before hearing execution.

## Decision Tree

```text
START
  |
  |-- Do you have a statement conflict tied to a material issue?
  |       |
  |       |-- NO --> Route to ID4 for motive/bias/perception analysis
  |       |
  |       |-- YES
  |             |
  |             |-- Is the conflict already normalized in `contradictions`?
  |             |       |
  |             |       |-- NO --> Run ID1 extraction and scoring first
  |             |       |
  |             |       |-- YES
  |             |             |
  |             |             |-- Need a hearing chart? --> ID2
  |             |             |
  |             |             |-- Need live question sequence? --> ID3
  |             |             |
  |             |             |-- Need deposition lock-in first? --> ID5
  |             |             |
  |             |             |-- Source is transcript testimony? --> ID6
  |             |             |
  |             |             |-- Witness is expert / evaluator? --> ID7
  |             |             |
  |             |             |-- Expect countermove / objection / rescue? --> ID8
  |             |
  |             |-- Is the issue more about character or bias than statement inconsistency?
  |                     |
  |                     |-- YES --> ID4 first, then return to ID3 or ID5 if a cross route emerges
  |                     |
  |                     |-- NO --> Stay in contradiction pipeline
  |
  |-- Are you preserving a record because the court limited cross?
          |
          |-- YES --> ID6 preservation ledger + ID8 recovery planning
          |
          |-- NO --> proceed to hearing packet assembly
```
## Cross-Module Integration Patterns

### 1. Impeachment Cascade Workflow

1. **ID1** identifies that a witness's 2026 statement conflicts with another source on a material parenting-time issue.
2. **ID2** turns that conflict into a chart row with exact foundation questions and exhibit references.
3. **ID4** explains why the witness may resist, minimize, or deflect.
4. **ID3** converts the row into a COMMIT → PIN → CONFRONT → EXHIBIT script.
5. **ID8** predicts the rescue narrative or objection and attaches the shortest counter.
6. **ID6** preserves any judicial limitation or objection pattern that affects how the contradiction lands.
7. **ID5** uses the same contradiction if the witness must first be locked in at deposition.
8. **ID7** activates if the witness is an expert and the contradiction reveals method or data defects.

### 2. Deposition-to-Hearing Cascade

| Stage | Module | Output | Why It Matters |
|---|---|---|---|
| Pre-deposition | ID4 + ID5 | witness dossier + topic outline | sequences the deposition for clean lock-ins |
| During deposition | ID5 | admissions + document authentication | creates future impeachment leverage |
| Post-deposition | ID1 + ID2 | contradiction bundle + MRE 613 chart | normalizes the lock-ins for hearing use |
| Hearing prep | ID3 + ID8 | live cross script + counter matrix | converts discovery into courtroom execution |
| Preservation | ID6 | ruling / interruption ledger | protects later review if impeachment is curtailed |

### 3. Transcript-Driven Rescue Pattern

- If a hearing transcript reveals that foundation was cut short, **ID6** captures the cite.
- **ID8** predicts the next objection or judicial concern that caused the cutoff.
- **ID3** rewrites the question sequence to shorten orientation and avoid the same trigger.
- **ID2** condenses the chart row so only essential foundation facts remain.
- **ID5** adds a deposition topic or witness lock-in to cure the weakness outside the hearing context.

### 4. Expert-Opinion Collapse Pattern

- **ID6** extracts expert claims from transcript testimony.
- **ID1** compares those claims against omitted materials or contradictory statements.
- **ID7** packages the omission as an MRE 702 / 703 challenge.
- **ID2** builds any expert-specific prior inconsistent statement charts.
- **ID3** scripts the hearing cross.
- **ID8** predicts the expert's fallback position: "I would have reached the same opinion anyway."

### 5. Adversary Pattern Loop

| Trigger | Primary Module | Secondary Modules | Tactical Goal |
|---|---|---|---|
| repeated minimization | ID8 | ID3, ID4 | strip ambiguity and pin practical control |
| memory-loss answer | ID3 | ID2, ID5 | refresh or confront without losing control |
| narrative objection from opponent | ID8 | ID3 | shorten question and keep it leading |
| court limits topic | ID6 | ID8, ID5 | preserve issue and find alternate route |
| expert claims complete review | ID7 | ID1, ID6 | expose omitted data and reduce opinion weight |
## Domain Applications

### Application 1: Parenting-Time Interference Hearing

- Pull 2026 text and message records from `evidence_quotes` involving Emily A. Watson and Andrew James Pigors.
- Run ID1 to normalize denials, cancellations, or gatekeeping communications.
- Use ID2 to generate chart rows keyed to each disputed exchange.
- Use ID3 to script direct, short confrontation sequences for each denied contact event involving L.D.W.
- Use ID8 to anticipate a safety-based reframing and prepare the follow-up that separates a claimed concern from the actual denial of access.

### Application 2: Third-Party Influence by Ronald Berry

- Use ID4 to build a role-and-bias dossier for Ronald Berry as a non-attorney partner tied to the household decision environment.
- Use ID1 to compare statements minimizing his involvement against messages or testimony placing him in exchange decision loops.
- Use ID3 to script questions that distinguish transportation assistance from actual authority or influence.
- Use ID6 to preserve any hearing event where inquiry into Berry-related influence is cut short.

### Application 3: FOC Credibility and Administrative Notice Issues

- Use ID5 to create a Pamela Rusco deposition or examination outline around records, recommendation language, and notice mechanics.
- Use ID1 and ID2 to chart differences between written communications and later hearing testimony.
- Use ID3 for concise impeachment or lock-in sequences focused on what records exist and were reviewed.
- Use ID8 to prepare for the claim that any defect was harmless or merely clerical.

### Application 4: Expert Reliability Challenge in Custody-Related Testimony

- Use ID7 to list every material the expert says was reviewed.
- Use ID6 and ID1 to locate omitted transcript segments, unreviewed text messages, or contradictions about data completeness.
- Use ID2 if the expert's statements about file completeness differ across report, deposition, and hearing.
- Use ID3 to force admissions that the opinion was formed without the omitted 2026 material.
- Use ID8 to counter the fallback claim that the omitted material would not matter.
## Implementation Notes for LitigationOS

### Suggested Data Contracts

| Table | Minimum Fields the FORGE expects |
|---|---|
| `evidence_quotes` | `id`, `source_doc`, `event_date`, `speaker`, `quote_text` |
| `contradictions` | `contradiction_id`, `actor_name`, `issue_tag`, `statement_a`, `statement_b`, `source_a`, `source_b`, `severity_score`, `event_date` |
| `impeachment_items` | `item_id`, `witness_name`, `proposition`, `prior_statement`, `current_statement`, `exhibit_label`, `source_reference`, `rule_tag`, `use_case`, `priority_score`, `event_date` |

### Severity Rubric Template

| Score Band | Meaning | Typical Use |
|---|---|---|
| 90-100 | direct, material, documented contradiction with exhibit-ready proof | primary hearing impeachment |
| 70-89 | strong contradiction needing minor foundation work | chart and deposition target |
| 50-69 | useful inconsistency with ambiguity or limited corroboration | supporting theme or follow-up |
| 30-49 | weak inconsistency, omission, or context-dependent issue | dossier note only unless strengthened |
| 0-29 | noise, ambiguity, or non-material difference | do not force into live cross |

### Minimal Python Loader Pattern
```python
import sqlite3
from pathlib import Path

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

def fetch_all(sql, params=()):
    return [dict(r) for r in conn.execute(sql, params).fetchall()]

def contradiction_count(actor_name: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM contradictions WHERE actor_name = ? AND event_date >= '2026-01-01'",
        (actor_name,),
    ).fetchone()
    return int(row["n"])

print(contradiction_count("Emily A. Watson"))
conn.close()
```

### Example SQL Health Checks
```sql
-- Verify the three core tables exist.
SELECT name
FROM sqlite_master
WHERE type = 'table'
  AND name IN ('evidence_quotes', 'contradictions', 'impeachment_items')
ORDER BY name;

-- Verify there is 2026 data to work with.
SELECT 'evidence_quotes' AS table_name, COUNT(*) AS rows_2026
FROM evidence_quotes
WHERE event_date >= '2026-01-01'
UNION ALL
SELECT 'contradictions', COUNT(*)
FROM contradictions
WHERE event_date >= '2026-01-01'
UNION ALL
SELECT 'impeachment_items', COUNT(*)
FROM impeachment_items
WHERE event_date >= '2026-01-01';
```

## Michigan Rule Alignment

- **MRE 607:** Any party may attack a witness's credibility; the FORGE uses this as the doorway, not the full method.
- **MRE 608:** Character-for-truthfulness proof is separate from prior inconsistent statement proof; do not collapse them.
- **MRE 609:** Conviction-based impeachment requires an independent admissibility analysis.
- **MRE 613:** Prior inconsistent statements require disciplined foundation and opportunity-to-explain logic when extrinsic evidence is used.
- **MRE 614:** Court questioning and control issues matter for transcript extraction, preservation, and adjusted cross strategy.
- **MRE 702:** Expert opinion must rest on reliable principles and methods reliably applied to sufficient facts or data.
- **MRE 703:** The data relied upon must be of a type reasonably relied upon by experts in the field.

## Quick Reference Card

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ FORGE-IMPEACHMENT-DESTROYER QUICK CARD                                      │
├───────────────────────────────────────────────────────────────────────────────┤
│ Case Anchor: Pigors v Watson, No. 2024-001507-DC                            │
│ Child Rule: Use L.D.W. only                                                  │
│ Core Flow: ID1 -> ID2 -> ID3 -> ID8                                          │
│ Dossier Path: ID1 -> ID4 -> ID3                                              │
│ Deposition Path: ID4 -> ID5 -> ID1 -> ID2 -> ID3                            │
│ Transcript Path: ID6 -> ID1 -> ID2 / ID3 / ID8                              │
│ Expert Path: ID6 -> ID1 -> ID7 -> ID2 -> ID3                                │
├───────────────────────────────────────────────────────────────────────────────┤
│ MRE Checklist                                                                │
│  • 607 = who may impeach                                                     │
│  • 608 = character for truthfulness limits                                   │
│  • 609 = conviction impeachment limits                                       │
│  • 613 = prior inconsistent statement mechanics                              │
│  • 614 = court questioning / control awareness                               │
│  • 702/703 = expert reliability and data-sufficiency attack                  │
├───────────────────────────────────────────────────────────────────────────────┤
│ Cross Formula                                                                 │
│  COMMIT -> PIN -> CONFRONT -> EXHIBIT -> CLOSE                               │
├───────────────────────────────────────────────────────────────────────────────┤
│ Never Do This                                                                 │
│  • never use prohibited names/credentials                                    │
│  • never invent counts or percentages                                        │
│  • never use a full child name                                               │
│  • never confuse MRE 608 with MRE 613                                        │
└───────────────────────────────────────────────────────────────────────────────┘
```
