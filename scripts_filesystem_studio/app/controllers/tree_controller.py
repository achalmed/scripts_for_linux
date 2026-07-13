"""
controllers/tree_controller.py — Página «Árbol de directorios».

Integra script_proyect_tree: vista previa, exportación con formato y el
modo proyectos que ejecuta el backend intacto mostrando su salida real
en la Consola.
"""

import os

from app.controllers.base import PageController
from app.services import tree_service
from app.utils.ui_loader import load_ui
from app.workers.function_worker import FunctionWorker
from app.workers.process_worker import ProcessWorker

_FILTERS = {"txt": "Texto (*.txt)", "md": "Markdown (*.md)",
            "json": "JSON (*.json)"}


class TreeController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = load_ui("page_tree.ui")
        ui = self.widget
        settings = ctx.settings

        ui.editDirectory.setText(settings.last_directory())
        ui.spinDepth.setValue(settings.default_depth())
        ui.editExcludeDirs.setText(", ".join(settings.exclude_dirs()))
        ui.editExcludeFiles.setText(", ".join(settings.exclude_files()))

        ui.btnBrowse.clicked.connect(
            lambda: self.browse_directory(ui.editDirectory))
        ui.btnPreview.clicked.connect(self._preview)
        ui.btnSaveHere.clicked.connect(self._save_in_folder)
        ui.btnExport.clicked.connect(self._export)
        ui.btnBackendRun.clicked.connect(self._run_backend)

    # -------------------------------------------------------- integración
    def set_target_path(self, path: str) -> None:
        self.widget.editDirectory.setText(path)

    # ----------------------------------------------------------- acciones
    def _gather(self) -> dict | None:
        ui = self.widget
        directory = ui.editDirectory.text().strip()
        if not directory or not os.path.isdir(directory):
            self.ctx.status("Selecciona una carpeta válida.")
            return None
        return dict(
            directory=directory,
            depth=ui.spinDepth.value(),
            exclude_dirs=self.parse_csv_list(ui.editExcludeDirs.text()),
            exclude_files=self.parse_csv_list(ui.editExcludeFiles.text()),
            fmt=ui.comboFormat.currentText(),
            with_meta=ui.checkMeta.isChecked(),
        )

    def _generate(self, on_done) -> None:
        params = self._gather()
        if params is None:
            return
        worker = FunctionWorker(tree_service.generate_tree, **params)
        worker.result_ready.connect(lambda text: on_done(text, params))
        self.ctx.run_function_worker(
            worker, f"Árbol de {params['directory']}")

    def _preview(self) -> None:
        self._generate(lambda text, params:
                       self.widget.previewText.setPlainText(text))

    def _save_in_folder(self) -> None:
        def done(text: str, params: dict) -> None:
            out_path = os.path.join(
                params["directory"],
                tree_service.output_filename(params["fmt"]))
            from app.services.export_service import save_text
            save_text(text, out_path)
            self.widget.previewText.setPlainText(text)
            self.ctx.history.add_operation(
                "Árbol", f"Estructura generada ({params['fmt']})", out_path)
            self.ctx.history.add_report("Árbol", out_path)
            self.ctx.console.log("ok", f"Guardado: {out_path}")
            self.ctx.status(f"Guardado: {out_path}")

        self._generate(done)

    def _export(self) -> None:
        params = self._gather()
        if params is None:
            return
        fmt = params["fmt"]
        suggested = os.path.join(
            self.ctx.settings.reports_dir(),
            tree_service.output_filename(fmt))
        path = self.save_file_dialog("Exportar árbol", suggested,
                                     _FILTERS[fmt])
        if not path:
            return

        def done(text: str, _params: dict) -> None:
            from app.services.export_service import save_text
            save_text(text, path)
            self.widget.previewText.setPlainText(text)
            self.ctx.history.add_operation("Árbol", f"Exportado ({fmt})", path)
            self.ctx.history.add_report("Árbol", path)
            self.ctx.console.log("ok", f"Exportado: {path}")

        worker = FunctionWorker(tree_service.generate_tree, **params)
        worker.result_ready.connect(lambda text: done(text, params))
        self.ctx.run_function_worker(
            worker, f"Exportando árbol de {params['directory']}")

    def _run_backend(self) -> None:
        ui = self.widget
        argv, cwd = tree_service.backend_argv(
            target=ui.comboTarget.currentText(),
            fmt=ui.comboFormat.currentText(),
            depth=ui.spinDepth.value(),
            dry_run=ui.checkBackendDry.isChecked(),
        )
        worker = ProcessWorker(argv, cwd=cwd,
                               description="proyect_tree backend")
        worker.finished_with_code.connect(self._backend_done)
        self.ctx.run_process_worker(
            worker, f"Backend proyect_tree — target {ui.comboTarget.currentText()}")

    def _backend_done(self, code: int) -> None:
        if code == 0:
            self.ctx.history.add_operation(
                "Árbol", "Estructuras de proyectos actualizadas (backend)")
        self.ctx.status(f"Backend proyect_tree terminó con código {code}")
