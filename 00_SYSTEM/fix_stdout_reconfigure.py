"""Bulk fix: wrap all sys.stdout.reconfigure(encoding='utf-8') in try/except.

Targets 24 files across delta999 agents and standalone engine scripts.
Pattern: bare `sys.stdout.reconfigure(encoding='utf-8')` at module level → wrap in try/except.
"""
import re
from pathlib import Path

REPO = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\engines")

# All known files with bare sys.stdout.reconfigure at module level
TARGETS = [
    # delta999 agents
    REPO / "agents" / "delta999_citation.py",
    REPO / "agents" / "delta999_coa.py",
    REPO / "agents" / "delta999_compliance.py",
    REPO / "agents" / "delta999_evidence_chain.py",
    REPO / "agents" / "delta999_orchestrator.py",
    REPO / "agents" / "delta999_rebuttal.py",
    REPO / "agents" / "delta999_redteam.py",
    REPO / "agents" / "delta999_trial.py",
    # standalone scripts in engines root
    REPO / "backup_version_engine.py",
    REPO / "court_calendar_engine.py",
    REPO / "evidence_chain_engine.py",
    REPO / "filing_production_runner.py",
    REPO / "ingest_superpin_atlas.py",
    REPO / "llm_classifier_engine.py",
    REPO / "omega_convergence_9999.py",
    REPO / "placeholder_scanner.py",
    REPO / "skill_authority_validator.py",
    REPO / "skill_bias_quantifier.py",
    REPO / "skill_convergence_engine.py",
    REPO / "skill_filing_tracker.py",
    REPO / "skill_landlord_tenant.py",
    REPO / "skill_michigan_tort_lawsuit.py",
    REPO / "skill_ppo_detector.py",
    REPO / "skill_timeline_builder.py",
    REPO / "skill_torts_claims.py",
]

# Pattern: bare `sys.stdout.reconfigure(encoding='utf-8')` (with optional quotes/spaces)
PATTERN = re.compile(
    r"^(sys\.stdout\.reconfigure\(encoding=['\"]utf-8['\"]\))\s*$",
    re.MULTILINE,
)

REPLACEMENT = (
    "try:\n"
    "    sys.stdout.reconfigure(encoding='utf-8')\n"
    "except (AttributeError, OSError):\n"
    "    pass"
)

fixed = 0
skipped = 0
missing = 0
already_safe = 0

for path in TARGETS:
    if not path.exists():
        print(f"  MISSING: {path.name}")
        missing += 1
        continue

    text = path.read_text(encoding="utf-8", errors="replace")

    if "try:" in text and "sys.stdout.reconfigure" in text:
        # Already wrapped
        print(f"  SKIP (already safe): {path.name}")
        already_safe += 1
        continue

    if not PATTERN.search(text):
        # Check if it exists at all
        if "sys.stdout.reconfigure" in text:
            print(f"  SKIP (non-standard pattern): {path.name}")
            skipped += 1
        else:
            print(f"  SKIP (no reconfigure found): {path.name}")
            skipped += 1
        continue

    new_text = PATTERN.sub(REPLACEMENT, text)
    path.write_text(new_text, encoding="utf-8")
    fixed += 1
    print(f"  FIXED: {path.name}")

print(f"\n{'='*50}")
print(f"Results: {fixed} fixed, {already_safe} already safe, {skipped} skipped, {missing} missing")
print(f"Total files processed: {fixed + already_safe + skipped + missing}")
