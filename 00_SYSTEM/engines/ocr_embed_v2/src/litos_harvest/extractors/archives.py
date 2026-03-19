
from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Iterator, Tuple, Optional

def iter_zip_members(zip_path: Path) -> Iterator[Tuple[str, bytes]]:
    """
    Yields (member_name, raw_bytes) for each file member in the zip.
    Note: caller must enforce size limits; this streams into memory per file.
    """
    with zipfile.ZipFile(str(zip_path), "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            # Avoid huge members
            if info.file_size > 250 * 1024 * 1024:
                continue
            with z.open(info, "r") as f:
                yield info.filename, f.read()

def is_zip(path: Path) -> bool:
    return path.suffix.lower() == ".zip"
