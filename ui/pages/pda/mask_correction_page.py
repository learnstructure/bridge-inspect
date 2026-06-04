# ui/pages/pda/mask_correction_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QFormLayout, QLineEdit, QLabel, QMessageBox
)
from PySide6.QtCore import Qt

from services.cv_service import class_names # Import class_names
from ui.widgets.image_viewer import ImageViewer

class MaskCorrectionPage(QWidget):
    """
    A page for users to manually correct the column mask and see updated defect counts.
    """
    def __init__(self):
        super().__init__()
        self.controller = None
        self.current_file_path = None

        main_layout = QVBoxLayout(self)

        # --- Instructions Label ---
        instructions = QLabel("<b>Instructions:</b> Click and drag on the image to draw a new bounding box for the column. Then, click 'Update from New Mask'.")
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setWordWrap(True)
        main_layout.addWidget(instructions)

        # --- Main Content Splitter ---
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel: Image Viewer
        self.image_viewer = ImageViewer()
        
        # Right Panel: Results and Controls
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        
        self.results_form = QFormLayout()
        self.results_form.setRowWrapPolicy(QFormLayout.WrapAllRows)
        self.results_form.setLabelAlignment(Qt.AlignLeft)
        self.results_form.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        self.results_title = QLabel("<h4>Analysis Results</h4>")
        self.damage_level_display = QLineEdit()
        self.num_h_cracks_display = QLineEdit()
        self.num_v_cracks_display = QLineEdit()
        self.spalled_ratio_display = QLineEdit()
        self.num_h_bars_display = QLineEdit()
        self.num_v_bars_display = QLineEdit()
        
        # Make results display-only
        for field in [self.damage_level_display, self.num_h_cracks_display, self.num_v_cracks_display,
                      self.spalled_ratio_display, self.num_h_bars_display, self.num_v_bars_display]:
            field.setReadOnly(True)
            field.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc; padding: 4px;")

        self.results_form.addRow(self.results_title)
        self.results_form.addRow("<b>Damage State:</b>", self.damage_level_display)
        self.results_form.addRow("Horizontal Cracks:", self.num_h_cracks_display)
        self.results_form.addRow("Diagonal Cracks:", self.num_v_cracks_display)
        self.results_form.addRow("Spalled Ratio (%):", self.spalled_ratio_display)
        self.results_form.addRow("Exposed Horizontal Bars:", self.num_h_bars_display)
        self.results_form.addRow("Exposed Vertical Bars:", self.num_v_bars_display)
        
        right_panel_layout.addLayout(self.results_form)
        right_panel_layout.addStretch() # Pushes buttons to the bottom

        # --- Control Buttons ---
        button_layout = QHBoxLayout()
        self.restore_btn = QPushButton("Restore Original")
        self.restore_btn.clicked.connect(self.on_restore_original)
        
        self.update_btn = QPushButton("Update from New Mask")
        self.update_btn.clicked.connect(self.on_update_mask)
        
        button_layout.addWidget(self.restore_btn)
        button_layout.addWidget(self.update_btn)
        right_panel_layout.addLayout(button_layout)

        splitter.addWidget(self.image_viewer)
        splitter.addWidget(right_panel_widget)
        splitter.setSizes([700, 300]) 

        main_layout.addWidget(splitter)

    def set_controller(self, controller):
        self.controller = controller

    def display_image(self, file_path):
        """Loads the image into the viewer and resets the view."""
        self.current_file_path = file_path
        self.image_viewer.load_image(file_path)
        
    def display_column_roi(self, results):
        """Draws the initial AI-detected column bounding box."""
        if not results: return
        try:
            # class_names mapping: 1 -> 'column'
            column_indices = [i for i, class_id in enumerate(results.get("class_ids", [])) if class_names.get(class_id) == 'column']
            if column_indices:
                column_roi = results["rois"][column_indices[0]]
                self.image_viewer.draw_bbox(column_roi) # Green dashed box
        except (IndexError, KeyError) as e:
            QMessageBox.warning(self, "Warning", f"Could not display the original column ROI: {e}")
            
    def on_update_mask(self):
        """Handles the click of the 'Update from New Mask' button."""
        if not self.controller or not self.current_file_path:
            QMessageBox.warning(self, "Warning", "Please run an analysis on an image first.")
            return

        new_coords = self.image_viewer.get_drawn_rect_coords()
        if not new_coords:
            QMessageBox.information(self, "Information", "Please draw a new rectangle (in red) on the image to define the new column area.")
            return
        
        self.controller.recalculate_results_with_new_mask(new_coords)
        QMessageBox.information(self, "Success", "Results have been updated based on the new mask.")

    def on_restore_original(self):
        """Restores the original analysis results and removes the manual mask."""
        if not self.controller:
            QMessageBox.warning(self, "Warning", "Controller not available.")
            return
            
        self.image_viewer.clear_all_rects() # Clears user-drawn rect
        self.controller.restore_original_results()
        QMessageBox.information(self, "Restored", "The original analysis results have been restored.")

    def display_updated_results(self, results):
        """Populates the results panel with data (either original or recalculated)."""
        self.last_results = results
        if not results:
            for field in [self.damage_level_display, self.num_h_cracks_display, self.num_v_cracks_display,
                          self.spalled_ratio_display, self.num_h_bars_display, self.num_v_bars_display]:
                field.setText("")
            self.image_viewer.clear_all_rects()
            return

        damage_level = results.get("damage_level", "N/A")
        num_h_cracks = results.get("num_horizontal_cracks", 0)
        num_v_cracks = results.get("num_vertical_cracks", 0)
        spalled_ratio = results.get("spalled_ratio", 0)
        num_h_bars = results.get("num_exposed_horizontal_bars", 0)
        num_v_bars = results.get("num_exposed_vertical_bars", 0)

        self.damage_level_display.setText(damage_level)
        self.spalled_ratio_display.setText(f"{spalled_ratio:.2f}")
        self.num_h_bars_display.setText(str(num_h_bars))
        self.num_v_bars_display.setText(str(num_v_bars))
        
        is_spalled = damage_level in ["Level 3", "Level 4", "Level 5"]
        self.num_h_cracks_display.setText("N/A" if is_spalled else str(num_h_cracks))
        self.num_v_cracks_display.setText("N/A" if is_spalled else str(num_v_cracks))
        
        # Redraw the original column ROI for context
        self.display_column_roi(results)