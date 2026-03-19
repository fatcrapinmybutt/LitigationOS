# Gotchas — litigation-asset-discovery-engine

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "We don't need formal discovery — we already know what assets exist." | Hidden assets are hidden by definition. MCL 552.401 requires equitable division of ALL marital property. Without formal discovery (interrogatories, production requests, subpoenas), you only know what the opposing party voluntarily disclosed. In Pigors v Watson, undisclosed assets may affect support calculations. | Missing hidden accounts, unreported income, transferred property, or dissipated assets. The court divides only what's before it — undiscovered assets are effectively awarded to the hiding party. MCR 2.302(B) allows broad discovery precisely because parties conceal. |
| 2 | "Bank subpoenas are expensive and time-consuming — the financial affidavit is sufficient." | Financial affidavits are self-reported and unverified. Parties routinely underreport income and omit accounts. MCR 2.305 subpoenas to financial institutions are the ONLY way to verify what actually exists. The cost of a subpoena ($25-50 service fee) is trivial compared to undiscovered assets. | Relying on self-reported financials means accepting the opposing party's version of their wealth. In custody cases, unreported income directly affects child support under MCL 552.517. A single unreported account can change the support calculation by hundreds per month. |
| 3 | "Asset dissipation is hard to prove — it's not worth pursuing." | Dissipation claims under Michigan law require showing: (1) assets existed, (2) they were dissipated, (3) during or in anticipation of divorce. *Sparks v Sparks*, 440 Mich 141, 158 (1992) establishes the framework. Transaction records from banks and credit cards often prove dissipation conclusively. | Unpursued dissipation claims reward bad behavior. If Emily A. Watson transferred, spent, or hid marital assets, failing to trace those transactions means Andrew James Pigors absorbs the loss. The court can credit dissipated assets to the dissipating party's share. |
| 4 | "Real property records are public — no discovery needed." | While deeds and mortgages are public (MCL 565.29, Register of Deeds), they don't show: beneficial ownership through trusts or LLCs, equity positions, encumbrances not yet recorded, or agreements to transfer. Full asset discovery requires both public records AND formal discovery. | Missing beneficial interests, unrecorded liens, or entity-held property. A party can hold significant real property assets through LLCs or trusts that don't appear in a basic deed search. |
| 5 | "We'll address financial discovery later — custody is the priority right now." | Financial status directly impacts custody factors. MCL 722.23(c) considers capacity to provide food, clothing, medical care. MCL 722.23(e) considers permanence of family unit, which depends on financial stability. Delaying financial discovery means arguing custody factors without complete information. | Custody arguments under MCL 722.23(c) and (e) are weakened without financial evidence. Child support calculations under MCL 552.517 require income verification. Delaying asset discovery also allows time for further dissipation or concealment. |

---

## Common Failure Modes

### 1. Incomplete Subpoena Coverage
- **What happens**: Subpoenas sent to known banks but not to all financial institutions where party may hold accounts
- **How to prevent**: Use discovery interrogatories to identify all accounts BEFORE issuing subpoenas; check credit reports for account indicators; cross-reference tax returns for interest/dividend income sources
- **Lane risk**: HIGH for Lane A — incomplete financial picture affects support and property division

### 2. Dissipation Timeline Gap
- **What happens**: Transaction records obtained for wrong date range, missing the period when dissipation occurred
- **How to prevent**: Request records from 2+ years before separation through present; *Sparks v Sparks* looks at dissipation "during or in contemplation of" divorce proceedings
- **Lane risk**: HIGH — dissipation outside the requested date range is invisible

### 3. Entity Ownership Blindness
- **What happens**: Assets held in LLCs, trusts, or corporate entities not discovered because discovery focused only on individual accounts
- **How to prevent**: Interrogatory asking for all business interests, trust beneficiary status, and entity ownership; check Secretary of State records for entity filings
- **Lane risk**: MEDIUM — entity-held assets can be substantial but are commonly overlooked

### 4. Income Imputation Failure
- **What happens**: Opposing party claims reduced income but actual earning capacity is higher, and engine fails to identify imputation arguments
- **How to prevent**: Analyze employment history, education, certifications, and comparable wages; MCL 552.605(2) allows imputation of income to voluntarily unemployed/underemployed parties
- **Lane risk**: HIGH for Lane A — imputed income directly affects child support calculation

### 5. Discovery Sanction Exposure
- **What happens**: Overly broad or harassing discovery requests result in MCR 2.313 sanctions against the requesting party
- **How to prevent**: Tailor discovery to specific, articulable financial issues; use proportionality analysis; avoid duplicative requests
- **Lane risk**: MEDIUM — sanctions waste resources and damage credibility with Judge McNeill

---

## Integration Gotchas

- **litigation-child-support-analyzer** depends on accurate income data from asset discovery — garbage financial data = garbage support calculations
- **litigation-damages-calculator** uses asset data for property division and damages computation
- **litigation-discovery-warfare** handles the procedural aspects of discovery — asset engine focuses on WHAT to discover, discovery warfare handles HOW
- Financial records must be authenticated per MRE 901/902 before use — coordinate with **litigation-evidence-authentication**
- MCR 2.302(B) scope limitations apply — discovery must be relevant and proportional
