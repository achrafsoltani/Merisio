#!/usr/bin/env python3
"""
AnalyseSI Modern - A MERISE database modeling tool.

Entry point for the application.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from src.views.main_window import MainWindow
from src.utils.constants import APP_NAME
from src.utils.theme import get_stylesheet


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("Merisio")
    app.setDesktopFileName("merisio")

    # Set application icon - try theme icon first, fallback to file
    app_icon = QIcon.fromTheme("merisio")
    if app_icon.isNull():
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, "resources", "icons", "app_icon.png")
        app_icon = QIcon(icon_path)

    # Set application style
    app.setStyle("Fusion")
    app.setStyleSheet(get_stylesheet())

    window = MainWindow()
    window.setWindowIcon(app_icon)
    app.setWindowIcon(app_icon)
    window.show()
    window.raise_()
    window.activateWindow()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
