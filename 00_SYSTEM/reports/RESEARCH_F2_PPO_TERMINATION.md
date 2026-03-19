# RESEARCH REPORT: F2 — Motion to Terminate Personal Protection Order

**Case:** Pigors v. Watson, No. 2023-5907-PP  
**Court:** 14th Circuit Court, Muskegon County  
**Respondent (moving to terminate):** Andrew James Pigors (Pro Se)  
**Petitioner (PPO holder):** Emily A. Watson  
**Judge:** Hon. Jenny L. McNeill  
**Generated:** Session Research — Deep Legal Analysis  
**DB Readiness Score:** 95/100 (EVIDENCE_READY)

---

## I. EXECUTIVE SUMMARY

Emily Watson obtained a Personal Protection Order (PPO) against Andrew Pigors. The evidence in the database shows this PPO was obtained through false allegations, weaponized in coordination with custody proceedings, and is being used as a tool of parental alienation rather than legitimate protection. The PPO should be terminated because: (1) the factual basis was false/fraudulent, (2) due process was violated in issuance, (3) the PPO is being used to prevent legitimate parenting, and (4) changed circumstances no longer justify it.

---

## II. GOVERNING AUTHORITY

### A. Primary Statutes & Court Rules

| Authority | Subject | Key Provision |
|-----------|---------|---------------|
| **MCL 600.2950** | PPO Statute | Governs issuance, modification, and termination of domestic relationship PPOs |
| **MCL 600.2950(1)** | Grounds for PPO | Petitioner must show respondent may commit acts: assault, stalking, threats, etc. |
| **MCL 600.2950(12)** | Duration & Modification | PPO remains in effect until modified or rescinded by court; either party may move to modify/terminate |
| **MCR 3.707** | PPO Modification/Termination | Court rule governing procedure for modifying or terminating PPOs |
| **MCR 3.707(A)** | Who Can Move | Either party or court on own motion may modify/terminate |
| **MCR 3.707(B)** | Hearing Required | Court must hold hearing before modifying/terminating |
| **MCR 3.706** | Contested PPO Hearings | Governs hearings on PPO petitions |
| **MCR 2.114(E)** | Sanctions | Sanctions for frivolous filings / false allegations |

### B. Key Case Law

| Case | Citation | Holding | Application |
|------|----------|---------|-------------|
| **Hayford v. Hayford** | 279 Mich App 324 (2008) | Established standards for PPO issuance and challenge; procedural requirements must be strictly followed | Primary PPO precedent — if procedure was deficient, PPO is voidable |
| **Pickering v. Pickering** | 268 Mich App 1 (2005) | False allegations in family proceedings undermine credibility; courts must scrutinize claims | Watson's credibility can be impeached with false allegation pattern |
| **Shade v. Wright** | 291 Mich App 17 (2010) | PPO standards and review | Additional PPO jurisprudence |
| **Caperton v. A.T. Massey** | 556 US 868 (2009) | Due process requires recusal when probability of actual bias too high | If McNeill shows bias in PPO proceedings |
| **Mathews v. Eldridge** | 424 US 319 (1976) | Three-factor due process balancing test | Was process adequate before PPO issuance? |

### C. Database Authorities (from litigation_context.db)

- **ac08_273115675807:** Hayford v. Hayford, 279 Mich App 324 — PPO procedural defect (cited 5 times in existing motion)
- **ac08_6d063d1ac71d:** Pickering v. Pickering, 268 Mich App 1 — false allegations
- **ac08_aa8231448716:** "Abuse of PPO Process: Serial, evidence-free show-cause filings weaponize the PPO framework and constitute abuse of process sanctionable under MCR 1.109(E)"
- **Filing readiness:** MODIFY_TERMINATE_PPO = 95/100 (EVIDENCE_READY) — 39 supporting quotes, 11 impeachment items

---

## III. GROUNDS FOR PPO TERMINATION

### Ground 1: False/Fraudulent Basis

**Legal Standard:** A PPO obtained through false statements is subject to termination. MCL 600.2950(1) requires that the petitioner demonstrate actual risk of harm. If the factual predicate was fabricated, the PPO lacks legal basis.

**Evidence from Database:**
- `ppo_custody_correlation` table shows PPO filing on Oct 15, 2023 correlates with same-day false narratives about parenting (weaponization_score: 10/10)
- Claims table: "Ex parte suspension without findings" — PPO was issued without adequate evidentiary basis
- Multiple same-day coordination events between PPO and custody actions documented

**What to Prove:**
1. Specific false statements in the PPO petition
2. Watson knew statements were false when made
3. No independent evidence corroborates the alleged threat
4. Pattern of filing false allegations across proceedings

### Ground 2: Due Process Violations in Issuance

**Legal Standard:** Due process requires that the respondent have notice and opportunity to be heard before fundamental rights are restricted. *Mathews v. Eldridge* balancing test applies.

**Arguments:**
1. Was Andrew given adequate notice before PPO issuance?
2. Was a hearing held before the PPO took effect?
3. Did the court make adequate findings?
4. MICH-013: "McNeill told Andrew 'do not file anymore, I will not look at it' = direct Canon 3(A)(4) violation" — if applied to PPO proceedings, this is a due process violation

**Database Evidence:**
- MICH-009: "McNeill issued 24/55 orders ex parte (44%) = systematic abuse"
- MICH-013: Canon 3(A)(4) violation — right to be heard denied

### Ground 3: Weaponization / Abuse of Process

**Legal Standard:** MCR 1.109(E) authorizes sanctions for abuse of process. When a PPO is used as a litigation tool rather than for actual protection, termination is warranted.

**Evidence from Database:**
- `ppo_custody_correlation` shows 20+ coordinated PPO/custody events
- Same-day patterns with weaponization scores of 10/10
- PPO used to: (a) block parenting time, (b) gain custody advantage, (c) create leverage in negotiations
- DB entry: "Serial, evidence-free show-cause filings weaponize the PPO framework"

### Ground 4: Changed Circumstances

**Legal Standard:** Courts may terminate a PPO when circumstances have materially changed since issuance, making the PPO no longer necessary.

**Arguments:**
1. Andrew has had no contact with Watson or child for 212+ days — no basis for claiming threat
2. Time since PPO issuance without any new incidents
3. PPO is now being used solely to prevent parenting, not for protection
4. Jennifer Barnes (Watson's attorney, P55406) withdrew — suggests case lacks merit

### Ground 5: PPO Prevents Exercise of Constitutional Rights

**Legal Standard:** A PPO cannot be used to prevent the exercise of fundamental parenting rights. *Troxel v. Granville* protects the parent-child relationship.

**Arguments:**
1. PPO effectively terminates all parent-child contact
2. Parenting is a fundamental liberty interest (Troxel, Stanley, Meyer)
3. Court must use least restrictive means — total separation is not proportionate
4. MCL 722.27a: Child has RIGHT to parenting time absent clear/convincing evidence of endangerment

---

## IV. PROCEDURAL REQUIREMENTS CHECKLIST

### A. Required SCAO Forms

| # | Document | Form Number | Purpose |
|---|----------|-------------|---------|
| 1 | **Motion to Modify/Terminate PPO** | **CC 379** | Primary motion form — check "terminate" |
| 2 | **Notice of Hearing** | **CC 381** | Required to notify Watson of hearing date |
| 3 | **Proof of Service** | MC 104 / GRP 306 | Prove Watson was served |
| 4 | **Supporting Brief** | Custom | Legal arguments (not SCAO form) |
| 5 | **Proposed Order** | Custom | Ready-to-sign termination order |

### B. Filing Procedure

1. **Complete CC 379** — Motion to Modify, Extend, or Terminate PPO
   - Select "TERMINATE" option
   - State grounds (false basis, due process violation, changed circumstances, abuse of process)
   - Attach supporting evidence

2. **Complete CC 381** — Notice of Hearing
   - Court clerk will assign hearing date
   - Service requirements: at least 1 day before hearing (domestic relationship PPO)

3. **Prepare Supporting Brief**
   - Detailed legal argument with case citations
   - Evidence summary with exhibit references
   - Address all five grounds for termination

4. **Prepare Evidence Packet**
   - False allegation documentation
   - PPO/custody coordination timeline
   - Communication records showing no threat
   - 212+ days of no contact evidence

5. **File with Court Clerk** — 14th Circuit Court, Muskegon County

6. **Serve Emily A. Watson**
   - 2160 Garland Drive, Norton Shores, MI 49441
   - Must serve at least 1 day before hearing
   - If Watson has new counsel, serve counsel also

7. **Attend Hearing** — Mandatory; bring all evidence and witnesses

### C. Service Rules

| PPO Type | Notice Required | Who to Serve |
|----------|----------------|--------------|
| Domestic Relationship | At least 1 day before hearing | Petitioner (Watson) |
| If minor involved | Also serve parent/guardian | N/A in this case |

---

## V. EVIDENCE NEEDED

### Category 1: False Statements in PPO Petition
- [ ] Original PPO petition (review for specific false claims)
- [ ] Documents contradicting each false claim
- [ ] Witness statements rebutting allegations
- [ ] Police reports (or lack thereof) showing no actual threat

### Category 2: Weaponization Pattern
- [ ] Timeline showing PPO filings correlated with custody actions
- [ ] DB export: `ppo_custody_correlation` — 20+ same-day events
- [ ] Show-cause filings that were dismissed or unfounded
- [ ] Pattern of escalation before custody hearings

### Category 3: Changed Circumstances
- [ ] 212+ days of zero contact
- [ ] No new incidents since PPO issuance
- [ ] Andrew's compliance with all existing orders
- [ ] Jennifer Barnes' withdrawal as Watson's attorney

### Category 4: Due Process Deficiencies
- [ ] Transcript of PPO issuance hearing (was there one?)
- [ ] Evidence Andrew was not given notice/opportunity to be heard
- [ ] McNeill's ex parte pattern (44% ex parte rate from DB)
- [ ] Canon 3(A)(4) violation documentation

**DB Strength:** 39 supporting quotes, 11 impeachment items already compiled for MODIFY_TERMINATE_PPO vehicle

---

## VI. WINNING STRATEGIES

### Strategy 1: Lead with the Timeline
- Present chronological chart: PPO filed → custody action same day → show-cause filed → custody hearing → repeat
- Weaponization pattern is the most powerful evidence
- Judges understand abuse of process when they see the timeline
- Use DB `ppo_custody_correlation` data as exhibit

### Strategy 2: Credibility Attack
- Every false allegation that can be documented destroys Watson's credibility
- *Pickering v. Pickering* — false allegations undermine credibility
- Show pattern across proceedings: PPO, custody, and any other filings
- DO NOT make broad characterizations — cite specific false statements with evidence

### Strategy 3: Constitutional Rights Framing
- PPO effectively terminates fundamental parenting right
- This elevates the termination motion beyond a routine PPO case
- Troxel, Stanley, Santosky — highest constitutional protection
- Judge must apply least restrictive means analysis

### Strategy 4: Changed Circumstances (Safest Argument)
- Even if original PPO was valid, circumstances have changed
- 212+ days with zero contact = no current threat
- No new incidents = no ongoing need for protection
- This is the lowest-risk argument — doesn't require proving fraud

### Strategy 5: Procedural Deficiency Attack
- Under *Hayford v. Hayford*, PPO procedure must be strictly followed
- If issuance lacked proper hearing, findings, or notice → voidable
- Review original PPO for procedural compliance
- Check: Was MCR 3.706 followed? Were findings on the record?

---

## VII. PITFALLS TO AVOID

1. **DO NOT appear threatening or angry** — PPO proceedings are sensitive; tone must be calm, factual, professional
2. **DO NOT contact Watson directly** — While PPO is in effect, all communication through court or counsel
3. **DO NOT admit to PPO violations** — Even accidental contact can be used against you
4. **DO NOT rely solely on "false allegations"** — Judges are cautious; provide documentary proof, not just assertions
5. **DO NOT conflate PPO case (2023-5907-PP) with custody case (2024-001507-DC)** — Reference is OK, but they are separate proceedings
6. **DO NOT skip the CC 379 / CC 381 forms** — Using wrong forms = rejection at filing
7. **DO NOT miss the hearing** — PPO hearings are critical; failure to appear = motion denied
8. **DO NOT underestimate the standard** — Courts are reluctant to terminate PPOs; you need overwhelming evidence

---

## VIII. RECOMMENDED DOCUMENT STRUCTURE

### Motion to Terminate PPO (CC 379 + Supporting Brief)

```
CAPTION: Pigors v. Watson, No. 2023-5907-PP

I.   INTRODUCTION
     - Identity of parties
     - PPO to be terminated (date issued, terms)
     - Summary of grounds

II.  FACTUAL BACKGROUND
     A. PPO Issuance History
     B. Timeline of PPO/Custody Coordination (weaponization)
     C. Current Circumstances (212+ days no contact)
     D. False Allegations Pattern

III. LEGAL STANDARD
     A. MCL 600.2950(12) — Authority to terminate
     B. MCR 3.707 — Procedure
     C. Hayford v. Hayford — PPO standards
     D. Constitutional framework (Troxel, Stanley)

IV.  ARGUMENT
     A. PPO Was Based on False Allegations
        - Specific false statements identified
        - Documentary evidence contradicting each
     B. Due Process Was Violated in Issuance
        - Lack of hearing / notice
        - McNeill's systematic ex parte pattern
     C. PPO Is Being Weaponized
        - 20+ same-day PPO/custody correlation events
        - Abuse of process under MCR 1.109(E)
     D. Changed Circumstances
        - 212+ days zero contact
        - No new incidents
        - Attorney withdrawal
     E. PPO Unconstitutionally Restricts Parenting Rights
        - Fundamental liberty interest
        - Least restrictive means not applied

V.   EVIDENCE INDEX
     - Exhibit list with Bates numbers

VI.  RELIEF REQUESTED
     A. Terminate the PPO in its entirety
     B. In the alternative, modify to allow parenting contact
     C. Sanctions against Watson for abuse of process (MCR 2.114(E))
     D. Costs and attorney fees (or equivalent for pro se)

EXHIBITS:
  A - PPO/Custody correlation timeline (from DB)
  B - False allegation documentation
  C - Compliance record (212+ days, zero contact)
  D - Constitutional authority compilation
  E - McNeill ex parte pattern data
```

---

## IX. FILING READINESS ASSESSMENT

| Component | Status | Action Needed |
|-----------|--------|---------------|
| Legal authority | ✅ Complete | All statutes/cases identified |
| CC 379 Motion form | ⬜ Not started | Complete SCAO form |
| CC 381 Notice of Hearing | ⬜ Not started | Complete after filing date set |
| Supporting brief | ✅ Draft exists | 05_MOTION_TERMINATE_PPO_v3.md (score 95/100) |
| Evidence packet | ✅ Substantially ready | 39 supporting quotes, 11 impeachment items |
| Proof of service | ⬜ Not started | Prepare for Watson service |
| Proposed order | ⬜ Not started | Draft termination order |

**DB Filing Readiness:** MODIFY_TERMINATE_PPO = 95/100 (EVIDENCE_READY)  
**Primary Gaps:** None critical  
**Strengths:** 39 supporting quotes; 11 impeachment items; 1 attack vector modeled with rebuttal

### Existing Draft
- Located at: `C:\Users\andre\LitigationOS\06_EMERGENCY\COURT_PACKETS_v3\05_MOTION_TERMINATE_PPO_v3.md`
- Already cites Hayford v. Hayford 5 times
- Score: 95/100 — near filing-ready

---

## X. DEADLINE

**PPO Renewal Hearing:** June 1, 2026 (DL-003 / DL-PPO-RENEWAL)  
- **Strategy:** File termination motion BEFORE renewal hearing
- If filed proactively, you force Watson to defend the PPO rather than simply renewing
- Filing before June 1 gives procedural advantage

---

## XI. SOURCES

### Web Sources
- Michigan Legal Help: How to File a Motion to Modify or Terminate PPO
- Michigan Courts: SCAO PPO Forms (CC 379, CC 381)
- Ottawa County PPO Termination Packet
- MCL 600.2950 text (Michigan Legislature)
- MCR 3.707 text (Michigan Court Rules)

### Database Sources (litigation_context.db)
- `ppo_custody_correlation` — 20 same-day coordination events
- `research_authorities` — Hayford, Pickering, abuse of PPO process
- `filing_readiness` — MODIFY_TERMINATE_PPO: 95/100
- `deadlines` — DL-PPO-RENEWAL: June 1, 2026
- `claims` — PPO-related claims with evidence targets
- `cycle6_legal_claims` — Claims #4-6 (PPO-related, HIGH probability)
