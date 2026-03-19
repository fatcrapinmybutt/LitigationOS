# Gotchas — ELITE_SKILLSET

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "ELITE_SKILLSET handles everything, so I don't need to pick a specific OMEGA skill." | ELITE is a meta-router. For deep domain work (e.g., pure SQLite optimization), a focused OMEGA skill like OMEGA-DATA gives better results because it has domain-specific decision trees and reference material. | Shallow, generic outputs that miss domain nuance — filings lack MCR citations, code lacks LitigationOS-specific patterns. |
| 2 | "I activated 5 skills at once for maximum coverage." | Skill overlap causes conflicting instructions. If ELITE_SKILLSET + OMEGA-LITIGATION + michigan-litigation-writer all fire, the agent gets contradictory formatting guidance. One skill per task domain. | Token waste, contradictory outputs, confused reasoning chain — the agent tries to satisfy 3 formatting standards simultaneously. |
| 3 | "The skill didn't mention my exact task, so I'll proceed without any skill." | ELITE_SKILLSET covers 27 skills across 9 domains. Check the Fused Skill Manifest table — if the task touches agent architecture, litigation, evidence, performance, prompts, data engineering, or execution planning, this skill applies. | Working without skill context = no guardrails. Agent hallucinates party names, misses shadow module traps, ignores EAGAIN limits. |
| 4 | "I'll just rely on ELITE_SKILLSET for the legal filing — it includes michigan-litigation-writer." | ELITE fuses legal writing knowledge but does NOT include Michigan court form numbers, MCR page limits, or SCAO template requirements. For filing work, route through OMEGA-LITIGATION-SUPREME which has full filing factory (M4) and QA (M8) modules. | Filed motion gets rejected: wrong caption format, missing certificate of service, exceeds page limit, wrong form number. |
| 5 | "I checked the skill prerequisites — none listed, so I'm good." | ELITE_SKILLSET implicitly requires: (a) MANBEARPIG startup protocol completed, (b) litigation_context.db accessible, (c) EAGAIN prevention rules loaded. These aren't listed as "dependencies" but are system-wide non-negotiables. | DB queries fail silently, shell sessions crash with EAGAIN, startup report data is stale or missing. |
| 6 | "ELITE_SKILLSET's agent architecture section is enough for building new agents." | The fused agent-architecture content is a summary. For actual agent implementation (Agent9999 base class, message bus wiring, tier placement), use ai-agent-architect-omega which has full implementation patterns and fleet integration guidance. | New agent doesn't inherit Agent9999, misses `run() → AgentResult` contract, isn't registered in master_index.db, breaks orchestrator. |
| 7 | "I used ELITE for evidence analysis and it found 47 incidents." | Did you deduplicate? ELITE doesn't enforce content-based dedup by default. The evidence-intelligence-nexus component counts raw matches. Cross-reference with `evidence_quotes` table and check for duplicate `source_file` + `quote_text` pairs. | Inflated evidence count cited in sworn filing — could constitute misrepresentation to the court. Traceable Statistics rule violated. |

---

## Common Failure Modes

### 1. Skill Overlap Collision
- **What happens**: ELITE_SKILLSET is activated alongside another OMEGA skill that covers the same domain (e.g., OMEGA-LITIGATION for legal writing). The agent receives conflicting instructions about format, citation style, or output structure.
- **How to prevent**: Use ELITE_SKILLSET as the sole skill OR decompose the task and route each sub-task to a single focused OMEGA skill. Never stack overlapping skills.
- **Risk level**: HIGH

### 2. Shallow Domain Coverage
- **What happens**: Because ELITE fuses 27 skills, each domain section is a condensed summary. For deep tasks (e.g., SQLite query optimization on a 12GB database), the fused content lacks specific patterns like composite index strategies or adaptive query rewriting.
- **How to prevent**: For deep single-domain tasks, prefer the domain-specific OMEGA skill (OMEGA-DATA for SQL, OMEGA-CODE for Python, OMEGA-LITIGATION-SUPREME for filings). Use ELITE only for cross-domain tasks that genuinely span 3+ domains.
- **Risk level**: MEDIUM

### 3. Missing Startup Context
- **What happens**: ELITE is invoked before the MANBEARPIG startup protocol runs. The skill references DB tables, deadline counts, and evidence statistics that haven't been loaded yet.
- **How to prevent**: Always complete the 5-step startup protocol before invoking any OMEGA/ELITE skill. Verify STARTUP_REPORT.md exists and is current.
- **Risk level**: HIGH

### 4. Stale Skill Manifest
- **What happens**: The 27-skill fusion was generated on a specific date. If source skills have been updated since then, ELITE may contain outdated patterns or missing new capabilities.
- **How to prevent**: Check forge_date in metadata. If source skills have been modified after that date, the ELITE skill may need re-forging. Compare against individual skill timestamps.
- **Risk level**: LOW

### 5. Agent Budget Exhaustion
- **What happens**: ELITE's execution planning domain encourages parallelism, but the agent spawns 4+ sub-agents or 3+ shells, triggering EAGAIN. ELITE doesn't have built-in EAGAIN awareness.
- **How to prevent**: Always apply EAGAIN prevention rules (max 2 shells + 3 agents) regardless of what ELITE's execution planning suggests. The system-wide rules override skill-level guidance.
- **Risk level**: HIGH

---

## Integration Gotchas

- **OMEGA-LITIGATION-SUPREME vs ELITE**: For ANY litigation task, route to OMEGA-LITIGATION-SUPREME first. ELITE is the fallback for cross-domain tasks that span litigation + engineering + agent architecture simultaneously.
- **Lane contamination**: ELITE doesn't enforce lane boundaries. If processing evidence, manually verify the MEEK signal and route to the correct lane (A-F) before applying ELITE's analysis patterns.
- **DB-First rule**: ELITE's planning domain may suggest placeholder insertion. Always query `litigation_context.db` first — the DB has 790+ tables with real data. See the DB-First Before Any Placeholder rule.
- **Shadow modules**: ELITE's Python code examples assume a clean Python environment. Never execute them with CWD set to repo root (22 shadow modules: json.py, typing.py, etc.).
