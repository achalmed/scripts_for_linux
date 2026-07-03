#!/usr/bin/env python3
"""
main.py — Entry point for hardlinks-creator.

Two execution modes share the exact same pipeline:

  Single : python main.py _metadata.yml
  Batch  : python main.py --batch archivos.txt

Flow:
  1. Parse CLI arguments (lib/cli.py).
  2. Validate inputs and resolve configuration once.
  3. Dispatch to run_single() or run_batch(); both delegate the real
     work to lib/pipeline.process_filename(), which chains
     scanner → linker. lib/batch.py only parses the batch list.
  4. Print summary and optional JSON report (lib/reporter.py).

Each phase is handled by a dedicated module so this file
reads like a high-level summary of the program's flow.

Author : Edison Achalma <achalmed.18@gmail.com>
Version: 3.1.0
"""

import os
import sys
import time
from typing import Set

# ---------------------------------------------------------------------------
# Bootstrap: ensure lib/ is importable regardless of working directory
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    DEFAULT_DIRECTORY,
    DEFAULT_EXCLUDED_DIRS,
    LOG_FILE,
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_INTERRUPTED,
)
from lib.cli import build_parser
from lib.logger import get_logger, disable_colors
from lib import ui
from lib.validator import validate_directory, validate_filename, is_valid_filename
from lib.scanner import build_exclusion_set
from lib.pipeline import process_filename, empty_stats
from lib.batch import read_batch_file
from lib.reporter import build_report, build_batch_report, save_report


def run_single(args, search_dir: str, exclusion_set: Set[str]) -> int:
    """
    Original single-filename mode: one pipeline run, full summary,
    optional JSON report.

    Returns:
        Exit code (EXIT_ERROR if any link operation failed).
    """
    validate_filename(args.filename)

    ui.print_header("HARDLINKS CREATOR — ANÁLISIS COMPLETO")
    ui.print_field("Directorio", search_dir, "📁")
    ui.print_field("Archivo buscado", args.filename, "🔎")
    ui.print_field("Exclusiones", f"{len(exclusion_set)} carpeta(s)", "🚫")
    if args.dry_run:
        ui.print_warning("MODO SIMULACIÓN: no se realizarán cambios en disco.")
    ui.print_separator()

    stats, hash_groups = process_filename(
        filename=args.filename,
        search_dir=search_dir,
        exclusion_set=exclusion_set,
        auto_mode=args.auto,
        dry_run=args.dry_run,
    )
    if not hash_groups:
        return EXIT_SUCCESS

    ui.print_summary(stats)

    if args.report_json:
        report = build_report(
            stats=stats,
            filename=args.filename,
            search_dir=search_dir,
            dry_run=args.dry_run,
            hash_groups=hash_groups,
        )
        save_report(report, args.report_json)

    return EXIT_ERROR if stats["errors"] > 0 else EXIT_SUCCESS


def run_batch(args, search_dir: str, exclusion_set: Set[str], logger) -> int:
    """
    Batch mode: runs the single-file pipeline for every name in the
    batch list. A failure in one entry is recorded and the batch
    continues with the next one.

    Returns:
        Exit code (EXIT_ERROR if any entry failed).
    """
    filenames = read_batch_file(args.batch)
    total = len(filenames)

    ui.print_header("HARDLINKS CREATOR — MODO BATCH")
    ui.print_field("Directorio", search_dir, "📁")
    ui.print_field("Listado", os.path.abspath(args.batch), "📄")
    ui.print_field("Archivos encontrados", str(total), "🔎")
    ui.print_field("Exclusiones", f"{len(exclusion_set)} carpeta(s)", "🚫")
    if args.dry_run:
        ui.print_warning("MODO SIMULACIÓN: no se realizarán cambios en disco.")
    ui.print_separator()

    total_stats = empty_stats()
    runs = []       # per-file results for the JSON report
    failures = []   # (filename, message) — shown at the end
    start = time.perf_counter()

    for index, filename in enumerate(filenames, start=1):
        ui.print_batch_item(index, total, filename)

        if not is_valid_filename(filename):
            message = "Nombre inválido: no debe contener rutas."
            ui.print_error(message)
            failures.append((filename, message))
            continue

        try:
            stats, hash_groups = process_filename(
                filename=filename,
                search_dir=search_dir,
                exclusion_set=exclusion_set,
                auto_mode=args.auto,
                dry_run=args.dry_run,
            )
        except OSError as exc:
            logger.error(f"Fallo procesando '{filename}': {exc}")
            failures.append((filename, str(exc)))
            continue

        if not hash_groups:
            failures.append((filename, "No encontrado en el directorio."))
            continue

        for key in total_stats:
            total_stats[key] += stats[key]
        if stats["errors"] > 0:
            failures.append(
                (filename, f"{stats['errors']} error(es) durante el enlace.")
            )

        runs.append(
            {"filename": filename, "stats": stats, "hash_groups": hash_groups}
        )

    elapsed = time.perf_counter() - start

    ui.print_batch_summary(
        processed=total,
        failed=len(failures),
        elapsed_seconds=elapsed,
        total_stats=total_stats,
        failures=failures,
    )

    if args.report_json:
        report = build_batch_report(
            batch_file=args.batch,
            search_dir=search_dir,
            dry_run=args.dry_run,
            files_processed=total,
            total_stats=total_stats,
            elapsed_seconds=elapsed,
            runs=runs,
            failures=failures,
        )
        save_report(report, args.report_json)

    return EXIT_ERROR if failures else EXIT_SUCCESS


def main() -> None:
    args = build_parser().parse_args()

    # Phase 0: Apply global settings before any output
    if args.no_color:
        disable_colors()

    logger = get_logger(verbose=args.verbose, log_file=LOG_FILE)

    # Phase 1: Resolve configuration shared by both modes
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

    # Phase 2: Dispatch to the selected mode
    try:
        if args.batch:
            exit_code = run_batch(args, search_dir, exclusion_set, logger)
        else:
            exit_code = run_single(args, search_dir, exclusion_set)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario.\n")
        sys.exit(EXIT_INTERRUPTED)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
