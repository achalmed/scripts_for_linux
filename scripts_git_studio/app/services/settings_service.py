"""
services/settings_service.py — Envoltorio tipado sobre QSettings.

Centraliza TODAS las preferencias persistentes de la aplicación.
Los valores por defecto de clonado provienen de config.sh del script
original (script_git_download_respos): profundidad 1, protocolo ssh.

El token de GitHub NO se persiste aquí: se lee de la variable de
entorno GITHUB_TOKEN o se introduce por sesión en la página Clonar
(QSettings guarda en texto plano y un token no debe quedar en disco).
"""

import json
import os

from PySide6.QtCore import QSettings

from app.utils.paths import REPORTS_DIR

DEFAULT_DEPTH = "1"        # solo el último commit, como config.sh
DEFAULT_PROTOCOL = "ssh"
DEFAULT_EXPORT_FORMAT = "md"
DEFAULT_THEME = "oscuro"
DEFAULT_ACTIVITY_DAYS = 7


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

    # --------------------------------------------------------------- github
    def github_user(self) -> str:
        return str(self._s.value("github/user", "achalmed"))

    def set_github_user(self, user: str) -> None:
        self._s.setValue("github/user", user)

    @staticmethod
    def github_token_from_env() -> str:
        return os.environ.get("GITHUB_TOKEN", "")

    # -------------------------------------------------------------- clonado
    def clone_depth(self) -> str:
        return str(self._s.value("clone/depth", DEFAULT_DEPTH))

    def set_clone_depth(self, depth: str) -> None:
        self._s.setValue("clone/depth", depth)

    def clone_protocol(self) -> str:
        return str(self._s.value("clone/protocol", DEFAULT_PROTOCOL))

    def set_clone_protocol(self, protocol: str) -> None:
        self._s.setValue("clone/protocol", protocol)

    def clone_dest_dir(self) -> str:
        return str(self._s.value("clone/dest_dir",
                                 os.path.expanduser("~/Documents")))

    def set_clone_dest_dir(self, path: str) -> None:
        self._s.setValue("clone/dest_dir", path)

    def clone_exclude(self) -> list[str]:
        return self._get_list("clone/exclude", [])

    def set_clone_exclude(self, repos: list[str]) -> None:
        self._set_list("clone/exclude", repos)

    # -------------------------------------------------------------- estado
    def activity_days(self) -> int:
        return int(self._s.value("status/activity_days",
                                 DEFAULT_ACTIVITY_DAYS))

    def set_activity_days(self, days: int) -> None:
        self._s.setValue("status/activity_days", days)

    def fetch_on_status(self) -> bool:
        """git fetch antes de calcular ahead/behind (corrección Bug 2).
        Desactivable para análisis rápidos sin red."""
        return self._s.value("status/fetch", "true") in ("true", True)

    def set_fetch_on_status(self, fetch: bool) -> None:
        self._s.setValue("status/fetch", "true" if fetch else "false")

    # ------------------------------------------------------------- generales
    def export_format(self) -> str:
        return str(self._s.value("defaults/export_format",
                                 DEFAULT_EXPORT_FORMAT))

    def set_export_format(self, fmt: str) -> None:
        self._s.setValue("defaults/export_format", fmt)

    def theme(self) -> str:
        return str(self._s.value("ui/theme", DEFAULT_THEME))

    def set_theme(self, theme: str) -> None:
        self._s.setValue("ui/theme", theme)

    def icon_size(self) -> int:
        return int(self._s.value("ui/icon_size", 22))

    def set_icon_size(self, size: int) -> None:
        self._s.setValue("ui/icon_size", size)

    # ----------------------------------------------------------------- rutas
    def reports_dir(self) -> str:
        return str(self._s.value("paths/reports_dir", str(REPORTS_DIR)))

    def set_reports_dir(self, path: str) -> None:
        self._s.setValue("paths/reports_dir", path)

    def last_directory(self) -> str:
        return str(self._s.value("paths/last_directory",
                                 os.path.expanduser("~")))

    def set_last_directory(self, path: str) -> None:
        self._s.setValue("paths/last_directory", path)
