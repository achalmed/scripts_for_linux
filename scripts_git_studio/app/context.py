"""
app/context.py — Contexto compartido que la ventana principal inyecta
en cada controlador de página.

Es la única vía por la que las páginas acceden a servicios transversales
(registro de repos, configuración, historial, consola, workers) y se
comunican entre sí (navegación, «último análisis de estado»).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.main_window import MainWindow
    from app.services.config_service import ConfigService
    from app.services.history_service import HistoryService
    from app.services.settings_service import SettingsService
    from app.services.status_service import RepoStatus
    from app.widgets.console_dock import ConsoleDock


class AppContext:
    def __init__(self, settings: "SettingsService", config: "ConfigService",
                 history: "HistoryService", window: "MainWindow"):
        self.settings = settings
        self.config = config
        self.history = history
        self.window = window

        # Último análisis de estado (lo comparten Dashboard, Repositorios
        # y Reportes para no repetir fetch innecesariamente).
        self.last_statuses: list["RepoStatus"] = []

    @property
    def console(self) -> "ConsoleDock":
        return self.window.console

    def run_function_worker(self, worker, task_name: str) -> None:
        self.window.run_function_worker(worker, task_name)

    def run_process_worker(self, worker, task_name: str) -> None:
        self.window.run_process_worker(worker, task_name)

    def navigate(self, page_id: str) -> None:
        self.window.navigate(page_id)

    def status(self, message: str, msecs: int = 5000) -> None:
        self.window.ui.statusbar.showMessage(message, msecs)
