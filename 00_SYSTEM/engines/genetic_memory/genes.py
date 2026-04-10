"""Seed genes — pre-loaded critical litigation knowledge.

Seeds ~20 foundational genes into the genetic memory system.
These are verified facts, established patterns, and proven
strategies from the Pigors v Watson case.

Safe to call multiple times — uses INSERT OR IGNORE on gene content
to avoid duplicates.
"""

import sys
import os
import sqlite3
import logging
from datetime import datetime

sys.path.insert(0, r"C:\Users\andre\LitigationOS")

logger = logging.getLogger(__name__)

# ── Seed Data ─────────────────────────────────────────────────────────────

_SEED_GENES = [
    # ── Facts (verified, high confidence) ─────────────────────────────
    {
        "gene_type": "fact",
        "content": "Separation anchor date is July 29, 2025 — last contact with L.D.W.",
        "confidence": 0.99,
        "lane": "A",
        "tags": "separation,timeline,critical",
    },
    {
        "gene_type": "fact",
        "content": "Trial date was July 17, 2024 — judge found ALL 12 MCL 722.23 factors favor Mother",
        "confidence": 0.99,
        "lane": "A",
        "tags": "trial,custody,judgment",
    },
    {
        "gene_type": "fact",
        "content": "Albert Watson admitted premeditation in NSPD report NS2505044 on Aug 7, 2025",
        "confidence": 0.95,
        "lane": "A",
        "tags": "albert,premeditation,smoking_gun",
    },
    {
        "gene_type": "fact",
        "content": "Five ex parte orders issued on Aug 8, 2025 — one day after Albert's premeditation admission",
        "confidence": 0.95,
        "lane": "E",
        "tags": "ex_parte,misconduct,five_orders",
    },
    {
        "gene_type": "fact",
        "content": "HealthWest evaluation: Psychosis=0, Substance=0, Danger=0, LOCUS=12/Level One — excluded by McNeill",
        "confidence": 0.95,
        "lane": "A",
        "tags": "healthwest,evaluation,excluded_evidence",
    },
    {
        "gene_type": "fact",
        "content": "Emily recanted physical allegations on Oct 13, 2023 (NSPD-2023-08121) then filed PPO Oct 15, 2023",
        "confidence": 0.95,
        "lane": "D",
        "tags": "recantation,ppo,contradiction",
    },
    {
        "gene_type": "fact",
        "content": "Jennifer Barnes (P55406) withdrew as counsel March 2026 — Emily is now unrepresented",
        "confidence": 0.99,
        "lane": "A",
        "tags": "attorney,withdrawal,service",
    },
    {
        "gene_type": "fact",
        "content": "59 days total incarceration from contempt: SC#5 14 days + SC#6+7 45 days — lost 2 homes and 2 jobs",
        "confidence": 0.95,
        "lane": "A",
        "tags": "contempt,incarceration,harm",
    },
    {
        "gene_type": "fact",
        "content": "Officer Ella Randall documented Emily's meth use admission in police report",
        "confidence": 0.90,
        "lane": "A",
        "tags": "meth,projection,police_report",
    },
    {
        "gene_type": "fact",
        "content": "9 NSPD police contacts — zero arrests, zero charges across all interactions",
        "confidence": 0.95,
        "lane": "A",
        "tags": "police,exoneration,pattern",
    },
    # ── Patterns (observed behavioral patterns) ──────────────────────
    {
        "gene_type": "pattern",
        "content": "Emily's allegations are projections of her own conduct — meth admission contradicts drug allegations against Andrew",
        "confidence": 0.85,
        "lane": "A",
        "tags": "projection,pattern,credibility",
    },
    {
        "gene_type": "pattern",
        "content": "Retaliation cycle: Andrew files motion → Emily files false allegations → judge punishes Andrew",
        "confidence": 0.80,
        "lane": "E",
        "tags": "retaliation,cycle,misconduct",
    },
    {
        "gene_type": "pattern",
        "content": "McNeill-Hoopes-Ladas judicial cartel: former law partners at Ladas, Hoopes & McNeill, 435 Whitehall Rd",
        "confidence": 0.90,
        "lane": "E",
        "tags": "cartel,conflict_of_interest,judicial",
    },
    {
        "gene_type": "pattern",
        "content": "Ex parte orders precede every major custody change — notice to Andrew systematically omitted",
        "confidence": 0.85,
        "lane": "E",
        "tags": "ex_parte,due_process,pattern",
    },
    # ── Strategies (proven filing approaches) ─────────────────────────
    {
        "gene_type": "strategy",
        "content": "Filing sequence: F03 Disqualification → F06 JTC → F05 MSC Original → F09 COA Brief → F04 Federal 1983",
        "confidence": 0.80,
        "lane": "F",
        "tags": "filing,sequence,strategy",
    },
    {
        "gene_type": "strategy",
        "content": "Use MCR 7.306 superintending control when lower courts are compromised — bypass normal appeal",
        "confidence": 0.85,
        "lane": "F",
        "tags": "msc,superintending,bypass",
    },
    {
        "gene_type": "strategy",
        "content": "Mathews v Eldridge (424 US 319) for family law due process — NOT Brady v Maryland which is criminal only",
        "confidence": 0.95,
        "lane": "C",
        "tags": "due_process,authority,anti_hallucination",
    },
    # ── Heuristics (operational rules) ────────────────────────────────
    {
        "gene_type": "heuristic",
        "content": "Compute separation days dynamically: (today - date(2025,7,29)).days — never hardcode",
        "confidence": 0.99,
        "lane": "",
        "tags": "separation,dynamic,rule",
    },
    {
        "gene_type": "heuristic",
        "content": "MCL 722.27c DOES NOT EXIST — correct cite is MCL 722.23(j) for willingness to facilitate",
        "confidence": 0.99,
        "lane": "A",
        "tags": "anti_hallucination,citation,correction",
    },
    {
        "gene_type": "heuristic",
        "content": "Serve Emily Watson directly at 2160 Garland Dr, Norton Shores MI 49441 — Barnes withdrew",
        "confidence": 0.99,
        "lane": "A",
        "tags": "service,address,direct",
    },
]


# ── Seeding Function ──────────────────────────────────────────────────────

def seed_initial_genes(memory) -> int:
    """Seed the genetic memory with foundational litigation genes.

    Uses content matching to avoid duplicates — safe to call repeatedly.

    Args:
        memory: A GeneticMemory instance (must have .conn and .store_gene)

    Returns:
        Number of new genes inserted
    """
    inserted = 0

    for gene_data in _SEED_GENES:
        # Check if this gene already exists by content match
        existing = memory.conn.execute(
            "SELECT gene_id FROM genetic_memory WHERE content = ?",
            (gene_data["content"],),
        ).fetchone()

        if existing:
            logger.debug("Seed gene already exists: %s...", gene_data["content"][:50])
            continue

        memory.store_gene(
            gene_type=gene_data["gene_type"],
            content=gene_data["content"],
            confidence=gene_data["confidence"],
            lane=gene_data.get("lane", ""),
            tags=gene_data.get("tags", ""),
        )
        inserted += 1

    logger.info("Seeded %d new genes (skipped %d existing)",
                inserted, len(_SEED_GENES) - inserted)
    return inserted
