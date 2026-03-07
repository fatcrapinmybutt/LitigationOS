"""
LitigationOS Safe Shell Toolkit — Permanent fixes for recurring agent errors.

Problems this solves:
  1. Shadow modules (tokenize.py, typing.py, etc.) in repo root break Python
  2. Windows cp1252 encoding crashes on UTF-8 files
  3. Inline `python -c` via PowerShell mangles quotes/backslashes
  4. py_compile fails when run from repo root
  5. No safe temp-script runner

Usage from PowerShell:
    python 00_SYSTEM/tools/safe_shell.py check __init__.py file2.py ...
    python 00_SYSTEM/tools/safe_shell.py run   some_script.py --arg1 val
    python 00_SYSTEM/tools/safe_shell.py shadow-audit
    python 00_SYSTEM/tools/safe_shell.py env-check
"""
import ast
import os
import sys
import shutil
import hashlib
import tempfile
import subprocess
from pathlib import Path

# ─── Constants ───────────────────────────────────────────────────────
LITIGOS_ROOT = Path(r"C:\Users\andre\LitigationOS")

# Known Python stdlib module names that exist as shadow files in our repo root
KNOWN_SHADOWS = {
    "json.py", "parser.py", "thread.py", "token.py", "tokenize.py", "typing.py",
    "bson.py", "cbor2.py", "django.py", "flask.py", "google.py", "msgpack.py",
    "msgspec.py", "numpy.py", "orjson.py", "pandas.py", "pep8.py", "pytest.py",
    "pyyaml.py", "tomlkit.py", "ujson.py",
}

# The SAFE directory — guaranteed no shadow modules
SAFE_DIR = LITIGOS_ROOT / "00_SYSTEM" / "tools"


def ensure_utf8_stdout():
    """Force UTF-8 stdout — prevents cp1252 crashes on Windows."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    else:
        sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")


def check_syntax(files: list[str]) -> dict:
    """
    AST-parse Python files to verify syntax. Works regardless of shadow modules
    because it reads files as text and parses — never imports them.

    Returns: {"ok": [...], "fail": [...], "missing": [...]}
    """
    ensure_utf8_stdout()
    results = {"ok": [], "fail": [], "missing": []}

    for fpath in files:
        p = Path(fpath)
        if not p.exists():
            # Try relative to CWD and to LITIGOS_ROOT
            if (Path.cwd() / fpath).exists():
                p = Path.cwd() / fpath
            elif (LITIGOS_ROOT / fpath).exists():
                p = LITIGOS_ROOT / fpath
            else:
                results["missing"].append(fpath)
                print(f"  MISSING: {fpath}")
                continue

        try:
            source = p.read_text(encoding="utf-8", errors="replace")
            ast.parse(source, filename=str(p))
            results["ok"].append(str(p))
            print(f"  ✅ OK: {p.name}")
        except SyntaxError as e:
            results["fail"].append({"file": str(p), "error": str(e)})
            print(f"  ❌ FAIL: {p.name} — {e}")

    total = len(results["ok"]) + len(results["fail"]) + len(results["missing"])
    print(f"\n  {len(results['ok'])}/{total} valid")
    return results


def safe_run(script_path: str, args: list[str] = None, cwd: str = None) -> int:
    """
    Run a Python script safely — avoids shadow module contamination.

    Strategy: Sets PYTHONDONTWRITEBYTECODE, removes repo root from sys.path
    by using the script's own directory as CWD (not the repo root).
    """
    ensure_utf8_stdout()
    p = Path(script_path).resolve()
    if not p.exists():
        print(f"  ❌ Script not found: {script_path}")
        return 1

    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    # Remove repo root from PYTHONPATH if present
    pythonpath = env.get("PYTHONPATH", "")
    clean_path = os.pathsep.join(
        part for part in pythonpath.split(os.pathsep)
        if part and Path(part).resolve() != LITIGOS_ROOT
    )
    env["PYTHONPATH"] = clean_path

    # Run from script's own directory to avoid shadow imports
    run_cwd = cwd or str(p.parent)
    cmd = [sys.executable, str(p)] + (args or [])

    print(f"  🔧 Running: {p.name} {' '.join(args or [])}")
    print(f"  📁 CWD: {run_cwd}")

    result = subprocess.run(cmd, cwd=run_cwd, env=env, capture_output=False)
    return result.returncode


def safe_exec_code(code: str, description: str = "inline") -> int:
    """
    Execute Python code safely via temp file — NEVER use python -c on Windows.

    Writes code to a temp .py file in SAFE_DIR, executes, cleans up.
    """
    ensure_utf8_stdout()
    SAFE_DIR.mkdir(parents=True, exist_ok=True)

    # Deterministic temp name to avoid collisions
    code_hash = hashlib.md5(code.encode()).hexdigest()[:8]
    tmp_path = SAFE_DIR / f"_tmp_{code_hash}.py"

    try:
        # Prepend UTF-8 stdout fix
        full_code = (
            "import sys\n"
            "if hasattr(sys.stdout, 'reconfigure'):\n"
            "    sys.stdout.reconfigure(encoding='utf-8', errors='replace')\n"
            "\n" + code
        )
        tmp_path.write_text(full_code, encoding="utf-8")
        return safe_run(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)


def shadow_audit() -> list[dict]:
    """
    Scan repo root for files that shadow Python stdlib/third-party modules.
    Returns list of shadow files with details.
    """
    ensure_utf8_stdout()
    print(f"\n  Shadow Module Audit: {LITIGOS_ROOT}\n")

    # Get all stdlib module names
    import pkgutil
    stdlib_names = set()
    for mod in pkgutil.iter_modules():
        stdlib_names.add(mod.name)

    # Also add known problematic names
    stdlib_names.update({
        "tokenize", "typing", "json", "token", "parser", "thread",
        "ast", "io", "os", "sys", "re", "collections", "abc", "enum",
        "types", "copy", "signal", "string", "keyword", "code", "base64",
        "email", "calendar", "profile", "test", "site", "stat", "struct",
        "array", "random", "socket", "select", "http", "html", "xml",
        "csv", "sqlite3", "logging", "inspect", "traceback", "warnings",
        "importlib", "pathlib", "subprocess", "shutil", "tempfile",
        "hashlib", "secrets", "datetime", "time", "math", "pickle",
        "shelve", "argparse", "configparser", "functools", "itertools",
        "operator", "contextlib", "concurrent", "asyncio", "threading",
        "multiprocessing", "unittest", "pdb", "dis", "compileall",
        "textwrap", "difflib", "pprint", "dataclasses",
    })

    shadows = []
    for f in LITIGOS_ROOT.iterdir():
        if not f.is_file() or f.suffix != ".py":
            continue
        stem = f.stem
        if stem in stdlib_names or f.name in KNOWN_SHADOWS:
            size = f.stat().st_size
            shadows.append({
                "file": f.name,
                "path": str(f),
                "size": size,
                "shadows": stem,
            })
            print(f"  ⚠️  {f.name:25s} ({size:>8,} bytes) — shadows '{stem}'")

    if not shadows:
        print("  ✅ No shadow modules found")
    else:
        print(f"\n  Found {len(shadows)} shadow modules in repo root")
        print(f"  ⚡ Fix: Never run Python with CWD={LITIGOS_ROOT}")
        print(f"  ⚡ Fix: Use `safe_run()` or `safe_exec_code()` from this toolkit")

    return shadows


def env_check() -> dict:
    """Full environment health check — reports everything an agent needs to know."""
    ensure_utf8_stdout()
    print(f"\n  {'='*55}")
    print(f"  LitigationOS Environment Health Check")
    print(f"  {'='*55}\n")

    info = {}

    # Python version
    info["python_version"] = sys.version
    info["python_path"] = sys.executable
    print(f"  Python: {sys.version.split()[0]} ({sys.executable})")

    # Encoding
    info["stdout_encoding"] = sys.stdout.encoding
    info["fs_encoding"] = sys.getfilesystemencoding()
    info["default_encoding"] = sys.getdefaultencoding()
    ok = sys.stdout.encoding.lower().replace("-", "") == "utf8"
    print(f"  Stdout encoding: {sys.stdout.encoding} {'✅' if ok else '⚠️ NOT UTF-8'}")
    print(f"  FS encoding: {sys.getfilesystemencoding()}")

    # PYTHONUTF8 mode
    utf8_mode = os.environ.get("PYTHONUTF8", "0")
    print(f"  PYTHONUTF8: {utf8_mode} {'✅' if utf8_mode == '1' else '⚠️ set to 1 for safety'}")

    # Shadow modules
    shadow_count = sum(1 for f in LITIGOS_ROOT.iterdir()
                       if f.is_file() and f.suffix == ".py" and f.name in KNOWN_SHADOWS)
    info["shadow_modules"] = shadow_count
    print(f"  Shadow modules in root: {shadow_count} {'⚠️ USE safe_run()' if shadow_count else '✅'}")

    # Drive space
    print(f"\n  Drive Space:")
    for drive in ["C", "D", "F", "G", "H", "I"]:
        dp = Path(f"{drive}:\\")
        if dp.exists():
            try:
                usage = shutil.disk_usage(str(dp))
                free_gb = usage.free / (1024**3)
                total_gb = usage.total / (1024**3)
                pct = usage.used / usage.total * 100
                warn = "⚠️" if free_gb < 10 else "✅"
                print(f"    {drive}:\\ {free_gb:6.1f} GB free / {total_gb:6.1f} GB total ({pct:.0f}% used) {warn}")
                info[f"drive_{drive}_free_gb"] = round(free_gb, 1)
            except Exception:
                print(f"    {drive}:\\ (error reading)")

    # Key databases
    print(f"\n  Databases:")
    for db_name, db_path in [
        ("litigation_context.db", LITIGOS_ROOT / "litigation_context.db"),
        ("copilot_state.db", LITIGOS_ROOT / "00_SYSTEM" / "copilot_state" / "copilot_state.db"),
        ("INDEX.db", LITIGOS_ROOT / "_INDEX" / "INDEX.db"),
    ]:
        if db_path.exists():
            size_mb = db_path.stat().st_size / (1024 * 1024)
            print(f"    {db_name:30s} {size_mb:8.1f} MB ✅")
        else:
            print(f"    {db_name:30s} NOT FOUND")

    # Key tools
    print(f"\n  Tool Availability:")
    tools = [
        ("safe_shell.py", SAFE_DIR / "safe_shell.py"),
        ("copilot_startup_hook.py", LITIGOS_ROOT / "00_SYSTEM" / "local_model" / "copilot_startup_hook.py"),
        ("org_orchestrator.py", LITIGOS_ROOT / "00_SYSTEM" / "org_agents" / "org_orchestrator.py"),
        ("inference_engine.py", LITIGOS_ROOT / "00_SYSTEM" / "local_model" / "inference_engine.py"),
    ]
    for name, path in tools:
        print(f"    {name:35s} {'✅' if path.exists() else '❌'}")

    print(f"\n  {'='*55}")
    return info


def create_powershell_profile():
    """
    Generate a PowerShell helper profile that agents can dot-source.
    Provides: sspy (safe syntax check), srun (safe run), senv (env check).
    """
    ensure_utf8_stdout()
    profile_path = LITIGOS_ROOT / "00_SYSTEM" / "tools" / "agent_profile.ps1"

    profile_content = r'''# LitigationOS Agent PowerShell Profile
# Dot-source this: . C:\Users\andre\LitigationOS\00_SYSTEM\tools\agent_profile.ps1

$env:PYTHONUTF8 = "1"
$env:PYTHONDONTWRITEBYTECODE = "1"

# Safe syntax check — avoids shadow module issues
function sspy {
    param([Parameter(ValueFromRemainingArguments=$true)]$files)
    python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py check @files
}

# Safe run — executes script from its own directory, not repo root
function srun {
    param([Parameter(ValueFromRemainingArguments=$true)]$args_)
    python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py run @args_
}

# Environment health check
function senv {
    python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py env-check
}

# Shadow module audit
function sshadow {
    python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py shadow-audit
}

# Safe inline Python execution (writes to temp file, never python -c)
function spy {
    param([string]$code)
    $hash = [System.BitConverter]::ToString(
        [System.Security.Cryptography.MD5]::Create().ComputeHash(
            [System.Text.Encoding]::UTF8.GetBytes($code)
        )
    ).Replace("-","").Substring(0,8).ToLower()
    $tmp = "C:\Users\andre\LitigationOS\00_SYSTEM\tools\_tmp_$hash.py"
    @"
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
$code
"@ | Out-File -Encoding utf8 $tmp
    python $tmp
    Remove-Item $tmp -ErrorAction SilentlyContinue
}

Write-Host "LitigationOS agent profile loaded. Commands: sspy, srun, senv, sshadow, spy" -ForegroundColor Green
'''
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(profile_content, encoding="utf-8")
    print(f"  ✅ Profile written to {profile_path}")
    print(f"  Usage: . {profile_path}")
    return str(profile_path)


# ─── CLI ─────────────────────────────────────────────────────────────
def main():
    ensure_utf8_stdout()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  safe_shell.py check FILE [FILE ...]   — Syntax check Python files")
        print("  safe_shell.py run SCRIPT [ARGS ...]    — Run script safely")
        print("  safe_shell.py shadow-audit             — Find shadow modules")
        print("  safe_shell.py env-check                — Full environment health check")
        print("  safe_shell.py install-profile           — Create PowerShell helper profile")
        return

    cmd = sys.argv[1]

    if cmd == "check":
        if len(sys.argv) < 3:
            print("  Provide files to check: safe_shell.py check file1.py file2.py ...")
            return
        check_syntax(sys.argv[2:])

    elif cmd == "run":
        if len(sys.argv) < 3:
            print("  Provide script: safe_shell.py run script.py [args...]")
            return
        rc = safe_run(sys.argv[2], sys.argv[3:])
        sys.exit(rc)

    elif cmd == "shadow-audit":
        shadow_audit()

    elif cmd == "env-check":
        env_check()

    elif cmd == "install-profile":
        create_powershell_profile()

    else:
        print(f"  Unknown command: {cmd}")
        print("  Commands: check, run, shadow-audit, env-check, install-profile")


if __name__ == "__main__":
    main()
