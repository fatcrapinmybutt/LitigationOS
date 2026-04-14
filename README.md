# CORTEX Healthcare Compliance Starter Pack

> Free intelligence pack for healthcare compliance, HIPAA investigation, and medical fraud detection.

**[CORTEX](https://fatcrapinmybutt.github.io/cortex-site/)** is an offline desktop intelligence platform that scans your local files and builds interactive knowledge graphs. This starter pack adds healthcare intelligence capabilities.

## What This Pack Detects

| Entity Type | Examples | Color |
|---|---|---|
| PHI Indicator | Patient names, DOB, SSN, MRN references | Red |
| Medical Code | ICD-10, CPT, HCPCS, DRG codes | Blue |
| Provider | NPI numbers, DEA numbers, facility names | Purple |
| Drug/Device | FDA references, controlled substances, opioids | Orange |
| Regulation | HIPAA, Stark Law, Anti-Kickback, EMTALA | Green |
| Financial Amount | Dollar amounts in billing/claims | Yellow |

## Categories

- **HIPAA Violation** — Privacy breaches, unauthorized PHI access, security rule failures
- **Medical Fraud** — Upcoding, unbundling, phantom billing, kickbacks
- **Prescriber Abuse** — Pill mills, doctor shopping, opioid diversion
- **Clinical Safety** — Adverse events, sentinel events, medication errors

## Focus Modes

| Mode | Best For |
|---|---|
| `hipaa_investigation` | HIPAA breach and privacy investigations |
| `billing_fraud` | Healthcare billing fraud detection |
| `opioid_diversion` | Controlled substance diversion cases |

## Quick Start

```bash
cortex.exe analyze --pack healthcare_starter.json --focus hipaa_investigation ./breach_files/
cortex.exe brain --pack healthcare_starter.json ./compliance_docs/
cortex.exe hunt --pack healthcare_starter.json --focus billing_fraud C:\
```

## Get More

This is a free starter with 6 entity types. The full CORTEX platform includes 55 domain packs covering OSINT, cybersecurity, legal compliance, fraud detection, and more.

- **[CORTEX Pro ($29)](https://andrewpioneer6.gumroad.com/l/cjamvzo)** — Desktop app + 3 premium packs
- **[Complete Bundle ($79)](https://andrewpioneer6.gumroad.com/l/cjamvzo)** — All 55 domain packs

## License

MIT — free for personal and commercial use.
