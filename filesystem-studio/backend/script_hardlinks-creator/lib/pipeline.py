"""
lib/pipeline.py — Single-filename pipeline for hardlinks-creator.

Encapsulates the scan → group → link flow for ONE filename so the
exact same code path serves both execution modes:

  - single mode: main.py calls process_filename() once
  - batch mode : main.py iterates the list from lib/batch.py and
                 calls process_filename() per entry

Presentation that differs between modes (headers, per-file progress,
summaries) stays in main.py; this module only runs the pipeline.
"""

import logging
from typing import Dict, List, Set, Tuple

from lib import ui
from lib.linker import process_groups
from lib.scanner import scan_files

logger = logging.getLogger("hardlinks-creator")


def empty_stats() -> dict:
    """Returns a zeroed stats dict with the same keys as linker.process_groups()."""
    return dict(
        groups_found=0, groups_created=0, groups_skipped=0,
        links_created=0, files_skipped=0, errors=0,
    )


def process_filename(
    filename: str,
    search_dir: str,
    exclusion_set: Set[str],
    auto_mode: bool,
    dry_run: bool,
) -> Tuple[dict, Dict[str, List[str]]]:
    """
    Runs the complete pipeline for a single filename.

    Args:
        filename:      Exact filename to search for.
        search_dir:    Validated absolute root directory.
        exclusion_set: Absolute paths to skip (from scanner.build_exclusion_set).
        auto_mode:     Skip interactive confirmation prompts.
        dry_run:       Simulate without touching the disk.

    Returns:
        (stats, hash_groups) — stats from linker.process_groups()
        (all-zero when no file matched) and the raw scan groups,
        needed by reporter.py for the JSON report.
    """
    print("🔍 Escaneando directorio…\n")
    hash_groups = scan_files(search_dir, filename, exclusion_set)

    total_files = sum(len(v) for v in hash_groups.values())
    if total_files == 0:
        ui.print_warning(f"No se encontraron archivos con el nombre '{filename}'.")
        return empty_stats(), {}

    ui.print_success(
        f"{total_files} archivo(s) encontrado(s) con el nombre '{filename}'."
    )

    stats = process_groups(
        hash_groups=hash_groups,
        search_dir=search_dir,
        auto_mode=auto_mode,
        dry_run=dry_run,
    )
    return stats, hash_groups
