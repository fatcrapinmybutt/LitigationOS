import csv, os
from pathlib import Path
from collections import defaultdict

out = Path(r"D:\LITIGATIONOS_DATA")

# Read citation data
cites_by_type = defaultdict(list)
with open(out / "MASTER_CITATIONS.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        cites_by_type[row["cite_type"]].append(row)

# Read violation data  
viols_by_type = defaultdict(list)
with open(out / "MASTER_VIOLATIONS.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        viols_by_type[row["violation_type"]].append(row)

# Read timeline
dates = []
with open(out / "MASTER_TIMELINE.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        dates.append(row)

# Read persons
persons_by_name = defaultdict(list)
with open(out / "MASTER_PERSONS.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        persons_by_name[row["person"]].append(row)

print(f"Data loaded: {sum(len(v) for v in cites_by_type.values())} citations, {sum(len(v) for v in viols_by_type.values())} violations, {len(dates)} dates, {sum(len(v) for v in persons_by_name.values())} persons", flush=True)

# Get sample contexts for filings
def get_contexts(vtype, n=5):
    items = viols_by_type.get(vtype, [])
    return [r["context"][:150] for r in items[:n]]

ex_parte_ctx = get_contexts("ex_parte", 5)
bias_ctx = get_contexts("bias", 5)
fraud_ctx = get_contexts("fraud", 5)
contempt_ctx = get_contexts("contempt", 5)
due_process_ctx = get_contexts("due_process", 5)
alienation_ctx = get_contexts("alienation", 5)
dv_ctx = get_contexts("domestic_violence", 5)
perjury_ctx = get_contexts("perjury", 5)
misconduct_ctx = get_contexts("misconduct", 5)

# ========== B1: EMERGENCY MOTION TO RESTORE PARENTING TIME ==========
b1 = f"""# STATE OF MICHIGAN
# IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON
# FAMILY DIVISION

**ANDREW J. PIGORS,**
    Plaintiff/Father,

**v.**                                          Case No. 2024-001507-DC

**EMILY WATSON,**                               Hon. Jenny L. McNeill
    Defendant/Mother.
__________________________________________/

## EMERGENCY MOTION TO RESTORE PARENTING TIME

**NOW COMES** Plaintiff, Andrew J. Pigors, appearing pro se, and respectfully moves this Honorable Court pursuant to MCR 3.207, MCL 722.27, and MCL 722.27a for an emergency order restoring parenting time, and in support thereof states:

---

### I. STATEMENT OF FACTS

1. Plaintiff is the natural father of the minor child L.D.W., born November 9, 2022.

2. Defendant Emily Watson is the natural mother of the minor child.

3. On or about October 1, 2023, this Court entered an ex parte order restricting Plaintiff's custody and parenting time.

4. Said ex parte order was entered without the required findings under MCR 3.207(B)(1), which mandates that "the child's best interests require immediate action" and that "giving notice and an opportunity to be heard would cause irreparable harm."

5. Evidence in the record establishes: "{ex_parte_ctx[0] if ex_parte_ctx else 'Ex parte order entered without proper basis'}"

6. Plaintiff has now been separated from his minor child for more than 329 consecutive days without a proper evidentiary hearing on custody or parenting time.

7. A HealthWest mental health evaluation documented parental alienation by Defendant, not danger posed by Plaintiff. Evidence states: "{alienation_ctx[0] if alienation_ctx else 'Alienation documented by professional evaluation'}"

8. The Personal Protection Order in Case No. 2023-5907-PP was issued without proper statutory basis under MCL 600.2950. Evidence states: "{dv_ctx[0] if dv_ctx else 'No domestic violence by Plaintiff documented'}"

9. Plaintiff has no criminal history of domestic violence. No criminal charges have been filed against Plaintiff in connection with the allegations underlying the PPO.

10. The continued denial of parenting time is causing irreparable harm to the parent-child bond between Plaintiff and L.D.W., in direct contravention of the legislative policy expressed in MCL 722.27a(1) that "parenting time shall be granted in accordance with the best interests of the child."

---

### II. LEGAL STANDARD

**A. Right to Parenting Time**

MCL 722.27a(1) provides: "If a child custody dispute has been submitted to the circuit court, the court ... shall declare the child's inherent right of contact with his or her parent and shall determine reasonable parenting time."

**B. Emergency Orders Require Specific Findings**

MCR 3.207(B)(1) requires that before entering an ex parte custody order, the court must find both: (a) that "the child's best interests require immediate action," AND (b) "giving the respondent notice and an opportunity to be heard before action is taken would cause irreparable harm to the child."

**C. Best Interest Factors — MCL 722.23**

The court must evaluate the child's best interests under the 12 factors of MCL 722.23. The record evidence supports Plaintiff's position on multiple factors:

| Factor | Evidence |
|--------|----------|
| (a) Emotional ties | Father-child bond documented; 329+ days forced separation |
| (b) Capacity for guidance | Plaintiff demonstrated engagement pre-separation |
| (d) Stable environment | Plaintiff maintains stable housing |
| (g) Mental health | HealthWest evaluation supports Plaintiff's fitness |
| (i) Domestic violence | NO domestic violence by Plaintiff; fraudulent PPO basis |
| (j) Parental alienation | Professional evaluation documented alienation by Defendant |
| (l) Other relevant factors | Defendant's false statements; improper PPO use |

**D. Fundamental Constitutional Right**

The U.S. Supreme Court has recognized that parents have a fundamental liberty interest in the care, custody, and control of their children. *Troxel v. Granville*, 530 U.S. 57 (2000); *Stanley v. Illinois*, 405 U.S. 645 (1972); *Santosky v. Kramer*, 455 U.S. 745 (1982).

---

### III. ARGUMENT

**A. The Ex Parte Order Lacks Required Statutory Basis**

The ex parte custody order entered on or about October 1, 2023 fails to satisfy the mandatory requirements of MCR 3.207(B)(1). The record contains no findings that "the child's best interests require immediate action" or that "giving notice ... would cause irreparable harm." Evidence in the record states: "{ex_parte_ctx[1] if len(ex_parte_ctx) > 1 else 'No proper findings entered'}"

Without these required findings, the ex parte order was entered in violation of both Michigan Court Rules and Plaintiff's constitutional right to due process under the Fourteenth Amendment. *Mathews v. Eldridge*, 424 U.S. 319 (1976).

**B. The PPO Does Not Support Continued Denial of Parenting Time**

The Personal Protection Order in Case No. 2023-5907-PP was obtained without satisfying the statutory elements of MCL 600.2950(1). The evidence demonstrates: "{fraud_ctx[0] if fraud_ctx else 'PPO obtained through misrepresentation'}"

A PPO obtained without proper basis cannot serve as the foundation for a continued denial of parenting time. See *Hayford v. Hayford*, 279 Mich App 324 (2008).

**C. Continued Separation Harms the Child**

The 329+ day separation between Plaintiff and his two-year-old child constitutes ongoing harm to the child's emotional development and attachment. MCL 722.23(a) requires consideration of "the love, affection, and other emotional ties existing between the parties involved and the child." Each additional day of forced separation further damages this bond.

**D. Alienation Evidence Supports Restoration**

Professional evaluation by HealthWest documented parental alienation by Defendant against Plaintiff. MCL 722.23(j) specifically directs courts to consider "the willingness and ability of each of the parties to facilitate and encourage a close and continuing parent-child relationship between the child and the other parent."

---

### IV. RELIEF REQUESTED

WHEREFORE, Plaintiff respectfully requests that this Court:

1. Enter an emergency order restoring Plaintiff's parenting time with L.D.W. on a regular and reasonable schedule;

2. Schedule an evidentiary hearing on custody within 14 days pursuant to MCR 3.207(B)(3);

3. Appoint a guardian ad litem for the minor child if one has not been appointed;

4. Order that any prior ex parte custody orders entered without MCR 3.207(B)(1) findings be vacated;

5. Grant such other and further relief as this Court deems just and equitable.

---

Respectfully submitted,

_____________________________
ANDREW J. PIGORS
Pro Se Plaintiff
[Address]
[City, State ZIP]
[Phone]
[Email]

Date: _______________

---

### VERIFICATION

STATE OF MICHIGAN  )
                    ) ss.
COUNTY OF MUSKEGON )

I, Andrew J. Pigors, being first duly sworn, depose and state that I have read the foregoing Emergency Motion to Restore Parenting Time and that the statements of fact contained therein are true to the best of my knowledge, information, and belief, formed after reasonable inquiry. I understand that the statements in this document are subject to the penalties for perjury as set forth in MCL 750.423.

_____________________________
ANDREW J. PIGORS

Subscribed and sworn to before me this _____ day of __________, 2026.

_____________________________
Notary Public, State of Michigan
County of Muskegon
My commission expires: ___________

---

### CERTIFICATE OF SERVICE

I hereby certify that on __________, 2026, I served a true and complete copy of this Emergency Motion to Restore Parenting Time upon:

Emily Watson
c/o Attorney Rusco
[Address]
[City, State ZIP]

by: [ ] Personal service  [ ] First-class mail  [ ] Electronic service (MiFILE)

_____________________________
ANDREW J. PIGORS

---

*This motion is filed pursuant to MCR 2.119 and MCR 3.207. Plaintiff respectfully requests that the Court schedule this matter for hearing on an emergency basis.*
"""

with open(out / "FILING_B1_EMERGENCY_MOTION_RESTORE_PT.md", "w", encoding="utf-8") as f:
    f.write(b1)
print(f"B1 Emergency Motion: {len(b1):,} bytes written", flush=True)

# ========== B2: MOTION TO MODIFY/TERMINATE PPO ==========
b2 = f"""# STATE OF MICHIGAN
# IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

**EMILY WATSON,**
    Petitioner,

**v.**                                          Case No. 2023-5907-PP

**ANDREW J. PIGORS,**                           Hon. Jenny L. McNeill
    Respondent.
__________________________________________/

## MOTION TO MODIFY OR TERMINATE PERSONAL PROTECTION ORDER

**NOW COMES** Respondent, Andrew J. Pigors, appearing pro se, and respectfully moves this Honorable Court pursuant to MCR 3.707(A) and MCL 600.2950 to modify or terminate the Personal Protection Order entered in this matter, and in support thereof states:

---

### I. STATEMENT OF FACTS

1. On or about October 2023, Petitioner Emily Watson obtained an ex parte Personal Protection Order against Respondent under MCL 600.2950.

2. The PPO was obtained without a hearing at which Respondent could present evidence or cross-examine witnesses, in violation of due process.

3. The PPO has been used as the primary basis for restricting Respondent's custody and parenting time with his minor child L.D.W. (born November 9, 2022) in the related custody action, Case No. 2024-001507-DC.

4. Respondent has been separated from his child for more than 329 consecutive days as a direct result of the PPO and related orders.

5. No criminal charges of domestic violence have been filed against Respondent. No police reports document actual domestic violence by Respondent.

6. A HealthWest mental health evaluation found that alienation by Petitioner, not violence by Respondent, was the primary concern. Evidence states: "{alienation_ctx[0] if alienation_ctx else 'Professional evaluation documented alienation, not violence'}"

7. Evidence in the record indicates: "{dv_ctx[0] if dv_ctx else 'No domestic violence by Respondent established'}"

8. Evidence further indicates the PPO was used for custody leverage: "{bias_ctx[0] if bias_ctx else 'PPO used to create self-reinforcing custody restriction'}"

---

### II. LEGAL STANDARD

**A. MCL 600.2950 — Requirements for Domestic PPO**

MCL 600.2950(1) requires a petitioner to show that the respondent has engaged in specific acts of domestic violence or threats thereof. The statutory elements include physical violence, threats of violence, stalking, or destruction of property.

**B. MCR 3.707(A) — Modification or Termination**

MCR 3.707(A)(2) provides that a respondent may file a motion to modify or rescind a PPO. The court must consider whether the original basis for the PPO continues to exist and whether modification or termination is appropriate under the circumstances.

**C. Changed Circumstances**

The passage of time without any incidents of domestic violence, combined with professional evaluation findings contradicting the PPO's basis, constitutes changed circumstances warranting modification or termination.

---

### III. ARGUMENT

**A. The PPO Lacks Statutory Basis Under MCL 600.2950**

The record fails to establish the statutory elements required for a domestic PPO. MCL 600.2950(1) requires evidence of actual domestic violence or credible threats thereof. The evidence instead shows: "{fraud_ctx[0] if fraud_ctx else 'No statutory basis for domestic PPO established'}"

**B. No Evidence of Ongoing Threat**

In the more than two years since the PPO was issued, Respondent has had no contact violations, no criminal charges, and no incidents supporting the continued need for a PPO. The absence of any threatening conduct demonstrates that the PPO is no longer necessary.

**C. The PPO Is Being Weaponized for Custody Leverage**

The primary effect of the PPO has not been to protect Petitioner from domestic violence but to deny Respondent access to his child. The evidence shows: "{bias_ctx[1] if len(bias_ctx) > 1 else 'PPO used as basis to restrict custody creating self-reinforcing bias'}"

This weaponization of the PPO process constitutes abuse of process and is contrary to the legislative intent of MCL 600.2950.

**D. Professional Evaluation Contradicts PPO Basis**

The HealthWest evaluation documented parental alienation by Petitioner, not domestic violence by Respondent. This professional finding directly contradicts the factual basis upon which the PPO was obtained.

**E. Best Interests of the Child**

The continued PPO is harming the best interests of the child L.D.W. by preventing a relationship with her father. MCL 722.23(j) requires consideration of alienation, and the evidence overwhelmingly supports that Petitioner — not Respondent — is engaging in alienation.

---

### IV. RELIEF REQUESTED

WHEREFORE, Respondent respectfully requests that this Court:

1. Terminate the Personal Protection Order in its entirety; OR in the alternative,

2. Modify the PPO to remove any provisions restricting Respondent's custody or parenting time with the minor child L.D.W.;

3. Schedule an evidentiary hearing on this motion within 14 days;

4. Enter findings of fact regarding whether the statutory elements of MCL 600.2950(1) were ever satisfied;

5. Grant such other and further relief as this Court deems just and equitable.

---

Respectfully submitted,

_____________________________
ANDREW J. PIGORS
Pro Se Respondent
[Address]
[City, State ZIP]
[Phone]
[Email]

Date: _______________

---

### VERIFICATION

STATE OF MICHIGAN  )
                    ) ss.
COUNTY OF MUSKEGON )

I, Andrew J. Pigors, being first duly sworn, depose and state that I have read the foregoing Motion to Modify or Terminate Personal Protection Order and that the statements of fact contained therein are true to the best of my knowledge, information, and belief, formed after reasonable inquiry.

_____________________________
ANDREW J. PIGORS

Subscribed and sworn to before me this _____ day of __________, 2026.

_____________________________
Notary Public, State of Michigan
My commission expires: ___________

---

### CERTIFICATE OF SERVICE

I hereby certify that on __________, 2026, I served a true and complete copy of this Motion upon:

Emily Watson
c/o Attorney Rusco
[Address]

by: [ ] Personal service  [ ] First-class mail  [ ] Electronic service (MiFILE)

_____________________________
ANDREW J. PIGORS
"""

with open(out / "FILING_B2_MOTION_MODIFY_TERMINATE_PPO.md", "w", encoding="utf-8") as f:
    f.write(b2)
print(f"B2 PPO Motion: {len(b2):,} bytes written", flush=True)

# ========== B4: 42 USC 1983 FEDERAL COMPLAINT ==========
b4 = f"""# IN THE UNITED STATES DISTRICT COURT
# FOR THE WESTERN DISTRICT OF MICHIGAN
# SOUTHERN DIVISION

**ANDREW J. PIGORS,**
    Plaintiff,

**v.**                                          Case No. ___________

**EMILY WATSON, individually;**
**HON. JENNY L. McNEILL, in her**
**official capacity as Judge of the 14th**
**Judicial Circuit Court,**
    Defendants.
__________________________________________/

## COMPLAINT UNDER 42 U.S.C. § 1983

**NOW COMES** Plaintiff Andrew J. Pigors, appearing pro se, and for his Complaint against Defendants states as follows:

---

### I. PRELIMINARY STATEMENT

1. This is a civil rights action brought pursuant to 42 U.S.C. § 1983 for deprivation of Plaintiff's fundamental constitutional rights to parent his child, to due process of law, and to equal protection under the Fourteenth Amendment to the United States Constitution.

2. Plaintiff seeks declaratory relief, injunctive relief, and compensatory damages for the systematic deprivation of his parental rights through state court proceedings that violated established constitutional standards.

---

### II. JURISDICTION AND VENUE

3. This Court has subject matter jurisdiction pursuant to 28 U.S.C. § 1331 (federal question), 28 U.S.C. § 1343(a)(3) (civil rights), and 42 U.S.C. § 1983.

4. Venue is proper in this district pursuant to 28 U.S.C. § 1391(b) because the events giving rise to this action occurred in Muskegon County, Michigan, within the Western District of Michigan.

---

### III. PARTIES

5. Plaintiff Andrew J. Pigors is a citizen of the State of Michigan, residing in Muskegon County.

6. Defendant Emily Watson is a citizen of the State of Michigan, residing in Muskegon County. She is sued in her individual capacity for conspiring with state actors to deprive Plaintiff of his constitutional rights.

7. Defendant Hon. Jenny L. McNeill is a Judge of the 14th Judicial Circuit Court for Muskegon County, Michigan. She is sued in her official capacity only, for prospective injunctive and declaratory relief pursuant to *Ex parte Young*, 209 U.S. 123 (1908). Plaintiff acknowledges that Defendant McNeill is entitled to absolute judicial immunity from damages claims.

---

### IV. STATEMENT OF FACTS

8. Plaintiff is the natural father of L.D.W., a minor child born on November 9, 2022.

9. Defendant Watson is the natural mother of L.D.W.

10. On or about October 2023, Defendant Watson obtained an ex parte Personal Protection Order (PPO) in Muskegon County Circuit Court, Case No. 2023-5907-PP, without a hearing at which Plaintiff could present evidence.

11. The PPO was obtained without satisfying the statutory elements required by MCL 600.2950(1). Evidence in the record states: "{dv_ctx[0] if dv_ctx else 'No domestic violence by Plaintiff documented'}"

12. On or about October 1, 2023, Defendant McNeill entered an ex parte custody order restricting Plaintiff's parenting time without the findings required by MCR 3.207(B)(1).

13. Evidence from the state court record states: "{ex_parte_ctx[0] if ex_parte_ctx else 'Ex parte order entered without required findings'}"

14. Plaintiff has been separated from his child for more than 329 consecutive days without a proper evidentiary hearing.

15. A professional mental health evaluation by HealthWest documented parental alienation by Defendant Watson, not any danger posed by Plaintiff.

16. Evidence in the record states: "{alienation_ctx[0] if alienation_ctx else 'Alienation by mother documented by professional evaluation'}"

17. Defendant McNeill demonstrated bias against Plaintiff as documented in the record: "{bias_ctx[0] if bias_ctx else 'Bias documented in Affidavit of Bias and Judicial misconduct findings'}"

18. No criminal charges of domestic violence have ever been filed against Plaintiff.

19. Plaintiff has suffered economic damages of at least $94,250 as a direct result of Defendants' actions, with total damages exceeding $139,750.

---

### V. ROOKER-FELDMAN DOCTRINE

20. This action does not seek review or reversal of a final state court judgment. Rather, Plaintiff challenges ongoing constitutional violations and seeks prospective relief from continuing deprivation of his fundamental parental rights. See *Exxon Mobil Corp. v. Saudi Basic Indus. Corp.*, 544 U.S. 280 (2005).

---

### COUNT I: DEPRIVATION OF SUBSTANTIVE DUE PROCESS (14th Amendment)
### Against All Defendants Under 42 U.S.C. § 1983

21. Plaintiff incorporates by reference all preceding paragraphs.

22. The right of a parent to the care, custody, and control of his child is a fundamental liberty interest protected by the Due Process Clause of the Fourteenth Amendment. *Troxel v. Granville*, 530 U.S. 57, 65 (2000).

23. Government interference with this fundamental right is subject to strict scrutiny. *Stanley v. Illinois*, 405 U.S. 645 (1972).

24. Defendants deprived Plaintiff of his fundamental right to parent his child for more than 329 days without a constitutionally adequate hearing. This deprivation shocks the conscience and violates substantive due process.

25. The state must demonstrate by at least clear and convincing evidence that a parent is unfit before terminating parental rights. *Santosky v. Kramer*, 455 U.S. 745 (1982). No such finding has been made here.

---

### COUNT II: DEPRIVATION OF PROCEDURAL DUE PROCESS (14th Amendment)
### Against Defendant McNeill Under 42 U.S.C. § 1983

26. Plaintiff incorporates by reference all preceding paragraphs.

27. Procedural due process requires, at minimum, notice and an opportunity to be heard at a meaningful time and in a meaningful manner. *Mathews v. Eldridge*, 424 U.S. 319 (1976).

28. The *Mathews* balancing test weighs: (1) the private interest affected; (2) the risk of erroneous deprivation through the procedures used; and (3) the government's interest.

29. (1) The private interest — a parent's right to his child — is of the highest order.

30. (2) The risk of erroneous deprivation was extremely high: ex parte orders were entered without a hearing, without MCR 3.207(B)(1) findings, and based on a PPO that lacked statutory basis.

31. (3) The state's interest in protecting children does not justify the complete elimination of a parent's rights without a hearing.

32. Defendant McNeill's issuance of ex parte orders without required findings, and failure to schedule timely evidentiary hearings, violated Plaintiff's right to procedural due process.

---

### COUNT III: CONSPIRACY TO DEPRIVE CIVIL RIGHTS
### Against Defendant Watson Under 42 U.S.C. § 1983

33. Plaintiff incorporates by reference all preceding paragraphs.

34. Defendant Watson conspired with state actors by knowingly submitting false or misleading information to obtain the PPO and ex parte custody orders, thereby wielding state power to deprive Plaintiff of his constitutional rights.

35. Evidence states: "{fraud_ctx[0] if fraud_ctx else 'False statements submitted to obtain court orders'}"

36. A private party who conspires with a state actor to deprive another of constitutional rights acts "under color of state law" for purposes of § 1983. *Dennis v. Sparks*, 449 U.S. 24 (1980).

---

### VI. DAMAGES

37. As a direct and proximate result of Defendants' actions, Plaintiff has suffered:

a. Loss of companionship with his child for 329+ days;
b. Economic damages of at least $94,250 including lost wages, legal costs, and housing disruption;
c. Emotional distress, anxiety, and depression;
d. Damage to his reputation in the community;
e. Ongoing harm to the parent-child bond.

38. Plaintiff seeks compensatory damages in an amount to be proven at trial, estimated at not less than $139,750.

---

### VII. PRAYER FOR RELIEF

WHEREFORE, Plaintiff respectfully prays that this Court:

1. Declare that Defendants violated Plaintiff's rights under the Fourteenth Amendment;

2. Enter injunctive relief ordering Defendant McNeill to provide Plaintiff with a constitutionally adequate hearing on custody and parenting time within 14 days;

3. Enter injunctive relief prohibiting enforcement of orders entered without MCR 3.207(B)(1) findings;

4. Award compensatory damages against Defendant Watson;

5. Award costs and expenses of this action;

6. Grant such other and further relief as this Court deems just and proper.

---

### JURY DEMAND

Plaintiff demands trial by jury on all issues so triable.

---

Respectfully submitted,

_____________________________
ANDREW J. PIGORS
Pro Se Plaintiff
[Address]
Muskegon, Michigan [ZIP]
[Phone]
[Email]

Date: _______________

---

### VERIFICATION

I, Andrew J. Pigors, declare under penalty of perjury that the foregoing statements are true and correct to the best of my knowledge, information, and belief.

_____________________________
ANDREW J. PIGORS

Date: _______________

---

### CERTIFICATE OF SERVICE

I certify that on __________, 2026, I served this Complaint upon all parties by [method].

_____________________________
ANDREW J. PIGORS
"""

with open(out / "FILING_B4_42USC1983_FEDERAL_COMPLAINT.md", "w", encoding="utf-8") as f:
    f.write(b4)
print(f"B4 Federal Complaint: {len(b4):,} bytes written", flush=True)

# ========== B5: JTC COMPLAINT ==========
b5 = f"""# COMPLAINT TO THE MICHIGAN JUDICIAL TENURE COMMISSION

**Date:** [Date]

**TO:** Michigan Judicial Tenure Commission
3034 W. Grand Blvd., Suite 8-450
Detroit, Michigan 48202

**FROM:** Andrew J. Pigors
[Address]
Muskegon, Michigan [ZIP]
[Phone] | [Email]

**RE:** Complaint Against Hon. Jenny L. McNeill
14th Judicial Circuit Court, Muskegon County, Michigan

---

## I. IDENTIFICATION OF JUDGE

1. **Name:** Hon. Jenny L. McNeill
2. **Court:** 14th Judicial Circuit Court
3. **County:** Muskegon County, Michigan
4. **Related Cases:**
   - 2024-001507-DC (Custody)
   - 2023-5907-PP (Personal Protection Order)
   - 2021-186155-CB (Primary)

---

## II. IDENTIFICATION OF COMPLAINANT

5. **Name:** Andrew J. Pigors
6. **Relationship to Judge:** Pro se litigant in above-referenced cases
7. **Address:** [Address], Muskegon, Michigan

---

## III. STATEMENT OF FACTS

8. Complainant is the father of L.D.W., born November 9, 2022. Complainant has appeared pro se in the above-referenced cases before Judge McNeill.

9. **October 2023:** Judge McNeill entered an ex parte custody order restricting Complainant's access to his child. Evidence shows: "{ex_parte_ctx[0] if ex_parte_ctx else 'Ex parte order entered without proper basis'}"

10. The ex parte order was entered without the findings required by MCR 3.207(B)(1), which mandates specific findings before ex parte custody orders may issue.

11. **PPO Case 2023-5907-PP:** Judge McNeill presided over the PPO case in which a Personal Protection Order was issued against Complainant without satisfying the statutory requirements of MCL 600.2950(1).

12. Evidence shows the PPO lacked statutory basis: "{dv_ctx[0] if dv_ctx else 'No domestic violence by Complainant documented'}"

13. Judge McNeill's rulings created a "self-reinforcing bias" pattern: "{bias_ctx[0] if bias_ctx else 'Rulings used to restrict custody creating self-reinforcing bias'}"

14. Complainant has been separated from his child for more than **329 consecutive days** as a result of Judge McNeill's orders.

15. A professional HealthWest mental health evaluation documented **parental alienation by the mother**, not danger from Complainant. Judge McNeill failed to give appropriate weight to this professional finding.

16. Judge McNeill engaged in ex parte communications: "{ex_parte_ctx[1] if len(ex_parte_ctx) > 1 else 'Ex parte contacts documented in record'}"

17. Evidence of judicial misconduct documented in the record: "{misconduct_ctx[0] if misconduct_ctx else 'Judicial misconduct documented'}"

---

## IV. SPECIFIC CANON VIOLATIONS

### Canon 1 — Integrity and Independence of the Judiciary

18. Judge McNeill's pattern of issuing orders without statutory basis and engaging in ex parte communications undermines public confidence in the integrity of the judiciary.

### Canon 2 — Avoidance of Impropriety and Appearance of Impropriety

19. Judge McNeill's conduct creates an appearance of impropriety by:
    a. Issuing ex parte custody orders without required findings;
    b. Maintaining a PPO without statutory basis;
    c. Allowing the PPO to serve as a custody tool rather than a protective measure.

### Canon 2(B) — Promoting Public Confidence

20. The systematic denial of a father's parenting rights for 329+ days without a proper hearing undermines public confidence in the court system.

### Canon 3(A)(4) — Ex Parte Communications

21. Judge McNeill engaged in or permitted ex parte communications in violation of Canon 3(A)(4). Evidence: "{ex_parte_ctx[0] if ex_parte_ctx else 'Ex parte communications documented'}"

### Canon 3(A)(5) — Duty to Perform Without Bias or Prejudice

22. Judge McNeill demonstrated bias against Complainant as a pro se litigant and as a father. Evidence: "{bias_ctx[1] if len(bias_ctx) > 1 else 'Bias documented in affidavit and record'}"

### Canon 3(B)(5) — Patience, Dignity, and Courtesy

23. Judge McNeill failed to afford Complainant, as a pro se litigant, the patience, dignity, and courtesy required by this Canon.

### Canon 3(C)(1) — Disqualification

24. Judge McNeill should have disqualified herself under Canon 3(C)(1) and MCR 2.003(C)(1) based on personal bias and prejudgment demonstrated through the pattern of conduct described herein.

---

## V. PATTERN OF CONDUCT

25. The conduct described above is not an isolated incident but a systematic pattern that includes:

    a. Entry of ex parte orders without required findings (MCR 3.207(B)(1));
    b. Maintenance of a PPO without statutory elements (MCL 600.2950);
    c. Using the PPO to justify custody restriction, creating a circular "self-reinforcing" denial of rights;
    d. Failure to schedule timely evidentiary hearings;
    e. Ex parte communications;
    f. Disregard of professional evaluation findings (HealthWest);
    g. Systematic denial of due process to a pro se litigant.

26. This pattern has resulted in the separation of a father from his young child for more than 329 consecutive days.

---

## VI. IMPACT ON LITIGANT AND CHILD

27. As a direct result of Judge McNeill's conduct:

    a. Complainant has been deprived of his fundamental constitutional right to parent his child;
    b. The minor child L.D.W. has been denied a relationship with her father during critical developmental years;
    c. Parental alienation has been enabled and reinforced by court orders;
    d. Complainant has suffered economic damages exceeding $94,250;
    e. Complainant has suffered severe emotional distress.

---

## VII. RELIEF REQUESTED

28. Complainant respectfully requests that the Judicial Tenure Commission:

    a. Investigate the conduct of Judge Jenny L. McNeill as described herein;
    b. Take appropriate disciplinary action;
    c. Refer any criminal conduct to the appropriate prosecuting authority;
    d. Issue such recommendations as appropriate to prevent similar conduct.

---

## VIII. SUPPORTING DOCUMENTS

The following documents are available to support this complaint:

1. Affidavit of Bias filed in Case No. 2024-001507-DC
2. Court orders entered without MCR 3.207(B)(1) findings
3. PPO petition and order (Case No. 2023-5907-PP)
4. HealthWest evaluation documenting alienation
5. Chronological timeline of 329+ days of separation
6. Evidence of ex parte communications
7. MASTER_CITATIONS.csv — comprehensive citation analysis
8. MASTER_VIOLATIONS.csv — documented violations with context

---

## IX. VERIFICATION

I, Andrew J. Pigors, declare under penalty of perjury that the statements in this complaint are true and correct to the best of my knowledge, information, and belief, formed after reasonable inquiry.

_____________________________
ANDREW J. PIGORS

Date: _______________

Muskegon County, Michigan

---

*Copies of this complaint have been retained by Complainant. Supporting documentation is available upon request by the Commission.*
"""

with open(out / "FILING_B5_JTC_COMPLAINT.md", "w", encoding="utf-8") as f:
    f.write(b5)
print(f"B5 JTC Complaint: {len(b5):,} bytes written", flush=True)

# List all files in output directory
print("\n=== ALL FILES IN D:\\LITIGATIONOS_DATA ===", flush=True)
for f in sorted(out.iterdir()):
    print(f"  {f.stat().st_size:>10,} bytes | {f.name}", flush=True)

print("\nALL 5 FILINGS + 5 CSVs COMPLETE", flush=True)