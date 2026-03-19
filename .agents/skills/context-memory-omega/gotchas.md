# Gotchas — context-memory-omega

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "I already stored this fact — I can trust it" | Stored facts become stale as code evolves. A fact from 3 weeks ago about DB schema may reference columns that were renamed or dropped. | Queries crash with `no such column`, or worse — filings cite nonexistent evidence tables. |
| 2 | "More stored memories = better recall" | Flooding store_memory with low-value facts pollutes retrieval. 200 memories about file paths drown out the 5 critical legal conventions. | Agent wastes tokens reading irrelevant memories, misses the one fact that matters, produces wrong output. |
| 3 | "The memory has a citation so it must be accurate" | Citations point to source at storage time. If the source file was edited, moved, or deleted, the citation is a dead link and the fact may be wrong. | Agent confidently cites a dead reference, user trusts it, files a motion with outdated legal authority. |
| 4 | "Session SQL has my state — I don't need to re-check the DB" | Session SQL captures a snapshot. The central litigation_context.db changes between sessions (new evidence ingested, deadlines updated, claims modified). | Agent reports "305 evidence items" when there are now 412, or misses a deadline added yesterday. |
| 5 | "I'll store everything and filter later" | Context windows are finite (200K tokens). Loading 50 memories + session state + conversation can consume 40%+ of the window before any work begins. | Context overflow triggers compaction, which drops agent results and conversation history — work is LOST. |
| 6 | "The agent_memory MCP will handle dedup" | agent_memory stores verbatim. If you store "litigation_context.db has 694 tables" and later "litigation_context.db has 782 tables", both persist. Retrieval returns the stale one first (older = higher ID). | Agent uses outdated DB stats in generated filings. Past sessions generated "694 tables" when the DB had grown to 790+. |
| 7 | "I recalled a prior session — that context is still valid" | session_recall.py returns summaries of past sessions. Those sessions may have made changes that were later reverted, or worked on a branch that was never merged. | Agent builds on abandoned work, recreates files that were intentionally deleted, or follows a deprecated architecture. |

---

## Common Failure Modes

### 1. Memory-Reality Drift
- **What happens**: Stored facts diverge from actual system state over time. DB schema evolves, file paths change, deadlines pass.
- **How to prevent**: Before using any stored memory in a critical path (filings, DB queries, evidence citations), verify it against the live source. Run `PRAGMA table_info()` before trusting stored column names. Check file existence before citing paths.
- **Risk level**: HIGH

### 2. Context Window Exhaustion
- **What happens**: Loading too many memories + session state + conversation history exceeds the context window. Compaction kicks in and silently drops agent results, earlier conversation turns, or memory content.
- **How to prevent**: Budget context deliberately. Load only memories relevant to the current task. Use SQL queries to fetch specific data rather than loading entire memory stores. Keep session state lean.
- **Risk level**: HIGH

### 3. Stale Cross-Session Recall
- **What happens**: session_recall returns summaries from sessions that worked on since-abandoned approaches. Agent follows outdated plans or rebuilds deleted artifacts.
- **How to prevent**: Always check recency of recalled sessions. Cross-reference recalled session work against current filesystem and DB state. Treat recalled sessions as hints, not instructions.
- **Risk level**: MEDIUM

### 4. Citation Decay
- **What happens**: Stored memories reference files, line numbers, or DB tables that no longer exist in their original form. The citation looks authoritative but points to nothing.
- **How to prevent**: When retrieving a memory with a citation, verify the cited source still exists and still says what the memory claims. Use `view` or `grep` to spot-check.
- **Risk level**: MEDIUM

### 5. Duplicate Memory Accumulation
- **What happens**: Multiple sessions store overlapping facts with slightly different wording. Retrieval returns 5 near-identical memories, wasting context tokens and creating confusion when versions conflict.
- **How to prevent**: Before storing a new memory, search existing memories for the same topic. Prefer updating or superseding existing facts over creating new ones. Use specific, unique subjects.
- **Risk level**: LOW

---

## Integration Gotchas

- **store_memory vs session SQL**: Use `store_memory` only for facts that persist across sessions (conventions, verified commands, architecture decisions). Use session SQL for ephemeral task tracking within a session. Mixing them leads to stale session-specific data living forever in memory.
- **agent_memory MCP vs store_memory**: These are separate storage systems. Facts stored in one are NOT retrievable from the other. Know which system you're writing to and reading from.
- **session_store (read-only)**: The session_store DB contains historical session data searchable via FTS5. It is read-only — you cannot update or delete entries. Stale entries persist forever.
- **MANBEARPIG startup hook**: The startup hook reads memories and generates a report. If memories are polluted with stale facts, the startup report will be misleading from the very first message.
