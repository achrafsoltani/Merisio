"""Tests for data models."""

import pytest
from src.models.attribute import Attribute
from src.models.entity import Entity
from src.models.association import Association
from src.models.link import Link
from src.models.dictionary import Dictionary
from src.models.project import Project


class TestAttribute:
    """Tests for Attribute model."""

    def test_create_simple_attribute(self):
        attr = Attribute(name="id", data_type="INT", is_primary_key=True)
        assert attr.name == "id"
        assert attr.data_type == "INT"
        assert attr.size is None
        assert attr.is_primary_key is True

    def test_create_varchar_attribute(self):
        attr = Attribute(name="nom", data_type="VARCHAR", size=100)
        assert attr.name == "nom"
        assert attr.get_sql_type() == "VARCHAR(100)"
        assert attr.is_primary_key is False

    def test_to_dict_and_from_dict(self):
        attr = Attribute(name="email", data_type="VARCHAR", size=255, is_primary_key=False)
        data = attr.to_dict()
        restored = Attribute.from_dict(data)
        assert restored.name == attr.name
        assert restored.data_type == attr.data_type
        assert restored.size == attr.size
        assert restored.is_primary_key == attr.is_primary_key


class TestEntity:
    """Tests for Entity model."""

    def test_create_entity(self):
        entity = Entity(name="Client", attributes=["id_client", "nom"])
        assert entity.name == "Client"
        assert len(entity.attributes) == 2
        assert entity.id  # UUID should be generated

    def test_add_remove_attribute(self):
        entity = Entity(name="Produit")
        entity.add_attribute("id_produit")
        entity.add_attribute("libelle")
        assert len(entity.attributes) == 2

        entity.remove_attribute("libelle")
        assert len(entity.attributes) == 1
        assert "id_produit" in entity.attributes

    def test_to_dict_and_from_dict(self):
        entity = Entity(name="Commande", attributes=["id_cmd"], x=100, y=200)
        data = entity.to_dict()
        restored = Entity.from_dict(data)
        assert restored.id == entity.id
        assert restored.name == entity.name
        assert restored.attributes == entity.attributes
        assert restored.x == entity.x
        assert restored.y == entity.y


class TestAssociation:
    """Tests for Association model."""

    def test_create_association(self):
        assoc = Association(name="Passer")
        assert assoc.name == "Passer"
        assert len(assoc.attributes) == 0
        assert assoc.id

    def test_carrying_attributes(self):
        assoc = Association(name="Contenir", attributes=["quantite"])
        assert assoc.has_attributes() is True
        assoc.remove_attribute("quantite")
        assert assoc.has_attributes() is False


class TestLink:
    """Tests for Link model."""

    def test_create_link(self):
        link = Link(
            entity_id="e1",
            association_id="a1",
            cardinality_min="1",
            cardinality_max="N"
        )
        assert link.cardinality == "1,N"
        assert link.is_multiple() is True
        assert link.is_mandatory() is True

    def test_optional_single_link(self):
        link = Link(
            entity_id="e1",
            association_id="a1",
            cardinality_min="0",
            cardinality_max="1"
        )
        assert link.cardinality == "0,1"
        assert link.is_multiple() is False
        assert link.is_mandatory() is False


class TestDictionary:
    """Tests for Dictionary model."""

    def test_add_and_get_attribute(self):
        dictionary = Dictionary()
        attr = Attribute(name="id", data_type="INT", is_primary_key=True)
        assert dictionary.add_attribute(attr) is True
        assert dictionary.get_attribute("id") == attr
        assert len(dictionary) == 1

    def test_duplicate_attribute_rejected(self):
        dictionary = Dictionary()
        attr1 = Attribute(name="id", data_type="INT")
        attr2 = Attribute(name="id", data_type="VARCHAR", size=50)
        assert dictionary.add_attribute(attr1) is True
        assert dictionary.add_attribute(attr2) is False
        assert len(dictionary) == 1

    def test_update_attribute(self):
        dictionary = Dictionary()
        attr = Attribute(name="old_name", data_type="INT")
        dictionary.add_attribute(attr)

        new_attr = Attribute(name="new_name", data_type="VARCHAR", size=100)
        assert dictionary.update_attribute("old_name", new_attr) is True
        assert dictionary.get_attribute("old_name") is None
        assert dictionary.get_attribute("new_name") == new_attr


class TestProject:
    """Tests for Project model."""

    def test_create_empty_project(self):
        project = Project()
        assert len(project.dictionary) == 0
        assert len(project.get_all_entities()) == 0
        assert len(project.get_all_associations()) == 0
        assert len(project.get_all_links()) == 0

    def test_add_entity(self):
        project = Project()
        entity = Entity(name="Client")
        project.add_entity(entity)
        assert len(project.get_all_entities()) == 1
        assert project.get_entity(entity.id) == entity
        assert project.modified is True

    def test_remove_entity_removes_links(self):
        project = Project()

        entity = Entity(name="Client")
        project.add_entity(entity)

        assoc = Association(name="Passer")
        project.add_association(assoc)

        link = Link(entity_id=entity.id, association_id=assoc.id)
        project.add_link(link)

        assert len(project.get_all_links()) == 1

        project.remove_entity(entity.id)
        assert len(project.get_all_entities()) == 0
        assert len(project.get_all_links()) == 0  # Link should be removed too

    def test_serialization(self):
        project = Project()

        # Add attribute
        attr = Attribute(name="id_client", data_type="INT", is_primary_key=True)
        project.dictionary.add_attribute(attr)

        # Add entity
        entity = Entity(name="Client", attributes=["id_client"], x=100, y=100)
        project.add_entity(entity)

        # Add association
        assoc = Association(name="Passer", x=200, y=100)
        project.add_association(assoc)

        # Add link
        link = Link(
            entity_id=entity.id,
            association_id=assoc.id,
            cardinality_min="1",
            cardinality_max="N"
        )
        project.add_link(link)

        # Serialize
        data = project.to_dict()

        # Deserialize
        restored = Project.from_dict(data)

        assert len(restored.dictionary) == 1
        assert len(restored.get_all_entities()) == 1
        assert len(restored.get_all_associations()) == 1
        assert len(restored.get_all_links()) == 1

        restored_entity = restored.get_all_entities()[0]
        assert restored_entity.name == "Client"
        assert restored_entity.id == entity.id
