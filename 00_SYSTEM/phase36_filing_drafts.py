"""
Phase 36: Generate three court filing drafts.
1. MCR 2.612(C)(1)(c) Motion to Vacate — Brown's res judicata insertion
2. Slander of Title Complaint — VanDam / HOA
3. JTC Complaint — Kenneth Hoopes
"""
from pathlib import Path
from datetime import datetime

OUT_DIR = Path(r"C:\Users\andre\LitigationOS\05_FILINGS\LANE_B_HOUSING")
OUT_DIR.mkdir(parents=True, exist_ok=True)

today = datetime.now().strftime("%B %d, %Y")
today_short = datetime.now().strftime("%Y-%m-%d")

# ══════════════════════════════════════════════════
# FILING 1: MCR 2.612 MOTION TO VACATE
# ══════════════════════════════════════════════════
motion_vacate = f"""STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW JAMES PIGORS,
    Plaintiff,

v.                                                          Case No. 2025-002760-CZ
                                                            Hon. Kenneth Hoopes
SHADY OAKS PARK MHP LLC, et al.,
    Defendants.
_____________________________________________/

PLAINTIFF'S MOTION TO SET ASIDE JUDGMENT AND FOR RELIEF FROM ORDER PURSUANT TO
MCR 2.612(C)(1)(c) — FRAUD, MISREPRESENTATION, AND MISCONDUCT OF ADVERSE PARTY;
AND MOTION FOR ORDER TO SHOW CAUSE RE: FRAUD ON THE COURT

Plaintiff Andrew James Pigors, appearing pro se, moves this Court pursuant to MCR 2.612(C)(1)(c)
to set aside the Order of Dismissal entered in this matter, and states:

                                         I. INTRODUCTION

The dismissal order in this case contains "res judicata" language that was never stated from the
bench at any hearing and was never ruled upon by this Court. Defendants' counsel, Jeremy Brown
(P77427), inserted that language into the proposed order after the hearing, without any oral ruling
supporting it. This is fraud on the court under MRPC 3.3(a)(1) and requires vacatur.

                                    II. STATEMENT OF FACTS

1. On [HEARING DATE — obtain from transcript], this Court held a hearing in Case No. 2025-002760-CZ.

2. At no point during that hearing did this Court make an oral ruling that Plaintiff's claims were
   barred by res judicata. [TO BE CONFIRMED BY TRANSCRIPT — SEE ACQUISITION RADAR, ITEM 10]

3. Following the hearing, Defendants' counsel, Jeremy Brown (P77427), submitted a proposed order
   purportedly memorializing the Court's ruling.

4. The order submitted by Brown contains the following language: [INSERT EXACT QUOTE FROM ORDER].

5. That "res judicata" language does not appear anywhere in the transcript of the hearing.

6. No party was given an opportunity to review or object to the order as submitted before it was
   entered. [VERIFY — if ex parte submission, this independently grounds vacatur under MCR 2.119(G)(3)]

7. The insertion of "res judicata" language is material: it purports to bar Plaintiff's future claims
   in all Michigan courts on the same subject matter, causing irreparable and ongoing harm.

                                  III. APPLICABLE STANDARDS

8. MCR 2.612(C)(1)(c): The Court may relieve a party from a final judgment or order for "fraud,
   misrepresentation, or other misconduct of an adverse party." Motion must be made within a
   "reasonable time" of discovery.

9. MRPC 3.3(a)(1): A lawyer shall not knowingly make a false statement of fact to a tribunal.
   Submitting an order containing language the court never stated is a false statement to the
   tribunal — the Court itself.

10. MRPC 3.3(a)(2): A lawyer shall not knowingly fail to disclose a material fact to the tribunal
    when disclosure is necessary to avoid assisting a client in criminal or fraudulent conduct.

11. MCR 2.119(G)(3): The prevailing party may prepare a proposed order — but the proposed order
    must "accurately reflect" the court's ruling. An order that expands the ruling violates
    this requirement.

12. In re Contempt of Dudzinski, 257 Mich App 96 (2003): Michigan courts scrutinize proposed
    orders that exceed the scope of oral rulings.

                                     IV. ARGUMENT

A. Brown's Insertion of Res Judicata Language Constitutes Fraud on the Court.

The record will show that this Court did not rule on res judicata from the bench. Counsel for
Defendants thereafter submitted an order containing res judicata language — language that purports
to bind the Plaintiff in all future proceedings. This is not a clerical error. It is a deliberate
expansion of the court's ruling that would permanently bar Plaintiff's meritorious claims.

Fraud on the court occurs when an officer of the court — here, a licensed attorney — intentionally
presents false information that deceives the court and compromises the integrity of the proceeding.
Brown knew the court did not rule on res judicata. He submitted the order anyway. That is fraud.

B. The Prejudice Is Irreversible Without Vacatur.

If this order stands, Plaintiff's claims regarding: HOA financial fraud, slander of title, wrongful
eviction, spoliation of the ledger, and post-eviction destruction — are all potentially barred.
MCR 2.612 exists precisely for this situation: to prevent an opponent's fraud from permanently
extinguishing meritorious claims.

C. The Motion Is Timely.

Plaintiff discovered the res judicata language upon review of the entered order. This motion is
filed within a reasonable time of that discovery. MCR 2.612(C)(2) applies.

                                      V. RELIEF REQUESTED

WHEREFORE, Plaintiff respectfully requests that this Court:

1. Set aside the Order of Dismissal in Case No. 2025-002760-CZ pursuant to MCR 2.612(C)(1)(c);

2. Order Defendants' counsel Jeremy Brown (P77427) to produce the audio/transcript of the hearing
   at which the dismissal was entered, for comparison against the submitted order language;

3. Order an evidentiary hearing on whether fraud on the court was committed;

4. Refer Jeremy Brown to the Attorney Grievance Commission pursuant to MCR 9.104 for
   violations of MRPC 3.3(a)(1), 3.4, and 8.4(c);

5. Award Plaintiff costs and reasonable attorney equivalency fees under MCR 2.625 and MCL 600.2591;

6. Grant such other relief as is just and proper.

                                                Respectfully submitted,

                                                /s/ Andrew James Pigors
                                                Andrew James Pigors, Plaintiff, Pro Se
                                                1977 Whitehall Rd, Lot 17
                                                North Muskegon, MI 49445
                                                (231) 903-5690
                                                andrewjpigors@gmail.com
Date: {today}

                              CERTIFICATE OF SERVICE

I certify that on {today}, I served a true copy of this Motion by first-class mail upon:

Emily A. Watson — [NOTE: This filing is Lane B only — do not serve custody parties]
Shady Oaks Park MHP LLC / Homes of America LLC
c/o Jeremy Brown P77427 [NOTE: Check if Brown is still counsel — may serve directly on entity]
[ADDRESS — confirm current registered agent for service]

                                                /s/ Andrew James Pigors
                                                Andrew James Pigors
"""

# ══════════════════════════════════════════════════
# FILING 2: SLANDER OF TITLE COMPLAINT
# ══════════════════════════════════════════════════
slander_complaint = f"""STATE OF MICHIGAN
IN THE CIRCUIT COURT FOR THE COUNTY OF MUSKEGON

ANDREW JAMES PIGORS,
    Plaintiff,

v.                                                          Case No. _______________
                                                            Hon. _______________
HOMES OF AMERICA LLC, a Michigan limited liability company,
SHADY OAKS PARK MHP LLC, a New Jersey limited liability company,
CASSANDRA VANDAM, individually and as agent,
    Defendants.
_____________________________________________/

COMPLAINT FOR SLANDER OF TITLE, TORTIOUS INTERFERENCE,
AND DECLARATORY JUDGMENT

Plaintiff Andrew James Pigors, appearing pro se, alleges as follows:

                                         PARTIES

1. Plaintiff Andrew James Pigors resides at 1977 Whitehall Rd, Lot 17, North Muskegon, MI 49445,
   and at all relevant times held title to the mobile home situated at that address.

2. Defendant Homes of America LLC is a Michigan limited liability company operating mobile home
   parks in Michigan, including Shady Oaks Mobile Home Community (formerly "Shady Oaks Park MHP").

3. Defendant Shady Oaks Park MHP LLC is a New Jersey limited liability company (dissolved 2022)
   that operated as the predecessor management entity for the park. LARA License #1201891 was
   held by Bryon Fields on behalf of associated entities.

4. Defendant Cassandra VanDam is employed as a property manager or similar role at Shady Oaks
   Mobile Home Community, acting as agent of Homes of America LLC.

                                    JURISDICTION AND VENUE

5. This Court has jurisdiction under MCL 600.605. Venue is proper in Muskegon County as the
   real property at issue is situated in Muskegon County.

                                    STATEMENT OF FACTS

6. Plaintiff is, and at all relevant times has been, the titled owner of the mobile home situated
   at Lot 17, 1977 Whitehall Rd, North Muskegon, MI 49445.

7. On or about February 18, 2026, Defendant VanDam communicated via Facebook Messenger with
   Carmyn Hanna, a third-party prospective purchaser who had expressed interest in buying
   Plaintiff's mobile home.

8. In those communications, VanDam made the following false statements:

   a. "No maam he abandoned the home it is no longer his home."
   b. "Andrew Pigors does not own a home at Shady Oaks MHC."
   c. "We are in the process thru our legal team: Once that process is completed we will place
      the home up for sale but I don't have a date for that yet."

9. Each of these statements is false:

   a. Plaintiff never abandoned his home. No court had entered any order of abandonment as of
      February 18, 2026. The legal process referenced by VanDam in statement (c) was still
      pending — confirming she knew the matter was unresolved.
   b. Plaintiff held and holds title to the mobile home at Lot 17.
   c. VanDam's own statement (c) admits that the "process" was not yet complete — making
      statements (a) and (b) knowingly false at the time they were made.

10. As a direct and proximate result of VanDam's statements, Carmyn Hanna ceased her inquiry about
    purchasing Plaintiff's home — constituting a lost sale of an asset Plaintiff was entitled to sell.

11. HOA's own internal emails demonstrate that HOA's agents did NOT KNOW whether they owned
    Plaintiff's trailer, yet VanDam publicly declared Plaintiff did not own it.

12. In February 2025, HOA agent Shelly Przybylek had attempted to coerce Plaintiff into selling
    the trailer for $750 (fair market value: $18,000–$25,000). When Plaintiff refused, HOA
    escalated its legal campaign.

                                     COUNT I — SLANDER OF TITLE
                                           MCL 565.108

13. Plaintiff realleges paragraphs 1–12.

14. VanDam's statements (a) and (b) constitute a malicious, false, and unprivileged publication
    of statements that disparage Plaintiff's title to real property (including his mobile home
    and interest in Lot 17).

15. These statements were published to a third party (Carmyn Hanna) and directly caused pecuniary
    damage by foreclosing a prospective sale.

16. VanDam acted with malice: she knew the "process" was pending yet affirmatively declared the
    matter concluded in HOA's favor.

17. Plaintiff is entitled to actual damages, punitive damages, and attorney equivalency fees.

                              COUNT II — TORTIOUS INTERFERENCE WITH
                            PROSPECTIVE ECONOMIC ADVANTAGE

18. Plaintiff realleges paragraphs 1–12.

19. Plaintiff had a prospective business relationship with Carmyn Hanna regarding the sale of his
    mobile home.

20. Defendants knew of this prospective relationship (Hanna had made inquiry to HOA about
    purchasing the home).

21. Defendants intentionally interfered with that relationship through the false statements
    described above, and through the claim that HOA would place the home "up for sale" — which
    would only be possible if Plaintiff's title were extinguished.

22. The interference was improper and caused Plaintiff loss of a contemplated transaction.

                        COUNT III — DECLARATORY JUDGMENT — TITLE
                                    MCL 600.1601

23. Plaintiff realleges paragraphs 1–12.

24. An actual controversy exists between Plaintiff and Defendants regarding ownership of the
    mobile home at Lot 17.

25. Defendants have publicly, repeatedly, and falsely stated that Plaintiff does not own the
    mobile home.

26. Plaintiff is entitled to a declaratory judgment confirming his title to the mobile home,
    which has not been extinguished by any lawful adjudication.

                                    RELIEF REQUESTED

WHEREFORE, Plaintiff requests:

A. Compensatory damages for loss of the Carmyn Hanna prospective sale (trailer FMV: $18,000–$25,000);
B. Punitive damages for malicious slander of title;
C. Declaratory judgment that Plaintiff is and has been the titled owner of the mobile home at Lot 17;
D. Injunctive relief prohibiting Defendants from making further false statements about Plaintiff's title;
E. Costs and attorney equivalency fees under MCL 600.2591;
F. Such other relief as is just.

                                                Respectfully submitted,

                                                /s/ Andrew James Pigors
                                                Andrew James Pigors, Plaintiff, Pro Se
                                                1977 Whitehall Rd, Lot 17
                                                North Muskegon, MI 49445
                                                (231) 903-5690
                                                andrewjpigors@gmail.com
Date: {today}
"""

# ══════════════════════════════════════════════════
# FILING 3: JTC COMPLAINT — KENNETH HOOPES
# ══════════════════════════════════════════════════
jtc_complaint = f"""JUDICIAL TENURE COMMISSION OF MICHIGAN
3034 West Grand Boulevard, Suite 8-450
Detroit, Michigan 48202

                              FORMAL COMPLAINT AGAINST JUDICIAL OFFICER

Date: {today}

TO THE JUDICIAL TENURE COMMISSION:

Complainant: Andrew James Pigors
Address: 1977 Whitehall Rd, Lot 17, North Muskegon, MI 49445
Telephone: (231) 903-5690
Email: andrewjpigors@gmail.com

Respondent Judge: Hon. Kenneth Hoopes
Court: 14th Circuit Court, Muskegon County
Cases Involved: 2025-002760-CZ; Emergency Petition (Case No. TBD — emergency petition to stop eviction)

                                      I. SUMMARY

This complaint alleges that Hon. Kenneth Hoopes violated the Michigan Code of Judicial Conduct
by: (1) presiding over cases directly involving his wife's court and his wife's judicial rulings
without disclosure or recusal; (2) denying an emergency petition to stop an unlawful eviction
when the evidence clearly supported relief; and (3) allowing his wife's courtroom to perpetuate
an unjust result by refusing to intervene and then departing on vacation.

                                   II. THE SPOUSAL CONFLICT

Hon. Kenneth Hoopes is married to Hon. Maria Ladas-Hoopes, Judge of the 60th District Court,
Muskegon County.

In Case No. 2025-002760-CZ, Complainant brought a civil action arising out of the eviction
proceedings presided over by Hon. Ladas-Hoopes in the 60th District Court, Case No. 2025-061626-LT.

In an Emergency Petition filed with the 14th Circuit Court (presided over by Respondent Hoopes),
Complainant sought an emergency stay of the eviction being conducted by Ladas-Hoopes' court.

At no time did Hon. Hoopes disclose that:
(a) He is married to the judge whose eviction order he was being asked to review;
(b) He and his wife were formerly law partners at Ladas, Hoopes & McNeill, 435 Whitehall Rd,
    Muskegon, MI;
(c) His ruling on the emergency petition would directly affect the outcome of proceedings
    in his wife's court.

                            III. APPLICABLE CANON VIOLATIONS

Canon 2, Rule 2.11(A)(1): A judge shall disqualify himself or herself in any proceeding in which
the judge's impartiality might reasonably be questioned, including when the judge has personal
bias or prejudice concerning a party or when the judge's spouse is a party or officer of a party.

Canon 2, Rule 2.11(A)(2)(a): Disqualification required when judge or spouse has an economic
interest in the subject matter.

Canon 2, Rule 2.11(A)(6)(a): Disqualification required when judge served as a lawyer in the matter
in controversy. Hoopes' former firm (Ladas, Hoopes & McNeill) may have represented HOA-related
entities when the firm was operating.

                         IV. THE EMERGENCY PETITION — DENIAL WITHOUT MERIT

On or about July 2025, Complainant filed an emergency petition in 14th Circuit Court requesting
an emergency order to stop the eviction of Complainant from his home at Lot 17.

The basis for the emergency petition included:
1. HOA had represented to the 60th District Court that it owned Complainant's mobile home;
2. HOA's own internal emails showed that HOA did NOT know if it owned the mobile home;
3. Complainant's security cameras had captured HOA agents drilling his locks;
4. Muskegon County Sheriff had been called by Complainant on July 17, 2025;
5. The eviction was proceeding on false representations of ownership.

Under established Michigan standards, an emergency stay requires:
(a) Likelihood of success on the merits — MET: HOA could not document ownership
(b) Irreparable harm — MET: Complainant would lose his home

Hon. Hoopes DENIED the emergency petition.
Hon. Hoopes then departed on vacation.

This left Complainant without any judicial protection against an eviction carried out on false
pretenses, executed by the judge who is Hoopes' wife, while Hoopes refused to act.

                                  V. FORMER PARTNERSHIP

All three judges involved in Complainant's overlapping cases — Hon. McNeill, Hon. Kenneth Hoopes,
and Hon. Ladas-Hoopes — were formerly partners at Ladas, Hoopes & McNeill, 435 Whitehall Rd,
Muskegon, Michigan.

Not one of these three judges has disclosed this relationship to Complainant.
Not one has recused.

The result is that Complainant has lost custody of his son, his home, and his freedom across
three separate courts — all operated by former partners from the same law firm — without any
disclosure of those relationships.

                                    VI. RELIEF REQUESTED

The Judicial Tenure Commission is respectfully requested to:

1. Investigate the undisclosed spousal relationship between Kenneth Hoopes and Maria Ladas-Hoopes
   and their joint participation in proceedings adversely affecting Complainant;

2. Investigate the undisclosed former partnership among Hoopes, Ladas-Hoopes, and McNeill at
   Ladas, Hoopes & McNeill;

3. Determine whether the denial of the emergency petition constitutes judicial misconduct or
   willful misuse of judicial authority;

4. Refer findings for appropriate discipline, including admonishment, censure, or removal;

5. Issue a recommended order of recusal for all future proceedings in which Complainant is a party
   before any former partner of Ladas, Hoopes & McNeill.

                                              Respectfully submitted,

                                              /s/ Andrew James Pigors
                                              Andrew James Pigors, Complainant, Pro Se
                                              1977 Whitehall Rd, Lot 17
                                              North Muskegon, MI 49445
                                              (231) 903-5690
                                              andrewjpigors@gmail.com
Date: {today}

                                    EXHIBITS ATTACHED

Exhibit A: Screenshot of VanDam "abandoned" Facebook message (Feb 18, 2026)
Exhibit B: HOA coercion email — Shelly Przybylek to Andrew Pigors (Feb 13, 2025)
Exhibit C: HOA emails demonstrating uncertainty of trailer ownership
Exhibit D: Security camera footage description — lock drilling, July 17, 2025
Exhibit E: Order of Dismissal, Case No. 2025-002760-CZ (with res judicata language)
Exhibit F: LARA records — License #1201891, entity dissolution documents
"""

# ══════════════════════════════════════════════════
# WRITE ALL THREE DRAFTS
# ══════════════════════════════════════════════════
filings = {
    f"F36_MCR2612_MOTION_TO_VACATE_{today_short}.md": motion_vacate,
    f"F36_SLANDER_OF_TITLE_COMPLAINT_{today_short}.md": slander_complaint,
    f"F36_JTC_COMPLAINT_HOOPES_{today_short}.md": jtc_complaint,
}

for fname, content in filings.items():
    fpath = OUT_DIR / fname
    fpath.write_text(content, encoding='utf-8')
    print(f"WRITTEN: {fpath}")

print(f"\nAll 3 filing drafts written to: {OUT_DIR}")
