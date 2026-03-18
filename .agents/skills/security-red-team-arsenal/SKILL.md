---
name: security-red-team-arsenal
description: "ELITE security & red team — fusion of 15 security/pentest/threat skills. Covers ethical hacking, vulnerability scanning, red team methodology, threat modeling, security auditing, attack trees, SAST, hardening, penetration testing, and security bluebook building."
metadata:
  model: opus
  forged_from: 15
  forge_date: 2026-03-12
---

# SECURITY-RED-TEAM-ARSENAL — Elite Composite Skill

> Forged from 15 individual skills into one supreme composite.
> Sources: ethical-hacking-methodology, vulnerability-scanner, red-team-tools-and-methodology, red-team-tactics, threat-modeling-expert, threat-mitigation-mapping, security-auditor, security-review, attack-tree-construction, security-scanning-tools, security-scanning-security-sast, security-scanning-security-hardening, pentest-commands, pentest-checklist, security-bluebook-builder

## When to Apply

Activate this skill for ANY work related to:
- **Ethical Hacking Methodology**: recon, scanning, enumeration, exploitation, reporting
- **Vulnerability Scanning**: automated scanning, CVE databases, severity scoring
- **Red Team Operations**: adversary simulation, TTPs, MITRE ATT&CK, purple team
- **Threat Modeling**: STRIDE, DREAD, attack trees, threat landscapes, risk assessment
- **Security Auditing**: code review, configuration audit, compliance checking
- **SAST & Static Analysis**: source code scanning, taint analysis, dependency audit
- **Security Hardening**: OS hardening, network security, encryption, access control
- **Penetration Testing**: web app, API, network, social engineering, physical
- **Attack Tree Construction**: threat decomposition, probability, impact, countermeasures
- **Security Bluebook**: security standards, compliance frameworks, policy templates

---

## §1. Ethical Hacking Methodology

> recon, scanning, enumeration, exploitation, reporting

### 2. Reconnaissance Principles
*Source: red-team-tactics*

### Passive vs Active

| Type | Trade-off |
|------|-----------|
| **Passive** | No target contact, limited info |
| **Active** | Direct contact, more detection risk |

### Information Targets

| Category | Value |
|----------|-------|
| Technology stack | Attack vector selection |
| Employee info | Social engineering |
| Network ranges | Scanning scope |
| Third parties | Supply chain attack |

---

### 8. Reporting Principles
*Source: red-team-tactics*

### Attack Narrative

Document the full attack chain:
1. How initial access was gained
2. What techniques were used
3. What objectives were achieved
4. Where detection failed

### Detection Gaps

For each successful technique:
- What should have detected it?
- Why didn't detection work?
- How to improve detection

---

## §2. Vulnerability Scanning

> automated scanning, CVE databases, severity scoring

### 7. Scanning Methodology
*Source: vulnerability-scanner*

### Phase-Based Approach

```
1. RECONNAISSANCE
   └── Understand the target
       ├── Technology stack
       ├── Entry points
       └── Data flows

2. DISCOVERY
   └── Identify potential issues
       ├── Configuration review
       ├── Dependency analysis
       └── Code pattern search

3. ANALYSIS
   └── Validate and prioritize
       ├── False positive elimination
       ├── Risk scoring
       └── Attack chain mapping

4. REPORTING
   └── Actionable findings
       ├── Clear reproduction steps
       ├── Business impact
       └── Remediation guidance
```

---

## §3. Red Team Operations

> adversary simulation, TTPs, MITRE ATT&CK, purple team

### 1. MITRE ATT&CK Phases
*Source: red-team-tactics*

### Attack Lifecycle

```
RECONNAISSANCE → INITIAL ACCESS → EXECUTION → PERSISTENCE
       ↓              ↓              ↓            ↓
   PRIVILEGE ESC → DEFENSE EVASION → CRED ACCESS → DISCOVERY
       ↓              ↓              ↓            ↓
LATERAL MOVEMENT → COLLECTION → C2 → EXFILTRATION → IMPACT
```

### Phase Objectives

| Phase | Objective |
|-------|-----------|
| **Recon** | Map attack surface |
| **Initial Access** | Get first foothold |
| **Execution** | Run code on target |
| **Persistence** | Survive reboots |
| **Privilege Escalation** | Get admin/root |
| **Defense Evasion** | Avoid detection |
| **Credential Access** | Harvest credentials |
| **Discovery** | Map internal network |
| **Lateral Movement** | Spread to other systems |
| **Collection** | Gather target data |
| **C2** | Maintain command channel |
| **Exfiltration** | Extract data |

---

## §4. Threat Modeling

> STRIDE, DREAD, attack trees, threat landscapes, risk assessment

### Phase 1: Comprehensive Security Assessment
*Source: security-scanning-security-hardening*

### 1. Initial Vulnerability Scanning
- Use Task tool with subagent_type="security-auditor"
- Prompt: "Perform comprehensive security assessment on: $ARGUMENTS. Execute SAST analysis with Semgrep/SonarQube, DAST scanning with OWASP ZAP, dependency audit with Snyk/Trivy, secrets detection with GitLeaks/TruffleHog. Generate SBOM for supply chain analysis. Identify OWASP Top 10 vulnerabilities, CWE weaknesses, and CVE exposures."
- Output: Detailed vulnerability report with CVSS scores, exploitability analysis, attack surface mapping, secrets exposure report, SBOM inventory
- Context: Initial baseline for all remediation efforts

### 2. Threat Modeling and Risk Analysis
- Use Task tool with subagent_type="security-auditor"
- Prompt: "Conduct threat modeling using STRIDE methodology for: $ARGUMENTS. Analyze attack vectors, create attack trees, assess business impact of identified vulnerabilities. Map threats to MITRE ATT&CK framework. Prioritize risks based on likelihood and impact."
- Output: Threat model diagrams, risk matrix with prioritized vulnerabilities, attack scenario documentation, business impact analysis
- Context: Uses vulnerability scan results to inform threat priorities

### 3. Architecture Security Review
- Use Task tool with subagent_type="backend-api-security::backend-architect"
- Prompt: "Review architecture for security weaknesses in: $ARGUMENTS. Evaluate service boundaries, data flow security, authentication/authorization architecture, encryption implementation, network segmentation. Design zero-trust architecture patterns. Reference threat model and vulnerability findings."
- Output: Security architecture assessment, zero-trust design recommendations, service mesh security requirements, data classification matrix
- Context: Incorporates threat model to address architectural vulnerabilities

## §5. Security Auditing

> code review, configuration audit, compliance checking

## §6. SAST & Static Analysis

> source code scanning, taint analysis, dependency audit

### 7. Scanning Methodology
*Source: vulnerability-scanner*

### Phase-Based Approach

```
1. RECONNAISSANCE
   └── Understand the target
       ├── Technology stack
       ├── Entry points
       └── Data flows

2. DISCOVERY
   └── Identify potential issues
       ├── Configuration review
       ├── Dependency analysis
       └── Code pattern search

3. ANALYSIS
   └── Validate and prioritize
       ├── False positive elimination
       ├── Risk scoring
       └── Attack chain mapping

4. REPORTING
   └── Actionable findings
       ├── Clear reproduction steps
       ├── Business impact
       └── Remediation guidance
```

---

### 8. Code Pattern Analysis
*Source: vulnerability-scanner*

### High-Risk Patterns

| Pattern | Risk | Look For |
|---------|------|----------|
| **String concat in queries** | Injection | `"SELECT * FROM " + user_input` |
| **Dynamic code execution** | RCE | `eval()`, `exec()`, `Function()` |
| **Unsafe deserialization** | RCE | `pickle.loads()`, `unserialize()` |
| **Path manipulation** | Traversal | User input in file paths |
| **Disabled security** | Various | `verify=False`, `--insecure` |

### Secret Patterns

| Type | Indicators |
|------|-----------|
| API Keys | `api_key`, `apikey`, high entropy |
| Tokens | `token`, `bearer`, `jwt` |
| Credentials | `password`, `secret`, `key` |
| Cloud | `AWS_`, `AZURE_`, `GCP_` prefixes |

---

## §7. Security Hardening

> OS hardening, network security, encryption, access control

### Phase 1: Comprehensive Security Assessment
*Source: security-scanning-security-hardening*

### 1. Initial Vulnerability Scanning
- Use Task tool with subagent_type="security-auditor"
- Prompt: "Perform comprehensive security assessment on: $ARGUMENTS. Execute SAST analysis with Semgrep/SonarQube, DAST scanning with OWASP ZAP, dependency audit with Snyk/Trivy, secrets detection with GitLeaks/TruffleHog. Generate SBOM for supply chain analysis. Identify OWASP Top 10 vulnerabilities, CWE weaknesses, and CVE exposures."
- Output: Detailed vulnerability report with CVSS scores, exploitability analysis, attack surface mapping, secrets exposure report, SBOM inventory
- Context: Initial baseline for all remediation efforts

### 2. Threat Modeling and Risk Analysis
- Use Task tool with subagent_type="security-auditor"
- Prompt: "Conduct threat modeling using STRIDE methodology for: $ARGUMENTS. Analyze attack vectors, create attack trees, assess business impact of identified vulnerabilities. Map threats to MITRE ATT&CK framework. Prioritize risks based on likelihood and impact."
- Output: Threat model diagrams, risk matrix with prioritized vulnerabilities, attack scenario documentation, business impact analysis
- Context: Uses vulnerability scan results to inform threat priorities

### 3. Architecture Security Review
- Use Task tool with subagent_type="backend-api-security::backend-architect"
- Prompt: "Review architecture for security weaknesses in: $ARGUMENTS. Evaluate service boundaries, data flow security, authentication/authorization architecture, encryption implementation, network segmentation. Design zero-trust architecture patterns. Reference threat model and vulnerability findings."
- Output: Security architecture assessment, zero-trust design recommendations, service mesh security requirements, data classification matrix
- Context: Incorporates threat model to address architectural vulnerabilities

### Phase 3: Security Controls Implementation
*Source: security-scanning-security-hardening*

### 8. Authentication and Authorization Enhancement
- Use Task tool with subagent_type="security-auditor"
- Prompt: "Implement modern authentication system for: $ARGUMENTS. Deploy OAuth2/OIDC with PKCE, implement MFA with TOTP/WebAuthn/FIDO2, add risk-based authentication, implement RBAC/ABAC with principle of least privilege, add session management with secure token rotation."
- Output: Authentication service configuration, MFA implementation, authorization policies, session management system
- Context: Strengthens access controls based on architecture review

### 9. Infrastructure Security Controls
- Use Task tool with subagent_type="deployment-strategies::deployment-engineer"
- Prompt: "Deploy infrastructure security controls for: $ARGUMENTS. Configure WAF rules for OWASP protection, implement network segmentation with micro-segmentation, deploy IDS/IPS systems, configure cloud security groups and NACLs, implement DDoS protection with rate limiting and geo-blocking."
- Output: WAF configuration, network security policies, IDS/IPS rules, cloud security configurations
- Context: Implements network-level defenses

### 10. Secrets Management Implementation
- Use Task tool with subagent_type="deployment-strategies::deployment-engineer"
- Prompt: "Implement enterprise secrets management for: $ARGUMENTS. Deploy HashiCorp Vault or AWS Secrets Manager, implement secret rotation policies, remove hardcoded secrets, configure least-privilege IAM roles, implement encryption key management with HSM support."
- Output: Secrets management configuration, rotation policies, IAM role definitions, key management procedures
- Context: Eliminates secrets exposure vulnerabilities

## §8. Penetration Testing

> web app, API, network, social engineering, physical

## §9. Attack Tree Construction

> threat decomposition, probability, impact, countermeasures

## §10. Security Bluebook

> security standards, compliance frameworks, policy templates

### Phase 1: Comprehensive Security Assessment
*Source: security-scanning-security-hardening*

### 1. Initial Vulnerability Scanning
- Use Task tool with subagent_type="security-auditor"
- Prompt: "Perform comprehensive security assessment on: $ARGUMENTS. Execute SAST analysis with Semgrep/SonarQube, DAST scanning with OWASP ZAP, dependency audit with Snyk/Trivy, secrets detection with GitLeaks/TruffleHog. Generate SBOM for supply chain analysis. Identify OWASP Top 10 vulnerabilities, CWE weaknesses, and CVE exposures."
- Output: Detailed vulnerability report with CVSS scores, exploitability analysis, attack surface mapping, secrets exposure report, SBOM inventory
- Context: Initial baseline for all remediation efforts

### 2. Threat Modeling and Risk Analysis
- Use Task tool with subagent_type="security-auditor"
- Prompt: "Conduct threat modeling using STRIDE methodology for: $ARGUMENTS. Analyze attack vectors, create attack trees, assess business impact of identified vulnerabilities. Map threats to MITRE ATT&CK framework. Prioritize risks based on likelihood and impact."
- Output: Threat model diagrams, risk matrix with prioritized vulnerabilities, attack scenario documentation, business impact analysis
- Context: Uses vulnerability scan results to inform threat priorities

### 3. Architecture Security Review
- Use Task tool with subagent_type="backend-api-security::backend-architect"
- Prompt: "Review architecture for security weaknesses in: $ARGUMENTS. Evaluate service boundaries, data flow security, authentication/authorization architecture, encryption implementation, network segmentation. Design zero-trust architecture patterns. Reference threat model and vulnerability findings."
- Output: Security architecture assessment, zero-trust design recommendations, service mesh security requirements, data classification matrix
- Context: Incorporates threat model to address architectural vulnerabilities

### Phase 3: Security Controls Implementation
*Source: security-scanning-security-hardening*

### 8. Authentication and Authorization Enhancement
- Use Task tool with subagent_type="security-auditor"
- Prompt: "Implement modern authentication system for: $ARGUMENTS. Deploy OAuth2/OIDC with PKCE, implement MFA with TOTP/WebAuthn/FIDO2, add risk-based authentication, implement RBAC/ABAC with principle of least privilege, add session management with secure token rotation."
- Output: Authentication service configuration, MFA implementation, authorization policies, session management system
- Context: Strengthens access controls based on architecture review

### 9. Infrastructure Security Controls
- Use Task tool with subagent_type="deployment-strategies::deployment-engineer"
- Prompt: "Deploy infrastructure security controls for: $ARGUMENTS. Configure WAF rules for OWASP protection, implement network segmentation with micro-segmentation, deploy IDS/IPS systems, configure cloud security groups and NACLs, implement DDoS protection with rate limiting and geo-blocking."
- Output: WAF configuration, network security policies, IDS/IPS rules, cloud security configurations
- Context: Implements network-level defenses

### 10. Secrets Management Implementation
- Use Task tool with subagent_type="deployment-strategies::deployment-engineer"
- Prompt: "Implement enterprise secrets management for: $ARGUMENTS. Deploy HashiCorp Vault or AWS Secrets Manager, implement secret rotation policies, remove hardcoded secrets, configure least-privilege IAM roles, implement encryption key management with HSM support."
- Output: Secrets management configuration, rotation policies, IAM role definitions, key management procedures
- Context: Eliminates secrets exposure vulnerabilities

### Phase 4: Validation and Compliance
*Source: security-scanning-security-hardening*

### 11. Penetration Testing and Validation
- Use Task tool with subagent_type="security-auditor"
- Prompt: "Execute comprehensive penetration testing for: $ARGUMENTS. Perform authenticated and unauthenticated testing, API security testing, business logic testing, privilege escalation attempts. Use Burp Suite, Metasploit, and custom exploits. Validate all security controls effectiveness."
- Output: Penetration test report, proof-of-concept exploits, remediation validation, security control effectiveness metrics
- Context: Validates all implemented security measures

### 12. Compliance and Standards Verification
- Use Task tool with subagent_type="security-auditor"
- Prompt: "Verify compliance with security frameworks for: $ARGUMENTS. Validate against OWASP ASVS Level 2, CIS Benchmarks, SOC2 Type II requirements, GDPR/CCPA privacy controls, HIPAA/PCI-DSS if applicable. Generate compliance attestation reports."
- Output: Compliance assessment report, gap analysis, remediation requirements, audit evidence collection
- Context: Ensures regulatory and industry standard compliance

### 13. Security Monitoring and SIEM Integration
- Use Task tool with subagent_type="incident-response::devops-troubleshooter"
- Prompt: "Implement security monitoring and SIEM for: $ARGUMENTS. Deploy Splunk/ELK/Sentinel integration, configure security event correlation, implement behavioral analytics for anomaly detection, set up automated incident response playbooks, create security dashboards and alerting."
- Output: SIEM configuration, correlation rules, incident response playbooks, security dashboards, alert definitions
- Context: Establishes continuous security monitoring

### Framework Security
*Source: security-scanning-security-sast*

### Django

**VULNERABLE**: @csrf_exempt, DEBUG=True, weak SECRET_KEY, missing security middleware

**SECURE**:
```python
# settings.py
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
```

### Flask

**VULNERABLE**: debug=True, weak secret_key, CORS wildcard

**SECURE**:
```python
import os
from flask_talisman import Talisman

app.secret_key = os.environ.get('FLASK_SECRET_KEY')
Talisman(app, force_https=True)
CORS(app, origins=['https://example.com'])
```

### Express.js

**VULNERABLE**: Missing helmet, CORS wildcard, no rate limiting

**SECURE**:
```javascript
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

app.use(helmet());
app.use(cors({ origin: 'https://example.com' }));
app.use(rateLimit({ windowMs: 15 * 60 * 1000, max: 100 }));
```
