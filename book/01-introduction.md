# Chapter 1: Introduction

## 1.1 What Is MSD?

**MSD** (Merisio Schema Definition) is a plain-text domain-specific language for defining MERISE conceptual data models. Instead of dragging entities and associations around a canvas, you write them as structured text:

```msd
entity Tourist {
    *id: INT
    name: VARCHAR(255)
    email: VARCHAR(255)
}

association voyager {
    date_depart: DATE
}

link Tourist (1,N) voyager
```

The MSD toolchain parses this text, validates it, generates UUIDs and automatic layout positions, and produces a standard `.merisio` project file that opens directly in the Merisio GUI.

## 1.2 Why a Text-Based DSL?

Graphical editors are excellent for exploring and visualising a model, but they have limitations:

| Concern | GUI | Text (MSD) |
|---------|-----|------------|
| Version control | Binary/JSON diffs are noisy | Clean, line-by-line diffs |
| Collaboration | Merge conflicts are painful | Standard text merge tools work |
| Automation | Requires scripting the GUI | Pipe through CLI tools |
| Speed | Click-heavy for large models | Type faster than you click |
| Reproducibility | Layout depends on manual placement | Deterministic auto-layout |
| Code review | Impossible to review a diagram diff | Natural in pull requests |

MSD does not replace the GUI — it complements it. You can author a model in MSD, import it into the GUI for visual refinement, then continue editing in either format.

## 1.3 Design Principles

MSD was designed with five principles:

### Explicit Over Implicit

Every primary key is marked with `*`. Every attribute has a data type. There is no guessing:

```msd
entity Invoice {
    *invoice_id: INT        # Explicitly marked as PK
    amount: DECIMAL(10)     # Explicit type with size
    issued_on: DATE         # Explicit type
}
```

Compare this with Mocodo, where the first attribute is implicitly the primary key and types are absent entirely.

### Block-Structured

Every construct uses `name { ... }` blocks. This makes the structure unambiguous, easy to parse, and natural to indent:

```msd
entity Student {
    *id: INT
    name: VARCHAR(100)
}

association enrolled_in {
    year: INT
}
```

### Familiar Syntax

If you have written SQL DDL, JSON, or any C-family language, MSD will feel natural. Braces delimit blocks, colons separate names from types, parentheses contain cardinalities.

### Error-Friendly

The parser is designed to report multiple errors in a single pass. It recovers from syntax errors and continues parsing, so you fix all problems at once rather than one at a time:

```
schema.msd:5: error: unknown data type: 'BLOB'
schema.msd:12: error: unknown entity: 'Tourits' (did you mean 'Tourist'?)
schema.msd:15: warning: entity 'Role' has no primary key
```

### Minimal

MSD has exactly four top-level constructs: `project`, `entity`, `association`, and `link`. There are no imports, no inheritance, no triggers, no stored procedures. It models the MCD layer and nothing more.

## 1.4 The MSD Pipeline

An MSD file passes through four stages to become a Merisio project:

```
 .msd file
     │
     ▼
 ┌─────────┐
 │  Lexer   │  Tokenises source text
 └────┬─────┘
      │ tokens
      ▼
 ┌─────────┐
 │  Parser  │  Builds intermediate AST
 └────┬─────┘
      │ ParseResult
      ▼
 ┌─────────┐
 │ Builder  │  Creates Project + semantic validation
 └────┬─────┘
      │ Project
      ▼
 ┌─────────┐
 │  Layout  │  Positions entities and associations
 └────┬─────┘
      │
      ▼
 .merisio file (JSON)
```

Each stage is a separate module with clear inputs and outputs. Errors can occur at any stage and are collected into a unified error list with source locations.

## 1.5 MSD vs Mocodo

For readers familiar with the Mocodo DSL, here is a direct comparison:

| Feature | Mocodo | MSD |
|---------|--------|-----|
| Primary keys | Implicit (first attribute) | Explicit (`*` prefix) |
| Composite PKs | Not supported | Multiple `*` attributes |
| Data types | None | Mandatory, 13 types |
| Sized types | N/A | `VARCHAR(255)`, `DECIMAL(10)` |
| Syntax | Single-line, comma-separated | Block-structured with braces |
| Comments | None | `#` and `//` |
| Metadata | None | `project {}` block |
| Error messages | Minimal | Line numbers, suggestions |
| Output format | Proprietary | Standard `.merisio` JSON |

## 1.6 File Extension

MSD files use the `.msd` extension:

```
my-database.msd
tourism-system.msd
school-management.msd
```

The extension is registered in Merisio's constants as `MSD_FILE_EXTENSION = ".msd"` and appears in file dialogs as `"MSD Files (*.msd)"`.

## 1.7 What You Will Learn

By the end of this book, you will be able to:

- Write complete MCD models in MSD syntax
- Use the CLI to convert MSD files to Merisio projects
- Import MSD files into the Merisio GUI
- Understand every stage of the MSD processing pipeline
- Extend the DSL with new features if needed
- Write tests for DSL components
