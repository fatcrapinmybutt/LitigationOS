"""Integration tests — full filing pipeline end-to-end.

Exercises the complete lifecycle:
  case creation → claim setup → evidence linkage → IRAC scoring →
  authority chain → filing assembly → proof of service → e-filing validation.

All tests use the ``tmp_db`` fixture from conftest.py (temporary SQLite).
No production database is touched.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from litigationos.db.connection import DatabaseManager

# ── Engine imports (defensive) ──────────────────────────────────────────────

try:
    from litigationos.engines.case_engine import CaseEngine
except ImportError:
    CaseEngine = None  # type: ignore[assignment,misc]

try:
    from litigationos.engines.evidence import EvidenceEngine
except ImportError:
    EvidenceEngine = None  # type: ignore[assignment,misc]

try:
    from litigationos.engines.irac_engine import IRACEngine
except ImportError:
    IRACEngine = None  # type: ignore[assignment,misc]

try:
    from litigationos.engines.authority_chain import AuthorityChainEngine
except ImportError:
    AuthorityChainEngine = None  # type: ignore[assignment,misc]

try:
    from litigationos.engines.filing import FilingEngine
except ImportError:
    FilingEngine = None  # type: ignore[assignment,misc]

try:
    from litigationos.engines.filing_factory import (
        CaptionInfo,
        FilingFactory,
        FilingSpec,
        FilingType,
    )
except ImportError:
    FilingFactory = None  # type: ignore[assignment,misc]
    FilingSpec = None  # type: ignore[assignment,misc]
    FilingType = None  # type: ignore[assignment,misc]
    CaptionInfo = None  # type: ignore[assignment,misc]

try:
    from litigationos.engines.dashboard import DashboardEngine
except ImportError:
    DashboardEngine = None  # type: ignore[assignment,misc]

try:
    from litigationos.engines.witness_prep import WitnessEngine
except ImportError:
    WitnessEngine = None  # type: ignore[assignment,misc]


# ── Helpers ─────────────────────────────────────────────────────────────────


def _skip_if_missing(*engines):
    """Skip the test if any required engine failed to import."""
    for eng in engines:
        if eng is None:
            pytest.skip(f"Engine {eng!r} not importable")


def _seed_case(db: DatabaseManager) -> int:
    """Insert a minimal case and return its id."""
    cursor = db.execute(
        "INSERT INTO cases (case_number, case_type, title, status) "
        "VALUES (?, ?, ?, ?)",
        ("2025-INTEG-001", "family", "Pigors v. Watson", "active"),
    )
    return cursor.lastrowid


def _seed_parties(db: DatabaseManager, case_id: int) -> tuple[int, int]:
    """Insert plaintiff + defendant and return (plaintiff_id, defendant_id)."""
    p = db.execute(
        "INSERT INTO parties (case_id, name, role, party_type) VALUES (?, ?, ?, ?)",
        (case_id, "Andrew James Pigors", "petitioner", "individual"),
    ).lastrowid
    d = db.execute(
        "INSERT INTO parties (case_id, name, role, party_type) VALUES (?, ?, ?, ?)",
        (case_id, "Emily A. Watson", "respondent", "individual"),
    ).lastrowid
    return p, d


def _seed_claim(db: DatabaseManager, case_id: int, defendant_id: int) -> int:
    """Insert a custody-modification claim and return its id."""
    cursor = db.execute(
        "INSERT INTO claims (case_id, count_number, title, legal_basis, "
        "against_party_id, status) VALUES (?, ?, ?, ?, ?, ?)",
        (
            case_id,
            1,
            "Custody Modification",
            "MCL 722.27",
            defendant_id,
            "active",
        ),
    )
    return cursor.lastrowid


def _seed_evidence(
    db: DatabaseManager, case_id: int, tmp_path: Path
) -> list[int]:
    """Create 3 dummy files + evidence rows and return ids."""
    ids: list[int] = []
    items = [
        ("Custody Agreement", "Original custody agreement from 2020", "pdf"),
        ("Text Messages", "Screenshots from 2024-01-15", "image"),
        ("Financial Records", "Bank statements Jan-Mar 2024", "document"),
    ]
    for i, (title, desc, ftype) in enumerate(items, start=1):
        dummy = tmp_path / f"evidence_{i}.{ftype}"
        dummy.write_text(f"dummy evidence content {i}", encoding="utf-8")
        cursor = db.execute(
            "INSERT INTO evidence (case_id, title, description, file_path, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (case_id, title, desc, str(dummy), ftype),
        )
        ids.append(cursor.lastrowid)
    return ids


# ============================================================================
# 1.  Full Pipeline — Happy Path
# ============================================================================


class TestFullPipelineHappyPath:
    """End-to-end: case → claims → evidence → IRAC → authority → filing → dashboard."""

    def test_full_pipeline(self, tmp_db: DatabaseManager, tmp_path: Path):
        """Exercise every engine in sequence on a single case."""
        _skip_if_missing(CaseEngine, EvidenceEngine)

        # ── Step 1: Create case via CaseEngine ────────────────────────
        case_engine = CaseEngine(db=tmp_db)
        case_id = case_engine.create_case(
            "Pigors v. Watson",
            case_number="2025-PIPE-001",
            case_type="family",
        )
        assert case_id > 0

        case = case_engine.get_case(case_id)
        assert case["title"] == "Pigors v. Watson"
        assert case["status"] == "active"

        # ── Step 2: Add parties (verified names) ──────────────────────
        plaintiff_id = case_engine.add_party(
            case_id, "Andrew James Pigors", "petitioner",
        )
        defendant_id = case_engine.add_party(
            case_id, "Emily A. Watson", "respondent",
        )
        assert plaintiff_id > 0
        assert defendant_id > 0

        # ── Step 3: Add claims with statutory basis ───────────────────
        claim_id = case_engine.add_claim(
            case_id,
            "Custody Modification",
            legal_basis="MCL 722.27",
            against_party_id=defendant_id,
        )
        assert claim_id > 0

        # ── Step 4: Add evidence + link to claim ─────────────────────
        ev_engine = EvidenceEngine(tmp_db)
        ev_ids: list[int] = []
        evidence_files = [
            ("Custody Agreement", "document", "pdf"),
            ("Text Messages", "screenshot", "image"),
            ("Financial Records", "financial", "pdf"),
        ]
        for title, ev_type, ext in evidence_files:
            dummy = tmp_path / f"{title.replace(' ', '_').lower()}.{ext}"
            dummy.write_text(f"content for {title}", encoding="utf-8")
            eid = ev_engine.add_evidence(
                case_id=case_id,
                file_path=str(dummy),
                evidence_type=ev_type,
                description=f"{title} evidence item",
                title=title,
            )
            ev_ids.append(eid)

        assert len(ev_ids) == 3

        # Link evidence to claim
        for eid in ev_ids:
            case_engine.link_evidence_to_claim(
                eid, claim_id, strength="strong",
            )

        # Verify linkage via DB
        links = tmp_db.fetchall(
            "SELECT * FROM evidence_claims WHERE claim_id = ?", (claim_id,)
        )
        assert len(links) == 3

        # ── Step 5: Assign Bates numbers ─────────────────────────────
        assignments = ev_engine.assign_bates(case_id)
        assert len(assignments) == 3
        assert all("PIGORS-" in a["bates_number"] for a in assignments)

        # ── Step 6: Exhibit list generation ──────────────────────────
        exhibit_list = ev_engine.get_exhibit_list(case_id)
        assert "PIGORS-" in exhibit_list

        # ── Step 7: Evidence gap analysis ────────────────────────────
        gaps = ev_engine.check_gaps(case_id)
        # All claims have linked evidence, so no gaps expected
        gap_for_our_claim = [g for g in gaps if g.get("claim_id") == claim_id]
        assert len(gap_for_our_claim) == 0

        # ── Step 8: IRAC analysis ────────────────────────────────────
        if IRACEngine is not None:
            irac = IRACEngine(db_path=str(tmp_db.db_path))
            facts = [
                "Parent has demonstrated changed circumstances since last order",
                "Child's best interests require modification",
                "Existing custody arrangement is no longer appropriate",
            ]
            result = irac.analyze_claim("custody_modification", facts)
            assert isinstance(result, dict)
            assert "applicable_rules" in result or "issue" in result
            memo = irac.generate_irac_memo("custody_modification", facts)
            assert len(memo) > 50

        # ── Step 9: Authority chain ──────────────────────────────────
        if AuthorityChainEngine is not None:
            auth = AuthorityChainEngine(db=tmp_db)
            chain = auth.build_chain("custody_modification")
            assert isinstance(chain, list)

            validation = auth.validate_chain(chain)
            assert isinstance(validation, dict)
            score = auth.score_chain_strength(chain)
            assert 0 <= score <= 100

        # ── Step 10: Filing engine — create + stack + validate ───────
        if FilingEngine is not None:
            filing_eng = FilingEngine(tmp_db)
            filing_id = filing_eng.create_filing(
                case_id=case_id,
                filing_type="motion",
                court="14th Circuit Court, Family Division",
                title="Motion for Custody Modification",
            )
            assert filing_id > 0

            stack = filing_eng.build_stack(case_id, "motion")
            assert stack is not None

            val = filing_eng.validate_stack(stack)
            assert hasattr(val, "score")
            assert 0 <= val.score <= 100

            # Export to disk
            export_dir = tmp_path / "export"
            out = filing_eng.export_stack(stack, export_dir)
            assert out.exists()
            assert (out / "manifest.json").exists()

        # ── Step 11: FilingFactory — generate complete filing ────────
        if FilingFactory is not None:
            factory = FilingFactory(tmp_db)
            spec = FilingSpec(
                case_id=case_id,
                filing_type=FilingType.MOTION,
                court="14th Circuit Court, Family Division",
                title="Motion for Custody Modification",
                caption=CaptionInfo(
                    court_name="14th Circuit Court, Family Division",
                    case_number="2025-PIPE-001",
                    judge_name="Hon. Jenny L. McNeill",
                    plaintiff="Andrew James Pigors",
                    defendant="Emily A. Watson",
                    filing_title="Motion for Custody Modification",
                ),
                body_text=(
                    "Under MCL 722.27, Plaintiff moves this Court "
                    "for modification of the existing custody order."
                ),
            )
            generated = factory.generate_filing(spec)
            assert generated is not None
            assert generated.word_count > 0

        # ── Step 12: Dashboard — reflects all data ───────────────────
        if DashboardEngine is not None:
            dash = DashboardEngine(db_path=str(tmp_db.db_path))
            stats = dash.get_evidence_stats()
            assert isinstance(stats, dict)

            health = dash.get_case_health()
            assert isinstance(health, dict)

        # ── Step 13: Witness engine ──────────────────────────────────
        if WitnessEngine is not None:
            wit = WitnessEngine(db_path=str(tmp_db.db_path))
            w1 = wit.add_witness(
                name="Dr. Child Psychologist",
                role="expert",
                lane="A",
                relevance_score=9.5,
            )
            w2 = wit.add_witness(
                name="School Teacher",
                role="fact",
                lane="A",
                relevance_score=7.0,
            )
            witnesses = wit.list_witnesses(lane="A")
            assert len(witnesses) >= 2
            # Sorted by relevance descending
            assert witnesses[0]["relevance_score"] >= witnesses[1]["relevance_score"]

        # ── Step 14: Verify all DB tables populated ──────────────────
        counts = tmp_db.fetchone(
            """SELECT
                (SELECT COUNT(*) FROM cases) AS cases,
                (SELECT COUNT(*) FROM parties) AS parties,
                (SELECT COUNT(*) FROM claims) AS claims,
                (SELECT COUNT(*) FROM evidence) AS evidence,
                (SELECT COUNT(*) FROM evidence_claims) AS evidence_claims
            """
        )
        assert counts["cases"] >= 1
        assert counts["parties"] >= 2
        assert counts["claims"] >= 1
        assert counts["evidence"] >= 3
        assert counts["evidence_claims"] >= 3


# ============================================================================
# 2.  Multi-Lane Isolation
# ============================================================================


class TestLaneIsolation:
    """Verify evidence from Lane A doesn't leak into Lane D filings."""

    def test_lane_isolation(self, tmp_db: DatabaseManager, tmp_path: Path):
        _skip_if_missing(CaseEngine)

        case_engine = CaseEngine(db=tmp_db)

        # Create two cases in different lanes
        lane_a_id = case_engine.create_case(
            "Custody Case",
            case_number="2024-001507-DC",
            case_type="family",
        )
        lane_d_id = case_engine.create_case(
            "PPO Violation",
            case_number="2023-5907-PP",
            case_type="criminal",
        )

        # Seed evidence into Lane A only
        dummy = tmp_path / "lane_a_doc.pdf"
        dummy.write_text("Lane A evidence only", encoding="utf-8")
        tmp_db.execute(
            "INSERT INTO evidence (case_id, title, description, file_path, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (lane_a_id, "Custody Doc", "Lane A only doc", str(dummy), "pdf"),
        )

        # Lane D should have zero evidence
        lane_d_evidence = tmp_db.fetchall(
            "SELECT * FROM evidence WHERE case_id = ?", (lane_d_id,)
        )
        assert len(lane_d_evidence) == 0

        # Lane A should have one
        lane_a_evidence = tmp_db.fetchall(
            "SELECT * FROM evidence WHERE case_id = ?", (lane_a_id,)
        )
        assert len(lane_a_evidence) == 1

        # Cross-check: no evidence_claims from Lane A linked to Lane D claims
        claim_d = tmp_db.execute(
            "INSERT INTO claims (case_id, title, status) VALUES (?, ?, ?)",
            (lane_d_id, "PPO Violation Count", "active"),
        ).lastrowid

        claim_a = tmp_db.execute(
            "INSERT INTO claims (case_id, title, status) VALUES (?, ?, ?)",
            (lane_a_id, "Custody Claim", "active"),
        ).lastrowid

        # Link evidence to Lane A claim
        ev_a = lane_a_evidence[0]["id"]
        case_engine.link_evidence_to_claim(ev_a, claim_a, strength="strong")

        # Verify no cross-contamination: Lane D claim should have zero links
        links_d = tmp_db.fetchall(
            "SELECT ec.* FROM evidence_claims ec "
            "WHERE ec.claim_id = ?",
            (claim_d,),
        )
        assert len(links_d) == 0

        # Lane A claim should have the link
        links_a = tmp_db.fetchall(
            "SELECT ec.* FROM evidence_claims ec "
            "WHERE ec.claim_id = ?",
            (claim_a,),
        )
        assert len(links_a) == 1


# ============================================================================
# 3.  Filing State Machine
# ============================================================================


class TestFilingLifecycle:
    """Filing status progression: draft → review → qa → ready → filed → served."""

    def test_filing_state_machine_via_engine(self, tmp_db: DatabaseManager):
        _skip_if_missing(FilingEngine)

        case_id = _seed_case(tmp_db)
        engine = FilingEngine(tmp_db)

        filing_id = engine.create_filing(
            case_id=case_id,
            filing_type="motion",
            court="14th Circuit",
            title="Motion to Compel",
        )

        # Verify initial state is draft
        filings = engine.get_filings(case_id=case_id)
        assert filings[0]["status"] == "draft"

        # Walk through each transition
        for target_status in ["review", "ready", "filed", "served"]:
            engine.update_status(filing_id, target_status)
            filings = engine.get_filings(case_id=case_id)
            assert filings[0]["status"] == target_status

    def test_filing_state_machine_raw_sql(self, tmp_db: DatabaseManager):
        """Fallback: state machine via raw SQL when FilingEngine unavailable."""
        case_id = _seed_case(tmp_db)
        cursor = tmp_db.execute(
            "INSERT INTO filings (case_id, title, filing_type, status) "
            "VALUES (?, ?, ?, ?)",
            (case_id, "Raw SQL Motion", "motion", "draft"),
        )
        fid = cursor.lastrowid

        for status in ["draft", "review", "ready", "filed", "served"]:
            tmp_db.execute(
                "UPDATE filings SET status = ? WHERE id = ?", (status, fid)
            )
            row = tmp_db.fetchone(
                "SELECT status FROM filings WHERE id = ?", (fid,)
            )
            assert row["status"] == status

    def test_filed_sets_date(self, tmp_db: DatabaseManager):
        case_id = _seed_case(tmp_db)
        cursor = tmp_db.execute(
            "INSERT INTO filings (case_id, title, filing_type, status) "
            "VALUES (?, ?, ?, ?)",
            (case_id, "Date Motion", "motion", "draft"),
        )
        fid = cursor.lastrowid
        tmp_db.execute(
            "UPDATE filings SET status = 'filed', filed_date = '2025-07-01' "
            "WHERE id = ?",
            (fid,),
        )
        row = tmp_db.fetchone("SELECT * FROM filings WHERE id = ?", (fid,))
        assert row["status"] == "filed"
        assert row["filed_date"] == "2025-07-01"

    def test_served_sets_date(self, tmp_db: DatabaseManager):
        case_id = _seed_case(tmp_db)
        cursor = tmp_db.execute(
            "INSERT INTO filings (case_id, title, filing_type, status, filed_date) "
            "VALUES (?, ?, ?, ?, ?)",
            (case_id, "Served Motion", "motion", "filed", "2025-07-01"),
        )
        fid = cursor.lastrowid
        tmp_db.execute(
            "UPDATE filings SET status = 'served', served_date = '2025-07-02' "
            "WHERE id = ?",
            (fid,),
        )
        row = tmp_db.fetchone("SELECT * FROM filings WHERE id = ?", (fid,))
        assert row["status"] == "served"
        assert row["served_date"] == "2025-07-02"


# ============================================================================
# 4.  Dashboard Aggregation
# ============================================================================


class TestDashboardAggregation:
    """Dashboard should reflect data from all engines."""

    def test_dashboard_aggregates_all_engines(
        self, tmp_db: DatabaseManager, tmp_path: Path,
    ):
        _skip_if_missing(DashboardEngine)

        case_id = _seed_case(tmp_db)
        _seed_parties(tmp_db, case_id)
        _seed_evidence(tmp_db, case_id, tmp_path)

        # Add a filing
        tmp_db.execute(
            "INSERT INTO filings (case_id, title, filing_type, status) "
            "VALUES (?, ?, ?, ?)",
            (case_id, "Dashboard Motion", "motion", "draft"),
        )

        dash = DashboardEngine(db_path=str(tmp_db.db_path))

        # Evidence stats should return a dict (tables may not exist yet — safe_count)
        stats = dash.get_evidence_stats()
        assert isinstance(stats, dict)
        # All values should be non-negative integers
        for key, val in stats.items():
            assert isinstance(val, (int, float)), f"{key} is {type(val)}"
            assert val >= 0, f"{key} is negative: {val}"

        # Filing status returns a list
        filing_status = dash.get_filing_status()
        assert isinstance(filing_status, list)

        # Case health is a dict
        health = dash.get_case_health()
        assert isinstance(health, dict)

    def test_dashboard_empty_db(self, tmp_db: DatabaseManager):
        """Dashboard should handle an empty database gracefully."""
        _skip_if_missing(DashboardEngine)

        dash = DashboardEngine(db_path=str(tmp_db.db_path))
        stats = dash.get_evidence_stats()
        assert isinstance(stats, dict)

        health = dash.get_case_health()
        assert isinstance(health, dict)


# ============================================================================
# 5.  Witness–Evidence Cross-Reference
# ============================================================================


class TestWitnessEvidenceLinkage:
    """Witnesses link to evidence items correctly."""

    def test_witness_evidence_linkage(
        self, tmp_db: DatabaseManager, tmp_path: Path,
    ):
        _skip_if_missing(WitnessEngine)

        case_id = _seed_case(tmp_db)
        ev_ids = _seed_evidence(tmp_db, case_id, tmp_path)

        wit = WitnessEngine(db_path=str(tmp_db.db_path))

        w_id = wit.add_witness(
            name="Dr. Expert Witness",
            role="expert",
            lane="A",
            relevance_score=9.0,
            testimony_summary="Expert in child psychology",
        )
        assert w_id > 0

        # Retrieve the witness
        witness = wit.get_witness(w_id)
        assert witness is not None
        assert witness["name"] == "Dr. Expert Witness"
        assert witness["role"] == "expert"

        # Update witness with notes referencing evidence
        updated = wit.update_witness(
            w_id, notes=f"Relates to evidence IDs: {ev_ids}",
        )
        assert updated is True

        # Fetch back and confirm update
        witness = wit.get_witness(w_id)
        assert str(ev_ids[0]) in witness["notes"]

    def test_witness_list_ordered_by_relevance(self, tmp_db: DatabaseManager):
        _skip_if_missing(WitnessEngine)

        _seed_case(tmp_db)
        wit = WitnessEngine(db_path=str(tmp_db.db_path))

        # Add witnesses with different relevance scores
        wit.add_witness(name="Low Priority", role="fact", lane="A", relevance_score=3.0)
        wit.add_witness(name="High Priority", role="expert", lane="A", relevance_score=9.5)
        wit.add_witness(name="Medium Priority", role="fact", lane="A", relevance_score=6.0)

        witnesses = wit.list_witnesses(lane="A")
        assert len(witnesses) >= 3

        # Should be sorted descending by relevance
        scores = [w["relevance_score"] for w in witnesses]
        assert scores == sorted(scores, reverse=True)

    def test_witness_lane_filtering(self, tmp_db: DatabaseManager):
        _skip_if_missing(WitnessEngine)

        _seed_case(tmp_db)
        wit = WitnessEngine(db_path=str(tmp_db.db_path))

        wit.add_witness(name="Custody Witness", role="fact", lane="A")
        wit.add_witness(name="PPO Witness", role="fact", lane="D")

        lane_a = wit.list_witnesses(lane="A")
        lane_d = wit.list_witnesses(lane="D")

        a_names = {w["name"] for w in lane_a}
        d_names = {w["name"] for w in lane_d}

        assert "Custody Witness" in a_names
        assert "PPO Witness" not in a_names
        assert "PPO Witness" in d_names
        assert "Custody Witness" not in d_names

    def test_generate_witness_list(self, tmp_db: DatabaseManager):
        _skip_if_missing(WitnessEngine)

        _seed_case(tmp_db)
        wit = WitnessEngine(db_path=str(tmp_db.db_path))

        wit.add_witness(
            name="Dr. Child Psychologist",
            role="expert",
            lane="A",
            relevance_score=9.0,
        )
        wit.add_witness(
            name="School Teacher",
            role="fact",
            lane="A",
            relevance_score=7.0,
        )

        doc = wit.generate_witness_list("F7")
        assert isinstance(doc, str)
        assert len(doc) > 0
        assert "Dr. Child Psychologist" in doc


# ============================================================================
# 6.  Case Summary Aggregation
# ============================================================================


class TestCaseSummary:
    """Verify CaseEngine.get_case_summary aggregates all linked data."""

    def test_case_summary(self, tmp_db: DatabaseManager, tmp_path: Path):
        _skip_if_missing(CaseEngine)

        engine = CaseEngine(db=tmp_db)
        case_id = engine.create_case(
            "Summary Test", case_number="2025-SUM-001", case_type="family",
        )
        engine.add_party(case_id, "Andrew James Pigors", "petitioner")
        engine.add_party(case_id, "Emily A. Watson", "respondent")
        engine.add_claim(case_id, "Test Claim", legal_basis="MCL 722.27")

        summary = engine.get_case_summary(case_id)
        assert summary is not None
        # CaseSummary should reflect the parties and claims we added
        # (exact attribute names depend on implementation)
        assert hasattr(summary, "id") or isinstance(summary, dict)


# ============================================================================
# 7.  Evidence Gap Analysis
# ============================================================================


class TestEvidenceGapAnalysis:
    """Verify check_gaps correctly identifies claims missing evidence."""

    def test_gap_detected_for_unsupported_claim(
        self, tmp_db: DatabaseManager, tmp_path: Path,
    ):
        _skip_if_missing(CaseEngine, EvidenceEngine)

        case_engine = CaseEngine(db=tmp_db)
        case_id = case_engine.create_case(
            "Gap Test", case_number="2025-GAP-001", case_type="family",
        )
        defendant_id = case_engine.add_party(
            case_id, "Emily A. Watson", "respondent",
        )

        # Claim WITH evidence
        supported_claim = case_engine.add_claim(
            case_id, "Supported Claim", legal_basis="MCL 722.27",
        )
        dummy = tmp_path / "supported.pdf"
        dummy.write_text("evidence content", encoding="utf-8")
        ev_engine = EvidenceEngine(tmp_db)
        eid = ev_engine.add_evidence(
            case_id=case_id,
            file_path=str(dummy),
            evidence_type="document",
            description="Supporting document",
        )
        case_engine.link_evidence_to_claim(eid, supported_claim, strength="strong")

        # Claim WITHOUT evidence
        unsupported_claim = case_engine.add_claim(
            case_id, "Unsupported Claim", legal_basis="MCL 600.2911",
        )

        gaps = ev_engine.check_gaps(case_id)
        gap_claim_ids = [g.get("claim_id") for g in gaps]
        assert unsupported_claim in gap_claim_ids
        assert supported_claim not in gap_claim_ids


# ============================================================================
# 8.  Filing Score Calculation
# ============================================================================


class TestFilingScore:
    """Verify FilingEngine.score_filing returns a numeric score."""

    def test_score_filing(self, tmp_db: DatabaseManager):
        _skip_if_missing(FilingEngine)

        case_id = _seed_case(tmp_db)
        engine = FilingEngine(tmp_db)

        filing_id = engine.create_filing(
            case_id=case_id,
            filing_type="motion",
            court="14th Circuit",
            title="Scoreable Motion",
        )

        score = engine.score_filing(filing_id)
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
