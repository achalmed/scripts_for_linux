"""Input, option and dependency validation for firma-digital.

Everything is checked before any work starts so failures happen early,
with actionable Spanish messages and the project's exit codes. In
--dry-run mode missing dependencies degrade to warnings so the plan can
still be inspected on a machine that lacks the libraries.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from logging import Logger
from pathlib import Path
from typing import Optional

import config


def validate_dependencies(dry_run: bool, logger: Logger) -> bool:
    """Verifies the required Python libraries are importable.

    Real runs exit with EXIT_DEPENDENCY on the first missing library; dry
    runs downgrade to warnings so the plan is still shown.

    Returns:
        True if every dependency is present; False (dry-run only) otherwise.
    """
    missing = [(name, hint) for name, hint in config.DEPENDENCIES.items()
               if importlib.util.find_spec(name) is None]
    if not missing:
        return True
    report = logger.warning if dry_run else logger.error
    for name, hint in missing:
        report("Falta la dependencia '%s' (instálala con: %s).", name, hint)
    if not dry_run:
        sys.exit(config.EXIT_DEPENDENCY)
    logger.warning("Simulación: se continúa aunque falten dependencias.")
    return False


def validate_input(raw: Optional[str], logger: Logger) -> Path:
    """Ensures the input photo was given, exists, is a file and is readable."""
    if not raw:
        logger.error("Falta la foto de entrada. Usa --help para ver el uso.")
        sys.exit(config.EXIT_USAGE)
    path = Path(raw).expanduser()
    if not path.exists():
        logger.error("El archivo '%s' no existe.", path)
        sys.exit(config.EXIT_NOT_FOUND)
    if path.is_dir():
        logger.error("'%s' es un directorio; se esperaba un archivo.", path)
        sys.exit(config.EXIT_USAGE)
    if not os.access(path, os.R_OK):
        logger.error("Sin permisos para leer '%s'.", path)
        sys.exit(config.EXIT_PERMISSION)
    return path


def resolve_output_dir(raw: Optional[str], input_path: Path,
                       dry_run: bool, logger: Logger) -> Path:
    """Resolves and prepares the output directory (defaults to the photo's)."""
    out_dir = Path(raw).expanduser() if raw else input_path.parent
    return _ensure_writable_dir(out_dir, dry_run, logger)


def resolve_qa_dir(raw: Optional[str], dry_run: bool,
                   logger: Logger) -> Optional[Path]:
    """Resolves the optional QA directory, or None when --qa-dir is absent."""
    if raw is None:
        return None
    return _ensure_writable_dir(Path(raw).expanduser(), dry_run, logger)


def _ensure_writable_dir(out_dir: Path, dry_run: bool, logger: Logger) -> Path:
    """Creates the directory if needed and verifies it is writable."""
    if out_dir.exists():
        if not out_dir.is_dir():
            logger.error("'%s' existe y no es un directorio.", out_dir)
            sys.exit(config.EXIT_USAGE)
        if not os.access(out_dir, os.W_OK):
            logger.error("Sin permisos de escritura en '%s'.", out_dir)
            sys.exit(config.EXIT_PERMISSION)
        return out_dir
    if dry_run:
        logger.info("[SIMULACIÓN] Se crearía el directorio '%s'.", out_dir)
        return out_dir
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error("Sin permisos para crear el directorio '%s'.", out_dir)
        sys.exit(config.EXIT_PERMISSION)
    return out_dir
