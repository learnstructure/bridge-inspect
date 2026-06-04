# ui/pages/pda/summary_report_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QFormLayout, QLineEdit, QLabel, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from ui.widgets.image_viewer import ImageViewer

class SummaryReportPage(QWidget):
    """A page to display a comprehensive summary of the PDA results, including an image."""
    def __init__(self):
        super().__init__()
        self.controller = None
        
        main_layout = QVBoxLayout(self)

        # --- Title ---
        title = QLabel("<h2>PDA Summary Report</h2>")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # --- Main Content Splitter ---
        splitter = QSplitter(Qt.Horizontal)

        # Left Panel: Image Viewer for the overlay
        self.image_viewer = ImageViewer()
        self.image_viewer.setReadOnly(True) # Disable drawing on the summary image

        # Right Panel: Results & Notes
        self.results_widget = QWidget()
        results_panel_layout = QVBoxLayout(self.results_widget)
        
        # Using QLineEdit for a cleaner, organized look
        self.results_form = QFormLayout()
        self.results_form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.results_form.setLabelAlignment(Qt.AlignLeft)
        self.results_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.damage_level_display = QLineEdit()
        self.num_h_cracks_display = QLineEdit()
        self.num_v_cracks_display = QLineEdit()
        self.spalled_ratio_display = QLineEdit()
        self.num_h_bars_display = QLineEdit()
        self.num_v_bars_display = QLineEdit()

        # Make result fields read-only and style them
        for field in [self.damage_level_display, self.num_h_cracks_display, self.num_v_cracks_display,
                      self.spalled_ratio_display, self.num_h_bars_display, self.num_v_bars_display]:
            field.setReadOnly(True)
            field.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 4px;")

        self.results_form.addRow("<b>Final Damage State:</b>", self.damage_level_display)
        self.results_form.addRow("Horizontal Cracks:", self.num_h_cracks_display)
        self.results_form.addRow("Diagonal Cracks:", self.num_v_cracks_display)
        self.results_form.addRow("Spalled Ratio (%):", self.spalled_ratio_display)
        self.results_form.addRow("Exposed Horizontal Bars:", self.num_h_bars_display)
        self.results_form.addRow("Exposed Vertical Bars:", self.num_v_bars_display)

        # Notes Section
        self.notes_area = QTextEdit()
        self.notes_area.setPlaceholderText("Add any final notes or observations for the report...")

        results_panel_layout.addWidget(QLabel("<h4>Analysis Results</h4>"))
        results_panel_layout.addLayout(self.results_form)
        results_panel_layout.addWidget(QLabel("<h4>Notes</h4>"))
        results_panel_layout.addWidget(self.notes_area)

        splitter.addWidget(self.image_viewer)
        splitter.addWidget(self.results_widget)
        splitter.setSizes([600, 400]) # Give more space to the image initially

        main_layout.addWidget(splitter)

        # --- Bottom Buttons ---
        button_layout = QHBoxLayout()
        self.save_report_btn = QPushButton("Save Report")
        self.save_report_btn.setMinimumWidth(150)
        self.save_report_btn.clicked.connect(self.save_report)
        button_layout.addStretch()
        button_layout.addWidget(self.save_report_btn)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

    def set_controller(self, controller):
        self.controller = controller

    def update_summary(self, results):
        """Populates the summary page with results and the overlay image."""
        if not results:
            # Clear fields if no results
            for field in [self.damage_level_display, self.num_h_cracks_display, self.num_v_cracks_display,
                          self.spalled_ratio_display, self.num_h_bars_display, self.num_v_bars_display]:
                field.clear()
            self.image_viewer.clear_image()
            self.notes_area.clear()
            return

        damage_level = results.get("damage_level", "N/A")
        is_spalled = damage_level in ["Level 3", "Level 4", "Level 5"]
        h_cracks = "N/A" if is_spalled else str(results.get("num_horizontal_cracks", 0))
        v_cracks = "N/A" if is_spalled else str(results.get("num_vertical_cracks", 0))

        self.damage_level_display.setText(damage_level)
        self.num_h_cracks_display.setText(h_cracks)
        self.num_v_cracks_display.setText(v_cracks)
        self.spalled_ratio_display.setText(f'{results.get("spalled_ratio", 0):.2f}')
        self.num_h_bars_display.setText(str(results.get("num_exposed_horizontal_bars", 0)))
        self.num_v_bars_display.setText(str(results.get("num_exposed_vertical_bars", 0)))

        # Display the overlay image passed from the controller
        if "overlay_image" in results and results["overlay_image"] is not None:
            self.image_viewer.load_image(results["overlay_image"], is_np_array=True)
        else:
            self.image_viewer.clear_image()

    def save_report(self):
        """Saves the summary report content to a text file (for now)."""
        if not self.damage_level_display.text():
            QMessageBox.warning(self, "Warning", "There is no report to save. Please run an analysis first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "pda_summary_report.txt", "Text Files (*.txt);;All Files (*)")

        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("           PDA SUMMARY REPORT\n")
                    f.write("="*40 + "\n\n")
                    f.write(f"Final Damage State: {self.damage_level_display.text()}\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Spalled Ratio (%): {self.spalled_ratio_display.text()}\n")
                    f.write(f"Exposed Horizontal Bars: {self.num_h_bars_display.text()}\n")
                    f.write(f"Exposed Vertical Bars: {self.num_v_bars_display.text()}\n")
                    f.write(f"Detected Horizontal Cracks: {self.num_h_cracks_display.text()}\n")
                    f.write(f"Detected Diagonal Cracks: {self.num_v_cracks_display.text()}\n\n")
                    f.write("="*40 + "\n")
                    f.write("Notes and Observations\n")
                    f.write("-" * 40 + "\n")
                    f.write(self.notes_area.toPlainText() + "\n")
                
                QMessageBox.information(self, "Success", f"Report successfully saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save report. Error: {e}")
