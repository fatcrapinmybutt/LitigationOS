# Judicial & Legal Phases (10-16)

## Phase 10: Judicial Analysis

**Script:** `phase10_judicial_analysis.py`

- **Judge Pattern Analysis**: Cross-reference all evidence against McNeill's orders/rulings
  - Track: ex parte orders, missing hearings, due process violations, bias indicators
  - Score: severity (1-10) × evidence density × temporal recency
  - Map to Canon violations (3(A)(3), 3(B)(2), 3(C)(1))
- **Benchbook Violation Audit**: Compare actions against MJI benchbooks
  - DV Benchbook §5.4, Best Interest §4.2/§4.6, Civil Proceedings
- **JTC Gap-Fill**: New JTC exhibits from unearthed evidence
- **Disqualification Scoring**: Cumulative MCR 2.003(C) grounds

**Output:** judicial_analysis_report.json, benchbook_violations.jsonl, jtc_new_exhibits.jsonl

## Phase 11: Legal Action Discovery

**Script:** `phase11_legal_action_discovery.py`

Scores ALL 56 legal actions across 3 lanes:
- **Lane A**: A1-A35 (Watson/Custody) — See [lane-a-custody.md](../case-lanes/lane-a-custody.md)
- **Lane B**: B1-B14 (Shady Oaks/Housing) — See [lane-b-housing.md](../case-lanes/lane-b-housing.md)
- **Lane C**: C1-C7 (Convergence/County) — See [lane-c-convergence.md](../case-lanes/lane-c-convergence.md)

**Per-action scoring:**
1. Evidence strength: (fact_atoms × 3 + citation_atoms × 2 + person_atoms) × posture_weight
2. Authority backing: citations available ÷ citations needed
3. Adversary vulnerability: contradiction_atoms targeting that adversary
4. Composite: evidence × authority × vulnerability → 0-100

**Output per lane:** legal_action_matrix.json, adversary_profiles.jsonl, filing_priority_sequence.json

## Phase 12: Rule Audit

**Script:** `phase12_rule_audit.py`

- **Citation accuracy**: Every MCR/MCL cite verified against court rules corpus
- **Required elements check**: MCR 2.113 caption, MCR 2.119 motion requirements
- **Procedural compliance**: Service (MCR 2.107), filing (MCR 2.108), discovery (MCR 2.302)
- **Sanctions risk scan**: MCR 1.109(E) frivolous check
- **Authority chain completeness**: Every citation traces to source text
- **Contradiction detection**: Order vs MCR, party vs testimony, timeline impossibilities

**Output:** rule_audit_report.json, citation_verification.jsonl, sanctions_risk_scan.jsonl

## Phase 13: Document Refinement

**Script:** `phase13_doc_refinement.py`

- **Evidence enhancement**: Insert highest-scored new atoms into argument chains
- **Authority strengthening**: Fill citation gaps from Phase 12 audit
- **Impeachment integration**: Inject new contradictions as exhibits
- **Readiness re-scoring**: Before/after comparison (should improve all 4 dimensions)

**Output:** refined_filings/ (B1-B5 + Shady Oaks), refinement_delta.json

## Phase 14: Finalization

**Script:** `phase14_finalization.py`

- **Exhibit re-indexing**: Extend 641-exhibit index with new discoveries
- **Court packet assembly** (v4): Complete packets per filing lane
- **DOCX generation**: MCR 2.113 compliant (1" margins, TNR 12pt, double-spaced)
- **Proof of service**: Templates per MCR 2.107

**Output:** COURT_PACKETS_v4/, COURT_FILINGS_FINAL/ (updated), MASTER_EXHIBIT_INDEX_v2.txt

## Phase 15: Court-Ready Validation

**Script:** `phase15_court_validation.py`

7 QA checks:
1. Exhibit completeness (every cited exhibit exists)
2. Citation verification (every cite matches rule text)
3. Cross-filing consistency (same facts cited identically)
4. Format compliance (MCR 2.113)
5. Proof of service (all fields populated)
6. No orphans (no dangling references)
7. Sanctions shield (every claim traceable to evidence atom)

**Output:** court_validation_report.json, ready_to_file.json

## Phase 16: Desktop Offload

**Script:** `phase16_desktop_offload.py`

Exports the OMEGA pipeline as a repeatable blueprint into LitigationOS-Desktop:
- `desktop_blueprint.json` — Machine-readable pipeline definition
- `omegaPipelineService.js` — Backend orchestration service
- `OmegaPipeline.jsx` — Frontend dashboard UI

See [desktop/pipeline-integration.md](../desktop/pipeline-integration.md) for details.
