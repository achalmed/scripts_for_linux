#!/usr/bin/env python3
"""
main.py — Entry point for hardlinks-creator.

Orchestrates the four-phase pipeline:
  1. Parse CLI arguments.
  2. Validate inputs and resolve configuration.
  3. Scan the directory tree and hash files.
  4. Process groups (link or simulate).

Each phase is handled by a dedicated module so this file
reads like a high-level summary of the program's flow.

Author : Edison Achalma <achalmed.18@gmail.com>
Version: 3.0.0
"""

import os
import sys

# ---------------------------------------------------------------------------
# Bootstrap: ensure lib/ is importable regardless of working directory
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEFAULT_DIRECTORY, DEFAULT_EXCLUDED_DIRS, LOG_FILE, EXIT_INTERRUPTED
from lib.cli import build_parser
from lib.logger import get_logger, disable_colors
from lib import ui
from lib.validator import validate_directory, validate_filename
from lib.scanner import scan_files, build_exclusion_set
from lib.linker import process_groups
from lib.reporter import build_report, save_report


def main() -> None:
    args = build_parser().parse_args()

    # Phase 0: Apply global settings before any output
    if args.no_color:
        disable_colors()

    logger = get_logger(verbose=args.verbose, log_file=LOG_FILE)

    # Phase 1: Resolve configuration
    validate_filename(args.filename)

    search_dir_raw = (
        args.directory
        or DEFAULT_DIRECTORY
        or os.path.dirname(os.path.abspath(__file__))
    )
    search_dir = validate_directory(search_dir_raw)

    if args.replace_exclude is not None:
        raw_exclusions = args.replace_exclude
    else:
        raw_exclusions = list(DEFAULT_EXCLUDED_DIRS) + (args.exclude or [])

    exclusion_set = build_exclusion_set(search_dir, raw_exclusions)

    # Phase 2: Display run parameters
    ui.print_header("HARDLINKS CREATOR — ANÁLISIS COMPLETO")
    ui.print_field("Directorio", search_dir, "📁")
    ui.print_field("Archivo buscado", args.filename, "🔎")
    ui.print_field("Exclusiones", str(len(exclusion_set)) + " carpeta(s)", "🚫")
    if args.dry_run:
        ui.print_warning("MODO SIMULACIÓN: no se realizarán cambios en disco.")

    ui.print_separator()

    # Phase 3: Scan
    print(f"🔍 Escaneando directorio…\n")
    hash_groups = scan_files(search_dir, args.filename, exclusion_set)

    total_files = sum(len(v) for v in hash_groups.values())
    if total_files == 0:
        ui.print_warning(f"No se encontraron archivos con el nombre '{args.filename}'.")
        sys.exit(0)

    ui.print_success(
        f"{total_files} archivo(s) encontrado(s) con el nombre '{args.filename}'."
    )

    # Phase 4: Link
    try:
        stats = process_groups(
            hash_groups=hash_groups,
            search_dir=search_dir,
            auto_mode=args.auto,
            dry_run=args.dry_run,
        )
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Operación cancelada por el usuario.\n")
        sys.exit(EXIT_INTERRUPTED)

    ui.print_summary(stats)

    # Phase 5: Optional JSON report
    if args.report_json:
        report = build_report(
            stats=stats,
            filename=args.filename,
            search_dir=search_dir,
            dry_run=args.dry_run,
            hash_groups=hash_groups,
        )
        save_report(report, args.report_json)

    sys.exit(1 if stats["errors"] > 0 else 0)


if __name__ == "__main__":
    main()
