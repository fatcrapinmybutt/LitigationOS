# Agent Fleet Optimization Framework — LitigationOS (v1.0)

> **Date:** 2025-07-18 | **Scope:** 155+ agents across 5 fleets | **Base class:** `Agent9999` (`00_SYSTEM/pipeline/agents/agent_base.py`)
>
> **Targets:** 15% improvement in task success rate · 25% reduction in user corrections · Zero EAGAIN incidents

---

## Table of Contents

1. [Performance Baseline Metrics](#1-performance-baseline-metrics)
2. [Failure Mode Classification](#2-failure-mode-classification)
3. [Optimization Strategies](#3-optimization-strategies)
4. [Agent Architecture Patterns](#4-agent-architecture-patterns)
5. [Continuous Learning Protocol](#5-continuous-learning-protocol)
6. [RAG Integration](#6-rag-integration)
7. [Automation Workflows](#7-automation-workflows)
8. [Tool Schema Improvements](#8-tool-schema-improvements)
9. [Implementation Roadmap](#9-implementation-roadmap)

---

## 1. Performance Baseline Metrics

### 1.1 Metric Definitions

Every agent inherits `AgentStats` (processed, skipped, errored, elapsed) and returns `AgentResult` (status: SUCCESS | FATAL | CRASH). The optimization framework layers fleet-wide analytics on top of these primitives.

| Metric | Formula | Target | Measured From |
|--------|---------|--------|---------------|
| **Task Completion Rate** | `processed / total` per agent | ≥ 95% per tier | `AgentStats.processed / AgentStats.total` |
| **Error Rate** | `errored / total` per agent | ≤ 2% per tier | `AgentStats.errored / AgentStats.total` |
| **Skip Rate** | `skipped / total` per agent | ≤ 5% (informational) | `AgentStats.skipped / AgentStats.total` |
| **Throughput** | `processed / elapsed` (items/sec) | Baseline + 20% | `AgentStats.rate` property |
| **Mean Recovery Time** | avg seconds from error to next successful item | ≤ 5s | `agent_log` timestamps between ERROR→OK |
| **Deadman Trigger Rate** | deadman activations / total runs | ≤ 1% | `agent_log WHERE level = 'DEADMAN'` |
| **Checkpoint Efficiency** | checkpoint saves / crash recoveries that used them | 100% crash-resume | `agent_checkpoints` table usage |
| **Tool Selection Accuracy** | correct tool chosen / total tool invocations | ≥ 90% | MCP tool call logs |
| **Token Consumption** | tokens per task completion | Baseline - 25% | Inference engine call tracking |
| **Recovery Success Rate** | recovered errors / total errors across 7 layers | ≥ 85% | `agent_log` ERROR→RETRY→OK chains |

### 1.2 Per-Tier Baselines

Collect baselines by querying `agent_log` from `master_index.db`:

```sql
-- Fleet health dashboard query
SELECT
    CASE
        WHEN agent_id LIKE 'A%' OR agent_id LIKE 'B%' OR agent_id LIKE 'C%' THEN 'Lane1-IO'
        WHEN agent_id LIKE 'J%' OR agent_id LIKE 'K%' OR agent_id LIKE 'L%' THEN 'Lane2-Intel'
        WHEN agent_id LIKE 'F%' THEN 'Convergence'
        ELSE 'Other'
    END AS tier,
    COUNT(DISTINCT agent_id) AS agent_count,
    SUM(items_processed) AS total_processed,
    SUM(items_errored) AS total_errored,
    ROUND(100.0 * SUM(items_errored) / NULLIF(SUM(items_processed) + SUM(items_errored), 0), 2) AS error_pct
FROM agent_log
WHERE level IN ('DONE', 'ERROR', 'FATAL', 'CRASH')
GROUP BY tier;
```

### 1.3 Fleet Scoreboard Schema

Add a `fleet_metrics` table to `master_index.db` for longitudinal tracking:

```sql
CREATE TABLE IF NOT EXISTS fleet_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,           -- UUID per pipeline run
    agent_id TEXT NOT NULL,
    tier TEXT NOT NULL,
    total_items INTEGER,
    processed INTEGER,
    skipped INTEGER,
    errored INTEGER,
    elapsed_seconds REAL,
    throughput REAL,                -- items/sec
    deadman_triggers INTEGER DEFAULT 0,
    checkpoint_count INTEGER DEFAULT 0,
    status TEXT,                    -- SUCCESS/FATAL/CRASH
    recorded_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_fleet_metrics_tier
    ON fleet_metrics(tier, recorded_at);
CREATE INDEX IF NOT EXISTS idx_fleet_metrics_agent
    ON fleet_metrics(agent_id, recorded_at);
```

Populate from `AgentResult` at the end of every `run()`:

```python
# In agent_orchestrator.py, after each agent completes:
def record_metrics(result: AgentResult, run_id: str, tier: str):
    db.execute(
        """INSERT INTO fleet_metrics
           (run_id, agent_id, tier, total_items, processed, skipped,
            errored, elapsed_seconds, throughput, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (run_id, result.agent_id, tier, result.stats.total,
         result.stats.processed, result.stats.skipped,
         result.stats.errored, result.stats.elapsed,
         result.stats.rate, result.status)
    )
```

---

## 2. Failure Mode Classification

### 2.1 Severity Matrix

| ID | Failure Mode | Severity | Status | Root Cause | Mitigation |
|----|-------------|----------|--------|------------|------------|
| **F01** | EAGAIN / pipe overflow | CRITICAL | SOLVED | >4 concurrent pipe-producing processes overflow 64KB Windows pipe buffers | Zero-pipe architecture: main session uses only `view/edit/grep/glob/sql`; all execution delegated to `task` agents with isolated pipes |
| **F02** | Shadow module imports | HIGH | SOLVED | 22 files in repo root shadow stdlib (`json.py`, `typing.py`, etc.) | Renamed files; `safe_shell.py` sets CWD away from root; `srun`/`spy` wrappers enforce this |
| **F03** | SQLite BUSY/locked | HIGH | MANAGED | Concurrent agents writing to same DB | `db_lock_manager.py` enforces max 3 connections; `_db_execute()` retries 8× with random jitter; WAL mode + `busy_timeout=120000` |
| **F04** | Agent timeout (deadman) | MEDIUM | MANAGED | Single item takes >120s; common with large PDFs or corrupt files | `deadman_timeout=120s` auto-skips stuck items; `item_timeout=30s` per-item cap via `ThreadPoolExecutor` |
| **F05** | Context overflow | MEDIUM | PARTIAL | Large file processing (>50MB) or unbounded output floods context window | `_read_file_content()` skips files >50MB; output cap of 100 lines per shell; redirect large output to temp files |
| **F06** | Cross-lane contamination | LOW | MANAGED | MEEK signal misclassification routes evidence to wrong case lane | `LaneCrossContaminationError` (non-fatal, skip-item); detection priority E→D→F→C→A→B; compiled regexes in `config.py` |
| **F07** | GOAWAY/503 timeout | HIGH | PARTIAL | Copilot agent sessions killed after 27-40 minutes | Checkpoint every 10 min or every 3 agent completions; SQL `todos` persistence; `_save_checkpoint()` after every batch |
| **F08** | Disk space exhaustion | CRITICAL | MANAGED | DB grows beyond available space on drive | `_diagnose()` checks free space; raises `FatalAgentError` if <0.5GB free |
| **F09** | DB corruption | CRITICAL | MANAGED | Power loss during WAL write | `_diagnose()` runs `PRAGMA integrity_check`; WAL + `synchronous=NORMAL` provides crash safety |
| **F10** | Thread connection leak | MEDIUM | SOLVED | Per-thread DB connections not closed after parallel batch | `_cleanup_thread_connections()` called after every parallel batch; `_close_db()` closes main + central + thread-local |

### 2.2 Error Classification for `agent_log`

Extend the log schema to classify errors for pattern detection:

```python
# Failure classifier — add to Agent9999._log() for ERROR/CRASH levels
FAILURE_CLASSIFIERS = {
    "EAGAIN":       lambda msg: "EAGAIN" in msg or "pipe" in msg.lower(),
    "SQLITE_BUSY":  lambda msg: "locked" in msg or "busy" in msg.lower(),
    "TIMEOUT":      lambda msg: "timeout" in msg.lower() or "deadman" in msg.lower(),
    "DISK":         lambda msg: "disk" in msg.lower() or "space" in msg.lower(),
    "IMPORT":       lambda msg: "import" in msg.lower() or "module" in msg.lower(),
    "LANE_CROSS":   lambda msg: "contamination" in msg.lower() or "wrong lane" in msg.lower(),
    "PERMISSION":   lambda msg: "permission" in msg.lower() or "access denied" in msg.lower(),
    "CORRUPT":      lambda msg: "corrupt" in msg.lower() or "malformed" in msg.lower(),
}

def classify_failure(detail: str) -> str:
    for label, test in FAILURE_CLASSIFIERS.items():
        if test(detail):
            return label
    return "UNKNOWN"
```

### 2.3 Escalation Protocol

```
Item Error → _safe_process_item retry (5× with jitter)
           → SkipItemError (logged, item skipped)
           → Error rate >10% triggers _diagnose()
           → FatalAgentError → agent stops, returns FATAL
           → Unhandled Exception → agent stops, returns CRASH
           → Orchestrator sees FATAL/CRASH → flags tier, continues other agents
           → Fleet-level: >3 FATAL in same tier → pause tier, notify
```

---

## 3. Optimization Strategies

### 3.1 Workload Distribution

Route tasks to the right model tier based on complexity:

```python
# Model selection matrix
TASK_MODEL_MAP = {
    # Simple / high-volume → fast model (Haiku equivalent = LocalAI heuristic)
    "file_classification": "local_ai",
    "lane_detection": "local_ai",
    "entity_extraction": "local_ai",
    "dedup_comparison": "local_ai",

    # Medium complexity → standard model (Sonnet equivalent = MANBEARPIG TF-IDF + BM25)
    "evidence_scoring": "manbearpig",
    "summarization": "manbearpig",
    "citation_validation": "manbearpig",
    "gap_analysis": "manbearpig",

    # Complex / creative → premium model (Opus equivalent = full MANBEARPIG + semantic)
    "brief_drafting": "manbearpig_full",
    "judicial_analysis": "manbearpig_full",
    "impeachment_detection": "manbearpig_full",
    "settlement_calculation": "manbearpig_full",
}

def select_model(task_type: str) -> str:
    return TASK_MODEL_MAP.get(task_type, "manbearpig")
```

### 3.2 Parallel Execution Rules

Derived from the EAGAIN prevention protocol — these are hard-won constraints:

| Rule | Limit | Rationale |
|------|-------|-----------|
| Background agents (Copilot `task` tool) | Max 2 concurrent | Each agent spawns internal pipes |
| Async PowerShell shells | Max 2 concurrent | Each shell = 3 pipes = 192KB buffer |
| Combined pipe-producing processes | Max 4 total | 2 shells + 2 agents = 12 pipes = safe |
| Spawn cooldown | 2 seconds minimum | Prevents buffer flood from burst spawning |
| Shell + agent in same turn | **NEVER** | Sequential only |
| Pipeline agent threads (`parallel_workers`) | Max 4 per agent | Thread pool + per-thread DB connections |

```python
# In agent_base.py — parallel worker auto-tuning
@property
def optimal_workers(self) -> int:
    """Auto-select parallel workers based on task type and system load."""
    if self.stats.total < 10:
        return 1  # Not worth parallelism overhead
    if self.stats.total > 1000:
        return min(4, self.parallel_workers)  # Cap at 4 for large batches
    return min(2, self.parallel_workers)  # Default: modest parallelism
```

### 3.3 Context Compression

Reduce token waste when passing data between agents:

```python
# Summarize large outputs before inter-agent handoff
def compress_for_handoff(content: str, max_tokens: int = 2000) -> str:
    """Compress content for inter-agent communication."""
    if len(content) < max_tokens * 4:  # ~4 chars per token
        return content

    # Strategy 1: Extract structured data (tables, lists, key-value pairs)
    lines = content.split('\n')
    key_lines = [l for l in lines if any(
        marker in l for marker in [':', '|', '-', '*', '##', 'ERROR', 'FATAL', 'WARNING']
    )]

    if len('\n'.join(key_lines)) < max_tokens * 4:
        return '\n'.join(key_lines)

    # Strategy 2: Head + tail with summary
    head = '\n'.join(lines[:20])
    tail = '\n'.join(lines[-20:])
    return f"{head}\n\n... [{len(lines) - 40} lines omitted] ...\n\n{tail}"
```

### 3.4 Cost-Aware Orchestration

Track resource consumption per agent to identify optimization targets:

```sql
-- Identify most expensive agents (time × items)
SELECT
    agent_id,
    COUNT(*) AS runs,
    AVG(elapsed_seconds) AS avg_time,
    AVG(CAST(errored AS REAL) / NULLIF(total_items, 0)) AS avg_error_rate,
    SUM(total_items) AS lifetime_items
FROM fleet_metrics
GROUP BY agent_id
ORDER BY avg_time DESC
LIMIT 20;
```

### 3.5 Caching Strategy

Use `agent_memory` (central DB) and `extracted_text` (master_index.db) for cross-agent caching:

```python
# Cache-first pattern for any expensive computation
def cached_compute(self, cache_key: str, compute_fn, ttl_hours: int = 24):
    """Check agent_memory cache before computing. Store result if computed."""
    # 1. Check cache
    memories = self.recall(key=cache_key, limit=1)
    if memories:
        age_hours = (time.time() - parse_timestamp(memories[0]['updated_at'])) / 3600
        if age_hours < ttl_hours:
            return json.loads(memories[0]['value'])

    # 2. Compute
    result = compute_fn()

    # 3. Store
    self.remember(cache_key, json.dumps(result, default=str), category='cache')
    return result
```

### 3.6 Pre-warming

Load common context into agent prompts before task execution:

```python
# Pre-warm agent with relevant memories and recent errors
def pre_warm(self):
    """Load context before main processing loop."""
    # Recall past errors for this agent (self-healing)
    past_errors = self.recall_errors(limit=5)
    if past_errors:
        self._log("PREWARM", f"Loaded {len(past_errors)} past error patterns")

    # Load lane-specific signals
    lane_memories = self.recall(category='lane_config', limit=10)

    # Load recent checkpoint for crash-resume awareness
    last_checkpoint = self.restore_checkpoint()
    if last_checkpoint:
        self._log("PREWARM", f"Restored checkpoint: {list(last_checkpoint.keys())}")
```

---

## 4. Agent Architecture Patterns

### 4.1 ReAct Loop (Current Pattern — Enhanced)

The `Agent9999.react_loop()` already implements Thought→Action→Observation. Enhancements:

```python
# Enhanced ReAct with iteration budget and early termination
class EnhancedReActMixin:
    """Drop-in mixin for Agent9999 subclasses needing smarter ReAct loops."""

    def react_loop_enhanced(self, task: str, max_iterations: int = 10,
                            confidence_threshold: float = 0.85) -> dict:
        """ReAct loop with confidence-based early termination."""
        context = {"task": task, "history": [], "iteration": 0, "confidence": 0.0}

        for i in range(max_iterations):
            context["iteration"] = i + 1

            reasoning = self._reason(context)
            action, action_result = self._act(reasoning, context)
            observation = self._observe(action, action_result, context)

            # Confidence estimation from observation quality
            confidence = self._estimate_confidence(observation, context)
            context["confidence"] = confidence

            context["history"].append({
                "iteration": i + 1,
                "reasoning": reasoning,
                "action": action,
                "result": str(action_result)[:500],
                "observation": observation,
                "confidence": confidence,
            })

            if observation.startswith("DONE") or confidence >= confidence_threshold:
                return {"status": "SUCCESS", "iterations": i + 1,
                        "result": action_result, "confidence": confidence}

            # Diminishing returns detection: 3 iterations with no confidence gain → stop
            if i >= 2:
                recent = [h["confidence"] for h in context["history"][-3:]]
                if max(recent) - min(recent) < 0.05:
                    self._log("REACT", "Diminishing returns — early stop")
                    return {"status": "PLATEAU", "iterations": i + 1,
                            "result": action_result, "confidence": confidence}

        return {"status": "MAX_ITERATIONS", "iterations": max_iterations,
                "result": None, "confidence": context["confidence"]}

    def _estimate_confidence(self, observation: str, context: dict) -> float:
        """Estimate confidence from observation quality. Override for domain-specific logic."""
        if observation.startswith("DONE"):
            return 1.0
        if "error" in observation.lower() or "failed" in observation.lower():
            return max(0.0, context.get("confidence", 0.5) - 0.2)
        return min(1.0, context.get("confidence", 0.5) + 0.1)
```

### 4.2 Plan-Execute Pattern

For complex multi-step tasks (e.g., filing assembly), plan before executing:

```python
class PlanExecuteAgent(Agent9999):
    """Agent that generates a plan, then executes each step with replanning on failure."""

    def _get_work_items(self) -> list:
        # Phase 1: Generate plan
        plan = self._generate_plan()
        self.remember("current_plan", json.dumps(plan), category="plan")
        return plan["steps"]

    def _process_item(self, step: dict) -> None:
        # Phase 2: Execute each step
        result = self._execute_step(step)

        if result["status"] == "FAILED":
            # Phase 3: Replan from failure point
            remaining = self._replan(step, result["error"])
            if remaining:
                self.remember("replanned", json.dumps(remaining), category="plan")
                raise SkipItemError(f"Replanned from step {step['id']}")

    @abstractmethod
    def _generate_plan(self) -> dict:
        """Generate execution plan. Returns {steps: [...], dependencies: {...}}"""
        ...

    @abstractmethod
    def _execute_step(self, step: dict) -> dict:
        """Execute a single plan step. Returns {status, output, error}"""
        ...

    def _replan(self, failed_step: dict, error: str) -> list:
        """Generate alternative steps when a step fails. Override for custom logic."""
        self._log("REPLAN", f"Step {failed_step.get('id')} failed: {error}")
        return []  # Default: no replanning
```

### 4.3 Reflection Pattern

After task completion, evaluate output quality:

```python
class ReflectiveMixin:
    """Mixin that adds post-task reflection to any Agent9999 subclass."""

    def _finalize(self) -> None:
        """Run reflection after all items processed."""
        reflection = self._reflect()
        self.remember("last_reflection", json.dumps(reflection), category="reflection")

        if reflection["quality_score"] < 0.7:
            self._log("REFLECT", f"Low quality ({reflection['quality_score']:.2f}): "
                       f"{reflection['issues']}")

    def _reflect(self) -> dict:
        """Evaluate own output quality. Override for domain-specific checks."""
        error_rate = self.stats.errored / max(self.stats.total, 1)
        skip_rate = self.stats.skipped / max(self.stats.total, 1)
        quality = 1.0 - (error_rate * 2) - (skip_rate * 0.5)

        issues = []
        if error_rate > 0.05:
            issues.append(f"High error rate: {error_rate:.1%}")
        if skip_rate > 0.10:
            issues.append(f"High skip rate: {skip_rate:.1%}")
        if self.stats.elapsed > 600:
            issues.append(f"Slow execution: {self.stats.elapsed:.0f}s")

        return {
            "quality_score": max(0.0, min(1.0, quality)),
            "error_rate": error_rate,
            "skip_rate": skip_rate,
            "throughput": self.stats.rate,
            "issues": issues,
            "recommendation": self._recommend(issues),
        }

    def _recommend(self, issues: list) -> str:
        if not issues:
            return "Performance nominal."
        if any("error rate" in i for i in issues):
            return "Investigate error patterns in agent_log. Consider increasing retry count."
        if any("skip rate" in i for i in issues):
            return "Review skip conditions. May indicate data quality issues."
        if any("Slow" in i for i in issues):
            return "Consider increasing parallel_workers or optimizing _process_item."
        return "Review flagged issues."
```

### 4.4 Tool Registry Pattern

Dynamic tool selection from the 45 MCP tools based on task context:

```python
# Tool registry with selection hints — built into Agent9999.__init__
TOOL_REGISTRY = {
    # Evidence operations
    "find_evidence":    {"tool": "litigation_search", "when": "need to find documents by keyword"},
    "check_chain":      {"tool": "litigation_evidence_chain", "when": "need provenance verification"},
    "find_gaps":        {"tool": "litigation_evidence_gaps", "when": "need to identify missing evidence"},
    "build_timeline":   {"tool": "litigation_evidence_timeline", "when": "need chronological ordering"},

    # Filing operations
    "check_readiness":  {"tool": "litigation_filing_readiness", "when": "before assembling any filing"},
    "validate_filing":  {"tool": "litigation_filing_validate", "when": "after draft, before final"},
    "run_qa":           {"tool": "litigation_prefiling_qa", "when": "final check before submission"},

    # Analysis operations
    "check_citations":  {"tool": "litigation_citation_graph", "when": "validating legal authorities"},
    "scan_bias":        {"tool": "litigation_judicial_bias_scan", "when": "analyzing judicial patterns"},
    "find_contradictions": {"tool": "litigation_contradiction_find", "when": "cross-referencing testimony"},

    # System operations
    "check_health":     {"tool": "litigation_system_health", "when": "diagnosing system issues"},
    "check_deadlines":  {"tool": "litigation_deadline_dashboard", "when": "checking upcoming deadlines"},
}

def select_tool(task_description: str) -> str:
    """Select the best MCP tool for a given task description."""
    task_lower = task_description.lower()
    scores = {}
    for key, entry in TOOL_REGISTRY.items():
        # Simple keyword overlap scoring
        when_words = set(entry["when"].lower().split())
        task_words = set(task_lower.split())
        overlap = len(when_words & task_words)
        if overlap > 0:
            scores[entry["tool"]] = overlap
    if scores:
        return max(scores, key=scores.get)
    return "litigation_search"  # Default fallback
```

### 4.5 Memory-First Pattern

Always search agent memory before starting any task:

```python
# Memory-first workflow — add to run() preamble
def _memory_first_preamble(self):
    """Check memory for relevant context before processing."""
    # 1. Check for past errors on this task type
    errors = self.recall_errors(limit=5)
    if errors:
        self._log("MEMORY", f"Found {len(errors)} past error patterns — adjusting strategy")
        for err in errors:
            if "timeout" in err.get("value", "").lower():
                self.item_timeout = min(60, self.item_timeout * 2)
                self._log("ADAPT", f"Increased item_timeout to {self.item_timeout}s")

    # 2. Check for cached results that might skip work
    cached = self.recall(category='cache', limit=20)
    if cached:
        self._log("MEMORY", f"Found {len(cached)} cached results")

    # 3. Check for user corrections (learning from feedback)
    corrections = self.recall(category='correction', limit=10)
    if corrections:
        self._log("MEMORY", f"Found {len(corrections)} user corrections to apply")
```

---

## 5. Continuous Learning Protocol

### 5.1 Pattern Extraction Pipeline

After every session, extract reusable patterns and persist them:

```python
# Pattern categories with detection heuristics
LEARNABLE_PATTERNS = {
    "error_resolution": {
        "detect": lambda log: log["level"] in ("ERROR", "CRASH") and
                  any(r["level"] == "DONE" for r in log.get("subsequent", [])),
        "store_as": "error",
        "description": "Error that was successfully recovered from",
    },
    "user_correction": {
        "detect": lambda log: log.get("source") == "user_feedback",
        "store_as": "correction",
        "description": "User corrected an agent output",
    },
    "workaround": {
        "detect": lambda log: "retry" in log.get("detail", "").lower() or
                  "fallback" in log.get("detail", "").lower(),
        "store_as": "workaround",
        "description": "Alternative approach that succeeded after primary failed",
    },
    "debugging_technique": {
        "detect": lambda log: log["level"] == "DIAG",
        "store_as": "debug",
        "description": "Self-diagnosis that identified a root cause",
    },
    "project_specific": {
        "detect": lambda log: any(kw in log.get("detail", "").lower()
                  for kw in ["meek", "lane", "mcr", "mcl", "watson", "pigors"]),
        "store_as": "domain",
        "description": "Domain-specific pattern (Michigan family law)",
    },
}

# Patterns to IGNORE (noise — don't waste memory on these)
IGNORE_PATTERNS = {
    "simple_typos",           # One-time text corrections
    "one_time_fixes",         # Fixes that won't recur
    "external_api_issues",    # N/A — no external APIs (local-only)
    "transient_disk_errors",  # Temporary I/O blips
    "checkpoint_saves",       # Routine operations
}
```

### 5.2 Learning Loop Implementation

```python
class ContinuousLearner:
    """Extracts, stores, and applies learned patterns across sessions."""

    def __init__(self, agent: Agent9999):
        self.agent = agent

    def extract_patterns(self, session_log: list) -> list:
        """Scan session log for learnable patterns."""
        patterns = []
        for i, entry in enumerate(session_log):
            entry["subsequent"] = session_log[i+1:i+4]  # Look-ahead window
            for name, config in LEARNABLE_PATTERNS.items():
                if config["detect"](entry):
                    patterns.append({
                        "type": name,
                        "category": config["store_as"],
                        "detail": entry.get("detail", ""),
                        "context": {
                            "agent_id": entry.get("agent_id"),
                            "level": entry.get("level"),
                            "timestamp": entry.get("ts"),
                        },
                    })
        return patterns

    def store_patterns(self, patterns: list):
        """Persist patterns to agent_memory for cross-session use."""
        for p in patterns:
            key = f"learned_{p['type']}_{int(p['context'].get('timestamp', 0))}"
            self.agent.remember(
                key=key,
                value=json.dumps(p, default=str),
                category=p["category"],
                confidence=0.8  # Initial confidence; increases if pattern recurs
            )

    def apply_learned(self):
        """Apply stored patterns to current session."""
        # Error patterns → preemptive avoidance
        error_patterns = self.agent.recall(category='error', limit=20)
        for ep in error_patterns:
            data = json.loads(ep.get("value", "{}"))
            if "timeout" in data.get("detail", ""):
                self.agent.item_timeout = max(self.agent.item_timeout, 45)
            if "locked" in data.get("detail", ""):
                self.agent.max_retries = max(self.agent.max_retries, 5)

        # Correction patterns → output adjustment
        corrections = self.agent.recall(category='correction', limit=10)
        return len(error_patterns) + len(corrections)
```

### 5.3 Metrics to Track

| What | Storage | Query |
|------|---------|-------|
| What worked | `agent_memory WHERE type = 'cache'` | Successful computation results |
| What failed | `agent_memory WHERE type = 'error'` | Error patterns with context |
| What was corrected | `agent_memory WHERE type = 'correction'` | User feedback applied |
| Pattern recurrence | `COUNT(*) GROUP BY type` on `agent_memory` | Which patterns repeat most |
| Confidence drift | `AVG(confidence) GROUP BY type` over time | Are we getting better? |

---

## 6. RAG Integration

### 6.1 Evidence Retrieval Pipeline

```
Query → FTS5 Search → BM25 Ranking → Content Reranking → Top-K Selection → Context Injection
```

```python
# Evidence RAG pipeline using litigation_context.db
def retrieve_evidence(query: str, top_k: int = 10, vehicle: str = None) -> list:
    """Hybrid retrieval: FTS5 keyword search + BM25 scoring."""
    conn = get_central_db()

    # Stage 1: FTS5 full-text search (fast, recall-oriented)
    fts_results = conn.execute("""
        SELECT rowid, rank, snippet(search_index, 0, '<b>', '</b>', '...', 32)
        FROM search_index
        WHERE search_index MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, top_k * 3)).fetchall()  # Over-fetch for reranking

    # Stage 2: BM25 reranking via MANBEARPIG
    # The FTS5 rank column IS BM25 by default in SQLite
    candidates = []
    for row in fts_results:
        candidates.append({
            "id": row[0],
            "bm25_score": -row[1],  # FTS5 rank is negative (lower = better)
            "snippet": row[2],
        })

    # Stage 3: Vehicle/lane filter (if specified)
    if vehicle:
        candidates = [c for c in candidates if vehicle_matches(c, vehicle)]

    # Stage 4: Return top-K after reranking
    candidates.sort(key=lambda x: x["bm25_score"], reverse=True)
    return candidates[:top_k]
```

### 6.2 Authority Retrieval

```python
# Authority validation pipeline
def retrieve_authorities(claim_text: str, jurisdiction: str = "MI") -> list:
    """Retrieve relevant legal authorities with validation."""
    conn = get_central_db()

    # Stage 1: Citation extraction from claim text
    import re
    mcl_pattern = r'MCL\s+[\d.]+(?:\([a-z0-9]+\))?'
    mcr_pattern = r'MCR\s+[\d.]+(?:\([A-Z]\))?(?:\(\d+\))?'
    citations = re.findall(f'{mcl_pattern}|{mcr_pattern}', claim_text, re.IGNORECASE)

    # Stage 2: Bloom filter pre-check (if available)
    # Fast rejection of non-existent citations before expensive DB lookup
    valid_citations = []
    for cite in citations:
        row = conn.execute(
            "SELECT citation, full_text, authority_score FROM authority_index WHERE citation = ?",
            (cite,)
        ).fetchone()
        if row:
            valid_citations.append({
                "citation": row[0],
                "text": row[1][:500],
                "score": row[2],
            })

    # Stage 3: PageRank-style authority scoring
    # Authorities cited by more claims rank higher
    for auth in valid_citations:
        citing_count = conn.execute(
            "SELECT COUNT(*) FROM citation_edges WHERE target_citation = ?",
            (auth["citation"],)
        ).fetchone()[0]
        auth["pagerank_boost"] = citing_count * 0.1
        auth["final_score"] = auth["score"] + auth["pagerank_boost"]

    valid_citations.sort(key=lambda x: x["final_score"], reverse=True)
    return valid_citations
```

### 6.3 Hybrid Search Architecture

```
                    ┌─────────────┐
        Query ──────┤ Query Router │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼────┐ ┌────▼─────┐
        │  FTS5      │ │ BM25   │ │ Semantic  │
        │  Keyword   │ │ TF-IDF │ │ MiniLM    │
        │  (fast)    │ │ (med)  │ │ (slow)    │
        └─────┬──────┘ └───┬────┘ └────┬──────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │ Score Fusion │  ← Reciprocal Rank Fusion (RRF)
                    │ + Rerank     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ Context      │
                    │ Window Mgmt  │  ← Token budget: 4000 per section
                    └──────┬──────┘
                           │
                      Final Context
```

### 6.4 Context Window Management

```python
# Token budget allocation for context injection
CONTEXT_BUDGET = {
    "evidence_quotes": 2000,    # Direct evidence text
    "authority_text": 1500,     # Legal authority excerpts
    "case_history": 1000,       # Relevant prior filings
    "agent_memory": 500,        # Learned patterns
    "total_budget": 5000,       # Hard cap
}

def build_context_window(query: str, budget: dict = CONTEXT_BUDGET) -> str:
    """Assemble context within token budget."""
    sections = []

    # Evidence (highest priority)
    evidence = retrieve_evidence(query, top_k=5)
    evidence_text = summarize_to_budget(
        [e["snippet"] for e in evidence],
        budget["evidence_quotes"]
    )
    sections.append(f"## Evidence\n{evidence_text}")

    # Authorities
    authorities = retrieve_authorities(query)
    auth_text = summarize_to_budget(
        [f"{a['citation']}: {a['text']}" for a in authorities],
        budget["authority_text"]
    )
    sections.append(f"## Authorities\n{auth_text}")

    return "\n\n".join(sections)

def summarize_to_budget(items: list, char_budget: int) -> str:
    """Fit items within character budget, truncating from the end."""
    result = []
    used = 0
    for item in items:
        if used + len(item) > char_budget:
            remaining = char_budget - used
            if remaining > 100:  # Only include if meaningful
                result.append(item[:remaining] + "...")
            break
        result.append(item)
        used += len(item) + 1
    return "\n".join(result)
```

---

## 7. Automation Workflows

### 7.1 Filing Pipeline Automation

End-to-end workflow from raw evidence to court-ready filing:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Evidence  │───▶│ Classify │───▶│  Draft   │───▶│ Verify   │───▶│   QA     │───▶│  Export  │
│ Harvest   │    │ + Route  │    │ Filing   │    │ Cites    │    │ Sweep    │    │ Package  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
    A01-A04        A05-A08       F01-F02         L01-L04        F05 (QA)        F06 (Export)
```

```python
# Pipeline orchestration with wave-based execution
FILING_PIPELINE = [
    {"wave": 1, "agents": ["A01", "A02", "A03", "A04"], "name": "Evidence Harvest",
     "parallel": True, "timeout": 600},
    {"wave": 2, "agents": ["A05", "A06", "A07", "A08"], "name": "Classify & Route",
     "parallel": True, "timeout": 300, "depends_on": 1},
    {"wave": 3, "agents": ["F01", "F02"], "name": "Draft Filing",
     "parallel": False, "timeout": 900, "depends_on": 2},  # Sequential: F02 needs F01 output
    {"wave": 4, "agents": ["L01", "L02", "L03", "L04"], "name": "Verify Citations",
     "parallel": True, "timeout": 300, "depends_on": 3},
    {"wave": 5, "agents": ["F05"], "name": "QA Sweep",
     "parallel": False, "timeout": 300, "depends_on": 4},
    {"wave": 6, "agents": ["F06"], "name": "Export Package",
     "parallel": False, "timeout": 120, "depends_on": 5},
]
```

### 7.2 Batch Processing with Parallel Waves

```python
# Wave executor respecting EAGAIN constraints
def execute_waves(pipeline: list, max_concurrent: int = 2):
    """Execute pipeline waves with dependency tracking and agent limits."""
    completed_waves = set()
    results = {}

    for wave in sorted(pipeline, key=lambda w: w["wave"]):
        # Check dependencies
        depends = wave.get("depends_on")
        if depends and depends not in completed_waves:
            raise FatalAgentError(f"Wave {wave['wave']} depends on incomplete wave {depends}")

        wave_id = wave["wave"]
        agents = wave["agents"]

        if wave["parallel"] and len(agents) > 1:
            # Run agents in parallel, respecting max_concurrent
            for batch_start in range(0, len(agents), max_concurrent):
                batch = agents[batch_start:batch_start + max_concurrent]
                # Execute batch (2 agents max)
                batch_results = run_agent_batch(batch, timeout=wave["timeout"])
                results.update(batch_results)
                time.sleep(2)  # Cooldown between batches
        else:
            # Sequential execution
            for agent_id in agents:
                result = run_single_agent(agent_id, timeout=wave["timeout"])
                results[agent_id] = result

        # Check wave health
        wave_errors = [r for r in results.values()
                       if r.status in ("FATAL", "CRASH") and r.agent_id in agents]
        if len(wave_errors) > len(agents) // 2:
            raise FatalAgentError(f"Wave {wave_id} failed: {len(wave_errors)}/{len(agents)} agents")

        completed_waves.add(wave_id)

    return results
```

### 7.3 Retry with Fallback Chain

```python
# 3-tier retry with model fallback
RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_base": 2,       # Exponential: 2s, 4s, 8s
    "backoff_max": 30,       # Cap at 30 seconds
    "fallback_chain": [
        "manbearpig_full",   # Primary: full MANBEARPIG
        "manbearpig",        # Fallback 1: standard MANBEARPIG
        "local_ai",          # Fallback 2: LocalAI heuristic
        "offline_heuristic", # Fallback 3: regex/keyword (always works)
    ],
}

def retry_with_fallback(func, *args, config=RETRY_CONFIG, **kwargs):
    """Execute with exponential backoff and model fallback."""
    for model_idx, model in enumerate(config["fallback_chain"]):
        for attempt in range(config["max_attempts"]):
            try:
                kwargs["model"] = model
                return func(*args, **kwargs)
            except Exception as e:
                wait = min(
                    config["backoff_base"] ** attempt,
                    config["backoff_max"]
                )
                logging.warning(
                    f"Attempt {attempt + 1}/{config['max_attempts']} "
                    f"with {model} failed: {e}. Waiting {wait}s."
                )
                time.sleep(wait)

        logging.warning(f"All attempts exhausted for {model}. Falling back.")

    raise FatalAgentError("All retry attempts and fallback models exhausted")
```

### 7.4 Scheduled Task Definitions

```python
# cron-style schedule for autonomous operations
SCHEDULED_TASKS = {
    "deadline_monitor": {
        "interval_hours": 6,
        "agent": "deadline_dashboard",
        "action": "Check all deadlines, alert if any within 72 hours",
        "priority": "CRITICAL",
    },
    "evidence_scan": {
        "interval_hours": 24,
        "agent": "A01",
        "action": "Scan all drives for new evidence files",
        "priority": "HIGH",
    },
    "db_health": {
        "interval_hours": 12,
        "agent": "system_health",
        "action": "PRAGMA integrity_check + WAL checkpoint + free space audit",
        "priority": "MEDIUM",
    },
    "dedup_sweep": {
        "interval_hours": 48,
        "agent": "A06",
        "action": "Content-based dedup scan (no hash-only — peek inside documents)",
        "priority": "MEDIUM",
    },
    "memory_consolidation": {
        "interval_hours": 24,
        "agent": "ContinuousLearner",
        "action": "Consolidate agent_memory: merge duplicates, prune stale entries",
        "priority": "LOW",
    },
}
```

### 7.5 Monitoring and Alerting

```python
# Structured logging format for all agents
LOG_FORMAT = {
    "timestamp": "ISO 8601",
    "agent_id": "str",
    "level": "BOOT|WORK|CHECKPOINT|ERROR|FATAL|CRASH|DONE|DIAG|REACT|DEADMAN",
    "detail": "str (max 500 chars)",
    "metrics": {
        "processed": "int",
        "errored": "int",
        "elapsed": "float",
        "throughput": "float",
    },
}

# Alert thresholds
ALERT_THRESHOLDS = {
    "error_rate_critical": 0.10,   # >10% errors → immediate alert
    "error_rate_warning": 0.05,    # >5% errors → warning
    "deadman_trigger": 1,          # Any deadman → investigate
    "disk_space_gb": 1.0,          # <1GB free → critical
    "wave_failure_pct": 0.50,      # >50% agents in wave fail → halt
}
```

---

## 8. Tool Schema Improvements

### 8.1 Top 10 MCP Tool Recommendations

#### 1. `litigation_search`

```json
{
  "name": "litigation_search",
  "description": "Full-text search across all ingested documents in the litigation database. Uses FTS5 with BM25 ranking. Returns matching documents with snippets, relevance scores, and metadata. Use this as the primary discovery tool before using specialized tools.",
  "input_schema": {
    "query": {"type": "string", "description": "Search terms. Supports FTS5 syntax: AND, OR, NOT, phrase matching with quotes. Example: '\"security deposit\" AND mcl'"},
    "vehicle": {"type": "string", "description": "Filter by case vehicle name. Optional."},
    "limit": {"type": "integer", "default": 20, "description": "Max results to return (1-100)."},
    "doc_type": {"type": "string", "enum": ["all", "pdf", "docx", "txt", "email"], "default": "all"}
  },
  "error_returns": {
    "NO_RESULTS": "No documents matched the query. Suggest broadening search terms.",
    "INVALID_FTS": "FTS5 syntax error. Show corrected query.",
    "DB_UNAVAILABLE": "Database connection failed. Retry after 5 seconds."
  },
  "examples": [
    {"query": "MCR 2.003 disqualification", "vehicle": "Lane_E_misconduct"},
    {"query": "\"best interest\" factors children", "doc_type": "pdf"},
    {"query": "shady oaks habitability violations", "vehicle": "Lane_B_housing"}
  ]
}
```

#### 2. `litigation_filing_readiness`

```json
{
  "description": "Check if a case vehicle has all required components for filing: evidence completeness, citation validity, form compliance, and deadline status. Returns a GO/NO-GO assessment with specific missing items. Run this BEFORE litigation_filing_validate.",
  "input_schema": {
    "vehicle": {"type": "string", "required": true, "description": "Case vehicle name (e.g., 'Lane_A_custody', '2024-001507-DC')"},
    "filing_type": {"type": "string", "description": "Type of filing: motion, brief, complaint, response, appeal"}
  },
  "error_returns": {
    "UNKNOWN_VEHICLE": "Vehicle not found. List available vehicles.",
    "INCOMPLETE_DATA": "Cannot assess — key tables missing. Run evidence harvest first."
  }
}
```

#### 3. `litigation_evidence_chain`

```json
{
  "description": "Trace the provenance chain for a specific piece of evidence: source file → extraction → classification → citation → filing. Verifies SHA-256 integrity at each step. Use when you need to prove evidence authenticity or find gaps in the chain of custody.",
  "input_schema": {
    "evidence_id": {"type": "integer", "description": "File ID from the files table"},
    "include_hash_verification": {"type": "boolean", "default": true}
  },
  "error_returns": {
    "BROKEN_CHAIN": "Chain has gaps — return the last valid link and the missing step.",
    "HASH_MISMATCH": "SHA-256 mismatch detected — evidence may have been modified."
  }
}
```

#### 4. `litigation_deadline_dashboard`

```json
{
  "description": "Display all active filing deadlines with urgency scoring. Urgency levels: CRITICAL (<72h), HIGH (<7d), MEDIUM (<30d), LOW (>30d). Includes court rules that set each deadline and consequences of missing them.",
  "input_schema": {
    "vehicle": {"type": "string", "description": "Filter by case vehicle. Omit for all cases."},
    "urgency_min": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"], "default": "LOW"}
  },
  "error_returns": {
    "NO_DEADLINES": "No active deadlines found. Verify deadline data has been loaded."
  }
}
```

#### 5. `litigation_prefiling_qa`

```json
{
  "description": "Final quality assurance sweep before court filing. Checks: all citations valid, no placeholder text remaining, signature blocks present, proof of service attached, page limits met, formatting compliant with MCR. Returns GO/NO-GO with specific fix-it items.",
  "input_schema": {
    "filing_id": {"type": "string", "required": true, "description": "Filing package identifier"},
    "court": {"type": "string", "enum": ["circuit", "district", "coa", "msc", "federal"], "default": "circuit"}
  },
  "error_returns": {
    "NO_GO": "Filing not ready — return all failing checks with fix instructions.",
    "FILING_NOT_FOUND": "Filing ID not found in system."
  }
}
```

#### 6. `litigation_citation_graph`

```json
{
  "description": "Build and query the citation dependency graph for a filing. Shows which authorities support which claims, identifies unsupported claims, and detects circular citations. Use after evidence gathering to verify legal foundation.",
  "input_schema": {
    "vehicle": {"type": "string", "required": true},
    "claim_id": {"type": "string", "description": "Specific claim to trace. Omit for full graph."},
    "depth": {"type": "integer", "default": 2, "description": "How many citation levels deep to traverse (1-5)"}
  }
}
```

#### 7. `litigation_evidence_gaps`

```json
{
  "description": "Identify missing evidence for each claim in a case vehicle. Compares required evidence (from claim elements) against available evidence. Returns a gap report with acquisition suggestions. Critical for trial preparation.",
  "input_schema": {
    "vehicle": {"type": "string", "required": true},
    "claim_type": {"type": "string", "description": "Filter to specific claim type. Omit for all claims."}
  },
  "error_returns": {
    "NO_CLAIMS": "No claims defined for this vehicle. Define claims first.",
    "NO_EVIDENCE": "No evidence ingested for this vehicle. Run evidence harvest."
  }
}
```

#### 8. `litigation_filing_validate`

```json
{
  "description": "Validate a draft filing against court rules (MCR) and local rules. Checks formatting, page limits, font requirements, margin compliance, caption format, and certificate of service. Run AFTER litigation_filing_readiness (which checks content completeness).",
  "input_schema": {
    "filing_path": {"type": "string", "required": true, "description": "Path to the filing document"},
    "court": {"type": "string", "required": true, "enum": ["circuit", "district", "coa", "msc", "federal"]},
    "filing_type": {"type": "string", "required": true}
  }
}
```

#### 9. `litigation_judicial_bias_scan`

```json
{
  "description": "Analyze judicial decision patterns for potential bias indicators. Searches ruling history, ex parte communications, recusal record, and sentencing patterns. Outputs structured bias indicators with confidence scores. Use for disqualification motions (MCR 2.003).",
  "input_schema": {
    "judge_name": {"type": "string", "required": true},
    "case_number": {"type": "string", "description": "Specific case to analyze. Omit for full history."},
    "bias_categories": {"type": "array", "items": {"type": "string"}, "default": ["procedural", "substantive", "ex_parte", "recusal"]}
  }
}
```

#### 10. `litigation_system_health`

```json
{
  "description": "Comprehensive system health check: database integrity, disk space, WAL status, table counts, index health, and recent error rates. Run at session start and periodically during long operations.",
  "input_schema": {
    "include_table_stats": {"type": "boolean", "default": true},
    "include_disk_check": {"type": "boolean", "default": true}
  },
  "error_returns": {
    "DB_CORRUPT": "Database integrity check failed. Run WAL checkpoint and retry.",
    "DISK_CRITICAL": "Less than 500MB free. Immediate cleanup required."
  }
}
```

### 8.2 Cross-Cutting Schema Improvements

Apply these patterns to **all 45 tools**:

1. **Structured error returns** — never return bare strings on failure:
   ```python
   # Every tool should return this on error:
   {"error": True, "code": "SPECIFIC_CODE", "message": "Human-readable fix instruction",
    "suggested_action": "What the agent should do next"}
   ```

2. **Input validation before execution** — fail fast with clear messages:
   ```python
   if not vehicle:
       return {"error": True, "code": "MISSING_VEHICLE",
               "message": "vehicle parameter is required. Available: Lane_A, Lane_B, ..."}
   ```

3. **Consistent pagination** — all list-returning tools support `limit` + `offset`:
   ```python
   {"limit": 20, "offset": 0, "total": 1547, "results": [...]}
   ```

---

## 9. Implementation Roadmap

### Phase 1: Memory-First Workflow + Continuous Learning (Immediate)

**Goal:** Every agent checks memory before starting; every session extracts patterns.

| Task | File | Change | Effort |
|------|------|--------|--------|
| Add `_memory_first_preamble()` call to `run()` | `agent_base.py` | Insert after `_load_checkpoint()`, before `_get_work_items()` | 1 hour |
| Add `ContinuousLearner` class | `agents/learning.py` (new) | Full implementation from §5.2 | 2 hours |
| Add `fleet_metrics` table | `agent_orchestrator.py` | Schema from §1.3, populate in `run_tier()` | 1 hour |
| Add failure classifier to `_log()` | `agent_base.py` | Classify ERROR/CRASH entries per §2.2 | 30 min |
| Wire `ContinuousLearner.extract_patterns()` | `agent_orchestrator.py` | Call after each tier completes | 30 min |

**Validation:**
```python
# Verify memory-first is active:
# 1. Run any agent
# 2. Check agent_log for "PREWARM" and "MEMORY" entries
# 3. Check agent_memory for new entries after run
```

### Phase 2: Tool Schema Improvements + Error Handling (Week 1)

**Goal:** All top-10 MCP tools return structured errors; LLM tool selection accuracy ≥ 90%.

| Task | File | Change | Effort |
|------|------|--------|--------|
| Update tool descriptions per §8.1 | `00_SYSTEM/mcp_server/tools/*.py` | Rewrite docstrings with examples | 4 hours |
| Add structured error returns | `00_SYSTEM/mcp_server/tools/*.py` | Replace bare string errors | 3 hours |
| Add input validation | `00_SYSTEM/mcp_server/tools/*.py` | Validate required params, return clear errors | 2 hours |
| Add TOOL_REGISTRY to `agent_base.py` | `agent_base.py` | §4.4 implementation | 1 hour |
| Tool selection A/B test | `agent_orchestrator.py` | Log tool choices, measure accuracy | 2 hours |

**Validation:**
```bash
# Run each of the top-10 tools with invalid input — verify structured error returns
python -c "from mcp_server.tools import search; search.run(query='')"
# Should return: {"error": True, "code": "EMPTY_QUERY", ...}
```

### Phase 3: RAG Integration + Automation Workflows (Week 2)

**Goal:** Evidence retrieval uses hybrid search; filing pipeline runs end-to-end automatically.

| Task | File | Change | Effort |
|------|------|--------|--------|
| Implement `retrieve_evidence()` per §6.1 | `agents/rag_pipeline.py` (new) | FTS5 + BM25 hybrid retrieval | 3 hours |
| Implement `retrieve_authorities()` per §6.2 | `agents/rag_pipeline.py` | Citation validation pipeline | 2 hours |
| Context window manager per §6.4 | `agents/context_manager.py` (new) | Token budget allocation | 2 hours |
| Filing pipeline definition per §7.1 | `agents/filing_pipeline.py` (new) | Wave-based execution config | 2 hours |
| Wave executor per §7.2 | `agent_orchestrator.py` | Add `execute_waves()` method | 3 hours |
| Retry with fallback per §7.3 | `agent_base.py` | Add `retry_with_fallback()` utility | 1 hour |

**Validation:**
```bash
# Run filing pipeline on test data (dry-run mode):
python -m agents.agent_orchestrator --pipeline filing --dry-run --vehicle Lane_A_custody
```

### Phase 4: Full Fleet Optimization + A/B Testing (Week 3)

**Goal:** Measurable improvement across all metrics; A/B test framework active.

| Task | File | Change | Effort |
|------|------|--------|--------|
| `EnhancedReActMixin` per §4.1 | `agents/mixins.py` (new) | Confidence-based early termination | 2 hours |
| `ReflectiveMixin` per §4.3 | `agents/mixins.py` | Post-task quality evaluation | 2 hours |
| `PlanExecuteAgent` per §4.2 | `agents/plan_execute.py` (new) | Plan-then-execute pattern | 3 hours |
| Workload distribution per §3.1 | `agent_base.py` | Model selection matrix | 1 hour |
| Parallel worker auto-tuning per §3.2 | `agent_base.py` | `optimal_workers` property | 30 min |
| A/B testing framework | `agents/ab_testing.py` (new) | Route 50% of runs through optimized path | 3 hours |
| Fleet scoreboard dashboard | `agents/dashboard.py` (new) | Query `fleet_metrics` for trend analysis | 2 hours |

**Validation:**
```sql
-- Compare baseline vs. optimized metrics after 1 week:
SELECT
    CASE WHEN run_id LIKE 'opt_%' THEN 'optimized' ELSE 'baseline' END AS variant,
    AVG(CAST(processed AS REAL) / NULLIF(total_items, 0)) AS completion_rate,
    AVG(CAST(errored AS REAL) / NULLIF(total_items, 0)) AS error_rate,
    AVG(throughput) AS avg_throughput
FROM fleet_metrics
WHERE recorded_at > datetime('now', '-7 days')
GROUP BY variant;
```

### Success Criteria

| Metric | Baseline | Target | Measured By |
|--------|----------|--------|-------------|
| Task completion rate | ~88% | ≥ 95% (+15%) | `fleet_metrics.processed / total_items` |
| User corrections per session | ~4 | ≤ 3 (-25%) | `agent_memory WHERE type = 'correction'` |
| EAGAIN incidents | ~2/week | 0 | `agent_log WHERE detail LIKE '%EAGAIN%'` |
| Mean agent execution time | Baseline | -20% | `fleet_metrics.elapsed_seconds` |
| Error recovery success | ~70% | ≥ 85% | ERROR→RETRY→OK chains in `agent_log` |
| Tool selection accuracy | ~75% | ≥ 90% | MCP tool call audit log |

---

## Appendix A: Agent9999 Contract Summary

From `00_SYSTEM/pipeline/agents/agent_base.py`:

```
Class:        Agent9999 (ABC)
Constructor:  __init__(agent_id: str, db_path: Optional[Path])
Entry point:  run() → AgentResult(agent_id, status, stats)
Status codes: SUCCESS | FATAL | CRASH

Required overrides:
  _get_work_items() → list           # What to process
  _process_item(item) → None         # How to process one item
  _validate_preconditions() → None   # Pre-flight checks

Optional overrides:
  _finalize() → None                 # Post-processing cleanup
  _ensure_tables() → None            # Create agent-specific tables
  _reason(context) → str             # ReAct: reasoning step
  _act(reasoning, context) → tuple   # ReAct: action step
  _observe(action, result, ctx) → str # ReAct: observation step

Built-in features:
  - Parallel execution (parallel_workers > 1 → ThreadPoolExecutor)
  - Per-item timeout (item_timeout=30s via ThreadPoolExecutor)
  - Deadman switch (deadman_timeout=120s → auto-skip stuck items)
  - Checkpoint/resume (JSON file + DB-backed agent_checkpoints)
  - Self-diagnosis (_diagnose: disk space + DB integrity)
  - Retry with backoff (_retry: 3× exponential)
  - Thread-safe DB (per-thread connections via threading.local)
  - SQLite locked retry (_db_execute: 8× with random jitter)
  - Persistent memory (remember/recall via central litigation_context.db)
  - ReAct loop (react_loop: Reason→Act→Observe with max iterations)
  - Tool registry (_tool_registry: dict for dynamic tool selection)
  - Local AI (self.ai → LocalAI: classify, detect_lane, extract, score, summarize)
  - Content reader (_read_file_content: txt/pdf/docx with caching)
```

## Appendix B: Fleet Inventory

| Fleet | Agent IDs | Count | Tier | Focus |
|-------|-----------|-------|------|-------|
| **Delta9 Lane 1** | A01–A12 | 12 | 1-3 (I/O) | Indexing, dedup, extraction |
| **Delta9 Lane 2** | J01–J08, K01–K08, L01–L08 | 24 | J/K/L (Intel) | Judicial, case intel, legal analysis |
| **Delta9 Convergence** | F01–F06 | 6 | Convergence | Filing, brain feed, graph, certification |
| **Delta9 Other** | B01–C08 | 14 | 2-3 | Classification, routing |
| **Delta999** | d999_classifier, d999_validator, ... | 12 | Advanced | Classifier, validator, brief, opposing, settlement, assembly, deadline, db_lock |
| **Copilot Agents** | `.copilot/agents/*.md` | 64 | Specialized | Court forms, research, QA, filing, transcripts |
| **Superpower** | SP01–SP13 | 13 | Cross-cutting | Orchestration, governance, self-evolution |
| **Convergence** | CV01–CV10 | 10 | Hardening | Phase 5-6, filing workflow, complaint prep, MCP v2 |
| **Total** | — | **155+** | — | — |
