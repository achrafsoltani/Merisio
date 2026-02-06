---
layout: default
---

# Merisio

A modern **MERISE database modeling tool** built with Python and PySide6.

Create MCD (Conceptual Data Model) diagrams, automatically generate MLD (Logical Data Model) views, and export PostgreSQL SQL scripts — from the GUI or the command line.

![MCD Editor](mcd-editor.png)

---

## Download

<a href="https://github.com/AchrafSoltani/Merisio/releases/latest" class="btn">Download Latest Release</a>

### Available formats:
- **Linux**: `.tar.gz` (portable) or `.deb` (Debian/Ubuntu)
- **Windows**: `.zip` (portable)

All packages include both the GUI application (`merisio`) and the CLI tool (`merisio-cli`).

---

## Features

### MCD Editor
- Visual diagram editor for entities, associations, and links
- Drag-and-drop positioning
- Multi-selection and deletion
- Cardinalities: (0,1), (0,N), (1,1), (1,N)
- Link styles: Curved, Orthogonal, Straight
- Toggle attribute visibility
- Zoom controls (25%–400%)
- Customizable diagram colours
- Export diagrams to SVG, PNG, or PDF

### CLI Tool (`merisio-cli`)
- Validate MCD models in CI pipelines
- Generate PostgreSQL DDL to stdout or file
- Inspect MLD tables and columns
- Export diagrams headlessly (PNG, SVG, PDF)

### Data Dictionary
- Overview of all attributes across entities
- Define data types: INT, VARCHAR, TEXT, DATE, BOOLEAN, etc.

### MLD View
- Automatic Logical Data Model generation from MCD
- Editable column names (rename auto-generated foreign keys)
- Custom names saved in project

### SQL Generation
- PostgreSQL CREATE TABLE statements
- Automatic primary/foreign key generation
- Ready to execute scripts

### Project Management
- Save/load projects in `.merisio` JSON format
- Cross-platform compatibility

---

## Installation

### Linux (Debian/Ubuntu)

```bash
sudo dpkg -i merisio_1.3.0_amd64.deb
```

This installs both `/usr/bin/merisio` (GUI) and `/usr/bin/merisio-cli` (CLI).

### Linux (Portable)

```bash
tar -xzvf Merisio-linux-x64.tar.gz
cd Merisio-linux-x64
./Merisio        # GUI
./merisio-cli    # CLI
```

### Windows

Extract `Merisio-windows-x64.zip` and run `Merisio.exe` (GUI) or `merisio-cli.exe` (CLI).

### From Source

```bash
git clone https://github.com/AchrafSoltani/Merisio.git
cd Merisio
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py       # GUI
python cli.py        # CLI
```

---

## CLI Usage

```
merisio-cli <file.merisio> <command> [options]
```

| Command | Description |
|---------|-------------|
| `info` | Show project metadata and statistics |
| `validate` | Validate the MCD model (exit code 1 on errors) |
| `sql` | Generate PostgreSQL DDL |
| `mld` | Show the logical data model |
| `export` | Export diagram to PNG, SVG, or PDF |

### Examples

```bash
# Project info
merisio-cli project.merisio info

# Validate (useful in CI — fails with exit code 1)
merisio-cli project.merisio validate

# Generate SQL
merisio-cli project.merisio sql
merisio-cli project.merisio sql -o schema.sql

# View MLD tables
merisio-cli project.merisio mld

# Export diagram
merisio-cli project.merisio export --format png -o diagram.png
merisio-cli project.merisio export --format svg -o diagram.svg
merisio-cli project.merisio export --format pdf -o diagram.pdf
merisio-cli project.merisio export --format png -o diagram.png --scale 3.0
```

---

## Keyboard Shortcuts

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

---

## About MERISE

MERISE is a French methodology for database design, widely used in France and French-speaking countries. It uses:

- **MCD** (Modèle Conceptuel de Données) - Conceptual Data Model with entities and associations
- **MLD** (Modèle Logique de Données) - Logical Data Model with tables and relationships
- **MPD** (Modèle Physique de Données) - Physical Data Model (SQL implementation)

Merisio helps you design at the conceptual level and automatically generates the logical and physical models.

---

## License

GNU GPL v2

---

## Author

**Achraf SOLTANI**

- Email: [achraf.soltani@pm.me](mailto:achraf.soltani@pm.me)
- GitHub: [@AchrafSoltani](https://github.com/AchrafSoltani)

---

## Acknowledgments

Inspired by the original [AnalyseSI](https://launchpad.net/analysesi) Java project.
