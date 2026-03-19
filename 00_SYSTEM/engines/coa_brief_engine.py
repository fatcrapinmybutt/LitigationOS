#!/usr/bin/env python3
"""
ENGINE 1: COA BRIEF DRAFTING ENGINE
Auto-generates Michigan Court of Appeals brief sections from DB intelligence.
Outputs substantive legal argument paragraphs, not just templates.
Case 366810 — Deadline April 15, 2026
"""
import sqlite3
import os
from datetime import datetime, date

db_path = r'C:\Users\andre\LitigationOS\litigation_context.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 70)
print("  COA BRIEF DRAFTING ENGINE v1.0")
print("  Case No. 366810 — Michigan Court of Appeals")
print("=" * 70)

today = date.today()
deadline = date(2026, 4, 15)
days_left = (deadline - today).days
suspension_start = date(2025, 8, 8)
days_suspended = (today - suspension_start).days
last_pt = date(2025, 7, 29)
days_no_contact = (today - last_pt).days

# Gather intelligence from DB
c.execute("SELECT COUNT(*) FROM judicial_violations")
jv_count = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM constitutional_violations")
cv_count = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM rebuttal_matrix")
rb_count = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM psych_analysis_results WHERE pattern_category='MANIPULATION'")
manip_count = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM appclose_messages")
msg_count = c.fetchone()[0]

# Get constitutional violations for argument sections
c.execute("""SELECT amendment, clause, violation_type, description, controlling_caselaw, michigan_authority 
FROM constitutional_violations ORDER BY amendment, clause""")
const_violations = c.fetchall()

# Get top rebuttal entries
c.execute("""SELECT assertion_category, COUNT(*), GROUP_CONCAT(DISTINCT tort_cause) 
FROM rebuttal_matrix GROUP BY assertion_category ORDER BY COUNT(*) DESC LIMIT 10""")
rebuttal_summary = c.fetchall()

# Get damages
c.execute("SELECT SUM(amount) FROM damages_itemization WHERE amount > 0")
total_damages = c.fetchone()[0] or 0

brief_path = r'C:\Users\andre\LitigationOS\04_COURT_FILINGS\COA_BRIEF_DRAFT.md'
with open(brief_path, 'w', encoding='utf-8') as f:
    # ================================================================
    # COVER PAGE
    # ================================================================
    f.write("# IN THE MICHIGAN COURT OF APPEALS\n\n")
    f.write("**Case No. 366810**\n\n")
    f.write("---\n\n")
    f.write("**ANDREW J. PIGORS,**\n")
    f.write("Plaintiff-Appellant,\n\n")
    f.write("v.\n\n")
    f.write("**TIFFANY EMILY WATSON (fka PIGORS),**\n")
    f.write("Defendant-Appellee.\n\n")
    f.write("---\n\n")
    f.write("**Appeal from the 14th Judicial Circuit Court**\n")
    f.write("**Muskegon County, Michigan**\n")
    f.write("**Case No. 2024-001507-DC**\n")
    f.write("**Hon. Jenny L. McNeill, Presiding**\n\n")
    f.write("---\n\n")
    f.write("# APPELLANT'S BRIEF ON APPEAL\n\n")
    f.write("---\n\n")
    f.write("**Andrew J. Pigors, Pro Se**\n")
    f.write("1977 Whitehall Rd, Lot 17\n")
    f.write("Laketon Township, MI 49445\n")
    f.write("(231) 903-5690\n\n")
    f.write(f"**Filed:** [Date]\n\n")
    f.write("---\n\n")

    # ================================================================
    # TABLE OF CONTENTS
    # ================================================================
    f.write("## TABLE OF CONTENTS\n\n")
    sections = [
        "I. Statement of Jurisdiction",
        "II. Statement of Questions Presented",
        "III. Statement of Facts",
        "IV. Standard of Review",
        "V. Argument",
        "   A. The Trial Court Violated Appellant's Procedural Due Process Rights",
        "   B. The Trial Court Violated Appellant's Substantive Due Process Rights",
        "   C. The Trial Court's Ex Parte Orders Were Based on Illegally Obtained Evidence",
        "   D. The Trial Court Exhibited Systematic Judicial Bias Requiring Reversal",
        "   E. The Trial Court Failed to Apply the Best Interest Factors Under MCL 722.23",
        "   F. The Trial Court's Orders Constitute an Abuse of Discretion",
        "VI. Relief Requested",
    ]
    for s in sections:
        f.write(f"- {s}\n")
    f.write("\n---\n\n")

    # ================================================================
    # TABLE OF AUTHORITIES
    # ================================================================
    f.write("## TABLE OF AUTHORITIES\n\n")
    f.write("### Federal Cases\n\n")
    federal_cases = [
        "Mathews v. Eldridge, 424 U.S. 319 (1976)",
        "Troxel v. Granville, 530 U.S. 57 (2000)",
        "Santosky v. Kramer, 455 U.S. 745 (1982)",
        "Turner v. Rogers, 564 U.S. 431 (2011)",
        "Fuentes v. Shevin, 407 U.S. 67 (1972)",
        "Caperton v. A.T. Massey Coal Co., 556 U.S. 868 (2009)",
        "Ward v. Village of Monroeville, 409 U.S. 57 (1972)",
        "Mapp v. Ohio, 367 U.S. 643 (1961)",
        "Wong Sun v. United States, 371 U.S. 471 (1963)",
        "Craig v. Boren, 429 U.S. 190 (1976)",
        "Goldberg v. Kelly, 397 U.S. 254 (1970)",
    ]
    for case in federal_cases:
        f.write(f"- {case}\n")
    
    f.write("\n### Michigan Cases\n\n")
    mi_cases = [
        "In re Rood, 483 Mich 73 (2009)",
        "In re Sanders, 495 Mich 394 (2014)",
        "People v. Beavers, 393 Mich 554 (1975)",
        "Vodvarka v. Grasmeyer, 259 Mich App 499 (2003)",
        "Berger v. Berger, 277 Mich App 700 (2008)",
        "Fletcher v. Fletcher, 447 Mich 871 (1994)",
        "Grew v. Knox, 265 Mich App 333 (2005)",
        "Brown v. Loveman, 260 Mich App 576 (2004)",
    ]
    for case in mi_cases:
        f.write(f"- {case}\n")
    
    f.write("\n### Statutes and Court Rules\n\n")
    statutes = [
        "MCL 722.23 — Best Interest of the Child Factors",
        "MCL 722.27a — Parenting Time",
        "MCL 750.539c — Eavesdropping (Felony)",
        "MCR 2.003 — Disqualification of Judge",
        "MCR 3.207 — Interim Orders in Domestic Relations",
        "MCR 7.212 — Briefs in Court of Appeals",
        "U.S. Const. amend. XIV — Due Process and Equal Protection",
        "U.S. Const. amend. I — Freedom of Speech and Petition",
        "Mich. Const. 1963, art. 1, §§ 3, 5, 11, 17, 20",
        "MCJC Canons 1, 2, 3 — Judicial Conduct",
    ]
    for s in statutes:
        f.write(f"- {s}\n")
    f.write("\n---\n\n")

    # ================================================================
    # I. JURISDICTION
    # ================================================================
    f.write("## I. STATEMENT OF JURISDICTION\n\n")
    f.write("This Court has jurisdiction pursuant to MCL 600.308 and MCR 7.203(A). ")
    f.write("Appellant timely filed a claim of appeal from the 14th Judicial Circuit Court, ")
    f.write("Muskegon County, Case No. 2024-001507-DC, challenging orders that terminated ")
    f.write("Appellant's parenting time and resulted in his incarceration for a cumulative ")
    f.write("59+ days. The orders below constitute final orders affecting substantial rights ")
    f.write("under MCR 7.202(6)(a)(iv).\n\n")
    f.write("---\n\n")

    # ================================================================
    # II. QUESTIONS PRESENTED
    # ================================================================
    f.write("## II. STATEMENT OF QUESTIONS PRESENTED\n\n")
    questions = [
        "Whether the trial court violated Appellant's procedural due process rights under the Fourteenth Amendment by suspending all parenting time via ex parte order without notice or meaningful hearing, where the underlying ex parte order was based on an illegal recording made in violation of MCL 750.539c?",
        "Whether the trial court violated Appellant's substantive due process right to parent his child by terminating all contact for 217+ days despite a NEGATIVE drug screen, a psychological evaluation returning ALL ZEROS, and nine police investigations yielding ZERO findings of wrongdoing?",
        "Whether the trial court's pattern of 52 ex parte orders — granted at a 44% rate with 100% favoring Defendant-Appellee — constitutes judicial bias requiring disqualification under MCR 2.003(C)(1) and reversal of all orders entered during the period of bias?",
        "Whether the trial court abused its discretion by failing to make findings under the best interest factors of MCL 722.23 before ordering the most extreme remedy of complete parenting time termination?",
        "Whether the trial court's ex parte communication with the HealthWest evaluator, resulting in a changed evaluation from ALL ZEROS to 'Rule Out,' constitutes grounds for reversal?",
    ]
    for i, q in enumerate(questions, 1):
        f.write(f"**{i}.** {q}\n\n")
        f.write("**Appellant answers:** Yes.\n\n")
    f.write("---\n\n")

    # ================================================================
    # III. STATEMENT OF FACTS
    # ================================================================
    f.write("## III. STATEMENT OF FACTS\n\n")
    f.write("### A. Background\n\n")
    f.write("Appellant Andrew J. Pigors (\"Father\") and Defendant-Appellee Tiffany Emily Watson ")
    f.write("(\"Mother\") are the parents of Lincoln D. Watson, born November 9, 2022. ")
    f.write("The underlying domestic relations case, No. 2024-001507-DC, was filed in the ")
    f.write("14th Judicial Circuit Court, Muskegon County, with the Honorable Jenny L. McNeill presiding.\n\n")
    
    f.write("Mother has been employed for nine years at the Kent County Prosecutor's Office, ")
    f.write("Family Court Division, giving her extensive familiarity with family court procedures, ")
    f.write("judges, and legal strategies — a significant advantage over Father, who proceeds pro se.\n\n")

    f.write("### B. The Premeditated Ex Parte Scheme\n\n")
    f.write("On August 7, 2025, Albert Watson — a member of Mother's family — stated: ")
    f.write("*\"they want this documented so Emily can go tomorrow to get an Ex Parte order.\"* ")
    f.write("This admission constitutes direct evidence that the August 8, 2025 ex parte order ")
    f.write("was premeditated and strategically timed, not the product of genuine emergency.\n\n")
    
    f.write("The ex parte motion relied upon a recording made by Lori Watson in violation of ")
    f.write("Michigan's eavesdropping statute, MCL 750.539c — a felony punishable by up to two years' ")
    f.write("imprisonment. This illegally obtained evidence should have been excluded under the fruit ")
    f.write("of the poisonous tree doctrine. *Wong Sun v. United States*, 371 U.S. 471 (1963); ")
    f.write("*People v. Beavers*, 393 Mich 554 (1975).\n\n")

    f.write("### C. Suspension Without Basis\n\n")
    f.write(f"On August 8, 2025, Judge McNeill suspended all parenting time. Father's last contact ")
    f.write(f"with Lincoln was July 29, 2025 — now {days_no_contact} days ago. The suspension was imposed ")
    f.write("despite the following exculpatory evidence:\n\n")
    f.write("- **Drug Screen:** NEGATIVE — no substances detected\n")
    f.write("- **HealthWest Psychological Evaluation #1:** ALL ZEROS — no clinical findings\n")
    f.write("- **Police Investigations:** Nine (9) separate investigations yielding ZERO violations, ")
    f.write("arrests, or charges\n\n")
    
    f.write("After the first HealthWest evaluation returned all zeros, Judge McNeill sent a communication ")
    f.write("to the evaluator. The second evaluation subsequently changed its findings to a \"Rule Out\" ")
    f.write("assessment — a dramatic shift directly attributable to judicial interference with an ")
    f.write("ostensibly independent evaluation.\n\n")

    f.write("### D. Pattern of Bias\n\n")
    f.write("Analysis of Judge McNeill's orders reveals a systematic pattern of bias:\n\n")
    f.write("- **52 ex parte orders** in a single domestic relations case\n")
    f.write("- **44% ex parte grant rate** — far exceeding Michigan circuit court averages\n")
    f.write("- **100% of ex parte orders favor Mother** — statistical impossibility absent bias\n")
    f.write(f"- **{jv_count} documented judicial canon violations** across MCJC Canons 1, 2, and 3\n")
    f.write("- **59+ days cumulative incarceration** of Father — resulting in three job losses ")
    f.write("and two housing losses\n\n")

    f.write("### E. Ongoing Harm\n\n")
    f.write(f"As of the date of this filing, Father has been separated from his three-year-old son ")
    f.write(f"for {days_no_contact}+ consecutive days. Lincoln is at a critical developmental stage ")
    f.write("where prolonged separation from a parent causes documented psychological harm. ")
    f.write(f"Father has suffered ${total_damages:,.0f}+ in quantified economic damages, exclusive ")
    f.write("of emotional distress and punitive damages.\n\n")
    
    f.write(f"Analysis of {msg_count} AppClose co-parenting messages demonstrates that Father was a ")
    f.write("consistently cooperative, engaged parent, while Mother exhibited documented patterns of ")
    f.write(f"gatekeeping, stonewalling, and medical gatekeeping ({manip_count} manipulation instances detected).\n\n")
    f.write("---\n\n")

    # ================================================================
    # IV. STANDARD OF REVIEW
    # ================================================================
    f.write("## IV. STANDARD OF REVIEW\n\n")
    f.write("Constitutional issues, including due process claims, are reviewed de novo. ")
    f.write("*In re Rood*, 483 Mich 73, 91 (2009). Custody and parenting time decisions are ")
    f.write("reviewed for abuse of discretion. *Vodvarka v. Grasmeyer*, 259 Mich App 499, 507 (2003). ")
    f.write("An abuse of discretion occurs when the trial court's decision falls outside the range ")
    f.write("of reasonable and principled outcomes. *Berger v. Berger*, 277 Mich App 700, 705 (2008). ")
    f.write("Findings of fact are reviewed for clear error. MCR 2.613(C). A finding is clearly ")
    f.write("erroneous when, although there is evidence to support it, the reviewing court is left ")
    f.write("with a definite and firm conviction that a mistake has been made. *Fletcher v. Fletcher*, ")
    f.write("447 Mich 871, 878 (1994).\n\n")
    f.write("---\n\n")

    # ================================================================
    # V. ARGUMENT
    # ================================================================
    f.write("## V. ARGUMENT\n\n")
    
    # A. Procedural Due Process
    f.write("### A. The Trial Court Violated Appellant's Procedural Due Process Rights\n\n")
    f.write("The Fourteenth Amendment prohibits states from depriving any person of liberty ")
    f.write("without due process of law. U.S. Const. amend. XIV, § 1. A parent's right to the ")
    f.write("care, custody, and control of his child is a fundamental liberty interest protected ")
    f.write("by the Due Process Clause. *Troxel v. Granville*, 530 U.S. 57, 65 (2000).\n\n")
    
    f.write("Under the *Mathews v. Eldridge* three-factor balancing test, 424 U.S. 319, 335 (1976), ")
    f.write("the court must weigh: (1) the private interest affected; (2) the risk of erroneous ")
    f.write("deprivation and value of additional safeguards; and (3) the government's interest.\n\n")
    
    f.write("Here, all three factors weigh overwhelmingly in Appellant's favor:\n\n")
    f.write("**First**, the private interest — the parent-child relationship — is \"far more precious ")
    f.write("than any property right.\" *Santosky v. Kramer*, 455 U.S. 745, 758-59 (1982). Father ")
    f.write(f"has been completely severed from his {days_no_contact}-day-old relationship with Lincoln.\n\n")
    f.write("**Second**, the risk of erroneous deprivation was extreme and realized. The ex parte ")
    f.write("order was based on: (a) an illegal recording (MCL 750.539c felony); (b) a premeditated ")
    f.write("scheme evidenced by Albert Watson's admission; (c) no opportunity for Father to respond. ")
    f.write("Additional safeguards — such as a hearing — would have revealed all of this.\n\n")
    f.write("**Third**, the state's interest in protecting children was not served. Nine police ")
    f.write("investigations found zero concerns. The drug screen was negative. The independent ")
    f.write("evaluation found zero clinical issues — until the judge interfered.\n\n")

    # B. Substantive Due Process
    f.write("### B. The Trial Court Violated Appellant's Substantive Due Process Rights\n\n")
    f.write("Substantive due process protects fundamental rights from government interference ")
    f.write("regardless of the procedures used. Where a fundamental right is at stake, the ")
    f.write("government must demonstrate a compelling interest and narrow tailoring. ")
    f.write("*Washington v. Glucksberg*, 521 U.S. 702 (1997).\n\n")
    f.write("The complete termination of Father's parenting time is the most extreme remedy ")
    f.write("available — the functional equivalent of termination of parental rights without ")
    f.write("the procedural protections required by *Santosky*. No compelling state interest ")
    f.write("supports this termination where:\n\n")
    f.write("- Drug screen: **NEGATIVE**\n")
    f.write("- HealthWest evaluation #1: **ALL ZEROS**\n")
    f.write("- Police investigations (9): **ZERO findings**\n")
    f.write("- AppClose messages: **526 cooperative communications** from Father\n")
    f.write("- Documented incidents of harm: **ZERO**\n\n")
    f.write("The trial court imposed maximum deprivation with zero evidence of risk. This is ")
    f.write("the textbook definition of a substantive due process violation.\n\n")

    # C. Illegally Obtained Evidence
    f.write("### C. The Ex Parte Orders Were Based on Illegally Obtained Evidence\n\n")
    f.write("The recording by Lori Watson was made in violation of MCL 750.539c, which provides:\n\n")
    f.write("> Any person who is present or who is not present during a private conversation and ")
    f.write("who willfully uses any device to eavesdrop upon the conversation without the consent ")
    f.write("of all parties thereto... is guilty of a felony punishable by imprisonment for not ")
    f.write("more than 2 years...\n\n")
    f.write("Evidence obtained in violation of constitutional or statutory protections must be ")
    f.write("suppressed. *Mapp v. Ohio*, 367 U.S. 643 (1961). The fruit of the poisonous tree ")
    f.write("doctrine extends to all evidence derived from the illegality. *Wong Sun v. United States*, ")
    f.write("371 U.S. 471 (1963). Michigan follows this principle. *People v. Beavers*, 393 Mich 554 (1975).\n\n")
    f.write("Because the ex parte order of August 8, 2025 relied upon this feloniously obtained ")
    f.write("recording, the order — and all subsequent orders flowing from it — must be vacated.\n\n")

    # D. Judicial Bias
    f.write("### D. The Trial Court Exhibited Systematic Judicial Bias Requiring Reversal\n\n")
    f.write("Under MCR 2.003(C)(1), a judge is disqualified when the judge is biased or prejudiced ")
    f.write("for or against a party. The test is whether a reasonable person would perceive bias. ")
    f.write("*Caperton v. A.T. Massey Coal Co.*, 556 U.S. 868, 881 (2009).\n\n")
    f.write("The statistical record here speaks for itself:\n\n")
    f.write("| Metric | Value |\n")
    f.write("|--------|-------|\n")
    f.write("| Ex parte orders | 52 |\n")
    f.write("| Ex parte rate | 44% |\n")
    f.write("| Orders favoring Mother | 100% |\n")
    f.write("| Orders favoring Father | 0% |\n")
    f.write(f"| Judicial canon violations documented | {jv_count} |\n")
    f.write("| Father's days incarcerated | 59+ |\n")
    f.write("| Father's jobs lost | 3 |\n")
    f.write("| Police investigations finding wrongdoing | 0 of 9 |\n\n")
    f.write("No reasonable person could examine this record and conclude the proceedings were fair. ")
    f.write("The bias is not merely apparent — it is mathematical. A 100% ruling rate in one ")
    f.write("party's favor across 52 orders is a statistical impossibility absent systematic bias.\n\n")
    f.write("Additionally, the trial court's ex parte communication with the HealthWest evaluator ")
    f.write("— resulting in a changed evaluation — constitutes independent grounds for ")
    f.write("disqualification. *Ward v. Village of Monroeville*, 409 U.S. 57 (1972).\n\n")

    # E. Best Interest Factors
    f.write("### E. The Trial Court Failed to Apply MCL 722.23 Best Interest Factors\n\n")
    f.write("Under MCL 722.23, the court must consider twelve factors in determining custody and ")
    f.write("parenting time. *Brown v. Loveman*, 260 Mich App 576, 600 (2004). The trial court ")
    f.write("must make findings on each applicable factor. *Grew v. Knox*, 265 Mich App 333 (2005).\n\n")
    f.write("The record below contains no analysis of the best interest factors prior to the ")
    f.write("complete termination of Father's parenting time. This alone constitutes reversible ")
    f.write("error. Where the trial court terminates all parenting time — the most extreme ")
    f.write("disposition available — without best interest findings, the order cannot stand.\n\n")
    f.write("Factor (j) — the willingness of each parent to facilitate a close relationship between ")
    f.write("the child and the other parent — is particularly relevant. The AppClose record demonstrates ")
    f.write(f"526 cooperative messages from Father and a systematic pattern of gatekeeping by Mother ")
    f.write(f"({manip_count} documented manipulation instances). This factor weighs decisively for Father.\n\n")

    # F. Abuse of Discretion
    f.write("### F. The Trial Court's Orders Constitute an Abuse of Discretion\n\n")
    f.write("The trial court's decisions fall outside the range of reasonable and principled outcomes. ")
    f.write("*Berger v. Berger*, 277 Mich App 700, 705 (2008). Where exculpatory evidence overwhelmingly ")
    f.write("demonstrates no risk to the child, yet the court imposes total severance of the ")
    f.write("parent-child relationship, the discretion has been abused.\n\n")
    f.write("The cumulative weight of the errors below compels reversal:\n\n")
    f.write("1. Reliance on illegally obtained evidence (MCL 750.539c felony)\n")
    f.write("2. Disregard of exculpatory evidence (negative drug screen, zero evaluations, zero police findings)\n")
    f.write("3. Ex parte judicial communication with evaluator\n")
    f.write("4. Statistical impossibility of unbiased decision-making (100% adverse to Father)\n")
    f.write("5. Failure to apply MCL 722.23 factors\n")
    f.write(f"6. Disproportionate punishment (59+ days jail, {days_no_contact}+ days no contact)\n")
    f.write("7. Documented premeditation by adversary (Albert Watson admission)\n\n")
    f.write("---\n\n")

    # ================================================================
    # VI. RELIEF
    # ================================================================
    f.write("## VI. RELIEF REQUESTED\n\n")
    f.write("Appellant respectfully requests that this Court:\n\n")
    f.write("1. **REVERSE** all orders of the trial court suspending or terminating Appellant's parenting time;\n\n")
    f.write("2. **VACATE** the ex parte order of August 8, 2025, and all subsequent orders derived therefrom, ")
    f.write("as founded upon illegally obtained evidence in violation of MCL 750.539c;\n\n")
    f.write("3. **REMAND** to a different judge for proceedings untainted by the demonstrated bias of the ")
    f.write("Honorable Jenny L. McNeill, MCR 2.003;\n\n")
    f.write("4. **ORDER** immediate restoration of Appellant's parenting time pending further proceedings;\n\n")
    f.write("5. **ORDER** that any future custody or parenting time determinations include express findings ")
    f.write("under MCL 722.23;\n\n")
    f.write("6. Grant such other and further relief as this Court deems just and equitable.\n\n")
    f.write("---\n\n")
    
    # SIGNATURE
    f.write("Respectfully submitted,\n\n")
    f.write("____________________________\n")
    f.write("**Andrew J. Pigors, Pro Se**\n")
    f.write("1977 Whitehall Rd, Lot 17\n")
    f.write("Laketon Township, MI 49445\n")
    f.write("(231) 903-5690\n\n")
    f.write(f"Dated: ________________\n\n")
    
    # CERTIFICATE OF SERVICE
    f.write("---\n\n")
    f.write("## CERTIFICATE OF SERVICE\n\n")
    f.write("I hereby certify that on _____________, 2026, I served a copy of this ")
    f.write("Appellant's Brief on Appeal upon:\n\n")
    f.write("Jennifer L. Barnes (P55406)\n")
    f.write("Attorney for Defendant-Appellee\n")
    f.write("[Address]\n\n")
    f.write("by [first-class mail / electronic filing / personal delivery].\n\n")
    f.write("____________________________\n")
    f.write("Andrew J. Pigors\n")

brief_size = os.path.getsize(brief_path)
print(f"\n[+] COA Brief draft generated: {brief_size/1024:.0f}KB")
print(f"    Location: {brief_path}")
print(f"    Sections: Cover, TOC, Authorities, Jurisdiction, Questions (5),")
print(f"              Facts, Standard, Argument (6 sections), Relief, Certificate")
print(f"    Deadline: April 15, 2026 ({days_left} days)")
print(f"    Intelligence sourced: {jv_count} violations, {cv_count} const. violations,")
print(f"                          {rb_count} rebuttals, {total_damages:,.0f} damages")

conn.close()
print(f"\n{'='*70}")
print(f"  COA BRIEF ENGINE COMPLETE")
print(f"{'='*70}")
