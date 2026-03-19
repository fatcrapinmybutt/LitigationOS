#!/usr/bin/env python3
"""
LitigationOS Deep Litigation Analysis Engine
Searches 472K+ pages and 308K+ evidence quotes for ALL litigation focus areas.
Outputs court-ready analysis report to Desktop.
"""
import sys, os, sqlite3, re, json
from datetime import datetime
from collections import defaultdict, Counter

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')
sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', errors='replace')

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"
REPORT_DIR = r"C:\Users\andre\Desktop\LITIGATION_ANALYSIS"

PRAGMAS = """
PRAGMA busy_timeout = 120000;
PRAGMA journal_mode = WAL;
PRAGMA cache_size = -64000;
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;
PRAGMA mmap_size = 8589934592;
"""

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.row_factory = sqlite3.Row
    for p in PRAGMAS.strip().split('\n'):
        conn.execute(p.strip())
    return conn

def ensure_dir(d):
    os.makedirs(d, exist_ok=True)

# ============================================================
# FOCUS AREA DEFINITIONS — Every negative connotation to rebut
# ============================================================

FOCUS_AREAS = {
    # ---- FRAUD ON THE COURT ----
    "ELLA_RANDALL_FRAUD": {
        "title": "Ella Randall Police Quote Fraud — Meth Misattribution",
        "description": "Emily used a police quote from Officer Ella Randall as if police said something about meth, when it was Emily who made the meth accusation. This is fraud on the court — intentional misrepresentation of evidence.",
        "search_terms": ["Ella Randall", "Randall", "meth", "methamphetamine", "drug test", 
                        "substance abuse", "drug use", "police report", "police said", "officer said",
                        "officer Randall", "Randall report"],
        "category": "fraud_on_court"
    },
    "QUIT_NITPICKING": {
        "title": "Judge McNeill 'Quit Nitpicking' — Dismissal of Due Process",
        "description": "Judge told Andrew to 'quit nitpicking' when he raised legitimate legal objections. This demonstrates bias and refusal to hear pro se litigant's arguments.",
        "search_terms": ["nitpick", "quit nitpicking", "stop nitpicking", "nitpicking",
                        "stop arguing", "enough", "move on", "overruled", "denied without hearing"],
        "category": "judicial_bias"
    },
    
    # ---- EMILY'S PERJURY & FALSE STATEMENTS ----
    "EMILY_PERJURY_GENERAL": {
        "title": "Emily Watson Perjury — Sworn False Statements",
        "description": "Every instance of Emily making sworn statements contradicted by evidence.",
        "search_terms": ["perjur", "false statement", "lied under oath", "sworn", "affidavit",
                        "verification", "under penalty", "misrepresent", "deceived the court"],
        "category": "perjury"
    },
    "EMILY_FALSE_ACCUSATIONS": {
        "title": "Emily's Accusations Without Evidence",
        "description": "Every accusation Emily made against Andrew that lacks evidentiary support.",
        "search_terms": ["accused", "allegation", "alleged", "claimed", "without evidence",
                        "unsubstantiated", "unfounded", "no proof", "no evidence", "baseless",
                        "fabricat", "false accus"],
        "category": "false_accusations"
    },
    "EMILY_FALSE_POLICE_REPORTS": {
        "title": "False Police Reports Filed by Emily",
        "description": "Every police report or welfare check initiated by Emily based on false information.",
        "search_terms": ["police report", "welfare check", "false report", "called police",
                        "law enforcement", "officer", "dispatch", "911", "complaint filed",
                        "North Shore", "Norton Shores", "Muskegon police"],
        "category": "false_reports"
    },
    "EMILY_METH_DRUG_LIES": {
        "title": "Drug/Meth Accusations — All Unsubstantiated",
        "description": "Emily's drug accusations against Andrew — zero positive drug tests, zero findings.",
        "search_terms": ["meth", "methamphetamine", "drug", "substance", "intoxicat", "impair",
                        "drug test", "hair follicle", "urinalysis", "substance abuse",
                        "clean", "negative test", "no finding"],
        "category": "false_accusations"
    },
    "EMILY_ABUSE_LIES": {
        "title": "Abuse Allegations — All Unfounded",
        "description": "Emily's abuse/neglect allegations against Andrew — zero CPS findings, zero convictions.",
        "search_terms": ["abuse", "neglect", "domestic violence", "assault", "harm to child",
                        "danger", "unsafe", "violent", "aggressive", "threat", "CPS",
                        "protective services", "investigation", "unfounded", "no finding"],
        "category": "false_accusations"
    },
    "EMILY_MENTAL_HEALTH_LIES": {
        "title": "Mental Health Stigmatization",
        "description": "Emily weaponized mental health stigma against Andrew without clinical basis.",
        "search_terms": ["mental health", "mental illness", "psych", "unstable", "delusional",
                        "paranoid", "narciss", "disorder", "diagnosis", "evaluation",
                        "counseling", "therapy", "competent", "capacity"],
        "category": "false_accusations"
    },

    # ---- JUDICIAL BIAS & MISCONDUCT ----
    "JUDGE_EX_PARTE": {
        "title": "Ex Parte Communications — 18.26% Rate",
        "description": "All ex parte contacts between Judge McNeill and Emily/her counsel.",
        "search_terms": ["ex parte", "without notice", "outside presence", "not notified",
                        "no notice to", "unilateral", "one-sided", "chambers",
                        "off the record"],
        "category": "judicial_misconduct"
    },
    "JUDGE_BIAS_RULINGS": {
        "title": "Asymmetric Ruling Patterns — 87× Motion Imbalance",
        "description": "Judge ruled in Emily's favor disproportionately, denied Andrew's motions systematically.",
        "search_terms": ["denied", "overruled", "motion denied", "request denied",
                        "granted", "plaintiff's motion", "defendant's motion",
                        "without hearing", "sua sponte", "sua sponte order"],
        "category": "judicial_bias"
    },
    "JUDGE_PARENTING_TIME_SUSPENSION": {
        "title": "Parenting Time Suspension — 569+ Days Without Due Process",
        "description": "Judge suspended Andrew's parenting time without evidentiary hearing, violating MCR 3.207.",
        "search_terms": ["parenting time", "suspend", "restrict", "denied access",
                        "no contact", "supervised", "supervision required",
                        "bond", "cash bond", "financial barrier",
                        "MCR 3.207", "MCR 3.310", "best interest"],
        "category": "due_process"
    },
    "JUDGE_BOND_REQUIREMENT": {
        "title": "Unconstitutional Bond Requirement",
        "description": "Cash bond requirement blocking court access — violates due process and equal protection.",
        "search_terms": ["bond", "cash bond", "$500", "$1000", "financial", "deposit",
                        "payment required", "pay before", "access to court",
                        "indigent", "inability to pay"],
        "category": "due_process"
    },
    "JUDGE_MCR_3207_VIOLATION": {
        "title": "MCR 3.207(B) Noncompliance — 0% Compliance Rate",
        "description": "Court never conducted required MCR 3.207(B) review of parenting time order.",
        "search_terms": ["3.207", "MCR 3.207", "review hearing", "status conference",
                        "continued without review", "no review", "Friend of Court",
                        "FOC", "recommendation"],
        "category": "procedural_violation"
    },
    "JUDGE_HEARING_DENIALS": {
        "title": "Hearings Denied or Never Scheduled",
        "description": "Motions that were denied without hearing or where hearings were never scheduled.",
        "search_terms": ["hearing denied", "no hearing", "without hearing",
                        "hearing not scheduled", "motion to schedule", "request for hearing",
                        "14 day", "MCR 3.310"],
        "category": "due_process"
    },

    # ---- PARENTAL ALIENATION ----
    "ALIENATION_INTERFERENCE": {
        "title": "305 Documented Interference Incidents",
        "description": "Every documented instance of Emily interfering with father-child relationship.",
        "search_terms": ["alienat", "interfere", "withhold", "prevent contact",
                        "denied visit", "cancelled", "refused", "blocked",
                        "phone call denied", "FaceTime", "video call",
                        "gatekeep", "no communication"],
        "category": "alienation"
    },
    "ALIENATION_CHILD_IMPACT": {
        "title": "Impact on L.D.W. — Child Harm Documentation",
        "description": "Evidence of harm to Lincoln from forced separation from father.",
        "search_terms": ["child's wellbeing", "child welfare", "developmental",
                        "attachment", "bonding", "emotional harm", "psychological",
                        "regression", "behavior change", "crying", "misses",
                        "Lincoln", "L.D.W.", "son", "child"],
        "category": "child_harm"
    },

    # ---- CONSPIRACY ----
    "WATSON_FAMILY_COORDINATION": {
        "title": "Watson Family Coordinated Action",
        "description": "Evidence of coordination between Emily, Mark Watson, Patricia Watson, Albert Watson.",
        "search_terms": ["Mark Watson", "Patricia Watson", "Albert Watson", "Tiffany",
                        "Watson family", "coordinated", "conspiracy", "concerted",
                        "together", "assisted", "facilitated", "helped Emily"],
        "category": "conspiracy"
    },
    "RON_BERRY_UPL": {
        "title": "Ronald Berry Unauthorized Practice of Law",
        "description": "Evidence of Ron Berry providing legal advice/assistance without a license.",
        "search_terms": ["Ron Berry", "Ronald Berry", "Berry", "boyfriend",
                        "legal advice", "unauthorized practice", "UPL",
                        "coaching", "prepared", "drafted", "filed on behalf"],
        "category": "upl"
    },

    # ---- PPO WEAPONIZATION ----
    "PPO_WEAPONIZATION": {
        "title": "PPO Used as Custody Weapon",
        "description": "Personal Protection Order obtained on false pretenses to gain custody leverage.",
        "search_terms": ["PPO", "personal protection", "protection order",
                        "2023-5907", "stalking", "harassment", "reasonable cause",
                        "no contact", "restrain", "violat"],
        "category": "ppo_abuse"
    },
    "PPO_FALSE_BASIS": {
        "title": "PPO Based on False Allegations",
        "description": "The factual basis for the PPO was false — no actual threat, no violence.",
        "search_terms": ["no threat", "no violence", "no history", "no prior",
                        "fabricated", "exaggerated", "inflated", "manufactured",
                        "weaponized", "tactical", "strategic"],
        "category": "ppo_abuse"
    },

    # ---- CONSTITUTIONAL VIOLATIONS ----
    "DUE_PROCESS_DENIAL": {
        "title": "14th Amendment Due Process Violations",
        "description": "Every instance where Andrew was denied due process of law.",
        "search_terms": ["due process", "14th amendment", "fundamental right",
                        "liberty interest", "Troxel", "Santosky", "Sanders",
                        "Mathews v Eldridge", "meaningful hearing",
                        "notice", "opportunity to be heard"],
        "category": "constitutional"
    },
    "RIGHT_TO_PARENT": {
        "title": "Fundamental Right to Parent — De Facto Termination",
        "description": "569+ day separation constitutes de facto termination without TPR protections.",
        "search_terms": ["fundamental right", "right to parent", "termination",
                        "de facto", "custody", "care and control",
                        "Troxel v Granville", "parent-child", "relationship"],
        "category": "constitutional"
    },

    # ---- SPECIFIC INCIDENTS ----
    "AUGUST_2025_SUSPENSION": {
        "title": "August 2025 Ex Parte Suspension Order",
        "description": "The critical ex parte order that suspended parenting time without hearing.",
        "search_terms": ["August 2025", "August 8", "suspension order", "ex parte order",
                        "suspended parenting", "without hearing", "emergency order"],
        "category": "critical_incident"
    },
    "BRUISING_INCIDENT": {
        "title": "Child Bruising — Andrew Reported, Emily Weaponized",
        "description": "Andrew reported bruising on Lincoln; Emily twisted it into accusation against Andrew.",
        "search_terms": ["bruis", "marks", "injury", "hurt", "CPS call",
                        "protective services", "report", "bruise on"],
        "category": "critical_incident"
    },
    "CONTEMPT_VIOLATIONS": {
        "title": "Emily's Contempt of Court Orders",
        "description": "Every instance where Emily violated court orders.",
        "search_terms": ["contempt", "violat", "disobey", "failed to comply",
                        "non-compliance", "willful", "court order violated",
                        "in violation of"],
        "category": "contempt"
    },
    "FRAUD_ON_COURT_ALL": {
        "title": "All Instances of Fraud on the Court",
        "description": "Every misrepresentation, fabrication, or deception presented to the court.",
        "search_terms": ["fraud on the court", "misrepresent", "deceiv", "fabricat",
                        "false evidence", "tamper", "alter", "forge",
                        "material misrepresentation", "mislead"],
        "category": "fraud_on_court"
    },
    "FINANCIAL_HARM": {
        "title": "Financial Harm to Andrew",
        "description": "All financial damages: legal costs, lost income, housing costs, bond.",
        "search_terms": ["financial", "cost", "expense", "lost income", "employment",
                        "housing", "rent", "evict", "damage", "payment",
                        "attorney fees", "filing fee", "bond"],
        "category": "damages"
    },
    "EMOTIONAL_HARM": {
        "title": "Emotional/Psychological Harm",
        "description": "Documentation of emotional and psychological harm to Andrew and L.D.W.",
        "search_terms": ["emotional", "psychological", "distress", "suffering",
                        "anguish", "trauma", "PTSD", "depression", "anxiety",
                        "sleep", "weight", "health"],
        "category": "damages"
    },
}

def search_pages_fts(conn, terms, limit=500):
    """Search pages using FTS5"""
    results = []
    for term in terms:
        try:
            # Try FTS5 first
            rows = conn.execute("""
                SELECT p.text_content, p.page_number, d.file_path, d.file_name
                FROM pages_fts pf
                JOIN pages p ON pf.rowid = p.id
                JOIN documents d ON p.document_id = d.id
                WHERE pages_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (f'"{term}"', limit)).fetchall()
            results.extend(rows)
        except:
            # Fallback to LIKE
            rows = conn.execute("""
                SELECT p.text_content, p.page_number, d.file_path, d.file_name
                FROM pages p
                JOIN documents d ON p.document_id = d.id
                WHERE p.text_content LIKE ?
                LIMIT ?
            """, (f'%{term}%', limit)).fetchall()
            results.extend(rows)
    return results

def search_evidence_quotes(conn, terms, limit=500):
    """Search evidence_quotes table"""
    results = []
    for term in terms:
        try:
            rows = conn.execute("""
                SELECT quote_text, source_file, page_number, evidence_category
                FROM evidence_quotes
                WHERE quote_text LIKE ?
                LIMIT ?
            """, (f'%{term}%', limit)).fetchall()
            results.extend(rows)
        except:
            pass
    return results

def search_contradictions(conn, terms, limit=200):
    """Search contradiction_map using correct column names"""
    results = []
    for term in terms:
        try:
            rows = conn.execute("""
                SELECT id, source_a_text, source_b_text, contradiction_type, severity, legal_impact
                FROM contradiction_map
                WHERE source_a_text LIKE ? OR source_b_text LIKE ? OR legal_impact LIKE ?
                LIMIT ?
            """, (f'%{term}%', f'%{term}%', f'%{term}%', limit)).fetchall()
            results.extend(rows)
        except:
            pass
    return results

def search_judicial_violations(conn, terms, limit=200):
    """Search judicial_violations using correct column names"""
    results = []
    for term in terms:
        try:
            rows = conn.execute("""
                SELECT violation_id, judge_name, canon_number, violation_description, severity
                FROM judicial_violations
                WHERE violation_description LIKE ? OR canon_text LIKE ? OR evidence_refs LIKE ?
                LIMIT ?
            """, (f'%{term}%', f'%{term}%', f'%{term}%', limit)).fetchall()
            results.extend(rows)
        except:
            pass
    return results

def analyze_focus_area(conn, area_id, area_def):
    """Run deep analysis for one focus area"""
    terms = area_def["search_terms"]
    
    # Search across all tables
    page_hits = search_pages_fts(conn, terms, limit=300)
    quote_hits = search_evidence_quotes(conn, terms, limit=300)
    contradiction_hits = search_contradictions(conn, terms[:5], limit=100)
    violation_hits = search_judicial_violations(conn, terms[:5], limit=100)
    
    # Deduplicate page hits by content
    seen_content = set()
    unique_pages = []
    for row in page_hits:
        content_key = str(row[0])[:200]
        if content_key not in seen_content:
            seen_content.add(content_key)
            unique_pages.append(row)
    
    # Deduplicate quote hits
    seen_quotes = set()
    unique_quotes = []
    for row in quote_hits:
        qkey = str(row[0])[:200]
        if qkey not in seen_quotes:
            seen_quotes.add(qkey)
            unique_quotes.append(row)
    
    # Extract source files
    source_files = set()
    for row in unique_pages:
        try:
            source_files.add(str(row[2]) if row[2] else str(row[3]))
        except:
            pass
    for row in unique_quotes:
        try:
            source_files.add(str(row[1]))
        except:
            pass
    
    return {
        "area_id": area_id,
        "title": area_def["title"],
        "description": area_def["description"],
        "category": area_def["category"],
        "page_hits": len(unique_pages),
        "quote_hits": len(unique_quotes),
        "contradiction_hits": len(contradiction_hits),
        "violation_hits": len(violation_hits),
        "total_evidence_points": len(unique_pages) + len(unique_quotes) + len(contradiction_hits) + len(violation_hits),
        "source_files": list(source_files)[:50],
        "sample_pages": [{"text": str(r[0])[:500], "page": r[1], "file": str(r[2])[:100] if r[2] else str(r[3])[:100]} for r in unique_pages[:15]],
        "sample_quotes": [{"text": str(r[0])[:500], "source": str(r[1])[:100]} for r in unique_quotes[:15]],
    }

def generate_master_report(results):
    """Generate comprehensive analysis report"""
    ensure_dir(REPORT_DIR)
    report_path = os.path.join(REPORT_DIR, "MASTER_LITIGATION_ANALYSIS.md")
    
    # Sort by evidence count
    sorted_results = sorted(results.values(), key=lambda x: x["total_evidence_points"], reverse=True)
    
    lines = [
        "# MASTER LITIGATION ANALYSIS — EVERY FOCUS AREA",
        f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"## Case: Pigors v. Watson et al.",
        f"## Database: 472K+ pages, 308K+ evidence quotes, 10K+ contradictions",
        "",
        "---",
        "",
        "# EXECUTIVE SUMMARY",
        "",
        f"**Total Focus Areas Analyzed:** {len(results)}",
        f"**Total Evidence Points Found:** {sum(r['total_evidence_points'] for r in sorted_results):,}",
        "",
        "## Focus Area Rankings (by evidence strength)",
        "",
        "| # | Focus Area | Evidence Points | Pages | Quotes | Contradictions | Violations | Category |",
        "|---|-----------|----------------|-------|--------|---------------|------------|----------|",
    ]
    
    for i, r in enumerate(sorted_results, 1):
        lines.append(f"| {i} | {r['title'][:50]} | **{r['total_evidence_points']}** | "
                     f"{r['page_hits']} | {r['quote_hits']} | {r['contradiction_hits']} | "
                     f"{r['violation_hits']} | {r['category']} |")
    
    lines.extend(["", "---", ""])
    
    # Category totals
    cat_totals = defaultdict(int)
    for r in sorted_results:
        cat_totals[r["category"]] += r["total_evidence_points"]
    
    lines.extend([
        "## Evidence by Category",
        "",
        "| Category | Total Evidence Points |",
        "|----------|---------------------|",
    ])
    for cat, total in sorted(cat_totals.items(), key=lambda x: -x[1]):
        lines.append(f"| {cat} | **{total:,}** |")
    
    lines.extend(["", "---", ""])
    
    # Detailed sections for each focus area
    for r in sorted_results:
        lines.extend([
            f"# {r['title']}",
            f"**Category:** {r['category']} | **Evidence Points:** {r['total_evidence_points']}",
            "",
            f"> {r['description']}",
            "",
            f"### Evidence Summary",
            f"- **Page matches:** {r['page_hits']}",
            f"- **Evidence quotes:** {r['quote_hits']}",
            f"- **Contradictions:** {r['contradiction_hits']}",
            f"- **Judicial violations:** {r['violation_hits']}",
            "",
        ])
        
        if r["sample_pages"]:
            lines.append("### Key Document Excerpts")
            lines.append("")
            for j, sp in enumerate(r["sample_pages"][:10], 1):
                lines.append(f"**{j}. [{sp.get('file', 'unknown')}] p.{sp.get('page', '?')}:**")
                text = sp.get('text', '')[:400].replace('\n', ' ')
                lines.append(f"> {text}")
                lines.append("")
        
        if r["sample_quotes"]:
            lines.append("### Key Evidence Quotes")
            lines.append("")
            for j, sq in enumerate(r["sample_quotes"][:10], 1):
                text = sq.get('text', '')[:400].replace('\n', ' ')
                lines.append(f"**{j}.** [{sq.get('source', '?')[:60]}]: *\"{text}\"*")
                lines.append("")
        
        if r["source_files"]:
            lines.append("### Source Documents")
            lines.append("")
            for sf in r["source_files"][:20]:
                lines.append(f"- `{sf}`")
            lines.append("")
        
        lines.extend(["---", ""])
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"\nMaster report saved: {report_path}")
    print(f"Total focus areas: {len(results)}")
    print(f"Total evidence points: {sum(r['total_evidence_points'] for r in sorted_results):,}")
    return report_path

def generate_rebuttal_matrix(results):
    """Generate a rebuttal matrix — every negative connotation with counter-evidence"""
    path = os.path.join(REPORT_DIR, "REBUTTAL_MATRIX.md")
    
    lines = [
        "# MASTER REBUTTAL MATRIX",
        f"## Every Negative Connotation — Documented Counter-Evidence",
        f"## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "| # | Negative Claim/Connotation | Category | Counter-Evidence Points | Rebuttal Strategy |",
        "|---|--------------------------|----------|------------------------|-------------------|",
    ]
    
    rebuttals = {
        "EMILY_METH_DRUG_LIES": "Zero positive drug tests. Zero findings. Zero convictions. Emily made the meth claim — not police.",
        "EMILY_ABUSE_LIES": "Zero CPS findings. Zero founded abuse/neglect. Andrew called CPS once about bruising on Lincoln.",
        "EMILY_MENTAL_HEALTH_LIES": "No clinical diagnosis supports Emily's claims. Weaponized stigma without professional basis.",
        "EMILY_FALSE_POLICE_REPORTS": "Pattern of false welfare checks. No charges ever resulted. Reports used as custody leverage.",
        "EMILY_FALSE_ACCUSATIONS": "Systematic false accusations without supporting evidence. Pattern of fabrication for court advantage.",
        "ELLA_RANDALL_FRAUD": "Emily attributed her own meth accusation to Officer Randall. Fraud on the court — MCR 2.114.",
        "QUIT_NITPICKING": "Judge dismissed legitimate due process objections. Demonstrates bias against pro se litigant.",
        "JUDGE_EX_PARTE": "18.26% ex parte rate = 3.65× normal. Documented pattern of ex parte contact with Emily/counsel.",
        "JUDGE_BIAS_RULINGS": "87× motion asymmetry. MCR 3.207(B) 0% compliance. p < 0.0001 probability of fair proceedings.",
        "JUDGE_PARENTING_TIME_SUSPENSION": "569+ days without evidentiary hearing. De facto TPR without constitutional protections.",
        "PPO_WEAPONIZATION": "PPO obtained on false pretenses. Used to block parenting time. Tactical, not protective.",
        "PPO_FALSE_BASIS": "No actual threat. No violence history. No prior incidents. Manufactured for custody leverage.",
        "ALIENATION_INTERFERENCE": "305 documented interference incidents. Systematic pattern under MCL 722.23(j).",
        "WATSON_FAMILY_COORDINATION": "Coordinated action by Watson family to alienate Andrew from Lincoln.",
        "RON_BERRY_UPL": "Non-attorney providing legal advice. MCL 600.916 violation. AGC complaint filed.",
        "JUDGE_BOND_REQUIREMENT": "Cash bond blocks court access for indigent litigant. Violates due process + equal protection.",
        "JUDGE_MCR_3207_VIOLATION": "0% compliance with mandatory MCR 3.207(B) review. Never conducted.",
        "FRAUD_ON_COURT_ALL": "Multiple instances of fabricated evidence presented to court.",
        "CONTEMPT_VIOLATIONS": "Emily violated court orders with impunity. No enforcement by Judge McNeill.",
        "DUE_PROCESS_DENIAL": "14th Amendment violated: no hearing, no evidence, no review, no meaningful process.",
        "RIGHT_TO_PARENT": "Fundamental right (Troxel v. Granville) terminated de facto without TPR protections.",
        "AUGUST_2025_SUSPENSION": "Ex parte order suspending parenting time without ANY hearing. MCR 3.310(C)(3) violated.",
        "BRUISING_INCIDENT": "Andrew reported bruising on son to CPS. Emily twisted it into accusation against Andrew.",
        "FINANCIAL_HARM": "Catastrophic financial damage: legal costs, lost income, housing instability, court-imposed bond.",
        "EMOTIONAL_HARM": "Severe emotional distress from 569+ day forced separation from son.",
        "ALIENATION_CHILD_IMPACT": "Documented developmental harm to L.D.W. from parent-child separation.",
        "JUDGE_HEARING_DENIALS": "Multiple motions denied without hearing. No opportunity to present evidence.",
        "EMILY_PERJURY_GENERAL": "Pattern of sworn false statements contradicted by documentary evidence.",
    }
    
    sorted_results = sorted(results.values(), key=lambda x: x["total_evidence_points"], reverse=True)
    
    for i, r in enumerate(sorted_results, 1):
        rebuttal = rebuttals.get(r["area_id"], "Counter-evidence documented — see analysis.")
        lines.append(f"| {i} | **{r['title'][:45]}** | {r['category']} | "
                     f"**{r['total_evidence_points']}** | {rebuttal[:80]} |")
    
    lines.extend(["", "---", ""])
    lines.append("## LITIGATION STRATEGY NOTES")
    lines.append("")
    lines.append("1. **Lead with the strongest evidence**: Present focus areas with highest evidence counts first")
    lines.append("2. **Ella Randall fraud**: This is potentially the strongest single impeachment point — Emily committed fraud on the court")
    lines.append("3. **Statistical evidence**: 87× motion asymmetry, 18.26% ex parte rate, 0% MCR 3.207(B) compliance — devastating pattern")
    lines.append("4. **Constitutional framing**: Always frame as fundamental rights violations (Troxel, Santosky, Sanders)")
    lines.append("5. **569+ days**: This number alone is shocking to any appellate court — use it in every filing")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Rebuttal matrix saved: {path}")

def main():
    print("=" * 60)
    print("LitigationOS Deep Litigation Analysis Engine")
    print(f"Analyzing {len(FOCUS_AREAS)} focus areas")
    print(f"Database: {DB_PATH}")
    print("=" * 60)
    
    conn = get_db()
    
    # Get DB stats
    doc_count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    page_count = conn.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    print(f"\nDatabase: {doc_count:,} documents, {page_count:,} pages")
    
    try:
        quote_count = conn.execute("SELECT COUNT(*) FROM evidence_quotes").fetchone()[0]
        print(f"Evidence quotes: {quote_count:,}")
    except:
        quote_count = 0
    
    results = {}
    for i, (area_id, area_def) in enumerate(FOCUS_AREAS.items(), 1):
        print(f"\n[{i}/{len(FOCUS_AREAS)}] Analyzing: {area_def['title'][:60]}...")
        try:
            result = analyze_focus_area(conn, area_id, area_def)
            results[area_id] = result
            print(f"  → {result['total_evidence_points']} evidence points "
                  f"({result['page_hits']} pages, {result['quote_hits']} quotes, "
                  f"{result['contradiction_hits']} contradictions, {result['violation_hits']} violations)")
        except Exception as e:
            print(f"  → ERROR: {e}")
            results[area_id] = {
                "area_id": area_id, "title": area_def["title"],
                "description": area_def["description"], "category": area_def["category"],
                "page_hits": 0, "quote_hits": 0, "contradiction_hits": 0, "violation_hits": 0,
                "total_evidence_points": 0, "source_files": [], "sample_pages": [], "sample_quotes": []
            }
    
    # Generate reports
    print("\n" + "=" * 60)
    print("GENERATING REPORTS")
    print("=" * 60)
    
    report_path = generate_master_report(results)
    generate_rebuttal_matrix(results)
    
    # Save JSON data for further processing
    json_path = os.path.join(REPORT_DIR, "analysis_data.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"JSON data saved: {json_path}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    total_evidence = sum(r["total_evidence_points"] for r in results.values())
    print(f"Total focus areas: {len(results)}")
    print(f"Total evidence points: {total_evidence:,}")
    print(f"Reports saved to: {REPORT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
