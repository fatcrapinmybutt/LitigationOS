# SINGULARITY Toolchain — Bleeding-Edge Stack (2026)

> **SINGLE SOURCE OF TRUTH** for the technology stack, tool routing, and apex method selection.
> Absorbs: eagain-prevention, elite-omega-standard. Pre-SINGULARITY relics archived.

## Execution Hierarchy (route every operation through this)

| Priority | Tool | Use For |
|----------|------|---------|
| **1** | `view`/`edit`/`create`/`grep`/`glob`/`sql` | Files, search, state — instant, zero overhead |
| **2** | `exec_python` / `exec_git` / `exec_command` | Scripts, git, CLI — subprocess, no pipes |
| **3** | `task` agents (explore/task/general-purpose) | Parallel work — isolated processes |
| **4** | `powershell` | Interactive REPL only — max 2, close immediately |

## Apex Method Selection (always pick the highest)

| Operation | SINGULARITY | Legacy (don't use) |
|-----------|-------------|-------------------|
| File scanning | `fd` (Rust) | `Get-ChildItem -Recurse` |
| Text search | `tantivy`/`rg` | `LIKE '%term%'` |
| Analytics | `DuckDB` | pandas / SQLite GROUP BY |
| DataFrames | `Polars` | pandas |
| JSON | `orjson` | `json.load()` |
| PDF extraction | `pypdfium2` | PyMuPDF |
| Full-text search | `tantivy` + FTS5 BM25 | `LIKE` full scan |
| Semantic search | `sentence-transformers` + `LanceDB` | keyword counting |
| Reranking | `cross-encoder/ms-marco-MiniLM` | cosine-only |
| Court PDFs | `Typst` | LaTeX / python-docx |
| File ingestion | `Go ingest` (8-worker goroutines) | Python sequential |
| OCR | `PaddleOCR` / `Surya` | Tesseract |
| Schema validation | `msgspec.Struct` | pydantic |
| Streaming JSON | `ijson` | loading GB into memory |

## Compilation Toolchains

| Tool | Version | Installed |
|------|---------|-----------|
| Go | 1.26.1 | 2026-03-31 |
| Rust/Cargo | 1.94.1 | 2026-03-31 |
| Python | 3.12 | Pre-existing |
| Node.js | 25.8.1 | Pre-existing |

## Hardware

| Component | Spec |
|-----------|------|
| CPU | AMD Ryzen 3 3200G (Radeon Vega) |
| RAM | 24 GB |
| GPU | Vega 8 (2GB VRAM, integrated) |
| Embedding | all-MiniLM-L6-v2 runs fast on CPU |

## Python Packages

### Data & Analytics
- **DuckDB 1.5.1** — 10-100× faster analytical queries than SQLite
- **Polars 1.39.3** — 2-10× faster DataFrames than pandas
- **orjson** — 10× JSON serialization (Rust-backed)

### Search & Retrieval
- **tantivy** — Rust full-text search, sub-ms BM25
- **LanceDB** — Embedded vector DB (Rust-backed), 75K vectors
- **sentence-transformers 5.3.0** — 384-dim embeddings, CPU
- **cross-encoder** — ms-marco-MiniLM, 25-35% MRR boost
- **torch 2.11.0** (CPU-only) — PyTorch backend

### Document Processing
- **pypdfium2** — PDF extraction 5× faster than PyMuPDF
- **Typst 0.14.2** — Court-ready PDF generation (Rust-based)

### System
- watchdog — File system monitoring
- ruff — Python linting 100× faster than pylint
- uv — Package management 10× faster than pip

## Rust CLI Tools

- **fd 10.4.2** — File finder 5× faster than find/dir
- **bat 0.26.1** — Syntax-highlighted file viewing
- **dust 1.2.4** — Disk usage visualization
- **hyperfine 1.20.0** — CLI benchmarking
- **tokei 12.1.2** — Code statistics

## LitigationOS Engines

| Engine | Backend | Purpose |
|--------|---------|---------|
| Analytics | DuckDB | 10-100× analytical queries |
| Semantic | LanceDB + sentence-transformers | Vector similarity search |
| Search | tantivy + semantic + FTS5 | Hybrid multi-backend search |
| Typst | Typst compiler | Court-ready PDF generation |
| Ingest | Go (8-worker goroutines) | Bulk file ingestion |

## Dead Libraries (researched and rejected — do NOT use)

| Library | Why Dead | Use Instead |
|---------|----------|-------------|
| Blackstone NLP | Dead since 2019, incompatible Python 3.12 | spaCy + EntityRuler |
| LexNLP | Stale, Python 3.8 only | spaCy + custom patterns |
| pysimdjson | Won't compile (no MSVC) | msgspec / orjson |
| HeidelTime/SUTime | Requires Java | dateparser |
| pydantic (validation) | 10-80× slower | msgspec.Struct |
| EasyOCR | 62.5% accuracy | PaddleOCR (100%) |
| Tesseract | 85-95% accuracy | PaddleOCR / Surya |

## Disk Space
C: drive is TIGHT (255 GB total). Keep pip cache purged. J: has 1.9 TB free for bulk storage.