"""Phase 3 Validation Tests - Agent Fleet Optimization
Tests all changes from Phases 2A-2D.
"""
import ast, sys, os, json, tempfile, importlib.util, re
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

REPO = Path(r"C:\Users\andre\LitigationOS")
PASS = FAIL = WARN = 0

def test(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"  PASS: {name}")
    else:
        FAIL += 1; print(f"  FAIL: {name} -- {detail}")

# ============================================================
print("=" * 60)
print("TEST GROUP 1: Syntax Validation (all 8 files)")
print("=" * 60)
for f in [
    REPO / "00_SYSTEM" / "local_model" / "self_evolve_v2.py",
    REPO / "00_SYSTEM" / "engines" / "filing_production_pipeline.py",
    REPO / "agents" / "orchestrator.py",
    REPO / "agents" / "evidence_agent.py",
    REPO / "agents" / "chronology_agent.py",
    REPO / "agents" / "filing_agent.py",
    REPO / "agents" / "authority_agent.py",
    REPO / "agents" / "feedback_agent.py",
]:
    try:
        with open(f, encoding="utf-8") as fh:
            ast.parse(fh.read(), filename=f.name)
        test(f"Syntax: {f.name}", True)
    except SyntaxError as e:
        test(f"Syntax: {f.name}", False, str(e))

# ============================================================
print("\n" + "=" * 60)
print("TEST GROUP 2: Phase 2A - Self-Evolution Plateau Detection")
print("=" * 60)
se_src = (REPO / "00_SYSTEM" / "local_model" / "self_evolve_v2.py").read_text(encoding="utf-8")
test("Plateau threshold constant", "_PLATEAU_STREAK_THRESHOLD" in se_src)
test("Param grid _NGRAM_OPTIONS", "_NGRAM_OPTIONS" in se_src)
test("Param grid _MIN_DF_OPTIONS", "_MIN_DF_OPTIONS" in se_src)
test("Param grid _NB_ALPHA_OPTIONS", "_NB_ALPHA_OPTIONS" in se_src)
test("Plateau reads evolution_log.json", "evolution_log.json" in se_src and "plateau_streak" in se_src)
test("Quality delta tracking", "quality_delta" in se_src)
test("Adjustment applied flag", "adjustment_applied" in se_src)
test("Log capped at 200", "[-200:]" in se_src)
test("Parameterized TF-IDF with getattr", "getattr(self" in se_src and "ngram_range" in se_src)

# ============================================================
print("\n" + "=" * 60)
print("TEST GROUP 3: Phase 2B - Placeholder Resolution Wiring")
print("=" * 60)
fp_src = (REPO / "00_SYSTEM" / "engines" / "filing_production_pipeline.py").read_text(encoding="utf-8")
test("PlaceholderResolverV2 referenced", "PlaceholderResolverV2" in fp_src)
test("load_db_values called", "load_db_values" in fp_src)
test("process_file called", "process_file" in fp_src)
test("fill_rate metric", "fill_rate" in fp_src)

# ============================================================
print("\n" + "=" * 60)
print("TEST GROUP 4: Phase 2C - Citation Verification Wiring")
print("=" * 60)
test("bloom_citation_filter referenced", "bloom_citation_filter" in fp_src)
test("get_filter() called", "get_filter" in fp_src)
test("contains() used", ".contains(" in fp_src)
test("verify_rate metric", "verify_rate" in fp_src)

# ============================================================
print("\n" + "=" * 60)
print("TEST GROUP 5: Phase 2D - Root Agent Error Handling")
print("=" * 60)
for name in ["orchestrator.py", "evidence_agent.py", "chronology_agent.py",
             "filing_agent.py", "authority_agent.py", "feedback_agent.py"]:
    src = (REPO / "agents" / name).read_text(encoding="utf-8")
    test(f"{name}: import logging", "import logging" in src)
    test(f"{name}: logger instance",
         "logger = logging.getLogger" in src or "logging.getLogger" in src)
    test(f"{name}: try/except", "try:" in src and "except" in src)

orch_src = (REPO / "agents" / "orchestrator.py").read_text(encoding="utf-8")
test("orchestrator: errors accumulator", "errors" in orch_src and "append" in orch_src)
test("orchestrator: PARTIAL status", "PARTIAL" in orch_src)
test("orchestrator: CRASH.txt fallback", "CRASH.txt" in orch_src)

# ============================================================
print("\n" + "=" * 60)
print("TEST GROUP 6: Import & Functional Tests")
print("=" * 60)

os.chdir(REPO / "agents")
# Ensure agents dir is on sys.path for relative imports
if str(REPO / "agents") not in sys.path:
    sys.path.insert(0, str(REPO / "agents"))

# Import agent_base
try:
    import importlib
    ab = importlib.import_module("agent_base")
    test("agent_base imports", True)
    test("EvidenceAtom exists", hasattr(ab, "EvidenceAtom"))
    test("ChronoEvent exists", hasattr(ab, "ChronoEvent"))
except Exception as e:
    test("agent_base imports", False, str(e))
    ab = None

if ab:
    sys.modules["agents.agent_base"] = ab

    # authority_agent functional test
    try:
        aa = importlib.import_module("authority_agent")
        test("authority_agent imports", True)
        t = aa.make_authority(
            "MCL", "MCL 600.2918", "Recovery", "2024-01-01", 1,
            ["600.2918(1)(a)"])
        test("make_authority returns AuthorityTriple",
             isinstance(t, aa.AuthorityTriple))
    except Exception as e:
        test("authority_agent functional", False, str(e))

    # feedback_agent functional test
    try:
        fa = importlib.import_module("feedback_agent")
        test("feedback_agent imports", True)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sub" / "outcomes.jsonl"
            sig = fa.OutcomeSignal(
                outcome_id=ab.uuid_str(), case_id="TEST",
                meek_track="MEEK2", observed_time=ab.now_iso(),
                outcome_type="SUCCESS", description="test signal")
            fa.append_outcome(p, sig)
            test("append_outcome creates file", p.exists())
            parsed = json.loads(
                p.read_text(encoding="utf-8").strip())
            test("append_outcome writes valid JSON",
                 parsed["outcome_type"] == "SUCCESS")
    except Exception as e:
        test("feedback_agent functional", False, str(e))

    # evidence_agent graceful degradation
    try:
        ea = importlib.import_module("evidence_agent")
        test("evidence_agent imports", True)
        atoms = ea.build_atoms(
            case_id="TEST", root=Path(r"C:\NONEXISTENT_12345"))
        test("build_atoms bad root -> empty list (no crash)",
             isinstance(atoms, list) and len(atoms) == 0)
    except Exception as e:
        test("evidence_agent graceful degradation", False, str(e))

    # chronology_agent empty input
    try:
        ca = importlib.import_module("chronology_agent")
        test("chronology_agent imports", True)
        evts = ca.build_events([])
        test("build_events empty -> empty list",
             isinstance(evts, list) and len(evts) == 0)
    except Exception as e:
        test("chronology_agent functional", False, str(e))

    # filing_agent empty input
    try:
        fil = importlib.import_module("filing_agent")
        test("filing_agent imports", True)
        pkt = fil.build_packet(
            case_id="TEST", meek_track="MEEK2",
            atoms=[], events=[])
        test("build_packet returns valid dict",
             isinstance(pkt, dict) and "artifact_id" in pkt)
        test("build_packet empty -> empty outputs",
             pkt["outputs"]["exhibit_matrix"] == [])
    except Exception as e:
        test("filing_agent functional", False, str(e))

# ============================================================
print("\n" + "=" * 60)
print(f"SUMMARY: {PASS} PASS, {FAIL} FAIL, {WARN} WARN")
print("=" * 60)
sys.exit(1 if FAIL else 0)
