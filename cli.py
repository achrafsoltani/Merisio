#!/usr/bin/env python3
"""Merisio CLI — validate, generate SQL, view MLD, and export diagrams from .merisio files."""

import argparse
import os
import sys


def load_project(file_path):
    """Load a .merisio project file, exiting on failure."""
    from src.utils.file_io import FileIO

    if not os.path.isfile(file_path):
        print(f"Error: file not found: {file_path}", file=sys.stderr)
        sys.exit(2)

    project = FileIO.load_project(file_path)
    if project is None:
        print(f"Error: failed to load project: {file_path}", file=sys.stderr)
        sys.exit(2)

    return project


def cmd_info(args):
    """Show project metadata and statistics."""
    from src.controllers.mcd_controller import MCDController

    project = load_project(args.file)
    controller = MCDController(project)
    stats = controller.get_statistics()

    print(f"Project:      {project.name}")
    print(f"Author:       {project.author or '(none)'}")
    print(f"Description:  {project.description or '(none)'}")
    print(f"Created:      {project.created_at}")
    print(f"Modified:     {project.modified_at}")
    print(f"Entities:     {stats['entities']}")
    print(f"Associations: {stats['associations']}")
    print(f"Links:        {stats['links']}")
    print(f"Attributes:   {stats['attributes']}")


def cmd_validate(args):
    """Validate the MCD model."""
    from src.controllers.mcd_controller import MCDController

    project = load_project(args.file)
    controller = MCDController(project)
    errors = controller.validate()

    if errors:
        print(f"Validation failed with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("Validation passed. No errors found.")


def cmd_sql(args):
    """Generate PostgreSQL DDL."""
    from src.controllers.sql_generator import SQLGenerator

    project = load_project(args.file)
    generator = SQLGenerator(project)
    sql = generator.generate()

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(sql)
            print(f"SQL written to {args.output}")
        except OSError as e:
            print(f"Error writing file: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        print(sql)


def cmd_mld(args):
    """Show the logical data model (MLD tables)."""
    from src.controllers.mld_transformer import MLDTransformer

    project = load_project(args.file)
    transformer = MLDTransformer(project)
    tables = transformer.transform()

    if not tables:
        print("No tables generated.")
        return

    for table in tables:
        pk_cols = [c.name for c in table.columns if c.is_primary_key]
        fk_cols = [c for c in table.columns if c.is_foreign_key]

        print(f"{table.name} ({table.source_type})")

        for col in table.columns:
            flags = []
            if col.is_primary_key:
                flags.append("PK")
            if col.is_foreign_key:
                flags.append(f"FK -> {col.references_table}.{col.references_column}")
            if not col.is_nullable:
                flags.append("NOT NULL")

            flag_str = f"  [{', '.join(flags)}]" if flags else ""
            print(f"  {col.name} {col.data_type}{flag_str}")

        print()


def cmd_export(args):
    """Export diagram to PNG, SVG, or PDF."""
    # QGraphicsScene requires QApplication (not QGuiApplication)
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    from src.export.renderer import HeadlessRenderer

    project = load_project(args.file)

    if not args.output:
        print("Error: export requires -o / --output", file=sys.stderr)
        sys.exit(2)

    renderer = HeadlessRenderer(project)
    fmt = args.format.lower()

    if fmt == "png":
        ok = renderer.export_png(args.output, scale=args.scale)
    elif fmt == "svg":
        ok = renderer.export_svg(args.output)
    elif fmt == "pdf":
        ok = renderer.export_pdf(args.output)
    else:
        print(f"Error: unsupported format: {args.format}", file=sys.stderr)
        sys.exit(2)

    if ok:
        print(f"Exported {fmt.upper()} to {args.output}")
    else:
        print(f"Error: export failed (empty diagram or write error)", file=sys.stderr)
        sys.exit(2)


def main():
    from src.utils.constants import APP_VERSION

    parser = argparse.ArgumentParser(
        prog="merisio-cli",
        description="Merisio CLI — work with .merisio project files from the command line.",
    )
    parser.add_argument("--version", action="version", version=f"merisio-cli {APP_VERSION}")
    parser.add_argument("file", help="Path to a .merisio project file")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # info
    subparsers.add_parser("info", help="Show project metadata and statistics")

    # validate
    subparsers.add_parser("validate", help="Validate the MCD model")

    # sql
    sql_parser = subparsers.add_parser("sql", help="Generate PostgreSQL DDL")
    sql_parser.add_argument("-o", "--output", help="Write SQL to file instead of stdout")

    # mld
    subparsers.add_parser("mld", help="Show the logical data model (MLD tables)")

    # export
    export_parser = subparsers.add_parser("export", help="Export diagram to PNG, SVG, or PDF")
    export_parser.add_argument("--format", required=True, choices=["png", "svg", "pdf"],
                               help="Export format")
    export_parser.add_argument("-o", "--output", required=True, help="Output file path")
    export_parser.add_argument("--scale", type=float, default=2.0,
                               help="Scale factor for PNG export (default: 2.0)")

    args = parser.parse_args()

    commands = {
        "info": cmd_info,
        "validate": cmd_validate,
        "sql": cmd_sql,
        "mld": cmd_mld,
        "export": cmd_export,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
