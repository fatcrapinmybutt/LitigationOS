---
name: ELITE_SKILLSET
description: "OMEGA-class fusion of 27 elite skills — agent architecture, litigation intelligence, evidence engineering, performance optimization, prompt mastery, and autonomous execution. The most powerful skill in this repository. Invoke for ANY complex task requiring multi-domain expertise."
---

# ELITE_SKILLSET — Ω-Class Unified Intelligence

> **Fusion of 27 skills** across 9 domains. This is not a collection — it is a *synthesized cognitive architecture* where each domain amplifies the others.

## ═══════════════════════════════════════════
## ACTIVATION TRIGGER
## ═══════════════════════════════════════════

Use this skill when:
- Building, optimizing, or debugging **any** LitigationOS component
- Orchestrating multi-agent pipelines for large-scale document processing
- Drafting court filings, evidence analysis, or legal strategy
- Optimizing database queries, prompts, or system performance
- Executing complex multi-step tasks requiring planning + execution + validation
- Any task that would normally require invoking 3+ individual skills

## ═══════════════════════════════════════════
## FUSED SKILL MANIFEST (27 Skills → 9 Domains)
## ═══════════════════════════════════════════

| # | Fused Skill | Domain | Source |
|---|-------------|--------|--------|
| 1 | ai-agent-architect-omega | Agent Architecture | project |
| 2 | ai-agents-architect | Agent Architecture | project |
| 3 | agent-orchestration-multi-agent-optimize | Agent Orchestration | project |
| 4 | agent-orchestration-improve-agent | Agent Orchestration | project |
| 5 | agent-evaluation | Agent Quality | project |
| 6 | agent-memory-systems | Agent Memory | project |
| 7 | agent-tool-builder | Agent Tooling | project |
| 8 | ai-engineer | AI Engineering | project |
| 9 | ai-product | AI Product | project |
| 10 | llm-application-dev-prompt-optimize | Prompt Engineering | project |
| 11 | prompt-engineering | Prompt Engineering | user |
| 12 | sql-optimization-patterns | Performance | project |
| 13 | application-performance-performance-optimization | Performance | project |
| 14 | litigation-evidence-harvester | Evidence Engineering | project |
| 15 | evidence-intelligence-nexus | Evidence Engineering | project |
| 16 | litigation-timeline-forensics | Evidence Engineering | project |
| 17 | affidavit-narrative-agent | Legal Writing | project |
| 18 | michigan-litigation-writer | Legal Writing | project |
| 19 | litigation-analysis-engine | Legal Intelligence | project |
| 20 | litigation-case-strategy-architect | Legal Strategy | project |
| 21 | data-engineering-data-pipeline | Data Engineering | project |
| 22 | context-driven-development | Development Process | project |
| 23 | self-improvement | Continuous Improvement | user |
| 24 | executing-plans | Execution | user |
| 25 | writing-plans | Planning | user |
| 26 | fact-checker | Quality Assurance | user |
| 27 | deep-research | Research | user |

## ═══════════════════════════════════════════
## DOMAIN 1: AGENT ARCHITECTURE & ORCHESTRATION
## ═══════════════════════════════════════════
## Fused from: ai-agent-architect-omega, ai-agents-architect,
##   agent-orchestration-multi-agent-optimize, agent-orchestration-improve-agent,
##   agent-evaluation, agent-memory-systems, agent-tool-builder

### Core Architecture Patterns

**ReAct Loop** — The fundamental agent reasoning cycle:
```
Observe → Think → Act → Observe → Think → Act → ...
```
Every agent action follows: perceive state → reason about next step → execute tool → evaluate result. If result is unexpected, re-reason before acting again. Never chain actions without observation.

**Plan-and-Execute** — For complex multi-step tasks:
```
1. PLAN: Decompose goal into ordered subtasks with dependencies
2. EXECUTE: Run each subtask (possibly in parallel if independent)
3. REPLAN: After each subtask, evaluate if plan needs adjustment
4. CONVERGE: Merge results and validate against original goal
```

**Map-Reduce** — For large-scale parallel processing:
```
1. PARTITION: Split data into N batches (sized for GOAWAY-safe execution)
2. MAP: Deploy N agents in parallel (max 3 concurrent, per EAGAIN rules)
3. CHECKPOINT: After each batch completes, persist results to SQL/filesystem
4. REDUCE: Merge all batch results into unified output
5. VALIDATE: Cross-check merged result against source data integrity
```

### Multi-Agent Orchestration Rules

1. **Dependency Graph First**: Before spawning agents, draw the dependency DAG. Independent tasks run in parallel; dependent tasks run sequentially.

2. **Budget Awareness**: Always check resource budgets before spawning:
   - `list_agents` → running < 3 (EAGAIN v3.0 allows 4, but 3 is safer)
   - Checkpoint every 3 agent completions
   - Each agent must complete within 25 minutes (GOAWAY protection)

3. **Prompt Specificity**: Agent prompts must include:
   - Complete context (agents are stateless — no shared memory)
   - Exact file paths (never relative)
   - Expected output format
   - Success/failure criteria
   - Anti-hallucination anchors (verified facts, not assumptions)

4. **Result Preservation**: On EVERY agent completion notification:
   ```
   read_agent → extract results → INSERT INTO session SQL → continue
   ```
   Never defer reading. Context compaction erases unread results.

5. **Failure Recovery**: If an agent fails:
   - Log the error to SQL
   - Adjust the prompt (more specific, smaller scope)
   - Retry once with refined prompt
   - If retry fails, decompose the task further or do it manually

### Agent Memory Architecture

**Three-Tier Memory Model:**
- **Working Memory** (context window): Current conversation + tool results. Ephemeral. ~200K tokens max.
- **Session Memory** (SQL database): Persists across the session. Use for todos, extracted data, agent results, progress tracking. Survives compaction.
- **Persistent Memory** (store_memory tool): Cross-session facts. Use for conventions, patterns, verified information that future sessions need.

**When to use which:**
- Need it in 5 minutes → working memory (just keep it in context)
- Need it in 2 hours → session SQL (INSERT INTO a table)
- Need it next week → store_memory (with citations and reason)

### Tool Design Principles

When building new tools (MCP or otherwise):
1. **Description > Implementation**: The tool description is what the LLM sees. Make it crystal clear.
2. **Narrow scope**: One tool = one action. Don't build Swiss Army knives.
3. **Explicit errors**: Return error messages that tell the agent what to do differently.
4. **Idempotent**: Running the same tool twice with same args should produce same result.
5. **Schema-first**: Define JSON Schema for inputs BEFORE writing implementation.

### Agent Evaluation Framework

Before deploying any agent improvement:
```
1. BASELINE: Measure current success rate, error rate, latency, cost
2. CHANGE: Apply one change at a time (prompt, tool, workflow)
3. TEST: Run against 10+ representative tasks
4. COMPARE: Statistical significance (is the improvement real?)
5. ROLLBACK PLAN: If metrics regress >10%, revert immediately
```

## ═══════════════════════════════════════════
## DOMAIN 2: AI & LLM ENGINEERING
## ═══════════════════════════════════════════
## Fused from: ai-engineer, ai-product, llm-application-dev-prompt-optimize, prompt-engineering

### Production LLM Integration Checklist

Every LLM-powered feature must have:
- [ ] **Structured output** (JSON schema or function calling — never free-text parsing)
- [ ] **Hallucination guardrails** (UNVERIFIED tags, confidence signals, source citations)
- [ ] **Fallback chain** (primary model → secondary → offline heuristic → graceful degradation)
- [ ] **Cost tracking** (tokens in + out per request, aggregated by feature)
- [ ] **Latency budget** (streaming for >2s expected latency)
- [ ] **Prompt versioning** (every prompt change is a versioned commit)
- [ ] **Regression tests** (golden set of 10+ input/output pairs)

### Prompt Engineering — The ELITE Method

**E**xplicit Role + **L**ayered Instructions + **I**RAC Structure + **T**echnique Injection + **E**valuation Anchors

```
SYSTEM PROMPT TEMPLATE:
═══════════════════════
[ROLE] You are a {specific_expertise} with {years} experience in {domain}.

[CONTEXT] You are operating within LitigationOS, a litigation intelligence
system for Michigan family law. Central DB: litigation_context.db.

[TASK] {specific_task_description}

[CONSTRAINTS]
- NEVER fabricate names, dates, case numbers, or statistics
- If uncertain, output [UNVERIFIED] tag with confidence level
- Cite specific sources (table.column, file path, MCR/MCL number)

[FORMAT]
{output_format_specification}

[TECHNIQUE]
Think step-by-step:
1. Identify the legal issue
2. Find applicable rule/statute
3. Apply rule to facts
4. State conclusion with confidence (HIGH/MED/LOW)

[EXAMPLES]
Input: {example_input}
Output: {example_output}
═══════════════════════
```

### Prompt Optimization Techniques

| Technique | When to Use | Token Impact |
|-----------|-------------|-------------|
| **Chain-of-Thought** | Complex reasoning, legal analysis | +20-50 tokens, +40% accuracy |
| **Few-Shot Examples** | Classification, formatting | +100-300 tokens, +60% consistency |
| **Constitutional AI** | Safety-critical outputs (filings) | +30 tokens, prevents hallucination |
| **Role Priming** | Domain expertise needed | +15 tokens, +25% relevance |
| **IRAC Structure** | Legal analysis | +10 tokens, +50% structure |
| **Confidence Signals** | Any RAG output | +5 tokens, catches uncertainty |

### RAG Architecture (for LitigationOS)

```
Query → Embedding → Vector Search (top-k=10) → Rerank (top-k=3) → Context Assembly → LLM → Response
         ↓              ↓                            ↓
    BM25 Hybrid    FTS5 fallback              Source citation
```

**RAG Quality Rules:**
1. Always include source attribution in LLM response
2. Use hybrid search (vector + BM25/FTS5) — neither alone is sufficient
3. Chunk documents at semantic boundaries (paragraphs, sections), not fixed token counts
4. Rerank with cross-encoder before feeding to LLM
5. If retrieval returns <3 relevant chunks, say "insufficient evidence" — don't hallucinate

## ═══════════════════════════════════════════
## DOMAIN 3: EVIDENCE ENGINEERING
## ═══════════════════════════════════════════
## Fused from: litigation-evidence-harvester, evidence-intelligence-nexus,
##   litigation-timeline-forensics

### Evidence Processing Pipeline

```
RAW FILES (6+ drives, 21K+ files)
  │
  ├─ PHASE 1: INVENTORY — SHA256 fingerprint every file
  │     └─ Output: file_manifest.json {path, hash, size, type, modified}
  │
  ├─ PHASE 2: FILTER — Tier by litigation relevance
  │     ├─ Tier 1: Case numbers, party names, legal keywords → READ FIRST
  │     ├─ Tier 2: Large documents with substantive content → READ SECOND
  │     ├─ Tier 3: Small/ambiguous files → READ LAST
  │     └─ Excluded: Code, configs, binaries → SKIP
  │
  ├─ PHASE 3: EXTRACT — Pull structured data from each file
  │     ├─ Dates (all formats: Month DD, YYYY / MM/DD/YYYY / ISO)
  │     ├─ Actors (Andrew, Emily, McNeill, Barnes, Berry, FOC, etc.)
  │     ├─ Event type (order, motion, hearing, incident, filing, etc.)
  │     ├─ Key quotes (IT IS ORDERED, FINDING, SENTENCED, etc.)
  │     └─ Case lane assignment (A/B/C/D/E/F via MEEK signals)
  │
  ├─ PHASE 4: DEDUPLICATE — Content-based dedup (NOT hash-only)
  │     └─ Compare actual content, not just hashes. Move dupes to I:\
  │
  ├─ PHASE 5: TIMELINE — Merge all events into chronological order
  │     └─ {date, event_summary, source_files[], actors[], event_type, lane}
  │
  └─ PHASE 6: EXHIBIT ASSIGNMENT — Only PDFs become exhibits
        ├─ Assign sequential exhibit labels: Exhibit A, B, C...
        ├─ Create Exhibit Index (number, description, Bates range)
        └─ TXT files inform narrative but are NOT cited as exhibits
```

### Evidence Authentication Checklist (MRE 901-903)

Before citing any exhibit in a filing:
- [ ] **Foundation**: Can the source be identified? (who created it, when, how)
- [ ] **Authenticity**: Is it what it purports to be? (MRE 901(a))
- [ ] **Chain of custody**: Can we trace from creation to court submission?
- [ ] **Best evidence**: Is this the original or an admissible copy? (MRE 1001-1004)
- [ ] **Hearsay check**: Does any quoted text fall under a hearsay exception? (MRE 803/804)

### Timeline Forensics Techniques

1. **Date anchoring**: Start with court orders (most reliable dates), then align other events
2. **Gap detection**: If timeline has >30 day gap in active litigation, investigate
3. **Contradiction flagging**: Same event with different dates across sources = flag for review
4. **Temporal clustering**: Group events within same week — they're often causally related
5. **Pattern recognition**: Repeated patterns (e.g., ex parte → jail → appeal cycle) reveal systemic issues

## ═══════════════════════════════════════════
## DOMAIN 4: LEGAL WRITING & STRATEGY
## ═══════════════════════════════════════════
## Fused from: affidavit-narrative-agent, michigan-litigation-writer,
##   litigation-analysis-engine, litigation-case-strategy-architect

### Affidavit Narrative Structure

```
AFFIDAVIT OF [DECLARANT NAME]

STATE OF MICHIGAN  )
                   ) ss.
COUNTY OF MUSKEGON )

I, [FULL NAME], being duly sworn, depose and state as follows:

[CHRONOLOGICAL PARAGRAPHS — numbered sequentially]

1. On [DATE], [EVENT]. See Exhibit [X], attached hereto.
2. On [DATE], [EVENT]. See Exhibit [Y], attached hereto.
...
N. The foregoing statements are true and correct to the best of my
   knowledge, information, and belief.

________________________________
[SIGNATURE]
[PRINTED NAME]

Subscribed and sworn to before me
this ___ day of _________, 20__.

________________________________
Notary Public, State of Michigan
County of _______________
My Commission Expires: __________
```

### IRAC Legal Analysis Framework

For every legal argument:
```
ISSUE:  What is the specific legal question?
RULE:   What statute, court rule, or case law governs?
        (cite MCR, MCL, or Michigan appellate decision)
APPLICATION: How do the facts satisfy/violate the rule?
             (connect specific evidence → specific legal elements)
CONCLUSION: What relief should the court grant?
            (specific, actionable prayer for relief)
```

### Michigan Court Writing Standards

- **Citations**: MCR X.XXX(X)(x) for court rules, MCL XXX.XXX for statutes
- **Case citations**: *Party v Party*, XXX Mich App XXX; XXX NW2d XXX (YEAR)
- **Tone**: Respectful but firm. Never attack opposing counsel personally.
- **Length**: Briefs ≤50 pages (MCR 7.212(B)). Motions: concise.
- **Format**: 12pt Times New Roman, double-spaced, 1" margins
- **Caption**: Include FULL case number, court, division, judge name

### Strategy Architecture

**The Six-Lane Convergence Strategy:**
Each case lane reinforces the others. Evidence from Lane A (custody) supports Lane E (judicial misconduct) which strengthens Lane F (appeal). The ELITE approach:
1. Identify evidence that spans multiple lanes
2. Use strongest evidence in the lane where it has most impact
3. Cross-reference between filings (e.g., "As shown in the pending JTC complaint...")
4. Coordinate filing timing — each filing creates pressure for the next

## ═══════════════════════════════════════════
## DOMAIN 5: DATA ENGINEERING & PIPELINES
## ═══════════════════════════════════════════
## Fused from: data-engineering-data-pipeline, sql-optimization-patterns,
##   application-performance-performance-optimization

### SQLite Performance Patterns (litigation_context.db — 11.87 GB)

**Connection Setup (MANDATORY for every connection):**
```python
PRAGMA busy_timeout = 60000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;   -- 32 MB
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
```

**Query Optimization Rules:**
1. **Consolidate COUNT(*)** — Use single query with subqueries, not N round-trips
2. **executemany()** — Batch inserts, never row-by-row in loops
3. **Explicit columns** — Name columns, never SELECT *
4. **Composite indexes** — Match WHERE clause column order
5. **EXPLAIN QUERY PLAN** — Check before deploying any new query
6. **FTS5 over LIKE** — Route `LIKE '%term%'` through adaptive_query_rewriter.py

**Batch Processing Pattern:**
```python
BATCH_SIZE = 500
rows = []
for item in source:
    rows.append(transform(item))
    if len(rows) >= BATCH_SIZE:
        conn.executemany("INSERT OR IGNORE INTO target VALUES (?, ?)", rows)
        conn.commit()
        rows.clear()
if rows:  # flush remainder
    conn.executemany("INSERT OR IGNORE INTO target VALUES (?, ?)", rows)
    conn.commit()
```

### Pipeline Architecture (16-Phase OMEGA)

```
Phase 0:  Safety Snapshot (SHA-256 manifest)
Phase 1:  Inventory (scan all drives)
Phase 2:  Dedup (content-based, NOT hash-only)
Phase 3:  Classify (MEEK lane assignment)
Phase 4a-e: Extract (PDF/DOCX/structured/atomize/archive)
Phase 5:  LEXOS Brain Feed
Phase 6:  Gap Analysis (EGCP scoring)
Phase 7a-c: Graph → Synthesis → Knowledge Merge
Phase 8:  Litigation Refresh
Phase 9:  MCP Ingest
Phase 10-12: Judicial Analysis → Legal Discovery → Rule Audit
Phase 13-16: Refine → Finalize → Validate → Desktop Offload
```

**Pipeline Reliability Rules:**
- Checkpoint after every phase
- Each phase is idempotent (re-runnable without duplication)
- Crash recovery: resume from last checkpoint
- Progress tracking in SQL (not just console output)

## ═══════════════════════════════════════════
## DOMAIN 6: PLANNING & EXECUTION
## ═══════════════════════════════════════════
## Fused from: writing-plans, executing-plans, context-driven-development

### Plan Structure (The ELITE Format)

```markdown
## Goal
[1-2 sentence statement of what success looks like]

## Approach
[Brief description of the strategy — which patterns, which tools]

## Tasks
Each task must have:
- [ ] **ID**: descriptive-kebab-case
- [ ] **What**: Exact action to take
- [ ] **Where**: Exact file paths
- [ ] **How**: Commands or code to run
- [ ] **Verify**: How to confirm it worked
- [ ] **Depends on**: Which task(s) must complete first

## Risks
[Known risks and mitigations]
```

### Execution Protocol

1. **Load plan** → Read plan.md, load SQL todos
2. **Query ready** → Find todos where all dependencies are 'done'
3. **Mark in_progress** → UPDATE status before starting
4. **Execute** → Do the work (using agents, tools, or manual)
5. **Verify** → Run the verification step from the plan
6. **Mark done** → UPDATE status after verification passes
7. **Checkpoint** → Save progress every 3 completions
8. **Report** → Brief status to user after each wave

### Context Artifacts (Persistent Project Knowledge)

Maintain these as living documents:
- **copilot-instructions.md**: System identity, architecture, rules, party info
- **AGENTS.md**: Agent-specific instructions and workflow
- **plan.md**: Current session's active plan
- **LEARNINGS.md**: Session-specific learnings (promote to instructions if persistent)

## ═══════════════════════════════════════════
## DOMAIN 7: QUALITY ASSURANCE & FACT-CHECKING
## ═══════════════════════════════════════════
## Fused from: fact-checker, agent-evaluation, self-improvement

### The Zero-Hallucination Protocol

**For ANY generated content (filings, analyses, summaries, dashboards):**

1. **VERIFY before citing**: Every statistic must trace to a specific DB query
   ```sql
   -- Before writing "305 interference incidents":
   SELECT COUNT(*) FROM evidence_quotes WHERE evidence_category = 'interference';
   -- Record the actual number, not an estimate
   ```

2. **Tag uncertainty**: If a fact cannot be verified, tag it:
   - `[VERIFIED — source: table.column]` → safe to use in filings
   - `[UNVERIFIED — needs confirmation]` → do NOT use in sworn documents
   - `[ANDREW_REQUIRED]` → only after checking DB + filesystem + reference files

3. **Party identity lockdown**: NEVER invent names. NEVER invent bar numbers.
   The verified party table in copilot-instructions.md is the ONLY source of truth.

4. **Cross-reference check**: Before filing any document:
   - Names match verified party table
   - Case numbers match lane assignments
   - Dates are internally consistent
   - Gender references are correct (L.D.W. is Andrew's SON)
   - Statistics match DB queries

### Continuous Improvement Loop

```
OBSERVE → document what went wrong (ERRORS.md)
ANALYZE → identify root cause and pattern
FIX → apply targeted correction
PREVENT → add rule/check/test to prevent recurrence
PROMOTE → if pattern is persistent, add to copilot-instructions.md
```

### Self-Audit Triggers

Run a self-audit when:
- Starting a new session (MANBEARPIG startup protocol)
- Before any court filing (pre-filing QA)
- After any large-scale generation (encyclopedia, brief, complaint)
- After agent failures (what went wrong, how to prevent)

## ═══════════════════════════════════════════
## DOMAIN 8: RESEARCH & INVESTIGATION
## ═══════════════════════════════════════════
## Fused from: deep-research, fact-checker

### Research Protocol

1. **Clarify the question** — What specifically needs to be answered?
2. **Multi-source search** — DB queries + filesystem search + web search
3. **Source hierarchy** — Court records > official filings > testimony > correspondence > inference
4. **Credibility assessment** — Primary sources > secondary > tertiary
5. **Gap identification** — What CAN'T we find? Document the gaps.
6. **Synthesis** — Combine findings into coherent narrative with citations
7. **Confidence rating** — HIGH (multiple confirming sources) / MEDIUM (single source) / LOW (inference only)

### Prior Work Discovery (MANDATORY before any document creation)

```powershell
# Search ALL drives for existing versions
fd --type f "motion" C:\Users\andre\LitigationOS\ I:\ F:\ G:\
rg -l "disqualification" C:\Users\andre\LitigationOS\ --type md --type txt
```

**NEVER create from scratch** when prior work exists. Find → Diff → Merge → Improve.

## ═══════════════════════════════════════════
## DOMAIN 9: SECURITY & DATA INTEGRITY
## ═══════════════════════════════════════════
## Derived from: security-best-practices + LitigationOS rules

### Data Protection Rules

1. **NO HARD DELETIONS** — Move to I:\ or Recycle Bin. Never `rm`, `del`, or `os.remove()`.
2. **SHA-256 manifests** — Every evidence file has a hash. Verify before and after operations.
3. **Chain of custody** — Log every file move, copy, or transform with timestamp and actor.
4. **PII protection** — L.D.W. initials only per MCR 8.119(H). Never full name in filings.
5. **Backup before destructive ops** — Always create a safety snapshot before bulk operations.
6. **Local-only** — No cloud providers, no API keys, no remote inference. Everything stays on-device.
7. **Shadow module safety** — Never run Python from repo root (22 shadow modules). Use safe_shell.py.

### Integrity Verification

After any bulk operation:
```python
# Verify file count matches expected
assert actual_count == expected_count, f"Missing {expected_count - actual_count} files"

# Verify no data loss
for file_hash in original_manifest:
    assert file_hash in post_operation_manifest, f"Lost file: {file_hash}"
```

## ═══════════════════════════════════════════
## OPERATIONAL PROTOCOL — HOW TO USE THIS SKILL
## ═══════════════════════════════════════════

### Quick Decision Matrix

| Task Type | Primary Domain | Key Technique |
|-----------|---------------|---------------|
| Read thousands of files | Domain 3 (Evidence) + Domain 1 (Agents) | Map-Reduce with 3 parallel agents |
| Draft court filing | Domain 4 (Legal) + Domain 7 (QA) | IRAC + Zero-Hallucination Protocol |
| Optimize slow query | Domain 5 (Data) | EXPLAIN → Index → executemany |
| Build new agent | Domain 1 (Architecture) + Domain 2 (AI) | ReAct loop + ELITE prompt method |
| Fix a bug | Domain 7 (QA) + Domain 6 (Planning) | Isolate → Root cause → Test → Fix → Prevent |
| Research legal issue | Domain 8 (Research) + Domain 4 (Legal) | Multi-source + IRAC analysis |
| Process evidence | Domain 3 (Evidence) + Domain 5 (Data) | Pipeline + Batch + Checkpoint |
| Improve a prompt | Domain 2 (AI) | ELITE method + A/B test + regression check |
| Plan multi-step work | Domain 6 (Planning) | ELITE plan format + SQL todos + dependency DAG |

### The ELITE Execution Loop

```
For ANY complex task:

1. ASSESS — What domains does this task touch? (usually 2-3)
2. PLAN — Use Domain 6 to create structured plan with todos
3. RESEARCH — Use Domain 8 to find existing work and fill knowledge gaps
4. EXECUTE — Use Domain 1 for agent orchestration, Domain 5 for data work
5. VERIFY — Use Domain 7 for fact-checking and quality assurance
6. IMPROVE — Use self-improvement loop to capture learnings
```

## ═══════════════════════════════════════════
## ANTI-PATTERNS (learned from 200+ sessions)
## ═══════════════════════════════════════════

| Anti-Pattern | Why It Fails | ELITE Alternative |
|-------------|-------------|-------------------|
| Spawn 5+ agents at once | EAGAIN pipe overflow | Max 3 concurrent, checkpoint between waves |
| Read 1000 files in one agent | GOAWAY 503 at 27 min | Batch into 200-file chunks per agent |
| Use `python -c "..."` in shell | Backslash/quote hell | Write .py file, execute, clean up |
| Trust LLM-generated statistics | Hallucinated numbers in filings | Always verify with DB query |
| Create from scratch | Duplicate prior work, lose history | Search all drives first, then build on existing |
| Hard-delete files | Lose evidence, break chain of custody | Move to I:\ or Recycle Bin |
| Skip checkpointing | Lose 40 min of agent work on crash | Checkpoint to SQL every 3 agent completions |
| Assume column names | Schema changed, query crashes | PRAGMA table_info() before first query |
| Use SELECT * | Wastes I/O, breaks on schema change | Name columns explicitly |
| Defer read_agent | Context compaction erases results | Read IMMEDIATELY on completion notification |
