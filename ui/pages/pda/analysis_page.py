# ui/pages/pda/analysis_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, 
    QCheckBox, QLabel, QFrame, QFileDialog
)
from PySide6.QtCore import Qt
from ui.widgets.image_viewer import ImageViewer
from ui.widgets.results_panel import ResultsPanel

class AnalysisPage(QWidget):
    """This widget contains the primary PDA functionality. The results are read-only."""
    def __init__(self):
        super().__init__()
        self.controller = None
        self.current_file_path = None
        self.last_results = None

        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # --- Left Panel (Image) ---
        left_panel_widget = QWidget()
        left_panel_layout = QVBoxLayout(left_panel_widget)
        left_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.upload_btn = QPushButton("Upload Image")
        self.image_viewer = ImageViewer()
        left_panel_layout.addWidget(self.upload_btn)
        left_panel_layout.addWidget(self.image_viewer)
        
        # --- Right Panel (Results) --- 
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        self.results_panel = ResultsPanel(is_editable=False)

        # --- Controls Layout ---
        self.run_btn = QPushButton("Run PDA")
        self.show_defects_checkbox = QCheckBox("Show Defects")
        self.show_defects_checkbox.setChecked(True) # Set checkbox to be checked by default
        
        bottom_controls_layout = QHBoxLayout()
        bottom_controls_layout.addWidget(self.run_btn)
        bottom_controls_layout.addWidget(self.show_defects_checkbox)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        zoom_instructions = QLabel("Use mouse scroll to zoom, right-click to pan.")
        zoom_instructions.setAlignment(Qt.AlignCenter)

        right_panel_layout.addWidget(self.results_panel)
        right_panel_layout.addStretch()
        right_panel_layout.addLayout(bottom_controls_layout)
        right_panel_layout.addWidget(separator)
        right_panel_layout.addWidget(zoom_instructions)

        splitter.addWidget(left_panel_widget)
        splitter.addWidget(right_panel_widget)
        splitter.setSizes([750, 250])

        main_layout.addWidget(splitter)

    def set_controller(self, controller):
        self.controller = controller
        self.image_viewer.image_dropped.connect(self.controller.upload_image)
        self.upload_btn.clicked.connect(self.select_file)
        self.run_btn.clicked.connect(self.run_pda)
        self.show_defects_checkbox.stateChanged.connect(self.on_toggle_defects)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            self.controller.upload_image(file_path)

    def display_image(self, image_data, is_np_array=False):
        if not is_np_array:
            self.current_file_path = image_data
        self.image_viewer.load_image(image_data, is_np_array=is_np_array)

    def run_pda(self):
        if self.current_file_path:
            self.controller.run_pda(self.current_file_path)

    def display_results(self, results):
        self.last_results = results
        self.results_panel.update_results(results)

    def on_toggle_defects(self):
        if self.last_results and self.current_file_path:
            self.controller.update_image_display(
                self.current_file_path, 
                self.last_results, 
                show_cracks=self.show_defects_checkbox.isChecked()
            )
