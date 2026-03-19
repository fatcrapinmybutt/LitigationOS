# LitigationOS Gotchas & Anti-Rationalization

## Iron Law Violations

### Case Lane Mixing — The #1 Mistake

**The rule:** Watson/custody (Lane A) and Shady Oaks/housing (Lane B) are SEPARATE. Period.

| Excuse | Reality |
|--------|---------|
| "Housing evidence strengthens the custody case" | Irrelevant to custody. Judge will sanction. Lane A only. |
| "McNeill handles both matters" | McNeill is custody only. Hoopes is housing. Different judges. |
| "The Watson family lives at Shady Oaks" | Residency is not a legal nexus for mixing claims. Separate filings. |
| "It shows a pattern of harm" | Pattern claims go in Lane C (Convergence) ONLY — against the county. |
| "This atom fits multiple lanes" | Tag it with ONE primary lane. If truly cross-lane → Lane C. |
| "I'll sort it out later" | Later = sanctions risk. Tag NOW. |

**Mixed a lane?** Delete the output. Re-run with correct lane filter.

### Missing Snapshot — The Pipeline Killer

**The rule:** Phase 0 safety.py runs BEFORE any other phase. No snapshot.lock = no pipeline.

| Excuse | Reality |
|--------|---------|
| "It's just a small test run" | Small runs corrupt master files too. Snapshot takes 30 seconds. |
| "I already have a backup from yesterday" | Yesterday's snapshot doesn't match today's state. Fresh snapshot. |
| "I'll snapshot after Phase 1" | Phase 1 might fail mid-write. Snapshot BEFORE. |
| "Dry-run mode is safe" | Dry-run is safe. But the NEXT run won't be. Build the habit. |

**Ran without snapshot?** STOP. Check master files manually. Run `validate.py`. Then snapshot.

### Writing to scans/ — The Evidence Destroyer

**The rule:** `C:\Users\andre\scans` is READ-ONLY. All outputs go to `cyclepacks/` or `LITIGATIONOS_MASTER/`.

| Excuse | Reality |
|--------|---------|
| "I'm just adding an index file" | Index files go in cyclepacks/. scans/ is source evidence. |
| "I need to rename for clarity" | Renaming = destroying provenance. Original names are evidence. |
| "I'm cleaning up duplicates" | Dedup is Phase 2. It marks canonicals in SQLite. It never deletes. |

**Wrote to scans/?** Restore from backup immediately. Check SHA-256 integrity.

## Evidence Posture Shortcuts

### Every Atom MUST Have a Posture Tag

| Posture | When to use | Weight |
|---------|-------------|--------|
| RECORD_FACT | From official court record (orders, docket) | 4x |
| EVIDENCE_FACT | From submitted evidence (exhibits) | 3x |
| SWORN_FACT | From sworn testimony/affidavit | 5x |
| ALLEGATION | Claimed but unverified | 1x |
| INFERENCE | Derived by analysis | 0.5x |

| Excuse | Reality |
|--------|---------|
| "I'll tag posture in a later pass" | Untagged atoms are useless. Tag on creation. |
| "It's obviously a record fact" | "Obviously" = assumption. Verify source type. Tag explicitly. |
| "The scoring handles it" | Scoring USES posture weights. No posture = no score. |

## MCP Server Gotchas

### PyMuPDF Import
```python
# ❌ WRONG — breaks on newer versions
import fitz

# ✅ CORRECT
import pymupdf
```

### FTS5 Query Syntax
```python
# ❌ WRONG — unbalanced quotes crash FTS5
query = 'parenting time" OR custody'

# ✅ CORRECT — properly quoted
query = '"parenting time" OR custody'

# ✅ CORRECT — prefix search
query = 'MCR 3.206*'
```

### MCP stdio
```python
# ❌ WRONG — print() goes to stdout, corrupts MCP protocol
print("Debug info")

# ✅ CORRECT — use stderr
import sys
print("Debug info", file=sys.stderr)
```

### Windows Long Paths (depth > 260 chars)
```python
# ❌ WRONG — fails on paths >260 characters
path = "C:\\Users\\andre\\scans\\discovery\\deep\\nested\\file.pdf"

# ✅ CORRECT — long-path prefix
path = "\\\\?\\C:\\Users\\andre\\scans\\discovery\\deep\\nested\\file.pdf"
```

## BRAIN_SPEC Violations

### Append-Only — NEVER Overwrite

| Excuse | Reality |
|--------|---------|
| "The old CyclePack had errors" | Leave it. Create a new CyclePack. Append corrections. |
| "I'm just updating a count" | Counts go in the NEW CyclePack's stats. Old stats are historical. |
| "The brain is full (500KB)" | Trim lowest-scored entries. Don't delete the brain. |

### Deterministic IDs
```python
# ❌ WRONG — random IDs break dedup
atom_id = f"FA-{uuid4()}"

# ✅ CORRECT — deterministic, dedup-safe
atom_id = f"FA-{sha1(f'{brain_id}|{type}|{key_fields}')}"
```

## Scoring Formula Misuse

The formula: `(citations * 3.0 + keywords * 1.5 + dollars + dates) * length_factor`

| Mistake | Fix |
|---------|-----|
| Counting all regex matches (inflated) | Count UNIQUE citations/keywords |
| Ignoring length_factor | `length_factor = min(1.0, char_count / 500)` — short docs get penalized |
| Using score without posture weight | Final score = base_score × posture_weight (SWORN=5x, RECORD=4x, etc.) |

## Red Flags — STOP Immediately

- "This is different because..." → It's not. Follow the rule.
- "Just this once..." → One exception = permanent habit.
- Modifying a file in `scans/` → STOP. Revert. Restore.
- Creating atoms without posture tags → STOP. Tag them.
- Running pipeline without `snapshot.lock` → STOP. Run safety.py.
- Filing with Lane A evidence in a Lane B motion → STOP. Separate.
- Score of 0 on a legal document → Bug in classification. Investigate.

**All mean:** Stop. Fix. Verify. Then continue.

## Fleet Coordination Anti-Patterns

### Cross-Skill Dispatch Violations

| Excuse | Reality |
|--------|---------|
| "I'll handle the MSC filing myself" | Use litigation-supreme-court-architect. It has the MCR 7.3xx state machine. |
| "Red team isn't needed for this small motion" | Red team is MANDATORY in FILE_READY mode. No exceptions. |
| "I'll skip the claim researcher and just draft" | Skipping research = missing viable claims. Always research first. |
| "This agent can handle the whole chain" | Multi-agent chains exist for a reason. Don't bypass dispatch. |
| "I'll merge outputs from two agents manually" | Use the coordination protocol. Manual merges lose provenance. |

### Fleet Health

| Red Flag | Action |
|----------|--------|
| Agent returns `STATUS: BLOCKED` | Route through core dispatcher to alternative agent |
| Two agents produce conflicting outputs | Escalate to litigation-convergence-orchestrator |
| Agent produces output for wrong lane | DELETE output. Re-dispatch with correct lane filter. |
| Agent modifies another agent's output block | STOP. Create new block, reference original. |
| Fleet audit score < 80 | Run litigation-skill-auditor immediately |
