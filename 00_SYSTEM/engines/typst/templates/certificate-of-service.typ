// certificate-of-service.typ — Michigan Certificate of Service
// MCR 2.107 (Service and Filing of Pleadings)
// Equivalent to SCAO Form MC 12
// LitigationOS · Pigors v Watson · Case No. 2024-001507-DC
//
// USAGE (as appendix to any filing):
//   #import "certificate-of-service.typ": certificate-of-service
//   // ... at end of your motion/brief ...
//   #certificate-of-service(date: "March 25, 2026")
//
// USAGE (as standalone document):
//   #import "caption.typ": court-page
//   #import "certificate-of-service.typ": certificate-of-service
//   #show: court-page
//   #certificate-of-service(date: "March 25, 2026")
//
// CUSTOM PARTIES:
//   #certificate-of-service(
//     date: "March 25, 2026",
//     method: "first-class mail",
//     parties: (
//       (name: "Emily A. Watson", address: "2160 Garland Dr, Norton Shores, MI 49441"),
//       (name: "Other Party", address: "123 Main St, Muskegon, MI 49440"),
//     ),
//   )

#import "caption.typ": pro-se-signature

// ═══════════════════════════════════════════════════════════════
// CERTIFICATE OF SERVICE
// Inserts a pagebreak, title, certification text, party list,
// and pro se signature block.
// ═══════════════════════════════════════════════════════════════

#let certificate-of-service(
  // Filing date (displayed in certification text)
  date: none,
  // Service method: "electronic filing", "first-class mail", "personal service"
  method: "electronic filing through the Court's e-filing system",
  // Parties served — array of (name, address) dictionaries
  parties: (
    (
      name: "Emily A. Watson",
      address: "2160 Garland Dr\nNorton Shores, MI 49441",
      via: none,
    ),
    (
      name: "Muskegon County Friend of the Court\nc/o Pamela Rusco",
      address: "990 Terrace St\nMuskegon, MI 49442",
      via: none,
    ),
  ),
  // Filer info
  filer-name: "Andrew James Pigors",
  // Whether to start a new page
  new-page: true,
) = {
  if new-page { pagebreak() }

  set par(first-line-indent: 0pt, leading: 0.85em, spacing: 0.85em)

  // Title
  align(center)[
    #text(weight: "bold", size: 12pt)[CERTIFICATE OF SERVICE]
  ]
  v(0.2in)

  // Certification text
  let serve-date = if date != none { date } else { [\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_] }

  set par(first-line-indent: 0.5in, leading: 1.5em, spacing: 1.5em)
  [I, #filer-name, Plaintiff, appearing _pro se_, hereby certify that on #serve-date, I served a true and correct copy of the foregoing document upon the following parties by #method:]

  v(0.15in)

  // Party list
  set par(first-line-indent: 0pt, leading: 0.75em, spacing: 0.65em)
  for party in parties {
    block(width: 100%, inset: (left: 1in))[
      #text(weight: "bold")[#party.name] \
      #party.address
      #if party.keys().contains("via") and party.via != none [
        \ (via #party.via)
      ]
    ]
    v(0.12in)
  }

  // Signature
  pro-se-signature(
    date: date,
    show-respectfully: false,
  )
}
