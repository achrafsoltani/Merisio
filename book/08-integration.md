# Chapter 8: CLI and GUI Integration

The MSD pipeline is a library — a set of modules that can be used programmatically. To make it useful, it needs to be integrated into Merisio's two entry points: the command-line interface (CLI) and the graphical user interface (GUI).

## 8.1 CLI Integration

### The `parse` Subcommand

The CLI integration lives in `cli.py`. A new `cmd_parse()` function and `parse` subparser were added alongside the existing commands (`info`, `validate`, `sql`, `mld`, `export`).

### Usage

```bash
merisio-cli schema.msd parse [-o output.merisio]
```

The `parse` command:
1. Reads the `.msd` file
2. Parses it through the MSD pipeline
3. Reports errors and warnings to stderr
4. Saves the resulting project as `.merisio`
5. Exits with code 0 (success), 1 (parse errors), or 2 (runtime errors)

### Implementation

```python
def cmd_parse(args):
    from src.msd import MSDParser, MSDProjectBuilder
    from src.utils.file_io import FileIO

    file_path = args.file
    if not os.path.isfile(file_path):
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(2)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(2)

    parser = MSDParser()
    parse_result = parser.parse(source, filename=file_path)

    builder = MSDProjectBuilder()
    project, errors = builder.build(parse_result)

    # Print warnings and errors
    has_fatal = False
    for err in errors:
        print(str(err), file=sys.stderr)
        if err.severity == "error":
            has_fatal = True

    if has_fatal:
        print(f"Parse failed with errors.", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    output = args.output
    if not output:
        base, _ = os.path.splitext(file_path)
        output = base + ".merisio"

    if FileIO.save_project(project, output):
        print(f"Saved project to {output}")
    else:
        print(f"Error: failed to save project to {output}", file=sys.stderr)
        sys.exit(2)
```

Key design choices:

- **Lazy imports** — `MSDParser` and `MSDProjectBuilder` are imported inside the function, matching the pattern used by other commands. This avoids loading the MSD modules when running unrelated commands.
- **Errors to stderr** — all errors and warnings go to stderr, while the success message goes to stdout. This lets users pipe output cleanly.
- **Default output** — if `-o` is not specified, the output file is the input filename with a `.merisio` extension.
- **Exit codes** — follows the existing convention: 0 = success, 1 = validation/parse failure, 2 = runtime error.

### Subparser Registration

```python
# parse
parse_parser = subparsers.add_parser("parse",
    help="Parse an MSD file and convert to .merisio")
parse_parser.add_argument("-o", "--output",
    help="Output .merisio file (default: same name with .merisio extension)")
```

And in the command dispatch table:

```python
commands = {
    "info": cmd_info,
    "validate": cmd_validate,
    "sql": cmd_sql,
    "mld": cmd_mld,
    "parse": cmd_parse,
    "export": cmd_export,
}
```

### Argument Structure

The `file` positional argument comes before the subcommand, matching the existing CLI pattern:

```bash
merisio-cli <file> <command> [options]
```

This means the `parse` command accepts `.msd` files in the same `file` argument that other commands use for `.merisio` files. The description was updated to reflect this:

```python
parser.add_argument("file", help="Path to a .merisio or .msd project file")
```

## 8.2 GUI Integration

### The "Import MSD..." Menu Item

The GUI integration lives in `src/views/main_window.py`. A new menu item was added to the File menu, placed after "Open...":

```python
import_msd_action = QAction("&Import MSD...", self)
import_msd_action.triggered.connect(self._on_import_msd)
file_menu.addAction(import_msd_action)
```

The placement is deliberate — "Import" is conceptually different from "Open" (it creates a new project from a different format rather than loading an existing project file).

### The `_on_import_msd()` Method

```python
def _on_import_msd(self):
    if not self._check_save():
        return

    file_path, _ = QFileDialog.getOpenFileName(
        self, "Import MSD File", "", MSD_FILE_FILTER
    )

    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
        except OSError:
            QMessageBox.critical(
                self, "Error",
                f"Failed to read file:\n{file_path}"
            )
            return

        from ..msd import MSDParser, MSDProjectBuilder

        parser = MSDParser()
        parse_result = parser.parse(source, filename=file_path)

        builder = MSDProjectBuilder()
        project, errors = builder.build(parse_result)

        # Show errors/warnings if any
        fatal_errors = [e for e in errors if e.severity == "error"]
        warnings = [e for e in errors if e.severity == "warning"]

        if fatal_errors:
            msg = "Import failed with errors:\n\n"
            msg += "\n".join(f"- {e}" for e in fatal_errors)
            if warnings:
                msg += "\n\nWarnings:\n"
                msg += "\n".join(f"- {e}" for e in warnings)
            QMessageBox.critical(self, "Import Error", msg)
            return

        if warnings:
            msg = "Import succeeded with warnings:\n\n"
            msg += "\n".join(f"- {e}" for e in warnings)
            QMessageBox.warning(self, "Import Warnings", msg)

        self._project = project
        self._dictionary_view.set_project(self._project)
        self._mcd_canvas.set_project(self._project)
        self._mcd_canvas.apply_colors(self._project.colors)
        self._mld_view.set_project(self._project)
        self._sql_view.set_project(self._project)
        self._update_title()
        self._update_status(f"Imported MSD: {file_path}")
        self._mcd_canvas.zoom_fit()
```

The method follows the exact pattern of `_on_open()`, with these additions:

1. **File reading** — the MSD file is read as text (not loaded as JSON via `FileIO`)
2. **MSD pipeline** — the text is parsed and built through the MSD pipeline
3. **Error handling** — fatal errors are shown in a critical dialog and the import is aborted; warnings are shown in a warning dialog but the import proceeds
4. **Zoom to fit** — after import, the canvas zooms to show the entire model. This is essential because auto-layout positions may be far from the default viewport

### Error Presentation

The GUI presents errors and warnings in modal dialogs:

**Fatal errors** — shown in a `QMessageBox.critical` dialog. The import does not proceed. All errors and warnings are listed.

**Warnings only** — shown in a `QMessageBox.warning` dialog. The import proceeds normally. The user is informed about potential issues (e.g. entities without primary keys).

**No errors** — the import proceeds silently with a status bar message.

### File Filter

The file dialog uses `MSD_FILE_FILTER` from constants:

```python
MSD_FILE_FILTER = "MSD Files (*.msd);;All Files (*)"
```

This shows `.msd` files by default but allows the user to select any file type.

## 8.3 Man Page Updates

The `man/merisio-cli.1` man page was updated with:

1. **Updated description** — mentions `.msd` files alongside `.merisio`
2. **New `parse` command section** — synopsis, description, and options
3. **Updated exit status** — clarifies that exit code 1 covers both validation and parse failures
4. **New examples** — shows `parse` usage with and without `-o`

Example from the man page:

```
.SS parse
Parse an MSD (Merisio Schema Definition) file and convert it to a .merisio project.
.PP
.RS
.B merisio-cli
.I file.msd
.B parse
.RB [ \-o
.IR output ]
.RE
```

## 8.4 Integration Pattern

Both the CLI and GUI follow the same integration pattern:

```
Read source text
    ↓
MSDParser().parse(source, filename)
    ↓
MSDProjectBuilder().build(parse_result)
    ↓
Handle errors/warnings
    ↓
Use project (save/display)
```

This pattern is clean and consistent:

- The MSD modules are imported lazily (only when needed)
- Error handling is adapted to the context (stderr for CLI, dialogs for GUI)
- The resulting `Project` object is used the same way as any other project

## 8.5 Workflow Examples

### CLI: Batch Conversion

```bash
# Convert all .msd files in a directory
for f in models/*.msd; do
    merisio-cli "$f" parse -o "output/$(basename "${f%.msd}.merisio")"
done
```

### CLI: CI Pipeline

```bash
# Parse MSD and validate in one pipeline
merisio-cli schema.msd parse -o /tmp/schema.merisio
merisio-cli /tmp/schema.merisio validate
merisio-cli /tmp/schema.merisio sql -o schema.sql
```

### GUI: Visual Refinement

1. Write your model in `schema.msd`
2. Open Merisio
3. File > Import MSD... > select `schema.msd`
4. Rearrange entities manually if needed
5. File > Save As... > `schema.merisio`
6. Continue editing in the GUI
