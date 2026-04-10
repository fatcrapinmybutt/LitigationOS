"""P1D: Bulk fix hardcoded C:\\Users\\andre\\ paths in engine files.

Replaces hardcoded paths with Path(__file__).resolve().parents[N] resolution.
Safe: reads each file, computes correct parent depth, writes back only if changed.
"""
import os
import sys
from pathlib import Path

REPO = Path(r"C:\Users\andre\LitigationOS")
ENGINES = REPO / "00_SYSTEM" / "engines"

# Hardcoded path variants to find in source text
HC_DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
HC_DB_ESC = r"C:\\Users\\andre\\LitigationOS\\litigation_context.db"
HC_ROOT = r"C:\Users\andre\LitigationOS"
HC_ROOT_ESC = r"C:\\Users\\andre\\LitigationOS"
HC_CARGO = r"C:\Users\andre\.cargo\bin\typst.exe"

# Specific files to SKIP (already properly handled or should not change)
SKIP_FILES = {
    "themanbearpig.py",      # User mandate: DO NOT MODIFY
    "project_kraken.py",     # DO NOT REGRESS
}

stats = {"files_scanned": 0, "files_fixed": 0, "changes": 0}


def compute_depth(filepath: Path) -> int:
    """Compute parents[N] depth from file to repo root."""
    rel = filepath.relative_to(REPO)
    return len(rel.parts) - 1


def has_path_import(text: str) -> bool:
    """Check if file already imports Path."""
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        if ("from pathlib import" in s and "Path" in s) or "import pathlib" in s:
            return True
    return False


def add_path_import(text: str) -> str:
    """Add 'from pathlib import Path' after existing imports."""
    lines = text.splitlines(keepends=True)
    insert_idx = 0
    for j, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("import ") or s.startswith("from "):
            insert_idx = j + 1
        elif s.startswith("def ") or s.startswith("class ") or (s and not s.startswith("#") and not s.startswith('"""') and not s.startswith("'''")):
            if insert_idx > 0:
                break
    lines.insert(insert_idx, "from pathlib import Path\n")
    return "".join(lines)


def fix_content(filepath: Path, text: str) -> tuple[str, list[str]]:
    """Fix hardcoded paths in file content. Returns (new_text, list_of_changes)."""
    depth = compute_depth(filepath)
    changes = []
    original = text

    db_resolver = f'str(Path(__file__).resolve().parents[{depth}] / "litigation_context.db")'
    root_resolver = f'Path(__file__).resolve().parents[{depth}]'

    # --- Fix DB path patterns ---
    # r"C:\Users\andre\LitigationOS\litigation_context.db"
    for quote in ['"', "'"]:
        old_raw = f'r{quote}{HC_DB}{quote}'
        old_plain = f'{quote}{HC_DB}{quote}'
        old_path_raw = f'Path(r{quote}{HC_DB}{quote})'
        old_path_plain = f'Path({quote}{HC_DB}{quote})'

        for old in [old_path_raw, old_path_plain, old_raw, old_plain]:
            if old in text:
                text = text.replace(old, db_resolver)
                changes.append(f"  DB: {old[:60]}... -> dynamic resolver")

    # Escaped backslash variant: "C:\\Users\\andre\\..."
    for quote in ['"', "'"]:
        old_esc = f'{quote}{HC_DB_ESC}{quote}'
        if old_esc in text:
            text = text.replace(old_esc, db_resolver)
            changes.append(f"  DB(esc): escaped path -> dynamic resolver")

    # --- Fix repo root patterns ---
    # Must come AFTER db fix to avoid partial replacement
    for quote in ['"', "'"]:
        old_path_raw = f'Path(r{quote}{HC_ROOT}{quote})'
        old_path_plain = f'Path({quote}{HC_ROOT}{quote})'
        old_raw = f'r{quote}{HC_ROOT}{quote}'
        old_plain = f'{quote}{HC_ROOT}{quote}'

        # Path(...) variants -> root_resolver (already a Path)
        for old in [old_path_raw, old_path_plain]:
            if old in text:
                text = text.replace(old, root_resolver)
                changes.append(f"  ROOT(Path): {old[:50]}... -> parents[{depth}]")

        # String variants -> str(root_resolver)
        for old in [old_raw, old_plain]:
            if old in text:
                text = text.replace(old, f'str({root_resolver})')
                changes.append(f"  ROOT(str): {old[:50]}... -> str(parents[{depth}])")

    # Escaped root variant
    for quote in ['"', "'"]:
        old_esc_path = f'Path({quote}{HC_ROOT_ESC}{quote})'
        old_esc = f'{quote}{HC_ROOT_ESC}{quote}'
        if old_esc_path in text:
            text = text.replace(old_esc_path, root_resolver)
            changes.append(f"  ROOT(esc,Path): -> parents[{depth}]")
        elif old_esc in text:
            text = text.replace(old_esc, f'str({root_resolver})')
            changes.append(f"  ROOT(esc,str): -> str(parents[{depth}])")

    # --- Fix typst binary path ---
    if HC_CARGO in text:
        for quote in ['"', "'"]:
            old_cargo = f'r{quote}{HC_CARGO}{quote}'
            new_cargo = f'str(Path.home() / ".cargo" / "bin" / "typst.exe")'
            if old_cargo in text:
                text = text.replace(old_cargo, new_cargo)
                changes.append(f"  CARGO: typst path -> Path.home() based")

    # --- Ensure Path import if we made changes ---
    if changes and not has_path_import(text):
        text = add_path_import(text)
        changes.append(f"  IMPORT: added 'from pathlib import Path'")

    return text, changes


def process_dir(directory: Path, label: str):
    """Process all .py files in directory tree."""
    print(f"\n--- Scanning {label} ---")
    for py_file in sorted(directory.rglob("*.py")):
        if py_file.name in SKIP_FILES:
            continue

        stats["files_scanned"] += 1

        try:
            text = py_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"  [SKIP] {py_file.name}: {e}")
            continue

        # Quick check: does this file have any hardcoded paths?
        if HC_ROOT not in text and HC_ROOT_ESC not in text:
            continue

        new_text, changes = fix_content(py_file, text)

        if changes:
            py_file.write_text(new_text, encoding="utf-8")
            stats["files_fixed"] += 1
            stats["changes"] += len(changes)
            rel = py_file.relative_to(REPO)
            print(f"\n[FIXED] {rel} ({len(changes)} changes):")
            for c in changes:
                print(c)


def main():
    print("=" * 70)
    print("P1D: Bulk Path Fix")
    print("  Hardcoded C:\\Users\\andre\\ -> Path(__file__).resolve().parents[N]")
    print("=" * 70)

    # Process engines
    process_dir(ENGINES, "00_SYSTEM/engines/")

    # Process shared (skip config.py — handled separately via edit tool)
    shared = REPO / "00_SYSTEM" / "shared"
    # We still scan shared but config.py will be fixed by edit tool
    process_dir(shared, "00_SYSTEM/shared/")

    print(f"\n{'=' * 70}")
    print(f"SUMMARY:")
    print(f"  Files scanned: {stats['files_scanned']}")
    print(f"  Files fixed:   {stats['files_fixed']}")
    print(f"  Total changes: {stats['changes']}")
    print(f"{'=' * 70}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
