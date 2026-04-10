// _test-brief.typ — Compilation test for brief template
// Compile: typst compile _test-brief.typ _test-brief.pdf

#import "brief.typ": brief, creac
#import "caption.typ": numbered-paras, cite-case, exhibit-ref
#import "certificate-of-service.typ": certificate-of-service

#show: brief.with(
  document-title: "Brief in Support of Emergency Motion to Restore Parenting Time",
  date: "March 25, 2026",
  authorities: (
    cases: (
      (name: "Troxel v. Granville, 530 U.S. 57 (2000)", pages: "3, 5, 8"),
      (name: "Mathews v. Eldridge, 424 U.S. 319 (1976)", pages: "4, 7"),
      (name: "Vodvarka v. Grasher, 259 Mich App 499 (2003)", pages: "5"),
      (name: "Rains v. Rains, 301 Mich App 313 (2013)", pages: "6"),
    ),
    statutes: (
      (name: "MCL 722.23 (Best Interest Factors)", pages: "3, 5, 6, 7", italic: false),
      (name: "MCL 722.27a (Parenting Time)", pages: "4, 6", italic: false),
      (name: "MCL 722.27(1)(c) (Established Custodial Environment)", pages: "5", italic: false),
    ),
    court-rules: (
      (name: "MCR 2.119 (Motion Practice)", pages: "1", italic: false),
      (name: "MCR 3.210 (Custody Proceedings)", pages: "4", italic: false),
    ),
    constitutional: (
      (name: "U.S. Const. amend. XIV (Due Process)", pages: "3, 7, 8", italic: false),
    ),
  ),
)

= Statement of Issues Presented

Whether the trial court committed reversible error by suspending all parenting time via ex parte order on August 9, 2025, without providing Plaintiff notice, opportunity to be heard, or an evidentiary hearing, in violation of the Due Process Clause and MCL 722.27a.

= Statement of Facts

#numbered-paras(
  [Plaintiff and Defendant are the parents of L.D.W., born November 9, 2022.],
  [On April 1, 2024, Plaintiff filed a Complaint for Custody seeking joint legal and physical custody.],
  [On April 29, 2024, this Court entered a consent order granting joint legal and physical custody with equal parenting time.],
  [On July 17, 2024, following trial, this Court found all twelve MCL 722.23 best interest factors favored Mother and awarded Defendant sole physical custody.],
  [On August 9, 2025, this Court entered an ex parte order suspending all of Plaintiff's parenting time without prior notice or hearing.],
  [On September 28, 2025, this Court entered a custody order granting Defendant 100% custody with zero parenting time for Plaintiff.],
  [Plaintiff has had no contact with his son since July 29, 2025.],
)

= Standard of Review

A trial court's decision regarding parenting time is reviewed for an abuse of discretion. #cite-case("Vodvarka v. Grasher", pin: "259 Mich App 499, 508 (2003)"). An abuse of discretion occurs when the result falls outside the range of principled outcomes. Questions of constitutional law are reviewed de novo.

= Argument

== The Ex Parte Suspension of All Parenting Time Violated Due Process

The Fourteenth Amendment guarantees that no state shall deprive any person of life, liberty, or property without due process of law. A parent's fundamental liberty interest in the care, custody, and control of their children is "perhaps the oldest of the fundamental liberty interests recognized by this Court." #cite-case("Troxel v. Granville", pin: "530 U.S. 57, 65 (2000)").

#creac(
  conclusion-intro: [The ex parte order of August 9, 2025, violated Plaintiff's due process rights because it eliminated all parenting time without notice or hearing.],
  rule: [Procedural due process requires, at minimum: (1) notice, (2) an opportunity to be heard, and (3) a decision by a neutral decisionmaker. #cite-case("Mathews v. Eldridge", pin: "424 U.S. 319, 333 (1976)"). The deprivation of a fundamental right demands heightened procedural protections.],
  explanation: [In custody matters, Michigan courts have consistently held that parenting time decisions must be based on an evidentiary record and findings under MCL 722.23. #cite-case("Rains v. Rains", pin: "301 Mich App 313, 324 (2013)"). Complete termination of contact is the most extreme measure and requires the strongest justification.],
  application: [Here, the Court entered its August 9, 2025 order without providing Plaintiff any notice of the proceeding, any opportunity to present evidence or argument, or any evidentiary hearing. The order eliminated 100% of Plaintiff's parenting time. No findings were made under MCL 722.23. The severity of the deprivation --- complete severance of the father-child relationship --- demanded the highest level of procedural protection, yet none was provided.],
  conclusion: [The ex parte order must be vacated and parenting time restored, at minimum on a supervised basis, pending a full evidentiary hearing.],
)

== The Best Interest Factors Require Restoration of Parenting Time

Under MCL 722.27a, parenting time must be granted consistent with the best interests of the child. Factor (j), the willingness to facilitate a close relationship with the other parent, strongly favors Plaintiff. The continued total deprivation of contact harms L.D.W. by denying him a relationship with his father.

= Conclusion and Relief Requested

For the foregoing reasons, Plaintiff respectfully requests that this Court:

#numbered-paras(
  [Immediately restore supervised parenting time between Plaintiff and L.D.W.;],
  [Schedule an evidentiary hearing within 14 days;],
  [Vacate the ex parte order of August 9, 2025;],
  [Grant further relief as this Court deems just and equitable.],
)

#certificate-of-service(date: "March 25, 2026")
