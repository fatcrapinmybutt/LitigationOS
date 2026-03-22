# Ω6 Timeline Intelligence Brain — OMEGA-INFINITY Reference
> Module 6 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose

Provide the chronological backbone for all litigation outputs — every affidavit, motion, brief, and complaint depends on accurate, source-pinned event sequencing. This brain structures raw timeline data into 10 queryable chronology views, detects patterns across time, identifies gaps, and feeds chronological spines to Modules M1 (Evidence Pipeline), M4 (Filing Factory), and M5 (Strategic Command).

---

## 1. Master Timeline Data Sources

### 1.1 Primary: `case_timeline`

The canonical timeline table. All chronology views derive from this source.

```sql
PRAGMA table_info(case_timeline);
-- Columns: id, event_date, event_type, description, source_file, source_quote,
--          lane, case_number, is_key_event, created_at
```

**Live count:** `SELECT COUNT(*) FROM case_timeline;`

**Event type distribution:**

```sql
SELECT event_type, COUNT(*) as cnt
FROM case_timeline
GROUP BY event_type
ORDER BY cnt DESC;
```

Known event types: `violation`, `other`, `order`, `filing`, `incident`, `communication`, `hearing`.

**Lane distribution:**

```sql
SELECT lane, COUNT(*) as cnt
FROM case_timeline
WHERE lane IS NOT NULL
GROUP BY lane
ORDER BY cnt DESC;
```

Known lanes: E (judicial misconduct — largest), D (PPO), A (custody), B (housing), F (appellate).

### 1.2 Secondary: `docket_events`

Court docket entries with filing attribution — essential for procedural chronology.

```sql
PRAGMA table_info(docket_events);
-- Columns: id, case_number, event_date, event_type, description, filed_by,
--          source_file, created_at
```

**Live count:** `SELECT COUNT(*) FROM docket_events;`

**Case number distribution:**

```sql
SELECT case_number, COUNT(*) as cnt
FROM docket_events
GROUP BY case_number
ORDER BY cnt DESC;
```

### 1.3 Tertiary: `alienation_timeline`

Specialized timeline for parenting time withholding episodes with cumulative day tracking.

```sql
PRAGMA table_info(alienation_timeline);
-- Columns: id, event_date, event_description, category, evidence_source,
--          source_table, source_id, quote_text, mcl_section, withholding_episode,
--          days_in_episode, cumulative_days_withheld, lane, case_number,
--          relevance_score, created_at
```

**Live count:** `SELECT COUNT(*) FROM alienation_timeline;`

### 1.4 Quaternary: `judicial_bias_chronology`

Dedicated bias event timeline with canon/MCR violation attribution.

```sql
PRAGMA table_info(judicial_bias_chronology);
-- Columns: id, date, event_description, canon_violated, evidence_source,
--          severity, mcr_violation, filing_relevance, source_table,
--          source_quote, lane, created_at
```

**Live count:** `SELECT COUNT(*) FROM judicial_bias_chronology;`

---

## 2. Ten Required Chronology Views

Each chronology view is a filtered, ordered projection of the master timeline data. Build each view using SQL queries against `case_timeline`, `docket_events`, `alienation_timeline`, and `judicial_bias_chronology` as appropriate.

### View 1: MASTER_CHRONOLOGY

**Purpose:** Complete event sequence across all lanes, all types.

```sql
SELECT ct.id AS ChronoID, ct.event_date AS DateOrRange, ct.event_type AS EventType,
       ct.description AS Description, ct.lane AS Lane, ct.case_number AS CaseNumber,
       ct.source_file AS SourcePath, ct.is_key_event AS IsKeyEvent
FROM case_timeline ct
ORDER BY ct.event_date ASC, ct.id ASC;
```

**Enrichment:** Join with `docket_events` for filing attribution:

```sql
SELECT ct.event_date, ct.event_type, ct.description, ct.lane,
       de.filed_by, de.event_type AS docket_type
FROM case_timeline ct
LEFT JOIN docket_events de ON ct.event_date = de.event_date
  AND ct.case_number = de.case_number
ORDER BY ct.event_date ASC;
```

### View 2: WATSON_CLUSTER_CHRONOLOGY (Custody/PPO/Contempt)

```sql
SELECT id, event_date, event_type, description, lane, source_file, source_quote
FROM case_timeline
WHERE lane IN ('A', 'D')
  OR description LIKE '%Watson%'
  OR description LIKE '%custody%'
  OR description LIKE '%PPO%'
  OR description LIKE '%contempt%'
ORDER BY event_date ASC;
```

**Enrichment from alienation_timeline:**

```sql
SELECT event_date, event_description, category, withholding_episode,
       cumulative_days_withheld, evidence_source
FROM alienation_timeline
ORDER BY event_date ASC;
```

### View 3: JUDGE_COURT_CONDUCT_CHRONOLOGY

```sql
SELECT id, date AS event_date, event_description, canon_violated,
       mcr_violation, severity, filing_relevance, source_quote
FROM judicial_bias_chronology
ORDER BY date ASC;
```

**Supplemental from case_timeline:**

```sql
SELECT id, event_date, event_type, description, source_file
FROM case_timeline
WHERE lane = 'E'
ORDER BY event_date ASC;
```

### View 4: SHADY_OAKS_CHRONOLOGY (Housing/Property)

```sql
SELECT id, event_date, event_type, description, source_file, source_quote
FROM case_timeline
WHERE lane = 'B'
ORDER BY event_date ASC;
```

**Enrichment from evidence_quotes:**

```sql
SELECT id, quote_text, source_file, category
FROM evidence_quotes
WHERE category = 'housing'
  AND (quote_text LIKE '%Shady Oaks%' OR quote_text LIKE '%Garland%'
       OR quote_text LIKE '%water%' OR quote_text LIKE '%sewage%'
       OR quote_text LIKE '%evict%' OR quote_text LIKE '%lockout%')
ORDER BY id;
```

### View 5: PPO_CONTEMPT_JAIL_CHRONOLOGY

```sql
SELECT id, event_date, event_type, description, lane, source_file
FROM case_timeline
WHERE lane = 'D'
  OR description LIKE '%PPO%'
  OR description LIKE '%contempt%'
  OR description LIKE '%jail%'
  OR description LIKE '%incarcerat%'
  OR description LIKE '%arrest%'
ORDER BY event_date ASC;
```

### View 6: PARENTING_TIME_WITHHOLDING_CHRONOLOGY

Primary source: `alienation_timeline` (purpose-built for this view).

```sql
SELECT event_date, event_description, category, withholding_episode,
       days_in_episode, cumulative_days_withheld, mcl_section,
       evidence_source, quote_text
FROM alienation_timeline
WHERE withholding_episode = 1
ORDER BY event_date ASC;
```

**Episode summary:**

```sql
SELECT withholding_episode, COUNT(*) as events,
       MIN(event_date) as start_date, MAX(event_date) as end_date,
       MAX(cumulative_days_withheld) as total_days
FROM alienation_timeline
WHERE withholding_episode = 1
GROUP BY withholding_episode;
```

### View 7: ORDER_AND_PROCEEDING_CHRONOLOGY

```sql
SELECT id, event_date, event_type, description, case_number, source_file
FROM case_timeline
WHERE event_type IN ('order', 'hearing', 'filing')
ORDER BY event_date ASC;
```

**Docket-enriched version:**

```sql
SELECT de.event_date, de.event_type, de.description, de.filed_by,
       de.case_number, de.source_file
FROM docket_events de
ORDER BY de.event_date ASC;
```

### View 8: SERVICE_AND_NONSERVICE_CHRONOLOGY

```sql
SELECT id, event_date, event_type, description, source_file, source_quote
FROM case_timeline
WHERE description LIKE '%serv%'
  OR description LIKE '%notice%'
  OR description LIKE '%ex parte%'
  OR event_type = 'violation'
ORDER BY event_date ASC;
```

**Cross-reference judicial violations for nonservice events:**

```sql
SELECT id, violation_type, description, date_occurred, mcr_rule, source_quote
FROM judicial_violations
WHERE violation_type = 'ex_parte'
  AND (description LIKE '%serv%' OR description LIKE '%notice%')
ORDER BY date_occurred ASC;
```

### View 9: HARM_AND_ESCALATION_CHRONOLOGY

```sql
SELECT id, event_date, event_type, description, lane, source_file
FROM case_timeline
WHERE event_type = 'incident'
  OR description LIKE '%harm%'
  OR description LIKE '%escala%'
  OR description LIKE '%threat%'
  OR description LIKE '%arrest%'
  OR description LIKE '%incarcerat%'
ORDER BY event_date ASC;
```

### View 10: RECENT_EMERGENCY_CHRONOLOGY

```sql
SELECT id, event_date, event_type, description, lane, source_file, source_quote
FROM case_timeline
WHERE event_date >= date('now', '-90 days')
ORDER BY event_date DESC;
```

**Fallback for stale data (if no recent events):**

```sql
SELECT id, event_date, event_type, description, lane
FROM case_timeline
ORDER BY event_date DESC
LIMIT 50;
```

---

## 3. Date Extraction Methods

### 3.1 Source Date Extraction Hierarchy

When ingesting new evidence, extract dates in this priority order:

| Priority | Source | Method | Reliability |
|----------|--------|--------|------------|
| 1 | Court file stamp | Regex: `\b(Filed|Entered|Signed)\s+\d{1,2}/\d{1,2}/\d{4}\b` | Highest — official |
| 2 | Document metadata | PDF CreationDate / ModDate fields via PyMuPDF | High — automated |
| 3 | Email headers | `Date:` header from .eml/.msg files | High — machine-generated |
| 4 | Text body dates | Regex: `\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b` or named months | Medium — requires context |
| 5 | EXIF data | Image metadata (screenshots, photos) | Medium — can be stripped |
| 6 | Filename dates | Pattern: `2024-01-15_motion.pdf` | Low — user-assigned |
| 7 | Contextual inference | "Last Tuesday" / "two weeks ago" relative to source date | Lowest — ambiguous |

### 3.2 Date Normalization

All dates in the DB use ISO 8601 format: `YYYY-MM-DD`. When a date is ambiguous:

- Prefer the earliest plausible date (conservative for deadlines)
- Store the original format in `source_quote` for audit
- Flag uncertain dates with `[DATE_UNCERTAIN]` in description

### 3.3 Date Range Events

Some events span ranges (e.g., "parenting time withheld Aug 8 - Mar 21"). Store as:

- `event_date` = start date
- Description includes end date
- Use `alienation_timeline.days_in_episode` for computed durations

---

## 4. Pattern Detection Algorithms

### 4.1 Escalation Detection

Identify escalation by tracking severity increases over time:

```sql
SELECT event_date, event_type, description,
       ROW_NUMBER() OVER (ORDER BY event_date) as seq,
       lane
FROM case_timeline
WHERE event_type = 'incident' OR event_type = 'violation'
ORDER BY event_date ASC;
```

**Escalation indicators:**

- Accusations increase in severity (see Ω5-adversary-brain §2.2)
- Time between incidents decreases (clustering)
- New lanes activated (lateral escalation)
- Legal remedies exhausted → extralegal tactics

### 4.2 Cyclic Behavior Detection

Detect repeating patterns (accusation → PPO → contempt → reset):

```sql
SELECT event_date, event_type, description, lane,
       LAG(event_date) OVER (ORDER BY event_date) as prev_date,
       julianday(event_date) - julianday(LAG(event_date) OVER (ORDER BY event_date)) as days_gap
FROM case_timeline
WHERE lane IN ('A', 'D')
  AND (description LIKE '%PPO%' OR description LIKE '%contempt%'
       OR description LIKE '%allegation%' OR description LIKE '%arrest%')
ORDER BY event_date ASC;
```

### 4.3 Response Delay Analysis

Measure court response times to detect bias:

```sql
SELECT a.event_date AS filing_date, a.description AS filing,
       b.event_date AS response_date, b.description AS response,
       julianday(b.event_date) - julianday(a.event_date) as response_days
FROM docket_events a
JOIN docket_events b ON b.event_date > a.event_date
  AND b.case_number = a.case_number
WHERE a.filed_by LIKE '%Pigors%'
  AND b.event_type IN ('order', 'hearing')
ORDER BY a.event_date ASC;
```

Compare Andrew's filing→response time vs. Emily's filing→response time for bias evidence.

### 4.4 Clustering Analysis

Identify event clusters (multiple events in short windows):

```sql
SELECT event_date, COUNT(*) as events_on_date,
       GROUP_CONCAT(event_type, ' | ') as types,
       GROUP_CONCAT(lane, ' | ') as lanes
FROM case_timeline
GROUP BY event_date
HAVING COUNT(*) >= 3
ORDER BY events_on_date DESC;
```

### 4.5 Gap Detection

Identify suspiciously quiet periods:

```sql
WITH dated AS (
  SELECT event_date,
         LEAD(event_date) OVER (ORDER BY event_date) as next_date,
         julianday(LEAD(event_date) OVER (ORDER BY event_date)) - julianday(event_date) as gap_days
  FROM case_timeline
)
SELECT event_date, next_date, gap_days
FROM dated
WHERE gap_days > 30
ORDER BY gap_days DESC;
```

---

## 5. Cross-Lane Event Linking

### 5.1 Same-Date Cross-Lane Events

Events on the same date across different lanes indicate coordinated action:

```sql
SELECT a.event_date, a.lane AS lane_1, a.description AS desc_1,
       b.lane AS lane_2, b.description AS desc_2
FROM case_timeline a
JOIN case_timeline b ON a.event_date = b.event_date AND a.lane < b.lane
ORDER BY a.event_date ASC;
```

### 5.2 Cross-Lane Escalation Chains

When an event in one lane triggers events in another:

```sql
SELECT a.event_date AS trigger_date, a.lane AS trigger_lane, a.description AS trigger_event,
       b.event_date AS response_date, b.lane AS response_lane, b.description AS response_event,
       julianday(b.event_date) - julianday(a.event_date) as days_lag
FROM case_timeline a
JOIN case_timeline b ON b.event_date BETWEEN a.event_date AND date(a.event_date, '+7 days')
  AND a.lane != b.lane
  AND a.id != b.id
ORDER BY a.event_date ASC, days_lag ASC;
```

### 5.3 Lane Convergence Points

Events where 3+ lanes intersect on the same date:

```sql
SELECT event_date, COUNT(DISTINCT lane) as lane_count,
       GROUP_CONCAT(DISTINCT lane) as lanes,
       COUNT(*) as total_events
FROM case_timeline
WHERE lane IS NOT NULL
GROUP BY event_date
HAVING COUNT(DISTINCT lane) >= 3
ORDER BY lane_count DESC;
```

---

## 6. Timeline Gap Detection Protocol

### 6.1 Automated Gap Scan

Run periodically to identify missing timeline coverage:

```sql
-- Gaps by lane
SELECT lane,
       MIN(event_date) as earliest,
       MAX(event_date) as latest,
       COUNT(*) as event_count,
       CAST(julianday(MAX(event_date)) - julianday(MIN(event_date)) AS INTEGER) as span_days,
       ROUND(COUNT(*) * 1.0 / (julianday(MAX(event_date)) - julianday(MIN(event_date))), 2) as events_per_day
FROM case_timeline
WHERE lane IS NOT NULL
GROUP BY lane
ORDER BY events_per_day ASC;
```

Low `events_per_day` indicates sparse coverage — prioritize evidence harvesting for that lane.

### 6.2 Monthly Coverage Check

```sql
SELECT strftime('%Y-%m', event_date) as month, lane, COUNT(*) as events
FROM case_timeline
WHERE event_date IS NOT NULL AND lane IS NOT NULL
GROUP BY month, lane
ORDER BY month ASC, lane ASC;
```

### 6.3 Key Event Coverage

Verify that critical milestones have timeline entries:

```sql
SELECT id, event_date, event_type, description, is_key_event
FROM case_timeline
WHERE is_key_event = 1
ORDER BY event_date ASC;
```

---

## 7. Chronology Row Schema (for generated chronology documents)

When producing chronology outputs for filings or affidavits, each row carries:

| Field | Source | Required |
|-------|--------|----------|
| ChronoID | `case_timeline.id` | Yes |
| DateOrRange | `event_date` (ISO 8601) | Yes |
| Actor | Extract from `description` or `docket_events.filed_by` | Yes |
| Conduct | Verb phrase from `description` | Yes |
| Target | Extract from `description` | If applicable |
| SourcePath | `source_file` | Yes |
| SourceType | `event_type` | Yes |
| Confidence | Derived from source reliability tier (§3.1) | Yes |
| Lane | `lane` | Yes |
| RelatedOrder | Cross-ref `docket_events` for associated orders | If applicable |
| Harm | Extract harm language from `description` or `source_quote` | If applicable |
| Accusation | Cross-ref `false_allegations` by date | If applicable |
| Exhibit | Bound exhibit reference | If available |
| AffidavitUse | Paragraph class (see Ω5 affidavit doctrine) | For affidavit output |
| Gap | `[GAP — ACQUISITION NEEDED]` if missing evidence | If gap detected |

---

## 8. Key DB Queries — Ready to Run

### Query 1: Full Master Timeline Export

```sql
SELECT ct.id, ct.event_date, ct.event_type, ct.description,
       ct.lane, ct.case_number, ct.is_key_event, ct.source_file
FROM case_timeline ct
WHERE ct.event_date IS NOT NULL
ORDER BY ct.event_date ASC, ct.id ASC;
```

### Query 2: Lane-Specific Timeline with Event Counts

```sql
SELECT lane, event_type, COUNT(*) as cnt
FROM case_timeline
WHERE lane IS NOT NULL
GROUP BY lane, event_type
ORDER BY lane, cnt DESC;
```

### Query 3: Docket Timeline for Specific Case

```sql
SELECT event_date, event_type, description, filed_by
FROM docket_events
WHERE case_number = '2024-001507-DC'
ORDER BY event_date ASC;
```

### Query 4: Alienation Episode Summary

```sql
SELECT MIN(event_date) as episode_start, MAX(event_date) as episode_end,
       COUNT(*) as events, MAX(cumulative_days_withheld) as total_days,
       GROUP_CONCAT(DISTINCT category) as categories
FROM alienation_timeline
WHERE withholding_episode = 1;
```

### Query 5: Bias Chronology with Canon Attribution

```sql
SELECT date, event_description, canon_violated, mcr_violation,
       severity, filing_relevance
FROM judicial_bias_chronology
WHERE severity >= 7
ORDER BY date ASC;
```

---

## 9. Cross-Wiring Points

| Target Brain | Connection | Data Flow |
|-------------|------------|-----------|
| **Ω5-adversary-brain** | Adversary actions are dated events | `false_allegations.date_alleged` anchors into WATSON_CLUSTER chronology; retaliation cycle uses docket date correlation |
| **Ω7-judicial-brain** | Judicial violations are dated events | `judicial_bias_chronology` IS the JUDGE_COURT_CONDUCT view; `judicial_violations.date_occurred` anchors into master timeline |
| **Ω8-financial-brain** | Damages require date-bounded calculations | `alienation_timeline.cumulative_days_withheld` → per-day damages computation; employment loss dates → lost income window |
| **Ω1-evidence-brain** | Evidence discovery dates feed timeline | New evidence intake triggers timeline entry creation |
| **Ω4-filing-brain** | Deadline dates drive filing urgency | Filing deadlines cross-reference with recent timeline events for urgency scoring |
| **Ω3-authority-brain** | Statute of limitations anchored to event dates | Each claim's viability window starts at the timeline event establishing the cause of action |

---

## 10. Operational Directives

1. **Never hardcode event counts.** Always use `SELECT COUNT(*) FROM case_timeline` for live numbers.
2. **ISO 8601 dates only.** Every date in every output must be YYYY-MM-DD format.
3. **Source-pin every event.** A timeline entry without `source_file` is an acquisition task, not a fact.
4. **Distinguish key events.** Use `is_key_event = 1` to surface critical milestones for affidavit and brief construction.
5. **Run gap detection monthly.** Sparse lanes need targeted evidence harvesting.
6. **Cross-lane linking is mandatory** for convergence analysis (Lane C). Same-date events across different lanes indicate coordinated adversary action or systemic judicial bias.
7. **Alienation timeline is purpose-built.** Use it for parenting time calculations — do not reconstruct from `case_timeline` manually.
8. **Bias chronology feeds JTC complaints.** The `judicial_bias_chronology` table is the primary source for Ω7 judicial accountability analysis.
