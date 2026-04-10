"""Harvest Engine — Archive extraction (ZIP / 7z).

Extracts ZIP files using stdlib zipfile, 7z files using py7zr (optional).
Preserves internal structure, handles corrupted/password-protected archives
gracefully, and returns structured metadata for downstream pipeline stages.

NO module-level side effects. NO stdout clobbering. NO database connections.
"""

import logging
import os
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# ── Default extraction directory ─────────────────────────────────────────────
DEFAULT_EXTRACT_DIR = Path(r"D:\LitigationOS_tmp\extracted_zips")

# ── Supported archive extensions ─────────────────────────────────────────────
ZIP_EXTENSIONS = frozenset({".zip"})
SEVENZ_EXTENSIONS = frozenset({".7z"})
ALL_ARCHIVE_EXTENSIONS = ZIP_EXTENSIONS | SEVENZ_EXTENSIONS

# ── Lazy import for py7zr ────────────────────────────────────────────────────
_py7zr = None


def _get_py7zr():
    """Lazy-load py7zr. Returns module or None if unavailable."""
    global _py7zr
    if _py7zr is None:
        try:
            import py7zr
            _py7zr = py7zr
        except ImportError:
            logger.warning("py7zr not available — 7z extraction disabled")
            _py7zr = False
    return _py7zr if _py7zr is not False else None


# ── Data classes ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ExtractedFile:
    """Metadata for a single file extracted from an archive."""
    original_path: str
    extracted_path: str
    internal_name: str
    file_size: int
    file_type: str


@dataclass
class ZipResult:
    """Result of extracting a single archive."""
    archive_path: str
    extract_dir: str
    files_extracted: List[ExtractedFile] = field(default_factory=list)
    total_size: int = 0
    errors: List[str] = field(default_factory=list)


# ── Internal helpers ─────────────────────────────────────────────────────────


def _suffix_to_type(path: Path) -> str:
    """Map file suffix to a human-readable type string."""
    ext = path.suffix.lower()
    type_map = {
        ".pdf": "pdf", ".docx": "docx", ".doc": "doc",
        ".txt": "text", ".md": "markdown", ".csv": "csv",
        ".json": "json", ".jsonl": "jsonl", ".xml": "xml",
        ".html": "html", ".htm": "html", ".rtf": "rtf",
        ".jpg": "image", ".jpeg": "image", ".png": "image",
        ".gif": "image", ".bmp": "image", ".tiff": "image",
        ".tif": "image", ".heic": "image", ".mp4": "video",
        ".mp3": "audio", ".wav": "audio", ".eml": "email",
        ".msg": "email", ".db": "database", ".sqlite": "database",
        ".zip": "archive", ".7z": "archive",
    }
    return type_map.get(ext, "unknown")


def _ensure_extract_dir(extract_dir: Path, archive_stem: str) -> Path:
    """Create a subdirectory named after the archive for extraction.

    Returns the subdirectory path. Creates parent dirs as needed.
    """
    dest = extract_dir / archive_stem
    dest.mkdir(parents=True, exist_ok=True)
    return dest


def _collect_extracted_files(
    dest_dir: Path,
    archive_path: str,
) -> List[ExtractedFile]:
    """Walk the extraction directory and build ExtractedFile entries."""
    files: List[ExtractedFile] = []
    try:
        for root, _dirs, filenames in os.walk(dest_dir):
            root_path = Path(root)
            for fname in filenames:
                full_path = root_path / fname
                try:
                    size = full_path.stat().st_size
                except OSError:
                    size = 0
                internal = str(full_path.relative_to(dest_dir))
                files.append(ExtractedFile(
                    original_path=archive_path,
                    extracted_path=str(full_path),
                    internal_name=internal,
                    file_size=size,
                    file_type=_suffix_to_type(full_path),
                ))
    except OSError as exc:
        logger.error("Failed to walk extraction dir %s: %s", dest_dir, exc)
    return files


# ── ZIP extraction ───────────────────────────────────────────────────────────


def _extract_zip(
    archive_path: Path,
    dest_dir: Path,
) -> ZipResult:
    """Extract a .zip archive using stdlib zipfile."""
    result = ZipResult(
        archive_path=str(archive_path),
        extract_dir=str(dest_dir),
    )

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            # Check for password protection
            for info in zf.infolist():
                if info.flag_bits & 0x1:  # encrypted flag
                    msg = f"Password-protected ZIP skipped: {archive_path}"
                    logger.warning(msg)
                    result.errors.append(msg)
                    return result

            # Test archive integrity before full extraction
            bad_file = zf.testzip()
            if bad_file is not None:
                msg = f"Corrupt entry in {archive_path}: {bad_file} — extracting remaining files"
                logger.warning(msg)
                result.errors.append(msg)

            # Extract all members, skipping entries that fail individually
            for member in zf.infolist():
                if member.is_dir():
                    continue
                try:
                    zf.extract(member, dest_dir)
                except (zipfile.BadZipFile, RuntimeError, KeyError) as exc:
                    msg = f"Failed to extract {member.filename} from {archive_path}: {exc}"
                    logger.warning(msg)
                    result.errors.append(msg)
                except Exception as exc:
                    msg = f"Unexpected error extracting {member.filename}: {exc}"
                    logger.error(msg)
                    result.errors.append(msg)

    except zipfile.BadZipFile as exc:
        msg = f"Corrupt ZIP archive {archive_path}: {exc}"
        logger.error(msg)
        result.errors.append(msg)
        return result
    except Exception as exc:
        msg = f"Failed to open ZIP {archive_path}: {exc}"
        logger.error(msg)
        result.errors.append(msg)
        return result

    # Collect what was successfully extracted
    result.files_extracted = _collect_extracted_files(dest_dir, str(archive_path))
    result.total_size = sum(f.file_size for f in result.files_extracted)
    logger.info(
        "ZIP extracted: %s → %d files, %d bytes",
        archive_path.name, len(result.files_extracted), result.total_size,
    )
    return result


# ── 7z extraction ────────────────────────────────────────────────────────────


def _extract_7z(
    archive_path: Path,
    dest_dir: Path,
) -> ZipResult:
    """Extract a .7z archive using py7zr (optional dependency)."""
    result = ZipResult(
        archive_path=str(archive_path),
        extract_dir=str(dest_dir),
    )

    py7zr = _get_py7zr()
    if py7zr is None:
        msg = f"7z extraction unavailable (py7zr not installed) — skipped: {archive_path}"
        logger.warning(msg)
        result.errors.append(msg)
        return result

    try:
        with py7zr.SevenZipFile(archive_path, mode="r") as szf:
            # Password-protected check
            if szf.needs_password():
                msg = f"Password-protected 7z skipped: {archive_path}"
                logger.warning(msg)
                result.errors.append(msg)
                return result

            szf.extractall(path=dest_dir)

    except py7zr.Bad7zFile as exc:
        msg = f"Corrupt 7z archive {archive_path}: {exc}"
        logger.error(msg)
        result.errors.append(msg)
        return result
    except py7zr.PasswordRequired:
        msg = f"Password-protected 7z skipped: {archive_path}"
        logger.warning(msg)
        result.errors.append(msg)
        return result
    except Exception as exc:
        msg = f"Failed to extract 7z {archive_path}: {exc}"
        logger.error(msg)
        result.errors.append(msg)
        return result

    result.files_extracted = _collect_extracted_files(dest_dir, str(archive_path))
    result.total_size = sum(f.file_size for f in result.files_extracted)
    logger.info(
        "7z extracted: %s → %d files, %d bytes",
        archive_path.name, len(result.files_extracted), result.total_size,
    )
    return result


# ── Public API ───────────────────────────────────────────────────────────────


def extract_archive(
    archive_path: str | Path,
    extract_dir: Optional[str | Path] = None,
) -> ZipResult:
    """Extract a single archive (ZIP or 7z) and return structured metadata.

    Args:
        archive_path: Path to the archive file.
        extract_dir: Base directory for extraction. A subdirectory named after
            the archive stem is created automatically. Defaults to
            ``D:\\LitigationOS_tmp\\extracted_zips\\``.

    Returns:
        ZipResult with extraction metadata and any errors encountered.
    """
    archive = Path(archive_path)

    if not archive.is_file():
        return ZipResult(
            archive_path=str(archive),
            extract_dir="",
            errors=[f"Archive not found: {archive}"],
        )

    base_dir = Path(extract_dir) if extract_dir else DEFAULT_EXTRACT_DIR
    dest = _ensure_extract_dir(base_dir, archive.stem)

    ext = archive.suffix.lower()
    if ext in ZIP_EXTENSIONS:
        return _extract_zip(archive, dest)
    elif ext in SEVENZ_EXTENSIONS:
        return _extract_7z(archive, dest)
    else:
        return ZipResult(
            archive_path=str(archive),
            extract_dir=str(dest),
            errors=[f"Unsupported archive format: {ext}"],
        )


def extract_batch(
    archive_paths: List[str | Path],
    extract_dir: Optional[str | Path] = None,
) -> List[ZipResult]:
    """Extract multiple archives sequentially, returning results for each.

    Args:
        archive_paths: List of archive file paths.
        extract_dir: Base directory for extraction (see ``extract_archive``).

    Returns:
        List of ZipResult, one per input archive (order preserved).
    """
    results: List[ZipResult] = []
    for path in archive_paths:
        result = extract_archive(path, extract_dir)
        results.append(result)
    return results


def discover_archives(
    root_dir: str | Path,
    recursive: bool = True,
) -> List[Path]:
    """Scan a directory for extractable archive files.

    Args:
        root_dir: Directory to scan.
        recursive: If True, scan subdirectories. Defaults to True.

    Returns:
        Sorted list of archive file paths found.
    """
    root = Path(root_dir)
    if not root.is_dir():
        logger.warning("Archive scan directory not found: %s", root)
        return []

    archives: List[Path] = []
    try:
        iterator = root.rglob("*") if recursive else root.iterdir()
        for entry in iterator:
            if entry.is_file() and entry.suffix.lower() in ALL_ARCHIVE_EXTENSIONS:
                archives.append(entry)
    except OSError as exc:
        logger.error("Error scanning for archives in %s: %s", root, exc)

    archives.sort()
    logger.info("Discovered %d archives in %s", len(archives), root)
    return archives


def discover_extracted_files(
    extract_dir: str | Path,
    extensions: Optional[frozenset] = None,
) -> List[Path]:
    """Recursively discover files within an extraction directory.

    Useful for feeding extracted files into the main harvest pipeline.

    Args:
        extract_dir: Root of the extraction output.
        extensions: Optional filter — only return files with these suffixes
            (lowercased, including dot). If None, returns all files.

    Returns:
        Sorted list of file paths.
    """
    root = Path(extract_dir)
    if not root.is_dir():
        logger.warning("Extraction directory not found: %s", root)
        return []

    files: List[Path] = []
    try:
        for entry in root.rglob("*"):
            if not entry.is_file():
                continue
            if extensions is not None and entry.suffix.lower() not in extensions:
                continue
            files.append(entry)
    except OSError as exc:
        logger.error("Error scanning extracted files in %s: %s", root, exc)

    files.sort()
    return files
