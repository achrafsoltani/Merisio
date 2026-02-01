from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar,
    QMessageBox, QFileDialog, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QCheckBox, QSlider
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
        self._mcd_canvas.apply_colors(self._project.colors)
        self._tabs.setCurrentIndex(1)  # Start on MCD tab
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
        self._status_bar.addWidget(self._status_label, 1)  # Stretch to fill

        # Zoom controls in status bar (right side)
        round_btn_style = """
            QPushButton {
                border-radius: 10px;
                border: 1px solid #999;
                background-color: #f0f0f0;
                color: #333;
                font-weight: bold;
                font-size: 13px;
                padding: 0px;
                min-width: 20px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """

        self._zoom_out_btn = QPushButton("\u2212")  # Unicode minus sign
        self._zoom_out_btn.setFixedSize(20, 20)
        self._zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        self._zoom_out_btn.setStyleSheet(round_btn_style)
        self._zoom_out_btn.clicked.connect(self._on_zoom_out)
        self._status_bar.addPermanentWidget(self._zoom_out_btn)

        self._zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_slider.setFixedWidth(120)
        self._zoom_slider.setMinimum(25)   # 25%
        self._zoom_slider.setMaximum(400)  # 400%
        self._zoom_slider.setValue(100)    # 100%
        self._zoom_slider.setToolTip("Drag to zoom")
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider_changed)
        self._status_bar.addPermanentWidget(self._zoom_slider)

        self._zoom_in_btn = QPushButton("+")
        self._zoom_in_btn.setFixedSize(20, 20)
        self._zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
        self._zoom_in_btn.setStyleSheet(round_btn_style)
        self._zoom_in_btn.clicked.connect(self._on_zoom_in)
        self._status_bar.addPermanentWidget(self._zoom_in_btn)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(45)
        self._zoom_label.setAlignment(Qt.AlignCenter)
        self._status_bar.addPermanentWidget(self._zoom_label)

        self._zoom_fit_btn = QPushButton("Fit")
        self._zoom_fit_btn.setFixedSize(36, 22)
        self._zoom_fit_btn.setToolTip("Fit to View (Ctrl+0)")
        self._zoom_fit_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #999;
                border-radius: 3px;
                background-color: #f0f0f0;
                color: #333;
                padding: 2px 6px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        self._zoom_fit_btn.clicked.connect(self._on_zoom_fit)
        self._status_bar.addPermanentWidget(self._zoom_fit_btn)

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

        # Export submenu
        export_menu = file_menu.addMenu("&Export Diagram")

        export_svg_action = QAction("As &SVG...", self)
        export_svg_action.triggered.connect(self._on_export_svg)
        export_menu.addAction(export_svg_action)

        export_png_action = QAction("As &PNG...", self)
        export_png_action.triggered.connect(self._on_export_png)
        export_menu.addAction(export_png_action)

        export_pdf_action = QAction("As P&DF...", self)
        export_pdf_action.triggered.connect(self._on_export_pdf)
        export_menu.addAction(export_pdf_action)

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

        view_menu.addSeparator()

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self._on_zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self._on_zoom_out)
        view_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("&Reset Zoom", self)
        zoom_reset_action.setShortcut("Ctrl+Shift+0")
        zoom_reset_action.triggered.connect(self._on_zoom_reset)
        view_menu.addAction(zoom_reset_action)

        zoom_fit_action = QAction("&Fit to View", self)
        zoom_fit_action.setShortcut("Ctrl+0")
        zoom_fit_action.triggered.connect(self._on_zoom_fit)
        view_menu.addAction(zoom_fit_action)

        # Options menu
        options_menu = menubar.addMenu("&Options")

        self._show_attributes_action = QAction("Show &Attributes", self)
        self._show_attributes_action.setCheckable(True)
        self._show_attributes_action.setChecked(True)
        self._show_attributes_action.triggered.connect(self._on_toggle_attributes)
        options_menu.addAction(self._show_attributes_action)

        options_menu.addSeparator()

        # Link style submenu
        link_style_menu = options_menu.addMenu("Link Style")

        self._curved_links_action = QAction("&Curved", self)
        self._curved_links_action.setCheckable(True)
        self._curved_links_action.setChecked(True)
        self._curved_links_action.triggered.connect(lambda: self._on_link_style_changed("curved"))
        link_style_menu.addAction(self._curved_links_action)

        self._orthogonal_links_action = QAction("&Orthogonal", self)
        self._orthogonal_links_action.setCheckable(True)
        self._orthogonal_links_action.setChecked(False)
        self._orthogonal_links_action.triggered.connect(lambda: self._on_link_style_changed("orthogonal"))
        link_style_menu.addAction(self._orthogonal_links_action)

        self._straight_links_action = QAction("&Straight", self)
        self._straight_links_action.setCheckable(True)
        self._straight_links_action.setChecked(False)
        self._straight_links_action.triggered.connect(lambda: self._on_link_style_changed("straight"))
        link_style_menu.addAction(self._straight_links_action)

        options_menu.addSeparator()

        colors_action = QAction("Diagram &Colors...", self)
        colors_action.triggered.connect(self._on_diagram_colors)
        options_menu.addAction(colors_action)

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
        self._mcd_canvas.zoom_changed.connect(self._on_zoom_changed)
        self._mld_view.mld_modified.connect(self._on_modified)
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
        self._mcd_canvas.apply_colors(self._project.colors)
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
                self._mcd_canvas.apply_colors(self._project.colors)
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

    def _on_export_svg(self):
        """Export diagram as SVG."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export as SVG", "", "SVG Files (*.svg)"
        )
        if file_path:
            if not file_path.endswith(".svg"):
                file_path += ".svg"
            if self._mcd_canvas.export_to_svg(file_path):
                self._update_status(f"Exported: {file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export as SVG.")

    def _on_export_png(self):
        """Export diagram as PNG."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export as PNG", "", "PNG Files (*.png)"
        )
        if file_path:
            if not file_path.endswith(".png"):
                file_path += ".png"
            if self._mcd_canvas.export_to_png(file_path):
                self._update_status(f"Exported: {file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export as PNG.")

    def _on_export_pdf(self):
        """Export diagram as PDF."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export as PDF", "", "PDF Files (*.pdf)"
        )
        if file_path:
            if not file_path.endswith(".pdf"):
                file_path += ".pdf"
            if self._mcd_canvas.export_to_pdf(file_path):
                self._update_status(f"Exported: {file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export as PDF.")

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

    def _on_toggle_attributes(self, checked: bool):
        """Toggle attribute visibility in MCD."""
        self._mcd_canvas.set_show_attributes(checked)

    def _on_link_style_changed(self, style: str):
        """Change link style in MCD."""
        # Update checkmarks
        self._curved_links_action.setChecked(style == "curved")
        self._orthogonal_links_action.setChecked(style == "orthogonal")
        self._straight_links_action.setChecked(style == "straight")
        # Apply to canvas
        self._mcd_canvas.set_link_style(style)

    def _on_diagram_colors(self):
        """Show diagram colors dialog."""
        from .dialogs.color_settings_dialog import ColorSettingsDialog

        dialog = ColorSettingsDialog(self._project, parent=self)
        if dialog.exec():
            dialog.apply_to_project()
            self._mcd_canvas.apply_colors(self._project.colors)
            self._project.modified = True
            self._update_title()
            self._update_status("Diagram colors updated")

    def _on_zoom_in(self):
        """Zoom in on MCD canvas."""
        self._mcd_canvas.zoom_in()

    def _on_zoom_out(self):
        """Zoom out on MCD canvas."""
        self._mcd_canvas.zoom_out()

    def _on_zoom_reset(self):
        """Reset MCD canvas zoom to 100%."""
        self._mcd_canvas.zoom_reset()

    def _on_zoom_fit(self):
        """Fit MCD canvas to view."""
        self._mcd_canvas.zoom_fit()

    def _on_zoom_changed(self, percentage: int):
        """Update zoom label and slider when zoom changes."""
        self._zoom_label.setText(f"{percentage}%")
        # Update slider without triggering another zoom change
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(percentage)
        self._zoom_slider.blockSignals(False)

    def _on_zoom_slider_changed(self, value: int):
        """Handle zoom slider changes."""
        self._mcd_canvas._apply_zoom(value / 100.0)

    def closeEvent(self, event):
        """Handle window close event."""
        if self._check_save():
            event.accept()
        else:
            event.ignore()
