"""
controllers/reports_controller.py — Página «Reportes».

Centraliza todo lo generado por los demás módulos (estructuras, reportes
de hardlinks, exportaciones de estadísticas): historial, apertura y
limpieza de entradas.
"""

import os
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.controllers.base import PageController


class ReportsController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = QWidget()
        root = QVBoxLayout(self.widget)

        title = QLabel("Reportes generados")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        root.addWidget(title)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Fecha", "Módulo", "Ruta", "Descripción"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(lambda item, _col:
                                            self._open(item))
        root.addWidget(self.tree, 1)

        buttons = QHBoxLayout()
        btn_open = QPushButton("Abrir")
        btn_open.clicked.connect(
            lambda: self._open(self.tree.currentItem()))
        btn_folder = QPushButton("Abrir carpeta contenedora")
        btn_folder.clicked.connect(self._open_folder)
        btn_remove = QPushButton("Quitar de la lista")
        btn_remove.clicked.connect(self._remove)
        btn_refresh = QPushButton("Actualizar")
        btn_refresh.clicked.connect(self.refresh)
        for button in (btn_open, btn_folder, btn_remove, btn_refresh):
            buttons.addWidget(button)
        buttons.addStretch(1)
        root.addLayout(buttons)

        self.refresh()

    def refresh(self) -> None:
        self.tree.clear()
        for report in self.ctx.history.reports():
            exists = os.path.exists(report["path"])
            item = QTreeWidgetItem(self.tree, [
                report["when"], report["module"],
                report["path"] + ("" if exists else "  (no existe)"),
                report.get("description", "")])
            item.setData(0, Qt.UserRole, report)
        for col in range(4):
            self.tree.resizeColumnToContents(col)

    def _selected(self) -> dict | None:
        item = self.tree.currentItem()
        return item.data(0, Qt.UserRole) if item else None

    def _open(self, item) -> None:
        report = item.data(0, Qt.UserRole) if item else None
        if report and os.path.exists(report["path"]):
            subprocess.Popen(["xdg-open", report["path"]])
        elif report:
            self.ctx.status("El archivo del reporte ya no existe.")

    def _open_folder(self) -> None:
        report = self._selected()
        if report:
            subprocess.Popen(["xdg-open",
                              os.path.dirname(report["path"]) or "/"])

    def _remove(self) -> None:
        report = self._selected()
        if report:
            self.ctx.history.remove_report(report["path"], report["when"])
            self.refresh()
