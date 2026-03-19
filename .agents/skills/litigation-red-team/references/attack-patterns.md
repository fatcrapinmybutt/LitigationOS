# Attack Patterns — litigation-red-team

## Comprehensive Attack Vector Library

This reference catalogs all 28 attack vectors with detailed Michigan-specific
application guidance for the 14th Judicial Circuit, Muskegon County.

---

## PROCEDURAL ATTACKS (V1–V8)

### V1: Jurisdiction / Standing Challenge

**Attack**: The filing party lacks standing or the court lacks jurisdiction.

| Lane | Attack Application |
|------|-------------------|
| A | Challenge non-parent standing under MCL 722.26b. If filing party is not legal parent, standing must be independently established. |
| B | Challenge contractual standing — is plaintiff actually on the lease? Does plaintiff have privity with Shady Oaks? |
| C | Challenge Article III standing for federal claims. Injury-in-fact, causation, redressability. |

**Michigan Authority**: MCL 600.605 (circuit court jurisdiction); MCR 2.116(C)(1) (lack of jurisdiction)

### V2: Statute of Limitations / Laches

**Attack**: Claims are time-barred or unreasonably delayed.

| Claim Type | Limitation Period | Authority |
|------------|------------------|-----------|
| Custody modification | None (but laches possible) | MCL 722.27 |
| Personal injury (housing) | 3 years | MCL 600.5805(10) |
| Contract (housing) | 6 years | MCL 600.5807(8) |
| MCPA violations | 6 years | MCL 445.911(7) |
| 42 USC § 1983 | 3 years (borrows state PI) | Owens v Okure, 488 US 235 |
| JTC complaint | No fixed limit | MCR 9.220 |

### V3: Service Defects

**Attack**: Service of process was defective, depriving court of personal jurisdiction.

**Common Defects**:
- Served by a party (MCR 2.103(A) requires non-party server)
- Wrong address (not defendant's usual place of abode)
- Corporate defendant not served via registered agent (MCR 2.105(D))
- Service outside 91-day window (MCR 2.102(D))

### V4: Failure to State a Claim — MCR 2.116(C)(8)

**Attack**: Even accepting all allegations as true, no legal claim is stated.

**Lane-Specific Application**:
- Lane A: Custody modification without alleging proper cause or change of circumstances
- Lane B: Habitability claim without alleging notice to landlord per MCL 554.139
- Lane C: § 1983 claim without alleging specific constitutional violation + state action

### V5: Improper Venue

**Attack**: Case filed in wrong county or court division.

**Michigan Venue Rules**: MCL 600.1621 et seq.
- Lane A: County where child resides (Muskegon = proper if child is here)
- Lane B: County where property is located or defendant resides
- Lane C: Federal venue under 28 USC § 1391

### V6: Failure to Exhaust Administrative Remedies

**Attack**: Administrative process not completed before court filing.

**Lane A**: Friend of the Court process not exhausted for custody/support
**Lane B**: Local housing code enforcement process not exhausted
**Lane C**: Government tort claims act notice (MCL 691.1404) — 6 months

### V7: Mootness / Ripeness

**Attack**: Issue is not yet ripe for adjudication or has become moot.

**Examples**:
- PPO modification moot if PPO already expired
- Housing conditions fixed before trial → damages may survive but injunction moot
- Government policy changed → § 1983 prospective relief moot

### V8: Res Judicata / Collateral Estoppel

**Attack**: Issue already decided in prior proceeding.

**Michigan Test**: Adair v State, 470 Mich 105 (2004)
1. Prior action decided on merits
2. Both actions involve same parties or their privies
3. Issues were or could have been raised in prior action
4. Same transaction or occurrence

---

## SUBSTANTIVE ATTACKS (V9–V18)

### V9: Insufficient Factual Allegations

**Attack**: Filing contains legal conclusions without supporting facts.
**Defense**: Distinguish between notice pleading (Michigan) and heightened
pleading standards. MCR 2.111(B)(1) requires "concise statement of facts."

### V10: Weak Evidence Linkage

**Attack**: Claims lack evidentiary support or evidence doesn't prove what filer claims.
**Key Question**: For each factual assertion, is there admissible evidence in the record?

### V11: Misapplied Legal Standard

**Attack**: Wrong legal standard applied to the facts.
**Lane A Examples**: Using "preponderance" when "clear and convincing" required for ECE change.
**Lane B Examples**: Applying strict liability when negligence standard applies.

### V12: Contradicted by Record Evidence

**Attack**: Filer's assertions contradicted by documents already in the record.
**Integration**: Cross-reference with litigation-impeachment-engine data.

### V13: Hearsay Reliance — MRE 801–807

**Attack**: Key claims supported only by hearsay without exception.
**Checklist**: For each key statement, identify: declarant, circumstances, applicable exception.

### V14: Authentication Gaps — MRE 901

**Attack**: Evidence not properly authenticated.
**Digital Evidence**: Screenshots, emails, texts require authentication methodology.

### V15: Privilege / Confidentiality Issues

**Attack**: Filing relies on or discloses privileged material.
**Types**: Attorney-client, physician-patient (MCL 600.2157), spousal, therapist.

### V16: Best Evidence Rule — MRE 1001–1008

**Attack**: Copies offered when originals available and content is disputed.
**Application**: Primarily Lane B (lease terms, inspection reports).

### V17: Expert Witness Foundation — MRE 702

**Attack**: Expert opinions lack proper foundation or qualification.
**Michigan Standard**: Gilbert v DaimlerChrysler Corp, 470 Mich 749 (2004).

### V18: Constitutional Argument Weaknesses

**Attack**: Constitutional claims lack established precedent or fail elements.
**Lane C Focus**: Due process, equal protection, First Amendment claims must meet
established framework. Conclusory constitutional allegations are insufficient.

---

## STRATEGIC ATTACKS (V19–V28)

### V19: Predictable Counter-Narrative
Opposing counsel will construct an alternative narrative. What is it?
Lane A: "The other parent is the problem, not our client."
Lane B: "Tenant caused the conditions / failed to report / failed to mitigate."
Lane C: "Officials acted in good faith within their authority."

### V20: Timing Vulnerability
Is this filing premature or late? Could opposing counsel argue bad faith timing?

### V21: Credibility Exposure
Does this filing expose the filer's prior inconsistencies?

### V22: Proportionality Challenge
Could opposing counsel argue the relief sought is disproportionate?

### V23: Alternative Explanation Strength
How strong is the innocent explanation for the facts alleged?

### V24: Sympathy Asymmetry
Which party does the judge naturally sympathize with? How does this affect framing?

### V25: Resource Asymmetry Exploitation
Corporate defendants (Lane B) will outspend. Government defendants (Lane C) have
institutional resources. Strategy must account for this.

### V26: Cross-Lane Contamination Risk
Does evidence or argument in one lane create problems in another?

### V27: Public Record / Media Exposure Risk
Could this filing attract unwanted attention or be used against the filer?

### V28: Appeal Vulnerability Analysis
If this filing fails, what is the appellate path? Are issues preserved?
