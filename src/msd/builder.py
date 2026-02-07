from typing import Dict, List, Optional, Tuple

from ..models.attribute import Attribute
from ..models.entity import Entity
from ..models.association import Association
from ..models.link import Link
from ..models.project import Project
from .errors import MSDError
from .parser import ParseResult, ParsedEntity, ParsedAssociation, ParsedLink
from .layout import auto_layout


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        return _levenshtein(b, a)
    if not b:
        return len(a)

    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]


def _suggest(name: str, candidates: list, max_distance: int = 3) -> Optional[str]:
    """Find the closest match by Levenshtein distance."""
    best = None
    best_dist = max_distance + 1
    for c in candidates:
        d = _levenshtein(name.lower(), c.lower())
        if d < best_dist:
            best_dist = d
            best = c
    return best if best_dist <= max_distance else None


class MSDProjectBuilder:
    """Converts a ParseResult into a Merisio Project."""

    def build(self, parse_result: ParseResult) -> Tuple[Optional[Project], List[MSDError]]:
        """Build a Project from parsed MSD data.

        Returns (project, errors). If there are fatal errors the project may
        still be partially populated.
        """
        errors: List[MSDError] = list(parse_result.errors)
        filename = parse_result.filename

        project = Project()

        # Apply metadata
        if parse_result.metadata:
            m = parse_result.metadata
            if m.name:
                project.name = m.name
            if m.author:
                project.author = m.author
            if m.description:
                project.description = m.description

        # Track names for duplicate detection and reference resolution
        entity_names: Dict[str, Entity] = {}
        assoc_names: Dict[str, Association] = {}

        # Build entities
        for pe in parse_result.entities:
            if pe.name in entity_names:
                errors.append(MSDError(
                    message=f"duplicate entity name: '{pe.name}'",
                    line=pe.line,
                    column=pe.column,
                    filename=filename,
                    severity="error",
                ))
                continue

            entity = Entity(name=pe.name)
            has_pk = False
            for pa in pe.attributes:
                attr = Attribute(
                    name=pa.name,
                    data_type=pa.data_type,
                    size=pa.size,
                    is_primary_key=pa.is_primary_key,
                )
                entity.add_attribute(attr)
                if pa.is_primary_key:
                    has_pk = True

            if not has_pk:
                errors.append(MSDError(
                    message=f"entity '{pe.name}' has no primary key",
                    line=pe.line,
                    column=pe.column,
                    filename=filename,
                    severity="warning",
                ))

            entity_names[pe.name] = entity
            project.add_entity(entity)

        # Build associations
        for pa in parse_result.associations:
            if pa.name in assoc_names:
                errors.append(MSDError(
                    message=f"duplicate association name: '{pa.name}'",
                    line=pa.line,
                    column=pa.column,
                    filename=filename,
                    severity="error",
                ))
                continue

            if pa.name in entity_names:
                errors.append(MSDError(
                    message=f"association name '{pa.name}' conflicts with an entity of the same name",
                    line=pa.line,
                    column=pa.column,
                    filename=filename,
                    severity="error",
                ))
                continue

            assoc = Association(name=pa.name)
            for attr_parsed in pa.attributes:
                attr = Attribute(
                    name=attr_parsed.name,
                    data_type=attr_parsed.data_type,
                    size=attr_parsed.size,
                    is_primary_key=attr_parsed.is_primary_key,
                )
                assoc.add_attribute(attr)

            assoc_names[pa.name] = assoc
            project.add_association(assoc)

        # Build links
        all_entity_names = list(entity_names.keys())
        all_assoc_names = list(assoc_names.keys())

        for pl in parse_result.links:
            entity = entity_names.get(pl.entity_name)
            if entity is None:
                msg = f"unknown entity: '{pl.entity_name}'"
                suggestion = _suggest(pl.entity_name, all_entity_names)
                if suggestion:
                    msg += f" (did you mean '{suggestion}'?)"
                errors.append(MSDError(
                    message=msg,
                    line=pl.line,
                    column=pl.column,
                    filename=filename,
                    severity="error",
                ))
                continue

            assoc = assoc_names.get(pl.association_name)
            if assoc is None:
                msg = f"unknown association: '{pl.association_name}'"
                suggestion = _suggest(pl.association_name, all_assoc_names)
                if suggestion:
                    msg += f" (did you mean '{suggestion}'?)"
                errors.append(MSDError(
                    message=msg,
                    line=pl.line,
                    column=pl.column,
                    filename=filename,
                    severity="error",
                ))
                continue

            link = Link(
                entity_id=entity.id,
                association_id=assoc.id,
                cardinality_min=pl.cardinality_min,
                cardinality_max=pl.cardinality_max,
            )
            project.add_link(link)

        # Auto-layout all elements
        all_entities = project.get_all_entities()
        all_associations = project.get_all_associations()
        all_links = project.get_all_links()

        if all_entities or all_associations:
            # Build a mapping from ID to name for layout edge resolution
            id_to_name = {}
            for e in all_entities:
                id_to_name[e.id] = e.name
            for a in all_associations:
                id_to_name[a.id] = a.name

            # Create lightweight link proxies with name-based references for layout
            class _LayoutLink:
                def __init__(self, entity_name, association_name):
                    self.entity_name = entity_name
                    self.association_name = association_name

            layout_links = []
            for lnk in all_links:
                en = id_to_name.get(lnk.entity_id, "")
                an = id_to_name.get(lnk.association_id, "")
                layout_links.append(_LayoutLink(en, an))

            auto_layout(all_entities, all_associations, layout_links)

        project.modified = False
        return project, errors
