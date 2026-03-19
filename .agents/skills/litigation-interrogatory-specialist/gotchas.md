# Gotchas — Interrogatory Specialist

## Anti-Rationalization Matrix

| Trap | What It Looks Like | Why It's Wrong | Correct Approach |
|------|-------------------|----------------|------------------|
| Exceeding interrogatory limits | Drafting 40+ interrogatories and assuming subparts don't count | MCR 2.309(A)(2) limits interrogatories to 20 including subparts in non-complex cases; courts strictly enforce this | Count every subpart as a separate interrogatory; seek leave of court before exceeding the limit |
| Asking compound questions disguised as single | "State the date, time, location, and all witnesses to each incident" as one interrogatory | Each discrete request counts as a separate interrogatory; courts will strike or refuse to compel answers | Break compound questions into discrete, numbered interrogatories within the limit |
| Ignoring objection specificity requirements | Objecting with boilerplate "vague and ambiguous" or "overly broad" without explanation | MCR 2.309(B)(4) requires objections to state the reason with specificity; boilerplate objections are waived | State the precise reason each interrogatory is objectionable and what would make it answerable |
| Missing the 28-day response deadline | Assuming extensions are automatic or that partial responses buy time | MCR 2.309(B)(2) requires answers within 28 days of service; failure to respond waives objections | Calendar the deadline immediately; file for extension before expiration if needed |
| Failing to supplement answers | Treating initial answers as final even when new information emerges | MCR 2.302(E) requires supplementation of prior responses when new information is obtained | Create a system to track which interrogatory answers need updating as case develops |

## Failure Modes
1. **Waived Objections**: Failing to timely object within 28 days results in waiver of all objections. Recovery: File motion for relief from waiver under MCR 2.612(C)(1) showing excusable neglect; success rate is low so prevention is critical.
2. **Incomplete Verification**: Answers not signed under oath by the party (not the attorney). Recovery: Opposing party can move to compel verified answers; re-serve properly verified responses immediately upon discovering the error.
3. **Privilege Log Failure**: Withholding information on privilege grounds without providing a privilege log. Recovery: File amended responses with proper privilege log listing each withheld document, its date, author, recipients, and privilege claimed per MCR 2.302(C).
4. **Sanction Cascade**: Evasive or incomplete answers treated as failure to answer under MCR 2.313(A)(3). Recovery: File amended answers addressing all deficiencies; file motion explaining good faith effort to comply; demonstrate prejudice was minimal.

## Integration Gotchas
- When combining with **litigation-subpoena-engine**, coordinate interrogatory answers with document requests — inconsistencies between interrogatory answers and produced documents are the most common impeachment tool at trial.
- Data flow from **litigation-timeline-forensics** must be cross-referenced against interrogatory answers to identify contradictions — if opposing party's interrogatory answer says "no contact after March" but your timeline shows April communications, flag immediately.
- Michigan-specific pitfall: In 14th Circuit Family Division, discovery disputes are often handled informally by the court — but you still need a formal MCR 2.313 motion to compel on the record to preserve the issue for appeal to COA.
