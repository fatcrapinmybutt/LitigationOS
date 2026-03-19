#!/usr/bin/env python3
"""
Forensic Judicial Analysis — Pigors v. Watson
Case No. 2024-001507-DC | 14th Circuit Court (Muskegon)
Judge Jenny L. McNeill

Queries litigation_context.db across all relevant tables, builds
pattern analysis, and outputs:
  - forensic_judicial_report.md  (human-readable)
  - forensic_judicial_analysis table in the DB
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
import textwrap
import uuid
from collections import Counter, defaultdict
from datetime import datetime

# ── constants ──────────────────────────────────────────────────────────
DB_PATH = r"C:\Users\andre\litigation_context.db"
REPORT_DIR = r"C:\Users\andre\LitigationOS\06_ANALYSIS"
REPORT_PATH = os.path.join(REPORT_DIR, "forensic_judicial_report.md")

CASE_NO = "2024-001507-DC"
JUDGE = "Jenny L. McNeill"
COURT = "14th Circuit Court, Muskegon County"
PARTIES = "Pigors v. Watson"

# severity ordering
SEV_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

# ── helpers ────────────────────────────────────────────────────────────

def _fid() -> str:
    return f"FJA-{uuid.uuid4().hex[:8].upper()}"


def _safe(val, max_len: int = 2000) -> str:
    if val is None:
        return ""
    s = str(val)
    if len(s) > max_len:
        s = s[:max_len] + "..."
    return s


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.text_factory = lambda b: b.decode("utf-8", "replace")
    return conn


def safe_query(conn: sqlite3.Connection, sql: str, params=()) -> list:
    """Execute a query wrapped in try/except; never crash."""
    try:
        cur = conn.execute(sql, params)
        return cur.fetchall()
    except Exception as exc:
        print(f"  [WARN] Query failed: {exc}", file=sys.stderr)
        return []


# ── data-collection functions ──────────────────────────────────────────

def collect_benchbook_violations(conn) -> list[dict]:
    """Merge benchbook_violation_findings + auth_benchbook_violations."""
    findings = []
    rows = safe_query(conn,
        "SELECT rowid, rule, explanation, matching_text FROM benchbook_violation_findings")
    for r in rows:
        findings.append({
            "finding_id": _fid(),
            "category": "BENCHBOOK_DEVIATION",
            "severity": "high",
            "rule": _safe(r[1]),
            "description": _safe(r[2]),
            "matching_text": _safe(r[3]),
            "evidence_citations": f"benchbook_violation_findings.rowid={r[0]}",
            "mcr_violations": _safe(r[1]),
            "date_iso": "",
            "source_table": "benchbook_violation_findings",
        })

    # auth_benchbook_violations has severity score
    rows2 = safe_query(conn,
        "SELECT id, rule, explanation, matching_text, judge, severity "
        "FROM auth_benchbook_violations")
    seen_rules = set()
    for r in rows2:
        key = (_safe(r[1]), _safe(r[2])[:80])
        if key in seen_rules:
            continue
        seen_rules.add(key)
        sev_num = r[5] if r[5] else 0
        sev = "critical" if sev_num and sev_num >= 0.8 else (
              "high" if sev_num and sev_num >= 0.5 else "medium")
        findings.append({
            "finding_id": _fid(),
            "category": "BENCHBOOK_DEVIATION",
            "severity": sev,
            "rule": _safe(r[1]),
            "description": _safe(r[2]),
            "matching_text": _safe(r[3]),
            "evidence_citations": f"auth_benchbook_violations.id={r[0]}",
            "mcr_violations": _safe(r[1]),
            "date_iso": "",
            "source_table": "auth_benchbook_violations",
        })
    return findings


def collect_chronological_misconduct(conn) -> list[dict]:
    rows = safe_query(conn, "SELECT rowid, issue, date FROM chronological_misconduct")
    findings = []
    for r in rows:
        issue_text = _safe(r[1])
        # classify
        cat = "PROCEDURAL_MISCONDUCT"
        sev = "medium"
        lower = issue_text.lower()
        if any(k in lower for k in ["ex parte", "exparte"]):
            cat = "EX_PARTE_VIOLATION"
            sev = "critical"
        elif any(k in lower for k in ["due process", "hearing", "no notice"]):
            cat = "DUE_PROCESS_VIOLATION"
            sev = "high"
        elif any(k in lower for k in ["alienat", "coaching", "withhol"]):
            cat = "ALIENATION_ENABLEMENT"
            sev = "high"
        elif any(k in lower for k in ["false", "fabricat", "perjur"]):
            cat = "CREDIBILITY_FAILURE"
            sev = "high"
        elif any(k in lower for k in ["bias", "one-sided", "prejudg"]):
            cat = "BIAS_INDICATOR"
            sev = "critical"
        elif any(k in lower for k in ["ppo", "protection order"]):
            cat = "PPO_WEAPONIZATION"
            sev = "high"
        elif any(k in lower for k in ["frivolous", "fee", "bond"]):
            cat = "ACCESS_TO_JUSTICE"
            sev = "high"

        findings.append({
            "finding_id": _fid(),
            "category": cat,
            "severity": sev,
            "description": issue_text,
            "evidence_citations": f"chronological_misconduct.rowid={r[0]}",
            "mcr_violations": "",
            "date_iso": _safe(r[2]),
            "source_table": "chronological_misconduct",
        })
    return findings


def collect_global_harms(conn) -> list[dict]:
    rows = safe_query(conn,
        "SELECT rowid, harmsviolations_text, sourcefile, ts_local "
        "FROM global_harms_violations")
    findings = []
    for r in rows:
        text = _safe(r[1])
        lower = text.lower()
        cat = "HARM_VIOLATION"
        sev = "high"
        if any(k in lower for k in ["constitution", "due process", "14th amendment"]):
            cat = "CONSTITUTIONAL_VIOLATION"
            sev = "critical"
        elif any(k in lower for k in ["child", "minor", "lincoln", "custody"]):
            cat = "CHILD_WELFARE_HARM"
            sev = "critical"
        elif any(k in lower for k in ["ppo", "false", "fabricat"]):
            cat = "FALSE_ALLEGATIONS"
            sev = "high"

        findings.append({
            "finding_id": _fid(),
            "category": cat,
            "severity": sev,
            "description": text[:500],
            "evidence_citations": f"global_harms_violations.rowid={r[0]}; source={_safe(r[2])}",
            "mcr_violations": "",
            "date_iso": _safe(r[3]),
            "source_table": "global_harms_violations",
        })
    return findings


def collect_weaponization(conn) -> list[dict]:
    rows = safe_query(conn,
        "SELECT rowid, category, fact240, authoritieshitsuggested, "
        "relief_lever, sourcefile, ts_local "
        "FROM global_weaponization "
        "WHERE category IN ('bias/muting','fee/frivolous','service/notice',"
        "'exchanges/denials','allegation-assault','allegation-drugs',"
        "'allegation-erratic','allegation-arsenic','PPO chain')")
    findings = []
    for r in rows:
        cat_map = {
            "bias/muting": "BIAS_INDICATOR",
            "fee/frivolous": "ACCESS_TO_JUSTICE",
            "service/notice": "DUE_PROCESS_VIOLATION",
            "exchanges/denials": "PARENTING_TIME_DENIAL",
            "allegation-assault": "FALSE_ALLEGATIONS",
            "allegation-drugs": "FALSE_ALLEGATIONS",
            "allegation-erratic": "FALSE_ALLEGATIONS",
            "allegation-arsenic": "FALSE_ALLEGATIONS",
            "PPO chain": "PPO_WEAPONIZATION",
        }
        wcat = _safe(r[1])
        cat = cat_map.get(wcat, "WEAPONIZATION_PATTERN")
        sev = "critical" if cat in ("BIAS_INDICATOR", "FALSE_ALLEGATIONS") else "high"

        auth = _safe(r[3])
        relief = _safe(r[4])
        mcr = auth if auth else ""

        findings.append({
            "finding_id": _fid(),
            "category": cat,
            "severity": sev,
            "description": _safe(r[2], 500),
            "evidence_citations": (
                f"global_weaponization.rowid={r[0]}; "
                f"cat={wcat}; relief={relief}; source={_safe(r[5])}"
            ),
            "mcr_violations": mcr,
            "date_iso": _safe(r[6]),
            "source_table": "global_weaponization",
        })
    return findings


def collect_evidence_quotes(conn) -> list[dict]:
    """Quotes related to judge conduct."""
    rows = safe_query(conn,
        "SELECT id, evidence_category, quote_text, quote_type, speaker, "
        "date_ref, legal_significance "
        "FROM evidence_quotes "
        "WHERE evidence_category IN ('JUDGE_ORDER','TRANSCRIPT','EX_PARTE_ORDER',"
        "'CUSTODY_ORDER') "
        "AND (quote_type IN ('RULING','JUDICIAL_STATEMENT','ORDER_DIRECTIVE',"
        "'EX_PARTE_REF','COURT_FINDING','BEST_INTEREST','IMMINENT_HARM_CLAIM'))")
    findings = []
    for r in rows:
        ecat = _safe(r[1])
        qtype = _safe(r[3])
        cat = "JUDICIAL_ACTION"
        sev = "medium"
        if qtype == "EX_PARTE_REF":
            cat = "EX_PARTE_VIOLATION"
            sev = "critical"
        elif qtype == "RULING":
            cat = "RULING_ANALYSIS"
            sev = "high"
        elif qtype == "JUDICIAL_STATEMENT":
            cat = "JUDICIAL_STATEMENT"
            sev = "high"
        elif qtype == "ORDER_DIRECTIVE":
            cat = "ORDER_DIRECTIVE"
            sev = "high"
        elif qtype == "IMMINENT_HARM_CLAIM":
            cat = "IMMINENT_HARM_CLAIM"
            sev = "critical"
        elif qtype == "BEST_INTEREST":
            cat = "BEST_INTEREST_ANALYSIS"
            sev = "high"
        elif qtype == "COURT_FINDING":
            cat = "COURT_FINDING"
            sev = "high"

        findings.append({
            "finding_id": _fid(),
            "category": cat,
            "severity": sev,
            "description": _safe(r[2], 600),
            "evidence_citations": (
                f"evidence_quotes.id={r[0]}; cat={ecat}; "
                f"speaker={_safe(r[4])}; sig={_safe(r[6])}"
            ),
            "mcr_violations": "",
            "date_iso": _safe(r[5]),
            "source_table": "evidence_quotes",
        })
    return findings


def collect_master_citations(conn) -> list[dict]:
    """Citations specifically about judicial misconduct / disqualification."""
    rows = safe_query(conn,
        "SELECT rowid, cite_type, citation, context, source_file "
        "FROM master_citations "
        "WHERE ("
        "  context LIKE '%judicial%' OR context LIKE '%disqualif%' "
        "  OR context LIKE '%canon%' OR context LIKE '%McNeill%' "
        "  OR context LIKE '%bias%' OR context LIKE '%ex parte%' "
        "  OR context LIKE '%due process%' OR context LIKE '%JTC%' "
        ") LIMIT 500")
    findings = []
    seen = set()
    for r in rows:
        cite = _safe(r[2])
        ctx = _safe(r[3], 300)
        key = (cite, ctx[:60])
        if key in seen:
            continue
        seen.add(key)

        cat = "AUTHORITY_CITATION"
        sev = "info"
        lower = ctx.lower()
        if "disqualif" in lower:
            cat = "MCR_2003_DISQUALIFICATION"
            sev = "critical"
        elif "canon" in lower:
            cat = "MCJC_CANON_VIOLATION"
            sev = "high"
        elif "ex parte" in lower:
            cat = "EX_PARTE_VIOLATION"
            sev = "critical"
        elif "bias" in lower:
            cat = "BIAS_INDICATOR"
            sev = "high"
        elif "due process" in lower:
            cat = "DUE_PROCESS_VIOLATION"
            sev = "critical"
        elif "jtc" in lower:
            cat = "JTC_STANDARD"
            sev = "high"

        findings.append({
            "finding_id": _fid(),
            "category": cat,
            "severity": sev,
            "description": f"[{_safe(r[1])}] {cite}: {ctx}",
            "evidence_citations": (
                f"master_citations.rowid={r[0]}; file={_safe(r[4])}"
            ),
            "mcr_violations": cite,
            "date_iso": "",
            "source_table": "master_citations",
        })
    return findings


def collect_md_sections(conn) -> list[dict]:
    """Filing sections discussing judicial conduct."""
    rows = safe_query(conn,
        "SELECT id, source_file, section_title, substr(content,1,600) "
        "FROM md_sections "
        "WHERE ("
        "  content LIKE '%McNeill%' OR content LIKE '%disqualif%' "
        "  OR content LIKE '%judicial misconduct%' OR content LIKE '%ex parte%' "
        "  OR section_title LIKE '%judicial%' OR section_title LIKE '%disqualif%' "
        "  OR section_title LIKE '%bias%' OR section_title LIKE '%canon%' "
        ") LIMIT 300")
    findings = []
    seen_titles = set()
    for r in rows:
        title = _safe(r[2])
        src = _safe(r[1])
        key = (src, title)
        if key in seen_titles:
            continue
        seen_titles.add(key)

        content = _safe(r[3], 500)
        lower = content.lower()
        cat = "FILING_REFERENCE"
        sev = "medium"
        if "disqualif" in lower:
            cat = "MCR_2003_DISQUALIFICATION"
            sev = "critical"
        elif "ex parte" in lower:
            cat = "EX_PARTE_VIOLATION"
            sev = "critical"
        elif "bias" in lower or "prejudg" in lower:
            cat = "BIAS_INDICATOR"
            sev = "high"
        elif "canon" in lower:
            cat = "MCJC_CANON_VIOLATION"
            sev = "high"
        elif "due process" in lower:
            cat = "DUE_PROCESS_VIOLATION"
            sev = "high"

        findings.append({
            "finding_id": _fid(),
            "category": cat,
            "severity": sev,
            "description": f"[{src}] {title}: {content[:300]}",
            "evidence_citations": f"md_sections.id={r[0]}",
            "mcr_violations": "",
            "date_iso": "",
            "source_table": "md_sections",
        })
    return findings


def collect_watsons_evidence(conn) -> list[dict]:
    """New evidence docs mentioning judge/court actions."""
    rows = safe_query(conn,
        "SELECT id, filename, substr(content,1,800) "
        "FROM watsons_evidence_docs "
        "WHERE content LIKE '%McNeill%' OR content LIKE '%order%' "
        "OR content LIKE '%ex parte%' OR content LIKE '%suspend%' "
        "OR content LIKE '%dismiss%' "
        "LIMIT 200")
    findings = []
    seen = set()
    for r in rows:
        fname = _safe(r[1])
        if fname in seen:
            continue
        seen.add(fname)

        content = _safe(r[2], 500)
        lower = content.lower()
        cat = "NEW_EVIDENCE"
        sev = "medium"
        if "ex parte" in lower:
            cat = "EX_PARTE_VIOLATION"
            sev = "critical"
        elif "suspend" in lower:
            cat = "PARENTING_TIME_SUSPENSION"
            sev = "critical"
        elif "dismiss" in lower:
            cat = "MOTION_DISMISSAL"
            sev = "high"
        elif "mcneill" in lower:
            cat = "JUDICIAL_ACTION"
            sev = "high"
        elif "bond" in lower or "frivolous" in lower:
            cat = "ACCESS_TO_JUSTICE"
            sev = "high"

        findings.append({
            "finding_id": _fid(),
            "category": cat,
            "severity": sev,
            "description": f"[{fname}] {content[:400]}",
            "evidence_citations": f"watsons_evidence_docs.id={r[0]}; file={fname}",
            "mcr_violations": "",
            "date_iso": "",
            "source_table": "watsons_evidence_docs",
        })
    return findings


def collect_alienation_tactics(conn) -> list[dict]:
    rows = safe_query(conn, "SELECT rowid, tactic, description FROM alienation_tactics")
    findings = []
    for r in rows:
        findings.append({
            "finding_id": _fid(),
            "category": "ALIENATION_TACTIC",
            "severity": "high",
            "description": f"{_safe(r[1])}: {_safe(r[2])}",
            "evidence_citations": f"alienation_tactics.rowid={r[0]}",
            "mcr_violations": "MCL 722.23(j)",
            "date_iso": "",
            "source_table": "alienation_tactics",
        })
    return findings


def collect_judicial_violations(conn) -> list[dict]:
    """judicial_violations table (may be empty; populate if rows exist)."""
    rows = safe_query(conn,
        "SELECT violation_id, judge_name, canon_number, canon_text, "
        "violation_description, evidence_refs, severity, jtc_exhibit_id "
        "FROM judicial_violations")
    findings = []
    for r in rows:
        findings.append({
            "finding_id": _safe(r[0]) or _fid(),
            "category": "JUDICIAL_VIOLATION",
            "severity": _safe(r[6]) or "high",
            "description": _safe(r[4]),
            "evidence_citations": _safe(r[5]),
            "mcr_violations": _safe(r[2]),
            "date_iso": "",
            "source_table": "judicial_violations",
        })
    return findings


def collect_global_chronology_judicial(conn) -> list[dict]:
    """Chronology entries specifically about judicial actions."""
    rows = safe_query(conn,
        "SELECT rowid, date, issue, shortfact240 "
        "FROM global_chronology "
        "WHERE shortfact240 LIKE '%McNeill%' "
        "   OR shortfact240 LIKE '%judge%' "
        "   OR shortfact240 LIKE '%ex parte%' "
        "   OR shortfact240 LIKE '%court order%' "
        "   OR shortfact240 LIKE '%dismiss%' "
        "   OR shortfact240 LIKE '%suspend%' "
        "   OR shortfact240 LIKE '%ruling%' "
        "   OR shortfact240 LIKE '%bond%' "
        "   OR shortfact240 LIKE '%frivolous%' "
        "LIMIT 500")
    findings = []
    for r in rows:
        fact = _safe(r[3], 400)
        lower = fact.lower()
        cat = "CHRONOLOGY_JUDICIAL"
        sev = "medium"
        if "ex parte" in lower:
            cat = "EX_PARTE_VIOLATION"
            sev = "critical"
        elif "suspend" in lower:
            cat = "PARENTING_TIME_SUSPENSION"
            sev = "critical"
        elif "dismiss" in lower:
            cat = "MOTION_DISMISSAL"
            sev = "high"
        elif "bond" in lower or "frivolous" in lower:
            cat = "ACCESS_TO_JUSTICE"
            sev = "high"
        elif "mcneill" in lower:
            cat = "JUDICIAL_ACTION"
            sev = "high"

        findings.append({
            "finding_id": _fid(),
            "category": cat,
            "severity": sev,
            "description": f"[{_safe(r[2])}] {fact}",
            "evidence_citations": f"global_chronology.rowid={r[0]}",
            "mcr_violations": "",
            "date_iso": _safe(r[1]),
            "source_table": "global_chronology",
        })
    return findings


# ── pattern analysis ───────────────────────────────────────────────────

def analyze_patterns(findings: list[dict]) -> dict:
    """Build aggregate pattern analysis from all findings."""
    by_cat = Counter()
    by_sev = Counter()
    by_source = Counter()
    by_cat_sev = defaultdict(Counter)
    mcr_rules = Counter()
    timeline = []

    for f in findings:
        by_cat[f["category"]] += 1
        by_sev[f["severity"]] += 1
        by_source[f["source_table"]] += 1
        by_cat_sev[f["category"]][f["severity"]] += 1
        if f["mcr_violations"]:
            for rule in f["mcr_violations"].split(";"):
                rule = rule.strip()
                if rule:
                    mcr_rules[rule] += 1
        if f["date_iso"] and f["date_iso"] not in ("", "Unknown", "None"):
            timeline.append((f["date_iso"], f["category"], f["description"][:120]))

    timeline.sort(key=lambda x: x[0])

    # key pattern groups
    due_process = [f for f in findings if f["category"] in (
        "DUE_PROCESS_VIOLATION", "EX_PARTE_VIOLATION",
        "CONSTITUTIONAL_VIOLATION")]
    bias = [f for f in findings if f["category"] in (
        "BIAS_INDICATOR", "CREDIBILITY_FAILURE")]
    alienation = [f for f in findings if f["category"] in (
        "ALIENATION_ENABLEMENT", "ALIENATION_TACTIC",
        "PARENTING_TIME_DENIAL", "PARENTING_TIME_SUSPENSION")]
    access = [f for f in findings if f["category"] in (
        "ACCESS_TO_JUSTICE", "MOTION_DISMISSAL")]
    benchbook = [f for f in findings if f["category"] == "BENCHBOOK_DEVIATION"]
    mcjc = [f for f in findings if f["category"] == "MCJC_CANON_VIOLATION"]
    disqualification = [f for f in findings if f["category"] == "MCR_2003_DISQUALIFICATION"]
    weaponization_ppo = [f for f in findings if f["category"] == "PPO_WEAPONIZATION"]
    false_allegations = [f for f in findings if f["category"] == "FALSE_ALLEGATIONS"]

    return {
        "total": len(findings),
        "by_category": dict(by_cat.most_common()),
        "by_severity": dict(by_sev.most_common()),
        "by_source": dict(by_source.most_common()),
        "by_cat_sev": {k: dict(v) for k, v in by_cat_sev.items()},
        "mcr_rules_cited": dict(mcr_rules.most_common(30)),
        "timeline": timeline[:100],
        "pattern_groups": {
            "due_process_violations": len(due_process),
            "bias_indicators": len(bias),
            "alienation_enablement": len(alienation),
            "access_to_justice": len(access),
            "benchbook_deviations": len(benchbook),
            "mcjc_canon_violations": len(mcjc),
            "mcr_2003_disqualification": len(disqualification),
            "ppo_weaponization": len(weaponization_ppo),
            "false_allegations": len(false_allegations),
        },
    }


# ── report generation ──────────────────────────────────────────────────

def generate_report(findings: list[dict], patterns: dict) -> str:
    """Generate a human-readable Markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    w = lines.append

    w(f"# Forensic Judicial Analysis Report")
    w(f"## {PARTIES} — Case No. {CASE_NO}")
    w(f"### Judge {JUDGE} | {COURT}")
    w(f"**Generated:** {now}")
    w("")
    w("---")
    w("")

    # ── Executive summary ──
    w("## 1. Executive Summary")
    w("")
    w(f"This forensic analysis examined **{patterns['total']}** findings across "
      f"**{len(patterns['by_source'])}** database tables in `litigation_context.db`.")
    w("")
    w("### Severity Distribution")
    w("| Severity | Count |")
    w("|----------|-------|")
    for sev in ["critical", "high", "medium", "low", "info"]:
        cnt = patterns["by_severity"].get(sev, 0)
        if cnt:
            w(f"| **{sev.upper()}** | {cnt} |")
    w("")

    w("### Key Pattern Groups")
    w("| Pattern | Count | Significance |")
    w("|---------|-------|-------------|")
    pg = patterns["pattern_groups"]
    labels = {
        "due_process_violations": ("Due Process / Ex Parte Violations", "Constitutional — 14th Amendment"),
        "bias_indicators": ("Bias Indicators", "MCR 2.003(C)(1) — Disqualification trigger"),
        "alienation_enablement": ("Parental Alienation Enablement", "MCL 722.23(j) — Factor J violation"),
        "access_to_justice": ("Access to Justice Barriers", "Boddie v. Connecticut — Court access right"),
        "benchbook_deviations": ("Benchbook Deviations", "SCAO Benchbook — Procedural standards"),
        "mcjc_canon_violations": ("MCJC Canon Violations", "JTC complaint basis"),
        "mcr_2003_disqualification": ("MCR 2.003 Disqualification Refs", "Mandatory disqualification"),
        "ppo_weaponization": ("PPO Weaponization Patterns", "MCL 600.2950 — Abuse of process"),
        "false_allegations": ("False Allegation Patterns", "Impeachment / Fraud on court"),
    }
    for key, (label, sig) in labels.items():
        cnt = pg.get(key, 0)
        if cnt:
            w(f"| {label} | **{cnt}** | {sig} |")
    w("")

    # ── Category breakdown ──
    w("## 2. Findings by Category")
    w("")
    for cat, cnt in sorted(patterns["by_category"].items(),
                           key=lambda x: -x[1]):
        w(f"### {cat} ({cnt} findings)")
        cat_findings = [f for f in findings if f["category"] == cat]
        # show up to 10 representative findings
        for i, f in enumerate(cat_findings[:10]):
            desc = f["description"][:250].replace("\n", " ").strip()
            sev = f["severity"].upper()
            w(f"- **[{sev}]** {desc}")
            if f["mcr_violations"]:
                w(f"  - *Authority:* {f['mcr_violations'][:150]}")
            if f["evidence_citations"]:
                w(f"  - *Source:* {f['evidence_citations'][:150]}")
        if len(cat_findings) > 10:
            w(f"- *(... {len(cat_findings) - 10} additional findings)*")
        w("")

    # ── MCR Violations ──
    w("## 3. Michigan Court Rule Violations")
    w("")
    w("| Rule | Occurrences | Significance |")
    w("|------|-------------|-------------|")
    rule_sigs = {
        "MCR 2.003": "Judicial disqualification — mandatory grounds",
        "MCR 3.207(B)": "Emergency ex parte orders require imminent-harm findings",
        "MCR 3.210(C)": "Custody modification requires evidentiary hearing",
        "MCR 2.116": "Summary disposition standards",
        "MCR 2.119": "Motion practice requirements",
        "Canon 2(B)": "Judge shall not allow relationships to influence conduct",
        "Canon 3(A)(4)": "Judge shall accord full right to be heard",
        "MCL 722.23": "Best-interest factors — all 12 must be addressed",
        "MCL 722.23(j)": "Factor J — willingness to facilitate relationship",
        "MCL 552.511b": "Child support / financial disclosure requirements",
    }
    for rule, cnt in patterns["mcr_rules_cited"].items():
        sig = ""
        for key, val in rule_sigs.items():
            if key.lower() in rule.lower():
                sig = val
                break
        w(f"| {rule} | {cnt} | {sig} |")
    w("")

    # ── Benchbook Deviations ──
    w("## 4. SCAO Benchbook Deviations")
    w("")
    bench_findings = [f for f in findings if f["category"] == "BENCHBOOK_DEVIATION"]
    # group by rule
    bench_by_rule = defaultdict(list)
    for f in bench_findings:
        bench_by_rule[f.get("rule", "Unknown")].append(f)
    for rule, items in sorted(bench_by_rule.items(),
                               key=lambda x: -len(x[1])):
        w(f"### {rule} ({len(items)} violations)")
        for item in items[:5]:
            desc = item["description"][:200].replace("\n", " ").strip()
            w(f"- {desc}")
        if len(items) > 5:
            w(f"- *(... {len(items) - 5} more)*")
        w("")

    # ── Due Process ──
    w("## 5. Due Process Violation Analysis")
    w("")
    dp = [f for f in findings if f["category"] in (
        "DUE_PROCESS_VIOLATION", "EX_PARTE_VIOLATION", "CONSTITUTIONAL_VIOLATION")]
    w(f"**Total due-process-related findings: {len(dp)}**")
    w("")
    w("Constitutional requirements under the 14th Amendment and "
      "*Mathews v. Eldridge* (1976) demand: (1) notice, (2) opportunity to be "
      "heard, and (3) a neutral decision-maker. The following patterns emerge:")
    w("")
    sub_cats = Counter(f["category"] for f in dp)
    for sc, cnt in sub_cats.most_common():
        w(f"- **{sc}**: {cnt} instances")
    w("")
    for f in dp[:15]:
        desc = f["description"][:200].replace("\n", " ").strip()
        w(f"- [{f['severity'].upper()}] {desc}")
        w(f"  - Source: {f['source_table']}")
    if len(dp) > 15:
        w(f"- *(... {len(dp) - 15} additional)*")
    w("")

    # ── Bias Indicators ──
    w("## 6. Bias Indicator Analysis")
    w("")
    bias = [f for f in findings if f["category"] in (
        "BIAS_INDICATOR", "CREDIBILITY_FAILURE")]
    w(f"**Total bias-related findings: {len(bias)}**")
    w("")
    w("Under *Caperton v. A.T. Massey Coal Co.* (2009) and MCR 2.003(C)(1), "
      "objective indicators of bias require disqualification:")
    w("")
    for f in bias[:15]:
        desc = f["description"][:200].replace("\n", " ").strip()
        w(f"- [{f['severity'].upper()}] {desc}")
    if len(bias) > 15:
        w(f"- *(... {len(bias) - 15} additional)*")
    w("")

    # ── Alienation Enablement ──
    w("## 7. Parental Alienation Enablement Patterns")
    w("")
    alien = [f for f in findings if f["category"] in (
        "ALIENATION_ENABLEMENT", "ALIENATION_TACTIC",
        "PARENTING_TIME_DENIAL", "PARENTING_TIME_SUSPENSION")]
    w(f"**Total alienation-related findings: {len(alien)}**")
    w("")
    w("Under MCL 722.23(j) (Factor J), courts must consider each parent's "
      "willingness to facilitate a close relationship with the other parent. "
      "The following patterns indicate judicial enablement of alienation:")
    w("")
    for f in alien[:20]:
        desc = f["description"][:200].replace("\n", " ").strip()
        w(f"- [{f['severity'].upper()}] {desc}")
    if len(alien) > 20:
        w(f"- *(... {len(alien) - 20} additional)*")
    w("")

    # ── PPO Weaponization ──
    w("## 8. PPO Weaponization Analysis")
    w("")
    ppo = [f for f in findings if f["category"] == "PPO_WEAPONIZATION"]
    w(f"**Total PPO weaponization findings: {len(ppo)}**")
    w("")
    for f in ppo[:10]:
        desc = f["description"][:200].replace("\n", " ").strip()
        w(f"- [{f['severity'].upper()}] {desc}")
    if len(ppo) > 10:
        w(f"- *(... {len(ppo) - 10} additional)*")
    w("")

    # ── JTC / Canon Comparison ──
    w("## 9. JTC Standards & MCJC Canon Comparison")
    w("")
    w("The Michigan Code of Judicial Conduct (MCJC) and Judicial Tenure "
      "Commission (JTC) standards require judges to:")
    w("")
    w("1. **Canon 1** — Uphold integrity and independence of the judiciary")
    w("2. **Canon 2** — Avoid impropriety and the appearance of impropriety")
    w("3. **Canon 3** — Perform duties impartially and diligently")
    w("4. **Canon 3(A)(4)** — Accord every person full right to be heard")
    w("5. **Canon 3(B)(5)** — Not initiate or consider ex parte communications")
    w("")
    canon_findings = [f for f in findings if "CANON" in f["category"] or
                      "MCJC" in f["category"] or "JTC" in f["category"]]
    w(f"**Findings implicating JTC/Canon standards: {len(canon_findings)}**")
    w("")
    for f in canon_findings[:15]:
        desc = f["description"][:200].replace("\n", " ").strip()
        w(f"- [{f['severity'].upper()}] {desc}")
    if len(canon_findings) > 15:
        w(f"- *(... {len(canon_findings) - 15} additional)*")
    w("")

    # ── Timeline ──
    w("## 10. Chronological Timeline of Judicial Actions")
    w("")
    if patterns["timeline"]:
        w("| Date | Category | Description |")
        w("|------|----------|-------------|")
        for date, cat, desc in patterns["timeline"][:60]:
            desc_clean = desc.replace("\n", " ").replace("|", "/").strip()
            w(f"| {date} | {cat} | {desc_clean} |")
    else:
        w("*(Most findings lack ISO dates; see category sections above for chronological context.)*")
    w("")

    # ── Data Sources ──
    w("## 11. Data Source Summary")
    w("")
    w("| Source Table | Findings Extracted |")
    w("|-------------|-------------------|")
    for src, cnt in sorted(patterns["by_source"].items(), key=lambda x: -x[1]):
        w(f"| {src} | {cnt} |")
    w("")

    # ── Conclusions ──
    w("## 12. Conclusions and Recommended Actions")
    w("")
    w(f"Based on **{patterns['total']}** forensic findings across "
      f"{len(patterns['by_source'])} data sources:")
    w("")
    crit = patterns["by_severity"].get("critical", 0)
    high = patterns["by_severity"].get("high", 0)
    w(f"1. **{crit} CRITICAL** and **{high} HIGH** severity findings establish "
      "a pattern of judicial conduct warranting review.")
    w(f"2. **{pg.get('due_process_violations', 0)} due-process violations** "
      "implicate constitutional protections under the 14th Amendment.")
    w(f"3. **{pg.get('benchbook_deviations', 0)} benchbook deviations** "
      "demonstrate departure from SCAO procedural standards.")
    w(f"4. **{pg.get('bias_indicators', 0)} bias indicators** "
      "support MCR 2.003(C)(1) disqualification.")
    w(f"5. **{pg.get('alienation_enablement', 0)} alienation-related findings** "
      "show judicial enablement of Factor J violations.")
    w("")
    w("### Recommended Vehicles")
    w("- **Motion to Disqualify** (MCR 2.003)")
    w("- **JTC Complaint** (MCJC Canons 1, 2, 3)")
    w("- **Court of Appeals — Interlocutory Appeal** (MCR 7.203)")
    w("- **Superintending Control** (MCR 3.302)")
    w("")
    w("---")
    w(f"*Report generated {now} by forensic_judicial_analysis.py*")
    w(f"*Database: {DB_PATH}*")

    return "\n".join(lines)


# ── DB persistence ─────────────────────────────────────────────────────

def create_results_table(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS forensic_judicial_analysis (
            finding_id   TEXT PRIMARY KEY,
            category     TEXT NOT NULL,
            severity     TEXT NOT NULL,
            description  TEXT,
            evidence_citations TEXT,
            mcr_violations TEXT,
            date_iso     TEXT,
            source_table TEXT
        )
    """)
    conn.commit()


def insert_findings(conn: sqlite3.Connection, findings: list[dict]):
    conn.execute("DELETE FROM forensic_judicial_analysis")  # idempotent
    conn.executemany(
        "INSERT OR REPLACE INTO forensic_judicial_analysis "
        "(finding_id, category, severity, description, evidence_citations, "
        " mcr_violations, date_iso, source_table) "
        "VALUES (?,?,?,?,?,?,?,?)",
        [
            (
                f["finding_id"],
                f["category"],
                f["severity"],
                f["description"][:4000],
                f["evidence_citations"][:2000],
                f["mcr_violations"][:500],
                f["date_iso"],
                f["source_table"],
            )
            for f in findings
        ],
    )
    conn.commit()


# ── main ───────────────────────────────────────────────────────────────

def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"[*] Forensic Judicial Analysis — {PARTIES}")
    print(f"[*] Database: {DB_PATH}")
    print(f"[*] Judge: {JUDGE} | Court: {COURT}")
    print()

    conn = _connect()
    all_findings: list[dict] = []

    collectors = [
        ("judicial_violations", collect_judicial_violations),
        ("benchbook_violation_findings", collect_benchbook_violations),
        ("chronological_misconduct", collect_chronological_misconduct),
        ("global_harms_violations", collect_global_harms),
        ("global_weaponization", collect_weaponization),
        ("evidence_quotes", collect_evidence_quotes),
        ("master_citations", collect_master_citations),
        ("md_sections", collect_md_sections),
        ("watsons_evidence_docs", collect_watsons_evidence),
        ("alienation_tactics", collect_alienation_tactics),
        ("global_chronology", collect_global_chronology_judicial),
    ]

    for name, fn in collectors:
        try:
            results = fn(conn)
            print(f"  [{name}] -> {len(results)} findings")
            all_findings.extend(results)
        except Exception as exc:
            print(f"  [{name}] ERROR: {exc}", file=sys.stderr)

    print(f"\n[*] Total findings collected: {len(all_findings)}")

    # ── Pattern analysis ──
    patterns = analyze_patterns(all_findings)

    # ── Generate report ──
    report_md = generate_report(all_findings, patterns)
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8", errors="replace") as fh:
        fh.write(report_md)
    print(f"[*] Report written to: {REPORT_PATH}")

    # ── Persist to DB ──
    try:
        create_results_table(conn)
        insert_findings(conn, all_findings)
        verify = safe_query(conn, "SELECT COUNT(*) FROM forensic_judicial_analysis")
        print(f"[*] Inserted {verify[0][0]} rows into forensic_judicial_analysis table")
    except Exception as exc:
        print(f"[!] DB insert error: {exc}", file=sys.stderr)

    conn.close()

    # ── Summary ──
    print("\n" + "=" * 65)
    print(f"  FORENSIC JUDICIAL ANALYSIS SUMMARY")
    print(f"  {PARTIES} | Case {CASE_NO}")
    print(f"  Judge: {JUDGE}")
    print("=" * 65)
    print(f"\n  Total Findings: {patterns['total']}")
    print(f"\n  BY SEVERITY:")
    for sev in ["critical", "high", "medium", "low", "info"]:
        cnt = patterns["by_severity"].get(sev, 0)
        if cnt:
            bar = "#" * min(cnt // 2, 40)
            print(f"    {sev.upper():10s}: {cnt:5d}  {bar}")

    print(f"\n  BY CATEGORY (top 15):")
    for cat, cnt in list(patterns["by_category"].items())[:15]:
        print(f"    {cat:40s}: {cnt:5d}")

    print(f"\n  PATTERN GROUPS:")
    for key, cnt in patterns["pattern_groups"].items():
        if cnt:
            label = key.replace("_", " ").title()
            print(f"    {label:40s}: {cnt:5d}")

    print(f"\n  TOP MCR/AUTHORITY RULES CITED:")
    for rule, cnt in list(patterns["mcr_rules_cited"].items())[:10]:
        print(f"    {rule:40s}: {cnt:5d}")

    print(f"\n  DATA SOURCES:")
    for src, cnt in patterns["by_source"].items():
        print(f"    {src:40s}: {cnt:5d}")

    print("\n" + "=" * 65)
    print(f"  Report: {REPORT_PATH}")
    print(f"  DB Table: forensic_judicial_analysis ({patterns['total']} rows)")
    print("=" * 65)


if __name__ == "__main__":
    main()
