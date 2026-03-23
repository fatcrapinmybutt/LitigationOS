"""Comprehensive test suite for the ServiceGenerator engine.

Tests cover instantiation, proof of service generation, certificate of service,
service method listing, validation, service tracking (DB), service history,
service list generation, caption building, edge cases, and MCR compliance.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

import pytest

from litigationos.engines.service_generator import (
    FILING_COURTS,
    FILING_SERVICE_MAP,
    PARTIES,
    SERVICE_METHODS,
    ProofOfService,
    ServiceGenerator,
    ServiceMethod,
    ServiceRecord,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Create a minimal SQLite database for service tracking tests."""
    db_path = tmp_path / "test_service.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=60000")
    conn.commit()
    conn.close()
    return db_path


class _MinimalDB:
    """Lightweight stand-in for DatabaseManager used in tests."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=120)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.row_factory = sqlite3.Row
        return conn

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self.connect()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor
        finally:
            conn.close()

    def fetchone(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        conn = self.connect()
        try:
            return conn.execute(sql, params).fetchone()
        finally:
            conn.close()

    def fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        conn = self.connect()
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()


@pytest.fixture
def db(tmp_db_path: Path) -> _MinimalDB:
    """Return a _MinimalDB backed by a temporary SQLite file."""
    return _MinimalDB(tmp_db_path)


@pytest.fixture
def gen(db: _MinimalDB) -> ServiceGenerator:
    """Return a ServiceGenerator backed by the temporary database."""
    return ServiceGenerator(db)


# ---------------------------------------------------------------------------
# 1. Instantiation & table creation
# ---------------------------------------------------------------------------


class TestInstantiation:
    """ServiceGenerator bootstraps correctly."""

    def test_creates_service_tracking_table(self, gen: ServiceGenerator, db: _MinimalDB) -> None:
        conn = db.connect()
        try:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
            assert "service_tracking" in tables
        finally:
            conn.close()

    def test_creates_indexes(self, gen: ServiceGenerator, db: _MinimalDB) -> None:
        conn = db.connect()
        try:
            indexes = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index'"
                ).fetchall()
            ]
            assert "idx_service_tracking_filing" in indexes
            assert "idx_service_tracking_case" in indexes
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# 2. get_service_methods
# ---------------------------------------------------------------------------


class TestGetServiceMethods:
    """get_service_methods returns valid MCR methods."""

    def test_returns_all_four_methods(self, gen: ServiceGenerator) -> None:
        methods = gen.get_service_methods()
        assert len(methods) == 4

    def test_methods_are_service_method_instances(self, gen: ServiceGenerator) -> None:
        methods = gen.get_service_methods()
        for m in methods:
            assert isinstance(m, ServiceMethod)
            assert m.method_name
            assert m.mcr_rule

    def test_mail_method_has_3_day_effectiveness(self, gen: ServiceGenerator) -> None:
        methods = gen.get_service_methods()
        mail = [m for m in methods if m.method_name == "First-Class Mail"]
        assert len(mail) == 1
        assert mail[0].time_to_effective_service == 3

    def test_personal_method_immediate(self, gen: ServiceGenerator) -> None:
        methods = gen.get_service_methods()
        personal = [m for m in methods if m.method_name == "Personal Service"]
        assert len(personal) == 1
        assert personal[0].time_to_effective_service == 0


# ---------------------------------------------------------------------------
# 3. generate_proof_of_service
# ---------------------------------------------------------------------------


class TestGenerateProofOfService:
    """Proof of service generation produces MCR-compliant documents."""

    def test_returns_proof_of_service_model(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "mail", ["defendant"])
        assert isinstance(pos, ProofOfService)

    def test_contains_case_number(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "mail")
        assert pos.case_number == "2024-001507-DC"

    def test_markdown_contains_signer(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "mail", ["defendant"])
        assert "Andrew James Pigors" in pos.markdown

    def test_markdown_contains_mcr_rule(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "mail", ["defendant"])
        assert "MCR 2.107(C)(1)" in pos.markdown

    def test_markdown_contains_recipient_name(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "mail", ["defendant"])
        assert "Emily A. Watson" in pos.markdown

    def test_mail_service_includes_effective_date_note(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "mail", ["defendant"])
        assert "three (3) days" in pos.markdown
        assert "Effective date of service" in pos.markdown

    def test_personal_service_no_effective_note(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "personal", ["defendant"])
        assert "three (3) days" not in pos.markdown

    def test_multiple_recipients(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "mail", ["defendant", "foc"])
        assert len(pos.service_records) == 2
        assert "Emily A. Watson" in pos.markdown
        assert "Pamela Rusco" in pos.markdown

    def test_default_recipients_from_map(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "mail")
        expected = FILING_SERVICE_MAP["F3"]
        assert len(pos.service_records) == len(expected)

    def test_coa_caption(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F9", "efiling", ["defendant"])
        assert "COURT OF APPEALS" in pos.markdown
        assert "366810" in pos.markdown

    def test_invalid_filing_raises(self, gen: ServiceGenerator) -> None:
        with pytest.raises(ValueError, match="Unknown filing"):
            gen.generate_proof_of_service("F999", "mail")

    def test_invalid_method_raises(self, gen: ServiceGenerator) -> None:
        with pytest.raises(ValueError, match="Unknown service method"):
            gen.generate_proof_of_service("F3", "carrier_pigeon")

    def test_custom_service_date(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service(
            "F3", "mail", ["defendant"], service_date="January 15, 2025"
        )
        assert "January 15, 2025" in pos.markdown

    def test_perjury_language(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "mail", ["defendant"])
        assert "penalties of perjury" in pos.markdown

    def test_signature_block_address(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "mail")
        assert "1977 Whitehall Road, Lot 17" in pos.markdown
        assert "North Muskegon, MI 49445" in pos.markdown

    def test_federal_caption(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F4", "mail", ["defendant"])
        assert "WESTERN DISTRICT OF MICHIGAN" in pos.markdown

    def test_jtc_caption(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F6", "personal", ["judge"])
        assert "JUDICIAL TENURE COMMISSION" in pos.markdown

    def test_supreme_court_caption(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F5", "mail", ["defendant"])
        assert "SUPREME COURT" in pos.markdown


# ---------------------------------------------------------------------------
# 4. generate_certificate_of_service
# ---------------------------------------------------------------------------


class TestGenerateCertificateOfService:
    """Certificate of service is a shorter attachment form."""

    def test_returns_string(self, gen: ServiceGenerator) -> None:
        cert = gen.generate_certificate_of_service("F3")
        assert isinstance(cert, str)

    def test_contains_certificate_header(self, gen: ServiceGenerator) -> None:
        cert = gen.generate_certificate_of_service("F3")
        assert "CERTIFICATE OF SERVICE" in cert

    def test_contains_mcr_rule(self, gen: ServiceGenerator) -> None:
        cert = gen.generate_certificate_of_service("F3", service_method="personal")
        assert "MCR 2.105(A)" in cert

    def test_mail_includes_effective_date(self, gen: ServiceGenerator) -> None:
        cert = gen.generate_certificate_of_service(
            "F3", service_method="mail", service_date="January 10, 2025"
        )
        assert "Effective date of service" in cert
        assert "January 13, 2025" in cert

    def test_email_has_no_effective_date(self, gen: ServiceGenerator) -> None:
        cert = gen.generate_certificate_of_service("F3", service_method="email")
        assert "Effective date of service" not in cert


# ---------------------------------------------------------------------------
# 5. validate_service
# ---------------------------------------------------------------------------


class TestValidateService:
    """Service validation catches MCR compliance issues."""

    def test_valid_mail_record_no_issues(self, gen: ServiceGenerator) -> None:
        record = ServiceRecord(
            filing_id="F3",
            served_party="defendant",
            method="mail",
            date="2025-01-15",
            address="2160 Garland Drive, Norton Shores, MI 49441",
            completed=True,
        )
        issues = gen.validate_service(record)
        assert issues == []

    def test_missing_address_for_mail(self, gen: ServiceGenerator) -> None:
        record = ServiceRecord(
            filing_id="F3",
            served_party="defendant",
            method="mail",
            date="2025-01-15",
            address="",
            completed=True,
        )
        issues = gen.validate_service(record)
        assert any("Address required" in i for i in issues)

    def test_email_without_consent(self, gen: ServiceGenerator) -> None:
        record = ServiceRecord(
            filing_id="F3",
            served_party="defendant",
            method="email",
            date="2025-01-15",
            completed=True,
        )
        issues = gen.validate_service(record)
        assert any("consent" in i.lower() for i in issues)

    def test_email_with_consent_passes(self, gen: ServiceGenerator) -> None:
        record = ServiceRecord(
            filing_id="F3",
            served_party="defendant",
            method="email",
            date="2025-01-15",
            notes="Written consent obtained on 2025-01-01",
            completed=True,
        )
        issues = gen.validate_service(record)
        assert issues == []

    def test_invalid_method_flagged(self, gen: ServiceGenerator) -> None:
        record = ServiceRecord(
            filing_id="F3",
            served_party="defendant",
            method="smoke_signal",
            date="2025-01-15",
        )
        issues = gen.validate_service(record)
        assert any("Invalid service method" in i for i in issues)

    def test_missing_party_flagged(self, gen: ServiceGenerator) -> None:
        record = ServiceRecord(
            filing_id="F3",
            served_party="",
            method="mail",
            date="2025-01-15",
            address="123 Main St",
        )
        issues = gen.validate_service(record)
        assert any("served_party" in i for i in issues)

    def test_bad_date_flagged(self, gen: ServiceGenerator) -> None:
        record = ServiceRecord(
            filing_id="F3",
            served_party="defendant",
            method="efiling",
            date="not-a-date",
            completed=True,
        )
        issues = gen.validate_service(record)
        assert any("Cannot parse" in i for i in issues)

    def test_incomplete_service_flagged(self, gen: ServiceGenerator) -> None:
        record = ServiceRecord(
            filing_id="F3",
            served_party="defendant",
            method="efiling",
            date="2025-01-15",
            completed=False,
        )
        issues = gen.validate_service(record)
        assert any("incomplete" in i.lower() for i in issues)


# ---------------------------------------------------------------------------
# 6. track_service (DB)
# ---------------------------------------------------------------------------


class TestTrackService:
    """Service tracking persists to the database."""

    def test_returns_row_id(self, gen: ServiceGenerator) -> None:
        row_id = gen.track_service("F3", "defendant", "mail", "2025-01-15")
        assert isinstance(row_id, int)
        assert row_id > 0

    def test_record_persisted(self, gen: ServiceGenerator, db: _MinimalDB) -> None:
        gen.track_service("F3", "defendant", "mail", "2025-01-15")
        row = db.fetchone(
            "SELECT * FROM service_tracking WHERE filing_id = 'F3'"
        )
        assert row is not None
        d = dict(row)
        assert d["served_party"] == "defendant"
        assert d["party_name"] == "Emily A. Watson"
        assert d["service_method"] == "mail"

    def test_tracks_multiple_parties(self, gen: ServiceGenerator, db: _MinimalDB) -> None:
        gen.track_service("F3", "defendant", "mail", "2025-01-15")
        gen.track_service("F3", "foc", "mail", "2025-01-15")
        rows = db.fetchall(
            "SELECT * FROM service_tracking WHERE filing_id = 'F3'"
        )
        assert len(rows) == 2

    def test_invalid_method_raises(self, gen: ServiceGenerator) -> None:
        with pytest.raises(ValueError, match="Unknown service method"):
            gen.track_service("F3", "defendant", "telegram", "2025-01-15")


# ---------------------------------------------------------------------------
# 7. get_service_history
# ---------------------------------------------------------------------------


class TestGetServiceHistory:
    """Service history retrieval from database."""

    def test_empty_history(self, gen: ServiceGenerator) -> None:
        records = gen.get_service_history()
        assert records == []

    def test_returns_service_records(self, gen: ServiceGenerator) -> None:
        gen.track_service("F3", "defendant", "mail", "2025-01-15")
        records = gen.get_service_history()
        assert len(records) == 1
        assert isinstance(records[0], ServiceRecord)
        assert records[0].served_party == "defendant"

    def test_filter_by_case_number(self, gen: ServiceGenerator) -> None:
        gen.track_service("F3", "defendant", "mail", "2025-01-15")
        gen.track_service("F2", "defendant", "mail", "2025-01-16")
        # F3 is case 2024-001507-DC, F2 is 2025-002760-CZ
        records = gen.get_service_history("2024-001507-DC")
        assert len(records) == 1
        assert records[0].filing_id == "F3"

    def test_history_by_filing(self, gen: ServiceGenerator) -> None:
        gen.track_service("F3", "defendant", "mail", "2025-01-15")
        gen.track_service("F3", "foc", "mail", "2025-01-15")
        gen.track_service("F7", "defendant", "mail", "2025-01-16")
        records = gen.get_service_history_by_filing("F3")
        assert len(records) == 2


# ---------------------------------------------------------------------------
# 8. generate_service_list
# ---------------------------------------------------------------------------


class TestGenerateServiceList:
    """Service list generation for all parties."""

    def test_returns_markdown(self, gen: ServiceGenerator) -> None:
        result = gen.generate_service_list()
        assert isinstance(result, str)
        assert "SERVICE LIST" in result

    def test_includes_plaintiff(self, gen: ServiceGenerator) -> None:
        result = gen.generate_service_list()
        assert "Andrew James Pigors" in result

    def test_includes_defendant(self, gen: ServiceGenerator) -> None:
        result = gen.generate_service_list()
        assert "Emily A. Watson" in result

    def test_case_number_in_header(self, gen: ServiceGenerator) -> None:
        result = gen.generate_service_list("2024-001507-DC")
        assert "2024-001507-DC" in result

    def test_contact_info_present(self, gen: ServiceGenerator) -> None:
        result = gen.generate_service_list()
        assert "(231) 903-5690" in result
        assert "andrewjpigors@gmail.com" in result


# ---------------------------------------------------------------------------
# 9. Pydantic model validation
# ---------------------------------------------------------------------------


class TestPydanticModels:
    """Pydantic models serialize and validate correctly."""

    def test_service_record_defaults(self) -> None:
        record = ServiceRecord(filing_id="F3", served_party="defendant")
        assert record.method == "mail"
        assert record.completed is True

    def test_proof_of_service_defaults(self) -> None:
        pos = ProofOfService(case_number="2024-001507-DC", filing_title="Test")
        assert pos.signer == "Andrew James Pigors"
        assert pos.court_rule_basis == "MCR 2.107"

    def test_service_method_model(self) -> None:
        sm = ServiceMethod(
            method_name="Test",
            mcr_rule="MCR 9.999",
            requirements=["Req 1", "Req 2"],
            time_to_effective_service=5,
        )
        assert sm.time_to_effective_service == 5
        assert len(sm.requirements) == 2


# ---------------------------------------------------------------------------
# 10. Edge cases & constants
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and constant validation."""

    def test_all_filing_courts_have_entries(self) -> None:
        for fid in FILING_COURTS:
            assert "court" in FILING_COURTS[fid]
            assert "case_number" in FILING_COURTS[fid]

    def test_all_service_methods_have_rules(self) -> None:
        for key, method in SERVICE_METHODS.items():
            assert method.mcr_rule, f"Missing MCR rule for {key}"

    def test_party_identity_no_hallucinations(self) -> None:
        """Verify no hallucinated names appear in the PARTIES dict."""
        all_names = " ".join(
            p.get("name", "") for p in PARTIES.values() if isinstance(p, dict)
        )
        assert "Jane Berry" not in all_names
        assert "Patricia Berry" not in all_names
        assert "Tiffany" not in all_names

    def test_plaintiff_identity(self) -> None:
        p = PARTIES["plaintiff"]
        assert p["name"] == "Andrew James Pigors"
        assert "North Muskegon" in p["address"]

    def test_defendant_identity(self) -> None:
        d = PARTIES["defendant"]
        assert d["name"] == "Emily A. Watson"
        assert "Norton Shores" in d["address"]

    def test_case_insensitive_filing_id(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("f3", "mail", ["defendant"])
        assert pos.case_number == "2024-001507-DC"

    def test_efiling_method_mifle_rule(self, gen: ServiceGenerator) -> None:
        pos = gen.generate_proof_of_service("F3", "efiling", ["defendant"])
        assert "MCR 1.109(G)(6)(a)" in pos.markdown

    def test_withdrawn_attorney_status(self) -> None:
        assert PARTIES["defendant_attorney"]["status"] == "WITHDREW"
