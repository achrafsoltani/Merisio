from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QComboBox, QDialogButtonBox, QLabel, QGroupBox
)
from PySide6.QtCore import Qt

from ...models.link import Link
from ...models.entity import Entity
from ...models.association import Association
from ...utils.constants import CARDINALITY_MIN, CARDINALITY_MAX


class LinkDialog(QDialog):
    """Dialog for creating or editing a link with cardinalities."""

    def __init__(
        self,
        entities: list[Entity],
        associations: list[Association],
        link: Link = None,
        parent=None
    ):
        super().__init__(parent)
        self._entities = entities
        self._associations = associations
        self._link = link
        self._is_edit = link is not None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        self.setWindowTitle("Edit Link" if self._is_edit else "Add Link")
        self.setMinimumWidth(350)

        layout = QVBoxLayout(self)

        # Entity and Association selection
        form = QFormLayout()

        self._entity_combo = QComboBox()
        for entity in self._entities:
            self._entity_combo.addItem(entity.name, entity.id)
        form.addRow("Entity:", self._entity_combo)

        self._assoc_combo = QComboBox()
        for assoc in self._associations:
            self._assoc_combo.addItem(assoc.name, assoc.id)
        form.addRow("Association:", self._assoc_combo)

        layout.addLayout(form)

        # Cardinality group
        card_group = QGroupBox("Cardinality")
        card_layout = QHBoxLayout()

        self._card_min_combo = QComboBox()
        self._card_min_combo.addItems(CARDINALITY_MIN)
        card_layout.addWidget(QLabel("Min:"))
        card_layout.addWidget(self._card_min_combo)

        card_layout.addWidget(QLabel(","))

        self._card_max_combo = QComboBox()
        self._card_max_combo.addItems(CARDINALITY_MAX)
        card_layout.addWidget(QLabel("Max:"))
        card_layout.addWidget(self._card_max_combo)

        card_layout.addStretch()

        card_group.setLayout(card_layout)
        layout.addWidget(card_group)

        # Preview
        self._preview_label = QLabel()
        self._preview_label.setStyleSheet("font-weight: bold; padding: 10px;")
        layout.addWidget(self._preview_label)

        # Connect signals for preview update
        self._card_min_combo.currentTextChanged.connect(self._update_preview)
        self._card_max_combo.currentTextChanged.connect(self._update_preview)
        self._entity_combo.currentTextChanged.connect(self._update_preview)
        self._assoc_combo.currentTextChanged.connect(self._update_preview)

        # Info label
        info_label = QLabel(
            "Common cardinalities:\n"
            "• (0,N) - Optional, many\n"
            "• (1,N) - Mandatory, many\n"
            "• (0,1) - Optional, single\n"
            "• (1,1) - Mandatory, single"
        )
        info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._update_preview()

    def _load_data(self):
        """Load data from existing link if editing."""
        if self._link:
            # Set entity
            index = self._entity_combo.findData(self._link.entity_id)
            if index >= 0:
                self._entity_combo.setCurrentIndex(index)

            # Set association
            index = self._assoc_combo.findData(self._link.association_id)
            if index >= 0:
                self._assoc_combo.setCurrentIndex(index)

            # Set cardinalities
            index = self._card_min_combo.findText(self._link.cardinality_min)
            if index >= 0:
                self._card_min_combo.setCurrentIndex(index)

            index = self._card_max_combo.findText(self._link.cardinality_max)
            if index >= 0:
                self._card_max_combo.setCurrentIndex(index)

    def _update_preview(self):
        """Update the cardinality preview."""
        entity = self._entity_combo.currentText()
        assoc = self._assoc_combo.currentText()
        card_min = self._card_min_combo.currentText()
        card_max = self._card_max_combo.currentText()

        self._preview_label.setText(
            f"[{entity}] —({card_min},{card_max})— [{assoc}]"
        )

    def get_link(self) -> Link | None:
        """Get the link from the dialog."""
        entity_id = self._entity_combo.currentData()
        assoc_id = self._assoc_combo.currentData()

        if not entity_id or not assoc_id:
            return None

        if self._link:
            # Update existing link
            self._link.entity_id = entity_id
            self._link.association_id = assoc_id
            self._link.cardinality_min = self._card_min_combo.currentText()
            self._link.cardinality_max = self._card_max_combo.currentText()
            return self._link
        else:
            # Create new link
            return Link(
                entity_id=entity_id,
                association_id=assoc_id,
                cardinality_min=self._card_min_combo.currentText(),
                cardinality_max=self._card_max_combo.currentText()
            )
