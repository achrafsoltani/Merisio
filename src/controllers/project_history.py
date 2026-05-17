"""Snapshot-based undo/redo history for Project state.

Every mutation that flips `project.modified` and reaches `MainWindow._on_modified`
appends a fresh `project.to_dict()` snapshot. Undo and redo walk the index
through the stack and return the snapshot for the caller to restore via
`Project.from_dict` + `_set_project`.

Snapshot-based (rather than command-based) on purpose: covers every kind of
mutation automatically — waypoint drags, label slides, field edits, colour
changes — without per-mutation `Command` classes. Coarser granularity is the
trade-off (each `modified` emission is one undo step), but for typical Merisio
projects (a few dozen items, snapshots ~few KB), memory and rebuild cost are
both negligible.
"""

from typing import Optional

from ..models.project import Project


class ProjectHistory:
    """Bounded stack of project-state snapshots with an undo/redo cursor."""

    # Cap the history to bound memory. At ~few KB per snapshot for typical
    # projects, 100 entries is well under 1 MB even pessimistically.
    MAX_HISTORY = 100

    def __init__(self) -> None:
        self._stack: list[dict] = []
        # Index of the snapshot that represents the CURRENT live state.
        # -1 means uninitialised (no snapshots yet).
        self._index: int = -1

    def init(self, project: Project) -> None:
        """Reset history with `project`'s current state as the only entry.

        Call when opening or creating a project, so the user can't undo past
        the load point into an older session."""
        self._stack = [project.to_dict()]
        self._index = 0

    def clear(self) -> None:
        """Drop all history. `can_undo` / `can_redo` will both return False."""
        self._stack = []
        self._index = -1

    def push(self, project: Project) -> None:
        """Append a new snapshot after the current index, discarding any redo
        tail. Caps to MAX_HISTORY by dropping oldest entries."""
        if self._index < 0:
            self._stack = [project.to_dict()]
            self._index = 0
            return
        # Drop redo tail
        self._stack = self._stack[: self._index + 1]
        self._stack.append(project.to_dict())
        self._index += 1
        # Cap from the bottom (oldest entries)
        if len(self._stack) > self.MAX_HISTORY:
            drop = len(self._stack) - self.MAX_HISTORY
            self._stack = self._stack[drop:]
            self._index -= drop

    def can_undo(self) -> bool:
        return self._index > 0

    def can_redo(self) -> bool:
        return 0 <= self._index < len(self._stack) - 1

    def undo(self) -> Optional[dict]:
        """Step the cursor back one entry and return that snapshot, or None
        if already at the oldest entry."""
        if not self.can_undo():
            return None
        self._index -= 1
        return self._stack[self._index]

    def redo(self) -> Optional[dict]:
        """Step the cursor forward one entry and return that snapshot, or
        None if already at the newest entry."""
        if not self.can_redo():
            return None
        self._index += 1
        return self._stack[self._index]
