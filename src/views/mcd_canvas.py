from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QPointF, QMarginsF, QRectF
from PySide6.QtGui import QPainter, QAction, QImage, QColor
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtGui import QPageSize, QPageLayout
from PySide6.QtCore import QSizeF

from ..models.project import Project
from ..models.entity import Entity
from ..models.association import Association
from ..models.link import Link
from .mcd_items import EntityItem, AssociationItem, LinkItem


class MCDCanvas(QGraphicsView):
    """Canvas for editing MCD diagrams."""

    # Signals
    modified = Signal()  # Emitted when the diagram is modified
    zoom_changed = Signal(int)  # Emitted when zoom level changes (percentage)

    # Zoom constants
    ZOOM_MIN = 0.25  # 25%
    ZOOM_MAX = 4.0   # 400%
    ZOOM_STEP = 1.2  # 20% per step

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Item tracking
        self._entity_items: dict[str, EntityItem] = {}
        self._association_items: dict[str, AssociationItem] = {}
        self._link_items: dict[str, LinkItem] = {}

        # Display options
        self._show_attributes = True
        self._link_style = "curved"  # "curved", "orthogonal", "straight"

        # Zoom tracking
        self._zoom_level = 1.0

        # Track item positions for move detection
        self._drag_start_positions: dict[str, QPointF] = {}

        self._setup_view()
        self._context_pos = QPointF(0, 0)

    def _setup_view(self):
        """Configure the view settings."""
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # Set scene rect
        self._scene.setSceneRect(-2000, -2000, 4000, 4000)

    def set_project(self, project: Project):
        """Set a new project and refresh the canvas."""
        self._project = project
        self.refresh()

    def refresh(self):
        """Refresh the canvas from the project data."""
        self._scene.clear()
        self._entity_items.clear()
        self._association_items.clear()
        self._link_items.clear()

        # Create entity items
        for entity in self._project.get_all_entities():
            item = EntityItem(entity)
            self._scene.addItem(item)
            self._entity_items[entity.id] = item

        # Create association items
        for assoc in self._project.get_all_associations():
            item = AssociationItem(assoc)
            self._scene.addItem(item)
            self._association_items[assoc.id] = item

        # Create link items
        for link in self._project.get_all_links():
            entity_item = self._entity_items.get(link.entity_id)
            assoc_item = self._association_items.get(link.association_id)
            if entity_item and assoc_item:
                item = LinkItem(link, entity_item, assoc_item)
                self._scene.addItem(item)
                self._link_items[link.id] = item

    def _show_context_menu(self, pos):
        """Show context menu at the given position."""
        self._context_pos = self.mapToScene(pos)
        item = self.itemAt(pos)

        menu = QMenu(self)

        if item is None:
            # Context menu for empty space
            add_entity = menu.addAction("Add Entity")
            add_entity.triggered.connect(self._add_entity)

            add_assoc = menu.addAction("Add Association")
            add_assoc.triggered.connect(self._add_association)

        elif isinstance(item, EntityItem):
            edit_action = menu.addAction("Edit Entity")
            edit_action.triggered.connect(lambda: self._edit_entity(item))

            delete_action = menu.addAction("Delete Entity")
            delete_action.triggered.connect(lambda: self._delete_entity(item))

            menu.addSeparator()

            add_link = menu.addAction("Add Link to Association...")
            add_link.triggered.connect(lambda: self._add_link_from_entity(item))

        elif isinstance(item, AssociationItem):
            edit_action = menu.addAction("Edit Association")
            edit_action.triggered.connect(lambda: self._edit_association(item))

            delete_action = menu.addAction("Delete Association")
            delete_action.triggered.connect(lambda: self._delete_association(item))

            menu.addSeparator()

            add_link = menu.addAction("Add Link to Entity...")
            add_link.triggered.connect(lambda: self._add_link_from_association(item))

        elif isinstance(item, LinkItem):
            edit_action = menu.addAction("Edit Link")
            edit_action.triggered.connect(lambda: self._edit_link(item))

            delete_action = menu.addAction("Delete Link")
            delete_action.triggered.connect(lambda: self._delete_link(item))

        # Handle clicking on child items (like cardinality labels)
        elif item.parentItem():
            parent = item.parentItem()
            if isinstance(parent, LinkItem):
                edit_action = menu.addAction("Edit Link")
                edit_action.triggered.connect(lambda: self._edit_link(parent))

                delete_action = menu.addAction("Delete Link")
                delete_action.triggered.connect(lambda: self._delete_link(parent))

        menu.exec(self.mapToGlobal(pos))

    def _add_entity(self):
        """Add a new entity at the context menu position."""
        from .dialogs.entity_dialog import EntityDialog

        dialog = EntityDialog(parent=self)
        if dialog.exec():
            entity = dialog.get_entity()
            if entity:
                entity.x = self._context_pos.x()
                entity.y = self._context_pos.y()
                self._project.add_entity(entity)

                item = EntityItem(entity)
                self._scene.addItem(item)
                self._entity_items[entity.id] = item
                self.modified.emit()

    def _add_association(self):
        """Add a new association at the context menu position."""
        from .dialogs.association_dialog import AssociationDialog

        dialog = AssociationDialog(parent=self)
        if dialog.exec():
            assoc = dialog.get_association()
            if assoc:
                assoc.x = self._context_pos.x()
                assoc.y = self._context_pos.y()
                self._project.add_association(assoc)

                item = AssociationItem(assoc)
                self._scene.addItem(item)
                self._association_items[assoc.id] = item
                self.modified.emit()

    def _edit_entity(self, item: EntityItem):
        """Edit an existing entity."""
        from .dialogs.entity_dialog import EntityDialog

        dialog = EntityDialog(entity=item.entity, parent=self)
        if dialog.exec():
            dialog.get_entity()  # Updates the entity in place
            item.refresh()
            self.modified.emit()

    def _delete_entity(self, item: EntityItem):
        """Delete an entity."""
        result = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete entity '{item.entity.name}'?\nThis will also remove all connected links.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if result == QMessageBox.Yes:
            # Remove links first
            links_to_remove = self._project.get_links_for_entity(item.entity.id)
            for link in links_to_remove:
                link_item = self._link_items.get(link.id)
                if link_item:
                    link_item.cleanup()
                    self._scene.removeItem(link_item)
                    del self._link_items[link.id]

            # Remove entity
            self._project.remove_entity(item.entity.id)
            self._scene.removeItem(item)
            del self._entity_items[item.entity.id]
            self.modified.emit()

    def _edit_association(self, item: AssociationItem):
        """Edit an existing association."""
        from .dialogs.association_dialog import AssociationDialog

        dialog = AssociationDialog(association=item.association, parent=self)
        if dialog.exec():
            dialog.get_association()  # Updates the association in place
            item.refresh()
            self.modified.emit()

    def _delete_association(self, item: AssociationItem):
        """Delete an association."""
        result = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete association '{item.association.name}'?\nThis will also remove all connected links.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if result == QMessageBox.Yes:
            # Remove links first
            links_to_remove = self._project.get_links_for_association(item.association.id)
            for link in links_to_remove:
                link_item = self._link_items.get(link.id)
                if link_item:
                    link_item.cleanup()
                    self._scene.removeItem(link_item)
                    del self._link_items[link.id]

            # Remove association
            self._project.remove_association(item.association.id)
            self._scene.removeItem(item)
            del self._association_items[item.association.id]
            self.modified.emit()

    def _add_link_from_entity(self, entity_item: EntityItem):
        """Add a link from an entity to an association."""
        from .dialogs.link_dialog import LinkDialog

        associations = self._project.get_all_associations()
        if not associations:
            QMessageBox.warning(
                self, "No Associations",
                "Please add at least one association first."
            )
            return

        # Pre-select the entity
        entities = self._project.get_all_entities()
        dialog = LinkDialog(entities, associations, parent=self)

        # Set the entity in the dialog
        index = dialog._entity_combo.findData(entity_item.entity.id)
        if index >= 0:
            dialog._entity_combo.setCurrentIndex(index)

        if dialog.exec():
            link = dialog.get_link()
            if link:
                self._create_link_item(link)

    def _add_link_from_association(self, assoc_item: AssociationItem):
        """Add a link from an association to an entity."""
        from .dialogs.link_dialog import LinkDialog

        entities = self._project.get_all_entities()
        if not entities:
            QMessageBox.warning(
                self, "No Entities",
                "Please add at least one entity first."
            )
            return

        associations = self._project.get_all_associations()
        dialog = LinkDialog(entities, associations, parent=self)

        # Set the association in the dialog
        index = dialog._assoc_combo.findData(assoc_item.association.id)
        if index >= 0:
            dialog._assoc_combo.setCurrentIndex(index)

        if dialog.exec():
            link = dialog.get_link()
            if link:
                self._create_link_item(link)

    def _create_link_item(self, link: Link):
        """Create a link item and add it to the scene."""
        entity_item = self._entity_items.get(link.entity_id)
        assoc_item = self._association_items.get(link.association_id)

        if entity_item and assoc_item:
            self._project.add_link(link)
            item = LinkItem(link, entity_item, assoc_item)
            self._scene.addItem(item)
            self._link_items[link.id] = item
            self.modified.emit()

    def _edit_link(self, item: LinkItem):
        """Edit an existing link."""
        from .dialogs.link_dialog import LinkDialog

        entities = self._project.get_all_entities()
        associations = self._project.get_all_associations()

        dialog = LinkDialog(entities, associations, link=item.link, parent=self)
        if dialog.exec():
            dialog.get_link()  # Updates the link in place
            item.update_position()
            self.modified.emit()

    def _delete_link(self, item: LinkItem):
        """Delete a link."""
        result = QMessageBox.question(
            self, "Confirm Delete",
            "Delete this link?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if result == QMessageBox.Yes:
            item.cleanup()
            self._project.remove_link(item.link.id)
            self._scene.removeItem(item)
            del self._link_items[item.link.id]
            self.modified.emit()

    # Public API for toolbar actions
    def add_entity_at_center(self):
        """Add entity at center of view."""
        self._context_pos = self.mapToScene(self.viewport().rect().center())
        self._add_entity()

    def add_association_at_center(self):
        """Add association at center of view."""
        self._context_pos = self.mapToScene(self.viewport().rect().center())
        self._add_association()

    def add_link(self):
        """Open dialog to add a link."""
        from .dialogs.link_dialog import LinkDialog

        entities = self._project.get_all_entities()
        associations = self._project.get_all_associations()

        if not entities:
            QMessageBox.warning(self, "No Entities", "Please add at least one entity first.")
            return
        if not associations:
            QMessageBox.warning(self, "No Associations", "Please add at least one association first.")
            return

        dialog = LinkDialog(entities, associations, parent=self)
        if dialog.exec():
            link = dialog.get_link()
            if link:
                self._create_link_item(link)

    def delete_selected(self):
        """Delete all selected items."""
        selected = self._scene.selectedItems()
        if not selected:
            return

        result = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(selected)} selected item(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if result != QMessageBox.Yes:
            return

        for item in selected:
            if isinstance(item, EntityItem):
                # Remove connected links first
                links_to_remove = self._project.get_links_for_entity(item.entity.id)
                for link in links_to_remove:
                    link_item = self._link_items.get(link.id)
                    if link_item:
                        link_item.cleanup()
                        self._scene.removeItem(link_item)
                        del self._link_items[link.id]
                self._project.remove_entity(item.entity.id)
                self._scene.removeItem(item)
                del self._entity_items[item.entity.id]

            elif isinstance(item, AssociationItem):
                # Remove connected links first
                links_to_remove = self._project.get_links_for_association(item.association.id)
                for link in links_to_remove:
                    link_item = self._link_items.get(link.id)
                    if link_item:
                        link_item.cleanup()
                        self._scene.removeItem(link_item)
                        del self._link_items[link.id]
                self._project.remove_association(item.association.id)
                self._scene.removeItem(item)
                del self._association_items[item.association.id]

            elif isinstance(item, LinkItem):
                item.cleanup()
                self._project.remove_link(item.link.id)
                self._scene.removeItem(item)
                del self._link_items[item.link.id]

        self.modified.emit()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Delete:
            self.delete_selected()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Track item positions before potential drag."""
        self._drag_start_positions.clear()

        # Track the item under cursor
        item = self.itemAt(event.pos())
        if isinstance(item, EntityItem):
            self._drag_start_positions[item.entity.id] = QPointF(item.pos())
        elif isinstance(item, AssociationItem):
            self._drag_start_positions[item.association.id] = QPointF(item.pos())

        # Also track already selected items
        for sel_item in self._scene.selectedItems():
            if isinstance(sel_item, EntityItem):
                self._drag_start_positions[sel_item.entity.id] = QPointF(sel_item.pos())
            elif isinstance(sel_item, AssociationItem):
                self._drag_start_positions[sel_item.association.id] = QPointF(sel_item.pos())

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Detect if items were moved and emit modified signal."""
        super().mouseReleaseEvent(event)

        if not self._drag_start_positions:
            return

        # Check if any tracked items moved
        moved = False
        for item in self._scene.items():
            if isinstance(item, EntityItem):
                item_id = item.entity.id
                if item_id in self._drag_start_positions:
                    start_pos = self._drag_start_positions[item_id]
                    if item.pos().x() != start_pos.x() or item.pos().y() != start_pos.y():
                        moved = True
                        break
            elif isinstance(item, AssociationItem):
                item_id = item.association.id
                if item_id in self._drag_start_positions:
                    start_pos = self._drag_start_positions[item_id]
                    if item.pos().x() != start_pos.x() or item.pos().y() != start_pos.y():
                        moved = True
                        break

        if moved:
            self.modified.emit()

        self._drag_start_positions.clear()

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to edit items."""
        item = self.itemAt(event.pos())
        if isinstance(item, EntityItem):
            self._edit_entity(item)
        elif isinstance(item, AssociationItem):
            self._edit_association(item)
        elif isinstance(item, LinkItem):
            self._edit_link(item)
        elif item and item.parentItem():
            # Handle clicking on child items (like cardinality labels)
            parent = item.parentItem()
            if isinstance(parent, LinkItem):
                self._edit_link(parent)
        else:
            super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        if event.modifiers() & Qt.ControlModifier:
            # Zoom with Ctrl + scroll
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            super().wheelEvent(event)

    def zoom_in(self):
        """Zoom in by one step."""
        new_zoom = self._zoom_level * self.ZOOM_STEP
        if new_zoom <= self.ZOOM_MAX:
            self._apply_zoom(new_zoom)

    def zoom_out(self):
        """Zoom out by one step."""
        new_zoom = self._zoom_level / self.ZOOM_STEP
        if new_zoom >= self.ZOOM_MIN:
            self._apply_zoom(new_zoom)

    def zoom_reset(self):
        """Reset zoom to 100%."""
        self._apply_zoom(1.0)

    def zoom_fit(self):
        """Fit the diagram to the view."""
        # Get bounding rect of all items
        items_rect = self._scene.itemsBoundingRect()
        if items_rect.isEmpty():
            self.zoom_reset()
            return

        # Add margin
        margin = 50
        items_rect.adjust(-margin, -margin, margin, margin)

        # Fit to view
        self.fitInView(items_rect, Qt.KeepAspectRatio)

        # Calculate and store the new zoom level
        view_rect = self.viewport().rect()
        scale_x = view_rect.width() / items_rect.width()
        scale_y = view_rect.height() / items_rect.height()
        new_zoom = min(scale_x, scale_y)

        # Clamp to limits
        new_zoom = max(self.ZOOM_MIN, min(self.ZOOM_MAX, new_zoom))
        self._zoom_level = new_zoom
        self.zoom_changed.emit(int(self._zoom_level * 100))

    def _apply_zoom(self, new_zoom: float):
        """Apply a new zoom level."""
        factor = new_zoom / self._zoom_level
        self._zoom_level = new_zoom
        self.scale(factor, factor)
        self.zoom_changed.emit(int(self._zoom_level * 100))

    def get_zoom_level(self) -> int:
        """Get current zoom level as percentage."""
        return int(self._zoom_level * 100)

    def export_to_svg(self, file_path: str) -> bool:
        """Export the diagram to SVG format."""
        try:
            # Get bounding rect of all items with margin
            items_rect = self._scene.itemsBoundingRect()
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
            self._scene.render(painter, QRectF(0, 0, items_rect.width(), items_rect.height()), items_rect)
            painter.end()
            return True
        except Exception:
            return False

    def export_to_png(self, file_path: str, scale: float = 2.0) -> bool:
        """Export the diagram to PNG format with optional scale for higher resolution."""
        try:
            # Get bounding rect of all items with margin
            items_rect = self._scene.itemsBoundingRect()
            if items_rect.isEmpty():
                return False

            margin = 20
            items_rect.adjust(-margin, -margin, margin, margin)

            # Create image with scaled size for better quality
            width = int(items_rect.width() * scale)
            height = int(items_rect.height() * scale)
            image = QImage(width, height, QImage.Format_ARGB32)
            image.fill(QColor(255, 255, 255))  # White background

            painter = QPainter()
            painter.begin(image)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            self._scene.render(painter, QRectF(0, 0, width, height), items_rect)
            painter.end()

            return image.save(file_path, "PNG")
        except Exception:
            return False

    def export_to_pdf(self, file_path: str) -> bool:
        """Export the diagram to PDF format."""
        try:
            from PySide6.QtGui import QPdfWriter

            # Get bounding rect of all items with margin
            items_rect = self._scene.itemsBoundingRect()
            if items_rect.isEmpty():
                return False

            margin = 20
            items_rect.adjust(-margin, -margin, margin, margin)

            writer = QPdfWriter(file_path)
            writer.setTitle("Merisio MCD Diagram")
            writer.setCreator("Merisio")

            # Set page size to fit the diagram
            page_size = QPageSize(QSizeF(items_rect.width(), items_rect.height()), QPageSize.Point)
            writer.setPageSize(page_size)
            writer.setPageMargins(QMarginsF(0, 0, 0, 0))

            painter = QPainter()
            painter.begin(writer)
            painter.setRenderHint(QPainter.Antialiasing)

            # Scale to fit the PDF page
            scale = min(writer.width() / items_rect.width(), writer.height() / items_rect.height())
            painter.scale(scale, scale)

            self._scene.render(painter, QRectF(0, 0, items_rect.width(), items_rect.height()), items_rect)
            painter.end()
            return True
        except Exception:
            return False

    def set_show_attributes(self, show: bool):
        """Toggle showing attributes in entity and association items."""
        self._show_attributes = show
        EntityItem.show_attributes = show
        AssociationItem.show_attributes = show
        # Refresh all entity items
        for item in self._entity_items.values():
            item.refresh()
        # Refresh all association items
        for item in self._association_items.values():
            item.refresh()
        # Update all links (positions may change due to resized items)
        for link_item in self._link_items.values():
            link_item.update_position()

    def set_link_style(self, style: str):
        """Set the link style: 'curved', 'orthogonal', or 'straight'."""
        self._link_style = style
        LinkItem.link_style = style
        # Update all link items
        for link_item in self._link_items.values():
            link_item.update_position()
