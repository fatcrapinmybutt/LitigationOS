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
