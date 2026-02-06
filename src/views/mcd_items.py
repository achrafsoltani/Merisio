from PySide6.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem,
    QGraphicsLineItem, QGraphicsTextItem, QGraphicsPathItem,
    QStyleOptionGraphicsItem, QWidget
)
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QFontMetrics, QPainterPath
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

    # Class-level colors (can be updated from project settings)
    fill_color = ENTITY_COLOR
    border_color = ENTITY_BORDER

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
        # Measure entity name with bold font (as drawn)
        bold_font = QFont()
        bold_font.setBold(True)
        fm_bold = QFontMetrics(bold_font)
        name_width = fm_bold.horizontalAdvance(self.entity.name) + 20

        if EntityItem.show_attributes and self.entity.attributes:
            self._width = max(self.MIN_WIDTH, name_width, self._calculate_width())
            self._height = self.HEADER_HEIGHT + len(self.entity.attributes) * self.ATTR_HEIGHT + 10
        else:
            self._width = max(self.MIN_WIDTH, name_width)
            self._height = ENTITY_HEIGHT

    def _calculate_width(self):
        """Calculate width based on longest attribute text."""
        fm = QFontMetrics(QFont())
        max_width = 0
        for attr in self.entity.attributes:
            attr_text = f"{attr.name} : {attr.data_type}"
            if attr.size:
                attr_text += f"({attr.size})"
            max_width = max(max_width, fm.horizontalAdvance(attr_text))
        return max_width + 20  # padding

    def boundingRect(self) -> QRectF:
        return QRectF(-self._width / 2, -self._height / 2, self._width, self._height)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        rect = self.boundingRect()
        path = QPainterPath()
        path.addRoundedRect(rect, 3, 3)  # Sharp corners (minimal rounding)

        # Fill
        if self.isSelected():
            painter.setBrush(QBrush(QColor(SELECTED_COLOR).lighter(150)))
            painter.setPen(QPen(QColor(SELECTED_COLOR), 2))
        else:
            painter.setBrush(QBrush(QColor(EntityItem.fill_color)))
            painter.setPen(QPen(QColor(EntityItem.border_color), 2))

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
            painter.setPen(QPen(QColor(EntityItem.border_color), 1))
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
    """Graphical representation of an MCD association (rounded rectangle/pill shape)."""

    # Class-level setting for showing attributes
    show_attributes = True
    HEADER_HEIGHT = 30
    ATTR_HEIGHT = 18
    MIN_WIDTH = 80
    MIN_HEIGHT = 40

    # Class-level colors (can be updated from project settings)
    fill_color = ASSOCIATION_COLOR
    border_color = ASSOCIATION_BORDER

    def __init__(self, association: Association, parent=None):
        super().__init__(parent)
        self.association = association
        self.setPos(association.x, association.y)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCursor(Qt.OpenHandCursor)
        self._links: list["LinkItem"] = []
        self._update_size()

    def _update_size(self):
        """Update size based on content."""
        self.prepareGeometryChange()
        # Measure association name with italic font (as drawn)
        italic_font = QFont()
        italic_font.setItalic(True)
        fm_italic = QFontMetrics(italic_font)
        name_width = fm_italic.horizontalAdvance(self.association.name) + 30
        self._width = max(self.MIN_WIDTH, name_width)

        if AssociationItem.show_attributes and self.association.attributes:
            # Calculate width for attributes too
            fm = QFontMetrics(QFont())
            for attr in self.association.attributes:
                attr_text = f"{attr.name} : {attr.data_type}"
                if attr.size:
                    attr_text += f"({attr.size})"
                attr_width = fm.horizontalAdvance(attr_text) + 20
                self._width = max(self._width, attr_width)
            self._height = self.HEADER_HEIGHT + len(self.association.attributes) * self.ATTR_HEIGHT + 5
        else:
            self._height = self.MIN_HEIGHT

    def boundingRect(self) -> QRectF:
        return QRectF(-self._width / 2, -self._height / 2, self._width, self._height)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        rect = self.boundingRect()
        path = QPainterPath()

        # Fully rounded corners (pill shape) - radius is half the height
        radius = self._height / 2 if not (AssociationItem.show_attributes and self.association.attributes) else 15
        path.addRoundedRect(rect, radius, radius)

        # Fill
        if self.isSelected():
            painter.setBrush(QBrush(QColor(SELECTED_COLOR).lighter(150)))
            painter.setPen(QPen(QColor(SELECTED_COLOR), 2))
        else:
            painter.setBrush(QBrush(QColor(AssociationItem.fill_color)))
            painter.setPen(QPen(QColor(AssociationItem.border_color), 2))

        painter.drawPath(path)

        # Draw association name
        painter.setPen(Qt.black)
        font = QFont()
        font.setItalic(True)
        painter.setFont(font)

        if AssociationItem.show_attributes and self.association.attributes:
            # Draw header with name
            header_rect = QRectF(rect.left(), rect.top(), rect.width(), self.HEADER_HEIGHT)
            painter.drawText(header_rect, Qt.AlignCenter, self.association.name)

            # Draw separator line
            sep_y = rect.top() + self.HEADER_HEIGHT - 3
            painter.setPen(QPen(QColor(AssociationItem.border_color), 1))
            painter.drawLine(int(rect.left() + 10), int(sep_y), int(rect.right() - 10), int(sep_y))

            # Draw carrying attributes
            font.setItalic(False)
            font.setPointSize(font.pointSize() - 1)
            painter.setFont(font)
            painter.setPen(Qt.black)

            y = rect.top() + self.HEADER_HEIGHT
            for attr in self.association.attributes:
                attr_text = f"{attr.name} : {attr.data_type}"
                if attr.size:
                    attr_text += f"({attr.size})"
                text_rect = QRectF(rect.left() + 8, y, rect.width() - 16, self.ATTR_HEIGHT)
                painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, attr_text)
                y += self.ATTR_HEIGHT
        else:
            # Simple mode - just name centered
            painter.drawText(rect, Qt.AlignCenter, self.association.name)

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
        """Get the point on the rounded rectangle edge closest to the target."""
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
        """Refresh the item after association changes."""
        self._update_size()
        self.update()
        # Update connected links
        for link_item in self._links:
            link_item.update_position()


class LinkItem(QGraphicsPathItem):
    """Graphical representation of a link between entity and association."""

    # Class-level setting for link style
    link_style = "curved"  # "curved", "orthogonal", "straight"

    # Class-level color (can be updated from project settings)
    line_color = LINK_COLOR

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
        self.setPen(QPen(QColor(LinkItem.line_color), 1))
        self.setBrush(Qt.NoBrush)

        # Create background for cardinality label (white box)
        self._card_bg = QGraphicsRectItem(self)
        self._card_bg.setBrush(QBrush(QColor("white")))
        self._card_bg.setPen(QPen(QColor(LinkItem.line_color), 1))

        # Create cardinality label
        self._card_label = QGraphicsTextItem(self)
        font = QFont()
        font.setBold(True)
        font.setPointSize(9)
        self._card_label.setFont(font)
        self._card_label.setDefaultTextColor(QColor("black"))

        # Store points for curve calculation
        self._p1 = QPointF()
        self._p2 = QPointF()
        self._control = QPointF()

        # Register with connected items
        entity_item.add_link(self)
        association_item.add_link(self)

        self.update_position()

    def update_position(self):
        """Update link position based on connected items and current style."""
        # Get centers first to calculate direction
        entity_center = self.entity_item.get_center()
        assoc_center = self.association_item.get_center()

        # Get edge points (where line meets the shape borders)
        self._p1 = self.entity_item.get_edge_point(assoc_center)
        self._p2 = self.association_item.get_edge_point(entity_center)

        # Calculate midpoint
        mid_x = (self._p1.x() + self._p2.x()) / 2
        mid_y = (self._p1.y() + self._p2.y()) / 2

        # Create path based on style
        path = QPainterPath()
        path.moveTo(self._p1)

        if LinkItem.link_style == "straight":
            # Simple straight line
            path.lineTo(self._p2)
            self._control = QPointF(mid_x, mid_y)

        elif LinkItem.link_style == "orthogonal":
            # Orthogonal (right-angle) path
            # Determine if horizontal or vertical first based on angle
            dx = self._p2.x() - self._p1.x()
            dy = self._p2.y() - self._p1.y()

            if abs(dx) > abs(dy):
                # Go horizontal first, then vertical
                mid_point = QPointF(mid_x, self._p1.y())
                path.lineTo(mid_point)
                path.lineTo(QPointF(mid_x, self._p2.y()))
                path.lineTo(self._p2)
            else:
                # Go vertical first, then horizontal
                mid_point = QPointF(self._p1.x(), mid_y)
                path.lineTo(mid_point)
                path.lineTo(QPointF(self._p2.x(), mid_y))
                path.lineTo(self._p2)
            self._control = QPointF(mid_x, mid_y)

        else:  # "curved" (default)
            # Quadratic Bezier curve
            dx = self._p2.x() - self._p1.x()
            dy = self._p2.y() - self._p1.y()
            length = math.sqrt(dx * dx + dy * dy)

            if length > 0:
                # Perpendicular vector (normalized)
                perp_x = -dy / length
                perp_y = dx / length
                # Curve amount (proportional to distance, but capped)
                curve_amount = min(length * 0.15, 30)
                self._control = QPointF(mid_x + perp_x * curve_amount, mid_y + perp_y * curve_amount)
            else:
                self._control = QPointF(mid_x, mid_y)

            path.quadTo(self._control, self._p2)

        self.setPath(path)

        # Position cardinality label near entity edge
        # For curved: use point on Bezier at t=0.2
        # For others: use point 20% along the path
        t = 0.2
        if LinkItem.link_style == "curved":
            label_x = (1-t)*(1-t)*self._p1.x() + 2*(1-t)*t*self._control.x() + t*t*self._p2.x()
            label_y = (1-t)*(1-t)*self._p1.y() + 2*(1-t)*t*self._control.y() + t*t*self._p2.y()
        else:
            label_x = self._p1.x() + t * (self._p2.x() - self._p1.x())
            label_y = self._p1.y() + t * (self._p2.y() - self._p1.y())

        card_text = f"{self.link.cardinality_min},{self.link.cardinality_max}"
        self._card_label.setPlainText(card_text)

        # Get text bounding rect for background sizing
        text_rect = self._card_label.boundingRect()
        padding = 3

        # Position the background rectangle
        bg_width = text_rect.width() + padding * 2
        bg_height = text_rect.height()
        self._card_bg.setRect(
            label_x - bg_width / 2,
            label_y - bg_height / 2,
            bg_width,
            bg_height
        )

        # Position the text centered on the background
        self._card_label.setPos(
            label_x - text_rect.width() / 2,
            label_y - text_rect.height() / 2
        )

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        if self.isSelected():
            self.setPen(QPen(QColor(SELECTED_COLOR), 2))
        else:
            self.setPen(QPen(QColor(LinkItem.line_color), 1))
        # Update cardinality box border color
        self._card_bg.setPen(QPen(QColor(LinkItem.line_color), 1))
        super().paint(painter, option, widget)

    def cleanup(self):
        """Remove this link from connected items."""
        self.entity_item.remove_link(self)
        self.association_item.remove_link(self)
