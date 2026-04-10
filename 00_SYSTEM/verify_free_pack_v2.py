"""Verify the upgraded free pack loads and validates correctly."""
import sys, os, json
sys.path.insert(0, r"J:\CORTEX")

from cortex_schema import load, analyze, discover_packs

# Test loading the upgraded pack
pack_path = r"J:\CORTEX\domains\osint.json"
try:
    pack = load(pack_path)
    print("=== PACK VALIDATION ===")
    print(f"Name:        {pack.name}")
    print(f"Version:     {pack.version}")
    print(f"Entities:    {len(pack.entity_patterns)} extractors")
    print(f"Categories:  {len(pack.evidence_categories)} evidence types")
    print(f"Authorities: {len(pack.authority_patterns)} legal pattern sets")
    print(f"Status:      PASS")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Quick analyze test with sample text
try:
    test_text = """
    John Smith called 555-123-4567 from IP 192.168.1.100.
    Payment sent to 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD12.
    Meeting at 123 Main St, Springfield. Case No. 2024-001507-DC.
    Email: test@example.com. SSN: 123-45-6789.
    Company: Acme Corp Inc. FOIA request pending.
    """
    result = analyze(test_text, "test_sample.txt", pack)
    total_entities = sum(result["entities"].values())
    print(f"\nAnalysis test: {total_entities} entities found in sample text")
    for ent_type, count in sorted(result["entities"].items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"  {ent_type}: {count}")
    print(f"Categories:  {len(result['categories'])}")
    print(f"Value Score: {result['value_score']} ({result['value_label']})")
except Exception as e:
    print(f"ANALYZE FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Verify all 55 packs still load
print(f"\n=== ALL PACKS VERIFICATION ===")
packs = discover_packs(r"J:\CORTEX\domains")
passed = 0
failed = 0
for p in packs:
    try:
        pk = load(p)
        passed += 1
    except Exception as e:
        failed += 1
        print(f"  FAIL: {os.path.basename(p)} - {e}")

print(f"Results: {passed} PASS, {failed} FAIL out of {len(packs)} packs")
if failed == 0:
    print("ALL PACKS PASS")
else:
    print("SOME PACKS FAILED")
    sys.exit(1)
