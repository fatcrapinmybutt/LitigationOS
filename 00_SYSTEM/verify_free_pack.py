"""Verify the upgraded free pack loads and validates correctly."""
import sys, os, json
sys.path.insert(0, r"J:\CORTEX")

from cortex_schema import load as load_pack

# Test loading the upgraded pack
pack_path = r"J:\CORTEX\domains\osint.json"
try:
    domain = load_pack(pack_path)
    info = domain.info()
    print("=== PACK VALIDATION ===")
    print(f"Name:        {info.get('name', 'UNKNOWN')}")
    print(f"Version:     {info.get('version', '?')}")
    print(f"Entities:    {info.get('entity_count', 0)}")
    print(f"Categories:  {info.get('category_count', 0)}")
    print(f"Authorities: {info.get('authority_count', 0)}")
    print(f"Status:      PASS")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()

# Quick analyze test with sample text
try:
    test_text = """
    John Smith called 555-123-4567 from IP 192.168.1.100.
    Payment sent to 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD12.
    Meeting at 123 Main St, Springfield. Case No. 2024-001507-DC.
    Email: test@example.com. SSN: 123-45-6789.
    Company: Acme Corp Inc. FOIA request pending.
    """
    result = domain.analyze(test_text)
    total_entities = sum(result["entities"].values())
    print(f"\nAnalysis test: {total_entities} entities found in sample text")
    for ent_type, count in sorted(result["entities"].items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"  {ent_type}: {count}")
    print(f"Categories:  {len(result['categories'])}")
    print(f"Value Score: {result['value_score']} ({result['value_label']})")
    print(f"\nALL TESTS PASS")
except Exception as e:
    print(f"ANALYZE FAIL: {e}")
    import traceback
    traceback.print_exc()
