---
name: OMEGA-ENGINEER
description: >-
  Use when writing, debugging, testing, refactoring, reviewing, or securing code in LitigationOS.
  Covers Python 3.12+ development, SQLite optimization, engine development patterns, security
  auditing, performance tuning, and code review. Coordinates the full engineering lifecycle from
  implementation through testing to production hardening. Enforces codebase conventions including
  shadow module safety, EAGAIN-safe execution, parameterized queries, and the Engine pattern.
category: discipline
version: "2.0.0"
triggers:
  - code
  - debug
  - test
  - refactor
  - review
  - security audit
  - build
  - fix
  - implement
  - engine
  - Python
  - pytest
  - SQL
  - optimize
  - performance
  - type hints
  - Pydantic
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: Pigors v Watson
dependencies:
  - OMEGA-ARCHITECT
  - OMEGA-SENTINEL
metadata:
  tier: META
  fused_skills: 67
  author: andrew-pigors + copilot-omega
  forge_date: 2026-03-21
---

# ⚙️ OMEGA-ENGINEER — Strategic Engineering Leadership

> **META TIER** — Coordinates OMEGA-CODE, OMEGA-DATA, and OMEGA-MCP implementation
> **Domain:** Code quality, testing, engines, debugging, security, performance, refactoring
> **Scope:** Every line of code written in LitigationOS meets this skill's standards
> **Principle:** Ship working code that is correct, tested, secure, and performant — in that order

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        OMEGA-ENGINEER v2.0                                  ║
║              67 Skills → 8 Strategic Areas → 1 Engineering Authority        ║
║                                                                             ║
║  SE1  Code Quality ─────────┐                                               ║
║  SE2  Testing Strategy ─────┤                                               ║
║  SE3  Engine Development ───┤→ UNIFIED ENGINEERING STANDARD                 ║
║  SE4  Bug Hunting ──────────┤        ↓                                      ║
║  SE5  Code Review ──────────┤   IMPLEMENTATION                              ║
║  SE6  Security Audit ───────┤        ↓                                      ║
║  SE7  Performance ──────────┤   VALIDATION → SHIP                           ║
║  SE8  Refactoring ──────────┘                                               ║
║                                                                             ║
║  Subordinates: OMEGA-CODE · OMEGA-DATA · OMEGA-MCP (implementation)         ║
║  Peers:        OMEGA-ARCHITECT · OMEGA-SENTINEL                             ║
║  Reports to:   OMEGA-ARCHITECT (structural decisions)                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

## Strategic Leadership Mission

OMEGA-ENGINEER is the **quality authority** for all code in LitigationOS. While OMEGA-ARCHITECT
designs the blueprint, OMEGA-ENGINEER ensures every brick is laid correctly. This means Python
that passes type checking, SQL that uses parameterized queries, tests that verify real behavior,
engines that follow the established pattern, and security practices that protect litigation data.

The engineer's priority stack is absolute and non-negotiable:
1. **Correctness** — Code does what it claims. No silent failures. No fabricated results.
2. **Tested** — Every behavior has a test. Regressions are caught before they ship.
3. **Secure** — No SQL injection, no PII leaks, no unvalidated input.
4. **Performant** — SQLite optimized, batch operations, appropriate indexes.
5. **Clean** — Readable, maintainable, documented where non-obvious.

---

## When to Apply

Use OMEGA-ENGINEER when:

- **Writing new code** — Python modules, engines, agents, scripts, tools
- **Fixing bugs** — Error trace analysis, shadow module conflicts, FK constraint failures
- **Writing tests** — pytest fixtures, DB mocking, coverage targets, edge cases
- **Reviewing code** — High signal-to-noise review focused on bugs, security, logic
- **Refactoring** — Safe transformations with backward compatibility and test coverage
- **Security auditing** — SQL injection, PII handling, input validation, file safety
- **Optimizing performance** — SQLite queries, batch operations, connection pooling
- **Building engines** — The LitigationOS engine pattern with DB table creation

Do NOT use OMEGA-ENGINEER when:
- Making architectural decisions → use OMEGA-ARCHITECT
- Monitoring system health → use OMEGA-SENTINEL
- Writing litigation filings → use OMEGA-LITIGATION-SUPREME
- Designing agent fleet structure → use OMEGA-ARCHITECT

---

## Decision Tree

```
                         ┌─────────────────────┐
                         │  Engineering Task    │
                         │     Received         │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
      ┌──────────────┐    ┌──────────────┐      ┌──────────────┐
      │ New Feature / │    │ Bug / Error  │      │ Maintenance  │
      │ Implementation│    │   Report     │      │ / Improve    │
      └──────┬───────┘    └──────┬───────┘      └──────┬───────┘
             │                   │                      │
             ▼                   ▼                      ▼
      ┌──────────────┐    ┌──────────────┐      ┌──────────────┐
      │ SE1: Quality  │    │ SE4: Debug   │      │ SE8: Refactor│
      │ SE2: Test     │    │ SE6: Sec Aud │      │ SE7: Perf    │
      │ SE3: Engine   │    │              │      │ SE5: Review  │
      └──────┬───────┘    └──────┬───────┘      └──────┬───────┘
             │                   │                      │
             └───────────────────┼──────────────────────┘
                                 ▼
                  ┌──────────────────────────┐
                  │ Validation Gate          │
                  │ □ Tests pass?            │
                  │ □ No security issues?    │
                  │ □ Performance acceptable?│
                  │ □ Conventions followed?  │
                  └─────────────┬────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              ┌──────────┐ ┌────────┐ ┌─────────┐
              │  Ship    │ │  Fix   │ │ Escalate│
              │  It      │ │  First │ │ to Arch │
              └──────────┘ └────────┘ └─────────┘
```

---

## SE1: Code Quality — Python 3.12+ Standards

### Mandatory Code Standards

```python
# 1. Type hints on ALL function signatures (no exceptions)
def score_evidence(
    claim_id: str,
    vehicle_name: str,
    weight: float = 1.0,
) -> dict[str, Any]:
    """Score evidence strength for a specific claim."""
    ...

# 2. Pydantic models for all structured data
from pydantic import BaseModel, Field

class FilingReadiness(BaseModel):
    vehicle_name: str = Field(..., description="Case lane identifier")
    status: str = Field(default="pending")
    score: float = Field(ge=0.0, le=1.0)
    missing_items: list[str] = Field(default_factory=list)

# 3. Explicit imports (never import *)
from pathlib import Path
from typing import Any, Optional

# 4. Context managers for resources
with managed_db() as conn:
    result = conn.execute("SELECT ...", (param,)).fetchall()

# 5. f-strings for formatting (never % or .format())
log.info(f"Processed {count} records for lane {lane}")
```

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Variables | `snake_case` | `claim_count`, `vehicle_name` |
| Functions | `snake_case` | `score_evidence()`, `run_phase()` |
| Classes | `PascalCase` | `EvidenceEngine`, `AgentResult` |
| Constants | `UPPER_SNAKE` | `MAX_RETRIES`, `DB_PATH` |
| DB tables | `snake_case` | `evidence_quotes`, `filing_readiness` |
| DB columns | `snake_case` | `vehicle_name`, `claim_id` |
| Files | `snake_case` | `evidence_engine.py`, `test_models.py` |
| Agents | `AgentNNNN` | `Agent0001`, `Agent9999` |

### Import Safety (Shadow Module Protection)

The repo root contains 22 shadow modules (`json.py`, `typing.py`, `tokenize.py`,
`numpy.py`, `pandas.py`, etc.) that mask Python stdlib/third-party modules.

**CRITICAL RULES:**
- NEVER set CWD to the repo root when running Python
- NEVER run `python -c "..."` from PowerShell (use temp .py files)
- Always use `safe_run()` or set CWD to the script's own directory
- Use the toolkit: `sspy`, `srun`, `spy` from `agent_profile.ps1`

```python
# CORRECT: Run from script's directory
import subprocess
subprocess.run(
    ["python", "my_script.py"],
    cwd=r"C:\Users\andre\LitigationOS\00_SYSTEM\pipeline"
)

# WRONG: Run from repo root (shadow modules will break imports)
subprocess.run(
    ["python", "my_script.py"],
    cwd=r"C:\Users\andre\LitigationOS"  # DANGER: json.py, typing.py
)
```

---

## SE2: Testing Strategy — pytest-First Development

### Test Infrastructure

```
Test location:     11_CODE/litigationos/tests/
Test runner:       python -m pytest tests/ -q
Test with cov:     python -m pytest tests/ --cov=litigationos
Single test:       python -m pytest tests/test_models.py::test_case -v
```

### Test Fixture Patterns

```python
# conftest.py — ALWAYS use temp DB, never production
import pytest
import sqlite3
from pathlib import Path

@pytest.fixture
def tmp_db(tmp_path: Path) -> Path:
    """Create a temporary SQLite database for testing."""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.close()
    return db_path

@pytest.fixture
def sample_evidence(tmp_db: Path) -> Path:
    """Seed a test DB with sample evidence records."""
    conn = sqlite3.connect(str(tmp_db))
    conn.execute("""
        CREATE TABLE evidence_quotes (
            id INTEGER PRIMARY KEY,
            vehicle_name TEXT,
            quote_text TEXT,
            source_file TEXT
        )
    """)
    conn.executemany(
        "INSERT INTO evidence_quotes (vehicle_name, quote_text, source_file) VALUES (?, ?, ?)",
        [
            ("A", "Defendant denied visitation on 2024-03-15", "exhibit_001.pdf"),
            ("A", "Child expressed desire to see father", "exhibit_002.pdf"),
        ],
    )
    conn.commit()
    conn.close()
    return tmp_db
```

### Test Quality Rules

1. **Every test verifies REAL behavior** — No assertions on mocked return values that
   you just set up. Test the transformation, not the scaffolding.
2. **Every new feature gets tests FIRST** — Write the test, watch it fail, implement, watch it pass.
3. **Edge cases are mandatory** — Empty inputs, None values, Unicode, very large inputs.
4. **Tests are independent** — No test depends on another test's side effects.
5. **No production DB in tests** — EVER. Use `tmp_db` fixture or `tmp_path`.
6. **Meaningful assertion messages** — `assert count == 5, f"Expected 5 evidence items, got {count}"`

### Anti-Pattern: Fabricated Assertions

```python
# WRONG — This tests nothing real, just confirms the mock
mock_db.return_value = [{"count": 42}]
result = get_count(mock_db)
assert result == 42  # You just tested that Python returns what you told it to

# CORRECT — This tests actual transformation logic
def test_score_calculation(tmp_db):
    """Verify scoring weights evidence recency and severity."""
    seed_evidence(tmp_db, [
        {"date": "2024-01-01", "severity": "high"},
        {"date": "2023-01-01", "severity": "low"},
    ])
    engine = ScoringEngine(tmp_db)
    scores = engine.run()
    assert scores[0] > scores[1], "Recent high-severity should score higher"
```

---

## SE3: Engine Development — The LitigationOS Engine Pattern

### Canonical Engine Structure

Every engine in LitigationOS follows this pattern:

```python
"""Engine: [Name] — [one-line description].

Creates table(s): [table_name]
Reads from: [source_tables]
Reports: [what it generates]
"""
from pathlib import Path
import sqlite3
from typing import Any

class ExampleEngine:
    """Processes [domain] and writes results to [table]."""

    TABLE_NAME = "example_results"
    CREATE_SQL = """
        CREATE TABLE IF NOT EXISTS example_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_name TEXT NOT NULL,
            result_text TEXT,
            score REAL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """
    INDEX_SQL = """
        CREATE INDEX IF NOT EXISTS idx_example_vehicle
            ON example_results(vehicle_name)
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create output table and indexes if they don't exist."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute(self.CREATE_SQL)
            conn.execute(self.INDEX_SQL)
            conn.commit()

    def run(self, vehicle_name: str | None = None) -> dict[str, Any]:
        """Execute the engine for a specific lane or all lanes."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout=60000")
            conn.execute("PRAGMA cache_size=-32000")

            # Query source data
            if vehicle_name:
                rows = conn.execute(
                    "SELECT * FROM source_table WHERE vehicle_name = ?",
                    (vehicle_name,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM source_table").fetchall()

            # Process and write results
            results = self._process(rows)
            self._write_results(conn, results)

            return {
                "status": "ok",
                "processed": len(rows),
                "results": len(results),
            }

    def _process(self, rows: list[sqlite3.Row]) -> list[tuple]:
        """Core processing logic — override in subclasses."""
        ...

    def _write_results(self, conn: sqlite3.Connection, results: list[tuple]) -> None:
        """Batch insert results using executemany."""
        conn.executemany(
            f"INSERT OR REPLACE INTO {self.TABLE_NAME} "
            "(vehicle_name, result_text, score) VALUES (?, ?, ?)",
            results,
        )
        conn.commit()

    def report(self, vehicle_name: str | None = None) -> str:
        """Generate a human-readable report of results."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            if vehicle_name:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {self.TABLE_NAME} WHERE vehicle_name = ?",
                    (vehicle_name,),
                ).fetchone()[0]
            else:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {self.TABLE_NAME}"
                ).fetchone()[0]
            return f"{self.TABLE_NAME}: {count} results"
```

### Engine Checklist

When building a new engine:

- [ ] Follows the canonical structure above
- [ ] Creates its own table(s) with `IF NOT EXISTS`
- [ ] Indexes on `vehicle_name` and any common filter columns
- [ ] Uses `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=60000`
- [ ] Uses `executemany` for batch inserts (never row-by-row)
- [ ] Uses parameterized queries (`?` placeholders, never f-strings in SQL)
- [ ] Returns structured results dict with `status` and counts
- [ ] Has a `report()` method for human-readable output
- [ ] Has corresponding test file in `tests/`
- [ ] Docstring specifies tables created and tables read

---

## SE4: Bug Hunting — Systematic Debugging

### Debugging Protocol

```
STEP 1: REPRODUCE — Get the exact error message and stack trace
STEP 2: ISOLATE — Narrow down to the specific module/function/line
STEP 3: HYPOTHESIZE — Form a theory about the root cause
STEP 4: VERIFY — Test the hypothesis with targeted investigation
STEP 5: FIX — Make the minimal correct change
STEP 6: TEST — Write a regression test that would have caught this bug
STEP 7: REVIEW — Check for the same bug pattern elsewhere in the codebase
```

### Common LitigationOS Bug Patterns

| Bug Pattern | Symptoms | Root Cause | Fix |
|-------------|----------|------------|-----|
| Shadow module | `ImportError`, wrong module loaded | CWD is repo root | Set CWD to script dir |
| Column mismatch | `OperationalError: no such column` | Schema evolved | `PRAGMA table_info()` first |
| EAGAIN | `write EAGAIN`, invalid shell | Too many shared pipes | Follow EAGAIN protocol |
| FK constraint | `FOREIGN KEY constraint failed` | Missing parent row | Verify FK targets exist |
| Encoding | `UnicodeDecodeError` | Windows files without UTF-8 | `errors='replace'` |
| Stale stats | Wrong counts in reports | Hardcoded numbers | Always query DB live |

### Shadow Module Diagnostic

```python
# Quick check: which module is actually loaded?
import json
print(f"json loaded from: {json.__file__}")
# If this prints a repo root path → shadow module is active → DANGER

# Full audit (22 known shadows in repo root):
# json.py, typing.py, tokenize.py, numpy.py, pandas.py,
# collections.py, io.py, os.py, re.py, sys.py, ...
```

---

## SE5: Code Review — High Signal, Zero Noise

### Review Focus (ONLY these matter)

1. **Bugs** — Logic errors, off-by-one, null dereferences, unhandled exceptions
2. **Security** — SQL injection, PII exposure, unvalidated input, unsafe file ops
3. **Logic errors** — Wrong conditions, missing edge cases, incorrect calculations
4. **Data integrity** — Missing transactions, race conditions, inconsistent state
5. **Convention violations** — Only when they could cause future bugs

### Review Anti-Focus (NEVER comment on these)

- Style preferences (already enforced by linters)
- Variable naming (unless genuinely confusing)
- Comment density (unless code is truly incomprehensible)
- Import order (tools handle this)
- Line length (formatters handle this)

### Review Template

```
## [BUG/SECURITY/LOGIC/DATA] — file.py:NN

**Issue:** [One sentence describing the problem]
**Impact:** [What breaks if this ships]
**Fix:** [Specific code change needed]
**Test:** [How to verify the fix]
```

---

## SE6: Security Audit — Litigation Data Protection

### SQL Injection Prevention (ZERO TOLERANCE)

```python
# CORRECT — Parameterized query
conn.execute(
    "SELECT * FROM claims WHERE vehicle_name = ? AND status = ?",
    (vehicle_name, status),
)

# WRONG — String interpolation (SQL injection vector)
conn.execute(f"SELECT * FROM claims WHERE vehicle_name = '{vehicle_name}'")

# WRONG — String concatenation
conn.execute("SELECT * FROM claims WHERE vehicle_name = '" + vehicle_name + "'")

# WRONG — .format()
conn.execute("SELECT * FROM claims WHERE vehicle_name = '{}'".format(vehicle_name))
```

### PII Handling Rules

- Child's name: Use **L.D.W.** (initials only) per MCR 8.119(H) — NEVER full name
- SSNs: Never store, never log, redact on sight
- Financial data: Encrypt at rest in DB, redact in logs
- Addresses: Include in filings only when legally required
- Phone/email: Verify party identity table before using

### File Operation Safety

```python
# CORRECT — Safe path handling
from pathlib import Path

target = Path(base_dir) / user_input
if not target.resolve().is_relative_to(Path(base_dir).resolve()):
    raise ValueError("Path traversal attempt detected")

# CORRECT — Move to I:\ for dedup (never delete)
import shutil
shutil.move(str(source), str(dedup_dir / source.name))

# WRONG — Hard delete (NEVER for litigation files)
os.remove(filepath)  # FORBIDDEN
Path(filepath).unlink()  # FORBIDDEN
```

---

## SE7: Performance — SQLite Optimization Patterns

### Connection Setup (MANDATORY PRAGMAs)

```python
def get_optimized_connection(db_path: str) -> sqlite3.Connection:
    """Standard optimized connection for LitigationOS."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA cache_size=-32000")     # 32 MB
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")    # WAL protects durability
    conn.row_factory = sqlite3.Row
    return conn
```

### Batch Operations (10-100x faster)

```python
# CORRECT — executemany for batch inserts
rows = [(r["col1"], r["col2"]) for r in source_data]
conn.executemany(
    "INSERT OR IGNORE INTO target (col1, col2) VALUES (?, ?)",
    rows,
)
conn.commit()

# WRONG — Row-by-row insert in a loop (10-100x slower)
for r in source_data:
    conn.execute("INSERT INTO target (col1, col2) VALUES (?, ?)", (r["col1"], r["col2"]))
    conn.commit()  # Committing per row is catastrophically slow
```

### Consolidated COUNT Queries

```python
# CORRECT — Single round-trip for multiple counts
row = conn.execute("""
    SELECT
        (SELECT COUNT(*) FROM evidence_quotes) AS evidence_count,
        (SELECT COUNT(*) FROM claims) AS claims_count,
        (SELECT COUNT(*) FROM deadlines WHERE status = 'active') AS active_deadlines
""").fetchone()

# WRONG — Three separate queries (3x latency)
ev_count = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
cl_count = conn.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
dl_count = conn.execute("SELECT COUNT(*) FROM deadlines WHERE status = 'active'").fetchone()[0]
```

### Index Strategy

```sql
-- Single-column for simple lookups
CREATE INDEX IF NOT EXISTS idx_claims_vehicle
    ON claims(vehicle_name);

-- Composite for multi-column WHERE clauses (column order matters)
CREATE INDEX IF NOT EXISTS idx_evidence_quotes_vehicle_claim
    ON evidence_quotes(vehicle_name, claim_id);

-- Covering index for hot queries (avoids table lookup)
CREATE INDEX IF NOT EXISTS idx_deadlines_active
    ON deadlines(vehicle_name, status, due_date_iso)
    WHERE status = 'active';
```

### FTS5 for Text Search (NEVER use LIKE '%term%' on large tables)

```python
# Use adaptive_query_rewriter.py to auto-convert LIKE → FTS5
from adaptive_query_rewriter import rewrite
optimized_sql = rewrite("SELECT * FROM documents WHERE content LIKE '%disqualification%'")
# Returns FTS5 MATCH query instead
```

---

## SE8: Refactoring — Safe Transformations

### Refactoring Protocol

```
STEP 1: Write characterization tests for current behavior
STEP 2: Run tests — they must all pass (baseline)
STEP 3: Make ONE refactoring transformation
STEP 4: Run tests — they must still all pass
STEP 5: Repeat steps 3-4 until refactoring is complete
STEP 6: Review for missed edge cases
STEP 7: Verify no regressions in production-adjacent behavior
```

### Safe Refactoring Patterns

| Pattern | When | Risk Level |
|---------|------|-----------|
| Rename variable | Anytime | Low (IDE handles references) |
| Extract function | Long methods (>30 lines) | Low |
| Extract class | God classes with multiple responsibilities | Medium |
| Change function signature | Adding/removing params | Medium (check all callers) |
| Move module | Wrong directory | High (update all imports) |
| Change DB schema | Column rename/add/drop | High (migration required) |

### Backward Compatibility Rules

- **Adding** a function parameter? Give it a default value.
- **Renaming** a function? Keep the old name as an alias for 1 release.
- **Changing** DB schema? Never DROP columns — add new, deprecate old.
- **Moving** a module? Leave a re-export stub at the old location.

---

## Anti-Patterns to Flag (IMMEDIATE REJECTION in code review)

| Anti-Pattern | Why It's Dangerous | Correct Alternative |
|-------------|-------------------|---------------------|
| `SELECT *` in hot paths | Wastes I/O, breaks on schema change | Explicit column list |
| Row-by-row INSERT in loops | 10-100x slower than executemany | `executemany()` |
| Hardcoded DB statistics | Stale within hours | Always query DB live |
| Missing PRAGMAs on connection | Slow queries, lock contention | Standard PRAGMA block |
| `python -c "..."` in PowerShell | Quote escaping breaks everything | Temp .py file |
| CWD set to repo root | Shadow modules break imports | Script's own directory |
| `os.remove()` on litigation files | Destroys evidence chain | `shutil.move()` to I:\ |
| String interpolation in SQL | SQL injection vulnerability | Parameterized queries |
| Fabricated test assertions | Tests prove nothing | Test real transformations |
| Missing `busy_timeout` | `SQLITE_BUSY` under concurrency | `PRAGMA busy_timeout=60000` |

---

## IQ Boost Patterns (MANDATORY for all engineering work)

### 1. Chain-of-Thought

Before writing any code:
```
THINK: What is the exact requirement?
THINK: What existing code does something similar?
THINK: What could go wrong (edge cases, errors, concurrency)?
THINK: What's the simplest correct implementation?
CODE:  Write it.
TEST:  Verify it.
```

### 2. Self-Reflection

After writing code, before committing:
```
CHECK: Does this follow the Engine pattern (if applicable)?
CHECK: Are all SQL queries parameterized?
CHECK: Is there a test for the happy path AND error paths?
CHECK: Would a future developer understand this without context?
CHECK: Does this respect EAGAIN limits?
```

### 3. Anti-Hallucination

Every engineering claim must be grounded:
```
VERIFY: Run PRAGMA table_info() before writing queries against a table
VERIFY: Run existing tests before and after changes
VERIFY: Check actual error messages, not assumed ones
VERIFY: Confirm import paths exist before referencing them
VERIFY: Count actual rows, not estimated counts
```

### 4. Cross-Skill Fusion

When engineering work crosses boundaries:
```
DETECT: Does this need a new DB table? → Invoke OMEGA-DATA
DETECT: Does this need a new MCP tool? → Invoke OMEGA-MCP
DETECT: Does this change architecture? → Escalate to OMEGA-ARCHITECT
DETECT: Does this affect monitoring? → Notify OMEGA-SENTINEL
DETECT: Does this need security review? → Invoke OMEGA-SECURITY
```

### 5. Adaptive Depth

Scale engineering effort to task complexity:
```
SIMPLE (typo fix): Fix, test, ship.
MEDIUM (new function): Design, test, implement, test, review.
COMPLEX (new engine): Architecture review, full test suite, security audit,
  performance benchmarks, documentation, staged rollout.
```

---

## Subordinate Skills Coordinated

### Direct Reports (OMEGA-ENGINEER coordinates these)

| Skill | Source Skills | When Invoked |
|-------|-------------|--------------|
| **OMEGA-CODE** | python-omega-engine, python-pro, clean-code, python-anti-patterns, python-testing-patterns, python-type-safety, tdd-workflows-*, debugging-*, refactor-* | All Python development, testing, debugging |
| **OMEGA-DATA** | sql-pro, sql-optimization-patterns, database-*, sqlite, FTS5 | Database queries, schema changes, optimization |
| **OMEGA-MCP** (impl) | mcp-builder, tool-design, fastapi-pro | MCP tool implementation (not design — that's ARCHITECT) |

### Peer Coordination

| Peer Skill | Coordination Pattern |
|------------|---------------------|
| **OMEGA-ARCHITECT** | Architect designs structure → Engineer implements it. Engineer identifies technical debt → Architect prioritizes structural fixes. |
| **OMEGA-SENTINEL** | Engineer builds health checks → Sentinel runs them. Sentinel detects anomalies → Engineer investigates root cause. |

---

## Engineering Validation Checklist (use before shipping ANY code change)

```
□ All existing tests still pass (python -m pytest tests/ -q)
□ New code has corresponding tests
□ Type hints on all function signatures
□ SQL queries use parameterized placeholders (?)
□ No SELECT * in production code paths
□ Batch inserts use executemany (not row-by-row)
□ DB connections set WAL mode and busy_timeout
□ No hardcoded statistics (query DB live)
□ No python -c inline execution
□ CWD is not set to repo root for Python execution
□ No hard deletes on litigation files (move to I:\)
□ No PII in logs or debug output
□ Shadow module audit passed (no repo-root imports)
□ EAGAIN budget respected (max 2 shells, max 4 agents)
□ Engine follows canonical pattern (if applicable)
□ Docstrings on public functions and classes
```
