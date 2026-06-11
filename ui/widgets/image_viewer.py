# ui/widgets/image_viewer.py
import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QCursor, QImage, QPen, QPixmap, QPainter
from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsScene, QGraphicsView, QGraphicsObject, QLabel
)

from services.cv_service import class_names


class HandleItem(QGraphicsRectItem):
    """A resize handle for the InteractiveRectItem."""

    def __init__(self, position, parent):
        super().__init__(-5, -5, 10, 10, parent)
        self.position = position
        self.parent_item = parent
        self.setBrush(QBrush(QColor("cyan")))
        self.setPen(QPen(QColor("black"), 1))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setZValue(10)

    def hoverEnterEvent(self, event):
        cursors = {
            1: Qt.SizeFDiagCursor, 2: Qt.SizeVerCursor, 3: Qt.SizeBDiagCursor,
            4: Qt.SizeHorCursor, 5: Qt.SizeHorCursor,
            6: Qt.SizeBDiagCursor, 7: Qt.SizeVerCursor, 8: Qt.SizeFDiagCursor
        }
        self.setCursor(cursors.get(self.position, Qt.ArrowCursor))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setCursor(Qt.ArrowCursor)
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            return self.parent_item.handle_moved(self.position, value)
        return super().itemChange(change, value)
    
    def mouseReleaseEvent(self, event):
        self.parent_item.resize_finished()
        super().mouseReleaseEvent(event)


class InteractiveRectItem(QGraphicsObject):
    """A bounding box that is selectable, hoverable, and resizable via handles."""
    
    resized = Signal(int, QRectF)

    def __init__(self, rect, index, class_id, viewer):
        super().__init__()
        self._rect = QRectF(rect)
        self.index = index
        self.class_id = class_id
        self.viewer = viewer
        self.handles = []
        self.is_selected = False

        class_name = class_names[self.class_id] if 0 <= self.class_id < len(class_names) else "Unknown"
        pen_color = Qt.darkCyan if class_name == 'column' else Qt.green
        self._original_pen = QPen(pen_color, 2, Qt.DashLine)
        self._pen = self._original_pen

        self.setZValue(0 if class_name == 'column' else 1)
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        handle_size = 10
        pen_width = self.pen().widthF()
        adjust = handle_size / 2 + pen_width
        return self._rect.adjusted(-adjust, -adjust, adjust, adjust)

    def paint(self, painter, option, widget=None):
        painter.setPen(self._pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self._rect)

    def pen(self):
        return self._pen

    def setPen(self, pen):
        self._pen = pen
        self.update()

    def rect(self):
        return self._rect

    def setRect(self, rect):
        rect = QRectF(rect)
        if self._rect == rect:
            return
        self.prepareGeometryChange()
        self._rect = rect
        if self.is_selected:
            self.update_handles()
        self.update()

    def set_selected(self, selected):
        if self.is_selected == selected:
            return
        self.is_selected = selected

        if selected:
            selected_pen = QPen(Qt.yellow, 3, Qt.SolidLine)
            self.setPen(selected_pen)
            self.add_handles()
        else:
            self.setPen(self._original_pen)
            self.remove_handles()
        self.update()

    def add_handles(self):
        self.remove_handles()
        rect = self.rect()
        positions = [
            rect.topLeft(), QPointF(rect.center().x(), rect.top()), rect.topRight(),
            QPointF(rect.left(), rect.center().y()), QPointF(rect.right(), rect.center().y()),
            rect.bottomLeft(), QPointF(rect.center().x(), rect.bottom()), rect.bottomRight(),
        ]
        for i, pos in enumerate(positions, 1):
            handle = HandleItem(i, self)
            handle.setPos(pos)
            self.handles.append(handle)

    def remove_handles(self):
        for handle in self.handles:
            if handle.scene():
                self.scene().removeItem(handle)
        self.handles.clear()

    def handle_moved(self, handle_pos, new_pos):
        rect = self.rect()
        if handle_pos == 1: rect.setTopLeft(new_pos)
        elif handle_pos == 2: rect.setTop(new_pos.y())
        elif handle_pos == 3: rect.setTopRight(new_pos)
        elif handle_pos == 4: rect.setLeft(new_pos.x())
        elif handle_pos == 5: rect.setRight(new_pos.x())
        elif handle_pos == 6: rect.setBottomLeft(new_pos)
        elif handle_pos == 7: rect.setBottom(new_pos.y())
        elif handle_pos == 8: rect.setBottomRight(new_pos)
        
        self.setRect(rect.normalized())
        return new_pos

    def update_handles(self):
        if not self.is_selected: return
        rect = self.rect()
        positions = [
            rect.topLeft(), QPointF(rect.center().x(), rect.top()), rect.topRight(),
            QPointF(rect.left(), rect.center().y()), QPointF(rect.right(), rect.center().y()),
            rect.bottomLeft(), QPointF(rect.center().x(), rect.bottom()), rect.bottomRight(),
        ]
        for i, handle in enumerate(self.handles):
            handle.setPos(positions[i])

    def resize_finished(self):
        self.resized.emit(self.index, self.rect())

    def hoverEnterEvent(self, event):
        self.viewer.viewport().setCursor(Qt.PointingHandCursor)
        if not self.is_selected:
            highlight_pen = QPen(QColor("cyan"), self._original_pen.widthF() + 1, Qt.SolidLine)
            self.setPen(highlight_pen)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.viewer.viewport().setCursor(Qt.CrossCursor)
        if not self.is_selected:
            self.setPen(self._original_pen)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.viewer.box_clicked.emit(self.index)
            event.accept()
        else:
            super().mousePressEvent(event)


class ImageViewer(QGraphicsView):
    box_clicked = Signal(int)
    box_resize_finished = Signal(int, list)
    image_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self._pixmap_item = None
        self.bbox_items = []
        self.drawn_rect_item = None
        self.start_pos = None
        self.is_drawing = False
        self._read_only = False

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.viewport().setCursor(Qt.CrossCursor)

        # Add a placeholder for drop instructions
        self.drop_placeholder = QLabel("Drag & Drop Image Here", self)
        self.drop_placeholder.setAlignment(Qt.AlignCenter)
        self.drop_placeholder.setStyleSheet("color: grey; font-size: 20px;")

    def setReadOnly(self, is_read_only: bool):
        self._read_only = is_read_only
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        cursor = Qt.ArrowCursor if is_read_only else Qt.CrossCursor
        self.viewport().setCursor(cursor)

    def load_image(self, image_data, is_np_array=False):
        self.clear_image()
        self.drop_placeholder.hide()
        if is_np_array:
            image_data = np.ascontiguousarray(image_data)
            h, w, ch = image_data.shape
            q_img = QImage(image_data.data, w, h, ch * w, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
        else:
            pixmap = QPixmap(image_data)
        self._pixmap_item = self.scene.addPixmap(pixmap)
        self.setSceneRect(pixmap.rect())
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def wheelEvent(self, event):
        zoom_factor = 1.25
        if event.angleDelta().y() > 0: self.scale(zoom_factor, zoom_factor)
        else: self.scale(1 / zoom_factor, 1 / zoom_factor)

    def mousePressEvent(self, event):
        if not self._read_only and event.button() == Qt.RightButton:
            self.is_drawing = True
            self.start_pos = self.mapToScene(event.pos())
            if self.drawn_rect_item: self.scene.removeItem(self.drawn_rect_item)
            self.drawn_rect_item = QGraphicsRectItem(QRectF(self.start_pos, self.start_pos))
            self.drawn_rect_item.setPen(QPen(Qt.red, 3, Qt.SolidLine))
            self.scene.addItem(self.drawn_rect_item)
            self.setDragMode(QGraphicsView.NoDrag)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            rect = QRectF(self.start_pos, self.mapToScene(event.pos())).normalized()
            self.drawn_rect_item.setRect(rect)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.is_drawing and event.button() == Qt.RightButton:
            self.is_drawing = False
            if not self._read_only: self.setDragMode(QGraphicsView.ScrollHandDrag)
        super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()
            self.drop_placeholder.setText("Drop Image to Load")
            self.drop_placeholder.setStyleSheet("background-color: rgba(0, 0, 0, 0.5); color: white; font-size: 20px;")
            self.drop_placeholder.show()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.drop_placeholder.setText("Drag & Drop Image Here")
        self.drop_placeholder.setStyleSheet("color: grey; font-size: 20px;")
        if self._pixmap_item is None:
            self.drop_placeholder.show()
        else:
            self.drop_placeholder.hide()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                self.image_dropped.emit(file_path)
        self.dragLeaveEvent(None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.drop_placeholder.setGeometry(self.rect())

    def draw_bbox(self, index, bbox_coords, class_id, is_selected=False):
        if bbox_coords is None or not np.any(bbox_coords): return
        y1, x1, y2, x2 = bbox_coords
        bbox_item = InteractiveRectItem(QRectF(QPointF(x1, y1), QPointF(x2, y2)), index, class_id, self)
        bbox_item.set_selected(is_selected)
        bbox_item.resized.connect(self.on_box_resized)
        self.scene.addItem(bbox_item)
        self.bbox_items.append(bbox_item)

    def on_box_resized(self, index, rectF):
        coords = [int(rectF.top()), int(rectF.left()), int(rectF.bottom()), int(rectF.right())]
        self.box_resize_finished.emit(index, coords)

    def get_drawn_rect_coords(self):
        if not self.drawn_rect_item: return None
        rect = self.drawn_rect_item.rect()
        return [int(rect.top()), int(rect.left()), int(rect.bottom()), int(rect.right())]

    def clear_all_rects(self):
        for item in self.bbox_items:
            item.remove_handles()
            if item.scene(): self.scene.removeItem(item)
        self.bbox_items.clear()
        if self.drawn_rect_item:
            if self.drawn_rect_item.scene(): self.scene.removeItem(self.drawn_rect_item)
            self.drawn_rect_item = None

    def clear_image(self):
        self.scene.clear()
        self._pixmap_item = None
        self.bbox_items.clear()
        self.drawn_rect_item = None
        self.drop_placeholder.show()
