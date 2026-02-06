from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import QRectF, QMarginsF
from PySide6.QtGui import QPainter, QImage, QColor, QPageSize
from PySide6.QtCore import QSizeF
from PySide6.QtSvg import QSvgGenerator

from ..models.project import Project
from ..views.mcd_items import EntityItem, AssociationItem, LinkItem


class HeadlessRenderer:
    """Renders a Merisio project diagram to PNG, SVG, or PDF without a display."""

    def __init__(self, project: Project):
        self._project = project
        self._apply_colors()

    def _apply_colors(self):
        """Apply project colours to item class-level settings."""
        colors = self._project.colors
        EntityItem.fill_color = colors.get("entity_fill", "#E3F2FD")
        EntityItem.border_color = colors.get("entity_border", "#1976D2")
        AssociationItem.fill_color = colors.get("association_fill", "#FFF3E0")
        AssociationItem.border_color = colors.get("association_border", "#F57C00")
        LinkItem.line_color = colors.get("link_color", "#000000")

    def _build_scene(self) -> QGraphicsScene:
        """Build a QGraphicsScene populated with all project items."""
        scene = QGraphicsScene()

        entity_items = {}
        association_items = {}

        for entity in self._project.get_all_entities():
            item = EntityItem(entity)
            scene.addItem(item)
            entity_items[entity.id] = item

        for assoc in self._project.get_all_associations():
            item = AssociationItem(assoc)
            scene.addItem(item)
            association_items[assoc.id] = item

        for link in self._project.get_all_links():
            entity_item = entity_items.get(link.entity_id)
            assoc_item = association_items.get(link.association_id)
            if entity_item and assoc_item:
                item = LinkItem(link, entity_item, assoc_item)
                scene.addItem(item)

        return scene

    def export_png(self, file_path: str, scale: float = 2.0) -> bool:
        """Export the diagram to PNG."""
        try:
            scene = self._build_scene()
            items_rect = scene.itemsBoundingRect()
            if items_rect.isEmpty():
                return False

            margin = 20
            items_rect.adjust(-margin, -margin, margin, margin)

            width = int(items_rect.width() * scale)
            height = int(items_rect.height() * scale)
            image = QImage(width, height, QImage.Format_ARGB32)
            image.fill(QColor(255, 255, 255))

            painter = QPainter()
            painter.begin(image)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            scene.render(painter, QRectF(0, 0, width, height), items_rect)
            painter.end()

            return image.save(file_path, "PNG")
        except Exception:
            return False

    def export_svg(self, file_path: str) -> bool:
        """Export the diagram to SVG."""
        try:
            scene = self._build_scene()
            items_rect = scene.itemsBoundingRect()
            if items_rect.isEmpty():
                return False

            margin = 20
            items_rect.adjust(-margin, -margin, margin, margin)

            generator = QSvgGenerator()
            generator.setFileName(file_path)
            generator.setSize(items_rect.size().toSize())
            generator.setViewBox(QRectF(0, 0, items_rect.width(), items_rect.height()))
            generator.setTitle("Merisio MCD Diagram")

            painter = QPainter()
            painter.begin(generator)
            painter.setRenderHint(QPainter.Antialiasing)
            scene.render(painter, QRectF(0, 0, items_rect.width(), items_rect.height()), items_rect)
            painter.end()
            return True
        except Exception:
            return False

    def export_pdf(self, file_path: str) -> bool:
        """Export the diagram to PDF."""
        try:
            from PySide6.QtGui import QPdfWriter

            scene = self._build_scene()
            items_rect = scene.itemsBoundingRect()
            if items_rect.isEmpty():
                return False

            margin = 20
            items_rect.adjust(-margin, -margin, margin, margin)

            writer = QPdfWriter(file_path)
            writer.setTitle("Merisio MCD Diagram")
            writer.setCreator("Merisio")

            page_size = QPageSize(QSizeF(items_rect.width(), items_rect.height()), QPageSize.Point)
            writer.setPageSize(page_size)
            writer.setPageMargins(QMarginsF(0, 0, 0, 0))

            painter = QPainter()
            painter.begin(writer)
            painter.setRenderHint(QPainter.Antialiasing)

            pdf_scale = min(writer.width() / items_rect.width(), writer.height() / items_rect.height())
            painter.scale(pdf_scale, pdf_scale)

            scene.render(painter, QRectF(0, 0, items_rect.width(), items_rect.height()), items_rect)
            painter.end()
            return True
        except Exception:
            return False
