# Chapter 10: Testing

The MSD implementation is backed by a comprehensive test suite of 64 tests across four test files. This chapter describes the testing strategy, the test organisation, and notable test patterns.

## 10.1 Test Organisation

| File | Tests | Coverage |
|------|-------|----------|
| `tests/test_msd_lexer.py` | 18 | Tokenisation, comments, keywords, symbols, context sensitivity |
| `tests/test_msd_parser.py` | 22 | Parsing all constructs, error cases, multi-error recovery |
| `tests/test_msd_builder.py` | 19 | Project building, semantic validation, suggestions, round-trip |
| `tests/test_msd_integration.py` | 5 | End-to-end pipeline, `.merisio` round-trip |

Tests are written using **pytest** with class-based grouping. Each test class covers a specific aspect of the module.

## 10.2 Testing Philosophy

The test suite follows three principles:

### Test Each Layer Independently

The lexer tests do not depend on the parser. The parser tests do not depend on the builder. Each layer is tested with its own inputs and expected outputs.

```python
# Lexer test — directly calls tokenize()
def test_all_keywords(self, lexer):
    tokens, errors = lexer.tokenize("project entity association link")
    types = _types(tokens)
    assert types == [TokenType.PROJECT, TokenType.ENTITY,
                     TokenType.ASSOCIATION, TokenType.LINK]

# Parser test — directly calls parse()
def test_single_entity(self, parser):
    result = parser.parse("entity Foo {\n    *id: INT\n}")
    assert not result.has_errors
    assert len(result.entities) == 1

# Builder test — parses then builds
def test_builds_project(self, parser, builder):
    result = parser.parse(SIMPLE_MSD)
    project, errors = builder.build(result)
    assert project is not None
```

### Test Both Success and Failure Paths

For every feature, there are tests for correct input and tests for invalid input:

```python
# Success: valid cardinalities
def test_all_cardinalities(self, parser):
    # ... verifies (0,1), (0,N), (1,1), (1,N) all parse correctly

# Failure: invalid cardinality
def test_invalid_cardinality_min(self, parser):
    result = parser.parse("... link A (5,N) R")
    assert result.has_errors
    assert any("invalid minimum cardinality" in e.message for e in result.errors)
```

### Test the Contract, Not the Implementation

Tests verify observable behaviour, not internal state:

```python
# Good: tests the output
def test_entities_get_positions(self, parser, builder):
    project, _ = builder.build(result)
    positions = [(e.x, e.y) for e in project.get_all_entities()]
    assert not all(x == 0 and y == 0 for x, y in positions)

# Not: assert layout._temperature == 0.1  (testing internals)
```

## 10.3 Lexer Tests

### Token Extraction Helpers

The lexer tests use helper functions to filter out structural tokens:

```python
def _types(tokens):
    """Extract non-NEWLINE, non-EOF token types."""
    return [t.type for t in tokens
            if t.type not in (TokenType.NEWLINE, TokenType.EOF)]

def _values(tokens):
    """Extract non-NEWLINE, non-EOF token values."""
    return [t.value for t in tokens
            if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
```

This lets tests focus on meaningful tokens without being cluttered by structural ones.

### Test Categories

| Category | Tests |
|----------|-------|
| Empty input | Empty string, whitespace only |
| Comments | Hash, double-slash, inline after code |
| Keywords | All four keywords, case insensitivity |
| Symbols | All seven symbol tokens |
| Identifiers | Regular identifiers, underscores, digits |
| Integers | Single and multi-digit |
| Project block | STRING_VALUE capture, comment stripping |
| Line/column | Correct line numbers, correct columns |
| Invalid chars | Single invalid char, multiple invalid chars |
| Full constructs | Entity block, link statement |

### Notable Test: Context-Sensitive Project Values

```python
def test_project_string_value_with_comment(self, lexer):
    source = "project {\n    name: My Project # a comment\n}"
    tokens, errors = lexer.tokenize(source)
    string_vals = [t.value for t in tokens if t.type == TokenType.STRING_VALUE]
    assert string_vals == ["My Project"]
```

This verifies that comments are stripped from project values — a subtle but important behaviour of the context-sensitive lexer.

## 10.4 Parser Tests

### Test Categories

| Category | Tests |
|----------|-------|
| Minimal entity | Single entity, empty entity |
| Composite PKs | Multiple `*` attributes |
| Sized types | VARCHAR(n), DECIMAL(n), CHAR(n), size on unsized type |
| Associations | Empty body, with carrying attributes |
| Links | Simple link, all four cardinalities |
| Metadata | Project block, no project block, unknown property |
| Full file | Complete MSD with all constructs |
| Errors | Missing brace, invalid type, invalid cardinality, unexpected token |
| Multi-error | Multiple errors reported, recovery after error |

### Notable Test: Error Recovery

```python
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
```

This test verifies that the parser continues after an error in entity A and successfully parses entity B. It exercises the panic-mode recovery at the attribute level.

## 10.5 Builder Tests

### Test Categories

| Category | Tests |
|----------|-------|
| Simple build | Project creation, attribute mapping |
| UUIDs | Uniqueness, link reference validity |
| Metadata | Applied correctly, defaults when absent |
| Semantic errors | Unknown entity, unknown association, duplicates, name conflicts |
| Warnings | No primary key |
| "Did you mean?" | Levenshtein function, entity suggestion, association suggestion |
| Round-trip | Save to `.merisio` and reload |
| Auto-layout | Positions assigned, no overlaps |

### Notable Test: "Did You Mean?"

```python
def test_suggestion_for_entity(self, parser, builder):
    source = """entity Tourist { *id: INT }
association R { }
link Tourits (0,N) R"""
    result = parser.parse(source)
    project, errors = builder.build(result)
    fatal = [e for e in errors if e.severity == "error"]
    assert any("did you mean 'Tourist'" in e.message for e in fatal)
```

This verifies the complete suggestion pipeline: Levenshtein distance is computed between "Tourits" and "Tourist" (distance 2, within the threshold of 3), and the suggestion is included in the error message.

### Notable Test: Round-Trip

```python
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
    assert loaded.name == "Tourism System"
```

This test verifies the complete pipeline: MSD text → parse → build → save as JSON → reload → verify. It uses pytest's `tmp_path` fixture for a clean temporary directory.

## 10.6 Integration Tests

### Test Categories

| Test | Description |
|------|-------------|
| Full pipeline | Parse → build → save → load → verify structure |
| Line numbers | Error messages include correct line numbers |
| Comments | Comments do not affect parsing |
| Case-insensitive keywords | ENTITY, Entity, entity all work |
| Case-sensitive identifiers | Foo and foo are different entities |

### The Full Pipeline Test

The most comprehensive test verifies every aspect of the end-to-end flow:

```python
def test_full_pipeline(self, tmp_path):
    parser = MSDParser()
    builder = MSDProjectBuilder()

    result = parser.parse(COMPLETE_MSD, filename="test.msd")
    assert not result.has_errors

    project, errors = builder.build(result)
    fatal = [e for e in errors if e.severity == "error"]
    assert len(fatal) == 0

    # Verify project structure
    assert project.name == "Tourism Management System"
    entities = project.get_all_entities()
    entity_names = {e.name for e in entities}
    assert entity_names == {"Tourist", "Role", "Guide", "Experience"}

    # ... verify associations, links, attributes, cardinalities ...

    # Save and reload
    file_path = str(tmp_path / "output.merisio")
    assert FileIO.save_project(project, file_path) is True

    loaded = FileIO.load_project(file_path)
    assert loaded is not None

    # Verify JSON structure
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["version"] == Project.VERSION
    assert len(data["mcd"]["entities"]) == 4
```

This test is intentionally thorough — it checks:
- Parse result has no errors
- Build produces the correct number of entities, associations, and links
- Metadata is applied correctly
- Attribute details (names, types, PKs) are correct
- Cardinalities are mapped correctly
- The saved JSON has the correct structure
- The reloaded project matches the original

## 10.7 Test Fixtures

### Shared MSD Strings

The builder and integration tests use constant MSD strings defined at module level:

```python
SIMPLE_MSD = """entity Tourist {
    *id: INT
    name: VARCHAR(255)
}
association voyager { }
link Tourist (1,N) voyager
"""

FULL_MSD = """project {
    name: Tourism System
    author: Test Author
    description: A test project
}
entity Tourist { ... }
entity Guide { ... }
association accompagner { date_debut: DATE }
link Tourist (0,N) accompagner
link Guide (1,N) accompagner
"""
```

### Pytest Fixtures

```python
@pytest.fixture
def lexer():
    return MSDLexer()

@pytest.fixture
def parser():
    return MSDParser()

@pytest.fixture
def builder():
    return MSDProjectBuilder()
```

Each test gets a fresh instance, ensuring no state leaks between tests.

## 10.8 Running the Tests

```bash
# Run all MSD tests
python -m pytest tests/test_msd_*.py -v

# Run a specific test file
python -m pytest tests/test_msd_lexer.py -v

# Run a specific test class
python -m pytest tests/test_msd_parser.py::TestErrorCases -v

# Run a specific test
python -m pytest tests/test_msd_builder.py::TestDidYouMean::test_suggestion_for_entity -v

# Run with coverage
python -m pytest tests/test_msd_*.py --cov=src/msd
```

All 64 tests pass in approximately 0.06 seconds.
