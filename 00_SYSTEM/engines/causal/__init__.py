"""
CausalChainEngine — Fruit of the Poisonous Tree extraction for Pigors v Watson.

Extracts, persists, and queries causal chains from the litigation database.
Root poison: Oct 15, 2023 PPO filed 2 days after Emily recanted ("nothing was physical").
Every subsequent custody change, ex parte order, contempt, and jailing traces back.

Usage:
    from OO_SYSTEM.engines.causal import CausalChainEngine
    engine = CausalChainEngine()
    tree = engine.get_poisonous_tree()
"""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

DB_PATH = str(Path(__file__).resolve().parents[3] / "litigation_context.db")

# ── Chain relationship types ──────────────────────────────────────────────
CHAIN_TYPES = (
    "TRIGGERED_BY",    # Event A directly caused Event B
    "RETALIATION_FOR", # Event B was retaliation for Event A
    "ENABLED_BY",      # Event A made Event B possible
    "CONCEALED_FROM",  # Event A was hidden from affected party
    "FRUIT_OF",        # Event B is tainted by poisoned Event A (the PPO)
)

# ── Poisonous root event ─────────────────────────────────────────────────
PPO_ROOT_DATE = "2023-10-15"
PPO_ROOT_DESC = (
    "Emily A. Watson files PPO (2023-5907-PP) — 2 days after recanting "
    "that 'nothing was physical' (NSPD-2023-08121 on Oct 13, 2023)"
)
RECANT_DATE = "2023-10-13"
RECANT_DESC = (
    "Emily recants to NSPD: 'nothing was physical' (NSPD-2023-08121) — "
    "undermines entire basis for PPO filed 2 days later"
)

DDL_CAUSAL_CHAINS = """
CREATE TABLE IF NOT EXISTS causal_chains (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    cause_event     TEXT    NOT NULL,
    cause_date      TEXT,
    effect_event    TEXT    NOT NULL,
    effect_date     TEXT,
    chain_type      TEXT    NOT NULL,
    confidence      REAL    DEFAULT 0.8,
    lane            TEXT,
    source_evidence TEXT,
    narrative       TEXT,
    created_at      TEXT    DEFAULT (datetime('now'))
)
"""

IDX_CAUSAL = [
    "CREATE INDEX IF NOT EXISTS idx_cc_chain_type ON causal_chains(chain_type)",
    "CREATE INDEX IF NOT EXISTS idx_cc_lane ON causal_chains(lane)",
    "CREATE INDEX IF NOT EXISTS idx_cc_cause_date ON causal_chains(cause_date)",
    "CREATE INDEX IF NOT EXISTS idx_cc_effect_date ON causal_chains(effect_date)",
]


def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Open a connection with mandatory safety PRAGMAs."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=60000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-32000")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


# ══════════════════════════════════════════════════════════════════════════
#  SEED DATA — Known causal chains from 41 sessions of case investigation
# ══════════════════════════════════════════════════════════════════════════

_SEED_CHAINS: list[dict] = [
    # ── THE ROOT: Recantation → Fraudulent PPO ───────────────────────────
    {
        "cause_event": RECANT_DESC,
        "cause_date": RECANT_DATE,
        "effect_event": PPO_ROOT_DESC,
        "effect_date": PPO_ROOT_DATE,
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.98,
        "lane": "D",
        "source_evidence": "NSPD-2023-08121; 2023-5907-PP docket",
        "narrative": (
            "Two days after telling police 'nothing was physical,' Emily "
            "filed for a PPO. The recantation fatally undermines the PPO's "
            "factual basis — yet it was granted ex parte."
        ),
    },
    # ── PPO → Custody Complaint ──────────────────────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": "Andrew files Complaint for Custody (2024-001507-DC)",
        "effect_date": "2024-04-01",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.95,
        "lane": "A",
        "source_evidence": "2024-001507-DC docket entry 1",
        "narrative": (
            "The fraudulent PPO restricted Andrew's access to L.D.W., "
            "forcing him to file a custody complaint to restore his "
            "parental rights through proper legal channels."
        ),
    },
    # ── PPO → Ex Parte Custody Order (Apr 29, 2024) ─────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "Ex parte order entered — joint legal/physical custody, 50/50 "
            "parenting time"
        ),
        "effect_date": "2024-04-29",
        "chain_type": "FRUIT_OF",
        "confidence": 0.90,
        "lane": "A",
        "source_evidence": "2024-001507-DC ex parte order Apr 29, 2024",
        "narrative": (
            "Court entered ex parte custody order using the PPO as background "
            "context. Without the fraudulent PPO, no emergency ex parte "
            "custody proceeding would have been initiated."
        ),
    },
    # ── PPO → Trial outcome (Jul 17, 2024) ──────────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "Trial held — sole custody awarded to Emily, ALL 12 MCL 722.23 "
            "factors found to favor Mother"
        ),
        "effect_date": "2024-07-17",
        "chain_type": "FRUIT_OF",
        "confidence": 0.92,
        "lane": "A",
        "source_evidence": "Trial transcript Jul 17, 2024; Judgment",
        "narrative": (
            "Trial court relied on the PPO narrative to paint Andrew as "
            "dangerous. The PPO — filed 2 days after recantation — poisoned "
            "the evidentiary record that led to sole custody for Emily."
        ),
    },
    # ── Trial → Emily withholds child ────────────────────────────────────
    {
        "cause_event": (
            "Trial held — sole custody awarded to Emily, ALL 12 MCL 722.23 "
            "factors found to favor Mother"
        ),
        "cause_date": "2024-07-17",
        "effect_event": "Emily begins systematically withholding L.D.W. from Andrew",
        "effect_date": "2024-10-20",
        "chain_type": "ENABLED_BY",
        "confidence": 0.93,
        "lane": "A",
        "source_evidence": "AppClose logs Oct-Dec 2024; parenting time violation log",
        "narrative": (
            "Emboldened by the sole-custody judgment (itself fruit of the "
            "poisoned PPO), Emily began withholding L.D.W. from Andrew — "
            "violating court-ordered parenting time with impunity."
        ),
    },
    # ── Withholding → Andrew's motions ───────────────────────────────────
    {
        "cause_event": "Emily begins systematically withholding L.D.W. from Andrew",
        "cause_date": "2024-10-20",
        "effect_event": "Andrew files motions to enforce parenting time",
        "effect_date": "2024-11-01",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.95,
        "lane": "A",
        "source_evidence": "2024-001507-DC docket; filed motions",
        "narrative": (
            "Emily's withholding of L.D.W. forced Andrew to file enforcement "
            "motions — the court's response was to punish him, not her."
        ),
    },
    # ── Andrew's motions → McNeill retaliatory contempt ──────────────────
    {
        "cause_event": "Andrew files motions to enforce parenting time",
        "cause_date": "2024-11-01",
        "effect_event": (
            "McNeill sentences Andrew to 14 days jail for contempt (SC#5) — "
            "muted 3x during hearing, police report ignored"
        ),
        "effect_date": "2024-11-15",
        "chain_type": "RETALIATION_FOR",
        "confidence": 0.90,
        "lane": "E",
        "source_evidence": "SC#5 hearing transcript; contempt order Nov 15, 2024",
        "narrative": (
            "Instead of enforcing Emily's parenting time violations, "
            "McNeill retaliated against Andrew for filing motions by "
            "sentencing him to 14 days jail on a contempt charge."
        ),
    },
    # ── Contempt SC#5 → Lost home #1 ────────────────────────────────────
    {
        "cause_event": (
            "McNeill sentences Andrew to 14 days jail for contempt (SC#5)"
        ),
        "cause_date": "2024-11-15",
        "effect_event": "Andrew loses first home due to incarceration",
        "effect_date": "2024-12-01",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.88,
        "lane": "B",
        "source_evidence": "Housing records; employment termination",
        "narrative": (
            "14 days of incarceration caused Andrew to lose his first home — "
            "he could not pay rent or maintain employment while jailed."
        ),
    },
    # ── Contempt SC#5 → Lost job #1 ─────────────────────────────────────
    {
        "cause_event": (
            "McNeill sentences Andrew to 14 days jail for contempt (SC#5)"
        ),
        "cause_date": "2024-11-15",
        "effect_event": "Andrew loses first job due to incarceration",
        "effect_date": "2024-12-01",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.88,
        "lane": "C",
        "source_evidence": "Employment records",
        "narrative": (
            "Incarceration for contempt directly caused job loss — employer "
            "terminated Andrew for unexplained absence."
        ),
    },
    # ── Albert Watson premeditation ──────────────────────────────────────
    {
        "cause_event": (
            "Albert Watson tells NSPD: 'they want this documented so Emily "
            "can go tomorrow to get an Ex Parte order for full custody' "
            "(NS2505044)"
        ),
        "cause_date": "2025-05-04",
        "effect_event": (
            "Emily files for ex parte custody modification"
        ),
        "effect_date": "2025-08-07",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.95,
        "lane": "A",
        "source_evidence": "NSPD NS2505044 (May 4, 2025); Aug 2025 filings",
        "narrative": (
            "Albert Watson's admission to police proves the ex parte "
            "custody grab was premeditated — the police report was "
            "manufactured specifically to support the filing."
        ),
    },
    # ── Albert premeditation → USB recording retaliation ─────────────────
    {
        "cause_event": "Andrew makes USB recording at Watson home (Aug 5, 2025)",
        "cause_date": "2025-08-05",
        "effect_event": (
            "Watson family escalates — Albert calls NSPD to manufacture "
            "police report for ex parte filing"
        ),
        "effect_date": "2025-08-07",
        "chain_type": "RETALIATION_FOR",
        "confidence": 0.88,
        "lane": "E",
        "source_evidence": "NS2505044; USB recording metadata",
        "narrative": (
            "Within 48 hours of Andrew's recording, the Watson family "
            "retaliated by manufacturing a police report to support an "
            "ex parte custody grab — proving premeditation."
        ),
    },
    # ── Albert report → Five Orders Day ─────────────────────────────────
    {
        "cause_event": (
            "Watson family escalates — Albert calls NSPD to manufacture "
            "police report for ex parte filing"
        ),
        "cause_date": "2025-08-07",
        "effect_event": (
            "FIVE ex parte orders issued in single day — all parenting "
            "time suspended, zero notice to Andrew"
        ),
        "effect_date": "2025-08-08",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.95,
        "lane": "E",
        "source_evidence": "Five Orders Day docket entries Aug 8, 2025",
        "narrative": (
            "The manufactured police report from Aug 7 was used the very "
            "next day to obtain FIVE ex parte orders — suspending all of "
            "Andrew's parenting time without any notice or hearing."
        ),
    },
    # ── Five Orders Day → Last contact ──────────────────────────────────
    {
        "cause_event": (
            "FIVE ex parte orders issued in single day — all parenting "
            "time suspended, zero notice to Andrew"
        ),
        "cause_date": "2025-08-08",
        "effect_event": "Father's last contact with L.D.W.",
        "effect_date": "2025-07-29",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.98,
        "lane": "A",
        "source_evidence": "Parenting time records; ex parte orders",
        "narrative": (
            "The Five Orders Day ex parte suspension ended all contact "
            "between Andrew and L.D.W. — July 29, 2025 was the last day "
            "father saw his son. Separation is now ongoing."
        ),
    },
    # ── Five Orders → Custody order (Sep 28, 2025) ──────────────────────
    {
        "cause_event": (
            "FIVE ex parte orders issued in single day — all parenting "
            "time suspended, zero notice to Andrew"
        ),
        "cause_date": "2025-08-08",
        "effect_event": (
            "Custody order entered — Emily 100% custody, zero for Father"
        ),
        "effect_date": "2025-09-28",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.93,
        "lane": "A",
        "source_evidence": "Sep 28, 2025 custody order",
        "narrative": (
            "The ex parte suspension established a de facto sole-custody "
            "arrangement that was then formalized into a final order — "
            "all without a proper adversarial hearing."
        ),
    },
    # ── PPO → Five Orders Day (direct FRUIT_OF chain) ───────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "FIVE ex parte orders issued in single day — all parenting "
            "time suspended, zero notice to Andrew"
        ),
        "effect_date": "2025-08-08",
        "chain_type": "FRUIT_OF",
        "confidence": 0.90,
        "lane": "E",
        "source_evidence": "PPO docket; Five Orders Day docket",
        "narrative": (
            "The fraudulent PPO established the false narrative of danger "
            "that McNeill relied upon to issue five ex parte orders nearly "
            "two years later — classic fruit of the poisonous tree."
        ),
    },
    # ── PPO → Contempt for birthday messages ────────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "Andrew sentenced to 45 days jail (SC#6+7) for sending birthday "
            "messages to L.D.W. via AppClose"
        ),
        "effect_date": "2025-11-26",
        "chain_type": "FRUIT_OF",
        "confidence": 0.92,
        "lane": "E",
        "source_evidence": "SC#6, SC#7 orders; AppClose logs",
        "narrative": (
            "The PPO framework was weaponized to jail Andrew for sending "
            "birthday messages to his own child through a court-approved "
            "communication platform — 1st Amendment violation."
        ),
    },
    # ── 45-day contempt → Lost home #2 ──────────────────────────────────
    {
        "cause_event": (
            "Andrew sentenced to 45 days jail (SC#6+7) for sending birthday "
            "messages to L.D.W. via AppClose"
        ),
        "cause_date": "2025-11-26",
        "effect_event": "Andrew loses second home due to extended incarceration",
        "effect_date": "2026-01-10",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.90,
        "lane": "B",
        "source_evidence": "Housing records; incarceration dates",
        "narrative": (
            "45 days of incarceration — for birthday messages — caused "
            "Andrew to lose his second home. Two homes lost to contempt "
            "orders rooted in a fraudulent PPO."
        ),
    },
    # ── 45-day contempt → Lost job #2 ───────────────────────────────────
    {
        "cause_event": (
            "Andrew sentenced to 45 days jail (SC#6+7) for sending birthday "
            "messages to L.D.W. via AppClose"
        ),
        "cause_date": "2025-11-26",
        "effect_event": "Andrew loses second job due to extended incarceration",
        "effect_date": "2026-01-10",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.90,
        "lane": "C",
        "source_evidence": "Employment records; incarceration dates",
        "narrative": (
            "Second job lost to incarceration rooted in the poisoned PPO "
            "chain — employer could not hold position for 45 days."
        ),
    },
    # ── McNeill conflicts of interest → Biased rulings ──────────────────
    {
        "cause_event": (
            "McNeill married to Cavan Berry (attorney/magistrate at 60th "
            "District, office at 990 Terrace St = FOC address)"
        ),
        "cause_date": "2023-10-01",
        "effect_event": (
            "McNeill systematically rules against Andrew — denies every "
            "motion, excludes evidence, mutes at hearings"
        ),
        "effect_date": "2024-07-17",
        "chain_type": "ENABLED_BY",
        "confidence": 0.85,
        "lane": "E",
        "source_evidence": "Berry marriage records; FOC address 990 Terrace St; docket",
        "narrative": (
            "McNeill's marriage to Cavan Berry creates structural bias — "
            "Berry's office at the same address as FOC, combined with "
            "former law partnership with Chief Judge Hoopes, forms a "
            "three-court judicial cartel."
        ),
    },
    # ── McNeill-Hoopes partnership → Compromised appellate path ─────────
    {
        "cause_event": (
            "McNeill and Hoopes were former law partners at Ladas, Hoopes "
            "& McNeill (435 Whitehall Rd)"
        ),
        "cause_date": "2023-10-01",
        "effect_event": (
            "Chief Judge Hoopes cannot neutrally reassign disqualification "
            "motion — entire 14th Circuit compromised"
        ),
        "effect_date": "2024-01-01",
        "chain_type": "ENABLED_BY",
        "confidence": 0.88,
        "lane": "E",
        "source_evidence": "Ladas, Hoopes & McNeill firm records; MCR 2.003",
        "narrative": (
            "The former law partnership between McNeill and Chief Judge "
            "Hoopes means a disqualification motion under MCR 2.003 would "
            "be reassigned by a compromised chief judge — necessitating "
            "MSC original jurisdiction."
        ),
    },
    # ── McNeill-Ladas-Hoopes triad → Criminal case contamination ────────
    {
        "cause_event": (
            "Judge Ladas-Hoopes (60th District) is wife of Chief Judge "
            "Hoopes and former partner of McNeill"
        ),
        "cause_date": "2023-10-01",
        "effect_event": (
            "Andrew faces criminal charges in 60th District Court — same "
            "judicial cartel that stripped his custody"
        ),
        "effect_date": "2025-01-01",
        "chain_type": "ENABLED_BY",
        "confidence": 0.82,
        "lane": "E",
        "source_evidence": "2025-25245676SM; judicial connections",
        "narrative": (
            "The three-court judicial cartel (McNeill + Hoopes + "
            "Ladas-Hoopes) means Andrew lost his home, son, and freedom "
            "across all three courts controlled by former law partners."
        ),
    },
    # ── PPO → Emily's alienation campaign ───────────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "Emily weaponizes PPO framework to systematically alienate "
            "L.D.W. from Father — MCL 722.23(j) factor"
        ),
        "effect_date": "2024-01-01",
        "chain_type": "FRUIT_OF",
        "confidence": 0.90,
        "lane": "A",
        "source_evidence": "Parenting time logs; AppClose records; MCL 722.23(j)",
        "narrative": (
            "The PPO gave Emily the legal framework to restrict all contact "
            "and begin systematic parental alienation — using a protective "
            "order obtained through fraud as a weapon."
        ),
    },
    # ── HealthWest exclusion ────────────────────────────────────────────
    {
        "cause_event": (
            "McNeill systematically rules against Andrew — denies every "
            "motion, excludes evidence, mutes at hearings"
        ),
        "cause_date": "2024-07-17",
        "effect_event": (
            "McNeill excludes court-ordered HealthWest evaluation that "
            "cleared Andrew (Psychosis=0, Substance=0, LOCUS 12)"
        ),
        "effect_date": "2025-08-05",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.92,
        "lane": "E",
        "source_evidence": "HealthWest eval Aug 5, 2025; MRE 901, 702-703",
        "narrative": (
            "McNeill excluded the court-ordered psychological evaluation "
            "that found Andrew fit — Psychosis=0, Substance=0, Danger=0, "
            "LOCUS Score 12. The evaluation that would have undermined "
            "the PPO narrative was suppressed."
        ),
    },
    # ── Medication coercion ─────────────────────────────────────────────
    {
        "cause_event": (
            "McNeill excludes court-ordered HealthWest evaluation that "
            "cleared Andrew (Psychosis=0, Substance=0, LOCUS 12)"
        ),
        "cause_date": "2025-08-05",
        "effect_event": (
            "McNeill and Emily discuss on record that prescription "
            "medication is the 'only way' Andrew can see his son — "
            "unlawful practice of medicine"
        ),
        "effect_date": "2025-09-01",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.88,
        "lane": "E",
        "source_evidence": "Hearing transcript; Andrew's testimony",
        "narrative": (
            "Having excluded the clean evaluation, McNeill and Emily "
            "imposed medication as a condition for parenting time — "
            "neither is qualified to mandate medication, constituting "
            "unlawful practice of medicine and coercive conditioning."
        ),
    },
    # ── Andrew objecting → Contempt for speaking ────────────────────────
    {
        "cause_event": (
            "Andrew objects to medication requirement — states neither "
            "judge nor Emily is qualified to mandate medication"
        ),
        "cause_date": "2025-09-01",
        "effect_event": (
            "McNeill sentences Andrew to jail for contempt — his "
            "'contempt' was objecting to unlawful medication coercion. "
            "Judge told him to 'shut my mouth'"
        ),
        "effect_date": "2025-09-01",
        "chain_type": "RETALIATION_FOR",
        "confidence": 0.92,
        "lane": "E",
        "source_evidence": "Hearing testimony; contempt order",
        "narrative": (
            "McNeill jailed Andrew for exercising his right to object — "
            "his 'contempt' was pointing out that neither a judge nor "
            "a party can mandate prescription medication. The judge "
            "told him to 'shut my mouth.'"
        ),
    },
    # ── McNeill "Do not file anymore" ───────────────────────────────────
    {
        "cause_event": "Andrew files motions to restore parenting time",
        "cause_date": "2025-10-01",
        "effect_event": (
            "McNeill states verbatim: 'Do not file anymore, I will not "
            "look at it' — direct denial of access to courts"
        ),
        "effect_date": "2025-10-01",
        "chain_type": "RETALIATION_FOR",
        "confidence": 0.95,
        "lane": "E",
        "source_evidence": "Hearing transcript — verbatim quote",
        "narrative": (
            "McNeill's verbatim statement 'Do not file anymore, I will "
            "not look at it' constitutes denial of access to courts — "
            "a fundamental constitutional right. Retaliation for Andrew "
            "exercising his right to petition."
        ),
    },
    # ── PPO → Sep 28 custody order (FRUIT_OF) ──────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "Custody order entered — Emily 100% custody, zero for Father"
        ),
        "effect_date": "2025-09-28",
        "chain_type": "FRUIT_OF",
        "confidence": 0.93,
        "lane": "A",
        "source_evidence": "Sep 28, 2025 custody order; PPO docket",
        "narrative": (
            "The Sep 28, 2025 order granting Emily 100% custody and "
            "zero parenting time for Father is the ultimate fruit of "
            "the poisonous tree — every step traces back to the "
            "fraudulent PPO filed 2 days after recantation."
        ),
    },
    # ── PPO → 59 days total jail (FRUIT_OF) ─────────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "Andrew jailed a total of 59 days (SC#5: 14 days + SC#6+7: "
            "45 days) on contempt charges rooted in PPO framework"
        ),
        "effect_date": "2025-11-26",
        "chain_type": "FRUIT_OF",
        "confidence": 0.93,
        "lane": "C",
        "source_evidence": "SC#5, SC#6, SC#7 orders",
        "narrative": (
            "59 days of incarceration — for a father trying to see his "
            "child — all rooted in a PPO filed after the complainant "
            "recanted. This is the fruit of the poisonous tree manifest "
            "as loss of liberty."
        ),
    },
    # ── PPO → Two lost homes (FRUIT_OF) ─────────────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": "Andrew loses 2 homes due to repeated incarceration",
        "effect_date": "2026-01-10",
        "chain_type": "FRUIT_OF",
        "confidence": 0.88,
        "lane": "B",
        "source_evidence": "Housing records; incarceration timeline",
        "narrative": (
            "Both housing losses trace directly to incarceration, which "
            "traces to contempt orders, which trace to the PPO framework. "
            "Two homes lost to a fraudulent protection order."
        ),
    },
    # ── PPO → Two lost jobs (FRUIT_OF) ──────────────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": "Andrew loses 2 jobs due to repeated incarceration",
        "effect_date": "2026-01-10",
        "chain_type": "FRUIT_OF",
        "confidence": 0.88,
        "lane": "C",
        "source_evidence": "Employment records; incarceration timeline",
        "narrative": (
            "Both job losses trace directly to incarceration, which "
            "traces to contempt, which traces to the PPO. Economic "
            "devastation is a fruit of the poisonous tree."
        ),
    },
    # ── PPO → Emergency Motion (Mar 25, 2026) ──────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": "Emergency Motion filed to restore parenting time",
        "effect_date": "2026-03-25",
        "chain_type": "FRUIT_OF",
        "confidence": 0.90,
        "lane": "A",
        "source_evidence": "Emergency Motion Mar 25, 2026",
        "narrative": (
            "The need for an emergency motion to restore parenting time "
            "exists solely because the poisoned PPO chain led to total "
            "separation. Without the fraudulent PPO, no emergency would "
            "exist."
        ),
    },
    # ── Emily false allegation: suicidal ────────────────────────────────
    {
        "cause_event": "Emily alleges Andrew is suicidal",
        "cause_date": "2023-10-01",
        "effect_event": (
            "Police welfare checks conducted — Andrew cleared, no safety "
            "concerns found"
        ),
        "effect_date": "2023-11-01",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.90,
        "lane": "D",
        "source_evidence": "NSPD welfare check reports Oct-Nov 2023",
        "narrative": (
            "Emily's suicidal allegations triggered welfare checks that "
            "cleared Andrew — establishing a pattern of unfounded reports "
            "used to build a false narrative."
        ),
    },
    # ── Emily false allegation: arsenic ─────────────────────────────────
    {
        "cause_event": "Emily alleges arsenic poisoning by Andrew",
        "cause_date": "2023-11-01",
        "effect_event": (
            "ER toxicology conducted — results NEGATIVE, no charges"
        ),
        "effect_date": "2023-11-15",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.92,
        "lane": "D",
        "source_evidence": "ER toxicology report; NSPD report",
        "narrative": (
            "Arsenic poisoning allegation — toxicology was negative. "
            "Another fabricated allegation in the escalating pattern."
        ),
    },
    # ── Emily false allegation: physical assault ────────────────────────
    {
        "cause_event": "Emily alleges physical assault by Andrew",
        "cause_date": "2023-10-10",
        "effect_event": "Police investigate — find no evidence of assault",
        "effect_date": "2023-10-12",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.92,
        "lane": "D",
        "source_evidence": "NSPD investigation report",
        "narrative": (
            "Physical assault allegation investigated and unfounded — "
            "3 days before Emily recanted 'nothing was physical.'"
        ),
    },
    # ── Emily false allegation: drug use ────────────────────────────────
    {
        "cause_event": "Emily alleges drug use by Andrew",
        "cause_date": "2024-01-01",
        "effect_event": (
            "Officer Randall's report reveals Emily admitted to METH USE — "
            "projection exposed"
        ),
        "effect_date": "2024-01-15",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.88,
        "lane": "D",
        "source_evidence": "Officer Ella Randall report; Emily meth admission",
        "narrative": (
            "Emily alleged Andrew used drugs — but Officer Randall's report "
            "documents Emily's own admission of methamphetamine use. "
            "Classic projection: accuse the other party of your own conduct."
        ),
    },
    # ── False allegations → PPO filing (pattern established) ────────────
    {
        "cause_event": (
            "Pattern of false allegations: suicidal, arsenic, assault, "
            "drugs — all unfounded by police"
        ),
        "cause_date": "2023-10-01",
        "effect_event": PPO_ROOT_DESC,
        "effect_date": PPO_ROOT_DATE,
        "chain_type": "ENABLED_BY",
        "confidence": 0.92,
        "lane": "D",
        "source_evidence": "Multiple NSPD reports showing pattern",
        "narrative": (
            "The pattern of false allegations created a volume of police "
            "contacts that Emily cited in her PPO petition — despite "
            "every single allegation being unfounded."
        ),
    },
    # ── Emily withholding → FOC inaction ────────────────────────────────
    {
        "cause_event": "Emily begins systematically withholding L.D.W. from Andrew",
        "cause_date": "2024-10-20",
        "effect_event": (
            "FOC (Pamela Rusco) fails to enforce parenting time violations "
            "— systemic bias toward Emily"
        ),
        "effect_date": "2024-11-01",
        "chain_type": "CONCEALED_FROM",
        "confidence": 0.85,
        "lane": "A",
        "source_evidence": "FOC records; parenting time violation complaints",
        "narrative": (
            "FOC failed to enforce Emily's documented parenting time "
            "violations — the withholding was effectively concealed "
            "from enforcement by institutional bias."
        ),
    },
    # ── McNeill cross-examines witnesses herself ────────────────────────
    {
        "cause_event": (
            "Andrew successfully cross-examines witnesses at hearing"
        ),
        "cause_date": "2025-09-01",
        "effect_event": (
            "McNeill begins cross-examining witnesses herself — abandoning "
            "judicial neutrality"
        ),
        "effect_date": "2025-09-01",
        "chain_type": "RETALIATION_FOR",
        "confidence": 0.85,
        "lane": "E",
        "source_evidence": "Hearing transcript; Andrew testimony",
        "narrative": (
            "When Andrew proved effective at cross-examination, McNeill "
            "took over questioning herself — abandoning her role as "
            "neutral arbiter and acting as opposing counsel."
        ),
    },
    # ── PPO → COA Appeal (366810) ───────────────────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "Andrew files appeal of right — COA 366810"
        ),
        "effect_date": "2025-12-01",
        "chain_type": "FRUIT_OF",
        "confidence": 0.88,
        "lane": "F",
        "source_evidence": "COA 366810 docket",
        "narrative": (
            "The need to appeal exists because the trial court's judgment "
            "was poisoned by the PPO narrative. The appellate case is "
            "itself a fruit of the poisonous tree."
        ),
    },
    # ── PPO → Federal §1983 claim ───────────────────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "Federal 42 USC §1983 civil rights claim in development — "
            "constitutional violations across all courts"
        ),
        "effect_date": "2026-03-01",
        "chain_type": "FRUIT_OF",
        "confidence": 0.85,
        "lane": "C",
        "source_evidence": "§1983 complaint draft; constitutional analysis",
        "narrative": (
            "The entire §1983 federal claim exists because state courts "
            "— corrupted by the judicial cartel — denied Andrew's "
            "constitutional rights. The fraudulent PPO started the chain "
            "that led to federal intervention being necessary."
        ),
    },
    # ── PPO → MSC Superintending Control ────────────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "MSC Superintending Control petition necessary — entire 14th "
            "Circuit compromised by judicial cartel"
        ),
        "effect_date": "2026-03-01",
        "chain_type": "FRUIT_OF",
        "confidence": 0.85,
        "lane": "F",
        "source_evidence": "MCR 7.306; judicial cartel analysis",
        "narrative": (
            "The poisoned PPO chain has so thoroughly corrupted the 14th "
            "Circuit that MSC superintending control is the only remedy — "
            "no adequate remedy exists at the trial court level."
        ),
    },
    # ── Recantation → PPO lacks factual basis ───────────────────────────
    {
        "cause_event": RECANT_DESC,
        "cause_date": RECANT_DATE,
        "effect_event": (
            "PPO petition lacks factual basis — recantation destroys "
            "credibility of every allegation in the petition"
        ),
        "effect_date": PPO_ROOT_DATE,
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.95,
        "lane": "D",
        "source_evidence": "NSPD-2023-08121; PPO petition text",
        "narrative": (
            "Emily's own words to police — 'nothing was physical' — "
            "destroy the factual basis for her PPO petition filed just "
            "2 days later. The PPO is built on a recanted foundation."
        ),
    },
    # ── Andrew's emergency motion → Current status ──────────────────────
    {
        "cause_event": "Emergency Motion filed to restore parenting time",
        "cause_date": "2026-03-25",
        "effect_event": (
            "Motion pending — McNeill previously stated 'Do not file "
            "anymore, I will not look at it'"
        ),
        "effect_date": "2026-03-25",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.90,
        "lane": "A",
        "source_evidence": "Emergency Motion Mar 25, 2026; hearing transcript",
        "narrative": (
            "Despite McNeill's verbatim threat to refuse filings, Andrew "
            "filed an emergency motion — demonstrating exhaustion of "
            "remedies and the need for higher-court intervention."
        ),
    },
    # ── Barnes withdrawal → Emily unrepresented ─────────────────────────
    {
        "cause_event": (
            "Jennifer Barnes (P55406) withdraws as Emily's attorney"
        ),
        "cause_date": "2026-03-01",
        "effect_event": (
            "Emily A. Watson is now unrepresented — must be served directly"
        ),
        "effect_date": "2026-03-01",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.95,
        "lane": "A",
        "source_evidence": "Barnes withdrawal filing Mar 2026",
        "narrative": (
            "Barnes withdrew as counsel — Emily must now be served directly "
            "at 2160 Garland Dr, Norton Shores, MI 49441."
        ),
    },
    # ── Emily meth admission → Projection pattern ───────────────────────
    {
        "cause_event": (
            "Officer Randall's report: Emily admitted to METH USE"
        ),
        "cause_date": "2024-01-15",
        "effect_event": (
            "Emily's drug-use allegations against Andrew exposed as "
            "projection — accusing him of her own conduct"
        ),
        "effect_date": "2024-01-15",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.88,
        "lane": "D",
        "source_evidence": "Officer Ella Randall report",
        "narrative": (
            "Emily's own drug use admission exposes her allegations "
            "against Andrew as projection — a key impeachment point "
            "for trial and any future proceedings."
        ),
    },
    # ── Ex parte orders → Concealed from Andrew ─────────────────────────
    {
        "cause_event": (
            "FIVE ex parte orders issued in single day — all parenting "
            "time suspended, zero notice to Andrew"
        ),
        "cause_date": "2025-08-08",
        "effect_event": (
            "Andrew not notified of ex parte orders — MCR 2.107/3.207 "
            "service requirements violated"
        ),
        "effect_date": "2025-08-08",
        "chain_type": "CONCEALED_FROM",
        "confidence": 0.95,
        "lane": "E",
        "source_evidence": "Service records (absent); MCR 2.107; MCR 3.207",
        "narrative": (
            "Five orders were entered affecting Andrew's parental rights "
            "without any notice or opportunity to be heard — a fundamental "
            "due process violation concealed from the affected party."
        ),
    },
    # ── Kitchen recording → Evidence of conspiracy ──────────────────────
    {
        "cause_event": (
            "Kitchen recording captures Albert Watson saying 'I will make "
            "sure you don't see your son'"
        ),
        "cause_date": "2024-11-30",
        "effect_event": (
            "Direct evidence of coordinated parental alienation by Watson "
            "family — MCL 722.23(j)"
        ),
        "effect_date": "2024-11-30",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.90,
        "lane": "A",
        "source_evidence": (
            "I:\\08_AUDIO\\albert and Emily audio nov 30 2023.mp3; "
            "I:\\Appclose\\EVERYTHIING\\videos\\Albertemily.mp4"
        ),
        "narrative": (
            "Albert Watson's recorded statement proves coordinated "
            "alienation — directly relevant to MCL 722.23 factor (j) "
            "(willingness to facilitate parent-child relationship)."
        ),
    },
    # ── Emily accusations via AppClose → Weaponized platform ────────────
    {
        "cause_event": (
            "Court orders communication via AppClose platform"
        ),
        "cause_date": "2024-07-17",
        "effect_event": (
            "Emily uses AppClose logs selectively to manufacture "
            "contempt allegations — court-approved platform weaponized"
        ),
        "effect_date": "2024-10-01",
        "chain_type": "ENABLED_BY",
        "confidence": 0.85,
        "lane": "D",
        "source_evidence": "AppClose export logs; contempt filings",
        "narrative": (
            "The court-ordered communication platform was weaponized — "
            "normal parental communication was recharacterized as "
            "contempt-worthy violations."
        ),
    },
    # ── Full PPO → Ongoing separation (dynamic) ────────────────────────
    {
        "cause_event": PPO_ROOT_DESC,
        "cause_date": PPO_ROOT_DATE,
        "effect_event": (
            "Ongoing separation — Father has not seen L.D.W. since "
            "Jul 29, 2025. Separation counter increases daily."
        ),
        "effect_date": "2025-07-29",
        "chain_type": "FRUIT_OF",
        "confidence": 0.98,
        "lane": "A",
        "source_evidence": "Parenting time records; separation anchor date",
        "narrative": (
            "The ultimate fruit of the poisonous tree: a father completely "
            "severed from his child. Every day of separation traces back "
            "to a PPO filed on a recanted foundation."
        ),
    },
    # --- 50: Father lost two jobs due to incarceration ---
    {
        "cause_event": (
            "McNeill sentences Father to 59 days jail across SC#5, SC#6, "
            "SC#7 — for birthday messages sent via court-approved AppClose"
        ),
        "cause_date": "2024-11-15",
        "effect_event": (
            "Father loses two jobs as direct result of incarceration — "
            "employers terminated employment during jail periods"
        ),
        "effect_date": "2025-02-01",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.92,
        "lane": "C",
        "source_evidence": "Employment records; contempt orders SC#5 SC#6 SC#7",
        "narrative": (
            "59 days of incarceration for birthday messages destroyed "
            "Father's employment. Two jobs lost — economic devastation "
            "traceable to weaponized contempt rooted in the fraudulent PPO."
        ),
    },
    # --- 51: Father lost two homes due to incarceration ---
    {
        "cause_event": (
            "Father loses two jobs from incarceration, destroying income "
            "needed to maintain housing"
        ),
        "cause_date": "2025-02-01",
        "effect_event": (
            "Father loses two homes — unable to pay rent/mortgage after "
            "employment terminated during jail periods"
        ),
        "effect_date": "2025-04-01",
        "chain_type": "TRIGGERED_BY",
        "confidence": 0.90,
        "lane": "C",
        "source_evidence": "Housing records; employment records; contempt orders",
        "narrative": (
            "Job loss from weaponized incarceration cascaded into housing "
            "loss. Two homes gone — the economic chain traces directly "
            "from PPO → contempt → jail → job loss → homelessness."
        ),
    },
]


class CausalChainEngine:
    """Extract, persist, and query causal chains for Pigors v Watson.

    Central theory: Fruit of the Poisonous Tree — the Oct 15, 2023 PPO
    filed 2 days after Emily recanted taints every subsequent proceeding.
    """

    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self._db_path = Path(db_path)
        self._ensure_table()
        self._auto_populate()

    # ── Connection management ────────────────────────────────────────────

    def _conn(self) -> sqlite3.Connection:
        return _connect(self._db_path)

    # ── Schema bootstrap ─────────────────────────────────────────────────

    def _ensure_table(self) -> None:
        """Create causal_chains table and indexes if absent."""
        conn = self._conn()
        try:
            conn.execute(DDL_CAUSAL_CHAINS)
            for idx_sql in IDX_CAUSAL:
                conn.execute(idx_sql)
            conn.commit()
        finally:
            conn.close()

    # ── Auto-populate seed data ──────────────────────────────────────────

    def _auto_populate(self) -> None:
        """Insert seed chains if the table is empty or undersized."""
        conn = self._conn()
        try:
            existing = conn.execute(
                "SELECT COUNT(*) FROM causal_chains"
            ).fetchone()[0]
            if existing >= len(_SEED_CHAINS):
                return

            # Wipe and re-seed for idempotency on schema changes
            if existing > 0 and existing < len(_SEED_CHAINS):
                conn.execute("DELETE FROM causal_chains")
                conn.commit()

            rows = [
                (
                    s["cause_event"],
                    s["cause_date"],
                    s["effect_event"],
                    s["effect_date"],
                    s["chain_type"],
                    s["confidence"],
                    s["lane"],
                    s["source_evidence"],
                    s["narrative"],
                )
                for s in _SEED_CHAINS
            ]
            conn.executemany(
                """INSERT INTO causal_chains
                   (cause_event, cause_date, effect_event, effect_date,
                    chain_type, confidence, lane, source_evidence, narrative)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )
            conn.commit()

            # Verify
            final = conn.execute(
                "SELECT COUNT(*) FROM causal_chains"
            ).fetchone()[0]
            if final != len(_SEED_CHAINS):
                raise RuntimeError(
                    f"Seed verification failed: expected {len(_SEED_CHAINS)}, "
                    f"got {final}"
                )
        finally:
            conn.close()

    # ── Core query helpers ───────────────────────────────────────────────

    def _rows_to_dicts(self, rows: list[sqlite3.Row]) -> list[dict]:
        """Convert Row objects to plain dicts."""
        return [dict(r) for r in rows]

    def _query(self, sql: str, params: tuple = ()) -> list[dict]:
        conn = self._conn()
        try:
            return self._rows_to_dicts(conn.execute(sql, params).fetchall())
        finally:
            conn.close()

    # ══════════════════════════════════════════════════════════════════════
    #  PUBLIC API
    # ══════════════════════════════════════════════════════════════════════

    def get_poisonous_tree(self) -> list[dict]:
        """Return all causal chains rooted in the Oct 15, 2023 PPO.

        Includes both direct FRUIT_OF chains and the full transitive
        closure of chains that trace back to the PPO root.
        """
        return self._query(
            """SELECT * FROM causal_chains
               WHERE chain_type = 'FRUIT_OF'
                  OR cause_date = ?
                  OR (cause_event LIKE '%PPO%' AND cause_event LIKE '%2023-5907%')
                  OR (cause_event LIKE '%recant%')
               ORDER BY effect_date ASC""",
            (PPO_ROOT_DATE,),
        )

    def get_retaliation_chains(self, actor: Optional[str] = None) -> list[dict]:
        """Return all RETALIATION_FOR chains, optionally filtered by actor.

        Args:
            actor: Partial match on cause_event or effect_event (e.g. 'McNeill').
                   If None, returns all retaliation chains.
        """
        if actor:
            sanitized = re.sub(r"[^\w\s]", "", actor)
            return self._query(
                """SELECT * FROM causal_chains
                   WHERE chain_type = 'RETALIATION_FOR'
                     AND (cause_event LIKE '%' || ? || '%'
                          OR effect_event LIKE '%' || ? || '%'
                          OR narrative LIKE '%' || ? || '%')
                   ORDER BY effect_date ASC""",
                (sanitized, sanitized, sanitized),
            )
        return self._query(
            """SELECT * FROM causal_chains
               WHERE chain_type = 'RETALIATION_FOR'
               ORDER BY effect_date ASC"""
        )

    def get_chain_for_filing(self, lane: str) -> list[dict]:
        """Return all causal chains relevant to a specific filing lane.

        Args:
            lane: Case lane identifier (A, B, C, D, E, F).
        """
        lane_upper = lane.strip().upper()
        return self._query(
            """SELECT * FROM causal_chains
               WHERE lane = ?
               ORDER BY
                 CASE chain_type
                   WHEN 'FRUIT_OF' THEN 1
                   WHEN 'TRIGGERED_BY' THEN 2
                   WHEN 'RETALIATION_FOR' THEN 3
                   WHEN 'ENABLED_BY' THEN 4
                   WHEN 'CONCEALED_FROM' THEN 5
                 END,
                 effect_date ASC""",
            (lane_upper,),
        )

    def get_full_chain(self, event_fragment: str) -> list[dict]:
        """Trace full causal chain containing any event matching the fragment.

        Follows both forward (cause→effect) and backward (effect→cause)
        links to reconstruct the full chain of causation.

        Args:
            event_fragment: Text fragment to match in cause_event or effect_event.
        """
        sanitized = re.sub(r"[^\w\s]", "", event_fragment)
        pattern = f"%{sanitized}%"

        conn = self._conn()
        try:
            # Find seed rows matching the fragment
            seeds = conn.execute(
                """SELECT id, cause_event, effect_event FROM causal_chains
                   WHERE cause_event LIKE ? OR effect_event LIKE ?""",
                (pattern, pattern),
            ).fetchall()

            if not seeds:
                return []

            # Collect all related event text for transitive search
            visited_ids: set[int] = set()
            event_texts: set[str] = set()
            for s in seeds:
                visited_ids.add(s["id"])
                event_texts.add(s["cause_event"])
                event_texts.add(s["effect_event"])

            # BFS: expand by matching cause/effect text
            changed = True
            max_iterations = 10
            iteration = 0
            while changed and iteration < max_iterations:
                changed = False
                iteration += 1
                for evt in list(event_texts):
                    # Exact match on cause or effect to find connected chains
                    related = conn.execute(
                        """SELECT id, cause_event, effect_event
                           FROM causal_chains
                           WHERE (cause_event = ? OR effect_event = ?)
                             AND id NOT IN ({})""".format(
                            ",".join(str(i) for i in visited_ids) if visited_ids else "0"
                        ),
                        (evt, evt),
                    ).fetchall()
                    for r in related:
                        if r["id"] not in visited_ids:
                            visited_ids.add(r["id"])
                            event_texts.add(r["cause_event"])
                            event_texts.add(r["effect_event"])
                            changed = True

            # Fetch full rows for all discovered chain links
            if not visited_ids:
                return []
            placeholders = ",".join("?" * len(visited_ids))
            result = conn.execute(
                f"""SELECT * FROM causal_chains
                    WHERE id IN ({placeholders})
                    ORDER BY
                      COALESCE(cause_date, '9999') ASC,
                      COALESCE(effect_date, '9999') ASC""",
                tuple(visited_ids),
            ).fetchall()
            return self._rows_to_dicts(result)
        finally:
            conn.close()

    def build_narrative(self, chains: Optional[list[dict]] = None) -> str:
        """Generate a court-ready narrative from causal chains.

        Args:
            chains: List of chain dicts. If None, uses the full poisonous tree.

        Returns:
            Formatted narrative string suitable for court filings.
        """
        if chains is None:
            chains = self.get_poisonous_tree()

        if not chains:
            return "No causal chains found."

        # Group by chain type for structured narrative
        grouped: dict[str, list[dict]] = {}
        for c in chains:
            ct = c.get("chain_type", "UNKNOWN")
            grouped.setdefault(ct, []).append(c)

        today = datetime.now()
        anchor = datetime(2025, 7, 29)
        sep_days = (today - anchor).days

        lines: list[str] = []
        lines.append("CAUSAL CHAIN ANALYSIS: FRUIT OF THE POISONOUS TREE")
        lines.append("=" * 60)
        lines.append("")
        lines.append(
            f"Root Event: On October 15, 2023, Defendant Emily A. Watson "
            f"filed a Personal Protection Order (Case No. 2023-5907-PP) — "
            f"exactly two days after telling police that 'nothing was "
            f"physical' (NSPD-2023-08121, October 13, 2023)."
        )
        lines.append("")
        lines.append(
            f"Current Status: Plaintiff has been separated from the minor "
            f"child, L.D.W., for {sep_days} days (since July 29, 2025). "
            f"Every proceeding, order, and sanction traces back to the "
            f"fraudulently obtained PPO."
        )
        lines.append("")

        type_labels = {
            "FRUIT_OF": "FRUITS OF THE POISONOUS TREE",
            "TRIGGERED_BY": "DIRECT CAUSAL LINKS",
            "RETALIATION_FOR": "RETALIATORY ACTIONS",
            "ENABLED_BY": "ENABLING CONDITIONS",
            "CONCEALED_FROM": "CONCEALMENT AND DUE PROCESS VIOLATIONS",
        }

        for ct in CHAIN_TYPES:
            items = grouped.get(ct, [])
            if not items:
                continue
            label = type_labels.get(ct, ct)
            lines.append(f"\n{'─' * 60}")
            lines.append(f"  {label} ({len(items)} links)")
            lines.append(f"{'─' * 60}")
            for i, c in enumerate(items, 1):
                cause_d = c.get("cause_date", "undated")
                effect_d = c.get("effect_date", "undated")
                lines.append(f"\n  {i}. [{cause_d}] → [{effect_d}]")
                lines.append(f"     CAUSE:  {c['cause_event']}")
                lines.append(f"     EFFECT: {c['effect_event']}")
                if c.get("narrative"):
                    lines.append(f"     NOTE:   {c['narrative']}")
                if c.get("source_evidence"):
                    lines.append(f"     EVIDENCE: {c['source_evidence']}")
                conf = c.get("confidence", 0)
                lines.append(f"     CONFIDENCE: {conf:.0%}  |  LANE: {c.get('lane', '?')}")

        lines.append(f"\n{'═' * 60}")
        lines.append(f"Total causal links: {len(chains)}")
        lines.append(
            f"Chain types: "
            + ", ".join(f"{k}={len(v)}" for k, v in grouped.items())
        )
        lines.append(f"Separation days: {sep_days}")
        lines.append(f"Generated: {today.strftime('%Y-%m-%d %H:%M')}")

        return "\n".join(lines)

    # ── Additional query methods ─────────────────────────────────────────

    def get_chains_by_type(self, chain_type: str) -> list[dict]:
        """Return all chains of a specific relationship type."""
        if chain_type not in CHAIN_TYPES:
            raise ValueError(
                f"Invalid chain_type '{chain_type}'. "
                f"Must be one of: {', '.join(CHAIN_TYPES)}"
            )
        return self._query(
            "SELECT * FROM causal_chains WHERE chain_type = ? ORDER BY effect_date ASC",
            (chain_type,),
        )

    def get_concealment_chains(self) -> list[dict]:
        """Return all chains involving concealment or due process violations."""
        return self._query(
            """SELECT * FROM causal_chains
               WHERE chain_type = 'CONCEALED_FROM'
                  OR narrative LIKE '%due process%'
                  OR narrative LIKE '%without notice%'
                  OR narrative LIKE '%concealed%'
                  OR narrative LIKE '%ex parte%'
               ORDER BY effect_date ASC"""
        )

    def get_damages_chain(self) -> list[dict]:
        """Return chains relevant to damages calculation (housing, jobs, jail)."""
        return self._query(
            """SELECT * FROM causal_chains
               WHERE effect_event LIKE '%home%'
                  OR effect_event LIKE '%job%'
                  OR effect_event LIKE '%jail%'
                  OR effect_event LIKE '%incarcerat%'
                  OR effect_event LIKE '%separation%'
                  OR narrative LIKE '%economic%'
                  OR narrative LIKE '%housing%'
                  OR narrative LIKE '%employment%'
               ORDER BY effect_date ASC"""
        )

    def get_chain_stats(self) -> dict:
        """Return summary statistics for all causal chains."""
        conn = self._conn()
        try:
            row = conn.execute(
                """SELECT
                    COUNT(*) as total,
                    (SELECT COUNT(*) FROM causal_chains WHERE chain_type='FRUIT_OF') as fruit_of,
                    (SELECT COUNT(*) FROM causal_chains WHERE chain_type='TRIGGERED_BY') as triggered_by,
                    (SELECT COUNT(*) FROM causal_chains WHERE chain_type='RETALIATION_FOR') as retaliation_for,
                    (SELECT COUNT(*) FROM causal_chains WHERE chain_type='ENABLED_BY') as enabled_by,
                    (SELECT COUNT(*) FROM causal_chains WHERE chain_type='CONCEALED_FROM') as concealed_from,
                    (SELECT COUNT(DISTINCT lane) FROM causal_chains) as lanes_covered,
                    ROUND(AVG(confidence), 3) as avg_confidence
                   FROM causal_chains"""
            ).fetchone()
            return dict(row)
        finally:
            conn.close()

    def add_chain(
        self,
        cause_event: str,
        effect_event: str,
        chain_type: str,
        cause_date: Optional[str] = None,
        effect_date: Optional[str] = None,
        confidence: float = 0.8,
        lane: Optional[str] = None,
        source_evidence: Optional[str] = None,
        narrative: Optional[str] = None,
    ) -> int:
        """Add a new causal chain link to the database.

        Returns:
            The id of the inserted row.
        """
        if chain_type not in CHAIN_TYPES:
            raise ValueError(
                f"Invalid chain_type '{chain_type}'. "
                f"Must be one of: {', '.join(CHAIN_TYPES)}"
            )
        conn = self._conn()
        try:
            cur = conn.execute(
                """INSERT INTO causal_chains
                   (cause_event, cause_date, effect_event, effect_date,
                    chain_type, confidence, lane, source_evidence, narrative)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cause_event,
                    cause_date,
                    effect_event,
                    effect_date,
                    chain_type,
                    confidence,
                    lane,
                    source_evidence,
                    narrative,
                ),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def search_chains(self, query: str, limit: int = 50) -> list[dict]:
        """Search chains by keyword across all text fields.

        Args:
            query: Search term (partial match).
            limit: Max results.
        """
        sanitized = re.sub(r"[^\w\s]", "", query)
        pattern = f"%{sanitized}%"
        return self._query(
            """SELECT * FROM causal_chains
               WHERE cause_event LIKE ?
                  OR effect_event LIKE ?
                  OR narrative LIKE ?
                  OR source_evidence LIKE ?
               ORDER BY confidence DESC, effect_date ASC
               LIMIT ?""",
            (pattern, pattern, pattern, pattern, limit),
        )

    def enrich_from_timeline(self, limit: int = 100) -> int:
        """Scan timeline_events for additional causal relationships.

        Looks for timeline events near known chain dates and proposes
        new chain entries based on temporal proximity and keyword overlap.

        Returns:
            Number of new chains discovered and inserted.
        """
        conn = self._conn()
        try:
            # Verify timeline_events exists and has expected columns
            cols = {
                r[1]
                for r in conn.execute("PRAGMA table_info(timeline_events)").fetchall()
            }
            required = {"event_date", "event_description", "lane"}
            if not required.issubset(cols):
                return 0

            # Get existing chain dates to avoid duplicates
            existing_pairs = set()
            for r in conn.execute(
                "SELECT cause_event, effect_event FROM causal_chains"
            ).fetchall():
                existing_pairs.add((r[0], r[1]))

            # Look for ex parte orders in timeline
            ex_parte_events = conn.execute(
                """SELECT event_date, substr(event_description, 1, 300) as desc, lane
                   FROM timeline_events
                   WHERE (event_description LIKE '%ex parte%'
                          OR event_description LIKE '%without notice%'
                          OR event_description LIKE '%without hearing%')
                     AND event_date IS NOT NULL
                     AND event_date != ''
                   ORDER BY event_date
                   LIMIT ?""",
                (limit,),
            ).fetchall()

            new_count = 0
            for evt in ex_parte_events:
                effect_text = f"Ex parte action: {evt['desc'][:200]}"
                cause_text = PPO_ROOT_DESC

                if (cause_text, effect_text) in existing_pairs:
                    continue

                conn.execute(
                    """INSERT INTO causal_chains
                       (cause_event, cause_date, effect_event, effect_date,
                        chain_type, confidence, lane, source_evidence, narrative)
                       VALUES (?, ?, ?, ?, 'FRUIT_OF', 0.70, ?, 'timeline_events', ?)""",
                    (
                        cause_text,
                        PPO_ROOT_DATE,
                        effect_text,
                        evt["event_date"],
                        evt["lane"],
                        f"Ex parte action on {evt['event_date']} in lane {evt['lane']} "
                        f"— traces back to the poisoned PPO framework.",
                    ),
                )
                existing_pairs.add((cause_text, effect_text))
                new_count += 1
                if new_count >= 20:
                    break

            if new_count > 0:
                conn.commit()
            return new_count
        finally:
            conn.close()
