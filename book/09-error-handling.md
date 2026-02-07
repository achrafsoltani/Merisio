# Chapter 9: Error Handling and Recovery

Robust error handling is one of MSD's design priorities. This chapter covers the error system in detail: how errors are represented, how they flow through the pipeline, and how the parser recovers from syntax errors to report multiple problems in a single pass.

## 9.1 The MSDError Dataclass

All errors and warnings in the MSD pipeline are represented by a single dataclass:

```python
@dataclass
class MSDError:
    message: str
    line: int = 0
    column: int = 0
    filename: str = ""
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        loc = self.filename or "<string>"
        if self.line:
            loc += f":{self.line}"
        return f"{loc}: {self.severity}: {self.message}"
```

### Fields

| Field | Description |
|-------|-------------|
| `message` | Human-readable description of the problem |
| `line` | Source line number (1-based), 0 if unknown |
| `column` | Source column number (1-based), 0 if unknown |
| `filename` | Source filename, empty for string input |
| `severity` | `"error"` (fatal) or `"warning"` (informational) |

### String Representation

The `__str__` method formats errors in the style used by compilers (GCC, Clang, rustc):

```
schema.msd:5: error: unknown data type: 'BLOB'
<string>:3: warning: entity 'Foo' has no primary key
```

When no filename is provided (e.g. when parsing a string in tests), `<string>` is used as the location prefix.

## 9.2 Error Sources

Errors can originate from three stages of the pipeline:

### Lexer Errors

The lexer produces errors for unexpected characters:

```
schema.msd:3: error: unexpected character: '@'
```

These are rare in practice — most MSD files only contain alphanumeric characters and standard punctuation.

### Parser Errors

The parser produces errors for syntax violations:

| Error | Example |
|-------|---------|
| Unknown data type | `unknown data type: 'BLOB' (valid types: ...)` |
| Invalid cardinality | `invalid minimum cardinality: '5' (expected 0 or 1)` |
| Unexpected token | `expected IDENTIFIER, got RBRACE ('}')` |
| Size on unsized type | `data type 'INT' does not accept a size parameter` (warning) |
| Unknown project property | `unknown project property: 'version'` (warning) |

### Builder Errors

The builder produces errors for semantic violations:

| Error | Example |
|-------|---------|
| Duplicate entity | `duplicate entity name: 'Tourist'` |
| Duplicate association | `duplicate association name: 'voyager'` |
| Name conflict | `association name 'Booking' conflicts with an entity of the same name` |
| Unknown entity in link | `unknown entity: 'Tourits' (did you mean 'Tourist'?)` |
| Unknown assoc in link | `unknown association: 'voayger' (did you mean 'voyager'?)` |
| No primary key | `entity 'TempData' has no primary key` (warning) |

## 9.3 Error vs Warning

The distinction between errors and warnings is significant:

**Errors** (severity = `"error"`):
- Indicate a problem that prevents correct model generation
- In the CLI: cause exit code 1 and prevent output file creation
- In the GUI: prevent the import and show a critical dialog
- Links with unknown references are not created

**Warnings** (severity = `"warning"`):
- Indicate a potential issue that does not prevent model generation
- In the CLI: printed to stderr but the output file is still created
- In the GUI: shown in a warning dialog but the import proceeds
- The entity/association is still created

The `ParseResult.has_errors` property checks for fatal errors only:

```python
@property
def has_errors(self) -> bool:
    return any(e.severity == "error" for e in self.errors)
```

## 9.4 Error Flow Through the Pipeline

Errors accumulate as data flows through the pipeline:

```
Lexer
  │ errors: [lexer errors]
  ▼
Parser
  │ errors: [lexer errors] + [parser errors]
  ▼
Builder
  │ errors: [lexer errors] + [parser errors] + [builder errors]
  ▼
CLI/GUI
  │ reports all errors to user
```

Each stage copies the error list from the previous stage and appends its own errors:

- **Lexer** → returns `(tokens, errors)`
- **Parser** → starts with `self._result.errors.extend(lex_errors)`, appends parser errors
- **Builder** → starts with `errors = list(parse_result.errors)`, appends builder errors

The final error list is comprehensive — a single call to `builder.build()` returns all errors from all stages.

## 9.5 Panic-Mode Recovery

The parser's error recovery mechanism is based on the **panic mode** strategy, a well-known technique from compiler construction.

### The Problem

Without error recovery, the parser would stop at the first error:

```msd
entity A {
    x: BLOB       # Error here — parser stops
}
entity B {
    *id: INT      # Never parsed
}
```

With panic-mode recovery, both errors are reported:

```
schema.msd:2: error: unknown data type: 'BLOB'
```

And entity B is still parsed successfully.

### How It Works

1. When the parser encounters an unexpected token, it:
   - Emits an `MSDError`
   - Raises `_ParsePanic` (a lightweight internal exception)

2. The nearest `try/except _ParsePanic` handler catches the exception

3. A **recovery method** skips tokens until a **synchronisation point** is found

4. Parsing resumes from the synchronisation point

### Synchronisation Points

The parser uses two sets of synchronisation points:

**Top-level recovery** — synchronises on:
- Top-level keywords (`entity`, `association`, `link`, `project`)
- Closing braces (`}`)

**Attribute-level recovery** — synchronises on:
- Closing braces (`}`)
- Top-level keywords
- Star (`*`) — the start of a primary key attribute
- Identifier followed by colon — the start of a non-PK attribute

### Recovery Scopes

The parser has `try/except` blocks at two levels:

1. **Top level** (in the main parsing loop):
   ```python
   while not self._at_end():
       try:
           self._parse_top_level()
       except _ParsePanic:
           self._recover_to_top_level()
   ```

2. **Attribute level** (inside entity/association blocks):
   ```python
   while not self._check(TokenType.RBRACE) and not self._at_end():
       try:
           attr = self._parse_attribute()
           entity.attributes.append(attr)
       except _ParsePanic:
           self._recover_to_brace_or_keyword()
           if self._check(TokenType.RBRACE):
               break
   ```

The attribute-level recovery is more fine-grained: if one attribute fails, the parser can continue with the next attribute in the same entity.

### Example: Multi-Error Reporting

```msd
entity A {
    x: BLOB           # Error 1: unknown type
    name: TEXT         # Parsed OK
}
entity B {
    y: INVALID_TYPE    # Error 2: unknown type
    *id: INT           # Parsed OK
}
link Unknown (0,N) R   # Error 3: unknown entity
```

The parser reports all three errors:

```
schema.msd:2: error: unknown data type: 'BLOB' (valid types: ...)
schema.msd:5: error: unknown data type: 'INVALID_TYPE' (valid types: ...)
schema.msd:8: error: unknown entity: 'Unknown'
```

Entity A is created with `name: TEXT` (the valid attribute). Entity B is created with `*id: INT`. The link is not created.

## 9.6 The _ParsePanic Exception

```python
class _ParsePanic(Exception):
    pass
```

This is the simplest possible exception — no message, no payload. It exists solely as a control flow mechanism. Key properties:

- **Private** — the underscore prefix signals it is not part of the public API
- **Never escapes** — it is always caught within the parser
- **Lightweight** — no traceback is useful (the error is already recorded in `_result.errors`)
- **Not an error in itself** — it does not carry error information; the error is recorded before the exception is raised

## 9.7 Error Message Quality

Good error messages are descriptive, actionable, and include context. MSD's error messages follow these principles:

### Include Valid Alternatives

```
unknown data type: 'BLOB' (valid types: BIGINT, BOOLEAN, CHAR, DATE, DECIMAL, DOUBLE, FLOAT, INT, SMALLINT, TEXT, TIME, TIMESTAMP, VARCHAR)
```

The user knows immediately what types are available.

### Include Suggestions

```
unknown entity: 'Tourits' (did you mean 'Tourist'?)
```

Typos are a common source of errors. The Levenshtein-based suggestion system catches most of them.

### Include Context

```
expected IDENTIFIER, got RBRACE ('}')
```

The error includes both the expected token type and the actual token (with its value), helping the user locate the problem.

### Include Source Location

```
schema.msd:5: error: unknown data type: 'BLOB'
```

The filename and line number let the user jump directly to the problem in their editor.

## 9.8 Testing Error Handling

Error handling is extensively tested. The test suite includes:

- **Unknown data types** — verifies the error message and that parsing continues
- **Invalid cardinalities** — verifies both min and max validation
- **Missing braces** — verifies detection and recovery
- **Multi-error reporting** — verifies that multiple errors are found in one pass
- **Recovery after error** — verifies that valid constructs after errors are still parsed
- **Unknown references** — verifies entity/association lookup errors
- **Duplicate names** — verifies duplicate detection
- **"Did you mean?" suggestions** — verifies Levenshtein suggestions appear
- **Line number accuracy** — verifies that errors reference the correct source line

## 9.9 Design Decisions

### Why Not Exceptions for User-Facing Errors?

MSD uses a list of `MSDError` objects rather than raising Python exceptions. This has several benefits:

1. **Multiple errors** — a list can hold many errors; an exception stops at the first one
2. **Warnings** — warnings coexist with errors in the same list
3. **No try/except burden** — callers do not need to wrap every call in try/except
4. **Unified reporting** — all errors from all stages are in one place

### Why Both Errors and Warnings?

Some issues are definitively wrong (unknown type = code will not compile), while others are merely suspicious (no primary key = valid but unusual). Conflating these would force users to either fix all warnings or ignore all warnings. Separate severities let tools decide: the CLI shows both but only fails on errors; the GUI shows warnings in a non-blocking dialog.

### Why Not More Granular Severities?

Some systems use `info`, `hint`, `note`, etc. MSD keeps it simple with just `error` and `warning`. For a DSL of this size, additional granularity would add complexity without benefit.
