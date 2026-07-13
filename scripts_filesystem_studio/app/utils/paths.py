"""
utils/paths.py — Rutas canónicas del proyecto.

Única fuente de verdad para localizar backend/, resources/ y ui/,
independiente del directorio de trabajo actual.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = PROJECT_ROOT / "app"
UI_DIR = APP_DIR / "ui"
BACKEND_DIR = PROJECT_ROOT / "backend"
RESOURCES_DIR = PROJECT_ROOT / "resources"
ICONS_DIR = RESOURCES_DIR / "icons"
THEMES_DIR = RESOURCES_DIR / "themes"

BACKEND_TREE = BACKEND_DIR / "script_proyect_tree"
BACKEND_COUNT = BACKEND_DIR / "script_count_files_by_extension"
BACKEND_FOLDERS = BACKEND_DIR / "script_create_folders_batch"
BACKEND_HL_CREATOR = BACKEND_DIR / "script_hardlinks-creator"
BACKEND_HL_DETECTOR = BACKEND_DIR / "script_hardlinks-detector"
