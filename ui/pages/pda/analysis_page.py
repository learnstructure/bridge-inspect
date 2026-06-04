# ui/pages/pda/analysis_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, 
    QCheckBox, QGraphicsView, QFileDialog
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

        top_btn_layout = QHBoxLayout()
        self.upload_btn = QPushButton("Upload Image")
        self.run_btn = QPushButton("Run PDA")
        top_btn_layout.addWidget(self.upload_btn)
        top_btn_layout.addWidget(self.run_btn)

        splitter = QSplitter(Qt.Horizontal)
        self.image_viewer = ImageViewer()
        # The results panel on this page is for display only.
        self.results_panel = ResultsPanel(is_editable=False)

        splitter.addWidget(self.image_viewer)
        splitter.addWidget(self.results_panel)
        splitter.setSizes([700, 300])

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

        main_layout.addLayout(top_btn_layout)
        main_layout.addWidget(splitter)
        main_layout.addLayout(toolbar_layout)

    def set_controller(self, controller):
        self.controller = controller
        self.upload_btn.clicked.connect(self.select_file)
        self.run_btn.clicked.connect(self.run_pda)
        self.zoom_in_btn.clicked.connect(lambda: self.image_viewer.scale(1.25, 1.25))
        self.zoom_out_btn.clicked.connect(lambda: self.image_viewer.scale(0.8, 0.8))
        self.pan_btn.clicked.connect(self.enable_pan_mode)
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

    def enable_pan_mode(self):
        self.image_viewer.setDragMode(QGraphicsView.ScrollHandDrag)

    def on_toggle_defects(self):
        if self.last_results and self.current_file_path:
            self.controller.update_image_display(
                self.current_file_path, 
                self.last_results, 
                show_cracks=self.show_defects_checkbox.isChecked()
            )
