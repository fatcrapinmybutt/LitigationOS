# Ω2 Evidence Brain — OMEGA-INFINITY Reference
> Module 2 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose
The evidence brain governs the end-to-end evidence pipeline — from raw file discovery across six drives through extraction, deduplication, classification, authentication, indexing, gap analysis, and timeline construction. Every fact asserted in any filing must trace back to an evidence record in this pipeline.

---

## 1. Eight-Module Evidence Pipeline

### Module E1 — Scan (Discovery & Inventory)
Recursively scan all mounted drives for litigation-relevant files. Drives: C:\, D:\, F:\, G:\, H:\, I:\. Capture file path, size, hash, modified date, MIME type. Write inventory to `documents` table.

**Input:** Raw filesystem
**Output:** `documents` rows with `file_path`, `file_hash`, `file_size`, `mime_type`, `discovered_date`
**Query:** `SELECT file_path, mime_type, file_size FROM documents ORDER BY discovered_date DESC LIMIT 20`

Target file types (priority order):
1. PDF (court orders, filings, transcripts, FOIA responses)
2. DOCX/DOC (drafts, letters, affidavits)
3. Images (screenshots, photos of property, texts)
4. Email exports (EML, MSG, MBOX)
5. Structured data (JSON, CSV, JSONL, TSV)
6. Text (TXT, MD, LOG)
7. Archives (ZIP, RAR — explode and process contents)
8. Database exports (SQLite, SQL dumps)

### Module E2 — Extract (Content Extraction)
Extract text content from each document. OCR for scanned PDFs. Metadata extraction for all types. Write extracted content to `evidence_atoms` and `evidence_quotes`.

**Input:** `documents` rows
**Output:** `evidence_atoms` (atomic facts), `evidence_quotes` (quotable passages)
**Tools:** PyMuPDF for PDF, python-docx for DOCX, Tesseract for OCR
**Query:** `SELECT atom_id, content, source_file, page_number FROM evidence_atoms WHERE source_file = ?`

Extraction priorities:
- Dates and date ranges (temporal anchors)
- Named entities (persons, organizations, courts, agencies)
- Quoted statements (admissions, contradictions)
- Order/control language (court directives, conditions)
- Financial figures (support amounts, costs, damages)
- Legal citations (statutes, rules, case law)

### Module E3 — Dedup (Content-Based Deduplication)
**CRITICAL: Content-based dedup only. NEVER rely solely on file hashing.**

Protocol:
1. Compute SHA-256 hash as a first-pass filter
2. For hash matches, OPEN BOTH FILES and compare actual content
3. Compare headers, footers, page counts, watermarks, modification dates
4. If content is truly identical, move the duplicate to `I:\dedup\[original_hash]\`
5. Record the dedup action in `dedup_log` with both paths and the decision reason
6. NEVER hard-delete a file — always move to I:\ drive

**Input:** `documents` inventory with hashes
**Output:** Deduplicated `documents` table, dedup log entries
**Query:** `SELECT original_path, duplicate_path, decision_reason FROM dedup_log ORDER BY created_date DESC LIMIT 20`

Edge cases requiring manual review:
- Same document with different OCR quality
- Same document with court stamps vs. filed copy
- Draft vs. final version of same filing
- Scanned copy vs. electronic original

### Module E4 — Classify (Lane Assignment via MEEK Signals)
Assign each evidence item to one or more case lanes using MEEK signal detection. MEEK signals are compiled regex patterns defined in `config.py → MEEK_SIGNALS`.

**MEEK Priority Order: E → D → F → C → A → B**

| Signal | Lane | Pattern Examples |
|--------|------|-----------------|
| MEEK4 | E (Misconduct) | `judicial.*misconduct`, `ex.*parte`, `canon.*\d`, `JTC`, `tenure.*commission` |
| MEEK3 | D (PPO) | `protection.*order`, `PPO`, `2023-5907`, `contempt`, `MCL.*600\.2950` |
| MEEK5 | F (Appellate) | `court.*appeals`, `COA`, `366810`, `MCR.*7\.2`, `claim.*appeal` |
| MEEK_FED | C (Federal) | `§.*1983`, `42.*USC`, `1983`, `federal.*court`, `USDC`, `FRCP` |
| MEEK2 | A (Custody) | `custody`, `parenting.*time`, `best.*interest`, `MCL.*722`, `2024-001507` |
| MEEK1 | B (Housing) | `shady.*oaks`, `evict`, `lockout`, `title`, `property`, `2025-002760` |

**Detection Algorithm:**
```
for each evidence_item:
  signals_found = []
  for priority in [E, D, F, C, A, B]:
    if MEEK[priority].search(evidence_item.content):
      signals_found.append(priority)
  primary_lane = signals_found[0] if signals_found else 'UNCLASSIFIED'
  cross_lanes = signals_found[1:] if len(signals_found) > 1 else []
```

**Input:** Extracted content from E2
**Output:** `lane` column populated in `evidence_quotes`, cross-lane references recorded
**Error:** `LaneCrossContaminationError` raised (non-fatal, skip item) when evidence from wrong lane detected in a lane-specific operation

### Module E5 — Authenticate (MRE 901/902 Framework)
Establish admissibility foundation for each evidence item per Michigan Rules of Evidence. Authentication is prerequisite to admissibility — even highly relevant evidence is excluded without proper foundation.

**MRE 901 — Authentication Required:**
- (a) General provision: evidence sufficient to support a finding that it is what proponent claims
- (b)(1) Testimony of witness with knowledge — Andrew testifies to personal knowledge of the item
- (b)(3) Comparison by expert or trier of fact — handwriting comparison, voice identification
- (b)(4) Distinctive characteristics (appearance, contents, substance, internal patterns) — email headers, phone number metadata, writing style
- (b)(7) Public records — government documents in expected custody
- (b)(9) Process or system — showing result produced by process/system with reliable results (computer records, phone extraction reports)
- (b)(10) Methods provided by statute — MCL provisions for specific document types

**MRE 902 — Self-Authenticating (no extrinsic evidence needed):**
- (1) Domestic public documents under seal — certified court orders, official records with seal
- (2) Domestic public documents not under seal (with certification) — government records with attestation
- (4) Certified copies of public records — certified docket sheets, certified judgments
- (5) Official publications — published statutes, rules, government reports
- (8) Acknowledged documents (notarized) — notarized affidavits, acknowledged deeds
- (11) Certified domestic records of a regularly conducted activity — business records with proper certification

**Authentication Scoring:**
```
3 = Self-authenticating (MRE 902) — court orders, certified records, notarized docs
2 = Authenticated via distinctive characteristics (MRE 901(b)(4)) — emails with headers, texts with metadata
1 = Requires testimony (MRE 901(b)(1)) — screenshots, personal observations
0 = Unauthenticated — needs foundation work before admissible
```

**Input:** Classified evidence from E4
**Output:** `evidence_authentication` rows with `auth_method`, `auth_score`, `foundation_needed`
**Query:** `SELECT file_path, auth_method, auth_score, foundation_needed FROM evidence_authentication WHERE auth_score < 2 ORDER BY auth_score ASC`

### Module E6 — Index (Exhibit Indexing & Bates Stamping)
Assign Bates numbers and build the master exhibit index.

**Bates Stamping Protocol:**
- Format: `PIGORS-NNNNN` (5-digit zero-padded, e.g., PIGORS-00001)
- Sequential assignment within each filing package
- Once assigned, a Bates number NEVER changes (append-only)
- Record in `bates_registry`: `bates_number`, `file_path`, `page_number`, `filing_id`, `assigned_date`

**Exhibit Index Structure:**
- `exhibit_number` (e.g., Exhibit A, Exhibit 1)
- `bates_range` (e.g., PIGORS-00001 through PIGORS-00015)
- `description` (1-2 sentence description of what the exhibit contains)
- `authentication` (MRE basis for admissibility)
- `relevance` (which claims this exhibit supports)
- `filing_id` (which filing package this exhibit belongs to)

**Input:** Authenticated evidence from E5
**Output:** `bates_registry` entries, `exhibit_index` rows
**Query:** `SELECT exhibit_number, bates_range, description, filing_id FROM exhibit_index WHERE filing_id = ? ORDER BY exhibit_number`

### Module E7 — Gaps (Evidence Gap Detection via EGCP Scoring)
Identify claims that lack sufficient evidentiary support.

**EGCP Scoring Model:**
- **E** — Evidence exists (0 = none, 1 = weak, 2 = moderate, 3 = strong)
- **G** — Gap severity (0 = no gap, 1 = minor, 2 = significant, 3 = critical)
- **C** — Curability (0 = incurable, 1 = difficult, 2 = feasible, 3 = easy)
- **P** — Priority (0 = low, 1 = medium, 2 = high, 3 = urgent)

**Composite Score:** `EGCP = E - G + C + P` (range: -3 to 9)
- Score ≥ 7: Filing-ready, strong evidence
- Score 4-6: Filing-possible with gap acknowledgment
- Score 1-3: Evidence hardening needed before filing
- Score ≤ 0: Blocked — acquisition task required

**Gap Detection Algorithm:**
```sql
SELECT 
  c.claim_id, c.claim_type, c.vehicle_name,
  (SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.claim_id = c.claim_id) AS evidence_count,
  CASE 
    WHEN (SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.claim_id = c.claim_id) = 0 THEN 'CRITICAL_GAP'
    WHEN (SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.claim_id = c.claim_id) < 3 THEN 'WEAK'
    ELSE 'ADEQUATE'
  END AS gap_status
FROM claims c
WHERE c.status = 'active'
ORDER BY evidence_count ASC;
```

**Input:** Claims table cross-referenced with evidence inventory
**Output:** Gap report with acquisition tasks for missing evidence
**Acquisition Task Format:** When evidence is missing, generate a task specifying: what evidence is needed, where it might be found (which drive, which agency, which person), how to obtain it (FOIA, subpoena, personal records), and the deadline for acquisition.

### Module E8 — Timeline (Chronological Reconstruction)
Build master chronology and per-lane chronologies from dated evidence.

**Timeline Entry Structure:**
```
date_or_range | actor | conduct | target | source_path | source_type | 
confidence | lane | related_order | harm | exhibit | affidavit_use | gap
```

**Confidence Levels:**
- `CONFIRMED` — date and event verified by court record or official document (docket entry, signed order, stamped filing)
- `SUPPORTED` — date and event supported by multiple independent sources (e.g., email + text message + police report)
- `SINGLE_SOURCE` — one source only, needs corroboration before relying on in sworn filings
- `INFERRED` — date estimated from surrounding context (e.g., "the following week" computed from anchor date)
- `APPROXIMATE` — month/year known, exact date unknown (use "on or about" language in filings)

**Timeline Construction Algorithm:**
1. Extract all dated evidence from `evidence_quotes` using `date_referenced` field
2. Merge with `docket_events` for court dates (hearing dates, order dates, filing dates)
3. Add milestone events from `deadlines` (filing deadlines, response deadlines)
4. Sort chronologically and assign confidence levels
5. Identify gaps (periods with no evidence — may indicate withholding or missing records)
6. Cross-reference actors and conduct verbs to detect patterns (see Section 7 below)
7. Generate per-lane views by filtering on `lane` column
8. Export to structured format for affidavit construction

**Required Chronology Views:**
1. `MASTER_CHRONOLOGY` — all events, all lanes
2. `WATSON_CLUSTER_CHRONOLOGY` — Lane A + D events
3. `JUDGE_COURT_CONDUCT_CHRONOLOGY` — Lane E events
4. `SHADY_OAKS_CHRONOLOGY` — Lane B events
5. `PPO_CONTEMPT_JAIL_CHRONOLOGY` — Lane D focused
6. `PARENTING_TIME_WITHHOLDING_CHRONOLOGY` — Subset of Lane A
7. `ORDER_AND_PROCEEDING_CHRONOLOGY` — All court orders and hearings
8. `SERVICE_AND_NONSERVICE_CHRONOLOGY` — Service/nonservice events
9. `HARM_AND_ESCALATION_CHRONOLOGY` — Pattern evidence
10. `RECENT_EMERGENCY_CHRONOLOGY` — Last 90 days

---

## 2. Per-Lane Evidence Distribution

Query for current counts — never hardcode:
```sql
SELECT lane, COUNT(*) AS quote_count 
FROM evidence_quotes 
WHERE lane IS NOT NULL 
GROUP BY lane 
ORDER BY quote_count DESC;
```

Expected approximate distribution (verify with query above):
- **Lane E (Misconduct):** Highest concentration — judicial violation evidence
- **Lane A (Custody):** Second highest — parenting time, best-interest factor evidence
- **Lane D (PPO):** Third — protection order and contempt evidence
- **Lane B (Housing):** Moderate — property and lockout evidence
- **Lane F (Appellate):** Lower — primarily cites evidence from other lanes
- **Lane C (Federal):** Minimal — pre-filing stage, evidence still being assembled

---

## 3. Key DB Tables

### evidence_quotes
The primary evidence table. Each row is a quotable passage extracted from a source document.
- Key columns: `quote_id`, `quote_text`, `source_file`, `page_number`, `date_referenced`, `lane`, `vehicle_name`, `claim_id`, `filing_id`, `confidence`, `authentication_score`
- Query: `SELECT quote_id, quote_text, source_file, lane FROM evidence_quotes WHERE lane = ? ORDER BY date_referenced`

### documents
Master file inventory across all drives.
- Key columns: `doc_id`, `file_path`, `file_hash`, `file_size`, `mime_type`, `discovered_date`, `processed`, `lane`
- Query: `SELECT file_path, mime_type, file_size, lane FROM documents WHERE processed = 1 ORDER BY discovered_date DESC`

### evidence_atoms
Atomic facts extracted from documents — smaller and more granular than quotes.
- Key columns: `atom_id`, `content`, `source_file`, `page_number`, `entity_type`, `entity_value`, `date_value`
- Query: `SELECT atom_id, content, entity_type, entity_value FROM evidence_atoms WHERE entity_type = 'DATE' ORDER BY date_value`

### exhibit_index
Maps exhibits to filing packages with Bates ranges and descriptions.
- Key columns: `exhibit_id`, `exhibit_number`, `bates_range`, `description`, `authentication`, `filing_id`, `relevance`
- Query: `SELECT exhibit_number, bates_range, description FROM exhibit_index WHERE filing_id = ? ORDER BY exhibit_number`

### bates_registry
Bates number assignment log — append-only, numbers never reused.
- Key columns: `bates_number`, `file_path`, `page_number`, `filing_id`, `assigned_date`
- Query: `SELECT MAX(CAST(REPLACE(bates_number, 'PIGORS-', '') AS INTEGER)) AS last_bates FROM bates_registry`

### evidence_authentication
Authentication status and method for each evidence item.
- Key columns: `auth_id`, `file_path`, `auth_method`, `auth_score`, `mre_basis`, `foundation_needed`, `authenticated_date`
- Query: `SELECT auth_method, COUNT(*) FROM evidence_authentication GROUP BY auth_method ORDER BY COUNT(*) DESC`

### judicial_violations
Documented judicial conduct violations — feeds Lane E.
- Key columns: `violation_id`, `violation_type`, `description`, `date_occurred`, `mcr_rule`, `canon_violated`, `evidence_source`, `severity`
- Query: `SELECT violation_type, COUNT(*), AVG(severity) FROM judicial_violations GROUP BY violation_type ORDER BY COUNT(*) DESC`

---

## 4. Content-Based Dedup Rules

### Absolute Rules (Non-Negotiable)
1. **NEVER rely solely on file hashing.** SHA-256 is a first-pass filter only. Always peek inside.
2. **OPEN and compare actual content** before declaring a duplicate.
3. **Move all duplicates to I:\ drive** — never hard-delete. Path: `I:\dedup\[SHA256_prefix]\[filename]`
4. **Preserve the highest-quality version** as the canonical copy:
   - Electronic original > scanned copy
   - Higher OCR quality > lower OCR quality
   - Court-stamped version > unstamped draft
   - Later version > earlier version (unless both are needed for timeline)
5. **Log every dedup decision** with: original_path, duplicate_path, decision_reason, confidence_level

### Comparison Checklist
When two files hash-match OR have similar names:
- [ ] Open both files and read first page
- [ ] Compare page counts
- [ ] Compare file creation/modification dates
- [ ] Check for court stamps, file stamps, or watermarks
- [ ] Check for handwritten annotations
- [ ] Verify header/footer content matches
- [ ] If scanned: compare OCR quality (character count, error rate)
- [ ] If PDF: compare metadata (author, creator, producer)

### Edge Cases
- **Same content, different formatting:** Keep both — formatting differences may be legally significant
- **Draft vs. filed version:** Keep both — drafts may contain attorney notes or redlined changes
- **Exhibit copy vs. standalone:** Keep both — exhibit may have Bates stamps or exhibit tabs
- **Partially overlapping content:** Not duplicates — classify and index separately

---

## 5. Bates Stamping Protocol — Detailed

### Format Specification
```
PIGORS-NNNNN
│       │
│       └─ 5-digit zero-padded sequential number (00001-99999)
└──────── Fixed prefix identifying Andrew James Pigors as producing party
```

### Assignment Rules
1. Assign sequentially within each filing package
2. Each page gets its own Bates number (not each document)
3. Multi-page documents get a range: `PIGORS-00001 through PIGORS-00015`
4. Bates numbers are PERMANENT and APPEND-ONLY — once assigned, never reassigned
5. Maintain a gap-free sequence within each filing package
6. Cross-filing-package numbering continues from the last assigned number
7. Record every assignment in `bates_registry` immediately

### Current State Query
```sql
-- Get the next available Bates number
SELECT 'PIGORS-' || PRINTF('%05d', COALESCE(MAX(CAST(REPLACE(bates_number, 'PIGORS-', '') AS INTEGER)), 0) + 1) AS next_bates
FROM bates_registry;

-- Get Bates assignments for a filing
SELECT bates_number, file_path, page_number 
FROM bates_registry 
WHERE filing_id = ? 
ORDER BY bates_number;
```

---

## 6. EGCP Scoring — Extended Reference

### Scoring Rubric by Claim Type

**Custody Claims (Lane A):**
- Best-interest factor claims need evidence for each of the 12 MCL 722.23 factors
- Minimum 2 supporting quotes per factor for ADEQUATE rating
- Parenting time interference claims need dated incidents with corroboration

**PPO Claims (Lane D):**
- Requires specific incidents with dates, witnesses, or documentation
- Pattern evidence strengthens individual incident claims
- Contempt claims require proof of specific order + specific violation

**Misconduct Claims (Lane E):**
- Each violation type needs: (1) the conduct, (2) the rule/canon violated, (3) the harm
- Ex parte contact claims need circumstantial or direct evidence of the contact
- Bias claims need pattern of disparate treatment with comparison baseline

**Appellate Claims (Lane F):**
- Requires preserved objection in trial court record
- Needs specific order being challenged + legal basis for challenge
- Standard of review determination affects evidence sufficiency threshold

### Acquisition Task Template
When EGCP score ≤ 3 for any claim, generate an acquisition task:
```
ACQUISITION TASK
  Claim: [claim_id] — [description]
  Gap: [what evidence is missing]
  Source Options:
    1. [Drive/path where evidence might exist]
    2. [Agency/person who might have it]
    3. [FOIA target if government record]
  Method: [FOIA / Subpoena / Personal Records / Search drives]
  Deadline: [When this evidence is needed by]
  Priority: [Based on EGCP P-score]
```

---

## Key DB Queries

### 1. Evidence inventory by lane
```sql
SELECT lane, COUNT(*) AS total,
  SUM(CASE WHEN confidence = 'CONFIRMED' THEN 1 ELSE 0 END) AS confirmed,
  SUM(CASE WHEN confidence = 'SINGLE_SOURCE' THEN 1 ELSE 0 END) AS single_source
FROM evidence_quotes
WHERE lane IS NOT NULL
GROUP BY lane
ORDER BY total DESC;
```

### 2. Unauthenticated evidence requiring foundation
```sql
SELECT ea.file_path, ea.auth_score, ea.foundation_needed, d.mime_type
FROM evidence_authentication ea
JOIN documents d ON ea.file_path = d.file_path
WHERE ea.auth_score < 2
ORDER BY ea.auth_score ASC
LIMIT 30;
```

### 3. Evidence gaps by claim
```sql
SELECT c.claim_id, c.claim_type, c.vehicle_name,
  (SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.claim_id = c.claim_id) AS ev_count,
  CASE 
    WHEN (SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.claim_id = c.claim_id) = 0 THEN 'CRITICAL'
    WHEN (SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.claim_id = c.claim_id) < 3 THEN 'WEAK'
    WHEN (SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.claim_id = c.claim_id) < 6 THEN 'MODERATE'
    ELSE 'STRONG'
  END AS strength
FROM claims c
WHERE c.status = 'active'
ORDER BY ev_count ASC;
```

### 4. Cross-lane evidence items
```sql
SELECT eq.source_file, eq.lane AS primary_lane,
  GROUP_CONCAT(DISTINCT eq2.lane) AS also_relevant_to
FROM evidence_quotes eq
JOIN evidence_quotes eq2 ON eq.source_file = eq2.source_file AND eq.lane != eq2.lane
GROUP BY eq.source_file, eq.lane
ORDER BY COUNT(DISTINCT eq2.lane) DESC
LIMIT 20;
```

### 5. Timeline construction query
```sql
SELECT date_referenced, quote_text, source_file, lane,
  vehicle_name, confidence
FROM evidence_quotes
WHERE date_referenced IS NOT NULL
ORDER BY date_referenced ASC;
```

---

## 7. Pattern Detection — Identifying Systemic Conduct

Evidence gains exponential power when it reveals patterns. Isolated incidents are easy to dismiss; documented patterns are compelling. The evidence brain must always search for patterns across the timeline.

### Pattern Categories to Detect

**Retaliation Pattern:**
When Andrew files a motion or makes a complaint, Emily or the court responds with a punitive action (PPO filing, custody restriction, contempt charge) within a predictable timeframe.
```sql
SELECT e1.date_referenced AS andrew_action_date, e1.quote_text AS andrew_action,
       e2.date_referenced AS response_date, e2.quote_text AS response_action,
       JULIANDAY(e2.date_referenced) - JULIANDAY(e1.date_referenced) AS days_between
FROM evidence_quotes e1
JOIN evidence_quotes e2 ON e2.date_referenced > e1.date_referenced
  AND JULIANDAY(e2.date_referenced) - JULIANDAY(e1.date_referenced) BETWEEN 1 AND 30
WHERE e1.lane = 'A' AND e1.claim_type LIKE '%motion%'
  AND e2.lane IN ('D', 'A') AND e2.claim_type LIKE '%ppo%' OR e2.claim_type LIKE '%contempt%'
ORDER BY e1.date_referenced;
```

**Parenting Time Withholding Pattern:**
Systematic denial or interference with Andrew's court-ordered parenting time.
- Track: dates of scheduled parenting time, whether exercised, reason for denial
- Source: text messages, emails, FOC records, police reports

**Accusation Escalation Pattern:**
Accusations against Andrew that escalate in severity over time without corresponding evidence.
- Track: date, accusation type, severity level, evidence supporting accusation
- Look for: vague → specific → criminal allegations without corroboration

**Hostile Record Pattern (Lane E):**
Court record entries that consistently disadvantage Andrew — missing filings, incorrect dates, selective recording of testimony.
- Track: docket entries that omit Andrew's filings or mischaracterize his positions
- Source: docket_events cross-referenced with filing_packages

**Process Weaponization Pattern:**
Using legal processes (PPOs, contempt, CPS reports) as weapons rather than for their intended protective purposes.
- Track: filing dates, outcomes, retaliatory timing, lack of factual basis
- Source: cross-lane evidence from A, D, and E

### Pattern Strength Scoring
- **3+ incidents** with **consistent timing** and **no legitimate explanation** = STRONG pattern
- **2 incidents** with **suspicious timing** = MODERATE pattern (needs more evidence)
- **1 incident** = ISOLATED (not a pattern, but may be part of one)

---

## 8. Evidence Preservation Protocol

### Append-Only Rule (NON-NEGOTIABLE)
- **NEVER overwrite an original evidence file.** Create new versions only.
- **NEVER hard-delete evidence.** Move to I:\ if archiving.
- **Every modification creates a new version** with a new hash, linked to the original via `source_id`.

### Chain of Custody Documentation
For every evidence item that may be introduced at trial:
1. Record who discovered/obtained the item and when
2. Record every access and transfer (who touched it, when, why)
3. Maintain hash integrity — any content change creates a new version
4. Document storage location at each stage (which drive, which directory)

### Digital Evidence Best Practices
- **Screenshots:** Capture full screen including URL bar, timestamps, device time
- **Text messages:** Capture full thread context, not isolated messages
- **Emails:** Preserve full headers (From, To, Date, Subject, Message-ID)
- **Social media:** Archive with Wayback Machine or screenshot with metadata
- **Audio/video:** Preserve original format, do not re-encode
- **Scanned documents:** Scan at 300+ DPI, save as PDF/A for long-term preservation

---

## Cross-Wiring Points

| This Brain | Links To | Via Column(s) |
|------------|----------|---------------|
| Ω2 Evidence → Ω1 Litigation | `evidence_quotes.vehicle_name` → `claims.vehicle_name` |
| Ω2 Evidence → Ω1 Litigation | `evidence_quotes.filing_id` → `filing_packages.package_id` |
| Ω2 Evidence → Ω1 Litigation | `evidence_quotes.claim_id` → `claims.claim_id` |
| Ω2 Evidence → Ω3 Forms | `exhibit_index.filing_id` → form package requires exhibit list |
| Ω2 Evidence → Ω4 Rules | `judicial_violations.mcr_rule` → `authority_master_index.identifier` |
| Ω2 Evidence → Ω4 Rules | `judicial_violations.canon_violated` → Canon authority entries |
| Ω1 Litigation → Ω2 Evidence | `filing_readiness.vehicle_name` drives evidence gap analysis |
| Ω3 Forms → Ω2 Evidence | Filing package assembly pulls from `exhibit_index` and `bates_registry` |
| Ω4 Rules → Ω2 Evidence | `authority_chains_v2.supporting_evidence` references evidence items |
