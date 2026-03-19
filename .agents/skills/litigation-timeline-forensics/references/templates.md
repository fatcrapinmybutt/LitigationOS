# Templates — Timeline Forensics

## Master Timeline Template

| # | Date | Time | Event | Source | Authentication | Factor | Exhibit |
|---|------|------|-------|--------|---------------|--------|---------|
| 1 | 2023-XX-XX | | [Event description] | [Document type] | MRE 901(b)(1) | (j) | Ex. A |
| 2 | 2023-XX-XX | | [Event description] | [Record type] | MRE 803(6) | (k) | Ex. B |
| 3 | 2024-XX-XX | | [Event description] | [Text message] | MRE 901(b)(4) | (j) | Ex. C |
| 4 | 2024-XX-XX | | [Court filing] | [Court record] | MRE 902(4) | — | Ex. D |

## Court-Ready Timeline Summary

```
TIMELINE OF KEY EVENTS

Case: Pigors v. Watson, No. 2024-001507-DC

[DATE]     [CATEGORY]  [Description — 1-2 sentences max]
           Source: [Document, Exhibit reference]

[DATE]     [CATEGORY]  [Description]
           Source: [Document, Exhibit reference]

[DATE]     [CATEGORY]  [Description]
           Source: [Document, Exhibit reference]

Categories: CUSTODY | PPO | FINANCIAL | PARENTING TIME | HOUSING |
           MISCONDUCT | FILING | COURT ORDER

Note: This summary references exhibits attached to Plaintiff's
[Motion/Trial Brief]. Full timeline with all entries available
upon request.
```

## Evidence Source Cross-Reference Matrix

| Event | Text Msgs | Emails | Court Records | Financial | Medical | Witness | Photos |
|-------|-----------|--------|--------------|-----------|---------|---------|--------|
| Event 1 | ✓ | | ✓ | | | ✓ | |
| Event 2 | ✓ | ✓ | | ✓ | | | |
| Event 3 | | | ✓ | | ✓ | | ✓ |
| Event 4 | ✓ | | | | | ✓ | |

## Metadata Preservation Log

| File | Original Hash (SHA-256) | Creation Date | Modification Date | Source Device | Preserved By | Date Preserved |
|------|----------------------|--------------|------------------|--------------|-------------|---------------|
| text_screenshot_001.png | [hash] | [date] | [date] | [device] | A. Pigors | [date] |
| email_chain_002.pdf | [hash] | [date] | [date] | [account] | A. Pigors | [date] |
| court_order_003.pdf | [hash] | [date] | [date] | Court website | A. Pigors | [date] |

## Timeline Gap Analysis

| Period | Expected Evidence | Available Evidence | Gap | Action Needed |
|--------|------------------|-------------------|-----|--------------|
| Jan-Mar 2024 | Phone records | None | Full gap | Subpoena carrier |
| Mar-Jun 2024 | Text messages | Partial | Deleted msgs | Forensic recovery |
| Jun-Sep 2024 | Medical records | None | Full gap | Authorization/subpoena |
| Sep-Dec 2024 | All types | Complete | None | N/A |

## Workflow: Building a Litigation Timeline

```
Step 1: Inventory all available evidence sources
    ↓
Step 2: Request/subpoena missing records (phone, bank, medical)
    ↓
Step 3: Extract dates and events from each source
    ↓
Step 4: Preserve digital evidence with SHA-256 hashes
    ↓
Step 5: Enter all events into master timeline database
    ↓
Step 6: Cross-reference events across multiple sources
    ↓
Step 7: Identify gaps — issue additional discovery if needed
    ↓
Step 8: Verify internal consistency (no contradictions)
    ↓
Step 9: Map events to legal factors (MCL 722.23)
    ↓
Step 10: Create court-ready summary (2-5 pages, key events only)
    ↓
Step 11: Prepare authentication foundation for each exhibit
    ↓
Step 12: File as exhibit with motion or trial brief
```

## Authentication Foundation Guide

| Evidence Type | MRE Rule | Foundation Required | Who Can Authenticate |
|-------------|---------|-------------------|---------------------|
| Text messages | 901(b)(4) | Distinctive characteristics (phone number, content) | Recipient or sender |
| Emails | 901(b)(4) | Email address, content, headers | Recipient or sender |
| Phone records | 803(6) | Business records — carrier custodian | Carrier custodian |
| Bank statements | 803(6) | Business records — bank custodian | Bank custodian |
| Court records | 902(4) | Self-authenticating with certification | Court clerk |
| Photos (digital) | 901(b)(1) | Testimony of photographer or person who recognizes scene | Photographer or witness |
| Social media | 901(b)(4) | Distinctive characteristics + account identification | Person who accessed it |
| Medical records | 803(6) | Business records — records custodian | Records custodian |

## Common Anti-Patterns

| Anti-Pattern | Why It Fails | Better Approach |
|-------------|-------------|-----------------|
| Memory-based timeline | Inaccurate; impeachable; no foundation | Build from documents; use memory only for context |
| Ignoring metadata | Miss fabrication/alteration evidence | Extract and preserve metadata for all digital evidence |
| Cherry-picking events | Gaps expose bias; destroys credibility | Include all significant events; address unfavorable ones |
| Single-source construction | Incomplete; easily attacked | Cross-reference 3+ sources for key events |
| 50-page court submission | Judge won't read it; loses impact | Court summary (2-5 pages) + full version for preparation |
| No authentication plan | Exhibits excluded at trial | Plan MRE 901 foundation for every timeline entry |
