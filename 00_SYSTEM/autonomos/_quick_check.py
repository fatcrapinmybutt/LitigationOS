"""Quick validation — run: python _quick_check.py"""
import sys, importlib
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
ok, fail = 0, 0
modules = [
    ("shared.autonomos_config", "Config"),
    ("shared.provenance", "Provenance"),
    ("shared.event_bridge", "EventBridge"),
    ("sentinel.sentinel_monitor", "Monitor"),
    ("sentinel.sentinel_classifier", "Classifier"),
    ("sentinel.sentinel_mover", "Mover"),
    ("sentinel.sentinel", "Sentinel"),
    ("sentinel.self_heal", "SelfHeal"),
    ("sentinel.drive_fortress", "DriveFortress"),
    ("sentinel.root_cleanup", "RootCleanup"),
    ("sentinel.windows_service", "WinService"),
    ("sentinel.desktop_ws", "DesktopWS"),
    ("inquisitor.inquisitor", "Inquisitor"),
    ("inquisitor.publisher", "Publisher"),
    ("inquisitor.evidence_chain_validator", "EvidenceChain"),
    ("inquisitor.citation_validator", "CitationValidator"),
    ("inquisitor.judicial_tracker", "JudicialTracker"),
    ("inquisitor.filing_optimizer", "FilingOptimizer"),
    ("inquisitor.temporal_anomaly", "TemporalAnomaly"),
    ("inquisitor.watson_pattern", "WatsonPattern"),
    ("inquisitor.cross_lane_fusion", "CrossLaneFusion"),
    ("inquisitor.semantic_dedup", "SemanticDedup"),
    ("inquisitor.nuclear_assembler", "NuclearAssembler"),
    ("inquisitor.auto_impeach", "AutoImpeach"),
    ("inquisitor.counter_intel", "CounterIntel"),
    ("inquisitor.predict_filing", "PredictFiling"),
    ("inquisitor.auto_report", "AutoReport"),
    ("inquisitor.response_warfare", "ResponseWarfare"),
    ("inquisitor.self_evolve", "SelfEvolve"),
    # APEX Ω∞ engines (20)
    ("inquisitor.perjury_detector", "PerjuryDetector"),
    ("inquisitor.bif_scorer", "BIFScorer"),
    ("inquisitor.damages_calc", "DamagesCalc"),
    ("inquisitor.emergency_gen", "EmergencyGen"),
    ("inquisitor.order_tracker", "OrderTracker"),
    ("inquisitor.alienation_compiler", "AlienationCompiler"),
    ("inquisitor.coordination_prover", "CoordinationProver"),
    ("inquisitor.constitutional_mapper", "ConstitutionalMapper"),
    ("inquisitor.witness_credibility", "WitnessCredibility"),
    ("inquisitor.discovery_gen", "DiscoveryGen"),
    ("inquisitor.record_builder", "RecordBuilder"),
    ("inquisitor.plain_error", "PlainError"),
    ("inquisitor.amicus_finder", "AmicusFinder"),
    ("inquisitor.sixthcircuit_prep", "SixthCircuitPrep"),
    ("inquisitor.proc_guardian", "ProcGuardian"),
    ("inquisitor.intel_dashboard", "IntelDashboard"),
    ("inquisitor.gal_bias_detector", "GALBiasDetector"),
    ("inquisitor.habeas_compiler", "HabeasCompiler"),
    ("inquisitor.deposition_prep", "DepositionPrep"),
    ("inquisitor.settlement_analyzer", "SettlementAnalyzer"),
]
for mod, label in modules:
    try:
        importlib.import_module(mod)
        print(f"  OK  {label:25s} ({mod})")
        ok += 1
    except Exception as e:
        print(f"  FAIL {label:25s} -> {e}")
        fail += 1
print(f"\n{'='*50}\n{ok} OK, {fail} FAILED out of {ok+fail} modules")
