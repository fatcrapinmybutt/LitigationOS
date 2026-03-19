# Gotchas — litigation-authority-validator

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "The citation is probably still good — it's only a few years old." | Cases get overruled, statutes get amended, and rules get modified without warning. A 2020 case can be bad law by 2024. There is no "probably" in citation work. | Citing overruled authority = sanctions under MCR 1.109(E), malpractice exposure, instant credibility loss with the judge. In custody cases (Lane A), Judge McNeill will question every other citation in your brief. |
| 2 | "Pinpoint cites aren't necessary — the judge will find the relevant passage." | Judges read dozens of briefs. They will NOT search for your proposition. MCR 7.212(C)(7) requires pinpoint citations in appellate briefs, and trial courts expect the same professionalism. | Missing pinpoints = the court ignores your authority. In summary disposition motions (Lane B, Judge Hoopes), unsupported propositions are treated as conceded. |
| 3 | "I'll verify the citations before filing — right now I just need a draft." | Draft citations become filed citations. Every draft should be citation-accurate because last-minute verification gets skipped under deadline pressure. The OMEGA pipeline (Phase 14) catches this, but Phase 12 should have clean authority already. | Unverified citations that slip into filed documents cannot be recalled. The 14th Circuit has no "oops" procedure. Opposing counsel WILL Shepardize your brief. |
| 4 | "An unpublished case is fine to cite — it supports our argument perfectly." | Under MCR 7.215(C)(1), unpublished opinions are not precedentially binding. You MUST disclose unpublished status and cannot rely on them as primary authority. Using them without disclosure is sanctionable. | Judge McNeill and Judge Hoopes both follow this rule strictly. Citing unpublished opinions as if they were binding authority undermines your entire brief's credibility. |
| 5 | "The authority chain doesn't need to be complete — one good case is enough." | Michigan courts expect thorough authority support. A single case can be distinguished; a complete chain (statute + binding case + supporting case + pinpoint) is much harder to attack. Incomplete chains signal weak research. | Opposing counsel will distinguish your single authority and argue your position is unsupported. Judge Hoopes (Lane B) is known for requiring comprehensive authority in CZ cases. |
| 6 | "Federal authority works fine for this state-law issue." | Federal courts interpreting Michigan law are persuasive, not binding. State courts can and do disagree with federal interpretations. Always lead with Michigan authority. | If your primary authority is federal on a state-law question, the court may treat your argument as unsupported. This is especially dangerous in Lane A custody matters where Michigan has its own comprehensive statutory scheme (MCL 722.21-722.31). |
| 7 | "The citation format is close enough — substance matters more than form." | Citation format IS substance. Wrong reporter, wrong volume, wrong page = the court cannot verify your authority. Michigan uses its own citation format that differs from Bluebook in key respects. | Incorrect format signals carelessness. If the court can't find your case at the cited location, they assume you fabricated it. Format errors compound — one sloppy cite makes the court scrutinize all your cites. |

---

## Common Failure Modes

### 1. Stale Authority
- **What happens**: Statute amended, case overruled, rule modified
- **How to prevent**: Run currency check on EVERY citation before filing
- **Lane risk**: HIGH for Lane A (custody law changes frequently)

### 2. Cross-Lane Citation Contamination
- **What happens**: Authority appropriate for Lane B (housing) cited in Lane A (custody) filing
- **How to prevent**: Tag every authority with lane assignment; validate lane match at filing
- **Lane risk**: HIGH for Lane C (convergence creates temptation to mix)

### 3. Phantom Citations
- **What happens**: LLM generates plausible but non-existent citations
- **How to prevent**: EVERY citation must be verified against actual reporter volumes
- **Lane risk**: CRITICAL for all lanes — this is the #1 AI-assisted litigation risk

### 4. Missing Parentheticals
- **What happens**: String citations without context leave court guessing
- **How to prevent**: Require parenthetical for every case citation in authority chain
- **Lane risk**: MEDIUM — improves persuasiveness but not always required

### 5. Jurisdiction Mismatch
- **What happens**: Out-of-state authority cited without noting persuasive-only status
- **How to prevent**: Flag all non-Michigan authority; require Michigan primary authority first
- **Lane risk**: HIGH for Lane B (housing law varies significantly by state)

---

## Integration Gotchas

- **litigation-filing-packager** expects validated authority lists — DO NOT pass unvalidated citations
- **litigation-appellate-strategist** requires pinpoint accuracy — appellate courts are strictest
- **litigation-convergence-orchestrator** counts authority gaps as DNEW items — incomplete chains lower quality score
- **litigation-brain-spec** may contain authorities from initial research that have since been superseded — always re-validate
