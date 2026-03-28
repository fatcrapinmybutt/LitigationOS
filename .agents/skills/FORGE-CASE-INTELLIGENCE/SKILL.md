---
name: FORGE-CASE-INTELLIGENCE
description: >-
  Total case intelligence operations center providing strategic planning,
  timeline forensics, risk assessment, evidence gap analysis, EGCP filing
  readiness scoring, 15-gate QA validation, deadline tracking, and multi-court
  docket monitoring for complex multi-lane Michigan family law litigation.
category: litigation
version: "1.0.0"
triggers:
  - case strategy planning
  - timeline forensic analysis
  - litigation risk assessment
  - evidence gap detection
  - filing readiness scoring
  - EGCP score calculation
  - QA validation pipeline
  - court deadline tracking
  - docket monitoring
  - filing priority matrix
  - convergence gap analysis
  - emergence pattern detection
metadata:
  tier: FORGE
  fused_skills: 8
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-03-27
  forge_class: litigation-case-intelligence
  emergent_capability: Unified case intelligence providing real-time strategic awareness across all litigation lanes with automated risk, readiness, and quality scoring
---

# 🔱 FORGE-CASE-INTELLIGENCE — Total Case Intelligence Operations Center (Ω-Δ99)

> | Field | Value |
> | --- | --- |
> | Tier | FORGE |
> | Domain | Multi-lane Michigan litigation intelligence |
> | Scope | Strategic planning, timeline forensics, risk assessment, evidence gap analysis, filing readiness, QA, deadlines, and docket monitoring |
> | Emergent Capability | Unified case intelligence providing real-time strategic awareness across all litigation lanes with automated risk, readiness, and quality scoring |

This superskill functions as the **operations center** for Michigan litigation intelligence.
It is built for Andrew James Pigors, plaintiff pro se, against Emily A. Watson, with
Hon. Jenny L. McNeill in the 14th Circuit context, Pamela Rusco for FOC routing, and
Jennifer Barnes P55406 explicitly marked as **WITHDREW** whenever her name appears.

The intelligence model assumes a **seven-lane operational map**:

- **Lane A** — Custody / parenting-time litigation (**2024-001507-DC**)
- **Lane B** — Housing / civil lane (**2025-002760-CZ**)
- **Lane C** — Convergence / coordination lane
- **Lane D** — PPO lane (**2023-5907-PP**)
- **Lane E** — Misconduct / judicial accountability lane
- **Lane F** — Appellate lane (**COA 366810**)
- **Lane G** — Reserve expansion lane for MSC or federal escalation when triggered

The child is **L.D.W. only**. No full child name is ever allowed in examples, output,
snippets, exhibits, or validation logic.

## Forged from 8 Skills

| # | Source Skill | Core Capability Added to the Forge |
| --- | --- | --- |
| 1 | `case-strategy-architect` | High-level litigation sequencing, lane prioritization, convergence planning, and opposition war-gaming. |
| 2 | `timeline-forensics` | Event extraction, chronology reconstruction, contradiction detection, and exhibit-ready timeline assembly. |
| 3 | `risk-assessor` | Severity scoring, vulnerability detection, red-team review, immunity barriers, and cure path generation. |
| 4 | `gap-analyzer` | Evidence/authority coverage analysis, gap classification, and acquisition task generation. |
| 5 | `filing-readiness-scorer` | EGCP readiness scoring and weakest-link diagnostics for every filing candidate. |
| 6 | `qa-validator` | Fifteen-gate anti-hallucination review, decontamination, and traceability enforcement. |
| 7 | `deadline-tracker` | Motion-response tracking, appellate timing, trigger-event deadlines, and SOL monitoring. |
| 8 | `docket-monitor` | Multi-court entry awareness, compliance tracking, and event-to-deadline routing. |

## Architecture

```text
┌────────────────────────────────────────────────────────────────────────────────────────────┐
│                     FORGE-CASE-INTELLIGENCE (Ω-Δ99)                                       │
│                  Total Case Intelligence Operations Center                                │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│  CI8 Multi-Court Docket Monitor ──┐                                                      │
│                                   ▼                                                      │
│  CI7 Deadline Intelligence Engine ───────┐                                               │
│                                          ▼                                               │
│  CI2 Timeline Forensics Engine ───────► CI1 Strategic Command Center ───────┐           │
│                                          ▲                                   │           │
│                                          │                                   ▼           │
│  CI4 Evidence Gap Analyzer ──────────────┤                         Filing Sequence Map    │
│                                          │                                   │           │
│  CI3 Risk Assessment Matrix ─────────────┤                                   ▼           │
│                                          │                         CI5 EGCP Readiness      │
│                                          │                                   │           │
│  CI6 15-Gate QA Validator ◄──────────────┴───────────────────────────────────┘           │
├────────────────────────────────────────────────────────────────────────────────────────────┤
│ INPUTS: evidence_quotes, claims, deadlines, judicial_violations, docket_events, drafts   │
│ OUTPUTS: priorities, timelines, risk registers, gap tickets, EGCP scores, QA verdicts,   │
│          deadline dashboards, docket alerts, and unified filing intelligence               │
└────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Global Michigan Operating Constraints

1. **All authorities must be real Michigan authorities or real federal authorities used in Michigan litigation context.**
2. **All dates in examples remain in 2026 unless a historical case number requires an older event date reference.**
3. **All statistics must trace to SQL queries.** If a number cannot be tied to a query, CI6 rejects it.
4. **Party identity is locked**:
   - Andrew James Pigors — plaintiff pro se
   - Emily A. Watson — defendant
   - Hon. Jenny L. McNeill — judge
   - Jennifer Barnes P55406 — WITHDREW
   - Pamela Rusco — FOC
5. **Child reference is L.D.W. only** under the privacy discipline reflected in **MCR 8.119(H)**.
6. **Core database tables** referenced throughout this forge:
   - `evidence_quotes`
   - `claims`
   - `deadlines`
   - `judicial_violations`
   - `docket_events`
   - `filing_readiness`

## CI1: Strategic Command Center

**Purpose:** Coordinate all active lanes, assign urgency bands P0-P3, detect convergence opportunities, optimize filing order, and allocate finite pro se resources without sacrificing Michigan procedural discipline.

**Design Pattern:** Weighted Priority Matrix + Game-Theory Sequencer + Cross-Lane Convergence Router

### Michigan Authority Anchors

- MCR 2.119
- MCR 2.003
- MCR 7.204
- MCR 7.212
- MCL 722.23
- MCL 722.27
- MCL 722.27a
- Vodvarka v Grasmeyer, 259 Mich App 499 (2003)
- Shade v Wright, 291 Mich App 17 (2010)
- Pierron v Pierron, 486 Mich 81 (2010)

### Integration Contract

| Direction | Interfaces |
| --- | --- |
| Receives from | timeline clusters from CI2; risk scores from CI3; gap tickets from CI4; EGCP readiness from CI5; QA gate verdicts from CI6; deadline clocks from CI7; docket events from CI8 |
| Feeds to | lane priority matrix; filing sequence recommendations; resource allocation plan; opposition-response contingencies |

### Operating Notes

1. Always treat Lane F deadlines as hard stops even when other lanes are factually stronger.
2. Use CI2 before making any narrative claim about escalation or retaliation.
3. Do not elevate Lane C above substantive lanes unless convergence unlocks a higher-value filing.
4. If Jennifer Barnes P55406 is referenced, mark her as WITHDREW and do not allocate service tasks to her.
5. If the child is mentioned, the string must remain L.D.W. only.
6. Prefer filings that improve downstream leverage in multiple lanes at once.

### Code Example A

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
import sqlite3

LANE_LABELS = {
    "A": "Custody",
    "B": "Housing",
    "C": "Convergence",
    "D": "PPO",
    "E": "Misconduct",
    "F": "Appellate",
}

@dataclass(slots=True)
class LaneSignal:
    lane: str
    readiness_score: int
    risk_score: int
    open_deadlines: int
    blocker_count: int
    docket_velocity: int
    convergence_score: int

def compute_priority(signal: LaneSignal) -> str:
    pressure = (
        (100 - signal.readiness_score)
        + signal.risk_score
        + (signal.open_deadlines * 10)
        + (signal.blocker_count * 12)
        + signal.docket_velocity
        - signal.convergence_score
    )
    if pressure >= 150:
        return "P0"
    if pressure >= 110:
        return "P1"
    if pressure >= 70:
        return "P2"
    return "P3"

def load_lane_signals(db_path: str) -> list[LaneSignal]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = """
    SELECT
        fr.lane,
        COALESCE(MAX(fr.total_score), 0) AS readiness_score,
        COALESCE(MAX(rf.severity_score), 0) AS risk_score,
        COALESCE(SUM(CASE WHEN d.status = 'OPEN' THEN 1 ELSE 0 END), 0) AS open_deadlines,
        COALESCE(SUM(CASE WHEN g.gap_type = 'BLOCKER' THEN 1 ELSE 0 END), 0) AS blocker_count,
        COALESCE(COUNT(DISTINCT de.event_id), 0) AS docket_velocity,
        COALESCE(MAX(cc.convergence_score), 0) AS convergence_score
    FROM filing_readiness fr
    LEFT JOIN risk_findings rf ON rf.lane = fr.lane
    LEFT JOIN deadlines d ON d.lane = fr.lane
    LEFT JOIN convergence_gaps g ON g.lane = fr.lane
    LEFT JOIN docket_events de ON de.lane = fr.lane
    LEFT JOIN cross_lane_convergence cc ON cc.lane = fr.lane
    GROUP BY fr.lane
    ORDER BY fr.lane;
    """
    rows = conn.execute(query).fetchall()
    return [LaneSignal(**dict(row)) for row in rows]
```

### SQL Example

```sql
-- CI1 strategic lane state query
SELECT
    fr.lane,
    MAX(fr.total_score) AS readiness_score,
    MAX(rf.severity_score) AS max_risk,
    SUM(CASE WHEN d.status = 'OPEN' THEN 1 ELSE 0 END) AS open_deadlines,
    SUM(CASE WHEN cg.gap_type = 'BLOCKER' THEN 1 ELSE 0 END) AS blocker_count,
    COUNT(DISTINCT de.event_id) AS docket_events_last_30,
    MAX(jv.severity_score) AS judicial_pressure
FROM filing_readiness fr
LEFT JOIN risk_findings rf ON rf.lane = fr.lane
LEFT JOIN deadlines d ON d.lane = fr.lane
LEFT JOIN convergence_gaps cg ON cg.lane = fr.lane
LEFT JOIN docket_events de
    ON de.lane = fr.lane
   AND de.event_date >= '2026-02-26'
LEFT JOIN judicial_violations jv ON jv.lane = fr.lane
GROUP BY fr.lane
ORDER BY blocker_count DESC, open_deadlines DESC, max_risk DESC;
```

### Code Example B

```python
def sequence_filings(signals: Iterable[LaneSignal]) -> list[dict]:
    staged = []
    for signal in signals:
        priority = compute_priority(signal)
        next_action = {
            "P0": "Draft immediately and reserve service resources",
            "P1": "Draft this week and cross-check deadlines",
            "P2": "Develop evidence and authority support",
            "P3": "Monitor only unless convergence event occurs",
        }[priority]
        staged.append(
            {
                "lane": signal.lane,
                "label": LANE_LABELS.get(signal.lane, signal.lane),
                "priority": priority,
                "next_action": next_action,
                "why_now": {
                    "readiness_score": signal.readiness_score,
                    "risk_score": signal.risk_score,
                    "open_deadlines": signal.open_deadlines,
                    "blocker_count": signal.blocker_count,
                    "docket_velocity": signal.docket_velocity,
                    "convergence_score": signal.convergence_score,
                },
            }
        )

    return sorted(
        staged,
        key=lambda item: (
            item["priority"],
            -item["why_now"]["open_deadlines"],
            -item["why_now"]["risk_score"],
        ),
    )

def war_game_opposition(priority_lane: str) -> list[str]:
    if priority_lane == "A":
        return [
            "Expect argument that no proper cause or change exists under Vodvarka.",
            "Expect minimization of denied parenting time and attack on timeline reliability.",
            "Prepare PIERRON-based due process framing if notice defects appear.",
        ]
    if priority_lane == "E":
        return [
            "Expect immunity rhetoric and claims that adverse rulings are not misconduct.",
            "Separate judicial immunity analysis from disqualification and appellate preservation.",
            "Anchor to docket chronology rather than adjectives.",
        ]
    return [
        "Expect standing, ripeness, and mootness attacks.",
        "Lead with verified docket dates, orders, and evidence coverage metrics.",
        "Do not over-claim statistics unless CI6 can trace them to SQL.",
    ]
```

### Michigan-Specific Execution Rules

- CI1 must preserve the identity lock for Andrew James Pigors, Emily A. Watson, Hon. Jenny L. McNeill, Pamela Rusco, and Jennifer Barnes P55406 (WITHDREW).
- CI1 must avoid any child full-name disclosure and keep the minor referenced as L.D.W. only.
- CI1 must expose enough structured output for CI6 to validate every citation, statistic, and date.
- CI1 must push any newly discovered timing issue into CI7 and any new docket-derived event into CI8.
- CI1 must keep lane assignments explicit so CI1 can prioritize without guessing.
- CI1 must prefer query-backed facts from litigation_context.db over narrative intuition.

### Sample Inputs

| Input Type | Example | Why It Matters |
| --- | --- | --- |
| Structured row | `CI1-sample-row` | Demonstrates how the module consumes query-backed data. |
| Case anchor | `2024-001507-DC / 2025-002760-CZ / 2023-5907-PP / COA 366810` | Keeps lane and court routing correct. |
| Identity rule | `L.D.W. only` | Forces privacy discipline and QA compatibility. |

### Output Contract

- CI1 returns structured, reviewable output rather than opaque prose.
- CI1 always includes lane, case number, date context, and authority support where applicable.
- CI1 output must be usable by CI1, CI5, and CI6 without manual reinterpretation.
- CI1 output should state assumptions when a rule default is used instead of a docket-specific date.
- CI1 output should flag uncertainty rather than invent precision.
- CI1 output should stay suitable for conversion into hearing notes, dashboards, or filing exhibits.


## CI2: Timeline Forensics Engine

**Purpose:** Extract dated events from transcripts, orders, police reports, messages, and docket activity; build a master chronology; surface temporal gaps; and turn chronology into exhibit-grade narrative support.

**Design Pattern:** Event Sourcing + Temporal Normalization + Cross-Lane Correlation Graph

### Michigan Authority Anchors

- MRE 401
- MRE 402
- MRE 403
- MRE 901
- MCR 8.119(H)
- MCL 750.539c
- MCL 722.27a

### Integration Contract

| Direction | Interfaces |
| --- | --- |
| Receives from | raw documents and structured rows; docket entry dates from CI8; order compliance facts; transcript snippets |
| Feeds to | master timeline; gap windows; timeline exhibits; event acceleration flags |

### Operating Notes

1. Court-filed and police-origin dates outrank memory-based dates.
2. Never infer a date when a source provides only a month without labeling the result as inferred.
3. Merge parallel lane events only when the factual nucleus overlaps.
4. Escalation claims require at least two sequential support points tied to actual source references.
5. Timeline exhibits should keep source references visible so CI6 can validate them.
6. Protect the child's identity by using L.D.W. only, even inside extracted snippets.

### Code Example A

```python
from dataclasses import dataclass
from datetime import datetime
import re
import sqlite3

DATE_PATTERNS = [
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2}, 2026\b",
]

@dataclass(slots=True)
class EventAtom:
    lane: str
    event_date: str
    source_type: str
    source_ref: str
    actor: str
    description: str
    confidence: float

def extract_dates(text: str) -> list[str]:
    found: list[str] = []
    for pattern in DATE_PATTERNS:
        found.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return found

def normalize_event(
    lane: str,
    source_type: str,
    source_ref: str,
    actor: str,
    description: str,
    event_date: str,
) -> EventAtom:
    confidence = 1.0 if source_type in {"court_order", "docket", "police_report"} else 0.75
    return EventAtom(
        lane=lane,
        event_date=event_date,
        source_type=source_type,
        source_ref=source_ref,
        actor=actor,
        description=description.strip(),
        confidence=confidence,
    )
```

### SQL Example

```sql
-- CI2 master chronology query
SELECT lane,
       event_date,
       source_type,
       source_ref,
       actor,
       summary
FROM (
    SELECT lane,
           quote_date AS event_date,
           'evidence_quote' AS source_type,
           quote_id AS source_ref,
           speaker AS actor,
           quote_text AS summary
    FROM evidence_quotes
    WHERE quote_date IS NOT NULL

    UNION ALL

    SELECT lane,
           filed_date AS event_date,
           'docket' AS source_type,
           docket_number AS source_ref,
           filed_by AS actor,
           title AS summary
    FROM docket_events
    WHERE filed_date IS NOT NULL

    UNION ALL

    SELECT lane,
           violation_date AS event_date,
           'judicial_violation' AS source_type,
           violation_id AS source_ref,
           actor_name AS actor,
           finding AS summary
    FROM judicial_violations
    WHERE violation_date IS NOT NULL
)
ORDER BY event_date, lane, source_type;
```

### Code Example B

```python
def detect_temporal_gaps(events: list[EventAtom], min_days: int = 14) -> list[dict]:
    ordered = sorted(events, key=lambda e: e.event_date)
    gaps: list[dict] = []
    for previous, current in zip(ordered, ordered[1:]):
        start = datetime.fromisoformat(previous.event_date)
        end = datetime.fromisoformat(current.event_date)
        delta = (end - start).days
        if delta >= min_days:
            gaps.append(
                {
                    "lane": current.lane,
                    "gap_start": previous.event_date,
                    "gap_end": current.event_date,
                    "gap_days": delta,
                    "needs_acquisition": True,
                    "rationale": "No event support in the interval; request messages, police logs, or orders.",
                }
            )
    return gaps

def build_timeline_exhibit(events: list[EventAtom], title: str) -> str:
    lines = [f"TIMELINE EXHIBIT: {title}", ""]
    for idx, event in enumerate(sorted(events, key=lambda e: e.event_date), start=1):
        lines.append(
            f"{idx:02d}. {event.event_date} | Lane {event.lane} | {event.source_type} | "
            f"{event.source_ref} | {event.actor} | {event.description}"
        )
    return "\n".join(lines)
```

### Michigan-Specific Execution Rules

- CI2 must preserve the identity lock for Andrew James Pigors, Emily A. Watson, Hon. Jenny L. McNeill, Pamela Rusco, and Jennifer Barnes P55406 (WITHDREW).
- CI2 must avoid any child full-name disclosure and keep the minor referenced as L.D.W. only.
- CI2 must expose enough structured output for CI6 to validate every citation, statistic, and date.
- CI2 must push any newly discovered timing issue into CI7 and any new docket-derived event into CI8.
- CI2 must keep lane assignments explicit so CI1 can prioritize without guessing.
- CI2 must prefer query-backed facts from litigation_context.db over narrative intuition.

### Sample Inputs

| Input Type | Example | Why It Matters |
| --- | --- | --- |
| Structured row | `CI2-sample-row` | Demonstrates how the module consumes query-backed data. |
| Case anchor | `2024-001507-DC / 2025-002760-CZ / 2023-5907-PP / COA 366810` | Keeps lane and court routing correct. |
| Identity rule | `L.D.W. only` | Forces privacy discipline and QA compatibility. |

### Output Contract

- CI2 returns structured, reviewable output rather than opaque prose.
- CI2 always includes lane, case number, date context, and authority support where applicable.
- CI2 output must be usable by CI1, CI5, and CI6 without manual reinterpretation.
- CI2 output should state assumptions when a rule default is used instead of a docket-specific date.
- CI2 output should flag uncertainty rather than invent precision.
- CI2 output should stay suitable for conversion into hearing notes, dashboards, or filing exhibits.


## CI3: Risk Assessment Matrix

**Purpose:** Score filing risks from 0-100, map each risk to a cure path, monitor standing/ripeness/mootness, and surface legal barriers such as immunity, timing, proof defects, or compliance vulnerabilities.

**Design Pattern:** Risk Register + Cure-Step Mapper + Red-Team Stress Harness

### Michigan Authority Anchors

- MCR 2.116(C)(4)
- MCR 2.116(C)(5)
- MCR 2.116(C)(8)
- MCR 2.116(C)(10)
- MCR 2.119
- MCL 600.5805
- 42 USC § 1983
- Haines v Kerner, 404 US 519 (1972)

### Integration Contract

| Direction | Interfaces |
| --- | --- |
| Receives from | draft filing candidates; timeline support from CI2; evidence coverage from CI4; deadline status from CI7 |
| Feeds to | risk register; cure plan; red-team attack list; go / no-go weighting for CI1 and CI5 |

### Operating Notes

1. Every risk must include a cure step and an authority anchor.
2. If a risk cannot be cured before the filing deadline, CI1 should downgrade priority unless preservation requires filing.
3. Do not collapse federal immunity analysis into Michigan disqualification standards.
4. Use MCL 600.5805 for borrowed limitation-period discussions in Michigan-based §1983 timing analysis.
5. Risk scoring should be transparent enough for CI6 to trace each number.
6. Never convert uncertainty into fake precision; explain why a score was assigned.

### Code Example A

```python
from dataclasses import dataclass
import sqlite3

@dataclass(slots=True)
class RiskFinding:
    filing_id: str
    lane: str
    category: str
    severity_score: int
    risk_statement: str
    cure_step: str
    authority_anchor: str

def score_risk(evidence_score: int, deadline_days: int, citation_coverage: int, qa_failures: int) -> int:
    raw = (
        max(0, 30 - evidence_score)
        + max(0, 20 - citation_coverage)
        + max(0, 15 - deadline_days)
        + qa_failures * 8
    )
    return min(100, raw)

def immunity_barrier(lane: str, target: str) -> str:
    if lane == "C" and "judge" in target.lower():
        return "Absolute judicial immunity requires careful claim slicing; focus on declaratory or non-judicial conduct theories."
    if lane == "E":
        return "Disqualification and complaint routing differ from damages theories; keep procedural vehicles separate."
    return "No special immunity barrier detected beyond ordinary defenses."
```

### SQL Example

```sql
-- CI3 risk sweep for filing candidates
SELECT
    fr.filing_id,
    fr.lane,
    fr.total_score AS readiness_score,
    COALESCE(MAX(d.days_remaining), 999) AS days_remaining,
    COALESCE(SUM(CASE WHEN q.status = 'FAIL' THEN 1 ELSE 0 END), 0) AS qa_failures,
    COALESCE(MAX(g.coverage_score), 0) AS evidence_coverage,
    COALESCE(MAX(c.citation_score), 0) AS citation_coverage
FROM filing_readiness fr
LEFT JOIN deadlines d ON d.filing_id = fr.filing_id
LEFT JOIN qa_results q ON q.filing_id = fr.filing_id
LEFT JOIN gap_coverage g ON g.filing_id = fr.filing_id
LEFT JOIN citation_coverage c ON c.filing_id = fr.filing_id
GROUP BY fr.filing_id, fr.lane, fr.total_score
ORDER BY days_remaining ASC, qa_failures DESC;
```

### Code Example B

```python
def build_red_team_findings(filing_id: str, lane: str) -> list[RiskFinding]:
    catalog: list[RiskFinding] = []
    catalog.append(
        RiskFinding(
            filing_id=filing_id,
            lane=lane,
            category="Standing / Ripeness / Mootness",
            severity_score=55,
            risk_statement="Opponent may argue the requested relief does not address a live controversy or lacks present injury framing.",
            cure_step="Tie every requested remedy to a dated event, current order, or active deprivation.",
            authority_anchor="MCR 2.116(C)(4)-(5)",
        )
    )
    catalog.append(
        RiskFinding(
            filing_id=filing_id,
            lane=lane,
            category="Proof Density",
            severity_score=48,
            risk_statement="Narrative may outrun the evidence if factual assertions do not map to evidence_quotes rows.",
            cure_step="Require CI4 to produce a claim-to-evidence matrix before filing.",
            authority_anchor="MRE 401; MRE 402; MCR 2.119",
        )
    )
    if lane == "C":
        catalog.append(
            RiskFinding(
                filing_id=filing_id,
                lane=lane,
                category="Immunity",
                severity_score=72,
                risk_statement="Qualified or absolute immunity may narrow the viable defendant and relief set.",
                cure_step="Separate municipal, individual, and judicial theories and verify clearly established law.",
                authority_anchor="42 USC § 1983",
            )
        )
    return catalog
```

### Michigan-Specific Execution Rules

- CI3 must preserve the identity lock for Andrew James Pigors, Emily A. Watson, Hon. Jenny L. McNeill, Pamela Rusco, and Jennifer Barnes P55406 (WITHDREW).
- CI3 must avoid any child full-name disclosure and keep the minor referenced as L.D.W. only.
- CI3 must expose enough structured output for CI6 to validate every citation, statistic, and date.
- CI3 must push any newly discovered timing issue into CI7 and any new docket-derived event into CI8.
- CI3 must keep lane assignments explicit so CI1 can prioritize without guessing.
- CI3 must prefer query-backed facts from litigation_context.db over narrative intuition.

### Sample Inputs

| Input Type | Example | Why It Matters |
| --- | --- | --- |
| Structured row | `CI3-sample-row` | Demonstrates how the module consumes query-backed data. |
| Case anchor | `2024-001507-DC / 2025-002760-CZ / 2023-5907-PP / COA 366810` | Keeps lane and court routing correct. |
| Identity rule | `L.D.W. only` | Forces privacy discipline and QA compatibility. |

### Output Contract

- CI3 returns structured, reviewable output rather than opaque prose.
- CI3 always includes lane, case number, date context, and authority support where applicable.
- CI3 output must be usable by CI1, CI5, and CI6 without manual reinterpretation.
- CI3 output should state assumptions when a rule default is used instead of a docket-specific date.
- CI3 output should flag uncertainty rather than invent precision.
- CI3 output should stay suitable for conversion into hearing notes, dashboards, or filing exhibits.


## CI4: Evidence Gap Analyzer

**Purpose:** Map claims to actual support, distinguish blockers from discoveries and improvements, and generate acquisition tasks that close evidentiary and authority gaps before drafting becomes brittle.

**Design Pattern:** Claim-to-Evidence Coverage Matrix + Acquisition Ticket Generator + Density Heatmap

### Michigan Authority Anchors

- MCR 2.302
- MCR 2.309
- MCR 2.310
- MCR 2.313
- MRE 401
- MRE 901
- MCL 722.23

### Integration Contract

| Direction | Interfaces |
| --- | --- |
| Receives from | claims rows; evidence_quotes coverage; timeline gaps from CI2; risk findings from CI3 |
| Feeds to | BLOCKER / DNEW / NEXT_PATCH inventory; acquisition task list; lane density map; claim support matrix |

### Operating Notes

1. A claim is not filing-ready merely because it sounds legally compelling.
2. Authority gaps and proof gaps should be tracked separately because their cures differ.
3. BLOCKER means the claim should not appear in a verified pleading without additional support.
4. DNEW means a potentially important discovery surfaced and should be routed to CI1 for sequencing review.
5. NEXT_PATCH means the filing can proceed only if CI3 and CI5 remain favorable.
6. Every acquisition task should specify whether the source is document, witness, transcript, police report, or docket.

### Code Example A

```python
from dataclasses import dataclass
import sqlite3

@dataclass(slots=True)
class GapTicket:
    claim_id: str
    lane: str
    gap_type: str
    severity: str
    missing_item: str
    acquisition_task: str

def classify_gap(quote_count: int, authority_count: int, has_deadline: bool) -> str:
    if quote_count == 0:
        return "BLOCKER"
    if authority_count == 0:
        return "BLOCKER" if has_deadline else "DNEW"
    if quote_count < 3:
        return "NEXT_PATCH"
    return "SUPPORTED"

def make_acquisition_task(claim_name: str, gap_type: str) -> str:
    if gap_type == "BLOCKER":
        return f"Acquire primary evidence for claim '{claim_name}' before drafting any sworn factual paragraph."
    if gap_type == "DNEW":
        return f"Research missing authority and add at least one controlling Michigan rule or case for '{claim_name}'."
    return f"Supplement '{claim_name}' with corroborating timeline and exhibit references."
```

### SQL Example

```sql
-- CI4 claim-to-evidence coverage
SELECT
    c.claim_id,
    c.lane,
    c.claim_name,
    COUNT(DISTINCT eq.quote_id) AS supporting_quotes,
    COUNT(DISTINCT ac.authority_id) AS supporting_authorities,
    MAX(CASE WHEN d.status = 'OPEN' THEN 1 ELSE 0 END) AS has_open_deadline
FROM claims c
LEFT JOIN evidence_quotes eq ON eq.claim_id = c.claim_id
LEFT JOIN authority_chains ac ON ac.claim_id = c.claim_id
LEFT JOIN deadlines d ON d.claim_id = c.claim_id
GROUP BY c.claim_id, c.lane, c.claim_name
ORDER BY c.lane, c.claim_name;
```

### Code Example B

```python
def density_by_lane(conn: sqlite3.Connection) -> list[dict]:
    query = """
    SELECT
        c.lane,
        COUNT(DISTINCT c.claim_id) AS claim_count,
        COUNT(DISTINCT eq.quote_id) AS quote_count,
        COUNT(DISTINCT ac.authority_id) AS authority_count
    FROM claims c
    LEFT JOIN evidence_quotes eq ON eq.claim_id = c.claim_id
    LEFT JOIN authority_chains ac ON ac.claim_id = c.claim_id
    GROUP BY c.lane
    ORDER BY c.lane;
    """
    rows = conn.execute(query).fetchall()
    result = []
    for row in rows:
        lane, claim_count, quote_count, authority_count = row
        density = 0 if claim_count == 0 else round((quote_count + authority_count) / claim_count, 2)
        result.append(
            {
                "lane": lane,
                "claim_count": claim_count,
                "quote_count": quote_count,
                "authority_count": authority_count,
                "density": density,
            }
        )
    return result

def gap_dashboard(tickets: list[GapTicket]) -> str:
    lines = ["GAP DASHBOARD", ""]
    for ticket in tickets:
        lines.append(
            f"{ticket.gap_type:<10} | {ticket.severity:<8} | Lane {ticket.lane} | "
            f"{ticket.claim_id} | {ticket.missing_item}"
        )
    return "\n".join(lines)
```

### Michigan-Specific Execution Rules

- CI4 must preserve the identity lock for Andrew James Pigors, Emily A. Watson, Hon. Jenny L. McNeill, Pamela Rusco, and Jennifer Barnes P55406 (WITHDREW).
- CI4 must avoid any child full-name disclosure and keep the minor referenced as L.D.W. only.
- CI4 must expose enough structured output for CI6 to validate every citation, statistic, and date.
- CI4 must push any newly discovered timing issue into CI7 and any new docket-derived event into CI8.
- CI4 must keep lane assignments explicit so CI1 can prioritize without guessing.
- CI4 must prefer query-backed facts from litigation_context.db over narrative intuition.

### Sample Inputs

| Input Type | Example | Why It Matters |
| --- | --- | --- |
| Structured row | `CI4-sample-row` | Demonstrates how the module consumes query-backed data. |
| Case anchor | `2024-001507-DC / 2025-002760-CZ / 2023-5907-PP / COA 366810` | Keeps lane and court routing correct. |
| Identity rule | `L.D.W. only` | Forces privacy discipline and QA compatibility. |

### Output Contract

- CI4 returns structured, reviewable output rather than opaque prose.
- CI4 always includes lane, case number, date context, and authority support where applicable.
- CI4 output must be usable by CI1, CI5, and CI6 without manual reinterpretation.
- CI4 output should state assumptions when a rule default is used instead of a docket-specific date.
- CI4 output should flag uncertainty rather than invent precision.
- CI4 output should stay suitable for conversion into hearing notes, dashboards, or filing exhibits.


## CI5: EGCP Filing Readiness Scorer

**Purpose:** Score Evidence, Grounds, Citations, and Presentation on a 0-25 scale, compute filing readiness, track score drift over time, and identify the weakest component preventing a filing from reaching the ready threshold.

**Design Pattern:** Four-Axis Quadrant Scoring + Trend Tracking + Weakest-Link Diagnostics

### Michigan Authority Anchors

- MCR 2.113
- MCR 2.119
- MCR 7.212
- MCL 722.23
- MCL 722.27
- MCL 722.27a

### Integration Contract

| Direction | Interfaces |
| --- | --- |
| Receives from | claim and evidence matrices from CI4; risk weighting from CI3; QA gate results from CI6; deadline urgency from CI7 |
| Feeds to | filing_readiness rows; readiness dashboards; weakest-component alerts; trend reports for CI1 |

### Operating Notes

1. Do not inflate Presentation just because the prose sounds persuasive.
2. Evidence is about support, not emotion.
3. Grounds requires a valid legal vehicle, not just a grievance.
4. Citations must be actual, verifiable authorities, not placeholders.
5. A score of 65 or higher means filing ready, but CI6 still retains veto power.
6. The weakest component should drive the next improvement cycle.

### Code Example A

```python
from dataclasses import dataclass
from datetime import date
import sqlite3

@dataclass(slots=True)
class EGCPScore:
    filing_id: str
    lane: str
    evidence: int
    grounds: int
    citations: int
    presentation: int
    scored_on: str

    @property
    def total(self) -> int:
        return self.evidence + self.grounds + self.citations + self.presentation

    @property
    def status(self) -> str:
        return "READY" if self.total >= 65 else "DEVELOPING"

def weakest_component(score: EGCPScore) -> tuple[str, int]:
    parts = {
        "Evidence": score.evidence,
        "Grounds": score.grounds,
        "Citations": score.citations,
        "Presentation": score.presentation,
    }
    return min(parts.items(), key=lambda item: item[1])
```

### SQL Example

```sql
-- CI5 readiness scoreboard
SELECT
    filing_id,
    lane,
    evidence_score,
    grounds_score,
    citations_score,
    presentation_score,
    (evidence_score + grounds_score + citations_score + presentation_score) AS total_score,
    scored_on
FROM filing_readiness
ORDER BY total_score DESC, scored_on DESC;
```

### Code Example B

```python
def calculate_egcp(
    evidence_density: float,
    legal_fit: float,
    citation_coverage: float,
    format_health: float,
) -> tuple[int, int, int, int]:
    evidence = min(25, round(evidence_density * 5))
    grounds = min(25, round(legal_fit * 5))
    citations = min(25, round(citation_coverage * 5))
    presentation = min(25, round(format_health * 5))
    return evidence, grounds, citations, presentation

def readiness_trend(conn: sqlite3.Connection, filing_id: str) -> list[dict]:
    query = """
    SELECT scored_on,
           evidence_score,
           grounds_score,
           citations_score,
           presentation_score
    FROM filing_readiness_history
    WHERE filing_id = ?
    ORDER BY scored_on;
    """
    rows = conn.execute(query, (filing_id,)).fetchall()
    trend = []
    for row in rows:
        scored_on, evidence, grounds, citations, presentation = row
        total = evidence + grounds + citations + presentation
        trend.append(
            {
                "scored_on": scored_on,
                "total": total,
                "ready": total >= 65,
                "weakest": min(
                    {
                        "Evidence": evidence,
                        "Grounds": grounds,
                        "Citations": citations,
                        "Presentation": presentation,
                    }.items(),
                    key=lambda item: item[1],
                )[0],
            }
        )
    return trend
```

### Michigan-Specific Execution Rules

- CI5 must preserve the identity lock for Andrew James Pigors, Emily A. Watson, Hon. Jenny L. McNeill, Pamela Rusco, and Jennifer Barnes P55406 (WITHDREW).
- CI5 must avoid any child full-name disclosure and keep the minor referenced as L.D.W. only.
- CI5 must expose enough structured output for CI6 to validate every citation, statistic, and date.
- CI5 must push any newly discovered timing issue into CI7 and any new docket-derived event into CI8.
- CI5 must keep lane assignments explicit so CI1 can prioritize without guessing.
- CI5 must prefer query-backed facts from litigation_context.db over narrative intuition.

### Sample Inputs

| Input Type | Example | Why It Matters |
| --- | --- | --- |
| Structured row | `CI5-sample-row` | Demonstrates how the module consumes query-backed data. |
| Case anchor | `2024-001507-DC / 2025-002760-CZ / 2023-5907-PP / COA 366810` | Keeps lane and court routing correct. |
| Identity rule | `L.D.W. only` | Forces privacy discipline and QA compatibility. |

### Output Contract

- CI5 returns structured, reviewable output rather than opaque prose.
- CI5 always includes lane, case number, date context, and authority support where applicable.
- CI5 output must be usable by CI1, CI5, and CI6 without manual reinterpretation.
- CI5 output should state assumptions when a rule default is used instead of a docket-specific date.
- CI5 output should flag uncertainty rather than invent precision.
- CI5 output should stay suitable for conversion into hearing notes, dashboards, or filing exhibits.


## CI6: 15-Gate QA Validator

**Purpose:** Enforce identity discipline, citation verification, year control, child-name protection, exhibit cross-references, and anti-hallucination rules so nothing reaches a court-ready packet without traceability.

**Design Pattern:** Sequential Gatekeeper Pipeline + Decontamination Filter + Traceability Ledger

### Michigan Authority Anchors

- MCR 2.113
- MCR 2.107
- MCR 7.212
- MCR 8.119(H)
- MRE 901
- MCL 750.539c

### Integration Contract

| Direction | Interfaces |
| --- | --- |
| Receives from | draft documents; citation lists; statistics from CI1-CI5 and CI7-CI8; exhibit references |
| Feeds to | GO / NO-GO verdicts; decontaminated text; repair queue; traceability logs |

### Operating Notes

1. Gate failures are cumulative; one critical failure is enough for NO-GO.
2. Child name protection is absolute: L.D.W. only.
3. Jennifer Barnes P55406 may be mentioned only as WITHDREW.
4. All dates and examples in this superskill are anchored to 2026.
5. MCR 2.113 formatting checks should confirm caption discipline and signature blocks.
6. Every number displayed in dashboards must be query-backed and reproducible.

### Code Example A

```python
from dataclasses import dataclass
import re

BANNED_PATTERNS = {
    "Lincoln David": "Use L.D.W. only per MCR 8.119(H).",
    "Ron Berry Esq": "Ronald Berry is not an attorney.",
    "Jane Berry": "Banned hallucinated identity.",
    "Patricia Berry": "Banned hallucinated identity.",
    "P35878": "Fabricated bar number.",
    "91% alienation": "Untraceable fabricated statistic.",
    "Amy McNeill": "Judge is Hon. Jenny L. McNeill.",
}

REQUIRED_IDENTITIES = {
    "Andrew James Pigors": "Plaintiff pro se",
    "Emily A. Watson": "Defendant",
    "Hon. Jenny L. McNeill": "Judge",
    "Pamela Rusco": "FOC",
}

@dataclass(slots=True)
class GateResult:
    gate: str
    status: str
    detail: str

def gate_identity(document_text: str) -> list[GateResult]:
    results: list[GateResult] = []
    for banned, reason in BANNED_PATTERNS.items():
        if banned.lower() in document_text.lower():
            results.append(GateResult("G1", "FAIL", reason))
    if "2026" not in document_text:
        results.append(GateResult("G2", "FAIL", "Examples and filing dates must remain in 2026."))
    return results
```

### SQL Example

```sql
-- CI6 statistic traceability pattern
SELECT quote_count
FROM (
    SELECT COUNT(*) AS quote_count
    FROM evidence_quotes
    WHERE lane = 'A'
);

SELECT COUNT(*) AS violation_count
FROM judicial_violations
WHERE lane = 'E';

-- Rule: do not print any count in the final document unless it came from a query like the above.
```

### Code Example B

```python
def validate_citations(citations: list[str], conn) -> list[GateResult]:
    results: list[GateResult] = []
    for citation in citations:
        row = conn.execute(
            """
            SELECT authority_id, citation
            FROM authority_chains
            WHERE citation = ?
            """,
            (citation,),
        ).fetchone()
        if row is None:
            results.append(GateResult("G3", "FAIL", f"Unverified citation: {citation}"))
        else:
            results.append(GateResult("G3", "PASS", f"Verified citation: {citation}"))
    return results

def decontaminate_text(document_text: str) -> str:
    cleaned = document_text
    for banned in BANNED_PATTERNS:
        cleaned = re.sub(re.escape(banned), "[REMOVED]", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bLincoln\s+D\w+\b", "L.D.W.", cleaned, flags=re.IGNORECASE)
    return cleaned

def exhibit_cross_reference(exhibits: list[str], document_text: str) -> list[GateResult]:
    results: list[GateResult] = []
    for exhibit in exhibits:
        if exhibit not in document_text:
            results.append(GateResult("G9", "FAIL", f"Missing exhibit cross-reference: {exhibit}"))
    return results
```

### Michigan-Specific Execution Rules

- CI6 must preserve the identity lock for Andrew James Pigors, Emily A. Watson, Hon. Jenny L. McNeill, Pamela Rusco, and Jennifer Barnes P55406 (WITHDREW).
- CI6 must avoid any child full-name disclosure and keep the minor referenced as L.D.W. only.
- CI6 must expose enough structured output for CI6 to validate every citation, statistic, and date.
- CI6 must push any newly discovered timing issue into CI7 and any new docket-derived event into CI8.
- CI6 must keep lane assignments explicit so CI1 can prioritize without guessing.
- CI6 must prefer query-backed facts from litigation_context.db over narrative intuition.

### Sample Inputs

| Input Type | Example | Why It Matters |
| --- | --- | --- |
| Structured row | `CI6-sample-row` | Demonstrates how the module consumes query-backed data. |
| Case anchor | `2024-001507-DC / 2025-002760-CZ / 2023-5907-PP / COA 366810` | Keeps lane and court routing correct. |
| Identity rule | `L.D.W. only` | Forces privacy discipline and QA compatibility. |

### Output Contract

- CI6 returns structured, reviewable output rather than opaque prose.
- CI6 always includes lane, case number, date context, and authority support where applicable.
- CI6 output must be usable by CI1, CI5, and CI6 without manual reinterpretation.
- CI6 output should state assumptions when a rule default is used instead of a docket-specific date.
- CI6 output should flag uncertainty rather than invent precision.
- CI6 output should stay suitable for conversion into hearing notes, dashboards, or filing exhibits.


## CI7: Deadline Intelligence Engine

**Purpose:** Calculate and rank deadlines using docket events, rule windows, and case-specific anchors such as the COA 366810 brief deadline of April 15, 2026, while also monitoring SOL exposure for §1983-related theories.

**Design Pattern:** Rule Clock + Trigger Event Graph + Urgency Ranking Dashboard

### Michigan Authority Anchors

- MCR 2.107
- MCR 2.119
- MCR 7.204
- MCR 7.212
- MCR 7.305
- MCL 600.5805
- 42 USC § 1983

### Integration Contract

| Direction | Interfaces |
| --- | --- |
| Receives from | docket trigger events from CI8; filing plans from CI1; risk escalation from CI3 |
| Feeds to | deadline dashboard; days-remaining alerts; SOL monitoring flags; response window calculations |

### Operating Notes

1. If a docket order supplies a specific date, that date outranks generic rule defaults.
2. Track the COA 366810 brief deadline as April 15, 2026 unless the docket changes.
3. For motions, record both the case-management response window and the actual hearing-notice timing constraints.
4. Borrowed §1983 limitation analysis should be flagged for accrual review rather than treated as self-proving.
5. CI7 deadlines must feed back into CI1 priorities and CI3 risk calculations.
6. Open deadlines should remain visible even if a filing is not yet ready.

### Code Example A

```python
from dataclasses import dataclass
from datetime import date, timedelta

@dataclass(slots=True)
class DeadlineItem:
    lane: str
    matter: str
    trigger_date: date
    due_date: date
    authority: str
    rule_note: str

    @property
    def days_remaining(self) -> int:
        return (self.due_date - date(2026, 3, 27)).days

def motion_response_window(trigger_date: date) -> DeadlineItem:
    return DeadlineItem(
        lane="A",
        matter="Case-management motion response window",
        trigger_date=trigger_date,
        due_date=trigger_date + timedelta(days=21),
        authority="MCR 2.119(C) + case-management configuration",
        rule_note="Track a 21-day response window in this intelligence system unless a shorter order or hearing notice controls.",
    )

def coa_brief_deadline() -> DeadlineItem:
    return DeadlineItem(
        lane="F",
        matter="COA 366810 appellate brief",
        trigger_date=date(2026, 3, 1),
        due_date=date(2026, 4, 15),
        authority="MCR 7.212",
        rule_note="User-specified appellate brief deadline anchor.",
    )
```

### SQL Example

```sql
-- CI7 deadline dashboard source
SELECT
    lane,
    case_number,
    trigger_event,
    trigger_date,
    due_date,
    authority,
    status,
    CAST(julianday(due_date) - julianday('2026-03-27') AS INTEGER) AS days_remaining
FROM deadlines
ORDER BY due_date ASC, lane ASC;
```

### Code Example B

```python
def section_1983_sol(accrual_date: date) -> DeadlineItem:
    return DeadlineItem(
        lane="C",
        matter="Borrowed Michigan personal injury limitation period for §1983 theory",
        trigger_date=accrual_date,
        due_date=accrual_date.replace(year=accrual_date.year + 3),
        authority="MCL 600.5805 + 42 USC § 1983",
        rule_note="Review tolling and accrual facts before relying on the computed date.",
    )

def urgency_band(item: DeadlineItem) -> str:
    if item.days_remaining <= 3:
        return "CRITICAL"
    if item.days_remaining <= 10:
        return "HIGH"
    if item.days_remaining <= 21:
        return "MEDIUM"
    return "LOW"

def deadline_dashboard(items: list[DeadlineItem]) -> str:
    lines = ["DEADLINE INTELLIGENCE DASHBOARD", ""]
    for item in sorted(items, key=lambda i: i.due_date):
        lines.append(
            f"{urgency_band(item):<8} | {item.lane} | {item.matter:<45} | "
            f"{item.due_date.isoformat()} | {item.authority}"
        )
    return "\n".join(lines)
```

### Michigan-Specific Execution Rules

- CI7 must preserve the identity lock for Andrew James Pigors, Emily A. Watson, Hon. Jenny L. McNeill, Pamela Rusco, and Jennifer Barnes P55406 (WITHDREW).
- CI7 must avoid any child full-name disclosure and keep the minor referenced as L.D.W. only.
- CI7 must expose enough structured output for CI6 to validate every citation, statistic, and date.
- CI7 must push any newly discovered timing issue into CI7 and any new docket-derived event into CI8.
- CI7 must keep lane assignments explicit so CI1 can prioritize without guessing.
- CI7 must prefer query-backed facts from litigation_context.db over narrative intuition.

### Sample Inputs

| Input Type | Example | Why It Matters |
| --- | --- | --- |
| Structured row | `CI7-sample-row` | Demonstrates how the module consumes query-backed data. |
| Case anchor | `2024-001507-DC / 2025-002760-CZ / 2023-5907-PP / COA 366810` | Keeps lane and court routing correct. |
| Identity rule | `L.D.W. only` | Forces privacy discipline and QA compatibility. |

### Output Contract

- CI7 returns structured, reviewable output rather than opaque prose.
- CI7 always includes lane, case number, date context, and authority support where applicable.
- CI7 output must be usable by CI1, CI5, and CI6 without manual reinterpretation.
- CI7 output should state assumptions when a rule default is used instead of a docket-specific date.
- CI7 output should flag uncertainty rather than invent precision.
- CI7 output should stay suitable for conversion into hearing notes, dashboards, or filing exhibits.


## CI8: Multi-Court Docket Monitor

**Purpose:** Track multi-court docket activity for 14th Circuit, PPO, COA, and potential MSC/Federal lanes; detect new entries; compute response implications; and monitor compliance with court orders.

**Design Pattern:** Polling Observer + Compliance Ledger + Event-to-Deadline Router

### Michigan Authority Anchors

- MCR 2.107
- MCR 2.119
- MCR 2.602
- MCR 3.210
- MCR 3.707
- MCR 7.204
- MCR 7.212

### Integration Contract

| Direction | Interfaces |
| --- | --- |
| Receives from | known case numbers; existing docket snapshots; order compliance facts |
| Feeds to | new-entry alerts; response calculations for CI7; order compliance ledger; status awareness for CI1 |

### Operating Notes

1. A new order should create both a compliance task and a deadline review.
2. A new motion should trigger CI7 even if the filing is weak or duplicative.
3. COA entries require immediate cross-check against MCR 7.212 deliverables.
4. Potential MSC or Federal matters can be added without disturbing the lane map.
5. Keep case numbers exact: 2024-001507-DC, 2025-002760-CZ, 2023-5907-PP, and COA 366810.
6. Docket monitoring is only useful if entries are converted into actionable next steps.

### Code Example A

```python
from dataclasses import dataclass
from datetime import date

MONITORED_CASES = {
    "2024-001507-DC": {"lane": "A", "court": "14th Circuit"},
    "2025-002760-CZ": {"lane": "B", "court": "14th Circuit"},
    "2023-5907-PP": {"lane": "D", "court": "14th Circuit"},
    "366810": {"lane": "F", "court": "Michigan Court of Appeals"},
}

@dataclass(slots=True)
class DocketEntry:
    case_number: str
    lane: str
    court: str
    entry_date: date
    title: str
    docket_number: str
    entered_by: str

def classify_entry(entry: DocketEntry) -> str:
    title = entry.title.lower()
    if "order" in title:
        return "ORDER"
    if "motion" in title:
        return "MOTION"
    if "brief" in title or "appeal" in title:
        return "APPELLATE"
    return "NOTICE"
```

### SQL Example

```sql
-- CI8 docket monitoring query
SELECT
    case_number,
    lane,
    event_date,
    docket_number,
    title,
    entered_by,
    compliance_required,
    compliance_due_date
FROM docket_events
WHERE case_number IN ('2024-001507-DC', '2025-002760-CZ', '2023-5907-PP', '366810')
ORDER BY event_date DESC, docket_number DESC;
```

### Code Example B

```python
def compliance_alerts(entries: list[DocketEntry]) -> list[dict]:
    alerts: list[dict] = []
    for entry in entries:
        kind = classify_entry(entry)
        if kind == "ORDER":
            alerts.append(
                {
                    "case_number": entry.case_number,
                    "lane": entry.lane,
                    "alert": "New order entered; confirm service, obligations, and response path.",
                    "authority": "MCR 2.602; MCR 2.107",
                }
            )
        elif kind == "MOTION":
            alerts.append(
                {
                    "case_number": entry.case_number,
                    "lane": entry.lane,
                    "alert": "Motion entered; CI7 should calculate response timing and hearing implications.",
                    "authority": "MCR 2.119",
                }
            )
    return alerts

def new_entry_delta(previous_numbers: set[str], current_entries: list[DocketEntry]) -> list[DocketEntry]:
    return [entry for entry in current_entries if entry.docket_number not in previous_numbers]
```

### Michigan-Specific Execution Rules

- CI8 must preserve the identity lock for Andrew James Pigors, Emily A. Watson, Hon. Jenny L. McNeill, Pamela Rusco, and Jennifer Barnes P55406 (WITHDREW).
- CI8 must avoid any child full-name disclosure and keep the minor referenced as L.D.W. only.
- CI8 must expose enough structured output for CI6 to validate every citation, statistic, and date.
- CI8 must push any newly discovered timing issue into CI7 and any new docket-derived event into CI8.
- CI8 must keep lane assignments explicit so CI1 can prioritize without guessing.
- CI8 must prefer query-backed facts from litigation_context.db over narrative intuition.

### Sample Inputs

| Input Type | Example | Why It Matters |
| --- | --- | --- |
| Structured row | `CI8-sample-row` | Demonstrates how the module consumes query-backed data. |
| Case anchor | `2024-001507-DC / 2025-002760-CZ / 2023-5907-PP / COA 366810` | Keeps lane and court routing correct. |
| Identity rule | `L.D.W. only` | Forces privacy discipline and QA compatibility. |

### Output Contract

- CI8 returns structured, reviewable output rather than opaque prose.
- CI8 always includes lane, case number, date context, and authority support where applicable.
- CI8 output must be usable by CI1, CI5, and CI6 without manual reinterpretation.
- CI8 output should state assumptions when a rule default is used instead of a docket-specific date.
- CI8 output should flag uncertainty rather than invent precision.
- CI8 output should stay suitable for conversion into hearing notes, dashboards, or filing exhibits.

## Decision Tree for Module Routing

```text
START
  │
  ├─ Need to decide what to file, when, or in which lane?
  │      └─► CI1 Strategic Command Center
  │
  ├─ Need to reconstruct what happened and when?
  │      └─► CI2 Timeline Forensics Engine
  │
  ├─ Need to know how vulnerable a filing is?
  │      └─► CI3 Risk Assessment Matrix
  │
  ├─ Need to know what proof or authority is missing?
  │      └─► CI4 Evidence Gap Analyzer
  │
  ├─ Need a filing-ready score or weakest component?
  │      └─► CI5 EGCP Filing Readiness Scorer
  │
  ├─ Need anti-hallucination, name, date, citation, or exhibit verification?
  │      └─► CI6 15-Gate QA Validator
  │
  ├─ Need to compute or rank deadlines?
  │      └─► CI7 Deadline Intelligence Engine
  │
  └─ Need to detect new docket entries or order-compliance obligations?
         └─► CI8 Multi-Court Docket Monitor
```

**Routing override rules**

- If the question includes both **what happened** and **what to do next**, run **CI2 first**, then **CI1**.
- If the question includes both **can we file** and **how strong is it**, run **CI4 → CI5 → CI3** in that order.
- If a draft already exists, inject **CI6** before any recommendation to file.
- If a new docket event arrived today, route **CI8 → CI7 → CI1** before editing any filing plan.

## Cross-Module Integration Patterns

### Cascade 1 — Docket Shock Response

1. CI8 detects a new order or motion entry.
2. CI7 computes response and compliance dates.
3. CI2 injects the event into the master chronology.
4. CI1 re-ranks lanes and filing sequence.
5. CI6 validates any updated draft before release.

### Cascade 2 — Weak Filing Rescue Loop

1. CI5 reports a total below 65 or a weak Evidence/Citations component.
2. CI4 identifies missing support and generates acquisition tasks.
3. CI3 reassesses whether the risk profile is tolerable.
4. CI1 decides whether to file for preservation or delay for development.
5. CI6 blocks release until repaired facts and citations are verified.

### Cascade 3 — Misconduct to Appellate Preservation

1. CI2 reconstructs chronology showing notice defects or order irregularities.
2. CI3 separates disqualification risk from immunity arguments.
3. CI1 sequences Lane E and Lane F actions to preserve review posture.
4. CI7 clocks deadlines tied to objections, appeals, or applications.
5. CI6 confirms no fabricated statistics or names contaminate the record.

### Cascade 4 — Convergence Opportunity Capture

1. CI4 notices the same evidence cluster supports multiple claims across lanes.
2. CI2 aligns those facts in a single temporal chain.
3. CI1 identifies the lane that can produce the highest leverage first.
4. CI5 measures whether the chosen filing is actually ready.
5. CI8 watches for the resulting docket activity and CI7 converts it into next deadlines.

## Domain Applications

### Michigan Custody Modification Readiness

- Use CI2 to assemble the chronology of parenting-time denials and notice defects.
- Use CI4 to confirm support for **MCL 722.27** threshold arguments and **MCL 722.23** factor narratives.
- Use CI5 to score the draft motion and identify whether Evidence or Grounds is weak.
- Use CI6 to enforce **L.D.W. only**, 2026 date discipline, and verified citations.

### PPO Event Escalation Review

- Use CI8 to monitor **2023-5907-PP** for new orders or scheduled hearings.
- Use CI7 to compute the response or hearing-preparation window.
- Use CI2 to align PPO events with custody-lane consequences.
- Use CI3 to flag overreach, mootness, or proof-density risks before filing any motion to modify or terminate.

### Appellate Lane COA 366810

- Use CI7 to anchor the appellate brief deadline at **April 15, 2026**.
- Use CI2 and CI8 together to reconstruct the precise procedural history for the statement of facts.
- Use CI5 to measure **MCR 7.212** readiness across Evidence, Grounds, Citations, and Presentation.
- Use CI6 to validate caption, names, dates, citations, and minor-child anonymization.

### Multi-Lane Strategic Review for a Pro Se Litigant

- Use CI1 to decide whether Lane A, D, E, or F gets the next filing slot.
- Use CI3 to surface the risk of filing too early versus waiting too long.
- Use CI4 to prevent emotionally compelling but under-evidenced claims from entering a verified filing.
- Use CI8 and CI7 to keep the sequence tethered to actual court activity rather than intuition.

## Quick Reference Card

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ FORGE-CASE-INTELLIGENCE QUICK REFERENCE                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│ CI1 → What should we file next?                                             │
│ CI2 → What happened, in what order, and where are the gaps?                 │
│ CI3 → What can opposing counsel or the court attack?                        │
│ CI4 → What evidence or authority is still missing?                          │
│ CI5 → Are we filing ready (EGCP ≥ 65)?                                      │
│ CI6 → Did the draft survive all 15 gates?                                   │
│ CI7 → What is due, when, and how urgent is it?                              │
│ CI8 → What changed on the docket and what does it trigger?                  │
├──────────────────────────────────────────────────────────────────────────────┤
│ Locked identities: Andrew James Pigors / Emily A. Watson / Hon. Jenny L.    │
│ McNeill / Pamela Rusco / Jennifer Barnes P55406 (WITHDREW)                  │
│ Minor child: L.D.W. only                                                    │
│ Core cases: 2024-001507-DC / 2025-002760-CZ / 2023-5907-PP / COA 366810    │
│ Hard rule: Never print an unqueried statistic                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Unified Operating Doctrine

FORGE-CASE-INTELLIGENCE is not a generic dashboard writer. It is a **litigation-grade
operational system**. It assumes that every improvement in strategy must be tied to
timeline proof, every risk must have a cure path, every deadline must map to a trigger,
every docket event must generate a next-step implication, and every filing score must
stay subordinate to verification. The forge therefore works best when all eight modules
are treated as one integrated intelligence loop rather than independent utilities.

**Doctrine summary**

- Strategy without chronology is guesswork.
- Chronology without evidence coverage is brittle.
- Evidence without readiness scoring is inefficient.
- Readiness without QA is dangerous.
- Docket awareness without deadlines is passive.
- Deadlines without strategy create panic instead of leverage.

The correct operating sequence is:

1. Observe the docket and incoming facts.
2. Normalize them into chronology.
3. Measure support and exposure.
4. Score readiness.
5. Validate ruthlessly.
6. File only when the record, timing, and quality gates align.

## Appendix: Query Templates

### A. Evidence density by filing

```sql
SELECT filing_id,
       lane,
       evidence_score,
       grounds_score,
       citations_score,
       presentation_score,
       (evidence_score + grounds_score + citations_score + presentation_score) AS total_score
FROM filing_readiness
ORDER BY total_score DESC;
```

### B. Judicial-violation chronology

```sql
SELECT violation_date,
       lane,
       violation_type,
       actor_name,
       finding
FROM judicial_violations
ORDER BY violation_date;
```

### C. Deadline queue

```sql
SELECT case_number,
       lane,
       due_date,
       authority,
       status
FROM deadlines
ORDER BY due_date;
```

### D. Docket activity stream

```sql
SELECT event_date,
       case_number,
       docket_number,
       title
FROM docket_events
ORDER BY event_date DESC;
```

