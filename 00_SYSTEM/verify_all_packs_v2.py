"""Verify ALL domain packs load and analyze correctly."""
import sys, os, json, traceback

sys.path.insert(0, r"J:\CORTEX")
import cortex_schema

DOMAINS_DIR = r"J:\CORTEX\domains"
TEST_CONTENT = """
John Smith met with Acme Corp on January 15, 2025 at 123 Main St.
Email: john@example.com Phone: (555) 123-4567 IP: 192.168.1.1
Case No. 2024-001507-DC MCR 2.003 MCL 722.23
$50,000 wire transfer to offshore account in Cayman Islands.
EPA violation notice for PCB contamination at 500 ppb.
FIFA match-fixing investigation found suspicious odds movement.
Form 5471 shows undisclosed BVI subsidiary with $2.3 million.
"""

packs = cortex_schema.discover_packs(DOMAINS_DIR)
print(f"Discovered: {len(packs)} packs\n")

passed = 0
failed = 0
for p in sorted(packs, key=lambda x: x["name"]):
    try:
        pack = cortex_schema.load(p["path"])
        result = cortex_schema.analyze(TEST_CONTENT, "test.txt", pack)
        ents = sum(result["entities"].values()) if result["entities"] else 0
        cats = len(result["categories"]) if result["categories"] else 0
        score = result.get("value_score", 0)
        print(f"  PASS  {pack.name:30s}  entities={ents:3d}  cats={cats:2d}  score={score:3d}")
        passed += 1
    except Exception as e:
        print(f"  FAIL  {p['name']:30s}  {e}")
        traceback.print_exc()
        failed += 1

print(f"\n{'='*60}")
print(f"TOTAL: {passed + failed} | PASS: {passed} | FAIL: {failed}")
if failed == 0:
    print("ALL PACKS VERIFIED")
else:
    print(f"WARNING: {failed} packs FAILED")
    sys.exit(1)
