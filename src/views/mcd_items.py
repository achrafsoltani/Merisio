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


def _curve_control(a: QPointF, b: QPointF, reference: QPointF = None) -> QPointF:
    """Quadratic Bezier control point with a capped perpendicular offset.

    If `reference` is provided, the perpendicular is flipped so the control
    point lies on the side opposite the reference — curves bow AWAY from it.
    Pass the diagram's centroid as reference to get an "outward bloom" effect
    where every link bends away from the visual centre of the diagram, never
    inward toward other items.

    Without a reference, falls back to a consistent +Y / +X perpendicular so
    mirrored links at least bend the same direction."""
    dx = b.x() - a.x()
    dy = b.y() - a.y()
    length = math.sqrt(dx * dx + dy * dy)
    mid = QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)
    if length == 0:
        return mid
    perp_x = -dy / length
    perp_y = dx / length
    if reference is not None:
        to_ref_x = reference.x() - mid.x()
        to_ref_y = reference.y() - mid.y()
        if perp_x * to_ref_x + perp_y * to_ref_y > 0:
            perp_x = -perp_x
            perp_y = -perp_y
    elif perp_y < 0 or (perp_y == 0 and perp_x < 0):
        perp_x = -perp_x
        perp_y = -perp_y
    curve_amount = min(length * 0.15, 30)
    return QPointF(mid.x() + perp_x * curve_amount, mid.y() + perp_y * curve_amount)


def _project_point_to_segment(p: QPointF, a: QPointF, b: QPointF):
    """Foot of perpendicular from p onto segment [a, b]. Returns (foot, distance) or None
    if the projection falls outside the segment endpoints — snapping/collapsing a waypoint
    onto a remote extension of the line would change the path shape rather than tidy it."""
    dx = b.x() - a.x()
    dy = b.y() - a.y()
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return None
    t = ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / length_sq
    if t < 0 or t > 1:
        return None
    foot = QPointF(a.x() + t * dx, a.y() + t * dy)
    distance = math.hypot(p.x() - foot.x(), p.y() - foot.y())
    return foot, distance


class WaypointHandle(QGraphicsRectItem):
    """Solid square handle marking an existing waypoint on a link. Drag to move."""

    SIZE = 8

    def __init__(self, link_item: "LinkItem", waypoint_index: int):
        super().__init__(-self.SIZE / 2, -self.SIZE / 2, self.SIZE, self.SIZE, link_item)
        self.link_item = link_item
        self.waypoint_index = waypoint_index
        self.setBrush(QBrush(QColor(SELECTED_COLOR)))
        self.setPen(QPen(QColor("white"), 1))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        # Constant pixel size regardless of zoom level
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setZValue(10)
        self.setCursor(Qt.SizeAllCursor)

    def itemChange(self, change, value):
        if not self.link_item._suspend_handle_updates:
            if change == QGraphicsItem.ItemPositionChange:
                snapped = self.link_item._snap_waypoint_position(self.waypoint_index, value)
                if snapped is not None:
                    return snapped
            elif change == QGraphicsItem.ItemPositionHasChanged:
                wps = self.link_item.link.waypoints
                if 0 <= self.waypoint_index < len(wps):
                    wps[self.waypoint_index] = [value.x(), value.y()]
                    self.link_item.update_position()
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.link_item._notify_modified()

    def remove(self):
        self.link_item._remove_waypoint(self.waypoint_index)


class SegmentHandle(QGraphicsRectItem):
    """Outlined square at a segment midpoint. Dragging inserts a new waypoint."""

    SIZE = 6

    def __init__(self, link_item: "LinkItem", segment_index: int):
        super().__init__(-self.SIZE / 2, -self.SIZE / 2, self.SIZE, self.SIZE, link_item)
        self.link_item = link_item
        # Index in link.waypoints where a new waypoint will be inserted on drag.
        self.segment_index = segment_index
        self.setBrush(QBrush(QColor("white")))
        self.setPen(QPen(QColor(SELECTED_COLOR), 1))
        self.setOpacity(0.7)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setZValue(9)
        self.setCursor(Qt.SizeAllCursor)
        self._inserted = False
        # Original segment endpoints, captured at construction so snap remains
        # anchored to the pre-insertion segment line throughout the drag.
        waypoints_qpf = [QPointF(wp[0], wp[1]) for wp in link_item.link.waypoints]
        full = [link_item._p1, *waypoints_qpf, link_item._p2]
        self._segment_start = QPointF(full[segment_index])
        self._segment_end = QPointF(full[segment_index + 1])

    def itemChange(self, change, value):
        if not self.link_item._suspend_handle_updates:
            if change == QGraphicsItem.ItemPositionChange:
                snapped = self.link_item._snap_to_line(value, self._segment_start, self._segment_end)
                if snapped is not None:
                    return snapped
            elif change == QGraphicsItem.ItemPositionHasChanged:
                wps = self.link_item.link.waypoints
                if not self._inserted:
                    wps.insert(self.segment_index, [value.x(), value.y()])
                    self._inserted = True
                else:
                    wps[self.segment_index] = [value.x(), value.y()]
                self.link_item.update_position()
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._inserted:
            self.link_item._rebuild_handles()
            self.link_item._notify_modified()


class LinkItem(QGraphicsPathItem):
    """Graphical representation of a link between entity and association."""

    # Class-level setting for link style
    link_style = "curved"  # "curved", "orthogonal", "straight"

    # Class-level color (can be updated from project settings)
    line_color = LINK_COLOR

    # Tight zone (scene units) for the magnetic drag-snap. Predictable during edit.
    SNAP_THRESHOLD = 20.0
    # Wider zone for the explicit "Tidy Up" action. Snap prevents new ugliness;
    # tidy cleans up legacy waypoints the user wants gone, so it's more forgiving.
    TIDY_THRESHOLD = 40.0

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

        # Draggable handles, created lazily on selection.
        self._handles: list = []
        # Flag set while we reposition handles programmatically, so the
        # handles' itemChange doesn't loop back into update_position.
        self._suspend_handle_updates = False

        # Register with connected items
        entity_item.add_link(self)
        association_item.add_link(self)

        self.update_position()

    def update_position(self):
        """Update link path from connected items, stored waypoints, and current style."""
        waypoints_qpf = [QPointF(wp[0], wp[1]) for wp in self.link.waypoints]
        entity_center = self.entity_item.get_center()
        assoc_center = self.association_item.get_center()

        # Anchor each endpoint toward its closest neighbour (first/last waypoint
        # if any, else the opposite shape's centre — the auto-routing default).
        p1_target = waypoints_qpf[0] if waypoints_qpf else assoc_center
        p2_target = waypoints_qpf[-1] if waypoints_qpf else entity_center
        self._p1 = self.entity_item.get_edge_point(p1_target)
        self._p2 = self.association_item.get_edge_point(p2_target)

        points = [self._p1, *waypoints_qpf, self._p2]

        path = QPainterPath()
        path.moveTo(points[0])

        if LinkItem.link_style == "straight":
            for pt in points[1:]:
                path.lineTo(pt)

        elif LinkItem.link_style == "orthogonal":
            # No waypoints: a single Z (two corners in the middle of the segment) looks
            # balanced. With waypoints: an L per segment (one corner each) produces a
            # cleaner staircase — a Z per segment piles on too many right angles.
            single_segment = len(points) == 2
            for i in range(len(points) - 1):
                a, b = points[i], points[i + 1]
                dx = b.x() - a.x()
                dy = b.y() - a.y()
                if single_segment:
                    mid_x = (a.x() + b.x()) / 2
                    mid_y = (a.y() + b.y()) / 2
                    if abs(dx) > abs(dy):
                        path.lineTo(QPointF(mid_x, a.y()))
                        path.lineTo(QPointF(mid_x, b.y()))
                    else:
                        path.lineTo(QPointF(a.x(), mid_y))
                        path.lineTo(QPointF(b.x(), mid_y))
                else:
                    if abs(dx) > abs(dy):
                        path.lineTo(QPointF(b.x(), a.y()))
                    else:
                        path.lineTo(QPointF(a.x(), b.y()))
                path.lineTo(b)

        else:  # "curved"
            if len(points) == 2:
                # Single segment: perpendicular-offset quadratic Bezier so even
                # straight links look curved. Direction biased by centroid.
                a, b = points[0], points[1]
                path.quadTo(_curve_control(a, b, self._compute_centroid()), b)
            else:
                # Multi-segment: Catmull-Rom → cubic Bezier per segment. Tangent
                # at each interior point is half the chord through its neighbours,
                # so consecutive segments meet smoothly with no kink. Endpoints
                # clamp to the segment direction (p0=a, p3=b at the boundaries).
                for i in range(len(points) - 1):
                    a, b = points[i], points[i + 1]
                    p0 = points[i - 1] if i > 0 else a
                    p3 = points[i + 2] if i + 2 < len(points) else b
                    c1 = QPointF(
                        a.x() + (b.x() - p0.x()) / 6,
                        a.y() + (b.y() - p0.y()) / 6,
                    )
                    c2 = QPointF(
                        b.x() - (p3.x() - a.x()) / 6,
                        b.y() - (p3.y() - a.y()) / 6,
                    )
                    path.cubicTo(c1, c2, b)

        self.setPath(path)

        # Cardinality label sits 20% along the first segment, near the entity.
        seg_a, seg_b = points[0], points[1]
        if LinkItem.link_style == "curved":
            self._control = _curve_control(seg_a, seg_b, self._compute_centroid())
        else:
            self._control = QPointF(
                (self._p1.x() + self._p2.x()) / 2,
                (self._p1.y() + self._p2.y()) / 2,
            )

        t = 0.2
        if LinkItem.link_style == "curved":
            label_x = (1-t)*(1-t)*seg_a.x() + 2*(1-t)*t*self._control.x() + t*t*seg_b.x()
            label_y = (1-t)*(1-t)*seg_a.y() + 2*(1-t)*t*self._control.y() + t*t*seg_b.y()
        else:
            label_x = seg_a.x() + t * (seg_b.x() - seg_a.x())
            label_y = seg_a.y() + t * (seg_b.y() - seg_a.y())

        card_text = f"{self.link.cardinality_min},{self.link.cardinality_max}"
        self._card_label.setPlainText(card_text)

        text_rect = self._card_label.boundingRect()
        padding = 3
        bg_width = text_rect.width() + padding * 2
        bg_height = text_rect.height()
        self._card_bg.setRect(
            label_x - bg_width / 2,
            label_y - bg_height / 2,
            bg_width,
            bg_height
        )
        self._card_label.setPos(
            label_x - text_rect.width() / 2,
            label_y - text_rect.height() / 2
        )

        self._refresh_handles()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if self.isSelected():
                self._rebuild_handles()
            else:
                self._clear_handles()
        return super().itemChange(change, value)

    def _refresh_handles(self):
        """Rebuild handles if the link is selected and no handle is mid-drag."""
        if not self.isSelected():
            return
        scene = self.scene()
        if scene is not None:
            grabber = scene.mouseGrabberItem()
            if isinstance(grabber, (WaypointHandle, SegmentHandle)) and grabber.parentItem() is self:
                return
        self._rebuild_handles()

    def _rebuild_handles(self):
        self._suspend_handle_updates = True
        try:
            self._clear_handles()
            waypoints_qpf = [QPointF(wp[0], wp[1]) for wp in self.link.waypoints]
            points = [self._p1, *waypoints_qpf, self._p2]

            for i, wp in enumerate(waypoints_qpf):
                handle = WaypointHandle(self, i)
                handle.setPos(wp)
                self._handles.append(handle)

            for i in range(len(points) - 1):
                a, b = points[i], points[i + 1]
                handle = SegmentHandle(self, i)
                handle.setPos(QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2))
                self._handles.append(handle)
        finally:
            self._suspend_handle_updates = False

    def _clear_handles(self):
        scene = self.scene()
        for handle in self._handles:
            if scene is not None and handle.scene() is scene:
                scene.removeItem(handle)
        self._handles = []

    def _remove_waypoint(self, index: int):
        if 0 <= index < len(self.link.waypoints):
            del self.link.waypoints[index]
            self.update_position()
            self._notify_modified()

    def clear_waypoints(self):
        """Drop all waypoints, returning the link to auto-routing."""
        if not self.link.waypoints:
            return
        self.link.waypoints.clear()
        self.update_position()
        self._notify_modified()

    def tidy_up_waypoints(self):
        """Remove waypoints near-collinear with their neighbours. Iterates until stable
        so that removing one redundant waypoint can expose another (e.g. a chain of
        nearly-straight bends collapses in two passes rather than leaving one behind)."""
        if not self.link.waypoints:
            return
        changed = False
        while self._collinear_pass():
            changed = True
        if changed:
            self.update_position()
            self._notify_modified()

    def _collinear_pass(self) -> bool:
        """Single pass: drop every waypoint whose perpendicular distance to the line
        through its neighbours is below TIDY_THRESHOLD. Returns True if any
        were dropped."""
        waypoints = self.link.waypoints
        waypoints_qpf = [QPointF(wp[0], wp[1]) for wp in waypoints]
        full = [self._p1, *waypoints_qpf, self._p2]
        redundant = []
        for i, wp in enumerate(waypoints_qpf):
            prev = full[i]
            nxt = full[i + 2]
            result = _project_point_to_segment(wp, prev, nxt)
            if result is None:
                continue
            _, distance = result
            if distance < self.TIDY_THRESHOLD:
                redundant.append(i)
        for i in reversed(redundant):
            del waypoints[i]
        return bool(redundant)

    def _compute_centroid(self):
        """Average position of every entity and association in the scene.
        Used to bend curved links AWAY from the diagram's visual centre."""
        scene = self.scene()
        if scene is None:
            return None
        total_x = 0.0
        total_y = 0.0
        count = 0
        for item in scene.items():
            if isinstance(item, (EntityItem, AssociationItem)):
                center = item.get_center()
                total_x += center.x()
                total_y += center.y()
                count += 1
        if count == 0:
            return None
        return QPointF(total_x / count, total_y / count)

    def _snap_to_line(self, proposed: QPointF, a: QPointF, b: QPointF):
        """Return the foot of perpendicular from proposed onto segment [a, b] if it
        lies within the segment AND the distance is under SNAP_THRESHOLD; else None."""
        result = _project_point_to_segment(proposed, a, b)
        if result is None:
            return None
        foot, distance = result
        if distance < self.SNAP_THRESHOLD:
            return foot
        return None

    def _snap_waypoint_position(self, index: int, proposed: QPointF):
        """Snap a waypoint's proposed position onto the line through its neighbours."""
        if not (0 <= index < len(self.link.waypoints)):
            return None
        waypoints_qpf = [QPointF(wp[0], wp[1]) for wp in self.link.waypoints]
        full = [self._p1, *waypoints_qpf, self._p2]
        return self._snap_to_line(proposed, full[index], full[index + 2])

    def _notify_modified(self):
        scene = self.scene()
        if scene is None:
            return
        for view in scene.views():
            sig = getattr(view, "modified", None)
            if sig is not None:
                sig.emit()
                return

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
