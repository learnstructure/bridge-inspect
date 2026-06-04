# ui/pages/pda/damage_state_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QSpinBox, 
    QPushButton, QGroupBox, QScrollArea, QSplitter, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt

from ui.widgets.image_viewer import ImageViewer

class DamageStateEditorPage(QWidget):
    """
    A page to display and edit the numerical rules that define each damage state,
    with a visual example on the side.
    """
    def __init__(self):
        super().__init__()
        self.controller = None

        # The original, hard-coded rules to allow for reset
        self.default_rules = {
            "level_5": {"min_h_bars": 3, "min_v_bars": 2},
            "level_4": {"min_h_bars": 1, "min_v_bars": 1, "min_spall_ratio": 50},
            "level_3": {"min_spall_ratio": 10},
            "level_2": {"min_v_cracks": 3},
            "level_1": {"min_h_cracks": 1, "max_v_cracks": 0}
        }

        # Main layout is now horizontal, managed by a splitter
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # --- Left side: Rules Editor in a Scroll Area ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        rules_container = QWidget()
        rules_layout = QVBoxLayout(rules_container)
        rules_layout.setAlignment(Qt.AlignTop)
        scroll_area.setWidget(rules_container)

        title = QLabel("<h3>Damage State Rules</h3>")
        title.setAlignment(Qt.AlignCenter)
        rules_layout.addWidget(title)

        self.create_level_5_group(rules_layout)
        self.create_level_4_group(rules_layout)
        self.create_level_3_group(rules_layout)
        self.create_level_2_group(rules_layout)
        self.create_level_1_group(rules_layout)

        # --- Action Buttons ---
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Update Rules")
        self.reset_btn = QPushButton("Reset to Defaults")
        self.save_btn.setFixedWidth(150)
        self.reset_btn.setFixedWidth(200)
        self.save_btn.clicked.connect(self.on_save_rules)
        self.reset_btn.clicked.connect(self.on_reset_rules)
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()
        rules_layout.addLayout(button_layout)

        # --- Right side: Image Viewer ---
        self.image_viewer = ImageViewer()
        image_path = "assets/images/damage-levels.jpg"
        self.image_viewer.load_image(image_path)
        
        # --- Add widgets to splitter ---
        splitter.addWidget(scroll_area)
        splitter.addWidget(self.image_viewer)
        splitter.setSizes([450, 550])

    def set_controller(self, controller):
        self.controller = controller

    def _create_spinbox(self, value, min_val=0, max_val=100):
        spinbox = QSpinBox()
        spinbox.setRange(min_val, max_val)
        spinbox.setValue(value)
        # This prevents the spinbox from changing value on mouse wheel scroll
        spinbox.setFocusPolicy(Qt.StrongFocus)
        return spinbox

    def create_level_5_group(self, parent_layout):
        group = QGroupBox("Level 5 (Highest Damage)")
        layout = QFormLayout(group)
        self.l5_h_bars = self._create_spinbox(self.default_rules["level_5"]["min_h_bars"])
        self.l5_v_bars = self._create_spinbox(self.default_rules["level_5"]["min_v_bars"])
        layout.addRow("Min Exposed H-Bars:", self.l5_h_bars)
        layout.addRow("Min Exposed V-Bars:", self.l5_v_bars)
        layout.addRow(QLabel("<i>Condition: If EITHER is met</i>"))
        parent_layout.addWidget(group)

    def create_level_4_group(self, parent_layout):
        group = QGroupBox("Level 4")
        layout = QFormLayout(group)
        self.l4_h_bars = self._create_spinbox(self.default_rules["level_4"]["min_h_bars"])
        self.l4_v_bars = self._create_spinbox(self.default_rules["level_4"]["min_v_bars"])
        self.l4_spall = self._create_spinbox(self.default_rules["level_4"]["min_spall_ratio"])
        layout.addRow("Min Exposed H-Bars:", self.l4_h_bars)
        layout.addRow("Min Exposed V-Bars:", self.l4_v_bars)
        layout.addRow("Min Spalling Ratio (%):", self.l4_spall)
        layout.addRow(QLabel("<i>Condition: If ANY are met</i>"))
        parent_layout.addWidget(group)

    def create_level_3_group(self, parent_layout):
        group = QGroupBox("Level 3")
        layout = QFormLayout(group)
        self.l3_spall = self._create_spinbox(self.default_rules["level_3"]["min_spall_ratio"])
        layout.addRow("Min Spalling Ratio (%):", self.l3_spall)
        parent_layout.addWidget(group)

    def create_level_2_group(self, parent_layout):
        group = QGroupBox("Level 2")
        layout = QFormLayout(group)
        self.l2_v_cracks = self._create_spinbox(self.default_rules["level_2"]["min_v_cracks"])
        layout.addRow("Min Diagonal/V-Cracks:", self.l2_v_cracks)
        parent_layout.addWidget(group)

    def create_level_1_group(self, parent_layout):
        group = QGroupBox("Level 1 (Lowest Damage)")
        layout = QFormLayout(group)
        self.l1_h_cracks = self._create_spinbox(self.default_rules["level_1"]["min_h_cracks"])
        self.l1_v_cracks = self._create_spinbox(self.default_rules["level_1"]["max_v_cracks"])
        layout.addRow("Min Horizontal Cracks:", self.l1_h_cracks)
        layout.addRow("Max Diagonal/V-Cracks:", self.l1_v_cracks)
        layout.addRow(QLabel("<i>Condition: If BOTH are met</i>"))
        parent_layout.addWidget(group)

    def on_save_rules(self):
        if not self.controller: return
        
        reply = QMessageBox.question(self, 'Confirm Update', 
                                     "Are you sure you want to update the rules? This will update the damage assessment logic.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            new_rules = {
                "level_5": {"min_h_bars": self.l5_h_bars.value(), "min_v_bars": self.l5_v_bars.value()},
                "level_4": {"min_h_bars": self.l4_h_bars.value(), "min_v_bars": self.l4_v_bars.value(), "min_spall_ratio": self.l4_spall.value()},
                "level_3": {"min_spall_ratio": self.l3_spall.value()},
                "level_2": {"min_v_cracks": self.l2_v_cracks.value()},
                "level_1": {"min_h_cracks": self.l1_h_cracks.value(), "max_v_cracks": self.l1_v_cracks.value()}
            }
            self.controller.update_damage_rules(new_rules)

    def on_reset_rules(self):
        reply = QMessageBox.question(self, 'Confirm Reset',
                                     "Are you sure you want to reset all rules to their default values?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.l5_h_bars.setValue(self.default_rules["level_5"]["min_h_bars"])
            self.l5_v_bars.setValue(self.default_rules["level_5"]["min_v_bars"])
            self.l4_h_bars.setValue(self.default_rules["level_4"]["min_h_bars"])
            self.l4_v_bars.setValue(self.default_rules["level_4"]["min_v_bars"])
            self.l4_spall.setValue(self.default_rules["level_4"]["min_spall_ratio"])
            self.l3_spall.setValue(self.default_rules["level_3"]["min_spall_ratio"])
            self.l2_v_cracks.setValue(self.default_rules["level_2"]["min_v_cracks"])
            self.l1_h_cracks.setValue(self.default_rules["level_1"]["min_h_cracks"])
            self.l1_v_cracks.setValue(self.default_rules["level_1"]["max_v_cracks"])
