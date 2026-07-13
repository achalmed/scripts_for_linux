"""
dialogs/preferences_dialog.py — Ventana de preferencias.

Carga dialog_preferences.ui (Qt Designer) y sincroniza todos los campos
con SettingsService (QSettings). El tema se aplica inmediatamente.
"""

from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QVBoxLayout

from app.services.settings_service import SettingsService
from app.utils.theming import apply_theme
from app.utils.ui_loader import load_ui


class PreferencesDialog(QDialog):
    def __init__(self, settings: SettingsService, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.ui = load_ui("dialog_preferences.ui")
        self.setWindowTitle(self.ui.windowTitle())
        self.setMinimumSize(self.ui.minimumSize())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        self._load()

        ui = self.ui
        ui.btnReportsBrowse.clicked.connect(self._browse_reports)
        ui.buttonBox.accepted.connect(self._save_and_accept)
        ui.buttonBox.rejected.connect(self.reject)

    # ---------------------------------------------------------------- load
    def _load(self) -> None:
        s = self.settings
        ui = self.ui
        ui.editUser.setText(s.github_user())
        ui.comboProtocol.setCurrentText(s.clone_protocol())
        ui.comboDepth.setCurrentText(s.clone_depth())
        ui.spinDays.setValue(s.activity_days())
        ui.comboFormat.setCurrentText(s.export_format())
        ui.editReportsDir.setText(s.reports_dir())
        ui.chkFetch.setChecked(s.fetch_on_status())
        ui.comboTheme.setCurrentText(s.theme())
        ui.spinIconSize.setValue(s.icon_size())

    # ---------------------------------------------------------------- save
    def _save_and_accept(self) -> None:
        s = self.settings
        ui = self.ui
        s.set_github_user(ui.editUser.text().strip())
        s.set_clone_protocol(ui.comboProtocol.currentText())
        s.set_clone_depth(ui.comboDepth.currentText().strip() or "1")
        s.set_activity_days(ui.spinDays.value())
        s.set_export_format(ui.comboFormat.currentText())
        s.set_reports_dir(ui.editReportsDir.text().strip())
        s.set_fetch_on_status(ui.chkFetch.isChecked())
        s.set_theme(ui.comboTheme.currentText())
        s.set_icon_size(ui.spinIconSize.value())

        app = QApplication.instance()
        if app:
            apply_theme(app, s.theme())
        self.accept()

    # ------------------------------------------------------------- helpers
    def _browse_reports(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Carpeta de reportes",
            self.ui.editReportsDir.text().strip() or "~")
        if path:
            self.ui.editReportsDir.setText(path)
