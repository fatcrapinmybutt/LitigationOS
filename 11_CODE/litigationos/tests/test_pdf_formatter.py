"""Tests for the Court-Specific PDF Formatting Engine (pdf_formatter)."""

from __future__ import annotations

import pytest

from litigationos.engines.pdf_formatter import (
    CaptionInfo,
    CourtFormat,
    CourtType,
    DEFAULT_CAPTION,
    DEFAULT_SIGNER,
    FormattingResult,
    PDFFormatter,
    ServiceEntry,
    ServiceInfo,
    SignerInfo,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fmt() -> PDFFormatter:
    return PDFFormatter()


@pytest.fixture()
def sample_markdown() -> str:
    return (
        "# Motion to Compel Discovery\n\n"
        "## Statement of Facts\n\n"
        "Plaintiff states the following facts in support of this motion.\n\n"
        "## Argument\n\n"
        "The Court should compel discovery under MCR 2.313.\n\n"
        "## Relief Requested\n\n"
        "Plaintiff requests an order compelling discovery responses.\n"
    )


# ============================================================================
# 1. CourtFormat / CourtType model tests
# ============================================================================


class TestCourtFormat:
    def test_circuit_format_defaults(self, fmt: PDFFormatter):
        cf = fmt.get_court_format("circuit")
        assert cf.court_type == CourtType.CIRCUIT
        assert cf.margin_inches == 1.0
        assert cf.font_size == 12
        assert cf.line_spacing == 2.0
        assert cf.max_pages == 50

    def test_coa_format_has_required_sections(self, fmt: PDFFormatter):
        cf = fmt.get_court_format("coa")
        assert "table_of_contents" in cf.required_sections
        assert "table_of_authorities" in cf.required_sections
        assert "jurisdictional_statement" in cf.required_sections

    def test_federal_page_limit(self, fmt: PDFFormatter):
        cf = fmt.get_court_format("federal")
        assert cf.max_pages == 25

    def test_jtc_no_page_limit(self, fmt: PDFFormatter):
        cf = fmt.get_court_format("jtc")
        assert cf.max_pages is None

    def test_unknown_court_raises(self, fmt: PDFFormatter):
        with pytest.raises(ValueError):
            fmt.get_court_format("lunar_tribunal")


# ============================================================================
# 2. format_for_court
# ============================================================================


class TestFormatForCourt:
    def test_returns_formatting_result(self, fmt: PDFFormatter, sample_markdown: str):
        result = fmt.format_for_court(sample_markdown, "circuit")
        assert isinstance(result, FormattingResult)

    def test_strips_markdown_headings(self, fmt: PDFFormatter):
        md = "# Heading\n## Sub\nBody text"
        result = fmt.format_for_court(md, "circuit")
        assert "# Heading" not in result.formatted_text
        assert "Heading" in result.formatted_text

    def test_page_count_positive(self, fmt: PDFFormatter, sample_markdown: str):
        result = fmt.format_for_court(sample_markdown, "circuit")
        assert result.page_count >= 1

    def test_exceeding_page_limit_warns(self, fmt: PDFFormatter):
        huge = "\n".join(["This is a line of content."] * 2000)
        result = fmt.format_for_court(huge, "federal")
        assert not result.compliant
        assert any("limit" in w.lower() for w in result.warnings)

    def test_within_page_limit_compliant(self, fmt: PDFFormatter):
        small = "Short document.\n"
        result = fmt.format_for_court(small, "circuit")
        assert result.compliant


# ============================================================================
# 3. apply_caption
# ============================================================================


class TestApplyCaption:
    def test_default_caption_has_state_header(self, fmt: PDFFormatter):
        out = fmt.apply_caption("Body text")
        assert "STATE OF MICHIGAN" in out

    def test_default_caption_has_case_number(self, fmt: PDFFormatter):
        out = fmt.apply_caption("Body text")
        assert "2024-001507-DC" in out

    def test_default_caption_has_parties(self, fmt: PDFFormatter):
        out = fmt.apply_caption("Body text")
        assert "ANDREW JAMES PIGORS" in out
        assert "EMILY A. WATSON" in out

    def test_default_caption_has_judge(self, fmt: PDFFormatter):
        out = fmt.apply_caption("Body text")
        assert "Hon. Jenny L. McNeill" in out

    def test_custom_caption(self, fmt: PDFFormatter):
        custom = CaptionInfo(
            court_name="IN THE MICHIGAN COURT OF APPEALS",
            case_number="366810",
            plaintiff="ANDREW JAMES PIGORS",
            defendant="EMILY A. WATSON",
            document_title="Appellant's Brief",
            judge=None,
        )
        out = fmt.apply_caption("Brief body", case_info=custom)
        assert "MICHIGAN COURT OF APPEALS" in out
        assert "366810" in out
        assert "APPELLANT'S BRIEF" in out

    def test_caption_precedes_body(self, fmt: PDFFormatter):
        out = fmt.apply_caption("THE BODY TEXT")
        state_idx = out.index("STATE OF MICHIGAN")
        body_idx = out.index("THE BODY TEXT")
        assert state_idx < body_idx


# ============================================================================
# 4. apply_signature_block
# ============================================================================


class TestApplySignatureBlock:
    def test_pro_se_signature(self, fmt: PDFFormatter):
        out = fmt.apply_signature_block("Body")
        assert "Respectfully submitted" in out
        assert "Andrew James Pigors, Pro Se" in out

    def test_signature_has_contact(self, fmt: PDFFormatter):
        out = fmt.apply_signature_block("Body")
        assert "(231) 903-5690" in out
        assert "andrewjpigors@gmail.com" in out

    def test_attorney_signature_has_bar_number(self, fmt: PDFFormatter):
        atty = SignerInfo(
            name="Test Attorney",
            address="123 Main St\nAnytown, MI 48000",
            phone="(555) 555-5555",
            email="test@example.com",
            bar_number="P12345",
            designation="Attorney",
        )
        out = fmt.apply_signature_block("Body", signer_info=atty)
        assert "Test Attorney (P12345)" in out

    def test_signature_appended(self, fmt: PDFFormatter):
        out = fmt.apply_signature_block("First line")
        assert out.startswith("First line")


# ============================================================================
# 5. apply_certificate_of_service
# ============================================================================


class TestApplyCertificateOfService:
    def test_cert_header_present(self, fmt: PDFFormatter):
        out = fmt.apply_certificate_of_service("Body")
        assert "CERTIFICATE OF SERVICE" in out

    def test_cert_default_recipient(self, fmt: PDFFormatter):
        out = fmt.apply_certificate_of_service("Body")
        assert "Emily A. Watson" in out

    def test_cert_custom_recipients(self, fmt: PDFFormatter):
        svc = ServiceInfo(
            recipients=[
                ServiceEntry(name="Recipient One", address="100 Oak St\nCity, MI"),
                ServiceEntry(name="Recipient Two", address="200 Elm St\nCity, MI"),
            ],
            method="electronic filing via MiFile",
        )
        out = fmt.apply_certificate_of_service("Body", service_info=svc)
        assert "Recipient One" in out
        assert "Recipient Two" in out
        assert "electronic filing via MiFile" in out


# ============================================================================
# 6. number_pages
# ============================================================================


class TestNumberPages:
    def test_single_page_has_marker(self, fmt: PDFFormatter):
        out = fmt.number_pages("Short text")
        assert "Page 1 of 1" in out

    def test_multi_page_markers(self, fmt: PDFFormatter):
        long_text = "\n".join([f"Line {i}" for i in range(60)])
        out = fmt.number_pages(long_text)
        assert "Page 1 of" in out
        assert "Page 2 of" in out


# ============================================================================
# 7. add_line_numbers
# ============================================================================


class TestAddLineNumbers:
    def test_lines_are_numbered(self, fmt: PDFFormatter):
        out = fmt.add_line_numbers("First\nSecond\nThird")
        assert "   1 | First" in out
        assert "   2 | Second" in out
        assert "   3 | Third" in out

    def test_blank_lines_not_counted(self, fmt: PDFFormatter):
        out = fmt.add_line_numbers("Alpha\n\nBravo")
        lines = out.splitlines()
        assert "   1 | Alpha" in lines[0]
        assert "   2 | Bravo" in lines[2]


# ============================================================================
# 8. validate_formatting
# ============================================================================


class TestValidateFormatting:
    def test_compliant_circuit_doc(self, fmt: PDFFormatter):
        doc = (
            "STATE OF MICHIGAN\nCase No. 2024-001507-DC\n"
            "Body of document\n"
            "Respectfully submitted\n"
            "CERTIFICATE OF SERVICE\n"
        )
        result = fmt.validate_formatting(doc, "circuit")
        assert result.compliant

    def test_missing_caption_warns(self, fmt: PDFFormatter):
        doc = "Body only\nRespectfully submitted\nCERTIFICATE OF SERVICE\n"
        result = fmt.validate_formatting(doc, "circuit")
        assert not result.compliant
        assert any("caption" in w for w in result.warnings)

    def test_coa_missing_toc_warns(self, fmt: PDFFormatter):
        doc = (
            "STATE OF MICHIGAN\nCase No.\n"
            "Respectfully submitted\nCERTIFICATE OF SERVICE\n"
        )
        result = fmt.validate_formatting(doc, "coa")
        assert any("table_of_contents" in w for w in result.warnings)

    def test_page_limit_exceeded_warns(self, fmt: PDFFormatter):
        huge = "\n".join(["Content line."] * 2000)
        result = fmt.validate_formatting(huge, "federal")
        assert any("limit" in w.lower() for w in result.warnings)


# ============================================================================
# 9. generate_exhibit_cover
# ============================================================================


class TestGenerateExhibitCover:
    def test_cover_has_exhibit_id(self, fmt: PDFFormatter):
        cover = fmt.generate_exhibit_cover("A", "Text messages, Jan 2024")
        assert "EXHIBIT A" in cover

    def test_cover_has_description(self, fmt: PDFFormatter):
        cover = fmt.generate_exhibit_cover("B", "Email correspondence")
        assert "Email correspondence" in cover


# ============================================================================
# 10. generate_bates_stamp
# ============================================================================


class TestGenerateBatesStamp:
    def test_single_stamp(self, fmt: PDFFormatter):
        stamps = fmt.generate_bates_stamp(1, "PIGORS", count=1)
        assert stamps == ["PIGORS-000001"]

    def test_batch_stamps(self, fmt: PDFFormatter):
        stamps = fmt.generate_bates_stamp(100, "WATSON", count=3)
        assert stamps == ["WATSON-000100", "WATSON-000101", "WATSON-000102"]

    def test_default_prefix(self, fmt: PDFFormatter):
        stamps = fmt.generate_bates_stamp(5)
        assert stamps[0] == "PIGORS-000005"


# ============================================================================
# 11. assemble_filing_package
# ============================================================================


class TestAssembleFilingPackage:
    def test_combines_components(self, fmt: PDFFormatter):
        result = fmt.assemble_filing_package(["Caption", "Body", "Cert"])
        assert "Caption" in result.formatted_text
        assert "Body" in result.formatted_text
        assert "Cert" in result.formatted_text

    def test_empty_produces_warning(self, fmt: PDFFormatter):
        result = fmt.assemble_filing_package([])
        assert not result.compliant
        assert result.warnings

    def test_page_count_positive(self, fmt: PDFFormatter):
        result = fmt.assemble_filing_package(["Some text\n" * 30])
        assert result.page_count >= 1

    def test_form_feed_separators(self, fmt: PDFFormatter):
        result = fmt.assemble_filing_package(["Part A", "Part B"])
        assert "\f" in result.formatted_text


# ============================================================================
# 12. End-to-end assembly
# ============================================================================


class TestEndToEnd:
    def test_full_filing_workflow(self, fmt: PDFFormatter):
        """Caption → body → signature → cert → pages → validate."""
        body = "The plaintiff respectfully moves this Court for relief."
        doc = fmt.apply_caption(body)
        doc = fmt.apply_signature_block(doc)
        doc = fmt.apply_certificate_of_service(doc)
        doc = fmt.number_pages(doc)
        result = fmt.validate_formatting(doc, "circuit")
        assert result.compliant
        assert "STATE OF MICHIGAN" in doc
        assert "Respectfully submitted" in doc
        assert "CERTIFICATE OF SERVICE" in doc
        assert "Page 1 of" in doc
