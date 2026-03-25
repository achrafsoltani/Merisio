"""Output panel — bottom tabbed panel with dictionary, validation, SQL preview."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout, QWidget

from ..controllers.mcd_controller import MCDController
from ..models.project import Project
from .dictionary_view import DictionaryView
from .sql_view import SQLView


class OutputPanel(QTabWidget):
    """Bottom panel with Dictionary, Validation, and SQL Preview tabs."""

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self._project = project

        # Dictionary tab (reuse existing view)
        self._dictionary_view = DictionaryView(project)
        self.addTab(self._dictionary_view, "Dictionary")

        # Validation tab
        self._validation_text = QTextEdit()
        self._validation_text.setReadOnly(True)
        self._validation_text.setPlaceholderText("Click Validate to check the model...")
        self.addTab(self._validation_text, "Validation")

        # SQL Preview tab (reuse existing view)
        self._sql_view = SQLView(project)
        self.addTab(self._sql_view, "SQL")

        self.setMaximumHeight(250)

        # Auto-refresh SQL when its tab is shown
        self.currentChanged.connect(self._on_tab_changed)

    @property
    def dictionary_view(self) -> DictionaryView:
        return self._dictionary_view

    @property
    def sql_view(self) -> SQLView:
        return self._sql_view

    def set_project(self, project: Project):
        self._project = project
        self._dictionary_view.set_project(project)
        self._sql_view.set_project(project)
        self._validation_text.clear()

    def _on_tab_changed(self, index: int):
        if index == 2:  # SQL tab
            self._sql_view.generate_sql()

    def highlight_entity(self, entity_name: str):
        """Highlight rows in dictionary for the given entity."""
        self._dictionary_view.highlight_entity(entity_name)

    def clear_highlight(self):
        """Clear dictionary highlights."""
        self._dictionary_view.clear_highlight()

    def refresh_dictionary(self):
        self._dictionary_view.refresh()

    def refresh_sql(self):
        self._sql_view.generate_sql()

    def run_validation(self, project: Project):
        """Run validation and display results."""
        controller = MCDController(project)
        errors = controller.validate()

        self._validation_text.clear()

        if errors:
            html = '<p style="color: #D32F2F; font-weight: bold;">Validation Issues:</p>'
            for err in errors:
                html += f'<p style="color: #D32F2F;">&#x2022; {err}</p>'
            self._validation_text.setHtml(html)
        else:
            stats = controller.get_statistics()
            html = '<p style="color: #2E7D32; font-weight: bold;">Model is valid!</p>'
            html += f'<p>Entities: {stats["entities"]} &nbsp; '
            html += f'Associations: {stats["associations"]} &nbsp; '
            html += f'Links: {stats["links"]} &nbsp; '
            html += f'Attributes: {stats["attributes"]}</p>'
            self._validation_text.setHtml(html)

        # Switch to validation tab
        self.setCurrentIndex(1)
