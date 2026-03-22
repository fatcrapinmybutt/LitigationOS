---
description: "ELITE-OMEGA Quality Standard — The absolute minimum tier for EVERY action taken by ANY agent in LitigationOS. Non-negotiable. Applies universally."
applyTo: "**/*"
---

# ELITE-OMEGA Quality Standard

Every action, every tool call, every script, every query, every decision — ELITE-OMEGA tier minimum. No exceptions.

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

### USE (proven for LitigationOS constraints: Python 3.12, Windows, local-only, <15GB disk)
| Tool | Purpose | Why Apex |
|------|---------|----------|
| **MEEK compiled regex** | Lane detection (A-F) | Single-pass, O(1), already built |
| **spaCy + EntityRuler** | Legal NER (cases, statutes, judges, parties) | Lightweight, extensible, Michigan-customizable |
| **dateparser** | Date normalization from varied formats | Python-native, no Java, handles "Oct 30, 2024" and "last Thursday" |
| **TF-IDF + MiniBatchKMeans** | Topic clustering (scikit-learn) | Local, fast, interpretable, scales to millions |
| **NetworkX** | Evidence knowledge graph | Directed graphs, path analysis, gap detection |
| **FTS5 + BM25** | Full-text search | Production-grade relevance ranking in SQLite |
| **ijson** | Stream 1.5GB ChatGPT JSON | O(1) memory, binary mode, IncompleteJSONError handling |
| **PyMuPDF (fitz)** | PDF text extraction | Fastest Python PDF library |
| **TF-IDF cosine similarity** | Lightweight contradiction detection | No PyTorch needed, good baseline |
| **sentence-transformers** | Semantic contradiction detection | all-MiniLM-L6-v2, local-only, 80MB model, cosine similarity + NLI |

### SKIP (researched and rejected — do NOT waste time on these)
| Tool | Why Skip |
|------|----------|
| **Blackstone NLP** | DEAD since 2019, incompatible with spaCy v3 / Python 3.12 |
| **pysimdjson** | Won't compile on this machine (no MSVC C++ compiler) |
| **HeidelTime / SUTime** | Requires Java JVM, overkill for our date formats |
| **Remote LLMs (Ollama/Gemini)** | Violates local-only mandate, Ollama already deleted |
| **Commercial e-discovery** | We're building our own; subscription not viable for pro se |

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
