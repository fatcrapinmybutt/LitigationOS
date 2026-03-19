# AUTHLOCK — Exponential Expansion Layer (v0.7) — Lane-Aware Authority & Harvester Blueprints (Append-Only)

This file extends v0.6 with lane-aware authority coverage logic and “harvester-grade” ingestion blueprints.
It is designed for integration into your MI_HC_ZIP_Harvester + AuthoritySnapshot + PCW/QUOTELOCK systems.

---

## 1) Lane-aware authority universes (MEEK tracks)

### 1.1 Why lane-aware AUTHLOCK matters
Expert practice is not “one authority list.” It is **authority + lane + vehicle**:
- The same authority may be controlling in one lane and irrelevant in another.
- A proposition must prove: **(a) authority exists, (b) it is binding for this lane, (c) it is in-snapshot, (d) it is not negatively treated, (e) it supports the exact proposition text.**

### 1.2 Minimal lane tags
Every Proposition and Proof Obligation MUST carry:
- `lane` ∈ {MEEK1, MEEK2, MEEK3, MEEK4, APPEALS, JTC, FOIA, FED_OVL}
- `vehicle_id` (forms-first vehicle)
- `court_level` ∈ {trial, COA, MSC, JTC}
- `binding_scope` ∈ {statewide, court_scoped, case_scoped, persuasive_only}

### 1.3 MEEK lane authority targets (category-level, no pseudo-law)
#### MEEK1 (Housing / landlord-tenant / utilities / habitability)
Primary targets:
- MCL landlord-tenant statutory spine (track-specific statute index)
- Administrative Code / agency rules (LARA, health/sanitation, local code adoption where applicable)
- Published COA/MSC caselaw on habitability / statutory duties / damages / defenses
Operational targets:
- AO 1999-4 + record standards (exhibit integrity)
- Local building/health code sources (only if sourced and validity tracked)
Harvester priority:
- “Statute + published caselaw first; admin code second; local code last (strict verification).”

#### MEEK2 (Custody / parenting time / FOC support)
Primary targets:
- Domestic relations MCL spine (custody/PT/support statutes)
- Family procedure MCR spine (family division procedural rules)
- Published COA/MSC caselaw on best-interest factors, custody standards, modification thresholds, due process
Operational targets:
- Michigan Child Support Formula Manual + supplement + deviation findings grid (statute-anchored)
- MJI benchbooks and checklists as operational guidance (tagged non-binding unless coupled)

#### MEEK3 (PPO / contempt / enforcement)
Primary targets:
- PPO statutory anchors + procedural MCR spine (service, hearings, evidence)
- Published COA/MSC caselaw on PPO standards, due process at hearings, evidentiary requirements
Operational targets:
- Evidence discipline: MRE + record preservation + transcript/record mismatch detection

#### MEEK4 (Judicial conduct / JTC / Canon + procedure)
Primary targets:
- Michigan Constitution JTC authority structure (constitutional lane)
- MCR 9.200+ procedural requirements (typed authority; confidentiality constraints)
- Code of Judicial Conduct (Canon nodes) + JTC guidance materials (tagged by weight)
Operational targets:
- Complaint vehicle map: intake → screening → investigation → proceedings
- Confidentiality gates (case materials vs JTC filing materials)

---

## 2) “Harvester-grade” ingestion blueprints (deterministic, auditable)

### 2.1 Authority sources: acquisition priority
Order your public sources (high to low):
1. Michigan Courts official rules/administrative orders (authoritative rule text + AOs)
2. Michigan Legislature official MCL/Constitution print endpoints
3. MSC/COA official opinions repositories where available (or official reporter references)
4. SCAO/MJI official manuals, benchbooks, and approved forms
5. Only then: third-party caselaw mirrors (for discovery convenience; not authoritative source of truth)

### 2.2 Caselaw harvester (published-first; lane-aware)
Pipeline:
1. Identify lane doctrine clusters (topic keywords + vehicle mapping)
2. Pull **published** opinions first (COA published + MSC)
3. For MSC orders:
   - ingest order
   - run predicate test (final disposition + concise facts/reasons)
   - only then label as binding precedent
4. Track negative treatment edges (overruled/superseded) by harvesting subsequent opinions and rule changes

Output artifacts:
- `caselaw_index.jsonl` (case id, court, publication status, date, citation, topic tags)
- `caselaw_pinpoints.jsonl` (paragraph/section anchors)
- `caselaw_propositions.jsonl` (proposition → pinpoint refs)
- `caselaw_treatment_edges.csv` (overrules, distinguishes, limits, etc.)

### 2.3 Proposed/adopted/effective watcher (“rule drift”)
Always separate:
- PROPOSED items (watchlist only)
- ADOPTED order (not necessarily effective)
- EFFECTIVE date state (binding)
Write a daily/weekly “diff” that produces `authority_change_log.csv` and revalidates dependent propositions.

### 2.4 Local rule/LAO harvester (validity proof required)
- Harvest local rules/LAOs only from official court sources.
- Require metadata: approval chain, effective date, scope.
- Build “validity proof bundle” for each local item; without it, local authority cannot satisfy a core PO.

---

## 3) “Exponential acceleration” rule for future expansions (how to grow faster without hallucinating)
### 3.1 Expansion must be evidence-anchored
To expand quickly without inventing law:
- Expand *structures, validators, schemas, workflows* (safe)
- Expand *pinpoints only after extraction* from authoritative text (QUOTELOCK)
- Expand *lane doctrine libraries* by pulling published opinions + building proposition grids

### 3.2 Convergence metric
Stop expanding a given module when:
- New additions are mostly synonyms, or
- They fail to add new node/edge types, validator rules, or measurable outputs.

---
Append-only note: v0.7 is designed to plug into your MI_HC_ZIP_SUPERPIN_SPEC and AuthoritySnapshot framework.
