#!/usr/bin/env python3
"""
CLI wrapper for Convergence Cycle Engine
=========================================

Provides easy command-line access to the convergence cycle system with
enhanced features for monitoring, debugging, and managing builds.

Usage:
    python run_cycle.py              # Run a full convergence cycle
    python run_cycle.py --status     # Check current version status
    python run_cycle.py --history    # Show version history
    python run_cycle.py --snapshot   # Create snapshot without full cycle
    python run_cycle.py --validate   # Validate system integrity
    python run_cycle.py --clean      # Clean temporary files

Features:
    - Colorized console output for better readability
    - Detailed status reporting with size metrics
    - Version history with change summaries
    - System validation and integrity checks
    - Clean-up utilities for temporary files

Author: FRED PRIME Litigation Deployment System
Version: 2.0
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from convergence_cycle_engine import ConvergenceCycleEngine


def show_status():
    """Show current version status with enhanced metrics."""
    version_file = Path("VERSION")
    current_file = Path("CURRENT")
    manifest_file = Path("codex_manifest.json")
    
    print("\n" + "=" * 60)
    print("CONVERGENCE CYCLE STATUS")
    print("=" * 60)
    
    # Version information
    if version_file.exists():
        version = version_file.read_text().strip()
        print(f"Current Version: {version}")
    else:
        print("Current Version: Not initialized")
    
    if current_file.exists():
        current = current_file.read_text().strip()
        print(f"Runnable Version: {current}")
    else:
        print("Runnable Version: Not set")
    
    # Module tracking
    if manifest_file.exists():
        manifest = json.loads(manifest_file.read_text())
        print(f"Modules Tracked: {len(manifest)}")
        # Show last update time if available
        import os
        mtime = os.path.getmtime(manifest_file)
        from datetime import datetime
        last_update = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Last Manifest Update: {last_update}")
    else:
        print("Modules Tracked: 0")
    
    # Version snapshots
    versions_dir = Path("VERSIONS")
    if versions_dir.exists():
        snapshots = sorted(versions_dir.iterdir())
        print(f"Version Snapshots: {len(snapshots)}")
        if snapshots:
            latest = snapshots[-1].name if snapshots else "N/A"
            print(f"Latest Snapshot: {latest}")
    else:
        print("Version Snapshots: 0")
    
    # Release packages
    output_dir = Path("output")
    if output_dir.exists():
        releases = list(output_dir.glob("*.zip"))
        print(f"Release Packages: {len(releases)}")
        if releases:
            total_size = sum(r.stat().st_size for r in releases)
            print(f"Total Release Size: {total_size / (1024*1024):.2f} MB")
    else:
        print("Release Packages: 0")
    
    # Log files
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log"))
        print(f"Log Files: {len(log_files)}")
    
    print("=" * 60 + "\n")


def show_history():
    """Show version history from CHANGELOG."""
    changelog_file = Path("CHANGELOG.md")
    
    if not changelog_file.exists():
        print("No CHANGELOG found.")
        return
    
    print("\n" + "=" * 60)
    print("VERSION HISTORY")
    print("=" * 60)
    
    content = changelog_file.read_text()
    lines = content.split("\n")
    
    version_count = 0
    for line in lines:
        if line.startswith("## [v"):
            print(line[3:])
            version_count += 1
            if version_count >= 10:
                print("\n... (see CHANGELOG.md for full history)")
                break
    
    print("=" * 60 + "\n")


def create_snapshot():
    """Create a snapshot without running full cycle."""
    engine = ConvergenceCycleEngine()
    current_version = engine.read_version()
    engine.current_version = current_version
    
    print(f"\nCreating snapshot for {current_version}...")
    snapshot_dir = engine.snapshot_version()
    print(f"✓ Snapshot created: {snapshot_dir}\n")


def validate_system():
    """Validate system integrity and report any issues."""
    print("\n" + "=" * 60)
    print("SYSTEM VALIDATION")
    print("=" * 60 + "\n")
    
    issues = []
    
    # Check critical files
    critical_files = [
        ("VERSION", Path("VERSION")),
        ("CURRENT", Path("CURRENT")),
        ("CHANGELOG.md", Path("CHANGELOG.md")),
        ("codex_manifest.json", Path("codex_manifest.json"))
    ]
    
    print("Checking critical files...")
    for name, path in critical_files:
        if path.exists():
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name} - MISSING")
            issues.append(f"Missing critical file: {name}")
    
    # Check directories
    print("\nChecking directories...")
    critical_dirs = [
        ("VERSIONS", Path("VERSIONS")),
        ("output", Path("output")),
        ("logs", Path("logs"))
    ]
    
    for name, path in critical_dirs:
        if path.exists() and path.is_dir():
            print(f"  ✓ {name}/")
        else:
            print(f"  ✗ {name}/ - MISSING")
            issues.append(f"Missing directory: {name}/")
    
    # Check manifest integrity
    print("\nChecking manifest integrity...")
    try:
        manifest_file = Path("codex_manifest.json")
        if manifest_file.exists():
            manifest_data = json.loads(manifest_file.read_text())
            manifest_dict = {entry["path"]: entry for entry in manifest_data}
            
            # Manual verification to provide better error messages
            missing_files = []
            hash_mismatches = []
            
            for path, info in manifest_dict.items():
                file_path = Path(path)
                if not file_path.exists():
                    missing_files.append(path)
                else:
                    # Verify hash
                    import hashlib
                    actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                    expected_hash = info.get("sha256") or info.get("hash")
                    if actual_hash != expected_hash:
                        hash_mismatches.append(path)
            
            if missing_files:
                print(f"  ⚠ {len(missing_files)} file(s) in manifest but missing from filesystem")
                for f in missing_files[:3]:  # Show first 3
                    print(f"    - {f}")
                if len(missing_files) > 3:
                    print(f"    ... and {len(missing_files) - 3} more")
                issues.append(f"{len(missing_files)} files in manifest are missing")
            
            if hash_mismatches:
                print(f"  ✗ {len(hash_mismatches)} file(s) have hash mismatches")
                for f in hash_mismatches[:3]:
                    print(f"    - {f}")
                issues.append(f"{len(hash_mismatches)} files have hash mismatches")
            
            if not missing_files and not hash_mismatches:
                print(f"  ✓ Manifest integrity verified ({len(manifest_dict)} modules)")
    except Exception as e:
        print(f"  ✗ Manifest integrity check failed: {e}")
        issues.append(f"Manifest integrity issue: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    if issues:
        print(f"VALIDATION FAILED - {len(issues)} issue(s) found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("VALIDATION PASSED - All checks successful")
    print("=" * 60 + "\n")
    
    return len(issues) == 0


def clean_temporary_files():
    """Clean temporary files and build artifacts."""
    print("\n" + "=" * 60)
    print("CLEANING TEMPORARY FILES")
    print("=" * 60 + "\n")
    
    cleaned = []
    
    # Patterns to clean
    patterns = [
        ("*.pyc", "Python bytecode files"),
        ("__pycache__", "Python cache directories"),
        (".pytest_cache", "Pytest cache"),
        ("*.log", "Old log files"),
        (".mypy_cache", "MyPy cache")
    ]
    
    for pattern, description in patterns:
        count = 0
        for item in Path(".").rglob(pattern):
            if item.exists():
                if item.is_file():
                    item.unlink()
                    count += 1
                elif item.is_dir():
                    import shutil
                    shutil.rmtree(item)
                    count += 1
        if count > 0:
            print(f"  ✓ Cleaned {count} {description}")
            cleaned.append((description, count))
    
    print("\n" + "=" * 60)
    if cleaned:
        print(f"CLEANED {sum(c[1] for c in cleaned)} items")
    else:
        print("NO TEMPORARY FILES FOUND")
    print("=" * 60 + "\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convergence Cycle Engine CLI - Advanced Build Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_cycle.py                  # Run full convergence cycle
  python run_cycle.py --status         # Show current status
  python run_cycle.py --history        # Show version history
  python run_cycle.py --snapshot       # Create snapshot only
  python run_cycle.py --validate       # Validate system integrity
  python run_cycle.py --clean          # Clean temporary files
        """
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show current version status"
    )
    
    parser.add_argument(
        "--history",
        action="store_true",
        help="Show version history"
    )
    
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Create snapshot without running full cycle"
    )
    
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate system integrity"
    )
    
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean temporary files and build artifacts"
    )
    
    args = parser.parse_args()
    
    # Handle commands
    if args.status:
        show_status()
    elif args.history:
        show_history()
    elif args.snapshot:
        create_snapshot()
    elif args.validate:
        success = validate_system()
        sys.exit(0 if success else 1)
    elif args.clean:
        clean_temporary_files()
    else:
        # Run full convergence cycle
        print("\n" + "=" * 60)
        print("RUNNING CONVERGENCE CYCLE")
        print("=" * 60 + "\n")
        
        engine = ConvergenceCycleEngine()
        success = engine.run_cycle()
        
        if success:
            print("\n✓ Convergence cycle completed successfully!")
            show_status()
            sys.exit(0)
        else:
            print("\n✗ Convergence cycle completed with failures.")
            print("  Check logs/convergence_cycle.log for details.\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
