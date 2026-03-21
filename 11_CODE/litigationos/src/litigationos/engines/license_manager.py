"""License key management engine for LitigationOS.

Manages Free/Pro/Enterprise licensing tiers with offline-first HMAC-SHA256
key validation, activation/deactivation, feature gating, resource limit
checks, and a 14-day Pro trial. License state persists in
``~/.litigationos/license.json``; no network calls are ever required.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ── Signing secret ────────────────────────────────────────────────────────────
# In production this would live on a key-management server.  For offline
# validation the secret is embedded — the key format is tamper-evident, not
# tamper-proof, which is adequate for a desktop-local product.
_SIGNING_SECRET = "LitigationOS-HMAC-2025-xK9mPqR7vLw3"

# ── License-file location ────────────────────────────────────────────────────
_LICENSE_DIR = Path.home() / ".litigationos"
_LICENSE_FILE = _LICENSE_DIR / "license.json"

# ── Tier prefix map (key ↔ tier) ─────────────────────────────────────────────
_TIER_PREFIX = {"FREE": "free", "PRO": "pro", "ENT": "enterprise"}
_PREFIX_TIER = {v: k for k, v in _TIER_PREFIX.items()}

# ── Trial duration ────────────────────────────────────────────────────────────
_TRIAL_DAYS = 14


# ── Tier definitions ─────────────────────────────────────────────────────────

TIERS: dict[str, dict[str, Any]] = {
    "free": {
        "name": "Free",
        "price": 0,
        "max_cases": 1,
        "max_filings": 3,
        "max_evidence": 100,
        "features": ["basic_search", "deadline_tracking", "single_case"],
        "pipeline_phases": [1, 2, 3],
        "support": "community",
    },
    "pro": {
        "name": "Pro",
        "price": 49.99,
        "max_cases": 5,
        "max_filings": 50,
        "max_evidence": 10000,
        "features": [
            "basic_search",
            "deadline_tracking",
            "multi_case",
            "irac_analysis",
            "discovery_generator",
            "motion_templates",
            "pdf_production",
            "filing_wizard",
            "evidence_browser",
            "legal_brain",
            "authority_chains",
            "court_forms",
            "notifications",
        ],
        "pipeline_phases": list(range(1, 10)),
        "support": "email",
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 199.99,
        "max_cases": -1,
        "max_filings": -1,
        "max_evidence": -1,
        "features": ["all"],
        "pipeline_phases": list(range(0, 17)),
        "support": "priority",
        "extras": [
            "api_access",
            "custom_branding",
            "multi_user",
            "audit_log",
            "judge_profiling",
            "adversary_modeling",
            "pipeline_runner",
        ],
    },
}

# ── Resource-limit field mapping ──────────────────────────────────────────────
_RESOURCE_LIMIT_KEYS: dict[str, str] = {
    "cases": "max_cases",
    "filings": "max_filings",
    "evidence": "max_evidence",
}


# ── Helper utilities ──────────────────────────────────────────────────────────


def _compute_signature(tier: str, random_hex: str, email: str, expiry_ts: str) -> str:
    """Return the first 8 hex chars of an HMAC-SHA256 over the key payload."""
    message = f"{tier}:{random_hex}:{email}:{expiry_ts}"
    digest = hmac.new(
        _SIGNING_SECRET.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()
    return digest[:8].upper()


def _utcnow() -> datetime:
    """Timezone-aware UTC now (avoids deprecated ``datetime.utcnow``)."""
    return datetime.now(timezone.utc)


def _ts_to_iso(ts: float) -> str:
    """Unix timestamp → ISO-8601 string."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


# ── LicenseManager ────────────────────────────────────────────────────────────


class LicenseManager:
    """Offline-first license key management for LitigationOS.

    Handles key generation, HMAC-SHA256 validation, activation/deactivation,
    feature gating, resource-limit checks, and a 14-day Pro trial.
    """

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self._db = db
        self._cache: Optional[dict[str, Any]] = None
        logger.debug("LicenseManager initialised (db=%s)", "yes" if db else "no")

    # ── Key generation ────────────────────────────────────────────────────

    def generate_key(
        self,
        tier: str,
        email: str,
        expires_days: int = 365,
    ) -> str:
        """Generate a signed license key.

        Format: ``LOS-{TIER}-{RANDOM}-{SIGNATURE}``

        Parameters
        ----------
        tier:
            One of ``"free"``, ``"pro"``, ``"enterprise"``.
        email:
            Licensee email — baked into the HMAC so the key is bound to the
            purchaser.
        expires_days:
            Validity window in days from today.

        Returns
        -------
        str
            The license key string.

        Raises
        ------
        ValueError
            If *tier* is not a recognised tier name.
        """
        tier = tier.lower()
        if tier not in TIERS:
            raise ValueError(f"Unknown tier '{tier}'. Expected one of: {list(TIERS)}")

        prefix = _PREFIX_TIER[tier]
        random_hex = secrets.token_hex(6).upper()  # 12 hex chars
        expiry_ts = str(int((_utcnow() + timedelta(days=expires_days)).timestamp()))
        signature = _compute_signature(prefix, random_hex, email, expiry_ts)

        key = f"LOS-{prefix}-{random_hex}-{signature}"

        # Persist key metadata alongside the key so offline validation can
        # recover the email/expiry that were baked into the HMAC.
        self._save_key_metadata(key, tier, email, expiry_ts)

        logger.info("Generated %s key for %s (expires in %d days)", tier, email, expires_days)
        return key

    # ── Key validation ────────────────────────────────────────────────────

    def validate_key(self, key: str) -> dict[str, Any]:
        """Validate a license key offline.

        Checks format, HMAC signature, and expiry date.

        Returns
        -------
        dict
            ``{"valid": bool, "tier": str, "email": str, "expires": str,
            "days_remaining": int, "error": str|None}``
        """
        result: dict[str, Any] = {
            "valid": False,
            "tier": "free",
            "email": "",
            "expires": "",
            "days_remaining": 0,
            "error": None,
        }

        # ── Format check ─────────────────────────────────────────────────
        parts = key.split("-") if key else []
        if len(parts) != 4 or parts[0] != "LOS":
            result["error"] = "Invalid key format — expected LOS-TIER-RANDOM-SIG"
            logger.warning("Key validation failed: bad format")
            return result

        _, tier_prefix, random_hex, provided_sig = parts

        if tier_prefix not in _TIER_PREFIX:
            result["error"] = f"Unknown tier prefix '{tier_prefix}'"
            logger.warning("Key validation failed: unknown tier prefix %s", tier_prefix)
            return result

        if len(random_hex) != 12 or not all(c in "0123456789ABCDEF" for c in random_hex):
            result["error"] = "Invalid random segment — expected 12 uppercase hex chars"
            logger.warning("Key validation failed: bad random segment")
            return result

        tier_name = _TIER_PREFIX[tier_prefix]

        # ── Metadata lookup (needed for HMAC recomputation) ──────────────
        meta = self._load_key_metadata(key)
        if meta is None:
            result["error"] = (
                "Key metadata not found — the key may have been generated on "
                "another machine or the metadata file was deleted"
            )
            logger.warning("Key validation failed: no metadata for %s…", key[:16])
            return result

        email = meta.get("email", "")
        expiry_ts = meta.get("expiry_ts", "")

        # ── Signature check ──────────────────────────────────────────────
        expected_sig = _compute_signature(tier_prefix, random_hex, email, expiry_ts)
        if not hmac.compare_digest(provided_sig.upper(), expected_sig.upper()):
            result["error"] = "HMAC signature mismatch — key may be tampered"
            logger.warning("Key validation failed: HMAC mismatch")
            return result

        # ── Expiry check ─────────────────────────────────────────────────
        try:
            expiry_dt = datetime.fromtimestamp(int(expiry_ts), tz=timezone.utc)
        except (ValueError, OSError):
            result["error"] = f"Corrupt expiry timestamp: {expiry_ts}"
            return result

        now = _utcnow()
        remaining = (expiry_dt - now).days

        if remaining < 0:
            result["error"] = "License key has expired"
            result["tier"] = tier_name
            result["email"] = email
            result["expires"] = expiry_dt.isoformat()
            result["days_remaining"] = remaining
            logger.info("Key validation: expired %d days ago", abs(remaining))
            return result

        # ── Valid ─────────────────────────────────────────────────────────
        result.update(
            valid=True,
            tier=tier_name,
            email=email,
            expires=expiry_dt.isoformat(),
            days_remaining=remaining,
            error=None,
        )
        logger.info("Key validated: tier=%s, days_remaining=%d", tier_name, remaining)
        return result

    # ── Activation / deactivation ─────────────────────────────────────────

    def activate(self, key: str) -> dict[str, Any]:
        """Activate a license key and persist state.

        Returns
        -------
        dict
            ``{"success": bool, "tier": str, "message": str, ...}``
        """
        validation = self.validate_key(key)
        if not validation["valid"]:
            return {
                "success": False,
                "tier": "free",
                "message": f"Activation failed: {validation['error']}",
            }

        license_state: dict[str, Any] = {
            "key": key,
            "tier": validation["tier"],
            "email": validation["email"],
            "expires": validation["expires"],
            "activated_at": _utcnow().isoformat(),
            "trial": False,
        }

        self._write_license_file(license_state)
        self._cache = license_state
        logger.info("Activated %s license for %s", validation["tier"], validation["email"])

        return {
            "success": True,
            "tier": validation["tier"],
            "email": validation["email"],
            "expires": validation["expires"],
            "days_remaining": validation["days_remaining"],
            "message": f"Successfully activated {TIERS[validation['tier']]['name']} license.",
        }

    def deactivate(self) -> bool:
        """Deactivate the current license and revert to Free tier.

        Returns ``True`` on success, ``False`` if no license was active.
        """
        current = self._read_license_file()
        if not current:
            logger.info("Deactivate called but no active license found")
            return False

        _LICENSE_FILE.unlink(missing_ok=True)
        self._cache = None
        logger.info("License deactivated (was %s)", current.get("tier", "unknown"))
        return True

    # ── Current license queries ───────────────────────────────────────────

    def get_current_license(self) -> dict[str, Any]:
        """Return the active license state, or a synthetic Free-tier record."""
        state = self._effective_state()
        tier = state.get("tier", "free")
        tier_info = TIERS.get(tier, TIERS["free"])

        return {
            "tier": tier,
            "tier_name": tier_info["name"],
            "email": state.get("email", ""),
            "key": state.get("key", ""),
            "expires": state.get("expires", ""),
            "activated_at": state.get("activated_at", ""),
            "trial": state.get("trial", False),
            "features": tier_info["features"],
            "support": tier_info["support"],
        }

    def get_tier(self) -> str:
        """Return the current tier name (``'free'``, ``'pro'``, or ``'enterprise'``)."""
        return self._effective_state().get("tier", "free")

    # ── Feature gating ────────────────────────────────────────────────────

    def check_feature(self, feature: str) -> bool:
        """Return ``True`` if the current tier grants *feature*.

        Enterprise's ``"all"`` wildcard matches every feature.
        """
        tier = self.get_tier()
        tier_def = TIERS.get(tier, TIERS["free"])
        features: list[str] = tier_def["features"]

        if "all" in features:
            return True
        return feature in features

    def check_limit(self, resource: str, current_count: int) -> dict[str, Any]:
        """Check whether the current tier permits one more *resource*.

        Parameters
        ----------
        resource:
            ``"cases"``, ``"filings"``, or ``"evidence"``.
        current_count:
            How many of the resource already exist.

        Returns
        -------
        dict
            ``{"allowed": bool, "limit": int, "current": int, "remaining": int,
            "message": str}``
        """
        tier = self.get_tier()
        tier_def = TIERS.get(tier, TIERS["free"])
        limit_key = _RESOURCE_LIMIT_KEYS.get(resource)

        if limit_key is None:
            return {
                "allowed": True,
                "limit": -1,
                "current": current_count,
                "remaining": -1,
                "message": f"No limit defined for resource '{resource}'.",
            }

        limit: int = tier_def.get(limit_key, 0)

        # -1 means unlimited
        if limit == -1:
            return {
                "allowed": True,
                "limit": -1,
                "current": current_count,
                "remaining": -1,
                "message": f"Unlimited {resource} on {tier_def['name']} tier.",
            }

        remaining = max(limit - current_count, 0)
        allowed = current_count < limit

        if allowed:
            message = f"{resource.title()}: {current_count}/{limit} used ({remaining} remaining)."
        else:
            message = (
                f"{resource.title()} limit reached ({current_count}/{limit}). "
                f"Upgrade to unlock more."
            )

        return {
            "allowed": allowed,
            "limit": limit,
            "current": current_count,
            "remaining": remaining,
            "message": message,
        }

    # ── Tier info ─────────────────────────────────────────────────────────

    def get_tier_info(self, tier: str = "") -> dict[str, Any]:
        """Return details for *tier*, or the current tier when *tier* is empty.

        Returns an empty dict if *tier* is unrecognised.
        """
        if not tier:
            tier = self.get_tier()
        info = TIERS.get(tier)
        if info is None:
            logger.warning("get_tier_info: unknown tier '%s'", tier)
            return {}
        return {"tier_id": tier, **info}

    # ── Upgrade prompts ───────────────────────────────────────────────────

    def get_upgrade_prompt(self, feature: str) -> str:
        """Return a user-friendly upgrade message when *feature* is gated."""
        tier = self.get_tier()
        tier_name = TIERS.get(tier, TIERS["free"])["name"]

        # Determine which tier unlocks the feature
        target_tier: Optional[str] = None
        for tid in ("pro", "enterprise"):
            tier_features = TIERS[tid]["features"]
            if "all" in tier_features or feature in tier_features:
                target_tier = tid
                break

        if target_tier is None:
            return f"The feature '{feature}' is not available in any tier."

        target_name = TIERS[target_tier]["name"]
        target_price = TIERS[target_tier]["price"]

        return (
            f"🔒  '{feature}' requires a {target_name} license "
            f"(${target_price:.2f}/mo).\n"
            f"    You are currently on the {tier_name} tier.\n"
            f"    Upgrade at https://litigationos.com/pricing to unlock this feature."
        )

    # ── Expiry helpers ────────────────────────────────────────────────────

    def days_remaining(self) -> int:
        """Return the number of days until the active license expires.

        Returns ``0`` for the free tier (never expires) and negative values
        for already-expired keys.
        """
        state = self._effective_state()
        expires_raw = state.get("expires", "")
        if not expires_raw:
            return 0

        try:
            expiry_dt = datetime.fromisoformat(expires_raw)
            if expiry_dt.tzinfo is None:
                expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
            return (expiry_dt - _utcnow()).days
        except (ValueError, TypeError):
            logger.warning("Could not parse expiry date: %s", expires_raw)
            return 0

    # ── Trial management ──────────────────────────────────────────────────

    def is_trial(self) -> bool:
        """Return ``True`` if a Pro trial is currently active (not expired)."""
        state = self._effective_state()
        if not state.get("trial", False):
            return False
        # Make sure the trial hasn't expired
        remaining = self.days_remaining()
        return remaining > 0

    def start_trial(self) -> dict[str, Any]:
        """Start a 14-day Pro trial.

        Returns
        -------
        dict
            ``{"success": bool, "expires": str, "days": int, "message": str}``
        """
        current = self._read_license_file()

        # Prevent multiple trials
        if current and current.get("trial"):
            return {
                "success": False,
                "expires": current.get("expires", ""),
                "days": self.days_remaining(),
                "message": "A trial has already been used on this machine.",
            }

        # Prevent trial if a paid license is active
        if current and current.get("tier") in ("pro", "enterprise") and not current.get("trial"):
            return {
                "success": False,
                "expires": current.get("expires", ""),
                "days": self.days_remaining(),
                "message": (
                    f"You already have an active {current['tier'].title()} license — "
                    "no trial needed."
                ),
            }

        expiry = _utcnow() + timedelta(days=_TRIAL_DAYS)
        trial_state: dict[str, Any] = {
            "key": "",
            "tier": "pro",
            "email": "",
            "expires": expiry.isoformat(),
            "activated_at": _utcnow().isoformat(),
            "trial": True,
        }

        self._write_license_file(trial_state)
        self._cache = trial_state
        logger.info("Pro trial started — expires %s", expiry.isoformat())

        return {
            "success": True,
            "expires": expiry.isoformat(),
            "days": _TRIAL_DAYS,
            "message": f"🎉  {_TRIAL_DAYS}-day Pro trial activated! Enjoy full Pro features.",
        }

    # ── Private helpers ───────────────────────────────────────────────────

    def _effective_state(self) -> dict[str, Any]:
        """Return the current license state, falling back to Free defaults.

        Uses an in-memory cache to avoid repeated disk reads within the same
        ``LicenseManager`` lifetime.
        """
        if self._cache is not None:
            return self._cache

        state = self._read_license_file()
        if state:
            # Check for expired trial → revert to free
            if state.get("trial"):
                expires_raw = state.get("expires", "")
                try:
                    expiry_dt = datetime.fromisoformat(expires_raw)
                    if expiry_dt.tzinfo is None:
                        expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
                    if _utcnow() > expiry_dt:
                        logger.info("Pro trial expired — reverting to Free tier")
                        state = {"tier": "free", "trial": True, "expired_trial": True}
                except (ValueError, TypeError):
                    pass

            self._cache = state
            return state

        self._cache = {"tier": "free"}
        return self._cache

    @staticmethod
    def _read_license_file() -> Optional[dict[str, Any]]:
        """Read the license JSON file, returning ``None`` on any error."""
        try:
            if _LICENSE_FILE.is_file():
                return json.loads(_LICENSE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read license file: %s", exc)
        return None

    @staticmethod
    def _write_license_file(data: dict[str, Any]) -> None:
        """Write *data* to the license JSON file, creating dirs as needed."""
        try:
            _LICENSE_DIR.mkdir(parents=True, exist_ok=True)
            _LICENSE_FILE.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8",
            )
            logger.debug("Wrote license state to %s", _LICENSE_FILE)
        except OSError as exc:
            logger.error("Could not write license file: %s", exc)
            raise

    # ── Key-metadata persistence ──────────────────────────────────────────
    # Metadata is stored alongside the license file so that ``validate_key``
    # can recompute the HMAC without needing the original email/expiry args.

    @staticmethod
    def _metadata_path() -> Path:
        """Path to the key-metadata store."""
        return _LICENSE_DIR / "key_metadata.json"

    def _save_key_metadata(
        self,
        key: str,
        tier: str,
        email: str,
        expiry_ts: str,
    ) -> None:
        """Persist the email and expiry for a generated key."""
        path = self._metadata_path()
        store: dict[str, Any] = {}
        try:
            if path.is_file():
                store = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            store = {}

        store[key] = {"tier": tier, "email": email, "expiry_ts": expiry_ts}

        try:
            _LICENSE_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(store, indent=2), encoding="utf-8")
        except OSError as exc:
            logger.error("Could not write key metadata: %s", exc)

    def _load_key_metadata(self, key: str) -> Optional[dict[str, Any]]:
        """Load metadata for a previously generated key."""
        path = self._metadata_path()
        try:
            if path.is_file():
                store = json.loads(path.read_text(encoding="utf-8"))
                return store.get(key)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read key metadata: %s", exc)
        return None
