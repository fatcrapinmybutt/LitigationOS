# BRAIN_SPEC Governance — v2026.02.20

## Core Invariants

1. **Append-only** — Each pipeline run = new CyclePack. Never overwrite prior artifacts.
2. **Provenance** — Every output carries SHA-256 + source pointer + build recipe.
3. **Evidence posture** — RECORD_FACT / EVIDENCE_FACT / SWORN_FACT / ALLEGATION / INFERENCE (mandatory).
4. **EGCP v2** — No "UNKNOWN". Missing data → Gap Ticket with acquisition plan.
5. **Deterministic IDs** — `sha1(f"{BrainID}|{Type}|{KeyFields}")` for dedup safety.

## 39 Modules

| Range | Domain |
|-------|--------|
| 1-3 | Graph Brains (knowledge graph construction) |
| 4-9 | Inputs/Normalization (evidence intake + citation normalization) |
| 10-12 | Vehicles/Authority/Forms (filing vehicles + authority mapping) |
| 13 | Deadlines (temporal reasoning + MCR computation) |

## References

- [Atom Formats](atom-formats.md) — 5 JSONL atom store schemas
- [Scoring](scoring.md) — Formula + 50-brain LEXOS map
- [EGCP v2](egcp-v2.md) — Gap Ticket protocol

## No-Hallucination Rule

If a proposition cannot be grounded in a source:
1. Tag it as `INFERENCE` with confidence score
2. Generate a Gap Ticket with acquisition plan
3. Proceed only with what IS grounded
4. NEVER fabricate citations or authority text
