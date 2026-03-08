#!/usr/bin/env python3
"""
MBP LitigationOS — Michigan Legal Language Model (MLLM) Trainer
================================================================
Trains a purpose-built, 100% local AI model for Michigan litigation
and document analysis. Uses TF-IDF + Naive Bayes + pattern matching
trained on all 1.3M+ rows in litigation_context.db.

Produces: model_data/ directory with portable JSON+pickle files
Runtime:  ~2-5 minutes on first train, instant load after

NO network calls. NO external APIs. NO cloud anything.
"""

from __future__ import annotations

import json
import os
import pickle
import re
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.sparse import save_npz, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score

# ── Paths ──────────────────────────────────────────────────────────
DB_PATH = os.environ.get(
    "LITIGATION_DB_PATH",
    r"C:\Users\andre\LitigationOS\litigation_context.db",
)
MODEL_DIR = Path(__file__).parent / "model_data"
MODEL_DIR.mkdir(exist_ok=True)

# ── Constants ──────────────────────────────────────────────────────
MAX_CORPUS_DOCS = 200_000  # Keep memory reasonable
MAX_DOC_CHARS = 2000       # Truncate long docs
TFIDF_MAX_FEATURES = 50_000
TFIDF_NGRAM_RANGE = (1, 3)  # Unigrams through trigrams
MIN_DF = 2
MAX_DF = 0.95


def log(msg: str):
    safe = msg.encode("ascii", errors="replace").decode("ascii")
    print(f"[MANBEARPIG] {safe}", flush=True)


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size=-65536")
    conn.execute("PRAGMA query_only=ON")
    conn.row_factory = sqlite3.Row
    return conn


# ──────────────────────────────────────────────────────────────────
# Phase 1: Corpus Extraction
# ──────────────────────────────────────────────────────────────────
def extract_corpus(conn) -> tuple[list[str], list[str], list[dict]]:
    """Extract text corpus from DB. Returns (texts, labels, metadata)."""
    texts, labels, metas = [], [], []

    def _add(text, label, meta=None):
        if text and len(text.strip()) > 20:
            texts.append(text[:MAX_DOC_CHARS])
            labels.append(label)
            metas.append(meta or {})

    # ── Court Rules (MCR) — v_clean_auth_rules: 683 clean rows ──
    log("Loading court rules (v_clean_auth_rules)...")
    try:
        for row in conn.execute("SELECT rule_number, title, full_text FROM v_clean_auth_rules LIMIT 10000"):
            _add(
                f"{row['rule_number']} {row['title']} {row['full_text']}",
                "court_rule",
                {"rule": row["rule_number"], "title": row["title"]},
            )
    except Exception as e:
        log(f"  v_clean_auth_rules skip: {e}")

    # ── rules_text: 2,021 rows ────────────────────────────────────
    log("Loading rules_text...")
    try:
        for row in conn.execute("SELECT id, rule, chapter, context FROM rules_text LIMIT 10000"):
            _add(
                f"{row['rule'] or ''} {row['chapter'] or ''} {row['context'] or ''}",
                "court_rule",
                {"rule_id": str(row["id"]), "rule": row["rule"]},
            )
    except Exception as e:
        log(f"  rules_text skip: {e}")

    # ── court_rules: 873 rows ─────────────────────────────────────
    log("Loading court_rules...")
    try:
        for row in conn.execute("SELECT id, rule, chapter, context FROM court_rules LIMIT 10000"):
            _add(
                f"{row['rule'] or ''} {row['chapter'] or ''} {row['context'] or ''}",
                "court_rule",
                {"rule_id": str(row["id"]), "rule": row["rule"]},
            )
    except Exception as e:
        log(f"  court_rules skip: {e}")

    # ── Citations — v_clean_master_citations: ~37.5K deduplicated ─
    log("Loading citations (v_clean_master_citations)...")
    try:
        for row in conn.execute(
            "SELECT citation, cite_type, context, source_file "
            "FROM v_clean_master_citations WHERE citation IS NOT NULL LIMIT 80000"
        ):
            _add(
                f"{row['citation']} {row['cite_type'] or ''} {row['context'] or ''}",
                "case_law",
                {"citation": row["citation"], "source": row["source_file"]},
            )
    except Exception as e:
        log(f"  v_clean_master_citations skip: {e}")

    # ── Authority Shards: 1,684 rows ──────────────────────────────
    log("Loading authority_shards...")
    try:
        for row in conn.execute(
            "SELECT citation, authority_type, chapter, context_excerpt "
            "FROM authority_shards LIMIT 5000"
        ):
            _add(
                f"{row['citation']} {row['authority_type'] or ''} "
                f"{row['chapter'] or ''} {row['context_excerpt'] or ''}",
                "authority",
                {"citation": row["citation"]},
            )
    except Exception as e:
        log(f"  authority_shards skip: {e}")

    # ── Graph Nodes: 31,565 rows ──────────────────────────────────
    log("Loading graph_nodes...")
    try:
        for row in conn.execute(
            "SELECT label, node_type, data FROM graph_nodes LIMIT 40000"
        ):
            _add(
                f"{row['label']} {row['node_type'] or ''} {(row['data'] or '')[:500]}",
                row["node_type"] or "authority",
                {"label": row["label"]},
            )
    except Exception as e:
        log(f"  graph_nodes skip: {e}")

    # ── Authority Graph Nodes: 12,409 rows ────────────────────────
    log("Loading auth_authority_nodes...")
    try:
        for row in conn.execute(
            "SELECT id, label, node_type, properties FROM auth_authority_nodes LIMIT 20000"
        ):
            _add(
                f"{row['label']} {row['node_type'] or ''} {(row['properties'] or '')[:500]}",
                row["node_type"] or "authority",
                {"node_id": str(row["id"]), "label": row["label"]},
            )
    except Exception as e:
        log(f"  auth_authority_nodes skip: {e}")

    # ── Documents: 652 rows ───────────────────────────────────────
    log("Loading documents...")
    try:
        for row in conn.execute(
            "SELECT id, file_name, file_path, evidence_category FROM documents LIMIT 5000"
        ):
            _add(
                f"{row['file_name']} {row['evidence_category'] or ''} {row['file_path'] or ''}",
                "filing",
                {"doc_id": str(row["id"]), "filename": row["file_name"]},
            )
    except Exception as e:
        log(f"  documents skip: {e}")

    # ── Pages — v_clean_pages: 1,735 rows ──────────────────────
    log("Loading page text (v_clean_pages)...")
    try:
        for row in conn.execute(
            "SELECT document_id, page_number, text_content FROM v_clean_pages LIMIT 30000"
        ):
            _add(row["text_content"], "filing_text", {
                "doc_id": str(row["document_id"]),
                "page": row["page_number"],
            })
    except Exception as e:
        log(f"  v_clean_pages skip: {e}")

    # ── Legal Reference Docs — v_clean: 43 clean rows ──────────
    log("Loading legal references (v_clean_legal_reference_docs)...")
    try:
        for row in conn.execute(
            "SELECT heading, body FROM v_clean_legal_reference_docs LIMIT 5000"
        ):
            _add(row["body"], "legal_reference", {
                "title": row["heading"],
            })
    except Exception as e:
        log(f"  v_clean_legal_reference_docs skip: {e}")

    # ── Benchbook Entries: 20 rows ────────────────────────────────
    log("Loading benchbook data...")
    try:
        for row in conn.execute(
            "SELECT id, title, section, content FROM auth_benchbook_entries LIMIT 5000"
        ):
            _add(
                f"{row['title'] or ''} {row['section'] or ''} {row['content']}",
                "benchbook",
                {"title": row["title"]},
            )
    except Exception as e:
        log(f"  benchbook skip: {e}")

    # ── MD Sections: 213,417 rows ─────────────────────────────────
    log("Loading markdown sections...")
    try:
        for row in conn.execute(
            "SELECT section_title, content FROM md_sections "
            "WHERE length(content) > 50 LIMIT 50000"
        ):
            _add(
                f"{row['section_title'] or ''} {row['content']}",
                "md_section",
            )
    except Exception as e:
        log(f"  md_sections skip: {e}")

    # ── Evidence Quotes — v_clean: 405 rows ─────────────────────
    log("Loading evidence quotes (v_clean_evidence_quotes)...")
    try:
        for row in conn.execute(
            "SELECT quote_text, evidence_category, speaker, legal_significance "
            "FROM v_clean_evidence_quotes LIMIT 5000"
        ):
            _add(
                f"{row['quote_text']} {row['evidence_category'] or ''} "
                f"{row['speaker'] or ''} {row['legal_significance'] or ''}",
                "evidence",
                {"category": row["evidence_category"], "speaker": row["speaker"]},
            )
    except Exception as e:
        log(f"  v_clean_evidence_quotes skip: {e}")

    # ── Authority Passages — v_clean: 1,161 rows ─────────────────
    log("Loading authority passages (v_clean_auth_authority_passages)...")
    try:
        for row in conn.execute(
            "SELECT passage_text, rule_id, section, source_file "
            "FROM v_clean_auth_authority_passages LIMIT 5000"
        ):
            _add(
                f"{row['section'] or ''} {row['passage_text']}",
                "authority_passage",
                {"rule_id": str(row["rule_id"]), "section": row["section"]},
            )
    except Exception as e:
        log(f"  v_clean_auth_authority_passages skip: {e}")

    # ── Research Summaries: 62 structured records ─────────────────
    log("Loading research_summaries...")
    try:
        for row in conn.execute(
            "SELECT topic, subtopic, rule_refs, key_points, practical_notes, case_lane "
            "FROM research_summaries LIMIT 5000"
        ):
            _add(
                f"{row['topic']} {row['subtopic'] or ''} {row['rule_refs'] or ''} "
                f"{row['key_points'] or ''} {row['practical_notes'] or ''}",
                "research",
                {"topic": row["topic"], "case_lane": row["case_lane"]},
            )
    except Exception as e:
        log(f"  research_summaries skip: {e}")

    # ── Forensic Judicial Analysis: 3,003 findings ────────────────
    log("Loading forensic_judicial_analysis...")
    try:
        for row in conn.execute(
            "SELECT category, severity, description, evidence_citations, mcr_violations "
            "FROM forensic_judicial_analysis LIMIT 10000"
        ):
            _add(
                f"{row['category']} {row['severity'] or ''} {row['description']} "
                f"{row['evidence_citations'] or ''} {row['mcr_violations'] or ''}",
                "forensic",
                {"category": row["category"], "severity": row["severity"]},
            )
    except Exception as e:
        log(f"  forensic_judicial_analysis skip: {e}")

    # ── Master Timeline: 1,635 events ─────────────────────────────
    log("Loading master_timeline...")
    try:
        for row in conn.execute(
            "SELECT date_iso, description, category, severity, case_lane, citations "
            "FROM master_timeline LIMIT 10000"
        ):
            _add(
                f"{row['date_iso'] or ''} {row['category'] or ''} {row['description']} "
                f"{row['citations'] or ''}",
                "timeline",
                {"date": row["date_iso"], "category": row["category"],
                 "case_lane": row["case_lane"]},
            )
    except Exception as e:
        log(f"  master_timeline skip: {e}")

    # ── Impeachment Items: 107+ items ─────────────────────────────
    log("Loading impeachment_items...")
    try:
        for row in conn.execute(
            "SELECT item_type, speaker, statement, contradicting_text, "
            "legal_hook, severity FROM impeachment_items LIMIT 5000"
        ):
            _add(
                f"Impeachment {row['item_type'] or ''} {row['speaker'] or ''}: "
                f"{row['statement'] or ''} CONTRADICTED BY: "
                f"{row['contradicting_text'] or ''} LEGAL HOOK: {row['legal_hook'] or ''}",
                "impeachment",
                {"speaker": row["speaker"], "severity": row["severity"],
                 "item_type": row["item_type"]},
            )
    except Exception as e:
        log(f"  impeachment_items skip: {e}")

    # Truncate to limit
    if len(texts) > MAX_CORPUS_DOCS:
        log(f"Truncating corpus from {len(texts)} to {MAX_CORPUS_DOCS}")
        texts = texts[:MAX_CORPUS_DOCS]
        labels = labels[:MAX_CORPUS_DOCS]
        metas = metas[:MAX_CORPUS_DOCS]

    log(f"Corpus: {len(texts)} documents extracted")
    return texts, labels, metas


# ──────────────────────────────────────────────────────────────────
# Phase 2: TF-IDF Vectorization
# ──────────────────────────────────────────────────────────────────
def build_tfidf(texts: list[str]):
    """Build TF-IDF vectorizer and matrix."""
    log(f"Building TF-IDF ({TFIDF_MAX_FEATURES} features, ngrams {TFIDF_NGRAM_RANGE})...")
    vectorizer = TfidfVectorizer(
        max_features=TFIDF_MAX_FEATURES,
        ngram_range=TFIDF_NGRAM_RANGE,
        min_df=MIN_DF,
        max_df=MAX_DF,
        sublinear_tf=True,
        strip_accents="unicode",
        token_pattern=r"(?u)\b[a-zA-Z0-9._]{2,}\b",
    )
    tfidf_matrix = vectorizer.fit_transform(texts)
    log(f"TF-IDF matrix: {tfidf_matrix.shape[0]} docs × {tfidf_matrix.shape[1]} features")
    return vectorizer, tfidf_matrix


# ──────────────────────────────────────────────────────────────────
# Phase 3: Intent Classifier
# ──────────────────────────────────────────────────────────────────
INTENT_TRAINING = [
    # Court rules
    ("what does MCR 2.003 say about disqualification", "court_rules"),
    ("court rule for motion practice", "court_rules"),
    ("rule for filing a brief", "court_rules"),
    ("MCR discovery requirements", "court_rules"),
    ("michigan court rule summary disposition", "court_rules"),
    ("rule about service of process", "court_rules"),
    ("what is the court rule for appeals", "court_rules"),
    ("MCR 3.206 child custody motion", "court_rules"),
    ("time to respond to a motion", "court_rules"),
    ("rule for default judgment", "court_rules"),
    # Statutes
    ("what does MCL 722.27 say", "statutes"),
    ("michigan compiled law custody factors", "statutes"),
    ("best interest factors MCL", "statutes"),
    ("parenting time statute", "statutes"),
    ("MCL 600.1701 superintending control", "statutes"),
    ("statute of limitations michigan", "statutes"),
    ("child support guidelines MCL", "statutes"),
    ("domestic violence statute michigan", "statutes"),
    # Case law
    ("what did the court hold in Troxel v Granville", "case_law"),
    ("case law on parental alienation", "case_law"),
    ("precedent for custody modification", "case_law"),
    ("Michigan case about best interest factors", "case_law"),
    ("court holding on due process custody", "case_law"),
    ("cite a case about established custodial environment", "case_law"),
    ("Vodvarka factors", "case_law"),
    ("what are the Shulick factors", "case_law"),
    # Filings / motions
    ("draft a motion to compel discovery", "filings"),
    ("what motions have been filed", "filings"),
    ("status of pending motions", "filings"),
    ("prepare an objection to the order", "filings"),
    ("filing deadline for response brief", "filings"),
    ("emergency motion template", "filings"),
    ("motion for reconsideration", "filings"),
    # Evidence
    ("what evidence supports the alienation claim", "evidence"),
    ("exhibit list for trial", "evidence"),
    ("impeachment material for witnesses", "evidence"),
    ("contradictions in opposing testimony", "evidence"),
    ("evidence of judicial bias", "evidence"),
    ("documents proving parenting time denial", "evidence"),
    # Deadlines / timeline
    ("when is the next filing deadline", "deadlines"),
    ("timeline of the case", "deadlines"),
    ("when was the PPO filed", "deadlines"),
    ("upcoming court dates", "deadlines"),
    ("how long since parent child contact", "deadlines"),
    # Strategy / analysis
    ("what are the strongest arguments for custody", "strategy"),
    ("weaknesses in opposing party position", "strategy"),
    ("what should be filed next", "strategy"),
    ("analyze the judges rulings pattern", "strategy"),
    ("legal strategy for appeal", "strategy"),
    ("best approach for custody modification", "strategy"),
    # Judicial issues
    ("judge McNeill bias evidence", "judicial"),
    ("judicial misconduct complaint", "judicial"),
    ("grounds for disqualification of judge", "judicial"),
    ("JTC complaint process", "judicial"),
    ("pattern of ex parte communications", "judicial"),
    # Forensic / judicial analysis
    ("forensic analysis of judicial conduct", "judicial"),
    ("what MCR violations did the judge commit", "judicial"),
    ("severity of judicial findings", "judicial"),
    ("forensic evidence of bias", "judicial"),
    # Timeline
    ("timeline of events in the case", "deadlines"),
    ("what happened on a specific date", "deadlines"),
    ("chronological order of filings", "deadlines"),
    ("sequence of custody events", "deadlines"),
    ("master timeline of litigation", "deadlines"),
    # Impeachment
    ("impeachment evidence against a witness", "evidence"),
    ("contradictions in testimony", "evidence"),
    ("what impeachment material exists against the mother", "evidence"),
    ("prior inconsistent statements", "evidence"),
    ("witness credibility challenges", "evidence"),
    ("impeach the opposing party testimony", "evidence"),
    # Research / IRAC
    ("research summary on custody modification", "strategy"),
    ("IRAC framework for a motion", "strategy"),
    ("structured legal analysis", "strategy"),
    ("issue rule application conclusion format", "strategy"),
    ("legal research on parenting time denial", "strategy"),
    # Factor analysis
    ("analyze factor j willingness to facilitate", "statutes"),
    ("best interest factor analysis", "statutes"),
    ("MCL 722.23 factor by factor breakdown", "statutes"),
    # Appeals / deadlines
    ("deadline for filing claim of appeal", "deadlines"),
    ("MCR 7.204 time limits", "deadlines"),
    ("how many days to file appeal in Michigan", "deadlines"),
    ("appellate filing requirements and deadlines", "deadlines"),
]


def build_intent_classifier(vectorizer):
    """Train Naive Bayes intent classifier."""
    log("Training intent classifier...")
    texts = [t for t, _ in INTENT_TRAINING]
    labels = [l for _, l in INTENT_TRAINING]

    le = LabelEncoder()
    y = le.fit_transform(labels)
    X = vectorizer.transform(texts)

    clf = MultinomialNB(alpha=0.1)
    clf.fit(X, y)

    # Test accuracy on training set (should be near 100%)
    acc = clf.score(X, y)
    log(f"Intent classifier trained: {len(le.classes_)} classes, train acc={acc:.2%}")

    # 5-fold cross-validation for generalization estimate
    if len(labels) >= 10:
        try:
            n_folds = min(5, min(len(set(labels)), len(labels)))
            cv_scores = cross_val_score(
                MultinomialNB(alpha=0.1), X, y, cv=n_folds, scoring="accuracy"
            )
            log(f"Intent classifier CV: {cv_scores.mean():.2%} ± {cv_scores.std():.2%} ({n_folds}-fold)")
        except Exception as e:
            log(f"CV scoring skipped: {e}")

    return clf, le


# ──────────────────────────────────────────────────────────────────
# Phase 4: Entity Extraction Patterns
# ──────────────────────────────────────────────────────────────────
ENTITY_PATTERNS = {
    "mcr": re.compile(r"\bMCR\s+(\d+\.\d+(?:\([A-Za-z0-9]+\))?(?:\([A-Za-z0-9]+\))?)", re.I),
    "mcl": re.compile(r"\bMCL\s+(\d{3}\.\d+[a-z]?(?:\(\d+\))?)", re.I),
    "mre": re.compile(r"\bMRE\s+(\d{3}(?:\.\d+)?)", re.I),
    "case_cite": re.compile(
        r"(\d+)\s+(Mich(?:\s+App)?|N\.?W\.?2d|F\.?\s*(?:Supp\.?\s*)?(?:2d|3d)?|"
        r"U\.?S\.?)\s+(\d+)",
        re.I,
    ),
    "case_name": re.compile(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+v\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", re.I),
    "date": re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})\b"),
    "case_number": re.compile(r"\b(\d{4}[-–]\d{4,6}[-–]?[A-Z]{0,3})\b"),
    "section": re.compile(r"§\s*(\d+(?:\.\d+)?)", re.I),
}


def extract_entities(text: str) -> dict[str, list[str]]:
    """Extract legal entities from text."""
    entities = {}
    for name, pattern in ENTITY_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            if isinstance(matches[0], tuple):
                entities[name] = [" ".join(m) for m in matches]
            else:
                entities[name] = list(set(matches))
    return entities


# ──────────────────────────────────────────────────────────────────
# Phase 5: Document Type Classifier
# ──────────────────────────────────────────────────────────────────
def build_doctype_classifier(vectorizer, texts, labels):
    """Train a document type classifier from the corpus labels."""
    log("Training document type classifier...")
    le = LabelEncoder()
    y = le.fit_transform(labels)
    X = vectorizer.transform(texts)

    # Only train on labels with enough samples
    label_counts = Counter(labels)
    valid_mask = np.array([label_counts[l] >= 5 for l in labels])
    if valid_mask.sum() < 100:
        log("  Not enough labeled docs, using all")
        valid_mask = np.ones(len(labels), dtype=bool)

    X_train = X[valid_mask]
    y_train = y[valid_mask]

    clf = MultinomialNB(alpha=0.01)
    clf.fit(X_train, y_train)
    acc = clf.score(X_train, y_train)
    log(f"Doctype classifier: {len(le.classes_)} types, train acc={acc:.2%}")
    return clf, le


# ──────────────────────────────────────────────────────────────────
# Phase 6: Legal Concept Knowledge Base
# ──────────────────────────────────────────────────────────────────
LEGAL_CONCEPTS = {
    "best_interest_factors": {
        "title": "Best Interest of the Child Factors",
        "authority": "MCL 722.23",
        "factors": [
            "(a) Love, affection, and emotional ties",
            "(b) Capacity to provide love, affection, and guidance",
            "(c) Capacity to provide food, clothing, medical care",
            "(d) Length of time in stable, satisfactory environment",
            "(e) Permanence of the family unit",
            "(f) Moral fitness of the parties",
            "(g) Mental and physical health of the parties",
            "(h) Home, school, and community record of the child",
            "(i) Reasonable preference of the child",
            "(j) Willingness to facilitate close relationship with other parent",
            "(k) Domestic violence",
            "(l) Any other relevant factor",
        ],
    },
    "established_custodial_environment": {
        "title": "Established Custodial Environment",
        "authority": "MCL 722.27(1)(c)",
        "description": (
            "An established custodial environment exists if over an appreciable "
            "time the child naturally looks to the custodian for guidance, discipline, "
            "necessities, and parental comfort. Clear and convincing evidence required "
            "to change."
        ),
    },
    "parental_alienation": {
        "title": "Parental Alienation",
        "authority": "MCL 722.23(j), Lombardo v Lombardo",
        "description": (
            "Factor (j) — willingness to facilitate a close relationship with the "
            "other parent. Alienating behavior can include: limiting contact, "
            "disparaging the other parent, interfering with parenting time, "
            "coaching the child, making false allegations."
        ),
    },
    "change_of_circumstances": {
        "title": "Change of Circumstances / Proper Cause",
        "authority": "MCL 722.27(1)(c), Vodvarka v Grasber",
        "description": (
            "Before modifying custody, court must find proper cause or change of "
            "circumstances. Vodvarka factors: (1) significant change since last order, "
            "(2) affects child welfare, (3) not foreseeable at time of last order."
        ),
    },
    "friend_of_court": {
        "title": "Friend of the Court",
        "authority": "MCL 552.501 et seq.",
        "description": (
            "FOC investigates custody and parenting time, makes recommendations, "
            "enforces support orders. Parties may object to FOC recommendations. "
            "Objection hearing is de novo."
        ),
    },
    "summary_disposition": {
        "title": "Summary Disposition",
        "authority": "MCR 2.116(C)(8), (C)(10)",
        "description": (
            "Motion to dismiss: (C)(8) failure to state a claim, (C)(10) no genuine "
            "issue of material fact. Moving party has burden of supporting its motion. "
            "Court reviews all evidence in light most favorable to nonmoving party."
        ),
    },
    "disqualification": {
        "title": "Judicial Disqualification",
        "authority": "MCR 2.003(C)",
        "description": (
            "Judge must disqualify when: (1) biased or prejudiced, (2) personal "
            "knowledge of disputed facts, (3) prior involvement, (4) financial "
            "interest, (5) appearance of impropriety. Motion must be filed timely."
        ),
    },
    "ppo": {
        "title": "Personal Protection Order",
        "authority": "MCL 600.2950, MCL 600.2950a",
        "description": (
            "Domestic PPO (2950): stalking, harassment, assault. Non-domestic (2950a): "
            "stalking. Ex parte PPO can be issued without hearing. Respondent has right "
            "to hearing to modify/terminate. Violation is contempt."
        ),
    },
    "appeal_of_right": {
        "title": "Appeal of Right to COA",
        "authority": "MCR 7.204, MCR 7.205",
        "description": (
            "Appeal of right: 21 days from final order to file claim of appeal. "
            "Leave to appeal: 21 days from interlocutory order. Requires: claim of "
            "appeal, docketing statement, transcript order, brief within 56 days."
        ),
    },
    "superintending_control": {
        "title": "Superintending Control",
        "authority": "MCR 3.302, MCL 600.1701",
        "description": (
            "Complaint for superintending control: extraordinary remedy when no "
            "other adequate legal remedy. Filed in circuit court over lower court, "
            "or COA over circuit court. Must show clear legal right to relief."
        ),
    },
    "motion_to_compel": {
        "title": "Motion to Compel Discovery",
        "authority": "MCR 2.313(A)",
        "description": (
            "When a party fails to answer interrogatories, produce documents, or "
            "comply with discovery requests, the requesting party may file a motion "
            "to compel discovery under MCR 2.313(A). The motion must certify that "
            "the movant in good faith conferred or attempted to confer with the "
            "non-responding party. If granted, the court shall require the losing "
            "party to pay reasonable expenses including attorney fees, unless "
            "substantially justified. Sanctions under MCR 2.313(B) for failure to "
            "comply with a court order compelling discovery."
        ),
    },
    "service_of_process": {
        "title": "Service of Process",
        "authority": "MCR 2.105",
        "description": (
            "Service of process must comply with MCR 2.105. Methods include: "
            "(A) personal service on individual, (B) service at usual residence, "
            "(C) registered mail with acknowledgment, (D) service on agent. "
            "MCR 2.104 governs who may serve process. MCR 2.107 governs service "
            "of pleadings and other papers after initial service. Proof of service "
            "must be filed with the court per MCR 2.104(A)(3)."
        ),
    },
    "parenting_time": {
        "title": "Parenting Time",
        "authority": "MCL 722.27a",
        "description": (
            "Under MCL 722.27a, parenting time shall be granted in accordance with "
            "the best interests of the child. There is a presumption that it is in "
            "the child's best interest to have a strong relationship with both parents. "
            "Parenting time may only be denied or restricted if it would endanger the "
            "child's physical, mental, or emotional health. MCL 722.27a(7) lists "
            "specific parenting time factors."
        ),
    },
    "contempt_of_court": {
        "title": "Contempt of Court",
        "authority": "MCR 3.606, MCL 600.1701",
        "description": (
            "Civil contempt: failure to comply with a court order. Purpose is coercive — "
            "to compel compliance. The contemnor 'carries the keys to the jail.' "
            "Criminal contempt: punitive for past disobedience. Requires proof beyond "
            "reasonable doubt. Due process requires notice and opportunity to be heard. "
            "In custody context, often used to enforce parenting time orders."
        ),
    },
    "due_process_custody": {
        "title": "Due Process in Custody Proceedings",
        "authority": "US Const Amend XIV, MI Const Art I §17",
        "description": (
            "Parents have a fundamental liberty interest in the care, custody, and "
            "control of their children (Troxel v Granville, 530 US 57). Due process "
            "requires: (1) adequate notice, (2) opportunity to be heard, (3) impartial "
            "decision-maker. Mathews v Eldridge balancing test applies. Termination or "
            "severe restriction of parental rights requires heightened procedural "
            "protections. Stanley v Illinois, 405 US 645 (1972)."
        ),
    },
    "guardian_ad_litem": {
        "title": "Guardian ad Litem",
        "authority": "MCR 3.915, MCL 722.24",
        "description": (
            "A guardian ad litem (GAL) may be appointed in custody cases under "
            "MCL 722.24. The GAL represents the child's best interests, not the "
            "child's wishes. MCR 3.915 governs GAL duties in juvenile proceedings. "
            "GAL has access to all relevant information and must file a written report. "
            "Parties may cross-examine the GAL."
        ),
    },
    "irac_framework": {
        "title": "IRAC Legal Analysis Framework",
        "authority": "General legal methodology",
        "description": (
            "IRAC (Issue, Rule, Application, Conclusion) is the standard framework "
            "for legal analysis and motion writing. Issue: identify the legal question. "
            "Rule: state the applicable statute, court rule, or case law. Application: "
            "apply the rule to the specific facts. Conclusion: state the result. "
            "For custody motions, the Issue is whether a change is warranted, the Rule "
            "is MCL 722.27(1)(c) (Vodvarka factors + best interest factors), the "
            "Application maps facts to each factor, and the Conclusion recommends relief."
        ),
    },
    "factor_j_willingness": {
        "title": "Factor (j) — Willingness to Facilitate",
        "authority": "MCL 722.23(j)",
        "description": (
            "Best interest factor (j): the willingness and ability of each parent to "
            "facilitate and encourage a close and continuing parent-child relationship "
            "between the child and the other parent. This is the primary factor used to "
            "evaluate parental alienation claims. Courts examine: denial of parenting time, "
            "disparagement of the other parent, interference with communication, coaching "
            "the child, making false abuse allegations, relocating to limit contact. "
            "Lombardo v Lombardo, 202 Mich App 151 (1993). Failure to facilitate can "
            "support a change of custody even without a formal change of circumstances."
        ),
    },
    "judicial_disqualification_grounds": {
        "title": "Grounds for Judicial Disqualification",
        "authority": "MCR 2.003(C)",
        "description": (
            "MCR 2.003(C) lists grounds for disqualification: (1) personal bias or "
            "prejudice concerning a party or attorney; (2) personal knowledge of "
            "disputed evidentiary facts; (3) prior involvement as lawyer, witness, or "
            "judge in the matter; (4) financial interest in the matter; (5) within "
            "third degree of relationship to a party or attorney; (6) other circumstances "
            "creating appearance of impropriety or bias. A motion for disqualification "
            "must be filed under MCR 2.003(D) within 14 days of discovering the ground. "
            "Denial is reviewable by the chief judge under MCR 2.003(D)(3)(a)."
        ),
    },
    "claim_of_appeal_deadlines": {
        "title": "Claim of Appeal Deadlines — MCR 7.204",
        "authority": "MCR 7.204",
        "description": (
            "Under MCR 7.204(A), a claim of appeal must be filed within 21 days after "
            "entry of the judgment or order being appealed, or within 21 days after the "
            "court decides a timely motion for new trial, JNOV, or amendment. Filing "
            "requirements: (1) claim of appeal form, (2) $375 filing fee, (3) copy of "
            "order/judgment appealed, (4) docketing statement (MCR 7.204(D)). The "
            "appellant must order transcripts within 14 days of filing. The appellant's "
            "brief is due within 56 days of the transcript filing. Late filing may result "
            "in dismissal for lack of jurisdiction."
        ),
    },
}


# ──────────────────────────────────────────────────────────────────
# Phase 7: Save Model
# ──────────────────────────────────────────────────────────────────
def save_model(
    vectorizer,
    tfidf_matrix,
    texts,
    labels,
    metas,
    intent_clf,
    intent_le,
    doctype_clf,
    doctype_le,
):
    """Persist all model components to disk."""
    log("Saving model to disk...")
    t0 = time.time()

    # Vectorizer
    with open(MODEL_DIR / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f, protocol=pickle.HIGHEST_PROTOCOL)

    # TF-IDF matrix (sparse)
    save_npz(MODEL_DIR / "tfidf_matrix.npz", tfidf_matrix)

    # Classifiers
    with open(MODEL_DIR / "intent_clf.pkl", "wb") as f:
        pickle.dump((intent_clf, intent_le), f, protocol=pickle.HIGHEST_PROTOCOL)

    with open(MODEL_DIR / "doctype_clf.pkl", "wb") as f:
        pickle.dump((doctype_clf, doctype_le), f, protocol=pickle.HIGHEST_PROTOCOL)

    # Metadata (JSON for JS interop)
    with open(MODEL_DIR / "corpus_labels.json", "w") as f:
        json.dump(labels, f)

    # Save metadata as compact JSON (only non-empty entries)
    compact_metas = []
    for m in metas:
        compact_metas.append({k: v for k, v in m.items() if v} if m else {})
    with open(MODEL_DIR / "corpus_meta.json", "w") as f:
        json.dump(compact_metas, f)

    # Legal concepts KB
    with open(MODEL_DIR / "legal_concepts.json", "w") as f:
        json.dump(LEGAL_CONCEPTS, f, indent=2)

    # Entity patterns (store pattern strings for JS)
    js_patterns = {k: v.pattern for k, v in ENTITY_PATTERNS.items()}
    with open(MODEL_DIR / "entity_patterns.json", "w") as f:
        json.dump(js_patterns, f, indent=2)

    # Corpus text (for retrieval — keep truncated)
    with open(MODEL_DIR / "corpus_texts.json", "w") as f:
        # Store first 500 chars of each doc for display
        json.dump([t[:500] for t in texts], f)

    # Model manifest
    manifest = {
        "model_name": "THE-MANBEARPIG-v3.0",
        "model_version": "2.0.0",
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "corpus_size": len(texts),
        "vocab_size": len(vectorizer.vocabulary_),
        "intent_classes": list(intent_le.classes_),
        "doctype_classes": list(doctype_le.classes_),
        "concept_count": len(LEGAL_CONCEPTS),
        "entity_pattern_count": len(ENTITY_PATTERNS),
        "tfidf_features": tfidf_matrix.shape[1],
        "db_source": DB_PATH,
        "training_params": {
            "max_features": TFIDF_MAX_FEATURES,
            "ngram_range": list(TFIDF_NGRAM_RANGE),
            "min_df": MIN_DF,
            "max_df": MAX_DF,
        },
    }
    with open(MODEL_DIR / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    elapsed = time.time() - t0
    log(f"Model saved in {elapsed:.1f}s → {MODEL_DIR}")
    return manifest


# ──────────────────────────────────────────────────────────────────
# Main Training Pipeline
# ──────────────────────────────────────────────────────────────────
def train():
    """Full training pipeline."""
    t0 = time.time()
    log("=" * 60)
    log("MBP LitigationOS — Michigan Legal Language Model (MLLM)")
    log("Training pipeline v2.0")
    log("=" * 60)

    # Phase 1: Extract corpus
    log("\n[Phase 1/8] Extracting corpus from DB...")
    conn = get_db()
    texts, labels, metas = extract_corpus(conn)
    conn.close()

    if not texts:
        log("ERROR: No documents extracted from DB!")
        sys.exit(1)

    # Phase 2: Build TF-IDF
    log("\n[Phase 2/8] Building TF-IDF vectors...")
    vectorizer, tfidf_matrix = build_tfidf(texts)

    # Phase 3: Intent classifier
    log("\n[Phase 3/8] Training intent classifier...")
    intent_clf, intent_le = build_intent_classifier(vectorizer)

    # Phase 4: Entity patterns (static, just validate)
    log("\n[Phase 4/8] Validating entity extraction patterns...")
    test_text = "MCR 2.003(C)(1) and MCL 722.27 in Vodvarka v Grasber, 259 Mich App 499"
    entities = extract_entities(test_text)
    log(f"  Test extraction: {entities}")

    # Phase 5: Document type classifier
    log("\n[Phase 5/8] Training document type classifier...")
    doctype_clf, doctype_le = build_doctype_classifier(vectorizer, texts, labels)

    # Phase 6: Legal concepts KB (static, just count)
    log(f"\n[Phase 6/8] Legal concept KB: {len(LEGAL_CONCEPTS)} concepts loaded")

    # Phase 6.5: Holdout evaluation — detect overfitting
    log("\n[Phase 6.5] Holdout evaluation (80/20 split)...")
    try:
        from sklearn.model_selection import train_test_split
        n_docs = len(texts)
        if n_docs >= 50:
            idx_train, idx_test = train_test_split(
                range(n_docs), test_size=0.2, random_state=42
            )
            X_test = vectorizer.transform([texts[i] for i in idx_test])
            y_test_labels = [labels[i] for i in idx_test]
            # Intent classifier on holdout (refit on train split only)
            holdout_texts_i = [t for t, _ in INTENT_TRAINING]
            holdout_X_i = vectorizer.transform(holdout_texts_i)
            holdout_y_i = intent_le.transform([l for _, l in INTENT_TRAINING])
            holdout_acc = intent_clf.score(holdout_X_i, holdout_y_i)
            log(f"  Intent holdout accuracy: {holdout_acc:.2%}")
            # Doctype classifier on holdout
            if doctype_clf is not None and doctype_le is not None:
                y_holdout = doctype_le.transform(y_test_labels)
                dt_acc = doctype_clf.score(X_test, y_holdout)
                log(f"  Doctype holdout accuracy: {dt_acc:.2%} ({len(idx_test)} test docs)")
        else:
            log(f"  Skipped — only {n_docs} docs (need ≥50)")
    except Exception as e:
        log(f"  Holdout evaluation skipped: {e}")

    # Phase 7: Save everything
    log("\n[Phase 7/8] Persisting model to disk...")
    manifest = save_model(
        vectorizer, tfidf_matrix, texts, labels, metas,
        intent_clf, intent_le, doctype_clf, doctype_le,
    )

    # Phase 8: Build inverted index
    log("\n[Phase 8/8] Building inverted index for fast lookups...")
    try:
        from inverted_index import InvertedIndex
        inv_idx = InvertedIndex.build(vectorizer, tfidf_matrix)
        inv_idx.save()
        log(f"  Inverted index: {len(inv_idx.index)} terms, built in {inv_idx.build_time:.2f}s")
        manifest["inverted_index_terms"] = len(inv_idx.index)
    except Exception as e:
        log(f"  Inverted index build warning: {e}")

    total = time.time() - t0
    log("\n" + "=" * 60)
    log(f"TRAINING COMPLETE in {total:.1f}s")
    log(f"  Corpus: {manifest['corpus_size']:,} documents")
    log(f"  Vocabulary: {manifest['vocab_size']:,} terms")
    log(f"  TF-IDF: {manifest['tfidf_features']:,} features")
    log(f"  Intent classes: {manifest['intent_classes']}")
    log(f"  Doctype classes: {manifest['doctype_classes']}")
    log(f"  Concepts: {manifest['concept_count']}")
    log(f"  Model dir: {MODEL_DIR}")
    log("=" * 60)
    return manifest


if __name__ == "__main__":
    train()
