# PROCESS BLUEPRINT — LitigationOS Filing Factory DNA

> **Version:** 1.0 · **Date:** 2025-07-14 · **System:** LitigationOS Event Horizon Δ∞
>
> This document reverse-engineers every step from raw evidence to court-ready
> filings — the exact process that produced **30+ filing packages** across
> **8 jurisdictions** for **19 defendants** seeking **$3.4M–$22.9M in damages**.
> It is the DNA of the product: detailed enough to replicate for ANY case.

---

## Build-By-Numbers (What This Process Actually Produced)

| Metric | Value |
|--------|-------|
| Files scanned | 1.47M across 6 drives (C/D/F/G/H/I), 526 GB |
| Duplicates detected | 63,493 found, 36,860 moved to I:\ |
| Files classified | 172,532 into 13 categories |
| Database tables | 702 tables, 18.1M rows, 10.22 GB |
| Filing packages | 30+ assembled |
| PDFs generated | 148+ documents, 1,212 pages total |
| Jurisdictions | 8 (14th Circuit, COA, MSC, WDMI, EDMI, 6th Cir., SCOTUS, JTC) |
| Defendants | 19 named parties |
| Damages claimed | $3.4M–$22.9M |
| Pipeline phases | 17 (Phase 0 through Phase 16) |
| Agent fleet | 155+ agents across 7 tiers |
| AI skills | 54 MANBEARPIG skills, 140+ JSON-RPC methods |
| MCP tools | 45 tools across 9 categories |

---

## Phase 1 — EVIDENCE INTAKE

### Input
Raw files on 6 physical drives (C:\, D:\, F:\, G:\, H:\, I:\) containing legal
documents, court filings, emails, screenshots, PDFs, chat exports, financial
records, photos, and miscellaneous digital evidence. No structure. No index.

### Process

**1.1 — Safety Snapshot (Phase 0)**
Before touching anything, create a SHA-256 manifest of every file on every drive.
This is the append-only evidence guarantee — originals are never overwritten.

```
Phase 0 → SHA-256 manifest + full backup snapshot
         Stored: 00_SYSTEM/safety_snapshots/
```

**1.2 — Multi-Drive Scanning (Phase 1: Inventory)**
The pipeline walks every drive root and catalogs files into `drive_inventory.db`:

- File path, size, extension, modification date
- SHA-256 hash of first 64 KB (fast fingerprint) + full hash for < 10 MB files
- Drive letter, depth level, parent directory classification
- Scan rate: ~12,000 files/minute on SSD, ~3,000 on HDD

**Orchestrator:** `00_SYSTEM/pipeline/run_omega_pipeline.py` — Phase 1 module
**Key script:** `smart_drive_scanner.py` — parallel directory walker

**1.3 — Content-Based Deduplication (Phase 2)**
Not hash-only — Andrew's iron rule: "peek inside the document."

1. SHA-256 groups files with identical hashes
2. For each hash group, open files and compare actual content (first 4 KB + structure)
3. Canonical selection uses 8-priority bucket system:
   - Priority 1: `01_FILINGS/` (court-filed originals)
   - Priority 2: `10_Exhibits/` (exhibit-stamped copies)
   - Priority 3: `Legal Documents/` (working copies)
   - Priority 4–8: Progressively lower-priority directories
4. Canonical file stays; duplicates move to `I:\dedup_archive\` (NEVER deleted)

**Output:** 63,493 duplicates identified → 36,860 safely moved to I:\ drive.

### Output
`drive_inventory.db` with complete file catalog, `content_dedup_registry` table
with canonical/duplicate mappings, SHA-256 manifest for provenance chain.

### Tools Used
`smart_drive_scanner.py`, `_dedup_fast.py`, `_dedup_scan.py`, `convergence_dedup_engine.md`

### Michigan-Specific
MI court e-filing (MiFILE) has a 25 MB per-document upload limit. Scanning flags
oversized PDFs early so they can be split before filing.

### Generalization
Replace drive letters with configurable `SCAN_ROOTS` in `config.py`. The 8-priority
bucket system is jurisdiction-agnostic — just reorder the priority directories.

---

## Phase 2 — DOCUMENT PROCESSING

### Input
172,532 classified files from the inventory phase.

### Process

**2.1 — PDF Text Extraction**
PyMuPDF (`fitz`) extracts text page-by-page, preserving layout coordinates.
Each page becomes a row in the `pages` table with full-text content and metadata.

**2.2 — OCR for Scanned Images**
Tesseract OCR processes image-only PDFs and standalone images (screenshots,
scanned court orders). Results feed into the same `pages` pipeline.

**2.3 — DOCX/RTF Parsing**
python-docx extracts paragraphs, tables, headers. Preserves formatting metadata
(bold = emphasis, tables = structured data, headers = section boundaries).

**2.4 — Structured Data Ingestion**
CSV files → SQLite tables. JSON metadata → document attributes.
Court docket exports → structured `dockets` table.
Financial records → `financial_evidence` table with amount extraction.

**2.5 — Email/Chat Evidence Parsing**
Chat exports (ChatGPT, SMS, email) are parsed into timestamped message sequences.
Each message gets: sender, timestamp, content, attachments list.
200+ pages of chat exports were processed in this build.

### Output
`documents` table (metadata), `pages` table with FTS5 index (`pages_fts`),
`md_sections` table with FTS5 index (`md_sections_fts`). Every piece of text is
now searchable via hybrid FTS5 + BM25 queries.

### Tools Used
`PyMuPDF`, `Tesseract`, `python-docx`, Phase 4a–4e extraction modules

### Michigan-Specific
Michigan court orders follow a predictable format: caption → body → "IT IS SO
ORDERED" → judge signature block. The parser uses these landmarks to extract
ruling text separately from procedural boilerplate.

### Generalization
Add jurisdiction-specific document templates to `config.py` → `DOC_TEMPLATES`.
The extraction pipeline is format-agnostic; only the landmark detection needs
customization per state.

---

## Phase 3 — ENTITY & CITATION EXTRACTION

### Input
Full-text content from all processed documents (pages table + FTS5 index).

### Process

**3.1 — Three-Pass Classification System**

*Pass 1 — Extension + Path Patterns:*
Maps files into 11 categories by extension and directory signals:
`LEGAL_DOC`, `LEGAL_TEXT`, `STRUCTURED_DATA`, `GRAPH_DATA`, `EVIDENCE_IMAGE`,
`ARCHIVE`, `SCRIPT`, `WEB_DOC`, `IRRELEVANT`, `OTHER`, `SKIP`

*Pass 2 — Content Signals:*
Opens each file and scores content using a weighted formula:

```
score = (citation_count × 3.0) + (legal_keywords × 1.5) + dollar_amounts + dates
```

High-scoring `OTHER` files get reclassified as `LEGAL_DOC` or `LEGAL_TEXT`.

*Pass 3 — MEEK Lane Assignment:*
Five compiled regex signal sets route evidence to case lanes:

| Signal | Lane | Pattern Examples |
|--------|------|-----------------|
| MEEK1 | B (Housing) | `shady oaks`, `2025-002760`, `habitability` |
| MEEK2 | A (Custody) | `watson`, `2024-001507`, `custody`, `parenting time` |
| MEEK3 | D (PPO) | `2023-5907-PP`, `protection order`, `stalking` |
| MEEK4 | E (Misconduct) | `mcneill`, `judicial misconduct`, `JTC` |
| MEEK5 | F (Appellate) | `COA`, `366810`, `court of appeals` |

Detection priority: **E → D → F → C → A → B** (most specific first).
`LaneCrossContaminationError` fires when evidence appears in the wrong lane.

**3.2 — Citation Pattern Extraction**
Six citation types are detected via compiled regex:

| Type | Pattern | Example |
|------|---------|---------|
| MCL | `MCL \d+\.\d+` | MCL 600.1701 |
| MCR | `MCR \d+\.\d+` | MCR 2.003(D) |
| MRE | `MRE \d+` | MRE 801(d)(1) |
| CASE_CITE | `\d+ Mich\.? (App\.?)? \d+` | 123 Mich App 456 |
| USC | `\d+ U\.?S\.?C\.? § ?\d+` | 42 USC § 1983 |
| CANON | Michigan Code of Judicial Conduct references | Canon 2, Rule 2.2 |

**3.3 — Entity Extraction**
Party names, judge names, case numbers, dollar amounts, and dates are extracted
using regex + pattern matching (MANBEARPIG's entity extraction skill). Results
populate `graph_nodes`, `risk_events`, and entity relationship tables.

### Output
`graph_nodes` table (entities + relationships), citation index, lane assignments
per file, classified file inventory with category and MEEK signal.

### Tools Used
`phase3_classify.py`, `config.py` → `MEEK_SIGNALS`, `citation_checker.py`,
MANBEARPIG `extract_entities()` skill

### Michigan-Specific
MCR/MCL/MRE patterns are Michigan-only. The citation regex set is defined in
`config.py` and swapped per jurisdiction. Michigan case citations use the
`Mich` / `Mich App` reporter format.

### Generalization
Define a `CITATION_PATTERNS` dict per jurisdiction in config. Add state-specific
court rule prefixes (e.g., `ORCP` for Oregon, `CPLR` for New York). The MEEK
signal framework is case-agnostic — just define new regex sets per matter.

---

## Phase 4 — EVIDENCE ANALYSIS

### Input
Classified, extracted, lane-assigned evidence with entity and citation indexes.

### Process

**4.1 — Evidence-to-Claim Mapping**
Each piece of evidence is scored against every active claim using BM25 relevance
+ entity overlap + citation co-occurrence. The `action_scores` table stores
per-claim relevance scores (0–100).

**4.2 — Contradiction Detection**
`contradiction_detector.py` cross-references statements across all evidence:
- Same party making inconsistent statements at different times
- Court filings contradicting sworn testimony
- Financial records contradicting verbal claims
Results feed the impeachment engine.

**4.3 — Impeachment Item Identification**
`extract_impeachment.py` identifies prior inconsistent statements suitable for
cross-examination. Each item gets: source document, page, statement text,
contradicting document, and impeachment strength score.

**4.4 — Timeline Construction**
`build_timelines.py` extracts all dated events and constructs per-lane timelines.
Outputs chronological event sequences with source citations. The
`timeline_anomaly_detector.md` engine flags gaps, overlaps, and suspicious
temporal patterns.

**4.5 — Gap Analysis (EGCP Scoring)**
For each claim in each lane, the system scores evidence completeness:
- **E**vidence: Do we have documentary proof? (0–25)
- **G**ap: What's missing? (0–25, inverse)
- **C**itation: Do we have legal authority? (0–25)
- **P**recedent: Do we have binding case law? (0–25)

Claims scoring below 50 generate acquisition tasks (what evidence to find).

**4.6 — Strength Scoring**
`case_strength_model.ts` / MANBEARPIG `case_strength_scorer` skill produces
per-claim strength scores (0–100) based on evidence weight, authority support,
contradiction exposure, and opposing-party vulnerability.

### Output
`action_scores` table, impeachment items, timelines, gap analysis reports,
claim strength scores, contradiction maps.

### Tools Used
`contradiction_detector.py`, `extract_impeachment.py`, `build_timelines.py`,
`deep_evidence_scan.py`, `analysis_engine.py`, MANBEARPIG skills:
`case_strength_scorer`, `evidence_clusterer`, `impeachment_engine`

### Michigan-Specific
Michigan's Friend of the Court (FOC) reports are treated as high-priority
evidence in custody lanes. PPO evidence (Lane D) has special handling for
MCL 600.2950 requirements (specific acts of harassment/stalking).

### Generalization
The EGCP scoring framework is jurisdiction-agnostic. Replace Michigan-specific
claim types in `config.py` → `CLAIM_TYPES` for other states. The impeachment
engine works on any adversarial proceeding.

---

## Phase 5 — LEGAL RESEARCH

### Input
Claim inventory with gap analysis, citation index, authority needs per claim.

### Process

**5.1 — Authority Search (LEXOS Brain Feed)**
Phase 5 feeds extracted knowledge into 50 micro-brains organized across 8
categories. Each brain specializes in a legal domain (custody law, housing
code, judicial ethics, civil rights, etc.).

Hybrid search: FTS5 full-text + BM25 relevance ranking + entity overlap
scoring. The `court_rules` table contains 1,000+ Michigan court rules
indexed for instant retrieval.

**5.2 — Citation Validation**
Every cited authority is checked against the database:
- Is the statute still in effect? (not repealed/amended)
- Is the case still good law? (not overruled/distinguished)
- Is the court rule current? (MCR amendments tracked)

**5.3 — Authority Chain Building**
For each claim, the system builds a citation chain:
1. **Binding authority** — Michigan Supreme Court, COA (published)
2. **Persuasive authority** — COA (unpublished), other state courts
3. **Federal authority** — 6th Circuit, SCOTUS
4. **Secondary sources** — treatises, law review articles

The `authority_chains` table stores chain completeness (`chain_complete` flag)
and linking relationships between authorities.

**5.4 — Deadline Calculation**
Court rules drive deadline computation:
- MCR 2.108: Service deadlines (21 days for answer)
- MCR 7.204: Appeal filing (21 days from entry)
- MCR 7.212: Brief filing (56 days from claim of appeal)
- Local rules: 14th Circuit specific motion hearing schedules

Deadlines populate the `deadlines` table with urgency scores and ICS calendar
export capability.

### Output
Authority index, validated citation chains, deadline calendar, enriched
micro-brains, gap acquisition tasks for missing authorities.

### Tools Used
MANBEARPIG skills: `find_authority`, `precedent_matcher`, `index_of_authorities`,
`build_authority_guides.py`, MCP tools: `authority_index`, `citation_graph`,
`deadline_dashboard`, `deadline_add`

### Michigan-Specific
MCR rules are the primary deadline source. Michigan's published/unpublished
opinion distinction affects authority weight. The Friend of the Court has its
own procedural timeline separate from general civil rules.

### Generalization
Replace `court_rules` entries with target jurisdiction rules. The authority
chain hierarchy (binding → persuasive → federal) applies universally — just
swap the court hierarchy definition.

---

## Phase 6 — FILING GENERATION

### Input
Claim analysis with evidence mapping, authority chains, deadline calendar.

### Process

**6.1 — Filing Type Selection**
Based on claim analysis and procedural posture, the system selects filing types:
- Complaints (new actions)
- Motions (within existing cases)
- Briefs (appellate)
- Emergency motions (time-sensitive)
- Responses / replies
- JTC complaints (judicial misconduct)
- Federal § 1983 actions

**6.2 — Court Caption Generation**
Each jurisdiction gets a properly formatted caption:
- State: "STATE OF MICHIGAN / IN THE [COURT] FOR THE COUNTY OF [X]"
- Federal: "UNITED STATES DISTRICT COURT / WESTERN DISTRICT OF MICHIGAN"
- Appellate: "IN THE MICHIGAN COURT OF APPEALS" or "IN THE MICHIGAN SUPREME COURT"

**6.3 — Argument Drafting**
MANBEARPIG's `filing_generator` and `motion_generator` skills draft arguments:
1. Statement of facts (sourced from evidence, every fact cite-checked)
2. Legal standard (from authority chain)
3. Application (evidence applied to legal elements)
4. Relief requested (from claim type)

**6.4 — Filing State Machine**
Every filing moves through a strict state progression:

```
DRAFT → REVIEW → QA_PASS → READY → FILED → SERVED
```

No filing advances without passing the prior gate. The `filing_readiness`
MCP tool reports current state for all active filings.

**6.5 — Filing Stack Assembly (Event Horizon)**
The Event Horizon factory assembles filing stacks:

```
forms + rules + evidence → instruction atoms → requirements graph
→ AKN templates → filing stacks → lint → satisfaction → graph export
→ CyclePack
```

Each `FilingStack` contains: cover page, motion/brief body, exhibits,
proposed order, certificate of service, proof of service.

### Output
Draft filings per claim per jurisdiction, filing state tracking,
`FilingStack` objects with all components linked.

### Tools Used
`filing.py` engine (FilingStack, StackComponent, ValidationResult classes),
MANBEARPIG skills: `filing_generator`, `motion_generator`, `response_drafter`,
`proposed_order_generator`, MCP tools: `filing_readiness`, `filing_validate`,
`filing_assemble`

### Michigan-Specific
MCR 2.113 governs motion format. MCR 7.212 governs appellate brief format.
SCAO form numbers (MC, DC, CC, FOC series) are required for many filing types.
The `court-form-finder` agent maps filing types to exact SCAO form numbers.

### Generalization
Define filing templates per jurisdiction in `packet_templates/`. The state
machine is universal. Caption formats, form requirements, and formatting rules
are config-driven.

---

## Phase 7 — DOCUMENT ASSEMBLY

### Input
Draft filings, exhibits, authority citations, service lists.

### Process

**7.1 — PDF Generation with Court Formatting**
Strict compliance with Michigan court rules:
- **Margins:** 1 inch all sides
- **Font:** Times New Roman, 12-point
- **Spacing:** Double-spaced (body), single-spaced (block quotes, footnotes)
- **Page limits:** Brief = 50 pages, Motion = 20 pages, Reply = 10 pages
- **Page numbers:** Bottom center, Arabic numerals

**7.2 — Table of Contents & Table of Authorities**
Auto-generated from document headings (TOC) and citation index (TOA).
TOA groups authorities by type: Cases, Statutes, Court Rules, Other.
Page references are dynamically computed.

**7.3 — Exhibit Bates Stamping**
Format: `PIGORS_XXXX` (sequential, zero-padded to 4 digits).
The `bates_assign` MCP tool manages the Bates number registry.
`exhibit_index` generates the exhibit list with descriptions.

**7.4 — Cover Pages**
Per-jurisdiction cover pages with court caption, case number, filing title,
attorney/party information, and filing date.

**7.5 — Certificate of Service**
Auto-generated listing all parties served, method of service (mail, email,
e-filing, personal), and date of service.

**7.6 — Proof of Service Templates**
SCAO-approved proof of service forms pre-populated with party addresses,
filing descriptions, and service method.

### Output
Court-formatted PDFs, Bates-stamped exhibits, TOC/TOA, cover pages,
certificates and proofs of service. 148+ PDFs totaling 1,212 pages.

### Tools Used
`PyMuPDF` for PDF manipulation, `exhibit-formatter` agent for Bates stamps,
`filing.py` engine for assembly, MCP tools: `bates_assign`, `exhibit_index`,
`filing_export`

### Michigan-Specific
SCAO forms have specific formatting that must be preserved (form numbers in
footer, checkbox fields, specific margin requirements). MiFILE e-filing
requires PDF/A format and ≤ 25 MB per document.

### Generalization
Define page-format rules in a `COURT_FORMAT` config dict per jurisdiction.
Bates prefix is configurable (`PIGORS_` → `{CLIENT_NAME}_`). Service
requirements are driven by court rules, not hardcoded.

---

## Phase 8 — QUALITY ASSURANCE

### Input
Assembled filing packages with all components.

### Process

**8.1 — Six-Gate QA Pipeline**

| Gate | Check | Failure Action |
|------|-------|----------------|
| **G1: Completeness** | All required components present (body, exhibits, service cert) | Block filing, list missing items |
| **G2: Citations** | Every legal citation verified against authority DB | Flag unverified cites for manual review |
| **G3: Format** | MCR compliance (margins, font, spacing, page limits) | Auto-fix where possible, flag where not |
| **G4: Service** | All defendants on service list, addresses current | Block until service list verified |
| **G5: Signatures** | Signature blocks present, verification stamps | Add signature blocks if missing |
| **G6: Compliance** | Jurisdiction-specific rules (MCR 7.212, local rules) | Detailed compliance report with fix instructions |

**8.2 — Red-Team Adversarial Review**
MANBEARPIG's `adversary_war_room` skill reviews each filing as opposing
counsel would, identifying:
- Weak arguments an opponent could attack
- Factual claims without sufficient evidence
- Procedural vulnerabilities (standing, jurisdiction, timeliness)
- Counter-arguments and how to pre-empt them

**8.3 — Factual Accuracy Verification**
Every factual statement in every filing is traced back to source evidence.
Statements without evidence support are flagged. The `evidence_chain` MCP
tool validates the full provenance chain: claim → argument → fact → evidence
→ source document → page number.

**8.4 — Placeholder Resolution**
Scan all documents for unresolved placeholders: `[INSERT]`, `{{variable}}`,
`[DATE]`, `[AMOUNT]`, `TBD`, etc. Zero placeholders is a hard gate — no
filing advances with any placeholder remaining. The `placeholder_scan` and
`placeholder_resolve` MCP tools automate this.

**8.5 — Party Name Consistency**
Cross-filing verification that party names are spelled identically across
all 30+ filings. Catches "McNeill" vs "McNeil" vs "Mc Neill" variations.

**8.6 — Phase 15 Validation (Automated)**
Five automated validation checks run at pipeline end:
1. Atom store integrity (every atom has ID + source)
2. Citation format regex validation
3. Lane cross-contamination detection
4. Touchlog coverage (modified files have audit entries)
5. Brain nucleus size limits (≤ 500 KB per file)

Results: **PASS / FAIL / WARN** with detailed diagnostics.

### Output
QA report per filing, compliance checklist, adversarial review notes,
placeholder resolution log, party name consistency report.

### Tools Used
`phase15_validation.py`, `pre-filing-qa` agent, MCP tools: `prefiling_qa`,
`qa_sweep`, `signature_check`, `service_check`, `placeholder_scan`,
`placeholder_resolve`, MANBEARPIG: `adversary_war_room`, `pre_filing_validator`

### Michigan-Specific
MCR 7.212(B) requires specific sections in appellate briefs (jurisdictional
statement, statement of questions, statement of facts, argument, relief).
The QA gate checks for all required sections by heading detection.

### Generalization
Define QA gates per filing type in config. The six-gate framework is
universal — customize the specific checks within each gate.

---

## Phase 9 — FILING PACKAGING

### Input
QA-passed filing packages ready for submission.

### Process

**9.1 — E-Filing Format Preparation**

| System | Format | Requirements |
|--------|--------|-------------|
| **MiFILE** (Michigan state) | PDF/A, ≤ 25 MB | Separate PDFs per document type |
| **CM/ECF** (Federal) | PDF, ≤ 35 MB | Main document + attachments |
| **Manual filing** (some courts) | Paper, original + copies | Print-ready formatting |

**9.2 — Service Requirement Calculation**
Per-defendant service matrix generated from court rules:
- Method: personal service, mail, email, e-filing notification
- Timing: MCR 2.107 (service timing), MCR 2.108 (answer deadline)
- Proof: SCAO proof of service form per defendant per filing

The `service-tracker` agent maintains a cross-case service ledger.

**9.3 — Fee Waiver Applications**
In forma pauperis (IFP) applications auto-generated where applicable.
Financial affidavit templates pre-populated from case data.

**9.4 — Filing Calendar**
All deadlines compiled into a master calendar:
- Filing deadlines with urgency scoring (critical/high/medium/low)
- Response deadlines (triggered by opponent filings)
- Hearing dates
- ICS calendar export for integration with external calendar apps
- The `filing-countdown` agent provides a real-time urgency dashboard

**9.5 — Multi-Drive Backup**
Every filing package is backed up to at least 2 drives:
- Primary: `C:\Users\andre\LitigationOS\01_FILINGS\`
- Backup: `I:\LitigationOS_Backup\` or `F:\Backup\`
- Version-controlled copies with timestamps

### Output
E-filing-ready packages, service tracking ledger, fee waiver applications,
filing calendar with ICS export, multi-drive backups.

### Tools Used
`filing_packager.py`, `service-tracker` agent, `filing-countdown` agent,
MCP tools: `efiling_prep`, `filing_export`, `backup_create`, `backup_version`,
`calendar_generate`, `calendar_sync`

### Michigan-Specific
MiFILE requires separate document uploads per filing type (motion, brief,
exhibits are separate uploads). Some Michigan courts (e.g., Muskegon County)
still accept paper filings for certain motion types.

### Generalization
E-filing system integration is abstracted behind the `efiling_prep` tool.
Add new e-filing systems by implementing the upload format specification.
Service rules are court-rule-driven and config-based.

---

## Phase 10 — CONTINUOUS IMPROVEMENT

### Input
Court outcomes, error logs, new evidence, system metrics.

### Process

**10.1 — Court Outcome Tracking**
When a court rules on a filing, the outcome is recorded:
- Granted / Denied / Granted in part
- Judge reasoning (extracted from order text)
- Feeds back into QA rules (what worked, what didn't)

**10.2 — Error Pattern Mining**
Pipeline error logs are analyzed for recurring patterns:
- Common OCR failures → improve preprocessing
- Citation format misses → expand regex patterns
- Lane misclassification → refine MEEK signals
- QA gate failures → tighten upstream checks

**10.3 — Knowledge Graph Enrichment**
New evidence, rulings, and legal developments continuously enrich the graph:
- `graph_nodes` + `graph_edges` tables grow with each pipeline run
- Authority chains are extended as new cases are decided
- Party relationship maps deepen with each discovery cycle

**10.4 — Model Retraining**
MANBEARPIG's TF-IDF + Naive Bayes models retrain on new corpus:
- `train_model.py` (~60 second cycle)
- `self_evolve_v2.py` runs self-improvement loops
- New skills can be added to the 54-skill roster without code changes

**10.5 — Agent Fleet Evolution**
The 155+ agent fleet evolves through:
- Performance metrics per agent (success rate, processing time)
- Superpower agents handle cross-cutting optimization
- Agent memory persists insights across sessions

### Output
Updated QA rules, refined MEEK signals, enriched knowledge graph,
retrained models, improved agent fleet.

### Tools Used
`self_evolve_v2.py`, `train_model.py`, `session_recall.py`,
MANBEARPIG self-healing + auto-reconnect, `agent_memory` MCP server

### Michigan-Specific
Michigan appellate decisions (published and unpublished) are tracked for
authority chain updates. MCR amendments are monitored and reflected in
deadline calculations and format requirements.

### Generalization
The feedback loop is jurisdiction-agnostic. Define outcome categories and
tracking fields per jurisdiction. The model retraining pipeline works on
any legal corpus.

---

## Infrastructure Summary

### The 17-Phase Pipeline

| Phase | Name | Module | Purpose |
|-------|------|--------|---------|
| 0 | Safety Snapshot | `phase0_snapshot` | SHA-256 manifest + backup |
| 1 | Inventory | `phase1_inventory` | Multi-drive file scanning |
| 2 | Dedup | `phase2_dedup` | Content-based deduplication |
| 3 | Classify | `phase3_classify` | 3-pass classification + MEEK routing |
| 4a | Extract PDF | `phase4a_extract_pdf` | PDF text extraction |
| 4b | Extract DOCX | `phase4b_extract_docx` | DOCX/RTF parsing |
| 4c | Extract Structured | `phase4c_extract_structured` | CSV/JSON/SQL ingestion |
| 4d | Atomize | `phase4d_atomize` | Break documents into atomic claims |
| 4e | Extract Archive | `phase4e_extract_archive` | ZIP/archive unpacking |
| 5 | LEXOS Brain Feed | `phase5_brain_feed` | 50 micro-brains, 8 categories |
| 6 | Gap Analysis | `phase6_gap_analysis` | EGCP scoring per claim |
| 7a | Graph Delta | `phase7a_graph_delta` | Knowledge graph updates |
| 7b | Synthesis Merge | `phase7b_synthesis_merge` | Cross-source synthesis |
| 7c | Knowledge Merge | `phase7c_knowledge_merge` | Unified knowledge base |
| 8 | Litigation Refresh | `phase8_lit_refresh` | Impeachment + authority + readiness |
| 9 | MCP Ingest | `phase9_mcp_ingest` | MCP server data loading |
| 10 | Judicial Analysis | `phase10_judicial` | Judge profiling + bias scan |
| 11 | Legal Action Discovery | `phase11_actions` | New claim identification |
| 12 | Rule Audit | `phase12_rule_audit` | Court rule compliance check |
| 13 | Refinement | `phase13_refine` | Legal theory + fact extraction |
| 14 | Finalization | `phase14_finalize` | Filing atom-to-stack matching |
| 15 | Validation | `phase15_validation` | 5-check automated QA |
| 16 | Desktop Offload | `phase16_offload` | GUI app data sync |

### The Agent Fleet

| Fleet | Count | Tiers | Role |
|-------|-------|-------|------|
| Delta9 | 56 | 7 (Tier1–3, J, K, L, Convergence) | Core pipeline execution |
| Delta999 | 12 | — | Advanced engines (classifier, validator, assembly) |
| Copilot | 64 | — | Specialized sub-agents (filing, research, QA) |
| Superpower | 13 | — | Cross-cutting orchestration |
| Convergence | 10 | — | Phase 5–6 hardening, filing workflow |

Agent contract: `run() → AgentResult(agent_id, status, stats)`
Status: `SUCCESS` | `FATAL` | `CRASH`
Error protocol: 7 layers (try → catch → broad-catch → checkpoint → deadman → retry → fallback)

### The Six Case Lanes

| Lane | Case | MEEK | Signal |
|------|------|------|--------|
| A | Custody (Watson) | MEEK2 | `custody`, `parenting`, `2024-001507` |
| B | Housing (Shady Oaks) | MEEK1 | `shady oaks`, `habitability`, `2025-002760` |
| C | Convergence | — | Multi-lane cross-references |
| D | PPO | MEEK3 | `protection order`, `2023-5907-PP` |
| E | Judicial Misconduct | MEEK4 | `mcneill`, `JTC`, `judicial misconduct` |
| F | Appellate | MEEK5 | `COA`, `366810`, `court of appeals` |

### AI Stack (100% Local — Zero Network)

| Component | Technology | Role |
|-----------|-----------|------|
| MANBEARPIG v9.0 | TF-IDF + Naive Bayes + BM25 + semantic embeddings | Primary inference (54 skills) |
| LocalAI | TF-IDF + pattern matching | Pipeline provider |
| Offline heuristic | Regex/keyword fallback | Always-available baseline |

No remote API calls. No cloud dependencies. All data stays on local drives.

---

## Replication Checklist (For New Cases)

To replicate this process for a completely new case:

1. **Configure lanes** — Define case lanes in `config.py` with MEEK signal regexes
2. **Set scan roots** — Point `SCAN_ROOTS` to drives containing evidence
3. **Define claim types** — Add jurisdiction-specific claims to `CLAIM_TYPES`
4. **Load court rules** — Import target jurisdiction rules into `court_rules` table
5. **Set citation patterns** — Define regex patterns for jurisdiction's legal citations
6. **Configure filing templates** — Add court caption + format rules to `packet_templates/`
7. **Define deadlines** — Import court rule deadlines into `deadlines` table
8. **Run pipeline** — `python run_omega_pipeline.py` (full 17-phase execution)
9. **Review QA gates** — Address all FAIL items before advancing to READY
10. **Package and file** — Use e-filing tools for target court system

**Estimated time:** First run on a new case with ~10,000 files: 4–8 hours.
Subsequent incremental runs: 30–60 minutes.

---

*This document is the product's DNA. Every filing LitigationOS produces
follows this exact process. The phases are sequential, the gates are
non-negotiable, and the evidence chain is unbroken from raw file to
court-ready PDF.*
