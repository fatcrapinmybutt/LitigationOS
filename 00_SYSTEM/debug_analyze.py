"""Debug: inspect analyze() return format."""
import sys, json
sys.path.insert(0, r"J:\CORTEX")
import cortex_schema as cs

pack = cs.load(r"J:\CORTEX\domains\fraud.json")
result = cs.analyze("John Smith paid $50,000 to Acme Corp on January 1, 2025. Email: j@test.com", "test.txt", pack, "all")
print("Type:", type(result))
print("Keys:", list(result.keys()) if isinstance(result, dict) else "NOT A DICT")
print()
for k, v in result.items():
    print(f"  {k}: type={type(v).__name__}, value={repr(v)[:120]}")
