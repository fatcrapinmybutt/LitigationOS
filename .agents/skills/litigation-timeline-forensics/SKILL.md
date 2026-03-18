---
name: litigation-timeline-forensics
description: "Chronological event reconstruction and contradiction detection for multi-source litigation evidence. Use when: build timeline, detect contradictions, gap analysis, event reconstruction, parallel timeline, custody exchange log, compliance timeline."
---

# Litigation Timeline Forensics

**Role**: Chronological event reconstruction and contradiction detection specialist for multi-source, multi-lane litigation (Pigors v. Watson). Compiles events from transcripts, filings, records, exhibits, and police reports into unified timelines. Detects contradictions between accounts, identifies evidentiary gaps, generates visual timeline outputs, and tracks court order compliance across all 6 case lanes.

## Capabilities

- Multi-source event compilation from transcripts, filings, court records, exhibits, and police reports
- Contradiction detection: witness vs. witness, witness vs. official record, filing vs. filing
- Gap identification: missing time periods, undocumented events, suppressed evidence windows
- Mermaid diagram and Gantt chart generation for visual timeline presentation
- Custody exchange timeline with incident mapping for Lane A
- Court order compliance tracking (which orders violated, when, by whom)
- Evidence chain-of-custody tracking with timestamp verification
- Parallel timeline comparison (Andrew's account vs. Emily's account vs. Official record)
- Temporal pattern recognition (recurring violations, escalation sequences)
- Statute of limitations tracking per claim type

## Requirements

- Access to `litigation_context.db` for indexed evidence with timestamps
- All source documents must have date metadata (filing date, event date, or extraction date)
- Lane assignment (A-F) for proper routing — events can span lanes
- MANBEARPIG inference engine for contradiction scoring
- Python 3.12+ with `datetime` and `zoneinfo` (all timestamps in America/Detroit timezone)

## Patterns

### Pattern 1: Multi-Source Event Compilation

**When to use**: At the start of any case analysis — build the master timeline before any argument construction.

```python
from datetime import datetime, date
from typing import List, Optional
from zoneinfo import ZoneInfo

MI_TZ = ZoneInfo("America/Detroit")

def compile_master_timeline(
    lane: str,
    sources: List[dict],
) -> List[dict]:
    """
    Compile events from multiple sources into a single chronological timeline.
    Each event is tagged with source, confidence, and lane.
    """
    events = []
    for source in sources:
        for raw_event in source["events"]:
            event = {
                "date": raw_event["date"],
                "time": raw_event.get("time"),  # None if unknown
                "description": raw_event["description"],
                "source_type": source["type"],  # transcript, filing, exhibit, police_report
                "source_ref": source["reference"],  # Exhibit A-1, Dkt #42, etc.
                "actors": raw_event.get("actors", []),
                "lane": lane,
                "confidence": score_date_confidence(raw_event),
                "contradicts": [],  # Populated by contradiction detection pass
                "supports": [],     # Cross-references that corroborate this event
            }
            events.append(event)

    # Sort chronologically — stable sort preserves source order for same-date events
    events.sort(key=lambda e: (e["date"], e["time"] or "00:00:00"))
    return events


def score_date_confidence(event: dict) -> float:
    """Score how reliable the date attribution is (0.0 to 1.0)."""
    if event.get("date_source") == "document_metadata":
        return 1.0  # Court filing stamp, official record date
    elif event.get("date_source") == "witness_testimony":
        return 0.7  # Witness recollection — may be approximate
    elif event.get("date_source") == "inferred":
        return 0.4  # Date inferred from context
    return 0.2  # Unknown source
```

### Pattern 2: Contradiction Detection Engine

**When to use**: After compiling events from multiple sources — run contradiction detection to find impeachment material.

```python
def detect_contradictions(
    timeline_a: List[dict],  # e.g., Andrew's account
    timeline_b: List[dict],  # e.g., Emily's account
    tolerance_days: int = 3,
) -> List[dict]:
    """
    Compare two timelines and flag contradictions.
    A contradiction exists when:
    1. Same event described differently by two sources
    2. One source claims event happened, other denies/omits it
    3. Timeline of events is logically impossible (A before B in one, B before A in other)
    """
    contradictions = []
    for event_a in timeline_a:
        for event_b in timeline_b:
            # Check if events reference the same incident (within tolerance window)
            if not events_overlap(event_a, event_b, tolerance_days):
                continue

            # Compare descriptions for factual conflicts
            conflict = compare_event_facts(event_a, event_b)
            if conflict["severity"] > 0:
                contradictions.append({
                    "event_date": event_a["date"],
                    "source_a": event_a["source_ref"],
                    "source_b": event_b["source_ref"],
                    "claim_a": event_a["description"],
                    "claim_b": event_b["description"],
                    "conflict_type": conflict["type"],
                    "severity": conflict["severity"],  # 1-10
                    "impeachment_value": conflict["severity"] >= 7,
                    "lanes_affected": list({event_a["lane"], event_b["lane"]}),
                })

    return sorted(contradictions, key=lambda c: c["severity"], reverse=True)
```

### Pattern 3: Mermaid Timeline Generation

**When to use**: When preparing visual exhibits for court filings or brief appendices.

```python
def generate_mermaid_timeline(events: List[dict], title: str) -> str:
    """Generate a Mermaid Gantt chart from timeline events."""
    lines = [
        f"gantt",
        f"    title {title}",
        f"    dateFormat YYYY-MM-DD",
        f"    axisFormat %b %Y",
    ]

    # Group events by lane for sectioning
    lanes_seen = {}
    for event in events:
        lane = event["lane"]
        if lane not in lanes_seen:
            lanes_seen[lane] = True
            lane_labels = {
                "A": "Lane A — Custody", "B": "Lane B — Housing",
                "C": "Lane C — Convergence", "D": "Lane D — PPO",
                "E": "Lane E — Misconduct", "F": "Lane F — Appellate",
            }
            lines.append(f"    section {lane_labels.get(lane, lane)}")

        # Mermaid task entry
        desc = event["description"][:60].replace(":", " -")
        evt_date = event["date"]
        severity_tag = "crit," if event.get("contradicts") else ""
        lines.append(f"    {desc} :{severity_tag} {evt_date}, 1d")

    return "\n".join(lines)
```

### Pattern 4: Court Order Compliance Tracker

**When to use**: For Lane A/D — track compliance or non-compliance with every court order by all parties.

```python
def build_compliance_timeline(
    orders: list,
    events: list,
    party: str,
) -> list:
    """
    For each court order, track whether it was complied with, when,
    and by whom. Non-compliance events feed into contempt motions
    and judicial misconduct analysis.
    """
    compliance_records = []
    for order in orders:
        # Find events related to this order
        related_events = [
            e for e in events
            if order["order_id"] in e.get("related_orders", [])
        ]
        
        complied = any(
            e.get("compliance_status") == "complied" and e.get("actor") == party
            for e in related_events
        )
        
        violations = [
            e for e in related_events
            if e.get("compliance_status") == "violated" and e.get("actor") == party
        ]
        
        compliance_records.append({
            "order_id": order["order_id"],
            "order_date": order["date"],
            "order_description": order["description"],
            "party": party,
            "complied": complied,
            "violation_count": len(violations),
            "violations": [
                {
                    "date": v["date"],
                    "description": v["description"],
                    "source_ref": v["source_ref"],
                    "severity": v.get("severity", "unknown"),
                }
                for v in violations
            ],
            "contempt_eligible": len(violations) > 0 and order.get("enforceable", True),
            "mcl_authority": "MCL 722.27a (parenting time); MCL 600.1711 (contempt)",
        })
    
    return sorted(compliance_records, key=lambda r: r["order_date"])
```

### Pattern 5: Temporal Gap Detection

**When to use**: After compiling the master timeline — identify suspicious gaps where events should exist but documentation is missing.

```python
def detect_timeline_gaps(
    events: list,
    expected_frequency: str = "weekly",
    lane: str = "A",
) -> list:
    """
    Identify time periods where no events are documented but activity
    is expected. In custody cases (Lane A), gaps in custody exchange
    records suggest suppressed evidence or undocumented incidents.
    """
    gaps = []
    freq_days = {"daily": 1, "weekly": 7, "biweekly": 14, "monthly": 30}
    threshold = freq_days.get(expected_frequency, 7)
    
    sorted_events = sorted(events, key=lambda e: e["date"])
    for i in range(1, len(sorted_events)):
        prev_date = sorted_events[i - 1]["date"]
        curr_date = sorted_events[i]["date"]
        gap_days = (curr_date - prev_date).days
        
        if gap_days > threshold * 2:  # Gap is 2x the expected frequency
            gaps.append({
                "gap_start": prev_date.isoformat(),
                "gap_end": curr_date.isoformat(),
                "gap_days": gap_days,
                "expected_max_gap": threshold,
                "severity": "HIGH" if gap_days > threshold * 4 else "MODERATE",
                "lane": lane,
                "investigation_note": f"No documented events for {gap_days} days "
                                       f"(expected every {threshold} days). "
                                       f"Check for suppressed evidence or undocumented incidents.",
                "acquisition_tasks": [
                    f"FOIA request for records between {prev_date} and {curr_date}",
                    f"Subpoena third-party records covering this period",
                    f"Deposition question: 'What happened between {prev_date} and {curr_date}?'",
                ],
            })
    
    return gaps
```

## Anti-Patterns

### ❌ Building Timelines from a Single Source

**Why bad**: A timeline built from only Andrew's account or only Emily's filings is an advocacy document, not a forensic reconstruction. Courts and opposing counsel will discredit single-source timelines. Contradiction detection requires at minimum two independent sources to function.

**Instead**: Always compile from at least 3 source categories: (1) official court records/filings, (2) party testimony/statements, (3) independent records (police reports, medical records, school records). Tag each event with its source for transparency.

### ❌ Treating Approximate Dates as Exact

**Why bad**: Witness testimony often uses approximate dates ("sometime in March 2024"). Recording this as "2024-03-15" creates false precision that can be used against you when the actual date is proven different. This undermines the entire timeline's credibility.

**Instead**: Use a `date_confidence` score (Pattern 1) and mark approximate dates explicitly. When exact dates are unknown, record as date ranges: `{"date_start": "2024-03-01", "date_end": "2024-03-31", "date_confidence": 0.4}`. Visual timelines should show ranges, not points, for approximate dates.

### ❌ Ignoring Timezone and Business-Hours Context

**Why bad**: Michigan court filings use Eastern Time (America/Detroit). Police reports may use 24-hour format. Medical records may use UTC. Mixing timezones silently corrupts the chronological order and creates phantom contradictions.

**Instead**: Normalize all timestamps to `America/Detroit` timezone at ingestion. Store original timezone alongside normalized time. Flag events that occur outside business hours (courts), after midnight (custody exchanges), or on weekends/holidays for special attention.

## Michigan-Specific Rules

- **MCR 3.206**: Custody proceedings require detailed timeline of child's living arrangements — compile from Lane A evidence
- **MCL 722.23**: Best interest factors require temporal analysis — factor (c) stability: length of time in environment; factor (j) willingness to facilitate relationship
- **MCR 2.612**: Void judgment timeline — track jurisdictional events to establish when jurisdiction was lost
- **MCR 2.119(F)(1)**: Motion for reconsideration — 21-day deadline from order entry, requires precise date tracking
- **MCR 2.108**: Time computation rules — exclude day of event, include last day, weekend/holiday extension
- **MCL 600.5805**: Statute of limitations tracking — 3 years for personal injury, 6 years for contract
- **MCR 8.119(H)**: Minor child referenced as L.D.W. only in all timeline outputs
- **MCL 722.27a**: Parenting time compliance tracking — document each violation with date, time, circumstances

## Integration Points

- **litigation-analysis-engine**: Receives compiled timelines for pattern analysis and anomaly detection
- **litigation-evidence-harvester**: Provides timestamped evidence records for timeline compilation
- **litigation-impeachment-engine**: Consumes contradiction detection output for impeachment packages
- **litigation-deposition-strategist**: Uses timeline gaps to generate deposition questions about missing periods
- **litigation-witness-preparation**: Timeline inconsistencies inform cross-examination strategy
- **litigation-custody-specialist**: Custody exchange timelines feed best-interest-factor analysis
- **litigation-judicial-analyst**: Court order compliance timelines support misconduct patterns (Lane E)
- **MANBEARPIG inference engine**: Powers contradiction scoring and temporal pattern recognition


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

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| A | 3,502 | 2024-001507-DC | 14th Circuit, Muskegon County |
| B | 3,531 | 2025-002760-CZ | 14th Circuit, Muskegon County |
| C | 279 | USDC filing pending | U.S. District Court, W.D. Michigan |
| D | 6,462 | 2023-5907-PP | 14th Circuit |
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |
| F | 975 | COA 366810 | Michigan Court of Appeals / Supreme Court |

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
SELECT * FROM pages_fts WHERE pages_fts MATCH 'habitability OR housing OR landlord';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'protection AND order';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
SELECT * FROM pages_fts WHERE pages_fts MATCH 'appeal AND error AND preserved';
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
| E (Judicial Misconduct (JTC)) | F | Misconduct findings → appellate arguments |

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
| Custody Modification | 65/100 | A,B,C,D,E,F | Verified |
| Emergency Custody | 55/100 | A,B,C,D,E,F | Verified |
| PPO Modification/Termination | 60/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C10) | 75/100 | A,B,C,D,E,F | Verified |
| Summary Disposition (C8) | 70/100 | A,B,C,D,E,F | Verified |
| Contempt | 70/100 | A,B,C,D,E,F | Verified |
| Judicial Disqualification | 75/100 | A,B,C,D,E,F | Verified |
| Appeal Brief | 70/100 | A,B,C,D,E,F | Verified |
| Leave Application (MSC) | 80/100 | A,B,C,D,E,F | Verified |
| Default Judgment | 60/100 | A,B,C,D,E,F | Verified |
| TRO Application | 60/100 | A,B,C,D,E,F | Verified |
| Federal §1983 Complaint | 70/100 | A,B,C,D,E,F | Verified |
| JTC Formal Complaint | 75/100 | A,B,C,D,E,F | Verified |

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

**Lane B: Housing (Shady Oaks)**
- Case: 2025-002760-CZ
- Court: 14th Circuit, Muskegon County
- Judge: TBD
- Key Statutes: MCL 554.139, MCL 125.534-540, MCL 600.2918
- Key Rules: MCR 2.116, MCR 2.603
- Critical Evidence: 6GB evidence, HOA complaints, LARA registrations, FOIA personnel

**Lane C: Federal Civil Rights (§1983)**
- Case: USDC filing pending
- Court: U.S. District Court, W.D. Michigan
- Judge: TBD
- Key Statutes: 42 USC § 1983, 42 USC § 1985, 42 USC § 1988
- Key Rules: FRCP 8, FRCP 12, FRCP 56
- Critical Evidence: Color of law violations, Monell policy, pattern evidence across lanes

**Lane D: PPO (Protection Orders)**
- Case: 2023-5907-PP
- Court: 14th Circuit
- Judge: Hon. Jenny L. McNeill
- Key Statutes: MCL 600.2950, MCL 750.411h
- Key Rules: MCR 3.705-3.708
- Critical Evidence: False PPO allegations pattern, zero CPS findings after 1 investigation

**Lane E: Judicial Misconduct (JTC)**
- Case: JTC Complaint - McNeill
- Court: Judicial Tenure Commission
- Judge: Target: Hon. Jenny L. McNeill
- Key Statutes: Const 1963 art 6 § 30, MCR 9.104-9.205
- Key Rules: MCR 2.003, Code of Judicial Conduct
- Critical Evidence: 1,127 violations, 44% ex parte rate, muting father 7x in hearing

**Lane F: Appellate (COA/MSC)**
- Case: COA 366810
- Court: Michigan Court of Appeals / Supreme Court
- Judge: Panel TBD
- Key Statutes: MCL 722.28, MCL 600.308
- Key Rules: MCR 7.203-7.305
- Critical Evidence: Preserved errors, constitutional violations, due process denial

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
