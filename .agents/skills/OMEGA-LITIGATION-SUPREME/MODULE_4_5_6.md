## ═══════════════════════════════════════════
## MODULE 4: FILING FACTORY (Court Document Generation)
## ═══════════════════════════════════════════

> **Absorbs 22 skills:** litigation-filing-architect, litigation-brief-writer, litigation-complaint-drafter,
> litigation-motion-practice, litigation-emergency-motion-engine, litigation-service-engine,
> litigation-pro-se-guardian, litigation-sanctions-engine, litigation-contempt-specialist,
> litigation-default-judgment-engine, litigation-summary-judgment-engine, litigation-lawsuit-forge,
> litigation-damages-calculator, litigation-harm-quantifier, litigation-fee-petition-engine

---

### Phase F-1: Action Selection

Every filing originates from a numbered **Action ID** within one of six lanes. The Filing Factory
never generates a document without a lane assignment and action ID — this is the atomic unit of work.

#### Action ID Registry by Lane

| Lane | Range | Examples |
|------|-------|---------|
| **A — Custody** | A1–A35 | A1: Custody modification, A5: Parenting time enforcement, A12: Emergency custody, A18: FOC objection, A22: Contempt (parenting time), A30: Motion to compel discovery |
| **B — Housing** | B1–B14 | B1: Complaint (breach of habitability), B4: Demand for repairs, B7: Rent escrow, B10: Counterclaim, B14: Motion for summary disposition |
| **C — Convergence** | C1–C7 | C1: Convergence brief (cross-lane), C3: Judicial misconduct + custody nexus, C5: Pattern-of-harm synthesis, C7: Omnibus motion |
| **D — PPO** | D1–D10 | D1: PPO petition (MCL 600.2950), D3: PPO modification, D5: PPO violation enforcement, D8: Motion to terminate PPO, D10: Appeal of PPO denial |
| **E — Misconduct** | E1–E8 | E1: JTC request for investigation, E3: Formal complaint, E5: Mandamus petition, E7: Disqualification motion (MCR 2.003), E8: Federal §1983 complaint |
| **F — Appellate** | F1–F12 | F1: Claim of appeal, F3: Application for leave (COA), F5: Emergency stay, F7: Leave to MSC, F10: Amicus brief, F12: Motion for reconsideration |

#### Decision Tree — Selecting the Optimal Filing Vehicle

```
INPUT: Triggering event + lane assignment + urgency level
  │
  ├─ Is there immediate irreparable harm?
  │   ├─ YES → Emergency vehicle (ex parte motion / TRO / emergency custody)
  │   │        Time target: same-day filing
  │   └─ NO ──┐
  │            │
  ├─ Is there a pending deadline or court order requiring response?
  │   ├─ YES → Responsive vehicle (response brief / objection / counter-motion)
  │   │        Time target: within MCR deadline (typically 14-21 days)
  │   └─ NO ──┐
  │            │
  ├─ Is the goal to initiate new relief?
  │   ├─ YES → Initiating vehicle (motion / petition / complaint)
  │   └─ NO → Enforcement vehicle (contempt / sanctions / motion to compel)
  │
  └─ CROSS-CHECK: Does this action touch multiple lanes?
      ├─ YES → Route through Lane C convergence for unified strategy
      └─ NO  → Proceed in single lane
```

---

### Phase F-2: Document Architecture

#### VehicleMap Schema

Every filing action resolves to a **VehicleMap** — a structured packet of documents that travel together.

```
VehicleMap {
  action_id:        "A22"                           // Action identifier
  lane:             "A"                              // Case lane
  primary_vehicle:  "Motion for Contempt"            // The main filing
  supporting:       ["Brief in Support", "Affidavit of Andrew Pigors"]
  exhibits:         ["Exhibit A — Text Messages", "Exhibit B — Parenting Time Log"]
  service:          ["Proof of Service (MC 12)"]
  administrative:   ["Fee Waiver (MC 20)", "Filing Checklist"]
  proposed_order:   "Proposed Order Finding Contempt"
  court:            "14th Circuit Court, Family Division"
  judge:            "Hon. Jenny L. McNeill"
}
```

#### Standard Filing Packet Structure

Every packet follows this numbered sequence — no exceptions:

| Position | Document | Required | Notes |
|----------|----------|----------|-------|
| `00` | Cover Sheet | If required by court | JS 44 (federal), local cover (state) |
| `01` | Motion / Petition / Complaint | **Always** | The primary vehicle |
| `02` | Brief in Support | Most motions | IRAC/CREAC/TEC argument |
| `03` | Affidavit / Verification | When facts need sworn support | MCR 2.119(B) requires affidavit for most motions |
| `04` | Exhibits | When evidence supports | Bates-stamped, tabbed, indexed |
| `05` | Proposed Order | **Always for motions** | MCR 2.119(A)(2) — must accompany motion |
| `06` | Certificate / Proof of Service | **Always** | MC 12 form or equivalent |
| `07` | Fee Waiver (MC 20/20a) | If applicable | Attach income verification |
| `08` | Filing Checklist | Internal QA | Not filed — tracks completeness |

---

### Phase F-3: Argument Construction

#### Three Argument Structures

**IRAC — Simple, Single-Issue Motions**
```
Issue:        One sentence framing the legal question
Rule:         Controlling statute + binding case law (cite Michigan authority first)
Application:  Apply rule to specific facts (cite exhibit, date, Bates number)
Conclusion:   State the relief requested in one sentence
```
Use for: routine motions (adjournment, extension of time, simple discovery motions)

**CREAC — Complex, Multi-Factor Analysis**
```
Conclusion:   Lead with the answer — tell the court what you want immediately
Rule:         Comprehensive rule synthesis (statute + case law + MCR)
Explanation:  How courts have applied this rule in analogous cases
Application:  Detailed fact-to-element mapping for each factor
Conclusion:   Restate with emphasis on strongest element
```
Use for: custody modification (12 best-interest factors), summary disposition, contempt

**TEC — Narrative / Equity Arguments**
```
Theme:        Establish the narrative frame (e.g., "pattern of systematic interference")
Evidence:     Walk through facts chronologically — let the story build
Conclusion:   Connect the narrative to the legal standard and requested relief
```
Use for: emergency motions, opening statements, appellate arguments, JTC complaints

#### 15 Persuasion Techniques (deploy selectively — never stack more than 4 per filing)

| # | Technique | Deployment | Example |
|---|-----------|------------|---------|
| 1 | **Primacy** | Strongest argument first | Lead brief with most compelling violation |
| 2 | **Recency** | Second-strongest last | Close with the "and furthermore" punch |
| 3 | **Rule of Three** | Group in threes | "Three separate violations on three dates" |
| 4 | **Anchoring** | Set the frame early | Open with the controlling standard |
| 5 | **Framing** | Choose the lens | "This is a safety case, not a scheduling dispute" |
| 6 | **Narrative** | Tell a story | Chronological fact pattern with human impact |
| 7 | **Concession-and-Refute** | Acknowledge weakness, then defeat it | "While Defendant argues X, the record shows Y" |
| 8 | **Repetition** | Key phrase through brief | "The child's best interest requires..." (recurring) |
| 9 | **Contrast** | Juxtapose behaviors | Plaintiff's compliance vs. Defendant's violations |
| 10 | **Understatement** | Let facts speak | State egregious facts flatly — impact is stronger |
| 11 | **Authority Stacking** | Multiple citations | Cite 3+ authorities for key propositions |
| 12 | **Rhetorical Question** | Sparingly, in briefs | "If not contempt, then what remedy remains?" |
| 13 | **Parallel Structure** | Syntactic repetition | "Defendant failed to... Defendant refused to... Defendant ignored..." |
| 14 | **Negative Pregnant** | Strategic admission language | Craft RFA responses that admit damaging inferences |
| 15 | **Building Momentum** | Escalating pattern | Start small, build to the most serious violation |

---

### Phase F-4: Court-Specific Compliance

#### 14th Circuit Court — Muskegon County (Trial Level)

- **Caption format**: MCR 2.113(C) — case number, division, judge, parties
- **Page limits**: No hard local limit; briefs should target ≤25 pages
- **Filing**: MiFile e-filing (mandatory). Paper courtesy copies if >25 pages
- **Service**: MCR 2.107 — serve opposing counsel/party within required timeframe
- **Motions**: MCR 2.119 — 14-day notice for hearing; affidavit + proposed order required
- **Parenting time**: MCR 3.218 — FOC objection within 21 days of recommendation

#### Michigan Court of Appeals (COA)

- **Claim of Appeal**: MCR 7.204 — file within 21 days of final order (42 days for some)
- **Application for Leave**: MCR 7.205 — within 21 days; requires supporting brief
- **Brief format**: MCR 7.212 — **50-page limit**, table of contents, table of authorities
- **Appendix**: Tabs A–H minimum (A=order appealed, B=register of actions, C=relevant orders, etc.)
- **Filing**: TrueFiling electronic system. One original + copies per MCR
- **Emergency motions**: MCR 7.211(C)(6) — must explain irreparable harm and urgency
- **Oral argument**: MCR 7.214 — request in brief; granted at panel discretion

#### Michigan Supreme Court (MSC)

- **Leave application**: MCR 7.305 — **RED cover**. 50-page limit
- **Bypass application**: MCR 7.303 — direct appeal skipping COA (rare, extraordinary cases)
- **Amicus curiae**: MCR 7.306 — leave required before filing
- **Timeline**: File within 56 days of COA decision

#### Federal — Western District of Michigan (WDMI)

- **Complaint**: FRCP 8 (short and plain statement), FRCP 10 (form of pleadings)
- **Cover sheet**: JS 44 Civil Cover Sheet required
- **Service**: FRCP 4 — 90-day service deadline; waiver of service option
- **Filing**: CM/ECF electronic filing. PACER for docket access
- **§1983 claims**: 42 USC §1983 — must plead deprivation of federal right under color of state law

#### Judicial Tenure Commission (JTC)

- **Format**: MCR 9.104–9.205 — formal complaint structure
- **Filing**: Paper filing to JTC, 3034 W. Grand Blvd, Suite 8-450, Detroit, MI 48202
- **Contents**: Specific acts of misconduct with dates, supporting evidence, witnesses
- **Standard**: "Conduct clearly prejudicial to the administration of justice"

---

### Phase F-5: Pro Se Compliance Layer

#### Haines v. Kerner Leniency Doctrine (404 U.S. 519, 1972)

Pro se filings are held to "less stringent standards than formal pleadings drafted by lawyers."
This does NOT mean sloppy work — it means the court should construe filings liberally. The Filing
Factory exploits this by producing **attorney-quality filings** from a pro se litigant, which
creates a powerful credibility advantage.

#### Tone Calibration Protocol

```
ALWAYS:  Measured, factual, respectful to the court
NEVER:   Angry, accusatory toward the judge, argumentative in affidavits
TARGET:  "Respectful but firm" — cite facts, let the record speak
SIGNAL:  "Plaintiff respectfully requests..." / "The record demonstrates..."
AVOID:   "The Court erroneously..." → USE: "Plaintiff respectfully submits that..."
```

#### Fee Waiver (MC 20 / MC 20a)

- MC 20: Affidavit of Indigency and Request to Waive Fees
- MC 20a: Supplemental attachment for household financial details
- Attach proof of income (pay stubs, benefit statements, tax return)
- Renewal: re-file if circumstances change or for new case filings

#### Length Discipline by Filing Type

| Filing Type | Target Length | Hard Limit |
|-------------|-------------|------------|
| Simple motion | 3–5 pages | 10 pages |
| Brief in support | 10–20 pages | 25 pages (circuit), 50 pages (COA/MSC) |
| Emergency motion | 5–8 pages | 15 pages |
| Complaint / petition | 8–15 pages | 30 pages |
| Appellate brief | 25–40 pages | 50 pages (MCR 7.212) |

---

### Phase F-6: Service & Filing

#### Process Service Methods (MCR 2.105)

| Method | Rule | Use When |
|--------|------|----------|
| Personal service | MCR 2.105(A)(1) | Default — hand delivery to party |
| Registered mail | MCR 2.105(A)(2) | Alternative — return receipt requested |
| Substituted service | MCR 2.105(A)(3) | At dwelling with suitable-age person |
| Publication | MCR 2.106 | Cannot locate party after due diligence |
| E-service | MCR 2.107(C)(4) | After first service, if consented or ordered |

#### Proof of Service — MC 12

Every filed document MUST have proof of service. MC 12 form requires:
- Name and address of person served
- Method of service (personal, mail, e-service)
- Date and time of service
- Signature of person who served

#### Electronic Filing Systems

| Court | System | Notes |
|-------|--------|-------|
| Michigan trial courts | **MiFile** | Mandatory e-filing. Upload PDF. Pay fees or attach MC 20 |
| Michigan COA | **TrueFiling** | Create account. Upload brief + appendix as separate PDFs |
| Michigan Supreme Court | **TrueFiling** | Same system as COA |
| Federal WDMI | **CM/ECF** | Register for attorney/pro se access. PACER for viewing |
| JTC | **Paper filing** | Mail to Detroit office. No e-filing available |

---

## ═══════════════════════════════════════════
## MODULE 5: STRATEGIC COMMAND & WARFARE
## ═══════════════════════════════════════════

> **Absorbs:** litigation-case-strategy-architect, litigation-convergence-orchestrator,
> litigation-discovery-warfare, litigation-settlement-analyzer, litigation-mediation-strategist,
> litigation-deposition-strategist, litigation-red-team, litigation-warfare-engine

---

### Phase S-1: Strategic Assessment

#### Six-Lane Dependency Graph

Lanes are NOT independent — actions in one lane create leverage, prerequisites, or risks in others.
The canonical priority order reflects this dependency chain:

```
E (Misconduct) → D (PPO) → F (Appellate) → A (Custody) → B (Housing) → C (Convergence)
      │               │            │              │              │              │
      │               │            │              │              │              └─ Synthesizes all
      │               │            │              └──────────────┴─ Core relief
      │               │            └─ Preserves issues for higher courts
      │               └─ Immediate safety protection
      └─ Removes biased decision-maker (unlocks all downstream lanes)
```

**Why E-first:** If the judge is biased, every order she enters is tainted. Disqualification
or JTC complaint creates pressure that shifts ALL downstream outcomes. If E succeeds, lanes
D/F/A recalculate entirely.

#### Filing Wave Architecture

Filings deploy in coordinated waves, not random individual filings:

| Wave | Timing | Filings | Strategic Purpose |
|------|--------|---------|-------------------|
| **Wave 1** | Immediate | E7 (disqualification), D1 (PPO if needed) | Secure safety + challenge judge |
| **Wave 2** | Week 1–2 | F1/F3 (appeal), A1 (custody mod) | Preserve issues + initiate core relief |
| **Wave 3** | Week 3–4 | A5 (enforcement), A22 (contempt) | Pressure compliance |
| **Wave 4** | Month 2 | Discovery package (A30, interrogatories, RFPs) | Build factual record |
| **Wave 5** | Month 3–4 | B1 (housing complaint), C1 (convergence brief) | Expand pressure |
| **Wave 6** | Ongoing | Responsive filings as needed | Maintain momentum |

---

### Phase S-2: Game Theory Engine

#### Opponent Modeling — Watson Response Prediction

Model the opponent's likely responses to each filing action:

```
FILING ACTION          → LIKELY RESPONSE           → OUR COUNTER
──────────────────────────────────────────────────────────────────
Custody modification   → Deny all, blame Plaintiff → Evidence arsenal (texts, logs)
Contempt motion        → Claim compliance/excuses  → Date-specific violation log
Discovery requests     → Delay/obstruct            → Motion to compel + sanctions
PPO petition           → Counter-PPO filing         → Documented pattern vs. isolated claim
Disqualification       → Judge denies (self-interest) → Mandamus / appeal of denial
Emergency motion       → Oppose urgency claim      → Specific harm documentation
```

#### Sequential Pressure Escalation

```
Level 1: Filing + service (puts opponent on notice)
Level 2: Discovery (forces disclosure under oath)
Level 3: Motions to compel (court-ordered compliance)
Level 4: Sanctions (financial consequences for obstruction)
Level 5: Contempt (incarceration threat for willful violation)
Level 6: Appellate review (higher court oversight)
Level 7: Federal civil rights (§1983 — removes state-court shield)
```

Each level creates a **commitment problem** for the opponent: responding costs resources,
not responding creates defaults and adverse inferences.

#### Nash Equilibrium Settlement Zone

```
BATNA (Best Alternative to Negotiated Agreement):
  Plaintiff: Trial on custody + contempt → uncertain but evidence-heavy
  Defendant: Trial exposure + potential sanctions + contempt finding

WATNA (Worst Alternative):
  Plaintiff: Status quo continues, child harm persists
  Defendant: Custody transfer + contempt sanctions + costs

Settlement zone exists where:
  Defendant's cost of settlement < Defendant's expected trial cost
  Plaintiff's settlement gain > Plaintiff's expected trial gain minus costs
```

---

### Phase S-3: Discovery Warfare

#### Interrogatory Design (35-Question Limit — MCR 2.309(A)(2))

Every interrogatory must serve a strategic purpose. Categories:

| Category | Count | Purpose |
|----------|-------|---------|
| Timeline establishment | 5–7 | Pin opponent to dates/facts under oath |
| Relationship/household | 3–5 | Identify cohabitants, overnight guests, caregivers |
| Financial disclosure | 5–7 | Income, expenses, hidden assets, support |
| Parenting conduct | 5–7 | Specific interference incidents, communication |
| Third-party witnesses | 3–5 | Identify witnesses to lock down deposition targets |
| Admissions setup | 3–5 | Questions designed to contradict expected RFA denials |

#### Request for Production (RFP) Targeting

Target categories: text messages, emails, social media posts, financial records, medical records
(with HIPAA release), school records, phone call logs, photos/videos from key dates.

**RFP design principle:** Request narrow date ranges around known incidents. Broad requests
invite objections; targeted requests are harder to resist.

#### Request for Admissions (RFA) — Admissions Traps

RFAs are the most powerful discovery tool because unanswered RFAs are **deemed admitted**
(MCR 2.312(B)(1)). Design RFAs in chains:

```
RFA 1: "Admit that on [date], you received Plaintiff's text message at [time]."
RFA 2: "Admit that you did not respond to said text message within 24 hours."
RFA 3: "Admit that the text message requested make-up parenting time."
RFA 4: "Admit that no make-up parenting time was provided."
→ Chain establishes interference pattern even if opponent ignores RFAs
```

#### Motion to Compel Escalation (MCR 2.313)

```
Step 1: Serve discovery → wait response deadline (28 days MCR 2.309)
Step 2: Send meet-and-confer letter (required before filing motion)
Step 3: File Motion to Compel (MCR 2.313(A)) + request costs
Step 4: If still non-compliant → Motion for Sanctions (MCR 2.313(B))
Step 5: If continued non-compliance → Motion for Default / Evidence Preclusion
```

---

### Phase S-4: Red Team Protocol

#### 25 Attack Vectors (anticipate and pre-empt)

| # | Attack Vector | Risk | Pre-Emption |
|---|--------------|------|-------------|
| 1 | Motion to strike (improper pleading) | Medium | Strict MCR compliance in every filing |
| 2 | Standing challenge | Low | Establish standing in opening paragraph |
| 3 | Laches (unreasonable delay) | Medium | Document reasons for any delay; file promptly |
| 4 | Hearsay objections to exhibits | High | Authenticate under MRE 803/804 exceptions |
| 5 | Mootness | Low | Show ongoing harm or capable-of-repetition |
| 6 | Rooker-Feldman (federal review of state judgment) | High (federal) | Frame as independent §1983 claim, not appeal |
| 7 | Res judicata / collateral estoppel | Medium | Distinguish prior rulings on different facts |
| 8 | Failure to exhaust (JTC/admin) | Medium | Show exhaustion or futility exception |
| 9 | Unclean hands | Medium | Demonstrate full compliance with all orders |
| 10 | Frivolous filing (MCR 2.114 sanctions) | Low | Every filing backed by evidence + authority |
| 11 | Improper service | Medium | Meticulous MC 12 compliance, keep receipts |
| 12 | Timeliness challenge | High | Calendar ALL deadlines, file early |
| 13 | Failure to state a claim | Medium | Plead every element with factual support |
| 14 | Insufficient evidence | Medium | Attach exhibits for every factual claim |
| 15 | Bias claim against Plaintiff | Low | Maintain measured, respectful tone throughout |
| 16 | Motion to dismiss (MCR 2.116) | Medium | Anticipate grounds; address in complaint |
| 17 | Venue challenge (MCR 2.222) | Low | File in proper venue; establish residence |
| 18 | Failure to join necessary party | Low | Identify all required parties in complaint |
| 19 | Privilege assertions in discovery | Medium | Demand privilege log; challenge overbroad claims |
| 20 | Motion in limine (exclude evidence) | High | Pre-authenticate; brief admissibility proactively |
| 21 | Character evidence objection (MRE 404) | Medium | Frame as pattern, not character (MRE 404(b)) |
| 22 | Expert witness challenge (Daubert) | Low (pro se) | Rely on factual evidence over expert testimony |
| 23 | Separation of claims challenge | Low | Keep lane-specific claims in lane-specific filings |
| 24 | Abstention doctrine (federal) | Medium (federal) | Argue exception; show state courts inadequate |
| 25 | Qualified immunity (§1983) | High (federal) | Show clearly established right violated |

---

### Phase S-5: Convergence Cycle

#### 7-Phase Cycle (runs continuously)

```
Phase 1: SELF-TEST
  → Run automated checks on all filing packets and evidence chains
  → Output: pass/fail per action ID

Phase 2: SELF-AUDIT
  → Verify authority citations exist and are current
  → Check evidence references resolve to actual documents
  → Validate service and deadline compliance

Phase 3: QUALITY SCORING
  → Compute quality_score per action and per lane (formula below)
  → Track score trends over time (improving/degrading)

Phase 4: GAP CLASSIFICATION
  → Classify gaps as: DNEW (new deficiency), BLOCKERS (prevents filing),
    NEXT_PATCH (fixable in next iteration)
  → Priority: BLOCKERS first, then DNEW, then NEXT_PATCH

Phase 5: EMERGENCE DETECTION
  → Identify cross-lane patterns not visible in single-lane analysis
  → Example: custody interference + housing instability + financial manipulation
    → convergence pattern of coercive control

Phase 6: PATCH EXECUTION
  → Generate targeted fixes for each gap
  → Route patches to appropriate lane/action

Phase 7: RE-TEST
  → Re-run Phase 1 on patched items
  → Loop until PASS or BLOCKED (no infinite loops — max 3 iterations per gap)
```

#### Quality Score Formula

```
quality_score = (
    authority_completeness  × 0.25    # Do we have controlling authority for every legal argument?
  + evidence_coverage       × 0.20    # Is every factual claim supported by exhibits?
  + filing_readiness        × 0.20    # Is the packet complete per VehicleMap?
  + strategy_coherence      × 0.15    # Does this action align with wave/lane strategy?
  + cross_lane_integrity    × 0.10    # No contradictions across lanes?
  + emergence_capture       × 0.10    # Have we identified cross-lane patterns?
) × 100

Thresholds:
  ≥ 85: FILING-READY (green light to file)
  70–84: REVIEW-NEEDED (human review before filing)
  50–69: DRAFT (significant gaps remain)
  < 50:  BLOCKED (missing critical elements)
```

---

### Phase S-6: Resource Allocation

#### Pro Se Time Budget (~20 hours/week available)

| Activity | Hours/Week | Notes |
|----------|-----------|-------|
| Research & writing | 8 | Primary brief drafting, legal research |
| Evidence organization | 4 | Exhibit prep, Bates stamping, indexing |
| Filing & service | 2 | MiFile, TrueFiling, mail service |
| Court appearances | 2 | Hearings, conferences (average) |
| Strategy & planning | 2 | Lane review, convergence analysis |
| Administrative | 2 | Correspondence, record-keeping |

#### Filing Cost Tracking

| Filing Type | Circuit Court | COA | MSC | Federal |
|-------------|:------------:|:---:|:---:|:-------:|
| New case | $175 | $375 | $375 | $405 |
| Motion | $20 | — | — | — |
| Appeal | — | $375 | $375 | varies |
| Fee waiver | $0 (MC 20) | $0 | $0 | IFP |

#### Minimax Resource Strategy

```
Lane A (Custody):       50% of resources — primary relief sought
Lane F (Appellate):     25% of resources — preserves rights, creates leverage
Lanes B + D + E + C:    25% combined — strategic pressure, not resource sinks

Principle: Concentrate force on the decisive lane (A), maintain pressure
everywhere else. Never spread so thin that no lane reaches filing-ready.
```

---

## ═══════════════════════════════════════════
## MODULE 6: DOMAIN SPECIALISTS (Court-Level Expertise)
## ═══════════════════════════════════════════

> **Absorbs:** litigation-custody-specialist, litigation-ppo-specialist, litigation-protective-order-specialist,
> litigation-appellate-strategist, litigation-appeal-brief-engine, litigation-appellate-record-specialist,
> litigation-appellate-supreme, litigation-judicial-analyst, litigation-judicial-recusal-engine,
> litigation-family-law-master, litigation-foc-challenge-engine, litigation-child-support-analyzer,
> litigation-guardian-ad-litem-specialist, litigation-case-evaluation-specialist,
> litigation-trial-preparation-specialist, litigation-void-judgment-engine, litigation-venue-transfer-specialist

---

### D-1: Custody Specialist (Lane A)

#### MCL 722.23 — Best Interest Factors (a–l)

Every custody determination MUST address all 12 factors. The Filing Factory maps evidence to each:

| Factor | Statutory Text (abbreviated) | Evidence Type |
|--------|------------------------------|---------------|
| (a) | Love, affection, emotional ties | Communication logs, testimony |
| (b) | Capacity to give love, affection, guidance | Parenting actions, school involvement |
| (c) | Capacity to provide food, clothing, medical care | Financial records, living conditions |
| (d) | Length of time in stable environment | Residence history, school records |
| (e) | Permanence of family unit | Household stability documentation |
| (f) | Moral fitness | Conduct evidence, criminal records |
| (g) | Mental and physical health | Medical records (with proper release) |
| (h) | Home, school, community record | School reports, community ties |
| (i) | Reasonable preference of child | Age-appropriate, GAL report |
| (j) | Willingness to facilitate relationship | Communication re: parenting time |
| (k) | Domestic violence | Police reports, PPO records, incident logs |
| (l) | Any other relevant factor | Catch-all — convergence evidence |

#### Custody Modification Standard — Vodvarka v. Grasber

Movant must show: (1) proper cause or (2) change of circumstances, then best-interest analysis.
**Proper cause**: appropriate ground for legal action relating to custody.
**Change of circumstances**: conditions since last order that have or could have a significant effect on the child.

---

### D-2: PPO / Protective Order Specialist (Lane D)

#### MCL 600.2950 — Domestic PPO Lifecycle

```
PETITION → EX PARTE ISSUANCE → SERVICE → HEARING (if respondent objects) → ORDER
    │                                          │
    └─ Denied? → Appeal to circuit court       └─ Violated? → Contempt (MCL 600.2950(23))
```

- **Filing**: Petition on MC 375 (domestic) or MC 376 (non-domestic/stalking)
- **Standard**: "Reasonable cause to believe" respondent may commit listed acts
- **Duration**: Up to 182 days; renewable upon showing of continued need
- **Enforcement**: Violation is a criminal misdemeanor. Also civil contempt available.
- **Modification/Termination**: Either party may move; burden on movant

---

### D-3: Appellate Stack (Lane F)

#### Three-Tier Appellate Path

```
Trial Court (14th Circuit) → Michigan COA → Michigan Supreme Court
                                 ↓                    ↓
                          MCR 7.204/7.205      MCR 7.303/7.305
                          21-day deadline       56-day deadline
```

#### Appellate Brief Structure (MCR 7.212)

| Section | Requirement | Notes |
|---------|-------------|-------|
| Cover page | Party designation, case number, COA docket | Color: blue (appellant), red (appellee) |
| Table of Contents | Required | With page references |
| Table of Authorities | Required | Cases, statutes, rules, secondary sources |
| Jurisdictional Statement | Required | Basis for appellate jurisdiction |
| Statement of Questions Presented | Required | Each issue on a separate page |
| Statement of Facts | Required | Record citations mandatory |
| Argument | Required | Each issue with standard of review stated |
| Relief Requested | Required | Specific relief for each issue |
| Appendix | Required | Tabs A–H (order appealed, register, relevant orders, opinion, etc.) |

#### Standards of Review

| Standard | Applies To | Deference Level |
|----------|-----------|-----------------|
| **De novo** | Questions of law, constitutional issues | None — COA decides fresh |
| **Clear error** | Factual findings | High — reverse only if "definitely and firmly convinced" of mistake |
| **Abuse of discretion** | Custody, evidentiary rulings | High — must show outcome outside range of principled outcomes |
| **Plain error** | Unpreserved issues | Highest — clear error affecting substantial rights |

#### Record Preservation Essentials

- **Object contemporaneously** to preserve issues for appeal
- **Make an offer of proof** when evidence is excluded
- **Request findings** under MCR 2.517 for bench trials
- **Order transcripts** within 14 days of filing claim of appeal (MCR 7.210)

---

### D-4: Judicial Analyst & Recusal Engine (Lane E)

#### Disqualification Motion (MCR 2.003)

Grounds for disqualification (MCR 2.003(C)):
1. Personal bias or prejudice
2. Personal knowledge of disputed evidentiary facts
3. Prior involvement as attorney, witness, or judge in the matter
4. Financial interest in the outcome
5. Family relationship to a party or attorney
6. Any other ground in the Michigan Code of Judicial Conduct

**Procedure**: File motion → assigned to chief judge (MCR 2.003(D)). If chief judge = challenged judge,
next senior judge decides. If denied → mandamus to COA.

#### JTC Complaint Process (MCR 9.104–9.205)

```
Complaint filed → JTC investigates → Probable cause determination
  → Formal complaint → Public hearing → Recommendation to MSC
  → MSC issues final discipline (censure, suspension, removal)
```

**Key standards**: Conduct clearly prejudicial to the administration of justice; persistent
failure to perform judicial duties; habitual intemperance.

---

### D-5: FOC Challenge Engine (Lane A — Sub-Specialty)

#### MCR 3.218 — Friend of the Court Objections

- **21-day deadline** to file objection to FOC recommendation
- File objection + request for de novo hearing before the judge
- FOC recommendation is NOT binding — it becomes the order only if no objection filed
- **Objection procedure**: written objection stating specific grounds + request for hearing
- **De novo review**: Judge reviews from scratch — not limited to FOC's analysis

#### Common FOC Challenge Grounds
- Failure to investigate allegations
- Reliance on one party's account without verification
- Mathematical errors in support calculations
- Failure to consider all statutory factors
- Bias or appearance of impropriety in investigation

---

### D-6: Child Support Analyzer

#### Michigan Child Support Formula (MCSF)

Key inputs: both parents' gross incomes, overnights per parent, health insurance costs,
childcare costs, other children. Formula produces a recommended support amount.

- **Income imputation**: If a parent is voluntarily unemployed/underemployed, court may impute
  income at prior earning level or local median (MCL 552.605(2))
- **Deviation**: Court may deviate from MCSF if unjust/inappropriate, but must state reasons
- **Modification**: Changed circumstances (>10% change in support or significant income change)

---

### D-7: Guardian ad Litem Specialist

#### MCL 722.24 — GAL Appointment and Interaction

- GAL represents child's best interests (not child's preferences)
- GAL has access to all records and may interview parties, child, witnesses
- GAL files report with recommendations to the court
- **Interaction protocol**: Cooperate fully, provide requested documents promptly,
  document all communications, never attempt to influence GAL ex parte

---

### D-8: Trial Preparation Specialist

#### MCR 2.507 — Pretrial Conference

- Court may require pretrial conference to narrow issues, identify witnesses, discuss settlement
- **Pretrial statement**: File list of witnesses, exhibits, legal issues, stipulations
- **Exhibit exchange**: Exchange copies of all proposed exhibits before trial

#### MCR 2.509 — Trial Procedure

- **Witness preparation**: Review testimony scope, practice direct examination, prepare for cross
- **Exhibit organization**: Pre-marked, pre-tabbed, with index. Three copies (court, self, opposing)
- **Trial notebook**: Organized by witness — direct questions, anticipated cross, exhibits to introduce

---

### D-9: Void Judgment Engine

#### MCR 2.612(C)(1) — Relief from Judgment

Grounds to set aside a judgment or order:
| Ground | Rule | Standard |
|--------|------|----------|
| (a) Mistake, inadvertence, surprise | MCR 2.612(C)(1)(a) | Within 1 year of judgment |
| (b) Newly discovered evidence | MCR 2.612(C)(1)(b) | Within 1 year; due diligence required |
| (c) Fraud, misrepresentation | MCR 2.612(C)(1)(c) | Within 1 year; clear and convincing |
| (d) Void judgment | MCR 2.612(C)(1)(d) | **No time limit** — jurisdictional defect |
| (e) Satisfied/released/inequitable | MCR 2.612(C)(1)(e) | Changed circumstances |
| (f) Any other reason | MCR 2.612(C)(1)(f) | Extraordinary circumstances |

**Void judgment strategy**: If the court lacked jurisdiction (personal or subject matter),
the judgment is void ab initio and may be challenged at any time. This is the most powerful
tool for attacking orders entered without proper authority.

---

### D-10: Venue Transfer Specialist

#### MCR 2.222 — Change of Venue

- **Improper venue**: Motion to dismiss or transfer (MCR 2.222(A))
- **Convenience**: Transfer for convenience of parties and witnesses (MCR 2.222(C))
- **Forum non conveniens**: Rare; another forum is significantly more appropriate
- **Timing**: Raise venue objection early — waived if not raised in first responsive pleading

---

### D-11: Case Evaluation Specialist

#### MCR 2.403 — Case Evaluation (Mediation Alternative)

- Court may order case evaluation; panel of 3 evaluators
- Each side presents summary; panel issues award within specified range
- **Accept/reject within 28 days** — if rejecting party does not improve position at trial by
  greater than the evaluation, court sanctions (actual costs from date of rejection)
- Strategic consideration: rejection risk vs. trial outcome confidence

---

*End of Module 4-5-6 — Filing Factory, Strategic Command, and Domain Specialists*
