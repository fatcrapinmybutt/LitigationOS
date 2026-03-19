# Court of Appeals Brief — DISCOVERY DRAFT

STATUS: DISCOVERY ONLY — DO NOT FILE FROM THIS OUTPUT
FACT POLICY: No invented facts. All missing content is listed as INPUT_REQUIRED lines.

## Blockers
- [warn] COA_COURT_NOT_DETECTED: No COA court signal detected in extracted text; draft will be structure-only and discovery-only.
- [hard_stop] CASE_NUMBER_MISSING: Case number not detected; provide caption/case metadata to generate any filing-ready cover.

## Detected metadata
- courts_detected: NONE_DETECTED
- case_numbers_detected: NONE_DETECTED
- candidate_order_dates_from_context: NONE_DETECTED

## Structure anchors
- AUTHORITY_ANCHOR: MCR 7.212 (brief contents/format) — verify against your authority snapshot / official MCR PDF.

## Statement of Questions Involved
- INPUT_REQUIRED: issue_nodes (validated questions + standards of review + preservation flags)

## Statement of Facts
- INPUT_REQUIRED: pinned_record_excerpts (orders/transcripts with page/line pinpoints)
- INPUT_REQUIRED: chrono_events_subset (events linked to evidence pointers)

## Argument
- INPUT_REQUIRED: authority_triples (proposition → authority → pinpoint; MSC/COA published status)
- INPUT_REQUIRED: record_pinpoints (transcript/order snippets for each argument unit)

## Relief Requested
- INPUT_REQUIRED: vehicle_map (requested relief units mapped to authorized vehicles/forms)
