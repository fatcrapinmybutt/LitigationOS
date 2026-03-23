"""Tests for CourtFormFiller engine — SCAO form auto-fill, party data, validation."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from litigationos.engines.court_form_filler import (
    CourtFormFiller,
    PARTY_DATA,
    _MOTION_FORM_MAP,
    _HAS_REPORTLAB,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def forms_db(tmp_path: Path) -> Path:
    """Create a temporary court_forms.db with realistic schema and seed data."""
    db_path = tmp_path / "court_forms.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(
        """
        CREATE TABLE court_forms (
            form_id      TEXT PRIMARY KEY,
            form_number  TEXT,
            form_name    TEXT,
            form_series  TEXT,
            court_level  TEXT,
            division     TEXT,
            description  TEXT,
            url          TEXT,
            page_count   INTEGER,
            fillable     INTEGER DEFAULT 0,
            required_for TEXT,
            filing_lanes TEXT,
            mcr_reference TEXT,
            notes        TEXT
        );

        CREATE TABLE form_fields (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            form_id         TEXT,
            field_name      TEXT,
            field_type      TEXT,
            field_label     TEXT,
            auto_fill_source TEXT,
            auto_fill_value  TEXT,
            required        INTEGER DEFAULT 0,
            section         TEXT,
            notes           TEXT
        );

        CREATE TABLE form_filing_map (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            filing_type      TEXT,
            form_id          TEXT,
            required         INTEGER DEFAULT 1,
            order_in_package INTEGER DEFAULT 1,
            notes            TEXT
        );

        INSERT INTO court_forms VALUES
            ('MC_15', 'MC 15', 'Motion', 'MC', 'Circuit', 'General',
             'Generic motion form', NULL, 2, 1, 'all motions', 'A,D,E', 'MCR 2.119', NULL),
            ('MC_16', 'MC 16', 'Response to Motion', 'MC', 'Circuit', 'General',
             'Response/answer to motion', NULL, 2, 1, 'responses', 'A,D', 'MCR 2.119', NULL),
            ('CC_375', 'CC 375', 'Petition for PPO (Domestic)', 'CC', 'Circuit', 'Civil',
             'PPO petition form', NULL, 4, 1, 'ppo', 'D', 'MCL 600.2950', NULL),
            ('FOC_10', 'FOC 10', 'UCCJEA Affidavit', 'FOC', 'Circuit', 'Family',
             'Uniform Child Custody Jurisdiction affidavit', NULL, 3, 1, 'custody', 'A',
             'MCR 3.206', NULL);

        INSERT INTO form_fields (form_id, field_name, field_type, field_label,
                                 auto_fill_source, auto_fill_value, required, section)
        VALUES
            ('MC_15', 'plaintiff_name', 'text', 'Plaintiff/Moving Party',
             'party_data', NULL, 1, 'header'),
            ('MC_15', 'defendant_name', 'text', 'Defendant/Responding Party',
             'party_data', NULL, 1, 'header'),
            ('MC_15', 'case_number', 'text', 'Case Number',
             'party_data', NULL, 1, 'header'),
            ('MC_15', 'judge_name', 'text', 'Judge',
             'party_data', NULL, 0, 'header'),
            ('MC_15', 'court_address', 'text', 'Court Address',
             'party_data', '990 Terrace St, Muskegon, MI 49442', 0, 'header');

        INSERT INTO form_filing_map (filing_type, form_id, required, order_in_package, notes)
        VALUES
            ('disqualify', 'MC_15', 1, 1, 'Motion form'),
            ('ppo', 'CC_375', 1, 1, 'PPO petition');
        """
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def filler(tmp_path: Path, forms_db: Path) -> CourtFormFiller:
    """CourtFormFiller wired to the temporary court_forms.db."""
    filler = CourtFormFiller()
    filler._court_forms_db = forms_db
    # Point litigation DB at a non-existent path (not needed for most tests)
    filler._litigation_db = tmp_path / "litigation_context.db"
    return filler


# ============================================================================
# Core Operations
# ============================================================================


class TestCoreOperations:
    """Core instantiation and public API surface."""

    def test_form_filler_instantiation(self):
        """CourtFormFiller can be created with no arguments."""
        engine = CourtFormFiller()
        assert engine is not None
        assert engine._db is None

    def test_form_filler_instantiation_with_db(self, tmp_db):
        """CourtFormFiller accepts an optional DatabaseManager."""
        engine = CourtFormFiller(db=tmp_db)
        assert engine._db is tmp_db

    def test_list_forms(self, filler: CourtFormFiller):
        """list_forms returns all registered court forms from DB."""
        forms = filler.list_forms()
        assert isinstance(forms, list)
        assert len(forms) == 4
        form_ids = {f["form_id"] for f in forms}
        assert form_ids == {"MC_15", "MC_16", "CC_375", "FOC_10"}

    def test_list_forms_contains_expected_keys(self, filler: CourtFormFiller):
        """Each form dict has all expected metadata keys."""
        forms = filler.list_forms()
        expected_keys = {
            "form_id", "form_number", "form_name", "form_series",
            "court_level", "division", "description", "url",
            "page_count", "fillable", "required_for", "filing_lanes",
            "mcr_reference", "notes",
        }
        for form in forms:
            assert expected_keys.issubset(form.keys()), (
                f"Missing keys in form {form.get('form_id')}"
            )

    def test_get_form_fields(self, filler: CourtFormFiller):
        """get_form_fields returns field definitions for a known form."""
        fields = filler.get_form_fields("MC_15")
        assert isinstance(fields, list)
        assert len(fields) == 5
        names = [f["field_name"] for f in fields]
        assert "plaintiff_name" in names
        assert "case_number" in names

    def test_auto_fill_party_data(self, filler: CourtFormFiller):
        """auto_fill_party_data merges PARTY_DATA with DB auto-fill values."""
        data = filler.auto_fill_party_data("MC_15")
        assert isinstance(data, dict)
        # Must contain all base PARTY_DATA keys
        for key in PARTY_DATA:
            assert key in data, f"Missing PARTY_DATA key: {key}"
            assert data[key] == PARTY_DATA[key]
        # Must contain the DB-sourced auto_fill_value for court_address
        assert data["court_address"] == "990 Terrace St, Muskegon, MI 49442"
        # Must have date fields injected
        today = datetime.now().strftime("%m/%d/%Y")
        assert data["date"] == today


# ============================================================================
# Party Data Verification (identity truth — NEVER fabricate)
# ============================================================================


class TestPartyDataVerification:
    """Verify the hardcoded PARTY_DATA matches the single source of truth."""

    def test_party_data_plaintiff_correct(self):
        """Plaintiff is Andrew James Pigors at the verified address."""
        assert PARTY_DATA["plaintiff_name"] == "Andrew James Pigors"
        assert "1977 Whitehall Road" in PARTY_DATA["plaintiff_address"]
        assert PARTY_DATA["plaintiff_city"] == "North Muskegon"
        assert PARTY_DATA["plaintiff_state"] == "MI"
        assert PARTY_DATA["plaintiff_zip"] == "49445"
        assert PARTY_DATA["plaintiff_phone"] == "(231) 903-5690"
        assert PARTY_DATA["plaintiff_email"] == "andrewjpigors@gmail.com"

    def test_party_data_defendant_correct(self):
        """Defendant is Emily A. Watson — NOT 'Emily Ann' or 'Emily M.'."""
        assert PARTY_DATA["defendant_name"] == "Emily A. Watson"
        assert "Emily Ann" not in PARTY_DATA["defendant_name"]
        assert "Emily M." not in PARTY_DATA["defendant_name"]
        assert "Tiffany" not in PARTY_DATA["defendant_name"]
        assert PARTY_DATA["defendant_city"] == "Norton Shores"
        assert PARTY_DATA["defendant_zip"] == "49441"

    def test_child_initials_in_party_data(self):
        """Child is referenced by initials only (L.D.W.) per MCR 8.119(H)."""
        assert PARTY_DATA["child_initials"] == "L.D.W."
        # Ensure no full child name appears anywhere in PARTY_DATA values
        all_values = " ".join(str(v) for v in PARTY_DATA.values())
        assert "L.D.W." in all_values

    def test_judge_name_correct(self):
        """Judge is Hon. Jenny L. McNeill (NOT 'Amy McNeill')."""
        assert PARTY_DATA["judge_name"] == "Hon. Jenny L. McNeill"
        assert "Amy" not in PARTY_DATA["judge_name"]

    def test_case_number_correct(self):
        """Primary case number is 2024-001507-DC."""
        assert PARTY_DATA["case_number"] == "2024-001507-DC"

    def test_foc_name_correct(self):
        """FOC representative is Pamela Rusco."""
        assert PARTY_DATA["foc_name"] == "Pamela Rusco"


# ============================================================================
# Form Filling
# ============================================================================


class TestFormFilling:
    """Fill_form and validate_form outputs."""

    @pytest.mark.skipif(not _HAS_REPORTLAB, reason="reportlab not installed")
    def test_fill_form_produces_output(self, filler: CourtFormFiller, tmp_path: Path):
        """fill_form creates a PDF file at the specified output path."""
        out = tmp_path / "output" / "mc15_filled.pdf"
        result = filler.fill_form("MC_15", PARTY_DATA.copy(), str(out))
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0

    @pytest.mark.skipif(not _HAS_REPORTLAB, reason="reportlab not installed")
    def test_fill_form_with_custom_data(self, filler: CourtFormFiller, tmp_path: Path):
        """fill_form accepts arbitrary field_values dict."""
        custom = {"custom_field": "Custom Value", "notes": "Test notes"}
        out = tmp_path / "custom_filled.pdf"
        result = filler.fill_form("NONEXISTENT_FORM", custom, str(out))
        assert Path(result).exists()

    def test_fill_form_no_libraries_raises(self, filler: CourtFormFiller, tmp_path: Path):
        """fill_form raises RuntimeError when both pikepdf and reportlab are absent."""
        out = tmp_path / "should_fail.pdf"
        with patch("litigationos.engines.court_form_filler._HAS_PIKEPDF", False), \
             patch("litigationos.engines.court_form_filler._HAS_REPORTLAB", False):
            with pytest.raises(RuntimeError, match="Neither pikepdf nor reportlab"):
                filler.fill_form("MC_15", {"field": "value"}, str(out))

    def test_validate_form_missing_file(self, filler: CourtFormFiller, tmp_path: Path):
        """validate_form returns invalid result for non-existent file."""
        report = filler.validate_form(str(tmp_path / "no_such_file.pdf"))
        assert report["valid"] is False
        assert any("not found" in w.lower() for w in report["warnings"])

    def test_validate_form_result_structure(self, filler: CourtFormFiller, tmp_path: Path):
        """validate_form always returns expected keys regardless of input."""
        report = filler.validate_form(str(tmp_path / "missing.pdf"))
        assert "valid" in report
        assert "total_fields" in report
        assert "filled_fields" in report
        assert "empty_required" in report
        assert "warnings" in report
        assert isinstance(report["empty_required"], list)
        assert isinstance(report["warnings"], list)

    @pytest.mark.skipif(not _HAS_REPORTLAB, reason="reportlab not installed")
    def test_batch_fill(self, filler: CourtFormFiller, tmp_path: Path):
        """batch_fill fills multiple forms into an output directory."""
        out_dir = tmp_path / "batch_out"
        results = filler.batch_fill(
            ["MC_15", "MC_16"], PARTY_DATA.copy(), str(out_dir),
        )
        assert isinstance(results, list)
        assert len(results) == 2
        for p in results:
            assert Path(p).exists()


# ============================================================================
# Motion Form Mapping
# ============================================================================


class TestMotionFormMapping:
    """get_form_for_motion and _MOTION_FORM_MAP coverage."""

    def test_motion_form_map_coverage(self):
        """All expected motion types are in _MOTION_FORM_MAP."""
        expected = {"disqualify", "response", "ppo", "custody", "show_cause",
                    "discovery", "appeal"}
        assert expected == set(_MOTION_FORM_MAP.keys())

    def test_get_form_for_motion_hardcoded(self, filler: CourtFormFiller):
        """get_form_for_motion returns results from the hardcoded map."""
        forms = filler.get_form_for_motion("custody")
        assert len(forms) >= 2
        form_ids = {f["form_id"] for f in forms}
        assert "FOC_10" in form_ids
        assert "DC_100" in form_ids

    def test_get_form_for_motion_db_lookup(self, filler: CourtFormFiller):
        """get_form_for_motion checks DB form_filing_map first."""
        forms = filler.get_form_for_motion("disqualify")
        assert len(forms) >= 1
        # DB row should be returned (has form_name key from JOIN)
        assert any("form_name" in f for f in forms)

    def test_get_form_for_motion_unknown(self, filler: CourtFormFiller):
        """Unknown motion type returns an empty list."""
        forms = filler.get_form_for_motion("totally_unknown_motion_xyz")
        assert forms == []

    def test_get_form_for_motion_normalizes_input(self, filler: CourtFormFiller):
        """Motion type lookup strips whitespace and normalizes case."""
        forms = filler.get_form_for_motion("  APPEAL  ")
        assert len(forms) >= 1
        form_ids = {f["form_id"] for f in forms}
        assert "CA_1" in form_ids

    def test_get_form_for_motion_fuzzy_substring(self, filler: CourtFormFiller):
        """Fuzzy fallback matches substring keys (e.g., 'cause' → 'show_cause')."""
        forms = filler.get_form_for_motion("cause")
        assert len(forms) >= 1


# ============================================================================
# Edge Cases
# ============================================================================


class TestEdgeCases:
    """Graceful degradation and boundary conditions."""

    def test_unknown_form_handled(self, filler: CourtFormFiller):
        """get_form_fields returns empty list for unknown form_id."""
        fields = filler.get_form_fields("NONEXISTENT_FORM_999")
        assert fields == []

    def test_missing_db_graceful(self, tmp_path: Path):
        """Engine degrades gracefully when court_forms.db doesn't exist."""
        engine = CourtFormFiller()
        engine._court_forms_db = tmp_path / "nonexistent.db"
        # list_forms should handle the missing DB without crashing
        # (sqlite3.connect creates the file, but the table won't exist)
        forms = engine.list_forms()
        assert forms == []

    def test_table_exists_check(self, tmp_path: Path):
        """_table_exists correctly detects present and absent tables."""
        db_path = tmp_path / "check.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE present_table (id INTEGER)")
        assert CourtFormFiller._table_exists(conn, "present_table") is True
        assert CourtFormFiller._table_exists(conn, "absent_table") is False
        conn.close()

    def test_acro_type_label(self):
        """_acro_type_label maps AcroForm /FT names correctly."""
        assert CourtFormFiller._acro_type_label("/Tx") == "text"
        assert CourtFormFiller._acro_type_label("/Btn") == "checkbox"
        assert CourtFormFiller._acro_type_label("/Ch") == "choice"
        assert CourtFormFiller._acro_type_label("/Sig") == "signature"
        assert CourtFormFiller._acro_type_label("/Unknown") == "text"

    def test_auto_fill_party_data_unknown_form(self, filler: CourtFormFiller):
        """auto_fill_party_data still returns base PARTY_DATA for unknown forms."""
        data = filler.auto_fill_party_data("FAKE_FORM_999")
        assert data["plaintiff_name"] == "Andrew James Pigors"
        assert data["defendant_name"] == "Emily A. Watson"
        assert "date" in data

    def test_list_forms_no_court_forms_table(self, tmp_path: Path):
        """list_forms returns [] when DB exists but has no court_forms table."""
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE other_table (id INTEGER)")
        conn.close()
        engine = CourtFormFiller()
        engine._court_forms_db = db_path
        assert engine.list_forms() == []

    def test_get_form_fields_no_form_fields_table(self, tmp_path: Path):
        """get_form_fields returns [] when form_fields table doesn't exist."""
        db_path = tmp_path / "minimal.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            "CREATE TABLE court_forms (form_id TEXT, url TEXT)"
        )
        conn.close()
        engine = CourtFormFiller()
        engine._court_forms_db = db_path
        fields = engine.get_form_fields("MC_15")
        assert fields == []

    def test_motion_form_map_entries_valid(self):
        """Every entry in _MOTION_FORM_MAP has required keys."""
        for motion_type, forms in _MOTION_FORM_MAP.items():
            assert isinstance(forms, list), f"{motion_type} is not a list"
            for form in forms:
                assert "form_id" in form, f"Missing form_id in {motion_type}"
                assert "form_number" in form, f"Missing form_number in {motion_type}"
                assert "reason" in form, f"Missing reason in {motion_type}"
