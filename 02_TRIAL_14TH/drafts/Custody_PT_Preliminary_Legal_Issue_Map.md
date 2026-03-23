# Custody/PT first — Preliminary Legal Issue Map (Michigan)

## Evidence-anchored facts from this pack (OCR excerpts)
**F1. Ex parte parenting-time suspension order (file-stamped 08/08/2025)**
- Source: `custody_pt/key_ocr/mcneillexparte_0011_p0_zoom3.txt`
- OCR shows: an order titled “ORDER REGARDING DEFENDANT'S EX PARTE MOTION TO SUSPEND PLAINTIFF'S PARENTING TIME”
- Relief granted includes: suspend parenting time; random drug screenings; mental health evaluation.

**F2. Order on objection to ex parte order (file-stamped 09/09/2025)**
- Source: `custody_pt/key_ocr/custody_scanned_0003_p0_zoom3.txt`
- OCR shows: “ORDER REGARDING PLAINTIFF'S OBJECTION TO EX PARTE ORDER”
- OCR text states an evidentiary hearing occurred on 09/04/2025 and references an assessment at HealthWest.

**F3. Referee recommendation excerpt (Recommendation dated 03/26/2025; page 10 excerpt)**
- Source: `custody_pt/key_ocr/custody_scanned2_0022_p0_zoom3.txt`
- OCR shows adverse language describing July 16 motions as “frivolous,” “harassment,” and “abuse of the Court system” (context must be verified against full recommendation).

## Core legal questions these facts raise (issue framing only)
### Q1 — Ex parte parenting-time suspension: threshold and findings
- What rule/standard did the court apply to suspend parenting time ex parte?
- Were required findings made on the face of the order (or incorporated by reference)?
- What evidence was presented (affidavit/hearsay/recordings) supporting the “irreparable injury” claim?

### Q2 — Procedural due process: prompt hearing + meaningful opportunity to be heard
- Was the objection hearing held promptly after the ex parte suspension?
- Was the hearing “meaningful” (evidentiary vs. argument-only; witness handling; exhibits admitted/refused)?
- Was the right to be heard conditioned on completing an evaluation (if so, the controlling written order must be pinned/verified).

### Q3 — Parenting-time / custody best-interest analysis
- Did the court rely on mental-health allegations or “risk” findings without an on-record best-interest factor analysis and (if required) proper evidentiary foundation?
- Did the court make/modify parenting-time conditions consistent with statutory factors governing parenting time and the child’s best interests?

### Q4 — Record integrity + appellate posture
- Identify the **controlling operative orders** (signed/entered/file-stamped/served/effective) and any superseding orders.
- Build the ROA linkage and service proofs to compute the correct deadlines for trial-court relief and higher-court vehicles.

## What is missing (must be acquired from the attachments or ROA)
- The complete file-stamped PDF of the 08/08/2025 ex parte order (all pages).
- The complete file-stamped PDF of the 09/09/2025 order (all pages).
- The complete referee recommendation and any adoption order.
- ROA entries for the above items, including entry dates and service records.
- Any written order stating that a hearing/relief is “continued until Plaintiff provides assessment” (if applicable).

## Next extraction step (mechanical)
Run `scripts/harvest_ocr_extract.py` on the full attachment ZIP(s) to produce:
- full-page text for every custody/PT PDF (embedded + OCR fallback),
- page-level indices to find the exact pages with controlling-order language,
- adverse sentence ledger with strict doc_id/page pins.
