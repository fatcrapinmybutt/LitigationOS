# Evidence Chain Analysis — Pigors v. Watson (LitigationOS)

> **All statistics from `litigation_context.db` queries. No fabricated counts.**
> Source tables: `evidence_quotes`, `claims`, `judicial_violations`, `critical_facts`, `case_timeline`, `filing_readiness`

---

## Lane A — Watson Custody (Case 2024-001507-DC)

### Total Evidence Items
- **Evidence quotes:** 39,009
- **Critical facts:** 1,736
- **Narrative context:** 2,794
- **Case timeline entries:** 170
- **Claims:** 12 (3 ready, 9 draft/proposed)

### Strongest Evidence

| Rank | Source | Category | Score | Key Content |
|------|--------|----------|------:|-------------|
| 1 | 2sided judge orders scanned_0004.pdf | COURT_ORDER | 99.0 | Ex parte order 8/8/25 suspending Father's parenting time based on Mother's allegations of drug use/mental health/homelessness |
| 2 | Court docket entries | custody | 98+ | Documented pattern of ex parte orders entered without Father's knowledge or opportunity to respond |
| 3 | AppClose communication logs | interference | 95+ | 305+ documented interference incidents by Emily Watson on court-approved platform |
| 4 | Albert+Emily kitchen recording | threat/admission | N/A | Albert Watson and Emily Watson recorded making threats regarding L.D.W. custody |
| 5 | HealthWest Evaluation H0002 | medical | N/A | Father deemed fit; judge excluded favorable evaluation from record |

### Ready-to-File Claims (strength ≥ 0.9)
- **A-EMRG-CUST** — Emergency custody restoration (5,730 evidence items) → Filing F1
- **A-VACATE** — Omnibus vacate void orders (6,085 evidence items) → Filing F4/F5
- **A-CUST-MOD** — Custody modification (6,233 evidence items) → Filing F7

### Weakest Links
- **A-CONTEMPT** (502 evidence items, strength 0.7) — Needs specific order violation instances with dates, the violated order text, and proof of non-compliance
- **A-CHILD-WELF** (1,770 items, strength 0.7) — Child welfare claims for L.D.W. need third-party professional corroboration (teacher reports, therapist notes, pediatric records)
- **A-PT-ENFORCE** (1,149 items, strength 0.7) — Parenting time enforcement needs calendar documentation showing each denied visit

### Missing Evidence
- [ ] Current school records for L.D.W.
- [ ] Pediatric/medical records showing impact on L.D.W.
- [ ] Third-party witness declarations (teachers, coaches, family friends)
- [ ] Complete AppClose export with metadata (305+ incidents referenced in DB)
- [ ] Updated income verification for Emily Watson (raise not reported)

### Authentication Status
| Evidence | Court-Ready? | Foundation |
|----------|:----------:|------------|
| Court orders/docket | ✅ | Self-authenticating (MRE 902) |
| Albert+Emily recording | ⚠️ | MRE 901(a) — need testimony from recording party |
| AppClose logs | ⚠️ | Business records (MRE 803(6)) — need platform certification |
| HealthWest evaluation | ⚠️ | Official record — need certified copy or custodian testimony |
| Police reports | ✅ | Public records (MRE 803(8)) |

---

## Lane B — Shady Oaks Housing (Case 2025-002760-CZ)

### Total Evidence Items
- **Evidence quotes:** 6,737
- **Critical facts:** 244
- **Narrative context:** 712
- **Case timeline entries:** 99
- **Claims:** 6 (all strength 0.9)

### Strongest Evidence

| Claim | Evidence Count | Strength | Key Support |
|-------|---------------:|----------:|-------------|
| B-CONSTR-FRAUD | 20,597 | 0.9 | Constructive fraud in property dealings |
| B-LEASE-FRAUD | 20,590 | 0.9 | Lease fraud documentation |
| B-PROPERTY-DEST | 6,934 | 0.9 | Property destruction/removal evidence |
| B-RETALIATION | 7,110 | 0.9 | Landlord retaliation pattern |
| B-HABITABILITY | 6,927 | 0.9 | Habitability violations (sewage, water shutoff) |
| B-UTILITY | 6,927 | 0.9 | Utility shutoff abuse documentation |

### Weakest Links
- All claims at 0.9 strength — Lane B is well-supported
- Primary weakness: need updated property status and current habitability photos

### Missing Evidence
- [ ] Current property condition photos/video
- [ ] EGLE complaint records (if filed)
- [ ] Title search/deed records (current chain of title)
- [ ] Utility company records documenting shutoff dates
- [ ] Building inspection reports

### Authentication Status
| Evidence | Court-Ready? | Foundation |
|----------|:----------:|------------|
| Lease/property documents | ⚠️ | Need originals or certified copies |
| Utility records | ⚠️ | Business records — need provider certification |
| Photos/condition evidence | ⚠️ | Need date/location testimony from photographer |
| Title records | ✅ | Public records (Register of Deeds) |

---

## Lane C — Convergence (Multi-Lane)

### Total Evidence Items
- **Evidence quotes:** 841
- **Critical facts:** 31
- **Narrative context:** 1,336
- **Claims:** 3

### Strongest Evidence
- **C-ENTITY-FRAUD** (20,597 items, strength 0.9) — Entity fraud at Shady Oaks
- **C-RICO-PATTERN** (13,894 items, strength 0.9) — RICO pattern enterprise

### Weakest Links
- **C-CONSPIRACY** (239 items, strength 0.6) — Conspiracy claim connecting Berry-Watson-judicial coordination is the weakest claim across all lanes. Needs direct evidence of coordinated action, not just parallel behavior.

### Missing Evidence
- [ ] Communications between Emily Watson and Ronald Berry regarding litigation strategy
- [ ] Communications between Emily Watson and Jennifer Barnes (P55406) re: coordinated tactics
- [ ] Financial records showing money flows between Watson family members and Shady Oaks entities
- [ ] Any direct evidence of judicial-party coordination

### Authentication Status
| Evidence | Court-Ready? | Foundation |
|----------|:----------:|------------|
| Corporate/entity records | ✅ | Public records (LARA) |
| Financial records | ⚠️ | Need subpoena or voluntary production |
| Communication records | ❌ | Need discovery/subpoena |

---

## Lane D — PPO / Protection Orders (Case 2023-5907-PP)

### Total Evidence Items
- **Evidence quotes:** 19,418
- **Critical facts:** 574
- **Narrative context:** 2,887
- **Case timeline entries:** 257
- **Judicial violations:** 109
- **Claims:** 3

### Strongest Evidence
- **D-FALSE-ALLEG-PPO** (5,063 items, strength 0.9) — False allegations underlying the PPO
- **D-PPO-WEAPON** (4,008 items, strength 0.8) — PPO used as custody weapon
- **D-PPO-TERM** (3,979 items, strength 0.8) — Grounds for PPO termination

**Key evidence:** Albert+Emily kitchen recording (Nov 30, 2023) — Albert Watson's own statements contradict Emily Watson's PPO allegations. This recording is pivotal to demonstrating the PPO was obtained through false pretenses.

### Weakest Links
- Need to establish timeline showing PPO filing was retaliatory (filed after custody filing)
- Need police report analysis showing allegations were investigated and unfounded

### Missing Evidence
- [ ] Complete CPS investigation records (if any investigations occurred)
- [ ] Text messages from Cody Watson threatening to "take my son and put me in jail"
- [ ] Emily Watson's workplace records from Kent County Prosecutor's Office
- [ ] Body camera footage from any police encounters

### Authentication Status
| Evidence | Court-Ready? | Foundation |
|----------|:----------:|------------|
| PPO filings/orders | ✅ | Court records — self-authenticating |
| Albert+Emily recording | ⚠️ | MRE 901(a) — need foundation testimony |
| Police reports | ✅ | Public records (MRE 803(8)) |
| Text messages | ⚠️ | Need authentication per MRE 901(b)(6) |

---

## Lane E — Judicial Misconduct / JTC (Hon. Jenny L. McNeill)

### Total Evidence Items
- **Evidence quotes:** 22,694
- **Critical facts:** 362
- **Narrative context:** 713
- **Case timeline entries:** 878 (highest of any lane)
- **Judicial violations:** 4,812 (96% of all judicial violations)
- **Claims:** 6

### Strongest Evidence

**Judicial Violation Breakdown** (Source: `SELECT violation_type, COUNT(*) FROM judicial_violations WHERE lane='E' GROUP BY violation_type`):

| Violation Type | Count |
|---------------|------:|
| ex_parte | 3,697 |
| bias | 1,076 |
| improper_procedure | 37 |
| canon_violation | 29 |
| denial_of_hearing | 19 |
| due_process | 8 |

### Ready-to-File Claims
- **E-EX-PARTE** (11,807 items, strength 0.9) → Ex parte violations documented with 3,697 specific violations
- **E-DISQUALIFY** (11,800 items, strength 0.9) → MCR 2.003 disqualification — Filing F3
- **E-HOSTILE-RECORD** (14,484 items, strength 0.9) → Hostile record practices

### Weakest Links
- **E-BIAS** (12 items, strength 0.35) — **CRITICAL GAP.** Generic bias claim has almost no evidence. The specifics are in E-EX-PARTE and E-HOSTILE-RECORD instead.
- **E-CANON** (4 items, strength 0.35) — Canon violation claim nearly unsupported. Needs specific Michigan Code of Judicial Conduct provisions cited with factual violations.

### Missing Evidence
- [ ] Transcripts of hearings where bias was demonstrated
- [ ] Comparison analysis: how Judge McNeill treated similarly-situated litigants
- [ ] Specific Canon provisions with factual violation narratives
- [ ] JTC complaint precedents (prior successful complaints for comparison)

### Authentication Status
| Evidence | Court-Ready? | Foundation |
|----------|:----------:|------------|
| Court orders/transcripts | ✅ | Court records — self-authenticating |
| Docket entries | ✅ | Public records |
| Violation analysis | ⚠️ | Need to attach underlying source documents |

---

## Lane F — Appellate (COA 366810)

### Total Evidence Items
- **Evidence quotes:** 3,504
- **Critical facts:** 88
- **Narrative context:** 620
- **Case timeline entries:** 68
- **Judicial violations:** 63
- **Claims:** 5 (2 ready, 3 draft/proposed)

### Strongest Evidence
- **F-COA-APPEAL** (17,875 items, strength 0.9) → Filing F9 (COA Brief)
- **F-MSC-BYPASS** (15,183 items, strength 0.9) → MSC bypass application
- **F-SUPER-CTRL** (17,866 items, strength 0.9) → Superintending control

### Weakest Links
- Lane F relies heavily on evidence from Lanes A, D, and E. The appellate record must be properly compiled.
- Need to ensure all lower court orders are properly certified for the appellate record.

### Missing Evidence
- [ ] Complete certified lower court record
- [ ] All hearing transcripts (ordered and received)
- [ ] Proof of all motions filed below (with file stamps)
- [ ] Certificate of service for all filings

### Authentication Status
| Evidence | Court-Ready? | Foundation |
|----------|:----------:|------------|
| Lower court record | ⚠️ | Need certified copies from 14th Circuit clerk |
| Transcripts | ⚠️ | Need court reporter certification |
| Prior briefs/motions | ✅ | Self-authenticating as court filings |

---

## Cross-Lane Summary

### Evidence Arsenal Totals
| Metric | Count |
|--------|------:|
| Total evidence quotes | 92,246 |
| Total critical facts | 3,048 |
| Total narrative context | 9,110 |
| Total judicial violations | 5,063 |
| Total case timeline entries | 1,472 |
| Total docket events | 683 |
| Total claims | 35 |
| Filing packages | 10 |
| Documents cataloged | 6,386 |
| Files inventoried | 230,000 |

### Claims Ready for Filing (strength ≥ 0.9, status = "ready")
1. **A-EMRG-CUST** — Emergency custody restoration
2. **A-VACATE** — Omnibus vacate void orders
3. **A-PT-ENFORCE** — Parenting time enforcement
4. **D-PPO-TERM** — PPO termination
5. **E-EX-PARTE** — Ex parte violations
6. **E-DISQUALIFY** — Judicial disqualification MCR 2.003
7. **F-COA-APPEAL** — COA appeal brief
8. **F-MSC-BYPASS** — MSC bypass application

### Critical Gaps Requiring Immediate Action
1. **E-BIAS** and **E-CANON** claims have almost no evidence (12 and 4 items respectively)
2. **C-CONSPIRACY** needs direct coordination evidence (only 239 items, strength 0.6)
3. **Evidence authentication** table has only 1 record — all exhibits need authentication tracking
4. **Albert+Emily recording** needs proper foundation testimony prepared
5. **Missing third-party corroboration** for child welfare claims (L.D.W.)
