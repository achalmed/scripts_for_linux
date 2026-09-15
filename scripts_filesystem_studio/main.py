#!/usr/bin/env python3
"""
main.py — Punto de entrada de Filesystem Studio.

Orquestación mínima: crea la QApplication, aplica el tema guardado en
QSettings y muestra la ventana principal. Toda la lógica vive en app/.

Uso:
    python3 main.py            # ejecución normal
    python3 main.py --smoke    # construye la UI y sale (prueba de humo)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.services.settings_service import SettingsService
from app.utils.theming import apply_theme

ORG_NAME = "EdisonAchalma"
APP_NAME = "FilesystemStudio"


def main() -> int:
    smoke = "--smoke" in sys.argv

    QApplication.setOrganizationName(ORG_NAME)
    QApplication.setApplicationName(APP_NAME)
    app = QApplication(sys.argv)

    settings = SettingsService()
    apply_theme(app, settings.theme())

    window = MainWindow(settings)
    window.show()

    if smoke:
        QTimer.singleShot(0, app.quit)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
