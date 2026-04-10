"""Test CORTEX v1.1.0 schema alignment against real DB."""
import sys, sqlite3, json
sys.path.insert(0, r"D:\LitigationOS_tmp\blueprint_build")
from cortex import CortexEngine, VERSION

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA cache_size=-32000")

cx = CortexEngine(conn)
print(f"CORTEX {VERSION} -- {len(cx._tables)} tables found")
results = {}

# 1. compute_damages
print("\n=== compute_damages ===")
d = cx.compute_damages()
print(f"  Lanes: {list(d['lanes'].keys())}")
print(f"  Total: ${d['total_low']:,.0f} - ${d['total_high']:,.0f}")
sep = d.get('separation_damages', {})
print(f"  Sep damages: {sep.get('days',0)} days = ${sep.get('low',0):,.0f} - ${sep.get('high',0):,.0f}")
results['damages'] = 'PASS' if d['total_high'] > 0 else 'FAIL'

# 2. lane_readiness
print("\n=== lane_readiness ===")
lr = cx.lane_readiness()
for ln, info in lr.items():
    s = info['scores']
    print(f"  Lane {ln}: E={s['evidence']} G={s['grounds']} C={s['citations']} P={s['presentation']} Total={info['total']}/100")
results['readiness'] = 'PASS' if any(v['total'] > 0 for v in lr.values()) else 'FAIL'

# 3. check_deadlines
print("\n=== check_deadlines ===")
dl = cx.check_deadlines(365)
print(f"  Upcoming: {len(dl['deadlines'])}")
print(f"  Overdue: {len(dl['overdue'])}")
print(f"  Critical: {len(dl['critical'])}")
sep = dl['separation']
print(f"  Separation: {sep['days']} days ({sep['urgency']})")
for d in dl['deadlines'][:3]:
    print(f"    {d.get('due_date','?')} | {d.get('title','?')[:60]} | {d.get('status','?')}")
results['deadlines'] = 'PASS' if sep['days'] > 200 else 'FAIL'

# 4. filing_qa (test with F1)
print("\n=== filing_qa('F1') ===")
qa = cx.filing_qa('F1')
print(f"  Score: {qa['score']:.0%} ({qa['passed']}/{qa['total']} gates)")
print(f"  Verdict: {qa['verdict']}")
for g in qa['gates']:
    mark = '[PASS]' if g['passed'] else '[FAIL]'
    print(f"    {mark} {g['gate']}: {g['detail'][:60]}")
results['filing_qa'] = 'PASS'  # structural test, always passes if no crash

# 5. adversary_profile
print("\n=== adversary_profile('Emily Watson') ===")
ap = cx.adversary_profile('Emily Watson')
print(f"  Threat score: {ap['threat_score']}/10")
print(f"  Evidence: {ap.get('evidence_count', 0)}")
print(f"  Impeachment: {ap.get('impeachment_total', 0)}")
print(f"  Contradictions: {len(ap.get('contradictions', []))}")
print(f"  Violations: {ap.get('violation_total', 0)}")
results['adversary'] = 'PASS' if ap['threat_score'] > 0 else 'FAIL'

# 6. adversary_profile (judge)
print("\n=== adversary_profile('McNeill') ===")
jap = cx.adversary_profile('McNeill')
print(f"  Threat score: {jap['threat_score']}/10")
print(f"  Violations: {jap.get('violation_total', 0)}")
print(f"  Cartel intel: {len(jap.get('cartel', []))}")
results['judge_profile'] = 'PASS' if jap.get('violation_total', 0) > 0 else 'FAIL'

# 7. detect_gaps
print("\n=== detect_gaps ===")
gaps = cx.detect_gaps()
for ln, data in gaps.items():
    g_count = len(data['gaps'])
    print(f"  Lane {ln}: {g_count} gaps, score={data['score']}")
results['gaps'] = 'PASS'

# 8. strategic_report
print("\n=== strategic_report ===")
sr = cx.strategic_report()
print(f"  Separation: {sr['separation_days']} days")
print(f"  DB tables tracked: {len(sr['db_stats'])}")
print(f"  Threats: {len(sr['top_threats'])}")
print(f"  Critical gaps: {len(sr['critical_gaps'])}")
print(f"  Actions: {len(sr['recommended_actions'])}")
for t in sr['top_threats'][:3]:
    print(f"    {t['name']}: threat={t['threat']}, evidence={t['evidence']}")
results['strategic'] = 'PASS' if sr['separation_days'] > 200 else 'FAIL'

# 9. nexus_fuse
print("\n=== nexus_fuse('parental alienation') ===")
nf = cx.nexus_fuse('parental alienation', 5)
print(f"  Total hits: {nf['total_hits']}")
print(f"  Coverage: {nf['coverage']}/{nf['max_sources']} sources")
for key, rows in nf['sources'].items():
    if rows:
        print(f"    {key}: {len(rows)} results")
results['fuse'] = 'PASS' if nf['total_hits'] > 0 else 'FAIL'

# 10. irac_analyze
print("\n=== irac_analyze('parental alienation') ===")
ir = cx.irac_analyze('parental alienation', 'A')
print(f"  Existing analyses: {len(ir['analyses'])}")
print(f"  Authorities: {len(ir['authorities'])}")
results['irac'] = 'PASS'

# 11. build_xexam
print("\n=== build_xexam('Emily Watson') ===")
xe = cx.build_xexam('Emily Watson', 5)
print(f"  Packages: {len(xe['packages'])}")
print(f"  Contradictions: {len(xe['contradictions'])}")
print(f"  Questions: {len(xe['questions'])}")
results['xexam'] = 'PASS' if len(xe['packages']) > 0 else 'FAIL'

# 12. search_all
print("\n=== search_all('ex parte') ===")
sa = cx.search_all('ex parte', 3)
print(f"  Total hits: {sa['total']}")
for key, rows in sa['results'].items():
    if rows:
        print(f"    {key}: {len(rows)}")
results['search'] = 'PASS' if sa['total'] > 0 else 'FAIL'

# 13. generate_rebuttal
print("\n=== generate_rebuttal('Andrew is dangerous') ===")
rb = cx.generate_rebuttal('Andrew is dangerous')
print(f"  Evidence: {len(rb['evidence'])}")
print(f"  Authorities: {len(rb['authorities'])}")
print(f"  Impeachment: {len(rb['impeachment'])}")
print(f"  Strength: {rb['strength']}/100 ({rb['rating']})")
results['rebuttal'] = 'PASS' if rb['strength'] > 0 else 'FAIL'

# SUMMARY
print("\n" + "="*60)
print("CORTEX v1.1.0 ALIGNMENT TEST RESULTS")
print("="*60)
passed = sum(1 for v in results.values() if v == 'PASS')
total = len(results)
for name, status in results.items():
    mark = '[OK]' if status == 'PASS' else '[!!]'
    print(f"  {mark} {name}: {status}")
print(f"\n  TOTAL: {passed}/{total} PASS")
print(f"  STATUS: {'ALL CHECKS PASSED' if passed == total else 'SOME CHECKS FAILED'}")

conn.close()
