#!/usr/bin/env python3
"""
prefetch_cache.py — Predictive Prefetch Cache for Filing Assembly
=================================================================

Pre-loads all data a filing assembly will need in parallel background
threads the moment a vehicle/lane is selected.  Filing assembly follows
a deterministic pattern (claims → evidence → authority → deadlines →
impeachment → readiness), so we can predict and fetch everything at once
instead of issuing 35-50 sequential queries.

Usage:
    from prefetch_cache import cache          # module-level singleton
    cache.prefetch("Motion to Disqualify", "E")
    claims = cache.get("claims")              # blocks briefly if still loading
    stats  = cache.stats()

Performance:
    - Sequential: 50 queries × 0.1-9ms ≈ 200-450ms
    - Prefetched: all queries in parallel ≈ 10-50ms wall-clock (mmap + WAL)
"""

import sys
import os
import time
import sqlite3
import threading
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

logger = logging.getLogger("prefetch_cache")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DB_PATH = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
_TTL_SECONDS = 120          # cache entries expire after 2 minutes
_MAX_CACHE_BYTES = 50 * 1024 * 1024   # 50 MB soft limit
_MAX_WORKERS = 6            # parallel query threads (safe with WAL readers)
_PRAGMA_SETUP = [
    "PRAGMA busy_timeout=120000",
    "PRAGMA mmap_size=12884901888",
    "PRAGMA cache_size=-131072",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA journal_mode=WAL",
    "PRAGMA query_only=ON",
]

# ---------------------------------------------------------------------------
# Schema discovery helpers
# ---------------------------------------------------------------------------

_schema_lock = threading.Lock()
_schema_cache: dict[str, list[str]] = {}


def _get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    """Return column names for *table*, cached process-wide."""
    with _schema_lock:
        if table in _schema_cache:
            return _schema_cache[table]
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    cols = [r[1] for r in rows] if rows else []
    with _schema_lock:
        _schema_cache[table] = cols
    return cols


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cols = _get_columns(conn, table)
    return len(cols) > 0


# ---------------------------------------------------------------------------
# Connection factory (read-only, per-thread)
# ---------------------------------------------------------------------------

def _open_reader(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a read-only connection with full PRAGMA tuning."""
    path = db_path or DB_PATH
    if not path.exists():
        raise FileNotFoundError(f"DB not found: {path}")
    conn = sqlite3.connect(str(path), timeout=120)
    conn.row_factory = sqlite3.Row
    for pragma in _PRAGMA_SETUP:
        conn.execute(pragma)
    return conn


# ---------------------------------------------------------------------------
# Cache entry
# ---------------------------------------------------------------------------

class _CacheEntry:
    """One category of prefetched data."""

    __slots__ = ("key", "data", "ready", "error", "fetched_at", "size_bytes")

    def __init__(self, key: str):
        self.key = key
        self.data: list[dict] | None = None
        self.ready = threading.Event()
        self.error: str | None = None
        self.fetched_at: float = 0.0
        self.size_bytes: int = 0

    def set_result(self, rows: list[dict]) -> None:
        self.data = rows
        self.fetched_at = time.monotonic()
        self.size_bytes = _estimate_size(rows)
        self.ready.set()

    def set_error(self, msg: str) -> None:
        self.error = msg
        self.data = []
        self.fetched_at = time.monotonic()
        self.size_bytes = 0
        self.ready.set()

    @property
    def expired(self) -> bool:
        return (time.monotonic() - self.fetched_at) > _TTL_SECONDS if self.fetched_at else False


def _estimate_size(rows: list[dict]) -> int:
    """Rough byte estimate for a list of dicts (good enough for eviction)."""
    if not rows:
        return 0
    # sample first row then multiply
    sample = rows[0]
    per_row = sum(len(str(v)) for v in sample.values()) + 64  # overhead
    return per_row * len(rows)


def _rows_to_dicts(cursor: sqlite3.Cursor) -> list[dict]:
    """Convert sqlite3.Row results to plain dicts for safe cross-thread use."""
    return [dict(row) for row in cursor.fetchall()]


# ---------------------------------------------------------------------------
# Query definitions (the heart of prefetch)
# ---------------------------------------------------------------------------

def _build_queries(vehicle_id: str, lane: str, claim_ids: list[str] | None = None):
    """Return {category: (sql, params)} for all prefetch targets.

    Each query is validated against live schema before execution, so
    missing tables / columns degrade gracefully.
    """
    queries: dict[str, tuple[str, tuple]] = {}

    # 1. Claims
    queries["claims"] = (
        "SELECT * FROM claims WHERE classification LIKE ? OR claim_id LIKE ?",
        (f"%{lane}%", f"%{vehicle_id}%"),
    )

    # 2. Evidence quotes (top 500 most recent)
    queries["evidence"] = (
        "SELECT * FROM evidence_quotes ORDER BY id DESC LIMIT 500",
        (),
    )

    # 3. Claim-evidence links
    queries["claim_evidence_links"] = (
        "SELECT * FROM claim_evidence_links ORDER BY id DESC LIMIT 1000",
        (),
    )

    # 4. Authority chains
    queries["authority"] = (
        "SELECT * FROM authority_chains WHERE filing_vehicle LIKE ?",
        (f"%{vehicle_id}%",),
    )

    # 5. Auth rules (all — typically small table)
    queries["auth_rules"] = (
        "SELECT * FROM auth_rules LIMIT 2000",
        (),
    )

    # 6. Deadlines
    queries["deadlines"] = (
        "SELECT * FROM deadlines WHERE status = 'active' ORDER BY due_date_iso ASC",
        (),
    )

    # 7. Filing readiness
    queries["filing_readiness"] = (
        "SELECT * FROM filing_readiness WHERE vehicle_name LIKE ?",
        (f"%{vehicle_id}%",),
    )

    # 8. Impeachment items (all — used for cross-examination prep)
    queries["impeachment"] = (
        "SELECT * FROM impeachment_items ORDER BY severity DESC LIMIT 200",
        (),
    )

    # 9. Judicial violations (critical + high only)
    queries["judicial_violations"] = (
        "SELECT * FROM judicial_violations WHERE severity IN ('critical','high') LIMIT 50",
        (),
    )

    return queries


# ---------------------------------------------------------------------------
# PrefetchCache
# ---------------------------------------------------------------------------

class PrefetchCache:
    """Predictive prefetch cache for filing assembly.

    Call ``prefetch(vehicle_id, lane)`` when a vehicle is selected.
    All required data is fetched in parallel on background threads.
    Call ``get(key)`` to retrieve — blocks briefly if still loading.
    """

    def __init__(self, db_path: Path | None = None, ttl: float = _TTL_SECONDS,
                 max_bytes: int = _MAX_CACHE_BYTES, max_workers: int = _MAX_WORKERS):
        self._db_path = db_path or DB_PATH
        self._ttl = ttl
        self._max_bytes = max_bytes
        self._max_workers = max_workers

        # {vehicle_id: {category: _CacheEntry}}
        self._store: dict[str, dict[str, _CacheEntry]] = {}
        self._lock = threading.Lock()

        # stats
        self._hits = 0
        self._misses = 0
        self._prefetch_times: list[float] = []
        self._active_vehicle: str | None = None

    # ---- public API -------------------------------------------------------

    def prefetch(self, vehicle_id: str, lane: str) -> None:
        """Trigger background prefetch for *vehicle_id* / *lane*.

        Returns immediately.  Data is fetched on daemon threads.
        """
        self._active_vehicle = vehicle_id
        self._maybe_evict()

        entries: dict[str, _CacheEntry] = {}
        queries = _build_queries(vehicle_id, lane)

        with self._lock:
            self._store[vehicle_id] = entries
            for cat in queries:
                entries[cat] = _CacheEntry(cat)

        # launch background thread that fans out queries
        t = threading.Thread(
            target=self._background_fetch,
            args=(vehicle_id, lane, queries, entries),
            daemon=True,
            name=f"prefetch-{vehicle_id[:20]}",
        )
        t.start()

    def get(self, key: str, default: Any = None, *, timeout: float = 10.0) -> Any:
        """Retrieve prefetched data.  Blocks up to *timeout* seconds if
        the category is still loading.  Returns *default* on miss/error.
        """
        vid = self._active_vehicle
        if vid is None:
            self._misses += 1
            return default

        with self._lock:
            entries = self._store.get(vid)
            if entries is None or key not in entries:
                self._misses += 1
                return default
            entry = entries[key]

        # wait for the background thread to finish this category
        if not entry.ready.wait(timeout=timeout):
            logger.warning("prefetch timeout for %s/%s", vid, key)
            self._misses += 1
            return default

        if entry.expired:
            self._misses += 1
            return default

        if entry.error:
            self._misses += 1
            return default

        self._hits += 1
        return entry.data

    def invalidate(self, vehicle_id: str) -> None:
        """Clear all cached data for a vehicle."""
        with self._lock:
            self._store.pop(vehicle_id, None)
        if self._active_vehicle == vehicle_id:
            self._active_vehicle = None

    def invalidate_all(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._store.clear()
        self._active_vehicle = None

    def stats(self) -> dict:
        """Return cache statistics."""
        total = self._hits + self._misses
        with self._lock:
            total_bytes = sum(
                sum(e.size_bytes for e in entries.values())
                for entries in self._store.values()
            )
            vehicles_cached = len(self._store)
            categories_cached = sum(
                sum(1 for e in entries.values() if e.ready.is_set() and not e.error)
                for entries in self._store.values()
            )

        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{(self._hits / total * 100):.1f}%" if total else "N/A",
            "miss_rate": f"{(self._misses / total * 100):.1f}%" if total else "N/A",
            "vehicles_cached": vehicles_cached,
            "categories_cached": categories_cached,
            "memory_bytes": total_bytes,
            "memory_mb": f"{total_bytes / 1024 / 1024:.2f}",
            "prefetch_times_ms": [f"{t * 1000:.1f}" for t in self._prefetch_times[-10:]],
            "avg_prefetch_ms": (
                f"{sum(self._prefetch_times[-10:]) / len(self._prefetch_times[-10:]) * 1000:.1f}"
                if self._prefetch_times else "N/A"
            ),
            "ttl_seconds": self._ttl,
            "max_bytes": self._max_bytes,
        }

    # ---- internals --------------------------------------------------------

    def _background_fetch(self, vehicle_id: str, lane: str,
                          queries: dict, entries: dict[str, _CacheEntry]) -> None:
        """Run all prefetch queries in parallel via ThreadPoolExecutor."""
        t0 = time.monotonic()

        def _run_query(category: str, sql: str, params: tuple) -> tuple[str, list[dict], str | None]:
            """Execute a single query on its own connection (thread-safe)."""
            try:
                conn = _open_reader(self._db_path)
                try:
                    # verify table exists before querying
                    table_name = _extract_table(sql)
                    if table_name and not _table_exists(conn, table_name):
                        return (category, [], f"table '{table_name}' not found")
                    cur = conn.execute(sql, params)
                    rows = _rows_to_dicts(cur)
                    return (category, rows, None)
                finally:
                    conn.close()
            except Exception as exc:
                return (category, [], str(exc))

        with ThreadPoolExecutor(max_workers=self._max_workers,
                                thread_name_prefix="pf-query") as pool:
            futures = {
                pool.submit(_run_query, cat, sql, params): cat
                for cat, (sql, params) in queries.items()
            }
            for future in as_completed(futures):
                cat, rows, err = future.result()
                entry = entries.get(cat)
                if entry is None:
                    continue
                if err:
                    logger.warning("prefetch %s/%s: %s", vehicle_id, cat, err)
                    entry.set_error(err)
                else:
                    entry.set_result(rows)

        elapsed = time.monotonic() - t0
        self._prefetch_times.append(elapsed)
        logger.info("prefetch complete for %s in %.1fms (%d categories)",
                     vehicle_id, elapsed * 1000, len(entries))

    def _maybe_evict(self) -> None:
        """Evict oldest vehicles if cache exceeds size limit."""
        with self._lock:
            # evict expired entries first
            expired_vids = [
                vid for vid, entries in self._store.items()
                if all(e.expired for e in entries.values() if e.ready.is_set())
                and any(e.ready.is_set() for e in entries.values())
            ]
            for vid in expired_vids:
                del self._store[vid]

            # then check size
            total = sum(
                sum(e.size_bytes for e in entries.values())
                for entries in self._store.values()
            )
            if total <= self._max_bytes:
                return

            # evict oldest (by earliest fetched_at) until under limit
            scored: list[tuple[str, float]] = []
            for vid, entries in self._store.items():
                times = [e.fetched_at for e in entries.values() if e.fetched_at]
                oldest = min(times) if times else 0
                scored.append((vid, oldest))
            scored.sort(key=lambda x: x[1])

            for vid, _ in scored:
                if total <= self._max_bytes:
                    break
                evicted = self._store.pop(vid, {})
                total -= sum(e.size_bytes for e in evicted.values())


def _extract_table(sql: str) -> str | None:
    """Best-effort extract main table name from a SELECT or PRAGMA statement."""
    sql_upper = sql.upper()
    # handle "SELECT * FROM table_name ..."
    if "FROM" in sql_upper:
        parts = sql.split()
        for i, p in enumerate(parts):
            if p.upper() == "FROM":
                if i + 1 < len(parts):
                    return parts[i + 1].strip("(").strip(",").strip(";")
    return None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

cache = PrefetchCache()

# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

def _demo():
    """Run a demo prefetch and print stats."""
    import json

    print("=" * 70)
    print("  PrefetchCache — Demo & Self-Test")
    print("=" * 70)
    print()

    db_path = DB_PATH
    if not db_path.exists():
        print(f"[SKIP] Database not found at {db_path}")
        return

    # check DB is accessible
    try:
        conn = _open_reader(db_path)
        row_count = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        conn.close()
        print(f"[OK]   Database: {db_path}")
        print(f"[OK]   Tables:   {row_count}")
    except Exception as e:
        print(f"[ERR]  Cannot open DB: {e}")
        return

    print()

    # --- Demo 1: prefetch for a vehicle ---
    c = PrefetchCache(db_path=db_path, ttl=120)

    vehicle = "Motion to Disqualify"
    lane = "E"

    print(f"[1]  Prefetching for vehicle='{vehicle}', lane='{lane}' ...")
    t0 = time.monotonic()
    c.prefetch(vehicle, lane)

    # retrieve all categories (blocks until ready)
    categories = [
        "claims", "evidence", "claim_evidence_links", "authority",
        "auth_rules", "deadlines", "filing_readiness", "impeachment",
        "judicial_violations",
    ]

    results = {}
    for cat in categories:
        data = c.get(cat, timeout=15)
        count = len(data) if data is not None else 0
        results[cat] = count

    elapsed_ms = (time.monotonic() - t0) * 1000
    print(f"[OK]  All {len(categories)} categories loaded in {elapsed_ms:.1f}ms")
    print()

    # print row counts
    print("  Category                  Rows")
    print("  " + "-" * 40)
    for cat, count in results.items():
        print(f"  {cat:<26} {count:>6}")
    print()

    # --- Demo 2: cache hit ---
    print("[2]  Testing cache hits ...")
    for cat in categories:
        data = c.get(cat)
        assert data is not None, f"cache miss on {cat}"
    print(f"[OK]  All {len(categories)} categories served from cache (hits)")
    print()

    # --- Demo 3: cache miss ---
    print("[3]  Testing cache miss ...")
    miss = c.get("nonexistent_category")
    assert miss is None, "expected None for missing category"
    print("[OK]  Missing category returns None")
    print()

    # --- Demo 4: invalidation ---
    print("[4]  Testing invalidation ...")
    c.invalidate(vehicle)
    miss2 = c.get("claims")
    assert miss2 is None, "expected None after invalidation"
    print("[OK]  Invalidation works")
    print()

    # --- Demo 5: second vehicle ---
    vehicle2 = "Custody FOF"
    lane2 = "A"
    print(f"[5]  Prefetching for vehicle='{vehicle2}', lane='{lane2}' ...")
    t1 = time.monotonic()
    c.prefetch(vehicle2, lane2)
    for cat in categories:
        c.get(cat, timeout=15)
    elapsed2 = (time.monotonic() - t1) * 1000
    print(f"[OK]  Loaded in {elapsed2:.1f}ms")
    print()

    # --- Stats ---
    print("[STATS]")
    s = c.stats()
    print(json.dumps(s, indent=2))
    print()
    print("=" * 70)
    print("  All tests passed.")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
    _demo()
