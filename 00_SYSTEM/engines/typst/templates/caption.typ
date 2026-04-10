// caption.typ — Michigan Circuit Court Caption & Core Utilities
// MCR 2.113 (Form of Pleadings) · MCR 8.119 (Case Records)
// LitigationOS · Pigors v Watson · Case No. 2024-001507-DC
//
// USAGE:
//   #import "caption.typ": court-page, caption, pro-se-signature,
//     numbered-paras, section-heading, exhibit-ref
//
//   #show: court-page
//   #caption(document-title: "Motion to Restore Parenting Time")
//   Your content here...
//   #pro-se-signature(date: "March 25, 2026")

// ═══════════════════════════════════════════════════════════════
// PAGE SETUP — Apply via: #show: court-page
// Times New Roman 12pt, double-spaced, 1" margins, US Letter
// ═══════════════════════════════════════════════════════════════

#let court-page(body) = {
  set page(
    paper: "us-letter",
    margin: (top: 1in, bottom: 1in, left: 1in, right: 1in),
    numbering: "1",
    number-align: center + bottom,
  )
  set text(
    font: "Times New Roman",
    size: 12pt,
    lang: "en",
    region: "us",
  )
  set par(
    leading: 1.5em,
    spacing: 1.5em,
    first-line-indent: 0.5in,
  )
  body
}

// ═══════════════════════════════════════════════════════════════
// CAPTION BLOCK — Michigan Circuit Court standard format
// Renders: STATE OF MICHIGAN header, party block, case info,
//          caption closing line with slash
// ═══════════════════════════════════════════════════════════════

#let caption(
  case-number: "2024-001507-DC",
  court: "CIRCUIT COURT FOR THE COUNTY OF MUSKEGON",
  division: none,
  judge: "HON. JENNY L. McNEILL",
  plaintiff: "ANDREW JAMES PIGORS",
  plaintiff-label: [Plaintiff, appearing _pro se_],
  defendant: "EMILY A. WATSON",
  defendant-label: [Defendant],
  document-title: none,
) = {
  // Caption uses tight single spacing
  set par(leading: 0.65em, first-line-indent: 0pt, spacing: 0.65em)

  // --- Court header centered ---
  align(center)[
    #text(weight: "bold", size: 12pt)[STATE OF MICHIGAN]
    #v(2pt)
    #text(size: 12pt)[IN THE #court]
    #if division != none {
      v(2pt)
      text(size: 11pt)[#division]
    }
  ]

  v(0.2in)

  // --- Party block (left) + Case info (right) ---
  grid(
    columns: (1fr, 0.4in, auto),
    gutter: 0pt,
    // Left column: parties
    {
      text(weight: "bold")[#plaintiff]
      [, #linebreak()]
      [#h(0.3in) #plaintiff-label, #linebreak()]
      v(0.12in)
      [#h(0.5in) v #linebreak()]
      v(0.12in)
      text(weight: "bold")[#defendant]
      [, #linebreak()]
      [#h(0.3in) #defendant-label.]
    },
    // Spacer
    [],
    // Right column: case info
    {
      [Case No. #text(weight: "bold")[#case-number]]
      linebreak()
      v(0.25in)
      judge
    },
  )

  // --- Caption closing line with forward slash (Michigan convention) ---
  v(4pt)
  box(width: 100% - 6pt)[#line(length: 100%, stroke: 0.5pt)]
  text(size: 12pt)[/]

  // --- Document title ---
  if document-title != none {
    v(0.2in)
    align(center)[
      #text(weight: "bold", size: 12pt)[#upper(document-title)]
    ]
  }

  // Restore double-spacing for subsequent content
  v(0.2in)
}

// ═══════════════════════════════════════════════════════════════
// PRO SE SIGNATURE BLOCK
// Right-aligned, includes address/phone/email per MCR 2.114
// ═══════════════════════════════════════════════════════════════

#let pro-se-signature(
  name: "Andrew James Pigors",
  address-line1: "1977 Whitehall Rd, Lot 17",
  address-line2: "North Muskegon, MI 49445",
  phone: "(231) 903-5690",
  email: "andrewjpigors@gmail.com",
  date: none,
  show-respectfully: true,
) = {
  set par(first-line-indent: 0pt, leading: 0.65em, spacing: 0.65em)

  if show-respectfully {
    v(0.3in)
    [Respectfully submitted,]
  }

  v(0.4in)

  // Signature line — right half of page
  grid(
    columns: (45%, 55%),
    [],
    {
      line(length: 100%, stroke: 0.5pt)
      v(2pt)
      text(weight: "bold")[#name]
      linebreak()
      [Plaintiff, appearing _pro se_]
      linebreak()
      address-line1
      linebreak()
      address-line2
      linebreak()
      phone
      linebreak()
      email
    },
  )

  if date != none {
    v(0.2in)
    grid(
      columns: (45%, 55%),
      [],
      [Dated: #date],
    )
  }
}

// ═══════════════════════════════════════════════════════════════
// HELPER: Numbered Paragraphs
// Court-style numbered paragraphs (1., 2., 3., ...)
// ═══════════════════════════════════════════════════════════════

#let numbered-paras(..items) = {
  set par(first-line-indent: 0pt, leading: 1.5em, spacing: 1.0em)
  for (i, item) in items.pos().enumerate() {
    grid(
      columns: (0.5in, 1fr),
      gutter: 0.15in,
      align(right)[#(i + 1).],
      item,
    )
    v(0.05in)
  }
}

// ═══════════════════════════════════════════════════════════════
// HELPER: Section Heading (centered, bold, uppercase)
// ═══════════════════════════════════════════════════════════════

#let section-heading(title) = {
  set par(first-line-indent: 0pt)
  v(0.1in)
  align(center)[
    #text(weight: "bold", size: 12pt)[#upper(title)]
  ]
  v(0.05in)
}

// ═══════════════════════════════════════════════════════════════
// HELPER: Exhibit Reference (inline bold reference)
// Usage: ... as shown in #exhibit-ref("A") ...
// ═══════════════════════════════════════════════════════════════

#let exhibit-ref(label) = {
  text(weight: "bold")[(Exhibit #label)]
}

// ═══════════════════════════════════════════════════════════════
// HELPER: Case Citation (italicized case name)
// Usage: #cite-case("Troxel v. Granville", pin: "530 U.S. 57, 65 (2000)")
// ═══════════════════════════════════════════════════════════════

#let cite-case(name, pin: none) = {
  emph(name)
  if pin != none [, #pin]
}

// ═══════════════════════════════════════════════════════════════
// HELPER: NOW COMES introductory paragraph
// Standard opening for Michigan motions
// ═══════════════════════════════════════════════════════════════

#let now-comes(
  name: "Andrew James Pigors",
  action: [respectfully moves this Honorable Court],
  body,
) = {
  set par(first-line-indent: 0.5in)
  [#text(weight: "bold")[NOW COMES] #name, Plaintiff, appearing _pro se_, and #action, and in support thereof states as follows:]
  body
}
