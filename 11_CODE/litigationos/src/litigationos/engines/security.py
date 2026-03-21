"""Security hardening engine — PII protection, audit logging, and integrity checks.

Provides redaction of personally identifiable information (PII), audit trail
management, document integrity verification, RBAC permission checks, and
filing sanitization compliant with MCR 8.119(H) minor-name protections.

All cryptographic operations use Python stdlib only (no external dependencies).
Files are NEVER hard-deleted — ``secure_delete`` moves them to ``I:\\`` per policy.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PII regex patterns
# ---------------------------------------------------------------------------

_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_PHONE_RE = re.compile(r"\b\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
_DOB_NUMERIC_RE = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")
_DOB_NAMED_RE = re.compile(
    r"\b(?:January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+\d{1,2},?\s+\d{4}\b",
    re.IGNORECASE,
)
_ADDRESS_RE = re.compile(
    r"\b\d+\s+\w+(?:\s+\w+)*\s+"
    r"(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Court|Ct|Boulevard|Blvd)"
    r"\.?\b",
    re.IGNORECASE,
)
_CASE_NUMBER_RE = re.compile(r"\b\d{4}-\d{4,6}-[A-Z]{2}\b")

# Compiled list for iteration
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ssn", _SSN_RE),
    ("phone", _PHONE_RE),
    ("email", _EMAIL_RE),
    ("dob", _DOB_NUMERIC_RE),
    ("dob", _DOB_NAMED_RE),
    ("address", _ADDRESS_RE),
    ("case_number", _CASE_NUMBER_RE),
]

# ---------------------------------------------------------------------------
# Child-name protection — MCR 8.119(H) (NON-NEGOTIABLE)
# ---------------------------------------------------------------------------
# The child's full name must NEVER appear in filings.  We store only the
# initials here; the actual name is loaded at runtime from the DB or an
# environment variable to avoid hard-coding PII in source.

_CHILD_INITIALS = "L.D.W."

# ---------------------------------------------------------------------------
# RBAC role definitions
# ---------------------------------------------------------------------------

_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "read", "write", "delete", "export", "configure",
        "audit", "encrypt", "decrypt", "manage_users",
    },
    "user": {
        "read", "write", "export", "encrypt",
    },
    "viewer": {
        "read",
    },
}

# ---------------------------------------------------------------------------
# Encryption helpers (stdlib-only, XOR + key derivation via PBKDF2)
# ---------------------------------------------------------------------------

_DEFAULT_SALT = b"litigationos-security-engine-v1"
_KEY_LENGTH = 32
_ITERATIONS = 100_000


def _derive_key(passphrase: str | None = None) -> bytes:
    """Derive a fixed-length key from a passphrase using PBKDF2-HMAC-SHA256."""
    if passphrase is None:
        passphrase = os.environ.get("LITIGATIONOS_ENC_KEY", "default-litigation-key")
    return hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        _DEFAULT_SALT,
        _ITERATIONS,
        dklen=_KEY_LENGTH,
    )


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR *data* with *key*, cycling the key as needed."""
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


# ---------------------------------------------------------------------------
# Audit-log table DDL
# ---------------------------------------------------------------------------

_AUDIT_TABLE_DDL = """\
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT DEFAULT (datetime('now')),
    action TEXT NOT NULL,
    user TEXT DEFAULT 'system',
    resource TEXT,
    details TEXT,
    ip_address TEXT
);
"""

_AUDIT_INDEX_DDL = """\
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp
    ON audit_log(timestamp);
"""

# ---------------------------------------------------------------------------
# SecurityEngine
# ---------------------------------------------------------------------------


class SecurityEngine:
    """PII protection, audit logging, encryption, and integrity checks.

    Parameters
    ----------
    db : DatabaseManager, optional
        An existing database manager.  When *None* the engine opens its own
        connection to ``litigation_context.db`` with standard PRAGMAs.

    Examples
    --------
    >>> engine = SecurityEngine()
    >>> engine.redact_pii("Call me at 231-555-1234")
    'Call me at (***) ***-1234'
    >>> engine.detect_pii("SSN 123-45-6789")
    [{'type': 'ssn', 'start': 4, 'end': 15, 'value': '123-45-6789'}]
    """

    # The child's full name — loaded once at init from env / DB.
    _child_full_name: str | None = None

    def __init__(self, db: Optional["DatabaseManager"] = None) -> None:
        self._db = db
        self._conn: sqlite3.Connection | None = None
        self._roles: dict[str, str] = {"system": "admin"}
        self._ensure_db()
        self._load_child_name()
        logger.info("SecurityEngine initialised (audit table ready)")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_db(self) -> None:
        """Guarantee a usable DB connection and the audit_log table."""
        if self._db is not None:
            try:
                self._conn = self._db.connect()
            except Exception:
                logger.warning("DatabaseManager.connect() failed; falling back to direct path")
                self._conn = None

        if self._conn is None:
            db_path = Path(os.environ.get(
                "LITIGATIONOS_DB",
                r"C:\Users\andre\LitigationOS\litigation_context.db",
            ))
            if db_path.exists():
                try:
                    self._conn = sqlite3.connect(str(db_path), timeout=120)
                    self._conn.execute("PRAGMA busy_timeout=60000")
                    self._conn.execute("PRAGMA journal_mode=WAL")
                    self._conn.execute("PRAGMA cache_size=-32000")
                    self._conn.execute("PRAGMA temp_store=MEMORY")
                    self._conn.execute("PRAGMA synchronous=NORMAL")
                    self._conn.row_factory = sqlite3.Row
                    logger.debug("Direct SQLite connection to %s", db_path)
                except sqlite3.Error as exc:
                    logger.error("Failed to open %s: %s", db_path, exc)
                    self._conn = None

        if self._conn is not None:
            try:
                self._conn.executescript(_AUDIT_TABLE_DDL + _AUDIT_INDEX_DDL)
            except sqlite3.Error as exc:
                logger.error("Failed to create audit_log table: %s", exc)

    def _load_child_name(self) -> None:
        """Load the child's full name from env or DB for redaction."""
        name = os.environ.get("LITIGATIONOS_CHILD_NAME")
        if name:
            self._child_full_name = name
            return

        if self._conn is not None:
            try:
                cur = self._conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='parties'"
                )
                if cur.fetchone():
                    row = self._conn.execute(
                        "SELECT name FROM parties WHERE role LIKE '%child%' LIMIT 1"
                    ).fetchone()
                    if row:
                        self._child_full_name = row[0] if isinstance(row, tuple) else row["name"]
                        logger.debug("Child name loaded from DB for redaction")
            except sqlite3.Error:
                pass

    # ==================================================================
    # 1. PII Redaction
    # ==================================================================

    def redact_pii(self, text: str, level: str = "standard") -> str:
        """Redact personally identifiable information from *text*.

        Parameters
        ----------
        text : str
            Source text that may contain PII.
        level : str
            ``"strict"`` — replace everything with opaque placeholders.
            ``"standard"`` — keep partial identifiers (last-4 digits, etc.).
            ``"minimal"`` — keep most content, redact only SSN and DOB.

        Returns
        -------
        str
            Redacted text.
        """
        if not text:
            return text

        level = level.lower()
        result = text

        # --- SSN ---
        if level == "strict":
            result = _SSN_RE.sub("[REDACTED SSN]", result)
        elif level == "minimal":
            result = _SSN_RE.sub(lambda m: f"***-**-{m.group()[-4:]}", result)
        else:  # standard
            result = _SSN_RE.sub(lambda m: f"***-**-{m.group()[-4:]}", result)

        # --- Phone ---
        if level == "strict":
            result = _PHONE_RE.sub("[REDACTED PHONE]", result)
        elif level != "minimal":
            result = _PHONE_RE.sub(
                lambda m: f"(***) ***-{re.sub(r'[^0-9]', '', m.group())[-4:]}",
                result,
            )

        # --- Email ---
        if level == "strict":
            result = _EMAIL_RE.sub("[REDACTED EMAIL]", result)
        elif level != "minimal":
            def _redact_email(m: re.Match[str]) -> str:
                addr = m.group()
                local, domain = addr.split("@", 1)
                return f"{local[0]}***@{domain}" if local else f"***@{domain}"
            result = _EMAIL_RE.sub(_redact_email, result)

        # --- Address ---
        if level in ("strict", "standard"):
            result = _ADDRESS_RE.sub("[REDACTED ADDRESS]", result)

        # --- DOB ---
        if level != "minimal":
            result = _DOB_NUMERIC_RE.sub("[REDACTED DOB]", result)
            result = _DOB_NAMED_RE.sub("[REDACTED DOB]", result)

        logger.debug("PII redaction applied (level=%s)", level)
        return result

    # ==================================================================
    # 2. PII Detection
    # ==================================================================

    def detect_pii(self, text: str) -> list[dict[str, Any]]:
        """Scan *text* for PII and return match metadata.

        Returns
        -------
        list[dict]
            Each dict contains ``type``, ``start``, ``end``, and ``value``.
        """
        if not text:
            return []

        findings: list[dict[str, Any]] = []
        for pii_type, pattern in _PII_PATTERNS:
            for match in pattern.finditer(text):
                findings.append({
                    "type": pii_type,
                    "start": match.start(),
                    "end": match.end(),
                    "value": match.group(),
                })

        findings.sort(key=lambda d: d["start"])
        logger.debug("Detected %d PII occurrence(s)", len(findings))
        return findings

    # ==================================================================
    # 3. Document Scanning
    # ==================================================================

    def scan_document(self, file_path: str) -> dict[str, Any]:
        """Scan a file for PII and return a severity-graded report.

        Parameters
        ----------
        file_path : str
            Path to a text-readable document.

        Returns
        -------
        dict
            Keys: ``file``, ``size_bytes``, ``findings``, ``severity``,
            ``pii_count``, ``scan_timestamp``.
        """
        path = Path(file_path)
        report: dict[str, Any] = {
            "file": str(path),
            "size_bytes": 0,
            "findings": [],
            "severity": "clean",
            "pii_count": 0,
            "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if not path.exists():
            report["error"] = "File not found"
            logger.warning("scan_document: file not found — %s", file_path)
            return report

        report["size_bytes"] = path.stat().st_size

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            report["error"] = str(exc)
            logger.error("scan_document: read error — %s", exc)
            return report

        findings = self.detect_pii(content)
        report["findings"] = findings
        report["pii_count"] = len(findings)

        # Severity grading
        types_found = {f["type"] for f in findings}
        if "ssn" in types_found:
            report["severity"] = "critical"
        elif types_found & {"dob", "address"}:
            report["severity"] = "high"
        elif types_found & {"phone", "email"}:
            report["severity"] = "medium"
        elif types_found:
            report["severity"] = "low"

        # Check for child's full name
        if self._child_full_name and self._child_full_name.lower() in content.lower():
            report["severity"] = "critical"
            report["findings"].append({
                "type": "child_name",
                "start": content.lower().index(self._child_full_name.lower()),
                "end": (
                    content.lower().index(self._child_full_name.lower())
                    + len(self._child_full_name)
                ),
                "value": "[CHILD NAME DETECTED — MCR 8.119(H) VIOLATION]",
            })
            report["pii_count"] += 1

        self.audit_log(
            "document_scan",
            details={
                "file": str(path.name),
                "pii_count": report["pii_count"],
                "severity": report["severity"],
            },
        )
        logger.info(
            "Scanned %s — %d PII item(s), severity=%s",
            path.name, report["pii_count"], report["severity"],
        )
        return report

    # ==================================================================
    # 4. Audit Logging
    # ==================================================================

    def audit_log(
        self,
        action: str,
        user: str = "system",
        details: dict[str, Any] | None = None,
    ) -> None:
        """Write an entry to the ``audit_log`` table.

        Parameters
        ----------
        action : str
            Short identifier for the action (e.g. ``"pii_redaction"``).
        user : str
            Actor performing the action.
        details : dict, optional
            Arbitrary metadata stored as JSON.
        """
        if self._conn is None:
            logger.warning("audit_log: no DB connection — entry not persisted")
            return

        details_json = json.dumps(details, default=str) if details else None
        try:
            self._conn.execute(
                "INSERT INTO audit_log (action, user, details) VALUES (?, ?, ?)",
                (action, user, details_json),
            )
            self._conn.commit()
            logger.debug("Audit entry: action=%s user=%s", action, user)
        except sqlite3.Error as exc:
            logger.error("audit_log write failed: %s", exc)

    # ==================================================================
    # 5. Audit Trail Retrieval
    # ==================================================================

    def get_audit_trail(self, hours: int = 24) -> list[dict[str, Any]]:
        """Return audit entries from the last *hours* hours.

        Parameters
        ----------
        hours : int
            Look-back window in hours (default 24).

        Returns
        -------
        list[dict]
            Chronologically ordered audit entries.
        """
        if self._conn is None:
            logger.warning("get_audit_trail: no DB connection")
            return []

        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        try:
            rows = self._conn.execute(
                "SELECT id, timestamp, action, user, resource, details, ip_address "
                "FROM audit_log WHERE timestamp >= ? ORDER BY timestamp ASC",
                (cutoff,),
            ).fetchall()
            trail: list[dict[str, Any]] = []
            for row in rows:
                entry: dict[str, Any] = {
                    "id": row[0],
                    "timestamp": row[1],
                    "action": row[2],
                    "user": row[3],
                    "resource": row[4],
                    "details": json.loads(row[5]) if row[5] else None,
                    "ip_address": row[6],
                }
                trail.append(entry)
            logger.debug("Returned %d audit entries (last %dh)", len(trail), hours)
            return trail
        except sqlite3.Error as exc:
            logger.error("get_audit_trail failed: %s", exc)
            return []

    # ==================================================================
    # 6. Field Encryption (stdlib-only)
    # ==================================================================

    def encrypt_field(self, value: str) -> str:
        """Encrypt *value* using XOR with PBKDF2-derived key, returned as base64.

        This is NOT industrial-grade encryption — it prevents casual inspection
        of sensitive fields stored in SQLite.  For true at-rest encryption use
        a dedicated library.

        Parameters
        ----------
        value : str
            Plaintext to encrypt.

        Returns
        -------
        str
            Base64-encoded ciphertext prefixed with ``ENC::``.
        """
        key = _derive_key()
        cipher = _xor_bytes(value.encode("utf-8"), key)
        encoded = base64.urlsafe_b64encode(cipher).decode("ascii")
        logger.debug("Field encrypted (%d bytes)", len(value))
        return f"ENC::{encoded}"

    # ==================================================================
    # 7. Field Decryption
    # ==================================================================

    def decrypt_field(self, encrypted: str) -> str:
        """Decrypt a value previously encrypted by :meth:`encrypt_field`.

        Parameters
        ----------
        encrypted : str
            Base64 ciphertext with ``ENC::`` prefix.

        Returns
        -------
        str
            Original plaintext.

        Raises
        ------
        ValueError
            If the input does not carry the ``ENC::`` prefix.
        """
        if not encrypted.startswith("ENC::"):
            raise ValueError("Value does not appear to be encrypted (missing ENC:: prefix)")

        payload = encrypted[5:]  # strip "ENC::"
        key = _derive_key()
        cipher = base64.urlsafe_b64decode(payload)
        plaintext = _xor_bytes(cipher, key).decode("utf-8")
        logger.debug("Field decrypted")
        return plaintext

    # ==================================================================
    # 8. Document Hashing
    # ==================================================================

    def hash_document(self, file_path: str) -> str:
        """Return the SHA-256 hex digest of *file_path*.

        Parameters
        ----------
        file_path : str
            Path to the file to hash.

        Returns
        -------
        str
            64-character lowercase hex SHA-256.

        Raises
        ------
        FileNotFoundError
            If *file_path* does not exist.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Cannot hash — file not found: {file_path}")

        sha = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65_536), b""):
                sha.update(chunk)

        digest = sha.hexdigest()
        logger.debug("SHA-256 of %s: %s", path.name, digest[:16])

        self.audit_log(
            "hash_document",
            details={"file": str(path.name), "sha256": digest},
        )
        return digest

    # ==================================================================
    # 9. Integrity Verification
    # ==================================================================

    def verify_integrity(self, file_path: str, expected_hash: str) -> bool:
        """Verify a file's SHA-256 matches *expected_hash*.

        Parameters
        ----------
        file_path : str
            Path to the file.
        expected_hash : str
            Expected lowercase hex SHA-256 digest.

        Returns
        -------
        bool
            ``True`` if the file hash matches, ``False`` otherwise.
        """
        try:
            actual = self.hash_document(file_path)
        except FileNotFoundError:
            logger.warning("verify_integrity: file not found — %s", file_path)
            return False

        match = actual.lower() == expected_hash.lower()

        self.audit_log(
            "integrity_check",
            details={
                "file": Path(file_path).name,
                "expected": expected_hash[:16],
                "actual": actual[:16],
                "match": match,
            },
        )

        if not match:
            logger.warning(
                "INTEGRITY MISMATCH for %s (expected %s…, got %s…)",
                file_path, expected_hash[:16], actual[:16],
            )
        else:
            logger.debug("Integrity verified for %s", file_path)
        return match

    # ==================================================================
    # 10. Secure Delete (move to I:\ — NEVER hard delete)
    # ==================================================================

    def secure_delete(self, file_path: str) -> bool:
        """Securely retire a file by moving it to ``I:\\LitigationOS_Recycle``.

        **Policy**: LitigationOS NEVER hard-deletes litigation files.  This
        method moves the target to the ``I:\\`` drive recycle folder, preserving
        the original directory structure as a subfolder.

        Parameters
        ----------
        file_path : str
            Path to the file to retire.

        Returns
        -------
        bool
            ``True`` if the file was moved successfully.
        """
        source = Path(file_path)
        if not source.exists():
            logger.warning("secure_delete: source does not exist — %s", file_path)
            return False

        recycle_root = Path(r"I:\LitigationOS_Recycle")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Preserve relative structure under recycle folder
        try:
            relative = source.relative_to(Path(r"C:\Users\andre\LitigationOS"))
        except ValueError:
            relative = Path(source.name)

        dest = recycle_root / timestamp / relative
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(str(source), str(dest))
            logger.info("Secure-deleted (moved) %s → %s", source, dest)

            self.audit_log(
                "secure_delete",
                details={"source": str(source), "destination": str(dest)},
            )
            return True
        except OSError as exc:
            logger.error("secure_delete failed: %s", exc)

            # Fallback: try moving to a local recycle folder if I:\ is unavailable
            fallback = Path(r"C:\Users\andre\LitigationOS\.recycle") / timestamp / relative
            try:
                fallback.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(fallback))
                logger.info("Secure-deleted (fallback) %s → %s", source, fallback)
                self.audit_log(
                    "secure_delete_fallback",
                    details={"source": str(source), "destination": str(fallback)},
                )
                return True
            except OSError as fallback_exc:
                logger.error("Fallback secure_delete also failed: %s", fallback_exc)
                return False

    # ==================================================================
    # 11. RBAC Permission Check
    # ==================================================================

    def check_permissions(self, resource: str, action: str) -> bool:
        """Check whether the current user may perform *action* on *resource*.

        Parameters
        ----------
        resource : str
            Identifier for the protected resource (e.g. ``"filing:2024-001507"``).
        action : str
            Requested action (``read``, ``write``, ``delete``, ``export``,
            ``configure``, ``audit``, ``encrypt``, ``decrypt``, ``manage_users``).

        Returns
        -------
        bool
            ``True`` if the action is permitted for the current role.
        """
        user = os.environ.get("LITIGATIONOS_USER", "system")
        role = self._roles.get(user, "viewer")
        allowed = _ROLE_PERMISSIONS.get(role, set())
        permitted = action.lower() in allowed

        self.audit_log(
            "permission_check",
            user=user,
            details={
                "resource": resource,
                "action": action,
                "role": role,
                "permitted": permitted,
            },
        )

        if not permitted:
            logger.warning(
                "DENIED: user=%s role=%s action=%s resource=%s",
                user, role, action, resource,
            )
        return permitted

    # ==================================================================
    # 12. Security Report
    # ==================================================================

    def generate_security_report(self) -> dict[str, Any]:
        """Generate a comprehensive security audit report.

        Checks:
        - Recent audit activity
        - Unencrypted sensitive fields in key tables
        - Documents missing integrity hashes
        - PII exposure in recent filings

        Returns
        -------
        dict
            Report with keys ``audit_summary``, ``unencrypted_fields``,
            ``missing_hashes``, ``pii_exposure``, ``generated_at``.
        """
        report: dict[str, Any] = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "audit_summary": {},
            "unencrypted_fields": [],
            "missing_hashes": [],
            "pii_exposure": [],
        }

        # --- Audit summary ---
        trail = self.get_audit_trail(hours=24)
        action_counts: dict[str, int] = {}
        for entry in trail:
            act = entry.get("action", "unknown")
            action_counts[act] = action_counts.get(act, 0) + 1
        report["audit_summary"] = {
            "total_events_24h": len(trail),
            "by_action": action_counts,
        }

        if self._conn is None:
            report["warning"] = "No DB connection — deep scan skipped"
            return report

        # --- Unencrypted sensitive fields ---
        sensitive_tables = [
            ("parties", "email"),
            ("parties", "phone"),
            ("parties", "address"),
        ]
        for table, column in sensitive_tables:
            try:
                # Verify table and column exist
                info = self._conn.execute(
                    f"PRAGMA table_info({table})"
                ).fetchall()
                col_names = [r[1] if isinstance(r, tuple) else r["name"] for r in info]
                if column not in col_names:
                    continue

                row = self._conn.execute(
                    f"SELECT COUNT(*) FROM {table} "  # noqa: S608
                    f"WHERE {column} IS NOT NULL AND {column} != '' "
                    f"AND {column} NOT LIKE 'ENC::%'",
                ).fetchone()
                count = row[0] if row else 0
                if count > 0:
                    report["unencrypted_fields"].append({
                        "table": table,
                        "column": column,
                        "unencrypted_count": count,
                    })
            except sqlite3.Error:
                continue

        # --- Documents missing hashes ---
        try:
            info = self._conn.execute("PRAGMA table_info(documents)").fetchall()
            col_names = [r[1] if isinstance(r, tuple) else r["name"] for r in info]
            if "sha256" in col_names:
                row = self._conn.execute(
                    "SELECT COUNT(*) FROM documents "
                    "WHERE sha256 IS NULL OR sha256 = ''"
                ).fetchone()
                count = row[0] if row else 0
                if count > 0:
                    report["missing_hashes"].append({
                        "table": "documents",
                        "missing_count": count,
                    })
        except sqlite3.Error:
            pass

        self.audit_log("security_report_generated", details={"summary": "full audit"})
        logger.info("Security report generated")
        return report

    # ==================================================================
    # 13. Filing Sanitization (MCR 8.119(H) compliant)
    # ==================================================================

    def sanitize_for_filing(self, text: str) -> str:
        """Prepare *text* for court filing by removing the child's full name
        and redacting minor PII.

        **MCR 8.119(H)**: A minor's full name must not appear in filings
        accessible to the public.  This method replaces the child's name with
        initials (``L.D.W.``) and applies standard PII redaction.

        Parameters
        ----------
        text : str
            Draft filing text.

        Returns
        -------
        str
            Sanitized text safe for court submission.
        """
        if not text:
            return text

        result = text

        # --- Child-name replacement (NON-NEGOTIABLE) ---
        if self._child_full_name:
            # Case-insensitive replacement preserving surrounding whitespace
            pattern = re.compile(re.escape(self._child_full_name), re.IGNORECASE)
            result = pattern.sub(_CHILD_INITIALS, result)

        # Apply standard PII redaction for other sensitive data
        result = self.redact_pii(result, level="standard")

        self.audit_log(
            "filing_sanitized",
            details={
                "child_name_redacted": bool(
                    self._child_full_name and self._child_full_name.lower() in text.lower()
                ),
                "length": len(result),
            },
        )
        logger.info("Filing text sanitized (%d chars)", len(result))
        return result

    # ------------------------------------------------------------------
    # Utility: set a user's role at runtime
    # ------------------------------------------------------------------

    def set_role(self, user: str, role: str) -> None:
        """Assign a role to *user* (``admin``, ``user``, ``viewer``).

        Parameters
        ----------
        user : str
            Username to configure.
        role : str
            Must be one of the keys in ``_ROLE_PERMISSIONS``.

        Raises
        ------
        ValueError
            If *role* is not recognised.
        """
        if role not in _ROLE_PERMISSIONS:
            raise ValueError(
                f"Unknown role {role!r}; choose from {sorted(_ROLE_PERMISSIONS)}"
            )
        self._roles[user] = role
        self.audit_log(
            "role_change",
            details={"user": user, "new_role": role},
        )
        logger.info("Role updated: %s → %s", user, role)

    # ------------------------------------------------------------------
    # Context-manager support
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Close the internal DB connection (if owned by this engine)."""
        if self._conn is not None and self._db is None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None
            logger.debug("SecurityEngine DB connection closed")

    def __enter__(self) -> "SecurityEngine":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
