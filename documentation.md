# Merisio - Documentation

A modern MERISE database modeling tool built with Python and PySide6.

## Table of Contents

1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [Features](#features)
4. [GUI Usage](#gui-usage)
5. [CLI Usage](#cli-usage)
6. [Man Pages](#man-pages)
7. [File Format](#file-format)
8. [Architecture](#architecture)
9. [Development](#development)

---

## Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Setup

1. Navigate to the project directory:
   ```bash
   cd Merisio
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

### Pre-built Binaries

Download the latest release from the [Releases](https://github.com/AchrafSoltani/Merisio/releases) page.

**Linux:**
- `Merisio-x.x.x-linux-x64.tar.gz` - Portable archive
- `merisio_x.x.x_amd64.deb` - Debian/Ubuntu package

**Windows:**
- `Merisio-x.x.x-windows-x64.zip` - Portable archive

#### Linux Installation

**From .deb package (Debian/Ubuntu):**
```bash
sudo dpkg -i merisio_1.3.1_amd64.deb
```
This installs both `merisio` (GUI) and `merisio-cli` (CLI) to `/usr/bin/`.

**From archive:**
```bash
tar -xzvf Merisio-linux-x64.tar.gz
cd Merisio-linux-x64
./Merisio        # GUI
./merisio-cli    # CLI
```

---

## Quick Start

### Creating Your First Model

1. **Create Entities**
   - Go to the "MCD" tab
   - Right-click on the canvas or use the toolbar to click "Add Entity"
   - Enter entity name (e.g., `Client`)
   - Add attributes: enter name (e.g., `id_client`), select type (e.g., `INT`), check "Primary Key"
   - Repeat for other attributes (e.g., `nom` VARCHAR(100), `email` VARCHAR(255))

2. **Create Associations**
   - Click "Add Association" or right-click on canvas > "Add Association"
   - Enter association name (e.g., `Passer`)
   - Optionally add carrying attributes

3. **Create Links**
   - Click "Add Link" or right-click on an entity/association
   - Select entity and association to connect
   - Choose cardinality (e.g., `1,N`)

4. **View the MLD**
   - Switch to the "MLD" tab to see the auto-generated logical data model
   - Double-click column names to rename them

5. **Generate SQL**
   - Go to the "SQL" tab
   - View or copy the generated PostgreSQL DDL

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
- Ctrl + Scroll to zoom (25%-400%)
- Delete key to remove selected items
- Rubber band selection (click and drag)

**Link Styles:**
- Curved (Bezier curves, default)
- Orthogonal (right-angle lines)
- Straight (direct lines)

**Diagram Colours:**
- Customisable via Options > Diagram Colours
- Colours saved per-project in the `.merisio` file

### Cardinalities

| Cardinality | Meaning |
|-------------|---------|
| (0,1) | Optional, at most one |
| (0,N) | Optional, many |
| (1,1) | Mandatory, exactly one |
| (1,N) | Mandatory, at least one |

### MLD View

- Auto-generated Logical Data Model from the MCD
- Table/column tree view
- Editable column names: double-click or right-click to rename
- Custom names saved in project and used in SQL generation

### SQL Generation

Generates PostgreSQL DDL with:
- CREATE TABLE statements for entities
- Primary key constraints
- Foreign key constraints for 1-N relationships
- Junction tables for N-N relationships
- Carrying attributes in junction tables

### Diagram Export

Export diagrams via File > Export Diagram:
- **SVG** - Scalable vector graphics
- **PNG** - Raster images (configurable scale factor)
- **PDF** - Print-ready documents

### File Operations

- **New Project** (Ctrl+N) - Create empty project
- **Open** (Ctrl+O) - Load `.merisio` file
- **Save** (Ctrl+S) - Save current project
- **Save As** (Ctrl+Shift+S) - Save with new name

---

## GUI Usage

### Command-Line Flags

The GUI binary accepts the following flags:

```bash
merisio --help       # Print usage summary and exit
merisio -h           # Same as --help
merisio --version    # Print version and exit
merisio -v           # Same as --version
```

When launched without arguments, the graphical editor opens.

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New project |
| Ctrl+O | Open project |
| Ctrl+S | Save project |
| Ctrl+Shift+S | Save as |
| Ctrl+1 | Switch to Dictionary tab |
| Ctrl+2 | Switch to MCD tab |
| Ctrl+3 | Switch to MLD tab |
| Ctrl+4 | Switch to SQL tab |
| Delete | Delete selected items |
| Ctrl+Scroll | Zoom in/out (MCD canvas) |
| Ctrl++ | Zoom in |
| Ctrl+- | Zoom out |
| Ctrl+0 | Fit to view |
| Ctrl+Shift+0 | Reset zoom (100%) |

### Options Menu

| Option | Description |
|--------|-------------|
| Show Attributes | Toggle attribute visibility in MCD entities/associations |
| Link Style > Curved | Bezier curve links (default) |
| Link Style > Orthogonal | Right-angle links |
| Link Style > Straight | Direct line links |
| Diagram Colours | Customise colours for entities, associations, and links |

### Workflow Tips

1. **Start with Entities** - Create entities with their attributes before creating associations
2. **Use Primary Keys** - Every entity should have at least one PK attribute
3. **Check the MLD** - Review the auto-generated logical model after creating links
4. **Rename Columns** - Use the MLD view to rename auto-generated column names
5. **Save Frequently** - Save your work to avoid losing changes

### Validation Rules

The validator checks for:
- Entities without primary keys
- Associations with fewer than 2 links
- Orphan entities (not connected to any association)

---

## CLI Usage

The `merisio-cli` tool allows you to work with `.merisio` project files from the command line, useful for CI pipelines and scripting.

### Synopsis

```
merisio-cli [--help] [--version] <file.merisio> <command> [options]
```

### Global Options

```bash
merisio-cli --help       # Print usage and exit
merisio-cli --version    # Print version and exit
```

### Commands

| Command | Description |
|---------|-------------|
| `info` | Show project metadata and statistics |
| `validate` | Validate the MCD model (exit code 1 on errors) |
| `sql` | Generate PostgreSQL DDL |
| `mld` | Show the logical data model (MLD tables) |
| `export` | Export diagram to PNG, SVG, or PDF |

### Command Details

#### info

```bash
merisio-cli project.merisio info
```

Displays project name, author, description, creation and modification timestamps, and counts of entities, associations, links, and attributes.

#### validate

```bash
merisio-cli project.merisio validate
```

Checks the model for errors. Exits with code 0 on success, code 1 on validation failure.

#### sql

```bash
merisio-cli project.merisio sql              # Print SQL to stdout
merisio-cli project.merisio sql -o schema.sql  # Write SQL to file
```

**Options:**
- `-o, --output PATH` - Write SQL to a file instead of stdout

#### mld

```bash
merisio-cli project.merisio mld
```

Prints all tables with their columns, primary keys, foreign keys, and nullability constraints.

#### export

```bash
merisio-cli project.merisio export --format png -o diagram.png
merisio-cli project.merisio export --format svg -o diagram.svg
merisio-cli project.merisio export --format pdf -o diagram.pdf
merisio-cli project.merisio export --format png -o diagram.png --scale 3.0
```

**Options:**
- `--format FORMAT` - Export format: `png`, `svg`, or `pdf` (required)
- `-o, --output PATH` - Output file path (required)
- `--scale FACTOR` - Scale factor for PNG export (default: 2.0)

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation failed (one or more errors in the MCD model) |
| 2 | Runtime error (file not found, write failure, unsupported format) |

---

## Man Pages

Man pages are provided for both binaries: `merisio(1)` and `merisio-cli(1)`.

### Installation

```bash
# Install system-wide (requires root)
sudo python build.py install-man

# Read the man pages
man merisio
man merisio-cli

# Uninstall
sudo python build.py uninstall-man
```

### Reading Without Installation

```bash
man ./man/merisio.1
man ./man/merisio-cli.1
```

---

## File Format

Projects are saved as JSON files with the `.merisio` extension (format version 2.1).

### Schema

```json
{
  "version": "2.1",
  "metadata": {
    "name": "Project Name",
    "description": "Project description",
    "author": "Author Name",
    "created_at": "2026-01-20T10:00:00",
    "modified_at": "2026-02-01T15:30:00"
  },
  "mcd": {
    "entities": [
      {
        "id": "uuid-string",
        "name": "Client",
        "attributes": [
          {
            "name": "id_client",
            "type": "INT",
            "size": null,
            "pk": true
          }
        ],
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
  },
  "mld": {
    "column_overrides": {
      "TABLE.original_col": "renamed_col"
    }
  },
  "colors": {
    "entity_fill": "#E3F2FD",
    "entity_border": "#1976D2",
    "association_fill": "#FFF3E0",
    "association_border": "#F57C00",
    "link_color": "#000000"
  }
}
```

---

## Architecture

### Project Structure

```
Merisio/
├── main.py                 # GUI entry point
├── cli.py                  # CLI entry point (merisio-cli)
├── build.py                # Build script for PyInstaller
├── merisio.desktop         # Linux desktop integration
├── requirements.txt        # Python dependencies
├── man/
│   ├── merisio.1           # GUI man page
│   └── merisio-cli.1       # CLI man page
├── resources/
│   └── icons/
│       ├── app_icon.svg    # Vector icon
│       └── app_icon.png    # PNG icon (256x256)
├── src/
│   ├── models/             # Data models (dataclasses)
│   │   ├── attribute.py    # Attribute definition
│   │   ├── entity.py       # MCD entity
│   │   ├── association.py  # MCD association
│   │   ├── link.py         # Entity-Association link
│   │   ├── dictionary.py   # Attribute collection
│   │   ├── mld.py          # MLD table/column models
│   │   └── project.py      # Project container
│   ├── views/              # UI components (PySide6)
│   │   ├── main_window.py       # Main window with tabs
│   │   ├── dictionary_view.py   # Dictionary table
│   │   ├── mcd_canvas.py        # Graphics view
│   │   ├── mcd_items.py         # Graphics items
│   │   ├── mld_view.py          # MLD tree view
│   │   ├── sql_view.py          # SQL display
│   │   └── dialogs/             # Input dialogs
│   ├── controllers/        # Business logic
│   │   ├── mcd_controller.py    # Validation and statistics
│   │   ├── mld_transformer.py   # MCD to MLD transformation
│   │   └── sql_generator.py     # DDL generation
│   ├── export/             # Headless rendering
│   │   └── renderer.py     # Offscreen diagram export
│   └── utils/              # Utilities
│       ├── constants.py    # App constants and version
│       ├── file_io.py      # JSON serialisation
│       └── theme.py        # UI stylesheet
└── tests/                  # Unit tests
    ├── test_models.py
    └── test_sql_generator.py
```

### Design Patterns

- **MVC Architecture** - Models, Views, and Controllers are separated
- **Qt Signals/Slots** - For event handling between components
- **Dataclasses** - For data models
- **Factory Pattern** - `from_dict()` class methods for deserialisation

### Key Classes

| Class | Purpose |
|-------|---------|
| `Project` | Root container for all model data |
| `Entity` | Represents an MCD entity |
| `Association` | Represents an MCD relationship |
| `Link` | Connects entity to association with cardinality |
| `MLDTable` | Logical model table |
| `MainWindow` | Application main window |
| `MCDCanvas` | QGraphicsView for diagram editing |
| `MCDController` | Validation and statistics |
| `MLDTransformer` | MCD to MLD transformation |
| `SQLGenerator` | Transforms MLD to PostgreSQL DDL |
| `HeadlessRenderer` | Offscreen diagram export (used by CLI) |

---

## Development

### Building

```bash
# Build both GUI and CLI (default)
python build.py build-all

# Build GUI only
python build.py build

# Build CLI only
python build.py build-cli

# Install man pages (Linux, requires root)
sudo python build.py install-man

# Uninstall man pages
sudo python build.py uninstall-man

# Create .ico from PNG (Windows, requires ImageMagick)
python build.py ico

# Clean build files
python build.py clean
```

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

### Transformation Rules (MCD to MLD)

1. **Entity to Table** - Each entity becomes a table
2. **(1,1)-(0,N)** - FK added to the "1" side table
3. **(0,N)-(0,N)** - Junction table created
4. **Carrying Attributes** - Added to junction table

---

## License

GNU GPL v2

## Credits

- Original AnalyseSI: https://launchpad.net/analysesi
- Built with PySide6 (Qt for Python)

## Author

**Achraf SOLTANI**
- Email: achraf.soltani@pm.me
- GitHub: [@AchrafSoltani](https://github.com/AchrafSoltani)
