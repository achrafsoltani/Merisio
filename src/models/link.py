from dataclasses import dataclass, field
import uuid


@dataclass
class Link:
    """Represents a link between an entity and an association with cardinality."""

    entity_id: str
    association_id: str
    cardinality_min: str = "0"  # "0" or "1"
    cardinality_max: str = "N"  # "1" or "N"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # User-defined bend points in absolute scene coordinates. Empty = auto-routed.
    waypoints: list[list[float]] = field(default_factory=list)
    # Cardinality label position along the path (0 = entity edge, 1 = association edge).
    card_t: float = 0.2

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "association_id": self.association_id,
            "card_min": self.cardinality_min,
            "card_max": self.cardinality_max,
            "waypoints": self.waypoints,
            "card_t": self.card_t,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Link":
        """Create a Link from a dictionary."""
        return cls(
            id=data["id"],
            entity_id=data["entity_id"],
            association_id=data["association_id"],
            cardinality_min=data.get("card_min", "0"),
            cardinality_max=data.get("card_max", "N"),
            waypoints=data.get("waypoints", []),
            card_t=data.get("card_t", 0.2),
        )

    @property
    def cardinality(self) -> str:
        """Get cardinality as string (e.g., '0,N' or '1,1')."""
        return f"{self.cardinality_min},{self.cardinality_max}"

    def is_multiple(self) -> bool:
        """Check if this is a multiple cardinality (max = N)."""
        return self.cardinality_max == "N"

    def is_mandatory(self) -> bool:
        """Check if this link is mandatory (min = 1)."""
        return self.cardinality_min == "1"

    def __str__(self) -> str:
        return f"Link({self.cardinality})"
