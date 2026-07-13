"""
controllers/explorer_controller.py — Página «Explorador».

Explorador integrado sobre QFileSystemModel: navegación, propiedades,
copiar rutas, abrir con el gestor del sistema y envío de la carpeta
seleccionada a cualquier otro módulo («Usar en…»).
"""

import os
import subprocess

from PySide6.QtCore import QDir, Qt
from PySide6.QtGui import QAction, QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtWidgets import QFileSystemModel

from app.controllers.base import PageController
from app.dialogs.properties_dialog import PropertiesDialog

_SEND_TARGETS = [("Árbol de directorios", "tree"),
                 ("Estadísticas", "stats"),
                 ("Carpetas", "folders"),
                 ("Hardlinks", "hardlinks")]


class ExplorerController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = QWidget()
        root = QVBoxLayout(self.widget)

        title = QLabel("Explorador de archivos")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        root.addWidget(title)

        # ------------------------------------------------------ barra ruta
        bar = QHBoxLayout()
        self.path_edit = QLineEdit(os.path.expanduser("~"))
        self.path_edit.returnPressed.connect(self._go_to_path)
        btn_up = QPushButton("↑ Subir")
        btn_up.clicked.connect(self._go_up)
        btn_open = QPushButton("Abrir en el gestor")
        btn_open.clicked.connect(self._open_in_file_manager)
        btn_copy = QPushButton("Copiar ruta")
        btn_copy.clicked.connect(self._copy_path)
        bar.addWidget(self.path_edit, 1)
        bar.addWidget(btn_up)
        bar.addWidget(btn_open)
        bar.addWidget(btn_copy)
        root.addLayout(bar)

        # ------------------------------------------------------------ vista
        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot
                             | QDir.Hidden)
        self.view = QTreeView()
        self.view.setModel(self.model)
        self.view.setRootIndex(self.model.index(os.path.expanduser("~")))
        self.view.setSortingEnabled(True)
        self.view.sortByColumn(0, Qt.AscendingOrder)
        self.view.setColumnWidth(0, 380)
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self._context_menu)
        self.view.doubleClicked.connect(self._double_clicked)
        root.addWidget(self.view, 1)

    # -------------------------------------------------------- integración
    def set_target_path(self, path: str) -> None:
        if os.path.isdir(path):
            self.path_edit.setText(path)
            self.view.setRootIndex(self.model.index(path))

    # ---------------------------------------------------------- navegación
    def _current_path(self) -> str:
        index = self.view.currentIndex()
        if index.isValid():
            return self.model.filePath(index)
        return self.path_edit.text().strip()

    def _go_to_path(self) -> None:
        path = os.path.expanduser(self.path_edit.text().strip())
        if os.path.isdir(path):
            self.view.setRootIndex(self.model.index(path))
        else:
            self.ctx.status(f"No es una carpeta: {path}")

    def _go_up(self) -> None:
        current = self.path_edit.text().strip() or os.path.expanduser("~")
        parent = os.path.dirname(current.rstrip("/")) or "/"
        self.set_target_path(parent)

    def _double_clicked(self, index) -> None:
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.set_target_path(path)
        else:
            subprocess.Popen(["xdg-open", path])

    # ------------------------------------------------------------ acciones
    def _open_in_file_manager(self) -> None:
        path = self._current_path()
        target = path if os.path.isdir(path) else os.path.dirname(path)
        subprocess.Popen(["xdg-open", target])

    def _copy_path(self) -> None:
        path = self._current_path()
        QGuiApplication.clipboard().setText(path)
        self.ctx.status(f"Ruta copiada: {path}")

    def _context_menu(self, pos) -> None:
        index = self.view.indexAt(pos)
        if not index.isValid():
            return
        path = self.model.filePath(index)
        menu = QMenu(self.view)

        action_open = QAction("Abrir", menu)
        action_open.triggered.connect(
            lambda: subprocess.Popen(["xdg-open", path]))
        menu.addAction(action_open)

        action_manager = QAction("Abrir con el gestor de archivos", menu)
        action_manager.triggered.connect(
            lambda: subprocess.Popen(
                ["xdg-open", path if os.path.isdir(path)
                 else os.path.dirname(path)]))
        menu.addAction(action_manager)

        action_copy = QAction("Copiar ruta", menu)
        action_copy.triggered.connect(
            lambda: QGuiApplication.clipboard().setText(path))
        menu.addAction(action_copy)

        action_props = QAction("Propiedades…", menu)
        action_props.triggered.connect(
            lambda: PropertiesDialog(path, self.widget).exec())
        menu.addAction(action_props)

        menu.addSeparator()
        if os.path.isdir(path):
            action_fav = QAction("Añadir a favoritas", menu)
            action_fav.triggered.connect(
                lambda: (self.ctx.settings.add_favorite(path),
                         self.ctx.status(f"Favorita añadida: {path}")))
            menu.addAction(action_fav)

            send_menu = menu.addMenu("Usar en…")
            for label, page_id in _SEND_TARGETS:
                action = QAction(label, send_menu)
                action.triggered.connect(
                    lambda _=False, p=page_id:
                    self.ctx.send_path(p, path))
                send_menu.addAction(action)

        menu.exec(self.view.viewport().mapToGlobal(pos))
