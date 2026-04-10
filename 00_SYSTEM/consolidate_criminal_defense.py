"""
Consolidate all criminal defense files (People v. Pigors, 61-25006911-01)
into a single Desktop folder. COPIES only — originals never deleted (Rule 1).
Excludes criminal complaints AGAINST Watson (those are Lane A/E, not CRIMINAL lane).
"""
import shutil, os
from pathlib import Path

TARGET = Path(r"C:\Users\andre\Desktop\CRIMINAL_DEFENSE_61-25006911")
TARGET.mkdir(parents=True, exist_ok=True)

# Subfolders for organization
(TARGET / "01_MOTIONS").mkdir(exist_ok=True)
(TARGET / "02_BRIEFS").mkdir(exist_ok=True)
(TARGET / "03_DISCOVERY").mkdir(exist_ok=True)
(TARGET / "04_ATTORNEY_PREP").mkdir(exist_ok=True)
(TARGET / "05_EVIDENCE").mkdir(exist_ok=True)
(TARGET / "06_REFERENCE").mkdir(exist_ok=True)

# Files to copy: (source, destination subfolder, optional rename)
FILES = [
    # --- MOTIONS ---
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\BRADY_MOTION.md", "01_MOTIONS", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\MOTION_TO_DISMISS.md", "01_MOTIONS", None),
    (r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\LITIGATION_FILING_PACKAGE\PKG_CRIMINAL\BRIEF_MOTION_TO_COMPEL.md", "01_MOTIONS", None),
    (r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\LITIGATION_FILING_PACKAGE\PKG_CRIMINAL\MOTION_TO_COMPEL_DISCOVERY.md", "01_MOTIONS", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\PROPOSED_ORDER_BRADY_MOTION.md", "01_MOTIONS", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\PROPOSED_ORDER_MOTION_TO_DISMISS.md", "01_MOTIONS", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\CRIMINAL_MOTION_SUBSTITUTE_COUNSEL_001.txt", "01_MOTIONS", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\CRIMINAL_MOTION_TO_SUBSTITUTE_COUNSEL_20260325.pdf", "01_MOTIONS", None),

    # --- BRIEFS ---
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\SELF_DEFENSE_BRIEF.md", "02_BRIEFS", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\04_SELF_DEFENSE_TRIAL_BRIEF.txt", "02_BRIEFS", None),

    # --- DISCOVERY ---
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\SUBPOENA_PACKAGE.md", "03_DISCOVERY", None),
    (r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\LITIGATION_FILING_PACKAGE\PKG_CRIMINAL\FOIA_REQUEST_BODY_CAM.md", "03_DISCOVERY", None),
    (r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\LITIGATION_FILING_PACKAGE\PKG_CRIMINAL\DEMAND_LETTER_DISCOVERY.md", "03_DISCOVERY", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\01_BRADY_DEMAND_LETTER.txt", "03_DISCOVERY", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\CRIMINAL_FOIA_BODY_CAM_REQUEST.txt", "03_DISCOVERY", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\CRIMINAL_DISCOVERY_DEMAND_PROSECUTOR.txt", "03_DISCOVERY", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\CRIMINAL_MCR_6201_MOTION_DISCOVERY_INSPECTION_001.txt", "03_DISCOVERY", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\CRIMINAL_PROPOSED_ORDER_DISCOVERY_001.txt", "03_DISCOVERY", None),

    # --- ATTORNEY PREP ---
    (r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\CRIMINAL_DEFENSE_PREP\ATTORNEY_BREAKDOWN_MYSELWICK.md", "04_ATTORNEY_PREP", None),
    (r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\CRIMINAL_DEFENSE_PREP\DEFENSE_PREPARATION_2025-25245676SM.md", "04_ATTORNEY_PREP", None),
    (r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\CRIMINAL_DEFENSE_PREP\DEFENSE_PREPARATION_2025-25245676SM.docx", "04_ATTORNEY_PREP", None),
    (r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\CRIMINAL_DEFENSE_PREP\ATTORNEY_MEETING_PLAYBOOK.md", "04_ATTORNEY_PREP", None),
    (r"C:\Users\andre\Desktop\COURT_FILING_PACKETS\CRIMINAL_DEFENSE_PREP\ATTORNEY_MEETING_PLAYBOOK.docx", "04_ATTORNEY_PREP", None),
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\trial_prep_package.md", "04_ATTORNEY_PREP", None),

    # --- EVIDENCE ---
    (r"C:\Users\andre\Desktop\Case_61-25006911-01_Pigors.pdf", "05_EVIDENCE", "CRIMINAL_COMPLAINT_WARRANT_7pg.pdf"),
    (r"C:\Users\andre\Desktop\Assault_Battery_From_Attorney_Reports.pdf", "05_EVIDENCE", None),

    # --- REFERENCE ---
    (r"C:\Users\andre\LitigationOS\05_FILINGS\DRAFTS\muskegon_criminal_quicksteps (1)(0).md", "06_REFERENCE", "muskegon_criminal_quicksteps.md"),
]

copied = 0
skipped = 0
missing = 0

for src, subfolder, rename in FILES:
    src_path = Path(src)
    if not src_path.exists():
        print(f"  MISSING: {src_path.name}")
        missing += 1
        continue
    
    dest_name = rename if rename else src_path.name
    dest_path = TARGET / subfolder / dest_name
    
    if dest_path.exists():
        # Check if source is newer
        if src_path.stat().st_mtime > dest_path.stat().st_mtime:
            shutil.copy2(str(src_path), str(dest_path))
            print(f"  UPDATED: {subfolder}/{dest_name}")
            copied += 1
        else:
            print(f"  SKIP (current): {subfolder}/{dest_name}")
            skipped += 1
    else:
        shutil.copy2(str(src_path), str(dest_path))
        print(f"  COPIED: {subfolder}/{dest_name}")
        copied += 1

# Create a README index
readme = TARGET / "README.md"
readme_text = f"""# CRIMINAL DEFENSE — People v. Pigors
## Case No. 61-25006911-01 (also 2025-25245676SM)
## 60th District Court | Judge Kostrzewa | Trial: April 7, 2026

**Defendant:** Andrew James Pigors
**Defense Attorney:** Tom Myselwick (appointed after PD recusal)
**Prosecutor:** Lauren J. Duguid (P87908)
**Charge:** MCL 750.81(1) — Simple Assault/Battery (misdemeanor, max 93 days)
**Enhancement:** MCL 750.506a (consecutive sentence, place of confinement)

---

### ⚠️ THIS FOLDER IS 100% SEPARATE FROM ALL OTHER CASES ⚠️
Per Rule 7: Zero connection to Lanes A-F (custody, housing, PPO, appellate, federal).

---

## Folder Structure

| Folder | Contents |
|--------|----------|
| `01_MOTIONS/` | Brady motion, motion to dismiss, motion to compel, proposed orders |
| `02_BRIEFS/` | Self-defense trial brief |
| `03_DISCOVERY/` | Subpoena package, FOIA requests, discovery demands |
| `04_ATTORNEY_PREP/` | Attorney breakdown for Myselwick, defense prep, trial prep, playbook |
| `05_EVIDENCE/` | Criminal complaint/warrant PDF, attorney reports PDF |
| `06_REFERENCE/` | Muskegon criminal procedure quicksteps |

## Key Defense Theories
1. **Self-Defense (MCL 780.972)** — PRIMARY. Honest + reasonable belief of imminent harm.
2. **Duress (MCL 768.21b)** — Inmate-specific statutory defense. ⚠️ REQUIRES PRE-TRIAL NOTICE.
3. **Necessity** — Harm avoided (group attack) > harm caused (single altercation).
4. **Spoliation / Brady** — Body cam + jail footage destroyed. MCL 780.316(2) retention violation.

## Key Case Law (Verified Michigan)
- *People v Riddle*, 467 Mich 116 (2002) — Prosecution must disprove self-defense BRD
- *People v Dupree*, 486 Mich 693 (2010) — Self-defense available even during technical crime
- *People v Guajardo*, 300 Mich App 26 (2013) — Initial aggressor regains self-defense rights
- *People v Stevens*, 306 Mich App 620 (2014) — Prosecution must "exclude the possibility"
- *People v Fortson*, 202 Mich App 13 (1993) — Prosecution burden + character evidence rules

## URGENT ACTION ITEMS (3 DAYS TO TRIAL)
- [ ] File MCL 768.21b duress notice (MANDATORY or defense WAIVED)
- [ ] File Brady/spoliation motion re: destroyed body cam footage
- [ ] Subpoena jail surveillance footage (if it still exists)
- [ ] Get Myselwick the ATTORNEY_BREAKDOWN_MYSELWICK.md document

*Last updated: {os.popen('date /t').read().strip()}*
"""
readme.write_text(readme_text, encoding="utf-8")
print(f"\n  CREATED: README.md (index)")

print(f"\nDONE: {copied} copied, {skipped} skipped (current), {missing} missing")
print(f"Target: {TARGET}")

# List final contents
for sub in sorted(TARGET.iterdir()):
    if sub.is_dir():
        files = list(sub.iterdir())
        print(f"\n  {sub.name}/ ({len(files)} files)")
        for f in sorted(files):
            size = f.stat().st_size
            print(f"    {f.name} ({size:,} bytes)")
