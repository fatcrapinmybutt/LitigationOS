"""Test ALL 6 THEMANBEARPIG engines against real DB.
CORTEX v1.2.0 + CHRONOS v1.0.0 + ORACLE v1.0.0 + PROMETHEUS v1.0.0 + ATHENA v1.0.0 + AUTOMATON v1.0.0
Run: $env:PYTHONUTF8="1"; python -I D:\LitigationOS_tmp\test_all_engines.py
"""
import sys, os, sqlite3, traceback

# Add engine dir to path
sys.path.insert(0, r"D:\LitigationOS_tmp\blueprint_build")

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"

def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn

results = []
def test(name, fn):
    try:
        r = fn()
        ok = r is not None and (not isinstance(r, dict) or "error" not in r)
        tag = "PASS" if ok else "FAIL"
        detail = ""
        if isinstance(r, dict):
            detail = " | ".join(f"{k}={v}" for k, v in list(r.items())[:5])
        elif isinstance(r, list):
            detail = f"list[{len(r)}]"
        results.append((tag, name, str(detail)[:120]))
        print(f"  [{tag}] {name}: {str(detail)[:100]}")
    except Exception as e:
        results.append(("FAIL", name, str(e)[:120]))
        print(f"  [FAIL] {name}: {e}")
        traceback.print_exc()

conn = get_conn()

# ═══ CORTEX ═══
print("\n=== CORTEX v1.2.0 ===")
from cortex import CortexEngine
cx = CortexEngine(conn)

test("cortex.compute_damages", lambda: cx.compute_damages())
test("cortex.lane_readiness", lambda: cx.lane_readiness())
test("cortex.check_deadlines", lambda: cx.check_deadlines())
test("cortex.filing_qa(F1)", lambda: cx.filing_qa("F1"))
test("cortex.adversary_profile(Emily)", lambda: cx.adversary_profile("Emily"))
test("cortex.detect_gaps", lambda: cx.detect_gaps())
test("cortex.strategic_report", lambda: cx.strategic_report())
test("cortex.nexus_fuse(custody)", lambda: cx.nexus_fuse("custody"))
test("cortex.irac_analyze(alienation)", lambda: cx.irac_analyze("alienation"))
test("cortex.build_xexam(Watson)", lambda: cx.build_xexam("Watson"))
test("cortex.search_all(PPO)", lambda: cx.search_all("PPO"))
test("cortex.generate_rebuttal(dangerous)", lambda: cx.generate_rebuttal("dangerous"))
test("cortex.build_narrative(A)", lambda: cx.build_narrative("A"))

# ═══ CHRONOS ═══
print("\n=== CHRONOS v1.0.0 ===")
from chronos import ChronosEngine
ch = ChronosEngine(conn)

test("chronos.build_timeline", lambda: ch.build_timeline())
test("chronos.detect_cycles", lambda: ch.detect_cycles())
test("chronos.escalation_score(Emily)", lambda: ch.escalation_score("Emily"))
test("chronos.separation_impact", lambda: ch.separation_impact())
test("chronos.event_velocity", lambda: ch.event_velocity())
test("chronos.temporal_clusters", lambda: ch.temporal_clusters())
test("chronos.milestone_timeline", lambda: ch.milestone_timeline())
test("chronos.actor_timeline(McNeill)", lambda: ch.actor_timeline("McNeill"))
test("chronos.lane_chronology(A)", lambda: ch.lane_chronology("A"))

# ═══ ORACLE ═══
print("\n=== ORACLE v1.0.0 ===")
from oracle import OracleEngine
oc = OracleEngine(conn)

test("oracle.predict_ruling(custody)", lambda: oc.predict_ruling("custody"))
test("oracle.forecast_adversary(Emily)", lambda: oc.forecast_adversary("Emily"))
test("oracle.filing_success(F1)", lambda: oc.filing_success_probability("F1"))
test("oracle.optimal_sequence", lambda: oc.optimal_sequence())
test("oracle.counter_strategy(false allegations)", lambda: oc.counter_strategy("false allegations"))
test("oracle.risk_matrix", lambda: oc.risk_matrix())
test("oracle.early_warning", lambda: oc.early_warning())
test("oracle.judicial_tendency", lambda: oc.judicial_tendency())

# ═══ PROMETHEUS ═══
print("\n=== PROMETHEUS v1.0.0 ===")
from prometheus import PrometheusEngine
pm = PrometheusEngine(conn)

test("prometheus.generate_irac(alienation)", lambda: pm.generate_irac("alienation"))
test("prometheus.authority_chain(MCR 2.003)", lambda: pm.authority_chain("MCR 2.003"))
test("prometheus.build_affidavit(custody)", lambda: pm.build_affidavit("custody"))
test("prometheus.exhibit_index(A)", lambda: pm.exhibit_index("A"))
test("prometheus.strike_plan(A)", lambda: pm.strike_plan("A"))
test("prometheus.weapon_inventory", lambda: pm.weapon_inventory())
test("prometheus.xexam_script(Emily Watson)", lambda: pm.xexam_script("Emily Watson"))
test("prometheus.filing_package_status", lambda: pm.filing_package_status())
test("prometheus.rebuttal_builder(dangerous)", lambda: pm.rebuttal_builder("dangerous"))

# === ATHENA ===
print("\n=== ATHENA v1.0.0 ===")
from athena import Athena
at = Athena(conn)

test("athena.enrich_argument(alienation,A)", lambda: at.enrich_argument("parental alienation", "A"))
test("athena.find_authority(custody)", lambda: at.find_authority("custody"))
test("athena.doctrine_map(due_process)", lambda: at.doctrine_map("due_process"))
test("athena.citation_network(MCL 722.23)", lambda: at.citation_network("MCL 722.23"))
test("athena.scotus_precedent(parental rights)", lambda: at.scotus_precedent("parental rights"))
test("athena.michigan_precedent(custody)", lambda: at.michigan_precedent("custody"))
test("athena.normalize_language(test)", lambda: at.normalize_language("the judge kept the dad from seeing his kid"))
test("athena.authority_score(F3)", lambda: at.authority_score("F3"))
test("athena.build_authority_brief(due process,E)", lambda: at.build_authority_brief("ex parte orders violated due process", "E"))
test("athena.professional_standards(judicial)", lambda: at.professional_standards("judicial conduct"))

# ═══ AUTOMATON ═══
print("\n=== AUTOMATON v1.0.0 ===")
from automaton import AutomatonEngine
# AUTOMATON takes db_path, not conn — builds its own connections (thread-safe)
au = AutomatonEngine(db_path=DB, callback=None, cycle_interval=300)

test("automaton.status", lambda: au.status())
test("automaton.get_templates", lambda: au.get_templates())
test("automaton.get_centrality(10)", lambda: au.get_centrality(top_n=10))
test("automaton.get_gaps", lambda: au.get_gaps())
test("automaton.get_results(5)", lambda: au.get_results(limit=5))
test("automaton.get_compound_discoveries", lambda: au.get_compound_discoveries())
# Test single inference cycle (force, don't start daemon)
test("automaton.force_cycle", lambda: au.force_cycle())

# After force_cycle, results should be populated
test("automaton.post_cycle_results", lambda: au.get_results(limit=3))
test("automaton.post_cycle_centrality", lambda: au.get_centrality(top_n=5))
test("automaton.post_cycle_gaps", lambda: au.get_gaps())
test("automaton.post_cycle_compounds", lambda: au.get_compound_discoveries())

# Test node-specific queries (use actual graph node IDs with P: prefix)
test("automaton.coa_for_node(McNeill)", lambda: au.coa_for_node("P:Hon. Jenny L. McNeill"))
test("automaton.paths(Watson,McNeill)", lambda: au.paths_between("P:Emily A. Watson", "P:Hon. Jenny L. McNeill"))
test("automaton.filing_skeleton(T01)", lambda: au.filing_skeleton("T01"))

# Clean up — ensure no daemon was started
try:
    au.stop()
except Exception:
    pass

# ═══ D3: NODE DEEP-DIVE MODAL API ═══
print("\n=== D3 NODE DEEP-DIVE v13.0.0 ===")
# These are LitigationAPI instance methods — construct a lightweight API
from adversary_blueprint import LitigationAPI
api = LitigationAPI()

test("d3.node_full_profile(Watson)", lambda: api.node_full_profile("Emily Watson"))
test("d3.node_connections(McNeill)", lambda: api.node_connections("McNeill"))
test("d3.node_connections_graph(Watson)", lambda: api.node_connections_graph("Watson"))
test("d3.node_legal(McNeill)", lambda: api.node_legal("McNeill"))
test("d3.node_timeline_full(Watson)", lambda: api.node_timeline_full("Watson", 20))
test("d3.node_evidence_vault(PPO)", lambda: api.node_evidence_vault("PPO", "relevance", 10, 0))
test("d3.node_weapons(Emily Watson)", lambda: api.node_weapons("Emily Watson"))

# ═══ D4: CROSSWIRE INTELLIGENCE API ═══
print("\n=== D4 CROSSWIRE INTELLIGENCE v14.0.0 ===")
test("d4.edge_intelligence(Watson,McNeill)", lambda: api.edge_intelligence("Emily Watson", "McNeill"))
test("d4.edge_conspiracy_check(Watson,McNeill)", lambda: api.edge_conspiracy_check("Emily Watson", "McNeill"))
test("d4.edge_constitutional_cascade(Watson,McNeill)", lambda: api.edge_constitutional_cascade("Emily Watson", "McNeill"))

# ═══ D5: INFERENCE THEATER API ═══
print("\n=== D5 INFERENCE THEATER v15.0.0 ===")
test("d5.inference_theater_status", lambda: api.inference_theater_status())
test("d5.inference_theater_feed(10)", lambda: api.inference_theater_feed(10))
test("d5.inference_theater_top_coa(10)", lambda: api.inference_theater_top_coa(10))
test("d5.inference_theater_gaps(10)", lambda: api.inference_theater_gaps(10))
test("d5.inference_theater_compounds(10)", lambda: api.inference_theater_compounds(10))
test("d5.inference_theater_cascade_alerts", lambda: api.inference_theater_cascade_alerts())

# === D6: ROOMS Navigation System ===
test("d6.room_war_room", lambda: api.room_war_room())
test("d6.room_dossier_grid", lambda: api.room_dossier_grid())
test("d6.room_chronicle(50)", lambda: api.room_chronicle(50))
test("d6.room_arsenal(20)", lambda: api.room_arsenal(20))
test("d6.room_situation", lambda: api.room_situation())

# === D7: Auto-Filing Skeleton Generator ===
test("d7.filing_skeleton_full(disqualification)", lambda: api.filing_skeleton_full(template_id="disqualification"))
test("d7.filing_skeleton_batch(50)", lambda: api.filing_skeleton_batch(50, 5))
test("d7.filing_skeleton_export(custody)", lambda: api.filing_skeleton_export(template_id="custody"))

# Cleanup API AUTOMATON if it started
try:
    if hasattr(api, '_automaton') and api._automaton:
        api._automaton.stop()
except Exception:
    pass

# ═══ SUMMARY ═══
conn.close()
print("\n" + "=" * 60)
passed = sum(1 for r in results if r[0] == "PASS")
failed = sum(1 for r in results if r[0] == "FAIL")
total = len(results)
print(f"TOTAL: {passed}/{total} PASS, {failed} FAIL")
for tag, name, detail in results:
    if tag == "FAIL":
        print(f"  FAILED: {name} -- {detail}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
