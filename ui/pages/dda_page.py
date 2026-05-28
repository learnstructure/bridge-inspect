from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QScrollArea,
    QSplitter,
)
from PySide6.QtCore import Qt


class DDAPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # --- Left Side: Input Form ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        form_container = QWidget()
        form_layout = QFormLayout(form_container)
        form_layout.setLabelAlignment(Qt.AlignLeft)

        # --- Section: Column Properties ---
        form_layout.addRow(QLabel("<h3>Column Properties</h3>"))
        self.column_type_combo = QComboBox()
        self.column_type_combo.addItems(["Circular", "Rectangular"])
        form_layout.addRow("Column Type:", self.column_type_combo)

        # Create labels and inputs for dynamic fields
        self.diameter_label = QLabel("Diameter (mm):")
        self.diameter_input = QLineEdit()
        form_layout.addRow(self.diameter_label, self.diameter_input)

        self.width_label = QLabel("Width (mm):")
        self.width_input = QLineEdit()
        form_layout.addRow(self.width_label, self.width_input)
        
        self.height_label = QLabel("Height (mm):")
        self.height_input = QLineEdit()
        form_layout.addRow(self.height_label, self.height_input)

        self.length_input = QLineEdit()
        self.cover_input = QLineEdit()
        form_layout.addRow("Length (mm):", self.length_input)
        form_layout.addRow("Cover (mm):", self.cover_input)

        # --- Section: Concrete Properties ---
        form_layout.addRow(QLabel("<h3>Concrete Strength</h3>"))
        self.fc_input = QLineEdit()
        form_layout.addRow("fc' (MPa):", self.fc_input)

        # --- Section: Longitudinal Reinforcement ---
        form_layout.addRow(QLabel("<h3>Longitudinal Reinforcement</h3>"))
        self.long_num_bars_input = QLineEdit()
        self.long_bar_dia_input = QLineEdit()
        self.long_fy_input = QLineEdit()
        self.long_fu_input = QLineEdit()
        self.long_eps_ult_input = QLineEdit()
        form_layout.addRow("Number of Bars:", self.long_num_bars_input)
        form_layout.addRow("Bar Diameter (mm):", self.long_bar_dia_input)
        form_layout.addRow("fy (MPa):", self.long_fy_input)
        form_layout.addRow("fu (MPa):", self.long_fu_input)
        form_layout.addRow("Ultimate Strain (eps_ultimate):", self.long_eps_ult_input)

        # --- Section: Transverse Reinforcement ---
        form_layout.addRow(QLabel("<h3>Transverse Reinforcement</h3>"))
        self.trans_bar_dia_input = QLineEdit()
        self.trans_spacing_input = QLineEdit()
        self.trans_fyh_input = QLineEdit()
        self.trans_fuh_input = QLineEdit()
        self.trans_epsh_ult_input = QLineEdit()
        form_layout.addRow("Bar Diameter (mm):", self.trans_bar_dia_input)
        form_layout.addRow("Spacing (mm):", self.trans_spacing_input)
        form_layout.addRow("fyh (MPa):", self.trans_fyh_input)
        form_layout.addRow("fuh (MPa):", self.trans_fuh_input)
        form_layout.addRow("Ultimate Strain (epsh_ultimate):", self.trans_epsh_ult_input)
        
        # --- Section: Loading ---
        form_layout.addRow(QLabel("<h3>Loading</h3>"))
        self.axial_load_input = QLineEdit()
        form_layout.addRow("Axial Load (kN):", self.axial_load_input)

        # --- Action Buttons ---
        self.submit_btn = QPushButton("Submit")
        self.clear_btn = QPushButton("Clear")
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(self.clear_btn)
        form_layout.addRow(button_layout)

        # Set the form widget into the scroll area
        scroll_area.setWidget(form_container)

        # --- Right Side: Output Panel ---
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText("Pushover analysis results will appear here...")

        # Add widgets to splitter and set initial sizes
        splitter.addWidget(scroll_area)
        splitter.addWidget(self.output)
        splitter.setSizes([450, 550])

        # --- Connect Signals to Slots ---
        self.submit_btn.clicked.connect(self._run_analysis)
        self.clear_btn.clicked.connect(self._clear_form)
        self.column_type_combo.currentIndexChanged.connect(self._update_column_fields)
        
        self._update_column_fields() # Set initial visibility

    def _update_column_fields(self):
        """Shows or hides form widgets based on the selected column type."""
        is_circular = self.column_type_combo.currentText() == "Circular"
        
        # Directly set the visibility of the labels and their corresponding inputs
        self.diameter_label.setVisible(is_circular)
        self.diameter_input.setVisible(is_circular)
        
        self.width_label.setVisible(not is_circular)
        self.width_input.setVisible(not is_circular)
        
        self.height_label.setVisible(not is_circular)
        self.height_input.setVisible(not is_circular)

    def _run_analysis(self):
        """Placeholder for running the pushover analysis."""
        self.output.clear()
        self.output.append("--- Starting Pushover Analysis ---")
        
        all_inputs = {
            "Column Type": self.column_type_combo.currentText(),
            "Length": self.length_input.text(),
            "Cover": self.cover_input.text(),
            "fc": self.fc_input.text(),
            "Long. Num Bars": self.long_num_bars_input.text(),
            "Long. Bar Dia": self.long_bar_dia_input.text(),
            "Long. fy": self.long_fy_input.text(),
            "Long. fu": self.long_fu_input.text(),
            "Long. eps_ultimate": self.long_eps_ult_input.text(),
            "Trans. Bar Dia": self.trans_bar_dia_input.text(),
            "Trans. Spacing": self.trans_spacing_input.text(),
            "Trans. fyh": self.trans_fyh_input.text(),
            "Trans. fuh": self.trans_fuh_input.text(),
            "Trans. epsh_ultimate": self.trans_epsh_ult_input.text(),
            "Axial Load": self.axial_load_input.text(),
        }

        if self.column_type_combo.currentText() == "Circular":
            all_inputs["Diameter"] = self.diameter_input.text()
        else:
            all_inputs["Width"] = self.width_input.text()
            all_inputs["Height"] = self.height_input.text()
            
        for key, value in all_inputs.items():
            self.output.append(f"{key}: {value}")
            
        self.output.append("\nAnalysis logic is not yet implemented.")
        
    def _clear_form(self):
        """Clears all QLineEdit fields in the form."""
        for child in self.findChildren(QLineEdit):
            child.clear()
        self.output.clear()
        self.column_type_combo.setCurrentIndex(0)
