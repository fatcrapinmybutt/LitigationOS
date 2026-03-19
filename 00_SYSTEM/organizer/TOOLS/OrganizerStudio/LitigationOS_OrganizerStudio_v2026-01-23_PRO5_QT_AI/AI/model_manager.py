#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

def _default_cache_dir() -> Path:
    return Path(os.environ.get("HF_HOME") or "F:/LitigationOS/_HF_CACHE").resolve()

def ensure_hf_deps() -> None:
    import huggingface_hub  # noqa

def download_model(repo_id: str, cache_dir: Optional[str] = None) -> str:
    """
    Download a Hugging Face model snapshot into cache_dir using huggingface_hub.
    Returns local path to the snapshot directory.
    """
    ensure_hf_deps()
    from huggingface_hub import snapshot_download

    cdir = Path(cache_dir).resolve() if cache_dir else _default_cache_dir()
    cdir.mkdir(parents=True, exist_ok=True)

    path = snapshot_download(
        repo_id=repo_id,
        cache_dir=str(cdir),
        local_files_only=False,
        resume_download=True,
    )
    return str(Path(path).resolve())

def resolve_local_model_dir(repo_id: str, cache_dir: Optional[str] = None) -> Optional[str]:
    """
    Best-effort lookup for an already-downloaded model in the HF cache.
    """
    cdir = Path(cache_dir).resolve() if cache_dir else _default_cache_dir()
    if not cdir.exists():
        return None
    try:
        from huggingface_hub import snapshot_download
        path = snapshot_download(repo_id=repo_id, cache_dir=str(cdir), local_files_only=True)
        return str(Path(path).resolve())
    except Exception:
        return None
