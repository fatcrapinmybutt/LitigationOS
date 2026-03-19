
from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional, Tuple

from .utils import file_size_mb

def _matches_any_glob(rel: str, globs: List[str]) -> bool:
    rel_norm = rel.replace("\\", "/")
    for g in globs:
        if fnmatch.fnmatch(rel_norm, g.replace("\\", "/")):
            return True
    return False

def iter_files(
    root: Path,
    include_exts: List[str],
    ignore_globs: List[str],
    max_file_mb: float,
    max_files: int,
):
    """
    Yields (path, relpath) for files under root with allowed extensions, skipping ignored patterns and huge files.
    """
    count = 0
    include_exts = [e.lower() for e in include_exts]
    for dirpath, dirnames, filenames in os.walk(root):
        # quick prune ignored dirs
        rel_dir = str(Path(dirpath).relative_to(root)).replace("\\", "/")
        # Mutate dirnames in-place to prune
        pruned = []
        for d in list(dirnames):
            rel = (Path(rel_dir) / d).as_posix()
            if _matches_any_glob(rel + "/**", ignore_globs) or _matches_any_glob(rel + "/", ignore_globs):
                pruned.append(d)
        for d in pruned:
            dirnames.remove(d)

        for fn in filenames:
            p = Path(dirpath) / fn
            rel = p.relative_to(root).as_posix()
            if _matches_any_glob(rel, ignore_globs):
                continue
            ext = p.suffix.lower()
            if ext not in include_exts:
                continue
            try:
                if file_size_mb(p) > max_file_mb:
                    continue
            except Exception:
                continue
            yield p, rel
            count += 1
            if count >= max_files:
                return

