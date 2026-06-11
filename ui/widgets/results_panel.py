# ui/widgets/results_panel.py
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QLineEdit, QLabel, QPushButton, QMessageBox
)
from PySide6.QtCore import Signal

class ResultsPanel(QWidget):
    """A reusable widget to display PDA results, with an optional editable mode."""
    update_clicked = Signal(dict)

    def __init__(self, is_editable=False, show_update_button=True, parent=None):
        super().__init__(parent)
        self._is_editable = is_editable
        self._show_update_button = show_update_button
        
        self.layout = QFormLayout(self)
        self.layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        
        self.results_title = QLabel("<h3>Analysis Results</h3>")
        self.damage_level_display = QLineEdit()
        self.num_h_cracks_input = QLineEdit()
        self.num_v_cracks_input = QLineEdit()
        self.spalled_ratio_input = QLineEdit()
        self.num_h_bars_input = QLineEdit()
        self.num_v_bars_input = QLineEdit()

        self.all_fields = {
            "damage_level": self.damage_level_display,
            "num_h_cracks": self.num_h_cracks_input,
            "num_v_cracks": self.num_v_cracks_input,
            "spalled_ratio": self.spalled_ratio_input,
            "num_h_bars": self.num_h_bars_input,
            "num_v_bars": self.num_v_bars_input,
        }

        self.damage_level_display.setReadOnly(True)
        self.damage_level_display.setStyleSheet("background-color: #e9ecef; color: #495057;")
        
        # Set initial read-only state
        self.set_editable(self._is_editable)

        self.layout.addRow(self.results_title)
        self.layout.addRow("<b>Damage State:</b>", self.damage_level_display)
        self.layout.addRow("Horizontal Cracks:", self.num_h_cracks_input)
        self.layout.addRow("Diagonal Cracks:", self.num_v_cracks_input)
        self.layout.addRow("Spalled Ratio (%):", self.spalled_ratio_input)
        self.layout.addRow("Exposed Horizontal Bars:", self.num_h_bars_input)
        self.layout.addRow("Exposed Vertical Bars:", self.num_v_bars_input)

        if self._is_editable and self._show_update_button:
            self.update_btn = QPushButton("Update Assessment")
            self.update_btn.clicked.connect(self.on_update_clicked)
            self.layout.addRow(self.update_btn)

    def set_editable(self, editable):
        """Toggles the editable state of the input fields."""
        self._is_editable = editable
        # Damage level display is always read-only
        fields_to_toggle = {k: v for k, v in self.all_fields.items() if k != 'damage_level'}

        for field in fields_to_toggle.values():
            field.setReadOnly(not editable)
            if editable:
                field.setStyleSheet("background-color: #ffffff; border: 1px solid #999; padding: 4px;")
            else:
                field.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 4px;")
        
        # Re-apply logic for enabling/disabling crack fields based on current data
        damage_level = self.damage_level_display.text()
        is_spalled = damage_level in ["Level 3", "Level 4", "Level 5"]
        if self._is_editable:
             self.num_h_cracks_input.setEnabled(not is_spalled)
             self.num_v_cracks_input.setEnabled(not is_spalled)

    def update_results(self, results):
        if not results:
            for field in self.all_fields.values(): field.clear()
            return

        damage_level = results.get("damage_level", "N/A")
        is_spalled = damage_level in ["Level 3", "Level 4", "Level 5"]
        
        h_cracks = "N/A" if is_spalled else str(results.get("num_horizontal_cracks", 0))
        v_cracks = "N/A" if is_spalled else str(results.get("num_vertical_cracks", 0))
        
        self.damage_level_display.setText(damage_level)
        self.num_h_cracks_input.setText(h_cracks)
        self.num_v_cracks_input.setText(v_cracks)
        self.spalled_ratio_input.setText(f'{results.get("spalled_ratio", 0):.2f}')
        self.num_h_bars_input.setText(str(results.get("num_exposed_horizontal_bars", 0)))
        self.num_v_bars_input.setText(str(results.get("num_exposed_vertical_bars", 0)))

        # When results are updated, ensure the editable state is correctly applied
        if self._is_editable:
            self.num_h_cracks_input.setEnabled(not is_spalled)
            self.num_v_cracks_input.setEnabled(not is_spalled)

    def get_values(self):
        """Gathers data from input fields and returns it as a dictionary."""
        try:
            updated_values = {
                "spalled_ratio": float(self.spalled_ratio_input.text()),
                "num_exposed_horizontal_bars": int(self.num_h_bars_input.text()),
                "num_exposed_vertical_bars": int(self.num_v_bars_input.text()),
            }
            if self.num_h_cracks_input.isEnabled():
                h_cracks_text = self.num_h_cracks_input.text()
                updated_values["num_horizontal_cracks"] = int(h_cracks_text) if h_cracks_text != "N/A" else 0
            if self.num_v_cracks_input.isEnabled():
                v_cracks_text = self.num_v_cracks_input.text()
                updated_values["num_vertical_cracks"] = int(v_cracks_text) if v_cracks_text != "N/A" else 0
            return updated_values
        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Invalid Input", f"Please check your input values. All fields must contain valid numbers. Error: {e}")
            return None
            
    def on_update_clicked(self):
        """Gathers data and emits the update_clicked signal."""
        updated_values = self.get_values()
        if updated_values:
            self.update_clicked.emit(updated_values)
