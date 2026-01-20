# AnalyseSI Modern - Documentation

A modern MERISE database modeling tool built with Python and PySide6.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [User Guide](#user-guide)
5. [File Format](#file-format)
6. [Architecture](#architecture)
7. [Development](#development)

---

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Setup

1. Navigate to the project directory:
   ```bash
   cd analysesi
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   # Linux/macOS
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

```bash
./venv/bin/python main.py
```

Or with activated virtual environment:
```bash
python main.py
```

---

## Quick Start

### Creating Your First Model

1. **Add Attributes to Dictionary**
   - Go to the "Dictionary" tab
   - Click "Add Attribute"
   - Enter name (e.g., `id_client`), select type (e.g., `INT`), check "Primary Key"
   - Repeat for other attributes (e.g., `nom` VARCHAR(100), `email` VARCHAR(255))

2. **Create Entities**
   - Go to the "MCD" tab
   - Click "Add Entity" or right-click on canvas → "Add Entity"
   - Enter entity name (e.g., `Client`)
   - Select attributes from the dictionary

3. **Create Associations**
   - Click "Add Association" or right-click → "Add Association"
   - Enter association name (e.g., `Passer`)
   - Optionally select carrying attributes

4. **Create Links**
   - Click "Add Link" or right-click on an entity/association
   - Select entity and association to connect
   - Choose cardinality (e.g., `1,N`)

5. **Generate SQL**
   - Go to the "SQL" tab
   - Click "Generate SQL"
   - Copy or export the generated PostgreSQL DDL

---

## Features

### Data Dictionary

The dictionary manages all attributes used in the model:

| Field | Description |
|-------|-------------|
| Name | Attribute identifier (e.g., `id_client`) |
| Type | SQL data type (INT, VARCHAR, DATE, etc.) |
| Size | Size for VARCHAR, CHAR, DECIMAL types |
| Primary Key | Marks attribute as primary key |

**Supported Data Types:**
- INT, BIGINT, SMALLINT
- VARCHAR, CHAR, TEXT
- BOOLEAN
- DATE, TIME, TIMESTAMP
- DECIMAL, FLOAT, DOUBLE

### MCD Editor

Visual canvas for creating MERISE Conceptual Data Models:

- **Entities** - Rounded rectangles (blue)
- **Associations** - Diamond shapes (orange)
- **Links** - Lines with cardinality labels

**Canvas Interactions:**
- Drag items to reposition
- Right-click for context menu
- Ctrl + Scroll to zoom
- Delete key to remove selected items
- Rubber band selection (click and drag)

### Cardinalities

| Cardinality | Meaning |
|-------------|---------|
| (0,1) | Optional, at most one |
| (0,N) | Optional, many |
| (1,1) | Mandatory, exactly one |
| (1,N) | Mandatory, at least one |

### SQL Generation

Generates PostgreSQL DDL with:
- CREATE TABLE statements for entities
- Primary key constraints
- Foreign key constraints for 1-N relationships
- Junction tables for N-N relationships
- Carrying attributes in junction tables

### File Operations

- **New Project** (Ctrl+N) - Create empty project
- **Open** (Ctrl+O) - Load .asip file
- **Save** (Ctrl+S) - Save current project
- **Save As** (Ctrl+Shift+S) - Save with new name

---

## User Guide

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New project |
| Ctrl+O | Open project |
| Ctrl+S | Save project |
| Ctrl+Shift+S | Save as |
| Ctrl+1 | Switch to Dictionary tab |
| Ctrl+2 | Switch to MCD tab |
| Ctrl+3 | Switch to SQL tab |
| Delete | Delete selected items |
| Ctrl+Scroll | Zoom in/out (MCD canvas) |

### Workflow Tips

1. **Start with the Dictionary** - Define all attributes before creating entities
2. **Use Primary Keys** - Every entity should have at least one PK attribute
3. **Validate Often** - Use the "Validate" button to check for issues
4. **Save Frequently** - Save your work to avoid losing changes

### Validation Rules

The validator checks for:
- Empty dictionary
- Entities without primary keys
- Associations with fewer than 2 links
- Orphan entities (not connected to any association)

---

## File Format

Projects are saved as JSON files with `.asip` extension.

### Schema

```json
{
  "version": "1.0",
  "dictionary": {
    "attributes": [
      {
        "name": "id_client",
        "type": "INT",
        "size": null,
        "pk": true
      },
      {
        "name": "nom",
        "type": "VARCHAR",
        "size": 100,
        "pk": false
      }
    ]
  },
  "mcd": {
    "entities": [
      {
        "id": "uuid-string",
        "name": "Client",
        "attributes": ["id_client", "nom"],
        "x": 100.0,
        "y": 100.0
      }
    ],
    "associations": [
      {
        "id": "uuid-string",
        "name": "Passer",
        "attributes": [],
        "x": 300.0,
        "y": 100.0
      }
    ],
    "links": [
      {
        "id": "uuid-string",
        "entity_id": "entity-uuid",
        "association_id": "assoc-uuid",
        "card_min": "1",
        "card_max": "N"
      }
    ]
  }
}
```

---

## Architecture

### Project Structure

```
analysesi/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── src/
│   ├── models/            # Data models (dataclasses)
│   │   ├── attribute.py   # Attribute definition
│   │   ├── entity.py      # MCD entity
│   │   ├── association.py # MCD association
│   │   ├── link.py        # Entity-Association link
│   │   ├── dictionary.py  # Attribute collection
│   │   └── project.py     # Project container
│   ├── views/             # UI components (PySide6)
│   │   ├── main_window.py      # Main window with tabs
│   │   ├── dictionary_view.py  # Dictionary table
│   │   ├── mcd_canvas.py       # Graphics view
│   │   ├── mcd_items.py        # Graphics items
│   │   ├── sql_view.py         # SQL display
│   │   └── dialogs/            # Input dialogs
│   ├── controllers/       # Business logic
│   │   ├── mcd_controller.py   # Validation
│   │   └── sql_generator.py    # DDL generation
│   └── utils/             # Utilities
│       ├── constants.py   # App constants
│       └── file_io.py     # JSON serialization
└── tests/                 # Unit tests
    ├── test_models.py
    └── test_sql_generator.py
```

### Design Patterns

- **MVC Architecture** - Models, Views, and Controllers are separated
- **Qt Signals/Slots** - For event handling between components
- **Dataclasses** - For immutable data models
- **Factory Pattern** - `from_dict()` class methods for deserialization

### Key Classes

| Class | Purpose |
|-------|---------|
| `Project` | Root container for all model data |
| `Dictionary` | Manages attribute definitions |
| `Entity` | Represents an MCD entity |
| `Association` | Represents an MCD relationship |
| `Link` | Connects entity to association with cardinality |
| `MainWindow` | Application main window |
| `MCDCanvas` | QGraphicsView for diagram editing |
| `SQLGenerator` | Transforms MCD to PostgreSQL DDL |

---

## Development

### Running Tests

```bash
./venv/bin/python -m pytest tests/ -v
```

### Adding New Features

1. **New Data Type** - Add to `DATA_TYPES` in `src/utils/constants.py`
2. **New Cardinality** - Add to `CARDINALITY_MIN/MAX` in constants
3. **New SQL Dialect** - Create new generator class based on `SQLGenerator`

### Code Style

- Python 3.11+ type hints
- PEP 8 naming conventions
- Dataclasses for models
- Qt naming conventions for UI classes

---

## MERISE Methodology Reference

### Conceptual Data Model (MCD)

The MCD represents the business domain with:
- **Entities** - Real-world objects (Client, Product, Order)
- **Associations** - Relationships between entities (places, contains)
- **Attributes** - Properties of entities and associations
- **Cardinalities** - Constraints on relationships

### Transformation Rules (MCD → MPD)

1. **Entity → Table** - Each entity becomes a table
2. **(1,1)-(0,N)** - FK added to the "1" side table
3. **(0,N)-(0,N)** - Junction table created
4. **Carrying Attributes** - Added to junction table

---

## License

Based on the original AnalyseSI project (GNU GPL v2).

## Credits

- Original AnalyseSI: https://launchpad.net/analysesi
- Built with PySide6 (Qt for Python)
