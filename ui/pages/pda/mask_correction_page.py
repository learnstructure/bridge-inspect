# ui/pages/pda/mask_correction_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, 
    QFormLayout, QLineEdit, QLabel, QGraphicsView
)
from PySide6.QtCore import Qt
from ui.widgets.image_viewer import ImageViewer

class MaskCorrectionPage(QWidget):
    """A page for users to manually correct the column bounding box."""
    def __init__(self):
        super().__init__()
        self.controller = None

        main_layout = QVBoxLayout(self)

        # Top action buttons - these might be shared or context-specific
        top_btn_layout = QHBoxLayout()
        # For now, let's assume the image is already loaded from the Analysis page
        # We can add an upload button here if needed later.
        self.refresh_btn = QPushButton("Load Latest Image")
        top_btn_layout.addWidget(self.refresh_btn)

        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        self.image_viewer = ImageViewer() # This will show the image with masks

        # --- Correction Panel ---
        self.correction_widget = QWidget()
        self.correction_layout = QFormLayout(self.correction_widget)
        self.correction_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.correction_layout.setLabelAlignment(Qt.AlignLeft)
        self.correction_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.correction_widget.setLayout(self.correction_layout)

        self.correction_title = QLabel("<h3>Column Bounding Box</h3>")
        self.bbox_y1_input = QLineEdit()
        self.bbox_x1_input = QLineEdit()
        self.bbox_y2_input = QLineEdit()
        self.bbox_x2_input = QLineEdit()

        self.correction_layout.addRow(self.correction_title)
        self.correction_layout.addRow("Top (y1):", self.bbox_y1_input)
        self.correction_layout.addRow("Left (x1):", self.bbox_x1_input)
        self.correction_layout.addRow("Bottom (y2):", self.bbox_y2_input)
        self.correction_layout.addRow("Right (x2):", self.bbox_x2_input)
        
        self.update_mask_btn = QPushButton("Update Column Mask")
        self.correction_layout.addWidget(self.update_mask_btn)
        # ---------------------

        splitter.addWidget(self.image_viewer)
        splitter.addWidget(self.correction_widget)
        splitter.setSizes([700, 300])

        main_layout.addLayout(top_btn_layout)
        main_layout.addWidget(splitter)

    def set_controller(self, controller):
        self.controller = controller
        # Connect signals
        # self.update_mask_btn.clicked.connect(self.on_update_mask)
        # self.refresh_btn.clicked.connect(self.on_refresh)

    def on_refresh(self):
        """Placeholder to load the latest image and data from the controller."""
        print("Refreshing Mask Correction Page")

    def on_update_mask(self):
        """Placeholder for sending updated bbox to the controller."""
        if self.controller:
            try:
                new_bbox = [
                    int(self.bbox_y1_input.text()),
                    int(self.bbox_x1_input.text()),
                    int(self.bbox_y2_input.text()),
                    int(self.bbox_x2_input.text()),
                ]
                # self.controller.update_column_mask(new_bbox)
                print(f"Requesting mask update with bbox: {new_bbox}")
            except (ValueError, TypeError):
                print("Invalid input for bounding box.")

    def display_image(self, file_path):
        self.image_viewer.load_image(file_path)

    def display_column_bbox(self, results):
        """Extracts the column bbox from results and populates the fields."""
        if not results or "rois" not in results or "class_ids" not in results:
            return
        
        class_ids = results["class_ids"]
        rois = results["rois"]

        # Find the first instance of a "column" (class_id == 1)
        column_indices = [i for i, cid in enumerate(class_ids) if cid == 1]
        if not column_indices:
            return # No column found
        
        col_index = column_indices[0]
        y1, x1, y2, x2 = rois[col_index]

        self.bbox_y1_input.setText(str(int(y1)))
        self.bbox_x1_input.setText(str(int(x1)))
        self.bbox_y2_input.setText(str(int(y2)))
        self.bbox_x2_input.setText(str(int(x2)))
