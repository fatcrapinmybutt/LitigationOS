#!/usr/bin/env python3
"""
Tool #237 — Emergency Motion Generator
========================================
Generates framework for emergency custody motion (F4):
- Gathers evidence of immediate harm to child (medical, aggression, withholding)
- Maps to MCL 722.27a(3) requirements for emergency orders
- Builds fact section from actual DB evidence (NO placeholders where data exists)
- Includes Albert Watson aggression evidence (NS2505044, physical removal of child)
- References HealthWest weaponization

Outputs: MD motion framework + JSON to reports dir
LitigationOS — Pigors v. Watson (14th Circuit Court, Muskegon County)
"""
import sys
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from collections import defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
REPO = SCRIPT_DIR.parent.parent
REPORTS_DIR = REPO / "00_SYSTEM" / "reports"
DB_PATH = REPO / "litigation_context.db"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Party identity (VERIFIED — from instructions, NEVER fabricate) ──────
PLAINTIFF = "Andrew James Pigors"
PLAINTIFF_ADDRESS = "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445"
PLAINTIFF_PHONE = "(231) 903-5690"
PLAINTIFF_EMAIL = "andrewjpigors@gmail.com"
DEFENDANT = "Emily A. Watson"
DEFENDANT_ADDRESS = "2160 Garland Drive, Norton Shores, MI 49441"
CHILD_INITIALS = "L.D.W."
JUDGE = "Hon. Jenny L. McNeill"
COURT = "14th Circuit Court, Family Division, Muskegon County"
CASE_NO = "2024-001507-DC"
FOC = "Pamela Rusco"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH), timeout=60)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def safe_trunc(text, maxlen=300):
    if not text:
        return ""
    text = str(text).replace('\n', ' ').replace('\r', '').strip()
    return text[:maxlen] + "..." if len(text) > maxlen else text


def table_exists(conn, name):
    return conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()[0] > 0


# ── MCL 722.27a(3) elements for emergency custody ──────────────────────
MCL_722_27a_ELEMENTS = {
    "immediate_danger": {
        "statute": "MCL 722.27a(3)(a)",
        "text": "The child has a reasonable likelihood of being exposed to or affected by "
                "domestic violence, substance abuse, or has been removed from the parent "
                "having custody.",
        "db_categories": ["AGGRESSION", "MEDICAL", "PPO_ABUSE"],
    },
    "change_circumstances": {
        "statute": "MCL 722.27a(3)(b)",
        "text": "The child's present environment is likely to cause the child physical, "
                "mental, or emotional harm.",
        "db_categories": ["INTERFERENCE", "MEDICAL", "AGGRESSION"],
    },
    "best_interest": {
        "statute": "MCL 722.23 (Best Interest Factors)",
        "text": "The best interest factors must be considered: factor (j) willingness to "
                "facilitate relationship with other parent is particularly relevant.",
        "db_categories": ["INTERFERENCE", "GENERAL"],
    },
}


def query_emergency_events(conn):
    """Pull all emergency-relevant d_drive_events."""
    print("  [1/7] Querying d_drive_events for emergency categories...")
    results = {"MEDICAL": [], "AGGRESSION": [], "INTERFERENCE": [], "OTHER": []}
    try:
        rows = conn.execute("""
            SELECT id, source_doc, event_date, event_description, actors,
                   category, lane, severity
            FROM d_drive_events
            WHERE category IN ('MEDICAL', 'AGGRESSION', 'INTERFERENCE',
                               'PPO_ABUSE', 'FRAUD', 'POLICE')
            ORDER BY category, event_date
        """).fetchall()
        for r in rows:
            cat = r["category"]
            bucket = cat if cat in results else "OTHER"
            entry = {
                "id": r["id"],
                "date": r["event_date"],
                "description": safe_trunc(r["event_description"], 400),
                "actors": r["actors"],
                "category": cat,
                "severity": r["severity"],
            }
            results[bucket].append(entry)
        total = sum(len(v) for v in results.values())
        print(f"    MEDICAL={len(results['MEDICAL'])}, AGGRESSION={len(results['AGGRESSION'])}, "
              f"INTERFERENCE={len(results['INTERFERENCE'])}, OTHER={len(results['OTHER'])}")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_albert_watson_evidence(conn):
    """Pull all Albert Watson aggression evidence."""
    print("  [2/7] Querying Albert Watson aggression evidence...")
    results = []
    try:
        rows = conn.execute("""
            SELECT id, event_date, event_description, actors, category, severity
            FROM d_drive_events
            WHERE (actors LIKE '%Albert%' OR event_description LIKE '%Albert%')
            ORDER BY event_date
        """).fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "date": r["event_date"],
                "description": safe_trunc(r["event_description"], 400),
                "actors": r["actors"],
                "category": r["category"],
                "severity": r["severity"],
            })
        print(f"    Found {len(results)} Albert Watson events")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_healthwest_evidence(conn):
    """Pull HealthWest weaponization evidence."""
    print("  [3/7] Querying HealthWest evidence...")
    results = []
    try:
        rows = conn.execute("""
            SELECT id, document_id, page_number, quote_text, speaker,
                   date_ref, legal_significance, source_type
            FROM evidence_quotes
            WHERE quote_text LIKE '%HealthWest%'
               OR quote_text LIKE '%health west%'
               OR quote_text LIKE '%mental health%assessment%'
               OR quote_text LIKE '%evaluation%rule out%'
            LIMIT 50
        """).fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "text": safe_trunc(r["quote_text"], 400),
                "speaker": r["speaker"],
                "date": r["date_ref"],
                "significance": r["legal_significance"],
                "source_type": r["source_type"],
            })
        print(f"    Found {len(results)} HealthWest evidence items")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_medical_evidence(conn):
    """Pull medical events for the child."""
    print("  [4/7] Querying medical events for child...")
    results = []
    try:
        rows = conn.execute("""
            SELECT id, event_date, event_description, actors, severity
            FROM d_drive_events
            WHERE category = 'MEDICAL'
            ORDER BY event_date
        """).fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "date": r["event_date"],
                "description": safe_trunc(r["event_description"], 400),
                "actors": r["actors"],
                "severity": r["severity"],
            })
        print(f"    Found {len(results)} medical events")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_interference_evidence(conn):
    """Pull parenting time interference evidence."""
    print("  [5/7] Querying interference evidence...")
    results = []
    try:
        rows = conn.execute("""
            SELECT id, event_date, event_description, actors, severity
            FROM d_drive_events
            WHERE category = 'INTERFERENCE'
            ORDER BY event_date
        """).fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "date": r["event_date"],
                "description": safe_trunc(r["event_description"], 400),
                "actors": r["actors"],
                "severity": r["severity"],
            })
        print(f"    Found {len(results)} interference events")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_related_claims(conn):
    """Pull claims related to emergency custody issues."""
    print("  [6/7] Querying related claims...")
    results = []
    try:
        rows = conn.execute("""
            SELECT claim_id, issue_id, classification, actor, proposition,
                   evidence_targets, status
            FROM claims
            WHERE issue_id LIKE '%PARENTING%'
               OR issue_id LIKE '%CUSTODY%'
               OR issue_id LIKE '%EMERGENCY%'
               OR issue_id LIKE '%EX_PARTE%'
               OR classification LIKE '%custody%'
               OR proposition LIKE '%emergency%'
               OR proposition LIKE '%parenting time%'
            ORDER BY status DESC
        """).fetchall()
        for r in rows:
            results.append({
                "claim_id": r["claim_id"],
                "issue_id": r["issue_id"],
                "classification": r["classification"],
                "proposition": safe_trunc(r["proposition"], 250),
                "evidence_targets": r["evidence_targets"],
                "status": r["status"],
            })
        print(f"    Found {len(results)} related claims")
    except Exception as e:
        print(f"    Error: {e}")
    return results


def query_police_narratives(conn):
    """Pull police narrative documents (NS2505044)."""
    print("  [7/7] Querying police narratives...")
    results = []
    try:
        rows = conn.execute("""
            SELECT id, file_name, content_text, doc_type
            FROM d_drive_documents
            WHERE doc_type = 'POLICE_NARRATIVES'
               OR file_name LIKE '%POLICE%'
               OR file_name LIKE '%NS2505044%'
        """).fetchall()
        for r in rows:
            results.append({
                "id": r["id"],
                "file_name": r["file_name"],
                "content": safe_trunc(r["content_text"], 500),
                "doc_type": r["doc_type"],
            })
        print(f"    Found {len(results)} police narrative documents")
    except Exception as e:
        print(f"    Error: {e}")

    # Also search evidence_quotes for NS2505044
    try:
        rows = conn.execute("""
            SELECT id, quote_text, date_ref, source_type
            FROM evidence_quotes
            WHERE quote_text LIKE '%NS2505044%'
               OR quote_text LIKE '%Norton Shores%police%'
            LIMIT 10
        """).fetchall()
        for r in rows:
            results.append({
                "id": f"EQ-{r['id']}",
                "file_name": "evidence_quotes",
                "content": safe_trunc(r["quote_text"], 400),
                "doc_type": r["source_type"],
            })
        if rows:
            print(f"    + {len(rows)} police references in evidence_quotes")
    except Exception:
        pass
    return results


def deduplicate_events(events):
    """Deduplicate events by description similarity."""
    seen = set()
    unique = []
    for e in events:
        key = (e.get("description", "")[:80], e.get("date", ""))
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def build_fact_section(emergency_events, albert_evidence, healthwest,
                       medical, interference, police_narratives):
    """Build fact section from actual DB evidence — NO placeholders where data exists."""
    facts = []

    # Albert Watson aggression
    unique_albert = deduplicate_events(albert_evidence)
    if unique_albert:
        facts.append({
            "category": "PHYSICAL AGGRESSION — Albert Watson",
            "count": len(unique_albert),
            "key_facts": [],
        })
        for ae in unique_albert[:8]:
            facts[-1]["key_facts"].append({
                "date": ae["date"],
                "fact": ae["description"],
                "db_source": f"d_drive_events.id={ae['id']}",
            })

    # Medical harm
    unique_medical = deduplicate_events(medical)
    if unique_medical:
        facts.append({
            "category": "MEDICAL HARM / NEGLECT",
            "count": len(unique_medical),
            "key_facts": [],
        })
        for me in unique_medical[:8]:
            facts[-1]["key_facts"].append({
                "date": me["date"],
                "fact": me["description"],
                "db_source": f"d_drive_events.id={me['id']}",
            })

    # Interference / withholding
    unique_interf = deduplicate_events(interference)
    if unique_interf:
        facts.append({
            "category": "PARENTING TIME INTERFERENCE / WITHHOLDING",
            "count": len(unique_interf),
            "key_facts": [],
        })
        for ie in unique_interf[:8]:
            facts[-1]["key_facts"].append({
                "date": ie["date"],
                "fact": ie["description"],
                "db_source": f"d_drive_events.id={ie['id']}",
            })

    # HealthWest weaponization
    if healthwest:
        facts.append({
            "category": "HEALTHWEST EVALUATION WEAPONIZATION",
            "count": len(healthwest),
            "key_facts": [],
        })
        for hw in healthwest[:5]:
            facts[-1]["key_facts"].append({
                "date": hw.get("date", "N/A"),
                "fact": hw["text"],
                "db_source": f"evidence_quotes.id={hw['id']}",
            })

    # Police narratives
    if police_narratives:
        facts.append({
            "category": "POLICE REPORT EVIDENCE (NS2505044)",
            "count": len(police_narratives),
            "key_facts": [],
        })
        for pn in police_narratives[:3]:
            facts[-1]["key_facts"].append({
                "date": "N/A",
                "fact": pn["content"],
                "db_source": f"d_drive_documents.id={pn['id']}",
            })

    return facts


def build_affidavit_outline(facts, emergency_events):
    """Build affidavit outline from gathered facts."""
    outline = {
        "caption": {
            "court": COURT,
            "case_no": CASE_NO,
            "judge": JUDGE,
            "plaintiff": PLAINTIFF,
            "defendant": DEFENDANT,
        },
        "affiant": PLAINTIFF,
        "affiant_address": PLAINTIFF_ADDRESS,
        "sections": [],
    }

    # Section 1: Identity and standing
    outline["sections"].append({
        "number": 1,
        "text": f"I, {PLAINTIFF}, am the Plaintiff in the above-captioned matter and the "
                f"biological father of {CHILD_INITIALS}. I reside at {PLAINTIFF_ADDRESS}.",
    })

    # Section 2: Emergency basis
    agg_count = len(emergency_events.get("AGGRESSION", []))
    med_count = len(emergency_events.get("MEDICAL", []))
    int_count = len(emergency_events.get("INTERFERENCE", []))
    outline["sections"].append({
        "number": 2,
        "text": f"I bring this emergency motion because {CHILD_INITIALS} faces immediate risk "
                f"of harm. The record contains {agg_count} aggression incidents, "
                f"{med_count} medical events, and {int_count} interference incidents "
                f"documented in the evidence below.",
    })

    # Build fact paragraphs from DB evidence
    para_num = 3
    for fact_group in facts:
        for kf in fact_group["key_facts"][:4]:
            outline["sections"].append({
                "number": para_num,
                "text": f"On or about {kf['date']}, {kf['fact'][:300]} "
                        f"(Source: {kf['db_source']})",
            })
            para_num += 1

    # Concluding paragraph
    outline["sections"].append({
        "number": para_num,
        "text": f"Based on the foregoing facts, {CHILD_INITIALS}'s present environment poses "
                f"an immediate risk of physical, mental, or emotional harm. Emergency relief "
                f"is necessary to protect {CHILD_INITIALS}'s welfare.",
    })

    return outline


def main():
    ts = datetime.now()
    print("=" * 70)
    print("  TOOL #237 — EMERGENCY MOTION GENERATOR (F4)")
    print(f"  Pigors v. Watson | {ts.strftime('%Y-%m-%d %H:%M')}")
    print("=" * 70)

    conn = get_conn()

    # ── Gather all evidence ──
    emergency_events = query_emergency_events(conn)
    albert_evidence = query_albert_watson_evidence(conn)
    healthwest = query_healthwest_evidence(conn)
    medical = query_medical_evidence(conn)
    interference = query_interference_evidence(conn)
    related_claims = query_related_claims(conn)
    police_narratives = query_police_narratives(conn)

    conn.close()

    # ── Build outputs ──
    print("\n  Building fact section from DB evidence...")
    fact_section = build_fact_section(
        emergency_events, albert_evidence, healthwest,
        medical, interference, police_narratives
    )

    print("  Building affidavit outline...")
    affidavit = build_affidavit_outline(fact_section, emergency_events)

    # ── Deduplicated counts ──
    unique_agg = deduplicate_events(emergency_events.get("AGGRESSION", []))
    unique_med = deduplicate_events(emergency_events.get("MEDICAL", []))
    unique_int = deduplicate_events(emergency_events.get("INTERFERENCE", []))
    unique_albert = deduplicate_events(albert_evidence)

    # ── MCL 722.27a element mapping ──
    element_mapping = {}
    for key, elem in MCL_722_27a_ELEMENTS.items():
        matching = []
        for cat in elem["db_categories"]:
            matching.extend(emergency_events.get(cat, []))
        element_mapping[key] = {
            "statute": elem["statute"],
            "text": elem["text"],
            "evidence_count": len(matching),
            "sample_evidence": [safe_trunc(m["description"], 200) for m in matching[:5]],
        }

    # ── JSON output ──
    json_data = {
        "tool": "#237 — Emergency Motion Generator (F4)",
        "generated": ts.isoformat(),
        "case": f"Pigors v. Watson ({CASE_NO})",
        "court": COURT,
        "judge": JUDGE,
        "summary": {
            "aggression_events_raw": len(emergency_events.get("AGGRESSION", [])),
            "aggression_events_unique": len(unique_agg),
            "medical_events_raw": len(emergency_events.get("MEDICAL", [])),
            "medical_events_unique": len(unique_med),
            "interference_events_raw": len(emergency_events.get("INTERFERENCE", [])),
            "interference_events_unique": len(unique_int),
            "albert_watson_events": len(unique_albert),
            "healthwest_evidence": len(healthwest),
            "police_narratives": len(police_narratives),
            "related_claims": len(related_claims),
            "fact_section_categories": len(fact_section),
            "affidavit_paragraphs": len(affidavit["sections"]),
        },
        "mcl_722_27a_mapping": element_mapping,
        "fact_section": fact_section,
        "affidavit_outline": affidavit,
        "albert_watson_evidence": unique_albert[:20],
        "healthwest_evidence": healthwest[:20],
        "medical_evidence": unique_med[:20],
        "interference_evidence": unique_int[:20],
        "police_narratives": police_narratives[:5],
        "related_claims": related_claims[:20],
    }

    json_path = REPORTS_DIR / "tool_237_emergency_motion_generator.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, default=str, ensure_ascii=False)
    print(f"\n  JSON → {json_path}")

    # ── MD report / motion framework ──
    md_path = REPORTS_DIR / "tool_237_emergency_motion_generator.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Tool #237 — Emergency Motion Generator (F4)\n\n")
        f.write(f"**Generated:** {ts.strftime('%Y-%m-%d %H:%M')}  \n")
        f.write(f"**Case:** {CASE_NO} — Pigors v. Watson  \n")
        f.write(f"**Court:** {COURT}  \n")
        f.write(f"**Judge:** {JUDGE}  \n\n")

        f.write("---\n\n## EMERGENCY MOTION FRAMEWORK\n\n")
        f.write("### Caption\n\n")
        f.write(f"**STATE OF MICHIGAN — {COURT.upper()}**  \n\n")
        f.write(f"| | |\n|---|---|\n")
        f.write(f"| {PLAINTIFF}, Plaintiff | Case No. {CASE_NO} |\n")
        f.write(f"| v. | {JUDGE} |\n")
        f.write(f"| {DEFENDANT}, Defendant | |\n\n")
        f.write("**EMERGENCY MOTION FOR CHANGE OF CUSTODY / RESTORATION OF PARENTING TIME**\n\n")

        f.write("---\n\n### Evidence Summary\n\n")
        f.write("| Category | Raw Events | Unique Events |\n")
        f.write("|----------|-----------|---------------|\n")
        f.write(f"| Aggression | {len(emergency_events.get('AGGRESSION', []))} | {len(unique_agg)} |\n")
        f.write(f"| Medical | {len(emergency_events.get('MEDICAL', []))} | {len(unique_med)} |\n")
        f.write(f"| Interference | {len(emergency_events.get('INTERFERENCE', []))} | {len(unique_int)} |\n")
        f.write(f"| Albert Watson Events | {len(albert_evidence)} | {len(unique_albert)} |\n")
        f.write(f"| HealthWest Evidence | {len(healthwest)} | — |\n")
        f.write(f"| Police Narratives | {len(police_narratives)} | — |\n")
        f.write(f"| Related Claims | {len(related_claims)} | — |\n\n")

        # MCL 722.27a elements
        f.write("---\n\n### MCL 722.27a(3) Element Mapping\n\n")
        for key, elem in element_mapping.items():
            f.write(f"#### {elem['statute']}\n\n")
            f.write(f"**Requirement:** {elem['text']}  \n")
            f.write(f"**Supporting Evidence Count:** {elem['evidence_count']}  \n\n")
            if elem["sample_evidence"]:
                for i, se in enumerate(elem["sample_evidence"], 1):
                    f.write(f"{i}. {se}  \n")
                f.write("\n")

        # Fact section
        f.write("---\n\n### Statement of Facts (DB-Sourced)\n\n")
        for fg in fact_section:
            f.write(f"#### {fg['category']} ({fg['count']} unique events)\n\n")
            for i, kf in enumerate(fg["key_facts"], 1):
                f.write(f"**{i}.** On or about **{kf['date']}**:  \n")
                f.write(f"> {kf['fact']}  \n")
                f.write(f"*(DB: {kf['db_source']})*  \n\n")

        # Affidavit outline
        f.write("---\n\n### Affidavit Outline\n\n")
        f.write(f"**AFFIDAVIT OF {PLAINTIFF.upper()}**\n\n")
        f.write(f"STATE OF MICHIGAN )  \n")
        f.write(f"COUNTY OF MUSKEGON ) ss.  \n\n")
        f.write(f"I, {PLAINTIFF}, being first duly sworn, depose and state as follows:\n\n")
        for sec in affidavit["sections"]:
            f.write(f"**{sec['number']}.** {sec['text']}  \n\n")
        f.write(f"FURTHER AFFIANT SAYETH NOT.\n\n")
        f.write(f"_____________________________  \n")
        f.write(f"{PLAINTIFF}  \n")
        f.write(f"Date: _______________  \n\n")

        # Legal standards
        f.write("---\n\n### Legal Standards\n\n")
        f.write("**MCL 722.27a(3)** — Emergency custody modifications:\n")
        f.write("> The court may modify a custody or parenting time order if the court finds, "
                "on the basis of facts that have arisen since the prior order, or that were "
                "unknown to the court at the time of the prior order, that a change has "
                "occurred in the circumstances of the child or the child's custodian, and "
                "that the modification is in the best interest of the child.\n\n")
        f.write("**MCL 722.23** — Best Interest Factors:\n")
        f.write("> Factor (j): The willingness and ability of each of the parties to "
                "facilitate and encourage a close and continuing parent-child relationship "
                "between the child and the other parent.\n\n")
        f.write("**MCL 722.27(1)(c)** — Court powers:\n")
        f.write("> The court may modify or amend its previous judgments or orders for proper "
                "cause shown or because of change of circumstances.\n\n")

        # Albert Watson specific section
        if unique_albert:
            f.write("---\n\n### Albert Watson Aggression Evidence\n\n")
            f.write("Albert Watson (Emily's father) has engaged in documented physical "
                    "aggression during custody exchanges:\n\n")
            for i, ae in enumerate(unique_albert[:10], 1):
                f.write(f"**{i}.** [{ae['date']}] {ae['description']}  \n")
                f.write(f"*(Category: {ae['category']}, Severity: {ae['severity']}, "
                        f"DB: d_drive_events.id={ae['id']})*  \n\n")

        # HealthWest section
        if healthwest:
            f.write("---\n\n### HealthWest Evaluation Weaponization\n\n")
            f.write("Evidence that the HealthWest mental health evaluation was improperly "
                    "influenced by the court and FOC:\n\n")
            for i, hw in enumerate(healthwest[:8], 1):
                f.write(f"**{i}.** [{hw.get('date', 'N/A')}]  \n")
                f.write(f"> {hw['text']}  \n")
                f.write(f"*(DB: evidence_quotes.id={hw['id']})*  \n\n")

        # Filing recommendations
        f.write("---\n\n### Filing Recommendations\n\n")
        f.write("1. **Emergency Motion for Change of Custody** — File under MCL 722.27a(3) "
                "with supporting affidavit\n")
        f.write("2. **Request for Emergency Hearing** — MCR 3.207(A) for ex parte relief "
                "or expedited hearing\n")
        f.write("3. **Motion to Restore Parenting Time** — Vacate prior ex parte orders "
                "entered without due process\n")
        f.write("4. **Motion for Protective Order** — Against Albert Watson for documented "
                "aggression during exchanges\n")
        f.write("5. **Motion to Suppress HealthWest Evaluation** — Tainted by ex parte "
                "judicial interference\n\n")

        f.write("\n---\n*Generated by LitigationOS Tool #237*\n")

    print(f"  MD  → {md_path}")

    # ── Console summary ──
    print("\n" + "=" * 70)
    print("  EMERGENCY MOTION GENERATOR RESULTS")
    print("=" * 70)
    print(f"  Aggression events (unique):    {len(unique_agg)}")
    print(f"  Medical events (unique):       {len(unique_med)}")
    print(f"  Interference events (unique):  {len(unique_int)}")
    print(f"  Albert Watson events (unique): {len(unique_albert)}")
    print(f"  HealthWest evidence:           {len(healthwest)}")
    print(f"  Police narratives:             {len(police_narratives)}")
    print(f"  Fact section categories:       {len(fact_section)}")
    print(f"  Affidavit paragraphs:          {len(affidavit['sections'])}")
    print(f"  MCL 722.27a elements mapped:   {len(element_mapping)}")
    for key, elem in element_mapping.items():
        print(f"    {elem['statute']}: {elem['evidence_count']} supporting events")
    print("=" * 70)
    print("  COMPLETE")


if __name__ == "__main__":
    main()
