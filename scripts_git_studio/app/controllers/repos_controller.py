"""
controllers/repos_controller.py — Página «Repositorios».

Explorador del registro central (repos-config.yml): tabla de estado de
cada repo (equivalente GUI de status.sh), alta/baja/habilitación de
repos y puente hacia la página Sincronizar con la selección hecha.
"""

import subprocess

from PySide6.QtWidgets import QInputDialog, QMessageBox

from app.controllers.base import PageController
from app.models.repo_status_model import RepoStatusModel
from app.services import status_service
from app.services.config_service import RepoEntry
from app.workers.function_worker import FunctionWorker
from app.utils.ui_loader import load_ui


class ReposController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = load_ui("page_repos.ui")
        self.model = RepoStatusModel()
        ui = self.widget
        ui.tableRepos.setModel(self.model)
        ui.tableRepos.horizontalHeader().setStretchLastSection(True)
        ui.chkFetch.setChecked(self.ctx.settings.fetch_on_status())

        ui.btnBrowseBase.clicked.connect(
            lambda: self.browse_directory(ui.editBaseDir,
                                          "Directorio base de repositorios"))
        ui.btnAnalyze.clicked.connect(self._analyze)
        ui.btnAddRepo.clicked.connect(self._add_repo)
        ui.btnRemoveRepo.clicked.connect(self._remove_repos)
        ui.btnToggleEnabled.clicked.connect(self._toggle_enabled)
        ui.btnOpenFolder.clicked.connect(self._open_folder)
        ui.btnSyncSelected.clicked.connect(self._sync_selected)

        self._load_config()
        self._show_unanalyzed()

    # -------------------------------------------------------------- config
    def _load_config(self) -> None:
        self.config = self.ctx.config.load()
        self.widget.editBaseDir.setText(self.config.base_dir)

    def _save_config(self) -> None:
        base_dir = self.widget.editBaseDir.text().strip()
        if base_dir:
            self.config.base_dir = base_dir
        self.ctx.config.save(self.config)
        self.ctx.console.log("ok", "repos-config.yml actualizado.")

    def _show_unanalyzed(self) -> None:
        """Puebla la tabla sin tocar la red (estado «sin analizar»)."""
        rows = [status_service.RepoStatus(
            name=repo.name, path=self.config.repo_path(repo.name),
            branch=repo.branch,
            status="(habilitado)" if repo.enabled else "(deshabilitado)",
            enabled=repo.enabled) for repo in self.config.repos]
        self.model.set_statuses(rows)

    # ------------------------------------------------------------ análisis
    def _analyze(self) -> None:
        self._load_config()
        base_dir = self.widget.editBaseDir.text().strip()
        if base_dir and base_dir != self.config.base_dir:
            self.config.base_dir = base_dir
            self.ctx.config.save(self.config)

        fetch = self.widget.chkFetch.isChecked()
        self.ctx.settings.set_fetch_on_status(fetch)

        worker = FunctionWorker(
            status_service.collect_all, self.config, fetch=fetch,
            description="análisis de estado")
        worker.result_ready.connect(self._on_analyzed)
        self.ctx.run_function_worker(worker, "Analizando repositorios…")

    def _on_analyzed(self, statuses) -> None:
        self.model.set_statuses(statuses)
        self.ctx.last_statuses = statuses
        clean = sum(1 for s in statuses
                    if s.status == status_service.STATUS_CLEAN)
        summary = (f"Analizados: {len(statuses)} · Sincronizados: {clean} · "
                   f"Con pendientes: {len(statuses) - clean}")
        self.ctx.status(summary)
        self.ctx.history.add_operation("repos", summary)

    # ------------------------------------------------------------- gestión
    def _add_repo(self) -> None:
        name, accepted = QInputDialog.getText(
            self.widget, "Añadir repositorio",
            "Nombre de la carpeta del repo (dentro del directorio base):")
        name = name.strip()
        if not accepted or not name:
            return
        if self.config.find(name):
            QMessageBox.information(self.widget, "Ya registrado",
                                    f"'{name}' ya está en el registro.")
            return
        branch, accepted = QInputDialog.getText(
            self.widget, "Añadir repositorio", "Rama:", text="main")
        if not accepted:
            return
        self.config.repos.append(
            RepoEntry(name=name, branch=branch.strip() or "main"))
        self._save_config()
        self._show_unanalyzed()

    def _selected(self) -> list[status_service.RepoStatus]:
        rows = {index.row() for index in
                self.widget.tableRepos.selectionModel().selectedRows()}
        return [status for row in sorted(rows)
                if (status := self.model.status_at(row))]

    def _remove_repos(self) -> None:
        selected = self._selected()
        if not selected:
            return
        names = [s.name for s in selected]
        answer = QMessageBox.question(
            self.widget, "Quitar del registro",
            "Se quitarán del registro (la carpeta NO se borra):\n\n"
            + "\n".join(names))
        if answer != QMessageBox.Yes:
            return
        self.config.repos = [r for r in self.config.repos
                             if r.name not in names]
        self._save_config()
        self._show_unanalyzed()

    def _toggle_enabled(self) -> None:
        selected = self._selected()
        if not selected:
            return
        for status in selected:
            entry = self.config.find(status.name)
            if entry:
                entry.enabled = not entry.enabled
        self._save_config()
        self._show_unanalyzed()

    def _open_folder(self) -> None:
        selected = self._selected()
        if selected:
            subprocess.Popen(["xdg-open", selected[0].path])

    def _sync_selected(self) -> None:
        names = [s.name for s in self._selected()]
        self.ctx.navigate("sync")
        controller = self.ctx.window.controllers.get("sync")
        if controller and names:
            controller.preselect(names)

    # -------------------------------------------------------------- página
    def refresh(self) -> None:
        previous = {r.name for r in self.config.repos}
        self._load_config()
        if {r.name for r in self.config.repos} != previous:
            self._show_unanalyzed()
