from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QMenu, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPainter, QAction

from ..models.project import Project
from ..models.entity import Entity
from ..models.association import Association
from ..models.link import Link
from .mcd_items import EntityItem, AssociationItem, LinkItem


class MCDCanvas(QGraphicsView):
    """Canvas for editing MCD diagrams."""

    # Signals
    modified = Signal()  # Emitted when the diagram is modified

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        # Item tracking
        self._entity_items: dict[str, EntityItem] = {}
        self._association_items: dict[str, AssociationItem] = {}
        self._link_items: dict[str, LinkItem] = {}

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
            factor = 1.2
            if event.angleDelta().y() < 0:
                factor = 1 / factor
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def toggle_show_attributes(self, show: bool):
        """Toggle showing attributes in entity items."""
        EntityItem.show_attributes = show
        # Refresh all entity items
        for item in self._entity_items.values():
            item.refresh()
