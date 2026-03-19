"""
APEX Ω∞ — Deposition Preparation Engine
==========================================
Generates targeted deposition outlines for each adversary witness.
Cross-references perjury_detector findings + witness credibility scores
to identify optimal questioning sequences that expose contradictions.
"""
import sys, sqlite3, json, time
from pathlib import Path
from datetime import datetime

_shared = Path(__file__).parent.parent / "shared"
if str(_shared) not in sys.path:
    sys.path.insert(0, str(_shared))
from autonomos_config import CENTRAL_DB

DEPO_DB = Path(__file__).parent / "deposition_prep.db"

DEPOSITION_TARGETS = {
    "emily_watson": {
        "name": "Emily A. Watson",
        "role": "Defendant / Mother",
        "priority": 1,
        "topic_areas": [
            {"topic": "Parenting Time Denial", "goal": "Establish pattern of denying Father access",
             "db_search": ["parenting time", "denied", "visitation", "custody exchange"]},
            {"topic": "Ex Parte Communications", "goal": "Expose unauthorized contact with court/FOC",
             "db_search": ["ex parte", "communication", "contact", "without notice"]},
            {"topic": "Financial Concealment", "goal": "Establish unreported income/assets",
             "db_search": ["income", "financial", "employment", "bank account"]},
            {"topic": "Watson Family Coordination", "goal": "Prove coordinated harassment campaign",
             "db_search": ["albert watson", "cody watson", "lori watson", "family"]},
            {"topic": "Child's Statements", "goal": "Document child's desire to see Father",
             "db_search": ["child said", "lincoln", "wants to see", "misses"]},
            {"topic": "Prior Sworn Statements", "goal": "Lock in prior testimony for impeachment",
             "db_search": ["sworn", "testified", "stated under oath", "affidavit"]},
        ],
    },
    "albert_watson": {
        "name": "Albert Watson",
        "role": "Defendant's Father",
        "priority": 2,
        "topic_areas": [
            {"topic": "Physical Confrontations", "goal": "Document throwing papers, removing child",
             "db_search": ["threw", "papers", "car window", "removed", "forcibly"]},
            {"topic": "Custody Exchange Interference", "goal": "Establish pattern of interference",
             "db_search": ["exchange", "interfere", "present at", "custody"]},
            {"topic": "Coordination with Emily", "goal": "Prove planned interference",
             "db_search": ["coordinated", "planned", "instructed", "told to"]},
        ],
    },
    "pamela_rusco": {
        "name": "Pamela Rusco",
        "role": "Friend of the Court",
        "priority": 3,
        "topic_areas": [
            {"topic": "Investigation Methodology", "goal": "Expose incomplete/biased investigation",
             "db_search": ["investigation", "interviewed", "reviewed", "considered"]},
            {"topic": "Ex Parte Information", "goal": "Establish unauthorized information flow",
             "db_search": ["ex parte", "information", "contact", "without both parties"]},
            {"topic": "Recommendation Basis", "goal": "Challenge factual basis of recommendations",
             "db_search": ["recommendation", "basis", "evidence considered", "findings"]},
            {"topic": "Document Review", "goal": "Determine which evidence was actually reviewed",
             "db_search": ["reviewed documents", "evidence", "file review", "records"]},
        ],
    },
    "ron_berry": {
        "name": "Ron Berry",
        "role": "Former Guardian Ad Litem / Attorney",
        "priority": 2,
        "topic_areas": [
            {"topic": "Voicemail Coordination", "goal": "Establish timing and content of coordination",
             "db_search": ["voicemail", "berry", "phone call", "message"]},
            {"topic": "Relationship with Watson", "goal": "Prove improper attorney-party relationship",
             "db_search": ["berry", "watson", "meeting", "contact", "hired"]},
            {"topic": "Filings Timeline", "goal": "Show filings within 48hrs of McNeill orders",
             "db_search": ["filed within", "same day", "48 hours", "timing"]},
        ],
    },
    "mandi_martini": {
        "name": "Mandi Martini",
        "role": "Court Staff / Clerk",
        "priority": 4,
        "topic_areas": [
            {"topic": "Bad Mood Warning", "goal": "Document 'judge is in a bad mood' statement",
             "db_search": ["bad mood", "don't say", "martini", "warned"]},
            {"topic": "Courtroom Procedures", "goal": "Establish irregular courtroom procedures",
             "db_search": ["procedure", "courtroom", "hearing", "notice"]},
        ],
    },
}

def _init_db() -> sqlite3.Connection:
    DEPO_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DEPO_DB), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS depo_outlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            deponent TEXT NOT NULL,
            topic TEXT NOT NULL,
            goal TEXT NOT NULL,
            evidence_count INTEGER DEFAULT 0,
            question_count INTEGER DEFAULT 0,
            questions_json TEXT DEFAULT '[]',
            generated_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    return conn

def prepare_depositions(target: str = None) -> dict:
    """Generate deposition preparation outlines."""
    start = time.time()
    ddb = _init_db()
    results = []
    targets = {target: DEPOSITION_TARGETS[target]} if target and target in DEPOSITION_TARGETS else DEPOSITION_TARGETS

    try:
        cdb = sqlite3.connect(str(CENTRAL_DB), timeout=30)
        cdb.execute("PRAGMA query_only=ON")

        for tid, tgt in targets.items():
            deponent_result = {
                "target": tid, "name": tgt["name"], "role": tgt["role"],
                "priority": tgt["priority"], "topics": [],
            }

            for topic in tgt["topic_areas"]:
                evidence_count = 0
                sample_quotes = []

                for term in topic["db_search"]:
                    try:
                        rows = cdb.execute("""
                            SELECT quote_text FROM evidence_quotes
                            WHERE LOWER(COALESCE(quote_text,'')) LIKE ?
                            LIMIT 5
                        """, (f"%{term}%",)).fetchall()
                        evidence_count += len(rows)
                        for r in rows[:2]:
                            q = str(r[0])[:200]
                            if q not in sample_quotes:
                                sample_quotes.append(q)
                    except Exception:
                        pass

                    try:
                        rows = cdb.execute("""
                            SELECT COUNT(*) FROM contradiction_map
                            WHERE LOWER(COALESCE(statement_1,'') || COALESCE(statement_2,''))
                            LIKE ?
                        """, (f"%{term}%",)).fetchone()[0]
                        evidence_count += rows
                    except Exception:
                        pass

                # Generate questions based on evidence
                questions = []
                questions.append(f"Please state your full name and relationship to this case.")
                questions.append(f"Regarding {topic['topic'].lower()}: {topic['goal']}.")
                if sample_quotes:
                    questions.append(f"I'd like to direct your attention to the following: '{sample_quotes[0][:100]}...' — is this accurate?")
                questions.append(f"Are there any documents or records that would contradict your testimony on this topic?")

                ddb.execute("""
                    INSERT INTO depo_outlines
                    (deponent, topic, goal, evidence_count, question_count, questions_json)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (tgt["name"], topic["topic"], topic["goal"],
                      evidence_count, len(questions), json.dumps(questions)))

                deponent_result["topics"].append({
                    "topic": topic["topic"], "goal": topic["goal"],
                    "evidence_count": evidence_count,
                    "sample_quotes": sample_quotes[:3],
                    "questions": questions,
                })

            deponent_result["total_evidence"] = sum(t["evidence_count"] for t in deponent_result["topics"])
            results.append(deponent_result)

        cdb.close()
    except Exception as e:
        results.append({"error": str(e)})

    ddb.commit()
    ddb.close()

    ranked = sorted(results, key=lambda x: x.get("priority", 99))
    return {
        "deponents_prepared": len(results),
        "total_topics": sum(len(r.get("topics", [])) for r in results),
        "results": ranked,
        "duration_s": round(time.time() - start, 2),
    }

if __name__ == "__main__":
    tgt = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(prepare_depositions(tgt), indent=2, default=str))
