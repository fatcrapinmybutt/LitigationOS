---
description: "Testing and validation gates for court filings, evidence processing, and system operations. PASS gates per artifact type. Apply when validating any generated content."
applyTo: "**/*.{py,md,txt}"
---

# Testing & Validation Memory

Quality gates for court filings, evidence processing, and system operations. Zero tolerance for errors in sworn documents.

## PASS Gates by Artifact Type

### Affidavit PASS Gate
- [ ] Chronological order (no date jumps or inversions)
- [ ] Every factual claim has a citation or source reference
- [ ] Exhibits linked for each evidentiary claim
- [ ] No editorializing or legal argument (facts only)
- [ ] Epistemic markers present: "personal knowledge" vs "information and belief"
- [ ] Verification clause at end ("under penalty of perjury")
- [ ] No hallucinated names, dates, or statistics
- [ ] L.D.W. initials only (never full name)

### Brief/Memorandum PASS Gate
- [ ] IRAC structure complete for each argument
- [ ] All citations verified against authority_chains_v2 or master_citations
- [ ] Table of Contents matches actual headings
- [ ] Index of Authorities matches actual citations
- [ ] Page count within court limit (50 pages for COA, varies by court)
- [ ] Standard of review stated for each issue
- [ ] Relief requested clearly stated
- [ ] No fabricated case law or incorrect holdings

### Motion PASS Gate
- [ ] Relief requested defined in opening paragraph
- [ ] Legal grounds cited with specificity
- [ ] Supporting facts from affidavit or record
- [ ] Proof of service attached (MC 12)
- [ ] Correct case number and caption
- [ ] Correct court designation
- [ ] Proposed order attached (where required)
- [ ] Year is 2026 throughout

### Exhibit PASS Gate
- [ ] Bates numbered (PIGORS-{LANE}-{NNNNNN})
- [ ] Exhibit index complete (label, description, pages, source)
- [ ] Authentication noted (MRE 901/902 basis for each)
- [ ] No PII violations (child name redacted, SSN redacted)
- [ ] Files exist at referenced paths
- [ ] Content matches description

### Evidence Atom PASS Gate
- [ ] Source file_path verifiable
- [ ] Lane assignment correct (MEEK signal match)
- [ ] Date extracted (or marked unknown)
- [ ] Actor/target identified
- [ ] Confidence score ≥ 0.7

## Anti-Hallucination Checks

Run BEFORE any content is finalized:

```python
# Check for known hallucinations
BANNED_STRINGS = [
    "91% alienation", "Emily A. Watson", "Lincoln David Watson",
    "Ron Berry, Esq", "Jane Berry", "Patricia Berry",
    "SBN P35878", "9 CPS investigations"
]
for s in BANNED_STRINGS:
    assert s.lower() not in content.lower(), f"HALLUCINATION: {s}"
```

## Traceable Statistics Rule

Every number in a generated document MUST have a traceable query:

```
GOOD: "5,059 documented judicial violations (SELECT COUNT(*) FROM judicial_violations)"
BAD:  "Over 5,000 judicial violations" (rounded, unverifiable)
WORST: "91% alienation score" (fabricated, no query possible)
```

## Product App Tests

```powershell
cd 11_CODE\litigationos
pip install -e ".[dev]"
python -m pytest tests/ -q                    # All tests
python -m pytest tests/ --cov=litigationos    # With coverage
```

## Pipeline Validation

```powershell
cd 00_SYSTEM\scripts && python syntax_check.py     # Syntax check all modules
python integration_test_phase123.py                  # Integration phases 1-3
cd 00_SYSTEM\pipeline && python quick_status.py     # Status
python validate.py                                   # Full validation
```

## Engine Smoke Test Requirement

Every engine directory under `00_SYSTEM/engines/` MUST have at least one smoke test that verifies:
1. **Import succeeds** — `from engines.{name} import *` without errors
2. **Instantiation succeeds** — Primary class can be created (may use mock DB)
3. **Basic operation** — One representative query/function returns expected type

Currently 34/36 engine directories have ZERO tests (only `narrative/` and `semantic/` have tests). When touching any engine, add a `test_{engine}.py` in the engine directory or in `tests/engines/`.

```python
# Minimal smoke test template
def test_engine_import():
    """Engine module imports without stdout corruption or missing deps."""
    import importlib
    mod = importlib.import_module(f"engines.{ENGINE_NAME}")
    assert hasattr(mod, "EXPECTED_CLASS")

def test_engine_instantiate():
    """Primary class instantiates without crashing."""
    engine = mod.EXPECTED_CLASS()  # or with mock config
    assert engine is not None
```

## Regression Watchlist

Known issues that MUST NOT regress:
1. `documents` table schema mismatch — `_doc_columns()` must remain adaptive
2. Shadow modules in repo root — Python `-I` flag required
3. exFAT on J:\ — NO WAL mode writes
4. Berry/Barnes name confusion — decontamination must hold
5. Child name exposure — MCR 8.119(H) compliance mandatory
