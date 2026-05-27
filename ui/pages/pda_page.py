# ui/pages/pda_page.py
from PySide6.QtWidgets import (
    QGraphicsView,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QSplitter,
    QCheckBox,
    QFormLayout,
    QLineEdit,
    QLabel,
)
from PySide6.QtCore import Qt
from ui.widgets.image_viewer import ImageViewer
from controllers.pda_controller import PDAController


class PDAPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()

        # Top action buttons (Upload / Run PDA)
        top_btn_layout = QHBoxLayout()
        self.upload_btn = QPushButton("Upload Image")
        self.run_btn = QPushButton("Run PDA")
        top_btn_layout.addWidget(self.upload_btn)
        top_btn_layout.addWidget(self.run_btn)

        # Splitter for Image + Results
        splitter = QSplitter(Qt.Horizontal)
        self.image_viewer = ImageViewer()

        # --- Results Panel (Now an Editable Form) ---
        self.results_widget = QWidget()
        self.results_layout = QFormLayout(self.results_widget)
        self.results_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.results_layout.setLabelAlignment(Qt.AlignLeft)
        self.results_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_widget.setLayout(self.results_layout)

        self.results_title = QLabel("<h3>PDA Results</h3>")
        self.num_h_cracks_input = QLineEdit()
        self.num_v_cracks_input = QLineEdit()
        self.max_spall_ratio_input = QLineEdit()
        self.num_h_bars_input = QLineEdit()
        self.num_v_bars_input = QLineEdit()
        self.damage_level_display = QLineEdit()
        self.damage_level_display.setReadOnly(True)
        self.damage_level_display.setStyleSheet("background-color: #e9ecef; color: #495057;")

        self.results_layout.addRow(self.results_title)
        self.results_layout.addRow("Number of horizontal cracks:", self.num_h_cracks_input)
        self.results_layout.addRow("Number of diagonal cracks:", self.num_v_cracks_input)
        self.results_layout.addRow("Maximum spalled ratio (%):", self.max_spall_ratio_input)
        self.results_layout.addRow("Number of exposed horizontal bars:", self.num_h_bars_input)
        self.results_layout.addRow("Number of exposed vertical bars:", self.num_v_bars_input)
        self.results_layout.addRow("Damage state:", self.damage_level_display)
        
        self.update_results_btn = QPushButton("Update Assessment")
        self.results_layout.addWidget(self.update_results_btn)
        # ----------------------------------------

        splitter.addWidget(self.image_viewer)
        splitter.addWidget(self.results_widget)
        splitter.setSizes([700, 300])

        # Image toolbar (zoom in/out, pan)
        toolbar_layout = QHBoxLayout()
        self.zoom_in_btn = QPushButton("Zoom +")
        self.zoom_out_btn = QPushButton("Zoom -")
        self.pan_btn = QPushButton("Pan")
        self.show_defects_checkbox = QCheckBox("Show Defects")
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.zoom_in_btn)
        toolbar_layout.addWidget(self.zoom_out_btn)
        toolbar_layout.addWidget(self.pan_btn)
        toolbar_layout.addWidget(self.show_defects_checkbox)
        toolbar_layout.addStretch()

        # Combine layouts
        main_layout.addLayout(top_btn_layout)
        main_layout.addWidget(splitter)
        main_layout.addLayout(toolbar_layout)
        self.setLayout(main_layout)

        # Controller
        self.controller = PDAController(self)
        self.current_file_path = None
        self.last_results = None

        # Connect signals
        self.upload_btn.clicked.connect(self.select_file)
        self.run_btn.clicked.connect(self.run_pda)
        self.zoom_in_btn.clicked.connect(lambda: self.image_viewer.zoom(1.25))
        self.zoom_out_btn.clicked.connect(lambda: self.image_viewer.zoom(0.8))
        self.pan_btn.clicked.connect(self.enable_pan_mode)
        self.show_defects_checkbox.stateChanged.connect(self.on_toggle_defects)
        self.update_results_btn.clicked.connect(self.on_update_assessment)

    def select_file(self):
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.png *.jpg *.jpeg)"
        )
        if file_path:
            self.current_file_path = file_path
            self.controller.upload_image(file_path)

    def display_image(self, file_path):
        self.image_viewer.load_image(file_path)

    def run_pda(self):
        if self.current_file_path:
            self.controller.run_pda(self.current_file_path)

    def display_results(self, results):
        self.last_results = results

        if not results or "error" in results:
            # You can add a dialog or a status bar message for errors if you want
            self.num_h_cracks_input.setText("Error")
            self.num_v_cracks_input.setText("Error")
            self.max_spall_ratio_input.setText("Error")
            self.num_h_bars_input.setText("Error")
            self.num_v_bars_input.setText("Error")
            self.damage_level_display.setText(results.get("error", "Unknown error"))
            return

        damage_level = results.get("damage_level", "Not available")
        num_h_cracks = results.get("num_horizontal_cracks", 0)
        num_v_cracks = results.get("num_vertical_cracks", 0)
        max_spall_ratio = results.get("spalled_ratio", 0)
        num_h_bars = results.get("num_exposed_horizontal_bars", 0)
        num_v_bars = results.get("num_exposed_vertical_bars", 0)

        # Set values in the QLineEdit widgets
        self.max_spall_ratio_input.setText(f"{max_spall_ratio:.2f}")
        self.num_h_bars_input.setText(str(num_h_bars))
        self.num_v_bars_input.setText(str(num_v_bars))
        self.damage_level_display.setText(damage_level)

        # Handle special case for crack fields
        if damage_level in ["Level 3", "Level 4", "Level 5"]:
            self.num_h_cracks_input.setText("N/A")
            self.num_h_cracks_input.setEnabled(False)
            self.num_v_cracks_input.setText("N/A")
            self.num_v_cracks_input.setEnabled(False)
        else:
            self.num_h_cracks_input.setText(str(num_h_cracks))
            self.num_h_cracks_input.setEnabled(True)
            self.num_v_cracks_input.setText(str(num_v_cracks))
            self.num_v_cracks_input.setEnabled(True)

    def on_update_assessment(self):
        if not self.last_results:
            return
        
        updated_data = self.last_results.copy()
        
        try:
            # Only update values if they are enabled
            if self.num_h_cracks_input.isEnabled():
                updated_data["num_horizontal_cracks"] = int(self.num_h_cracks_input.text())
            if self.num_v_cracks_input.isEnabled():
                updated_data["num_vertical_cracks"] = int(self.num_v_cracks_input.text())
            
            updated_data["spalled_ratio"] = float(self.max_spall_ratio_input.text())
            updated_data["num_exposed_horizontal_bars"] = int(self.num_h_bars_input.text())
            updated_data["num_exposed_vertical_bars"] = int(self.num_v_bars_input.text())
        except (ValueError, TypeError):
            # You could show a QErrorMessage dialog here
            print("Invalid input. Please enter valid numbers.")
            return

        # Pass the updated data to the controller for recalculation
        self.controller.update_damage_assessment(updated_data)

    def enable_pan_mode(self):
        self.image_viewer.setDragMode(QGraphicsView.ScrollHandDrag)

    def on_toggle_defects(self):
        if self.last_results and self.current_file_path:
            self.controller.update_image_display(
                self.current_file_path,
                self.last_results,
                show_cracks=self.show_defects_checkbox.isChecked(),
            )
