# On-Demand Tools Quick Reference
# 49 extension tools consolidated → 22 always-loaded. The rest: invoke via exec_python.

---

## 1. LEXOS LLM Tools (6 tools — require Ollama)

Bridge script: `.github\extensions\singularity\lexos_bridge.py`
Prerequisite: Ollama running with models at `J:\OLLAMA_MODELS`

### Invocation Pattern

```python
import json, subprocess, os

BRIDGE = r"C:\Users\andre\LitigationOS\.github\extensions\singularity\lexos_bridge.py"
ENV = {**os.environ, "OLLAMA_MODELS": r"J:\OLLAMA_MODELS"}

def lexos(payload: dict, timeout=360) -> dict:
    r = subprocess.run(
        ["python", BRIDGE],
        input=json.dumps(payload),
        capture_output=True, text=True, timeout=timeout, env=ENV
    )
    return json.loads(r.stdout)
```

### Actions

| Tool | Payload | Use Case |
|------|---------|----------|
| `lexos_analyze` | `{"action": "analyze", "query": "..."}` | LLM legal analysis of a topic or claim |
| `lexos_draft` | `{"action": "draft", "topic": "...", "section": "argument\|facts\|conclusion"}` | Draft a filing section |
| `lexos_impeach` | `{"action": "impeach", "target": "Emily Watson"}` | Generate cross-examination material |
| `lexos_cite` | `{"action": "cite", "query": "custody modification"}` | Build authority chain for a legal concept |
| `lexos_reason` | `{"action": "reason", "query": "..."}` | Chain-of-thought legal reasoning |
| `lexos_ask` | `{"action": "ask", "query": "..."}` | General legal Q&A |

### Examples

```python
# Analyze parental alienation evidence
result = lexos({"action": "analyze", "query": "parental alienation evidence"})

# Draft argument section for emergency motion
result = lexos({"action": "draft", "topic": "emergency custody restoration", "section": "argument"})

# Build impeachment package for Watson
result = lexos({"action": "impeach", "target": "Emily Watson"})

# Authority chain for disqualification
result = lexos({"action": "cite", "query": "judicial disqualification MCR 2.003"})
```

---

## 2. MCP Litigation Context Tools (on-demand import)

Previously loaded via MCP server. Now import directly from `00_SYSTEM\mcp_server\`.

### Import Pattern

```python
import sys
sys.path.insert(0, r"C:\Users\andre\LitigationOS\00_SYSTEM\mcp_server")
from server import <function_name>
```

### Key On-Demand Tools

| Tool | Purpose |
|------|---------|
| `litigation_filing_generate_pdf` | Convert markdown → court-formatted PDF (Times New Roman 12pt, double-spaced) |
| `litigation_exhibit_bates_stamp` | Apply sequential Bates numbers (`PREFIX-NNNNNN`) to PDF pages |
| `litigation_filing_assemble_package` | Assemble full filing: motion + exhibits + COS + Bates + manifest |
| `litigation_filing_certificate_of_service` | Generate COS (defaults: Watson via Barnes, FOC via Rusco) |
| `litigation_evolve_files` | Evolve .md/.txt files into cross-reference knowledge layer |
| `litigation_evolve_pdfs` | Evolve ingested PDF pages into cross-reference layer |

### Examples

```python
# Generate court-formatted PDF from markdown
from server import litigation_filing_generate_pdf
litigation_filing_generate_pdf(filing_id="F1", markdown_content="# MOTION\n...")

# Bates-stamp an exhibit
from server import litigation_exhibit_bates_stamp
litigation_exhibit_bates_stamp(
    input_pdf=r"05_FILINGS\exhibit_a.pdf",
    output_pdf=r"05_FILINGS\exhibit_a_bates.pdf",
    prefix="PIGORS", start_number=1
)

# Assemble complete filing package
from server import litigation_filing_assemble_package
litigation_filing_assemble_package(
    filing_id="F3",
    main_document=r"05_FILINGS\motion_to_compel.md",
    exhibits=[
        {"label": "Exhibit A", "title": "PPO Filing", "path": r"01_EVIDENCE\ppo.pdf"},
        {"label": "Exhibit B", "title": "Recantation", "path": r"01_EVIDENCE\recant.pdf"}
    ]
)

# Generate Certificate of Service
from server import litigation_filing_certificate_of_service
litigation_filing_certificate_of_service(method="electronic", filing_date="July 15, 2026")
```

---

## 3. Direct DB Queries (fallback for everything else)

For any capability not covered above, query `litigation_context.db` directly.

### Connection Pattern

```python
import sqlite3

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-50000")
```

### FTS5 Safety (MANDATORY)

```python
import re
def safe_fts5(query: str) -> str:
    return re.sub(r'[^\w\s*"]', ' ', query)

# CORRECT — sanitized
cursor.execute("SELECT * FROM evidence_fts WHERE evidence_fts MATCH ?", (safe_fts5(query),))

# FALLBACK — if FTS5 errors
cursor.execute("SELECT * FROM evidence_quotes WHERE quote_text LIKE ?", (f"%{query}%",))
```

### Key Tables

| Table | Rows | FTS Index | Common Query |
|-------|------|-----------|--------------|
| `evidence_quotes` | 92K+ | `evidence_fts` | Evidence search by keyword |
| `timeline_events` | 16K+ | `timeline_fts` | Chronological event lookup |
| `authority_chains_v2` | 31K+ | — | Legal authority chain traversal |
| `impeachment_matrix` | 1.4K+ | — | Cross-exam material by target |
| `contradiction_map` | 10K+ | — | Statement contradictions |
| `judicial_violations` | 5K+ | — | McNeill misconduct evidence |
| `police_reports` | 356 | — | NSPD/MSP report data |
| `master_citations` | 3.6M | — | Citation verification |

### Schema Discovery

```python
# Always verify schema before first query on unfamiliar table
cursor.execute("PRAGMA table_info(evidence_quotes)")
columns = [row[1] for row in cursor.fetchall()]
```

---

## Decision Tree

```
Need LLM reasoning/drafting?
  YES → LEXOS tools (Section 1)
  NO ↓

Need PDF generation / Bates / filing assembly?
  YES → MCP server import (Section 2)
  NO ↓

Need data from litigation DB?
  YES → Direct SQL (Section 3)
  NO → Check 00_SYSTEM/engines/ for specialized engines
```

---

## Notes

- **Ollama must be running** for any LEXOS tool. Start with: `ollama serve`
- **exec_python preferred** over powershell for all Python invocations (Rule 17)
- **Never hardcode day counts** — compute `(today - date(2025,7,29)).days` dynamically
- **Brain DBs** at `00_SYSTEM\brains\*.db` for specialized datasets
- **Always close DB connections** after use to avoid WAL lock contention
