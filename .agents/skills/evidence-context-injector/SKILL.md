---
name: evidence-context-injector
description: >-
  Inject real evidence context from databases, analysis files, and harvested data into legal
  documents. Use when enriching authority packages, filing documents, or briefs with specific
  quotes, dates, exhibit references, and quantified damages from the litigation evidence corpus.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: inject context, enrich document, evidence injection, context injection, real evidence
---

# evidence-context-injector

## Purpose

Transform generic legal document sections into evidence-backed, court-ready content by pulling
real data from LitigationOS databases and analysis files. Every "Application to Case" section
should contain specific quotes, dates, source references, and quantified damages.

## Data Sources (Priority Order)

| Source | Location | Content |
|--------|----------|---------|
| Master Timeline | Desktop\LITIGATION_ANALYSIS\MASTER_CHRONOLOGICAL_TIMELINE.md | 8,162 events with dates |
| Impeachment Playbook | Desktop\LITIGATION_ANALYSIS\EMILY_WATSON_IMPEACHMENT_PLAYBOOK.md | 9,624 items |
| Master Analysis | Desktop\LITIGATION_ANALYSIS\MASTER_LITIGATION_ANALYSIS.md | 28 focus areas, evidence scores |
| Analysis Data JSON | Desktop\LITIGATION_ANALYSIS\analysis_data.json | 329 evidence points indexed |
| Housing Results JSON | Desktop\LITIGATION_ANALYSIS\housing_deep_results.json | Housing violations DB |
| Evidence Harvest Report | LEGAL_REFERENCE_LIBRARY\09_INDEXES\EVIDENCE_HARVEST_REPORT.md | DB extracts per lane |
| Central DB | LitigationOS\litigation_context.db | 308K quotes, 15K impeachment, 10K contradictions |
| Shady Oaks Evidence | Desktop\LITIGATION_ANALYSIS\SHADYOAKS_EVIDENCE_001\ | Mining reports |

## Injection Pattern

### Step 1: Identify Target Sections
Scan document for "Application to Case", "Application", or "Evidence" sections that contain
generic summaries without specific quotes, dates, or source references.

### Step 2: Map Claims to Evidence
For each claim/count, identify:
- **Top 5 evidence quotes** (strongest, most specific, most damaging)
- **Key dates** (when events occurred, filed, discovered)
- **Source documents** (PDF names, page numbers, DB table+row IDs)
- **Quantified damages** (specific dollar amounts with calculation basis)
- **Witness statements** (attributed quotes from depositions, affidavits, transcripts)

### Step 3: Format for Court
Each evidence injection block follows this template:

#### Evidence Supporting [Claim Name]

**Key Evidence:**
1. **[Date]** — "[Exact quote from evidence]" *(Source: [document name], p. [page])*
2. **[Date]** — "[Exact quote from evidence]" *(Source: [document name], p. [page])*
3. **[Date]** — "[Exact quote from evidence]" *(Source: [document name], p. [page])*

**Quantified Damages:**
- Economic: $[amount] (basis: [calculation])
- Non-economic: $[amount] (basis: [standard])
- Treble/Punitive: $[amount] (statute: [MCL citation])

**Exhibits:** See Exhibit [letter] (PIGORS-[lane]-[####])

### Step 4: Cross-Reference
Add "See Also" links to related authority packages and filing documents.

## Lane-Specific Evidence Keywords

| Lane | Primary Keywords | Secondary Keywords |
|------|-----------------|-------------------|
| A (Custody) | alienation, parenting time, best interest, custody, visitation | L.D.W., Lincoln, exchange, school, medical |
| B (Housing) | Shady Oaks, rent, ledger, habitability, sewage, eviction | lease, EGLE, VanDam, Davis, Browley, Alden |
| D (PPO) | protection order, PPO, harassment, stalking | bond, violation, false allegation |
| E (Misconduct) | McNeill, ex parte, bias, ruling, disqualification | Canon, JTC, void order, due process |
| F (Appellate) | appeal, COA 366810, standard of review, preserved error | abuse of discretion, de novo, clearly erroneous |

## Quality Gates

- Every "Application" section has 3+ specific evidence quotes with dates
- Every damages range has a calculation basis (not just "estimated")
- Every claim maps to 1+ exhibit reference
- No placeholder text remains ([INSERT], [DATE], [AMOUNT])
- All quotes are attributed to specific sources
- Cross-references link to related packages
