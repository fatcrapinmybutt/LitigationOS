#!/usr/bin/env python3
"""Initialize master_index.db with the OMEGA v2.0 agent fleet registry."""

import os
import sys
import sqlite3
from datetime import datetime, timezone

# UTF-8 stdout safety
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = os.path.realpath(
    os.path.join(os.path.dirname(__file__),
                 '..', 'pipeline', 'agents', 'master_index.db')
)

OMEGA_AGENTS = [
    ("filing-forge-master", "Filing Forge Master", "Filing packages, QA, Bates stamps, service tracking", "filing,QA,bates,service,exhibit,pre-filing", "A,B,D", "pre-filing-qa,filing-countdown,exhibit-formatter,service-tracker"),
    ("omega-litigation-commander", "Omega Litigation Commander", "Complex multi-step filing workflows with compliance", "COA,docket,record,multi-step,compliance", "A,C,D,F", "michigan-litigation-orchestrator"),
    ("court-form-finder", "Court Form Finder", "Michigan SCAO court form identification", "form,MC,DC,CC,COA,SCAO", "A,B,D", None),
    ("appellate-record-builder", "Appellate Record Builder", "COA/MSC record assembly and appendices", "appellate,COA,MSC,record,appendix", "F", None),
    ("contempt-prosecutor", "Contempt Prosecutor", "Contempt motions and show cause orders", "contempt,show cause,order violation,enforcement", "A,D", None),
    ("garnishment-specialist", "Garnishment Specialist", "Garnishment and wage order enforcement", "garnishment,wage,post-judgment,enforcement", "A,D,F", None),
    ("post-judgment-enforcer", "Post-Judgment Enforcer", "Post-judgment enforcement motions", "post-judgment,enforcement,collections,compliance", "A,D,F", None),
    ("timeline-forensics", "Timeline Forensics", "Hearing transcripts, chronology, testimony extraction", "transcript,chronology,testimony,ruling,objection,timeline", "A,B,C", "transcript-analyzer"),
    ("court-order-tracker", "Court Order Tracker", "Track compliance with court orders by all parties", "order,compliance,tracking,violation", "A,D,E", "order-compliance-monitor"),
    ("damages-calculator", "Damages Calculator", "Calculate damages, filing fees, service costs, mileage", "damages,costs,fees,mileage,calculation", "A,D,F", "cost-tracker"),
    ("case-strategy-architect", "Case Strategy Architect", "High-level litigation strategy and prioritization", "strategy,war plan,priorities,case theory", "A,C", None),
    ("settlement-analyzer", "Settlement Analyzer", "Settlement evaluation and counter-proposals", "settlement,evaluation,counter,negotiation", "A,C,F", None),
    ("summary-judgment", "Summary Judgment", "Summary judgment analysis and no-genuine-issue arguments", "MSJ,SJ,summary judgment,no genuine issue", "A,D", None),
    ("evidence-warfare-commander", "Evidence Warfare Commander", "Evidence triage, gap analysis, impeachment prep", "evidence,gap,impeachment,triage,strategy", "A,B,C", None),
    ("evidence-vehicle-scanner", "Evidence Vehicle Scanner", "PDF scanning and lane routing via MEEK signals", "PDF,scan,MEEK,lane,routing,vehicle", "A,B", None),
    ("evidence-authentication", "Evidence Authentication", "Chain of custody and evidence admissibility", "authentication,chain of custody,admissibility,foundation", "B", None),
    ("parental-alienation-detector", "Parental Alienation Detector", "Detect and document parental alienation indicators", "alienation,withholding,factor j,722.23", "A", None),
    ("expert-witness-manager", "Expert Witness Manager", "Expert witness selection, reports, Daubert prep", "expert,witness,Daubert,report", "A,B,D", None),
    ("subpoena-engine", "Subpoena Engine", "Draft and track subpoenas", "subpoena,witness,document request", "A,B,D", None),
    ("judicial-accountability-engine", "Judicial Accountability Engine", "JTC complaints and judicial misconduct documentation", "JTC,misconduct,judicial,complaint,canon", "E", None),
    ("judicial-recusal-engine", "Judicial Recusal Engine", "MCR 2.003 disqualification and bias documentation", "recusal,disqualification,2.003,bias,mcr", "A,E", None),
    ("family-law-guardian", "Family Law Guardian", "Custody, parenting time, GAL motions", "custody,parenting time,GAL,family law", "A", None),
    ("affidavit-chronology-builder", "Affidavit Chronology Builder", "Mine affidavits/exports, build master chronology", "affidavit,chronology,narrative,sworn", "A,B,C", None),
    ("motion-practice", "Motion Practice", "Draft, review, and strengthen any motion type", "motion,draft,review,practice", "A,D", None),
    ("trial-preparation", "Trial Preparation", "Witness lists, exhibit lists, trial briefs, voir dire", "trial,witness list,exhibit list,brief,voir dire", "A,D", None),
    ("omega-dedup", "Omega Dedup", "Content-based dedup across drives (peek inside, no hashing)", "dedup,duplicate,content,comparison", "B,C", None),
    ("self-evolving-fleet-manager", "Self-Evolving Fleet Manager", "Monitor, upgrade, and evolve the agent fleet", "fleet,optimize,monitor,upgrade,evolve", "C,E", None),
    ("compliance-auditor", "Compliance Auditor", "PII redaction, filing compliance, pre-submission checks", "PII,redaction,compliance,audit,submission", "D,E", "redaction-agent"),
]


def main():
    print(f"[init_agent_registry] DB path: {DB_PATH}")
    print(f"[init_agent_registry] DB exists: {os.path.exists(DB_PATH)}")
    print(f"[init_agent_registry] DB size before: {os.path.getsize(DB_PATH)} bytes")
    print()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Set PRAGMAs
    cur.execute("PRAGMA busy_timeout = 60000;")
    cur.execute("PRAGMA journal_mode = WAL;")
    cur.execute("PRAGMA cache_size = -32000;")
    cur.execute("PRAGMA temp_store = MEMORY;")
    cur.execute("PRAGMA synchronous = NORMAL;")
    print("[init_agent_registry] PRAGMAs set (WAL, busy_timeout=60s, cache=32MB)")

    # Create agent_registry table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_registry (
            agent_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            trigger_keywords TEXT,
            lanes_supported TEXT,
            status TEXT DEFAULT 'active',
            agent_type TEXT DEFAULT 'omega_v2',
            replaces TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    print("[init_agent_registry] Created table: agent_registry")

    # Create agent_log table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (agent_id) REFERENCES agent_registry(agent_id)
        );
    """)
    print("[init_agent_registry] Created table: agent_log")

    # Create index on agent_log for faster lookups
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_log_agent_id
            ON agent_log(agent_id);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_registry_status
            ON agent_registry(status);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_agent_registry_type
            ON agent_registry(agent_type);
    """)
    print("[init_agent_registry] Created indexes")

    conn.commit()

    # Insert agents using INSERT OR REPLACE for idempotency
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    rows = []
    for agent in OMEGA_AGENTS:
        agent_id, name, desc, keywords, lanes, replaces = agent
        rows.append((agent_id, name, desc, keywords, lanes, 'active', 'omega_v2', replaces, now, now))

    cur.executemany("""
        INSERT OR REPLACE INTO agent_registry
            (agent_id, name, description, trigger_keywords, lanes_supported,
             status, agent_type, replaces, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)
    print(f"[init_agent_registry] Inserted {len(rows)} agents")

    # Log registrations
    log_rows = [
        (a[0], 'registered', f'OMEGA v2.0 fleet init — {a[1]}', now)
        for a in OMEGA_AGENTS
    ]
    cur.executemany("""
        INSERT INTO agent_log (agent_id, action, details, timestamp)
        VALUES (?, ?, ?, ?)
    """, log_rows)
    print(f"[init_agent_registry] Logged {len(log_rows)} registration events")

    conn.commit()

    # Verification
    count = cur.execute("SELECT COUNT(*) FROM agent_registry").fetchone()[0]
    log_count = cur.execute("SELECT COUNT(*) FROM agent_log").fetchone()[0]
    active = cur.execute("SELECT COUNT(*) FROM agent_registry WHERE status='active'").fetchone()[0]

    print()
    print("=" * 60)
    print("  OMEGA v2.0 Agent Fleet Registry — Summary")
    print("=" * 60)
    print(f"  Agents registered:  {count}")
    print(f"  Active agents:      {active}")
    print(f"  Log entries:        {log_count}")
    print(f"  Agent type:         omega_v2")
    print(f"  DB size:            {os.path.getsize(DB_PATH):,} bytes")
    print()

    # Print lane distribution
    print("  Lane Distribution:")
    for lane in ['A', 'B', 'C', 'D', 'E', 'F']:
        lane_count = cur.execute(
            "SELECT COUNT(*) FROM agent_registry WHERE lanes_supported LIKE ?",
            (f'%{lane}%',)
        ).fetchone()[0]
        print(f"    Lane {lane}: {lane_count} agents")

    print()
    print("  Agent Roster:")
    for row in cur.execute("SELECT agent_id, lanes_supported FROM agent_registry ORDER BY agent_id"):
        print(f"    {row[0]:<35} lanes: {row[1]}")

    print()
    print("=" * 60)
    print("  Registry initialization COMPLETE")
    print("=" * 60)

    conn.close()


if __name__ == '__main__':
    main()
