import os, csv, json
from collections import Counter

OUT = r"D:\LITIGATIONOS_DATA"

# Read current stats
def count_csv(fn):
    p = os.path.join(OUT, fn)
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return sum(1 for _ in f) - 1  # minus header

cite_rows = count_csv("MASTER_CITATIONS.csv")
viol_rows = count_csv("MASTER_VIOLATIONS.csv")
time_rows = count_csv("MASTER_TIMELINE.csv")
pers_rows = count_csv("MASTER_PERSONS.csv")
evid_rows = count_csv("MASTER_EVIDENCE_INDEX.csv")

# Get unique authorities
authorities = set()
cite_types = Counter()
with open(os.path.join(OUT, "MASTER_CITATIONS.csv"), "r", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        c = row.get("citation","").strip()
        t = row.get("cite_type","").strip()
        if c:
            authorities.add(c)
            cite_types[t] += 1

# Get violation type counts
viol_types = Counter()
with open(os.path.join(OUT, "MASTER_VIOLATIONS.csv"), "r", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        vt = row.get("violation_type","").strip()
        if vt:
            viol_types[vt] += 1

# Get unique dates
dates = set()
with open(os.path.join(OUT, "MASTER_TIMELINE.csv"), "r", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        d = row.get("date","").strip()
        if d:
            dates.add(d)

# Graph stats
with open(os.path.join(OUT, "bloom_perspective.json"), "r") as f:
    bloom = json.load(f)
graph_nodes = bloom["stats"]["total_nodes"]
graph_edges = bloom["stats"]["total_edges"]

# Top 10 most-cited authorities
top_auth = Counter()
with open(os.path.join(OUT, "MASTER_CITATIONS.csv"), "r", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        c = row.get("citation","").strip()
        if c:
            top_auth[c] += 1

# Top 5 evidence files by score
top_evid = []
with open(os.path.join(OUT, "MASTER_EVIDENCE_INDEX.csv"), "r", encoding="utf-8", errors="replace") as f:
    reader = csv.DictReader(f)
    rows = []
    for row in reader:
        try:
            score = float(row.get("score","0"))
        except:
            score = 0
        rows.append((row.get("source_file",""), score))
    rows.sort(key=lambda x: x[1], reverse=True)
    top_evid = rows[:15]

md = f"""# PIGGYPIGGY ULTIMATE — LITIGATIONOS DATA DELIVERABLE
## Pigors v. Watson | 14th Judicial Circuit, Muskegon County, MI
## Case No. 2024-001507-DC | Judge Jenny L. McNeill

---

## 📊 EXTRACTION STATISTICS (REAL DATA)

| Metric | Count |
|--------|-------|
| Total citation instances | {cite_rows:,} |
| Unique legal authorities | {len(authorities):,} |
| Violation instances | {viol_rows:,} |
| Timeline events | {time_rows:,} |
| Person mentions | {pers_rows:,} |
| Evidence files scored | {evid_rows:,} |
| Graph nodes (Neo4j) | {graph_nodes:,} |
| Graph edges (Neo4j) | {graph_edges:,} |

---

## 📚 CITATION MATRIX

| Citation Type | Count |
|---------------|-------|
"""
for ct, cnt in sorted(cite_types.items(), key=lambda x: -x[1]):
    md += f"| {ct} | {cnt:,} |\n"

md += f"""
### Top 20 Most-Cited Authorities
| Authority | Mentions |
|-----------|----------|
"""
for auth, cnt in top_auth.most_common(20):
    md += f"| {auth[:80]} | {cnt:,} |\n"

md += f"""
---

## ⚠️ VIOLATION MATRIX

| Violation Type | Instances |
|----------------|-----------|
"""
for vt, cnt in sorted(viol_types.items(), key=lambda x: -x[1]):
    md += f"| {vt.replace('_',' ').title()} | {cnt:,} |\n"

md += f"""
---

## 📅 TIMELINE
- **{time_rows:,}** dated events extracted
- **{len(dates):,}** unique dates identified
- Spanning full case history

---

## 🏆 TOP 15 EVIDENCE FILES BY SCORE

| File | Score |
|------|-------|
"""
for fn, score in top_evid:
    md += f"| {os.path.basename(fn)[:60]} | {score:.0f} |\n"

md += f"""
---

## 📁 COURT FILINGS (5 COMPLETE)

| Filing | Description | Size |
|--------|-------------|------|
| B1 | Emergency Motion to Restore Parenting Time (MCR 3.207; MCL 722.27a) | 8,121 bytes |
| B2 | Motion to Modify/Terminate PPO (MCR 3.707; MCL 600.2950) | 6,309 bytes |
| B3 | Motion for Judicial Disqualification (MCR 2.003(C)) | 22,578 bytes |
| B4 | 42 USC 1983 Federal Civil Rights Complaint | 9,095 bytes |
| B5 | JTC Complaint (Canons 1, 2, 3) | 6,971 bytes |

---

## 🔗 GRAPH INTELLIGENCE

| Component | Details |
|-----------|---------|
| Neo4j Nodes CSV | {graph_nodes:,} nodes (Authority, Evidence, Person, Violation, Event) |
| Neo4j Edges CSV | {graph_edges:,} edges (CITES, DOCUMENTS, MENTIONS) |
| GraphML (Gephi) | 2.1 MB visualization-ready |
| Bloom Perspective | JSON with 6 search phrases |
| Constraints Cypher | 5 uniqueness + 6 indexes + full-text search |
| Graph Contract | YAML schema with node/edge type definitions |

---

## 📦 ALL ARTIFACTS IN D:\\LITIGATIONOS_DATA\\

"""
for fn in sorted(os.listdir(OUT)):
    fp = os.path.join(OUT, fn)
    if os.path.isfile(fp):
        sz = os.path.getsize(fp)
        if sz > 1048576:
            sz_str = f"{sz/1048576:.1f} MB"
        elif sz > 1024:
            sz_str = f"{sz/1024:.0f} KB"
        else:
            sz_str = f"{sz} bytes"
        md += f"- `{fn}` — {sz_str}\n"

md += f"""
---

## ⚖️ CASE POSTURE

**Father:** Andrew J. Pigors (Pro Se)
**Mother:** Emily Watson
**Child:** L.D.W. (born Nov 9, 2022)
**Judge:** Jenny L. McNeill
**Court:** 14th Judicial Circuit, Muskegon County, MI

**Active Case Numbers:**
- 2024-001507-DC (Custody)
- 2023-5907-PP (PPO)
- 2021-186155-CB (Primary)
- 2025-002760-CZ (New)

**Key Opposing Counsel:** Rusco
**Key Persons:** Martini, Lori Watson, Albert Watson, Dr. Richard Bone, Officer Ella Randall

**MEEK Tracks:**
- MEEK1: Housing | MEEK2: Custody/PT | MEEK3: PPO/Contempt
- MEEK4: JTC/Canon | MEEK5: Higher Courts

**Damages:** $94,250 documented / $139,750+ recovery potential
**Child Separation:** 329+ days documented

---

*Generated by LitigationOS Autopilot — All data extracted from actual evidence files*
*Source directories: C:\\Users\\andre\\Music, C:\\Users\\andre\\Scans*
"""

# Write to all locations
for p in [os.path.join(OUT, "PIGGYPIGGY_ULTIMATE.md"),
          r"D:\PIGGYPIGGY_ULTIMATE.md",
          r"C:\Users\andre\Desktop\PIGGYPIGGY_ULTIMATE.md"]:
    with open(p, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Written: {p} ({len(md):,} chars)", flush=True)

print("DONE", flush=True)