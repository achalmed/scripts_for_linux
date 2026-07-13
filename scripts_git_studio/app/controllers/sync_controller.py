"""
controllers/sync_controller.py — Página «Sincronizar».

Equivalente GUI de sync.sh: selección de repos habilitados, mensaje de
commit, modo verificación (--check) y sin pull (--no-pull). La operación
corre en un FunctionWorker (servicio sync_service); el botón alternativo
«Ejecutar sync.sh (CLI)» lanza el script Bash original de backend/ vía
ProcessWorker, con su salida completa en la Consola.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem, QTableWidgetItem

from app.controllers.base import PageController
from app.services import sync_service
from app.utils.paths import BACKEND_SYNC
from app.utils.ui_loader import load_ui
from app.workers.function_worker import FunctionWorker
from app.workers.process_worker import ProcessWorker


class SyncController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = load_ui("page_sync.ui")
        ui = self.widget

        ui.tableResult.setHorizontalHeaderLabels(
            ["Repositorio", "Resultado", "Detalle"])
        ui.tableResult.horizontalHeader().setStretchLastSection(True)

        ui.btnSelectAll.clicked.connect(lambda: self._check_all(True))
        ui.btnSelectNone.clicked.connect(lambda: self._check_all(False))
        ui.btnSync.clicked.connect(self._sync)
        ui.btnRunCli.clicked.connect(self._run_cli)

        self.refresh()

    # -------------------------------------------------------------- página
    def refresh(self) -> None:
        self.config = self.ctx.config.load()
        checked = {self.widget.listRepos.item(i).text()
                   for i in range(self.widget.listRepos.count())
                   if self.widget.listRepos.item(i).checkState()
                   == Qt.Checked}
        self.widget.listRepos.clear()
        self.widget.editMessage.setPlaceholderText(
            self.config.default_commit_message)
        for repo in self.config.enabled_repos():
            item = QListWidgetItem(repo.name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(
                Qt.Checked if not checked or repo.name in checked
                else Qt.Unchecked)
            self.widget.listRepos.addItem(item)

    def preselect(self, names: list[str]) -> None:
        """Marca solo los repos indicados (llegada desde Repositorios)."""
        wanted = set(names)
        for i in range(self.widget.listRepos.count()):
            item = self.widget.listRepos.item(i)
            item.setCheckState(
                Qt.Checked if item.text() in wanted else Qt.Unchecked)

    def _check_all(self, checked: bool) -> None:
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.widget.listRepos.count()):
            self.widget.listRepos.item(i).setCheckState(state)

    def _checked_names(self) -> list[str]:
        return [self.widget.listRepos.item(i).text()
                for i in range(self.widget.listRepos.count())
                if self.widget.listRepos.item(i).checkState() == Qt.Checked]

    # ------------------------------------------------------- sincronización
    def _sync(self) -> None:
        names = self._checked_names()
        if not names:
            self.ctx.status("No hay repositorios seleccionados.")
            return
        message = (self.widget.editMessage.text().strip()
                   or self.config.default_commit_message)
        check_only = self.widget.chkCheckOnly.isChecked()

        worker = FunctionWorker(
            sync_service.sync_repos, self.config, names, message,
            check_only=check_only,
            no_pull=self.widget.chkNoPull.isChecked(),
            description="sincronización")
        worker.result_ready.connect(self._on_synced)
        task = ("Verificando repositorios…" if check_only
                else "Sincronizando repositorios…")
        self.ctx.run_function_worker(worker, task)

    def _on_synced(self, report: sync_service.SyncReport) -> None:
        table = self.widget.tableResult
        table.setRowCount(len(report.items))
        for row, item in enumerate(report.items):
            table.setItem(row, 0, QTableWidgetItem(item.name))
            table.setItem(row, 1, QTableWidgetItem(item.result))
            table.setItem(row, 2, QTableWidgetItem(item.detail))
        summary = (f"Sincronizados: {report.count(sync_service.RESULT_SYNCED)}"
                   f" · Sin cambios: "
                   f"{report.count(sync_service.RESULT_NO_CHANGES)}"
                   f" · Errores: {report.count(sync_service.RESULT_ERROR)}")
        self.widget.lblSummary.setText(summary)
        self.ctx.status(summary)
        mode = "verificación" if report.check_only else "sincronización"
        self.ctx.history.add_operation("sync", f"{mode}: {summary}")

    # ----------------------------------------------------------- modo CLI
    def _run_cli(self) -> None:
        """Ejecuta el script Bash original con las opciones actuales."""
        argv = [str(BACKEND_SYNC / "sync.sh")]
        names = self._checked_names()
        if names and len(names) != len(self.config.enabled_repos()):
            argv += ["-r", ",".join(names)]
        message = self.widget.editMessage.text().strip()
        if message:
            argv += ["-m", message]
        if self.widget.chkCheckOnly.isChecked():
            argv.append("-c")
        if self.widget.chkNoPull.isChecked():
            argv.append("-n")

        worker = ProcessWorker(argv, cwd=str(BACKEND_SYNC),
                               description="sync.sh")
        self.ctx.run_process_worker(worker, "sync.sh (CLI)")
        self.ctx.history.add_operation("sync", "ejecución de sync.sh (CLI)")
