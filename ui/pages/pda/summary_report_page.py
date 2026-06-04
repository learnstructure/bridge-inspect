# ui/pages/pda/summary_report_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QLabel, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from ui.widgets.image_viewer import ImageViewer
from ui.widgets.results_panel import ResultsPanel  # Import the new panel

class SummaryReportPage(QWidget):
    """A page to display a comprehensive summary of the PDA results, now using ResultsPanel."""
    def __init__(self):
        super().__init__()
        self.controller = None
        
        main_layout = QVBoxLayout(self)

        title = QLabel("<h2>PDA Summary Report</h2>")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)

        self.image_viewer = ImageViewer()
        self.image_viewer.setReadOnly(True)

        right_panel_widget = QWidget()
        results_panel_layout = QVBoxLayout(right_panel_widget)
        
        self.results_panel = ResultsPanel(is_editable=False)

        self.notes_area = QTextEdit()
        self.notes_area.setPlaceholderText("Add any final notes or observations for the report...")

        results_panel_layout.addWidget(self.results_panel)
        results_panel_layout.addWidget(QLabel("<h4>Notes</h4>"))
        results_panel_layout.addWidget(self.notes_area)

        splitter.addWidget(self.image_viewer)
        splitter.addWidget(right_panel_widget)
        splitter.setSizes([600, 400])

        main_layout.addWidget(splitter)

        button_layout = QHBoxLayout()
        self.save_report_btn = QPushButton("Save Report")
        self.save_report_btn.clicked.connect(self.save_report)
        button_layout.addStretch()
        button_layout.addWidget(self.save_report_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def set_controller(self, controller):
        self.controller = controller

    def update_summary(self, results):
        """Populates the summary page with results and the overlay image."""
        self.results_panel.update_results(results)

        if not results:
            self.image_viewer.clear_image()
            self.notes_area.clear()
            return

        if "overlay_image" in results and results["overlay_image"] is not None:
            self.image_viewer.load_image(results["overlay_image"], is_np_array=True)
        else:
            self.image_viewer.clear_image()

    def save_report(self):
        """Saves the summary report content to a text file."""
        damage_level = self.results_panel.damage_level_display.text()
        
        if not damage_level:
            QMessageBox.warning(self, "Warning", "There is no report to save. Please run an analysis first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "pda_summary_report.txt", "Text Files (*.txt);;All Files (*)")

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("           PDA SUMMARY REPORT\n")
                    f.write("="*40 + "\n\n")
                    f.write(f"Final Damage State: {damage_level}\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Spalled Ratio (%): {self.results_panel.spalled_ratio_input.text()}\n")
                    f.write(f"Exposed Horizontal Bars: {self.results_panel.num_h_bars_input.text()}\n")
                    f.write(f"Exposed Vertical Bars: {self.results_panel.num_v_bars_input.text()}\n")
                    f.write(f"Detected Horizontal Cracks: {self.results_panel.num_h_cracks_input.text()}\n")
                    f.write(f"Detected Diagonal Cracks: {self.results_panel.num_v_cracks_input.text()}\n\n")
                    f.write("="*40 + "\n")
                    f.write("Notes and Observations\n")
                    f.write("-" * 40 + "\n")
                    f.write(self.notes_area.toPlainText() + "\n")
                
                QMessageBox.information(self, "Success", f"Report successfully saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save report. Error: {e}")
