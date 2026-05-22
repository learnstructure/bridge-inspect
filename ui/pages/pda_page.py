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
        self.results_panel = QTextEdit()
        self.results_panel.setReadOnly(True)
        self.results_panel.setPlaceholderText("PDA Results will appear here...")
        splitter.addWidget(self.image_viewer)
        splitter.addWidget(self.results_panel)
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
        self.results_panel.clear()

        if not results or "error" in results:
            error_message = results.get("error", "An unknown error occurred.")
            html_content = f'''<div style="background-color: #f8d7da; color: #721c24; padding: 20px; border-radius: 5px; border: 1px solid #f5c6cb;">
                <h3>Operation Failed</h3>
                <p>{error_message}</p>
            </div>'''
            self.results_panel.setHtml(html_content)
            return

        damage_level = results.get("damage_level", "Not available")
        num_h_cracks = results.get("num_horizontal_cracks", 0)
        num_v_cracks = results.get("num_vertical_cracks", 0)
        max_spall_ratio = results.get("spalled_ratio", 0)
        num_h_bars = results.get("num_exposed_horizontal_bars", 0)
        num_v_bars = results.get("num_exposed_vertical_bars", 0)

        if damage_level in ["Level 3", "Level 4", "Level 5"]:
            num_h_cracks = "N/A"
            num_v_cracks = "N/A"

        html_content = f'''
<!DOCTYPE html>
<html>
<head>
<style>
body {{
    background-color: #f8f9fa;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    padding: 15px;
    color: #212529;
}}
.results-container {{
    padding: 0;
}}
h3 {{
    font-size: 1.5rem;
    margin-bottom: 2rem;
    border-bottom: 1px solid #dee2e6;
    padding-bottom: 1rem;
}}
.result-item {{
    background-color: #fff;
    padding: 0.75rem 1.25rem;
    margin-bottom: 10px;
    border: 1px solid #dee2e6;
    border-radius: 0.25rem;
    font-size: 1rem;
}}
.result-item b {{
    color: #495057;
}}
.damage-state {{
    background-color: #f8d7da;
    border-color: #f5c6cb;
    color: #721c24;
}}
.damage-state b {{
    color: #721c24;
}}
</style>
</head>
<body>
<div class="results-container">
    <h3>PDA Results</h3>
    <hr/>
    <div class="result-item">
        <b>Number of horizontal cracks</b> = {num_h_cracks}
    </div>
    <div class="result-item">
        <b>Number of vertical cracks</b> = {num_v_cracks}
    </div>
    <div class="result-item">
        <b>Maximum spalled ratio</b> = {max_spall_ratio:.2f} %
    </div>
    <div class="result-item">
        <b>Number of exposed horizontal bars</b> = {num_h_bars}
    </div>
    <div class="result-item">
        <b>Number of exposed vertical bars</b> = {num_v_bars}
    </div>
    <div class="result-item damage-state">
        <b>Damage state</b> = {damage_level}
    </div>
</div>
</body>
</html>
'''
        self.results_panel.setHtml(html_content)


    def enable_pan_mode(self):
        self.image_viewer.setDragMode(QGraphicsView.ScrollHandDrag)

    def on_toggle_defects(self):
        if self.last_results and self.current_file_path:
            self.controller.update_image_display(
                self.current_file_path,
                self.last_results,
                show_cracks=self.show_defects_checkbox.isChecked(),
            )
