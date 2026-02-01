# Merisio

A modern MERISE database modeling tool built with Python and PySide6.

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![License](https://img.shields.io/badge/license-GPL%20v2-green)
![Python](https://img.shields.io/badge/python-3.11+-yellow)

## Features

- **MCD Editor** - Visual diagram editor for entities, associations, and links
  - Drag-and-drop positioning
  - Multi-selection and deletion
  - Cardinalities: (0,1), (0,N), (1,1), (1,N)
  - Link styles: Curved, Orthogonal, Straight
  - Toggle attribute visibility
  - Zoom controls with slider (25%-400%)
  - Customizable colors for entities, associations, and links
- **Export** - Export diagrams to SVG, PNG, or PDF formats
- **Data Dictionary** - Overview of all attributes across entities
- **MLD View** - Logical Data Model with table/column tree view
  - Editable column names (right-click or double-click to rename)
  - Custom names saved in project and used in SQL generation
- **SQL Generation** - PostgreSQL CREATE TABLE statements
- **Project Management** - Save/load projects in `.merisio` JSON format
- **Options Menu** - Show/hide attributes, link style, diagram colors

## Screenshots

![MCD Editor](resources/screenshots/mcd-editor.png)
*MCD Editor - First screenshot of Merisio v1.0.0 (January 21, 2026)*

## Requirements

- Python 3.11+
- PySide6

## Installation

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
sudo dpkg -i merisio_1.2.0_amd64.deb
```

**From archive:**
```bash
tar -xzvf Merisio-1.2.0-linux-x64.tar.gz
cd Merisio-1.2.0-linux-x64
./Merisio
```

### From Source

```bash
# Clone the repository
git clone https://github.com/AchrafSoltani/Merisio.git
cd Merisio

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Building from Source

### Prerequisites

```bash
pip install pyinstaller
```

### Build Commands

**Linux:**
```bash
# Activate virtual environment
source venv/bin/activate

# Build
python build.py build

# Output: dist/Merisio (standalone executable)
```

**Windows:**
```bash
# Activate virtual environment
venv\Scripts\activate

# Create .ico from SVG (requires ImageMagick)
python build.py ico

# Build
python build.py build

# Output: dist\Merisio.exe
```

**Clean build files:**
```bash
python build.py clean
```

## Usage

1. **Create Entities** - Right-click on the MCD canvas or use the toolbar to add entities
2. **Create Associations** - Add associations to define relationships between entities
3. **Link Them** - Connect entities to associations with cardinalities
4. **View MLD** - Switch to MLD tab to see the logical model (double-click columns to rename)
5. **Generate SQL** - Switch to SQL tab to see PostgreSQL DDL statements
6. **Save Project** - File > Save to save your work

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New Project |
| Ctrl+O | Open Project |
| Ctrl+S | Save Project |
| Ctrl+1 | Dictionary Tab |
| Ctrl+2 | MCD Tab |
| Ctrl+3 | MLD Tab |
| Ctrl+4 | SQL Tab |
| Delete | Delete Selected |
| Ctrl+Scroll | Zoom In/Out |
| Ctrl++ | Zoom In |
| Ctrl+- | Zoom Out |
| Ctrl+0 | Fit to View |
| Ctrl+Shift+0 | Reset Zoom (100%) |

### Options Menu

| Option | Description |
|--------|-------------|
| Show Attributes | Toggle attribute visibility in MCD entities/associations |
| Link Style > Curved | Bezier curve links (default) |
| Link Style > Orthogonal | Right-angle links |
| Link Style > Straight | Direct line links |
| Diagram Colors | Customize colors for entities, associations, and links |

## Project Structure

```
Merisio/
├── main.py                 # Application entry point
├── build.py                # Build script for PyInstaller
├── merisio.spec            # PyInstaller configuration
├── merisio.desktop         # Linux desktop integration
├── requirements.txt        # Python dependencies
├── resources/
│   └── icons/
│       ├── app_icon.svg    # Vector icon
│       └── app_icon.png    # PNG icon (256x256)
├── src/
│   ├── models/             # Data models (Entity, Association, Link, Project)
│   ├── views/              # UI components (Canvas, Dialogs, Views)
│   ├── controllers/        # Business logic (MLD transformer, SQL generator)
│   └── utils/              # Utilities, constants, theme
├── tests/                  # Unit tests
└── .github/
    └── workflows/
        └── build.yml       # GitHub Actions CI/CD
```

## File Format

Merisio uses a JSON-based project format with the `.merisio` extension:

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
    "entities": [...],
    "associations": [...],
    "links": [...]
  },
  "mld": {
    "column_overrides": { "TABLE.original_col": "renamed_col" }
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

## License

GNU GPL v2

## Author

**Achraf SOLTANI**
Email: achraf.soltani@pm.me
GitHub: [@AchrafSoltani](https://github.com/AchrafSoltani)

## Acknowledgments

Inspired by the original [AnalyseSI](https://launchpad.net/analysesi) Java project.
