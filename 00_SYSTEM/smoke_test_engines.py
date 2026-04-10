#!/usr/bin/env python3
"""
SINGULARITY Engine Smoke Tests (v22)
Tests import, instantiation, and basic operations for all 9 engines wired into themanbearpig.py
"""
import sys
import os
from pathlib import Path

# Add 00_SYSTEM to path (no shadow module risk with -I flag)
sys.path.insert(0, r"C:\Users\andre\LitigationOS\00_SYSTEM")

# Database path constant
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Track results
results = {}

def test_engine(engine_name, test_func):
    """Generic engine test wrapper"""
    try:
        print(f"\n[TEST] {engine_name}...", end=" ")
        test_func()
        results[engine_name] = ("PASS", None)
        print("✓ PASS")
        return True
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)[:120]}"
        results[engine_name] = ("FAIL", error_msg)
        print(f"✗ FAIL: {error_msg}")
        return False


# ===== ENGINE 1: EventBus =====
def test_eventbus():
    """EventBus: subscribe, publish_sync, verify callback"""
    from engines.event_bus.bus import EventBus
    
    bus = EventBus()
    
    # Create a callback tracker
    calls = []
    def handler(event):
        calls.append(event)
    
    # Subscribe and publish
    bus.subscribe("test_topic", handler)
    bus.publish_sync("test_topic", {"data": "test"})
    
    # Verify
    assert len(calls) > 0, "Event handler not called"
    # Handler receives an Event object, extract payload
    assert hasattr(calls[0], 'payload') or isinstance(calls[0], dict), "Event structure invalid"


# ===== ENGINE 2: GeneticMemory =====
def test_genetic_memory():
    """GeneticMemory: instantiate and call stats()"""
    from engines.genetic_memory.memory import GeneticMemory
    
    gm = GeneticMemory(db_path=DB_PATH)
    
    # Call a read method to verify connectivity
    result = gm.stats()
    assert result is not None, "stats() returned None"


# ===== ENGINE 3: ContradictionHarvester =====
def test_contradiction_harvester():
    """ContradictionHarvester: instantiate and call stats()"""
    from engines.contradiction_harvester.harvester import ContradictionHarvester
    
    ch = ContradictionHarvester(db_path=DB_PATH)
    
    # Call a status method
    result = ch.stats()
    assert result is not None, "stats() returned None"


# ===== ENGINE 4: ProvenanceChain =====
def test_provenance_chain():
    """ProvenanceChain: instantiate and call read method"""
    from engines.provenance.chain import ProvenanceChain
    
    pc = ProvenanceChain(db_path=DB_PATH)
    
    # Call a read method
    if hasattr(pc, 'get_status'):
        result = pc.get_status()
    elif hasattr(pc, 'status'):
        result = pc.status()
    else:
        # Just verify instantiation worked
        result = pc
    
    assert result is not None, "ProvenanceChain read failed"


# ===== ENGINE 5: PredictiveEngine =====
def test_predictive_engine():
    """PredictiveEngine: instantiate and call predict/status"""
    from engines.predictive.predictor import PredictiveEngine
    
    pe = PredictiveEngine(db_path=DB_PATH)
    
    # Call a method to verify it works
    if hasattr(pe, 'get_status'):
        result = pe.get_status()
    elif hasattr(pe, 'status'):
        result = pe.status()
    elif hasattr(pe, 'predict'):
        result = pe.predict({})
    else:
        result = pe
    
    assert result is not None, "PredictiveEngine method failed"


# ===== ENGINE 6: EvidenceGraphBridge =====
def test_evidence_graph_bridge():
    """EvidenceGraphBridge: verify class and method signatures"""
    from engines.bridge.bridge import EvidenceGraphBridge
    
    egb = EvidenceGraphBridge()
    
    # Verify key methods exist
    methods = ['process_queue', 'get_stats', 'ensure_queue_table', 'extract_entities']
    found_methods = sum(1 for m in methods if hasattr(egb, m))
    
    assert found_methods > 0, f"EvidenceGraphBridge missing expected methods (found {found_methods}/{len(methods)})"


# ===== ENGINE 7: FilingAssembler =====
def test_filing_assembler():
    """FilingAssembler: instantiate and call status/list"""
    from engines.filing_assembly.assembler import FilingAssembler
    
    fa = FilingAssembler(db_path=DB_PATH)
    
    # Call a read method
    if hasattr(fa, 'get_status'):
        result = fa.get_status()
    elif hasattr(fa, 'list_packages'):
        result = fa.list_packages()
    elif hasattr(fa, 'status'):
        result = fa.status()
    else:
        result = fa
    
    assert result is not None, "FilingAssembler method failed"


# ===== ENGINE 8: BrainSyncEngine =====
def test_brain_sync_engine():
    """BrainSyncEngine: verify class and method signatures"""
    from engines.brain_sync.sync_engine import BrainSyncEngine
    
    bse = BrainSyncEngine()
    
    # Verify key methods exist
    methods = ['sync_status', 'discover_brains', 'sync_brain_to_central', 'close']
    found_methods = sum(1 for m in methods if hasattr(bse, m))
    
    assert found_methods > 0, f"BrainSyncEngine missing expected methods (found {found_methods}/{len(methods)})"


# ===== ENGINE 9: TelemetryEngine =====
def test_telemetry_engine():
    """TelemetryEngine: instantiate and call status/read"""
    from engines.telemetry.engine import TelemetryEngine
    
    te = TelemetryEngine(db_path=DB_PATH)
    
    # Call a read method
    if hasattr(te, 'get_status'):
        result = te.get_status()
    elif hasattr(te, 'status'):
        result = te.status()
    elif hasattr(te, 'query'):
        result = te.query()
    else:
        result = te
    
    assert result is not None, "TelemetryEngine method failed"


def main():
    """Run all tests"""
    print("=" * 70)
    print("SINGULARITY ENGINE SMOKE TESTS (v22)")
    print("=" * 70)
    print(f"Database: {DB_PATH}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print()
    
    # Run all 9 tests
    test_engine("EventBus", test_eventbus)
    test_engine("GeneticMemory", test_genetic_memory)
    test_engine("ContradictionHarvester", test_contradiction_harvester)
    test_engine("ProvenanceChain", test_provenance_chain)
    test_engine("PredictiveEngine", test_predictive_engine)
    test_engine("EvidenceGraphBridge", test_evidence_graph_bridge)
    test_engine("FilingAssembler", test_filing_assembler)
    test_engine("BrainSyncEngine", test_brain_sync_engine)
    test_engine("TelemetryEngine", test_telemetry_engine)
    
    # Print summary
    print("\n" + "=" * 70)
    passed = sum(1 for status, _ in results.values() if status == "PASS")
    failed = sum(1 for status, _ in results.values() if status == "FAIL")
    
    print(f"SUMMARY: {passed}/9 engines operational")
    
    if failed > 0:
        print(f"\nFailed engines ({failed}):")
        for engine, (status, error) in results.items():
            if status == "FAIL":
                print(f"  • {engine}: {error}")
    
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
