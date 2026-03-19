# EGCP v2 — Evidence Gap Closure Protocol

## Philosophy

No "UNKNOWN" fields. Every gap in knowledge gets a formal **Gap Ticket** with:
1. What's missing
2. Why it's needed
3. How to acquire it
4. How urgent it is

## Gap Ticket Format

```json
{
  "ticket_id": "EGT-{timestamp}-{sequence}",
  "target_field": "MCL 554.139 full text",
  "why_needed": "Shady Oaks landlord-tenant claims require warranty of habitability statute text",
  "acquisition_method": "legislature.mi.gov scrape OR Westlaw",
  "search_query_terms": ["MCL 554.139", "warranty habitability", "landlord obligations"],
  "deadline_risk": "medium|high|critical",
  "state": "MISSING|INFERRED|SUPPORTED|VERIFIED",
  "created_local": "2026-02-21T12:00:00",
  "resolved_local": null,
  "resolution_sha256": null
}
```

## Gap States

| State | Meaning | Action |
|-------|---------|--------|
| **MISSING** | No data exists | Must acquire before filing |
| **INFERRED** | Derived from related data | Acceptable for DRAFT mode; must verify for FILE_READY |
| **SUPPORTED** | Multiple sources agree | Acceptable for most purposes |
| **VERIFIED** | Confirmed against authoritative source | Ready for court |

## Gap Detection (Phase 6)

Phase 6 compares scans corpus against existing knowledge base:

1. **File-level gaps** — SHA-256s in scans not in any existing index
2. **Citation gaps** — MCL/MCR/MRE cites found in scans not in SYNTHESIS_DATA
3. **Person gaps** — New person mentions not in MASTER_PERSONS.csv
4. **Timeline gaps** — New dates/events not in MASTER_TIMELINE.csv
5. **Contradiction gaps** — New contradictions not in existing stores
6. **Authority gaps** — MCL/MCR rules cited but no text shard exists

## Gap Priority

| Priority | Criteria | Example |
|----------|----------|---------|
| **CRITICAL** | Blocks a filing from being court-ready | Missing MCR text for cited rule |
| **HIGH** | Weakens evidence chain significantly | Missing sworn testimony reference |
| **MEDIUM** | Would strengthen but not essential | Additional case law authority |
| **LOW** | Nice-to-have completeness | Formatting improvements |

## Acquisition Methods

- `legislature.mi.gov` — MCL statute text
- `courts.michigan.gov` — MCR rule text, SCAO forms
- `scholar.google.com` — Case law opinions
- `westlaw/lexis` — Comprehensive legal research
- `FOIA request` — Government records
- `discovery request` — Opposing party documents
- `subpoena` — Third-party records

## Resolution Protocol

When a gap is filled:
1. Set `state` → `VERIFIED`
2. Set `resolved_local` → timestamp
3. Set `resolution_sha256` → SHA-256 of acquired content
4. Append acquired content to appropriate atom store
5. Generate new atoms from the acquired content
6. Re-score affected legal actions
