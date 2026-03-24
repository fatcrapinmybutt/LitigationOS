# Quality Gates Reference — OMEGA-LITIGATION-SUPREME

## Overview

Every output from OMEGA-LITIGATION-SUPREME must pass through M8 QA Gates before delivery.
This document defines all quality gates, the pre-filing checklist, and citation verification protocol.

---

## Gate 1: Anti-Hallucination Check

### Party Name Verification
- [ ] Every proper noun cross-referenced against verified party table
- [ ] Emily Watson spelled exactly as "Emily A. Watson" (not "Emily Ann", "Emily M.", "Tiffany")
- [ ] Judge spelled as "Hon. Jenny L. McNeill" (not "McNeil", "Amy McNeill")
- [ ] Child referenced as "L.D.W." only — never full name per MCR 8.119(H)
- [ ] Ronald Berry identified as NON-ATTORNEY — no "Esq.", no bar number
- [ ] Jennifer Barnes (P55406) noted as WITHDRAWN if referenced

### Fabricated Data Detection
- [ ] No statistics without traceable SQL query
- [ ] No "alienation scores" or pseudo-scientific metrics
- [ ] No extrapolated or rounded-up counts
- [ ] Every date verified against DB or court record

---

## Gate 2: DB-First Confirmation

### Pre-Placeholder Protocol
Before inserting ANY placeholder (`[ANDREW_REQUIRED]`, `[INSERT]`, `[ATTACH]`):

1. **Query `litigation_context.db`**:
   - Check `docket_events` for dates and procedural history
   - Check `evidence_quotes` for testimony and document excerpts
   - Check `claims` for cause of action details
   - Check `deadlines` for filing dates
   - Check `documents` for exhibit references
   - Check `judicial_violations` for misconduct evidence

2. **Search filesystem**:
   ```powershell
   rg -l "search_term" C:\Users\andre\LitigationOS\ --type md --type txt
   fd --type f "filename" C:\Users\andre\LitigationOS\ I:\ F:\ G:\
   ```

3. **Check reference files**:
   - `COMPLETE_FILING_DATA_SUMMARY.txt`
   - `QUICK_REFERENCE_FILING_PLACEHOLDERS.txt`
   - `QUICK_REFERENCE.txt`

4. **Only if ALL three return nothing** → insert placeholder with:
   - Specific description of what data is needed
   - Suggested location where Andrew might find it
   - Which DB table/column would store it once found

---

## Gate 3: Citation Verification Protocol

### Authority Chain Validation
- [ ] Every case citation verified for: correct name, correct reporter citation, correct year
- [ ] Every statute citation verified for: correct MCL/MCR number, current version (not repealed/amended)
- [ ] Check `authority_chains` table: `SELECT * FROM authority_chains WHERE citation = ?`
- [ ] Flag any citation with `chain_complete = 0` as needing verification
- [ ] No "see generally" citations without at least one pinpoint cite in the same section

### Citation Format Requirements (Michigan)
- Cases: *Party v Party*, Vol Reporter Page (Court Year)
- Statutes: MCL Section.Number
- Court Rules: MCR Rule.Subrule(Subsection)
- Federal: 42 USC § Section

### Overruled/Superseded Detection
- [ ] Check if cited case has been overruled, distinguished, or superseded
- [ ] Check if cited statute has been amended since the version cited
- [ ] Check if cited court rule has been modified by administrative order

---

## Gate 4: Lane Integrity Check

- [ ] All evidence tagged with correct lane (A-F)
- [ ] No cross-lane contamination (Lane A evidence in Lane E filing, etc.)
- [ ] MEEK signal detection confirms lane assignment
- [ ] Lane-specific case numbers correct:
  - Lane A: 2024-001507-DC
  - Lane B: 2025-002760-CZ
  - Lane D: 2023-5907-PP
  - Lane E: (JTC complaint — no case number until filed)
  - Lane F: COA 366810
  - Lane C: Cross-lane convergence (document which lanes are converging)

---

## Gate 5: Traceable Statistics Audit

- [ ] Every numerical claim has a documented SQL query
- [ ] `COUNT(*)` queries use `DISTINCT` where duplicates possible
- [ ] No aggregate spans multiple tables without dedup
- [ ] Format: "X incidents (source: `SELECT COUNT(DISTINCT id) FROM table WHERE condition`)"
- [ ] Dashboard numbers match filing numbers — no inflation for either

---

## Gate 6: Format Compliance (MCR)

- [ ] Caption format per MCR 1.109
- [ ] Page limits respected (MCR 7.212(B): 50 pages for briefs)
- [ ] Font and margin requirements met
- [ ] Certificate of service included
- [ ] Verification/signature block present
- [ ] Exhibit index with Bates numbers if applicable

---

## Pre-Filing Checklist (Final)

```
BEFORE SUBMITTING ANY FILING:
□ Anti-hallucination check passed (Gate 1)
□ DB-first confirmation completed (Gate 2)
□ All citations verified (Gate 3)
□ Lane integrity confirmed (Gate 4)
□ Statistics traceable (Gate 5)
□ Format compliant (Gate 6)
□ Proof of service prepared
□ Filing fee addressed (waiver if applicable)
□ E-filing format requirements met (TrueFiling/MiFile)
□ Backup copy saved to appropriate lane folder
```

---

## Gate Failure Protocol

When any gate fails:
1. **STOP** — do not deliver the output
2. **IDENTIFY** — which gate failed and why
3. **FIX** — correct the specific failure
4. **RE-RUN** — all gates from the beginning (fixes can introduce new issues)
5. **LOG** — record the failure in M12 Self-Evolution for future prevention
