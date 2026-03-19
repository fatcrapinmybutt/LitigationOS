# Atom Store Formats

All atoms follow BRAIN_SPEC v2026.02.20 JSONL format. One JSON object per line.

## fact_atoms.jsonl

```json
{
  "atom_id": "FA-{sha1}",
  "posture": "RECORD_FACT|EVIDENCE_FACT|SWORN_FACT|ALLEGATION|INFERENCE",
  "text": "The court entered an ex parte order on 2025-08-08 without hearing",
  "source_sha256": "abc123...",
  "source_path": "court_orders/2025-08-08_order.pdf",
  "page": 1,
  "line": 42,
  "macro_bucket": "DUE_PROCESS_SUPPRESSION|EXPARTE_ABUSE|BIAS_INDICATORS",
  "confidence": 0.95,
  "meek_lane": "MEEK2",
  "created_ts": "2026-02-21T12:00:00Z"
}
```

## citation_atoms.jsonl

```json
{
  "atom_id": "CA-{sha1}",
  "cite_type": "MCL|MCR|MRE|CASE|CANON",
  "cite_text": "MCR 3.207(B)(1)",
  "source_sha256": "abc123...",
  "source_path": "briefs/motion_restore_pt.md",
  "page": 3,
  "line": 15,
  "context": "...surrounding text for disambiguation..."
}
```

## event_atoms.jsonl

```json
{
  "atom_id": "EA-{sha1}",
  "date": "2025-08-08",
  "event_type": "ORDER|HEARING|SERVICE|FILING|VIOLATION",
  "description": "Ex parte custody order entered without noticed hearing",
  "source_sha256": "abc123...",
  "actors": ["McNeill", "Watson"],
  "meek_lane": "MEEK2"
}
```

## person_atoms.jsonl

```json
{
  "atom_id": "PA-{sha1}",
  "person": "EMILY_WATSON|JENNY_MCNEILL|ANDREW_PIGORS|...",
  "role": "DEFENDANT|JUDGE|PLAINTIFF|WITNESS|ATTORNEY|FOC",
  "context": "Watson filed a false police report on...",
  "source_sha256": "abc123...",
  "source_path": "evidence/police_report.pdf"
}
```

## contradiction_atoms.jsonl

```json
{
  "atom_id": "XA-{sha1}",
  "statement_a": "Watson testified she feared for her safety",
  "statement_b": "Watson's text messages show ongoing friendly contact",
  "source_a_sha256": "abc123...",
  "source_b_sha256": "def456...",
  "contradiction_type": "SWORN_VS_RECORD|ORDER_VS_TRANSCRIPT|CLAIM_VS_EVIDENCE"
}
```

## Posture Weights (for scoring)

| Posture | Weight | When to Use |
|---------|--------|-------------|
| SWORN_FACT | 5x | From sworn testimony, affidavit, deposition |
| RECORD_FACT | 4x | From official court record (orders, docket entries) |
| EVIDENCE_FACT | 3x | From submitted evidence (exhibits, documents) |
| ALLEGATION | 1x | Claimed but unverified by independent source |
| INFERENCE | 0.5x | Derived by analysis — requires confidence score |

## ID Generation

```python
import hashlib

def atom_id(prefix, brain_id, type_str, key_fields):
    raw = f"{brain_id}|{type_str}|{key_fields}"
    sha = hashlib.sha1(raw.encode()).hexdigest()[:12]
    return f"{prefix}-{sha}"

# Examples:
# atom_id("FA", "brain_01", "fact", "court_order|2025-08-08|page1")
# atom_id("CA", "brain_03", "citation", "MCR 3.207(B)(1)|motion_restore")
```
