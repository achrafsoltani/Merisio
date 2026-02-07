"""Tests for MSD project builder."""

import json
import pytest
from src.msd.parser import MSDParser
from src.msd.builder import MSDProjectBuilder, _levenshtein


@pytest.fixture
def parser():
    return MSDParser()


@pytest.fixture
def builder():
    return MSDProjectBuilder()


SIMPLE_MSD = """entity Tourist {
    *id: INT
    name: VARCHAR(255)
}

association voyager {
}

link Tourist (1,N) voyager
"""

FULL_MSD = """project {
    name: Tourism System
    author: Test Author
    description: A test project
}

entity Tourist {
    *id: INT
    name: VARCHAR(255)
    email: VARCHAR(255)
}

entity Guide {
    *id: INT
    name: VARCHAR(255)
}

association accompagner {
    date_debut: DATE
}

link Tourist (0,N) accompagner
link Guide (1,N) accompagner
"""


class TestSimpleBuild:
    def test_builds_project(self, parser, builder):
        result = parser.parse(SIMPLE_MSD)
        project, errors = builder.build(result)
        assert project is not None
        assert len(project.get_all_entities()) == 1
        assert len(project.get_all_associations()) == 1
        assert len(project.get_all_links()) == 1

    def test_entity_attributes(self, parser, builder):
        result = parser.parse(SIMPLE_MSD)
        project, _ = builder.build(result)
        entities = project.get_all_entities()
        entity = entities[0]
        assert entity.name == "Tourist"
        assert len(entity.attributes) == 2
        assert entity.attributes[0].name == "id"
        assert entity.attributes[0].is_primary_key is True
        assert entity.attributes[0].data_type == "INT"
        assert entity.attributes[1].name == "name"
        assert entity.attributes[1].data_type == "VARCHAR"
        assert entity.attributes[1].size == 255


class TestUUIDGeneration:
    def test_unique_uuids(self, parser, builder):
        result = parser.parse(FULL_MSD)
        project, _ = builder.build(result)
        ids = set()
        for e in project.get_all_entities():
            assert e.id not in ids
            ids.add(e.id)
        for a in project.get_all_associations():
            assert a.id not in ids
            ids.add(a.id)
        for l in project.get_all_links():
            assert l.id not in ids
            ids.add(l.id)

    def test_links_reference_valid_ids(self, parser, builder):
        result = parser.parse(FULL_MSD)
        project, _ = builder.build(result)
        entity_ids = {e.id for e in project.get_all_entities()}
        assoc_ids = {a.id for a in project.get_all_associations()}
        for link in project.get_all_links():
            assert link.entity_id in entity_ids
            assert link.association_id in assoc_ids


class TestMetadata:
    def test_metadata_applied(self, parser, builder):
        result = parser.parse(FULL_MSD)
        project, _ = builder.build(result)
        assert project.name == "Tourism System"
        assert project.author == "Test Author"
        assert project.description == "A test project"

    def test_default_metadata(self, parser, builder):
        result = parser.parse(SIMPLE_MSD)
        project, _ = builder.build(result)
        assert project.name == "Untitled Project"


class TestSemanticErrors:
    def test_unknown_entity_in_link(self, parser, builder):
        source = """entity A { *id: INT }
association R { }
link Unknown (0,N) R"""
        result = parser.parse(source)
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert len(fatal) >= 1
        assert "unknown entity" in fatal[0].message

    def test_unknown_association_in_link(self, parser, builder):
        source = """entity A { *id: INT }
association R { }
link A (0,N) Unknown"""
        result = parser.parse(source)
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert len(fatal) >= 1
        assert "unknown association" in fatal[0].message

    def test_duplicate_entity_name(self, parser, builder):
        source = """entity A { *id: INT }
entity A { *id: INT }"""
        result = parser.parse(source)
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert any("duplicate entity" in e.message for e in fatal)

    def test_duplicate_association_name(self, parser, builder):
        source = """association R { }
association R { }"""
        result = parser.parse(source)
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert any("duplicate association" in e.message for e in fatal)

    def test_entity_assoc_name_conflict(self, parser, builder):
        source = """entity X { *id: INT }
association X { }"""
        result = parser.parse(source)
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert any("conflicts" in e.message for e in fatal)


class TestWarnings:
    def test_no_primary_key_warning(self, parser, builder):
        source = "entity Foo {\n    name: TEXT\n}"
        result = parser.parse(source)
        project, errors = builder.build(result)
        warnings = [e for e in errors if e.severity == "warning"]
        assert any("no primary key" in w.message for w in warnings)


class TestDidYouMean:
    def test_levenshtein_basic(self):
        assert _levenshtein("kitten", "sitting") == 3
        assert _levenshtein("", "") == 0
        assert _levenshtein("a", "") == 1

    def test_suggestion_for_entity(self, parser, builder):
        source = """entity Tourist { *id: INT }
association R { }
link Tourits (0,N) R"""
        result = parser.parse(source)
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert any("did you mean 'Tourist'" in e.message for e in fatal)

    def test_suggestion_for_association(self, parser, builder):
        source = """entity A { *id: INT }
association accompagner { }
link A (0,N) accopagner"""
        result = parser.parse(source)
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert any("did you mean 'accompagner'" in e.message for e in fatal)


class TestRoundTrip:
    def test_save_and_load(self, parser, builder, tmp_path):
        from src.utils.file_io import FileIO

        result = parser.parse(FULL_MSD)
        project, errors = builder.build(result)
        assert not any(e.severity == "error" for e in errors)

        file_path = str(tmp_path / "test.merisio")
        assert FileIO.save_project(project, file_path) is True

        loaded = FileIO.load_project(file_path)
        assert loaded is not None
        assert len(loaded.get_all_entities()) == len(project.get_all_entities())
        assert len(loaded.get_all_associations()) == len(project.get_all_associations())
        assert len(loaded.get_all_links()) == len(project.get_all_links())
        assert loaded.name == "Tourism System"
        assert loaded.author == "Test Author"


class TestAutoLayout:
    def test_entities_get_positions(self, parser, builder):
        result = parser.parse(FULL_MSD)
        project, _ = builder.build(result)
        entities = project.get_all_entities()
        # All entities should have non-default positions after layout
        positions = [(e.x, e.y) for e in entities]
        # Not all at (0, 0)
        assert not all(x == 0 and y == 0 for x, y in positions)

    def test_no_exact_overlaps(self, parser, builder):
        result = parser.parse(FULL_MSD)
        project, _ = builder.build(result)
        all_items = project.get_all_entities() + project.get_all_associations()
        positions = [(item.x, item.y) for item in all_items]
        # All positions should be unique
        assert len(positions) == len(set(positions))
