"""
DELTA9 — Phoenix Bootstrap: Intelligent Agent Respawn System
ADR-001 Phase 3 · MAX LEVEL 9999++

Auto-classifies agent failures and respawns transient errors only.
Coordinates with Agent9999 retry stack to avoid amplification.
Hard ceiling: never exceeds LITIGOS_MAX_AGENT_INSTANCES (default 56).

Kill switch: LITIGOS_DISABLE_PHOENIX=1
Canary: convergence tier only (gate other tiers behind env var)
"""
import os
import time
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("phoenix")


# Error classification categories
TRANSIENT_MARKERS = [
    "locked", "busy", "timeout", "EAGAIN", "pipe",
    "connection refused", "temporary", "try again",
]
PERSISTENT_MARKERS = [
    "schema", "missing table", "no such table", "no such column",
    "syntax error", "not found", "does not exist",
]
FATAL_MARKERS = [
    "permission denied", "disk full", "out of memory",
    "segfault", "killed", "OOM",
]


def classify_error(error_text: str) -> str:
    """Classify an agent error as transient, persistent, or fatal.

    - transient: safe to retry (DB locks, timeouts, EAGAIN)
    - persistent: root cause must be fixed (schema, missing tables)
    - fatal: cannot be retried (OOM, permissions, disk)
    """
    if not error_text:
        return "fatal"

    err_lower = str(error_text).lower()

    for marker in FATAL_MARKERS:
        if marker in err_lower:
            return "fatal"

    for marker in PERSISTENT_MARKERS:
        if marker in err_lower:
            return "persistent"

    for marker in TRANSIENT_MARKERS:
        if marker in err_lower:
            return "transient"

    return "fatal"  # unknown errors are not retried


class PhoenixBootstrap:
    """Intelligent agent respawn for transient failures.

    NOT an Agent9999 subclass — this is an orchestrator extension.
    Called by the orchestrator after a tier run to handle failures.

    Usage:
        phoenix = PhoenixBootstrap(max_respawn=2, agent_ceiling=56)
        recovery = phoenix.attempt_recovery(failed_results, tier_name, run_tier_fn)
    """

    def __init__(self, max_respawn: int = 2, agent_ceiling: int = None):
        self.max_respawn = max_respawn
        self.agent_ceiling = agent_ceiling or int(
            os.environ.get("LITIGOS_MAX_AGENT_INSTANCES", "56")
        )
        self._respawn_log: List[Dict] = []
        self._disabled = os.environ.get("LITIGOS_DISABLE_PHOENIX", "0") == "1"

    def is_enabled(self) -> bool:
        return not self._disabled

    def attempt_recovery(
        self,
        failed_results: list,
        tier_name: str,
        agent_factory_fn,
        current_agent_count: int = 0,
    ) -> Dict[str, Any]:
        """Attempt to recover failed agents via classification + respawn.

        Args:
            failed_results: List of AgentResult objects with status != SUCCESS
            tier_name: Tier name (e.g., "convergence")
            agent_factory_fn: Callable that takes agent_id and returns a fresh instance
            current_agent_count: Number of currently running agents

        Returns:
            {
                respawned: [agent_ids],
                recovered: [agent_ids],
                abandoned: [agent_ids],
                error_classes: {agent_id: "transient"|"persistent"|"fatal"},
                log: [{agent_id, error_class, attempt, outcome}]
            }
        """
        if self._disabled:
            return {
                "respawned": [], "recovered": [], "abandoned": [],
                "error_classes": {}, "log": [],
                "reason": "Phoenix disabled (LITIGOS_DISABLE_PHOENIX=1)"
            }

        # Canary: only convergence tier by default
        allowed_tiers = {"convergence"}
        if os.environ.get("LITIGOS_PHOENIX_ALL_TIERS", "0") == "1":
            allowed_tiers = None  # allow all
        if allowed_tiers and tier_name not in allowed_tiers:
            return {
                "respawned": [], "recovered": [], "abandoned": [],
                "error_classes": {}, "log": [],
                "reason": f"Phoenix canary: tier '{tier_name}' not in allowed set"
            }

        result = {
            "respawned": [], "recovered": [], "abandoned": [],
            "error_classes": {}, "log": [],
        }

        for agent_result in failed_results:
            agent_id = getattr(agent_result, 'agent_id', str(agent_result))
            error_text = str(getattr(agent_result, 'error', '') or '')
            error_class = classify_error(error_text)
            result["error_classes"][agent_id] = error_class

            log_entry = {
                "agent_id": agent_id,
                "error_class": error_class,
                "original_error": error_text[:200],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            # Only retry transient errors
            if error_class != "transient":
                log_entry["outcome"] = f"abandoned ({error_class})"
                result["abandoned"].append(agent_id)
                result["log"].append(log_entry)
                logger.info(f"[PHOENIX] {agent_id}: {error_class} error — NOT retrying")
                continue

            # Check agent ceiling
            if current_agent_count >= self.agent_ceiling:
                log_entry["outcome"] = "abandoned (ceiling reached)"
                result["abandoned"].append(agent_id)
                result["log"].append(log_entry)
                logger.warning(f"[PHOENIX] {agent_id}: ceiling reached "
                              f"({current_agent_count}/{self.agent_ceiling})")
                continue

            # Attempt respawn (up to max_respawn attempts)
            recovered = False
            for attempt in range(1, self.max_respawn + 1):
                logger.info(f"[PHOENIX] {agent_id}: respawn attempt "
                           f"{attempt}/{self.max_respawn}")

                # Exponential backoff before retry (coordinate with Agent9999)
                backoff = min(2 ** attempt, 16)
                time.sleep(backoff)

                try:
                    # Get fresh agent instance
                    agent = agent_factory_fn(agent_id)
                    if agent is None:
                        log_entry["outcome"] = f"abandoned (factory returned None)"
                        break

                    # Kill-before-respawn: ensure no lingering state
                    if hasattr(agent, '_reset_state'):
                        agent._reset_state()

                    # Run the agent
                    agent_result_new = agent.run()

                    status = getattr(agent_result_new, 'status', 'UNKNOWN')
                    if status == "SUCCESS":
                        result["recovered"].append(agent_id)
                        log_entry["outcome"] = f"recovered (attempt {attempt})"
                        recovered = True
                        current_agent_count += 1
                        logger.info(f"[PHOENIX] {agent_id}: RECOVERED on attempt {attempt}")
                        break
                    else:
                        # Re-classify the new error
                        new_error = str(getattr(agent_result_new, 'error', '') or '')
                        new_class = classify_error(new_error)
                        if new_class != "transient":
                            log_entry["outcome"] = f"abandoned (escalated to {new_class})"
                            break

                except Exception as e:
                    new_class = classify_error(str(e))
                    if new_class != "transient":
                        log_entry["outcome"] = f"abandoned (exception: {new_class})"
                        break
                    logger.warning(f"[PHOENIX] {agent_id}: attempt {attempt} "
                                  f"failed: {str(e)[:100]}")

            if not recovered:
                result["abandoned"].append(agent_id)
                if "outcome" not in log_entry:
                    log_entry["outcome"] = f"abandoned (max attempts {self.max_respawn})"

            if recovered:
                result["respawned"].append(agent_id)

            result["log"].append(log_entry)
            self._respawn_log.append(log_entry)

        return result

    def get_respawn_log(self) -> List[Dict]:
        """Return full respawn history."""
        return self._respawn_log

    def get_summary(self) -> Dict[str, int]:
        """Return summary counts."""
        recovered = sum(1 for e in self._respawn_log if "recovered" in e.get("outcome", ""))
        abandoned = sum(1 for e in self._respawn_log if "abandoned" in e.get("outcome", ""))
        return {
            "total_events": len(self._respawn_log),
            "recovered": recovered,
            "abandoned": abandoned,
            "recovery_rate": recovered / max(len(self._respawn_log), 1),
        }
