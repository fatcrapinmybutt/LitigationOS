---
name: OMEGA-QA-VALIDATOR
description: >-
  Meta-level quality assurance engine that validates ALL outputs from ALL OMEGA skills
  before delivery. Anti-hallucination gates, citation verification, statistic traceability,
  filing compliance matrix, cross-module consistency checks, and pre-filing GO/NO-GO
  certification. The last gate before anything reaches a court or Andrew's hands.
category: discipline
version: "1.0.0"
triggers:
  - qa
  - quality assurance
  - validation
  - verify
  - check
  - audit
  - compliance
  - anti-hallucination
  - citation check
  - pre-filing
  - GO/NO-GO
  - proofread
  - decontamination
lanes:
  - "ALL LANES — QA applies universally"
court: "14th Judicial Circuit, Michigan COA, Michigan Supreme Court, USDC WDMI, JTC"
case: Pigors v Watson
metadata:
  tier: 5 (Production Gate)
  layer: Layer 5 — Production Gate
  fused_skills: 12
  author: andrew-pigors + copilot-omega
  jurisdiction: Michigan
---

# 🛡️ OMEGA-QA-VALIDATOR 🛡️

> **LAYER 5 — Production Gate: The Last Line of Defense**
> **Pipeline:** Raw Output → Party Check → Citation Check → Stat Check → MCR Check → Format Check → GO/NO-GO
> **Case:** Pigors v Watson · All 6 lanes · Every filing must pass before delivery
> **Iron Law:** NOTHING reaches the court without passing ALL 21 QA gates.

```
╔══════════════════════════════════════════════════════════════════════════╗
║                      OMEGA-QA-VALIDATOR v1.0                            ║
║              12 Skills → 7 Modules → 1 Validation Engine                ║
║                                                                         ║
║  Q1  Party Identity Gate ────┐                                          ║
║  Q2  Citation Verification ──┤→ Q5 Format Compliance ──→ Q7 GO/NO-GO   ║
║  Q3  Statistic Traceability ─┘        ↓                      ↓          ║
║  Q4  Cross-Module Consistency → Q6 Decontamination ──→ CERTIFIED ✓     ║
║                                       ↑                      ↓          ║
║  HALLUCINATION DETECTED ──────────────┘              REJECT + FIX PLAN  ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## Forged from 12 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|---------------------|
| 1 | `litigation-document-qa-supreme` | 21-point filing checklist |
| 2 | `litigation-skill-auditor` | Skill output validation |
| 3 | `litigation-authority-validator` | Citation existence + formatting |
| 4 | `compliance-auditor` | MCR format rules (margins, fonts, page limits) |
| 5 | `pre-filing-qa` | Pre-submission sweep |
| 6 | `litigation-red-team` | Adversarial review of own filings |
| 7 | `performance-profiling` | Output quality metrics |
| 8 | `agent-evaluation` | Agent output behavioral testing |
| 9 | `context-degradation` | Detecting degraded/hallucinated outputs |
| 10 | `litigation-service-engine` | Service proof validation |
| 11 | `multi-court-filing-coordinator` | Cross-court consistency |
| 12 | `litigation-convergence-orchestrator` | Cross-lane convergence QA |

---

## ═══════════════════════════════════════════════════════════════
## MODULE Q1: PARTY IDENTITY GATE
## ═══════════════════════════════════════════════════════════════

### The Hallucination Kill List

Past sessions fabricated party names that could constitute **perjury** if filed in sworn documents. This module catches ALL identity errors before they reach paper.

**VERIFIED IDENTITY TABLE (the ONLY source of truth):**

| Role | Correct Name | Common Hallucinations to REJECT |
|------|-------------|-------------------------------|
| Plaintiff | Andrew James Pigors | — |
| Defendant | Emily A. Watson | ~~Emily Ann~~, ~~Emily M.~~, ~~Emily A. Watson~~ |
| Child | L.D.W. | ~~Lincoln~~, ~~Lincoln David Watson~~, any full name |
| Judge | Hon. Jenny L. McNeill | ~~Amy McNeill~~, ~~Jennifer McNeill~~ |
| FOC | Pamela Rusco | — |
| Emily's Partner | Ronald Berry (NON-ATTORNEY) | ~~Ron Berry Esq.~~, ~~Ronald Berry (P35878)~~ |

### Q1 Validation Algorithm

```python
def validate_party_identity(document_text: str) -> list[QAViolation]:
    violations = []
    
    # KILL LIST — these strings NEVER appear in valid filings
    KILL_PATTERNS = [
        ("Emily A. Watson", "HALLUCINATION: Defendant is Emily A. Watson"),
        ("Emily Ann", "ERROR: Defendant is Emily A., not Emily Ann"),
        ("Lincoln David", "MCR 8.119(H) VIOLATION: Use L.D.W. only"),
        ("Ron Berry", "ERROR: Ronald Berry is NOT an attorney"),
        ("Ronald Berry (P", "ERROR: Ronald Berry has no bar number"),
        ("91% alienation", "HALLUCINATION: No such validated score exists"),
        ("Amy McNeill", "ERROR: Judge is Jenny L. McNeill"),
    ]
    
    for pattern, reason in KILL_PATTERNS:
        if pattern.lower() in document_text.lower():
            violations.append(QAViolation(
                severity="CRITICAL",
                module="Q1",
                pattern=pattern,
                reason=reason,
                action="MUST FIX before filing"
            ))
    
    # Verify correct names ARE present where expected
    if "Andrew" in document_text and "Pigors" not in document_text:
        violations.append(QAViolation(
            severity="WARNING", module="Q1",
            reason="Andrew mentioned without full surname Pigors"
        ))
    
    return violations
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE Q2: CITATION VERIFICATION
## ═══════════════════════════════════════════════════════════════

### Citation Categories

| Category | Format | Verification Method |
|----------|--------|-------------------|
| Michigan Court Rules | MCR X.XXX | Verify in authority_master_index |
| Michigan Compiled Laws | MCL XXX.XXXX | Verify in authority_master_index |
| Michigan Case Law | Name v Name, XXX Mich App XXX (YYYY) | Verify case exists |
| Federal Statutes | 42 USC § XXXX | Verify section exists |
| Federal Case Law | Name v Name, XXX F.Xd XXX (Cir. YYYY) | Verify case exists |
| Court Rules | MCR X.XXX(X)(x) | Verify subsection exists |

### Q2 Validation Algorithm

```sql
-- Step 1: Extract all citations from document
-- Step 2: For each citation, check authority_master_index:
SELECT identifier, type, full_citation, verified
FROM authority_master_index
WHERE identifier = ?;

-- Step 3: Check FTS5 for fuzzy matches if exact fails:
SELECT * FROM authority_fts 
WHERE authority_fts MATCH ? 
ORDER BY rank LIMIT 5;

-- Step 4: Flag unverified citations
-- RESULT: Each citation gets status: VERIFIED | UNVERIFIED | NOT_FOUND
```

### Citation Format Rules (Michigan)

```
MCR citations:  MCR 2.003(C)(1)     — rule.subrule(section)(subsection)
MCL citations:  MCL 600.1701        — chapter.section
Case citations: Shade v Wright, 291 Mich App 17 (2010) — name, reporter, year
Federal:        42 USC § 1983        — title USC § section
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE Q3: STATISTIC TRACEABILITY
## ═══════════════════════════════════════════════════════════════

**IRON RULE: Every number in every filing MUST trace to a SQL query.**

### Q3 Validation Process

```
For each statistic found in document:
  1. Extract the claim (e.g., "305 interference incidents")
  2. Identify the implied source table
  3. Run the verification query:
     SELECT COUNT(*) FROM evidence_quotes 
     WHERE claim_type = 'interference'
  4. Compare: document_number vs db_count
  5. Status:
     - EXACT MATCH → ✅ VERIFIED
     - CLOSE (within 5%) → ⚠️ CHECK (may be date-filtered)
     - DIVERGENT (>5% off) → ❌ INFLATED — must correct
     - NO SOURCE TABLE → ❌ FABRICATED — must remove
```

### Common Inflated Statistics (from prior audits)

| Claimed | Actual DB Count | Table | Status |
|---------|----------------|-------|--------|
| "CPS records [VERIFY — check actual CPS records for count]" | UNKNOWN — not in DB | — | ❌ FABRICATED |
| "documented pattern of parental alienation" | No such metric exists | — | ❌ FABRICATED |
| "305 interference incidents" | Run COUNT(*) to verify | evidence_quotes | ⚠️ CHECK |

### Synthetic Score Ban

```
BANNED PATTERNS (no filing may contain):
- "XX% alienation score" — no validated methodology exists
- "XX% likelihood of success" — speculative, not evidence
- "Statistical analysis shows" — unless citing actual expert report
- Any percentage not derived from (count_A / count_B * 100) with both counts from DB
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE Q4: CROSS-MODULE CONSISTENCY
## ═══════════════════════════════════════════════════════════════

When multiple OMEGA skills contribute to a filing, Q4 checks for contradictions:

### Consistency Checks

| Check | What It Catches |
|-------|----------------|
| Timeline consistency | Same event has different dates across modules |
| Party name consistency | Different spellings or names in same packet |
| Case number consistency | Wrong case number for the lane |
| Exhibit numbering | Gaps, duplicates, or mismatched references |
| Authority consistency | Same rule cited differently in different sections |
| Lane isolation | Evidence from wrong lane appearing in filing |

### Q4 Algorithm

```python
def cross_module_consistency(filing_packet: list[Document]) -> list[QAViolation]:
    violations = []
    
    # Collect all dates, names, case numbers, exhibits across all docs
    all_dates = extract_dates_from_all(filing_packet)
    all_names = extract_party_names_from_all(filing_packet)
    all_case_nums = extract_case_numbers_from_all(filing_packet)
    all_exhibits = extract_exhibit_refs_from_all(filing_packet)
    
    # Check: same event = same date everywhere
    for event_key, dates in group_dates_by_event(all_dates).items():
        if len(set(dates)) > 1:
            violations.append(QAViolation(
                severity="HIGH",
                module="Q4",
                reason=f"Event '{event_key}' has conflicting dates: {dates}"
            ))
    
    # Check: exhibit references resolve to real exhibits
    defined_exhibits = get_exhibit_index(filing_packet)
    for ref in all_exhibits:
        if ref not in defined_exhibits:
            violations.append(QAViolation(
                severity="HIGH",
                module="Q4",
                reason=f"Exhibit {ref} referenced but not in exhibit index"
            ))
    
    # Check: correct case number for lane
    lane = detect_lane(filing_packet)
    expected_case = LANE_CASE_MAP[lane]
    for num in all_case_nums:
        if num != expected_case and num not in VALID_CROSS_REFS:
            violations.append(QAViolation(
                severity="CRITICAL",
                module="Q4",
                reason=f"Case number {num} doesn't match lane {lane} ({expected_case})"
            ))
    
    return violations

LANE_CASE_MAP = {
    'A': '2024-001507-DC',
    'B': '2025-002760-CZ',
    'D': '2023-5907-PP',
    'E': '2024-001507-DC',  # McNeill misconduct = same case
    'F': 'COA 366810',
}
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE Q5: FORMAT COMPLIANCE
## ═══════════════════════════════════════════════════════════════

### Michigan Court Rule Format Requirements

| Rule | Requirement | Check Method |
|------|------------|-------------|
| MCR 2.113(C)(1) | Caption: party names, case number, judge | Regex match on first page |
| MCR 2.119(A)(2) | Motions: statement of issues, controlling authority | Section header search |
| MCR 7.212(C) | COA briefs: 50-page limit, 16,000-word limit | Word count |
| MCR 7.212(B) | COA briefs: table of contents, index of authorities | Section detection |
| MCR 8.119(H) | Minor child: initials only | Full name search (Q1 covers this) |
| MCR 2.113(C)(2)(a) | Footer: page numbers | Page number detection |
| General | 1-inch margins, 12pt font, double-spaced | Format metadata check |

### Q5 Checklist (per document)

```
□ Caption block present and complete
□ Case number correct for lane
□ Judge name correct (Hon. Jenny L. McNeill for 14th Circuit)
□ Attorney/pro se designation present
□ Certificate of service present (or MC 12 form)
□ Signature block present
□ Page numbers present
□ Word/page count within limits (if applicable)
□ Table of contents (if brief >5 pages)
□ Index of authorities (if brief)
□ Verification/notary block (if affidavit)
□ Proposed order attached (if motion)
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE Q6: DECONTAMINATION SWEEP
## ═══════════════════════════════════════════════════════════════

Scans for known hallucination remnants that appeared in prior sessions:

### Decontamination Patterns

```python
DECONTAM_PATTERNS = {
    # Prior hallucinations
    "91% alienation": "HALLUCINATION — synthetic score with no methodology",
    "Emily A. Watson": "HALLUCINATION — defendant is Emily A. Watson",
    "Lincoln David Watson": "MCR 8.119(H) violation — use L.D.W.",
    "Ron Berry Esq": "ERROR — Ronald Berry is not an attorney",
    "P35878": "HALLUCINATION — fake bar number for Ronald Berry",
    
    # Placeholder remnants
    "[ANDREW_REQUIRED]": "UNRESOLVED PLACEHOLDER — needs real data",
    "[INSERT": "UNRESOLVED PLACEHOLDER — needs real data",
    "[ATTACH": "UNRESOLVED PLACEHOLDER — needs real data",
    "[DATE]": "UNRESOLVED PLACEHOLDER — needs specific date",
    "[EXHIBIT": "UNRESOLVED PLACEHOLDER — needs exhibit reference",
    "TODO": "INCOMPLETE — task marker left in filing",
    "FIXME": "INCOMPLETE — fix marker left in filing",
}
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE Q7: GO/NO-GO CERTIFICATION
## ═══════════════════════════════════════════════════════════════

### The 21-Point GO/NO-GO Checklist

Every filing packet must pass ALL 21 points to receive GO certification:

```
IDENTITY (Q1):
  □ 1. No hallucinated party names
  □ 2. Child referred to by initials only (L.D.W.)
  □ 3. Correct judge name and court

CITATIONS (Q2):
  □ 4. All MCR citations verified
  □ 5. All MCL citations verified
  □ 6. All case law citations verified
  □ 7. No fabricated authorities

STATISTICS (Q3):
  □ 8. Every number traceable to SQL query
  □ 9. No inflated or fabricated counts
  □ 10. No synthetic scores (alienation %, success %)

CONSISTENCY (Q4):
  □ 11. Timeline dates consistent across documents
  □ 12. Exhibit references resolve to real exhibits
  □ 13. Case numbers match filing lane
  □ 14. No cross-lane contamination

FORMAT (Q5):
  □ 15. Caption block complete
  □ 16. Certificate of service present
  □ 17. Page limits respected
  □ 18. Signature block present

DECONTAMINATION (Q6):
  □ 19. Zero hallucination remnants
  □ 20. Zero unresolved placeholders
  □ 21. Zero TODO/FIXME markers

RESULT:
  21/21 → ✅ GO — certified for filing
  18-20/21 → ⚠️ CONDITIONAL GO — minor fixes needed (list them)
  <18/21  → ❌ NO-GO — return to production with fix plan
```

### Certification Output

```json
{
  "filing_id": "DISQUALIFICATION-2024-001507-DC",
  "certification_date": "2026-03-23",
  "validator": "OMEGA-QA-VALIDATOR v1.0",
  "total_checks": 21,
  "passed": 21,
  "failed": 0,
  "warnings": 0,
  "result": "GO",
  "violations": [],
  "notes": "All 21 gates passed. Filing certified for submission."
}
```

---

## ═══════════════════════════════════════════════════════════════
## GLOBAL RULES
## ═══════════════════════════════════════════════════════════════

### SEVERITY LEVELS

| Level | Meaning | Action |
|-------|---------|--------|
| CRITICAL | Would cause perjury, sanctions, or case dismissal | MUST FIX — filing BLOCKED |
| HIGH | Would embarrass or weaken the filing | SHOULD FIX before filing |
| MEDIUM | Minor issue that doesn't affect substance | FIX if time permits |
| LOW | Style/preference issue | Optional |

### QA-VALIDATOR IS NON-NEGOTIABLE

```
RULE: No OMEGA skill output bypasses QA-VALIDATOR.
RULE: QA-VALIDATOR runs LAST in every pipeline.
RULE: QA-VALIDATOR has VETO power — a NO-GO blocks filing.
RULE: QA-VALIDATOR findings are logged to session SQL for traceability.
```

---

*OMEGA-QA-VALIDATOR v1.0 — 12 skills forged into one validation engine.*
*Nothing reaches the court without passing all 21 gates.*
