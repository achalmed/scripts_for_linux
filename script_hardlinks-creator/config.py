"""
config.py — Centralized configuration for hardlinks-creator.

All tunable constants live here so the rest of the codebase
never contains magic strings or hardcoded paths.
"""

import os

# ==============================================================================
# VERSIÓN
# ==============================================================================
VERSION = "3.1.0"
AUTHOR = "Edison Achalma"
EMAIL = "achalmed.18@gmail.com"

# ==============================================================================
# DIRECTORIO DE TRABAJO
# Set to None to use the parent directory of this script automatically.
# Override with --directory CLI flag or by editing this value.
# ==============================================================================
DEFAULT_DIRECTORY: str | None = os.environ.get("DOCS_ROOT", os.path.expanduser("~/Documents")) + "/"   # FS2: sin ruta literal

# ==============================================================================
# DIRECTORIOS EXCLUIDOS POR DEFECTO
# These protect build artifacts, caches, and VCS internals from being scanned.
# Additional exclusions can be passed via --exclude at runtime.
# ==============================================================================
DEFAULT_EXCLUDED_DIRS = [
    # Version control & IDE
    ".git",
    ".github",
    ".vscode",
    ".idea",
    ".obsidian",
    # Quarto build outputs — scanning _site would create links inside rendered HTML
    "_site",
    "_freeze",
    "_extensions",
    ".quarto",
    # Python / Node caches
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    # Un nombre suelto excluye la carpeta a cualquier profundidad (lib/scanner.py), así que `_site` y
    # `_extensions` cubren también los pubs anidados en `04 index/_pubs/`. `_partials` no se excluye: el hub y
    # los pubs comparten sus parciales por hardlink (decisión del autor, 2026-10-08).
]

# ==============================================================================
# HASHING
# SHA-256 block size for memory-efficient hashing of large files.
# 8 KB per read keeps RAM usage flat regardless of file size.
# ==============================================================================
HASH_BLOCK_SIZE = 8192

# ==============================================================================
# LOGGING
# Log file path. Set to None to disable file logging.
# ==============================================================================
LOG_FILE: str | None = None  # e.g. "/tmp/hardlinks-creator.log"

# ==============================================================================
# EXIT CODES (POSIX convention)
# ==============================================================================
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_BAD_ARGS = 2
EXIT_NOT_FOUND = 3
EXIT_NO_PERMISSION = 4
EXIT_INTERRUPTED = 130
