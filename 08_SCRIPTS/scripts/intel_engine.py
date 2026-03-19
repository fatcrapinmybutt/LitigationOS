"""
COURT INFRASTRUCTURE INTELLIGENCE INTEGRATION ENGINE
Ingests Michigan court tech/vendor/data flow intelligence into LitigationOS.
Builds: infrastructure map, vulnerability exploitation matrix, deadline engine,
docket monitor config, and package injection targets.
"""
import json, os
from datetime import datetime, timedelta

D99 = r"I:\LitigationOS_Delta99"
LOG = r"I:\DRIVE_ORG\operations.log"

def log(msg):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def write_md(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

# ============================================================
# 1. COURT INFRASTRUCTURE INTELLIGENCE MAP
# ============================================================
def build_infrastructure_intel():
    content = """# MICHIGAN COURT INFRASTRUCTURE INTELLIGENCE MAP

## Pigors v. Watson et al. | Case 2024-001507-DC | 14th Circuit, Muskegon County

---

> **CLASSIFICATION:** Strategic litigation intelligence. This document maps the
> technical infrastructure, vendor ecosystem, data flows, and exploitable structural
> vulnerabilities of Michigan's court systems as they relate to this case.

---

## I. SYSTEM ARCHITECTURE — TARGET COURTS

### A. 14th Circuit Court (Muskegon County) — PRIMARY TARGET
| Component | System | Vendor | Access |
|-----------|--------|--------|--------|
| Case Management | Odyssey Case Manager | Tyler Technologies | Clerk GUI / MiCourt API |
| E-Filing | MiFILE (TrueFiling) | Tyler/ImageSoft | mifile.courts.michigan.gov |
| Document Management | OnBase EDMS | Hyland/ImageSoft | Back-end (no public access) |
| Payments | AllPaid | Tyler/ACI | allpaid.com |
| Case Search | MiCourt/JIS | SCAO | micourt.courts.michigan.gov |
| Court ID | **D60** (District) / Circuit TBD | SCAO JIS | API parameter |

### B. Michigan Court of Appeals — APPELLATE TARGET
| Component | System | Vendor | Access |
|-----------|--------|--------|--------|
| E-Filing | MiFILE / TrueFiling | Tyler | mifile.courts.michigan.gov |
| Case Management | JIS / Odyssey | Tyler/SCAO | Internal |
| Opinions | courts.michigan.gov | State hosting | Public HTML/PDF |
| Proof of Service | COA-specific form | SCAO | PDF download |

### C. Michigan Supreme Court — ESCALATION TARGET
| Component | System | Access |
|-----------|--------|--------|
| Applications | Paper + MiFILE | mifile.courts.michigan.gov |
| Opinions | courts.michigan.gov | Public |
| Superintending Control | Original jurisdiction | MCR 7.306 |

### D. U.S. District Court, W.D. Michigan — FEDERAL TARGET
| Component | System | Access |
|-----------|--------|--------|
| E-Filing | CM/ECF (PACER) | ecf.miwd.uscourts.gov |
| Case Search | PACER | pacer.uscourts.gov |
| Payments | pay.gov | Federal |

---

## II. MiCOURT CASE SEARCH API — TECHNICAL SPECIFICATION

### Endpoint
```
GET https://micourt.courts.michigan.gov/CaseSearch/api/v1/search
```

### Authentication
- **Method:** OAuth2 Bearer Token
- **Identity Provider:** OneCourtID
- **Additional:** Subscription key in header (`Ocp-Apim-Subscription-Key`)

### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| `court` | string | Court ID (e.g., `D60` for Muskegon District) |
| `caseNumber` | string | Full case number (e.g., `2024-001507-DC`) |
| `firstName` | string | Party first name |
| `lastName` | string | Party last name |
| `filingDateFrom` | date | Start date filter |
| `filingDateTo` | date | End date filter |
| `caseType` | string | Case type code |
| `status` | string | Case status filter |
| `limit` | int | Results per page (default: 20) |
| `offset` | int | Pagination offset |

### Response Format
```json
{
  "cases": [
    {
      "caseNumber": "2024-001507-DC",
      "court": "14th Circuit",
      "parties": [...],
      "filingDate": "2024-XX-XX",
      "status": "Open",
      "events": [...]
    }
  ],
  "totalCount": N,
  "limit": 20,
  "offset": 0
}
```

### Rate Limiting
- No published rate limits
- Paginated responses (limit/offset)
- Polite polling interval recommended: ≥60 seconds

### STRATEGIC USE
1. **Automated docket monitoring** — Poll for new filings/orders on case 2024-001507-DC
2. **Opposition filing detection** — Alert when opposing counsel files anything
3. **Judge assignment tracking** — Detect if judge changes (disqualification outcome)
4. **Cross-case research** — Search for judge's other cases, pattern analysis

---

## III. MiFILE E-FILING SPECIFICATIONS

### Portal: mifile.courts.michigan.gov

### Technical Requirements (SCAO Electronic Document Standards)
| Requirement | Specification | MCR Reference |
|-------------|---------------|---------------|
| Format | PDF (text-searchable preferred) | MCR 1.109 |
| Page Size | 8.5" x 11" (Letter) | SCAO Standards |
| Margins | Minimum 1" all sides | MCR 1.109(D) |
| Font | Readable, minimum 12pt | MCR 1.109(D) |
| File Size | Max per document varies by court | MiFILE limits |
| Naming | Descriptive, no special characters | MiFILE standards |
| Signatures | "/s/ Name" for e-filed | MCR 1.109(E) |
| Confidential | Separate upload with confidential flag | MCR 1.109(D)(9) |
| Exhibits | Separate PDFs or combined with bookmarks | Court preference |

### Rejection Risk Factors
1. Non-text-searchable PDF (scanned without OCR)
2. Incorrect court/case number in filing
3. Missing signature block
4. Confidential info in public filing
5. Exceeds file size limits
6. Wrong document type selection in portal
7. Missing required forms (e.g., MC 20 for fee waiver)
8. Non-compliant formatting

---

## IV. VENDOR ECOSYSTEM — CONFLICT & LEVERAGE MAP

### Tyler Technologies (PRIMARY VENDOR)
- **Products in use:** Odyssey CMS, TrueFiling (MiFILE), AllPaid, Axess
- **Relationship:** State contract + Muskegon County maintenance contract
- **Relevance:** System controls what the clerk sees, how filings are processed
- **FOIA Target:** Muskegon County contract with Tyler (procurement records)

### Hyland/ImageSoft
- **Products:** OnBase EDMS (document management behind MiFILE)
- **Relationship:** SCAO integration partner
- **Relevance:** Document storage and retrieval — if a filing "disappears," OnBase is where to look

### Enqbator (Middleware)
- **Products:** Custom API bridges (MiFILE ↔ Odyssey)
- **Relevance:** Integration failures between e-filing and case management could explain
  delayed or missing filings

### AllPaid (Payment Processing)
- **Relevance:** Fee payment records can verify filing dates independent of clerk entries

---

## V. DATA FLOW MAP — CASE-SPECIFIC

```
PLAINTIFF (Pigors)                    DEFENDANT (Watson)
    |                                      |
    | e-file via MiFILE                    | e-file via MiFILE
    |                                      | (counsel: Barnes Law)
    v                                      v
[MiFILE Portal] ──── Tyler TrueFiling ────→ [OnBase EDMS]
                                              |
                                              v
                                    [Odyssey Case Manager]
                                         14th Circuit
                                              |
                        ┌─────────────────────┼─────────────────────┐
                        |                     |                     |
                        v                     v                     v
                   [Judge McNeill]       [FOC Office]          [Clerk's Office]
                   (Judicial review)     (Investigation)       (Register of Actions)
                        |                     |                     |
                        v                     v                     v
                   [JIS Database]        [MISDU/MDHHS]        [MiCourt API]
                   (Warrants/LEIN)       (Child Support)       (Public Search)
                        |
                        v
                   [Court of Appeals]  ←── Appeal filed (PKG05)
                        |
                        v
                   [Supreme Court]     ←── Leave application (PKG07)
```

### CRITICAL DATA FLOW VULNERABILITIES (This Case)

1. **Clerk Entry Control:** The Register of Actions is maintained by the clerk.
   If filings are not accurately logged (wrong dates, missing entries), the
   appellate record is corrupted. **MONITOR via MiCourt API for discrepancies.**

2. **FOC → Judge Channel:** FOC recommendations flow directly to the judge.
   If the FOC investigation was biased (see PKG12), the recommendation
   carries undeserved weight. **FOC objection triggers de novo hearing.**

3. **Ex Parte Order Entry:** August 8, 2025 ex parte orders were entered
   without notice. The data flow was: Mother's unsworn motion → MiFILE →
   Odyssey → Judge → Order signed → LEIN (if PPO). **Father was not in the loop.**

4. **Prosecutor's Office Nexus:** Mother employed at Kent County Prosecutor's
   Office, Family Court Division. Data flow risk: prosecutor databases →
   mother's access → litigation advantage. **This is a due process violation
   if prosecutorial resources were used in a private custody case.**

---

## VI. STRUCTURAL VULNERABILITY EXPLOITATION MATRIX

### Exploitable Vulnerabilities (LEGAL, NOT TECHNICAL)

| Vulnerability | How It Applies | Package | Argument |
|--------------|----------------|---------|----------|
| **Ex Parte Power Concentration** | Orders entered Aug 8, 2025 without notice or hearing | PKG01, PKG04, PKG05 | Due process violation — MCR 2.119(B), 14th Amendment |
| **Clerk Record Control** | ROA may not reflect all filings accurately | PKG04, PKG05 | Request certified ROA, compare to own filing records |
| **Transcript Cost Barrier** | MCR 7.216 fees can prevent appeal | PKG05 | MC 20 fee waiver + transcript substitute contingency |
| **FOIA Judiciary Exemption** | Cannot FOIA court records directly | ALL | Use MCR 8.119 (open records) instead of FOIA |
| **FOC Investigation Opacity** | FOC recommendations lack transparency | PKG12 | Object + demand de novo hearing (MCL 552.507(4)) |
| **Prosecutorial Conflict** | Mother's employer = Family Court Division | PKG03, PKG06, PKG10 | Appearance of impropriety, MCJC Canon 2 |
| **Bond/Fee Barriers** | Filing fees can prevent access | ALL | MC 20 fee waiver at every level |
| **Sealed Record Abuse** | Confidential filings can hide information | PKG04, PKG05 | Motion to unseal if opposing party uses sealed info |
| **Data Fragmentation** | Multiple systems = inconsistent records | PKG05 | Compare MiCourt API data vs clerk's physical file |
| **Coding Discretion** | Clerk event codes shape case statistics | PKG03, PKG06 | Request raw event log for bias analysis |

### Counter-Vulnerability Defenses

| Their Move | Your Counter | Authority |
|-----------|-------------|-----------|
| Claim FOIA exemption | Invoke MCR 8.119(H)(7) — open court records | MCR 8.119 |
| High transcript fees | MC 20 fee waiver + settled statement alternative | MCR 7.210(B)(3) |
| "Filed under seal" | Motion to unseal under MCR 8.119(I) | MCR 8.119(I) |
| Clerk says "no record" | MiCourt API search + independent filing confirmation | AllPaid receipt |
| FOC says "confidential" | Objection triggers de novo hearing anyway | MCL 552.507(4) |
| Judge denies access | Mandamus/superintending control to MSC | MCR 7.306 |

---

## VII. AUTOMATION DEPLOYMENT PLAN

### A. Docket Monitor (Immediate Priority)
```python
# MiCourt API polling configuration
MONITOR_CONFIG = {
    "case_number": "2024-001507-DC",
    "court_id": "D60",  # or circuit court ID
    "poll_interval_seconds": 3600,  # hourly
    "alert_on": ["new_filing", "new_order", "hearing_scheduled",
                 "judge_change", "status_change"],
    "api_base": "https://micourt.courts.michigan.gov/CaseSearch/api/v1",
    "auth": "OAuth2/OneCourtID"
}
```

### B. Deadline Engine (Critical)
| Event | Deadline | MCR | Status |
|-------|----------|-----|--------|
| COA Brief due | **April 15, 2026** | MCR 7.212 | **44 DAYS** |
| FOC Objection | 21 days from recommendation | MCL 552.507 | Watch for trigger |
| Disqualification motion | 14 days from discovery | MCR 2.003 | File ASAP |
| PPO modification hearing | 7 days notice minimum | MCR 3.707 | Compute from filing |
| MSC bypass window | 42 days if COA pending >180 days | MCR 7.305 | Track COA timeline |
| Federal §1983 SOL | 3 years from violation | 28 USC 1658 | ~Aug 2028 |
| JTC Request | No formal deadline | MCR 9.207 | File with Phase 4 |

### C. Record Integrity Verification
1. Pull case data from MiCourt API
2. Compare against personal filing records
3. Flag any discrepancies (missing filings, wrong dates, altered entries)
4. Document discrepancies for PKG04 (void orders) and PKG05 (COA brief)

### D. Opposition Intelligence
1. Search MiCourt for Barnes Law Firm PLLC filings
2. Track opposing counsel's filing patterns
3. Monitor for any new motions or responses to our filings
4. Alert on hearing date changes

### E. Judge Pattern Analysis
1. Query MiCourt for Judge McNeill's other cases
2. Analyze grant/deny rates on motions
3. Compare disposition patterns to county average
4. Use for PKG03 (disqualification) and PKG06 (JTC) evidence

---

## VIII. LEGAL ACCESS MATRIX — CASE-SPECIFIC PATHWAYS

| Target Record | Access Method | Legal Basis | Priority |
|--------------|---------------|-------------|----------|
| Register of Actions | Clerk inspection + MiCourt API | MCR 8.119(H)(7) | CRITICAL |
| FOC Investigation File | FOC objection → de novo hearing | MCL 552.507 | HIGH |
| Ex Parte Order File | Clerk inspection | MCR 8.119 | CRITICAL |
| Opposing Counsel's Filings | MiCourt API + MiFILE | Public record | HIGH |
| Tyler/Odyssey Contract | FOIA to Muskegon County | MCL 15.231 | MEDIUM |
| Judge's Other Cases | MiCourt API search | Public record | HIGH |
| Transcript of Proceedings | Court reporter + MC 20 | MCR 7.210 | CRITICAL |
| MDHHS/CPS Records | FOIA to MDHHS | MCL 15.231 + MCL 722.627 | HIGH |
| Prosecutor Office Records | FOIA to Kent County | MCL 15.231 | HIGH |
| Payment/Filing Receipts | AllPaid records | Account records | MEDIUM |

---

## IX. FOIA CAMPAIGN TARGETS

### Tier 1 — File Immediately
1. **Muskegon County → Tyler Technologies contract** (court system procurement)
2. **Kent County Prosecutor → Employee conflict policies** (mother's employment)
3. **MDHHS → CPS investigation records** (if any CPS involvement)

### Tier 2 — File After Phase 1 Filings
4. **Muskegon FOC → Investigation protocols and training materials**
5. **Muskegon County → Judge McNeill's recusal/disqualification history**
6. **SCAO → MiFILE filing statistics for 14th Circuit** (processing times)

### Tier 3 — Strategic
7. **Michigan State Police → LEIN query logs for case parties** (if accessible)
8. **HealthWest → Any court-ordered evaluation protocols** (if mental health at issue)

**NOTE:** Judiciary is FOIA-exempt. Access court records via MCR 8.119, not FOIA.
Use FOIA only for county/state agency records.

---

## X. INTELLIGENCE INTEGRATION — PACKAGE TARGETS

| Package | New Intelligence Injected |
|---------|--------------------------|
| PKG01 | FOC data flow vulnerability, de novo hearing leverage |
| PKG03 | Judge pattern analysis framework, vendor system awareness |
| PKG04 | Record integrity verification protocol, MiCourt comparison |
| PKG05 | Transcript cost mitigation, record completeness verification |
| PKG06 | System-level misconduct documentation, coding discretion bias |
| PKG09 | Housing court (60th District) system specs, payment verification |
| PKG10 | Prosecutorial nexus data flow, system-enabled due process violations |
| PKG12 | FOC investigation opacity exploitation, MISDU data access |

---

*Generated by LitigationOS Court Infrastructure Intelligence Engine*
*Source: Michigan Court Technology & Infrastructure Research, March 2026*
"""
    write_md(os.path.join(D99, "COURT_INFRASTRUCTURE_INTELLIGENCE.md"), content)
    log(f"  Court infrastructure intelligence map built ({len(content)} chars)")

# ============================================================
# 2. DEADLINE ENGINE
# ============================================================
def build_deadline_engine():
    today = datetime.now()
    coa_deadline = datetime(2026, 4, 15)
    days_to_coa = (coa_deadline - today).days
    
    deadlines = {
        "generated": today.isoformat(),
        "case": "Pigors v. Watson, 2024-001507-DC",
        "coa_case": "366810",
        "deadlines": [
            {
                "id": "COA-BRIEF",
                "description": "Court of Appeals Appellant Brief Due",
                "deadline": "2026-04-15",
                "mcr": "MCR 7.212",
                "days_remaining": days_to_coa,
                "status": "CRITICAL" if days_to_coa <= 45 else "ACTIVE",
                "package": "PKG05",
                "dependencies": ["Transcript or settled statement", "Lower court record",
                                 "Reproduced materials addendum"],
                "notes": "HARD DEADLINE — cannot be extended without motion for good cause"
            },
            {
                "id": "FOC-OBJECTION",
                "description": "FOC Objection (21 days from recommendation service)",
                "deadline": "TRIGGERED — 21 days from FOC recommendation",
                "mcr": "MCL 552.507(4)",
                "days_remaining": "WATCH",
                "status": "WATCHING",
                "package": "PKG12",
                "dependencies": ["FOC recommendation issued"],
                "notes": "Triggers de novo hearing before judge"
            },
            {
                "id": "DISQUALIFICATION",
                "description": "Motion to Disqualify Judge (14 days from discovery)",
                "deadline": "TRIGGERED — 14 days from discovery of bias",
                "mcr": "MCR 2.003(D)",
                "days_remaining": "ASAP",
                "status": "URGENT",
                "package": "PKG03",
                "dependencies": ["Affidavit of bias", "All known grounds listed"],
                "notes": "Must include ALL known grounds — cannot supplement later"
            },
            {
                "id": "PPO-HEARING",
                "description": "PPO Modification/Termination Hearing Notice",
                "deadline": "7 days before hearing (minimum)",
                "mcr": "MCR 3.707",
                "days_remaining": "COMPUTE from filing",
                "status": "READY TO FILE",
                "package": "PKG02",
                "dependencies": ["CC 379 motion filed", "CC 381 notice served"],
                "notes": "Service must be 7+ days before hearing"
            },
            {
                "id": "MSC-BYPASS",
                "description": "MSC Bypass Application (42-day window)",
                "deadline": "42 days if COA pending >180 days",
                "mcr": "MCR 7.305(B)(4)",
                "days_remaining": "TRACK COA",
                "status": "FUTURE",
                "package": "PKG07",
                "dependencies": ["COA case filed", "180+ days pending"],
                "notes": "Bypass allows direct MSC application while COA pending"
            },
            {
                "id": "FEDERAL-SOL",
                "description": "Federal §1983 Statute of Limitations",
                "deadline": "3 years from each violation",
                "mcr": "28 USC 1658 / Owens v. Okure, 488 US 235",
                "days_remaining": "~850+ days (varies by violation)",
                "status": "SAFE",
                "package": "PKG10",
                "dependencies": ["State remedies exhausted or futile"],
                "notes": "Michigan borrows 3-year personal injury SOL for §1983"
            },
            {
                "id": "SPOLIATION",
                "description": "Evidence Preservation Notice",
                "deadline": "IMMEDIATE — before evidence destroyed",
                "mcr": "MCR 2.313(B)",
                "days_remaining": 0,
                "status": "FILE NOW",
                "package": "PKG11",
                "dependencies": ["Specific evidence identified", "Custodians named"],
                "notes": "Earlier = stronger — preservation duty attaches on notice"
            },
            {
                "id": "CONTEMPT-MOTION",
                "description": "Motion for Contempt (PT enforcement)",
                "deadline": "No time limit, but sooner = more weight",
                "mcr": "MCR 3.606",
                "days_remaining": "DISCRETIONARY",
                "status": "READY",
                "package": "PKG08",
                "dependencies": ["Clear court order exists", "Violation documented"],
                "notes": "Must prove willful violation of clear, specific order"
            },
        ],
        "filing_sequence": {
            "phase_1_establish": ["PKG01", "PKG11", "PKG12"],
            "phase_1_timing": "File simultaneously — ASAP",
            "phase_2_attack": ["PKG03", "PKG04", "PKG02"],
            "phase_2_timing": "Within 7 days of Phase 1",
            "phase_3_escalate": ["PKG05", "PKG08"],
            "phase_3_timing": "After trial court acts on Phase 1-2 (PKG05 by Apr 15)",
            "phase_4_nuclear": ["PKG06", "PKG07", "PKG10"],
            "phase_4_timing": "After state remedies exhausted",
            "phase_5_parallel": ["PKG09"],
            "phase_5_timing": "Independent — file when ready",
        },
        "coa_countdown": {
            "deadline": "2026-04-15",
            "days_remaining": days_to_coa,
            "weeks_remaining": round(days_to_coa / 7, 1),
            "warning_level": "CRITICAL" if days_to_coa <= 30 else "URGENT" if days_to_coa <= 60 else "ACTIVE"
        }
    }
    
    write_json(os.path.join(D99, "DEADLINE_ENGINE.json"), deadlines)
    
    # Human-readable version
    md = f"""# DEADLINE & CALENDAR ENGINE

## Case: Pigors v. Watson | 2024-001507-DC | COA: 366810
## Generated: {today.strftime('%B %d, %Y')}

---

## ⚡ COA BRIEF COUNTDOWN: **{days_to_coa} DAYS** (April 15, 2026)

---

## ACTIVE DEADLINES

| Priority | Deadline | Days | Package | Authority |
|----------|----------|------|---------|-----------|
| 🔴 CRITICAL | COA Appellant Brief | **{days_to_coa}** | PKG05 | MCR 7.212 |
| 🔴 FILE NOW | Evidence Preservation | **0** | PKG11 | MCR 2.313(B) |
| 🟡 ASAP | Disqualification Motion | 14 from discovery | PKG03 | MCR 2.003(D) |
| 🟡 READY | Emergency PT Motion | Ready to file | PKG01 | MCR 3.207 |
| 🟡 READY | Void Ex Parte Orders | Ready to file | PKG04 | MCR 2.612 |
| 🟡 READY | Vacate PPO | Ready to file | PKG02 | MCR 3.707 |
| 🟡 READY | Contempt Motion | Ready to file | PKG08 | MCR 3.606 |
| 🟢 WATCH | FOC Objection | 21 days from trigger | PKG12 | MCL 552.507 |
| 🟢 FUTURE | MSC Bypass | 42 days if COA >180d | PKG07 | MCR 7.305 |
| 🟢 SAFE | Federal §1983 | ~850+ days | PKG10 | 28 USC 1658 |
| ⚪ NONE | JTC Investigation | No deadline | PKG06 | MCR 9.207 |
| ⚪ NONE | Housing Complaint | SOL check needed | PKG09 | MCL 600.5805 |

---

## OPTIMAL FILING SEQUENCE

### Phase 1: ESTABLISH THE RECORD (File ASAP)
- PKG01 — Emergency Parenting Time Motion
- PKG11 — Evidence Preservation / Spoliation Notice
- PKG12 — FOC Objection (if FOC recommendation issued)

### Phase 2: ATTACK THE PROCESS (Within 7 days of Phase 1)
- PKG03 — Disqualify Judge McNeill
- PKG04 — Void Ex Parte Orders (August 8, 2025)
- PKG02 — Vacate/Terminate PPO

### Phase 3: ESCALATE (After trial court acts)
- PKG05 — **COA Appellant Brief (HARD DEADLINE: April 15, 2026)**
- PKG08 — Contempt Motion (enforce any orders gained)

### Phase 4: NUCLEAR (After state remedies exhausted)
- PKG06 — JTC Request for Investigation
- PKG07 — MSC Application for Leave to Appeal
- PKG10 — Federal §1983/§1985 Action

### Phase 5: PARALLEL
- PKG09 — Housing Complaint (60th District Court)

---

## CRITICAL PATH: COA BRIEF (PKG05)

The COA brief is the highest-priority deadline. Everything else supports it.

### Required Before Filing:
- [ ] Transcript obtained (or settled statement under MCR 7.210(B)(3))
- [ ] Lower court record certified by clerk
- [ ] Reproduced materials addendum compiled
- [ ] Word count statement (≤16,000 words)
- [ ] COA Proof of Service form completed
- [ ] MC 20 fee waiver (if needed for COA)
- [ ] Blue cover page with ORAL ARGUMENT REQUESTED

### Milestone Targets:
| Milestone | Target Date | Days Out |
|-----------|-------------|----------|
| Transcript ordered | IMMEDIATELY | {days_to_coa} |
| Brief draft complete | March 25, 2026 | {(datetime(2026,3,25)-today).days} |
| Final review | April 5, 2026 | {(datetime(2026,4,5)-today).days} |
| Proofread + format | April 10, 2026 | {(datetime(2026,4,10)-today).days} |
| **FILE** | **April 14, 2026** | **{(datetime(2026,4,14)-today).days}** |
| DEADLINE | April 15, 2026 | {days_to_coa} |

---

*Generated by LitigationOS Deadline Engine*
"""
    write_md(os.path.join(D99, "DEADLINE_ENGINE.md"), md)
    log(f"  Deadline engine built — COA: {days_to_coa} days remaining")

# ============================================================
# 3. DOCKET MONITOR CONFIGURATION
# ============================================================
def build_docket_monitor():
    config = {
        "monitor_name": "LitigationOS Docket Monitor",
        "version": "1.0.0",
        "targets": [
            {
                "case_number": "2024-001507-DC",
                "court": "14th Circuit Court, Muskegon County",
                "court_id_district": "D60",
                "parties": {
                    "plaintiff": "Andrew J. Pigors",
                    "defendant": "Tiffany Emily Watson",
                    "counsel_defendant": "Jennifer L. Barnes, Barnes Law Firm PLLC"
                },
                "monitor_events": [
                    "NEW_FILING", "ORDER_ENTERED", "HEARING_SCHEDULED",
                    "HEARING_CANCELLED", "JUDGE_CHANGE", "MOTION_FILED",
                    "RESPONSE_FILED", "STATUS_CHANGE", "APPEARANCE_FILED"
                ]
            },
            {
                "case_number": "366810",
                "court": "Michigan Court of Appeals",
                "parties": {
                    "appellant": "Andrew J. Pigors",
                    "appellee": "Tiffany Emily Watson"
                },
                "monitor_events": [
                    "BRIEF_FILED", "ORDER_ENTERED", "OPINION_ISSUED",
                    "ORAL_ARGUMENT_SCHEDULED", "MOTION_FILED", "RESPONSE_DUE"
                ]
            }
        ],
        "api_config": {
            "base_url": "https://micourt.courts.michigan.gov/CaseSearch/api/v1",
            "auth_type": "OAuth2",
            "auth_provider": "OneCourtID",
            "poll_interval_seconds": 3600,
            "retry_attempts": 3,
            "retry_delay_seconds": 300
        },
        "alert_config": {
            "critical_events": ["ORDER_ENTERED", "HEARING_SCHEDULED", "JUDGE_CHANGE"],
            "high_events": ["MOTION_FILED", "RESPONSE_FILED", "BRIEF_FILED"],
            "medium_events": ["STATUS_CHANGE", "APPEARANCE_FILED"],
            "output_file": os.path.join(D99, "DOCKET_ALERTS.json")
        },
        "record_verification": {
            "enabled": True,
            "description": "Compare MiCourt API results against personal filing log",
            "filing_log": os.path.join(D99, "PERSONAL_FILING_LOG.json"),
            "discrepancy_report": os.path.join(D99, "RECORD_DISCREPANCIES.json")
        },
        "opposition_tracking": {
            "enabled": True,
            "counsel": "Jennifer L. Barnes",
            "firm": "Barnes Law Firm PLLC",
            "track": ["filing_frequency", "motion_types", "response_patterns"]
        }
    }
    
    write_json(os.path.join(D99, "DOCKET_MONITOR_CONFIG.json"), config)
    log(f"  Docket monitor configuration built")

# ============================================================
# 4. FOIA CAMPAIGN GENERATOR
# ============================================================
def build_foia_campaign():
    content = """# FOIA CAMPAIGN — STRATEGIC RECORDS REQUESTS

## Case: Pigors v. Watson | 2024-001507-DC

---

> **LEGAL BASIS:** Michigan Freedom of Information Act, MCL 15.231 et seq.
> **NOTE:** Michigan judiciary is EXEMPT from FOIA. Use MCR 8.119 for court records.
> Only county/state agencies are FOIA-eligible.

---

## TIER 1 — FILE IMMEDIATELY

### FOIA Request #1: Muskegon County — Tyler Technologies Contract
**To:** Muskegon County Clerk / Purchasing Department
**Records Sought:**
- Contract(s) between Muskegon County and Tyler Technologies for Odyssey Case Manager
- Maintenance and support agreements
- Implementation documentation
- Any amendments or change orders
- Total contract value and payment history

**Purpose:** Understand system capabilities, audit trail features, data retention policies.
Relevant to PKG04 (record integrity) and PKG06 (system-level misconduct documentation).

---

### FOIA Request #2: Kent County Prosecutor — Conflict Policies
**To:** Kent County Prosecutor's Office, Administration
**Records Sought:**
- Employee conflict of interest policies
- Policies regarding employee involvement in personal litigation using office resources
- Any communications regarding Tiffany Watson and/or family court cases
- Access logs to prosecutor databases for Watson's user account (if lawful)

**Purpose:** Establish whether prosecutorial resources were used in private custody case.
Relevant to PKG03, PKG06, PKG10 (prosecutorial nexus).

---

### FOIA Request #3: MDHHS — CPS Investigation Records
**To:** Michigan Department of Health and Human Services, Children's Services Agency
**Records Sought:**
- Any CPS complaint, investigation, or finding involving Andrew Pigors and/or Lincoln Watson
- Any CPS complaint filed by or through Tiffany Watson
- Investigation outcome documents
- Investigator assignment records

**Purpose:** Document whether CPS system was weaponized. Negative drug screen = cleared.
Relevant to PKG01, PKG10 (state actor deprivation of rights).

**Note:** MCL 722.627 governs confidentiality of CPS records. As a subject of investigation,
the parent has a right to access under MCL 722.627(2).

---

## TIER 2 — FILE AFTER PHASE 1

### FOIA Request #4: Muskegon FOC — Investigation Protocols
**To:** Muskegon County Friend of the Court
**Records Sought:**
- Investigation protocols and procedural manuals
- Training materials for custody/parenting time investigations
- Statistical reports on investigation outcomes (grant/deny rates)
- Any specific communications or notes regarding Case 2024-001507-DC

**Purpose:** Compare FOC investigation to SCAO Custody & PT Investigation Manual standards.
Relevant to PKG12 (FOC Objection).

---

### FOIA Request #5: Muskegon County — Judicial Recusal History
**To:** Muskegon County Clerk
**Records Sought:**
- Records of any recusal or disqualification motions involving Judge Jenny L. McNeill
- Outcomes of those motions
- Statistical data on disqualification motions in 14th Circuit (past 5 years)

**Purpose:** Establish pattern (or lack thereof) of judicial accountability.
Relevant to PKG03 (Disqualification) and PKG06 (JTC).

**Note:** This may be partially covered by MCR 8.119 (open court records) rather than FOIA.

---

## TIER 3 — STRATEGIC

### FOIA Request #6: SCAO — MiFILE Filing Statistics
**To:** State Court Administrative Office
**Records Sought:**
- MiFILE filing statistics for 14th Circuit Court (processing times, rejection rates)
- Any system audit reports
- Electronic Document Standards compliance reports

**Purpose:** Establish baseline for e-filing reliability and processing integrity.

---

### FOIA Request #7: Muskegon County — UpTrust/AllPaid Contracts
**To:** Muskegon County Purchasing
**Records Sought:**
- Contracts with UpTrust (payment plan communications)
- Contracts with AllPaid (online payment processing)
- Fee schedules and revenue sharing arrangements

**Purpose:** Understand financial infrastructure and potential fee abuse.

---

## FOIA TEMPLATE

```
[Date]

[Agency Name]
[Address]

Re: Freedom of Information Act Request (MCL 15.231 et seq.)

Dear FOIA Coordinator:

Under the Michigan Freedom of Information Act, MCL 15.231 et seq., I request
copies of the following records:

[SPECIFIC RECORDS DESCRIBED]

I request a fee waiver under MCL 15.234(1) as this request is in the public
interest and will contribute significantly to public understanding of government
operations.

If fees exceed $20, please notify me before processing.

I expect a response within 5 business days as required by MCL 15.235(2).

Sincerely,
Andrew J. Pigors
1977 Whitehall Rd Lot 17
Laketon Twp, MI 49445
(231) 903-5690
```

---

*Generated by LitigationOS FOIA Campaign Engine*
"""
    write_md(os.path.join(D99, "FOIA_CAMPAIGN.md"), content)
    log(f"  FOIA campaign plan built")

# ============================================================
# 5. RECORD INTEGRITY VERIFICATION PROTOCOL
# ============================================================
def build_record_verification():
    content = """# RECORD INTEGRITY VERIFICATION PROTOCOL

## Purpose: Detect Discrepancies Between Court Records and Personal Filing Records

---

## METHODOLOGY

### Step 1: Obtain Official Register of Actions
1. Visit 14th Circuit Court Clerk's Office
2. Request certified copy of Register of Actions for Case 2024-001507-DC
3. Pay certification fee (or request fee waiver via MC 20)
4. **Alternative:** Pull case data from MiCourt Case Search API

### Step 2: Build Personal Filing Log
Document every filing YOU have made with:
- Date filed
- Document name
- Method (MiFILE, hand-delivery, mail)
- Confirmation number (MiFILE) or stamped copy
- Certificate of service date and method

### Step 3: Cross-Reference
Compare your filing log against the ROA for:

| Check | What to Look For | Impact if Discrepant |
|-------|-------------------|---------------------|
| Filing dates | Your date vs clerk's date | Late filing = potential dismissal |
| Document presence | All filings appear | Missing filing = denied access |
| Event codes | Correct categorization | Wrong code = wrong statistics |
| Order dates | When orders were actually entered | Timing affects appeal deadlines |
| Service records | Service marked correctly | Improper service = defective process |
| Hearing dates | Scheduled vs actual | Discrepancy = due process issue |

### Step 4: Document Discrepancies
For each discrepancy:
1. Screenshot MiCourt API results
2. Compare to your stamped/confirmed copy
3. Write discrepancy memo (date, expected vs actual, significance)
4. Preserve as exhibit for PKG04 and PKG05

### Step 5: Remediation
If discrepancies found:
- File motion to correct register of actions
- Include as evidence in PKG04 (void orders) and PKG05 (COA brief)
- Reference in PKG06 (JTC — clerk/system integrity concerns)
- If systemic, reference in PKG10 (federal — state actor conduct)

---

## MiCOURT API VERIFICATION SCRIPT

```python
# Conceptual — requires OneCourtID OAuth2 credentials
import requests, json

API_BASE = "https://micourt.courts.michigan.gov/CaseSearch/api/v1"
CASE = "2024-001507-DC"

def get_case_data(token, subscription_key):
    headers = {
        "Authorization": f"Bearer {token}",
        "Ocp-Apim-Subscription-Key": subscription_key
    }
    resp = requests.get(
        f"{API_BASE}/search",
        params={"caseNumber": CASE, "limit": 100},
        headers=headers
    )
    return resp.json()

def compare_to_filing_log(api_data, filing_log):
    discrepancies = []
    for filing in filing_log:
        found = False
        for api_entry in api_data.get("cases", [{}])[0].get("events", []):
            if filing["date"] == api_entry.get("date") and \\
               filing["type"] in api_entry.get("description", ""):
                found = True
                break
        if not found:
            discrepancies.append({
                "filing": filing,
                "status": "NOT FOUND IN ROA",
                "severity": "CRITICAL"
            })
    return discrepancies
```

---

## INDEPENDENT VERIFICATION SOURCES

| Source | What It Proves | How to Obtain |
|--------|---------------|---------------|
| MiFILE confirmation email | Filing was received | Your email records |
| AllPaid receipt | Fee was paid | AllPaid account or email |
| USPS tracking | Mail service completed | USPS.com tracking |
| MiCourt API snapshot | Current state of ROA | API query (save JSON) |
| Clerk's certified copy | Official record | Request at courthouse |
| Personal stamped copy | You filed on X date | Your copy with clerk stamp |

---

*Generated by LitigationOS Record Integrity Verification Protocol*
"""
    write_md(os.path.join(D99, "RECORD_INTEGRITY_PROTOCOL.md"), content)
    log(f"  Record integrity verification protocol built")

# ============================================================
# RUN ALL
# ============================================================
def run_all():
    log("=" * 60)
    log("COURT INFRASTRUCTURE INTELLIGENCE ENGINE — BUILDING ALL")
    log("=" * 60)
    
    build_infrastructure_intel()
    build_deadline_engine()
    build_docket_monitor()
    build_foia_campaign()
    build_record_verification()
    
    outputs = [
        "COURT_INFRASTRUCTURE_INTELLIGENCE.md",
        "DEADLINE_ENGINE.md",
        "DEADLINE_ENGINE.json",
        "DOCKET_MONITOR_CONFIG.json",
        "FOIA_CAMPAIGN.md",
        "RECORD_INTEGRITY_PROTOCOL.md",
    ]
    
    log(f"\n  NEW STRATEGIC DOCUMENTS: {len(outputs)}")
    for f in outputs:
        path = os.path.join(D99, f)
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024
            log(f"    {f}: {size:.1f}KB")
    
    log("=" * 60)
    log("COURT INFRASTRUCTURE INTELLIGENCE — COMPLETE")
    log("=" * 60)

if __name__ == "__main__":
    run_all()