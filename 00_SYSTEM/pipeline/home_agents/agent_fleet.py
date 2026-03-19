#!/usr/bin/env python3
# AGENT FLEET HARVESTER v1.0 - 50 Specialized Judicial Intelligence Agents
# LitigationOS - Pigors v. Watson - Full Recursive Scan
# Each agent harvests curated judicial data types, maintaining individual journals.
import os,re,sys,json,time,datetime,traceback

SCAN=r"C:\Users\andre\Scans"
JDIR=r"C:\Users\andre\Desktop\AGENT_JOURNALS"
PROG=r"D:\TEMP\agent_fleet_progress.json"

TEXT_EXT={'.txt','.md','.csv','.json','.jsonl','.html','.htm','.cypher','.sql',
          '.log','.graphml','.rtf','.xml','.yaml','.yml','.rst','.eml','.cfg',
          '.ini','.toml','.tsx','.jsx','.ts','.js','.mdx','.ndjson','.ipynb'}
DOC_EXT={'.pdf','.docx'}
SKIP={'node_modules','__pycache__','.git','.vscode','site-packages',
      'java-1.8.0-openjdk-1.8.0.392-1.b08.redhat.windows.x86_64',
      '.tox','venv','.venv','Lib','Scripts','Include','dist-packages',
      '__MACOSX','DLLs','tcl','tk','Tcl','encodings','__pycache__'}

AG={
"01_MCL":("MCL Citations",[r'MCL\s*[^a-zA-Z\d]*\d+[\.\-]\d+\w*',r'Michigan\s+Compiled\s+Laws?\s*[^a-zA-Z\d]*\d+']),
"02_MCR":("MCR Rules",[r'MCR\s*\d+\.\d+(?:\([A-Za-z0-9]+\))*',r'Michigan\s+Court\s+Rules?\s+\d+']),
"03_CASELAW":("Case Citations",[r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+v\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*\d+\s+(?:Mich|NW|US|F\.\d|S\.?\s*Ct)',r'In\s+re\s+[A-Z][a-z]+',r'\d+\s+Mich(?:\s+App)?\s+\d+']),
"04_USC":("Federal Statutes",[r'\d+\s+U\.?S\.?C\.?\s*[^a-zA-Z\d]*\d+',r'(?:42|28|18|5)\s+USC\s+[^a-zA-Z\d]*\d+']),
"05_CFR":("Federal Regulations",[r'\d+\s+C\.?F\.?R\.?\s*[^a-zA-Z\d]*\d+',r'Code\s+of\s+Federal\s+Regulations']),
"06_CONSTITUTION":("Constitutional Provisions",[r'(?:First|Fourth|Fifth|Sixth|Eighth|Ninth|Fourteenth)\s+Amendment',r'U\.?S\.?\s*Const\.?\s*(?:art|amend)',r'Mich\.?\s*Const\.?\s*(?:art|[^a-zA-Z\d])\s*\d+']),
"07_BENCHBOOK":("Benchbook References",[r'[Bb]enchbook',r'Michigan\s+(?:Judicial|Family)\s+(?:Institute|Benchbook)',r'(?:pattern|model)\s+(?:jury\s+)?instruction']),
"08_AUTHORITY":("General Authorities",[r'(?:Restatement|Black.?s\s+Law|Am\.?\s*Jur|ALR|CJS)',r'(?:treatise|commentary|annotation|law\s+review)']),
"09_ANDREW":("Andrew/Father",[r'Andrew\s+(?:J\.?\s+)?Pigors',r'(?:father|dad|Pigors)\s+\w+\s+\w+',r'(?:I\s+(?:was|am|have|had|did|went|tried|filed|asked|requested|demanded))',r'(?:my\s+(?:son|child|rights?|case|family|life|home|job))']),
"10_EMILY":("Emily Watson",[r'Emily\s+(?:\w+\s+)?Watson',r'Watson,?\s*Emily',r'(?:mother|respondent|defendant)\s+(?:\w+\s+){0,2}(?:Emily|Watson)',r'(?:Emily|mother)\s+(?:filed|claimed|alleged|refused|denied|failed)']),
"11_ALBERT":("Albert Watson",[r'Albert\s+Watson',r'Watson,?\s*Albert',r'(?:maternal\s+grandfather|Albert)\s+\w+']),
"12_LORI":("Lori Watson",[r'Lori\s+Watson',r'Watson,?\s*Lori',r'(?:maternal\s+grandmother|Lori)\s+\w+']),
"13_CODY":("Cody Watson",[r'Cody\s+Watson',r'Watson,?\s*Cody']),
"14_MCNEILL":("Judge McNeill",[r'(?:Judge|Hon\.?|Justice)?\s*(?:Jenny)?\s*(?:L\.?)?\s*McNeill',r'McNeill\s+\w+',r'(?:the\s+(?:trial\s+)?(?:court|judge))\s+(?:\w+\s+){0,3}(?:ordered|ruled|found|held|denied|granted)']),
"15_RUSCO":("Attorney Rusco",[r'(?:Attorney|Counsel)?\s*Rusco',r'Rusco\s+\w+',r'(?:opposing\s+counsel|mother.?s\s+attorney)\s+\w+']),
"16_CHILD":("Child LDW",[r'L\.?D\.?W\.?',r'(?:the\s+)?minor\s+child',r'(?:son|baby|boy|toddler)',r'(?:born\s+(?:on\s+)?(?:November|Nov)?\s*9?,?\s*2022)']),
"17_PERSONS":("Other Persons",[r'(?:Martini|Dr\.?\s*(?:Richard\s+)?Bone|Officer\s+(?:Ella\s+)?Randall)',r'(?:Guardian|GAL|Referee|Mediator|Evaluator)\s+[A-Z][a-z]+']),
"18_ALIENATION":("Parental Alienation",[r'(?:parental\s+)?alienat(?:ion|ing|ed)',r'(?:interfere?(?:nce|d|ing)?\s+with\s+(?:parent|custod|relationship|bond))',r'withhold(?:ing)?\s+(?:the\s+)?(?:child|contact|access)',r'(?:gatekeep|obstruct|estrange|denied?\s+access)',r'(?:coaching|manipulat|brainwash)',r'(?:turned?\s+(?:the\s+child|him|her)\s+against)']),
"19_CUSTODY":("Custody & PT",[r'(?:custody|parenting\s+time|visitation|placement)',r'(?:joint|sole|primary|physical|legal)\s+custody',r'(?:parenting\s+(?:plan|schedule|order))',r'overnights?|weekends?|holidays?']),
"20_PPO":("PPO & Protection",[r'(?:PPO|personal\s+protection|protective\s+order|restraining)',r'(?:MCL\s+600\.2950|MCR\s+3\.70)',r'(?:no.?contact|stay.?away|stalking|harassment)']),
"21_DUE_PROCESS":("Due Process",[r'due\s+process',r'(?:notice\s+and\s+(?:an?\s+)?(?:opportunity|hearing))',r'Mathews\s+v\.?\s+Eldridge',r'(?:liberty\s+interest|fundamental\s+right)',r'(?:Troxel|Stanley|Santosky|Lassiter)']),
"22_MISCONDUCT":("Judicial Misconduct",[r'(?:judicial\s+(?:misconduct|bias|prejudice|impropriety|corruption))',r'Canon\s+\d',r'Code\s+of\s+(?:Judicial\s+)?Conduct',r'(?:JTC|Judicial\s+Tenure)']),
"23_FRAUD":("Fraud & Perjury",[r'(?:fraud(?:ulent)?|perjur(?:y|ious))',r'false\s+(?:statement|testimony|claim|allegation|report)',r'(?:lied?|lying|fabricat|deceiv|mislead)',r'(?:CPS|protective\s+services|DHHS)\s+(?:false|report)']),
"24_CONTEMPT":("Contempt & Sanctions",[r'(?:contempt|sanction(?:s|ed)?)',r'(?:show\s+cause|purge\s+condition)',r'willful(?:ly)?\s+(?:violat|disobey|refus)',r'(?:vexatious|frivolous|bad\s+faith)']),
"25_VIOLATIONS":("Rights Violations",[r'(?:violat(?:ion|ed|ing)|depri(?:vation|ved)|infring(?:ement|ed))',r'without\s+(?:notice|hearing|opportunity|due\s+process|counsel)',r'(?:ex\s+parte|unilateral(?:ly)?)',r'(?:abuse\s+of\s+discretion)']),
"26_HEARINGS":("Hearings",[r'(?:hearing|proceeding|trial|conference|oral\s+argument)',r'(?:transcript|testimony|deposition|affidavit)',r'(?:evidentiary\s+hearing|status\s+conference)',r'(?:scheduled|continued|adjourned|postponed)']),
"27_ORDERS":("Court Orders",[r'(?:court\s+)?order(?:ed)?|ruling|judgment|decree',r'(?:hereby\s+ordered|it\s+is\s+ordered)',r'(?:stipulat(?:ion|ed)|consent\s+(?:order|agreement))',r'(?:temporary|emergency|final|default)\s+(?:order|judgment)']),
"28_MOTIONS":("Motions",[r'motion\s+(?:to|for|in)\s+\w+',r'(?:emergency|ex\s+parte)\s+motion',r'(?:response|reply|brief|memorandum|petition)',r'(?:filed?|submit)\s+(?:a\s+)?(?:motion|petition|complaint)']),
"29_DISCOVERY":("Discovery",[r'(?:discovery|interrogator(?:y|ies)|subpoena|deposition)',r'request\s+(?:for|to)\s+(?:produce|admit|disclose)',r'(?:FOIA|Freedom\s+of\s+Information)']),
"30_EVIDENCE":("Evidence & Exhibits",[r'(?:Exhibit|Ex\.?)\s*[A-Z0-9\-]+',r'(?:screenshot|photo|recording|video|audio|text\s+message)',r'(?:Bates|bates)\s*#?\s*[A-Z]*\d+',r'(?:evidence|proof|documentation)']),
"31_BEST_INT":("Best Interest Factors",[r'best\s+interest(?:s)?(?:\s+of\s+(?:the\s+)?child)?',r'MCL\s+722\.23|factor\s+[a-l]',r'(?:established\s+custodial\s+environment|ECE)',r'(?:moral\s+fitness|emotional\s+ties|reasonable\s+preference)']),
"32_FINANCIAL":("Financial & Damages",[r'\$[\d,]+(?:\.\d{2})?',r'(?:damages?|costs?|fees?|expenses?|compensation)',r'(?:attorney.?s?\s+fees?|filing\s+fee|court\s+costs?)',r'(?:child\s+support|lost\s+(?:wages?|income))']),
"33_TIMELINE":("Timeline & Dates",[r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}',r'\d{1,2}/\d{1,2}/\d{2,4}',r'\d{4}-\d{2}-\d{2}']),
"34_NARRATIVE":("Father Narrative",[r'(?:Andrew|father|dad|Pigors)\s+(?:\w+\s+){0,3}(?:son|child|LDW)',r'(?:they\s+(?:took|removed|prevented|denied|refused|blocked))',r'(?:I\s+(?:love|miss|want|need)\s+my\s+(?:son|child))',r'(?:fight(?:ing)?\s+for\s+(?:my\s+)?(?:son|child|rights))']),
"35_WELFARE":("Child Welfare",[r'(?:welfare|well.?being|safety)\s+of\s+(?:the\s+)?child',r'(?:developmental|emotional|psychological)\s+(?:harm|impact|needs?)',r'(?:stable\s+(?:environment|home)|continuity|nurtur)']),
"36_BOND":("Parent-Child Bond",[r'(?:bond(?:ing)?|attachment|relationship)\s+(?:with|between|to)\s+(?:father|parent|child)',r'(?:love|close|strong|deep)\s+(?:bond|relationship|connection)',r'(?:separation|severed?|disrupt(?:ed|ion))\s+(?:bond|relationship|attachment)']),
"37_COMMS":("Communications",[r'(?:text\s+message|email|voicemail|phone\s+call|letter)',r'(?:sent|received|wrote|called|texted|emailed)',r'(?:communication|contact)\s+(?:between|with|from|to)']),
"38_CREDIBILITY":("Credibility",[r'(?:credib(?:ility|le)|reliab(?:ility|le)|trustworth)',r'(?:inconsisten(?:cy|t)|contradict(?:ion|ory))',r'(?:impeach|discredit|unreliable|untruthful)']),
"39_PATTERNS":("Behavioral Patterns",[r'pattern\s+of\s+(?:behavior|conduct|abuse|alienation|interference)',r'(?:repeated(?:ly)?|systematic(?:ally)?|ongoing|persistent)',r'(?:history\s+of|documented\s+(?:pattern|history))']),
"40_IMPACT":("Impact & Harm",[r'(?:harm(?:ed|ful)?|damage(?:d)?|injur(?:y|ed))',r'(?:irreparable\s+(?:harm|damage|injury))',r'(?:emotional\s+(?:distress|damage|suffering))',r'(?:psychological\s+(?:harm|trauma|impact))']),
"41_APPELLATE":("Appellate",[r'(?:appeal(?:s|ed)?|appellate)',r'(?:Court\s+of\s+Appeals?|COA|Supreme\s+Court|MSC)',r'(?:leave\s+to\s+appeal|application\s+for\s+leave)',r'MCR\s+7\.\d{3}']),
"42_EMERGENCY":("Emergency Relief",[r'emergency\s+(?:motion|petition|relief|order|hearing|stay)',r'(?:immediate|urgent|imminent|irreparable)',r'(?:TRO|temporary\s+restraining)',r'(?:expedited|time.?sensitive)']),
"43_REMEDIES":("Remedies & Relief",[r'(?:remed(?:y|ies)|relief|injunct(?:ion|ive)|declaratory)',r'(?:compensatory|punitive|nominal)\s+damages',r'(?:restore|reinstate|modify|terminate|vacate|reverse|remand)']),
"44_REVIEW":("Standards of Review",[r'(?:standard\s+of\s+review|de\s+novo|clearly\s+erroneous)',r'(?:abuse\s+of\s+discretion|plain\s+error|harmless\s+error)',r'(?:preponderance|clear\s+and\s+convincing)',r'(?:Vodvarka|Shade|Troxel|Santosky)']),
"45_PROCEDURAL":("Procedural Defects",[r'procedural(?:ly)?\s+(?:defect|error|deficien|improper)',r'(?:failed?\s+to\s+(?:provide|give|serve|notify|comply))',r'(?:lack\s+of\s+(?:jurisdiction|standing|notice|service))']),
"46_FOC":("Friend of Court",[r'(?:Friend\s+of\s+(?:the\s+)?Court|FOC)',r'(?:referee|recommendation|investigation|evaluation)',r'(?:custody\s+(?:evaluation|investigation|recommendation))']),
"47_POLICE":("Police & Law Enforcement",[r'(?:police|officer|law\s+enforcement|sheriff)',r'(?:police|incident|arrest|criminal)\s+report',r'(?:911|dispatch|arrest(?:ed)?)',r'Officer\s+(?:Ella\s+)?Randall']),
"48_MEDICAL":("Medical & Mental Health",[r'(?:medical|mental\s+health|therap(?:y|ist)|counseli?(?:ng|or)|psycholog)',r'Dr\.?\s+(?:Richard\s+)?Bone',r'(?:substance\s+(?:abuse|use)|drug\s+test)',r'(?:evaluation|assessment|diagnosis)']),
"49_MEEK":("MEEK Strategy",[r'MEEK\s*\d',r'Track\s*(?:1|2|3|4|5)',r'(?:housing|eviction|lease|homeless)',r'(?:circuit\s+court|family\s+court|probate)']),
"50_CASE_NO":("Case Numbers",[r'(?:2024-001507|2023-5907|2021-186155|2025-002760)',r'Case\s+(?:No|Number|#)\.?\s*:?\s*\d{2,4}[\-\.]\d+',r'(?:docket|file\s+(?:number|no))',r'14th\s+(?:Judicial\s+)?Circuit|Muskegon\s+County']),
}

def read_file(p):
    try:
        sz=os.path.getsize(p)
        if sz<30 or sz>50_000_000: return None
        ext=os.path.splitext(p)[1].lower()
        if ext in TEXT_EXT:
            with open(p,'r',encoding='utf-8',errors='replace') as f: return f.read()
        elif ext=='.pdf':
            try:
                import pdfplumber
                parts=[]
                with pdfplumber.open(p) as pdf:
                    for pg in pdf.pages[:200]:
                        t=pg.extract_text()
                        if t: parts.append(t)
                return '\n'.join(parts) if parts else None
            except: return None
        elif ext=='.docx':
            try:
                from docx import Document
                return '\n'.join(pr.text for pr in Document(p).paragraphs)
            except: return None
    except: pass
    return None

def ctx(text,s,e,w=150):
    cs=max(0,s-w)
    ce=min(len(text),e+w)
    return text[cs:ce].replace('\n',' ').replace('\r','').strip()[:300]

def harvest(fpath,text,compiled,jdir,stats):
    ext=os.path.splitext(fpath)[1].lower().lstrip('.') or 'noext'
    rel=os.path.relpath(fpath,SCAN)
    for aid,(name,pats) in compiled.items():
        finds=[]
        seen=set()
        for pat in pats:
            for m in pat.finditer(text):
                k=m.group().strip().lower()[:100]
                if k not in seen and len(k)>1:
                    seen.add(k)
                    finds.append((m.group().strip()[:200],ctx(text,m.start(),m.end())))
        if finds:
            jpath=os.path.join(jdir,aid,"journal_"+ext+".md")
            with open(jpath,'a',encoding='utf-8',errors='replace') as jf:
                jf.write("\n## "+os.path.basename(fpath)+"\n")
                jf.write("**Path:** `"+rel+"`\n")
                jf.write("**Time:** "+datetime.datetime.now().strftime('%H:%M:%S')+" | **Finds:** "+str(len(finds))+"\n\n")
                for matched,context in finds[:60]:
                    jf.write("- **"+matched+"**\n")
                    jf.write("  > "+context+"\n\n")
                if len(finds)>60:
                    jf.write("*+"+str(len(finds)-60)+" more*\n")
                jf.write("---\n")
            stats[aid]=stats.get(aid,0)+len(finds)

def main():
    print("="*70)
    print("AGENT FLEET HARVESTER v1.0 - 50 JUDICIAL INTELLIGENCE AGENTS")
    print("Target: Pigors v. Watson - C:\\Users\\andre\\Scans")
    print("Journals: C:\\Users\\andre\\Desktop\\AGENT_JOURNALS")
    print("Started:",datetime.datetime.now())
    print("="*70,flush=True)

    compiled={}
    for aid,(name,pats) in AG.items():
        compiled[aid]=(name,[re.compile(p,re.IGNORECASE) for p in pats])
        os.makedirs(os.path.join(JDIR,aid),exist_ok=True)

    os.makedirs(os.path.join(JDIR,"00_FLEET_DASHBOARD"),exist_ok=True)
    with open(os.path.join(JDIR,"00_FLEET_DASHBOARD","AGENT_INDEX.md"),'w',encoding='utf-8') as f:
        f.write("# AGENT FLEET - 50 Judicial Intelligence Agents\n\n")
        f.write("**Target:** "+SCAN+"\n")
        f.write("**Started:** "+str(datetime.datetime.now())+"\n\n")
        f.write("| # | Agent ID | Specialization | Patterns |\n")
        f.write("|---|----------|---------------|----------|\n")
        for aid,(name,pats) in AG.items():
            f.write("| "+aid[:2]+" | "+aid+" | "+name+" | "+str(len(pats))+" |\n")

    done=set()
    old_stats={}
    if os.path.exists(PROG):
        try:
            with open(PROG,'r') as f:
                p=json.load(f)
                done=set(p.get('done',[]))
                old_stats=p.get('stats',{})
            print("Resuming:",len(done),"files already done",flush=True)
        except: pass

    print("Scanning directory tree...",flush=True)
    files=[]
    for root,dirs,fnames in os.walk(SCAN):
        bn=os.path.basename(root)
        if bn in SKIP:
            dirs.clear()
            continue
        dirs[:]=[d for d in dirs if d not in SKIP]
        for fn in fnames:
            ext=os.path.splitext(fn)[1].lower()
            if ext in TEXT_EXT or ext in DOC_EXT:
                fp=os.path.join(root,fn)
                if fp not in done:
                    files.append(fp)

    # Sort: prioritize high-value extensions
    priority={'.md':0,'.txt':1,'.jsonl':2,'.pdf':3,'.docx':4,'.csv':5,'.json':6,'.html':7}
    files.sort(key=lambda f: priority.get(os.path.splitext(f)[1].lower(),9))

    print("Files to process:",len(files),"| Already done:",len(done),flush=True)
    print("="*70,flush=True)

    stats=dict(old_stats)
    processed=0
    errors=0
    t0=time.time()

    for i,fp in enumerate(files):
        try:
            text=read_file(fp)
            if text and len(text)>30:
                harvest(fp,text,compiled,JDIR,stats)
                processed+=1
            done.add(fp)

            if (i+1)%100==0:
                el=time.time()-t0
                rate=(i+1)/el if el>0 else 0
                eta=(len(files)-i-1)/rate/60 if rate>0 else 0
                tf=sum(stats.values())
                print("["+str(i+1)+"/"+str(len(files))+"] "+str(processed)+" harvested | "+str(tf)+" finds | "+"{:.1f}".format(rate)+" f/s | ETA "+"{:.0f}".format(eta)+"m",flush=True)

            if (i+1)%500==0:
                with open(PROG,'w') as f:
                    json.dump({'done':list(done),'stats':stats,'n':processed},f)
                dash=os.path.join(JDIR,"00_FLEET_DASHBOARD","LIVE_STATS.md")
                with open(dash,'w',encoding='utf-8') as f:
                    f.write("# Fleet Live Stats - "+str(datetime.datetime.now())+"\n\n")
                    f.write("**Processed:** "+str(processed)+" | **Errors:** "+str(errors)+" | **Total Finds:** "+str(sum(stats.values()))+"\n\n")
                    f.write("| Agent | Findings |\n|-------|----------|\n")
                    for aid in sorted(stats,key=stats.get,reverse=True):
                        f.write("| "+aid+" | "+str(stats[aid])+" |\n")
        except Exception as e:
            errors+=1
            if errors<30:
                print("  ERR ["+os.path.basename(fp)+"]: "+str(e)[:100],flush=True)

    with open(PROG,'w') as f:
        json.dump({'done':list(done),'stats':stats,'n':processed,'complete':True},f)

    el=time.time()-t0
    tf=sum(stats.values())
    print("\n"+"="*70)
    print("HARVEST COMPLETE - "+str(processed)+" files | "+str(tf)+" findings | "+"{:.1f}".format(el/60)+" min")
    print("="*70)
    for aid in sorted(stats,key=stats.get,reverse=True):
        print("  "+aid+": "+str(stats[aid]))

    rpt=os.path.join(JDIR,"00_FLEET_DASHBOARD","FINAL_REPORT.md")
    with open(rpt,'w',encoding='utf-8') as f:
        f.write("# AGENT FLEET FINAL REPORT\n\n")
        f.write("**Completed:** "+str(datetime.datetime.now())+"\n")
        f.write("**Duration:** "+"{:.1f}".format(el/60)+" minutes\n")
        f.write("**Files:** "+str(processed)+" | **Findings:** "+str(tf)+" | **Errors:** "+str(errors)+"\n\n")
        f.write("## Results by Agent\n\n")
        f.write("| Rank | Agent | Findings |\n|------|-------|----------|\n")
        for rank,(aid,cnt) in enumerate(sorted(stats.items(),key=lambda x:x[1],reverse=True),1):
            f.write("| "+str(rank)+" | "+aid+" | "+str(cnt)+" |\n")
    print("\nJournals saved to:",JDIR,flush=True)

if __name__=='__main__':
    main()