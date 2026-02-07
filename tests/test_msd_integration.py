"""End-to-end integration tests: MSD string -> Project -> .merisio round-trip."""

import json
import pytest
from src.msd.parser import MSDParser
from src.msd.builder import MSDProjectBuilder
from src.utils.file_io import FileIO
from src.models.project import Project


COMPLETE_MSD = """# Tourism Management System

project {
    name: Tourism Management System
    author: Achraf SOLTANI
    description: Database model for a tourism platform
}

entity Tourist {
    *id: INT
    name: VARCHAR(255)
    email: VARCHAR(255)
    password: TEXT
}

entity Role {
    *id: INT
    name: TEXT
}

entity Guide {
    *id: INT
    name: VARCHAR(255)
}

entity Experience {
    *id: INT
    title: VARCHAR(255)
}

association user_role {
    attribut_porte: TEXT
}

association creer {
}

link Tourist (1,1) user_role
link Role (0,N) user_role
link Guide (0,N) creer
link Experience (1,1) creer
"""


class TestEndToEnd:
    def test_full_pipeline(self, tmp_path):
        """Parse MSD -> build Project -> save .merisio -> load -> verify."""
        parser = MSDParser()
        builder = MSDProjectBuilder()

        # Parse
        result = parser.parse(COMPLETE_MSD, filename="test.msd")
        assert not result.has_errors

        # Build
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert len(fatal) == 0

        # Verify project structure
        assert project.name == "Tourism Management System"
        assert project.author == "Achraf SOLTANI"

        entities = project.get_all_entities()
        entity_names = {e.name for e in entities}
        assert entity_names == {"Tourist", "Role", "Guide", "Experience"}

        associations = project.get_all_associations()
        assoc_names = {a.name for a in associations}
        assert assoc_names == {"user_role", "creer"}

        links = project.get_all_links()
        assert len(links) == 4

        # Verify attributes
        tourist = next(e for e in entities if e.name == "Tourist")
        assert len(tourist.attributes) == 4
        pks = tourist.get_primary_keys()
        assert len(pks) == 1
        assert pks[0].name == "id"

        # Verify carrying attributes
        user_role = next(a for a in associations if a.name == "user_role")
        assert len(user_role.attributes) == 1
        assert user_role.attributes[0].name == "attribut_porte"

        creer = next(a for a in associations if a.name == "creer")
        assert len(creer.attributes) == 0

        # Verify cardinalities
        entity_id_map = {e.id: e.name for e in entities}
        assoc_id_map = {a.id: a.name for a in associations}

        for link in links:
            ename = entity_id_map[link.entity_id]
            aname = assoc_id_map[link.association_id]
            card = (link.cardinality_min, link.cardinality_max)

            if ename == "Tourist" and aname == "user_role":
                assert card == ("1", "1")
            elif ename == "Role" and aname == "user_role":
                assert card == ("0", "N")
            elif ename == "Guide" and aname == "creer":
                assert card == ("0", "N")
            elif ename == "Experience" and aname == "creer":
                assert card == ("1", "1")

        # Save and reload
        file_path = str(tmp_path / "output.merisio")
        assert FileIO.save_project(project, file_path) is True

        loaded = FileIO.load_project(file_path)
        assert loaded is not None
        assert loaded.name == "Tourism Management System"
        assert len(loaded.get_all_entities()) == 4
        assert len(loaded.get_all_associations()) == 2
        assert len(loaded.get_all_links()) == 4

        # Verify JSON structure
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["version"] == Project.VERSION
        assert data["metadata"]["name"] == "Tourism Management System"
        assert len(data["mcd"]["entities"]) == 4
        assert len(data["mcd"]["associations"]) == 2
        assert len(data["mcd"]["links"]) == 4

    def test_error_messages_include_line_numbers(self):
        """Errors should have useful line/column information."""
        parser = MSDParser()
        builder = MSDProjectBuilder()

        source = """entity A {
    *id: INT
}
link Bogus (0,N) Missing
"""
        result = parser.parse(source, filename="bad.msd")
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert len(fatal) >= 1
        # Should reference the line where 'link Bogus' appears
        error_str = str(fatal[0])
        assert "bad.msd" in error_str
        assert "4" in error_str  # line 4

    def test_comments_are_ignored(self):
        """Comments should not affect parsing."""
        parser = MSDParser()
        builder = MSDProjectBuilder()

        source = """# A comment
entity A { // another comment
    *id: INT # PK comment
}
// standalone comment
association R {
}
link A (0,N) R  # link comment
"""
        result = parser.parse(source)
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert len(fatal) == 0
        assert len(project.get_all_entities()) == 1
        assert len(project.get_all_associations()) == 1
        assert len(project.get_all_links()) == 1

    def test_case_insensitive_keywords(self):
        """Keywords should be case-insensitive."""
        parser = MSDParser()
        builder = MSDProjectBuilder()

        source = """ENTITY Foo {
    *id: INT
}
ASSOCIATION Bar {
}
LINK Foo (0,N) Bar
"""
        result = parser.parse(source)
        project, errors = builder.build(result)
        fatal = [e for e in errors if e.severity == "error"]
        assert len(fatal) == 0
        assert len(project.get_all_entities()) == 1

    def test_case_sensitive_identifiers(self):
        """Identifiers (names) should be case-sensitive."""
        parser = MSDParser()
        builder = MSDProjectBuilder()

        source = """entity Foo { *id: INT }
entity foo { *id: INT }
"""
        result = parser.parse(source)
        project, errors = builder.build(result)
        assert len(project.get_all_entities()) == 2
