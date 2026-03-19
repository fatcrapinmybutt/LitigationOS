<# New-PerfectCoder.ps1
Scaffolds a production-grade "Perfect Coder" repo with:
- Polyglot-ready structure (Python core today), CLI "forge" (plan/build/verify/ship)
- Static checks (ruff+mypy), tests (pytest+hypothesis), security (bandit)
- Coverage gate, simple SBOM generator, GitHub Actions CI
- Pre-commit hooks and editor config
Usage:
  pwsh -File .\New-PerfectCoder.ps1 -ProjectDir "C:\work\perfect-coder" [-Force]
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)][string]$ProjectDir = (Join-Path $PWD "perfect-coder"),
  [switch]$Force
)

function Write-Text($Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
  Write-Host "Wrote $Path"
}

if (Test-Path $ProjectDir) {
  if (-not $Force) {
    throw "Path exists: $ProjectDir. Use -Force to overwrite or choose a new path."
  } else {
    Write-Host "Cleaning $ProjectDir ..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $ProjectDir
  }
}
New-Item -ItemType Directory -Force -Path $ProjectDir | Out-Null

# ---------------- Files ----------------

$gitignore = @'
# OS
.DS_Store
Thumbs.db
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
*.egg-info/
.build/
dist/
.venv/
.coverage
.coverage.*
htmlcov/
# Tools
.mypy_cache/
.ruff_cache/
.pytest_cache/
.env
# IDE
.vscode/
.idea/
# Artifacts
sbom.json
'@

$editorconfig = @'
root = true

[*]
end_of_line = lf
insert_final_newline = true
charset = utf-8
indent_style = space
indent_size = 2
trim_trailing_whitespace = true

[*.py]
indent_size = 4
'@

$readme = @'
# Perfect Coder

Deterministic code generation and verification pipeline.

## Quick start
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
forge plan --spec "Initial install and smoke tests"
forge build
pytest
forge verify
Commands
forge plan → parse spec and produce a plan + checklist

forge build → ensure package buildable; emit artifacts

forge verify → run internal checks; CI runs full gate

forge ship → placeholder to integrate deploy (kept safe)

CI gates
Ruff lint + format check

MyPy types

PyTest + Hypothesis with coverage >= 85

Bandit security scan

SBOM JSON artifact

'@

$pyproject = @'
[build-system]
requires = ["hatchling>=1.24.2"]
build-backend = "hatchling.build"

[project]
name = "perfect-coder"
version = "0.1.0"
description = "Perfect Coder: plan → build → verify → ship"
readme = "README.md"
requires-python = ">=3.11"
authors = [{name="System Architect"}]
dependencies = [
"typer>=0.12.3",
"rich>=13.7.1",
]

[project.optional-dependencies]
dev = [
"pytest>=8.3.2",
"hypothesis>=6.112.0",
"coverage[toml]>=7.6.1",
"ruff>=0.6.9",
"mypy>=1.11.2",
"bandit>=1.7.9",
]

[project.scripts]
forge = "forge.main:app"

[tool.ruff]
line-length = 100
target-version = "py311"
extend-select = ["I"] # import sorting
lint.ignore = []

[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true
plugins = []

[tool.pytest.ini_options]
addopts = "-q --maxfail=1 --disable-warnings --color=yes --cov=forge --cov-report=term-missing --cov-fail-under=85"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["forge"]

[tool.coverage.report]
show_missing = true
skip_covered = true
'@

$precommit = @'
repos:

repo: https://github.com/astral-sh/ruff-pre-commit
rev: v0.6.9
hooks:

id: ruff
args: [--fix]

id: ruff-format

repo: https://github.com/pre-commit/mirrors-mypy
rev: v1.11.2
hooks:

id: mypy
additional_dependencies: []

repo: https://github.com/PyCQA/bandit
rev: 1.7.9
hooks:

id: bandit
args: ["-r", "src"]
'@

$workflow = @'
name: ci
on:
push:
branches: ["**"]
pull_request:

jobs:
build-test:
runs-on: windows-latest
steps:
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
with:
python-version: "3.11"
cache: "pip"
- name: Install package + dev deps
run: |
python -m pip install --upgrade pip
pip install -e ".[dev]"
- name: Ruff format check
run: ruff format --check
- name: Ruff lint
run: ruff check
- name: MyPy
run: mypy src
- name: Tests
run: pytest
- name: Bandit security scan
run: bandit -r src
- name: SBOM (simple)
run: python tools/sbom.py > sbom.json
- name: Upload artifacts
uses: actions/upload-artifact@v4
with:
name: sbom-and-coverage
path: |
sbom.json
.coverage
'@

$forge_main = @'
from future import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from rich.table import Table

app = typer.Typer(help="Perfect Coder: plan → build → verify → ship")

ROOT = Path(file).resolve().parents[1]
SRC = ROOT / "src"
PKG = SRC / "forge"
ART = ROOT / "artifacts"
ART.mkdir(parents=True, exist_ok=True)

def _run(cmd: List[str]) -> int:
proc = subprocess.run(cmd, shell=False)
return proc.returncode

def _ok(tag: str) -> None:
print(f"[green]✔ {tag}[/green]")

def _fail(tag: str) -> None:
print(f"[red]✖ {tag}[/red]")

@app.command()
def plan(
spec: Optional[str] = typer.Option(None, "--spec", "-s", help="Natural language spec"),
spec_file: Optional[Path] = typer.Option(None, "--spec-file", "-f", exists=False, help="Spec file"),
) -> None:
"""
Convert a spec into a minimal actionable plan.
"""
text = ""
if spec:
text = spec.strip()
elif spec_file and spec_file.exists():
text = spec_file.read_text(encoding="utf-8").strip()
else:
text = "No spec provided. Using default: create, test, and verify sample module."

pgsql
Copy code
plan = {
    "inputs": {"spec": text[:1000]},
    "goals": [
        "Maintain type safety",
        "Pass property tests",
        "Keep coverage >= 85%",
        "No bandit high issues",
        "Lint clean",
    ],
    "artifacts": ["wheel", "coverage report", "sbom.json"],
    "commands": ["forge build", "pytest", "forge verify"],
}
(ART / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
_ok("Plan written to artifacts/plan.json")
table = Table(title="Plan")
table.add_column("Goal")
for g in plan["goals"]:
    table.add_row(g)
print(table)
@app.command()
def build() -> None:
"""
Ensure package builds; emit wheel to artifacts.
"""
wheel_dir = ART / "dist"
wheel_dir.mkdir(parents=True, exist_ok=True)
code = _run(["python", "-m", "pip", "install", "--upgrade", "build"])
if code != 0:
_fail("pip install build")
raise typer.Exit(code)
code = _run(["python", "-m", "build", "--wheel", "--outdir", str(wheel_dir)])
if code != 0:
_fail("build wheel")
raise typer.Exit(code)
_ok("Wheel built")

@app.command()
def verify() -> None:
"""
Local verification of core gates. CI performs full gates.
"""
gates = [
(["ruff", "format", "--check"], "format"),
(["ruff", "check"], "lint"),
(["mypy", "src"], "types"),
(["pytest"], "tests"),
(["bandit", "-r", "src"], "security"),
]
failed = False
for cmd, tag in gates:
code = _run(cmd)
if code == 0:
_ok(tag)
else:
_fail(tag)
failed = True
if failed:
raise typer.Exit(1)
_ok("All local gates passed")

@app.command()
def ship(
target: Optional[str] = typer.Option(None, "--target", help="Distribution target hint")
) -> None:
"""
Prepare artifacts for distribution.
"""
# Placeholder for deploy choreography hooks (kept inert by default).
# Intentionally minimal to avoid unsafe defaults.
meta = {"target": target or "local", "artifacts": [p.name for p in ART.glob("**/*") if p.is_file()]}
(ART / "ship.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
_ok("Ship metadata written to artifacts/ship.json")
'@

$forge_pkg_init = @'
"""Perfect Coder core package."""
'@

$sample_module = @'
from future import annotations
from pathlib import PurePosixPath
from typing import Iterable

def normalize_segments(segments: Iterable[str]) -> str:
"""
Normalize path segments deterministically.
- Removes empty segments
- Collapses "." and resolves ".." when safe
- Uses POSIX separator for stability
"""
parts: list[str] = []
for seg in segments:
s = seg.strip().replace("\", "/")
if not s or s == ".":
continue
if s == "..":
if parts:
parts.pop()
continue
parts.append(s)
return str(PurePosixPath("/".join(parts)))

def bounded_sum(xs: Iterable[int], cap: int) -> int:
"""
Sum integers with a hard cap. Enforces monotonicity and non-negativity.
"""
total = 0
for x in xs:
total += x
if total >= cap:
return cap
return max(0, total)
'@

$tests = @'
from future import annotations
from hypothesis import given, strategies as st
from forge.sample import normalize_segments, bounded_sum

@given(st.lists(st.text(min_size=0, max_size=8), max_size=8))
def test_normalize_idempotent(xs):
a = normalize_segments(xs)
b = normalize_segments(a.split("/"))
assert a == b

@given(st.lists(st.integers(min_value=-10, max_value=10), max_size=20), st.integers(min_value=0, max_value=100))
def test_bounded_sum_caps(xs, cap):
s = bounded_sum(xs, cap)
assert 0 <= s <= cap

def test_bounded_sum_monotone():
assert bounded_sum([1,2,3], 10) < bounded_sum([1,2,3,4], 10)
'@

$tools_sbom = @'
#!/usr/bin/env python
from future import annotations
import json
import subprocess

def pip_freeze() -> list[dict[str, str]]:
try:
out = subprocess.check_output(["python", "-m", "pip", "list", "--format", "json"], text=True)
return json.loads(out)
except Exception:
return []

def main() -> None:
pkgs = pip_freeze()
doc = {
"sbom_format": "simple-spdx-like",
"generator": "tools/sbom.py",
"packages": [{"name": p["name"], "version": p["version"]} for p in pkgs],
}
print(json.dumps(doc, indent=2))

if name == "main":
main()
'@

$pytestini = @'

configured in pyproject [tool.pytest.ini_options]
'@

---------------- Write files ----------------
Write-Text (Join-Path $ProjectDir ".gitignore") $gitignore
Write-Text (Join-Path $ProjectDir ".editorconfig") $editorconfig
Write-Text (Join-Path $ProjectDir "README.md") $readme
Write-Text (Join-Path $ProjectDir "pyproject.toml") $pyproject
Write-Text (Join-Path $ProjectDir ".pre-commit-config.yaml") $precommit
Write-Text (Join-Path $ProjectDir ".github\workflows\ci.yml") $workflow
Write-Text (Join-Path $ProjectDir "src\forge_init_.py") $forge_pkg_init
Write-Text (Join-Path $ProjectDir "src\forge_main_.py") $forge_main
Write-Text (Join-Path $ProjectDir "src\forge\sample.py") $sample_module
Write-Text (Join-Path $ProjectDir "tests\test_sample.py") $tests
Write-Text (Join-Path $ProjectDir "tools\sbom.py") $tools_sbom
Write-Text (Join-Path $ProjectDir "pytest.ini") $pytestini

---------------- Final hints ----------------
$next = @'
Next:

py -3.11 -m venv .venv

..venv\Scripts\Activate.ps1

python -m pip install --upgrade pip

pip install -e ".[dev]"

pre-commit install

forge plan -s "Initialize project"

forge build

forge verify

git init; git add .; git commit -m "bootstrap perfect-coder"
'@
Write-Text (Join-Path $ProjectDir "NEXT_STEPS.txt") $next

Write-Host "`nScaffold complete at: $ProjectDir" -ForegroundColor Green
Write-Host "Open NEXT_STEPS.txt for the local setup sequence."

Copy code
Continuing. Run in PowerShell from the repo root you scaffolded earlier:
`pwsh -File .\Extend-PerfectCoder.ps1 -ProjectDir "$PWD"`

````powershell
<# Extend-PerfectCoder.ps1
Upgrades the "Perfect Coder" repo with advanced gates:
- Adds mutation testing (mutatest), complexity gates (radon), vuln scan (pip-audit)
- Adds basic contracts + CrossHair proving pass (icontract + crosshair-tool)
- Expands CLI (forge) with: audit, complexity, mutate, prove, sbom
- Tightens CI with new steps and artifacts

Usage:
  pwsh -File .\Extend-PerfectCoder.ps1 -ProjectDir "C:\path\perfect-coder"
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)][string]$ProjectDir = (Join-Path $PWD ""),
  [switch]$Force
)

function Assert-Dir($Path) {
  if (-not (Test-Path $Path)) { throw "Path not found: $Path" }
}
function Write-Text($Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
  Write-Host "Wrote $Path"
}

Assert-Dir $ProjectDir

# ----- Update pyproject.toml -----
$pyproject = @'
[build-system]
requires = ["hatchling>=1.24.2"]
build-backend = "hatchling.build"

[project]
name = "perfect-coder"
version = "0.2.0"
description = "Perfect Coder: plan → build → verify → ship"
readme = "README.md"
requires-python = ">=3.11"
authors = [{name="System Architect"}]
dependencies = [
  "typer>=0.12.3",
  "rich>=13.7.1",
  "icontract>=2.6.6",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.2",
  "pytest-randomly>=3.15.0",
  "pytest-xdist>=3.6.1",
  "hypothesis>=6.112.0",
  "coverage[toml]>=7.6.1",
  "ruff>=0.6.9",
  "mypy>=1.11.2",
  "bandit>=1.7.9",
  "pip-audit>=2.7.3",
  "radon>=6.0.1",
  "mutatest>=3.1.0",
  "crosshair-tool>=0.0.63",
]

[project.scripts]
forge = "forge.__main__:app"

[tool.ruff]
line-length = 100
target-version = "py311"
extend-select = ["I"]  # import sorting

[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true

[tool.pytest.ini_options]
addopts = "-q --maxfail=1 --disable-warnings --color=yes --cov=forge --cov-report=term-missing --cov-fail-under=85"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["forge"]

[tool.coverage.report]
show_missing = true
skip_covered = true
'@
Write-Text (Join-Path $ProjectDir "pyproject.toml") $pyproject

# ----- Update pre-commit to add pip-audit -----
$precommit = @'
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks:
      - id: mypy
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.9
    hooks:
      - id: bandit
        args: ["-r", "src"]
  - repo: https://github.com/pypa/pip-audit
    rev: v2.7.3
    hooks:
      - id: pip-audit
'@
Write-Text (Join-Path $ProjectDir ".pre-commit-config.yaml") $precommit

# ----- Replace/extend CLI with new subcommands -----
$forge_main = @'
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from rich.table import Table

app = typer.Typer(help="Perfect Coder: plan → build → verify → ship")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PKG = SRC / "forge"
ART = ROOT / "artifacts"
ART.mkdir(parents=True, exist_ok=True)

def _run(cmd: List[str]) -> int:
    proc = subprocess.run(cmd, shell=False)
    return proc.returncode

def _ok(tag: str) -> None:
    print(f"[green]✔ {tag}[/green]")

def _fail(tag: str) -> None:
    print(f"[red]✖ {tag}[/red]")

@app.command()
def plan(
    spec: Optional[str] = typer.Option(None, "--spec", "-s", help="Natural language spec"),
    spec_file: Optional[Path] = typer.Option(None, "--spec-file", "-f", exists=False, help="Spec file"),
) -> None:
    text = spec.strip() if spec else (spec_file.read_text(encoding="utf-8").strip() if spec_file and spec_file.exists() else "No spec provided. Using default: initialize and smoke.")
    plan = {
        "inputs": {"spec": text[:2000]},
        "goals": [
            "Type safety (mypy)",
            "Property tests pass (Hypothesis)",
            "Coverage >= 85%",
            "No Bandit HIGH",
            "Lint clean (ruff)",
            "No known vulns (pip-audit)",
            "Complexity within budget (radon)",
            "Mutation survivors = 0 (mutatest)",
            "Basic contracts hold (icontract + CrossHair)",
        ],
        "artifacts": ["wheel", "coverage report", "sbom.json", "audit.json"],
        "commands": ["forge build", "pytest -n auto -q", "forge verify", "forge audit", "forge complexity", "forge mutate", "forge prove", "forge sbom"],
    }
    (ART / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    _ok("Plan written to artifacts/plan.json")
    table = Table(title="Plan")
    table.add_column("Goal")
    for g in plan["goals"]:
        table.add_row(g)
    print(table)

@app.command()
def build() -> None:
    wheel_dir = ART / "dist"
    wheel_dir.mkdir(parents=True, exist_ok=True)
    code = _run(["python", "-m", "pip", "install", "--upgrade", "build"])
    if code != 0:
        _fail("pip install build"); raise typer.Exit(code)
    code = _run(["python", "-m", "build", "--wheel", "--outdir", str(wheel_dir)])
    if code != 0:
        _fail("build wheel"); raise typer.Exit(code)
    _ok("Wheel built")

@app.command()
def verify() -> None:
    gates = [
        (["ruff", "format", "--check"], "format"),
        (["ruff", "check"], "lint"),
        (["mypy", "src"], "types"),
        (["pytest", "-n", "auto", "-q"], "tests"),
        (["bandit", "-r", "src"], "security"),
    ]
    failed = False
    for cmd, tag in gates:
        code = _run(cmd)
        if code == 0: _ok(tag)
        else: _fail(tag); failed = True
    if failed: raise typer.Exit(1)
    _ok("Core gates passed")

@app.command()
def audit() -> None:
    """
    Vulnerability scan with pip-audit. Fails on any known vulnerabilities.
    """
    out = ART / "audit.json"
    code = _run(["python", "-m", "pip_audit", "-f", "json", "-o", str(out)])
    if code != 0:
        _fail("pip-audit"); raise typer.Exit(code)
    _ok(f"audit → {out}")

@app.command()
def complexity(
    cc_max: str = typer.Option("C", help="Max allowed radon CC grade (A best, F worst)"),
    mi_min: str = typer.Option("B", help="Min allowed Maintainability Index grade (A best, F worst)"),
) -> None:
    """
    Enforce complexity and maintainability budgets via radon.
    """
    code = _run(["python", "tools/complexity.py", "--cc-max", cc_max, "--mi-min", mi_min, "--path", "src"])
    if code != 0:
        _fail("complexity gates"); raise typer.Exit(code)
    _ok("complexity gates")

@app.command()
def mutate() -> None:
    """
    Mutation testing via mutatest. Fails on any survivors.
    """
    code = _run(["python", "tools/mut_gate.py", "--src", "src/forge", "--tests", "tests"])
    if code != 0:
        _fail("mutation survivors"); raise typer.Exit(code)
    _ok("mutation tests")

@app.command()
def prove() -> None:
    """
    Run CrossHair against contract-bearing functions.
    """
    # CrossHair exit code 0 = success, >0 = issues
    code = _run(["python", "-m", "crosshair", "check", "src/forge"])
    if code != 0:
        _fail("crosshair"); raise typer.Exit(code)
    _ok("crosshair proofs")

@app.command()
def sbom() -> None:
    code = _run(["python", "tools/sbom.py"])
    if code != 0:
        _fail("sbom"); raise typer.Exit(code)
    _ok("sbom printed (redirect to file if needed)")

@app.command()
def ship(target: Optional[str] = typer.Option(None, "--target", help="Distribution target hint")) -> None:
    meta = {"target": target or "local", "artifacts": [p.name for p in ART.glob("**/*") if p.is_file()]}
    (ART / "ship.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    _ok("Ship metadata written to artifacts/ship.json")
'@
Write-Text (Join-Path $ProjectDir "src\forge\__main__.py") $forge_main

# ----- Add contract-bearing sample + tests -----
$contracts_py = @'
from __future__ import annotations
from typing import Iterable
import icontract

@icontract.require(lambda xs: all(isinstance(x, int) for x in xs))
@icontract.require(lambda cap: cap >= 0)
@icontract.ensure(lambda xs, cap, result: 0 <= result <= cap)
def bounded_prefix_sum(xs: Iterable[int], cap: int) -> int:
    """
    Contract-driven variant of bounded_sum to demonstrate CrossHair/icontract.
    Monotone and capped.
    """
    total = 0
    for x in xs:
        total += x
        if total >= cap:
            return cap
    return max(0, total)
'@
Write-Text (Join-Path $ProjectDir "src\forge\contracts.py") $contracts_py

$tests_contracts = @'
from __future__ import annotations
from hypothesis import given, strategies as st
from forge.contracts import bounded_prefix_sum

@given(st.lists(st.integers(min_value=-10, max_value=10), max_size=20), st.integers(min_value=0, max_value=100))
def test_bounded_prefix_sum_caps(xs, cap):
    s = bounded_prefix_sum(xs, cap)
    assert 0 <= s <= cap
'@
Write-Text (Join-Path $ProjectDir "tests\test_contracts.py") $tests_contracts

# ----- Tools: complexity gate -----
$complexity_py = @'
from __future__ import annotations
import argparse, sys
from radon.complexity import cc_visit, cc_rank
from radon.metrics import mi_visit, mi_rank
from pathlib import Path

def gate(path: str, cc_max: str, mi_min: str) -> int:
    root = Path(path)
    violations = []
    for py in root.rglob("*.py"):
        code = py.read_text(encoding="utf-8", errors="ignore")
        # CC
        for block in cc_visit(code):
            grade = cc_rank(block.complexity)
            if grade > cc_max:  # lexicographic works for A..F
                violations.append(f"{py}:{block.name} CC {block.complexity:.1f} grade {grade} > {cc_max}")
        # MI
        mi = mi_visit(code, True)
        mgrade = mi_rank(mi)
        if mgrade < mi_min:
            violations.append(f"{py} MI {mi:.1f} grade {mgrade} < {mi_min}")
    if violations:
        print("Complexity/MI violations:")
        for v in violations: print(" -", v)
        return 2
    print("Complexity gates passed.")
    return 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--cc-max", default="C")
    ap.add_argument("--mi-min", default="B")
    args = ap.parse_args()
    sys.exit(gate(args.path, args.cc_max, args.mi_min))
'@
Write-Text (Join-Path $ProjectDir "tools\complexity.py") $complexity_py

# ----- Tools: mutation gate (mutatest wrapper) -----
$mut_gate = @'
from __future__ import annotations
import argparse, subprocess, sys

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="src/forge")
    ap.add_argument("--tests", default="tests")
    args = ap.parse_args()
    cmd = ["python", "-m", "mutatest", "-s", args.src, "-t", args.tests, "--nlocations", "0"]
    code = subprocess.call(cmd)
    # Mutatest exits nonzero if survivors present; propagate.
    return code

if __name__ == "__main__":
    sys.exit(main())
'@
Write-Text (Join-Path $ProjectDir "tools\mut_gate.py") $mut_gate

# ----- Expand CI workflow -----
$workflow = @'
name: ci
on:
  push:
    branches: ["**"]
  pull_request:

jobs:
  build-test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"
      - name: Install package + dev deps
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Ruff format check
        run: ruff format --check
      - name: Ruff lint
        run: ruff check
      - name: MyPy
        run: mypy src
      - name: Tests (xdist)
        run: pytest -n auto -q
      - name: Bandit security scan
        run: bandit -r src
      - name: Vulnerability scan (pip-audit)
        run: python -m pip_audit -f json -o artifacts/audit.json
      - name: Complexity gates (radon)
        run: python tools/complexity.py --cc-max C --mi-min B --path src
      - name: Mutation testing (mutatest)
        run: python tools/mut_gate.py --src src/forge --tests tests
      - name: SBOM (simple)
        run: python tools/sbom.py > sbom.json
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ci-artifacts
          path: |
            artifacts/**
            sbom.json
            .coverage
'@
Write-Text (Join-Path $ProjectDir ".github\workflows\ci.yml") $workflow

# ----- README badge hints -----
$readmePath = Join-Path $ProjectDir "README.md"
if (Test-Path $readmePath) {
  $readme = (Get-Content -Raw -Path $readmePath)
  $addon = @'

## Advanced gates
- `forge audit` → pip-audit (fails on known vulns)
- `forge complexity` → radon CC ≤ C, MI ≥ B
- `forge mutate` → mutatest survivors block
- `forge prove` → CrossHair over contract-bearing functions

### Quick upgrade
```powershell
pip install -e ".[dev]"
pre-commit install
forge plan -s "Harden with advanced gates"
forge build
forge verify
forge audit
forge complexity
forge mutate
forge prove
````

'@
Write-Text \$readmePath (\$readme + \$addon)
}

Write-Host "\`nUpgrade complete." -ForegroundColor Green
Write-Host "Next:"
Write-Host "1) py -3.11 -m venv .venv; ..venv\Scripts\Activate.ps1"
Write-Host "2) python -m pip install --upgrade pip"
Write-Host "3) pip install -e "".\[dev]"""
Write-Host "4) pre-commit install"
Write-Host "5) forge verify; forge audit; forge complexity; forge mutate; forge prove"

```
```
Run in PowerShell from your repo root:
`pwsh -File .\Fortify-PerfectCoder.ps1 -ProjectDir "$PWD"`

```powershell
<# Fortify-PerfectCoder.ps1
Adds plugin-like gates, provenance, license reporting, and Docker packaging.
- New CLI cmds: gate, provenance, licenses, docker
- External gate config: config/gates.yaml
- Tools: provenance hash, license inventory, YAML-driven gate runner
- CI extended to run new gates and build Docker image artifact

Usage:
  pwsh -File .\Fortify-PerfectCoder.ps1 -ProjectDir "C:\path\perfect-coder"
Then:
  py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  pip install -e ".[dev]"
  pre-commit install
  forge gate
  forge provenance
  forge licenses
  forge docker
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)][string]$ProjectDir = (Join-Path $PWD ""),
  [switch]$Force
)

function Assert-Dir($Path) { if (-not (Test-Path $Path)) { throw "Path not found: $Path" } }
function Write-Text($Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
  Write-Host "Wrote $Path"
}

Assert-Dir $ProjectDir

# ---------- Update pyproject: add deps for YAML + licenses ----------
$pyproject = @'
[build-system]
requires = ["hatchling>=1.24.2"]
build-backend = "hatchling.build"

[project]
name = "perfect-coder"
version = "0.3.0"
description = "Perfect Coder: plan → build → verify → ship"
readme = "README.md"
requires-python = ">=3.11"
authors = [{name="System Architect"}]
dependencies = [
  "typer>=0.12.3",
  "rich>=13.7.1",
  "icontract>=2.6.6",
  "PyYAML>=6.0.2",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.2",
  "pytest-randomly>=3.15.0",
  "pytest-xdist>=3.6.1",
  "hypothesis>=6.112.0",
  "coverage[toml]>=7.6.1",
  "ruff>=0.6.9",
  "mypy>=1.11.2",
  "bandit>=1.7.9",
  "pip-audit>=2.7.3",
  "radon>=6.0.1",
  "mutatest>=3.1.0",
  "crosshair-tool>=0.0.63",
  "pip-licenses>=5.0.0",
]

[project.scripts]
forge = "forge.__main__:app"

[tool.ruff]
line-length = 100
target-version = "py311"
extend-select = ["I"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true

[tool.pytest.ini_options]
addopts = "-q --maxfail=1 --disable-warnings --color=yes --cov=forge --cov-report=term-missing --cov-report=xml --cov-fail-under=85"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["forge"]

[tool.coverage.report]
show_missing = true
skip_covered = true
'@
Write-Text (Join-Path $ProjectDir "pyproject.toml") $pyproject

# ---------- External gates config ----------
$gates_yaml = @'
version: 1
gates:
  - name: format
    cmd: ["ruff","format","--check"]
  - name: lint
    cmd: ["ruff","check"]
  - name: types
    cmd: ["mypy","src"]
  - name: tests
    cmd: ["pytest","-n","auto","-q"]
  - name: security
    cmd: ["bandit","-r","src"]
  - name: vulns
    cmd: ["python","-m","pip_audit","-f","json","-o","artifacts/audit.json"]
  - name: complexity
    cmd: ["python","tools/complexity.py","--cc-max","C","--mi-min","B","--path","src"]
  - name: mutation
    cmd: ["python","tools/mut_gate.py","--src","src/forge","--tests","tests"]
  - name: crosshair
    cmd: ["python","-m","crosshair","check","src/forge"]
fail_fast: true
'@
Write-Text (Join-Path $ProjectDir "config\gates.yaml") $gates_yaml

# ---------- Tools: provenance ----------
$provenance_py = @'
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

SKIP_DIRS = {".git", ".venv", "artifacts", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def walk(root: Path) -> list[dict[str,str]]:
    items: list[dict[str,str]] = []
    for dp, dn, fn in os.walk(root):
        d = Path(dp)
        if any(part in SKIP_DIRS for part in d.parts): continue
        for name in fn:
            p = d / name
            if p.is_file():
                items.append({"path": str(p.relative_to(root)).replace("\\","/"), "sha256": sha256_file(p)})
    return sorted(items, key=lambda x: x["path"])

def git_rev() -> str | None:
    try:
        out = subprocess.check_output(["git","rev-parse","HEAD"], text=True).strip()
        return out
    except Exception:
        return None

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="artifacts/provenance.json")
    args = ap.parse_args()
    root = Path(args.root).resolve()
    items = walk(root)
    doc = {
        "schema": "prov.simple.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cwd": str(root),
        "git_commit": git_rev(),
        "files": items,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(f"Provenance → {out}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'@
Write-Text (Join-Path $ProjectDir "tools\provenance.py") $provenance_py

# ---------- Tools: license inventory ----------
$licenses_py = @'
from __future__ import annotations
import json, subprocess, sys

def main() -> int:
    try:
        out = subprocess.check_output(["python","-m","piplicenses","--format","json"], text=True)
        data = json.loads(out)
    except Exception as e:
        print(f"pip-licenses failed: {e}")
        return 2
    doc = {
        "generator": "tools/licenses.py",
        "packages": [
            {"name": x.get("Name"), "version": x.get("Version"), "license": x.get("License")}
            for x in data
        ],
    }
    print(json.dumps(doc, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'@
Write-Text (Join-Path $ProjectDir "tools\licenses.py") $licenses_py

# ---------- Tools: YAML-driven gate runner ----------
$gate_runner_py = @'
from __future__ import annotations
import argparse, subprocess, sys, yaml
from pathlib import Path

def run(cmd: list[str]) -> int:
    return subprocess.call(cmd, shell=False)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/gates.yaml")
    args = ap.parse_args()
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"Missing gate config: {cfg_path}")
        return 2
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    fail_fast = bool(cfg.get("fail_fast", True))
    failures = 0
    for gate in cfg.get("gates", []):
        name = gate.get("name","unnamed")
        cmd = gate.get("cmd",[])
        print(f"[gate] {name}: {' '.join(cmd)}")
        code = run([str(x) for x in cmd])
        if code != 0:
            print(f"[fail] {name} → {code}")
            failures += 1
            if fail_fast: break
        else:
            print(f"[ok] {name}")
    return 0 if failures == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
'@
Write-Text (Join-Path $ProjectDir "tools\gate_runner.py") $gate_runner_py

# ---------- Docker packaging ----------
$dockerfile = @'
# syntax=docker/dockerfile:1
FROM python:3.11-slim AS build
WORKDIR /w
COPY . /w
RUN python -m pip install --upgrade pip && pip install -e ".[dev]" && python -m pip install build \
 && python -m build --wheel --outdir /w/dist

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=build /w/dist /app/dist
# Install only the wheel for runtime minimalism
RUN python -m pip install --no-cache-dir /app/dist/*.whl
ENTRYPOINT ["forge"]
CMD ["plan","--spec","Container smoke"]
'@
Write-Text (Join-Path $ProjectDir "Dockerfile") $dockerfile

# ---------- Extend CLI with new cmds: gate/provenance/licenses/docker ----------
$forge_main = @'
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from rich.table import Table

app = typer.Typer(help="Perfect Coder: plan → build → verify → ship")

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
ART.mkdir(parents=True, exist_ok=True)

def _run(cmd: List[str]) -> int:
    return subprocess.run(cmd, shell=False).returncode

def _ok(tag: str) -> None:
    print(f"[green]✔ {tag}[/green]")

def _fail(tag: str) -> None:
    print(f"[red]✖ {tag}[/red]")

@app.command()
def plan(
    spec: Optional[str] = typer.Option(None, "--spec", "-s", help="Natural language spec"),
    spec_file: Optional[Path] = typer.Option(None, "--spec-file", "-f", exists=False, help="Spec file"),
) -> None:
    text = spec.strip() if spec else (spec_file.read_text(encoding="utf-8").strip() if spec_file and spec_file.exists() else "Initialize and smoke.")
    plan = {
        "inputs": {"spec": text[:2000]},
        "goals": [
            "Type safety (mypy)",
            "Property tests (Hypothesis)",
            "Coverage >= 85%",
            "No Bandit HIGH",
            "Lint clean (ruff)",
            "No known vulns (pip-audit)",
            "Complexity budgets (radon)",
            "0 mutation survivors (mutatest)",
            "Basic contracts hold (CrossHair)",
        ],
        "artifacts": ["wheel", "coverage report", "sbom.json", "audit.json", "provenance.json", "licenses.json"],
        "commands": ["forge build", "forge gate", "forge sbom", "forge provenance", "forge licenses"],
    }
    (ART / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    _ok("Plan → artifacts/plan.json")
    table = Table(title="Plan")
    for g in plan["goals"]: table.add_row(g)
    print(table)

@app.command()
def build() -> None:
    code = _run(["python","-m","pip","install","--upgrade","build"])
    if code != 0: _fail("pip install build"); raise typer.Exit(code)
    ART.joinpath("dist").mkdir(parents=True, exist_ok=True)
    code = _run(["python","-m","build","--wheel","--outdir", str(ART/"dist")])
    if code != 0: _fail("build wheel"); raise typer.Exit(code)
    _ok("Wheel built")

@app.command()
def verify() -> None:
    # Keep the lightweight local core; heavy gates live in 'gate'
    gates = [
        (["ruff","format","--check"], "format"),
        (["ruff","check"], "lint"),
        (["mypy","src"], "types"),
        (["pytest","-n","auto","-q"], "tests"),
        (["bandit","-r","src"], "security"),
    ]
    failed = False
    for cmd, tag in gates:
        if _run(cmd) == 0: _ok(tag)
        else: _fail(tag); failed = True
    if failed: raise typer.Exit(1)
    _ok("Core gates passed")

@app.command()
def gate(config: Path = typer.Option(Path("config/gates.yaml"), "--config", "-c", help="Gate config YAML")) -> None:
    code = _run(["python","tools/gate_runner.py","--config", str(config)])
    if code != 0: _fail("gates"); raise typer.Exit(code)
    _ok("All configured gates")

@app.command()
def sbom() -> None:
    code = _run(["python","tools/sbom.py"])
    if code != 0: _fail("sbom"); raise typer.Exit(code)
    _ok("sbom printed")

@app.command()
def provenance(out: Path = typer.Option(Path("artifacts/provenance.json"), "--out")) -> None:
    code = _run(["python","tools/provenance.py","--root",".","--out", str(out)])
    if code != 0: _fail("provenance"); raise typer.Exit(code)
    _ok(f"provenance → {out}")

@app.command()
def licenses(out: Path = typer.Option(Path("artifacts/licenses.json"), "--out")) -> None:
    try:
        p = subprocess.check_output(["python","tools/licenses.py"], text=True)
        (ART / out.name).write_text(p, encoding="utf-8")
        _ok(f"licenses → {ART/out.name}")
    except Exception:
        _fail("licenses"); raise typer.Exit(2)

@app.command()
def docker(tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Image tag, defaults to local/perfect-coder:latest")) -> None:
    image = tag or "local/perfect-coder:latest"
    code = _run(["docker","build","-t", image, "."])
    if code != 0: _fail("docker build"); raise typer.Exit(code)
    _ok(f"Docker image built: {image}")

@app.command()
def ship(target: Optional[str] = typer.Option(None, "--target", help="Distribution target hint")) -> None:
    meta = {"target": target or "local", "artifacts": [p.name for p in ART.glob("**/*") if p.is_file()]}
    (ART / "ship.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    _ok("Ship → artifacts/ship.json")
'@
Write-Text (Join-Path $ProjectDir "src\forge\__main__.py") $forge_main

# ---------- CI: add provenance, licenses, and Docker build ----------
$workflow = @'
name: ci
on:
  push: { branches: ["**"] }
  pull_request:

jobs:
  build-test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: "pip" }
      - name: Install package + dev deps
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Ruff format
        run: ruff format --check
      - name: Ruff lint
        run: ruff check
      - name: MyPy
        run: mypy src
      - name: Tests
        run: pytest -n auto -q
      - name: Bandit
        run: bandit -r src
      - name: Vuln scan
        run: python -m pip_audit -f json -o artifacts/audit.json
      - name: Complexity
        run: python tools/complexity.py --cc-max C --mi-min B --path src
      - name: Mutation
        run: python tools/mut_gate.py --src src/forge --tests tests
      - name: SBOM
        run: python tools/sbom.py > sbom.json
      - name: Provenance
        run: python tools/provenance.py --root . --out artifacts/provenance.json
      - name: Licenses
        run: python tools/licenses.py > artifacts/licenses.json
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ci-artifacts
          path: |
            artifacts/**
            sbom.json
            .coverage
  docker:
    runs-on: ubuntu-latest
    needs: build-test
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t local/perfect-coder:ci .
      - name: Save image
        run: docker save local/perfect-coder:ci | gzip > perfect-coder-image.tar.gz
      - name: Upload image artifact
        uses: actions/upload-artifact@v4
        with:
          name: docker-image
          path: perfect-coder-image.tar.gz
'@
Write-Text (Join-Path $ProjectDir ".github\workflows\ci.yml") $workflow

# ---------- README delta ----------
$readmePath = Join-Path $ProjectDir "README.md"
if (Test-Path $readmePath) {
  $readme = (Get-Content -Raw -Path $readmePath)
  $addon = @'

## Gates via config
`config/gates.yaml` controls what `forge gate` runs. Edit to add or reorder checks.

## Provenance and licenses
- `forge provenance` → writes `artifacts/provenance.json` with SHA-256 file hashes and git commit
- `forge licenses`   → writes `artifacts/licenses.json` with dependency licenses

## Docker
- `forge docker -t local/perfect-coder:latest` builds a runnable image
  - Run: `docker run --rm local/perfect-coder:latest plan --spec "hello"`

'@
  Write-Text $readmePath ($readme + $addon)
}

Write-Host "`nFortification complete." -ForegroundColor Green
Write-Host "Next:"
Write-Host " - Activate venv and reinstall: pip install -e "".[dev]"""
Write-Host " - Run: forge gate; forge provenance; forge licenses; forge docker"
```
Run in PowerShell from your repo root:
`pwsh -File .\Amplify-PerfectCoder.ps1 -ProjectDir "$PWD"`

````powershell
<# Amplify-PerfectCoder.ps1
Adds spec compiler, module scaffolder, docs, license policy gate, profiling, and optional EXE packaging.

New CLI:
  forge new --name mymod [--force]         # scaffold module + tests
  forge spec --in spec.yaml                # compile YAML spec -> plan + stubs
  forge docs                               # build docs via pdoc → site/
  forge licensecheck                        # enforce license allow/deny policy
  forge profile                             # cProfile over pytest; writes artifacts/profile.*
  forge package                             # PyInstaller onefile EXE (optional, local)

Usage:
  pwsh -File .\Amplify-PerfectCoder.ps1 -ProjectDir "C:\path\perfect-coder"
Then:
  py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  pip install -e ".[dev]"
  pre-commit install
  forge new --name demo
  forge docs
  forge licensecheck
  forge profile
  forge package
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)][string]$ProjectDir = (Join-Path $PWD ""),
  [switch]$Force
)

function Assert-Dir($Path) { if (-not (Test-Path $Path)) { throw "Path not found: $Path" } }
function Write-Text($Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
  Write-Host "Wrote $Path"
}

Assert-Dir $ProjectDir

# ---------- Update pyproject: add pydantic, pdoc, pyinstaller ----------
$pyproject = @'
[build-system]
requires = ["hatchling>=1.24.2"]
build-backend = "hatchling.build"

[project]
name = "perfect-coder"
version = "0.4.0"
description = "Perfect Coder: plan → build → verify → ship"
readme = "README.md"
requires-python = ">=3.11"
authors = [{name="System Architect"}]
dependencies = [
  "typer>=0.12.3",
  "rich>=13.7.1",
  "icontract>=2.6.6",
  "PyYAML>=6.0.2",
  "pydantic>=2.8.2",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.2",
  "pytest-randomly>=3.15.0",
  "pytest-xdist>=3.6.1",
  "hypothesis>=6.112.0",
  "coverage[toml]>=7.6.1",
  "ruff>=0.6.9",
  "mypy>=1.11.2",
  "bandit>=1.7.9",
  "pip-audit>=2.7.3",
  "radon>=6.0.1",
  "mutatest>=3.1.0",
  "crosshair-tool>=0.0.63",
  "pip-licenses>=5.0.0",
  "pdoc>=14.4.0",
  "pyinstaller>=6.9.0",
]

[project.scripts]
forge = "forge.__main__:app"

[tool.ruff]
line-length = 100
target-version = "py311"
extend-select = ["I"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_ignores = true
warn_redundant_casts = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
no_implicit_optional = true

[tool.pytest.ini_options]
addopts = "-q --maxfail=1 --disable-warnings --color=yes --cov=forge --cov-report=term-missing --cov-report=xml --cov-fail-under=85"
testpaths = ["tests"]

[tool.coverage.run]
branch = true
source = ["forge"]

[tool.coverage.report]
show_missing = true
skip_covered = true
'@
Write-Text (Join-Path $ProjectDir "pyproject.toml") $pyproject

# ---------- Config: license policy ----------
$licenses_yaml = @'
version: 1
allow:
  - MIT
  - BSD-2-Clause
  - BSD-3-Clause
  - Apache-2.0
  - ISC
  - PSF-2.0
warn:
  - MPL-2.0
deny:
  - GPL-3.0-only
  - GPL-3.0-or-later
  - AGPL-3.0
  - LGPL-3.0
'@
Write-Text (Join-Path $ProjectDir "config\licenses.yaml") $licenses_yaml

# ---------- Tools: spec compiler (YAML → stubs + plan) ----------
$spec_compiler = @'
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any, Dict
import yaml

TEMPLATE_PY = """\
from __future__ import annotations
from typing import *
# Generated from spec: {spec_name}

def {func_name}({params}) -> {returns}:
    \"\"\"{doc}\"\"\"
    raise NotImplementedError("TODO: implement {func_name}")
"""

TEMPLATE_TEST = """\
from __future__ import annotations
import pytest
from forge.generated.{mod_name} import {func_name}

def test_{func_name}_stub_exists():
    with pytest.raises(NotImplementedError):
        {func_name}({call_args})
"""

def snake(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()

def compile_spec(in_path: Path, out_dir: Path, art_dir: Path) -> int:
    data: Dict[str, Any] = yaml.safe_load(in_path.read_text(encoding="utf-8"))
    name = data.get("name","generated")
    mod_name = snake(name)
    pkg_dir = out_dir / "forge" / "generated"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "__init__.py").write_text('\"\"\"generated stubs\"\"\"', encoding="utf-8")

    # Plan
    plan = {
        "spec_name": name,
        "functions": [],
    }

    for f in data.get("functions", []):
        fname = f.get("name","func")
        params = f.get("params","")
        returns = f.get("returns","None")
        doc = f.get("doc","")
        src = TEMPLATE_PY.format(spec_name=name, func_name=fname, params=params, returns=returns, doc=doc)
        (pkg_dir / f"{mod_name}.py").write_text(src, encoding="utf-8")

        call_args = ", ".join([p.split(":")[0].strip() or "None" for p in params.split(",") if p.strip()]) if params else ""
        test_src = TEMPLATE_TEST.format(mod_name=mod_name, func_name=fname, call_args=call_args)
        tests_dir = out_dir.parent / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / f"test_{mod_name}_{fname}.py").write_text(test_src, encoding="utf-8")

        plan["functions"].append({"name": fname, "module": f"forge.generated.{mod_name}"})

    art_dir.mkdir(parents=True, exist_ok=True)
    (art_dir / "spec_plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(f"Generated stubs in forge/generated/{mod_name}.py and tests/")
    return 0

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True, help="YAML spec file")
    ap.add_argument("--src", default="src", help="Source root")
    ap.add_argument("--artifacts", default="artifacts", help="Artifacts dir")
    args = ap.parse_args()
    exit(compile_spec(Path(args.inp), Path(args.src), Path(args.artifacts)))
'@
Write-Text (Join-Path $ProjectDir "tools\spec_compiler.py") $spec_compiler

# ---------- Tools: docs generator ----------
$docs_gen = @'
from __future__ import annotations
import subprocess, sys, os
def main() -> int:
    os.makedirs("site", exist_ok=True)
    return subprocess.call([sys.executable, "-m", "pdoc", "-o", "site", "src/forge"])
if __name__ == "__main__":
    sys.exit(main())
'@
Write-Text (Join-Path $ProjectDir "tools\docs_gen.py") $docs_gen

# ---------- Tools: license policy checker ----------
$license_policy = @'
from __future__ import annotations
import json, sys, yaml
from pathlib import Path

def main() -> int:
    cfg = yaml.safe_load(Path("config/licenses.yaml").read_text(encoding="utf-8"))
    allow = set(cfg.get("allow", []))
    warn = set(cfg.get("warn", []))
    deny = set(cfg.get("deny", []))

    data = json.loads(Path("artifacts/licenses.json").read_text(encoding="utf-8"))
    bad = []
    warnings = []
    for pkg in data.get("packages", []):
        lic = (pkg.get("license") or "").strip()
        name = pkg.get("name")
        if lic in deny:
            bad.append(f"{name}: {lic}")
        elif lic in warn:
            warnings.append(f"{name}: {lic}")
        elif allow and lic not in allow:
            warnings.append(f"{name}: {lic or 'UNKNOWN'} (not in allow list)")
    if warnings:
        print("License warnings:")
        for w in sorted(warnings): print(" -", w)
    if bad:
        print("License violations:")
        for b in sorted(bad): print(" -", b)
        return 3
    print("License policy OK.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'@
Write-Text (Join-Path $ProjectDir "tools\license_policy.py") $license_policy

# ---------- Tools: pytest profiling ----------
$profile_tests = @'
from __future__ import annotations
import cProfile, pstats, io, subprocess, sys, os
from pathlib import Path

def main() -> int:
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    prof_path = "artifacts/profile.stats"
    pycmd = [sys.executable, "-m", "pytest", "-q"]
    pr = cProfile.Profile()
    pr.enable()
    code = subprocess.call(pycmd)
    pr.disable()
    pr.dump_stats(prof_path)
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
    ps.print_stats(50)
    Path("artifacts/profile.txt").write_text(s.getvalue(), encoding="utf-8")
    print(f"Profile → {prof_path} and artifacts/profile.txt")
    return code

if __name__ == "__main__":
    sys.exit(main())
'@
Write-Text (Join-Path $ProjectDir "tools\profile_tests.py") $profile_tests

# ---------- Update CLI with new commands ----------
$forge_main = @'
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional

import typer
from rich import print

app = typer.Typer(help="Perfect Coder: plan → build → verify → ship")

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"
SRC = ROOT / "src"
ART.mkdir(parents=True, exist_ok=True)

def _run(cmd: List[str]) -> int:
    return subprocess.run(cmd, shell=False).returncode

def _ok(tag: str) -> None:
    print(f"[green]✔ {tag}[/green]")

def _fail(tag: str) -> None:
    print(f"[red]✖ {tag}[/red]")

@app.command()
def plan(
    spec: Optional[str] = typer.Option(None, "--spec", "-s"),
    spec_file: Optional[Path] = typer.Option(None, "--spec-file", "-f", exists=False),
) -> None:
    text = spec.strip() if spec else (spec_file.read_text(encoding="utf-8").strip() if spec_file and spec_file.exists() else "Initialize and smoke.")
    plan = {
        "inputs": {"spec": text[:2000]},
        "goals": [
            "Types clean (mypy)",
            "Property tests (Hypothesis)",
            "Coverage >= 85%",
            "No Bandit HIGH",
            "Lint clean (ruff)",
            "No known vulns (pip-audit)",
            "Complexity budgets (radon)",
            "0 mutation survivors (mutatest)",
            "Basic contracts hold (CrossHair)",
            "Licenses policy OK",
            "Docs build succeeds",
        ],
        "commands": ["forge build", "forge gate", "forge licenses", "forge licensecheck", "forge docs"],
    }
    (ART / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    _ok("Plan → artifacts/plan.json")

@app.command()
def build() -> None:
    if _run(["python","-m","pip","install","--upgrade","build"]) != 0: _fail("pip build"); raise typer.Exit(1)
    (ART/"dist").mkdir(parents=True, exist_ok=True)
    if _run(["python","-m","build","--wheel","--outdir", str(ART/"dist")]) != 0: _fail("wheel"); raise typer.Exit(1)
    _ok("Wheel built")

@app.command()
def verify() -> None:
    gates = [
        (["ruff","format","--check"], "format"),
        (["ruff","check"], "lint"),
        (["mypy","src"], "types"),
        (["pytest","-n","auto","-q"], "tests"),
        (["bandit","-r","src"], "security"),
    ]
    failed = False
    for cmd, tag in gates:
        if _run(cmd) == 0: _ok(tag)
        else: _fail(tag); failed = True
    if failed: raise typer.Exit(1)
    _ok("Core gates passed")

@app.command()
def gate(config: Path = typer.Option(Path("config/gates.yaml"), "--config", "-c")) -> None:
    if _run(["python","tools/gate_runner.py","--config", str(config)]) != 0: _fail("gates"); raise typer.Exit(1)
    _ok("All configured gates")

@app.command()
def sbom() -> None:
    if _run(["python","tools/sbom.py"]) != 0: _fail("sbom"); raise typer.Exit(1)
    _ok("sbom printed")

@app.command()
def provenance(out: Path = typer.Option(Path("artifacts/provenance.json"), "--out")) -> None:
    if _run(["python","tools/provenance.py","--root",".","--out", str(out)]) != 0: _fail("provenance"); raise typer.Exit(1)
    _ok(f"provenance → {out}")

@app.command()
def licenses(out: Path = typer.Option(Path("artifacts/licenses.json"), "--out")) -> None:
    try:
        p = subprocess.check_output(["python","tools/licenses.py"], text=True)
        (ART / out.name).write_text(p, encoding="utf-8")
        _ok(f"licenses → {ART/out.name}")
    except Exception:
        _fail("licenses"); raise typer.Exit(2)

@app.command()
def licensecheck() -> None:
    # Requires artifacts/licenses.json (run `forge licenses` first)
    if _run(["python","tools/license_policy.py"]) != 0: _fail("license policy"); raise typer.Exit(3)
    _ok("license policy")

@app.command()
def docs() -> None:
    if _run(["python","tools/docs_gen.py"]) != 0: _fail("docs"); raise typer.Exit(1)
    _ok("docs → site/")

@app.command()
def new(name: str = typer.Option(..., "--name", "-n", help="Module name"), force: bool = typer.Option(False, "--force")) -> None:
    mod = name.strip().lower().replace("-", "_")
    pkg = SRC / "forge" / "plugins"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text("\"\"\"plugins\"\"\"", encoding="utf-8") if not (pkg/"__init__.py").exists() else None
    py = pkg / f"{mod}.py"
    test = ROOT / "tests" / f"test_{mod}.py"
    if (py.exists() or test.exists()) and not force:
        _fail("files exist; use --force"); raise typer.Exit(2)
    py.write_text(f"from __future__ import annotations\n\n"
                  f"def {mod}_hello(name: str) -> str:\n"
                  f"    \"\"\"Return a greeting for {mod}.\"\"\"\n"
                  f"    return f\"{mod}: {{name}}\"\n", encoding="utf-8")
    test.parent.mkdir(parents=True, exist_ok=True)
    test.write_text(f"from forge.plugins.{mod} import {mod}_hello\n\ndef test_{mod}_hello():\n"
                    f"    assert {mod}_hello('x').endswith('x')\n", encoding="utf-8")
    _ok(f"scaffolded forge/plugins/{mod}.py and tests/test_{mod}.py")

@app.command()
def spec(inp: Path = typer.Option(..., "--in", "-i", help="Spec YAML file")) -> None:
    if _run(["python","tools/spec_compiler.py","--in", str(inp), "--src", "src", "--artifacts", "artifacts"]) != 0:
        _fail("spec compile"); raise typer.Exit(1)
    _ok("spec compiled")

@app.command()
def profile() -> None:
    if _run(["python","tools/profile_tests.py"]) != 0: _fail("profile"); raise typer.Exit(1)
    _ok("profile done")

@app.command()
def docker(tag: Optional[str] = typer.Option(None, "--tag", "-t")) -> None:
    image = tag or "local/perfect-coder:latest"
    if _run(["docker","build","-t", image, "."]) != 0: _fail("docker build"); raise typer.Exit(1)
    _ok(f"Docker image built: {image}")

@app.command()
def package(name: str = typer.Option("forge_cli", "--name"), onefile: bool = typer.Option(True, "--onefile/--no-onefile")) -> None:
    args = ["pyinstaller", "-n", name, "-p", "src", "src/forge/__main__.py"]
    if onefile: args.insert(1, "--onefile")
    code = _run(args)
    if code != 0: _fail("pyinstaller"); raise typer.Exit(code)
    _ok("EXE packaged (see dist/)")
'@
Write-Text (Join-Path $ProjectDir "src\forge\__main__.py") $forge_main

# ---------- Sample spec YAML ----------
$spec_sample = @'
name: Example Utilities
functions:
  - name: join_nonempty
    params: "a: str, b: str, sep: str = '-'"
    returns: "str"
    doc: "Join a and b with sep if both nonempty, else return the nonempty one."
'
Write-Text (Join-Path $ProjectDir "specs\example.yaml") $spec_sample

# ---------- CI: build docs and check license policy ----------
$workflow = @'
name: ci
on:
  push: { branches: ["**"] }
  pull_request:

jobs:
  build-test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: "pip" }
      - name: Install package + dev deps
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      - name: Ruff format
        run: ruff format --check
      - name: Ruff lint
        run: ruff check
      - name: MyPy
        run: mypy src
      - name: Tests
        run: pytest -n auto -q
      - name: Bandit
        run: bandit -r src
      - name: Vuln scan
        run: python -m pip_audit -f json -o artifacts/audit.json
      - name: Complexity
        run: python tools/complexity.py --cc-max C --mi-min B --path src
      - name: Mutation
        run: python tools/mut_gate.py --src src/forge --tests tests
      - name: SBOM
        run: python tools/sbom.py > sbom.json
      - name: Provenance
        run: python tools/provenance.py --root . --out artifacts/provenance.json
      - name: Licenses dump
        run: python tools/licenses.py > artifacts/licenses.json
      - name: License policy
        run: python tools/license_policy.py
      - name: Docs
        run: python tools/docs_gen.py
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ci-artifacts
          path: |
            artifacts/**
            sbom.json
            site/**
  docker:
    runs-on: ubuntu-latest
    needs: build-test
    permissions: { contents: read }
    steps:
      - uses: actions/checkout@v4
      - name: Build image
        run: docker build -t local/perfect-coder:ci .
      - name: Save image
        run: docker save local/perfect-coder:ci | gzip > perfect-coder-image.tar.gz
      - name: Upload image artifact
        uses: actions/upload-artifact@v4
        with:
          name: docker-image
          path: perfect-coder-image.tar.gz
'@
Write-Text (Join-Path $ProjectDir ".github\workflows\ci.yml") $workflow

# ---------- README delta ----------
$readmePath = Join-Path $ProjectDir "README.md"
if (Test-Path $readmePath) {
  $readme = (Get-Content -Raw -Path $readmePath)
  $addon = @'

## New commands
- `forge new -n NAME` → scaffold module + tests
- `forge spec -i specs/example.yaml` → generate stubs from YAML spec
- `forge docs` → generate API docs to `site/`
- `forge licensecheck` → enforce `config/licenses.yaml`
- `forge profile` → cProfile over tests → `artifacts/profile.*`
- `forge package` → PyInstaller EXE in `dist/`

### Example spec (specs/example.yaml)
```yaml
name: Example Utilities
functions:
  - name: join_nonempty
    params: "a: str, b: str, sep: str = '-'"
    returns: "str"
    doc: "Join a and b with sep if both nonempty, else return the nonempty one."
````

'@
Write-Text \$readmePath (\$readme + \$addon)
}

Write-Host "\`nAmplification complete." -ForegroundColor Green
Write-Host "Next:"
Write-Host "  - Activate venv and run: pip install -e "".\[dev]"""
Write-Host "  - Try: forge new -n demo; forge docs; forge licensecheck; forge profile; forge package"

```
```
