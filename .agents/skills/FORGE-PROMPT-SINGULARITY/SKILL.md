---
name: FORGE-PROMPT-SINGULARITY
description: >-
  Unified cognitive architecture superskill that fuses prompt engineering,
  token optimization, RAG pipeline synthesis, agent memory architecture,
  LLM evaluation, fine-tuning, AI safety alignment, embedding specialist
  knowledge, multi-modal AI, and LLM orchestration into a single
  self-improving intelligence layer. Designs complete AI cognitive
  architectures from a single intent — prompt chains that evaluate
  themselves, retrieve context, maintain memory, enforce guardrails,
  handle multi-modal input, and orchestrate tool calls. The prompt
  engineers itself through iterative optimization loops.
category: intelligence
version: "1.0.0"
triggers:
  - "prompt singularity"
  - "cognitive architecture"
  - "self-improving prompt"
  - "prompt chain design"
  - "RAG pipeline"
  - "agent memory design"
  - "prompt optimization"
  - "AI safety prompt"
  - "multi-modal prompt"
  - "LLM orchestration"
  - "prompt evaluation loop"
  - "forge prompt"
metadata:
  tier: FORGE
  fused_skills: 10
  author: andrew-pigors + copilot-omega-delta-99
  forge_date: 2026-03-27
  forge_class: intelligence
  emergent_capability: >-
    Cognitive Architecture Synthesis — designs complete AI cognitive
    architectures from a single intent. Self-improving prompt chains
    that evaluate, retrieve, remember, guard, perceive, and orchestrate.
    The prompt engineers itself.
---

# 🧠 FORGE-PROMPT-SINGULARITY
## (Ω-Δ99)

> **The prompt that engineers itself.**
>
> FORGE-PROMPT-SINGULARITY is the convergence of 10 specialized AI/LLM
> skills into one unified cognitive architecture engine. It doesn't just
> write prompts — it designs self-improving AI systems that evaluate their
> own output, retrieve missing context, maintain persistent memory, enforce
> safety guardrails, process multi-modal input, and orchestrate complex
> tool chains — all from a single user intent.
>
> | Property   | Value                                    |
> |------------|------------------------------------------|
> | **Tier**   | FORGE (Fused Omega-Recursive Generation) |
> | **Domain** | AI/LLM Intelligence Architecture         |
> | **Scope**  | Full cognitive pipeline — intent to agent |
> | **Emergent** | Cognitive Architecture Synthesis        |

---

## 📊 Forged from 10 Skills

| #  | Source Skill               | Core Capability                         | Module Target |
|----|----------------------------|-----------------------------------------|---------------|
| 1  | prompt-engineering-master  | Chain-of-thought, few-shot, meta-prompt | PS1           |
| 2  | prompt-optimization        | Token compression, iterative refinement | PS2           |
| 3  | llm-evaluation             | BLEU, ROUGE, semantic similarity, human | PS5           |
| 4  | rag-engineer               | Chunking, embedding, reranking, hybrid  | PS3           |
| 5  | agent-memory-architect     | Episodic, semantic, working memory      | PS4           |
| 6  | llm-fine-tuning            | LoRA, QLoRA, dataset prep, training     | PS5           |
| 7  | ai-safety-alignment        | Guardrails, ConstitutionalAI, red-team  | PS6           |
| 8  | embedding-specialist       | Vector DBs, similarity, hybrid search   | PS3           |
| 9  | multi-modal-ai             | Vision, audio, document, tool-use       | PS7           |
| 10 | llm-orchestration          | LangChain, LlamaIndex, function call    | PS8           |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    FORGE-PROMPT-SINGULARITY  (Ω-Δ99)                        │
│                                                                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐                 │
│  │   PS1    │──▶│   PS2    │──▶│   PS3    │──▶│   PS4    │                 │
│  │ Prompt   │   │ Token    │   │  RAG     │   │ Memory   │                 │
│  │ Arch.    │   │ Optim.   │   │ Pipeline │   │ Arch.    │                 │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘                 │
│       │              │              │              │                         │
│       ▼              ▼              ▼              ▼                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐                 │
│  │   PS5    │◀──│   PS6    │◀──│   PS7    │◀──│   PS8    │                 │
│  │ Eval &   │   │ Safety   │   │ Multi-   │   │ Orchest. │                 │
│  │ Self-Imp │   │ Align.   │   │ Modal    │   │ Tool Use │                 │
│  └────┬─────┘   └──────────┘   └──────────┘   └──────────┘                 │
│       │                                                                      │
│       ▼                                                                      │
│  ┌──────────────────────────────────────────────────────┐                   │
│  │              EMERGENT: Cognitive Architecture         │                   │
│  │   PS1 → PS2 → PS3 → PS4 → PS5 → PS6 → PS7 → PS8   │                   │
│  │              ▲                              │         │                   │
│  │              └──────── SELF-IMPROVE ────────┘         │                   │
│  └──────────────────────────────────────────────────────┘                   │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │  COGNITIVE LOOP:                                                      │  │
│  │  Intent → PS1:Design → PS2:Compress → PS3:Retrieve → PS4:Remember    │  │
│  │       → PS5:Evaluate → PS6:Guard → PS7:Perceive → PS8:Orchestrate    │  │
│  │       → PS5:Re-evaluate → PS2:Re-compress → PS1:Re-design (repeat)   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Module PS1: Prompt Architecture Engine

**Purpose:** Design system prompts, chain-of-thought scaffolds, few-shot exemplars,
and meta-prompting frameworks. PS1 is the blueprint layer — every cognitive
architecture begins here.

**Design Pattern:** Builder Pattern + Strategy Pattern
- Builder: Incrementally assembles prompt components (role, context, constraints, format)
- Strategy: Selects prompting technique based on task complexity analysis

### Code Examples

#### System Prompt Builder

```python
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

class PromptStrategy(Enum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    TREE_OF_THOUGHT = "tree_of_thought"
    META_PROMPT = "meta_prompt"
    REACT = "react"

@dataclass
class PromptArchitecture:
    """PS1 core: builds structured prompt architectures."""
    role: str = ""
    context: str = ""
    constraints: list[str] = field(default_factory=list)
    output_format: str = ""
    exemplars: list[dict] = field(default_factory=list)
    chain_of_thought: bool = False
    strategy: PromptStrategy = PromptStrategy.ZERO_SHOT

    def build_system_prompt(self) -> str:
        sections = []
        if self.role:
            sections.append(f"# Role\n{self.role}")
        if self.context:
            sections.append(f"# Context\n{self.context}")
        if self.constraints:
            constraint_text = "\n".join(f"- {c}" for c in self.constraints)
            sections.append(f"# Constraints\n{constraint_text}")
        if self.exemplars:
            ex_text = "\n\n".join(
                f"**Input:** {e['input']}\n**Output:** {e['output']}"
                for e in self.exemplars
            )
            sections.append(f"# Examples\n{ex_text}")
        if self.chain_of_thought:
            sections.append(
                "# Reasoning\n"
                "Think step-by-step. Show your reasoning before the answer.\n"
                "Use <thinking>...</thinking> tags for internal reasoning."
            )
        if self.output_format:
            sections.append(f"# Output Format\n{self.output_format}")
        return "\n\n".join(sections)

    def select_strategy(self, task_complexity: float) -> PromptStrategy:
        """Auto-select prompting strategy based on task complexity (0-1)."""
        if task_complexity < 0.2:
            return PromptStrategy.ZERO_SHOT
        elif task_complexity < 0.4:
            return PromptStrategy.FEW_SHOT
        elif task_complexity < 0.6:
            return PromptStrategy.CHAIN_OF_THOUGHT
        elif task_complexity < 0.8:
            return PromptStrategy.TREE_OF_THOUGHT
        else:
            return PromptStrategy.META_PROMPT
```

#### Chain-of-Thought Template

```python
COT_TEMPLATE = """
You are an expert {domain} analyst.

## Task
{task_description}

## Approach
Think through this step-by-step:

1. **Identify** the core problem or question
2. **Decompose** into sub-problems
3. **Analyze** each sub-problem with evidence
4. **Synthesize** findings into a coherent answer
5. **Verify** the answer against the original question

## Constraints
{constraints}

## Output
Provide your step-by-step reasoning, then your final answer in this format:

<thinking>
[Your detailed reasoning here]
</thinking>

<answer>
[Your final answer here]
</answer>
"""

def build_cot_prompt(domain: str, task: str, constraints: list[str]) -> str:
    return COT_TEMPLATE.format(
        domain=domain,
        task_description=task,
        constraints="\n".join(f"- {c}" for c in constraints),
    )
```

#### Meta-Prompt Generator

```python
META_PROMPT_TEMPLATE = """
You are a prompt engineer. Your task is to write the BEST possible
prompt for the following objective:

## Objective
{objective}

## Target Model
{model_name} ({model_context_window} tokens)

## Requirements
- The prompt must be self-contained
- Include role, context, constraints, output format
- Optimize for {optimization_target}
- Token budget: {token_budget} tokens

## Output
Return ONLY the prompt text, ready to use. No commentary.
"""

class MetaPromptEngine:
    """PS1 meta-prompting: prompts that generate prompts."""

    def __init__(self, model_name: str = "gpt-4", context_window: int = 128000):
        self.model_name = model_name
        self.context_window = context_window

    def generate_prompt_request(
        self,
        objective: str,
        optimization_target: str = "accuracy",
        token_budget: int = 2000,
    ) -> str:
        return META_PROMPT_TEMPLATE.format(
            objective=objective,
            model_name=self.model_name,
            model_context_window=self.context_window,
            optimization_target=optimization_target,
            token_budget=token_budget,
        )

    def iterative_refine(self, prompt: str, feedback: str) -> str:
        """Feed evaluation back into meta-prompting (PS1↔PS5 loop)."""
        return (
            f"Improve the following prompt based on this feedback:\n\n"
            f"## Current Prompt\n{prompt}\n\n"
            f"## Feedback\n{feedback}\n\n"
            f"## Instructions\n"
            f"Return the improved prompt only. Preserve what works, fix what doesn't."
        )
```

**Integration Points:**
- **PS1 → PS2:** Raw prompts feed into token optimizer for compression
- **PS1 → PS5:** Prompt designs feed into eval loop; eval scores feed back to PS1
- **PS1 → PS8:** System prompts are injected into orchestration chains

---

## 📐 Module PS2: Token Efficiency Optimizer

**Purpose:** Compress prompts without semantic loss, manage context windows,
deduplicate content, and maximize information density per token.

**Design Pattern:** Pipeline Pattern + Decorator Pattern
- Pipeline: Sequential compression stages (dedup → compress → validate)
- Decorator: Wraps prompts with context-window-aware truncation

### Code Examples

#### Token Compression Pipeline

```python
import re
import hashlib
from typing import Callable

class TokenOptimizer:
    """PS2 core: multi-stage prompt compression pipeline."""

    def __init__(self, max_tokens: int = 4096):
        self.max_tokens = max_tokens
        self.stages: list[Callable[[str], str]] = [
            self.remove_redundant_whitespace,
            self.deduplicate_instructions,
            self.compress_enumerations,
            self.abbreviate_common_patterns,
        ]

    def optimize(self, prompt: str) -> str:
        result = prompt
        for stage in self.stages:
            result = stage(result)
        return self.enforce_token_budget(result)

    @staticmethod
    def remove_redundant_whitespace(text: str) -> str:
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    @staticmethod
    def deduplicate_instructions(text: str) -> str:
        lines = text.split('\n')
        seen_hashes: set[str] = set()
        unique_lines = []
        for line in lines:
            h = hashlib.md5(line.strip().lower().encode()).hexdigest()
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique_lines.append(line)
        return '\n'.join(unique_lines)

    @staticmethod
    def compress_enumerations(text: str) -> str:
        """Convert verbose lists to compact form."""
        text = re.sub(
            r'(?:You must |Please |Make sure to )(not |always )?',
            lambda m: ('NEVER ' if m.group(1) == 'not ' else
                       'ALWAYS ' if m.group(1) == 'always ' else ''),
            text
        )
        return text

    @staticmethod
    def abbreviate_common_patterns(text: str) -> str:
        abbreviations = {
            "for example": "e.g.",
            "in other words": "i.e.",
            "as a result": "→",
            "on the other hand": "conversely",
            "in order to": "to",
            "due to the fact that": "because",
            "at this point in time": "now",
        }
        for phrase, abbr in abbreviations.items():
            text = re.sub(re.escape(phrase), abbr, text, flags=re.IGNORECASE)
        return text

    def enforce_token_budget(self, text: str) -> str:
        """Rough token estimation: 1 token ≈ 4 chars for English."""
        estimated_tokens = len(text) // 4
        if estimated_tokens <= self.max_tokens:
            return text
        # Truncate from middle, preserving start (role/instructions) and end (format)
        char_budget = self.max_tokens * 4
        head_size = int(char_budget * 0.6)
        tail_size = int(char_budget * 0.3)
        return (
            text[:head_size]
            + "\n\n[... compressed — see full context via RAG ...]\n\n"
            + text[-tail_size:]
        )
```

#### Context Window Manager

```python
@dataclass
class ContextWindow:
    """Manages allocation within a model's context window."""
    total_tokens: int
    system_reserve: int = 500      # system prompt minimum
    output_reserve: int = 2000     # generation headroom
    rag_allocation: float = 0.4    # 40% for retrieved context
    memory_allocation: float = 0.15 # 15% for agent memory

    @property
    def available(self) -> int:
        return self.total_tokens - self.system_reserve - self.output_reserve

    @property
    def rag_budget(self) -> int:
        return int(self.available * self.rag_allocation)

    @property
    def memory_budget(self) -> int:
        return int(self.available * self.memory_allocation)

    @property
    def prompt_budget(self) -> int:
        return self.available - self.rag_budget - self.memory_budget

    def allocate(self) -> dict[str, int]:
        return {
            "system_prompt": self.system_reserve,
            "user_prompt": self.prompt_budget,
            "rag_context": self.rag_budget,
            "agent_memory": self.memory_budget,
            "output_generation": self.output_reserve,
            "total": self.total_tokens,
        }
```

**Integration Points:**
- **PS2 ← PS1:** Receives raw prompts, returns compressed versions
- **PS2 → PS3:** Token budget determines how much RAG context can be injected
- **PS2 ← PS5:** Eval feedback triggers re-compression with different strategies

---

## 📐 Module PS3: RAG Pipeline Synthesis

**Purpose:** Design and implement retrieval-augmented generation pipelines —
chunking strategies, embedding selection, hybrid search (keyword + vector),
reranking, and context assembly.

**Design Pattern:** Template Method + Strategy Pattern
- Template Method: Standard RAG pipeline with overridable stages
- Strategy: Swappable chunking, embedding, and reranking strategies

### Code Examples

#### RAG Pipeline Framework

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class Chunk:
    text: str
    metadata: dict[str, Any]
    embedding: list[float] | None = None
    score: float = 0.0

class ChunkingStrategy(ABC):
    @abstractmethod
    def chunk(self, document: str, metadata: dict) -> list[Chunk]:
        ...

class RecursiveCharacterChunker(ChunkingStrategy):
    def __init__(self, chunk_size: int = 512, overlap: int = 64):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, document: str, metadata: dict) -> list[Chunk]:
        chunks = []
        separators = ["\n\n", "\n", ". ", " "]
        self._split_recursive(document, separators, metadata, chunks)
        return chunks

    def _split_recursive(
        self, text: str, separators: list[str],
        metadata: dict, result: list[Chunk]
    ):
        if len(text) <= self.chunk_size:
            if text.strip():
                result.append(Chunk(text=text.strip(), metadata=metadata.copy()))
            return

        sep = separators[0] if separators else " "
        parts = text.split(sep)
        current = ""

        for part in parts:
            candidate = current + sep + part if current else part
            if len(candidate) > self.chunk_size and current:
                result.append(Chunk(text=current.strip(), metadata=metadata.copy()))
                # Overlap: keep tail of current chunk
                overlap_text = current[-self.overlap:] if self.overlap else ""
                current = overlap_text + sep + part
            else:
                current = candidate

        if current.strip():
            if len(current) > self.chunk_size and len(separators) > 1:
                self._split_recursive(current, separators[1:], metadata, result)
            else:
                result.append(Chunk(text=current.strip(), metadata=metadata.copy()))

class SemanticChunker(ChunkingStrategy):
    """Chunks by semantic similarity boundaries (requires embedder)."""
    def __init__(self, embed_fn, threshold: float = 0.3):
        self.embed_fn = embed_fn
        self.threshold = threshold

    def chunk(self, document: str, metadata: dict) -> list[Chunk]:
        sentences = [s.strip() for s in document.split('. ') if s.strip()]
        embeddings = [self.embed_fn(s) for s in sentences]
        chunks, current_group = [], [sentences[0]]

        for i in range(1, len(sentences)):
            sim = self._cosine_sim(embeddings[i - 1], embeddings[i])
            if sim < self.threshold:
                chunks.append(Chunk(
                    text='. '.join(current_group) + '.',
                    metadata=metadata.copy()
                ))
                current_group = []
            current_group.append(sentences[i])

        if current_group:
            chunks.append(Chunk(text='. '.join(current_group) + '.', metadata=metadata.copy()))
        return chunks

    @staticmethod
    def _cosine_sim(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x ** 2 for x in a) ** 0.5
        norm_b = sum(x ** 2 for x in b) ** 0.5
        return dot / (norm_a * norm_b + 1e-8)


class RAGPipeline:
    """PS3 core: configurable retrieval-augmented generation pipeline."""

    def __init__(
        self,
        chunker: ChunkingStrategy,
        embed_fn,
        vector_store,
        reranker=None,
        top_k: int = 5,
        hybrid_alpha: float = 0.7,
    ):
        self.chunker = chunker
        self.embed_fn = embed_fn
        self.vector_store = vector_store
        self.reranker = reranker
        self.top_k = top_k
        self.hybrid_alpha = hybrid_alpha

    def ingest(self, document: str, metadata: dict) -> int:
        chunks = self.chunker.chunk(document, metadata)
        for chunk in chunks:
            chunk.embedding = self.embed_fn(chunk.text)
        self.vector_store.upsert(chunks)
        return len(chunks)

    def retrieve(self, query: str) -> list[Chunk]:
        query_embedding = self.embed_fn(query)

        # Vector search
        vector_results = self.vector_store.search(query_embedding, top_k=self.top_k * 2)
        # Keyword search (BM25 fallback)
        keyword_results = self.vector_store.keyword_search(query, top_k=self.top_k * 2)

        # Hybrid fusion via Reciprocal Rank Fusion
        fused = self._reciprocal_rank_fusion(vector_results, keyword_results)

        # Rerank if reranker available
        if self.reranker:
            fused = self.reranker.rerank(query, fused)

        return fused[: self.top_k]

    def _reciprocal_rank_fusion(
        self, *result_lists: list[Chunk], k: int = 60
    ) -> list[Chunk]:
        scores: dict[str, float] = {}
        chunk_map: dict[str, Chunk] = {}
        for results in result_lists:
            for rank, chunk in enumerate(results):
                key = hashlib.md5(chunk.text.encode()).hexdigest()
                scores[key] = scores.get(key, 0) + 1.0 / (k + rank + 1)
                chunk_map[key] = chunk
        sorted_keys = sorted(scores, key=scores.get, reverse=True)
        return [chunk_map[k] for k in sorted_keys]

    def build_context(self, chunks: list[Chunk], token_budget: int) -> str:
        """Assemble retrieved chunks into context string within budget."""
        context_parts = []
        used_tokens = 0
        for i, chunk in enumerate(chunks):
            chunk_tokens = len(chunk.text) // 4
            if used_tokens + chunk_tokens > token_budget:
                break
            context_parts.append(
                f"[Source {i+1}: {chunk.metadata.get('source', 'unknown')}]\n"
                f"{chunk.text}"
            )
            used_tokens += chunk_tokens
        return "\n\n---\n\n".join(context_parts)
```

**Integration Points:**
- **PS3 ← PS2:** Token budget from context window manager constrains retrieval
- **PS3 → PS4:** Retrieved chunks can be stored in episodic memory for future recall
- **PS3 → PS1:** Retrieved context injected into prompt architecture
- **PS3 ← PS8:** Orchestration layer triggers retrieval at runtime

---

## 📐 Module PS4: Memory Architecture

**Purpose:** Design persistent memory systems for AI agents — episodic memory
(conversation history), semantic memory (learned facts), and working memory
(current task context).

**Design Pattern:** Repository Pattern + Observer Pattern
- Repository: Abstracted storage for each memory type
- Observer: Memory events trigger consolidation and pruning

### Code Examples

#### Three-Tier Memory System

```python
import time
import json
from dataclasses import dataclass, field
from collections import deque

@dataclass
class MemoryEntry:
    content: str
    memory_type: str          # "episodic", "semantic", "working"
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5   # 0-1 scale
    access_count: int = 0
    embedding: list[float] | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def recency_score(self) -> float:
        age_hours = (time.time() - self.timestamp) / 3600
        return max(0, 1.0 - (age_hours / 168))  # Decay over 1 week

    @property
    def composite_score(self) -> float:
        return (
            self.importance * 0.4
            + self.recency_score * 0.3
            + min(self.access_count / 10, 1.0) * 0.3
        )


class EpisodicMemory:
    """Stores conversation turns and interaction history."""

    def __init__(self, max_entries: int = 1000):
        self.entries: deque[MemoryEntry] = deque(maxlen=max_entries)

    def add(self, content: str, importance: float = 0.5, **meta):
        self.entries.append(MemoryEntry(
            content=content,
            memory_type="episodic",
            importance=importance,
            metadata=meta,
        ))

    def recall(self, n: int = 10) -> list[MemoryEntry]:
        return sorted(self.entries, key=lambda e: e.composite_score, reverse=True)[:n]

    def recent(self, n: int = 5) -> list[MemoryEntry]:
        return list(self.entries)[-n:]


class SemanticMemory:
    """Stores learned facts, entity relationships, and domain knowledge."""

    def __init__(self, embed_fn=None, vector_store=None):
        self.facts: dict[str, MemoryEntry] = {}
        self.embed_fn = embed_fn
        self.vector_store = vector_store

    def learn(self, key: str, content: str, importance: float = 0.7):
        entry = MemoryEntry(
            content=content,
            memory_type="semantic",
            importance=importance,
            metadata={"key": key},
        )
        if self.embed_fn:
            entry.embedding = self.embed_fn(content)
        self.facts[key] = entry
        if self.vector_store and entry.embedding:
            self.vector_store.upsert_one(key, entry.embedding, content)

    def query(self, question: str, top_k: int = 5) -> list[MemoryEntry]:
        if self.embed_fn and self.vector_store:
            q_emb = self.embed_fn(question)
            results = self.vector_store.search(q_emb, top_k=top_k)
            return [
                MemoryEntry(content=r.text, memory_type="semantic",
                            importance=r.score, metadata=r.metadata)
                for r in results
            ]
        # Fallback: keyword match
        matches = []
        for key, entry in self.facts.items():
            if any(w in entry.content.lower() for w in question.lower().split()):
                matches.append(entry)
        return sorted(matches, key=lambda e: e.importance, reverse=True)[:top_k]


class WorkingMemory:
    """Short-term scratchpad for current task context and intermediate results."""

    def __init__(self, capacity: int = 20):
        self.slots: dict[str, MemoryEntry] = {}
        self.capacity = capacity

    def store(self, key: str, content: str, importance: float = 0.8):
        if len(self.slots) >= self.capacity and key not in self.slots:
            # Evict lowest-scored entry
            worst = min(self.slots, key=lambda k: self.slots[k].composite_score)
            del self.slots[worst]
        self.slots[key] = MemoryEntry(
            content=content,
            memory_type="working",
            importance=importance,
            metadata={"key": key},
        )

    def get(self, key: str) -> str | None:
        entry = self.slots.get(key)
        if entry:
            entry.access_count += 1
            return entry.content
        return None

    def dump(self) -> str:
        """Serialize working memory for prompt injection."""
        items = sorted(self.slots.values(), key=lambda e: e.composite_score, reverse=True)
        return "\n".join(f"- [{e.metadata.get('key', '?')}]: {e.content}" for e in items)


class CognitiveMemory:
    """PS4 core: unified memory interface integrating all three tiers."""

    def __init__(self, embed_fn=None, vector_store=None):
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory(embed_fn, vector_store)
        self.working = WorkingMemory()

    def build_memory_context(self, query: str, token_budget: int) -> str:
        """Assemble memory context for prompt injection within budget."""
        sections = []

        # Working memory (highest priority)
        wm = self.working.dump()
        if wm:
            sections.append(f"## Current Context\n{wm}")

        # Semantic memory
        sem_results = self.semantic.query(query, top_k=5)
        if sem_results:
            sem_text = "\n".join(f"- {e.content}" for e in sem_results)
            sections.append(f"## Relevant Knowledge\n{sem_text}")

        # Episodic memory (recent + relevant)
        recent = self.episodic.recent(3)
        if recent:
            ep_text = "\n".join(f"- {e.content}" for e in recent)
            sections.append(f"## Recent History\n{ep_text}")

        full_context = "\n\n".join(sections)
        # Enforce budget
        char_budget = token_budget * 4
        if len(full_context) > char_budget:
            full_context = full_context[:char_budget] + "\n[memory truncated]"
        return full_context

    def consolidate(self):
        """Promote high-importance episodic memories to semantic store."""
        for entry in self.episodic.recall(20):
            if entry.importance > 0.8 and entry.access_count >= 3:
                key = f"consolidated_{int(entry.timestamp)}"
                self.semantic.learn(key, entry.content, entry.importance)
```

**Integration Points:**
- **PS4 ← PS3:** RAG results stored in episodic memory for future retrieval
- **PS4 → PS1:** Memory context injected into prompt architecture
- **PS4 ← PS5:** Eval results determine what to remember vs. forget
- **PS4 → PS8:** Orchestration reads/writes memory between agent steps

---

## 📐 Module PS5: Evaluation & Self-Improvement

**Purpose:** Auto-evaluate prompt/response quality using metrics (BLEU, ROUGE,
semantic similarity), run A/B tests, mutate prompts, and close the
self-improvement loop.

**Design Pattern:** Strategy Pattern + Observer Pattern + Genetic Algorithm
- Strategy: Pluggable evaluation metrics
- Observer: Eval results trigger prompt mutations
- Genetic: Population-based prompt evolution

### Code Examples

#### Evaluation Framework

```python
import re
import random
from dataclasses import dataclass
from collections import Counter

@dataclass
class EvalResult:
    metric: str
    score: float           # 0-1
    details: dict = None

    @property
    def passed(self) -> bool:
        thresholds = {
            "bleu": 0.3, "rouge_l": 0.4, "semantic_sim": 0.7,
            "format_compliance": 0.9, "safety": 0.95,
        }
        return self.score >= thresholds.get(self.metric, 0.5)


class EvaluationSuite:
    """PS5 core: multi-metric evaluation for prompt outputs."""

    @staticmethod
    def bleu_score(reference: str, candidate: str, n: int = 4) -> EvalResult:
        ref_tokens = reference.lower().split()
        cand_tokens = candidate.lower().split()
        scores = []
        for i in range(1, n + 1):
            ref_ngrams = Counter(
                tuple(ref_tokens[j:j+i]) for j in range(len(ref_tokens) - i + 1)
            )
            cand_ngrams = Counter(
                tuple(cand_tokens[j:j+i]) for j in range(len(cand_tokens) - i + 1)
            )
            overlap = sum((cand_ngrams & ref_ngrams).values())
            total = max(sum(cand_ngrams.values()), 1)
            scores.append(overlap / total)

        bleu = (scores[0] * scores[1] * scores[2] * scores[3]) ** 0.25 if all(scores) else 0
        return EvalResult(metric="bleu", score=bleu, details={"ngram_scores": scores})

    @staticmethod
    def rouge_l(reference: str, candidate: str) -> EvalResult:
        """ROUGE-L using longest common subsequence."""
        ref_tokens = reference.lower().split()
        cand_tokens = candidate.lower().split()
        m, n = len(ref_tokens), len(cand_tokens)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref_tokens[i-1] == cand_tokens[j-1]:
                    dp[i][j] = dp[i-1][j-1] + 1
                else:
                    dp[i][j] = max(dp[i-1][j], dp[i][j-1])
        lcs = dp[m][n]
        precision = lcs / max(n, 1)
        recall = lcs / max(m, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-8)
        return EvalResult(metric="rouge_l", score=f1,
                          details={"precision": precision, "recall": recall})

    @staticmethod
    def format_compliance(output: str, required_sections: list[str]) -> EvalResult:
        found = sum(1 for s in required_sections if s.lower() in output.lower())
        score = found / max(len(required_sections), 1)
        missing = [s for s in required_sections if s.lower() not in output.lower()]
        return EvalResult(metric="format_compliance", score=score,
                          details={"missing": missing})

    def evaluate_all(self, reference: str, candidate: str,
                     required_sections: list[str] = None) -> list[EvalResult]:
        results = [
            self.bleu_score(reference, candidate),
            self.rouge_l(reference, candidate),
        ]
        if required_sections:
            results.append(self.format_compliance(candidate, required_sections))
        return results
```

#### Self-Improving Prompt Loop

```python
class PromptEvolver:
    """PS5 genetic prompt evolution: mutate, evaluate, select, repeat."""

    def __init__(self, evaluator: EvaluationSuite, population_size: int = 5):
        self.evaluator = evaluator
        self.population_size = population_size

    def mutate(self, prompt: str) -> str:
        """Apply random mutation to a prompt."""
        mutations = [
            self._rephrase_instruction,
            self._add_constraint,
            self._reorder_sections,
            self._strengthen_directive,
        ]
        mutation_fn = random.choice(mutations)
        return mutation_fn(prompt)

    @staticmethod
    def _rephrase_instruction(prompt: str) -> str:
        swaps = [
            ("You are", "Act as"), ("must", "shall"),
            ("Provide", "Return"), ("detailed", "comprehensive"),
            ("step-by-step", "systematically"),
        ]
        for old, new in swaps:
            if old in prompt:
                return prompt.replace(old, new, 1)
        return prompt

    @staticmethod
    def _add_constraint(prompt: str) -> str:
        constraints = [
            "\n- Be concise: prefer clarity over verbosity.",
            "\n- Cite evidence for every claim.",
            "\n- Structure output with clear headers.",
            "\n- If uncertain, state your confidence level.",
        ]
        return prompt + random.choice(constraints)

    @staticmethod
    def _reorder_sections(prompt: str) -> str:
        sections = prompt.split("\n\n")
        if len(sections) > 2:
            mid = sections[1:-1]
            random.shuffle(mid)
            return "\n\n".join([sections[0]] + mid + [sections[-1]])
        return prompt

    @staticmethod
    def _strengthen_directive(prompt: str) -> str:
        return prompt.replace(
            "Please ", "").replace("Could you ", "").replace("I'd like you to ", "")

    def evolve(
        self,
        base_prompt: str,
        reference_output: str,
        llm_fn,
        generations: int = 3,
    ) -> tuple[str, float]:
        """Run evolutionary loop: mutate → generate → evaluate → select."""
        population = [base_prompt] + [self.mutate(base_prompt)
                                       for _ in range(self.population_size - 1)]
        best_prompt, best_score = base_prompt, 0.0

        for gen in range(generations):
            scored = []
            for prompt in population:
                output = llm_fn(prompt)
                results = self.evaluator.evaluate_all(reference_output, output)
                avg_score = sum(r.score for r in results) / len(results)
                scored.append((prompt, avg_score))

            scored.sort(key=lambda x: x[1], reverse=True)
            if scored[0][1] > best_score:
                best_prompt, best_score = scored[0]

            # Selection: keep top half, mutate to refill
            survivors = [p for p, _ in scored[: self.population_size // 2 + 1]]
            population = survivors + [self.mutate(random.choice(survivors))
                                       for _ in range(self.population_size - len(survivors))]

        return best_prompt, best_score
```

**Integration Points:**
- **PS5 ← PS1:** Evaluates prompts designed by PS1
- **PS5 → PS1:** Feedback drives meta-prompt refinement (self-improvement loop)
- **PS5 ← PS6:** Safety scores are an eval dimension
- **PS5 → PS4:** Eval results stored in memory for learning

---

## 📐 Module PS6: Safety & Alignment Layer

**Purpose:** Enforce guardrails, implement Constitutional AI principles,
red-team prompts, filter toxic/harmful outputs, and ensure alignment.

**Design Pattern:** Chain of Responsibility + Decorator Pattern
- Chain of Responsibility: Sequential safety filters, any can reject
- Decorator: Wraps LLM calls with pre/post safety checks

### Code Examples

#### Safety Pipeline

```python
from enum import Enum
from dataclasses import dataclass

class SafetyVerdict(Enum):
    PASS = "pass"
    WARN = "warn"
    BLOCK = "block"

@dataclass
class SafetyCheck:
    name: str
    verdict: SafetyVerdict
    reason: str
    score: float  # 0 = unsafe, 1 = safe

class SafetyFilter:
    """Base class for safety filters in the chain."""
    def check(self, text: str) -> SafetyCheck:
        raise NotImplementedError

class ToxicityFilter(SafetyFilter):
    """Keyword + pattern-based toxicity detection."""
    PATTERNS = [
        r'\b(hack|exploit|bypass)\b.*\b(security|auth|password)\b',
        r'\b(create|make|build)\b.*\b(weapon|bomb|virus)\b',
        r'\b(steal|extract)\b.*\b(data|credentials|keys)\b',
    ]

    def check(self, text: str) -> SafetyCheck:
        import re
        for pattern in self.PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return SafetyCheck(
                    name="toxicity", verdict=SafetyVerdict.BLOCK,
                    reason=f"Matched harmful pattern: {pattern[:40]}...",
                    score=0.0,
                )
        return SafetyCheck(name="toxicity", verdict=SafetyVerdict.PASS,
                           reason="No harmful patterns detected", score=1.0)

class PIIFilter(SafetyFilter):
    """Detect and redact personally identifiable information."""
    PII_PATTERNS = {
        "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
        "email": r'\b[\w.-]+@[\w.-]+\.\w+\b',
        "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    }

    def check(self, text: str) -> SafetyCheck:
        import re
        found = []
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, text):
                found.append(pii_type)
        if found:
            return SafetyCheck(
                name="pii", verdict=SafetyVerdict.WARN,
                reason=f"PII detected: {', '.join(found)}", score=0.3,
            )
        return SafetyCheck(name="pii", verdict=SafetyVerdict.PASS,
                           reason="No PII detected", score=1.0)

class ConstitutionalAIFilter(SafetyFilter):
    """Apply Constitutional AI principles as a post-generation check."""
    PRINCIPLES = [
        "The response should not encourage illegal activity.",
        "The response should not generate misinformation.",
        "The response should respect user privacy.",
        "The response should not exhibit bias based on protected characteristics.",
        "The response should be helpful while avoiding harm.",
    ]

    def __init__(self, llm_fn=None):
        self.llm_fn = llm_fn

    def check(self, text: str) -> SafetyCheck:
        if not self.llm_fn:
            return SafetyCheck(name="constitutional", verdict=SafetyVerdict.PASS,
                               reason="No LLM available for constitutional check", score=0.8)
        critique_prompt = (
            "Evaluate this text against these principles:\n"
            + "\n".join(f"- {p}" for p in self.PRINCIPLES)
            + f"\n\nText: {text[:1000]}\n\n"
            "Score 0-1 for each principle. Return JSON: "
            "{\"scores\": [...], \"overall\": float, \"issues\": [str]}"
        )
        result = self.llm_fn(critique_prompt)
        # Parse result (simplified)
        overall = 0.85  # placeholder for parsed score
        return SafetyCheck(name="constitutional", verdict=SafetyVerdict.PASS,
                           reason="Constitutional check passed", score=overall)


class SafetyPipeline:
    """PS6 core: chain-of-responsibility safety pipeline."""

    def __init__(self):
        self.filters: list[SafetyFilter] = [
            ToxicityFilter(),
            PIIFilter(),
            ConstitutionalAIFilter(),
        ]

    def evaluate(self, text: str) -> tuple[SafetyVerdict, list[SafetyCheck]]:
        checks = [f.check(text) for f in self.filters]
        if any(c.verdict == SafetyVerdict.BLOCK for c in checks):
            return SafetyVerdict.BLOCK, checks
        if any(c.verdict == SafetyVerdict.WARN for c in checks):
            return SafetyVerdict.WARN, checks
        return SafetyVerdict.PASS, checks

    def wrap_llm_call(self, llm_fn):
        """Decorator: wrap any LLM call with pre/post safety checks."""
        def safe_llm(prompt: str) -> str:
            # Pre-check input
            input_verdict, _ = self.evaluate(prompt)
            if input_verdict == SafetyVerdict.BLOCK:
                return "[BLOCKED] Input violates safety policy."

            output = llm_fn(prompt)

            # Post-check output
            output_verdict, checks = self.evaluate(output)
            if output_verdict == SafetyVerdict.BLOCK:
                return "[BLOCKED] Output violates safety policy."
            if output_verdict == SafetyVerdict.WARN:
                warnings = [c.reason for c in checks if c.verdict == SafetyVerdict.WARN]
                output += f"\n\n⚠️ Safety warnings: {'; '.join(warnings)}"

            return output
        return safe_llm
```

**Integration Points:**
- **PS6 ← PS1:** Validates system prompts for embedded injection risks
- **PS6 → PS5:** Safety scores feed into overall eval metrics
- **PS6 ← PS8:** Wraps orchestration LLM calls with safety guardrails
- **PS6 → PS7:** Validates multi-modal inputs for harmful content

---

## 📐 Module PS7: Multi-Modal Integration

**Purpose:** Design prompt patterns for vision, audio, document understanding,
and tool-use across multi-modal LLMs. Handle image+text, audio transcription,
structured document extraction, and interleaved modalities.

**Design Pattern:** Adapter Pattern + Composite Pattern
- Adapter: Normalize different modality inputs into unified prompt format
- Composite: Combine modality-specific prompts into coherent multi-modal requests

### Code Examples

#### Multi-Modal Prompt Builder

```python
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

@dataclass
class ModalityInput:
    modality: Literal["text", "image", "audio", "document"]
    content: str | bytes
    metadata: dict = None

    def to_message_part(self) -> dict:
        if self.modality == "text":
            return {"type": "text", "text": self.content}
        elif self.modality == "image":
            if isinstance(self.content, bytes):
                b64 = base64.b64encode(self.content).decode()
                return {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                }
            return {"type": "image_url", "image_url": {"url": self.content}}
        elif self.modality == "audio":
            b64 = base64.b64encode(self.content).decode()
            return {"type": "input_audio", "input_audio": {"data": b64, "format": "wav"}}
        elif self.modality == "document":
            return {"type": "text", "text": f"[Document Content]\n{self.content}"}
        raise ValueError(f"Unknown modality: {self.modality}")


class MultiModalPromptBuilder:
    """PS7 core: assemble multi-modal prompts for vision/audio/doc LLMs."""

    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt
        self.inputs: list[ModalityInput] = []

    def add_text(self, text: str) -> "MultiModalPromptBuilder":
        self.inputs.append(ModalityInput(modality="text", content=text))
        return self

    def add_image(self, image_path_or_url: str) -> "MultiModalPromptBuilder":
        if image_path_or_url.startswith(("http://", "https://")):
            content = image_path_or_url
        else:
            content = Path(image_path_or_url).read_bytes()
        self.inputs.append(ModalityInput(modality="image", content=content))
        return self

    def add_document(self, text: str, doc_type: str = "pdf") -> "MultiModalPromptBuilder":
        self.inputs.append(ModalityInput(
            modality="document", content=text,
            metadata={"doc_type": doc_type},
        ))
        return self

    def build(self) -> list[dict]:
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        user_content = [inp.to_message_part() for inp in self.inputs]
        messages.append({"role": "user", "content": user_content})
        return messages


# --- Multi-modal prompt templates ---

VISION_ANALYSIS_PROMPT = """Analyze this image in detail:
1. Describe what you see (objects, people, text, layout)
2. Extract any text visible in the image (OCR)
3. Identify the context/purpose of the image
4. Note any relevant details for {domain}

Output format:
## Description
[detailed description]

## Extracted Text
[any text found in the image]

## Analysis
[contextual analysis for {domain}]
"""

DOCUMENT_EXTRACTION_PROMPT = """Extract structured data from this document.

Target schema:
{schema}

Rules:
- Extract ONLY information present in the document
- Use null for missing fields
- Preserve exact values (dates, numbers, names)
- Flag any ambiguous extractions

Return valid JSON matching the target schema.
"""

def build_vision_prompt(image_path: str, domain: str) -> list[dict]:
    builder = MultiModalPromptBuilder(
        system_prompt="You are an expert visual analyst."
    )
    builder.add_text(VISION_ANALYSIS_PROMPT.format(domain=domain))
    builder.add_image(image_path)
    return builder.build()

def build_document_extraction(doc_text: str, schema: dict) -> list[dict]:
    import json
    builder = MultiModalPromptBuilder(
        system_prompt="You are a precision document extraction engine."
    )
    prompt = DOCUMENT_EXTRACTION_PROMPT.format(schema=json.dumps(schema, indent=2))
    builder.add_text(prompt)
    builder.add_document(doc_text)
    return builder.build()
```

**Integration Points:**
- **PS7 → PS3:** Extracted document content feeds into RAG pipeline for indexing
- **PS7 ← PS1:** System prompts from PS1 configure multi-modal behavior
- **PS7 → PS6:** All multi-modal inputs validated by safety pipeline
- **PS7 ← PS8:** Orchestration triggers multi-modal processing steps

---

## 📐 Module PS8: Orchestration & Tool Use

**Purpose:** Design agent loops, function calling, streaming pipelines,
parallel chains, and multi-step LLM orchestration. This is the execution
layer that wires all other modules into a running cognitive architecture.

**Design Pattern:** Mediator Pattern + State Machine
- Mediator: PS8 coordinates all other modules without them knowing each other
- State Machine: Agent loop transitions between states (think → act → observe)

### Code Examples

#### Agent Orchestration Loop

```python
import json
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum

class AgentState(Enum):
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"
    REFLECT = "reflect"
    DONE = "done"

@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict
    handler: Callable[..., str]

@dataclass
class AgentStep:
    state: AgentState
    thought: str = ""
    action: str = ""
    action_input: dict = field(default_factory=dict)
    observation: str = ""
    reflection: str = ""

class CognitiveAgent:
    """PS8 core: full cognitive agent loop integrating all PS modules."""

    def __init__(
        self,
        prompt_architect,       # PS1: PromptArchitecture
        token_optimizer,        # PS2: TokenOptimizer
        rag_pipeline,           # PS3: RAGPipeline
        memory,                 # PS4: CognitiveMemory
        evaluator,              # PS5: EvaluationSuite
        safety_pipeline,        # PS6: SafetyPipeline
        multimodal_builder,     # PS7: MultiModalPromptBuilder
        llm_fn: Callable,
        tools: list[ToolDefinition] = None,
        max_steps: int = 10,
    ):
        self.ps1 = prompt_architect
        self.ps2 = token_optimizer
        self.ps3 = rag_pipeline
        self.ps4 = memory
        self.ps5 = evaluator
        self.ps6 = safety_pipeline
        self.ps7 = multimodal_builder
        self.llm_fn = safety_pipeline.wrap_llm_call(llm_fn)  # PS6 wraps LLM
        self.tools = {t.name: t for t in (tools or [])}
        self.max_steps = max_steps
        self.steps: list[AgentStep] = []

    def run(self, user_input: str) -> str:
        # --- BUILD PROMPT (PS1 + PS2 + PS3 + PS4) ---
        context_window = ContextWindow(total_tokens=128000)
        allocation = context_window.allocate()

        # PS3: Retrieve relevant context
        rag_chunks = self.ps3.retrieve(user_input)
        rag_context = self.ps3.build_context(rag_chunks, allocation["rag_context"])

        # PS4: Recall from memory
        memory_context = self.ps4.build_memory_context(
            user_input, allocation["agent_memory"]
        )

        # PS1: Build system prompt
        self.ps1.context = f"{rag_context}\n\n{memory_context}"
        self.ps1.chain_of_thought = True
        system_prompt = self.ps1.build_system_prompt()

        # PS2: Optimize token usage
        system_prompt = self.ps2.optimize(system_prompt)

        # --- AGENT LOOP (ReAct: Think → Act → Observe) ---
        tool_descriptions = self._format_tools()
        state = AgentState.THINK
        final_answer = ""

        for step_num in range(self.max_steps):
            step = AgentStep(state=state)

            if state == AgentState.THINK:
                think_prompt = self._build_think_prompt(
                    system_prompt, user_input, tool_descriptions
                )
                response = self.llm_fn(think_prompt)
                step.thought = response

                if self._has_tool_call(response):
                    state = AgentState.ACT
                    step.action, step.action_input = self._parse_tool_call(response)
                elif self._has_final_answer(response):
                    final_answer = self._extract_answer(response)
                    state = AgentState.DONE
                else:
                    state = AgentState.REFLECT

            elif state == AgentState.ACT:
                tool_name = step.action
                if tool_name in self.tools:
                    tool = self.tools[tool_name]
                    observation = tool.handler(**step.action_input)
                    step.observation = observation
                    # PS4: Store observation in working memory
                    self.ps4.working.store(
                        f"tool_{step_num}", f"{tool_name}: {observation[:200]}"
                    )
                else:
                    step.observation = f"Error: Unknown tool '{tool_name}'"
                state = AgentState.OBSERVE

            elif state == AgentState.OBSERVE:
                state = AgentState.THINK  # Loop back to think with new observation

            elif state == AgentState.REFLECT:
                # PS5: Evaluate progress
                if self.steps:
                    last_thought = self.steps[-1].thought
                    eval_results = self.ps5.evaluate_all(user_input, last_thought)
                    avg_score = sum(r.score for r in eval_results) / max(len(eval_results), 1)
                    step.reflection = f"Progress score: {avg_score:.2f}"
                    if avg_score > 0.8:
                        final_answer = last_thought
                        state = AgentState.DONE
                    else:
                        state = AgentState.THINK
                else:
                    state = AgentState.THINK

            self.steps.append(step)

            if state == AgentState.DONE:
                break

        # --- POST-PROCESS ---
        # PS4: Store interaction in episodic memory
        self.ps4.episodic.add(f"Q: {user_input}\nA: {final_answer[:200]}", importance=0.7)
        self.ps4.consolidate()

        return final_answer

    def _format_tools(self) -> str:
        if not self.tools:
            return "No tools available."
        lines = []
        for t in self.tools.values():
            params = json.dumps(t.parameters, indent=2)
            lines.append(f"### {t.name}\n{t.description}\nParameters:\n```json\n{params}\n```")
        return "\n\n".join(lines)

    def _build_think_prompt(self, system: str, query: str, tools: str) -> str:
        history = ""
        for s in self.steps[-5:]:
            if s.thought:
                history += f"\nThought: {s.thought[:300]}"
            if s.observation:
                history += f"\nObservation: {s.observation[:300]}"
            if s.reflection:
                history += f"\nReflection: {s.reflection}"

        return (
            f"{system}\n\n"
            f"## Available Tools\n{tools}\n\n"
            f"## Conversation History\n{history}\n\n"
            f"## User Query\n{query}\n\n"
            f"## Instructions\n"
            f"Think step-by-step. If you need information, call a tool:\n"
            f"```tool\n{{\"name\": \"tool_name\", \"input\": {{...}}}}\n```\n"
            f"If you have the final answer:\n"
            f"```answer\n[your answer]\n```"
        )

    @staticmethod
    def _has_tool_call(response: str) -> bool:
        return "```tool" in response

    @staticmethod
    def _has_final_answer(response: str) -> bool:
        return "```answer" in response

    @staticmethod
    def _parse_tool_call(response: str) -> tuple[str, dict]:
        import re
        match = re.search(r'```tool\s*\n(.+?)\n```', response, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            return data.get("name", ""), data.get("input", {})
        return "", {}

    @staticmethod
    def _extract_answer(response: str) -> str:
        import re
        match = re.search(r'```answer\s*\n(.+?)\n```', response, re.DOTALL)
        return match.group(1).strip() if match else response
```

#### Parallel Chain Executor

```python
import asyncio
from typing import Callable, Awaitable

class ParallelChainExecutor:
    """Execute multiple LLM chains in parallel and merge results."""

    def __init__(self, llm_fn: Callable[[str], Awaitable[str]]):
        self.llm_fn = llm_fn

    async def execute_parallel(
        self, prompts: list[str], merge_strategy: str = "concatenate"
    ) -> str:
        tasks = [self.llm_fn(p) for p in prompts]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid = [r for r in results if isinstance(r, str)]
        errors = [str(r) for r in results if isinstance(r, Exception)]

        if merge_strategy == "concatenate":
            return "\n\n---\n\n".join(valid)
        elif merge_strategy == "vote":
            # Majority vote (for classification tasks)
            from collections import Counter
            votes = Counter(r.strip() for r in valid)
            return votes.most_common(1)[0][0] if votes else ""
        elif merge_strategy == "synthesize":
            synthesis_prompt = (
                "Synthesize these parallel results into one coherent answer:\n\n"
                + "\n\n---\n\n".join(valid)
            )
            return await self.llm_fn(synthesis_prompt)

        return "\n".join(valid)
```

**Integration Points:**
- **PS8 ↔ ALL:** PS8 is the mediator that orchestrates PS1-PS7
- **PS8 → PS3:** Triggers RAG retrieval during agent execution
- **PS8 → PS4:** Reads/writes memory between agent steps
- **PS8 → PS6:** All LLM calls wrapped with safety pipeline
- **PS8 → PS5:** Evaluates agent progress for self-improvement decisions

---

## 🌳 Decision Tree: Module Routing

```
                         USER INTENT
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
              "Design a            "Improve
               prompt"             existing"
                 │                    │
          ┌──────┴──────┐      ┌─────┴─────┐
          ▼             ▼      ▼           ▼
     Simple task    Complex   Low score   Safety
          │          task       │         concern
          ▼            │       ▼           │
        PS1           ▼     PS5→PS1       ▼
     (zero-shot)    PS1→PS2   (eval      PS6
                   (CoT+opt)  loop)    (guardrails)
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
          Needs     Needs     Needs
          context   memory    tools
              │        │        │
              ▼        ▼        ▼
            PS3      PS4      PS8
           (RAG)   (memory) (orchestrate)
              │        │        │
              └────────┴────────┘
                       │
                       ▼
                 Multi-modal?
                 ┌────┴────┐
                YES       NO
                 │         │
                 ▼         ▼
               PS7      Assemble
             (vision/    prompt
              audio)      │
                 │        ▼
                 └───▶ PS6→PS5
                     (safety→eval)
                          │
                          ▼
                    Score > 0.8?
                    ┌────┴────┐
                   YES       NO
                    │         │
                    ▼         ▼
                 OUTPUT    PS5→PS2→PS1
                          (self-improve
                           loop, max 3
                           iterations)
```

---

## 🔗 Cross-Module Integration Patterns

### Pattern 1: Full Cognitive Pipeline
**Flow:** Intent → PS1 → PS2 → PS3 → PS4 → PS8 → PS6 → PS5 → (loop)

```python
def cognitive_pipeline(user_intent: str, config: dict) -> str:
    """End-to-end cognitive architecture from a single intent."""
    # PS1: Design the prompt architecture
    architect = PromptArchitecture(
        role=config.get("role", "AI assistant"),
        chain_of_thought=True,
    )
    strategy = architect.select_strategy(config.get("complexity", 0.5))
    architect.strategy = strategy

    # PS2: Optimize for context window
    optimizer = TokenOptimizer(max_tokens=config.get("token_budget", 4096))
    window = ContextWindow(total_tokens=config.get("context_window", 128000))

    # PS3: Set up RAG pipeline
    rag = RAGPipeline(
        chunker=RecursiveCharacterChunker(),
        embed_fn=config["embed_fn"],
        vector_store=config["vector_store"],
        top_k=5,
    )

    # PS4: Initialize memory
    memory = CognitiveMemory(
        embed_fn=config["embed_fn"],
        vector_store=config.get("memory_store"),
    )

    # PS5: Evaluation suite
    evaluator = EvaluationSuite()

    # PS6: Safety pipeline
    safety = SafetyPipeline()

    # PS7: Multi-modal builder (if needed)
    mm_builder = MultiModalPromptBuilder()

    # PS8: Wire it all together
    agent = CognitiveAgent(
        prompt_architect=architect,
        token_optimizer=optimizer,
        rag_pipeline=rag,
        memory=memory,
        evaluator=evaluator,
        safety_pipeline=safety,
        multimodal_builder=mm_builder,
        llm_fn=config["llm_fn"],
        tools=config.get("tools", []),
    )

    return agent.run(user_intent)
```

### Pattern 2: Self-Improving RAG
**Flow:** PS3 retrieves → PS5 evaluates retrieval quality → PS2 adjusts chunking → repeat

```python
def self_improving_rag(query: str, rag: RAGPipeline,
                       evaluator: EvaluationSuite,
                       reference: str, iterations: int = 3) -> list[Chunk]:
    """RAG pipeline that improves its own retrieval quality."""
    best_chunks = []
    best_score = 0.0
    chunk_sizes = [512, 256, 1024, 128]

    for i in range(min(iterations, len(chunk_sizes))):
        rag.chunker = RecursiveCharacterChunker(chunk_size=chunk_sizes[i])
        chunks = rag.retrieve(query)
        context = rag.build_context(chunks, token_budget=2000)

        eval_result = evaluator.rouge_l(reference, context)
        if eval_result.score > best_score:
            best_score = eval_result.score
            best_chunks = chunks

        if best_score > 0.8:
            break

    return best_chunks
```

### Pattern 3: Memory-Augmented Evaluation
**Flow:** PS5 evaluates → PS4 stores learnings → PS1 adapts prompts from memory

```python
def memory_augmented_eval(prompt: str, output: str, reference: str,
                          memory: CognitiveMemory,
                          evaluator: EvaluationSuite,
                          meta_engine: MetaPromptEngine) -> str:
    """Evaluation that learns from past attempts via memory."""
    # Evaluate current output
    results = evaluator.evaluate_all(reference, output)
    avg_score = sum(r.score for r in results) / max(len(results), 1)

    # Store evaluation in semantic memory
    memory.semantic.learn(
        key=f"eval_{hash(prompt) % 10000}",
        content=f"Prompt scored {avg_score:.2f}. "
                f"Issues: {[r.metric for r in results if not r.passed]}",
        importance=avg_score,
    )

    # Recall past evaluation learnings
    past_learnings = memory.semantic.query("prompt evaluation improvement", top_k=3)
    feedback = (
        f"Score: {avg_score:.2f}\n"
        f"Failed: {[r.metric for r in results if not r.passed]}\n"
        f"Past learnings:\n"
        + "\n".join(f"- {l.content}" for l in past_learnings)
    )

    # PS1: Meta-prompt generates improved version
    improved = meta_engine.iterative_refine(prompt, feedback)
    return improved
```

### Pattern 4: Safe Multi-Modal Agent
**Flow:** PS7 processes input → PS6 validates → PS8 orchestrates → PS6 validates output

```python
def safe_multimodal_agent(
    text_input: str, image_path: str | None,
    safety: SafetyPipeline, agent: CognitiveAgent
) -> str:
    """Multi-modal agent with full safety wrapping."""
    # PS6: Pre-validate text input
    verdict, checks = safety.evaluate(text_input)
    if verdict == SafetyVerdict.BLOCK:
        return "[BLOCKED] Input violates safety policy."

    # PS7: Build multi-modal prompt if image provided
    if image_path:
        mm = MultiModalPromptBuilder("Expert analyst")
        mm.add_text(text_input)
        mm.add_image(image_path)
        messages = mm.build()
        combined_input = f"{text_input} [+image: {image_path}]"
    else:
        combined_input = text_input

    # PS8: Run through cognitive agent (safety already wraps LLM)
    result = agent.run(combined_input)

    return result
```

---

## 🌐 Domain Applications

### Legal AI (LitigationOS)
```python
litigation_config = {
    "role": "Expert Michigan family law attorney and legal analyst",
    "complexity": 0.9,
    "token_budget": 8000,
    "context_window": 128000,
    "tools": [
        ToolDefinition(
            name="search_evidence",
            description="Search litigation evidence database",
            parameters={"query": {"type": "string"}},
            handler=lambda query: evidence_search(query),
        ),
        ToolDefinition(
            name="lookup_authority",
            description="Look up MCR/MCL legal authorities",
            parameters={"citation": {"type": "string"}},
            handler=lambda citation: authority_lookup(citation),
        ),
    ],
}
# result = cognitive_pipeline("Draft motion to compel discovery", litigation_config)
```

### Code Generation
```python
code_config = {
    "role": "Senior software engineer specializing in Python and TypeScript",
    "complexity": 0.7,
    "token_budget": 4096,
    "context_window": 128000,
    "tools": [
        ToolDefinition(
            name="search_codebase",
            description="Search repository code with ripgrep",
            parameters={"pattern": {"type": "string"}, "path": {"type": "string"}},
            handler=lambda pattern, path=".": code_search(pattern, path),
        ),
        ToolDefinition(
            name="run_tests",
            description="Execute test suite",
            parameters={"test_path": {"type": "string"}},
            handler=lambda test_path: run_tests(test_path),
        ),
    ],
}
```

### Research & Analysis
```python
research_config = {
    "role": "Research scientist with expertise in systematic literature review",
    "complexity": 0.8,
    "token_budget": 6000,
    "context_window": 200000,
    "tools": [
        ToolDefinition(
            name="search_papers",
            description="Search academic papers by keyword",
            parameters={"query": {"type": "string"}, "limit": {"type": "integer"}},
            handler=lambda query, limit=10: search_papers(query, limit),
        ),
    ],
}
```

---

## 📋 Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════════════╗
║              FORGE-PROMPT-SINGULARITY  (Ω-Δ99)  Quick Reference       ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  MODULE      PURPOSE                    KEY CLASS / FUNCTION           ║
║  ─────────   ────────────────────────   ───────────────────────────    ║
║  PS1         Prompt architecture         PromptArchitecture            ║
║              Chain-of-thought            MetaPromptEngine              ║
║              Meta-prompting              build_cot_prompt()            ║
║                                                                        ║
║  PS2         Token compression           TokenOptimizer                ║
║              Context window mgmt         ContextWindow                 ║
║                                                                        ║
║  PS3         RAG pipeline                RAGPipeline                   ║
║              Chunking + retrieval        RecursiveCharacterChunker     ║
║              Hybrid search + rerank      SemanticChunker               ║
║                                                                        ║
║  PS4         Agent memory                CognitiveMemory               ║
║              Episodic + semantic          EpisodicMemory               ║
║              + working memory             SemanticMemory               ║
║                                           WorkingMemory                ║
║                                                                        ║
║  PS5         Evaluation                  EvaluationSuite               ║
║              Self-improvement            PromptEvolver                 ║
║              Genetic evolution           evolve()                      ║
║                                                                        ║
║  PS6         Safety & alignment          SafetyPipeline                ║
║              Guardrails + PII            ToxicityFilter                ║
║              Constitutional AI           ConstitutionalAIFilter        ║
║                                                                        ║
║  PS7         Multi-modal                 MultiModalPromptBuilder       ║
║              Vision + audio + doc        build_vision_prompt()         ║
║                                          build_document_extraction()   ║
║                                                                        ║
║  PS8         Orchestration               CognitiveAgent                ║
║              Agent loops + tools         ParallelChainExecutor         ║
║              Function calling            ToolDefinition                ║
║                                                                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  EMERGENT CAPABILITY: Cognitive Architecture Synthesis                 ║
║  ─────────────────────────────────────────────────────                 ║
║  Intent → PS1:Design → PS2:Compress → PS3:Retrieve → PS4:Remember     ║
║       → PS5:Evaluate → PS6:Guard → PS7:Perceive → PS8:Orchestrate     ║
║       → PS5:Re-evaluate → PS1:Re-design (self-improving loop)         ║
║                                                                        ║
║  CROSS-MODULE PATTERNS                                                 ║
║  ─────────────────────                                                 ║
║  1. cognitive_pipeline()        Full end-to-end architecture           ║
║  2. self_improving_rag()        RAG that optimizes its own retrieval   ║
║  3. memory_augmented_eval()     Eval that learns from past attempts    ║
║  4. safe_multimodal_agent()     Multi-modal with safety wrapping       ║
║                                                                        ║
║  TRIGGERS: prompt singularity | cognitive architecture | forge prompt  ║
║            self-improving prompt | RAG pipeline | agent memory design  ║
║            prompt optimization | AI safety prompt | multi-modal prompt ║
║            LLM orchestration | prompt evaluation loop | prompt chain   ║
║                                                                        ║
║  FORGED: 2026-03-27 | AUTHOR: andrew-pigors + copilot-omega-delta-99  ║
║  TIER: FORGE | FUSED: 10 skills | VERSION: 1.0.0                      ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

*Forged by Omega-Delta-99. The prompt that engineers itself.*
