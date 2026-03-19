# Gotchas — litigation-expert-witness-manager

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "We don't need expert witnesses — the facts speak for themselves." | Many claims require expert testimony to establish elements. In custody cases, psychological evaluations require qualified experts. In housing cases, building code compliance requires inspection experts. In damages cases, financial calculations may require forensic accountants. Without experts, certain claims are unproven as a matter of law. | Claim dismissed for failure to present evidence on essential element. For example, a housing habitability claim (Lane B) without an inspector's testimony may fail because lay testimony about building code compliance is insufficient. Under MRE 702, expert testimony is required when the subject matter is beyond common knowledge. |
| 2 | "Any professional in the field can serve as our expert — credentials don't matter that much." | Under MRE 702 and *Gilbert v DaimlerChrysler Corp*, 470 Mich 749 (2004), Michigan adopted a Daubert-like standard. The expert must be qualified by knowledge, skill, experience, training, or education AND their testimony must be based on reliable principles AND methods reliably applied to the facts. Weak credentials invite Daubert challenges. | Expert excluded under MRE 702 for insufficient qualifications. Opposing counsel files a Daubert motion, the court holds a hearing, and your expert is excluded. Now you've paid the expert's fees AND lost the testimony. Vet qualifications rigorously before retention. |
| 3 | "The expert report is sufficient — the expert doesn't need to testify." | Unless the parties stipulate, the expert must be available for cross-examination. MCR 2.302(B)(4) governs expert discovery. The report alone is hearsay without the expert's testimony. Even in non-jury proceedings, opposing counsel has the right to cross-examine your expert. | Expert report excluded as hearsay because the expert didn't testify. Or the court gives it reduced weight because opposing counsel couldn't cross-examine. Always plan for live (or video) testimony unless you have a stipulation. |
| 4 | "Pro se litigants can't afford experts — the court will understand." | While courts give pro se litigants some latitude, they do NOT waive evidentiary requirements. If expert testimony is required to prove an element, the absence of an expert means the element is unproven regardless of the litigant's resources. Some experts offer reduced fees for pro se parties, and court-appointed experts are possible. | Losing a claim that could have been won because the required expert testimony wasn't presented. The court cannot make up for missing evidence. Explore reduced-fee experts, university programs, and court-appointed options per MRE 706 before giving up. |
| 5 | "Our expert's opinion is unassailable — we don't need to prepare for Daubert challenges." | Every expert is vulnerable to challenge. *Gilbert v DaimlerChrysler* established four factors: (1) testability, (2) peer review, (3) error rate, (4) general acceptance. Opposing counsel will challenge methodology, data sources, assumptions, and the application of principles to facts. Preparation for challenges is essential. | Expert testimony excluded or severely limited by Daubert ruling. The court finds the methodology unreliable, the data insufficient, or the conclusions not properly connected to the facts. Prepare your expert for every potential challenge BEFORE the hearing. |

---

## Common Failure Modes

### 1. Late Expert Disclosure
- **What happens**: Expert not disclosed within discovery timeline, resulting in exclusion
- **How to prevent**: Disclose experts per scheduling order deadline; MCR 2.302(B)(4) requires disclosure of expert identity, opinions, and bases; mark disclosure deadlines in **litigation-filing-countdown**
- **Lane risk**: HIGH — late disclosure = excluded expert = lost testimony

### 2. Insufficient Expert Report
- **What happens**: Expert report is conclusory, lacks methodology explanation, or doesn't connect opinions to case facts
- **How to prevent**: Review report against MRE 702 requirements before submission; ensure report states: qualifications, methodology, data relied upon, opinions, and basis for each opinion
- **Lane risk**: HIGH — weak report invites successful Daubert challenge

### 3. Expert Bias Exposure
- **What happens**: Expert's testimony is undermined because they are perceived as a "hired gun" — too many appearances for one side, financial dependence on litigation work
- **How to prevent**: Vet expert's testimony history; ensure expert has balanced case portfolio; prepare expert for bias cross-examination questions
- **Lane risk**: MEDIUM — bias perception reduces testimony weight

### 4. Failure to Prepare Expert for Cross
- **What happens**: Expert performs well on direct but crumbles on cross-examination, making damaging admissions
- **How to prevent**: Conduct mock cross-examination; review all prior testimony for inconsistencies; identify weaknesses in methodology and prepare explanations
- **Lane risk**: HIGH — a poor cross-examination performance can be worse than no expert at all

---

## Integration Gotchas

- **litigation-evidence-authentication** handles foundation for expert reports and exhibits
- **litigation-damages-calculator** coordinates with financial experts on damages computation
- **litigation-deposition-strategist** prepares for expert depositions (both your experts and opposing experts)
- **litigation-fee-petition-engine** tracks expert costs as recoverable expenses
- Expert disclosure deadlines must be tracked by **litigation-filing-countdown** — missing disclosure deadline = exclusion
