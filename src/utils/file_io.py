import json
from pathlib import Path
from typing import Optional

from ..models.attribute import InvalidProjectData
from ..models.project import Project


class ProjectLoadError(Exception):
    """A project file that cannot be read or is not a valid Merisio project."""


class FileIO:
    """Handles project file save/load operations."""

    @staticmethod
    def save_project(project: Project, file_path: str) -> bool:
        """Save a project to a JSON file."""
        try:
            path = Path(file_path)
            data = project.to_dict()
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            project.file_path = file_path
            project.modified = False
            return True
        except Exception as e:
            print(f"Error saving project: {e}")
            return False

    @staticmethod
    def read_project(file_path: str) -> Project:
        """Load a project from a JSON file, raising ProjectLoadError with the reason."""
        try:
            with open(Path(file_path), 'r', encoding='utf-8') as f:
                data = json.load(f)
        except OSError as e:
            raise ProjectLoadError(f"cannot read the file ({e.strerror})") from e
        except ValueError as e:  # invalid JSON or text encoding
            raise ProjectLoadError("the file is not valid JSON") from e

        try:
            project = Project.from_dict(data)
        except InvalidProjectData as e:
            raise ProjectLoadError(str(e)) from e
        except Exception as e:
            raise ProjectLoadError("the file is not a valid Merisio project") from e

        project.file_path = file_path
        return project

    @staticmethod
    def load_project(file_path: str) -> Optional[Project]:
        """Load a project from a JSON file, or return None if it cannot be loaded."""
        try:
            return FileIO.read_project(file_path)
        except ProjectLoadError as e:
            print(f"Error loading project: {e}")
            return None

    @staticmethod
    def get_recent_files(max_count: int = 10) -> list:
        """Get list of recent files (placeholder for future implementation)."""
        return []
