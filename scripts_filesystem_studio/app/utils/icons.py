"""
utils/icons.py — Acceso a los iconos SVG de la aplicación.

Intenta usar los recursos Qt compilados (resources_rc.py, generado con
pyside6-rcc desde resources/resources.qrc). Si aún no se han compilado,
cae de forma transparente a cargar los .svg directamente del disco,
de modo que la app funciona clonada sin paso de build.
"""

from PySide6.QtGui import QIcon

from app.utils.paths import ICONS_DIR

try:
    import resources_rc  # noqa: F401  (registra el prefijo :/ en Qt)
    _USE_QRC = True
except ImportError:
    _USE_QRC = False


def get_icon(name: str) -> QIcon:
    """Devuelve el QIcon para resources/icons/<name>.svg."""
    if _USE_QRC:
        icon = QIcon(f":/icons/{name}.svg")
        if not icon.isNull():
            return icon
    path = ICONS_DIR / f"{name}.svg"
    return QIcon(str(path)) if path.exists() else QIcon()
