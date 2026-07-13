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
REPORTS_DIR = PROJECT_ROOT / "reports"

BACKEND_DOWNLOAD = BACKEND_DIR / "script_git_download_respos"
BACKEND_SYNC = BACKEND_DIR / "script_git_sync_respos"

# Archivo de configuración de repos COMPARTIDO con los scripts CLI:
# la GUI y sync.sh/status.sh leen y escriben el mismo archivo, de modo
# que nunca se desincronizan.
REPOS_CONFIG_FILE = BACKEND_SYNC / "repos-config.yml"
