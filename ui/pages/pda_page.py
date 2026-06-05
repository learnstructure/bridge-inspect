
# ui/pages/pda_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget

# Import the page widgets
from .pda.damage_state_page import DamageStateEditorPage
from .pda.analysis_page import AnalysisPage
from .pda.correction_page import CorrectionPage
from .pda.summary_report_page import SummaryReportPage

from controllers.pda_controller import PDAController

class PDAPage(QWidget):
    """A container for the multi-page PDA module, managed externally."""
    def __init__(self):
        super().__init__()
        # The layout is now simpler, just the stack
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # --- Controller ---
        self.controller = PDAController()

        # --- Create and Add Pages ---
        self.damage_states_page = DamageStateEditorPage()
        self.analysis_page = AnalysisPage()
        self.correction_page = CorrectionPage()
        self.report_page = SummaryReportPage()

        # Set up controllers for pages
        self.damage_states_page.set_controller(self.controller)
        self.analysis_page.set_controller(self.controller)
        self.correction_page.set_controller(self.controller)
        # Link views back to the controller
        self.controller.set_view(self.analysis_page, self.correction_page, self.report_page)

        # Add widgets to the stack and store their keys/indices
        self.page_indices = {
            "pda_rules": self.stacked_widget.addWidget(self.damage_states_page),
            "pda_analysis": self.stacked_widget.addWidget(self.analysis_page),
            "pda_correction": self.stacked_widget.addWidget(self.correction_page),
            "pda_report": self.stacked_widget.addWidget(self.report_page)
        }

    def set_current_page_by_key(self, key):
        """Sets the visible sub-page using a string key."""
        if key in self.page_indices:
            index = self.page_indices[key]
            self.stacked_widget.setCurrentIndex(index)
