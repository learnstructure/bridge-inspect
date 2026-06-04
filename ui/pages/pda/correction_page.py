# ui/pages/pda/correction_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QLabel, QMessageBox
)
from PySide6.QtCore import Qt

from services.cv_service import class_names
from ui.widgets.image_viewer import ImageViewer
from ui.widgets.results_panel import ResultsPanel

class CorrectionPage(QWidget):
    """A page for manual correction of the column mask and overriding results."""
    def __init__(self):
        super().__init__()
        self.controller = None
        self.current_file_path = None
        self.last_results = None

        main_layout = QVBoxLayout(self)

        instructions = QLabel(
            "<b>Instructions:</b><br>"
            "1. To adjust the column area, click and drag on the image, then click 'Update from New Mask'.<br>"
            "2. To manually override the detected defect counts, edit the values in the panel and click 'Override Results'."
        )
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)

        splitter = QSplitter(Qt.Horizontal)
        
        self.image_viewer = ImageViewer()
        
        self.results_panel = ResultsPanel(is_editable=True, show_update_button=False)
        
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        right_panel_layout.addWidget(self.results_panel)
        right_panel_layout.addStretch()

        # --- New Button Layout ---
        self.update_mask_btn = QPushButton("Update from New Mask")
        self.restore_btn = QPushButton("Restore Original")
        self.override_btn = QPushButton("Override Results")

        # Vertical layout for all buttons
        button_container_layout = QVBoxLayout()
        # Horizontal layout for the bottom two buttons
        bottom_button_layout = QHBoxLayout()
        bottom_button_layout.addWidget(self.restore_btn)
        bottom_button_layout.addWidget(self.override_btn)

        # Add the top button and the bottom layout to the container
        button_container_layout.addWidget(self.update_mask_btn)
        button_container_layout.addLayout(bottom_button_layout)

        right_panel_layout.addLayout(button_container_layout)
        # --- End New Button Layout ---

        splitter.addWidget(self.image_viewer)
        splitter.addWidget(right_panel_widget)
        splitter.setSizes([700, 300])

        main_layout.addWidget(splitter)

    def set_controller(self, controller):
        self.controller = controller
        self.restore_btn.clicked.connect(self.on_restore_original)
        self.update_mask_btn.clicked.connect(self.on_update_mask)
        self.override_btn.clicked.connect(self.on_override_results)

    def display_image(self, file_path):
        self.current_file_path = file_path
        self.image_viewer.load_image(file_path)
        
    def display_column_roi(self, results):
        if not results: return
        try:
            class_ids = results.get("class_ids", [])
            column_indices = [i for i, cid in enumerate(class_ids) if 0 <= cid < len(class_names) and class_names[cid] == 'column']
            if column_indices:
                column_roi = results["rois"][column_indices[0]]
                self.image_viewer.draw_bbox(column_roi)
        except (IndexError, KeyError) as e:
            QMessageBox.warning(self, "Warning", f"Could not display the original column ROI: {e}")

    def on_update_mask(self):
        if not self.controller or not self.current_file_path:
            QMessageBox.warning(self, "Warning", "Please run an analysis on an image first.")
            return

        new_coords = self.image_viewer.get_drawn_rect_coords()
        if not new_coords:
            QMessageBox.information(self, "Information", "Please draw a new rectangle on the image first.")
            return
        
        self.controller.recalculate_results_with_new_mask(new_coords)
        QMessageBox.information(self, "Success", "Results have been updated based on the new mask.")

    def on_restore_original(self):
        if not self.controller: return
        self.image_viewer.clear_all_rects()
        self.controller.restore_original_results()
        QMessageBox.information(self, "Restored", "The original analysis results have been restored.")
        
    def on_override_results(self):
        """Handler for the new 'Override Results' button."""
        if not self.controller or not self.last_results:
            QMessageBox.warning(self, "Warning", "No analysis results are available to override.")
            return

        updated_values = self.results_panel.get_values()
        if updated_values is None: return

        data_to_update = self.last_results.copy()
        data_to_update.update(updated_values)

        self.controller.update_damage_assessment(data_to_update)
        QMessageBox.information(self, "Success", "The damage assessment has been overridden with your values.")

    def display_updated_results(self, results):
        self.last_results = results
        self.results_panel.update_results(results)
        self.image_viewer.clear_all_rects()
        if results:
            self.display_column_roi(results)
