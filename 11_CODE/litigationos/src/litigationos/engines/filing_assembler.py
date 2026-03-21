"""Filing Assembler — one-click court-ready PDF package generation.

Orchestrates: legal knowledge lookup → template rendering → PDF generation
→ court form filling → exhibit covers → Bates stamping → merge → metadata.
"""

import json
import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from litigationos.engines.legal_knowledge import LegalKnowledgeEngine
from litigationos.engines.pdf_production import (
    assemble_filing_package,
    create_exhibit_cover,
    embed_pdf_metadata,
    fill_pdf_form,
    get_form_fields,
    markdown_to_pdf,
    stamp_bates_on_pdf,
)

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(r"C:\Users\andre\LitigationOS\litigation_context.db")
_DEFAULT_OUTPUT = Path(r"C:\Users\andre\LitigationOS\COURT_READY")
_COURT_FORMS_DB = Path(r"C:\Users\andre\LitigationOS\databases\court_forms.db")

# Verified party identity — the ONLY source of truth
_PARTIES = {
    "plaintiff": {
        "name": "Andrew James Pigors",
        "address": "1977 Whitehall Road, Lot 17, North Muskegon, MI 49445",
        "phone": "(231) 903-5690",
        "email": "andrewjpigors@gmail.com",
    },
    "defendant": {
        "name": "Emily A. Watson",
        "address": "2160 Garland Drive, Norton Shores, MI 49441",
    },
    "defendant_attorney": {
        "name": "Jennifer Barnes",
        "bar": "P55406",
        "firm": "Barnes Law Firm PLLC",
        "address": "880 Jefferson St Ste B, Muskegon, MI 49440",
        "status": "WITHDREW",
    },
    "foc": {
        "name": "Pamela Rusco",
        "title": "Friend of the Court",
        "address": "990 Terrace St, Muskegon, MI 49442",
    },
    "judge": {
        "name": "Hon. Jenny L. McNeill",
        "court": "14th Circuit Court, Family Division",
    },
}

_DEFAULT_CASE_NUMBER = "2024-001507-DC"


class FilingAssembler:
    """Orchestrate full filing pipeline from claim/filing ID to court-ready PDF."""

    def __init__(
        self,
        db_path: str | Path | None = None,
        output_dir: str | Path | None = None,
    ) -> None:
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        self.output_dir = Path(output_dir) if output_dir else _DEFAULT_OUTPUT
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.legal = LegalKnowledgeEngine(self.db_path)
        logger.info("FilingAssembler ready  db=%s  out=%s", self.db_path, self.output_dir)

    # ── DB helpers ──────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=60)
        conn.execute("PRAGMA busy_timeout=60000")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA cache_size=-32000")
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
        return (
            conn.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
                (name,),
            ).fetchone()[0]
            > 0
        )

    # ── 1. get_filing_config ────────────────────────────────────────

    def get_filing_config(self, filing_id: str) -> Dict[str, Any]:
        """Return filing metadata from the DB, or a template dict if unavailable."""
        conn = self._connect()
        try:
            # Try filing_readiness first, then filings
            for table in ("filing_readiness", "filings"):
                if self._table_exists(conn, table):
                    cols = [
                        r["name"]
                        for r in conn.execute(f"PRAGMA table_info({table})").fetchall()
                    ]
                    id_col = "filing_id" if "filing_id" in cols else "id"
                    row = conn.execute(
                        f"SELECT * FROM {table} WHERE {id_col} = ?", (filing_id,)
                    ).fetchone()
                    if row:
                        return dict(row)

            # Fallback — derive from filing_rule_map if it exists
            title = filing_id
            lane = "A_CUSTODY"
            if self._table_exists(conn, "filing_rule_map"):
                first = conn.execute(
                    "SELECT requirement FROM filing_rule_map WHERE filing_id = ? LIMIT 1",
                    (filing_id,),
                ).fetchone()
                if first:
                    title = f"Filing {filing_id}: {first['requirement'][:80]}"

            return {
                "filing_id": filing_id,
                "title": title,
                "lane": lane,
                "case_number": _DEFAULT_CASE_NUMBER,
                "status": "draft",
            }
        except Exception as exc:
            logger.warning("get_filing_config error: %s", exc)
            return {
                "filing_id": filing_id,
                "title": filing_id,
                "lane": "A_CUSTODY",
                "case_number": _DEFAULT_CASE_NUMBER,
                "status": "draft",
            }
        finally:
            conn.close()

    # ── 2. get_required_forms ───────────────────────────────────────

    def get_required_forms(self, filing_id: str) -> List[Dict[str, Any]]:
        """Return required authorities and SCAO court forms for a filing."""
        forms: List[Dict[str, Any]] = []
        conn = self._connect()
        try:
            # Authorities from filing_rule_map
            if self._table_exists(conn, "filing_rule_map"):
                rows = conn.execute(
                    "SELECT authority_type, authority_number, requirement, mandatory "
                    "FROM filing_rule_map WHERE filing_id = ? ORDER BY mandatory DESC",
                    (filing_id,),
                ).fetchall()
                for r in rows:
                    forms.append(
                        {
                            "form_id": f"{r['authority_type']}_{r['authority_number']}",
                            "form_number": r["authority_number"],
                            "form_name": r["requirement"] or r["authority_number"],
                            "required": bool(r["mandatory"]),
                        }
                    )

            # SCAO court forms from court_forms.db (if available)
            if _COURT_FORMS_DB.exists():
                try:
                    cf_conn = sqlite3.connect(str(_COURT_FORMS_DB), timeout=30)
                    cf_conn.execute("PRAGMA busy_timeout=30000")
                    cf_conn.row_factory = sqlite3.Row
                    for tbl in ("court_forms", "forms"):
                        try:
                            cf_rows = cf_conn.execute(
                                f"SELECT * FROM {tbl} WHERE filing_type LIKE ? "
                                f"OR description LIKE ? LIMIT 10",
                                (f"%{filing_id}%", f"%{filing_id}%"),
                            ).fetchall()
                            for cr in cf_rows:
                                d = dict(cr)
                                forms.append(
                                    {
                                        "form_id": d.get("form_id", d.get("id", "")),
                                        "form_number": d.get("form_number", ""),
                                        "form_name": d.get("name", d.get("description", "")),
                                        "required": True,
                                    }
                                )
                        except sqlite3.OperationalError:
                            continue
                    cf_conn.close()
                except Exception as exc:
                    logger.debug("court_forms.db lookup failed: %s", exc)

            # Deduplicate by form_number
            seen: set[str] = set()
            unique: List[Dict[str, Any]] = []
            for f in forms:
                key = f["form_number"]
                if key not in seen:
                    seen.add(key)
                    unique.append(f)
            return unique

        except Exception as exc:
            logger.warning("get_required_forms error: %s", exc)
            return forms
        finally:
            conn.close()

    # ── 3. get_exhibit_list ─────────────────────────────────────────

    def get_exhibit_list(self, filing_id: str) -> List[Dict[str, Any]]:
        """Return exhibits linked to a filing from evidence_quotes."""
        exhibits: List[Dict[str, Any]] = []
        conn = self._connect()
        try:
            if not self._table_exists(conn, "evidence_quotes"):
                return exhibits

            # Verify columns before querying
            cols = {
                r["name"]
                for r in conn.execute("PRAGMA table_info(evidence_quotes)").fetchall()
            }

            # Try filing_refs first (JSON array of filing IDs)
            rows = []
            if "filing_refs" in cols:
                rows = conn.execute(
                    "SELECT DISTINCT source_file, quote_text "
                    "FROM evidence_quotes "
                    "WHERE filing_refs LIKE ? LIMIT 20",
                    (f"%{filing_id}%",),
                ).fetchall()

            # Fallback: try tags column
            if not rows and "tags" in cols:
                rows = conn.execute(
                    "SELECT DISTINCT source_file, quote_text "
                    "FROM evidence_quotes "
                    "WHERE tags LIKE ? LIMIT 20",
                    (f"%{filing_id}%",),
                ).fetchall()

            # Last resort: try category or lane
            if not rows and "lane" in cols:
                rows = conn.execute(
                    "SELECT DISTINCT source_file, quote_text "
                    "FROM evidence_quotes "
                    "WHERE lane IS NOT NULL LIMIT 20",
                ).fetchall()

            for idx, r in enumerate(rows, start=1):
                label = chr(64 + idx) if idx <= 26 else f"EX-{idx}"
                source = r["source_file"] or ""
                exhibits.append(
                    {
                        "label": f"Exhibit {label}",
                        "title": Path(source).stem[:60] if source else f"Exhibit {label}",
                        "source_path": source,
                        "bates_range": "",
                    }
                )
            return exhibits
        except Exception as exc:
            logger.warning("get_exhibit_list error: %s", exc)
            return exhibits
        finally:
            conn.close()

    # ── 4. generate_certificate_of_service ──────────────────────────

    def generate_certificate_of_service(
        self,
        parties: Optional[List[Dict[str, str]]] = None,
        method: str = "electronic",
        filing_date: Optional[str] = None,
    ) -> str:
        """Generate Certificate of Service markdown text."""
        date_str = filing_date or datetime.now().strftime("%B %d, %Y")

        if parties is None:
            parties = [
                {
                    "name": _PARTIES["defendant"]["name"],
                    "via": f"Jennifer Barnes (P55406), Barnes Law Firm PLLC, "
                    f"880 Jefferson St Ste B, Muskegon, MI 49440",
                },
                {
                    "name": _PARTIES["foc"]["name"],
                    "via": "Friend of the Court, 990 Terrace St, Muskegon, MI 49442",
                },
            ]

        method_text = {
            "electronic": "electronic filing / e-mail",
            "personal": "personal service",
            "mail": "first-class U.S. Mail, postage prepaid",
        }.get(method, method)

        lines = [
            "# CERTIFICATE OF SERVICE",
            "",
            f"I, **Andrew James Pigors**, hereby certify that on **{date_str}**, "
            f"I served a true and correct copy of the foregoing document upon the "
            f"following parties by **{method_text}**:",
            "",
        ]

        for p in parties:
            lines.append(f"- **{p['name']}**")
            if p.get("via"):
                lines.append(f"  c/o {p['via']}")
            lines.append("")

        lines.extend(
            [
                "---",
                "",
                f"Dated: {date_str}",
                "",
                "Signature: /s/ Andrew James Pigors",
                "",
                "Andrew James Pigors, Pro Se",
                "1977 Whitehall Road, Lot 17",
                "North Muskegon, MI 49445",
                "(231) 903-5690",
            ]
        )
        return "\n".join(lines)

    # ── 5. assemble ─────────────────────────────────────────────────

    def assemble(
        self,
        filing_id: str,
        main_content: str | Path,
        exhibits: Optional[List[Dict[str, Any]]] = None,
        include_cos: bool = True,
        include_forms: bool = True,
        bates_start: int = 1,
    ) -> Dict[str, Any]:
        """Orchestrate full filing assembly from content to court-ready PDF.

        Returns dict with output_dir, main_pdf, package_pdf, manifest,
        page_count, bates_range, and forms_needed.
        """
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pkg_dir = self.output_dir / f"{filing_id}_{ts}"
        pkg_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Assembling %s → %s", filing_id, pkg_dir)

        config = self.get_filing_config(filing_id)
        case_number = config.get("case_number", _DEFAULT_CASE_NUMBER)
        result: Dict[str, Any] = {
            "output_dir": str(pkg_dir),
            "filing_id": filing_id,
            "config": config,
        }

        # ── Main document → PDF ─────────────────────────────────────
        main_pdf = pkg_dir / "main_document.pdf"
        try:
            content_path = Path(main_content) if not isinstance(main_content, Path) else main_content
            if content_path.exists() and content_path.suffix == ".md":
                md_text = content_path.read_text(encoding="utf-8")
                markdown_to_pdf(md_text, main_pdf, title=config.get("title", filing_id))
            elif content_path.exists() and content_path.suffix == ".pdf":
                shutil.copy2(content_path, main_pdf)
            else:
                # Treat as raw markdown string
                markdown_to_pdf(
                    str(main_content), main_pdf, title=config.get("title", filing_id)
                )
        except (OSError, ValueError):
            # main_content is a markdown string (not a valid path)
            markdown_to_pdf(
                str(main_content), main_pdf, title=config.get("title", filing_id)
            )
        result["main_pdf"] = str(main_pdf)

        # ── Certificate of Service ──────────────────────────────────
        cos_pdf = None
        if include_cos:
            try:
                cos_md = self.generate_certificate_of_service()
                cos_pdf = pkg_dir / "certificate_of_service.pdf"
                markdown_to_pdf(cos_md, cos_pdf, title="Certificate of Service")
                result["cos_pdf"] = str(cos_pdf)
            except Exception as exc:
                logger.warning("COS generation failed: %s", exc)

        # ── Exhibits ────────────────────────────────────────────────
        if exhibits is None:
            exhibits = self.get_exhibit_list(filing_id)

        exhibit_dicts: List[Dict[str, Any]] = []
        for ex in exhibits:
            src = ex.get("source_path", "")
            if src and Path(src).exists():
                exhibit_dicts.append(
                    {
                        "label": ex.get("label", "Exhibit"),
                        "title": ex.get("title", "Exhibit"),
                        "path": src,
                    }
                )

        # ── Assemble package ────────────────────────────────────────
        package_pdf = pkg_dir / f"{filing_id}_COMPLETE.pdf"
        # Build the list of PDFs to merge via assemble_filing_package
        all_exhibits = list(exhibit_dicts)
        if cos_pdf and cos_pdf.exists():
            all_exhibits.append(
                {
                    "label": "Certificate of Service",
                    "title": "Certificate of Service",
                    "path": str(cos_pdf),
                }
            )

        try:
            pkg_result = assemble_filing_package(
                main_document=main_pdf,
                exhibits=all_exhibits,
                output_pdf=package_pdf,
                case_number=case_number,
                bates_prefix="PIGORS",
                bates_start=bates_start,
                add_covers=bool(exhibit_dicts),
                add_bates=True,
            )
            result["package_pdf"] = str(package_pdf)
            result["page_count"] = pkg_result.get("page_count", 0)
            result["bates_range"] = pkg_result.get("bates_range", "")
        except Exception as exc:
            logger.warning("Package assembly failed, falling back to main PDF: %s", exc)
            result["package_pdf"] = str(main_pdf)
            result["page_count"] = 0
            result["bates_range"] = ""

        # ── Metadata ────────────────────────────────────────────────
        try:
            target = Path(result["package_pdf"])
            if target.exists():
                embed_pdf_metadata(
                    target,
                    target,
                    title=config.get("title", filing_id),
                    author="Andrew James Pigors",
                    subject=f"Case {case_number}",
                )
        except Exception as exc:
            logger.debug("Metadata embed skipped: %s", exc)

        # ── Forms needed ────────────────────────────────────────────
        forms_needed: List[Dict[str, Any]] = []
        if include_forms:
            forms_needed = self.get_required_forms(filing_id)
        result["forms_needed"] = forms_needed

        # ── Manifest ────────────────────────────────────────────────
        manifest = {
            "filing_id": filing_id,
            "created": ts,
            "case_number": case_number,
            "files": {
                "main_pdf": str(main_pdf),
                "package_pdf": result.get("package_pdf", ""),
                "cos_pdf": str(cos_pdf) if cos_pdf else None,
            },
            "page_count": result.get("page_count", 0),
            "bates_range": result.get("bates_range", ""),
            "forms_needed": forms_needed,
            "exhibit_count": len(exhibit_dicts),
        }
        manifest_path = pkg_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")
        result["manifest"] = str(manifest_path)

        logger.info(
            "Assembly complete: %s  pages=%s  bates=%s",
            filing_id,
            result.get("page_count"),
            result.get("bates_range"),
        )
        return result

    # ── 6. quick_assemble ───────────────────────────────────────────

    def quick_assemble(self, filing_id: str, markdown_text: str) -> Path:
        """Simplified one-call assembly with all defaults. Returns path to final PDF."""
        result = self.assemble(
            filing_id=filing_id,
            main_content=markdown_text,
            exhibits=None,
            include_cos=True,
            include_forms=True,
        )
        return Path(result.get("package_pdf", result.get("main_pdf", "")))
