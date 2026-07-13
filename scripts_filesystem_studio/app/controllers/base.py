"""
controllers/base.py — Clase base de los controladores de página.

Un controlador conecta la vista (.ui o widget en código) con la capa de
servicios a través de workers; nunca toca el disco ni backend/ directo.
"""

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QFileDialog, QLineEdit, QWidget

from app.context import AppContext


class PageController(QObject):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.widget: QWidget | None = None

    # ------------------------------------------------------------- helpers
    def browse_directory(self, line_edit: QLineEdit,
                         title: str = "Seleccionar carpeta") -> str | None:
        start = line_edit.text().strip() or self.ctx.settings.last_directory()
        path = QFileDialog.getExistingDirectory(self.widget, title, start)
        if path:
            line_edit.setText(path)
            self.ctx.settings.set_last_directory(path)
        return path or None

    def save_file_dialog(self, title: str, suggested: str,
                         filter_str: str) -> str | None:
        path, _ = QFileDialog.getSaveFileName(
            self.widget, title, suggested, filter_str)
        return path or None

    @staticmethod
    def parse_csv_list(text: str) -> list[str]:
        return [part.strip() for part in text.split(",") if part.strip()]
