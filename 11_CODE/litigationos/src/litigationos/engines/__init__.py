"""Engines package — business logic for court rules, deadlines, documents, and AI."""

from litigationos.engines.branding import BrandingEngine
from litigationos.engines.authority_chain import AuthorityChainEngine
from litigationos.engines.dashboard import DashboardEngine
from litigationos.engines.ai_legal_brain import LegalAIBrain
from litigationos.engines.autonomous_income import AutonomousIncomeEngine
from litigationos.engines.case_engine import CaseEngine
from litigationos.engines.court_form_filler import CourtFormFiller
from litigationos.engines.court_rules import CourtRulesEngine
from litigationos.engines.deadline import DeadlineEngine
from litigationos.engines.document import DocumentEngine
from litigationos.engines.filing import FilingEngine
from litigationos.engines.filing_assembler import FilingAssembler
from litigationos.engines.filing_factory import FilingFactory
from litigationos.engines.evidence import EvidenceEngine
from litigationos.engines.irac_engine import IRACEngine
from litigationos.engines.legal_knowledge import LegalKnowledgeEngine
from litigationos.engines.license_manager import LicenseManager
from litigationos.engines.monetization import MonetizationEngine
from litigationos.engines.motion_templates import MotionTemplateEngine
from litigationos.engines.emergency_motions import EmergencyMotionEngine
from litigationos.engines.notifications import NotificationEngine
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
from litigationos.engines.discovery_generator import DiscoveryGenerator
from litigationos.engines.mcp_bridge import MCPBridge
from litigationos.engines.rag import RAGEngine
from litigationos.engines.security import SecurityEngine
from litigationos.engines.settings import SettingsEngine
from litigationos.engines.witness_prep import WitnessEngine

__all__ = [
    "BrandingEngine",
    "AuthorityChainEngine",
    "DashboardEngine",
    "AutonomousIncomeEngine",
    "LegalAIBrain",
    "CaseEngine",
    "CourtFormFiller",
    "CourtRulesEngine",
    "DeadlineEngine",
    "DiscoveryGenerator",
    "DocumentEngine",
    "FilingAssembler",
    "FilingEngine",
    "FilingFactory",
    "EvidenceEngine",
    "IRACEngine",
    "LegalKnowledgeEngine",
    "LicenseManager",
    "MCPBridge",
    "MonetizationEngine",
    "MotionTemplateEngine",
    "EmergencyMotionEngine",
    "NotificationEngine",
    "OnboardingEngine",
    "RAGEngine",
    "SecurityEngine",
    "SettingsEngine",
    "WitnessEngine",
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
