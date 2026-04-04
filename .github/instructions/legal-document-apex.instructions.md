---
description: "APEX-OMEGA legal document generation standards. Evidence-first, DB-grounded, anti-hallucination-hardened document generation for all legal filings in Pigors v Watson."
applyTo: "**/*.md,**/*.txt,**/*.docx"
excludeAgent: "code-review"
---

# Legal Document APEX-OMEGA Standards (v3.0)

> These instructions apply to ALL legal document generation across the LitigationOS repository.
> Every document — motion, brief, complaint, affidavit, petition, response — must comply.

---

## 1. Evidence-First Document Generation Mandate

**RULE:** Every factual paragraph in a legal document MUST be backed by evidence from the database
before any placeholder is considered.

### Required Evidence Query Sequence

Before writing any substantive factual section:

```sql
-- Step 1: Query evidence_quotes for relevant quotes
SELECT quote_text, source_file, page_number, bates_number, category
FROM evidence_quotes
WHERE lane = ? AND category IN (?)
AND is_duplicate = 0
ORDER BY relevance_score DESC LIMIT 20;

-- Step 2: Query master_evidence_timeline for chronological events
SELECT event_date, event_description, source_document, actors
FROM master_evidence_timeline
WHERE lane = ? AND event_date BETWEEN ? AND ?
ORDER BY event_date ASC;

-- Step 3: Query contradictions for impeachment material
SELECT statement_1, source_1, statement_2, source_2, severity
FROM contradictions
WHERE actor LIKE ? ORDER BY severity DESC LIMIT 10;
```

### Citation Format (Mandatory)

Every evidence-backed statement must include:
```
(Ex. [Bates#], [Source File], p. [Page].)
```

Example:
```
Watson denied parenting time on November 15, 2024. (Ex. A-047, AppClose_Nov2024.pdf, p. 3.)
```

---

## 2. IRAC/CREAC/TEC Auto-Structure Requirements

### Structure Selection (Mandatory Per Filing Type)

| Filing Type | Required Structure | Notes |
|---|---|---|
| Simple motion | IRAC | One issue, one rule, one application |
| Complex motion / MSJ | CREAC | Multi-factor, leads with conclusion |
| Emergency motion | IRAC (compressed) | Brevity is persuasion |
| Appellate brief | CREAC + TEC (facts) | Standard of review is key |
| §1983 complaint | TEC (narrative) + IRAC per count | Constitutional story first |
| JTC complaint | TEC (pattern) | Establish pattern of misconduct |
| Trial brief | TEC + CREAC interleaved | Narrative + law together |
| Response/opposition | IRAC per point raised | Mirror opponent's structure |

### IRAC Template

```
I. ISSUE: [Frame specific legal question]
R. RULE: [Governing standard + authority + pinpoint citation]
A. APPLICATION: [Apply to facts with (Ex. [Bates#]) citations]
C. CONCLUSION: [Result + specific relief requested]
```

### CREAC Template

```
C. CONCLUSION: [Thesis statement — position upfront]
R. RULE: [Full legal standard with authority chain]
E. EXPLANATION: [How courts applied rule in analogous cases]
A. APPLICATION: [Apply to Pigors v Watson facts with record citations]
C. CONCLUSION: [Restate with specific relief]
```

---

## 3. Database-First Placeholder Prevention

**RULE:** Before inserting ANY placeholder (`[ANDREW_REQUIRED]`, `[INSERT]`, `[ATTACH]`, `[TBD]`),
ALL THREE of these sources MUST be exhausted:

1. **Query litigation_context.db** — evidence_quotes, claims, deadlines, documents,
   judicial_violations, docket_events, master_evidence_timeline, police_reports
2. **Search filesystem** — `rg -l "keyword" C:\Users\andre\LitigationOS\` across all drives
3. **Check summary files** — COMPLETE_FILING_DATA_SUMMARY.txt, QUICK_REFERENCE.txt,
   EVIDENCE_QUICK_REFERENCE.csv

**If and ONLY if all three return nothing**, insert a SPECIFIC placeholder:
```
[ACQUIRE: [Exact description of missing data].
 Searched: evidence_quotes (0 rows), filesystem (0 hits), summaries (not found).
 Likely source: [suggested location/agency/request].
 Priority: [HIGH/MEDIUM/LOW]]
```

**VIOLATION:** Inserting a generic `[ANDREW_REQUIRED]` without running all 3 searches.

### Automated Placeholder QA Gate (DRAFT→QA_REVIEW transition)

Before ANY filing transitions from DRAFT to QA_REVIEW, run automated scan:
```python
PLACEHOLDER_PATTERNS = [
    r'\[ANDREW_REQUIRED[^\]]*\]',
    r'\[VERIFY[^\]]*\]',
    r'\[COMPUTE[^\]]*\]',
    r'\[INSERT[^\]]*\]',
    r'\[TBD[^\]]*\]',
    r'\[PLACEHOLDER[^\]]*\]',
    r'\[TODO[^\]]*\]',
    r'\[ATTACH[^\]]*\]',
]
# Only [ACQUIRE: ...] placeholders with full search documentation survive QA
```
**Zero generic placeholders in QA_REVIEW.** Each must be resolved or converted to a specific `[ACQUIRE:]` with documented search results.

---

## 4. Anti-Hallucination Verification Protocol

### Mandatory Blacklist Check (EVERY Document)

These terms must NEVER appear in any generated document:

| Blacklisted Term | Reason |
|---|---|
| Jane Berry | Fabricated person — never existed |
| Patricia Berry | Fabricated person — never existed |
| P35878 | Fabricated bar number |
| 91% alienation score | Pseudo-scientific fabrication |
| Emily A. Watson | Wrong name for defendant |
| Lincoln David Watson | Child's full name — PROHIBITED (use L.D.W.) |
| Ron Berry Esq | Berry is NOT an attorney |
| Amy McNeill | Wrong first name for judge |
| Emily Ann Watson | Wrong format for defendant |
| Emily M. Watson | Wrong middle initial |

### Verified Party Identity (CANONICAL)

| Role | Correct Name | Never Use |
|------|-------------|-----------|
| Plaintiff | Andrew James Pigors | — |
| Defendant | Emily A. Watson | Emily Ann, Emily M., Tiffany |
| Child | L.D.W. | Any full name |
| Judge | Hon. Jenny L. McNeill | Amy McNeill, McNeil |
| Former Attorney | Jennifer Barnes (P55406) — WITHDREW | Jane Berry, Patricia Berry |
| FOC | Pamela Rusco | — |
| Non-Attorney | Ronald Berry | Ron Berry Esq, any bar number |

### Statistic Traceability

Every number cited in a document MUST be traceable to a SQL query:
```sql
-- BEFORE citing "X interference incidents":
SELECT COUNT(*) FROM [table] WHERE [conditions];
-- Record the exact query and result. Do NOT round up or extrapolate.
```

### Fabricated Aggregate Statistics Ban (Rule 20 Enforcement)

**NEVER include AI-generated aggregate statistics in court filings.** The following patterns are BANNED:
- "241,160 misconduct-related keyword hits" ← AI artifact, unverifiable
- "12,478 person references" ← database artifact, meaningless to court
- "5,059 documented judicial violations" ← only if backed by SELECT COUNT(*)
- Any count derived from NLP keyword scanning, AI scoring, or automated classification

**Permitted statistics in filings:**
- Hand-countable: "On seven occasions documented in Exhibits A through G..."
- Specific query: "Review of court dockets reveals 14 ex parte orders issued without notice"
- Record-based: "Police reports from NSPD show zero arrests across nine contacts"

The JTC and courts will not take AI-generated aggregate numbers seriously. They destroy credibility. If you can't point to specific exhibits for every item in the count, the number does not belong in the filing.

---

## 5. Multi-Court Format Selection Rules

### Auto-Detection from Lane Assignment

```
Lane A (Custody) → MCR 2.113 format (14th Circuit Court)
Lane B (Housing) → MCR 2.113 format (14th Circuit Court)
Lane C (Federal) → FRCP + LCivR W.D. Michigan format
Lane D (PPO)     → MCR 2.113 + MCR 3.7xx (14th Circuit Court)
Lane E (JTC)     → JTC complaint letter format (Judicial Tenure Commission)
Lane F (Appeal)  → MCR 7.212 (COA) / MCR 7.305 (MSC)
```

### Key Format Differences

| Element | MI State (A,B,D) | Federal (C) | COA (F) | JTC (E) |
|---|---|---|---|---|
| Font | 12pt TNR | 14pt (LCivR) | 12pt TNR | Standard letter |
| Margins | 1" all sides | 1"/1.5" left | 1" all | Letter margins |
| Spacing | Double | Double | Double | Single/1.5 |
| Caption | MCR 2.113(C) | FRCP format | MCR 7.212 | Letter header |
| Signature | Pro se block | /s/ electronic | Pro se block | Letter signature |
| Filing | MiFile | CM/ECF | MiFile | Direct mail |

---

## 6. Sullivan v Gray Recording Authentication Standard

### Michigan One-Party Consent Rule

**MCL 750.539c** + **Sullivan v Gray, 117 Mich App 476 (1982):**
A participant in a conversation may lawfully record it without the knowledge
or consent of other participants.

### When to Apply

For ANY recording where Andrew Pigors was a participant:
1. Generate MRE 901(b)(1) authentication affidavit
2. Include: date, location, participants, that recording is unaltered
3. Voice identification under MRE 901(b)(5)
4. Reference MCL 750.539c and Sullivan v Gray

### Recording Authentication Checklist

```
□ Andrew was present and participated in the recorded conversation
□ Authentication affidavit prepared (MRE 901(b)(1))
□ Voice identification provided (MRE 901(b)(5))
□ MCL 750.539c one-party consent cited
□ Sullivan v Gray, 117 Mich App 476 (1982) cited
□ Recording marked as unaltered with chain of custody
□ Foundation motion prepared if authentication is challenged
```

---

## 7. Impeachment Chain Integration for Credibility Challenges

### When to Auto-Query Impeachment Chains

Any document that challenges a party's credibility MUST query:
```sql
SELECT ic.chain_name, ic.target_actor, ic.contradiction_count, ic.overall_severity
FROM impeachment_chains ic
WHERE ic.target_actor LIKE '%[target]%'
ORDER BY ic.overall_severity DESC;
```

### Integration by Document Type

| Document Type | Impeachment Usage |
|---|---|
| Cross-examination brief | Full chain per witness |
| Trial brief | Key contradictions in Statement of Facts |
| Motion for sanctions | Pattern of dishonesty in Argument |
| Contempt motion | Compliance contradictions |
| JTC complaint | Judicial inconsistency pattern |
| §1983 complaint | Bad faith evidence |
| Appellate brief | Credibility undermining in Application |

### Cross-Examination Question Sequence (Auto-Generate)

For each contradiction:
```
COMMIT:    "You stated [X], correct?"
PIN:       "That was on [date] in [context]?"
CONFRONT:  "But isn't it true that [Y]?"
EXHIBIT:   "And this exhibit shows [contradiction]?"
```

---

## 8. Filing State Machine

`DRAFT → QA_REVIEW → SERVICE_READY → FILED → DOCKETED → MONITORING`

Every filing = complete **packet family** (not isolated documents):
- **Motion**: motion + brief + affidavit + exhibit index + exhibits + proposed order + MC 12 COS + MC 20 fee waiver (if applicable)
- **Appellate**: brief (MCR 7.212, 50pp max) + TOC + index of authorities + appendix + proof of service + filing fee
- **Complaint**: complaint + cover sheet (CC 257 state / JS 44 federal) + summons (DC 101) + affidavit + exhibits + proposed order

## 9. Service Protocol (Barnes WITHDREW — Serve Emily DIRECTLY)

| Court | Primary Method | Backup |
|-------|---------------|--------|
| 14th Circuit | MiFILE e-service or first-class mail | Personal service |
| Court of Appeals | TrueFiling | Mail |
| MSC | Mail to all parties | — |
| Federal (WDMI) | CM/ECF | Mail |
| JTC | Mail to JTC + respondent judge | — |

Serve: **Emily A. Watson**, 2160 Garland Dr, Norton Shores, MI 49441 + **FOC**: Pamela Rusco, 990 Terrace St, Muskegon, MI 49442 (custody/PT matters). MC 12 with EVERY filing.

## 10. SCAO Forms & Filing Fees

| Form | Name | Form | Name |
|------|------|------|------|
| MC 12 | Proof of Service | MC 375 | Motion |
| MC 20 | Fee Waiver | DC 100 | Complaint |
| MC 302 | PPO (Domestic) | DC 101 | Summons |
| COA 1 | Claim of Appeal | CC 257 | Civil Cover Sheet |
| JS 44 | Federal Cover Sheet | AO 239 | Federal IFP |

| Court | Motion | New Case | Appeal |
|-------|--------|----------|--------|
| Circuit | $20 | $175 | — |
| COA/MSC | — | — | $375 |
| Federal | — | $405 | — |
| JTC | $0 | $0 | — |

## 11. MCR Quick Reference

- **MCR 2.003** — Disqualification: motion + affidavit of bias, file ASAP after discovering grounds
- **MCR 2.107** — Service: personal (2.105), mail (2.107(C)(3)), e-filing. MC 12 required
- **MCR 2.612** — Relief from judgment: (a) mistake, (b) new evidence, (c) fraud, (f) catch-all. Within 1 year
- **MCR 3.206** — Custody modification: proper cause/change of circumstances (*Vodvarka*), all 12 MCL 722.23 factors
- **MCR 3.707** — PPO: ex parte if immediate harm, hearing within 14 days, MCL 764.15b criminal contempt
- **MCR 7.212** — COA briefs: 50pp/16K words, double-spaced, TOC + authorities + jurisdictional statement + facts + argument
- **MCR 7.305/7.306** — MSC: leave to appeal, superintending control, mandamus, habeas corpus

## Summary: SINGULARITY Document Generation Workflow

```
1. RECEIVE filing task → identify lane (A-F) and document type
2. SEARCH existing documents (hybrid search — prevent duplicates)
3. QUERY evidence from litigation_context.db (evidence grounding)
4. SELECT structure: IRAC / CREAC / TEC (per filing type table §2)
5. RETRIEVE authorities from authority_chains_v2 + michigan_rules_extracted
6. QUERY contradictions for credibility sections (impeachment)
7. APPLY correct court format (per lane table §5)
8. AUTHENTICATE recordings if applicable (Sullivan v Gray §6)
9. BUILD complete packet family (§8)
10. RUN QA gates: zero placeholders, verified citations, correct year/names/child/attorney
11. GENERATE service proof (MC 12) per protocol (§9)
12. VERDICT: GO / NO-GO / CONDITIONAL
```
