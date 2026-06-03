# ui/pages/pda/summary_report_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel
from PySide6.QtCore import Qt

class SummaryReportPage(QWidget):
    """A page to display the final summary of the PDA."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("<h3>Summary Report</h3>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.form_layout = QFormLayout()
        self.form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        
        # --- Result Displays ---
        self.damage_level_label = QLabel("<i>Pending analysis...</i>")
        self.num_cracks_label = QLabel("<i>Pending analysis...</i>")
        self.spalling_ratio_label = QLabel("<i>Pending analysis...</i>")
        self.exposed_bars_label = QLabel("<i>Pending analysis...</i>")

        self.form_layout.addRow(QLabel("<b>Final Damage Level:</b>"), self.damage_level_label)
        self.form_layout.addRow(QLabel("<b>Total Cracks:</b>"), self.num_cracks_label)
        self.form_layout.addRow(QLabel("<b>Spalling Ratio (%):</b>"), self.spalling_ratio_label)
        self.form_layout.addRow(QLabel("<b>Exposed Bars (H/V):</b>"), self.exposed_bars_label)

        layout.addLayout(self.form_layout)

    def update_summary(self, results):
        """Populates the summary fields with data from the final analysis results."""
        if not results or "error" in results:
            self.damage_level_label.setText("<font color='red'>Error</font>")
            self.num_cracks_label.setText("<font color='red'>Error</font>")
            self.spalling_ratio_label.setText("<font color='red'>Error</font>")
            self.exposed_bars_label.setText("<font color='red'>Error</font>")
            return

        damage_level = results.get("damage_level", "N/A")
        num_h_cracks = results.get("num_horizontal_cracks", 0)
        num_v_cracks = results.get("num_vertical_cracks", 0)
        spall_ratio = results.get("spalled_ratio", 0)
        num_h_bars = results.get("num_exposed_horizontal_bars", 0)
        num_v_bars = results.get("num_exposed_vertical_bars", 0)

        total_cracks = num_h_cracks + num_v_cracks
        if damage_level in ["Level 3", "Level 4", "Level 5"]:
            total_cracks_text = "N/A (Spalling Present)"
        else:
            total_cracks_text = str(total_cracks)

        self.damage_level_label.setText(f"<b>{damage_level}</b>")
        self.num_cracks_label.setText(total_cracks_text)
        self.spalling_ratio_label.setText(f"{spall_ratio:.2f}")
        self.exposed_bars_label.setText(f"{num_h_bars} / {num_v_bars}")
