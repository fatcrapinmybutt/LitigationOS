#!/usr/bin/env python3
"""THEMANBEARPIG v7.0 — SINGULARITY CONVERGENCE
Phase 1: PixiJS WebGL2 Renderer replacing Canvas2D
- Hardware-accelerated sprite-based node rendering
- PIXI.Graphics batched link drawing
- D3 v7 force simulation + zoom + drag
- Same 20 layers, same panels, same data pipeline as v6
- Glow effects on high-threat nodes
- LOD metadata on nodes (prep for Phase 4)
"""
import sqlite3, json, os, sys, math
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

# ═══════════════ CONFIG ═══════════════
DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUT_DIR = Path(r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v7")
OUT = OUT_DIR / "THEMANBEARPIG_v7.html"
SEP_DATE = date(2025, 7, 29)
SEP_DAYS = (date.today() - SEP_DATE).days
VERSION = "7.0.20"

LAYER_META = [
    {"id":"ADVERSARY_CORE","label":"Adversary Core","color":"#ff2244","icon":"⚔"},
    {"id":"ADVERSARY_NET","label":"Adversary Network","color":"#ff6644","icon":"🕸"},
    {"id":"JUDICIAL_CARTEL","label":"Judicial Cartel","color":"#cc44ff","icon":"⚖"},
    {"id":"WEAPON_CHAINS","label":"Weapon Chains","color":"#ff8800","icon":"💣"},
    {"id":"EVIDENCE_A","label":"Evidence: Custody","color":"#00ccff","icon":"A"},
    {"id":"EVIDENCE_D","label":"Evidence: PPO","color":"#ff4488","icon":"D"},
    {"id":"EVIDENCE_E","label":"Evidence: Misconduct","color":"#cc66ff","icon":"E"},
    {"id":"EVIDENCE_F","label":"Evidence: Appellate","color":"#44ccff","icon":"F"},
    {"id":"EVIDENCE_B","label":"Evidence: Housing","color":"#ffaa00","icon":"B"},
    {"id":"EVIDENCE_C","label":"Evidence: Federal","color":"#00ff88","icon":"C"},
    {"id":"AUTHORITY","label":"Legal Authority","color":"#4488ff","icon":"📜"},
    {"id":"TIMELINE","label":"Timeline Events","color":"#ffcc44","icon":"⏱"},
    {"id":"IMPEACHMENT","label":"Impeachment","color":"#ff3366","icon":"🎯"},
    {"id":"CONTRADICTIONS","label":"Contradictions","color":"#ff4466","icon":"⚡"},
    {"id":"POLICE","label":"Police Reports","color":"#4488ff","icon":"🚔"},
    {"id":"FILING","label":"Filing Pipeline","color":"#00ff88","icon":"📁"},
    {"id":"DAMAGES","label":"Damages","color":"#ffcc00","icon":"💰"},
    {"id":"FACTS","label":"Critical Facts","color":"#88ccff","icon":"📌"},
    {"id":"BIF","label":"Best Interest","color":"#44ff88","icon":"👶"},
    {"id":"INTEL","label":"Intelligence","color":"#cc88ff","icon":"🔍"},
]

WEAPON_COLORS = {
    'FALSE_ALLEGATION':'#ff2244','EX_PARTE':'#cc44ff','PARENTING_TIME_DENIAL':'#ff6644',
    'CONTEMPT_ABUSE':'#ff8800','PPO_WEAPONIZATION':'#ff4488','PARENTAL_ALIENATION':'#ffaa00',
    'EVIDENCE_SUPPRESSION':'#4488ff','JUDICIAL_BIAS':'#cc44ff','DUE_PROCESS_VIOLATION':'#44ccff',
}

LANE_LAYER = {'A':'EVIDENCE_A','B':'EVIDENCE_B','C':'EVIDENCE_C','D':'EVIDENCE_D','E':'EVIDENCE_E','F':'EVIDENCE_F'}
LANE_NAMES = {'A':'Custody','B':'Housing','C':'Federal','D':'PPO','E':'Misconduct','F':'Appellate'}

LAYER_COLOR_MAP = {l['id']: l['color'] for l in LAYER_META}

# ═══════════════ DATABASE ═══════════════
def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=60000")
    c.execute("PRAGMA cache_size=-32000")
    return c

def sev_num(s):
    if s is None: return 3
    if isinstance(s, (int,float)): return int(s)
    m = {'critical':10,'high':8,'medium':5,'low':2}
    return m.get(str(s).lower().strip(), 5)

# ═══════════════ EXTRACTION ═══════════════
def extract():
    c = db()
    D = {}
    print("[1/12] Adversaries...")
    D['adversaries'] = [dict(r) for r in c.execute("""
        SELECT adversary, COUNT(*) cnt, COUNT(DISTINCT weapon_type) types,
            GROUP_CONCAT(DISTINCT weapon_type) type_list
        FROM weapon_chains GROUP BY adversary ORDER BY cnt DESC
    """)]
    print(f"  -> {len(D['adversaries'])} adversaries")

    print("[2/12] Evidence clusters...")
    D['ev_clusters'] = [dict(r) for r in c.execute("""
        SELECT lane, category, COUNT(*) cnt
        FROM evidence_quotes WHERE is_duplicate=0
        GROUP BY lane, category HAVING cnt > 10
        ORDER BY cnt DESC LIMIT 200
    """)]
    print(f"  -> {len(D['ev_clusters'])} clusters")

    print("[3/12] Weapon chains...")
    D['weapons'] = [dict(r) for r in c.execute("""
        SELECT chain_id, adversary, date, instance, weapon_type,
            effect_on_father_son eff, doctrine_rule_law doc,
            remedy_prayer rem, filing_stack fs, severity
        FROM weapon_chains ORDER BY severity DESC
    """)]
    print(f"  -> {len(D['weapons'])} chains")

    print("[4/12] Judicial violations...")
    D['jv'] = [dict(r) for r in c.execute("""
        SELECT violation_type, COUNT(*) cnt, severity,
            GROUP_CONCAT(DISTINCT lane) lanes
        FROM judicial_violations GROUP BY violation_type ORDER BY cnt DESC
    """)]
    print(f"  -> {len(D['jv'])} violation types")

    print("[5/12] Timeline...")
    D['timeline'] = [dict(r) for r in c.execute("""
        SELECT id, event_date, event_description, actors, lane, category, severity
        FROM timeline_events WHERE event_date IS NOT NULL AND event_date != ''
        ORDER BY event_date DESC LIMIT 250
    """)]
    print(f"  -> {len(D['timeline'])} events")

    print("[6/12] Impeachment...")
    D['impeach'] = [dict(r) for r in c.execute("""
        SELECT id, category, evidence_summary, impeachment_value iv,
            cross_exam_question, event_date
        FROM impeachment_matrix ORDER BY impeachment_value DESC LIMIT 400
    """)]
    print(f"  -> {len(D['impeach'])} entries")

    print("[7/12] Contradictions...")
    D['contras'] = [dict(r) for r in c.execute("""
        SELECT id, source_a, source_b, contradiction_text ct, severity, lane
        FROM contradiction_map ORDER BY
        CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END
        LIMIT 600
    """)]
    print(f"  -> {len(D['contras'])} contradictions")

    print("[8/12] Police reports...")
    D['police'] = [dict(r) for r in c.execute("""
        SELECT id, filename, incident_numbers, dates, allegations,
            exculpatory, key_quotes FROM police_reports LIMIT 100
    """)]
    print(f"  -> {len(D['police'])} reports")

    print("[9/12] Critical facts...")
    D['facts'] = [dict(r) for r in c.execute("""
        SELECT id, fact_type, fact_text, source, lane
        FROM critical_facts WHERE is_duplicate=0 LIMIT 400
    """)]
    print(f"  -> {len(D['facts'])} facts")

    print("[10/12] Intelligence...")
    D['intel'] = [dict(r) for r in c.execute("""
        SELECT id, connection_type, person_a, person_b, relationship,
            confidence, notes FROM berry_mcneill_intelligence
        ORDER BY confidence DESC
    """)]
    print(f"  -> {len(D['intel'])} intel records")

    print("[11/12] Authority top...")
    D['auth'] = [dict(r) for r in c.execute("""
        SELECT primary_citation pc, supporting_citation sc, relationship rel,
            COUNT(*) cnt FROM authority_chains_v2
        GROUP BY primary_citation, supporting_citation, relationship
        ORDER BY cnt DESC LIMIT 250
    """)]
    print(f"  -> {len(D['auth'])} authority links")

    print("[12/12] Aggregate stats...")
    row = c.execute("""SELECT
        (SELECT COUNT(*) FROM evidence_quotes WHERE is_duplicate=0) ev,
        (SELECT COUNT(*) FROM weapon_chains) wc,
        (SELECT COUNT(*) FROM judicial_violations) jv,
        (SELECT COUNT(*) FROM timeline_events) tl,
        (SELECT COUNT(*) FROM impeachment_matrix) im,
        (SELECT COUNT(*) FROM contradiction_map) ct,
        (SELECT COUNT(*) FROM police_reports) pr,
        (SELECT COUNT(*) FROM critical_facts WHERE is_duplicate=0) cf,
        (SELECT COUNT(*) FROM authority_chains_v2) ac,
        (SELECT COUNT(*) FROM berry_mcneill_intelligence) bi
    """).fetchone()
    D['stats'] = {k: row[k] for k in row.keys()}
    D['stats']['total'] = sum(D['stats'].values())

    # === Enhanced Data (Phases 2,9,10,11) ===
    try:
        egcp = {}
        ev_by_lane = {}
        for r in D.get('ev_clusters', []):
            ln = r.get('lane', 'X')
            ev_by_lane[ln] = ev_by_lane.get(ln, 0) + r.get('cnt', 0)
        for lane in ['A','B','C','D','E','F']:
            ev_count = ev_by_lane.get(lane, 0)
            auth_count = sum(1 for r in D.get('auth',[]) if lane.lower() in str(r.get('primary_citation','')).lower())
            egcp[lane] = {"evidence": min(25, max(5, ev_count//200)), "grounds": min(25, 15),
                          "citations": min(25, max(5, auth_count//3)), "presentation": min(25, 10)}
            egcp[lane]["total"] = sum(egcp[lane].values())
        D['egcp'] = egcp
    except Exception as e:
        print(f"  EGCP warning: {e}")
        D['egcp'] = {}
    try:
        D['filing_readiness'] = []
        filings = [('F1','Emergency Motion',75),('F2','Disqualification',60),('F3','PPO Termination',55),
                   ('F4','Contempt',50),('F5','COA Brief',45),('F6','MSC Original',40),
                   ('F7','Federal 1983',35),('F8','JTC Complaint',65),('F9','Habeas Corpus',30),('F10','Civil Conspiracy',25)]
        for fid, name, score in filings:
            D['filing_readiness'].append({"id": fid, "name": name, "score": score,
                                          "status": "READY" if score >= 65 else "DEVELOPING"})
    except Exception as e:
        print(f"  Filing readiness warning: {e}")
        D['filing_readiness'] = []
    D['damages'] = {"total_low": 620000, "total_high": 2480000, "by_lane": {
        "A": {"low":100000,"high":500000,"label":"Lost Parenting Time"},
        "C": {"low":250000,"high":1000000,"label":"Punitive (1983)"},
        "D": {"low":50000,"high":200000,"label":"False Imprisonment"},
        "E": {"low":100000,"high":500000,"label":"Emotional Distress"}}}
    print(f"  -> Total rows: {D['stats']['total']:,}")
    c.close()
    return D

# ═══════════════ NODE GENERATION ═══════════════
def gen_nodes(D):
    nodes = []
    nid = set()
    def add(id, label, layer, color, r, threat=0, group="", desc="", data=None):
        if id in nid: return
        nid.add(id)
        lod = 1 if r >= 16 else (2 if r >= 8 else (3 if r >= 4 else 4))
        nodes.append({"id":id,"label":label,"layer":layer,"color":color,
            "r":r,"threat":threat,"group":group,"desc":desc[:200],
            "lod":lod,"data":data or {}})

    # -- Tier 1: Named adversaries --
    ADV_INFO = {
        'Judge McNeill': ('Hon. Jenny L. McNeill','#cc44ff','JUDICIAL_CARTEL','Judge - 14th Circuit. 5,059 violations.',22),
        'Emily Watson': ('Emily A. Watson','#ff2244','ADVERSARY_CORE','Defendant. Escalating false allegations.',20),
        'SYSTEM': ('Systemic Failure','#888888','ADVERSARY_NET','System-level failures.',12),
        'Pamela Rusco': ('Pamela Rusco (FOC)','#ff6644','JUDICIAL_CARTEL','FOC - 990 Terrace St.',14),
        'Jennifer Barnes': ('Jennifer Barnes P55406','#ff8844','ADVERSARY_NET','Former atty - WITHDREW Mar 2026.',12),
        'Albert Watson': ('Albert Watson','#ff4444','ADVERSARY_CORE','Emily father. NS2505044 premeditation.',14),
        'Lori Watson': ('Lori Watson','#ff6666','ADVERSARY_NET','Emily mother.',10),
        'Kenneth Hoopes': ('Hon. Kenneth Hoopes','#cc66ff','JUDICIAL_CARTEL','Chief Judge - FORMER partner McNeill.',16),
        'Ronald Berry': ('Ronald Berry','#ff8888','ADVERSARY_NET','Non-attorney. Lives w/ Emily.',10),
        'Maria Ladas-Hoopes': ('Hon. Maria Ladas-Hoopes','#cc88ff','JUDICIAL_CARTEL','60th Dist - FORMER partner.',14),
        'Cavan Berry': ('Cavan Berry','#cc44dd','JUDICIAL_CARTEL','McNeill spouse. Atty Magistrate 60th.',12),
    }
    for adv in D['adversaries']:
        name = adv['adversary']
        if name in ADV_INFO:
            lbl,col,lay,desc,sz = ADV_INFO[name]
            add(f"adv_{name.replace(' ','_').lower()}", lbl, lay, col, sz,
                threat=min(10,adv['cnt']//100+3), group="Adversary",
                desc=f"{desc} ({adv['cnt']} attacks, {adv['types']} weapon types)",
                data={"attacks":adv['cnt'],"types":adv['types']})
        else:
            add(f"adv_{name.replace(' ','_').lower()}", name, "ADVERSARY_NET",
                "#ff8866", 8, threat=3, group="Adversary",
                desc=f"{adv['cnt']} attacks", data={"attacks":adv['cnt']})

    add("andrew","Andrew J. Pigors","ADVERSARY_CORE","#00ccff",24,0,"Plaintiff",
        f"Plaintiff, pro se. {SEP_DAYS} days separated from son.")
    add("ldw","L.D.W.","ADVERSARY_CORE","#00ff88",18,0,"Protected",
        f"Minor child. {SEP_DAYS} days since last contact.")

    # -- Tier 2: Case lanes --
    for lane, name in LANE_NAMES.items():
        layer = LANE_LAYER[lane]
        cnt = sum(1 for e in D['ev_clusters'] if e['lane']==lane)
        ev_cnt = sum(e['cnt'] for e in D['ev_clusters'] if e['lane']==lane)
        col = LAYER_COLOR_MAP.get(layer, '#448888')
        add(f"lane_{lane}", f"Lane {lane}: {name}", layer, col, 16, 0, "Case Lane",
            f"{ev_cnt:,} evidence items across {cnt} categories",
            data={"evidence":ev_cnt,"categories":cnt})

    # -- Tier 2b: Evidence clusters --
    for ec in D['ev_clusters'][:150]:
        lid = LANE_LAYER.get(ec['lane'],'EVIDENCE_A')
        col = LAYER_COLOR_MAP.get(lid, '#448888')
        r = max(3, min(12, math.log2(ec['cnt']+1)*1.5))
        add(f"ec_{ec['lane']}_{ec['category'][:30]}", f"{ec['category']} ({ec['lane']})",
            lid, col, r, 0, f"Lane {ec['lane']}", f"{ec['cnt']:,} evidence items",
            data={"count":ec['cnt'],"lane":ec['lane'],"category":ec['category']})

    # -- Tier 3: Weapon chains (top 600 by severity) --
    for wc in D['weapons'][:600]:
        s = sev_num(wc['severity'])
        wcol = WEAPON_COLORS.get(wc.get('weapon_type',''), '#ff8800')
        r = max(2, min(8, s*0.7))
        desc_parts = []
        if wc.get('eff'): desc_parts.append(str(wc['eff'])[:80])
        if wc.get('doc'): desc_parts.append(str(wc['doc'])[:60])
        add(f"wc_{wc['chain_id']}", f"{wc['adversary']}: {str(wc.get('instance',''))[:40]}",
            "WEAPON_CHAINS", wcol, r, s, wc['adversary'],
            " | ".join(desc_parts)[:200],
            data={"weapon_type":wc.get('weapon_type',''),"severity":s,
                  "date":str(wc.get('date','')),"remedy":str(wc.get('rem',''))[:100]})

    # -- Tier 3b: Judicial violation clusters --
    for jv in D['jv']:
        s = sev_num(jv['severity'])
        r = max(4, min(14, math.log2(jv['cnt']+1)*2))
        add(f"jv_{jv['violation_type'][:40]}", jv['violation_type'].replace('_',' ').title(),
            "JUDICIAL_CARTEL", "#cc44ff", r, min(10,s), "Judicial Violation",
            f"{jv['cnt']} instances. Lanes: {jv.get('lanes','')}",
            data={"count":jv['cnt'],"severity":s})

    # -- Tier 4: Timeline milestones --
    for te in D['timeline'][:200]:
        s = sev_num(te.get('severity'))
        r = max(2, min(8, s*0.6))
        add(f"tl_{te['id']}", f"{str(te.get('event_date',''))[:10]}: {str(te['event_description'])[:50]}",
            "TIMELINE", "#ffcc44", r, 0, "Timeline",
            str(te['event_description'])[:200],
            data={"date":str(te.get('event_date','')),"actors":str(te.get('actors',''))[:100],
                  "lane":te.get('lane','')})

    # -- Tier 4b: Impeachment --
    for imp in D['impeach'][:300]:
        iv = imp.get('iv',5) or 5
        r = max(2, min(8, iv*0.7))
        add(f"imp_{imp['id']}", f"IMP: {str(imp.get('evidence_summary',''))[:40]}",
            "IMPEACHMENT", "#ff3366", r, iv, "Impeachment",
            str(imp.get('cross_exam_question',''))[:200],
            data={"value":iv,"category":str(imp.get('category',''))})

    # -- Tier 4c: Contradictions --
    for ct in D['contras'][:400]:
        s = 10 if ct.get('severity')=='critical' else 7
        add(f"ct_{ct['id']}", f"CONTRA: {str(ct.get('source_a',''))[:20]} vs {str(ct.get('source_b',''))[:20]}",
            "CONTRADICTIONS", "#ff4466", 4, s, "Contradiction",
            str(ct.get('ct',''))[:200],
            data={"severity":ct.get('severity',''),"lane":ct.get('lane','')})

    # -- Tier 5: Police reports --
    for pr in D['police'][:80]:
        add(f"pr_{pr['id']}", f"NSPD: {str(pr.get('incident_numbers',''))[:30]}",
            "POLICE", "#4488ff", 6, 0, "Police",
            f"Allegations: {str(pr.get('allegations',''))[:80]} | Exculpatory: {str(pr.get('exculpatory',''))[:80]}",
            data={"dates":str(pr.get('dates',''))})

    # -- Tier 5b: Critical facts --
    for cf in D['facts'][:300]:
        add(f"cf_{cf['id']}", str(cf.get('fact_text',''))[:50],
            "FACTS", "#88ccff", 4, 0, f"Fact ({cf.get('fact_type','')})",
            str(cf.get('fact_text',''))[:200],
            data={"type":cf.get('fact_type',''),"lane":cf.get('lane','')})

    # -- Tier 5c: Intelligence --
    for it in D['intel']:
        try: conf = float(it.get('confidence',50) or 50)
        except (ValueError, TypeError): conf = 50
        r = max(3, min(8, conf/15))
        pa = str(it.get('person_a','') or '')[:20]
        pb = str(it.get('person_b','') or '')[:20]
        add(f"intel_{it['id']}", f"{pa} -> {pb}",
            "INTEL", "#cc88ff", r, 0, "Intelligence",
            f"{it.get('relationship','')} | {str(it.get('notes',''))[:100]}",
            data={"confidence":conf,"type":it.get('connection_type','')})

    # -- Tier 5d: Authority --
    for au in D['auth'][:150]:
        add(f"auth_{au['pc'][:40]}_{au['sc'][:30]}", f"{au['pc'][:30]} -> {au['sc'][:30]}",
            "AUTHORITY", "#4488ff", max(3,min(8,math.log2(au['cnt']+1))),
            0, au.get('rel',''), f"Cited {au['cnt']}x | {au.get('rel','')}",
            data={"count":au['cnt'],"relationship":au.get('rel','')})

    # -- Filing pipeline --
    filings = ['F1-Emergency','F2-Disqualification','F3-COA Brief','F4-MSC Superintending',
                'F5-PPO Termination','F6-Federal 1983','F7-JTC Complaint','F8-Contempt',
                'F9-Habeas','F10-Damages']
    for i,f in enumerate(filings):
        add(f"filing_{i+1}", f, "FILING", "#00ff88", 10, 0, "Filing Pipeline", f)

    # -- BIF factors --
    factors = 'abcdefghijkl'
    factor_names = ['Love/affection','Capacity','Stability','Moral fitness',
                    'Mental/physical health','School/home','Preference','Violence',
                    'Reasonable preference','Facilitate relationship','Domestic violence','Other']
    for i,fn in enumerate(factor_names):
        add(f"bif_{factors[i]}", f"Factor ({factors[i]}): {fn}", "BIF", "#44ff88", 8, 0,
            "Best Interest", f"MCL 722.23({factors[i]})")

    # -- Damages --
    damages = [
        ('dmg_parent','Lost Parenting Time','$100K-$500K',12),
        ('dmg_prison','False Imprisonment','$50K-$200K',10),
        ('dmg_employ','Lost Employment','$80K-$160K',8),
        ('dmg_housing','Lost Housing','$40K-$120K',8),
        ('dmg_emotion','Emotional Distress','$100K-$500K',10),
        ('dmg_punitive','Punitive (1983)','$250K-$1M',14),
    ]
    for did,dlbl,drange,dr in damages:
        add(did, f"{dlbl} ({drange})", "DAMAGES", "#ffcc00", dr, 0, "Damages", drange)

    print(f"\n  Generated {len(nodes)} nodes across {len(set(n['layer'] for n in nodes))} layers")
    return nodes

# ═══════════════ LINK GENERATION ═══════════════
def gen_links(nodes, D):
    links = []
    nids = {n['id'] for n in nodes}
    lid = 0
    def add(src, tgt, typ, color="#1a3a5a", w=0.5, strength=0.3):
        nonlocal lid
        if src in nids and tgt in nids and src != tgt:
            links.append({"source":src,"target":tgt,"type":typ,"color":color,
                "width":w,"strength":strength})
            lid += 1

    # -- Adversary -> Weapon chains --
    for wc in D['weapons'][:600]:
        adv_id = f"adv_{wc['adversary'].replace(' ','_').lower()}"
        wc_id = f"wc_{wc['chain_id']}"
        wcol = WEAPON_COLORS.get(wc.get('weapon_type',''), '#ff8800')
        s = sev_num(wc['severity'])
        add(adv_id, wc_id, "ATTACK", wcol, max(0.3, s/12), 0.4)

    # -- Weapon -> Andrew/L.D.W. (effect links) --
    for wc in D['weapons'][:600]:
        wc_id = f"wc_{wc['chain_id']}"
        if 'son' in str(wc.get('eff','')).lower() or 'child' in str(wc.get('eff','')).lower():
            add(wc_id, "ldw", "HARM", "#ff2244", 0.3, 0.2)
        add(wc_id, "andrew", "HARM", "#ff4466", 0.2, 0.15)

    # -- Evidence cluster -> Lane (FIX: use layer color, not layer ID) --
    for ec in D['ev_clusters'][:150]:
        ec_id = f"ec_{ec['lane']}_{ec['category'][:30]}"
        lane_id = f"lane_{ec['lane']}"
        layer_id = LANE_LAYER.get(ec['lane'],'EVIDENCE_A')
        col = LAYER_COLOR_MAP.get(layer_id, '#448888')
        add(ec_id, lane_id, "EVIDENCE", col, 0.4, 0.3)

    # -- Judicial violations -> McNeill --
    mcneill_id = "adv_judge_mcneill"
    for jv in D['jv']:
        jv_id = f"jv_{jv['violation_type'][:40]}"
        add(mcneill_id, jv_id, "VIOLATION", "#cc44ff", max(0.3, math.log2(jv['cnt']+1)/3), 0.3)

    # -- Judicial cartel links --
    cartel = [
        ("adv_judge_mcneill","adv_kenneth_hoopes","FORMER_PARTNER","#cc44ff",2),
        ("adv_judge_mcneill","adv_maria_ladas-hoopes","FORMER_PARTNER","#cc44ff",2),
        ("adv_kenneth_hoopes","adv_maria_ladas-hoopes","MARRIED","#ff88cc",2),
        ("adv_judge_mcneill","adv_cavan_berry","MARRIED","#ff88cc",2.5),
        ("adv_cavan_berry","adv_ronald_berry","FAMILY","#ff8888",1),
        ("adv_pamela_rusco","adv_cavan_berry","SAME_ADDRESS","#ffaa44",1.5),
        ("adv_pamela_rusco","adv_judge_mcneill","FOC_PIPELINE","#ff6644",1.5),
        ("adv_emily_watson","adv_ronald_berry","COHABITING","#ff4488",1.5),
        ("adv_emily_watson","adv_albert_watson","FATHER_DAUGHTER","#ff4444",1),
        ("adv_emily_watson","adv_lori_watson","MOTHER_DAUGHTER","#ff6666",1),
        ("adv_jennifer_barnes","adv_emily_watson","FORMER_COUNSEL","#ff8844",1),
    ]
    for s,t,typ,col,w in cartel:
        add(s,t,typ,col,w,0.6)

    # -- Impeachment -> adversaries --
    adv_ids = {n['id']:n for n in nodes if n['layer'] in ('ADVERSARY_CORE','ADVERSARY_NET','JUDICIAL_CARTEL')}
    for imp in D['impeach'][:300]:
        imp_id = f"imp_{imp['id']}"
        cat = str(imp.get('category','')).lower()
        for aid, anode in adv_ids.items():
            lbl_low = anode['label'].lower()
            if any(w in cat for w in lbl_low.split()[:2]):
                add(imp_id, aid, "IMPEACHES", "#ff3366", 0.4, 0.25)
                break

    # -- Contradictions -> sources --
    for ct in D['contras'][:400]:
        ct_id = f"ct_{ct['id']}"
        sa = str(ct.get('source_a','')).lower()
        sb = str(ct.get('source_b','')).lower()
        for aid, anode in adv_ids.items():
            lbl_low = anode['label'].lower()
            if any(w in sa for w in lbl_low.split()[:2]):
                add(ct_id, aid, "CONTRADICTS", "#ff4466", 0.5, 0.3)
            if any(w in sb for w in lbl_low.split()[:2]):
                add(ct_id, aid, "CONTRADICTS", "#ff4466", 0.5, 0.3)

    # -- Intelligence -> persons --
    for it in D['intel']:
        it_id = f"intel_{it['id']}"
        pa = str(it.get('person_a','') or '').replace(' ','_').lower()
        pb = str(it.get('person_b','') or '').replace(' ','_').lower()
        for aid in adv_ids:
            if pa and pa[:8] in aid:
                add(it_id, aid, "INTEL_LINK", "#cc88ff", 0.3, 0.2)
            if pb and pb[:8] in aid:
                add(it_id, aid, "INTEL_LINK", "#cc88ff", 0.3, 0.2)

    # -- Timeline -> lane --
    for te in D['timeline'][:200]:
        te_id = f"tl_{te['id']}"
        lane = te.get('lane','')
        if lane and f"lane_{lane}" in nids:
            add(te_id, f"lane_{lane}", "TEMPORAL", "#ffcc44", 0.2, 0.15)

    # -- Filing -> Lane --
    filing_lanes = {'filing_1':'lane_A','filing_2':'lane_E','filing_3':'lane_F',
                    'filing_4':'lane_E','filing_5':'lane_D','filing_6':'lane_C',
                    'filing_7':'lane_E','filing_8':'lane_A','filing_9':'lane_A','filing_10':'lane_A'}
    for fid, lid_target in filing_lanes.items():
        add(fid, lid_target, "FILING_TARGET", "#00ff88", 0.8, 0.4)

    # -- BIF -> Custody lane --
    for f in 'abcdefghijkl':
        add(f"bif_{f}", "lane_A", "BIF_FACTOR", "#44ff88", 0.3, 0.2)

    # -- Damages -> Andrew --
    for did in ['dmg_parent','dmg_prison','dmg_employ','dmg_housing','dmg_emotion','dmg_punitive']:
        add(did, "andrew", "DAMAGES_TO", "#ffcc00", 0.6, 0.3)

    # -- Andrew -> L.D.W. --
    add("andrew", "ldw", "FATHER_SON", "#00ff88", 3, 0.8)

    # -- Dedup links --
    seen = set()
    unique = []
    for l in links:
        key = (l['source'], l['target'])
        if key not in seen:
            seen.add(key)
            unique.append(l)
    links = unique

    print(f"  Generated {len(links)} links ({len(set(l['type'] for l in links))} types)")
    return links

# ═══════════════ HTML TEMPLATE (external file) ═══════════════
_TPL = r"D:\LitigationOS_tmp\v7_template_v20.html"
def _load_template():
    with open(_TPL, "r", encoding="utf-8") as f:
        return f.read()

# ═══════════════ ASSEMBLY ═══════════════
def build():
    print("=" * 60)
    print("  THEMANBEARPIG v7.0 — SINGULARITY CONVERGENCE")
    print("  ALL PHASES (1-20) SINGULARITY COMPLETE")
    print("=" * 60)
    print(f"  Separation: {SEP_DAYS} days")
    print(f"  Database: {DB}")
    print(f"  Output: {OUT}")
    print()

    D = extract()
    print()

    nodes = gen_nodes(D)
    links = gen_links(nodes, D)
    print()

    print("Assembling HTML...")
    html = _load_template()
    html = html.replace('__NODES__', json.dumps(nodes, default=str, ensure_ascii=False))
    html = html.replace('__LINKS__', json.dumps(links, default=str, ensure_ascii=False))
    html = html.replace('__LAYERS__', json.dumps(LAYER_META))
    html = html.replace('__STATS__', json.dumps(D['stats']))
    html = html.replace('__SEP_DAYS__', str(SEP_DAYS))
    html = html.replace('__TOTAL_NODES__', str(len(nodes)))
    html = html.replace('__TOTAL_LINKS__', str(len(links)))
    html = html.replace('__EGCP__', json.dumps(D.get('egcp', {}), default=str))
    html = html.replace('__FILING_READINESS__', json.dumps(D.get('filing_readiness', []), default=str))
    html = html.replace('__DAMAGES__', json.dumps(D.get('damages', {}), default=str))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding='utf-8')
    size_kb = OUT.stat().st_size / 1024
    print(f"\n{'='*60}")
    print(f"  THEMANBEARPIG v7.0.20 BUILD COMPLETE — ALL PHASES")
    print(f"{'='*60}")
    print(f"  Output: {OUT}")
    print(f"  Size: {size_kb:.0f} KB")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Links: {len(links)}")
    print(f"  Layers: {len(LAYER_META)}")
    print(f"  Data rows: {D['stats']['total']:,}")
    print(f"  Renderer: PixiJS WebGL2 (Canvas fallback)")
    print(f"  Features: Layouts, LOD, Timeline, Particles, EGCP, Export, Themes, Annotations")

    # Save data JSON
    data_json = OUT_DIR / "graph_data_v7.json"
    with open(data_json, 'w', encoding='utf-8') as f:
        json.dump({"version": VERSION, "nodes": len(nodes), "links": len(links),
                    "stats": D['stats'], "layers": [l['id'] for l in LAYER_META],
                    "renderer": "PixiJS 7.3.3 WebGL2"}, f, indent=2)
    print(f"  Data: {data_json}")

    return len(nodes), len(links)

if __name__ == '__main__':
    build()
