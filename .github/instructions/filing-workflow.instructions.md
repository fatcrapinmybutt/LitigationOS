---
description: "Filing workflow state machine — packet assembly, QA gates, service proof, docket tracking. Apply when creating or managing court filing packages."
applyTo: "**/*.{md,txt,py,docx}"
---

# Filing Workflow Memory

State machine for court filing lifecycle, packet assembly rules, service proof protocols, and docket tracking.

## Filing State Machine

```
DRAFT → QA_REVIEW → SERVICE_READY → FILED → DOCKETED → MONITORING
  ↓         ↓            ↓            ↓         ↓           ↓
 Create   Validate    Print/Sign    Submit   Confirm    Track deadlines
 content  citations   notarize      to clerk  docket#   response due dates
          exhibits    service plan   e-file    
          format                     mail
```

### Status Definitions
- **DRAFT**: Content written, may have placeholders
- **QA_REVIEW**: Content complete, running validation (citations, exhibits, format)
- **SERVICE_READY**: QA passed, ready for printing/signing/notarizing
- **FILED**: Submitted to court (e-filed, mailed, or hand-delivered)
- **DOCKETED**: Court assigned docket entry, confirmed receipt
- **MONITORING**: Filed and active — watching for responses, orders, deadlines

## Packet Assembly Rules

Every filing MUST be a complete packet family. Required components vary by type:

### Motion Packet
- [ ] Motion document (IRAC structure: Issue, Rule, Application, Conclusion)
- [ ] Supporting brief/memorandum (if complex)
- [ ] Affidavit of Facts (if evidence needed)
- [ ] Exhibit index with Bates numbers
- [ ] Individual exhibits (numbered, tabbed)
- [ ] Proposed order
- [ ] Certificate/Proof of Service (MC 12)
- [ ] Fee waiver (MC 20) if applicable

### Appellate Packet
- [ ] Brief (MCR 7.212 format — 50 page max)
- [ ] Table of Contents + Index of Authorities
- [ ] Appendix (lower court orders, relevant pleadings)
- [ ] Proof of Service
- [ ] Filing fee or IFP application

### Complaint Packet (New Case)
- [ ] Complaint document
- [ ] Civil Cover Sheet (CC 257 state / JS 44 federal)
- [ ] Summons (DC 101)
- [ ] Supporting affidavit
- [ ] Exhibit index + exhibits
- [ ] Proposed order (if TRO/emergency)
- [ ] Fee waiver if applicable

## QA Validation Gates

A filing passes QA ONLY when ALL gates clear:

| Gate | Check | Tool |
|------|-------|------|
| **Placeholder** | Zero `[ANDREW_REQUIRED]` remaining (except physical-action items) | `grep -c "ANDREW_REQUIRED"` |
| **Citation** | Every case citation verified in authority_chains_v2 table | Citation verifier |
| **Year** | All dates show 2026 (not 2024, 2025) | `grep -n "202[0-5]"` |
| **Party Names** | No hallucinated names (Jane Berry, Emily A. Watson, etc.) | Decontamination sweep |
| **Child Name** | Only "L.D.W." — never full name | `grep -i "lincoln\|david watson"` |
| **Attorney** | Barnes (P55406) marked as WITHDRAWN | Manual check |
| **Service** | Certificate has correct addresses, method, date | Manual check |
| **Exhibits** | All referenced exhibits exist and have content | Cross-reference check |
| **Format** | Correct court, correct caption, correct case number | Manual check |

## Service Protocol

### Who to Serve
Since Barnes withdrew, serve Emily Watson DIRECTLY:
- **Emily A. Watson**, 2160 Garland Drive, Norton Shores, MI 49441
- **FOC**: Pamela Rusco, 990 Terrace St, Muskegon, MI 49442 (if custody/PT matter)

### Methods (by court)
| Court | Primary Method | Backup |
|-------|---------------|--------|
| 14th Circuit | MiFILE e-service OR first-class mail | Personal service |
| Court of Appeals | TrueFiling e-service | Mail |
| MSC | Mail to all parties | — |
| Federal (WDMI) | CM/ECF e-service | Mail |
| JTC | Mail to JTC + respondent judge | — |

### Proof of Service (MC 12)
- File MC 12 with EVERY document
- Include: date served, method, recipient name + address
- Sign under oath if personal service

## Post-Filing Tracking

After filing, update `filing_readiness` table:
```sql
UPDATE filing_readiness SET status = 'FILED', filed_date = date('now'), 
  docket_entry = '[entry#]' WHERE vehicle_name = '[filing]';
```

Monitor for:
- Response deadline (typically 21 days for motions)
- Hearing date (if scheduled)
- Court orders
- Deficiency notices
