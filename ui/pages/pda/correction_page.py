# ui/pages/pda/correction_page.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter, QLabel, 
    QMessageBox, QListWidget, QListWidgetItem, QComboBox, QFrame
)
from PySide6.QtCore import Qt

from services.cv_service import class_names
from ui.widgets.image_viewer import ImageViewer

# Map for UI display names
DISPLAY_NAME_MAP = {
    "horizontal": "Horizontal bar",
    "vertical": "Vertical bar",
    "spalling": "Spalling",
    "column": "Column"
}
# Reverse map for controller communication
INTERNAL_NAME_MAP = {v: k for k, v in DISPLAY_NAME_MAP.items()}


class CorrectionPage(QWidget):
    """A page for manual correction of masks and overriding results."""

    def __init__(self):
        super().__init__()
        self.controller = None
        self.current_file_path = None
        self.last_results = None

        main_layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        self.image_viewer = ImageViewer()
        self.image_viewer.box_clicked.connect(self.on_box_clicked)
        self.image_viewer.box_resize_finished.connect(self.on_box_resized)

        # --- Right Panel ---
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)

        self.defect_list = QListWidget()
        self.defect_list.itemSelectionChanged.connect(self.on_defect_selection_changed)

        self.new_defect_class_combo = QComboBox()
        # Populate with user-friendly names
        addable_classes = [name for name in class_names if name not in ['column', 'BG']]
        addable_display_names = [DISPLAY_NAME_MAP.get(name, name) for name in addable_classes]
        self.new_defect_class_combo.addItems(addable_display_names)

        self.add_btn = QPushButton("Add New")
        self.delete_btn = QPushButton("Delete Selected")
        self.restore_btn = QPushButton("Restore Original")

        add_layout = QHBoxLayout()
        add_layout.addWidget(self.new_defect_class_combo)
        add_layout.addWidget(self.add_btn)

        button_layout = QVBoxLayout()
        button_layout.addLayout(add_layout)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.restore_btn)

        right_panel_layout.addWidget(QLabel("<b>Detected Objects:</b>"))
        right_panel_layout.addWidget(self.defect_list)
        right_panel_layout.addLayout(button_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        right_panel_layout.addWidget(separator)
        
        instructions = QLabel(
            "<b>Instructions:</b><br>"
            "- Left-click to select a defect, then drag handles to resize.<br>"
            "- Right-click and drag to draw a new defect.<br>"
            "- Use the controls above to manage defects."
        )
        instructions.setWordWrap(True)
        right_panel_layout.addWidget(instructions)
        right_panel_layout.addStretch()

        splitter.addWidget(self.image_viewer)
        splitter.addWidget(right_panel_widget)
        splitter.setSizes([750, 250])

    def set_controller(self, controller):
        self.controller = controller
        self.add_btn.clicked.connect(self.on_add_defect)
        self.delete_btn.clicked.connect(self.on_delete_defect)
        self.restore_btn.clicked.connect(self.on_restore_original)

    def display_image(self, file_path):
        self.current_file_path = file_path
        self.image_viewer.load_image(file_path)
        self.defect_list.clear()

    def display_updated_results(self, results):
        """This method now simply updates the page's display from the controller."""
        self.last_results = results
        
        current_selection = self.get_selected_defect_index()
        self.populate_defect_list()
        self.draw_all_rois()
        
        if 0 <= current_selection < self.defect_list.count():
            self.defect_list.setCurrentRow(current_selection)

    def populate_defect_list(self):
        self.defect_list.blockSignals(True)
        self.defect_list.clear()
        if not self.last_results: 
            self.defect_list.blockSignals(False)
            return

        class_ids = self.last_results.get("class_ids", [])
        for i, class_id in enumerate(class_ids):
            # Use display names for the list
            internal_name = class_names[class_id] if 0 <= class_id < len(class_names) else "Unknown"
            display_name = DISPLAY_NAME_MAP.get(internal_name, internal_name)
            item = QListWidgetItem(f"{i}: {display_name}")
            item.setData(Qt.UserRole, i)
            self.defect_list.addItem(item)
        self.defect_list.blockSignals(False)
            
    def draw_all_rois(self):
        self.image_viewer.clear_all_rects()
        if not self.last_results: return

        rois = self.last_results.get("rois", [])
        class_ids = self.last_results.get("class_ids", [])
        selected_index = self.get_selected_defect_index()

        for i, (roi, cid) in enumerate(zip(rois, class_ids)):
            is_selected = (i == selected_index)
            self.image_viewer.draw_bbox(i, roi, cid, is_selected)

    def on_box_clicked(self, index):
        if 0 <= index < self.defect_list.count():
            self.defect_list.setCurrentRow(index)

    def on_defect_selection_changed(self):
        self.draw_all_rois()

    def get_selected_defect_index(self):
        selected_items = self.defect_list.selectedItems()
        if not selected_items: return -1
        return selected_items[0].data(Qt.UserRole)

    def on_add_defect(self):
        if not self.controller or not self.current_file_path: return
        new_coords = self.image_viewer.get_drawn_rect_coords()
        if not new_coords:
            QMessageBox.information(self, "Information", "Please draw a new rectangle first.")
            return
        
        # Translate display name back to internal name for the controller
        display_name = self.new_defect_class_combo.currentText()
        internal_name = INTERNAL_NAME_MAP.get(display_name, display_name)
        self.controller.add_mask(internal_name, new_coords)
        self.image_viewer.drawn_rect_item = None

    def on_box_resized(self, index, new_coords):
        if self.controller:
            self.controller.update_mask(index, new_coords)

    def on_delete_defect(self):
        selected_index = self.get_selected_defect_index()
        if selected_index == -1: return
        reply = QMessageBox.question(self, '''Confirm Deletion''', '''Are you sure you want to delete the selected mask?''', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.controller.delete_mask(selected_index)

    def on_restore_original(self):
        if not self.controller: return
        self.controller.restore_original_results()
        QMessageBox.information(self, "Restored", "The original analysis results have been restored.")
