# DELTA12 Append Notes — Transcript Quote-Lock Rail

## What was appended
- Added `transcript_quotes.json` (quote-lock target/anchor payload) and `order_evidence_quote_lock_links.json` (deterministic joins into orders, service proofs, evidence atoms, and vehicle lanes).
- Added `runtime/transcript_quote_lock.py` and wired `runtime/launch.py` to emit quote-lock payloads on each cycle.
- Added `Transcript Quote-Lock` interactive GUI panel with lane / band / status / source filters and provenance jump-hint copy actions.
- Added JSON Schemas + Pydantic contracts + `validate_delta12_payloads.py`.

## Why this matters
This creates the connective tissue for **verbatim transcript extraction** to land in the command center without redesigning the UI. Right now the panel is honest about what is a quote-ready anchor vs. a discovery/extraction target. Once transcripts/orders are harvested, exact page-line quote text can drop into the same payload and instantly propagate through the GUI.

## Next high-signal rails
1. Service confidence / deficiency scoring (proof-grade, not heuristic)
2. Exact quote extractor for hearing/order PDFs (page-line + snippet previews)
3. Docket delta sync into order supersession + deadlines
