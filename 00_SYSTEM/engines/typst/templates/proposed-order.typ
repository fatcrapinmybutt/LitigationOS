// proposed-order.typ — Michigan Circuit Court Proposed Order
// MCR 2.602 (Judgments and Orders)
// LitigationOS · Pigors v Watson · Case No. 2024-001507-DC
//
// USAGE:
//   #import "proposed-order.typ": proposed-order, order-item, further-ordered
//   #show: proposed-order.with(document-title: "Order Restoring Parenting Time")
//
//   At a session of said Court held in the
//   Courthouse in the City of Muskegon, County
//   of Muskegon, State of Michigan.
//
//   #order-item[
//     The Defendant's sole custody of the minor child, L.D.W., is hereby
//     modified to restore parenting time to Plaintiff under a supervised
//     schedule as determined by the Friend of the Court.
//   ]
//
//   #further-ordered[
//     An evidentiary hearing shall be held within 14 days of the date
//     of this Order to address the parenting time schedule.
//   ]
//
//   #further-ordered[
//     All prior orders not inconsistent with this Order shall remain
//     in full force and effect.
//   ]

#import "caption.typ": court-page, caption

// ═══════════════════════════════════════════════════════════════
// PROPOSED ORDER DOCUMENT TEMPLATE
// Apply via: #show: proposed-order.with(document-title: "...")
// ═══════════════════════════════════════════════════════════════

#let proposed-order(
  // Case parameters
  case-number: "2024-001507-DC",
  court: "CIRCUIT COURT FOR THE COUNTY OF MUSKEGON",
  division: none,
  judge: "HON. JENNY L. McNEILL",
  plaintiff: "ANDREW JAMES PIGORS",
  defendant: "EMILY A. WATSON",
  document-title: "ORDER",
  // Content
  body,
) = {
  // Apply court page setup
  show: court-page

  // Disable heading numbering in orders
  set heading(numbering: none)

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

  // Body content (session language, order paragraphs)
  body

  // --- "IT IS SO ORDERED." closing ---
  v(0.3in)
  set par(first-line-indent: 0.5in)
  text(weight: "bold")[IT IS SO ORDERED.]

  // --- Judge signature block ---
  v(0.6in)
  set par(first-line-indent: 0pt, leading: 0.65em, spacing: 0.65em)
  grid(
    columns: (50%, 50%),
    {
      [Dated: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_]
    },
    {
      line(length: 100%, stroke: 0.5pt)
      v(2pt)
      text(weight: "bold")[#judge]
      linebreak()
      [Circuit Court Judge]
    },
  )
}

// ═══════════════════════════════════════════════════════════════
// ORDER ITEM — "IT IS HEREBY ORDERED that..."
// First ordering paragraph in the order
// ═══════════════════════════════════════════════════════════════

#let order-item(body) = {
  set par(first-line-indent: 0.5in, leading: 1.5em, spacing: 1.5em)
  [#text(weight: "bold")[IT IS HEREBY ORDERED] that #body]
}

// ═══════════════════════════════════════════════════════════════
// FURTHER ORDERED — "IT IS FURTHER ORDERED that..."
// Subsequent ordering paragraphs
// ═══════════════════════════════════════════════════════════════

#let further-ordered(body) = {
  v(0.1in)
  set par(first-line-indent: 0.5in, leading: 1.5em, spacing: 1.5em)
  [#text(weight: "bold")[IT IS FURTHER ORDERED] that #body]
}
