# LitigationOS — Master Repository Index

**Case:** Pigors v. Watson | **Updated:** March 22, 2026 | **Status:** APEX-OMEGA v3.0

---

## 🏗️ System Architecture

| Component | Description |
|-----------|-------------|
| [00_SYSTEM/](00_SYSTEM/) | Core system — pipeline, agents, brains, MCP server, tools, inference engine (56,637 files) |
| [11_CODE/litigationos/](11_CODE/litigationos/) | Desktop app — CustomTkinter GUI, 14 screens, 9 engines, pip-installable (24,471 files) |
| [.agents/](.agents/) | Agent fleet — 28 OMEGA v2.0 agents + 200+ skills (28,948 files) |
| [databases/](databases/) | Jurisdiction databases — 10 specialized DBs (30 files) |
| [mcp_servers/](mcp_servers/) | MCP servers — litigation-context, command-runner |
| [backend/](backend/) | Backend services and API (49 files) |
| [config/](config/) | Configuration files and settings (33 files) |

## 📁 Case Lane Directories

| Lane | Directory | Case | Files |
|------|-----------|------|-------|
| **A** Custody | [01_FILINGS/](01_FILINGS/) | 2024-001507-DC | 3,346 |
| **B** Housing | [02_TRIAL_14TH/](02_TRIAL_14TH/) | 2025-002760-CZ | 965 |
| **D** PPO | [06_EMERGENCY/](06_EMERGENCY/) | 2023-5907-PP | 69 |
| **E** Misconduct | [04_JTC_MCNEILL/](04_JTC_MCNEILL/) | Judge McNeill | 1,817 |
| **F** Appellate | [01_COA_366810/](01_COA_366810/) | COA 366810 | 116 |
| **C** Federal | [03_FEDERAL_1983/](03_FEDERAL_1983/) | §1983 USDC WDMI | 18 |

## ⚖️ Court-Ready Filings

| Directory | Description | Files |
|-----------|-------------|-------|
| [COURT_READY/](COURT_READY/) | Documents formatted and validated for court submission | 88 |
| [GENERATED_FILINGS/](GENERATED_FILINGS/) | Auto-generated legal documents from pipeline | 57 |
| [02_Court_Forms/](02_Court_Forms/) | Michigan SCAO court form templates | 47 |
| [04_COURT_FILINGS/](04_COURT_FILINGS/) | Filed court documents and docket entries | 23 |
| [05_BAR_BARNES/](05_BAR_BARNES/) | Attorney Grievance Commission — Barnes P55406 | 2 |

## 🔍 Evidence & Analysis

| Directory | Description | Files |
|-----------|-------------|-------|
| [03_EVIDENCE/](03_EVIDENCE/) | Evidence exhibits and supporting materials | 155 |
| [10_Exhibits/](10_Exhibits/) | Trial exhibits and courtroom materials | — |
| [10_IMAGES/](10_IMAGES/) | Images, photos, and visual exhibits | 12,479 |
| [05_ANALYSIS/](05_ANALYSIS/) | Legal analysis, research, and briefs | 1,651 |
| [07_PDF/](07_PDF/) | PDF documents and converted materials | 2,710 |

## 🧠 Databases (C:\ Drive)

| Database | Description | Size |
|----------|-------------|------|
| [litigation_context.db](litigation_context.db) | Central litigation database — 691+ tables | ~10 GB |
| [court_forms.db](court_forms.db) | Michigan SCAO court form intelligence — 39 forms | ~1 MB |
| [mcr_rules.db](mcr_rules.db) | Michigan Court Rules database | ~5 MB |
| [script_forge.db](script_forge.db) | Script management and execution tracking | ~1 MB |
| [script_vault.db](script_vault.db) | Script vault and version control | ~1 MB |

### Brain Databases (00_SYSTEM/brains/)

| Database | Description | Size |
|----------|-------------|------|
| chat_intelligence_brain.db | 89K+ records — ChatGPT, sessions, OCR extractions | 728 MB |
| interpretation_brain.db | Legal interpretation and analysis brain | 360 MB |
| narrative_brain.db | Case narrative and chronology brain | 273 MB |
| authority_brain.db | Legal authority and case law brain (728 authorities) | 70 MB |
| claims_brain.db | Claims and cause of action brain | 15 MB |
| entity_brain.db | Entity extraction and relationship brain | 11 MB |
| contradictions.db | 2,930 contradictions, 31 impeachment chains | 4 MB |

## 🛠️ Tools & Scripts

| Directory | Description | Files |
|-----------|-------------|-------|
| [07_TOOLS/](07_TOOLS/) | Utility scripts and processing tools | 1,270 |
| [08_SCRIPTS/](08_SCRIPTS/) | Automation scripts and batch processing | 1,142 |
| [13_TOOLS/](13_TOOLS/) | Large tools collection and utility library | 53,929 |

## 📚 Reference & Documentation

| Directory | Description | Files |
|-----------|-------------|-------|
| [00_START_HERE/](00_START_HERE/) | Entry point — quick start guides | 8 |
| [06_REFERENCE/](06_REFERENCE/) | Reference materials, legal authorities, precedents | 7,893 |
| [09_DATA/](09_DATA/) | Structured case data and datasets | 17,632 |
| [docs/](docs/) | Project documentation and guides | 130 |
| [12_ARCHIVES/](12_ARCHIVES/) | Archived and historical documents | 21 |

## 📄 Key Root Files

### Quick Reference
| File | Description |
|------|-------------|
| [README.md](README.md) | Project overview and getting started |
| [AGENTS.md](AGENTS.md) | Agent fleet instructions (Ω∞) |
| [copilot-instructions.md](copilot-instructions.md) | Copilot session instructions (v18.0) |
| [MASTER_SYSTEM_ARCHITECTURE.md](MASTER_SYSTEM_ARCHITECTURE.md) | Complete system architecture |
| [MASTER_PLAN.md](MASTER_PLAN.md) | Strategic litigation plan |
| [CHANGELOG.md](CHANGELOG.md) | Version history and changes |

### Case Intelligence
| File | Description |
|------|-------------|
| [EXECUTIVE_SUMMARY.txt](EXECUTIVE_SUMMARY.txt) | Opposition brief vulnerability overview |
| [OPPOSITION_BRIEF_ANALYSIS_SUMMARY.md](OPPOSITION_BRIEF_ANALYSIS_SUMMARY.md) | Comprehensive opposition framework |
| [QUICK_REFERENCE_F1-F10.md](QUICK_REFERENCE_F1-F10.md) | Filing package quick reference |
| [QUICK_REFERENCE_1983_FEDERAL.md](QUICK_REFERENCE_1983_FEDERAL.md) | Federal §1983 quick reference |
| [PPO_QUICK_REFERENCE.md](PPO_QUICK_REFERENCE.md) | PPO case quick reference |
| [COA_366810_QUICK_INDEX.md](COA_366810_QUICK_INDEX.md) | Court of Appeals quick index |
| [ROAfight.md](ROAfight.md) | Register of Actions analysis |

### Agent & Fleet
| File | Description |
|------|-------------|
| [FLEET_INVENTORY.md](FLEET_INVENTORY.md) | Complete agent fleet inventory |
| [FLEET_QUICK_REFERENCE.md](FLEET_QUICK_REFERENCE.md) | Fleet quick reference card |
| [SKILLS_COMPLETE_LIST.md](SKILLS_COMPLETE_LIST.md) | All skills catalog |
| [AGENT_INFRASTRUCTURE_SUMMARY.md](AGENT_INFRASTRUCTURE_SUMMARY.md) | Agent infrastructure overview |

### Database & Evidence
| File | Description |
|------|-------------|
| [DATABASE_SCHEMA_SUMMARY.md](DATABASE_SCHEMA_SUMMARY.md) | Database schema documentation |
| [DATABASE_QUICK_REFERENCE.txt](DATABASE_QUICK_REFERENCE.txt) | Quick DB query reference |
| [EVIDENCE_QUICK_REFERENCE.csv](EVIDENCE_QUICK_REFERENCE.csv) | Evidence inventory CSV |
| [UNIFIED_EVIDENCE_REPORT_NO_DUPLICATES.txt](UNIFIED_EVIDENCE_REPORT_NO_DUPLICATES.txt) | Deduplicated evidence report |

## 🔧 APEX-OMEGA v3.0 Skills (Current)

| Skill | Version | Modules | Size |
|-------|---------|---------|------|
| OMEGA-LITIGATION-SUPREME | v3.0 | 16 (M1-M16) | Supreme litigation composite |
| OMEGA-EVIDENCE | v3.0 | 12 (E1-E12) | Evidence pipeline + hybrid search |
| OMEGA-ARCHITECT | v3.0 | APEX schema | System architecture |
| litigation-federal-civil-rights | v3.0 | 6 (F1-F6) | §1983 + FRCP + WDMI |
| document-forge-supreme | v3.0 | 6 (D1-D6) | Document generation engine |
| litigation-supreme-commander | v3.0 | 4 (SC1-SC4) | Motion practice + DB-first |
| litigation-document-qa-supreme | v3.0 | 15-gate QA | Anti-hallucination pipeline |
| msc-bypass-application | v3.0 | 6 (MSC1-MSC6) | MSC original jurisdiction |
| multi-court-filing-coordinator | v3.0 | 7 (MC1-MC7) | Cross-court coordination |

---

*Total repository: ~170,000+ files across 35+ directories*
*Central DB: litigation_context.db (~10 GB, 691+ tables)*
*Brain DBs: ~1.5 GB total across 7 specialized databases*
*Git: origin/main — latest commit `c9eae7d67`*

---

## 📋 Legacy: Opposition Brief Analysis

### 📈 Complete Analysis Report
**File:** `ANALYSIS_COMPLETE_REPORT.txt`  
**Size:** 20.0 KB  
**Purpose:** Full detailed report with all findings  
**Read Time:** 30–45 minutes  
**Contains:**
- Execution summary
- Core findings (all 19 tables)
- Detailed vulnerability assessment
- Filing package inventory (F1-F10)
- Six-phase opposition strategy
- Rebuttal preparation checklist
- Next steps and timeline

### 🔬 Raw Database Findings
**File:** `DATABASE_FINDINGS_RAW.md`  
**Size:** 8.5 KB  
**Purpose:** Raw structured data from database  
**Read Time:** 15–20 minutes  
**Contains:**
- Table inventory with row counts
- 14 claim types detailed breakdown
- 364 authority chain audit specs
- 2,369 citation audit structure
- 14,716 evidence quote organization
- Critical vulnerabilities list
- Database query readiness

### 💾 Complete Raw Output
**File:** `db_results.txt`  
**Size:** 21.0 KB  
**Purpose:** Full unfiltered database exploration output  
**Read Time:** 20–30 minutes or reference as needed  
**Contains:**
- All 19 table schemas
- Row counts for all tables
- Sample data from each table
- Complete IRAC analysis text
- All distinct IDs from filings/vehicles
- Raw query results

### 🛠️ Reusable Query Script
**File:** `db_explore.py`  
**Size:** 5.0 KB  
**Purpose:** Python script for database queries  
**Usage:** `python db_explore.py` (from temp directory)  
**Contains:**
- All query templates used in analysis
- PRAGMA optimizations
- Error handling
- Full database exploration logic

---

## 🎯 Quick Navigation by Task

### I Need to Start a Rebuttal
1. **Read:** `EXECUTIVE_SUMMARY.txt` (5 min)
2. **Reference:** `QUICK_REFERENCE_F1-F10.md` → Find your target filing
3. **Detailed:** `OPPOSITION_BRIEF_ANALYSIS_SUMMARY.md` → Section 9 (Attack Vectors)

### I Need to Attack F7 (Discovery Abuse)
1. **Read:** `EXECUTIVE_SUMMARY.txt` → "Critical Weaknesses"
2. **Reference:** `QUICK_REFERENCE_F1-F10.md` → F7 section
3. **Strategy:** `ANALYSIS_COMPLETE_REPORT.txt` → "PHASE 1: QUICK WINS"
4. **Query:** Use `db_explore.py` to verify zero citations

### I Need to Challenge F4 (PPO Violation)
1. **Read:** `QUICK_REFERENCE_F1-F10.md` → F4 section
2. **Detailed:** `OPPOSITION_BRIEF_ANALYSIS_SUMMARY.md` → F4 entry
3. **Strategy:** `ANALYSIS_COMPLETE_REPORT.txt` → "PHASE 2: STRENGTH TARGETING"
4. **Evidence:** Query `db_results.txt` for police quotes

### I Need to Find Citation Vulnerabilities
1. **Reference:** `OPPOSITION_BRIEF_ANALYSIS_SUMMARY.md` → Section 4 (Citation Audit)
2. **Query:** Use `db_explore.py` → Citation audit queries
3. **Target:** `QUICK_REFERENCE_F1-F10.md` → Query Templates section

### I Need to Build Evidence Counter-Attack
1. **Reference:** `OPPOSITION_BRIEF_ANALYSIS_SUMMARY.md` → Section 5 (Evidence Repository)
2. **Strategy:** `ANALYSIS_COMPLETE_REPORT.txt` → "PHASE 5: EVIDENCE CONTRADICTION ATTACK"
3. **Query:** Use `db_explore.py` → Evidence contradiction queries
4. **Reference:** `QUICK_REFERENCE_F1-F10.md` → Query Templates

### I Need to Challenge Damages
1. **Reference:** `QUICK_REFERENCE_F1-F10.md` → F1/F3 sections
2. **Detailed:** `OPPOSITION_BRIEF_ANALYSIS_SUMMARY.md` → Section 7 (Damages Analysis)
3. **Strategy:** `ANALYSIS_COMPLETE_REPORT.txt` → "PHASE 6: DAMAGES REDUCTION"
4. **Query:** Use `db_explore.py` → Damages calculation queries

---

## 📊 Key Metrics at a Glance

| Metric | Value |
|--------|-------|
| Filing Packages | F1–F10 (10 total) |
| Database Tables | 19 total, 15 relevant |
| Evidence Quotes | 14,716 |
| Verified Citations | 2,369 |
| Authority Chains | 364 audit entries |
| IRAC Claims | 14 types |
| Critical Vulnerabilities | 5 identified |
| Highest Priority | F7 (0 citations) |
| Weakest Strength | F4 (5/10) |
| Damages Range | $0 – $1.65M |
| Violations Claimed | 4,810 total |

---

## 🔴 Critical Vulnerabilities (Priority Order)

1. **F7 (Discovery Abuse):** 0 verified citations ← **ATTACK FIRST**
2. **F4 (PPO Violation):** 5/10 strength + police contradiction
3. **F2 (Contempt):** Only 14 citations for entire claim
4. **F5/F6 (Judicial Disqualification):** 4,810 violations (quantity ≠ quality)
5. **F1/F3 (Custody/Damages):** 5.7x spread ($286K vs $1.65M)

---

## 📖 Reading Guide by Expertise Level

### Beginner (New to case)
1. `EXECUTIVE_SUMMARY.txt` (overview)
2. `QUICK_REFERENCE_F1-F10.md` (quick facts)
3. `OPPOSITION_BRIEF_ANALYSIS_SUMMARY.md` (detailed framework)

### Intermediate (Familiar with case)
1. `QUICK_REFERENCE_F1-F10.md` (targeted reference)
2. `ANALYSIS_COMPLETE_REPORT.txt` (strategic detail)
3. `db_results.txt` (raw data as needed)

### Advanced (Expert-level analysis)
1. `db_explore.py` (query database directly)
2. `DATABASE_FINDINGS_RAW.md` (technical specs)
3. `db_results.txt` (deep data analysis)
4. Original database: `litigation_context.db`

---

## 🔧 Database Access

**Database Location:**  
`C:\Users\andre\LitigationOS\litigation_context.db`

**Query Script:**  
`C:\Users\andre\LitigationOS\temp\db_explore.py`

**Usage:**
```bash
cd C:\Users\andre\LitigationOS\temp
python db_explore.py
```

**Direct Query (SQLite):**
```bash
sqlite3 "C:\Users\andre\LitigationOS\litigation_context.db"
```

---

## 📝 Document Purposes

| Document | Purpose | Audience | Read Time |
|----------|---------|----------|-----------|
| EXECUTIVE_SUMMARY | Overview & strategy | Decision makers | 5–10 min |
| OPPOSITION_BRIEF_ANALYSIS_SUMMARY | Framework & tactics | Legal team | 15–20 min |
| QUICK_REFERENCE | Specific filings | Drafting attorney | 10 min + |
| ANALYSIS_COMPLETE_REPORT | Full details | Research team | 30–45 min |
| DATABASE_FINDINGS_RAW | Technical specs | Database admin | 15–20 min |
| db_results | Raw data | Detailed review | 20–30 min |
| db_explore.py | Query tool | Technical users | N/A |

---

## ✅ Rebuttal Preparation Timeline

**IMMEDIATE (24 hours):**
- [ ] Read EXECUTIVE_SUMMARY
- [ ] Review QUICK_REFERENCE for target filings
- [ ] Identify 3–5 priority attack angles

**SHORT-TERM (3–5 days):**
- [ ] Query database for unverified citations
- [ ] Extract key evidence quotes
- [ ] Map authority chain vulnerabilities

**MEDIUM-TERM (1–2 weeks):**
- [ ] Draft F7 rebuttal (no-authority argument)
- [ ] Prepare F4 response (police determination)
- [ ] Develop damages challenge

**LONG-TERM (2–3 weeks):**
- [ ] Complete all rebuttal sections
- [ ] File opposition brief

---

## 🎯 Opposition Brief Strategy Summary

**Approach:** Multi-phase systematic attack based on database analysis

**Phase 1:** F7 lack-of-authority (highest confidence win)  
**Phase 2:** F4 police contradiction (moderate-high confidence)  
**Phase 3:** Dismantle authority chains (364 audit entries)  
**Phase 4:** Challenge citations (2,369 verification audit)  
**Phase 5:** Find conflicting evidence (14,716 quotes)  
**Phase 6:** Reduce damages (alternative calculation)

**Expected Outcome:** Strong, evidence-based opposition brief with specific targets

---

## 📞 Support & Questions

For database queries or technical questions:
- Use `db_explore.py` script
- Refer to query templates in `QUICK_REFERENCE_F1-F10.md`
- Consult `DATABASE_FINDINGS_RAW.md` for table specifications

For opposition strategy questions:
- Review `ANALYSIS_COMPLETE_REPORT.txt` → "Opposition Brief Attack Strategy"
- Check `OPPOSITION_BRIEF_ANALYSIS_SUMMARY.md` → Section 9

For specific filing analysis:
- Use `QUICK_REFERENCE_F1-F10.md` → Filing-specific sections

---

## 📄 File Organization

```
C:\Users\andre\LitigationOS\
├── litigation_context.db ..................... Main database
├── EXECUTIVE_SUMMARY.txt ..................... START HERE
├── OPPOSITION_BRIEF_ANALYSIS_SUMMARY.md ...... Main framework
├── QUICK_REFERENCE_F1-F10.md ................. Per-filing guide
└── ANALYSIS_COMPLETE_REPORT.txt .............. Full report

C:\Users\andre\LitigationOS\temp\
├── db_explore.py ............................ Query script
├── DATABASE_FINDINGS_RAW.md .................. Raw findings
└── db_results.txt ........................... Raw output
```

---

## ✅ Status

**Database Exploration:** Complete ✅  
**Analysis:** Complete ✅  
**Opposition Strategy:** Ready ✅  
**Documentation:** Complete ✅  

**Ready for:** Opposition brief drafting upon receipt of opponent's brief materials

---

**Last Updated:** 2026-03-21 03:41:34  
**Analysis Version:** 1.0  
**Database Version:** litigation_context.db (final)
