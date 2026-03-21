# Criminal Evidence Scanner Skill

## Purpose
Scan the central litigation database for evidence of criminal statutes violated by opposing parties in Pigors v. Watson. Identifies prosecutable criminal conduct by Emily Watson, Ronald Berry, Jennifer Barnes, Judge McNeill, Pamela Rusco, and Watson family members.

## When to Use
- User asks about criminal evidence, prosecution potential, or criminal referrals
- User asks "what crimes did Emily/Berry/McNeill commit?"
- User wants to compile evidence for criminal complaint or police report
- User needs felony vs misdemeanor breakdown
- User asks about perjury, conspiracy, UPL, custodial interference, fraud on court

## Tool Location
`C:\Users\andre\LitigationOS\00_SYSTEM\tools\criminal_evidence_scanner.py`

## How to Run
```powershell
cd C:\Users\andre\LitigationOS\00_SYSTEM\tools && python criminal_evidence_scanner.py
```

## What It Scans
12 criminal statutes across 57+ database tables:

| Statute | Crime | Felony? | Key Perpetrators |
|---------|-------|---------|-----------------|
| MCL 750.423 | Perjury | YES (15yr) | Emily, Berry, Barnes |
| MCL 750.424 | Subornation of Perjury | YES | Berry, Barnes |
| MCL 750.157a | Criminal Conspiracy | YES (5yr) | Emily, Berry, Barnes, McNeill |
| MCL 750.350a | Custodial Interference | YES (1yr) | Emily, Berry, Lori Watson |
| MCL 600.916 | Unauthorized Practice of Law | Misdemeanor | Berry |
| MCL 764.15a | Filing False Police Report | Misdemeanor (93d) | Emily |
| MCL 750.218 | False Pretenses/Fraud | Misdemeanor | Emily, Berry |
| MCL 750.120a | Witness Tampering | Felony (4yr) | Emily, Berry, McNeill |
| MCL 750.81d | False DV Allegations | Misdemeanor | Emily |
| 42 USC 1983 | Deprivation of Rights | Federal civil | McNeill, Emily, Barnes, Rusco |
| MCR 2.612(C) | Fraud Upon the Court | Court sanction | Emily, Berry, Barnes |
| Contempt | Criminal/Civil Contempt | Court sanction | Emily |

## Outputs
- **DB Table**: `criminal_evidence_scan` in litigation_context.db
- **MD Report**: `00_SYSTEM/reports/tool_262_criminal_evidence.md`
- **JSON Report**: `00_SYSTEM/reports/tool_262_criminal_evidence.json`

## Key Metrics (Last Run)
- 16,634 total evidence items
- 33 prosecution records (statute × perpetrator combinations)
- 5 felony statutes with sufficient evidence
- 57 database tables scanned
- All 12 statutes show prosecutable evidence

## Perpetrator Profiles
7 perpetrator profiles with role-specific search patterns:
- **Emily Watson**: Primary perpetrator — perjury, false allegations, custodial interference
- **Ronald Berry**: Co-conspirator — UPL, conspiracy, witness tampering
- **Jennifer Barnes (P55406)**: Former attorney — subornation, conspiracy, fraud on court
- **Judge McNeill**: Judicial misconduct — §1983, conspiracy, witness intimidation
- **Pamela Rusco**: FOC — §1983, bias, due process violations
- **Lori Watson**: Emily's mother — custodial interference, conspiracy
- **Albert Watson**: Emily's father — witness tampering, conspiracy

## Integration
- Results feed into filing packages F3 (§1983), F7 (JTC), F10 (Criminal Referral)
- Cross-references with `actor_violations`, `evidence_quotes`, `contradiction_map` tables
- Uses FTS5 indexes for fast searching on large tables (168K+ rows)
