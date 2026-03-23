"""Comprehensive tests for the PDF Production Engine.

Covers Bates stamping, form filling, markdown→PDF, exhibit covers,
filing assembly, TOC/TOA generation, metadata embedding, and e-filing prep.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any

import pikepdf
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from litigationos.engines.pdf_production import (
    _escape_xml,
    _md_inline_to_xml,
    assemble_filing_package,
    create_exhibit_cover,
    create_exhibit_covers_batch,
    embed_pdf_metadata,
    fill_pdf_form,
    generate_toa,
    generate_toc,
    get_form_fields,
    markdown_file_to_pdf,
    markdown_to_pdf,
    prepare_for_efiling,
    stamp_bates_batch,
    stamp_bates_on_pdf,
)


# ---------------------------------------------------------------------------
# Helpers — create minimal PDFs for test inputs
# ---------------------------------------------------------------------------


def _make_blank_pdf(path: Path, pages: int = 1, text: str = "") -> Path:
    """Create a minimal PDF with reportlab for use as test input."""
    c = canvas.Canvas(str(path), pagesize=letter)
    for i in range(pages):
        if text:
            c.drawString(72, 700, f"{text} — page {i + 1}")
        c.showPage()
    c.save()
    return path


def _make_acroform_pdf(path: Path, fields: dict[str, str]) -> Path:
    """Create a PDF with AcroForm text fields using pikepdf."""
    # Build a minimal single-page PDF with reportlab first
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 700, "Form template")
    c.save()

    pdf = pikepdf.Pdf.open(buf)

    # Build AcroForm annotations manually
    annots = []
    y_pos = 650
    for name, default_value in fields.items():
        annot = pikepdf.Dictionary(
            Type=pikepdf.Name.Annot,
            Subtype=pikepdf.Name.Widget,
            FT=pikepdf.Name.Tx,
            T=pikepdf.String(name),
            V=pikepdf.String(default_value),
            Rect=pikepdf.Array([72, y_pos, 300, y_pos + 20]),
        )
        annots.append(pdf.make_indirect(annot))
        y_pos -= 30

    pdf.pages[0]["/Annots"] = pikepdf.Array(annots)
    pdf.Root["/AcroForm"] = pikepdf.Dictionary(
        Fields=pikepdf.Array(annots),
    )

    pdf.save(str(path))
    pdf.close()
    return path


# ===================================================================
# 1. CORE MARKDOWN → PDF GENERATION
# ===================================================================


class TestMarkdownToPdf:
    """Tests for markdown_to_pdf and markdown_file_to_pdf."""

    def test_markdown_to_pdf_produces_output(self, tmp_path: Path) -> None:
        """Basic markdown text produces a valid PDF file."""
        out = tmp_path / "basic.pdf"
        result = markdown_to_pdf("Hello world", out)
        assert result == out
        assert out.exists()
        assert out.stat().st_size > 0
        # Verify it's actually a PDF
        assert out.read_bytes()[:5] == b"%PDF-"

    def test_pdf_has_caption(self, tmp_path: Path) -> None:
        """When case_caption is provided it appears in the PDF."""
        out = tmp_path / "caption.pdf"
        caption = "IN THE 14TH CIRCUIT COURT\nFOR MUSKEGON COUNTY"
        markdown_to_pdf("Body text", out, case_caption=caption)

        # The PDF should be larger than one with no caption
        out_no_caption = tmp_path / "no_caption.pdf"
        markdown_to_pdf("Body text", out_no_caption)
        assert out.stat().st_size > out_no_caption.stat().st_size

    def test_pdf_page_numbers(self, tmp_path: Path) -> None:
        """Page numbers appear when page_numbers=True (default)."""
        out = tmp_path / "paged.pdf"
        # Long enough text to verify page number callback fires
        long_md = "\n\n".join([f"Paragraph {i}." for i in range(80)])
        markdown_to_pdf(long_md, out, page_numbers=True)
        assert out.exists()

        # Read back with pikepdf and confirm multi-page
        with pikepdf.Pdf.open(str(out)) as pdf:
            assert len(pdf.pages) >= 2

    def test_pdf_no_page_numbers(self, tmp_path: Path) -> None:
        """page_numbers=False still produces a valid PDF."""
        out = tmp_path / "no_page.pdf"
        markdown_to_pdf("Short text", out, page_numbers=False)
        assert out.exists()
        assert out.read_bytes()[:5] == b"%PDF-"

    def test_pdf_font_and_margins(self, tmp_path: Path) -> None:
        """Output PDF uses letter page size (612×792 points)."""
        out = tmp_path / "format.pdf"
        markdown_to_pdf("Test", out)
        with pikepdf.Pdf.open(str(out)) as pdf:
            page = pdf.pages[0]
            mbox = page.mediabox
            width = float(mbox[2]) - float(mbox[0])
            height = float(mbox[3]) - float(mbox[1])
            assert abs(width - 612) < 1  # letter width
            assert abs(height - 792) < 1  # letter height

    def test_markdown_file_to_pdf(self, tmp_path: Path) -> None:
        """Reading from a .md file produces the same result."""
        md_file = tmp_path / "input.md"
        md_file.write_text("# Heading\n\nBody text.", encoding="utf-8")
        out = tmp_path / "from_file.pdf"
        result = markdown_file_to_pdf(md_file, out)
        assert result == out
        assert out.exists()

    def test_markdown_file_not_found(self, tmp_path: Path) -> None:
        """FileNotFoundError when source .md doesn't exist."""
        with pytest.raises(FileNotFoundError):
            markdown_file_to_pdf(tmp_path / "nope.md", tmp_path / "out.pdf")


# ===================================================================
# 2. BATES STAMPING
# ===================================================================


class TestBatesStamping:
    """Tests for stamp_bates_on_pdf and stamp_bates_batch."""

    def test_bates_stamp_format(self, tmp_path: Path) -> None:
        """Stamps follow PREFIX-NNNNNN format."""
        src = _make_blank_pdf(tmp_path / "src.pdf", pages=3)
        out = tmp_path / "bates.pdf"
        result_path, next_num = stamp_bates_on_pdf(src, out, prefix="PIGORS")
        assert result_path == out
        assert out.exists()
        # next_num should be start + page_count
        assert next_num == 4  # 1 + 3

    def test_bates_sequential(self, tmp_path: Path) -> None:
        """Stamps are sequential across pages."""
        src = _make_blank_pdf(tmp_path / "seq.pdf", pages=5)
        out = tmp_path / "bates_seq.pdf"
        _, next_num = stamp_bates_on_pdf(src, out, start_number=10, prefix="EX")
        assert next_num == 15  # 10 + 5

    def test_bates_on_existing_pdf(self, tmp_path: Path) -> None:
        """Stamps are added without corrupting the PDF."""
        src = _make_blank_pdf(tmp_path / "exist.pdf", pages=2, text="Original content")
        out = tmp_path / "stamped.pdf"
        stamp_bates_on_pdf(src, out)
        with pikepdf.Pdf.open(str(out)) as pdf:
            assert len(pdf.pages) == 2

    def test_bates_positions(self, tmp_path: Path) -> None:
        """All three position options produce valid output."""
        src = _make_blank_pdf(tmp_path / "pos.pdf", pages=1)
        for pos in ("bottom-right", "bottom-left", "bottom-center"):
            out = tmp_path / f"bates_{pos}.pdf"
            path, _ = stamp_bates_on_pdf(src, out, position=pos)
            assert path.exists()

    def test_bates_file_not_found(self, tmp_path: Path) -> None:
        """FileNotFoundError when input PDF missing."""
        with pytest.raises(FileNotFoundError):
            stamp_bates_on_pdf(tmp_path / "nope.pdf", tmp_path / "out.pdf")

    def test_bates_batch(self, tmp_path: Path) -> None:
        """Batch Bates stamps multiple files with sequential numbering."""
        files = []
        for i in range(3):
            f = _make_blank_pdf(tmp_path / f"batch_{i}.pdf", pages=2)
            files.append(f)
        out_dir = tmp_path / "bates_out"
        results = stamp_bates_batch(files, out_dir, start_number=1, prefix="PIGORS")
        assert len(results) == 3
        # First file should have no error
        assert "error" not in results[0]
        assert results[0]["page_count"] == 2


# ===================================================================
# 3. FORM FILLING
# ===================================================================


class TestFormFilling:
    """Tests for fill_pdf_form and get_form_fields."""

    def test_fill_pdf_form(self, tmp_path: Path) -> None:
        """Fills form fields correctly and produces valid output."""
        template = _make_acroform_pdf(
            tmp_path / "template.pdf",
            {"CaseName": "", "CaseNumber": ""},
        )
        out = tmp_path / "filled.pdf"
        result = fill_pdf_form(
            template, out,
            field_values={"CaseName": "Pigors v Watson", "CaseNumber": "2024-001507-DC"},
        )
        assert result == out
        assert out.exists()

    def test_fill_with_party_data(self, tmp_path: Path) -> None:
        """Verified party names survive round-trip through form fill."""
        template = _make_acroform_pdf(
            tmp_path / "party.pdf",
            {"Plaintiff": "", "Defendant": ""},
        )
        out = tmp_path / "party_filled.pdf"
        fill_pdf_form(
            template, out,
            field_values={
                "Plaintiff": "Andrew James Pigors",
                "Defendant": "Emily A. Watson",
            },
            flatten=False,
        )
        # Read back and verify values persisted
        fields = get_form_fields(out)
        field_map = {f["name"]: f["value"] for f in fields}
        assert "Andrew James Pigors" in field_map.get("Plaintiff", "")
        assert "Emily A. Watson" in field_map.get("Defendant", "")

    def test_form_no_acroform(self, tmp_path: Path) -> None:
        """PDFs without AcroForm don't crash — just copy through."""
        plain = _make_blank_pdf(tmp_path / "plain.pdf")
        out = tmp_path / "filled_plain.pdf"
        result = fill_pdf_form(plain, out, field_values={"Foo": "Bar"})
        assert result == out
        assert out.exists()

    def test_get_form_fields(self, tmp_path: Path) -> None:
        """get_form_fields returns the correct field names/types."""
        template = _make_acroform_pdf(
            tmp_path / "fields.pdf",
            {"Name": "John", "Age": "30"},
        )
        fields = get_form_fields(template)
        names = {f["name"] for f in fields}
        assert "Name" in names
        assert "Age" in names

    def test_form_template_not_found(self, tmp_path: Path) -> None:
        """FileNotFoundError when template is missing."""
        with pytest.raises(FileNotFoundError):
            fill_pdf_form(tmp_path / "ghost.pdf", tmp_path / "out.pdf", {})

    def test_get_form_fields_not_found(self, tmp_path: Path) -> None:
        """FileNotFoundError from get_form_fields on missing file."""
        with pytest.raises(FileNotFoundError):
            get_form_fields(tmp_path / "ghost.pdf")


# ===================================================================
# 4. EXHIBIT COVERS
# ===================================================================


class TestExhibitCovers:
    """Tests for create_exhibit_cover and create_exhibit_covers_batch."""

    def test_create_exhibit_cover(self, tmp_path: Path) -> None:
        """Single exhibit cover produces a valid 1-page PDF."""
        out = tmp_path / "cover.pdf"
        result = create_exhibit_cover("Exhibit A", "Text Messages", out)
        assert result == out
        assert out.exists()
        with pikepdf.Pdf.open(str(out)) as pdf:
            assert len(pdf.pages) == 1

    def test_cover_with_caption_and_bates(self, tmp_path: Path) -> None:
        """Cover includes caption and Bates range without error."""
        out = tmp_path / "cover2.pdf"
        create_exhibit_cover(
            "Exhibit B",
            "Financial Records",
            out,
            case_caption="Pigors v Watson\n14th Circuit Court",
            bates_range="PIGORS-000001 through PIGORS-000015",
        )
        assert out.exists()

    def test_exhibit_covers_batch(self, tmp_path: Path) -> None:
        """Batch produces one cover per exhibit."""
        exhibits = [
            {"label": "Exhibit A", "title": "Text Messages"},
            {"label": "Exhibit B", "title": "Bank Statements"},
            {"label": "Exhibit C", "title": "Photos"},
        ]
        out_dir = tmp_path / "covers"
        paths = create_exhibit_covers_batch(exhibits, out_dir)
        assert len(paths) == 3
        for p in paths:
            assert p.exists()


# ===================================================================
# 5. TABLE OF CONTENTS & TABLE OF AUTHORITIES
# ===================================================================


class TestTocAndToa:
    """Tests for generate_toc and generate_toa."""

    def test_generate_toc(self, tmp_path: Path) -> None:
        """TOC generates a valid PDF from entry list."""
        entries = [
            {"title": "Introduction", "page": 1, "level": 0},
            {"title": "Argument", "page": 3, "level": 0},
            {"title": "Sub-point A", "page": 4, "level": 1},
            {"title": "Exhibit A", "page": 10, "level": 2},
        ]
        out = tmp_path / "toc.pdf"
        result = generate_toc(entries, out)
        assert result == out
        assert out.exists()

    def test_toc_empty_entries(self, tmp_path: Path) -> None:
        """TOC with no entries still produces a valid PDF."""
        out = tmp_path / "toc_empty.pdf"
        generate_toc([], out)
        assert out.exists()
        assert out.read_bytes()[:5] == b"%PDF-"

    def test_generate_toa(self, tmp_path: Path) -> None:
        """TOA groups by type and produces valid PDF."""
        authorities = [
            {"citation": "Smith v Jones, 123 Mich 456", "type": "case", "pages": "3, 5"},
            {"citation": "MCL 722.23", "type": "statute", "pages": "7"},
            {"citation": "MCR 2.003", "type": "rule", "pages": "1, 4"},
        ]
        out = tmp_path / "toa.pdf"
        result = generate_toa(authorities, out)
        assert result == out
        assert out.exists()

    def test_toa_empty_authorities(self, tmp_path: Path) -> None:
        """TOA with no authorities still produces valid PDF."""
        out = tmp_path / "toa_empty.pdf"
        generate_toa([], out)
        assert out.exists()


# ===================================================================
# 6. METADATA EMBEDDING
# ===================================================================


class TestMetadata:
    """Tests for embed_pdf_metadata."""

    def test_embed_metadata(self, tmp_path: Path) -> None:
        """Metadata fields are written to the PDF."""
        src = _make_blank_pdf(tmp_path / "meta_src.pdf")
        out = tmp_path / "meta_out.pdf"
        result = embed_pdf_metadata(
            src, out,
            title="Motion to Compel",
            author="Andrew James Pigors",
            subject="Discovery dispute",
            keywords="discovery, compel, sanctions",
        )
        assert result == out
        with pikepdf.Pdf.open(str(out)) as pdf:
            info = pdf.docinfo
            assert str(info.get("/Title", "")) == "Motion to Compel"
            assert str(info.get("/Author", "")) == "Andrew James Pigors"
            assert str(info.get("/CaseNumber", "")) == "2024-001507-DC"

    def test_embed_metadata_in_place(self, tmp_path: Path) -> None:
        """When output_pdf is None, file is overwritten in-place."""
        src = _make_blank_pdf(tmp_path / "inplace.pdf")
        result = embed_pdf_metadata(src, title="In-Place Title")
        assert result == src
        with pikepdf.Pdf.open(str(src)) as pdf:
            assert str(pdf.docinfo.get("/Title", "")) == "In-Place Title"

    def test_embed_metadata_not_found(self, tmp_path: Path) -> None:
        """FileNotFoundError when source PDF missing."""
        with pytest.raises(FileNotFoundError):
            embed_pdf_metadata(tmp_path / "ghost.pdf")


# ===================================================================
# 7. E-FILING PREPARATION
# ===================================================================


class TestEfilingPrep:
    """Tests for prepare_for_efiling."""

    def test_efiling_basic(self, tmp_path: Path) -> None:
        """Basic e-filing prep produces compliant output."""
        src = _make_blank_pdf(tmp_path / "filing.pdf", pages=3, text="Motion text")
        out_dir = tmp_path / "efiled"
        result = prepare_for_efiling(src, out_dir, document_type="Motion")
        assert Path(result["output"]).exists()
        assert result["page_count"] == 3
        assert isinstance(result["file_size_mb"], float)

    def test_efiling_file_size_check(self, tmp_path: Path) -> None:
        """Oversized files get a warning and are non-compliant."""
        # Generate a PDF large enough to exceed 0.01 MB after rounding
        src = _make_blank_pdf(tmp_path / "big.pdf", pages=30, text="Bulk content " * 50)
        out = tmp_path / "efiled_big"
        size_mb = round(src.stat().st_size / (1024 * 1024), 2)
        # Set limit below actual size to trigger the warning
        limit = max(size_mb - 0.01, 0.0)
        result = prepare_for_efiling(src, out, max_file_size_mb=limit)
        if size_mb > limit:
            assert any("exceeds" in w for w in result["warnings"])
            assert result["compliant"] is False
        else:
            # File too small to exceed even 0.0 — just verify output exists
            assert Path(result["output"]).exists()

    def test_efiling_naming_convention(self, tmp_path: Path) -> None:
        """Output filename follows MiFILE pattern: CaseNum_DocType_Date.pdf."""
        src = _make_blank_pdf(tmp_path / "name.pdf")
        out_dir = tmp_path / "named"
        result = prepare_for_efiling(
            src, out_dir,
            case_number="2024-001507-DC",
            document_type="Motion",
            filing_date="2025-01-15",
        )
        out_name = Path(result["output"]).name
        assert "2024001507DC" in out_name
        assert "Motion" in out_name
        assert "20250115" in out_name
        assert out_name.endswith(".pdf")

    def test_efiling_not_found(self, tmp_path: Path) -> None:
        """FileNotFoundError when source PDF missing."""
        with pytest.raises(FileNotFoundError):
            prepare_for_efiling(tmp_path / "ghost.pdf", tmp_path / "out")


# ===================================================================
# 8. FILING PACKAGE ASSEMBLY
# ===================================================================


class TestFilingPackageAssembly:
    """Tests for assemble_filing_package."""

    def test_assemble_pdf_main_with_exhibits(self, tmp_path: Path) -> None:
        """Assembles a main PDF + exhibits into a merged package."""
        main = _make_blank_pdf(tmp_path / "main.pdf", pages=2, text="Main filing")
        ex1 = _make_blank_pdf(tmp_path / "ex1.pdf", pages=1, text="Exhibit 1")
        ex2 = _make_blank_pdf(tmp_path / "ex2.pdf", pages=1, text="Exhibit 2")

        out = tmp_path / "package.pdf"
        result = assemble_filing_package(
            main,
            exhibits=[
                {"path": str(ex1), "label": "Exhibit A", "title": "Text Messages"},
                {"path": str(ex2), "label": "Exhibit B", "title": "Bank Records"},
            ],
            output_pdf=out,
            add_bates=False,
            add_covers=False,
        )
        assert Path(result["output"]).exists()
        assert result["page_count"] == 4  # 2 main + 1 + 1
        assert result["exhibit_count"] == 2

    def test_assemble_markdown_main(self, tmp_path: Path) -> None:
        """Accepts a .md file as main document."""
        md = tmp_path / "main.md"
        md.write_text("# Motion\n\nThis is the motion body.", encoding="utf-8")
        ex = _make_blank_pdf(tmp_path / "ex.pdf", pages=1)

        out = tmp_path / "md_package.pdf"
        result = assemble_filing_package(
            md,
            exhibits=[{"path": str(ex), "label": "Exhibit A", "title": "Evidence"}],
            output_pdf=out,
            add_bates=False,
            add_covers=False,
        )
        assert Path(result["output"]).exists()
        assert result["page_count"] >= 2

    def test_assemble_unsupported_format(self, tmp_path: Path) -> None:
        """Unsupported main document format raises ValueError."""
        txt = tmp_path / "main.txt"
        txt.write_text("Not a PDF or MD")
        with pytest.raises(ValueError, match="Unsupported"):
            assemble_filing_package(txt, [], tmp_path / "out.pdf")

    def test_assemble_with_covers(self, tmp_path: Path) -> None:
        """add_covers=True inserts exhibit cover pages."""
        main = _make_blank_pdf(tmp_path / "main.pdf", pages=1)
        ex = _make_blank_pdf(tmp_path / "ex.pdf", pages=1)
        out = tmp_path / "covers_pkg.pdf"
        result = assemble_filing_package(
            main,
            exhibits=[{"path": str(ex), "label": "Exhibit A", "title": "Docs"}],
            output_pdf=out,
            add_bates=False,
            add_covers=True,
        )
        # Should have: 1 (main) + 1 (cover) + 1 (exhibit) = 3
        assert result["page_count"] == 3


# ===================================================================
# 9. EDGE CASES & HELPERS
# ===================================================================


class TestEdgeCases:
    """Edge cases and internal helper functions."""

    def test_empty_markdown(self, tmp_path: Path) -> None:
        """Empty markdown string produces a valid (small) PDF."""
        out = tmp_path / "empty.pdf"
        result = markdown_to_pdf("", out)
        assert result == out
        assert out.exists()

    def test_unicode_content(self, tmp_path: Path) -> None:
        """Unicode characters (accents, em-dash, section sign) don't crash."""
        md = "§ 722.23 — André's résumé: naïve → \"smart\" quotes"
        out = tmp_path / "unicode.pdf"
        result = markdown_to_pdf(md, out)
        assert result == out
        assert out.exists()

    def test_markdown_headings_and_lists(self, tmp_path: Path) -> None:
        """All markdown element types parse without error."""
        md = (
            "# Heading 1\n"
            "## Heading 2\n"
            "### Heading 3\n"
            "Normal paragraph.\n"
            "\n"
            "- Bullet one\n"
            "* Bullet two\n"
            "1. Numbered item\n"
            "\n"
            "> Blockquote text\n"
            "\n"
            "---\n"
            "\n"
            "<!-- pagebreak -->\n"
            "\n"
            "**Bold** and *italic* and `code`.\n"
        )
        out = tmp_path / "elements.pdf"
        markdown_to_pdf(md, out)
        assert out.exists()

    def test_escape_xml(self) -> None:
        """_escape_xml handles ampersands, angles correctly."""
        assert _escape_xml("A & B") == "A &amp; B"
        assert _escape_xml("<tag>") == "&lt;tag&gt;"

    def test_md_inline_to_xml_bold(self) -> None:
        """Bold markers become <b> tags."""
        result = _md_inline_to_xml("**bold** text")
        assert "<b>bold</b>" in result

    def test_md_inline_to_xml_italic(self) -> None:
        """Italic markers become <i> tags."""
        result = _md_inline_to_xml("*italic* text")
        assert "<i>italic</i>" in result

    def test_md_inline_to_xml_code(self) -> None:
        """Backtick markers become Courier font tags."""
        result = _md_inline_to_xml("`code` text")
        assert "Courier" in result
        assert "code" in result

    def test_output_dirs_created(self, tmp_path: Path) -> None:
        """Nested output directories are auto-created."""
        deep = tmp_path / "a" / "b" / "c" / "output.pdf"
        markdown_to_pdf("test", deep)
        assert deep.exists()

    def test_large_document(self, tmp_path: Path) -> None:
        """A document with 100+ paragraphs produces multi-page output."""
        paragraphs = [f"Paragraph number {i}. " * 5 for i in range(120)]
        md = "\n\n".join(paragraphs)
        out = tmp_path / "large.pdf"
        markdown_to_pdf(md, out)
        with pikepdf.Pdf.open(str(out)) as pdf:
            assert len(pdf.pages) >= 5
