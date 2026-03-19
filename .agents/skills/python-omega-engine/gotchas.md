# Gotchas — python-omega-engine

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "I'll just run a quick `python -c 'print(...)'` in PowerShell to test this." | Inline Python via PowerShell ALWAYS breaks. Backslashes in Windows paths get interpreted as escapes, f-strings with braces collide with PowerShell variable expansion, and nested quotes corrupt. This has caused SyntaxError cascades in 10+ past sessions. | SyntaxError, mangled output, or worse — silently wrong results that get used in downstream processing. Write to a temp `.py` file instead. |
| 2 | "I'm in the repo root, let me just `python script.py` real quick." | The repo root contains **22 shadow modules**: `json.py`, `typing.py`, `tokenize.py`, `numpy.py`, `pandas.py`, `ast.py`, `io.py`, `os.py`, and 14 more. Python's import system finds these before stdlib. Running ANY Python from repo root will import fake modules. | `import json` loads a local file instead of stdlib. Cryptic errors like `AttributError: module 'json' has no attribute 'dumps'`. Every downstream import chain is corrupted. |
| 3 | "UTF-8 is the default encoding in Python 3, so I don't need to set it." | On Windows, Python's default encoding is often `cp1252` or the system locale, NOT UTF-8. LitigationOS evidence files contain diacritics, smart quotes, and Unicode characters. Without explicit UTF-8, `UnicodeDecodeError` crashes the pipeline. | Pipeline crashes mid-processing on any file with non-ASCII content. Evidence files with names like "café" or content with em-dashes silently corrupt. |
| 4 | "I'll clean up the temp files later." | 'Later' never comes. Past sessions left 50+ temp `.py` files in `temp/` and repo root. These accumulate, some shadow real modules, and the next session inherits the mess. Temp files are a technical debt vector. | Stale temp files confuse future agents, shadow modules multiply, disk fills with abandoned scripts. `spreflight` cleanup should run at session end. |
| 5 | "I need to open 4 DB connections for parallel queries — it'll be faster." | LitigationOS enforces max 3 concurrent DB connections via `db_lock_manager.py`. Opening a 4th triggers `SQLITE_BUSY` with 60-second timeout, then fails. The 12GB `litigation_context.db` is shared across all agents. | `SQLITE_BUSY` errors cascade. The 4th connection blocks, timeout expires, query fails, agent retries, creates 5th connection — deadlock spiral. |
| 6 | "I'll use `SELECT *` — it's faster to write and I need all columns anyway." | On a 12GB database with 790+ tables, `SELECT *` pulls columns you don't need, wastes I/O, and breaks when schema changes (columns get renamed/added). LitigationOS schema evolves constantly — column names documented in instructions may be stale. | Query returns wrong data after schema migration. `KeyError` on expected column names. 10x more I/O than needed on hot-path queries. |
| 7 | "I don't need `PRAGMA busy_timeout` — my queries are fast." | Even fast queries can collide with concurrent WAL checkpoints or other agents' writes. Without `busy_timeout=60000`, a 50ms read that hits a WAL checkpoint returns `SQLITE_BUSY` immediately instead of retrying. | Intermittent `database is locked` errors that only appear under concurrent load — the hardest bugs to reproduce and diagnose. |

---

## Common Failure Modes

### 1. Shadow Module Import Corruption
- **What happens**: Python script runs with CWD = repo root. `import json` loads `C:\Users\andre\LitigationOS\json.py` instead of stdlib `json`. All downstream imports that depend on stdlib `json` also break.
- **How to prevent**: NEVER set CWD to repo root for Python execution. Use `safe_shell.py run` or set CWD to the script's own directory. Run `sshadow` to audit shadow modules.
- **Risk level**: HIGH

### 2. Windows Encoding Explosion
- **What happens**: Python script reads a file without explicit `encoding='utf-8'` on Windows. The default `cp1252` encoding can't handle UTF-8 multibyte characters. Crashes with `UnicodeDecodeError` or silently corrupts text.
- **How to prevent**: Every `open()` call must include `encoding='utf-8'`. Set `sys.stdout` to UTF-8 mode at script start. Set `$env:PYTHONUTF8 = "1"` in PowerShell before running Python.
- **Risk level**: HIGH

### 3. DB Connection Pool Exhaustion
- **What happens**: Multiple agents or concurrent queries open DB connections without using `managed_db()`. Exceeds the 3-connection limit. `SQLITE_BUSY` errors cascade.
- **How to prevent**: Always use `managed_db()` context manager from `db_lock_manager.py`. Set PRAGMAs: `busy_timeout=60000`, `journal_mode=WAL`, `cache_size=-32000`. Never open raw `sqlite3.connect()` in production code.
- **Risk level**: HIGH

### 4. Temp File Accumulation
- **What happens**: Scripts write to `temp/` or repo root for intermediate results but never clean up. Over sessions, hundreds of orphaned files accumulate. Some shadow stdlib modules.
- **How to prevent**: Use `tempfile.NamedTemporaryFile(delete=True)` or explicit cleanup in `finally` blocks. Run `spreflight` at session start and end. Never write temp files to repo root.
- **Risk level**: MEDIUM

### 5. PRAGMA Omission on New Connections
- **What happens**: A new DB connection is opened without setting WAL mode, busy_timeout, or cache_size. Under concurrent access, the connection uses default journal mode (DELETE), which locks the entire database during writes.
- **How to prevent**: Use the three-tier connection strategy. Every connection must set at minimum: `PRAGMA busy_timeout=60000; PRAGMA journal_mode=WAL; PRAGMA cache_size=-32000; PRAGMA temp_store=MEMORY; PRAGMA synchronous=NORMAL;`
- **Risk level**: HIGH

---

## Integration Gotchas

- **safe_shell.py**: Always use `python 00_SYSTEM\tools\safe_shell.py run script.py` instead of direct `python script.py`. It avoids shadow modules and sets correct encoding.
- **agent_profile.ps1**: Dot-source this first (`. agent_profile.ps1`) to get `sspy`, `srun`, `spy`, `senv`, `sshadow`, `spreflight` wrapper functions.
- **EAGAIN + Python**: Never open DB connections inside PowerShell shell commands. Write a standalone `.py` script and execute it. DB connections inside shells consume both pipe resources AND DB connection slots.
- **executemany vs execute loop**: Always collect rows into a list and use `conn.executemany()` for batch inserts. Row-by-row `execute()` inside a loop is 10-100x slower on the 12GB litigation database.
- **FTS5 queries**: Use `adaptive_query_rewriter.py` to automatically convert `LIKE '%term%'` to FTS5 `MATCH` queries. Direct LIKE patterns on large tables cause full table scans.
