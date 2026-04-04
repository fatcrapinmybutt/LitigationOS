---
description: "Modern toolchain routing — Go/Rust/DuckDB-first architecture"
applyTo: "**/*"
---

# Toolchain Routing (2026 — Post-Legacy)

## Execution Hierarchy

| Priority | Tool | Speed | Use For |
|----------|------|-------|---------|
| **1** | `view`/`edit`/`create`/`grep`/`glob`/`sql` | Instant | Files, search, state |
| **2** | `exec_python` / `exec_git` / `exec_command` | Fast | Scripts, git, CLI — subprocess, zero overhead |
| **3** | `task` agents (explore/task/general-purpose) | Parallel | Multi-step work — isolated processes |
| **4** | `powershell` | Slow | Interactive REPL only — max 2, close immediately |

## Bleeding-Edge Stack (use these, not legacy Python)

| Tool | Language | Use Instead Of | Speed Gain |
|------|----------|---------------|------------|
| **Go ingest engine** | Go | Python file processing | 8-worker goroutines, 57K files zero errors |
| **fd** | Rust | `Get-ChildItem`, `os.walk` | 5-50× faster file finding |
| **bat** | Rust | `cat`, `type` | Syntax-highlighted viewing |
| **tantivy** | Rust | FTS5 for hot-path search | Sub-ms full-text, BM25 |
| **DuckDB** | C++ | SQLite OLAP queries | 10-100× analytical queries |
| **LanceDB** | Rust | Manual vector search | Sub-ms similarity, 75K vectors |
| **Polars** | Rust | pandas DataFrames | 2-10× faster, zero copy |
| **Typst** | Rust | LaTeX / python-docx PDF | Instant compile, court-ready |
| **orjson** | Rust | `json.load()` | 10× JSON serialization |
| **pypdfium2** | C | PyMuPDF for extraction | 5× PDF text extraction |
| **sentence-transformers** | PyTorch | Keyword-only search | 384-dim embeddings, CPU |
| **cross-encoder** | PyTorch | Cosine-only ranking | 25-35% MRR boost, reranking |
| **PaddleOCR** | PaddlePaddle | Tesseract | 100% accuracy on legal forms |
| **Surya OCR** | PyTorch | Tesseract | Layout-aware, table detection |

## Apex Decision Rule

Before every operation: **Is there a Rust/Go/C++ tool that does this faster than Python?** If yes, use it.

- File scan → `fd` not `os.walk`
- Text search → `tantivy`/`rg` not `LIKE '%term%'`
- Analytics → `DuckDB` not pandas/SQLite
- JSON → `orjson` not `json`
- PDF → `pypdfium2` not PyMuPDF
- Embeddings → `sentence-transformers` not keyword counting
- Court PDFs → `Typst` not LaTeX
