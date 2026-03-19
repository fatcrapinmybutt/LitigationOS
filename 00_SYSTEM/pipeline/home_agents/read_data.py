import csv

with open("D:/LITIGATIONOS_DATA/MASTER_CITATIONS.csv", encoding="utf-8") as f:
    r = csv.DictReader(f)
    mcr = set(); mcl = set(); cases = set()
    for row in r:
        if row["cite_type"] == "MCR": mcr.add(row["citation"])
        elif row["cite_type"] == "MCL": mcl.add(row["citation"])
        elif row["cite_type"] == "CASE_LAW": cases.add(row["citation"])
    print(f"Unique MCR: {len(mcr)}")
    print(f"Unique MCL: {len(mcl)}")
    print(f"Unique Cases: {len(cases)}")
    print("MCR:", sorted(mcr)[:15])
    print("MCL:", sorted(mcl)[:15])
    print("Cases:", sorted(cases)[:10])

print("\n--- VIOLATION SAMPLES ---")
with open("D:/LITIGATIONOS_DATA/MASTER_VIOLATIONS.csv", encoding="utf-8") as f:
    r = csv.DictReader(f)
    by_type = {}
    for row in r:
        vt = row["violation_type"]
        if vt not in by_type: by_type[vt] = []
        if len(by_type[vt]) < 2:
            by_type[vt].append(row["context"][:120])
    for vt in sorted(by_type):
        print(f"  {vt}: {by_type[vt]}")

print("\n--- DATES ---")
with open("D:/LITIGATIONOS_DATA/MASTER_TIMELINE.csv", encoding="utf-8") as f:
    r = csv.DictReader(f)
    dates = sorted(set(row["date"] for row in r))
    print(f"  {len(dates)} unique dates: {dates[:20]}")