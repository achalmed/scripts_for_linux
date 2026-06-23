"""
lib/validator.py — Input and environment validation for hardlinks-creator.

All checks that can abort the program early live here.
Centralizing them prevents the business logic from being
cluttered with guard clauses.
"""

import os
import sys
import logging

logger = logging.getLogger("hardlinks-creator")


def validate_directory(path: str) -> str:
    """
    Ensures the target directory exists and is readable.

    Resolving to an absolute path here prevents subtle bugs
    from relative paths changing meaning after os.chdir().

    Args:
        path: Raw directory path from config or CLI.

    Returns:
        Absolute, validated path string.

    Raises:
        SystemExit(3): Directory does not exist.
        SystemExit(4): Directory exists but is not readable.
    """
    abs_path = os.path.abspath(path)
    if not os.path.isdir(abs_path):
        logger.error(f"El directorio '{abs_path}' no existe.")
        sys.exit(3)
    if not os.access(abs_path, os.R_OK):
        logger.error(f"Sin permisos de lectura en '{abs_path}'.")
        sys.exit(4)
    return abs_path


def validate_filename(filename: str) -> None:
    """
    Rejects filenames that contain path separators or are empty.

    A filename like '../../../etc/passwd' passed as the search
    target would traverse upward unexpectedly.

    Args:
        filename: The raw filename argument from the CLI.

    Raises:
        SystemExit(2): Filename is invalid.
    """
    if not filename or os.sep in filename:
        logger.error(
            f"Nombre de archivo inválido: '{filename}'. "
            "Proporciona solo el nombre, sin rutas (ej. '_metadata.yml')."
        )
        sys.exit(2)


def validate_write_permission(path: str) -> bool:
    """
    Checks whether the process can write to the given path.
    Used before attempting os.remove() + os.link() to give
    a clear error instead of an OSError mid-operation.

    Args:
        path: File path to check.

    Returns:
        True if writable, False otherwise.
    """
    return os.access(path, os.W_OK)


def same_filesystem(path_a: str, path_b: str) -> bool:
    """
    Verifies that two paths reside on the same filesystem.

    Hard links cannot cross filesystem boundaries. Detecting
    this up front avoids a confusing 'Invalid cross-device link'
    OSError during the actual link operation.

    Args:
        path_a: First file path.
        path_b: Second file path.

    Returns:
        True if both paths are on the same device.
    """
    try:
        return os.stat(path_a).st_dev == os.stat(path_b).st_dev
    except OSError:
        return False
