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
