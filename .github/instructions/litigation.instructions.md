---
description: "Litigation case intelligence supplement — unique intel NOT in copilot-instructions.md. Pigors v. Watson operational details."
applyTo: "**/*.{md,txt,py,json,sql,docx}"
---

# Litigation Case Intelligence — Supplement

> Parties, case matrix, DB tables, and rules are in `.github/copilot-instructions.md`. This file has ONLY unique additions.

## HALLUCINATIONS PURGED (never regenerate)
1. **"91% alienation score"** → Fabricated. Use: "230+ days withheld, 7 PPO weaponizations, 3 jailings"
2. **"Tiffany Watson"** → Always "Emily A. Watson"
3. **"Lincoln David Watson"** → Always "L.D.W." per MCR 8.119(H)
4. **"Ron Berry, Esq."** → "Ronald Berry" (NON-ATTORNEY)
5. **"Jane Berry" / "Patricia Berry (P35878)"** → "Jennifer Barnes (P55406)" or "Ronald Berry"
6. **"9 CPS investigations"** → FABRICATED. Andrew called CPS once.

---

## SEPARATION CRISIS TIMELINE (detailed)

| Date | Event | Impact |
|------|-------|--------|
| Dec 3, 2023 | PPO filed AND granted same day (ex parte) | No notice, no hearing |
| Mar 26, 2024 | 1st withholding begins | 40-day deprivation |
| Apr 1, 2024 | Andrew files custody FIRST | Filing priority established |
| May 5, 2024 | 50/50 custody ordered | After 40-day withholding |
| Jul 17, 2024 | Custody trial → loss | 182.5 → 79 overnights |
| Jul 29, 2025 | **LAST CONTACT with L.D.W.** | Separation ongoing — compute dynamically |
| Aug 5, 2025 | USB audio recording at Watson home | Albert intimidation documented |
| Aug 7, 2025 | **NSPD NS2505044**: Albert admits premeditation | **SMOKING GUN** — 3 days before ex parte orders |
| Aug 8, 2025 | 5 ex parte orders in single day | Complete PT suspension |
| Nov 15, 2024 | Show Cause #5 → 14 days jail | Lost 1st house + 1st job |
| Nov 26, 2025 | Show Cause #6+7 → 45 days jail | Lost 2nd house + 2nd job |

---

## FILING STATUS & LOCATIONS

| Filing | Location | Status |
|--------|----------|--------|
| F01: MSC Petition | `05_FILINGS/GOLDEN_SET/F01_MSC_PETITION/` | ✅ Complete |
| F03: MCR 2.003 Disqualification | `05_FILINGS/GOLDEN_SET/F03_DISQUALIFICATION/` | ✅ Complete |
| F04: Federal §1983 | `05_FILINGS/GOLDEN_SET/F04_FEDERAL_1983/` | ✅ Complete |
| F05: MSC Original Action | `05_FILINGS/GOLDEN_SET/F05_MSC_ORIGINAL/` | ✅ Complete |
| F06: JTC Complaint | `05_FILINGS/GOLDEN_SET/F06_JTC_COMPLAINT/` | ⚠️ 32 exhibits missing |
| F08: PPO Termination | `05_FILINGS/GOLDEN_SET/F08_PPO_TERMINATION/` | ✅ Complete |
| F09: COA Brief | `05_FILINGS/GOLDEN_SET/F09_COA_BRIEF/` | ✅ Complete (8-tab appendix) |
| F10: COA Emergency | `05_FILINGS/GOLDEN_SET/F10_COA_EMERGENCY/` | ✅ Complete |

**Filing Sequence**: F03 → F06 → F05 → F09 (COA by Apr 30) → F04 (§1983) → F08

---

## TECHNICAL ENVIRONMENT

- **Shadow modules at repo root**: `json.py`, `typing.py`, `tokenize.py` — NEVER CWD to repo root for Python. Use `-I` flag.
- **Python**: 3.12.10 (system). `.mcp_venv` for MCP server venv.
- **J:\ drive**: exFAT — NO WAL mode. Use `PRAGMA journal_mode=DELETE` or `immutable=1`.
- **DB schema**: Run `PRAGMA table_info(table_name)` before first query. Production schemas may differ from DDL.
- **Tool hierarchy**: exec_python > exec_git > grep/glob > view/edit > sql > exec_command > PowerShell (LAST RESORT).

---

## KEY EVIDENCE (unique details)

- **Police reports**: 9 NSPD cases, ZERO arrests/charges across all contacts
- **HealthWest eval**: Psychosis=0, Substance=0, Danger=0, LOCUS=12/Level One — EXCLUDED by McNeill
- **Officer Ella Randall report**: Emily's METH USE admission — judge: "quit nitpicking"
- **AppClose logs**: 305+ interference incidents documented
- **Court outcomes**: Emily wins 85% of motions vs Andrew's 15%
- **Albert+Emily recording**: Audio `I:\08_AUDIO\albert and Emily audio nov 30 2023.mp3`, Video `I:\Appclose\EVERYTHIING\videos\Albertemily.mp4`

---

## DEBUNKED FALSE ALLEGATIONS

| Allegation | Status | Key Rebuttal |
|------------|--------|-------------|
| Arsenic/poisoning | **Debunked** (37 evidence) | No toxicology |
| Assault | **Debunked** (0 evidence) | No police report |
| Sexual assault | **Debunked** (15 evidence) | No investigation |
| Cocaine straw | **Debunked** (5 evidence) | Never tested |
| Meth use (projection) | **Debunked** (160 evidence) | Emily admitted to meth |
| Child abuse/danger | **Debunked** (49 evidence) | HealthWest all clear |
| Mental instability | **Debunked** (91 evidence) | LOCUS=12/Level One |

Pattern: Emily's allegations are projections of her own conduct.

---

## DB CONTEXT TABLES (on-demand query, not auto-loaded)

| Table | Content |
|-------|---------|
| `critical_facts` | Verified immutable facts |
| `narrative_context` | Categorized intel (strategy, evidence, judicial) |
| `evidence_exhibits` | Exhibit catalog with file paths + MRE basis |
| `police_reports` | Police report index with smoking gun quotes |
| `false_allegations` | Emily's allegation pattern with evidence |

---

## CRITICAL EXHIBITS (4 NOT YET LOCATED)

| Exhibit | Status | Why Critical |
|---------|--------|-------------|
| NS2505044 (Albert premeditation) | **NOT LOCATED** | Proves custody grab was premeditated |
| HealthWest Evaluation | **NOT LOCATED** | Proves judicial manipulation |
| Officer Randall Report | **NOT LOCATED** | Emily meth projection evidence |
| AppClose 305+ incidents | **NOT LOCATED** | Documents interference pattern |
