# Gotchas — litigation-default-judgment-engine

## Anti-Rationalization Table

| # | Excuse (The Lie) | Reality (The Truth) | Consequence |
|---|-----------------|---------------------|-------------|
| 1 | "If they don't respond, we automatically get everything we asked for." | Default judgment is a TWO-STEP process under MCR 2.603. Step 1: Entry of default (clerk's ministerial act). Step 2: Default judgment (requires court hearing for unliquidated damages). The court still evaluates damages and can award LESS than requested. The default admits liability, not the damages amount. | Expecting automatic full recovery and being shocked when the court reduces damages at the prove-up hearing. In Lane B housing claims, the court may find the damages calculation excessive even though liability is established. Always prepare a strong damages presentation for the prove-up hearing. |
| 2 | "Service was probably good enough — they knew about the case." | Service must strictly comply with MCR 2.105 (personal service), MCR 2.106 (substituted service), or MCR 2.107 (service by publication). "Probably" good service is the #1 basis for setting aside a default under MCR 2.603(D). If service was defective, the entire default judgment is void — not voidable, VOID. | A default judgment obtained on defective service can be attacked at any time — there is no time limit for challenging void judgments. *Shawl v Spence*, 236 Mich App 120 (1999). Opposing counsel will comb service records looking for defects when a default is entered. |
| 3 | "Once we have the default, they can't do anything about it." | MCR 2.603(D) allows the court to set aside a default for "good cause" and a default judgment for "good cause and an affidavit of meritorious defense." Courts liberally set aside defaults because there is a strong preference for adjudication on the merits. *Alken-Ziegler v Waterbury Headers*, 461 Mich 219 (1999). | Counting on the default as final when it's likely to be set aside wastes strategic momentum. If the default is set aside, you've spent time and resources on default proceedings instead of building your case for trial. Know the likelihood of set-aside before pursuing default strategy. |
| 4 | "We don't need to worry about military service — this isn't a military case." | The Servicemembers Civil Relief Act (50 USC § 3931) requires an affidavit of non-military service before ANY default judgment. Failure to comply makes the judgment voidable. Even if you're certain the defendant isn't military, the affidavit is REQUIRED. SCRA violations carry serious penalties. | Default judgment entered without SCRA affidavit is subject to being set aside and may expose the filing party to penalties. Always file the non-military affidavit (SCAO form MC 99, or federal equivalent) with the default judgment application. |
| 5 | "Default judgment is a quick victory — it's always worth pursuing." | Default judgment strategy must account for: collectability (is the judgment worth the paper?), set-aside risk (will the court undo it?), strategic cost (does pursuing default delay other case actions?), and relationship impact (in family cases, aggressive defaults escalate conflict). | In Lane A custody cases, pursuing default against a co-parent escalates conflict that Judge McNeill weighs under MCL 722.23(j). In Lane B, a judgment against an insolvent defendant is worthless. Default is a tool, not always the best one. |

---

## Common Failure Modes

### 1. Defective Service Foundation
- **What happens**: Default entered based on service that doesn't strictly comply with MCR 2.105/2.106, making the entire default void
- **How to prevent**: Use professional process server; obtain detailed proof of service with descriptions; verify service address is correct; consider alternative service order if personal service fails
- **Lane risk**: CRITICAL — void service = void default, no time limit to challenge

### 2. Premature Default Request
- **What happens**: Default requested before the response deadline has actually expired (21 days for complaint, 28 days for some answers)
- **How to prevent**: Calculate response deadline precisely from date of service (not filing); account for additional time for service by mail (MCR 2.107(C)(3) — add 3 days)
- **Lane risk**: HIGH — premature default is improper and will be set aside

### 3. Failure to Prepare Prove-Up Hearing
- **What happens**: Default entered on liability, but damages hearing is unprepared; court awards minimal damages
- **How to prevent**: Prepare damages prove-up as thoroughly as a trial; bring all evidence, calculations, and testimony; the court is the factfinder on damages even in default
- **Lane risk**: HIGH for Lane B — housing damages require specific proof of each category

### 4. Missing SCRA Affidavit
- **What happens**: Default judgment entered without Servicemembers Civil Relief Act non-military affidavit, making judgment voidable
- **How to prevent**: ALWAYS file SCRA affidavit; check Department of Defense database for military status; include affidavit with default judgment application
- **Lane risk**: MEDIUM — easily prevented but commonly forgotten

---

## Integration Gotchas

- **litigation-damages-calculator** provides the damages framework for the prove-up hearing — essential for meaningful default judgments
- **litigation-service-engine** verifies proper service before default is requested — defective service = void default
- **litigation-filing-packager** assembles the default judgment application package
- **litigation-garnishment-specialist** handles post-judgment enforcement of default judgments
- MCR 2.603 procedural requirements must be strictly followed — the clerk will reject non-compliant applications
