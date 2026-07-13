"""
utils/theming.py — Aplicación de temas QSS (oscuro / claro / sistema).

Los archivos .qss viven en resources/themes/. "sistema" no aplica hoja
de estilos y deja que Qt use la paleta del escritorio (Dolphin-style).
"""

from PySide6.QtWidgets import QApplication

from app.utils.paths import THEMES_DIR

THEMES = ("oscuro", "claro", "sistema")


def apply_theme(app: QApplication, theme: str) -> None:
    if theme not in ("oscuro", "claro"):
        app.setStyleSheet("")
        return
    qss_file = THEMES_DIR / ("dark.qss" if theme == "oscuro" else "light.qss")
    if qss_file.exists():
        app.setStyleSheet(qss_file.read_text(encoding="utf-8"))
