#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     ██╗  ██╗██╗   ██╗██████╗ ██████╗  █████╗                                ║
║     ██║  ██║╚██╗ ██╔╝██╔══██╗██╔══██╗██╔══██╗                               ║
║     ███████║ ╚████╔╝ ██║  ██║██████╔╝███████║                               ║
║     ██╔══██║  ╚██╔╝  ██║  ██║██╔══██╗██╔══██║                               ║
║     ██║  ██║   ██║   ██████╔╝██║  ██║██║  ██║                               ║
║     ╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝                               ║
║                                                                               ║
║     Hyper-resilient Universal Death-proof Runtime Architecture                ║
║     "Cut off one head, two more shall take its place"                        ║
║                                                                               ║
║     v1.0 — LitigationOS Agent Immortality Protocol                          ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  PROBLEM: Agents die from GOAWAY (27-40 min), context compaction,            ║
║  pipe EAGAIN, prompt bloat, and hallucination spirals. When they die,        ║
║  ALL work is lost — 33 minutes of compute evaporated.                        ║
║                                                                               ║
║  SOLUTION: Make agents IMMORTAL through 7 interlocking systems:              ║
║                                                                               ║
║  ┌─────────────────────────────────────────────────────────┐                 ║
║  │  H1  PHOENIX PROTOCOL    — Death-triggered auto-respawn │                 ║
║  │  H2  STREAMING RESULTS   — Write-ahead log, never lose  │                 ║
║  │  H3  COGNITIVE SHARDING  — Smart task decomposition     │                 ║
║  │  H4  PROMPT EVOLUTION    — Failed prompts auto-improve  │                 ║
║  │  H5  PREDICTIVE TIMEOUT  — Kill before GOAWAY kills you │                 ║
║  │  H6  REDUNDANT DISPATCH  — Critical tasks get 2 agents  │                 ║
║  │  H7  GENETIC MEMORY      — Learn from every agent death │                 ║
║  └─────────────────────────────────────────────────────────┘                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import sys
import time
import hashlib
import math
import re
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

HYDRA_DIR = Path(r"C:\Users\andre\LitigationOS\temp\hydra")
HYDRA_DIR.mkdir(parents=True, exist_ok=True)

LITDB = r"C:\Users\andre\LitigationOS\litigation_context.db"


# ═══════════════════════════════════════════════════════════════
# ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class ShardStatus(str, Enum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    STREAMING = "streaming"     # Agent alive, writing results
    COMPLETE = "complete"
    STALE = "stale"             # Agent presumed dead
    PHOENIX = "phoenix"         # Being respawned
    FAILED = "failed"           # 3 retries exhausted
    REDUNDANT = "redundant"     # Backup agent (for critical tasks)

class TaskComplexity(str, Enum):
    TRIVIAL = "trivial"     # <1 min, single command
    SIMPLE = "simple"       # 1-3 min, single agent
    MODERATE = "moderate"   # 3-8 min, may need sharding
    COMPLEX = "complex"     # 8-15 min, must shard
    EPIC = "epic"           # >15 min, multi-wave sharding
    LEGENDARY = "legendary" # >30 min, needs redundancy + streaming

class AgentDNA(str, Enum):
    """Agent archetypes — each has proven prompt patterns."""
    SCANNER = "scanner"         # File/drive scanning
    EXTRACTOR = "extractor"     # Content extraction from documents
    ANALYZER = "analyzer"       # Legal/evidence analysis
    GRADER = "grader"           # Document quality scoring
    BUILDER = "builder"         # Document generation/assembly
    RESEARCHER = "researcher"   # Legal research / DB queries
    ORGANIZER = "organizer"     # File organization / dedup

# Proven time estimates per DNA type (from session history)
DNA_TIME_ESTIMATES = {
    AgentDNA.SCANNER: {"trivial": 1, "simple": 3, "moderate": 7, "complex": 12, "epic": 20},
    AgentDNA.EXTRACTOR: {"trivial": 2, "simple": 4, "moderate": 8, "complex": 15, "epic": 25},
    AgentDNA.ANALYZER: {"trivial": 1, "simple": 3, "moderate": 6, "complex": 12, "epic": 20},
    AgentDNA.GRADER: {"trivial": 1, "simple": 2, "moderate": 5, "complex": 10, "epic": 18},
    AgentDNA.BUILDER: {"trivial": 2, "simple": 5, "moderate": 10, "complex": 18, "epic": 30},
    AgentDNA.RESEARCHER: {"trivial": 1, "simple": 3, "moderate": 7, "complex": 14, "epic": 22},
    AgentDNA.ORGANIZER: {"trivial": 1, "simple": 3, "moderate": 8, "complex": 15, "epic": 25},
}

# Max safe runtime before GOAWAY risk (minutes)
GOAWAY_DANGER_ZONE = 20
GOAWAY_KILL_ZONE = 25
MAX_RETRIES = 3
HEARTBEAT_INTERVAL_SEC = 60
STALE_THRESHOLD_MIN = 8


# ═══════════════════════════════════════════════════════════════
# H1: PHOENIX PROTOCOL — Death-triggered auto-respawn
# ═══════════════════════════════════════════════════════════════

@dataclass
class PhoenixRecord:
    """Records an agent death and the respawn plan."""
    dead_agent_id: str
    shard_id: str
    death_reason: str          # goaway, stale, eagain, context_overflow, hallucination
    partial_results_path: Optional[str]
    items_completed: int
    items_remaining: int
    original_prompt_hash: str
    evolved_prompt: str        # Refined prompt for respawn
    respawn_agent_id: Optional[str] = None
    respawn_at: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, default=str)

    @classmethod
    def from_json(cls, data: dict) -> "PhoenixRecord":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class PhoenixProtocol:
    """
    When an agent dies, Phoenix:
    1. Reads whatever partial results exist on disk
    2. Determines what work remains
    3. Evolves the prompt (shorter, more focused, informed by partial results)
    4. Generates a respawn plan
    """

    @staticmethod
    def detect_death(shard_id: str, agent_id: str, elapsed_min: float) -> Optional[str]:
        """Classify the cause of death."""
        if elapsed_min >= GOAWAY_KILL_ZONE:
            return "goaway"
        if elapsed_min >= STALE_THRESHOLD_MIN:
            # Check for partial results
            result_file = HYDRA_DIR / f"{shard_id}.json"
            journal_file = HYDRA_DIR / f"{shard_id}.journal.jsonl"
            if not result_file.exists() and not journal_file.exists():
                return "stale"  # No output at all
            return "partial_death"  # Had some output, then died
        return None  # Not dead yet

    @staticmethod
    def salvage_results(shard_id: str) -> Tuple[Optional[dict], int]:
        """
        Recover whatever an agent left behind.
        Returns (partial_data, items_completed).
        """
        result_file = HYDRA_DIR / f"{shard_id}.json"
        journal_file = HYDRA_DIR / f"{shard_id}.journal.jsonl"

        partial_data = None
        items = 0

        # Check result file first (most complete)
        if result_file.exists():
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    partial_data = json.load(f)
                items = partial_data.get("items_processed", 0)
            except (json.JSONDecodeError, KeyError):
                pass

        # Check journal for heartbeats
        if journal_file.exists():
            try:
                with open(journal_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for line in reversed(lines):
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("items_processed", 0) > items:
                            items = entry["items_processed"]
                        if not partial_data and entry.get("data"):
                            partial_data = entry
                    except json.JSONDecodeError:
                        continue
            except Exception:
                pass

        return partial_data, items

    @staticmethod
    def generate_respawn(
        shard: "HydraShard",
        death_reason: str,
        partial_data: Optional[dict],
        items_completed: int
    ) -> PhoenixRecord:
        """Generate a Phoenix respawn plan with evolved prompt."""

        # Build evolved prompt
        evolved_parts = [
            f"## PHOENIX RESPAWN — Continuing from dead agent\n",
            f"**Previous agent died after processing {items_completed} items ({death_reason}).**\n",
        ]

        if partial_data:
            # Inject partial results so new agent doesn't redo work
            summary = partial_data.get("summary", "")
            if summary:
                evolved_parts.append(f"**Partial results recovered:** {summary}\n")
            evolved_parts.append(
                f"**DO NOT re-process items already completed.** "
                f"Start from item {items_completed + 1}.\n\n"
            )

        # Shorten the prompt if the original was too long (possible cause of death)
        original_prompt = shard.prompt
        if len(original_prompt) > 2000:
            evolved_parts.append(
                "**NOTE: Original prompt was too long and may have caused context overflow. "
                "Condensed version below.**\n\n"
            )
            # Take first 800 chars + last 800 chars
            original_prompt = original_prompt[:800] + "\n...[condensed]...\n" + original_prompt[-800:]

        evolved_parts.append(f"### Remaining Task\n{original_prompt}\n")

        # Add time awareness
        reduced_budget = max(3, shard.max_minutes - 2)
        evolved_parts.append(
            f"\n### TIME BUDGET: {reduced_budget} minutes MAXIMUM\n"
            f"Write results to `{HYDRA_DIR / shard.shard_id}.json` IMMEDIATELY "
            f"as you work. Partial results > no results.\n"
        )

        return PhoenixRecord(
            dead_agent_id=shard.agent_id or "unknown",
            shard_id=shard.shard_id,
            death_reason=death_reason,
            partial_results_path=str(HYDRA_DIR / f"{shard.shard_id}.json"),
            items_completed=items_completed,
            items_remaining=shard.total_items - items_completed if shard.total_items else -1,
            original_prompt_hash=hashlib.sha256(shard.prompt.encode()).hexdigest()[:12],
            evolved_prompt="\n".join(evolved_parts),
        )


# ═══════════════════════════════════════════════════════════════
# H2: STREAMING RESULTS — Write-ahead log, never lose work
# ═══════════════════════════════════════════════════════════════

class StreamingResultsProtocol:
    """
    Generates prompt instructions that make agents write results
    incrementally to disk as they work.

    The key insight: if agents write to disk FIRST, before reporting,
    their work survives even if they die before completing.
    """

    PREAMBLE = """
### 🔥 HYDRA STREAMING PROTOCOL (READ FIRST — NON-NEGOTIABLE)

You are running under the HYDRA resilience protocol. Your work MUST survive
even if you are killed mid-task. Follow these rules EXACTLY:

**RULE 1: WRITE-AHEAD LOG**
Before processing each batch of items, write your current results to:
  `{output_file}`
Overwrite with the latest version each time. Format:
```json
{{"shard_id": "{shard_id}", "status": "streaming", "items_processed": N,
  "summary": "...", "data": {{...}}, "last_update": "ISO_TIMESTAMP"}}
```

**RULE 2: JOURNAL HEARTBEATS**
Every ~20 items or ~60 seconds, APPEND a line to:
  `{journal_file}`
Format (one JSON per line):
```json
{{"ts": "ISO", "items": N, "msg": "Processing batch 3...", "data_keys": [...]}}
```

**RULE 3: TIME AWARENESS**
You have {max_minutes} minutes. At minute {warn_minute}:
- STOP processing new items
- Write final results to disk
- Report what you completed and what remains

**RULE 4: PARTIAL > NOTHING**
If you can only process 50 of 200 items — that's fine. Write the 50.
A Phoenix agent will pick up the remaining 150.
"""

    @classmethod
    def wrap_prompt(cls, shard: "HydraShard") -> str:
        """Wrap a shard's prompt with streaming instructions."""
        output_file = HYDRA_DIR / f"{shard.shard_id}.json"
        journal_file = HYDRA_DIR / f"{shard.shard_id}.journal.jsonl"

        preamble = cls.PREAMBLE.format(
            output_file=output_file,
            journal_file=journal_file,
            shard_id=shard.shard_id,
            max_minutes=shard.max_minutes,
            warn_minute=max(1, shard.max_minutes - 2),
        )

        return f"{preamble}\n---\n\n{shard.prompt}"


# ═══════════════════════════════════════════════════════════════
# H3: COGNITIVE SHARDING — Smart task decomposition
# ═══════════════════════════════════════════════════════════════

@dataclass
class HydraShard:
    """Enhanced shard with HYDRA metadata."""
    shard_id: str
    parent_todo_id: str
    sequence: int
    title: str
    prompt: str
    agent_type: str = "general-purpose"
    agent_dna: str = "scanner"
    max_minutes: int = 5
    complexity: str = "simple"
    status: str = "pending"
    agent_id: Optional[str] = None
    result_summary: Optional[str] = None
    total_items: Optional[int] = None  # Expected item count
    items_done: int = 0
    retry_count: int = 0
    phoenix_count: int = 0        # Times respawned
    is_critical: bool = False     # Critical = gets redundant dispatch
    depends_on: Optional[str] = None  # Shard dependency

    def hydra_prompt(self) -> str:
        """Generate full HYDRA-wrapped prompt."""
        return StreamingResultsProtocol.wrap_prompt(self)

    def to_sql_values(self) -> str:
        """SQL INSERT values."""
        return (
            f"('{self.shard_id}', '{self.parent_todo_id}', {self.sequence}, "
            f"'{_esc(self.title)}', '{_esc(self.prompt[:500])}', "
            f"'{self.agent_type}', '{self.agent_dna}', {self.max_minutes}, "
            f"'{self.complexity}', '{self.status}', "
            f"{self.total_items or 'NULL'}, {self.items_done}, "
            f"{self.retry_count}, {self.phoenix_count}, "
            f"{'1' if self.is_critical else '0'}, "
            f"'{self.depends_on or ''}'"
            f")"
        )


class CognitiveShardEngine:
    """
    Smart task decomposition that considers:
    - Estimated complexity (not just item count)
    - Agent DNA (what type of agent handles this best)
    - GOAWAY danger zones (never assign >20 min tasks)
    - Dependency chains (shard B needs shard A's output)
    - Criticality (mission-critical shards get redundancy)
    """

    @staticmethod
    def estimate_complexity(
        description: str,
        item_count: int = 0,
        involves_ocr: bool = False,
        involves_llm: bool = False,
        involves_network: bool = False,
    ) -> TaskComplexity:
        """Estimate task complexity from description and metadata."""
        score = 0

        # Item count scoring
        if item_count > 1000: score += 5
        elif item_count > 200: score += 4
        elif item_count > 50: score += 3
        elif item_count > 10: score += 2
        else: score += 1

        # Content analysis
        complex_keywords = ["extract", "analyze", "grade", "compare", "deduplicate",
                           "cross-reference", "validate", "compile", "generate"]
        simple_keywords = ["list", "count", "find", "search", "inventory"]

        desc_lower = description.lower()
        score += sum(2 for kw in complex_keywords if kw in desc_lower)
        score -= sum(1 for kw in simple_keywords if kw in desc_lower)

        # Modifiers
        if involves_ocr: score += 3
        if involves_llm: score += 2
        if involves_network: score += 2

        # Classify
        if score <= 2: return TaskComplexity.TRIVIAL
        elif score <= 4: return TaskComplexity.SIMPLE
        elif score <= 7: return TaskComplexity.MODERATE
        elif score <= 10: return TaskComplexity.COMPLEX
        elif score <= 14: return TaskComplexity.EPIC
        else: return TaskComplexity.LEGENDARY

    @staticmethod
    def select_dna(description: str) -> AgentDNA:
        """Select the optimal agent DNA type for a task."""
        desc_lower = description.lower()

        dna_signals = {
            AgentDNA.SCANNER: ["scan", "inventory", "list", "find", "count", "drive", "directory"],
            AgentDNA.EXTRACTOR: ["extract", "ocr", "parse", "read", "content", "text", "pdf"],
            AgentDNA.ANALYZER: ["analyz", "pattern", "contradiction", "impeach", "bias", "violat"],
            AgentDNA.GRADER: ["grade", "score", "rubric", "quality", "audit", "compliance"],
            AgentDNA.BUILDER: ["draft", "generate", "write", "create", "motion", "brief", "filing"],
            AgentDNA.RESEARCHER: ["research", "case law", "authority", "mcr", "mcl", "statute"],
            AgentDNA.ORGANIZER: ["organize", "dedup", "consolidate", "flatten", "move", "sort"],
        }

        scores = {dna: 0 for dna in AgentDNA}
        for dna, signals in dna_signals.items():
            for signal in signals:
                if signal in desc_lower:
                    scores[dna] += 1

        return max(scores, key=scores.get) if max(scores.values()) > 0 else AgentDNA.SCANNER

    @classmethod
    def shard(
        cls,
        parent_todo_id: str,
        title: str,
        description: str,
        context: Optional[dict] = None,
        is_critical: bool = False,
    ) -> List[HydraShard]:
        """
        Intelligently shard a task based on complexity analysis.

        Returns optimally-sized shards that:
        - Never exceed GOAWAY_DANGER_ZONE minutes
        - Have the right agent DNA
        - Include streaming + Phoenix instructions
        - Chain dependencies where needed
        """
        ctx = context or {}
        item_count = ctx.get("item_count", 0)
        items = ctx.get("items", [])
        if items and not item_count:
            item_count = len(items)

        complexity = cls.estimate_complexity(
            description, item_count,
            involves_ocr=ctx.get("ocr", False),
            involves_llm=ctx.get("llm", False),
        )
        dna = cls.select_dna(description)

        # Get time estimate from DNA table
        time_est = DNA_TIME_ESTIMATES.get(dna, {}).get(complexity.value, 10)

        # If under danger zone, single shard
        if time_est <= GOAWAY_DANGER_ZONE and complexity.value in ("trivial", "simple", "moderate"):
            return [HydraShard(
                shard_id=f"{parent_todo_id}-hydra-0",
                parent_todo_id=parent_todo_id,
                sequence=0,
                title=title,
                prompt=description,
                agent_dna=dna.value,
                max_minutes=min(time_est + 3, GOAWAY_DANGER_ZONE),  # Buffer
                complexity=complexity.value,
                total_items=item_count,
                is_critical=is_critical,
            )]

        # Need to shard — calculate optimal shard size
        if item_count > 0:
            # Items per minute (conservative estimate)
            items_per_min = {
                AgentDNA.SCANNER: 100,
                AgentDNA.EXTRACTOR: 10,
                AgentDNA.ANALYZER: 5,
                AgentDNA.GRADER: 3,
                AgentDNA.BUILDER: 2,
                AgentDNA.RESEARCHER: 8,
                AgentDNA.ORGANIZER: 50,
            }.get(dna, 10)

            target_shard_minutes = 5  # Optimal shard time
            items_per_shard = items_per_min * target_shard_minutes
            num_shards = max(1, math.ceil(item_count / items_per_shard))
            actual_per_shard = math.ceil(item_count / num_shards)
        else:
            # No item count — shard by logical steps
            num_shards = max(1, math.ceil(time_est / 5))
            actual_per_shard = 0

        shards = []
        for i in range(num_shards):
            start_idx = i * actual_per_shard if actual_per_shard else 0
            end_idx = min((i + 1) * actual_per_shard, item_count) if actual_per_shard else 0

            shard_items = items[start_idx:end_idx] if items else []
            shard_count = end_idx - start_idx if actual_per_shard else 0

            shard_prompt = description
            if shard_items:
                shard_prompt += (
                    f"\n\n**THIS SHARD: Process items {start_idx + 1} to {end_idx} "
                    f"(of {item_count} total).**\n"
                    f"Items:\n" + "\n".join(f"- {item}" for item in shard_items[:50])
                )
                if len(shard_items) > 50:
                    shard_prompt += f"\n... and {len(shard_items) - 50} more"
            elif num_shards > 1:
                shard_prompt += (
                    f"\n\n**THIS SHARD: Part {i + 1} of {num_shards}.** "
                    f"Focus on the next logical chunk of work."
                )

            shards.append(HydraShard(
                shard_id=f"{parent_todo_id}-hydra-{i}",
                parent_todo_id=parent_todo_id,
                sequence=i,
                title=f"{title} [{i + 1}/{num_shards}]",
                prompt=shard_prompt,
                agent_dna=dna.value,
                max_minutes=min(target_shard_minutes + 3, GOAWAY_DANGER_ZONE) if actual_per_shard else min(8, GOAWAY_DANGER_ZONE),
                complexity=complexity.value,
                total_items=shard_count,
                is_critical=is_critical,
                depends_on=f"{parent_todo_id}-hydra-{i - 1}" if i > 0 and ctx.get("sequential", False) else None,
            ))

        return shards


# ═══════════════════════════════════════════════════════════════
# H4: PROMPT EVOLUTION — Failed prompts auto-improve
# ═══════════════════════════════════════════════════════════════

class PromptEvolver:
    """
    Evolves prompts based on failure patterns.

    When an agent fails, the prompt is analyzed and mutated to avoid
    the same failure mode. Mutations are stored for future reference.
    """

    # Known failure patterns and their fixes
    FAILURE_MUTATIONS = {
        "goaway": [
            ("REDUCE_SCOPE", "Add: 'Process only the first {N} items. Write results and stop.'"),
            ("ADD_CHECKPOINTS", "Add: 'Write partial results every 10 items to {output_file}.'"),
            ("SIMPLIFY", "Remove complex analysis requirements. Focus on data extraction only."),
        ],
        "stale": [
            ("CLARIFY_TASK", "Rewrite prompt with explicit step-by-step instructions."),
            ("ADD_EXAMPLES", "Add concrete input/output examples."),
            ("REDUCE_AMBIGUITY", "Replace open-ended language with specific requirements."),
        ],
        "hallucination": [
            ("ADD_CONSTRAINTS", "Add: 'ONLY report data you find in the specified files/DB. Never fabricate.'"),
            ("ADD_VERIFICATION", "Add: 'For each fact, cite the exact file path and line number.'"),
            ("REDUCE_CREATIVITY", "Add: 'Output raw data only. No analysis, no interpretation.'"),
        ],
        "context_overflow": [
            ("SPLIT_PROMPT", "Split into 2 separate shards with smaller prompts."),
            ("COMPRESS_CONTEXT", "Remove redundant context. Keep only essential instructions."),
            ("USE_FILE_REFS", "Replace inline data with file path references."),
        ],
        "partial_death": [
            ("CONTINUE_FROM", "Inject partial results and add: 'Continue from item {N}.'"),
            ("REDUCE_BATCH", "Halve the batch size for the remaining items."),
        ],
    }

    @classmethod
    def evolve(cls, prompt: str, failure_type: str, attempt: int = 1) -> str:
        """Evolve a prompt based on its failure mode."""
        mutations = cls.FAILURE_MUTATIONS.get(failure_type, cls.FAILURE_MUTATIONS["stale"])

        # Select mutation based on attempt number (cycle through options)
        mutation_idx = (attempt - 1) % len(mutations)
        mutation_name, mutation_desc = mutations[mutation_idx]

        evolved = f"## ⚡ EVOLVED PROMPT (attempt {attempt + 1}, mutation: {mutation_name})\n"
        evolved += f"**Previous attempt failed due to: {failure_type}**\n"
        evolved += f"**Applied fix: {mutation_desc}**\n\n"

        # Apply specific mutations
        if mutation_name == "REDUCE_SCOPE":
            # Cut item counts in half
            evolved += re.sub(
                r'(\d{3,})\s*(items|files|documents|records)',
                lambda m: f"{int(m.group(1)) // 2} {m.group(2)} (REDUCED — process this batch only)",
                prompt
            )
        elif mutation_name == "SIMPLIFY":
            # Strip analysis requirements
            evolved += prompt
            evolved += "\n\n**SIMPLIFIED MODE: Skip analysis. Extract raw data only. Speed > depth.**"
        elif mutation_name == "CONTINUE_FROM":
            evolved += prompt
            evolved += "\n\n**CONTINUATION MODE: Skip already-processed items. Start fresh from where the last agent stopped.**"
        else:
            evolved += prompt

        # Always add time awareness on retry
        evolved += f"\n\n**TIME LIMIT: 5 minutes. At 4 minutes, STOP and write what you have.**"

        return evolved

    @classmethod
    def record_evolution(cls, shard_id: str, failure_type: str, 
                         original_hash: str, evolved_hash: str) -> dict:
        """Record a prompt evolution event for genetic memory."""
        record = {
            "shard_id": shard_id,
            "failure_type": failure_type,
            "original_hash": original_hash,
            "evolved_hash": evolved_hash,
            "timestamp": datetime.now().isoformat(),
        }
        # Append to evolution log
        log_file = HYDRA_DIR / "evolution_log.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return record


# ═══════════════════════════════════════════════════════════════
# H5: PREDICTIVE TIMEOUT — Kill before GOAWAY kills you
# ═══════════════════════════════════════════════════════════════

class PredictiveTimeout:
    """
    Estimates when an agent will hit the GOAWAY wall and generates
    pre-emptive checkpoint instructions.

    Uses DNA-based time estimates + historical data to predict:
    - When the agent should start wrapping up
    - When to force-checkpoint
    - When to declare stale
    """

    @staticmethod
    def calculate_deadlines(shard: HydraShard) -> dict:
        """Calculate critical deadlines for a shard."""
        budget = shard.max_minutes
        return {
            "soft_deadline_min": max(1, budget - 2),     # Start wrapping up
            "hard_deadline_min": max(2, budget - 1),     # Force write results
            "stale_threshold_min": budget + 3,            # Declare dead
            "goaway_danger_min": GOAWAY_DANGER_ZONE,      # System-wide danger
            "budget_minutes": budget,
        }

    @staticmethod
    def generate_time_instructions(shard: HydraShard) -> str:
        """Generate time-aware instructions for the agent prompt."""
        deadlines = PredictiveTimeout.calculate_deadlines(shard)
        return (
            f"\n### ⏰ TIME MANAGEMENT (HYDRA Predictive Timeout)\n"
            f"- **Budget:** {deadlines['budget_minutes']} minutes total\n"
            f"- **Minute {deadlines['soft_deadline_min']}:** Start wrapping up. "
            f"Finish current item, then write results.\n"
            f"- **Minute {deadlines['hard_deadline_min']}:** HARD STOP. Write "
            f"whatever you have to disk immediately.\n"
            f"- **DO NOT** try to 'squeeze in one more item' past the soft deadline.\n"
            f"- **Partial results written to disk will be picked up by a Phoenix agent.**\n"
        )

    @staticmethod
    def is_in_danger_zone(elapsed_minutes: float) -> Tuple[bool, str]:
        """Check if an agent is approaching danger."""
        if elapsed_minutes >= GOAWAY_KILL_ZONE:
            return True, "CRITICAL: Past GOAWAY kill zone. Agent likely dead."
        if elapsed_minutes >= GOAWAY_DANGER_ZONE:
            return True, "WARNING: In GOAWAY danger zone. Read results NOW."
        if elapsed_minutes >= 15:
            return False, "CAUTION: Approaching danger zone. Monitor closely."
        return False, "OK: Within safe operating window."


# ═══════════════════════════════════════════════════════════════
# H6: REDUNDANT DISPATCH — Critical tasks get 2 agents
# ═══════════════════════════════════════════════════════════════

class RedundantDispatch:
    """
    For mission-critical shards, dispatch 2 agents with slightly
    different prompts. First to complete wins; other is cancelled.

    Use sparingly — burns 2x agent budget.
    """

    @staticmethod
    def should_duplicate(shard: HydraShard) -> bool:
        """Determine if a shard warrants redundant dispatch."""
        if not shard.is_critical:
            return False
        if shard.complexity in ("epic", "legendary"):
            return True
        if shard.phoenix_count >= 2:
            return True  # Died twice — try two agents
        return False

    @staticmethod
    def create_variant(shard: HydraShard) -> HydraShard:
        """Create a variant shard with a different approach."""
        variant = HydraShard(
            shard_id=f"{shard.shard_id}-variant",
            parent_todo_id=shard.parent_todo_id,
            sequence=shard.sequence,
            title=f"{shard.title} [VARIANT]",
            prompt=(
                f"## ALTERNATIVE APPROACH\n\n"
                f"A primary agent is also working on this task. "
                f"Use a DIFFERENT strategy than the obvious approach.\n\n"
                f"If the obvious approach is top-down, try bottom-up.\n"
                f"If the obvious approach is exhaustive, try sampling.\n"
                f"If the obvious approach is file-based, try DB-based.\n\n"
                f"### Original Task\n{shard.prompt}"
            ),
            agent_type=shard.agent_type,
            agent_dna=shard.agent_dna,
            max_minutes=shard.max_minutes,
            complexity=shard.complexity,
            total_items=shard.total_items,
            is_critical=True,
            status="redundant",
        )
        return variant


# ═══════════════════════════════════════════════════════════════
# H7: GENETIC MEMORY — Learn from every agent death
# ═══════════════════════════════════════════════════════════════

class GeneticMemory:
    """
    Maintains a database of what works and what doesn't across sessions.

    Tracks:
    - Which prompt patterns succeed vs fail
    - Which DNA types work best for which task types
    - Average completion times by DNA × complexity
    - Common failure modes and their fixes
    """

    MEMORY_FILE = HYDRA_DIR / "genetic_memory.json"

    @classmethod
    def load(cls) -> dict:
        if cls.MEMORY_FILE.exists():
            try:
                with open(cls.MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "successes": [],
            "failures": [],
            "dna_performance": {},
            "prompt_patterns": {},
            "total_agents_spawned": 0,
            "total_agents_died": 0,
            "total_phoenix_respawns": 0,
            "total_items_processed": 0,
        }

    @classmethod
    def save(cls, memory: dict):
        with open(cls.MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, indent=2, default=str)

    @classmethod
    def record_success(cls, shard: HydraShard, elapsed_min: float, items: int):
        memory = cls.load()
        memory["successes"].append({
            "shard_id": shard.shard_id,
            "dna": shard.agent_dna,
            "complexity": shard.complexity,
            "elapsed_min": elapsed_min,
            "items": items,
            "prompt_len": len(shard.prompt),
            "ts": datetime.now().isoformat(),
        })
        memory["total_agents_spawned"] += 1
        memory["total_items_processed"] += items

        # Update DNA performance stats
        key = f"{shard.agent_dna}_{shard.complexity}"
        if key not in memory["dna_performance"]:
            memory["dna_performance"][key] = {"successes": 0, "failures": 0, "avg_min": 0}
        perf = memory["dna_performance"][key]
        perf["successes"] += 1
        perf["avg_min"] = (perf["avg_min"] * (perf["successes"] - 1) + elapsed_min) / perf["successes"]

        # Keep last 100 entries
        memory["successes"] = memory["successes"][-100:]
        cls.save(memory)

    @classmethod
    def record_failure(cls, shard: HydraShard, elapsed_min: float, reason: str):
        memory = cls.load()
        memory["failures"].append({
            "shard_id": shard.shard_id,
            "dna": shard.agent_dna,
            "complexity": shard.complexity,
            "elapsed_min": elapsed_min,
            "reason": reason,
            "prompt_len": len(shard.prompt),
            "retry_count": shard.retry_count,
            "ts": datetime.now().isoformat(),
        })
        memory["total_agents_died"] += 1

        key = f"{shard.agent_dna}_{shard.complexity}"
        if key not in memory["dna_performance"]:
            memory["dna_performance"][key] = {"successes": 0, "failures": 0, "avg_min": 0}
        memory["dna_performance"][key]["failures"] += 1

        memory["failures"] = memory["failures"][-100:]
        cls.save(memory)

    @classmethod
    def record_phoenix(cls):
        memory = cls.load()
        memory["total_phoenix_respawns"] += 1
        cls.save(memory)

    @classmethod
    def get_optimal_budget(cls, dna: str, complexity: str) -> int:
        """Get optimal time budget based on historical performance."""
        memory = cls.load()
        key = f"{dna}_{complexity}"
        perf = memory.get("dna_performance", {}).get(key)
        if perf and perf["successes"] >= 3:
            # Use historical average + 50% buffer
            return min(int(perf["avg_min"] * 1.5) + 1, GOAWAY_DANGER_ZONE)
        # Fall back to DNA table estimate
        return DNA_TIME_ESTIMATES.get(AgentDNA(dna), {}).get(complexity, 8)

    @classmethod
    def dashboard(cls) -> str:
        """Generate a genetic memory dashboard."""
        memory = cls.load()
        total = memory["total_agents_spawned"]
        died = memory["total_agents_died"]
        phoenix = memory["total_phoenix_respawns"]
        items = memory["total_items_processed"]
        survival = ((total - died) / total * 100) if total else 0

        lines = [
            "╔═══════════════════════════════════════════════╗",
            "║        HYDRA GENETIC MEMORY DASHBOARD         ║",
            "╠═══════════════════════════════════════════════╣",
            f"║  Agents Spawned:  {total:>6}                      ║",
            f"║  Agents Died:     {died:>6}                      ║",
            f"║  Phoenix Respawns:{phoenix:>6}                      ║",
            f"║  Survival Rate:   {survival:>5.1f}%                     ║",
            f"║  Items Processed: {items:>6}                      ║",
            "╠═══════════════════════════════════════════════╣",
            "║  DNA Performance:                             ║",
        ]

        for key, perf in sorted(memory.get("dna_performance", {}).items()):
            s, f = perf["successes"], perf["failures"]
            rate = (s / (s + f) * 100) if (s + f) > 0 else 0
            avg = perf.get("avg_min", 0)
            lines.append(f"║  {key:<20} {rate:>5.0f}% ok  ~{avg:.1f}min  ║")

        lines += [
            "╚═══════════════════════════════════════════════╝",
        ]
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# HYDRA ORCHESTRATOR — Ties all 7 systems together
# ═══════════════════════════════════════════════════════════════

class HydraOrchestrator:
    """
    The master orchestrator that combines all 7 HYDRA systems.

    Usage from Copilot main loop:
    1. hydra.prepare(todo_id, description, context) → List[HydraShard]
    2. For each shard: dispatch agent with shard.hydra_prompt()
    3. On agent completion: hydra.on_complete(shard_id, agent_result)
    4. On agent timeout: hydra.on_death(shard_id, reason) → PhoenixRecord
    5. Every 2 min: hydra.watchdog_check() → List of stale shards
    6. After all shards: hydra.finalize(todo_id) → merged results
    """

    def __init__(self):
        self.sharder = CognitiveShardEngine()
        self.phoenix = PhoenixProtocol()
        self.evolver = PromptEvolver()
        self.timeout = PredictiveTimeout()
        self.memory = GeneticMemory()
        self.redundancy = RedundantDispatch()

    def prepare(
        self,
        todo_id: str,
        title: str,
        description: str,
        context: Optional[dict] = None,
        is_critical: bool = False,
    ) -> List[HydraShard]:
        """
        Prepare a todo for HYDRA-protected execution.
        Returns shards with full HYDRA instrumentation.
        """
        # Step 1: Cognitive sharding
        shards = self.sharder.shard(todo_id, title, description, context, is_critical)

        # Step 2: Optimize time budgets from genetic memory
        for shard in shards:
            optimal = self.memory.get_optimal_budget(shard.agent_dna, shard.complexity)
            shard.max_minutes = min(optimal, GOAWAY_DANGER_ZONE)

        # Step 3: Add streaming + timeout instructions to prompts
        for shard in shards:
            shard.prompt = StreamingResultsProtocol.wrap_prompt(shard)
            shard.prompt += self.timeout.generate_time_instructions(shard)

        # Step 4: Generate redundant variants for critical shards
        variants = []
        for shard in shards:
            if self.redundancy.should_duplicate(shard):
                variants.append(self.redundancy.create_variant(shard))
        shards.extend(variants)

        return shards

    def on_complete(self, shard: HydraShard, elapsed_min: float, items: int, summary: str):
        """Handle successful shard completion."""
        shard.status = ShardStatus.COMPLETE.value
        shard.items_done = items
        shard.result_summary = summary
        self.memory.record_success(shard, elapsed_min, items)

    def on_death(self, shard: HydraShard, elapsed_min: float, reason: str) -> Optional[PhoenixRecord]:
        """Handle agent death — trigger Phoenix respawn."""
        self.memory.record_failure(shard, elapsed_min, reason)

        if shard.retry_count >= MAX_RETRIES:
            shard.status = ShardStatus.FAILED.value
            return None  # Give up after 3 tries

        # Salvage partial results
        partial, items_done = self.phoenix.salvage_results(shard.shard_id)

        # Generate Phoenix respawn
        phoenix_record = self.phoenix.generate_respawn(shard, reason, partial, items_done)

        # Evolve the prompt
        phoenix_record.evolved_prompt = self.evolver.evolve(
            shard.prompt, reason, shard.retry_count
        )

        # Update shard for retry
        shard.status = ShardStatus.PHOENIX.value
        shard.retry_count += 1
        shard.phoenix_count += 1
        shard.items_done = items_done
        shard.prompt = phoenix_record.evolved_prompt

        self.memory.record_phoenix()

        # Save Phoenix record
        phoenix_file = HYDRA_DIR / f"phoenix_{shard.shard_id}_{shard.phoenix_count}.json"
        with open(phoenix_file, 'w', encoding='utf-8') as f:
            f.write(phoenix_record.to_json())

        return phoenix_record

    def watchdog_check(self, active_shards: List[dict]) -> List[dict]:
        """
        Check for stale agents. Call every 2 minutes.

        Args:
            active_shards: List of {"shard_id", "agent_id", "started_at", "elapsed_min"}

        Returns:
            List of shards that need Phoenix respawn
        """
        stale = []
        for info in active_shards:
            elapsed = info.get("elapsed_min", 0)
            in_danger, msg = self.timeout.is_in_danger_zone(elapsed)

            if elapsed >= STALE_THRESHOLD_MIN:
                # Check for heartbeats
                result_file = HYDRA_DIR / f"{info['shard_id']}.json"
                journal_file = HYDRA_DIR / f"{info['shard_id']}.journal.jsonl"

                has_recent_output = False
                if result_file.exists():
                    age_min = (time.time() - result_file.stat().st_mtime) / 60
                    has_recent_output = age_min < 3  # Updated within 3 min
                if journal_file.exists():
                    age_min = (time.time() - journal_file.stat().st_mtime) / 60
                    if age_min < 3:
                        has_recent_output = True

                if not has_recent_output:
                    stale.append({**info, "reason": "stale", "message": msg})
                elif in_danger:
                    stale.append({**info, "reason": "danger_zone", "message": msg})

        return stale

    def finalize(self, todo_id: str) -> dict:
        """
        Merge all shard results for a todo into a final result.
        """
        results = []
        total_items = 0

        # Read all shard result files
        for result_file in sorted(HYDRA_DIR.glob(f"{todo_id}-hydra-*.json")):
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                results.append(data)
                total_items += data.get("items_processed", 0)
            except (json.JSONDecodeError, IOError):
                continue

        return {
            "todo_id": todo_id,
            "shard_count": len(results),
            "total_items": total_items,
            "status": "complete" if results else "no_results",
            "shards": results,
            "finalized_at": datetime.now().isoformat(),
        }

    def generate_sql_schema(self) -> str:
        """Generate the full HYDRA SQL schema."""
        return """
-- HYDRA Protocol SQL Schema
CREATE TABLE IF NOT EXISTS hydra_shards (
    shard_id TEXT PRIMARY KEY,
    parent_todo_id TEXT NOT NULL,
    sequence INTEGER NOT NULL,
    title TEXT NOT NULL,
    prompt_hash TEXT,
    agent_type TEXT DEFAULT 'general-purpose',
    agent_dna TEXT DEFAULT 'scanner',
    max_minutes INTEGER DEFAULT 5,
    complexity TEXT DEFAULT 'simple',
    status TEXT DEFAULT 'pending',
    agent_id TEXT,
    result_summary TEXT,
    total_items INTEGER,
    items_done INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    phoenix_count INTEGER DEFAULT 0,
    is_critical INTEGER DEFAULT 0,
    depends_on TEXT,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS hydra_heartbeats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shard_id TEXT NOT NULL,
    agent_id TEXT,
    items_processed INTEGER DEFAULT 0,
    message TEXT,
    heartbeat_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS hydra_phoenix_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shard_id TEXT NOT NULL,
    dead_agent_id TEXT,
    death_reason TEXT,
    items_salvaged INTEGER DEFAULT 0,
    evolved_prompt_hash TEXT,
    respawn_agent_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS hydra_genetic_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_dna TEXT,
    complexity TEXT,
    outcome TEXT,
    elapsed_minutes REAL,
    items_processed INTEGER,
    prompt_length INTEGER,
    failure_reason TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_hydra_shards_status ON hydra_shards(status);
CREATE INDEX IF NOT EXISTS idx_hydra_shards_parent ON hydra_shards(parent_todo_id);
CREATE INDEX IF NOT EXISTS idx_hydra_heartbeats_shard ON hydra_heartbeats(shard_id);
CREATE INDEX IF NOT EXISTS idx_hydra_phoenix_shard ON hydra_phoenix_log(shard_id);
"""


# ═══════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════

def _esc(s: str) -> str:
    """SQL-safe string escaping."""
    return (s or "").replace("'", "''")


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("""
╔═══════════════════════════════════════════════════════════════╗
║              HYDRA Protocol v1.0 — Agent Immortality          ║
╠═══════════════════════════════════════════════════════════════╣
║                                                               ║
║  Commands:                                                    ║
║    shard <todo_id> <description> [context_json]               ║
║    phoenix <shard_id>           — Respawn a dead shard        ║
║    watchdog                     — Check for stale agents      ║
║    dashboard                    — Genetic memory dashboard    ║
║    schema                       — Print SQL schema            ║
║    status <todo_id>             — Shard completion status      ║
║    finalize <todo_id>           — Merge shard results         ║
║                                                               ║
║  7 Systems:                                                   ║
║    H1 Phoenix Protocol    — Auto-respawn dead agents          ║
║    H2 Streaming Results   — Write-ahead log, never lose       ║
║    H3 Cognitive Sharding  — Smart task decomposition          ║
║    H4 Prompt Evolution    — Failed prompts auto-improve       ║
║    H5 Predictive Timeout  — Kill before GOAWAY kills you      ║
║    H6 Redundant Dispatch  — Critical tasks get 2 agents       ║
║    H7 Genetic Memory      — Learn from every agent death      ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")
        return

    cmd = sys.argv[1]
    hydra = HydraOrchestrator()

    if cmd == "shard":
        todo_id = sys.argv[2] if len(sys.argv) > 2 else "test"
        desc = sys.argv[3] if len(sys.argv) > 3 else "Test task"
        ctx = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}

        shards = hydra.prepare(todo_id, f"Task: {todo_id}", desc, ctx)

        print(f"\n{'='*60}")
        print(f"  HYDRA SHARDING: {todo_id} → {len(shards)} shards")
        print(f"{'='*60}\n")

        for s in shards:
            print(f"  [{s.sequence}] {s.shard_id}")
            print(f"      DNA: {s.agent_dna} | Complexity: {s.complexity}")
            print(f"      Budget: {s.max_minutes}min | Items: {s.total_items or '?'}")
            print(f"      Critical: {'YES' if s.is_critical else 'no'}")
            if s.depends_on:
                print(f"      Depends on: {s.depends_on}")
            print()

    elif cmd == "phoenix":
        shard_id = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        partial, items = PhoenixProtocol.salvage_results(shard_id)
        if partial:
            print(f"Salvaged {items} items from {shard_id}")
            print(json.dumps(partial, indent=2)[:500])
        else:
            print(f"No salvageable results for {shard_id}")

    elif cmd == "dashboard":
        print(GeneticMemory.dashboard())

    elif cmd == "schema":
        print(hydra.generate_sql_schema())

    elif cmd == "finalize":
        todo_id = sys.argv[2] if len(sys.argv) > 2 else "test"
        result = hydra.finalize(todo_id)
        print(json.dumps(result, indent=2))

    elif cmd == "status":
        todo_id = sys.argv[2] if len(sys.argv) > 2 else "test"
        files = list(HYDRA_DIR.glob(f"{todo_id}-hydra-*.json"))
        print(f"Shard results found: {len(files)}")
        for f in sorted(files):
            try:
                with open(f, 'r', encoding='utf-8') as fh:
                    data = json.load(fh)
                status = data.get("status", "?")
                items = data.get("items_processed", 0)
                print(f"  {f.stem}: {status} ({items} items)")
            except Exception:
                print(f"  {f.stem}: [unreadable]")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
