from ..models.project import Project


class MCDController:
    """Controller for MCD operations."""

    def __init__(self, project: Project):
        self._project = project

    def validate(self) -> list[str]:
        """Validate the MCD model and return list of errors/warnings."""
        errors = []

        # Check for empty dictionary
        if len(self._project.dictionary) == 0:
            errors.append("Dictionary is empty. Add attributes first.")

        # Check entities have at least one primary key
        for entity in self._project.get_all_entities():
            has_pk = False
            for attr_name in entity.attributes:
                attr = self._project.dictionary.get_attribute(attr_name)
                if attr and attr.is_primary_key:
                    has_pk = True
                    break
            if not has_pk:
                errors.append(f"Entity '{entity.name}' has no primary key attribute.")

        # Check associations have at least 2 links
        for assoc in self._project.get_all_associations():
            links = self._project.get_links_for_association(assoc.id)
            if len(links) < 2:
                errors.append(
                    f"Association '{assoc.name}' must be connected to at least 2 entities."
                )

        # Check for orphan entities (no links)
        for entity in self._project.get_all_entities():
            links = self._project.get_links_for_entity(entity.id)
            if len(links) == 0:
                errors.append(f"Entity '{entity.name}' is not connected to any association.")

        return errors

    def get_statistics(self) -> dict:
        """Get statistics about the current model."""
        return {
            "attributes": len(self._project.dictionary),
            "entities": len(self._project.get_all_entities()),
            "associations": len(self._project.get_all_associations()),
            "links": len(self._project.get_all_links())
        }
