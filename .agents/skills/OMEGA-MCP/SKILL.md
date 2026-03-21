---
name: OMEGA-MCP
description: >-
  Use when building, extending, debugging, or integrating MCP (Model Context Protocol)
  servers and tools. Covers MCP server architecture, tool design patterns, FastMCP Python
  framework, resource/prompt management, error handling, testing strategies, multi-transport
  configuration (stdio/SSE/streamable-HTTP), and deep integration with LitigationOS MCP
  servers (litigation-context with 45 tools across 9 categories, command-runner with 5
  execution tools). Includes JSON Schema best practices, Pydantic model integration,
  PyMuPDF PDF processing, and SQLite connection patterns (WAL, busy_timeout, managed_db).
category: discipline
version: "2.0.0"
triggers:
  - MCP
  - model context protocol
  - MCP server
  - MCP tool
  - FastMCP
  - tool design
  - tool schema
  - JSON Schema
  - MCP transport
  - stdio
  - SSE
  - streamable HTTP
  - litigation-context MCP
  - command-runner MCP
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Convergence (Cross-Lane)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County; Michigan COA; Michigan Supreme Court"
case: Pigors v Watson
dependencies: []
metadata:
  tier: 3 (Tools)
  fused_skills: 13
  author: andrew-pigors + copilot-omega
  jurisdiction: Michigan
  courts: [14th Circuit, Michigan COA, Michigan Supreme Court, USDC WDMI, JTC]
---

# 🔌 OMEGA-MCP 🔌

> **TIER 3 — Tools: MCP Server Development & Integration**
> **Pipeline:** Design → Schema → Implement → Test → Deploy → Monitor → Evolve
> **Case:** Pigors v Watson · 2 MCP servers · 50+ tools · 9 categories · Zero-pipe execution
> **Iron Law:** Tool descriptions matter more than implementations. JSON Schema is the contract. Test everything.

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                           OMEGA-MCP v2.0                                 ║
║               13 Skills → 8 Modules → 1 MCP Mastery System              ║
║                                                                          ║
║  M1  MCP Server Architecture ──┐                                         ║
║  M2  Tool Design Patterns ─────┤→ M3 FastMCP Python ──→ M6 Testing      ║
║  M4  Resource Management ──────┘        ↓                    ↓           ║
║  M5  Error Handling ───────────→ M7 Multi-Transport    M8 LitOS MCP     ║
║                                         ↓                    ↓           ║
║                                    DEPLOYED ✓          INTEGRATED ✓      ║
║                                                                          ║
║  litigation-context MCP: 45 tools · 9 categories · 12 GB DB             ║
║  command-runner MCP: 5 tools · zero-pipe · unlimited executions          ║
║  Transport: stdio (primary) · SSE · streamable-HTTP                      ║
║  Stack: Python · FastMCP · Pydantic · PyMuPDF · SQLite WAL              ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

## Forged from 13 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|---------------------|
| 1 | `mcp-builder` | MCP server scaffolding, lifecycle management |
| 2 | `mcp-tool-designer` | JSON Schema tool definitions, description engineering |
| 3 | `fastmcp-python` | FastMCP framework patterns, decorators, type hints |
| 4 | `mcp-resource-manager` | Resource URIs, templates, dynamic resource discovery |
| 5 | `mcp-error-handling` | Error codes, graceful degradation, retry patterns |
| 6 | `mcp-testing` | Tool testing, mock transports, integration tests |
| 7 | `mcp-multi-transport` | stdio, SSE, streamable-HTTP configuration |
| 8 | `python-mcp-server-generator` | Python MCP server code generation |
| 9 | `typescript-mcp-server-generator` | TypeScript MCP server patterns |
| 10 | `json-schema-expert` | JSON Schema drafts, validation, OpenAPI integration |
| 11 | `pydantic-integration` | Pydantic v2 models, serialization, validation |
| 12 | `agent-tool-builder` | Tool description optimization for LLM consumption |
| 13 | `litigation-mcp-integration` | LitigationOS-specific MCP server patterns |

---

## ═══════════════════════════════════════════════════════════════
## MODULE M1: MCP SERVER ARCHITECTURE
## ═══════════════════════════════════════════════════════════════
*Absorbs: mcp-builder, python-mcp-server-generator, typescript-mcp-server-generator*

### Phase M1-1: MCP Protocol Fundamentals

MCP (Model Context Protocol) is the standardized interface between AI agents and external tools/data. The core primitives:

| Primitive | Direction | Purpose |
|-----------|-----------|---------|
| **Tools** | Client → Server | Execute actions (query DB, generate files, run commands) |
| **Resources** | Client → Server | Read data (files, DB records, system state) |
| **Prompts** | Client → Server | Retrieve prompt templates with arguments |
| **Notifications** | Bidirectional | Progress updates, state changes, cancellation |
| **Sampling** | Server → Client | Request LLM completions from within server code |

### Phase M1-2: Server Lifecycle

```
INITIALIZATION:
  1. Client connects (stdio pipe, SSE, or HTTP)
  2. Client sends initialize request (protocol version, capabilities)
  3. Server responds with capabilities (tools, resources, prompts)
  4. Client sends initialized notification
  5. Server is ready for requests

REQUEST HANDLING:
  Client: tools/call { name: "litigation_search", arguments: { query: "withholding" } }
  Server: → validate arguments against JSON Schema
          → execute tool logic
          → return result (text, images, embedded resources)

SHUTDOWN:
  Client sends close → Server cleans up connections → Process exits
```

### Phase M1-3: LitigationOS MCP Server Layout

```
00_SYSTEM/mcp_server/
├── __init__.py
├── server.py            ← FastMCP app entry point
├── db.py                ← SQLite connection manager (WAL, busy_timeout, managed_db)
├── tools/
│   ├── core.py          ← scan_drives, ingest_pdf, bulk_ingest, search, list, get, stats
│   ├── filing.py        ← filing_readiness, validate, assemble, efiling_prep, compliance
│   ├── evidence.py      ← evidence_chain, gaps, link, authenticate, bates, exhibit, timeline
│   ├── deadline.py      ← deadline_dashboard, ics, urgency, add, update
│   ├── analysis.py      ← authority_index, citation_graph, impeachment, contradiction, bias
│   ├── qa.py            ← prefiling_qa, qa_sweep, signature_check, service_check
│   ├── backup.py        ← backup_create, version, report
│   ├── calendar.py      ← calendar_generate, sync
│   └── system.py        ← system_health
├── models/              ← Pydantic models for all tool inputs/outputs
├── utils/               ← PDF processing (PyMuPDF), text extraction, hashing
└── pyproject.toml       ← pip install -e 00_SYSTEM/mcp_server/
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE M2: TOOL DESIGN PATTERNS
## ═══════════════════════════════════════════════════════════════
*Absorbs: mcp-tool-designer, agent-tool-builder, json-schema-expert*

### Phase M2-1: The Description-First Principle

**Tool descriptions are more important than tool implementations.** The LLM reads the description to decide whether and how to call a tool. A perfect implementation with a bad description will never be called correctly.

```python
# BAD — vague description, LLM can't decide when to use it
@mcp.tool()
def search(query: str) -> str:
    """Search the database."""
    ...

# GOOD — specific, actionable, tells LLM exactly when and how to use it
@mcp.tool()
def litigation_search(
    query: str,
    lane: str | None = None,
    limit: int = 20
) -> str:
    """Full-text search across litigation evidence, filings, and case documents.

    Use when: looking for specific evidence, finding related documents,
    checking if evidence exists before creating new entries.

    Args:
        query: Natural language search query. Supports FTS5 syntax
               (AND, OR, NOT, "exact phrase", prefix*).
        lane: Optional case lane filter (A=custody, B=housing, C=convergence,
              D=PPO, E=misconduct, F=appellate). Omit to search all lanes.
        limit: Maximum results to return (default: 20, max: 100).

    Returns: Markdown table with columns: id, score, lane, date, content_preview.
    """
    ...
```

### Phase M2-2: JSON Schema Best Practices

Every MCP tool's arguments are defined by JSON Schema. Follow these rules:

```json
{
  "name": "litigation_filing_readiness",
  "description": "Check if a filing is ready for court submission. Returns GO/NO-GO with specific deficiencies.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "vehicle_name": {
        "type": "string",
        "description": "Filing vehicle identifier (e.g., 'Motion to Modify Custody')",
        "examples": ["Motion to Modify Custody", "PPO Response", "COA Application"]
      },
      "lane": {
        "type": "string",
        "enum": ["A", "B", "C", "D", "E", "F"],
        "description": "Case lane: A=custody, B=housing, C=convergence, D=PPO, E=misconduct, F=appellate"
      },
      "strict": {
        "type": "boolean",
        "default": true,
        "description": "If true, requires ALL fields filled (no placeholders). If false, allows [VERIFY] placeholders."
      }
    },
    "required": ["vehicle_name", "lane"],
    "additionalProperties": false
  }
}
```

**Schema Rules:**
| Rule | Why |
|------|-----|
| Always set `"additionalProperties": false` | Prevents LLM from inventing parameters |
| Use `"enum"` for known value sets | Constrains LLM to valid options |
| Add `"description"` to EVERY property | LLM needs per-field guidance |
| Use `"examples"` for complex string fields | Shows LLM the expected format |
| Set `"default"` for optional parameters | Documents expected behavior |
| Use `"required"` array explicitly | LLM needs to know what's mandatory |

### Phase M2-3: Tool Naming Convention

All LitigationOS MCP tools follow the `litigation_` prefix convention:

```
Pattern: litigation_{category}_{action}

Examples:
  litigation_search              (core — search documents)
  litigation_filing_readiness    (filing — check readiness)
  litigation_evidence_chain      (evidence — trace chain of custody)
  litigation_deadline_dashboard  (deadline — view upcoming deadlines)
  litigation_prefiling_qa        (qa — pre-filing quality sweep)
  litigation_system_health       (system — health check)
```

### Phase M2-4: Return Value Patterns

```python
# Pattern A: Markdown table (for structured results)
def litigation_search(query: str) -> str:
    rows = db.execute("SELECT ...").fetchall()
    lines = ["| ID | Score | Content |", "|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['id']} | {r['score']} | {r['content'][:80]} |")
    return "\n".join(lines)

# Pattern B: Structured report (for analysis results)
def litigation_filing_readiness(vehicle: str) -> str:
    return f"""## Filing Readiness: {vehicle}
**Status:** {'GO ✅' if ready else 'NO-GO ❌'}
**Deficiencies:** {deficiencies or 'None'}
**Evidence Count:** {count}
**Missing:** {missing}"""

# Pattern C: JSON (for machine-consumable results)
def litigation_get_stats() -> str:
    return json.dumps(stats, indent=2)
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE M3: FASTMCP PYTHON
## ═══════════════════════════════════════════════════════════════
*Absorbs: fastmcp-python, pydantic-integration*

### Phase M3-1: FastMCP Server Setup

```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="litigation-context-mcp",
    version="2.0.0",
    description="LitigationOS litigation intelligence MCP server. "
                "45 tools across 9 categories for evidence, filings, "
                "deadlines, analysis, and QA."
)
```

### Phase M3-2: Tool Registration with Type Hints

FastMCP uses Python type hints to auto-generate JSON Schema:

```python
from pydantic import BaseModel, Field
from enum import Enum

class CaseLane(str, Enum):
    CUSTODY = "A"
    HOUSING = "B"
    CONVERGENCE = "C"
    PPO = "D"
    MISCONDUCT = "E"
    APPELLATE = "F"

class SearchRequest(BaseModel):
    query: str = Field(description="FTS5 search query")
    lane: CaseLane | None = Field(default=None, description="Filter by case lane")
    limit: int = Field(default=20, ge=1, le=100, description="Max results")

@mcp.tool()
def litigation_search(request: SearchRequest) -> str:
    """Full-text search across all litigation documents and evidence."""
    conn = get_db_connection()
    # ... implementation
```

### Phase M3-3: Pydantic Model Patterns

LitigationOS uses Pydantic v2 models for all MCP tool inputs and outputs:

```python
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Literal

class DeadlineCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    due_date: date
    lane: Literal["A", "B", "C", "D", "E", "F"]
    priority: Literal["critical", "high", "medium", "low"] = "medium"
    court: str | None = None
    notes: str | None = None

    @field_validator("title")
    @classmethod
    def no_placeholder_in_title(cls, v: str) -> str:
        if "[" in v and "]" in v:
            raise ValueError("Deadline title must not contain placeholders")
        return v

class DeadlineResponse(BaseModel):
    id: int
    title: str
    due_date: date
    days_remaining: int
    urgency: Literal["overdue", "critical", "soon", "normal"]
    lane: str
```

### Phase M3-4: Resource Registration

```python
@mcp.resource("litigation://stats")
def get_litigation_stats() -> str:
    """Current database statistics — table counts, evidence totals, filing status."""
    row = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM documents) AS doc_count,
            (SELECT COUNT(*) FROM evidence_quotes) AS evidence_count,
            (SELECT COUNT(*) FROM claims) AS claim_count,
            (SELECT COUNT(*) FROM deadlines WHERE status = 'active') AS active_deadlines
    """).fetchone()
    return json.dumps(dict(row))

@mcp.resource("litigation://deadline/{deadline_id}")
def get_deadline(deadline_id: int) -> str:
    """Get a specific deadline by ID."""
    ...
```

### Phase M3-5: Prompt Templates

```python
@mcp.prompt()
def filing_review_prompt(vehicle_name: str, lane: str) -> str:
    """Generate a structured prompt for reviewing a filing before submission."""
    return f"""Review the following filing for court submission readiness:

Filing: {vehicle_name}
Lane: {lane}
Court: 14th Judicial Circuit, Muskegon County

Checklist:
1. All citations verified against authority_chains table?
2. No hallucinated case names or statute numbers?
3. Party names match verified identities?
4. All placeholders resolved (no [ANDREW_REQUIRED])?
5. Cross-lane contamination check passed?
6. Bates stamps sequential and complete?
7. Exhibit index matches exhibit pack?
"""
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE M4: RESOURCE MANAGEMENT
## ═══════════════════════════════════════════════════════════════
*Absorbs: mcp-resource-manager*

### Phase M4-1: Resource URI Patterns

```
Static resources (fixed URIs):
  litigation://stats                    → Database statistics
  litigation://health                   → System health report
  litigation://lanes                    → Case lane summary

Dynamic resources (parameterized URIs):
  litigation://deadline/{id}            → Specific deadline
  litigation://document/{doc_id}        → Specific document
  litigation://evidence/{atom_id}       → Specific evidence atom
  litigation://lane/{lane_letter}       → Lane-specific summary

Template resources (discovery):
  litigation://search?q={query}         → Search results
  litigation://filing/{vehicle_name}    → Filing status
```

### Phase M4-2: Connection Lifecycle

```python
import sqlite3
from contextlib import contextmanager

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

@contextmanager
def managed_db():
    """Context manager enforcing WAL mode, busy_timeout, and cache settings."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")    # 32 MB
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")   # WAL protects durability
    try:
        yield conn
    finally:
        conn.close()
```

### Phase M4-3: PyMuPDF PDF Processing

LitigationOS uses PyMuPDF (fitz) for all PDF operations:

```python
import fitz  # PyMuPDF

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF with page markers."""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append(f"--- Page {i+1} ---\n{text}")
    doc.close()
    return "\n\n".join(pages)

def extract_pdf_metadata(pdf_path: str) -> dict:
    """Extract PDF metadata (title, author, dates, page count)."""
    doc = fitz.open(pdf_path)
    meta = doc.metadata
    meta["page_count"] = len(doc)
    meta["file_size_kb"] = os.path.getsize(pdf_path) // 1024
    doc.close()
    return meta

def ingest_pdf(pdf_path: str, lane: str) -> dict:
    """Full PDF ingestion: extract text, metadata, fingerprint, classify, store."""
    import hashlib
    text = extract_pdf_text(pdf_path)
    meta = extract_pdf_metadata(pdf_path)
    sha256 = hashlib.sha256(open(pdf_path, "rb").read()).hexdigest()

    with managed_db() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO documents
            (file_path, sha256, page_count, lane, extracted_text, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (pdf_path, sha256, meta["page_count"], lane, text, json.dumps(meta)))
        conn.commit()

    return {"status": "ingested", "sha256": sha256, "pages": meta["page_count"]}
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE M5: ERROR HANDLING
## ═══════════════════════════════════════════════════════════════
*Absorbs: mcp-error-handling*

### Phase M5-1: MCP Error Codes

| Code | Name | When to Use |
|------|------|------------|
| `-32600` | Invalid Request | Malformed JSON-RPC request |
| `-32601` | Method Not Found | Unknown tool name |
| `-32602` | Invalid Params | Arguments fail JSON Schema validation |
| `-32603` | Internal Error | Server-side exception (DB error, file not found) |
| `-32000` | Tool Execution Error | Tool logic failed (custom application error) |

### Phase M5-2: Graceful Error Responses

```python
from fastmcp.exceptions import ToolError

@mcp.tool()
def litigation_evidence_chain(atom_id: str) -> str:
    """Trace the chain of custody for an evidence atom."""
    try:
        with managed_db() as conn:
            row = conn.execute(
                "SELECT * FROM evidence_quotes WHERE atom_id = ?",
                (atom_id,)
            ).fetchone()

            if not row:
                # Informative error — helps LLM self-correct
                raise ToolError(
                    f"Evidence atom '{atom_id}' not found in evidence_quotes table. "
                    f"Use litigation_search to find valid atom IDs first."
                )

            return format_evidence_chain(row)

    except sqlite3.OperationalError as e:
        if "database is locked" in str(e):
            raise ToolError(
                "Database is locked (SQLITE_BUSY). Another process is writing. "
                "Retry in 5 seconds. If persistent, check db_lock_manager connections."
            )
        raise ToolError(f"Database error: {e}")
```

### Phase M5-3: Validation Before Execution

```python
@mcp.tool()
def litigation_filing_assemble(vehicle_name: str, lane: str) -> str:
    """Assemble a court-ready filing package."""
    # Pre-flight validation
    errors = []

    if lane not in ("A", "B", "C", "D", "E", "F"):
        errors.append(f"Invalid lane '{lane}'. Must be A-F.")

    with managed_db() as conn:
        # Verify vehicle exists
        row = conn.execute(
            "SELECT COUNT(*) FROM filing_readiness WHERE vehicle_name = ?",
            (vehicle_name,)
        ).fetchone()
        if row[0] == 0:
            errors.append(f"Vehicle '{vehicle_name}' not found in filing_readiness table.")

    if errors:
        raise ToolError("Validation failed:\n" + "\n".join(f"- {e}" for e in errors))

    # Proceed with assembly...
```

### Phase M5-4: SQLite-Specific Error Handling

```python
# ALWAYS verify schema before querying a table for the first time
def safe_query(conn, table_name: str, query: str, params=()) -> list:
    """Query with schema verification to prevent column-name crashes."""
    # Step 1: Verify table exists
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    if table_name not in tables:
        raise ToolError(f"Table '{table_name}' does not exist in litigation_context.db")

    # Step 2: Get actual columns
    columns = [r[1] for r in conn.execute(f"PRAGMA table_info({table_name})").fetchall()]

    # Step 3: Execute query
    try:
        return conn.execute(query, params).fetchall()
    except sqlite3.OperationalError as e:
        raise ToolError(
            f"Query failed on {table_name}: {e}\n"
            f"Available columns: {', '.join(columns)}"
        )
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE M6: TESTING MCP TOOLS
## ═══════════════════════════════════════════════════════════════
*Absorbs: mcp-testing*

### Phase M6-1: Unit Testing with pytest

```python
import pytest
from unittest.mock import patch, MagicMock

def test_litigation_search_returns_markdown_table():
    """Tool must return a markdown table with expected columns."""
    result = litigation_search(SearchRequest(query="withholding", limit=5))
    assert "| ID |" in result
    assert "|---|" in result

def test_litigation_search_empty_query():
    """Empty query should return helpful error, not crash."""
    with pytest.raises(ToolError, match="query must not be empty"):
        litigation_search(SearchRequest(query="", limit=5))

def test_litigation_search_lane_filter():
    """Lane filter should restrict results to specified lane."""
    result = litigation_search(SearchRequest(query="custody", lane=CaseLane.CUSTODY))
    # All results should be Lane A
    for line in result.split("\n")[2:]:  # Skip header rows
        if line.strip() and line.startswith("|"):
            assert "| A |" in line or line.startswith("|---")
```

### Phase M6-2: Integration Testing

```python
@pytest.fixture
def test_db(tmp_path):
    """Create a test database with known data."""
    db_path = tmp_path / "test_litigation.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, content TEXT, lane TEXT)")
    conn.execute("INSERT INTO documents VALUES (1, 'Custody withholding evidence', 'A')")
    conn.execute("INSERT INTO documents VALUES (2, 'PPO violation report', 'D')")
    conn.commit()
    conn.close()
    return str(db_path)

def test_full_tool_lifecycle(test_db):
    """Test tool from request through DB query to response."""
    with patch("tools.core.DB_PATH", test_db):
        result = litigation_search(SearchRequest(query="withholding"))
        assert "withholding" in result.lower()
        assert "custody" in result.lower()
```

### Phase M6-3: MCP Protocol Testing

```python
import json
from fastmcp.testing import MockTransport

async def test_mcp_tool_call():
    """Test the full MCP protocol flow."""
    transport = MockTransport(mcp)

    # Send initialize
    response = await transport.send({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}}
    })
    assert "capabilities" in response["result"]

    # Send tool call
    response = await transport.send({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "litigation_search",
            "arguments": {"query": "withholding", "limit": 5}
        }
    })
    assert response["result"]["content"][0]["type"] == "text"
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE M7: MULTI-TRANSPORT
## ═══════════════════════════════════════════════════════════════
*Absorbs: mcp-multi-transport*

### Phase M7-1: Transport Comparison

| Transport | Protocol | Use Case | LitigationOS Usage |
|-----------|----------|----------|-------------------|
| **stdio** | stdin/stdout pipes | CLI tools, Copilot CLI | **Primary** — both MCP servers |
| **SSE** | Server-Sent Events over HTTP | Web clients, remote access | Future: web dashboard |
| **Streamable HTTP** | HTTP POST with streaming | Scalable deployments | Future: multi-user |

### Phase M7-2: stdio Configuration (Primary)

LitigationOS MCP servers run over stdio, configured in `.copilot/mcp-config.json` or `.vscode/mcp.json`:

```json
{
  "mcpServers": {
    "litigation-context": {
      "command": "python",
      "args": ["-m", "litigation_context_mcp"],
      "cwd": "C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\mcp_server",
      "env": {
        "PYTHONUTF8": "1",
        "LITIGATION_DB": "C:\\Users\\andre\\LitigationOS\\litigation_context.db"
      }
    },
    "command-runner": {
      "command": "python",
      "args": ["-m", "command_runner"],
      "cwd": "C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\mcp_server",
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

### Phase M7-3: Transport Selection Guide

```
Is the client on the same machine?
├─ YES → stdio (simplest, fastest, no network)
│   └─ This is LitigationOS's primary mode
│
└─ NO → Does the client need streaming responses?
    ├─ YES → SSE (Server-Sent Events)
    │   └─ Good for: web dashboards, real-time updates
    │
    └─ NO → Streamable HTTP
        └─ Good for: RESTful integrations, load-balanced deployments
```

---

## ═══════════════════════════════════════════════════════════════
## MODULE M8: LITIGATIONOS MCP INTEGRATION
## ═══════════════════════════════════════════════════════════════
*Absorbs: litigation-mcp-integration*

### Phase M8-1: litigation-context MCP — 45 Tools, 9 Categories

| Category | Count | Tools | Key DB Tables |
|----------|-------|-------|---------------|
| **Core** | 10 | `scan_drives`, `ingest_pdf`, `bulk_ingest`, `search` (FTS5), `list_documents`, `get_document`, `get_stats`, `upcoming_deadlines`, `filing_search`, `evidence_lookup` | `documents`, `evidence_quotes`, `claims` |
| **Filing** | 8 | `filing_readiness`, `filing_validate`, `filing_assemble`, `efiling_prep`, `brief_compliance`, `placeholder_scan`, `placeholder_resolve`, `filing_export` | `filing_readiness`, `claims`, `authority_chains` |
| **Evidence** | 7 | `evidence_chain`, `evidence_gaps`, `evidence_link`, `evidence_authenticate`, `bates_assign`, `exhibit_index`, `evidence_timeline` | `evidence_quotes`, `documents`, `atoms` |
| **Deadline** | 5 | `deadline_dashboard`, `deadline_ics`, `deadline_urgency`, `deadline_add`, `deadline_update` | `deadlines` |
| **Analysis** | 5 | `authority_index`, `citation_graph`, `impeachment_search`, `contradiction_find`, `judicial_bias_scan` | `authority_chains`, `judicial_findings`, `contradictions` |
| **QA** | 4 | `prefiling_qa`, `qa_sweep`, `signature_check`, `service_check` | All tables (cross-cutting) |
| **Backup** | 3 | `backup_create`, `backup_version`, `backup_report` | `backup_log` |
| **Calendar** | 2 | `calendar_generate`, `calendar_sync` | `deadlines`, `docket_events` |
| **System** | 1 | `system_health` | `sqlite_master` (schema introspection) |

### Phase M8-2: command-runner MCP — 5 Execution Tools

The command-runner MCP replaces PowerShell for non-interactive commands. **Zero pipe consumption.**

| Tool | Signature | Purpose |
|------|-----------|---------|
| `exec_command(command: str)` | Any shell command | General execution — replaces `powershell` tool |
| `exec_python(script_path: str, args: str)` | Python script execution | Shadow-module-safe (sets CWD to script dir) |
| `exec_git(args: str)` | Git operations | Auto-adds `--no-pager` |
| `exec_pipeline_phase(phase: str)` | Pipeline phase execution | Runs specific pipeline phases |
| `system_status()` | No arguments | System health without any shell |

**Why command-runner is critical:**
```
PowerShell tool  → Creates OS session → 3 SHARED pipes → EAGAIN risk
command-runner   → subprocess.run()   → 0 shared pipes → ZERO EAGAIN risk

PowerShell tool  → Limited to ~50 per session → exhausts pool
command-runner   → Unlimited executions → never exhausts

ALWAYS prefer command-runner over powershell for non-interactive commands.
```

### Phase M8-3: SQLite Connection Patterns

All MCP tools connecting to `litigation_context.db` MUST follow the three-tier strategy:

```python
# TIER 1 — Multiplexer (connection_multiplexer.py)
# For high-throughput pipeline operations
PRAGMA mmap_size = 12884901888;   # 12 GB
PRAGMA cache_size = -131072;       # 128 MB
PRAGMA busy_timeout = 180000;      # 180 seconds

# TIER 2 — Standard (db_lock_manager.py, MCP db.py)
# For MCP tool queries and normal operations
PRAGMA busy_timeout = 60000;       # 60 seconds
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -32000;        # 32 MB
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;

# TIER 3 — Simple (one-off scripts)
PRAGMA busy_timeout = 30000;       # 30 seconds
PRAGMA journal_mode = WAL;
```

**Consolidate COUNT(*) calls — NEVER do N separate round-trips:**

```python
# CORRECT — single query, multiple counts
row = conn.execute("""
    SELECT
        (SELECT COUNT(*) FROM documents) AS doc_count,
        (SELECT COUNT(*) FROM evidence_quotes) AS evidence_count,
        (SELECT COUNT(*) FROM claims) AS claim_count,
        (SELECT COUNT(*) FROM deadlines WHERE status = 'active') AS deadline_count
""").fetchone()

# WRONG — 4 separate queries (4× slower)
doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
ev_count = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
# ... etc
```

### Phase M8-4: Adding a New Tool to litigation-context MCP

Step-by-step process for extending the MCP server:

```
1. DESIGN: Write the tool description FIRST (see M2-1)
   - What does it do?
   - When should the LLM call it?
   - What arguments does it take?
   - What does it return?

2. MODEL: Create Pydantic input/output models (see M3-3)
   - Validate all inputs
   - Use enums for constrained values
   - Add field descriptions

3. IMPLEMENT: Write the tool function
   - Use managed_db() for DB access
   - Verify schema with PRAGMA table_info before querying
   - Return markdown tables or structured reports
   - Handle errors gracefully (see M5)

4. REGISTER: Add @mcp.tool() decorator
   - Ensure name follows litigation_{category}_{action} convention
   - Description is actionable and specific

5. TEST: Write unit + integration tests (see M6)
   - Test happy path
   - Test error cases
   - Test with empty/null inputs
   - Test with the actual litigation_context.db schema

6. CONFIGURE: Update MCP config if needed
   - Usually not needed for new tools (auto-discovered)
   - Update documentation if tool count changes
```

---

## ═══════════════════════════════════════════════════════════════
## IQ BOOST PATTERNS
## ═══════════════════════════════════════════════════════════════

### Pattern 1: Description Engineering
Write tool descriptions as if briefing a junior attorney. Be specific about WHEN to use the tool, WHAT it returns, and HOW to interpret results. The LLM's tool selection accuracy scales directly with description quality.

### Pattern 2: Schema-Driven Development
Define the JSON Schema BEFORE writing implementation code. The schema IS the contract. Implementation is just fulfillment. If you can't express the tool's interface in JSON Schema, the tool is too complex — decompose it.

### Pattern 3: Fail-Informative
Every error message should tell the caller HOW to fix the problem. "Not found" is useless. "Evidence atom 'X' not found — use litigation_search to find valid atom IDs" enables self-correction.

### Pattern 4: Zero-Pipe Architecture
The MCP server runs in its own process with its own pipes. Tools execute via subprocess.run() — completely outside the Copilot CLI pipe pool. This makes MCP tools immune to EAGAIN. Design accordingly — prefer MCP execution for ALL non-interactive commands.

### Pattern 5: Composable Tools
Design tools to be composed: `search → get_document → evidence_chain → filing_readiness`. Each tool returns enough context for the next tool in the chain. Never require the LLM to hold intermediate state — embed IDs and references in tool outputs.

---

## ═══════════════════════════════════════════════════════════════
## GLOBAL RULES (Apply to ALL MCP Development)
## ═══════════════════════════════════════════════════════════════

### ██ ANTI-HALLUCINATION ██

```
□ NEVER hardcode DB statistics — query dynamically with COUNT(*)
□ NEVER assume column names — run PRAGMA table_info() first
□ NEVER fabricate tool capabilities — test every tool before documenting
□ Tool descriptions must accurately reflect what the tool ACTUALLY does
```

### ██ DB-FIRST ██

```
□ Use managed_db() for ALL database access
□ Max 3 concurrent DB connections (enforced by db_lock_manager.py)
□ Consolidate COUNT(*) into single queries
□ Batch inserts with executemany — never row-by-row
□ Explicit column lists — never SELECT *
```

### ██ SECURITY ██

```
□ NEVER commit secrets (API keys, passwords) into MCP server code
□ NEVER expose file system paths outside the project directory
□ ALWAYS use parameterized queries (?) — never string concatenation
□ ALWAYS validate inputs against JSON Schema before execution
□ PII redaction for any data that leaves the local machine
```

### ██ PERFORMANCE ██

```
□ Add composite indexes for hot query patterns
□ Use FTS5 for text search (via adaptive_query_rewriter.py)
□ Cache frequently-accessed data (prefetch_cache.py)
□ Limit result sets — always include LIMIT in queries
□ Use WAL mode for concurrent read/write access
```

---

## ═══════════════════════════════════════════════════════════════
## APPENDIX A: COMPLETE TOOL REGISTRY
## ═══════════════════════════════════════════════════════════════

### litigation-context MCP (45 tools)

```
CORE (10):
  litigation_scan_drives          — Scan local drives for litigation files
  litigation_ingest_pdf           — Ingest a single PDF (extract, classify, store)
  litigation_bulk_ingest          — Batch ingest multiple files
  litigation_search               — FTS5 full-text search across all documents
  litigation_list_documents       — List documents with filters
  litigation_get_document         — Get full document by ID
  litigation_get_stats            — Database statistics dashboard
  litigation_upcoming_deadlines   — Next N deadlines by urgency
  litigation_filing_search        — Search filing vehicles
  litigation_evidence_lookup      — Quick evidence lookup by keyword

FILING (8):
  litigation_filing_readiness     — GO/NO-GO readiness check
  litigation_filing_validate      — Validate filing against court rules
  litigation_filing_assemble      — Assemble complete filing package
  litigation_efiling_prep         — Prepare for e-filing submission
  litigation_brief_compliance     — Check brief against page/word limits
  litigation_placeholder_scan     — Find unresolved placeholders
  litigation_placeholder_resolve  — Auto-resolve placeholders from DB
  litigation_filing_export        — Export filing to PDF/DOCX

EVIDENCE (7):
  litigation_evidence_chain       — Trace chain of custody
  litigation_evidence_gaps        — Identify evidence gaps per claim
  litigation_evidence_link        — Link evidence to claims
  litigation_evidence_authenticate— MRE 901/902 authentication check
  litigation_bates_assign         — Assign Bates stamp numbers
  litigation_exhibit_index        — Generate exhibit index
  litigation_evidence_timeline    — Build chronological evidence timeline

DEADLINE (5):
  litigation_deadline_dashboard   — Visual deadline dashboard
  litigation_deadline_ics         — Generate ICS calendar events
  litigation_deadline_urgency     — Urgency scoring for all deadlines
  litigation_deadline_add         — Add new deadline
  litigation_deadline_update      — Update existing deadline

ANALYSIS (5):
  litigation_authority_index      — Index of legal authorities cited
  litigation_citation_graph       — Citation relationship graph
  litigation_impeachment_search   — Find impeachment material
  litigation_contradiction_find   — Detect contradictions in testimony
  litigation_judicial_bias_scan   — Scan for judicial bias indicators

QA (4):
  litigation_prefiling_qa         — Pre-filing quality assurance sweep
  litigation_qa_sweep             — General QA sweep across all filings
  litigation_signature_check      — Verify signature blocks
  litigation_service_check        — Verify proof of service

BACKUP (3):
  litigation_backup_create        — Create timestamped backup
  litigation_backup_version       — Version a specific filing
  litigation_backup_report        — Backup status report

CALENDAR (2):
  litigation_calendar_generate    — Generate calendar from deadlines
  litigation_calendar_sync        — Sync with external calendar

SYSTEM (1):
  litigation_system_health        — Full system health check
```

### command-runner MCP (5 tools)

```
  exec_command(command)           — Any shell command (zero pipes)
  exec_python(script_path, args)  — Python script (shadow-safe)
  exec_git(args)                  — Git operations (--no-pager)
  exec_pipeline_phase(phase)      — Pipeline phase execution
  system_status()                 — System health (no args)
```

---

*OMEGA-MCP v2.0 — 13 skills forged into one MCP mastery system.*
*Design descriptions first. Schema is the contract. Test everything. Zero pipes.*
