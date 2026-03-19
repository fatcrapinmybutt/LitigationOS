# Gotchas — OMEGA-LITIGATION-SUPREME

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "I'll use a placeholder and Andrew can fill it in later." | The data is almost certainly already in `litigation_context.db` (790+ tables, 308K evidence quotes). Query the DB before inserting ANY placeholder. Andrew explicitly said: "thats the whole point of this. to USE MY FILES ON MY DRIVES." | Filings go out with `[ANDREW_REQUIRED]` stubs that should have been real data — wastes days of manual work and delays court deadlines. |
| 2 | "I'm pretty sure Emily's middle name is Ann." | Emily's name is **Emily A. Watson** — period. Past sessions fabricated "Emily Ann", "Emily M.", and even "Tiffany." The verified party table is the ONLY source of truth. | A misspelled party name on a sworn filing can be grounds for dismissal or sanctions. Wrong-party filings are void. |
| 3 | "There were approximately 9 CPS investigations based on my analysis." | That statistic was FABRICATED by a prior session. Every count must come from a `SELECT COUNT(*) FROM [table] WHERE [condition]` with the exact query documented. If you can't produce the query, don't cite the number. | Fabricated statistics in sworn filings constitute potential perjury (MCL 750.423). Opposing counsel will verify and impeach. |
| 4 | "Jane Berry is Emily's mother and helped with custody interference." | **Jane Berry never existed.** "Patricia Berry (SBN P35878)" also never existed. Ronald Berry is Emily's boyfriend — he is a NON-ATTORNEY with no bar number. These were hallucinations that infected 60+ files. | Filing a document naming a fabricated party is sanctionable under MCR 1.109(E) and potentially fraudulent. |
| 5 | "This custody evidence also supports the PPO motion, so I'll include it in both." | Lane contamination is a critical error. Lane A (Custody) and Lane D (PPO) have overlapping case numbers but different legal theories and evidence standards. Evidence must be routed through MEEK signal detection (priority: E→D→F→C→A→B). | Cross-contaminated filings confuse the court, create inconsistent record positions, and can waive arguments through judicial estoppel. |
| 6 | "The alienation score is 91% based on the pattern analysis I ran." | There is NO validated alienation scoring methodology. The "91% alienation score" was pseudo-scientific fabrication. Use documented incident counts only — e.g., "X documented instances of parenting-time interference per `SELECT COUNT(*) FROM evidence_quotes WHERE claim_type = 'interference'`." | Pseudo-scientific scores get shredded on cross-examination and destroy credibility for the legitimate evidence underneath. |
| 7 | "I'll round up the evidence count to 305 interference incidents for impact." | Duplicate counting across tables inflated prior counts. Before reporting ANY aggregate, run dedup: `SELECT COUNT(DISTINCT evidence_hash) FROM ...` and document the exact query. Round nothing. Extrapolate nothing. | Inflated numbers get caught when opposing counsel subpoenas the database. The entire evidence presentation loses credibility. |

---

## Common Failure Modes

### 1. DB-Bypass Placeholder Cascade
- **What happens**: Agent skips database queries and inserts `[INSERT DATE]`, `[ATTACH EXHIBIT]`, `[ANDREW_REQUIRED]` placeholders throughout a filing — even when the data exists in `litigation_context.db`.
- **How to prevent**: Before ANY placeholder, execute this 3-step protocol: (1) Query `litigation_context.db` for the data, (2) Search filesystem with `rg`/`fd` across all drives, (3) Check `COMPLETE_FILING_DATA_SUMMARY.txt`. Only if ALL three fail → insert placeholder with specific retrieval instructions.
- **Lane risk**: HIGH for all lanes — affects every filing type.

### 2. Party Name Hallucination
- **What happens**: The LLM generates plausible-sounding but fabricated names (e.g., "Jane Berry," "Patricia Berry," "Amy McNeill") or incorrect name variants ("Emily Ann Watson").
- **How to prevent**: Hard-code the verified party table into every prompt. Cross-check EVERY proper noun in output against the table. If a name isn't in the table, insert `[UNKNOWN — VERIFY]`.
- **Lane risk**: HIGH for Lanes A, D, E — party names appear in every filing caption.

### 3. Cross-Lane Evidence Contamination
- **What happens**: Evidence tagged for Lane A (custody) gets included in Lane E (misconduct) filings, or Lane D (PPO) evidence bleeds into Lane F (appellate) briefs.
- **How to prevent**: Always run MEEK signal detection before including any evidence. Check `lane` column in evidence tables. Never manually override lane assignment without documenting the legal basis.
- **Lane risk**: HIGH for Lane C (convergence) — the cross-lane nature makes it the most vulnerable to contamination.

### 4. Statistic Inflation via Duplicate Counting
- **What happens**: Agent counts rows across multiple tables that reference the same underlying event, inflating totals (e.g., counting the same incident in both `evidence_quotes` and `claims` tables).
- **How to prevent**: Always use `COUNT(DISTINCT ...)` on a unique identifier. Before reporting aggregates, check for and exclude duplicates. Document the exact SQL query alongside every statistic.
- **Lane risk**: MEDIUM for all lanes — particularly dangerous in Lane A (custody) where best-interest factor scoring depends on accurate counts.

### 5. Module Routing Failure (Wrong Module for Task)
- **What happens**: A filing task gets routed to M1 (Evidence Pipeline) instead of M4 (Filing Factory), or a strategy question goes to M3 (Authority Validator) instead of M5 (Strategic Command).
- **How to prevent**: Always use M11 (Smart Router) as the entry point. Match task keywords against the module activation triggers. When in doubt, ask: "Am I extracting evidence (M1), finding contradictions (M2), validating law (M3), or assembling a filing (M4)?"
- **Lane risk**: LOW individually but cascading — wrong module produces wrong output format, which downstream modules can't consume.

---

## Integration Gotchas

- **M7 (DB Intelligence) must initialize before ALL other modules** — every module depends on DB queries, and M7 sets the connection PRAGMAs and validates schema. Calling M1-M6 without M7 init causes silent failures with stale data.
- **M8 (QA Gates) is NOT optional** — every output from M4 (Filing Factory) must pass through M8 before delivery. Skipping QA "to save time" is how hallucinated names and inflated stats reach filings.
- **M12 (Self-Evolution) feedback must be logged** — if you don't log what worked/failed, the next session starts from zero and repeats the same mistakes.
- **OMEGA-LITIGATION-SUPREME absorbs but does NOT replace lane-specific databases** — always write lane-tagged data to the correct lane DB (`lane_A_custody.db`, etc.), not just to `litigation_context.db`.
- **The MCP `litigation-context` server and direct DB queries are complementary** — use MCP tools for standard operations (search, filing_readiness, deadline_dashboard) and direct SQL for complex joins or aggregations that MCP tools don't cover.
