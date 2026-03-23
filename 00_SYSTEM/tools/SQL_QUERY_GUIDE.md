# Common Litigation Queries for litigation_context.db

## SCHEMA CONNECTION TEMPLATE
```python
import sqlite3
db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path, timeout=60)
cursor = conn.cursor()
cursor.execute("PRAGMA busy_timeout=60000")
cursor.execute("PRAGMA journal_mode=WAL")
```

## QUERY 1: Get All Critical Violations by Judge
```sql
SELECT judge_name, COUNT(*) as count, severity
FROM judicial_violations
WHERE severity = 'critical'
GROUP BY judge_name
ORDER BY count DESC
```

## QUERY 2: Get Evidence Quotes 
```sql
SELECT id, speaker, quote_text, legal_significance, date_ref
FROM evidence_quotes
WHERE legal_significance IS NOT NULL
LIMIT 50
```

## QUERY 3: Build Case Timeline with Violations
```sql
SELECT de.event_date_iso, de.title, de.event_type
FROM docket_events de
ORDER BY de.event_date_iso ASC
```

## QUERY 4: Find Witness Contradictions
```sql
SELECT target_witness, statement_a, statement_b, contradiction_type
FROM impeachment_index
ORDER BY target_witness
```

## QUERY 5: Get Supported Claims with Evidence
```sql
SELECT claim_id, classification, proposition, evidence_targets
FROM claims
WHERE status = 'supported'
```

## QUERY 6: Find Rebuttal Strategies
```sql
SELECT adversary, assertion_text, rebuttal_evidence, priority_score
FROM rebuttal_matrix
WHERE priority_score >= 7
ORDER BY priority_score DESC
```

## QUERY 7: Get High-Impact Contradictions
```sql
SELECT source_a_text, source_b_text, contradiction_type, legal_impact
FROM contradiction_map
WHERE severity IN ('critical', 'high')
```

## QUERY 8: Pattern of Violations by Actor
```sql
SELECT actor, violation_type, COUNT(*) as freq, severity
FROM actor_violations
WHERE actor IS NOT NULL
GROUP BY actor, violation_type
ORDER BY freq DESC
```

## KEY FIELDS FOR FILTERING
- evidence_category: HEARING_REF, JUDICIAL_ORDER, TRANSCRIPT
- severity: critical, high, medium, low
- status: supported, rebuttable, disputed
- event_type: filing, order, hearing, appeal
- contradiction_type: statement_contradiction, date_discrepancy

Database: C:\Users\andre\LitigationOS\litigation_context.db
