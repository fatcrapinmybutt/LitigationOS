<# Amplify-PerfectCoder.ps1 — FIXED
Adds: spec compiler, module scaffolder, docs, license policy gate, profiling, optional EXE packaging.
New forge cmds: new, spec, docs, licensecheck, profile, package.
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

# pyproject deps
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

# license policy config
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

# tools: spec compiler
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

    plan = {"spec_name": name, "functions": []}

    for f in data.get("functions", []):
        fname = f.get("name","func")
        params = f.get("params","")
        returns = f.get("returns","None")
        doc = f.get("doc","")
        src = TEMPLATE_PY.format(spec_name=name, func_name=fname, params=params, returns=returns, doc=doc)
        (pkg_dir / f"{mod_name}.py").write_text(src, encoding="utf-8")

        call_args = ", ".join([p.split(":")[0].strip() or "None" for p in params.split(",") if p.strip()]) if params else ""
        tests_dir = out_dir.parent / "tests"
        tests_dir.mkdir(parents=True, exist_ok=True)
        test_src = TEMPLATE_TEST.format(mod_name=mod_name, func_name=fname, call_args=call_args)
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

# tools: docs generator
$docs_gen = @'
from __future__ import annotations
import os, subprocess, sys

def main() -> int:
    os.makedirs("site", exist_ok=True)
    return subprocess.call([sys.executable, "-m", "pdoc", "-o", "site", "src/forge"])

if __name__ == "__main__":
    sys.exit(main())
'@
Write-Text (Join-Path $ProjectDir "tools\docs_gen.py") $docs_gen

# tools: license policy checker
$license_policy = @'
from __future__ import annotations
import json, yaml
from pathlib import Path

def main() -> int:
    cfg = yaml.safe_load(Path("config/licenses.yaml").read_text(encoding="utf-8"))
    allow = set(cfg.get("allow", []))
    warn = set(cfg.get("warn", []))
    deny = set(cfg.get("deny", []))

    data = json.loads(Path("artifacts/licenses.json").read_text(encoding="utf-8"))
    bad, warnings = [], []
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
        print("License warnings:"); [print(" -", w) for w in sorted(warnings)]
    if bad:
        print("License violations:"); [print(" -", b) for b in sorted(bad)]
        return 3
    print("License policy OK."); return 0

if __name__ == "__main__":
    raise SystemExit(main())
'@
Write-Text (Join-Path $ProjectDir "tools\license_policy.py") $license_policy

# tools: pytest profiling
$profile_tests = @'
from __future__ import annotations
import cProfile, pstats, io, subprocess, sys
from pathlib import Path

def main() -> int:
    Path("artifacts").mkdir(parents=True, exist_ok=True)
    prof_path = "artifacts/profile.stats"
    pr = cProfile.Profile()
    pr.enable()
    code = subprocess.call([sys.executable, "-m", "pytest", "-q"])
    pr.disable()
    pr.dump_stats(prof_path)
    s = io.StringIO()
    pstats.Stats(pr, stream=s).sort_stats("cumtime").print_stats(50)
    Path("artifacts/profile.txt").write_text(s.getvalue(), encoding="utf-8")
    print(f"Profile → {prof_path} and artifacts/profile.txt")
    return code

if __name__ == "__main__":
    raise SystemExit(main())
'@
Write-Text (Join-Path $ProjectDir "tools\profile_tests.py") $profile_tests

# forge CLI add cmds
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
    if _run(["python","tools/license_policy.py"]) != 0: _fail("license policy"); raise typer.Exit(3)
    _ok("license policy")

@app.command()
def docs() -> None:
    if _run(["python","tools/docs_gen.py"]) != 0: _fail("docs"); raise typer.Exit(1)
    _ok("docs → site/")

@app.command()
def new(name: str = typer.Option(..., "--name", "-n"), force: bool = typer.Option(False, "--force")) -> None:
    mod = name.strip().lower().replace("-", "_")
    pkg = SRC / "forge" / "plugins"; pkg.mkdir(parents=True, exist_ok=True)
    init = pkg / "__init__.py"
    if not init.exists(): init.write_text('"""plugins"""', encoding="utf-8")
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
def spec(inp: Path = typer.Option(..., "--in", "-i")) -> None:
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
    _ok("EXE packaged (dist/)")
'@
Write-Text (Join-Path $ProjectDir "src\forge\__main__.py") $forge_main

# sample spec
$spec_sample = @'
name: Example Utilities
functions:
  - name: join_nonempty
    params: "a: str, b: str, sep: str = '-'"
    returns: "str"
    doc: "Join a and b with sep if both nonempty, else return the nonempty one."
'@
Write-Text (Join-Path $ProjectDir "specs\example.yaml") $spec_sample

# CI update
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

# README delta
$readmePath = Join-Path $ProjectDir "README.md"
if (Test-Path $readmePath) {
  $readme = (Get-Content -Raw -Path $readmePath)
  $addon = @'

## New commands
- `forge new -n NAME` → scaffold module + tests
- `forge spec -i specs/example.yaml` → generate stubs from YAML spec
- `forge docs` → API docs to `site/`
- `forge licensecheck` → enforce `config/licenses.yaml`
- `forge profile` → cProfile over tests → `artifacts/profile.*`
- `forge package` → PyInstaller EXE in `dist/`
'@
  Write-Text $readmePath ($readme + $addon)
}

Write-Host "`nAmplification complete." -ForegroundColor Green
Write-Host "Run: pip install -e "".[dev]""; forge new -n demo; forge docs; forge licensecheck; forge profile; forge package"
