#!/usr/bin/env python3
"""
C: DRIVE ORGANIZER — Surgical cleanup of C:\\Users\\andre
==========================================================
PROTECTED (never touched):
  - LitigationOS, Scans, AppData, all dot-folders
  - Windows shell junctions (Application Data, Local Settings, etc.)
  - pylibs, .vscode, .ollama, .copilot, .docker, etc.

ACTIONS:
  1. Consolidate stray projects into Projects/
  2. Consolidate loose tools into Tools/
  3. Clean empty Windows shell folders
  4. Flatten deep nesting in Github/ and VoidWalker*/

Usage:
    python c_drive_organize.py --dry-run
    python c_drive_organize.py
"""
import os
import sys
import shutil
import time
from pathlib import Path
from collections import Counter
from datetime import datetime

HOME = Path(r"C:\Users\andre")

# ═══════════════════════════════════════════════════════════
# PROTECTION LISTS
# ═══════════════════════════════════════════════════════════

# NEVER touch these folders (case-insensitive match)
PROTECTED = {
    "litigationos", "scans", "appdata",
    "desktop", "documents", "downloads", "music", "pictures", "videos",
    "favorites", "links", "searches", "contacts",
    "onedrive", "saved games",
    # Windows junctions/system
    "application data", "local settings", "cookies",
    "my documents", "nethood", "printhood", "recent",
    "sendto", "start menu", "templates",
    # Tool config (dot-folders handled separately)
    "pylibs",
}

# Also protect anything starting with dot (app config folders)
def is_protected(name: str) -> bool:
    if name.startswith("."):
        return True
    if name.lower() in PROTECTED:
        return True
    return False

# ═══════════════════════════════════════════════════════════
# CONSOLIDATION RULES
# ═══════════════════════════════════════════════════════════

# Move these into Projects/
PROJECT_FOLDERS = [
    "VoidWalker", "VoidWalker2",
    "czkawka-master",
    "Github",
    "LITIGATIONOS_MASTER",
    "CytoscapeConfiguration",
]

# Move these into Tools/
TOOL_FOLDERS = [
    "pandoc",
    "rclone",
    "node-compile-cache",
]

# Folders that match a glob → Tools/
TOOL_GLOBS = [
    "java-*",
]

# Delete these (empty/useless)
CLEANUP_FOLDERS = [
    "3D Objects",
    "__pycache__",
]


def safe_move_tree(src: Path, dst_parent: Path, dry_run: bool) -> int:
    """Move a folder tree into dst_parent/, preserving the folder name. Returns file count."""
    dst = dst_parent / src.name
    count = sum(1 for _ in src.rglob("*") if _.is_file()) if src.exists() else 0
    if dry_run:
        print(f"    [DRY] {src.name}/ → {dst_parent.name}/{src.name}/  ({count} files)")
        return count
    try:
        if dst.exists():
            # Merge: move files one by one
            for fp in src.rglob("*"):
                if fp.is_file():
                    rel = fp.relative_to(src)
                    target = dst / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    if target.exists():
                        stem = target.stem
                        suffix = target.suffix
                        counter = 2
                        while target.exists():
                            target = target.parent / f"{stem}_{counter}{suffix}"
                            counter += 1
                    try:
                        fp.rename(target)
                    except OSError:
                        shutil.move(str(fp), str(target))
            # Clean source
            shutil.rmtree(str(src), ignore_errors=True)
        else:
            src.rename(dst)
        print(f"    {src.name}/ → {dst_parent.name}/{src.name}/  ({count} files)")
    except Exception as e:
        print(f"    ERROR {src.name}: {e}")
    return count


def flatten_deep_folder(folder: Path, max_depth: int, dry_run: bool) -> int:
    """Flatten files deeper than max_depth to that depth level."""
    flattened = 0
    for dirpath, dirnames, filenames in os.walk(str(folder)):
        dp = Path(dirpath)
        rel = dp.relative_to(folder)
        depth = len(rel.parts)
        if depth < max_depth:
            continue
        # Files at this depth or deeper should be moved up to max_depth level
        target_dir = folder
        for part in rel.parts[:max_depth]:
            target_dir = target_dir / part
        for fname in filenames:
            src = dp / fname
            dst = target_dir / fname
            if dst.exists():
                stem = dst.stem
                suffix = dst.suffix
                counter = 2
                while dst.exists():
                    dst = target_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
            if not dry_run:
                try:
                    target_dir.mkdir(parents=True, exist_ok=True)
                    src.rename(dst)
                    flattened += 1
                except Exception:
                    try:
                        shutil.move(str(src), str(dst))
                        flattened += 1
                    except Exception:
                        pass
            else:
                flattened += 1
    return flattened


def run(dry_run: bool = False):
    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"\n{'='*60}")
    print(f"  C: DRIVE ORGANIZER — {HOME} [{mode}]")
    print(f"{'='*60}")
    t0 = time.time()
    total_moved = 0

    # Phase 1: Create consolidation folders
    print(f"\nPhase 1: CREATE CONSOLIDATION FOLDERS")
    projects_dir = HOME / "Projects"
    tools_dir = HOME / "Tools"
    for d in [projects_dir, tools_dir]:
        if not dry_run:
            d.mkdir(exist_ok=True)
        print(f"  {'[DRY] ' if dry_run else ''}Created {d.name}/")

    # Phase 2: Consolidate projects
    print(f"\nPhase 2: CONSOLIDATE PROJECTS")
    for name in PROJECT_FOLDERS:
        src = HOME / name
        if src.exists() and src.is_dir():
            total_moved += safe_move_tree(src, projects_dir, dry_run)

    # Phase 3: Consolidate tools
    print(f"\nPhase 3: CONSOLIDATE TOOLS")
    for name in TOOL_FOLDERS:
        src = HOME / name
        if src.exists() and src.is_dir():
            total_moved += safe_move_tree(src, tools_dir, dry_run)

    # Handle glob patterns (java-*)
    for pattern in TOOL_GLOBS:
        for src in HOME.glob(pattern):
            if src.is_dir() and not is_protected(src.name):
                total_moved += safe_move_tree(src, tools_dir, dry_run)

    # Phase 4: Clean empty/useless folders
    print(f"\nPhase 4: CLEAN EMPTY FOLDERS")
    cleaned = 0
    for name in CLEANUP_FOLDERS:
        target = HOME / name
        if target.exists():
            try:
                items = list(target.rglob("*"))
                file_count = sum(1 for f in items if f.is_file())
                if file_count <= 3:  # empty or trivial
                    if not dry_run:
                        shutil.rmtree(str(target), ignore_errors=True)
                    print(f"  {'[DRY] ' if dry_run else ''}Removed {name}/  ({file_count} files)")
                    cleaned += 1
                else:
                    print(f"  KEPT {name}/ — {file_count} files")
            except Exception as e:
                print(f"  ERROR {name}: {e}")

    # Phase 5: Flatten deep nesting in Projects/
    print(f"\nPhase 5: FLATTEN DEEP NESTING IN Projects/")
    if projects_dir.exists():
        # For each project, flatten anything deeper than 3 levels
        # (Projects/ProjectName/category/file is fine, deeper is not)
        for proj in projects_dir.iterdir():
            if proj.is_dir():
                flat_count = flatten_deep_folder(proj, max_depth=3, dry_run=dry_run)
                if flat_count:
                    print(f"  {proj.name}: flattened {flat_count} files")

        # Clean empty subdirs
        if not dry_run:
            for dirpath, _, _ in os.walk(str(projects_dir), topdown=False):
                dp = Path(dirpath)
                if dp == projects_dir:
                    continue
                try:
                    if not any(dp.iterdir()):
                        dp.rmdir()
                except OSError:
                    pass

    # Summary
    elapsed = time.time() - t0
    print(f"\n{'─'*60}")
    print(f"  C: DONE in {elapsed:.1f}s")
    print(f"    files_consolidated: {total_moved:,}")
    print(f"    empty_folders_cleaned: {cleaned}")
    print(f"{'─'*60}")

    # Show final state
    print(f"\n  Final C:\\Users\\andre layout:")
    for item in sorted(HOME.iterdir()):
        if item.name.startswith(".") or item.name.lower() in {"appdata", "ntuser.dat", "ntuser.dat.log1", "ntuser.dat.log2", "ntuser.ini"}:
            continue
        if not item.is_dir():
            continue
        try:
            count = sum(1 for _ in item.rglob("*") if _.is_file())
        except Exception:
            count = -1
        marker = " ★" if item.name in ("LitigationOS", "Scans") else ""
        marker = " 🔒" if is_protected(item.name) else marker
        print(f"    {item.name}/  ({count:,} files){marker}")


def main():
    dry_run = "--dry-run" in sys.argv
    run(dry_run=dry_run)


if __name__ == "__main__":
    main()
