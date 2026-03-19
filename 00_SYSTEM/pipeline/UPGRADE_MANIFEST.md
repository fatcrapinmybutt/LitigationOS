# DELTA9 AGENT UPGRADE MANIFEST
## LitigationOS Pipeline — Per-Agent Assessment & Improvement Plan
## Generated: 2025-07-25

---

## TIER 1 — INDEX SCOUTS (Lane 1 Infrastructure)

### A01-A04: Index Scouts (C, D, F, GI drives)
**Does Well:**
- Parallel drive scanning with Windows long-path support
- Skip-list filtering for irrelevant directories (node_modules, .git, etc.)
- Efficient bulk INSERT into files table

**Missing/Poor:**
- No incremental scanning — re-scans everything on each run
- No file-change detection (modified timestamp comparison)
- No symlink/junction-point handling (common on Windows with OneDrive)

**Improvements:**
- Add `last_scan_ts` to files table; only scan files modified after last run
- Add `os.path.islink()` check to avoid infinite loops on junction points
- File: `agents/lane1_infrastructure/a01_index_scout_c.py` — add `WHERE modified > last_run_ts` filter

---

## TIER 2 — DEDUP & ARCHIVE

### A05: Legal Dedup
**Does Well:**
- SHA-256 hash-based deduplication
- Canonical election using bucket priority system

**Missing/Poor:**
- No fuzzy/near-duplicate detection (same document with different headers/footers)
- No content-aware dedup (identical text in different PDF layouts)

**Improvements:**
- Add SimHash or MinHash for near-duplicate detection
- Store first 1000 chars text hash as secondary dedup signal
- File: `agents/lane1_infrastructure/a05_legal_dedup.py` — add content fingerprint column

### A06-A07: Data/Code Dedup
**Does Well:** Standard hash dedup for non-legal files
**Missing:** These rarely matter for litigation — consider deprioritizing

### A08: Archive Cracker
**Does Well:**
- Handles .zip, .rar, .7z, .tar.gz
- Catalogs inner file contents without full extraction

**Missing/Poor:**
- No password-protected archive handling
- No nested archive detection (zip-in-zip)
- No memory limit on extraction (a 50GB archive could OOM)

**Improvements:**
- Add extraction memory limit (max 500MB per archive)
- Log password-protected archives for manual review
- File: `agents/lane1_infrastructure/a08_archive_cracker.py` — add size guard before extraction

---

## TIER 3 — EXTRACTION

### A09: Flatten Commander
**Does Well:** Coordinates extraction ordering
**Missing:** No dependency tracking on which files need which extractor

### A10: PDF Harvester ★ CRITICAL AGENT
**Does Well:**
- Dual-engine extraction (pymupdf + pdfplumber fallback)
- Encrypted/zero-page PDF detection
- Citation and entity atom generation
- MEEK lane detection from content signals

**Missing/Poor:**
- **BUG: `agent_source` column doesn't exist in ready_queue** (line 108-110)
- No OCR for scanned documents (huge gap — many court docs are scans)
- No page-level atom tracking (atoms don't record which PDF page)
- No table extraction (pdfplumber can extract tables, not used)
- MD5 used for atom IDs instead of SHA-256 (inconsistent with rest)
- `source_page` is always None in atom inserts (lines 199-206)

**Improvements:**
1. **Fix BUG-001:** Change `agent_source` to `claimed_by` in INSERT at line 108
2. Add Tesseract OCR fallback with `needs_ocr` flag
3. Track page numbers: pass page index through extraction loop
4. Add table extraction using `pdfplumber.extract_tables()`
5. Switch atom IDs to SHA-256 truncated
- File: `agents/lane1_infrastructure/a10_pdf_harvester.py` — lines 108, 126-131, 191-231

### A11: Text Miner
**Does Well:** Extracts text from .txt, .md, .csv, .json files
**Missing:** No structured metadata extraction from JSON/CSV (just raw text)

### A12: Struct Parser
**Does Well:** Parses structured data files
**Missing:** No JSONL streaming for large files (loads entire file into memory)

---

## TIER J — JUDICIAL INTELLIGENCE (Lane 2)

### J01-J02: McNeill/Hoopes Profilers
**Does Well:**
- Judge-specific pattern matching
- Ruling pattern analysis

**Missing/Poor:**
- No temporal analysis (how judge's rulings changed over time)
- No comparison against published benchbook standards
- No recusal-motion history tracking

**Improvements:**
- Add chronological ruling analysis to detect bias patterns
- Cross-reference with JTC complaint database
- File: `agents/lane2_intelligence/j01_mcneill_profiler.py`

### J03: Benchbook Auditor
**Does Well:** Compares judicial behavior against Michigan benchbook
**Missing:** Benchbook rules are likely hardcoded — needs regular updates

### J04: Canon Mapper
**Does Well:** Maps judicial conduct to Michigan Code of Judicial Conduct canons
**Missing:** No weighted severity scoring per canon violation

### J05: JTC Compiler
**Does Well:** Compiles Judicial Tenure Commission complaint data
**Missing:** No integration with public JTC records for historical context

### J06: Disqualification Engine
**Does Well:** Identifies potential disqualification grounds
**Missing:**
- No MCR 2.003(C)(1) rubric scoring
- No Caperton v. Massey factor analysis
- No automatic motion template generation

### J07: Ex Parte Detector
**Does Well:** Detects ex parte communication patterns
**Missing:**
- No calendar/docket cross-reference (to verify timing)
- No communication metadata analysis

### J08: Transcript Impeacher ★ CRITICAL AGENT
**Does Well:**
- Speaker extraction from transcript format
- Contradiction detection using MRE 613/801(d)(1) patterns
- Per-witness impeachment index generation
- Confidence-based severity scoring

**Missing/Poor:**
- **BUG: Hardcodes all contradictions to Lane A** (line 129) — Lane B/C transcripts get mis-routed
- No cross-transcript contradiction detection (witness says X in depo, Y at hearing)
- No deposition page/line citation tracking (critical for impeachment motions)
- Confidence scoring is simplistic (binary: 0.6 or 0.85)
- No MRE 611(c) leading question detection
- `_ensure_tables()` doesn't CREATE the atoms table (line 54) — relies on it existing

**Improvements:**
1. **Fix BUG-006:** Detect lane from file's `meek_lane` column or content analysis
2. Add cross-transcript contradiction matching (store per-witness statements, compare across files)
3. Add page/line citation tracking from transcript format
4. Implement graduated confidence scoring (0.0-1.0 continuous)
5. Add leading question and suggestive question detection
- File: `agents/lane2_intelligence/j08_transcript_impeacher.py` — lines 54, 129, 142-190

---

## TIER K — CASE INTELLIGENCE (Lane 2)

### K01: Lane A Custody
**Does Well:** Custody-specific evidence analysis
**Missing:**
- No Best Interest Factor (MCL 722.23 a-l) systematic mapping
- No established custodial environment (ECE) analysis
- No parenting-time computation under MCL 722.27a

### K02: Lane A PPO
**Does Well:** Protection order analysis
**Missing:** No MCL 600.2950 element-by-element checklist validation

### K03: Lane B Housing
**Does Well:** Habitability evidence collection
**Missing:**
- No building code violation severity ranking
- No rent abatement calculation per MCL 554.139

### K04: Lane C Convergence
**Does Well:** Cross-case pattern detection
**Missing:**
- No Monell policy/custom aggregation
- No qualified immunity analysis framework

### K05: Person Profiler
**Does Well:** Entity relationship mapping
**Missing:** No role-change tracking (e.g., Rusco as both FOC and attorney)

### K06: Timeline Builder
**Does Well:** Chronological event ordering
**Missing:**
- No deadline/statute-of-limitations calculation
- No MCR filing deadline tracking

### K07: Authority Harvester
**Does Well:** Citation extraction and categorization
**Missing:**
- No Shepard's/KeyCite-style validity checking
- No binding vs. persuasive authority classification

### K08: Contradiction Detector
**Does Well:** Cross-document contradiction finding
**Missing:** No sworn vs. unsworn statement distinction (affects evidentiary weight)

---

## TIER L — LEGAL WARFARE (Lane 2)

### L01-L03: Lane Scorers (A, B, C)
**Does Well:** Composite evidence scoring per lane
**Missing:** Scores aren't calibrated against actual filing success rates

### L04: Gap Detector
**Does Well:** Identifies missing evidence
**Missing:** No priority ranking of gaps by filing deadline proximity

### L05: Citation Validator
**Does Well:** Validates citation format
**Missing:** No case-law currency check (is the cited case still good law?)

### L06: Damages Calculator
**Does Well:** Basic damages estimation
**Missing:**
- No Michigan-specific statutory multiplier application
- No treble damages calculation for consumer protection (MCL 445.911)
- No attorney fee estimation

### L07: Filing Readiness
**Does Well:** Readiness assessment
**Missing:** No SCAO form compliance check

### L08: Red Team Scanner
**Does Well:** Adversarial weakness analysis
**Missing:** No opposing counsel strategy prediction

---

## CONVERGENCE TIER

### F01: Filing Factory ★ CRITICAL AGENT
**Does Well:**
- Assembles filing manifests from scored actions
- Caps exhibit lists at 50 (practical)
- Writes structured JSON filing packages

**Missing/Poor:**
- **No actual document generation** — only produces JSON manifests, not Word/PDF court documents
- No SCAO form template population
- No certificate of service generation
- No proof of service tracking
- No e-filing format validation (Michigan courts use TrueFiling)
- Filing manifests go to checkpoint dir, not a proper output folder

**Improvements:**
1. Add python-docx templates for common motions (Motion for Summary Disposition, Motion to Disqualify, etc.)
2. Add SCAO form auto-fill using extracted entity data
3. Add court-specific formatting rules (caption, margins, font per local rules)
4. Move filing output to `LitigationOS/04_FILINGS/` with proper naming
- File: `agents/convergence/f01_filing_factory.py` — complete rewrite needed for document generation

### F02: Brain Feeder
**Does Well:**
- Maps atoms to brain nuclei by type
- Confidence-weighted distribution
- Feed report generation

**Missing/Poor:**
- **BUG: Column index access wrong** (lines 52-54) — `atom[2]` gets `source_file_id`, not `confidence`
- Only maps to brains 1-30 out of 50
- No brain saturation detection (some brains may be overloaded)
- No feedback loop (brains don't signal what they need more of)

**Improvements:**
1. **Fix BUG-007:** Use dict-style access: `atom["confidence"]`, `atom["content"]`
2. Expand brain mapping to cover brains 31-50
3. Add brain saturation metrics (max atoms per brain)
- File: `agents/convergence/f02_brain_feeder.py` — lines 20-24, 52-54

### F03: Graph Builder
**Does Well:** Neo4j graph construction from atoms
**Missing:** No graph validation or consistency checks

### F04: MSC Architect
**Does Well:** Michigan Supreme Court packet preparation
**Missing:** No MSC-specific formatting rules

### F05: Test Runner
**Does Well:** Automated testing of pipeline outputs
**Missing:** No regression test suite for filing quality

### F06: Convergence Certifier
**Does Well:** Final validation before output
**Missing:** No court-rule compliance checklist

---

## CROSS-CUTTING IMPROVEMENTS

### 1. Improve Judicial Extraction Accuracy
- **Add OCR pipeline** for scanned court documents (currently ~30% of PDFs are scan-only)
- **Add handwriting detection** for judge's handwritten orders/annotations
- **Implement layout-aware extraction** using pymupdf's block-level API instead of full-page text
- **Add header/footer stripping** to remove court letterhead from classification

### 2. Improve Court Document Generation Quality
- **Template engine:** Use Jinja2 + python-docx for motion/brief templates
- **Citation formatting:** Auto-format MCL/MCR/case citations per Michigan Uniform Citation System
- **Table of Authorities:** Auto-generate from citation atoms
- **Exhibit indexing:** Auto-number and cross-reference exhibits
- **Local rule compliance:** 14th Circuit local rules for margins, fonts, page limits

### 3. System-Wide Improvements
- **Migrate from singleton SQLite to per-lane databases** with convergence merge
- **Add incremental processing** — don't re-process files that haven't changed
- **Implement the LLM Guardian** (`llm_guardian.py`) for permanent LLM reliability
- **Add provenance tracking** for audit trail from source file → atom → filing

---

*Generated by Copilot CLI comprehensive audit.*
