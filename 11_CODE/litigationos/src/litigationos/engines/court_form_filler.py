"""SCAO Court Form Auto-Filler Engine.

Auto-fills Michigan SCAO court forms using pikepdf AcroForm manipulation
with reportlab overlay fallback.  Connects to ``court_forms.db`` for the
form registry and ``litigation_context.db`` for case data.

Usage::

    filler = CourtFormFiller()
    forms  = filler.list_forms()
    fields = filler.get_form_fields("MC_15")
    data   = filler.auto_fill_party_data("MC_15")
    path   = filler.fill_form("MC_15", data, "output/mc15_filled.pdf")
    report = filler.validate_form(path)
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from litigationos.db.connection import DatabaseManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature flags — degrade gracefully when optional deps are missing
# ---------------------------------------------------------------------------

_HAS_PIKEPDF: bool = False
try:
    import pikepdf  # noqa: F401
    from pikepdf import Name as PdfName, Pdf, String as PdfString

    _HAS_PIKEPDF = True
except ImportError:  # pragma: no cover
    pass

_HAS_REPORTLAB: bool = False
try:
    from reportlab.lib.pagesizes import letter  # noqa: F401
    from reportlab.pdfgen import canvas  # noqa: F401

    _HAS_REPORTLAB = True
except ImportError:  # pragma: no cover
    pass

# ---------------------------------------------------------------------------
# Database paths
# ---------------------------------------------------------------------------

_COURT_FORMS_DB = Path(r"C:\Users\andre\LitigationOS\court_forms.db")
_LITIGATION_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")

# ---------------------------------------------------------------------------
# Verified party identity — SINGLE SOURCE OF TRUTH
# ---------------------------------------------------------------------------

PARTY_DATA: dict[str, str] = {
    # Plaintiff
    "plaintiff_name": "Andrew James Pigors",
    "plaintiff_address": "1977 Whitehall Road, Lot 17",
    "plaintiff_city": "North Muskegon",
    "plaintiff_state": "MI",
    "plaintiff_zip": "49445",
    "plaintiff_phone": "(231) 903-5690",
    "plaintiff_email": "andrewjpigors@gmail.com",
    "plaintiff_full_address": (
        "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445"
    ),
    # Defendant
    "defendant_name": "Emily A. Watson",
    "defendant_address": "2160 Garland Drive",
    "defendant_city": "Norton Shores",
    "defendant_state": "MI",
    "defendant_zip": "49441",
    "defendant_full_address": "2160 Garland Drive, Norton Shores, MI 49441",
    # Child — initials only per MCR 8.119(H)
    "child_initials": "L.D.W.",
    # Court
    "court_name": "14th Circuit Court",
    "court_division": "Family Division",
    "court_full": "14th Circuit Court, Family Division",
    "court_address": "990 Terrace St, Muskegon, MI 49442",
    "county": "Muskegon",
    # Judge
    "judge_name": "Hon. Jenny L. McNeill",
    # Case
    "case_number": "2024-001507-DC",
    # FOC
    "foc_name": "Pamela Rusco",
    "foc_address": "990 Terrace St, Muskegon, MI 49442",
}

# ---------------------------------------------------------------------------
# Motion-type → SCAO form mapping
# ---------------------------------------------------------------------------

_MOTION_FORM_MAP: dict[str, list[dict[str, str]]] = {
    "disqualify": [
        {"form_id": "MC_15", "form_number": "MC 15", "reason": "Motion"},
    ],
    "response": [
        {"form_id": "MC_16", "form_number": "MC 16", "reason": "Response to Motion"},
    ],
    "ppo": [
        {"form_id": "CC_375", "form_number": "CC 375", "reason": "PPO Petition"},
        {"form_id": "CC_376", "form_number": "CC 376", "reason": "PPO (Ex Parte)"},
        {"form_id": "CC_377", "form_number": "CC 377", "reason": "PPO (Non-Domestic)"},
        {"form_id": "CC_380", "form_number": "CC 380", "reason": "PPO Order"},
    ],
    "custody": [
        {"form_id": "FOC_10", "form_number": "FOC 10", "reason": "Uniform Child Custody Jurisdiction Enforcement"},
        {"form_id": "DC_100", "form_number": "DC 100", "reason": "Complaint for Custody"},
        {"form_id": "DC_101", "form_number": "DC 101", "reason": "Answer to Custody Complaint"},
    ],
    "show_cause": [
        {"form_id": "MC_15", "form_number": "MC 15", "reason": "Motion"},
        {"form_id": "OSC", "form_number": "Order to Show Cause", "reason": "Show Cause Order"},
    ],
    "discovery": [
        {"form_id": "MC_15", "form_number": "MC 15", "reason": "Generic Motion for Discovery"},
    ],
    "appeal": [
        {"form_id": "CA_1", "form_number": "CA 1", "reason": "Claim of Appeal"},
        {"form_id": "CA_6", "form_number": "CA 6", "reason": "Certificate of Service (Appeal)"},
        {"form_id": "CA_7", "form_number": "CA 7", "reason": "Docketing Statement"},
    ],
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class CourtFormFiller:
    """Auto-fill Michigan SCAO court forms via pikepdf AcroForm manipulation.

    Falls back to a reportlab text-overlay strategy when pikepdf cannot
    manipulate AcroForm fields (e.g. the PDF has no interactive fields).

    Parameters
    ----------
    db : DatabaseManager, optional
        Shared database manager.  When ``None`` the engine opens its own
        connections to ``court_forms.db`` and ``litigation_context.db``.
    """

    def __init__(self, db: Optional[DatabaseManager] = None) -> None:
        self._db = db
        self._court_forms_db = _COURT_FORMS_DB
        self._litigation_db = _LITIGATION_DB
        logger.info(
            "CourtFormFiller ready  pikepdf=%s  reportlab=%s  forms_db=%s",
            _HAS_PIKEPDF,
            _HAS_REPORTLAB,
            self._court_forms_db,
        )

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connect_forms(self) -> sqlite3.Connection:
        """Open a WAL-mode connection to ``court_forms.db``."""
        conn = sqlite3.connect(str(self._court_forms_db), timeout=60)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    def _connect_litigation(self) -> sqlite3.Connection:
        """Open a WAL-mode connection to ``litigation_context.db``."""
        conn = sqlite3.connect(str(self._litigation_db), timeout=60)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 60000")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA cache_size = -32000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA synchronous = NORMAL")
        return conn

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
        """Return ``True`` if *name* exists as a table in *conn*."""
        row = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone()
        return row[0] > 0

    # ------------------------------------------------------------------
    # 1. list_forms
    # ------------------------------------------------------------------

    def list_forms(self) -> list[dict]:
        """Return every SCAO form registered in ``court_forms.db``.

        Each dict contains at minimum: ``form_id``, ``form_number``,
        ``form_name``, ``court_level``, ``division``, ``description``,
        ``fillable``, and ``filing_lanes``.
        """
        conn = self._connect_forms()
        try:
            if not self._table_exists(conn, "court_forms"):
                logger.warning("court_forms table not found in %s", self._court_forms_db)
                return []
            rows = conn.execute(
                "SELECT form_id, form_number, form_name, form_series, "
                "court_level, division, description, url, page_count, "
                "fillable, required_for, filing_lanes, mcr_reference, notes "
                "FROM court_forms ORDER BY form_number"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 2. get_form_fields
    # ------------------------------------------------------------------

    def get_form_fields(self, form_id: str) -> list[dict]:
        """Return field definitions for *form_id*.

        First checks the ``form_fields`` table in ``court_forms.db``.
        If a template PDF is available and pikepdf is installed, also
        extracts live AcroForm field names/types from the PDF.
        """
        fields: list[dict] = []

        # --- DB field definitions ---
        conn = self._connect_forms()
        try:
            if self._table_exists(conn, "form_fields"):
                rows = conn.execute(
                    "SELECT field_name, field_type, field_label, "
                    "auto_fill_source, auto_fill_value, required, "
                    "section, notes "
                    "FROM form_fields WHERE form_id = ? "
                    "ORDER BY id",
                    (form_id,),
                ).fetchall()
                fields = [dict(r) for r in rows]
        finally:
            conn.close()

        # --- Live AcroForm extraction (pikepdf) ---
        if _HAS_PIKEPDF:
            pdf_path = self._locate_template(form_id)
            if pdf_path and pdf_path.exists():
                try:
                    acro_fields = self._extract_acroform_fields(pdf_path)
                    # Merge: add any PDF-only fields not already in DB list
                    known = {f["field_name"] for f in fields}
                    for af in acro_fields:
                        if af["field_name"] not in known:
                            fields.append(af)
                except Exception:
                    logger.warning(
                        "AcroForm extraction failed for %s", form_id, exc_info=True
                    )

        return fields

    # ------------------------------------------------------------------
    # 3. auto_fill_party_data
    # ------------------------------------------------------------------

    def auto_fill_party_data(self, form_id: str) -> dict[str, str]:
        """Build a field-value dict pre-filled with known party data.

        Merges the module-level ``PARTY_DATA`` with any
        ``auto_fill_value`` entries stored in the ``form_fields`` table
        for *form_id*.
        """
        values: dict[str, str] = {}

        # Start with the universal party constants
        values.update(PARTY_DATA)

        # Layer on form-specific auto-fill values from the DB
        conn = self._connect_forms()
        try:
            if self._table_exists(conn, "form_fields"):
                rows = conn.execute(
                    "SELECT field_name, auto_fill_value "
                    "FROM form_fields "
                    "WHERE form_id = ? AND auto_fill_value IS NOT NULL "
                    "      AND auto_fill_value != ''",
                    (form_id,),
                ).fetchall()
                for r in rows:
                    values[r["field_name"]] = r["auto_fill_value"]
        finally:
            conn.close()

        # Add today's date for common date fields
        today = datetime.now().strftime("%m/%d/%Y")
        values.setdefault("date", today)
        values.setdefault("filing_date", today)
        values.setdefault("signature_date", today)

        logger.debug("auto_fill_party_data(%s) → %d values", form_id, len(values))
        return values

    # ------------------------------------------------------------------
    # 4. fill_form
    # ------------------------------------------------------------------

    def fill_form(
        self,
        form_id: str,
        field_values: dict[str, str],
        output_path: str,
    ) -> str:
        """Fill a PDF form and write the result to *output_path*.

        Strategy:
        1. If pikepdf is available and the template has AcroForm fields →
           write values directly into the AcroForm dictionary.
        2. Otherwise, if reportlab is available → render a text-overlay
           PDF and merge it onto the template.
        3. If neither library is available, raise ``RuntimeError``.

        Returns the absolute path of the written file.
        """
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)

        template = self._locate_template(form_id)

        if _HAS_PIKEPDF and template and template.exists():
            try:
                self._fill_with_pikepdf(template, field_values, out)
                logger.info("Filled %s → %s (pikepdf)", form_id, out)
                return str(out.resolve())
            except Exception:
                logger.warning(
                    "pikepdf fill failed for %s, trying reportlab fallback",
                    form_id,
                    exc_info=True,
                )

        if _HAS_REPORTLAB:
            self._fill_with_reportlab(field_values, out)
            logger.info("Filled %s → %s (reportlab overlay)", form_id, out)
            return str(out.resolve())

        raise RuntimeError(
            "Neither pikepdf nor reportlab is available — cannot fill form."
        )

    # ------------------------------------------------------------------
    # 5. batch_fill
    # ------------------------------------------------------------------

    def batch_fill(
        self,
        form_ids: list[str],
        common_data: dict[str, str],
        output_dir: str,
    ) -> list[str]:
        """Fill multiple forms with shared party/case data.

        Returns a list of output paths for each successfully filled form.
        """
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        results: list[str] = []

        for fid in form_ids:
            merged = self.auto_fill_party_data(fid)
            merged.update(common_data)
            out_path = out_dir / f"{fid}_filled.pdf"
            try:
                path = self.fill_form(fid, merged, str(out_path))
                results.append(path)
            except Exception:
                logger.error("batch_fill: failed to fill %s", fid, exc_info=True)

        logger.info(
            "batch_fill complete: %d/%d forms filled → %s",
            len(results),
            len(form_ids),
            out_dir,
        )
        return results

    # ------------------------------------------------------------------
    # 6. validate_form
    # ------------------------------------------------------------------

    def validate_form(self, filled_path: str) -> dict[str, Any]:
        """Check that required fields in a filled PDF are populated.

        Returns a dict with keys:
        - ``valid`` (bool): True when all required fields have values.
        - ``total_fields`` (int): Number of fields found.
        - ``filled_fields`` (int): Number of non-empty fields.
        - ``empty_required`` (list[str]): Names of required-but-empty fields.
        - ``warnings`` (list[str]): Non-fatal issues.
        """
        result: dict[str, Any] = {
            "valid": True,
            "total_fields": 0,
            "filled_fields": 0,
            "empty_required": [],
            "warnings": [],
        }

        pdf_path = Path(filled_path)
        if not pdf_path.exists():
            result["valid"] = False
            result["warnings"].append(f"File not found: {filled_path}")
            return result

        if not _HAS_PIKEPDF:
            result["warnings"].append(
                "pikepdf not available — cannot inspect AcroForm fields"
            )
            return result

        try:
            pdf = Pdf.open(str(pdf_path))
            if "/AcroForm" not in pdf.Root:
                result["warnings"].append("PDF has no AcroForm — cannot validate fields")
                return result

            fields = pdf.Root["/AcroForm"].get("/Fields", [])
            for field_ref in fields:
                field_obj = field_ref.resolve() if hasattr(field_ref, "resolve") else field_ref
                result["total_fields"] += 1

                name = str(field_obj.get("/T", ""))
                value = str(field_obj.get("/V", ""))

                if value and value not in ("", "/"):
                    result["filled_fields"] += 1
                else:
                    # Check if field is flagged required (Ff bit 2)
                    flags = int(field_obj.get("/Ff", 0))
                    is_required = bool(flags & 0x2)
                    if is_required:
                        result["empty_required"].append(name)

            pdf.close()
        except Exception:
            logger.warning("validate_form failed for %s", filled_path, exc_info=True)
            result["valid"] = False
            result["warnings"].append("Failed to parse PDF")
            return result

        if result["empty_required"]:
            result["valid"] = False

        logger.debug(
            "validate_form(%s): %d/%d filled, %d empty-required",
            filled_path,
            result["filled_fields"],
            result["total_fields"],
            len(result["empty_required"]),
        )
        return result

    # ------------------------------------------------------------------
    # 7. get_form_for_motion
    # ------------------------------------------------------------------

    def get_form_for_motion(self, motion_type: str) -> list[dict]:
        """Map a motion type to the required SCAO form(s).

        Checks the ``form_filing_map`` table first, then falls back to
        the hardcoded ``_MOTION_FORM_MAP``.

        Parameters
        ----------
        motion_type : str
            A slug such as ``"disqualify"``, ``"custody"``, ``"ppo"``,
            ``"appeal"``, ``"show_cause"``, ``"discovery"``, or
            ``"response"``.
        """
        key = motion_type.lower().strip().replace(" ", "_")
        results: list[dict] = []

        # --- DB lookup (form_filing_map) ---
        conn = self._connect_forms()
        try:
            if self._table_exists(conn, "form_filing_map"):
                rows = conn.execute(
                    "SELECT ffm.form_id, cf.form_number, cf.form_name, "
                    "ffm.required, ffm.order_in_package, ffm.notes "
                    "FROM form_filing_map ffm "
                    "LEFT JOIN court_forms cf ON ffm.form_id = cf.form_id "
                    "WHERE LOWER(ffm.filing_type) = ? "
                    "ORDER BY ffm.order_in_package",
                    (key,),
                ).fetchall()
                if rows:
                    results = [dict(r) for r in rows]
        finally:
            conn.close()

        # --- Hardcoded fallback ---
        if not results and key in _MOTION_FORM_MAP:
            results = list(_MOTION_FORM_MAP[key])
        elif not results:
            # Fuzzy match: try substring search against keys
            for map_key, forms in _MOTION_FORM_MAP.items():
                if key in map_key or map_key in key:
                    results = list(forms)
                    break

        if not results:
            logger.warning("No SCAO forms mapped for motion_type=%r", motion_type)

        return results

    # ==================================================================
    # Private helpers
    # ==================================================================

    def _locate_template(self, form_id: str) -> Optional[Path]:
        """Try to find a PDF template for *form_id* on disk.

        Search order:
        1. ``court_forms.db`` → ``url`` column (if it's a local path)
        2. Common template directories under LitigationOS
        """
        # Check the DB for a path/URL
        conn = self._connect_forms()
        try:
            if self._table_exists(conn, "court_forms"):
                row = conn.execute(
                    "SELECT url FROM court_forms WHERE form_id = ?",
                    (form_id,),
                ).fetchone()
                if row and row["url"]:
                    candidate = Path(row["url"])
                    if candidate.exists():
                        return candidate
        finally:
            conn.close()

        # Scan known template directories
        search_dirs = [
            Path(r"C:\Users\andre\LitigationOS\COURT_FORMS"),
            Path(r"C:\Users\andre\LitigationOS\templates"),
            Path(r"C:\Users\andre\LitigationOS\Vault\COURT_FORMS"),
        ]
        for d in search_dirs:
            if not d.exists():
                continue
            for ext in ("*.pdf", "*.PDF"):
                for f in d.glob(ext):
                    stem = f.stem.upper().replace(" ", "_").replace("-", "_")
                    if form_id.upper().replace("-", "_") in stem:
                        return f

        return None

    # ------------------------------------------------------------------
    # pikepdf AcroForm helpers
    # ------------------------------------------------------------------

    def _extract_acroform_fields(self, pdf_path: Path) -> list[dict]:
        """Extract AcroForm field metadata from a PDF using pikepdf."""
        fields: list[dict] = []
        pdf = Pdf.open(str(pdf_path))
        try:
            if "/AcroForm" not in pdf.Root:
                return fields
            acro = pdf.Root["/AcroForm"]
            for field_ref in acro.get("/Fields", []):
                field_obj = (
                    field_ref.resolve()
                    if hasattr(field_ref, "resolve")
                    else field_ref
                )
                name = str(field_obj.get("/T", ""))
                ft = str(field_obj.get("/FT", "/Tx"))
                flags = int(field_obj.get("/Ff", 0))
                fields.append(
                    {
                        "field_name": name,
                        "field_type": self._acro_type_label(ft),
                        "field_label": name,
                        "auto_fill_source": None,
                        "auto_fill_value": None,
                        "required": 1 if (flags & 0x2) else 0,
                        "section": None,
                        "notes": f"Extracted from PDF AcroForm ({pdf_path.name})",
                    }
                )
        finally:
            pdf.close()
        return fields

    @staticmethod
    def _acro_type_label(ft_name: str) -> str:
        """Convert an AcroForm /FT name to a human-readable label."""
        mapping = {
            "/Tx": "text",
            "/Btn": "checkbox",
            "/Ch": "choice",
            "/Sig": "signature",
        }
        return mapping.get(ft_name, "text")

    def _fill_with_pikepdf(
        self,
        template: Path,
        field_values: dict[str, str],
        output: Path,
    ) -> None:
        """Write *field_values* into AcroForm fields of *template*."""
        pdf = Pdf.open(str(template))
        try:
            if "/AcroForm" not in pdf.Root:
                raise ValueError(f"Template {template.name} has no AcroForm fields")

            acro = pdf.Root["/AcroForm"]
            # Disable NeedAppearances so readers regenerate appearances
            acro[PdfName("/NeedAppearances")] = True

            for field_ref in acro.get("/Fields", []):
                field_obj = (
                    field_ref.resolve()
                    if hasattr(field_ref, "resolve")
                    else field_ref
                )
                name = str(field_obj.get("/T", ""))
                if name in field_values:
                    field_obj[PdfName("/V")] = PdfString(field_values[name])

            pdf.save(str(output))
        finally:
            pdf.close()

    # ------------------------------------------------------------------
    # reportlab fallback
    # ------------------------------------------------------------------

    def _fill_with_reportlab(
        self,
        field_values: dict[str, str],
        output: Path,
    ) -> None:
        """Generate a simple one-page overlay PDF listing field values.

        This is a degraded fallback — it produces a readable document
        but not a filled interactive form.
        """
        from reportlab.lib.pagesizes import letter as rl_letter
        from reportlab.pdfgen.canvas import Canvas

        c = Canvas(str(output), pagesize=rl_letter)
        width, height = rl_letter
        y = height - 72  # 1-inch top margin
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, y, "SCAO Court Form — Auto-Fill Data")
        y -= 28
        c.setFont("Helvetica", 10)

        for key, value in field_values.items():
            if y < 72:
                c.showPage()
                y = height - 72
                c.setFont("Helvetica", 10)
            label = key.replace("_", " ").title()
            c.drawString(72, y, f"{label}:  {value}")
            y -= 16

        c.save()
