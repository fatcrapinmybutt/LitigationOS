// _test-compile.typ — Compilation test for all templates
// Compile: typst compile _test-compile.typ _test-compile.pdf
// This file exercises caption, motion, COS, and exhibit-cover templates

#import "motion.typ": motion, irac, wherefore
#import "caption.typ": numbered-paras, exhibit-ref, cite-case, now-comes
#import "certificate-of-service.typ": certificate-of-service
#import "exhibit-cover.typ": exhibit-cover

#show: motion.with(
  document-title: "Emergency Motion to Restore Parenting Time",
  date: "March 25, 2026",
)

#now-comes(action: [respectfully moves this Honorable Court for an order immediately restoring parenting time with the minor child, L.D.W.])[

== Statement of Facts

#numbered-paras(
  [Plaintiff is the biological father of L.D.W., born November 9, 2022.],
  [On April 29, 2024, this Court entered a consent order providing joint legal and physical custody with equal parenting time.],
  [On August 9, 2025, this Court entered an ex parte order suspending all of Plaintiff's parenting time without prior notice or hearing.],
  [On September 28, 2025, this Court entered a custody order granting Defendant sole legal and physical custody with zero parenting time for Plaintiff.],
  [Plaintiff has had no contact with his son since July 29, 2025, a period that now exceeds 240 days.],
  [The complete severance of the parent-child relationship causes ongoing irreparable harm to both Plaintiff and L.D.W.],
)

== Legal Argument

A parent's right to the care, custody, and control of their children is "perhaps the oldest of the fundamental liberty interests recognized by this Court." #cite-case("Troxel v. Granville", pin: "530 U.S. 57, 65 (2000)"). The Due Process Clause of the Fourteenth Amendment protects this fundamental right. #cite-case("Mathews v. Eldridge", pin: "424 U.S. 319 (1976)").

#irac(
  issue: [Whether the complete elimination of Plaintiff's parenting time without an evidentiary hearing violates Plaintiff's fundamental parental rights under the Fourteenth Amendment and MCL 722.27a.],
  rule: [Under MCL 722.27a, parenting time shall be granted in accordance with the best interests of the child as defined in MCL 722.23. The complete termination of a parent's contact with their child is the most extreme measure available and requires clear and convincing evidence of harm. #cite-case("Rains v. Rains", pin: "301 Mich App 313, 324 (2013)").],
  application: [Here, this Court terminated all parenting time via ex parte order on August 9, 2025, without providing Plaintiff notice or opportunity to be heard. No evidentiary hearing has been conducted. No findings of fact under MCL 722.23 support the complete elimination of contact. The absence of any parenting time --- even supervised --- is disproportionate to any alleged concern and causes demonstrated harm to L.D.W., who has been deprived of his father for over 240 days. See #exhibit-ref("A").],
  conclusion: [The Court should immediately restore, at minimum, supervised parenting time pending a full evidentiary hearing on the merits. The continued complete deprivation of contact is constitutionally impermissible.],
)

== Relief Requested

#wherefore(
  [Immediately restore supervised parenting time between Plaintiff and L.D.W. pending a full evidentiary hearing;],
  [Schedule an evidentiary hearing on the merits within 14 days of the date of this motion;],
  [Enter a temporary order defining a specific supervised parenting time schedule;],
  [Grant such other and further relief as this Court deems just and equitable.],
)

]

#certificate-of-service(date: "March 25, 2026")

#exhibit-cover(
  letter: "A",
  description: "Ex Parte Order Suspending All Parenting Time (August 9, 2025)",
  bates-start: "PIGORS-000001",
  bates-end: "PIGORS-000003",
)
