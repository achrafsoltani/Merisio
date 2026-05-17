"""Tests for ProjectHistory."""

from src.controllers.project_history import ProjectHistory
from src.models.entity import Entity
from src.models.project import Project


def _make_project(name: str = "p") -> Project:
    project = Project()
    project.name = name
    return project


class TestProjectHistory:
    def test_uninitialised_cannot_undo_or_redo(self):
        history = ProjectHistory()
        assert history.can_undo() is False
        assert history.can_redo() is False
        assert history.undo() is None
        assert history.redo() is None

    def test_init_seeds_one_snapshot(self):
        history = ProjectHistory()
        history.init(_make_project("v0"))
        # Single snapshot, sitting at index 0 — nothing to undo to, nothing to redo to.
        assert history.can_undo() is False
        assert history.can_redo() is False

    def test_push_after_init_enables_undo(self):
        history = ProjectHistory()
        project = _make_project("v0")
        history.init(project)
        project.name = "v1"
        history.push(project)
        assert history.can_undo() is True
        assert history.can_redo() is False

    def test_undo_then_redo_round_trips(self):
        history = ProjectHistory()
        project = _make_project("v0")
        history.init(project)
        project.name = "v1"
        history.push(project)
        project.name = "v2"
        history.push(project)

        snap = history.undo()
        assert snap is not None
        assert snap["metadata"]["name"] == "v1"
        assert history.can_undo() is True
        assert history.can_redo() is True

        snap = history.undo()
        assert snap["metadata"]["name"] == "v0"
        assert history.can_undo() is False
        assert history.can_redo() is True

        snap = history.redo()
        assert snap["metadata"]["name"] == "v1"
        snap = history.redo()
        assert snap["metadata"]["name"] == "v2"
        assert history.can_redo() is False

    def test_push_after_undo_discards_redo_tail(self):
        history = ProjectHistory()
        project = _make_project("v0")
        history.init(project)
        project.name = "v1"
        history.push(project)
        project.name = "v2"
        history.push(project)
        history.undo()  # back to v1
        # Pushing a fresh state should discard the v2 redo branch.
        project.name = "v1b"
        history.push(project)
        assert history.can_redo() is False
        assert history.undo()["metadata"]["name"] == "v1"

    def test_max_history_caps_from_oldest(self):
        history = ProjectHistory()
        project = _make_project("v0")
        history.init(project)
        # Push more than MAX_HISTORY entries; the cap should drop oldest.
        for i in range(1, ProjectHistory.MAX_HISTORY + 10):
            project.name = f"v{i}"
            history.push(project)
        assert len(history._stack) == ProjectHistory.MAX_HISTORY
        # Index still points at the latest entry.
        assert history._stack[history._index]["metadata"]["name"] == project.name

    def test_clear_resets(self):
        history = ProjectHistory()
        history.init(_make_project())
        history.push(_make_project("v1"))
        history.clear()
        assert history.can_undo() is False
        assert history.can_redo() is False
        assert history._index == -1

    def test_init_after_modifications_replaces_history(self):
        history = ProjectHistory()
        project = _make_project("v0")
        history.init(project)
        project.name = "v1"
        history.push(project)
        # Loading a different project should drop the old session's history.
        new_project = _make_project("new")
        history.init(new_project)
        assert history.can_undo() is False
        assert history.can_redo() is False

    def test_snapshot_carries_entity_state(self):
        history = ProjectHistory()
        project = _make_project()
        history.init(project)
        project.add_entity(Entity(name="Customer"))
        history.push(project)
        # Undo: snapshot should describe a project without Customer.
        snap = history.undo()
        assert len(snap["mcd"]["entities"]) == 0
        # Redo: back to the version with Customer.
        snap = history.redo()
        assert len(snap["mcd"]["entities"]) == 1
        assert snap["mcd"]["entities"][0]["name"] == "Customer"
