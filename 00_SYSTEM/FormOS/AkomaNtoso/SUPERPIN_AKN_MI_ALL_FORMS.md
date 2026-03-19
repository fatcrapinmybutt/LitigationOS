# SUPERPIN — MI AKN FORM FACTORY (ALL COURTS, ALL FORMS, ALL JURISDICTIONS)

**COMMAND NAME:** `MI_AKN_FORMS:BUILD_ALL@100pct`  
**DATE STAMP:** 2026-02-28  
**TARGET:** VS Code Copilot CLI (generate code + docs + DB migrations + tests)  
**SCOPE:** Michigan Trial Courts + Michigan Court of Appeals + Michigan Supreme Court  
**OBJECTIVE:** Create a Form Factory that generates **Akoma Ntoso XML templates + field maps + composition profiles**
for **every** Michigan court form (SCAO-approved forms = hundreds) and for **all appellate/trial document-types**
that function as “forms” even if not SCAO PDFs.

---

## 0) Non-negotiable outputs (Definition of Done)

### A. Coverage
1. **SCAO-approved forms**: all families (MC, DC, CC, FOC, JC, PC, etc.), all revisions/versions found.
2. **Non-SCAO “procedural forms” (document-types)** for:
   - **COA**: brief/appx/motion/original action complaint/answers/service proofs/etc.
   - **MSC**: application for leave, motions, answers, appendices/record excerpts, etc.
   - **Trial**: generic pleadings when no SCAO form exists (motion, brief, affidavit, proposed order, notice of hearing, proof of service, exhibit index, etc.)

### B. For each “Form” in database, produce:
- `FormProfile` (JSON): identity + jurisdiction/court + document-type + required sections/fields + attachments rules + service rules + PII rules + page/format rules + authority citations.
- `FieldMap` (JSON): every field keyed, typed, and normalized.
- `AkomaNtosoTemplate` (XML): LegalDocML AKN for the document-type, with placeholders matching the FieldMap.
- `RenderTargets`:
  - `preview.md` (human readable)
  - optional `docx` renderer hooks (not required initially, but design must allow)
- `ComplianceProfile` (JSON): MiFILE + MCR composition checks that LitigationOS can lint before “submit”.

### C. Storage + provenance
- Deterministic IDs; stable filenames.
- SHA-256 for every artifact; manifest+index tables.
- Immutable versioning per revision date (no overwrites).

### D. CI + validation
- JSON Schema validation for FormProfile/FieldMap/ComplianceProfile
- AKN XML well-formedness + schema/structure validation
- Lint rules for MiFILE + MCR composition requirements
- Unit tests for 10+ seed forms and 5+ appellate doc-types.

---

## 1) Authoritative rule sources to encode (Michigan)

Your generator must encode composition requirements from these authoritative sources **as rules**, not prose.

### A. Global filing standards (applies everywhere unless form/rule exception)
- **MCR 1.109(D)** filing standards: legibility, English, 8½×11, font, caption structure, etc.
- **MCR 1.109(E)** signatures and e-signatures.
- **MCR 1.109(D)(9)** protected PII redaction + PII form workflow.
- **MiFILE “Electronic Document Standards” / Policies and Standards No. 2** (rev. 7/17/2020):
  - OCR/searchable PDF, direct-to-PDF requirement,
  - margins (1" top/bottom, ½" sides), no margin text,
  - 25 MB file size, multi-part filings,
  - attachment indexing rules (Index to Attachments on last page of lead doc; attachment naming),
  - hyperlinks self-contained, no embedded audio/video,
  - page limits for motions/briefs where referenced.

### B. Motions and motion practice
- **MCR 2.119** (motion requirements, titles, briefs, attachments/affidavits, timing).

### C. Pleadings and captions
- **MCR 2.111** general pleading requirements (referenced by MiFILE standards).

### D. Appellate composition rules
- COA briefs: **MCR 7.212**
- COA original actions: **MCR 7.206**
- MSC applications/motions: **Subchapter 7.300** rules.
- Always include MiFILE standards “Preparing Appellate Documents” as an extra layer.

### E. Court records / rejection reasons
- Michigan Trial Court Records Management Standards — standard rejection reasons and SCAO-form-version handling.

---

## 2) Core idea (how you make “hundreds of forms” tractable)

Treat SCAO PDFs and their instruction PDFs as **inputs**, and produce per-form structured outputs:

1) identity metadata  
2) authority citations (bottom-of-form)  
3) structural requirements (instructions)  
4) field map (blanks + checkboxes)  
5) composition profile (rules layered: global → court-level → doc-type → form-specific)

---

## 3) Data model (DB tables)

Implement migrations for:
- forms
- form_versions
- authority_citations
- field_maps
- akn_templates
- composition_profiles
- artifacts
- ingest_runs

IDs must be deterministic hashes of (form_code + revision_date + canonical_url).

---

## 4) Ingestion

### A. Catalog fetch
Build a catalog fetcher from SCAO forms endpoints. If the site is dynamic, implement fallbacks:
- parse official “recent revisions” PDFs/memos
- parse published directories / indexes
- cache `catalog_raw.json` so you never rediscover

### B. Versioning
For each form_code, locate:
- current PDF
- instruction PDF if present: `inst{formcode}.pdf`
- other appendices

---

## 5) Akoma Ntoso generation rules (AKN)

- Namespace: `http://docs.oasis-open.org/legaldocml/ns/akn/3.0`
- Root element by doc_type (motion/petition/order/affidavit/brief/etc.)
- FRBR URNs deterministic (include MI + form code + revision)
- Every fillable field becomes a deterministic placeholder keyed to `field_id`.
- Implement attachment indexing (Index to Attachments) as required by MiFILE standards.

---

## 6) Composition requirements engine

Emit a per-form `ComplianceProfile` by layering:
1) global (MCR 1.109 + MiFILE standards)  
2) court-level (Trial vs COA vs MSC)  
3) doc-type (motion/brief/order/etc)  
4) form-specific (instructions + citations + companion forms)

---

## 7) Deliverables (code + docs)

- `form_factory/` package
- `db/` migrations
- `cli/` commands: sync/build/export
- `docs/` Form Catalog + RuleBank + QA coverage report
- CI pipeline validates JSON schemas + AKN well-formedness + rule linting

---

## 8) Convergence loop (mandatory)

Iterate until:
- catalog coverage hits 100% of discovered forms
- validators pass
- templates render cleanly for seed forms + appellate doc-types

---

## 9) Seed targets (tests must include)

- FOC 65, FOC 87
- DC 100a, DC 100c, DC 104
- MC 01, MC 97m
- CC 375M
- plus 5 synthetic appellate doc-types: COA brief, COA original action complaint, MSC application for leave, MSC motion, certificate of compliance

END SUPERPIN.
