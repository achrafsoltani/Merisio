"""Properties panel — inline editor for selected entity/association."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QCheckBox,
    QVBoxLayout,
    QWidget,
)

from ...models.project import Project
from ...utils.constants import DATA_TYPES


class PropertiesPanel(QWidget):
    """Sidebar panel showing properties of the selected item."""

    property_changed = Signal()  # emitted when user edits a property

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._current_type = None  # "entity" or "association"
        self._current_id = None
        self._updating = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QLabel("PROPERTIES")
        header.setStyleSheet("font-weight: bold; color: #5F6368; padding: 4px 8px;")
        layout.addWidget(header)

        self._empty_label = QLabel("Select an entity or association")
        self._empty_label.setStyleSheet("color: #9AA0A6; padding: 8px;")
        self._empty_label.setWordWrap(True)
        layout.addWidget(self._empty_label)

        # Form container (hidden when nothing selected)
        self._form_widget = QWidget()
        form_layout = QVBoxLayout(self._form_widget)
        form_layout.setContentsMargins(8, 0, 8, 0)
        form_layout.setSpacing(6)

        # Name field
        name_form = QFormLayout()
        name_form.setContentsMargins(0, 0, 0, 0)
        self._name_edit = QLineEdit()
        self._name_edit.editingFinished.connect(self._on_name_changed)
        name_form.addRow("Name:", self._name_edit)
        form_layout.addLayout(name_form)

        # Type label
        self._type_label = QLabel()
        self._type_label.setStyleSheet("color: #5F6368;")
        form_layout.addWidget(self._type_label)

        # Attributes table
        attrs_label = QLabel("Attributes:")
        attrs_label.setStyleSheet("font-weight: bold; margin-top: 4px;")
        form_layout.addWidget(attrs_label)

        self._attrs_table = QTableWidget()
        self._attrs_table.setColumnCount(3)
        self._attrs_table.setHorizontalHeaderLabels(["Name", "Type", "PK"])
        self._attrs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._attrs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._attrs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._attrs_table.verticalHeader().setVisible(False)
        self._attrs_table.setMaximumHeight(200)
        self._attrs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        form_layout.addWidget(self._attrs_table)

        self._form_widget.setVisible(False)
        layout.addWidget(self._form_widget)

        layout.addStretch()

    def set_project(self, project: Project):
        self._project = project
        self.clear_selection()

    def clear_selection(self):
        self._current_type = None
        self._current_id = None
        self._form_widget.setVisible(False)
        self._empty_label.setVisible(True)

    def show_item(self, item_type: str, item_id: str):
        """Display properties for the given entity or association."""
        self._current_type = item_type
        self._current_id = item_id
        self._empty_label.setVisible(False)
        self._form_widget.setVisible(True)
        self._refresh_form()

    def _refresh_form(self):
        self._updating = True

        if self._current_type == "entity":
            entity = self._project.get_entity(self._current_id)
            if entity:
                self._name_edit.setText(entity.name)
                self._type_label.setText("Entity")
                self._show_attributes(entity.attributes)
            else:
                self.clear_selection()
                return

        elif self._current_type == "association":
            assoc = self._project.get_association(self._current_id)
            if assoc:
                self._name_edit.setText(assoc.name)
                self._type_label.setText("Association")
                self._show_attributes(assoc.attributes)
            else:
                self.clear_selection()
                return

        else:
            self.clear_selection()

        self._updating = False

    def _show_attributes(self, attributes):
        self._attrs_table.setRowCount(len(attributes))
        for i, attr in enumerate(attributes):
            self._attrs_table.setItem(i, 0, QTableWidgetItem(attr.name))
            type_str = attr.data_type
            if attr.size:
                type_str += f"({attr.size})"
            self._attrs_table.setItem(i, 1, QTableWidgetItem(type_str))
            pk_item = QTableWidgetItem("PK" if attr.is_primary_key else "")
            pk_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._attrs_table.setItem(i, 2, pk_item)

    def _on_name_changed(self):
        if self._updating or not self._current_id:
            return

        new_name = self._name_edit.text().strip()
        if not new_name:
            return

        if self._current_type == "entity":
            entity = self._project.get_entity(self._current_id)
            if entity and entity.name != new_name:
                entity.name = new_name
                self.property_changed.emit()

        elif self._current_type == "association":
            assoc = self._project.get_association(self._current_id)
            if assoc and assoc.name != new_name:
                assoc.name = new_name
                self.property_changed.emit()
