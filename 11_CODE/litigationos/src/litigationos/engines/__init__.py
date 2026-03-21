"""Engines package — business logic for court rules, deadlines, documents, and AI."""

from litigationos.engines.ai_legal_brain import LegalAIBrain
from litigationos.engines.autonomous_income import AutonomousIncomeEngine
from litigationos.engines.case_engine import CaseEngine
from litigationos.engines.court_rules import CourtRulesEngine
from litigationos.engines.deadline import DeadlineEngine
from litigationos.engines.document import DocumentEngine
from litigationos.engines.filing import FilingEngine
from litigationos.engines.filing_assembler import FilingAssembler
from litigationos.engines.filing_factory import FilingFactory
from litigationos.engines.evidence import EvidenceEngine
from litigationos.engines.legal_knowledge import LegalKnowledgeEngine
from litigationos.engines.monetization import MonetizationEngine
from litigationos.engines.onboarding import OnboardingEngine
from litigationos.engines.pdf_production import (
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
from litigationos.engines.rag import RAGEngine
from litigationos.engines.settings import SettingsEngine

__all__ = [
    "AutonomousIncomeEngine",
    "LegalAIBrain",
    "CaseEngine",
    "CourtRulesEngine",
    "DeadlineEngine",
    "DocumentEngine",
    "FilingAssembler",
    "FilingEngine",
    "FilingFactory",
    "EvidenceEngine",
    "LegalKnowledgeEngine",
    "MonetizationEngine",
    "OnboardingEngine",
    "RAGEngine",
    "SettingsEngine",
    # PDF Production functions
    "assemble_filing_package",
    "create_exhibit_cover",
    "create_exhibit_covers_batch",
    "embed_pdf_metadata",
    "fill_pdf_form",
    "generate_toa",
    "generate_toc",
    "get_form_fields",
    "markdown_file_to_pdf",
    "markdown_to_pdf",
    "prepare_for_efiling",
    "stamp_bates_batch",
    "stamp_bates_on_pdf",
]
