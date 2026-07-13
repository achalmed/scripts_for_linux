"""
controllers/dashboard_controller.py — Página inicial «Dashboard».

Contenido dinámico (se reconstruye al entrar a la página), por eso se
construye en código y no en .ui: operaciones recientes, favoritas,
últimos reportes, espacio en disco y accesos directos.
"""

import shutil
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.controllers.base import PageController
from app.utils.format import format_size
from app.utils.icons import get_icon

_SHORTCUTS = [
    ("Árbol de directorios", "tree", "tree"),
    ("Estadísticas", "stats", "stats"),
    ("Carpetas", "folders", "folders"),
    ("Hardlinks", "links", "hardlinks"),
    ("Explorador", "explorer", "explorer"),
    ("Reportes", "reports", "reports"),
]


class DashboardController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = QWidget()
        root = QVBoxLayout(self.widget)

        title = QLabel("Filesystem Studio")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        subtitle = QLabel("Gestión unificada del sistema de archivos")
        root.addWidget(title)
        root.addWidget(subtitle)

        grid = QGridLayout()
        root.addLayout(grid, 1)

        # ------------------------------------------------ accesos directos
        group_shortcuts = QGroupBox("Accesos directos")
        sc_layout = QGridLayout(group_shortcuts)
        for index, (label, icon, page_id) in enumerate(_SHORTCUTS):
            button = QPushButton(get_icon(icon), f"  {label}")
            button.setMinimumHeight(40)
            button.clicked.connect(
                lambda _=False, p=page_id: self.ctx.navigate(p))
            sc_layout.addWidget(button, index // 2, index % 2)
        grid.addWidget(group_shortcuts, 0, 0)

        # ------------------------------------------------ espacio en disco
        group_disk = QGroupBox("Espacio utilizado (partición de inicio)")
        disk_layout = QVBoxLayout(group_disk)
        self.disk_label = QLabel("—")
        self.disk_bar = QProgressBar()
        disk_layout.addWidget(self.disk_label)
        disk_layout.addWidget(self.disk_bar)
        disk_layout.addStretch(1)
        grid.addWidget(group_disk, 0, 1)

        # ------------------------------------------- operaciones recientes
        self.list_ops = QListWidget()
        grid.addWidget(self._boxed("Operaciones recientes", self.list_ops),
                       1, 0)

        # -------------------------------------------------- favoritas
        self.list_favs = QListWidget()
        self.list_favs.itemDoubleClicked.connect(self._open_favorite)
        grid.addWidget(self._boxed(
            "Carpetas favoritas (doble clic → Explorador)", self.list_favs),
            1, 1)

        # ---------------------------------------------- últimos reportes
        self.list_reports = QListWidget()
        self.list_reports.itemDoubleClicked.connect(self._open_report)
        grid.addWidget(self._boxed(
            "Últimos reportes (doble clic → abrir)", self.list_reports),
            2, 0, 1, 2)

        self.refresh()

    @staticmethod
    def _boxed(title: str, widget: QWidget) -> QGroupBox:
        box = QGroupBox(title)
        layout = QHBoxLayout(box)
        layout.addWidget(widget)
        return box

    # ------------------------------------------------------------- refresh
    def refresh(self) -> None:
        self.list_ops.clear()
        for op in self.ctx.history.recent_operations(12):
            self.list_ops.addItem(
                f"{op['when']}  ·  [{op['module']}]  {op['description']}")
        if self.list_ops.count() == 0:
            self.list_ops.addItem("Sin operaciones todavía.")

        self.list_favs.clear()
        for path in self.ctx.settings.favorite_paths():
            item = QListWidgetItem(get_icon("folders"), path)
            item.setData(Qt.UserRole, path)
            self.list_favs.addItem(item)

        self.list_reports.clear()
        for report in self.ctx.history.reports()[:12]:
            item = QListWidgetItem(
                f"{report['when']}  ·  [{report['module']}]  {report['path']}")
            item.setData(Qt.UserRole, report["path"])
            self.list_reports.addItem(item)
        if self.list_reports.count() == 0:
            self.list_reports.addItem("Sin reportes todavía.")

        try:
            usage = shutil.disk_usage(
                self.ctx.settings.favorite_paths()[0]
                if self.ctx.settings.favorite_paths() else "/")
            percent = int(usage.used * 100 / usage.total)
            self.disk_bar.setValue(percent)
            self.disk_label.setText(
                f"{format_size(usage.used)} usados de "
                f"{format_size(usage.total)} "
                f"({format_size(usage.free)} libres)")
        except OSError:
            self.disk_label.setText("No disponible")

    # ------------------------------------------------------------- private
    def _open_favorite(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path:
            self.ctx.send_path("explorer", path)

    def _open_report(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.UserRole)
        if path:
            subprocess.Popen(["xdg-open", path])
