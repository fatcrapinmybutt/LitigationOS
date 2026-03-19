# Gotchas — litigation-analysis-engine

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The analysis engine covers all case lanes automatically — no lane configuration needed." | Each lane (A-F) has distinct legal frameworks, judges, standards of review, and MCR requirements. Lane A custody analysis under MCL 722.23 uses completely different factors than Lane B housing analysis under MCL 554.139. Running the engine without explicit lane targeting produces contaminated analysis. | Cross-lane contamination: custody evidence scored under housing rubrics, or PPO factors analyzed under appellate standards. Judge McNeill (Lane A) and Judge Hoopes (Lane B) apply different weight to the same evidence types. Contaminated analysis = wrong strategic recommendations. |
| 2 | "Line-by-line document analysis is overkill — paragraph-level summarization is sufficient." | Michigan courts require pinpoint citations. MCR 7.212(C)(7) demands specific page references. Paragraph-level analysis misses individual sentences that contain admissions, contradictions, or impeachment material. In Pigors v Watson, single-sentence admissions in FOC reports changed case trajectory. | Missing impeachment opportunities, overlooked admissions, and inability to provide pinpoint cites in motions. A single missed sentence in a custody evaluation can be the difference between modification granted and denied under MCL 722.27. |
| 3 | "The scoring rubric doesn't need calibration — the defaults work for all case types." | Evidence strength scoring must be calibrated per claim type. A financial record scores differently for child support (Lane A, MCL 552.517) than for damages (Lane B, MCL 600.2918). Default scoring treats all evidence equally, which produces misleading strength assessments. | Filing motions with weak evidence because the engine scored it as strong, or failing to file strong motions because the engine undervalued critical evidence. In custody cases, judicial discretion means evidence weight is especially context-dependent. |
| 4 | "We can analyze documents without OCR verification — the text extraction is good enough." | PDF text extraction fails silently on scanned documents, court stamps, handwritten annotations, and redacted sections. Without OCR verification, the engine analyzes incomplete text and produces incomplete analysis. Phase 4a (extraction) must complete clean before Phase 5 (analysis). | Missing entire pages of evidence, analyzing OCR artifacts as real text, or skipping handwritten judicial notes. In Pigors v Watson, handwritten margin notes on a custody evaluation contained critical findings that text extraction missed entirely. |
| 5 | "One analysis pass is sufficient — iterative refinement is academic perfectionism." | Legal analysis requires multiple passes: (1) factual extraction, (2) legal issue identification, (3) authority mapping, (4) strength scoring, (5) gap identification. Single-pass analysis conflates these steps, producing shallow results that miss connections between evidence and legal standards. | Shallow analysis leads to weak filings. The OMEGA pipeline uses Phases 10-12 (Judicial Analysis → Legal Action Discovery → Rule Audit) as sequential refinement passes for exactly this reason. Skipping refinement passes means missing the gap analysis that identifies what evidence you still need. |
| 6 | "Analysis results from one case can be reused across cases without re-running." | Case contexts change — new evidence is filed, orders are entered, positions shift. Analysis results have a shelf life measured in days during active litigation. Reusing stale analysis for a new motion risks relying on superseded facts. | Filing a motion based on analysis that doesn't account for the opposing party's most recent filing. In custody cases, a single new CPS report or school record can flip best-interest factor analysis under MCL 722.23. |

---

## Common Failure Modes

### 1. Lane Cross-Contamination
- **What happens**: Engine processes Lane A custody documents through Lane B housing analysis rules, or vice versa
- **How to prevent**: Enforce MEEK signal detection at intake; validate lane assignment before analysis begins; raise `LaneCrossContaminationError` on mismatch
- **Lane risk**: HIGH — custody and housing use fundamentally different legal frameworks

### 2. Stale Evidence Scoring
- **What happens**: Engine scores evidence against outdated claim requirements because claim definitions weren't refreshed
- **How to prevent**: Run Phase 6 (Gap Analysis) with EGCP scoring before every analysis cycle; refresh claim-evidence mappings from `litigation_context.db`
- **Lane risk**: HIGH for Lane A — custody factors and parenting time evidence evolve rapidly

### 3. Citation Chain Breakage
- **What happens**: Analysis identifies relevant authority but doesn't verify the citation chain (statute → binding case → supporting case → pinpoint)
- **How to prevent**: Integrate with `litigation-authority-validator` before finalizing any analysis that includes legal citations; validate every MCR/MCL reference
- **Lane risk**: CRITICAL for Lane F (Appellate) — MCR 7.212(C)(7) requires complete citation chains

### 4. OCR-Dependent Data Loss
- **What happens**: Scanned PDFs produce garbled text; engine analyzes garbled text and generates nonsensical conclusions
- **How to prevent**: Phase 4a extraction must flag low-confidence OCR pages; analysis engine must check OCR confidence scores before processing; require manual review for pages below 85% confidence
- **Lane risk**: HIGH for all lanes — court filings, police reports, and FOC reports are frequently scanned documents

### 5. Unweighted Factor Analysis
- **What happens**: All 12 best-interest factors (MCL 722.23(a)-(l)) treated as equally weighted when Michigan case law establishes that certain factors carry more weight in specific contexts
- **How to prevent**: Apply case-law-derived weight modifiers per factor; Factor (j) (willingness to facilitate) and Factor (k) (domestic violence) receive enhanced weight per *Fletcher v Fletcher*, 447 Mich 871 (1994)
- **Lane risk**: CRITICAL for Lane A — incorrect factor weighting produces wrong custody recommendations

---

## Integration Gotchas

- **litigation-authority-validator** must validate all citations produced by analysis before they flow downstream
- **litigation-convergence-orchestrator** consumes analysis scores to compute convergence quality — garbage analysis = garbage convergence
- **litigation-filing-packager** expects analysis output in a specific schema — format changes break downstream assembly
- **litigation-brain-spec** feeds analysis with micro-brain data — if brain feed (Phase 5) is stale, analysis is stale
- MEEK signal priority (E → D → F → C → A → B) must be respected in analysis routing decisions
