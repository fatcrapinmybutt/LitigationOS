// motion.typ — Michigan Circuit Court Motion Template
// MCR 2.119 (Motion Practice) · MCR 2.113 (Form of Pleadings)
// LitigationOS · Pigors v Watson · Case No. 2024-001507-DC
//
// USAGE:
//   #import "motion.typ": motion, irac, wherefore
//   #show: motion.with(document-title: "Emergency Motion to Restore Parenting Time")
//
//   #now-comes(action: [moves for an order restoring parenting time with L.D.W.])[
//     // body content
//   ]
//
//   == STATEMENT OF FACTS
//   #numbered-paras(
//     [Fact one.],
//     [Fact two.],
//   )
//
//   == LEGAL ARGUMENT
//   #irac(
//     issue: [Whether the court erred...],
//     rule: [Under MCL 722.27a...],
//     application: [Here, the facts show...],
//     conclusion: [Therefore, the court should...],
//   )
//
//   == RELIEF REQUESTED
//   #wherefore(
//     [Restore supervised parenting time;],
//     [Schedule an evidentiary hearing within 14 days;],
//     [Grant further relief as this Court deems just.],
//   )

#import "caption.typ": court-page, caption, pro-se-signature, numbered-paras,
  section-heading, exhibit-ref, cite-case, now-comes

// Re-export caption utilities so users only need one import
// (Typst re-exports work via the import above)

// ═══════════════════════════════════════════════════════════════
// MOTION DOCUMENT TEMPLATE
// Apply via: #show: motion.with(document-title: "...")
// ═══════════════════════════════════════════════════════════════

#let motion(
  // Case parameters (defaults to Pigors v Watson)
  case-number: "2024-001507-DC",
  court: "CIRCUIT COURT FOR THE COUNTY OF MUSKEGON",
  division: none,
  judge: "HON. JENNY L. McNEILL",
  plaintiff: "ANDREW JAMES PIGORS",
  defendant: "EMILY A. WATSON",
  document-title: "MOTION",
  // Signature parameters
  date: none,
  show-signature: true,
  // Content
  body,
) = {
  // Apply court page setup (font, margins, spacing)
  show: court-page

  // Heading style for motion sections (== HEADING becomes centered bold)
  show heading.where(level: 1): it => {
    set par(first-line-indent: 0pt)
    v(0.15in)
    align(center)[
      #text(weight: "bold", size: 12pt)[#upper(it.body)]
    ]
    v(0.1in)
  }
  show heading.where(level: 2): it => {
    set par(first-line-indent: 0pt)
    v(0.1in)
    text(weight: "bold", size: 12pt)[#it.body]
    v(0.05in)
  }

  // Render caption
  caption(
    case-number: case-number,
    court: court,
    division: division,
    judge: judge,
    plaintiff: plaintiff,
    defendant: defendant,
    document-title: document-title,
  )

  // Body content
  body

  // Signature block
  if show-signature {
    pro-se-signature(date: date)
  }
}

// ═══════════════════════════════════════════════════════════════
// IRAC ANALYSIS BLOCK
// Issue → Rule → Application → Conclusion
// ═══════════════════════════════════════════════════════════════

#let irac(
  issue: none,
  rule: none,
  application: none,
  conclusion: none,
  numbered: false,
) = {
  set par(first-line-indent: 0pt, leading: 1.5em, spacing: 1.0em)

  if issue != none {
    block(inset: (left: 0.25in))[
      #text(weight: "bold")[Issue: ] #issue
    ]
  }
  if rule != none {
    block(inset: (left: 0.25in))[
      #text(weight: "bold")[Rule: ] #rule
    ]
  }
  if application != none {
    block(inset: (left: 0.25in))[
      #text(weight: "bold")[Application: ] #application
    ]
  }
  if conclusion != none {
    block(inset: (left: 0.25in))[
      #text(weight: "bold")[Conclusion: ] #conclusion
    ]
  }
}

// ═══════════════════════════════════════════════════════════════
// WHEREFORE RELIEF BLOCK
// Standard Michigan "WHEREFORE, Plaintiff respectfully requests..."
// ═══════════════════════════════════════════════════════════════

#let wherefore(..items) = {
  set par(first-line-indent: 0.5in, leading: 1.5em, spacing: 1.0em)

  [WHEREFORE, Plaintiff, Andrew James Pigors, appearing _pro se_, respectfully requests that this Honorable Court:]
  v(0.05in)
  numbered-paras(..items)
}
