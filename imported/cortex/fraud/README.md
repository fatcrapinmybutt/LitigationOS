# CORTEX Fraud Detection Starter Pack

> Free intelligence pack for fraud investigation, forensic accounting, and financial crime detection.

**[CORTEX](https://fatcrapinmybutt.github.io/cortex-site/)** is an offline desktop intelligence platform that scans your local files and builds interactive knowledge graphs. This starter pack adds fraud detection capabilities.

## What This Pack Detects

| Entity Type | Examples | Color |
|---|---|---|
| Transaction | Wire transfers, ACH, refunds, chargebacks | Red |
| Financial Amount | Dollar amounts, cryptocurrency values | Green |
| Account | Account numbers, card numbers | Blue |
| Entity Name | LLC, Corp, Ltd entities | Purple |
| Suspicious Pattern | Structuring, shell companies, Ponzi schemes | Orange |
| Jurisdiction | Offshore jurisdictions (Cayman, BVI, Panama) | Yellow |
| Regulatory Body | FinCEN, SEC, FBI, FATF | Green |
| SAR/CTR | Suspicious Activity Reports, CTRs | Dark Red |

## Categories

- **Money Laundering** — Placement, layering, integration indicators
- **Insurance Fraud** — Staged claims, inflated damages, phantom policies
- **Identity Fraud** — Synthetic identities, account takeover, impersonation
- **Financial Crime** — Embezzlement, bribery, insider trading, Ponzi schemes
- **Tax Fraud** — Evasion, unreported income, offshore shelters

## Focus Modes

| Mode | Best For |
|---|---|
| `aml_investigation` | Anti-money laundering case files |
| `insurance_fraud` | Insurance claim analysis |
| `forensic_accounting` | Embezzlement and misappropriation |

## Quick Start

```bash
cortex.exe analyze --pack fraud_starter.json --focus aml_investigation ./case_files/
cortex.exe brain --pack fraud_starter.json ./transaction_records/
cortex.exe hunt --pack fraud_starter.json --focus forensic_accounting C:\
```

## Get More

This is a free starter with 8 entity types. The full CORTEX platform includes 55 domain packs covering OSINT, cybersecurity, healthcare compliance, and more.

- **[CORTEX Pro ($29)](https://andrewpioneer6.gumroad.com/l/cjamvzo)** — Desktop app + 3 premium packs
- **[Complete Bundle ($79)](https://andrewpioneer6.gumroad.com/l/cjamvzo)** — All 55 domain packs

## License

MIT — free for personal and commercial use.
