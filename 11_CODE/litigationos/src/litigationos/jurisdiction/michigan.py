"""Michigan jurisdiction plugin for LitigationOS.

Implements JurisdictionPlugin with real court data for the Michigan courts
relevant to the Pigors v. Watson litigation:
  - 14th Circuit Court (Muskegon County — Family Division)
  - 60th District Court (Muskegon County)
  - Michigan Court of Appeals (COA)
  - Michigan Supreme Court (MSC)
"""

from typing import Dict, List

from litigationos.jurisdiction.base import JurisdictionInfo, JurisdictionPlugin


# Court identifiers used throughout LitigationOS
COURT_14TH_CIRCUIT = "14th-circuit"
COURT_60TH_DISTRICT = "60th-district"
COURT_COA = "coa"
COURT_MSC = "msc"

_COURT_RULES: Dict[str, Dict] = {
    COURT_14TH_CIRCUIT: {
        "name": "14th Circuit Court — Muskegon County",
        "division": "Family Division",
        "rule_set": "MCR (Michigan Court Rules)",
        "local_rules": "14th Circuit Local Administrative Orders",
        "efiling": "MiFILE",
        "address": "990 Terrace St, Muskegon, MI 49442",
        "judge": "Hon. Jenny L. McNeill",
        "key_rules": [
            "MCR 2.003 — Disqualification of Judge",
            "MCR 2.107 — Service of Pleadings",
            "MCR 2.119 — Motion Practice",
            "MCR 3.206 — Domestic Relations — Initiating a Case",
            "MCR 3.210 — Hearings and Trials",
            "MCR 3.211 — Determination of Support",
            "MCR 3.214 — Domestic Relations Referees",
        ],
    },
    COURT_60TH_DISTRICT: {
        "name": "60th District Court — Muskegon County",
        "rule_set": "MCR (Michigan Court Rules)",
        "local_rules": "60th District Local Administrative Orders",
        "efiling": "MiFILE",
        "address": "990 Terrace St, Muskegon, MI 49442",
        "key_rules": [
            "MCR 2.107 — Service of Pleadings",
            "MCR 4.201 — Summary Proceedings to Recover Possession of Premises",
        ],
    },
    COURT_COA: {
        "name": "Michigan Court of Appeals",
        "rule_set": "MCR Chapter 7",
        "local_rules": "COA Internal Operating Procedures (IOP)",
        "efiling": "MiFILE / TrueFiling",
        "address": "Cadillac Place, 3020 W Grand Blvd, Detroit, MI 48202",
        "key_rules": [
            "MCR 7.201 — Applicability",
            "MCR 7.202 — Definitions",
            "MCR 7.204 — Filing Appeal of Right",
            "MCR 7.205 — Application for Leave to Appeal",
            "MCR 7.210 — Record on Appeal",
            "MCR 7.212 — Briefs",
            "MCR 7.215 — Opinions, Orders, Judgments",
        ],
    },
    COURT_MSC: {
        "name": "Michigan Supreme Court",
        "rule_set": "MCR Chapter 7",
        "local_rules": "MSC Internal Operating Procedures",
        "efiling": "MiFILE / TrueFiling",
        "address": "925 W Ottawa St, Lansing, MI 48915",
        "key_rules": [
            "MCR 7.301 — Applicability",
            "MCR 7.303 — Application for Leave to Appeal",
            "MCR 7.305 — Original Proceedings",
            "MCR 7.306 — Extraordinary Writs",
            "MCR 7.310 — Briefs and Appendixes",
        ],
    },
}

_FILING_REQUIREMENTS: Dict[str, Dict[str, Dict]] = {
    COURT_14TH_CIRCUIT: {
        "motion": {
            "format": "8.5 x 11 paper, double-spaced, 12pt font min",
            "required_fields": ["caption", "case_number", "motion_title", "prayer_for_relief"],
            "attachments": ["brief_in_support", "proposed_order", "proof_of_service"],
            "hearing_notice": "MCR 2.119(C) — 9 days before hearing (personal), 14 days (mail)",
            "efiling_format": "PDF/A, max 25 MB per document",
            "fee": "Varies — check court schedule",
        },
        "brief": {
            "format": "8.5 x 11, double-spaced, 12pt proportional or 10pt monospaced",
            "required_fields": ["caption", "case_number", "statement_of_facts", "argument", "relief_requested"],
            "page_limit": "No fixed limit at circuit level (but be reasonable)",
            "efiling_format": "PDF/A, max 25 MB",
            "fee": "None (included with motion)",
        },
        "complaint": {
            "format": "8.5 x 11, double-spaced, 12pt font min",
            "required_fields": ["caption", "parties", "jurisdiction", "factual_allegations", "claims", "prayer_for_relief"],
            "attachments": ["summons", "civil_cover_sheet"],
            "fee": "$175 filing fee (civil) — verify with clerk",
            "service": "MCR 2.105 — personal service required for initial complaint",
        },
    },
    COURT_COA: {
        "motion": {
            "format": "MCR 7.211 format requirements",
            "required_fields": ["caption", "coa_case_number", "motion_title", "supporting_brief"],
            "attachments": ["proof_of_service", "lower_court_order"],
            "efiling_format": "PDF, filed via TrueFiling or MiFILE",
            "fee": "Varies",
        },
        "brief": {
            "format": "MCR 7.212 — max 50 pages (proportional) or 16,000 words",
            "required_fields": [
                "table_of_contents",
                "index_of_authorities",
                "statement_of_jurisdiction",
                "statement_of_questions",
                "statement_of_facts",
                "argument",
                "relief_requested",
            ],
            "attachments": ["proof_of_service", "appendix_per_mcr_7.212(H)"],
            "page_limit": "50 pages (proportional) or 16,000 words",
            "font": "Proportional 12pt minimum, or monospaced 10pt",
            "fee": "None separate",
        },
        "application_leave": {
            "format": "MCR 7.205",
            "required_fields": ["caption", "statement_of_judgment", "statement_of_facts", "argument"],
            "attachments": [
                "copy_of_judgment_or_order",
                "proof_of_service",
                "copy_of_opinion_if_any",
            ],
            "deadline": "21 days from entry of order being appealed",
            "fee": "$375 filing fee",
        },
    },
    COURT_MSC: {
        "application_leave": {
            "format": "MCR 7.303",
            "required_fields": ["caption", "questions_presented", "statement_of_facts", "argument"],
            "attachments": [
                "coa_opinion_and_order",
                "lower_court_judgment",
                "proof_of_service",
            ],
            "deadline": "42 days from COA decision",
            "page_limit": "50 pages",
            "fee": "$375 filing fee",
        },
    },
    COURT_60TH_DISTRICT: {
        "motion": {
            "format": "8.5 x 11, double-spaced, 12pt font",
            "required_fields": ["caption", "case_number", "motion_title"],
            "efiling_format": "PDF/A via MiFILE",
            "fee": "Varies — check court schedule",
        },
    },
}


class MichiganJurisdiction(JurisdictionPlugin):
    """Michigan jurisdiction plugin with real court data."""

    def get_info(self) -> JurisdictionInfo:
        return JurisdictionInfo(
            state="Michigan",
            courts=[
                COURT_14TH_CIRCUIT,
                COURT_60TH_DISTRICT,
                COURT_COA,
                COURT_MSC,
            ],
            rules_db="mcr_rules.db",
            forms_db="court_forms.db",
            statutes_prefix="MCL",
        )

    def get_court_rules(self, court: str) -> Dict:
        rules = _COURT_RULES.get(court)
        if rules is None:
            return {"error": f"Unknown court: {court}", "available": list(_COURT_RULES.keys())}
        return dict(rules)

    def get_filing_requirements(self, court: str, filing_type: str) -> Dict:
        court_reqs = _FILING_REQUIREMENTS.get(court, {})
        reqs = court_reqs.get(filing_type)
        if reqs is None:
            return {
                "error": f"No requirements for filing_type='{filing_type}' in court='{court}'",
                "available_courts": list(_FILING_REQUIREMENTS.keys()),
                "available_types": list(court_reqs.keys()) if court_reqs else [],
            }
        return dict(reqs)

    def validate_filing(self, filing: dict) -> List[str]:
        """Validate a filing dict against Michigan rules.

        Checks for required fields based on court and filing_type.
        Returns list of error strings (empty = valid).
        """
        errors: List[str] = []

        court = filing.get("court")
        if not court:
            errors.append("Missing required field: 'court'")
            return errors

        filing_type = filing.get("filing_type")
        if not filing_type:
            errors.append("Missing required field: 'filing_type'")
            return errors

        reqs = self.get_filing_requirements(court, filing_type)
        if "error" in reqs:
            errors.append(reqs["error"])
            return errors

        for field_name in reqs.get("required_fields", []):
            if not filing.get(field_name):
                errors.append(f"Missing required field: '{field_name}'")

        if not filing.get("case_number") and court != COURT_MSC:
            errors.append("Missing 'case_number' (required for all non-MSC filings)")

        if court == COURT_COA:
            if filing_type == "brief":
                word_count = filing.get("word_count", 0)
                if word_count > 16000:
                    errors.append(
                        f"Brief exceeds 16,000 word limit (MCR 7.212): {word_count} words"
                    )
                page_count = filing.get("page_count", 0)
                if page_count > 50:
                    errors.append(
                        f"Brief exceeds 50-page limit (MCR 7.212): {page_count} pages"
                    )

        return errors
