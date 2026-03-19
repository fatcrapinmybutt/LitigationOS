# AUTHLOCK — Recursive Assistant Response Log (Append-Only)

Generated: 2026-01-19T20:37:03.514730 (America/Detroit context)



---

## Included file: AUTHLOCK_patch_v0.4_20260119.md


# AUTHLOCK Patch v0.4 (2026-01-19) — Missing Elements + Upgraded Block

## 1) What was missing from your AUTHLOCK list (high-signal adds)

### 1.1 Constitutional / foundational
- **Michigan Constitution of 1963** (top-of-stack; also authorizes Michigan’s judicial discipline framework, including JTC).

### 1.2 Michigan caselaw (bindingness classes)
- **Michigan Supreme Court opinions** (binding).
- **Michigan Supreme Court orders that qualify as binding precedent** (separate class; treat explicitly).
- **Published Michigan Court of Appeals opinions** (binding on lower courts under stare decisis unless and until reversed/modified by higher authority).
- **Unpublished Michigan Court of Appeals opinions**: not precedentially binding; usable only as persuasive/instructive with an explicit “why-cited” explanation and copy-service discipline.

### 1.3 Administrative / court-governance authority (MI-only)
- **Michigan Supreme Court Administrative Orders (AOs)** (often operationally controlling; include effective date + scope).
- **Michigan Court Rules Chapter 8 (Administrative Rules of Court)**: local rule / local administrative order mechanisms, record-management structures, and other governance rules.
- **SCAO “guidelines” documents** that explain Chapter 8 processes (operational/interpretive guidance; not a replacement for MCR text).

### 1.4 Local rules / LAOs validity gate (not just “if sourced”)
Local court rules and local administrative orders should be treated as usable only if:
- the adoption/approval pathway is satisfied (per controlling Michigan court rules/guidelines),
- the local rule is not inconsistent with statewide rules,
- the effective date window is satisfied, and
- you have the archived source text.

### 1.5 Court-record authority (case-specific, but controlling in practice)
- **Controlling case orders / judgments / opinions** (the “governing order set” for the case), with:
  - entry date, effective date, and operative terms,
  - any stay/suspension provisions,
  - record citations (page/paragraph/line) for every operative proposition.

### 1.6 JTC-specific authority set (MI-only)
- **MCR Subchapter 9.200 (Judicial Tenure Commission)** (including confidentiality/disclosure rule(s)).
- **JTC official intake/process pages and forms** (operational constraints; confidentiality is not optional).

### 1.7 Explicit “status tags” and “precedence rules”
AUTHLOCK needs explicit tagging for each authority item and proposition:
- `BINDING_MI` (Constitution; binding caselaw; binding MSC orders; MCR/MCL/MRE; MSC AOs where applicable)
- `OFFICIAL_GUIDE_MI` (SCAO clerk/practice guides; COA/MSC practice materials)
- `JUDICIAL_EDU_MI` (MJI benchbooks/QRMs/manuals; persuasive/educational)
- `LOCAL_RULE_MI` (MSC-approved local court rules; SCAO-approved LAOs)
- `PERSUASIVE_MI` (e.g., Michigan State Bar commentary; never a substitute for MI primary authority)
- `TOOLING_NONAUTH` (NIST/OWASP/etc. for system controls only)
- `FED_OVERLAY` (non-controlling overlay; always labeled)

### 1.8 Versioning + effective-date governance (AuthoritySnapshot discipline)
Add explicit requirements:
- Every authority item must store: publisher, publication date/effective date, capture timestamp, and the “snapshot date” used by the system.
- Propositions must declare whether they rely on “snapshot authority” or “case order authority,” and must fail if out-of-snapshot for filing-ready products.

---

## 2) Updated AUTHLOCK block (drop-in)

### 0.1 Michigan-Only Authority Lock (AUTHLOCK) — v0.4
1. Treat **Michigan primary authority** as the default universe; propositions may rely on these only:
   - **Michigan Constitution of 1963**
   - **Michigan Court Rules (MCR)** (official publication; include Chapter 8 administrative rules and Chapter 9 JTC subchapter where applicable)
   - **Michigan Compiled Laws (MCL)**
   - **Michigan Rules of Evidence (MRE)**
   - **Michigan Supreme Court Administrative Orders (AOs)** (and other official Michigan Courts administrative issuances)
   - **Michigan Supreme Court opinions** and **binding-precedent MSC orders**
   - **Published Michigan Court of Appeals opinions** (binding)
   - **Unpublished COA opinions**: NOT binding; persuasive only; must include “why-cited” explanation + attach/provide copy with the filing paper that cites it
   - **Michigan Code of Judicial Conduct** + **MCR Subchapter 9.200 (JTC rules)** + official JTC materials (forms/process/confidentiality)
   - **SCAO-approved forms** + SCAO publications that are part of Michigan Courts official materials (forms-first routing; treat instructions/checklists as `OFFICIAL_GUIDE_MI` unless rule text says otherwise)
   - **Michigan Judicial Institute (MJI) benchbooks / checklists / manuals** (`JUDICIAL_EDU_MI`; persuasive/educational; never a substitute for rule text)
   - **MSC-approved local court rules** and **SCAO-approved local administrative orders (LAOs)**, usable only if:
     - adoption/approval requirements are met,
     - not inconsistent with statewide authority,
     - within effective-date window, and
     - you have the archived source text.
2. **Case-order supremacy within the case**: controlling orders/judgments in the record govern the parties for that case unless stayed/reversed/modified; do not treat them as “law,” but do treat them as controlling constraints that must be mapped and complied with.
3. **Federal material is allowed only as non-controlling overlay** and must be explicitly labeled `FED_OVERLAY`; it may not be used as the sole authority for any Michigan proposition in a filing-ready product.
4. **Authority status tags are mandatory** (`BINDING_MI`, `OFFICIAL_GUIDE_MI`, `JUDICIAL_EDU_MI`, `LOCAL_RULE_MI`, `PERSUASIVE_MI`, `TOOLING_NONAUTH`, `FED_OVERLAY`), and the system must enforce precedence:
   - Constitution > MSC opinions / binding-precedent orders > MCR/MCL/MRE/MSC AOs > published COA > (LOCAL_RULE_MI consistent with statewide authority) > official guides/benchbooks > persuasive commentary > tooling-only.
5. **AuthoritySnapshot**: every run pins an authority snapshot date; any out-of-snapshot citation fails `FILE_READY` unless explicitly approved as an “authority refresh” with a recorded snapshot delta.

### 0.2 Minimal enforcement checks (for PCW/PCG)
- Every proposition must carry: `(authority_id, status_tag, effective_date, pinpoint)`.
- Every factual claim must carry: `(evidence_ref, locator)`.
- Any quotation must be QuoteLock-verified before `FILE_READY`.
- Any local-rule/LAO cite must include an “approval/effective-date” proof item.


---

## Included file: AUTHLOCK_patch_v0.5_20260119.md


# AUTHLOCK Patch v0.4 (2026-01-19) — Missing Elements + Upgraded Block

## 1) What was missing from your AUTHLOCK list (high-signal adds)

### 1.1 Constitutional / foundational
- **Michigan Constitution of 1963** (top-of-stack; also authorizes Michigan’s judicial discipline framework, including JTC).

### 1.2 Michigan caselaw (bindingness classes)
- **Michigan Supreme Court opinions** (binding).
- **Michigan Supreme Court orders that qualify as binding precedent** (separate class; treat explicitly).
- **Published Michigan Court of Appeals opinions** (binding on lower courts under stare decisis unless and until reversed/modified by higher authority).
- **Unpublished Michigan Court of Appeals opinions**: not precedentially binding; usable only as persuasive/instructive with an explicit “why-cited” explanation and copy-service discipline.

### 1.3 Administrative / court-governance authority (MI-only)
- **Michigan Supreme Court Administrative Orders (AOs)** (often operationally controlling; include effective date + scope).
- **Michigan Court Rules Chapter 8 (Administrative Rules of Court)**: local rule / local administrative order mechanisms, record-management structures, and other governance rules.
- **SCAO “guidelines” documents** that explain Chapter 8 processes (operational/interpretive guidance; not a replacement for MCR text).

### 1.4 Local rules / LAOs validity gate (not just “if sourced”)
Local court rules and local administrative orders should be treated as usable only if:
- the adoption/approval pathway is satisfied (per controlling Michigan court rules/guidelines),
- the local rule is not inconsistent with statewide rules,
- the effective date window is satisfied, and
- you have the archived source text.

### 1.5 Court-record authority (case-specific, but controlling in practice)
- **Controlling case orders / judgments / opinions** (the “governing order set” for the case), with:
  - entry date, effective date, and operative terms,
  - any stay/suspension provisions,
  - record citations (page/paragraph/line) for every operative proposition.

### 1.6 JTC-specific authority set (MI-only)
- **MCR Subchapter 9.200 (Judicial Tenure Commission)** (including confidentiality/disclosure rule(s)).
- **JTC official intake/process pages and forms** (operational constraints; confidentiality is not optional).

### 1.7 Explicit “status tags” and “precedence rules”
AUTHLOCK needs explicit tagging for each authority item and proposition:
- `BINDING_MI` (Constitution; binding caselaw; binding MSC orders; MCR/MCL/MRE; MSC AOs where applicable)
- `OFFICIAL_GUIDE_MI` (SCAO clerk/practice guides; COA/MSC practice materials)
- `JUDICIAL_EDU_MI` (MJI benchbooks/QRMs/manuals; persuasive/educational)
- `LOCAL_RULE_MI` (MSC-approved local court rules; SCAO-approved LAOs)
- `PERSUASIVE_MI` (e.g., Michigan State Bar commentary; never a substitute for MI primary authority)
- `TOOLING_NONAUTH` (NIST/OWASP/etc. for system controls only)
- `FED_OVERLAY` (non-controlling overlay; always labeled)

### 1.8 Versioning + effective-date governance (AuthoritySnapshot discipline)
Add explicit requirements:
- Every authority item must store: publisher, publication date/effective date, capture timestamp, and the “snapshot date” used by the system.
- Propositions must declare whether they rely on “snapshot authority” or “case order authority,” and must fail if out-of-snapshot for filing-ready products.

---

## 2) Updated AUTHLOCK block (drop-in)

### 0.1 Michigan-Only Authority Lock (AUTHLOCK) — v0.4
1. Treat **Michigan primary authority** as the default universe; propositions may rely on these only:
   - **Michigan Constitution of 1963**
   - **Michigan Court Rules (MCR)** (official publication; include Chapter 8 administrative rules and Chapter 9 JTC subchapter where applicable)
   - **Michigan Compiled Laws (MCL)**
   - **Michigan Rules of Evidence (MRE)**
   - **Michigan Supreme Court Administrative Orders (AOs)** (and other official Michigan Courts administrative issuances)
   - **Michigan Supreme Court opinions** and **binding-precedent MSC orders**
   - **Published Michigan Court of Appeals opinions** (binding)
   - **Unpublished COA opinions**: NOT binding; persuasive only; must include “why-cited” explanation + attach/provide copy with the filing paper that cites it
   - **Michigan Code of Judicial Conduct** + **MCR Subchapter 9.200 (JTC rules)** + official JTC materials (forms/process/confidentiality)
   - **SCAO-approved forms** + SCAO publications that are part of Michigan Courts official materials (forms-first routing; treat instructions/checklists as `OFFICIAL_GUIDE_MI` unless rule text says otherwise)
   - **Michigan Judicial Institute (MJI) benchbooks / checklists / manuals** (`JUDICIAL_EDU_MI`; persuasive/educational; never a substitute for rule text)
   - **MSC-approved local court rules** and **SCAO-approved local administrative orders (LAOs)**, usable only if:
     - adoption/approval requirements are met,
     - not inconsistent with statewide authority,
     - within effective-date window, and
     - you have the archived source text.
2. **Case-order supremacy within the case**: controlling orders/judgments in the record govern the parties for that case unless stayed/reversed/modified; do not treat them as “law,” but do treat them as controlling constraints that must be mapped and complied with.
3. **Federal material is allowed only as non-controlling overlay** and must be explicitly labeled `FED_OVERLAY`; it may not be used as the sole authority for any Michigan proposition in a filing-ready product.
4. **Authority status tags are mandatory** (`BINDING_MI`, `OFFICIAL_GUIDE_MI`, `JUDICIAL_EDU_MI`, `LOCAL_RULE_MI`, `PERSUASIVE_MI`, `TOOLING_NONAUTH`, `FED_OVERLAY`), and the system must enforce precedence:
   - Constitution > MSC opinions / binding-precedent orders > MCR/MCL/MRE/MSC AOs > published COA > (LOCAL_RULE_MI consistent with statewide authority) > official guides/benchbooks > persuasive commentary > tooling-only.
5. **AuthoritySnapshot**: every run pins an authority snapshot date; any out-of-snapshot citation fails `FILE_READY` unless explicitly approved as an “authority refresh” with a recorded snapshot delta.

### 0.2 Minimal enforcement checks (for PCW/PCG)
- Every proposition must carry: `(authority_id, status_tag, effective_date, pinpoint)`.
- Every factual claim must carry: `(evidence_ref, locator)`.
- Any quotation must be QuoteLock-verified before `FILE_READY`.
- Any local-rule/LAO cite must include an “approval/effective-date” proof item.

===============================================================================
APPENDIX — v0.5 ADDENDUM (2026-01-19) — “WHAT’S MISSING” + HARDENED CITATION RULES
===============================================================================

PURPOSE
- This addendum answers: “What’s missing from 0.1 AUTHLOCK?” and hardens the Authority Universe and
  bindingness model with explicit Michigan pinpoints.
- This section is append-only; it does not delete or rewrite v0.4.

-------------------------------------------------------------------------------
A) WHAT WAS MISSING FROM YOUR 0.1 LIST (AUTHORITY CLASSES)
-------------------------------------------------------------------------------

A.1 Michigan Constitution of 1963 (CONSTITUTION)
- Must be inside the Michigan authority universe. It is a primary source and can control conflicts.
- Practical relevance: jurisdiction, due process, courts’ powers, and (notably) requirements for written MSC decisions.

A.2 Binding Michigan caselaw (MSC + published COA) + persuasive caselaw tiers
- MSC opinions are binding statewide.
- COA published opinions are binding on lower courts (and on later COA panels unless superseded).
- Unpublished COA opinions are not binding precedent but may be cited for their persuasive value.

A.3 Michigan Supreme Court orders as precedent (CONSTITUTION + MSC caselaw gate)
- MSC orders can be precedential when they constitute a final disposition and include a “concise statement of
  the facts and reasons for each decision.”
- Treat this as a separate authority class from “MSC opinions” because it needs its own predicate test.

A.4 Michigan Administrative Code (ADMIN_RULES)
- State agency rules and regulations (administrative law) can be controlling when validly promulgated and applicable.
- Necessary for MEEK1 (housing regulatory layers) and for cross-agency matters (DHHS, LARA, etc.).

A.5 Professional responsibility / discipline sources (MRPC + MCR Ch. 9)
- Michigan Rules of Professional Conduct (MRPC) (lawyer ethics) and Michigan Court Rules governing discipline.
- Separate class because it is frequently a “constraint layer” (e.g., conflicts, contact rules, tribunal candor).

A.6 Michigan Child Support Formula Manual (MCSF) as a required statewide guideline + deviation statute anchor
- The MCSF Manual is an SCAO statewide guide; courts generally must apply the formula and deviations require
  findings/record support under statute.

A.7 Michigan Supreme Court Administrative Orders impacting filing/records/e-filing/records access
- Example: AO 1999-4 (records management standards). This is not “MCR” and not “MCL” but is controlling statewide.

-------------------------------------------------------------------------------
B) MICHIGAN PINPOINTS (AUTHLOCK “HARD REFERENCES”)
-------------------------------------------------------------------------------

B.1 Unpublished COA opinions are not binding precedent
- **MCR 7.215(C)(1)**: unpublished opinions are not precedentially binding (but may be persuasive).

B.2 Local court rules and local administrative orders (LAOs) validity mechanics
- **MCR 8.112(A)** governs local court rules, including that a trial court may adopt rules that do not conflict with
  the MCRs and regulate matters not covered; practices requiring notice/compliance must be adopted as a local rule
  and approved by the Supreme Court before enforcement.
- **MCR 8.112(B)** governs administrative orders: internal court management only; must be sent to the State Court
  Administrator before its effective date; and the order may be stayed or revoked if directed.

B.3 Constitutional requirement for written MSC decisions
- **Michigan Constitution 1963, art 6, § 6**: “Decisions of the supreme court … shall be in writing and shall contain
  a concise statement of the facts and reasons for each decision.”

B.4 MSC orders as precedent (predicate test)
- **DeFrain v State Farm Mut Auto Ins Co, 491 Mich 359 (2012)** (MSC): recognizes that Supreme Court orders can be
  binding where they are a final disposition and contain an adequate statement of facts/reasons (Art 6, § 6 predicate).
- AUTHLOCK rule: treat MSC orders as their own class; admit as binding only if the predicate test passes.

B.5 Records standards are controlled by AO 1999-4
- **AO 1999-4** orders that the State Court Administrator establish Michigan Trial Court Records Management Standards
  and that trial courts conform; it also addresses electronic availability and handling of protected identifiers.

B.6 Child support guideline presumption and deviation anchor
- **MCL 552.605(2)**: generally requires application of the child support formula; deviations require specified findings.
- **Michigan Child Support Formula Manual**: states that courts must order support by applying the formula, except as
  permitted by MCL 552.605; manual is effective by date and updated via supplements.

B.7 MRPC is a primary Michigan ethics authority for lawyers
- Michigan Rules of Professional Conduct (MRPC) are adopted and published as a Michigan primary authority source.

-------------------------------------------------------------------------------
C) AUTHLOCK “AUTHORITY UNIVERSE” v0.5 (NORMALIZED LIST)
-------------------------------------------------------------------------------

C.1 Primary / controlling Michigan authorities (default universe)
- **Michigan Constitution of 1963**
- **Michigan Supreme Court opinions (published)**
- **Michigan Supreme Court orders** (binding only if predicate test passes: final disposition + Art 6, § 6 facts/reasons)
- **Michigan Court of Appeals opinions**
  - Published (binding on lower courts; subject to superseding authority)
  - Unpublished (persuasive only; not binding)
- **Michigan Compiled Laws (MCL)**
- **Michigan Court Rules (MCR)** (including appellate rules and Ch. 8 administrative rules; Ch. 9 discipline/JTC)
- **Michigan Rules of Evidence (MRE)**
- **Michigan Supreme Court Administrative Orders (AOs)** (records, e-filing programs, etc.)
- **Michigan Administrative Code (state agency rules/regulations)**
- **SCAO-approved forms + instructions** (SCAO mandated use / SCAO publications)
- **Michigan Judicial Institute (MJI)** benchbooks / checklists / manuals
- **Statewide SCAO standards/guidelines manuals** (e.g., **Michigan Child Support Formula Manual**)
- **Court-specific local court rules (LCRs) + Local Administrative Orders (LAOs)** (only if sourced and valid under MCR 8.112)
- **Case-specific controlling orders** (entered in the case; used for deadlines/constraints; still subject to higher authority)

C.2 Federal overlay (allowed but explicitly labeled; never controlling “by default”)
- Federal constitution, federal statutes, federal rules, and federal caselaw may be used as an overlay only when:
  (a) a federal claim/vehicle is actually invoked, or (b) Michigan doctrine expressly incorporates federal standards.
- Must be labeled `OVL_FED` and never used to displace Michigan controlling sources unless Michigan law requires it.

-------------------------------------------------------------------------------
D) GRAPH/VALIDATOR HARDENING (AUTHLOCK ↔ AUTHORITYSNAPSHOT ↔ PCW)
-------------------------------------------------------------------------------

D.1 AuthorityRef type taxonomy (minimum)
- CON_MI (MI Const)
- MSC_OPINION_PUB
- MSC_ORDER (with predicate_test fields)
- COA_PUB
- COA_UNPUB
- MCL
- MCR
- MRE
- AO_MSC (Michigan Supreme Court Administrative Order)
- ADMIN_CODE (Michigan Administrative Code rule)
- SCAO_FORM (form + instructions)
- SCAO_GUIDE (manual / guideline / publication)
- MJI_BENCHBOOK
- LCR (local court rule)
- LAO (local administrative order)
- CASE_ORDER (entered order in the case)
- ETHICS_MRPC
- DISCIPLINE_MCR9 (MCR discipline/judicial conduct/JTC procedural rules)

D.2 Required AuthorityRef fields (validator minimum)
- authority_id (stable)
- authority_type (enum above)
- title
- citation_string (human)
- effective_start_date, effective_end_date (nullable)
- capture_date (when harvested)
- source_locator (URL or archive path)
- pinpoint (section/rule/subrule; page/paragraph; etc.)
- bindingness (BINDING / PERSUASIVE / NONCONTROLLING_OVERLAY)
- snapshot_id (AuthoritySnapshot batch identifier)

D.3 Predicate test fields (MSC_ORDER only)
- is_final_disposition (bool)
- has_concise_facts_and_reasons (bool)
- predicate_basis (e.g., “MI Const art 6 § 6”)
- predicate_source_ref (pointer to the order/opinion where this is assessed)
- validator_result (PASS/FAIL) + audit notes

D.4 AUTHLOCK ↔ PCW integration rule (proposition-level)
- Every Proof Obligation (PO) must cite at least one **AuthorityRef** whose `bindingness` is BINDING within the
  relevant Michigan authority universe **as of the filing date**.
- If only persuasive authority exists, PO status cannot advance to SATISFIED unless:
  (a) the PO is explicitly marked “persuasive-permitted,” and
  (b) the strategy layer documents why binding authority is unavailable or unnecessary.
- If a local rule/LAO is invoked, PO must also include a “validity proof” edge to MCR 8.112 compliance artifact
  (e.g., LAO/approval metadata).

-------------------------------------------------------------------------------
E) IMPLEMENTATION NOTE — “OUT-OF-SNAPSHOT” GATE (refinement)
-------------------------------------------------------------------------------

OUT_OF_SNAPSHOT is triggered if:
- authority_ref.capture_date > snapshot_cutoff_date, OR
- authority_ref.effective_start_date > snapshot_asof_date, OR
- authority_ref.effective_end_date < snapshot_asof_date (expired), OR
- authority_ref.authority_type is not in the allowed enum set for the track/court

Gate behavior:
- DISCOVERY/DRAFT: warn + acquisition plan
- FILE_READY/PCG: FAIL unless explicitly overridden with a pinned “AuthorityUpdate” transaction that
  (a) expands the snapshot, (b) revalidates all dependent propositions/POs, and (c) logs the delta.

-------------------------------------------------------------------------------
F) QUICK CHECKLIST — AUTHLOCK MINIMUM (v0.5)
-------------------------------------------------------------------------------

[ ] Constitution present (CON_MI)
[ ] Caselaw tiers present (MSC + COA_PUB + COA_UNPUB) + bindingness tagging
[ ] MCR 7.215(C)(1) rule captured (unpublished = not binding)
[ ] MCR 8.112 captured (local rules + admin orders validity)
[ ] MCR Ch. 9 captured (JTC/discipline procedural layer) + MRPC captured
[ ] AO 1999-4 captured (records management standards)
[ ] MCSF Manual captured + MCL 552.605(2) deviation anchor captured
[ ] ADMIN_CODE category enabled for tracks requiring regulations
[ ] AuthorityRef schema + predicate test for MSC orders implemented


---

## Included file: AUTHLOCK_expert_knowledge_pack_v2026-01-19.1.md


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


---

## Included file: AUTHLOCK_exponential_expansion_v0.6_20260119.md


# AUTHLOCK — Exponential Expansion Layer (v0.6) — v2026-01-19.2 (Append-Only)

This file is an append-only upgrade layer intended to sit above AUTHLOCK v0.4 and v0.5 and the Expert Pack v2026-01-19.1.
It adds *expert practice mechanics*: hierarchy resolution, precedential-weight enforcement, proposal/adoption/effectivity separation,
and ingestion/validation pipelines aligned to AuthoritySnapshot + PCW + QUOTELOCK.

---

## 0) Core invariants (expert level)
### 0.1 Hierarchy is a function, not a list
AUTHLOCK must encode an explicit **Rule of Decision** function that answers: “If sources conflict, which wins?”
Minimum ordering (highest to lowest, MI-only):
1. **MI Constitution (1963)**
2. **Binding Michigan Supreme Court decisions** (opinions; and qualifying precedent orders)
3. **MCL (statutes)**
4. **MCR (court rules)** + MRE (evidence rules) (note: evidence rules can override procedural defaults inside the evidentiary lane)
5. **Published COA opinions**
6. **MSC Administrative Orders (AOs)** (statewide administrative governance; still cannot contradict Constitution/statute/rule)
7. **Michigan Administrative Code** (agency rules) (valid only if authorized and consistent with higher law)
8. **SCAO mandated-use forms + instructions** (binding only to the extent the rule/administrative framework requires)
9. **Statewide guidelines/manuals (MJI, MCSF, etc.)** (operational; “must-use” when governing rule/statute requires)
10. **Local court rules / LAOs** (court-scoped; valid only if adopted/approved and non-conflicting)
11. **Persuasive authority** (unpublished opinions, treatises, federal overlays—always tagged)

### 0.2 Status tagging is mandatory
Every AuthorityRef MUST carry at least:
- authority_type
- bindingness
- court_level / issuer
- publication_status (where applicable)
- effective_start/end (nullable)
- snapshot_id + capture_date
- proposal/adopted/effective lifecycle phase (for rule changes)

### 0.3 “Proposed ≠ Effective” hard separation
- Proposed orders / staff comments / proposals are **never** effective law.
- They may produce WATCH nodes only.
- Any downstream Proposition that cites a proposal must be automatically tagged `PROPOSAL_ONLY` and barred from FILE_READY.

---

## 1) Precedent discipline (caselaw engine)
### 1.1 COA published vs unpublished (enforce, don’t explain)
- COA_PUB: binding under stare decisis.
- COA_UNPUB: persuasive only; requires relevance explanation and must not be used when published authority exists.

**Graph rule:** if Proposition relies on COA_UNPUB, attach `PERSUASIVE_JUSTIFICATION` node and a `NO_PUBLISHED_AVAILABLE` check.
Failing either => PO remains OPEN/partial.

### 1.2 MSC orders as precedent (predicate test node)
Create an explicit predicate-test artifact:
- is_final_disposition?
- contains concise facts?
- contains reasons?
- linked to Const 1963 art 6 § 6 basis
- validator PASS/FAIL + audit notes

Only PASS => bindingness=BINDING.

### 1.3 “Overruled / superseded / vacated” must be tracked
AuthoritySnapshot should support:
- supersedes_ref
- negative_treatment (overruled, vacated, superseded, distinguished, limited)
- treatment_source (the later decision/rule change)
A Proposition cannot be SATISFIED if its sole authority has negative_treatment=overruled/superseded.

---

## 2) Local rules / LAOs (validity and enforceability engine)
### 2.1 Validity evidence bundle requirement
A LocalRuleRef must include:
- source PDF/HTML capture (official site or certified copy)
- effective date
- adoption/approval metadata (MCR 8.112 trace)
- non-conflict assertion (auto-check against MCR topic scope)
If any missing => LocalRuleRef is `UNVERIFIED_LOCAL` and cannot satisfy a core PO.

### 2.2 Remote hearing / video tech LAO patterns (example class)
Model LAOs that implement procedural programs (e.g., remote appearance) as “PROGRAM_LAO” subtype with:
- implementation procedures
- scope of hearing types
- required notices
- data collection/reporting obligations

---

## 3) Records survival & file integrity (AO + MCR + MRE fusion)
### 3.1 AO 1999-4 operationalization
Treat AO 1999-4 as an **administrative compliance layer** for:
- records access
- electronic availability
- protected identifiers handling
- standards enforcement

**Graph pattern:** `RecordArtifact` ↔ `AO_1999_4_Standard` edges + `PII_Redaction` constraints.

### 3.2 QUOTELOCK methodology (mechanical)
QUOTELOCK PASS requires:
1. primary extraction from the stored authority source
2. independent re-extraction (different tool/path or second pass)
3. byte-for-byte match (or a logged diff explaining formatting-only deltas)
Until PASS => quote is `QUOTE_CANDIDATE` and barred from FILE_READY.

---

## 4) AuthoritySnapshot ingestion pipeline (state-of-the-art but deterministic)
### 4.1 Lifecycle events
Maintain `AuthorityChangeEvent` nodes:
- PROPOSED (includes staff comment; watch only)
- ADOPTED (order entered; not necessarily effective yet)
- EFFECTIVE (date; now binding)
Each AuthorityRef version must link to one or more events.

### 4.2 Snapshot build outputs (minimum)
- authority_snapshot_index.jsonl
- authority_sections.jsonl (or parquet) with anchors/pinpoints
- authority_propositions.jsonl (proposition ↔ pinpoints)
- authority_change_log.csv
- authority_watchlist.jsonl (proposals not yet adopted/effective)

### 4.3 Cross-snapshot delta protocol
Authority update is not a silent refresh:
- Create an `AuthorityUpdateTransaction` with:
  - old snapshot_id
  - new snapshot_id
  - changed refs list
  - affected propositions list
  - revalidation results
This is the only permitted mechanism to move FILE_READY work forward after a rule change.

---

## 5) PCW integration upgrades (fast, enforceable)
### 5.1 “Authority PO” template
Add a mandatory PO class for every Vehicle/Claim lane:
- PO_AUTH_BINDING: at least one binding AuthorityRef per proposition
- PO_AUTH_PINPOINT: has precise section/subsection/pinpoint
- PO_AUTH_IN_SNAPSHOT: authority is within snapshot dates
- PO_AUTH_NO_NEG_TREAT: not overruled/superseded

### 5.2 Graded gate (avoid over-strictness)
- DISCOVERY/DRAFT: allow persuasive + proposals but tag as such.
- FILE_READY/PCG: hard fail on proposals/out-of-snapshot/unverified locals/unverified quotes.

---

## 6) “Expert coverage” expansion targets (what to build next)
1. Full caselaw ingest for your active lanes (MEEK1–MEEK4):
   - COA/MSC: published opinions; key MSC precedent orders; lane-specific doctrine sets.
2. Local court rule/LAO registry for Muskegon courts (with MCR 8.112 metadata).
3. Records survival: AO 1999-4 + MCR 1.109, 8.119, 8.119(D) mapping.
4. Child support spine: MCL 552.605 ↔ MCSF Manual ↔ deviation findings grid.
5. JTC lane: Const art 6 § 30 + MCR 9.200+ procedural vehicle map.

---
Append-only note: this file is meant to be merged into your existing AUTHLOCK as an “upgrade layer.”

---
## Included file: AUTHLOCK_exponential_expansion_v0.7_20260119.md

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

---
## Included file: AUTHLOCK_exponential_expansion_v0.8_20260119.md

# AUTHLOCK — Exponential Expansion Layer (v0.8) — GraphContracts + AuthorityTriples + VehicleMap Wiring (Append-Only)

This file accelerates the AUTHLOCK ecosystem by hardening the **graph contract layer** and the **forms-first vehicle layer**
so the authority stack becomes executable: authorities → propositions → proof obligations → vehicles → filings.

---

## 1) GraphContracts (node/edge schema) — authority-grade minimums

### 1.1 Authority nodes
#### AuthorityRef
Required fields:
- authority_id (stable)
- jurisdiction = "MI"
- authority_type (enum)
- issuer (MSC/COA/SCAO/Legislature/Court/etc.)
- title
- citation_string
- publication_status (PUB/UNPUB/NA)
- bindingness (BINDING/PERSUASIVE/OVL_FED/NONCONTROLLING)
- effective_start_date, effective_end_date (nullable)
- capture_date
- snapshot_id
- source_locator (URL or vault path)
- checksum / integrity_key

#### AuthoritySection
- section_id (stable)
- authority_id (FK)
- pinpoint (rule/subrule; article/section; statute subsection; paragraph range)
- anchors[] (structured anchors for re-extraction)
- text (verbatim; QUOTELOCK gated)
- token_count (for retrieval planning)
- extraction_provenance (tool + version)

#### AuthorityChangeEvent
- event_id
- authority_id
- event_type (PROPOSED/ADOPTED/EFFECTIVE/AMENDED/REPEALED)
- event_date
- ADM_file_no (if applicable)
- summary
- links[]

### 1.2 Caselaw nodes
#### CaseLawDecision
- case_id
- court_level (MSC/COA)
- publication_status
- decision_date
- official_citation
- docket/app_id (if known)
- topics[] (lane tags)
- negative_treatment (list) + treatment_sources[]

### 1.3 Proposition nodes
#### Proposition
- proposition_id
- proposition_text (short, atomic)
- lane
- vehicle_id (nullable in discovery)
- authority_pinpoints[] (AuthoritySection refs)
- bindingness_required (bool)
- status (DRAFT/VERIFIED/DEPRECATED)
- validator_notes

### 1.4 PCW nodes
#### ProofObligation
- po_id
- po_type (AUTH_BINDING, AUTH_PINPOINT, AUTH_IN_SNAPSHOT, QUOTELOCK_PASS, LOCAL_RULE_VALID, etc.)
- lane
- vehicle_id
- proposition_id (FK)
- required (bool)
- status (OPEN/PARTIAL/SATISFIED)
- evidence_refs[] (EvidenceAtom ids)
- authority_refs[] (AuthoritySection ids)
- test_spec (how to validate)
- validator_result (PASS/FAIL/WARN) + audit trail

---

## 2) VehicleMap (forms-first execution layer)

### 2.1 VehicleMap node types
- `Vehicle` (e.g., “Motion”, “Objection”, “Claim of Appeal”, “Superintending Control Complaint”, “JTC Complaint”)
- `Form` (SCAO/MC/FOC mandated use forms)
- `AttachmentRequirement` (what must be included)
- `ServiceChain` (who/how/when)
- `DeadlineRule` (authority-bound deadline logic)
- `CourtPreference` (e.g., “oral argument preferred” as operational guidance; tagged non-authoritative unless sourced)

### 2.2 Mapping edges
- Vehicle REQUIRES Form (mandatory forms-first)
- Vehicle CONTROLLED_BY AuthoritySection (procedural standards)
- Vehicle SATISFIES/CREATES ProofObligation
- Vehicle REQUIRES ServiceChain + DeadlineRule
- Vehicle SUPPORTS Lane

### 2.3 Validator rules (minimum)
- A Vehicle cannot be FILE_READY unless:
  - all required POs are SATISFIED
  - all citations are in-snapshot
  - all verbatim quotes are QUOTELOCK_PASS
  - all local rules/LAOs used are VALIDATED_LOCAL
  - service chain is complete with address/fee/mileage rules as applicable

---

## 3) AuthorityTriples (Proposition ↔ Authority ↔ Pinpoint) — enforceable pattern

### 3.1 Triple schema
- triple_id
- proposition_id
- authority_section_id
- claim_strength (BINDING/PERSUASIVE)
- lane
- usage_role (elements, standard, procedure, deadline, remedy, evidence rule)
- notes

### 3.2 “No-claim” rule enforcement
Every filing-facing claim MUST map to ≥1 triple with:
- binding authority for the lane/court, OR
- explicit persuasive justification.

---

## 4) Bloom perspective pack (deterministic visualization)

### 4.1 Labels and colors (deterministic)
- AuthorityRef: label by authority_type (MCR/MCL/MRE/CONST/AO/etc.)
- Proposition: label by lane + status
- ProofObligation: label by status (OPEN/PARTIAL/SATISFIED)
- Vehicle/Form: label by vehicle type

### 4.2 Bloom import checklist
- Constraints (unique ids)
- Indexes (authority_id, section_id, proposition_id, po_id)
- Relationship types imported before styling
- Styles applied from a single JSON preset file
- Verification query pack (counts + orphan checks + “no-claim” checks)

---
Append-only note: v0.8 is designed to be directly compatible with “Graph contracts + Bloom perspective pack + AuthoritySnapshot ingestion + PO/PCW overlay” requirements.
