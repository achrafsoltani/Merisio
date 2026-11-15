"""Runs the generated DDL on a real PostgreSQL server.

Skipped locally unless MERISIO_TEST_PG holds a connection string and psql is
installed. CI provides both, and there (CI is set) the tests never skip, so a
broken setup fails loudly. Each script runs inside a transaction that is rolled back.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from src.controllers.sql_generator import SQLGenerator
from src.models.association import Association
from src.models.attribute import Attribute
from src.models.entity import Entity
from src.models.link import Link
from src.models.project import Project
from src.utils.constants import DATA_TYPES, SIZED_DATA_TYPES
from src.utils.file_io import FileIO

PG = os.environ.get("MERISIO_TEST_PG")
pytestmark = pytest.mark.skipif(
    not (PG and shutil.which("psql")) and not os.environ.get("CI"),
    reason="set MERISIO_TEST_PG to a PostgreSQL connection string and install psql",
)

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "ecommerce.merisio"


def run_on_postgres(sql: str):
    script = f"BEGIN;\n{sql}\nROLLBACK;\n"
    result = subprocess.run(
        ["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-d", PG, "-f", "-"],
        input=script, capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr


def _link(project, entity, assoc, card_min, card_max):
    project.add_link(Link(entity_id=entity.id, association_id=assoc.id,
                          cardinality_min=card_min, cardinality_max=card_max))


def stress_project() -> Project:
    """Reserved-word names, every data type, and two tables that reference each other."""
    project = Project()
    order = Entity(name="Order", attributes=[
        Attribute(name="id", data_type="INT", is_primary_key=True),
        Attribute(name="select", data_type="TEXT"),
    ])
    user = Entity(name="User", attributes=[
        Attribute(name="user", data_type="BIGINT", is_primary_key=True),
    ] + [
        Attribute(name=f"col_{t.lower()}", data_type=t, size=10 if t in SIZED_DATA_TYPES else None)
        for t in DATA_TYPES
    ])
    group = Entity(name="2fa group", attributes=[
        Attribute(name="id", data_type="INT", is_primary_key=True),
    ])
    for entity in (order, user, group):
        project.add_entity(entity)

    places = Association(name="Places")
    owns = Association(name="Table")          # cycle: user -> order and order -> user
    member = Association(name="Group", attributes=[Attribute(name="since", data_type="DATE")])
    for assoc in (places, owns, member):
        project.add_association(assoc)

    _link(project, order, places, "1", "1")
    _link(project, user, places, "0", "N")
    _link(project, user, owns, "1", "1")
    _link(project, order, owns, "0", "N")
    _link(project, user, member, "0", "N")
    _link(project, group, member, "0", "N")
    return project


def test_bundled_example_runs_on_postgres():
    run_on_postgres(SQLGenerator(FileIO.read_project(str(EXAMPLE))).generate())


def test_reserved_words_types_and_cycles_run_on_postgres():
    run_on_postgres(SQLGenerator(stress_project()).generate())
