#!/usr/bin/env python
"""Test imports of new modules."""

import sys
import traceback

# Test 1: Import cross_brain_optimizer
print("=" * 60)
print("TEST 1: Importing CrossBrainOptimizer...")
try:
    from legal_ai.cross_brain_optimizer import CrossBrainOptimizer
    print("✓ cross_brain_optimizer imported OK")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()

# Test 2: Import rag_engine
print("=" * 60)
print("TEST 2: Importing LegalRAGEngine...")
try:
    from legal_ai.rag_engine import LegalRAGEngine
    print("✓ rag_engine imported OK")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()

# Test 3: Import dataclasses from cross_brain_optimizer
print("=" * 60)
print("TEST 3: Importing CrossBrainOptimizer dataclasses...")
try:
    from legal_ai.cross_brain_optimizer import (
        CrossBrainOptimizer, QueryPlan, CrossBrainResult, 
        CrossBrainSearchResult, QueryLatencyReport
    )
    o = CrossBrainOptimizer.__new__(CrossBrainOptimizer)
    print("✓ All cross_brain dataclasses importable")
    print(f"✓ Stats doc: {CrossBrainOptimizer.get_stats.__doc__}")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()

# Test 4: Import dataclasses from rag_engine
print("=" * 60)
print("TEST 4: Importing LegalRAGEngine dataclasses...")
try:
    from legal_ai.rag_engine import (
        LegalRAGEngine, RetrievedEvidence, GroundedClaim, RAGResponse
    )
    e = LegalRAGEngine.__new__(LegalRAGEngine)
    print("✓ All rag_engine dataclasses importable")
    print(f"✓ Stats doc: {LegalRAGEngine.get_stats.__doc__}")
except Exception as e:
    print(f"✗ FAILED: {e}")
    traceback.print_exc()

print("=" * 60)
print("ALL TESTS COMPLETED")
