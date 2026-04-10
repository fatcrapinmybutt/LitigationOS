"""SURGICAL FIX: Replace ALL bare sys.stdout.reconfigure lines across 21 files.

The previous script had a false-positive 'already safe' check. This one:
1. Reads each file
2. Finds the EXACT line with bare sys.stdout.reconfigure
3. Checks the line BEFORE it — if it's 'try:', skip (truly safe)
4. Otherwise, wraps it in try/except
"""
import re
from pathlib import Path

ENGINES = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\engines")

# All 21 files identified by the verification audit
TARGETS = [
    ENGINES / "agents" / "delta999_citation_agent.py",
    ENGINES / "agents" / "delta999_coa_agent.py",
    ENGINES / "agents" / "delta999_compliance_agent.py",
    ENGINES / "agents" / "delta999_evidence_chain_agent.py",
    ENGINES / "agents" / "delta999_orchestrator.py",
    ENGINES / "agents" / "delta999_rebuttal_agent.py",
    ENGINES / "agents" / "delta999_redteam_agent.py",
    ENGINES / "agents" / "delta999_trial_agent.py",
    ENGINES / "backup_version_engine.py",
    ENGINES / "court_calendar_engine.py",
    ENGINES / "evidence_chain_engine.py",
    ENGINES / "filing_production_runner.py",
    ENGINES / "ingest_superpin_atlas.py",
    ENGINES / "llm_classifier_engine.py",
    ENGINES / "omega_convergence_9999.py",
    ENGINES / "placeholder_scanner.py",
    ENGINES / "skill_authority_validator.py",
    ENGINES / "skill_bias_quantifier.py",
    ENGINES / "skill_filing_tracker.py",
    ENGINES / "skill_ppo_detector.py",
    ENGINES / "skill_torts_claims.py",
]

fixed = 0

for path in TARGETS:
    if not path.exists():
        print(f"  MISSING: {path.name}")
        continue

    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    new_lines = []
    i = 0
    file_fixed = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Match bare sys.stdout.reconfigure at any indent level
        if re.match(r'^(\s*)sys\.stdout\.reconfigure\(encoding=[\'"]utf-8[\'"]\)\s*$', line):
            indent = line[:len(line) - len(line.lstrip())]
            
            # Check if previous line is already 'try:'
            prev = lines[i-1].strip() if i > 0 else ""
            if prev == "try:":
                new_lines.append(line)
                i += 1
                continue

            # Wrap it
            new_lines.append(f"{indent}try:")
            new_lines.append(f"{indent}    sys.stdout.reconfigure(encoding='utf-8')")
            new_lines.append(f"{indent}except (AttributeError, OSError):")
            new_lines.append(f"{indent}    pass")
            file_fixed = True
            i += 1
            continue

        new_lines.append(line)
        i += 1

    if file_fixed:
        path.write_text("\n".join(new_lines), encoding="utf-8")
        fixed += 1
        print(f"  FIXED: {path.name}")
    else:
        print(f"  SKIP: {path.name} (no bare reconfigure found)")

print(f"\n{'='*50}")
print(f"Fixed: {fixed} files")
