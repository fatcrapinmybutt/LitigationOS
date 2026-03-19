
import re
from pathlib import Path
import json

# Simple index of MCR/MCL patterns (expandable)
MCR_PATTERNS = [
    (r"mcr\s*2\.119", "MCR 2.119 - Motion Practice"),
    (r"mcr\s*2\.612", "MCR 2.612 - Relief from Judgment"),
    (r"mcr\s*3\.904", "MCR 3.904 - Custody/Parenting Time"),
    (r"mcr\s*3\.706", "MCR 3.706 - PPO Procedure"),
]

MCL_PATTERNS = [
    (r"mcl\s*722\.27", "MCL 722.27 - Custody Decisions"),
    (r"mcl\s*600\.2950", "MCL 600.2950 - PPO Statute"),
    (r"mcl\s*552\.605", "MCL 552.605 - Support Modification"),
    (r"mcl\s*554\.601", "MCL 554.601 - Landlord-Tenant Act"),
]

# Path to sorted evidence
EVIDENCE_ROOT = Path("F:/OMNILITIGATION_SYSTEM/EvidenceChronoMap/")
RESULTS_PATH = Path("F:/OMNILITIGATION_SYSTEM/LegalViolations/violation_map.json")

def scan_text_file(path: Path) -> list:
    try:
        content = path.read_text(errors="ignore").lower()
    except:
        return []

    matches = []
    for pat, label in MCR_PATTERNS + MCL_PATTERNS:
        if re.search(pat, content):
            matches.append(label)
    return matches

def scan_all_files():
    result_map = {}
    for file_path in EVIDENCE_ROOT.rglob("*.*"):
        if file_path.suffix.lower() not in [".txt", ".docx", ".pdf"]:
            continue
        violations = scan_text_file(file_path)
        if violations:
            result_map[str(file_path)] = violations
    return result_map

def save_results(results):
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        json.dump(results, f, indent=2)

def main():
    print("⚖️ Scanning for MCR/MCL violations...")
    results = scan_all_files()
    save_results(results)
    print(f"✅ Violation scan complete. Results saved to: {RESULTS_PATH}")

if __name__ == "__main__":
    main()
