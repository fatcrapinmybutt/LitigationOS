#!/usr/bin/env python3
"""
APEX Michigan Legal EntityRuler v1.0
Custom spaCy NER patterns for Michigan litigation entities:
- Case numbers (MI circuit, district, COA, MSC formats)
- MCR/MCL citations
- Party names (Pigors v Watson specific + general)
- Judge names
- Court names
- Legal terms/motions
Outputs enriched entity JSON back to brain DB
"""
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', errors='replace')

import sqlite3
import json
import re
from datetime import datetime

try:
    import spacy
    from spacy.language import Language
    from spacy.tokens import Span
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False
    print("INFO: spaCy not available — using regex-only extraction (fully functional)")

BRAIN_DB = r'C:\Users\andre\LitigationOS\00_SYSTEM\brains\chat_intelligence_brain.db'
LIT_DB = r'C:\Users\andre\LitigationOS\litigation_context.db'

# ============================================================
# Pattern definitions — Michigan-specific legal entities
# ============================================================

CASE_NUMBER_PATTERNS = [
    # Circuit Court: YYYY-NNNNNN-XX (e.g., 2024-001507-DC)
    {"label": "MI_CASE_NUMBER", "pattern": [
        {"SHAPE": "dddd"}, {"ORTH": "-"}, {"SHAPE": "dddddd"}, {"ORTH": "-"}, {"IS_ALPHA": True, "LENGTH": 2}
    ]},
    # District Court: YYYY-NNNNNNNNN-XX (e.g., 2025-25245676-SM)
    {"label": "MI_CASE_NUMBER", "pattern": [
        {"SHAPE": "dddd"}, {"ORTH": "-"}, {"LIKE_NUM": True}, {"ORTH": "-"}, {"IS_ALPHA": True, "LENGTH": 2}
    ]},
    # COA docket: 366810
    {"label": "COA_DOCKET", "pattern": [{"SHAPE": "dddddd"}]},
]

# Regex-based patterns (more flexible than token patterns)
REGEX_PATTERNS = {
    'MI_CASE_NUMBER': re.compile(
        r'\b(\d{4}[-‐]\d{5,9}[-‐][A-Z]{2}(?:[-‐][A-Z]{2})?)\b'
    ),
    'MCR_CITATION': re.compile(
        r'\bMCR\s*(\d+\.\d+(?:\([A-Za-z0-9]+\))*)\b'
    ),
    'MCL_CITATION': re.compile(
        r'\bMCL\s*(\d+\.\d+[a-z]?(?:\([a-z0-9]+\))*)\b'
    ),
    'MSC_CITATION': re.compile(
        r'\b(\d+\s+Mich(?:\s+App)?\s+\d+)\b'
    ),
    'NW_CITATION': re.compile(
        r'\b(\d+\s+NW\s*2d\s+\d+)\b'
    ),
    'COA_DOCKET': re.compile(
        r'\b(?:COA|Court of Appeals)\s*(?:No\.?\s*)?(\d{6})\b', re.IGNORECASE
    ),
}

# Known entities for this case
KNOWN_PARTIES = {
    'Andrew Pigors': 'PLAINTIFF',
    'Andrew James Pigors': 'PLAINTIFF',
    'Pigors': 'PLAINTIFF',
    'Emily Watson': 'DEFENDANT',
    'Emily A. Watson': 'DEFENDANT',
    'Watson': 'DEFENDANT',
    'L.D.W.': 'CHILD',
    'LDW': 'CHILD',
    'Ronald Berry': 'THIRD_PARTY',
    'Ron Berry': 'THIRD_PARTY',
    'Berry': 'THIRD_PARTY',
    'Albert Watson': 'THIRD_PARTY',
    'Lori Watson': 'THIRD_PARTY',
    'Cody Watson': 'THIRD_PARTY',
}

KNOWN_JUDGES = {
    'Jenny McNeill': 'JUDGE_14TH_FAMILY',
    'McNeill': 'JUDGE_14TH_FAMILY',
    'Jenny L. McNeill': 'JUDGE_14TH_FAMILY',
    'Kenneth Hoopes': 'JUDGE_14TH_CHIEF',
    'Hoopes': 'JUDGE_14TH_CHIEF',
    'Maria Ladas-Hoopes': 'JUDGE_60TH',
    'Ladas-Hoopes': 'JUDGE_60TH',
    'Ladas Hoopes': 'JUDGE_60TH',
    'Kostrzewa': 'JUDGE_60TH_CRIMINAL',
    'Raymond Kostrzewa': 'JUDGE_60TH_CRIMINAL',
}

KNOWN_ATTORNEYS = {
    'Jennifer Barnes': 'ATT_DEFENDANT',
    'Barnes': 'ATT_DEFENDANT',
    'Amy Campanelli': 'ATT_PUBLIC_DEFENDER',
    'Campanelli': 'ATT_PUBLIC_DEFENDER',
    'Pamela Rusco': 'FOC',
    'Rusco': 'FOC',
}

KNOWN_COURTS = {
    '14th Circuit Court': 'COURT_CIRCUIT',
    '14th Circuit': 'COURT_CIRCUIT',
    'Muskegon Circuit Court': 'COURT_CIRCUIT',
    '60th District Court': 'COURT_DISTRICT',
    '60th District': 'COURT_DISTRICT',
    'Court of Appeals': 'COURT_COA',
    'Michigan Court of Appeals': 'COURT_COA',
    'Michigan Supreme Court': 'COURT_MSC',
    'Supreme Court': 'COURT_MSC',
}


def extract_entities_regex(text):
    """Extract entities using regex patterns — fast and precise for legal citations"""
    entities = []
    
    for label, pattern in REGEX_PATTERNS.items():
        for match in pattern.finditer(text):
            entities.append({
                'text': match.group(0),
                'label': label,
                'start': match.start(),
                'end': match.end(),
                'value': match.group(1) if match.lastindex else match.group(0)
            })
    
    # Known entity matching (case-sensitive for names)
    for name_dict, entity_type_prefix in [
        (KNOWN_PARTIES, 'PARTY'),
        (KNOWN_JUDGES, 'JUDGE'),
        (KNOWN_ATTORNEYS, 'ATTORNEY'),
        (KNOWN_COURTS, 'COURT'),
    ]:
        for name, role in name_dict.items():
            # Find all occurrences
            start = 0
            while True:
                idx = text.find(name, start)
                if idx == -1:
                    break
                entities.append({
                    'text': name,
                    'label': f'{entity_type_prefix}_{role}',
                    'start': idx,
                    'end': idx + len(name),
                    'value': name
                })
                start = idx + len(name)
    
    # Deduplicate overlapping entities (prefer longer matches)
    entities.sort(key=lambda e: (e['start'], -(e['end'] - e['start'])))
    deduped = []
    last_end = -1
    for e in entities:
        if e['start'] >= last_end:
            deduped.append(e)
            last_end = e['end']
    
    return deduped


def enrich_brain_db(limit=5000, batch_size=100):
    """Enrich brain DB records with extracted entities"""
    db = sqlite3.connect(BRAIN_DB)
    db.execute('PRAGMA busy_timeout=60000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA cache_size=-32000')
    
    # Get records without entity enrichment
    rows = db.execute("""
        SELECT rowid, content, lanes, legal_relevance_score
        FROM chat_intelligence 
        WHERE (entities_json IS NULL OR entities_json = '' OR entities_json = '[]')
        AND length(content) > 30
        ORDER BY legal_relevance_score DESC
        LIMIT ?
    """, (limit,)).fetchall()
    
    print(f"Enriching {len(rows)} records with Michigan legal entities...")
    
    enriched = 0
    entity_counts = {}
    batch = []
    
    for i, (rowid, content, lanes, score) in enumerate(rows):
        entities = extract_entities_regex(content)
        
        if entities:
            entities_json = json.dumps([{
                'text': e['text'],
                'label': e['label'],
                'value': e.get('value', e['text'])
            } for e in entities])
            
            batch.append((entities_json, rowid))
            enriched += 1
            
            for e in entities:
                label = e['label']
                entity_counts[label] = entity_counts.get(label, 0) + 1
        
        if len(batch) >= batch_size:
            db.executemany("UPDATE chat_intelligence SET entities_json = ? WHERE rowid = ?", batch)
            db.commit()
            print(f"  Batch {i//batch_size + 1}: enriched {len(batch)} records")
            batch = []
    
    # Final batch
    if batch:
        db.executemany("UPDATE chat_intelligence SET entities_json = ? WHERE rowid = ?", batch)
        db.commit()
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"Entity Enrichment Complete!")
    print(f"  Records processed: {len(rows)}")
    print(f"  Records with entities: {enriched}")
    print(f"  Entity types found:")
    for label, count in sorted(entity_counts.items(), key=lambda x: -x[1])[:20]:
        print(f"    {label}: {count}")
    print(f"{'=' * 60}")
    
    # Also save entity index to litigation_context.db
    save_entity_index(entity_counts)
    
    db.close()
    return enriched, entity_counts


def save_entity_index(entity_counts):
    """Save entity extraction stats to litigation_context.db"""
    try:
        lit = sqlite3.connect(LIT_DB)
        lit.execute('PRAGMA busy_timeout=60000')
        lit.execute('PRAGMA journal_mode=WAL')
        
        lit.execute("""CREATE TABLE IF NOT EXISTS entity_extraction_stats (
            entity_type TEXT PRIMARY KEY,
            count INTEGER,
            last_updated TEXT
        )""")
        
        now = datetime.now().isoformat()
        batch = [(label, count, now) for label, count in entity_counts.items()]
        lit.executemany("""INSERT OR REPLACE INTO entity_extraction_stats 
            (entity_type, count, last_updated) VALUES (?,?,?)""", batch)
        lit.commit()
        lit.close()
        print(f"  Saved {len(batch)} entity type stats to litigation_context.db")
    except Exception as e:
        print(f"  Warning: Could not save to litigation_context.db: {e}")


def main():
    print("=" * 60)
    print("APEX Michigan Legal EntityRuler v1.0")
    print("Regex-based NER for MI case numbers, MCR/MCL, parties, judges")
    print("=" * 60)
    
    enriched, counts = enrich_brain_db(limit=50000)
    
    # Print top entities for impeachment/litigation value
    print("\n🎯 HIGH-VALUE ENTITY SUMMARY:")
    party_hits = sum(v for k, v in counts.items() if k.startswith('PARTY_'))
    judge_hits = sum(v for k, v in counts.items() if k.startswith('JUDGE_'))
    citation_hits = sum(v for k, v in counts.items() if k.startswith('MC'))
    case_hits = sum(v for k, v in counts.items() if 'CASE' in k or 'DOCKET' in k)
    
    print(f"  Party mentions: {party_hits}")
    print(f"  Judge mentions: {judge_hits}")
    print(f"  Legal citations (MCR/MCL/NW): {citation_hits}")
    print(f"  Case numbers: {case_hits}")


if __name__ == '__main__':
    main()
