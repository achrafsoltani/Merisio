from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar,
    QMessageBox, QFileDialog, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QCheckBox, QSlider,
    QSplitter,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence, QIcon
import os

from ..models.project import Project
from ..utils.constants import APP_NAME, APP_VERSION, FILE_FILTER, MSD_FILE_FILTER
from ..utils.file_io import FileIO
from ..controllers.mcd_controller import MCDController
from .mcd_canvas import MCDCanvas
from .mld_view import MLDView
from .output_panel import OutputPanel
from .sidebar.project_tree import ProjectTree
from .sidebar.properties_panel import PropertiesPanel
from .sidebar.minimap import Minimap


class MainWindow(QMainWindow):
    """Main application window — MySQL Workbench-inspired layout."""

    def __init__(self):
        super().__init__()
        self._project = Project()
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._connect_signals()
        self._mcd_canvas.apply_colors(self._project.colors)
        self._tabs.setCurrentIndex(0)  # Start on MCD tab
        self._update_title()

    def _setup_ui(self):
        """Set up the main UI layout with sidebar + central tabs + bottom panel."""
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")

        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setMinimumSize(1100, 768)

        # =====================================================================
        # Main horizontal splitter: sidebar | content
        # =====================================================================
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self._main_splitter)

        # --- Left sidebar ---
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Minimap
        self._minimap = Minimap()
        sidebar_layout.addWidget(self._minimap)

        # Project tree
        self._project_tree = ProjectTree(self._project)
        sidebar_layout.addWidget(self._project_tree, 1)

        # Properties panel
        self._properties_panel = PropertiesPanel(self._project)
        sidebar_layout.addWidget(self._properties_panel, 1)

        sidebar.setMinimumWidth(180)
        sidebar.setMaximumWidth(320)
        self._main_splitter.addWidget(sidebar)

        # --- Right content area (vertical splitter: tabs on top, output on bottom) ---
        self._content_splitter = QSplitter(Qt.Orientation.Vertical)

        # Central tabs: MCD, MLD
        self._tabs = QTabWidget()

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

        self._tabs.addTab(mcd_widget, "MCD Diagram")

        # MLD tab
        self._mld_view = MLDView(self._project)
        self._tabs.addTab(self._mld_view, "MLD")

        self._content_splitter.addWidget(self._tabs)

        # Bottom output panel
        self._output_panel = OutputPanel(self._project)
        self._content_splitter.addWidget(self._output_panel)

        # Set initial splitter proportions (75% tabs, 25% output)
        self._content_splitter.setSizes([500, 180])

        self._main_splitter.addWidget(self._content_splitter)

        # Set initial sidebar width
        self._main_splitter.setSizes([220, 880])

        # Connect minimap to canvas
        self._minimap.set_canvas(self._mcd_canvas)

        # =====================================================================
        # Status bar
        # =====================================================================
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_label = QLabel("Ready")
        self._status_bar.addWidget(self._status_label, 1)

        # Zoom controls
        round_btn_style = """
            QPushButton {
                border-radius: 10px; border: 1px solid #999;
                background-color: #f0f0f0; color: #333;
                font-weight: bold; font-size: 13px; padding: 0px;
                min-width: 20px; min-height: 20px;
            }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:pressed { background-color: #d0d0d0; }
        """

        self._zoom_out_btn = QPushButton("\u2212")
        self._zoom_out_btn.setFixedSize(20, 20)
        self._zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        self._zoom_out_btn.setStyleSheet(round_btn_style)
        self._zoom_out_btn.clicked.connect(self._on_zoom_out)
        self._status_bar.addPermanentWidget(self._zoom_out_btn)

        self._zoom_slider = QSlider(Qt.Horizontal)
        self._zoom_slider.setFixedWidth(120)
        self._zoom_slider.setMinimum(25)
        self._zoom_slider.setMaximum(400)
        self._zoom_slider.setValue(100)
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
            QPushButton { border: 1px solid #999; border-radius: 3px;
                background-color: #f0f0f0; color: #333; padding: 2px 6px; }
            QPushButton:hover { background-color: #e0e0e0; }
            QPushButton:pressed { background-color: #d0d0d0; }
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

        import_msd_action = QAction("&Import MSD...", self)
        import_msd_action.triggered.connect(self._on_import_msd)
        file_menu.addAction(import_msd_action)

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

        mcd_action = QAction("&MCD Diagram", self)
        mcd_action.setShortcut("Ctrl+1")
        mcd_action.triggered.connect(lambda: self._tabs.setCurrentIndex(0))
        view_menu.addAction(mcd_action)

        mld_action = QAction("M&LD", self)
        mld_action.setShortcut("Ctrl+2")
        mld_action.triggered.connect(lambda: self._tabs.setCurrentIndex(1))
        view_menu.addAction(mld_action)

        view_menu.addSeparator()

        self._toggle_sidebar_action = QAction("Toggle &Sidebar", self)
        self._toggle_sidebar_action.setShortcut("Ctrl+B")
        self._toggle_sidebar_action.triggered.connect(self._toggle_sidebar)
        view_menu.addAction(self._toggle_sidebar_action)

        self._toggle_output_action = QAction("Toggle &Output Panel", self)
        self._toggle_output_action.setShortcut("Ctrl+J")
        self._toggle_output_action.triggered.connect(self._toggle_output)
        view_menu.addAction(self._toggle_output_action)

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

        # Model menu (new)
        model_menu = menubar.addMenu("&Model")

        validate_action = QAction("&Validate", self)
        validate_action.setShortcut("F5")
        validate_action.triggered.connect(self._on_validate)
        model_menu.addAction(validate_action)

        model_menu.addSeparator()

        gen_mld_action = QAction("Generate &MLD", self)
        gen_mld_action.triggered.connect(self._on_generate_mld)
        model_menu.addAction(gen_mld_action)

        gen_sql_action = QAction("Generate &SQL", self)
        gen_sql_action.triggered.connect(self._on_generate_sql)
        model_menu.addAction(gen_sql_action)

        # Options menu
        options_menu = menubar.addMenu("&Options")

        self._show_attributes_action = QAction("Show &Attributes", self)
        self._show_attributes_action.setCheckable(True)
        self._show_attributes_action.setChecked(True)
        self._show_attributes_action.triggered.connect(self._on_toggle_attributes)
        options_menu.addAction(self._show_attributes_action)

        options_menu.addSeparator()

        link_style_menu = options_menu.addMenu("Link Style")

        self._curved_links_action = QAction("&Curved", self)
        self._curved_links_action.setCheckable(True)
        self._curved_links_action.setChecked(True)
        self._curved_links_action.triggered.connect(lambda: self._on_link_style_changed("curved"))
        link_style_menu.addAction(self._curved_links_action)

        self._orthogonal_links_action = QAction("&Orthogonal", self)
        self._orthogonal_links_action.setCheckable(True)
        self._orthogonal_links_action.triggered.connect(lambda: self._on_link_style_changed("orthogonal"))
        link_style_menu.addAction(self._orthogonal_links_action)

        self._straight_links_action = QAction("&Straight", self)
        self._straight_links_action.setCheckable(True)
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

        toolbar.addAction("New").triggered.connect(self._on_new)
        toolbar.addAction("Open").triggered.connect(self._on_open)
        toolbar.addAction("Save").triggered.connect(self._on_save)
        toolbar.addSeparator()
        toolbar.addAction("Add Entity").triggered.connect(self._on_add_entity)
        toolbar.addAction("Add Association").triggered.connect(self._on_add_association)
        toolbar.addAction("Add Link").triggered.connect(self._on_add_link)
        toolbar.addSeparator()
        toolbar.addAction("Validate").triggered.connect(self._on_validate)

    def _connect_signals(self):
        """Connect signals between components."""
        # Canvas signals
        self._mcd_canvas.modified.connect(self._on_modified)
        self._mcd_canvas.zoom_changed.connect(self._on_zoom_changed)
        self._mcd_canvas.selection_changed.connect(self._on_canvas_selection_changed)
        self._mld_view.mld_modified.connect(self._on_modified)
        self._tabs.currentChanged.connect(self._on_tab_changed)

        # Sidebar signals
        self._project_tree.item_selected.connect(self._on_tree_item_selected)
        self._project_tree.item_double_clicked.connect(self._on_tree_item_double_clicked)
        self._project_tree.add_entity_requested.connect(self._on_add_entity)
        self._project_tree.add_association_requested.connect(self._on_add_association)
        self._project_tree.delete_requested.connect(self._on_tree_delete)

        # Properties panel
        self._properties_panel.property_changed.connect(self._on_property_changed)

    # =========================================================================
    # View toggles
    # =========================================================================

    def _toggle_sidebar(self):
        sizes = self._main_splitter.sizes()
        if sizes[0] > 0:
            self._main_splitter.setSizes([0, sum(sizes)])
        else:
            self._main_splitter.setSizes([220, sum(sizes) - 220])

    def _toggle_output(self):
        sizes = self._content_splitter.sizes()
        if sizes[1] > 0:
            self._content_splitter.setSizes([sum(sizes), 0])
        else:
            self._content_splitter.setSizes([sum(sizes) - 180, 180])

    # =========================================================================
    # Sidebar handlers
    # =========================================================================

    def _on_tree_item_selected(self, item_type: str, item_id: str):
        """Handle tree selection — show properties and highlight on canvas."""
        self._properties_panel.show_item(item_type, item_id)
        self._mcd_canvas.select_item_by_id(item_type, item_id)

    def _on_tree_item_double_clicked(self, item_type: str, item_id: str):
        """Handle tree double-click — open edit dialog."""
        if item_type == "entity":
            self._mcd_canvas.edit_entity_by_id(item_id)
        elif item_type == "association":
            self._mcd_canvas.edit_association_by_id(item_id)

    def _on_tree_delete(self, item_type: str, item_id: str):
        """Handle tree delete request."""
        if item_type == "entity":
            self._mcd_canvas.delete_entity_by_id(item_id)
        elif item_type == "association":
            self._mcd_canvas.delete_association_by_id(item_id)

    def _on_canvas_selection_changed(self, item_type: str, item_id: str):
        """Handle canvas selection — update tree and properties panel."""
        if item_type and item_id:
            self._properties_panel.show_item(item_type, item_id)
            self._project_tree.select_item(item_type, item_id)
        else:
            self._properties_panel.clear_selection()

    def _on_property_changed(self):
        """Handle property edit from sidebar."""
        self._mcd_canvas.refresh()
        self._on_modified()

    # =========================================================================
    # Model menu handlers
    # =========================================================================

    def _on_generate_mld(self):
        self._mld_view.generate_mld()
        self._tabs.setCurrentIndex(1)

    def _on_generate_sql(self):
        self._output_panel.refresh_sql()
        self._output_panel.setCurrentIndex(2)  # SQL tab in output

    # =========================================================================
    # Original handlers (preserved from v1.3.1)
    # =========================================================================

    def _update_title(self):
        title = f"{APP_NAME} {APP_VERSION}"
        title += f" - {self._project.name}"
        if self._project.modified:
            title += " *"
        self.setWindowTitle(title)
        self._update_path_status()

    def _update_path_status(self):
        if self._project.file_path:
            self._status_label.setText(f"File: {self._project.file_path}")
        else:
            self._status_label.setText("New project (not saved)")

    def _update_status(self, message: str):
        self._status_label.setText(message)

    def _on_modified(self):
        self._project.modified = True
        self._update_title()
        self._output_panel.refresh_dictionary()
        self._project_tree.refresh()
        self._minimap.refresh()

    def _on_tab_changed(self, index: int):
        if index == 1:  # MLD tab
            self._mld_view.generate_mld()

    def _set_project(self, project: Project):
        """Update all views with a new project."""
        self._project = project
        self._output_panel.set_project(project)
        self._mcd_canvas.set_project(project)
        self._mcd_canvas.apply_colors(project.colors)
        self._mld_view.set_project(project)
        self._project_tree.set_project(project)
        self._properties_panel.set_project(project)
        self._minimap.refresh()
        self._update_title()

    def _check_save(self) -> bool:
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
        return False

    def _on_new(self):
        if not self._check_save():
            return
        self._set_project(Project())
        self._update_status("New project created")

    def _on_open(self):
        if not self._check_save():
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", FILE_FILTER)
        if file_path:
            project = FileIO.load_project(file_path)
            if project:
                self._set_project(project)
                self._update_status(f"Opened: {file_path}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to open project:\n{file_path}")

    def _on_import_msd(self):
        if not self._check_save():
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Import MSD File", "", MSD_FILE_FILTER)
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    source = f.read()
            except OSError:
                QMessageBox.critical(self, "Error", f"Failed to read file:\n{file_path}")
                return

            from ..msd import MSDParser, MSDProjectBuilder
            parser = MSDParser()
            parse_result = parser.parse(source, filename=file_path)
            builder = MSDProjectBuilder()
            project, errors = builder.build(parse_result)

            fatal_errors = [e for e in errors if e.severity == "error"]
            warnings = [e for e in errors if e.severity == "warning"]

            if fatal_errors:
                msg = "Import failed with errors:\n\n"
                msg += "\n".join(f"- {e}" for e in fatal_errors)
                if warnings:
                    msg += "\n\nWarnings:\n"
                    msg += "\n".join(f"- {e}" for e in warnings)
                QMessageBox.critical(self, "Import Error", msg)
                return

            if warnings:
                msg = "Import succeeded with warnings:\n\n"
                msg += "\n".join(f"- {e}" for e in warnings)
                QMessageBox.warning(self, "Import Warnings", msg)

            self._set_project(project)
            self._update_status(f"Imported MSD: {file_path}")
            self._mcd_canvas.zoom_fit()

    def _on_save(self) -> bool:
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
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", FILE_FILTER)
        if file_path:
            if not file_path.endswith(".asip"):
                file_path += ".asip"
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
        file_path, _ = QFileDialog.getSaveFileName(self, "Export as SVG", "", "SVG Files (*.svg)")
        if file_path:
            if not file_path.endswith(".svg"):
                file_path += ".svg"
            if self._mcd_canvas.export_to_svg(file_path):
                self._update_status(f"Exported: {file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export as SVG.")

    def _on_export_png(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export as PNG", "", "PNG Files (*.png)")
        if file_path:
            if not file_path.endswith(".png"):
                file_path += ".png"
            if self._mcd_canvas.export_to_png(file_path):
                self._update_status(f"Exported: {file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export as PNG.")

    def _on_export_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export as PDF", "", "PDF Files (*.pdf)")
        if file_path:
            if not file_path.endswith(".pdf"):
                file_path += ".pdf"
            if self._mcd_canvas.export_to_pdf(file_path):
                self._update_status(f"Exported: {file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export as PDF.")

    def _on_add_entity(self):
        self._tabs.setCurrentIndex(0)
        self._mcd_canvas.add_entity_at_center()

    def _on_add_association(self):
        self._tabs.setCurrentIndex(0)
        self._mcd_canvas.add_association_at_center()

    def _on_add_link(self):
        self._tabs.setCurrentIndex(0)
        self._mcd_canvas.add_link()

    def _on_delete_selected(self):
        self._mcd_canvas.delete_selected()

    def _on_toggle_attributes(self, checked: bool):
        self._mcd_canvas.set_show_attributes(checked)

    def _on_validate(self):
        self._output_panel.run_validation(self._project)

    def _on_project_properties(self):
        from .dialogs.project_properties_dialog import ProjectPropertiesDialog
        dialog = ProjectPropertiesDialog(self._project, parent=self)
        if dialog.exec():
            dialog.apply_to_project()
            self._project.modified = True
            self._update_title()
            self._update_status("Project properties updated")

    def _on_about(self):
        from PySide6.QtWidgets import QSpacerItem, QSizePolicy
        msgbox = QMessageBox(self)
        msgbox.setWindowTitle(f"About {APP_NAME}")
        msgbox.setText(f"<h2>{APP_NAME}</h2><p><b>Version {APP_VERSION}</b></p>")
        msgbox.setInformativeText(
            "<p>A modern MERISE database modeling tool.</p>"
            "<p>Built with Python and PySide6.</p><br>"
            "<p><b>Author:</b> Achraf SOLTANI</p>"
        )
        spacer = QSpacerItem(450, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        layout = msgbox.layout()
        layout.addItem(spacer, layout.rowCount(), 0, 1, layout.columnCount())
        msgbox.exec()

    def _on_link_style_changed(self, style: str):
        self._curved_links_action.setChecked(style == "curved")
        self._orthogonal_links_action.setChecked(style == "orthogonal")
        self._straight_links_action.setChecked(style == "straight")
        self._mcd_canvas.set_link_style(style)

    def _on_diagram_colors(self):
        from .dialogs.color_settings_dialog import ColorSettingsDialog
        dialog = ColorSettingsDialog(self._project, parent=self)
        if dialog.exec():
            dialog.apply_to_project()
            self._mcd_canvas.apply_colors(self._project.colors)
            self._project.modified = True
            self._update_title()
            self._update_status("Diagram colors updated")

    def _on_zoom_in(self):
        self._mcd_canvas.zoom_in()

    def _on_zoom_out(self):
        self._mcd_canvas.zoom_out()

    def _on_zoom_reset(self):
        self._mcd_canvas.zoom_reset()

    def _on_zoom_fit(self):
        self._mcd_canvas.zoom_fit()

    def _on_zoom_changed(self, percentage: int):
        self._zoom_label.setText(f"{percentage}%")
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(percentage)
        self._zoom_slider.blockSignals(False)

    def _on_zoom_slider_changed(self, value: int):
        self._mcd_canvas._apply_zoom(value / 100.0)

    def closeEvent(self, event):
        if self._check_save():
            event.accept()
        else:
            event.ignore()
