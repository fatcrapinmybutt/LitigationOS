// brief.typ — Michigan Circuit Court Brief / Memorandum Template
// MCR 2.119(A)(2) (Supporting Briefs) · MCR 7.212 (Appellate Briefs)
// LitigationOS · Pigors v Watson · Case No. 2024-001507-DC
//
// USAGE:
//   #import "brief.typ": brief, index-of-authorities, creac
//   #show: brief.with(
//     document-title: "Brief in Support of Emergency Motion to Restore Parenting Time",
//     show-toc: true,
//     authorities: (
//       cases: (
//         (name: "Troxel v. Granville, 530 U.S. 57 (2000)", pages: "4, 8"),
//         (name: "Vodvarka v. Grasher, 259 Mich App 499 (2003)", pages: "5, 9"),
//       ),
//       statutes: (
//         (name: "MCL 722.23", pages: "3, 6, 7"),
//         (name: "MCL 722.27a", pages: "5"),
//       ),
//       court-rules: (
//         (name: "MCR 2.119", pages: "1"),
//       ),
//     ),
//   )
//
//   = Statement of Issues Presented
//   ...
//   = Statement of Facts
//   ...
//   = Standard of Review
//   ...
//   = Argument
//   == The Court Erred in Suspending All Parenting Time
//   ...
//   = Conclusion and Relief Requested
//   ...

#import "caption.typ": court-page, caption, pro-se-signature, numbered-paras,
  section-heading, exhibit-ref, cite-case, now-comes

// ═══════════════════════════════════════════════════════════════
// INDEX OF AUTHORITIES — formatted by category
// ═══════════════════════════════════════════════════════════════

#let index-of-authorities(
  cases: (),
  statutes: (),
  court-rules: (),
  constitutional: (),
  other: (),
) = {
  set par(first-line-indent: 0pt, leading: 0.85em, spacing: 0.65em)

  pagebreak()
  align(center)[
    #text(weight: "bold", size: 12pt)[INDEX OF AUTHORITIES]
  ]
  v(0.2in)

  // Render a category block
  let render-category(title, entries) = {
    if entries.len() > 0 {
      text(weight: "bold", style: "italic", size: 12pt)[#title]
      v(0.1in)
      for entry in entries {
        block(width: 100%, inset: (left: 0.0in))[
          #grid(
            columns: (1fr, auto),
            gutter: 4pt,
            {
              if entry.keys().contains("italic") and entry.italic == false {
                entry.name
              } else {
                emph(entry.name)
              }
            },
            {
              if entry.keys().contains("pages") { entry.pages }
            },
          )
        ]
        v(2pt)
      }
      v(0.15in)
    }
  }

  render-category("Cases", cases)
  render-category("Statutes", statutes)
  render-category("Court Rules", court-rules)
  render-category("Constitutional Provisions", constitutional)
  render-category("Other Authorities", other)
}

// ═══════════════════════════════════════════════════════════════
// BRIEF DOCUMENT TEMPLATE
// Apply via: #show: brief.with(document-title: "...")
// ═══════════════════════════════════════════════════════════════

#let brief(
  // Case parameters
  case-number: "2024-001507-DC",
  court: "CIRCUIT COURT FOR THE COUNTY OF MUSKEGON",
  division: none,
  judge: "HON. JENNY L. McNEILL",
  plaintiff: "ANDREW JAMES PIGORS",
  defendant: "EMILY A. WATSON",
  document-title: "BRIEF IN SUPPORT",
  // Brief-specific options
  show-toc: true,
  show-ioa: true,
  authorities: (cases: (), statutes: (), court-rules: (), constitutional: (), other: ()),
  // Signature
  date: none,
  show-signature: true,
  // Content
  body,
) = {
  // Apply court page setup
  show: court-page

  // --- Heading styles for legal brief ---
  // Level 1 = Roman numeral, centered, bold, uppercase
  set heading(numbering: (..nums) => {
    let n = nums.pos()
    let depth = n.len()
    let current = n.last()
    if depth == 1 { numbering("I.", current) }
    else if depth == 2 { numbering("A.", current) }
    else if depth == 3 { numbering("1.", current) }
    else { numbering("a.", current) }
  })

  show heading.where(level: 1): it => {
    set par(first-line-indent: 0pt)
    v(0.2in)
    align(center)[
      #text(weight: "bold", size: 12pt)[
        #counter(heading).display((..nums) => {
          numbering("I.", nums.pos().last())
        })
        #h(0.3em)
        #upper(it.body)
      ]
    ]
    v(0.12in)
  }

  show heading.where(level: 2): it => {
    set par(first-line-indent: 0pt)
    v(0.15in)
    block(inset: (left: 0.25in))[
      #text(weight: "bold", size: 12pt)[
        #counter(heading).display((..nums) => {
          numbering("A.", nums.pos().last())
        })
        #h(0.3em)
        #it.body
      ]
    ]
    v(0.08in)
  }

  show heading.where(level: 3): it => {
    set par(first-line-indent: 0pt)
    v(0.1in)
    block(inset: (left: 0.5in))[
      #text(weight: "bold", size: 12pt)[
        #counter(heading).display((..nums) => {
          numbering("1.", nums.pos().last())
        })
        #h(0.3em)
        #it.body
      ]
    ]
    v(0.05in)
  }

  // --- Render caption ---
  caption(
    case-number: case-number,
    court: court,
    division: division,
    judge: judge,
    plaintiff: plaintiff,
    defendant: defendant,
    document-title: document-title,
  )

  // --- Table of Contents ---
  if show-toc {
    pagebreak()
    set par(first-line-indent: 0pt, leading: 0.85em, spacing: 0.65em)
    align(center)[
      #text(weight: "bold", size: 12pt)[TABLE OF CONTENTS]
    ]
    v(0.2in)
    outline(
      title: none,
      indent: 0.3in,
      depth: 3,
    )
  }

  // --- Index of Authorities ---
  if show-ioa {
    index-of-authorities(
      cases: authorities.at("cases", default: ()),
      statutes: authorities.at("statutes", default: ()),
      court-rules: authorities.at("court-rules", default: ()),
      constitutional: authorities.at("constitutional", default: ()),
      other: authorities.at("other", default: ()),
    )
  }

  // --- Brief body ---
  pagebreak()
  body

  // --- Signature ---
  if show-signature {
    pro-se-signature(date: date)
  }
}

// ═══════════════════════════════════════════════════════════════
// CREAC ANALYSIS BLOCK
// Conclusion → Rule → Explanation → Application → Conclusion
// Used in persuasive briefs (vs. IRAC in motions)
// ═══════════════════════════════════════════════════════════════

#let creac(
  conclusion-intro: none,
  rule: none,
  explanation: none,
  application: none,
  conclusion: none,
) = {
  set par(first-line-indent: 0.5in, leading: 1.5em, spacing: 1.0em)

  if conclusion-intro != none {
    conclusion-intro
    v(0.05in)
  }
  if rule != none {
    rule
    v(0.05in)
  }
  if explanation != none {
    explanation
    v(0.05in)
  }
  if application != none {
    application
    v(0.05in)
  }
  if conclusion != none {
    conclusion
  }
}
