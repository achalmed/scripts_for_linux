"""
config.py — Centralized configuration for hardlinks-creator.

All tunable constants live here so the rest of the codebase
never contains magic strings or hardcoded paths.
"""

# ==============================================================================
# VERSIÓN
# ==============================================================================
VERSION = "3.0.0"
AUTHOR = "Edison Achalma"
EMAIL = "achalmaedison@gmail.com"

# ==============================================================================
# DIRECTORIO DE TRABAJO
# Set to None to use the parent directory of this script automatically.
# Override with --directory CLI flag or by editing this value.
# ==============================================================================
DEFAULT_DIRECTORY: str | None = "/home/achalmaedison/Documents/"

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
    "_partials",
    ".quarto",
    # Python / Node caches
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    # Per-site build exclusions (prevents cross-site linking of rendered assets)
    "pub_aequilibria/_site/",
    "pub_pecunia-fluxus/_site/",
    "pub_numerus-scriptum/_site/",
    "pub_epsilon-y-beta/_site/",
    "pub_optimums/_site/",
    "pub_methodica/_site/",
    "pub_chaska/_site/",
    "pub_axiomata/_site/",
    "pub_actus-mercator/_site/",
    "pub_res-publica/_site/",
    "website-achalma/_site/",
    "pub_dialectica-y-mercado/_site/",
    # Per-site extension exclusions
    "pub_pecunia-fluxus/_extensions/",
    "pub_numerus-scriptum/_extensions/",
    "pub_epsilon-y-beta/_extensions/",
    "pub_optimums/_extensions/",
    "pub_methodica/_extensions/",
    "pub_chaska/_extensions/",
    "pub_axiomata/_extensions/",
    "pub_actus-mercator/_extensions/",
    "pub_res-publica/_extensions/",
    "pub_website-achalma/_extensions/",
    "pub_dialectica-y-mercado/_extensions/",
    "pub_borradores/tesis 2025/_extensions/",
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
