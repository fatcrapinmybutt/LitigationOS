"""
Test the Chronological Narrative Engine end-to-end.
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(str(Path(__file__).resolve().parents[3]), "00_SYSTEM", "engines"))

from narrative import NarrativeBuilder, NarrativeFormatter, NarrativeEvent, SeverityLevel

DB = str(Path(__file__).resolve().parents[3] / "litigation_context.db")


def test_severity_levels():
    print("=== SeverityLevel.at_least ===")
    assert SeverityLevel.at_least("critical") == ["critical"], f"Got {SeverityLevel.at_least('critical')}"
    assert SeverityLevel.at_least("high") == ["critical", "high"]
    assert SeverityLevel.at_least("medium") == ["critical", "high", "medium"]
    assert SeverityLevel.at_least("low") == ["critical", "high", "medium", "low"]
    print("  PASS: All severity level filters correct")


def test_narrative_event_model():
    print("\n=== NarrativeEvent model ===")
    ev = NarrativeEvent(
        event_date="2025-07-29",
        event_summary="Test event",
        claim_elements=["MCL 722.23(j)"],
        actors=["Emily Watson"],
        severity="critical",
    )
    tup = ev.to_insert_tuple()
    assert len(tup) == 13, f"Expected 13-tuple, got {len(tup)}"
    assert tup[0] == "2025-07-29"
    assert '"MCL 722.23(j)"' in tup[4]
    print("  PASS: Model serialization correct")

    sep = NarrativeEvent.separation_days()
    assert sep > 0, f"Separation days should be positive, got {sep}"
    print(f"  PASS: Separation counter = {sep} days")

    dt = ev.date_obj()
    assert dt is not None
    assert dt.year == 2025 and dt.month == 7 and dt.day == 29
    print("  PASS: date_obj() parsing correct")


def test_builder_statement_of_facts():
    print("\n=== NarrativeBuilder.build_statement_of_facts ===")
    builder = NarrativeBuilder(DB)

    # Full statement
    sof = builder.build_statement_of_facts()
    assert "STATEMENT OF FACTS" in sof
    assert "L.D.W." in sof
    assert "separated" in sof.lower() or "separation" in sof.lower()
    lines = [l for l in sof.split("\n") if l.strip().startswith(("1.", "2.", "3."))]
    assert len(lines) >= 3, f"Expected at least 3 numbered paragraphs, got {len(lines)}"
    print(f"  PASS: Full SOF generated ({len(sof)} chars, {len(lines)} paragraphs)")

    # Lane A only
    sof_a = builder.build_statement_of_facts(lane="A")
    assert "STATEMENT OF FACTS" in sof_a
    print(f"  PASS: Lane A SOF generated ({len(sof_a)} chars)")

    # Critical only
    sof_crit = builder.build_statement_of_facts(severity_min="critical")
    assert len(sof_crit) < len(sof)  # Should be shorter
    print(f"  PASS: Critical-only SOF generated ({len(sof_crit)} chars)")

    # Date range
    sof_range = builder.build_statement_of_facts(date_from="2025-01-01", date_to="2025-12-31")
    assert "STATEMENT OF FACTS" in sof_range
    print(f"  PASS: Date-range SOF generated ({len(sof_range)} chars)")


def test_builder_claim_narrative():
    print("\n=== NarrativeBuilder.build_claim_narrative ===")
    builder = NarrativeBuilder(DB)

    claim = builder.build_claim_narrative("MCL 722.23(j)")
    assert "MCL 722.23(j)" in claim
    assert len(claim) > 100
    print(f"  PASS: Factor j narrative generated ({len(claim)} chars)")

    claim2 = builder.build_claim_narrative("42 USC")
    assert "42 USC" in claim2
    print(f"  PASS: § 1983 narrative generated ({len(claim2)} chars)")


def test_builder_defendant_narrative():
    print("\n=== NarrativeBuilder.build_defendant_narrative ===")
    builder = NarrativeBuilder(DB)

    dn = builder.build_defendant_narrative("Emily Watson")
    assert "EMILY WATSON" in dn
    assert len(dn) > 200
    print(f"  PASS: Emily Watson narrative generated ({len(dn)} chars)")

    dn2 = builder.build_defendant_narrative("McNeill")
    assert "MCNEILL" in dn2
    print(f"  PASS: Judge McNeill narrative generated ({len(dn2)} chars)")


def test_builder_separation_counter():
    print("\n=== NarrativeBuilder.get_separation_counter ===")
    builder = NarrativeBuilder(DB)
    days = builder.get_separation_counter()
    assert days > 200, f"Expected > 200 days, got {days}"
    print(f"  PASS: Separation counter = {days} days")


def test_builder_exhibit_list():
    print("\n=== NarrativeBuilder.generate_exhibit_list ===")
    builder = NarrativeBuilder(DB)
    exhibits = builder.generate_exhibit_list()
    assert len(exhibits) > 5
    assert all("label" in e and "description" in e for e in exhibits)
    print(f"  PASS: {len(exhibits)} exhibits generated")
    for ex in exhibits[:5]:
        print(f"    {ex['label']}: {ex['description'][:60]}")


def test_builder_event_count():
    print("\n=== NarrativeBuilder.get_event_count ===")
    builder = NarrativeBuilder(DB)
    total = builder.get_event_count()
    assert total >= 50, f"Expected >= 50, got {total}"
    print(f"  PASS: Total events = {total}")

    lane_a = builder.get_event_count(lane="A")
    assert lane_a > 0
    print(f"  PASS: Lane A events = {lane_a}")


def test_formatter_circuit_court():
    print("\n=== NarrativeFormatter.format_circuit_court ===")
    builder = NarrativeBuilder(DB)
    formatter = NarrativeFormatter()

    events = builder._query_events(severity_min="critical")
    output = formatter.format_circuit_court(events)
    assert "STATEMENT OF FACTS" in output
    assert "L.D.W." in output
    # Check no child full name
    assert "Liam" not in output
    assert "undersigned counsel" not in output
    print(f"  PASS: Circuit court format ({len(output)} chars)")


def test_formatter_appellate():
    print("\n=== NarrativeFormatter.format_appellate ===")
    builder = NarrativeBuilder(DB)
    formatter = NarrativeFormatter()

    events = builder._query_events(severity_min="critical")
    output = formatter.format_appellate(events)
    assert "STATEMENT OF FACTS" in output
    assert "Appellant" in output or "Record" in output
    print(f"  PASS: Appellate format ({len(output)} chars)")


def test_formatter_federal():
    print("\n=== NarrativeFormatter.format_federal ===")
    builder = NarrativeBuilder(DB)
    formatter = NarrativeFormatter()

    events = builder._query_events(lane="C")
    output = formatter.format_federal(events)
    assert "FACTUAL ALLEGATIONS" in output
    assert "Fourteenth Amendment" in output
    print(f"  PASS: Federal format ({len(output)} chars)")


def test_formatter_emergency():
    print("\n=== NarrativeFormatter.format_emergency ===")
    builder = NarrativeBuilder(DB)
    formatter = NarrativeFormatter()

    events = builder._query_events(severity_min="critical")
    output = formatter.format_emergency(events)
    assert "VERIFIED STATEMENT OF FACTS" in output
    assert "EMERGENCY" in output
    assert "pro se" in output
    assert "L.D.W." in output
    assert "consecutive days" in output
    print(f"  PASS: Emergency format ({len(output)} chars)")


def test_link_evidence():
    print("\n=== NarrativeBuilder.link_evidence_to_timeline ===")
    builder = NarrativeBuilder(DB)
    updated = builder.link_evidence_to_timeline()
    print(f"  PASS: Updated evidence links for {updated} events")


def main():
    print("=" * 60)
    print("CHRONOLOGICAL NARRATIVE ENGINE — TEST SUITE")
    print("=" * 60)

    test_severity_levels()
    test_narrative_event_model()
    test_builder_event_count()
    test_builder_statement_of_facts()
    test_builder_claim_narrative()
    test_builder_defendant_narrative()
    test_builder_separation_counter()
    test_builder_exhibit_list()
    test_formatter_circuit_court()
    test_formatter_appellate()
    test_formatter_federal()
    test_formatter_emergency()
    test_link_evidence()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
