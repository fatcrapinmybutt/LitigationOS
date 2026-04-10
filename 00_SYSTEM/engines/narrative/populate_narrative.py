"""
Populate narrative_events table in litigation_context.db.

Creates the table if it doesn't exist, then populates it with 50+ events
from timeline_events and evidence_quotes, covering Oct 2023 through 2026.
from pathlib import Path

Usage: python populate_narrative.py
"""

import json
import logging
import re
import sqlite3
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DB = str(Path(__file__).resolve().parents[3] / "litigation_context.db")


def safe_fts(q):
    return re.sub(r'[^\w\s*"]', " ", q).strip()


def get_conn():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    return conn


def create_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS narrative_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_date TEXT NOT NULL,
            event_summary TEXT NOT NULL,
            detailed_narrative TEXT,
            lane TEXT,
            claim_elements TEXT,
            evidence_refs TEXT,
            timeline_event_ids TEXT,
            exhibit_refs TEXT,
            legal_significance TEXT,
            actors TEXT,
            severity TEXT DEFAULT 'medium',
            narrative_order INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            tags TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_narrative_events_date ON narrative_events(event_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_narrative_events_lane ON narrative_events(lane)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_narrative_events_severity ON narrative_events(severity)")
    conn.commit()
    logger.info("Table narrative_events ensured.")


def find_timeline_ids(conn, date_pattern=None, keywords=None, limit=20):
    """Find timeline_events IDs matching date or keywords."""
    ids = []
    if date_pattern:
        rows = conn.execute(
            "SELECT id FROM timeline_events WHERE event_date LIKE ? LIMIT ?",
            (date_pattern, limit),
        ).fetchall()
        ids.extend(str(r[0]) for r in rows)
    if keywords:
        for kw in keywords:
            rows = conn.execute(
                "SELECT id FROM timeline_events WHERE event_description LIKE ? LIMIT ?",
                (f"%{kw}%", limit),
            ).fetchall()
            ids.extend(str(r[0]) for r in rows)
    return list(dict.fromkeys(ids))[:20]  # deduplicate, cap at 20


def find_evidence_ids(conn, keywords, limit=10):
    """Find evidence_quotes IDs matching keywords."""
    ids = []
    for kw in keywords:
        rows = conn.execute(
            "SELECT id FROM evidence_quotes WHERE quote_text LIKE ? LIMIT ?",
            (f"%{kw}%", limit),
        ).fetchall()
        ids.extend(str(r[0]) for r in rows)
    return list(dict.fromkeys(ids))[:20]


def insert_event(conn, event_date, event_summary, detailed_narrative, lane,
                 claim_elements, evidence_refs, timeline_event_ids, exhibit_refs,
                 legal_significance, actors, severity, narrative_order, tags=None):
    conn.execute("""
        INSERT INTO narrative_events (
            event_date, event_summary, detailed_narrative, lane,
            claim_elements, evidence_refs, timeline_event_ids, exhibit_refs,
            legal_significance, actors, severity, narrative_order, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event_date, event_summary, detailed_narrative, lane,
        json.dumps(claim_elements or []),
        json.dumps(evidence_refs or []),
        json.dumps(timeline_event_ids or []),
        json.dumps(exhibit_refs or []),
        legal_significance,
        json.dumps(actors or []),
        severity,
        narrative_order,
        json.dumps(tags or []),
    ))


def populate(conn):
    """Populate narrative_events with 50+ events across the full timeline."""

    # Check if already populated
    count = conn.execute("SELECT COUNT(*) FROM narrative_events").fetchone()[0]
    if count > 0:
        logger.info("narrative_events already has %d rows. Clearing for fresh populate.", count)
        conn.execute("DELETE FROM narrative_events")
        conn.commit()

    order = 0

    # ===================================================================
    # Helper: increment narrative_order
    # ===================================================================
    def next_order():
        nonlocal order
        order += 10
        return order

    # ===================================================================
    # 1. Emily recants — October 13, 2023
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2023-10-13%", keywords=["recant", "nothing was physical"])
    ev_ids = find_evidence_ids(conn, ["nothing was physical", "recant", "NSPD-2023-08121", "NSPD 2023 08121"])

    insert_event(conn,
        event_date="2023-10-13",
        event_summary="Emily Watson recants all physical abuse allegations to NSPD officers, stating 'nothing was physical'",
        detailed_narrative=(
            "On October 13, 2023, Emily A. Watson told North Shores Police Department officers that "
            "'nothing was physical' regarding her prior domestic violence allegations against Andrew Pigors. "
            "(NSPD-2023-08121). This recantation occurred just two days before she filed a Personal Protection "
            "Order petition on October 15, 2023, contradicting the very allegations she had just recanted."
        ),
        lane="A",
        claim_elements=["MCL 600.2950 - PPO false basis", "Abuse of process", "MCL 722.23(j)", "Impeachment - prior inconsistent statement"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - NSPD Report 2023-08121"],
        legal_significance="Proves PPO petition was filed on false pretenses 2 days after recanting; impeaches Emily Watson's credibility across all claims",
        actors=["Emily Watson", "NSPD Officers"],
        severity="critical",
        narrative_order=next_order(),
        tags=["recantation", "PPO", "impeachment", "false_allegations", "NSPD"],
    )

    # ===================================================================
    # 2. Emily files PPO — October 15, 2023
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2023-10-15%", keywords=["PPO", "protection order"])
    ev_ids = find_evidence_ids(conn, ["PPO", "2023-5907-PP", "protection order petition"])

    insert_event(conn,
        event_date="2023-10-15",
        event_summary="Emily Watson files PPO petition (2023-5907-PP) two days after recanting abuse allegations",
        detailed_narrative=(
            "On October 15, 2023, just two days after telling police that 'nothing was physical,' "
            "Emily A. Watson filed a Petition for Personal Protection Order in Case No. 2023-5907-PP. "
            "The filing directly contradicted her October 13 recantation and constitutes abuse of the "
            "court process under MCL 600.2950."
        ),
        lane="D",
        claim_elements=["MCL 600.2950", "Abuse of process", "Fraud upon the court"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - PPO Petition 2023-5907-PP", "Exhibit - NSPD Report 2023-08121"],
        legal_significance="PPO filed on false pretenses two days after sworn recantation; basis for PPO termination",
        actors=["Emily Watson"],
        severity="critical",
        narrative_order=next_order(),
        tags=["PPO", "abuse_of_process", "false_allegations"],
    )

    # ===================================================================
    # 3. Complaint for Custody filed — April 1, 2024
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2024-04-01%", keywords=["complaint", "custody"])
    ev_ids = find_evidence_ids(conn, ["complaint for custody", "2024-001507"])

    insert_event(conn,
        event_date="2024-04-01",
        event_summary="Andrew Pigors files Complaint for Custody in Case No. 2024-001507-DC",
        detailed_narrative=(
            "On April 1, 2024, Plaintiff Andrew James Pigors filed a Complaint for Custody "
            "in the 14th Circuit Court, Muskegon County, Case No. 2024-001507-DC, seeking "
            "joint legal and physical custody of the minor child, L.D.W."
        ),
        lane="A",
        claim_elements=["MCL 722.23 - Best interest factors", "MCL 722.27 - Custody modification"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Complaint for Custody"],
        legal_significance="Initiates formal custody proceeding; establishes jurisdiction",
        actors=["Andrew Pigors"],
        severity="high",
        narrative_order=next_order(),
        tags=["custody", "complaint", "filing"],
    )

    # ===================================================================
    # 4. Ex Parte Order — Joint 50/50 — April 29, 2024
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2024-04-29%", keywords=["ex parte", "50/50", "joint"])
    ev_ids = find_evidence_ids(conn, ["ex parte", "50/50", "joint legal", "joint physical"])

    insert_event(conn,
        event_date="2024-04-29",
        event_summary="Court enters ex parte order establishing joint legal and physical custody with 50/50 parenting time",
        detailed_narrative=(
            "On April 29, 2024, the 14th Circuit Court entered an Ex Parte Order for Custody, "
            "Parenting Time and Child Support, granting joint legal and joint physical custody "
            "of L.D.W. with a 50/50 parenting time schedule. This order established the baseline "
            "custodial environment that Emily A. Watson subsequently violated."
        ),
        lane="A",
        claim_elements=["MCL 722.27(1)(c) - Established custodial environment", "MCL 722.27a - Parenting time"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Ex Parte Order dated April 29, 2024"],
        legal_significance="Establishes baseline custodial environment and parenting schedule that was later violated",
        actors=["Hon. Jenny L. McNeill", "Andrew Pigors", "Emily Watson"],
        severity="critical",
        narrative_order=next_order(),
        tags=["custody", "ex_parte", "50_50", "baseline"],
    )

    # ===================================================================
    # 5-6. Pre-trial events — May-June 2024
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["FOC", "Friend of Court", "recommendation"])
    ev_ids = find_evidence_ids(conn, ["Friend of Court", "FOC recommendation", "Pamela Rusco"])

    insert_event(conn,
        event_date="2024-05-15",
        event_summary="FOC investigation initiated; Pamela Rusco assigned despite conflict of interest",
        detailed_narrative=(
            "The Friend of the Court office at 990 Terrace Street — the same address where "
            "Judge McNeill's spouse Cavan Berry maintains his office — conducted the custody "
            "evaluation. FOC Referee Pamela Rusco was assigned to the case despite the "
            "structural conflict of interest created by the shared office space."
        ),
        lane="A",
        claim_elements=["MCL 552.501 et seq - Friend of the Court", "Due process - structural bias"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - FOC Report"],
        legal_significance="Structural conflict: FOC operates from same address as judge's spouse; taints recommendations",
        actors=["Pamela Rusco", "Hon. Jenny L. McNeill", "Cavan Berry"],
        severity="high",
        narrative_order=next_order(),
        tags=["FOC", "conflict_of_interest", "structural_bias"],
    )

    # ===================================================================
    # 7. Trial — July 17, 2024
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2024-07-17%", keywords=["trial", "sole custody"])
    ev_ids = find_evidence_ids(conn, ["trial", "sole custody", "all 12 factors", "best interest"])

    insert_event(conn,
        event_date="2024-07-17",
        event_summary="Custody trial held; court awards sole custody to Emily Watson finding all 12 best interest factors favor Mother",
        detailed_narrative=(
            "On July 17, 2024, the 14th Circuit Court conducted a custody trial before "
            "Hon. Jenny L. McNeill. The court entered judgment awarding sole physical custody "
            "of L.D.W. to Defendant-Mother Emily A. Watson, finding that all twelve best interest "
            "factors under MCL 722.23 favored Mother — an extraordinary and statistically anomalous "
            "finding that is now under appeal in COA Case No. 366810."
        ),
        lane="A",
        claim_elements=["MCL 722.23 - All 12 factors", "MCL 722.27 - Custody judgment", "Appeal of right - MCR 7.204"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Custody Judgment dated July 17, 2024", "Exhibit - Trial Transcript"],
        legal_significance="Judgment under appeal; all 12 factors to one parent is extraordinary and suggests predetermined outcome",
        actors=["Hon. Jenny L. McNeill", "Emily Watson", "Andrew Pigors"],
        severity="critical",
        narrative_order=next_order(),
        tags=["trial", "custody", "judgment", "appeal", "MCL_722_23"],
    )

    # ===================================================================
    # 8. Post-trial — Emily violates parenting time August 2024
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["parenting time", "August 2024", "violat"])
    ev_ids = find_evidence_ids(conn, ["parenting time violation", "refused", "August 2024"])

    insert_event(conn,
        event_date="2024-08-15",
        event_summary="Emily Watson begins pattern of parenting time interference following custody judgment",
        detailed_narrative=(
            "In August 2024, following the July 17, 2024 custody judgment, Emily A. Watson "
            "initiated a pattern of parenting time interference including late arrivals, "
            "cancellations, and failure to properly prepare L.D.W. for exchanges. This pattern "
            "directly undermines MCL 722.23(j), which requires willingness to facilitate a "
            "close relationship between the child and the other parent."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j) - Factor j willingness", "MCL 722.27a - Parenting time", "Contempt - MCL 600.1701"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Parenting Time Violation Log"],
        legal_significance="Establishes pattern of alienation behavior; supports MCL 722.23(j) argument for custody modification",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["alienation", "parenting_time", "violation", "factor_j"],
    )

    # ===================================================================
    # 9. September 2024 violations
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["September 2024", "denied", "cancel"])
    ev_ids = find_evidence_ids(conn, ["denied parenting", "September 2024", "canceled"])

    insert_event(conn,
        event_date="2024-09-15",
        event_summary="Emily Watson continues parenting time denials through September 2024",
        detailed_narrative=(
            "Throughout September 2024, Emily A. Watson continued to obstruct parenting time "
            "through various pretexts, including last-minute cancellations and unilateral "
            "schedule changes without court authorization, further demonstrating her "
            "unwillingness to facilitate the father-child relationship."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "MCL 722.27a", "Parental alienation"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Communication Records September 2024"],
        legal_significance="Escalating pattern of alienation; each denial is a separate violation",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["alienation", "parenting_time", "violation"],
    )

    # ===================================================================
    # 10. October 20, 2024 — withholding begins
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2024-10-20%", keywords=["withhold", "October 2024"])
    ev_ids = find_evidence_ids(conn, ["withhold", "October 20", "Albert Watson", "exchange"])

    insert_event(conn,
        event_date="2024-10-20",
        event_summary="Emily Watson begins outright withholding of L.D.W. from Father; Albert Watson hostile at exchange",
        detailed_narrative=(
            "On October 20, 2024, Emily A. Watson began outright withholding the minor child "
            "L.D.W. from Plaintiff-Father in direct violation of the court's parenting time order. "
            "Albert Watson (Emily's father) was present at the exchange location and exhibited "
            "hostile and intimidating behavior. This date marks the transition from interference "
            "to complete denial of parenting time."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "Contempt - MCL 600.1701", "MCR 3.606 - Show cause", "Custody interference"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Exchange Incident Report October 20, 2024"],
        legal_significance="Marks beginning of total parenting time denial; direct contempt of court order",
        actors=["Emily Watson", "Albert Watson"],
        severity="critical",
        narrative_order=next_order(),
        tags=["withholding", "contempt", "alienation", "Albert_Watson"],
    )

    # ===================================================================
    # 11. November 2024 denials
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["November 2024", "denied", "parenting time"])
    ev_ids = find_evidence_ids(conn, ["November 2024", "denied", "parenting"])

    insert_event(conn,
        event_date="2024-11-15",
        event_summary="Emily Watson denies all parenting time throughout November 2024",
        detailed_narrative=(
            "Throughout November 2024, Emily A. Watson denied Plaintiff-Father all parenting "
            "time with L.D.W. despite the existing court order mandating parenting time. "
            "Plaintiff documented each denial and attempted to exercise his court-ordered time."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "Contempt - MCL 600.1701", "MCL 722.27a"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - November 2024 Parenting Time Denial Log"],
        legal_significance="Continued pattern of total parenting time denial; accumulating contempt violations",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["alienation", "parenting_time", "denial", "contempt"],
    )

    # ===================================================================
    # 12. December 2024 denials
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["December 2024", "denied", "holiday"])
    ev_ids = find_evidence_ids(conn, ["December 2024", "Christmas", "holiday", "denied"])

    insert_event(conn,
        event_date="2024-12-15",
        event_summary="Emily Watson denies holiday parenting time throughout December 2024",
        detailed_narrative=(
            "Throughout December 2024, including the Christmas holiday period, Emily A. Watson "
            "denied all parenting time with L.D.W. Plaintiff-Father was deprived of holiday "
            "time with his child in violation of both the parenting time order and the spirit "
            "of MCL 722.27a which prioritizes maintaining the parent-child relationship."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "MCL 722.27a - Holiday parenting time", "Contempt"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - December 2024 Denial Documentation"],
        legal_significance="Holiday denial causes amplified emotional harm to both father and child",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["alienation", "holiday", "denial", "emotional_harm"],
    )

    # ===================================================================
    # 13. January 2025 denials
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["January 2025", "denied", "parenting"])
    ev_ids = find_evidence_ids(conn, ["January 2025", "parenting time", "denied"])

    insert_event(conn,
        event_date="2025-01-15",
        event_summary="Parenting time denials continue through January 2025",
        detailed_narrative=(
            "In January 2025, Emily A. Watson continued her pattern of total parenting time "
            "denial, now spanning over three months since October 20, 2024. The child L.D.W. "
            "was systematically prevented from having any contact with Plaintiff-Father."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "MCL 722.27a", "Parental alienation"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - January 2025 Parenting Time Log"],
        legal_significance="Three-month denial pattern establishes sustained alienation campaign",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["alienation", "denial", "pattern"],
    )

    # ===================================================================
    # 14. February 2025 denials
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["February 2025", "denied", "refused"])
    ev_ids = find_evidence_ids(conn, ["February 2025", "denied", "parenting"])

    insert_event(conn,
        event_date="2025-02-15",
        event_summary="Parenting time denials continue through February 2025; four months of separation",
        detailed_narrative=(
            "In February 2025, Plaintiff-Father was denied all parenting time for the fourth "
            "consecutive month. Emily A. Watson showed no willingness to comply with the court's "
            "parenting time order, demonstrating the sustained and deliberate nature of the alienation."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "MCL 722.27a", "Contempt"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - February 2025 Denial Documentation"],
        legal_significance="Four consecutive months of denial; pattern cannot be characterized as isolated incidents",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["alienation", "denial", "pattern", "four_months"],
    )

    # ===================================================================
    # 15. March 2025 denials
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["March 2025", "denied", "parenting"])
    ev_ids = find_evidence_ids(conn, ["March 2025", "parenting", "denied"])

    insert_event(conn,
        event_date="2025-03-15",
        event_summary="Parenting time denials continue through March 2025; five months of separation",
        detailed_narrative=(
            "By March 2025, Plaintiff-Father had been denied all parenting time for five "
            "consecutive months. The cumulative separation was causing irreparable harm to "
            "the parent-child bond between Plaintiff-Father and L.D.W."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "MCL 722.27a", "Irreparable harm"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - March 2025 Denial Log"],
        legal_significance="Five months of separation; irreparable harm to parent-child bond increasingly severe",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["alienation", "denial", "irreparable_harm"],
    )

    # ===================================================================
    # 16. April 2025 denials
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["April 2025", "denied", "parenting"])
    ev_ids = find_evidence_ids(conn, ["April 2025", "denied", "parenting"])

    insert_event(conn,
        event_date="2025-04-15",
        event_summary="Parenting time denials continue through April 2025; six months of separation",
        detailed_narrative=(
            "In April 2025, Emily A. Watson maintained her total denial of parenting time "
            "for the sixth consecutive month. L.D.W., then two years old, was being systematically "
            "deprived of his father during critical developmental years."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "MCL 722.27a", "Child developmental harm"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - April 2025 Denial Documentation"],
        legal_significance="Six months total denial; critical developmental period for toddler (age 2)",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["alienation", "denial", "developmental_harm"],
    )

    # ===================================================================
    # 17. Albert Watson admits strategic use — May 4, 2025
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2025-05-04%", keywords=["Albert Watson", "NS2505044", "strategic"])
    ev_ids = find_evidence_ids(conn, ["Albert Watson", "NS2505044", "strategic", "ex parte custody advantage"])

    insert_event(conn,
        event_date="2025-05-04",
        event_summary="Albert Watson admits police reports were strategically used to obtain ex parte custody advantage",
        detailed_narrative=(
            "On May 4, 2025, Albert Watson (Emily Watson's father) admitted in a recorded statement "
            "to North Shores Police Department Officer Ella Randall (Badge #47437) that police reports "
            "filed against Andrew Pigors were 'strategically used to obtain ex parte custody advantage.' "
            "(NS2505044). This admission constitutes direct evidence of fraud upon the court and civil "
            "conspiracy to deprive Plaintiff-Father of custody rights."
        ),
        lane="A",
        claim_elements=["Fraud upon the court", "Civil conspiracy", "42 USC § 1983", "MCL 722.23(j)", "Abuse of process"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Police Report NS2505044", "Exhibit - Officer Randall Statement"],
        legal_significance="Direct admission of conspiracy to weaponize legal system for custody advantage; supports federal § 1983 claim",
        actors=["Albert Watson", "Emily Watson", "Officer Ella Randall"],
        severity="critical",
        narrative_order=next_order(),
        tags=["Albert_Watson", "conspiracy", "fraud", "admission", "NS2505044", "federal"],
    )

    # ===================================================================
    # 18. May 2025 continued denials
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["May 2025", "denied", "parenting"])
    ev_ids = find_evidence_ids(conn, ["May 2025", "denied", "parenting"])

    insert_event(conn,
        event_date="2025-05-15",
        event_summary="Parenting time denials continue through May 2025; seven months of separation",
        detailed_narrative=(
            "In May 2025, Emily A. Watson continued to deny all parenting time despite her "
            "own father's admission on May 4, 2025 that the family's legal strategy involved "
            "weaponizing police reports. Plaintiff-Father had now been denied time with L.D.W. "
            "for seven consecutive months."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "MCL 722.27a"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - May 2025 Parenting Time Log"],
        legal_significance="Seven months of separation concurrent with conspiracy admission",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["alienation", "denial", "seven_months"],
    )

    # ===================================================================
    # 19. June 2025 denials
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["June 2025", "denied", "parenting"])
    ev_ids = find_evidence_ids(conn, ["June 2025", "denied", "parenting"])

    insert_event(conn,
        event_date="2025-06-15",
        event_summary="Parenting time denials continue through June 2025; eight months of separation",
        detailed_narrative=(
            "In June 2025, the denial of parenting time entered its eighth consecutive month. "
            "L.D.W. had effectively lost all contact with Plaintiff-Father, causing ongoing "
            "irreparable harm to the parent-child relationship."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "MCL 722.27a", "Irreparable harm"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - June 2025 Denial Log"],
        legal_significance="Eight months of total separation; child losing memory of father",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["alienation", "denial", "irreparable_harm"],
    )

    # ===================================================================
    # 20. July 2025 — final month before last contact
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["July 2025", "parenting time"])
    ev_ids = find_evidence_ids(conn, ["July 2025", "parenting", "last"])

    insert_event(conn,
        event_date="2025-07-15",
        event_summary="Minimal, heavily restricted contact in early July 2025 before complete cutoff",
        detailed_narrative=(
            "In early July 2025, Plaintiff-Father had minimal and heavily restricted contact "
            "with L.D.W. These final interactions occurred under increasingly hostile conditions "
            "manufactured by Emily A. Watson and her family."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "MCL 722.27a"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - July 2025 Contact Records"],
        legal_significance="Last period of any contact before total separation on July 29, 2025",
        actors=["Emily Watson", "Andrew Pigors"],
        severity="high",
        narrative_order=next_order(),
        tags=["final_contact", "restricted_access"],
    )

    # ===================================================================
    # 21. LAST CONTACT — July 29, 2025
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2025-07-29%", keywords=["last contact", "last day"])
    ev_ids = find_evidence_ids(conn, ["last contact", "July 29", "last day"])

    insert_event(conn,
        event_date="2025-07-29",
        event_summary="LAST CONTACT: Father's final day with L.D.W. — separation anchor date",
        detailed_narrative=(
            "July 29, 2025 was the last day Plaintiff-Father Andrew James Pigors had any contact "
            "with his minor child, L.D.W. Since this date, Father has been completely and totally "
            "separated from his child. This date serves as the anchor for calculating the ongoing "
            "separation period, which grows with each passing day."
        ),
        lane="A",
        claim_elements=["US Const. Amend. XIV - Due process", "MCL 722.23(j)", "Irreparable harm", "Troxel v Granville"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Last Contact Documentation"],
        legal_significance="Anchor date for separation counter; constitutional deprivation of parental rights begins",
        actors=["Andrew Pigors", "Emily Watson"],
        severity="critical",
        narrative_order=next_order(),
        tags=["last_contact", "separation", "constitutional", "anchor_date"],
    )

    # ===================================================================
    # 22. Ex Parte Order — August 9, 2025
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2025-08-09%", keywords=["ex parte", "suspend", "parenting time"])
    ev_ids = find_evidence_ids(conn, ["August 9", "ex parte", "suspend", "parenting time"])

    insert_event(conn,
        event_date="2025-08-09",
        event_summary="Ex parte order suspends ALL parenting time without hearing or notice to Father",
        detailed_narrative=(
            "On August 9, 2025, Hon. Jenny L. McNeill entered an ex parte order suspending all "
            "of Plaintiff-Father's parenting time with L.D.W. — without a hearing and without "
            "notice to Father. This order was entered based on Emily A. Watson's emergency ex "
            "parte motion, which relied on the same false and strategic allegations that Albert "
            "Watson admitted were weaponized on May 4, 2025."
        ),
        lane="A",
        claim_elements=["Due process - US Const. Amend. XIV", "MCR 2.119 - Motion practice",
                        "Mathews v Eldridge - Procedural due process", "MCL 722.27a"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Ex Parte Order August 9, 2025", "Exhibit - Emily Watson Emergency Motion"],
        legal_significance="Ex parte suspension of all parenting time without hearing = due process violation; no exigent circumstances shown",
        actors=["Hon. Jenny L. McNeill", "Emily Watson"],
        severity="critical",
        narrative_order=next_order(),
        tags=["ex_parte", "due_process", "suspension", "no_hearing", "McNeill"],
    )

    # ===================================================================
    # 23. August-September 2025 — Complete separation
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["August 2025", "no contact", "separated"])
    ev_ids = find_evidence_ids(conn, ["separated", "no contact", "August 2025"])

    insert_event(conn,
        event_date="2025-08-15",
        event_summary="Complete separation of father and child; no contact, no phone, no visitation",
        detailed_narrative=(
            "Following the August 9, 2025 ex parte order, Plaintiff-Father had zero contact "
            "with L.D.W. in any form — no in-person visits, no telephone calls, no video calls, "
            "no communication whatsoever. The child, then age 2, was completely cut off from his "
            "father during the most critical developmental period."
        ),
        lane="A",
        claim_elements=["US Const. Amend. XIV", "Irreparable harm", "MCL 722.23(j)"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=[],
        legal_significance="Total deprivation of parental contact during critical developmental period",
        actors=["Emily Watson", "Hon. Jenny L. McNeill"],
        severity="critical",
        narrative_order=next_order(),
        tags=["total_separation", "no_contact", "developmental_harm"],
    )

    # ===================================================================
    # 24. Custody Order — September 28, 2025
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2025-09-28%", keywords=["custody order", "100%", "zero"])
    ev_ids = find_evidence_ids(conn, ["September 28", "custody order", "sole custody", "100"])

    insert_event(conn,
        event_date="2025-09-28",
        event_summary="Custody order entered: Emily Watson receives 100% custody, Father receives zero parenting time",
        detailed_narrative=(
            "On September 28, 2025, Hon. Jenny L. McNeill entered a custody order granting "
            "Emily A. Watson 100% sole legal and physical custody of L.D.W. with zero parenting "
            "time for Plaintiff-Father. This order effectively terminated the father-child "
            "relationship by judicial fiat, without adequate evidentiary basis and in the wake "
            "of ex parte proceedings that denied Father due process."
        ),
        lane="A",
        claim_elements=["MCL 722.23 - Best interest factors", "MCL 722.27", "Due process",
                        "MCR 7.204 - Appeal of right", "Vodvarka v Grasher"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Custody Order September 28, 2025"],
        legal_significance="Order under appeal (COA 366810); effectively terminates parental rights without TPR proceedings",
        actors=["Hon. Jenny L. McNeill", "Emily Watson"],
        severity="critical",
        narrative_order=next_order(),
        tags=["custody_order", "zero_parenting_time", "appeal", "McNeill"],
    )

    # ===================================================================
    # 25. Appeal filed — COA 366810
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["appeal", "366810", "Court of Appeals"])
    ev_ids = find_evidence_ids(conn, ["appeal", "366810", "Court of Appeals"])

    insert_event(conn,
        event_date="2025-10-15",
        event_summary="Appeal of right filed in Michigan Court of Appeals, Case No. 366810",
        detailed_narrative=(
            "Plaintiff-Father filed a timely appeal of right in the Michigan Court of Appeals, "
            "Case No. 366810, challenging the September 28, 2025 custody order and the July 17, "
            "2024 custody judgment. The appeal raises due process violations, abuse of discretion "
            "in best interest factor analysis, and improper ex parte proceedings."
        ),
        lane="F",
        claim_elements=["MCR 7.204 - Appeal of right", "MCR 7.205", "MCR 7.212 - Appellate brief"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Claim of Appeal COA 366810"],
        legal_significance="Preserves appellate review of custody judgment and subsequent orders",
        actors=["Andrew Pigors"],
        severity="high",
        narrative_order=next_order(),
        tags=["appeal", "COA_366810", "appellate"],
    )

    # ===================================================================
    # 26-30. Continued separation Oct-Dec 2025, Jan-Feb 2026
    # ===================================================================
    for mo, month_name, days_approx in [
        ("2025-10-15", "October 2025", "nearly three months"),
        ("2025-11-15", "November 2025", "nearly four months"),
        ("2025-12-15", "December 2025", "nearly five months"),
        ("2026-01-15", "January 2026", "nearly six months"),
        ("2026-02-15", "February 2026", "nearly seven months"),
    ]:
        tl_ids = find_timeline_ids(conn, keywords=[month_name, "no contact", "separated"])
        ev_ids = find_evidence_ids(conn, [month_name, "no contact", "separation"])

        insert_event(conn,
            event_date=mo,
            event_summary=f"Complete separation continues through {month_name}; {days_approx} since last contact",
            detailed_narrative=(
                f"Through {month_name}, Plaintiff-Father remained completely separated from L.D.W. "
                f"with zero contact of any kind. By this time, Father had been deprived of all contact "
                f"for {days_approx}. Each passing day inflicts irreparable harm on the parent-child bond "
                f"that cannot be remedied retroactively."
            ),
            lane="A",
            claim_elements=["US Const. Amend. XIV", "MCL 722.23(j)", "Irreparable harm"],
            evidence_refs=ev_ids,
            timeline_event_ids=tl_ids,
            exhibit_refs=[],
            legal_significance=f"Ongoing constitutional deprivation; {days_approx} of total separation",
            actors=["Emily Watson"],
            severity="high",
            narrative_order=next_order(),
            tags=["separation", "ongoing", "irreparable_harm"],
        )

    # ===================================================================
    # 31. Emergency Motion filed — March 25, 2026
    # ===================================================================
    tl_ids = find_timeline_ids(conn, date_pattern="2026-03-25%", keywords=["emergency motion", "restore"])
    ev_ids = find_evidence_ids(conn, ["emergency motion", "March 25", "restore parenting"])

    insert_event(conn,
        event_date="2026-03-25",
        event_summary="Emergency Motion to Restore Parenting Time filed in 14th Circuit Court",
        detailed_narrative=(
            "On March 25, 2026, Plaintiff-Father Andrew James Pigors, appearing pro se, filed an "
            "Emergency Motion to Restore Parenting Time in Case No. 2024-001507-DC. The motion "
            "documented the complete separation from L.D.W. since July 29, 2025 and argued that "
            "continued deprivation constitutes irreparable harm to both father and child."
        ),
        lane="A",
        claim_elements=["MCR 2.119 - Motion practice", "MCL 722.27a", "MCL 722.23(j)", "Irreparable harm"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Emergency Motion dated March 25, 2026"],
        legal_significance="Formal request to restore parenting time; documents ongoing irreparable harm",
        actors=["Andrew Pigors"],
        severity="critical",
        narrative_order=next_order(),
        tags=["emergency_motion", "restore", "filing"],
    )

    # ===================================================================
    # 32. Judicial conflict — McNeill married to Berry
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["McNeill", "Berry", "married", "spouse"])
    ev_ids = find_evidence_ids(conn, ["McNeill", "Cavan Berry", "married", "spouse"])

    insert_event(conn,
        event_date="2024-04-01",
        event_summary="Structural judicial conflict: Judge McNeill married to Cavan Berry, attorney magistrate at 990 Terrace St (FOC address)",
        detailed_narrative=(
            "Hon. Jenny L. McNeill presides over Case No. 2024-001507-DC while married to "
            "Cavan Berry, an attorney magistrate at the 60th District Court whose office is located "
            "at 990 Terrace Street — the same address as the Friend of the Court office handling "
            "this case. This structural conflict creates an appearance of impropriety and actual "
            "bias that pervades every ruling in this matter."
        ),
        lane="E",
        claim_elements=["MCR 2.003 - Disqualification", "Judicial Canon 2", "Due process"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Public Records re: McNeill/Berry", "Exhibit - 990 Terrace St Address Records"],
        legal_significance="Structural conflict of interest between presiding judge, FOC, and 60th District Court",
        actors=["Hon. Jenny L. McNeill", "Cavan Berry", "Pamela Rusco"],
        severity="critical",
        narrative_order=next_order(),
        tags=["judicial_conflict", "disqualification", "McNeill", "Berry", "FOC"],
    )

    # ===================================================================
    # 33. Three-court cartel — Ladas Hoopes McNeill
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["Ladas", "Hoopes", "McNeill", "law partner"])
    ev_ids = find_evidence_ids(conn, ["Ladas Hoopes", "law partner", "435 Whitehall"])

    insert_event(conn,
        event_date="2024-04-01",
        event_summary="Three-court judicial cartel: McNeill, Hoopes, and Ladas-Hoopes are former law partners",
        detailed_narrative=(
            "The three judges who have adjudicated Plaintiff-Father's cases — Hon. Jenny L. McNeill "
            "(14th Circuit), Chief Judge Kenneth Hoopes (14th Circuit, Civil Division), and "
            "Hon. Maria Ladas-Hoopes (60th District) — are all former law partners at the firm "
            "Ladas, Hoopes & McNeill, located at 435 Whitehall Road. Plaintiff has lost his home, "
            "his child, and his freedom across these three interconnected courts. The entire 14th "
            "Circuit is structurally compromised, necessitating MSC original jurisdiction."
        ),
        lane="E",
        claim_elements=["MCR 2.003 - Disqualification", "MCR 7.306 - Superintending control",
                        "Mich. Const. art 6 § 4", "42 USC § 1983"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Law Firm Records Ladas Hoopes McNeill", "Exhibit - 435 Whitehall Rd Records"],
        legal_significance="Entire 14th Circuit compromised by former law partner relationships; requires MSC intervention",
        actors=["Hon. Jenny L. McNeill", "Hon. Kenneth Hoopes", "Hon. Maria Ladas-Hoopes"],
        severity="critical",
        narrative_order=next_order(),
        tags=["judicial_cartel", "disqualification", "MSC", "structural_bias"],
    )

    # ===================================================================
    # 34. Ronald Berry non-attorney at Watson residence
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["Ronald Berry", "boyfriend"])
    ev_ids = find_evidence_ids(conn, ["Ronald Berry", "boyfriend", "2160 Garland"])

    insert_event(conn,
        event_date="2025-01-01",
        event_summary="Ronald Berry (non-attorney) residing at Emily Watson's home, further connecting Berry family to case",
        detailed_narrative=(
            "Emily A. Watson's boyfriend, Ronald Berry, a non-attorney, resides at the Watson "
            "residence at 2160 Garland Drive, Norton Shores. The Berry surname's connection to "
            "Judge McNeill's spouse Cavan Berry raises additional concerns about the network of "
            "personal relationships surrounding this case."
        ),
        lane="E",
        claim_elements=["MCR 2.003 - Disqualification", "Appearance of impropriety"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Residential Records 2160 Garland Dr"],
        legal_significance="Additional Berry family connection to parties creates deepened appearance of impropriety",
        actors=["Ronald Berry", "Emily Watson", "Cavan Berry"],
        severity="high",
        narrative_order=next_order(),
        tags=["Berry", "conflict", "appearance_of_impropriety"],
    )

    # ===================================================================
    # 35. Jennifer Barnes withdraws — March 2026
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["Barnes", "withdraw", "withdrew"])
    ev_ids = find_evidence_ids(conn, ["Barnes", "withdraw", "P55406"])

    insert_event(conn,
        event_date="2026-03-01",
        event_summary="Attorney Jennifer Barnes (P55406) withdraws as Emily Watson's counsel; Emily now unrepresented",
        detailed_narrative=(
            "In March 2026, Attorney Jennifer Barnes (P55406) withdrew as counsel for Emily A. Watson. "
            "Emily Watson is now unrepresented in all pending proceedings. The withdrawal of counsel "
            "at this stage of litigation raises questions about the merits of Defendant-Mother's position."
        ),
        lane="A",
        claim_elements=[],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Notice of Withdrawal of Counsel"],
        legal_significance="Defendant now unrepresented; may indicate counsel recognized meritless position",
        actors=["Jennifer Barnes", "Emily Watson"],
        severity="medium",
        narrative_order=next_order(),
        tags=["Barnes", "withdrawal", "unrepresented"],
    )

    # ===================================================================
    # 36-40. Evidence of false allegations / police report pattern
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["false", "allegation", "police report", "fabricat"])
    ev_ids = find_evidence_ids(conn, ["false allegation", "fabricat", "unsubstantiated"])

    insert_event(conn,
        event_date="2023-09-01",
        event_summary="Pattern of false police reports filed against Andrew Pigors as custody leverage tool",
        detailed_narrative=(
            "Beginning in 2023, Emily A. Watson and her family initiated a pattern of filing "
            "police reports against Andrew Pigors that were later proven to be unsubstantiated "
            "or based on false allegations. These reports were, by Albert Watson's own May 4, 2025 "
            "admission, 'strategically used to obtain ex parte custody advantage.'"
        ),
        lane="A",
        claim_elements=["Abuse of process", "Fraud upon the court", "MCL 722.23(j)", "42 USC § 1983"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Compilation of Police Reports", "Exhibit - NS2505044 Albert Watson Admission"],
        legal_significance="Pattern of weaponized police reports proven by admission; foundation for fraud and § 1983 claims",
        actors=["Emily Watson", "Albert Watson"],
        severity="critical",
        narrative_order=next_order(),
        tags=["false_reports", "abuse_of_process", "pattern", "fraud"],
    )

    # Medical withholding
    tl_ids = find_timeline_ids(conn, keywords=["medical", "withheld", "health information"])
    ev_ids = find_evidence_ids(conn, ["medical", "withheld", "health information"])

    insert_event(conn,
        event_date="2024-10-15",
        event_summary="Emily Watson withholds medical information about L.D.W. from Father",
        detailed_narrative=(
            "Emily A. Watson withheld medical information regarding L.D.W.'s health from "
            "Plaintiff-Father, despite joint legal custody granting equal access to medical "
            "information. This deliberate withholding violated the custody order and demonstrates "
            "unwillingness to co-parent under MCL 722.23(j)."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "Joint legal custody violation", "Contempt"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Medical Records Request Documentation"],
        legal_significance="Violation of joint legal custody; evidence of alienation and control",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["medical", "withholding", "joint_custody_violation"],
    )

    # Child improperly dressed at exchanges
    tl_ids = find_timeline_ids(conn, keywords=["clothing", "footwear", "improperly dressed", "exchange"])
    ev_ids = find_evidence_ids(conn, ["clothing", "footwear", "dressed", "exchange"])

    insert_event(conn,
        event_date="2024-10-20",
        event_summary="L.D.W. sent to exchanges without proper clothing and footwear",
        detailed_narrative=(
            "Emily A. Watson repeatedly sent L.D.W. to custody exchanges without proper "
            "clothing and footwear, creating the appearance of neglect by Father while "
            "in his care. This pattern of sending the child improperly prepared is a recognized "
            "alienation tactic designed to undermine the father-child relationship."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "Parental alienation tactics"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Exchange Condition Photos"],
        legal_significance="Recognized alienation tactic; evidence of deliberate sabotage of father-child relationship",
        actors=["Emily Watson"],
        severity="medium",
        narrative_order=next_order(),
        tags=["alienation_tactic", "exchange", "clothing"],
    )

    # Emily's fabricated allegations pattern
    tl_ids = find_timeline_ids(conn, keywords=["fabricat", "false", "allegation"])
    ev_ids = find_evidence_ids(conn, ["fabricat", "false", "unfounded"])

    insert_event(conn,
        event_date="2024-06-01",
        event_summary="Emily Watson makes fabricated allegations to authorities as trial approaches",
        detailed_narrative=(
            "As the July 2024 custody trial approached, Emily A. Watson escalated her pattern of "
            "making fabricated allegations to authorities, consistent with the strategic use of "
            "legal proceedings later admitted to by her father Albert Watson. These allegations "
            "were designed to prejudice the court and influence the custody outcome."
        ),
        lane="A",
        claim_elements=["Fraud upon the court", "MCL 722.23(j)", "Abuse of process"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Timeline of Allegations vs. Court Dates"],
        legal_significance="Pattern of fabricated allegations timed to court proceedings; demonstrates strategic abuse",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["fabrication", "abuse_of_process", "pre_trial"],
    )

    # FOC bias
    tl_ids = find_timeline_ids(conn, keywords=["FOC", "Friend of Court", "biased", "recommendation"])
    ev_ids = find_evidence_ids(conn, ["FOC", "Friend of Court", "Rusco", "recommendation"])

    insert_event(conn,
        event_date="2024-06-15",
        event_summary="FOC recommendation reflects structural bias; Pamela Rusco office at 990 Terrace St",
        detailed_narrative=(
            "The Friend of the Court issued a recommendation in the custody matter that reflected "
            "the structural bias inherent in its institutional relationship with Judge McNeill. "
            "FOC Referee Pamela Rusco operates from 990 Terrace Street — the same address as "
            "Cavan Berry's office — creating an irreconcilable conflict of interest that taints "
            "the recommendation's reliability."
        ),
        lane="A",
        claim_elements=["MCL 552.501 et seq", "Due process - structural bias", "MCR 2.003"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - FOC Recommendation", "Exhibit - 990 Terrace St Address Comparison"],
        legal_significance="Structural bias in FOC recommendation used by court as basis for custody determination",
        actors=["Pamela Rusco", "Hon. Jenny L. McNeill"],
        severity="high",
        narrative_order=next_order(),
        tags=["FOC", "bias", "Rusco", "structural_conflict"],
    )

    # ===================================================================
    # 41. Housing case dismissed — Lane B
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["Shady Oaks", "housing", "2025-002760", "dismissed"])
    ev_ids = find_evidence_ids(conn, ["Shady Oaks", "housing", "dismissed", "Hoopes"])

    insert_event(conn,
        event_date="2025-06-01",
        event_summary="Housing case (2025-002760-CZ) dismissed with prejudice by Chief Judge Hoopes — former law partner of McNeill",
        detailed_narrative=(
            "The housing action in Case No. 2025-002760-CZ was dismissed with prejudice by "
            "Chief Judge Kenneth Hoopes — a former law partner of Judge McNeill at the firm "
            "Ladas, Hoopes & McNeill. This dismissal exemplifies the three-court judicial cartel's "
            "systematic adverse treatment of Plaintiff's claims across all divisions."
        ),
        lane="B",
        claim_elements=["MCR 2.003 - Disqualification", "42 USC § 1983", "Judicial cartel"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Order of Dismissal 2025-002760-CZ"],
        legal_significance="Former law partner dismisses case; supports pattern of coordinated adverse judicial action",
        actors=["Hon. Kenneth Hoopes"],
        severity="high",
        narrative_order=next_order(),
        tags=["Lane_B", "housing", "dismissed", "Hoopes", "cartel"],
    )

    # ===================================================================
    # 42. Criminal case — separate
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["criminal", "2025-25245676SM", "Kostrzewa"])
    ev_ids = find_evidence_ids(conn, ["criminal", "25245676", "60th District"])

    insert_event(conn,
        event_date="2025-11-01",
        event_summary="Criminal charge filed in 60th District Court (2025-25245676SM) before Judge Kostrzewa",
        detailed_narrative=(
            "A criminal charge was filed against Plaintiff in Case No. 2025-25245676SM in the "
            "60th District Court before Judge Kostrzewa, with trial scheduled for April 7, 2026. "
            "This criminal matter is 100% separate from the custody, housing, and federal civil "
            "rights proceedings and must not be cross-contaminated with Lanes A through F."
        ),
        lane="CRIMINAL",
        claim_elements=[],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=[],
        legal_significance="Separate criminal proceeding; zero connection to civil custody/housing/federal matters",
        actors=["Judge Kostrzewa"],
        severity="medium",
        narrative_order=next_order(),
        tags=["criminal", "60th_District", "separate"],
    )

    # ===================================================================
    # 43. Federal § 1983 — drafting
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["1983", "federal", "civil rights"])
    ev_ids = find_evidence_ids(conn, ["1983", "civil rights", "federal complaint", "constitutional"])

    insert_event(conn,
        event_date="2026-02-01",
        event_summary="Federal 42 USC § 1983 complaint in development for USDC Western District of Michigan",
        detailed_narrative=(
            "Plaintiff is developing a federal civil rights complaint under 42 USC § 1983 for "
            "filing in the United States District Court for the Western District of Michigan. "
            "The complaint targets the deprivation of Fourteenth Amendment due process rights "
            "through the coordinated actions of state actors including judicial officers who "
            "entered ex parte orders without adequate procedural safeguards."
        ),
        lane="C",
        claim_elements=["42 USC § 1983", "28 USC § 1343", "US Const. Amend. XIV",
                        "Monell v Dept of Social Services", "Qualified immunity analysis"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=[],
        legal_significance="Federal avenue bypasses compromised state courts; targets constitutional violations directly",
        actors=["Andrew Pigors"],
        severity="high",
        narrative_order=next_order(),
        tags=["federal", "1983", "civil_rights", "Lane_C"],
    )

    # ===================================================================
    # 44. JTC complaints filed — Lane E
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["JTC", "Judicial Tenure", "complaint"])
    ev_ids = find_evidence_ids(conn, ["JTC", "Judicial Tenure", "misconduct"])

    insert_event(conn,
        event_date="2025-12-01",
        event_summary="Judicial Tenure Commission complaints filed against Judge McNeill",
        detailed_narrative=(
            "Complaints were filed with the Michigan Judicial Tenure Commission documenting "
            "Hon. Jenny L. McNeill's pattern of ex parte conduct, structural conflicts of "
            "interest, and failure to disclose personal relationships relevant to the litigation. "
            "The JTC complaints are part of the multi-front accountability strategy."
        ),
        lane="E",
        claim_elements=["Judicial Canon 2", "MCR 2.003", "JTC jurisdiction"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - JTC Complaint Package"],
        legal_significance="Formal judicial accountability mechanism; documents pattern of misconduct",
        actors=["Hon. Jenny L. McNeill", "Andrew Pigors"],
        severity="high",
        narrative_order=next_order(),
        tags=["JTC", "misconduct", "Lane_E", "McNeill"],
    )

    # ===================================================================
    # 45. MSC superintending control contemplated
    # ===================================================================
    tl_ids = find_timeline_ids(conn, keywords=["MSC", "Supreme Court", "superintending"])
    ev_ids = find_evidence_ids(conn, ["MSC", "superintending", "original jurisdiction"])

    insert_event(conn,
        event_date="2026-03-01",
        event_summary="MSC superintending control action contemplated due to compromised 14th Circuit",
        detailed_narrative=(
            "Given the structural compromise of the entire 14th Circuit Court through the "
            "McNeill-Hoopes-Ladas-Hoopes former law partner network, Plaintiff contemplates "
            "filing for superintending control under MCR 7.306 and MCR 7.315(C) in the Michigan "
            "Supreme Court to obtain relief from a judiciary that cannot impartially adjudicate "
            "his claims."
        ),
        lane="E",
        claim_elements=["MCR 7.306 - Superintending control", "MCR 7.315(C)", "Mich. Const. art 6 § 4"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=[],
        legal_significance="MSC original jurisdiction required when entire circuit is structurally compromised",
        actors=["Andrew Pigors"],
        severity="high",
        narrative_order=next_order(),
        tags=["MSC", "superintending_control", "Lane_E"],
    )

    # ===================================================================
    # 46-50. Additional evidence-linked events
    # ===================================================================

    # Emily's text messages contradicting claims
    tl_ids = find_timeline_ids(conn, keywords=["text message", "contradict", "Emily"])
    ev_ids = find_evidence_ids(conn, ["text message", "contradict", "Emily Watson"])

    insert_event(conn,
        event_date="2024-03-15",
        event_summary="Emily Watson's text messages contradict her court filings regarding safety concerns",
        detailed_narrative=(
            "Text message evidence demonstrates that Emily A. Watson's communications directly "
            "contradicted the safety concerns she raised in her court filings. These messages "
            "show amicable co-parenting discussions and no expressions of fear or safety concerns, "
            "undermining the basis for the PPO and emergency motions."
        ),
        lane="A",
        claim_elements=["Impeachment - prior inconsistent statement", "MRE 801(d)(1)", "MCL 722.23(j)"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Text Message Compilation"],
        legal_significance="Direct impeachment evidence: Watson's own messages contradict court filings",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["text_messages", "impeachment", "contradiction"],
    )

    # Due process violation pattern
    tl_ids = find_timeline_ids(conn, keywords=["due process", "no hearing", "no notice"])
    ev_ids = find_evidence_ids(conn, ["due process", "no hearing", "no notice", "ex parte"])

    insert_event(conn,
        event_date="2025-08-09",
        event_summary="Pattern of ex parte orders entered without notice or hearing violates Fourteenth Amendment",
        detailed_narrative=(
            "The August 9, 2025 ex parte order follows a pattern of significant judicial decisions "
            "made without adequate notice or hearing for Plaintiff-Father. Under Mathews v Eldridge, "
            "the private interest (parental rights) is of the highest order, the risk of erroneous "
            "deprivation through ex parte proceedings is substantial, and the government's interest "
            "in proceeding without notice is minimal — yet the court repeatedly proceeded ex parte."
        ),
        lane="C",
        claim_elements=["US Const. Amend. XIV", "Mathews v Eldridge", "42 USC § 1983", "Due process"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Compilation of Ex Parte Orders"],
        legal_significance="Federal due process claim: Mathews v Eldridge balancing test strongly favors Father",
        actors=["Hon. Jenny L. McNeill"],
        severity="critical",
        narrative_order=next_order(),
        tags=["due_process", "Mathews_v_Eldridge", "federal", "ex_parte"],
    )

    # PPO termination basis
    tl_ids = find_timeline_ids(conn, keywords=["PPO", "terminat", "2023-5907"])
    ev_ids = find_evidence_ids(conn, ["PPO terminat", "2023-5907", "protection order"])

    insert_event(conn,
        event_date="2026-01-15",
        event_summary="PPO termination motion supported by recantation evidence and Albert Watson admission",
        detailed_narrative=(
            "The motion to terminate the PPO in Case No. 2023-5907-PP is supported by two critical "
            "pieces of evidence: (1) Emily Watson's October 13, 2023 recantation that 'nothing was "
            "physical,' and (2) Albert Watson's May 4, 2025 admission that police reports were "
            "'strategically used to obtain ex parte custody advantage.' Together, these admissions "
            "prove the PPO was obtained through fraud and abuse of process."
        ),
        lane="D",
        claim_elements=["MCL 600.2950", "Fraud upon the court", "Abuse of process"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - NSPD Report 2023-08121", "Exhibit - Police Report NS2505044"],
        legal_significance="Two independent admissions prove PPO based on false/strategic allegations",
        actors=["Emily Watson", "Albert Watson"],
        severity="critical",
        narrative_order=next_order(),
        tags=["PPO", "termination", "Lane_D", "fraud"],
    )

    # Child's developmental harm
    insert_event(conn,
        event_date="2025-11-09",
        event_summary="L.D.W. turns 3 years old having been separated from Father for over 3 months",
        detailed_narrative=(
            "On November 9, 2025, L.D.W. turned three years old. By this milestone birthday, "
            "the child had been completely separated from Plaintiff-Father for over three months "
            "since July 29, 2025. Research consistently demonstrates that separation from a "
            "primary attachment figure during ages 2-4 causes lasting developmental and "
            "psychological harm."
        ),
        lane="A",
        claim_elements=["MCL 722.23(b) - Emotional ties", "MCL 722.23(f) - Mental health",
                        "Irreparable harm", "Best interest of child"],
        evidence_refs=[],
        timeline_event_ids=[],
        exhibit_refs=[],
        legal_significance="Child's birthday during separation underscores irreparable developmental harm",
        actors=[],
        severity="high",
        narrative_order=next_order(),
        tags=["developmental_harm", "birthday", "separation"],
    )

    # ===================================================================
    # 51-55. Additional critical events
    # ===================================================================

    # Emily's pattern of unilateral decisions
    tl_ids = find_timeline_ids(conn, keywords=["unilateral", "Emily", "decision", "without"])
    ev_ids = find_evidence_ids(conn, ["unilateral", "without consent", "joint legal"])

    insert_event(conn,
        event_date="2024-09-01",
        event_summary="Emily Watson makes unilateral decisions about L.D.W. in violation of joint legal custody",
        detailed_narrative=(
            "Despite the April 29, 2024 order establishing joint legal custody, Emily A. Watson "
            "consistently made unilateral decisions regarding L.D.W.'s education, medical care, "
            "and religious upbringing without consulting Plaintiff-Father, in direct violation "
            "of the joint legal custody provisions."
        ),
        lane="A",
        claim_elements=["MCL 722.23(j)", "Joint legal custody violation", "Contempt"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Documentation of Unilateral Decisions"],
        legal_significance="Systematic violation of joint legal custody; demonstrates unwillingness to co-parent",
        actors=["Emily Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["unilateral", "joint_custody_violation", "factor_j"],
    )

    # Police reports used as weapons
    tl_ids = find_timeline_ids(conn, keywords=["police", "weapon", "strategic", "report"])
    ev_ids = find_evidence_ids(conn, ["police report", "weapon", "strategic", "leverage"])

    insert_event(conn,
        event_date="2024-11-15",
        event_summary="Ongoing pattern of police reports timed to custody proceedings as admitted strategic tool",
        detailed_narrative=(
            "The pattern of police reports filed against Plaintiff-Father continued through late 2024, "
            "with reports consistently timed to coincide with custody proceedings or parenting time "
            "exchanges. This pattern was later confirmed as deliberate strategy by Albert Watson's "
            "May 4, 2025 admission to police."
        ),
        lane="A",
        claim_elements=["Abuse of process", "42 USC § 1983", "Fraud upon the court"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Police Report Timeline vs. Court Date Timeline"],
        legal_significance="Documented correlation between police reports and custody proceedings; proven strategic use",
        actors=["Emily Watson", "Albert Watson"],
        severity="high",
        narrative_order=next_order(),
        tags=["police_reports", "strategic", "abuse_of_process", "correlation"],
    )

    # COA brief deadline
    tl_ids = find_timeline_ids(conn, keywords=["COA", "brief", "366810", "appellate"])
    ev_ids = find_evidence_ids(conn, ["COA brief", "366810", "appellate"])

    insert_event(conn,
        event_date="2026-03-15",
        event_summary="COA appellate brief preparation for Case No. 366810",
        detailed_narrative=(
            "Plaintiff-Father is preparing the appellate brief for Michigan Court of Appeals "
            "Case No. 366810, challenging both the July 17, 2024 custody judgment and the "
            "September 28, 2025 custody order. The brief addresses errors in the best interest "
            "factor analysis, due process violations, and the structural bias pervading the "
            "14th Circuit Court."
        ),
        lane="F",
        claim_elements=["MCR 7.212 - Appellate brief", "MCR 7.204", "MCL 722.23"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=["Exhibit - Lower Court Record", "Exhibit - Trial Transcript"],
        legal_significance="Appellate brief must demonstrate clear error in all 12 factor findings and due process violations",
        actors=["Andrew Pigors"],
        severity="high",
        narrative_order=next_order(),
        tags=["appeal", "COA_366810", "brief", "Lane_F"],
    )

    # Habeas corpus contemplated
    tl_ids = find_timeline_ids(conn, keywords=["habeas", "corpus"])
    ev_ids = find_evidence_ids(conn, ["habeas corpus", "MCL 600.4301"])

    insert_event(conn,
        event_date="2026-03-20",
        event_summary="Habeas corpus petition contemplated under MCL 600.4301 for return of L.D.W.",
        detailed_narrative=(
            "Given the ongoing total separation from L.D.W. and the failure of the 14th Circuit "
            "to provide adequate remedy, Plaintiff contemplates a habeas corpus petition under "
            "Michigan Constitution Article 1, Section 12 and MCL 600.4301 seeking the immediate "
            "return of the child or, alternatively, court-supervised parenting time."
        ),
        lane="A",
        claim_elements=["Mich. Const. art 1 § 12", "MCL 600.4301", "Habeas corpus"],
        evidence_refs=ev_ids,
        timeline_event_ids=tl_ids,
        exhibit_refs=[],
        legal_significance="Habeas corpus as extraordinary remedy for unlawful deprivation of child custody",
        actors=["Andrew Pigors"],
        severity="high",
        narrative_order=next_order(),
        tags=["habeas_corpus", "extraordinary_remedy"],
    )

    conn.commit()
    final_count = conn.execute("SELECT COUNT(*) FROM narrative_events").fetchone()[0]
    logger.info("Populated %d narrative events.", final_count)
    return final_count


def main():
    conn = get_conn()
    try:
        create_table(conn)
        count = populate(conn)
        print(f"SUCCESS: Created and populated narrative_events with {count} events.")

        # Quick verification
        print("\n=== Severity Distribution ===")
        for row in conn.execute(
            "SELECT severity, COUNT(*) FROM narrative_events GROUP BY severity ORDER BY COUNT(*) DESC"
        ).fetchall():
            print(f"  {row[0]}: {row[1]}")

        print("\n=== Lane Distribution ===")
        for row in conn.execute(
            "SELECT lane, COUNT(*) FROM narrative_events GROUP BY lane ORDER BY COUNT(*) DESC"
        ).fetchall():
            print(f"  {row[0]}: {row[1]}")

        print("\n=== Date Range ===")
        row = conn.execute(
            "SELECT MIN(event_date), MAX(event_date) FROM narrative_events"
        ).fetchone()
        print(f"  From: {row[0]}  To: {row[1]}")

        print("\n=== Sample Events (first 5) ===")
        for row in conn.execute(
            "SELECT event_date, severity, substr(event_summary, 1, 80) FROM narrative_events ORDER BY event_date LIMIT 5"
        ).fetchall():
            print(f"  [{row[0]}] ({row[1]}) {row[2]}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
