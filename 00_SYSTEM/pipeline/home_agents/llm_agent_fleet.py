# LLM Agent Fleet v3.1 - FIXED MAPPINGS
import sys, os, json, time, shutil
sys.path.insert(0, 'D:/TEMP/pylibs')
import ollama

JOURNALS = r"C:\Users\andre\Desktop\AGENT_JOURNALS"
OUTPUT = r"C:\Users\andre\Desktop\AGENT_JOURNALS\00_FLEET_DASHBOARD"
PROGRESS_FILE = r"D:\TEMP\llm_agent_progress.json"

def llm_ask(prompt, max_tokens=800):
    try:
        r = ollama.chat(model="mistral", messages=[
            {"role": "system", "content": "You are a Michigan litigation expert. Case: Pigors v Watson, 14th Circuit Muskegon County. Father Andrew Pigors (Pro Se) vs Mother Emily Watson. Child L.D.W. (DOB 11/9/2022). Key issues: parental alienation, judicial misconduct (Judge McNeill), 329+ days separation without hearing, Watson family (Emily, Albert, Lori, Cody). Produce court-ready analysis. Cite MCR/MCL."},
            {"role": "user", "content": prompt}
        ], options={"num_predict": max_tokens, "temperature": 0.2})
        return r.message.content.strip()
    except Exception as e:
        return f"[LLM_ERROR: {e}]"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"completed_agents": [], "total_llm_calls": 0}

def save_progress(prog):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(prog, f)

def get_top_findings(agent_dir, max_chars=5000):
    text = ""
    for fname in ["SIGNAL_SCORES.md", "VERBATIM_QUOTES.md"]:
        fpath = os.path.join(agent_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            if len(content) > 100:
                lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]
                text += '\n'.join(lines[:80]) + '\n'
                if len(text) >= max_chars:
                    return text[:max_chars]
    if len(text) < 500:
        jpath = os.path.join(agent_dir, "journal_md.md")
        if os.path.exists(jpath):
            with open(jpath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]
            text += '\n'.join(lines[:60])
    return text[:max_chars]

# CORRECT folder name -> (prompt, output_file) mapping
AGENTS = {
    "18_ALIENATION": ("PARENTAL ALIENATION DOSSIER (FOCAL POINT): Emily Watson's specific alienating behaviors, Watson family involvement (Albert, Lori, Cody), impact on child L.D.W., MCL 722.23 factors, 329+ days separation, recommended relief. Be exhaustive.", "LLM_ALIENATION_DOSSIER.md"),
    "19_CUSTODY": ("Custody analysis: current arrangement, improper modifications without hearing, MCL 722.23(a-l) best interest factors with evidence, emergency custody motion basis.", "LLM_CUSTODY_ANALYSIS.md"),
    "21_DUE_PROCESS": ("Due process violations: 14th Amendment, Michigan Constitution Art 1 Sec 17, denial of evidentiary hearing, 329+ days separation, 42 USC 1983 federal claims, procedural failures.", "LLM_DUE_PROCESS_BRIEF.md"),
    "22_MISCONDUCT": ("Judicial misconduct dossier: Judge McNeill's specific bias, procedural violations, MCR 2.003 disqualification grounds, Judicial Tenure Commission complaint, appellate reversal.", "LLM_MISCONDUCT_DOSSIER.md"),
    "10_EMILY": ("Emily Watson litigation profile: alienating behaviors with dates, false statements to court, PPO abuse, parenting time interference, gatekeeping pattern, credibility issues.", "LLM_EMILY_PROFILE.md"),
    "09_ANDREW": ("Andrew Pigors narrative: timeline of events, efforts to maintain relationship with child, legal actions taken, obstacles, fitness evidence, harm suffered, damages.", "LLM_ANDREW_NARRATIVE.md"),
    "32_FINANCIAL": ("Damages calculation: $94K+ economic damages itemized, lost income, legal costs, child support, property, civil damages claim against Watson family.", "LLM_DAMAGES_BRIEF.md"),
    "41_APPELLATE": ("Appellate strategy: COA and Supreme Court arguments, standards of review, preserved errors, constitutional claims, recommended appellate filings.", "LLM_APPELLATE_STRATEGY.md"),
    "42_EMERGENCY": ("Emergency relief analysis: grounds for emergency motion, immediate danger to child, 329+ days separation, ex parte motion basis, MCR 3.207.", "LLM_EMERGENCY_BRIEF.md"),
    "39_PATTERNS": ("Pattern analysis: recurring behaviors by Emily Watson and family, judicial patterns by McNeill, systematic due process violations, evidence of coordinated conduct.", "LLM_PATTERNS_ANALYSIS.md"),
}

def run():
    prog = load_progress()
    print(f"=== LLM AGENT FLEET v3.1 ===")
    print(f"Model: mistral | {len(AGENTS)} priority agents")
    print(f"Prior: {len(prog['completed_agents'])} done, {prog['total_llm_calls']} calls")
    
    results = {}
    for agent_id, (prompt_base, outfile) in AGENTS.items():
        if agent_id in prog['completed_agents']:
            print(f"  [{agent_id}] SKIP (done)")
            opath = os.path.join(JOURNALS, agent_id, outfile)
            if os.path.exists(opath):
                with open(opath, 'r', encoding='utf-8', errors='replace') as f:
                    results[agent_id] = f.read()
            continue
        
        agent_dir = os.path.join(JOURNALS, agent_id)
        if not os.path.isdir(agent_dir):
            print(f"  [{agent_id}] SKIP (no dir)")
            continue
        
        findings = get_top_findings(agent_dir)
        if len(findings) < 50:
            print(f"  [{agent_id}] SKIP (no data)")
            continue
        
        prompt = f"{prompt_base}\n\nEVIDENCE DATA:\n{findings}"
        print(f"  [{agent_id}] LLM analyzing {len(findings)} chars...", end=" ", flush=True)
        
        t0 = time.time()
        analysis = llm_ask(prompt)
        elapsed = time.time() - t0
        prog['total_llm_calls'] += 1
        
        header = f"# LLM Analysis: {agent_id}\n"
        header += f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"Model: mistral | Input: {len(findings)} chars | Time: {elapsed:.0f}s\n"
        header += f"Case: Pigors v. Watson | 14th Circuit Muskegon MI\n\n---\n\n"
        
        full = header + analysis
        with open(os.path.join(agent_dir, outfile), 'w', encoding='utf-8') as f:
            f.write(full)
        
        # Copy critical analyses to dashboard
        if agent_id in ["18_ALIENATION", "21_DUE_PROCESS", "22_MISCONDUCT"]:
            with open(os.path.join(OUTPUT, outfile), 'w', encoding='utf-8') as f:
                f.write(full)
        
        results[agent_id] = full
        prog['completed_agents'].append(agent_id)
        save_progress(prog)
        print(f"DONE ({elapsed:.0f}s, {len(analysis)} chars)")
    
    # Also load the 3 already-done agents for synthesis
    for aid in ["01_MCL", "02_MCR", "03_CASELAW"]:
        adir = os.path.join(JOURNALS, aid)
        for f in os.listdir(adir):
            if f.startswith("LLM_"):
                with open(os.path.join(adir, f), 'r', encoding='utf-8', errors='replace') as fh:
                    results[aid] = fh.read()
    
    # MASTER SYNTHESIS
    if "MASTER" not in prog['completed_agents'] and len(results) >= 5:
        print(f"\n=== MASTER STRATEGY SYNTHESIS ({len(results)} agents) ===")
        brief = []
        for aid, content in results.items():
            body = '\n'.join(l for l in content.split('\n') if l.strip() and not l.startswith('#') and not l.startswith('Generated') and not l.startswith('Model'))[:1200]
            brief.append(f"[{aid}]: {body}")
        
        master_prompt = """MASTER LITIGATION STRATEGY for Andrew J. Pigors. From all agent analyses:
1. TOP 5 STRONGEST LEGAL ARGUMENTS (MCR/MCL/caselaw)
2. EMERGENCY FILINGS (within 7 days)
3. ALIENATION PROSECUTION (all Watsons)
4. JUDICIAL MISCONDUCT COMPLAINT (Judge McNeill)
5. APPELLATE STRATEGY (COA + Supreme Court)
6. CIVIL DAMAGES ($94K+ against Watsons)
7. COMPLETE FILING SEQUENCE (court, case#, document)

""" + '\n\n'.join(brief[:10])
        
        print(f"  Synthesizing...", end=" ", flush=True)
        t0 = time.time()
        master = llm_ask(master_prompt[:12000], max_tokens=2500)
        elapsed = time.time() - t0
        prog['total_llm_calls'] += 1
        
        mfull = f"# MASTER LITIGATION STRATEGY BRIEF\n"
        mfull += f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        mfull += f"Model: Mistral LLM | Agents: {len(results)}\n"
        mfull += f"Case: Pigors v. Watson | 14th Judicial Circuit, Muskegon County MI\n"
        mfull += f"Party: Andrew J. Pigors (Pro Se Father)\n\n---\n\n"
        mfull += master
        
        with open(os.path.join(OUTPUT, "MASTER_LLM_STRATEGY.md"), 'w', encoding='utf-8') as f:
            f.write(mfull)
        shutil.copy2(os.path.join(OUTPUT, "MASTER_LLM_STRATEGY.md"), r"C:\Users\andre\Desktop\MASTER_LLM_STRATEGY.md")
        
        prog['completed_agents'].append("MASTER")
        save_progress(prog)
        print(f"DONE ({elapsed:.0f}s)")
        print(f"  -> Desktop\\MASTER_LLM_STRATEGY.md")
    
    print(f"\n=== COMPLETE: {prog['total_llm_calls']} LLM calls, {len(prog['completed_agents'])} agents ===")

if __name__ == "__main__":
    run()