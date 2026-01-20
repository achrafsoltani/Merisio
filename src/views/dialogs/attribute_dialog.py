from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QCheckBox,
    QPushButton, QDialogButtonBox
)
from PySide6.QtCore import Qt

from ...models.attribute import Attribute
from ...models.dictionary import Dictionary
from ...utils.constants import DATA_TYPES


class AttributeDialog(QDialog):
    """Dialog for creating or editing an attribute."""

    def __init__(self, dictionary: Dictionary, attribute: Attribute = None, parent=None):
        super().__init__(parent)
        self._dictionary = dictionary
        self._attribute = attribute
        self._is_edit = attribute is not None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("Edit Attribute" if self._is_edit else "Add Attribute")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        # Form layout
        form = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g., id_client, nom, email")
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

        # Buttons
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
        """Handle type selection change - enable/disable size field."""
        # Size is relevant for VARCHAR, CHAR, DECIMAL
        size_relevant = type_name in ("VARCHAR", "CHAR", "DECIMAL")
        self._size_spin.setEnabled(size_relevant)
        if not size_relevant:
            self._size_spin.setValue(0)

    def _on_accept(self):
        """Validate and accept the dialog."""
        name = self._name_edit.text().strip()
        if not name:
            self._name_edit.setFocus()
            return

        # Check for duplicate names (if adding or if name changed)
        if not self._is_edit or (self._is_edit and name != self._attribute.name):
            if self._dictionary.has_attribute(name):
                self._name_edit.selectAll()
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
