#!/usr/bin/env python3
"""
build_filing_matrix.py — Master Evidence-to-Filing Mapping Matrix Builder
Reads the adverse evidence matrix CSV and filing inventory to produce:
  1. evidence_filing_matrix.csv — structured mapping of evidence to filings
  2. filing_dashboard.md — human-readable dashboard
"""
import sys, os, csv, json
from datetime import datetime
from collections import defaultdict
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

BASE = Path(r"C:\Users\andre\LitigationOS")
REPORTS = BASE / "00_SYSTEM" / "reports"
MATRIX_CSV = REPORTS / "adverse_evidence_matrix.csv"
OUT_CSV = REPORTS / "evidence_filing_matrix.csv"
OUT_MD = REPORTS / "filing_dashboard.md"

# ── Filing registry: canonical definition of every filing target ──────────
FILINGS = [
    {
        "filing_target": "MSC Superintending Control",
        "court_level": "Supreme",
        "case_number": "TBD (Original Action)",
        "filing_type": "petition",
        "filing_status": "draft",
        "filing_path": "01_FILINGS/MSC_ACTION/A_msc_complaint_superintending_control.md",
        "key_statutes": "MCR 7.304; Const 1963 art 6 §4; MCR 7.312",
        "defendants": "14th Circuit Court (Hon. Jenny L. McNeill)",
    },
    {
        "filing_target": "Federal 1983 WDMI",
        "court_level": "Federal District",
        "case_number": "TBD (WDMI)",
        "filing_type": "complaint",
        "filing_status": "enhanced",
        "filing_path": "01_FILINGS/FEDERAL_1983/01_COMPLAINT_1983.md",
        "key_statutes": "42 USC §§1983,1985,1986; 28 USC §1331; 28 USC §1343",
        "defendants": "Hon. Jenny L. McNeill; Tiffany A. Watson; Pamela Barnes",
    },
    {
        "filing_target": "COA 366810",
        "court_level": "Appellate",
        "case_number": "366810",
        "filing_type": "brief",
        "filing_status": "enhanced",
        "filing_path": "01_FILINGS/COA_366810/APPELLANT_BRIEF_COA_366810.md",
        "key_statutes": "MCR 7.212; MCR 7.216; MCL 722.27; MCL 722.28",
        "defendants": "Kari Watson (Appellee); Hon. Jenny L. McNeill (lower court)",
    },
    {
        "filing_target": "JTC Investigation",
        "court_level": "Administrative",
        "case_number": "N/A (Investigative)",
        "filing_type": "investigation request",
        "filing_status": "draft",
        "filing_path": "JUDICIAL_PACKET_v2026-02-10_R2/",
        "key_statutes": "Const 1963 art 6 §30; MCR 9.200-9.225; MCJC Canons 1-3",
        "defendants": "Hon. Jenny L. McNeill",
    },
    {
        "filing_target": "Shady Oaks Circuit",
        "court_level": "Trial",
        "case_number": "2025-002760-CZ",
        "filing_type": "complaint",
        "filing_status": "draft",
        "filing_path": "01_FILINGS/SHADY_OAKS_CIRCUIT/complaint_shady_oaks_circuit_court.md",
        "key_statutes": "MCL 600.601; MCL 125.2301 (MHCA); MCL 554.601 (TARA); MCL 600.2919",
        "defendants": "Shady Oaks Park MHP; Homes of America LLC; Cricklewood MHP LLC",
    },
    {
        "filing_target": "Shady Oaks Federal WDMI",
        "court_level": "Federal District",
        "case_number": "TBD (WDMI)",
        "filing_type": "complaint",
        "filing_status": "draft",
        "filing_path": "01_FILINGS/SHADY_OAKS_FEDERAL/complaint_shady_oaks_federal.md",
        "key_statutes": "42 USC §3601 (FHA); 18 USC §1961 (RICO); 28 USC §1331",
        "defendants": "Shady Oaks Park MHP; Homes of America LLC; Cricklewood MHP LLC; Kim Davis",
    },
    {
        "filing_target": "Trial 14th Circuit",
        "court_level": "Trial",
        "case_number": "2024-001507-DC",
        "filing_type": "motion",
        "filing_status": "enhanced",
        "filing_path": "01_FILINGS/COA_366810/ (custody motions via appellate record)",
        "key_statutes": "MCL 722.23 (BIC); MCL 722.27; MCR 2.119; MCR 3.206",
        "defendants": "Kari Watson",
    },
]

# ── Map adverse_evidence_matrix filing targets → our canonical targets ────
TARGET_MAP = {
    "Federal §1983 McNeill": "Federal 1983 WDMI",
    "COA Appeal": "COA 366810",
    "MSC Superintending Control": "MSC Superintending Control",
    "JTC Investigation": "JTC Investigation",
    "Circuit Court Shady Oaks": "Shady Oaks Circuit",
    "Federal Fair Housing": "Shady Oaks Federal WDMI",
    "Circuit Court Custody": "Trial 14th Circuit",
}

# ── Evidence category mapping from 'type' column in the CSV ──────────────
CATEGORY_MAP = {
    "ex parte": "ex parte",
    "due process": "due process",
    "judicial misconduct": "judicial misconduct",
    "housing violation": "housing violation",
    "bias": "bias",
    "fraud": "fraud",
    "financial harm": "financial harm",
    "retaliation": "retaliation",
    "contempt": "contempt",
    "PPO abuse": "PPO abuse",
}


def load_adverse_matrix():
    """Parse adverse_evidence_matrix.csv and aggregate counts."""
    # Structure: {(filing_target, evidence_category): {severity: count}}
    agg = defaultdict(lambda: defaultdict(int))
    total_rows = 0

    if not MATRIX_CSV.exists():
        print(f"WARNING: {MATRIX_CSV} not found, using summary data")
        return agg, 0

    with open(MATRIX_CSV, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            raw_target = row.get('filing_target', '').strip()
            raw_type = row.get('type', '').strip().lower()
            severity = row.get('severity', 'medium').strip().lower()

            canon_target = TARGET_MAP.get(raw_target, raw_target)
            canon_cat = CATEGORY_MAP.get(raw_type, raw_type)

            key = (canon_target, canon_cat)
            agg[key][severity] += 1

    return agg, total_rows


def build_matrix_csv(agg):
    """Write evidence_filing_matrix.csv."""
    rows = []
    for filing in FILINGS:
        ft = filing["filing_target"]
        categories_for_filing = sorted(
            set(cat for (t, cat) in agg if t == ft)
        )
        if not categories_for_filing:
            # Filing has no mapped evidence yet — still include it
            rows.append({
                "filing_target": ft,
                "court_level": filing["court_level"],
                "case_number": filing["case_number"],
                "filing_type": filing["filing_type"],
                "filing_status": filing["filing_status"],
                "filing_path": filing["filing_path"],
                "evidence_category": "(none mapped)",
                "evidence_count": 0,
                "severity_distribution": "",
                "key_statutes": filing["key_statutes"],
                "defendants": filing["defendants"],
            })
            continue

        for cat in categories_for_filing:
            sev = agg[(ft, cat)]
            total = sum(sev.values())
            sev_str = ",".join(
                f"{s}:{sev.get(s,0)}"
                for s in ["critical", "high", "medium", "low"]
                if sev.get(s, 0) > 0
            )
            rows.append({
                "filing_target": ft,
                "court_level": filing["court_level"],
                "case_number": filing["case_number"],
                "filing_type": filing["filing_type"],
                "filing_status": filing["filing_status"],
                "filing_path": filing["filing_path"],
                "evidence_category": cat,
                "evidence_count": total,
                "severity_distribution": sev_str,
                "key_statutes": filing["key_statutes"],
                "defendants": filing["defendants"],
            })

    cols = [
        "filing_target", "court_level", "case_number", "filing_type",
        "filing_status", "filing_path", "evidence_category",
        "evidence_count", "severity_distribution", "key_statutes", "defendants",
    ]
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    return rows


def build_dashboard(rows, agg, total_findings):
    """Write filing_dashboard.md."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Pre-compute aggregates
    filing_totals = defaultdict(int)
    for r in rows:
        filing_totals[r["filing_target"]] += r["evidence_count"]

    all_categories = sorted(set(r["evidence_category"] for r in rows if r["evidence_category"] != "(none mapped)"))
    all_targets = [f["filing_target"] for f in FILINGS]

    # Build cross-tab: cat × target
    cross = {}
    for r in rows:
        cross[(r["evidence_category"], r["filing_target"])] = r["evidence_count"]

    # Court level sort order (highest first)
    level_order = {
        "Supreme": 0, "Federal Appellate": 1, "Federal District": 2,
        "Appellate": 3, "Administrative": 4, "Trial": 5,
    }
    sorted_filings = sorted(FILINGS, key=lambda f: level_order.get(f["court_level"], 99))

    lines = []
    a = lines.append

    a(f"# Master Evidence-to-Filing Mapping Dashboard")
    a(f"")
    a(f"**Generated:** {now}  ")
    a(f"**Total adverse findings mapped:** {total_findings:,}  ")
    a(f"**Filing targets:** {len(FILINGS)}  ")
    a(f"**Evidence categories:** {len(all_categories)}  ")
    a(f"")
    a(f"---")
    a(f"")

    # ── Section 1: Filing Inventory ────────────────────────────────────
    a(f"## Section 1: Filing Inventory")
    a(f"")
    a(f"| Court Level | Filing Target | Status | Case # | Defendants | Evidence Count | Path |")
    a(f"|---|---|---|---|---|---|---|")
    for f in sorted_filings:
        ft = f["filing_target"]
        cnt = filing_totals.get(ft, 0)
        a(f"| {f['court_level']} | **{ft}** | {f['filing_status']} | {f['case_number']} | {f['defendants']} | {cnt:,} | `{f['filing_path']}` |")
    a(f"")
    grand = sum(filing_totals.values())
    a(f"**Grand total mapped findings: {grand:,}**")
    a(f"")
    a(f"---")
    a(f"")

    # ── Section 2: Evidence Coverage Matrix ────────────────────────────
    a(f"## Section 2: Evidence Coverage Matrix")
    a(f"")
    # Short labels
    short = {
        "MSC Superintending Control": "MSC",
        "Federal 1983 WDMI": "Fed §1983",
        "COA 366810": "COA",
        "JTC Investigation": "JTC",
        "Shady Oaks Circuit": "SO Circuit",
        "Shady Oaks Federal WDMI": "SO Federal",
        "Trial 14th Circuit": "Trial",
    }
    header_targets = [short.get(t, t) for t in all_targets]
    a(f"| Evidence Category | {' | '.join(header_targets)} | **Row Total** |")
    a(f"|---|{'---|' * len(all_targets)}---|")
    for cat in all_categories:
        vals = []
        row_total = 0
        for t in all_targets:
            v = cross.get((cat, t), 0)
            row_total += v
            vals.append(f"{v:,}" if v > 0 else "—")
        a(f"| **{cat}** | {' | '.join(vals)} | **{row_total:,}** |")
    # Column totals
    col_totals = []
    g = 0
    for t in all_targets:
        ct = sum(cross.get((cat, t), 0) for cat in all_categories)
        col_totals.append(f"**{ct:,}**")
        g += ct
    a(f"| **COLUMN TOTAL** | {' | '.join(col_totals)} | **{g:,}** |")
    a(f"")
    a(f"---")
    a(f"")

    # ── Section 3: Negative Connotation Summary by Defendant ──────────
    a(f"## Section 3: Negative Connotation Summary by Defendant")
    a(f"")

    defendants_detail = [
        {
            "name": "Judge Jenny L. McNeill",
            "violations": "1,127+ documented judicial violations",
            "categories": "judicial misconduct, ex parte, due process, bias, contempt",
            "targets": ["MSC Superintending Control", "Federal 1983 WDMI", "JTC Investigation", "COA 366810"],
        },
        {
            "name": "Shady Oaks Park MHP",
            "violations": "housing violations, habitability failures, retaliatory eviction",
            "categories": "housing violation, fraud, financial harm, retaliation",
            "targets": ["Shady Oaks Circuit", "Shady Oaks Federal WDMI"],
        },
        {
            "name": "Homes of America LLC",
            "violations": "corporate fraud, dissolved-entity operations, RICO predicate acts",
            "categories": "fraud, financial harm, housing violation",
            "targets": ["Shady Oaks Circuit", "Shady Oaks Federal WDMI"],
        },
        {
            "name": "Cricklewood MHP LLC",
            "violations": "shell entity, lease coercion, RICO enterprise participant",
            "categories": "fraud, financial harm",
            "targets": ["Shady Oaks Circuit", "Shady Oaks Federal WDMI"],
        },
        {
            "name": "Kim Davis",
            "violations": "individual liability, fraudulent billing, discriminatory conduct",
            "categories": "fraud, retaliation, housing violation",
            "targets": ["Shady Oaks Circuit", "Shady Oaks Federal WDMI"],
        },
        {
            "name": "Kari Watson (Tiffany A. Watson)",
            "violations": "custody adverse party, perjury, ex parte collaboration",
            "categories": "fraud, ex parte, due process",
            "targets": ["Trial 14th Circuit", "COA 366810", "Federal 1983 WDMI"],
        },
        {
            "name": "Pamela Barnes (Atty, P55406)",
            "violations": "attorney misconduct, ex parte collaboration with judge",
            "categories": "ex parte, due process, fraud",
            "targets": ["Federal 1983 WDMI", "COA 366810"],
        },
    ]

    for d in defendants_detail:
        target_labels = ", ".join(short.get(t, t) for t in d["targets"])
        a(f"### {d['name']}")
        a(f"- **Violations:** {d['violations']}")
        a(f"- **Evidence categories:** {d['categories']}")
        a(f"- **Target filings:** {target_labels}")
        a(f"")

    a(f"---")
    a(f"")

    # ── Section 4: Court Hierarchy Strategy ────────────────────────────
    a(f"## Section 4: Court Hierarchy Strategy")
    a(f"")
    a(f"*Ordered from highest court authority to lowest — maximize leverage at the top.*")
    a(f"")

    strategy = [
        ("1", "Michigan Supreme Court", "MSC Superintending Control", "MCR 7.304",
         "Original jurisdiction. Seeks order directing 14th Circuit to vacate void orders, disqualify McNeill, and reassign. Bypasses COA delay.",
         filing_totals.get("MSC Superintending Control", 0)),
        ("2", "U.S. District Court — WDMI", "Federal 1983 WDMI", "42 USC §1983 + Fair Housing + RICO",
         "Federal civil rights complaint. Damages + injunctive relief. Addresses both judicial misconduct (McNeill) AND housing violations (Shady Oaks). Jury trial demanded.",
         filing_totals.get("Federal 1983 WDMI", 0)),
        ("3", "Michigan Court of Appeals", "COA 366810", "MCR 7.212",
         "Appeal of custody orders. Challenges ex parte actions, due process violations, and improper findings. Currently pending.",
         filing_totals.get("COA 366810", 0)),
        ("4", "Judicial Tenure Commission", "JTC Investigation", "Const 1963 art 6 §30",
         "Administrative investigation into McNeill's pattern of misconduct. 86 JTC conduct patterns documented. Supports all other filings.",
         filing_totals.get("JTC Investigation", 0)),
        ("5", "Muskegon Circuit Court", "Shady Oaks Circuit", "MCL 125.2301 (MHCA)",
         "State housing complaint. Damages for habitability violations, illegal eviction, property destruction. Case 2025-002760-CZ filed.",
         filing_totals.get("Shady Oaks Circuit", 0)),
        ("6", "U.S. District Court — WDMI (Housing)", "Shady Oaks Federal WDMI", "42 USC §3601 (FHA) + RICO",
         "Federal fair housing and RICO complaint. Targets corporate fraud scheme, discriminatory practices, pattern of racketeering.",
         filing_totals.get("Shady Oaks Federal WDMI", 0)),
        ("7", "14th Circuit Court — Family Division", "Trial 14th Circuit", "MCL 722.23",
         "Custody motions. Limited utility while McNeill presides — primary strategy is to remove/reassign via MSC/COA first.",
         filing_totals.get("Trial 14th Circuit", 0)),
    ]

    a(f"| Priority | Court | Filing | Authority | Evidence | Strategy |")
    a(f"|---|---|---|---|---|---|")
    for s in strategy:
        a(f"| **{s[0]}** | {s[1]} | {s[2]} | {s[3]} | {s[5]:,} findings | {s[4]} |")
    a(f"")
    a(f"---")
    a(f"")

    # ── Section 5: Gap Analysis ────────────────────────────────────────
    a(f"## Section 5: Gap Analysis")
    a(f"")

    # Identify categories with NO evidence for certain filings
    a(f"### 5a. Evidence Categories NOT Mapped to Specific Filings")
    a(f"")
    expected_mappings = {
        "MSC Superintending Control": ["judicial misconduct", "ex parte", "due process", "bias", "contempt"],
        "Federal 1983 WDMI": ["judicial misconduct", "ex parte", "due process", "bias", "fraud", "retaliation", "financial harm"],
        "COA 366810": ["judicial misconduct", "ex parte", "due process", "bias"],
        "JTC Investigation": ["judicial misconduct", "ex parte", "due process", "bias", "retaliation"],
        "Shady Oaks Circuit": ["housing violation", "fraud", "financial harm", "retaliation", "due process"],
        "Shady Oaks Federal WDMI": ["housing violation", "fraud", "financial harm", "retaliation", "due process"],
        "Trial 14th Circuit": ["due process", "ex parte", "bias", "financial harm"],
    }
    gaps_found = False
    for ft, expected_cats in expected_mappings.items():
        missing = []
        for ec in expected_cats:
            if cross.get((ec, ft), 0) == 0:
                missing.append(ec)
        if missing:
            gaps_found = True
            a(f"- **{ft}**: missing evidence for **{', '.join(missing)}**")
    if not gaps_found:
        a(f"- ✅ All expected evidence categories are mapped to their target filings.")
    a(f"")

    a(f"### 5b. Filings That Need Additional Evidence")
    a(f"")
    for f in sorted_filings:
        ft = f["filing_target"]
        cnt = filing_totals.get(ft, 0)
        if cnt < 100:
            a(f"- ⚠️ **{ft}**: only {cnt:,} findings mapped — needs evidence enrichment")
        elif cnt < 1000:
            a(f"- 📋 **{ft}**: {cnt:,} findings mapped — adequate but could be strengthened")
        else:
            a(f"- ✅ **{ft}**: {cnt:,} findings — strong evidence base")
    a(f"")

    a(f"### 5c. Unmapped Evidence Types")
    a(f"")
    unmapped_cats = ["contempt", "PPO abuse"]
    for uc in unmapped_cats:
        total_uc = sum(cross.get((uc, t), 0) for t in all_targets)
        if total_uc == 0:
            a(f"- **{uc}**: no findings extracted yet — search `EVIDENCE_ATOMS.jsonl` and custody records for {uc} evidence")
    a(f"")

    a(f"### 5d. Cross-Filing Reinforcement Opportunities")
    a(f"")
    a(f"- JTC findings directly strengthen MSC petition (judicial misconduct → superintending control)")
    a(f"- Federal §1983 ex parte evidence also supports COA arguments (constitutional violations)")
    a(f"- Shady Oaks housing violations connect to custody harm (loss of home → loss of custody)")
    a(f"- Financial harm evidence (bond requirements, fees) supports both §1983 and COA filings")
    a(f"")

    a(f"---")
    a(f"")
    a(f"*Generated by `build_filing_matrix.py` — LitigationOS Evidence-Filing Mapper*")

    with open(OUT_MD, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))


def main():
    print(f"[build_filing_matrix] Loading adverse evidence matrix from {MATRIX_CSV}")
    agg, total = load_adverse_matrix()
    print(f"[build_filing_matrix] Loaded {total:,} raw findings across {len(agg)} (target, category) pairs")

    print(f"[build_filing_matrix] Writing evidence_filing_matrix.csv ...")
    rows = build_matrix_csv(agg)
    print(f"[build_filing_matrix] Wrote {len(rows)} rows to {OUT_CSV}")

    print(f"[build_filing_matrix] Writing filing_dashboard.md ...")
    build_dashboard(rows, agg, total)
    print(f"[build_filing_matrix] Wrote dashboard to {OUT_MD}")

    # Quick verification
    csv_size = OUT_CSV.stat().st_size
    md_size = OUT_MD.stat().st_size
    print(f"[build_filing_matrix] Verification:")
    print(f"  evidence_filing_matrix.csv : {csv_size:,} bytes, {len(rows)} rows")
    print(f"  filing_dashboard.md        : {md_size:,} bytes")
    print(f"[build_filing_matrix] DONE")


if __name__ == "__main__":
    main()
