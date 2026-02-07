# Appendix A: Formal Grammar

This appendix defines the MSD grammar in Extended Backus-Naur Form (EBNF).

## A.1 Notation

| Symbol | Meaning |
|--------|---------|
| `=` | Definition |
| `\|` | Alternative |
| `[ ... ]` | Optional (0 or 1) |
| `{ ... }` | Repetition (0 or more) |
| `( ... )` | Grouping |
| `"..."` | Terminal (literal string) |
| `UPPERCASE` | Token type |
| `lowercase` | Non-terminal |

## A.2 Grammar

```ebnf
(* Top level *)
file            = { top_level_decl } ;
top_level_decl  = project_block
                | entity_block
                | association_block
                | link_statement ;

(* Project metadata *)
project_block   = "project" "{" { project_prop } "}" ;
project_prop    = IDENTIFIER ":" STRING_VALUE ;

(* Entities *)
entity_block    = "entity" IDENTIFIER "{" { attribute } "}" ;

(* Associations *)
assoc_block     = "association" IDENTIFIER "{" { attribute } "}" ;

(* Attributes *)
attribute       = [ "*" ] IDENTIFIER ":" type_expr ;
type_expr       = IDENTIFIER [ "(" INTEGER ")" ] ;

(* Links *)
link_statement  = "link" IDENTIFIER cardinality IDENTIFIER ;
cardinality     = "(" card_min "," card_max ")" ;
card_min        = "0" | "1" ;
card_max        = "1" | "N" ;
```

## A.3 Lexical Rules

```ebnf
(* Whitespace and comments *)
whitespace      = " " | "\t" ;
newline         = "\n" ;
comment         = "#" { any_char }
                | "//" { any_char } ;

(* Identifiers *)
IDENTIFIER      = ( letter | "_" ) { letter | digit | "_" } ;
letter          = "a" .. "z" | "A" .. "Z" ;
digit           = "0" .. "9" ;

(* Integers *)
INTEGER         = digit { digit } ;

(* String values — only inside project blocks *)
STRING_VALUE    = { any_char_except_comment_or_newline } ;

(* Keywords — matched case-insensitively *)
keyword         = "project" | "entity" | "association" | "link" ;
```

## A.4 Semantic Constraints

The following constraints are not expressed in the grammar but are enforced by the parser and builder:

1. The `project` block may appear at most once
2. `type_expr` IDENTIFIER must be one of: `INT`, `BIGINT`, `SMALLINT`, `VARCHAR`, `CHAR`, `TEXT`, `BOOLEAN`, `DATE`, `TIME`, `TIMESTAMP`, `DECIMAL`, `FLOAT`, `DOUBLE`
3. Size parameter `(INTEGER)` is only meaningful for `VARCHAR`, `CHAR`, `DECIMAL`
4. `card_min` must be `"0"` or `"1"`
5. `card_max` must be `"1"` or `"N"`
6. Entity names must be unique
7. Association names must be unique and must not conflict with entity names
8. Entity and association names in link statements must reference declared entities/associations

## A.5 Grammar Properties

The MSD grammar is:

- **LL(1)** — each production can be determined by looking at one token of lookahead
- **Context-free** — with the exception of the `STRING_VALUE` token in `project {}` blocks, which is context-sensitive at the lexical level
- **Unambiguous** — every valid input has exactly one parse tree

The LL(1) property makes the grammar ideal for recursive descent parsing. No backtracking is ever needed.

## A.6 Token Summary

| Token | Pattern | Example |
|-------|---------|---------|
| `PROJECT` | `project` (case-insensitive) | `project`, `PROJECT` |
| `ENTITY` | `entity` (case-insensitive) | `entity`, `Entity` |
| `ASSOCIATION` | `association` (case-insensitive) | `association` |
| `LINK` | `link` (case-insensitive) | `link`, `LINK` |
| `LBRACE` | `{` | `{` |
| `RBRACE` | `}` | `}` |
| `LPAREN` | `(` | `(` |
| `RPAREN` | `)` | `)` |
| `COLON` | `:` | `:` |
| `COMMA` | `,` | `,` |
| `STAR` | `*` | `*` |
| `IDENTIFIER` | `[a-zA-Z_][a-zA-Z0-9_]*` | `Tourist`, `id`, `VARCHAR` |
| `INTEGER` | `[0-9]+` | `255`, `0`, `1` |
| `STRING_VALUE` | Rest of line after `:` in project block | `Tourism System` |
| `NEWLINE` | End of line | (implicit) |
| `EOF` | End of input | (implicit) |
