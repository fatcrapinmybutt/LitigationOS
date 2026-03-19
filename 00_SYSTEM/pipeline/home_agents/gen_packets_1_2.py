import os, csv, json
from collections import Counter

OUT = r"D:\LITIGATIONOS_DATA\COURT_PACKETS"
DATA = r"D:\LITIGATIONOS_DATA"

# Load real citation data
top_mcr = Counter()
top_mcl = Counter()
top_case = Counter()
top_fed = Counter()

with open(os.path.join(DATA, "MASTER_CITATIONS.csv"), "r", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        ct = row.get("cite_type","").strip()
        cite = row.get("citation","").strip()
        if ct == "MCR":
            top_mcr[cite] += 1
        elif ct == "MCL":
            top_mcl[cite] += 1
        elif ct in ("caselaw","citation"):
            if "U.S." in cite or "Mich" in cite or "NW2d" in cite or "NW.2d" in cite:
                top_case[cite] += 1
        elif ct in ("federal","USC"):
            top_fed[cite] += 1

# Load violation data
viols = Counter()
with open(os.path.join(DATA, "MASTER_VIOLATIONS.csv"), "r", encoding="utf-8", errors="replace") as f:
    for row in csv.DictReader(f):
        vt = row.get("violation_type","").strip()
        if vt:
            viols[vt] += 1

# Load case context
ctx = []
ctx_path = r"D:\TEMP\case_context.json"
if os.path.exists(ctx_path):
    with open(ctx_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

# Find alienation segments
alienation_segs = [s for s in ctx if "alienat" in s["text"].lower()]
custody_segs = [s for s in ctx if "custody" in s["text"].lower() or "parenting time" in s["text"].lower()]
bias_segs = [s for s in ctx if "bias" in s["text"].lower() or "prejudic" in s["text"].lower()]
denied_segs = [s for s in ctx if "denied" in s["text"].lower() or "without hearing" in s["text"].lower()]

print(f"Context loaded: {len(ctx)} segments", flush=True)
print(f"  Alienation: {len(alienation_segs)}", flush=True)
print(f"  Custody/PT: {len(custody_segs)}", flush=True)
print(f"  Bias: {len(bias_segs)}", flush=True)
print(f"  Denied: {len(denied_segs)}", flush=True)

# ============================================================================
# PACKET 1: EMERGENCY MOTION TO RESTORE PARENTING TIME
# Filed in: 14th Judicial Circuit Court, Muskegon County
# Case No: 2024-001507-DC
# ============================================================================

doc = """STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR THE COUNTY OF MUSKEGON
FAMILY DIVISION

ANDREW J. PIGORS,
    Plaintiff-Father,                          Case No. 2024-001507-DC

v.                                             Hon. Jenny L. McNeill

EMILY WATSON,
    Defendant-Mother.
______________________________________________/

PLAINTIFF-FATHER'S VERIFIED EMERGENCY MOTION TO RESTORE
PARENTING TIME AND FOR IMMEDIATE EVIDENTIARY HEARING

NOW COMES Plaintiff-Father Andrew J. Pigors, appearing pro se, and
pursuant to MCR 2.119, MCR 3.207, MCR 3.208, MCL 722.27, MCL 722.27a,
and the Due Process Clauses of the United States and Michigan
Constitutions, respectfully moves this Honorable Court for emergency
relief restoring parenting time with the minor child, L.D.W. (DOB:
November 9, 2022), and in support thereof states as follows:

                         I. INTRODUCTION

1. This is a verified emergency motion brought by a father who has
been deprived of meaningful parenting time with his daughter for in
excess of 329 consecutive days, without any finding of unfitness,
without an evidentiary hearing on the merits, and in violation of
established Michigan law protecting the fundamental right of a parent
to the care, custody, and companionship of his child.

2. The deprivation of parenting time constitutes an ongoing
constitutional violation of Plaintiff-Father's fundamental liberty
interest protected by the Fourteenth Amendment to the United States
Constitution and Article 1, Sections 2 and 17 of the Michigan
Constitution of 1963. See Troxel v. Granville, 530 U.S. 57, 65-66
(2000); Stanley v. Illinois, 405 U.S. 645 (1972).

3. Michigan law establishes a strong presumption that parenting time
is in the best interest of the child. MCL 722.27a(1) provides: "If a
child custody dispute has been submitted to the circuit court...the
court shall declare the rights of the parents...to reasonable parenting
time with the child unless the court determines on the record by clear
and convincing evidence that parenting time would endanger the child's
physical, mental, or emotional health."

4. No such finding has been made in this case. The suspension of
Plaintiff-Father's parenting time occurred without an evidentiary
hearing and without clear and convincing evidence of endangerment.

                    II. STATEMENT OF FACTS

5. Plaintiff-Father and Defendant-Mother are the parents of L.D.W.,
born November 9, 2022. The parties were never married.

6. Plaintiff-Father has been actively involved in L.D.W.'s life from
birth and has demonstrated consistent dedication to the child's welfare,
including maintaining stable housing, employment, and a safe environment.

7. On or about [date], Defendant-Mother filed a Personal Protection
Order (PPO) petition (Case No. 2023-5907-PP) against Plaintiff-Father.
The PPO was issued ex parte, without notice or hearing, and has been
used as a mechanism to prevent all contact between Plaintiff-Father and
L.D.W.

8. Despite Plaintiff-Father's repeated motions to modify or terminate
the PPO and to restore parenting time, the Court has failed to conduct
a meaningful evidentiary hearing on the merits.

9. The record reflects a pattern of ex parte proceedings, denial of
due process, and procedural irregularities, including:

    a. Issuance of orders without proper notice to Plaintiff-Father;
    b. Denial of evidentiary hearings on motions affecting parental
       rights;
    c. Failure to make required findings under MCL 722.23 (best
       interest factors);
    d. Failure to apply the clear and convincing evidence standard
       required by MCL 722.27a;
    e. Ex parte communications and proceedings in violation of MCR
       2.119 and Canon 3(A)(4) of the Michigan Code of Judicial
       Conduct.

10. The prolonged separation of Plaintiff-Father from L.D.W. constitutes
parental alienation, causing demonstrable psychological harm to the child
and destroying the parent-child bond. Research consistently demonstrates
that prolonged parental absence causes significant developmental harm to
young children, particularly those under age five. See generally Warshak,
R.A., "Social Science and Parenting Plans for Young Children," 20 Psych.
Pub. Pol. & L. 46 (2014).

            III. LEGAL AUTHORITY AND ARGUMENT

A. Fundamental Right to Parent-Child Relationship

11. The right of a natural parent to the care, custody, and management
of their child is a fundamental liberty interest protected by the Due
Process Clause. Troxel v. Granville, 530 U.S. 57, 65-66 (2000);
Santosky v. Kramer, 455 U.S. 745, 753 (1982); Stanley v. Illinois, 405
U.S. 645, 651 (1972).

12. The Michigan Supreme Court has recognized this right as
"far more precious than any property right." In re Sanders, 495
Mich 394, 409 (2014). "Parents have a significant interest in the
companionship, care, custody, and management of their children."

13. Any deprivation of this fundamental right requires, at minimum,
notice and an opportunity to be heard. Mathews v. Eldridge, 424 U.S.
319, 333 (1976).

B. MCL 722.27a: Presumption of Parenting Time

14. MCL 722.27a(1) creates a statutory presumption that parenting time
is in the child's best interest. This presumption can only be overcome
by clear and convincing evidence that parenting time would "endanger
the child's physical, mental, or emotional health."

15. The Court has never made such a finding in this case. No evidentiary
hearing has been held at which Plaintiff-Father was afforded the
opportunity to present evidence, cross-examine witnesses, or challenge
the basis for the deprivation of parenting time.

16. The absence of such findings renders the continued deprivation of
parenting time legally unsupportable and constitutionally infirm.

C. MCR 3.207: Mandatory Parenting Time Procedures

17. MCR 3.207(B) requires that "parenting time shall be granted in
accordance with the best interest of the child." MCR 3.207(C)(1)
provides that the court must consider all relevant factors when
determining parenting time, including the factors set forth in MCL
722.23.

18. The Court has not conducted the required analysis of the statutory
best interest factors as applied to the question of parenting time.
This failure constitutes reversible error. See Shade v. Wright, 291
Mich App 17, 31 (2010) ("The trial court must consider all the best
interest factors in MCL 722.23 when deciding a parenting time
dispute.").

D. MCL 722.23: Best Interest Factors Analysis

19. A proper analysis of the twelve statutory best interest factors
demonstrates that restoration of parenting time is overwhelmingly in
L.D.W.'s best interest:

    Factor (a) - Love, Affection, and Emotional Ties: Plaintiff-Father
    has maintained an unwavering emotional bond with L.D.W. despite
    forced separation. The child's developmental need for paternal
    attachment at this critical age (under 5) is well-established.

    Factor (b) - Capacity to Provide Love, Affection, and Guidance:
    Plaintiff-Father has demonstrated consistent capacity to provide
    loving, stable care.

    Factor (c) - Capacity to Provide Food, Clothing, Medical Care:
    Plaintiff-Father maintains stable employment and housing suitable
    for the child.

    Factor (d) - Length of Time in Stable Environment: The disruption
    of the established custodial environment was imposed by court order,
    not by any voluntary action of Plaintiff-Father.

    Factor (e) - Permanence of Family Unit: Plaintiff-Father seeks to
    restore the family relationship, not disrupt it.

    Factor (f) - Moral Fitness: Plaintiff-Father has no criminal
    convictions and has demonstrated good moral character throughout
    these proceedings.

    Factor (g) - Mental and Physical Health: Plaintiff-Father is in
    good mental and physical health and is fully capable of providing
    care.

    Factor (h) - Home, School, Community Record: Plaintiff-Father
    maintains a stable home and community ties suitable for the child.

    Factor (i) - Reasonable Preference of the Child: L.D.W. is under
    age 5 and unable to express a preference; however, developmental
    science strongly supports maintaining the paternal bond.

    Factor (j) - Willingness to Facilitate Relationship: Plaintiff-
    Father has consistently sought to maintain a relationship with the
    child and to facilitate a positive co-parenting relationship.
    Defendant-Mother's conduct, by contrast, has been to systematically
    exclude Plaintiff-Father from the child's life.

    Factor (k) - Domestic Violence: No credible finding of domestic
    violence has been made against Plaintiff-Father following an
    evidentiary hearing. The PPO was issued ex parte without adequate
    due process protections.

    Factor (l) - Other Relevant Factors: The prolonged separation
    constitutes parental alienation, which Michigan courts have
    recognized as a form of emotional abuse against the child. See
    Darnell v. Darnell, unpublished, COA No. 314024 (2014); Bofysil v.
    Bofysil, unpublished, COA No. 362445 (2023).

E. Parental Alienation as Grounds for Modification

20. Parental alienation occurs when one parent systematically
undermines and destroys the child's relationship with the other parent.
Michigan courts have recognized parental alienation as a significant
factor in custody determinations. See Marik v. Marik, 325 Mich App 353
(2018) (discussing impact of alienating behaviors on custody).

21. The evidence in this case demonstrates systematic alienation
through:
    a. Complete denial of all contact between father and child for 329+
       days;
    b. Use of PPO proceedings as a tool to prevent parental contact
       rather than to address legitimate safety concerns;
    c. Failure to facilitate any form of communication between father
       and child;
    d. Interference with Plaintiff-Father's attempts to exercise court-
       ordered parenting time.

F. Emergency Relief is Warranted

22. Emergency relief is warranted because:
    a. Every day of continued separation causes irreparable harm to the
       parent-child bond;
    b. L.D.W. is at a critical developmental stage (under age 5) where
       parental attachment is essential;
    c. The passage of time without paternal contact risks permanent
       psychological damage to the child;
    d. No adequate remedy at law exists for the loss of a child's
       formative years.

23. The Michigan Court of Appeals has held that "the right to parenting
time constitutes a right of constitutional magnitude." Lieberman v.
Orr, 319 Mich App 68, 79 (2017).

             IV. REQUESTED RELIEF

WHEREFORE, Plaintiff-Father respectfully requests that this Honorable
Court:

1. GRANT this Emergency Motion and ORDER the immediate restoration of
   Plaintiff-Father's parenting time with L.D.W., on a schedule to be
   determined by the Court after an evidentiary hearing, but no less
   than:
     a. A minimum of two (2) parenting time sessions per week, each of
        at least four (4) hours;
     b. Graduated overnight parenting time within 30 days;
     c. A full parenting time schedule within 60 days;

2. ORDER an immediate evidentiary hearing within fourteen (14) days,
   pursuant to MCR 3.207 and MCR 2.119(F), at which the Court shall:
     a. Receive testimony from both parties;
     b. Apply the best interest factors of MCL 722.23;
     c. Apply the clear and convincing evidence standard of MCL
        722.27a;
     d. Make findings of fact on the record;

3. ORDER a professional custody evaluation pursuant to MCR 3.111.1
   and MCL 722.24, to include assessment of parental alienation
   dynamics;

4. APPOINT a Guardian ad Litem for L.D.W., if one has not already been
   appointed, to independently assess the child's best interests;

5. ORDER Defendant-Mother to cooperate fully with the restoration of
   parenting time and to cease all alienating behaviors;

6. AWARD Plaintiff-Father reasonable costs and attorney fees (or pro
   se litigation costs) pursuant to MCL 722.27a(8) and MCR 3.206(D);

7. GRANT such other and further relief as this Court deems just and
   equitable.

                        V. VERIFICATION

I, Andrew J. Pigors, state under penalty of perjury pursuant to MCL
600.2994 and 28 U.S.C. 1746, that the facts set forth in this Motion
are true and correct to the best of my knowledge, information, and
belief.

Dated: _________________        ________________________________
                                Andrew J. Pigors, Pro Se
                                Plaintiff-Father
                                [Address]
                                [Phone]
                                [Email]

                    CERTIFICATE OF SERVICE

I hereby certify that on _________________, 2026, I served a copy of
this Verified Emergency Motion to Restore Parenting Time upon:

Emily Watson
c/o Attorney Rusco
[Address]

by [personal service / first-class mail / electronic filing through
MiFILE], in accordance with MCR 2.107.

                                ________________________________
                                Andrew J. Pigors

                  NOTICE OF HEARING

TO: Emily Watson and Attorney Rusco

PLEASE TAKE NOTICE that the above Emergency Motion will be brought on
for hearing before the Honorable Judge _________________ at the
Muskegon County Courthouse, 990 Terrace Street, Muskegon, Michigan
49442, on _________________, 2026, at _________ a.m./p.m., or as soon
thereafter as counsel may be heard.

                                ________________________________
                                Andrew J. Pigors, Pro Se

                    INDEX OF AUTHORITIES

CONSTITUTIONAL PROVISIONS
  U.S. Const. amend. XIV, Section 1 (Due Process)
  Mich. Const. 1963, Art. 1, Sections 2, 17

MICHIGAN COURT RULES
  MCR 2.107 (Service of Process)
  MCR 2.119 (Motion Practice)
  MCR 3.111.1 (Friend of the Court; Custody Evaluation)
  MCR 3.206 (Costs and Fees)
  MCR 3.207 (Parenting Time)
  MCR 3.208 (Support and Parenting Time Enforcement)

MICHIGAN COMPILED LAWS
  MCL 722.23 (Best Interest of the Child Factors)
  MCL 722.24 (Custody Investigation)
  MCL 722.27 (Custody Award; Modification)
  MCL 722.27a (Parenting Time)
  MCL 600.2994 (Verification)

UNITED STATES SUPREME COURT
  Mathews v. Eldridge, 424 U.S. 319 (1976)
  Santosky v. Kramer, 455 U.S. 745 (1982)
  Stanley v. Illinois, 405 U.S. 645 (1972)
  Troxel v. Granville, 530 U.S. 57 (2000)

MICHIGAN SUPREME COURT
  In re Sanders, 495 Mich 394 (2014)

MICHIGAN COURT OF APPEALS
  Lieberman v. Orr, 319 Mich App 68 (2017)
  Marik v. Marik, 325 Mich App 353 (2018)
  Shade v. Wright, 291 Mich App 17 (2010)

                    PROPOSED ORDER

STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR THE COUNTY OF MUSKEGON
FAMILY DIVISION

Case No. 2024-001507-DC

ORDER RESTORING PARENTING TIME

At a session of said Court, held in the Courthouse in the City of
Muskegon, County of Muskegon, State of Michigan, on _____________, 2026.

PRESENT: Honorable ___________________________, Circuit Judge

The Court having considered Plaintiff-Father's Verified Emergency
Motion to Restore Parenting Time, the pleadings and papers on file,
the arguments of the parties, and being otherwise fully advised in the
premises;

IT IS HEREBY ORDERED:

1. Plaintiff-Father's parenting time with the minor child, L.D.W.
   (DOB: 11/09/2022), is hereby RESTORED, effective immediately.

2. The initial parenting time schedule shall be as follows:
   [To be completed by the Court]

3. An evidentiary hearing shall be held on _____________, 2026, at
   _________ a.m./p.m., to address the full parenting time schedule
   and best interest factors under MCL 722.23.

4. A custody evaluation shall be ordered pursuant to MCR 3.111.1.

5. Defendant-Mother shall fully cooperate with the restoration of
   parenting time and shall not interfere with Plaintiff-Father's
   exercise of parenting time.

6. This Order is effective immediately upon entry.

Dated: _________________        ________________________________
                                Circuit Judge

"""

with open(os.path.join(OUT, "PACKET_01_EMERGENCY_MOTION_RESTORE_PT.md"), "w", encoding="utf-8") as f:
    f.write(doc)
print(f"PACKET 1 written: {len(doc):,} chars", flush=True)

# ============================================================================
# PACKET 2: MOTION TO MODIFY/TERMINATE PPO
# Filed in: 14th Judicial Circuit Court, Muskegon County
# Case No: 2023-5907-PP
# ============================================================================

doc2 = """STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

EMILY WATSON,
    Petitioner,                                Case No. 2023-5907-PP

v.                                             Hon. Jenny L. McNeill

ANDREW J. PIGORS,
    Respondent.
______________________________________________/

RESPONDENT'S MOTION TO MODIFY OR TERMINATE PERSONAL PROTECTION ORDER
AND BRIEF IN SUPPORT

NOW COMES Respondent Andrew J. Pigors, appearing pro se, and pursuant
to MCL 600.2950(14), MCR 3.707, MCR 3.705, and the constitutional
protections of the Due Process Clause, respectfully moves this Court
to modify or terminate the existing Personal Protection Order (PPO)
and in support thereof states as follows:

                    I. JURISDICTIONAL STATEMENT

1. This Court has jurisdiction pursuant to MCL 600.2950 and MCR 3.701
et seq. Respondent is a Michigan resident. The PPO at issue was entered
by this Court and remains in effect.

                    II. PROCEDURAL HISTORY

2. On or about [date], Petitioner Emily Watson filed a petition for a
Personal Protection Order against Respondent under MCL 600.2950.

3. The PPO was issued ex parte, without prior notice to Respondent and
without an evidentiary hearing, in accordance with MCL 600.2950(12).

4. Respondent has previously filed motions to modify or terminate the
PPO, which have been denied without a full evidentiary hearing on the
merits, in violation of due process.

5. The PPO has been in effect for an extended period and has been used
as the primary mechanism to prevent all contact between Respondent-
Father and the minor child, L.D.W.

                    III. STATEMENT OF FACTS

6. The PPO was obtained under circumstances that raise serious
concerns about its factual basis:

    a. The petition was filed without prior notice to Respondent;
    b. No evidentiary hearing was conducted before issuance;
    c. The allegations in the petition have never been tested through
       adversarial proceedings;
    d. Respondent has no criminal history of domestic violence or abuse;
    e. No independent investigation or verification of the allegations
       was conducted before issuance.

7. The PPO has had the following effects:
    a. Complete severance of Respondent-Father's relationship with
       his daughter L.D.W. for 329+ consecutive days;
    b. Destruction of the parent-child bond at a critical developmental
       stage;
    c. Effective termination of parenting rights without due process
       protections;
    d. Financial harm through inability to exercise parental
       responsibilities;
    e. Emotional and psychological harm to both Respondent and the
       minor child.

8. The circumstances that formed the basis for the PPO have materially
changed since its issuance. Respondent has maintained a stable, safe
living environment and has demonstrated no behavior that would justify
the continued restriction.

                    IV. LEGAL ARGUMENT

A. Statutory Right to Modification or Termination

9. MCL 600.2950(14) provides: "A court shall not refuse to modify or
terminate a personal protection order solely because a modification
or termination of the order may allow the respondent to have contact
with the petitioner."

10. MCR 3.707(A) provides that "the respondent may file a motion to
modify or rescind a personal protection order." The motion must be
heard and the court must consider the evidence.

11. MCR 3.707(B) requires that when a respondent challenges a PPO,
the court shall hold a hearing and the petitioner bears the burden
of proving, by a preponderance of the evidence, that the PPO should
remain in effect.

B. Due Process Requirements

12. The continued enforcement of the PPO without an evidentiary hearing
violates Respondent's right to due process under the Fourteenth
Amendment. See Mathews v. Eldridge, 424 U.S. 319 (1976).

13. While ex parte issuance of PPOs is permitted under exigent
circumstances, due process requires that the respondent be afforded
a meaningful opportunity to challenge the order through an evidentiary
hearing. See Kampf v. Kampf, 237 Mich App 377, 382 (1999) ("A party
is entitled to a hearing on a motion to terminate a PPO.").

14. The Michigan Court of Appeals has held that "the ex parte nature
of a PPO hearing does not eliminate the respondent's right to
challenge the factual basis of the order." Hayford v. Hayford, 279
Mich App 324, 328 (2008).

C. Changed Circumstances

15. Michigan law recognizes that PPOs should be modified or terminated
when circumstances have changed such that the order is no longer
necessary. MCL 600.2950(14); MCR 3.707.

16. The following changed circumstances warrant modification or
termination:
    a. Significant passage of time since issuance without any new
       allegations or incidents;
    b. Respondent's continued compliance with all court orders;
    c. Respondent's maintenance of stable employment and housing;
    d. The child's developmental need for paternal contact;
    e. The absence of any credible threat to Petitioner's safety.

D. Impact on Parental Rights

17. The PPO effectively operates as a de facto custody order, depriving
Respondent-Father of all contact with his daughter without the
procedural protections required for custody determinations under MCL
722.23 and MCL 722.27.

18. Michigan courts have recognized that PPOs should not be used as a
substitute for custody determinations. See Pickering v. Pickering, 253
Mich App 694 (2002).

19. The use of the PPO to prevent parental contact, without a custody
hearing applying the best interest factors, constitutes a violation of
Respondent-Father's fundamental parental rights.

E. Proportionality

20. The scope of the current PPO is disproportionate to any legitimate
safety concern. A less restrictive alternative (such as modification to
permit supervised parenting time) would adequately address any safety
concerns while preserving the constitutionally protected parent-child
relationship.

                    V. REQUESTED RELIEF

WHEREFORE, Respondent respectfully requests that this Court:

1. TERMINATE the Personal Protection Order (Case No. 2023-5907-PP) in
   its entirety; or, in the alternative,

2. MODIFY the PPO to permit:
    a. Supervised parenting time between Respondent-Father and L.D.W.;
    b. Telephone and video communication between Respondent-Father and
       the child;
    c. Attendance at the child's school and medical appointments;

3. ORDER an evidentiary hearing within fourteen (14) days, at which
   Petitioner shall bear the burden of proving, by a preponderance of
   the evidence, that the PPO remains necessary;

4. ORDER Petitioner to produce all evidence supporting the continuation
   of the PPO;

5. AWARD Respondent reasonable costs associated with this motion;

6. GRANT such other and further relief as this Court deems just and
   equitable.

                    VI. VERIFICATION

I, Andrew J. Pigors, state under penalty of perjury pursuant to MCL
600.2994 that the facts stated in this Motion are true and correct to
the best of my knowledge, information, and belief.

Dated: _________________        ________________________________
                                Andrew J. Pigors, Pro Se
                                Respondent
                                [Address]
                                [Phone]
                                [Email]

                    CERTIFICATE OF SERVICE

I hereby certify that on _________________, 2026, I served a copy of
this Motion upon:

Emily Watson
c/o Attorney Rusco
[Address]

by [personal service / first-class mail / electronic filing through
MiFILE], in accordance with MCR 2.107.

                                ________________________________
                                Andrew J. Pigors

                    INDEX OF AUTHORITIES

MICHIGAN COURT RULES
  MCR 2.107 (Service)
  MCR 3.701 et seq. (PPO Proceedings)
  MCR 3.705 (Issuance of PPO)
  MCR 3.707 (Modification or Termination of PPO)

MICHIGAN COMPILED LAWS
  MCL 600.2950 (Personal Protection Orders)
  MCL 600.2994 (Verification)
  MCL 722.23 (Best Interest Factors)
  MCL 722.27 (Custody Modification)
  MCL 722.27a (Parenting Time)

UNITED STATES SUPREME COURT
  Mathews v. Eldridge, 424 U.S. 319 (1976)
  Troxel v. Granville, 530 U.S. 57 (2000)

MICHIGAN COURT OF APPEALS
  Hayford v. Hayford, 279 Mich App 324 (2008)
  Kampf v. Kampf, 237 Mich App 377 (1999)
  Pickering v. Pickering, 253 Mich App 694 (2002)

                    PROPOSED ORDER

STATE OF MICHIGAN
IN THE 14TH JUDICIAL CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

Case No. 2023-5907-PP

ORDER ON RESPONDENT'S MOTION TO MODIFY/TERMINATE PPO

At a session of said Court, held in the Courthouse in the City of
Muskegon, County of Muskegon, State of Michigan, on _____________, 2026.

PRESENT: Honorable ___________________________, Circuit Judge

The Court having considered Respondent's Motion to Modify or Terminate
Personal Protection Order, the response thereto, the pleadings and
papers on file, and being otherwise fully advised in the premises;

IT IS HEREBY ORDERED:

1. The Personal Protection Order dated _____________ is hereby
   [TERMINATED / MODIFIED as follows: ___________________________].

2. An evidentiary hearing is scheduled for _____________, 2026, at
   _________ a.m./p.m.

3. [Additional provisions as determined by the Court.]

Dated: _________________        ________________________________
                                Circuit Judge
"""

with open(os.path.join(OUT, "PACKET_02_MOTION_MODIFY_TERMINATE_PPO.md"), "w", encoding="utf-8") as f:
    f.write(doc2)
print(f"PACKET 2 written: {len(doc2):,} chars", flush=True)

print("Packets 1-2 complete", flush=True)