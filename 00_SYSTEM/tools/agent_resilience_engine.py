#!/usr/bin/env python3
"""
Agent Resilience Engine (ARE) v1.0
===================================
Prevents agent stale-outs, GOAWAY losses, and context death.

Architecture:
  TaskAtomizer  → Breaks big tasks into <5 min micro-shards
  ProgressJournal → Agents write incremental results to disk + DB
  WatchdogTimer → Detects stalls, triggers re-dispatch
  ResultStreamer → Partial results survive agent death

Usage:
  from agent_resilience_engine import TaskAtomizer, ProgressJournal, ShardTracker

  # 1. Atomize a big task into micro-shards
  atomizer = TaskAtomizer()
  shards = atomizer.atomize(
      parent_todo="H01",
      task_description="Inventory I:\\ drive by extension",
      strategy="directory_walk",  # or "file_batch", "query_batch", "sequential"
      max_shard_minutes=5
  )

  # 2. Track shard progress
  tracker = ShardTracker(db_path="session.db")
  tracker.register_shards(shards)
  ready = tracker.get_ready_shards(limit=3)

  # 3. Generate self-contained agent prompts (each shard = 1 agent dispatch)
  for shard in ready:
      prompt = shard.to_agent_prompt()
      # dispatch via task() tool...

  # 4. Agent writes progress as it works
  journal = ProgressJournal(agent_id="drive-inv-shard-3", output_dir="temp/are/")
  journal.heartbeat("Scanning I:\\05_EVIDENCE — found 2,340 PDFs")
  journal.write_partial({"pdfs": 2340, "docx": 156, "total_gb": 4.2})
  journal.complete(summary="Shard complete: 2,340 PDFs, 156 DOCX, 4.2 GB")

  # 5. Watchdog detects stale agents
  stale = tracker.find_stale_agents(max_idle_minutes=8)
  for agent in stale:
      tracker.mark_stale(agent.shard_id)
      # re-dispatch shard to new agent...
"""

import json
import os
import sys
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timedelta

# UTF-8 safety
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

# ═══════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Shard:
    """Atomic unit of work — completable in <5 minutes by a single agent."""
    shard_id: str
    parent_todo_id: str
    sequence: int
    title: str
    prompt: str
    agent_type: str = "general-purpose"
    max_minutes: int = 5
    status: str = "pending"
    agent_id: Optional[str] = None
    result_summary: Optional[str] = None
    output_file: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0

    def to_agent_prompt(self) -> str:
        """Generate a self-contained prompt for agent dispatch."""
        return (
            f"## Task: {self.title}\n\n"
            f"**Shard ID:** {self.shard_id}\n"
            f"**Parent Todo:** {self.parent_todo_id}\n"
            f"**Time Budget:** {self.max_minutes} minutes MAX\n\n"
            f"### Instructions\n{self.prompt}\n\n"
            f"### Output Requirements\n"
            f"1. Write results to: `C:\\Users\\andre\\LitigationOS\\temp\\are\\{self.shard_id}.json`\n"
            f"2. If task takes >4 minutes, write partial results and note what remains\n"
            f"3. Include a `summary` field with a 1-2 sentence description of results\n"
            f"4. Include an `items_processed` count\n"
            f"5. If you cannot complete the task, write what you DID complete\n\n"
            f"### CRITICAL: Write output file FIRST, then report. If you die mid-task, "
            f"the output file preserves your work."
        )

    def to_sql_insert(self) -> tuple:
        """Generate SQL INSERT values."""
        return (
            self.shard_id, self.parent_todo_id, self.sequence,
            self.title, self.prompt, self.agent_type, self.max_minutes,
            self.status, self.agent_id, self.result_summary,
            self.output_file, self.started_at, self.completed_at,
            self.retry_count
        )


# ═══════════════════════════════════════════════════════════════
# TASK ATOMIZER — Breaks big tasks into micro-shards
# ═══════════════════════════════════════════════════════════════

class TaskAtomizer:
    """Decomposes large tasks into time-bounded micro-shards."""

    STRATEGIES = {
        "directory_walk": "_atomize_directory_walk",
        "file_batch": "_atomize_file_batch",
        "query_batch": "_atomize_query_batch",
        "sequential": "_atomize_sequential",
        "evidence_scan": "_atomize_evidence_scan",
        "document_grade": "_atomize_document_grade",
    }

    def atomize(
        self,
        parent_todo_id: str,
        task_description: str,
        strategy: str = "sequential",
        max_shard_minutes: int = 5,
        context: Optional[dict] = None,
    ) -> list:
        """
        Break a task into shards.

        Args:
            parent_todo_id: The todo this task belongs to
            task_description: Full description of the work
            strategy: Decomposition strategy name
            max_shard_minutes: Max time per shard
            context: Additional context (paths, queries, file lists, etc.)

        Returns:
            List[Shard] — ordered micro-tasks
        """
        context = context or {}
        method = self.STRATEGIES.get(strategy, "_atomize_sequential")
        return getattr(self, method)(
            parent_todo_id, task_description, max_shard_minutes, context
        )

    def _atomize_directory_walk(self, parent_id, desc, max_min, ctx) -> list:
        """Strategy for scanning drives/directories."""
        root_path = ctx.get("root_path", "I:\\")
        shards = []

        # Shard 0: List top-level structure
        shards.append(Shard(
            shard_id=f"{parent_id}-s0-structure",
            parent_todo_id=parent_id,
            sequence=0,
            title=f"Map top-level structure of {root_path}",
            prompt=(
                f"List all top-level directories in {root_path}. "
                f"For each directory, count files (non-recursive) and get total size. "
                f"Output as JSON: {{\"directories\": [{{\"name\": ..., \"file_count\": ..., \"size_mb\": ...}}]}}"
            ),
            agent_type="task",
            max_minutes=3,
        ))

        # Shard 1: Count by extension
        shards.append(Shard(
            shard_id=f"{parent_id}-s1-extensions",
            parent_todo_id=parent_id,
            sequence=1,
            title=f"Count files by extension on {root_path}",
            prompt=(
                f"Count all files on {root_path} grouped by extension. "
                f"Use: Get-ChildItem -Recurse -File | Group-Object Extension | "
                f"Sort-Object Count -Descending | Select-Object -First 30. "
                f"Output as JSON: {{\"extensions\": [{{\"ext\": ..., \"count\": ..., \"total_mb\": ...}}]}}"
            ),
            agent_type="task",
            max_minutes=5,
        ))

        # Shard 2: Sample high-value files
        shards.append(Shard(
            shard_id=f"{parent_id}-s2-sample-pdfs",
            parent_todo_id=parent_id,
            sequence=2,
            title=f"Sample first 50 PDFs on {root_path} for content classification",
            prompt=(
                f"Find the first 50 PDF files on {root_path} (by path order). "
                f"For each, extract: filename, size, path, and first 200 chars of text content. "
                f"Classify each as: court_order, police_report, evidence, correspondence, "
                f"legal_filing, financial, medical, unknown. "
                f"Output as JSON array."
            ),
            agent_type="general-purpose",
            max_minutes=5,
        ))

        # Shard 3: Find duplicates
        shards.append(Shard(
            shard_id=f"{parent_id}-s3-dedup-candidates",
            parent_todo_id=parent_id,
            sequence=3,
            title=f"Identify duplicate candidates on {root_path}",
            prompt=(
                f"Find files with identical names but different paths on {root_path}. "
                f"Group by filename, show all paths. For groups with >1 file, "
                f"compare sizes. Flag same-name-same-size pairs as dedup candidates. "
                f"Output as JSON: {{\"duplicates\": [{{\"name\": ..., \"paths\": [...], \"sizes\": [...]}}]}}"
            ),
            agent_type="task",
            max_minutes=5,
        ))

        return shards

    def _atomize_file_batch(self, parent_id, desc, max_min, ctx) -> list:
        """Strategy for processing batches of files."""
        file_list = ctx.get("files", [])
        batch_size = ctx.get("batch_size", 20)
        shards = []

        for i in range(0, len(file_list), batch_size):
            batch = file_list[i:i + batch_size]
            shard_num = i // batch_size
            shards.append(Shard(
                shard_id=f"{parent_id}-s{shard_num}-batch",
                parent_todo_id=parent_id,
                sequence=shard_num,
                title=f"Process files batch {shard_num + 1} ({len(batch)} files)",
                prompt=(
                    f"{desc}\n\nProcess these {len(batch)} files:\n"
                    + "\n".join(f"- {f}" for f in batch)
                ),
                max_minutes=max_min,
            ))

        return shards

    def _atomize_query_batch(self, parent_id, desc, max_min, ctx) -> list:
        """Strategy for database query batches."""
        tables = ctx.get("tables", [])
        queries = ctx.get("queries", [])
        shards = []

        items = queries if queries else [f"SELECT * FROM {t} LIMIT 100" for t in tables]
        for i, item in enumerate(items):
            shards.append(Shard(
                shard_id=f"{parent_id}-s{i}-query",
                parent_todo_id=parent_id,
                sequence=i,
                title=f"Execute query batch {i + 1}",
                prompt=f"{desc}\n\nExecute: {item}",
                agent_type="task",
                max_minutes=max_min,
            ))

        return shards

    def _atomize_sequential(self, parent_id, desc, max_min, ctx) -> list:
        """Strategy for sequential multi-step tasks."""
        steps = ctx.get("steps", [])
        if not steps:
            # Single shard — the task itself
            return [Shard(
                shard_id=f"{parent_id}-s0-main",
                parent_todo_id=parent_id,
                sequence=0,
                title=desc[:80],
                prompt=desc,
                max_minutes=max_min,
            )]

        return [
            Shard(
                shard_id=f"{parent_id}-s{i}-step",
                parent_todo_id=parent_id,
                sequence=i,
                title=step.get("title", f"Step {i + 1}"),
                prompt=step.get("prompt", step.get("title", "")),
                agent_type=step.get("agent_type", "general-purpose"),
                max_minutes=step.get("max_minutes", max_min),
            )
            for i, step in enumerate(steps)
        ]

    def _atomize_evidence_scan(self, parent_id, desc, max_min, ctx) -> list:
        """Strategy for scanning evidence across drives."""
        drives = ctx.get("drives", ["I:\\", "F:\\", "G:\\", "H:\\", "J:\\"])
        evidence_types = ctx.get("types", ["pdf", "docx", "txt", "jpg", "png"])
        shards = []

        for i, drive in enumerate(drives):
            shards.append(Shard(
                shard_id=f"{parent_id}-s{i}-{drive[0].lower()}drive",
                parent_todo_id=parent_id,
                sequence=i,
                title=f"Scan {drive} for evidence files",
                prompt=(
                    f"Scan {drive} for files with extensions: {', '.join(evidence_types)}. "
                    f"For each file found: record path, size, extension, modified date. "
                    f"Classify by content type where possible. "
                    f"Write results to temp/are/{parent_id}-s{i}-{drive[0].lower()}drive.json"
                ),
                agent_type="task",
                max_minutes=max_min,
            ))

        return shards

    def _atomize_document_grade(self, parent_id, desc, max_min, ctx) -> list:
        """Strategy for grading legal documents."""
        documents = ctx.get("documents", [])
        rubric = ctx.get("rubric", "10-point legal document rubric")
        shards = []

        for i, doc in enumerate(documents):
            doc_path = doc if isinstance(doc, str) else doc.get("path", "")
            doc_name = Path(doc_path).stem if doc_path else f"doc_{i}"
            shards.append(Shard(
                shard_id=f"{parent_id}-s{i}-grade-{doc_name[:30]}",
                parent_todo_id=parent_id,
                sequence=i,
                title=f"Grade: {Path(doc_path).name}" if doc_path else f"Grade document {i + 1}",
                prompt=(
                    f"Read and grade this legal document using the {rubric}:\n"
                    f"File: {doc_path}\n\n"
                    f"Score each criterion 0-10 and provide specific feedback. "
                    f"Output JSON: {{\"file\": ..., \"total_score\": ..., \"max_score\": 100, "
                    f"\"criteria\": [{{\"name\": ..., \"score\": ..., \"max\": ..., \"feedback\": ...}}], "
                    f"\"critical_issues\": [...], \"improvement_actions\": [...]}}"
                ),
                agent_type="general-purpose",
                max_minutes=max_min,
            ))

        return shards


# ═══════════════════════════════════════════════════════════════
# PROGRESS JOURNAL — Agents write incremental results to disk
# ═══════════════════════════════════════════════════════════════

class ProgressJournal:
    """
    File-based progress journal for agent resilience.

    Agents write incremental results here. If the agent dies,
    partial results survive on disk for the next agent to pick up.
    """

    def __init__(self, agent_id: str, output_dir: str = None):
        self.agent_id = agent_id
        self.output_dir = Path(output_dir or r"C:\Users\andre\LitigationOS\temp\are")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.journal_file = self.output_dir / f"{agent_id}_journal.jsonl"
        self.result_file = self.output_dir / f"{agent_id}_result.json"
        self._items_processed = 0
        self._start_time = datetime.now()

    def heartbeat(self, message: str = "alive", items: int = 0):
        """Write a heartbeat entry — proves agent is still working."""
        self._items_processed += items
        entry = {
            "type": "heartbeat",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "items_processed": self._items_processed,
            "elapsed_seconds": (datetime.now() - self._start_time).total_seconds(),
        }
        with open(self.journal_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def write_partial(self, data: dict):
        """Write partial results — survives agent death."""
        result = {
            "type": "partial",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "items_processed": self._items_processed,
            "data": data,
        }
        # Overwrite result file with latest partial
        with open(self.result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def complete(self, summary: str, data: dict = None):
        """Mark task as complete with final results."""
        result = {
            "type": "complete",
            "agent_id": self.agent_id,
            "timestamp": datetime.now().isoformat(),
            "items_processed": self._items_processed,
            "elapsed_seconds": (datetime.now() - self._start_time).total_seconds(),
            "summary": summary,
            "data": data or {},
        }
        with open(self.result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        # Final heartbeat
        self.heartbeat(f"COMPLETE: {summary}")

    @classmethod
    def read_result(cls, agent_id: str, output_dir: str = None) -> Optional[dict]:
        """Read whatever results an agent left behind (partial or complete)."""
        base = Path(output_dir or r"C:\Users\andre\LitigationOS\temp\are")
        result_file = base / f"{agent_id}_result.json"
        if result_file.exists():
            with open(result_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    @classmethod
    def read_journal(cls, agent_id: str, output_dir: str = None) -> list:
        """Read all journal entries (heartbeats + partials)."""
        base = Path(output_dir or r"C:\Users\andre\LitigationOS\temp\are")
        journal_file = base / f"{agent_id}_journal.jsonl"
        entries = []
        if journal_file.exists():
            with open(journal_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        return entries

    @classmethod
    def last_heartbeat(cls, agent_id: str, output_dir: str = None) -> Optional[dict]:
        """Get the most recent heartbeat for an agent."""
        entries = cls.read_journal(agent_id, output_dir)
        heartbeats = [e for e in entries if e.get("type") == "heartbeat"]
        return heartbeats[-1] if heartbeats else None


# ═══════════════════════════════════════════════════════════════
# SHARD TRACKER — SQL-backed shard state machine
# ═══════════════════════════════════════════════════════════════

class ShardTracker:
    """
    Tracks shard lifecycle via SQL.

    Generates SQL statements for the Copilot session DB.
    (Cannot connect directly — generates SQL for the `sql` tool.)
    """

    @staticmethod
    def register_shards_sql(shards: list) -> str:
        """Generate SQL to register shards in the session DB."""
        values = []
        for s in shards:
            values.append(
                f"('{s.shard_id}', '{s.parent_todo_id}', {s.sequence}, "
                f"'{_sql_escape(s.title)}', '{_sql_escape(s.prompt[:500])}', "
                f"'{s.agent_type}', {s.max_minutes}, 'pending', NULL, NULL, NULL, NULL, NULL, 0)"
            )
        return (
            "INSERT OR REPLACE INTO task_shards "
            "(shard_id, parent_todo_id, sequence, title, prompt, agent_type, "
            "max_minutes, status, agent_id, result_summary, output_file, "
            "started_at, completed_at, retry_count) VALUES\n"
            + ",\n".join(values) + ";"
        )

    @staticmethod
    def get_ready_sql(parent_todo_id: str = None, limit: int = 3) -> str:
        """SQL to find shards ready for dispatch."""
        where = f"AND parent_todo_id = '{parent_todo_id}'" if parent_todo_id else ""
        return (
            f"SELECT * FROM task_shards "
            f"WHERE status = 'pending' {where} "
            f"ORDER BY parent_todo_id, sequence "
            f"LIMIT {limit};"
        )

    @staticmethod
    def mark_dispatched_sql(shard_id: str, agent_id: str) -> str:
        return (
            f"UPDATE task_shards SET status = 'running', "
            f"agent_id = '{agent_id}', started_at = datetime('now') "
            f"WHERE shard_id = '{shard_id}';"
        )

    @staticmethod
    def mark_complete_sql(shard_id: str, summary: str) -> str:
        return (
            f"UPDATE task_shards SET status = 'complete', "
            f"result_summary = '{_sql_escape(summary)}', "
            f"completed_at = datetime('now') "
            f"WHERE shard_id = '{shard_id}';"
        )

    @staticmethod
    def mark_stale_sql(shard_id: str) -> str:
        return (
            f"UPDATE task_shards SET status = 'stale', "
            f"agent_id = NULL "
            f"WHERE shard_id = '{shard_id}';"
        )

    @staticmethod
    def retry_stale_sql(shard_id: str) -> str:
        return (
            f"UPDATE task_shards SET status = 'pending', "
            f"retry_count = retry_count + 1 "
            f"WHERE shard_id = '{shard_id}' AND retry_count < 3;"
        )

    @staticmethod
    def find_stale_sql(max_idle_minutes: int = 8) -> str:
        return (
            f"SELECT * FROM task_shards "
            f"WHERE status = 'running' "
            f"AND started_at < datetime('now', '-{max_idle_minutes} minutes');"
        )

    @staticmethod
    def progress_sql(parent_todo_id: str = None) -> str:
        where = f"WHERE parent_todo_id = '{parent_todo_id}'" if parent_todo_id else ""
        return (
            f"SELECT parent_todo_id, status, COUNT(*) as count "
            f"FROM task_shards {where} "
            f"GROUP BY parent_todo_id, status "
            f"ORDER BY parent_todo_id, status;"
        )

    @staticmethod
    def is_parent_complete_sql(parent_todo_id: str) -> str:
        """Check if all shards for a parent todo are complete."""
        return (
            f"SELECT "
            f"  (SELECT COUNT(*) FROM task_shards WHERE parent_todo_id = '{parent_todo_id}') as total, "
            f"  (SELECT COUNT(*) FROM task_shards WHERE parent_todo_id = '{parent_todo_id}' AND status = 'complete') as done, "
            f"  (SELECT COUNT(*) FROM task_shards WHERE parent_todo_id = '{parent_todo_id}' AND status IN ('stale', 'pending')) as remaining;"
        )


# ═══════════════════════════════════════════════════════════════
# WATCHDOG PROTOCOL — Detect and recover from stale agents
# ═══════════════════════════════════════════════════════════════

class WatchdogProtocol:
    """
    Generates the watchdog check sequence for the orchestrator.

    The orchestrator (Copilot main loop) should run this every 2 minutes:
    1. Check for stale shards (running > max_minutes)
    2. Check for partial results on disk
    3. Re-dispatch stale shards to new agents
    """

    @staticmethod
    def generate_check_sequence() -> str:
        """Returns the SQL + filesystem check sequence as instructions."""
        return """
## Watchdog Check Sequence (run every 2 minutes)

### Step 1: Find stale shards
```sql
SELECT shard_id, agent_id, title, started_at,
       ROUND((julianday('now') - julianday(started_at)) * 1440, 1) as minutes_running
FROM task_shards
WHERE status = 'running'
AND started_at < datetime('now', '-8 minutes');
```

### Step 2: For each stale shard, check for partial results
```python
from agent_resilience_engine import ProgressJournal
result = ProgressJournal.read_result(agent_id)
if result and result['type'] == 'partial':
    # Partial results exist — save them and re-dispatch remainder
    pass
elif result and result['type'] == 'complete':
    # Agent actually finished but didn't report back — mark complete
    pass
else:
    # No results at all — full re-dispatch needed
    pass
```

### Step 3: Re-dispatch stale shards
```sql
-- Reset stale shards for retry (max 3 retries)
UPDATE task_shards SET status = 'pending', retry_count = retry_count + 1
WHERE shard_id IN (...) AND retry_count < 3;

-- Mark permanently failed shards
UPDATE task_shards SET status = 'failed'
WHERE shard_id IN (...) AND retry_count >= 3;
```

### Step 4: Report
```sql
SELECT parent_todo_id, status, COUNT(*) FROM task_shards
GROUP BY parent_todo_id, status;
```
"""

    @staticmethod
    def generate_prompt_wrapper(shard: Shard) -> str:
        """
        Wraps a shard prompt with resilience instructions.

        Tells the agent to:
        1. Write results to disk FIRST (survives death)
        2. Use incremental writes for long tasks
        3. Stay within time budget
        """
        are_dir = r"C:\Users\andre\LitigationOS\temp\are"
        return (
            f"## RESILIENCE-WRAPPED TASK\n\n"
            f"**Shard:** {shard.shard_id}\n"
            f"**Time Budget:** {shard.max_minutes} minutes MAXIMUM\n"
            f"**Output Dir:** {are_dir}\n\n"
            f"### CRITICAL RULES (read first):\n"
            f"1. **WRITE RESULTS TO DISK FIRST** — before reporting anything, write your "
            f"findings to `{are_dir}\\{shard.shard_id}.json`\n"
            f"2. **INCREMENTAL WRITES** — if processing many items, write partial results "
            f"every 20 items to `{are_dir}\\{shard.shard_id}.json` (overwrite with latest)\n"
            f"3. **TIME BUDGET** — if you've been working for {shard.max_minutes - 1} minutes, "
            f"STOP and write whatever you have. Partial results > no results.\n"
            f"4. **SELF-CONTAINED** — this task has ALL context you need. Don't ask questions.\n\n"
            f"### Task\n{shard.prompt}\n\n"
            f"### Output Format\n"
            f"Write JSON to `{are_dir}\\{shard.shard_id}.json`:\n"
            f"```json\n"
            f'{{"shard_id": "{shard.shard_id}", "status": "complete|partial", '
            f'"items_processed": N, "summary": "...", "data": {{...}}}}\n'
            f"```"
        )


# ═══════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════

def _sql_escape(s: str) -> str:
    """Escape single quotes for SQL."""
    if s is None:
        return ""
    return s.replace("'", "''")


def ensure_are_dir():
    """Create the ARE output directory if it doesn't exist."""
    are_dir = Path(r"C:\Users\andre\LitigationOS\temp\are")
    are_dir.mkdir(parents=True, exist_ok=True)
    return are_dir


# ═══════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════

def main():
    """CLI interface for the Agent Resilience Engine."""
    if len(sys.argv) < 2:
        print("Agent Resilience Engine v1.0")
        print("Usage:")
        print("  python agent_resilience_engine.py atomize <parent_todo> <strategy> [context_json]")
        print("  python agent_resilience_engine.py status [parent_todo]")
        print("  python agent_resilience_engine.py read <agent_id>")
        print("  python agent_resilience_engine.py watchdog")
        print("\nStrategies: directory_walk, file_batch, query_batch, sequential, evidence_scan, document_grade")
        return

    cmd = sys.argv[1]

    if cmd == "atomize":
        parent = sys.argv[2] if len(sys.argv) > 2 else "test"
        strategy = sys.argv[3] if len(sys.argv) > 3 else "directory_walk"
        ctx = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}

        atomizer = TaskAtomizer()
        shards = atomizer.atomize(parent, f"Task for {parent}", strategy, context=ctx)

        print(f"\n{'='*60}")
        print(f"  ATOMIZED: {parent} → {len(shards)} shards ({strategy})")
        print(f"{'='*60}\n")

        for s in shards:
            print(f"  [{s.sequence}] {s.shard_id}")
            print(f"      {s.title}")
            print(f"      Agent: {s.agent_type} | Budget: {s.max_minutes}min")
            print()

        # Output SQL for registration
        sql = ShardTracker.register_shards_sql(shards)
        print(f"\n--- SQL to register shards ---\n{sql}\n")

    elif cmd == "read":
        agent_id = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        result = ProgressJournal.read_result(agent_id)
        if result:
            print(json.dumps(result, indent=2))
        else:
            print(f"No results found for agent: {agent_id}")

        journal = ProgressJournal.read_journal(agent_id)
        if journal:
            print(f"\n--- Journal ({len(journal)} entries) ---")
            for entry in journal[-5:]:  # Last 5 entries
                print(f"  [{entry.get('timestamp', '?')}] {entry.get('message', '?')}")

    elif cmd == "watchdog":
        print(WatchdogProtocol.generate_check_sequence())

    elif cmd == "status":
        parent = sys.argv[2] if len(sys.argv) > 2 else None
        print(ShardTracker.progress_sql(parent))

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
