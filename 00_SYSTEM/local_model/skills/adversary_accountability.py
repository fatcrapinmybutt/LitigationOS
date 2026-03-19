"""
Skill: adversary_accountability
Maps each adversary to their specific harms, legal theories, and filing stacks.
Ensures no adversary escapes accountability.

ADVERSARY PROFILES:
  WATSON TRACK (01_ADVERSARY_WATSON):
    Emily Watson — Primary antagonist: PPO weaponization, parental alienation, 
      false allegations, conspiracy with Berry/McNeill
    Albert Watson — Intimidation: Oct 20 2024 incident, threw papers, removed child
    Cody Watson — Road harassment Sep/Oct 2024
    Lori Watson — Conspiracy participant
    Judge McNeill — 1,127 judicial violations, 24 ex parte orders, muting, $250 bond
    Ron Berry — Ex parte voicemail, coordination pattern, MRPC violations
    Pamela Rusco — Potential ex parte information flow
    Mandi Martini — "Do not say a word" instruction, ineffective assistance

  HOUSING TRACK (01_ADVERSARY_HOUSING):
    Shady Oaks — 4,580 harms: habitability, retaliation, fraud
    Homes of America — 211 harms: corporate parent liability
    Alden Global — 199 harms: private equity predatory practices
"""
import sqlite3

SKILL_NAME = "adversary_accountability"
SKILL_VERSION = "1.0.0"
DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

# Complete adversary → legal theory → filing stack mapping
ACCOUNTABILITY_MAP = {
    "Emily Watson": {
        "legal_theories": [
            "Civil Conspiracy (MCL 600.2910; Halberstam v. Welch)",
            "Intentional Infliction of Emotional Distress (Roberts v. Auto-Owners)",
            "Abuse of Process (Friedman v. Dozorc) — PPO as custody weapon",
            "Tortious Interference with Parental Relationship (Hashem v. Les Stanford)",
            "Malicious Prosecution (Show Cause #3 dismissed)",
            "Parental Alienation (MCL 722.23(j) Factor J)",
            "Contempt (MCR 3.606) — willful PT violations"
        ],
        "filing_stacks": [1, 5, 6, 7, 10, 11, 13, 21, 24],
        "harm_categories": ["PARENTAL_ALIENATION", "PPO_WEAPONIZATION", "FALSE_IMPRISONMENT",
                          "CONSPIRACY_COORDINATION", "CHILD_WELFARE", "EMOTIONAL_PSYCHOLOGICAL"],
        "relief_sought": [
            "Immediate restoration of Father's parenting time",
            "Sole legal custody to Father or joint custody",
            "Compensatory damages ($260K-$1.69M)",
            "Punitive damages",
            "Contempt sanctions (jail/fine for PT withholding)",
            "Vacatur of all orders based on her false allegations"
        ]
    },
    "Judge McNeill": {
        "legal_theories": [
            "JTC Complaint (MCR 9.200) — 9 counts of judicial misconduct",
            "MSC Superintending Control (MCR 7.306; Const art 6 § 4)",
            "MSC Mandamus (MCR 7.306(B)(2))",
            "MSC Prohibition (MCR 7.306(B)(3))",
            "42 USC § 1983 — judicial immunity waived for non-judicial acts",
            "Disqualification (MCR 2.003(C))"
        ],
        "filing_stacks": [1, 2, 3, 4, 5, 9, 11, 14, 23],
        "harm_categories": ["JUDICIAL_BIAS", "EX_PARTE_ABUSE", "PROCEDURAL_VIOLATIONS",
                          "FALSE_IMPRISONMENT", "CONSPIRACY_COORDINATION"],
        "relief_sought": [
            "Removal from bench (JTC)",
            "Vacatur of ALL 24 ex parte orders",
            "Vacatur of $250 filing bond",
            "Reassignment to different judge",
            "Prohibition from further action",
            "§1983 damages if immunity waived"
        ]
    },
    "Ron Berry": {
        "legal_theories": [
            "MRPC 3.5(b) — Ex parte communication with tribunal",
            "MRPC 8.4(c) — Conduct involving dishonesty",
            "MRPC 3.4(a) — Obstructing access to evidence",
            "Civil Conspiracy (Dennis v. Sparks — private party + judge)"
        ],
        "filing_stacks": [1, 5, 11, 19],
        "harm_categories": ["ATTORNEY_MISCONDUCT", "CONSPIRACY_COORDINATION", "EX_PARTE_ABUSE"],
        "relief_sought": [
            "AGC disciplinary action / disbarment",
            "§1983 damages (no judicial immunity for attorneys)",
            "Sanctions"
        ]
    },
    "Albert Watson": {
        "legal_theories": [
            "Assault/Battery (threw papers, forcibly removed child)",
            "Tortious Interference with Parental Relationship",
            "Intimidation"
        ],
        "filing_stacks": [1, 13, 21],
        "harm_categories": ["WATSON_FAMILY_INTIMIDATION"],
        "relief_sought": ["Compensatory damages", "Restraining order", "Criminal referral"]
    },
    "Cody Watson": {
        "legal_theories": [
            "Harassment (road incidents Sep/Oct 2024)",
            "Tortious Interference",
            "Intimidation"
        ],
        "filing_stacks": [1, 21],
        "harm_categories": ["WATSON_FAMILY_INTIMIDATION"],
        "relief_sought": ["Compensatory damages", "Restraining order"]
    },
    "Shady Oaks": {
        "legal_theories": [
            "MCL 554.139 — Covenant of habitability",
            "MCL 600.5720 — Retaliatory eviction",
            "Consumer fraud (MCPA MCL 445.901)",
            "Negligence / Gross negligence",
            "Breach of lease / Constructive eviction",
            "Fair Housing Act (42 USC 3601) if discrimination"
        ],
        "filing_stacks": ["housing_stack"],
        "harm_categories": ["HOUSING_HARM", "FINANCIAL_HARM", "EMOTIONAL_PSYCHOLOGICAL"],
        "relief_sought": [
            "Compensatory damages (displacement, deposits, moving costs)",
            "Treble damages under MCPA",
            "Injunctive relief (repairs, habitability compliance)",
            "Attorney fees / costs"
        ]
    },
    "Homes of America": {
        "legal_theories": [
            "Respondeat superior (corporate parent of Shady Oaks)",
            "Direct liability for management policies",
            "Consumer fraud (pattern and practice)"
        ],
        "filing_stacks": ["housing_stack"],
        "harm_categories": ["HOUSING_HARM", "FINANCIAL_HARM"],
        "relief_sought": ["Vicarious liability damages", "Policy reform injunction"]
    },
    "Alden Global": {
        "legal_theories": [
            "Corporate veil piercing (alter ego doctrine)",
            "Private equity liability for portfolio company conduct",
            "Unjust enrichment"
        ],
        "filing_stacks": ["housing_stack"],
        "harm_categories": ["HOUSING_HARM", "FINANCIAL_HARM"],
        "relief_sought": ["Piercing corporate veil", "Damages", "Injunction"]
    }
}

def get_accountability(adversary: str) -> dict:
    """Get complete accountability profile for an adversary."""
    if adversary in ACCOUNTABILITY_MAP:
        profile = ACCOUNTABILITY_MAP[adversary]
        # Also query DB for harm counts
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*), AVG(severity) FROM extracted_harms WHERE adversary LIKE ?",
                    (f"%{adversary}%",))
        row = cur.fetchone()
        profile["db_harm_count"] = row[0]
        profile["db_avg_severity"] = round(row[1], 1) if row[1] else 0
        conn.close()
        return profile
    return {"error": f"No profile for {adversary}"}

def all_adversaries() -> dict:
    """List all adversaries with harm counts."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""SELECT adversary, COUNT(*), AVG(severity), MAX(severity)
                   FROM extracted_harms GROUP BY adversary ORDER BY COUNT(*) DESC""")
    results = [{"adversary": r[0], "harm_count": r[1], 
                "avg_severity": round(r[2], 1), "max_severity": r[3]} for r in cur.fetchall()]
    conn.close()
    return {"adversaries": results}

METHODS = {
    "get_accountability": get_accountability,
    "all_adversaries": all_adversaries,
}
