#!/usr/bin/env python3
"""
scan_adverse_evidence.py — Master Adverse Evidence Matrix Generator
Scans all LitigationOS adverse-evidence CSVs and EVIDENCE_ATOMS.jsonl,
categorizes findings by filing target / severity / type, and outputs:
  1. adverse_evidence_matrix.csv  (full row-level matrix)
  2. adverse_evidence_summary.md  (human-readable roll-up)
"""

import sys, os, csv, json, re, hashlib, io
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# ── UTF-8 safety ──────────────────────────────────────────────────────────
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

BASE = Path(r"C:\Users\andre\LitigationOS")
REPORTS = BASE / "00_SYSTEM" / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

# ── Filing target mapping ─────────────────────────────────────────────────
FILING_TARGETS = {
    "Circuit Court Custody":       "Lane A — 2024-001507-DC / 2023-5907-PP",
    "Circuit Court Shady Oaks":    "Lane B — 2025-002760-CZ",
    "Federal §1983 McNeill":       "Federal — 42 USC §1983 (judicial misconduct)",
    "Federal Fair Housing":        "Federal — Fair Housing Act (Shady Oaks)",
    "MSC Superintending Control":  "MSC — Superintending Control",
    "COA Appeal":                  "COA — Appeal",
    "JTC Investigation":           "JTC — Judicial Tenure Commission",
}

def targets_for_type(finding_type: str, topic: str = "") -> list[str]:
    """Return list of filing-target keys based on finding type and topic."""
    t = finding_type.lower()
    tp = topic.lower() if topic else ""
    targets = []

    # Judicial misconduct / bias / ex parte / contempt
    if any(k in t for k in ("judicial misconduct", "bias", "ex parte", "contempt")):
        targets += ["JTC Investigation", "MSC Superintending Control",
                     "Federal §1983 McNeill", "COA Appeal"]

    # PPO / parenting time
    if any(k in t for k in ("ppo", "parenting")) or any(k in tp for k in ("ppo", "parenting_time", "pt_exparte")):
        targets += ["COA Appeal", "MSC Superintending Control", "Federal §1983 McNeill"]

    # Housing / rent / utility / habitability / sewage
    if any(k in t for k in ("housing", "rent", "utility", "habitability", "sewage")) or \
       any(k in tp for k in ("housing", "utility", "rent", "sewage", "habitability")):
        targets += ["Circuit Court Shady Oaks", "Federal Fair Housing"]

    # Notice / service defects → ALL
    if any(k in t for k in ("notice", "service defect", "due process")) or \
       any(k in tp for k in ("service_notice", "notice_service")):
        targets += list(FILING_TARGETS.keys())

    # Retaliatory by judge
    if "retaliation" in t and "judge" in t:
        targets += ["JTC Investigation", "Federal §1983 McNeill"]
    elif "retaliation" in t and ("landlord" in t or "housing" in tp):
        targets += ["Circuit Court Shady Oaks", "Federal Fair Housing"]
    elif "retaliation" in t:
        targets += ["JTC Investigation", "Federal §1983 McNeill"]

    # Fraud
    if "fraud" in t:
        targets += ["Circuit Court Custody", "COA Appeal", "Federal §1983 McNeill"]

    # Financial harm
    if "financial" in t or "bond" in tp or "overcharge" in tp or "overbilling" in tp:
        targets += ["Circuit Court Custody", "Federal §1983 McNeill"]

    # Default: if nothing matched, assign to Circuit Court Custody + COA
    if not targets:
        targets += ["Circuit Court Custody", "COA Appeal"]

    return sorted(set(targets))


def classify_type(conduct_pattern: str, topic: str = "", text: str = "") -> str:
    """Map a conduct pattern / topic / text snippet to a finding type."""
    cp = (conduct_pattern or "").upper()
    tp = (topic or "").upper()
    tx = (text or "").upper()
    combined = f"{cp} {tp} {tx}"

    if any(k in combined for k in ("EX_PARTE", "EX PARTE")):
        return "ex parte"
    if any(k in combined for k in ("RECUSAL", "BIAS", "BIAS_SIGNAL")):
        return "bias"
    if any(k in combined for k in ("CONTEMPT", "SANCTION", "JAIL")):
        return "judicial misconduct"
    if any(k in combined for k in ("SERVICE", "NOTICE", "DEFECT")):
        return "due process"
    if any(k in combined for k in ("PPO", "PROTECTION ORDER")):
        return "judicial misconduct"
    if any(k in combined for k in ("HOUSING", "UTILITY", "RENT", "SEWAGE", "HABITABILITY", "OVERBILLING", "OVERCHARGE")):
        return "housing violation"
    if any(k in combined for k in ("PARENTING", "CUSTODY", "PT_EXPARTE")):
        return "due process"
    if any(k in combined for k in ("THREAT", "HARASSMENT", "RETALIA")):
        return "retaliation"
    if any(k in combined for k in ("FRAUD", "PERJUR")):
        return "fraud"
    if any(k in combined for k in ("MENTAL_HEALTH", "EVAL")):
        return "due process"
    if any(k in combined for k in ("BOND", "FINANCIAL")):
        return "financial harm"
    if "JUDICIAL" in combined or "MISCONDUCT" in combined:
        return "judicial misconduct"
    return "due process"


def severity_from_row(row: dict, default: str = "medium") -> str:
    """Extract or infer severity from a row dict."""
    sev = (row.get("severity") or row.get("priority_score") or "").strip()
    if sev.upper() in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        return sev.lower()
    # Infer from priority_score
    try:
        score = int(sev)
        if score >= 5000:
            return "critical"
        if score >= 1000:
            return "high"
        if score >= 100:
            return "medium"
        return "low"
    except (ValueError, TypeError):
        pass
    return default


def lane_label(lane: str, case_id: str) -> str:
    """Human-readable lane label."""
    l = (lane or "").upper()
    c = (case_id or "").upper()
    if "MEEK1" in l or "HOUSING" in l:
        return "B (Housing)"
    if "MEEK2" in l:
        return "A (Custody)"
    if "MEEK3" in l:
        return "D (PPO)"
    if "MEEK4" in l:
        return "E (Misconduct)"
    if "MEEK5" in l:
        return "F (Appellate)"
    if "001507" in c:
        return "A (Custody)"
    if "005907" in c or "5907" in c:
        return "A/D (Custody/PPO)"
    return "C (Cross-lane)"

# ── Accumulators ──────────────────────────────────────────────────────────
findings = []
fid_counter = 0

def next_id():
    global fid_counter
    fid_counter += 1
    return f"AEM_{fid_counter:06d}"

def add_finding(source_file, description, severity, finding_type, case_lane, snippet, topic=""):
    filing_targets = targets_for_type(finding_type, topic)
    for ft in filing_targets:
        findings.append({
            "finding_id": next_id(),
            "source_file": source_file,
            "description": description[:300],
            "severity": severity,
            "type": finding_type,
            "filing_target": ft,
            "case_lane": case_lane,
            "evidence_text_snippet": (snippet or "")[:500],
        })


# ══════════════════════════════════════════════════════════════════════════
# SOURCE 1: JTC_Conduct_Pattern_Table.csv
# ══════════════════════════════════════════════════════════════════════════
print("[1/8] Scanning JTC_Conduct_Pattern_Table.csv ...")
src = BASE / "JTC_Conduct_Pattern_Table.csv"
if src.exists():
    with open(src, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pattern = row.get("conduct_pattern", "")
            case_id = row.get("case_id", "")
            snippet = row.get("sample_snippet", "")
            row_count = int(row.get("row_count", "0") or "0")
            priority = int(row.get("priority_score", "0") or "0")

            if priority >= 5000:
                sev = "critical"
            elif priority >= 1000:
                sev = "high"
            elif priority >= 100:
                sev = "medium"
            else:
                sev = "low"

            ft = classify_type(pattern, text=snippet)
            cl = lane_label("", case_id)
            desc = f"JTC pattern: {pattern} ({row_count} rows, priority={priority}) — case {case_id}"
            add_finding("JTC_Conduct_Pattern_Table.csv", desc, sev, ft, cl, snippet, pattern)
    print(f"   → processed, {fid_counter} findings so far")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 2: Adverse_Rebuttal_Packet_Summary.csv
# ══════════════════════════════════════════════════════════════════════════
print("[2/8] Scanning Adverse_Rebuttal_Packet_Summary.csv ...")
src = BASE / "Adverse_Rebuttal_Packet_Summary.csv"
if src.exists():
    with open(src, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            topic = row.get("topic", "")
            case_id = row.get("case_id", "")
            lane = row.get("lane", "")
            adverse_rows = int(row.get("adverse_rows", "0") or "0")
            priority = int(row.get("priority_score", "0") or "0")

            if adverse_rows == 0:
                continue

            if priority >= 500:
                sev = "critical"
            elif priority >= 100:
                sev = "high"
            elif priority >= 20:
                sev = "medium"
            else:
                sev = "low"

            ft = classify_type("", topic)
            cl = lane_label(lane, case_id)
            desc = f"Adverse rebuttal: {topic} — {adverse_rows} adverse rows, case {case_id}, lane {lane}"
            add_finding("Adverse_Rebuttal_Packet_Summary.csv", desc, sev, ft, cl,
                        f"Topic={topic}, adverse_rows={adverse_rows}, findings_missing={row.get('findings_missing_rows','')}",
                        topic)
    print(f"   → processed, {fid_counter} findings so far")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 3: Adverse_Statement_Rebuttal_Matrix_ENHANCED.csv
# ══════════════════════════════════════════════════════════════════════════
print("[3/8] Scanning Adverse_Statement_Rebuttal_Matrix_ENHANCED.csv ...")
src = BASE / "Adverse_Statement_Rebuttal_Matrix_ENHANCED.csv"
if src.exists():
    with open(src, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            topic = row.get("topic", "")
            case_id = row.get("case_id", "")
            lane = row.get("lane", "")
            neg_stmt = row.get("negative_statement", "")
            strength = row.get("counter_evidence_strength", "")
            adv_id = row.get("adverse_id", "")
            vehicle = row.get("vehicle_hooks", "")

            sev_map = {"HIGH": "high", "MEDIUM": "medium", "LOW": "low", "CRITICAL": "critical"}
            sev = sev_map.get((strength or "").upper(), "medium")

            ft = classify_type("", topic, neg_stmt)
            cl = lane_label(lane, case_id)
            desc = f"Adverse statement {adv_id}: {topic} — {neg_stmt[:150]}"
            add_finding("Adverse_Statement_Rebuttal_Matrix_ENHANCED.csv", desc, sev, ft, cl,
                        neg_stmt[:500], topic)
    print(f"   → processed, {fid_counter} findings so far")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 4: Notice_Risk_Register.csv
# ══════════════════════════════════════════════════════════════════════════
print("[4/8] Scanning Notice_Risk_Register.csv ...")
src = BASE / "Notice_Risk_Register.csv"
if src.exists():
    with open(src, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sev_raw = (row.get("severity") or "").strip().upper()
            if sev_raw not in ("HIGH", "CRITICAL"):
                continue  # only high/critical notice risks
            topic = row.get("topic", "")
            case_id = row.get("case_id", "")
            lane = row.get("lane", "")
            snippet = row.get("snippet", "")
            audit_type = row.get("audit_event_type", "")

            ft = classify_type(audit_type, topic, snippet)
            cl = lane_label(lane, case_id)
            desc = f"Notice risk: {audit_type}/{topic} sev={sev_raw} — case {case_id}"
            add_finding("Notice_Risk_Register.csv", desc, sev_raw.lower(), ft, cl, snippet, topic)
    print(f"   → processed, {fid_counter} findings so far")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 5: Deadline_Notice_Audit_Enhanced.csv
# ══════════════════════════════════════════════════════════════════════════
print("[5/8] Scanning Deadline_Notice_Audit_Enhanced.csv ...")
src = BASE / "Deadline_Notice_Audit_Enhanced.csv"
if src.exists():
    with open(src, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sev_raw = (row.get("severity") or "").strip().upper()
            notice_risk = (row.get("notice_risk") or "").strip()
            audit_type = row.get("audit_event_type", "")
            topic = row.get("topic", "")
            case_id = row.get("case_id", "")
            lane = row.get("lane", "")
            snippet = row.get("snippet", "")

            # Include HIGH/CRITICAL or any with notice_risk=True
            if sev_raw not in ("HIGH", "CRITICAL") and notice_risk != "True":
                continue

            sev = sev_raw.lower() if sev_raw in ("HIGH", "CRITICAL") else "medium"
            ft = classify_type(audit_type, topic, snippet)
            cl = lane_label(lane, case_id)
            desc = f"Deadline audit: {audit_type}/{topic} notice_risk={notice_risk} — case {case_id}"
            add_finding("Deadline_Notice_Audit_Enhanced.csv", desc, sev, ft, cl, snippet, topic)
    print(f"   → processed, {fid_counter} findings so far")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 6: Vehicle_Proof_Obligations_Calibrated.csv
# ══════════════════════════════════════════════════════════════════════════
print("[6/8] Scanning Vehicle_Proof_Obligations_Calibrated.csv ...")
src = BASE / "Vehicle_Proof_Obligations_Calibrated.csv"
if src.exists():
    with open(src, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = (row.get("status") or "").strip().upper()
            if status in ("SATISFIED", "COMPLETE", "CLOSED"):
                continue
            vehicle_id = row.get("vehicle_id", "")
            obligation = row.get("proof_obligation", "")
            forum = row.get("forum", "")

            sev = "high" if status == "OPEN" else "medium"
            ft = classify_type(vehicle_id, "", obligation)
            cl = "A (Custody)" if "MEEK2" in vehicle_id or "MEEK3" in vehicle_id else \
                 "B (Housing)" if "MEEK1" in vehicle_id else "C (Cross-lane)"
            desc = f"Proof obligation [{status}]: {vehicle_id} — {obligation}"
            add_finding("Vehicle_Proof_Obligations_Calibrated.csv", desc, sev, ft, cl,
                        f"Forum={forum}, Status={status}", vehicle_id)
    print(f"   → processed, {fid_counter} findings so far")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 7: Continuance_Chain_Summary.csv + Proceeding_Chain_Summary.csv
# ══════════════════════════════════════════════════════════════════════════
print("[7/8] Scanning Continuance + Proceeding chains ...")
src = BASE / "Continuance_Chain_Summary.csv"
if src.exists():
    with open(src, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row.get("case_id", "")
            lane = row.get("lane", "")
            cont_rows = int(row.get("continuance_rows", "0") or "0")
            if cont_rows < 5:
                continue  # only significant continuance patterns

            sev = "critical" if cont_rows >= 100 else "high" if cont_rows >= 30 else "medium"
            cl = lane_label(lane, case_id)
            desc = f"Continuance pattern: {cont_rows} continuances — case {case_id}, lane {lane}"
            add_finding("Continuance_Chain_Summary.csv", desc, sev, "due process", cl,
                        f"Rows={cont_rows}, earliest={row.get('earliest_event','')}, latest={row.get('latest_event','')}",
                        "CONTINUANCE")

src = BASE / "Proceeding_Chain_Summary.csv"
if src.exists():
    with open(src, encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row.get("case_id", "")
            lane = row.get("issue_lane", "")
            proc_id = row.get("proceeding_id", "")
            adverse = int(row.get("adverse_rows", "0") or "0")
            notice_risk = int(row.get("notice_risk_rows", "0") or "0")
            priority = int(row.get("priority_score", "0") or "0")

            if priority < 50:
                continue

            if priority >= 5000:
                sev = "critical"
            elif priority >= 1000:
                sev = "high"
            elif priority >= 200:
                sev = "medium"
            else:
                sev = "low"

            ft = classify_type(proc_id, lane)
            cl = lane_label(lane, case_id)
            desc = f"Proceeding chain: {proc_id} — {adverse} adverse, {notice_risk} notice-risk, priority={priority}"
            add_finding("Proceeding_Chain_Summary.csv", desc, sev, ft, cl,
                        f"Adverse={adverse}, findings_missing={row.get('findings_missing_rows','')}, service_gaps={row.get('service_gap_rows','')}",
                        proc_id)
print(f"   → processed, {fid_counter} findings so far")

# ══════════════════════════════════════════════════════════════════════════
# SOURCE 8: EVIDENCE_ATOMS.jsonl  (first 1000 lines)
# ══════════════════════════════════════════════════════════════════════════
print("[8/8] Scanning EVIDENCE_ATOMS.jsonl (first 1000 lines) ...")
NEGATIVE_KW = re.compile(
    r'(?i)\b(violation|misconduct|bias|ex.?parte|fraud|contempt|threat|deny|refuse|'
    r'sanction|retaliatory|coerce|overcharge|habitability|sewage|overbilling|'
    r'muted|suspended|jail|perjury|harassment|abuse|neglect|intimidat|deprive|'
    r'unreasonable|discriminat|retaliat|corrupt|illegal|unlawful)\b'
)
src = BASE / "EVIDENCE_ATOMS.jsonl"
atom_hits = 0
if src.exists():
    with open(src, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= 1000:
                break
            line = line.strip()
            if not line:
                continue
            try:
                atom = json.loads(line)
            except json.JSONDecodeError:
                continue
            preview = atom.get("preview", "")
            doc_path = atom.get("source", {}).get("doc_path", "")
            atom_id = atom.get("evidence_atom_id", "")

            if not NEGATIVE_KW.search(preview):
                continue

            atom_hits += 1
            matches = NEGATIVE_KW.findall(preview)
            kw_str = ", ".join(set(m.lower() for m in matches))

            # Classify
            ft = classify_type("", "", preview)
            sev = "high" if any(k in kw_str for k in ("contempt", "jail", "fraud", "ex parte", "misconduct")) else "medium"

            courts = atom.get("courts_extracted", [])
            entities = atom.get("entities_guess", [])
            cl = "C (Cross-lane)"
            if any("judge" in str(e).lower() for e in entities):
                cl = "E (Misconduct)"
            elif any("housing" in kw_str for kw_str in [kw_str]):
                cl = "B (Housing)"

            desc = f"Evidence atom {atom_id}: keywords=[{kw_str}] — {doc_path}"
            add_finding("EVIDENCE_ATOMS.jsonl", desc, sev, ft, cl, preview[:500], kw_str)

    print(f"   → {atom_hits} atom hits, {fid_counter} total findings")

# ══════════════════════════════════════════════════════════════════════════
# OUTPUT 1: adverse_evidence_matrix.csv
# ══════════════════════════════════════════════════════════════════════════
print(f"\nWriting matrix CSV ({len(findings)} rows) ...")
csv_path = REPORTS / "adverse_evidence_matrix.csv"
cols = ["finding_id", "source_file", "description", "severity", "type",
        "filing_target", "case_lane", "evidence_text_snippet"]
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(findings)
print(f"   → {csv_path}")

# ══════════════════════════════════════════════════════════════════════════
# OUTPUT 2: adverse_evidence_summary.md
# ══════════════════════════════════════════════════════════════════════════
print("Writing summary markdown ...")

# Roll-up counts
by_target = defaultdict(int)
by_severity = defaultdict(int)
by_type = defaultdict(int)
by_source = defaultdict(int)
by_target_severity = defaultdict(lambda: defaultdict(int))
by_target_type = defaultdict(lambda: defaultdict(int))

for f_item in findings:
    by_target[f_item["filing_target"]] += 1
    by_severity[f_item["severity"]] += 1
    by_type[f_item["type"]] += 1
    by_source[f_item["source_file"]] += 1
    by_target_severity[f_item["filing_target"]][f_item["severity"]] += 1
    by_target_type[f_item["filing_target"]][f_item["type"]] += 1

md_path = REPORTS / "adverse_evidence_summary.md"
with open(md_path, "w", encoding="utf-8") as md:
    md.write("# Adverse Evidence Master Matrix — Summary Report\n\n")
    md.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
    md.write(f"**Total findings:** {len(findings)}  \n")
    md.write(f"**Source files scanned:** {len(by_source)}  \n\n")
    md.write("---\n\n")

    # By Filing Target
    md.write("## Findings by Filing Target\n\n")
    md.write("| Filing Target | Count | % |\n")
    md.write("|---|---|---|\n")
    for tgt in sorted(by_target, key=by_target.get, reverse=True):
        pct = 100 * by_target[tgt] / len(findings) if findings else 0
        md.write(f"| {tgt} | {by_target[tgt]:,} | {pct:.1f}% |\n")
    md.write(f"| **TOTAL** | **{len(findings):,}** | **100%** |\n\n")

    # By Severity
    md.write("## Findings by Severity\n\n")
    md.write("| Severity | Count | % |\n")
    md.write("|---|---|---|\n")
    sev_order = ["critical", "high", "medium", "low"]
    for sev in sev_order:
        if sev in by_severity:
            pct = 100 * by_severity[sev] / len(findings) if findings else 0
            md.write(f"| {sev.upper()} | {by_severity[sev]:,} | {pct:.1f}% |\n")
    md.write("\n")

    # By Type
    md.write("## Findings by Type\n\n")
    md.write("| Type | Count | % |\n")
    md.write("|---|---|---|\n")
    for tp in sorted(by_type, key=by_type.get, reverse=True):
        pct = 100 * by_type[tp] / len(findings) if findings else 0
        md.write(f"| {tp} | {by_type[tp]:,} | {pct:.1f}% |\n")
    md.write("\n")

    # By Source File
    md.write("## Findings by Source File\n\n")
    md.write("| Source File | Count |\n")
    md.write("|---|---|\n")
    for sf in sorted(by_source, key=by_source.get, reverse=True):
        md.write(f"| {sf} | {by_source[sf]:,} |\n")
    md.write("\n")

    # Cross-tab: Filing Target × Severity
    md.write("## Filing Target × Severity Cross-Tab\n\n")
    md.write("| Filing Target | Critical | High | Medium | Low |\n")
    md.write("|---|---|---|---|---|\n")
    for tgt in sorted(by_target, key=by_target.get, reverse=True):
        c = by_target_severity[tgt].get("critical", 0)
        h = by_target_severity[tgt].get("high", 0)
        m = by_target_severity[tgt].get("medium", 0)
        lo = by_target_severity[tgt].get("low", 0)
        md.write(f"| {tgt} | {c} | {h} | {m} | {lo} |\n")
    md.write("\n")

    # Cross-tab: Filing Target × Type
    md.write("## Filing Target × Type Cross-Tab\n\n")
    all_types = sorted(by_type.keys())
    md.write("| Filing Target | " + " | ".join(all_types) + " |\n")
    md.write("|---" + "|---" * len(all_types) + "|\n")
    for tgt in sorted(by_target, key=by_target.get, reverse=True):
        vals = " | ".join(str(by_target_type[tgt].get(t, 0)) for t in all_types)
        md.write(f"| {tgt} | {vals} |\n")
    md.write("\n")

    # Top 20 critical findings
    md.write("## Top 20 Critical/High-Severity Findings\n\n")
    critical_high = [f_item for f_item in findings if f_item["severity"] in ("critical", "high")]
    seen_descs = set()
    count = 0
    for f_item in critical_high:
        desc_key = f_item["description"][:100]
        if desc_key in seen_descs:
            continue
        seen_descs.add(desc_key)
        count += 1
        if count > 20:
            break
        md.write(f"### {count}. [{f_item['severity'].upper()}] {f_item['type']}\n")
        md.write(f"- **Source:** {f_item['source_file']}\n")
        md.write(f"- **Filing Target:** {f_item['filing_target']}\n")
        md.write(f"- **Lane:** {f_item['case_lane']}\n")
        md.write(f"- **Description:** {f_item['description'][:200]}\n")
        md.write(f"- **Snippet:** `{f_item['evidence_text_snippet'][:150]}`\n\n")

    md.write("---\n\n")
    md.write("*This report was auto-generated by `scan_adverse_evidence.py`.*\n")

print(f"   → {md_path}")
print(f"\n{'='*60}")
print(f"DONE — {len(findings)} total findings written.")
print(f"  CSV: {csv_path}")
print(f"  MD:  {md_path}")
print(f"{'='*60}")
