"""Seed data for Michigan jurisdiction — courts, rules, and SCAO forms.

Called during first-run initialization or when the Michigan plugin is enabled.
Populates the database with baseline Michigan-specific data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager


def seed_michigan(db: DatabaseManager) -> None:
    """Insert Michigan seed data (jurisdiction, sample courts, default settings)."""
    conn = db.connect()
    try:
        # Ensure Michigan jurisdiction exists
        existing = conn.execute(
            "SELECT id FROM jurisdictions WHERE id = 'MI'"
        ).fetchone()
        if existing:
            return  # Already seeded

        conn.execute(
            "INSERT INTO jurisdictions (id, name, state_code, rules_version, enabled) "
            "VALUES ('MI', 'Michigan', 'MI', '2024', 1)"
        )

        # Sample Michigan courts
        michigan_courts = [
            ("MI", "Washtenaw County Circuit Court", "circuit", "Washtenaw",
             "101 E. Huron St, Ann Arbor, MI 48104", "(734) 222-3270",
             "https://www.washtenaw.org/839/Circuit-Court", None),
            ("MI", "Michigan Court of Appeals", "coa", None,
             "Cadillac Place, 3020 W. Grand Blvd, Detroit, MI 48202", "(313) 972-5700",
             "https://courts.michigan.gov/courts/coa", None),
            ("MI", "Michigan Supreme Court", "supreme", None,
             "925 W. Ottawa St, Lansing, MI 48915", "(517) 373-0120",
             "https://courts.michigan.gov/courts/supremecourt", None),
        ]
        conn.executemany(
            "INSERT INTO courts (jurisdiction_id, name, type, county, address, phone, efiling_url, local_rules_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            michigan_courts,
        )

        conn.commit()
    finally:
        conn.close()


def seed_default_settings(db: DatabaseManager) -> None:
    """Ensure default settings exist in the settings table."""
    defaults = [
        ("default_jurisdiction", "MI", "jurisdiction"),
        ("theme", "dark", "display"),
        ("bates_prefix", "EXHIBIT", "general"),
        ("auto_save", "1", "general"),
        ("ai_enabled", "0", "ai"),
        ("ollama_model", "llama3.2", "ai"),
        ("ollama_url", "http://localhost:11434", "ai"),
    ]
    conn = db.connect()
    try:
        for key, value, category in defaults:
            existing = conn.execute(
                "SELECT key FROM settings WHERE key = ?", (key,)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO settings (key, value, category) VALUES (?, ?, ?)",
                    (key, value, category),
                )
        conn.commit()
    finally:
        conn.close()
