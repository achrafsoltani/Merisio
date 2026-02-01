from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QPushButton, QDialogButtonBox, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ...models.project import Project


class ColorButton(QPushButton):
    """A button that displays and allows selecting a color."""

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        self.setFixedSize(80, 28)
        self._update_style()
        self.clicked.connect(self._pick_color)

    def _update_style(self):
        """Update button style to show the current color."""
        # Calculate contrasting text color
        qcolor = QColor(self._color)
        luminance = 0.299 * qcolor.red() + 0.587 * qcolor.green() + 0.114 * qcolor.blue()
        text_color = "#000000" if luminance > 128 else "#FFFFFF"

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color};
                color: {text_color};
                border: 1px solid #666;
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                border: 2px solid #333;
            }}
        """)
        self.setText(self._color.upper())

    def _pick_color(self):
        """Open color picker dialog."""
        from PySide6.QtWidgets import QColorDialog
        color = QColorDialog.getColor(QColor(self._color), self, "Select Color")
        if color.isValid():
            self._color = color.name()
            self._update_style()

    def get_color(self) -> str:
        """Get the current color."""
        return self._color

    def set_color(self, color: str):
        """Set the color."""
        self._color = color
        self._update_style()


class ColorSettingsDialog(QDialog):
    """Dialog for customizing diagram colors."""

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project
        self._setup_ui()
        self._load_colors()

    def _setup_ui(self):
        self.setWindowTitle("Diagram Colors")
        self.setMinimumSize(350, 300)

        layout = QVBoxLayout(self)

        # Entity colors section
        entity_label = QLabel("Entity Colors")
        entity_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(entity_label)

        entity_form = QFormLayout()
        entity_form.setContentsMargins(20, 5, 0, 10)

        self._entity_fill_btn = ColorButton("#E3F2FD")
        entity_form.addRow("Fill:", self._entity_fill_btn)

        self._entity_border_btn = ColorButton("#1976D2")
        entity_form.addRow("Border:", self._entity_border_btn)

        layout.addLayout(entity_form)

        # Separator
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)

        # Association colors section
        assoc_label = QLabel("Association Colors")
        assoc_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(assoc_label)

        assoc_form = QFormLayout()
        assoc_form.setContentsMargins(20, 5, 0, 10)

        self._assoc_fill_btn = ColorButton("#FFF3E0")
        assoc_form.addRow("Fill:", self._assoc_fill_btn)

        self._assoc_border_btn = ColorButton("#F57C00")
        assoc_form.addRow("Border:", self._assoc_border_btn)

        layout.addLayout(assoc_form)

        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

        # Link colors section
        link_label = QLabel("Link Colors")
        link_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(link_label)

        link_form = QFormLayout()
        link_form.setContentsMargins(20, 5, 0, 10)

        self._link_color_btn = ColorButton("#000000")
        link_form.addRow("Line & Cardinality:", self._link_color_btn)

        layout.addLayout(link_form)

        layout.addStretch()

        # Reset button
        reset_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_defaults)
        reset_layout.addWidget(reset_btn)
        reset_layout.addStretch()
        layout.addLayout(reset_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_colors(self):
        """Load colors from the project."""
        colors = self._project.colors
        self._entity_fill_btn.set_color(colors.get("entity_fill", "#E3F2FD"))
        self._entity_border_btn.set_color(colors.get("entity_border", "#1976D2"))
        self._assoc_fill_btn.set_color(colors.get("association_fill", "#FFF3E0"))
        self._assoc_border_btn.set_color(colors.get("association_border", "#F57C00"))
        self._link_color_btn.set_color(colors.get("link_color", "#000000"))

    def _reset_defaults(self):
        """Reset colors to default values."""
        self._entity_fill_btn.set_color("#E3F2FD")
        self._entity_border_btn.set_color("#1976D2")
        self._assoc_fill_btn.set_color("#FFF3E0")
        self._assoc_border_btn.set_color("#F57C00")
        self._link_color_btn.set_color("#000000")

    def apply_to_project(self):
        """Apply the selected colors to the project."""
        self._project.colors["entity_fill"] = self._entity_fill_btn.get_color()
        self._project.colors["entity_border"] = self._entity_border_btn.get_color()
        self._project.colors["association_fill"] = self._assoc_fill_btn.get_color()
        self._project.colors["association_border"] = self._assoc_border_btn.get_color()
        self._project.colors["link_color"] = self._link_color_btn.get_color()
