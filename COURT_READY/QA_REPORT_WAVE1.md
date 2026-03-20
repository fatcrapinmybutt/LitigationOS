# RED TEAM QA REPORT — WAVE 1

## Date: March 19, 2026
## Auditor: Judicial-Grade QA Engine (Red Team)
## Packages Audited: F1, F2, F3, F8

---

## EXECUTIVE SUMMARY

| Severity | Count | Description |
|----------|-------|-------------|
| **🔴 CRITICAL** | **14** | Must fix before filing — rejection, sanctions, or credibility risk |
| **🟠 MAJOR** | **9** | Should fix — weakens the filing or creates inconsistency |
| **🟡 MINOR** | **7** | Cosmetic or style — fix if time permits |
| **TOTAL** | **30** | |

### TOP 5 MOST DANGEROUS FINDINGS

1. **C-01: L.D.W. gender pronoun error in F3** — The disqualification motion refers to L.D.W. as "her" when L.D.W. is male. This will destroy credibility with the court and suggests careless drafting.
2. **C-02: PPO petition date contradicts across F2 and F3** — F2 says December 3, 2023; F3 says October 15, 2023. A court that reads both filings will immediately notice this.
3. **C-03: F1 references documents not in the package** — The Certificate of Service lists a "Proposed Order" and "UCCJEA Affidavit (MC 416)" as served documents, but neither exists in the F1 package.
4. **C-06: Potential fabricated statistic** — "14 of 14 recognized indicators of parental alienation" in F1 motion sounds like a pseudo-scientific metric. There is no universally recognized 14-indicator scale. This mirrors the "91% alienation score" hallucination from prior sessions.
5. **C-08: F8 Exhibit Index has 9/12 exhibits unattached** — Filing this as-is means the court receives a motion citing exhibits that don't exist in the filing.

---

## F1 — EMERGENCY CUSTODY

### A. Party Identity: ✅ PASS (with 1 note)

| Check | Result | Detail |
|-------|--------|--------|
| Plaintiff name | ✅ | "Andrew James Pigors" — correct |
| Defendant name | ✅ | "Emily A. Watson" — correct |
| Child initials | ✅ | "L.D.W." — initials only per MCR 8.119(H) |
| Judge name | ✅ | "Hon. Jenny L. McNeill" — correct |
| Case number | ✅ | 2024-001507-DC — correct |
| Ronald Berry | ✅ | Described as "Defendant's boyfriend" — no bar number, no "Esq." |
| Address/contact | ✅ | All addresses and phone numbers match verified records |

**Note:** COS section "Service on Friend of the Court" with "Attn: Pamela Rusco" is acceptable — it's routing to the FOC office, not describing Rusco's role.

---

### B. Citations: ⚠️ FAIL — 3 issues

| ID | Severity | Citation | Issue |
|----|----------|----------|-------|
| **C-06** | 🔴 CRITICAL | "14 of 14 recognized indicators of parental alienation" (Motion §V.C) | **ANTI-HALLUCINATION FLAG.** No universally recognized "14 indicators" scale exists in peer-reviewed literature. This is a fabricated metric that mirrors the banned "91% alienation score." Remove entirely or replace with verifiable incident counts (e.g., "multiple documented indicators"). |
| **C-09** | 🔴 CRITICAL | "286 evidence items" (Motion §V.C) | **UNVERIFIED STATISTIC.** Where does 286 come from? If from litigation_context.db, cite the query. If not traceable, remove. Every stat in a sworn filing must be verifiable. |
| **C-10** | 🔴 CRITICAL | *Saul Parent v. Mousel*, COA No. 364910 (2023) | **POTENTIALLY FABRICATED CITATION.** "Saul Parent" is an unusual party name. This case is cited twice (§III.B and §V.A) as recognizing parental alienation harm. If this case doesn't exist, citing it is sanctionable under MCR 2.114(D). **MUST verify this case exists in Michigan COA records before filing.** |
| **M-01** | 🟠 MAJOR | "24 of 55 orders (44%) were entered ex parte" (Motion ¶22) | Specific stat needs DB verification. If accurate, powerful. If wrong, devastating to credibility. Run `SELECT COUNT(*) FROM docket_events WHERE ex_parte = 1` or equivalent. |
| **M-02** | 🟠 MAJOR | Bowlby (1969); Wallerstein (2000) | Academic citations in a motion are unusual in Michigan circuit court. Not improper, but the court may give them little weight. Consider whether they add value or clutter. |

**All other citations verified as properly formatted:** MCR 3.207(B)(C), MCL 722.27, MCL 722.27a(1)(3)(7), MCL 722.23, MCL 600.605, MCL 722.26, MCL 722.1201, MCR 8.119(H), MCR 2.114(A), MCL 750.423, MCL 750.424, *Vodvarka v. Grasmeyer* 259 Mich App 499 (2003), *Troxel v. Granville* 530 U.S. 57 (2000), *Meyer v. Nebraska* 262 U.S. 390 (1923), *Santosky v. Kramer* 455 U.S. 745 (1982), *Stanley v. Illinois* 405 U.S. 645 (1972), *Mathews v. Eldridge* 424 U.S. 319 (1976), *Hunter v. Hunter* 484 Mich 247 (2009). All MRE citations in Exhibit Index are properly formatted.

---

### C. Formatting: ⚠️ FAIL — 2 issues

| ID | Severity | Issue |
|----|----------|-------|
| **C-04** | 🔴 CRITICAL | **Emoji in filing title.** Line 30: "⚠️ EMERGENCY ⚠️" — Emoji characters are **never** appropriate in a court filing. Remove immediately. Use "EMERGENCY" in all caps if emphasis is needed. A judge seeing emoji will question the seriousness of the filer. |
| **C-11** | 🔴 CRITICAL | **No Table of Contents.** The Emergency Motion is 20+ pages. MCR 2.119(A)(2) requires a table of contents for briefs exceeding 5 pages. While motions have slightly different rules, a TOC is expected and its absence looks amateurish for a document this length. F2 and F3 both have TOCs. |
| **m-01** | 🟡 MINOR | Page numbers not present (markdown limitation — would be added in final PDF formatting). |

**Formatting passes:** Caption format (MCR 2.113), numbered paragraphs in affidavit, verification/jurat language, notarization block, signature blocks, MCR 2.107 COS compliance.

---

### D. Completeness: ⚠️ FAIL — 2 critical gaps

| ID | Severity | Issue |
|----|----------|-------|
| **C-03** | 🔴 CRITICAL | **Missing documents referenced in COS.** The Certificate of Service lists 5 documents served: (1) Emergency Motion ✅, (2) Affidavit ✅, (3) Exhibit Index ✅, (4) **Proposed Order** ❌ NOT IN PACKAGE, (5) **UCCJEA Affidavit (MC 416)** ❌ NOT IN PACKAGE. Filing a COS that certifies service of non-existent documents is a MCR 2.114(D) violation. Either create these documents or remove them from the COS. |
| **M-03** | 🟠 MAJOR | **Exhibit page counts blank.** Every exhibit in the index shows "____" for page count. Must be filled before filing. |

**Prayer for relief:** 10 specific numbered items ✅. All counts have elements stated, facts applied, relief requested ✅.

---

### E. Anti-Hallucination: ⚠️ FAIL — 2 issues

| ID | Severity | Issue |
|----|----------|-------|
| **C-06** | 🔴 CRITICAL | "14 of 14 recognized indicators of parental alienation" — No standard 14-indicator scale exists. This is pseudo-scientific fabrication. **REMOVE.** |
| **C-09** | 🔴 CRITICAL | "286 evidence items relevant to Factor (j)" — Untraced DB statistic. If not from a verified query, this is fabrication in a sworn filing. |
| **M-01** | 🟠 MAJOR | "24 of 55 orders (44%)" — Verify against docket. |

**Passes:** 223-day count is mathematically correct (Aug 8, 2025 → Mar 19, 2026). 438 consecutive days (May 5, 2024 → Jul 17, 2025) is correct. "Seven law enforcement investigations" — needs verification but is presented as fact from personal knowledge. Party names match verified list. No fabricated party names detected.

---

### F. Cross-References: ⚠️ FAIL — 1 issue

| ID | Severity | Issue |
|----|----------|-------|
| **M-07** | 🟠 MAJOR | **No mention of pending F3 disqualification motion.** If the disqualification motion is being filed simultaneously, the Emergency Motion should reference it. A judge reading F1 without knowing F3 exists may react differently than one who knows disqualification is pending. Strategic cross-reference improves both filings. |

**Passes:** Exhibit letters A-L match between motion and exhibit index ✅. Case number consistent ✅. Dates internally consistent within F1 ✅.

---

### F1 OVERALL: 🔴 NO-GO

**Blocking issues:** Emoji in title (C-04), missing Proposed Order and UCCJEA (C-03), fabricated alienation metric (C-06), unverified stat (C-09), potentially fabricated case citation (C-10), no TOC (C-11).

---

---

## F2 — PPO TERMINATION

### A. Party Identity: ✅ PASS

| Check | Result | Detail |
|-------|--------|--------|
| Petitioner/Respondent | ✅ | Correctly reversed for PPO case — Watson is Petitioner, Pigors is Respondent |
| Case number | ✅ | 2023-5907-PP — correct for PPO |
| Judge name | ✅ | "Hon. Jenny L. McNeill" — correct |
| Jennifer Barnes | ✅ | "P55406" correct, described as withdrew ✅ |
| Ronald Berry | ✅ | No bar number, described as "domestic partner" / "boyfriend" |
| L.D.W. | ✅ | Initials only throughout |

---

### B. Citations: ⚠️ FAIL — 2 issues

| ID | Severity | Issue |
|----|----------|-------|
| **M-04** | 🟠 MAJOR | **"Fruit of the Poisonous Tree" doctrine misapplied** (Motion ¶23). This is a *criminal law exclusionary rule* doctrine (*Wong Sun v. United States*, 371 U.S. 471 (1963)) that applies to evidence obtained through unconstitutional searches. It does NOT apply to fraudulently obtained civil court orders. The motion already correctly cites MCR 2.612(C)(1)(c) for fraud on the court — the FPT reference is legally wrong and will undermine credibility. **Remove the FPT reference.** |
| **M-05** | 🟠 MAJOR | **Inconsistent SCOTUS citation format.** F2 uses "US" without periods (e.g., "530 US 57") while F1 and F3 use "U.S." with periods (e.g., "530 U.S. 57"). Standard Bluebook/Michigan citation format requires "U.S." The inconsistency across simultaneously-filed packages looks careless. Affected citations: *Troxel* (¶24), *Stanley* (¶24), *Santosky* (¶24), *Mathews* (¶24, ¶46a), *In re Contempt of Henry* (¶44). |

**All other citations verified:** MCL 600.2950(12), MCR 3.707(A)(B), MCL 600.2950a, MCR 2.612(C)(1)(c), MCR 2.114(E), MCR 1.109(E), MCR 3.706, MCR 3.708, MCL 722.27, MCL 722.23, MCL 722.27a. *Hayford v. Hayford* 279 Mich App 324 (2008), *Pickering v. Pickering* 253 Mich App 694 (2002), *Kampf v. Kampf* 237 Mich App 377 (1999), *Hunter v. Hunter* 484 Mich 247 (2009), *Friedman v. Dozorc* 412 Mich 1 (1981) — all properly formatted.

---

### C. Formatting: ✅ PASS (with 1 note)

| Check | Result |
|-------|--------|
| Table of Contents | ✅ Present |
| Caption format | ✅ Correct for PPO case |
| Verification | ✅ MCR 2.114(A) |
| Certificate of Service | ✅ MCR 2.107(C) |
| Signature blocks | ✅ Present |

**Note:** Caption uses code-block formatting while F1 uses markdown. Inconsistent style across packages (minor — see m-02 below).

---

### D. Completeness: ⚠️ FAIL — 1 critical issue

| ID | Severity | Issue |
|----|----------|-------|
| **C-12** | 🔴 CRITICAL | **Internal preparation checklist in Exhibit Index.** Lines 62-79 of EXHIBIT_INDEX.md contain an "EXHIBIT PREPARATION CHECKLIST" with action items like "Request certified copies," "Verify in possession," "Compile from docket entries," etc. **This MUST be removed before filing.** Filing internal preparation notes reveals: (a) which exhibits you don't yet have, (b) your litigation strategy, and (c) your organizational weaknesses. Opposing counsel will use this against you. |

**Passes:** All 4 documents present. Motion comprehensive with IRAC blocks. Affidavit detailed and well-structured. 19 exhibits (A-S) — very thorough. Prayer for relief with specific items. Verification present.

---

### E. Anti-Hallucination: ✅ PASS

No fabricated statistics, no invented party names, no pseudo-scientific metrics detected. All claims are presented as facts from personal knowledge or documented records. "Six or more show-cause motions" uses appropriately hedged language.

**One verification flag:** Exhibit S cites "Lori Watson Text Message (March 26, 2023)" with a direct quote. March 2023 is early in the timeline (L.D.W. was ~4 months old). Verify this date is accurate.

---

### F. Cross-References: ⚠️ FAIL — 2 issues

| ID | Severity | Issue |
|----|----------|-------|
| **C-02** | 🔴 CRITICAL | **PPO filing date contradicts F3.** F2 Affidavit ¶4: "On or about December 3, 2023, Petitioner Emily A. Watson filed a petition." F3 Affidavit ¶4: "On October 15, 2023, a petition for a PPO was filed." F3 Motion ¶9: "On October 15, 2023." F2 Exhibit Index: "Original PPO Petition (December 3, 2023)." **These dates are 49 days apart. A court reviewing both filings will catch this immediately.** One of these dates is wrong. Verify against the actual docket and correct ALL references across ALL packages. |
| **C-05** | 🔴 CRITICAL | **HealthWest evaluation date inconsistency.** F2 says "September 5, 2025" (Affidavit ¶19.d and Motion ¶17.b). F1 says "September 4, 2025" (Affidavit ¶17 and Motion ¶14). F3 says "September 4, 2025" (Affidavit ¶13 and Motion ¶22). The evaluation happened on ONE date. Verify and make consistent across ALL packages. |

---

### F2 OVERALL: 🔴 NO-GO

**Blocking issues:** PPO date contradiction (C-02), HealthWest date inconsistency (C-05), internal prep notes in exhibit index (C-12), misapplied FPT doctrine (M-04).

---

---

## F3 — DISQUALIFICATION

### A. Party Identity: ❌ FAIL — 1 critical error

| ID | Severity | Issue |
|----|----------|-------|
| **C-01** | 🔴 CRITICAL | **Gender pronoun error for L.D.W.** Motion ¶3: "L.D.W. missed **her** third birthday (November 9, 2025), Thanksgiving, Christmas, and every holiday with **her** father." L.D.W. is MALE. Every other filing uses "his son," "he," etc. This error in the disqualification motion — the most consequential filing in the package — will: (a) undermine credibility, (b) suggest careless drafting, (c) give the judge grounds to question the reliability of ALL claims in the motion. **FIX IMMEDIATELY: Change "her" to "his" in both instances.** |

**Passes:** All other party identifications correct. Andrew James Pigors ✅. Emily A. Watson ✅. Hon. Jenny L. McNeill ✅. Case numbers correct (2024-001507-DC consolidated with 2023-5907-PP) ✅. Pamela Rusco correctly identified as "Judge McNeill's judicial secretary" ✅. Mandi Martini identified as court-appointed attorney ✅. Jennifer Barnes (P55406) ✅. Chief Judge Kenneth Hoopes and Judge Maria Ladas Hoopes named in structural conflict section ✅.

---

### B. Citations: ✅ PASS — Strong

F3 has the strongest citation work of all four packages. Every case is properly formatted with Michigan-style parallel citations where applicable:

- *Caperton v A.T. Massey Coal Co.*, 556 U.S. 868, 884 (2009) ✅
- *Cain v Department of Corrections*, 451 Mich. 470, 497; 548 N.W.2d 210 (1996) ✅
- *Liteky v United States*, 510 U.S. 540, 555 (1994) ✅
- *Crampton v Department of State*, 395 Mich. 347; 235 N.W.2d 352 (1975) ✅
- *In re Contempt of Henry*, 282 Mich. App. 656, 671; 766 N.W.2d 44 (2009) ✅
- *Armstrong v Ypsilanti Charter Twp*, 248 Mich. App. 573, 597 (2001) ✅
- *Boddie v Connecticut*, 401 U.S. 371, 383 (1971) ✅
- *In re Contempt of Dougherty*, 429 Mich. 81, 95 (1987) ✅
- *In re MKK*, 286 Mich. App. 546 (2009) ✅
- *People v Jackson*, 292 Mich. App. 583, 597 (2011) ✅
- Canon 2, Canon 3(A)(4), Canon 3(B)(7) — Michigan Code of Judicial Conduct ✅
- MCR 2.003(C)(1)(a)(b), (D)(1)(2)(3) ✅
- Michigan Ethics Opinion JI-134 — **Flag:** Verify this opinion number exists. Format is plausible.
- *In re Disqualification of Noe*, 454 Mich. 1201 (1997) — **Flag:** Page 1201 suggests a table order/register entry, not a full opinion. Verify this provides the holding attributed to it.

---

### C. Formatting: ✅ PASS

| Check | Result |
|-------|--------|
| Table of Contents | ✅ Present and detailed |
| Caption format | ✅ MCR 2.113 compliant |
| Verification | ✅ MCR 2.114(A) and MCR 2.003(D)(1) |
| Certificate of Service | ✅ Embedded at end of motion |
| Affidavit with Jurat | ✅ Proper notarization block |
| Proposed Order | ✅ Based on MC 264 form |
| Pilcrow (¶) paragraph marks | ✅ Consistently used |

**Note:** HTML comment on line 1 (`<!-- Format: Times New Roman 12pt... -->`) must be removed from final filing — it's a formatting instruction, not part of the document.

---

### D. Completeness: ✅ PASS

All three required documents present: Motion, Affidavit of Bias, Proposed Order. Exhibit index embedded in affidavit with 13 exhibits (A-M), each mapped to specific affidavit paragraphs. Prayer for relief with 7 specific items including alternative relief. Timeliness argument addressed (§VI). Structural conflict argument included (§VII — strong strategic addition).

---

### E. Anti-Hallucination: ✅ PASS (except C-01)

No fabricated statistics. No invented party names. No pseudo-scientific metrics. All events described are consistent with the factual narrative across packages. The gender pronoun error (C-01) is a transcription error, not a fabrication.

---

### F. Cross-References: ⚠️ FAIL — 1 issue

| ID | Severity | Issue |
|----|----------|-------|
| **C-02** | 🔴 CRITICAL | **PPO petition date conflicts with F2.** F3 says October 15, 2023 (petition filed) and November 1, 2023 (PPO issued). F2 says December 3, 2023 (filed AND issued same day). These are materially different — one describes a petition-then-hearing process, the other describes same-day ex parte issuance. Both cannot be correct. |

**Passes:** Exhibit letters match affidavit paragraph references ✅. Both case numbers referenced ✅. Internal dates consistent within F3 ✅.

---

### F3 OVERALL: 🔴 NO-GO

**Blocking issues:** Gender pronoun error (C-01), PPO date contradiction (C-02). F3 is otherwise the strongest package — once these two issues are fixed, it's close to filing-ready.

---

---

## F8 — CONTEMPT ENFORCEMENT

### A. Party Identity: ⚠️ FAIL — 1 issue

| ID | Severity | Issue |
|----|----------|-------|
| **M-06** | 🟠 MAJOR | **Incomplete identification of "Lori."** Affidavit ¶17: "Lori (facilitation): A member of the Watson/Berry household network who facilitated the coordination of interference activities." This is unacceptable in a sworn affidavit. "Lori" is not a legal identification. Must be "Lori Watson (Defendant's mother)" — as correctly identified in F1 Motion ¶19 and F1 Affidavit ¶25c. |

**Passes:** All other party IDs correct. Andrew James Pigors ✅. Emily A. Watson ✅. Hon. Jenny L. McNeill ✅. Case No. 2024-001507-DC ✅. Ronald Berry as "domestic partner" with no bar number ✅. Jennifer Barnes (P55406) as withdrew ✅. L.D.W. initials only ✅.

---

### B. Citations: ✅ PASS — Solid

| Citation | Format | Verified |
|----------|--------|----------|
| MCL 600.1701(c) | ✅ | Contempt authority |
| MCL 552.644 | ✅ | Parenting time enforcement remedies |
| MCL 722.27a(7) | ✅ | Makeup parenting time |
| MCR 3.606 | ✅ | Show cause procedure |
| *Porter v. Porter*, 285 Mich App 450 (2009) | ✅ | Four-element contempt test |
| *Bowie v. Arder*, 441 Mich 23, 40 (1992) | ✅ | Inherent contempt power |
| MCL 552.601 *et seq.* | ✅ | Support and Parenting Time Enforcement Act |
| MCL 552.645 | ✅ | Good cause definition |
| *Shade v. Wright*, 291 Mich App 17, 31 (2010) | ✅ | Factor (j) analysis |
| MCL 722.23(j) | ✅ | Best interest factor |

All statutory and rule citations properly formatted. Case citations appear legitimate.

---

### C. Formatting: ✅ PASS (with 1 note)

| Check | Result |
|-------|--------|
| Caption | ✅ Correct |
| IRAC blocks | ✅ 5 well-structured IRAC analyses |
| Verification | ✅ MCR 2.114(A) |
| Certificate of Service | ✅ Both embedded (motion) and separate file |
| Oral Argument Request | ✅ Noted in title |
| Signature blocks | ✅ Present |

**Note:** Motion lacks a Table of Contents despite being 20+ pages. F2 and F3 both have TOCs. Add one for consistency.

---

### D. Completeness: ❌ FAIL — 2 critical issues

| ID | Severity | Issue |
|----|----------|-------|
| **C-08** | 🔴 CRITICAL | **9 of 12 exhibits not attached.** The Exhibit Index shows placeholder markers for 9 exhibits: A "[ATTACH — obtain certified copy from Clerk]", B "[ATTACH]", D "[COMPILE — extract from AppClose records]", E "[ATTACH — transcribe recording if available]", F "[ATTACH — compile screenshots]", H "[ATTACH — obtain certified copy via FOIA]", I "[COMPILE — parenting time log]", J "[ATTACH — obtain from Clerk]", K "[ATTACH — obtain from Clerk]". Only C, G, and L are marked "Attached." **A motion filed with 9 of 12 exhibits missing will be stricken.** |
| **C-13** | 🔴 CRITICAL | **Internal preparation notes in Exhibit Index.** Lines 84-96 contain "EXHIBIT PREPARATION NOTES" with an action table showing what Plaintiff still needs to obtain. Same issue as F2 — **remove before filing.** |
| **M-08** | 🟠 MAJOR | **No Proposed Order.** Contempt motions typically require a proposed order for the court's convenience. F3 includes one; F8 does not. The Exhibit Index references "Exhibit L: Proposed Order" as "Attached" but no separate Proposed Order document exists in the package. |

---

### E. Anti-Hallucination: ⚠️ FAIL — 1 issue

| ID | Severity | Issue |
|----|----------|-------|
| **M-09** | 🟠 MAJOR | **Unverifiable superlative claim.** Motion ¶1: "one of the most severe and sustained patterns of parenting time denial in the history of this Court." This is an unprovable claim about the court's entire history. The judge will know her own docket better than Plaintiff. This reads as hyperbole and could irritate the court. **Replace with:** "a severe and sustained pattern of parenting time denial" — equally strong, but doesn't make an unverifiable historical claim. |

**Passes:** 44 AppClose violations — presented as documented from personal records ✅. 223-day count ✅. 438-day count ✅. 59 days incarceration ✅. All party names match verified list ✅. No fabricated bar numbers or case statistics ✅.

---

### F. Cross-References: ⚠️ FAIL — 1 issue

| ID | Severity | Issue |
|----|----------|-------|
| **C-14** | 🔴 CRITICAL | **No mention of pending disqualification motion.** If F3 (disqualification) is pending when F8 is filed, the contempt motion should note this. It's strategically important: the court needs to know that Plaintiff is simultaneously challenging the judge's impartiality while asking that same judge to hold Defendant in contempt. Failure to disclose this creates an appearance of gamesmanship. |

**Passes:** Case number consistent (2024-001507-DC) ✅. Exhibits A-L match motion references ✅. Dates internally consistent ✅. Both motion and affidavit COS list same documents ✅.

---

### F8 OVERALL: 🔴 NO-GO

**Blocking issues:** 9/12 exhibits unattached (C-08), internal prep notes exposed (C-13), no mention of pending disqualification (C-14).

---

---

## CROSS-PACKAGE ISSUES

### X-01: PPO Petition Date Discrepancy (🔴 CRITICAL)

| Package | Document | Date Given | What Happened |
|---------|----------|------------|---------------|
| F2 | Motion ¶8 | December 3, 2023 | "filed a petition... PPO was issued the same day" |
| F2 | Affidavit ¶4 | December 3, 2023 | "On or about December 3, 2023" |
| F2 | Exhibit Index, Ex. A | December 3, 2023 | "Original PPO Petition (December 3, 2023)" |
| F3 | Affidavit ¶4 | October 15, 2023 | "On October 15, 2023, a petition for a PPO was filed" |
| F3 | Affidavit ¶5 | November 1, 2023 | "On November 1, 2023, the Court issued a PPO" |
| F3 | Motion ¶9 | October 15, 2023 | "On October 15, 2023, a petition for a PPO was filed" |
| F3 | Motion ¶10 | November 1, 2023 | "the Court issued a PPO (domestic)" |

**These timelines are irreconcilable.** F2 describes same-day filing and issuance on December 3. F3 describes an October 15 petition followed by November 1 issuance. The actual docket will show ONE correct sequence. **Check the court docket and correct ALL references in ALL packages.**

### X-02: HealthWest Evaluation Date (🔴 CRITICAL)

| Package | Document | Date |
|---------|----------|------|
| F1 | Motion ¶14 | September 4, 2025 |
| F1 | Affidavit ¶17 | September 4, 2025 |
| F2 | Motion ¶17.b | September 5, 2025 |
| F2 | Affidavit ¶19.d | September 5, 2025 |
| F2 | Exhibit Index, Ex. L | September 5, 2025 |
| F3 | Motion ¶22 | September 4, 2025 |
| F3 | Affidavit ¶13 | September 4, 2025 |

**F2 says September 5; all others say September 4.** Check the actual HealthWest report and standardize.

### X-03: No Strategic Cross-References (🟠 MAJOR)

None of the four packages reference the other pending motions. If filed simultaneously or near-simultaneously, each should acknowledge the others:

- **F1 (Emergency Custody)** should mention: "Plaintiff has concurrently filed a Motion for Disqualification (F3) based on the documented pattern of judicial bias, and a Motion for Contempt (F8) addressing Defendant's willful violations."
- **F3 (Disqualification)** should mention: "The emergency custody motion and contempt enforcement motion filed concurrently demonstrate the urgency of reassignment."
- **F8 (Contempt)** should mention: "Plaintiff notes that a Motion for Disqualification is pending; however, this contempt motion is filed to preserve Plaintiff's rights regardless of the disqualification outcome."
- **F2 (PPO Termination)** should reference F1 and F3 as related proceedings.

### X-04: Caption Format Inconsistency (🟡 MINOR)

| Package | Caption Style |
|---------|--------------|
| F1 | Markdown headers with &nbsp; spacing |
| F2 | Code block (``` ```) |
| F3 | Plain text with HTML formatting comment |
| F8 | Code block (``` ```) |

All four packages should use consistent formatting. Since these will ultimately be converted to PDF/DOCX with Times New Roman 12pt, the markdown format matters less, but consistency shows attention to detail.

### X-05: "44 AppClose Violations" Claim (🟠 MAJOR)

This stat appears in F1 (Motion §V.C) and F8 (Motion ¶13d, Affidavit ¶11). It's a specific count that must be verifiable. If Andrew has documented these 44 violations with dates and descriptions, the claim is solid. If the number was generated by a database query, verify the query. An opposing attorney WILL demand specifics.

### X-06: Filing Strategy Concern (🟡 ADVISORY)

Filing F8 (Contempt against Emily) and F3 (Disqualification of Judge McNeill) simultaneously creates a tension: you're asking Judge McNeill to hold Emily in contempt while simultaneously saying McNeill is biased. If F3 is filed first and pending, McNeill may decline to act on F8 until the disqualification is resolved — meaning MORE delay. **Consider filing order:**
1. F3 (Disqualification) — file FIRST
2. Wait for ruling or reassignment
3. Then file F1, F2, F8 before the new judge

Alternatively, file F1 (Emergency) first as it has the most time-sensitive relief request, then F3.

---

## COMPLETE ISSUE REGISTER

| ID | Severity | Package | Issue | Action Required |
|----|----------|---------|-------|----------------|
| C-01 | 🔴 CRITICAL | F3 | L.D.W. "her" → "his" gender pronoun error | Change "her" to "his" in ¶3 (two instances) |
| C-02 | 🔴 CRITICAL | F2/F3 | PPO petition date: Dec 3 vs Oct 15 | Verify docket; correct all references |
| C-03 | 🔴 CRITICAL | F1 | COS lists Proposed Order + UCCJEA not in package | Create documents or remove from COS |
| C-04 | 🔴 CRITICAL | F1 | Emoji "⚠️" in filing title | Remove emoji, use caps "EMERGENCY" only |
| C-05 | 🔴 CRITICAL | F1/F2/F3 | HealthWest date: Sept 4 vs Sept 5 | Verify report; standardize all refs |
| C-06 | 🔴 CRITICAL | F1 | "14 of 14 indicators" — fabricated metric | Remove or replace with verifiable counts |
| C-08 | 🔴 CRITICAL | F8 | 9 of 12 exhibits not attached | Obtain and attach before filing |
| C-09 | 🔴 CRITICAL | F1 | "286 evidence items" — untraced stat | Verify via DB query or remove |
| C-10 | 🔴 CRITICAL | F1 | *Saul Parent v. Mousel* — verify exists | Search Michigan COA records |
| C-11 | 🔴 CRITICAL | F1 | No Table of Contents (20+ page motion) | Add TOC |
| C-12 | 🔴 CRITICAL | F2 | Internal prep checklist in Exhibit Index | Remove before filing |
| C-13 | 🔴 CRITICAL | F8 | Internal prep notes in Exhibit Index | Remove before filing |
| C-14 | 🔴 CRITICAL | F8 | No mention of pending disqualification | Add cross-reference |
| M-01 | 🟠 MAJOR | F1 | "24 of 55 orders (44%)" — verify stat | Run docket query |
| M-02 | 🟠 MAJOR | F1 | Academic citations may lack judicial weight | Consider removing or footnoting |
| M-03 | 🟠 MAJOR | F1 | Exhibit page counts blank ("____") | Fill before filing |
| M-04 | 🟠 MAJOR | F2 | "Fruit of Poisonous Tree" misapplied | Remove FPT reference |
| M-05 | 🟠 MAJOR | F2 | "US" vs "U.S." citation inconsistency | Standardize to "U.S." throughout |
| M-06 | 🟠 MAJOR | F8 | "Lori (facilitation)" — incomplete ID | Change to "Lori Watson (Defendant's mother)" |
| M-07 | 🟠 MAJOR | F1 | No cross-reference to F3 disqualification | Add strategic cross-reference |
| M-08 | 🟠 MAJOR | F8 | No Proposed Order document | Create proposed contempt order |
| M-09 | 🟠 MAJOR | F8 | "most severe... in history of this Court" | Remove unverifiable superlative |
| m-01 | 🟡 MINOR | ALL | Page numbers missing (markdown) | Add in final PDF conversion |
| m-02 | 🟡 MINOR | ALL | Caption formatting inconsistent | Standardize across packages |
| m-03 | 🟡 MINOR | F3 | HTML comment on line 1 | Remove before filing |
| m-04 | 🟡 MINOR | F1 | Affidavit uses markdown numbered lists (1\.) | Consistent but unusual |
| m-05 | 🟡 MINOR | F2 | COS doesn't serve FOC | Verify if PPO service requires FOC |
| m-06 | 🟡 MINOR | F8 | No Table of Contents (20+ pages) | Add for consistency |
| m-07 | 🟡 MINOR | F2 | Exhibit S date (March 26, 2023) — early | Verify Lori Watson text date |

---

## RECOMMENDED FIX PRIORITY

### Wave 1 — Fix TONIGHT (blocks filing)
1. ✏️ C-01: Fix "her" → "his" in F3 Motion ¶3
2. 🔍 C-02: Verify PPO date against docket → fix all references
3. 🔍 C-05: Verify HealthWest date → fix all references
4. ✏️ C-04: Remove emoji from F1 title
5. ✏️ C-06: Remove "14 of 14 indicators" from F1
6. 🔍 C-09: Verify "286 evidence items" or remove
7. 🔍 C-10: Verify *Saul Parent v. Mousel* exists
8. ✏️ C-12/C-13: Remove prep checklists from F2 and F8 Exhibit Indexes
9. ✏️ M-04: Remove "Fruit of Poisonous Tree" reference from F2

### Wave 2 — Fix BEFORE filing
10. 📝 C-03: Create Proposed Order and UCCJEA for F1, or update COS
11. 📝 C-08: Obtain and attach F8 exhibits
12. 📝 C-11: Add TOC to F1 Emergency Motion
13. ✏️ C-14: Add cross-references between packages
14. ✏️ M-05: Standardize "U.S." across F2
15. ✏️ M-06: Fix "Lori" → "Lori Watson" in F8

### Wave 3 — Polish
16. All minor formatting items (m-01 through m-07)

---

## VERDICT

| Package | Status | Fixes Needed |
|---------|--------|-------------|
| **F1 Emergency Custody** | 🔴 **NO-GO** | 8 critical fixes required |
| **F2 PPO Termination** | 🔴 **NO-GO** | 4 critical fixes required |
| **F3 Disqualification** | 🔴 **NO-GO** | 2 critical fixes (closest to ready) |
| **F8 Contempt** | 🔴 **NO-GO** | 4 critical fixes required |

**F3 is closest to filing-ready** — only needs the pronoun fix and PPO date reconciliation. The substantive legal work in F3 is excellent.

**F1 needs the most work** — fabricated metrics, missing documents, and unverified citations create the most risk.

---

*Report generated by Red Team QA Engine. Every issue flagged is a potential rejection point, sanction risk, or credibility loss. Fix the criticals. File nothing until the NO-GO items are resolved.*
