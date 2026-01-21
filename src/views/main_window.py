from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar,
    QMessageBox, QFileDialog, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QCheckBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon
import os

from ..models.project import Project
from ..utils.constants import APP_NAME, APP_VERSION, FILE_FILTER
from ..utils.file_io import FileIO
from ..controllers.mcd_controller import MCDController
from .dictionary_view import DictionaryView
from .mcd_canvas import MCDCanvas
from .mld_view import MLDView
from .sql_view import SQLView


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self._project = Project()
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._connect_signals()
        self._update_title()

    def _setup_ui(self):
        """Set up the main UI layout."""
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setMinimumSize(1024, 768)

        # Central widget with tabs
        self._tabs = QTabWidget()
        self.setCentralWidget(self._tabs)

        # Dictionary tab (read-only overview of all attributes)
        self._dictionary_view = DictionaryView(self._project)
        self._tabs.addTab(self._dictionary_view, "Dictionary")

        # MCD tab
        mcd_widget = QWidget()
        mcd_layout = QVBoxLayout(mcd_widget)
        mcd_layout.setContentsMargins(8, 8, 8, 8)
        mcd_layout.setSpacing(8)

        # MCD toolbar
        mcd_toolbar = QHBoxLayout()
        self._add_entity_btn = QPushButton("Add Entity")
        self._add_entity_btn.clicked.connect(self._on_add_entity)
        mcd_toolbar.addWidget(self._add_entity_btn)

        self._add_assoc_btn = QPushButton("Add Association")
        self._add_assoc_btn.clicked.connect(self._on_add_association)
        mcd_toolbar.addWidget(self._add_assoc_btn)

        self._add_link_btn = QPushButton("Add Link")
        self._add_link_btn.clicked.connect(self._on_add_link)
        mcd_toolbar.addWidget(self._add_link_btn)

        self._delete_btn = QPushButton("Delete Selected")
        self._delete_btn.clicked.connect(self._on_delete_selected)
        mcd_toolbar.addWidget(self._delete_btn)

        mcd_toolbar.addStretch()

        self._show_attrs_check = QCheckBox("Show Attributes")
        self._show_attrs_check.setChecked(True)
        self._show_attrs_check.toggled.connect(self._on_toggle_attributes)
        mcd_toolbar.addWidget(self._show_attrs_check)

        self._validate_btn = QPushButton("Validate")
        self._validate_btn.clicked.connect(self._on_validate)
        mcd_toolbar.addWidget(self._validate_btn)

        mcd_layout.addLayout(mcd_toolbar)

        self._mcd_canvas = MCDCanvas(self._project)
        mcd_layout.addWidget(self._mcd_canvas)

        self._tabs.addTab(mcd_widget, "MCD")

        # MLD tab
        self._mld_view = MLDView(self._project)
        self._tabs.addTab(self._mld_view, "MLD")

        # SQL tab
        self._sql_view = SQLView(self._project)
        self._tabs.addTab(self._sql_view, "SQL")

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel("Ready")
        self._status_bar.addWidget(self._status_label)

    def _setup_menus(self):
        """Set up menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        new_action = QAction("&New Project", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        properties_action = QAction("Project &Properties...", self)
        properties_action.triggered.connect(self._on_project_properties)
        file_menu.addAction(properties_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        delete_action = QAction("&Delete Selected", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self._on_delete_selected)
        edit_menu.addAction(delete_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        dict_action = QAction("&Dictionary", self)
        dict_action.setShortcut("Ctrl+1")
        dict_action.triggered.connect(lambda: self._tabs.setCurrentIndex(0))
        view_menu.addAction(dict_action)

        mcd_action = QAction("&MCD", self)
        mcd_action.setShortcut("Ctrl+2")
        mcd_action.triggered.connect(lambda: self._tabs.setCurrentIndex(1))
        view_menu.addAction(mcd_action)

        mld_action = QAction("M&LD", self)
        mld_action.setShortcut("Ctrl+3")
        mld_action.triggered.connect(lambda: self._tabs.setCurrentIndex(2))
        view_menu.addAction(mld_action)

        sql_action = QAction("&SQL", self)
        sql_action.setShortcut("Ctrl+4")
        sql_action.triggered.connect(lambda: self._tabs.setCurrentIndex(3))
        view_menu.addAction(sql_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        """Set up the main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # File actions
        toolbar.addAction("New").triggered.connect(self._on_new)
        toolbar.addAction("Open").triggered.connect(self._on_open)
        toolbar.addAction("Save").triggered.connect(self._on_save)
        toolbar.addSeparator()

    def _connect_signals(self):
        """Connect signals between components."""
        self._mcd_canvas.modified.connect(self._on_modified)
        self._tabs.currentChanged.connect(self._on_tab_changed)

    def _update_title(self):
        """Update window title based on project state."""
        title = f"{APP_NAME} {APP_VERSION}"
        # Show project name instead of full path
        title += f" - {self._project.name}"
        if self._project.modified:
            title += " *"
        self.setWindowTitle(title)
        # Update status bar with full path
        self._update_path_status()

    def _update_path_status(self):
        """Update status bar with file path."""
        if self._project.file_path:
            self._status_label.setText(f"File: {self._project.file_path}")
        else:
            self._status_label.setText("New project (not saved)")

    def _update_status(self, message: str):
        """Update status bar message temporarily."""
        self._status_label.setText(message)

    def _on_modified(self):
        """Handle project modification."""
        self._project.modified = True
        self._update_title()
        # Refresh dictionary view since attributes now come from entities
        self._dictionary_view.refresh()

    def _on_tab_changed(self, index: int):
        """Handle tab change - auto-generate MLD/SQL."""
        if index == 2:  # MLD tab
            self._mld_view.generate_mld()
        elif index == 3:  # SQL tab
            self._sql_view.generate_sql()

    def _check_save(self) -> bool:
        """Check if user wants to save unsaved changes. Returns True to proceed."""
        if not self._project.modified:
            return True

        result = QMessageBox.question(
            self, "Unsaved Changes",
            "Do you want to save changes before proceeding?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save
        )

        if result == QMessageBox.Save:
            return self._on_save()
        elif result == QMessageBox.Discard:
            return True
        else:
            return False

    def _on_new(self):
        """Create a new project."""
        if not self._check_save():
            return

        self._project = Project()
        self._dictionary_view.set_project(self._project)
        self._mcd_canvas.set_project(self._project)
        self._mld_view.set_project(self._project)
        self._sql_view.set_project(self._project)
        self._update_title()
        self._update_status("New project created")

    def _on_open(self):
        """Open an existing project."""
        if not self._check_save():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "", FILE_FILTER
        )

        if file_path:
            project = FileIO.load_project(file_path)
            if project:
                self._project = project
                self._dictionary_view.set_project(self._project)
                self._mcd_canvas.set_project(self._project)
                self._mld_view.set_project(self._project)
                self._sql_view.set_project(self._project)
                self._update_title()
                self._update_status(f"Opened: {file_path}")
            else:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to open project:\n{file_path}"
                )

    def _on_save(self) -> bool:
        """Save the current project."""
        if not self._project.file_path:
            return self._on_save_as()

        if FileIO.save_project(self._project, self._project.file_path):
            self._update_title()
            self._update_status(f"Saved: {self._project.file_path}")
            return True
        else:
            QMessageBox.critical(self, "Error", "Failed to save project.")
            return False

    def _on_save_as(self) -> bool:
        """Save the project with a new name."""
        import os
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "", FILE_FILTER
        )

        if file_path:
            # Ensure correct extension
            if not file_path.endswith(".asip"):
                file_path += ".asip"

            # Set project name from filename (without extension)
            basename = os.path.basename(file_path)
            self._project.name = os.path.splitext(basename)[0]

            if FileIO.save_project(self._project, file_path):
                self._update_title()
                self._update_status(f"Saved: {file_path}")
                return True
            else:
                QMessageBox.critical(self, "Error", "Failed to save project.")
                return False

        return False

    def _on_add_entity(self):
        """Add entity via MCD canvas."""
        self._tabs.setCurrentIndex(1)  # Switch to MCD tab
        self._mcd_canvas.add_entity_at_center()

    def _on_add_association(self):
        """Add association via MCD canvas."""
        self._tabs.setCurrentIndex(1)
        self._mcd_canvas.add_association_at_center()

    def _on_add_link(self):
        """Add link via MCD canvas."""
        self._tabs.setCurrentIndex(1)
        self._mcd_canvas.add_link()

    def _on_delete_selected(self):
        """Delete selected items."""
        self._mcd_canvas.delete_selected()

    def _on_toggle_attributes(self, checked: bool):
        """Toggle showing attributes in entities."""
        self._mcd_canvas.toggle_show_attributes(checked)

    def _on_validate(self):
        """Validate the MCD model."""
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy

        controller = MCDController(self._project)
        errors = controller.validate()

        if errors:
            msg = "Validation found the following issues:\n\n"
            msg += "\n".join(f"- {e}" for e in errors)
            msgbox = QMessageBox(QMessageBox.Warning, "Validation Issues", msg, QMessageBox.Ok, self)
        else:
            stats = controller.get_statistics()
            msg = "Model is valid!\n\n"
            msg += f"Attributes: {stats['attributes']}\n"
            msg += f"Entities: {stats['entities']}\n"
            msg += f"Associations: {stats['associations']}\n"
            msg += f"Links: {stats['links']}"
            msgbox = QMessageBox(QMessageBox.Information, "Validation Passed", msg, QMessageBox.Ok, self)

        # Force wider dialog using spacer
        spacer = QSpacerItem(400, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout = msgbox.layout()
        layout.addItem(spacer, layout.rowCount(), 0, 1, layout.columnCount())
        msgbox.exec()

    def _on_project_properties(self):
        """Show project properties dialog."""
        from .dialogs.project_properties_dialog import ProjectPropertiesDialog

        dialog = ProjectPropertiesDialog(self._project, parent=self)
        if dialog.exec():
            dialog.apply_to_project()
            self._project.modified = True
            self._update_title()
            self._update_status("Project properties updated")

    def _on_about(self):
        """Show about dialog."""
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy

        msgbox = QMessageBox(self)
        msgbox.setWindowTitle(f"About {APP_NAME}")
        msgbox.setText(
            f"<h2>{APP_NAME}</h2>"
            f"<p><b>Version {APP_VERSION}</b></p>"
        )
        msgbox.setInformativeText(
            "<p>A modern MERISE database modeling tool.</p>"
            "<p>Built with Python and PySide6.</p>"
            "<br>"
            "<p><b>Author:</b> Achraf SOLTANI</p>"
        )

        # Make dialog wider
        spacer = QSpacerItem(450, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout = msgbox.layout()
        layout.addItem(spacer, layout.rowCount(), 0, 1, layout.columnCount())

        msgbox.exec()

    def closeEvent(self, event):
        """Handle window close event."""
        if self._check_save():
            event.accept()
        else:
            event.ignore()
