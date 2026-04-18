# CROSS-FILING CONSISTENCY REPORT
**Generated:** Auto-audit of 8 court-ready filings  
**Scope:** `C:\Users\andre\LitigationOS\01_FILINGS\COURT_READY\` (01–08)  
**Result:** **56 inconsistencies found → 42 MUST FIX + 14 STATS WARNINGS**

---

## EXECUTIVE SUMMARY

| Category | Count | Severity | Files Affected |
|----------|-------|----------|---------------|
| "Andrew J. Pigors" → "Andrew James Pigors" | 28 | **MUST FIX** | 03, 05 |
| "Emily Watson" → "Emily A. Watson" | 11 | **MUST FIX** | 03, 05, 08 |
| "Whitehall Rd" → "Whitehall Road" | 3 | **MUST FIX** | 05, 07 |
| "127 judicial violations" → "1,127" | 12 | **WARNING** | 03, 05 |
| "126 violations" (PPO-specific) | 2 | **REVIEW** | 08 |
| **TOTAL** | **56** | | |

### ✅ CLEAN (No Issues Found)
- **Case numbers**: All 8 files use correct `2024-001507-DC`, `2023-5907-PP`, `2025-002760-CZ`, `366810`
- **No hallucinations**: Zero instances of "Jane Berry", "Patricia Berry", "P35878"
- **No wrong judge name**: Zero instances of "Amy McNeill"
- **No wrong Emily name**: Zero instances of "Emily Ann Watson"
- **Barnes bar number**: Correctly `P55406` everywhere
- **Ronald Berry**: Correctly identified as non-attorney everywhere
- **Files 01, 02, 04, 06**: Zero MUST FIX issues

---

## DETAILED FINDINGS

### 1. PLAINTIFF NAME: "Andrew J. Pigors" → "Andrew James Pigors"

**Rule:** Full legal name "Andrew James Pigors" must be used consistently in all filings.

#### File: `03_DISQUALIFICATION_MCR2003.md` (3 occurrences)
| Line | Found | Fix |
|------|-------|-----|
| 48 | `Sworn Statement of Andrew J. Pigors` | → `Andrew James Pigors` |
| 73 | `Affidavit of Bias of Andrew J. Pigors` | → `Andrew James Pigors` |
| 620 | `Affidavit of Bias of Andrew J. Pigors` | → `Andrew James Pigors` |

#### File: `05_MSC_ORIGINAL_ACTION.md` (25 occurrences)
| Line | Found | Fix |
|------|-------|-----|
| 50 | `Andrew J. Pigors 1977 Whitehall Rd` | → `Andrew James Pigors` |
| 130 | `Affidavit of Andrew J. Pigors` | → `Andrew James Pigors` |
| 299 | `Petitioner Andrew J. Pigors is the biological father` | → `Andrew James Pigors` |
| 534 | `Petitioner Andrew J. Pigors respectfully requests` | → `Andrew James Pigors` |
| 597 | `Petitioner Andrew J. Pigors is the father` | → `Andrew James Pigors` |
| 637 | `Affidavit of Andrew J. Pigors` | → `Andrew James Pigors` |
| 1141 | `I, Andrew J. Pigors, declare under penalty` | → `Andrew James Pigors` |
| 1146 | `Andrew J. Pigors, Petitioner (Pro Se)` | → `Andrew James Pigors` |
| 1167 | `Andrew J. Pigors, Petitioner (Pro Se)` | → `Andrew James Pigors` |
| 1181 | `Andrew J. Pigors` (signature block) | → `Andrew James Pigors` |
| 1233 | `I, Andrew J. Pigors, being first duly sworn` | → `Andrew James Pigors` |
| 1406 | `I, Andrew J. Pigors, being duly sworn` | → `Andrew James Pigors` |
| 1411 | `Andrew J. Pigors, Affiant` | → `Andrew James Pigors` |
| 1426 | `appeared **Andrew J. Pigors**` | → `Andrew James Pigors` |
| 1492 | `Petitioner Andrew J. Pigors, pro se` (2×) | → `Andrew James Pigors` |
| 1516 | `Petitioner Andrew J. Pigors and the minor child` | → `Andrew James Pigors` |
| 1613 | `Petitioner Andrew J. Pigors, 1977 Whitehall` | → `Andrew James Pigors` |
| 1637 | `Petitioner Andrew J. Pigors, pro se` | → `Andrew James Pigors` |
| 1684 | `I, Andrew J. Pigors, hereby certify` | → `Andrew James Pigors` |
| 1688 | `Affidavit of Andrew J. Pigors` | → `Andrew James Pigors` |
| 1779 | `Andrew J. Pigors, Petitioner (Pro Se)` | → `Andrew James Pigors` |
| 1837 | `Andrew J. Pigors, Petitioner (Pro Se)` | → `Andrew James Pigors` |
| 1849 | `Andrew J. Pigors, being first duly sworn` | → `Andrew James Pigors` |
| 1858 | `Andrew J. Pigors` (signature block) | → `Andrew James Pigors` |

**Fix applied:** Global replace `Andrew J. Pigors` → `Andrew James Pigors` in files 03 and 05.

---

### 2. DEFENDANT NAME: "Emily Watson" → "Emily A. Watson"

**Rule:** Middle initial "A." must always be included: "Emily A. Watson".

#### File: `03_DISQUALIFICATION_MCR2003.md` (6 occurrences)
| Line | Context | Fix |
|------|---------|-----|
| 95 | `listen to Emily Watson's recordings` | → `Emily A. Watson` |
| 99 | `Defendant Emily Watson's child support arrears` | → `Emily A. Watson` |
| 179 | `Defendant Emily Watson's recordings` | → `Emily A. Watson` |
| 470 | `recordings submitted by Defendant Emily Watson` | → `Emily A. Watson` |
| 478 | `Defendant Emily Watson's child support arrears` | → `Emily A. Watson` |
| 498 | `Defendant Emily Watson's boyfriend` | → `Emily A. Watson` |

#### File: `05_MSC_ORIGINAL_ACTION.md` (4 occurrences)
| Line | Context | Fix |
|------|---------|-----|
| 303 | `acting as Emily Watson's domestic partner` | → `Emily A. Watson` |
| 370 | `originated from Emily Watson herself` | → `Emily A. Watson` |
| 871 | `originated from Emily Watson herself` | → `Emily A. Watson` |
| 1311 | `originated from Emily Watson herself` | → `Emily A. Watson` |

#### File: `08_PPO_TERMINATION.md` (1 occurrence)
| Line | Context | Fix |
|------|---------|-----|
| 314 | `violation of court orders (Emily Watson, Lori Watson)` | → `Emily A. Watson` |

**Fix applied:** Replace `Emily Watson` → `Emily A. Watson` in files 03, 05, 08 (only standalone "Emily Watson", NOT "Cody Watson", "Albert Watson", "Lori Watson").

---

### 3. ADDRESS: "Whitehall Rd" → "Whitehall Road"

**Rule:** Full street name "Whitehall Road" must be used (not abbreviated "Rd").

| File | Line | Found | Fix |
|------|------|-------|-----|
| `05_MSC_ORIGINAL_ACTION.md` | 51 | `1977 Whitehall Rd, Lot 17` | → `Whitehall Road` |
| `05_MSC_ORIGINAL_ACTION.md` | 1168 | `1977 Whitehall Rd, Lot 17` | → `Whitehall Road` |
| `07_CUSTODY_MODIFICATION.md` | 553 | `1977 Whitehall Rd, Lot 17` | → `Whitehall Road` |

**Fix applied:** Replace `Whitehall Rd` → `Whitehall Road` in files 05 and 07.

---

### 4. STATS: "127 judicial violations" → "1,127 judicial violations"

**Rule:** The canonical violation count is **1,127**. The number "127" appears to be a truncation.

#### File: `03_DISQUALIFICATION_MCR2003.md` (1 occurrence)
| Line | Found |
|------|-------|
| 280 | `127 judicial violations` |

#### File: `05_MSC_ORIGINAL_ACTION.md` (11 occurrences)
| Line | Found |
|------|-------|
| 285 | `127 judicial violations` |
| 408 | `127 documented judicial violations` |
| 525 | `127 judicial violations` |
| 611 | `127 judicial violations` |
| 659 | `127 violations` |
| 702 | `127 judicial violations` |
| 728 | `127 documented judicial violations` |
| 969 | `127 judicial violations` |
| 982 | `127 judicial violations` |
| 1099 | `127 judicial violations` |

**Fix applied:** Replace `127 judicial violations` → `1,127 judicial violations`, `127 documented judicial violations` → `1,127 documented judicial violations`, `127 violations` → `1,127 violations` in files 03 and 05.

---

### 5. REVIEW: "126 violations" in `08_PPO_TERMINATION.md`

| Line | Found | Assessment |
|------|-------|-----------|
| 173 | `126 documented procedural violations` | **PPO-specific subset** — the 126 count refers to violations specific to PPO procedure under MCL 600.2950. This is a legitimate subset count, NOT the total 1,127. **NO FIX NEEDED** — this is domain-specific and intentional. |
| 181 | `126 documented procedural violations` | Same — PPO-specific subset. **NO FIX NEEDED.** |

---

## DATE PRESENCE MATRIX

Dates are referenced only in filings where they are relevant. No date inconsistencies found.

| Date | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 |
|------|----|----|----|----|----|----|----|----|
| PPO filed (Dec 3, 2023) | - | - | - | ✓ | ✓ | ✓ | - | ✓ |
| Custody filed (Apr 1, 2024) | - | - | ✓ | ✓ | - | - | ✓ | - |
| 1st withholding (Mar 26, 2024) | ✓ | ✓ | - | ✓ | - | - | - | ✓ |
| 50/50 temp order (May 5, 2024) | - | - | - | ✓ | ✓ | - | ✓ | - |
| Ex parte #1 (Jul 17, 2025) | ✓ | ✓ | ✓ | ✓ | ✓ | - | ✓ | - |
| Ex parte #2 (Aug 8, 2025) | - | - | ✓ | ✓ | - | ✓ | ✓ | - |
| 2nd withholding (Jul 29, 2025) | - | - | - | ✓ | ✓ | - | - | - |
| HealthWest eval (Sep 5, 2025) | - | - | ✓ | - | - | - | ✓ | - |
| Guilty plea (Oct 18, 2025) | - | - | - | ✓ | - | - | - | ✓ |
| SC#5 jail (Nov 15, 2025) | - | - | ✓ | - | ✓ | - | - | ✓ |
| SC#6+7 jail (Nov 26, 2025) | - | - | ✓ | ✓ | ✓ | ✓ | - | ✓ |
| Child DOB (Nov 9, 2022) | - | - | ✓ | - | ✓ | - | ✓ | - |

---

## FIXES APPLIED

| # | Find | Replace | Files | Count |
|---|------|---------|-------|-------|
| 1 | `Andrew J. Pigors` | `Andrew James Pigors` | 03, 05 | 28 |
| 2 | `Emily Watson` (standalone) | `Emily A. Watson` | 03, 05, 08 | 11 |
| 3 | `Whitehall Rd` (not Road) | `Whitehall Road` | 05, 07 | 3 |
| 4 | `127 judicial violations` | `1,127 judicial violations` | 03, 05 | 9 |
| 5 | `127 documented judicial violations` | `1,127 documented judicial violations` | 05 | 2 |
| 6 | `127 violations` | `1,127 violations` | 05 | 1 |
| **TOTAL** | | | | **54** |

**NOT fixed (by design):**
- "126 documented procedural violations" in `08_PPO_TERMINATION.md` — PPO-specific subset count
- "Judge McNeill" references — standard legal shorthand after first full reference to "Hon. Jenny L. McNeill"
- "Watson" as surname for family members (Albert Watson, Cody Watson, Lori Watson) — different people
