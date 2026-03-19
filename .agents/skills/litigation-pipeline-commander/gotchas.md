# Gotchas — litigation-pipeline-commander

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "We can skip Phase 0 (Safety) — it's just a formality for simple documents." | Phase 0 catches PII exposure, privileged material leaks, and corrupted inputs. Skipping it has resulted in privileged attorney-client communications being included in discovery productions. There are no "simple documents" in litigation. | Privileged material disclosure = waiver of privilege. In Pigors v Watson, a single privileged email exposed in Lane A could waive privilege across ALL lanes. Phase 0 is non-negotiable. |
| 2 | "Phase 2 (Dedup) isn't necessary — I manually checked for duplicates." | Human dedup catches exact copies. It misses near-duplicates (same document, different scan quality), versioned duplicates (draft 1 vs draft 3), and metadata-only differences. The pipeline catches what humans cannot. | Duplicate documents in court filings = sanctions risk. Duplicate evidence in exhibits = credibility damage. Judge Hoopes (Lane B) specifically flagged redundant exhibits in a prior Shady Oaks matter. |
| 3 | "Phase 7 (Merge) can be simplified — the lanes don't really overlap." | Lane A (custody) and Lane B (housing) ALWAYS overlap in Pigors v Watson. Watson's housing situation affects custody fitness arguments. Shady Oaks conditions affect the children's welfare. Phase 7 is where the case becomes greater than its parts. | Simplified merge = missed convergence opportunities. The entire Lane C strategy depends on proper Phase 7 merge. Skipping or simplifying it reduces a three-lane coordinated litigation to two disconnected small cases. |
| 4 | "The checkpoint failed but the data looks fine — we can skip re-running the phase." | Checkpoint failures mean the phase exit conditions were not met. "Data looks fine" is subjective; checkpoint validation is objective. A failed checkpoint means something specific was wrong — find it and fix it. | Proceeding past a failed checkpoint propagates the error downstream. By Phase 11 (Legal Actions), you're building motions on a corrupted foundation. The error compounds at every subsequent phase. |
| 5 | "Phase 10 (Judicial) isn't reliable — judicial pattern analysis is speculative." | Judicial pattern analysis is based on actual rulings, not speculation. Judge McNeill's custody ruling patterns and Judge Hoopes' housing case dispositions are documented in the record. Pattern analysis improves strategy; ignoring it means flying blind. | Failing to analyze judicial patterns means writing briefs that don't speak to the judge's concerns. Judge McNeill emphasizes certain best-interest factors; Judge Hoopes has specific expectations for CZ motions. Ignoring patterns wastes the court's time and yours. |
| 6 | "We can run Phases 8, 9, 10 sequentially — parallel execution is overcomplicating things." | Sequential execution of independent phases wastes time. Phases 8 (Impeach), 9 (MCP), and 10 (Judicial) have no mutual dependencies after Phase 7 completes. Parallel execution is not a luxury — it's how you meet deadlines. | Sequential execution of three 2-hour phases = 6 hours. Parallel execution = 2 hours. With a court deadline in 48 hours, those 4 extra hours are the difference between a polished filing and a rushed one. |
| 7 | "Phase 15 (Validate) is redundant if Phase 14 (Finalize) passed." | Phase 14 checks format and completeness. Phase 15 runs a FULL convergence cycle on the complete work product — testing cross-references, authority currency, evidence coverage, and strategy coherence as a whole. They test entirely different things. | Skipping Phase 15 means your "final" product was never tested as a complete unit. Individual phases passing does not mean the integrated product works. This is the most common cause of filing-day surprises. |

---

## Common Failure Modes

### 1. Phase Dependency Violation
- **What happens**: A phase executes before its prerequisite phase completes
- **How to prevent**: Dependency graph is enforced — no phase starts without predecessor checkpoint
- **Lane risk**: CRITICAL — data integrity depends on execution order

### 2. Checkpoint Corruption
- **What happens**: Checkpoint file is malformed, truncated, or has invalid hash
- **How to prevent**: Checkpoints include SHA-256 hash verification; corrupted checkpoints trigger Level 3 recovery
- **Lane risk**: HIGH — corrupted checkpoint can cascade to all downstream phases

### 3. Quarantine Overflow
- **What happens**: Too many documents quarantined in Phase 2-3, insufficient data for later phases
- **How to prevent**: If quarantine exceeds 20% of documents, HALT and investigate root cause
- **Lane risk**: MEDIUM — usually indicates a data quality problem at intake

### 4. Merge Conflicts (Phase 7)
- **What happens**: Lane A and Lane B data contradict each other during merge
- **How to prevent**: Contradiction detection runs before merge; conflicts must be resolved manually
- **Lane risk**: CRITICAL for Lane C — this IS the convergence point

### 5. Stale Pipeline State
- **What happens**: Pipeline resumed from old checkpoint after case data has changed
- **How to prevent**: Checkpoints include timestamp; resume validates checkpoint age against latest data
- **Lane risk**: HIGH — litigation data changes rapidly during active proceedings

---

## Performance Gotchas

- Phase 4 (Extract) on large document sets can exceed memory limits — process in batches
- Phase 5 (Brains) knowledge graph updates are not atomic — interrupted updates leave partial state
- Phase 8 (Impeach) requires all deposition transcripts — missing transcripts = incomplete impeachment
- Phase 11 (Legal Actions) depends on ALL prior phases — it cannot produce quality output from incomplete inputs
- Phase 16 (Desktop) packaging assumes Phase 15 passed — never package unvalidated work product

---

## Integration Gotchas

- **litigation-convergence-orchestrator** runs during Phase 15 — ensure convergence skill is operational
- **litigation-authority-validator** runs during Phase 12 and Phase 14 — authority validation is invoked twice by design
- **litigation-brain-spec** is updated during Phase 5 — brain changes propagate to all downstream phases
- **litigation-filing-packager** is invoked by Phase 16 — packaging depends on all prior phases completing cleanly
- **litigation-appellate-strategist** may consume pipeline outputs — ensure Phase 16 outputs are accessible
