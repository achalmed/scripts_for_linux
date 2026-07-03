"""
lib/batch.py — Batch list parsing for hardlinks-creator.

Reads a plain-text file containing one filename per line and returns
a clean, ordered list ready for the pipeline. This module only deals
with the listado itself (reading, cleaning, deduplication); it knows
nothing about hashing or hard links.

Formato del archivo batch:
    # Las líneas que comienzan con '#' son comentarios
    _metadata.yml

    README.md        # (las líneas vacías se ignoran)
"""

import logging
import os
import sys
from typing import List

from config import EXIT_BAD_ARGS, EXIT_NOT_FOUND, EXIT_NO_PERMISSION

logger = logging.getLogger("hardlinks-creator")

COMMENT_PREFIX = "#"


def read_batch_file(path: str) -> List[str]:
    """
    Parses a batch file into an ordered list of unique filenames.

    Cleaning rules, applied per line:
      - strip leading/trailing whitespace
      - skip empty lines
      - skip lines starting with '#' (comments)
      - skip duplicates, keeping the first occurrence

    Args:
        path: Path to the batch file (one filename per line).

    Returns:
        List of filenames in file order, without duplicates.

    Raises:
        SystemExit(3): Batch file does not exist.
        SystemExit(4): Batch file exists but cannot be read.
        SystemExit(2): Batch file contains no usable filenames.
    """
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        logger.error(f"El archivo batch '{abs_path}' no existe.")
        sys.exit(EXIT_NOT_FOUND)

    try:
        with open(abs_path, encoding="utf-8") as f:
            raw_lines = f.readlines()
    except OSError as exc:
        logger.error(f"No se pudo leer el archivo batch '{abs_path}': {exc}")
        sys.exit(EXIT_NO_PERMISSION)

    filenames: List[str] = []
    seen: set[str] = set()
    duplicates = 0

    for line in raw_lines:
        name = line.strip()
        if not name or name.startswith(COMMENT_PREFIX):
            continue
        if name in seen:
            duplicates += 1
            logger.debug(f"Nombre duplicado ignorado en el listado: '{name}'")
            continue
        seen.add(name)
        filenames.append(name)

    if duplicates:
        logger.info(f"{duplicates} nombre(s) duplicado(s) ignorado(s) en el listado.")

    if not filenames:
        logger.error(f"El archivo batch '{abs_path}' no contiene nombres válidos.")
        sys.exit(EXIT_BAD_ARGS)

    return filenames
