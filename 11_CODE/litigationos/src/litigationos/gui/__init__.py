"""GUI package — CustomTkinter desktop interface for LitigationOS."""

from litigationos.gui.agent_dashboard_screen import AgentDashboardFrame
from litigationos.gui.calendar_view import CalendarViewFrame
from litigationos.gui.deadline_dashboard import DeadlineDashboardFrame
from litigationos.gui.document_editor import DocumentEditorFrame
from litigationos.gui.evidence_map import EvidenceMapFrame
from litigationos.gui.filing_audit_screen import FilingAuditFrame
from litigationos.gui.filing_wizard import FilingWizardFrame
from litigationos.gui.filing_wizard_v2 import FilingWizardV2Frame
from litigationos.gui.first_run_wizard import FirstRunWizard
from litigationos.gui.judge_profile import JudgeProfileFrame
from litigationos.gui.legal_brain_screen import LegalBrainFrame
from litigationos.gui.pdf_studio_screen import PDFStudioFrame
from litigationos.gui.pipeline_runner_screen import PipelineRunnerFrame

__all__ = [
    "AgentDashboardFrame",
    "CalendarViewFrame",
    "DeadlineDashboardFrame",
    "DocumentEditorFrame",
    "EvidenceMapFrame",
    "FilingAuditFrame",
    "FilingWizardFrame",
    "FilingWizardV2Frame",
    "FirstRunWizard",
    "JudgeProfileFrame",
    "LegalBrainFrame",
    "PDFStudioFrame",
    "PipelineRunnerFrame",
]
