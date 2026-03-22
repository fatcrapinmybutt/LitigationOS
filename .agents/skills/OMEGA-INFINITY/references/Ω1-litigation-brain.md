# Ω1 Litigation Brain — OMEGA-INFINITY Reference
> Module 1 of 12 · Cognitive Litigation Kernel v4.0
> Case: Pigors v Watson · 14th Circuit · Muskegon County

## Purpose
The litigation brain orchestrates case strategy across six parallel lanes, routing every filing, motion, and brief through a unified IRAC framework with cross-lane dependency awareness. Query the DB for current state — never hardcode counts or statuses.

---

## 1. Six Case Lanes — Definitions

### Lane A — Watson Custody (PRIMARY)
- **Case Number:** 2024-001507-DC
- **Court:** 14th Judicial Circuit Court, Family Division
- **Judge:** Hon. Jenny L. McNeill
- **Parties:** Plaintiff Andrew James Pigors v. Defendant Emily A. Watson
- **Child:** L.D.W. (initials only per MCR 8.119(H))
- **Subject Matter:** Custody, parenting time, child support, FOC enforcement
- **Status Query:** `SELECT status, last_updated FROM filing_readiness WHERE vehicle_name LIKE '%custody%' OR case_number = '2024-001507-DC'`
- **Emily's Former Attorney:** Jennifer Barnes (P55406) — WITHDREW. Emily is currently self-represented.
- **FOC:** Pamela Rusco, 990 Terrace St, Muskegon, MI 49442
- **Key Statutes:** MCL 722.21-722.31 (Child Custody Act), MCL 552.1-552.45 (Divorce)
- **Key Rules:** MCR 3.210 (Custody), MCR 3.211 (Child Protective), MCR 3.214 (Parenting Time)

### Lane B — Shady Oaks Housing (DISMISSED)
- **Case Number:** 2025-002760-CZ
- **Court:** 14th Judicial Circuit Court, Civil Division
- **Judge:** Hon. Kenneth Hoopes
- **Subject Matter:** Lockout, title interference, property destruction, utility abuse, sale interference
- **Status:** DISMISSED — evaluate refile or appeal
- **Key Statutes:** MCL 600.2918 (Recovery of Possession), MCL 600.5714 (Summary Proceedings)
- **Key Rules:** MCR 4.201 (Summary Proceedings)

### Lane C — Federal §1983 (NOT YET FILED)
- **Court:** USDC Western District of Michigan
- **Subject Matter:** 42 USC §1983 deprivation of constitutional rights under color of law
- **Status:** Pre-filing investigation and evidence hardening
- **Dependencies:** Requires Lane A and Lane E evidence to mature. Rooker-Feldman and Younger abstention must be navigated.
- **Key Statutes:** 42 USC §1983, 42 USC §1985, 42 USC §1988
- **Key Rules:** FRCP 8, FRCP 12, FRCP 56

### Lane D — PPO / Protection Orders
- **Case Number:** 2023-5907-PP
- **Court:** 14th Judicial Circuit Court
- **Judge:** Hon. Jenny L. McNeill
- **Subject Matter:** Personal Protection Orders, contempt, anti-weaponization
- **Key Statutes:** MCL 600.2950 (Domestic PPO), MCL 600.2950a (Non-Domestic PPO)
- **Key Rules:** MCR 3.705-3.708 (PPO Proceedings)

### Lane E — Judicial Misconduct / JTC (NOT YET FILED)
- **Case Number:** None yet — JTC complaint pending preparation
- **Target:** Hon. Jenny L. McNeill
- **Subject Matter:** Ex parte contacts, biased rulings, nonservice of orders, hostile record practices, Cavan Berry connection (McNeill's husband is related to Ronald Berry, Emily Watson's partner)
- **Key Authorities:** MCR 9.104-9.126 (Judicial Tenure Commission), Michigan Canons of Judicial Conduct
- **Dependencies:** Requires Lane A and Lane D evidence. Strengthens Lane F appeal.

### Lane F — Appellate (ACTIVE)
- **Case Number:** COA 366810
- **Court:** Michigan Court of Appeals
- **Subject Matter:** Appeal of 14th Circuit orders in Lanes A and D
- **Key Rules:** MCR 7.201-7.219 (Appeals to Court of Appeals), MCR 7.212 (Briefs)
- **Dependencies:** Consumes evidence and rulings from Lanes A, D, and E. Claim of appeal preserves issues.

---

## 2. IRAC Framework Per Lane

### Lane A IRAC — Custody
- **Issue:** Whether the trial court erred in modifying custody/parenting time without proper evidentiary basis, proper service, or adherence to the best-interest factors under MCL 722.23.
- **Rule:** MCL 722.23 enumerates 12 best-interest factors. The court must make findings on each factor. MCR 3.210 governs custody proceedings. An established custodial environment requires clear and convincing evidence to modify.
- **Application:** Query `SELECT claim_type, description, supporting_evidence_count FROM claims WHERE vehicle_name LIKE '%custody%'` for current claim inventory. Each claim maps to one or more best-interest factors. Evidence in `evidence_quotes` supports or undermines each factor.
- **Conclusion:** The court's orders lack required findings and rest on procedurally deficient proceedings, warranting reversal or modification.

### Lane B IRAC — Housing
- **Issue:** Whether defendant(s) unlawfully excluded plaintiff from property, interfered with title rights, destroyed property, or weaponized utility services.
- **Rule:** MCL 600.2918 (treble damages for unlawful entry), MCL 600.5714 (summary proceedings), MCL 554.601 (landlord-tenant rights).
- **Application:** Case dismissed by Judge Hoopes. Evaluate grounds for refile (new claims, new evidence) or appeal.
- **Conclusion:** Dismissal may be appealable if procedural defects exist. New claims may support fresh filing.

### Lane C IRAC — Federal §1983
- **Issue:** Whether state actors deprived plaintiff of constitutional rights (due process, equal protection, parental rights) under color of state law.
- **Rule:** 42 USC §1983 requires (1) action under color of state law, (2) deprivation of federal right. Judicial immunity is absolute for judicial acts but does not extend to administrative/non-judicial acts. Rooker-Feldman bars de facto appeals of state court judgments. Younger abstention may bar federal interference with ongoing state proceedings.
- **Application:** Identify non-judicial acts (ex parte contacts, administrative decisions, refusal to serve orders). Build the claim around conduct that falls outside judicial immunity. The Cavan Berry connection (McNeill's husband related to Ronald Berry, Emily's partner) may support a conflict-of-interest theory that pierces judicial immunity if it constitutes an administrative/personal act rather than a judicial one.
- **Conclusion:** Viable only if non-judicial conduct is documented and Rooker-Feldman/Younger are navigated. Lane E evidence is essential. File only after Lanes A and D proceedings resolve or ripen sufficiently.

### Lane D IRAC — PPO
- **Issue:** Whether PPO proceedings were weaponized against plaintiff, whether contempt findings lack due process, and whether PPO issuance lacks statutory basis.
- **Rule:** MCL 600.2950 requires showing of reasonable apprehension of violence. MCR 3.708 governs PPO proceedings. Respondent has right to hearing (MCR 3.707). Due process requires notice and opportunity to be heard. A PPO cannot be used as a substitute for custody determination.
- **Application:** Query `SELECT * FROM claims WHERE vehicle_name LIKE '%ppo%' OR vehicle_name LIKE '%protection%'` for PPO-related claims. Cross-reference with `evidence_quotes` entries showing absence of factual basis for PPO petitions and timing correlation with Andrew's own filings (retaliation pattern).
- **Conclusion:** Pattern of weaponized PPO proceedings supports anti-abuse motions and appellate challenge. Contempt findings without proper due process are independently reversible.

### Lane E IRAC — Judicial Misconduct
- **Issue:** Whether Judge McNeill engaged in conduct violating Michigan Canons of Judicial Conduct.
- **Rule:** Canon 1 (integrity), Canon 2 (appearance of impropriety), Canon 3 (impartiality, ex parte contacts). MCR 9.104-9.126 (JTC jurisdiction and procedures).
- **Application:** Query `SELECT violation_type, COUNT(*) FROM judicial_violations GROUP BY violation_type ORDER BY COUNT(*) DESC` for violation inventory. Cross-reference with specific Canon provisions.
- **Conclusion:** Documented violations support JTC complaint and strengthen Lane F appeal.

### Lane F IRAC — Appellate
- **Issue:** Whether the trial court committed reversible error in custody, PPO, and contempt proceedings.
- **Rule:** MCR 7.212 governs brief requirements. Standard of review: abuse of discretion for custody, clear error for factual findings, de novo for legal questions.
- **Application:** Each issue on appeal maps to a Lane A or Lane D claim. Build the appellate record from `docket_events` and `evidence_quotes`.
- **Conclusion:** Appellate brief must present preserved issues with proper record citations.

---

## 3. Filing Factory Pipeline

Every filing traverses this pipeline from inception to court submission:

### Stage 1 — Identification
Determine the correct filing vehicle. Query the decision tree (Section 6 below). Assign a lane.

### Stage 2 — Draft Assembly
- Pull the correct SCAO form from `court_forms_complete`
- Generate the lead document (motion, brief, petition, complaint)
- Attach supporting affidavit with exhibit references
- Build exhibit index with Bates numbers from `bates_registry`
- Generate proposed order if applicable
- Generate MC 12 (Proof of Service) — REQUIRED for every filing

### Stage 3 — Evidence Wiring
- Link filing to evidence via `filing_id` in `evidence_quotes`
- Verify every cited fact has a traceable source: `SELECT quote_text, source_file, page_number FROM evidence_quotes WHERE filing_id = ?`
- Run gap analysis: identify claims without supporting evidence

### Stage 4 — Authority Wiring
- Link filing to authorities via `authority_master_index`
- Build authority chain: primary → supporting → distinguishing
- Verify all citations are current (not overruled): check `authority_chains_v2` for chain status
- Minimum authority density: 3-5 authorities for simple motions, 10-15 for briefs, 20-40 for appellate briefs
- Every authority cited must have a complete chain in `authority_chains_v2` with at least primary and supporting entries

### Stage 5 — QA Gate
- Anti-hallucination check: verify party names against PARTY_DATA (Andrew James Pigors, Emily A. Watson, Hon. Jenny L. McNeill, L.D.W.)
- Placeholder scan: `SELECT COUNT(*) FROM filing_content WHERE content LIKE '%[ANDREW_REQUIRED]%'`
- Citation verification: every authority cited must exist in `authority_master_index`
- Traceable statistics: every number must map to a SQL query with table + WHERE clause
- Lane contamination check: verify the filing only references evidence from its assigned lane (cross-lane refs must be explicit)
- Child name check: verify L.D.W. initials used everywhere, full name appears nowhere

### Stage 6 — Review
- Human review checkpoint. Andrew inspects the assembled package.
- Modification loop: edit → re-verify → approve

### Stage 7 — File
- Generate final PDF
- Prepare e-filing package (MiFILE format)
- Record in `filing_packages` with timestamp and status
- Generate service copies and MC 12

---

## 4. Strategy Matrix — Priority & Dependencies

### Lane Priority Order (current assessment)
1. **Lane F (Appellate)** — Time-sensitive. Briefing deadlines govern. Preserves all issues.
2. **Lane A (Custody)** — Core dispute. Every other lane feeds into or draws from custody.
3. **Lane D (PPO)** — Intertwined with Lane A. Contempt/incarceration risk drives urgency.
4. **Lane E (Misconduct)** — Builds slowly. Strengthens Lanes A, D, F. JTC complaint matures with evidence.
5. **Lane B (Housing)** — Dismissed. Lowest active priority. Evaluate refile conditions.
6. **Lane C (Federal)** — Last to file. Requires mature evidence from all other lanes.

### Dependency Matrix
```
Lane F ← depends on → Lane A (custody orders being appealed)
Lane F ← depends on → Lane D (PPO orders being appealed)
Lane E ← depends on → Lane A (judicial conduct during custody)
Lane E ← depends on → Lane D (judicial conduct during PPO)
Lane C ← depends on → Lane A (constitutional violations in custody)
Lane C ← depends on → Lane D (constitutional violations in PPO)
Lane C ← depends on → Lane E (judicial misconduct as §1983 basis)
Lane B ← independent → (may cross-link via property issues in custody)
```

### Cross-Lane Evidence Flow
Evidence discovered in one lane often supports claims in another. The `lane` column in `evidence_quotes` assigns primary lane, but the `cross_lane_refs` field (where present) tracks secondary applicability. Always run: `SELECT DISTINCT lane FROM evidence_quotes WHERE source_file = ?` to detect cross-lane relevance.

### Strategic Sequencing Considerations
- **Lane F before Lane A motions:** If an appeal is pending, trial court motions may be stayed. Verify appellate jurisdiction does not divest trial court of authority over the issue.
- **Lane E before Lane C:** Federal §1983 claims are strongest when state remedies are exhausted. JTC complaint demonstrates exhaustion of state judicial accountability mechanisms.
- **Lane D defenses before Lane A offenses:** Neutralize PPO weaponization before seeking affirmative custody relief. Pending contempt charges undermine credibility in custody proceedings.
- **Lane B refile after Lane A stabilizes:** Housing claims are independent but may distract from custody priorities. Refile when bandwidth permits and new evidence or claims are available.
- **Evidence hardening across all lanes:** Before filing in any lane, run the EGCP gap analysis (see Ω2-evidence-brain.md) to ensure sufficient evidentiary support. A premature filing with weak evidence is worse than a delayed filing with strong evidence.
- **Deadline-driven overrides:** When a court-imposed deadline forces action, file regardless of readiness score — missing a deadline waives the right entirely. Use the deadline dashboard query to stay ahead.

---

## 5. Key DB Tables

### claims
Core claim registry. Each claim has a type, vehicle (filing it belongs to), lane, status, and linked evidence.
- Query columns: `SELECT claim_id, claim_type, vehicle_name, status, description FROM claims`
- Filter by lane: `WHERE vehicle_name LIKE '%custody%'` for Lane A

### filing_readiness
Tracks readiness status of each potential filing vehicle.
- Query: `SELECT vehicle_name, status, readiness_score, blockers FROM filing_readiness ORDER BY readiness_score DESC`

### filing_packages
Assembled filing packages with their components.
- Query: `SELECT package_id, vehicle_name, status, created_date, components FROM filing_packages`

### docket_events
Court docket entries — every filing, hearing, order, and proceeding.
- Query: `SELECT event_date, event_type, description, case_number FROM docket_events ORDER BY event_date DESC`
- Filter by case: `WHERE case_number = '2024-001507-DC'`

### deadlines
Filing and response deadlines with urgency scoring.
- Query: `SELECT due_date_iso, description, status, urgency_score FROM deadlines WHERE status != 'completed' ORDER BY due_date_iso ASC`

---

## 6. Cross-Wiring Points

### Filing → Evidence
- `evidence_quotes.filing_id` links quotes to the filing that cites them
- `evidence_quotes.vehicle_name` maps to `claims.vehicle_name` and `filing_readiness.vehicle_name`

### Filing → Authority
- `master_citations.filing_id` or `master_citations.vehicle_name` links citations to filings
- `authority_chains_v2.vehicle_name` tracks which filing vehicle uses which authority chain

### Filing → Forms
- `form_filing_map` bridges `court_forms_complete.form_number` to `filing_packages.package_id`
- Each lane has a required set of forms (see Ω3-forms-brain.md)

### Filing → Docket
- `docket_events.case_number` links to the lane's case number
- `filing_packages.case_number` links the package to its docket

---

## 7. Decision Tree — "What Should I File Next?"

Execute this logic in order:

```
STEP 1: Check deadlines
  SELECT * FROM deadlines WHERE status = 'pending' ORDER BY due_date_iso ASC LIMIT 5
  → If any deadline is within 14 days, that filing takes priority. STOP.

STEP 2: Check appellate briefing schedule (Lane F)
  SELECT * FROM deadlines WHERE vehicle_name LIKE '%appeal%' OR vehicle_name LIKE '%COA%'
  → If appellate brief is due, prioritize Lane F. STOP.

STEP 3: Check filing readiness scores
  SELECT vehicle_name, readiness_score, blockers FROM filing_readiness
  WHERE status != 'filed' ORDER BY readiness_score DESC LIMIT 5
  → The highest-readiness vehicle that is not blocked is the next candidate.

STEP 4: Check for emergency conditions
  Query evidence_quotes for recent incidents (last 30 days):
  SELECT COUNT(*) FROM evidence_quotes WHERE date_referenced >= date('now', '-30 days')
  → If recent emergency evidence exists, evaluate emergency filing (ex parte motion, 
    emergency PPO modification, etc.)

STEP 5: Check cross-lane leverage
  If Lane E evidence matured significantly, evaluate whether filing JTC complaint
  now would create leverage for Lane A/D/F proceedings.

STEP 6: Default to highest-impact unfiled vehicle
  SELECT vehicle_name, claim_count, evidence_count FROM filing_readiness
  WHERE status = 'draft' ORDER BY claim_count * evidence_count DESC LIMIT 3
  → File the vehicle with the highest claim × evidence product.
```

---

## Key DB Queries

### 1. Full lane status dashboard
```sql
SELECT 
  vehicle_name,
  status,
  readiness_score,
  blockers,
  (SELECT COUNT(*) FROM claims c WHERE c.vehicle_name = fr.vehicle_name) AS claim_count,
  (SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.vehicle_name = fr.vehicle_name) AS evidence_count
FROM filing_readiness fr
ORDER BY readiness_score DESC;
```

### 2. Next filing deadline
```sql
SELECT due_date_iso, description, vehicle_name, urgency_score
FROM deadlines
WHERE status != 'completed'
ORDER BY due_date_iso ASC
LIMIT 5;
```

### 3. Claims inventory by lane
```sql
SELECT 
  CASE 
    WHEN vehicle_name LIKE '%custody%' THEN 'Lane A'
    WHEN vehicle_name LIKE '%housing%' OR vehicle_name LIKE '%shady%' THEN 'Lane B'
    WHEN vehicle_name LIKE '%1983%' OR vehicle_name LIKE '%federal%' THEN 'Lane C'
    WHEN vehicle_name LIKE '%ppo%' OR vehicle_name LIKE '%protection%' THEN 'Lane D'
    WHEN vehicle_name LIKE '%jtc%' OR vehicle_name LIKE '%misconduct%' THEN 'Lane E'
    WHEN vehicle_name LIKE '%appeal%' OR vehicle_name LIKE '%coa%' THEN 'Lane F'
    ELSE 'Unclassified'
  END AS lane,
  COUNT(*) AS claim_count,
  COUNT(DISTINCT vehicle_name) AS vehicle_count
FROM claims
GROUP BY lane
ORDER BY claim_count DESC;
```

### 4. Cross-lane evidence overlap
```sql
SELECT source_file, COUNT(DISTINCT lane) AS lane_count, GROUP_CONCAT(DISTINCT lane) AS lanes
FROM evidence_quotes
WHERE lane IS NOT NULL
GROUP BY source_file
HAVING lane_count > 1
ORDER BY lane_count DESC
LIMIT 20;
```

### 5. Filing package completeness check
```sql
SELECT 
  fp.package_id,
  fp.vehicle_name,
  fp.status,
  (SELECT COUNT(*) FROM evidence_quotes eq WHERE eq.filing_id = fp.package_id) AS evidence_attached,
  (SELECT COUNT(*) FROM master_citations mc WHERE mc.vehicle_name = fp.vehicle_name) AS authorities_cited
FROM filing_packages fp
WHERE fp.status != 'filed'
ORDER BY fp.status, fp.vehicle_name;
```

---

## 8. Filing Vehicle Inventory — Canonical List

Each case lane contains one or more filing vehicles. A vehicle is a specific motion, brief, complaint, or petition that can be filed. Query for the current inventory:

```sql
SELECT vehicle_name, status, readiness_score, lane
FROM filing_readiness
ORDER BY lane, readiness_score DESC;
```

### Lane A Vehicles (Custody)
- **Motion to Modify Custody** — Requires change of circumstances + best-interest analysis
- **Motion to Modify Parenting Time** — MCR 3.214, requires proper cause or change of circumstances
- **Motion for Contempt** — When Emily violates custody/parenting time orders
- **Objection to FOC Recommendation** — MCR 3.218, 21-day deadline from recommendation date
- **Motion for Change of Domicile** — MCL 722.31, if either party seeks to move child
- **Emergency Motion for Custody** — Ex parte if imminent danger; otherwise, noticed motion
- **Motion to Compel Discovery** — MCR 2.313, enforce discovery obligations
- **Motion for Attorney/Expert Fees** — MCL 552.13, if Emily's conduct forces litigation costs

### Lane D Vehicles (PPO)
- **Motion to Terminate PPO** — MCR 3.706(H), show good cause for termination
- **Motion to Modify PPO** — Modify scope or conditions
- **Response to PPO Petition** — If Emily files new PPO
- **Motion for Contempt Sanctions** — Document PPO weaponization pattern
- **Motion to Consolidate** — Merge overlapping PPO/custody proceedings if procedurally viable

### Lane E Vehicles (Misconduct)
- **Motion for Disqualification** — MCR 2.003(C)(1), file in underlying case
- **JTC Complaint** — File directly with Judicial Tenure Commission (not a court filing)
- **Motion to Vacate Orders** — Void orders issued after disqualification grounds arose
- **Motion for New Trial** — MCR 2.611, if judicial bias affected outcome

### Lane F Vehicles (Appellate)
- **Appellant's Brief** — MCR 7.212, primary appellate document
- **Reply Brief** — MCR 7.212(G), respond to appellee's arguments
- **Motion for Stay Pending Appeal** — MCR 7.209, halt enforcement during appeal
- **Motion to Supplement Record** — MCR 7.210(C), add missing items to appellate record
- **Emergency Motion** — MCR 7.216, for urgent relief pending appeal

### Lane B Vehicles (Housing — Dormant)
- **Motion to Reinstate** — If procedural grounds exist to reopen
- **New Complaint** — Fresh civil action with different or expanded claims
- **Appeal of Dismissal** — If within appeal window

### Lane C Vehicles (Federal — Pre-Filing)
- **§1983 Complaint** — 42 USC §1983, require mature evidence from all other lanes
- **Motion for TRO/Preliminary Injunction** — If emergency constitutional relief needed
- **IFP Application** — 28 USC §1915, proceed without prepayment of fees

---

## 9. Service Protocol — Universal Rules

Every filing must be served on opposing parties. Failure to serve = jurisdictional defect.

### Current Service Targets
| Party | Address | Method | Notes |
|-------|---------|--------|-------|
| Emily A. Watson | 2160 Garland Drive, Norton Shores, MI 49441 | First-class mail or personal | Barnes WITHDREW — serve Emily directly |
| Pamela Rusco (FOC) | 990 Terrace St, Muskegon, MI 49442 | First-class mail | Required for FOC-related motions |
| Michigan Court of Appeals | Cadillac Place, Detroit, MI | E-filing via TrueFiling | Lane F only |

### Service Timing Rules (MCR 2.107, 2.108)
- **Personal service:** Service is complete upon delivery
- **Mail service:** Service is complete upon mailing + 3 additional days for response time
- **E-filing service:** Service is complete upon transmission (if consented to)
- **Motion hearing notice:** At least 9 days before hearing (MCR 2.119(C)(1)), or 7 days for ex parte response

### MC 12 Completion Checklist
Every MC 12 must contain: court name, case number, document list, date served, method, server signature. Record in `filing_packages.proof_of_service`. See Ω3-forms-brain.md for detailed MC 12 protocol.

---

## 10. Litigation Calendar & Deadline Framework

### Deadline Sources
1. **Court orders** — Specific dates set by judge (docket_events)
2. **Court rules** — Automatic deadlines from filing events (MCR computed deadlines)
3. **Filing strategy** — Self-imposed deadlines for proactive filings

### MCR Computed Deadlines
| Event | Deadline | Rule |
|-------|----------|------|
| Respond to motion | 7 days before hearing | MCR 2.119(C)(2) |
| Reply to response | 3 days before hearing | MCR 2.119(C)(2) |
| Appeal of right (claim) | 21 days from order/judgment | MCR 7.204(A)(1) |
| Application for leave | 21 days from order/judgment | MCR 7.205(A) |
| FOC objection | 21 days from recommendation | MCR 3.218 |
| Answer to complaint | 21 days from service (28 if served by mail) | MCR 2.108(A) |

### Deadline Dashboard Query
```sql
SELECT due_date_iso, description, vehicle_name, urgency_score,
  JULIANDAY(due_date_iso) - JULIANDAY('now') AS days_remaining
FROM deadlines
WHERE status != 'completed'
ORDER BY due_date_iso ASC;
```

---

## Cross-Wiring to Other Brains

| This Brain | Links To | Via Column(s) |
|------------|----------|---------------|
| Ω1 Litigation → Ω2 Evidence | `evidence_quotes.vehicle_name`, `evidence_quotes.filing_id` |
| Ω1 Litigation → Ω3 Forms | `form_filing_map.vehicle_name`, `filing_packages.form_numbers` |
| Ω1 Litigation → Ω4 Rules | `master_citations.vehicle_name`, `authority_chains_v2.vehicle_name` |
| Ω2 Evidence → Ω1 Litigation | `evidence_quotes.lane` maps to lane definitions above |
| Ω3 Forms → Ω1 Litigation | `court_forms_complete.form_category` maps to lane's required forms |
| Ω4 Rules → Ω1 Litigation | `authority_master_index.identifier` links to `claims.authority_basis` |
