#!/usr/bin/env python3
"""THEMANBEARPIG v6.0 — Full Data Saturation Build
Extracts ALL data from litigation_context.db (464K+ rows, 13 tables)
Generates Canvas2D force-directed graph with 2K-5K smart-clustered nodes
20 toggleable layers, glassmorphism HUD, weapon chain visualization
"""
import sqlite3, json, os, sys, math
from datetime import date, datetime
from pathlib import Path
from collections import defaultdict

# ═══════════════ CONFIG ═══════════════
DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
OUT = r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v6.html"
SEP_DATE = date(2025, 7, 29)
SEP_DAYS = (date.today() - SEP_DATE).days

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
    print(f"  → {len(D['adversaries'])} adversaries")

    print("[2/12] Evidence clusters...")
    D['ev_clusters'] = [dict(r) for r in c.execute("""
        SELECT lane, category, COUNT(*) cnt
        FROM evidence_quotes WHERE is_duplicate=0
        GROUP BY lane, category HAVING cnt > 10
        ORDER BY cnt DESC LIMIT 150
    """)]
    print(f"  → {len(D['ev_clusters'])} clusters")

    print("[3/12] Weapon chains...")
    D['weapons'] = [dict(r) for r in c.execute("""
        SELECT chain_id, adversary, date, instance, weapon_type,
            effect_on_father_son eff, doctrine_rule_law doc,
            remedy_prayer rem, filing_stack fs, severity
        FROM weapon_chains ORDER BY severity DESC
    """)]
    print(f"  → {len(D['weapons'])} chains")

    print("[4/12] Judicial violations...")
    D['jv'] = [dict(r) for r in c.execute("""
        SELECT violation_type, COUNT(*) cnt, severity,
            GROUP_CONCAT(DISTINCT lane) lanes
        FROM judicial_violations GROUP BY violation_type ORDER BY cnt DESC
    """)]
    print(f"  → {len(D['jv'])} violation types")

    print("[5/12] Timeline...")
    D['timeline'] = [dict(r) for r in c.execute("""
        SELECT id, event_date, event_description, actors, lane, category, severity
        FROM timeline_events WHERE event_date IS NOT NULL AND event_date != ''
        ORDER BY event_date DESC LIMIT 200
    """)]
    print(f"  → {len(D['timeline'])} events")

    print("[6/12] Impeachment...")
    D['impeach'] = [dict(r) for r in c.execute("""
        SELECT id, category, evidence_summary, impeachment_value iv,
            cross_exam_question, event_date
        FROM impeachment_matrix ORDER BY impeachment_value DESC LIMIT 300
    """)]
    print(f"  → {len(D['impeach'])} entries")

    print("[7/12] Contradictions...")
    D['contras'] = [dict(r) for r in c.execute("""
        SELECT id, source_a, source_b, contradiction_text ct, severity, lane
        FROM contradiction_map ORDER BY
        CASE severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 ELSE 3 END
        LIMIT 500
    """)]
    print(f"  → {len(D['contras'])} contradictions")

    print("[8/12] Police reports...")
    D['police'] = [dict(r) for r in c.execute("""
        SELECT id, filename, incident_numbers, dates, allegations,
            exculpatory, key_quotes FROM police_reports LIMIT 100
    """)]
    print(f"  → {len(D['police'])} reports")

    print("[9/12] Critical facts...")
    D['facts'] = [dict(r) for r in c.execute("""
        SELECT id, fact_type, fact_text, source, lane
        FROM critical_facts WHERE is_duplicate=0 LIMIT 300
    """)]
    print(f"  → {len(D['facts'])} facts")

    print("[10/12] Intelligence...")
    D['intel'] = [dict(r) for r in c.execute("""
        SELECT id, connection_type, person_a, person_b, relationship,
            confidence, notes FROM berry_mcneill_intelligence
        ORDER BY confidence DESC
    """)]
    print(f"  → {len(D['intel'])} intel records")

    print("[11/12] Authority top...")
    D['auth'] = [dict(r) for r in c.execute("""
        SELECT primary_citation pc, supporting_citation sc, relationship rel,
            COUNT(*) cnt FROM authority_chains_v2
        GROUP BY primary_citation, supporting_citation, relationship
        ORDER BY cnt DESC LIMIT 200
    """)]
    print(f"  → {len(D['auth'])} authority links")

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
    print(f"  → Total rows: {D['stats']['total']:,}")
    c.close()
    return D

# ═══════════════ NODE GENERATION ═══════════════
def gen_nodes(D):
    nodes = []
    nid = set()
    def add(id, label, layer, color, r, threat=0, group="", desc="", data=None):
        if id in nid: return
        nid.add(id)
        nodes.append({"id":id,"label":label,"layer":layer,"color":color,
            "r":r,"threat":threat,"group":group,"desc":desc[:200],
            "data":data or {}})

    # ── Tier 1: Named adversaries ──
    ADV_INFO = {
        'Judge McNeill': ('Hon. Jenny L. McNeill','#cc44ff','JUDICIAL_CARTEL','Judge — 14th Circuit. 5,059 violations.',22),
        'Emily Watson': ('Emily A. Watson','#ff2244','ADVERSARY_CORE','Defendant. Escalating false allegations.',20),
        'SYSTEM': ('Systemic Failure','#888888','ADVERSARY_NET','System-level failures.',12),
        'Pamela Rusco': ('Pamela Rusco (FOC)','#ff6644','JUDICIAL_CARTEL','FOC — 990 Terrace St.',14),
        'Jennifer Barnes': ('Jennifer Barnes P55406','#ff8844','ADVERSARY_NET','Former atty — WITHDREW Mar 2026.',12),
        'Albert Watson': ('Albert Watson','#ff4444','ADVERSARY_CORE','Emily father. NS2505044 premeditation.',14),
        'Lori Watson': ('Lori Watson','#ff6666','ADVERSARY_NET','Emily mother.',10),
        'Kenneth Hoopes': ('Hon. Kenneth Hoopes','#cc66ff','JUDICIAL_CARTEL','Chief Judge — FORMER partner McNeill.',16),
        'Ronald Berry': ('Ronald Berry','#ff8888','ADVERSARY_NET','Non-attorney. Lives w/ Emily.',10),
        'Maria Ladas-Hoopes': ('Hon. Maria Ladas-Hoopes','#cc88ff','JUDICIAL_CARTEL','60th Dist — FORMER partner.',14),
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

    # Andrew & L.D.W.
    add("andrew","Andrew J. Pigors","ADVERSARY_CORE","#00ccff",24,0,"Plaintiff",
        f"Plaintiff, pro se. {SEP_DAYS} days separated from son.")
    add("ldw","L.D.W.","ADVERSARY_CORE","#00ff88",18,0,"Protected",
        f"Minor child. {SEP_DAYS} days since last contact.")

    # ── Tier 2: Case lanes ──
    for lane, name in LANE_NAMES.items():
        layer = LANE_LAYER[lane]
        cnt = sum(1 for e in D['ev_clusters'] if e['lane']==lane)
        ev_cnt = sum(e['cnt'] for e in D['ev_clusters'] if e['lane']==lane)
        col = next((l['color'] for l in LAYER_META if l['id']==layer), '#448')
        add(f"lane_{lane}", f"Lane {lane}: {name}", layer, col, 16, 0, "Case Lane",
            f"{ev_cnt:,} evidence items across {cnt} categories",
            data={"evidence":ev_cnt,"categories":cnt})

    # ── Tier 2b: Evidence clusters ──
    for ec in D['ev_clusters'][:100]:
        lid = LANE_LAYER.get(ec['lane'],'EVIDENCE_A')
        col = next((l['color'] for l in LAYER_META if l['id']==lid), '#448')
        r = max(3, min(12, math.log2(ec['cnt']+1)*1.5))
        add(f"ec_{ec['lane']}_{ec['category'][:30]}", f"{ec['category']} ({ec['lane']})",
            lid, col, r, 0, f"Lane {ec['lane']}", f"{ec['cnt']:,} evidence items",
            data={"count":ec['cnt'],"lane":ec['lane'],"category":ec['category']})

    # ── Tier 3: Weapon chains (top 500 by severity) ──
    for wc in D['weapons'][:500]:
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

    # ── Tier 3b: Judicial violation clusters ──
    for jv in D['jv']:
        s = sev_num(jv['severity'])
        r = max(4, min(14, math.log2(jv['cnt']+1)*2))
        add(f"jv_{jv['violation_type'][:40]}", jv['violation_type'].replace('_',' ').title(),
            "JUDICIAL_CARTEL", "#cc44ff", r, min(10,s), "Judicial Violation",
            f"{jv['cnt']} instances. Lanes: {jv.get('lanes','')}",
            data={"count":jv['cnt'],"severity":s})

    # ── Tier 4: Timeline milestones ──
    for te in D['timeline'][:150]:
        s = sev_num(te.get('severity'))
        r = max(2, min(8, s*0.6))
        add(f"tl_{te['id']}", f"{str(te.get('event_date',''))[:10]}: {str(te['event_description'])[:50]}",
            "TIMELINE", "#ffcc44", r, 0, f"Timeline",
            str(te['event_description'])[:200],
            data={"date":str(te.get('event_date','')),"actors":str(te.get('actors',''))[:100],
                  "lane":te.get('lane','')})

    # ── Tier 4b: Impeachment ──
    for imp in D['impeach'][:200]:
        iv = imp.get('iv',5) or 5
        r = max(2, min(8, iv*0.7))
        add(f"imp_{imp['id']}", f"IMP: {str(imp.get('evidence_summary',''))[:40]}",
            "IMPEACHMENT", "#ff3366", r, iv, "Impeachment",
            str(imp.get('cross_exam_question',''))[:200],
            data={"value":iv,"category":str(imp.get('category',''))})

    # ── Tier 4c: Contradictions ──
    for ct in D['contras'][:300]:
        s = 10 if ct.get('severity')=='critical' else 7
        add(f"ct_{ct['id']}", f"CONTRA: {str(ct.get('source_a',''))[:20]} vs {str(ct.get('source_b',''))[:20]}",
            "CONTRADICTIONS", "#ff4466", 4, s, "Contradiction",
            str(ct.get('ct',''))[:200],
            data={"severity":ct.get('severity',''),"lane":ct.get('lane','')})

    # ── Tier 5: Police reports ──
    for pr in D['police'][:50]:
        add(f"pr_{pr['id']}", f"NSPD: {str(pr.get('incident_numbers',''))[:30]}",
            "POLICE", "#4488ff", 6, 0, "Police",
            f"Allegations: {str(pr.get('allegations',''))[:80]} | Exculpatory: {str(pr.get('exculpatory',''))[:80]}",
            data={"dates":str(pr.get('dates',''))})

    # ── Tier 5b: Critical facts ──
    for cf in D['facts'][:200]:
        add(f"cf_{cf['id']}", str(cf.get('fact_text',''))[:50],
            "FACTS", "#88ccff", 4, 0, f"Fact ({cf.get('fact_type','')})",
            str(cf.get('fact_text',''))[:200],
            data={"type":cf.get('fact_type',''),"lane":cf.get('lane','')})

    # ── Tier 5c: Intelligence ──
    for it in D['intel']:
        try: conf = float(it.get('confidence',50) or 50)
        except (ValueError, TypeError): conf = 50
        r = max(3, min(8, conf/15))
        pa = str(it.get('person_a','') or '')[:20]
        pb = str(it.get('person_b','') or '')[:20]
        add(f"intel_{it['id']}", f"{pa} → {pb}",
            "INTEL", "#cc88ff", r, 0, "Intelligence",
            f"{it.get('relationship','')} | {str(it.get('notes',''))[:100]}",
            data={"confidence":conf,"type":it.get('connection_type','')})

    # ── Tier 5d: Authority ──
    for au in D['auth'][:100]:
        add(f"auth_{au['pc'][:40]}_{au['sc'][:30]}", f"{au['pc'][:30]} → {au['sc'][:30]}",
            "AUTHORITY", "#4488ff", max(3,min(8,math.log2(au['cnt']+1))),
            0, au.get('rel',''), f"Cited {au['cnt']}x | {au.get('rel','')}",
            data={"count":au['cnt'],"relationship":au.get('rel','')})

    # ── Filing pipeline ──
    filings = ['F1-Emergency','F2-Disqualification','F3-COA Brief','F4-MSC Superintending',
                'F5-PPO Termination','F6-Federal 1983','F7-JTC Complaint','F8-Contempt',
                'F9-Habeas','F10-Damages']
    for i,f in enumerate(filings):
        add(f"filing_{i+1}", f, "FILING", "#00ff88", 10, 0, "Filing Pipeline", f)

    # ── BIF factors ──
    factors = 'abcdefghijkl'
    factor_names = ['Love/affection','Capacity','Stability','Moral fitness',
                    'Mental/physical health','School/home','Preference','Violence',
                    'Reasonable preference','Facilitate relationship','Domestic violence','Other']
    for i,fn in enumerate(factor_names):
        add(f"bif_{factors[i]}", f"Factor ({factors[i]}): {fn}", "BIF", "#44ff88", 8, 0,
            "Best Interest", f"MCL 722.23({factors[i]})")

    # ── Damages ──
    damages = [
        ('dmg_parent','Lost Parenting Time','$100K-$500K',12),
        ('dmg_prison','False Imprisonment','$50K-$200K',10),
        ('dmg_employ','Lost Employment','$80K-$160K',8),
        ('dmg_housing','Lost Housing','$40K-$120K',8),
        ('dmg_emotion','Emotional Distress','$100K-$500K',10),
        ('dmg_punitive','Punitive (§1983)','$250K-$1M',14),
    ]
    for did,dlbl,drange,dr in damages:
        add(did, f"{dlbl} ({drange})", "DAMAGES", "#ffcc00", dr, 0, "Damages", drange)

    print(f"\n✅ Generated {len(nodes)} nodes across {len(set(n['layer'] for n in nodes))} layers")
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

    # ── Adversary → Weapon chains ──
    for wc in D['weapons'][:500]:
        adv_id = f"adv_{wc['adversary'].replace(' ','_').lower()}"
        wc_id = f"wc_{wc['chain_id']}"
        wcol = WEAPON_COLORS.get(wc.get('weapon_type',''), '#ff8800')
        s = sev_num(wc['severity'])
        add(adv_id, wc_id, "ATTACK", wcol, max(0.3, s/12), 0.4)

    # ── Weapon → Andrew/L.D.W. (effect links) ──
    for wc in D['weapons'][:500]:
        wc_id = f"wc_{wc['chain_id']}"
        if 'son' in str(wc.get('eff','')).lower() or 'child' in str(wc.get('eff','')).lower():
            add(wc_id, "ldw", "HARM", "#ff2244", 0.3, 0.2)
        add(wc_id, "andrew", "HARM", "#ff4466", 0.2, 0.15)

    # ── Evidence cluster → Lane ──
    for ec in D['ev_clusters'][:100]:
        ec_id = f"ec_{ec['lane']}_{ec['category'][:30]}"
        lane_id = f"lane_{ec['lane']}"
        add(ec_id, lane_id, "EVIDENCE", LANE_LAYER.get(ec['lane'],'#448'), 0.4, 0.3)

    # ── Judicial violations → McNeill ──
    mcneill_id = "adv_judge_mcneill"
    for jv in D['jv']:
        jv_id = f"jv_{jv['violation_type'][:40]}"
        add(mcneill_id, jv_id, "VIOLATION", "#cc44ff", max(0.3, math.log2(jv['cnt']+1)/3), 0.3)

    # ── Judicial cartel links ──
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

    # ── Impeachment → adversaries ──
    adv_ids = {n['id']:n for n in nodes if n['layer'] in ('ADVERSARY_CORE','ADVERSARY_NET','JUDICIAL_CARTEL')}
    for imp in D['impeach'][:200]:
        imp_id = f"imp_{imp['id']}"
        cat = str(imp.get('category','')).lower()
        for aid, anode in adv_ids.items():
            lbl_low = anode['label'].lower()
            if any(w in cat for w in lbl_low.split()[:2]):
                add(imp_id, aid, "IMPEACHES", "#ff3366", 0.4, 0.25)
                break

    # ── Contradictions → sources ──
    for ct in D['contras'][:300]:
        ct_id = f"ct_{ct['id']}"
        sa = str(ct.get('source_a','')).lower()
        sb = str(ct.get('source_b','')).lower()
        for aid, anode in adv_ids.items():
            lbl_low = anode['label'].lower()
            if any(w in sa for w in lbl_low.split()[:2]):
                add(ct_id, aid, "CONTRADICTS", "#ff4466", 0.5, 0.3)
            if any(w in sb for w in lbl_low.split()[:2]):
                add(ct_id, aid, "CONTRADICTS", "#ff4466", 0.5, 0.3)

    # ── Intelligence → persons ──
    for it in D['intel']:
        it_id = f"intel_{it['id']}"
        pa = str(it.get('person_a','')).replace(' ','_').lower()
        pb = str(it.get('person_b','')).replace(' ','_').lower()
        for aid in adv_ids:
            if pa and pa[:8] in aid:
                add(it_id, aid, "INTEL_LINK", "#cc88ff", 0.3, 0.2)
            if pb and pb[:8] in aid:
                add(it_id, aid, "INTEL_LINK", "#cc88ff", 0.3, 0.2)

    # ── Timeline → lane ──
    for te in D['timeline'][:150]:
        te_id = f"tl_{te['id']}"
        lane = te.get('lane','')
        if lane and f"lane_{lane}" in nids:
            add(te_id, f"lane_{lane}", "TEMPORAL", "#ffcc44", 0.2, 0.15)

    # ── Filing → Lane ──
    filing_lanes = {'filing_1':'lane_A','filing_2':'lane_E','filing_3':'lane_F',
                    'filing_4':'lane_E','filing_5':'lane_D','filing_6':'lane_C',
                    'filing_7':'lane_E','filing_8':'lane_A','filing_9':'lane_A','filing_10':'lane_A'}
    for fid, lid_target in filing_lanes.items():
        add(fid, lid_target, "FILING_TARGET", "#00ff88", 0.8, 0.4)

    # ── BIF → Custody lane ──
    for f in 'abcdefghijkl':
        add(f"bif_{f}", "lane_A", "BIF_FACTOR", "#44ff88", 0.3, 0.2)

    # ── Damages → Andrew ──
    for did,_,_,_ in [('dmg_parent','','',0),('dmg_prison','','',0),('dmg_employ','','',0),
                       ('dmg_housing','','',0),('dmg_emotion','','',0),('dmg_punitive','','',0)]:
        add(did, "andrew", "DAMAGES_TO", "#ffcc00", 0.6, 0.3)

    # ── Andrew → L.D.W. ──
    add("andrew", "ldw", "FATHER_SON", "#00ff88", 3, 0.8)

    # ── Dedup links ──
    seen = set()
    unique = []
    for l in links:
        key = (l['source'], l['target'])
        if key not in seen:
            seen.add(key)
            unique.append(l)
    links = unique

    print(f"✅ Generated {len(links)} links ({len(set(l['type'] for l in links))} types)")
    return links

# ═══════════════ HTML TEMPLATE ═══════════════
HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>THEMANBEARPIG v6.0 — Full Data Saturation</title>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#060a14;--panel:rgba(8,16,32,0.88);--border:rgba(0,204,255,0.15);--text:#c8d8e8;
--accent:#00ccff;--red:#ff2244;--gold:#ffaa00;--green:#00ff88;--purple:#cc44ff;
--font:'Consolas','JetBrains Mono',monospace}
body{background:var(--bg);color:var(--text);font-family:var(--font);overflow:hidden;cursor:crosshair}
canvas#graph{position:fixed;top:0;left:0;z-index:1}
.panel{position:fixed;z-index:10;background:var(--panel);border:1px solid var(--border);
border-radius:10px;backdrop-filter:blur(12px);padding:12px;font-size:11px;
box-shadow:0 4px 30px rgba(0,0,0,0.5)}
#hud{top:10px;left:10px;display:flex;gap:12px;align-items:center;padding:8px 16px;
border-radius:8px;font-family:'Orbitron',sans-serif;font-size:10px;letter-spacing:1px}
#hud .stat{display:flex;flex-direction:column;align-items:center}
#hud .stat .val{font-size:16px;font-weight:700}
#hud .stat .lbl{font-size:8px;opacity:0.6;text-transform:uppercase}
.accent{color:var(--accent)}.red{color:var(--red)}.gold{color:var(--gold)}.green{color:var(--green)}.purple{color:var(--purple)}
#sep-counter{top:10px;right:10px;text-align:center;padding:10px 20px;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 15px rgba(255,34,68,0.3)}50%{box-shadow:0 0 30px rgba(255,34,68,0.6)}}
#sep-counter .days{font-family:'Orbitron',sans-serif;font-size:28px;font-weight:700;color:var(--red)}
#sep-counter .label{font-size:9px;opacity:0.7;text-transform:uppercase;letter-spacing:2px}
#search{position:fixed;top:60px;left:10px;z-index:10;width:260px;padding:8px 12px;
background:var(--panel);border:1px solid var(--border);border-radius:6px;color:var(--text);
font-family:var(--font);font-size:11px;outline:none}
#search:focus{border-color:var(--accent);box-shadow:0 0 10px rgba(0,204,255,0.2)}
#controls{top:90px;left:10px;width:260px;max-height:calc(100vh - 120px);overflow-y:auto}
#controls h3{font-family:'Orbitron',sans-serif;font-size:10px;margin-bottom:8px;color:var(--accent);
letter-spacing:1px}
.layer-btn{display:flex;align-items:center;gap:6px;padding:4px 8px;margin:2px 0;border-radius:4px;
cursor:pointer;font-size:10px;transition:all 0.2s}
.layer-btn:hover{background:rgba(0,204,255,0.1)}
.layer-btn .dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.layer-btn .cnt{margin-left:auto;opacity:0.5;font-size:9px}
.layer-btn.off{opacity:0.3}
.layer-btn.off .dot{background:#333!important}
#info{bottom:10px;right:10px;width:320px;max-height:50vh;overflow-y:auto;display:none}
#info h3{font-family:'Orbitron',sans-serif;font-size:11px;margin-bottom:6px;color:var(--accent)}
#info .field{margin:4px 0;font-size:10px}
#info .field .k{color:var(--accent);text-transform:uppercase;font-size:9px}
#info .field .v{margin-left:4px}
#stats{bottom:10px;left:10px;width:260px;font-size:10px}
#stats h3{font-family:'Orbitron',sans-serif;font-size:10px;margin-bottom:6px;color:var(--gold)}
#stats .row{display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid rgba(255,255,255,0.05)}
#stats .row .v{color:var(--accent);font-weight:700}
#minimap{position:fixed;bottom:10px;left:280px;z-index:10;width:160px;height:120px;
background:rgba(6,10,20,0.9);border:1px solid var(--border);border-radius:6px}
#legend{top:10px;right:200px;padding:8px;font-size:9px;display:flex;gap:8px;flex-wrap:wrap;max-width:400px}
.leg-item{display:flex;align-items:center;gap:4px}
.leg-dot{width:8px;height:8px;border-radius:50%}
#ctx-menu{display:none;z-index:100;width:180px;padding:4px 0}
#ctx-menu .item{padding:6px 12px;cursor:pointer;font-size:10px}
#ctx-menu .item:hover{background:rgba(0,204,255,0.15)}
#help{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);z-index:200;
width:400px;padding:20px;display:none;text-align:center}
#help h2{font-family:'Orbitron',sans-serif;color:var(--accent);margin-bottom:12px}
#help .key{display:inline-block;padding:2px 8px;background:rgba(0,204,255,0.1);
border:1px solid var(--border);border-radius:3px;margin:2px;font-size:10px}
#tooltip{position:fixed;z-index:50;padding:6px 10px;background:rgba(0,0,0,0.9);
border:1px solid var(--accent);border-radius:4px;font-size:10px;pointer-events:none;display:none;max-width:300px}
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px}
</style>
</head>
<body>
<canvas id="graph"></canvas>

<div class="panel" id="hud">
  <div class="stat"><span class="val accent" id="h-nodes">0</span><span class="lbl">Nodes</span></div>
  <div class="stat"><span class="val green" id="h-links">0</span><span class="lbl">Links</span></div>
  <div class="stat"><span class="val gold" id="h-layers">0</span><span class="lbl">Layers</span></div>
  <div class="stat"><span class="val purple" id="h-fps">0</span><span class="lbl">FPS</span></div>
  <div class="stat"><span class="val red" id="h-threats">0</span><span class="lbl">Threats</span></div>
</div>

<div class="panel" id="sep-counter">
  <div class="days">__SEP_DAYS__</div>
  <div class="label">Days Separated</div>
</div>

<input type="text" id="search" placeholder="🔍 Search nodes... (Ctrl+F)">

<div class="panel" id="controls">
  <h3>⚡ LAYERS (20)</h3>
  <div id="layer-list"></div>
  <div style="margin-top:8px;padding-top:6px;border-top:1px solid var(--border)">
    <span class="layer-btn" onclick="toggleAll(true)" style="color:var(--green)">Show All</span>
    <span class="layer-btn" onclick="toggleAll(false)" style="color:var(--red)">Hide All</span>
  </div>
</div>

<div class="panel" id="stats">
  <h3>📊 DATA SATURATION</h3>
  <div id="stats-content"></div>
</div>

<canvas id="minimap" width="160" height="120"></canvas>

<div class="panel" id="info">
  <h3 id="info-title">Select a node</h3>
  <div id="info-content"></div>
</div>

<div class="panel" id="ctx-menu">
  <div class="item" onclick="focusNode()">🔍 Focus</div>
  <div class="item" onclick="expandNode()">🕸 Expand Neighbors</div>
  <div class="item" onclick="hideLayer()">👁 Hide Layer</div>
  <div class="item" onclick="pinNode()">📌 Pin/Unpin</div>
  <div class="item" onclick="copyInfo()">📋 Copy Info</div>
</div>

<div class="panel" id="help">
  <h2>THEMANBEARPIG v6.0</h2>
  <p style="margin:8px 0;font-size:11px;opacity:0.7">Full Data Saturation — __TOTAL_NODES__ nodes / __TOTAL_LINKS__ links / 20 layers</p>
  <div style="text-align:left;font-size:10px;margin-top:12px">
    <span class="key">Scroll</span> Zoom &nbsp;
    <span class="key">Drag</span> Pan &nbsp;
    <span class="key">Click</span> Select &nbsp;
    <span class="key">Right-click</span> Menu<br>
    <span class="key">Ctrl+F</span> Search &nbsp;
    <span class="key">Esc</span> Deselect &nbsp;
    <span class="key">H</span> Help &nbsp;
    <span class="key">R</span> Reset view<br>
    <span class="key">1-9</span> Toggle layers &nbsp;
    <span class="key">0</span> Show all &nbsp;
    <span class="key">Space</span> Pause physics
  </div>
  <div style="margin-top:12px;font-size:9px;opacity:0.5">Built by LitigationOS SINGULARITY FORGE</div>
</div>

<div id="tooltip"></div>

<script src="https://d3js.org/d3.v7.min.js"></script>
<script>
// ══════════════════════════════════════
//  DATA INJECTION
// ══════════════════════════════════════
const NODES = __NODES__;
const LINKS = __LINKS__;
const LAYERS = __LAYERS__;
const STATS = __STATS__;
const SEP_DAYS = __SEP_DAYS__;

// ══════════════════════════════════════
//  CANVAS SETUP
// ══════════════════════════════════════
const canvas = document.getElementById('graph');
const ctx = canvas.getContext('2d');
const mmCanvas = document.getElementById('minimap');
const mmCtx = mmCanvas.getContext('2d');

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
resize();
window.addEventListener('resize', () => { resize(); render(); });

// ══════════════════════════════════════
//  STATE
// ══════════════════════════════════════
let transform = d3.zoomIdentity;
let selectedNode = null;
let hoveredNode = null;
let ctxNode = null;
let visibleLayers = new Set(LAYERS.map(l => l.id));
let paused = false;
let frameCount = 0;
let lastFpsTime = performance.now();
let fps = 0;

// Layer node counts
const layerCounts = {};
NODES.forEach(n => { layerCounts[n.layer] = (layerCounts[n.layer]||0) + 1; });

// ══════════════════════════════════════
//  LAYER CONTROLS
// ══════════════════════════════════════
const layerList = document.getElementById('layer-list');
LAYERS.forEach((L, i) => {
  const div = document.createElement('div');
  div.className = 'layer-btn';
  div.dataset.layer = L.id;
  div.innerHTML = `<span class="dot" style="background:${L.color}"></span>
    <span>${L.icon} ${L.label}</span>
    <span class="cnt">${layerCounts[L.id]||0}</span>`;
  div.onclick = () => toggleLayer(L.id);
  layerList.appendChild(div);
});

function toggleLayer(id) {
  if (visibleLayers.has(id)) visibleLayers.delete(id); else visibleLayers.add(id);
  document.querySelectorAll('.layer-btn').forEach(b => {
    b.classList.toggle('off', !visibleLayers.has(b.dataset.layer));
  });
  render();
}
function toggleAll(on) {
  if (on) LAYERS.forEach(l => visibleLayers.add(l.id));
  else visibleLayers.clear();
  document.querySelectorAll('.layer-btn').forEach(b => {
    b.classList.toggle('off', !visibleLayers.has(b.dataset.layer));
  });
  render();
}
function isVis(n) { return visibleLayers.has(n.layer); }

// ══════════════════════════════════════
//  STATS PANEL
// ══════════════════════════════════════
const statsDiv = document.getElementById('stats-content');
const statNames = {ev:'Evidence',wc:'Weapons',jv:'Violations',tl:'Timeline',
  im:'Impeachment',ct:'Contradictions',pr:'Police',cf:'Facts',ac:'Authority',bi:'Intelligence'};
let statsHTML = '';
for (const [k,v] of Object.entries(STATS)) {
  if (k === 'total') continue;
  statsHTML += `<div class="row"><span>${statNames[k]||k}</span><span class="v">${Number(v).toLocaleString()}</span></div>`;
}
statsHTML += `<div class="row" style="border-top:1px solid var(--accent);margin-top:4px;padding-top:4px"><span style="color:var(--gold)">TOTAL ROWS</span><span class="v" style="color:var(--gold)">${Number(STATS.total).toLocaleString()}</span></div>`;
statsDiv.innerHTML = statsHTML;

// ══════════════════════════════════════
//  FORCE SIMULATION
// ══════════════════════════════════════
const W = canvas.width, H = canvas.height;
const sim = d3.forceSimulation(NODES)
  .force('link', d3.forceLink(LINKS).id(d => d.id).distance(d => {
    const baseD = 40;
    if (d.type === 'FATHER_SON') return 60;
    if (d.type === 'FORMER_PARTNER' || d.type === 'MARRIED') return 80;
    if (d.type === 'ATTACK') return 30 + (1 - d.strength) * 40;
    return baseD + (1 - (d.strength||0.3)) * 60;
  }).strength(d => d.strength || 0.3))
  .force('charge', d3.forceManyBody().strength(d => -20 * d.r).theta(0.8))
  .force('center', d3.forceCenter(W/2, H/2).strength(0.03))
  .force('collision', d3.forceCollide().radius(d => d.r + 3).iterations(2))
  .force('x', d3.forceX(W/2).strength(0.015))
  .force('y', d3.forceY(H/2).strength(0.015))
  .alphaDecay(0.02)
  .velocityDecay(0.4);

sim.on('tick', () => {
  if (!paused) render();
  frameCount++;
  const now = performance.now();
  if (now - lastFpsTime > 1000) {
    fps = Math.round(frameCount * 1000 / (now - lastFpsTime));
    frameCount = 0;
    lastFpsTime = now;
  }
});

// ══════════════════════════════════════
//  ZOOM
// ══════════════════════════════════════
const zoomBehavior = d3.zoom()
  .scaleExtent([0.02, 20])
  .on('zoom', e => { transform = e.transform; render(); });
d3.select(canvas).call(zoomBehavior);

// ══════════════════════════════════════
//  HIT DETECTION
// ══════════════════════════════════════
function findNode(mx, my) {
  const [x, y] = transform.invert([mx, my]);
  let best = null, bestD = Infinity;
  for (const n of NODES) {
    if (!isVis(n)) continue;
    const dx = n.x - x, dy = n.y - y;
    const d2 = dx*dx + dy*dy;
    const hitR = Math.max(n.r, 6/transform.k);
    if (d2 < hitR*hitR*4 && d2 < bestD) { bestD = d2; best = n; }
  }
  return best;
}

// ══════════════════════════════════════
//  RENDER
// ══════════════════════════════════════
function drawGrid() {
  const s = 100 * transform.k;
  const ox = transform.x % s;
  const oy = transform.y % s;
  ctx.strokeStyle = 'rgba(0,204,255,0.03)';
  ctx.lineWidth = 1;
  for (let x = ox; x < canvas.width; x += s) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = oy; y < canvas.height; y += s) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }
}

function render() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#060a14';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  drawGrid();

  ctx.save();
  ctx.translate(transform.x, transform.y);
  ctx.scale(transform.k, transform.k);

  // Links
  const vLinks = LINKS.filter(l => isVis(l.source) && isVis(l.target));
  for (const l of vLinks) {
    ctx.beginPath();
    ctx.moveTo(l.source.x, l.source.y);
    ctx.lineTo(l.target.x, l.target.y);
    ctx.strokeStyle = l.color || '#1a3a5a';
    ctx.globalAlpha = l.type === 'FATHER_SON' ? 0.8 :
                      l.type === 'FORMER_PARTNER' || l.type === 'MARRIED' ? 0.6 : 0.15;
    ctx.lineWidth = (l.width || 0.5);
    ctx.stroke();
  }
  ctx.globalAlpha = 1;

  // Nodes
  const vNodes = NODES.filter(isVis);
  for (const n of vNodes) {
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
    ctx.fillStyle = n.color;

    // Glow for threats
    if (n.threat > 6) {
      ctx.shadowBlur = n.threat * 2;
      ctx.shadowColor = n.color;
    }
    ctx.fill();
    ctx.shadowBlur = 0;

    // Selection ring
    if (n === selectedNode) {
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2.5;
      ctx.stroke();
    } else if (n === hoveredNode) {
      ctx.strokeStyle = 'rgba(0,204,255,0.6)';
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }

  // Labels
  const zk = transform.k;
  if (zk > 0.4) {
    const fontSize = Math.max(7, Math.min(12, 10/zk));
    ctx.font = `${fontSize}px Consolas`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    for (const n of vNodes) {
      const showLabel = (n.r > 8) || (zk > 1 && n.r > 4) || (zk > 2.5) || n === selectedNode || n === hoveredNode;
      if (!showLabel) continue;
      ctx.fillStyle = n === selectedNode ? '#ffffff' : 'rgba(200,216,232,0.75)';
      const lbl = n.label.length > 35 ? n.label.slice(0,33) + '..' : n.label;
      ctx.fillText(lbl, n.x, n.y - n.r - 3);
    }
  }

  ctx.restore();

  // HUD
  document.getElementById('h-nodes').textContent = vNodes.length;
  document.getElementById('h-links').textContent = vLinks.length;
  document.getElementById('h-layers').textContent = visibleLayers.size;
  document.getElementById('h-fps').textContent = fps;
  document.getElementById('h-threats').textContent = vNodes.filter(n => n.threat > 6).length;

  // Minimap
  renderMinimap(vNodes);
}

// ══════════════════════════════════════
//  MINIMAP
// ══════════════════════════════════════
function renderMinimap(vNodes) {
  if (!vNodes) vNodes = NODES.filter(isVis);
  const mw = 160, mh = 120;
  mmCtx.clearRect(0, 0, mw, mh);
  mmCtx.fillStyle = 'rgba(6,10,20,0.95)';
  mmCtx.fillRect(0, 0, mw, mh);
  if (vNodes.length === 0) return;

  let minX=Infinity, maxX=-Infinity, minY=Infinity, maxY=-Infinity;
  for (const n of vNodes) {
    if (n.x < minX) minX = n.x; if (n.x > maxX) maxX = n.x;
    if (n.y < minY) minY = n.y; if (n.y > maxY) maxY = n.y;
  }
  const pad = 50;
  const rangeX = (maxX - minX + pad*2) || 1;
  const rangeY = (maxY - minY + pad*2) || 1;
  const scale = Math.min(mw / rangeX, mh / rangeY);
  const ox = (mw - rangeX * scale) / 2;
  const oy = (mh - rangeY * scale) / 2;

  for (const n of vNodes) {
    const mx = ox + (n.x - minX + pad) * scale;
    const my = oy + (n.y - minY + pad) * scale;
    mmCtx.fillStyle = n.color;
    mmCtx.fillRect(mx-1, my-1, 2, 2);
  }

  // Viewport rectangle
  const vx1 = -transform.x / transform.k;
  const vy1 = -transform.y / transform.k;
  const vx2 = vx1 + canvas.width / transform.k;
  const vy2 = vy1 + canvas.height / transform.k;
  mmCtx.strokeStyle = 'rgba(0,204,255,0.5)';
  mmCtx.lineWidth = 1;
  mmCtx.strokeRect(
    ox + (vx1 - minX + pad) * scale,
    oy + (vy1 - minY + pad) * scale,
    (vx2 - vx1) * scale,
    (vy2 - vy1) * scale
  );
}

// ══════════════════════════════════════
//  INTERACTIONS
// ══════════════════════════════════════
canvas.addEventListener('mousemove', e => {
  const n = findNode(e.clientX, e.clientY);
  if (n !== hoveredNode) {
    hoveredNode = n;
    canvas.style.cursor = n ? 'pointer' : 'crosshair';
    const tt = document.getElementById('tooltip');
    if (n) {
      tt.innerHTML = `<b style="color:${n.color}">${n.label}</b><br><span style="opacity:0.7">${n.desc||''}</span>`;
      tt.style.display = 'block';
      tt.style.left = (e.clientX + 12) + 'px';
      tt.style.top = (e.clientY - 10) + 'px';
    } else {
      tt.style.display = 'none';
    }
    render();
  } else if (n) {
    const tt = document.getElementById('tooltip');
    tt.style.left = (e.clientX + 12) + 'px';
    tt.style.top = (e.clientY - 10) + 'px';
  }
});

canvas.addEventListener('click', e => {
  const n = findNode(e.clientX, e.clientY);
  selectedNode = n;
  const info = document.getElementById('info');
  if (n) {
    info.style.display = 'block';
    document.getElementById('info-title').innerHTML = `<span style="color:${n.color}">${n.label}</span>`;
    let html = `<div class="field"><span class="k">Layer</span><span class="v">${n.layer}</span></div>`;
    html += `<div class="field"><span class="k">Group</span><span class="v">${n.group}</span></div>`;
    if (n.threat) html += `<div class="field"><span class="k">Threat</span><span class="v red">${n.threat}/10</span></div>`;
    if (n.desc) html += `<div class="field"><span class="k">Info</span><span class="v">${n.desc}</span></div>`;
    if (n.data) {
      for (const [k,v] of Object.entries(n.data)) {
        if (v) html += `<div class="field"><span class="k">${k}</span><span class="v">${v}</span></div>`;
      }
    }
    // Connected nodes
    const connected = LINKS.filter(l => (l.source === n || l.source.id === n.id || l.target === n || l.target.id === n.id));
    html += `<div class="field" style="margin-top:6px;border-top:1px solid var(--border);padding-top:4px"><span class="k">Connections</span><span class="v accent">${connected.length}</span></div>`;
    document.getElementById('info-content').innerHTML = html;
  } else {
    info.style.display = 'none';
  }
  render();
});

canvas.addEventListener('contextmenu', e => {
  e.preventDefault();
  const n = findNode(e.clientX, e.clientY);
  ctxNode = n;
  const menu = document.getElementById('ctx-menu');
  if (n) {
    menu.style.display = 'block';
    menu.style.left = e.clientX + 'px';
    menu.style.top = e.clientY + 'px';
  } else {
    menu.style.display = 'none';
  }
});

document.addEventListener('click', e => {
  if (!e.target.closest('#ctx-menu')) document.getElementById('ctx-menu').style.display = 'none';
});

// Context menu actions
function focusNode() {
  if (!ctxNode) return;
  const x = canvas.width/2 - ctxNode.x * 3;
  const y = canvas.height/2 - ctxNode.y * 3;
  d3.select(canvas).transition().duration(750).call(
    zoomBehavior.transform, d3.zoomIdentity.translate(x, y).scale(3));
  document.getElementById('ctx-menu').style.display = 'none';
}
function expandNode() {
  if (!ctxNode) return;
  const neighbors = new Set();
  LINKS.forEach(l => {
    if (l.source === ctxNode || l.source.id === ctxNode.id) neighbors.add(typeof l.target === 'object' ? l.target.layer : '');
    if (l.target === ctxNode || l.target.id === ctxNode.id) neighbors.add(typeof l.source === 'object' ? l.source.layer : '');
  });
  neighbors.forEach(ly => { if (ly) visibleLayers.add(ly); });
  document.querySelectorAll('.layer-btn').forEach(b => b.classList.toggle('off', !visibleLayers.has(b.dataset.layer)));
  render();
  document.getElementById('ctx-menu').style.display = 'none';
}
function hideLayer() {
  if (!ctxNode) return;
  visibleLayers.delete(ctxNode.layer);
  document.querySelectorAll('.layer-btn').forEach(b => b.classList.toggle('off', !visibleLayers.has(b.dataset.layer)));
  render();
  document.getElementById('ctx-menu').style.display = 'none';
}
function pinNode() {
  if (!ctxNode) return;
  if (ctxNode.fx != null) { ctxNode.fx = null; ctxNode.fy = null; }
  else { ctxNode.fx = ctxNode.x; ctxNode.fy = ctxNode.y; }
  document.getElementById('ctx-menu').style.display = 'none';
}
function copyInfo() {
  if (!ctxNode) return;
  const text = `${ctxNode.label}\nLayer: ${ctxNode.layer}\n${ctxNode.desc}\n${JSON.stringify(ctxNode.data, null, 2)}`;
  navigator.clipboard.writeText(text);
  document.getElementById('ctx-menu').style.display = 'none';
}

// ══════════════════════════════════════
//  SEARCH
// ══════════════════════════════════════
const searchInput = document.getElementById('search');
searchInput.addEventListener('input', e => {
  const q = e.target.value.toLowerCase().trim();
  if (!q) { NODES.forEach(n => n._searchHide = false); render(); return; }
  NODES.forEach(n => {
    const text = `${n.label} ${n.desc} ${n.group} ${n.layer} ${JSON.stringify(n.data)}`.toLowerCase();
    n._searchHide = !text.includes(q);
  });
  render();
});
const origIsVis = isVis;
// Override isVis to include search
window.isVis = function(n) { return visibleLayers.has(n.layer) && !n._searchHide; };

// ══════════════════════════════════════
//  KEYBOARD
// ══════════════════════════════════════
document.addEventListener('keydown', e => {
  if (e.target === searchInput) return;
  if (e.key === 'h' || e.key === 'H') {
    const h = document.getElementById('help');
    h.style.display = h.style.display === 'none' ? 'block' : 'none';
  }
  if (e.key === 'Escape') {
    selectedNode = null;
    document.getElementById('info').style.display = 'none';
    document.getElementById('help').style.display = 'none';
    render();
  }
  if (e.key === 'r' || e.key === 'R') {
    d3.select(canvas).transition().duration(750).call(zoomBehavior.transform, d3.zoomIdentity);
  }
  if (e.key === ' ') {
    e.preventDefault();
    paused = !paused;
    if (!paused) sim.alpha(0.3).restart();
    else sim.stop();
  }
  if (e.ctrlKey && e.key === 'f') {
    e.preventDefault();
    searchInput.focus();
  }
  // Number keys toggle layers
  const num = parseInt(e.key);
  if (num >= 1 && num <= 9 && num <= LAYERS.length) {
    toggleLayer(LAYERS[num-1].id);
  }
  if (e.key === '0') toggleAll(true);
});

// ══════════════════════════════════════
//  DRAG
// ══════════════════════════════════════
let dragNode = null;
d3.select(canvas).call(d3.drag()
  .subject(e => {
    const [x, y] = transform.invert([e.x, e.y]);
    let best = null, bestD = Infinity;
    for (const n of NODES) {
      if (!isVis(n)) continue;
      const dx = n.x - x, dy = n.y - y;
      const d2 = dx*dx + dy*dy;
      if (d2 < n.r*n.r*9 && d2 < bestD) { bestD = d2; best = n; }
    }
    return best;
  })
  .on('start', e => {
    if (!e.subject) return;
    dragNode = e.subject;
    if (!e.active) sim.alphaTarget(0.3).restart();
    dragNode.fx = dragNode.x;
    dragNode.fy = dragNode.y;
  })
  .on('drag', e => {
    if (!dragNode) return;
    const [x, y] = transform.invert([e.x, e.y]);
    dragNode.fx = x;
    dragNode.fy = y;
  })
  .on('end', e => {
    if (!dragNode) return;
    if (!e.active) sim.alphaTarget(0);
    if (!dragNode._pinned) { dragNode.fx = null; dragNode.fy = null; }
    dragNode = null;
  })
);

// ══════════════════════════════════════
//  SEPARATION COUNTER UPDATE
// ══════════════════════════════════════
setInterval(() => {
  const now = new Date();
  const sep = new Date(2025, 6, 29);
  const days = Math.floor((now - sep) / 86400000);
  const el = document.querySelector('#sep-counter .days');
  if (el) el.textContent = days;
}, 60000);

// Initial zoom to fit
setTimeout(() => {
  let minX=Infinity, maxX=-Infinity, minY=Infinity, maxY=-Infinity;
  NODES.forEach(n => {
    if (n.x < minX) minX = n.x; if (n.x > maxX) maxX = n.x;
    if (n.y < minY) minY = n.y; if (n.y > maxY) maxY = n.y;
  });
  const pad = 100;
  const rangeX = maxX - minX + pad*2;
  const rangeY = maxY - minY + pad*2;
  const scale = Math.min(canvas.width/rangeX, canvas.height/rangeY, 1) * 0.85;
  const cx = (minX + maxX) / 2;
  const cy = (minY + maxY) / 2;
  d3.select(canvas).transition().duration(1500).call(
    zoomBehavior.transform,
    d3.zoomIdentity.translate(canvas.width/2 - cx*scale, canvas.height/2 - cy*scale).scale(scale)
  );
}, 3000);

console.log(`THEMANBEARPIG v6.0 loaded: ${NODES.length} nodes, ${LINKS.length} links, ${LAYERS.length} layers`);
</script>
</body>
</html>'''

# ═══════════════ ASSEMBLY ═══════════════
def build():
    print("=" * 60)
    print("  THEMANBEARPIG v6.0 — Full Data Saturation Build")
    print("=" * 60)
    print(f"  Separation: {SEP_DAYS} days")
    print(f"  Database: {DB}")
    print(f"  Output: {OUT}")
    print()

    # Extract
    D = extract()
    print()

    # Generate nodes & links
    nodes = gen_nodes(D)
    links = gen_links(nodes, D)
    print()

    # Assemble HTML
    print("Assembling HTML...")
    html = HTML
    html = html.replace('__NODES__', json.dumps(nodes, default=str, ensure_ascii=False))
    html = html.replace('__LINKS__', json.dumps(links, default=str, ensure_ascii=False))
    html = html.replace('__LAYERS__', json.dumps(LAYER_META))
    html = html.replace('__STATS__', json.dumps(D['stats']))
    html = html.replace('__SEP_DAYS__', str(SEP_DAYS))
    html = html.replace('__TOTAL_NODES__', str(len(nodes)))
    html = html.replace('__TOTAL_LINKS__', str(len(links)))

    # Save
    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT).write_text(html, encoding='utf-8')
    size_kb = Path(OUT).stat().st_size / 1024
    print(f"\n✅ THEMANBEARPIG v6.0 saved: {OUT}")
    print(f"   Size: {size_kb:.0f} KB")
    print(f"   Nodes: {len(nodes)}")
    print(f"   Links: {len(links)}")
    print(f"   Layers: {len(LAYER_META)}")
    print(f"   Data rows ingested: {D['stats']['total']:,}")

    # Also save to workspace
    ws = Path(r"C:\Users\andre\LitigationOS\12_WORKSPACE\THEMANBEARPIG_v6")
    ws.mkdir(exist_ok=True)
    (ws / "THEMANBEARPIG_v6.html").write_text(html, encoding='utf-8')
    print(f"   Copy: {ws / 'THEMANBEARPIG_v6.html'}")

    # Save data JSON for debugging
    data_json = ws / "graph_data_v6.json"
    with open(data_json, 'w', encoding='utf-8') as f:
        json.dump({"nodes": len(nodes), "links": len(links), "stats": D['stats'],
                    "layers": [l['id'] for l in LAYER_META]}, f, indent=2)
    print(f"   Data: {data_json}")

    return len(nodes), len(links)

if __name__ == '__main__':
    build()
