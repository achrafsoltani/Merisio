import json
from pathlib import Path
from typing import Optional

from ..models.project import Project


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
    def load_project(file_path: str) -> Optional[Project]:
        """Load a project from a JSON file."""
        try:
            path = Path(file_path)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            project = Project.from_dict(data)
            project.file_path = file_path
            return project
        except Exception as e:
            print(f"Error loading project: {e}")
            return None

    @staticmethod
    def get_recent_files(max_count: int = 10) -> list:
        """Get list of recent files (placeholder for future implementation)."""
        return []
