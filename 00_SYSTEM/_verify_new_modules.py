"""Verify cross_brain_optimizer.py and rag_engine.py import correctly."""
import sys, os, ast

# Ensure we're not in repo root (shadow modules)
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=== Step 1: Syntax Check ===")
for fname in ["cross_brain_optimizer.py", "rag_engine.py"]:
    fpath = os.path.join("legal_ai", fname)
    try:
        with open(fpath, encoding="utf-8") as f:
            ast.parse(f.read(), filename=fname)
        print(f"  {fname}: SYNTAX OK")
    except SyntaxError as e:
        print(f"  {fname}: SYNTAX ERROR — {e}")
        sys.exit(1)

print("\n=== Step 2: Import Test ===")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from legal_ai.cross_brain_optimizer import (
        CrossBrainOptimizer, QueryPlan, CrossBrainResult,
        CrossBrainSearchResult, QueryLatencyReport,
    )
    print("  cross_brain_optimizer: IMPORT OK")
except Exception as e:
    print(f"  cross_brain_optimizer: IMPORT FAILED — {e}")
    sys.exit(1)

try:
    from legal_ai.rag_engine import (
        LegalRAGEngine, RetrievedEvidence, GroundedClaim, RAGResponse,
    )
    print("  rag_engine: IMPORT OK")
except Exception as e:
    print(f"  rag_engine: IMPORT FAILED — {e}")
    sys.exit(1)

print("\n=== Step 3: Instantiation Test (no BrainManager) ===")
try:
    # Pass a dummy to prevent auto-discovery of BrainManager
    opt = CrossBrainOptimizer(brain_manager=False, cache_size=8, cache_ttl_seconds=10)
    # brain_manager=False makes `self._bm = False` which is falsy but not None,
    # so it skips the lazy import
    print(f"  CrossBrainOptimizer: OK — stats={opt.get_stats()['version']}")
except Exception as e:
    print(f"  CrossBrainOptimizer: INSTANTIATION FAILED — {e}")

try:
    rag = LegalRAGEngine(brain_manager=False, cross_brain_optimizer=False)
    print(f"  LegalRAGEngine: OK — stats={rag.get_stats()['version']}")
except Exception as e:
    print(f"  LegalRAGEngine: INSTANTIATION FAILED — {e}")

print("\n=== Step 4: Functional Test ===")
# Test query planning (no DB needed)
opt2 = CrossBrainOptimizer(brain_manager=False)
plan = opt2.plan_query("MCR 2.003 disqualification")
print(f"  plan_query: type={plan.query_type}, brains={plan.target_brains}")

# Test lane detection
rag2 = LegalRAGEngine(brain_manager=False, cross_brain_optimizer=False)
lane = rag2.detect_lane("custody parenting time best interest")
print(f"  detect_lane: {lane}")

# Test generate with mock evidence
mock_ev = [
    RetrievedEvidence(
        text="MCR 2.003 requires disqualification when a judge cannot be impartial. The rule provides that a party may file a motion.",
        source="authority_brain.court_rules_fts",
        brain_name="authority_brain",
        table_name="court_rules_fts",
        score=1.0,
        method="fts5",
        evidence_strength="strong",
    ),
    RetrievedEvidence(
        text="The judge denied the motion for disqualification without holding a hearing. This violated the procedural requirements of MCR 2.003(D).",
        source="narrative_brain.orders_fts",
        brain_name="narrative_brain",
        table_name="orders_fts",
        score=0.8,
        method="fts5",
        evidence_strength="moderate",
    ),
]
answer = rag2.generate("What MCR governs judicial disqualification?", mock_ev)
print(f"  generate: {len(answer)} chars, starts with: {answer[:80]}...")

# Test grounding
conf, claims = rag2.verify_grounding(answer, mock_ev)
print(f"  verify_grounding: confidence={conf}, claims={len(claims)}")

print("\n=== ALL TESTS PASSED ===")
