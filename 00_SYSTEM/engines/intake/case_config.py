"""
Case Configuration — Portable, Case-Agnostic Configuration Loader
=================================================================

Case specificity lives HERE, not in code. Every case has a config
that defines parties, courts, lanes, and DB paths. The system reads
this config at intake time and passes it through the pipeline.

Config can come from:
  1. A YAML file in the intake folder (case_config.yaml)
  2. A record in the case database (cases table)
  3. Manual dict passed to the pipeline

Example case_config.yaml:
  case_name: "Pigors v Watson"
  case_number: "2024-001507-DC"
  court: "14th Judicial Circuit, Muskegon County"
  division: "Family"
  judge: "Hon. Jenny L. McNeill"
  plaintiff:
    name: "Andrew J. Pigors"
    address: "1977 Whitehall Rd, Lot 17, North Muskegon, MI 49445"
    phone: "(231) 903-5690"
    email: "andrewjpigors@gmail.com"
    pro_se: true
  defendant:
    name: "Emily A. Watson"
    address: "2160 Garland Dr, Norton Shores, MI 49441"
  lanes:
    A:
      label: "Custody"
      case_number: "2024-001507-DC"
      court: "14th Circuit"
      judge: "Hon. Jenny L. McNeill"
    D:
      label: "PPO"
      case_number: "2023-5907-PP"
  db_path: "litigation_context.db"  # relative to intake root or absolute
  child_initials: "L.D.W."         # MCR 8.119(H) — never full name
  jurisdiction: "MI"
  key_dates:
    last_contact: "2025-07-29"
    complaint_filed: "2024-04-01"
"""

import os
import sqlite3
from pathlib import Path
from typing import Optional

# Try YAML import — optional dependency
try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

# Try JSON as fallback
import json


class CaseConfig:
    """Portable case configuration. No hardcoded parties or case numbers."""

    def __init__(self, config: dict = None):
        self._data = config or {}

    # --- Factory methods ---

    @classmethod
    def from_yaml(cls, path: str | Path) -> "CaseConfig":
        """Load from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Case config not found: {path}")
        if not _HAS_YAML:
            raise ImportError("PyYAML required for YAML configs: pip install pyyaml")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(data)

    @classmethod
    def from_json(cls, path: str | Path) -> "CaseConfig":
        """Load from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Case config not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(data)

    @classmethod
    def from_db(cls, db_path: str | Path, case_number: str) -> "CaseConfig":
        """Load from a database cases table."""
        conn = sqlite3.connect(str(db_path), timeout=30)
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.execute("PRAGMA temp_store=2")
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT config_json FROM cases WHERE case_number = ?",
            (case_number,)
        ).fetchone()
        conn.close()
        if not row:
            raise ValueError(f"Case {case_number} not found in {db_path}")
        return cls(json.loads(row["config_json"]))

    @classmethod
    def auto_detect(cls, intake_path: str | Path) -> "CaseConfig":
        """Auto-detect config from intake folder. Looks for:
        1. case_config.yaml
        2. case_config.json
        3. Returns empty config (will classify from content)
        """
        intake = Path(intake_path)
        yaml_path = intake / "case_config.yaml"
        json_path = intake / "case_config.json"

        if yaml_path.exists() and _HAS_YAML:
            return cls.from_yaml(yaml_path)
        elif json_path.exists():
            return cls.from_json(json_path)
        else:
            return cls({})  # Will use content-based classification

    # --- Accessors ---

    @property
    def case_name(self) -> str:
        return self._data.get("case_name", "Unknown Case")

    @property
    def case_number(self) -> str:
        return self._data.get("case_number", "")

    @property
    def court(self) -> str:
        return self._data.get("court", "")

    @property
    def division(self) -> str:
        return self._data.get("division", "")

    @property
    def judge(self) -> str:
        return self._data.get("judge", "")

    @property
    def plaintiff(self) -> dict:
        return self._data.get("plaintiff", {})

    @property
    def defendant(self) -> dict:
        return self._data.get("defendant", {})

    @property
    def lanes(self) -> dict:
        return self._data.get("lanes", {})

    @property
    def db_path(self) -> Optional[str]:
        return self._data.get("db_path")

    @property
    def child_initials(self) -> Optional[str]:
        return self._data.get("child_initials")

    @property
    def jurisdiction(self) -> str:
        return self._data.get("jurisdiction", "MI")

    @property
    def key_dates(self) -> dict:
        return self._data.get("key_dates", {})

    @property
    def is_configured(self) -> bool:
        """True if we have at least a case number."""
        return bool(self.case_number)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def to_dict(self) -> dict:
        return dict(self._data)

    def to_case_info(self) -> dict:
        """Convert to the case_info dict format used by Filing Engine."""
        return {
            "case_number": self.case_number,
            "court": self.court,
            "county": self._data.get("county", ""),
            "judge": self.judge,
            "plaintiff": self.plaintiff.get("name", ""),
            "defendant": self.defendant.get("name", ""),
            "division": self.division,
            "pro_se": self.plaintiff.get("pro_se", True),
        }

    def to_signer_info(self) -> dict:
        """Convert plaintiff data to signer_info dict for Filing Engine."""
        p = self.plaintiff
        return {
            "name": p.get("name", ""),
            "address": p.get("address", ""),
            "city": p.get("city", ""),
            "state": p.get("state", self.jurisdiction),
            "zip": p.get("zip", ""),
            "phone": p.get("phone", ""),
            "email": p.get("email", ""),
        }

    def to_parties_served(self) -> list[dict]:
        """Build parties_served list from defendant + any additional parties."""
        parties = []
        d = self.defendant
        if d.get("name"):
            parties.append({
                "name": d["name"],
                "address": d.get("address", ""),
            })
        for extra in self._data.get("additional_service", []):
            parties.append(extra)
        return parties
