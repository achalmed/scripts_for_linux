"""
app/main_window.py — Ventana principal de Filesystem Studio.

Carga app/ui/mainwindow.ui (Qt Designer), construye la barra lateral de
navegación por funcionalidades, apila las páginas y acopla la Consola.
Mantiene vivo el registro de workers activos (evita que el recolector
destruya un QThread en ejecución).
"""

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QListWidgetItem, QMessageBox

from app.context import AppContext
from app.controllers.dashboard_controller import DashboardController
from app.controllers.explorer_controller import ExplorerController
from app.controllers.folders_controller import FoldersController
from app.controllers.hardlinks_controller import HardlinksController
from app.controllers.reports_controller import ReportsController
from app.controllers.stats_controller import StatsController
from app.controllers.tree_controller import TreeController
from app.dialogs.preferences_dialog import PreferencesDialog
from app.services.history_service import HistoryService
from app.services.settings_service import SettingsService
from app.utils.icons import get_icon
from app.utils.ui_loader import load_ui
from app.widgets.console_dock import ConsoleDock

APP_VERSION = "1.0.0"


class MainWindow:
    """Envoltorio sobre el QMainWindow definido en mainwindow.ui."""

    def __init__(self, settings: SettingsService):
        self.settings = settings
        self.history = HistoryService()
        self.ui = load_ui("mainwindow.ui")
        self.ui.setWindowIcon(get_icon("app"))

        # Consola acoplada abajo (transversal a todas las páginas)
        self.console = ConsoleDock(self.ui)
        self.ui.addDockWidget(Qt.BottomDockWidgetArea, self.console)

        self._workers: list = []
        self.context = AppContext(self.settings, self.history, self)

        # ------------------------------------------------ páginas y sidebar
        self.controllers: dict[str, object] = {}
        self._page_order: list[str] = []
        pages = [
            ("dashboard", "Dashboard", "dashboard", DashboardController),
            ("explorer", "Explorador", "explorer", ExplorerController),
            ("tree", "Árbol", "tree", TreeController),
            ("stats", "Estadísticas", "stats", StatsController),
            ("folders", "Carpetas", "folders", FoldersController),
            ("hardlinks", "Hardlinks", "links", HardlinksController),
            ("reports", "Reportes", "reports", ReportsController),
        ]

        icon_size = self.settings.icon_size()
        self.ui.sidebar.setIconSize(QSize(icon_size, icon_size))
        for page_id, label, icon_name, controller_cls in pages:
            controller = controller_cls(self.context)
            self.controllers[page_id] = controller
            self._page_order.append(page_id)
            self.ui.stack.addWidget(controller.widget)
            item = QListWidgetItem(get_icon(icon_name), label)
            item.setSizeHint(QSize(0, 44))
            self.ui.sidebar.addItem(item)

        self.ui.sidebar.currentRowChanged.connect(self._on_page_changed)
        self.ui.sidebar.setCurrentRow(0)

        # ------------------------------------------------------------ menús
        self.ui.actionSalir.triggered.connect(self.ui.close)
        self.ui.actionPreferencias.triggered.connect(self._open_preferences)
        self.ui.actionConsola.toggled.connect(self.console.setVisible)
        self.console.visibilityChanged.connect(
            self.ui.actionConsola.setChecked)
        self.ui.actionAcercaDe.triggered.connect(self._about)

        self.ui.statusbar.showMessage("Listo", 3000)

    # ---------------------------------------------------------------- API
    def show(self) -> None:
        self.ui.show()

    def navigate(self, page_id: str) -> None:
        if page_id in self._page_order:
            self.ui.sidebar.setCurrentRow(self._page_order.index(page_id))

    def send_path(self, page_id: str, path: str) -> None:
        """Navega a una página y le entrega una ruta como objetivo."""
        self.navigate(page_id)
        controller = self.controllers.get(page_id)
        if controller and hasattr(controller, "set_target_path"):
            controller.set_target_path(path)

    def run_function_worker(self, worker, task_name: str) -> None:
        self.console.attach_function_worker(worker, task_name)
        self._track(worker)
        worker.start()

    def run_process_worker(self, worker, task_name: str) -> None:
        self.console.attach_process_worker(worker, task_name)
        self._track(worker)
        worker.start()

    def _track(self, worker) -> None:
        self._workers.append(worker)
        worker.finished.connect(lambda: self._untrack(worker))

    def _untrack(self, worker) -> None:
        if worker in self._workers:
            self._workers.remove(worker)

    # ------------------------------------------------------------- private
    def _on_page_changed(self, row: int) -> None:
        self.ui.stack.setCurrentIndex(row)
        page_id = self._page_order[row]
        controller = self.controllers.get(page_id)
        if controller and hasattr(controller, "refresh"):
            controller.refresh()

    def _open_preferences(self) -> None:
        dialog = PreferencesDialog(self.settings, parent=self.ui)
        if dialog.exec():
            self.console.log("ok", "Preferencias guardadas.")

    def _about(self) -> None:
        QMessageBox.about(
            self.ui, "Acerca de Filesystem Studio",
            f"<b>Filesystem Studio</b> v{APP_VERSION}<br><br>"
            "Suite unificada de gestión del sistema de archivos:<br>"
            "árboles de directorios, estadísticas por extensión, creación "
            "masiva de carpetas y hardlinks.<br><br>"
            "Los scripts originales viven en <code>backend/</code> y siguen "
            "siendo utilizables desde la línea de comandos.<br><br>"
            "Autor: Edison Achalma (@achalmed)")
