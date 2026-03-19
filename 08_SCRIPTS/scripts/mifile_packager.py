import os, json, datetime, shutil, subprocess, sys
from typing import Dict, Any, List

try:
    import PyPDF2  # optional
except Exception:
    PyPDF2 = None

from .autodraft import AutoDraftEngine
from .evidence import EvidenceManifest
from .pdf_tools import stamp_pdf
from .scao_autofill import ScaoAutofill
from .compliance import ComplianceValidator

class CaseProfileStore:
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data", "cases")
        os.makedirs(self.data_dir, exist_ok=True)

    def path_for(self, case_id: str) -> str:
        safe = "".join(c for c in case_id if c.isalnum() or c in ("_", "-")).strip()
        return os.path.join(self.data_dir, f"{safe}.json")

    def save(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        case_id = profile.get("case_id") or "default_case"
        path = self.path_for(case_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)
        return {"ok": True, "path": path}

    def load(self, case_id: str) -> Dict[str, Any]:
        path = self.path_for(case_id)
        if not os.path.exists(path):
            return {"ok": False, "error": "not_found", "path": path}
        profile = json.load(open(path, "r", encoding="utf-8"))
        return {"ok": True, "profile": profile, "path": path}

class MiFilePackager:
    def __init__(self):
        self.root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.root, "..", "..", "data")
        self.out_dir = os.path.join(self.data_dir, "mifile")
        os.makedirs(self.out_dir, exist_ok=True)
        self.case_store = CaseProfileStore()

    # ---------- helpers ----------
    def _which(self, exe: str) -> str | None:
        for p in os.environ.get("PATH", "").split(os.pathsep):
            cand = os.path.join(p, exe)
            if os.path.isfile(cand):
                return cand
            if os.name == "nt":
                cand_exe = cand + ".exe"
                if os.path.isfile(cand_exe):
                    return cand_exe
        return None

    def _doc_to_pdf(self, path: str, out_dir: str) -> str:
        base = os.path.splitext(os.path.basename(path))[0]
        out_pdf = os.path.join(out_dir, base + ".pdf")
        if path.lower().endswith(".pdf") and os.path.exists(path):
            # Copy as is
            shutil.copyfile(path, out_pdf)
            return out_pdf
        # Try LibreOffice if available
        soffice = self._which("soffice") or self._which("libreoffice")
        if soffice and os.path.exists(path):
            try:
                subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, path],
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if os.path.exists(out_pdf):
                    return out_pdf
            except Exception as e:
                pass
        # Fallback: create a minimal PDF-like file if no converter (not ideal; user should install LibreOffice)
        with open(out_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n% Minimal placeholder PDF generated; please install LibreOffice for proper conversion.\n")
            f.write(b"%%EOF")
        return out_pdf

    def _stamp_bates(self, pdf_path: str, stamp_text: str) -> str:
        # If PyPDF2 is available, stamp text to each page; otherwise pass-through
        if PyPDF2 is None:
            return pdf_path
        try:
            reader = PyPDF2.PdfReader(open(pdf_path, "rb"))
            writer = PyPDF2.PdfWriter()
            for page in reader.pages:
                # PyPDF2 text stamping is non-trivial without a separate overlay; keep passthrough here.
                writer.add_page(page)
            # TODO: integrate a proper stamping overlay (reportlab) if available.
            with open(pdf_path, "wb") as f:
                writer.write(f)
        except Exception:
            pass
        return pdf_path

    # ---------- main ----------
    def build(self, case_id: str, action: str, prefix: str = "AJB") -> Dict[str, Any]:
        # Ensure case profile exists
        case = self.case_store.load(case_id)
        if not case.get("ok"):
            return {"ok": False, "error": f"case_profile_not_found:{case_id}"}
        profile = case["profile"]

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        job_dir = os.path.join(self.out_dir, f"{case_id}_{action.replace(' ', '_')}_{ts}")
        os.makedirs(job_dir, exist_ok=True)

        # 1) Build fresh draft bundle for this action
        ad = AutoDraftEngine()
        draft = ad.build(action=action, context={})
        draft_dir = draft["dir"]

        # Convert main docs to PDF
        filing_pdf = self._doc_to_pdf(os.path.join(draft_dir, "Draft.docx"), job_dir)
        order_pdf = self._doc_to_pdf(os.path.join(draft_dir, "ProposedOrder.docx"), job_dir)
        pos_pdf = self._doc_to_pdf(os.path.join(draft_dir, "ProofOfService.docx"), job_dir)

        # 2) Ensure Evidence manifest exists
        em = EvidenceManifest()
        mani = em.build(prefix=prefix, start=1)
        mani_path = mani["json"]
        mani_json = json.load(open(mani_path, "r", encoding="utf-8"))
        exhibits_dir = os.path.join(job_dir, "Exhibits")
        os.makedirs(exhibits_dir, exist_ok=True)

        # 3) Build exhibit PDFs (copy/convert and stamp bates)
        exhibits = []
        letter_ord = ord("A")
        for row in mani_json.get("rows", [])[:50]:
            src = row.get("path")
            if not src or not os.path.exists(src):
                continue
            ex_letter = chr(letter_ord)
            letter_ord = letter_ord + 1 if letter_ord < ord("Z") else ord("A")
            short = os.path.splitext(os.path.basename(src))[0][:40]
            out_pdf = self._doc_to_pdf(src, exhibits_dir)
            stamped_path = os.path.join(exhibits_dir, f"_stamped_{ex_letter}.pdf"); stamp_pdf(out_pdf, stamped_path, bottom_right=row.get('bates'), top_right=f"Ex. {ex_letter}"); stamped = stamped_path
            out_name = f"Ex_{ex_letter}_{short}.pdf"
            final_path = os.path.join(exhibits_dir, out_name)
            try:
                shutil.move(stamped, final_path)
            except Exception:
                shutil.copyfile(stamped, final_path)
            exhibits.append({"letter": ex_letter, "bates": row.get("bates"), "path": final_path})

        # 4) Forms autofill — placeholder: create a forms checklist using forms referenced by AutoDraft
        forms_dir = os.path.join(job_dir, "Forms")
        os.makedirs(forms_dir, exist_ok=True)
        forms_
        # 4.5) SCAO Autofill sidecars (FDF + JSON) for common forms
        sc = ScaoAutofill()
        scao_out = os.path.join(job_dir, "Forms")
        sc_results = []
        for fid in ["MC01","MC12","FOC65","FOC88"]:
            try:
                sc_results.append(sc.generate_for(fid, profile, action, scao_out))
            except Exception as e:
                sc_results.append({"ok": False, "error": str(e), "form_id": fid})

        # 4.8) Compliance
        cv = ComplianceValidator()
        compliance = cv.validate(filing_pdf, order_pdf, pos_pdf)
    manifest = {
            "note": "Provide SCAO PDF templates in backend/templates/scao_forms/ to enable autofill mapping.",
            "forms": draft.get("forms", [])
        }
        with open(os.path.join(forms_dir, "forms_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(forms_manifest, f, ensure_ascii=False, indent=2)

        # 5) Compliance report — structural checks
        report = {
            "case_id": case_id,
            "action": action,
            "files": {
                "Main_Filing.pdf": os.path.basename(filing_pdf),
                "Proposed_Order.pdf": os.path.basename(order_pdf),
                "Proof_of_Service.pdf": os.path.basename(pos_pdf),
                "Exhibits": len(exhibits),
                "Forms": len(forms_manifest.get("forms", []))
            },
            "scao": sc_results,
            "compliance": compliance,
            "warnings": [
                "PDF conversion used local environment; install LibreOffice for high-fidelity DOCX→PDF.",
                "Bates stamping requires PyPDF2+reportlab overlay for visible stamps (pass-through used if unavailable).",
                "SCAO autofill requires templates; see docs."
            ]
        }

        # 6) Assemble MiFILE ZIP
        fl_dir = os.path.join(job_dir, "Filing")
        os.makedirs(fl_dir, exist_ok=True)
        shutil.copyfile(filing_pdf, os.path.join(fl_dir, "Main_Filing.pdf"))
        shutil.copyfile(order_pdf, os.path.join(fl_dir, "Proposed_Order.pdf"))
        shutil.copyfile(pos_pdf, os.path.join(fl_dir, "Proof_of_Service.pdf"))
        # Exhibits and Forms already in subfolders

        manifest = {
            "built_at": datetime.datetime.now().isoformat(),
            "case_profile_path": self.case_store.path_for(case_id),
            "action": action,
            "structure": {
                "Filing": ["Main_Filing.pdf", "Proposed_Order.pdf", "Proof_of_Service.pdf"],
                "Exhibits_dir": exhibits_dir,
                "Forms_dir": forms_dir
            },
            "report": report
        }
        with open(os.path.join(job_dir, "filing_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        zip_path = os.path.join(self.out_dir, f"{case_id}_{action.replace(' ', '_')}_{ts}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(job_dir):
                for n in files:
                    p = os.path.join(root, n)
                    z.write(p, arcname=os.path.relpath(p, job_dir))

        return {"ok": True, "zip_path": zip_path, "job_dir": job_dir, "report": report}
