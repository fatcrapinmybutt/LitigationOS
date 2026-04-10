"""
HYDRA ↔ Daemon Bridge — Resilience utilities for the daemon main loop.

Provides `check_and_heal()` which the daemon core.py can call periodically
to detect stale shards, trigger Phoenix respawns, and prune old HYDRA data.

All imports are lazy so this module adds zero startup cost.
"""

import json
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger("daemon.hydra_bridge")

HYDRA_DIR = Path(__file__).resolve().parent.parent.parent / "temp" / "hydra"


def check_and_heal(max_stale_minutes: float = 10.0,
                   prune_older_than_hours: int = 72) -> dict:
    """
    Run a single HYDRA health-and-heal cycle.

    1. Scan HYDRA_DIR for active shard journals and detect stale ones.
    2. For each stale shard, salvage partial results via PhoenixProtocol.
    3. Prune old result/journal files beyond *prune_older_than_hours*.
    4. Return a summary dict with counts and any errors.

    Safe to call every 60–120 seconds from the daemon main loop.
    Returns immediately if HYDRA_DIR doesn't exist (protocol unused).
    """
    result = {
        "status": "ok",
        "hydra_dir_exists": HYDRA_DIR.exists(),
        "active_journals": 0,
        "stale_detected": 0,
        "salvaged": 0,
        "pruned": 0,
        "errors": [],
    }

    if not HYDRA_DIR.exists():
        return result

    now = time.time()
    stale_threshold_sec = max_stale_minutes * 60
    prune_threshold_sec = prune_older_than_hours * 3600

    # ── 1. Detect stale journals ──────────────────────────────────────
    journals = list(HYDRA_DIR.glob("*.journal.jsonl"))
    result["active_journals"] = len(journals)

    stale_shard_ids = []
    for jf in journals:
        try:
            age_sec = now - jf.stat().st_mtime
            if age_sec > stale_threshold_sec:
                shard_id = jf.stem.replace(".journal", "")
                stale_shard_ids.append(shard_id)
        except OSError:
            continue

    result["stale_detected"] = len(stale_shard_ids)

    # ── 2. Salvage partial results from stale shards ──────────────────
    if stale_shard_ids:
        try:
            from .hydra_protocol import PhoenixProtocol
        except Exception as exc:
            logger.error("Failed to import PhoenixProtocol: %s", exc, exc_info=True)
            result["errors"].append(f"import PhoenixProtocol: {exc}")
            result["status"] = "degraded"
            return result

        for shard_id in stale_shard_ids:
            try:
                partial, items = PhoenixProtocol.salvage_results(shard_id)
                if partial and items > 0:
                    result["salvaged"] += 1
                    logger.info(
                        "HYDRA bridge salvaged %d items from stale shard %s",
                        items, shard_id,
                    )
            except Exception as exc:
                logger.error(
                    "HYDRA bridge salvage failed for %s: %s",
                    shard_id, exc, exc_info=True,
                )
                result["errors"].append(f"salvage {shard_id}: {exc}")

    # ── 3. Prune old files ────────────────────────────────────────────
    for path in HYDRA_DIR.iterdir():
        if not path.is_file():
            continue
        try:
            age_sec = now - path.stat().st_mtime
            if age_sec > prune_threshold_sec:
                path.unlink()
                result["pruned"] += 1
        except OSError as exc:
            logger.error("HYDRA prune failed for %s: %s", path, exc, exc_info=True)
            result["errors"].append(f"prune {path.name}: {exc}")

    if result["errors"]:
        result["status"] = "degraded"

    return result


def hydra_health_snapshot() -> dict:
    """
    Build a resilience health snapshot for reporting.

    Returns genetic memory stats, active shard counts, and HYDRA dir metrics.
    """
    snapshot = {
        "protocol": "HYDRA v1.0",
        "hydra_dir": str(HYDRA_DIR),
        "hydra_dir_exists": HYDRA_DIR.exists(),
        "genetic_memory": {},
        "active_shards": 0,
        "result_files": 0,
        "journal_files": 0,
        "phoenix_logs": 0,
        "total_files": 0,
        "disk_usage_kb": 0,
    }

    if not HYDRA_DIR.exists():
        return snapshot

    # File counts
    try:
        all_files = list(HYDRA_DIR.iterdir())
        snapshot["total_files"] = len([f for f in all_files if f.is_file()])
        snapshot["result_files"] = len(list(HYDRA_DIR.glob("*-hydra-*.json")))
        snapshot["journal_files"] = len(list(HYDRA_DIR.glob("*.journal.jsonl")))
        snapshot["phoenix_logs"] = len(list(HYDRA_DIR.glob("phoenix_*.json")))
        snapshot["disk_usage_kb"] = round(
            sum(f.stat().st_size for f in all_files if f.is_file()) / 1024, 1
        )
    except OSError as exc:
        logger.error("HYDRA health file scan failed: %s", exc, exc_info=True)

    # Genetic memory
    try:
        from .hydra_protocol import GeneticMemory
        mem = GeneticMemory.load()
        snapshot["genetic_memory"] = {
            "agents_spawned": mem.get("total_agents_spawned", 0),
            "agents_died": mem.get("total_agents_died", 0),
            "phoenix_respawns": mem.get("total_phoenix_respawns", 0),
            "items_processed": mem.get("total_items_processed", 0),
            "dna_profiles": len(mem.get("dna_performance", {})),
        }
        spawned = mem.get("total_agents_spawned", 0)
        died = mem.get("total_agents_died", 0)
        if spawned > 0:
            snapshot["genetic_memory"]["survival_rate_pct"] = round(
                (spawned - died) / spawned * 100, 1
            )
    except Exception as exc:
        logger.error("HYDRA genetic memory read failed: %s", exc, exc_info=True)
        snapshot["genetic_memory"] = {"error": str(exc)}

    return snapshot
