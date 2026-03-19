#!/usr/bin/env python3
# CYCLE 2: ENRICHMENT ENGINE - Cross-agent synthesis, scoring, and deep expansion
# Runs AFTER cycle 1 fleet completes (or concurrently on completed journals)
import os,re,json,datetime,collections

JDIR = r"C:\Users\andre\Desktop\AGENT_JOURNALS"
SCAN = r"C:\Users\andre\Scans"
PROG = r"D:\TEMP\agent_fleet_progress.json"

def count_journal_entries(jpath):
    """Count unique file entries in a journal"""
    count = 0
    try:
        with open(jpath, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                if line.startswith('## '):
                    count += 1
    except:
        pass
    return count

def extract_findings(jpath):
    """Extract all bold findings from a journal file"""
    findings = []
    try:
        with open(jpath, 'r', encoding='utf-8', errors='replace') as f:
            current_file = None
            for line in f:
                if line.startswith('## '):
                    current_file = line[3:].strip()
                elif line.startswith('- **') and line.rstrip().endswith('**'):
                    finding = line.strip()[4:-2]
                    findings.append((current_file, finding))
                elif line.startswith('- **'):
                    finding = line.strip()[4:].split('**')[0]
                    findings.append((current_file, finding))
    except:
        pass
    return findings

def build_file_scores():
    """Score every file by how many agents found hits in it"""
    file_agents = collections.defaultdict(set)
    file_finds = collections.defaultdict(int)

    for agent_dir in os.listdir(JDIR):
        if agent_dir == "00_FLEET_DASHBOARD":
            continue
        agent_path = os.path.join(JDIR, agent_dir)
        if not os.path.isdir(agent_path):
            continue
        for jfile in os.listdir(agent_path):
            if not jfile.startswith("journal_"):
                continue
            jpath = os.path.join(agent_path, jfile)
            findings = extract_findings(jpath)
            for fname, finding in findings:
                if fname:
                    file_agents[fname].add(agent_dir)
                    file_finds[fname] += 1

    scored = []
    for fname, agents in file_agents.items():
        scored.append({
            'file': fname,
            'agent_count': len(agents),
            'total_finds': file_finds[fname],
            'agents': sorted(agents),
            'score': len(agents) * 10 + file_finds[fname]
        })
    scored.sort(key=lambda x: x['score'], reverse=True)
    return scored

def build_cross_agent_synthesis():
    """Find entities/citations that appear across multiple agents"""
    entity_agents = collections.defaultdict(lambda: collections.defaultdict(int))

    for agent_dir in os.listdir(JDIR):
        if agent_dir == "00_FLEET_DASHBOARD":
            continue
        agent_path = os.path.join(JDIR, agent_dir)
        if not os.path.isdir(agent_path):
            continue
        for jfile in os.listdir(agent_path):
            if not jfile.startswith("journal_"):
                continue
            jpath = os.path.join(agent_path, jfile)
            findings = extract_findings(jpath)
            for fname, finding in findings:
                key = finding.lower().strip()[:80]
                if len(key) > 3:
                    entity_agents[key][agent_dir] += 1

    # Items found by 3+ agents = high signal
    cross = []
    for entity, agents in entity_agents.items():
        if len(agents) >= 3:
            cross.append({
                'entity': entity,
                'agent_count': len(agents),
                'total_hits': sum(agents.values()),
                'agents': dict(agents)
            })
    cross.sort(key=lambda x: x['agent_count'] * 100 + x['total_hits'], reverse=True)
    return cross

def build_narrative_timeline():
    """Extract all dates from timeline agent and build chronological narrative"""
    timeline = []
    tpath = None
    for jfile in os.listdir(os.path.join(JDIR, "33_TIMELINE")):
        if jfile.startswith("journal_"):
            tpath = os.path.join(JDIR, "33_TIMELINE", jfile)
            findings = extract_findings(tpath)
            for fname, finding in findings:
                timeline.append((finding, fname))

    timeline.sort()
    return timeline

def main():
    print("=" * 70)
    print("CYCLE 2: ENRICHMENT ENGINE")
    print("Cross-agent synthesis, file scoring, narrative timeline")
    print("Started:", datetime.datetime.now())
    print("=" * 70, flush=True)

    dash = os.path.join(JDIR, "00_FLEET_DASHBOARD")
    os.makedirs(dash, exist_ok=True)

    # 1. FILE SCORES
    print("\n[1/4] Building file scores...", flush=True)
    scores = build_file_scores()
    with open(os.path.join(dash, "FILE_SCORES.md"), 'w', encoding='utf-8') as f:
        f.write("# File Intelligence Scores\n\n")
        f.write("Files ranked by how many agents found judicial data in them.\n")
        f.write("Higher score = more legally relevant across multiple dimensions.\n\n")
        f.write("| Rank | Score | Agents | Finds | File |\n")
        f.write("|------|-------|--------|-------|------|\n")
        for i, s in enumerate(scores[:200], 1):
            f.write("| "+str(i)+" | "+str(s['score'])+" | "+str(s['agent_count'])+" | "+str(s['total_finds'])+" | "+s['file']+" |\n")
        f.write("\n## Agent Coverage per Top File\n\n")
        for s in scores[:50]:
            f.write("### "+s['file']+" (Score: "+str(s['score'])+")\n")
            f.write("Agents: "+", ".join(s['agents'])+"\n\n")
    print("  File scores: "+str(len(scores))+" files ranked", flush=True)

    # 2. CROSS-AGENT SYNTHESIS
    print("\n[2/4] Cross-agent synthesis...", flush=True)
    cross = build_cross_agent_synthesis()
    with open(os.path.join(dash, "CROSS_AGENT_SYNTHESIS.md"), 'w', encoding='utf-8') as f:
        f.write("# Cross-Agent Synthesis Report\n\n")
        f.write("Entities/citations found by 3+ agents = HIGH SIGNAL intelligence.\n\n")
        f.write("| Entity | Agents | Total Hits |\n")
        f.write("|--------|--------|------------|\n")
        for c in cross[:300]:
            f.write("| "+c['entity'][:60]+" | "+str(c['agent_count'])+" | "+str(c['total_hits'])+" |\n")
        f.write("\n\n## Top 50 Cross-Agent Entities (Detail)\n\n")
        for i, c in enumerate(cross[:50], 1):
            f.write("### "+str(i)+". "+c['entity']+"\n")
            f.write("Found by "+str(c['agent_count'])+" agents, "+str(c['total_hits'])+" total hits\n")
            for agent, cnt in sorted(c['agents'].items()):
                f.write("- "+agent+": "+str(cnt)+" hits\n")
            f.write("\n")
    print("  Cross-agent entities: "+str(len(cross))+" high-signal items", flush=True)

    # 3. NARRATIVE TIMELINE
    print("\n[3/4] Building narrative timeline...", flush=True)
    timeline = build_narrative_timeline()
    with open(os.path.join(dash, "NARRATIVE_TIMELINE.md"), 'w', encoding='utf-8') as f:
        f.write("# Chronological Narrative Timeline\n\n")
        f.write("All dates extracted from case files, in order.\n\n")
        f.write("| Date | Source File |\n")
        f.write("|------|-------------|\n")
        for date, src in timeline[:500]:
            f.write("| "+date+" | "+str(src)+" |\n")
    print("  Timeline entries: "+str(len(timeline)), flush=True)

    # 4. AGENT SUMMARY REPORTS
    print("\n[4/4] Building per-agent summaries...", flush=True)
    for agent_dir in sorted(os.listdir(JDIR)):
        if agent_dir == "00_FLEET_DASHBOARD":
            continue
        agent_path = os.path.join(JDIR, agent_dir)
        if not os.path.isdir(agent_path):
            continue
        all_findings = []
        files_processed = 0
        for jfile in os.listdir(agent_path):
            if not jfile.startswith("journal_"):
                continue
            jpath = os.path.join(agent_path, jfile)
            findings = extract_findings(jpath)
            all_findings.extend(findings)
            files_processed += count_journal_entries(jpath)

        if all_findings:
            # Count unique findings
            finding_counts = collections.Counter(f[1].lower().strip()[:80] for f in all_findings if f[1])
            top_findings = finding_counts.most_common(100)

            summary_path = os.path.join(agent_path, "SUMMARY.md")
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("# "+agent_dir+" - Summary Report\n\n")
                f.write("**Files Processed:** "+str(files_processed)+"\n")
                f.write("**Total Findings:** "+str(len(all_findings))+"\n")
                f.write("**Unique Findings:** "+str(len(finding_counts))+"\n\n")
                f.write("## Top Findings (by frequency)\n\n")
                f.write("| Rank | Finding | Count |\n")
                f.write("|------|---------|-------|\n")
                for rank, (finding, count) in enumerate(top_findings, 1):
                    f.write("| "+str(rank)+" | "+finding[:60]+" | "+str(count)+" |\n")

    # MASTER ENRICHMENT REPORT
    total_agents = len([d for d in os.listdir(JDIR) if d != "00_FLEET_DASHBOARD" and os.path.isdir(os.path.join(JDIR, d))])
    total_journals = 0
    for dd in os.listdir(JDIR):
        dp = os.path.join(JDIR, dd)
        if os.path.isdir(dp):
            for ff in os.listdir(dp):
                if ff.startswith("journal_"):
                    total_journals += 1

    with open(os.path.join(dash, "ENRICHMENT_REPORT.md"), 'w', encoding='utf-8') as f:
        f.write("# CYCLE 2 ENRICHMENT COMPLETE\n\n")
        f.write("**Completed:** "+str(datetime.datetime.now())+"\n")
        f.write("**Files Scored:** "+str(len(scores))+"\n")
        f.write("**Cross-Agent Entities:** "+str(len(cross))+"\n")
        f.write("**Timeline Entries:** "+str(len(timeline))+"\n\n")
        f.write("## Deliverables\n\n")
        f.write("1. **FILE_SCORES.md** - Every file ranked by judicial relevance\n")
        f.write("2. **CROSS_AGENT_SYNTHESIS.md** - High-signal entities found by 3+ agents\n")
        f.write("3. **NARRATIVE_TIMELINE.md** - Chronological case narrative\n")
        f.write("4. **Per-agent SUMMARY.md** - Top findings per agent\n")

    print("\n" + "=" * 70)
    print("ENRICHMENT COMPLETE")
    print("Files scored:", len(scores))
    print("Cross-agent entities:", len(cross))
    print("Timeline entries:", len(timeline))
    print("=" * 70, flush=True)

if __name__ == '__main__':
    main()