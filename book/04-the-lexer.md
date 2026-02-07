# Chapter 4: The Lexer

The lexer is the first stage of the MSD pipeline. It transforms raw source text into a stream of **tokens** — the atomic units that the parser consumes.

## 4.1 Architecture Overview

The lexer lives in `src/msd/lexer.py` and consists of three components:

| Component | Description |
|-----------|-------------|
| `TokenType` | Enum of all token types |
| `Token` | Dataclass holding type, value, line, and column |
| `MSDLexer` | The tokeniser class |

The public API is a single method:

```python
lexer = MSDLexer()
tokens, errors = lexer.tokenize(source, filename="schema.msd")
```

It returns a list of `Token` objects and a list of `MSDError` objects for any lexical errors (e.g. unexpected characters).

## 4.2 Token Types

The `TokenType` enum defines 17 token types, organised into four groups:

### Keywords (4)

```python
PROJECT = auto()
ENTITY = auto()
ASSOCIATION = auto()
LINK = auto()
```

These correspond to the four top-level MSD constructs. Keywords are matched case-insensitively: `entity`, `Entity`, and `ENTITY` all produce a `TokenType.ENTITY` token.

### Symbols (7)

```python
LBRACE = auto()    # {
RBRACE = auto()    # }
LPAREN = auto()    # (
RPAREN = auto()    # )
COLON = auto()     # :
COMMA = auto()     # ,
STAR = auto()      # *
```

Single-character punctuation tokens.

### Literals (3)

```python
IDENTIFIER = auto()      # Tourist, id, VARCHAR, etc.
INTEGER = auto()          # 255, 10, 0
STRING_VALUE = auto()     # Rest-of-line in project blocks
```

`STRING_VALUE` is special — it only appears inside `project {}` blocks, capturing everything after a colon to the end of the line (minus comments). This is what makes the lexer **context-sensitive**.

### Structural (2)

```python
NEWLINE = auto()   # End of line marker
EOF = auto()       # End of input
```

`NEWLINE` tokens are emitted after every source line, allowing the parser to be line-aware. `EOF` marks the end of the token stream.

## 4.3 The Keyword Table

Keywords are stored in a dictionary mapping lowercase strings to `TokenType` values:

```python
KEYWORDS = {
    "project": TokenType.PROJECT,
    "entity": TokenType.ENTITY,
    "association": TokenType.ASSOCIATION,
    "link": TokenType.LINK,
}
```

When the lexer encounters an identifier, it looks up `word.lower()` in this table. If found, the token is emitted as the keyword type; otherwise, it is emitted as `IDENTIFIER`.

This design means that keywords are **reserved** — you cannot name an entity `entity` or an association `link`. This is intentional and prevents ambiguity.

## 4.4 Tokenisation Algorithm

The lexer processes input **line by line**, maintaining a column pointer within each line. This line-based approach simplifies comment handling (comments extend to end of line) and makes line/column tracking natural.

### Main Loop

```python
for line_num, line_text in enumerate(lines, start=1):
    col = 0
    while col < length:
        ch = line_text[col]
        # ... match character ...
    tokens.append(Token(TokenType.NEWLINE, "\\n", line_num, length + 1))
```

For each character, the lexer tries to match (in order):

1. **Whitespace** — skip
2. **Comment** (`#` or `//`) — break to next line
3. **Single-character symbol** — emit and advance
4. **Colon** — emit, and if in project block, consume rest of line
5. **Digit** — consume integer literal
6. **Letter or underscore** — consume identifier or keyword
7. **Anything else** — emit error

### Comment Handling

Comments are handled by simply breaking out of the inner `while` loop:

```python
if ch == "#":
    break
if ch == "/" and col + 1 < length and line_text[col + 1] == "/":
    break
```

Everything from the comment character to the end of the line is ignored. After the loop, a `NEWLINE` token is still emitted, so the parser sees the line boundary.

### Integer Literals

Integers are consumed greedily:

```python
if ch.isdigit():
    start = col
    while col < length and line_text[col].isdigit():
        col += 1
    tokens.append(Token(TokenType.INTEGER, line_text[start:col], line_num, start + 1))
```

MSD only needs integers for type sizes (`VARCHAR(255)`) and cardinalities (`0`, `1`), so there is no need for floating-point or negative numbers.

### Identifier and Keyword Recognition

Identifiers start with a letter or underscore and continue with alphanumeric characters or underscores:

```python
if ch.isalpha() or ch == "_":
    start = col
    while col < length and (line_text[col].isalnum() or line_text[col] == "_"):
        col += 1
    word = line_text[start:col]

    keyword_type = KEYWORDS.get(word.lower())
    if keyword_type:
        tokens.append(Token(keyword_type, word, line_num, start + 1))
        if keyword_type == TokenType.PROJECT:
            in_project_block = True
    else:
        tokens.append(Token(TokenType.IDENTIFIER, word, line_num, start + 1))
```

Note the `in_project_block = True` flag set when the `project` keyword is encountered. This activates context-sensitive behaviour for the colon token.

## 4.5 Context-Sensitive Tokenisation

The most interesting part of the lexer is its handling of the colon (`:`) inside `project {}` blocks. Outside these blocks, a colon is simply the `COLON` token. Inside, it triggers **rest-of-line capture**:

```python
if ch == ":":
    tokens.append(Token(TokenType.COLON, ":", line_num, col + 1))
    col += 1

    if in_project_block:
        rest = line_text[col:].strip()
        # Strip trailing comment
        for comment_start in ("#", "//"):
            idx = rest.find(comment_start)
            if idx >= 0:
                rest = rest[:idx].rstrip()
        if rest:
            tokens.append(Token(TokenType.STRING_VALUE, rest, line_num, col + 1))
        break  # consumed rest of line
    continue
```

This means that inside a project block:

```msd
project {
    name: Tourism Management System   # comment
}
```

The tokens are: `PROJECT`, `LBRACE`, `IDENTIFIER("name")`, `COLON`, `STRING_VALUE("Tourism Management System")`, `RBRACE`.

The comment is stripped from the value. The rest of the line is consumed as a single `STRING_VALUE` token — no quoting is needed for spaces.

### Tracking Block Context

The lexer tracks whether it is inside a project block using two variables:

- `in_project_block: bool` — set to `True` when `project` keyword is seen
- `brace_depth: int` — incremented on `{`, decremented on `}`

When `brace_depth` returns to 0, `in_project_block` is reset to `False`. This correctly handles nested scenarios (though MSD does not define nested blocks, the lexer handles them gracefully).

## 4.6 Error Handling

The lexer handles exactly one type of error: **unexpected characters**. Any character that does not match a known pattern produces an `MSDError`:

```python
errors.append(MSDError(
    message=f"unexpected character: '{ch}'",
    line=line_num,
    column=col + 1,
    filename=filename,
))
col += 1
```

The character is skipped and tokenisation continues. This means a single pass can report multiple lexical errors.

The lexer does **not** validate:
- Whether keywords are used correctly (that is the parser's job)
- Whether identifiers are valid type names (also the parser's job)
- Whether braces are balanced (the parser will catch this)

## 4.7 Line and Column Tracking

Every token records its **line number** (1-based) and **column number** (1-based). These are used throughout the pipeline for error messages:

```
schema.msd:5:12: error: unknown data type: 'BLOB'
```

The lexer computes columns as `col + 1` because the internal `col` variable is 0-based, but error messages use 1-based columns for consistency with text editors.

## 4.8 Output Format

The lexer always terminates the token stream with:

1. A `NEWLINE` token after every source line (including the last)
2. An `EOF` token at the very end

This guarantees the parser can always safely peek ahead without bounds-checking.

### Example

For the input:

```msd
entity Foo {
    *id: INT
}
```

The token stream is:

```
ENTITY("entity", 1:1)
IDENTIFIER("Foo", 1:8)
LBRACE("{", 1:12)
NEWLINE("\n", 1:13)
STAR("*", 2:5)
IDENTIFIER("id", 2:6)
COLON(":", 2:8)
IDENTIFIER("INT", 2:10)
NEWLINE("\n", 2:13)
RBRACE("}", 3:1)
NEWLINE("\n", 3:2)
EOF("", 3:0)
```

## 4.9 Design Decisions

### Why Line-by-Line?

Processing line by line (rather than character by character over the entire input) has three benefits:

1. **Natural comment handling** — breaking out of the inner loop discards the rest of the line
2. **Automatic NEWLINE emission** — one `NEWLINE` per line, no counting needed
3. **Context-sensitive colon** — consuming "rest of line" is trivial when you have the line text

### Why Not Use Regular Expressions?

The lexer uses manual character matching rather than regex. This is a deliberate choice:

- MSD's lexical grammar is simple enough that regex adds complexity without benefit
- The context-sensitive colon cannot be handled by a single regex
- Manual matching gives precise control over column tracking
- Performance is irrelevant for files of this size

### Why Emit NEWLINE Tokens?

Newlines are semantically insignificant in MSD — they are not required between attributes or after links. However, emitting them as tokens lets the parser use `_skip_newlines()` to handle optional line breaks uniformly, without the lexer needing to decide where newlines matter.
