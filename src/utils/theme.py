"""Application theme and styling - Beekeeper Studio Light inspired."""

# Color palette - Light theme inspired by Beekeeper Studio
COLORS = {
    # Primary colors
    "primary": "#2196F3",
    "primary_hover": "#1E88E5",
    "primary_light": "#E3F2FD",

    # Accent (for associations, warnings)
    "accent": "#FF9800",
    "accent_light": "#FFF3E0",

    # Backgrounds
    "bg_main": "#F5F5F5",
    "bg_sidebar": "#EBEBEB",
    "bg_hover": "#E0E0E0",
    "bg_selected": "#D6E4F5",

    # Text
    "text_primary": "#202124",
    "text_secondary": "#5F6368",
    "text_muted": "#9AA0A6",

    # Borders
    "border": "#DADCE0",
    "border_light": "#E8EAED",

    # Status
    "success": "#34A853",
    "error": "#EA4335",
}


def get_stylesheet() -> str:
    """Get the application stylesheet."""
    return f"""
    /* Main Window */
    QMainWindow {{
        background-color: {COLORS['bg_main']};
    }}

    /* Menu Bar */
    QMenuBar {{
        background-color: {COLORS['bg_sidebar']};
        color: {COLORS['text_primary']};
        padding: 2px 0;
        border-bottom: 1px solid {COLORS['border']};
    }}

    QMenuBar::item {{
        background-color: transparent;
        padding: 6px 12px;
    }}

    QMenuBar::item:selected {{
        background-color: {COLORS['bg_hover']};
        border-radius: 4px;
    }}

    /* Menus */
    QMenu {{
        background-color: {COLORS['bg_main']};
        color: {COLORS['text_primary']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 4px;
    }}

    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}

    QMenu::item:selected {{
        background-color: {COLORS['bg_selected']};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {COLORS['border_light']};
        margin: 4px 8px;
    }}

    /* Toolbar */
    QToolBar {{
        background-color: {COLORS['bg_sidebar']};
        border: none;
        border-bottom: 1px solid {COLORS['border']};
        padding: 4px 8px;
        spacing: 2px;
    }}

    QToolBar::separator {{
        width: 1px;
        background-color: {COLORS['border']};
        margin: 4px 8px;
    }}

    QToolButton {{
        background-color: transparent;
        color: {COLORS['text_primary']};
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
    }}

    QToolButton:hover {{
        background-color: {COLORS['bg_hover']};
    }}

    QToolButton:pressed {{
        background-color: {COLORS['bg_selected']};
    }}

    /* Tab Widget */
    QTabWidget::pane {{
        border: 1px solid {COLORS['border']};
        background-color: {COLORS['bg_main']};
        border-radius: 0;
        top: -1px;
    }}

    QTabBar::tab {{
        background-color: {COLORS['bg_sidebar']};
        color: {COLORS['text_secondary']};
        padding: 8px 20px;
        border: 1px solid {COLORS['border']};
        border-bottom: none;
        margin-right: -1px;
    }}

    QTabBar::tab:selected {{
        background-color: {COLORS['bg_main']};
        color: {COLORS['primary']};
        border-bottom: 2px solid {COLORS['primary']};
        margin-bottom: -1px;
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {COLORS['bg_hover']};
    }}

    QTabBar::tab:first {{
        border-top-left-radius: 6px;
    }}

    QTabBar::tab:last {{
        border-top-right-radius: 6px;
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {COLORS['bg_sidebar']};
        color: {COLORS['text_secondary']};
        border-top: 1px solid {COLORS['border']};
        padding: 4px;
    }}

    QStatusBar::item {{
        border: none;
    }}

    /* Push Buttons */
    QPushButton {{
        background-color: {COLORS['primary']};
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 6px;
    }}

    QPushButton:hover {{
        background-color: {COLORS['primary_hover']};
    }}

    QPushButton:pressed {{
        background-color: {COLORS['primary']};
    }}

    QPushButton:disabled {{
        background-color: {COLORS['border']};
        color: {COLORS['text_muted']};
    }}

    /* Line Edit */
    QLineEdit {{
        background-color: {COLORS['bg_main']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px 12px;
        selection-background-color: {COLORS['primary_light']};
        selection-color: {COLORS['text_primary']};
    }}

    QLineEdit:focus {{
        border-color: {COLORS['primary']};
    }}

    /* Text Edit */
    QTextEdit {{
        background-color: {COLORS['bg_main']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px;
        selection-background-color: {COLORS['primary_light']};
    }}

    QTextEdit:focus {{
        border-color: {COLORS['primary']};
    }}

    /* Combo Box */
    QComboBox {{
        background-color: {COLORS['bg_main']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px 12px;
        min-width: 80px;
    }}

    QComboBox:focus {{
        border-color: {COLORS['primary']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    QComboBox::down-arrow {{
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {COLORS['text_secondary']};
        margin-right: 8px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS['bg_main']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        selection-background-color: {COLORS['bg_selected']};
        selection-color: {COLORS['text_primary']};
    }}

    /* Spin Box */
    QSpinBox {{
        background-color: {COLORS['bg_main']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        padding: 8px 12px;
    }}

    QSpinBox:focus {{
        border-color: {COLORS['primary']};
    }}

    /* Check Box */
    QCheckBox {{
        spacing: 8px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {COLORS['border']};
        border-radius: 4px;
        background-color: {COLORS['bg_main']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {COLORS['primary']};
        border-color: {COLORS['primary']};
    }}

    /* Table Widget */
    QTableWidget {{
        background-color: {COLORS['bg_main']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        gridline-color: {COLORS['border_light']};
    }}

    QTableWidget::item {{
        padding: 8px;
    }}

    QTableWidget::item:selected {{
        background-color: {COLORS['bg_selected']};
        color: {COLORS['text_primary']};
    }}

    QHeaderView::section {{
        background-color: {COLORS['bg_sidebar']};
        color: {COLORS['text_secondary']};
        padding: 10px;
        border: none;
        border-bottom: 1px solid {COLORS['border']};
        font-weight: 600;
    }}

    /* Tree Widget */
    QTreeWidget {{
        background-color: {COLORS['bg_main']};
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
    }}

    QTreeWidget::item {{
        padding: 4px;
    }}

    QTreeWidget::item:selected {{
        background-color: {COLORS['bg_selected']};
        color: {COLORS['text_primary']};
    }}

    QTreeWidget::item:hover {{
        background-color: {COLORS['bg_hover']};
    }}

    /* Scroll Bars */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 10px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background-color: {COLORS['border']};
        border-radius: 5px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {COLORS['text_muted']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        height: 10px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {COLORS['border']};
        border-radius: 5px;
        min-width: 30px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {COLORS['text_muted']};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* Labels */
    QLabel {{
        color: {COLORS['text_primary']};
    }}

    /* Group Box */
    QGroupBox {{
        font-weight: 600;
        border: 1px solid {COLORS['border']};
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 8px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: {COLORS['text_secondary']};
    }}

    /* Message Box */
    QMessageBox {{
        background-color: {COLORS['bg_main']};
    }}

    /* Dialog */
    QDialog {{
        background-color: {COLORS['bg_main']};
    }}

    /* Graphics View (MCD Canvas) */
    QGraphicsView {{
        background-color: {COLORS['bg_main']};
        border: 1px solid {COLORS['border']};
    }}

    /* Dialog Button Box */
    QDialogButtonBox QPushButton {{
        min-width: 80px;
    }}
    """
