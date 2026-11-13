"""Tests for MSD parser."""

import pytest
from src.msd.parser import MSDParser


@pytest.fixture
def parser():
    return MSDParser()


class TestMinimalEntity:
    def test_single_entity(self, parser):
        result = parser.parse("entity Foo {\n    *id: INT\n}")
        assert not result.has_errors
        assert len(result.entities) == 1
        assert result.entities[0].name == "Foo"
        assert len(result.entities[0].attributes) == 1
        assert result.entities[0].attributes[0].is_primary_key is True
        assert result.entities[0].attributes[0].data_type == "INT"

    def test_entity_no_attributes(self, parser):
        result = parser.parse("entity Empty {\n}")
        assert not result.has_errors
        assert len(result.entities) == 1
        assert len(result.entities[0].attributes) == 0


class TestCompositeKeys:
    def test_composite_pk(self, parser):
        source = """entity Enrolment {
    *student_id: INT
    *course_id: INT
    grade: DECIMAL(10)
}"""
        result = parser.parse(source)
        assert not result.has_errors
        pks = [a for a in result.entities[0].attributes if a.is_primary_key]
        assert len(pks) == 2
        assert pks[0].name == "student_id"
        assert pks[1].name == "course_id"


class TestSizedTypes:
    def test_varchar_with_size(self, parser):
        result = parser.parse("entity T {\n    name: VARCHAR(100)\n}")
        assert not result.has_errors
        attr = result.entities[0].attributes[0]
        assert attr.data_type == "VARCHAR"
        assert attr.size == 100

    def test_decimal_with_size(self, parser):
        result = parser.parse("entity T {\n    price: DECIMAL(10)\n}")
        assert not result.has_errors
        attr = result.entities[0].attributes[0]
        assert attr.data_type == "DECIMAL"
        assert attr.size == 10

    def test_char_with_size(self, parser):
        result = parser.parse("entity T {\n    code: CHAR(5)\n}")
        assert not result.has_errors
        attr = result.entities[0].attributes[0]
        assert attr.data_type == "CHAR"
        assert attr.size == 5

    def test_unsized_type_with_size_warns(self, parser):
        result = parser.parse("entity T {\n    x: INT(10)\n}")
        warnings = [e for e in result.errors if e.severity == "warning"]
        assert len(warnings) == 1
        assert "does not accept a size parameter" in warnings[0].message


class TestAssociation:
    def test_empty_association(self, parser):
        result = parser.parse("association creer {\n}")
        assert not result.has_errors
        assert len(result.associations) == 1
        assert result.associations[0].name == "creer"
        assert len(result.associations[0].attributes) == 0

    def test_association_with_attributes(self, parser):
        source = """association user_role {
    attribut_porte: TEXT
}"""
        result = parser.parse(source)
        assert not result.has_errors
        assert len(result.associations[0].attributes) == 1
        assert result.associations[0].attributes[0].name == "attribut_porte"


class TestLinks:
    def test_simple_link(self, parser):
        source = """entity A { *id: INT }
association R { }
link A (1,N) R"""
        result = parser.parse(source)
        assert not result.has_errors
        assert len(result.links) == 1
        link = result.links[0]
        assert link.entity_name == "A"
        assert link.cardinality_min == "1"
        assert link.cardinality_max == "N"
        assert link.association_name == "R"

    def test_all_cardinalities(self, parser):
        source = """entity A { *id: INT }
entity B { *id: INT }
entity C { *id: INT }
entity D { *id: INT }
association R { }
link A (0,1) R
link B (0,N) R
link C (1,1) R
link D (1,N) R"""
        result = parser.parse(source)
        assert not result.has_errors
        cards = [(l.cardinality_min, l.cardinality_max) for l in result.links]
        assert ("0", "1") in cards
        assert ("0", "N") in cards
        assert ("1", "1") in cards
        assert ("1", "N") in cards


class TestMetadata:
    def test_project_block(self, parser):
        source = """project {
    name: Tourism Management System
    author: Achraf SOLTANI
    description: A tourism platform database model
}"""
        result = parser.parse(source)
        assert not result.has_errors
        assert result.metadata is not None
        assert result.metadata.name == "Tourism Management System"
        assert result.metadata.author == "Achraf SOLTANI"
        assert result.metadata.description == "A tourism platform database model"

    def test_no_project_block(self, parser):
        result = parser.parse("entity A { *id: INT }")
        assert result.metadata is None

    def test_unknown_project_property_warns(self, parser):
        source = "project {\n    foo: bar\n}"
        result = parser.parse(source)
        warnings = [e for e in result.errors if e.severity == "warning"]
        assert len(warnings) == 1
        assert "unknown project property" in warnings[0].message


class TestFullFile:
    def test_complete_msd(self, parser):
        source = """# Tourism Management System

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
        result = parser.parse(source)
        assert not result.has_errors
        assert len(result.entities) == 4
        assert len(result.associations) == 2
        assert len(result.links) == 4
        assert result.metadata.name == "Tourism Management System"


class TestErrorCases:
    def test_missing_brace(self, parser):
        result = parser.parse("entity Foo {\n    *id: INT\n")
        assert result.has_errors

    def test_invalid_data_type(self, parser):
        result = parser.parse("entity Foo {\n    x: BLOB\n}")
        assert result.has_errors
        assert any("unknown data type" in e.message for e in result.errors)

    def test_invalid_cardinality_min(self, parser):
        source = "entity A { *id: INT }\nassociation R { }\nlink A (5,N) R"
        result = parser.parse(source)
        assert result.has_errors
        assert any("invalid minimum cardinality" in e.message for e in result.errors)

    def test_invalid_cardinality_max(self, parser):
        source = "entity A { *id: INT }\nassociation R { }\nlink A (0,M) R"
        result = parser.parse(source)
        assert result.has_errors
        assert any("invalid maximum cardinality" in e.message for e in result.errors)

    def test_unexpected_top_level_token(self, parser):
        result = parser.parse("foobar")
        assert result.has_errors

    def test_case_insensitive_type(self, parser):
        result = parser.parse("entity Foo {\n    x: int\n}")
        assert not result.has_errors
        assert result.entities[0].attributes[0].data_type == "INT"


class TestMultiErrorReporting:
    def test_multiple_errors_reported(self, parser):
        source = """entity A {
    x: BLOB
}
entity B {
    y: INVALID_TYPE
}"""
        result = parser.parse(source)
        type_errors = [e for e in result.errors if "unknown data type" in e.message]
        assert len(type_errors) >= 2

    def test_recovery_after_error(self, parser):
        source = """entity A {
    x: BLOB
}
entity B {
    *id: INT
}"""
        result = parser.parse(source)
        # Should still parse entity B despite error in A
        valid_entities = [e for e in result.entities if e.name == "B"]
        assert len(valid_entities) == 1


class TestKeywordsAsNames:
    """Keywords used as names must parse, not hang."""

    @pytest.mark.parametrize("name", ["link", "Link", "entity", "association", "project", "PROJECT"])
    def test_attribute_named_like_a_keyword(self, parser, name):
        result = parser.parse(f"entity A {{\n    *id: INT\n    {name}: VARCHAR(50)\n}}")
        assert not result.has_errors
        assert [a.name for a in result.entities[0].attributes] == ["id", name]

    def test_primary_key_named_like_a_keyword(self, parser):
        result = parser.parse("entity A {\n    *link: INT\n}")
        assert not result.has_errors
        assert result.entities[0].attributes[0].is_primary_key

    def test_entity_and_association_named_like_keywords(self, parser):
        source = """entity Project {
    *id: INT
}
entity Link {
    *id: INT
}
association Entity {
}
link Project (1,N) Entity
link Link (0,N) Entity"""
        result = parser.parse(source)
        assert not result.has_errors
        assert [e.name for e in result.entities] == ["Project", "Link"]
        assert [a.name for a in result.associations] == ["Entity"]
        assert [(l.entity_name, l.association_name) for l in result.links] == [
            ("Project", "Entity"), ("Link", "Entity")]

    def test_entity_named_project_does_not_alter_the_next_block(self, parser):
        source = "entity Project {\n    *id: INT\n}\nentity B {\n    *id: INT\n    label: TEXT\n}"
        result = parser.parse(source)
        assert not result.has_errors
        assert [a.data_type for a in result.entities[1].attributes] == ["INT", "TEXT"]

    def test_project_block_still_parses(self, parser):
        result = parser.parse("project {\n    name: Shop\n}\nentity A {\n    *id: INT\n}")
        assert not result.has_errors
        assert result.metadata.name == "Shop"


class TestTermination:
    """Every input must terminate, with a bounded number of errors."""

    def test_missing_brace_before_next_entity(self, parser):
        source = "entity A {\n    *id: INT\nentity B {\n    *id: INT\n}"
        result = parser.parse(source)
        assert any("missing '}' to close entity 'A'" in e.message for e in result.errors)
        assert [e.name for e in result.entities] == ["B"]

    def test_missing_brace_before_link(self, parser):
        source = "entity A {\n    *id: INT\nassociation R {\n}\nlink A (1,N) R"
        result = parser.parse(source)
        assert any("missing '}' to close entity 'A'" in e.message for e in result.errors)
        assert len(result.links) == 1

    def test_name_missing_at_end_of_line_does_not_swallow_next_statement(self, parser):
        source = "entity A {\n    *id: INT\n}\nassociation R {\n}\nlink A (1,N)\nentity B {\n    *id: INT\n}"
        result = parser.parse(source)
        assert result.has_errors
        assert [e.name for e in result.entities] == ["A", "B"]

    def test_error_count_is_capped(self, parser):
        from src.msd.parser import MAX_ERRORS
        source = "entity A {\n" + "    x: BLOB\n" * (3 * MAX_ERRORS) + "}"
        result = parser.parse(source)
        assert len(result.errors) == MAX_ERRORS + 1
        assert "too many errors" in result.errors[-1].message

    def test_random_inputs_terminate(self, parser):
        """Short random token soups: a parser that stops making progress would
        hit the error cap, which no input this short can reach legitimately."""
        import random
        vocabulary = [
            "entity", "Entity", "association", "link", "Link", "project", "PROJECT",
            "{", "}", "(", ")", ":", ",", "*", "\n", "\n", "\n",
            "A", "B", "R", "id", "INT", "VARCHAR", "N", "0", "1", "50", "# note",
        ]
        rng = random.Random(7)
        for _ in range(3000):
            source = " ".join(rng.choice(vocabulary) for _ in range(rng.randint(1, 30)))
            result = parser.parse(source)
            assert not any("too many errors" in e.message for e in result.errors), source
