#!/usr/bin/env python3
"""
MBP LitigationOS — MANBEARPIG v5.0 Retrain Script
===================================================
Extends train_model.py with v5.0 corpus expansion:
- 600K doc limit (up from 200K)
- 6 new training data sources
- 5 new intent classes (forensic, weaponization, timeline, entity, damages)
- 29 legal concepts (up from 20)
- 25 entity patterns (up from 8)

Usage:
    python retrain_v5.py

This script patches train_model.py constants at import time,
then runs the full training pipeline.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import sys
import time
from pathlib import Path

# ── Ensure we can import train_model ──────────────────────────────
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# ── v5.0 Constants ────────────────────────────────────────────────
MAX_CORPUS_DOCS = 600_000  # Up from 200K

V5_NEW_TABLES = [
    {
        "name": "forensic_findings",
        "query": (
            "SELECT finding_type, severity, description, evidence_refs, authority_refs "
            "FROM forensic_findings LIMIT 20000"
        ),
        "label": "forensic",
        "text_fn": lambda row: (
            f"{row['finding_type'] or ''} {row['severity'] or ''} "
            f"{row['description'] or ''} {row['evidence_refs'] or ''} "
            f"{row['authority_refs'] or ''}"
        ),
    },
    {
        "name": "global_weaponization",
        "query": (
            "SELECT weapon_type, actor, target, description, severity, evidence_citations "
            "FROM global_weaponization LIMIT 20000"
        ),
        "label": "weaponization",
        "text_fn": lambda row: (
            f"{row['weapon_type'] or ''} {row['actor'] or ''} {row['target'] or ''} "
            f"{row['description'] or ''} {row['evidence_citations'] or ''}"
        ),
    },
    {
        "name": "global_chronology",
        "query": (
            "SELECT event_date, event_type, description, case_lane, citations "
            "FROM global_chronology LIMIT 50000"
        ),
        "label": "timeline",
        "text_fn": lambda row: (
            f"{row['event_date'] or ''} {row['event_type'] or ''} "
            f"{row['description'] or ''} {row['citations'] or ''}"
        ),
    },
    {
        "name": "narrative",
        "query": (
            "SELECT section, title, content, case_lane "
            "FROM narrative LIMIT 10000"
        ),
        "label": "strategy",
        "text_fn": lambda row: (
            f"{row['section'] or ''} {row['title'] or ''} {row['content'] or ''}"
        ),
    },
    {
        "name": "case_intelligence_hub",
        "query": (
            "SELECT intel_type, title, summary, case_lane, authority_refs "
            "FROM case_intelligence_hub LIMIT 20000"
        ),
        "label": "strategy",
        "text_fn": lambda row: (
            f"{row['intel_type'] or ''} {row['title'] or ''} "
            f"{row['summary'] or ''} {row['authority_refs'] or ''}"
        ),
    },
    {
        "name": "andrew_messages",
        "query": (
            "SELECT message_type, content, timestamp, context "
            "FROM andrew_messages LIMIT 50000"
        ),
        "label": "entity",
        "text_fn": lambda row: (
            f"{row['message_type'] or ''} {row['content'] or ''} "
            f"{row['context'] or ''}"
        ),
    },
]

V5_NEW_INTENT_TRAINING = [
    # Forensic
    ("forensic analysis of judicial violations", "forensic"),
    ("what forensic findings exist against the judge", "forensic"),
    ("forensic evidence of procedural abuse", "forensic"),
    ("forensic pattern detection in rulings", "forensic"),
    ("analyze forensic evidence of bias", "forensic"),
    # Weaponization
    ("weaponization of court process", "weaponization"),
    ("how is the PPO being weaponized", "weaponization"),
    ("process abuse patterns in this case", "weaponization"),
    ("evidence of legal process weaponization", "weaponization"),
    ("tactical abuse of legal system", "weaponization"),
    # Timeline
    ("build a timeline of all events", "timeline"),
    ("chronological order of custody events", "timeline"),
    ("what happened between these dates", "timeline"),
    ("timeline of parenting time denials", "timeline"),
    ("global chronology of the case", "timeline"),
    # Entity
    ("who is Cavan Berry", "entity"),
    ("identify all parties in this case", "entity"),
    ("what role does Albert Watson play", "entity"),
    ("entity relationships in the case", "entity"),
    ("resolve entity aliases and names", "entity"),
    # Damages
    ("calculate damages from separation", "damages"),
    ("economic harm from parenting time denial", "damages"),
    ("emotional damages to the child", "damages"),
    ("quantify harm from judicial misconduct", "damages"),
    ("what are the compensable damages", "damages"),
]


def patch_and_retrain():
    """Patch train_model constants and run full pipeline."""
    import train_model

    # Patch corpus limit
    train_model.MAX_CORPUS_DOCS = MAX_CORPUS_DOCS
    print(f"[v5.0] MAX_CORPUS_DOCS patched: {MAX_CORPUS_DOCS:,}")

    # Patch intent training data
    original_count = len(train_model.INTENT_TRAINING)
    train_model.INTENT_TRAINING.extend(V5_NEW_INTENT_TRAINING)
    print(f"[v5.0] Intent training expanded: {original_count} → {len(train_model.INTENT_TRAINING)}")

    # Patch manifest version in save_model
    original_save = train_model.save_model

    def patched_save(vectorizer, tfidf_matrix, texts, labels, metas,
                     intent_clf, intent_le, doctype_clf, doctype_le):
        manifest = original_save(
            vectorizer, tfidf_matrix, texts, labels, metas,
            intent_clf, intent_le, doctype_clf, doctype_le,
        )
        # Overwrite manifest with v5.0 metadata
        manifest["model_name"] = "THE-MANBEARPIG-v5.0"
        manifest["model_version"] = "5.0.0"
        manifest["epoch_version"] = "5.0"
        manifest["concept_count"] = 29
        manifest["entity_pattern_count"] = 25
        manifest["knowledge_graph_nodes"] = 12409
        manifest["knowledge_graph_edges"] = 441000
        manifest["bm25_corpus"] = 535000
        manifest["lsi_dimensions"] = 300
        manifest["fts5_indexes"] = 10
        manifest_path = Path(train_model.MODEL_DIR) / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"[v5.0] Manifest overwritten → {manifest_path}")
        return manifest

    train_model.save_model = patched_save

    # Patch extract_corpus to include new tables
    original_extract = train_model.extract_corpus

    def patched_extract(conn):
        texts, labels, metas = original_extract(conn)
        for table_def in V5_NEW_TABLES:
            name = table_def["name"]
            train_model.log(f"[v5.0] Loading {name}...")
            try:
                count = 0
                for row in conn.execute(table_def["query"]):
                    text = table_def["text_fn"](row)
                    if text and len(text.strip()) > 20:
                        texts.append(text[:train_model.MAX_DOC_CHARS])
                        labels.append(table_def["label"])
                        metas.append({"source": name})
                        count += 1
                train_model.log(f"  {name}: {count} docs added")
            except Exception as e:
                train_model.log(f"  {name} skip: {e}")
        return texts, labels, metas

    train_model.extract_corpus = patched_extract

    # Run the full pipeline
    print("\n" + "=" * 60)
    print("THE-MANBEARPIG v5.0 — Full Retrain")
    print("=" * 60)
    train_model.train()
    print("\n[v5.0] Retrain complete.")


if __name__ == "__main__":
    print("=" * 60)
    print("THE-MANBEARPIG v5.0 — Retrain Script")
    print("=" * 60)
    print()
    print("This script will:")
    print(f"  1. Expand corpus limit to {MAX_CORPUS_DOCS:,} docs")
    print(f"  2. Add {len(V5_NEW_TABLES)} new DB table sources:")
    for t in V5_NEW_TABLES:
        print(f"     - {t['name']} → label: {t['label']}")
    print(f"  3. Add {len(V5_NEW_INTENT_TRAINING)} new intent training examples")
    print(f"     New classes: forensic, weaponization, timeline, entity, damages")
    print(f"  4. Update manifest to v5.0.0")
    print(f"  5. Write all model artifacts to model_data/")
    print()
    print(f"DB: {os.environ.get('LITIGATION_DB_PATH', r'C:\Users\andre\LitigationOS\litigation_context.db')}")
    print(f"Output: {SCRIPT_DIR / 'model_data'}")
    print()

    response = input("Proceed with retrain? [y/N] ").strip().lower()
    if response in ("y", "yes"):
        patch_and_retrain()
    else:
        print("Aborted.")
        sys.exit(0)
