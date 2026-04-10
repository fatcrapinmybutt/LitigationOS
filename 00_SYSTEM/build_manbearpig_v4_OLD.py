"""
THEMANBEARPIG v4.0 — 13-Layer Litigation Intelligence Weapon System
====================================================================
Queries litigation_context.db for ALL 13 layers:
  1. Adversary Network (berry_mcneill_intelligence)
  2. Legal Authority (authority_chains_v2 top-cited)
  3. Filing Pipeline (filing_readiness)
  4. Case Lanes (evidence_quotes distribution)
  5. Evidence Arsenal (impeachment + contradictions)
  6. System Architecture (engines + brains)
  7. FRED Governance (FRED modules lineage)
  8. MEEK Lane Routing (4 tracks + vehicle types)
  9. Event Horizon Pipeline (12 subsystems)
  10. Brain Network (23 registered brains)
  11. Weaponization Chains (weapon_chains — 2,179 chains)
  12. Police Reports (police_reports — 356 incidents)
  13. Doctrine/Remedy Map (legal foundations + remedies)

Generates a self-contained HTML with inline D3.js v7.
"""
import sqlite3, json, os, sys, collections
from pathlib import Path
from datetime import date

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUT_HTML = r"C:\Users\andre\LitigationOS\12_WORKSPACE\ADVERSARY_NETWORK_BLUEPRINT.html"

sep_days = (date.today() - date(2025, 7, 29)).days

def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.row_factory = sqlite3.Row
    return conn

def safe_query(conn, sql, params=(), fallback=[]):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception as e:
        print(f"  WARN: {e}")
        return fallback

# ── LAYER 1: Adversary Network ──────────────────────────────────────────
def layer_adversary(conn):
    print("[1/10] Adversary Network...")
    nodes, links = [], []
    families = {
        "McNeill": {"members": [
            ("Hon. Jenny L. McNeill", "Judge — 14th Circuit", "judge"),
            ("Cavan Berry", "Atty Magistrate — 60th District, McNeill spouse", "judicial"),
        ], "color": "#ff0040"},
        "Watson": {"members": [
            ("Emily A. Watson", "Defendant — Custody/PPO", "adversary"),
            ("Albert Watson", "Emily's father — premeditation admission NS2505044", "adversary"),
            ("Lori Watson", "Emily's mother", "adversary"),
        ], "color": "#ff6600"},
        "Berry": {"members": [
            ("Ronald Berry", "Emily's boyfriend — NON-ATTORNEY legal ops", "adversary"),
            ("Andrew T. Berry", "Ezekiel Dr neighbor — Natoya's spouse", "connected"),
            ("Natoya Berry", "Ezekiel Dr — connected to A.T. Berry", "connected"),
        ], "color": "#ff00ff"},
        "Baxter": {"members": [
            ("Dennis 'Denny' Baxter", "Whitecaps co-owner — Rachel's father", "connected"),
            ("Sally J. Baxter", "Ezekiel Dr 2663 — connected to Berry/Rusco", "connected"),
            ("Rachel Baxter (Wren)", "Emily's best friend — Baxter daughter", "connected"),
        ], "color": "#00ccff"},
        "Rusco": {"members": [
            ("Pamela Rusco", "FOC + McNeill's judicial secretary", "judicial"),
            ("Tony Rusco", "Ezekiel Dr 2677 — connected to Berry/Baxter", "connected"),
        ], "color": "#ffcc00"},
        "Hoopes/Ladas": {"members": [
            ("Hon. Kenneth Hoopes", "Chief Judge — FORMER partner McNeill", "judge"),
            ("Hon. Maria Ladas-Hoopes", "60th District — FORMER partner McNeill", "judge"),
            ("Jennifer Barnes P55406", "Former opp counsel — WITHDREW Mar 2026", "legal"),
        ], "color": "#00ff88"},
        "Pigors": {"members": [
            ("Andrew James Pigors", "Plaintiff — pro se father", "plaintiff"),
            ("L.D.W.", "Minor child — MCR 8.119(H)", "child"),
        ], "color": "#4488ff"},
    }
    nid = 0
    name_to_id = {}
    for fam, data in families.items():
        for name, desc, role in data["members"]:
            nodes.append({
                "id": f"adv_{nid}", "label": name, "layer": "adversary",
                "group": fam, "role": role, "desc": desc,
                "color": data["color"], "size": 14 if role in ("judge","adversary","plaintiff") else 10
            })
            name_to_id[name] = f"adv_{nid}"
            nid += 1

    # Key relationship links
    rels = [
        ("Hon. Jenny L. McNeill","Cavan Berry","spouse","#ff0040"),
        ("Hon. Jenny L. McNeill","Pamela Rusco","judicial_secretary","#ffcc00"),
        ("Hon. Jenny L. McNeill","Hon. Kenneth Hoopes","former_law_partners","#00ff88"),
        ("Hon. Jenny L. McNeill","Hon. Maria Ladas-Hoopes","former_law_partners","#00ff88"),
        ("Hon. Kenneth Hoopes","Hon. Maria Ladas-Hoopes","married","#00ff88"),
        ("Cavan Berry","Hon. Maria Ladas-Hoopes","same_court_60th","#ff00ff"),
        ("Emily A. Watson","Ronald Berry","romantic_partner","#ff6600"),
        ("Emily A. Watson","Albert Watson","parent_child","#ff6600"),
        ("Emily A. Watson","Lori Watson","parent_child","#ff6600"),
        ("Emily A. Watson","Rachel Baxter (Wren)","best_friends","#00ccff"),
        ("Emily A. Watson","Jennifer Barnes P55406","attorney_client_WITHDREW","#00ff88"),
        ("Ronald Berry","Cavan Berry","family_surname","#ff00ff"),
        ("Andrew T. Berry","Natoya Berry","married","#ff00ff"),
        ("Andrew T. Berry","Tony Rusco","ezekiel_dr_neighbors","#aaaaaa"),
        ("Andrew T. Berry","Sally J. Baxter","ezekiel_dr_same_address","#aaaaaa"),
        ("Tony Rusco","Sally J. Baxter","ezekiel_dr_neighbors","#aaaaaa"),
        ("Tony Rusco","Pamela Rusco","family","#ffcc00"),
        ("Dennis 'Denny' Baxter","Rachel Baxter (Wren)","parent_child","#00ccff"),
        ("Dennis 'Denny' Baxter","Sally J. Baxter","family","#00ccff"),
        ("Albert Watson","Andrew James Pigors","adversary","#ff6600"),
        ("Andrew James Pigors","L.D.W.","parent_child","#4488ff"),
        ("Emily A. Watson","L.D.W.","parent_child","#ff6600"),
        ("Pamela Rusco","Cavan Berry","same_address_990_terrace","#ffcc00"),
    ]
    for src, tgt, rel, color in rels:
        if src in name_to_id and tgt in name_to_id:
            links.append({
                "source": name_to_id[src], "target": name_to_id[tgt],
                "type": rel, "color": color, "layer": "adversary"
            })

    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 2: Legal Authority ────────────────────────────────────────────
def layer_authority(conn):
    print("[2/10] Legal Authority...")
    nodes, links = [], []
    rows = safe_query(conn, """
        SELECT primary_citation, COUNT(*) as cnt
        FROM authority_chains_v2
        GROUP BY primary_citation ORDER BY cnt DESC LIMIT 25
    """)
    cite_ids = {}
    for i, r in enumerate(rows):
        nid = f"auth_{i}"
        cite = r["primary_citation"]
        cite_ids[cite] = nid
        nodes.append({
            "id": nid, "label": cite, "layer": "authority",
            "group": "statute" if "MCL" in cite else ("rule" if "MCR" in cite else "case"),
            "desc": f"{r['cnt']} citation chains",
            "color": "#00ffcc" if "MCL" in cite else ("#00aaff" if "MCR" in cite else "#ff88ff"),
            "size": min(6 + r["cnt"] // 200, 18)
        })

    # Co-citation links (Python-side, avoids heavy self-join)
    top_cites = [r["primary_citation"] for r in rows[:15]]
    cite_docs = {}
    for cite in top_cites:
        docs = safe_query(conn, """
            SELECT DISTINCT source_document FROM authority_chains_v2
            WHERE primary_citation = ? LIMIT 200
        """, (cite,))
        cite_docs[cite] = {d["source_document"] for d in docs}

    seen = set()
    for i, c1 in enumerate(top_cites):
        for c2 in top_cites[i+1:]:
            overlap = len(cite_docs.get(c1, set()) & cite_docs.get(c2, set()))
            if overlap >= 5 and c1 in cite_ids and c2 in cite_ids:
                key = tuple(sorted([c1, c2]))
                if key not in seen:
                    seen.add(key)
                    links.append({
                        "source": cite_ids[c1], "target": cite_ids[c2],
                        "type": "co_cited", "color": "#00ffcc44",
                        "layer": "authority", "weight": overlap
                    })

    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 3: Filing Pipeline ────────────────────────────────────────────
def layer_filing(conn):
    print("[3/10] Filing Pipeline...")
    nodes, links = [], []
    rows = safe_query(conn, "SELECT vehicle_name, filing_id, status, readiness_score, lane, deadline FROM filing_readiness ORDER BY readiness_score DESC")
    for i, r in enumerate(rows):
        conf = r["readiness_score"] or 0
        color = "#00ff00" if conf >= 80 else ("#ffaa00" if conf >= 50 else "#ff4444")
        nodes.append({
            "id": f"fil_{i}", "label": r["vehicle_name"],
            "layer": "filing", "group": r["status"] or "unknown",
            "desc": f"Readiness: {conf}% | {r['status']} | Lane {r['lane'] or '?'}",
            "color": color, "size": max(6, conf // 8)
        })
    # Sequential pipeline links
    for i in range(len(nodes) - 1):
        links.append({
            "source": nodes[i]["id"], "target": nodes[i+1]["id"],
            "type": "pipeline_sequence", "color": "#ffffff22", "layer": "filing"
        })
    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 4: Case Lanes ────────────────────────────────────────────────
def layer_lanes(conn):
    print("[4/10] Case Lanes...")
    nodes, links = [], []
    lane_info = {
        "A": ("Lane A: Custody", "2024-001507-DC", "#4488ff"),
        "B": ("Lane B: Housing", "2025-002760-CZ (Dismissed)", "#88ff44"),
        "C": ("Lane C: Federal §1983", "USDC WDMI (Drafting)", "#ff8844"),
        "D": ("Lane D: PPO", "2023-5907-PP", "#ff44ff"),
        "E": ("Lane E: Misconduct", "JTC/MSC Complaints", "#ff4444"),
        "F": ("Lane F: Appellate", "COA 366810", "#44ffff"),
        "CRIMINAL": ("Lane CRIMINAL", "2025-25245676SM (SEPARATE)", "#ffff00"),
    }
    rows = safe_query(conn, """
        SELECT lane, COUNT(*) as cnt FROM evidence_quotes
        WHERE lane IS NOT NULL GROUP BY lane ORDER BY cnt DESC
    """)
    lane_counts = {r["lane"]: r["cnt"] for r in rows}
    for lane, (name, case, color) in lane_info.items():
        cnt = lane_counts.get(lane, 0)
        nodes.append({
            "id": f"lane_{lane}", "label": name, "layer": "lanes",
            "group": "case_lane", "desc": f"{case} | {cnt:,} evidence quotes",
            "color": color, "size": max(8, min(20, cnt // 5000))
        })
    # Cross-lane links for shared evidence themes
    for l1 in ["A","D"]:
        links.append({"source": f"lane_{l1}", "target": "lane_E", "type": "feeds_misconduct", "color": "#ff444444", "layer": "lanes"})
    links.append({"source": "lane_A", "target": "lane_F", "type": "appeal_of_right", "color": "#44ffff44", "layer": "lanes"})
    links.append({"source": "lane_E", "target": "lane_C", "type": "escalate_federal", "color": "#ff884444", "layer": "lanes"})
    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 5: Evidence Arsenal ───────────────────────────────────────────
def layer_evidence(conn):
    print("[5/10] Evidence Arsenal...")
    nodes, links = [], []
    imp_rows = safe_query(conn, """
        SELECT category, COUNT(*) as cnt FROM impeachment_matrix
        GROUP BY category ORDER BY cnt DESC LIMIT 15
    """)
    for i, r in enumerate(imp_rows):
        nodes.append({
            "id": f"imp_{i}", "label": f"IMP: {r['category']}",
            "layer": "evidence", "group": "impeachment",
            "desc": f"{r['cnt']} impeachment items",
            "color": "#ff2266", "size": max(5, r["cnt"] // 50)
        })
    con_rows = safe_query(conn, """
        SELECT COALESCE(lane,'?') as lane, COUNT(*) as cnt FROM contradiction_map
        GROUP BY lane ORDER BY cnt DESC LIMIT 10
    """)
    for i, r in enumerate(con_rows):
        nodes.append({
            "id": f"con_{i}", "label": f"CONTRADICTIONS: Lane {r['lane']}",
            "layer": "evidence", "group": "contradiction",
            "desc": f"{r['cnt']} contradictions",
            "color": "#ff8800", "size": max(5, r["cnt"] // 40)
        })
    jv_rows = safe_query(conn, """
        SELECT COALESCE(violation_type,'unknown') as vt, COUNT(*) as cnt
        FROM judicial_violations GROUP BY violation_type ORDER BY cnt DESC LIMIT 8
    """)
    for i, r in enumerate(jv_rows):
        nodes.append({
            "id": f"jv_{i}", "label": f"JV: {r['vt'][:30]}",
            "layer": "evidence", "group": "judicial_violation",
            "desc": f"{r['cnt']} judicial violations",
            "color": "#ff0000", "size": max(5, r["cnt"] // 80)
        })
    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 6: System Architecture ────────────────────────────────────────
def layer_system(conn):
    print("[6/10] System Architecture...")
    nodes, links = [], []
    engines = [
        ("nexus", "Cross-table fusion", "#00ff99"),
        ("chimera", "Multi-source blending", "#00cc88"),
        ("chronos", "Timeline construction", "#00aa77"),
        ("cerberus", "Filing validation", "#009966"),
        ("filing_engine", "F1-F10 pipeline", "#008855"),
        ("intake", "Document intake", "#007744"),
        ("rebuttal", "Argument rebuttal", "#006633"),
        ("narrative", "Statement of Facts", "#005522"),
        ("delta999", "8 specialized agents", "#00ff44"),
        ("analytics", "DuckDB 10-100×", "#ffaa00"),
        ("semantic", "LanceDB 75K vectors", "#ff6600"),
        ("search", "tantivy hybrid", "#ff4400"),
        ("typst", "Court-ready PDFs", "#ff2200"),
        ("ingest", "Go 8-worker goroutines", "#ff0000"),
    ]
    for i, (name, desc, color) in enumerate(engines):
        nodes.append({
            "id": f"eng_{i}", "label": name, "layer": "system",
            "group": "engine", "desc": desc, "color": color, "size": 9
        })
    # Engine interconnection links
    pairs = [(0,5),(0,1),(0,2),(0,3),(3,4),(5,13),(10,11),(9,0)]
    for a, b in pairs:
        links.append({
            "source": f"eng_{a}", "target": f"eng_{b}",
            "type": "data_flow", "color": "#00ff9933", "layer": "system"
        })
    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 7: FRED Governance ────────────────────────────────────────────
def layer_fred(conn):
    print("[7/10] FRED Governance Hierarchy...")
    nodes, links = [], []
    fred_modules = [
        ("FRED_PRIME", "Original litigation system", "genesis", "#ff00ff"),
        ("FRED_MONOLITH_v3", "Unified monolith build", "evolution", "#dd00ee"),
        ("FRED_CEPS_SUPREME_v1.0", "LOCKED immutable core — procedural compliance", "core", "#cc00dd"),
        ("FRED_CEPS_SUPREME_v1.1", "5 extended modules", "core", "#bb00cc"),
        ("FRED_CEPS_INIT", "Michigan compliance init", "core", "#aa00bb"),
        ("FRED_PREDATOR_v4", "Evidence-parsing + GUI launcher", "advanced", "#9900aa"),
        ("Semantic_Tagging", "MCR/MCL/Benchbook authority tagging", "module", "#8800bb"),
        ("Form_Matching", "SCAO form → rule → statute triangulation", "module", "#7700cc"),
        ("Motion_Gen", "Court-ready motion generation", "module", "#6600dd"),
        ("Red_Flag_Detection", "Contamination + hallucination scanner", "module", "#5500ee"),
        ("Exhibit_Embed_Positioner", "v1.1 — exhibit placement engine", "module", "#4400ff"),
        ("Relief_Type_Mapper", "v1.1 — relief → vehicle routing", "module", "#3300ff"),
        ("Trial_Suppression_Detector", "v1.1 — excluded evidence detector", "module", "#2200ff"),
        ("HEARING_DEFENSE_SIM", "INIT — hearing simulation engine", "module", "#1100ff"),
        ("PSYOP_FORENSICS", "INIT — adversary psych-ops analysis", "module", "#0000ff"),
        ("QA_Engine_12Gates", "Current: 12 validation gates (absorbed FRED)", "active", "#00ffff"),
    ]
    for i, (name, desc, group, color) in enumerate(fred_modules):
        nodes.append({
            "id": f"fred_{i}", "label": name, "layer": "fred",
            "group": group, "desc": desc, "color": color,
            "size": 12 if group in ("core","active") else 8
        })
    # Evolution links: PRIME → MONOLITH → CEPS 1.0 → 1.1 → INIT → PREDATOR
    evo = [(0,1),(1,2),(2,3),(3,4),(2,5)]
    for a,b in evo:
        links.append({"source":f"fred_{a}","target":f"fred_{b}","type":"evolved_into","color":"#ff00ff88","layer":"fred"})
    # Module ownership: CEPS 1.0 owns base modules, 1.1 owns extended, INIT owns advanced
    for m in [6,7,8,9]:
        links.append({"source":"fred_2","target":f"fred_{m}","type":"contains_module","color":"#cc00dd44","layer":"fred"})
    for m in [10,11,12]:
        links.append({"source":"fred_3","target":f"fred_{m}","type":"extended_module","color":"#bb00cc44","layer":"fred"})
    for m in [13,14]:
        links.append({"source":"fred_4","target":f"fred_{m}","type":"init_module","color":"#aa00bb44","layer":"fred"})
    # FRED absorbed into QA Engine
    links.append({"source":"fred_2","target":"fred_15","type":"absorbed_into","color":"#00ffff88","layer":"fred"})
    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 8: MEEK Lane Routing ──────────────────────────────────────────
def layer_meek(conn):
    print("[8/10] MEEK Lane Routing...")
    nodes, links = [], []
    tracks = [
        ("MEEK1", "Infrastructure / Housing (Lane B)", "#88ff44"),
        ("MEEK2", "Custody / Parenting Time (Lane A)", "#4488ff"),
        ("MEEK3", "PPO / Appeals (Lane D/F)", "#ff44ff"),
        ("MEEK4", "Judicial Disqualification / JTC (Lane E)", "#ff4444"),
    ]
    for i, (tid, desc, color) in enumerate(tracks):
        nodes.append({
            "id": f"meek_{i}", "label": tid, "layer": "meek",
            "group": "track", "desc": desc, "color": color, "size": 14
        })
    # Vehicle types
    vehicles = [
        ("MEEK2_MotionModifyPT", "Motion to Modify Parenting Time", 1, "#4488ff"),
        ("MEEK3_MotionTerminatePPO", "Motion to Modify/Terminate PPO", 2, "#ff44ff"),
        ("MEEK3_AppealOfRight", "Claim of Appeal (PPO)", 2, "#ff44ff"),
        ("MEEK4_MotionDisqualify", "Motion to Disqualify Judge", 3, "#ff4444"),
        ("MEEK4_JTC_Request", "JTC Request for Investigation", 3, "#ff4444"),
    ]
    for i, (vid, desc, track_idx, color) in enumerate(vehicles):
        nid = f"veh_{i}"
        nodes.append({
            "id": nid, "label": vid.split("_",1)[1], "layer": "meek",
            "group": "vehicle", "desc": desc, "color": color, "size": 8
        })
        links.append({
            "source": f"meek_{track_idx}", "target": nid,
            "type": "routes_to", "color": color + "66", "layer": "meek"
        })
    # Risk event types
    risks = [
        ("PPO_NoSpecificReasons", "Severity 70 — curable defect", 2, "#ff880088"),
        ("PPO_NoHearingRequest", "Severity 55 — dismissal risk", 2, "#ff660088"),
        ("MissingOperativeOrder", "Severity varies — all tracks", -1, "#ff440088"),
    ]
    for i, (rid, desc, track_idx, color) in enumerate(risks):
        nid = f"risk_{i}"
        nodes.append({
            "id": nid, "label": f"⚠ {rid}", "layer": "meek",
            "group": "risk", "desc": desc, "color": "#ff8800", "size": 6
        })
        if track_idx >= 0:
            links.append({"source":f"meek_{track_idx}","target":nid,"type":"raises_risk","color":color,"layer":"meek"})

    # MEEK graph schema nodes
    schema_nodes = ["Case","Court","Party","Order","Hearing","Motion","EvidenceAtom","DeadlineClock","RiskEvent","VehicleCandidate","AuthorityRef"]
    for i, sn in enumerate(schema_nodes):
        nodes.append({
            "id": f"schema_{i}", "label": f"📋 {sn}", "layer": "meek",
            "group": "schema", "desc": f"MEEK graph node type: {sn}",
            "color": "#aaddff", "size": 5
        })

    # DocForge connection
    nodes.append({
        "id": "docforge", "label": "DocForge v19", "layer": "meek",
        "group": "output", "desc": "MEEK → DocForge → CourtPack (DOCX/PDF)",
        "color": "#00ffaa", "size": 12
    })
    for i in range(4):
        links.append({"source":f"meek_{i}","target":"docforge","type":"feeds_docforge","color":"#00ffaa44","layer":"meek"})

    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 9: Event Horizon Pipeline ─────────────────────────────────────
def layer_event_horizon(conn):
    print("[9/10] Event Horizon Δ∞ Pipeline...")
    nodes, links = [], []
    subsystems = [
        ("GENESIS", "Deep filesystem scanner", "#ff0000"),
        ("ORACLE", "Routing decision engine", "#ff3300"),
        ("PROMETHEAN", "Execution engine (moves/actions)", "#ff6600"),
        ("ELYSIUM", "Quality validation + pre/post checks", "#ff9900"),
        ("HYDRA", "Multi-headed error recovery", "#ffcc00"),
        ("OUROBOROS", "Self-referential cycle detection", "#ffff00"),
        ("ESCHATON", "End-state convergence checker", "#ccff00"),
        ("SUPERNOVA", "High-energy burst processing", "#99ff00"),
        ("EMERGENCE", "Pattern emergence detector", "#66ff00"),
        ("TRANSCENDENT", "Cross-system integration", "#33ff00"),
        ("APOTHEOSIS", "Final ascension — quality score", "#00ff00"),
        ("StateDB", "Persistent state + WAL logs", "#00ffff"),
    ]
    for i, (name, desc, color) in enumerate(subsystems):
        nodes.append({
            "id": f"eh_{i}", "label": name, "layer": "event_horizon",
            "group": "subsystem" if i < 11 else "state",
            "desc": f"Event Horizon v1.5.0 — {desc}",
            "color": color, "size": 10
        })
    # Pipeline sequence: GENESIS → ORACLE → ... → APOTHEOSIS
    for i in range(10):
        links.append({
            "source": f"eh_{i}", "target": f"eh_{i+1}",
            "type": "pipeline_next", "color": "#ffffff44", "layer": "event_horizon"
        })
    # StateDB connects to all
    for i in range(11):
        links.append({
            "source": f"eh_{11}", "target": f"eh_{i}",
            "type": "persists_state", "color": "#00ffff22", "layer": "event_horizon"
        })
    # Confidence tiers
    tiers = [
        ("GREEN", "High confidence routing", "#00ff00"),
        ("YELLOW", "Moderate — needs review", "#ffff00"),
        ("ORANGE", "Low confidence — flagged", "#ff8800"),
        ("RED", "Critical — manual required", "#ff0000"),
    ]
    for i, (name, desc, color) in enumerate(tiers):
        nodes.append({
            "id": f"tier_{i}", "label": f"Tier: {name}", "layer": "event_horizon",
            "group": "confidence_tier", "desc": desc, "color": color, "size": 6
        })
        links.append({"source":"eh_1","target":f"tier_{i}","type":"classifies","color":color+"44","layer":"event_horizon"})

    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 10: Brain Network ─────────────────────────────────────────────
def layer_brains(conn):
    print("[10/10] Brain Network (23 registered)...")
    nodes, links = [], []
    rows = safe_query(conn, """
        SELECT db_name, db_path, size_mb, integration_status FROM brain_registry ORDER BY size_mb DESC
    """)
    status_colors = {
        "connected": "#00ff88",
        "integrated": "#00ffcc",
        "discovered": "#ffaa00",
    }
    for i, r in enumerate(rows):
        name = r["db_name"].replace(".db","")
        sz = r["size_mb"] or 0
        status = r["integration_status"] or "discovered"
        color = status_colors.get(status, "#888888")
        nodes.append({
            "id": f"brain_{i}", "label": name, "layer": "brains",
            "group": status, "desc": f"{sz:.1f} MB | Status: {status}",
            "color": color, "size": max(5, min(16, int(sz ** 0.4 * 3)))
        })

    # Hub: litigation_context.db
    nodes.append({
        "id": "brain_hub", "label": "litigation_context.db", "layer": "brains",
        "group": "hub", "desc": "Central hub — 790+ tables, ~1.3 GB",
        "color": "#ffffff", "size": 18
    })
    # Connect all brains to hub
    for i in range(len(rows)):
        links.append({
            "source": "brain_hub", "target": f"brain_{i}",
            "type": "federates", "color": "#ffffff22", "layer": "brains"
        })
    # Brain type clusters
    brain_types = {
        "AI Brains": ["chat_intelligence_brain","interpretation_brain","narrative_brain","authority_brain","claims_brain","entity_brain","contradictions"],
        "Evidence DBs": ["master_index","cross_brain_index","ocr_master","pdf_master_index","ec","claim_evidence_links"],
        "Filing DBs": ["lane_A_custody","litigation_lite","litigation_skills","michigan_judicial_system"],
        "System DBs": ["event_horizon","script_forge_1","dup_drive_inventory","dedup_index_1"],
    }
    name_to_brain = {r["db_name"].replace(".db",""): f"brain_{i}" for i, r in enumerate(rows)}
    cluster_id = 0
    for cluster_name, members in brain_types.items():
        cnid = f"bcluster_{cluster_id}"
        nodes.append({
            "id": cnid, "label": f"🧠 {cluster_name}", "layer": "brains",
            "group": "cluster", "desc": f"Brain cluster: {cluster_name}",
            "color": "#aaaaff", "size": 7
        })
        for m in members:
            if m in name_to_brain:
                links.append({"source":cnid,"target":name_to_brain[m],"type":"cluster_member","color":"#aaaaff33","layer":"brains"})
        cluster_id += 1

    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links


# ── LAYER 11: Weaponization Chains ──────────────────────────────────────
def layer_weapons(conn):
    print("[11/13] Weaponization Chains...")
    nodes, links = [], []
    WTYPE_COLORS = {
        "FALSE_ALLEGATION": "#ff0044",
        "EX_PARTE": "#ff4400",
        "PPO_WEAPONIZATION": "#ff8800",
        "PARENTAL_ALIENATION": "#aa00ff",
        "PARENTING_TIME_DENIAL": "#0088ff",
        "EVIDENCE_SUPPRESSION": "#ff00aa",
        "CONTEMPT_ABUSE": "#ffcc00",
        "JUDICIAL_BIAS": "#ff0000",
        "DUE_PROCESS_VIOLATION": "#ff6600",
    }
    # Adversary x weapon_type aggregates
    rows = safe_query(conn, """
        SELECT adversary, weapon_type, COUNT(*) as cnt, ROUND(AVG(severity),1) as avg_sev,
               SUM(CASE WHEN severity >= 9 THEN 1 ELSE 0 END) as critical
        FROM weapon_chains
        GROUP BY adversary, weapon_type
        HAVING cnt >= 3
        ORDER BY cnt DESC LIMIT 40
    """)
    adv_nodes = {}
    for i, r in enumerate(rows):
        adv = r["adversary"]
        wt = r["weapon_type"]
        cnt = r["cnt"]
        avg_s = r["avg_sev"] or 7
        crit = r["critical"] or 0
        nid = f"wc_{i}"
        color = WTYPE_COLORS.get(wt, "#ff4444")
        sz = max(5, min(20, int(cnt ** 0.45 * 3)))
        short_wt = wt.replace("_", " ").title()[:20]
        nodes.append({
            "id": nid, "label": f"{adv}: {short_wt} ({cnt})", "layer": "weapons",
            "group": wt, "desc": f"{cnt} chains | Avg severity: {avg_s} | Critical: {crit}",
            "color": color, "size": sz, "role": adv
        })
        if adv not in adv_nodes:
            adv_nodes[adv] = []
        adv_nodes[adv].append(nid)

    # Link same-adversary weapon nodes
    for adv, nids in adv_nodes.items():
        for j in range(len(nids) - 1):
            links.append({
                "source": nids[j], "target": nids[j+1],
                "type": "same_adversary_chain", "color": "#ff004422", "layer": "weapons"
            })

    # Top 25 critical individual chains
    hot = safe_query(conn, """
        SELECT chain_id, adversary, weapon_type, instance, severity, date
        FROM weapon_chains WHERE severity >= 9
        ORDER BY severity DESC, date DESC LIMIT 25
    """)
    for i, r in enumerate(hot):
        nid = f"whot_{i}"
        wt = r["weapon_type"] or "UNKNOWN"
        color = WTYPE_COLORS.get(wt, "#ff4444")
        inst = (r["instance"] or "")[:60]
        nodes.append({
            "id": nid, "label": f"★ {r['adversary']}: {inst}", "layer": "weapons",
            "group": "critical_chain", "desc": f"Severity {r['severity']} | {r['date']} | {wt}",
            "color": color, "size": 5
        })
        # Link to parent adversary-weapon aggregate if exists
        for pnid in adv_nodes.get(r["adversary"], []):
            parent_node = next((n for n in nodes if n["id"] == pnid and wt in n.get("group","")), None)
            if parent_node:
                links.append({"source": pnid, "target": nid, "type": "critical_instance", "color": color + "44", "layer": "weapons"})
                break

    # Weapon type summary hub nodes
    wtotals = safe_query(conn, """
        SELECT weapon_type, COUNT(*) as cnt FROM weapon_chains GROUP BY weapon_type ORDER BY cnt DESC
    """)
    for i, r in enumerate(wtotals):
        wt = r["weapon_type"]
        nid = f"whub_{i}"
        color = WTYPE_COLORS.get(wt, "#ff4444")
        nodes.append({
            "id": nid, "label": f"⚡ {wt.replace('_',' ')} ({r['cnt']})", "layer": "weapons",
            "group": "weapon_hub", "desc": f"Total: {r['cnt']} chains across all adversaries",
            "color": color, "size": 14
        })

    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 12: Police Reports ───────────────────────────────────────────
def layer_police(conn):
    print("[12/13] Police Reports...")
    nodes, links = [], []

    # Aggregate by adversary mention
    adversary_kw = {
        "Watson": ["%watson%", "%emily%"],
        "Albert Watson": ["%albert%"],
        "McNeill": ["%mcneill%"],
        "Rusco": ["%rusco%"],
        "Berry": ["%berry%"],
    }
    agg_nodes = {}
    for person, patterns in adversary_kw.items():
        conditions = " OR ".join(f"LOWER(COALESCE(allegations,'') || ' ' || COALESCE(filename,'') || ' ' || COALESCE(officers,'') || ' ' || COALESCE(entities,'')) LIKE '{p}'" for p in patterns)
        rows = safe_query(conn, f"SELECT COUNT(*) as cnt FROM police_reports WHERE {conditions}")
        cnt = rows[0]["cnt"] if rows else 0
        if cnt > 0:
            nid = f"pr_agg_{person.replace(' ','_')}"
            nodes.append({
                "id": nid, "label": f"🚨 {person}: {cnt} reports", "layer": "police",
                "group": "aggregate", "desc": f"{cnt} police reports mentioning {person}",
                "color": "#0088ff", "size": max(6, min(18, int(cnt ** 0.35 * 4)))
            })
            agg_nodes[person] = nid

    # Total reports summary
    total_rows = safe_query(conn, "SELECT COUNT(*) as cnt FROM police_reports")
    total = total_rows[0]["cnt"] if total_rows else 0
    nodes.append({
        "id": "pr_total", "label": f"📋 Total: {total} Reports", "layer": "police",
        "group": "summary", "desc": f"{total} police reports indexed — ZERO arrests across all contacts",
        "color": "#00aaff", "size": 16
    })
    for nid in agg_nodes.values():
        links.append({"source": "pr_total", "target": nid, "type": "contains_mentions", "color": "#0088ff33", "layer": "police"})

    # Top 20 individual reports
    reports = safe_query(conn, """
        SELECT id, filename, dates, allegations, incident_numbers, officers
        FROM police_reports
        WHERE allegations IS NOT NULL AND LENGTH(allegations) > 5
        ORDER BY id LIMIT 20
    """)
    for i, r in enumerate(reports):
        nid = f"pr_{i}"
        fn = (r["filename"] or "")[:30]
        allg = (r["allegations"] or "")[:80]
        dt = (r["dates"] or "unknown")[:20]
        inc = (r["incident_numbers"] or "")[:20]
        nodes.append({
            "id": nid, "label": f"📄 {inc or fn}", "layer": "police",
            "group": "report", "desc": f"Date: {dt} | {allg}",
            "color": "#2288cc", "size": 5
        })
        # Link to aggregate nodes based on content
        content = (str(r["filename"]) + str(r["allegations"]) + str(r["officers"])).lower()
        for person, kws in adversary_kw.items():
            for kw in kws:
                if kw.strip("%") in content:
                    if person in agg_nodes:
                        links.append({"source": agg_nodes[person], "target": nid, "type": "mentioned_in", "color": "#0088ff22", "layer": "police"})
                    break

    # Zero arrests marker
    nodes.append({
        "id": "pr_zero_arrests", "label": "✅ ZERO ARRESTS / CHARGES", "layer": "police",
        "group": "exculpatory", "desc": "Across ALL police contacts — no arrests, no charges, no evidence of wrongdoing",
        "color": "#00ff88", "size": 12
    })
    links.append({"source": "pr_total", "target": "pr_zero_arrests", "type": "outcome", "color": "#00ff8844", "layer": "police"})

    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links

# ── LAYER 13: Doctrine/Remedy Map ──────────────────────────────────────
def layer_doctrine(conn):
    print("[13/13] Doctrine/Remedy Map...")
    nodes, links = [], []

    doctrines = [
        ("MCR 2.114(D)", "Sanctions for false statements", "rule", "#00ffcc"),
        ("MRE 608/613", "Impeachment — prior inconsistent", "evidence", "#00ddaa"),
        ("MCR 2.119(B)", "Motion practice — notice required", "rule", "#00ffcc"),
        ("Mathews v Eldridge", "Due process balancing test", "case", "#ff88ff"),
        ("MCL 600.2950", "Personal Protection Orders", "statute", "#ffcc00"),
        ("MCR 3.707", "PPO issuance/modification", "rule", "#00ffcc"),
        ("MCL 722.23(j)", "Factor j — facilitate relationship", "statute", "#ffcc00"),
        ("Pierron v Pierron", "486 Mich 81 — custody due process", "case", "#ff88ff"),
        ("MCL 722.27a", "Parenting time statute", "statute", "#ffcc00"),
        ("Brown v Loveman", "260 Mich App 576 — PT enforcement", "case", "#ff88ff"),
        ("MRE 402/702/901", "Evidence admissibility rules", "evidence", "#00ddaa"),
        ("MCL 600.1701", "Contempt statute", "statute", "#ffcc00"),
        ("In re Dougherty", "Contempt standard of review", "case", "#ff88ff"),
        ("MCR 2.003(C)(1)(b)", "Disqualification for bias", "rule", "#00ffcc"),
        ("Canon 2/3", "Judicial conduct canons", "canon", "#ff6644"),
        ("US Const Amend XIV", "Due Process Clause", "constitutional", "#ffffff"),
        ("Troxel v Granville", "Parental rights fundamental", "case", "#ff88ff"),
        ("42 USC 1983", "Federal civil rights", "federal", "#ff4444"),
        ("Vodvarka v Grasmeyer", "Changed circumstances standard", "case", "#ff88ff"),
        ("MCR 7.306", "Superintending control — MSC", "rule", "#00ffcc"),
        ("MSC AO 2016-5", "Anti-nepotism policy", "admin_order", "#ff8844"),
        ("MCL 722.23", "Best interest factors (all 12)", "statute", "#ffcc00"),
    ]
    TYPE_COLORS = {"rule": "#00ffcc", "evidence": "#00ddaa", "case": "#ff88ff",
                   "statute": "#ffcc00", "canon": "#ff6644", "constitutional": "#ffffff",
                   "federal": "#ff4444", "admin_order": "#ff8844"}
    for i, (name, desc, dtype, color) in enumerate(doctrines):
        nid = f"doc_{i}"
        nodes.append({
            "id": nid, "label": f"📜 {name}", "layer": "doctrine",
            "group": dtype, "desc": desc, "color": color, "size": 8
        })

    # Remedies
    remedies = [
        ("Sanctions", "MCR 2.114(D)/7.216(D)", "#00ff88", "Filing false statements"),
        ("Disqualification", "MCR 2.003 — remove judge", "#ff4444", "Judicial bias"),
        ("Contempt", "MCL 600.1701 — enforce orders", "#ffcc00", "Order violations"),
        ("PPO Termination", "MCR 3.707(B)", "#ff88ff", "Weaponized PPO"),
        ("Custody Modification", "MCR 3.206 — changed circ.", "#4488ff", "Parenting time"),
        ("Federal 1983", "42 USC 1983 — constitutional", "#ff0000", "State actor violations"),
        ("MSC Superintending", "MCR 7.306 — original action", "#ffffff", "Systemic corruption"),
        ("JTC Complaint", "Judicial Tenure Commission", "#ff6600", "Judicial misconduct"),
        ("Emergency PT Restore", "MCL 722.27a — immediate", "#00aaff", "Child separation"),
        ("Appeal of Right", "MCR 7.204 — COA 366810", "#cc88ff", "Trial error correction"),
        ("Habeas Corpus", "MCL 600.4301 + art 1 s 12", "#ffaaff", "Wrongful detention/custody"),
    ]
    for i, (name, auth, color, desc) in enumerate(remedies):
        nid = f"rem_{i}"
        nodes.append({
            "id": nid, "label": f"⚖ {name}", "layer": "doctrine",
            "group": "remedy", "desc": f"{auth} — {desc}", "color": color, "size": 10
        })

    # Doctrine → Remedy links
    doc_rem_links = [
        (0, 0), (1, 0),   # MCR 2.114, MRE 608 → Sanctions
        (13, 1), (14, 1),  # MCR 2.003, Canon 2/3 → Disqualification
        (11, 2), (12, 2),  # MCL 600.1701, Dougherty → Contempt
        (4, 3), (5, 3),    # MCL 600.2950, MCR 3.707 → PPO Termination
        (6, 4), (7, 4), (8, 4),  # MCL 722.23(j), Pierron, MCL 722.27a → Custody Mod
        (15, 5), (17, 5),  # US Const XIV, 42 USC 1983 → Federal 1983
        (19, 6), (20, 6),  # MCR 7.306, AO 2016-5 → MSC Superintending
        (14, 7),           # Canon 2/3 → JTC Complaint
        (8, 8), (9, 8),   # MCL 722.27a, Brown → Emergency PT
        (18, 9),           # Vodvarka → Appeal of Right
        (15, 10), (16, 10),  # US Const XIV, Troxel → Habeas
    ]
    for d_idx, r_idx in doc_rem_links:
        if d_idx < len(doctrines) and r_idx < len(remedies):
            links.append({
                "source": f"doc_{d_idx}", "target": f"rem_{r_idx}",
                "type": "authorizes_remedy", "color": "#00ffcc33", "layer": "doctrine"
            })

    # Weapon type → Doctrine mapping hub
    wt_doctrine = {
        "FALSE_ALLEGATION": [0, 1, 21],
        "EX_PARTE": [2, 15, 3],
        "PPO_WEAPONIZATION": [4, 5],
        "PARENTAL_ALIENATION": [6, 7, 8],
        "PARENTING_TIME_DENIAL": [8, 9],
        "EVIDENCE_SUPPRESSION": [10, 1],
        "CONTEMPT_ABUSE": [11, 12],
        "JUDICIAL_BIAS": [13, 14, 20],
        "DUE_PROCESS_VIOLATION": [15, 16, 17],
    }
    for wt, doc_indices in wt_doctrine.items():
        wt_nid = f"wt_hub_{wt}"
        nodes.append({
            "id": wt_nid, "label": f"🔗 {wt.replace('_',' ')}", "layer": "doctrine",
            "group": "weapon_type_hub", "desc": f"Weapon type connector — links doctrine to weapon chains",
            "color": "#ff444488", "size": 6
        })
        for di in doc_indices:
            if di < len(doctrines):
                links.append({"source": f"doc_{di}", "target": wt_nid, "type": "applies_to", "color": "#ff444422", "layer": "doctrine"})

    print(f"  → {len(nodes)} nodes, {len(links)} links")
    return nodes, links


# ═══════════════════════════════════════════════════════════════════════
# CROSS-LAYER LINKS — Wire the 13 layers together
# ═══════════════════════════════════════════════════════════════════════
def cross_layer_links(all_nodes):
    print("[CROSS] Wiring cross-layer links...")
    links = []
    nmap = {n["id"]: n for n in all_nodes}

    # MEEK tracks → Case Lanes
    meek_lane = [("meek_0","lane_B"),("meek_1","lane_A"),("meek_2","lane_D"),("meek_3","lane_E")]
    for src, tgt in meek_lane:
        if src in nmap and tgt in nmap:
            links.append({"source":src,"target":tgt,"type":"routes_to_lane","color":"#ffffff15","layer":"cross"})

    # FRED QA Engine → Filing Pipeline (validates all filings)
    for n in all_nodes:
        if n["layer"] == "filing" and "fred_15" in nmap:
            links.append({"source":"fred_15","target":n["id"],"type":"validates","color":"#00ffff10","layer":"cross"})

    # Event Horizon GENESIS → Brain hub (scans all DBs)
    if "eh_0" in nmap and "brain_hub" in nmap:
        links.append({"source":"eh_0","target":"brain_hub","type":"scans","color":"#ff000022","layer":"cross"})

    # DocForge → Filing Pipeline
    if "docforge" in nmap:
        for n in all_nodes:
            if n["layer"] == "filing":
                links.append({"source":"docforge","target":n["id"],"type":"generates","color":"#00ffaa10","layer":"cross"})
                break

    # Adversary "McNeill" → Lane E (misconduct)
    for n in all_nodes:
        if n["layer"] == "adversary" and "McNeill" in n.get("label",""):
            if "lane_E" in nmap:
                links.append({"source":n["id"],"target":"lane_E","type":"subject_of","color":"#ff444422","layer":"cross"})
            break

    # Adversary "Emily" → Lane A (custody)
    for n in all_nodes:
        if n["layer"] == "adversary" and "Emily" in n.get("label",""):
            if "lane_A" in nmap:
                links.append({"source":n["id"],"target":"lane_A","type":"defendant_in","color":"#ff660022","layer":"cross"})
            break

    # ── NEW v4 cross-links ──

    # Weapon chain adversary nodes → Adversary network nodes
    adv_name_to_node = {}
    for n in all_nodes:
        if n["layer"] == "adversary" and n.get("group") == "person":
            adv_name_to_node[n.get("label","")] = n["id"]
    for n in all_nodes:
        if n["layer"] == "weapons" and n.get("role"):
            for aname, anid in adv_name_to_node.items():
                if n["role"] in aname or aname.startswith(n["role"]):
                    links.append({"source":anid,"target":n["id"],"type":"weaponized_by","color":"#ff004415","layer":"cross"})
                    break

    # Weapon hub types → Case Lanes
    weapon_lane_map = {
        "FALSE_ALLEGATION": "lane_A", "EX_PARTE": "lane_E", "PPO_WEAPONIZATION": "lane_D",
        "PARENTAL_ALIENATION": "lane_A", "PARENTING_TIME_DENIAL": "lane_A",
        "EVIDENCE_SUPPRESSION": "lane_E", "CONTEMPT_ABUSE": "lane_E",
        "JUDICIAL_BIAS": "lane_E", "DUE_PROCESS_VIOLATION": "lane_C",
    }
    for n in all_nodes:
        if n["layer"] == "weapons" and n.get("group") == "weapon_hub":
            for wt, lane_id in weapon_lane_map.items():
                if wt.replace("_"," ") in n.get("label","").upper():
                    if lane_id in nmap:
                        links.append({"source":n["id"],"target":lane_id,"type":"targets_lane","color":"#ff444415","layer":"cross"})
                    break

    # Police aggregate → Adversary nodes
    for n in all_nodes:
        if n["layer"] == "police" and n.get("group") == "aggregate":
            for aname, anid in adv_name_to_node.items():
                if any(k in aname for k in n.get("label","").split(":")):
                    links.append({"source":n["id"],"target":anid,"type":"police_contact","color":"#0088ff15","layer":"cross"})
                    break

    # Police total → Evidence arsenal (impeachment source)
    if "pr_total" in nmap:
        for n in all_nodes:
            if n["layer"] == "evidence" and "impeachment" in n.get("group",""):
                links.append({"source":"pr_total","target":n["id"],"type":"feeds_impeachment","color":"#0088ff15","layer":"cross"})
                break

    # Doctrine remedies → Filing pipeline nodes
    remedy_filing_map = {
        "rem_0": ["F3"],  # Sanctions → F3
        "rem_1": ["F5"],  # Disqualification → F5
        "rem_4": ["F1"],  # Custody Mod → F1
        "rem_5": ["F8"],  # Federal 1983 → F8
        "rem_6": ["F9"],  # MSC → F9
        "rem_7": ["F10"], # JTC → F10
        "rem_8": ["F1"],  # Emergency PT → F1
        "rem_9": ["F7"],  # Appeal → F7
    }
    for rem_id, filing_ids in remedy_filing_map.items():
        if rem_id in nmap:
            for n in all_nodes:
                if n["layer"] == "filing":
                    fid = n.get("label","").split("(")[-1].rstrip(")").strip() if "(" in n.get("label","") else ""
                    nfid = n.get("id","")
                    for target_fid in filing_ids:
                        if target_fid.lower() in nfid.lower() or target_fid in n.get("label",""):
                            links.append({"source":rem_id,"target":n["id"],"type":"remedy_via_filing","color":"#00ffcc15","layer":"cross"})

    # Weapon type hubs (doctrine layer) → Weapon hub nodes (weapons layer)
    for n in all_nodes:
        if n["layer"] == "doctrine" and n.get("group") == "weapon_type_hub":
            wt_name = n.get("label","").replace("🔗 ","").strip().upper().replace(" ","_")
            for w in all_nodes:
                if w["layer"] == "weapons" and w.get("group") == "weapon_hub":
                    if wt_name in w.get("label","").upper().replace(" ","_"):
                        links.append({"source":n["id"],"target":w["id"],"type":"doctrine_to_weapon","color":"#ff444415","layer":"cross"})
                        break

    print(f"  → {len(links)} cross-layer links")
    return links


# ═══════════════════════════════════════════════════════════════════════
# HTML TEMPLATE — D3.js v7 Force-Directed 10-Layer Mega-Visualization
# ═══════════════════════════════════════════════════════════════════════
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>THEMANBEARPIG v4.0 — 13-Layer Litigation Intelligence Weapon System</title>
<script src="https://d3js.org/d3.v7.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=JetBrains+Mono:wght@300;400;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#060a14;color:#c0d0e0;font-family:'JetBrains Mono',monospace;overflow:hidden}
#viz{width:100vw;height:100vh;position:relative}
svg{width:100%;height:100%}
.scanline{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,255,200,0.015) 2px,rgba(0,255,200,0.015) 4px);z-index:999}

/* HUD Panel */
#hud{position:fixed;top:12px;left:12px;z-index:100;font-size:11px;pointer-events:none}
#hud h1{font-family:'Orbitron',sans-serif;font-size:18px;color:#00ffc8;text-shadow:0 0 20px #00ffc866;letter-spacing:3px}
#hud .subtitle{font-size:10px;color:#5588aa;margin-top:2px;letter-spacing:1px}
#hud .stat{color:#88aacc;margin-top:4px}
#hud .stat b{color:#00ffc8}

/* Layer Controls */
#controls{position:fixed;top:12px;right:12px;z-index:100;background:rgba(6,10,20,0.92);
  border:1px solid #00ffc833;border-radius:8px;padding:10px 14px;backdrop-filter:blur(8px)}
#controls h3{font-family:'Orbitron',sans-serif;font-size:11px;color:#00ffc8;margin-bottom:8px;letter-spacing:2px}
.layer-btn{display:flex;align-items:center;gap:6px;padding:3px 0;cursor:pointer;user-select:none;font-size:10px}
.layer-btn .dot{width:10px;height:10px;border-radius:50%;border:1px solid #ffffff33;transition:all 0.3s}
.layer-btn.active .dot{box-shadow:0 0 8px currentColor}
.layer-btn.inactive{opacity:0.35}
.layer-btn.inactive .dot{background:transparent !important}
.layer-btn span{color:#88aacc;transition:color 0.3s}
.layer-btn.active span{color:#c0e0f0}

/* Info Panel */
#info{position:fixed;bottom:12px;left:12px;z-index:100;background:rgba(6,10,20,0.92);
  border:1px solid #00ffc833;border-radius:8px;padding:12px 16px;max-width:400px;
  backdrop-filter:blur(8px);display:none}
#info h4{font-family:'Orbitron',sans-serif;font-size:12px;color:#00ffc8;margin-bottom:4px}
#info .detail{font-size:10px;color:#88aacc;line-height:1.5}

/* Legend */
#legend{position:fixed;bottom:12px;right:12px;z-index:100;background:rgba(6,10,20,0.92);
  border:1px solid #00ffc833;border-radius:8px;padding:10px 14px;backdrop-filter:blur(8px);font-size:9px}
#legend h3{font-family:'Orbitron',sans-serif;font-size:10px;color:#00ffc8;margin-bottom:6px;letter-spacing:2px}
.leg-item{display:flex;align-items:center;gap:5px;padding:1px 0;color:#88aacc}
.leg-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0}

/* Tooltip */
.tooltip{position:absolute;background:rgba(6,10,20,0.95);border:1px solid #00ffc866;border-radius:6px;
  padding:8px 12px;font-size:10px;pointer-events:none;z-index:200;max-width:320px;
  backdrop-filter:blur(12px);box-shadow:0 0 20px rgba(0,255,200,0.15)}
.tooltip .tt-label{font-family:'Orbitron',sans-serif;color:#00ffc8;font-size:11px;margin-bottom:3px}
.tooltip .tt-layer{color:#5588aa;font-size:9px}
.tooltip .tt-desc{color:#aabbcc;margin-top:3px}
</style>
</head>
<body>
<div id="viz">
  <div class="scanline"></div>
  <div id="hud">
    <h1>▲ THEMANBEARPIG v4.0</h1>
    <div class="subtitle">13-LAYER LITIGATION INTELLIGENCE WEAPON SYSTEM — PIGORS v. WATSON</div>
    <div class="stat"><b>__NODECOUNT__</b> nodes · <b>__LINKCOUNT__</b> links · <b>13</b> layers</div>
    <div class="stat">Separation: <b>__SEP__ days</b> · Evidence: <b>__EVCOUNT__</b> quotes</div>
    <div class="stat">Authorities: <b>__AUTHCOUNT__</b> chains · Violations: <b>__JVCOUNT__</b> · Weapons: <b>__WCOUNT__</b></div>
  </div>
  <div id="controls">
    <h3>▼ LAYERS</h3>
  </div>
  <div id="info"><h4 id="info-title"></h4><div id="info-detail" class="detail"></div></div>
  <div id="legend">
    <h3>◆ LINK TYPES</h3>
  </div>
</div>
<script>
const NODES = __NODES__;
const LINKS = __LINKS__;
const STATS = __STATS__;

const LAYER_META = {
  adversary:     {label:"Adversary Network",    icon:"\u2694",  color:"#ff0040", y:0.08},
  authority:     {label:"Legal Authority",       icon:"\u2696",  color:"#00ffcc", y:0.18},
  filing:        {label:"Filing Pipeline",       icon:"\ud83d\udcc1", color:"#ffaa00", y:0.28},
  lanes:         {label:"Case Lanes",            icon:"\ud83d\udee4",  color:"#4488ff", y:0.38},
  evidence:      {label:"Evidence Arsenal",      icon:"\ud83d\udd2c", color:"#ff2266", y:0.48},
  system:        {label:"System Architecture",   icon:"\u2699",  color:"#00ff99", y:0.56},
  fred:          {label:"FRED Governance",       icon:"\ud83c\udfdb",  color:"#cc00dd", y:0.10},
  meek:          {label:"MEEK Lane Routing",     icon:"\ud83d\uddfa",  color:"#44aaff", y:0.30},
  event_horizon: {label:"Event Horizon \u0394\u221e",     icon:"\ud83c\udf00", color:"#ff6600", y:0.50},
  brains:        {label:"Brain Network",         icon:"\ud83e\udde0", color:"#00ff88", y:0.68},
  weapons:       {label:"Weapon Chains",         icon:"\ud83d\udd25", color:"#ff0044", y:0.78},
  police:        {label:"Police Reports",        icon:"\ud83d\udea8", color:"#0088ff", y:0.88},
  doctrine:      {label:"Doctrine/Remedy",       icon:"\ud83d\udcdc", color:"#00ffcc", y:0.95},
};

const width = window.innerWidth, height = window.innerHeight;
const activeLayers = new Set(Object.keys(LAYER_META));

// Build controls
const ctrl = d3.select("#controls");
Object.entries(LAYER_META).forEach(([key,m]) => {
  const btn = ctrl.append("div").attr("class","layer-btn active").attr("data-layer",key);
  btn.append("div").attr("class","dot").style("background",m.color).style("color",m.color);
  btn.append("span").text(`${m.icon} ${m.label}`);
  btn.on("click", function(){
    if(activeLayers.has(key)){activeLayers.delete(key);d3.select(this).attr("class","layer-btn inactive")}
    else{activeLayers.add(key);d3.select(this).attr("class","layer-btn active")}
    updateVisibility();
  });
});

// Legend
const linkTypes = [...new Set(LINKS.map(l=>l.type))].slice(0,12);
const leg = d3.select("#legend");
linkTypes.forEach(t => {
  const sample = LINKS.find(l=>l.type===t);
  const item = leg.append("div").attr("class","leg-item");
  item.append("div").attr("class","leg-dot").style("background",sample?sample.color:"#888");
  item.append("span").text(t.replace(/_/g," "));
});

// SVG
const svg = d3.select("#viz").append("svg");
const defs = svg.append("defs");
// Glow filter
const glow = defs.append("filter").attr("id","glow").attr("x","-50%").attr("y","-50%").attr("width","200%").attr("height","200%");
glow.append("feGaussianBlur").attr("stdDeviation","3").attr("result","blur");
const feMerge = glow.append("feMerge");
feMerge.append("feMergeNode").attr("in","blur");
feMerge.append("feMergeNode").attr("in","SourceGraphic");

const g = svg.append("g");
const zoom = d3.zoom().scaleExtent([0.15,6]).on("zoom",e=>g.attr("transform",e.transform));
svg.call(zoom);

// Tooltip
const tooltip = d3.select("#viz").append("div").attr("class","tooltip").style("display","none");

// Links
const linkG = g.append("g");
const linkSel = linkG.selectAll("line").data(LINKS).join("line")
  .attr("stroke",d=>d.color||"#ffffff22").attr("stroke-width",d=>d.weight?Math.min(d.weight/3,4):1)
  .attr("stroke-opacity",0.6).attr("data-layer",d=>d.layer);

// Nodes
const nodeG = g.append("g");
const nodeSel = nodeG.selectAll("g").data(NODES).join("g")
  .attr("data-layer",d=>d.layer).attr("cursor","pointer")
  .call(d3.drag().on("start",dragStart).on("drag",dragging).on("end",dragEnd));

nodeSel.append("circle")
  .attr("r",d=>d.size||8).attr("fill",d=>d.color||"#888")
  .attr("stroke",d=>d.color||"#888").attr("stroke-width",1.5)
  .attr("fill-opacity",0.25).attr("filter","url(#glow)");

nodeSel.append("text")
  .text(d=>d.label).attr("dx",d=>(d.size||8)+4).attr("dy",3)
  .attr("font-size",d=> d.size>=12?"10px":"8px")
  .attr("fill",d=>d.color||"#aaa").attr("font-family","'JetBrains Mono',monospace")
  .attr("opacity",0.85);

// Hover
nodeSel.on("mouseover",function(e,d){
  d3.select(this).select("circle").attr("fill-opacity",0.6).attr("stroke-width",3);
  tooltip.style("display","block")
    .html(`<div class="tt-label">${d.label}</div><div class="tt-layer">${(LAYER_META[d.layer]||{}).label||d.layer} · ${d.group||''}</div>${d.desc?'<div class="tt-desc">'+d.desc+'</div>':''}`);
  d3.select("#info").style("display","block");
  d3.select("#info-title").text(d.label);
  d3.select("#info-detail").text(`Layer: ${(LAYER_META[d.layer]||{}).label||d.layer}\nGroup: ${d.group||'—'}\nRole: ${d.role||'—'}\n${d.desc||''}`);
}).on("mousemove",function(e){
  tooltip.style("left",(e.pageX+15)+"px").style("top",(e.pageY-10)+"px");
}).on("mouseout",function(){
  d3.select(this).select("circle").attr("fill-opacity",0.25).attr("stroke-width",1.5);
  tooltip.style("display","none");
});

// Simulation
const sim = d3.forceSimulation(NODES)
  .force("link", d3.forceLink(LINKS).id(d=>d.id).distance(60).strength(0.25))
  .force("charge", d3.forceManyBody().strength(-100))
  .force("center", d3.forceCenter(width/2, height/2))
  .force("x", d3.forceX().x(d=>{
    const lm = LAYER_META[d.layer];
    if(!lm) return width/2;
    const idx = Object.keys(LAYER_META).indexOf(d.layer);
    return width*0.1 + (idx%5)*(width*0.2);
  }).strength(0.06))
  .force("y", d3.forceY().y(d=>{
    const lm = LAYER_META[d.layer];
    return lm ? height*lm.y : height/2;
  }).strength(0.08))
  .force("collision", d3.forceCollide().radius(d=>(d.size||8)+2))
  .alphaDecay(0.015)
  .on("tick",()=>{
    linkSel.attr("x1",d=>d.source.x).attr("y1",d=>d.source.y).attr("x2",d=>d.target.x).attr("y2",d=>d.target.y);
    nodeSel.attr("transform",d=>`translate(${d.x},${d.y})`);
  });

function updateVisibility(){
  nodeSel.style("display",d=>activeLayers.has(d.layer)?"":"none");
  linkSel.style("display",d=>{
    if(d.layer==="cross") return (activeLayers.size>=2)?"":"none";
    return activeLayers.has(d.layer)?"":"none";
  });
}

function dragStart(e,d){if(!e.active)sim.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y}
function dragging(e,d){d.fx=e.x;d.fy=e.y}
function dragEnd(e,d){if(!e.active)sim.alphaTarget(0);d.fx=null;d.fy=null}

// Initial zoom to fit
svg.call(zoom.transform,d3.zoomIdentity.translate(width*0.05,height*0.02).scale(0.9));
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════
# MAIN — Gather all layers, inject into HTML, write output
# ═══════════════════════════════════════════════════════════════════════
def main():
    print("=" * 60)
    print("THEMANBEARPIG v4.0 — 13-Layer Builder")
    print("=" * 60)
    conn = get_conn()

    all_nodes = []
    all_links = []

    # Gather all 13 layers
    for layer_fn in [layer_adversary, layer_authority, layer_filing, layer_lanes,
                     layer_evidence, layer_system, layer_fred, layer_meek,
                     layer_event_horizon, layer_brains,
                     layer_weapons, layer_police, layer_doctrine]:
        n, l = layer_fn(conn)
        all_nodes.extend(n)
        all_links.extend(l)

    # Cross-layer wiring
    xl = cross_layer_links(all_nodes)
    all_links.extend(xl)

    # Stats
    ev_count = safe_query(conn, "SELECT COUNT(*) as c FROM evidence_quotes")
    auth_count = safe_query(conn, "SELECT COUNT(*) as c FROM authority_chains_v2")
    jv_count = safe_query(conn, "SELECT COUNT(*) as c FROM judicial_violations")
    wc_count = safe_query(conn, "SELECT COUNT(*) as c FROM weapon_chains")

    stats = {
        "nodes": len(all_nodes),
        "links": len(all_links),
        "separation_days": sep_days,
        "evidence_quotes": ev_count[0]["c"] if ev_count else 0,
        "authority_chains": auth_count[0]["c"] if auth_count else 0,
        "judicial_violations": jv_count[0]["c"] if jv_count else 0,
        "weapon_chains": wc_count[0]["c"] if wc_count else 0,
    }

    conn.close()

    # Inject into HTML
    print(f"\n[BUILD] {stats['nodes']} nodes, {stats['links']} links")
    html = HTML_TEMPLATE
    html = html.replace("__NODES__", json.dumps(all_nodes, indent=None))
    html = html.replace("__LINKS__", json.dumps(all_links, indent=None))
    html = html.replace("__STATS__", json.dumps(stats))
    html = html.replace("__NODECOUNT__", str(stats["nodes"]))
    html = html.replace("__LINKCOUNT__", str(stats["links"]))
    html = html.replace("__SEP__", str(sep_days))
    html = html.replace("__EVCOUNT__", f"{stats['evidence_quotes']:,}")
    html = html.replace("__AUTHCOUNT__", f"{stats['authority_chains']:,}")
    html = html.replace("__JVCOUNT__", f"{stats['judicial_violations']:,}")
    html = html.replace("__WCOUNT__", f"{stats['weapon_chains']:,}")

    # Write
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    sz = os.path.getsize(OUT_HTML)
    print(f"[DONE] {OUT_HTML}")
    print(f"       {sz:,} bytes | {stats['nodes']} nodes | {stats['links']} links | 13 layers")
    print(f"       Weapon chains: {stats['weapon_chains']:,}")
    print(f"       Separation: {sep_days} days")

if __name__ == "__main__":
    main()
