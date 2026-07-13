"""
controllers/hardlinks_controller.py — Página «Hardlinks» (módulo unificado).

Une script_hardlinks-detector y script_hardlinks-creator en un solo
módulo con tres pestañas: Detectar, Crear y Reportes.
"""

import os

from PySide6.QtWidgets import QFileDialog, QTreeWidgetItem

from app.controllers.base import PageController
from app.services import export_service, hardlink_service
from app.services.hardlink_service import DetectionResult, LinkPlan
from app.utils.format import format_size, stamp_for_filename
from app.utils.ui_loader import load_ui
from app.workers.function_worker import FunctionWorker


class HardlinksController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = load_ui("page_hardlinks.ui")
        self.detection: DetectionResult | None = None
        self.plan: LinkPlan | None = None
        self.report_md: str = ""
        ui = self.widget

        last = ctx.settings.last_directory()
        ui.editDetectDir.setText(last)
        ui.editCreateDir.setText(last)

        # --------------------------------------------------------- Detectar
        ui.btnDetectBrowse.clicked.connect(
            lambda: self.browse_directory(ui.editDetectDir))
        ui.btnDetect.clicked.connect(self._detect)
        ui.btnDetectCsv.clicked.connect(lambda: self._export_detect("csv"))
        ui.btnDetectJson.clicked.connect(lambda: self._export_detect("json"))
        ui.btnDetectReport.clicked.connect(self._make_report)

        # ------------------------------------------------------------ Crear
        ui.btnCreateBrowse.clicked.connect(
            lambda: self.browse_directory(ui.editCreateDir))
        ui.btnPickFile.clicked.connect(self._pick_file)
        ui.btnPlan.clicked.connect(self._plan)
        ui.btnApply.clicked.connect(self._apply)

        # --------------------------------------------------------- Reportes
        ui.btnReportMd.clicked.connect(lambda: self._export_report("md"))
        ui.btnReportHtml.clicked.connect(lambda: self._export_report("html"))
        ui.btnReportPdf.clicked.connect(lambda: self._export_report("pdf"))

    def set_target_path(self, path: str) -> None:
        self.widget.editDetectDir.setText(path)
        self.widget.editCreateDir.setText(path)

    # ================================================================ DETECT
    def _detect(self) -> None:
        ui = self.widget
        directory = ui.editDetectDir.text().strip()
        if not directory or not os.path.isdir(directory):
            self.ctx.status("Selecciona una carpeta válida.")
            return
        ui.btnDetect.setEnabled(False)
        worker = FunctionWorker(hardlink_service.detect_hardlinks,
                                directory, ui.spinMinLinks.value())
        worker.result_ready.connect(self._on_detected)
        worker.finished.connect(lambda: ui.btnDetect.setEnabled(True))
        self.ctx.run_function_worker(
            worker, f"Detectando hardlinks en {directory}")

    def _on_detected(self, result: DetectionResult) -> None:
        self.detection = result
        tree = self.widget.treeDetect
        tree.clear()
        for num, group in enumerate(result.groups, start=1):
            main_file = os.path.relpath(group.paths[0], result.directory)
            parent = QTreeWidgetItem(tree, [
                f"Conjunto #{num} — {main_file}",
                str(group.inode), str(group.nlinks),
                format_size(group.size), format_size(group.saved_bytes)])
            for path in group.paths:
                QTreeWidgetItem(parent, [
                    os.path.relpath(path, result.directory), "", "", "", ""])
            outside = group.nlinks - len(group.paths)
            if outside > 0:
                QTreeWidgetItem(parent, [
                    f"⚠ {outside} enlace(s) fuera del directorio analizado",
                    "", "", "", ""])
        for col in range(5):
            tree.resizeColumnToContents(col)

        self.widget.lblDetectSummary.setText(
            f"Conjuntos: {len(result.groups)}  ·  "
            f"Espacio usado: {format_size(result.total_space_used)}  ·  "
            f"Espacio ahorrado: {format_size(result.total_space_saved)}  ·  "
            f"Archivos revisados: {result.scanned_files:,}")
        self.ctx.history.add_operation(
            "Hardlinks", f"Detección: {len(result.groups)} conjunto(s)",
            result.directory)

    def _export_detect(self, fmt: str) -> None:
        if self.detection is None:
            self.ctx.status("No hay detección que exportar.")
            return
        result = self.detection
        suggested = os.path.join(
            self.ctx.settings.reports_dir(),
            f"hardlinks-{stamp_for_filename()}.{fmt}")
        filters = {"csv": "CSV (*.csv)", "json": "JSON (*.json)"}
        path = self.save_file_dialog("Exportar detección", suggested,
                                     filters[fmt])
        if not path:
            return
        if fmt == "csv":
            # Mismo esquema que render_csv() del detector original
            rows = [[g.inode, g.nlinks, g.size,
                     os.path.relpath(p, result.directory)]
                    for g in result.groups for p in g.paths]
            export_service.save_csv(
                ["inode", "nlinks", "size_bytes", "relative_path"],
                rows, path)
        else:
            # Mismo esquema que render_json() del detector original
            data = {
                "tool": "filesystem-studio/hardlinks",
                "directory": result.directory,
                "total_groups": len(result.groups),
                "total_space_saved_bytes": result.total_space_saved,
                "groups": [
                    {"inode": g.inode, "nlinks": g.nlinks,
                     "size_bytes": g.size,
                     "files": [os.path.relpath(p, result.directory)
                               for p in g.paths]}
                    for g in result.groups],
            }
            export_service.save_json(data, path)
        self.ctx.history.add_report("Hardlinks", path)
        self.ctx.console.log("ok", f"Exportado: {path}")

    def _make_report(self) -> None:
        if self.detection is None:
            self.ctx.status("Ejecuta primero una detección.")
            return
        self.report_md = hardlink_service.build_markdown_report(self.detection)
        out_path = os.path.join(self.ctx.settings.reports_dir(),
                                f"hardlinks-report-{stamp_for_filename()}.md")
        export_service.save_text(self.report_md, out_path)
        self.ctx.history.add_report("Hardlinks", out_path,
                                    "Reporte de auditoría")
        self.widget.reportView.setMarkdown(self.report_md)
        self.widget.lblReportInfo.setText(f"Reporte generado: {out_path}")
        self.widget.tabs.setCurrentWidget(self.widget.tabReports)
        self.ctx.console.log("ok", f"Reporte generado: {out_path}")

    # ================================================================ CREATE
    def _pick_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self.widget, "Elegir archivo de referencia",
            self.widget.editCreateDir.text().strip()
            or self.ctx.settings.last_directory())
        if path:
            self.widget.editFilename.setText(os.path.basename(path))
            self.widget.editCreateDir.setText(os.path.dirname(path))

    def _plan(self) -> None:
        ui = self.widget
        directory = ui.editCreateDir.text().strip()
        filename = ui.editFilename.text().strip()
        if not directory or not os.path.isdir(directory):
            self.ctx.status("Selecciona una carpeta válida.")
            return
        if not filename or "/" in filename:
            self.ctx.status("Indica un nombre de archivo sin ruta.")
            return
        ui.btnPlan.setEnabled(False)
        ui.btnApply.setEnabled(False)
        worker = FunctionWorker(
            hardlink_service.plan_links, directory, filename,
            exclusions=self.ctx.settings.exclude_dirs())
        worker.result_ready.connect(self._on_planned)
        worker.finished.connect(lambda: ui.btnPlan.setEnabled(True))
        self.ctx.run_function_worker(
            worker, f"Buscando duplicados de '{filename}'")

    def _on_planned(self, plan: LinkPlan) -> None:
        self.plan = plan
        tree = self.widget.treePlan
        tree.clear()
        for num, group in enumerate(plan.groups, start=1):
            parent = QTreeWidgetItem(tree, [
                f"Grupo #{num} — {group.file_hash[:12]}… "
                f"({format_size(group.size)})", ""])
            QTreeWidgetItem(parent, [
                os.path.relpath(group.source, plan.directory), "fuente"])
            for path in group.already_linked:
                QTreeWidgetItem(parent, [
                    os.path.relpath(path, plan.directory), "ya enlazado"])
            for cand in group.candidates:
                status = ("se enlazará" if cand.valid
                          else f"omitido: {cand.reason}")
                QTreeWidgetItem(parent, [
                    os.path.relpath(cand.path, plan.directory), status])
        tree.expandAll()
        tree.resizeColumnToContents(0)

        total = plan.total_valid
        self.widget.lblPlanSummary.setText(
            f"{len(plan.groups)} grupo(s) idéntico(s), "
            f"{total} enlace(s) por crear")
        self.widget.btnApply.setEnabled(total > 0)
        if not plan.groups:
            self.ctx.status("No se encontraron duplicados por contenido.")

    def _apply(self) -> None:
        if self.plan is None or self.plan.total_valid == 0:
            return
        dry_run = self.widget.checkCreateDry.isChecked()
        self.widget.btnApply.setEnabled(False)
        worker = FunctionWorker(hardlink_service.apply_link_plan,
                                self.plan, dry_run=dry_run)
        worker.result_ready.connect(
            lambda stats: self._on_applied(stats, dry_run))
        label = ("Simulando creación de hardlinks" if dry_run
                 else "Creando hardlinks")
        self.ctx.run_function_worker(worker, label)

    def _on_applied(self, stats: dict, dry_run: bool) -> None:
        prefix = "[SIMULACIÓN] " if dry_run else ""
        message = (f"{prefix}Enlaces creados: {stats['links_created']}  ·  "
                   f"grupos: {stats['groups_created']}/{stats['groups_found']}"
                   f"  ·  errores: {stats['errors']}")
        self.widget.lblPlanSummary.setText(message)
        self.ctx.status(message)
        if not dry_run:
            self.ctx.history.add_operation(
                "Hardlinks",
                f"{stats['links_created']} hard link(s) creados",
                self.plan.directory if self.plan else None)
            self.widget.btnApply.setEnabled(False)
            self.plan = None

    # =============================================================== REPORTS
    def _export_report(self, fmt: str) -> None:
        if not self.report_md:
            self.ctx.status("Genera primero un reporte en «Detectar».")
            return
        suggested = os.path.join(
            self.ctx.settings.reports_dir(),
            f"hardlinks-report-{stamp_for_filename()}.{fmt}")
        filters = {"md": "Markdown (*.md)", "html": "HTML (*.html)",
                   "pdf": "PDF (*.pdf)"}
        path = self.save_file_dialog("Exportar reporte", suggested,
                                     filters[fmt])
        if not path:
            return
        if fmt == "md":
            export_service.save_text(self.report_md, path)
        else:
            html = export_service.markdown_to_html(
                self.report_md, "Reporte de Hardlinks")
            if fmt == "html":
                export_service.save_html(html, path)
            else:
                export_service.save_pdf_from_html(html, path)
        self.ctx.history.add_report("Hardlinks", path)
        self.ctx.console.log("ok", f"Reporte exportado: {path}")
