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
