# 7-PHASE LIFECYCLE OVERVIEW

## THE NEW LAWSUIT LIFECYCLE STATE MACHINE

Every lawsuit follows the same fundamental lifecycle. Skipping phases or rushing through quality gates produces defective complaints that get dismissed. This system enforces discipline.

---

## PHASE MAP

```
┌──────────┐    ┌──────────────┐    ┌─────────────┐    ┌───────────────┐
│ PHASE 1  │───►│   PHASE 2    │───►│   PHASE 3   │───►│    PHASE 4    │
│ RESEARCH │    │ IDENTIFY     │    │ MAP         │    │ DRAFT         │
│          │    │ CLAIMS       │    │ ELEMENTS    │    │ COMPLAINT     │
└──────────┘    └──────────────┘    └─────────────┘    └───────────────┘
                                                              │
┌──────────┐    ┌──────────────┐    ┌─────────────┐          │
│ PHASE 7  │◄───│   PHASE 6    │◄───│   PHASE 5   │◄─────────┘
│ SERVE    │    │ FILE         │    │ PREPARE     │
│          │    │              │    │ FORMS       │
└──────────┘    └──────────────┘    └─────────────┘
      │
      ▼
 CASE ACTIVE
```

## PHASE DETAIL REFERENCES

| PHASE | NAME | REFERENCE | KEY DELIVERABLE |
|-------|------|-----------|-----------------|
| 1 | Research | claim-identification.md (initial) | Master fact compilation |
| 2 | Identify Claims | claim-identification.md | Viable claims list with SOL audit |
| 3 | Map Elements | elements-mapping.md | Element-evidence matrix |
| 4 | Draft Complaint | complaint-architecture.md | Verified complaint draft |
| 5 | Prepare Forms | ../forms/README.md | Complete filing package |
| 6 | File | ../forms/README.md | Case number, stamped copies |
| 7 | Serve | ../forms/service-matrix.md | Proof of service, answer deadlines |

## QUALITY GATES

Quality gates are non-negotiable checkpoints. A phase cannot transition to the next phase until its quality gate is passed.

### GATE 1 → 2: RESEARCH COMPLETE
- [ ] All known facts documented with dates, participants, evidence
- [ ] Master timeline built and verified
- [ ] All potential defendants identified with correct legal names
- [ ] All documents cataloged and indexed
- [ ] All witnesses identified with contact information
- [ ] No major factual gaps identified (or gaps documented with remediation plan)

### GATE 2 → 3: CLAIMS LOCKED
- [ ] Every viable cause of action identified
- [ ] SOL confirmed unexpired for each claim (with exact expiry dates)
- [ ] Jurisdiction confirmed for each claim
- [ ] Venue confirmed correct
- [ ] Non-viable claims documented and excluded with reasoning
- [ ] Cross-claims and counterclaims identified if applicable
- [ ] Claims assigned to defendants

### GATE 3 → 4: ELEMENT MAP APPROVED
- [ ] Every element of every claim listed
- [ ] Each element mapped to specific evidence
- [ ] No fatal evidence gaps (or gap-filling plan in place)
- [ ] Burden of proof posture assessed per claim
- [ ] Claim strength scores calculated (minimum 60% to proceed)
- [ ] Special pleading requirements identified (fraud particularity, etc.)

### GATE 4 → 5: COMPLAINT APPROVED
- [ ] MCR 2.111 format compliance verified
- [ ] MCR 2.112 special pleading requirements met
- [ ] MCR 2.113 caption requirements met
- [ ] Every element of every count is pled
- [ ] Jury demand included (MCR 2.508(B))
- [ ] All citations verified as current and correct
- [ ] Verification language correct
- [ ] Exhibit list complete and accurate

### GATE 5 → 6: FILING PACKAGE ASSEMBLED
- [ ] All required forms completed and signed
- [ ] Correct number of copies prepared
- [ ] Filing fee calculated or MC 20 fee waiver completed
- [ ] Summons prepared for each defendant
- [ ] Exhibit package assembled and tabbed
- [ ] Service plan documented for each defendant

### GATE 6 → 7: FILING CONFIRMED
- [ ] Case number obtained from clerk
- [ ] All documents accepted by clerk
- [ ] Stamped copies received
- [ ] Filing date recorded
- [ ] 91-day service deadline calculated and calendared (MCR 2.102(D))
- [ ] All post-filing deadlines calendared

### GATE 7 → CASE ACTIVE: SERVICE COMPLETE
- [ ] All defendants served within 91 days of filing
- [ ] Service method compliant with MCR 2.105 for each defendant type
- [ ] Proof of service (MC 12) filed for each defendant
- [ ] Answer deadlines calculated and calendared per MCR 2.108
- [ ] No service defects identified

## EMERGENCY FAST-TRACK

When SOL is expiring within 30 days or emergency relief is needed:

```
PHASE 1 (abbreviated) → PHASE 4 (minimal viable complaint) → PHASE 5 → PHASE 6
     │
     └──► File immediately, then:
          PHASE 2 → PHASE 3 → Amended Complaint → PHASE 7
```

This fast-track files a minimal viable complaint to preserve claims, then follows up with a comprehensive amended complaint after proper analysis. Use ONLY when time pressure demands it.

## PARALLEL TRACKS

Some situations require parallel processing:

- **TRO Track:** Complaint + Emergency Motion for TRO filed simultaneously (MCR 3.310)
- **Discovery Track:** Discovery requests served with complaint (permitted in Michigan)
- **Preservation Track:** Motion for evidence preservation order filed with complaint
- **Fee Waiver Track:** MC 20 filed simultaneously with complaint

## METRICS AND MONITORING

Track these metrics for each lawsuit build:

| METRIC | TARGET | ALERT |
|--------|--------|-------|
| Total build time (phases 1-7) | < 30 days | > 45 days |
| Claims identified vs. viable | > 70% viable | < 50% viable |
| Element coverage per claim | 100% | < 90% |
| Service completion | < 60 days from filing | > 75 days |
| Quality gate pass rate | 100% first pass | Any gate failed |
