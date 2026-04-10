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
VERSION = "7.0.0"

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

# ═══════════════ HTML TEMPLATE (PixiJS WebGL2) ═══════════════
HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>THEMANBEARPIG v7.0 — SINGULARITY CONVERGENCE</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#060a14;--panel:rgba(8,16,32,0.88);--border:rgba(0,204,255,0.18);
--accent:#00ccff;--red:#ff2244;--gold:#ffaa00;--green:#00ff88;--purple:#cc44ff;
--text:#c8d8e8;--text2:#7890a8}
html,body{width:100%;height:100%;overflow:hidden;background:var(--bg);
font-family:Consolas,'JetBrains Mono',monospace;color:var(--text)}
#graph-container{position:fixed;top:0;left:0;width:100%;height:100%;z-index:1}
#graph-container canvas{display:block}
.panel{position:fixed;z-index:100;background:var(--panel);border:1px solid var(--border);
border-radius:8px;padding:10px 14px;backdrop-filter:blur(12px);
font-size:11px;pointer-events:auto;max-height:80vh;overflow-y:auto}
.panel::-webkit-scrollbar{width:4px}
.panel::-webkit-scrollbar-thumb{background:var(--accent);border-radius:2px}
#hud{top:12px;left:12px;font-family:'Orbitron',monospace}
#hud h1{font-size:14px;color:var(--accent);margin-bottom:4px;letter-spacing:1px}
#hud .ver{font-size:9px;color:var(--text2)}
#hud .fps{color:var(--gold);font-size:10px}
#hud .renderer{color:var(--green);font-size:9px}
#sep-counter{top:12px;right:12px;text-align:right;font-family:'Orbitron',monospace}
#sep-counter .days{font-size:28px;color:var(--red);font-weight:700}
#sep-counter .label{font-size:9px;color:var(--text2)}
#search{position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:200;
width:280px;padding:8px 14px;background:var(--panel);border:1px solid var(--border);
border-radius:20px;color:var(--text);font-size:12px;outline:none;
font-family:Consolas,monospace;display:none}
#search:focus{border-color:var(--accent)}
#controls{bottom:12px;left:12px;display:flex;flex-wrap:wrap;gap:3px;max-width:420px}
.lbtn{padding:3px 7px;border-radius:4px;border:1px solid;cursor:pointer;
font-size:9px;opacity:0.7;transition:all 0.2s;user-select:none}
.lbtn.active{opacity:1;font-weight:bold}
.lbtn:hover{opacity:1}
#stats{bottom:12px;right:12px;font-size:10px;min-width:180px}
#stats td{padding:1px 6px}
#stats .val{text-align:right;color:var(--accent)}
#minimap{position:fixed;bottom:90px;right:12px;z-index:100;
border:1px solid var(--border);border-radius:4px;background:var(--panel)}
#info{top:60px;right:12px;width:280px;display:none;font-size:10px}
#info h3{color:var(--accent);margin-bottom:4px;font-size:12px}
#info .detail{color:var(--text2);line-height:1.5}
#ctx-menu{display:none;z-index:300;min-width:140px;padding:4px 0}
#ctx-menu div{padding:5px 14px;cursor:pointer;font-size:11px}
#ctx-menu div:hover{background:rgba(0,204,255,0.15);color:var(--accent)}
#help{top:50%;left:50%;transform:translate(-50%,-50%);display:none;
width:360px;z-index:400;font-size:11px}
#help h2{color:var(--accent);margin-bottom:8px;font-family:'Orbitron',monospace;font-size:14px}
#help .row{display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.05)}
#help .key{color:var(--gold);min-width:80px}
#tooltip{position:fixed;z-index:500;background:rgba(4,8,20,0.95);border:1px solid var(--accent);
border-radius:6px;padding:6px 10px;font-size:10px;pointer-events:none;display:none;max-width:300px}
</style>
</head>
<body>
<div id="graph-container"></div>

<div class="panel" id="hud">
  <h1>THEMANBEARPIG v7</h1>
  <div class="ver">SINGULARITY CONVERGENCE</div>
  <div class="renderer" id="renderer-info">WebGL2</div>
  <div class="fps" id="fps-display">-- fps | __TOTAL_NODES__ nodes</div>
</div>

<div class="panel" id="sep-counter">
  <div class="days" id="sep-days">__SEP_DAYS__</div>
  <div class="label">DAYS SEPARATED<br>FROM L.D.W.</div>
</div>

<input type="text" id="search" placeholder="Search nodes... (Ctrl+F)">

<div class="panel" id="controls"></div>

<div class="panel" id="stats">
  <table id="stats-table"></table>
</div>

<canvas id="minimap" width="160" height="120"></canvas>

<div class="panel" id="info">
  <h3 id="info-title">Select a node</h3>
  <div class="detail" id="info-body"></div>
</div>

<div class="panel" id="ctx-menu">
  <div onclick="ctxFocus()">Focus neighborhood</div>
  <div onclick="ctxExpand()">Expand neighbors</div>
  <div onclick="ctxHideLayer()">Hide this layer</div>
  <div onclick="ctxPin()">Pin / Unpin</div>
  <div onclick="ctxCopy()">Copy info</div>
</div>

<div class="panel" id="help">
  <h2>KEYBOARD</h2>
  <div class="row"><span class="key">H</span><span>Toggle help</span></div>
  <div class="row"><span class="key">R</span><span>Reset view</span></div>
  <div class="row"><span class="key">Space</span><span>Pause / resume physics</span></div>
  <div class="row"><span class="key">1-9, 0</span><span>Toggle layers / show all</span></div>
  <div class="row"><span class="key">Ctrl+F</span><span>Search</span></div>
  <div class="row"><span class="key">Esc</span><span>Deselect / close panels</span></div>
  <div class="row"><span class="key">Click</span><span>Select node</span></div>
  <div class="row"><span class="key">Right-click</span><span>Context menu</span></div>
  <div class="row"><span class="key">Drag</span><span>Move node</span></div>
  <div class="row"><span class="key">Scroll</span><span>Zoom</span></div>
</div>

<div id="tooltip"></div>

<script src="https://cdn.jsdelivr.net/npm/pixi.js@7.3.3/dist/pixi.min.js"></script>
<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
// ═══ DATA ═══
const NODES = __NODES__;
const LINKS = __LINKS__;
const LAYERS = __LAYERS__;
const STATS = __STATS__;
const SEP_DAYS = __SEP_DAYS__;
const W = window.innerWidth, H = window.innerHeight;

// ═══ UTILITIES ═══
function hexNum(hex) {
  if (!hex || typeof hex !== 'string') return 0x1a3a5a;
  const n = parseInt(hex.replace('#',''), 16);
  return isNaN(n) ? 0x1a3a5a : n;
}
const nodeMap = new Map();
NODES.forEach(n => nodeMap.set(n.id, n));
const visibleLayers = new Set(LAYERS.map(l => l.id));
let searchFilter = null;
function isVis(n) {
  if (!visibleLayers.has(n.layer)) return false;
  if (searchFilter && !searchFilter.has(n.id)) return false;
  return true;
}

// ═══ PIXI APP ═══
const app = new PIXI.Application({
  width: W, height: H,
  backgroundColor: 0x060a14,
  antialias: true,
  resolution: Math.min(window.devicePixelRatio || 1, 2),
  autoDensity: true,
  powerPreference: 'high-performance'
});
document.getElementById('graph-container').appendChild(app.view);
app.view.style.touchAction = 'none';

// Detect renderer type
const isWebGL = app.renderer.type === PIXI.RENDERER_TYPE.WEBGL;
document.getElementById('renderer-info').textContent = isWebGL ? 'WebGL2' : 'Canvas (fallback)';

// ═══ WORLD HIERARCHY ═══
const world = new PIXI.Container();
app.stage.addChild(world);

// Links layer (bottom-most)
const linkGfx = new PIXI.Graphics();
world.addChild(linkGfx);

// Layer containers for nodes
const layerContainers = {};
LAYERS.forEach(L => {
  const c = new PIXI.Container();
  c.sortableChildren = false;
  layerContainers[L.id] = c;
  world.addChild(c);
});

// Selection overlay
const selGfx = new PIXI.Graphics();
world.addChild(selGfx);

// Label container (top-most in world)
const labelContainer = new PIXI.Container();
world.addChild(labelContainer);

// ═══ TEXTURES ═══
const circleGfx = new PIXI.Graphics();
circleGfx.beginFill(0xffffff);
circleGfx.drawCircle(16, 16, 16);
circleGfx.endFill();
const circleTex = app.renderer.generateTexture(circleGfx);

// ═══ CREATE SPRITES ═══
NODES.forEach(n => {
  const container = layerContainers[n.layer];
  if (!container) return;

  // Glow sprite for high-threat nodes
  if (n.threat > 5) {
    const glow = new PIXI.Sprite(circleTex);
    glow.anchor.set(0.5);
    glow.scale.set(n.r * 2.5 / 16);
    glow.tint = hexNum(n.color);
    glow.alpha = 0.15 + (n.threat / 40);
    n._glow = glow;
    container.addChild(glow);
  }

  // Main node sprite
  const sprite = new PIXI.Sprite(circleTex);
  sprite.anchor.set(0.5);
  sprite.scale.set(n.r / 16);
  sprite.tint = hexNum(n.color);
  n._sprite = sprite;
  container.addChild(sprite);
});

// ═══ CREATE LABELS ═══
NODES.forEach(n => {
  if (n.r < 6) return;
  const txt = n.label.length > 35 ? n.label.slice(0,33)+'..' : n.label;
  const label = new PIXI.Text(txt, {
    fontFamily: 'Consolas, monospace',
    fontSize: n.r >= 16 ? 11 : 9,
    fill: 0xc8d8e8,
    align: 'center'
  });
  label.anchor.set(0.5, 1);
  label.visible = false;
  label.resolution = 2;
  n._label = label;
  labelContainer.addChild(label);
});

// ═══ STATE ═══
let transform = d3.zoomIdentity;
let selectedNode = null;
let hoveredNode = null;
let dragNode = null;
let paused = false;
let linksDirty = true;
let fps = 0, frameCount = 0, lastFpsTime = performance.now();
let tickCount = 0;

// ═══ LAYER CONTROLS ═══
const ctrlEl = document.getElementById('controls');
LAYERS.forEach((L, i) => {
  const btn = document.createElement('div');
  btn.className = 'lbtn active';
  btn.style.borderColor = L.color;
  btn.style.color = L.color;
  btn.textContent = L.icon + ' ' + L.label;
  btn.onclick = () => toggleLayer(L.id, btn);
  btn.dataset.layer = L.id;
  ctrlEl.appendChild(btn);
});

function toggleLayer(id, btn) {
  if (visibleLayers.has(id)) {
    visibleLayers.delete(id);
    if (btn) btn.classList.remove('active');
  } else {
    visibleLayers.add(id);
    if (btn) btn.classList.add('active');
  }
  layerContainers[id].visible = visibleLayers.has(id);
  linksDirty = true;
  updateNodeVisibility();
}

function updateNodeVisibility() {
  NODES.forEach(n => {
    const v = isVis(n);
    if (n._sprite) n._sprite.visible = v;
    if (n._glow) n._glow.visible = v;
  });
  linksDirty = true;
}

// ═══ STATS PANEL ═══
const statsEl = document.getElementById('stats-table');
const statLabels = [['Evidence',STATS.ev],['Weapons',STATS.wc],['Violations',STATS.jv],
  ['Timeline',STATS.tl],['Impeachment',STATS.im],['Contradictions',STATS.ct],
  ['Police',STATS.pr],['Facts',STATS.cf],['Authority',STATS.ac],['Intel',STATS.bi]];
let statsHTML = '';
statLabels.forEach(([k,v]) => {
  statsHTML += '<tr><td>'+k+'</td><td class="val">'+(v||0).toLocaleString()+'</td></tr>';
});
statsHTML += '<tr style="border-top:1px solid rgba(0,204,255,0.2)"><td><b>Total</b></td><td class="val" style="color:var(--gold)"><b>'+(STATS.total||0).toLocaleString()+'</b></td></tr>';
statsEl.innerHTML = statsHTML;

// ═══ FORCE SIMULATION ═══
const sim = d3.forceSimulation(NODES)
  .force('link', d3.forceLink(LINKS).id(d => d.id).distance(d => {
    const t = d.type || '';
    if (t === 'FATHER_SON') return 50;
    if (t === 'MARRIED' || t === 'FORMER_PARTNER') return 40;
    if (t === 'ATTACK') return 30;
    return 60;
  }).strength(d => d.strength || 0.3))
  .force('charge', d3.forceManyBody().strength(-25).theta(0.8).distanceMax(500))
  .force('center', d3.forceCenter(W/2, H/2).strength(0.03))
  .force('collision', d3.forceCollide().radius(d => d.r + 2).strength(0.6))
  .force('x', d3.forceX(W/2).strength(0.012))
  .force('y', d3.forceY(H/2).strength(0.012))
  .alphaDecay(0.018)
  .velocityDecay(0.4)
  .on('tick', () => { linksDirty = true; });

// ═══ UPDATE FUNCTIONS ═══
function updateLinks() {
  linkGfx.clear();
  for (let i = 0; i < LINKS.length; i++) {
    const l = LINKS[i];
    const s = l.source, t = l.target;
    if (typeof s === 'string' || typeof t === 'string') continue;
    if (!isVis(s) || !isVis(t)) continue;

    let alpha = 0.12;
    const lt = l.type || '';
    if (lt === 'FATHER_SON') alpha = 0.8;
    else if (lt === 'FORMER_PARTNER' || lt === 'MARRIED' || lt === 'COHABITING') alpha = 0.55;
    else if (lt === 'ATTACK') alpha = 0.2;
    else if (lt === 'CONSPIRACY_CHAIN') alpha = 0.4;

    if (selectedNode && (s === selectedNode || t === selectedNode)) alpha = Math.min(1, alpha + 0.5);

    linkGfx.lineStyle(l.width || 0.5, hexNum(l.color), alpha);
    linkGfx.moveTo(s.x, s.y);
    linkGfx.lineTo(t.x, t.y);
  }
}

function updateSelection() {
  selGfx.clear();
  if (selectedNode && isVis(selectedNode)) {
    selGfx.lineStyle(2.5, 0xffffff, 0.9);
    selGfx.drawCircle(selectedNode.x, selectedNode.y, selectedNode.r + 3);
    selGfx.lineStyle(1.5, hexNum(selectedNode.color), 0.5);
    selGfx.drawCircle(selectedNode.x, selectedNode.y, selectedNode.r + 6);
  }
  if (hoveredNode && hoveredNode !== selectedNode && isVis(hoveredNode)) {
    selGfx.lineStyle(1.5, 0x00ccff, 0.5);
    selGfx.drawCircle(hoveredNode.x, hoveredNode.y, hoveredNode.r + 2);
  }
}

function updateLabels() {
  const zk = transform.k;
  NODES.forEach(n => {
    if (!n._label) return;
    if (!isVis(n)) { n._label.visible = false; return; }
    const show = (n.r >= 16) ||
                 (zk > 0.6 && n.r >= 10) ||
                 (zk > 1.2 && n.r >= 6) ||
                 (n === selectedNode) ||
                 (n === hoveredNode);
    n._label.visible = show;
    if (show) {
      n._label.position.set(n.x, n.y - n.r - 3);
      if (n === selectedNode) { n._label.style.fill = 0xffffff; n._label.alpha = 1; }
      else { n._label.style.fill = 0xc8d8e8; n._label.alpha = 0.75; }
    }
  });
}

// Minimap
const miniCanvas = document.getElementById('minimap');
const miniCtx = miniCanvas.getContext('2d');
const MW = 160, MH = 120;
function updateMinimap() {
  miniCtx.fillStyle = '#060a14';
  miniCtx.fillRect(0, 0, MW, MH);
  let minX=1e9, maxX=-1e9, minY=1e9, maxY=-1e9;
  NODES.forEach(n => {
    if (!isVis(n) || n.x == null) return;
    if (n.x < minX) minX = n.x; if (n.x > maxX) maxX = n.x;
    if (n.y < minY) minY = n.y; if (n.y > maxY) maxY = n.y;
  });
  const pad = 50;
  const rangeX = (maxX - minX + pad*2) || 1;
  const rangeY = (maxY - minY + pad*2) || 1;
  const scale = Math.min(MW / rangeX, MH / rangeY);
  const ox = (MW - rangeX * scale) / 2;
  const oy = (MH - rangeY * scale) / 2;
  NODES.forEach(n => {
    if (!isVis(n) || n.x == null) return;
    const mx = ox + (n.x - minX + pad) * scale;
    const my = oy + (n.y - minY + pad) * scale;
    miniCtx.fillStyle = n.color || '#448';
    miniCtx.globalAlpha = n === selectedNode ? 1 : 0.6;
    miniCtx.fillRect(mx - 1, my - 1, 2, 2);
  });
  miniCtx.globalAlpha = 1;
  // Viewport rect
  const vx = ox + (-transform.x / transform.k - minX + pad) * scale;
  const vy = oy + (-transform.y / transform.k - minY + pad) * scale;
  const vw = (W / transform.k) * scale;
  const vh = (H / transform.k) * scale;
  miniCtx.strokeStyle = '#00ccff';
  miniCtx.lineWidth = 1;
  miniCtx.strokeRect(vx, vy, vw, vh);
}

function updateHUD() {
  document.getElementById('fps-display').textContent =
    fps + ' fps | ' + NODES.length + ' nodes | ' + LINKS.length + ' links';
}

// ═══ TICKER (RENDER LOOP) ═══
app.ticker.add(() => {
  tickCount++;
  // Update sprite positions
  NODES.forEach(n => {
    if (n._sprite) {
      n._sprite.position.set(n.x || 0, n.y || 0);
    }
    if (n._glow) {
      n._glow.position.set(n.x || 0, n.y || 0);
    }
  });

  if (linksDirty) {
    updateLinks();
    linksDirty = false;
  }

  updateSelection();
  updateLabels();

  // FPS counter
  frameCount++;
  const now = performance.now();
  if (now - lastFpsTime > 1000) {
    fps = Math.round(frameCount * 1000 / (now - lastFpsTime));
    frameCount = 0;
    lastFpsTime = now;
    updateHUD();
  }

  // Minimap every 20 frames
  if (tickCount % 20 === 0) updateMinimap();
});

// ═══ ZOOM ═══
const zoomBehavior = d3.zoom()
  .scaleExtent([0.05, 12])
  .on('zoom', (e) => {
    transform = e.transform;
    world.position.set(transform.x, transform.y);
    world.scale.set(transform.k);
  });
d3.select(app.view).call(zoomBehavior);

// ═══ HIT DETECTION ═══
function findNode(sx, sy) {
  const [wx, wy] = transform.invert([sx, sy]);
  let closest = null, minD = Infinity;
  for (let i = 0; i < NODES.length; i++) {
    const n = NODES[i];
    if (!isVis(n) || n.x == null) continue;
    const dx = n.x - wx, dy = n.y - wy;
    const d = dx*dx + dy*dy;
    const hitR = Math.max(n.r + 4, 8);
    if (d < hitR * hitR && d < minD) {
      minD = d;
      closest = n;
    }
  }
  return closest;
}

// ═══ MOUSE EVENTS ═══
const tooltipEl = document.getElementById('tooltip');
const infoEl = document.getElementById('info');
const infoTitle = document.getElementById('info-title');
const infoBody = document.getElementById('info-body');
const ctxMenu = document.getElementById('ctx-menu');
let ctxNode = null;

app.view.addEventListener('pointermove', (e) => {
  if (dragNode) return;
  const found = findNode(e.offsetX, e.offsetY);
  if (found !== hoveredNode) {
    hoveredNode = found;
    if (found) {
      app.view.style.cursor = 'pointer';
      tooltipEl.style.display = 'block';
      tooltipEl.style.left = (e.clientX + 12) + 'px';
      tooltipEl.style.top = (e.clientY - 8) + 'px';
      let ttHtml = '<b style="color:'+found.color+'">'+found.label+'</b>';
      ttHtml += '<br><span style="color:var(--text2)">'+found.group+' | '+found.layer+'</span>';
      if (found.desc) ttHtml += '<br>'+found.desc.slice(0,120);
      if (found.threat > 0) ttHtml += '<br><span style="color:var(--red)">Threat: '+found.threat+'/10</span>';
      tooltipEl.innerHTML = ttHtml;
    } else {
      app.view.style.cursor = 'grab';
      tooltipEl.style.display = 'none';
    }
  } else if (found) {
    tooltipEl.style.left = (e.clientX + 12) + 'px';
    tooltipEl.style.top = (e.clientY - 8) + 'px';
  }
});

app.view.addEventListener('pointerdown', (e) => {
  if (e.button === 0) {
    ctxMenu.style.display = 'none';
    const found = findNode(e.offsetX, e.offsetY);
    if (found && found !== selectedNode) {
      selectedNode = found;
      showInfo(found);
    } else if (!found) {
      selectedNode = null;
      infoEl.style.display = 'none';
    }
    linksDirty = true;
  }
});

app.view.addEventListener('contextmenu', (e) => {
  e.preventDefault();
  const found = findNode(e.offsetX, e.offsetY);
  if (found) {
    ctxNode = found;
    ctxMenu.style.display = 'block';
    ctxMenu.style.left = e.clientX + 'px';
    ctxMenu.style.top = e.clientY + 'px';
  } else {
    ctxMenu.style.display = 'none';
  }
});

document.addEventListener('pointerdown', (e) => {
  if (!ctxMenu.contains(e.target)) ctxMenu.style.display = 'none';
});

function showInfo(n) {
  infoEl.style.display = 'block';
  infoTitle.textContent = n.label;
  infoTitle.style.color = n.color;
  let html = '<div><b>Layer:</b> '+n.layer+'</div>';
  html += '<div><b>Group:</b> '+n.group+'</div>';
  if (n.threat > 0) html += '<div><b>Threat:</b> <span style="color:var(--red)">'+n.threat+'/10</span></div>';
  html += '<div><b>LOD Tier:</b> '+n.lod+'</div>';
  if (n.desc) html += '<div style="margin-top:4px;color:var(--text2)">'+n.desc+'</div>';
  if (n.data) {
    html += '<div style="margin-top:4px;border-top:1px solid var(--border);padding-top:4px">';
    Object.entries(n.data).forEach(([k,v]) => {
      if (v !== '' && v !== null && v !== undefined)
        html += '<div><span style="color:var(--text2)">'+k+':</span> '+String(v).slice(0,80)+'</div>';
    });
    html += '</div>';
  }
  // Connected nodes
  const connected = [];
  LINKS.forEach(l => {
    const s = typeof l.source === 'string' ? l.source : l.source.id;
    const t = typeof l.target === 'string' ? l.target : l.target.id;
    if (s === n.id) connected.push({id: t, type: l.type, dir: 'out'});
    if (t === n.id) connected.push({id: s, type: l.type, dir: 'in'});
  });
  if (connected.length > 0) {
    html += '<div style="margin-top:4px;border-top:1px solid var(--border);padding-top:4px">';
    html += '<b>Connections:</b> '+connected.length+'<br>';
    connected.slice(0,8).forEach(c => {
      const cn = nodeMap.get(c.id);
      const lbl = cn ? cn.label.slice(0,30) : c.id.slice(0,20);
      html += '<span style="color:var(--text2)">'+(c.dir==='out'?'->':'<-')+' '+c.type+': </span>'+lbl+'<br>';
    });
    if (connected.length > 8) html += '<span style="color:var(--text2)">...+'+(connected.length-8)+' more</span>';
    html += '</div>';
  }
  infoBody.innerHTML = html;
}

// ═══ CONTEXT MENU ACTIONS ═══
function ctxFocus() {
  ctxMenu.style.display = 'none';
  if (!ctxNode) return;
  selectedNode = ctxNode;
  showInfo(ctxNode);
  // Zoom to node
  const k = 2;
  const x = W/2 - ctxNode.x * k;
  const y = H/2 - ctxNode.y * k;
  d3.select(app.view).transition().duration(600)
    .call(zoomBehavior.transform, d3.zoomIdentity.translate(x, y).scale(k));
}

function ctxExpand() {
  ctxMenu.style.display = 'none';
  if (!ctxNode) return;
  selectedNode = ctxNode;
  showInfo(ctxNode);
  linksDirty = true;
}

function ctxHideLayer() {
  ctxMenu.style.display = 'none';
  if (!ctxNode) return;
  const btn = document.querySelector('.lbtn[data-layer="'+ctxNode.layer+'"]');
  toggleLayer(ctxNode.layer, btn);
}

function ctxPin() {
  ctxMenu.style.display = 'none';
  if (!ctxNode) return;
  if (ctxNode.fx != null) {
    ctxNode.fx = null; ctxNode.fy = null;
  } else {
    ctxNode.fx = ctxNode.x; ctxNode.fy = ctxNode.y;
  }
  sim.alpha(0.1).restart();
}

function ctxCopy() {
  ctxMenu.style.display = 'none';
  if (!ctxNode) return;
  const text = ctxNode.label + '\n' + ctxNode.group + '\n' + ctxNode.desc;
  navigator.clipboard.writeText(text).catch(() => {});
}

// ═══ SEARCH ═══
const searchEl = document.getElementById('search');
searchEl.addEventListener('input', () => {
  const q = searchEl.value.trim().toLowerCase();
  if (!q) {
    searchFilter = null;
  } else {
    searchFilter = new Set();
    NODES.forEach(n => {
      if (n.label.toLowerCase().includes(q) ||
          n.group.toLowerCase().includes(q) ||
          n.desc.toLowerCase().includes(q) ||
          n.layer.toLowerCase().includes(q)) {
        searchFilter.add(n.id);
      }
    });
  }
  updateNodeVisibility();
});

searchEl.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    searchEl.style.display = 'none';
    searchEl.value = '';
    searchFilter = null;
    updateNodeVisibility();
  }
});

// ═══ KEYBOARD ═══
document.addEventListener('keydown', (e) => {
  if (e.target === searchEl) return;
  const helpEl = document.getElementById('help');

  if (e.key === 'h' || e.key === 'H') {
    helpEl.style.display = helpEl.style.display === 'none' ? 'block' : 'none';
  } else if (e.key === 'r' || e.key === 'R') {
    d3.select(app.view).transition().duration(800)
      .call(zoomBehavior.transform, d3.zoomIdentity.translate(0, 0).scale(1));
    sim.alpha(0.3).restart();
  } else if (e.key === ' ') {
    e.preventDefault();
    paused = !paused;
    if (paused) sim.stop(); else sim.alpha(0.3).restart();
  } else if (e.key >= '1' && e.key <= '9') {
    const idx = parseInt(e.key) - 1;
    if (idx < LAYERS.length) {
      const L = LAYERS[idx];
      const btn = document.querySelector('.lbtn[data-layer="'+L.id+'"]');
      toggleLayer(L.id, btn);
    }
  } else if (e.key === '0') {
    LAYERS.forEach(L => {
      visibleLayers.add(L.id);
      layerContainers[L.id].visible = true;
    });
    document.querySelectorAll('.lbtn').forEach(b => b.classList.add('active'));
    updateNodeVisibility();
  } else if (e.key === 'Escape') {
    selectedNode = null;
    hoveredNode = null;
    infoEl.style.display = 'none';
    ctxMenu.style.display = 'none';
    helpEl.style.display = 'none';
    searchEl.style.display = 'none';
    searchEl.value = '';
    searchFilter = null;
    updateNodeVisibility();
    linksDirty = true;
  } else if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
    e.preventDefault();
    searchEl.style.display = 'block';
    searchEl.focus();
  }
});

// ═══ DRAG ═══
const dragBehavior = d3.drag()
  .subject((e) => {
    const [wx, wy] = transform.invert([e.x, e.y]);
    let closest = null, minD = Infinity;
    for (let i = 0; i < NODES.length; i++) {
      const n = NODES[i];
      if (!isVis(n) || n.x == null) continue;
      const dx = n.x - wx, dy = n.y - wy;
      const d = dx*dx + dy*dy;
      const hitR = n.r + 4;
      if (d < hitR * hitR && d < minD) { minD = d; closest = n; }
    }
    return closest;
  })
  .on('start', (e) => {
    if (!e.subject) return;
    dragNode = e.subject;
    if (!e.active) sim.alphaTarget(0.1).restart();
    dragNode.fx = dragNode.x;
    dragNode.fy = dragNode.y;
    app.view.style.cursor = 'grabbing';
  })
  .on('drag', (e) => {
    if (!dragNode) return;
    const [wx, wy] = transform.invert([e.x, e.y]);
    dragNode.fx = wx;
    dragNode.fy = wy;
  })
  .on('end', (e) => {
    if (!dragNode) return;
    if (!e.active) sim.alphaTarget(0);
    // Keep pinned if moved significantly
    const dx = (dragNode.fx || 0) - (dragNode.x || 0);
    const dy = (dragNode.fy || 0) - (dragNode.y || 0);
    if (Math.abs(dx) < 2 && Math.abs(dy) < 2) {
      dragNode.fx = null;
      dragNode.fy = null;
    }
    dragNode = null;
    app.view.style.cursor = 'grab';
  });
d3.select(app.view).call(dragBehavior);

// ═══ SEPARATION COUNTER ═══
const sepEl = document.getElementById('sep-days');
setInterval(() => {
  const now = new Date();
  const sep = new Date(2025, 6, 29); // July = 6 (0-indexed)
  const days = Math.floor((now - sep) / 86400000);
  sepEl.textContent = days;
}, 60000);

// ═══ INITIAL ZOOM TO FIT ═══
setTimeout(() => {
  let minX=1e9, maxX=-1e9, minY=1e9, maxY=-1e9;
  NODES.forEach(n => {
    if (n.x == null) return;
    if (n.x < minX) minX = n.x; if (n.x > maxX) maxX = n.x;
    if (n.y < minY) minY = n.y; if (n.y > maxY) maxY = n.y;
  });
  const pad = 80;
  const rangeX = (maxX - minX + pad*2) || 1;
  const rangeY = (maxY - minY + pad*2) || 1;
  const k = Math.min(W / rangeX, H / rangeY, 1.5) * 0.85;
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  const tx = W/2 - cx * k;
  const ty = H/2 - cy * k;
  d3.select(app.view).transition().duration(1200)
    .call(zoomBehavior.transform, d3.zoomIdentity.translate(tx, ty).scale(k));
}, 3000);

// ═══ RESIZE ═══
window.addEventListener('resize', () => {
  app.renderer.resize(window.innerWidth, window.innerHeight);
});

console.log('THEMANBEARPIG v7.0 loaded:', NODES.length, 'nodes,', LINKS.length, 'links');
console.log('Renderer:', isWebGL ? 'WebGL2' : 'Canvas2D fallback');
</script>
</body>
</html>'''

# ═══════════════ ASSEMBLY ═══════════════
def build():
    print("=" * 60)
    print("  THEMANBEARPIG v7.0 — SINGULARITY CONVERGENCE")
    print("  Phase 1: PixiJS WebGL2 Renderer")
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

    # --- MERGE KRAKEN OVERLAY (if exists) ---
    overlay_path = OUT_DIR / "kraken_overlay.json"
    if overlay_path.exists():
        try:
            with open(overlay_path, 'r', encoding='utf-8') as f:
                krk = json.load(f)
            krk_nodes = krk.get('nodes', [])
            krk_links = krk.get('links', [])
            existing_ids = {n['id'] for n in nodes}
            added_n = 0
            for kn in krk_nodes:
                if kn['id'] not in existing_ids:
                    nodes.append(kn)
                    existing_ids.add(kn['id'])
                    added_n += 1
            all_ids = {n['id'] for n in nodes}
            added_l = 0
            for kl in krk_links:
                if kl['source'] in all_ids and kl['target'] in all_ids:
                    links.append(kl)
                    added_l += 1
            print(f"[KRAKEN] Merged overlay: +{added_n} nodes, +{added_l} links from {overlay_path}")
        except Exception as e:
            print(f"[KRAKEN] Overlay merge failed: {e}")
    else:
        print("[KRAKEN] No overlay found (run KAL rounds to generate)")

    print("Assembling HTML...")
    html = HTML
    html = html.replace('__NODES__', json.dumps(nodes, default=str, ensure_ascii=False))
    html = html.replace('__LINKS__', json.dumps(links, default=str, ensure_ascii=False))
    html = html.replace('__LAYERS__', json.dumps(LAYER_META))
    html = html.replace('__STATS__', json.dumps(D['stats']))
    html = html.replace('__SEP_DAYS__', str(SEP_DAYS))
    html = html.replace('__TOTAL_NODES__', str(len(nodes)))
    html = html.replace('__TOTAL_LINKS__', str(len(links)))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding='utf-8')
    size_kb = OUT.stat().st_size / 1024
    print(f"\n{'='*60}")
    print(f"  THEMANBEARPIG v7.0 BUILD COMPLETE")
    print(f"{'='*60}")
    print(f"  Output: {OUT}")
    print(f"  Size: {size_kb:.0f} KB")
    print(f"  Nodes: {len(nodes)}")
    print(f"  Links: {len(links)}")
    print(f"  Layers: {len(LAYER_META)}")
    print(f"  Data rows: {D['stats']['total']:,}")
    print(f"  Renderer: PixiJS WebGL2 (Canvas fallback)")

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
