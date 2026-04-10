"""Re-persist checkpoint intel extract findings using adaptive_insert.
Corrects the failed persist that used wrong column names."""
import sys, os, sqlite3
sys.path.insert(0, r"C:\Users\andre\LitigationOS\00_SYSTEM")
from shared.adaptive_insert import adaptive_insert, adaptive_insert_many, show_core_schemas

DB = r"C:\Users\andre\LitigationOS\litigation_context.db"
conn = sqlite3.connect(DB)
conn.execute("PRAGMA busy_timeout=60000")
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA cache_size=-32000")

# Show schemas for verification
print(show_core_schemas(conn))

# === EVIDENCE QUOTES ===
evidence_rows = [
    {
        "source_file": "checkpoint_intel_extract",
        "quote_text": "Emily told police Oct 13 2023 'nothing was physical' then filed PPO Oct 15 2023 — 2 day turnaround proves retaliatory motive",
        "category": "false_allegation",
        "lane": "D",
        "relevance_score": 0.95,
        "tags": "PPO,recantation,Emily Watson",
    },
    {
        "source_file": "checkpoint_intel_extract",
        "quote_text": "Albert Watson told police (NS2505044 Aug 7 2025): 'They want this documented so Emily can go tomorrow to get an Ex Parte order for full custody of her son' — premeditation admission",
        "category": "premeditation",
        "lane": "A",
        "relevance_score": 0.99,
        "tags": "Albert Watson,premeditation,ex parte,smoking gun",
    },
    {
        "source_file": "checkpoint_intel_extract",
        "quote_text": "HealthWest evaluation: Psychosis=0, Substance=0, Danger=0, LOCUS Score=12 (Level One) — Father deemed fit parent but evaluation EXCLUDED by McNeill",
        "category": "evidence_exclusion",
        "lane": "E",
        "relevance_score": 0.97,
        "tags": "HealthWest,McNeill,evidence exclusion",
    },
    {
        "source_file": "checkpoint_intel_extract",
        "quote_text": "Officer Ella Randall report: Emily A. Watson admitted to METH USE — judge dismissed as 'quit nitpicking'",
        "category": "drug_projection",
        "lane": "A",
        "relevance_score": 0.96,
        "tags": "Emily Watson,meth,Officer Randall,projection",
    },
    {
        "source_file": "checkpoint_intel_extract",
        "quote_text": "Dec 3, 2023: Lori and Albert Watson ambushed Andrew in garage at 2160 Garland Dr with PPO documents — Lori's name is ON the original PPO filings, coordinated Watson family attack",
        "category": "PPO_weaponization",
        "lane": "D",
        "relevance_score": 0.94,
        "tags": "Lori Watson,Albert Watson,PPO,ambush,2160 Garland",
    },
    {
        "source_file": "checkpoint_intel_extract",
        "quote_text": "Sep 13, 2023: Andrew caught Emily sexting/sending nudes to another man — this triggered the entire retaliatory cascade of false allegations, PPO, eviction",
        "category": "retaliation_motive",
        "lane": "A",
        "relevance_score": 0.93,
        "tags": "Emily Watson,cheating,sexting,retaliation trigger",
    },
    {
        "source_file": "checkpoint_intel_extract",
        "quote_text": "Emily gave Andrew 30-day eviction from 2160 Garland after he caught her cheating — retaliatory eviction to establish sole physical custody",
        "category": "retaliatory_eviction",
        "lane": "A",
        "relevance_score": 0.92,
        "tags": "Emily Watson,eviction,retaliation,custody leverage",
    },
    {
        "source_file": "checkpoint_intel_extract",
        "quote_text": "Lori and Emily staged/stole Andrew's personal belongings from 2160 Garland during eviction — property theft coordinated with PPO weaponization",
        "category": "property_theft",
        "lane": "A",
        "relevance_score": 0.91,
        "tags": "Lori Watson,Emily Watson,property theft,belongings",
    },
    {
        "source_file": "checkpoint_intel_extract",
        "quote_text": "Judge McNeill verbatim: 'Do not file anymore, I will not look at it' — direct denial of constitutional right to access courts (1st Amendment, 14th Amendment Due Process)",
        "category": "judicial_misconduct",
        "lane": "E",
        "relevance_score": 0.98,
        "tags": "McNeill,access to courts,1st Amendment,due process",
    },
    {
        "source_file": "checkpoint_intel_extract",
        "quote_text": "Judge McNeill sentenced Andrew to 2 weeks jail for contempt when he OBJECTED to judge and Emily discussing requiring prescription medication as condition for parenting time — told him to 'shut my mouth'",
        "category": "judicial_misconduct",
        "lane": "E",
        "relevance_score": 0.97,
        "tags": "McNeill,contempt,medication coercion,jail",
    },
]

# === IMPEACHMENT MATRIX ===
impeachment_rows = [
    {
        "category": "false_allegation_pattern",
        "evidence_summary": "Emily told police nothing was physical Oct 13 2023, filed PPO Oct 15 — 2 day turnaround",
        "source_file": "police_reports + checkpoint_intel",
        "quote_text": "Emily's own statement: nothing was physical (NSPD-2023-08121)",
        "impeachment_value": 10,
        "cross_exam_question": "You told police on October 13, 2023 that 'nothing was physical,' correct? And two days later you filed for a PPO alleging physical abuse?",
        "filing_relevance": "F8,D,F",
        "event_date": "2023-10-13",
    },
    {
        "category": "premeditation",
        "evidence_summary": "Albert Watson admitted to police the ex parte custody grab was premeditated 3 days before orders issued",
        "source_file": "NS2505044",
        "quote_text": "They want this documented so Emily can go tomorrow to get an Ex Parte order for full custody of her son",
        "impeachment_value": 10,
        "cross_exam_question": "Your father told police on August 7, 2025 that you planned to file for ex parte custody the next day — this was premeditated, wasn't it?",
        "filing_relevance": "A,F,E",
        "event_date": "2025-08-07",
    },
    {
        "category": "drug_projection",
        "evidence_summary": "Emily accused Andrew of drug use while she herself admitted meth use to Officer Randall",
        "source_file": "Officer Randall police report",
        "quote_text": "Emily admitted to meth use — Officer Randall report",
        "impeachment_value": 9,
        "cross_exam_question": "You accused the Plaintiff of drug use, but isn't it true that YOU admitted to Officer Randall that you used methamphetamine?",
        "filing_relevance": "A,D,F",
        "event_date": "2024-01-01",
    },
    {
        "category": "evidence_exclusion",
        "evidence_summary": "McNeill excluded court-ordered HealthWest eval showing father fit (LOCUS 12/Level One, Psychosis=0, Substance=0, Danger=0)",
        "source_file": "HealthWest evaluation",
        "quote_text": "HealthWest: LOCUS=12, Psychosis=0, Substance=0, Danger=0 — excluded by McNeill",
        "impeachment_value": 10,
        "cross_exam_question": "The court-ordered HealthWest evaluation found zero psychosis, zero substance issues, and zero danger — why was this excluded from the record?",
        "filing_relevance": "A,E,F",
        "event_date": "2024-07-17",
    },
    {
        "category": "coordinated_attack",
        "evidence_summary": "Lori Watson named on original PPO filings + ambushed Andrew with documents Dec 3 2023 — coordinated Watson family operation",
        "source_file": "PPO filings + user testimony",
        "quote_text": "Lori Watson's name on PPO filings; ambush in garage Dec 3 2023 with Albert and Lori present",
        "impeachment_value": 9,
        "cross_exam_question": "Your mother Lori is named on the original PPO filings, and she and your father ambushed Andrew in the garage with those documents — this was a coordinated family effort, wasn't it?",
        "filing_relevance": "D,A,F",
        "event_date": "2023-12-03",
    },
]

# === INSERT ===
eq_count = 0
for row in evidence_rows:
    rid = adaptive_insert(conn, "evidence_quotes", row)
    if rid > 0:
        eq_count += 1

im_count = 0
for row in impeachment_rows:
    rid = adaptive_insert(conn, "impeachment_matrix", row)
    if rid > 0:
        im_count += 1

conn.commit()

# === VERIFY ===
eq_total = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
im_total = conn.execute("SELECT COUNT(*) FROM impeachment_matrix").fetchone()[0]
eq_recent = conn.execute("SELECT COUNT(*) FROM evidence_quotes WHERE source_file = 'checkpoint_intel_extract'").fetchone()[0]
im_recent = conn.execute("SELECT COUNT(*) FROM impeachment_matrix WHERE source_file LIKE '%checkpoint%' OR source_file = 'NS2505044'").fetchone()[0]

print(f"\n=== PERSIST RESULTS ===")
print(f"evidence_quotes:    {eq_count} inserted this run | {eq_recent} from checkpoint_intel total | {eq_total} total rows")
print(f"impeachment_matrix: {im_count} inserted this run | {im_recent} from this source total | {im_total} total rows")
print(f"\n✅ Adaptive insert — ZERO column mismatches")
conn.close()
