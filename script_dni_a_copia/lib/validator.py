"""Input, option and dependency validation for dni-a-copia.

Everything is checked before any image is processed so failures happen
early, with actionable Spanish messages and the project's exit codes. In
--dry-run mode a missing LibreOffice degrades to a warning so the plan can
still be inspected.
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from logging import Logger
from pathlib import Path
from typing import Tuple

import config

# Third-party modules the image pipeline cannot run without.
_REQUIRED_MODULES = {
    "numpy": "numpy",
    "scipy": "scipy",
    "PIL": "Pillow",
    "docx": "python-docx",
}


def validate_dependencies(to_pdf: bool, dry_run: bool, logger: Logger) -> None:
    """Checks Python packages (always) and LibreOffice (only if --to-pdf)."""
    missing = [pip_name for mod, pip_name in _REQUIRED_MODULES.items()
               if importlib.util.find_spec(mod) is None]
    if missing:
        logger.error("Faltan dependencias de Python: %s "
                     "(instálalas con: pip install %s).",
                     ", ".join(missing), " ".join(missing))
        sys.exit(config.EXIT_DEPENDENCY)
    if to_pdf:
        _validate_soffice(dry_run, logger)


def _validate_soffice(dry_run: bool, logger: Logger) -> None:
    """LibreOffice is required to export the .docx to PDF."""
    if any(shutil.which(name) for name in config.SOFFICE_CANDIDATES):
        return
    message = ("Falta LibreOffice para exportar a PDF "
               "(instálalo con: sudo apt install libreoffice).")
    if dry_run:
        logger.warning(message)
        logger.warning("Simulación: se continúa aunque falte LibreOffice.")
    else:
        logger.error(message)
        sys.exit(config.EXIT_DEPENDENCY)


def validate_inputs(front: str, back: str,
                    logger: Logger) -> Tuple[Path, Path]:
    """Verifies the two image paths exist and are readable."""
    return (_validate_one_input(front, "anverso", logger),
            _validate_one_input(back, "reverso", logger))


def _validate_one_input(raw: str, label: str, logger: Logger) -> Path:
    """Exits on a missing or unreadable image: a clear early failure."""
    path = Path(raw).expanduser()
    if not path.is_file():
        logger.error("No existe la imagen del %s: '%s'.", label, path)
        sys.exit(config.EXIT_NOT_FOUND)
    if not os.access(path, os.R_OK):
        logger.error("Sin permisos para leer el %s: '%s'.", label, path)
        sys.exit(config.EXIT_PERMISSION)
    return path


def validate_output_dir(raw: str, dry_run: bool, logger: Logger) -> Path:
    """Ensures the output directory exists (creating it) and is writable."""
    out_dir = Path(raw).expanduser()
    if out_dir.exists():
        if not out_dir.is_dir():
            logger.error("'%s' existe y no es un directorio.", out_dir)
            sys.exit(config.EXIT_USAGE)
        if not os.access(out_dir, os.W_OK):
            logger.error("Sin permisos de escritura en '%s'.", out_dir)
            sys.exit(config.EXIT_PERMISSION)
        return out_dir
    if dry_run:
        logger.info("[SIMULACIÓN] Se crearía el directorio de salida '%s'.",
                    out_dir)
        return out_dir
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error("Sin permisos para crear el directorio '%s'.", out_dir)
        sys.exit(config.EXIT_PERMISSION)
    return out_dir


def validate_dpi(dpi: int, logger: Logger) -> int:
    """Keeps DPI within a sane print range."""
    if not config.MIN_DPI <= dpi <= config.MAX_DPI:
        logger.error("DPI fuera de rango: %d (admitido %d-%d).",
                     dpi, config.MIN_DPI, config.MAX_DPI)
        sys.exit(config.EXIT_USAGE)
    return dpi
