---
name: OMEGA-EVIDENCE
description: >-
  Use when processing, authenticating, classifying, deduplicating, or organizing
  evidence across all 6 local drives. Covers the full evidence lifecycle from
  raw file discovery through SHA-256 fingerprinting, content-based deduplication,
  MEEK lane classification, MRE authentication, Bates stamping, exhibit indexing,
  gap analysis, and timeline forensics. Michigan Rules of Evidence (MRE 901/902).
  All 6 case lanes (A-F). NEVER hard-delete — move duplicates to I:\ drive.
  Content-based dedup ONLY — peek inside documents, never rely solely on hashing.
category: discipline
version: "2.0.0"
triggers:
  - evidence
  - exhibit
  - Bates
  - chain of custody
  - authentication
  - dedup
  - forensics
  - scan
  - classify
  - MRE 901
  - MRE 902
  - OCR
  - drive scan
  - fingerprint
  - MEEK
  - inventory
  - extraction
  - timeline
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: Pigors v Watson
dependencies: []
metadata:
  tier: 1
  fused_skills: 10
  author: andrew-pigors + copilot-omega
  forge_date: 2026-03-21
---

# 🔬 OMEGA-EVIDENCE 🔬

> **TIER 1 — Core Litigation Evidence Pipeline**
> **Pipeline:** Raw Files → Scan → Fingerprint → Dedup → Classify → Extract → Authenticate → Index → Link → Timeline
> **Case:** Pigors v Watson · 6 drives · 6 lanes · 12 GB intelligence database
> **Iron Law:** NEVER hard-delete. Content-based dedup. Every item traceable to source.

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                        OMEGA-EVIDENCE v2.0                               ║
║               10 Skills → 8 Modules → 1 Evidence System                  ║
║                                                                          ║
║  E1  Drive Scanning ──────┐                                              ║
║  E2  Extraction & OCR ────┤→ E4 Classification ──→ E5 Authentication     ║
║  E3  Deduplication ───────┘        ↓                      ↓              ║
║  E7  Gap Analysis ←───── E6 Bates & Index ──→ E8 Timeline Forensics     ║
║                                                                          ║
║  Drives: C:\ D:\ F:\ G:\ H:\ I:\                                       ║
║  DB: litigation_context.db (evidence_quotes, documents, atoms, claims)   ║
║  Output: Court-ready exhibits with authentication & chain of custody     ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Forged from 10 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|---------------------|
| 1 | `litigation-evidence-harvester` | Drive scanning, file discovery, intake pipeline |
| 2 | `litigation-evidence-authentication` | MRE 901/902, chain of custody, admissibility |
| 3 | `drive-forensic-scanner` | SHA-256 fingerprinting, metadata extraction, drive inventory |
| 4 | `file-organizer` | File type detection, directory structuring, naming conventions |
| 5 | `evidence-intelligence-nexus` | Cross-referencing evidence to claims, intelligence linking |
| 6 | `evidence-context-injector` | Context enrichment, evidence-to-filing integration |
| 7 | `litigation-timeline-forensics` | Chronological ordering, date extraction, pattern detection |
| 8 | `litigation-asset-discovery-engine` | Multi-drive asset location, hidden file detection |
| 9 | `convergence_dedup_engine` | Content-based deduplication, I:\ routing, cluster analysis |
| 10 | `litigation-os` (evidence subsystem) | Pipeline phases 1-4, MEEK classification, lane routing |

---

## When to Apply

- **Drive scanning** — Inventory files across C:\, D:\, F:\, G:\, H:\, I:\ drives
- **Evidence intake** — New documents, screenshots, recordings, emails entering the system
- **Deduplication** — Cleaning duplicate files (MUST peek inside, not just hash)
- **Classification** — Assigning evidence to case lanes A-F via MEEK signals
- **Authentication prep** — Building MRE 901/902 foundations for court admissibility
- **Exhibit assembly** — Bates stamping, tab indexing, master exhibit list generation
- **Gap analysis** — Finding missing evidence for specific claims (EGCP scoring)
- **Timeline construction** — Building chronological event sequences from documents
- **OCR processing** — Extracting text from scanned PDFs and images
- **Chain of custody** — Tracking evidence provenance from source to filing

---

## Decision Tree

```
Evidence task received
  │
  ├─ "Scan" / "inventory" / "find files"
  │   └─→ E1: Drive Scanning & Inventory
  │
  ├─ "Extract" / "OCR" / "parse" / "read PDF"
  │   └─→ E2: Extraction & OCR
  │
  ├─ "Dedup" / "duplicate" / "clean up" / "organize"
  │   └─→ E3: Deduplication (content-based, move to I:\)
  │
  ├─ "Classify" / "lane" / "MEEK" / "route"
  │   └─→ E4: Classification & Lane Routing
  │
  ├─ "Authenticate" / "MRE" / "admissible" / "foundation"
  │   └─→ E5: Authentication & Admissibility
  │
  ├─ "Bates" / "exhibit" / "stamp" / "index"
  │   └─→ E6: Bates Stamping & Exhibit Indexing
  │
  ├─ "Gap" / "missing" / "what do I need" / "coverage"
  │   └─→ E7: Evidence Gaps & Linking
  │
  ├─ "Timeline" / "chronolog" / "when" / "sequence"
  │   └─→ E8: Timeline Forensics
  │
  └─ Complex / multi-step
      └─→ Run E1 → E2 → E3 → E4 → E5 → E6 → E7 → E8 sequentially
```

---

## ██ MODULE E1: Drive Scanning & Inventory ██

### Purpose
Discover and catalog all evidence files across 6 local drives. Build a complete
inventory with SHA-256 fingerprints, file metadata, and initial type classification.

### Drive Map

| Drive | Contents | Priority |
|-------|----------|----------|
| C:\ | LitigationOS repo, active working files, pipeline outputs | HIGH |
| D:\ | Overflow storage, older evidence batches | MEDIUM |
| F:\ | Document archives, correspondence, financial records | HIGH |
| G:\ | Media files (photos, videos, recordings) | HIGH |
| H:\ | Backup drive, historical snapshots | LOW |
| I:\ | Dedup destination, archive, overflow | DEDUP TARGET |

### Scanning Protocol

1. **File discovery** — Recursive scan with `fd` or `Get-ChildItem -Recurse`
2. **Type detection** — Classify by extension AND magic bytes (don't trust extensions alone)
3. **SHA-256 fingerprint** — Hash every file for dedup and provenance tracking
4. **Metadata extraction** — Created/modified dates, file size, EXIF data for images
5. **MEEK signal detection** — Scan filenames and first 500 bytes for lane indicators
6. **Database registration** — Insert into `documents` table in `litigation_context.db`

### Key Rules
- Scan ALL 6 drives — evidence is scattered everywhere
- Never skip hidden files or system-adjacent directories (evidence hides in odd places)
- Log every scan operation to `agent_log` table for audit trail
- If a file can't be read (locked/corrupted), log it and continue — never crash the scan

### Database Tables
```sql
-- Primary evidence inventory
SELECT file_path, sha256, file_type, file_size, created_date, lane
FROM documents WHERE drive = ?;

-- Scan log for audit trail
SELECT agent_id, action, file_path, timestamp
FROM agent_log WHERE action LIKE 'scan%';
```

---

## ██ MODULE E2: Extraction & OCR ██

### Purpose
Extract machine-readable text from all document formats. Every piece of evidence
must have searchable text content for the pipeline to classify, link, and cite.

### Extraction by File Type

| Format | Tool | Method |
|--------|------|--------|
| PDF (text) | PyMuPDF (`fitz`) | `page.get_text()` — fast, preserves layout |
| PDF (scanned) | PyMuPDF + OCR fallback | Extract images → OCR → reassemble text |
| DOCX | `python-docx` | Paragraph and table extraction |
| Images (JPG/PNG) | Tesseract OCR / local OCR | Image → text with confidence scoring |
| Email (EML/MSG) | `email` stdlib / `extract-msg` | Headers + body + attachment extraction |
| Excel (XLSX) | `openpyxl` | Cell-by-cell with sheet identification |
| Text/CSV | Direct read | UTF-8 with fallback encoding detection |

### OCR Quality Gates
- **Confidence threshold**: Flag pages with OCR confidence < 80%
- **Manual review queue**: Low-confidence pages go to `ready_queue` for human review
- **Re-OCR protocol**: If first pass fails, try with image preprocessing (deskew, contrast)

### Pipeline Integration
```
Phase 4a: PDF extraction (PyMuPDF)
Phase 4b: DOCX extraction (python-docx)
Phase 4c: Structured data extraction (forms, tables)
Phase 4d: Atomization (break documents into evidence atoms)
Phase 4e: Archive extraction (ZIP/RAR contents)
```

### Output Format
Every extracted document produces an evidence atom:
```python
{
    "atom_id": "ATM-00001",
    "source_file": "F:\\Correspondence\\email_2024-03-15.pdf",
    "source_sha256": "a3f8c9...",
    "extracted_text": "...",
    "extraction_method": "pymupdf",
    "confidence": 0.95,
    "page_count": 3,
    "lane": "A",
    "timestamp_extracted": "2026-03-21T10:00:00Z"
}
```

---

## ██ MODULE E3: Deduplication ██

### Purpose
Identify and consolidate duplicate evidence files. This is a USER-CRITICAL module —
Andrew explicitly requires content-based dedup, not hash-only.

### ⚠️ IRON RULES (Non-Negotiable)

1. **NEVER hard-delete files** — Move duplicates to `I:\LitigationOS_Dedup\`
2. **Content-based comparison** — Open files and compare actual content, not just hashes
3. **Peek inside documents** — Andrew said: "no hashing — peek at the document to ensure they are the same"
4. **SHA-256 as pre-filter ONLY** — Matching hashes are candidates, but MUST verify content
5. **Keep the best copy** — If versions differ slightly, keep the most complete one
6. **Log every move** — Record source path, destination path, reason, and timestamp

### Dedup Algorithm (3-Phase)

```
Phase 1: Hash Pre-Filter
  ├─ Compute SHA-256 for all files
  ├─ Group files with identical hashes
  └─ Files with unique hashes → SKIP (not duplicates)

Phase 2: Content Verification (MANDATORY)
  ├─ For each hash-match group:
  │   ├─ Open both files
  │   ├─ Compare first 4KB of content (text or binary)
  │   ├─ For text: normalize whitespace, compare semantic content
  │   ├─ For PDF: compare extracted text page-by-page
  │   └─ For images: compare pixel data or perceptual hash
  └─ Only confirmed content-identical files → mark as duplicates

Phase 3: Resolution
  ├─ Keep the file with:
  │   ├─ Most complete metadata
  │   ├─ Best OCR quality
  │   ├─ Earliest creation date (original)
  │   └─ Location on primary drive (C: > F: > G: > D: > H:)
  ├─ Move duplicates to I:\LitigationOS_Dedup\[original_drive]\[path]
  └─ Update documents table: SET status='dedup_moved', dedup_kept_path=?
```

### Database Tracking
```sql
-- Dedup clusters
SELECT cluster_id, file_count, kept_path, moved_paths
FROM dedup_clusters WHERE status = 'resolved';

-- Dedup audit trail
INSERT INTO dedup_clusters (cluster_id, sha256, file_count, kept_path, moved_paths, reason)
VALUES (?, ?, ?, ?, ?, 'content-verified identical');
```

---

## ██ MODULE E4: Classification & Lane Routing ██

### Purpose
Assign every evidence item to the correct case lane (A-F) using MEEK signal detection.
Prevent cross-contamination between lanes.

### MEEK Signal Priority Order: E → D → F → C → A → B

| Signal | Lane | Pattern Examples |
|--------|------|-----------------|
| MEEK4 | E (Misconduct) | "judicial misconduct", "JTC", "McNeill bias", "recusal" |
| MEEK3 | D (PPO) | "personal protection", "PPO", "2023-5907-PP", "restraining" |
| MEEK5 | F (Appellate) | "court of appeals", "COA", "366810", "appellant", "appellee" |
| — | C (Convergence) | Multi-lane evidence, cross-references, pattern evidence |
| MEEK2 | A (Custody) | "custody", "parenting time", "2024-001507-DC", "FOC", "L.D.W." |
| MEEK1 | B (Housing) | "Shady Oaks", "housing", "2025-002760-CZ", "eviction" |

### Classification Protocol

1. **Filename scan** — Check filename for MEEK keywords
2. **Content scan** — Extract first 2KB of text content, scan for MEEK patterns
3. **Case number detection** — Match `20XX-XXXXXX-XX` patterns to known case numbers
4. **Multi-lane detection** — Evidence matching 2+ lanes → Lane C (Convergence)
5. **Ambiguous routing** — If no clear signal, flag for manual review in `ready_queue`

### Cross-Contamination Prevention
```python
class LaneCrossContaminationError(Exception):
    """Non-fatal. Skip item and log warning."""
    pass

# Detection: evidence from wrong lane detected during processing
# Action: Log warning, skip item, continue pipeline
# NEVER: Silently assign to wrong lane
```

### Database Update
```sql
UPDATE documents SET lane = ?, meek_signal = ?, classification_confidence = ?
WHERE document_id = ?;
```

---

## ██ MODULE E5: Authentication & Admissibility ██

### Purpose
Build the legal foundation for each evidence item to be admissible in court under
the Michigan Rules of Evidence (MRE).

### Authentication Methods (MRE 901)

| Rule | Method | When to Use | Example |
|------|--------|-------------|---------|
| MRE 901(b)(1) | Testimony of witness with knowledge | Firsthand evidence | "I took this screenshot on [date]" |
| MRE 901(b)(3) | Expert testimony | Technical evidence | Digital forensics expert verifies metadata |
| MRE 901(b)(4) | Distinctive characteristics | Unique identifying features | Email headers, writing style, phone numbers |
| MRE 901(b)(7) | Public records | Government documents | Court filings, CPS reports, police reports |
| MRE 901(b)(9) | Process or system | Computer-generated records | Database records, automated logs |

### Self-Authenticating Documents (MRE 902)

| Rule | Category | Examples |
|------|----------|---------|
| MRE 902(1) | Domestic public documents under seal | Certified court records |
| MRE 902(4) | Certified copies of public records | FOC reports, vital records |
| MRE 902(5) | Official publications | Published statutes, court rules |
| MRE 902(7) | Trade inscriptions | Business letterheads, invoices |
| MRE 902(11) | Certified domestic records of regularly conducted activity | Business records with certification |

### Chain of Custody Template
```
CHAIN OF CUSTODY — [Exhibit ID]
═══════════════════════════════
1. ORIGIN: [Source file path] on [Drive]
   Date discovered: [scan date]
   SHA-256: [hash]
   
2. INTAKE: Scanned by OMEGA-EVIDENCE pipeline
   Date processed: [processing date]
   Extraction method: [method]
   
3. VERIFICATION: Content verified against original
   Date verified: [date]
   Verifier: [agent_id or human]
   
4. CLASSIFICATION: Assigned to Lane [X]
   MEEK signal: [signal]
   
5. INDEXING: Bates number [PIGORS-XXXXX]
   Exhibit tab: [tab number]
   
6. CURRENT STATUS: [location and status]
```

### Database Tracking
```sql
-- Authentication records
SELECT exhibit_id, auth_method, mre_rule, chain_of_custody, status
FROM evidence_authentication WHERE exhibit_id = ?;
```

---

## ██ MODULE E6: Bates Stamping & Exhibit Indexing ██

### Purpose
Apply sequential Bates numbers to all evidence pages and build a master exhibit index
for court filing.

### Bates Number Format
```
PIGORS-00001  through  PIGORS-99999
```

### Stamping Protocol

1. **Number assignment** — Sequential, no gaps, across all exhibits in a filing
2. **Stamp placement** — Bottom-right corner of every page
3. **Multi-page documents** — Each page gets its own Bates number
4. **Cross-reference** — Every Bates number maps to exhibit ID and page number
5. **Range tracking** — "Exhibit A: PIGORS-00001 through PIGORS-00047"

### Master Exhibit Index Format
```
MASTER EXHIBIT INDEX — Pigors v Watson
Case No. 2024-001507-DC
═══════════════════════════════════════

Ex. | Description              | Bates Range          | Pages | Auth
----+--------------------------+----------------------+-------+-----
A   | FOC Recommendation       | PIGORS-00001 - 00012 | 12    | 902(4)
B   | Text Messages (Mar 2024) | PIGORS-00013 - 00089 | 77    | 901(b)(4)
C   | CPS Investigation Report | PIGORS-00090 - 00103 | 14    | 902(1)
...
```

### Database Tables
```sql
-- Bates stamp registry
SELECT bates_number, exhibit_id, page_number, document_id
FROM bates_registry WHERE exhibit_id = ?;

-- Exhibit index
SELECT exhibit_label, description, bates_start, bates_end, page_count, auth_method
FROM exhibit_index WHERE filing_id = ? ORDER BY exhibit_label;
```

---

## ██ MODULE E7: Evidence Gaps & Linking ██

### Purpose
Identify missing evidence for each claim and link existing evidence to the claims
it supports. Uses EGCP scoring (Evidence-Gaps-Claims-Proof).

### EGCP Scoring Framework

| Component | Score Range | Meaning |
|-----------|------------|---------|
| **E** (Evidence) | 0-5 | Strength of existing evidence for this claim |
| **G** (Gaps) | 0-5 | Severity of missing evidence (5 = critical gap) |
| **C** (Claims) | 0-5 | Legal viability of the claim itself |
| **P** (Proof) | 0-5 | Overall proof sufficiency for court |

### Gap Detection Process

1. **List all claims** — Query `claims` table for active claims per lane
2. **Map evidence** — For each claim, find linked evidence in `evidence_quotes`
3. **Score coverage** — Rate E/G/C/P for each claim
4. **Prioritize gaps** — Sort by gap severity (highest G score first)
5. **Generate acquisition tasks** — For each gap, specify what evidence is needed

### Evidence-to-Claim Linking
```sql
-- Find evidence supporting a specific claim
SELECT eq.quote_text, eq.source_document, eq.relevance_score
FROM evidence_quotes eq
JOIN claim_evidence_links cel ON eq.quote_id = cel.evidence_id
WHERE cel.claim_id = ?
ORDER BY eq.relevance_score DESC;

-- Find claims with no evidence
SELECT c.claim_id, c.claim_type, c.description
FROM claims c
LEFT JOIN claim_evidence_links cel ON c.claim_id = cel.claim_id
WHERE cel.evidence_id IS NULL AND c.status = 'active';
```

### Filing Threshold Assessment
- **Ready to file**: E ≥ 3, G ≤ 2, C ≥ 3, P ≥ 3
- **Needs more evidence**: E < 3 or G > 2
- **Claim viability issue**: C < 3 (reconsider claim strategy)
- **Not ready**: P < 3 (insufficient proof standard)

---

## ██ MODULE E8: Timeline Forensics ██

### Purpose
Build chronological event timelines from evidence documents. Detect patterns,
gaps in activity, and temporal anomalies.

### Date Extraction Methods

| Source | Extraction | Confidence |
|--------|-----------|------------|
| Document metadata | File created/modified dates | MEDIUM (can be altered) |
| Email headers | `Date:` header field | HIGH |
| Court filing stamps | OCR from filed-stamp dates | HIGH |
| Text content | Regex for date patterns | MEDIUM (needs context) |
| EXIF data | Photo/video timestamps | HIGH (unless stripped) |
| File naming | Date patterns in filenames | LOW (verify against content) |

### Timeline Construction
```
1. Extract ALL dates from ALL evidence items
2. Normalize to ISO 8601 (YYYY-MM-DD HH:MM:SS)
3. De-duplicate events (same date + same event description)
4. Sort chronologically
5. Identify gaps (periods with no documented activity)
6. Flag anomalies (out-of-order events, impossible timelines)
7. Cross-reference with known court dates from docket_events
```

### Pattern Detection Targets

| Pattern | Significance | Detection Method |
|---------|-------------|-----------------|
| Escalation | Increasing severity over time | Frequency + severity scoring |
| Cyclic behavior | Repeated patterns around events | Period analysis |
| Response delays | Slow responses to time-sensitive matters | Gap analysis between action-reaction |
| Coincidence clustering | Events that cluster suspiciously | Statistical clustering |
| Documentation gaps | Periods with no records | Calendar gap detection |

### Database Output
```sql
-- Timeline events
SELECT event_date, event_type, description, source_document, lane, confidence
FROM timeline_events
WHERE lane = ? AND event_date BETWEEN ? AND ?
ORDER BY event_date;

-- Gap detection
SELECT gap_start, gap_end, gap_days, lane, significance
FROM timeline_gaps WHERE significance >= 'MEDIUM';
```

---

## ██ GLOBAL RULES (Apply to ALL Modules) ██

### File Handling
- **NEVER hard-delete** — Move to `I:\` or Recycle Bin
- **Content-based dedup** — Peek inside documents to confirm duplicates
- **All duplicates → I:\ drive** — `I:\LitigationOS_Dedup\[drive]\[path]`
- **SHA-256 everywhere** — Every file gets fingerprinted on first contact

### Traceability
- Every evidence item traceable to: source file → drive → SHA-256 → lane → exhibit
- Every statistic backed by a DB query (table + WHERE clause)
- Every authentication claim linked to specific MRE rule
- Chain of custody from discovery through court filing

### Database Access
```python
# ALWAYS use managed_db() for database access
from db_lock_manager import managed_db

with managed_db() as conn:
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    # ... queries ...
```

### Error Handling (7-Layer Protocol)
1. Try operation → 2. Specific catch → targeted recovery
3. Broad catch → log + skip + continue → 4. Checkpoint every N items
5. Deadman switch (120s no progress) → 6. Agent retry (3× backoff)
7. Tier fallback → orchestrator flags + continues

### Anti-Hallucination
- NEVER fabricate evidence counts — run `SELECT COUNT(*)` and cite the query
- NEVER invent file paths — verify with `os.path.exists()` before referencing
- NEVER assume evidence exists — query the DB first, then report what's actually there
- If data is missing, create an acquisition task — do not fill with placeholders
