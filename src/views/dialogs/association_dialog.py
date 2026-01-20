from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTableWidget, QTableWidgetItem, QPushButton,
    QDialogButtonBox, QLabel, QMessageBox, QComboBox,
    QSpinBox, QCheckBox, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt

from ...models.association import Association
from ...models.attribute import Attribute
from ...utils.constants import DATA_TYPES


class AssociationDialog(QDialog):
    """Dialog for creating or editing an association with optional carrying attributes."""

    def __init__(self, association: Association = None, parent=None):
        super().__init__(parent)
        self._association = association
        self._is_edit = association is not None
        self._attributes: list[Attribute] = []

        if association:
            # Copy attributes for editing
            self._attributes = [
                Attribute(
                    name=a.name,
                    data_type=a.data_type,
                    size=a.size,
                    is_primary_key=a.is_primary_key
                ) for a in association.attributes
            ]

        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("Edit Association" if self._is_edit else "Add Association")
        self.setMinimumSize(500, 400)
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
        self._name_edit.setPlaceholderText("e.g., Places, Contains, BelongsTo")
        form.addRow("Association Name:", self._name_edit)
        layout.addLayout(form)

        # Carrying attributes section
        layout.addWidget(QLabel("Carrying Attributes (optional):"))

        # Info label
        info_label = QLabel(
            "Carrying attributes store data about the relationship itself, "
            "e.g., 'quantity' in an Order-Product relationship."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info_label)

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

        attr_toolbar.addStretch()
        layout.addLayout(attr_toolbar)

        # Attribute table
        self._attr_table = QTableWidget()
        self._attr_table.setColumnCount(3)
        self._attr_table.setHorizontalHeaderLabels(["Name", "Type", "Size"])
        self._attr_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._attr_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._attr_table.setAlternatingRowColors(True)
        self._attr_table.doubleClicked.connect(self._on_edit_attribute)

        # Configure header
        header = self._attr_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Interactive)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.resizeSection(1, 100)
        header.resizeSection(2, 70)
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
        """Load data from existing association if editing."""
        if self._association:
            self._name_edit.setText(self._association.name)
        self._refresh_table()

    def _refresh_table(self):
        """Refresh the attribute table."""
        self._attr_table.setRowCount(len(self._attributes))
        for row, attr in enumerate(self._attributes):
            self._attr_table.setItem(row, 0, QTableWidgetItem(attr.name))
            self._attr_table.setItem(row, 1, QTableWidgetItem(attr.data_type))
            size_str = str(attr.size) if attr.size else ""
            self._attr_table.setItem(row, 2, QTableWidgetItem(size_str))

    def _get_selected_row(self) -> int:
        """Get the currently selected row index, or -1 if none."""
        items = self._attr_table.selectedItems()
        if items:
            return items[0].row()
        return -1

    def _on_add_attribute(self):
        """Add a new carrying attribute."""
        from .entity_dialog import AttributeEditDialog

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
                # Carrying attributes are never PKs
                attr.is_primary_key = False
                self._attributes.append(attr)
                self._refresh_table()

    def _on_edit_attribute(self):
        """Edit selected attribute."""
        from .entity_dialog import AttributeEditDialog

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
                new_attr.is_primary_key = False  # Carrying attributes are never PKs
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

    def _on_accept(self):
        """Validate and accept the dialog."""
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter an association name.")
            self._name_edit.setFocus()
            return

        self.accept()

    def get_association(self) -> Association | None:
        """Get the association from the dialog."""
        name = self._name_edit.text().strip()
        if not name:
            return None

        if self._association:
            # Update existing association
            self._association.name = name
            self._association.attributes = self._attributes.copy()
            return self._association
        else:
            # Create new association
            return Association(name=name, attributes=self._attributes.copy())
