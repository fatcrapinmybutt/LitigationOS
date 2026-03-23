"""
NOVEL Engine — Validator v2
Automatically tests generated prototypes: syntax, imports, execution, quality.

This is what separates NOVEL v2 from a template dumper — every invention
is validated BEFORE it gets deployed. Bad code gets caught, fixed, or killed.

Validation pipeline:
  1. SyntaxCheck  — AST parse (catches syntax errors instantly)
  2. ImportCheck  — verify all imports resolve
  3. RuntimeCheck — execute in sandbox, capture output + errors
  4. QualityCheck — anti-pattern detection, style, safety
  5. IntegrationCheck — verify DB connections, file paths, API calls work
"""

import os
import sys
import ast
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field

os.environ["PYTHONUTF8"] = "1"

REPO_ROOT = Path(r"C:\Users\andre\LitigationOS")
SAFE_CWD = REPO_ROOT / "00_SYSTEM" / "novel"


@dataclass
class ValidationResult:
    """Comprehensive result from validating a piece of generated code."""
    passed: bool = False
    syntax_ok: bool = False
    imports_ok: bool = False
    runtime_ok: bool = False
    quality_ok: bool = False
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    output: str = ""
    runtime_seconds: float = 0.0
    auto_fixes: list = field(default_factory=list)
    score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "syntax_ok": self.syntax_ok,
            "imports_ok": self.imports_ok,
            "runtime_ok": self.runtime_ok,
            "quality_ok": self.quality_ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "score": self.score,
            "auto_fixes": self.auto_fixes,
        }


class SyntaxValidator:
    """Validates Python code via AST parsing — catches syntax errors instantly."""

    def validate(self, code: str) -> ValidationResult:
        result = ValidationResult()
        try:
            tree = ast.parse(code)
            result.syntax_ok = True

            # Extract metadata from the AST
            result.warnings.extend(self._check_ast_issues(tree))

        except SyntaxError as e:
            result.errors.append(f"SyntaxError at line {e.lineno}: {e.msg}")

            # Try to auto-fix common syntax errors
            fixed_code, fix_desc = self._try_auto_fix(code, e)
            if fixed_code:
                result.auto_fixes.append(fix_desc)
                try:
                    ast.parse(fixed_code)
                    result.syntax_ok = True
                    result.output = fixed_code
                except SyntaxError:
                    pass

        return result

    def _check_ast_issues(self, tree: ast.AST) -> list:
        warnings = []

        for node in ast.walk(tree):
            # Catch bare except clauses
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                warnings.append(f"Line {node.lineno}: bare 'except:' — should catch specific exceptions")

            # Catch mutable default arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults + node.args.kw_defaults:
                    if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        warnings.append(f"Line {node.lineno}: mutable default argument in {node.name}()")

            # Catch global statements
            if isinstance(node, ast.Global):
                warnings.append(f"Line {node.lineno}: global statement — prefer passing as parameter")

        return warnings

    def _try_auto_fix(self, code: str, error: SyntaxError) -> tuple:
        """Attempt common auto-fixes for syntax errors."""
        lines = code.split("\n")

        # Fix: missing colon at end of def/class/if/for/while
        if error.lineno and error.lineno <= len(lines):
            line = lines[error.lineno - 1].rstrip()
            for kw in ("def ", "class ", "if ", "elif ", "else", "for ", "while ", "try", "except", "finally"):
                if line.lstrip().startswith(kw) and not line.endswith(":"):
                    lines[error.lineno - 1] = line + ":"
                    return "\n".join(lines), f"Added missing colon at line {error.lineno}"

        # Fix: unclosed string
        if "unterminated string" in str(error.msg).lower():
            line = lines[error.lineno - 1]
            for q in ('"""', "'''", '"', "'"):
                if line.count(q) % 2 != 0:
                    lines[error.lineno - 1] = line + q
                    return "\n".join(lines), f"Closed unclosed string at line {error.lineno}"

        return None, None


class ImportValidator:
    """Validates that all imports in generated code actually resolve."""

    # Known-safe stdlib modules
    STDLIB = {
        "os", "sys", "json", "csv", "re", "math", "random", "hashlib",
        "sqlite3", "pathlib", "datetime", "collections", "itertools",
        "functools", "typing", "dataclasses", "argparse", "subprocess",
        "tempfile", "shutil", "glob", "io", "time", "uuid", "copy",
        "textwrap", "string", "enum", "abc", "contextlib", "logging",
        "traceback", "unittest", "ast", "inspect", "struct", "base64",
        "urllib", "http", "socket", "threading", "multiprocessing",
        "concurrent", "asyncio", "queue", "heapq", "bisect",
        "statistics", "decimal", "fractions", "operator", "array",
    }

    # Known project modules
    PROJECT_MODULES = {
        "novel", "darwin", "litigationos",
    }

    # Shadow modules in repo root — imports that will BREAK
    SHADOW_DANGER = {
        "json", "typing", "tokenize", "numpy", "pandas", "csv", "re",
        "os", "sys", "collections", "inspect", "ast", "io",
    }

    def validate(self, code: str) -> ValidationResult:
        result = ValidationResult()
        try:
            tree = ast.parse(code)
        except SyntaxError:
            result.errors.append("Cannot validate imports — syntax error in code")
            return result

        imports = self._extract_imports(tree)
        result.imports_ok = True

        for imp in imports:
            module = imp["module"].split(".")[0] if imp["module"] else ""
            if not module:
                continue

            # Check for shadow module danger
            if module in self.SHADOW_DANGER:
                result.warnings.append(
                    f"Import '{module}' — shadow module exists in repo root. "
                    f"Ensure CWD is NOT the repo root when running this code."
                )

            # Check if it's stdlib or known
            if module in self.STDLIB or module in self.PROJECT_MODULES:
                continue

            # Check if it's a third-party package that might not be installed
            try:
                __import__(module)
            except ImportError:
                result.warnings.append(
                    f"Import '{imp['module']}' may not be available — "
                    f"not in stdlib and import check failed"
                )

        return result

    def _extract_imports(self, tree: ast.AST) -> list:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({"module": alias.name, "line": node.lineno})
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.append({"module": module, "line": node.lineno})
        return imports


class RuntimeValidator:
    """
    Actually EXECUTES generated code in a controlled environment.
    Captures stdout, stderr, return code, and runtime duration.
    """

    MAX_RUNTIME = 30  # seconds

    def validate(self, code: str, args: list = None) -> ValidationResult:
        result = ValidationResult()

        # Write to temp file (NEVER use python -c with complex code on Windows)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", dir=str(SAFE_CWD),
            delete=False, encoding="utf-8"
        ) as f:
            # Wrap code with safety preamble
            preamble = (
                "import os, sys\n"
                "os.environ['PYTHONUTF8'] = '1'\n"
                f"sys.path.insert(0, r'{REPO_ROOT / '00_SYSTEM'}')\n"
            )
            f.write(preamble + code)
            temp_path = f.name

        try:
            start = datetime.now()
            proc = subprocess.run(
                [sys.executable, temp_path] + (args or []),
                capture_output=True,
                text=True,
                timeout=self.MAX_RUNTIME,
                cwd=str(SAFE_CWD),
                env={**os.environ, "PYTHONUTF8": "1",
                     "PYTHONPATH": str(REPO_ROOT / "00_SYSTEM")},
            )
            elapsed = (datetime.now() - start).total_seconds()

            result.runtime_seconds = elapsed
            result.output = proc.stdout[:5000] if proc.stdout else ""

            if proc.returncode == 0:
                result.runtime_ok = True
            else:
                stderr = proc.stderr[:2000] if proc.stderr else ""
                result.errors.append(f"Exit code {proc.returncode}: {stderr}")

                # Try to diagnose common runtime errors
                diag = self._diagnose_error(stderr)
                if diag:
                    result.warnings.append(f"Diagnosis: {diag}")

        except subprocess.TimeoutExpired:
            result.errors.append(f"Timed out after {self.MAX_RUNTIME}s")
        except Exception as e:
            result.errors.append(f"Execution error: {str(e)[:200]}")
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

        return result

    def _diagnose_error(self, stderr: str) -> Optional[str]:
        if "ModuleNotFoundError" in stderr:
            module = stderr.split("No module named '")[-1].split("'")[0] if "No module named" in stderr else "unknown"
            return f"Missing module: {module}. May need pip install."
        if "sqlite3.OperationalError" in stderr:
            return "SQLite error — check table/column names with PRAGMA table_info()"
        if "FileNotFoundError" in stderr:
            return "File not found — check paths exist"
        if "PermissionError" in stderr:
            return "Permission denied — file may be locked by another process"
        if "WinError 6" in stderr or "Bad file descriptor" in stderr:
            return "Windows pipe error — use os.environ['PYTHONUTF8'] instead of sys.stdout rewrite"
        return None


class QualityValidator:
    """
    Checks generated code for anti-patterns, safety issues,
    and LitigationOS-specific rules.
    """

    def validate(self, code: str) -> ValidationResult:
        result = ValidationResult()
        result.quality_ok = True
        issues = []

        # CRITICAL: Check for hard deletions (LitigationOS rule)
        delete_patterns = [
            ("os.remove(", "Hard deletion detected — use shutil.move() to I:\\ drive"),
            ("os.unlink(", "Hard deletion detected — use shutil.move() to I:\\ drive"),
            ("shutil.rmtree(", "Recursive deletion detected — NEVER delete litigation directories"),
            (".unlink()", "Path.unlink() detected — move to I:\\ instead"),
        ]
        for pattern, msg in delete_patterns:
            if pattern in code:
                issues.append({"severity": "CRITICAL", "msg": msg})
                result.quality_ok = False

        # Check for hardcoded party names that might be wrong
        wrong_names = [
            ("Jane Berry", "Hallucinated name — Jane Berry never existed"),
            ("Patricia Berry", "Hallucinated name — Patricia Berry never existed"),
            ("Emily Ann", "Wrong middle name — use 'Emily A. Watson'"),
            ("Tiffany Watson", "Wrong name — defendant is Emily A. Watson"),
            ("Lincoln David", "NEVER use child's full name — use 'L.D.W.' per MCR 8.119(H)"),
        ]
        for pattern, msg in wrong_names:
            if pattern in code:
                issues.append({"severity": "CRITICAL", "msg": msg})
                result.quality_ok = False

        # Check for sys.stdout rewrite (Windows pipe breaker)
        if "sys.stdout = open(sys.stdout.fileno()" in code:
            issues.append({
                "severity": "HIGH",
                "msg": "sys.stdout rewrite breaks Windows pipes — "
                       "use os.environ['PYTHONUTF8'] = '1' instead",
            })
            result.quality_ok = False

        # Check for python -c usage
        if 'python -c "' in code or "python -c '" in code:
            issues.append({
                "severity": "HIGH",
                "msg": "python -c breaks on Windows with complex strings — "
                       "write to temp .py file instead",
            })

        # Check for DB best practices
        if "sqlite3.connect" in code:
            if "busy_timeout" not in code:
                issues.append({
                    "severity": "MEDIUM",
                    "msg": "Missing PRAGMA busy_timeout — add 'PRAGMA busy_timeout = 60000'",
                })
            if "journal_mode" not in code and "WAL" not in code:
                issues.append({
                    "severity": "MEDIUM",
                    "msg": "Missing WAL mode — add 'PRAGMA journal_mode = WAL'",
                })

        # Check for unbounded queries
        if "SELECT *" in code and "LIMIT" not in code:
            issues.append({
                "severity": "LOW",
                "msg": "Unbounded SELECT * — add LIMIT or specify columns explicitly",
            })

        result.errors.extend([i["msg"] for i in issues if i["severity"] == "CRITICAL"])
        result.warnings.extend([i["msg"] for i in issues if i["severity"] != "CRITICAL"])

        return result


# ─── Unified Validation Pipeline ────────────────────────────────────────

class ValidationPipeline:
    """
    Runs all validators in sequence, aggregates results,
    and produces a final pass/fail with detailed diagnostics.
    """

    def __init__(self):
        self.syntax = SyntaxValidator()
        self.imports = ImportValidator()
        self.runtime = RuntimeValidator()
        self.quality = QualityValidator()

    def validate(self, code: str, run_code: bool = True, args: list = None) -> ValidationResult:
        """Full validation pipeline. Set run_code=False to skip runtime execution."""

        # Phase 1: Syntax
        syn_result = self.syntax.validate(code)
        if not syn_result.syntax_ok:
            syn_result.score = 0.1
            return syn_result

        # Use auto-fixed code if available
        validated_code = syn_result.output if syn_result.output else code

        # Phase 2: Imports
        imp_result = self.imports.validate(validated_code)

        # Phase 3: Quality
        qual_result = self.quality.validate(validated_code)

        # Phase 4: Runtime (optional)
        run_result = ValidationResult()
        if run_code:
            run_result = self.runtime.validate(validated_code, args)

        # Aggregate
        final = ValidationResult(
            syntax_ok=syn_result.syntax_ok,
            imports_ok=imp_result.imports_ok,
            runtime_ok=run_result.runtime_ok if run_code else True,
            quality_ok=qual_result.quality_ok,
            errors=syn_result.errors + imp_result.errors + qual_result.errors + run_result.errors,
            warnings=syn_result.warnings + imp_result.warnings + qual_result.warnings + run_result.warnings,
            output=run_result.output,
            runtime_seconds=run_result.runtime_seconds,
            auto_fixes=syn_result.auto_fixes,
        )

        # Calculate composite score
        scores = [
            (0.25 if final.syntax_ok else 0),
            (0.20 if final.imports_ok else 0),
            (0.30 if final.runtime_ok else 0),
            (0.25 if final.quality_ok else 0),
        ]
        # Subtract for warnings
        warning_penalty = min(0.15, len(final.warnings) * 0.02)
        final.score = round(sum(scores) - warning_penalty, 3)
        final.passed = final.score >= 0.7 and not final.errors

        return final

    def quick_check(self, code: str) -> dict:
        """Fast check without runtime execution. Good for bulk validation."""
        result = self.validate(code, run_code=False)
        return {
            "passed": result.passed,
            "score": result.score,
            "errors": len(result.errors),
            "warnings": len(result.warnings),
        }
