#!/usr/bin/env python3
"""
APEX Resource Manager — Prevents OOM on 22 GB RAM system
═════════════════════════════════════════════════════════
Tracks model memory usage, queues tasks when RAM is tight, and
auto-evicts least-recently-used models to keep the system healthy.

This module provides a **thread-safe** memory reservation system for
the APEX model fleet.  It does NOT physically load or unload models —
it tracks *reservations* so that callers can check ``can_load()``
before loading a heavy model into RAM.

Physical model lifecycle is the caller's responsibility.  This
manager only answers: "Given what we've reserved, is there room?"

Design invariants
─────────────────
* Thread-safe — a single ``threading.Lock`` guards all mutable state.
* NEVER imports from the repo root (shadow modules).
* Uses ``Path(__file__).parent`` for all path resolution.
* Zero-crash: every public method is try/excepted.
* No DB connections (pure in-memory bookkeeping).
* Singleton via :func:`get_manager` — all callers share one instance.

Usage::

    >>> from resource_manager import ResourceManager
    >>> rm = ResourceManager()
    >>> rm.can_load("saul-legal")
    True
    >>> rm.request_model("saul-legal")
    True
    >>> rm.request_model("qwen-fast")
    True
    >>> rm.get_usage()
    {'total_ram_gb': 22.0, 'reserved_ram_gb': 6.0, ...}
    >>> rm.release_model("saul-legal")
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────────────
_log = logging.getLogger("apex.resource_manager")
if not _log.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    ))
    _log.addHandler(_h)
    _log.setLevel(logging.INFO)

# ──────────────────────────────────────────────────────────────────────
# Path helpers (never CWD to repo root)
# ──────────────────────────────────────────────────────────────────────
_THIS_DIR: Path = Path(__file__).resolve().parent


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    MODEL MEMORY CATALOGUE                           ║
# ╚══════════════════════════════════════════════════════════════════════╝

# Approximate resident memory footprints in GB.
# These are conservative estimates for the quantised / distilled
# variants actually deployed on the 22 GB system.
MODEL_MEMORY: Dict[str, float] = {
    "saul-legal": 5.1,       # SaulLM-7B-Instruct Q4_K_M GGUF
    "qwen-fast": 1.5,        # Qwen2.5-1.5B Q8_0
    "legal-bert": 0.5,       # legal-bert-base-uncased
    "bert-ner": 0.5,         # dslim/bert-base-NER
    "minilm": 0.1,           # all-MiniLM-L6-v2 (sentence embeddings)
    "manbearpig": 0.3,       # TF-IDF vectors + sklearn classifiers + hot cache
    "phi-mini": 2.0,         # Phi-3-mini Q4_K_M (if available)
    "nomic-embed": 0.3,      # nomic-embed-text (768-dim)
}

# ──────────────────────────────────────────────────────────────────────
# Hardware budget constants
# ──────────────────────────────────────────────────────────────────────
_TOTAL_RAM_GB: float = float(os.environ.get("APEX_TOTAL_RAM_GB", "22.0"))
_RESERVED_RAM_GB: float = float(os.environ.get("APEX_RESERVED_RAM_GB", "6.0"))
_AVAILABLE_RAM_GB: float = _TOTAL_RAM_GB - _RESERVED_RAM_GB

# Safety margin — never let reservations exceed 95 % of available
_SAFETY_FACTOR: float = 0.95
_MAX_USABLE_GB: float = _AVAILABLE_RAM_GB * _SAFETY_FACTOR


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                      RESOURCE MANAGER                               ║
# ╚══════════════════════════════════════════════════════════════════════╝

class ResourceManager:
    """Manages hardware resource reservations for the APEX model fleet.

    Provides a thread-safe reservation system that tracks which models
    are "loaded" (reserved) and how much RAM headroom remains.  The
    manager does **not** physically load/unload models — callers do
    that themselves after checking :meth:`can_load` / :meth:`request_model`.

    Attributes
    ----------
    TOTAL_RAM_GB : float
        Total physical RAM on the system (default 22.0).
    RESERVED_RAM_GB : float
        RAM reserved for the OS, Python interpreter, and DB cache.
    AVAILABLE_RAM_GB : float
        RAM budget available for models (``TOTAL - RESERVED``).
    MODEL_MEMORY : dict
        Known model → memory footprint (GB) mapping.
    """

    TOTAL_RAM_GB: float = _TOTAL_RAM_GB
    RESERVED_RAM_GB: float = _RESERVED_RAM_GB
    AVAILABLE_RAM_GB: float = _AVAILABLE_RAM_GB
    MODEL_MEMORY: Dict[str, float] = MODEL_MEMORY

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # model_name → {"loaded_at": epoch, "last_used": epoch, "memory_gb": float}
        self._loaded_models: Dict[str, Dict[str, Any]] = {}
        self._total_reserved_gb: float = 0.0
        self._created_at: float = time.time()
        self._event_log: List[Dict[str, Any]] = []
        _log.info(
            "ResourceManager initialised — %.1f GB available for models "
            "(%.1f GB total, %.1f GB reserved for OS)",
            _MAX_USABLE_GB, _TOTAL_RAM_GB, _RESERVED_RAM_GB,
        )

    # ── Query methods ────────────────────────────────────────────

    def can_load(self, model_name: str) -> bool:
        """Check if there is enough RAM to load *model_name*.

        Parameters
        ----------
        model_name : str
            Name of the model (must be in :data:`MODEL_MEMORY` or a
            custom size is estimated at 1.0 GB).

        Returns
        -------
        bool
            ``True`` if the model can fit, or is already loaded.
        """
        try:
            with self._lock:
                if model_name in self._loaded_models:
                    return True  # already loaded
                needed = MODEL_MEMORY.get(model_name, 1.0)
                return (self._total_reserved_gb + needed) <= _MAX_USABLE_GB
        except Exception as exc:
            _log.error("can_load(%s) error: %s", model_name, exc)
            return False

    def request_model(self, model_name: str) -> bool:
        """Request a model reservation.

        If the model is already reserved, refreshes ``last_used`` and
        returns ``True``.  If there is not enough headroom, attempts
        :meth:`auto_evict` before giving up.

        Parameters
        ----------
        model_name : str
            Model to reserve.

        Returns
        -------
        bool
            ``True`` if the reservation succeeded, ``False`` if OOM.
        """
        try:
            with self._lock:
                # Already loaded — just touch timestamp
                if model_name in self._loaded_models:
                    self._loaded_models[model_name]["last_used"] = time.time()
                    _log.debug("Model '%s' already loaded — refreshed", model_name)
                    return True

                needed = MODEL_MEMORY.get(model_name, 1.0)

                # Enough room?
                if (self._total_reserved_gb + needed) <= _MAX_USABLE_GB:
                    return self._reserve(model_name, needed)

            # Not enough room — try eviction (outside inner lock to avoid deadlock)
            evicted = self.auto_evict(needed)
            if not evicted:
                _log.warning(
                    "Cannot load '%s' (%.1f GB) — %.1f / %.1f GB used, eviction failed",
                    model_name, needed, self._total_reserved_gb, _MAX_USABLE_GB,
                )
                self._log_event("request_denied", model_name, needed)
                return False

            with self._lock:
                if (self._total_reserved_gb + needed) <= _MAX_USABLE_GB:
                    return self._reserve(model_name, needed)

            _log.warning(
                "Cannot load '%s' even after eviction — budget exhausted",
                model_name,
            )
            return False
        except Exception as exc:
            _log.error("request_model(%s) error: %s", model_name, exc)
            return False

    def release_model(self, model_name: str) -> None:
        """Release a model's memory reservation.

        Parameters
        ----------
        model_name : str
            Model to release. No-op if not currently reserved.
        """
        try:
            with self._lock:
                entry = self._loaded_models.pop(model_name, None)
                if entry:
                    self._total_reserved_gb -= entry["memory_gb"]
                    self._total_reserved_gb = max(0.0, self._total_reserved_gb)
                    _log.info(
                        "Released '%s' (%.1f GB) — %.1f GB now reserved",
                        model_name, entry["memory_gb"], self._total_reserved_gb,
                    )
                    self._log_event("released", model_name, entry["memory_gb"])
                else:
                    _log.debug("release_model('%s') — not loaded, no-op", model_name)
        except Exception as exc:
            _log.error("release_model(%s) error: %s", model_name, exc)

    def get_usage(self) -> Dict[str, Any]:
        """Current memory usage report.

        Returns
        -------
        dict
            Comprehensive memory usage breakdown including per-model
            reservations, headroom, and recommendations.
        """
        try:
            with self._lock:
                loaded_detail: Dict[str, Dict[str, Any]] = {}
                for name, entry in self._loaded_models.items():
                    loaded_detail[name] = {
                        "memory_gb": entry["memory_gb"],
                        "loaded_at": entry["loaded_at"],
                        "last_used": entry["last_used"],
                        "age_seconds": round(time.time() - entry["loaded_at"], 1),
                        "idle_seconds": round(time.time() - entry["last_used"], 1),
                    }

                headroom = _MAX_USABLE_GB - self._total_reserved_gb
                can_fit: List[str] = []
                for name, mem in MODEL_MEMORY.items():
                    if name not in self._loaded_models and mem <= headroom:
                        can_fit.append(name)

                return {
                    "total_ram_gb": _TOTAL_RAM_GB,
                    "reserved_for_os_gb": _RESERVED_RAM_GB,
                    "available_for_models_gb": round(_AVAILABLE_RAM_GB, 2),
                    "max_usable_gb": round(_MAX_USABLE_GB, 2),
                    "currently_reserved_gb": round(self._total_reserved_gb, 2),
                    "headroom_gb": round(headroom, 2),
                    "utilization_pct": round(
                        (self._total_reserved_gb / _MAX_USABLE_GB) * 100
                        if _MAX_USABLE_GB > 0 else 0.0,
                        1,
                    ),
                    "loaded_models": loaded_detail,
                    "loaded_count": len(self._loaded_models),
                    "can_still_fit": can_fit,
                    "uptime_seconds": round(time.time() - self._created_at, 1),
                    "event_log_size": len(self._event_log),
                }
        except Exception as exc:
            _log.error("get_usage() error: %s", exc)
            return {"error": str(exc)}

    def auto_evict(self, needed_gb: float) -> bool:
        """Evict least-recently-used models to free *needed_gb* of RAM.

        The eviction policy is **LRU** — models with the oldest
        ``last_used`` timestamp are evicted first.  ``manbearpig`` is
        protected and will only be evicted as a last resort (it is the
        core inference engine).

        Parameters
        ----------
        needed_gb : float
            Amount of RAM (GB) that must be freed.

        Returns
        -------
        bool
            ``True`` if enough RAM was freed, ``False`` otherwise.
        """
        try:
            with self._lock:
                headroom = _MAX_USABLE_GB - self._total_reserved_gb
                if headroom >= needed_gb:
                    return True  # already enough room

                deficit = needed_gb - headroom

                # Build eviction candidates sorted by last_used (oldest first)
                # Protect manbearpig by putting it last
                candidates: List[Tuple[str, Dict[str, Any]]] = sorted(
                    (
                        (n, e) for n, e in self._loaded_models.items()
                        if n != "manbearpig"
                    ),
                    key=lambda x: x[1]["last_used"],
                )
                # Append manbearpig last (only evict as absolute last resort)
                mb_entry = self._loaded_models.get("manbearpig")
                if mb_entry:
                    candidates.append(("manbearpig", mb_entry))

                freed = 0.0
                evicted_names: List[str] = []

                for name, entry in candidates:
                    if freed >= deficit:
                        break
                    freed += entry["memory_gb"]
                    evicted_names.append(name)

                if freed < deficit:
                    _log.warning(
                        "auto_evict: need %.1f GB, can only free %.1f GB",
                        deficit, freed,
                    )
                    return False

                # Perform eviction
                for name in evicted_names:
                    entry = self._loaded_models.pop(name, None)
                    if entry:
                        self._total_reserved_gb -= entry["memory_gb"]
                        self._total_reserved_gb = max(0.0, self._total_reserved_gb)
                        _log.info(
                            "Evicted '%s' (%.1f GB, idle %.0fs)",
                            name,
                            entry["memory_gb"],
                            time.time() - entry["last_used"],
                        )
                        self._log_event("evicted", name, entry["memory_gb"])

                return True
        except Exception as exc:
            _log.error("auto_evict(%.1f) error: %s", needed_gb, exc)
            return False

    # ── Bulk operations ──────────────────────────────────────────

    def release_all(self) -> int:
        """Release all model reservations.

        Returns
        -------
        int
            Number of models released.
        """
        try:
            with self._lock:
                count = len(self._loaded_models)
                for name in list(self._loaded_models):
                    self._log_event(
                        "released_all",
                        name,
                        self._loaded_models[name]["memory_gb"],
                    )
                self._loaded_models.clear()
                self._total_reserved_gb = 0.0
                _log.info("Released all models (%d)", count)
                return count
        except Exception as exc:
            _log.error("release_all() error: %s", exc)
            return 0

    def get_event_log(self, last_n: int = 50) -> List[Dict[str, Any]]:
        """Return the last *last_n* resource events.

        Returns
        -------
        list of dict
            Each: ``{'timestamp', 'event', 'model', 'memory_gb'}``
        """
        try:
            with self._lock:
                return list(self._event_log[-last_n:])
        except Exception:
            return []

    def get_recommendation(self) -> Dict[str, Any]:
        """Recommend which models to load given current headroom.

        Returns a priority-ordered list of models that can fit,
        with their estimated impact on headroom.

        Returns
        -------
        dict
            ``{'recommendations': [...], 'headroom_gb': float}``
        """
        try:
            with self._lock:
                headroom = _MAX_USABLE_GB - self._total_reserved_gb
                # Priority order: manbearpig > minilm > legal-bert > qwen-fast > saul-legal
                priority = [
                    "manbearpig", "minilm", "legal-bert", "bert-ner",
                    "nomic-embed", "qwen-fast", "phi-mini", "saul-legal",
                ]
                recs: List[Dict[str, Any]] = []
                remaining = headroom
                for name in priority:
                    if name in self._loaded_models:
                        continue
                    mem = MODEL_MEMORY.get(name, 1.0)
                    if mem <= remaining:
                        recs.append({
                            "model": name,
                            "memory_gb": mem,
                            "headroom_after": round(remaining - mem, 2),
                            "status": "can_fit",
                        })
                        remaining -= mem
                    else:
                        recs.append({
                            "model": name,
                            "memory_gb": mem,
                            "headroom_after": round(remaining - mem, 2),
                            "status": "too_large",
                        })
                return {
                    "recommendations": recs,
                    "current_headroom_gb": round(headroom, 2),
                }
        except Exception as exc:
            _log.error("get_recommendation() error: %s", exc)
            return {"recommendations": [], "error": str(exc)}

    # ── Internal helpers ─────────────────────────────────────────

    def _reserve(self, model_name: str, memory_gb: float) -> bool:
        """Record a model reservation. Caller must hold ``_lock``."""
        now = time.time()
        self._loaded_models[model_name] = {
            "loaded_at": now,
            "last_used": now,
            "memory_gb": memory_gb,
        }
        self._total_reserved_gb += memory_gb
        _log.info(
            "Reserved '%s' (%.1f GB) — %.1f / %.1f GB used",
            model_name, memory_gb, self._total_reserved_gb, _MAX_USABLE_GB,
        )
        self._log_event("loaded", model_name, memory_gb)
        return True

    def _log_event(self, event: str, model: str, memory_gb: float) -> None:
        """Append to the in-memory event log.  Caller should hold ``_lock``."""
        self._event_log.append({
            "timestamp": time.time(),
            "event": event,
            "model": model,
            "memory_gb": memory_gb,
        })
        # Cap log size
        if len(self._event_log) > 500:
            self._event_log = self._event_log[-250:]

    # ── Magic methods ────────────────────────────────────────────

    def __repr__(self) -> str:
        return (
            f"<ResourceManager "
            f"loaded={len(self._loaded_models)} "
            f"reserved={self._total_reserved_gb:.1f}GB "
            f"headroom={(_MAX_USABLE_GB - self._total_reserved_gb):.1f}GB>"
        )


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                         SINGLETON ACCESS                            ║
# ╚══════════════════════════════════════════════════════════════════════╝

_singleton_lock = threading.Lock()
_singleton: Optional[ResourceManager] = None


def get_manager() -> ResourceManager:
    """Return the process-wide singleton :class:`ResourceManager`.

    Thread-safe. The first call creates the instance; subsequent calls
    return the same object.
    """
    global _singleton
    if _singleton is not None:
        return _singleton
    with _singleton_lock:
        if _singleton is None:
            _singleton = ResourceManager()
        return _singleton


# ──────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.stdout = open(
        sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace"
    )
    import json as _json  # safe — running from __file__ dir

    rm = get_manager()

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "load" and len(sys.argv) > 2:
            model = sys.argv[2]
            ok = rm.request_model(model)
            print(f"{'OK' if ok else 'DENIED'}: {model}")
        elif cmd == "release" and len(sys.argv) > 2:
            model = sys.argv[2]
            rm.release_model(model)
            print(f"Released: {model}")
        elif cmd == "recommend":
            print(_json.dumps(rm.get_recommendation(), indent=2, default=str))
        elif cmd == "events":
            print(_json.dumps(rm.get_event_log(), indent=2, default=str))
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: resource_manager.py [load MODEL | release MODEL | recommend | events]")
    else:
        print(_json.dumps(rm.get_usage(), indent=2, default=str))
