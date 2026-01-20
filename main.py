#!/usr/bin/env python3
"""
AnalyseSI Modern - A MERISE database modeling tool.

Entry point for the application.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.views.main_window import MainWindow
from src.utils.constants import APP_NAME


def main():
    """Main entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("AnalyseSI")

    # Set application style
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
