# ui/pages/pda_page.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QStackedWidget, QListWidget

# Import the new, separated page widgets
from .pda.damage_state_page import DamageStateEditorPage
from .pda.analysis_page import AnalysisPage
from .pda.correction_page import CorrectionPage  # Updated import
from .pda.summary_report_page import SummaryReportPage

from controllers.pda_controller import PDAController

class PDAPage(QWidget):
    """The main container for the multi-page PDA module."""
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Sidebar Navigation ---
        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(200)
        layout.addWidget(self.nav_list)

        # --- Content Pages ---
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)

        # --- Controller ---
        self.controller = PDAController()

        # --- Create and Add Pages ---
        self.damage_states_page = DamageStateEditorPage()
        self.analysis_page = AnalysisPage()
        self.correction_page = CorrectionPage()  # Updated class
        self.report_page = SummaryReportPage()

        # Set up controllers for pages that need them
        self.damage_states_page.set_controller(self.controller)
        self.analysis_page.set_controller(self.controller)
        self.correction_page.set_controller(self.controller)
        # The controller needs a reference to the views to send data back
        self.controller.set_view(self.analysis_page, self.correction_page, self.report_page)

        # Add widgets to the stack
        self.stacked_widget.addWidget(self.damage_states_page)
        self.stacked_widget.addWidget(self.analysis_page)
        self.stacked_widget.addWidget(self.correction_page)
        self.stacked_widget.addWidget(self.report_page)

        # Add items to nav list in the desired order
        self.nav_list.addItem("Damage State Rules")
        self.nav_list.addItem("PDA Analysis")
        self.nav_list.addItem("Correction")  # Updated tab name
        self.nav_list.addItem("Summary Report")

        # Connect navigation
        self.nav_list.currentRowChanged.connect(self.stacked_widget.setCurrentIndex)
        
        # Set the initial page
        self.nav_list.setCurrentRow(0)
