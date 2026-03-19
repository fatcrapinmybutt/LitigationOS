# COURT FILING COMPLIANCE REPORT
**Generated:** 2026-03-19 08:11:52
**Tool:** #216 Court Filing Compliance Validator
**Packages Scanned:** 10
**Average Score:** 75/100

---

## Summary Matrix

| Package | Type | Score | Verdict |
|---------|------|-------|---------|
| PKG_F10_COA_EMERGENCY_MOTION | F10 | 80/100 | ⚠️ ⚠️ CONDITIONAL GO — Address warnings before filing |
| PKG_F1_EMERGENCY_TRO | F1 | 86/100 | ⚠️ ⚠️ CONDITIONAL GO — Address warnings before filing |
| PKG_F2_SHADY_OAKS_COMPLAINT | F2 | 86/100 | ⚠️ ⚠️ CONDITIONAL GO — Address warnings before filing |
| PKG_F3_DISQUALIFICATION_MCR_2003 | F3 | 50/100 | 🔶 🔶 NO-GO (FIXABLE) — Multiple issues need attention |
| PKG_F4_FEDERAL_S1983_COMPLAINT | F4 | 50/100 | 🔶 🔶 NO-GO (FIXABLE) — Multiple issues need attention |
| PKG_F5_MSC_ORIGINAL_ACTION | F5 | 50/100 | 🔶 🔶 NO-GO (FIXABLE) — Multiple issues need attention |
| PKG_F6_JTC_COMPLAINT | F6 | 87/100 | ⚠️ ⚠️ CONDITIONAL GO — Address warnings before filing |
| PKG_F7_CUSTODY_MODIFICATION | F7 | 88/100 | ⚠️ ⚠️ CONDITIONAL GO — Address warnings before filing |
| PKG_F8_PPO_TERMINATION | F8 | 83/100 | ⚠️ ⚠️ CONDITIONAL GO — Address warnings before filing |
| PKG_F9_COA_BRIEF_ON_APPEAL | F9 | 91/100 | ✅ ✅ GO — Ready for filing (minor warnings may remain) |

---

## PKG_F10_COA_EMERGENCY_MOTION — COA Emergency Motion
**Filing Type:** F10 | **Court:** Court of Appeals
**Score:** 80/100 | **Verdict:** ⚠️ CONDITIONAL GO — Address warnings before filing

### ⚠️ Universal Formatting (12/17)

- ✅ **UF-01: Caption includes court name**
- ✅ **UF-02: Caption includes case number**
- ✅ **UF-03: Caption includes party names**
- ✅ **UF-04: Document title present**
- ✅ **UF-05: Signature block includes name**
- ✅ **UF-06: Signature block includes address**
- ✅ **UF-07: Signature block includes phone**
- ❌ **UF-08: Date present in signature block or filing**
  - FIX: Add date in signature block (e.g., 'Dated: Month DD, YYYY')
- ✅ **UF-09: Certificate of service present**
- ❌ **UF-10: Certificate of service includes date served**
  - FIX: Certificate of service must state date of service
- ❌ **UF-11: Certificate of service includes method of service**
  - FIX: State method of service (e.g., 'first-class mail', 'MiFILE e-service', 'hand delivery')
- ✅ **UF-12: Certificate of service lists opposing party**
- ❌ **UF-13: No placeholder text remaining**
  - FIX: Remove 3 placeholder(s): ___________________, ______________________________, ___________________
- ✅ **UF-14: Pages appear consecutively numbered**
- ✅ **UF-15: Pro se status identified**
- ❌ **UF-16: Electronic signature format (/s/ Name) present**
  - FIX: For e-filing, use '/s/ Andrew James Pigors' as electronic signature
- ✅ **UF-17: Child referred to by initials only (MCR 8.119(H))**

### ✅ Anti-Hallucination Guard (8/8)

- ✅ **AH-01: No fabricated 'Jane Berry' (hallucination)**
- ✅ **AH-02: No fabricated 'Patricia Berry' (hallucination)**
- ✅ **AH-03: No wrong judge name 'Amy McNeill'**
- ✅ **AH-04: Ronald Berry not listed as attorney (he is not one)**
- ✅ **AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)**
- ✅ **AH-06: No fabricated '91% alienation score'**
- ✅ **AH-07: No fabricated '9 CPS investigations'**
- ✅ **AH-08: No wrong name 'Tiffany' for defendant**

### ✅ Common Rejection Screening (5/5)

- ✅ **CR-01: Case number present**
- ✅ **CR-02: Document appears legible (no binary garbage)**
- ✅ **CR-03: All files have substantive content**
- ✅ **CR-04: No bundled unrelated documents**
  - WARN: Verify each file contains only ONE document type when converting to PDF
- ✅ **CR-05: Required signature(s) present**

### ⚠️ F10: COA Emergency Motion (6/8)

- ✅ **F10-01: 'EMERGENCY' label prominent on first page**
- ❌ **F10-02: References MCR 7.211(C)(6) for immediate consideration**
  - FIX: Cite MCR 7.211(C)(6) — standard for emergency/immediate consideration
- ❌ **F10-03: Peremptory reversal: MCR 7.211(C)(4) + 'manifest error'**
  - FIX: For peremptory reversal, cite MCR 7.211(C)(4) and demonstrate 'manifest error' standard
- ✅ **F10-04: Brief portion within limits (max 50 pages / 14,000 words)**
- ✅ **F10-05: $375 filing fee referenced OR IFP application attached**
- ✅ **F10-06: Filed within 21 days of final order (or delay explained)**
- ✅ **F10-07: Served on ALL parties (Watson, FOC, lower court)**
- ✅ **F10-08: Caption includes COA Case No. 366810**

### ⚠️ MiFILE E-Filing (5/7)

- ✅ **EF-01: Each document is a separate file (not bundled)**
- ❌ **EF-02: Electronic signature format: /s/ Andrew James Pigors**
  - FIX: Add '/s/ Andrew James Pigors' as electronic signature for e-filing
- ❌ **EF-03: PDF format noted (recommended for MiFILE)**
  - WARN: Ensure documents are converted to PDF before uploading to MiFILE
- ✅ **EF-04: Descriptive file names with case number**
  - WARN: Consider adding case number to file names for MiFILE
- ✅ **EF-05: File size under 25 MB each**
  - WARN: Verify each PDF is under 25 MB (conservative: under 10 MB) before e-filing
- ✅ **EF-06: Scanned documents at 300 dpi B&W/grayscale**
  - WARN: If any scanned exhibits, ensure 300 dpi B&W or grayscale for legibility
- ✅ **EF-07: No password-protected or restricted PDFs**
  - WARN: Ensure no PDFs are password-protected before uploading to MiFILE

---

## PKG_F1_EMERGENCY_TRO — Emergency TRO
**Filing Type:** F1 | **Court:** 14th Circuit
**Score:** 86/100 | **Verdict:** ⚠️ CONDITIONAL GO — Address warnings before filing

### ⚠️ Universal Formatting (14/17)

- ✅ **UF-01: Caption includes court name**
- ✅ **UF-02: Caption includes case number**
- ✅ **UF-03: Caption includes party names**
- ✅ **UF-04: Document title present**
- ✅ **UF-05: Signature block includes name**
- ✅ **UF-06: Signature block includes address**
- ✅ **UF-07: Signature block includes phone**
- ✅ **UF-08: Date present in signature block or filing**
- ✅ **UF-09: Certificate of service present**
- ❌ **UF-10: Certificate of service includes date served**
  - FIX: Certificate of service must state date of service
- ✅ **UF-11: Certificate of service includes method of service**
- ✅ **UF-12: Certificate of service lists opposing party**
- ❌ **UF-13: No placeholder text remaining**
  - FIX: Remove 6 placeholder(s): [DATE OF FILING], [DATE OF FILING], [DATE OF SERVICE], ___________________________, _________________
- ✅ **UF-14: Pages appear consecutively numbered**
- ✅ **UF-15: Pro se status identified**
- ❌ **UF-16: Electronic signature format (/s/ Name) present**
  - FIX: For e-filing, use '/s/ Andrew James Pigors' as electronic signature
- ✅ **UF-17: Child referred to by initials only (MCR 8.119(H))**

### ✅ Anti-Hallucination Guard (8/8)

- ✅ **AH-01: No fabricated 'Jane Berry' (hallucination)**
- ✅ **AH-02: No fabricated 'Patricia Berry' (hallucination)**
- ✅ **AH-03: No wrong judge name 'Amy McNeill'**
- ✅ **AH-04: Ronald Berry not listed as attorney (he is not one)**
- ✅ **AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)**
- ✅ **AH-06: No fabricated '91% alienation score'**
- ✅ **AH-07: No fabricated '9 CPS investigations'**
- ✅ **AH-08: No wrong name 'Tiffany' for defendant**

### ✅ Common Rejection Screening (5/5)

- ✅ **CR-01: Case number present**
- ✅ **CR-02: Document appears legible (no binary garbage)**
- ✅ **CR-03: All files have substantive content**
- ✅ **CR-04: No bundled unrelated documents**
  - WARN: Verify each file contains only ONE document type when converting to PDF
- ✅ **CR-05: Required signature(s) present**

### ⚠️ MiFILE E-Filing (5/7)

- ✅ **EF-01: Each document is a separate file (not bundled)**
- ❌ **EF-02: Electronic signature format: /s/ Andrew James Pigors**
  - FIX: Add '/s/ Andrew James Pigors' as electronic signature for e-filing
- ❌ **EF-03: PDF format noted (recommended for MiFILE)**
  - WARN: Ensure documents are converted to PDF before uploading to MiFILE
- ✅ **EF-04: Descriptive file names with case number**
  - WARN: Consider adding case number to file names for MiFILE
- ✅ **EF-05: File size under 25 MB each**
  - WARN: Verify each PDF is under 25 MB (conservative: under 10 MB) before e-filing
- ✅ **EF-06: Scanned documents at 300 dpi B&W/grayscale**
  - WARN: If any scanned exhibits, ensure 300 dpi B&W or grayscale for legibility
- ✅ **EF-07: No password-protected or restricted PDFs**
  - WARN: Ensure no PDFs are password-protected before uploading to MiFILE

---

## PKG_F2_SHADY_OAKS_COMPLAINT — Shady Oaks Complaint
**Filing Type:** F2 | **Court:** 14th Circuit
**Score:** 86/100 | **Verdict:** ⚠️ CONDITIONAL GO — Address warnings before filing

### ⚠️ Universal Formatting (14/17)

- ✅ **UF-01: Caption includes court name**
- ✅ **UF-02: Caption includes case number**
- ✅ **UF-03: Caption includes party names**
- ✅ **UF-04: Document title present**
- ✅ **UF-05: Signature block includes name**
- ✅ **UF-06: Signature block includes address**
- ✅ **UF-07: Signature block includes phone**
- ✅ **UF-08: Date present in signature block or filing**
- ✅ **UF-09: Certificate of service present**
- ❌ **UF-10: Certificate of service includes date served**
  - FIX: Certificate of service must state date of service
- ✅ **UF-11: Certificate of service includes method of service**
- ✅ **UF-12: Certificate of service lists opposing party**
- ❌ **UF-13: No placeholder text remaining**
  - FIX: Remove 8 placeholder(s): [ANDREW: Consider filing a parallel LARA complaint regarding License #1201891 — this strengthens the civil case and creates an independent enforcement record.], [ANDREW: Consider filing a parallel LARA complaint regarding License #1201891 — this strengthens the civil case and creates an independent enforcement record.], [DATE OF FILING], [DATE OF FILING], [DATE OF FILING]
- ✅ **UF-14: Pages appear consecutively numbered**
- ✅ **UF-15: Pro se status identified**
- ❌ **UF-16: Electronic signature format (/s/ Name) present**
  - FIX: For e-filing, use '/s/ Andrew James Pigors' as electronic signature
- ✅ **UF-17: Child referred to by initials only (MCR 8.119(H))**

### ✅ Anti-Hallucination Guard (8/8)

- ✅ **AH-01: No fabricated 'Jane Berry' (hallucination)**
- ✅ **AH-02: No fabricated 'Patricia Berry' (hallucination)**
- ✅ **AH-03: No wrong judge name 'Amy McNeill'**
- ✅ **AH-04: Ronald Berry not listed as attorney (he is not one)**
- ✅ **AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)**
- ✅ **AH-06: No fabricated '91% alienation score'**
- ✅ **AH-07: No fabricated '9 CPS investigations'**
- ✅ **AH-08: No wrong name 'Tiffany' for defendant**

### ✅ Common Rejection Screening (5/5)

- ✅ **CR-01: Case number present**
- ✅ **CR-02: Document appears legible (no binary garbage)**
- ✅ **CR-03: All files have substantive content**
- ✅ **CR-04: No bundled unrelated documents**
  - WARN: Verify each file contains only ONE document type when converting to PDF
- ✅ **CR-05: Required signature(s) present**

### ⚠️ MiFILE E-Filing (5/7)

- ✅ **EF-01: Each document is a separate file (not bundled)**
- ❌ **EF-02: Electronic signature format: /s/ Andrew James Pigors**
  - FIX: Add '/s/ Andrew James Pigors' as electronic signature for e-filing
- ❌ **EF-03: PDF format noted (recommended for MiFILE)**
  - WARN: Ensure documents are converted to PDF before uploading to MiFILE
- ✅ **EF-04: Descriptive file names with case number**
  - WARN: Consider adding case number to file names for MiFILE
- ✅ **EF-05: File size under 25 MB each**
  - WARN: Verify each PDF is under 25 MB (conservative: under 10 MB) before e-filing
- ✅ **EF-06: Scanned documents at 300 dpi B&W/grayscale**
  - WARN: If any scanned exhibits, ensure 300 dpi B&W or grayscale for legibility
- ✅ **EF-07: No password-protected or restricted PDFs**
  - WARN: Ensure no PDFs are password-protected before uploading to MiFILE

---

## PKG_F3_DISQUALIFICATION_MCR_2003 — MCR 2.003 Disqualification
**Filing Type:** F3 | **Court:** 14th Circuit
**Score:** 50/100 | **Verdict:** 🔶 NO-GO (FIXABLE) — Multiple issues need attention

### ⚠️ Universal Formatting (14/17)

- ✅ **UF-01: Caption includes court name**
- ✅ **UF-02: Caption includes case number**
- ✅ **UF-03: Caption includes party names**
- ✅ **UF-04: Document title present**
- ✅ **UF-05: Signature block includes name**
- ✅ **UF-06: Signature block includes address**
- ✅ **UF-07: Signature block includes phone**
- ✅ **UF-08: Date present in signature block or filing**
- ✅ **UF-09: Certificate of service present**
- ❌ **UF-10: Certificate of service includes date served**
  - FIX: Certificate of service must state date of service
- ✅ **UF-11: Certificate of service includes method of service**
- ✅ **UF-12: Certificate of service lists opposing party**
- ❌ **UF-13: No placeholder text remaining**
  - FIX: Remove 9 placeholder(s): [ANDREW: SIGN AND DATE], [ANDREW: NOTARIZE BEFORE FILING], [ANDREW: SIGN AND DATE], [DATE OF FILING], [DATE OF FILING]
- ✅ **UF-14: Pages appear consecutively numbered**
- ✅ **UF-15: Pro se status identified**
- ❌ **UF-16: Electronic signature format (/s/ Name) present**
  - FIX: For e-filing, use '/s/ Andrew James Pigors' as electronic signature
- ✅ **UF-17: Child referred to by initials only (MCR 8.119(H))**

### ⚠️ Anti-Hallucination Guard (7/8)

- ✅ **AH-01: No fabricated 'Jane Berry' (hallucination)**
- ✅ **AH-02: No fabricated 'Patricia Berry' (hallucination)**
- ✅ **AH-03: No wrong judge name 'Amy McNeill'**
- ❌ **AH-04: Ronald Berry not listed as attorney (he is not one)**
  - CRITICAL: Ronald Berry is NOT an attorney. No bar number. No 'Esq.' Remove.
- ✅ **AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)**
- ✅ **AH-06: No fabricated '91% alienation score'**
- ✅ **AH-07: No fabricated '9 CPS investigations'**
- ✅ **AH-08: No wrong name 'Tiffany' for defendant**

### ✅ Common Rejection Screening (5/5)

- ✅ **CR-01: Case number present**
- ✅ **CR-02: Document appears legible (no binary garbage)**
- ✅ **CR-03: All files have substantive content**
- ✅ **CR-04: No bundled unrelated documents**
  - WARN: Verify each file contains only ONE document type when converting to PDF
- ✅ **CR-05: Required signature(s) present**

### ✅ F3: MCR 2.003 Disqualification (9/9)

- ✅ **F3-01: Caption includes Case No. 2024-001507-DC**
- ✅ **F3-02: References MCR 2.003(C) grounds**
- ✅ **F3-03: States specific grounds (bias/prejudice, Caperton, Canon 2)**
- ✅ **F3-04: Affidavit attached with factual grounds**
- ✅ **F3-05: Filed within 14 days of discovery (or good cause shown)**
- ✅ **F3-06: MC 264 form referenced or attached**
- ✅ **F3-07: Certificate of service includes Watson + FOC + Court Clerk**
- ✅ **F3-08: Exhibit index present (exhibits must be separate)**
- ✅ **F3-09: Correct judge name (Hon. Jenny L. McNeill)**

### ⚠️ MiFILE E-Filing (5/7)

- ✅ **EF-01: Each document is a separate file (not bundled)**
- ❌ **EF-02: Electronic signature format: /s/ Andrew James Pigors**
  - FIX: Add '/s/ Andrew James Pigors' as electronic signature for e-filing
- ❌ **EF-03: PDF format noted (recommended for MiFILE)**
  - WARN: Ensure documents are converted to PDF before uploading to MiFILE
- ✅ **EF-04: Descriptive file names with case number**
  - WARN: Consider adding case number to file names for MiFILE
- ✅ **EF-05: File size under 25 MB each**
  - WARN: Verify each PDF is under 25 MB (conservative: under 10 MB) before e-filing
- ✅ **EF-06: Scanned documents at 300 dpi B&W/grayscale**
  - WARN: If any scanned exhibits, ensure 300 dpi B&W or grayscale for legibility
- ✅ **EF-07: No password-protected or restricted PDFs**
  - WARN: Ensure no PDFs are password-protected before uploading to MiFILE

---

## PKG_F4_FEDERAL_S1983_COMPLAINT — Federal §1983 Complaint
**Filing Type:** F4 | **Court:** WDMI Federal
**Score:** 50/100 | **Verdict:** 🔶 NO-GO (FIXABLE) — Multiple issues need attention

### ⚠️ Universal Formatting (13/17)

- ✅ **UF-01: Caption includes court name**
- ✅ **UF-02: Caption includes case number**
- ✅ **UF-03: Caption includes party names**
- ✅ **UF-04: Document title present**
- ✅ **UF-05: Signature block includes name**
- ✅ **UF-06: Signature block includes address**
- ✅ **UF-07: Signature block includes phone**
- ❌ **UF-08: Date present in signature block or filing**
  - FIX: Add date in signature block (e.g., 'Dated: Month DD, YYYY')
- ✅ **UF-09: Certificate of service present**
- ❌ **UF-10: Certificate of service includes date served**
  - FIX: Certificate of service must state date of service
- ✅ **UF-11: Certificate of service includes method of service**
- ✅ **UF-12: Certificate of service lists opposing party**
- ❌ **UF-13: No placeholder text remaining**
  - FIX: Remove 6 placeholder(s): [ANDREW: FILE IFP APPLICATION SEPARATELY], [ANDREW: SIGN AND DATE], [ANDREW: SIGN AND DATE], _______________, _______________________________________
- ✅ **UF-14: Pages appear consecutively numbered**
- ✅ **UF-15: Pro se status identified**
- ❌ **UF-16: Electronic signature format (/s/ Name) present**
  - FIX: For e-filing, use '/s/ Andrew James Pigors' as electronic signature
- ✅ **UF-17: Child referred to by initials only (MCR 8.119(H))**

### ⚠️ Anti-Hallucination Guard (7/8)

- ✅ **AH-01: No fabricated 'Jane Berry' (hallucination)**
- ✅ **AH-02: No fabricated 'Patricia Berry' (hallucination)**
- ✅ **AH-03: No wrong judge name 'Amy McNeill'**
- ❌ **AH-04: Ronald Berry not listed as attorney (he is not one)**
  - CRITICAL: Ronald Berry is NOT an attorney. No bar number. No 'Esq.' Remove.
- ✅ **AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)**
- ✅ **AH-06: No fabricated '91% alienation score'**
- ✅ **AH-07: No fabricated '9 CPS investigations'**
- ✅ **AH-08: No wrong name 'Tiffany' for defendant**

### ✅ Common Rejection Screening (5/5)

- ✅ **CR-01: Case number present**
- ✅ **CR-02: Document appears legible (no binary garbage)**
- ✅ **CR-03: All files have substantive content**
- ✅ **CR-04: No bundled unrelated documents**
  - WARN: Verify each file contains only ONE document type when converting to PDF
- ✅ **CR-05: Required signature(s) present**

### ⚠️ F4: Federal §1983 Complaint (6/7)

- ✅ **F4-01: $402 filing fee OR IFP affidavit**
- ✅ **F4-02: 'Under color of state law' alleged + §1983 cited**
- ❌ **F4-03: 3-year statute of limitations addressed**
  - FIX: Address the 3-year statute of limitations for §1983 claims
- ✅ **F4-04: Each defendant specifically named with role**
- ✅ **F4-05: Numbered paragraphs**
- ✅ **F4-06: Jurisdiction + venue stated**
- ✅ **F4-07: Pro Se format per WDMI Pro Se Handbook**

---

## PKG_F5_MSC_ORIGINAL_ACTION — MSC Original Action
**Filing Type:** F5 | **Court:** Michigan Supreme Court
**Score:** 50/100 | **Verdict:** 🔶 NO-GO (FIXABLE) — Multiple issues need attention

### ⚠️ Universal Formatting (13/17)

- ✅ **UF-01: Caption includes court name**
- ✅ **UF-02: Caption includes case number**
- ✅ **UF-03: Caption includes party names**
- ✅ **UF-04: Document title present**
- ✅ **UF-05: Signature block includes name**
- ✅ **UF-06: Signature block includes address**
- ✅ **UF-07: Signature block includes phone**
- ❌ **UF-08: Date present in signature block or filing**
  - FIX: Add date in signature block (e.g., 'Dated: Month DD, YYYY')
- ✅ **UF-09: Certificate of service present**
- ❌ **UF-10: Certificate of service includes date served**
  - FIX: Certificate of service must state date of service
- ✅ **UF-11: Certificate of service includes method of service**
- ✅ **UF-12: Certificate of service lists opposing party**
- ❌ **UF-13: No placeholder text remaining**
  - FIX: Remove 6 placeholder(s): [ANDREW: SIGN AND DATE the Oath and Signature block above], [ANDREW: NOTARIZE BEFORE FILING — take this document and valid photo ID to a notary public], [ANDREW: SIGN AND DATE after completing service on all parties], _________________, _______________
- ✅ **UF-14: Pages appear consecutively numbered**
- ✅ **UF-15: Pro se status identified**
- ❌ **UF-16: Electronic signature format (/s/ Name) present**
  - FIX: For e-filing, use '/s/ Andrew James Pigors' as electronic signature
- ✅ **UF-17: Child referred to by initials only (MCR 8.119(H))**

### ⚠️ Anti-Hallucination Guard (7/8)

- ✅ **AH-01: No fabricated 'Jane Berry' (hallucination)**
- ✅ **AH-02: No fabricated 'Patricia Berry' (hallucination)**
- ✅ **AH-03: No wrong judge name 'Amy McNeill'**
- ❌ **AH-04: Ronald Berry not listed as attorney (he is not one)**
  - CRITICAL: Ronald Berry is NOT an attorney. No bar number. No 'Esq.' Remove.
- ✅ **AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)**
- ✅ **AH-06: No fabricated '91% alienation score'**
- ✅ **AH-07: No fabricated '9 CPS investigations'**
- ✅ **AH-08: No wrong name 'Tiffany' for defendant**

### ✅ Common Rejection Screening (5/5)

- ✅ **CR-01: Case number present**
- ✅ **CR-02: Document appears legible (no binary garbage)**
- ✅ **CR-03: All files have substantive content**
- ✅ **CR-04: No bundled unrelated documents**
  - WARN: Verify each file contains only ONE document type when converting to PDF
- ✅ **CR-05: Required signature(s) present**

### ⚠️ MiFILE E-Filing (6/7)

- ✅ **EF-01: Each document is a separate file (not bundled)**
- ❌ **EF-02: Electronic signature format: /s/ Andrew James Pigors**
  - FIX: Add '/s/ Andrew James Pigors' as electronic signature for e-filing
- ✅ **EF-03: PDF format noted (recommended for MiFILE)**
- ✅ **EF-04: Descriptive file names with case number**
  - WARN: Consider adding case number to file names for MiFILE
- ✅ **EF-05: File size under 25 MB each**
  - WARN: Verify each PDF is under 25 MB (conservative: under 10 MB) before e-filing
- ✅ **EF-06: Scanned documents at 300 dpi B&W/grayscale**
  - WARN: If any scanned exhibits, ensure 300 dpi B&W or grayscale for legibility
- ✅ **EF-07: No password-protected or restricted PDFs**
  - WARN: Ensure no PDFs are password-protected before uploading to MiFILE

---

## PKG_F6_JTC_COMPLAINT — JTC Complaint
**Filing Type:** F6 | **Court:** JTC (Mail Only)
**Score:** 87/100 | **Verdict:** ⚠️ CONDITIONAL GO — Address warnings before filing

### ⚠️ Universal Formatting (14/17)

- ✅ **UF-01: Caption includes court name**
- ✅ **UF-02: Caption includes case number**
- ✅ **UF-03: Caption includes party names**
- ✅ **UF-04: Document title present**
- ✅ **UF-05: Signature block includes name**
- ✅ **UF-06: Signature block includes address**
- ✅ **UF-07: Signature block includes phone**
- ✅ **UF-08: Date present in signature block or filing**
- ✅ **UF-09: Certificate of service present**
- ❌ **UF-10: Certificate of service includes date served**
  - FIX: Certificate of service must state date of service
- ✅ **UF-11: Certificate of service includes method of service**
- ✅ **UF-12: Certificate of service lists opposing party**
- ❌ **UF-13: No placeholder text remaining**
  - FIX: Remove 6 placeholder(s): [ANDREW: SIGN AND DATE], [ANDREW: SIGN AND DATE], [ANDREW: SIGN AND DATE], ____________________, ____________________
- ✅ **UF-14: Pages appear consecutively numbered**
- ✅ **UF-15: Pro se status identified**
- ❌ **UF-16: Electronic signature format (/s/ Name) present**
  - FIX: For e-filing, use '/s/ Andrew James Pigors' as electronic signature
- ✅ **UF-17: Child referred to by initials only (MCR 8.119(H))**

### ✅ Anti-Hallucination Guard (8/8)

- ✅ **AH-01: No fabricated 'Jane Berry' (hallucination)**
- ✅ **AH-02: No fabricated 'Patricia Berry' (hallucination)**
- ✅ **AH-03: No wrong judge name 'Amy McNeill'**
- ✅ **AH-04: Ronald Berry not listed as attorney (he is not one)**
- ✅ **AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)**
- ✅ **AH-06: No fabricated '91% alienation score'**
- ✅ **AH-07: No fabricated '9 CPS investigations'**
- ✅ **AH-08: No wrong name 'Tiffany' for defendant**

### ✅ Common Rejection Screening (5/5)

- ✅ **CR-01: Case number present**
- ✅ **CR-02: Document appears legible (no binary garbage)**
- ✅ **CR-03: All files have substantive content**
- ✅ **CR-04: No bundled unrelated documents**
  - WARN: Verify each file contains only ONE document type when converting to PDF
- ✅ **CR-05: Required signature(s) present**

### ⚠️ F6: JTC Complaint (7/9)

- ✅ **F6-01: ⚠️ Marked as MAIL-ONLY (cannot be e-filed)**
- ❌ **F6-02: Correct JTC address (3034 W. Grand Blvd., Suite 8-350, Detroit, MI 48202)**
  - FIX: JTC address is 3034 W. Grand Blvd., Suite 8-350, Detroit, MI 48202 (NOT Suite 8-450!)
- ✅ **F6-03: Uses 'Request for Investigation' form/format**
- ✅ **F6-04: Notarization noted (complaint must be notarized)**
- ❌ **F6-05: Attaches COPIES of evidence (not originals)**
  - FIX: Note that COPIES (not originals) of evidence are attached
- ✅ **F6-06: Focuses on CONDUCT violations (JTC cannot reverse rulings)**
- ✅ **F6-07: Detailed factual description of misconduct**
- ✅ **F6-08: JTC phone (313) 875-5110 referenced**
- ✅ **F6-09: Names correct judge (Hon. Jenny L. McNeill)**

---

## PKG_F7_CUSTODY_MODIFICATION — Custody Modification
**Filing Type:** F7 | **Court:** 14th Circuit
**Score:** 88/100 | **Verdict:** ⚠️ CONDITIONAL GO — Address warnings before filing

### ⚠️ Universal Formatting (14/17)

- ✅ **UF-01: Caption includes court name**
- ✅ **UF-02: Caption includes case number**
- ✅ **UF-03: Caption includes party names**
- ✅ **UF-04: Document title present**
- ✅ **UF-05: Signature block includes name**
- ✅ **UF-06: Signature block includes address**
- ✅ **UF-07: Signature block includes phone**
- ✅ **UF-08: Date present in signature block or filing**
- ✅ **UF-09: Certificate of service present**
- ❌ **UF-10: Certificate of service includes date served**
  - FIX: Certificate of service must state date of service
- ✅ **UF-11: Certificate of service includes method of service**
- ✅ **UF-12: Certificate of service lists opposing party**
- ❌ **UF-13: No placeholder text remaining**
  - FIX: Remove 9 placeholder(s): [ANDREW: SIGN AND DATE], [ANDREW: SIGN AND DATE], [ANDREW: SIGN AND DATE], [DATE OF FILING], [DATE OF FILING]
- ✅ **UF-14: Pages appear consecutively numbered**
- ✅ **UF-15: Pro se status identified**
- ❌ **UF-16: Electronic signature format (/s/ Name) present**
  - FIX: For e-filing, use '/s/ Andrew James Pigors' as electronic signature
- ✅ **UF-17: Child referred to by initials only (MCR 8.119(H))**

### ✅ Anti-Hallucination Guard (8/8)

- ✅ **AH-01: No fabricated 'Jane Berry' (hallucination)**
- ✅ **AH-02: No fabricated 'Patricia Berry' (hallucination)**
- ✅ **AH-03: No wrong judge name 'Amy McNeill'**
- ✅ **AH-04: Ronald Berry not listed as attorney (he is not one)**
- ✅ **AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)**
- ✅ **AH-06: No fabricated '91% alienation score'**
- ✅ **AH-07: No fabricated '9 CPS investigations'**
- ✅ **AH-08: No wrong name 'Tiffany' for defendant**

### ✅ Common Rejection Screening (5/5)

- ✅ **CR-01: Case number present**
- ✅ **CR-02: Document appears legible (no binary garbage)**
- ✅ **CR-03: All files have substantive content**
- ✅ **CR-04: No bundled unrelated documents**
  - WARN: Verify each file contains only ONE document type when converting to PDF
- ✅ **CR-05: Required signature(s) present**

### ✅ F7: Custody Modification (6/6)

- ✅ **F7-01: Case No. 2024-001507-DC in caption**
- ✅ **F7-02: Presumption of parenting time with BOTH parents cited**
- ✅ **F7-03: 'Clear and convincing evidence' standard cited for denial**
- ✅ **F7-04: 'Proper cause' or 'change of circumstances' threshold met**
- ✅ **F7-05: Best interest factors (MCL 722.23) addressed**
- ✅ **F7-06: Child referred to as L.D.W. (initials only)**

### ⚠️ MiFILE E-Filing (5/7)

- ✅ **EF-01: Each document is a separate file (not bundled)**
- ❌ **EF-02: Electronic signature format: /s/ Andrew James Pigors**
  - FIX: Add '/s/ Andrew James Pigors' as electronic signature for e-filing
- ❌ **EF-03: PDF format noted (recommended for MiFILE)**
  - WARN: Ensure documents are converted to PDF before uploading to MiFILE
- ✅ **EF-04: Descriptive file names with case number**
  - WARN: Consider adding case number to file names for MiFILE
- ✅ **EF-05: File size under 25 MB each**
  - WARN: Verify each PDF is under 25 MB (conservative: under 10 MB) before e-filing
- ✅ **EF-06: Scanned documents at 300 dpi B&W/grayscale**
  - WARN: If any scanned exhibits, ensure 300 dpi B&W or grayscale for legibility
- ✅ **EF-07: No password-protected or restricted PDFs**
  - WARN: Ensure no PDFs are password-protected before uploading to MiFILE

---

## PKG_F8_PPO_TERMINATION — PPO Termination
**Filing Type:** F8 | **Court:** 14th Circuit
**Score:** 83/100 | **Verdict:** ⚠️ CONDITIONAL GO — Address warnings before filing

### ⚠️ Universal Formatting (13/17)

- ✅ **UF-01: Caption includes court name**
- ✅ **UF-02: Caption includes case number**
- ✅ **UF-03: Caption includes party names**
- ✅ **UF-04: Document title present**
- ✅ **UF-05: Signature block includes name**
- ✅ **UF-06: Signature block includes address**
- ✅ **UF-07: Signature block includes phone**
- ❌ **UF-08: Date present in signature block or filing**
  - FIX: Add date in signature block (e.g., 'Dated: Month DD, YYYY')
- ✅ **UF-09: Certificate of service present**
- ❌ **UF-10: Certificate of service includes date served**
  - FIX: Certificate of service must state date of service
- ✅ **UF-11: Certificate of service includes method of service**
- ✅ **UF-12: Certificate of service lists opposing party**
- ❌ **UF-13: No placeholder text remaining**
  - FIX: Remove 6 placeholder(s): [ANDREW: SIGN AND DATE], [ANDREW: SIGN AND DATE], [ANDREW: SIGN AND DATE], _______________________________________, ______________________________
- ✅ **UF-14: Pages appear consecutively numbered**
- ✅ **UF-15: Pro se status identified**
- ❌ **UF-16: Electronic signature format (/s/ Name) present**
  - FIX: For e-filing, use '/s/ Andrew James Pigors' as electronic signature
- ✅ **UF-17: Child referred to by initials only (MCR 8.119(H))**

### ✅ Anti-Hallucination Guard (8/8)

- ✅ **AH-01: No fabricated 'Jane Berry' (hallucination)**
- ✅ **AH-02: No fabricated 'Patricia Berry' (hallucination)**
- ✅ **AH-03: No wrong judge name 'Amy McNeill'**
- ✅ **AH-04: Ronald Berry not listed as attorney (he is not one)**
- ✅ **AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)**
- ✅ **AH-06: No fabricated '91% alienation score'**
- ✅ **AH-07: No fabricated '9 CPS investigations'**
- ✅ **AH-08: No wrong name 'Tiffany' for defendant**

### ✅ Common Rejection Screening (5/5)

- ✅ **CR-01: Case number present**
- ✅ **CR-02: Document appears legible (no binary garbage)**
- ✅ **CR-03: All files have substantive content**
- ✅ **CR-04: No bundled unrelated documents**
  - WARN: Verify each file contains only ONE document type when converting to PDF
- ✅ **CR-05: Required signature(s) present**

### ⚠️ MiFILE E-Filing (5/7)

- ✅ **EF-01: Each document is a separate file (not bundled)**
- ❌ **EF-02: Electronic signature format: /s/ Andrew James Pigors**
  - FIX: Add '/s/ Andrew James Pigors' as electronic signature for e-filing
- ❌ **EF-03: PDF format noted (recommended for MiFILE)**
  - WARN: Ensure documents are converted to PDF before uploading to MiFILE
- ✅ **EF-04: Descriptive file names with case number**
  - WARN: Consider adding case number to file names for MiFILE
- ✅ **EF-05: File size under 25 MB each**
  - WARN: Verify each PDF is under 25 MB (conservative: under 10 MB) before e-filing
- ✅ **EF-06: Scanned documents at 300 dpi B&W/grayscale**
  - WARN: If any scanned exhibits, ensure 300 dpi B&W or grayscale for legibility
- ✅ **EF-07: No password-protected or restricted PDFs**
  - WARN: Ensure no PDFs are password-protected before uploading to MiFILE

---

## PKG_F9_COA_BRIEF_ON_APPEAL — COA Brief on Appeal
**Filing Type:** F9 | **Court:** Court of Appeals
**Score:** 91/100 | **Verdict:** ✅ GO — Ready for filing (minor warnings may remain)

### ⚠️ Universal Formatting (14/17)

- ✅ **UF-01: Caption includes court name**
- ✅ **UF-02: Caption includes case number**
- ✅ **UF-03: Caption includes party names**
- ✅ **UF-04: Document title present**
- ✅ **UF-05: Signature block includes name**
- ✅ **UF-06: Signature block includes address**
- ✅ **UF-07: Signature block includes phone**
- ❌ **UF-08: Date present in signature block or filing**
  - FIX: Add date in signature block (e.g., 'Dated: Month DD, YYYY')
- ✅ **UF-09: Certificate of service present**
- ❌ **UF-10: Certificate of service includes date served**
  - FIX: Certificate of service must state date of service
- ✅ **UF-11: Certificate of service includes method of service**
- ✅ **UF-12: Certificate of service lists opposing party**
- ❌ **UF-13: No placeholder text remaining**
  - FIX: Remove 5 placeholder(s): [ANDREW_REQUIRED: Review and supplement with specific hearing dates,
motions filed, and orders entered from your court records], [ANDREW_REQUIRED: Review and supplement with specific hearing dates,
motions filed, and orders entered from your court records], ___________________, ______________________________, _________________
- ✅ **UF-14: Pages appear consecutively numbered**
- ✅ **UF-15: Pro se status identified**
- ✅ **UF-16: Electronic signature format (/s/ Name) present**
- ✅ **UF-17: Child referred to by initials only (MCR 8.119(H))**

### ✅ Anti-Hallucination Guard (8/8)

- ✅ **AH-01: No fabricated 'Jane Berry' (hallucination)**
- ✅ **AH-02: No fabricated 'Patricia Berry' (hallucination)**
- ✅ **AH-03: No wrong judge name 'Amy McNeill'**
- ✅ **AH-04: Ronald Berry not listed as attorney (he is not one)**
- ✅ **AH-05: Correct defendant name (Emily A. Watson, not Ann/M.)**
- ✅ **AH-06: No fabricated '91% alienation score'**
- ✅ **AH-07: No fabricated '9 CPS investigations'**
- ✅ **AH-08: No wrong name 'Tiffany' for defendant**

### ✅ Common Rejection Screening (5/5)

- ✅ **CR-01: Case number present**
- ✅ **CR-02: Document appears legible (no binary garbage)**
- ✅ **CR-03: All files have substantive content**
- ✅ **CR-04: No bundled unrelated documents**
  - WARN: Verify each file contains only ONE document type when converting to PDF
- ✅ **CR-05: Required signature(s) present**

### ✅ MiFILE E-Filing (7/7)

- ✅ **EF-01: Each document is a separate file (not bundled)**
- ✅ **EF-02: Electronic signature format: /s/ Andrew James Pigors**
- ✅ **EF-03: PDF format noted (recommended for MiFILE)**
- ✅ **EF-04: Descriptive file names with case number**
  - WARN: Consider adding case number to file names for MiFILE
- ✅ **EF-05: File size under 25 MB each**
  - WARN: Verify each PDF is under 25 MB (conservative: under 10 MB) before e-filing
- ✅ **EF-06: Scanned documents at 300 dpi B&W/grayscale**
  - WARN: If any scanned exhibits, ensure 300 dpi B&W or grayscale for legibility
- ✅ **EF-07: No password-protected or restricted PDFs**
  - WARN: Ensure no PDFs are password-protected before uploading to MiFILE
