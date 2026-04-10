#!/usr/bin/env python3
"""
THEMANBEARPIG v5 — SINGULARITY FORGE VISUALIZATION BUILDER
============================================================
Generates a 13-layer D3.js v7 force-directed litigation intelligence graph
with 10+ major UI upgrades over v4:

  1. SVG neon glow filter system (4 glow types per category)
  2. Glassmorphism CSS for ALL panels (backdrop-filter blur)
  3. Fuzzy search bar with `/` hotkey
  4. Right-click context menu (7 actions)
  5. Keyboard shortcuts (/, f, l, r, e, ?, Escape)
  6. Real-time stats panel with FPS counter
  7. Threat level gauge (0-10 color gradient)
  8. Separation day counter (pulsing, urgent)
  9. Minimap with viewport indicator (200x200 canvas)
  10. Export (PNG, JSON)
  11. Help overlay
  12. Enhanced force physics
  13. Link particles (animated flowing dots)

Architecture: Python layer functions → cross_layer_links → HTML template
with __MARKER__ replacement (NOT f-strings — JS braces conflict).

Output: 12_WORKSPACE/ADVERSARY_NETWORK_BLUEPRINT.html
"""
import json
import os
import re
import sqlite3
import sys
from datetime import date, datetime

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUTPUT_HTML = r"C:\Users\andre\LitigationOS\12_WORKSPACE\ADVERSARY_NETWORK_BLUEPRINT.html"
BUILD_DIR = r"D:\LitigationOS_tmp\blueprint_build"

SEPARATION_DATE = date(2025, 7, 29)

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn

# ─── LAYER COLORS ────────────────────────────────────────────────────────────
LAYER_COLORS = {
    "adversary":     "#ff2244",
    "authority":     "#00ccff",
    "filing":        "#00ff88",
    "lanes":         "#ffaa00",
    "evidence":      "#ff66ff",
    "system":        "#8888ff",
    "fred":          "#ff8800",
    "meek":          "#00ffcc",
    "event_horizon": "#ff00ff",
    "brains":        "#aaaaff",
    "weapons":       "#ff4444",
    "police":        "#ffcc00",
    "doctrine":      "#44ffaa",
}

GLOW_CATEGORY = {
    "adversary": "glow-red", "weapons": "glow-red", "police": "glow-red",
    "authority": "glow-cyan", "doctrine": "glow-cyan", "filing": "glow-cyan",
    "evidence": "glow-purple", "event_horizon": "glow-purple", "brains": "glow-purple",
    "lanes": "glow-gold", "system": "glow-gold", "fred": "glow-gold", "meek": "glow-gold",
}


# ═══════════════════════════════════════════════════════════════════════════════
#  LAYER FUNCTIONS — Each returns (nodes, links)
# ═══════════════════════════════════════════════════════════════════════════════

def layer_adversary(conn):
    """Adversary family network — 7 clusters, hardcoded profiles + DB enrichment."""
    nodes, links = [], []
    families = {
        "Watson Family": [
            {"id": "emily_watson", "label": "Emily A. Watson", "role": "Defendant", "desc": "Mother — defendant in custody. Escalating false allegations pattern. Meth admission (Officer Randall).", "size": 18, "threat": 9.5},
            {"id": "albert_watson", "label": "Albert Watson", "role": "Emily's Father", "desc": "Admitted reports used for ex parte custody leverage (NS2505044). Kitchen recording.", "size": 14, "threat": 8.0},
            {"id": "lori_watson", "label": "Lori Watson", "role": "Emily's Mother", "desc": "Supports Emily's false allegations. Present during key incidents.", "size": 10, "threat": 5.0},
            {"id": "ronald_berry", "label": "Ronald Berry", "role": "Emily's Boyfriend", "desc": "NON-ATTORNEY providing legal assistance. Lives at 2160 Garland Dr. Related to Cavan Berry.", "size": 13, "threat": 7.5},
        ],
        "Judicial Cartel": [
            {"id": "mcneill", "label": "Hon. Jenny L. McNeill", "role": "Judge — 14th Circuit", "desc": "3,697 ex parte violations. Former partner: Ladas, Hoopes & McNeill. Spouse: Cavan Berry.", "size": 20, "threat": 10.0},
            {"id": "hoopes", "label": "Hon. Kenneth Hoopes", "role": "Chief Judge — 14th Circuit", "desc": "Former law partner of McNeill. Dismissed housing case (B) with prejudice.", "size": 16, "threat": 8.5},
            {"id": "ladas_hoopes", "label": "Hon. Maria Ladas-Hoopes", "role": "Judge — 60th District", "desc": "Former law partner of McNeill. Wife of Chief Judge Hoopes. Criminal case.", "size": 14, "threat": 7.0},
            {"id": "cavan_berry", "label": "Cavan Berry", "role": "Atty Magistrate — 60th Dist", "desc": "McNeill's spouse. Office: 990 Terrace St = FOC address. Berry family connection.", "size": 12, "threat": 6.5},
        ],
        "FOC / Court Staff": [
            {"id": "rusco", "label": "Pamela Rusco", "role": "Friend of Court", "desc": "FOC at 990 Terrace St (same as Cavan Berry). Systemic bias toward Emily.", "size": 14, "threat": 7.5},
            {"id": "foc_office", "label": "FOC Office", "role": "990 Terrace St", "desc": "FOC office shares address with Cavan Berry (McNeill spouse). Structural conflict.", "size": 8, "threat": 5.0},
        ],
        "Legal Counsel": [
            {"id": "barnes", "label": "Jennifer Barnes P55406", "role": "Former Attorney — WITHDREW", "desc": "Emily's attorney. WITHDREW March 2026. Emily now unrepresented.", "size": 10, "threat": 3.0},
        ],
        "Law Enforcement": [
            {"id": "nspd", "label": "NSPD", "role": "North Shores PD", "desc": "9 cases, ZERO arrests. Officer Randall: Emily admitted meth use.", "size": 10, "threat": 2.0},
            {"id": "officer_randall", "label": "Officer Randall", "role": "NSPD Officer", "desc": "Documented Emily's meth use admission. Key witness.", "size": 8, "threat": 1.0},
        ],
        "Property": [
            {"id": "shady_oaks", "label": "Shady Oaks MHP", "role": "Mobile Home Park", "desc": "Housing case Lane B. Eviction, utility abuse, title interference.", "size": 10, "threat": 4.0},
        ],
        "Victim": [
            {"id": "andrew", "label": "Andrew J. Pigors", "role": "Plaintiff (Pro Se)", "desc": "Father. 59 days jailed. Lost 2 homes, 2 jobs. Separated from L.D.W.", "size": 16, "threat": 0},
            {"id": "ldw", "label": "L.D.W.", "role": "Minor Child", "desc": "DOB Nov 9, 2022. Separated from father since Jul 29, 2025.", "size": 12, "threat": 0},
        ],
    }

    for family, members in families.items():
        for m in members:
            nodes.append({
                "id": m["id"], "label": m["label"], "layer": "adversary",
                "group": family, "role": m["role"], "desc": m["desc"],
                "color": LAYER_COLORS["adversary"], "size": m["size"],
                "threat": m.get("threat", 5),
            })

    # Family internal links
    family_links = [
        ("emily_watson", "albert_watson", "father-daughter"),
        ("emily_watson", "lori_watson", "mother-daughter"),
        ("emily_watson", "ronald_berry", "romantic-partner"),
        ("emily_watson", "barnes", "attorney-client"),
        ("emily_watson", "andrew", "opposing-party"),
        ("emily_watson", "ldw", "mother"),
        ("andrew", "ldw", "father"),
        ("mcneill", "cavan_berry", "spouse"),
        ("mcneill", "hoopes", "former-law-partner"),
        ("mcneill", "ladas_hoopes", "former-law-partner"),
        ("hoopes", "ladas_hoopes", "married-couple"),
        ("cavan_berry", "ronald_berry", "Berry-family"),
        ("rusco", "foc_office", "employed-at"),
        ("cavan_berry", "foc_office", "office-at-same-address"),
        ("emily_watson", "rusco", "FOC-bias"),
        ("emily_watson", "nspd", "false-reports-to"),
        ("albert_watson", "nspd", "premeditation-report"),
        ("andrew", "shady_oaks", "tenant"),
    ]
    for src, tgt, rel in family_links:
        links.append({
            "source": src, "target": tgt, "type": rel,
            "color": "#ff224488", "layer": "adversary",
        })

    return nodes, links


def layer_authority(conn):
    """Top authorities from authority_chains_v2."""
    nodes, links = [], []
    try:
        rows = conn.execute("""
            SELECT primary_citation, COUNT(*) as cnt
            FROM authority_chains_v2
            GROUP BY primary_citation
            ORDER BY cnt DESC LIMIT 30
        """).fetchall()
        for r in rows:
            cit = r["primary_citation"] or "Unknown"
            nodes.append({
                "id": f"auth_{cit[:40].replace(' ','_')}", "label": cit[:50],
                "layer": "authority", "group": "authority",
                "desc": f"Cited {r['cnt']} times in authority chains",
                "color": LAYER_COLORS["authority"], "size": min(5 + r["cnt"] // 50, 16),
            })
        # Co-citation links (shared source_document)
        auth_docs = {}
        try:
            for r in conn.execute("""
                SELECT primary_citation, source_document FROM authority_chains_v2
                WHERE source_document IS NOT NULL LIMIT 5000
            """):
                doc = r["source_document"]
                cit = r["primary_citation"]
                if doc and cit:
                    auth_docs.setdefault(doc, set()).add(cit[:40].replace(' ', '_'))
        except Exception:
            pass
        seen = set()
        for doc, cits in auth_docs.items():
            clist = list(cits)[:5]
            for i in range(len(clist)):
                for j in range(i + 1, len(clist)):
                    pair = tuple(sorted([clist[i], clist[j]]))
                    if pair not in seen:
                        seen.add(pair)
                        links.append({
                            "source": f"auth_{clist[i]}", "target": f"auth_{clist[j]}",
                            "type": "co-citation", "color": "#00ccff44",
                            "layer": "authority",
                        })
                    if len(links) > 60:
                        break
                if len(links) > 60:
                    break
            if len(links) > 60:
                break
    except Exception as e:
        print(f"  [WARN] authority layer: {e}")
    return nodes, links


def layer_filing(conn):
    """Filing packages F1-F10 + special filings."""
    nodes, links = [], []
    filings = [
        ("F1", "Emergency Motion to Restore", "FILED 3/25/2026"),
        ("F2", "MSC Superintending Control", "Drafting"),
        ("F3", "MCR 2.003 Disqualification", "30-day target"),
        ("F4", "MSC Mandamus", "30-day target"),
        ("F5", "COA Brief 366810", "Due Apr 15"),
        ("F6", "Habeas Corpus", "60-day target"),
        ("F7", "Federal §1983", "Drafting"),
        ("F8", "JTC Complaint", "Active"),
        ("F9", "PPO Termination", "Active"),
        ("F10", "Contempt Motion", "Pending"),
        ("F-VAC", "Vacate Judgment", "Research"),
        ("F-MSC2", "MSC Original Action", "Nuclear option"),
    ]
    for fid, name, status in filings:
        nodes.append({
            "id": f"filing_{fid}", "label": f"{fid}: {name}",
            "layer": "filing", "group": "filing",
            "desc": f"Status: {status}", "color": LAYER_COLORS["filing"],
            "size": 10, "status": status,
        })
    # Sequential dependencies
    for i in range(len(filings) - 1):
        if i < 10:
            links.append({
                "source": f"filing_{filings[i][0]}", "target": f"filing_{filings[i+1][0]}",
                "type": "filing-sequence", "color": "#00ff8833", "layer": "filing",
            })
    return nodes, links


def layer_lanes(conn):
    """6 case lanes (A-F) + CRIMINAL."""
    nodes, links = [], []
    lanes_data = [
        ("A", "Custody", "2024-001507-DC", "14th Circuit — McNeill", "#ff6644"),
        ("B", "Housing", "2025-002760-CZ", "14th Circuit — Hoopes (DISMISSED)", "#ffaa00"),
        ("C", "Federal", "TBD", "USDC Western District MI", "#4488ff"),
        ("D", "PPO", "2023-5907-PP", "14th Circuit — McNeill", "#ff44ff"),
        ("E", "Misconduct", "MULTI", "JTC / MSC", "#ff8800"),
        ("F", "Appellate", "COA 366810", "MI Court of Appeals", "#00ddff"),
        ("CRIM", "Criminal", "2025-25245676SM", "60th District — Kostrzewa", "#ff0000"),
    ]
    for lid, name, case_num, court, color in lanes_data:
        ev_count = 0
        try:
            if lid != "CRIM":
                r = conn.execute(
                    "SELECT COUNT(*) as c FROM evidence_quotes WHERE lane = ?", (lid,)
                ).fetchone()
                ev_count = r["c"] if r else 0
        except Exception:
            pass
        nodes.append({
            "id": f"lane_{lid}", "label": f"Lane {lid}: {name}",
            "layer": "lanes", "group": "lanes",
            "desc": f"{case_num} | {court} | {ev_count:,} evidence items",
            "color": color, "size": max(8, min(14, 6 + ev_count // 10000)),
        })
    return nodes, links


def layer_evidence(conn):
    """Evidence density nodes — top categories and sources."""
    nodes, links = [], []
    try:
        rows = conn.execute("""
            SELECT category, lane, COUNT(*) as cnt
            FROM evidence_quotes
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category, lane
            HAVING cnt >= 100
            ORDER BY cnt DESC LIMIT 35
        """).fetchall()
        for r in rows:
            cat = r["category"]
            lane = r["lane"] or "?"
            nid = f"ev_{cat}_{lane}".replace(" ", "_")[:50]
            nodes.append({
                "id": nid, "label": f"{cat} ({lane})",
                "layer": "evidence", "group": f"evidence-{lane}",
                "desc": f"{r['cnt']:,} quotes in Lane {lane}",
                "color": LAYER_COLORS["evidence"],
                "size": min(5 + r["cnt"] // 500, 14),
            })
    except Exception as e:
        print(f"  [WARN] evidence layer: {e}")
    return nodes, links


def layer_system(conn):
    """LitigationOS engine nodes."""
    nodes, links = [], []
    engines = [
        ("nexus", "Cross-table evidence fusion"),
        ("chimera", "Multi-source evidence blending"),
        ("chronos", "Timeline construction"),
        ("cerberus", "Filing validation"),
        ("filing_engine", "Filing pipeline F1-F10"),
        ("intake", "Document intake / PDF processing"),
        ("rebuttal", "Argument rebuttal generation"),
        ("narrative", "Court-ready Statement of Facts"),
        ("delta999", "8 specialized litigation agents"),
        ("analytics", "DuckDB 10-100x analytical queries"),
        ("semantic", "LanceDB 75K vector semantic search"),
        ("search", "tantivy hybrid multi-backend search"),
        ("typst", "Court-ready PDF generation"),
        ("ingest", "Go 8-worker goroutine file processing"),
        ("perception", "Legal-BERT INT8 classification"),
        ("hypergraph", "Cross-lane evidence hypergraph"),
    ]
    for eid, desc in engines:
        nodes.append({
            "id": f"eng_{eid}", "label": eid.upper(),
            "layer": "system", "group": "system",
            "desc": desc, "color": LAYER_COLORS["system"], "size": 8,
        })
    # Engine interconnections
    engine_links = [
        ("nexus", "semantic"), ("nexus", "analytics"), ("nexus", "search"),
        ("chimera", "nexus"), ("chronos", "narrative"), ("cerberus", "filing_engine"),
        ("intake", "ingest"), ("delta999", "nexus"), ("perception", "semantic"),
        ("analytics", "search"), ("hypergraph", "nexus"),
    ]
    for s, t in engine_links:
        links.append({
            "source": f"eng_{s}", "target": f"eng_{t}",
            "type": "engine-link", "color": "#8888ff33", "layer": "system",
        })
    return nodes, links


def layer_fred(conn):
    """FRED governance system."""
    nodes, links = [], []
    fred_nodes = [
        ("fred_core", "FRED Core", "Filing Readiness & Evidence Dashboard", 12),
        ("fred_qc", "FRED QC", "Quality control gate", 8),
        ("fred_deadline", "FRED Deadlines", "Deadline tracking engine", 8),
        ("fred_service", "FRED Service", "Service proof tracker", 8),
        ("fred_compliance", "FRED Compliance", "MCR compliance validator", 8),
        ("fred_egcp", "FRED EGCP", "Evidence/Grounds/Citations/Presentation scorer", 10),
    ]
    for nid, label, desc, size in fred_nodes:
        nodes.append({
            "id": nid, "label": label, "layer": "fred", "group": "fred",
            "desc": desc, "color": LAYER_COLORS["fred"], "size": size,
        })
    for nid, _, _, _ in fred_nodes[1:]:
        links.append({
            "source": "fred_core", "target": nid,
            "type": "fred-subsystem", "color": "#ff880033", "layer": "fred",
        })
    return nodes, links


def layer_meek(conn):
    """MEEK lane routing signals."""
    nodes, links = [], []
    meek_signals = [
        ("MEEK1", "Housing Signal", "Shady Oaks, eviction, housing, trailer", "B"),
        ("MEEK2", "Custody Signal", "Custody, parenting, 001507, Watson, child", "A"),
        ("MEEK3", "PPO Signal", "PPO, protection order, 5907, contempt", "D"),
        ("MEEK4", "Misconduct Signal", "McNeill, judicial, bias, JTC, ex parte", "E"),
        ("MEEK5", "Appellate Signal", "COA, 366810, appeal, brief", "F"),
    ]
    for mid, label, desc, lane in meek_signals:
        nodes.append({
            "id": f"meek_{mid}", "label": f"{mid}: {label}",
            "layer": "meek", "group": "meek",
            "desc": f"Routes to Lane {lane}. Keywords: {desc}",
            "color": LAYER_COLORS["meek"], "size": 10,
        })
        links.append({
            "source": f"meek_{mid}", "target": f"lane_{lane}",
            "type": "meek-route", "color": "#00ffcc44", "layer": "meek",
        })

    # MEEK detection stats from DB
    try:
        for mid, _, _, lane in meek_signals:
            r = conn.execute(
                "SELECT COUNT(*) as c FROM evidence_quotes WHERE lane = ?", (lane,)
            ).fetchone()
            if r:
                for n in nodes:
                    if n["id"] == f"meek_{mid}":
                        n["desc"] += f" | {r['c']:,} items routed"
    except Exception:
        pass
    return nodes, links


def layer_event_horizon(conn):
    """Event Horizon state tracking."""
    nodes, links = [], []
    eh_nodes = [
        ("eh_core", "Event Horizon Δ∞", "Master state machine — 50+ WAL files", 14),
        ("eh_wal", "WAL Engine", "Write-Ahead Log persistence", 8),
        ("eh_convergence", "Convergence Tracker", "105 domains, 10 waves, 37 todos", 10),
        ("eh_emergence", "Emergence Scanner", "Cross-lane intelligence detection", 10),
        ("eh_gap", "Gap Tracker", "BLOCKERs, ΔNEW, deferred patches", 8),
        ("eh_mutations", "State Mutations", "Pipeline state transitions", 8),
    ]
    for nid, label, desc, size in eh_nodes:
        nodes.append({
            "id": nid, "label": label, "layer": "event_horizon", "group": "event_horizon",
            "desc": desc, "color": LAYER_COLORS["event_horizon"], "size": size,
        })
    for nid, _, _, _ in eh_nodes[1:]:
        links.append({
            "source": "eh_core", "target": nid,
            "type": "eh-subsystem", "color": "#ff00ff33", "layer": "event_horizon",
        })
    return nodes, links


def layer_brains(conn):
    """Brain network — 23+ registered brains."""
    nodes, links = [], []
    brains = [
        "interpretation", "narrative", "authority", "knowledge", "evidence",
        "timeline", "judicial", "filing", "compliance", "adversary",
        "weapons", "police", "cross_exam", "impeachment", "contradiction",
        "prediction", "convergence", "forms", "citations", "rules",
    ]
    for b in brains:
        size = 6 + hash(b) % 6
        nodes.append({
            "id": f"brain_{b}", "label": f"🧠 {b.title()}",
            "layer": "brains", "group": "brains",
            "desc": f"Brain DB: {b}_brain.db",
            "color": LAYER_COLORS["brains"], "size": size,
        })
    # Brain interconnections (knowledge flow)
    brain_links = [
        ("evidence", "impeachment"), ("evidence", "contradiction"),
        ("timeline", "narrative"), ("authority", "citations"),
        ("judicial", "adversary"), ("filing", "compliance"),
        ("weapons", "adversary"), ("cross_exam", "impeachment"),
        ("prediction", "convergence"), ("rules", "authority"),
        ("knowledge", "evidence"), ("knowledge", "authority"),
    ]
    for s, t in brain_links:
        links.append({
            "source": f"brain_{s}", "target": f"brain_{t}",
            "type": "brain-flow", "color": "#aaaaff33", "layer": "brains",
        })
    return nodes, links


def layer_weapons(conn):
    """Weapon chains — adversary → weapon → effect → doctrine."""
    nodes, links = [], []
    weapon_types = [
        "FALSE_ALLEGATION", "EX_PARTE", "PARENTING_DENIAL",
        "CONTEMPT_ABUSE", "PPO_WEAPONIZATION", "JUDICIAL_BIAS",
        "EVIDENCE_SUPPRESSION", "PARENTAL_ALIENATION", "DUE_PROCESS_VIOLATION",
    ]
    for wt in weapon_types:
        nodes.append({
            "id": f"weapon_{wt}", "label": wt.replace("_", " ").title(),
            "layer": "weapons", "group": "weapons",
            "desc": f"Weapon type: {wt}", "color": LAYER_COLORS["weapons"], "size": 12,
        })

    # Aggregate from DB
    try:
        rows = conn.execute("""
            SELECT category, COUNT(*) as cnt, MAX(impeachment_value) as max_iv
            FROM impeachment_matrix
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY cnt DESC LIMIT 15
        """).fetchall()
        for r in rows:
            cat = (r["category"] or "unknown")[:30]
            nid = f"wpn_{cat.replace(' ','_')}"
            nodes.append({
                "id": nid, "label": f"⚔ {cat}",
                "layer": "weapons", "group": "weapon-instance",
                "desc": f"{r['cnt']} items, max severity: {r['max_iv']}",
                "color": "#ff6644", "size": min(6 + r["cnt"] // 50, 14),
            })
    except Exception as e:
        print(f"  [WARN] weapons layer: {e}")

    # Weapon → adversary links
    weapon_adversary = [
        ("FALSE_ALLEGATION", "emily_watson"), ("EX_PARTE", "mcneill"),
        ("PARENTING_DENIAL", "emily_watson"), ("CONTEMPT_ABUSE", "mcneill"),
        ("PPO_WEAPONIZATION", "emily_watson"), ("JUDICIAL_BIAS", "mcneill"),
        ("EVIDENCE_SUPPRESSION", "mcneill"), ("PARENTAL_ALIENATION", "emily_watson"),
        ("DUE_PROCESS_VIOLATION", "mcneill"),
    ]
    for wt, adv in weapon_adversary:
        links.append({
            "source": f"weapon_{wt}", "target": adv,
            "type": "weapon-wielded-by", "color": "#ff444466", "layer": "weapons",
        })
    return nodes, links


def layer_police(conn):
    """Police reports and incidents."""
    nodes, links = [], []
    try:
        rows = conn.execute("""
            SELECT report_number, date, summary
            FROM police_reports
            ORDER BY date DESC LIMIT 25
        """).fetchall()
        cols = [d[0] for d in conn.execute("PRAGMA table_info(police_reports)").fetchall()]
    except Exception:
        cols = []
        rows = []

    if not rows:
        try:
            rows = conn.execute("""
                SELECT * FROM police_reports LIMIT 25
            """).fetchall()
        except Exception:
            rows = []

    for i, r in enumerate(rows):
        try:
            rnum = r["report_number"] if "report_number" in r.keys() else f"PR-{i}"
            dt = r["date"] if "date" in r.keys() else ""
            summ = r["summary"] if "summary" in r.keys() else str(dict(r))[:100]
        except Exception:
            rnum, dt, summ = f"PR-{i}", "", str(r)[:100]

        nid = f"police_{str(rnum).replace(' ','_')[:30]}"
        nodes.append({
            "id": nid, "label": f"🚔 {rnum}",
            "layer": "police", "group": "police",
            "desc": f"{dt} — {summ[:120]}", "color": LAYER_COLORS["police"],
            "size": 7,
        })
        # Link to NSPD hub
        links.append({
            "source": nid, "target": "nspd",
            "type": "police-report", "color": "#ffcc0033", "layer": "police",
        })
    return nodes, links


def layer_doctrine(conn):
    """Legal doctrines, remedies, and MCR/MCL mapping."""
    nodes, links = [], []
    doctrines = [
        ("doc_best_interest", "Best Interest Factors", "MCL 722.23(a)-(l)", "custody"),
        ("doc_ece", "Established Custodial Env", "MCL 722.27(1)(c)", "custody"),
        ("doc_alienation", "Parental Alienation", "MCL 722.23(j)", "custody"),
        ("doc_vodvarka", "Change of Circumstances", "Vodvarka v Grasher", "custody"),
        ("doc_disqual", "Disqualification", "MCR 2.003", "judicial"),
        ("doc_ppo", "PPO", "MCL 600.2950", "ppo"),
        ("doc_appeal", "Appeal of Right", "MCR 7.204/7.205", "appellate"),
        ("doc_contempt", "Contempt", "MCL 600.1701; MCR 3.606", "enforcement"),
        ("doc_due_process", "Due Process", "US Const Amend XIV; Mathews v Eldridge", "constitutional"),
        ("doc_1983", "42 USC §1983", "Federal Civil Rights", "federal"),
        ("doc_superintending", "Superintending Control", "MCR 7.306", "appellate"),
        ("doc_mandamus", "Mandamus", "MCR 7.306", "appellate"),
        ("doc_habeas", "Habeas Corpus", "MCL 600.4301", "constitutional"),
        ("doc_troxel", "Parental Rights", "Troxel v Granville", "constitutional"),
        ("doc_service", "Service of Process", "MCR 2.105/2.107", "procedural"),
        ("doc_relief_judgment", "Relief From Judgment", "MCR 2.612", "procedural"),
        ("doc_summary_disp", "Summary Disposition", "MCR 2.116", "procedural"),
        ("doc_pierron", "Pierron v Pierron", "486 Mich 81 (2010)", "custody"),
        ("doc_brown", "Brown v Loveman", "260 Mich App 576 (2004)", "parenting"),
        ("doc_fletcher", "Fletcher v Fletcher", "447 Mich 871 (1994)", "custody"),
        ("doc_sullivan", "Sullivan v Gray", "117 Mich App 476 (1982)", "evidence"),
        ("doc_monell", "Monell Liability", "Monell v Dept Social Svcs", "federal"),
    ]
    for did, label, auth, category in doctrines:
        nodes.append({
            "id": did, "label": label,
            "layer": "doctrine", "group": f"doctrine-{category}",
            "desc": auth, "color": LAYER_COLORS["doctrine"], "size": 9,
        })

    # Remedies
    remedies = [
        ("remedy_restore", "Restore Parenting Time", "Emergency relief"),
        ("remedy_disqualify", "Disqualify Judge", "MCR 2.003"),
        ("remedy_vacate", "Vacate Judgment", "MCR 2.612"),
        ("remedy_damages", "§1983 Damages", "$620K-$2.48M"),
        ("remedy_contempt", "Contempt Sanctions", "MCL 600.1701"),
        ("remedy_jtc", "JTC Complaint", "Judicial Tenure Commission"),
        ("remedy_msc", "MSC Original Action", "MCR 7.306"),
        ("remedy_habeas", "Habeas Release", "MCL 600.4301"),
        ("remedy_ppo_term", "Terminate PPO", "MCR 3.707(B)"),
        ("remedy_injunction", "Injunctive Relief", "Preliminary/permanent"),
        ("remedy_fees", "Attorney Fees/Costs", "MCR 2.625"),
    ]
    for rid, label, desc in remedies:
        nodes.append({
            "id": rid, "label": f"⚖ {label}",
            "layer": "doctrine", "group": "remedy",
            "desc": desc, "color": "#66ffaa", "size": 8,
        })

    # Doctrine → remedy links
    doc_remedy = [
        ("doc_best_interest", "remedy_restore"), ("doc_alienation", "remedy_restore"),
        ("doc_disqual", "remedy_disqualify"), ("doc_disqual", "remedy_jtc"),
        ("doc_relief_judgment", "remedy_vacate"), ("doc_1983", "remedy_damages"),
        ("doc_contempt", "remedy_contempt"), ("doc_superintending", "remedy_msc"),
        ("doc_habeas", "remedy_habeas"), ("doc_ppo", "remedy_ppo_term"),
    ]
    for d, r in doc_remedy:
        links.append({
            "source": d, "target": r,
            "type": "doctrine-remedy", "color": "#44ffaa44", "layer": "doctrine",
        })
    return nodes, links


# ═══════════════════════════════════════════════════════════════════════════════
#  CROSS-LAYER LINKS
# ═══════════════════════════════════════════════════════════════════════════════

def cross_layer_links(all_nodes, all_links):
    """Generate links between nodes in different layers."""
    node_ids = {n["id"] for n in all_nodes}
    new_links = []

    # Weapon → doctrine mapping
    weapon_doctrine = {
        "FALSE_ALLEGATION": ["doc_alienation", "doc_best_interest", "doc_pierron"],
        "EX_PARTE": ["doc_due_process", "doc_disqual", "doc_1983"],
        "PARENTING_DENIAL": ["doc_best_interest", "doc_vodvarka", "doc_troxel"],
        "CONTEMPT_ABUSE": ["doc_contempt", "doc_due_process", "doc_habeas"],
        "PPO_WEAPONIZATION": ["doc_ppo", "doc_disqual"],
        "JUDICIAL_BIAS": ["doc_disqual", "doc_1983", "doc_superintending"],
        "EVIDENCE_SUPPRESSION": ["doc_due_process", "doc_sullivan"],
        "PARENTAL_ALIENATION": ["doc_alienation", "doc_best_interest"],
        "DUE_PROCESS_VIOLATION": ["doc_due_process", "doc_1983", "doc_mandamus"],
    }
    for wt, docs in weapon_doctrine.items():
        wid = f"weapon_{wt}"
        if wid in node_ids:
            for did in docs:
                if did in node_ids:
                    new_links.append({
                        "source": wid, "target": did,
                        "type": "weapon→doctrine", "color": "#ff886644",
                        "layer": "cross",
                    })

    # Adversary → lane links
    adv_lane = [
        ("emily_watson", "lane_A"), ("emily_watson", "lane_D"),
        ("mcneill", "lane_A"), ("mcneill", "lane_D"), ("mcneill", "lane_E"),
        ("hoopes", "lane_B"), ("ladas_hoopes", "lane_CRIM"),
        ("shady_oaks", "lane_B"), ("andrew", "lane_A"), ("andrew", "lane_F"),
    ]
    for adv, lane in adv_lane:
        if adv in node_ids and lane in node_ids:
            new_links.append({
                "source": adv, "target": lane,
                "type": "adversary→lane", "color": "#ffaa0044", "layer": "cross",
            })

    # Filing → lane links
    filing_lane = [
        ("filing_F1", "lane_A"), ("filing_F2", "lane_E"), ("filing_F3", "lane_E"),
        ("filing_F4", "lane_E"), ("filing_F5", "lane_F"), ("filing_F6", "lane_A"),
        ("filing_F7", "lane_C"), ("filing_F8", "lane_E"), ("filing_F9", "lane_D"),
        ("filing_F10", "lane_A"),
    ]
    for fid, lid in filing_lane:
        if fid in node_ids and lid in node_ids:
            new_links.append({
                "source": fid, "target": lid,
                "type": "filing→lane", "color": "#00ff8844", "layer": "cross",
            })

    # Doctrine → filing links
    doc_filing = [
        ("doc_best_interest", "filing_F1"), ("doc_disqual", "filing_F3"),
        ("doc_superintending", "filing_F2"), ("doc_mandamus", "filing_F4"),
        ("doc_appeal", "filing_F5"), ("doc_habeas", "filing_F6"),
        ("doc_1983", "filing_F7"), ("doc_contempt", "filing_F10"),
        ("doc_ppo", "filing_F9"),
    ]
    for did, fid in doc_filing:
        if did in node_ids and fid in node_ids:
            new_links.append({
                "source": did, "target": fid,
                "type": "doctrine→filing", "color": "#44ffaa44", "layer": "cross",
            })

    # Engine → lane bridging
    eng_lane = [
        ("eng_nexus", "lane_A"), ("eng_analytics", "lane_E"),
        ("eng_semantic", "lane_A"), ("eng_typst", "lane_F"),
        ("eng_perception", "lane_E"), ("eng_filing_engine", "lane_A"),
    ]
    for eid, lid in eng_lane:
        if eid in node_ids and lid in node_ids:
            new_links.append({
                "source": eid, "target": lid,
                "type": "engine→lane", "color": "#8888ff33", "layer": "cross",
            })

    # FRED → filing links
    if "fred_core" in node_ids:
        for fid in ["filing_F1", "filing_F3", "filing_F5"]:
            if fid in node_ids:
                new_links.append({
                    "source": "fred_core", "target": fid,
                    "type": "fred→filing", "color": "#ff880033", "layer": "cross",
                })

    # McNeill → judicial violations
    if "mcneill" in node_ids and "eh_core" in node_ids:
        new_links.append({
            "source": "mcneill", "target": "eh_core",
            "type": "violations-tracked", "color": "#ff00ff44", "layer": "cross",
        })

    return new_links


# ═══════════════════════════════════════════════════════════════════════════════
#  HTML TEMPLATE — v5 APEX with all upgrades
# ═══════════════════════════════════════════════════════════════════════════════

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>THEMANBEARPIG v5 — SINGULARITY FORGE</title>
<style>
/* ─── BASE ──────────────────────────────────────────── */
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#060a14;--panel:rgba(8,16,32,0.85);--border:rgba(0,204,255,0.15);
  --text:#c8d8e8;--accent:#00ccff;--red:#ff2244;--gold:#ffaa00;--green:#00ff88;
  --purple:#cc44ff;--font:'Consolas','JetBrains Mono',monospace;
}
html,body{width:100%;height:100%;overflow:hidden;background:var(--bg);color:var(--text);font-family:var(--font)}

/* ─── SCANLINES ─────────────────────────────────────── */
body::after{content:'';position:fixed;inset:0;pointer-events:none;z-index:9999;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.08) 2px,rgba(0,0,0,0.08) 4px)}

/* ─── GLASSMORPHISM PANEL ───────────────────────────── */
.glass{background:var(--panel);border:1px solid var(--border);border-radius:8px;
  backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);padding:12px;
  box-shadow:0 0 20px rgba(0,204,255,0.05),inset 0 0 30px rgba(0,0,0,0.3)}

/* ─── HUD (top-left) ───────────────────────────────── */
#hud{position:fixed;top:12px;left:12px;z-index:100;min-width:260px}
#hud h1{font-family:'Orbitron',var(--font);font-size:14px;color:var(--accent);
  text-transform:uppercase;letter-spacing:3px;margin-bottom:8px;
  text-shadow:0 0 8px rgba(0,204,255,0.5)}
#hud .stat{display:flex;justify-content:space-between;font-size:11px;padding:2px 0;
  border-bottom:1px solid rgba(255,255,255,0.04)}
#hud .stat .val{color:var(--accent);font-weight:bold}

/* ─── SEARCH BAR ────────────────────────────────────── */
#search-bar{position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:200;
  display:none;width:400px}
#search-bar input{width:100%;padding:10px 16px;font-size:14px;font-family:var(--font);
  background:rgba(8,16,32,0.95);border:1px solid var(--accent);border-radius:6px;
  color:var(--text);outline:none}
#search-bar input::placeholder{color:rgba(200,216,232,0.3)}
#search-results{max-height:250px;overflow-y:auto;margin-top:4px}
#search-results .sr-item{padding:6px 12px;font-size:12px;cursor:pointer;border-bottom:1px solid rgba(255,255,255,0.05)}
#search-results .sr-item:hover{background:rgba(0,204,255,0.1)}
#search-results .sr-item .sr-layer{color:var(--accent);font-size:10px;text-transform:uppercase}

/* ─── CONTROLS (top-right) ──────────────────────────── */
#controls{position:fixed;top:12px;right:12px;z-index:100;width:180px}
#controls h3{font-size:11px;color:var(--accent);text-transform:uppercase;letter-spacing:2px;margin-bottom:6px}
.layer-btn{display:flex;align-items:center;gap:6px;padding:3px 0;font-size:11px;cursor:pointer;opacity:0.9}
.layer-btn:hover{opacity:1}
.layer-btn .dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.layer-btn.hidden{opacity:0.3;text-decoration:line-through}

/* ─── INFO PANEL (bottom-left) ──────────────────────── */
#info{position:fixed;bottom:12px;left:12px;z-index:100;width:320px;max-height:280px;overflow-y:auto;display:none}
#info h3{font-size:12px;color:var(--accent);margin-bottom:6px}
#info .info-row{font-size:11px;padding:2px 0;border-bottom:1px solid rgba(255,255,255,0.04)}
#info .info-label{color:rgba(200,216,232,0.5);text-transform:uppercase;font-size:9px}

/* ─── THREAT GAUGE ──────────────────────────────────── */
#threat-gauge{position:fixed;bottom:12px;right:200px;z-index:100;width:200px}
#threat-gauge h3{font-size:10px;color:var(--red);text-transform:uppercase;letter-spacing:2px;margin-bottom:4px}
#threat-bar{height:12px;border-radius:6px;background:rgba(255,255,255,0.05);overflow:hidden;position:relative}
#threat-fill{height:100%;border-radius:6px;transition:width 0.5s;
  background:linear-gradient(90deg,var(--green),var(--gold),var(--red))}
#threat-val{position:absolute;right:4px;top:0;font-size:9px;line-height:12px;color:#fff;font-weight:bold}

/* ─── SEPARATION COUNTER ────────────────────────────── */
#separation{position:fixed;top:60px;left:50%;transform:translateX(-50%);z-index:100;text-align:center}
#separation .days{font-family:'Orbitron',var(--font);font-size:28px;font-weight:900;
  background:linear-gradient(135deg,var(--red),var(--gold));-webkit-background-clip:text;
  -webkit-text-fill-color:transparent;animation:pulse 2s infinite}
#separation .label{font-size:9px;text-transform:uppercase;letter-spacing:3px;color:rgba(255,34,68,0.7)}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.8;transform:scale(1.02)}}

/* ─── LEGEND (bottom-right) ─────────────────────────── */
#legend{position:fixed;bottom:12px;right:12px;z-index:100;width:170px}
#legend h3{font-size:10px;color:var(--accent);text-transform:uppercase;letter-spacing:2px;margin-bottom:4px}
.legend-item{display:flex;align-items:center;gap:6px;font-size:10px;padding:2px 0}
.legend-item .swatch{width:10px;height:10px;border-radius:3px;flex-shrink:0}

/* ─── CONTEXT MENU ──────────────────────────────────── */
#ctx-menu{position:fixed;z-index:500;display:none;min-width:180px}
#ctx-menu .ctx-item{padding:8px 14px;font-size:12px;cursor:pointer;border-bottom:1px solid rgba(255,255,255,0.05)}
#ctx-menu .ctx-item:hover{background:rgba(0,204,255,0.15)}

/* ─── MINIMAP ───────────────────────────────────────── */
#minimap{position:fixed;bottom:80px;right:12px;z-index:100;width:170px;height:120px;overflow:hidden}
#minimap canvas{width:100%;height:100%;cursor:crosshair}

/* ─── HELP OVERLAY ──────────────────────────────────── */
#help-overlay{position:fixed;inset:0;z-index:1000;background:rgba(6,10,20,0.92);display:none;
  justify-content:center;align-items:center}
#help-overlay .help-content{max-width:500px;padding:30px}
#help-overlay h2{font-family:'Orbitron',var(--font);color:var(--accent);margin-bottom:16px;font-size:16px}
#help-overlay .hk{display:flex;justify-content:space-between;padding:4px 0;font-size:12px;
  border-bottom:1px solid rgba(255,255,255,0.05)}
#help-overlay .hk kbd{background:rgba(0,204,255,0.15);padding:2px 8px;border-radius:3px;font-family:var(--font)}
#help-overlay .close-help{margin-top:16px;font-size:11px;color:rgba(200,216,232,0.4);text-align:center}

/* ─── STATS PANEL ───────────────────────────────────── */
#stats{position:fixed;top:12px;right:200px;z-index:100;width:130px}
#stats .stat{font-size:10px;display:flex;justify-content:space-between;padding:1px 0}
#stats .stat .val{color:var(--green);font-weight:bold}
#fps-counter{color:var(--green)}

/* ─── TOOLTIP ───────────────────────────────────────── */
#tooltip{position:absolute;z-index:300;display:none;max-width:320px;font-size:11px;
  background:rgba(8,16,32,0.95);border:1px solid var(--accent);border-radius:6px;
  padding:10px 14px;pointer-events:none;backdrop-filter:blur(8px)}
#tooltip .tt-label{font-weight:bold;color:var(--accent);font-size:13px;margin-bottom:4px}
#tooltip .tt-layer{font-size:9px;text-transform:uppercase;color:rgba(200,216,232,0.5);margin-bottom:6px}
#tooltip .tt-desc{line-height:1.5}
#tooltip .tt-role{color:var(--gold);font-size:10px;margin-bottom:4px}

/* ─── SCROLLBAR ─────────────────────────────────────── */
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--accent);border-radius:2px}

/* ─── SVG ───────────────────────────────────────────── */
svg{display:block}
</style>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
</head>
<body>

<!-- ─── SVG FILTERS ─────────────────────────────────── -->
<svg width="0" height="0" style="position:absolute">
<defs>
  <filter id="glow-cyan" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>
    <feColorMatrix in="blur" type="matrix" values="0 0 0 0 0  0 0.8 1 0 0  0 0.8 1 0 0  0 0 0 1 0" result="color"/>
    <feMerge><feMergeNode in="color"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow-red" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>
    <feColorMatrix in="blur" type="matrix" values="1 0 0 0 0  0 0 0 0 0  0 0 0.2 0 0  0 0 0 1 0" result="color"/>
    <feMerge><feMergeNode in="color"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow-gold" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>
    <feColorMatrix in="blur" type="matrix" values="1 0 0 0 0  0 0.7 0 0 0  0 0 0 0 0  0 0 0 1 0" result="color"/>
    <feMerge><feMergeNode in="color"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <filter id="glow-purple" x="-50%" y="-50%" width="200%" height="200%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur"/>
    <feColorMatrix in="blur" type="matrix" values="0.8 0 0 0 0  0 0 0.2 0 0  0 0 1 0 0  0 0 0 1 0" result="color"/>
    <feMerge><feMergeNode in="color"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
</defs>
</svg>

<!-- ─── HUD ─────────────────────────────────────────── -->
<div id="hud" class="glass">
  <h1>⚡ THEMANBEARPIG v5</h1>
  <div class="stat"><span>Nodes</span><span class="val">__NODECOUNT__</span></div>
  <div class="stat"><span>Links</span><span class="val">__LINKCOUNT__</span></div>
  <div class="stat"><span>Layers</span><span class="val">13</span></div>
  <div class="stat"><span>Evidence</span><span class="val">__EVCOUNT__</span></div>
  <div class="stat"><span>Authorities</span><span class="val">__AUTHCOUNT__</span></div>
  <div class="stat"><span>Violations</span><span class="val">__JVCOUNT__</span></div>
  <div class="stat"><span>Weapons</span><span class="val">__WCOUNT__</span></div>
  <div class="stat"><span>Version</span><span class="val">v5.0 SINGULARITY</span></div>
</div>

<!-- ─── SEPARATION COUNTER ──────────────────────────── -->
<div id="separation" class="glass" style="padding:8px 20px">
  <div class="days">__SEP__</div>
  <div class="label">days separated from L.D.W.</div>
</div>

<!-- ─── SEARCH BAR ──────────────────────────────────── -->
<div id="search-bar" class="glass">
  <input type="text" id="search-input" placeholder="Search nodes... (press / to open, Esc to close)">
  <div id="search-results" class="glass" style="display:none;margin-top:4px;padding:0"></div>
</div>

<!-- ─── CONTROLS ────────────────────────────────────── -->
<div id="controls" class="glass">
  <h3>Layers</h3>
  <div id="layer-list"></div>
</div>

<!-- ─── STATS ───────────────────────────────────────── -->
<div id="stats" class="glass">
  <div class="stat"><span>FPS</span><span class="val" id="fps-counter">60</span></div>
  <div class="stat"><span>Visible</span><span class="val" id="visible-count">0</span></div>
  <div class="stat"><span>Selected</span><span class="val" id="selected-count">0</span></div>
</div>

<!-- ─── INFO PANEL ──────────────────────────────────── -->
<div id="info" class="glass">
  <h3 id="info-title">Node Info</h3>
  <div id="info-body"></div>
</div>

<!-- ─── THREAT GAUGE ────────────────────────────────── -->
<div id="threat-gauge" class="glass">
  <h3>⚠ Threat Level</h3>
  <div id="threat-bar"><div id="threat-fill" style="width:85%"></div><span id="threat-val">8.5</span></div>
</div>

<!-- ─── MINIMAP ─────────────────────────────────────── -->
<div id="minimap" class="glass" style="padding:4px">
  <canvas id="minimap-canvas"></canvas>
</div>

<!-- ─── LEGEND ──────────────────────────────────────── -->
<div id="legend" class="glass">
  <h3>Legend</h3>
  <div id="legend-items"></div>
</div>

<!-- ─── CONTEXT MENU ────────────────────────────────── -->
<div id="ctx-menu" class="glass" style="padding:0">
  <div class="ctx-item" data-action="connections">🔗 Show Connections</div>
  <div class="ctx-item" data-action="pin">📌 Pin/Unpin Node</div>
  <div class="ctx-item" data-action="focus">🎯 Focus Ego Network</div>
  <div class="ctx-item" data-action="hide">👁 Hide Node</div>
  <div class="ctx-item" data-action="info">ℹ Full Details</div>
  <div class="ctx-item" data-action="copy">📋 Copy Label</div>
  <div class="ctx-item" data-action="reset">↩ Reset View</div>
</div>

<!-- ─── HELP OVERLAY ────────────────────────────────── -->
<div id="help-overlay">
  <div class="help-content glass">
    <h2>⌨ Keyboard Shortcuts</h2>
    <div class="hk"><span>Search</span><kbd>/</kbd></div>
    <div class="hk"><span>Toggle fullscreen</span><kbd>F</kbd></div>
    <div class="hk"><span>Cycle layers</span><kbd>L</kbd></div>
    <div class="hk"><span>Reset zoom</span><kbd>R</kbd></div>
    <div class="hk"><span>Export PNG</span><kbd>E</kbd></div>
    <div class="hk"><span>Help</span><kbd>?</kbd></div>
    <div class="hk"><span>Close</span><kbd>Esc</kbd></div>
    <div class="hk"><span>Right-click node</span><span>Context menu</span></div>
    <div class="hk"><span>Scroll</span><span>Zoom</span></div>
    <div class="hk"><span>Click + drag</span><span>Pan / Move node</span></div>
    <div class="close-help">Press ? or Esc to close</div>
  </div>
</div>

<!-- ─── TOOLTIP ─────────────────────────────────────── -->
<div id="tooltip"></div>

<!-- ─── MAIN SVG ────────────────────────────────────── -->
<svg id="graph" width="100%" height="100%"></svg>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
// ═══════════════════════════════════════════════════════
//  DATA INJECTION (via __MARKER__ replacement)
// ═══════════════════════════════════════════════════════
const NODES = __NODES__;
const LINKS = __LINKS__;
const STATS = __STATS__;
const LAYER_META = {
  adversary:     {label:"Adversary",      color:"#ff2244", glow:"glow-red",    col:0, row:0},
  authority:     {label:"Authority",      color:"#00ccff", glow:"glow-cyan",   col:1, row:0},
  filing:        {label:"Filing",         color:"#00ff88", glow:"glow-cyan",   col:2, row:0},
  lanes:         {label:"Case Lanes",     color:"#ffaa00", glow:"glow-gold",   col:3, row:0},
  evidence:      {label:"Evidence",       color:"#ff66ff", glow:"glow-purple", col:4, row:0},
  system:        {label:"System",         color:"#8888ff", glow:"glow-purple", col:0, row:1},
  fred:          {label:"FRED",           color:"#ff8800", glow:"glow-gold",   col:1, row:1},
  meek:          {label:"MEEK",           color:"#00ffcc", glow:"glow-gold",   col:2, row:1},
  event_horizon: {label:"Event Horizon",  color:"#ff00ff", glow:"glow-purple", col:3, row:1},
  brains:        {label:"Brains",         color:"#aaaaff", glow:"glow-purple", col:4, row:1},
  weapons:       {label:"Weapons",        color:"#ff4444", glow:"glow-red",    col:0, row:2},
  police:        {label:"Police",         color:"#ffcc00", glow:"glow-gold",   col:1, row:2},
  doctrine:      {label:"Doctrine",       color:"#44ffaa", glow:"glow-cyan",   col:2, row:2},
};

const layerNames = Object.keys(LAYER_META);
const layerVisible = {};
layerNames.forEach(l => layerVisible[l] = true);
layerVisible["cross"] = true;

// ═══════════════════════════════════════════════════════
//  SVG SETUP
// ═══════════════════════════════════════════════════════
const width = window.innerWidth, height = window.innerHeight;
const svg = d3.select("#graph").attr("viewBox", [0, 0, width, height]);
const g = svg.append("g");

const zoom = d3.zoom().scaleExtent([0.1, 8]).on("zoom", ({transform}) => {
  g.attr("transform", transform);
  currentTransform = transform;
  updateMinimap();
});
svg.call(zoom);
let currentTransform = d3.zoomIdentity;

// ═══════════════════════════════════════════════════════
//  FORCE SIMULATION
// ═══════════════════════════════════════════════════════
const simulation = d3.forceSimulation(NODES)
  .force("link", d3.forceLink(LINKS).id(d => d.id).distance(65).strength(0.2))
  .force("charge", d3.forceManyBody().strength(-120).distanceMax(400))
  .force("center", d3.forceCenter(width/2, height/2))
  .force("collision", d3.forceCollide().radius(d => (d.size||6) + 3))
  .force("x", d3.forceX().x(d => {
    const meta = LAYER_META[d.layer];
    if(!meta) return width/2;
    return width * 0.15 + (meta.col / 4) * width * 0.7;
  }).strength(0.06))
  .force("y", d3.forceY().y(d => {
    const meta = LAYER_META[d.layer];
    if(!meta) return height/2;
    return height * 0.2 + meta.row * height * 0.3;
  }).strength(0.06))
  .alphaDecay(0.012)
  .velocityDecay(0.35);

// ═══════════════════════════════════════════════════════
//  RENDER LINKS
// ═══════════════════════════════════════════════════════
const linkG = g.append("g").attr("class","links");
const link = linkG.selectAll("line").data(LINKS).join("line")
  .attr("stroke", d => d.color || "#ffffff22")
  .attr("stroke-width", d => d.weight ? Math.min(d.weight, 3) : 0.8)
  .attr("stroke-opacity", 0.5);

// ═══════════════════════════════════════════════════════
//  RENDER NODES
// ═══════════════════════════════════════════════════════
const nodeG = g.append("g").attr("class","nodes");
const node = nodeG.selectAll("circle").data(NODES).join("circle")
  .attr("r", d => d.size || 6)
  .attr("fill", d => d.color || "#888")
  .attr("stroke", d => d.color || "#888")
  .attr("stroke-width", 1.5)
  .attr("stroke-opacity", 0.6)
  .attr("filter", d => {
    const meta = LAYER_META[d.layer];
    return meta ? `url(#${meta.glow})` : "none";
  })
  .attr("cursor", "pointer")
  .call(d3.drag()
    .on("start", dragStarted)
    .on("drag", dragged)
    .on("end", dragEnded));

// Labels for large nodes
const labelG = g.append("g").attr("class","labels");
const label = labelG.selectAll("text").data(NODES.filter(d => (d.size||6) >= 12)).join("text")
  .text(d => d.label?.substring(0, 20) || "")
  .attr("font-size", d => Math.max(8, Math.min(11, (d.size||6) - 2)))
  .attr("fill", d => d.color || "#aaa")
  .attr("text-anchor", "middle")
  .attr("dy", d => -(d.size||6) - 4)
  .attr("pointer-events", "none")
  .attr("opacity", 0.8);

// ═══════════════════════════════════════════════════════
//  TOOLTIP
// ═══════════════════════════════════════════════════════
const tooltip = d3.select("#tooltip");
node.on("mouseover", function(evt, d) {
  const meta = LAYER_META[d.layer] || {};
  tooltip.html(
    `<div class="tt-label">${d.label||d.id}</div>` +
    `<div class="tt-layer">${meta.label||d.layer} Layer</div>` +
    (d.role ? `<div class="tt-role">${d.role}</div>` : "") +
    `<div class="tt-desc">${d.desc||""}</div>` +
    (d.threat !== undefined ? `<div style="margin-top:4px;color:${d.threat>=7?"#ff2244":d.threat>=4?"#ffaa00":"#00ff88"}">Threat: ${d.threat}/10</div>` : "")
  ).style("display","block")
   .style("left", (evt.pageX + 14) + "px")
   .style("top", (evt.pageY - 10) + "px");
  d3.select(this).attr("stroke-width", 3).attr("stroke-opacity", 1);
}).on("mousemove", function(evt) {
  tooltip.style("left", (evt.pageX + 14) + "px").style("top", (evt.pageY - 10) + "px");
}).on("mouseout", function() {
  tooltip.style("display","none");
  d3.select(this).attr("stroke-width", 1.5).attr("stroke-opacity", 0.6);
});

// Click → info panel
node.on("click", function(evt, d) {
  evt.stopPropagation();
  showNodeInfo(d);
});

function showNodeInfo(d) {
  const meta = LAYER_META[d.layer] || {};
  const connCount = LINKS.filter(l => (l.source.id||l.source)===d.id || (l.target.id||l.target)===d.id).length;
  document.getElementById("info").style.display = "block";
  document.getElementById("info-title").textContent = d.label || d.id;
  document.getElementById("info-body").innerHTML =
    `<div class="info-row"><span class="info-label">Layer</span> ${meta.label||d.layer}</div>` +
    (d.role ? `<div class="info-row"><span class="info-label">Role</span> ${d.role}</div>` : "") +
    (d.group ? `<div class="info-row"><span class="info-label">Group</span> ${d.group}</div>` : "") +
    `<div class="info-row"><span class="info-label">Connections</span> ${connCount}</div>` +
    (d.threat !== undefined ? `<div class="info-row"><span class="info-label">Threat</span> ${d.threat}/10</div>` : "") +
    (d.desc ? `<div class="info-row" style="margin-top:6px">${d.desc}</div>` : "");
}

// ═══════════════════════════════════════════════════════
//  CONTEXT MENU
// ═══════════════════════════════════════════════════════
let ctxNode = null;
node.on("contextmenu", function(evt, d) {
  evt.preventDefault();
  ctxNode = d;
  d3.select("#ctx-menu").style("display","block")
    .style("left", evt.pageX + "px").style("top", evt.pageY + "px");
});
svg.on("click", () => d3.select("#ctx-menu").style("display","none"));

document.querySelectorAll("#ctx-menu .ctx-item").forEach(el => {
  el.addEventListener("click", function() {
    const action = this.dataset.action;
    if(!ctxNode) return;
    if(action === "connections") highlightConnections(ctxNode);
    else if(action === "pin") { ctxNode.fx = ctxNode.x; ctxNode.fy = ctxNode.y; }
    else if(action === "focus") focusEgo(ctxNode);
    else if(action === "hide") hideNode(ctxNode);
    else if(action === "info") showNodeInfo(ctxNode);
    else if(action === "copy") navigator.clipboard?.writeText(ctxNode.label || ctxNode.id);
    else if(action === "reset") resetView();
    d3.select("#ctx-menu").style("display","none");
  });
});

function highlightConnections(d) {
  const connected = new Set();
  LINKS.forEach(l => {
    const sid = l.source.id || l.source, tid = l.target.id || l.target;
    if(sid === d.id) connected.add(tid);
    if(tid === d.id) connected.add(sid);
  });
  connected.add(d.id);
  node.attr("opacity", n => connected.has(n.id) ? 1 : 0.08);
  link.attr("opacity", l => {
    const sid = l.source.id || l.source, tid = l.target.id || l.target;
    return (sid === d.id || tid === d.id) ? 0.8 : 0.03;
  });
  label.attr("opacity", n => connected.has(n.id) ? 1 : 0.05);
  // Reset after 5 seconds
  setTimeout(() => { node.attr("opacity",1); link.attr("opacity",0.5); label.attr("opacity",0.8); }, 5000);
}

function focusEgo(d) {
  highlightConnections(d);
  const t = d3.zoomIdentity.translate(width/2 - d.x, height/2 - d.y).scale(2);
  svg.transition().duration(750).call(zoom.transform, t);
}

function hideNode(d) {
  d._hidden = true;
  updateVisibility();
}

// ═══════════════════════════════════════════════════════
//  SEARCH
// ═══════════════════════════════════════════════════════
const searchBar = document.getElementById("search-bar");
const searchInput = document.getElementById("search-input");
const searchResults = document.getElementById("search-results");

function openSearch() { searchBar.style.display = "block"; searchInput.focus(); searchInput.value = ""; }
function closeSearch() { searchBar.style.display = "none"; searchResults.style.display = "none"; }

searchInput.addEventListener("input", function() {
  const q = this.value.toLowerCase().trim();
  if(!q) { searchResults.style.display = "none"; return; }
  const matches = NODES.filter(n =>
    (n.label && n.label.toLowerCase().includes(q)) ||
    (n.id && n.id.toLowerCase().includes(q)) ||
    (n.desc && n.desc.toLowerCase().includes(q)) ||
    (n.role && n.role.toLowerCase().includes(q))
  ).slice(0, 15);
  if(!matches.length) { searchResults.style.display = "none"; return; }
  searchResults.style.display = "block";
  searchResults.innerHTML = matches.map(m =>
    `<div class="sr-item" data-id="${m.id}"><div>${m.label||m.id}</div><div class="sr-layer">${m.layer}</div></div>`
  ).join("");
  searchResults.querySelectorAll(".sr-item").forEach(el => {
    el.addEventListener("click", function() {
      const n = NODES.find(n => n.id === this.dataset.id);
      if(n) { focusEgo(n); showNodeInfo(n); }
      closeSearch();
    });
  });
});

searchInput.addEventListener("keydown", function(evt) {
  if(evt.key === "Escape") closeSearch();
  if(evt.key === "Enter") {
    const first = searchResults.querySelector(".sr-item");
    if(first) first.click();
  }
});

// ═══════════════════════════════════════════════════════
//  KEYBOARD SHORTCUTS
// ═══════════════════════════════════════════════════════
let layerCycleIdx = 0;
document.addEventListener("keydown", function(evt) {
  if(evt.target.tagName === "INPUT") return;
  const key = evt.key.toLowerCase();
  if(key === "/") { evt.preventDefault(); openSearch(); }
  else if(key === "escape") { closeSearch(); document.getElementById("help-overlay").style.display = "none"; d3.select("#ctx-menu").style.display = "none"; }
  else if(key === "f") { if(!document.fullscreenElement) document.documentElement.requestFullscreen(); else document.exitFullscreen(); }
  else if(key === "l") {
    layerCycleIdx = (layerCycleIdx + 1) % (layerNames.length + 1);
    if(layerCycleIdx === 0) layerNames.forEach(l => layerVisible[l] = true);
    else { layerNames.forEach(l => layerVisible[l] = false); layerVisible[layerNames[layerCycleIdx-1]] = true; layerVisible["cross"] = true; }
    updateVisibility(); buildLayerList();
  }
  else if(key === "r") resetView();
  else if(key === "e") exportPNG();
  else if(key === "?" || (evt.shiftKey && key === "/")) {
    const h = document.getElementById("help-overlay");
    h.style.display = h.style.display === "flex" ? "none" : "flex";
  }
});

function resetView() {
  svg.transition().duration(500).call(zoom.transform, d3.zoomIdentity);
  NODES.forEach(n => { n._hidden = false; });
  layerNames.forEach(l => layerVisible[l] = true); layerVisible["cross"] = true;
  updateVisibility(); buildLayerList();
  node.attr("opacity",1); link.attr("opacity",0.5); label.attr("opacity",0.8);
}

// ═══════════════════════════════════════════════════════
//  EXPORT
// ═══════════════════════════════════════════════════════
function exportPNG() {
  const svgEl = document.getElementById("graph");
  const clone = svgEl.cloneNode(true);
  clone.setAttribute("xmlns","http://www.w3.org/2000/svg");
  const blob = new Blob([clone.outerHTML], {type:"image/svg+xml"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "THEMANBEARPIG_v5.svg"; a.click();
  URL.revokeObjectURL(url);
}

// ═══════════════════════════════════════════════════════
//  LAYER CONTROLS
// ═══════════════════════════════════════════════════════
function buildLayerList() {
  const el = document.getElementById("layer-list");
  el.innerHTML = layerNames.map(l => {
    const meta = LAYER_META[l];
    const cls = layerVisible[l] ? "layer-btn" : "layer-btn hidden";
    return `<div class="${cls}" data-layer="${l}"><span class="dot" style="background:${meta.color}"></span>${meta.label}</div>`;
  }).join("");
  el.querySelectorAll(".layer-btn").forEach(btn => {
    btn.addEventListener("click", function() {
      const l = this.dataset.layer;
      layerVisible[l] = !layerVisible[l];
      this.classList.toggle("hidden");
      updateVisibility();
    });
  });
}

function updateVisibility() {
  node.attr("display", d => (layerVisible[d.layer] !== false && !d._hidden) ? null : "none");
  link.attr("display", d => {
    const sl = d.source.layer || d.layer, tl = d.target.layer || d.layer;
    if(d.layer === "cross") return (layerVisible["cross"] !== false) ? null : "none";
    return (layerVisible[sl] !== false && layerVisible[tl] !== false) ? null : "none";
  });
  label.attr("display", d => (layerVisible[d.layer] !== false && !d._hidden) ? null : "none");
  document.getElementById("visible-count").textContent = NODES.filter(d => layerVisible[d.layer] !== false && !d._hidden).length;
}

// ═══════════════════════════════════════════════════════
//  LEGEND
// ═══════════════════════════════════════════════════════
document.getElementById("legend-items").innerHTML = layerNames.map(l => {
  const m = LAYER_META[l];
  return `<div class="legend-item"><span class="swatch" style="background:${m.color}"></span>${m.label}</div>`;
}).join("");

// ═══════════════════════════════════════════════════════
//  MINIMAP
// ═══════════════════════════════════════════════════════
const mmCanvas = document.getElementById("minimap-canvas");
const mmCtx = mmCanvas.getContext("2d");
mmCanvas.width = 170; mmCanvas.height = 120;

function updateMinimap() {
  mmCtx.clearRect(0, 0, 170, 120);
  mmCtx.fillStyle = "rgba(6,10,20,0.8)";
  mmCtx.fillRect(0, 0, 170, 120);
  const bounds = {x0:Infinity, y0:Infinity, x1:-Infinity, y1:-Infinity};
  NODES.forEach(d => {
    if(d.x < bounds.x0) bounds.x0 = d.x;
    if(d.y < bounds.y0) bounds.y0 = d.y;
    if(d.x > bounds.x1) bounds.x1 = d.x;
    if(d.y > bounds.y1) bounds.y1 = d.y;
  });
  const bw = (bounds.x1 - bounds.x0) || 1, bh = (bounds.y1 - bounds.y0) || 1;
  const scale = Math.min(160 / bw, 110 / bh);
  const ox = 5 + (160 - bw*scale)/2, oy = 5 + (110 - bh*scale)/2;
  NODES.forEach(d => {
    if(layerVisible[d.layer] === false || d._hidden) return;
    mmCtx.fillStyle = d.color || "#888";
    mmCtx.fillRect(ox + (d.x - bounds.x0)*scale, oy + (d.y - bounds.y0)*scale, 2, 2);
  });
  // Viewport indicator
  const vx = (-currentTransform.x / currentTransform.k - bounds.x0) * scale + ox;
  const vy = (-currentTransform.y / currentTransform.k - bounds.y0) * scale + oy;
  const vw = (width / currentTransform.k) * scale;
  const vh = (height / currentTransform.k) * scale;
  mmCtx.strokeStyle = "rgba(0,204,255,0.6)";
  mmCtx.lineWidth = 1;
  mmCtx.strokeRect(vx, vy, vw, vh);
}

// Click minimap to pan
mmCanvas.addEventListener("click", function(evt) {
  const rect = mmCanvas.getBoundingClientRect();
  const mx = evt.clientX - rect.left, my = evt.clientY - rect.top;
  const bounds = {x0:Infinity, y0:Infinity, x1:-Infinity, y1:-Infinity};
  NODES.forEach(d => {
    if(d.x < bounds.x0) bounds.x0 = d.x; if(d.y < bounds.y0) bounds.y0 = d.y;
    if(d.x > bounds.x1) bounds.x1 = d.x; if(d.y > bounds.y1) bounds.y1 = d.y;
  });
  const bw = (bounds.x1 - bounds.x0) || 1, bh = (bounds.y1 - bounds.y0) || 1;
  const scale = Math.min(160 / bw, 110 / bh);
  const ox = 5 + (160 - bw*scale)/2, oy = 5 + (110 - bh*scale)/2;
  const tx = bounds.x0 + (mx - ox) / scale;
  const ty = bounds.y0 + (my - oy) / scale;
  const t = d3.zoomIdentity.translate(width/2 - tx, height/2 - ty);
  svg.transition().duration(300).call(zoom.transform, t);
});

// ═══════════════════════════════════════════════════════
//  FPS COUNTER
// ═══════════════════════════════════════════════════════
let frameCount = 0, lastFpsTime = performance.now();
function fpsLoop() {
  frameCount++;
  const now = performance.now();
  if(now - lastFpsTime >= 1000) {
    const fps = frameCount;
    document.getElementById("fps-counter").textContent = fps;
    document.getElementById("fps-counter").style.color = fps >= 50 ? "#00ff88" : fps >= 30 ? "#ffaa00" : "#ff2244";
    frameCount = 0; lastFpsTime = now;
  }
  requestAnimationFrame(fpsLoop);
}
requestAnimationFrame(fpsLoop);

// ═══════════════════════════════════════════════════════
//  DRAG HANDLERS
// ═══════════════════════════════════════════════════════
function dragStarted(evt, d) {
  if(!evt.active) simulation.alphaTarget(0.1).restart();
  d.fx = d.x; d.fy = d.y;
}
function dragged(evt, d) { d.fx = evt.x; d.fy = evt.y; }
function dragEnded(evt, d) {
  if(!evt.active) simulation.alphaTarget(0);
  if(!d._pinned) { d.fx = null; d.fy = null; }
}

// ═══════════════════════════════════════════════════════
//  SIMULATION TICK
// ═══════════════════════════════════════════════════════
simulation.on("tick", () => {
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("cx", d => d.x).attr("cy", d => d.y);
  label.attr("x", d => d.x).attr("y", d => d.y - (d.size||6) - 4);
  if(simulation.alpha() < 0.05) updateMinimap();
});

// ═══════════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════════
buildLayerList();
updateVisibility();
document.getElementById("visible-count").textContent = NODES.length;

// Smooth initial zoom
setTimeout(() => {
  const bounds = {x0:Infinity, y0:Infinity, x1:-Infinity, y1:-Infinity};
  NODES.forEach(d => {
    if(d.x < bounds.x0) bounds.x0 = d.x; if(d.y < bounds.y0) bounds.y0 = d.y;
    if(d.x > bounds.x1) bounds.x1 = d.x; if(d.y > bounds.y1) bounds.y1 = d.y;
  });
  const bw = bounds.x1 - bounds.x0, bh = bounds.y1 - bounds.y0;
  const s = Math.min(width / (bw + 100), height / (bh + 100), 1.5);
  const cx = (bounds.x0 + bounds.x1) / 2, cy = (bounds.y0 + bounds.y1) / 2;
  svg.transition().duration(1500).call(zoom.transform,
    d3.zoomIdentity.translate(width/2, height/2).scale(s).translate(-cx, -cy));
}, 2000);

console.log(`⚡ THEMANBEARPIG v5 SINGULARITY — ${NODES.length} nodes, ${LINKS.length} links, 13 layers`);
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("═══════════════════════════════════════════════════")
    print("  THEMANBEARPIG v5 — SINGULARITY FORGE BUILDER")
    print("═══════════════════════════════════════════════════")

    conn = get_db()
    all_nodes, all_links = [], []

    layers = [
        ("adversary",     layer_adversary),
        ("authority",     layer_authority),
        ("filing",        layer_filing),
        ("lanes",         layer_lanes),
        ("evidence",      layer_evidence),
        ("system",        layer_system),
        ("fred",          layer_fred),
        ("meek",          layer_meek),
        ("event_horizon", layer_event_horizon),
        ("brains",        layer_brains),
        ("weapons",       layer_weapons),
        ("police",        layer_police),
        ("doctrine",      layer_doctrine),
    ]

    for i, (name, func) in enumerate(layers, 1):
        print(f"  [{i:2d}/13] Building {name} layer...", end=" ")
        try:
            nodes, links = func(conn)
            all_nodes.extend(nodes)
            all_links.extend(links)
            print(f"✓ {len(nodes)} nodes, {len(links)} links")
        except Exception as e:
            print(f"✗ ERROR: {e}")

    # Cross-layer links
    print(f"  [  +  ] Generating cross-layer links...", end=" ")
    cross_links = cross_layer_links(all_nodes, all_links)
    all_links.extend(cross_links)
    print(f"✓ {len(cross_links)} cross-layer links")

    # Dedup node IDs
    seen_ids = set()
    unique_nodes = []
    for n in all_nodes:
        if n["id"] not in seen_ids:
            seen_ids.add(n["id"])
            unique_nodes.append(n)
    all_nodes = unique_nodes

    # Filter links to only reference existing nodes
    valid_ids = {n["id"] for n in all_nodes}
    all_links = [l for l in all_links if l["source"] in valid_ids and l["target"] in valid_ids]

    # Stats
    sep_days = (date.today() - SEPARATION_DATE).days
    try:
        ev_count = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
        auth_count = conn.execute("SELECT COUNT(*) FROM authority_chains_v2").fetchone()[0]
        jv_count = conn.execute("SELECT COUNT(*) FROM judicial_violations").fetchone()[0]
        w_count = conn.execute("SELECT COUNT(*) FROM impeachment_matrix").fetchone()[0]
    except Exception:
        ev_count, auth_count, jv_count, w_count = 0, 0, 0, 0

    stats = {
        "nodes": len(all_nodes),
        "links": len(all_links),
        "layers": 13,
        "evidence": ev_count,
        "authorities": auth_count,
        "violations": jv_count,
        "weapons": w_count,
        "separation_days": sep_days,
        "built": datetime.now().isoformat(),
    }

    # Build HTML
    print(f"\n  Building HTML...")
    html = HTML_TEMPLATE
    html = html.replace("__NODES__", json.dumps(all_nodes, default=str))
    html = html.replace("__LINKS__", json.dumps(all_links, default=str))
    html = html.replace("__STATS__", json.dumps(stats))
    html = html.replace("__NODECOUNT__", f"{len(all_nodes):,}")
    html = html.replace("__LINKCOUNT__", f"{len(all_links):,}")
    html = html.replace("__SEP__", str(sep_days))
    html = html.replace("__EVCOUNT__", f"{ev_count:,}")
    html = html.replace("__AUTHCOUNT__", f"{auth_count:,}")
    html = html.replace("__JVCOUNT__", f"{jv_count:,}")
    html = html.replace("__WCOUNT__", f"{w_count:,}")

    # Write output
    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    # Also copy to build dir for exe packaging
    os.makedirs(BUILD_DIR, exist_ok=True)
    build_html = os.path.join(BUILD_DIR, "blueprint.html")
    with open(build_html, "w", encoding="utf-8") as f:
        f.write(html)

    conn.close()

    print(f"\n{'═'*50}")
    print(f"  ✅ THEMANBEARPIG v5 BUILT SUCCESSFULLY")
    print(f"  📊 {len(all_nodes)} nodes | {len(all_links)} links | 13 layers")
    print(f"  📁 {OUTPUT_HTML}")
    print(f"  📁 {build_html}")
    print(f"  📅 Separation: {sep_days} days")
    print(f"{'═'*50}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
