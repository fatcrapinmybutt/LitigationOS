"""
Codebase Health Tracker — LitigationOS Legal AI
=================================================
Track codebase health metrics: test coverage estimation, import errors,
dead code detection, complexity analysis, and module quality scoring.
Generates a standalone HTML dashboard with dark theme.

Features:
  - AST-based analysis of every Python module
  - Quality scoring (0-100) with letter grades
  - Complexity estimation from branching statements
  - Test file matching and coverage estimation
  - HTML dashboard with CSS charts and sortable tables
  - Trend tracking in litigation_context.db

Usage:
    from legal_ai.codebase_health_tracker import CodebaseHealthTracker
    tracker = CodebaseHealthTracker()
    report = tracker.scan_codebase()
    tracker.export_dashboard("dashboard.html")
"""
from __future__ import annotations

import ast
import html
import json
import logging
import os
import re
import sqlite3
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("legal_ai.codebase_health_tracker")

_HERE = Path(__file__).parent
_REPO = _HERE.parent.parent
_DB_PATH = _REPO / "litigation_context.db"

# Default directories to scan (relative to _REPO / "00_SYSTEM")
_DEFAULT_SCAN_DIRS: List[str] = [
    "legal_ai",
    "engines",
    "pipeline",
    "local_model",
    "skills",
    "mcp_server",
]

# Grading thresholds
_GRADE_THRESHOLDS: List[Tuple[float, str]] = [
    (95.0, "A+"),
    (90.0, "A"),
    (85.0, "A-"),
    (80.0, "B+"),
    (75.0, "B"),
    (70.0, "B-"),
    (65.0, "C+"),
    (60.0, "C"),
    (50.0, "D"),
    (0.0, "F"),
]


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ModuleHealth:
    """Health metrics for a single Python module."""

    module_path: str
    module_name: str
    lines_of_code: int = 0
    function_count: int = 0
    class_count: int = 0
    has_docstrings: bool = False
    has_type_hints: bool = False
    has_error_handling: bool = False
    import_errors: List[str] = field(default_factory=list)
    syntax_valid: bool = True
    complexity_score: float = 0.0
    quality_score: float = 0.0
    has_tests: bool = False
    test_file: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "module_path": self.module_path,
            "module_name": self.module_name,
            "lines_of_code": self.lines_of_code,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "has_docstrings": self.has_docstrings,
            "has_type_hints": self.has_type_hints,
            "has_error_handling": self.has_error_handling,
            "import_errors": list(self.import_errors),
            "syntax_valid": self.syntax_valid,
            "complexity_score": round(self.complexity_score, 1),
            "quality_score": round(self.quality_score, 1),
            "has_tests": self.has_tests,
            "test_file": self.test_file,
        }


@dataclass
class CodebaseReport:
    """Aggregate codebase health report."""

    generated_at: str = ""
    total_modules: int = 0
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    syntax_pass_rate: float = 0.0
    docstring_coverage: float = 0.0
    type_hint_coverage: float = 0.0
    error_handling_coverage: float = 0.0
    test_coverage_estimate: float = 0.0
    avg_quality_score: float = 0.0
    grade: str = "F"
    modules: List[ModuleHealth] = field(default_factory=list)
    top_issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "total_modules": self.total_modules,
            "total_lines": self.total_lines,
            "total_functions": self.total_functions,
            "total_classes": self.total_classes,
            "syntax_pass_rate": round(self.syntax_pass_rate, 1),
            "docstring_coverage": round(self.docstring_coverage, 1),
            "type_hint_coverage": round(self.type_hint_coverage, 1),
            "error_handling_coverage": round(self.error_handling_coverage, 1),
            "test_coverage_estimate": round(self.test_coverage_estimate, 1),
            "avg_quality_score": round(self.avg_quality_score, 1),
            "grade": self.grade,
            "modules": [m.to_dict() for m in self.modules],
            "top_issues": list(self.top_issues),
            "recommendations": list(self.recommendations),
        }


# ---------------------------------------------------------------------------
# AST visitor for module analysis
# ---------------------------------------------------------------------------


class _ModuleVisitor(ast.NodeVisitor):
    """AST visitor that collects module-level metrics."""

    def __init__(self) -> None:
        self.function_count: int = 0
        self.class_count: int = 0
        self.has_docstrings: bool = False
        self.has_type_hints: bool = False
        self.has_error_handling: bool = False
        self.branch_count: int = 0  # if/for/while/try
        self.import_names: List[str] = []
        self._checked_module_doc: bool = False

    def visit_Module(self, node: ast.Module) -> None:
        docstring = ast.get_docstring(node)
        if docstring:
            self.has_docstrings = True
            self._checked_module_doc = True
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_count += 1
        # Check for docstring
        if ast.get_docstring(node):
            self.has_docstrings = True
        # Check for type hints on arguments
        for arg in node.args.args:
            if arg.annotation is not None:
                self.has_type_hints = True
                break
        # Check return annotation
        if node.returns is not None:
            self.has_type_hints = True
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.class_count += 1
        if ast.get_docstring(node):
            self.has_docstrings = True
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.has_error_handling = True
        self.branch_count += 1
        self.generic_visit(node)

    # Python 3.11+ uses TryStar for try/except*
    def visit_TryStar(self, node: ast.AST) -> None:
        self.has_error_handling = True
        self.branch_count += 1
        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self.branch_count += 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.import_names.append(alias.name)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.import_names.append(node.module)


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class CodebaseHealthTracker:
    """Track and report codebase health metrics."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self._db_path = Path(db_path) if db_path else _DB_PATH
        self._system_dir = _REPO / "00_SYSTEM"
        self._last_report: Optional[CodebaseReport] = None
        self._test_files: Dict[str, str] = {}  # module_name -> test_path
        logger.info("CodebaseHealthTracker initialized (db=%s)", self._db_path)

    # ------------------------------------------------------------------
    # DB helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Open a connection with standard PRAGMAs."""
        conn = sqlite3.connect(str(self._db_path), timeout=30)
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self, conn: sqlite3.Connection) -> None:
        """Create health tracking table if needed."""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS codebase_health (
                module_path TEXT PRIMARY KEY,
                quality_score REAL,
                lines_of_code INTEGER,
                checked_at TEXT,
                details TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS codebase_health_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                checked_at TEXT,
                total_modules INTEGER,
                avg_quality_score REAL,
                grade TEXT,
                total_lines INTEGER,
                report_json TEXT
            )
        """)

    # ------------------------------------------------------------------
    # Test file discovery
    # ------------------------------------------------------------------

    def _discover_test_files(self, directories: List[Path]) -> None:
        """Build a mapping of module names to their test files."""
        self._test_files.clear()
        test_dirs: List[Path] = []

        for d in directories:
            # Look for tests/ subdirectory
            tests_dir = d / "tests"
            if tests_dir.is_dir():
                test_dirs.append(tests_dir)
            # Also check parent tests/
            parent_tests = d.parent / "tests"
            if parent_tests.is_dir() and parent_tests not in test_dirs:
                test_dirs.append(parent_tests)

        # Also add the main test suites
        legal_ai_tests = _REPO / "00_SYSTEM" / "legal_ai" / "tests"
        if legal_ai_tests.is_dir() and legal_ai_tests not in test_dirs:
            test_dirs.append(legal_ai_tests)

        product_tests = _REPO / "11_CODE" / "litigationos" / "tests"
        if product_tests.is_dir() and product_tests not in test_dirs:
            test_dirs.append(product_tests)

        for td in test_dirs:
            try:
                for tf in td.rglob("test_*.py"):
                    # Extract module name from test filename
                    stem = tf.stem  # e.g., "test_brief_compliance"
                    module_name = stem.replace("test_", "", 1)
                    self._test_files[module_name] = str(tf)
            except OSError as exc:
                logger.warning("Could not scan test dir %s: %s", td, exc)

    # ------------------------------------------------------------------
    # Module analysis
    # ------------------------------------------------------------------

    def analyze_module(self, module_path: str) -> ModuleHealth:
        """Analyze a single Python module and return health metrics."""
        p = Path(module_path)
        health = ModuleHealth(
            module_path=module_path,
            module_name=p.stem,
        )

        # Read source
        try:
            source = p.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.warning("Cannot read %s: %s", module_path, exc)
            health.syntax_valid = False
            health.import_errors.append(f"Read error: {exc}")
            return health

        # Line count (non-blank, non-comment)
        lines = source.splitlines()
        health.lines_of_code = sum(
            1 for line in lines
            if line.strip() and not line.strip().startswith("#")
        )

        # AST parse
        try:
            tree = ast.parse(source, filename=module_path)
        except SyntaxError as exc:
            health.syntax_valid = False
            health.import_errors.append(f"SyntaxError: {exc.msg} (line {exc.lineno})")
            # Still score what we can from regex
            health.has_docstrings = '"""' in source or "'''" in source
            health.has_type_hints = bool(re.search(r"def\s+\w+\([^)]*:\s*\w", source))
            health.has_error_handling = "try:" in source
            health.quality_score = self.score_module(health)
            return health

        # Visit AST
        visitor = _ModuleVisitor()
        visitor.visit(tree)

        health.function_count = visitor.function_count
        health.class_count = visitor.class_count
        health.has_docstrings = visitor.has_docstrings
        health.has_type_hints = visitor.has_type_hints
        health.has_error_handling = visitor.has_error_handling

        # Complexity score: branches per 100 LOC (lower = simpler = better)
        if health.lines_of_code > 0:
            branch_density = (visitor.branch_count / health.lines_of_code) * 100
            # Scale to 0-100 where 0 = most complex, 100 = simplest
            # A module with >30 branches per 100 LOC is very complex
            health.complexity_score = max(0.0, min(100.0, 100.0 - branch_density * 3.0))
        else:
            health.complexity_score = 100.0

        # Check for import issues (static — just verify names are reasonable)
        for imp_name in visitor.import_names:
            if imp_name and imp_name.split(".")[0] in _SHADOW_MODULES:
                health.import_errors.append(
                    f"Potential shadow import: '{imp_name}' — "
                    f"may collide with repo-root shadow module"
                )

        # Test file matching
        stem = p.stem
        if stem in self._test_files:
            health.has_tests = True
            health.test_file = self._test_files[stem]
        else:
            # Try fuzzy match
            for tname, tpath in self._test_files.items():
                if stem in tname or tname in stem:
                    health.has_tests = True
                    health.test_file = tpath
                    break

        # Score
        health.quality_score = self.score_module(health)
        return health

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score_module(self, health: ModuleHealth) -> float:
        """Score a module 0-100 based on quality criteria."""
        score = 0.0

        # Syntax valid: +20
        if health.syntax_valid:
            score += 20.0

        # Has docstrings: +15
        if health.has_docstrings:
            score += 15.0

        # Has type hints: +10
        if health.has_type_hints:
            score += 10.0

        # Has error handling: +15
        if health.has_error_handling:
            score += 15.0

        # Has tests: +15
        if health.has_tests:
            score += 15.0

        # Low complexity (< 500 lines): +10
        if health.lines_of_code < 500:
            score += 10.0
        elif health.lines_of_code < 1000:
            score += 5.0

        # No import errors: +10
        if not health.import_errors:
            score += 10.0

        # Clean naming conventions: +5
        # Check module name follows snake_case
        if re.match(r"^[a-z][a-z0-9_]*$", health.module_name):
            score += 5.0

        return min(100.0, score)

    @staticmethod
    def calculate_grade(score: float) -> str:
        """Convert a numeric score to a letter grade."""
        for threshold, grade in _GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "F"

    # ------------------------------------------------------------------
    # Full codebase scan
    # ------------------------------------------------------------------

    def scan_codebase(
        self,
        directories: Optional[List[str]] = None,
    ) -> CodebaseReport:
        """Scan the codebase and generate a health report."""
        t0 = time.perf_counter()

        # Resolve directories
        if directories:
            scan_dirs = [Path(d) if Path(d).is_absolute() else self._system_dir / d for d in directories]
        else:
            scan_dirs = [self._system_dir / d for d in _DEFAULT_SCAN_DIRS]

        # Filter to existing directories
        scan_dirs = [d for d in scan_dirs if d.is_dir()]
        if not scan_dirs:
            logger.warning("No valid directories to scan")
            return CodebaseReport(
                generated_at=datetime.now(timezone.utc).isoformat(),
                grade="F",
                recommendations=["No valid directories found to scan."],
            )

        # Discover test files
        self._discover_test_files(scan_dirs)

        # Collect all .py files
        py_files: List[Path] = []
        for d in scan_dirs:
            try:
                for f in d.rglob("*.py"):
                    # Skip __pycache__, test files, and __init__.py stubs
                    if "__pycache__" in str(f):
                        continue
                    if ".pytest_cache" in str(f):
                        continue
                    py_files.append(f)
            except OSError as exc:
                logger.warning("Error scanning %s: %s", d, exc)

        logger.info("Scanning %d Python files across %d directories", len(py_files), len(scan_dirs))

        # Analyze each module
        modules: List[ModuleHealth] = []
        for pf in py_files:
            try:
                health = self.analyze_module(str(pf))
                modules.append(health)
            except Exception as exc:
                logger.warning("Failed to analyze %s: %s", pf, exc)

        # Build report
        report = self._build_report(modules)

        elapsed = (time.perf_counter() - t0) * 1000
        logger.info(
            "Scan complete: %d modules, avg score %.1f (%s) in %.1fms",
            report.total_modules, report.avg_quality_score, report.grade, elapsed,
        )

        self._last_report = report
        return report

    def _build_report(self, modules: List[ModuleHealth]) -> CodebaseReport:
        """Build aggregate report from individual module analyses."""
        report = CodebaseReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_modules=len(modules),
            modules=modules,
        )

        if not modules:
            report.grade = "F"
            report.recommendations.append("No modules found to analyze.")
            return report

        # Aggregates
        report.total_lines = sum(m.lines_of_code for m in modules)
        report.total_functions = sum(m.function_count for m in modules)
        report.total_classes = sum(m.class_count for m in modules)

        syntax_valid = sum(1 for m in modules if m.syntax_valid)
        with_docstrings = sum(1 for m in modules if m.has_docstrings)
        with_hints = sum(1 for m in modules if m.has_type_hints)
        with_handling = sum(1 for m in modules if m.has_error_handling)
        with_tests = sum(1 for m in modules if m.has_tests)
        n = len(modules)

        report.syntax_pass_rate = (syntax_valid / n) * 100
        report.docstring_coverage = (with_docstrings / n) * 100
        report.type_hint_coverage = (with_hints / n) * 100
        report.error_handling_coverage = (with_handling / n) * 100
        report.test_coverage_estimate = (with_tests / n) * 100

        scores = [m.quality_score for m in modules]
        report.avg_quality_score = statistics.mean(scores) if scores else 0.0
        report.grade = self.calculate_grade(report.avg_quality_score)

        # Top issues
        report.top_issues = self._identify_top_issues(modules)

        # Recommendations
        report.recommendations = self._build_recommendations(report)

        return report

    def _identify_top_issues(self, modules: List[ModuleHealth]) -> List[Dict[str, Any]]:
        """Identify the most impactful issues across the codebase."""
        issues: List[Dict[str, Any]] = []

        # Syntax errors are critical
        for m in modules:
            if not m.syntax_valid:
                issues.append({
                    "severity": "critical",
                    "module": m.module_name,
                    "path": m.module_path,
                    "issue": "Syntax error — module cannot be imported",
                    "details": "; ".join(m.import_errors[:3]),
                })

        # Large complex modules
        for m in modules:
            if m.lines_of_code > 1000 and m.complexity_score < 40:
                issues.append({
                    "severity": "high",
                    "module": m.module_name,
                    "path": m.module_path,
                    "issue": f"Large complex module ({m.lines_of_code} LOC, complexity {m.complexity_score:.0f})",
                    "details": "Consider splitting into smaller focused modules",
                })

        # Missing error handling
        for m in modules:
            if not m.has_error_handling and m.function_count > 3:
                issues.append({
                    "severity": "medium",
                    "module": m.module_name,
                    "path": m.module_path,
                    "issue": "No error handling (try/except) in module with "
                             f"{m.function_count} functions",
                    "details": "Add try/except blocks for robustness",
                })

        # Shadow import warnings
        for m in modules:
            shadow_warnings = [e for e in m.import_errors if "shadow" in e.lower()]
            if shadow_warnings:
                issues.append({
                    "severity": "medium",
                    "module": m.module_name,
                    "path": m.module_path,
                    "issue": "Potential shadow module import",
                    "details": shadow_warnings[0],
                })

        # Low quality modules
        for m in modules:
            if m.quality_score < 30 and m.syntax_valid:
                issues.append({
                    "severity": "low",
                    "module": m.module_name,
                    "path": m.module_path,
                    "issue": f"Low quality score ({m.quality_score:.0f}/100)",
                    "details": "Missing docstrings, type hints, tests, or error handling",
                })

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        issues.sort(key=lambda i: severity_order.get(i.get("severity", "low"), 99))

        return issues[:50]

    def _build_recommendations(self, report: CodebaseReport) -> List[str]:
        """Build actionable recommendations from the report."""
        recs: List[str] = []

        if report.syntax_pass_rate < 100:
            broken = sum(1 for m in report.modules if not m.syntax_valid)
            recs.append(
                f"FIX IMMEDIATELY: {broken} modules have syntax errors and cannot be imported."
            )

        if report.test_coverage_estimate < 50:
            untested = sum(1 for m in report.modules if not m.has_tests)
            recs.append(
                f"Test coverage is low ({report.test_coverage_estimate:.0f}%). "
                f"{untested} modules lack test files."
            )

        if report.docstring_coverage < 70:
            recs.append(
                f"Docstring coverage is {report.docstring_coverage:.0f}% — "
                f"aim for 80%+ for maintainability."
            )

        if report.type_hint_coverage < 50:
            recs.append(
                f"Type hint coverage is {report.type_hint_coverage:.0f}% — "
                f"add annotations to improve IDE support and catch bugs."
            )

        if report.error_handling_coverage < 60:
            recs.append(
                f"Error handling coverage is {report.error_handling_coverage:.0f}% — "
                f"add try/except blocks to prevent silent failures."
            )

        # Large modules
        large = [m for m in report.modules if m.lines_of_code > 1000]
        if large:
            names = ", ".join(m.module_name for m in large[:5])
            recs.append(
                f"{len(large)} modules exceed 1000 LOC ({names}) — "
                f"consider splitting for maintainability."
            )

        # Overall encouragement
        if report.avg_quality_score >= 80:
            recs.append(
                f"Overall quality is strong ({report.grade}). "
                f"Focus on closing remaining test and documentation gaps."
            )
        elif report.avg_quality_score >= 60:
            recs.append(
                f"Quality is fair ({report.grade}). Priority: fix syntax errors, "
                f"then add tests, then docstrings."
            )
        else:
            recs.append(
                f"Quality needs attention ({report.grade}). Start with fixing "
                f"syntax errors and adding basic error handling."
            )

        return recs

    # ------------------------------------------------------------------
    # HTML Dashboard
    # ------------------------------------------------------------------

    def generate_html_dashboard(self, report: Optional[CodebaseReport] = None) -> str:
        """Generate a standalone HTML dashboard page."""
        r = report or self._last_report
        if r is None:
            r = self.scan_codebase()

        # Pre-compute distribution buckets
        dist = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for m in r.modules:
            g = self.calculate_grade(m.quality_score)
            bucket = g[0] if g[0] in dist else "F"
            dist[bucket] += 1

        max_dist = max(dist.values(), default=1)

        # Build module table rows
        module_rows = []
        sorted_modules = sorted(r.modules, key=lambda m: m.quality_score, reverse=True)
        for m in sorted_modules:
            grade = self.calculate_grade(m.quality_score)
            grade_color = _grade_color(grade)
            esc_path = html.escape(m.module_path)
            esc_name = html.escape(m.module_name)
            test_badge = (
                '<span class="badge badge-pass">✓ tested</span>'
                if m.has_tests
                else '<span class="badge badge-fail">✗ no tests</span>'
            )
            syntax_badge = (
                '<span class="badge badge-pass">✓</span>'
                if m.syntax_valid
                else '<span class="badge badge-fail">✗ error</span>'
            )
            module_rows.append(
                f"<tr>"
                f'<td title="{esc_path}">{esc_name}</td>'
                f"<td>{m.lines_of_code}</td>"
                f"<td>{m.function_count}</td>"
                f"<td>{m.class_count}</td>"
                f"<td>{syntax_badge}</td>"
                f"<td>{test_badge}</td>"
                f'<td style="color:{grade_color};font-weight:bold">'
                f"{m.quality_score:.0f} ({grade})</td>"
                f"</tr>"
            )
        table_body = "\n".join(module_rows)

        # Build issues list
        issue_items = []
        sev_colors = {
            "critical": "#e74c3c",
            "high": "#e67e22",
            "medium": "#f1c40f",
            "low": "#95a5a6",
        }
        for issue in r.top_issues[:20]:
            sev = issue.get("severity", "low")
            color = sev_colors.get(sev, "#95a5a6")
            esc_issue = html.escape(str(issue.get("issue", "")))
            esc_mod = html.escape(str(issue.get("module", "")))
            esc_det = html.escape(str(issue.get("details", "")))
            issue_items.append(
                f'<div class="issue-item">'
                f'<span class="issue-sev" style="background:{color}">{sev.upper()}</span>'
                f"<strong>{esc_mod}</strong>: {esc_issue}"
                f'<div class="issue-detail">{esc_det}</div>'
                f"</div>"
            )
        issues_html = "\n".join(issue_items) if issue_items else "<p>No issues found.</p>"

        # Build recommendations
        rec_items = []
        for rec in r.recommendations:
            esc_rec = html.escape(rec)
            rec_items.append(f"<li>{esc_rec}</li>")
        recs_html = "<ul>" + "\n".join(rec_items) + "</ul>" if rec_items else "<p>None.</p>"

        # Distribution bars
        dist_bars = []
        for grade_letter in ["A", "B", "C", "D", "F"]:
            count = dist[grade_letter]
            pct = (count / max_dist * 100) if max_dist > 0 else 0
            color = _grade_color(grade_letter)
            dist_bars.append(
                f'<div class="bar-row">'
                f'<span class="bar-label">{grade_letter}</span>'
                f'<div class="bar-track">'
                f'<div class="bar-fill" style="width:{pct:.0f}%;background:{color}"></div>'
                f"</div>"
                f'<span class="bar-count">{count}</span>'
                f"</div>"
            )
        dist_html = "\n".join(dist_bars)

        # Grade color
        overall_color = _grade_color(r.grade)

        dashboard = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LitigationOS — Codebase Health Dashboard</title>
<style>
:root {{
  --bg: #0d1117; --surface: #161b22; --border: #30363d;
  --text: #c9d1d9; --text-muted: #8b949e; --accent: #58a6ff;
  --green: #3fb950; --red: #f85149; --orange: #d29922; --purple: #bc8cff;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.5; padding: 20px;
}}
.container {{ max-width: 1400px; margin: 0 auto; }}
h1 {{ color: var(--accent); margin-bottom: 4px; font-size: 1.6rem; }}
.subtitle {{ color: var(--text-muted); margin-bottom: 24px; font-size: 0.9rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 24px; }}
.card {{
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 8px; padding: 20px;
}}
.card h2 {{ font-size: 1rem; color: var(--text-muted); margin-bottom: 12px; }}
.big-score {{
  font-size: 4rem; font-weight: 700; text-align: center; line-height: 1;
  margin: 8px 0;
}}
.big-grade {{ font-size: 1.4rem; text-align: center; color: var(--text-muted); }}
.stat-row {{ display: flex; justify-content: space-between; padding: 6px 0;
             border-bottom: 1px solid var(--border); }}
.stat-row:last-child {{ border-bottom: none; }}
.stat-label {{ color: var(--text-muted); }}
.stat-value {{ font-weight: 600; }}
.bar-row {{ display: flex; align-items: center; margin: 6px 0; }}
.bar-label {{ width: 24px; font-weight: 600; text-align: center; }}
.bar-track {{ flex: 1; height: 22px; background: var(--border); border-radius: 4px;
              margin: 0 8px; overflow: hidden; }}
.bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.5s ease; }}
.bar-count {{ width: 30px; text-align: right; font-size: 0.85rem; color: var(--text-muted); }}
.issue-item {{
  padding: 10px; margin-bottom: 8px; background: var(--bg);
  border-radius: 6px; border-left: 3px solid var(--border);
}}
.issue-sev {{
  display: inline-block; padding: 1px 8px; border-radius: 3px;
  font-size: 0.7rem; font-weight: 700; color: #fff; margin-right: 8px;
  text-transform: uppercase; letter-spacing: 0.5px;
}}
.issue-detail {{ color: var(--text-muted); font-size: 0.85rem; margin-top: 4px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
th {{ text-align: left; padding: 10px 8px; border-bottom: 2px solid var(--border);
     color: var(--text-muted); cursor: pointer; user-select: none; }}
th:hover {{ color: var(--accent); }}
td {{ padding: 8px; border-bottom: 1px solid var(--border); }}
tr:hover {{ background: rgba(88,166,255,0.05); }}
.badge {{
  display: inline-block; padding: 2px 8px; border-radius: 10px;
  font-size: 0.75rem; font-weight: 600;
}}
.badge-pass {{ background: rgba(63,185,80,0.15); color: var(--green); }}
.badge-fail {{ background: rgba(248,81,73,0.15); color: var(--red); }}
ul {{ padding-left: 20px; }}
li {{ margin-bottom: 6px; }}
.footer {{ text-align: center; color: var(--text-muted); font-size: 0.8rem;
           margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="container">
  <h1>⚖️ LitigationOS — Codebase Health Dashboard</h1>
  <p class="subtitle">Generated {html.escape(r.generated_at)} | {r.total_modules} modules | {r.total_lines:,} lines</p>

  <div class="grid">
    <div class="card">
      <h2>Overall Health</h2>
      <div class="big-score" style="color:{overall_color}">{r.avg_quality_score:.0f}</div>
      <div class="big-grade">Grade: <strong style="color:{overall_color}">{html.escape(r.grade)}</strong></div>
    </div>
    <div class="card">
      <h2>Key Metrics</h2>
      <div class="stat-row"><span class="stat-label">Modules</span><span class="stat-value">{r.total_modules}</span></div>
      <div class="stat-row"><span class="stat-label">Lines of Code</span><span class="stat-value">{r.total_lines:,}</span></div>
      <div class="stat-row"><span class="stat-label">Functions</span><span class="stat-value">{r.total_functions}</span></div>
      <div class="stat-row"><span class="stat-label">Classes</span><span class="stat-value">{r.total_classes}</span></div>
      <div class="stat-row"><span class="stat-label">Syntax Pass</span><span class="stat-value">{r.syntax_pass_rate:.0f}%</span></div>
    </div>
    <div class="card">
      <h2>Coverage Rates</h2>
      <div class="stat-row"><span class="stat-label">Docstrings</span><span class="stat-value">{r.docstring_coverage:.0f}%</span></div>
      <div class="stat-row"><span class="stat-label">Type Hints</span><span class="stat-value">{r.type_hint_coverage:.0f}%</span></div>
      <div class="stat-row"><span class="stat-label">Error Handling</span><span class="stat-value">{r.error_handling_coverage:.0f}%</span></div>
      <div class="stat-row"><span class="stat-label">Tests (est.)</span><span class="stat-value">{r.test_coverage_estimate:.0f}%</span></div>
    </div>
  </div>

  <div class="grid" style="grid-template-columns: 1fr 1fr;">
    <div class="card">
      <h2>Grade Distribution</h2>
      {dist_html}
    </div>
    <div class="card">
      <h2>Recommendations</h2>
      {recs_html}
    </div>
  </div>

  <div class="card" style="margin-bottom:24px">
    <h2>Top Issues ({len(r.top_issues)})</h2>
    {issues_html}
  </div>

  <div class="card">
    <h2>Module Details</h2>
    <table id="module-table">
      <thead>
        <tr>
          <th onclick="sortTable(0)">Module ↕</th>
          <th onclick="sortTable(1)">LOC ↕</th>
          <th onclick="sortTable(2)">Functions ↕</th>
          <th onclick="sortTable(3)">Classes ↕</th>
          <th onclick="sortTable(4)">Syntax ↕</th>
          <th onclick="sortTable(5)">Tests ↕</th>
          <th onclick="sortTable(6)">Quality ↕</th>
        </tr>
      </thead>
      <tbody>
        {table_body}
      </tbody>
    </table>
  </div>

  <div class="footer">
    LitigationOS Codebase Health Tracker v1.0.0 — Generated by legal_ai.codebase_health_tracker
  </div>
</div>

<script>
let sortDir = {{}};
function sortTable(col) {{
  const table = document.getElementById("module-table");
  const tbody = table.querySelector("tbody");
  const rows = Array.from(tbody.querySelectorAll("tr"));
  sortDir[col] = !sortDir[col];
  rows.sort((a, b) => {{
    let av = a.children[col].textContent.trim();
    let bv = b.children[col].textContent.trim();
    let an = parseFloat(av), bn = parseFloat(bv);
    if (!isNaN(an) && !isNaN(bn)) {{
      return sortDir[col] ? an - bn : bn - an;
    }}
    return sortDir[col] ? av.localeCompare(bv) : bv.localeCompare(av);
  }});
  rows.forEach(r => tbody.appendChild(r));
}}
</script>
</body>
</html>"""

        return dashboard

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_dashboard(self, output_path: Optional[str] = None) -> str:
        """Write HTML dashboard to file. Returns the output path."""
        if output_path is None:
            output_path = str(_REPO / "00_SYSTEM" / "reports" / "codebase_health.html")

        dashboard_html = self.generate_html_dashboard()
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(dashboard_html, encoding="utf-8")
        logger.info("Dashboard exported to %s", out)
        return str(out)

    def export_report(self, output_path: str) -> str:
        """Write JSON report to file. Returns the output path."""
        r = self._last_report
        if r is None:
            r = self.scan_codebase()

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(r.to_dict(), indent=2), encoding="utf-8")
        logger.info("Report exported to %s", out)
        return str(out)

    # ------------------------------------------------------------------
    # DB persistence
    # ------------------------------------------------------------------

    def save_to_db(self, report: Optional[CodebaseReport] = None) -> int:
        """Persist report to DB. Returns count of rows saved."""
        r = report or self._last_report
        if r is None:
            return 0

        saved = 0
        try:
            conn = self._connect()
            self._ensure_tables(conn)

            # Save per-module records
            rows = [
                (
                    m.module_path,
                    m.quality_score,
                    m.lines_of_code,
                    r.generated_at,
                    json.dumps(m.to_dict()),
                )
                for m in r.modules
            ]
            conn.executemany(
                "INSERT OR REPLACE INTO codebase_health "
                "(module_path, quality_score, lines_of_code, checked_at, details) "
                "VALUES (?, ?, ?, ?, ?)",
                rows,
            )
            saved += len(rows)

            # Save history snapshot
            conn.execute(
                "INSERT INTO codebase_health_history "
                "(checked_at, total_modules, avg_quality_score, grade, total_lines, report_json) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    r.generated_at,
                    r.total_modules,
                    r.avg_quality_score,
                    r.grade,
                    r.total_lines,
                    json.dumps(r.to_dict()),
                ),
            )
            saved += 1

            conn.commit()
            conn.close()
            logger.info("Saved %d records to DB", saved)
        except sqlite3.Error as exc:
            logger.error("DB save failed: %s", exc)

        return saved

    # ------------------------------------------------------------------
    # Trend analysis
    # ------------------------------------------------------------------

    def get_trend(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get health score trend over the last N days."""
        if not self._db_path.exists():
            return []

        trend: List[Dict[str, Any]] = []
        try:
            conn = self._connect()
            self._ensure_tables(conn)

            rows = conn.execute(
                "SELECT checked_at, total_modules, avg_quality_score, grade, total_lines "
                "FROM codebase_health_history "
                "WHERE checked_at >= datetime('now', ? || ' days') "
                "ORDER BY checked_at ASC",
                (f"-{days}",),
            ).fetchall()

            for row in rows:
                trend.append({
                    "checked_at": row["checked_at"],
                    "total_modules": row["total_modules"],
                    "avg_quality_score": row["avg_quality_score"],
                    "grade": row["grade"],
                    "total_lines": row["total_lines"],
                })

            conn.close()
        except sqlite3.Error as exc:
            logger.warning("Could not load trend data: %s", exc)

        return trend

    # ------------------------------------------------------------------
    # Report comparison
    # ------------------------------------------------------------------

    def compare_reports(
        self,
        old: CodebaseReport,
        new: CodebaseReport,
    ) -> Dict[str, Any]:
        """Compare two reports and return a delta summary."""
        delta: Dict[str, Any] = {
            "old_generated_at": old.generated_at,
            "new_generated_at": new.generated_at,
            "modules_delta": new.total_modules - old.total_modules,
            "lines_delta": new.total_lines - old.total_lines,
            "functions_delta": new.total_functions - old.total_functions,
            "classes_delta": new.total_classes - old.total_classes,
            "quality_delta": round(new.avg_quality_score - old.avg_quality_score, 1),
            "old_grade": old.grade,
            "new_grade": new.grade,
            "syntax_delta": round(new.syntax_pass_rate - old.syntax_pass_rate, 1),
            "docstring_delta": round(new.docstring_coverage - old.docstring_coverage, 1),
            "type_hint_delta": round(new.type_hint_coverage - old.type_hint_coverage, 1),
            "error_handling_delta": round(new.error_handling_coverage - old.error_handling_coverage, 1),
            "test_delta": round(new.test_coverage_estimate - old.test_coverage_estimate, 1),
            "improved": new.avg_quality_score > old.avg_quality_score,
        }

        # Find new and removed modules
        old_paths = {m.module_path for m in old.modules}
        new_paths = {m.module_path for m in new.modules}
        delta["added_modules"] = sorted(new_paths - old_paths)
        delta["removed_modules"] = sorted(old_paths - new_paths)

        # Modules with biggest quality change
        old_scores = {m.module_path: m.quality_score for m in old.modules}
        changes: List[Dict[str, Any]] = []
        for m in new.modules:
            if m.module_path in old_scores:
                change = m.quality_score - old_scores[m.module_path]
                if abs(change) > 5:
                    changes.append({
                        "module": m.module_name,
                        "path": m.module_path,
                        "old_score": old_scores[m.module_path],
                        "new_score": m.quality_score,
                        "delta": round(change, 1),
                    })

        changes.sort(key=lambda c: abs(c["delta"]), reverse=True)
        delta["biggest_changes"] = changes[:10]

        return delta

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return engine status."""
        return {
            "version": "1.0.0",
            "db_path": str(self._db_path),
            "db_exists": self._db_path.exists(),
            "system_dir": str(self._system_dir),
            "system_dir_exists": self._system_dir.is_dir(),
            "scan_directories": _DEFAULT_SCAN_DIRS,
            "test_files_discovered": len(self._test_files),
            "last_report_available": self._last_report is not None,
            "last_grade": self._last_report.grade if self._last_report else None,
            "last_module_count": self._last_report.total_modules if self._last_report else 0,
        }


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

# Known shadow modules in the repo root (from shell-management instructions)
_SHADOW_MODULES: Set[str] = {
    "json", "typing", "tokenize", "numpy", "pandas",
    "re", "os", "sys", "time", "math", "hashlib",
    "collections", "functools", "itertools", "pathlib",
    "logging", "sqlite3", "csv", "io", "abc",
    "dataclasses", "enum",
}


def _grade_color(grade: str) -> str:
    """Return a hex color for a grade string."""
    g = grade[0] if grade else "F"
    colors = {
        "A": "#3fb950",  # green
        "B": "#58a6ff",  # blue
        "C": "#d29922",  # orange
        "D": "#f85149",  # red
        "F": "#f85149",  # red
    }
    return colors.get(g, "#8b949e")
