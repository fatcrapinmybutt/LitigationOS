import sys, sqlite3, json, time
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
start = time.time()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("PRAGMA busy_timeout=60000")
cur.execute("PRAGMA journal_mode=WAL")
cur.execute("PRAGMA cache_size=-32000")

# Step 1: Create tables
cur.executescript("""
CREATE TABLE IF NOT EXISTS agent_memory (
    key TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT,
    confidence REAL DEFAULT 1.0,
    source_session TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_memory_type ON agent_memory(type);
CREATE INDEX IF NOT EXISTS idx_memory_tags ON agent_memory(tags);

CREATE TABLE IF NOT EXISTS agent_session_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    action TEXT NOT NULL,
    detail TEXT,
    todos_completed INTEGER DEFAULT 0,
    todos_total INTEGER DEFAULT 0,
    timestamp TEXT DEFAULT (datetime('now'))
);
""")
conn.commit()
print("[OK] Tables created: agent_memory, agent_session_log")

# Step 2: Pre-populate memories
memories = [
    # --- Schema corrections ---
    ("schema:filing_readiness:total_score", "schema",
     "filing_readiness table uses 'total_score' NOT 'readiness_score'. Confirmed via PRAGMA table_info.",
     json.dumps(["schema", "filing_readiness", "column_name", "correction"]), 1.0),
    ("schema:authority_chains:filing_vehicle", "schema",
     "authority_chains table uses 'filing_vehicle' NOT 'action_name'. Confirmed via PRAGMA table_info.",
     json.dumps(["schema", "authority_chains", "column_name", "correction"]), 1.0),
    ("schema:omega_scores:name", "schema",
     "omega_scores table uses 'name' NOT 'action_name'. Confirmed via PRAGMA table_info.",
     json.dumps(["schema", "omega_scores", "column_name", "correction"]), 1.0),
    ("schema:omega_evidence_patterns:category", "schema",
     "omega_evidence_patterns table uses 'category' NOT 'pattern_type'. Confirmed via PRAGMA table_info.",
     json.dumps(["schema", "omega_evidence_patterns", "column_name", "correction"]), 1.0),

    # --- Filing priorities ---
    ("strategy:filing:emergency_pt_motion", "strategy",
     "Emergency PT Motion: score 88, lane A, deadline URGENT. Highest priority filing. Requires immediate parenting time restoration based on 210+ days separation.",
     json.dumps(["filing", "lane_A", "custody", "urgent", "parenting_time"]), 0.95),
    ("strategy:filing:emergency_stay_coa", "strategy",
     "Emergency Stay COA: score 87, lane F. Appellate emergency stay to halt harmful trial court orders pending appeal.",
     json.dumps(["filing", "lane_F", "appellate", "emergency", "stay"]), 0.95),
    ("strategy:filing:disqualification", "strategy",
     "Disqualification Motion: score 83.8, lane A, deadline 3/15. MCR 2.003 motion to disqualify Judge McNeill based on 377 critical violations and 267 ex parte communications.",
     json.dumps(["filing", "lane_A", "disqualification", "mcr_2003", "mcneill"]), 0.95),
    ("strategy:filing:msc_emergency_app", "strategy",
     "MSC Emergency Application: score 82, lane F. Michigan Supreme Court emergency application for extraordinary relief.",
     json.dumps(["filing", "lane_F", "appellate", "msc", "emergency"]), 0.90),
    ("strategy:filing:jtc_formal_complaint", "strategy",
     "JTC Formal Complaint: score 78.2, lane E. Formal complaint to Judicial Tenure Commission documenting 504 benchbook violations and 377 critical violations by Judge McNeill.",
     json.dumps(["filing", "lane_E", "jtc", "misconduct", "mcneill"]), 0.90),

    # --- Judicial findings ---
    ("discovery:mcneill:critical_violations", "discovery",
     "Judge McNeill: 377 critical violations documented. 267 ex parte communications. 44% ex parte rate. This is the foundation for disqualification and JTC complaint.",
     json.dumps(["judicial", "mcneill", "violations", "ex_parte", "critical"]), 1.0),
    ("discovery:mcneill:benchbook_violations", "discovery",
     "Judge McNeill: 504 benchbook violations documented across custody proceedings. Systematic pattern of non-compliance with Michigan judicial standards.",
     json.dumps(["judicial", "mcneill", "benchbook", "violations", "pattern"]), 1.0),
    ("discovery:mcneill:canon_violations", "discovery",
     "Judge McNeill: Canon 3(A)(4) is most violated canon. Relates to judicial duty to be patient, dignified, and courteous. Pattern shows systematic disregard.",
     json.dumps(["judicial", "mcneill", "canon", "3A4", "most_violated"]), 1.0),
    ("discovery:separation:parent_child", "discovery",
     "Parent-child separation: 210+ days since August 8, 2025. This is the central harm metric driving emergency filing priority. Every day adds to constitutional harm argument.",
     json.dumps(["separation", "parent_child", "constitutional", "harm", "days_count"]), 1.0),
    ("discovery:judicial:total_violations", "discovery",
     "Total judicial violations documented across all proceedings: 1,127. Spans multiple categories including ex parte, benchbook, procedural, and constitutional violations.",
     json.dumps(["judicial", "violations", "total", "all_categories"]), 1.0),

    # --- Evidence arsenal ---
    ("discovery:evidence:quotes", "discovery",
     "Evidence arsenal: 308,636 evidence quotes extracted and indexed. These are direct quotations from documents, testimony, and communications usable in filings.",
     json.dumps(["evidence", "quotes", "arsenal", "count"]), 1.0),
    ("discovery:evidence:harms", "discovery",
     "Evidence arsenal: 26,283 extracted harms documented. Categorized by adversary, type, and severity. Top adversary: Shady Oaks with 4,127 harms.",
     json.dumps(["evidence", "harms", "arsenal", "shady_oaks"]), 1.0),
    ("discovery:evidence:impeachment", "discovery",
     "Evidence arsenal: 15,171 impeachment items indexed. Available for cross-examination prep and credibility challenges in custody and housing proceedings.",
     json.dumps(["evidence", "impeachment", "arsenal", "cross_exam"]), 1.0),
    ("discovery:evidence:contradictions", "discovery",
     "Evidence arsenal: 10,558 contradictions documented between witness statements, filings, and testimony. Key resource for impeachment and credibility attacks.",
     json.dumps(["evidence", "contradictions", "arsenal", "credibility"]), 1.0),
    ("discovery:evidence:claims", "discovery",
     "Evidence arsenal: 653 claims tracked across all lanes. Each claim linked to supporting evidence, status, and filing vehicle.",
     json.dumps(["evidence", "claims", "arsenal", "tracking"]), 0.95),
    ("discovery:evidence:citations", "discovery",
     "Evidence arsenal: 3,600,000+ citations indexed. Massive citation graph supporting legal arguments across all six case lanes.",
     json.dumps(["evidence", "citations", "arsenal", "citation_graph"]), 1.0),
    ("discovery:evidence:shady_oaks", "discovery",
     "Top adversary by harm count: Shady Oaks with 4,127 documented harms. Primary target for lane B housing litigation (2025-002760-CZ).",
     json.dumps(["evidence", "shady_oaks", "adversary", "lane_B", "housing"]), 1.0),

    # --- System patterns ---
    ("pattern:eagain:max_agents", "pattern",
     "EAGAIN prevention: maximum 3 concurrent background agents. Before spawning ANY sub-agent, count running agents. If 3 running, WAIT. Violation causes SQLITE_BUSY and system crash.",
     json.dumps(["eagain", "concurrency", "agents", "limit", "critical"]), 1.0),
    ("pattern:python:safety", "pattern",
     "Python execution safety: NEVER run inline Python via PowerShell python -c. ALWAYS write to temp .py file, execute, then clean up. Every script MUST set UTF-8 stdout: sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')",
     json.dumps(["python", "safety", "temp_file", "utf8", "critical"]), 1.0),
    ("pattern:db:pragma", "pattern",
     "DB access pattern: ALWAYS set PRAGMA busy_timeout=60000; PRAGMA journal_mode=WAL; PRAGMA cache_size=-32000 on every connection. Use managed_db() from db_lock_manager.py for all access.",
     json.dumps(["database", "pragma", "wal", "busy_timeout", "critical"]), 1.0),
    ("pattern:no_hard_delete", "pattern",
     "No hard deletions EVER on litigation files. Move to I:\\ drive or Recycle Bin. Never rm, never del, never os.remove(). Andrew's explicit instruction.",
     json.dumps(["deletion", "safety", "recycle", "i_drive", "critical"]), 1.0),
    ("pattern:content_dedup", "pattern",
     "Content-based dedup: do NOT rely solely on file hashing. Open and compare actual document content (peek inside). Andrew explicitly said 'no hashing - peek at the document to ensure they are the same.' All duplicates go to I:\\ drive.",
     json.dumps(["dedup", "content_based", "peek", "no_hash_only", "critical"]), 1.0),
    ("pattern:lane_isolation", "pattern",
     "Lane isolation A-F: NEVER cross-contaminate. A=custody, B=housing, C=convergence, D=PPO, E=misconduct, F=appellate. MEEK signals detect lane. Priority: E>D>F>C>A>B. LaneCrossContaminationError is non-fatal skip.",
     json.dumps(["lanes", "isolation", "meek", "cross_contamination", "critical"]), 1.0),
    ("pattern:goaway_timeout", "pattern",
     "GOAWAY/503 timeout: agents die after 27-40 minutes. MUST checkpoint progress every 10 min or every 3 agent completions. Write to SQL todos + filesystem. If no checkpoint, all work is LOST.",
     json.dumps(["goaway", "timeout", "checkpoint", "503", "critical"]), 1.0),

    # --- Drive layout ---
    ("pattern:drive:C", "pattern",
     "C: drive - Primary workspace (C:\\Users\\andre\\LitigationOS). 5.94GB free. Contains all code, pipeline, agents, DB. Monitor space carefully.",
     json.dumps(["drive", "C", "workspace", "primary"]), 0.90),
    ("pattern:drive:D", "pattern",
     "D: drive - Golden set + extracted documents. 15.64GB free. Contains curated evidence sets and extracted content.",
     json.dumps(["drive", "D", "golden_set", "extracted"]), 0.90),
    ("pattern:drive:F", "pattern",
     "F: drive - Raw evidence archive. 20.08GB free. Original unprocessed evidence files. READ-ONLY for pipeline safety.",
     json.dumps(["drive", "F", "raw_evidence", "archive"]), 0.90),
    ("pattern:drive:G", "pattern",
     "G: drive - Organized backups. 20.8GB free. Structured backup copies of critical files.",
     json.dumps(["drive", "G", "backups", "organized"]), 0.90),
    ("pattern:drive:H", "pattern",
     "H: drive - Working overflow. 10.7GB free. Overflow workspace for large processing jobs.",
     json.dumps(["drive", "H", "overflow", "working"]), 0.90),
    ("pattern:drive:I", "pattern",
     "I: drive - Deep archive + dedup target. 2.92GB free CRITICAL. Duplicates moved here. Monitor space - nearly full.",
     json.dumps(["drive", "I", "archive", "dedup", "low_space", "critical"]), 0.95),

    # --- Infrastructure decisions ---
    ("decision:infra:db_indexes", "decision",
     "Created 5 new DB indexes on extracted_harms, deadlines, filing_readiness tables. Improves query performance for filing assembly and evidence lookup operations.",
     json.dumps(["infrastructure", "indexes", "performance", "database"]), 1.0),
    ("decision:infra:analytical_views", "decision",
     "Created 3 analytical views: v_case_health (per-lane health scores), v_adversary_threats (adversary harm rankings), v_filing_pipeline (filing readiness with evidence gaps).",
     json.dumps(["infrastructure", "views", "analytics", "case_health"]), 1.0),
    ("decision:infra:dedup_tables", "decision",
     "Created content_dedup_registry + drive_organization_log tables. content_dedup_registry tracks content-based dedup decisions. drive_organization_log tracks file movements across drives.",
     json.dumps(["infrastructure", "tables", "dedup", "drive_org"]), 1.0),
    ("decision:infra:mcp_v3_tools", "decision",
     "Built 9 MCP v3 tools in tools_v3.py with manifest and bridge. Extends litigation-context-mcp server with enhanced filing, evidence, and analysis capabilities.",
     json.dumps(["infrastructure", "mcp", "v3", "tools"]), 1.0),
    ("decision:infra:copilot_skills", "decision",
     "Created 40 Copilot skill files: 20 litigation-specific + 20 tool-backed. Located in .copilot/skills/. Covers filing, evidence, judicial analysis, and system operations.",
     json.dumps(["infrastructure", "copilot", "skills", "40_files"]), 1.0),
    ("decision:infra:copilot_agents", "decision",
     "Created 64 Copilot agents in .copilot/agents/. 10 enhanced with detailed SOPs. Covers all pipeline phases, filing workflows, and system operations.",
     json.dumps(["infrastructure", "copilot", "agents", "64_agents", "sops"]), 1.0),
    ("decision:infra:dedup_engine", "decision",
     "Built content_dedup_engine.py (400 lines). Content-based deduplication that peeks inside documents per Andrew's requirement. Moves duplicates to I:\\ drive.",
     json.dumps(["infrastructure", "dedup", "engine", "content_based"]), 1.0),
    ("decision:infra:weekly_maintenance", "decision",
     "Built weekly_maintenance.py (709 lines, 7 sections). Automated maintenance: DB vacuum, index rebuild, stale file cleanup, drive space monitoring, backup verification, report generation.",
     json.dumps(["infrastructure", "maintenance", "weekly", "automation"]), 1.0),
    ("decision:infra:key_documents", "decision",
     "Generated key planning documents: DRIVE_ORGANIZATION_PLAN.md, FILING_PRIORITY_MATRIX.md, MASTER_TIMELINE_EXHIBIT.md (7,812 events), AGENT_FLEET_REPORT.md, AGENT_REGISTRY.md.",
     json.dumps(["infrastructure", "documents", "planning", "reports"]), 1.0),
]

inserted = 0
updated = 0
for key, mtype, content, tags, confidence in memories:
    cur.execute("SELECT key FROM agent_memory WHERE key = ?", (key,))
    if cur.fetchone():
        cur.execute("""UPDATE agent_memory SET content=?, tags=?, confidence=?, updated_at=datetime('now')
                       WHERE key=?""", (content, tags, confidence, key))
        updated += 1
    else:
        cur.execute("""INSERT INTO agent_memory (key, type, content, tags, confidence, source_session)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (key, mtype, content, tags, confidence, "memory_bootstrap_v1"))
        inserted += 1

conn.commit()
print(f"[OK] Memories: {inserted} inserted, {updated} updated, {inserted+updated} total")

# Step 3: Create search view
cur.execute("""
CREATE VIEW IF NOT EXISTS v_agent_memory_search AS
SELECT key, type, substr(content, 1, 200) as preview, tags, confidence, updated_at
FROM agent_memory
ORDER BY updated_at DESC
""")
conn.commit()
print("[OK] View created: v_agent_memory_search")

# Log this session action
cur.execute("""INSERT INTO agent_session_log (session_id, action, detail, todos_completed, todos_total)
               VALUES (?, ?, ?, ?, ?)""",
            ("memory_bootstrap_v1", "memory_system_init",
             f"Created agent_memory ({inserted+updated} entries) + agent_session_log + v_agent_memory_search",
             inserted+updated, inserted+updated))
conn.commit()

# Step 4: Report
print("\n" + "="*60)
print("  AGENT MEMORY SYSTEM — BOOTSTRAP REPORT")
print("="*60)

cur.execute("SELECT COUNT(*) FROM agent_memory")
total = cur.fetchone()[0]
print(f"\n  Total memory entries: {total}")

cur.execute("SELECT type, COUNT(*) as cnt FROM agent_memory GROUP BY type ORDER BY cnt DESC")
print("\n  Breakdown by type:")
for row in cur.fetchall():
    print(f"    {row[0]:12s} : {row[1]:3d}")

cur.execute("SELECT SUM(LENGTH(content)) FROM agent_memory")
content_size = cur.fetchone()[0] or 0
print(f"\n  Total content size: {content_size:,} bytes ({content_size/1024:.1f} KB)")

cur.execute("SELECT COUNT(DISTINCT json_each.value) FROM agent_memory, json_each(agent_memory.tags)")
tag_count = cur.fetchone()[0]
print(f"  Unique tags: {tag_count}")

cur.execute("SELECT AVG(confidence) FROM agent_memory")
avg_conf = cur.fetchone()[0] or 0
print(f"  Average confidence: {avg_conf:.3f}")

elapsed = time.time() - start
print(f"\n  Completed in {elapsed:.2f}s")
print("="*60)

conn.close()
