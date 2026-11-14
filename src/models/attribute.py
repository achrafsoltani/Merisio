from dataclasses import dataclass, field
from typing import Optional

from ..utils.constants import DATA_TYPES


class InvalidProjectData(ValueError):
    """Raised when a project file holds a value that Merisio cannot accept."""


def _shorten(value, limit: int = 40) -> str:
    """Quote a value from a project file for an error message, cutting it if long."""
    text = repr(value)
    return text if len(text) <= limit else text[:limit - 1] + "…"


@dataclass
class Attribute:
    """Represents a data dictionary attribute."""

    name: str
    data_type: str  # VARCHAR, INT, DATE, etc.
    size: Optional[int] = None
    is_primary_key: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "type": self.data_type,
            "size": self.size,
            "pk": self.is_primary_key
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Attribute":
        """Create an Attribute from a dictionary, validating every field.

        The type and size reach the generated SQL verbatim, so a project file must
        not be able to put anything there but a known type and a positive integer.
        """
        name = data["name"]
        if not isinstance(name, str):
            raise InvalidProjectData(f"an attribute name must be text, not {_shorten(name)}")

        data_type = data["type"]
        if not isinstance(data_type, str) or data_type.upper() not in DATA_TYPES:
            raise InvalidProjectData(
                f"attribute {_shorten(name)} has an unknown data type: {_shorten(data_type)}")

        size = data.get("size")
        if size is not None and (isinstance(size, bool) or not isinstance(size, int) or size < 1):
            raise InvalidProjectData(
                f"attribute {_shorten(name)} has an invalid size: {_shorten(size)}")

        return cls(
            name=name,
            data_type=data_type.upper(),
            size=size,
            is_primary_key=bool(data.get("pk", False))
        )

    def get_sql_type(self) -> str:
        """Get the SQL type declaration."""
        if self.size is not None and self.data_type in ("VARCHAR", "CHAR", "DECIMAL"):
            return f"{self.data_type}({self.size})"
        return self.data_type

    def __str__(self) -> str:
        pk_marker = " [PK]" if self.is_primary_key else ""
        return f"{self.name}: {self.get_sql_type()}{pk_marker}"
