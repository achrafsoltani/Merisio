"""Project tree navigator — lists entities and associations."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...models.project import Project


class ProjectTree(QWidget):
    """Sidebar tree showing project entities and associations."""

    item_selected = Signal(str, str)  # (type: "entity"/"association", id)
    item_double_clicked = Signal(str, str)
    add_entity_requested = Signal()
    add_association_requested = Signal()
    delete_requested = Signal(str, str)

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QLabel("PROJECT")
        header.setStyleSheet("font-weight: bold; color: #5F6368; padding: 4px 8px;")
        layout.addWidget(header)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self._tree.currentItemChanged.connect(self._on_current_changed)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        self._tree.setIndentation(16)
        layout.addWidget(self._tree)

    def set_project(self, project: Project):
        self._project = project
        self.refresh()

    def refresh(self):
        self._tree.clear()

        # Entities
        entities_root = QTreeWidgetItem(["Entities"])
        entities_root.setFlags(entities_root.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        entities_root.setExpanded(True)
        for entity in self._project.get_all_entities():
            item = QTreeWidgetItem([entity.name])
            item.setData(0, Qt.ItemDataRole.UserRole, ("entity", entity.id))
            entities_root.addChild(item)
        self._tree.addTopLevelItem(entities_root)

        # Associations
        assocs_root = QTreeWidgetItem(["Associations"])
        assocs_root.setFlags(assocs_root.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        assocs_root.setExpanded(True)
        for assoc in self._project.get_all_associations():
            item = QTreeWidgetItem([assoc.name])
            item.setData(0, Qt.ItemDataRole.UserRole, ("association", assoc.id))
            assocs_root.addChild(item)
        self._tree.addTopLevelItem(assocs_root)

    def select_item(self, item_type: str, item_id: str):
        """Select an item in the tree programmatically (without emitting signals)."""
        self._tree.blockSignals(True)
        for i in range(self._tree.topLevelItemCount()):
            root = self._tree.topLevelItem(i)
            for j in range(root.childCount()):
                child = root.child(j)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                if data and data == (item_type, item_id):
                    self._tree.setCurrentItem(child)
                    self._tree.blockSignals(False)
                    return
        self._tree.blockSignals(False)

    def _on_current_changed(self, current, previous):
        if current is None:
            return
        data = current.data(0, Qt.ItemDataRole.UserRole)
        if data:
            item_type, item_id = data
            self.item_selected.emit(item_type, item_id)

    def _on_double_click(self, item, column):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data:
            item_type, item_id = data
            self.item_double_clicked.emit(item_type, item_id)

    def _on_context_menu(self, pos):
        menu = QMenu(self)
        item = self._tree.itemAt(pos)

        menu.addAction("Add Entity", lambda: self.add_entity_requested.emit())
        menu.addAction("Add Association", lambda: self.add_association_requested.emit())

        if item:
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if data:
                item_type, item_id = data
                menu.addSeparator()
                menu.addAction("Edit", lambda: self.item_double_clicked.emit(item_type, item_id))
                menu.addAction("Delete", lambda: self.delete_requested.emit(item_type, item_id))

        menu.exec(self._tree.mapToGlobal(pos))
