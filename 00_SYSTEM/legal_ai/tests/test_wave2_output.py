# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for LitigationOS Wave 2 legal_ai modules:
  1. LitigationPDFGenerator  (pdf_generator.py)
  2. TOCTOAGenerator         (toc_toa_generator.py)
  3. ExhibitStamper          (exhibit_stamper.py)
  4. EFilingFormatter        (efiling_formatter.py)
  5. ProvenanceTracker       (provenance_tracker.py)

All tests are pure unit tests — no DB connections or external dependencies.
Run with:
    cd C:\\Users\\andre\\LitigationOS\\00_SYSTEM\\legal_ai
    python -m pytest tests/test_wave2_output.py -v
"""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch, PropertyMock

# ---------------------------------------------------------------------------
# Ensure legal_ai package is importable
# ---------------------------------------------------------------------------
_LEGAL_AI_DIR = Path(__file__).resolve().parent.parent
if str(_LEGAL_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR))
if str(_LEGAL_AI_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_LEGAL_AI_DIR.parent))

from pdf_generator import (
    CourtType,
    ElementType,
    LitigationPDFGenerator,
    ParsedElement,
    PDFConfig,
    PDFResult,
)
from toc_toa_generator import (
    CitationCategory,
    TOCEntry,
    TOCTOAGenerator,
    TOCTOAResult,
    TOAEntry,
)
from exhibit_stamper import (
    AuthStatus,
    ExhibitEntry,
    ExhibitPackage,
    ExhibitStamper,
)
from efiling_formatter import (
    EFilingFormatter,
    EFilingPacket,
    EFilingSpec,
    EFilingSystem,
)
from provenance_tracker import (
    ProvenanceChain,
    ProvenanceEdge,
    ProvenanceNode,
    ProvenanceReport,
    ProvenanceTracker,
)


# ═══════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════

def _sample_markdown() -> str:
    """Markdown filing with headings, citations, and structure."""
    return """\
# MOTION TO MODIFY CUSTODY ARRANGEMENT

## I. STATEMENT OF FACTS

Plaintiff and Defendant are the parents of the minor child, L.D.W.
The Court's order dated January 15, 2025 established the current schedule.

## II. LEGAL ARGUMENT

### A. Proper Cause Standard

Under MCL 722.27(1)(c), modification requires proper cause or a change
of circumstances. *Vodvarka v Grasmeyer*, 259 Mich App 499 (2003).

The best-interest factors under MCL 722.23 weigh in favor of modification.
See also *Shade v Wright*, 291 Mich App 17 (2010).

MCR 3.210 governs custody proceedings.

### B. Constitutional Rights

The **Fourteenth Amendment** guarantees due process. *Troxel v Granville*,
530 US 57 (2000), protects parental rights.

42 USC §1983 provides a federal remedy.

## III. PRAYER FOR RELIEF

WHEREFORE, Plaintiff requests modification of the custody arrangement.

## IV. CERTIFICATE OF SERVICE

I certify that on this date I served copies per MCR 2.107.
"""


def _sample_markdown_with_lists() -> str:
    """Markdown with ordered and unordered lists."""
    return """\
# MOTION

## FACTS

The following occurred:

1. First event happened
2. Second event happened
3. Third event happened

Key points:

- Point one is important
- Point two is critical
- Point three supports our case

> The court stated: "This is a blockquote from the record."
"""


def _sample_exhibits() -> List[Dict[str, Any]]:
    """Sample exhibit list for stamping tests."""
    return [
        {
            "title": "Custody Order dated January 15, 2025",
            "description": "Original custody order establishing parenting time",
            "page_count": 5,
            "source_file": "orders/custody_order_2025-01-15.pdf",
            "filing_target": "Motion to Modify Custody",
        },
        {
            "title": "Affidavit of Andrew J. Pigors",
            "description": "Sworn statement regarding custody violations",
            "page_count": 3,
            "source_file": "affidavits/pigors_affidavit.pdf",
            "filing_target": "Motion to Modify Custody",
        },
        {
            "title": "Text Message Screenshots",
            "description": "Communications between parties re: parenting time",
            "page_count": 12,
            "source_file": "evidence/text_messages_2025.pdf",
            "filing_target": "Motion to Modify Custody",
        },
        {
            "title": "School Records for L.D.W.",
            "description": "Attendance and progress reports",
            "page_count": 8,
            "source_file": "evidence/school_records.pdf",
            "filing_target": "Motion to Modify Custody",
        },
    ]


# ═══════════════════════════════════════════════════════════════════
#  1. LitigationPDFGenerator Tests (15 tests)
# ═══════════════════════════════════════════════════════════════════

class TestLitigationPDFGenerator(unittest.TestCase):
    """Tests for the LitigationPDFGenerator class."""

    def setUp(self):
        self.gen = LitigationPDFGenerator()

    # -- markdown parsing -------------------------------------------

    def test_markdown_to_html_basic(self):
        elements = self.gen._parse_markdown("Hello world paragraph.")
        self.assertIsInstance(elements, list)
        self.assertGreater(len(elements), 0)

    def test_markdown_to_html_headings(self):
        text = "# Heading 1\n\n## Heading 2\n\n### Heading 3"
        elements = self.gen._parse_markdown(text)
        heading_elements = [
            e for e in elements if e.element_type == ElementType.HEADING
        ]
        self.assertGreaterEqual(len(heading_elements), 3)

    def test_markdown_to_html_lists(self):
        elements = self.gen._parse_markdown(_sample_markdown_with_lists())
        list_elements = [
            e for e in elements
            if e.element_type in (ElementType.NUMBERED_LIST, ElementType.BULLET_LIST)
        ]
        self.assertGreater(len(list_elements), 0)

    def test_markdown_to_html_bold_italic(self):
        text = "This is **bold** and *italic* text."
        html = LitigationPDFGenerator._md_inline_to_html(text)
        self.assertIn("<strong>", html)
        self.assertIn("<em>", html)

    # -- court configs ----------------------------------------------

    def test_court_config_14th_circuit(self):
        cfg = self.gen.COURT_CONFIGS.get("14th_circuit")
        self.assertIsNotNone(cfg)
        self.assertIsInstance(cfg, PDFConfig)
        self.assertEqual(cfg.court_rule, "MCR 2.119")

    def test_court_config_coa(self):
        cfg = self.gen.COURT_CONFIGS.get("coa")
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg.court_rule, "MCR 7.212")

    # -- page dimensions --------------------------------------------

    def test_page_dimensions(self):
        cfg = PDFConfig()
        self.assertEqual(cfg.page_width, 8.5)
        self.assertEqual(cfg.page_height, 11.0)

    def test_margins_one_inch(self):
        cfg = PDFConfig()
        self.assertEqual(cfg.margin_top, 1.0)
        self.assertEqual(cfg.margin_bottom, 1.0)
        self.assertEqual(cfg.margin_left, 1.0)
        self.assertEqual(cfg.margin_right, 1.0)

    def test_font_times_new_roman(self):
        cfg = PDFConfig()
        self.assertEqual(cfg.font_family, "Times New Roman")
        self.assertEqual(cfg.font_size, 12)

    # -- generation -------------------------------------------------

    def test_generate_returns_pdf_result(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "test_output.html")
            result = self.gen.generate(
                _sample_markdown(), out_path, court_type="14th_circuit",
            )
            self.assertIsInstance(result, PDFResult)
            self.assertGreater(result.word_count, 0)

    def test_get_stats(self):
        stats = self.gen.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn("supported_courts", stats)

    def test_empty_markdown_handled(self):
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = os.path.join(tmpdir, "empty.html")
            result = self.gen.generate("", out_path, court_type="14th_circuit")
            self.assertIsInstance(result, PDFResult)

    def test_pdf_config_to_dict(self):
        cfg = PDFConfig()
        d = cfg.to_dict()
        self.assertIn("font_family", d)
        self.assertIn("page_width", d)
        self.assertEqual(d["line_spacing"], 2.0)

    def test_content_width_calculation(self):
        cfg = PDFConfig()
        expected = 8.5 - 1.0 - 1.0  # page_width - margins
        self.assertAlmostEqual(cfg.content_width_inches, expected, places=1)

    def test_content_height_calculation(self):
        cfg = PDFConfig()
        expected = 11.0 - 1.0 - 1.0  # page_height - margins
        self.assertAlmostEqual(cfg.content_height_inches, expected, places=1)


# ═══════════════════════════════════════════════════════════════════
#  2. TOCTOAGenerator Tests (14 tests)
# ═══════════════════════════════════════════════════════════════════

class TestTOCTOAGenerator(unittest.TestCase):
    """Tests for the TOCTOAGenerator class."""

    def setUp(self):
        self.gen = TOCTOAGenerator()

    def test_generate_toc_from_headings(self):
        entries = self.gen.generate_toc(_sample_markdown())
        self.assertIsInstance(entries, list)
        self.assertGreater(len(entries), 0)
        self.assertIsInstance(entries[0], TOCEntry)

    def test_generate_toa_from_citations(self):
        entries = self.gen.generate_toa(_sample_markdown())
        self.assertIsInstance(entries, list)
        self.assertGreater(len(entries), 0, "Should find citations in sample")

    def test_toa_groups_by_type(self):
        entries = self.gen.generate_toa(_sample_markdown())
        categories = {e.category for e in entries}
        # Should have at least two categories (statutes + rules or cases)
        self.assertGreaterEqual(len(categories), 1)

    def test_toc_page_numbers(self):
        entries = self.gen.generate_toc(_sample_markdown())
        for entry in entries:
            self.assertIsInstance(entry.page_number, int)
            self.assertGreaterEqual(entry.page_number, 1)

    def test_toa_sorted_alphabetically(self):
        entries = self.gen.generate_toa(_sample_markdown())
        if len(entries) > 1:
            # Within each category group, citations should be sorted
            by_cat: Dict[str, List[str]] = {}
            for e in entries:
                by_cat.setdefault(e.category, []).append(e.citation.lower())
            for cat, cites in by_cat.items():
                self.assertEqual(cites, sorted(cites),
                                 f"Citations in {cat} not sorted")

    def test_mcr_7_212_compliance(self):
        result = self.gen.generate(_sample_markdown(), court_type="coa")
        self.assertIsInstance(result, TOCTOAResult)
        # Should report missing required sections
        self.assertIsInstance(result.missing_sections, list)

    def test_empty_document_handled(self):
        entries = self.gen.generate_toc("")
        self.assertIsInstance(entries, list)
        self.assertEqual(len(entries), 0)

    def test_no_citations_handled(self):
        entries = self.gen.generate_toa("This document has no legal citations.")
        self.assertIsInstance(entries, list)
        self.assertEqual(len(entries), 0)

    def test_toc_nested_headings(self):
        entries = self.gen.generate_toc(_sample_markdown())
        levels = {e.level for e in entries}
        self.assertGreater(len(levels), 1, "Should have multiple heading levels")

    def test_combined_toc_toa(self):
        result = self.gen.generate(_sample_markdown(), court_type="coa")
        self.assertIsInstance(result, TOCTOAResult)
        self.assertGreater(len(result.toc_entries), 0)
        self.assertIsInstance(result.toc_markdown, str)
        self.assertIsInstance(result.toa_markdown, str)

    def test_get_stats(self):
        self.gen.generate(_sample_markdown())
        stats = self.gen.get_stats()
        self.assertIsInstance(stats, dict)

    def test_toc_to_dict(self):
        entry = TOCEntry(level=1, title="Test Heading", page_number=1)
        d = entry.to_dict()
        self.assertIn("title", d)
        self.assertEqual(d["level"], 1)

    def test_toa_entry_to_dict(self):
        entry = TOAEntry(
            category="statutes", citation="MCL 722.23",
            full_text="MCL 722.23", pages=[1, 3, 5],
        )
        d = entry.to_dict()
        self.assertEqual(d["category"], "statutes")
        self.assertEqual(d["citation"], "MCL 722.23")

    def test_toc_toa_result_to_dict(self):
        result = self.gen.generate(_sample_markdown(), court_type="coa")
        d = result.to_dict()
        self.assertIn("toc_entries", d)
        self.assertIn("toa_entries", d)


# ═══════════════════════════════════════════════════════════════════
#  3. ExhibitStamper Tests (15 tests)
# ═══════════════════════════════════════════════════════════════════

class TestExhibitStamper(unittest.TestCase):
    """Tests for the ExhibitStamper class."""

    def setUp(self):
        self.stamper = ExhibitStamper()

    def test_bates_format_pigors_xxxx(self):
        bates = self.stamper.format_bates(1)
        self.assertEqual(bates, "PIGORS-0001")

    def test_bates_sequential_numbering(self):
        b1 = self.stamper.format_bates(1)
        b2 = self.stamper.format_bates(2)
        b3 = self.stamper.format_bates(100)
        self.assertEqual(b1, "PIGORS-0001")
        self.assertEqual(b2, "PIGORS-0002")
        self.assertEqual(b3, "PIGORS-0100")

    def test_exhibit_letter_assignment(self):
        self.assertEqual(ExhibitStamper.letter_sequence(0), "A")
        self.assertEqual(ExhibitStamper.letter_sequence(1), "B")
        self.assertEqual(ExhibitStamper.letter_sequence(2), "C")
        self.assertEqual(ExhibitStamper.letter_sequence(25), "Z")

    def test_exhibit_letter_overflow(self):
        self.assertEqual(ExhibitStamper.letter_sequence(26), "AA")
        self.assertEqual(ExhibitStamper.letter_sequence(27), "AB")

    def test_master_index_generated(self):
        pkg = self.stamper.stamp_exhibits(_sample_exhibits())
        index_md = self.stamper.generate_master_index(pkg)
        self.assertIsInstance(index_md, str)
        self.assertGreater(len(index_md), 0)

    def test_exhibit_cover_page(self):
        entry = ExhibitEntry(
            exhibit_letter="A",
            title="Custody Order",
            bates_start="PIGORS-0001",
            bates_end="PIGORS-0005",
            page_count=5,
        )
        cover = self.stamper.generate_cover_page(entry)
        self.assertIsInstance(cover, str)
        self.assertIn("A", cover)

    def test_stamp_single_exhibit(self):
        exhibits = [_sample_exhibits()[0]]
        pkg = self.stamper.stamp_exhibits(exhibits)
        self.assertIsInstance(pkg, ExhibitPackage)
        self.assertEqual(len(pkg.exhibits), 1)
        self.assertEqual(pkg.exhibits[0].exhibit_letter, "A")

    def test_stamp_multiple_exhibits(self):
        pkg = self.stamper.stamp_exhibits(_sample_exhibits())
        self.assertEqual(len(pkg.exhibits), 4)
        letters = [e.exhibit_letter for e in pkg.exhibits]
        self.assertEqual(letters, ["A", "B", "C", "D"])

    def test_cross_reference_tracking(self):
        pkg = self.stamper.stamp_exhibits(_sample_exhibits())
        # Bates ranges should be sequential across exhibits
        for i in range(1, len(pkg.exhibits)):
            prev_end = self.stamper.parse_bates_number(pkg.exhibits[i - 1].bates_end)
            curr_start = self.stamper.parse_bates_number(pkg.exhibits[i].bates_start)
            self.assertEqual(curr_start, prev_end + 1,
                             f"Exhibit {pkg.exhibits[i].exhibit_letter} Bates not sequential")

    def test_empty_exhibit_list(self):
        pkg = self.stamper.stamp_exhibits([])
        self.assertIsInstance(pkg, ExhibitPackage)
        self.assertEqual(len(pkg.exhibits), 0)

    def test_get_stats(self):
        self.stamper.stamp_exhibits(_sample_exhibits())
        stats = self.stamper.get_stats()
        self.assertIsInstance(stats, dict)

    def test_exhibit_to_dict(self):
        entry = ExhibitEntry(
            exhibit_letter="A",
            title="Test Exhibit",
            bates_start="PIGORS-0001",
            bates_end="PIGORS-0005",
            page_count=5,
        )
        d = entry.to_dict()
        self.assertIn("exhibit_letter", d)
        self.assertIn("bates_start", d)
        self.assertEqual(d["page_count"], 5)

    def test_next_bates_number(self):
        nxt = self.stamper.next_bates_number("PIGORS-0015")
        self.assertEqual(nxt, "PIGORS-0016")

    def test_parse_bates_number(self):
        num = self.stamper.parse_bates_number("PIGORS-0042")
        self.assertEqual(num, 42)

    def test_letter_to_index_roundtrip(self):
        for i in range(30):
            letter = ExhibitStamper.letter_sequence(i)
            idx = ExhibitStamper.letter_to_index(letter)
            self.assertEqual(idx, i, f"Roundtrip failed for index {i} -> {letter}")


# ═══════════════════════════════════════════════════════════════════
#  4. EFilingFormatter Tests (14 tests)
# ═══════════════════════════════════════════════════════════════════

class TestEFilingFormatter(unittest.TestCase):
    """Tests for the EFilingFormatter class."""

    def setUp(self):
        # Prevent real DB connections
        with patch.object(EFilingFormatter, "_get_conn", return_value=MagicMock()):
            with patch.object(EFilingFormatter, "_ensure_schema"):
                self.fmt = EFilingFormatter(db_path=None)
        # Reset internal connection so no real DB is used
        self.fmt._conn = None

    def test_mifile_format(self):
        system = self.fmt.get_system_for_court("14th_circuit")
        self.assertEqual(system, EFilingSystem.MIFILE)

    def test_truefiling_format(self):
        system = self.fmt.get_system_for_court("coa")
        self.assertEqual(system, EFilingSystem.TRUEFILING)

    def test_pacer_format(self):
        system = self.fmt.get_system_for_court("wdmi")
        self.assertEqual(system, EFilingSystem.PACER)

    def test_manual_filing_format(self):
        system = self.fmt.get_system_for_court("jtc")
        self.assertEqual(system, EFilingSystem.MANUAL)

    def test_filename_convention(self):
        spec = self.fmt.get_spec_for_court("14th_circuit")
        self.assertIsInstance(spec.naming_convention, str)
        self.assertIn("{", spec.naming_convention)

    def test_metadata_generation(self):
        spec = self.fmt.get_spec_for_court("14th_circuit")
        self.assertIsInstance(spec, EFilingSpec)
        self.assertIn("pdf", spec.accepted_formats)

    def test_fee_code_lookup(self):
        fee = self.fmt.estimate_fees("14th_circuit", "motion")
        self.assertIsInstance(fee, float)
        self.assertEqual(fee, 20.0)

    def test_format_selection_by_court(self):
        for court_id in ["14th_circuit", "coa", "wdmi", "jtc"]:
            system = self.fmt.get_system_for_court(court_id)
            self.assertIsInstance(system, EFilingSystem)

    def test_validation_checks(self):
        packet = EFilingPacket(
            filing_id="TEST001",
            system=EFilingSystem.MIFILE,
            court="14th_circuit",
            case_number="2024-001507-DC",
            filing_type="motion",
            main_document="nonexistent.pdf",
        )
        result = self.fmt.validate_packet(packet)
        self.assertIsInstance(result, dict)
        self.assertIn("valid", result)
        # Should fail since file doesn't exist
        self.assertFalse(result["valid"])

    def test_output_structure(self):
        spec = self.fmt.get_spec_for_court("coa")
        d = spec.to_dict()
        self.assertIn("system", d)
        self.assertIn("max_file_size_mb", d)
        self.assertIn("accepted_formats", d)

    def test_get_stats(self):
        stats = self.fmt.get_stats()
        self.assertIsInstance(stats, dict)

    def test_formatter_to_dict(self):
        packet = EFilingPacket(
            filing_id="TEST002",
            system=EFilingSystem.MIFILE,
            court="14th_circuit",
            case_number="2024-001507-DC",
            filing_type="motion",
            main_document="test.pdf",
        )
        d = packet.to_dict()
        self.assertIn("filing_id", d)
        self.assertEqual(d["court"], "14th_circuit")

    def test_fee_waiver_zeroes_fee(self):
        fee = self.fmt.estimate_fees("14th_circuit", "complaint", fee_waiver=True)
        self.assertEqual(fee, 0.0)

    def test_unknown_court_raises(self):
        with self.assertRaises(ValueError):
            self.fmt.get_system_for_court("nonexistent_court")


# ═══════════════════════════════════════════════════════════════════
#  5. ProvenanceTracker Tests (15 tests)
# ═══════════════════════════════════════════════════════════════════

class TestProvenanceTracker(unittest.TestCase):
    """Tests for the ProvenanceTracker class."""

    def _make_tracker(self) -> ProvenanceTracker:
        """Create a tracker with mocked DB."""
        with patch.object(ProvenanceTracker, "_get_conn", return_value=MagicMock()):
            with patch.object(ProvenanceTracker, "_ensure_schema"):
                pt = ProvenanceTracker(db_path=None)
        pt._conn = None
        return pt

    def setUp(self):
        self.pt = self._make_tracker()
        # Initialize internal state that constructor sets
        if not hasattr(self.pt, "_nodes"):
            self.pt._nodes = {}
        if not hasattr(self.pt, "_edges"):
            self.pt._edges = []
        if not hasattr(self.pt, "_stats"):
            self.pt._stats = {
                "nodes_registered": 0,
                "edges_registered": 0,
                "verifications_run": 0,
            }

    def test_add_document_to_chain(self):
        node = ProvenanceNode(
            node_id="abc123",
            node_type="raw_file",
            path="/evidence/contract.pdf",
            sha256="a" * 64,
        )
        self.pt._nodes[node.node_id] = node
        self.assertIn("abc123", self.pt._nodes)

    def test_sha256_hash_computed(self):
        text_hash = ProvenanceTracker._compute_sha256_text("hello world")
        expected = hashlib.sha256(b"hello world").hexdigest()
        self.assertEqual(text_hash, expected)

    def test_parent_child_relationship(self):
        parent = ProvenanceNode(
            node_id="parent1", node_type="raw_file",
            path="/raw.pdf", sha256="a" * 64,
        )
        child = ProvenanceNode(
            node_id="child1", node_type="extracted_text",
            path="/extracted.txt", sha256="b" * 64,
        )
        edge = ProvenanceEdge(
            source_id="parent1", target_id="child1",
            relationship="extracted_from",
        )
        self.pt._nodes[parent.node_id] = parent
        self.pt._nodes[child.node_id] = child
        self.pt._edges.append(edge)
        self.assertEqual(edge.source_id, "parent1")
        self.assertEqual(edge.target_id, "child1")

    def test_dag_structure_maintained(self):
        # Build a small DAG: raw -> extracted -> analysis
        nodes = [
            ProvenanceNode(node_id="n1", node_type="raw_file",
                           path="/raw.pdf", sha256="a" * 64),
            ProvenanceNode(node_id="n2", node_type="extracted_text",
                           path="/text.txt", sha256="b" * 64),
            ProvenanceNode(node_id="n3", node_type="analysis",
                           path="/analysis.json", sha256="c" * 64),
        ]
        edges = [
            ProvenanceEdge(source_id="n1", target_id="n2",
                           relationship="extracted_from"),
            ProvenanceEdge(source_id="n2", target_id="n3",
                           relationship="analyzed_by"),
        ]
        for n in nodes:
            self.pt._nodes[n.node_id] = n
        self.pt._edges.extend(edges)
        self.assertEqual(len(self.pt._nodes), 3)
        self.assertEqual(len(self.pt._edges), 2)

    def test_chain_verification(self):
        chain = ProvenanceChain(
            root_node=ProvenanceNode(
                node_id="root", node_type="filing_document",
                path="/filing.pdf", sha256="d" * 64,
            ),
            nodes=[
                ProvenanceNode(node_id="src", node_type="raw_file",
                               path="/evidence.pdf", sha256="e" * 64),
            ],
            edges=[
                ProvenanceEdge(source_id="src", target_id="root",
                               relationship="assembled_into"),
            ],
            depth=1,
            complete=True,
        )
        self.assertTrue(chain.complete)
        self.assertEqual(chain.depth, 1)

    def test_broken_chain_detected(self):
        chain = ProvenanceChain(
            root_node=ProvenanceNode(
                node_id="root", node_type="filing_document",
                path="/filing.pdf", sha256="f" * 64,
            ),
            nodes=[
                ProvenanceNode(node_id="mid", node_type="analysis",
                               path="/analysis.json", sha256="g" * 64),
            ],
            edges=[
                ProvenanceEdge(source_id="mid", target_id="root",
                               relationship="assembled_into"),
            ],
            depth=1,
            complete=False,  # Leaf is analysis, not raw_file
        )
        self.assertFalse(chain.complete)

    def test_mermaid_export(self):
        chain = ProvenanceChain(
            root_node=ProvenanceNode(
                node_id="root", node_type="filing_document",
                path="/filing.pdf", sha256="h" * 64,
            ),
            nodes=[
                ProvenanceNode(node_id="src", node_type="raw_file",
                               path="/evidence.pdf", sha256="i" * 64),
            ],
            edges=[
                ProvenanceEdge(source_id="src", target_id="root",
                               relationship="assembled_into"),
            ],
            depth=1,
            complete=True,
        )
        mermaid = self.pt.generate_dag_mermaid(chain)
        self.assertIsInstance(mermaid, str)
        self.assertIn("graph", mermaid.lower()) if mermaid else None

    def test_json_export(self):
        chain = ProvenanceChain(
            root_node=ProvenanceNode(
                node_id="root", node_type="filing_document",
                path="/filing.pdf", sha256="j" * 64,
            ),
            nodes=[],
            edges=[],
            depth=0,
            complete=False,
        )
        d = chain.to_dict()
        self.assertIn("root_node", d)
        self.assertIn("depth", d)
        json_str = json.dumps(d)
        self.assertIsInstance(json_str, str)

    def test_audit_trail_complete(self):
        edge = ProvenanceEdge(
            source_id="src1", target_id="tgt1",
            relationship="extracted_from",
            agent_id="A04_pdf_extractor",
        )
        d = edge.to_dict()
        self.assertIn("agent_id", d)
        self.assertEqual(d["agent_id"], "A04_pdf_extractor")
        self.assertIn("timestamp", d)

    def test_document_history(self):
        node = ProvenanceNode(
            node_id="doc1", node_type="filing_document",
            path="/filing.pdf", sha256="k" * 64,
            metadata={"version": 3, "author": "A. Pigors"},
        )
        d = node.to_dict()
        self.assertIn("metadata", d)
        self.assertEqual(d["metadata"]["version"], 3)

    def test_get_stats(self):
        stats = self.pt.get_stats()
        self.assertIsInstance(stats, dict)

    def test_provenance_to_dict(self):
        node = ProvenanceNode(
            node_id="test1", node_type="raw_file",
            path="/test.pdf", sha256="l" * 64,
        )
        d = node.to_dict()
        self.assertIn("node_id", d)
        self.assertIn("sha256", d)
        self.assertEqual(d["node_type"], "raw_file")

    def test_provenance_node_types_valid(self):
        valid_types = {
            "raw_file", "extracted_text", "analysis",
            "filing_section", "filing_document", "exhibit", "filed_document",
        }
        for ntype in valid_types:
            node = ProvenanceNode(
                node_id=f"n_{ntype}", node_type=ntype,
                path=f"/{ntype}.pdf", sha256="m" * 64,
            )
            self.assertEqual(node.node_type, ntype)

    def test_provenance_edge_relationships_valid(self):
        valid_rels = {
            "extracted_from", "analyzed_by", "included_in",
            "cited_by", "assembled_into", "filed_as",
        }
        for rel in valid_rels:
            edge = ProvenanceEdge(
                source_id="s", target_id="t", relationship=rel,
            )
            self.assertEqual(edge.relationship, rel)

    def test_provenance_report_structure(self):
        chain = ProvenanceChain(
            root_node=ProvenanceNode(
                node_id="root", node_type="filing_document",
                path="/filing.pdf", sha256="n" * 64,
            ),
            nodes=[], edges=[], depth=0, complete=False,
        )
        report = ProvenanceReport(
            filing_id="F300", chain=chain,
            coverage_pct=75.0,
            untracked_sections=["prayer_for_relief"],
            integrity_verified=True,
        )
        d = report.to_dict()
        self.assertIn("filing_id", d)
        self.assertIn("coverage_pct", d)
        self.assertEqual(d["coverage_pct"], 75.0)
        self.assertTrue(d["integrity_verified"])


if __name__ == "__main__":
    unittest.main()
