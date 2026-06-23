"""
lib/linker.py — Safe hard link creation for hardlinks-creator.

BUG FIX (original): The original script called os.remove() before os.link(),
meaning a failed os.link() would permanently destroy the target file.
This module fixes that by using an atomic rename-based approach:
  1. Rename the target to a .bak temp file (atomic on same filesystem).
  2. Attempt os.link(source, target).
  3. If link succeeds → remove the .bak.
  4. If link fails → restore the .bak to its original path.
The file is never left in a destroyed state.
"""

import os
import logging
from collections import defaultdict
from typing import Dict, List, Tuple

from lib import ui
from lib.validator import validate_write_permission, same_filesystem

logger = logging.getLogger("hardlinks-creator")


# ---------------------------------------------------------------------------
# Inode grouping helpers
# ---------------------------------------------------------------------------

def _group_by_inode(file_list: List[str]) -> Dict[int, List[str]]:
    """
    Groups a list of paths by their inode number.

    Paths that already share an inode are already hard links;
    we use the first inode group as the 'source' and all other
    unique inodes as candidates for re-linking.

    Args:
        file_list: Absolute paths of files with identical content.

    Returns:
        Dict mapping inode → [list of paths].
    """
    groups: Dict[int, List[str]] = defaultdict(list)
    for path in file_list:
        inode = _safe_inode(path)
        if inode is not None:
            groups[inode].append(path)
    return groups


def _safe_inode(path: str) -> int | None:
    try:
        return os.stat(path).st_ino
    except OSError as exc:
        logger.warning(f"stat falló para '{path}': {exc}")
        return None


# ---------------------------------------------------------------------------
# Atomic link operation
# ---------------------------------------------------------------------------

def _atomic_link(source: str, target: str) -> bool:
    """
    Replaces 'target' with a hard link to 'source' without data loss.

    Strategy: rename target → target.hltmp (atomic), then link.
    If linking fails, the .hltmp rename is reversed.

    Args:
        source: The file to link from (content is preserved).
        target: The path to replace with a hard link.

    Returns:
        True on success, False on any failure.
    """
    tmp_path = target + ".hltmp"
    try:
        os.rename(target, tmp_path)       # atomic on same filesystem
    except OSError as exc:
        logger.error(f"No se pudo preparar '{target}' para enlace: {exc}")
        return False

    try:
        os.link(source, target)
        os.remove(tmp_path)               # clean up backup only after success
        return True
    except OSError as exc:
        logger.error(f"No se pudo crear hard link '{target}': {exc}")
        # Restore original file — never leave the user with missing data
        try:
            os.rename(tmp_path, target)
        except OSError as restore_exc:
            logger.error(
                f"CRÍTICO: no se pudo restaurar '{target}' desde '{tmp_path}'. "
                f"Recupera manualmente el archivo: {restore_exc}"
            )
        return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def process_groups(
    hash_groups: Dict[str, List[str]],
    search_dir: str,
    auto_mode: bool,
    dry_run: bool,
) -> dict:
    """
    Iterates over hash groups and creates hard links as appropriate.

    For each group with ≥2 members:
      - Identifies existing links (same inode) and new candidates.
      - Asks user confirmation unless auto_mode or dry_run.
      - Calls _atomic_link for each candidate (unless dry_run).

    Args:
        hash_groups: Output from scanner.scan_files().
        search_dir:  Root directory (used for relative path display).
        auto_mode:   Skip confirmation prompts.
        dry_run:     Simulate without making changes.

    Returns:
        Stats dict with keys: groups_found, groups_created, groups_skipped,
        links_created, files_skipped, errors.
    """
    stats = dict(
        groups_found=0, groups_created=0, groups_skipped=0,
        links_created=0, files_skipped=0, errors=0,
    )

    linkable = [(h, paths) for h, paths in hash_groups.items() if len(paths) >= 2]
    stats["groups_found"] = len(linkable)

    if not linkable:
        ui.print_info("Todos los archivos tienen contenido único. No hay candidatos.")
        return stats

    ui.print_success(f"Se encontraron {stats['groups_found']} grupo(s) con contenido idéntico.\n")

    for group_num, (file_hash, file_list) in enumerate(linkable, start=1):
        ui.print_separator()
        ui.print_group_header(group_num, file_hash)

        inode_groups = _group_by_inode(file_list)
        if not inode_groups:
            stats["errors"] += 1
            continue

        # The first inode group provides the source file
        source_inode, source_group = next(iter(inode_groups.items()))
        source_path = source_group[0]

        already_linked = source_group[1:]          # same inode as source
        candidates = [                              # different inode → need linking
            p for inode, paths in inode_groups.items()
            if inode != source_inode
            for p in paths
        ]

        file_size = _safe_stat_size(source_path)
        size_str = ui.format_size(file_size) if file_size is not None else "?"
        rel = lambda p: os.path.relpath(p, search_dir)

        ui.print_field("Archivo fuente", rel(source_path), "📌")
        print(f"   Tamaño: {size_str} | Inodo: {source_inode}\n")

        if already_linked:
            ui.print_skip(f"Ya enlazados ({len(already_linked)}):")
            for p in already_linked:
                print(f"   • {rel(p)}")
            print()
            stats["files_skipped"] += len(already_linked)

        if not candidates:
            ui.print_info("Todos los archivos de este grupo ya están enlazados.")
            continue

        print(f"📋 Candidatos a enlazar ({len(candidates)}):")
        for i, p in enumerate(candidates, 1):
            print(f"   {i}. {rel(p)}")
        print()

        # Cross-filesystem guard: warn and skip incompatible candidates
        valid_candidates = []
        for p in candidates:
            if not same_filesystem(source_path, p):
                ui.print_warning(
                    f"'{rel(p)}' está en un sistema de archivos diferente. Omitido."
                )
                stats["errors"] += 1
            elif not validate_write_permission(p):
                ui.print_warning(f"Sin permisos de escritura en '{rel(p)}'. Omitido.")
                stats["errors"] += 1
            else:
                valid_candidates.append(p)

        if not valid_candidates:
            stats["groups_skipped"] += 1
            continue

        if dry_run:
            ui.print_info(f"[SIMULACIÓN] Se crearían {len(valid_candidates)} hard link(s).")
            stats["links_created"] += len(valid_candidates)
            stats["groups_created"] += 1
            continue

        if not auto_mode and not ui.confirm_group(group_num):
            ui.print_warning("Grupo omitido por el usuario.")
            stats["groups_skipped"] += 1
            continue

        # --- Perform linking ---
        success = 0
        for target in valid_candidates:
            if _atomic_link(source_path, target):
                ui.print_success(f"Hard link creado: {rel(target)}")
                success += 1
            else:
                stats["errors"] += 1

        stats["links_created"] += success
        if success > 0:
            stats["groups_created"] += 1

    return stats


def _safe_stat_size(path: str) -> int | None:
    try:
        return os.stat(path).st_size
    except OSError:
        return None
