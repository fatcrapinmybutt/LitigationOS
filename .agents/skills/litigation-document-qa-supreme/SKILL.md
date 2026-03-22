---
name: litigation-document-qa-supreme
description: "APEX-OMEGA QA skill for legal document verification. Runs 15-gate pre-filing pipeline with zero-tolerance for failures. Validates party identity, citations, statistics, Bates continuity, MCR format compliance, and anti-hallucination sweeps. Use before ANY document is filed with any court."
category: discipline
version: "3.0.0-APEX-OMEGA"
triggers:
  - qa
  - pre-filing
  - verification
  - quality-check
  - anti-hallucination
  - document-review
  - filing-validation
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County; Michigan COA; Michigan Supreme Court; USDC WDMI"
case: Pigors v Watson
dependencies:
  - document-forge-supreme
  - litigation-supreme-commander
  - OMEGA-LITIGATION-SUPREME
metadata:
  model: opus
  forge_date: 2026-07-06
  tier: APEX-OMEGA
---

# LITIGATION-DOCUMENT-QA-SUPREME — APEX-OMEGA Quality Assurance Skill

> Zero-tolerance pre-filing quality assurance for ALL legal documents.
> This skill is the FINAL gate before any document reaches a court.
> Every document must pass ALL 15 gates — a single failure = NO-GO.

## When to Apply

Activate this skill:
- **Before filing** any document with any court (mandatory)
- **After document generation** by document-forge-supreme or litigation-supreme-commander
- **During document review** for accuracy and compliance
- **On demand** for quality audits of existing filings
- **Before e-filing** via MiFile, CM/ECF, or physical filing

---

## The 15-Gate Pre-Filing Pipeline

```
ENTRY: Document submitted for QA review
│
├── GATE 01: Party Identity Verification ─────────── CRITICAL
├── GATE 02: Anti-Hallucination Sweep ────────────── CRITICAL
├── GATE 03: Citation Verification ───────────────── CRITICAL
├── GATE 04: Statistic Traceability ──────────────── CRITICAL
├── GATE 05: Evidence Grounding Check ────────────── HIGH
├── GATE 06: Bates Continuity Audit ──────────────── HIGH
├── GATE 07: MCR Format Compliance ───────────────── HIGH
├── GATE 08: Caption & Case Number Verification ──── HIGH
├── GATE 09: Certificate of Service Validation ───── HIGH
├── GATE 10: Signature Block Verification ────────── MEDIUM
├── GATE 11: Proposed Order Check ────────────────── MEDIUM
├── GATE 12: Page/Word Count Compliance ──────────── MEDIUM
├── GATE 13: Exhibit Index Continuity ────────────── MEDIUM
├── GATE 14: Tone & Professionalism Audit ────────── LOW
├── GATE 15: Cross-Reference Consistency ─────────── LOW
│
└── VERDICT: ALL gates PASS → GO │ ANY CRITICAL gate FAIL → NO-GO
             ANY HIGH gate FAIL → CONDITIONAL (fix required before filing)
             MEDIUM/LOW failures → WARNING (note but proceed)
```

---

## GATE 01: Party Identity Verification (CRITICAL)

**Purpose:** Ensure every party name, title, and identification matches the verified identity table exactly.

### Verified Party Identity Table (CANONICAL — SINGLE SOURCE OF TRUTH)

| Role | Correct Name | Details | Common Hallucinations to Reject |
|------|-------------|---------|-------------------------------|
| **Plaintiff** | Andrew James Pigors | 1977 Whitehall Road, Lot 17, North Muskegon, MI 49445 · (231) 903-5690 · andrewjpigors@gmail.com | — |
| **Defendant** | Emily A. Watson | 2160 Garland Drive, Norton Shores, MI 49441 | "Emily Ann Watson", "Emily M. Watson", "Tiffany Watson" |
| **Child** | L.D.W. | Initials ONLY per MCR 8.119(H) — NEVER full name in filings | "Lincoln David Watson", any full name |
| **Judge** | Hon. Jenny L. McNeill | 14th Circuit Court, Family Division | "Amy McNeill", "Judge McNeil" (wrong spelling) |
| **Emily's Former Attorney** | Jennifer Barnes (P55406) | Barnes Law Firm PLLC, 880 Jefferson St Ste B, Muskegon, MI 49440 — **WITHDREW** | "Patricia Berry", "Jane Berry" |
| **FOC** | Pamela Rusco | 990 Terrace St, Muskegon, MI 49442 | — |
| **Ronald Berry** | Ronald Berry — NON-ATTORNEY | Emily's boyfriend/domestic partner. No bar number. No "Esq." | "Ron Berry Esq", "Ronald Berry, Attorney", any bar number for Berry |

### Gate 01 Verification Steps

```
For EVERY name appearing in the document:
  1. Check against verified party identity table above
  2. If name matches exactly → PASS
  3. If name is a known hallucination → FAIL (CRITICAL)
  4. If name is not in table → FLAG for manual verification
  5. Check child reference: must be "L.D.W." only, never full name
  6. Check Ronald Berry: must NOT have "Esq.", "Attorney", or bar number
  7. Check Jennifer Barnes: must be marked as WITHDREW if referenced
  8. Check judge name: must be "Jenny L. McNeill" (not "Amy", not "McNeil")
```

---

## GATE 02: Anti-Hallucination Sweep (CRITICAL)

**Purpose:** Detect and reject ALL known hallucination patterns from past sessions.

### Hallucination Blacklist (MUST CHECK EVERY DOCUMENT)

| Hallucination | Why It's Wrong | Sessions That Produced It |
|---|---|---|
| "Jane Berry" | Never existed — fabricated name | 60+ files contaminated |
| "Patricia Berry" | Never existed — fabricated name | Combined with fake bar number |
| "Patricia Berry (SBN P35878)" | Fake person + fake bar number | Could constitute perjury if filed |
| "91% alienation score" | Pseudo-scientific fabrication | Appeared in multiple analyses |
| "9 CPS investigations" | Unverified count — may be inflated | Must query DB for actual count |
| "Tiffany Watson" | Wrong name for defendant | Defendant is Emily A. Watson |
| "Lincoln David Watson" | Full name of child — PROHIBITED | Must use L.D.W. per MCR 8.119(H) |
| "Ron Berry Esq" | Berry is NOT an attorney | Could constitute misrepresentation |
| "Amy McNeill" | Wrong first name for judge | Judge is Jenny L. McNeill |
| "Emily Ann Watson" | Wrong middle name/format | Defendant is Emily A. Watson |
| "Emily M. Watson" | Wrong middle initial | Defendant is Emily A. Watson |
| "P35878" | Fabricated bar number for nonexistent attorney | Not a real SBN |

### Gate 02 Sweep Protocol

```
For the ENTIRE document text:
  1. Search for each blacklisted term (case-insensitive)
  2. If ANY blacklisted term found → FAIL (CRITICAL)
  3. Search for any bar number not in verified database:
     SELECT bar_number FROM attorneys WHERE bar_number = ?;
     If not found → FLAG for verification
  4. Search for any name not in verified party table → FLAG
  5. Search for percentage-based "scores" (e.g., "X% alienation"):
     If found and not traceable to a validated assessment tool → FAIL
  6. Search for specific investigation counts (e.g., "N investigations"):
     Must be traceable to: SELECT COUNT(*) FROM police_reports WHERE [conditions];
     If not traceable → FAIL
```

---

## GATE 03: Citation Verification (CRITICAL)

**Purpose:** Every case, statute, and rule cited must exist in the authority database or be independently verifiable.

### Gate 03 Verification Steps

```sql
-- For each case citation in the document:
SELECT case_name, citation, court, year, verified
FROM authority_master_index
WHERE citation LIKE '%[cited case]%'
OR case_name LIKE '%[cited case name]%';

-- For each MCR citation:
SELECT rule_number, rule_title, effective_date
FROM court_rules
WHERE rule_number = ?;

-- For each statute citation:
SELECT statute_number, title, current_version
FROM statutes
WHERE statute_number LIKE '%[cited statute]%';
```

```
For EVERY legal citation in the document:
  1. Query authority_master_index for the citation
  2. If found and verified = TRUE → PASS
  3. If found but verified = FALSE → FLAG for manual verification
  4. If NOT found → FAIL (CRITICAL) — citation may be hallucinated
  5. Check citation format: [Case Name], [Volume] [Reporter] [Page] ([Court] [Year])
  6. Check MCR format: MCR [Number] (e.g., MCR 2.119(A)(1))
  7. Check statute format: MCL [Section] (e.g., MCL 722.23)
  8. Check federal: [USC Title] § [Section] (e.g., 42 USC § 1983)
```

### Known Valid Citations (Quick Reference)

| Citation | Verified | Category |
|---|---|---|
| Sullivan v Gray, 117 Mich App 476 (1982) | ✅ | Recording consent |
| Haines v Kerner, 404 US 519 (1972) | ✅ | Pro se leniency |
| Turner v Rogers, 564 US 431 (2011) | ✅ | Contempt due process |
| MCR 2.003 | ✅ | Judge disqualification |
| MCR 2.113 | ✅ | Pleading format |
| MCR 2.119 | ✅ | Motion practice |
| MCR 3.606 | ✅ | Contempt |
| MCR 7.212 | ✅ | Appellate brief format |
| MCR 8.119(H) | ✅ | Minor child privacy |
| MCL 722.23 | ✅ | Best interest factors |
| MCL 750.539c | ✅ | One-party consent |
| 42 USC § 1983 | ✅ | Civil rights |

---

## GATE 04: Statistic Traceability (CRITICAL)

**Purpose:** Every number, count, percentage, or aggregate statistic must be traceable to a specific SQL query.

### Gate 04 Verification Steps

```
For EVERY numeric claim in the document:
  1. Identify the statistic (e.g., "305 interference incidents")
  2. Identify the source query that produced it:
     SELECT COUNT(*) FROM [table] WHERE [conditions];
  3. If traceable to a verified query → PASS
  4. If NOT traceable → FAIL (CRITICAL)
  5. Check for rounded/inflated numbers:
     - If document says "over 300" but query returns 287 → FLAG
     - Exact counts preferred over approximations
  6. Check for duplicate counting:
     - Verify query uses DISTINCT or dedup filters
     - Check is_duplicate = 0 in evidence_quotes queries
  7. Check for synthetic scores:
     - "91% alienation score" → FAIL (pseudo-scientific)
     - "HIGH severity" from DB field → PASS (categorical, not fabricated)
```

### Common Statistics That Must Be Verified

| Statistic Type | Required Query | Table |
|---|---|---|
| Evidence count | `SELECT COUNT(*) FROM evidence_quotes WHERE lane = ? AND is_duplicate = 0` | evidence_quotes |
| Timeline events | `SELECT COUNT(*) FROM master_evidence_timeline WHERE lane = ?` | master_evidence_timeline |
| Contradictions | `SELECT COUNT(*) FROM contradictions WHERE actor LIKE ?` | contradictions |
| Police reports | `SELECT COUNT(*) FROM police_reports WHERE [conditions]` | police_reports |
| Zero-charge investigations | `SELECT COUNT(*) FROM police_reports WHERE charges_filed = 0 AND [conditions]` | police_reports |
| Impeachment chains | `SELECT COUNT(*) FROM impeachment_chains WHERE target_actor LIKE ?` | impeachment_chains |
| Docket events | `SELECT COUNT(*) FROM docket_events WHERE case_number = ?` | docket_events |
| Judicial violations | `SELECT COUNT(*) FROM judicial_violations WHERE judge_name LIKE ?` | judicial_violations |

---

## GATE 05: Evidence Grounding Check (HIGH)

**Purpose:** Every factual assertion in the document must link to a specific evidence source.

```
For EVERY factual paragraph:
  1. Check for citation to exhibit, record, or evidence source
  2. Format: (Ex. [Bates#], [Source], p. [Page].) → PASS
  3. Citation to docket: (Docket Entry #[N], [Date]) → PASS
  4. Citation to transcript: (Tr. [Date], p. [Page], ll. [Lines]) → PASS
  5. No citation for factual claim → FAIL (HIGH)
  6. Legal argument paragraphs (rule statements) exempt from evidence citations
     but must have legal authority citations (see Gate 03)
```

---

## GATE 06: Bates Continuity Audit (HIGH)

**Purpose:** Bates numbers must be sequential, non-duplicated, and continuous across the exhibit set.

```
For the document's exhibit set:
  1. Extract all Bates numbers referenced in the document
  2. Check for gaps in sequence → FLAG
  3. Check for duplicates → FAIL (HIGH)
  4. Check format consistency (e.g., all "PIGORS-XXXX" or all "Ex. A-XXX")
  5. Cross-reference with exhibit index → all referenced Bates must appear in index
  6. Cross-reference with evidence_quotes.bates_number → verify Bates exist in DB
```

---

## GATE 07: MCR Format Compliance (HIGH)

**Purpose:** Document formatting matches the target court's requirements.

### Format Check by Court Type

```
Michigan State Court (Lanes A, B, D):
  □ 8.5" × 11" paper
  □ 1" margins minimum
  □ 12pt Times New Roman (or comparable serif)
  □ Double-spaced body text
  □ Consecutively numbered paragraphs
  □ Page numbers bottom center
  □ MCR 2.113 caption format

Federal Court (Lane C):
  □ FRCP + LCivR W.D. Michigan formatting
  □ 14pt body text (LCivR check)
  □ Electronic signature format: /s/ Andrew James Pigors

Court of Appeals (Lane F):
  □ MCR 7.212 brief format
  □ Table of Contents + Table of Authorities
  □ 50 pages or 16,000 words limit
  □ Required sections present

JTC (Lane E):
  □ Letter format (not motion format)
  □ Addressed to JTC, Lansing
  □ Specific Canon violations cited
```

---

## GATE 08: Caption & Case Number Verification (HIGH)

```
  1. Court name matches lane assignment
  2. Case number is correct for the lane:
     Lane A: 2024-001507-DC
     Lane B: 2025-002760-CZ
     Lane D: 2023-5907-PP
     Lane F: COA 366810
  3. Judge name (if applicable): Hon. Jenny L. McNeill
  4. Parties listed correctly:
     ANDREW JAMES PIGORS, Plaintiff
     vs.
     EMILY A. WATSON, Defendant
  5. Document title is descriptive and identifies filing party
```

---

## GATE 09: Certificate of Service Validation (HIGH)

```
  1. Certificate of Service present at end of document
  2. Service date filled in (not blank)
  3. Service method specified (first-class mail, hand delivery, e-filing, etc.)
  4. Recipient name and address correct:
     - Emily A. Watson: 2160 Garland Drive, Norton Shores, MI 49441
     - Jennifer Barnes (P55406): 880 Jefferson St Ste B, Muskegon, MI 49440
       (ONLY if still attorney of record — check withdrawal status)
  5. Signer identified as Andrew James Pigors
```

---

## GATE 10: Signature Block Verification (MEDIUM)

```
  1. Pro se signature block present
  2. Contains: full name, address, phone, email
  3. Date line present (may be blank for pre-filing draft)
  4. Format:
     Respectfully submitted,
     ______________________________
     Andrew James Pigors, Pro Se
     1977 Whitehall Road, Lot 17
     North Muskegon, MI 49445
     (231) 903-5690
     andrewjpigors@gmail.com
     Date: ____________
```

---

## GATE 11: Proposed Order Check (MEDIUM)

```
For motions (required) and other filings (if applicable):
  1. Proposed order attached as exhibit or separate document
  2. Proposed order caption matches motion caption
  3. Relief in proposed order matches relief requested in motion
  4. Signature line for judge: Hon. Jenny L. McNeill
  5. "IT IS SO ORDERED" language present
  6. Date and signature lines blank (for judge to sign)
```

---

## GATE 12: Page/Word Count Compliance (MEDIUM)

```
  Emergency motions: ≤ 10 pages (recommended)
  Standard motions: ≤ 20 pages (recommended)
  Trial briefs: ≤ 35 pages (recommended)
  COA briefs: ≤ 50 pages or ≤ 16,000 words (MCR 7.212(B))
  MSC applications: ≤ 50 pages
  §1983 complaints: No limit (but conciseness encouraged)
```

---

## GATE 13: Exhibit Index Continuity (MEDIUM)

```
  1. Exhibit index present (if exhibits attached)
  2. Every exhibit referenced in body text appears in index
  3. Every exhibit in index is referenced in body text
  4. Exhibit labels are sequential (A, B, C... or 1, 2, 3...)
  5. No orphan exhibits (in index but not referenced)
  6. No phantom references (in text but not in index)
```

---

## GATE 14: Tone & Professionalism Audit (LOW)

```
  Scan for:
  □ No personal attacks on opposing party, counsel, or judge
  □ No inflammatory or emotional language
  □ No ALL CAPS for emphasis (use bold or italics)
  □ No exclamation points in legal argument
  □ Respectful references to the Court ("this Honorable Court", "the Court")
  □ Measured, factual tone throughout
  □ No sarcasm or condescension
  □ Opposing party referred to by proper name/title
```

---

## GATE 15: Cross-Reference Consistency (LOW)

```
  1. Internal cross-references resolve (e.g., "See Section III.B" → section exists)
  2. Exhibit references match exhibit labels
  3. Footnotes reference existing sources
  4. Dates mentioned in one section are consistent with dates in other sections
  5. Party names are consistent throughout (no "Emily" in one place and "Watson" in another)
  6. Case number references are consistent throughout
```

---

## QA Output Report Format

After running all 15 gates, produce a structured report:

```yaml
qa_report:
  document: "[Document Title]"
  lane: "[A-F]"
  court: "[Target Court]"
  timestamp: "[ISO 8601]"
  overall_verdict: "GO | NO-GO | CONDITIONAL"

  gates:
    - gate: 01
      name: "Party Identity Verification"
      severity: CRITICAL
      result: "PASS | FAIL"
      findings: "[Specific issues if FAIL]"

    - gate: 02
      name: "Anti-Hallucination Sweep"
      severity: CRITICAL
      result: "PASS | FAIL"
      findings: "[Blacklisted terms found, if any]"

    # ... gates 03-15 ...

  summary:
    critical_failures: [count]
    high_failures: [count]
    medium_failures: [count]
    low_failures: [count]
    total_findings: [count]

  action_items:
    - "[Specific fix required for each failure]"

  anti_hallucination_sweep:
    blacklist_terms_checked: 12
    blacklist_terms_found: [list]
    unverified_names: [list]
    unverified_bar_numbers: [list]
    untraceable_statistics: [list]
    fabricated_scores: [list]
```

---

## Integration with Other APEX Skills

| Skill | Integration Point |
|---|---|
| document-forge-supreme v3.0 | QA runs AFTER document generation (D1-D6 modules) |
| litigation-supreme-commander v3.0 | QA validates SC1-SC4 module outputs |
| OMEGA-LITIGATION-SUPREME | QA is M8 (QA/Anti-Hallucination module) |
| filing-forge-master agent | Agent auto-invokes QA before filing assembly |
| pre-filing-qa agent | Agent delegates to this skill for comprehensive checks |

---

## Quick Invocation

```
"Run QA on this filing"           → Full 15-gate pipeline
"Check for hallucinations"        → Gates 01 + 02 only (fast sweep)
"Verify citations"                → Gate 03 only
"Check formatting"                → Gates 07 + 08 + 10 + 12 only
"Pre-filing review"               → Full 15-gate pipeline + GO/NO-GO verdict
"Anti-hallucination sweep"        → Gates 01 + 02 + 04 (identity + fabrication + stats)
```
