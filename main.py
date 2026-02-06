#!/usr/bin/env python3
"""
Merisio - A MERISE database modeling tool.

Entry point for the GUI application.
"""

import sys
import os

from src.utils.constants import APP_NAME, APP_VERSION


def main():
    """Main entry point."""
    # Handle --help / --version before creating QApplication
    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"Usage: merisio [--help] [--version]")
        print()
        print(f"{APP_NAME} — a modern MERISE database modeling tool.")
        print()
        print("Options:")
        print("  -h, --help     Show this help message and exit")
        print("  -v, --version  Show version and exit")
        print()
        print("When launched without arguments, the graphical editor opens.")
        print(f"See merisio(1) and merisio-cli(1) for full documentation.")
        sys.exit(0)

    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"{APP_NAME} {APP_VERSION}")
        sys.exit(0)

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon

    from src.views.main_window import MainWindow
    from src.utils.theme import get_stylesheet

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
