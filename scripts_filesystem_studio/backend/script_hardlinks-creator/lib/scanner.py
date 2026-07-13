"""
lib/scanner.py — File discovery and hash-based grouping for hardlinks-creator.

Separating the scan phase from the link-creation phase makes each
independently testable and allows dry-run to reuse the same scanner
without any conditional branching in the main flow.
"""

import hashlib
import os
import logging
from collections import defaultdict
from typing import Dict, List, Set

from config import HASH_BLOCK_SIZE

logger = logging.getLogger("hardlinks-creator")


def build_exclusion_set(search_dir: str, raw_exclusions: List[str]) -> Set[str]:
    """
    Normalizes the exclusion list into a set of absolute paths.

    Using absolute normalized paths avoids false matches from
    directory names that happen to appear in unrelated path segments.

    Args:
        search_dir:     The root directory being scanned.
        raw_exclusions: Relative or partial paths to exclude.

    Returns:
        Set of absolute, normalized path strings.
    """
    return {
        os.path.normpath(os.path.join(search_dir, entry))
        for entry in raw_exclusions
    }


def compute_sha256(filepath: str) -> str | None:
    """
    Computes the SHA-256 digest of a file using block-by-block reading.

    Reading in HASH_BLOCK_SIZE chunks keeps memory usage constant
    regardless of file size — important for large PDF/dataset files.

    Args:
        filepath: Absolute path to the file.

    Returns:
        Hex digest string, or None on I/O error.
    """
    hasher = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for block in iter(lambda: f.read(HASH_BLOCK_SIZE), b""):
                hasher.update(block)
        return hasher.hexdigest()
    except OSError as exc:
        logger.warning(f"No se pudo calcular hash de '{filepath}': {exc}")
        return None


def get_inode(filepath: str) -> int | None:
    """
    Returns the inode number of a file.

    Inodes are the ground truth for detecting existing hard links —
    two paths sharing an inode are already linked.

    Args:
        filepath: Absolute file path.

    Returns:
        Inode integer, or None on stat error.
    """
    try:
        return os.stat(filepath).st_ino
    except OSError as exc:
        logger.warning(f"No se pudo leer inodo de '{filepath}': {exc}")
        return None


def scan_files(
    search_dir: str,
    filename: str,
    exclusion_set: Set[str],
) -> Dict[str, List[str]]:
    """
    Walks the directory tree and groups matching files by content hash.

    The walk is top-down so that excluded directories are pruned
    before descending, avoiding wasted I/O.

    Only groups with two or more members are useful for linking,
    but filtering is left to the caller (linker.py) so this function
    remains a pure data-gathering step.

    Args:
        search_dir:    Root directory to scan.
        filename:      Exact filename to match (case-sensitive).
        exclusion_set: Set of absolute paths to skip.

    Returns:
        Dict mapping SHA-256 hex digest → list of absolute file paths.
    """
    hash_groups: Dict[str, List[str]] = defaultdict(list)
    total_found = 0

    for root, dirs, files in os.walk(search_dir, topdown=True):
        # Prune excluded dirs in-place so os.walk won't descend into them
        dirs[:] = [
            d for d in dirs
            if os.path.normpath(os.path.join(root, d)) not in exclusion_set
        ]

        if filename not in files:
            continue

        filepath = os.path.join(root, filename)
        total_found += 1
        file_hash = compute_sha256(filepath)

        if file_hash is not None:
            hash_groups[file_hash].append(filepath)

    logger.debug(f"Escaneado completado: {total_found} archivo(s) encontrado(s).")
    return hash_groups
