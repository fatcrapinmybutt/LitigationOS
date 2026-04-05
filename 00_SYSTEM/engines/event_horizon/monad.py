"""
EVENT HORIZON Δ∞ — MONAD: Atomic Operations
=============================================
Composable, reusable primitives used by every subsystem.
Every file operation is atomic: it either fully succeeds or fully rolls back.
"""
from __future__ import annotations

import hashlib
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import (
    JUNK_EXTENSIONS,
    PROTECTED_DIRS,
    ALLOWED_ROOT_FILES,
    CANONICAL_FOLDERS,
    REPO_ROOT,
    MoveRecord,
)


# ---------------------------------------------------------------------------
# Classification primitives
# ---------------------------------------------------------------------------
EXTENSION_GROUPS = {
    "text":     {".txt", ".rst", ".log", ".cfg", ".ini", ".conf"},
    "markdown": {".md"},
    "code":     {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
                 ".c", ".h", ".cpp", ".cs", ".rb", ".php", ".sh", ".bat",
                 ".ps1", ".map", ".mdx"},
    "data":     {".csv", ".tsv", ".json", ".jsonl", ".jsonc", ".xml", ".yaml", ".yml",
                 ".toml", ".sql", ".cypher", ".graphml"},
    "document": {".docx", ".doc", ".pdf", ".rtf", ".odt", ".pptx", ".xlsx",
                 ".xls"},
    "image":    {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif",
                 ".webp", ".svg", ".ico"},
    "video":    {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"},
    "audio":    {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"},
    "archive":  {".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".xz"},
    "web":      {".html", ".htm", ".css", ".scss", ".less"},
    "config":   {".env", ".gitignore", ".editorconfig", ".prettierrc",
                 ".eslintrc", ".gitconfig", ".gitattributes", ".shellcheckrc",
                 ".vsixmanifest", ".cat", ".cmake", ".code-snippets",
                 ".ps1xml", ".psd1", ".psm1"},
    "test":     {".test", ".spec"},
    "database": {".sqlite", ".db", ".db-shm", ".db-wal", ".db-journal"},
    "compiled": {".pdb", ".dll", ".winmd", ".exe", ".pyd", ".so", ".o",
                 ".rev", ".rhk"},
}

# Reverse map: extension → group
_EXT_TO_GROUP: dict[str, str] = {}
for group, exts in EXTENSION_GROUPS.items():
    for ext in exts:
        _EXT_TO_GROUP[ext] = group


def classify_extension(ext: str) -> str:
    """Classify a file extension into a group name."""
    return _EXT_TO_GROUP.get(ext.lower(), "other")


def is_junk(name: str, ext: str) -> bool:
    """Check if a file is junk/temp that should be cleaned."""
    if ext.lower() in JUNK_EXTENSIONS:
        return True
    if name.lower() in {"thumbs.db", ".ds_store", "desktop.ini"}:
        return True
    if name.startswith("~$"):  # Office temp files
        return True
    return False


def is_protected_dir(path: Path) -> bool:
    """Check if a path is within a protected directory."""
    parts = set(path.parts)
    return bool(parts & PROTECTED_DIRS)


def is_allowed_root_file(name: str) -> bool:
    """Check if a filename is allowed to stay at repository root."""
    return name in ALLOWED_ROOT_FILES


def is_canonical_path(path: Path) -> bool:
    """Check if a path is already within a canonical folder."""
    try:
        rel = path.relative_to(REPO_ROOT)
        top = rel.parts[0] if rel.parts else ""
        return top in CANONICAL_FOLDERS
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Hash primitives
# ---------------------------------------------------------------------------
def hash_file(path: Path, algorithm: str = "sha256") -> Optional[str]:
    """Compute hash of a file. Returns None on error."""
    h = hashlib.new(algorithm)
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def quick_hash(path: Path) -> Optional[str]:
    """Quick hash using first 64KB + last 64KB + file size.
    Good enough for dedup without reading entire large files."""
    try:
        size = path.stat().st_size
        h = hashlib.sha256()
        h.update(str(size).encode())
        with open(path, "rb") as f:
            h.update(f.read(65536))
            if size > 131072:
                f.seek(-65536, 2)
                h.update(f.read(65536))
        return h.hexdigest()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# File operation primitives (atomic, with rollback support)
# ---------------------------------------------------------------------------
# Windows NTFS max path length (conservative — long path support may be enabled)
MAX_PATH_LENGTH = 255

# Characters that can break NTFS filenames or shell commands
_DANGEROUS_CHARS = set('<>:"/\\|?*\x00')
_WARN_CHARS = set('[]{}()$&;`!#%@^~')


def _sanitize_filename(name: str) -> str:
    """Sanitize a filename for safe NTFS storage.
    Replaces dangerous characters with underscore, normalizes Unicode."""
    import unicodedata
    # Normalize Unicode (NFC — precomposed form, most compatible with NTFS)
    name = unicodedata.normalize("NFC", name)
    # Replace dangerous chars
    sanitized = "".join(c if c not in _DANGEROUS_CHARS else "_" for c in name)
    # Trim trailing dots/spaces (Windows silently strips these)
    sanitized = sanitized.rstrip(". ")
    return sanitized or "_unnamed_"


def _check_path_length(path: Path) -> bool:
    """Check if path exceeds Windows MAX_PATH limit."""
    return len(str(path)) <= MAX_PATH_LENGTH


def safe_move(source: Path, destination: Path, dry_run: bool = False) -> MoveRecord:
    """
    Move a file atomically. Creates destination directories as needed.
    Returns a MoveRecord with rollback_path for undo.
    
    Handles:
    - Name collisions (appends _1, _2, etc.)
    - Dangerous/OCR-garbled filenames (sanitized)
    - Path length > 255 (truncated stem)
    - Cross-device moves (via shutil)
    - Full rollback support
    """
    rec = MoveRecord(
        source=source,
        destination=destination,
        timestamp=datetime.now(),
        rollback_path=source,
    )

    if dry_run:
        rec.success = True
        return rec

    try:
        # Sanitize destination filename if it has dangerous chars
        dest_name = destination.name
        sanitized = _sanitize_filename(dest_name)
        if sanitized != dest_name:
            destination = destination.parent / sanitized
            rec.destination = destination

        # Check path length — truncate stem if needed
        if not _check_path_length(destination):
            stem = destination.stem
            suffix = destination.suffix
            max_stem = MAX_PATH_LENGTH - len(str(destination.parent)) - len(suffix) - 2
            if max_stem > 10:
                destination = destination.parent / f"{stem[:max_stem]}{suffix}"
                rec.destination = destination

        # Ensure destination directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Handle name collision
        final_dest = destination
        if final_dest.exists():
            stem = final_dest.stem
            suffix = final_dest.suffix
            counter = 1
            while final_dest.exists():
                final_dest = final_dest.parent / f"{stem}_{counter}{suffix}"
                counter += 1
            rec.destination = final_dest

        # Move using shutil (handles cross-device, special chars)
        shutil.move(str(source), str(final_dest))
        rec.success = True

    except PermissionError as e:
        rec.success = False
        rec.error = f"Permission denied: {e}"
    except OSError as e:
        err = str(e).lower()
        if "disk" in err or "full" in err or "space" in err:
            rec.success = False
            rec.error = f"Disk full: {e}"
        else:
            rec.success = False
            rec.error = f"OS error: {e}"
    except Exception as e:
        rec.success = False
        rec.error = str(e)

    return rec


def safe_copy(source: Path, destination: Path, dry_run: bool = False) -> MoveRecord:
    """Copy a file atomically (preserves original)."""
    rec = MoveRecord(source=source, destination=destination, timestamp=datetime.now())

    if dry_run:
        rec.success = True
        return rec

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(destination))
        rec.success = True
    except Exception as e:
        rec.success = False
        rec.error = str(e)

    return rec


def rollback_move(rec: MoveRecord, dry_run: bool = False) -> bool:
    """Undo a file move using the rollback_path in MoveRecord."""
    if not rec.rollback_path or not rec.destination.exists():
        return False

    if dry_run:
        return True

    try:
        rec.rollback_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(rec.destination), str(rec.rollback_path))
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Content sampling
# ---------------------------------------------------------------------------
def sample_content(path: Path, max_bytes: int = 2048) -> Optional[str]:
    """Read first N bytes of a text file. Returns None for binary files."""
    text_exts = set()
    for group in ("text", "markdown", "code", "data", "web", "config"):
        text_exts |= EXTENSION_GROUPS.get(group, set())

    if path.suffix.lower() not in text_exts:
        return None

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(max_bytes)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Directory utilities
# ---------------------------------------------------------------------------
def ensure_canonical_dirs(root: Path = REPO_ROOT):
    """Ensure all 13 canonical folders exist."""
    for folder in CANONICAL_FOLDERS:
        (root / folder).mkdir(exist_ok=True)


def count_files(directory: Path, recursive: bool = True) -> int:
    """Count files in a directory."""
    try:
        if recursive:
            return sum(1 for _ in directory.rglob("*") if _.is_file())
        return sum(1 for _ in directory.iterdir() if _.is_file())
    except Exception:
        return 0
