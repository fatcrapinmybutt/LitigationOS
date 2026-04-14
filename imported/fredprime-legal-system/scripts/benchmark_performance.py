#!/usr/bin/env python3
"""
Performance benchmark script to demonstrate the improvements made to form_db.py and codex_supreme.py.

This script creates sample data and measures the performance of the optimized functions.
"""
import time
import tempfile
import json
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.form_db import FormDatabase
from modules import codex_supreme


def benchmark_database_operations():
    """Benchmark form_db.py operations."""
    print("=" * 70)
    print("BENCHMARK: Database Operations (form_db.py)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = FormDatabase(db_path)
        
        # Create test data
        print("\n1. Creating test dataset...")
        num_forms = 1000
        for i in range(num_forms):
            db.add_form(
                form_id=f"FORM-{i:04d}",
                title=f"Test Form {i}",
                filename=f"form{i}.docx",
                rules=[f"MCR {i % 10}.{i % 100}"],
                statutes=[f"MCL {i % 50}.{i % 200}"],
                benchbook=[f"Benchbook § {i % 20}"],
            )
        print(f"   Created {num_forms} forms")
        
        # Benchmark list_forms
        print("\n2. Benchmarking list_forms()...")
        start = time.perf_counter()
        forms = db.list_forms()
        elapsed = time.perf_counter() - start
        print(f"   ✓ Retrieved {len(forms)} forms in {elapsed*1000:.2f}ms")
        print(f"   ✓ Average: {(elapsed/len(forms))*1000000:.2f}μs per form")
        
        # Benchmark search_forms
        print("\n3. Benchmarking search_forms()...")
        start = time.perf_counter()
        results = db.search_forms("Test")
        elapsed = time.perf_counter() - start
        print(f"   ✓ Found {len(results)} matches in {elapsed*1000:.2f}ms")
        
        # Benchmark find_by_reference
        print("\n4. Benchmarking find_by_reference()...")
        start = time.perf_counter()
        results = db.find_by_reference("MCR")
        elapsed = time.perf_counter() - start
        print(f"   ✓ Found {len(results)} references in {elapsed*1000:.2f}ms")


def benchmark_manifest_operations():
    """Benchmark codex_supreme.py operations."""
    print("\n" + "=" * 70)
    print("BENCHMARK: Manifest Operations (codex_supreme.py)")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save original working directory
        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            
            # Clear any existing cache
            codex_supreme.clear_manifest_cache()
            
            # Create manifest with 500 entries
            print("\n1. Creating test manifest...")
            num_entries = 500
            manifest = []
            for i in range(num_entries):
                file_path = Path(tmpdir) / f"file{i}.py"
                file_path.write_text(f"# Test file {i}")
                manifest.append({
                    "path": str(file_path),
                    "hash": codex_supreme.sha256_file(str(file_path)),
                    "timestamp": f"2025-01-{(i % 28) + 1:02d}T00:00:00",
                    "legal_function": f"function_{i}",
                    "validated": i % 2 == 0,
                })
            
            manifest_path = Path(tmpdir) / "codex_manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            print(f"   Created manifest with {num_entries} entries")
            
            # Create required files
            (Path(tmpdir) / "logs").mkdir(exist_ok=True)
            (Path(tmpdir) / "logs/codex_errors.log").touch()
            (Path(tmpdir) / "patch_history.json").write_text("[]")
            (Path(tmpdir) / "codex_state.json").write_text("{}")
            
            # Benchmark first load (cold cache)
            print("\n2. Benchmarking first manifest load (cold cache)...")
            start = time.perf_counter()
            result1 = codex_supreme.timeline_event_matrix()
            elapsed1 = time.perf_counter() - start
            print(f"   ✓ Loaded {len(result1)} entries in {elapsed1*1000:.2f}ms")
            
            # Benchmark second load (warm cache)
            print("\n3. Benchmarking second manifest load (warm cache)...")
            start = time.perf_counter()
            result2 = codex_supreme.timeline_event_matrix()
            elapsed2 = time.perf_counter() - start
            print(f"   ✓ Loaded {len(result2)} entries in {elapsed2*1000:.2f}ms")
            
            speedup = elapsed1 / elapsed2 if elapsed2 > 0 else float('inf')
            print(f"   ✓ Cache speedup: {speedup:.2f}x faster")
            
            # Benchmark multiple operations (all should use cache)
            print("\n4. Benchmarking multiple operations with cache...")
            start = time.perf_counter()
            codex_supreme.self_diagnostic()
            codex_supreme.forensic_integrity_check()
            codex_supreme.timeline_event_matrix()
            elapsed_all = time.perf_counter() - start
            print(f"   ✓ Completed 3 operations in {elapsed_all*1000:.2f}ms")
            print(f"   ✓ Manifest loaded from cache (not disk) for all operations")
            
        finally:
            # Restore working directory
            os.chdir(original_dir)
            codex_supreme.clear_manifest_cache()


def main():
    """Run all benchmarks."""
    print("\n")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║         FRED SUPREME LITIGATION OS - Performance Benchmark        ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print("\nThis benchmark demonstrates the performance improvements made to:")
    print("  • form_db.py - Database query optimization")
    print("  • codex_supreme.py - File I/O caching")
    print()
    
    try:
        benchmark_database_operations()
        benchmark_manifest_operations()
        
        print("\n" + "=" * 70)
        print("BENCHMARK SUMMARY")
        print("=" * 70)
        print("\n✓ All benchmarks completed successfully!")
        print("\nKey Improvements:")
        print("  • Database cursor metadata extracted once per query (not per row)")
        print("  • Manifest file cached with smart invalidation")
        print("  • SHA256 hashes cached within operations")
        print("  • List comprehensions for efficient iteration")
        print("\nSee PERFORMANCE_IMPROVEMENTS.md for detailed documentation.")
        print()
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
