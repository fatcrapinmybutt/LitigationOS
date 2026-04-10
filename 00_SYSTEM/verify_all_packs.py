"""Verify ALL 17 CORTEX domain packs: discover, load, analyze."""
import sys, os, json

sys.path.insert(0, r"J:\CORTEX")
import cortex_schema as cs

DOMAINS_DIR = r"J:\CORTEX\domains"
SAMPLE_TEXT = """
John Smith works at Acme Corp in New York. 
He was paid $150,000 via wire transfer on January 15, 2025.
Contact: jsmith@acme.com or (555) 123-4567.
Dr. Jane Doe, NPI #1234567890, billed CPT 99213 for phantom patient.
Sen. Bob Jones received $50,000 from SuperPAC #4421.
FARA filing shows foreign agent registration for Organization X.
Whistleblower filed qui tam under False Claims Act 31 U.S.C. 3729.
Supply chain disruption at Port of Los Angeles affecting TSMC chips.
Missing person last seen at 123 Main Street, previously known as alias "Shadow".
Insider threat detected: unauthorized USB device connected to classified workstation.
Academic misconduct: fabricated data in Table 3, ORCID 0000-0002-1234-5678.
Anti-Kickback Statute violation, Stark Law self-referral scheme.
Gerrymandering in District 7, STOCK Act violation by congressman.
"""

print("=" * 60)
print("CORTEX DOMAIN PACK VERIFICATION")
print("=" * 60)

# Discover all packs
packs = cs.discover_packs(DOMAINS_DIR)
print(f"\nDiscovered: {len(packs)} domain packs\n")

passed = 0
failed = 0

for info in sorted(packs, key=lambda x: x["name"]):
    name = info["name"]
    path = info["path"]
    try:
        pack = cs.load(path)
        result = cs.analyze(SAMPLE_TEXT, "test.txt", pack, "all")
        ent_count = sum(result.get("entities", {}).values())
        cats = result.get("categories", [])
        cat_count = len(cats) if isinstance(cats, list) else sum(cats.values())
        score = result.get("value_score", 0)
        label = result.get("value_label", "?")
        print(f"  PASS  {name:<40} ent={ent_count:<3} cat={cat_count:<3} score={score} [{label}]")
        passed += 1
    except Exception as e:
        print(f"  FAIL  {name:<40} ERROR: {e}")
        failed += 1

print(f"\n{'=' * 60}")
print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
print(f"{'=' * 60}")
