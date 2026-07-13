"""
controllers/reports_controller.py — Página «Reportes».

Genera el reporte de estado (equivalente GUI de status.sh redirigido a
archivo): tabla de estado, repos que necesitan atención y actividad
reciente, exportado a Markdown o CSV en la carpeta de reportes.
"""

import os
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem, QMessageBox

from app.controllers.base import PageController
from app.services import report_service, status_service
from app.utils.ui_loader import load_ui
from app.workers.function_worker import FunctionWorker


class ReportsController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = load_ui("page_reports.ui")
        ui = self.widget
        ui.comboFormat.setCurrentText(self.ctx.settings.export_format())
        ui.spinDays.setValue(self.ctx.settings.activity_days())
        ui.chkFetch.setChecked(self.ctx.settings.fetch_on_status())

        ui.btnGenerate.clicked.connect(self._generate)
        ui.btnOpenReport.clicked.connect(self._open_selected)
        ui.btnDeleteReport.clicked.connect(self._delete_selected)
        ui.listReports.itemDoubleClicked.connect(self._open_item)

        self.refresh()

    # -------------------------------------------------------------- página
    def refresh(self) -> None:
        self.widget.listReports.clear()
        for report in self.ctx.history.reports():
            item = QListWidgetItem(
                f"{report['when']}  ·  {report['path']}")
            item.setData(Qt.UserRole, (report["path"], report["when"]))
            self.widget.listReports.addItem(item)

    # ---------------------------------------------------------- generación
    def _generate(self) -> None:
        fmt = self.widget.comboFormat.currentText()
        days = self.widget.spinDays.value()
        fetch = self.widget.chkFetch.isChecked()
        self.ctx.settings.set_export_format(fmt)
        self.ctx.settings.set_activity_days(days)

        reports_dir = self.ctx.settings.reports_dir()
        os.makedirs(reports_dir, exist_ok=True)
        suggested = os.path.join(reports_dir,
                                 report_service.suggest_filename(fmt))
        path = self.save_file_dialog(
            "Guardar reporte", suggested,
            "Markdown (*.md);;CSV (*.csv)" if fmt == "md"
            else "CSV (*.csv);;Markdown (*.md)")
        if not path:
            return

        config = self.ctx.config.load()

        def task(progress_cb=None, cancel_cb=None, message_cb=None):
            statuses = status_service.collect_all(
                config, fetch=fetch, progress_cb=progress_cb,
                cancel_cb=cancel_cb, message_cb=message_cb)
            activity = status_service.recent_activity(
                config, days, cancel_cb=cancel_cb)
            report_service.write_report(path, statuses, activity, days)
            return statuses

        worker = FunctionWorker(task, description="reporte de estado")
        worker.result_ready.connect(lambda statuses:
                                    self._on_generated(path, statuses))
        self.ctx.run_function_worker(worker, "Generando reporte…")

    def _on_generated(self, path: str, statuses) -> None:
        self.ctx.last_statuses = statuses
        self.ctx.history.add_report("reports", path)
        self.ctx.history.add_operation("reports", f"reporte generado: {path}")
        self.ctx.status(f"Reporte guardado en {path}")
        self.refresh()

    # ------------------------------------------------------------ historial
    def _current_report(self) -> tuple[str, str] | None:
        item = self.widget.listReports.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _open_item(self, item: QListWidgetItem) -> None:
        path, _when = item.data(Qt.UserRole)
        self._open_path(path)

    def _open_selected(self) -> None:
        if data := self._current_report():
            self._open_path(data[0])

    def _open_path(self, path: str) -> None:
        if not os.path.isfile(path):
            QMessageBox.warning(self.widget, "No encontrado",
                                f"El archivo ya no existe:\n{path}")
            return
        subprocess.Popen(["xdg-open", path])

    def _delete_selected(self) -> None:
        data = self._current_report()
        if not data:
            return
        path, when = data
        answer = QMessageBox.question(
            self.widget, "Eliminar reporte",
            f"¿Eliminar el archivo y quitarlo del historial?\n\n{path}")
        if answer != QMessageBox.Yes:
            return
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            QMessageBox.warning(self.widget, "Error", str(exc))
            return
        self.ctx.history.remove_report(path, when)
        self.refresh()
