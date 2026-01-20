from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTableWidget, QTableWidgetItem, QPushButton,
    QDialogButtonBox, QLabel, QMessageBox, QComboBox,
    QSpinBox, QCheckBox, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt

from ...models.entity import Entity
from ...models.attribute import Attribute
from ...utils.constants import DATA_TYPES


class EntityDialog(QDialog):
    """Dialog for creating or editing an entity with its attributes."""

    def __init__(self, entity: Entity = None, parent=None):
        super().__init__(parent)
        self._entity = entity
        self._is_edit = entity is not None
        self._attributes: list[Attribute] = []

        if entity:
            # Copy attributes for editing
            self._attributes = [
                Attribute(
                    name=a.name,
                    data_type=a.data_type,
                    size=a.size,
                    is_primary_key=a.is_primary_key
                ) for a in entity.attributes
            ]

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("Edit Entity" if self._is_edit else "Add Entity")
        self.setMinimumSize(550, 450)
        self.setStyleSheet("""
            QDialog {
                border: 2px solid #3daee9;
                border-radius: 6px;
                background-color: palette(window);
            }
        """)

        layout = QVBoxLayout(self)

        # Name field
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Client, Product, Order")
        form.addRow("Entity Name:", self._name_edit)
        layout.addLayout(form)

        # Attributes section
        layout.addWidget(QLabel("Attributes:"))

        # Attribute toolbar
        attr_toolbar = QHBoxLayout()

        self._add_attr_btn = QPushButton("Add")
        self._add_attr_btn.clicked.connect(self._on_add_attribute)
        attr_toolbar.addWidget(self._add_attr_btn)

        self._edit_attr_btn = QPushButton("Edit")
        self._edit_attr_btn.clicked.connect(self._on_edit_attribute)
        attr_toolbar.addWidget(self._edit_attr_btn)

        self._delete_attr_btn = QPushButton("Delete")
        self._delete_attr_btn.clicked.connect(self._on_delete_attribute)
        attr_toolbar.addWidget(self._delete_attr_btn)

        self._move_up_btn = QPushButton("Up")
        self._move_up_btn.clicked.connect(self._on_move_up)
        attr_toolbar.addWidget(self._move_up_btn)

        self._move_down_btn = QPushButton("Down")
        self._move_down_btn.clicked.connect(self._on_move_down)
        attr_toolbar.addWidget(self._move_down_btn)

        attr_toolbar.addStretch()
        layout.addLayout(attr_toolbar)

        # Attribute table
        self._attr_table = QTableWidget()
        self._attr_table.setColumnCount(4)
        self._attr_table.setHorizontalHeaderLabels(["Name", "Type", "Size", "PK"])
        self._attr_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._attr_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._attr_table.setAlternatingRowColors(True)
        self._attr_table.doubleClicked.connect(self._on_edit_attribute)

        # Configure header
        header = self._attr_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.resizeSection(1, 100)
        header.resizeSection(2, 70)
        header.resizeSection(3, 50)
        header.setStretchLastSection(False)

        layout.addWidget(self._attr_table)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        """Load data from existing entity if editing."""
        if self._entity:
            self._name_edit.setText(self._entity.name)
        self._refresh_table()

    def _refresh_table(self):
        """Refresh the attribute table."""
        self._attr_table.setRowCount(len(self._attributes))
        for row, attr in enumerate(self._attributes):
            self._attr_table.setItem(row, 0, QTableWidgetItem(attr.name))
            self._attr_table.setItem(row, 1, QTableWidgetItem(attr.data_type))
            size_str = str(attr.size) if attr.size else ""
            self._attr_table.setItem(row, 2, QTableWidgetItem(size_str))
            pk_str = "Yes" if attr.is_primary_key else "No"
            self._attr_table.setItem(row, 3, QTableWidgetItem(pk_str))

    def _get_selected_row(self) -> int:
        """Get the currently selected row index, or -1 if none."""
        items = self._attr_table.selectedItems()
        if items:
            return items[0].row()
        return -1

    def _on_add_attribute(self):
        """Add a new attribute."""
        dialog = AttributeEditDialog(parent=self)
        if dialog.exec():
            attr = dialog.get_attribute()
            if attr:
                # Check for duplicate name
                for existing in self._attributes:
                    if existing.name == attr.name:
                        QMessageBox.warning(
                            self, "Duplicate Name",
                            f"Attribute '{attr.name}' already exists."
                        )
                        return
                self._attributes.append(attr)
                self._refresh_table()

    def _on_edit_attribute(self):
        """Edit selected attribute."""
        row = self._get_selected_row()
        if row < 0:
            QMessageBox.information(self, "Info", "Please select an attribute to edit.")
            return

        attr = self._attributes[row]
        dialog = AttributeEditDialog(attribute=attr, parent=self)
        if dialog.exec():
            new_attr = dialog.get_attribute()
            if new_attr:
                # Check for duplicate name (excluding current)
                for i, existing in enumerate(self._attributes):
                    if i != row and existing.name == new_attr.name:
                        QMessageBox.warning(
                            self, "Duplicate Name",
                            f"Attribute '{new_attr.name}' already exists."
                        )
                        return
                self._attributes[row] = new_attr
                self._refresh_table()

    def _on_delete_attribute(self):
        """Delete selected attribute."""
        row = self._get_selected_row()
        if row < 0:
            QMessageBox.information(self, "Info", "Please select an attribute to delete.")
            return

        attr = self._attributes[row]
        result = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete attribute '{attr.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if result == QMessageBox.Yes:
            del self._attributes[row]
            self._refresh_table()

    def _on_move_up(self):
        """Move selected attribute up."""
        row = self._get_selected_row()
        if row <= 0:
            return
        self._attributes[row], self._attributes[row - 1] = \
            self._attributes[row - 1], self._attributes[row]
        self._refresh_table()
        self._attr_table.selectRow(row - 1)

    def _on_move_down(self):
        """Move selected attribute down."""
        row = self._get_selected_row()
        if row < 0 or row >= len(self._attributes) - 1:
            return
        self._attributes[row], self._attributes[row + 1] = \
            self._attributes[row + 1], self._attributes[row]
        self._refresh_table()
        self._attr_table.selectRow(row + 1)

    def _on_accept(self):
        """Validate and accept the dialog."""
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter an entity name.")
            self._name_edit.setFocus()
            return

        if not self._attributes:
            QMessageBox.warning(
                self, "Validation Error",
                "Please add at least one attribute to the entity."
            )
            return

        # Check for at least one primary key
        has_pk = any(attr.is_primary_key for attr in self._attributes)
        if not has_pk:
            result = QMessageBox.question(
                self, "No Primary Key",
                "Entity has no primary key. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return

        self.accept()

    def get_entity(self) -> Entity | None:
        """Get the entity from the dialog."""
        name = self._name_edit.text().strip()
        if not name:
            return None

        if self._entity:
            # Update existing entity
            self._entity.name = name
            self._entity.attributes = self._attributes.copy()
            return self._entity
        else:
            # Create new entity
            return Entity(name=name, attributes=self._attributes.copy())


class AttributeEditDialog(QDialog):
    """Dialog for adding/editing a single attribute."""

    def __init__(self, attribute: Attribute = None, parent=None):
        super().__init__(parent)
        self._attribute = attribute
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("Edit Attribute" if self._attribute else "Add Attribute")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                border: 2px solid #3daee9;
                border-radius: 6px;
                background-color: palette(window);
            }
        """)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., id, name, email")
        form.addRow("Name:", self._name_edit)

        self._type_combo = QComboBox()
        self._type_combo.addItems(DATA_TYPES)
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        form.addRow("Type:", self._type_combo)

        self._size_spin = QSpinBox()
        self._size_spin.setRange(0, 10000)
        self._size_spin.setSpecialValueText("N/A")
        self._size_spin.setValue(0)
        form.addRow("Size:", self._size_spin)

        self._pk_check = QCheckBox("Primary Key")
        form.addRow("", self._pk_check)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_data(self):
        """Load data from existing attribute if editing."""
        if self._attribute:
            self._name_edit.setText(self._attribute.name)
            index = self._type_combo.findText(self._attribute.data_type)
            if index >= 0:
                self._type_combo.setCurrentIndex(index)
            if self._attribute.size:
                self._size_spin.setValue(self._attribute.size)
            self._pk_check.setChecked(self._attribute.is_primary_key)

        self._on_type_changed(self._type_combo.currentText())

    def _on_type_changed(self, type_name: str):
        """Enable/disable size field based on type."""
        size_relevant = type_name in ("VARCHAR", "CHAR", "DECIMAL")
        self._size_spin.setEnabled(size_relevant)
        if not size_relevant:
            self._size_spin.setValue(0)

    def _on_accept(self):
        """Validate and accept."""
        name = self._name_edit.text().strip()
        if not name:
            self._name_edit.setFocus()
            return
        self.accept()

    def get_attribute(self) -> Attribute | None:
        """Get the attribute from the dialog."""
        name = self._name_edit.text().strip()
        if not name:
            return None

        size = self._size_spin.value() if self._size_spin.isEnabled() else None
        if size == 0:
            size = None

        return Attribute(
            name=name,
            data_type=self._type_combo.currentText(),
            size=size,
            is_primary_key=self._pk_check.isChecked()
        )
