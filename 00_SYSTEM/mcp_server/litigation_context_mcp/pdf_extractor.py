"""PDF text extraction and drive scanning using PyMuPDF with robust error handling."""

import functools
import hashlib
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Generator

import pymupdf  # PyMuPDF

logger = logging.getLogger("litigation_context_mcp")

# Max time per PDF extraction (seconds) - prevents hangs on corrupt files
MAX_EXTRACT_SECONDS = int(os.environ.get("LITIGATION_PDF_TIMEOUT", "120"))
# Max file size to attempt (bytes) - skip enormous PDFs that would exhaust memory
MAX_FILE_SIZE = int(os.environ.get("LITIGATION_MAX_PDF_BYTES", str(500 * 1024 * 1024)))  # 500 MB

# --- Windows-safe threaded timeout context manager ---

class ThreadedTimeout:
    """Context manager that enforces a timeout using a background thread.

    Works on Windows (where signal.alarm is unavailable).
    Wraps a callable; raises TimeoutError if it doesn't finish in time.
    """

    def __init__(self, seconds: int):
        self.seconds = seconds
        self._result = None
        self._exception = None

    def run(self, func, *args, **kwargs):
        """Run *func* in a thread; raise TimeoutError if it exceeds the deadline."""
        def _target():
            try:
                self._result = func(*args, **kwargs)
            except Exception as exc:
                self._exception = exc

        thread = threading.Thread(target=_target, daemon=True)
        thread.start()
        thread.join(timeout=self.seconds)
        if thread.is_alive():
            raise TimeoutError(
                f"Operation timed out after {self.seconds}s"
            )
        if self._exception is not None:
            raise self._exception
        return self._result


# --- Retry decorator for transient OS / file-lock errors ---

def retry_on_file_error(func=None, *, retries: int = 3, base_delay: float = 1.0):
    """Decorator: retry on OSError / PermissionError / IOError with exponential backoff."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(retries + 1):
                try:
                    return fn(*args, **kwargs)
                except (OSError, PermissionError, IOError) as exc:
                    last_exc = exc
                    if attempt < retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            "Retryable %s on attempt %d/%d for %s – retrying in %.1fs: %s",
                            type(exc).__name__, attempt + 1, retries, fn.__name__, delay, exc,
                        )
                        time.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


@retry_on_file_error
def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


@retry_on_file_error
def extract_pdf_text(file_path: str) -> Dict[str, Any]:
    """Extract text from a PDF file page-by-page with resilient error handling.

    Handles corrupt pages gracefully — extracts what it can, logs failures.
    Raises ValueError for unrecoverable issues (missing file, not a PDF, too large).
    """
    if not os.path.isfile(file_path):
        raise ValueError(f"File not found: {file_path}")
    if not file_path.lower().endswith(".pdf"):
        raise ValueError(f"Not a PDF file: {file_path}")

    stat = os.stat(file_path)
    if stat.st_size > MAX_FILE_SIZE:
        raise ValueError(
            f"File too large ({stat.st_size / (1024*1024):.1f} MB). "
            f"Max is {MAX_FILE_SIZE / (1024*1024):.0f} MB. Set LITIGATION_MAX_PDF_BYTES to override."
        )
    if stat.st_size == 0:
        raise ValueError("File is empty (0 bytes).")

    sha256 = compute_sha256(file_path)

    try:
        doc = pymupdf.open(file_path)
    except Exception as e:
        raise ValueError(f"Cannot open PDF ({type(e).__name__}): {e}")

    pages: List[Dict[str, Any]] = []
    errors: List[str] = []
    for i in range(len(doc)):
        try:
            page = doc[i]
            timeout = ThreadedTimeout(MAX_EXTRACT_SECONDS)
            text = timeout.run(page.get_text, "text").strip()
            if text:
                pages.append({"page_number": i + 1, "text_content": text})
        except TimeoutError:
            errors.append(f"Page {i + 1}: timed out after {MAX_EXTRACT_SECONDS}s")
            logger.warning("Timeout extracting page %d from %s", i + 1, file_path)
        except Exception as e:
            errors.append(f"Page {i + 1}: {type(e).__name__}: {e}")
            logger.warning("Error extracting page %d from %s: %s", i + 1, file_path, e)

    doc.close()

    if not pages and errors:
        raise ValueError(
            f"No text extracted from any of {len(doc)} pages. "
            f"Errors: {'; '.join(errors[:5])}"
        )

    return {
        "file_path": os.path.abspath(file_path),
        "file_name": os.path.basename(file_path),
        "file_size_bytes": stat.st_size,
        "modified_date": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "page_count": len(pages),
        "total_pages_in_pdf": len(doc) if 'doc' in dir() else len(pages),
        "sha256_hash": sha256,
        "pages": pages,
        "extraction_errors": errors,
    }


def scan_for_pdfs(
    root_path: str,
    max_results: int = 5000,
) -> Generator[Dict[str, Any], None, None]:
    """Walk a directory tree yielding PDF file info dicts.

    Skips inaccessible directories silently.
    """
    count = 0
    for dirpath, _dirnames, filenames in os.walk(root_path, topdown=True):
        try:
            for fname in filenames:
                if fname.lower().endswith(".pdf"):
                    full_path = os.path.join(dirpath, fname)
                    try:
                        stat = os.stat(full_path)
                        yield {
                            "file_path": os.path.abspath(full_path),
                            "file_name": fname,
                            "file_size_bytes": stat.st_size,
                            "modified_date": datetime.fromtimestamp(
                                stat.st_mtime, tz=timezone.utc
                            ).isoformat(),
                        }
                        count += 1
                        if count >= max_results:
                            return
                    except OSError:
                        continue
        except PermissionError:
            continue


def get_available_drives() -> List[str]:
    """Return list of available drive letters on Windows."""
    if sys.platform != "win32":
        return ["/"]
    drives = []
    for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
        path = f"{letter}:\\"
        if os.path.exists(path):
            drives.append(path)
    return drives
