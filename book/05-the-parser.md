# Chapter 5: The Parser

The parser is the second stage of the MSD pipeline. It consumes the token stream produced by the lexer and builds an **intermediate representation** — a set of dataclasses that capture the structure of the MSD file without yet creating Merisio model objects.

## 5.1 Architecture Overview

The parser lives in `src/msd/parser.py` and consists of:

| Component | Description |
|-----------|-------------|
| `ParsedAttribute` | Intermediate attribute representation |
| `ParsedEntity` | Intermediate entity representation |
| `ParsedAssociation` | Intermediate association representation |
| `ParsedLink` | Intermediate link representation |
| `ParsedMetadata` | Project metadata |
| `ParseResult` | Container for all parsed data + errors |
| `MSDParser` | The recursive descent parser |
| `_ParsePanic` | Internal exception for error recovery |

### Why an Intermediate Representation?

The parser does not create `Entity`, `Association`, or `Link` objects directly. Instead, it produces `Parsed*` dataclasses. This separation has several benefits:

1. **No UUID generation** — the parser does not need to generate UUIDs or resolve references
2. **No dependency on Merisio models** — the parser only depends on the lexer and errors module
3. **Clean error recovery** — partially parsed entities can be discarded without leaving orphaned model objects
4. **Testability** — parser tests can inspect the intermediate representation without involving the full model

## 5.2 The Intermediate Dataclasses

### ParsedAttribute

```python
@dataclass
class ParsedAttribute:
    name: str
    data_type: str
    size: Optional[int] = None
    is_primary_key: bool = False
    line: int = 0
    column: int = 0
```

Captures an attribute declaration. The `data_type` is stored in its canonical uppercase form (normalised during parsing). The `line` and `column` are preserved for error reporting in the builder.

### ParsedEntity and ParsedAssociation

```python
@dataclass
class ParsedEntity:
    name: str
    attributes: List[ParsedAttribute] = field(default_factory=list)
    line: int = 0
    column: int = 0
```

Both follow the same pattern: a name, a list of attributes, and source location. They are identical in structure but separate classes for type safety.

### ParsedLink

```python
@dataclass
class ParsedLink:
    entity_name: str
    cardinality_min: str = "0"
    cardinality_max: str = "N"
    association_name: str = ""
    line: int = 0
    column: int = 0
```

Links store **names** rather than IDs. The builder will resolve these names to UUIDs later. This means the parser does not need to track entity/association declarations — it just records what the user wrote.

### ParseResult

```python
@dataclass
class ParseResult:
    entities: List[ParsedEntity] = field(default_factory=list)
    associations: List[ParsedAssociation] = field(default_factory=list)
    links: List[ParsedLink] = field(default_factory=list)
    metadata: Optional[ParsedMetadata] = None
    errors: List[MSDError] = field(default_factory=list)
    filename: str = ""

    @property
    def has_errors(self) -> bool:
        return any(e.severity == "error" for e in self.errors)
```

The `ParseResult` collects everything. The `has_errors` property checks whether any errors have severity `"error"` (as opposed to `"warning"`).

## 5.3 The Parsing Algorithm

`MSDParser` is a **recursive descent parser**. Each grammar production has a corresponding `_parse_*` method:

| Method | Parses |
|--------|--------|
| `_parse_top_level()` | Dispatches to the correct construct |
| `_parse_project_block()` | `project { key: value ... }` |
| `_parse_entity_block()` | `entity Name { attrs... }` |
| `_parse_association_block()` | `association Name { attrs... }` |
| `_parse_attribute()` | `[*]name: TYPE[(size)]` |
| `_parse_type_expr()` | `TYPE` or `TYPE(size)` |
| `_parse_link_statement()` | `link Entity (min,max) Assoc` |
| `_parse_cardinality()` | `(min,max)` |

### The Main Loop

```python
def parse(self, source: str, filename: str = "") -> ParseResult:
    lexer = MSDLexer()
    tokens, lex_errors = lexer.tokenize(source, filename)

    self._tokens = tokens
    self._pos = 0
    self._filename = filename
    self._result = ParseResult(filename=filename)
    self._result.errors.extend(lex_errors)

    self._skip_newlines()

    while not self._at_end():
        try:
            self._parse_top_level()
        except _ParsePanic:
            self._recover_to_top_level()

    return self._result
```

The loop repeatedly calls `_parse_top_level()`, which inspects the current token and dispatches to the appropriate handler. If a `_ParsePanic` exception escapes, the recovery mechanism skips tokens until the next viable parsing point.

### Top-Level Dispatch

```python
def _parse_top_level(self):
    self._skip_newlines()
    if self._at_end():
        return

    tok = self._peek()

    if tok.type == TokenType.PROJECT:
        self._parse_project_block()
    elif tok.type == TokenType.ENTITY:
        self._parse_entity_block()
    elif tok.type == TokenType.ASSOCIATION:
        self._parse_association_block()
    elif tok.type == TokenType.LINK:
        self._parse_link_statement()
    else:
        self._error(f"expected 'entity', 'association', 'link', or 'project', "
                    f"got '{tok.value}'", tok)
        raise _ParsePanic()
```

If the current token is not a valid top-level keyword, an error is emitted and panic recovery begins.

## 5.4 Parsing Entity and Association Blocks

Entity and association blocks share the same structure:

```
keyword Name {
    attribute...
    attribute...
}
```

The parsing logic is nearly identical:

```python
def _parse_entity_block(self):
    kw_tok = self._expect(TokenType.ENTITY)
    name_tok = self._expect(TokenType.IDENTIFIER)
    self._skip_newlines()
    self._expect(TokenType.LBRACE)
    self._skip_newlines()

    entity = ParsedEntity(name=name_tok.value,
                          line=name_tok.line,
                          column=name_tok.column)

    while not self._check(TokenType.RBRACE) and not self._at_end():
        self._skip_newlines()
        if self._check(TokenType.RBRACE):
            break
        try:
            attr = self._parse_attribute()
            entity.attributes.append(attr)
        except _ParsePanic:
            self._recover_to_brace_or_keyword()
            if self._check(TokenType.RBRACE):
                break
        self._skip_newlines()

    self._expect(TokenType.RBRACE)
    self._result.entities.append(entity)
```

Key points:

1. **Name location** — the entity's `line` and `column` are set from the name token, not the keyword token, because the name is what the user cares about in error messages.
2. **Attribute-level recovery** — if an attribute fails to parse, the parser recovers within the block (to the next attribute or closing brace) rather than abandoning the entire entity.
3. **Entity is added even if some attributes fail** — this allows downstream stages to report additional errors about the entity.

## 5.5 Parsing Attributes

```python
def _parse_attribute(self) -> ParsedAttribute:
    is_pk = False
    if self._check(TokenType.STAR):
        self._advance()
        is_pk = True

    name_tok = self._expect(TokenType.IDENTIFIER)
    self._expect(TokenType.COLON)

    data_type, size = self._parse_type_expr()

    return ParsedAttribute(
        name=name_tok.value,
        data_type=data_type,
        size=size,
        is_primary_key=is_pk,
        line=name_tok.line,
        column=name_tok.column,
    )
```

The optional `*` prefix is checked first. Then the name, colon, and type expression are consumed.

### Type Expression Parsing

```python
def _parse_type_expr(self) -> Tuple[str, Optional[int]]:
    type_tok = self._expect(TokenType.IDENTIFIER)
    type_name = type_tok.value.upper()

    if type_name not in DATA_TYPES:
        self._error(
            f"unknown data type: '{type_tok.value}' "
            f"(valid types: {', '.join(sorted(DATA_TYPES))})",
            type_tok,
        )
        raise _ParsePanic()

    size = None
    if self._check(TokenType.LPAREN):
        self._advance()
        size_tok = self._expect(TokenType.INTEGER)
        size = int(size_tok.value)
        self._expect(TokenType.RPAREN)

        if type_name not in SIZED_TYPES:
            self._error(
                f"data type '{type_name}' does not accept a size parameter",
                type_tok,
                severity="warning",
            )

    return type_name, size
```

Data type validation happens here, not in the lexer. The type name is normalised to uppercase and checked against the `DATA_TYPES` set. Unknown types produce an error listing all valid types.

The size parameter is optional. If present, it is parsed as `(INTEGER)`. If the type does not accept sizes (e.g. `INT(10)`), a warning is emitted but parsing continues.

## 5.6 Parsing Links and Cardinalities

Links are single-line statements:

```python
def _parse_link_statement(self):
    kw_tok = self._expect(TokenType.LINK)
    entity_tok = self._expect(TokenType.IDENTIFIER)
    card_min, card_max = self._parse_cardinality()
    assoc_tok = self._expect(TokenType.IDENTIFIER)

    link = ParsedLink(
        entity_name=entity_tok.value,
        cardinality_min=card_min,
        cardinality_max=card_max,
        association_name=assoc_tok.value,
        line=kw_tok.line,
        column=kw_tok.column,
    )
    self._result.links.append(link)
```

### Cardinality Parsing

```python
def _parse_cardinality(self) -> Tuple[str, str]:
    self._expect(TokenType.LPAREN)
    min_tok = self._expect(TokenType.INTEGER, TokenType.IDENTIFIER)
    min_val = min_tok.value

    if min_val not in ("0", "1"):
        self._error(
            f"invalid minimum cardinality: '{min_val}' (expected 0 or 1)",
            min_tok,
        )
        raise _ParsePanic()

    self._expect(TokenType.COMMA)
    max_tok = self._expect(TokenType.INTEGER, TokenType.IDENTIFIER)
    max_val = max_tok.value.upper()

    if max_val not in ("1", "N"):
        self._error(
            f"invalid maximum cardinality: '{max_tok.value}' (expected 1 or N)",
            max_tok,
        )
        raise _ParsePanic()

    self._expect(TokenType.RPAREN)
    return min_val, max_val
```

Note that `_expect` accepts multiple token types: `INTEGER` or `IDENTIFIER`. This is because `N` is lexed as an identifier and `0`, `1` are lexed as integers. The cardinality values are validated after tokenisation.

## 5.7 Token Helper Methods

The parser uses a set of helper methods to navigate the token stream:

### `_peek()` and `_advance()`

```python
def _peek(self) -> Token:
    return self._tokens[self._pos]

def _advance(self) -> Token:
    tok = self._tokens[self._pos]
    self._pos += 1
    return tok
```

Standard lookahead-one pattern. `_peek()` returns the current token without consuming it. `_advance()` returns and consumes it.

### `_check()`

```python
def _check(self, *types: TokenType) -> bool:
    return self._peek().type in types
```

Tests the current token's type without consuming it. Accepts multiple types for convenience.

### `_expect()`

```python
def _expect(self, *types: TokenType) -> Token:
    self._skip_newlines()
    tok = self._peek()
    if tok.type in types:
        return self._advance()

    expected = " or ".join(t.name for t in types)
    self._error(f"expected {expected}, got {tok.type.name} ('{tok.value}')", tok)
    raise _ParsePanic()
```

The workhorse method. It skips newlines, checks the current token, and either consumes it or raises a panic. The error message includes both the expected and actual token types.

### `_skip_newlines()`

```python
def _skip_newlines(self):
    while not self._at_end() and self._peek().type == TokenType.NEWLINE:
        self._pos += 1
```

Consumes all consecutive `NEWLINE` tokens. This is called before most parsing operations, making newlines transparent to the grammar.

## 5.8 Error Recovery

MSD uses **panic-mode error recovery**, the simplest and most robust recovery strategy for recursive descent parsers.

### How It Works

1. When the parser encounters an unexpected token, it emits an error and raises `_ParsePanic`.
2. The nearest `try/except _ParsePanic` block catches the exception.
3. A recovery method skips tokens until a **synchronisation point** is found.
4. Parsing resumes from the synchronisation point.

### Two Recovery Strategies

The parser has two recovery methods for different contexts:

**Top-level recovery** (`_recover_to_top_level`):

```python
def _recover_to_top_level(self):
    while not self._at_end():
        tok = self._peek()
        if tok.type in (TokenType.ENTITY, TokenType.ASSOCIATION,
                        TokenType.LINK, TokenType.PROJECT):
            return
        if tok.type == TokenType.RBRACE:
            self._advance()
            return
        self._advance()
```

Skips to the next top-level keyword or past a closing brace. Used when an entire declaration is malformed.

**Attribute-level recovery** (`_recover_to_brace_or_keyword`):

```python
def _recover_to_brace_or_keyword(self):
    while not self._at_end():
        tok = self._peek()
        if tok.type == TokenType.RBRACE:
            return
        if tok.type in (TokenType.ENTITY, TokenType.ASSOCIATION,
                        TokenType.LINK, TokenType.PROJECT):
            return
        if tok.type == TokenType.STAR:
            return
        if tok.type == TokenType.IDENTIFIER and self._pos + 1 < len(self._tokens):
            next_tok = self._tokens[self._pos + 1]
            if next_tok.type == TokenType.COLON:
                return
        self._advance()
```

This is more fine-grained. It also stops at:
- A `*` (next primary key attribute)
- An identifier followed by a colon (next attribute)

This allows recovery within an entity block — if one attribute is malformed, the parser can skip to the next attribute and continue.

### Example: Multiple Error Reporting

```msd
entity A {
    x: BLOB          # Error 1: unknown type
    name: TEXT        # Parsed successfully
}
entity B {
    y: INVALID_TYPE   # Error 2: unknown type
}
```

The parser reports both errors in a single pass:

```
schema.msd:2: error: unknown data type: 'BLOB' (valid types: ...)
schema.msd:5: error: unknown data type: 'INVALID_TYPE' (valid types: ...)
```

Entity A is still created (with just `name: TEXT`), and entity B is created (with no attributes).

## 5.9 The `_ParsePanic` Exception

```python
class _ParsePanic(Exception):
    """Internal exception for panic-mode error recovery."""
    pass
```

This is a private exception class, not exposed in the public API. It is never caught outside the parser — it is purely an internal control flow mechanism.

The underscore prefix and the `pass` body emphasise that this is not a "real" exception — it is a lightweight signal that means "something went wrong, please recover".

## 5.10 Data Type Validation

The parser validates data types against two sets:

```python
DATA_TYPES = {
    "INT", "BIGINT", "SMALLINT",
    "VARCHAR", "CHAR", "TEXT",
    "BOOLEAN",
    "DATE", "TIME", "TIMESTAMP",
    "DECIMAL", "FLOAT", "DOUBLE",
}

SIZED_TYPES = {"VARCHAR", "CHAR", "DECIMAL"}
```

These are defined in the parser module rather than imported from `constants.py`. This keeps the parser self-contained and avoids a dependency on the broader Merisio codebase. The values are identical to those in `constants.py` by design.

## 5.11 Design Decisions

### Why Not Generate Model Objects Directly?

A simpler design would have the parser create `Entity` and `Association` objects directly. However, this would:

1. Require UUID generation during parsing (mixing concerns)
2. Make error recovery harder (partially created model objects would pollute the project)
3. Couple the parser to the Merisio model layer
4. Make it impossible to report semantic errors (like "unknown entity in link") during parsing, since link references need all entities to be parsed first

The intermediate representation keeps each stage focused on a single concern.

### Why Recursive Descent?

MSD's grammar is LL(1) — each construct can be identified by its first token. This makes recursive descent the natural choice:

- Simple to implement (one method per production)
- Easy to maintain (adding a new construct is one new method)
- Natural error messages ("expected X, got Y")
- Straightforward error recovery (try/except at each level)

Parser generators (like ANTLR or PLY) would add a dependency and learning curve for minimal benefit, given the simplicity of the grammar.
