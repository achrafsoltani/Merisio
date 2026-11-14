"""Loading project files: crafted values must be rejected, never reach the SQL.

An attribute's "type" or "size" in a .merisio file used to be copied verbatim
into the generated DDL, so a crafted file could inject SQL statements.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.models.attribute import Attribute, InvalidProjectData
from src.utils.file_io import FileIO, ProjectLoadError

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = ROOT / "examples" / "ecommerce.merisio"


def write_example_with(tmp_path, **changes):
    """Copy the bundled example, changing the first entity's second attribute."""
    data = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    data["mcd"]["entities"][0]["attributes"][1].update(changes)
    path = tmp_path / "crafted.merisio"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


class TestAttributeValidation:
    @pytest.mark.parametrize("data_type", [
        "TEXT); DROP TABLE payment; --", "BLOB", "", 42, None,
    ])
    def test_unknown_types_are_rejected(self, data_type):
        with pytest.raises(InvalidProjectData, match="unknown data type"):
            Attribute.from_dict({"name": "x", "type": data_type})

    @pytest.mark.parametrize("size", ["1); GRANT ALL ON t TO PUBLIC; --", "50", 0, -3, 2.5, True])
    def test_invalid_sizes_are_rejected(self, size):
        with pytest.raises(InvalidProjectData, match="invalid size"):
            Attribute.from_dict({"name": "x", "type": "VARCHAR", "size": size})

    def test_type_case_is_normalised(self):
        attr = Attribute.from_dict({"name": "x", "type": "varchar", "size": 20})
        assert attr.data_type == "VARCHAR"
        assert attr.get_sql_type() == "VARCHAR(20)"


class TestReadProject:
    def test_bundled_example_loads(self):
        project = FileIO.read_project(str(EXAMPLE))
        assert len(project.get_all_entities()) == 6

    def test_injected_type_is_rejected_with_its_reason(self, tmp_path):
        path = write_example_with(tmp_path, type="TEXT); DROP TABLE payment; --")
        with pytest.raises(ProjectLoadError, match="unknown data type"):
            FileIO.read_project(str(path))
        assert FileIO.load_project(str(path)) is None

    def test_injected_size_is_rejected_with_its_reason(self, tmp_path):
        path = write_example_with(tmp_path, size="1); GRANT ALL ON customer TO PUBLIC; --")
        with pytest.raises(ProjectLoadError, match="invalid size"):
            FileIO.read_project(str(path))

    def test_invalid_json_is_reported(self, tmp_path):
        path = tmp_path / "broken.merisio"
        path.write_text("{ not json", encoding="utf-8")
        with pytest.raises(ProjectLoadError, match="not valid JSON"):
            FileIO.read_project(str(path))

    def test_cli_refuses_a_crafted_file(self, tmp_path):
        path = write_example_with(tmp_path, type="TEXT); DROP TABLE payment; --")
        result = subprocess.run(
            [sys.executable, str(ROOT / "cli.py"), str(path), "sql"],
            capture_output=True, text=True, cwd=ROOT, timeout=60,
        )
        assert result.returncode == 2
        assert "unknown data type" in result.stderr
        assert "DROP TABLE" not in result.stdout
