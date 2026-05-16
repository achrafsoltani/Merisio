from typing import Dict, List, Optional, Tuple
from datetime import datetime
from .entity import Entity
from .association import Association
from .link import Link
from .attribute import Attribute


class Project:
    """Container for an entire AnalyseSI project."""

    VERSION = "2.2"  # Adds Link.waypoints for user-shaped relation paths

    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._associations: Dict[str, Association] = {}
        self._links: Dict[str, Link] = {}
        self.file_path: Optional[str] = None
        self.modified = False

        # Project metadata
        self.name: str = "Untitled Project"
        self.description: str = ""
        self.author: str = ""
        self.created_at: str = datetime.now().isoformat()
        self.modified_at: str = self.created_at

        # MLD customizations: {"TABLE.original_col": "new_col_name"}
        self._mld_column_overrides: Dict[str, str] = {}

        # Diagram colors (defaults)
        self.colors = {
            "entity_fill": "#E3F2FD",
            "entity_border": "#1976D2",
            "association_fill": "#FFF3E0",
            "association_border": "#F57C00",
            "link_color": "#000000",
        }

    # Entity operations
    def add_entity(self, entity: Entity) -> None:
        """Add an entity to the project."""
        self._entities[entity.id] = entity
        self.modified = True

    def remove_entity(self, entity_id: str) -> None:
        """Remove an entity and its associated links."""
        if entity_id in self._entities:
            # Remove all links connected to this entity
            links_to_remove = [
                link_id for link_id, link in self._links.items()
                if link.entity_id == entity_id
            ]
            for link_id in links_to_remove:
                del self._links[link_id]

            del self._entities[entity_id]
            self.modified = True

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        return self._entities.get(entity_id)

    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Get an entity by name."""
        for entity in self._entities.values():
            if entity.name == name:
                return entity
        return None

    def get_all_entities(self) -> List[Entity]:
        """Get all entities."""
        return list(self._entities.values())

    # Association operations
    def add_association(self, association: Association) -> None:
        """Add an association to the project."""
        self._associations[association.id] = association
        self.modified = True

    def remove_association(self, association_id: str) -> None:
        """Remove an association and its associated links."""
        if association_id in self._associations:
            # Remove all links connected to this association
            links_to_remove = [
                link_id for link_id, link in self._links.items()
                if link.association_id == association_id
            ]
            for link_id in links_to_remove:
                del self._links[link_id]

            del self._associations[association_id]
            self.modified = True

    def get_association(self, association_id: str) -> Optional[Association]:
        """Get an association by ID."""
        return self._associations.get(association_id)

    def get_all_associations(self) -> List[Association]:
        """Get all associations."""
        return list(self._associations.values())

    # Link operations
    def add_link(self, link: Link) -> None:
        """Add a link to the project."""
        self._links[link.id] = link
        self.modified = True

    def remove_link(self, link_id: str) -> None:
        """Remove a link."""
        if link_id in self._links:
            del self._links[link_id]
            self.modified = True

    def get_link(self, link_id: str) -> Optional[Link]:
        """Get a link by ID."""
        return self._links.get(link_id)

    def get_all_links(self) -> List[Link]:
        """Get all links."""
        return list(self._links.values())

    def get_links_for_entity(self, entity_id: str) -> List[Link]:
        """Get all links connected to an entity."""
        return [link for link in self._links.values() if link.entity_id == entity_id]

    def get_links_for_association(self, association_id: str) -> List[Link]:
        """Get all links connected to an association."""
        return [link for link in self._links.values() if link.association_id == association_id]

    def get_entities_for_association(self, association_id: str) -> List[Entity]:
        """Get all entities linked to an association."""
        links = self.get_links_for_association(association_id)
        entities = []
        for link in links:
            entity = self.get_entity(link.entity_id)
            if entity:
                entities.append(entity)
        return entities

    # Attribute overview (for dictionary view)
    def get_all_attributes(self) -> List[Tuple[str, Attribute]]:
        """Get all attributes across all entities as (entity_name, attribute) tuples."""
        result = []
        for entity in self._entities.values():
            for attr in entity.attributes:
                result.append((entity.name, attr))
        return result

    # MLD column overrides
    def set_mld_column_name(self, table_name: str, original_name: str, new_name: str) -> None:
        """Set a custom column name for the MLD."""
        key = f"{table_name}.{original_name}"
        if new_name and new_name != original_name:
            self._mld_column_overrides[key] = new_name
        elif key in self._mld_column_overrides:
            del self._mld_column_overrides[key]
        self.modified = True

    def get_mld_column_name(self, table_name: str, original_name: str) -> str:
        """Get the (possibly overridden) column name for the MLD."""
        key = f"{table_name}.{original_name}"
        return self._mld_column_overrides.get(key, original_name)

    def get_all_mld_overrides(self) -> Dict[str, str]:
        """Get all MLD column overrides."""
        return self._mld_column_overrides.copy()

    # Serialization
    def to_dict(self) -> dict:
        """Convert project to dictionary for JSON serialization."""
        self.modified_at = datetime.now().isoformat()
        return {
            "version": self.VERSION,
            "metadata": {
                "name": self.name,
                "description": self.description,
                "author": self.author,
                "created_at": self.created_at,
                "modified_at": self.modified_at
            },
            "mcd": {
                "entities": [e.to_dict() for e in self._entities.values()],
                "associations": [a.to_dict() for a in self._associations.values()],
                "links": [l.to_dict() for l in self._links.values()]
            },
            "mld": {
                "column_overrides": self._mld_column_overrides
            },
            "colors": self.colors
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """Create a Project from a dictionary."""
        project = cls()

        # Load metadata
        metadata = data.get("metadata", {})
        project.name = metadata.get("name", "Untitled Project")
        project.description = metadata.get("description", "")
        project.author = metadata.get("author", "")
        project.created_at = metadata.get("created_at", project.created_at)
        project.modified_at = metadata.get("modified_at", project.modified_at)

        # Load MCD elements
        mcd = data.get("mcd", {})

        for entity_data in mcd.get("entities", []):
            entity = Entity.from_dict(entity_data)
            project._entities[entity.id] = entity

        for assoc_data in mcd.get("associations", []):
            association = Association.from_dict(assoc_data)
            project._associations[association.id] = association

        for link_data in mcd.get("links", []):
            link = Link.from_dict(link_data)
            project._links[link.id] = link

        # Load MLD customizations
        mld = data.get("mld", {})
        project._mld_column_overrides = mld.get("column_overrides", {})

        # Load colors (merge with defaults to handle missing keys)
        saved_colors = data.get("colors", {})
        project.colors.update(saved_colors)

        project.modified = False
        return project

    def clear(self) -> None:
        """Clear all project data."""
        self._entities.clear()
        self._associations.clear()
        self._links.clear()
        self._mld_column_overrides.clear()
        self.file_path = None
        self.modified = False
