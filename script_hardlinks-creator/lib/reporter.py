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

logger = logging.getLogger("hardlinks-creator")


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
    groups_detail = []
    for file_hash, paths in hash_groups.items():
        if len(paths) >= 2:
            groups_detail.append({
                "hash": file_hash,
                "count": len(paths),
                "files": [os.path.relpath(p, search_dir) for p in paths],
            })

    return {
        "tool": "hardlinks-creator",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "parameters": {
            "filename": filename,
            "search_directory": search_dir,
            "dry_run": dry_run,
        },
        "summary": stats,
        "groups": groups_detail,
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
