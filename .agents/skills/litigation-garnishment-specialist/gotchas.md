# Gotchas — litigation-garnishment-specialist

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "Once we have a judgment, collecting is straightforward — just garnish their wages." | Garnishment has complex procedural requirements under MCL 600.4001-4065 and MCR 3.101. You must: file a verified statement, obtain a writ, serve it properly, respect federal and state exemptions (25% disposable earnings cap under 15 USC § 1673), and navigate the garnishee's obligations. Missing any step can void the garnishment. | Failed garnishment attempt that alerts the debtor to move assets. Improper garnishment exposes YOU to liability for wrongful garnishment. The garnishee (employer/bank) may refuse to comply with a defective writ, and you've wasted filing fees and time. |
| 2 | "We can garnish 100% of their bank account — the money is owed to us." | Bank account garnishment is subject to exemptions. Federal benefits (Social Security, SSI, VA benefits) are FULLY exempt under 42 USC § 407, 38 USC § 5301. Michigan exempts certain amounts needed for basic living expenses. The garnishee bank must review the account for exempt funds and cannot freeze exempt amounts. | Garnishing exempt funds = federal law violation. Banks that wrongfully freeze Social Security or VA benefits face federal penalties. A garnishment that sweeps exempt funds will be reversed by the court, and you may be ordered to pay the debtor's costs for the wrongful garnishment. |
| 3 | "Child support garnishment follows the same rules as regular garnishment." | Child support garnishment has SEPARATE and MORE FAVORABLE rules for the creditor. MCL 552.625f allows income withholding that exceeds the 25% Consumer Credit Protection Act limit — up to 50% of disposable earnings (60% if no current spouse/dependents, 65% if over 12 weeks in arrears). Support garnishment has priority over other garnishments. | Using regular garnishment limits when you're entitled to the higher child support limits = leaving money on the table. Conversely, applying child support limits to a non-support judgment = wrongful garnishment. The type of underlying judgment determines which limits apply. |
| 4 | "The garnishee will just comply — there's no need to follow up." | Garnishees have 28 days to respond to the writ (MCR 3.101(G)). They may: comply, object, claim the debtor has no property, or ignore the writ entirely. Each response requires different follow-up. An ignored writ requires a motion for default against the garnishee. An objection requires a hearing. | Assuming compliance and doing nothing means months pass with no collection. Employers change payroll procedures, banks process garnishments inconsistently, and garnishees who object can delay collection significantly. Active follow-up on EVERY garnishment is essential. |
| 5 | "Garnishment is the only post-judgment collection tool — if it doesn't work, we're stuck." | Michigan provides multiple collection tools: wage garnishment (MCL 600.4012), bank garnishment (MCL 600.4011), periodic garnishment (MCL 600.4061), judgment liens on real property (MCL 600.2801), creditor's examination (MCR 2.621), and execution on personal property (MCL 600.6001). Use them in combination. | Limiting yourself to one collection method when others are more effective. A debtor may have no wages to garnish but significant bank deposits, or no bank accounts but real property equity. Effective collection requires using ALL available tools. |

---

## Common Failure Modes

### 1. Exemption Calculation Error
- **What happens**: Garnishment writ doesn't account for federal/state exemptions, leading to over-garnishment that the court reverses
- **How to prevent**: Calculate disposable earnings correctly; apply the 25% federal cap (15 USC § 1673) or the state formula, whichever protects MORE of the debtor's earnings; identify exempt income sources
- **Lane risk**: HIGH — wrongful garnishment exposes you to liability and court sanctions

### 2. Improper Service of Writ
- **What happens**: Writ not properly served on garnishee, making the entire garnishment void
- **How to prevent**: Serve writ per MCR 3.101(D) — on the garnishee's registered agent (corporations) or personally (individuals); file proof of service; serve copy on judgment debtor
- **Lane risk**: HIGH — defective service = void garnishment = start over

### 3. Failure to Track Garnishee Response
- **What happens**: Garnishee doesn't respond within 28 days and the creditor doesn't notice, losing collection momentum
- **How to prevent**: Calendar the 28-day response deadline; if no response, immediately file motion for default against garnishee per MCR 3.101(H); follow up proactively
- **Lane risk**: MEDIUM — delay allows debtor to move assets

### 4. Wrong Garnishment Type
- **What happens**: Using periodic garnishment when a one-time bank garnishment would be more effective, or vice versa
- **How to prevent**: Analyze the debtor's assets: wages → periodic garnishment (MCL 600.4061); bank accounts → non-periodic garnishment (MCL 600.4011); match the tool to the asset type
- **Lane risk**: MEDIUM — wrong tool = inefficient collection

### 5. Failure to Claim Priority
- **What happens**: Multiple creditors garnish the same debtor, and your garnishment doesn't receive its proper priority
- **How to prevent**: Child support garnishment has statutory priority over other garnishments (MCL 552.625f); first-in-time garnishments generally have priority; monitor for competing garnishments
- **Lane risk**: MEDIUM — lost priority means reduced or delayed collection

---

## Integration Gotchas

- **litigation-default-judgment-engine** obtains the judgment that garnishment enforces — the judgment amount determines the garnishment scope
- **litigation-damages-calculator** calculates the total judgment amount including prejudgment interest that the garnishment must collect
- **litigation-asset-discovery-engine** identifies WHERE the debtor has assets to garnish — you must know the employer and bank before garnishing
- **litigation-child-support-analyzer** determines whether child support priority garnishment limits apply
- **litigation-filing-packager** assembles the garnishment papers (verified statement, writ, disclosure) for filing
- SCAO form MC 14 (garnishment) must be used — check current form version before filing
