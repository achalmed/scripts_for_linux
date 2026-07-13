"""
app/context.py — Contexto compartido que la ventana principal inyecta
en cada controlador de página.

Es la única vía por la que las páginas acceden a servicios transversales
(configuración, historial, consola, workers) y se comunican entre sí
(navegación, "usar esta ruta en…").
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.main_window import MainWindow
    from app.services.history_service import HistoryService
    from app.services.settings_service import SettingsService
    from app.widgets.console_dock import ConsoleDock


class AppContext:
    def __init__(self, settings: "SettingsService",
                 history: "HistoryService", window: "MainWindow"):
        self.settings = settings
        self.history = history
        self.window = window

    @property
    def console(self) -> "ConsoleDock":
        return self.window.console

    def run_function_worker(self, worker, task_name: str) -> None:
        self.window.run_function_worker(worker, task_name)

    def run_process_worker(self, worker, task_name: str) -> None:
        self.window.run_process_worker(worker, task_name)

    def navigate(self, page_id: str) -> None:
        self.window.navigate(page_id)

    def send_path(self, page_id: str, path: str) -> None:
        self.window.send_path(page_id, path)

    def status(self, message: str, msecs: int = 5000) -> None:
        self.window.ui.statusbar.showMessage(message, msecs)
