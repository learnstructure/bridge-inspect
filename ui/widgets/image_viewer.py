# ui/widgets/image_viewer.py
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PySide6.QtGui import QPixmap, QWheelEvent, QPen, QImage
from PySide6.QtCore import Qt, QPointF, QRectF
import numpy as np

class ImageViewer(QGraphicsView):
    """
    A widget for displaying images that supports panning, zooming, and drawing a rectangle.
    Can be set to read-only to disable drawing.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self._pixmap_item = None
        
        # --- Drawing and BBox Attributes ---
        self.bbox_item = None
        self.drawn_rect_item = None
        self.start_pos = None
        self.is_drawing = False
        self._read_only = False  # New attribute to control drawing

        # --- Interaction Settings ---
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def setReadOnly(self, is_read_only: bool):
        """Enable or disable drawing on the widget."""
        self._read_only = is_read_only
        # If turning to read-only, ensure drag mode is enabled for panning.
        if self._read_only:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        # If turning off read-only (making it editable), disable drag to allow drawing.
        # The drawing events will manage the drag mode from here.
        else:
            self.setDragMode(QGraphicsView.NoDrag)

    def load_image(self, image_data, is_np_array=False):
        if is_np_array:
            # Ensure data is contiguous
            if not image_data.flags['C_CONTIGUOUS']:
                image_data = np.ascontiguousarray(image_data)
            h, w, ch = image_data.shape
            bytes_per_line = ch * w
            q_img = QImage(image_data.data, w, h, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
        else:
            pixmap = QPixmap(image_data)

        if self._pixmap_item:
            self.scene.removeItem(self._pixmap_item)
        
        self.clear_all_rects()
        
        self._pixmap_item = self.scene.addPixmap(pixmap)
        self.setSceneRect(pixmap.rect())
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.25
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)

    # --- Drawing and BBox Methods ---

    def mousePressEvent(self, event):
        if self._read_only or event.button() != Qt.LeftButton:
            super().mousePressEvent(event)
            return

        self.start_pos = self.mapToScene(event.pos())
        self.is_drawing = True

        if self.drawn_rect_item:
            self.scene.removeItem(self.drawn_rect_item)
        
        self.drawn_rect_item = QGraphicsRectItem(QRectF(self.start_pos, self.start_pos))
        pen = QPen(Qt.red, 3, Qt.SolidLine)
        self.drawn_rect_item.setPen(pen)
        self.scene.addItem(self.drawn_rect_item)
        
        self.setDragMode(QGraphicsView.NoDrag)

    def mouseMoveEvent(self, event):
        if not self._read_only and self.is_drawing:
            current_pos = self.mapToScene(event.pos())
            rect_to_draw = QRectF(self.start_pos, current_pos).normalized()
            self.drawn_rect_item.setRect(rect_to_draw)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self._read_only and event.button() == Qt.LeftButton and self.is_drawing:
            self.is_drawing = False
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        else:
            super().mouseReleaseEvent(event)

    def draw_bbox(self, bbox_coords):
        if self.bbox_item:
            self.scene.removeItem(self.bbox_item)
        if not bbox_coords: return
        y1, x1, y2, x2 = bbox_coords
        rect = QRectF(QPointF(x1, y1), QPointF(x2, y2))
        self.bbox_item = QGraphicsRectItem(rect)
        pen = QPen(Qt.green, 2, Qt.DashLine)
        self.bbox_item.setPen(pen)
        self.scene.addItem(self.bbox_item)

    def get_drawn_rect_coords(self):
        if not self.drawn_rect_item:
            return None
        rect = self.drawn_rect_item.rect()
        return [int(rect.top()), int(rect.left()), int(rect.bottom()), int(rect.right())]

    def clear_all_rects(self):
        if self.bbox_item:
            self.scene.removeItem(self.bbox_item)
            self.bbox_item = None
        if self.drawn_rect_item:
            self.scene.removeItem(self.drawn_rect_item)
            self.drawn_rect_item = None

    def clear_image(self):
        """Clears the image and all drawings from the view."""
        self.scene.clear()
        self._pixmap_item = None
        self.bbox_item = None
        self.drawn_rect_item = None