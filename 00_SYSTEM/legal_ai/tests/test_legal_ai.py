"""Tests for legal_ai package — citation_extractor, entity_extractor, statute_parser.

Run from 00_SYSTEM/:
    python -m pytest legal_ai/tests/test_legal_ai.py -v --tb=short
"""

import pytest
import os
import sys

# Ensure we don't run from repo root (shadow modules)
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", ".."))


# ══════════════════════════════════════════════════════════════════
# Citation Extractor Tests
# ══════════════════════════════════════════════════════════════════

class TestCitationExtractor:

    def _get_extractor(self):
        from legal_ai.citation_extractor import CitationExtractor
        return CitationExtractor(validate_against_db=False, use_eyecite=False)

    def test_extract_mcr(self):
        cx = self._get_extractor()
        result = cx.extract("MCR 2.003 requires judicial disqualification")
        assert result.total_found >= 1
        rules = [c for c in result.citations if c.reporter == "MCR"]
        assert len(rules) >= 1
        assert rules[0].canonical == "MCR 2.003"
        assert rules[0].citation_type == "rule"
        assert rules[0].jurisdiction == "michigan"

    def test_extract_mcl(self):
        cx = self._get_extractor()
        result = cx.extract("Under MCL 722.23, the best interest factors include")
        statutes = [c for c in result.citations if c.reporter == "MCL"]
        assert len(statutes) >= 1
        assert statutes[0].canonical == "MCL 722.23"

    def test_extract_mre(self):
        cx = self._get_extractor()
        result = cx.extract("MRE 801 defines hearsay")
        rules = [c for c in result.citations if c.reporter == "MRE"]
        assert len(rules) >= 1
        assert rules[0].canonical == "MRE 801"

    def test_extract_michigan_case(self):
        cx = self._get_extractor()
        result = cx.extract("In Vodvarka v Grasmeyer, 259 Mich App 499")
        cases = [c for c in result.citations if c.citation_type == "case"]
        assert len(cases) >= 1
        assert any("259" in c.volume for c in cases)

    def test_extract_federal_case(self):
        cx = self._get_extractor()
        result = cx.extract("Troxel v. Granville, 530 US 57 (2000)")
        cases = [c for c in result.citations if c.reporter == "US"]
        assert len(cases) >= 1

    def test_extract_usc(self):
        cx = self._get_extractor()
        result = cx.extract("Under 42 USC 1983, state actors who deprive")
        statutes = [c for c in result.citations if c.citation_type == "statute"]
        assert len(statutes) >= 1

    def test_extract_multiple(self):
        cx = self._get_extractor()
        text = (
            "MCR 2.003(D)(1) mandates disqualification. "
            "See MCL 722.23 for best interest factors. "
            "Also 259 Mich App 499 and 530 US 57."
        )
        result = cx.extract(text)
        assert result.total_found >= 4
        assert len(result.unique_rules) >= 1
        assert len(result.unique_statutes) >= 1
        assert len(result.unique_cases) >= 2

    def test_hallucinated_citation_flagged(self):
        cx = self._get_extractor()
        result = cx.extract("McCraney v Ford Motor Co, 282 Mich App 647 (2009)")
        flagged = [c for c in result.citations if c.is_good_law is False]
        assert len(flagged) >= 1
        assert any("HALLUCINATED" in w for w in result.warnings)

    def test_deduplication(self):
        cx = self._get_extractor()
        result = cx.extract("MCR 2.003 and MCR 2.003 again")
        mcr_cites = [c for c in result.citations if c.canonical == "MCR 2.003"]
        assert len(mcr_cites) == 1

    def test_empty_text(self):
        cx = self._get_extractor()
        result = cx.extract("")
        assert result.total_found == 0

    def test_batch_extraction(self):
        cx = self._get_extractor()
        results = cx.extract_batch(
            ["MCR 2.003", "MCL 722.23", "no citations here"],
            labels=["doc_a", "doc_b", "doc_c"],
        )
        assert len(results) == 3
        assert results["doc_a"].total_found >= 1
        assert results["doc_c"].total_found == 0

    def test_stats(self):
        cx = self._get_extractor()
        stats = cx.get_stats()
        assert stats["version"] == "1.0.0"
        assert stats["michigan_patterns"] > 0
        assert stats["federal_patterns"] > 0


# ══════════════════════════════════════════════════════════════════
# Entity Extractor Tests
# ══════════════════════════════════════════════════════════════════

class TestEntityExtractor:

    def _get_extractor(self):
        from legal_ai.entity_extractor import EntityExtractor
        return EntityExtractor(use_spacy=False)

    def test_extract_known_judge(self):
        ex = self._get_extractor()
        result = ex.extract("Judge McNeill issued an ex parte order")
        judges = result.by_type.get("JUDGE", [])
        assert len(judges) >= 1
        assert any("McNeill" in j.normalized for j in judges)

    def test_extract_known_party(self):
        ex = self._get_extractor()
        result = ex.extract("Emily Watson filed a motion against Andrew Pigors")
        parties = result.by_type.get("PARTY", [])
        assert len(parties) >= 2
        names = [p.normalized for p in parties]
        assert "Emily A. Watson" in names
        assert "Andrew James Pigors" in names

    def test_extract_known_organization(self):
        ex = self._get_extractor()
        result = ex.extract("Shady Oaks park management violated MCL 125.2301")
        orgs = result.by_type.get("ORGANIZATION", [])
        assert len(orgs) >= 1
        assert any("Shady Oaks" in o.normalized for o in orgs)

    def test_extract_case_number(self):
        ex = self._get_extractor()
        result = ex.extract("Case No. 2024-001507-DC in the 14th Circuit")
        case_nums = result.by_type.get("CASE_NUMBER", [])
        assert len(case_nums) >= 1
        assert any("2024-001507-DC" in c.text for c in case_nums)

    def test_extract_date(self):
        ex = self._get_extractor()
        result = ex.extract("The hearing on March 15, 2026 was ex parte")
        dates = result.by_type.get("DATE", [])
        assert len(dates) >= 1
        assert any("March 15, 2026" in d.text for d in dates)

    def test_extract_amount(self):
        ex = self._get_extractor()
        result = ex.extract("Damages of $2,500,000.00 are sought")
        amounts = result.by_type.get("AMOUNT", [])
        assert len(amounts) >= 1
        assert any("$2,500,000.00" in a.text for a in amounts)

    def test_extract_case_name(self):
        ex = self._get_extractor()
        result = ex.extract("In Vodvarka v. Grasmeyer, the court held")
        case_names = result.by_type.get("CASE_NAME", [])
        assert len(case_names) >= 1

    def test_multiple_entity_types(self):
        ex = self._get_extractor()
        text = (
            "Judge McNeill denied Andrew Pigors' motion in "
            "Case No. 2024-001507-DC on March 15, 2026. "
            "Emily Watson and Shady Oaks sought $50,000 in damages."
        )
        result = ex.extract(text)
        assert result.total_found >= 5
        assert "JUDGE" in result.by_type
        assert "PARTY" in result.by_type

    def test_empty_text(self):
        ex = self._get_extractor()
        result = ex.extract("")
        assert result.total_found == 0

    def test_stats(self):
        ex = self._get_extractor()
        stats = ex.get_stats()
        assert stats["version"] == "1.0.0"
        assert stats["known_judges"] > 0
        assert stats["known_parties"] > 0


# ══════════════════════════════════════════════════════════════════
# Statute Parser Tests
# ══════════════════════════════════════════════════════════════════

class TestStatuteParser:

    def _get_parser(self):
        from legal_ai.statute_parser import StatuteParser
        return StatuteParser(enrich_from_db=False)

    def test_parse_mcl(self):
        sp = self._get_parser()
        result = sp.parse("MCL 722.23 defines the best interest factors")
        assert len(result.statutes) >= 1
        ref = result.statutes[0]
        assert ref.system == "MCL"
        assert ref.full_number == "722.23"
        assert ref.chapter == 722
        assert ref.topic == "Child Custody"
        assert "A" in ref.applicable_lanes

    def test_parse_mcr(self):
        sp = self._get_parser()
        result = sp.parse("MCR 2.003(D)(1) requires disqualification")
        assert len(result.rules) >= 1
        ref = result.rules[0]
        assert ref.system == "MCR"
        assert ref.full_number == "2.003"
        assert ref.topic == "Disqualification of Judge"
        assert "E" in ref.applicable_lanes

    def test_parse_mre(self):
        sp = self._get_parser()
        result = sp.parse("MRE 801 defines hearsay statements")
        assert len(result.evidence_rules) >= 1
        ref = result.evidence_rules[0]
        assert ref.system == "MRE"
        assert ref.full_number == "801"

    def test_parse_usc_1983(self):
        sp = self._get_parser()
        result = sp.parse("42 USC 1983 provides a cause of action")
        assert len(result.federal) >= 1
        ref = result.federal[0]
        assert ref.system == "USC"
        assert ref.title == "Civil Rights Act — Section 1983"

    def test_parse_multiple_systems(self):
        sp = self._get_parser()
        text = (
            "MCR 2.003 and MCL 722.23 together with 42 USC 1983 "
            "and MRE 801 establish the framework."
        )
        result = sp.parse(text)
        assert result.total_found >= 4
        assert len(result.rules) >= 1
        assert len(result.statutes) >= 1
        assert len(result.federal) >= 1
        assert len(result.evidence_rules) >= 1

    def test_parse_mcl_with_subsection(self):
        sp = self._get_parser()
        result = sp.parse("MCL 600.2919a(2) provides for treble damages")
        assert len(result.statutes) >= 1
        ref = result.statutes[0]
        assert ref.full_number == "600.2919a"
        assert ref.subsection == "(2)"
        assert "B" in ref.applicable_lanes

    def test_lane_statutes(self):
        sp = self._get_parser()
        lane_a = sp.get_lane_statutes("A")
        assert len(lane_a["MCL"]) > 0
        assert any("722.23" in s for s in lane_a["MCL"])
        lane_b = sp.get_lane_statutes("B")
        assert len(lane_b["MCL"]) > 0

    def test_empty_text(self):
        sp = self._get_parser()
        result = sp.parse("")
        assert result.total_found == 0

    def test_no_false_positives(self):
        sp = self._get_parser()
        result = sp.parse("The weather was nice on Tuesday. No legal content here.")
        assert result.total_found == 0

    def test_stats(self):
        sp = self._get_parser()
        stats = sp.get_stats()
        assert stats["version"] == "1.0.0"
        assert stats["mcl_chapters_known"] > 0
        assert stats["mcr_rules_known"] > 0
