# Python Safety Guide — python-omega-engine

## Shadow Module Avoidance

The LitigationOS repo root (`C:\Users\andre\LitigationOS\`) contains **22 shadow modules** — Python files that have the same name as stdlib or third-party packages. These WILL be imported instead of the real packages if Python's CWD is the repo root.

### Known Shadow Modules (as of current audit)

```
json.py          typing.py        tokenize.py      numpy.py
pandas.py        ast.py           io.py            os.py
re.py            sys.py           csv.py           math.py
collections.py   functools.py     itertools.py     pathlib.py
datetime.py      logging.py       unittest.py      subprocess.py
hashlib.py       sqlite3.py
```

### How Python Resolves Imports

```
import json  →  Python searches in this order:
  1. sys.modules cache (already imported?)
  2. Built-in modules (sys, builtins)
  3. CWD (current working directory)     ← DANGER: finds json.py here
  4. PYTHONPATH entries
  5. Site-packages (pip-installed)
  6. Stdlib
```

### Safe Execution Patterns

```powershell
# PATTERN 1: Use safe_shell.py (recommended)
python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py run script.py

# PATTERN 2: Set CWD to script's own directory
cd C:\Users\andre\LitigationOS\00_SYSTEM\pipeline && python phase3_classify.py

# PATTERN 3: Use agent_profile.ps1 wrappers
. C:\Users\andre\LitigationOS\00_SYSTEM\tools\agent_profile.ps1
srun script.py --arg           # safe run
spy "print(1+1)"               # safe inline Python (temp file, not -c)
sspy file1.py file2.py         # syntax check (AST parse only)
sshadow                        # audit shadow modules

# PATTERN 4: Explicit PYTHONPATH manipulation
$env:PYTHONPATH = "C:\Users\andre\LitigationOS\00_SYSTEM\pipeline"
python -m my_module
```

### NEVER Do This

```powershell
# ❌ Run Python from repo root
cd C:\Users\andre\LitigationOS && python script.py

# ❌ Inline Python via PowerShell
python -c "import json; print(json.dumps({'key': 'value'}))"

# ❌ PowerShell string interpolation with Python
$var = "test"
python -c "print(f'$var')"   # PowerShell expands $var before Python sees it
```

## Encoding Setup (Windows-Specific)

Windows default encoding is `cp1252`, NOT `utf-8`. Every Python script must handle this.

### Script-Level Setup (add to every script entry point)

```python
import sys
import io

# Force UTF-8 stdout (prevents UnicodeEncodeError on print)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

### Environment Variable (set before running Python)

```powershell
$env:PYTHONUTF8 = "1"    # Forces UTF-8 mode globally
```

### File I/O (always specify encoding)

```python
# ✅ CORRECT
with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# ❌ WRONG (uses system default — cp1252 on Windows)
with open(filepath, 'r') as f:
    content = f.read()
```

## Temp File Patterns

### Safe Temp File Usage

```python
import tempfile
import os

# Pattern 1: Auto-cleanup temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
    f.write(script_content)
    temp_path = f.name
try:
    subprocess.run(['python', temp_path], check=True)
finally:
    os.unlink(temp_path)  # Always clean up

# Pattern 2: Use LitigationOS temp directory
TEMP_DIR = r"C:\Users\andre\LitigationOS\temp"
os.makedirs(TEMP_DIR, exist_ok=True)
temp_path = os.path.join(TEMP_DIR, f"task_{os.getpid()}.py")
```

### Cleanup Protocol

```powershell
# Run at session start and end
spreflight    # kills orphan processes + cleans temp files

# Manual cleanup
Get-ChildItem C:\Users\andre\LitigationOS\temp\*.py | Remove-Item
```

### Rules

1. **Never write temp files to repo root** — they may shadow stdlib modules
2. **Always use `finally` blocks** for cleanup — exceptions must not leave temp files behind
3. **Use `os.getpid()` in temp filenames** — prevents collisions between concurrent agents
4. **Run `spreflight` at session boundaries** — catches anything missed by individual cleanups
5. **Prefer `tempfile` module** over manual path construction — handles OS-specific temp dirs
