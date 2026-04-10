"""Fix delta999 agent files with correct names (_agent suffix)."""
import re
from pathlib import Path

AGENTS_DIR = Path(r"C:\Users\andre\LitigationOS\00_SYSTEM\engines\agents")

TARGETS = [
    "delta999_citation_agent.py",
    "delta999_coa_agent.py",
    "delta999_compliance_agent.py",
    "delta999_evidence_chain_agent.py",
    "delta999_rebuttal_agent.py",
    "delta999_redteam_agent.py",
    "delta999_trial_agent.py",
]

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

for name in TARGETS:
    path = AGENTS_DIR / name
    if not path.exists():
        print(f"  MISSING: {name}")
        continue
    text = path.read_text(encoding="utf-8", errors="replace")
    if "try:" in text and "sys.stdout.reconfigure" in text:
        print(f"  SKIP (already safe): {name}")
        continue
    if not PATTERN.search(text):
        print(f"  SKIP (no bare reconfigure): {name}")
        continue
    new_text = PATTERN.sub(REPLACEMENT, text)
    path.write_text(new_text, encoding="utf-8")
    print(f"  FIXED: {name}")

print("\nDone.")
