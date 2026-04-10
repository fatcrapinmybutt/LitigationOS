// exhibit-cover.typ — Exhibit Cover Page
// For use in Michigan Circuit Court filing packages
// LitigationOS · Pigors v Watson · Case No. 2024-001507-DC
//
// USAGE (inline in a filing):
//   #import "exhibit-cover.typ": exhibit-cover
//   #exhibit-cover(
//     letter: "A",
//     description: "Ex Parte Order Suspending Parenting Time (August 9, 2025)",
//     bates-start: "PIGORS-000001",
//     bates-end: "PIGORS-000003",
//   )
//
// USAGE (standalone single cover page):
//   #import "exhibit-cover.typ": exhibit-cover-page
//   #show: exhibit-cover-page.with(
//     letter: "B",
//     description: "Police Report NSPD-2023-08121",
//   )

// ═══════════════════════════════════════════════════════════════
// EXHIBIT COVER — Insertable cover page within a filing
// Adds a pagebreak and renders the cover page
// ═══════════════════════════════════════════════════════════════

#let exhibit-cover(
  // Exhibit letter or number (A, B, C, 1, 2, 3, etc.)
  letter: "A",
  // Short description of the exhibit
  description: none,
  // Bates number range
  bates-start: none,
  bates-end: none,
  bates-prefix: "PIGORS",
  // Case reference line
  case-number: "2024-001507-DC",
  case-name: "Pigors v. Watson",
  // Whether to start a new page
  new-page: true,
) = {
  if new-page { pagebreak() }

  set par(first-line-indent: 0pt, leading: 0.65em, spacing: 0.65em)

  // Vertically center the content
  v(2.5in)

  // Exhibit label — large, bold, centered
  align(center)[
    #text(weight: "bold", size: 14pt, tracking: 0.1em)[EXHIBIT]
    #v(0.3in)
    #text(weight: "bold", size: 36pt)[#letter]
  ]

  v(0.5in)

  // Description
  if description != none {
    align(center)[
      #text(size: 12pt)[#description]
    ]
  }

  v(0.4in)

  // Bates range
  if bates-start != none {
    align(center)[
      #text(size: 11pt)[
        #if bates-end != none [
          #bates-start #sym.dash.em #bates-end
        ] else [
          #bates-start
        ]
      ]
    ]
  }

  // Case reference at bottom
  v(1fr)
  align(center)[
    #text(size: 10pt, fill: luma(100))[
      #case-name #sym.dot.c Case No. #case-number
    ]
  ]
}

// ═══════════════════════════════════════════════════════════════
// EXHIBIT COVER PAGE — Standalone document show rule
// Apply via: #show: exhibit-cover-page.with(letter: "A", ...)
// ═══════════════════════════════════════════════════════════════

#let exhibit-cover-page(
  letter: "A",
  description: none,
  bates-start: none,
  bates-end: none,
  bates-prefix: "PIGORS",
  case-number: "2024-001507-DC",
  case-name: "Pigors v. Watson",
  body,
) = {
  set page(
    paper: "us-letter",
    margin: (top: 1in, bottom: 1in, left: 1in, right: 1in),
    numbering: none,
  )
  set text(font: "Times New Roman", size: 12pt)

  exhibit-cover(
    letter: letter,
    description: description,
    bates-start: bates-start,
    bates-end: bates-end,
    bates-prefix: bates-prefix,
    case-number: case-number,
    case-name: case-name,
    new-page: false,
  )

  body
}
