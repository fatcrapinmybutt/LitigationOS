# Gotchas — litigation-red-team

## Anti-Rationalization Table

This table prevents the most dangerous form of self-deception in litigation:
believing your filing is stronger than it is. Every row represents a real
failure of adversarial self-assessment.

| # | Excuse (Rationalization) | Reality (What Actually Happens) | Consequence |
|---|--------------------------|--------------------------------|-------------|
| 1 | "Our facts are strong — no one could argue against this." | Opposing counsel doesn't need to disprove your facts. They need to reframe them, challenge admissibility, or show they don't support your legal conclusion. Shady Oaks' corporate counsel will attack evidence foundations, not facts. | Strong facts rendered inadmissible or legally insufficient. Motion denied despite compelling narrative. |
| 2 | "The judge will see through opposing counsel's tactics." | Judges rule on what's properly before them. McNeill follows procedure strictly in family cases. Hoopes applies civil standards neutrally. Neither judge will rescue a poorly constructed argument just because the underlying facts are sympathetic. | Substantively correct position fails on procedural or evidentiary grounds. |
| 3 | "We don't need to worry about summary disposition — this is going to trial." | MCR 2.116(C)(8) and (C)(10) motions can eliminate claims before trial. Lane B housing claims are particularly vulnerable to (C)(8) failure-to-state-a-claim attacks. Corporate defendants file these routinely. | Case dismissed before you ever present evidence. No trial occurs. |
| 4 | "Governmental immunity won't apply because they violated constitutional rights." | MCL 691.1407 governmental immunity is broadly applied in Michigan. The gross negligence exception is narrow. Constitutional claims require specific "state action" elements. Lane C convergence claims face the highest dismissal risk. | Federal § 1983 claims dismissed on qualified immunity. State claims dismissed on governmental immunity. |
| 5 | "The volume of our evidence is overwhelming — the other side can't match it." | Volume is not an advantage; it's a liability. Opposing counsel will argue you're burying relevant facts in noise, wasting court resources, or engaging in bad faith. Judges penalize litigants who over-file. | Court imposes page limits. Sanctions for frivolous filing. Judge develops negative impression of credibility. |
| 6 | "Opposing counsel probably won't notice the hearsay issue." | Competent opposing counsel catalogs every hearsay statement in your filing. Corporate defense firms (Lane B) have paralegals whose sole job is this. Even if trial counsel misses it, their motion team won't. | Key evidence excluded at hearing. Entire argument collapses because it rested on inadmissible foundation. |
| 7 | "We can fix it on appeal if the judge gets it wrong." | Appellate review requires preservation. If you don't object, raise the issue, or make the proper record at trial level, it's waived. Michigan Court of Appeals applies harmless error and plain error sparingly. | Issue waived on appeal. Unfavorable ruling becomes permanent. |
| 8 | "The opposing party won't hire a good lawyer for this." | Watson may appear pro se or with limited counsel, but Lane B defendants (Shady Oaks/Alden Global) will retain experienced corporate defense counsel. Lane C (county) has institutional legal resources. Never assume weak opposition. | Outmaneuvered on procedure. Critical motions lost because filings weren't litigation-hardened. |

## Common Red Team Failures

### 1. Confirmation Bias in Review
**Symptom**: Red team finds no significant issues in a filing.
**Cause**: Reviewer unconsciously agrees with the filing's position and cannot adopt adversarial mindset.
**Fix**: Explicitly roleplay as opposing counsel. Write the actual opposing brief, not just a list of theoretical concerns.

### 2. Procedural Blindness
**Symptom**: Red team focuses only on substantive arguments, misses procedural defects.
**Cause**: Procedural attacks are boring but are the most effective means of defeating filings without reaching the merits.
**Fix**: Always run procedural scan (Vectors 1–8) separately and first.

### 3. Underestimating Corporate Defendants
**Symptom**: Red team assumes Lane B opposing counsel will make simple arguments.
**Cause**: Failure to account for resource asymmetry. Corporate defendants file comprehensive response packages.
**Fix**: Lane B red team mode should assume well-resourced, experienced opposing counsel.

### 4. Ignoring Cross-Lane Attacks
**Symptom**: Filing in Lane A is secure, but same facts used in Lane C create vulnerability.
**Cause**: Red team reviews each lane in isolation rather than across the litigation portfolio.
**Fix**: Always run cross-lane contamination check (Vector 26) for any filing that shares facts across lanes.

### 5. Appeal Preservation Blindness
**Symptom**: Red team clears a filing, but the filing fails to preserve appellate issues.
**Cause**: Focus on winning the immediate motion rather than building the appellate record.
**Fix**: Always run appeal preview mode for any significant motion or hearing.

## Michigan-Specific Red Team Traps

- **Vodvarka standard (Lane A)**: Custody modification requires proper cause or change of circumstances *before* reaching best interest factors. If your filing jumps to best interest without clearing Vodvarka, opposing counsel's first attack wins.
- **MCL 554.139 notice (Lane B)**: Housing habitability claims require specific notice to landlord. If notice wasn't properly given, the entire claim fails regardless of conditions.
- **Qualified immunity analysis (Lane C)**: 42 USC § 1983 claims must survive two-prong qualified immunity. First: was a constitutional right violated? Second: was the right "clearly established"? Most Lane C claims fail on prong two.
- **Sanctions risk**: MCR 2.114(D)/(E) sanctions apply to filings without factual and legal basis. Red team must assess whether any argument crosses the sanctions line.
