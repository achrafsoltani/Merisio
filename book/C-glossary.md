# Appendix C: Glossary

### Association

A relationship between two or more entities in an MCD. In MSD, declared with the `association` keyword. Associations may have carrying attributes. In the GUI, displayed as diamond-shaped nodes.

### AST (Abstract Syntax Tree)

A tree representation of the syntactic structure of source code. MSD uses a flat intermediate representation (dataclasses) rather than a true AST, but the concept is similar.

### Auto-layout

The automatic positioning of entities and associations on the canvas using the Fruchterman-Reingold force-directed algorithm. See Chapter 7.

### Builder

The third stage of the MSD pipeline (`MSDProjectBuilder`). Converts the intermediate `ParseResult` into a Merisio `Project` with UUIDs, resolved references, and auto-layout. See Chapter 6.

### Cardinality

A constraint on a link that specifies the minimum and maximum number of times an entity can participate in an association. MSD supports four cardinalities: `(0,1)`, `(0,N)`, `(1,1)`, `(1,N)`.

### Carrying attribute

An attribute that belongs to an association rather than an entity. Represents data that is a property of the relationship itself.

### Composite primary key

A primary key consisting of two or more attributes. In MSD, each component is marked with `*`.

### Context-sensitive

A property of the MSD lexer whereby the colon (`:`) token behaves differently inside `project {}` blocks (capturing rest-of-line) than outside them (producing a simple COLON token).

### DSL (Domain-Specific Language)

A programming language designed for a specific application domain. MSD is a DSL for MERISE conceptual data modelling.

### Entity

A real-world concept represented in an MCD (e.g. Student, Course, Invoice). In MSD, declared with the `entity` keyword. Each entity has attributes, at least one of which should be a primary key.

### Fruchterman-Reingold

A force-directed graph layout algorithm that models nodes as repelling particles and edges as springs. Used by MSD for auto-layout. See Chapter 7.

### Intermediate representation

The set of `Parsed*` dataclasses (`ParsedEntity`, `ParsedAssociation`, `ParsedLink`, `ParsedMetadata`) that the parser produces and the builder consumes. See Chapter 5.

### Levenshtein distance

A metric measuring the minimum number of single-character edits (insertions, deletions, substitutions) needed to change one string into another. Used by the builder for "did you mean?" suggestions.

### Lexer

The first stage of the MSD pipeline (`MSDLexer`). Transforms source text into a stream of tokens. See Chapter 4.

### Link

A connection between an entity and an association with a cardinality. In MSD, declared with the `link` keyword. Links specify the entity name, cardinality, and association name.

### MCD (Modele Conceptuel de Donnees)

Conceptual Data Model in the MERISE methodology. A diagram showing entities, associations, and the cardinalities between them.

### MERISE

A French systems analysis and design methodology widely used in database modelling. Defines three abstraction levels: conceptual (MCD), logical (MLD), and physical (MPD).

### Merisio

A visual MCD editor with automatic MLD generation and SQL export. The target platform for MSD files.

### `.merisio`

The JSON file format used by Merisio to store projects. Contains entities, associations, links, metadata, MLD customisations, and diagram colours.

### MLD (Modele Logique de Donnees)

Logical Data Model. The relational representation of an MCD, showing tables, columns, primary keys, and foreign keys. Generated automatically by Merisio.

### MSD (Merisio Schema Definition)

The text-based DSL described in this book for defining MERISE conceptual data models. File extension: `.msd`.

### Panic mode

An error recovery strategy used by the MSD parser. When a syntax error is encountered, the parser skips tokens until a synchronisation point (a top-level keyword or closing brace) and then resumes parsing.

### ParseResult

The output of the MSD parser. A dataclass containing lists of parsed entities, associations, and links, optional metadata, accumulated errors, and the source filename.

### Parser

The second stage of the MSD pipeline (`MSDParser`). Consumes tokens from the lexer and produces an intermediate representation. See Chapter 5.

### Primary key (PK)

An attribute (or set of attributes) that uniquely identifies each instance of an entity. In MSD, marked with the `*` prefix.

### Project

A Merisio `Project` object containing all entities, associations, links, metadata, and settings. The output of the MSD builder.

### Recursive descent

A top-down parsing technique where each non-terminal in the grammar has a corresponding parsing function. The MSD parser is a recursive descent parser.

### STRING_VALUE

A special token type emitted by the MSD lexer for values in `project {}` blocks. Captures everything from after the colon to the end of the line (minus comments).

### Synchronisation point

A token at which the parser can safely resume after an error. For MSD, these are top-level keywords (`entity`, `association`, `link`, `project`), closing braces, and attribute starts.

### Token

An atomic unit of the source text produced by the lexer. Each token has a type, value, line number, and column number.

### UUID

Universally Unique Identifier. A 128-bit identifier generated for every entity, association, and link in a Merisio project. MSD's builder generates UUIDs automatically.
