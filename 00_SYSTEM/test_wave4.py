"""Test Wave 4 API methods for THEMANBEARPIG v15."""
import sys, os
SCRIPTS = r'C:\Users\andre\LitigationOS\scripts'
sys.path.insert(0, SCRIPTS)
os.chdir(SCRIPTS)

code = open('themanbearpig.py', encoding='utf-8').read()
exec(code.split('def main():')[0])

api = UnifiedAPI()
print('=== WAVE 4 API TESTS ===')
passed = 0
failed = 0

# Test 1: get_pattern_summary
try:
    ps = api.get_pattern_summary()
    assert isinstance(ps, dict), "Should return dict"
    print(f'[OK] get_pattern_summary: {ps}')
    passed += 1
except Exception as e:
    print(f'[FAIL] get_pattern_summary: {e}')
    failed += 1

# Test 2: get_patterns_by_type
try:
    pt = api.get_patterns_by_type('RETALIATION', severity='CRITICAL', limit=3)
    assert 'patterns' in pt, "Should have patterns key"
    assert 'count' in pt, "Should have count key"
    print(f'[OK] get_patterns_by_type(RETALIATION,CRITICAL): {pt["count"]} returned, {pt["total"]} total')
    if pt['patterns']:
        print(f'     Sample: {pt["patterns"][0]["description"][:80]}...')
    passed += 1
except Exception as e:
    print(f'[FAIL] get_patterns_by_type: {e}')
    failed += 1

# Test 3: get_cross_lane_bridges
try:
    clb = api.get_cross_lane_bridges(limit=5)
    assert 'bridges' in clb, "Should have bridges key"
    print(f'[OK] get_cross_lane_bridges: {clb["count"]} bridges found')
    if clb['bridges']:
        b = clb['bridges'][0]
        print(f'     Sample: node={b["node_id"][:40]} lanes={b.get("lanes",[])}')
    passed += 1
except Exception as e:
    print(f'[FAIL] get_cross_lane_bridges: {e}')
    failed += 1

# Test 4: search_similar_communities
try:
    sc = api.search_similar_communities('judicial misconduct', top_k=5)
    assert 'results' in sc, "Should have results key"
    assert 'method' in sc, "Should have method key"
    print(f'[OK] search_similar_communities: {sc["count"]} results via {sc["method"]}')
    if sc['results']:
        print(f'     Top: {sc["results"][0]["label"][:60]}')
    passed += 1
except Exception as e:
    print(f'[FAIL] search_similar_communities: {e}')
    failed += 1

# Test 5: build_filing_section
try:
    fs = api.build_filing_section('c_1')
    assert 'markdown' in fs, "Should have markdown key"
    assert len(fs['markdown']) > 50, "Markdown should be non-trivial"
    print(f'[OK] build_filing_section(c_1): {len(fs["markdown"])} chars')
    print(f'     Evidence: {fs["evidence_count"]}, Authorities: {fs["authority_count"]}')
    passed += 1
except Exception as e:
    print(f'[FAIL] build_filing_section: {e}')
    failed += 1

# Test 6: Health check includes patterns+embeddings
try:
    h = api.get_health()
    bd = h.get('brain_db', {})
    assert 'patterns' in bd, "Health should include pattern count"
    assert 'embeddings' in bd, "Health should include embedding count"
    print(f'[OK] Health check: patterns={bd["patterns"]}, embeddings={bd["embeddings"]}')
    passed += 1
except Exception as e:
    print(f'[FAIL] Health check patterns/embeddings: {e}')
    failed += 1

print(f'\n=== {passed}/{passed+failed} WAVE 4 TESTS PASSED ===')
if failed:
    sys.exit(1)
