from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsPathItem,
    QStyleOptionGraphicsItem, QWidget
)
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath
)
import math

from ..models.entity import Entity
from ..models.association import Association
from ..models.link import Link
from ..utils.constants import (
    ENTITY_WIDTH, ENTITY_HEIGHT, ENTITY_COLOR, ENTITY_BORDER,
    ASSOCIATION_WIDTH, ASSOCIATION_HEIGHT, ASSOCIATION_COLOR, ASSOCIATION_BORDER,
    LINK_COLOR, SELECTED_COLOR
)


class EntityItem(QGraphicsItem):
    """Graphical representation of an MCD entity."""

    # Class-level setting for showing attributes
    show_attributes = True
    HEADER_HEIGHT = 30
    ATTR_HEIGHT = 20
    MIN_WIDTH = ENTITY_WIDTH

    def __init__(self, entity: Entity, parent=None):
        super().__init__(parent)
        self.entity = entity
        self.setPos(entity.x, entity.y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCursor(Qt.OpenHandCursor)
        self._links: list["LinkItem"] = []
        self._update_size()

    def _update_size(self):
        """Update size based on content."""
        self.prepareGeometryChange()
        if EntityItem.show_attributes and self.entity.attributes:
            self._width = max(self.MIN_WIDTH, self._calculate_width())
            self._height = self.HEADER_HEIGHT + len(self.entity.attributes) * self.ATTR_HEIGHT + 10
        else:
            self._width = self.MIN_WIDTH
            self._height = ENTITY_HEIGHT

    def _calculate_width(self):
        """Calculate width based on longest attribute text."""
        max_len = len(self.entity.name) * 8  # Approximate width for name
        for attr in self.entity.attributes:
            # Format: "name : TYPE" or with underline for PK
            attr_text = f"{attr.name} : {attr.data_type}"
            if attr.size:
                attr_text += f"({attr.size})"
            max_len = max(max_len, len(attr_text) * 7)
        return max_len + 20  # padding

    def boundingRect(self) -> QRectF:
        return QRectF(-self._width / 2, -self._height / 2, self._width, self._height)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        rect = self.boundingRect()
        path = QPainterPath()
        path.addRoundedRect(rect, 10, 10)

        # Fill
        if self.isSelected():
            painter.setBrush(QBrush(QColor(SELECTED_COLOR).lighter(150)))
            painter.setPen(QPen(QColor(SELECTED_COLOR), 2))
        else:
            painter.setBrush(QBrush(QColor(ENTITY_COLOR)))
            painter.setPen(QPen(QColor(ENTITY_BORDER), 2))

        painter.drawPath(path)

        # Draw entity name (header)
        painter.setPen(Qt.black)
        font = QFont()
        font.setBold(True)
        painter.setFont(font)

        if EntityItem.show_attributes and self.entity.attributes:
            # Draw header with name
            header_rect = QRectF(rect.left(), rect.top(), rect.width(), self.HEADER_HEIGHT)
            painter.drawText(header_rect, Qt.AlignCenter, self.entity.name)

            # Draw separator line
            sep_y = rect.top() + self.HEADER_HEIGHT
            painter.setPen(QPen(QColor(ENTITY_BORDER), 1))
            painter.drawLine(int(rect.left() + 5), int(sep_y), int(rect.right() - 5), int(sep_y))

            # Draw attributes
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(Qt.black)

            y = rect.top() + self.HEADER_HEIGHT + 5
            for attr in self.entity.attributes:
                attr_text = f"{attr.name} : {attr.data_type}"
                if attr.size:
                    attr_text += f"({attr.size})"

                text_rect = QRectF(rect.left() + 10, y, rect.width() - 20, self.ATTR_HEIGHT)

                if attr.is_primary_key:
                    # Underline for primary key
                    font.setUnderline(True)
                    painter.setFont(font)
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, attr_text)
                    font.setUnderline(False)
                    painter.setFont(font)
                else:
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, attr_text)

                y += self.ATTR_HEIGHT
        else:
            # Compact mode - just name centered
            painter.drawText(rect, Qt.AlignCenter, self.entity.name)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Update entity coordinates
            pos = self.pos()
            self.entity.x = pos.x()
            self.entity.y = pos.y()
            # Update connected links
            for link_item in self._links:
                link_item.update_position()
        return super().itemChange(change, value)

    def add_link(self, link_item: "LinkItem"):
        """Register a link item connected to this entity."""
        if link_item not in self._links:
            self._links.append(link_item)

    def remove_link(self, link_item: "LinkItem"):
        """Unregister a link item."""
        if link_item in self._links:
            self._links.remove(link_item)

    def get_center(self) -> QPointF:
        """Get the center point in scene coordinates."""
        return self.scenePos()

    def get_edge_point(self, target: QPointF) -> QPointF:
        """Get the point on the rectangle edge closest to the target."""
        center = self.scenePos()
        dx = target.x() - center.x()
        dy = target.y() - center.y()

        if dx == 0 and dy == 0:
            return center

        # Half dimensions
        hw = self._width / 2
        hh = self._height / 2

        # Calculate intersection with rectangle edges
        if abs(dx) * hh > abs(dy) * hw:
            # Intersects left or right edge
            if dx > 0:
                return QPointF(center.x() + hw, center.y() + dy * hw / dx)
            else:
                return QPointF(center.x() - hw, center.y() - dy * hw / dx)
        else:
            # Intersects top or bottom edge
            if dy > 0:
                return QPointF(center.x() + dx * hh / dy, center.y() + hh)
            else:
                return QPointF(center.x() - dx * hh / dy, center.y() - hh)

    def refresh(self):
        """Refresh the item after entity changes."""
        self._update_size()
        self.update()
        # Update connected links
        for link_item in self._links:
            link_item.update_position()


class AssociationItem(QGraphicsItem):
    """Graphical representation of an MCD association (rounded octagon/diamond shape)."""

    def __init__(self, association: Association, parent=None):
        super().__init__(parent)
        self.association = association
        self.setPos(association.x, association.y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCursor(Qt.OpenHandCursor)
        self._width = ASSOCIATION_WIDTH
        self._height = ASSOCIATION_HEIGHT
        self._links: list["LinkItem"] = []

    def boundingRect(self) -> QRectF:
        return QRectF(-self._width / 2, -self._height / 2, self._width, self._height)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        # Create rounded diamond/octagon shape
        rect = self.boundingRect()
        path = QPainterPath()

        # Create a rounded diamond shape
        cx, cy = 0, 0
        w, h = self._width / 2, self._height / 2
        corner = 15  # Corner rounding

        path.moveTo(cx - w + corner, cy)
        path.lineTo(cx, cy - h + corner)
        path.lineTo(cx + w - corner, cy)
        path.lineTo(cx, cy + h - corner)
        path.closeSubpath()

        # Fill
        if self.isSelected():
            painter.setBrush(QBrush(QColor(SELECTED_COLOR).lighter(150)))
            painter.setPen(QPen(QColor(SELECTED_COLOR), 2))
        else:
            painter.setBrush(QBrush(QColor(ASSOCIATION_COLOR)))
            painter.setPen(QPen(QColor(ASSOCIATION_BORDER), 2))

        painter.drawPath(path)

        # Draw association name
        painter.setPen(Qt.black)
        font = QFont()
        font.setItalic(True)
        painter.setFont(font)
        text_rect = QRectF(-self._width / 2 + 5, -15, self._width - 10, 30)
        painter.drawText(text_rect, Qt.AlignCenter, self.association.name)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Update association coordinates
            pos = self.pos()
            self.association.x = pos.x()
            self.association.y = pos.y()
            # Update connected links
            for link_item in self._links:
                link_item.update_position()
        return super().itemChange(change, value)

    def add_link(self, link_item: "LinkItem"):
        """Register a link item connected to this association."""
        if link_item not in self._links:
            self._links.append(link_item)

    def remove_link(self, link_item: "LinkItem"):
        """Unregister a link item."""
        if link_item in self._links:
            self._links.remove(link_item)

    def get_center(self) -> QPointF:
        """Get the center point in scene coordinates."""
        return self.scenePos()

    def get_edge_point(self, target: QPointF) -> QPointF:
        """Get the point on the diamond edge closest to the target."""
        center = self.scenePos()
        dx = target.x() - center.x()
        dy = target.y() - center.y()

        if dx == 0 and dy == 0:
            return center

        # Diamond half dimensions (adjusted for the corner offset)
        hw = self._width / 2 - 15  # corner offset
        hh = self._height / 2 - 15

        # For a diamond, the edge equation is |x|/hw + |y|/hh = 1
        # Find the scale factor to reach the edge
        scale = 1.0 / (abs(dx) / hw + abs(dy) / hh) if (abs(dx) / hw + abs(dy) / hh) > 0 else 1.0

        return QPointF(center.x() + dx * scale, center.y() + dy * scale)

    def refresh(self):
        """Refresh the item after association changes."""
        self.update()
        # Update connected links
        for link_item in self._links:
            link_item.update_position()


class LinkItem(QGraphicsLineItem):
    """Graphical representation of a link between entity and association."""

    def __init__(
        self,
        link: Link,
        entity_item: EntityItem,
        association_item: AssociationItem,
        parent=None
    ):
        super().__init__(parent)
        self.link = link
        self.entity_item = entity_item
        self.association_item = association_item

        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setPen(QPen(QColor(LINK_COLOR), 2))

        # Create cardinality label
        self._card_label = QGraphicsTextItem(self)
        font = QFont()
        font.setBold(True)
        self._card_label.setFont(font)

        # Register with connected items
        entity_item.add_link(self)
        association_item.add_link(self)

        self.update_position()

    def update_position(self):
        """Update line position based on connected items."""
        # Get centers first to calculate direction
        entity_center = self.entity_item.get_center()
        assoc_center = self.association_item.get_center()

        # Get edge points (where line meets the shape borders)
        p1 = self.entity_item.get_edge_point(assoc_center)
        p2 = self.association_item.get_edge_point(entity_center)

        self.setLine(p1.x(), p1.y(), p2.x(), p2.y())

        # Position cardinality label near entity edge
        # Place label slightly offset from the entity edge point
        label_x = p1.x() + (p2.x() - p1.x()) * 0.15 - 15
        label_y = p1.y() + (p2.y() - p1.y()) * 0.15 - 10

        self._card_label.setPlainText(f"({self.link.cardinality})")
        self._card_label.setPos(label_x, label_y)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        if self.isSelected():
            self.setPen(QPen(QColor(SELECTED_COLOR), 3))
        else:
            self.setPen(QPen(QColor(LINK_COLOR), 2))
        super().paint(painter, option, widget)

    def cleanup(self):
        """Remove this link from connected items."""
        self.entity_item.remove_link(self)
        self.association_item.remove_link(self)
