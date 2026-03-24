#!/usr/bin/env python3
"""
build_court_forms_db.py — Rebuild court_forms.db with Michigan SCAO form data + FTS5
====================================================================================
Creates the court_forms.db SQLite database with:
- forms, form_fields, form_requirements tables
- FTS5 search on forms
- Key Michigan SCAO forms pre-populated
"""

import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace', closefd=False)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "databases" / "court_forms.db"


def build():
    # Remove empty file if exists
    if DB_PATH.exists() and os.path.getsize(str(DB_PATH)) == 0:
        os.remove(str(DB_PATH))

    conn = sqlite3.connect(str(DB_PATH))

    # Tier-2 PRAGMAs
    conn.execute("PRAGMA busy_timeout = 60000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA cache_size = -32000")
    conn.execute("PRAGMA temp_store = MEMORY")
    conn.execute("PRAGMA synchronous = NORMAL")

    # Create tables
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS forms (
            form_id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_number TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            category TEXT,
            court_level TEXT,
            url TEXT,
            instructions TEXT,
            last_updated TEXT
        );

        CREATE TABLE IF NOT EXISTS form_fields (
            field_id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_id INTEGER NOT NULL,
            field_name TEXT NOT NULL,
            field_type TEXT DEFAULT 'text',
            required INTEGER DEFAULT 0,
            description TEXT,
            FOREIGN KEY (form_id) REFERENCES forms(form_id)
        );

        CREATE TABLE IF NOT EXISTS form_requirements (
            req_id INTEGER PRIMARY KEY AUTOINCREMENT,
            form_id INTEGER NOT NULL,
            requirement_text TEXT NOT NULL,
            mcr_reference TEXT,
            FOREIGN KEY (form_id) REFERENCES forms(form_id)
        );

        CREATE INDEX IF NOT EXISTS idx_forms_number ON forms(form_number);
        CREATE INDEX IF NOT EXISTS idx_forms_category ON forms(category);
        CREATE INDEX IF NOT EXISTS idx_forms_court_level ON forms(court_level);
        CREATE INDEX IF NOT EXISTS idx_form_fields_form ON form_fields(form_id);
        CREATE INDEX IF NOT EXISTS idx_form_requirements_form ON form_requirements(form_id);
    """)

    # FTS5 search
    conn.execute("DROP TABLE IF EXISTS forms_fts")
    conn.execute("""
        CREATE VIRTUAL TABLE forms_fts USING fts5(
            title,
            instructions,
            content=forms,
            content_rowid=form_id
        )
    """)

    # Triggers to keep FTS in sync
    conn.executescript("""
        CREATE TRIGGER IF NOT EXISTS forms_ai AFTER INSERT ON forms BEGIN
            INSERT INTO forms_fts(rowid, title, instructions)
            VALUES (new.form_id, new.title, new.instructions);
        END;

        CREATE TRIGGER IF NOT EXISTS forms_ad AFTER DELETE ON forms BEGIN
            INSERT INTO forms_fts(forms_fts, rowid, title, instructions)
            VALUES ('delete', old.form_id, old.title, old.instructions);
        END;

        CREATE TRIGGER IF NOT EXISTS forms_au AFTER UPDATE ON forms BEGIN
            INSERT INTO forms_fts(forms_fts, rowid, title, instructions)
            VALUES ('delete', old.form_id, old.title, old.instructions);
            INSERT INTO forms_fts(rowid, title, instructions)
            VALUES (new.form_id, new.title, new.instructions);
        END;
    """)

    now = datetime.now().isoformat()

    # Michigan SCAO forms data
    forms_data = [
        ("MC 12", "Proof of Service", "Service", "All Courts",
         "https://courts.michigan.gov/siteassets/forms/scao/mc12.pdf",
         "Used to document proof of service of court papers on opposing party. Must include method of service, date, time, and person served. Required for all filings requiring service under MCR 2.105.", now),

        ("MC 01", "Case Inventory Addendum", "Administrative", "All Courts",
         "https://courts.michigan.gov/siteassets/forms/scao/mc01.pdf",
         "Lists all pending and recently disposed cases involving the same parties. Required under MCR 2.113(C)(2)(b) to identify related cases.", now),

        ("FOC 10", "Uniform Child Support Order", "Family/Support", "Circuit Court — Family Division",
         "https://courts.michigan.gov/siteassets/forms/scao/foc10.pdf",
         "Standard order for child support obligations. Includes base support, medical, childcare. Required per MCL 552.517. Must comply with Michigan Child Support Formula.", now),

        ("FOC 89", "Friend of the Court Memorandum", "Family/FOC", "Circuit Court — Family Division",
         "https://courts.michigan.gov/siteassets/forms/scao/foc89.pdf",
         "FOC recommendation memo to court regarding custody, parenting time, or support. Filed by FOC staff after investigation. Parties may object within 21 days per MCR 3.218.", now),

        ("CC 375", "Motion and Verification for Alternate Service", "Service/Motion", "Circuit Court",
         "https://courts.michigan.gov/siteassets/forms/scao/cc375.pdf",
         "Motion requesting alternate service when personal service cannot be made. Must show diligent attempts per MCR 2.105(J). Requires affidavit of process server attempts.", now),

        ("DC 100a", "Complaint for Divorce (with children)", "Divorce", "Circuit Court — Family Division",
         "https://courts.michigan.gov/siteassets/forms/scao/dc100a.pdf",
         "Initiating complaint for divorce where minor children are involved. Must state residency, grounds, and requested relief. Filed per MCL 552.6 et seq. Requires UCCJEA affidavit.", now),

        ("DC 100b", "Complaint for Divorce (no children)", "Divorce", "Circuit Court — Family Division",
         "https://courts.michigan.gov/siteassets/forms/scao/dc100b.pdf",
         "Initiating complaint for divorce where no minor children are involved. Must state residency requirements (180 days state, 10 days county). Filed per MCL 552.6 et seq.", now),

        ("PPO 01", "Petition for Personal Protection Order (Domestic Relationship)", "PPO", "Circuit Court",
         "https://courts.michigan.gov/siteassets/forms/scao/cc375.pdf",
         "Petition for PPO based on domestic relationship. Must allege specific acts per MCL 600.2950. Includes stalking, assault, threats, property damage. Ex parte issuance available.", now),

        ("PPO 02", "Personal Protection Order (Domestic Relationship)", "PPO", "Circuit Court",
         "https://courts.michigan.gov/siteassets/forms/scao/ppo02.pdf",
         "The actual PPO order form issued by the court. Lists prohibited conduct, protected persons, and duration. Effective upon signing; enforceable upon service or respondent notice.", now),

        ("PPO 03", "Motion to Terminate or Modify PPO", "PPO", "Circuit Court",
         "https://courts.michigan.gov/siteassets/forms/scao/ppo03.pdf",
         "Motion to modify or terminate an existing PPO. Must state grounds. Respondent has right to hearing per MCL 600.2950(12). Must be served on petitioner.", now),

        ("PPO 04", "Petition for PPO (Non-Domestic Stalking)", "PPO", "Circuit Court",
         "https://courts.michigan.gov/siteassets/forms/scao/ppo04.pdf",
         "Petition for PPO based on non-domestic stalking. Must allege pattern of unconsented contact causing fear per MCL 600.2950a. Two or more acts required.", now),

        ("PPO 05", "Motion to Show Cause for Violation of PPO", "PPO/Contempt", "Circuit Court",
         "https://courts.michigan.gov/siteassets/forms/scao/ppo05.pdf",
         "Motion alleging violation of PPO. Can result in criminal contempt under MCL 600.2950(23). Must specify exact provision violated and factual basis.", now),

        ("COA Claim", "Claim of Appeal", "Appellate", "Court of Appeals",
         "https://courts.michigan.gov/siteassets/forms/coa/claim-of-appeal.pdf",
         "Initiates appeal of right in Michigan Court of Appeals. Must be filed within 21 days of final order per MCR 7.204(A)(1). Requires $375 filing fee or fee waiver. Must include proof of service on all parties.", now),

        ("COA Leave", "Application for Leave to Appeal", "Appellate", "Court of Appeals",
         "https://courts.michigan.gov/siteassets/forms/coa/application-for-leave.pdf",
         "Application for discretionary review by Court of Appeals. Must be filed within 21 days of order per MCR 7.205(A). Must state why leave should be granted. Standard: issue of significant public interest or palpable error.", now),

        ("PC 625", "Affidavit (General)", "General", "All Courts",
         "https://courts.michigan.gov/siteassets/forms/scao/pc625.pdf",
         "General affidavit form for sworn statements under oath. Used for factual assertions supporting motions, petitions, and complaints. Must be signed before notary or court clerk. Perjury penalties apply per MCL 750.423.", now),

        ("MC 20", "Fee Waiver Request", "Administrative", "All Courts",
         "https://courts.michigan.gov/siteassets/forms/scao/mc20.pdf",
         "Request for waiver of court filing fees based on inability to pay. Must show income below 125% of federal poverty guidelines or receipt of public assistance. Per MCR 2.002.", now),

        ("FOC 67", "Objection to Referee Recommendation", "Family/FOC", "Circuit Court — Family Division",
         "https://courts.michigan.gov/siteassets/forms/scao/foc67.pdf",
         "Objection to FOC referee recommendation. Must be filed within 21 days of recommendation per MCR 3.218(D). Entitles party to de novo hearing before judge.", now),

        ("MC 15", "Motion/Stipulation to Adjourn", "Administrative", "All Courts",
         "https://courts.michigan.gov/siteassets/forms/scao/mc15.pdf",
         "Motion to adjourn (postpone) a scheduled hearing. Must state good cause per MCR 2.503. Opposing party consent noted. Judge approval required.", now),

        ("DC 111", "Answer to Complaint for Divorce", "Divorce", "Circuit Court — Family Division",
         "https://courts.michigan.gov/siteassets/forms/scao/dc111.pdf",
         "Response to divorce complaint. Must be filed within 21 days of service (28 days if served by mail/outside Michigan) per MCR 2.108. May include counterclaim.", now),

        ("MC 11", "Order/Stipulation to Adjourn", "Administrative", "All Courts",
         "https://courts.michigan.gov/siteassets/forms/scao/mc11.pdf",
         "Court order granting or denying adjournment. Signed by judge. States new date if granted or reason if denied.", now),

        ("FOC 100", "Motion Regarding Support", "Family/Support", "Circuit Court — Family Division",
         "https://courts.michigan.gov/siteassets/forms/scao/foc100.pdf",
         "Motion to establish, modify, or enforce child support orders. Must show change of circumstances for modification per MCL 552.517. Must include verified statement of income.", now),

        ("FOC 65", "Motion Regarding Parenting Time", "Family/Custody", "Circuit Court — Family Division",
         "https://courts.michigan.gov/siteassets/forms/scao/foc65.pdf",
         "Motion to establish, modify, or enforce parenting time. Must allege proper cause or change of circumstances per MCL 722.27. Best interests of child standard applies.", now),

        ("MC 231", "Subpoena", "Discovery", "All Courts",
         "https://courts.michigan.gov/siteassets/forms/scao/mc231.pdf",
         "Subpoena for witness attendance or document production. Issued under MCR 2.506. Must be served per MCR 2.105. Witness fees and mileage required per MCL 600.1875.", now),

        ("MC 255", "Verified Statement — Fee Waiver", "Administrative", "All Courts",
         "https://courts.michigan.gov/siteassets/forms/scao/mc255.pdf",
         "Verified statement of financial information supporting fee waiver request (MC 20). Lists income, assets, expenses, dependents.", now),

        ("TF 01", "UCCJEA Affidavit", "Family/Custody", "Circuit Court — Family Division",
         "https://courts.michigan.gov/siteassets/forms/scao/tf01.pdf",
         "Uniform Child Custody Jurisdiction and Enforcement Act affidavit. Required in all custody proceedings per MCL 722.1209. Lists child residences for past 5 years.", now),
    ]

    conn.executemany("""
        INSERT OR IGNORE INTO forms (form_number, title, category, court_level, url, instructions, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, forms_data)

    # Basic form fields for key forms
    fields_data = []
    # Get form_ids
    form_map = {}
    for row in conn.execute("SELECT form_id, form_number FROM forms").fetchall():
        form_map[row[1]] = row[0]

    common_fields = [
        ("Case Number", "text", 1, "Court case number"),
        ("Court Name", "text", 1, "Name of the court"),
        ("County", "text", 1, "County where case is filed"),
        ("Plaintiff/Petitioner", "text", 1, "Name of plaintiff or petitioner"),
        ("Defendant/Respondent", "text", 1, "Name of defendant or respondent"),
        ("Date", "date", 1, "Date of filing"),
    ]

    for form_num, form_id in form_map.items():
        for fname, ftype, req, desc in common_fields:
            fields_data.append((form_id, fname, ftype, req, desc))

    # PPO-specific fields
    if "PPO 01" in form_map:
        ppo_id = form_map["PPO 01"]
        for fname, ftype, req, desc in [
            ("Relationship to Respondent", "select", 1, "Domestic relationship type"),
            ("Specific Acts Alleged", "textarea", 1, "Description of acts warranting PPO"),
            ("Requested Prohibitions", "checkbox_group", 1, "Specific conduct to prohibit"),
            ("Minor Children", "text", 0, "Children affected by PPO"),
        ]:
            fields_data.append((ppo_id, fname, ftype, req, desc))

    # MC 12 specific fields
    if "MC 12" in form_map:
        mc12_id = form_map["MC 12"]
        for fname, ftype, req, desc in [
            ("Method of Service", "select", 1, "Personal, mail, alternate, etc."),
            ("Person Served", "text", 1, "Name of person served"),
            ("Date of Service", "date", 1, "Date service was completed"),
            ("Time of Service", "time", 0, "Time service was completed"),
            ("Server Name", "text", 1, "Name of person who served papers"),
        ]:
            fields_data.append((mc12_id, fname, ftype, req, desc))

    conn.executemany("""
        INSERT INTO form_fields (form_id, field_name, field_type, required, description)
        VALUES (?, ?, ?, ?, ?)
    """, fields_data)

    # Form requirements (MCR references)
    requirements_data = []
    mcr_refs = {
        "MC 12": [
            ("Must be signed by server under oath or penalty of perjury", "MCR 2.104"),
            ("Service must comply with Michigan Court Rules on method", "MCR 2.105"),
            ("Must state date, time, place, and manner of service", "MCR 2.104(A)(2)"),
        ],
        "FOC 10": [
            ("Must comply with Michigan Child Support Formula", "MCR 3.211"),
            ("Income must be verified with supporting documentation", "MCL 552.517"),
            ("Medical support obligation must be addressed", "MCL 552.517b"),
        ],
        "PPO 01": [
            ("Must allege specific acts constituting domestic violence", "MCL 600.2950(1)"),
            ("Must show immediate and irreparable harm", "MCL 600.2950(4)"),
            ("Petitioner must have domestic relationship with respondent", "MCL 600.2950(1)"),
        ],
        "COA Claim": [
            ("Must be filed within 21 days of entry of final order", "MCR 7.204(A)(1)"),
            ("Must include proof of service on all parties", "MCR 7.204(B)"),
            ("Filing fee of $375 or fee waiver required", "MCR 7.204(B)"),
            ("Must include certified copy of judgment or order appealed", "MCR 7.204(C)"),
        ],
        "COA Leave": [
            ("Must be filed within 21 days of entry of order", "MCR 7.205(A)"),
            ("Must state reasons leave should be granted", "MCR 7.205(B)(3)"),
            ("Must include copy of order and relevant transcripts", "MCR 7.205(B)"),
        ],
        "PC 625": [
            ("Must be sworn before notary public or court clerk", "MCR 1.109(D)(3)"),
            ("Must be based on personal knowledge unless stated otherwise", "MRE 602"),
            ("False statements subject to perjury penalties", "MCL 750.423"),
        ],
        "DC 100a": [
            ("Plaintiff must be Michigan resident for 180 days", "MCL 552.9"),
            ("Must include UCCJEA affidavit when children involved", "MCL 722.1209"),
            ("Must state grounds for divorce", "MCL 552.6"),
        ],
        "FOC 65": [
            ("Must show proper cause or change of circumstances", "MCL 722.27"),
            ("Best interests of child factors must be considered", "MCL 722.23"),
            ("Must be served on opposing party", "MCR 3.206(C)"),
        ],
        "FOC 67": [
            ("Must be filed within 21 days of referee recommendation", "MCR 3.218(D)"),
            ("Entitles party to de novo hearing before judge", "MCR 3.218(D)"),
        ],
        "MC 231": [
            ("Must be served per court rules", "MCR 2.506"),
            ("Witness fees and mileage required", "MCL 600.1875"),
            ("Reasonable time for compliance required", "MCR 2.506(D)"),
        ],
    }

    for form_num, reqs in mcr_refs.items():
        if form_num in form_map:
            fid = form_map[form_num]
            for req_text, mcr_ref in reqs:
                requirements_data.append((fid, req_text, mcr_ref))

    conn.executemany("""
        INSERT INTO form_requirements (form_id, requirement_text, mcr_reference)
        VALUES (?, ?, ?)
    """, requirements_data)

    conn.commit()

    # Verify
    counts = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM forms) AS form_count,
            (SELECT COUNT(*) FROM form_fields) AS field_count,
            (SELECT COUNT(*) FROM form_requirements) AS req_count
    """).fetchone()

    conn.close()
    return counts


if __name__ == "__main__":
    print(f"Building court_forms.db at: {DB_PATH}")
    counts = build()
    print(f"  Forms: {counts[0]}")
    print(f"  Fields: {counts[1]}")
    print(f"  Requirements: {counts[2]}")
    size_kb = os.path.getsize(str(DB_PATH)) // 1024
    print(f"  Size: {size_kb} KB")
    print("Done.")
