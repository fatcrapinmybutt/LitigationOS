---
name: litigation-service-engine
description: >-
  Use when serving process on any party type in Michigan — including method selection,
  execution steps, proof of service filing, troubleshooting failed service, and
  alternative service methods under MCR 2.103-2.107.
metadata:
  category: discipline
  author: andrew-pigors
  version: "1.0.0"
  triggers: service, serve, proof of service, MC 12, process
---
# litigation-service-engine

> **Category:** discipline
> **Tier:** 2
> **Jurisdiction:** Michigan — 14th Judicial Circuit, Muskegon County
> **Context:** Pigors v Watson, pro se litigation

## Description

Use when you need to serve process on any party type in Michigan — including method selection, execution steps, proof of service filing, troubleshooting failed service, and alternative service methods under MCR 2.103-2.107.

## Triggers

- User has filed a complaint and needs to serve defendants
- User needs to determine the correct service method for a specific party type
- User needs help with proof of service forms (MC 12)
- User needs service by publication (MCR 2.106) procedures
- User is troubleshooting failed or defective service
- User needs to serve additional parties (third-party, cross-claim, amended complaint)
- User needs to serve out-of-state defendants under long-arm jurisdiction

## Service Method Decision Tree

### Step 1 — Identify Party Type

| Party Type | Primary Service Method | Authority |
|-----------|----------------------|-----------|
| **Individual (Michigan resident)** | Personal service OR registered mail | MCR 2.105(A)(1)-(2) |
| **Individual (out-of-state)** | Long-arm service | MCR 2.105(J); MCL 600.701-745 |
| **Corporation (Michigan)** | Serve officer, resident agent, or LARA | MCR 2.105(D) |
| **Corporation (foreign)** | Serve registered agent or LARA | MCR 2.105(D) |
| **LLC** | Serve member, manager, or registered agent | MCR 2.105(D) (by analogy); MCL 450.4207 |
| **Partnership** | Serve any partner or agent | MCR 2.105(E) |
| **Government (state)** | Serve Attorney General | MCR 2.105(G)(1) |
| **Government (local)** | Serve chief executive or clerk | MCR 2.105(G)(2) |
| **Unknown defendant ("John Doe")** | Service by publication | MCR 2.106 |

### Step 2 — Select Specific Method

#### For Individuals — MCR 2.105(A):

**Method 1: Personal Service** (preferred)
- Process server personally delivers summons + complaint to the defendant
- Must identify the person and hand them the documents
- If defendant refuses to accept, placing documents at their feet constitutes service

**Method 2: Service at Defendant's Dwelling**
- Leave copies at the defendant's usual place of abode
- Must be with a person of suitable age and discretion residing therein
- MCR 2.105(A)(2)

**Method 3: Registered or Certified Mail**
- Send summons + complaint by registered or certified mail, return receipt requested
- Addressed to defendant's last known address
- Must receive signed return receipt — unsigned/unclaimed = NOT served
- MCR 2.105(A)(2)

**Method 4: Tacking/Posting (last resort before publication)**
- Attach to defendant's door if no one answers after multiple attempts
- Must also mail a copy by first-class mail
- MCR 2.105(A)(3) — only after diligent attempts at personal service

### Step 3 — Execute Service

**Timing Requirements:**
- Summons expires 91 days after issuance — MCR 2.102(D)
- Service must be completed within the summons validity period
- If summons expires before service, request a new summons from the clerk

**Who May Serve — MCR 2.103(A):**
- Any legally competent adult who is NOT a party to the action
- Professional process server (recommended for reliability)
- County sheriff or deputy
- NOT the plaintiff — pro se plaintiffs cannot serve their own process

### Step 4 — File Proof of Service

After service is accomplished, file proof of service with the court:
- **MC 12 form** (Michigan court standard form)
- Affidavit of service by the process server
- Return receipt (for service by mail)
- Must be filed with the clerk within a reasonable time

## Service After Filing — MCR 2.107

For documents filed AFTER the initial complaint (motions, discovery, amended pleadings):
- Service on parties who have appeared: by mail, hand delivery, or electronic service
- Must serve ALL parties who have appeared in the case
- Certificate of service required on every filed document

## Alternative Service — MCR 2.105(I)

When standard methods fail, move for alternative service:
1. File motion explaining diligent but unsuccessful attempts
2. Propose alternative method (email, social media, posting at workplace)
3. Court must find the alternative method reasonably calculated to give notice
4. Order specifies exact method and timeline

## Publication Service — MCR 2.106

### When Available:
- Defendant cannot be found after diligent search
- Defendant's address is unknown
- Used for unknown parties ("John Doe")

### Requirements:
1. File affidavit of diligent search (describe all efforts to locate defendant)
2. Obtain court order authorizing publication
3. Publish in newspaper of general circulation in county where defendant was last known
4. Publish once per week for 3 consecutive weeks — MCR 2.106(D)
5. Mail copy to defendant's last known address (if any) — MCR 2.106(E)
6. File proof of publication with court

## Service Troubleshooting

| Problem | Solution |
|---------|---------|
| Defendant avoids personal service | Attempt substitute service, then move for alternative service |
| Registered mail returned unclaimed | Attempt personal service, then substitute service |
| Wrong address | Research correct address (LARA, SOS, property records, voter registration) |
| Summons expired before service | Request new summons from clerk, re-serve |
| Defendant is out of state | Use long-arm service — see `references/special-service.md` |
| Defendant is a dissolved corporation | Serve last known officer or registered agent; check LARA records |
| Can't identify registered agent | Search LARA Corporate Entity database online |

## Quality Gates

Before considering service complete:
- [ ] Correct service method for this party type confirmed
- [ ] Summons was valid (not expired) at time of service
- [ ] Server was competent and not a party to the action
- [ ] Proof of service filed with clerk
- [ ] All defendants served (not just some)
- [ ] Service timeline within 91-day summons period

## Cross-References

- **Skill 23** (litigation-complaint-drafter): The complaint that gets served
- **Skill 22** (litigation-cause-of-action-library): Claims determine who to serve

## Related Skills

- [litigation-complaint-drafter](skill://litigation-complaint-drafter) — Drafts verified complaints per MCR
- [litigation-filing-architect](skill://litigation-filing-architect) — Architects court-ready filing packages


---

## 🔬 Pass 1: Data Intelligence Layer
*Enhanced: 2026-03-12 | Source: mega_file_harvest (53,625 files)*

### Live Database Arsenal
| Table | Records | Intelligence Value |
|-------|--------:|-------------------|
| `mega_file_harvest` | 53,625 | Complete file index with citations and metadata |
| `evidence_quotes` | 308,704 | Extracted evidence passages with legal significance |
| `contradiction_map` | 10,672 | Detected contradictions across all documents |
| `impeachment_items` | 15,171 | Impeachment-ready witness inconsistencies |
| `judicial_violations` | 1,127 | Documented judicial conduct violations |
| `pages` | 472,482 | Raw page text from ingested documents |
| `master_citations` | 3,684,757 | Extracted citations across all sources |
| `claims` | 653 | Active claims matrix with status tracking |
| `vehicles` | 6 | Filing vehicles with readiness scores |
| `authority_chains` | 28 | Authority chains with completeness scoring |
| `filing_readiness` | 24 | Per-vehicle filing readiness assessment |

### Governing Authority (Verified)
**MCR:** MCR 2.103, MCR 2.104, MCR 2.105, MCR 2.106, MCR 2.107, MCR 2.119(C)
**MCL:** MCL 600.1910, MCL 600.1911, MCL 600.1915
**Binding Cases:**
- *Krueger v Williams, 300 Mich App 692*

### Case Lane Intelligence
| Lane | Files Indexed | Case | Court |
|------|-------------:|------|-------|
| E | 9,945 | JTC Complaint - McNeill | Judicial Tenure Commission |

### Harvest-Discovered Citations (New)
| MCR Citation | Files Found | Status |
|-------------|----------:|--------|
| MCR 2.003 | 1980 | 🆕 Verify & integrate |
| MCR 2.119 | 1635 | 🆕 Verify & integrate |
| MCR 3.207 | 1302 | 🆕 Verify & integrate |
| MCR 3.207(B) | 933 | 🆕 Verify & integrate |
| MCR 2.003(C)(1) | 882 | 🆕 Verify & integrate |
| MCR 2.105 | 871 | 🆕 Verify & integrate |
| MCR 2.313 | 868 | 🆕 Verify & integrate |
| MCR 3.203 | 850 | 🆕 Verify & integrate |
| MCR 1.109 | 795 | 🆕 Verify & integrate |
| MCR 3.606 | 766 | 🆕 Verify & integrate |

### FTS5 Query Templates
```sql
-- Search evidence for this skill's domain
SELECT * FROM pages_fts WHERE pages_fts MATCH 'judicial AND misconduct OR bias';
```

## 🔗 Pass 2: Cross-Skill Integration Matrix
*Enhanced: 2026-03-12 | 71 skills in fleet*

### Direct Integration Points
| Skill | Relationship | Data Flow |
|-------|-------------|-----------|
| `litigation-analysis-engine` | Integration | Bidirectional data exchange |
| `litigation-authority-validator` | Integration | Receives citations → validates authority chains |
| `litigation-filing-architect` | Integration | Provides readiness scores → filing decisions |
| `litigation-red-team` | Integration | Receives outputs → adversarial stress testing |

### Cross-Lane Evidence Routing
| Source Lane | Target Lane | Connection Pattern |
|-----------|------------|-------------------|
| A (Custody (Pigors v Watson)) | E | Biased rulings → JTC complaint evidence |
| D (PPO (Protection Orders)) | E | Improper PPO issuance → judicial bias pattern |
| E (Judicial Misconduct (JTC)) | F | Misconduct findings → appellate arguments |

### OMEGA Pipeline Phase Mapping
```
This skill operates across these pipeline phases:
  Ω-3 Evidence Harvest → Ω-5 Claim Mapping → Ω-6 Contradiction Detection
  Ω-9 Gap Analysis → Ω-11 Risk Assessment → Ω-12 Filing Readiness
```

## ⚡ Pass 3: Elite Combat Refinement
*Enhanced: 2026-03-12 | EGCP-scored | Adversarial-hardened*

### EGCP Filing Thresholds
| Filing Type | Min EGCP | Lane | Authority |
|------------|--------:|------|-----------|
| Judicial Disqualification | 75/100 | E | Verified |
| JTC Formal Complaint | 75/100 | E | Verified |

### Adversarial Defense Matrix
| Attack Vector | Defense | Skill Response |
|-------------|---------|---------------|
| Opposing motion to strike evidence | Pre-authenticate under MRE 901-903 | Run litigation-evidence-authentication |
| Challenge to standing | Verify party status and injury-in-fact | Document concrete harm with citations |
| Laches/statute of limitations | Verify timeliness under MCL/MCR | Check deadline_sentinel calculations |
| Hearsay objection | Map to MRE 801-807 exceptions | Pre-classify all evidence by exception |
| Judicial discretion argument | Identify abuse-of-discretion factors | Score against published standards |
| Mootness challenge | Show continuing controversy or capable-of-repetition | Document ongoing harm pattern |

### Quality Gates (Pre-Output Checklist)
```
□ All citations verified against authority_chains table
□ No hallucinated case names or statute numbers
□ Cross-lane contamination check passed (MEEK signal verified)
□ EGCP score meets filing threshold for target vehicle
□ Pinpoint citations include page + paragraph references
□ Opposing argument anticipated and addressed
□ Party names verified: Andrew J. Pigors, Emily A. Watson, L.D.W.
□ Judge name verified: Hon. Jenny L. McNeill (NOT McNeil)
□ Case numbers verified with leading zeros: 2024-001507-DC
□ No fabricated evidence (CPS = 1 call, NOT 9 investigations)
```

### Case-Specific Intelligence

**Lane E: Judicial Misconduct (JTC)**
- Case: JTC Complaint - McNeill
- Court: Judicial Tenure Commission
- Judge: Target: Hon. Jenny L. McNeill
- Key Statutes: Const 1963 art 6 § 30, MCR 9.104-9.205
- Key Rules: MCR 2.003, Code of Judicial Conduct
- Critical Evidence: 1,127 violations, 44% ex parte rate, muting father 7x in hearing

### Self-Evolution Protocol
```
After each use of this skill:
1. Log output quality score (1-10) to session SQL
2. Record any missing citations or evidence gaps discovered
3. Update lane-specific intelligence if new orders/events occurred
4. Cross-reference findings with contradiction_map for consistency
5. Feed results to litigation-red-team for adversarial validation
```
