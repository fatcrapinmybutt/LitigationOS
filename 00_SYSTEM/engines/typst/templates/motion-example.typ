// Example: Motion to Restore Parenting Time
// Compile: typst compile motion-example.typ motion-example.pdf

#import "michigan-court.typ": michigan-court, signature-block, certificate-of-service, numbered-paragraphs, exhibit

#show: michigan-court.with(
  case-number: "2024-001507-DC",
  document-title: "Motion to Restore Parenting Time",
)

#text(weight: "bold")[NOW COMES] Plaintiff, Andrew James Pigors, appearing _pro se_, and respectfully moves this Honorable Court for an order restoring parenting time with the minor child, L.D.W., and in support thereof states as follows:

== STATEMENT OF FACTS

#numbered-paragraphs(
  [Plaintiff is the biological father of L.D.W., born November 9, 2022.],
  [On April 29, 2024, this Court entered a joint legal and physical custody order providing Plaintiff with equal parenting time.],
  [On August 9, 2025, this Court entered an ex parte order suspending all parenting time without notice or hearing.],
  [On September 28, 2025, this Court entered a custody order granting Defendant 100% custody with zero parenting time for Plaintiff.],
  [Plaintiff has been separated from his son for over 240 days as of the date of this filing.],
)

== LEGAL ARGUMENT

Plaintiff's fundamental right to parent his child is protected by the Fourteenth Amendment to the United States Constitution. _Troxel v. Granville_, 530 U.S. 57, 65 (2000). A parent's right to the care, custody, and control of their children is "perhaps the oldest of the fundamental liberty interests recognized by this Court." _Id._

Under MCL 722.27a, parenting time shall be granted in accordance with the best interests of the child as defined in MCL 722.23. The complete elimination of a parent's contact with their child is the most extreme measure available and should be reserved for circumstances involving actual harm to the child.

== RELIEF REQUESTED

WHEREFORE, Plaintiff respectfully requests that this Court:

#numbered-paragraphs(
  [Immediately restore supervised parenting time pending a full evidentiary hearing;],
  [Schedule an evidentiary hearing on the merits within 14 days;],
  [Grant such other and further relief as this Court deems just and equitable.],
)

#signature-block(date: "March 25, 2026")

#certificate-of-service(
  date: "March 25, 2026",
  parties: (
    (name: "Emily A. Watson", address: "2160 Garland Dr, Norton Shores, MI 49441"),
    (name: "Muskegon County FOC", address: "990 Terrace St, Muskegon, MI 49442"),
  ),
)
