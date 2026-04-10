import sqlite3, json, os
DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB, timeout=60)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.row_factory = sqlite3.Row

# 1. Get police_reports schema
cols = [r[1] for r in conn.execute("PRAGMA table_info(police_reports)")]
print("police_reports columns:", cols)

# 2. Get ALL police reports
rows = conn.execute("SELECT * FROM police_reports").fetchall()
print(f"\nTotal police reports: {len(rows)}")

# 3. Analyze each for adversary connections
results = []
adversaries = {
    "Watson": ["watson","emily","defendant"],
    "Albert Watson": ["albert"],
    "McNeill": ["mcneill","judge"],
    "Berry": ["berry","ronald","cavan"],
    "Baxter": ["baxter","rachel","wren","denny","dennis"],
    "Rusco": ["rusco","pamela","tony","foc"],
    "Barnes": ["barnes","jennifer","attorney"],
}

for r in rows:
    row_text = " ".join(str(r[c] or "") for c in cols).lower()
    matched = []
    for adv, kws in adversaries.items():
        if any(kw in row_text for kw in kws):
            matched.append(adv)
    
    d = {c: r[c] for c in cols}
    d["adversaries_matched"] = matched
    results.append(d)

# 4. Summary
from collections import Counter
adv_counts = Counter()
for r in results:
    for a in r["adversaries_matched"]:
        adv_counts[a] += 1

print("\nAdversary mentions in police reports:")
for a, c in adv_counts.most_common():
    print(f"  {a}: {c} reports")

# 5. Print top reports with content
print("\n=== DETAILED REPORTS (first 500 chars each) ===")
for i, r in enumerate(results[:50]):
    content_col = None
    for c in cols:
        if r.get(c) and isinstance(r[c], str) and len(r[c]) > 100:
            content_col = c
            break
    if content_col:
        print(f"\n--- Report {i+1} ---")
        print(f"Adversaries: {r['adversaries_matched']}")
        for c in cols:
            val = r.get(c)
            if val and isinstance(val, str) and len(str(val)) > 5:
                print(f"  {c}: {str(val)[:300]}")

# 6. Save full results as JSON
out = r"D:\LitigationOS_tmp\police_reports_mapped.json"
# Convert to serializable
clean = []
for r in results:
    clean.append({k: str(v) if v is not None else None for k, v in r.items()})
with open(out, "w") as f:
    json.dump(clean, f, indent=2)
print(f"\nSaved: {out} ({len(clean)} reports)")

conn.close()
