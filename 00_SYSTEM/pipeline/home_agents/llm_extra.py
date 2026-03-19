import sys, os, time
sys.path.insert(0, 'D:/TEMP/pylibs')
import ollama

JOURNALS = r"C:\Users\andre\Desktop\AGENT_JOURNALS"
OUT = r"C:\Users\andre\Desktop\OFFLOAD_20260219\LLM_ANALYSES"

def llm(prompt):
    r = ollama.chat(model="mistral", messages=[
        {"role":"system","content":"Michigan litigation expert. Pigors v Watson, 14th Circuit Muskegon. Pro Se Father Andrew Pigors vs Emily Watson. Child L.D.W. 329+ days separated. Cite MCR/MCL."},
        {"role":"user","content":prompt}
    ], options={"num_predict":800,"temperature":0.2})
    return r.message.content.strip()

def get_data(agent_dir):
    text = ""
    for f in ["SIGNAL_SCORES.md","VERBATIM_QUOTES.md","journal_md.md"]:
        p = os.path.join(agent_dir, f)
        if os.path.exists(p):
            with open(p,"r",encoding="utf-8",errors="replace") as fh:
                c = fh.read()
            if len(c)>100:
                lines = [l for l in c.split("\n") if l.strip() and not l.startswith("#")]
                text += "\n".join(lines[:60]) + "\n"
                if len(text)>5000: break
    return text[:5000]

extra = {
    "20_PPO": ("PPO analysis: How Emily Watson weaponized PPO against Andrew, MCR 3.706, evidence of PPO abuse, grounds to modify/terminate.", "LLM_PPO_ANALYSIS.md"),
    "24_CONTEMPT": ("Contempt analysis: Emily Watson violations of court orders, parenting time interference, MCL 600.1701, sanctions.", "LLM_CONTEMPT_ANALYSIS.md"),
    "46_FOC": ("Friend of Court analysis: FOC involvement, failures, MCL 552.505, complaints.", "LLM_FOC_ANALYSIS.md"),
    "31_BEST_INT": ("Best interest factors MCL 722.23(a-l): Evaluate each factor with evidence for Andrew.", "LLM_BEST_INTEREST.md"),
    "36_BOND": ("Parent-child bond: Andrew-L.D.W. bond evidence, 329+ days disruption, attachment harm, MCL 722.23(j).", "LLM_BOND_ANALYSIS.md"),
}

for aid, (prompt_base, outfile) in extra.items():
    adir = os.path.join(JOURNALS, aid)
    if not os.path.isdir(adir):
        print(f"[{aid}] no dir, skip")
        continue
    data = get_data(adir)
    if len(data) < 50:
        print(f"[{aid}] no data, skip")
        continue
    print(f"[{aid}] analyzing {len(data)} chars...", end=" ", flush=True)
    t0 = time.time()
    result = llm(prompt_base + "\n\nEVIDENCE:\n" + data)
    elapsed = time.time() - t0
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    header = "# LLM Analysis: " + aid + "\nGenerated: " + ts + "\nModel: mistral | Time: " + str(int(elapsed)) + "s\n\n---\n\n"
    with open(os.path.join(adir, outfile), "w", encoding="utf-8") as fh:
        fh.write(header + result)
    with open(os.path.join(OUT, aid + "_" + outfile), "w", encoding="utf-8") as fh:
        fh.write(header + result)
    print("DONE (" + str(int(elapsed)) + "s, " + str(len(result)) + " chars)")

print("=== EXTRA AGENTS COMPLETE ===")