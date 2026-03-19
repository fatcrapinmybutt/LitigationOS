# AUTHLOCK — Expert Michigan Authority Stack & Ingestion Pack (v2026-01-19.1)

## 1) What you’re missing to reach “expert-level” Michigan authority coverage

Your AUTHLOCK 0.1 list is directionally correct, but **expert-level** requires you to explicitly model **(a) authority hierarchy**, **(b) precedential weight rules**, and **(c) mandatory statewide “guideline” corpora** that routinely control trial-court outcomes.

### 1.1 Add to the Michigan-only authority universe (primary / controlling)
1. **Michigan Constitution of 1963** (esp. judicial power + appellate structure + JTC):
   - Treat as a top-tier node type with article/section pinpoints.
   - Example: **Const 1963, art 6, § 6** (writing requirement + “concise statement” concept that later cases tie to precedential effect of certain orders).  
2. **Binding Michigan caselaw**
   - **Michigan Supreme Court opinions** (majority decisions).
   - **Published Michigan Court of Appeals opinions** (binding under stare decisis per MCR 7.215(C)(2)).
   - **Michigan Supreme Court orders** may be binding **if** they meet the “final disposition + concise facts & reasons” criteria (see DeFrain rule).
3. **Michigan Administrative Code / agency rules** (when the dispute touches regulated domains; MCR 7.215’s publication criteria expressly contemplate cases invalidating provisions included in the Administrative Code).
4. **Statewide guideline corpora that courts must use**
   - **Michigan Child Support Formula Manual + current supplement** (FOC/SCAO). Courts “must” order support via formula absent deviation conditions (MCL 552.605 framework).

### 1.2 Add as Michigan “authoritative secondary” (not controlling, but high-value)
1. **MJI/SCAO appellate & practice bench materials** (especially “Appeals & Opinions” benchbook sections on precedent and citation discipline).
2. **Trial Court Records Management Standards** (Michigan Supreme Court AO 1999-4) — operationally critical for record survival, exhibits, and file integrity.
3. **Court administration manuals/guides** (SCAO publications; MiFILE standards & PII protection guidance).
4. **Ethics layers**
   - Michigan Code of Judicial Conduct (you already have).
   - **Judicial Tenure Commission procedural rules (MCR 9.200 et seq.)** (you already flagged “JTC materials” but you want the *rules* themselves as typed authority).  
   - (Optional) Michigan Rules of Professional Conduct + Attorney Discipline Rules (MCR 9.100 et seq.) when attorney behavior is a lane.

## 2) Precedential-weight rules you should hard-code into the graph

### 2.1 Court of Appeals opinions: published vs unpublished
- **Unpublished COA opinions are not precedentially binding**; if cited, the party must justify relevance and should not cite for propositions where published authority exists. (MCR 7.215(C)(1).)
- **Published COA opinions are precedentially binding** under stare decisis (MCR 7.215(C)(2)).

### 2.2 Michigan Supreme Court “orders” can be binding precedent (key nuance)
- Michigan Supreme Court orders are binding precedent **if** they:
  1) are a final disposition of an application, and  
  2) contain a concise statement of the applicable facts and reasons for the decision.  
  This standard is discussed in **DeFrain v State Farm** and is tied to **Const 1963, art 6, § 6**.

### 2.3 Local administrative orders and local rules
- Treat **MCR 8.112** as the controlling gate for local rules/LAOs: local practice must be sourced to an approved/valid local administrative order pathway (and tracked with effective dates + approval metadata).
- Model “LocalRule/LAO” as **non-self-authenticating** until you have a source + approval chain.

## 3) Canonical acquisition map (authoritative sources you can ingest)

### 3.1 Michigan Constitution / statutes
- Michigan Legislature “print document” endpoints are the cleanest stable source for constitutional text pinpoints and MCL sections.

### 3.2 Michigan Court Rules / Administrative Orders / Proposed & Adopted Orders
- Michigan Courts official rules site provides:
  - Responsive HTML for Court Rules (good for structured extraction).
  - Official Supreme Court administrative orders and the “proposed vs adopted” pipeline (critical because rules can change; proposals must not be treated as effective law).

### 3.3 JTC procedural rules (MCR 9.200 et seq.)
- Extract the subchapter text and link: **JTC procedural rule nodes** ↔ **Canon nodes** ↔ **complaint workflow vehicles**.

### 3.4 Child support formula (MCSF) + MiChildSupport calculator
- Ingest the manual (effective date tracked) and supplement pointers.
- Add the calculator as a “tool reference,” not authority, but useful for reproducible calculations and exhibits.

### 3.5 SCAO-approved forms
- Your “forms-first” protocol requires: **form PDF + instructions + revision date + use/approval status**. Build an index that maps:
  - proceeding type → form number → controlling MCR/MCL → required attachments → service chain.

## 4) AuthoritySnapshot ingestion spec upgrades (practical, LitigationOS-ready)

### 4.1 Minimum typed nodes
- `AuthorityRef` (base): {jurisdiction=MI, authority_type, title, citation, effective_date, version_id, source_url, checksum}
- `AuthoritySection`: {pinpoint, text, anchors[]}
- `Proposition`: {proposition_text, authority_pinpoint_refs[]}
- `AuthorityVersion`: {effective_start, effective_end, supersedes, adopted_order_ref}
- `AuthorityChangeEvent`: {proposal|adopted|effective, date, ADM_file_no, summary}

### 4.2 Gates
- **AUTHLOCK gate**: blocks any proposition lacking a pinned `AuthoritySection` in-snapshot.
- **QUOTELOCK gate**: blocks verbatim quotes unless independently re-extracted/verified from the stored authority source.
- **PROPOSAL gate**: proposed orders are never treated as effective; they may only create a “watch item” until an adopted+effective event exists.

### 4.3 Practical output artifacts
- `authority_snapshot_index.jsonl` (one row per AuthorityRef + version)
- `authority_sections.parquet` (or jsonl) with anchors, pinpoints, text
- `authority_propositions.jsonl` (proposition ↔ authority pinpoints)
- `authority_change_log.csv` (proposal/adopted/effective)
- `authority_citation_style.md` (house style for pinpoints)

## 5) 14-day “expert coverage sprint” (high ROI, court-facing)
Day 1–2: Authority hierarchy + precedent rules (Const 1963 art 6; MCR 7.215; MJI Precedent chapter)  
Day 3–4: Local-rules gating (MCR 8.112 + local AO sourcing discipline)  
Day 5–6: Administrative orders + records survival (AO 1999-4)  
Day 7–9: Domestic relations spine: custody/PT/support vehicles (MCR 3.200/3.300 family + MCSF manual)  
Day 10–11: PPO spine (MCR 3.310 and related evidence/service mechanics)  
Day 12–14: JTC pipeline (MCR 9.200 et seq + Code of Judicial Conduct → vehicle mapping)

Deliverables per day:
- 10–30 propositions with pinned authority sections
- 1–3 vehicle maps (forms-first) with service and deadline chain
- 1 “contradiction radar” checklist (what to look for in orders/transcripts)

## 6) Source list (official / high-authority anchors)
- Const 1963, art 6, § 6 (Michigan Legislature print document)
- MCR 7.215 (Michigan Courts official Court Rules HTML/ZIP)
- MCR 8.112 (Michigan Courts official Court Rules HTML/ZIP)
- Michigan Supreme Court AO 1999-4 (Trial Court Records Management Standards)
- MCR 9.200 et seq. (Judicial Tenure Commission rules) + JTC constitutional authority (Const 1963, art 6, § 30)
- 2025 Michigan Child Support Formula Manual (SCAO/FOC) + MiChildSupport calculator

---
Append-only note: This pack is designed to be merged into your existing AUTHLOCK and AuthoritySnapshot builders as an **upgrade layer** (no renames, only additive types/gates/indices).
