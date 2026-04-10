// _test-order.typ — Compilation test for proposed-order and exhibit-cover
// Compile: typst compile _test-order.typ _test-order.pdf

#import "proposed-order.typ": proposed-order, order-item, further-ordered
#import "exhibit-cover.typ": exhibit-cover

#show: proposed-order.with(
  document-title: "Order Restoring Parenting Time",
)

At a session of said Court held in the Courthouse in the City of Muskegon, County of Muskegon, State of Michigan.

The Court having reviewed Plaintiff's Emergency Motion to Restore Parenting Time, the response thereto, and the file in this matter, and the Court being otherwise fully advised in the premises,

#order-item[
  Plaintiff Andrew James Pigors shall have supervised parenting time with the minor child, L.D.W., commencing within seven (7) days of the date of this Order, under a schedule to be arranged through the Muskegon County Friend of the Court.
]

#further-ordered[
  An evidentiary hearing on the issue of parenting time and custody modification shall be held within fourteen (14) days of the date of this Order.
]

#further-ordered[
  The Friend of the Court shall investigate and provide a recommendation to the Court regarding an appropriate parenting time schedule within thirty (30) days.
]

#further-ordered[
  All prior orders not inconsistent with this Order shall remain in full force and effect.
]
