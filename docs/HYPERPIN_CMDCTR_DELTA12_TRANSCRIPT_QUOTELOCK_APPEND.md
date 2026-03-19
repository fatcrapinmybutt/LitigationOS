# HYPERPIN — CMDCTR Δ12 Transcript Quote-Lock Append

**Directive compass:** Expand the Litigation Command Center so transcript/order quote anchors become first-class objects linked to orders, service proofs, evidence atoms, and vehicle lanes.

## Build rail
- Generate `transcript_quotes.json` from `EvidenceAtoms` + hearing discovery targets.
- Generate `order_evidence_quote_lock_links.json` with deterministic joins (date/lane, direct IDs, ExhibitMatrix joins).
- Surface quote-lock objects in GUI with filters (lane / band / source / status) and provenance jump hints.
- Keep exact quote text nullable until source text is harvested; never fabricate verbatim text.

## Output artifacts
- `runtime/transcript_quote_lock.py`
- `data/transcript_quotes.json`
- `data/order_evidence_quote_lock_links.json`
- `schemas/*.schema.json`
- `schemas/contracts/delta12_transcript_quote_lock_contracts.py`
- `scripts/validate_delta12_payloads.py`
- UI patches for `quote-lock` panel

## Continuation target
Promote quote-lock rows from `EXTRACT_TARGET` to `QUOTELOCK_READY` by harvesting transcript/order text and binding exact page-line snippets.
