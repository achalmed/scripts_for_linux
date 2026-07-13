"""
controllers/folders_controller.py — Página «Creación masiva de carpetas».

Integra script_create_folders_batch: entrada manual, importación desde
TXT/CSV/Markdown, vista previa, dry-run y deshacer.
"""

import os

from PySide6.QtWidgets import QFileDialog, QTreeWidgetItem

from app.controllers.base import PageController
from app.services import folder_service
from app.services.folder_service import (
    ST_EXISTS,
    ST_FAILED,
    ST_OK,
    ST_REJECTED,
    FolderResult,
)
from app.utils.ui_loader import load_ui
from app.workers.function_worker import FunctionWorker

_STATUS_LABEL = {ST_OK: "✓ se creará", ST_EXISTS: "• ya existe",
                 ST_REJECTED: "✗ rechazada", ST_FAILED: "✗ error"}
_RESULT_LABEL = {ST_OK: "✓ creada", ST_EXISTS: "• ya existía",
                 ST_REJECTED: "✗ rechazada", ST_FAILED: "✗ error"}


class FoldersController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = load_ui("page_folders.ui")
        ui = self.widget

        ui.editBaseDir.setText(ctx.settings.last_directory())
        ui.btnBrowse.clicked.connect(
            lambda: self.browse_directory(ui.editBaseDir))
        ui.btnImport.clicked.connect(self._import_file)
        ui.btnPreview.clicked.connect(self._preview)
        ui.btnCreate.clicked.connect(self._create)
        ui.btnUndo.clicked.connect(self._undo)
        self._refresh_undo_state()

    def set_target_path(self, path: str) -> None:
        self.widget.editBaseDir.setText(path)

    def refresh(self) -> None:
        self._refresh_undo_state()

    # ------------------------------------------------------------- entrada
    def _base_and_names(self) -> tuple[str, list[str]] | None:
        base_dir = self.widget.editBaseDir.text().strip()
        if not base_dir or not os.path.isdir(base_dir):
            self.ctx.status("Selecciona un directorio base válido.")
            return None
        names = folder_service.parse_lines(
            self.widget.editNames.toPlainText())
        if not names:
            self.ctx.status("La lista de carpetas está vacía.")
            return None
        return base_dir, names

    def _import_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self.widget, "Importar lista de carpetas",
            self.ctx.settings.last_directory(),
            "Listas (*.txt *.csv *.md *.markdown);;Todos (*)")
        if not path:
            return
        try:
            names = folder_service.read_names_from_file(path)
        except OSError as exc:
            self.ctx.console.log("error", f"No se pudo importar: {exc}")
            return
        self.widget.editNames.setPlainText("\n".join(names))
        self.ctx.console.log(
            "ok", f"Importadas {len(names)} carpeta(s) desde {path}")
        self._preview()

    # --------------------------------------------------------- vista previa
    def _preview(self) -> None:
        gathered = self._base_and_names()
        if gathered is None:
            return
        base_dir, names = gathered
        items = folder_service.plan_folders(base_dir, names)
        self._fill_tree([(i.name, _STATUS_LABEL[i.status], i.note)
                         for i in items])
        to_create = sum(1 for i in items if i.status == ST_OK)
        self.widget.lblPlanSummary.setText(
            f"Total: {len(items)}  ·  se crearán: {to_create}  ·  "
            f"ya existen: {sum(1 for i in items if i.status == ST_EXISTS)}  ·  "
            f"rechazadas: {sum(1 for i in items if i.status == ST_REJECTED)}")

    def _fill_tree(self, rows: list[tuple[str, str, str]]) -> None:
        tree = self.widget.treePlan
        tree.clear()
        for name, status, note in rows:
            QTreeWidgetItem(tree, [name, status, note])
        for col in range(3):
            tree.resizeColumnToContents(col)

    # ------------------------------------------------------------- creación
    def _create(self) -> None:
        gathered = self._base_and_names()
        if gathered is None:
            return
        base_dir, names = gathered
        dry_run = self.widget.checkDryRun.isChecked()
        self.widget.btnCreate.setEnabled(False)

        worker = FunctionWorker(folder_service.create_folders,
                                base_dir, names, dry_run=dry_run)
        worker.result_ready.connect(self._on_created)
        worker.finished.connect(
            lambda: self.widget.btnCreate.setEnabled(True))
        label = "Simulando creación" if dry_run else "Creando carpetas"
        self.ctx.run_function_worker(worker, f"{label} en {base_dir}")

    def _on_created(self, result: FolderResult) -> None:
        self._fill_tree([(i.name, _RESULT_LABEL[i.status], i.note)
                         for i in result.items])
        summary = (f"Creadas: {result.count(ST_OK)}  ·  "
                   f"ya existían: {result.count(ST_EXISTS)}  ·  "
                   f"rechazadas: {result.count(ST_REJECTED)}  ·  "
                   f"errores: {result.count(ST_FAILED)}")
        if result.dry_run:
            summary = "[SIMULACIÓN] " + summary
        self.widget.lblPlanSummary.setText(summary)

        if not result.dry_run:
            if result.created_paths:
                self.ctx.history.set_undo_journal(result.created_paths)
            self.ctx.history.add_operation(
                "Carpetas",
                f"{result.count(ST_OK)} carpeta(s) creada(s)",
                result.base_dir)
        self._refresh_undo_state()
        self.ctx.status(summary)

    # ------------------------------------------------------------- deshacer
    def _refresh_undo_state(self) -> None:
        self.widget.btnUndo.setEnabled(
            bool(self.ctx.history.undo_journal()))

    def _undo(self) -> None:
        paths = self.ctx.history.undo_journal()
        if not paths:
            return
        worker = FunctionWorker(folder_service.undo_created, paths)
        worker.result_ready.connect(self._on_undone)
        self.ctx.run_function_worker(worker, "Deshaciendo creación de carpetas")

    def _on_undone(self, outcome: tuple[int, list[str]]) -> None:
        removed, kept = outcome
        self.ctx.history.clear_undo_journal()
        self._refresh_undo_state()
        message = f"Deshacer: {removed} carpeta(s) eliminada(s)"
        if kept:
            message += f", {len(kept)} no eliminadas (no vacías)"
        self.ctx.history.add_operation("Carpetas", message)
        self.ctx.status(message)
