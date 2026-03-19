#!/usr/bin/env python3
"""Run import tests and print results."""

import sys
import traceback

print("=" * 70)
print("TEST 1: Cross-Brain Optimizer Import")
print("=" * 70)
try:
    from legal_ai.cross_brain_optimizer import CrossBrainOptimizer
    print("cross_brain_optimizer OK")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

print()
print("=" * 70)
print("TEST 2: RAG Engine Import")
print("=" * 70)
try:
    from legal_ai.rag_engine import LegalRAGEngine
    print("rag_engine OK")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

print()
print("=" * 70)
print("TEST 3: Cross-Brain Dataclasses Import")
print("=" * 70)
try:
    from legal_ai.cross_brain_optimizer import (
        CrossBrainOptimizer, QueryPlan, CrossBrainResult,
        CrossBrainSearchResult, QueryLatencyReport
    )
    o = CrossBrainOptimizer.__new__(CrossBrainOptimizer)
    print("All cross_brain dataclasses importable")
    print("Stats:", CrossBrainOptimizer.get_stats.__doc__)
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

print()
print("=" * 70)
print("TEST 4: RAG Engine Dataclasses Import")
print("=" * 70)
try:
    from legal_ai.rag_engine import (
        LegalRAGEngine, RetrievedEvidence, GroundedClaim, RAGResponse
    )
    e = LegalRAGEngine.__new__(LegalRAGEngine)
    print("All rag_engine dataclasses importable")
    print("Stats:", LegalRAGEngine.get_stats.__doc__)
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

print()
print("=" * 70)
print("ALL TESTS COMPLETED")
print("=" * 70)
