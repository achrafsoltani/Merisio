"""Regression tests for GitHub issue #1: Save As must write a .merisio file.

Before the fix, Save As appended a hard-coded ".asip", so the Open dialog's
"*.merisio" filter hid every project saved for the first time from the GUI.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QFileDialog

from src.models.project import Project
from src.views.main_window import MainWindow


@pytest.fixture(scope="module")
def window():
    app = QApplication.instance() or QApplication([])
    w = MainWindow()
    yield w
    w.close()


@pytest.mark.parametrize("typed, expected", [
    ("demo", "demo.merisio"),
    ("demo.merisio", "demo.merisio"),
    ("Demo.MERISIO", "Demo.MERISIO"),
])
def test_save_as_writes_merisio_extension(window, tmp_path, monkeypatch, typed, expected):
    # Simulate the name the user types in the Save dialog.
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName",
        staticmethod(lambda *args, **kwargs: (str(tmp_path / typed), "")),
    )
    window._set_project(Project())

    assert window._on_save_as()
    assert sorted(os.listdir(tmp_path)) == [expected]
    assert window._project.file_path == str(tmp_path / expected)


def test_save_keeps_the_existing_file_name(window, tmp_path, monkeypatch):
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName",
        staticmethod(lambda *args, **kwargs: (str(tmp_path / "model"), "")),
    )
    window._set_project(Project())
    window._on_save_as()

    window._project.modified = True
    assert window._on_save()
    assert sorted(os.listdir(tmp_path)) == ["model.merisio"]
