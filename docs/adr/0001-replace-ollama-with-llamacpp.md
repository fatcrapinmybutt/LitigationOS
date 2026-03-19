# ADR-0001: Replace Ollama with llama.cpp for Local LLM Inference

- **Status:** Accepted
- **Date:** 2026-03-06
- **Deciders:** Andrew Pigors

## Context

LitigationOS is a litigation intelligence system for Michigan family law (Pigors v. Watson) with a **permanent local-only AI lock** — zero network traffic, zero API keys. This is a non-negotiable security and privacy constraint for handling sensitive litigation evidence.

The previous system used Ollama as the local LLM runtime, but it was permanently removed due to its heavier runtime overhead and operational issues. The current AI engine is **MANBEARPIG v9.0**, which provides TF-IDF + Naive Bayes + BM25 + semantic embeddings. While effective for document classification and lane detection, MANBEARPIG **cannot**:

- Reason about legal arguments or case law
- Synthesize evidence across multiple documents
- Draft motion language or legal briefs
- Perform multi-step inference chains

The system runs on constrained hardware:
- **RAM:** 22.4 GB
- **GPU:** AMD Vega 8 (2 GB integrated, no discrete GPU)
- **OS:** Windows 10
- **Storage:** Multi-drive (C:\, D:\, F:\, G:\, H:\, I:\)

The Ollama executable still exists at `C:\Users\andre\AppData\Local\Programs\Ollama\ollama.exe`, and 4.6 GB of dead-weight Ollama models on I:\ were already cleaned up.

## Decision Drivers

- Must operate fully offline — zero network, zero API keys
- Must fit within 22.4 GB RAM alongside other system processes
- Must run on CPU only (AMD Vega 8 integrated GPU is insufficient for LLM inference)
- Must be scriptable and embeddable in the Python pipeline (not GUI-dependent)
- Must provide genuine reasoning capability beyond statistical classification
- Should minimize storage footprint on already-constrained drives

## Considered Options

### Option 1: llama.cpp + Small Model (Phi-3-mini or Qwen-2.5-3B) — **CHOSEN**

Direct C++ inference engine with Python bindings (`llama-cpp-python`). Run a quantized small model (Phi-3-mini-4k-instruct Q4_K_M, ~2.3 GB) for CPU-only inference.

### Option 2: Re-enable Existing Ollama Installation

Re-activate the Ollama runtime already present on the system. Provides model management and an API layer.

### Option 3: LM Studio

Desktop application for running local LLMs with a polished GUI and model management.

### Option 4: Keep MANBEARPIG TF-IDF Only

Continue with the current statistical engine without adding LLM reasoning.

### Option 5: vLLM

High-throughput LLM serving engine optimized for GPU inference.

## Decision

Adopt **llama.cpp** via `llama-cpp-python` with **Phi-3-mini-4k-instruct Q4_K_M GGUF** (~2.3 GB) as the local reasoning backend. Wire it alongside the existing MANBEARPIG TF-IDF engine in a **dual-mode architecture**:

- **Fast path (MANBEARPIG):** Document classification, lane detection, entity extraction, evidence scoring — sub-second statistical inference.
- **Deep path (llama.cpp):** Legal argument reasoning, evidence synthesis, motion language drafting, multi-step analysis — 5-30 second LLM inference.

## Rationale

### Why llama.cpp + Phi-3-mini (Option 1)

- **Minimal runtime:** Single shared library, no daemon process, no server overhead. Loads on demand, unloads when done.
- **CPU-optimized:** Extensive AVX2/AVX-512 optimizations for x86 CPUs. Achieves ~8-12 tokens/sec on modern CPUs with Q4_K_M quantization.
- **RAM budget:** Phi-3-mini Q4_K_M uses ~2.3 GB VRAM/RAM. With 22.4 GB system RAM, this leaves ~18+ GB for Windows, Python, SQLite, and other processes.
- **Python-native:** `llama-cpp-python` provides a direct Python API — no HTTP server, no subprocess management, no port conflicts.
- **Phi-3-mini reasoning:** Despite being 3.8B parameters, Phi-3-mini demonstrates strong reasoning on benchmarks, particularly for structured tasks like legal analysis.
- **Fully offline:** One-time model download, then zero network forever.

### Why Not Option 2 (Ollama)

- Ollama was removed for good reason — heavier runtime with a persistent daemon process consuming resources.
- Adds an unnecessary HTTP API layer between Python and the model.
- Model management overhead not needed when running a single model.

### Why Not Option 3 (LM Studio)

- Closed-source application with GUI focus.
- Not scriptable for pipeline integration — cannot be called programmatically from Python agents.
- Adds a heavy desktop application dependency.

### Why Not Option 4 (MANBEARPIG Only)

- Statistical methods cannot reason about legal arguments. A 10x improvement in evidence analysis is available with even a small LLM.
- Cannot synthesize across documents or generate coherent legal language.
- System is already hitting the ceiling of what TF-IDF + Naive Bayes can do.

### Why Not Option 5 (vLLM)

- Requires NVIDIA GPU with CUDA support. The system only has AMD Vega 8 (integrated, 2 GB).
- Designed for high-throughput serving, not single-user local inference.
- Overkill for the use case.

## Consequences

### Positive

- **10x evidence analysis improvement:** LLM can reason about legal arguments, identify contradictions across depositions, and synthesize evidence chains.
- **Legal drafting capability:** Can generate motion language, brief sections, and argument structures — currently impossible with TF-IDF.
- **Zero network:** Maintains the permanent local-only lock. One-time model file download, then fully air-gapped.
- **Fits hardware:** 2.3 GB model + 22.4 GB RAM = comfortable headroom.
- **Dual-mode efficiency:** Fast statistical classification for bulk operations, deep LLM reasoning for targeted analysis.

### Negative

- **One-time model download:** ~2.3 GB GGUF file must be downloaded once and stored locally.
- **CPU inference speed:** ~8-12 tokens/sec on CPU vs ~50+ tokens/sec on GPU. Legal analysis tasks will take 5-30 seconds per query.
- **Compilation complexity:** `llama-cpp-python` may require C++ build tools on Windows (Visual Studio Build Tools or MinGW).
- **Context window limit:** Phi-3-mini-4k has a 4K token context window, limiting single-prompt document analysis to ~3,000 words.

### Neutral

- Ollama executable at `C:\Users\andre\AppData\Local\Programs\Ollama\ollama.exe` can be removed for cleanup but is not causing harm.

## Implementation Notes

### Integration Architecture

```
┌─────────────────────────────────────────────┐
│              inference_engine.py             │
│         (MANBEARPIG v9.0 - Router)          │
├──────────────────┬──────────────────────────┤
│   Fast Path      │      Deep Path           │
│   TF-IDF/BM25    │      llama.cpp           │
│   Naive Bayes    │      Phi-3-mini Q4_K_M   │
│   ~10ms/query    │      ~5-30s/query         │
├──────────────────┼──────────────────────────┤
│  Classification  │  Legal reasoning          │
│  Lane detection  │  Evidence synthesis       │
│  Entity extract  │  Motion drafting          │
│  Evidence score  │  Argument analysis        │
└──────────────────┴──────────────────────────┘
```

### Setup Steps

1. Install Python bindings: `pip install llama-cpp-python`
2. Download Phi-3-mini Q4_K_M GGUF to `00_SYSTEM/local_model/models/`
3. Create `llm_reasoning.py` wrapper with `reason()`, `synthesize()`, `draft()` methods
4. Wire into `inference_engine.py` as the deep-path provider
5. Add model health check to `copilot_startup_hook.py`

### Model Storage

```
C:\Users\andre\LitigationOS\00_SYSTEM\local_model\models\
  └── phi-3-mini-4k-instruct-q4_k_m.gguf  (~2.3 GB)
```

### Fallback Behavior

If the GGUF model file is missing or llama.cpp fails to load, the system falls back to MANBEARPIG TF-IDF only — no crash, just reduced capability with a warning logged.
