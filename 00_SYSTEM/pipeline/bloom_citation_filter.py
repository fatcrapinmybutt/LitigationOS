#!/usr/bin/env python3
"""
Bloom filter for O(1) probabilistic citation verification.

Replaces 60-80 individual DB queries during filing assembly with a single
in-memory membership test. Uses mmh3 (MurmurHash3) with multiple seeds.

Loaded from master_citations (3.7M rows) and auth_rules (1.2K rows).
Target: 0.01% false positive rate, ~9.6 MB memory.

Usage:
    # As module
    from bloom_citation_filter import BloomCitationFilter
    bf = BloomCitationFilter()
    assert bf.contains("MCL 600.605")
    results = bf.verify_batch(["MCR 2.105", "FAKE 999"])

    # CLI
    python bloom_citation_filter.py
"""
from __future__ import annotations

import math
import sqlite3
import sys
import threading
import time
from pathlib import Path
from typing import Optional

sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", errors="replace")

import mmh3

DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")


class BloomFilter:
    """Space-efficient probabilistic set with tuneable false-positive rate."""

    __slots__ = ("_bits", "_m", "_k", "_count", "_lock")

    def __init__(self, expected_items: int, fp_rate: float = 0.0001):
        # m = -n * ln(p) / (ln2)^2
        self._m = self._optimal_m(expected_items, fp_rate)
        self._k = self._optimal_k(self._m, expected_items)
        self._bits = bytearray(math.ceil(self._m / 8))
        self._count = 0
        self._lock = threading.Lock()

    @staticmethod
    def _optimal_m(n: int, p: float) -> int:
        return int(-n * math.log(p) / (math.log(2) ** 2)) + 1

    @staticmethod
    def _optimal_k(m: int, n: int) -> int:
        return max(1, int((m / n) * math.log(2) + 0.5))

    def _hashes(self, key: str) -> list[int]:
        """Generate k independent hash positions using double-hashing scheme.

        Uses two 64-bit halves of mmh3.hash128 as base hashes, then derives
        k positions via h1 + i*h2 (Kirsch-Mitzenmacker optimisation).
        """
        h128 = mmh3.hash128(key, seed=0, signed=False)
        h1 = h128 & 0xFFFFFFFFFFFFFFFF
        h2 = (h128 >> 64) & 0xFFFFFFFFFFFFFFFF
        return [(h1 + i * h2) % self._m for i in range(self._k)]

    def add(self, key: str) -> None:
        with self._lock:
            for pos in self._hashes(key):
                self._bits[pos >> 3] |= 1 << (pos & 7)
            self._count += 1

    def add_bulk_unlocked(self, keys: list[str]) -> int:
        """Bulk insert without per-item locking (caller holds lock or is single-threaded)."""
        bits = self._bits
        count = 0
        for key in keys:
            for pos in self._hashes(key):
                bits[pos >> 3] |= 1 << (pos & 7)
            count += 1
        self._count += count
        return count

    def __contains__(self, key: str) -> bool:
        bits = self._bits
        for pos in self._hashes(key):
            if not (bits[pos >> 3] & (1 << (pos & 7))):
                return False
        return True

    @property
    def item_count(self) -> int:
        return self._count

    @property
    def size_bytes(self) -> int:
        return len(self._bits)

    @property
    def num_hashes(self) -> int:
        return self._k

    @property
    def num_bits(self) -> int:
        return self._m

    def estimated_fp_rate(self) -> float:
        if self._count == 0:
            return 0.0
        return (1 - math.exp(-self._k * self._count / self._m)) ** self._k

    def fill_ratio(self) -> float:
        set_bits = sum(bin(b).count("1") for b in self._bits)
        return set_bits / self._m if self._m else 0.0


class BloomCitationFilter:
    """Thread-safe, lazy-loaded Bloom filter for citation verification."""

    def __init__(self, db_path: Optional[str | Path] = None):
        self._db_path = Path(db_path) if db_path else DEFAULT_DB
        self._bloom: Optional[BloomFilter] = None
        self._init_lock = threading.Lock()
        self._load_time: float = 0.0

    def _ensure_loaded(self) -> BloomFilter:
        if self._bloom is not None:
            return self._bloom
        with self._init_lock:
            if self._bloom is not None:
                return self._bloom
            self._bloom = self._build_filter()
            return self._bloom

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=120)
        conn.execute("PRAGMA busy_timeout=120000")
        conn.execute("PRAGMA mmap_size=12884901888")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        return conn

    def _build_filter(self) -> BloomFilter:
        t0 = time.perf_counter()
        conn = self._get_connection()
        try:
            # Count items to size the filter
            (n_citations,) = conn.execute(
                "SELECT COUNT(*) FROM master_citations"
            ).fetchone()
            (n_rules,) = conn.execute("SELECT COUNT(*) FROM auth_rules").fetchone()
            expected = n_citations + n_rules * 2 + 1000  # padding

            bf = BloomFilter(expected_items=max(expected, 100_000), fp_rate=0.0001)

            # Stream master_citations in batches
            batch_size = 50_000
            cursor = conn.execute(
                "SELECT citation FROM master_citations WHERE citation IS NOT NULL"
            )
            loaded = 0
            while True:
                rows = cursor.fetchmany(batch_size)
                if not rows:
                    break
                bf.add_bulk_unlocked([r[0] for r in rows])
                loaded += len(rows)

            # Load auth_rules (rule_number and title)
            rows = conn.execute(
                "SELECT rule_number, title FROM auth_rules "
                "WHERE rule_number IS NOT NULL"
            ).fetchall()
            for rule_number, title in rows:
                bf.add_bulk_unlocked([rule_number])
                if title:
                    bf.add_bulk_unlocked([title])
        finally:
            conn.close()

        self._load_time = time.perf_counter() - t0
        return bf

    # --- Public API ---

    def contains(self, citation_text: str) -> bool:
        """O(1) probabilistic membership test."""
        return citation_text in self._ensure_loaded()

    def verify_batch(self, citations: list[str]) -> dict[str, bool]:
        """Batch verify multiple citations. Returns {citation: bool}."""
        bloom = self._ensure_loaded()
        return {c: c in bloom for c in citations}

    def verify_with_fallback(self, citation: str) -> bool:
        """Check Bloom first; on positive, confirm against DB to eliminate FPs."""
        bloom = self._ensure_loaded()
        if citation not in bloom:
            return False  # definite negative
        # Bloom says yes — confirm with DB to rule out false positive
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT 1 FROM master_citations WHERE citation = ? LIMIT 1",
                (citation,),
            ).fetchone()
            if row:
                return True
            row = conn.execute(
                "SELECT 1 FROM auth_rules WHERE rule_number = ? OR title = ? LIMIT 1",
                (citation, citation),
            ).fetchone()
            return row is not None
        finally:
            conn.close()

    def stats(self) -> dict:
        """Return filter statistics."""
        bloom = self._ensure_loaded()
        return {
            "item_count": bloom.item_count,
            "num_bits": bloom.num_bits,
            "num_hashes": bloom.num_hashes,
            "size_bytes": bloom.size_bytes,
            "size_mb": round(bloom.size_bytes / (1024 * 1024), 2),
            "estimated_fp_rate": bloom.estimated_fp_rate(),
            "fill_ratio": round(bloom.fill_ratio(), 4),
            "load_time_sec": round(self._load_time, 3),
        }

    def reload(self) -> None:
        """Force a reload from DB (e.g., after new citations are ingested)."""
        with self._init_lock:
            self._bloom = None
        self._ensure_loaded()


# Singleton for import convenience
_default_filter: Optional[BloomCitationFilter] = None
_singleton_lock = threading.Lock()


def get_filter(db_path: Optional[str | Path] = None) -> BloomCitationFilter:
    """Return a module-level singleton filter (lazy-loaded, thread-safe)."""
    global _default_filter
    if _default_filter is not None:
        return _default_filter
    with _singleton_lock:
        if _default_filter is None:
            _default_filter = BloomCitationFilter(db_path=db_path)
        return _default_filter


if __name__ == "__main__":
    print("=" * 60)
    print("BloomCitationFilter — building from litigation_context.db")
    print("=" * 60)

    bf = BloomCitationFilter()
    s = bf.stats()

    print(f"\n  Items loaded : {s['item_count']:>12,}")
    print(f"  Bloom bits   : {s['num_bits']:>12,}")
    print(f"  Hash funcs   : {s['num_hashes']:>12}")
    print(f"  Memory       : {s['size_mb']:>12} MB")
    print(f"  Est. FP rate : {s['estimated_fp_rate']:>15.8f}")
    print(f"  Fill ratio   : {s['fill_ratio']:>12}")
    print(f"  Load time    : {s['load_time_sec']:>12} s")

    # Spot-check known citations
    test_citations = ["MCL 600.605", "MCR 2.105", "MCR 3.207", "FAKE_999.ZZZ"]
    print(f"\n  Spot-check:")
    for c in test_citations:
        result = bf.contains(c)
        print(f"    {c:30s} → {'FOUND' if result else 'NOT FOUND'}")

    # Batch verify
    batch = bf.verify_batch(test_citations)
    print(f"\n  Batch verify: {batch}")

    # Fallback verify
    print(f"\n  Fallback verify (MCL 600.605): {bf.verify_with_fallback('MCL 600.605')}")
    print(f"  Fallback verify (FAKE_999):    {bf.verify_with_fallback('FAKE_999.ZZZ')}")

    print("\n" + "=" * 60)
    print("Done.")
