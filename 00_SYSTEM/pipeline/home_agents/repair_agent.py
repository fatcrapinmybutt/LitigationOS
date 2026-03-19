#!/usr/bin/env python3
# REPAIR-MAN AGENT v1.0 - Cyclic Optimizer for the 50-Agent Fleet
# Visits each agent's journals in rotation, analyzing quality, fixing issues,
# adding enrichments, cross-linking, scoring, deduplicating, and upgrading.
import os,re,json,datetime,collections,hashlib,time

JDIR = r"C:\Users\andre\Desktop\AGENT_JOURNALS"
SCAN = r"C:\Users\andre\Scans"
PROG = r"D:\TEMP\repair_agent_progress.json"
LOG = os.path.join(JDIR, "00_FLEET_DASHBOARD", "REPAIR_LOG.md")

# ===== REPAIR CAPABILITIES =====

def repair_dedup(agent_dir):
    """Remove duplicate findings within each journal file"""
    fixed = 0
    agent_path = os.path.join(JDIR, agent_dir)
    for jfile in os.listdir(agent_path):
        if not jfile.startswith("journal_"): continue
        jpath = os.path.join(agent_path, jfile)
        try:
            with open(jpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            # Split into file entries
            entries = re.split(r'\n(?=## )', content)
            seen_hashes = set()
            unique_entries = []
            for entry in entries:
                if not entry.strip(): continue
                # Hash the file name + findings
                lines = entry.strip().split('\n')
                header = lines[0] if lines else ''
                findings = [l for l in lines if l.startswith('- **')]
                key = header + '|' + '|'.join(f[:50] for f in findings)
                h = hashlib.md5(key.encode()).hexdigest()
                if h not in seen_hashes:
                    seen_hashes.add(h)
                    unique_entries.append(entry)
                else:
                    fixed += 1
            if fixed > 0:
                with open(jpath, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(unique_entries))
        except: pass
    return fixed

def repair_add_signal_scores(agent_dir):
    """Add signal strength scores to journal entries based on context quality"""
    scored = 0
    agent_path = os.path.join(JDIR, agent_dir)
    high_signal_words = {
        'andrew': 3, 'pigors': 3, 'watson': 3, 'emily': 3, 'mcneill': 3,
        'alienation': 5, 'gatekeep': 5, 'withhold': 4, 'obstruct': 4,
        'custody': 3, 'parenting time': 4, 'due process': 4, 'ex parte': 4,
        'perjury': 5, 'fraud': 4, 'false': 3, 'violation': 3,
        'mcr': 2, 'mcl': 2, 'canon': 3, 'contempt': 3,
        'lincoln': 4, 'l.d.w': 5, 'minor child': 4,
        'hearing': 2, 'motion': 2, 'order': 2, 'appeal': 3,
        'irreparable': 4, 'emergency': 3, 'constitutional': 3,
        'best interest': 4, 'established custodial': 5,
        'rusco': 3, 'albert': 3, 'lori': 3, 'cody': 3,
        'muskegon': 3, '14th circuit': 4, '2024-001507': 5,
    }
    summary_path = os.path.join(agent_path, "SIGNAL_SCORES.md")
    high_entries = []
    for jfile in os.listdir(agent_path):
        if not jfile.startswith("journal_"): continue
        jpath = os.path.join(agent_path, jfile)
        try:
            with open(jpath, 'r', encoding='utf-8', errors='replace') as f:
                current_file = None
                current_score = 0
                current_context = ""
                for line in f:
                    if line.startswith('## '):
                        if current_file and current_score >= 8:
                            high_entries.append((current_score, current_file, current_context[:200]))
                        current_file = line[3:].strip()
                        current_score = 0
                        current_context = ""
                    elif line.strip().startswith('> '):
                        ctx = line.strip()[2:].lower()
                        current_context = line.strip()[2:]
                        for word, score in high_signal_words.items():
                            if word in ctx:
                                current_score += score
                                scored += 1
                if current_file and current_score >= 8:
                    high_entries.append((current_score, current_file, current_context[:200]))
        except: pass
    high_entries.sort(key=lambda x: x[0], reverse=True)
    if high_entries:
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# "+agent_dir+" - HIGH SIGNAL ENTRIES\n\n")
            f.write("Entries scored 8+ on case-relevance signal strength.\n\n")
            f.write("| Rank | Score | File | Context |\n")
            f.write("|------|-------|------|---------|\n")
            for i,(score,fname,ctx) in enumerate(high_entries[:100],1):
                f.write("| "+str(i)+" | "+str(score)+" | "+fname+" | "+ctx[:80].replace('|','/').replace('\n',' ')+" |\n")
    return scored, len(high_entries)

def repair_cross_link(agent_dir, all_agent_data):
    """Add cross-references to other agents that found data in the same files"""
    links = 0
    agent_path = os.path.join(JDIR, agent_dir)
    my_files = set()
    for jfile in os.listdir(agent_path):
        if not jfile.startswith("journal_"): continue
        jpath = os.path.join(agent_path, jfile)
        try:
            with open(jpath, 'r', encoding='utf-8', errors='replace') as f:
                for line in f:
                    if line.startswith('## '):
                        my_files.add(line[3:].strip())
        except: pass
    crosslinks = collections.defaultdict(int)
    for other_agent, other_files in all_agent_data.items():
        if other_agent == agent_dir: continue
        overlap = my_files & other_files
        if overlap:
            crosslinks[other_agent] = len(overlap)
            links += len(overlap)
    if crosslinks:
        xlink_path = os.path.join(agent_path, "CROSSLINKS.md")
        with open(xlink_path, 'w', encoding='utf-8') as f:
            f.write("# "+agent_dir+" - Cross-Agent Links\n\n")
            f.write("Files also analyzed by other agents:\n\n")
            f.write("| Agent | Shared Files |\n|-------|-------------|\n")
            for agent,cnt in sorted(crosslinks.items(), key=lambda x:x[1], reverse=True):
                f.write("| "+agent+" | "+str(cnt)+" |\n")
    return links

def repair_build_quotes(agent_dir):
    """Extract the best verbatim quotes for court filing use"""
    quotes = []
    agent_path = os.path.join(JDIR, agent_dir)
    quote_patterns = [
        re.compile(r'(?:stated|said|wrote|testified|declared|alleged|claimed|admitted|confirmed|reported)[:,]?\s*["\']([^"\']{20,300})["\']', re.IGNORECASE),
        re.compile(r'"([^"]{20,300})"', re.IGNORECASE),
        re.compile(r'["\u201c]([^"\u201d]{20,300})["\u201d]', re.IGNORECASE),
    ]
    for jfile in os.listdir(agent_path):
        if not jfile.startswith("journal_"): continue
        jpath = os.path.join(agent_path, jfile)
        try:
            with open(jpath, 'r', encoding='utf-8', errors='replace') as f:
                current_file = None
                for line in f:
                    if line.startswith('## '):
                        current_file = line[3:].strip()
                    elif line.strip().startswith('> '):
                        ctx = line.strip()[2:]
                        for pat in quote_patterns:
                            for m in pat.finditer(ctx):
                                quote = m.group(1).strip()
                                if len(quote) > 20 and not quote.startswith('http'):
                                    quotes.append((current_file, quote))
        except: pass
    if quotes:
        quote_path = os.path.join(agent_path, "VERBATIM_QUOTES.md")
        seen = set()
        with open(quote_path, 'w', encoding='utf-8') as f:
            f.write("# "+agent_dir+" - Verbatim Quotes for Court Filings\n\n")
            f.write("Exact quotes extracted from evidence, ready for citation.\n\n")
            count = 0
            for fname, quote in quotes:
                qkey = quote.lower()[:60]
                if qkey not in seen:
                    seen.add(qkey)
                    count += 1
                    f.write(str(count)+". **Source:** `"+str(fname)+"`\n")
                    f.write('   > "'+quote+'"\n\n')
                    if count >= 200: break
        return len(seen)
    return 0

def repair_build_evidence_chains(agent_dir):
    """Build violation->evidence->authority chains from journal data"""
    chains = []
    agent_path = os.path.join(JDIR, agent_dir)
    # Look for MCR/MCL citations in context
    cite_pat = re.compile(r'(?:MCR|MCL)\s*[\d\.]+(?:\([A-Za-z0-9]+\))*', re.IGNORECASE)
    for jfile in os.listdir(agent_path):
        if not jfile.startswith("journal_"): continue
        jpath = os.path.join(agent_path, jfile)
        try:
            with open(jpath, 'r', encoding='utf-8', errors='replace') as f:
                current_file = None
                current_finding = None
                for line in f:
                    if line.startswith('## '):
                        current_file = line[3:].strip()
                    elif line.startswith('- **'):
                        current_finding = line.strip()[4:].split('**')[0]
                    elif line.strip().startswith('> ') and current_finding:
                        ctx = line.strip()[2:]
                        cites = cite_pat.findall(ctx)
                        if cites:
                            chains.append({
                                'file': current_file,
                                'finding': current_finding,
                                'authorities': list(set(c.upper() for c in cites)),
                                'context': ctx[:150]
                            })
        except: pass
    if chains:
        chain_path = os.path.join(agent_path, "EVIDENCE_CHAINS.md")
        with open(chain_path, 'w', encoding='utf-8') as f:
            f.write("# "+agent_dir+" - Evidence-to-Authority Chains\n\n")
            f.write("Findings linked to specific legal authorities.\n\n")
            auth_freq = collections.Counter()
            for c in chains:
                for a in c['authorities']:
                    auth_freq[a] += 1
            f.write("## Authorities Referenced\n\n")
            f.write("| Authority | Times Linked |\n|-----------|-------------|\n")
            for auth,cnt in auth_freq.most_common(50):
                f.write("| "+auth+" | "+str(cnt)+" |\n")
            f.write("\n## Chain Details (top 100)\n\n")
            for i,c in enumerate(chains[:100],1):
                f.write(str(i)+". **"+c['finding']+"** -> "+", ".join(c['authorities'])+"\n")
                f.write("   Source: `"+str(c['file'])+"` | "+c['context'][:100]+"\n\n")
    return len(chains)

def main():
    print("="*70)
    print("REPAIR-MAN AGENT v1.0 - Fleet Optimizer")
    print("Cyclic patrol: dedup, score, cross-link, quote-extract, chain-build")
    print("Started:", datetime.datetime.now())
    print("="*70, flush=True)

    # Load repair progress
    repair_prog = {}
    if os.path.exists(PROG):
        try:
            with open(PROG, 'r') as f:
                repair_prog = json.load(f)
        except: pass
    cycle = repair_prog.get('cycle', 0) + 1

    # Collect all agent file sets for cross-linking
    print("\n[SCAN] Building cross-link index...", flush=True)
    all_agent_files = {}
    agents = sorted([d for d in os.listdir(JDIR) if d != "00_FLEET_DASHBOARD" and os.path.isdir(os.path.join(JDIR, d))])
    for agent_dir in agents:
        files = set()
        ap = os.path.join(JDIR, agent_dir)
        for jf in os.listdir(ap):
            if jf.startswith("journal_"):
                try:
                    with open(os.path.join(ap, jf), 'r', encoding='utf-8', errors='replace') as f:
                        for line in f:
                            if line.startswith('## '):
                                files.add(line[3:].strip())
                except: pass
        all_agent_files[agent_dir] = files
    print("  Indexed", len(agents), "agents", flush=True)

    # Open repair log
    log_entries = []
    total_fixes = {'dedup':0, 'scored':0, 'high_signal':0, 'crosslinks':0, 'quotes':0, 'chains':0}

    # Cycle through each agent
    for i, agent_dir in enumerate(agents, 1):
        print("\n["+str(i)+"/"+str(len(agents))+"] Repairing: "+agent_dir, flush=True)
        ap = os.path.join(JDIR, agent_dir)
        entry = {"agent": agent_dir, "time": str(datetime.datetime.now()), "actions": []}

        # 1. Deduplication
        deduped = repair_dedup(agent_dir)
        if deduped:
            entry["actions"].append("Removed "+str(deduped)+" duplicates")
            total_fixes['dedup'] += deduped
            print("  [DEDUP] Removed", deduped, "duplicates", flush=True)

        # 2. Signal scoring
        scored, high = repair_add_signal_scores(agent_dir)
        total_fixes['scored'] += scored
        total_fixes['high_signal'] += high
        if high:
            entry["actions"].append(str(high)+" high-signal entries found (score 8+)")
            print("  [SIGNAL]", high, "high-signal entries", flush=True)

        # 3. Cross-linking
        links = repair_cross_link(agent_dir, all_agent_files)
        total_fixes['crosslinks'] += links
        if links:
            entry["actions"].append(str(links)+" cross-agent file links")

        # 4. Quote extraction
        quotes = repair_build_quotes(agent_dir)
        total_fixes['quotes'] += quotes
        if quotes:
            entry["actions"].append(str(quotes)+" verbatim quotes extracted")
            print("  [QUOTES]", quotes, "verbatim quotes", flush=True)

        # 5. Evidence chains
        chains = repair_build_evidence_chains(agent_dir)
        total_fixes['chains'] += chains
        if chains:
            entry["actions"].append(str(chains)+" evidence-authority chains")
            print("  [CHAINS]", chains, "evidence chains", flush=True)

        log_entries.append(entry)

    # Write repair log
    with open(LOG, 'w', encoding='utf-8') as f:
        f.write("# REPAIR-MAN AGENT - Cycle "+str(cycle)+" Report\n\n")
        f.write("**Completed:** "+str(datetime.datetime.now())+"\n")
        f.write("**Agents Serviced:** "+str(len(agents))+"\n\n")
        f.write("## Totals\n\n")
        f.write("| Action | Count |\n|--------|-------|\n")
        f.write("| Duplicates removed | "+str(total_fixes['dedup'])+" |\n")
        f.write("| Signal scores computed | "+str(total_fixes['scored'])+" |\n")
        f.write("| High-signal entries (8+) | "+str(total_fixes['high_signal'])+" |\n")
        f.write("| Cross-agent file links | "+str(total_fixes['crosslinks'])+" |\n")
        f.write("| Verbatim quotes extracted | "+str(total_fixes['quotes'])+" |\n")
        f.write("| Evidence-authority chains | "+str(total_fixes['chains'])+" |\n")
        f.write("\n## Per-Agent Details\n\n")
        for entry in log_entries:
            if entry["actions"]:
                f.write("### "+entry["agent"]+"\n")
                for a in entry["actions"]:
                    f.write("- "+a+"\n")
                f.write("\n")

    # Save progress
    repair_prog['cycle'] = cycle
    repair_prog['last_run'] = str(datetime.datetime.now())
    repair_prog['totals'] = total_fixes
    with open(PROG, 'w') as f:
        json.dump(repair_prog, f)

    print("\n"+"="*70)
    print("REPAIR CYCLE "+str(cycle)+" COMPLETE")
    print("Duplicates removed:", total_fixes['dedup'])
    print("High-signal entries:", total_fixes['high_signal'])
    print("Verbatim quotes:", total_fixes['quotes'])
    print("Evidence chains:", total_fixes['chains'])
    print("Cross-links:", total_fixes['crosslinks'])
    print("="*70, flush=True)

if __name__ == '__main__':
    main()