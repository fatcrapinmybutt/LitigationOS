import sys, time, json, os, sqlite3
sys.stdout.reconfigure(encoding='utf-8')

# Add model path
sys.path.insert(0, r'C:\Users\andre\LitigationOS\00_SYSTEM\local_model')
from inference_engine import LocalLegalRAG

print("=" * 70)
print("  MBP LitigationOS — RAG LITIGATION ANALYSIS ENGINE")
print("  Qwen2.5-1.5B + TF-IDF Retrieval | All Lanes")
print("=" * 70)

rag = LocalLegalRAG()
print(f"\nModel: {rag.model_name} | LLM OK: {rag.llm_ok}")

# Key legal queries covering all active lanes
queries = [
    # Lane A — Emergency Motion (READY, score 85)
    ("LANE_A_EMERGENCY", "Under MCR 2.119 and MCL 722.27a, what is the legal standard for an emergency motion to restore parenting time after 700+ days of parent-child separation?"),

    # Lane A — Best Interest Factors
    ("LANE_A_FACTORS", "Analyze the 12 best interest factors under MCL 722.23(a)-(l) focusing on Factor J parental alienation and Factor L domestic violence in Pigors v Watson."),

    # Lane D — PPO Termination
    ("LANE_D_PPO", "What is the legal standard for terminating a PPO under MCL 600.2950 and what evidence must the movant present?"),

    # Lane E — Judicial Disqualification
    ("LANE_E_DISQUALIFY", "Under MCR 2.003(C)(1), what specific grounds support disqualification of a judge who has demonstrated bias in custody proceedings?"),

    # Lane F — COA Brief Issues
    ("LANE_F_COA", "Under MCR 7.212, what are the requirements for an appellant brief in the Michigan Court of Appeals, and what standard of review applies to custody determinations?"),

    # Lane F — MSC Superintending Control
    ("LANE_F_MSC", "Under MCR 7.305 and MCL 600.217, what is required for an application for leave to appeal or original action for superintending control to the Michigan Supreme Court?"),

    # Cross-Lane — Due Process
    ("CROSS_DUE_PROCESS", "How does the 14th Amendment Due Process Clause protect fundamental parental rights in Michigan custody cases, citing Troxel v Granville and Michigan case law?"),

    # Cross-Lane — Contempt
    ("CROSS_CONTEMPT", "Under MCL 600.1701 and MCR 3.606, what are the elements of civil contempt for violation of parenting time orders?"),
]

results = {}
total_start = time.time()

for tag, q in queries:
    print(f"\n{'─' * 70}")
    print(f"[{tag}]")
    print(f"Q: {q[:80]}...")
    t0 = time.time()
    try:
        result = rag.query(q)
        elapsed = time.time() - t0
        print(f"⏱ {elapsed:.1f}s | {result.get('retrieval_count',0)} retrieved | {result.get('authority_count',0)} authority")
        print(f"\n{result['response']}")
        results[tag] = {
            "query": q,
            "response": result["response"],
            "model": result["model"],
            "elapsed_s": round(elapsed, 1),
            "retrieval_count": result.get("retrieval_count", 0),
            "authority_count": result.get("authority_count", 0),
        }
    except Exception as e:
        print(f"ERROR: {e}")
        results[tag] = {"query": q, "error": str(e)}

total_elapsed = time.time() - total_start
print(f"\n{'=' * 70}")
print(f"  COMPLETE: {len(results)} analyses in {total_elapsed:.0f}s ({total_elapsed/len(queries):.0f}s avg)")
print(f"{'=' * 70}")

# Save to DB
db = sqlite3.connect(r'C:\Users\andre\litigation_context.db')
db.execute("""CREATE TABLE IF NOT EXISTS rag_analysis (
    id TEXT PRIMARY KEY,
    lane TEXT,
    query TEXT,
    response TEXT,
    model TEXT,
    elapsed_s REAL,
    retrieval_count INTEGER,
    authority_count INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
)""")
for tag, data in results.items():
    lane = tag.split('_')[0] + '_' + tag.split('_')[1] if '_' in tag else tag
    try:
        db.execute("INSERT OR REPLACE INTO rag_analysis (id, lane, query, response, model, elapsed_s, retrieval_count, authority_count) VALUES (?,?,?,?,?,?,?,?)",
            (tag, lane, data.get("query",""), data.get("response",""), data.get("model",""), data.get("elapsed_s",0), data.get("retrieval_count",0), data.get("authority_count",0)))
    except: pass
db.commit()
print(f"\nSaved {len(results)} analyses to rag_analysis table")

# Also save as markdown report
report_path = r'C:\Users\andre\LitigationOS\05_ANALYSIS\RAG_LEGAL_ANALYSIS_REPORT.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# RAG Legal Analysis Report\n")
    f.write(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"**Model:** {rag.model_name} + MLLM TF-IDF\n")
    f.write(f"**Total Time:** {total_elapsed:.0f}s for {len(queries)} queries\n\n")
    f.write("---\n\n")
    for tag, data in results.items():
        f.write(f"## {tag}\n\n")
        f.write(f"**Query:** {data.get('query','')}\n\n")
        f.write(f"**Analysis:**\n\n{data.get('response','ERROR')}\n\n")
        f.write(f"*[{data.get('model','')} | {data.get('elapsed_s',0)}s | {data.get('retrieval_count',0)} retrieved | {data.get('authority_count',0)} authority]*\n\n")
        f.write("---\n\n")
print(f"Report saved: {report_path}")
