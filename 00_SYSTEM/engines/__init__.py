"""
LitigationOS Engines Package v3.0.0
====================================
22 engine sub-packages for evidence processing, filing generation,
judicial analysis, filesystem intelligence, and litigation operations.

All engines: 100% local, zero-API, CPU-first.

Registered engines (class-based, instantiable via get_engine):
    nexus, chimera, chronos, cerberus, event_horizon, oracle,
    nemesis, lexicon, forge, intake, filing_engine, semantic,
    perception, search, analytics, typst

Module-based sub-packages (imported into namespace, not in get_engine):
    hydra_governor, filing_assembler, agents

Public API:
    from engines import NexusEngine, ChimeraEngine, ChronosEngine, CerberusEngine
    from engines import EventHorizonEngine, OracleEngine, NemesisEngine
    from engines import LexiconEngine, ForgeEngine, IntakePipeline, FilingEngine
    from engines import SemanticSearchEngine, LegalBERTEngine, HybridSearchEngine
    from engines import AnalyticsEngine, TypstFilingEngine
    from engines import get_engine
"""

# Safe imports — some engines touch stdout/stderr at module level,
# which fails in non-TTY contexts (exec_python, subprocess).
_ENGINE_MAP = {}

# ── Core 4 (original) ───────────────────────────────────────────────

try:
    from .nexus.nexus_engine import NexusEngine
    _ENGINE_MAP["nexus"] = NexusEngine
except Exception:
    NexusEngine = None

try:
    from .chimera.chimera_engine import ChimeraEngine
    _ENGINE_MAP["chimera"] = ChimeraEngine
except Exception:
    ChimeraEngine = None

try:
    from .chronos.chronos_engine import ChronosEngine
    _ENGINE_MAP["chronos"] = ChronosEngine
except Exception:
    ChronosEngine = None

try:
    from .cerberus.cerberus_engine import CerberusEngine
    _ENGINE_MAP["cerberus"] = CerberusEngine
except Exception:
    CerberusEngine = None

# ── Extended engines (class-based) ──────────────────────────────────

try:
    from .event_horizon import Engine as EventHorizonEngine
    _ENGINE_MAP["event_horizon"] = EventHorizonEngine
except Exception:
    EventHorizonEngine = None

try:
    from .oracle.oracle_engine import Oracle as OracleEngine
    _ENGINE_MAP["oracle"] = OracleEngine
except Exception:
    OracleEngine = None

try:
    from .nemesis.nemesis_engine import NemesisEngine
    _ENGINE_MAP["nemesis"] = NemesisEngine
except Exception:
    NemesisEngine = None

try:
    from .lexicon.lexicon_engine import LexiconEngine
    _ENGINE_MAP["lexicon"] = LexiconEngine
except Exception:
    LexiconEngine = None

try:
    from .forge.forge_engine import ForgeEngine
    _ENGINE_MAP["forge"] = ForgeEngine
except Exception:
    ForgeEngine = None

try:
    from .intake import IntakePipeline
    _ENGINE_MAP["intake"] = IntakePipeline
except Exception:
    IntakePipeline = None

try:
    from .filing_engine import FilingEngine
    _ENGINE_MAP["filing_engine"] = FilingEngine
except Exception:
    FilingEngine = None

# ── Module-based sub-packages (no single engine class) ──────────────
# These are function/module-oriented; import the sub-package directly.
# Not registered in _ENGINE_MAP (get_engine instantiates with ()).

try:
    from . import hydra_governor  # governor_engine.main(), mcp_launcher.launch_all()
except Exception:
    hydra_governor = None

try:
    from . import filing_assembler  # filing_stack_assembler.assemble_filing()
except Exception:
    filing_assembler = None

try:
    from . import agents  # delta999_orchestrator.dispatch(), delta999_*.py fleet
except Exception:
    agents = None

try:
    from .semantic.engine import SemanticSearchEngine
    _ENGINE_MAP["semantic"] = SemanticSearchEngine
except Exception:
    SemanticSearchEngine = None

try:
    from .perception.engine import LegalBERTEngine
    _ENGINE_MAP["perception"] = LegalBERTEngine
except Exception:
    LegalBERTEngine = None

try:
    from .search import HybridSearchEngine
    _ENGINE_MAP["search"] = HybridSearchEngine
except Exception:
    HybridSearchEngine = None

try:
    from .analytics import AnalyticsEngine
    _ENGINE_MAP["analytics"] = AnalyticsEngine
except Exception:
    AnalyticsEngine = None

try:
    from .typst import TypstFilingEngine
    _ENGINE_MAP["typst"] = TypstFilingEngine
except Exception:
    TypstFilingEngine = None

# ── Analysis engines (IRAC, Damages, Causal, Adversary) ─────────────

try:
    from .irac import IRACEngine
    _ENGINE_MAP["irac"] = IRACEngine
except Exception:
    IRACEngine = None

try:
    from .damages import DamagesEngine
    _ENGINE_MAP["damages"] = DamagesEngine
except Exception:
    DamagesEngine = None

try:
    from .causal import CausalChainEngine
    _ENGINE_MAP["causal"] = CausalChainEngine
except Exception:
    CausalChainEngine = None

try:
    from .adversary import AdversaryEngine
    _ENGINE_MAP["adversary"] = AdversaryEngine
except Exception:
    AdversaryEngine = None

try:
    from .temporal import TemporalKnowledgeGraph
    _ENGINE_MAP["temporal"] = TemporalKnowledgeGraph
except Exception:
    TemporalKnowledgeGraph = None

try:
    from .hypergraph import EvidenceHypergraph
    _ENGINE_MAP["hypergraph"] = EvidenceHypergraph
except Exception:
    EvidenceHypergraph = None

__all__ = [
    # Core 4
    "NexusEngine",
    "ChimeraEngine",
    "ChronosEngine",
    "CerberusEngine",
    # Extended class-based
    "EventHorizonEngine",
    "OracleEngine",
    "NemesisEngine",
    "LexiconEngine",
    "ForgeEngine",
    "IntakePipeline",
    "FilingEngine",
    # Bleeding-edge engines
    "SemanticSearchEngine",
    "LegalBERTEngine",
    "HybridSearchEngine",
    "AnalyticsEngine",
    "TypstFilingEngine",
    # Analysis engines
    "IRACEngine",
    "DamagesEngine",
    "CausalChainEngine",
    "AdversaryEngine",
    "TemporalKnowledgeGraph",
    "EvidenceHypergraph",
    # Module-based sub-packages
    "hydra_governor",
    "filing_assembler",
    "agents",
    # Factory
    "get_engine",
]

__version__ = "3.0.0"


def get_engine(name: str):
    """Factory: get_engine("nexus") → NexusEngine().

    Raises KeyError if engine name is not recognized or failed to load.
    Works for class-based engines only (22 registered).
    Module-based sub-packages (hydra_governor, filing_assembler, agents)
    should be imported directly.
    """
    name_lower = name.lower()
    if name_lower not in _ENGINE_MAP:
        available = ", ".join(sorted(_ENGINE_MAP))
        raise KeyError(f"Unknown engine '{name}'. Available: {available}")
    return _ENGINE_MAP[name_lower]()
