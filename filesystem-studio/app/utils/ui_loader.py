"""
utils/ui_loader.py — Carga de archivos .ui de Qt Designer en tiempo de ejecución.

Se usa QUiLoader (en vez de compilar con pyside6-uic) para que los .ui
sigan siendo la única fuente de verdad editable desde Qt Designer,
sin paso de compilación intermedio.
"""

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget

from app.utils.paths import UI_DIR

_loader = QUiLoader()


def load_ui(filename: str, parent: QWidget | None = None) -> QWidget:
    """Carga app/ui/<filename> y devuelve el widget raíz."""
    path = UI_DIR / filename
    ui_file = QFile(str(path))
    if not ui_file.open(QIODevice.ReadOnly):
        raise FileNotFoundError(f"No se pudo abrir el archivo UI: {path}")
    try:
        widget = _loader.load(ui_file, parent)
    finally:
        ui_file.close()
    if widget is None:
        raise RuntimeError(f"QUiLoader no pudo cargar: {path}")
    return widget
