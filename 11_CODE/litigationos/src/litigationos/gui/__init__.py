"""GUI package — CustomTkinter desktop interface for LitigationOS."""

from litigationos.gui.calendar_view import CalendarViewFrame
from litigationos.gui.deadline_dashboard import DeadlineDashboardFrame
from litigationos.gui.document_editor import DocumentEditorFrame
from litigationos.gui.evidence_map import EvidenceMapFrame
from litigationos.gui.filing_wizard import FilingWizardFrame

__all__ = [
    "CalendarViewFrame",
    "DeadlineDashboardFrame",
    "DocumentEditorFrame",
    "EvidenceMapFrame",
    "FilingWizardFrame",
]
