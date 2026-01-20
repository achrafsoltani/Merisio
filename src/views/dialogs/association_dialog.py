from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QListWidget, QListWidgetItem,
    QDialogButtonBox, QLabel, QMessageBox
)
from PySide6.QtCore import Qt

from ...models.association import Association
from ...models.dictionary import Dictionary


class AssociationDialog(QDialog):
    """Dialog for creating or editing an association."""

    def __init__(self, dictionary: Dictionary, association: Association = None, parent=None):
        super().__init__(parent)
        self._dictionary = dictionary
        self._association = association
        self._is_edit = association is not None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("Edit Association" if self._is_edit else "Add Association")
        self.setMinimumSize(400, 350)

        layout = QVBoxLayout(self)

        # Name field
        form = QFormLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Passer, Contenir, Appartenir")
        form.addRow("Name:", self._name_edit)
        layout.addLayout(form)

        # Carrying attributes (optional)
        layout.addWidget(QLabel("Carrying Attributes (optional):"))

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
            "Carrying attributes store data about the relationship itself, "
            "like quantity in an 'Order-Product' association."
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
        """Load data from existing association if editing."""
        if self._association:
            self._name_edit.setText(self._association.name)
            # Select the association's carrying attributes
            for i in range(self._attr_list.count()):
                item = self._attr_list.item(i)
                attr_name = item.data(Qt.UserRole)
                if attr_name in self._association.attributes:
                    item.setSelected(True)

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

        attributes = []
        for item in self._attr_list.selectedItems():
            attr_name = item.data(Qt.UserRole)
            attributes.append(attr_name)

        if self._association:
            # Update existing association
            self._association.name = name
            self._association.attributes = attributes
            return self._association
        else:
            # Create new association
            return Association(name=name, attributes=attributes)
