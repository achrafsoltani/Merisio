# Changelog

All notable changes to Merisio will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-02-06

### Added
- CLI tool (`merisio-cli`) for batch processing `.merisio` files without the GUI
  - `info` — show project metadata and statistics
  - `validate` — validate the MCD model (exit code 1 on errors)
  - `sql` — generate PostgreSQL DDL to stdout or file (`-o`)
  - `mld` — show the logical data model (MLD tables)
  - `export` — export diagram to PNG, SVG, or PDF (`--format`, `-o`, `--scale`)
- Headless diagram renderer (`src/export/renderer.py`) for offscreen export
- Build commands: `build-cli` (CLI only), `build-all` (GUI + CLI)
- `.deb` package now installs both `/usr/bin/merisio` and `/usr/bin/merisio-cli`
- Windows zip now includes both `Merisio.exe` and `merisio-cli.exe`
- Auto-size entity and association boxes to fit names using font metrics

### Changed
- Default `python build.py` now builds both GUI and CLI
- MCD tab opens by default on startup

## [1.2.0] - 2026-02-01

### Added
- Zoom controls in MCD canvas with limits (25%-400%)
- Zoom slider and round +/- buttons in status bar
- Zoom menu items in View menu with keyboard shortcuts (Ctrl++, Ctrl+-, Ctrl+0, Ctrl+Shift+0)
- Export diagram feature: File > Export Diagram (SVG, PNG, PDF formats)
- Customizable diagram colors: Options > Diagram Colors
- Color settings stored per-project in `.merisio` file

### Changed
- Project file format updated to version 2.1 with colors section
- Item position changes now mark project as modified (prompts save on close)

## [1.1.0] - 2026-01-21

### Added
- MLD column renaming (right-click or double-click to rename)
- Column overrides saved in project file under `mld.column_overrides`
- SQL generator uses renamed columns
- Options menu with "Show Attributes" toggle
- Link Style submenu: Curved, Orthogonal, Straight
- Project properties dialog (File > Project Properties)
- Project metadata: name, description, author, timestamps

### Changed
- MLD changes mark project as modified (star in title bar)
- Renamed project from "AnalyseSI" to "Merisio"
- Changed file extension to `.merisio`

## [1.0.0] - 2026-01-20

### Added
- Initial release
- MCD Editor with visual diagram editing
  - Entities with attributes
  - Associations with carrying attributes
  - Links with cardinalities (0,1), (0,N), (1,1), (1,N)
  - Drag-and-drop positioning
  - Multi-selection and deletion
- Data Dictionary tab with overview of all attributes
- MLD View with auto-generated logical model
- SQL View with PostgreSQL CREATE TABLE statements
- Project save/load in JSON format
- Light gray UI theme (Beekeeper Studio inspired)
- App icon (stylized M with nodes)
- Linux desktop integration
- Keyboard shortcuts (Ctrl+1-4 for tabs, Ctrl+N/O/S for file operations)

[1.3.0]: https://github.com/AchrafSoltani/Merisio/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/AchrafSoltani/Merisio/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/AchrafSoltani/Merisio/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/AchrafSoltani/Merisio/releases/tag/v1.0.0
