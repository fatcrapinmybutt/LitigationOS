---
name: OMEGA-SECURITY
description: >-
  Comprehensive security skill for LitigationOS covering PII protection and
  redaction (MCR 8.119(H)), data encryption at rest, audit logging with SHA-256
  integrity, access control for local-first architecture, OWASP Top 10 code
  security, incident response with evidence preservation, backup encryption,
  legal compliance (attorney-client privilege, work product doctrine), and
  shadow module defense. Invoke for ANY security audit, vulnerability scan,
  PII redaction, encryption task, compliance check, or incident response
  within the litigation system.
category: security
version: "2.0.0"
triggers:
  - security
  - audit
  - vulnerability
  - PII
  - encryption
  - redaction
  - OWASP
  - incident
  - penetration
  - privacy
  - compliance
  - chain of custody
  - MCR 8.119
  - shadow module
  - backup security
lanes:
  - "A: Watson/Custody (2024-001507-DC)"
  - "B: Shady Oaks/Housing (2025-002760-CZ)"
  - "C: Federal §1983 (USDC WDMI)"
  - "D: PPO (2023-5907-PP)"
  - "E: Judicial Misconduct/JTC"
  - "F: Appellate (COA 366810)"
court: "14th Judicial Circuit, Muskegon County"
case: Pigors v Watson
dependencies:
  - litigation_context.db
  - db_lock_manager.py
  - safe_shell.py
metadata:
  tier: 4
  fused_skills: 29
  author: andrew-pigors + copilot-omega
  forge_date: 2026-03-21
---

# 🛡️ OMEGA-SECURITY — Fortress-Grade Litigation Security

> **The last line of defense between Andrew's case and catastrophic data exposure.**
> Fuses 29 security disciplines into a unified shield that protects evidence integrity,
> ensures court compliance, and locks down a 10 GB+ local-first litigation system
> running across 6 physical drives with zero network dependency.

---

## Forged from 29 Individual Skills

| # | Source Skill | Absorbed Capability |
|---|-------------|-------------------|
| 1 | security-auditor | Full-stack security audit methodology |
| 2 | security-review | Code-level vulnerability scanning |
| 3 | security-compliance-compliance-check | Regulatory compliance verification |
| 4 | security-red-team-arsenal | Offensive security testing patterns |
| 5 | security-scanning-security-dependencies | Dependency vulnerability scanning |
| 6 | security-scanning-security-hardening | System hardening checklists |
| 7 | security-scanning-security-sast | Static application security testing |
| 8 | security-scanning-tools | Security toolchain integration |
| 9 | security-requirement-extraction | Security requirement derivation |
| 10 | security-bluebook-builder | Security documentation standards |
| 11 | pentest-checklist | Penetration testing methodology |
| 12 | pentest-commands | Offensive security command reference |
| 13 | incident-responder | Incident detection and response |
| 14 | incident-response-incident-response | Incident response playbooks |
| 15 | incident-response-smart-fix | Automated incident remediation |
| 16 | api-security-best-practices | API endpoint hardening |
| 17 | audit-openclaw-security | Legal system security auditing |
| 18 | broken-authentication-testing | Authentication bypass detection |
| 19 | ethical-hacking-methodology | Structured ethical hacking |
| 20 | network-engineer | Network security architecture |
| 21 | linux-privilege-escalation | Privilege escalation awareness |
| 22 | secrets-management | Credential and secret handling |
| 23 | vulnerability-scanner | Automated vulnerability detection |
| 24 | sql-injection-testing | SQL injection prevention and testing |
| 25 | pci-compliance | Payment/data handling standards |
| 26 | gdpr-data-handling | Privacy regulation compliance |
| 27 | threat-modeling-expert | STRIDE/DREAD threat modeling |
| 28 | threat-mitigation-mapping | Threat-to-control mapping |
| 29 | redaction-agent | Automated PII redaction for e-filing |

---

## When to Apply

- **PII detected in a filing draft** — SSN, DOB, full child name, financial account numbers
- **Pre-e-filing review** — mandatory redaction sweep before any court submission
- **New code touches database** — SQL injection check, parameterized query enforcement
- **Evidence ingested from external drive** — chain of custody verification, SHA-256 manifest
- **Backup operation initiated** — encryption verification, I:\ drive integrity check
- **Shadow module warning** — repo root CWD detection, safe execution path enforcement
- **Incident detected** — unauthorized access, file corruption, missing evidence, integrity failure
- **Audit requested** — compliance check against MCR 8.119, attorney-client privilege markers
- **New GUI feature** — XSS prevention, input validation, output encoding
- **Agent spawned with DB access** — connection pooling verification, WAL mode enforcement

---

## Decision Tree

```
Security task received
│
├─ Is it PII/Redaction? ──────────────────────────────── → S1: PII Protection
│   ├─ Child name detected? → Replace with "L.D.W." (MCR 8.119(H))
│   ├─ SSN/DOB/financial? → Full redaction with [REDACTED] marker
│   └─ Pre-e-filing? → Run full redaction sweep → S8: Legal Compliance
│
├─ Is it data at rest? ──────────────────────────────── → S2: Data Encryption
│   ├─ DB encryption? → SQLite encryption extension + DPAPI
│   ├─ Credential storage? → Windows Credential Manager / DPAPI
│   └─ Key rotation? → Verify key management lifecycle
│
├─ Is it access/change tracking? ────────────────────── → S3: Audit Logging
│   ├─ File access? → Log timestamp + user + action + SHA-256
│   ├─ DB modification? → Write-ahead log + before/after hash
│   └─ Evidence handling? → Full chain of custody record
│
├─ Is it permissions/access? ────────────────────────── → S4: Access Control
│   ├─ File permissions? → Windows ACL verification
│   ├─ DB access? → managed_db() enforcement + connection pool
│   └─ Network check? → Verify zero network dependency
│
├─ Is it code security? ─────────────────────────────── → S5: Code Security
│   ├─ SQL query? → Parameterized ONLY — never string concat
│   ├─ User input? → Validate + sanitize + encode
│   └─ GUI output? → XSS prevention + output encoding
│
├─ Is it an incident? ──────────────────────────────── → S6: Incident Response
│   ├─ Data breach? → Preserve → Contain → Assess → Recover
│   ├─ File corruption? → SHA-256 verify → restore from backup
│   └─ Missing evidence? → Audit log search → drive scan → alert
│
├─ Is it backup related? ───────────────────────────── → S7: Backup Security
│   ├─ Backup creation? → Encrypt → verify → rotate
│   ├─ Backup restore? → Integrity check → decrypt → validate
│   └─ Disaster recovery? → Full recovery protocol
│
├─ Is it legal compliance? ──────────────────────────── → S8: Legal Compliance
│   ├─ Attorney-client privilege? → Mark + protect + verify
│   ├─ Work product doctrine? → Classification + access control
│   └─ MCR 8.119? → Public access rules + redaction
│
└─ Is it shadow module defense? ─────────────────────── → S9: Shadow Module Defense
    ├─ CWD at repo root? → BLOCK — redirect to script directory
    ├─ Import conflict? → Detect json.py, typing.py, etc.
    └─ Safe execution? → Use safe_shell.py or set CWD explicitly
```

---

## S1: PII Protection — The Redaction Fortress

### Purpose
Detect and remove Personally Identifiable Information from all filings, documents, and
generated content before any court submission. Michigan Court Rule 8.119(H) requires
specific redactions in publicly accessible court filings.

### MCR 8.119(H) Mandatory Redactions

| PII Type | Action | Example |
|----------|--------|---------|
| **Minor's full name** | Replace with initials | "L.D.W." — NEVER the full name |
| **Social Security Number** | Full redaction | `[REDACTED — SSN]` |
| **Date of birth** | Redact day/month, keep year | `[REDACTED — DOB] (year: 20XX)` |
| **Financial account numbers** | Last 4 digits only | `****1234` |
| **Home address of minor** | Full redaction | `[REDACTED — MINOR ADDRESS]` |
| **Victim address (PPO)** | Full redaction | `[REDACTED — PROTECTED ADDRESS]` |

### PII Detection Patterns

```python
PII_PATTERNS = {
    'ssn': r'\b\d{3}-?\d{2}-?\d{4}\b',
    'dob': r'\b(?:DOB|born|birth\s*date)[:\s]*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
    'phone': r'\b\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}\b',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'financial': r'\b(?:account|acct|routing)[:\s#]*\d{4,}\b',
    'child_full_name': r'\b(?:CHILD_FULL_NAME_PATTERN)\b',  # configured per case
    'address': r'\b\d+\s+[A-Za-z]+\s+(?:St|Ave|Rd|Dr|Blvd|Ln|Way|Ct)\b',
}
```

### Pre-Filing Redaction Protocol
1. Parse document (PDF/DOCX/TXT) into text segments
2. Run ALL PII patterns against every segment
3. Flag matches with confidence scores (high/medium/low)
4. Auto-redact HIGH confidence matches
5. Queue MEDIUM/LOW matches for human review
6. Generate redaction manifest with before/after SHA-256
7. Verify child is referred to as "L.D.W." — never full name
8. Verify no party addresses appear unredacted in PPO filings

### CRITICAL Rules
- **L.D.W.** — the ONLY acceptable reference to the child in any filing
- Andrew's address (1977 Whitehall Road, Lot 17) — redact in PPO filings only
- Emily's address (2160 Garland Drive) — redact in PPO filings only
- Phone numbers — redact from public filings, retain in service documents
- NEVER redact case numbers, court names, or judge names — those are public record

---

## S2: Data Encryption — Local-First Lockdown

### Purpose
Protect the 10 GB+ litigation database and all evidence files at rest using
encryption that requires zero network connectivity.

### Encryption Architecture

```
Layer 1: SQLite Database
  └─ litigation_context.db → WAL mode + DPAPI-encrypted backups
  └─ lane_*.db files → Same encryption standard
  └─ master_index.db → Agent fleet data store

Layer 2: File System
  └─ Evidence files → SHA-256 integrity hashes (manifest)
  └─ Backup archives → Encrypted with Windows DPAPI
  └─ Temp files → Auto-purge on session end

Layer 3: Credentials
  └─ No API keys (local-only architecture)
  └─ No remote credentials stored
  └─ Windows Credential Manager for any local secrets
```

### Key Management Rules
- **No hardcoded secrets** — ever, in any file, in any commit
- **DPAPI binding** — encryption keys tied to Windows user profile
- **No key files on shared drives** — keys stay on C:\ only
- **Backup keys separately** — never in same archive as encrypted data

---

## S3: Audit Logging — Total Accountability

### Purpose
Maintain an immutable record of every action taken on evidence, filings, and
case data to support chain of custody requirements and detect tampering.

### Audit Record Schema

```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    user_agent TEXT NOT NULL,        -- 'copilot', 'pipeline', 'user', agent_id
    action TEXT NOT NULL,            -- 'read', 'write', 'delete', 'move', 'modify'
    target_type TEXT NOT NULL,       -- 'file', 'db_row', 'filing', 'evidence'
    target_path TEXT,                -- file path or table.row_id
    sha256_before TEXT,              -- hash before action (NULL for reads)
    sha256_after TEXT,               -- hash after action (NULL for reads/deletes)
    details TEXT,                    -- JSON with additional context
    lane TEXT                        -- case lane (A-F)
);
```

### Logging Rules
- **Every file access** → logged with timestamp and user agent
- **Every DB write** → logged with before/after SHA-256
- **Every evidence move** → logged with source and destination paths
- **Every deletion** → logged as MOVE to I:\ (hard deletes prohibited)
- **Every filing generation** → logged with all source evidence references
- Log entries are **append-only** — never modify or delete audit records

### Chain of Custody Protocol
1. Evidence received → SHA-256 computed → audit_log entry created
2. Every access → read event logged with requesting agent
3. Every transformation → new version created (append-only) → hash chain updated
4. Filing inclusion → evidence linked to filing via audit trail
5. Court submission → final integrity verification → submission log entry

---

## S4: Access Control — Zero-Network Security Model

### Purpose
Enforce access control in a local-first architecture where all processing
happens on Andrew's Windows machine with no network dependency.

### Access Boundaries

```
TRUSTED ZONE (full access):
  C:\Users\andre\LitigationOS\        — primary workspace
  C:\Users\andre\LitigationOS\litigation_context.db  — central DB

EVIDENCE ZONE (read + index, write via pipeline only):
  D:\, F:\, G:\, H:\                   — evidence source drives
  
BACKUP ZONE (write for backup, read for restore):
  I:\                                  — backup and dedup destination
  
RESTRICTED (never access):
  Network endpoints                    — zero remote calls
  Cloud storage                        — local only
  External APIs                        — all providers disabled
```

### Database Access Control
- **All DB access through `managed_db()`** from `db_lock_manager.py`
- **Max 3 concurrent connections** — enforced by semaphore
- **WAL mode mandatory** — enables concurrent reads during writes
- **busy_timeout=60000** — prevents SQLITE_BUSY errors under contention
- **No raw `sqlite3.connect()`** — always use the managed wrapper

---

## S5: Code Security — Hardened Development Practices

### Purpose
Prevent injection, XSS, and other OWASP Top 10 vulnerabilities in LitigationOS
application code, pipeline scripts, and MCP server tools.

### SQL Injection Prevention (ABSOLUTE RULE)

```python
# ✅ CORRECT — parameterized query
cursor.execute(
    "SELECT * FROM evidence_quotes WHERE vehicle_name = ? AND claim_id = ?",
    (vehicle_name, claim_id)
)

# ❌ NEVER — string concatenation (SQL injection vector)
cursor.execute(f"SELECT * FROM evidence_quotes WHERE vehicle_name = '{vehicle_name}'")

# ❌ NEVER — format string (SQL injection vector)
cursor.execute("SELECT * FROM evidence_quotes WHERE vehicle_name = '%s'" % vehicle_name)
```

### Input Validation Checklist
- [ ] All user inputs validated before use
- [ ] File paths canonicalized and checked against allowed directories
- [ ] SQL parameters always bound (never interpolated)
- [ ] CustomTkinter GUI inputs sanitized before DB insertion
- [ ] MCP tool inputs validated via Pydantic models
- [ ] No `eval()`, `exec()`, or `__import__()` on user-supplied data

### XSS Prevention in GUI
- Escape all dynamic content before rendering in CustomTkinter widgets
- Never use `tkinter.Label(text=user_input)` without sanitization
- HTML content in report generation must be escaped

### Dependency Security
- Run `pip audit` periodically to check for known vulnerabilities
- Pin dependency versions in `pyproject.toml`
- No wildcard version specifiers (`>=` without upper bound)

---

## S6: Incident Response — Evidence Preservation Protocol

### Purpose
Detect, contain, and recover from security incidents while maintaining
evidence integrity and chain of custody.

### Incident Classification

| Severity | Examples | Response Time |
|----------|---------|---------------|
| **CRITICAL** | Evidence tampering, DB corruption, filing integrity failure | Immediate — stop all operations |
| **HIGH** | Missing evidence files, audit log gaps, hash mismatches | Within 1 hour |
| **MEDIUM** | Permission changes, unexpected file access, shadow module activation | Within 4 hours |
| **LOW** | Configuration drift, deprecated dependency, minor log anomaly | Next session |

### Response Protocol (CRITICAL/HIGH)
1. **PRESERVE** — Do not modify anything. Take filesystem snapshot.
2. **CONTAIN** — Stop pipeline, stop agents, prevent further changes.
3. **ASSESS** — Compare SHA-256 manifests. Identify scope of impact.
4. **RECOVER** — Restore from I:\ backup if integrity compromised.
5. **DOCUMENT** — Full audit trail of incident and response actions.
6. **PREVENT** — Root cause analysis. Implement countermeasure.

### Evidence Preservation During Incidents
- **Never overwrite** potentially compromised files — copy to quarantine
- **Hash everything** before and after any recovery action
- **Audit log is sacrosanct** — if log integrity is questioned, restore from backup first
- **Court deadlines take priority** — if filing deadline is imminent, use last known good backup

---

## S7: Backup Security — Encrypted Defense in Depth

### Purpose
Ensure all backups are encrypted, verified, and recoverable with proper
rotation to prevent data loss.

### Backup Architecture

```
PRIMARY:   C:\Users\andre\LitigationOS\           ← active workspace
BACKUP:    I:\LitigationOS_Backup\                 ← encrypted backup destination
DEDUP:     I:\LitigationOS_Dedup\                  ← deduplicated file archive

Backup Schedule:
  - Before any pipeline run → incremental backup
  - Before any destructive operation → full snapshot
  - Daily automated → if pipeline cron is active
  - Before filing submission → court-ready snapshot
```

### Backup Verification Protocol
1. Create backup archive with SHA-256 manifest
2. Verify manifest matches source files (byte-for-byte)
3. Test restore of 3 random files from backup
4. Verify DB backup opens and passes `PRAGMA integrity_check`
5. Log backup event in audit_log with manifest hash

### Rotation Policy
- Keep last 7 daily backups
- Keep last 4 weekly backups
- Keep indefinitely: pre-filing snapshots, incident snapshots
- **NEVER delete backups of filed court documents** — these are permanent record

---

## S8: Legal Compliance — Court Rule Adherence

### Purpose
Ensure all generated documents, filings, and data handling comply with
Michigan Court Rules and legal privilege protections.

### MCR 8.119 Compliance Matrix

| Requirement | Implementation | Verification |
|-------------|---------------|-------------|
| Minor name redaction | L.D.W. initials only | Regex scan for full name |
| SSN redaction | Full removal | Pattern match + manual review |
| Financial account redaction | Last 4 digits only | Pattern match |
| Public access compliance | Separate public/sealed versions | Filing type check |

### Attorney-Client Privilege Protection
- Documents marked `[PRIVILEGED]` are excluded from discovery responses
- Work product marked `[WORK PRODUCT]` receives qualified protection
- Privilege log maintained for all withheld documents
- Inadvertent disclosure protocol: immediate claw-back notice

### Work Product Doctrine
- All analysis documents generated by LitigationOS are work product
- Strategic planning documents receive opinion work product protection
- Factual compilation receives fact work product protection
- Never share work product analysis in public filings without review

---

## S9: Shadow Module Defense — Python Import Safety

### Purpose
The LitigationOS repo root contains 22+ Python files that shadow standard library
and third-party modules. Running Python with CWD at repo root causes silent import
corruption that can crash the pipeline or produce wrong results.

### Known Shadow Modules (repo root)

```
json.py       — shadows stdlib json
typing.py     — shadows stdlib typing
tokenize.py   — shadows stdlib tokenize
numpy.py      — shadows third-party numpy
pandas.py     — shadows third-party pandas
+ 17 others   — run `sshadow` for full audit
```

### Defense Protocol

```python
# ✅ CORRECT — use safe_shell.py wrapper
# PowerShell:
#   srun script.py --arg          # sets CWD to script's directory
#   spy "print(1+1)"              # temp file execution, not python -c
#   sshadow                       # audit for shadow conflicts

# ✅ CORRECT — explicit CWD in subprocess
import subprocess, os
subprocess.run(
    ["python", "script.py"],
    cwd=os.path.dirname(os.path.abspath("script.py"))
)

# ❌ NEVER — run Python at repo root
# cd C:\Users\andre\LitigationOS && python script.py
# This imports json.py from repo root instead of stdlib!
```

### Pre-Execution Checklist
1. Verify CWD is NOT `C:\Users\andre\LitigationOS\` (repo root)
2. Set CWD to the script's own directory or a safe subdirectory
3. Use `safe_shell.py check` to validate before execution
4. Use `safe_shell.py run` for production script execution
5. If CWD must be repo root (rare), set `PYTHONPATH` to exclude it

### Detection Script
```powershell
# Run shadow audit to detect conflicts
python C:\Users\andre\LitigationOS\00_SYSTEM\tools\safe_shell.py shadow-audit
```

---

## Cross-Module Integration Patterns

### S1 + S8: Pre-Filing Security Sweep
```
Filing draft ready
  → S1: PII scan (SSN, DOB, child name, addresses)
  → S8: MCR 8.119 compliance check
  → S1: Auto-redact HIGH confidence matches
  → S8: Privilege marker verification
  → Generate redaction manifest
  → GO/NO-GO decision
```

### S3 + S6: Incident Detection via Audit Trails
```
Anomaly detected (hash mismatch, unexpected access)
  → S3: Query audit_log for recent actions on target
  → S6: Classify incident severity
  → S3: Preserve full audit trail snapshot
  → S6: Execute response protocol
  → S3: Log all response actions
```

### S5 + S9: Secure Code Execution
```
New Python script to execute
  → S9: Check CWD for shadow module conflicts
  → S5: Validate no SQL injection in DB queries
  → S5: Check input validation on all parameters
  → S9: Execute via safe_shell.py wrapper
  → S3: Log execution in audit trail
```

### S2 + S7: Encrypted Backup Lifecycle
```
Backup triggered
  → S7: Create file manifest with SHA-256 hashes
  → S2: Encrypt archive using DPAPI
  → S7: Write to I:\ backup destination
  → S7: Verify backup integrity
  → S3: Log backup event in audit_log
  → S7: Rotate old backups per retention policy
```

---

## LitigationOS-Specific Security Invariants

These rules are ABSOLUTE — no exception, no override, no "just this once":

1. **NEVER hard delete** — all removals are moves to `I:\` or Recycle Bin
2. **Child = L.D.W.** — initials only, every time, in every document (MCR 8.119(H))
3. **Chain of custody = SHA-256** — every evidence file has a hash, every transfer is logged
4. **Zero network** — no remote API calls, no cloud sync, no external services
5. **Parameterized queries ONLY** — no string interpolation in SQL, ever
6. **No fabricated data** — if it's not in the DB, use `[UNKNOWN — VERIFY]`
7. **managed_db() for ALL DB access** — max 3 connections, WAL mode, busy_timeout=60000
8. **No CWD at repo root for Python** — shadow modules will corrupt imports
9. **Append-only evidence** — new versions only, originals are immutable
10. **Backup before destruction** — snapshot I:\ before any bulk operation

---

## Quick Reference Card

```
╔════════════════════════════════════════════════════════════════╗
║           OMEGA-SECURITY v2.0 — QUICK REFERENCE               ║
╠════════════════════════════════════════════════════════════════╣
║                                                                ║
║  PII REDACTION (S1):                                           ║
║    Child: L.D.W. only (MCR 8.119(H))                          ║
║    SSN/DOB/Financial: Full redaction                           ║
║    Pre-filing: Mandatory sweep before e-filing                 ║
║                                                                ║
║  DATA PROTECTION (S2+S4):                                      ║
║    Encryption: DPAPI at rest, WAL mode for DB                  ║
║    Access: managed_db() only, max 3 connections                ║
║    Network: ZERO — all processing local                        ║
║                                                                ║
║  AUDIT (S3):                                                   ║
║    Every action logged: timestamp + user + SHA-256             ║
║    Chain of custody: hash before → action → hash after         ║
║    Append-only: never modify audit records                     ║
║                                                                ║
║  CODE (S5+S9):                                                 ║
║    SQL: Parameterized ONLY — never string concat               ║
║    Python: Never CWD at repo root (shadow modules)             ║
║    Input: Validate everything, trust nothing                   ║
║                                                                ║
║  INCIDENT (S6):                                                ║
║    Preserve → Contain → Assess → Recover → Document            ║
║                                                                ║
║  BACKUP (S7):                                                  ║
║    Destination: I:\ drive (encrypted)                          ║
║    Manifest: SHA-256 for every file                            ║
║    Rule: NEVER delete filed court document backups             ║
║                                                                ║
║  COMPLIANCE (S8):                                              ║
║    MCR 8.119: Public access redaction rules                    ║
║    Privilege: Attorney-client + work product markers           ║
║    Party names: VERIFIED TABLE ONLY — never fabricate          ║
║                                                                ║
║  GOLDEN RULE: If in doubt, BLOCK and ASK.                      ║
║  A false positive redaction is recoverable.                    ║
║  A missed PII exposure in a filed document is NOT.             ║
╚════════════════════════════════════════════════════════════════╝
```

---

## ═══════════════════════════════════════════════════════════════
## UPGRADE v2.1: MICHIGAN FILING SECURITY
## ═══════════════════════════════════════════════════════════════

### MCR 8.119(H) — Protected Personal Information
Michigan court rules REQUIRE redaction of:
```
MUST REDACT in all filings:
  □ Minor child's full name → use initials (L.D.W.)
  □ Social Security numbers → last 4 digits only (XXX-XX-1234)
  □ Date of birth (minors) → year only (born 20XX)
  □ Financial account numbers → last 4 digits only
  □ Driver's license numbers → redact entirely
  □ Home addresses (in DV/PPO cases) → use "address on file with court"
```

### PII Detection Patterns (Auto-Scan Before Filing)
```python
PII_PATTERNS = {
    'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
    'dob_full': r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # context-dependent
    'account_number': r'\b\d{10,17}\b',
    'drivers_license': r'\b[A-Z]\d{12}\b',  # MI format
    'child_full_name': r'Lincoln|L\.D\.W\.',  # Case-specific
    'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    'email': r'\b[\w.+-]+@[\w.-]+\.\w+\b',
}

# ALWAYS scan BEFORE any filing export:
# grep -n for each pattern in output document
# Flag findings for review, auto-redact where safe
```

### Metadata Scrubbing (Pre-Filing)
```
DOCX files contain:
  □ Author name → strip or set to "Andrew James Pigors"
  □ Company → strip
  □ Last modified by → strip
  □ Track changes → accept all, remove history
  □ Comments → remove all
  □ Embedded file paths → strip (reveals local directory structure)

PDF files contain:
  □ Producer/Creator metadata → strip
  □ Modification timestamps → normalize
  □ XMP metadata → remove
  □ Embedded fonts (subset only — don't leak full system fonts)
```

### Evidence Chain-of-Custody Protection
```
For every exhibit:
  □ Original file: SHA-256 hash recorded at intake
  □ Any modification: new hash + audit trail
  □ Export: verify hash matches original
  □ Filing: certify authenticity per MRE 901(b)(9)
  □ NEVER modify originals — create annotated copies
```

### Filing Sanitization Pipeline
```
Pre-Filing Checklist:
  1. PII scan → auto-redact SSN/accounts/DL
  2. Child name check → L.D.W. only (never full name)
  3. Metadata scrub → strip DOCX/PDF metadata
  4. Privilege check → no attorney-client communications
  5. Work product check → no internal strategy notes
  6. Hallucination check → no fabricated names/stats
  7. Hash verification → original evidence hashes intact
  8. Final review → human eyes before e-filing
```
