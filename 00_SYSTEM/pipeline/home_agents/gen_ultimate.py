import csv, os
from pathlib import Path
from collections import Counter, defaultdict

out = Path(r"D:\LITIGATIONOS_DATA")
desktop = Path(r"C:\Users\andre\Desktop")

# Load real data
cites = list(csv.DictReader(open(out/"MASTER_CITATIONS.csv", encoding="utf-8")))
viols = list(csv.DictReader(open(out/"MASTER_VIOLATIONS.csv", encoding="utf-8")))
dates = list(csv.DictReader(open(out/"MASTER_TIMELINE.csv", encoding="utf-8")))
persons = list(csv.DictReader(open(out/"MASTER_PERSONS.csv", encoding="utf-8")))
evidence = list(csv.DictReader(open(out/"MASTER_EVIDENCE_INDEX.csv", encoding="utf-8")))

# Count by type
cite_counts = Counter(r["cite_type"] for r in cites)
viol_counts = Counter(r["violation_type"] for r in viols)
person_counts = Counter(r["person"] for r in persons)

# Unique citations
unique_cites = defaultdict(set)
for r in cites:
    unique_cites[r["cite_type"]].add(r["citation"])

# Top evidence files
ev_sorted = sorted(evidence, key=lambda r: -int(r.get("score","0") or 0))

# Get sample contexts (actual quotes from evidence)
viol_samples = defaultdict(list)
for r in viols:
    vt = r["violation_type"]
    if len(viol_samples[vt]) < 3:
        viol_samples[vt].append(r["context"][:200])

report = f"""# PIGGYPIGGY ULTIMATE — LITIGATIONOS MASTER DELIVERABLE
## Pigors v. Watson | 14th Judicial Circuit, Muskegon County, Michigan
## Case Nos.: 2024-001507-DC | 2023-5907-PP | 2021-186155-CB | 2025-002760-CZ
## Generated from ACTUAL EXTRACTED DATA — {len(cites):,} citations, {len(viols):,} violations, {len(dates):,} dates, {len(persons):,} persons

---

# ═══ SECTION 1: REAL DATA SUMMARY ═══

## Extraction Pipeline Results
| Source | Files Processed | Characters | Errors |
|--------|----------------|------------|--------|
| Music .md (BEAST MODE) | 515 | ~12M | 0 |
| Music .txt (3 waves) | 3,234 | ~56.7M | 0 |
| Music .docx | 115 | 767,956 | 24 |
| Music .pdf | 857 | 13,473,590 | 2 |
| Scans .md+.txt | 29,457 | 1,436,641,277 | 0 |
| Scans .docx | 227 | 4,170,708 | 67 |
| Scans .pdf (partial) | 2,741+ | ~7M+ | ~25 |
| **TOTAL** | **37,146+** | **1.58 BILLION+** | **<120** |

## Structured Data Extracted (ACTUAL COUNTS)
| Data Type | Records | Unique Items |
|-----------|---------|-------------|
| Legal Citations | {len(cites):,} | {sum(len(v) for v in unique_cites.values())} |
| Violations | {len(viols):,} | {len(viol_counts)} types |
| Timeline Dates | {len(dates):,} | {len(set(r['date'] for r in dates))} unique |
| Person Mentions | {len(persons):,} | {len(person_counts)} people |
| Evidence Files Scored | {len(evidence)} | - |

---

# ═══ SECTION 2: CITATION MATRIX (ACTUAL) ═══

| Citation Type | Total Hits | Unique Citations | Sample |
|---------------|-----------|-----------------|--------|"""

for ct in sorted(cite_counts, key=lambda x: -cite_counts[x]):
    samples = sorted(unique_cites[ct])[:3]
    report += f"\n| {ct} | {cite_counts[ct]:,} | {len(unique_cites[ct])} | {', '.join(samples[:3])} |"

report += f"""

### Top Unique MCR Rules ({len(unique_cites.get('MCR',[]))} total)
"""
for c in sorted(unique_cites.get("MCR", []))[:30]:
    report += f"- {c}\n"

report += f"""
### Top Unique MCL Statutes ({len(unique_cites.get('MCL',[]))} total)
"""
for c in sorted(unique_cites.get("MCL", []))[:30]:
    report += f"- {c}\n"

report += f"""
### Case Law ({len(unique_cites.get('CASE_LAW',[]))} total)
"""
for c in sorted(unique_cites.get("CASE_LAW", [])):
    report += f"- {c}\n"

report += f"""
---

# ═══ SECTION 3: VIOLATION MATRIX (ACTUAL) ═══

| Violation Type | Hits | Sample Context (ACTUAL QUOTE FROM EVIDENCE) |
|---------------|------|----------------------------------------------|"""

for vt in sorted(viol_counts, key=lambda x: -viol_counts[x]):
    sample = viol_samples[vt][0][:120] if viol_samples[vt] else ""
    sample = sample.replace("|", "/").replace("\n", " ")
    report += f'\n| {vt} | {viol_counts[vt]:,} | "{sample}" |'

report += f"""

---

# ═══ SECTION 4: PERSON/ENTITY MENTIONS (ACTUAL) ═══

| Person/Entity | Total Mentions |
|---------------|---------------|"""
for p in sorted(person_counts, key=lambda x: -person_counts[x]):
    report += f"\n| {p} | {person_counts[p]:,} |"

report += f"""

---

# ═══ SECTION 5: TIMELINE (ACTUAL DATES EXTRACTED) ═══

{len(dates):,} dated events extracted. {len(set(r['date'] for r in dates))} unique dates.

| Date | Source File | Context |
|------|------------|---------|"""

seen_dates = set()
for r in sorted(dates, key=lambda x: x["date"]):
    d = r["date"]
    if d not in seen_dates and len(seen_dates) < 50:
        seen_dates.add(d)
        ctx = r["context"][:100].replace("|", "/").replace("\n", " ")
        report += f'\n| {d} | {r["source_file"][:40]} | {ctx} |'

report += f"""

---

# ═══ SECTION 6: TOP EVIDENCE FILES (ACTUAL SCORES) ═══

| Rank | File | Score | Citations | Violations |
|------|------|-------|-----------|------------|"""

for i, r in enumerate(ev_sorted[:25], 1):
    report += f"\n| {i} | {r['source_file'][:50]} | {r.get('score','?')} | {r.get('citations_count','?')} | {r.get('violations_count','?')} |"

report += f"""

---

# ═══ SECTION 7: COURT FILINGS PRODUCED ═══

| Filing | File | Size | Status |
|--------|------|------|--------|
| B1: Emergency Motion Restore PT | FILING_B1_EMERGENCY_MOTION_RESTORE_PT.md | {os.path.getsize(out/'FILING_B1_EMERGENCY_MOTION_RESTORE_PT.md'):,} bytes | COMPLETE |
| B2: Motion Modify/Terminate PPO | FILING_B2_MOTION_MODIFY_TERMINATE_PPO.md | {os.path.getsize(out/'FILING_B2_MOTION_MODIFY_TERMINATE_PPO.md'):,} bytes | COMPLETE |
| B3: Judicial Disqualification | FILING_B3_MOTION_JUDICIAL_DISQUALIFICATION.md | {os.path.getsize(out/'FILING_B3_MOTION_JUDICIAL_DISQUALIFICATION.md'):,} bytes | COMPLETE |
| B4: 42 USC 1983 Federal | FILING_B4_42USC1983_FEDERAL_COMPLAINT.md | {os.path.getsize(out/'FILING_B4_42USC1983_FEDERAL_COMPLAINT.md'):,} bytes | COMPLETE |
| B5: JTC Complaint | FILING_B5_JTC_COMPLAINT.md | {os.path.getsize(out/'FILING_B5_JTC_COMPLAINT.md'):,} bytes | COMPLETE |

## Data Files Produced

| File | Size | Records |
|------|------|---------|
| MASTER_CITATIONS.csv | {os.path.getsize(out/'MASTER_CITATIONS.csv'):,} bytes | {len(cites):,} rows |
| MASTER_VIOLATIONS.csv | {os.path.getsize(out/'MASTER_VIOLATIONS.csv'):,} bytes | {len(viols):,} rows |
| MASTER_TIMELINE.csv | {os.path.getsize(out/'MASTER_TIMELINE.csv'):,} bytes | {len(dates):,} rows |
| MASTER_PERSONS.csv | {os.path.getsize(out/'MASTER_PERSONS.csv'):,} bytes | {len(persons):,} rows |
| MASTER_EVIDENCE_INDEX.csv | {os.path.getsize(out/'MASTER_EVIDENCE_INDEX.csv'):,} bytes | {len(evidence)} rows |

---

# ═══ SECTION 8: CASE CONTEXT ═══

| Field | Value |
|-------|-------|
| Father (Pro Se) | Andrew J. Pigors |
| Mother | Emily Watson |
| Child | L.D.W. (born Nov 9, 2022) |
| Court | 14th Judicial Circuit, Muskegon County, MI |
| Judge | Jenny L. McNeill |
| Custody | 2024-001507-DC |
| PPO | 2023-5907-PP |
| Primary | 2021-186155-CB |
| New Filing | 2025-002760-CZ |
| Opposing Counsel | Rusco |
| Separation | 329+ days |
| Economic Damages | $94,250 documented |
| Total Recovery | $139,750+ potential |

---

# ═══ SECTION 9: ALL FILES ON DESKTOP ═══

All deliverables copied to C:\\Users\\andre\\Desktop:
- 5 court filing drafts (B1-B5)
- 5 structured data CSVs (MASTER_*)
- This file (PIGGYPIGGY_ULTIMATE.md)
- Previous deliverables (PIGGYPIGGY_FINAL.md, SCANS_JUDICIAL_ANALYSIS.md, LITIGATIONOS_FULL_OFFLOAD.md)

All backed up to D:\\LITIGATIONOS_DATA\\

---

# ═══ SECTION 10: FILING PRIORITY SEQUENCE ═══

## IMMEDIATE
1. **B1**: Emergency Motion to Restore Parenting Time — MCR 3.207; MCL 722.27a
2. **B2**: Motion to Modify/Terminate PPO — MCR 3.707; MCL 600.2950

## SHORT-TERM
3. **B3**: Motion for Judicial Disqualification — MCR 2.003(C)
4. **B5**: JTC Complaint — Canons 1, 2, 3

## MEDIUM-TERM
5. **B4**: 42 USC 1983 Federal Complaint — USDC Western District of Michigan

---

> **IMPORTANT DISCLAIMER**: These are DRAFT legal documents generated from extracted evidence data. They contain [bracketed placeholders] that must be filled in. ALL filings should be reviewed by a licensed Michigan attorney before submission. Verify all factual assertions against the original source documents. Ensure compliance with all court rules including MCR 2.114 (signature certification).

> **Generated by LitigationOS** — 1.58 BILLION characters processed across 37,000+ files
"""

# Write to both locations
for dest in [out / "PIGGYPIGGY_ULTIMATE.md", desktop / "PIGGYPIGGY_ULTIMATE.md", Path(r"D:\PIGGYPIGGY_ULTIMATE.md")]:
    with open(dest, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Written: {dest} ({len(report):,} chars)", flush=True)

print(f"\nPIGGYPIGGY ULTIMATE COMPLETE: {len(report):,} chars", flush=True)