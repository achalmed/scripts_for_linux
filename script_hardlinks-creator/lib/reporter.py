"""
lib/reporter.py — JSON report export for hardlinks-creator.

NEW FEATURE: Exports a machine-readable summary of the operation
so CI pipelines, Quarto automation scripts, or external tools can
consume results without parsing terminal output.

Useful when running hardlinks-creator from cron or GitHub Actions
to track how many duplicates were eliminated across publication cycles.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, List

from config import VERSION

logger = logging.getLogger("hardlinks-creator")


def _groups_detail(hash_groups: Dict[str, List[str]], search_dir: str) -> List[dict]:
    """Serializes linkable groups (≥2 members) with paths relative to search_dir."""
    return [
        {
            "hash": file_hash,
            "count": len(paths),
            "files": [os.path.relpath(p, search_dir) for p in paths],
        }
        for file_hash, paths in hash_groups.items()
        if len(paths) >= 2
    ]


def build_report(
    stats: dict,
    filename: str,
    search_dir: str,
    dry_run: bool,
    hash_groups: Dict[str, List[str]],
) -> dict:
    """
    Assembles a structured report dictionary from an operation's results.

    Args:
        stats:       Stats dict returned by linker.process_groups().
        filename:    The filename that was searched.
        search_dir:  Root directory that was scanned.
        dry_run:     Whether the run was a simulation.
        hash_groups: Raw groups from scanner for group detail section.

    Returns:
        Dict ready for json.dumps().
    """
    return {
        "tool": "hardlinks-creator",
        "version": VERSION,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "parameters": {
            "filename": filename,
            "search_directory": search_dir,
            "dry_run": dry_run,
        },
        "summary": stats,
        "groups": _groups_detail(hash_groups, search_dir),
    }


def build_batch_report(
    batch_file: str,
    search_dir: str,
    dry_run: bool,
    files_processed: int,
    total_stats: dict,
    elapsed_seconds: float,
    runs: List[dict],
    failures: List[tuple],
) -> dict:
    """
    Assembles a structured report for a batch run: one aggregated
    summary plus a per-filename breakdown.

    Args:
        batch_file:      Path of the batch list that was processed.
        search_dir:      Root directory that was scanned.
        dry_run:         Whether the run was a simulation.
        files_processed: Total filenames attempted (valid or not).
        total_stats:     Aggregated stats across all filenames.
        elapsed_seconds: Wall-clock duration of the whole batch.
        runs:            Per-file dicts with keys: filename, stats, hash_groups.
        failures:        List of (filename, message) tuples.

    Returns:
        Dict ready for json.dumps().
    """
    return {
        "tool": "hardlinks-creator",
        "version": VERSION,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": "batch",
        "parameters": {
            "batch_file": os.path.abspath(batch_file),
            "search_directory": search_dir,
            "dry_run": dry_run,
        },
        "summary": {
            **total_stats,
            "files_processed": files_processed,
            "files_failed": len(failures),
            "elapsed_seconds": round(elapsed_seconds, 2),
        },
        "runs": [
            {
                "filename": run["filename"],
                "summary": run["stats"],
                "groups": _groups_detail(run["hash_groups"], search_dir),
            }
            for run in runs
        ],
        "errors": [
            {"filename": name, "message": message} for name, message in failures
        ],
    }


def save_report(report: dict, output_path: str) -> None:
    """
    Writes the report dict as pretty-printed JSON.

    Creates parent directories if they don't exist so the caller
    can pass paths like '/tmp/reports/run-001.json' without pre-creating them.

    Args:
        report:      Dict built by build_report().
        output_path: Destination file path.

    Raises:
        SystemExit(1) on write failure (logged before exit).
    """
    import sys
    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Reporte JSON guardado en: {output_path}")
    except OSError as exc:
        logger.error(f"No se pudo guardar el reporte en '{output_path}': {exc}")
        sys.exit(1)
