# ui/widgets/image_viewer.py
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from PySide6.QtGui import QPixmap, QWheelEvent
from PySide6.QtCore import Qt


class ImageViewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self._pixmap_item = None

        # Drag / Zoom settings
        self.setDragMode(QGraphicsView.ScrollHandDrag)  # allow panning by default
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def load_image(self, file_path):
        pixmap = QPixmap(file_path)
        if self._pixmap_item:
            self.scene.removeItem(self._pixmap_item)
        self._pixmap_item = self.scene.addPixmap(pixmap)
        self.setSceneRect(pixmap.rect())
        self.resetTransform()  # reset zoom

    # Zoom with mouse wheel
    def wheelEvent(self, event: QWheelEvent):
        zoom_factor = 1.25
        if event.angleDelta().y() > 0:
            self.scale(zoom_factor, zoom_factor)
        else:
            self.scale(1 / zoom_factor, 1 / zoom_factor)
