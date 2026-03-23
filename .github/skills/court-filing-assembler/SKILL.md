---
name: court-filing-assembler
description: Assembles complete Michigan court filing stacks (motion + brief + proposed order + CoS + exhibits) across all 5 forums (MSC, COA, 14th Circuit, USDC, JTC). Queries litigation_context.db for evidence, authority, and citations, validates against MCR/MCL, and outputs Pydantic-validated FilingPackage objects. Use when users request "assemble filing", "generate motion", "build filing stack", "court document", "filing package", or "prepare for filing".
---

# Court Filing Assembler

Assemble court-ready filing stacks from the LitigationOS database — evidence-grounded, citation-verified, MCR-compliant.

## Core Workflow

1. **Identify vehicle & lane**: Determine which filing vehicle and case lane (A–F)
2. **Gather authority**: Query `auth_rules`, `master_citations`, `authority_chains` for legal basis
3. **Gather evidence**: Query `evidence_quotes`, `extracted_harms`, `contradiction_map` for factual support
4. **Check deadlines**: Query `deadlines`, `omega_deadlines` for time-sensitive constraints
5. **Assemble IRAC structure**: Issue → Rule (pinpoint cite) → Application (case facts) → Conclusion
6. **Generate components**: Caption + Motion/Brief + Proposed Order + CoS + Exhibit Index
7. **Validate output**: Run through `litigation_contracts.py` Pydantic models
8. **Compliance check**: MCR formatting, service timing, mandatory forms, citation pinpoints
9. **Package & export**: Write to `04_COURT_FILINGS/` workflow directory

## Architecture — Filing Module Map

```
                    ┌─────────────────────────────┐
                    │   litigation_contracts.py    │  ← Pydantic v2 validation
                    │   (15 models, strict mode)   │
                    └──────────┬──────────────────┘
                               │ validates
    ┌──────────────────────────┼──────────────────────────┐
    │                          │                          │
┌───▼────────────┐  ┌─────────▼──────────┐  ┌───────────▼─────────┐
│ filing_packager │  │ filing_assembler   │  │ court_document_gen  │
│ (00_SYSTEM/)   │  │ (local_model/)     │  │ (pipeline/)         │
│ Orchestrates   │  │ IRAC + DB queries  │  │ Captions + blocks   │
└───┬────────────┘  └─────────┬──────────┘  └───────────┬─────────┘
    │                         │                         │
    │  ┌──────────────────────┼─────────────────┐       │
    │  │                      │                 │       │
┌───▼──▼─────────┐  ┌────────▼────────┐  ┌─────▼───────▼───────┐
│ filing_package  │  │ motion_generator│  │ litigation_context.db│
│ _generator.py   │  │ .py (skill)     │  │ (10.4 GB, 691 tables)│
│ (skill)         │  │ 8 motion types  │  │ WAL mode, FTS5      │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
```

### Module Responsibilities

| Module | Location | Purpose |
|--------|----------|---------|
| `filing_packager.py` | `00_SYSTEM/` | Top-level orchestrator — exhibit covers, Bates numbers, checklists, package assembly |
| `filing_assembler.py` | `00_SYSTEM/local_model/` | IRAC structure, DB-backed authority/evidence fetch, caption generation, compliance validation |
| `filing_package_generator.py` | `00_SYSTEM/local_model/skills/` | Auto-generate complete packages per lane — inventory, readiness scoring, all vehicle types |
| `motion_generator.py` | `00_SYSTEM/local_model/skills/` | IRAC-structured motions — 8 types (emergency PT, disqualification, contempt, etc.) |
| `court_document_generator.py` | `00_SYSTEM/pipeline/` | Low-level document blocks — captions, CoS, proposed orders, verification |
| `litigation_contracts.py` | `00_SYSTEM/pipeline/` | Pydantic v2 validation — 15 models with `extra="forbid"`, JSON Schema export |
| `guardrails.py` | `00_SYSTEM/pipeline/` | Pre-flight DB safety checks — schema validation, safe queries |

## Case Lanes & Forums

### Lane Selection (IRON LAW — never cross-contaminate)

| Lane | Subject | MEEK Signal | Case Numbers |
|------|---------|-------------|-------------|
| **A** | Custody (Watson) | `MEEK2` — custody, parenting, FOC, MCL 722, MCR 3.206/210 | 2024-001507-DC |
| **B** | Housing (Shady Oaks) | `MEEK1` — habitability, landlord, MCL 554, rent | 2025-002760-CZ |
| **C** | Convergence | Cross-lane coordination | Multi-lane |
| **D** | PPO / Protection Orders | `MEEK3` — PPO, contempt, MCL 600.2950, MCR 3.706-708 | 2023-5907-PP |
| **E** | Judicial Misconduct | `MEEK4` — bias, JTC, disqualification, MCR 2.003, canons | 2024-001507-DC |
| **F** | Appellate (COA/MSC) | `MEEK5` — appellate, MCR 7.x, standard of review | COA 366810 |

**Detection priority:** E → D → F → C → A → B. Use MEEK regex patterns from `config.py`.

### Forum Routing

| Forum | Vehicle Type | Key MCR | Filing Path |
|-------|-------------|---------|-------------|
| **MSC** | Superintending Control, Emergency App, Habeas, Mandamus | MCR 7.301-7.306 | `06_FILINGS/OMEGA_GENERATED/` |
| **COA** | Appeal Brief, Emergency Stay | MCR 7.201-7.215 | `06_FILINGS/OMEGA_GENERATED/` |
| **14th Circuit** | Motions, Briefs, Responses | MCR 2.113-2.119, 3.206-3.210 | `04_COURT_FILINGS/` |
| **USDC** | §1983 Complaint, Federal Motions | FRCP, 42 USC §1983 | `06_FILINGS/OMEGA_GENERATED/` |
| **JTC** | Formal Complaint | MCR 9.104-9.240 | `06_FILINGS/OMEGA_GENERATED/` |

## Database Query Patterns

### Safe DB Connection (MANDATORY)

```python
import sqlite3

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

def connect_filing_db():
    """Safe read-only connection for filing assembly."""
    conn = sqlite3.connect(str(DB_PATH), timeout=180)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=180000")
    conn.execute("PRAGMA query_only=ON")       # Read-only safety
    conn.execute("PRAGMA cache_size=-64000")    # 64MB cache
    return conn
```

**NEVER** use `get_robust_connection()` — it runs `PRAGMA integrity_check` on 10GB and hangs.

### Authority Lookup (Optimized UNION Query)

```python
def query_authority(conn, topic: str, limit: int = 20) -> list[dict]:
    """Fetch authority rules — FTS + LIKE in single query."""
    sql = """
        SELECT rule_id, title, rule_text, source, 1 as rank_group
        FROM auth_rules
        WHERE title LIKE ? OR rule_text LIKE ?
        UNION ALL
        SELECT rule_id, title, rule_text, source, 2 as rank_group
        FROM auth_rules
        WHERE rule_id IN (
            SELECT rule_id FROM auth_rules_fts WHERE auth_rules_fts MATCH ?
        )
        ORDER BY rank_group, rule_id
        LIMIT ?
    """
    like_term = f"%{topic}%"
    fts_term = topic.replace(" ", " OR ")
    rows = conn.execute(sql, (like_term, like_term, fts_term, limit)).fetchall()
    return [dict(r) for r in rows]
```

### Evidence Lookup (Speaker + Significance Indexed)

```python
def query_evidence(conn, topic: str, lane: str = None, limit: int = 30) -> list[dict]:
    """Fetch evidence quotes with optional lane filter."""
    sql = """
        SELECT quote_id, speaker, quote_text, source_file, significance, page_number
        FROM evidence_quotes
        WHERE quote_id IN (
            SELECT rowid FROM evidence_quotes_fts WHERE evidence_quotes_fts MATCH ?
        )
    """
    params = [topic.replace(" ", " OR ")]
    if lane:
        sql += " AND source_file LIKE ?"
        params.append(f"%lane_{lane}%")
    sql += " ORDER BY significance DESC LIMIT ?"
    params.append(limit)
    return [dict(r) for r in conn.execute(sql, params).fetchall()]
```

### Batch Citation Verification (2 Queries, Not 60-80)

```python
def verify_citations_batch(conn, citations: list[str]) -> dict:
    """Verify all citations in 2 queries instead of N sequential COUNTs."""
    # Pre-load all authority rules
    auth_rows = conn.execute(
        "SELECT rule_id, title FROM auth_rules"
    ).fetchall()
    auth_set = {r["title"].lower() for r in auth_rows}

    # Pre-load all rules_text
    rules_rows = conn.execute(
        "SELECT rule_id, citation FROM rules_text"
    ).fetchall()
    rules_set = {r["citation"].lower() for r in rules_rows}

    verified, unverified = [], []
    for cite in citations:
        if cite.lower() in auth_set or cite.lower() in rules_set:
            verified.append(cite)
        else:
            unverified.append(cite)

    return {"verified": verified, "unverified": unverified, "total": len(citations)}
```

### Key DB Tables for Filing Assembly

| Table | Rows | Use |
|-------|------|-----|
| `auth_rules` + `auth_rules_fts` | ~3.7M | Legal authority (MCR, MCL, case law) |
| `evidence_quotes` + `evidence_quotes_fts` | ~308K | Verbatim quotes with speaker/source |
| `master_citations` | ~3.7M | Citation index (MCL 1.3M, MCR 949K, case law 559K) |
| `authority_chains` | 44 | Complete chains per legal argument |
| `judicial_violations` | 1,127 | McNeill violations (377 critical) |
| `impeachment_items` | 15,171 | Contradiction/impeachment evidence |
| `extracted_harms` + FTS | 26,459 | Categorized harms by adversary |
| `filing_readiness` | 24 | Vehicle readiness scores |
| `omega_legal_actions` | 19 | Scored legal actions (10-axis) |
| `claims` + `claim_evidence_links` | 653/2,655 | Claims with evidence backing |
| `deadlines` | varies | Filing deadlines with `due_date_iso` |
| `gap_tickets` | varies | Missing elements tracker |
| `scao_court_forms` | 32 | Required SCAO forms |

## Filing Stack Components

Every filing stack consists of these components (varies by forum):

### 1. Caption Block (MCR 2.113)

```
STATE OF MICHIGAN
IN THE [COURT NAME]
[COUNTY OF MUSKEGON]

ANDREW J. PIGORS,                Case No. [NUMBER]
        Plaintiff,               Hon. [JUDGE]
    v.

EMILY A. WATSON,
        Defendant.
______________________________/
```

Generate via `court_document_generator.michigan_state_caption()` or `filing_assembler.generate_caption()`.

### 2. Motion Body (MCR 2.119)

- Title (centered, bold, caps)
- Introduction paragraph (jurisdictional basis)
- Statement of Facts (chronological, evidence-backed)
- Legal Argument (IRAC per issue)
- Relief Requested (specific, numbered)
- Verification (MCR 2.114)
- Signature block (Pro Se)

### 3. Brief in Support (MCR 2.119(A)(2))

- Index of Authorities (for appellate: MCR 7.212(B))
- Questions Presented
- Statement of Facts
- Argument sections (IRAC)
- Conclusion & Relief

### 4. Proposed Order (MCR 2.602)

```
STATE OF MICHIGAN ...
ORDER [GRANTING/DENYING] [MOTION TYPE]
At a session of said Court, held in [City], Michigan, on [date].
PRESENT: HONORABLE [Judge Name], Circuit Judge.
IT IS ORDERED that ...
_________________________
[Judge Name]
Circuit Court Judge
```

Generate via `court_document_generator.proposed_order_block()`.

### 5. Certificate of Service (MCR 2.107)

```
CERTIFICATE OF SERVICE
I hereby certify that on [date], I served a copy of the foregoing
[document name] upon [opposing party/counsel] by:
[ ] First-class U.S. Mail to: [address]
[ ] Personal service
[ ] MiFILE e-filing notification
    ________________________
    Andrew J. Pigors, Pro Se
    [address]
```

Generate via `court_document_generator.certificate_of_service()`.

### 6. Exhibit Index

Bates-numbered exhibits with foundation paragraphs. Generate via `filing_packager.generate_exhibit_cover_sheet()`.

### 7. Mandatory Forms (custody filings)

- **FOC 30** (UCCJEA Affidavit) — **REQUIRED** for ALL custody filings
- FOC 30A (UCCJEA Supplement)
- FOC 2 (Domestic Relations Judgment Info)
- FOC 88 (Friend of the Court Supplemental Info)
- MC 229 (Case Inventory Addendum)
- PCM 201 (Scheduling Conference)

## Validation with Pydantic Contracts

```python
from litigation_contracts import (
    MotionOutput, AppellateBrief, FilingPackage, FilingCaption,
    CertificateOfService, CitationAudit, IracCheck, FilingDocument,
    CaseLane, ComplianceResult
)

# Validate a motion
motion = MotionOutput(
    text=assembled_text,               # Must contain "STATE OF MICHIGAN"
    motion_type="emergency_restore_pt",
    title="EMERGENCY MOTION TO RESTORE PARENTING TIME",
    authority_count=len(authority_refs),
    evidence_count=len(evidence_refs),
    word_count=len(assembled_text.split()),
    citation_validation=CitationAudit(
        verified=verified_cites,
        unverified=unverified_cites,
        total=len(all_cites)
    ),
    irac_check=IracCheck(
        complete=True,
        present=["ISSUE", "RULE", "APPLICATION", "CONCLUSION"],
        missing=[]
    ),
)

# Validate a complete package
package = FilingPackage(
    package_type="circuit_motion_A1",
    court="14th Circuit Court, Muskegon County",
    case_number="2024-001507-DC",
    lane=CaseLane.A,
    generated=datetime.now().isoformat(),
    documents={
        "motion": FilingDocument(doc_type="motion", title=motion.title),
        "proposed_order": FilingDocument(doc_type="proposed_order", title="Proposed Order"),
        "cos": FilingDocument(doc_type="certificate_of_service", title="Certificate of Service"),
    },
    document_count=3,
)
```

### Readiness Check

```python
from litigation_contracts import FilingReadiness

readiness = FilingReadiness(
    vehicle_name="Emergency Motion to Restore Parenting Time",
    total_score=82,
    authority_score=90,
    evidence_score=85,
    procedural_score=70,
)
if readiness.ready_to_file:  # True if total_score >= 70
    print(f"✅ {readiness.vehicle_name} is ready (score: {readiness.total_score})")
```

## Complete Assembly Workflow

### Step-by-Step: Circuit Court Motion (Lane A)

```python
import sqlite3
from pathlib import Path

DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
OUT = Path(r"C:\Users\andre\LitigationOS\04_COURT_FILINGS\02_REVIEW")

# 1. Connect safely
conn = sqlite3.connect(str(DB), timeout=180)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=180000")
conn.execute("PRAGMA query_only=ON")
conn.execute("PRAGMA cache_size=-64000")

# 2. Check deadlines FIRST
deadlines = conn.execute("""
    SELECT * FROM deadlines
    WHERE due_date_iso >= date('now')
    ORDER BY due_date_iso LIMIT 10
""").fetchall()

# 3. Gather authority
authority = conn.execute("""
    SELECT rule_id, title, rule_text FROM auth_rules
    WHERE title LIKE '%parenting time%' OR title LIKE '%MCR 3.210%'
    UNION ALL
    SELECT rule_id, title, rule_text FROM auth_rules
    WHERE rule_id IN (
        SELECT rule_id FROM auth_rules_fts
        WHERE auth_rules_fts MATCH 'parenting OR custody OR visitation'
    )
    LIMIT 25
""").fetchall()

# 4. Gather evidence
evidence = conn.execute("""
    SELECT quote_id, speaker, quote_text, source_file, significance
    FROM evidence_quotes
    WHERE quote_id IN (
        SELECT rowid FROM evidence_quotes_fts
        WHERE evidence_quotes_fts MATCH 'parenting OR custody OR separation'
    )
    ORDER BY significance DESC
    LIMIT 30
""").fetchall()

# 5. Check for contradictions / impeachment
impeach = conn.execute("""
    SELECT * FROM impeachment_items
    WHERE target LIKE '%Watson%' OR target LIKE '%McNeill%'
    ORDER BY severity DESC LIMIT 20
""").fetchall()

# 6. Assemble IRAC sections
# ... (use filing_assembler.generate_irac_section() or build manually)

# 7. Generate caption + CoS + proposed order
# ... (use court_document_generator functions)

# 8. Validate with Pydantic
# ... (use litigation_contracts models)

# 9. Write to staging directory
output_path = OUT / "Emergency_Motion_Restore_PT.txt"
output_path.write_text(assembled_document, encoding="utf-8")

conn.close()
```

### Step-by-Step: MSC Filing (Lane F)

```python
# MSC filings require ADDITIONAL components:
# - 13 copies (per MSC rules)
# - Index of Authorities (MCR 7.212(B))
# - Appendix (MCR 7.212(C)) — relevant orders, transcript excerpts
# - Statement of Jurisdiction
# - Statement of Questions Presented
# - Filing fee ($375 or fee waiver motion)

# Use filing_package_generator.py for MSC packages:
# python -c "from skills.filing_package_generator import FilingPackageGenerator; ..."
# Or invoke via JSON-RPC: {"method": "filing_package", "params": {"vehicle": "MSC Combined"}}
```

### Step-by-Step: Federal §1983 (USDC)

```python
# Federal filings follow FRCP, not MCR:
# - Caption format differs (district court style)
# - Must establish subject-matter jurisdiction (28 USC §1331)
# - Must plead Monell for municipal liability
# - Must defeat qualified immunity at pleading stage
# - Use court_document_generator.federal_caption()
# - Validate with: frcp_compliance_check JSON-RPC method
```

## Pre-Filing Checklist (Automated)

Run before ANY filing:

```python
# Via JSON-RPC:
# {"method": "pre_filing_check", "params": {"vehicle": "Emergency Motion"}}
# {"method": "validate_forum_filing", "params": {"forum": "14th Circuit"}}

# Or run the pre-filing validator directly:
# python 00_SYSTEM/local_model/inference_engine.py --pipe
# >> {"method": "pre_filing_check", "params": {"vehicle_name": "..."}}
```

### Automated Checks

| Check | Rule | Fatal? |
|-------|------|--------|
| Caption format | MCR 2.113 | Yes |
| Service timing | MCR 2.119(C)(1) — 9 days + 3 mailed = 12 min | Yes |
| UCCJEA form | FOC 30 on ALL custody filings | Yes |
| Citation pinpoints | Every legal assertion must cite authority | Yes |
| IRAC completeness | All 4 sections present per argument | Warning |
| Signature block | Pro Se with address | Yes |
| Proposed order | Separate document per MCR 2.602 | Yes |
| CoS | MCR 2.107 format | Yes |
| Word/page limits | MCR 7.212(B) — 50 pages appellate brief | Warning |
| Redaction | No SSN/DOB/financial unless required | Yes |

## Procedural Traps (5 CRITICAL — Flag Always)

1. **Issue preservation** — MCR 2.517; *Carines v People* — if not raised below, argue plain error
2. **FOC 21-day window** — MCL 552.507(5); MCR 3.208 — administrative remedies must be exhausted
3. **Mandatory disclosures** — MCR 3.206(B); SCAO forms must be attached
4. **Service minimums** — MCR 2.119(C)(1) — 9 days + 3 if mailed = 12 days minimum before hearing
5. **Claim of appeal deadline** — MCR 7.204(A)(1) — 21 days, jurisdictional, CANNOT extend

## Output Artifacts

Every filing assembly produces:

| Artifact | Format | Location |
|----------|--------|----------|
| Motion/Brief text | `.txt` + `.docx` | `04_COURT_FILINGS/02_REVIEW/` |
| Proposed Order | `.txt` | Same directory |
| Certificate of Service | `.txt` | Same directory |
| Exhibit Index | `.txt` | Same directory |
| Pydantic validation log | `.json` | `04_COURT_FILINGS/02_REVIEW/_validation/` |
| Gap tickets (if any) | DB rows | `gap_tickets` table |
| Run manifest | `.json` | `04_COURT_FILINGS/02_REVIEW/_manifests/` |

### Filing Workflow Directories

```
04_COURT_FILINGS/
├── 01_DRAFTING/    ← First drafts, working copies
├── 02_REVIEW/      ← Assembled stacks awaiting human review
├── 03_FINAL/       ← Court-ready documents
│   └── COURT_READY/  ← Final export
├── 04_FILED/       ← After e-filing/submission
├── 05_SERVED/      ← After service complete
└── _TEMPLATES/     ← Reusable templates
```

## Best Practices

1. **Query DB before drafting** — never write a fact without `evidence_quotes` backing
2. **Verify every citation** — use batch verification, not sequential COUNT queries
3. **Check deadlines FIRST** — time-sensitive constraints may change which vehicle to file
4. **Lane discipline** — never mix custody evidence into housing filings (or vice versa)
5. **IRAC is mandatory** — every legal argument must follow Issue → Rule → Application → Conclusion
6. **Caption validation** — `MotionOutput` rejects text missing "STATE OF MICHIGAN" header
7. **Use FTS + LIKE UNION** — single query instead of two-round-trip fallback
8. **Read-only connections** — `PRAGMA query_only=ON` for filing assembly (never write from filing modules)
9. **Validate with Pydantic** — `litigation_contracts.py` catches hallucinated fields with `extra="forbid"`
10. **Adversarial thinking** — for every argument, add "Watson/Berry counter" and "rebuttal" sections

## Output Checklist

Every filing stack must include:

- [ ] Correct case lane identified (A–F)
- [ ] Forum and MCR compliance verified
- [ ] Caption block present with correct case number and judge
- [ ] IRAC structure complete for each legal argument
- [ ] All citations verified against `auth_rules` / `master_citations`
- [ ] All facts backed by `evidence_quotes` with provenance refs
- [ ] Proposed Order as separate document
- [ ] Certificate of Service with correct addresses
- [ ] Mandatory SCAO forms attached (FOC 30 for custody)
- [ ] Service timing computed (≥12 days before hearing if mailed)
- [ ] Pydantic validation passed (`MotionOutput` or `AppellateBrief`)
- [ ] Gap tickets created for any missing elements
- [ ] No PII/SSN/DOB unless court-required
- [ ] Output written to `04_COURT_FILINGS/02_REVIEW/` for human review
- [ ] Run manifest generated with SHA-256 hashes
