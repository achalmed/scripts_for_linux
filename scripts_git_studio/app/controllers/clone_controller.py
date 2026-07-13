"""
controllers/clone_controller.py — Página «Clonar».

Equivalente GUI de script_git_download_respos: consulta la lista de
repos del usuario vía API de GitHub (github_service), permite marcar
cuáles clonar (los modos all/list/single del CLI se reducen a marcar
casillas) y clona con las mismas opciones: profundidad, protocolo,
rama, exclusiones, forks, snapshot sin .git y dry-run.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem

from app.controllers.base import PageController
from app.services import clone_service, github_service
from app.services.config_service import RepoEntry
from app.utils.ui_loader import load_ui
from app.workers.function_worker import FunctionWorker

ST = clone_service


class CloneController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = load_ui("page_clone.ui")
        self._remote_repos: list[github_service.RemoteRepo] = []
        ui = self.widget

        settings = self.ctx.settings
        ui.editUser.setText(settings.github_user())
        ui.editDest.setText(settings.clone_dest_dir())
        ui.comboDepth.setCurrentText(settings.clone_depth())
        ui.comboProtocol.setCurrentText(settings.clone_protocol())
        ui.editExclude.setText(", ".join(settings.clone_exclude()))

        ui.btnFetchList.clicked.connect(self._fetch_list)
        ui.btnBrowseDest.clicked.connect(
            lambda: self.browse_directory(ui.editDest, "Carpeta destino"))
        ui.btnMarkAll.clicked.connect(lambda: self._mark_all(True))
        ui.btnMarkNone.clicked.connect(lambda: self._mark_all(False))
        ui.btnClone.clicked.connect(self._clone)

    # ------------------------------------------------------------ API list
    def _fetch_list(self) -> None:
        user = self.widget.editUser.text().strip()
        if not user:
            self.ctx.status("Indica el usuario u organización de GitHub.")
            return
        token = (self.widget.editToken.text().strip()
                 or self.ctx.settings.github_token_from_env())
        self.ctx.settings.set_github_user(user)

        worker = FunctionWorker(self._fetch_repos_task, user, token,
                                description="consulta API GitHub")
        worker.result_ready.connect(self._on_list)
        self.ctx.run_function_worker(worker, f"Consultando repos de {user}…")

    @staticmethod
    def _fetch_repos_task(user, token, progress_cb=None, cancel_cb=None,
                          message_cb=None):
        if progress_cb:
            progress_cb(-1, f"usuarios/{user}/repos")
        repos = github_service.fetch_all_repos(user, token)
        if message_cb:
            message_cb("info", f"Se encontraron {len(repos)} repos.")
        return repos

    def _on_list(self, repos) -> None:
        self._remote_repos = repos
        widget_list = self.widget.listRemote
        widget_list.clear()
        for repo in repos:
            label = repo.name + (" (fork)" if repo.is_fork else "")
            if repo.description:
                label += f" — {repo.description}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, repo.name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            widget_list.addItem(item)
        self.ctx.status(f"{len(repos)} repos remotos listados.")

    def _mark_all(self, checked: bool) -> None:
        state = Qt.Checked if checked else Qt.Unchecked
        for i in range(self.widget.listRemote.count()):
            self.widget.listRemote.item(i).setCheckState(state)

    # -------------------------------------------------------------- clonado
    def _clone(self) -> None:
        ui = self.widget
        checked_names = {
            ui.listRemote.item(i).data(Qt.UserRole)
            for i in range(ui.listRemote.count())
            if ui.listRemote.item(i).checkState() == Qt.Checked}
        selection = [r for r in self._remote_repos
                     if r.name in checked_names]
        if not selection:
            self.ctx.status("Consulta la API y marca al menos un repo.")
            return

        options = clone_service.CloneOptions(
            user=ui.editUser.text().strip(),
            dest_dir=ui.editDest.text().strip(),
            depth=ui.comboDepth.currentText().strip() or "1",
            protocol=ui.comboProtocol.currentText(),
            branch=ui.editBranch.text().strip(),
            strip_git=ui.chkStripGit.isChecked(),
            include_forks=ui.chkIncludeForks.isChecked(),
            exclude=self.parse_csv_list(ui.editExclude.text()),
            dry_run=ui.chkDryRun.isChecked(),
        )
        if not options.dest_dir:
            self.ctx.status("Indica la carpeta destino.")
            return

        settings = self.ctx.settings
        settings.set_clone_dest_dir(options.dest_dir)
        settings.set_clone_depth(options.depth)
        settings.set_clone_protocol(options.protocol)
        settings.set_clone_exclude(options.exclude)

        worker = FunctionWorker(
            clone_service.clone_repos, options, selection,
            description="clonado")
        worker.result_ready.connect(
            lambda report: self._on_cloned(report, options))
        task = ("Simulando clonado…" if options.dry_run
                else "Clonando repositorios…")
        self.ctx.run_function_worker(worker, task)

    def _on_cloned(self, report: clone_service.CloneReport,
                   options: clone_service.CloneOptions) -> None:
        summary = (f"Descargados: {report.count(ST.ST_CLONED)} · "
                   f"Omitidos: {report.count(ST.ST_SKIPPED)} · "
                   f"Fallidos: {report.count(ST.ST_FAILED)}")
        if report.dry_run:
            summary = f"[DRY-RUN] {summary}"
        self.widget.lblSummary.setText(summary)
        self.ctx.status(summary)
        self.ctx.history.add_operation("clone", summary, options.dest_dir)

        if self.widget.chkRegister.isChecked() and not report.dry_run:
            self._register_cloned(report, options)

    def _register_cloned(self, report: clone_service.CloneReport,
                         options: clone_service.CloneOptions) -> None:
        """Alta de los repos clonados en repos-config.yml, para que
        Sincronizar y Estado los gestionen de inmediato."""
        config = self.ctx.config.load()
        if not config.base_dir:
            config.base_dir = options.dest_dir
        if config.base_dir != options.dest_dir:
            self.ctx.console.log(
                "warn", "El destino no coincide con base_directory del "
                        "registro; no se registran los clonados.")
            return
        by_name = {r.name: r for r in self._remote_repos}
        added = 0
        for item in report.items:
            if item.status != ST.ST_CLONED or config.find(item.name):
                continue
            remote = by_name.get(item.name)
            branch = (options.branch
                      or (remote.default_branch if remote else "main"))
            config.repos.append(RepoEntry(name=item.name, branch=branch))
            added += 1
        if added:
            self.ctx.config.save(config)
            self.ctx.console.log(
                "ok", f"{added} repos registrados en repos-config.yml.")
