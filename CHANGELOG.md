# Changelog

All notable changes to Merisio will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] — v1.6.0

### Added
- Draggable link geometry — select a link to reveal waypoint handles (drag to move a bend) and segment-midpoint handles (drag to insert a new waypoint). Constant on-screen pixel size at any zoom.
- Magnetic snap during waypoint drag — within 20 scene units of the line through its neighbours, the cursor sticks to that line.
- Right-click waypoint menu — "Remove waypoint", "Tidy Up Link" (collapse waypoints within 40 units of their neighbour line, iterates until stable), "Straighten Link" (wipe all waypoints).
- Conditional "Tidy Up Link" and "Straighten Link" entries on the link's own right-click menu (shown only when waypoints exist).
- Draggable cardinality label — the "1,N" / "0,1" box slides along the link's path; the position is stored as `card_t` in the `.merisio` file and survives save/reload.

### Changed
- Curved single-segment links now bend *away* from the diagram's visual centroid, so mirrored links never bow inward through other items.
- Curved multi-waypoint links use a Catmull-Rom cubic Bezier spline (C¹-continuous at every waypoint) instead of per-segment quadratic Bezier — no kink at joins, clean re-routing when a waypoint is removed.
- Orthogonal multi-waypoint links use one-corner-per-segment (L-shape) routing instead of two-corner Z-routing, producing a clean staircase. Single-segment orthogonal links keep the centred Z corner.
- File format bumped to **v2.2**: `Link` now carries `waypoints: list[list[float]]` (absolute scene coordinates) and `card_t: float` (label position along the path). Both fields default such that v2.1 files load unchanged.

## [1.5.0] - 2026-03-25

### Added
- Properties panel Edit button opens full entity/association dialog
- Link cardinality inline editing (Min/Max dropdowns) in properties panel
- Canvas emits selection_changed for links

### Changed
- Native Qt combo box rendering instead of custom CSS (cleaner on KDE/GNOME)

## [1.4.3] - 2026-03-25

### Fixed
- SQL tab auto-generates when selected in output panel
- Dictionary highlights selected entity's attributes in blue
- Canvas selection propagates highlight to dictionary

## [1.4.2] - 2026-03-25

### Fixed
- Minimap viewport tracking verified working with zoom/scroll
- Click-to-navigate in minimap verified working

## [1.4.1] - 2026-03-25

### Fixed
- Bidirectional sync between canvas, project tree, and properties panel
- Canvas selection updates tree highlight and properties
- Tree selection highlights item on canvas and centres view
- Fixed private method access in MCDCanvas (added public wrappers)
- Fixed project tree using correct API (get_all_entities/associations)
- Fixed properties panel attribute type field (data_type not type)

## [1.4.0] - 2026-03-25

### Added
- MySQL Workbench-inspired layout with QSplitter-based design
- Left sidebar: minimap (bird's eye diagram overview), project tree (entities/associations navigator), properties panel
- Bottom output panel with Dictionary, Validation, and SQL Preview tabs
- Model menu: Validate (F5), Generate MLD, Generate SQL
- Toggle sidebar (Ctrl+B) and output panel (Ctrl+J)
- Enhanced toolbar: Add Entity, Add Association, Add Link, Validate

### Changed
- Replaced flat 4-tab layout (Dictionary, MCD, MLD, SQL) with sidebar + central tabs + bottom panel
- Dictionary moved from top-level tab to bottom output panel
- Toned down theme: neutral grey buttons, subtle tab accents, native Qt combo box rendering

## [1.3.1] - 2026-02-06

### Added
- Man pages for `merisio(1)` and `merisio-cli(1)`
- `--help` and `--version` flags for the GUI binary (`merisio`)
- `--version` flag for the CLI binary (`merisio-cli`)
- Build commands: `install-man`, `uninstall-man` for system-wide man page installation

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

[1.5.0]: https://github.com/AchrafSoltani/Merisio/compare/v1.4.3...v1.5.0
[1.4.3]: https://github.com/AchrafSoltani/Merisio/compare/v1.4.2...v1.4.3
[1.4.2]: https://github.com/AchrafSoltani/Merisio/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/AchrafSoltani/Merisio/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/AchrafSoltani/Merisio/compare/v1.3.1...v1.4.0
[1.3.1]: https://github.com/AchrafSoltani/Merisio/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/AchrafSoltani/Merisio/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/AchrafSoltani/Merisio/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/AchrafSoltani/Merisio/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/AchrafSoltani/Merisio/releases/tag/v1.0.0
