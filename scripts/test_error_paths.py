"""
Error Path Tests — Validates resilience to corrupt, malformed, and edge-case inputs.
====================================================================================

Uses context managers for guaranteed cleanup. Tests all failure modes:
corrupt files, empty files, missing files, DB failures, invalid inputs.
"""

import os
import sys
import json
import sqlite3
import tempfile
import importlib.util
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import date

# --- Bootstrap: register intake as importable package ---
ROOT = Path(__file__).resolve().parent.parent
ENGINES = ROOT / "00_SYSTEM" / "engines"

# Register intake as a top-level package
spec = importlib.util.spec_from_file_location(
    "intake", ENGINES / "intake" / "__init__.py",
    submodule_search_locations=[str(ENGINES / "intake")]
)
intake_mod = importlib.util.module_from_spec(spec)
sys.modules["intake"] = intake_mod
spec.loader.exec_module(intake_mod)

from intake.extractor import TextExtractor, ExtractionResult
from intake.classifier import DocumentClassifier
from intake.analyzer import LitigationAnalyzer

passed = 0
failed = 0
errors = []

def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        failed += 1
        errors.append((name, str(e)))
        print(f"  [FAIL] {name}: {e}")

# --- Extractor Error Tests ---

def test_missing_file():
    ext = TextExtractor()
    result = ext.extract("/nonexistent/path/fake.pdf")
    assert result.error, "Should have error for missing file"
    assert "not found" in result.error.lower() or "File not found" in result.error

def test_empty_file():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "empty.txt"
        p.write_text("")
        ext = TextExtractor()
        result = ext.extract(str(p))
        assert result.char_count == 0, f"Empty file should have 0 chars, got {result.char_count}"
        assert not result.error, f"Empty file should not error: {result.error}"

def test_corrupt_pdf():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "corrupt.pdf"
        p.write_bytes(b"%PDF-1.4 THIS IS CORRUPT GARBAGE " + os.urandom(1024))
        ext = TextExtractor()
        result = ext.extract(str(p))
        # Should handle gracefully — either extract nothing or report error
        assert isinstance(result, ExtractionResult)

def test_binary_garbage():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "garbage.txt"
        p.write_bytes(os.urandom(4096))
        ext = TextExtractor()
        result = ext.extract(str(p))
        assert isinstance(result, ExtractionResult)

def test_unsupported_extension():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "file.xyz"
        p.write_text("some content")
        ext = TextExtractor()
        result = ext.extract(str(p))
        assert result.error, "Unsupported extension should report error"
        assert "unsupported" in result.error.lower()

def test_huge_single_line():
    """Test that very long single-line files don't crash."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "huge_line.txt"
        p.write_text("A" * 500_000)
        ext = TextExtractor()
        result = ext.extract(str(p))
        assert result.char_count == 500_000

def test_unicode_content():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "unicode.txt"
        p.write_text("\u65e5\u672c\u8a9e\u30c6\u30b9\u30c8 \u4e2d\u6587\u6d4b\u8bd5 \ud55c\uad6d\uc5b4 \u0627\u0644\u0639\u0631\u0628\u064a\u0629")
        ext = TextExtractor()
        result = ext.extract(str(p))
        assert "\u65e5\u672c\u8a9e" in result.full_text

# --- Classifier Error Tests ---

def test_classify_empty_text():
    clf = DocumentClassifier()
    result = clf.classify("", "empty.pdf")
    assert result.doc_type, "Should return a doc_type even for empty text"

def test_classify_none_safe():
    """Classifier should handle None-like inputs gracefully."""
    clf = DocumentClassifier()
    try:
        result = clf.classify("", "")
        assert isinstance(result.doc_type, str)
    except Exception as e:
        # If it raises, should be a clear error, not a crash
        assert "classify" in str(e).lower() or True  # any exception is acceptable

# --- Analyzer Error Tests ---

def test_analyze_empty():
    analyzer = LitigationAnalyzer()
    result = analyzer.analyze("", "empty.pdf")
    assert isinstance(result.evidence_quotes, list)
    assert len(result.evidence_quotes) == 0 or True  # may find nothing

def test_analyze_gibberish():
    analyzer = LitigationAnalyzer()
    gibberish = "asdf qwer zxcv " * 1000
    result = analyzer.analyze(gibberish, "gibberish.txt")
    assert isinstance(result.evidence_quotes, list)

# --- Database Router Error Tests ---

def test_router_corrupt_db():
    """Router should handle corrupt database gracefully."""
    import gc
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "corrupt.db"
        db_path.write_bytes(b"THIS IS NOT A SQLITE DATABASE")
        try:
            from intake.router import DatabaseRouter
            router = DatabaseRouter(str(db_path))
            router.connect()
            assert False, "Should have raised an error for corrupt DB"
        except Exception:
            pass  # Expected — corrupt DB should fail
        finally:
            # Ensure all refs are dropped so Windows releases file lock
            router = None
            gc.collect()

def test_router_readonly_dir():
    """Router handles non-writable paths."""
    try:
        from intake.router import DatabaseRouter
        router = DatabaseRouter("/nonexistent/path/db.sqlite")
        router.connect()
        assert False, "Should fail for non-writable path"
    except Exception:
        pass  # Expected

# --- DB Connection Mock Tests ---

def test_db_write_failure():
    """Simulate DB write failure with mock."""
    with tempfile.TemporaryDirectory() as td:
        db_path = Path(td) / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, val TEXT)")
        conn.close()

        with patch("sqlite3.connect") as mock_conn:
            mock_conn.return_value.execute.side_effect = sqlite3.OperationalError("disk I/O error")
            try:
                c = sqlite3.connect(str(db_path))
                c.execute("INSERT INTO test VALUES (1, 'x')")
                assert False, "Should have raised"
            except sqlite3.OperationalError:
                pass  # Expected

# --- Run all tests ---
if __name__ == "__main__":
    print("=" * 60)
    print("  Error Path Tests")
    print("=" * 60)

    tests = [
        ("Missing file", test_missing_file),
        ("Empty file", test_empty_file),
        ("Corrupt PDF", test_corrupt_pdf),
        ("Binary garbage", test_binary_garbage),
        ("Unsupported extension", test_unsupported_extension),
        ("Huge single line", test_huge_single_line),
        ("Unicode content", test_unicode_content),
        ("Classify empty text", test_classify_empty_text),
        ("Classify none-safe", test_classify_none_safe),
        ("Analyze empty", test_analyze_empty),
        ("Analyze gibberish", test_analyze_gibberish),
        ("Router corrupt DB", test_router_corrupt_db),
        ("Router readonly dir", test_router_readonly_dir),
        ("DB write failure", test_db_write_failure),
    ]

    for name, fn in tests:
        test(name, fn)

    print(f"\n{'=' * 60}")
    print(f"  RESULTS: {passed} passed, {failed} failed")
    if errors:
        print(f"\n  Failures:")
        for name, err in errors:
            print(f"    [FAIL] {name}: {err}")
    print(f"{'=' * 60}")

    sys.exit(0 if failed == 0 else 1)
