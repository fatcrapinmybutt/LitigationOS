# Neo4j Data Model — LitigationOS OMEGA-INFINITY

> **Version:** 4.0  
> **Last Updated:** 2025-07-14  
> **Case:** Pigors v. Watson (14th Circuit Court, Family Division)  
> **Database Source:** `litigation_context.db` (~12 GB, 790+ tables)

---

## Overview

This data model defines the graph schema for visualizing the LitigationOS litigation intelligence system in Neo4j. It maps 13 node types and 15 edge types across 6 case lanes, providing a complete knowledge graph of evidence, filings, rules, violations, and party relationships.

### Design Principles

1. **Lane Isolation** — Every node carries a `lane` property; cross-lane analysis uses Lane C (Convergence)
2. **Source Traceability** — Every node links back to a specific table/row in `litigation_context.db`
3. **Weight Semantics** — Edge weights represent relevance, severity, or readiness scores (0.0–1.0 normalized)
4. **Append-Only** — Graph updates add nodes/edges; existing data is never deleted
5. **Deterministic IDs** — Node IDs are derived from source table primary keys for idempotent imports

---

## Node Types (13)

### 1. Case

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `case_number` | String | Static mapping | Court case number (e.g., `2024-001507-DC`) |
| `case_type` | String | Static mapping | Case type code (DC, PP, CZ) |
| `court` | String | Static mapping | Court name |
| `lane` | String | Static mapping | Lane identifier (A–F) |
| `caption` | String | Static mapping | Full case caption |
| `filing_date` | Date | Docket records | Date case was filed |
| `status` | String | Docket records | Active, Closed, Pending |

- **Color:** Based on lane assignment (see color palette)
- **Source:** Static configuration — 4 active cases across 6 lanes
- **Unique Constraint:** `case_number`

### 2. Lane

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `lane_id` | String | Static mapping | Lane identifier (A, B, C, D, E, F) |
| `name` | String | Static mapping | Human-readable lane name |
| `meek_signal` | String | config.py MEEK_SIGNALS | MEEK regex pattern identifier |
| `case_number` | String | Static mapping | Primary case number for this lane |
| `description` | String | Static mapping | Lane purpose and scope |

- **Color:** Lane-specific color (Royal Blue, Forest Green, Gold, Crimson, Purple, Teal)
- **Source:** Static configuration — exactly 6 lanes
- **Unique Constraint:** `lane_id`

**Lane Definitions:**

| Lane | Name | MEEK Signal | Case Number(s) | Color |
|------|------|-------------|-----------------|-------|
| A | Custody | MEEK2 | 2024-001507-DC, 2023-5907-PP | Royal Blue (#1E3A5F) |
| B | Housing / Shady Oaks | MEEK1 | 2025-002760-CZ | Forest Green (#2E7D32) |
| C | Convergence | — | Multi-lane | Gold (#F9A825) |
| D | PPO / Protection Orders | MEEK3 | 2024-001507-DC, 2023-5907-PP | Crimson (#C62828) |
| E | Judicial Misconduct / JTC | MEEK4 | 2024-001507-DC | Purple (#6A1B9A) |
| F | Appellate (COA/MSC) | MEEK5 | Assigned on filing | Teal (#00838F) |

### 3. Party

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `name` | String | Static / verified identity | Full legal name |
| `role` | String | Static mapping | Plaintiff, Defendant, Child, FOC |
| `address` | String | Static / verified identity | Mailing address |
| `phone` | String | Static / verified identity | Contact phone |
| `email` | String | Static / verified identity | Contact email |

- **Color:** White (#FFFFFF)
- **Source:** Verified Party Identity table (NEVER fabricated)
- **Unique Constraint:** `name` + `role`

**Canonical Parties (source of truth):**

| Name | Role |
|------|------|
| Andrew James Pigors | Plaintiff |
| Emily A. Watson | Defendant |
| L.D.W. | Child (initials only per MCR 8.119(H)) |
| Pamela Rusco | FOC |

### 4. Judge

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `name` | String | Verified identity | Full name with honorific |
| `court` | String | Static mapping | Court assignment |
| `bar_number` | String | Static / DB lookup | State bar number |
| `division` | String | Static mapping | Court division |

- **Color:** Purple (#6A1B9A)
- **Source:** Verified identity — Hon. Jenny L. McNeill, 14th Circuit Court, Family Division
- **Unique Constraint:** `name`

### 5. Attorney

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `name` | String | Verified identity | Full legal name |
| `bar_number` | String | Verified identity | State bar number (e.g., P55406) |
| `firm` | String | Verified identity | Law firm name |
| `status` | String | Case records | Active, Withdrawn |
| `represents` | String | Case records | Party represented |

- **Color:** Dark Gray (#424242)
- **Source:** Verified identity table
- **Unique Constraint:** `bar_number`

**Known Attorneys:**

| Name | Bar Number | Firm | Status |
|------|-----------|------|--------|
| Jennifer Barnes | P55406 | Barnes Law Firm PLLC | WITHDRAWN |

> ⚠️ Ronald Berry is a NON-ATTORNEY. No bar number. Never was Emily's attorney.

### 6. Claim

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `claim_id` | String | claims.claim_id | Unique claim identifier |
| `claim_type` | String | claims.claim_type | Type of legal claim |
| `description` | String | claims.description | Claim description |
| `status` | String | claims.status | Pending, Active, Resolved |
| `vehicle_name` | String | claims.vehicle_name | Filing vehicle associated |
| `lane` | String | Derived from vehicle_name | Case lane |
| `strength_score` | Float | claims (if available) | Evidence strength (0.0–1.0) |

- **Color:** Based on lane assignment
- **Source Table:** `claims` in `litigation_context.db`
- **Unique Constraint:** `claim_id`

### 7. Evidence

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `id` | String | evidence_quotes.rowid or quote_id | Unique evidence identifier |
| `source_file` | String | evidence_quotes.source_file | Original file path |
| `category` | String | evidence_quotes.category | Evidence category |
| `lane` | String | evidence_quotes.lane | Case lane assignment |
| `quote_text` | String | evidence_quotes.quote_text | Extracted quote (truncated for graph) |
| `relevance_score` | Float | evidence_quotes.relevance_score | Relevance score (0.0–1.0) |
| `date_extracted` | String | evidence_quotes (if available) | When evidence was extracted |
| `authentication_status` | String | Derived | Authenticated, Pending, Unverified |

- **Color:** Orange (#E65100)
- **Source Table:** `evidence_quotes` in `litigation_context.db`
- **Unique Constraint:** `id`
- **Note:** Large table — use batch imports with periodic commit

### 8. Filing

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `vehicle_name` | String | filing_readiness.vehicle_name | Filing vehicle identifier |
| `readiness_score` | Float | filing_readiness.readiness_score | Readiness percentage (0–100) |
| `status` | String | filing_readiness.status | Draft, Ready, Filed, Pending |
| `lane` | String | filing_readiness (derived) | Case lane |
| `filing_type` | String | filing_readiness (if available) | Motion, Brief, Petition, etc. |
| `target_court` | String | filing_readiness (if available) | Target court for filing |
| `evidence_count` | Integer | Derived from exhibit_binders | Number of supporting exhibits |

- **Color:** Light Green (#66BB6A) with gradient based on readiness_score
- **Source Table:** `filing_readiness` in `litigation_context.db`
- **Unique Constraint:** `vehicle_name`

### 9. Form

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `form_number` | String | court_forms_complete.form_number | SCAO form number (e.g., MC 01) |
| `form_title` | String | court_forms_complete.form_title | Official form title |
| `category` | String | court_forms_complete.category | Form category |
| `division` | String | court_forms_complete.division | Court division |
| `url` | String | court_forms_complete.url | Download URL |
| `instructions` | String | court_forms_complete (if available) | Filing instructions summary |

- **Color:** Cyan (#00BCD4)
- **Source Table:** `court_forms_complete` in `court_forms.db`
- **Unique Constraint:** `form_number`

### 10. Rule

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `citation` | String | authority_master_index.citation | Full citation (e.g., MCR 2.003) |
| `rule_type` | String | authority_master_index.rule_type | MCR, MCL, Constitutional, etc. |
| `source` | String | authority_master_index.source | Source publication |
| `description` | String | authority_master_index.description | Rule description/summary |
| `relevance_count` | Integer | Derived | Number of filings citing this rule |

- **Color:** Amber/Gold (#FFB300)
- **Source Table:** `authority_master_index` in `litigation_context.db`
- **Unique Constraint:** `citation`

### 11. Violation

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `violation_id` | String | judicial_violations.rowid | Unique violation identifier |
| `violation_type` | String | judicial_violations.violation_type | Type of violation |
| `mcr_rule` | String | judicial_violations.mcr_rule | MCR rule violated |
| `severity` | String | judicial_violations.severity | Low, Medium, High, Critical |
| `date_occurred` | String | judicial_violations.date_occurred | Date of violation |
| `description` | String | judicial_violations.description | Violation description |
| `evidence_refs` | String | judicial_violations (if available) | Supporting evidence references |

- **Color:** Crimson (#C62828)
- **Source Table:** `judicial_violations` in `litigation_context.db`
- **Unique Constraint:** `violation_id`

### 12. Witness

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `name` | String | Derived from evidence/docket | Witness name |
| `role` | String | Derived | Fact witness, Expert, Character |
| `lane` | String | Derived | Primary case lane |
| `testimony_count` | Integer | Derived | Number of testimony references |

- **Color:** Teal (#008080)
- **Source:** Extracted from evidence_quotes and docket_events
- **Unique Constraint:** `name` + `lane`

### 13. Event

| Property | Type | Source | Description |
|----------|------|--------|-------------|
| `event_id` | String | case_timeline.rowid or docket_events.rowid | Unique event identifier |
| `event_date` | Date | case_timeline.event_date / docket_events.date | When event occurred |
| `event_type` | String | case_timeline.event_type / docket_events.type | Hearing, Filing, Order, etc. |
| `description` | String | case_timeline.description / docket_events.description | Event description |
| `lane` | String | Derived from case number | Case lane |
| `source_table` | String | Metadata | Which table this came from |

- **Color:** Timeline Blue (#1565C0)
- **Source Tables:** `case_timeline` and `docket_events` in `litigation_context.db`
- **Unique Constraint:** `event_id`

---

## Edge Types (15)

### 1. BELONGS_TO_LANE

| Property | Type | Description |
|----------|------|-------------|
| `weight` | Float | Always 1.0 |

- **From:** Case → **To:** Lane
- **Source:** Static lane mapping
- **Cardinality:** Many-to-One (multiple cases can share a lane)

### 2. PARTY_IN_CASE

| Property | Type | Description |
|----------|------|-------------|
| `role` | String | Party's role in this case |
| `weight` | Float | Always 1.0 |

- **From:** Party → **To:** Case
- **Source:** Static mapping from verified party identity
- **Cardinality:** Many-to-Many

### 3. JUDGE_PRESIDES

| Property | Type | Description |
|----------|------|-------------|
| `division` | String | Court division |
| `weight` | Float | Always 1.0 |

- **From:** Judge → **To:** Case
- **Source:** Static — Hon. Jenny L. McNeill presides over custody/PPO
- **Cardinality:** One-to-Many

### 4. ATTORNEY_REPRESENTS

| Property | Type | Description |
|----------|------|-------------|
| `status` | String | Active, Withdrawn |
| `start_date` | String | Representation start |
| `end_date` | String | Representation end (if withdrawn) |
| `weight` | Float | Always 1.0 |

- **From:** Attorney → **To:** Party
- **Source:** Verified identity table
- **Cardinality:** Many-to-Many

### 5. SUPPORTS_CLAIM

| Property | Type | Description |
|----------|------|-------------|
| `relevance_score` | Float | How strongly evidence supports claim (0.0–1.0) |
| `category_match` | String | Evidence category matching claim type |
| `weight` | Float | Same as relevance_score |

- **From:** Evidence → **To:** Claim
- **Source:** evidence_quotes.category mapped to claims via vehicle_name/claim_type
- **Cardinality:** Many-to-Many

### 6. FILED_IN_CASE

| Property | Type | Description |
|----------|------|-------------|
| `readiness_score` | Float | Filing readiness (0–100, normalized to 0.0–1.0) |
| `filing_date` | String | When filed (if filed) |
| `weight` | Float | readiness_score / 100.0 |

- **From:** Filing → **To:** Case
- **Source:** filing_readiness.vehicle_name → case mapping
- **Cardinality:** Many-to-One

### 7. REQUIRES_FORM

| Property | Type | Description |
|----------|------|-------------|
| `required` | Boolean | Whether form is mandatory |
| `weight` | Float | Always 1.0 |

- **From:** Filing → **To:** Form
- **Source:** Form-to-filing mapping (court_forms → filing_readiness)
- **Cardinality:** Many-to-Many

### 8. CITES_AUTHORITY

| Property | Type | Description |
|----------|------|-------------|
| `chain_count` | Integer | Number of authority chains citing this rule |
| `context` | String | Citation context snippet |
| `weight` | Float | Normalized chain_count |

- **From:** Filing → **To:** Rule
- **Source:** `authority_chains_v2` table
- **Cardinality:** Many-to-Many

### 9. VIOLATES_RULE

| Property | Type | Description |
|----------|------|-------------|
| `severity` | String | Low, Medium, High, Critical |
| `severity_weight` | Float | Low=0.25, Medium=0.5, High=0.75, Critical=1.0 |
| `date_occurred` | String | When violation occurred |
| `weight` | Float | Same as severity_weight |

- **From:** Violation → **To:** Rule
- **Source:** judicial_violations.mcr_rule
- **Cardinality:** Many-to-Many (a violation can violate multiple rules)

### 10. COMMITTED_BY

| Property | Type | Description |
|----------|------|-------------|
| `date` | String | Date of violation |
| `weight` | Float | Always 1.0 |

- **From:** Violation → **To:** Judge
- **Source:** judicial_violations — all linked to Hon. Jenny L. McNeill
- **Cardinality:** Many-to-One

### 11. EVIDENCE_IN_LANE

| Property | Type | Description |
|----------|------|-------------|
| `weight` | Float | Always 1.0 |

- **From:** Evidence → **To:** Lane
- **Source:** evidence_quotes.lane field
- **Cardinality:** Many-to-One

### 12. OCCURRED_ON

| Property | Type | Description |
|----------|------|-------------|
| `weight` | Float | Always 1.0 |

- **From:** Event → **To:** Lane
- **Source:** case_timeline.lane / docket_events mapped via case number
- **Cardinality:** Many-to-One

### 13. TESTIFIED_ABOUT

| Property | Type | Description |
|----------|------|-------------|
| `context` | String | Testimony context |
| `weight` | Float | Always 1.0 |

- **From:** Witness → **To:** Evidence
- **Source:** Witness-evidence linkage from transcripts/depositions
- **Cardinality:** Many-to-Many

### 14. CO_CITED_WITH

| Property | Type | Description |
|----------|------|-------------|
| `co_citation_count` | Integer | Number of filings where both rules are cited together |
| `weight` | Float | Normalized co_citation_count |

- **From:** Rule → **To:** Rule
- **Source:** `authority_chains_v2` WHERE relationship = 'co-cited'
- **Cardinality:** Many-to-Many (undirected — symmetric relationship)
- **Note:** Self-loops excluded

### 15. FILING_USES_EVIDENCE

| Property | Type | Description |
|----------|------|-------------|
| `exhibit_number` | String | Exhibit designation (e.g., Exhibit A) |
| `bates_range` | String | Bates stamp range |
| `weight` | Float | Always 1.0 |

- **From:** Filing → **To:** Evidence
- **Source:** exhibit_binders → evidence_quotes linkage
- **Cardinality:** Many-to-Many

---

## Indexes

| Index Name | Node Label | Property | Purpose |
|------------|-----------|----------|---------|
| `idx_case_number` | Case | case_number | Fast case lookup |
| `idx_lane_id` | Lane | lane_id | Lane filtering |
| `idx_claim_id` | Claim | claim_id | Claim lookup |
| `idx_evidence_lane` | Evidence | lane | Lane-based evidence filtering |
| `idx_evidence_category` | Evidence | category | Category-based queries |
| `idx_filing_vehicle` | Filing | vehicle_name | Filing lookup |
| `idx_filing_readiness` | Filing | readiness_score | Readiness-sorted queries |
| `idx_form_number` | Form | form_number | Form lookup |
| `idx_rule_citation` | Rule | citation | Authority lookup |
| `idx_violation_type` | Violation | violation_type | Violation filtering |
| `idx_violation_severity` | Violation | severity | Severity-sorted queries |
| `idx_event_date` | Event | event_date | Timeline queries |
| `idx_event_type` | Event | event_type | Event type filtering |
| `idx_witness_name` | Witness | name | Witness lookup |

---

## Color Palette

| Element | Hex Code | Usage |
|---------|----------|-------|
| Royal Blue | `#1E3A5F` | Lane A — Custody |
| Forest Green | `#2E7D32` | Lane B — Housing |
| Gold | `#F9A825` | Lane C — Convergence |
| Crimson | `#C62828` | Lane D — PPO |
| Purple | `#6A1B9A` | Lane E — Misconduct |
| Teal | `#00838F` | Lane F — Appellate |
| White | `#FFFFFF` | Parties |
| Dark Gray | `#424242` | Attorneys |
| Orange | `#E65100` | Evidence |
| Light Green | `#66BB6A` | Filings |
| Cyan | `#00BCD4` | Forms |
| Amber | `#FFB300` | Rules / Authorities |
| Timeline Blue | `#1565C0` | Events |
| Violation Red | `#D32F2F` | Violations |
| Witness Teal | `#008080` | Witnesses |
| Judge Purple | `#7B1FA2` | Judge |

---

## Graph Statistics (Query at Runtime)

Run these Cypher queries to get current graph statistics:

```cypher
// Node counts by label
CALL db.labels() YIELD label
CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) AS count', {}) YIELD value
RETURN label, value.count AS count ORDER BY count DESC;

// Edge counts by type
CALL db.relationshipTypes() YIELD relationshipType
CALL apoc.cypher.run('MATCH ()-[r:`' + relationshipType + '`]->() RETURN count(r) AS count', {}) YIELD value
RETURN relationshipType, value.count AS count ORDER BY count DESC;

// Lane distribution
MATCH (e:Evidence)
RETURN e.lane AS lane, count(e) AS evidence_count
ORDER BY lane;

// High-connectivity nodes (hubs)
MATCH (n)
WITH n, size([(n)--() | 1]) AS degree
WHERE degree > 10
RETURN labels(n)[0] AS label, n.name AS name, degree
ORDER BY degree DESC LIMIT 20;
```

---

## CSV Export File Manifest

The `scripts/omega_neo4j_export.py` script generates these CSV files:

| File | Node/Edge | Source Table | Expected Rows |
|------|-----------|-------------|---------------|
| `cases.csv` | Case nodes | Static | ~4–6 |
| `lanes.csv` | Lane nodes | Static | 6 |
| `parties.csv` | Party nodes | Static/verified | ~5 |
| `judges.csv` | Judge nodes | Static/verified | ~1–2 |
| `attorneys.csv` | Attorney nodes | Static/verified | ~1–2 |
| `claims.csv` | Claim nodes | claims table | Query DB |
| `evidence.csv` | Evidence nodes | evidence_quotes | Query DB |
| `filings.csv` | Filing nodes | filing_readiness | Query DB |
| `forms.csv` | Form nodes | court_forms_complete | ~39 |
| `rules.csv` | Rule nodes | authority_master_index | Query DB |
| `violations.csv` | Violation nodes | judicial_violations | Query DB |
| `witnesses.csv` | Witness nodes | Derived | Query DB |
| `events.csv` | Event nodes | case_timeline + docket_events | Query DB |
| `rel_belongs_to_lane.csv` | BELONGS_TO_LANE | Static | ~4–6 |
| `rel_party_in_case.csv` | PARTY_IN_CASE | Static | ~8–12 |
| `rel_judge_presides.csv` | JUDGE_PRESIDES | Static | ~2–3 |
| `rel_attorney_represents.csv` | ATTORNEY_REPRESENTS | Static | ~1–2 |
| `rel_supports_claim.csv` | SUPPORTS_CLAIM | evidence → claims | Query DB |
| `rel_filed_in_case.csv` | FILED_IN_CASE | filing → case | Query DB |
| `rel_requires_form.csv` | REQUIRES_FORM | filing → form | Query DB |
| `rel_cites_authority.csv` | CITES_AUTHORITY | authority_chains_v2 | Query DB |
| `rel_violates_rule.csv` | VIOLATES_RULE | judicial_violations | Query DB |
| `rel_committed_by.csv` | COMMITTED_BY | judicial_violations | Query DB |
| `rel_evidence_in_lane.csv` | EVIDENCE_IN_LANE | evidence_quotes | Query DB |
| `rel_occurred_on.csv` | OCCURRED_ON | case_timeline | Query DB |
| `rel_testified_about.csv` | TESTIFIED_ABOUT | Derived | Query DB |
| `rel_co_cited_with.csv` | CO_CITED_WITH | authority_chains_v2 | Query DB |
| `rel_filing_uses_evidence.csv` | FILING_USES_EVIDENCE | exhibit_binders | Query DB |

> **Note:** Row counts are not hardcoded. Run the export script and query the DB for current counts.
