"""
dialogs/properties_dialog.py — Propiedades de archivo/carpeta del Explorador.
"""

import os
import pwd
import stat
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

from app.utils.format import format_size


class PropertiesDialog(QDialog):
    def __init__(self, path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Propiedades")
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        try:
            st = os.stat(path)
            is_dir = os.path.isdir(path)
            try:
                owner = pwd.getpwuid(st.st_uid).pw_name
            except KeyError:
                owner = str(st.st_uid)

            rows = [
                ("Nombre", os.path.basename(path) or path),
                ("Ruta", path),
                ("Tipo", "Carpeta" if is_dir else "Archivo"),
                ("Tamaño", "—" if is_dir else format_size(st.st_size)),
                ("Inodo", str(st.st_ino)),
                ("Enlaces duros", str(st.st_nlink)),
                ("Permisos", stat.filemode(st.st_mode)),
                ("Propietario", owner),
                ("Modificado", datetime.fromtimestamp(st.st_mtime)
                 .strftime("%Y-%m-%d %H:%M:%S")),
            ]
        except OSError as exc:
            rows = [("Error", str(exc))]

        for label, value in rows:
            value_label = QLabel(value)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            value_label.setWordWrap(True)
            form.addRow(f"{label}:", value_label)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
