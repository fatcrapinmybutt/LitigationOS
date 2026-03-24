# HYDRA Protocol — Copilot Agent Orchestration Instructions
# ══════════════════════════════════════════════════════════

## What is HYDRA?

**H**yper-resilient **U**niversal **D**eath-proof **R**untime **A**rchitecture.

Seven interlocking systems that make agents immortal:

```
┌──────────────────────────────────────────────────────────────┐
│                    HYDRA PROTOCOL v1.0                        │
│                                                              │
│  H1 PHOENIX PROTOCOL     — Dead agents auto-respawn          │
│  H2 STREAMING RESULTS    — Write-ahead log, never lose work  │
│  H3 COGNITIVE SHARDING   — Smart task decomposition          │
│  H4 PROMPT EVOLUTION     — Failed prompts auto-improve       │
│  H5 PREDICTIVE TIMEOUT   — Kill before GOAWAY kills you      │
│  H6 REDUNDANT DISPATCH   — Critical tasks get backup agent   │
│  H7 GENETIC MEMORY       — Learn from every agent death      │
│                                                              │
│  Engine: 00_SYSTEM/hydra/hydra_protocol.py                   │
│  Data:   temp/hydra/ (shard results, journals, phoenix logs) │
│  SQL:    hydra_shards, hydra_phoenix_log, hydra_genetic_mem  │
└──────────────────────────────────────────────────────────────┘
```

## How to Use (Copilot Main Loop Integration)

### Step 1: Before dispatching any agent, HYDRA-wrap the prompt

Instead of:
```
task(prompt="Scan I:\ for evidence files")
```

Do:
```
task(prompt="""
### 🔥 HYDRA STREAMING PROTOCOL

**RULE 1:** Write results to `temp/hydra/{shard_id}.json` every 20 items.
**RULE 2:** Append heartbeats to `temp/hydra/{shard_id}.journal.jsonl`.
**RULE 3:** At minute 4 of 5: STOP and write whatever you have.
**RULE 4:** Partial results > no results. A Phoenix agent picks up leftovers.

### Task
Scan I:\ for evidence files...
""")
```

### Step 2: Every 2 minutes, run the Watchdog

```sql
-- Find agents that have been running too long with no output
SELECT shard_id, agent_id, 
       ROUND((julianday('now') - julianday(started_at)) * 1440, 1) as minutes
FROM hydra_shards
WHERE status = 'dispatched'
AND started_at < datetime('now', '-8 minutes');
```

For each stale shard:
1. Check `temp/hydra/{shard_id}.json` for partial results
2. If partial results exist → salvage and respawn for remainder
3. If no results → mark stale, evolve prompt, respawn

### Step 3: On agent death, trigger Phoenix

```python
# In the orchestrator's error handler:
phoenix = PhoenixProtocol()
partial, items = phoenix.salvage_results(shard_id)
evolved_prompt = PromptEvolver.evolve(original_prompt, "goaway", retry_count)
# Dispatch new agent with evolved_prompt
```

### Step 4: Record outcomes in Genetic Memory

```sql
-- After success:
INSERT INTO hydra_genetic_memory (agent_dna, complexity, outcome, elapsed_minutes, items_processed, prompt_length)
VALUES ('scanner', 'moderate', 'success', 7.2, 150, 1200);

-- After failure:
INSERT INTO hydra_genetic_memory (agent_dna, complexity, outcome, elapsed_minutes, failure_reason)
VALUES ('extractor', 'complex', 'failure', 22.5, 'goaway');
```

## Agent DNA Types

| DNA | Best For | Items/Min | Max Safe Budget |
|-----|----------|-----------|-----------------|
| scanner | File/drive scanning | ~100 | 12 min |
| extractor | Content extraction from PDFs/DOCX | ~10 | 15 min |
| analyzer | Legal/evidence analysis | ~5 | 12 min |
| grader | Document quality scoring | ~3 | 10 min |
| builder | Document generation | ~2 | 18 min |
| researcher | Legal research, DB queries | ~8 | 14 min |
| organizer | File org, dedup, consolidation | ~50 | 15 min |

## Complexity Classification

| Level | Items | Time Est | Action |
|-------|-------|----------|--------|
| trivial | <10 | <1 min | Single agent, no sharding |
| simple | 10-50 | 1-3 min | Single agent, streaming |
| moderate | 50-200 | 3-8 min | May need sharding |
| complex | 200-1000 | 8-15 min | Must shard |
| epic | 1000+ | 15-30 min | Multi-wave sharding |
| legendary | massive | >30 min | Redundancy + streaming + sharding |

## The Golden Rules

1. **Never dispatch a task expected to take >20 minutes** — shard it first
2. **Every agent prompt includes streaming instructions** — write to disk as you work
3. **Every agent result is cached in SQL immediately** — survives compaction
4. **Failed agents get evolved prompts** — same mistake never happens twice
5. **Critical tasks get redundant agents** — first to finish wins
6. **Genetic memory improves over time** — the system learns what works
7. **Phoenix never gives up until retry 3** — cut off one head, two grow back
