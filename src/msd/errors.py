from dataclasses import dataclass, field


@dataclass
class MSDError:
    """Represents a parsing or semantic error in an MSD file."""

    message: str
    line: int = 0
    column: int = 0
    filename: str = ""
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        loc = self.filename or "<string>"
        if self.line:
            loc += f":{self.line}"
        return f"{loc}: {self.severity}: {self.message}"
