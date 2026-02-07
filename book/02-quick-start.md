# Chapter 2: Quick Start

This chapter walks you through creating your first MSD file, converting it to a Merisio project, and opening it in the GUI.

## 2.1 Your First MSD File

Create a file called `school.msd` with the following content:

```msd
# School Management System

project {
    name: School Management System
    author: Your Name
    description: A simple school database model
}

entity Student {
    *student_id: INT
    first_name: VARCHAR(100)
    last_name: VARCHAR(100)
    date_of_birth: DATE
    email: VARCHAR(255)
}

entity Course {
    *course_id: INT
    title: VARCHAR(200)
    credits: INT
}

entity Professor {
    *professor_id: INT
    name: VARCHAR(200)
    department: VARCHAR(100)
}

association enrolled_in {
    grade: DECIMAL(10)
    enrollment_date: DATE
}

association teaches {
}

link Student (0,N) enrolled_in
link Course (1,N) enrolled_in
link Professor (0,N) teaches
link Course (1,1) teaches
```

Let us break down each section.

### The Project Block

```msd
project {
    name: School Management System
    author: Your Name
    description: A simple school database model
}
```

The `project` block is optional. It sets metadata that appears in the Merisio project properties dialog. The three supported properties are `name`, `author`, and `description`. Values are plain text — everything after the colon to the end of the line (or the start of a comment).

### Entities

```msd
entity Student {
    *student_id: INT
    first_name: VARCHAR(100)
    last_name: VARCHAR(100)
    date_of_birth: DATE
    email: VARCHAR(255)
}
```

Each entity has a name and a block of attributes. Attributes follow the pattern:

```
[*]name: TYPE[(size)]
```

- The `*` prefix marks an attribute as part of the primary key.
- The type is mandatory and must be one of the 13 supported types (see Section 2.5).
- Types that accept a size parameter (`VARCHAR`, `CHAR`, `DECIMAL`) use parentheses.

### Associations

```msd
association enrolled_in {
    grade: DECIMAL(10)
    enrollment_date: DATE
}

association teaches {
}
```

Associations represent relationships between entities. They may have **carrying attributes** (like `grade` and `enrollment_date` on `enrolled_in`) or an empty body (like `teaches`).

### Links

```msd
link Student (0,N) enrolled_in
link Course (1,N) enrolled_in
link Professor (0,N) teaches
link Course (1,1) teaches
```

Links connect entities to associations with cardinalities. The syntax is:

```
link EntityName (min,max) AssociationName
```

The four valid cardinalities are:

| Cardinality | Meaning |
|-------------|---------|
| `(0,1)` | Optional, at most one |
| `(0,N)` | Optional, any number |
| `(1,1)` | Mandatory, exactly one |
| `(1,N)` | Mandatory, one or more |

## 2.2 Converting with the CLI

Open a terminal in the directory containing your `school.msd` file and run:

```bash
merisio-cli school.msd parse
```

This produces `school.merisio` in the same directory. You can specify a different output path:

```bash
merisio-cli school.msd parse -o output/school-project.merisio
```

If there are errors, they are printed to stderr with line numbers:

```
school.msd:8: error: unknown data type: 'STRING'
school.msd:25: error: unknown entity: 'Studnt' (did you mean 'Student'?)
```

If running from source rather than the built binary:

```bash
python cli.py school.msd parse
```

## 2.3 Importing in the GUI

You can also import MSD files directly into the Merisio GUI:

1. Launch Merisio
2. Go to **File > Import MSD...**
3. Select your `.msd` file
4. The model appears on the canvas with automatic layout

The import process:
- Parses the MSD file
- Validates all entities, associations, and links
- Generates UUIDs for all elements
- Runs force-directed auto-layout
- Displays warnings if any (e.g. entities without primary keys)
- Zooms to fit the entire model in the viewport

After importing, you can:
- Rearrange entities manually if the auto-layout is not ideal
- Add or modify attributes through the entity/association dialogs
- Save as a standard `.merisio` file
- Generate MLD and SQL as usual

## 2.4 Comments

MSD supports two comment styles:

```msd
# This is a hash comment

// This is a double-slash comment

entity Foo {
    *id: INT          # Inline comment after an attribute
    name: TEXT        // Another inline comment
}
```

Comments extend to the end of the line. There are no block comments.

## 2.5 Supported Data Types

MSD supports the same 13 data types as the Merisio data dictionary:

| Type | Description | Accepts Size? |
|------|-------------|:-------------:|
| `INT` | Integer | No |
| `BIGINT` | Large integer | No |
| `SMALLINT` | Small integer | No |
| `VARCHAR` | Variable-length string | Yes |
| `CHAR` | Fixed-length string | Yes |
| `TEXT` | Unlimited text | No |
| `BOOLEAN` | True/false | No |
| `DATE` | Calendar date | No |
| `TIME` | Time of day | No |
| `TIMESTAMP` | Date and time | No |
| `DECIMAL` | Fixed-point number | Yes |
| `FLOAT` | Floating-point number | No |
| `DOUBLE` | Double-precision float | No |

Type names are **case-insensitive** in the MSD source — `int`, `Int`, and `INT` are all accepted and normalised to uppercase internally.

## 2.6 Composite Primary Keys

Some entities have composite primary keys — multiple attributes that together form the unique identifier:

```msd
entity Enrollment {
    *student_id: INT
    *course_id: INT
    semester: VARCHAR(20)
    grade: DECIMAL(10)
}
```

Both `student_id` and `course_id` are marked with `*`, making them a composite PK.

## 2.7 A Complete Example

Here is a more complete example modelling a tourism management system:

```msd
# Tourism Management System
# MSD file for the tourism platform database

project {
    name: Tourism Management System
    author: Achraf SOLTANI
    description: Database model for a tourism platform
}

entity Tourist {
    *id: INT
    name: VARCHAR(255)
    email: VARCHAR(255)
    password: TEXT
}

entity Role {
    *id: INT
    name: TEXT
}

entity Guide {
    *id: INT
    name: VARCHAR(255)
    speciality: VARCHAR(100)
    rating: DECIMAL(10)
}

entity Experience {
    *id: INT
    title: VARCHAR(255)
    description: TEXT
    price: DECIMAL(10)
    duration: INT
}

entity Booking {
    *id: INT
    booking_date: TIMESTAMP
    status: VARCHAR(50)
}

association user_role {
    assigned_at: TIMESTAMP
}

association creer {
}

association reserver {
    quantity: INT
}

link Tourist (1,1) user_role
link Role (0,N) user_role
link Guide (0,N) creer
link Experience (1,1) creer
link Tourist (0,N) reserver
link Experience (1,N) reserver
```

## 2.8 What Happens Under the Hood

When you run `merisio-cli school.msd parse`, the following steps occur:

1. **Lexing**: The source text is broken into tokens (keywords, identifiers, symbols, etc.)
2. **Parsing**: Tokens are assembled into an intermediate representation (ParseResult)
3. **Building**: The ParseResult is converted into a Merisio Project with:
   - UUID generation for every entity, association, and link
   - Name-to-UUID resolution for link references
   - Semantic validation (duplicate names, unknown references)
4. **Layout**: Fruchterman-Reingold force-directed placement positions all elements
5. **Saving**: The Project is serialised as JSON to a `.merisio` file

Each of these stages is covered in detail in the implementation chapters (4–7).
