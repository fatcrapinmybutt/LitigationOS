"""
HYDRA — Hyper-resilient Universal Death-proof Runtime Architecture.

Agent immortality protocol with 7 interlocking systems:
  H1 Phoenix Protocol    — Death-triggered auto-respawn
  H2 Streaming Results   — Write-ahead log, never lose work
  H3 Cognitive Sharding  — Smart task decomposition
  H4 Prompt Evolution    — Failed prompts auto-improve
  H5 Predictive Timeout  — Kill before GOAWAY kills you
  H6 Redundant Dispatch  — Critical tasks get backup agents
  H7 Genetic Memory      — Learn from every agent death

Usage:
    from hydra import HydraOrchestrator, GeneticMemory, PhoenixProtocol
"""

# Lazy imports — nothing loaded at import time.
# Callers use the accessor functions below to avoid loading the heavy
# hydra_protocol module until it's actually needed.


def get_orchestrator():
    """Return a new HydraOrchestrator instance (lazy-loaded)."""
    from .hydra_protocol import HydraOrchestrator
    return HydraOrchestrator()


def get_phoenix():
    """Return the PhoenixProtocol class (lazy-loaded)."""
    from .hydra_protocol import PhoenixProtocol
    return PhoenixProtocol


def get_genetic_memory():
    """Return the GeneticMemory class (lazy-loaded)."""
    from .hydra_protocol import GeneticMemory
    return GeneticMemory


def get_shard_engine():
    """Return a new CognitiveShardEngine instance (lazy-loaded)."""
    from .hydra_protocol import CognitiveShardEngine
    return CognitiveShardEngine()


def get_prompt_evolver():
    """Return the PromptEvolver class (lazy-loaded)."""
    from .hydra_protocol import PromptEvolver
    return PromptEvolver


def get_predictive_timeout():
    """Return the PredictiveTimeout class (lazy-loaded)."""
    from .hydra_protocol import PredictiveTimeout
    return PredictiveTimeout
