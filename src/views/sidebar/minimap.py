"""Minimap — bird's eye view of the MCD canvas."""

from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsView, QLabel, QVBoxLayout, QWidget


class Minimap(QWidget):
    """Scaled-down overview of the MCD canvas with viewport rectangle."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._canvas = None  # MCDCanvas reference
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QLabel("OVERVIEW")
        header.setStyleSheet("font-weight: bold; color: #5F6368; padding: 4px 8px;")
        layout.addWidget(header)

        self._view = MinimapView()
        self._view.setFixedHeight(140)
        layout.addWidget(self._view)

    def set_canvas(self, canvas):
        """Connect to an MCDCanvas to mirror its scene."""
        self._canvas = canvas
        self._view.set_canvas(canvas)

    def refresh(self):
        self._view.update()


class MinimapView(QGraphicsView):
    """The actual minimap rendering widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._canvas = None
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setInteractive(False)
        self.setStyleSheet("border: 1px solid #DADCE0; background: #FAFAFA;")

    def set_canvas(self, canvas):
        self._canvas = canvas
        if canvas and canvas.scene():
            self.setScene(canvas.scene())
            self._fit_scene()
            # Refresh when canvas scrolls or zooms
            canvas.viewport().installEventFilter(self)

    def _fit_scene(self):
        if self.scene():
            scene_rect = self.scene().itemsBoundingRect()
            if not scene_rect.isEmpty():
                padded = scene_rect.adjusted(-50, -50, 50, 50)
                self.fitInView(padded, Qt.AspectRatioMode.KeepAspectRatio)

    def drawForeground(self, painter, rect):
        """Draw viewport rectangle overlay."""
        super().drawForeground(painter, rect)
        if not self._canvas:
            return

        # Get the main canvas visible area in scene coordinates
        visible = self._canvas.mapToScene(self._canvas.viewport().rect()).boundingRect()
        if visible.isEmpty():
            return

        # Draw semi-transparent overlay outside viewport
        painter.setPen(QPen(QColor("#2196F3"), 1.5))
        painter.setBrush(QBrush(QColor(33, 150, 243, 30)))
        painter.drawRect(visible)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_scene()

    def mousePressEvent(self, event):
        """Click to navigate the main canvas."""
        if self._canvas and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self._canvas.centerOn(scene_pos)
            self.update()

    def eventFilter(self, obj, event):
        """Refresh minimap when canvas viewport updates."""
        if obj == (self._canvas.viewport() if self._canvas else None):
            if event.type() in (event.Type.Paint, event.Type.Resize):
                self._fit_scene()
                self.update()
        return super().eventFilter(obj, event)
