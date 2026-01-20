from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QDialogButtonBox, QLabel, QMessageBox
)
from PySide6.QtCore import Qt

from ...models.entity import Entity
from ...models.dictionary import Dictionary


class EntityDialog(QDialog):
    """Dialog for creating or editing an entity."""

    def __init__(self, dictionary: Dictionary, entity: Entity = None, parent=None):
        super().__init__(parent)
        self._dictionary = dictionary
        self._entity = entity
        self._is_edit = entity is not None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("Edit Entity" if self._is_edit else "Add Entity")
        self.setMinimumSize(400, 400)

        layout = QVBoxLayout(self)

        # Name field
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Client, Commande, Produit")
        form.addRow("Name:", self._name_edit)
        layout.addLayout(form)

        # Attributes selection
        layout.addWidget(QLabel("Select Attributes (from dictionary):"))

        self._attr_list = QListWidget()
        self._attr_list.setSelectionMode(QListWidget.MultiSelection)

        # Populate with dictionary attributes
        for attr in self._dictionary.get_all_attributes():
            item = QListWidgetItem(str(attr))
            item.setData(Qt.UserRole, attr.name)
            self._attr_list.addItem(item)

        layout.addWidget(self._attr_list)

        # Info label
        info_label = QLabel(
            "Tip: Primary key attributes are shown with [PK]. "
            "Hold Ctrl to select multiple attributes."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info_label)

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
            # Select the entity's attributes
            for i in range(self._attr_list.count()):
                item = self._attr_list.item(i)
                attr_name = item.data(Qt.UserRole)
                if attr_name in self._entity.attributes:
                    item.setSelected(True)

    def _on_accept(self):
        """Validate and accept the dialog."""
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Please enter an entity name.")
            self._name_edit.setFocus()
            return

        selected = self._attr_list.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, "Validation Error",
                "Please select at least one attribute for the entity."
            )
            return

        self.accept()

    def get_entity(self) -> Entity | None:
        """Get the entity from the dialog."""
        name = self._name_edit.text().strip()
        if not name:
            return None

        attributes = []
        for item in self._attr_list.selectedItems():
            attr_name = item.data(Qt.UserRole)
            attributes.append(attr_name)

        if self._entity:
            # Update existing entity
            self._entity.name = name
            self._entity.attributes = attributes
            return self._entity
        else:
            # Create new entity
            return Entity(name=name, attributes=attributes)
