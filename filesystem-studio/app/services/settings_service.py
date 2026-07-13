"""
services/settings_service.py — Envoltorio tipado sobre QSettings.

Centraliza TODAS las preferencias persistentes de la aplicación.
Los valores por defecto de exclusiones provienen de los config de los
scripts originales (proyect_tree + hardlinks-creator), unificados aquí
en un único perfil.
"""

import json
import os

from PySide6.QtCore import QSettings

from app.utils.paths import PROJECT_ROOT

# Unión de DEFAULT_EXCLUDE_DIRS (proyect_tree) y DEFAULT_EXCLUDED_DIRS
# (hardlinks-creator) — antes vivían duplicadas y desincronizadas.
DEFAULT_EXCLUDE_DIRS = [
    ".git", ".github", ".vscode", ".idea", ".obsidian", ".quarto",
    "_site", "_freeze", "_extensions", "_partials", "site_libs",
    "node_modules", "__pycache__", ".pytest_cache",
    "build", "log", "output", "temp",
    ".Rproj.user", "index_cache", "__MACOSX",
]

DEFAULT_EXCLUDE_FILES = [
    "*.aux", "*.log", "*.out", "*.toc", "*.bbl", "*.blg", "*.synctex.gz",
    "*.fff", "*.ttt", "*.fls", "*.fdb_latexmk",
    "*.pyc", "*.pyo", "*.egg-info", "*.ipynb_checkpoints",
    ".DS_Store", "Thumbs.db", ".Rhistory", ".RData",
    "estructura.txt",
]

DEFAULT_DEPTH = 6
DEFAULT_EXPORT_FORMAT = "csv"
DEFAULT_THEME = "oscuro"
DEFAULT_LANGUAGE = "es"


class SettingsService:
    def __init__(self):
        self._s = QSettings()

    # -------------------------------------------------------------- helpers
    def _get_list(self, key: str, default: list[str]) -> list[str]:
        raw = self._s.value(key, "")
        if not raw:
            return list(default)
        try:
            value = json.loads(raw)
            return value if isinstance(value, list) else list(default)
        except (json.JSONDecodeError, TypeError):
            return list(default)

    def _set_list(self, key: str, value: list[str]) -> None:
        self._s.setValue(key, json.dumps(value, ensure_ascii=False))

    # ------------------------------------------------------------ exclusiones
    def exclude_dirs(self) -> list[str]:
        return self._get_list("defaults/exclude_dirs", DEFAULT_EXCLUDE_DIRS)

    def set_exclude_dirs(self, dirs: list[str]) -> None:
        self._set_list("defaults/exclude_dirs", dirs)

    def exclude_files(self) -> list[str]:
        return self._get_list("defaults/exclude_files", DEFAULT_EXCLUDE_FILES)

    def set_exclude_files(self, patterns: list[str]) -> None:
        self._set_list("defaults/exclude_files", patterns)

    # ------------------------------------------------------------- generales
    def default_depth(self) -> int:
        return int(self._s.value("defaults/depth", DEFAULT_DEPTH))

    def set_default_depth(self, depth: int) -> None:
        self._s.setValue("defaults/depth", depth)

    def export_format(self) -> str:
        return str(self._s.value("defaults/export_format", DEFAULT_EXPORT_FORMAT))

    def set_export_format(self, fmt: str) -> None:
        self._s.setValue("defaults/export_format", fmt)

    def theme(self) -> str:
        return str(self._s.value("ui/theme", DEFAULT_THEME))

    def set_theme(self, theme: str) -> None:
        self._s.setValue("ui/theme", theme)

    def language(self) -> str:
        return str(self._s.value("ui/language", DEFAULT_LANGUAGE))

    def set_language(self, lang: str) -> None:
        self._s.setValue("ui/language", lang)

    def icon_size(self) -> int:
        return int(self._s.value("ui/icon_size", 22))

    def set_icon_size(self, size: int) -> None:
        self._s.setValue("ui/icon_size", size)

    def thread_count(self) -> int:
        default = max(2, (os.cpu_count() or 4) // 2)
        return int(self._s.value("performance/threads", default))

    def set_thread_count(self, count: int) -> None:
        self._s.setValue("performance/threads", count)

    # ----------------------------------------------------------------- rutas
    def favorite_paths(self) -> list[str]:
        return self._get_list("paths/favorites", [str(PROJECT_ROOT.parent.parent)])

    def set_favorite_paths(self, paths: list[str]) -> None:
        self._set_list("paths/favorites", paths)

    def add_favorite(self, path: str) -> None:
        favs = self.favorite_paths()
        if path not in favs:
            favs.append(path)
            self.set_favorite_paths(favs)

    def reports_dir(self) -> str:
        default = str(PROJECT_ROOT / "reports")
        return str(self._s.value("paths/reports_dir", default))

    def set_reports_dir(self, path: str) -> None:
        self._s.setValue("paths/reports_dir", path)

    def temp_dir(self) -> str:
        import tempfile
        return str(self._s.value("paths/temp_dir", tempfile.gettempdir()))

    def set_temp_dir(self, path: str) -> None:
        self._s.setValue("paths/temp_dir", path)

    def last_directory(self) -> str:
        return str(self._s.value("paths/last_directory", os.path.expanduser("~")))

    def set_last_directory(self, path: str) -> None:
        self._s.setValue("paths/last_directory", path)
