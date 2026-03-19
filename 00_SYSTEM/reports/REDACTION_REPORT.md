# 🔒 REDACTION ENGINE — MCR 8.119 Compliance Report
*Generated: 2026-03-18 23:24*
*103 files scanned*

---

## Summary
| Severity | Count | Action |
|----------|-------|--------|
| 🔴 CRITICAL | 0 | MUST redact before filing |
| 🟡 HIGH | 2 | Should redact |
| ℹ️ INFO | 110 | Review — may be intentional |
| **Total** | **147** | |

## MCR 8.119 Requirements
- **(D)(1)**: SSN — redact all but last 4 digits
- **(D)(2)**: Financial accounts — redact all but last 4 digits
- **(D)(3)**: DOB — use birth year only (not month/day)
- **(H)**: Minor children — use initials only (L.D.W.)

## ⚠️ Items Requiring Redaction
| File | Line | Type | Found | MCR |
|------|------|------|-------|-----|
| 01_MAIN_FILING.md | 102 | Financial Account | `Account #33700` | MCR 8.119(D)(2) |
| ASSEMBLED_FILING.md | 217 | Financial Account | `Account #33700` | MCR 8.119(D)(2) |

## ℹ️ Flagged Items (Review — May Be Intentional)
| File | Line | Type | Found |
|------|------|------|-------|
| 01_MAIN_FILING.md | 183 | Phone Number (personal) | `(231) 903-5690` |
| 01_MAIN_FILING.md | 222 | Phone Number (personal) | `(231) 903-5690` |
| 01_MAIN_FILING.md | 0 | FILE_ERROR | `'mcr'` |
| 02_AFFIDAVIT.md | 35 | Phone Number (personal) | `(231) 903-5690` |
| 02_AFFIDAVIT.md | 0 | FILE_ERROR | `'mcr'` |
| ASSEMBLED_FILING.md | 241 | Phone Number (personal) | `(231) 903-5690` |
| ASSEMBLED_FILING.md | 280 | Phone Number (personal) | `(231) 903-5690` |
| ASSEMBLED_FILING.md | 297 | Phone Number (personal) | `(231) 903-5690` |
| ASSEMBLED_FILING.md | 329 | Phone Number (personal) | `(231) 903-5690` |
| ASSEMBLED_FILING.md | 0 | FILE_ERROR | `'mcr'` |
| 01_MAIN_FILING.md | 10 | Phone Number (personal) | `(231) 903-5690` |
| 01_MAIN_FILING.md | 265 | Phone Number (personal) | `(231) 903-5690` |
| 01_MAIN_FILING.md | 483 | Phone Number (personal) | `(231) 903-5690` |
| 01_MAIN_FILING.md | 0 | FILE_ERROR | `'mcr'` |
| 02_AFFIDAVIT.md | 37 | Phone Number (personal) | `(231) 903-5690` |
| 02_AFFIDAVIT.md | 0 | FILE_ERROR | `'mcr'` |
| 07_FORM_FILL_GUIDE.md | 13 | Phone Number (personal) | `(231) 903-5690` |
| 07_FORM_FILL_GUIDE.md | 32 | Phone Number (personal) | `(231) 903-5690` |
| 07_FORM_FILL_GUIDE.md | 55 | Phone Number (personal) | `(231) 903-5690` |
| 07_FORM_FILL_GUIDE.md | 0 | FILE_ERROR | `'mcr'` |
*... and 125 more*

---
## Before Filing Checklist
- [ ] Review all CRITICAL findings and redact
- [ ] Ensure L.D.W. appears ONLY as initials
- [ ] Remove any SSNs (yours or Emily's)
- [ ] Redact financial account numbers
- [ ] Use birth year only (not full DOB) for minors

*Redaction Engine — Tool #70 — MCR 8.119 Compliance*