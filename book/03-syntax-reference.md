# Chapter 3: Syntax Reference

This chapter is the complete reference for the MSD language. Every construct, every rule, every edge case.

## 3.1 Lexical Structure

### Character Set

MSD source files are UTF-8 encoded. Identifiers are restricted to ASCII letters, digits, and underscores. Values in `project {}` blocks may contain any UTF-8 characters.

### Whitespace

Spaces and tabs are insignificant except as token separators. Indentation is conventional but not required. The following two forms are equivalent:

```msd
entity Foo{*id:INT name:VARCHAR(100)}
```

```msd
entity Foo {
    *id: INT
    name: VARCHAR(100)
}
```

The indented form is strongly recommended for readability.

### Newlines

Newlines separate statements within blocks. Multiple consecutive newlines and blank lines are ignored.

### Comments

Two comment styles are supported:

```msd
# Hash comments run to end of line
// Slash comments also run to end of line
```

Comments may appear:
- On their own line
- After code on the same line
- Inside blocks

```msd
entity Foo {          # Entity comment
    *id: INT          // Attribute comment
    # Standalone comment inside block
    name: TEXT
}
```

Comments inside `project {}` blocks are stripped from values:

```msd
project {
    name: My Project  # This comment is NOT part of the name
}
```

The value of `name` is `"My Project"`, not `"My Project  # This comment is NOT part of the name"`.

## 3.2 Keywords

MSD has four keywords:

| Keyword | Purpose |
|---------|---------|
| `project` | Declares the metadata block |
| `entity` | Declares an entity |
| `association` | Declares an association |
| `link` | Declares a link with cardinality |

Keywords are **case-insensitive**: `entity`, `Entity`, `ENTITY`, and `eNtItY` are all accepted. Internally they are normalised to lowercase for matching.

All other words (entity names, attribute names, type names) are treated as identifiers.

## 3.3 Identifiers

Identifiers name entities, associations, attributes, and data types. They must:

- Start with a letter (`a-z`, `A-Z`) or underscore (`_`)
- Contain only letters, digits (`0-9`), and underscores
- Not be a keyword (case-insensitive)

**Identifiers are case-sensitive** for names. `Tourist` and `tourist` are different entities. However, data type names are normalised to uppercase (`varchar` becomes `VARCHAR`).

Valid identifiers:
```
Tourist
user_role
id_client
_temp
Course123
```

Invalid identifiers:
```
123abc       (starts with digit)
my-entity    (contains hyphen)
my entity    (contains space)
```

## 3.4 The `project` Block

```
project {
    key: value
    key: value
    ...
}
```

The `project` block is optional. If present, it must appear at most once. It may appear anywhere at the top level, but conventionally it is placed at the beginning of the file.

### Supported Properties

| Property | Description |
|----------|-------------|
| `name` | Project name (displayed in title bar) |
| `author` | Author name |
| `description` | Free-text description |

### Value Syntax

Values are captured as the rest of the line after the colon, with leading whitespace stripped. No quoting is needed, even for values containing spaces:

```msd
project {
    name: Tourism Management System     # Spaces are fine
    description: A database model for managing tourism operations
}
```

Unknown properties produce a warning but do not cause a parse error:

```
schema.msd:3: warning: unknown project property: 'version'
```

## 3.5 Entities

```
entity Name {
    [*]attribute_name: TYPE[(size)]
    [*]attribute_name: TYPE[(size)]
    ...
}
```

### Entity Names

Entity names are identifiers (see Section 3.3). By convention they use PascalCase:

```msd
entity Student { ... }
entity CourseEnrollment { ... }
entity UserAccount { ... }
```

### Attributes

Each attribute occupies one line within the entity block:

```
[*]name: TYPE[(size)]
```

| Component | Required | Description |
|-----------|----------|-------------|
| `*` | No | Primary key marker |
| `name` | Yes | Attribute name (identifier) |
| `:` | Yes | Separator |
| `TYPE` | Yes | Data type (see Section 3.7) |
| `(size)` | No | Size parameter for VARCHAR, CHAR, DECIMAL |

### Primary Keys

The `*` prefix marks an attribute as part of the entity's primary key:

```msd
entity Order {
    *order_id: INT          # Single PK
    order_date: DATE
    total: DECIMAL(10)
}
```

Multiple attributes can be marked to form a composite primary key:

```msd
entity OrderLine {
    *order_id: INT          # Composite PK (part 1)
    *product_id: INT        # Composite PK (part 2)
    quantity: INT
    unit_price: DECIMAL(10)
}
```

Entities without any primary key produce a warning:

```
schema.msd:5: warning: entity 'TempData' has no primary key
```

### Empty Entities

Entities with no attributes are allowed (though unusual):

```msd
entity Placeholder {
}
```

## 3.6 Associations

```
association Name {
    [*]attribute_name: TYPE[(size)]
    ...
}
```

Associations represent relationships between entities. They follow the same syntax as entities, with two differences:

1. Attributes on associations are **carrying attributes** — data that belongs to the relationship itself, not to either participating entity.
2. Empty associations (no carrying attributes) are common and expected.

### With Carrying Attributes

```msd
association enrolled_in {
    enrollment_date: DATE
    grade: DECIMAL(10)
}
```

### Without Carrying Attributes

```msd
association teaches {
}
```

The braces are always required, even when the body is empty.

### Naming Convention

Association names conventionally use snake_case or a verb form:

```msd
association posseder { }
association enrolled_in { }
association user_role { }
```

### Name Uniqueness

An association name must not conflict with any entity name:

```msd
entity Booking { *id: INT }
association Booking { }       # ERROR: conflicts with entity 'Booking'
```

## 3.7 Data Types

MSD supports 13 data types, matching the Merisio data dictionary:

### Unsized Types

These types do not accept a size parameter:

| Type | SQL Equivalent | Description |
|------|---------------|-------------|
| `INT` | `INTEGER` | 32-bit integer |
| `BIGINT` | `BIGINT` | 64-bit integer |
| `SMALLINT` | `SMALLINT` | 16-bit integer |
| `TEXT` | `TEXT` | Unlimited text |
| `BOOLEAN` | `BOOLEAN` | True/false |
| `DATE` | `DATE` | Calendar date |
| `TIME` | `TIME` | Time of day |
| `TIMESTAMP` | `TIMESTAMP` | Date and time |
| `FLOAT` | `REAL` | Single-precision float |
| `DOUBLE` | `DOUBLE PRECISION` | Double-precision float |

### Sized Types

These types accept an optional size parameter in parentheses:

| Type | Syntax | Description |
|------|--------|-------------|
| `VARCHAR` | `VARCHAR(n)` | Variable-length string, max `n` characters |
| `CHAR` | `CHAR(n)` | Fixed-length string, exactly `n` characters |
| `DECIMAL` | `DECIMAL(p)` | Fixed-point number with `p` digits of precision |

If a size is provided on a type that does not accept one, a warning is emitted:

```
schema.msd:3: warning: data type 'INT' does not accept a size parameter
```

### Case Insensitivity

Type names are case-insensitive. All of the following are equivalent:

```msd
name: VARCHAR(100)
name: varchar(100)
name: Varchar(100)
```

They are all normalised to `VARCHAR` internally.

### Unknown Types

Using a type not in the supported list produces an error with suggestions:

```
schema.msd:3: error: unknown data type: 'STRING' (valid types: BIGINT, BOOLEAN, CHAR, DATE, DECIMAL, DOUBLE, FLOAT, INT, SMALLINT, TEXT, TIME, TIMESTAMP, VARCHAR)
```

## 3.8 Links

```
link EntityName (min,max) AssociationName
```

Links connect entities to associations with cardinalities. They are single-line statements (no braces).

### Cardinalities

| min | max | Notation | Meaning |
|-----|-----|----------|---------|
| `0` | `1` | `(0,1)` | Optional, at most one |
| `0` | `N` | `(0,N)` | Optional, any number |
| `1` | `1` | `(1,1)` | Mandatory, exactly one |
| `1` | `N` | `(1,N)` | Mandatory, one or more |

The minimum must be `0` or `1`. The maximum must be `1` or `N` (uppercase).

### Examples

```msd
link Student (0,N) enrolled_in    # A student may be enrolled in many courses
link Course (1,N) enrolled_in     # A course must have at least one student
link Professor (0,1) teaches      # A professor may teach at most one course
link Course (1,1) teaches         # A course is taught by exactly one professor
```

### Reference Resolution

Entity and association names in links must match a previously declared entity or association. Names are matched **case-sensitively**:

```msd
entity Tourist { *id: INT }
association voyager { }

link Tourist (0,N) voyager      # OK
link tourist (0,N) voyager      # ERROR: unknown entity 'tourist'
```

If a name is close to an existing one, the parser suggests a correction:

```
schema.msd:5: error: unknown entity: 'Tourits' (did you mean 'Tourist'?)
```

### Order Independence

Links may reference entities and associations that appear later in the file, because the parser builds the complete model before resolving references:

```msd
link Student (0,N) enrolled_in   # enrolled_in defined below — this is fine

entity Student { *id: INT }
association enrolled_in { }
```

However, placing links after their referenced entities and associations is the conventional style.

## 3.9 File Structure

A typical MSD file follows this structure:

```msd
# Comments / header

project {
    name: ...
    author: ...
    description: ...
}

# Entities
entity ... { ... }
entity ... { ... }

# Associations
association ... { ... }
association ... { ... }

# Links
link ...
link ...
```

This structure is conventional, not required. Entities, associations, links, and the project block may appear in any order, interleaved freely.

## 3.10 Summary of Rules

| Rule | Detail |
|------|--------|
| Keywords | Case-insensitive |
| Identifiers | Case-sensitive |
| Types | Case-insensitive, normalised to uppercase |
| `project {}` | Optional, at most once |
| Entity names | Must be unique |
| Association names | Must be unique, must not conflict with entity names |
| Primary keys | Explicit `*` prefix, supports composite |
| Data types | 13 supported, size for VARCHAR/CHAR/DECIMAL only |
| Cardinalities | `(0,1)`, `(0,N)`, `(1,1)`, `(1,N)` |
| Comments | `#` and `//`, extend to end of line |
| File extension | `.msd` |
