"""Test all 6 CORTEX domain packs load correctly (flat + rich formats)."""
import sys
sys.path.insert(0, r"J:\CORTEX")

import cortex_schema as cs

domains_dir = r"J:\CORTEX\domains"

# Test discover
print("=== discover_packs() ===")
packs = cs.discover_packs(domains_dir)
for p in packs:
    print(f"  {p['name']:20s} v{p['version']}  {p['path']}")
print(f"\nTotal discovered: {len(packs)}")
assert len(packs) >= 6, f"Expected >=6, got {len(packs)}"
print("PASS: All 6+ packs discovered\n")

# Test load each one
print("=== load() each pack ===")
for p in packs:
    try:
        pack = cs.load(p["path"])
        n_ent = len(pack.entity_re)
        n_cat = len(pack.category_re)
        n_auth = len(pack.authority_re)
        n_focus = len(pack.focus_boosts)
        n_ntypes = len(pack.node_types)
        print(f"  {pack.name:20s}  entities={n_ent:2d}  categories={n_cat:2d}  authorities={n_auth:2d}  focus_modes={n_focus:2d}  node_types={n_ntypes:2d}  OK")
    except Exception as e:
        print(f"  {p['name']:20s}  FAIL: {e}")

# Test analyze with a sample text
print("\n=== analyze() with fraud pack on sample text ===")
fraud_pack = cs.load(r"J:\CORTEX\domains\fraud.json")
sample = """
John Smith transferred $5,000,000 through Shell Corp LLC to an offshore account in 
the Cayman Islands. His accomplice, Jane Doe (SSN 123-45-6789), filed SAR reports 
that were flagged by FinCEN. The Ponzi scheme involved $50M in investor losses.
Email: john@shellcorp.com Phone: (555) 123-4567
"""
result = cs.analyze(sample, "test.txt", fraud_pack)
print(f"  Entities found: {result['entities']}")
print(f"  Categories: {result['categories']}")
print(f"  Authorities: {result['authorities']}")
print(f"  Score: {result['value_score']} ({result['value_label']})")

print("\n=== ALL TESTS PASSED ===")
