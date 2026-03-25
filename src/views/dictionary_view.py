from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QLabel,
    QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QColor

from ..models.attribute import Attribute
from ..models.project import Project


class DictionaryTableModel(QAbstractTableModel):
    """Read-only table model showing all attributes across entities."""

    COLUMNS = ["Entity", "Attribute", "Type", "Size", "PK"]

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._data: list[tuple[str, Attribute]] = []
        self._highlighted_entity: str = ""
        self.refresh()

    def set_project(self, project: Project):
        """Set a new project and refresh."""
        self._project = project
        self.refresh()

    def refresh(self):
        """Refresh the model from the project."""
        self.beginResetModel()
        self._data = self._project.get_all_attributes()
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self._data):
            return None

        entity_name, attr = self._data[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0:
                return entity_name
            elif col == 1:
                return attr.name
            elif col == 2:
                return attr.data_type
            elif col == 3:
                return str(attr.size) if attr.size else ""
            elif col == 4:
                return "Yes" if attr.is_primary_key else "No"

        elif role == Qt.BackgroundRole:
            if self._highlighted_entity and entity_name == self._highlighted_entity:
                return QColor("#E3F2FD")  # Light blue for selected entity
            if attr.is_primary_key:
                return QColor("#FFFDE7")  # Light yellow for PKs

        elif role == Qt.TextAlignmentRole:
            if col in (3, 4):
                return Qt.AlignCenter

        return None


class DictionaryView(QWidget):
    """Read-only view showing all attributes across all entities."""

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Info label
        info_label = QLabel(
            "This is a read-only overview of all attributes. "
            "To edit attributes, go to the MCD tab and edit the entity."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; padding: 5px;")
        layout.addWidget(info_label)

        # Table view
        self._model = DictionaryTableModel(self._project)
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Configure header
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Entity
        header.setSectionResizeMode(1, QHeaderView.Stretch)      # Attribute
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # Type
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # Size
        header.setSectionResizeMode(4, QHeaderView.Interactive)  # PK
        header.resizeSection(0, 120)
        header.resizeSection(2, 100)
        header.resizeSection(3, 70)
        header.resizeSection(4, 50)
        header.setStretchLastSection(False)

        layout.addWidget(self._table)

    def set_project(self, project: Project):
        """Set a new project and refresh the view."""
        self._project = project
        self._model.set_project(project)

    def refresh(self):
        """Refresh the view from the project."""
        self._model.refresh()

    def highlight_entity(self, entity_name: str):
        """Highlight all rows for the given entity."""
        self._model._highlighted_entity = entity_name
        self._model.dataChanged.emit(
            self._model.index(0, 0),
            self._model.index(self._model.rowCount() - 1, self._model.columnCount() - 1),
        )

    def clear_highlight(self):
        """Clear row highlighting."""
        self.highlight_entity("")
