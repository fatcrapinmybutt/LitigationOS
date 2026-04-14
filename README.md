# CORTEX Cybersecurity Starter Pack

> Free cybersecurity domain pack for the [CORTEX Intelligence Platform](https://fatcrapinmybutt.github.io/cortex-site/)

## What is this?

A JSON configuration file that transforms CORTEX into a **cybersecurity intelligence tool**. Point it at your local files — threat reports, logs, incident notes, CTI feeds — and it automatically:

- **Extracts entities**: IPs, CVEs, hashes (MD5/SHA256), domains, URLs, ports, MITRE ATT&CK techniques, registry keys, emails
- **Categorizes threats**: Malware, vulnerabilities, network attacks, phishing, data breaches, threat actors
- **Detects authorities**: CVE database references, MITRE ATT&CK IDs, NIST standards, CWE identifiers
- **Visualizes connections**: Interactive D3.js force-directed graph showing relationships between IOCs

## Quick Start

1. Download [CORTEX](https://fatcrapinmybutt.github.io/cortex-site/)
2. Drop `cyber_starter.json` into the `domains/` folder
3. Run: `cortex.exe hunt --domain cyber_starter --path C:\your\threat_intel\`
4. Open the interactive graph visualization

## What's in the pack

| Component | Count | Examples |
|-----------|-------|---------|
| Entity types | 10 | IP addresses, CVEs, file hashes, MITRE techniques |
| Threat categories | 6 | Malware, phishing, data breach, APT groups |
| Authority patterns | 4 | CVE, MITRE ATT&CK, NIST SP, CWE |
| Focus modes | 4 | Malware, network, vulnerability, threat actor |

## Use Cases

- **SOC Analysts**: Triage threat intel reports, extract IOCs automatically
- **Incident Response**: Scan case notes and logs for indicators
- **CTI Teams**: Build relationship graphs from threat reports
- **Bug Bounty**: Catalog vulnerabilities and track CVEs across targets
- **Students**: Learn threat intelligence concepts with real pattern matching

## Want More?

This starter pack covers the essentials. The **full Cybersecurity Pro pack** ($14) includes:

- 25+ entity types (ASN, certificate hashes, YARA rules, Sigma rules, etc.)
- 12 threat categories with granular sub-classification
- 10 authority databases
- 8 focus modes including APT tracking and ransomware hunting
- Advanced scoring with TTP chain analysis

**[Get CORTEX Pro](https://andrewpioneer6.gumroad.com/l/cjamvzo)** — includes the full cyber pack plus 2 more domains.

**[Get the Complete Bundle](https://andrewpioneer6.gumroad.com/l/cjamvzo)** — all 55 domain packs for $79.

## Also Available

- [Free OSINT Starter Pack](https://github.com/fatcrapinmybutt/cortex-osint) — usernames, emails, social media, geolocation
- 55 domain packs covering: fraud, journalism, HR, supply chain, real estate, healthcare, and 49 more

## License

MIT — use it however you want.

## Links

- [CORTEX Product Page](https://fatcrapinmybutt.github.io/cortex-site/)
- [Buy on Gumroad](https://andrewpioneer6.gumroad.com/l/cjamvzo)
- [OSINT Starter (free)](https://github.com/fatcrapinmybutt/cortex-osint)
