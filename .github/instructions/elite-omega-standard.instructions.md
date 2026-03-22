---
description: "ELITE-OMEGA Quality Standard — The absolute minimum tier for EVERY action taken by ANY agent in LitigationOS. Non-negotiable. Applies universally."
applyTo: "**/*"
---

# ELITE-OMEGA Quality Standard

Every action, every tool call, every script, every query, every decision — ELITE-OMEGA tier minimum. No exceptions.

## 🚨 APEX RESEARCH MANDATE (SUPREME GOVERNANCE — NON-NEGOTIABLE)

> **"Not just what you create, or your method, but the DECISIONS you make need to be apex decisions.
> Research things before you just proceed to doing them. There are apex, bleeding edge technologies
> out there that you can acquire/absorb to be exponentially better, in every aspect. Full spectrum."**
> — Andrew Pigors, 2026-03-22

### The Mandate

**BEFORE implementing ANYTHING — research first.** Every decision must be research-verified as the
absolute best available technology/approach in 2025. This applies to:

- **Tool selection** — Is there a faster/better library? Research it.
- **Algorithm choice** — Is there a more efficient approach? Research it.
- **Architecture decisions** — Is there a better pattern? Research it.
- **Data structures** — Is there a more optimal representation? Research it.
- **Parsing strategy** — Is there a higher-throughput method? Research it.
- **NLP approach** — Is there a more accurate model? Research it.
- **Search method** — Is there a more relevant ranking? Research it.
- **Storage format** — Is there a more compact/queryable option? Research it.

### Research Protocol (Mandatory Before Implementation)

1. **Multi-faceted web search** (minimum 3 queries per decision):
   - Comparative: "X vs Y vs Z for [specific use case] 2025 benchmark"
   - State-of-art: "best approach for [task] in [domain] 2025"
   - Failure analysis: "problems with [baseline approach] and better alternatives"
2. **Evaluate against constraints**: Python 3.12, Windows, local-only, <25GB disk, CPU-only
3. **Verify currency**: Is it maintained? Last release? Python 3.12 compatible?
4. **Save findings**: Permanent memory + instruction files + brain DB
5. **Only then implement** — using the research-verified apex approach

### Apex Decision Checklist (Self-Check Before EVERY Action)

```
□ Did I research alternatives before choosing this approach?
□ Is this the 2025 state-of-the-art for this specific task?
□ Have I verified it works with our constraints (Python 3.12, Windows, local, CPU)?
□ Am I using baseline when apex exists? (cosine → cross-encoder, regex → Legal-BERT, json.load → msgspec)
□ Would a principal engineer at a top tech company approve this choice?
□ Have I saved my research findings permanently?
```

### Apex vs Baseline Decision Matrix (Research-Verified 2025)

| Domain | BASELINE (unacceptable) | APEX (required) |
|--------|------------------------|-----------------|
| JSON parsing (multi-GB) | `json.load()` into memory | `ijson` streaming + `msgspec` Struct validation |
| Schema validation | Manual dict key checks | `msgspec.Struct` zero-cost typed validation (10-80x faster than pydantic) |
| Legal NER | Simple regex capture groups | `spaCy` + custom `EntityRuler` + `Legal-BERT` embeddings |
| Contradiction detection | Cosine similarity only | Two-stage: bi-encoder retrieval → cross-encoder precision reranking |
| Text classification | Keyword counting | `Legal-BERT` (nlpaueb/legal-bert-base-uncased, 110M params, CPU inference) |
| Relevance scoring | Keyword hit count 0-1.0 | TF-IDF vectorization against legal corpus + BM25 ranking |
| Date extraction | Regex patterns only | `dateparser` library (handles relative dates, multi-format) |
| Topic clustering | Manual folder tagging | TF-IDF + MiniBatchKMeans (scikit-learn) |
| Evidence graph | Flat lists / CSV | `NetworkX` directed knowledge graph with path analysis |
| Dedup | File hash comparison | Content-based peek + semantic similarity (user mandate) |
| File moving | `shutil.copy()` then delete | `os.rename()` zero-copy + `shutil.move()` cross-device fallback |
| DB queries | Sequential `SELECT COUNT(*)` | Single query with subqueries, CTEs, window functions |
| Search | `LIKE '%term%'` full scan | FTS5 + BM25 ranking + adaptive query rewriter |

### Dead/Abandoned Libraries (Do NOT Use — Researched and Rejected)

| Library | Status | Why Dead | Alternative |
|---------|--------|----------|-------------|
| **Blackstone NLP** | Abandoned 2019 | Incompatible spaCy v3 / Python 3.12 | spaCy + EntityRuler |
| **LexNLP** | Stale (last release Feb 2023) | Python 3.8 only, won't install on 3.12 | spaCy + custom patterns |
| **pysimdjson** | Broken on Windows | Requires MSVC C++ compiler | msgspec (faster anyway) |
| **HeidelTime/SUTime** | Java dependency | Requires JVM, overkill | dateparser (Python-native) |

## Apex Method Selection

Before executing ANY operation, evaluate: "Is this the absolute best method available?"

### Tool Hierarchy (always pick the highest available)

| Operation | Apex | Good | Unacceptable |
|-----------|------|------|-------------|
| File scanning | `fd` (Rust) or Python `os.scandir` single-pass | `rg --files` | PowerShell `Get-ChildItem -Recurse` with nested loops |
| Text search | `rg` with compiled patterns | `grep` with glob | PowerShell `Select-String` nested |
| DB queries | `ATTACH` cross-DB + CTE + window functions | Single-DB joins | Multiple sequential `SELECT COUNT(*)` |
| JSON parsing | Streaming (`ijson`) for >100MB, `orjson` for speed | `json.load` for small files | Loading 1GB into memory at once |
| Search | FTS5 + BM25 ranking | FTS5 MATCH | `LIKE '%term%'` full scan |
| Python execution | Temp `.py` file with `-I` flag via `.mcp_venv` | Here-string pipe | `python -c "..."` inline |
| Parallelism | Task agents (isolated pipes) | Async shells (shared pipes) | Sequential everything |
| Output handling | File redirect + `view` for large | Piped with `Select-Object -First N` | Unbounded pipe output |

### Engineering Principles

- **Single-pass over multi-pass**: Scan once with compiled regex, not N times with N patterns
- **Streaming over loading**: Process large files incrementally, never load GB files into memory
- **Compiled over interpreted**: Pre-compile regex patterns, use frozenset for lookups
- **Batch over sequential**: `executemany` not loops, bulk inserts not row-by-row
- **Index-first**: Create indexes BEFORE queries, not after discovering slowness
- **Fail-forward**: Every error is an upgrade opportunity, not a fallback excuse

### Quality Gates (self-check before EVERY action)

1. Is there a faster tool for this? → Use it
2. Is there a more memory-efficient approach? → Use it
3. Can this be parallelized? → Do it
4. Am I making multiple passes when one would suffice? → Consolidate
5. Am I using the language/tool's most advanced features? → Level up
6. Would a senior principal engineer approve this approach? → If not, redesign

## Apex Web Research Method (Non-Negotiable)

Never use keyword-stuffing searches. Always use:
1. **Full natural-language prompts** — describe exactly what you need in a complete sentence
2. **Multi-faceted parallel queries** (4+ per topic):
   - Technical: "What is the best approach for X?"
   - Adversarial: "What are the failure modes and problems with X?"
   - Industry: "What do professionals actually use for X in production?"
   - Comparative: "Compare X vs Y vs Z for this specific use case"
3. **Iterative depth** — use Round 1 findings to craft more specific Round 2 queries
4. **Deep-dive** — use `web_fetch` on the most promising result URLs for full article content
5. **Store findings** — persist research to permanent memory + instruction files

## Apex Legal Intelligence Stack (Vetted 2025)

### USE (proven for LitigationOS constraints: Python 3.12, Windows, local-only, <25GB disk)

#### Tier 1 — Core Pipeline (zero-dependency, always available)
| Tool | Purpose | Why Apex |
|------|---------|----------|
| **MEEK compiled regex** | Lane detection (A-F) | Single-pass, O(1), already built |
| **ijson** | Stream 1.5GB+ ChatGPT JSON | O(1) memory, SAX-style, binary mode |
| **msgspec Structs** | Zero-cost JSON schema validation | 10-80x faster than pydantic, typed extraction |
| **orjson** | Sub-GB JSON speed parsing | Rust-based, fastest full-load parser |
| **PyMuPDF (fitz)** | PDF text extraction | Fastest Python PDF library |
| **FTS5 + BM25** | Full-text search | Production-grade relevance ranking in SQLite |
| **dateparser** | Date normalization from varied formats | Python-native, no Java, handles relative dates |
| **TF-IDF + MiniBatchKMeans** | Topic clustering (scikit-learn) | Local, fast, interpretable, scales to millions |
| **NetworkX** | Evidence knowledge graph | Directed graphs, path analysis, gap detection |

#### Tier 2 — Intelligence Layer (ML models, requires torch)
| Tool | Purpose | Why Apex |
|------|---------|----------|
| **sentence-transformers** | Semantic embeddings + similarity | all-MiniLM-L6-v2 (80MB), local-only, bi-encoder |
| **cross-encoder** | Precision contradiction detection | ms-marco-MiniLM-L-6-v2, reranking stage 2 |
| **Legal-BERT** | Legal text classification | nlpaueb/legal-bert-base-uncased, 110M params, CPU OK |
| **spaCy + EntityRuler** | Legal NER (cases, statutes, judges) | Lightweight, extensible, Michigan-customizable |

#### Contradiction Detection Pipeline (TWO-STAGE — mandatory)
```
Stage 1 — RETRIEVAL (bi-encoder): sentence-transformers/all-MiniLM-L6-v2
  → Embed all evidence claims → cosine similarity → top-N candidates (fast, scalable)

Stage 2 — PRECISION (cross-encoder): cross-encoder/ms-marco-MiniLM-L-6-v2
  → Rerank top-N pairs → contradiction score → flag true contradictions (accurate, nuanced)

NEVER use cosine similarity alone — contradictory statements can be semantically close.
The two-stage pipeline catches nuanced legal contradictions that single-stage misses.
```

#### JSON Extraction Pipeline (HYBRID — mandatory for multi-GB)
```
ijson.items(f, 'item')  →  streams each conversation object (O(1) memory)
    ↓
msgspec.json.decode(chunk, type=ConversationStruct)  →  validates schema (zero-cost)
    ↓
executemany INSERT every 5000 rows  →  batch commits to brain DB
```

### SKIP (researched and rejected — do NOT waste time on these)
| Tool | Why Skip | Researched Date |
|------|----------|----------------|
| **Blackstone NLP** | DEAD since 2019, incompatible with spaCy v3 / Python 3.12 | 2026-03-22 |
| **LexNLP** | STALE — last release Feb 2023, Python 3.8 only, won't install on 3.12 | 2026-03-22 |
| **pysimdjson** | Won't compile on this machine (no MSVC C++ compiler) | 2026-03-22 |
| **HeidelTime / SUTime** | Requires Java JVM, overkill for our date formats | 2026-03-22 |
| **Remote LLMs (Ollama/Gemini)** | Violates local-only mandate, Ollama already deleted | 2026-03-22 |
| **Commercial e-discovery** | We're building our own; subscription not viable for pro se | 2026-03-22 |
| **pydantic for JSON validation** | msgspec is 10-80x faster with zero-cost schema validation | 2026-03-22 |
| **Simple cosine-only contradiction** | BASELINE — misses nuanced legal contradictions. Use two-stage pipeline | 2026-03-22 |
| **TypeLaw (appellate brief SaaS)** | $$$/filing — replaced locally with python-docx + PyMuPDF + regex | 2026-03-22 |

### NLP Failure Modes to Avoid
- **Never fabricate statistics** — every count must be a traceable DB query
- **Never trust NLP output blindly** — rule-based is explainable and auditable
- **User messages = ground truth** — Andrew's words in chats are affidavit-grade facts
- **AI responses = advisory only** — cluster by topic, tag with source platform
- **No cross-platform dedup** — keep ChatGPT/Claude/Grok analyses separately

## Apex Desktop & Architecture Stack (Vetted 2025)

### Desktop GUI Upgrade Path
| Framework | Best For | Why |
|-----------|----------|-----|
| **CustomTkinter** (current) | Legacy screens | Already built, 14 screens working |
| **Flet** (next-gen) | Desktop-native UI | Flutter-based, modern widgets, concise Python, compiles to standalone .exe |
| **NiceGUI** (dashboards) | Web-style dashboards | Material Design, Vue.js, most concise code, Pywebview for desktop |
| **Streamlit** (rapid prototypes) | Quick data dashboards | Fastest dev time, but web-branded look |
| **Taipy** (pipeline+UI) | Data pipeline dashboards | Workflow + UI in one framework |

### Graph Visualization at Scale
| Tool | Max Nodes | Python-Native | Best For |
|------|-----------|---------------|----------|
| **Neo4j Bloom** | 100K+ | No (Neo4j) | Production graph exploration, already in plan |
| **Gephi** | 100K+ | No (Java) | Analytics-heavy graph analysis, ForceAtlas2 layout |
| **yFiles Jupyter** | 50K+ | Partial | In-notebook professional graph rendering |
| **Cosmograph** | 100K+ | No (WebGL/JS) | Ultra-fast large graph browsing |
| **Pyvis** | ~20K | Yes | Quick Python renders, prototyping |
| **Dash Cytoscape** | ~30K | Yes | Custom dashboards with graph + tables |

### SQLite at Scale (10GB+ litigation_context.db)
```python
# APEX PRAGMAs for NVMe SSD
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = -50000;     # 50MB cache (up from 32MB)
PRAGMA mmap_size = 12884901888; # 12GB mmap on NVMe
PRAGMA page_size = 32768;       # 32KB pages for large-row data
PRAGMA temp_store = MEMORY;
PRAGMA busy_timeout = 60000;
PRAGMA optimize;                # Run periodically for query planner stats
```

### Appellate Brief Automation (Local Replacement for TypeLaw)
| Feature | TypeLaw (subscription) | LitigationOS (local, FREE) |
|---------|----------------------|---------------------------|
| Brief compliance | ✅ Per-court rules | ✅ Build with regex + MCR rules DB |
| Citation verification | ✅ Shepard's/KeyCite | ✅ Build with authority_master_index FTS5 |
| Word count enforcement | ✅ Integrated | ✅ python-docx word counter + court limits |
| Table of Authorities | ✅ Auto-generated | ✅ Build with python-docx + regex extraction |
| Appendix assembly | ✅ Auto-bookmarked | ✅ PyMuPDF merge + Bates stamps + bookmarks |
| Cost | $$$$ per filing | $0 — all local Python |
