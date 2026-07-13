"""
controllers/stats_controller.py — Página «Estadísticas por extensión».

Integra script_count_files_by_extension: escaneo recursivo con
exclusiones, tabla ordenable/filtrable, gráfico de pastel (QtCharts)
y exportación a CSV, Markdown y Excel.
"""

import os

from PySide6.QtGui import QPainter

from app.controllers.base import PageController
from app.models.extension_model import ExtensionTableModel, make_proxy
from app.services import export_service
from app.services.scanner_service import ScanResult, scan_extensions
from app.utils.format import format_size, stamp_for_filename
from app.utils.ui_loader import load_ui
from app.workers.function_worker import FunctionWorker

try:
    from PySide6.QtCharts import QChart, QChartView, QPieSeries
    _CHARTS = True
except ImportError:
    _CHARTS = False

_TOP_SLICES = 8


class StatsController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = load_ui("page_stats.ui")
        self.result: ScanResult | None = None
        ui = self.widget

        ui.editDirectory.setText(ctx.settings.last_directory())
        ui.editExcludeDirs.setText(", ".join(ctx.settings.exclude_dirs()))

        self.model = ExtensionTableModel()
        self.proxy = make_proxy(self.model)
        ui.tableView.setModel(self.proxy)
        ui.editFilter.textChanged.connect(self.proxy.setFilterFixedString)

        if _CHARTS:
            self.chart = QChart()
            self.chart.setTitle("Distribución por extensión")
            self.chart_view = QChartView(self.chart)
            self.chart_view.setRenderHint(QPainter.Antialiasing)
            ui.chartContainer.layout().addWidget(self.chart_view)
        else:
            from PySide6.QtWidgets import QLabel
            ui.chartContainer.layout().addWidget(
                QLabel("QtCharts no disponible — instala PySide6-Addons."))

        ui.btnBrowse.clicked.connect(
            lambda: self.browse_directory(ui.editDirectory))
        ui.btnScan.clicked.connect(self._scan)
        ui.btnExportCsv.clicked.connect(lambda: self._export("csv"))
        ui.btnExportMd.clicked.connect(lambda: self._export("md"))
        ui.btnExportXlsx.clicked.connect(lambda: self._export("xlsx"))

    def set_target_path(self, path: str) -> None:
        self.widget.editDirectory.setText(path)

    # ------------------------------------------------------------- escaneo
    def _scan(self) -> None:
        ui = self.widget
        directory = ui.editDirectory.text().strip()
        if not directory or not os.path.isdir(directory):
            self.ctx.status("Selecciona una carpeta válida.")
            return
        exclude = self.parse_csv_list(ui.editExcludeDirs.text())
        ui.btnScan.setEnabled(False)

        worker = FunctionWorker(scan_extensions, directory,
                                exclude_dirs=exclude)
        worker.result_ready.connect(self._on_result)
        worker.finished.connect(lambda: ui.btnScan.setEnabled(True))
        self.ctx.run_function_worker(worker, f"Escaneando {directory}")

    def _on_result(self, result: ScanResult) -> None:
        self.result = result
        entries = result.sorted_entries()
        self.model.set_entries(entries, result.total_files)
        self.widget.tableView.resizeColumnsToContents()
        self.widget.lblSummary.setText(
            f"Archivos: {result.total_files:,}  ·  "
            f"Directorios: {result.total_dirs:,}  ·  "
            f"Tamaño total: {format_size(result.total_size)}  ·  "
            f"Extensiones distintas: {len(entries)}")
        self._update_chart(entries, result.total_files)
        self.ctx.history.add_operation(
            "Estadísticas",
            f"Escaneadas {result.total_files:,} archivos", result.directory)

    def _update_chart(self, entries, total_files: int) -> None:
        if not _CHARTS or total_files == 0:
            return
        series = QPieSeries()
        top = entries[:_TOP_SLICES]
        rest = sum(e.count for e in entries[_TOP_SLICES:])
        for entry in top:
            series.append(f".{entry.extension} ({entry.count})", entry.count)
        if rest:
            series.append(f"otras ({rest})", rest)
        self.chart.removeAllSeries()
        self.chart.addSeries(series)

    # ---------------------------------------------------------- exportación
    def _export(self, fmt: str) -> None:
        if self.result is None or not self.model.export_rows():
            self.ctx.status("No hay resultados que exportar. Escanea primero.")
            return
        base = os.path.basename(self.result.directory) or "raiz"
        suggested = os.path.join(
            self.ctx.settings.reports_dir(),
            f"extensiones-{base}-{stamp_for_filename()}.{fmt}")
        filters = {"csv": "CSV (*.csv)", "md": "Markdown (*.md)",
                   "xlsx": "Excel (*.xlsx)"}
        path = self.save_file_dialog("Exportar estadísticas", suggested,
                                     filters[fmt])
        if not path:
            return

        headers = ["Extensión", "Cantidad", "Tamaño (bytes)", "% archivos"]
        rows = self.model.export_rows()
        try:
            if fmt == "csv":
                export_service.save_csv(headers, rows, path)
            elif fmt == "md":
                export_service.save_markdown_table(
                    f"Archivos por extensión — {self.result.directory}",
                    headers, rows, path,
                    intro=self.widget.lblSummary.text())
            else:
                export_service.save_excel(headers, rows, path,
                                          sheet_title="Extensiones")
        except RuntimeError as exc:
            self.ctx.console.log("error", str(exc))
            self.ctx.status(str(exc))
            return

        self.ctx.history.add_operation("Estadísticas",
                                       f"Exportado ({fmt})", path)
        self.ctx.history.add_report("Estadísticas", path)
        self.ctx.console.log("ok", f"Exportado: {path}")
        self.ctx.status(f"Exportado: {path}")
