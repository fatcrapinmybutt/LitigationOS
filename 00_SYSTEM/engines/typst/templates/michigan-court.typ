// Michigan Circuit Court Filing Template — LitigationOS
// Conforms to MCR 2.113 (Form of Pleadings) and MCR 8.119
// Times New Roman 12pt, double-spaced, 1" margins

#let michigan-court(
  case-number: "",
  court: "14TH JUDICIAL CIRCUIT COURT",
  county: "MUSKEGON COUNTY",
  judge: "HON. JENNY L. McNEILL",
  plaintiff: "ANDREW JAMES PIGORS",
  defendant: "EMILY A. WATSON",
  document-title: "",
  body,
) = {
  set page(
    paper: "us-letter",
    margin: (top: 1in, bottom: 1in, left: 1in, right: 1in),
    numbering: "1",
    number-align: center + bottom,
  )
  set text(font: "Times New Roman", size: 12pt)
  set par(leading: 1.4em, first-line-indent: 0.5in, spacing: 1.4em)

  // Court header block (single-spaced)
  set par(leading: 0.65em, first-line-indent: 0pt, spacing: 0.65em)
  align(center)[
    #text(weight: "bold", size: 12pt)[STATE OF MICHIGAN]
    #linebreak()
    #text(size: 12pt)[IN THE #court]
    #linebreak()
    #text(size: 12pt)[#county]
  ]

  v(0.3in)

  // Party block
  grid(
    columns: (1fr, auto, 1fr),
    align(left)[
      #text(weight: "bold")[#plaintiff,] \
      #h(0.25in) Plaintiff, appearing _pro se_, \
      \
      #h(0.5in) v \
      \
      #text(weight: "bold")[#defendant,] \
      #h(0.25in) Defendant. \
      #line(length: 100%, stroke: 0.5pt)
    ],
    h(0.25in),
    align(left)[
      Case No. #text(weight: "bold")[#case-number] \
      \
      #judge \
    ],
  )

  v(0.3in)

  // Document title
  align(center)[
    #text(weight: "bold", size: 12pt)[#upper(document-title)]
  ]

  v(0.2in)

  // Reset to double-spaced body
  set par(leading: 1.4em, first-line-indent: 0.5in, spacing: 1.4em)
  body
}

// Signature block
#let signature-block(name: "ANDREW JAMES PIGORS", date: none) = {
  v(0.5in)
  set par(first-line-indent: 0pt)
  line(length: 3in, stroke: 0.5pt)
  [#name \
  Plaintiff, appearing _pro se_ \
  1977 Whitehall Rd, Lot 17 \
  North Muskegon, MI 49445 \
  (231) 903-5690 \
  andrewjpigors\@gmail.com]
  if date != none {
    v(0.1in)
    [Date: #date]
  }
}

// Certificate of Service
#let certificate-of-service(
  date: none,
  method: "electronic filing",
  parties: (
    (name: "Emily A. Watson", address: "2160 Garland Dr, Norton Shores, MI 49441"),
  ),
) = {
  pagebreak()
  set par(first-line-indent: 0pt)
  align(center)[
    #text(weight: "bold")[CERTIFICATE OF SERVICE]
  ]
  v(0.2in)
  set par(first-line-indent: 0.5in)
  let serve-date = if date != none { date } else { "_______________" }
  [I, Andrew James Pigors, Plaintiff appearing _pro se_, hereby certify that on #serve-date, I served a copy of the foregoing document upon the following by #method:]
  v(0.15in)
  set par(first-line-indent: 0pt)
  for party in parties {
    [#h(1in) #party.name \
     #h(1in) #party.address]
    v(0.1in)
  }
  v(0.3in)
  signature-block()
}

// IRAC section helper
#let irac-section(issue: "", rule: "", application: "", conclusion: "") = {
  set par(first-line-indent: 0pt)
  text(weight: "bold")[Issue: ]
  issue
  v(0.1in)
  text(weight: "bold")[Rule: ]
  rule
  v(0.1in)
  text(weight: "bold")[Application: ]
  application
  v(0.1in)
  text(weight: "bold")[Conclusion: ]
  conclusion
}

// Numbered paragraph helper
#let numbered-paragraphs(..items) = {
  set par(first-line-indent: 0pt)
  enum(
    numbering: "1.",
    ..items
  )
}

// Exhibit reference
#let exhibit(label) = {
  text(weight: "bold")[(Exhibit #label)]
}
