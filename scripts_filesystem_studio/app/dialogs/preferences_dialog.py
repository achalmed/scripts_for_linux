"""
dialogs/preferences_dialog.py — Ventana de preferencias.

Carga dialog_preferences.ui (Qt Designer) y sincroniza todos los campos
con SettingsService (QSettings). El tema se aplica inmediatamente.
"""

from PySide6.QtWidgets import QApplication, QDialog, QFileDialog, QVBoxLayout

from app.services.settings_service import SettingsService
from app.utils.theming import apply_theme
from app.utils.ui_loader import load_ui

_LANG_MAP = {"Español": "es", "English": "en"}
_LANG_INV = {"es": "Español", "en": "English"}


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
        ui.btnAddFav.clicked.connect(self._add_favorite)
        ui.btnRemoveFav.clicked.connect(self._remove_favorite)
        ui.btnReportsBrowse.clicked.connect(
            lambda: self._browse_into(ui.editReportsDir))
        ui.btnTempBrowse.clicked.connect(
            lambda: self._browse_into(ui.editTempDir))
        ui.buttonBox.accepted.connect(self._save_and_accept)
        ui.buttonBox.rejected.connect(self.reject)

    # ---------------------------------------------------------------- load
    def _load(self) -> None:
        s = self.settings
        ui = self.ui
        ui.spinDepth.setValue(s.default_depth())
        ui.comboExport.setCurrentText(s.export_format())
        ui.comboLanguage.setCurrentText(_LANG_INV.get(s.language(), "Español"))
        ui.comboTheme.setCurrentText(s.theme())
        ui.spinIconSize.setValue(s.icon_size())
        ui.spinThreads.setValue(s.thread_count())
        ui.listFavorites.addItems(s.favorite_paths())
        ui.editReportsDir.setText(s.reports_dir())
        ui.editTempDir.setText(s.temp_dir())
        ui.editExcludeDirs.setPlainText("\n".join(s.exclude_dirs()))
        ui.editExcludeFiles.setPlainText("\n".join(s.exclude_files()))

    # ---------------------------------------------------------------- save
    def _save_and_accept(self) -> None:
        s = self.settings
        ui = self.ui
        s.set_default_depth(ui.spinDepth.value())
        s.set_export_format(ui.comboExport.currentText())
        s.set_language(_LANG_MAP.get(ui.comboLanguage.currentText(), "es"))
        s.set_theme(ui.comboTheme.currentText())
        s.set_icon_size(ui.spinIconSize.value())
        s.set_thread_count(ui.spinThreads.value())
        s.set_favorite_paths([
            ui.listFavorites.item(i).text()
            for i in range(ui.listFavorites.count())])
        s.set_reports_dir(ui.editReportsDir.text().strip())
        s.set_temp_dir(ui.editTempDir.text().strip())
        s.set_exclude_dirs([
            line.strip() for line in
            ui.editExcludeDirs.toPlainText().splitlines() if line.strip()])
        s.set_exclude_files([
            line.strip() for line in
            ui.editExcludeFiles.toPlainText().splitlines() if line.strip()])

        app = QApplication.instance()
        if app:
            apply_theme(app, s.theme())
        self.accept()

    # ------------------------------------------------------------- helpers
    def _browse_into(self, line_edit) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta", line_edit.text().strip() or "~")
        if path:
            line_edit.setText(path)

    def _add_favorite(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Añadir carpeta favorita", self.settings.last_directory())
        if path:
            self.ui.listFavorites.addItem(path)

    def _remove_favorite(self) -> None:
        row = self.ui.listFavorites.currentRow()
        if row >= 0:
            self.ui.listFavorites.takeItem(row)
