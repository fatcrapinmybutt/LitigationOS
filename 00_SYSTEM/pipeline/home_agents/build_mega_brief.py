#!/usr/bin/env python3
# MEGA INTELLIGENCE BRIEF GENERATOR
# Synthesizes all 50 agent journals into a single master intelligence document
import os,re,json,datetime,collections

JDIR = r"C:\Users\andre\Desktop\AGENT_JOURNALS"
OUT = r"C:\Users\andre\Desktop\AGENT_JOURNALS\00_FLEET_DASHBOARD\MEGA_INTELLIGENCE_BRIEF.md"

def extract_all(jpath):
    entries = []
    current_file = None
    current_path = None
    try:
        with open(jpath,'r',encoding='utf-8',errors='replace') as f:
            for line in f:
                if line.startswith('## '):
                    current_file = line[3:].strip()
                elif line.startswith('**Path:**'):
                    current_path = line.split('`')[1] if '`' in line else ''
                elif line.startswith('- **'):
                    parts = line.strip()[4:].split('**',1)
                    finding = parts[0] if parts else ''
                    context = ''
                    entries.append({'file':current_file,'path':current_path,'finding':finding,'context':''})
                elif line.strip().startswith('> ') and entries:
                    entries[-1]['context'] = line.strip()[2:][:300]
    except: pass
    return entries

def normalize_cite(s):
    s = s.lower().strip()
    s = re.sub(r'\s+',' ',s)
    s = re.sub(r'[^a-z0-9. ]','',s)
    return s

def main():
    print("Building MEGA INTELLIGENCE BRIEF...",flush=True)
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    # Collect ALL findings from ALL agents
    agent_data = {}
    total_finds = 0
    for agent_dir in sorted(os.listdir(JDIR)):
        if agent_dir == "00_FLEET_DASHBOARD": continue
        ap = os.path.join(JDIR, agent_dir)
        if not os.path.isdir(ap): continue
        entries = []
        for jf in os.listdir(ap):
            if jf.startswith("journal_"):
                entries.extend(extract_all(os.path.join(ap,jf)))
        agent_data[agent_dir] = entries
        total_finds += len(entries)

    # Build citation frequency map
    cite_freq = collections.Counter()
    for aid in ['01_MCL','02_MCR','03_CASELAW','04_USC','06_CONSTITUTION']:
        for e in agent_data.get(aid,[]):
            key = normalize_cite(e['finding'])
            if len(key) > 3:
                cite_freq[key] += 1

    # Build person frequency
    person_freq = collections.Counter()
    for aid in ['09_ANDREW','10_EMILY','11_ALBERT','12_LORI','13_CODY','14_MCNEILL','15_RUSCO','16_CHILD','17_PERSONS']:
        for e in agent_data.get(aid,[]):
            key = e['finding'].strip().lower()[:60]
            if len(key) > 2:
                person_freq[key] += 1

    # Build alienation evidence
    alienation_evidence = []
    for e in agent_data.get('18_ALIENATION',[]):
        if e['context']:
            alienation_evidence.append((e['finding'],e['context'],e.get('file','')))

    # Build violation evidence
    violation_evidence = []
    for aid in ['25_VIOLATIONS','21_DUE_PROCESS','22_MISCONDUCT','23_FRAUD']:
        for e in agent_data.get(aid,[]):
            if e['context']:
                violation_evidence.append((aid,e['finding'],e['context'],e.get('file','')))

    # Build MCR frequency for procedural weapons
    mcr_freq = collections.Counter()
    for e in agent_data.get('02_MCR',[]):
        key = e['finding'].strip().upper()[:20]
        if key.startswith('MCR'):
            mcr_freq[key] += 1

    # Build MCL frequency
    mcl_freq = collections.Counter()
    for e in agent_data.get('01_MCL',[]):
        key = e['finding'].strip().upper()[:20]
        if key.startswith('MCL'):
            mcl_freq[key] += 1

    # Write MEGA BRIEF
    with open(OUT,'w',encoding='utf-8') as f:
        f.write("# MEGA INTELLIGENCE BRIEF\n")
        f.write("## Pigors v. Watson - 50-Agent Fleet Synthesis\n\n")
        f.write("**Generated:** "+now+"\n")
        f.write("**Agents Active:** "+str(len(agent_data))+"\n")
        f.write("**Total Findings:** "+str(total_finds)+"\n")
        f.write("**Case:** Pigors v. Watson, 14th Judicial Circuit, Muskegon County\n")
        f.write("**Focal Point:** Parental alienation, 329+ days child separation\n\n")
        f.write("---\n\n")

        # SECTION 1: AUTHORITY ARSENAL
        f.write("# I. LEGAL AUTHORITY ARSENAL\n\n")
        f.write("## Michigan Court Rules (MCR) - Top 30\n\n")
        f.write("| Rank | MCR | Citations |\n|------|-----|----------|\n")
        for i,(mcr,cnt) in enumerate(mcr_freq.most_common(30),1):
            f.write("| "+str(i)+" | "+mcr+" | "+str(cnt)+" |\n")

        f.write("\n## Michigan Compiled Laws (MCL) - Top 30\n\n")
        f.write("| Rank | MCL | Citations |\n|------|-----|----------|\n")
        for i,(mcl,cnt) in enumerate(mcl_freq.most_common(30),1):
            f.write("| "+str(i)+" | "+mcl+" | "+str(cnt)+" |\n")

        f.write("\n## Case Law - Top 30\n\n")
        f.write("| Rank | Citation | Frequency |\n|------|----------|----------|\n")
        caselaw = collections.Counter()
        for e in agent_data.get('03_CASELAW',[]):
            key = e['finding'].strip()[:60]
            if len(key)>5:
                caselaw[key] += 1
        for i,(c,cnt) in enumerate(caselaw.most_common(30),1):
            f.write("| "+str(i)+" | "+c+" | "+str(cnt)+" |\n")

        # SECTION 2: PARENTAL ALIENATION DOSSIER
        f.write("\n\n# II. PARENTAL ALIENATION DOSSIER\n\n")
        f.write("**Total alienation indicators harvested:** "+str(len(agent_data.get('18_ALIENATION',[])))+"\n\n")
        alien_types = collections.Counter()
        for e in agent_data.get('18_ALIENATION',[]):
            alien_types[e['finding'].lower().strip()[:40]] += 1
        f.write("### Alienation Patterns Detected\n\n")
        f.write("| Pattern | Occurrences |\n|---------|------------|\n")
        for pat,cnt in alien_types.most_common(20):
            f.write("| "+pat+" | "+str(cnt)+" |\n")
        f.write("\n### Key Alienation Evidence (with context)\n\n")
        seen = set()
        for finding,ctx,src in alienation_evidence[:50]:
            key = ctx[:80].lower()
            if key not in seen:
                seen.add(key)
                f.write("**["+finding+"]** from `"+str(src)+"`\n")
                f.write("> "+ctx+"\n\n")

        # SECTION 3: WATSON FAMILY INTELLIGENCE
        f.write("\n# III. WATSON FAMILY INTELLIGENCE\n\n")
        for aid,label in [('10_EMILY','Emily Watson'),('11_ALBERT','Albert Watson'),('12_LORI','Lori Watson'),('13_CODY','Cody Watson')]:
            entries = agent_data.get(aid,[])
            f.write("## "+label+" ("+str(len(entries))+" findings)\n\n")
            types = collections.Counter()
            for e in entries:
                types[e['finding'].lower().strip()[:50]] += 1
            for t,cnt in types.most_common(10):
                f.write("- **"+t+"** ("+str(cnt)+"x)\n")
            f.write("\n### Key Quotes\n\n")
            shown = set()
            for e in entries[:20]:
                if e['context'] and e['context'][:60] not in shown:
                    shown.add(e['context'][:60])
                    f.write("> "+e['context']+"\n\n")
            f.write("\n")

        # SECTION 4: JUDICIAL MISCONDUCT DOSSIER
        f.write("\n# IV. JUDICIAL MISCONDUCT DOSSIER (Judge McNeill)\n\n")
        mcneill = agent_data.get('14_MCNEILL',[])
        misconduct = agent_data.get('22_MISCONDUCT',[])
        f.write("**McNeill references:** "+str(len(mcneill))+"\n")
        f.write("**Misconduct indicators:** "+str(len(misconduct))+"\n\n")
        f.write("### McNeill Actions Documented\n\n")
        mc_types = collections.Counter()
        for e in mcneill:
            mc_types[e['finding'].lower().strip()[:50]] += 1
        for t,cnt in mc_types.most_common(15):
            f.write("- **"+t+"** ("+str(cnt)+"x)\n")
        f.write("\n### Misconduct Evidence\n\n")
        shown = set()
        for e in misconduct[:30]:
            if e['context'] and e['context'][:60] not in shown:
                shown.add(e['context'][:60])
                f.write("**["+e['finding']+"]**\n> "+e['context']+"\n\n")

        # SECTION 5: DUE PROCESS & VIOLATIONS
        f.write("\n# V. DUE PROCESS & RIGHTS VIOLATIONS\n\n")
        dp = agent_data.get('21_DUE_PROCESS',[])
        viol = agent_data.get('25_VIOLATIONS',[])
        f.write("**Due process findings:** "+str(len(dp))+"\n")
        f.write("**Violation findings:** "+str(len(viol))+"\n\n")
        all_viols = []
        for aid in ['21_DUE_PROCESS','25_VIOLATIONS','45_PROCEDURAL']:
            for e in agent_data.get(aid,[]):
                if e['context']:
                    all_viols.append((e['finding'],e['context'],e.get('file','')))
        f.write("### Violation Evidence\n\n")
        shown = set()
        for finding,ctx,src in all_viols[:40]:
            key = ctx[:60].lower()
            if key not in seen:
                seen.add(key)
                f.write("**["+finding+"]** `"+str(src)+"`\n> "+ctx+"\n\n")

        # SECTION 6: FINANCIAL DAMAGES
        f.write("\n# VI. FINANCIAL DAMAGES & COSTS\n\n")
        fin = agent_data.get('32_FINANCIAL',[])
        dollar_amounts = []
        for e in fin:
            m = re.search(r'\$[\d,]+(?:\.\d{2})?', e['finding'])
            if m:
                dollar_amounts.append((m.group(), e.get('context',''), e.get('file','')))
        f.write("**Financial references:** "+str(len(fin))+"\n")
        f.write("**Dollar amounts found:** "+str(len(dollar_amounts))+"\n\n")
        amt_freq = collections.Counter(a[0] for a in dollar_amounts)
        f.write("| Amount | Occurrences |\n|--------|------------|\n")
        for amt,cnt in amt_freq.most_common(30):
            f.write("| "+amt+" | "+str(cnt)+" |\n")

        # SECTION 7: ANDREW'S NARRATIVE
        f.write("\n\n# VII. ANDREW'S NARRATIVE\n\n")
        andrew = agent_data.get('09_ANDREW',[])
        narrative = agent_data.get('34_NARRATIVE',[])
        f.write("**Andrew mentions:** "+str(len(andrew))+"\n")
        f.write("**Narrative segments:** "+str(len(narrative))+"\n\n")
        f.write("### Father's Voice (direct quotes)\n\n")
        shown = set()
        for e in andrew:
            if e['finding'].lower().startswith('i ') and e['context']:
                key = e['context'][:60].lower()
                if key not in shown and len(shown)<25:
                    shown.add(key)
                    f.write("> "+e['context']+"\n\n")

        # SECTION 8: CHILD LDW
        f.write("\n# VIII. CHILD WELFARE (L.D.W.)\n\n")
        child = agent_data.get('16_CHILD',[])
        welfare = agent_data.get('35_WELFARE',[])
        bond = agent_data.get('36_BOND',[])
        best_int = agent_data.get('31_BEST_INT',[])
        f.write("**Child references:** "+str(len(child))+"\n")
        f.write("**Welfare findings:** "+str(len(welfare))+"\n")
        f.write("**Bonding findings:** "+str(len(bond))+"\n")
        f.write("**Best interest findings:** "+str(len(best_int))+"\n\n")

        # SECTION 9: EMERGENCY & REMEDIES
        f.write("\n# IX. EMERGENCY RELIEF & REMEDIES\n\n")
        emerg = agent_data.get('42_EMERGENCY',[])
        remedies = agent_data.get('43_REMEDIES',[])
        f.write("**Emergency findings:** "+str(len(emerg))+"\n")
        f.write("**Remedy findings:** "+str(len(remedies))+"\n\n")

        # SECTION 10: CASE NUMBERS & DOCKET
        f.write("\n# X. CASE NUMBERS & DOCKET\n\n")
        cases = agent_data.get('50_CASE_NO',[])
        case_types = collections.Counter()
        for e in cases:
            case_types[e['finding'].strip()[:40]] += 1
        for c,cnt in case_types.most_common(20):
            f.write("- **"+c+"** ("+str(cnt)+"x)\n")

        # FOOTER
        f.write("\n\n---\n")
        f.write("*Generated by LitigationOS Agent Fleet v1.0 | 50 agents | "+now+"*\n")
        f.write("*All findings extracted from C:\\Users\\andre\\Scans via regex pattern matching*\n")

    sz = os.path.getsize(OUT)
    print("MEGA INTELLIGENCE BRIEF: "+str(sz)+" bytes ("+str(round(sz/1024,1))+" KB)",flush=True)
    print("Saved to:",OUT,flush=True)

if __name__=='__main__':
    main()