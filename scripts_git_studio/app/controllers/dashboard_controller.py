"""
controllers/dashboard_controller.py — Página inicial «Dashboard».

Contenido dinámico (se reconstruye al entrar a la página), por eso se
construye en código y no en .ui: resumen del último análisis de estado,
repos que necesitan atención, operaciones recientes y accesos directos.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.controllers.base import PageController
from app.services.status_service import STATUS_CLEAN
from app.utils.icons import get_icon

_SHORTCUTS = [
    ("Repositorios", "repos", "repos"),
    ("Sincronizar", "sync", "sync"),
    ("Clonar", "clone", "clone"),
    ("Reportes", "reports", "reports"),
]


class DashboardController(PageController):
    def __init__(self, ctx):
        super().__init__(ctx)
        self.widget = QWidget()
        root = QVBoxLayout(self.widget)

        title = QLabel("Git Studio")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        subtitle = QLabel("Administración unificada de repositorios Git")
        root.addWidget(title)
        root.addWidget(subtitle)

        grid = QGridLayout()
        root.addLayout(grid, 1)

        # ------------------------------------------------ accesos directos
        group_shortcuts = QGroupBox("Accesos directos")
        sc_layout = QGridLayout(group_shortcuts)
        for index, (label, icon, page_id) in enumerate(_SHORTCUTS):
            button = QPushButton(get_icon(icon), f"  {label}")
            button.setMinimumHeight(40)
            button.clicked.connect(
                lambda _=False, p=page_id: self.ctx.navigate(p))
            sc_layout.addWidget(button, index // 2, index % 2)
        grid.addWidget(group_shortcuts, 0, 0)

        # -------------------------------------------------- resumen global
        group_summary = QGroupBox("Resumen del último análisis")
        summary_layout = QVBoxLayout(group_summary)
        self.lbl_clean = QLabel("—")
        self.lbl_dirty = QLabel("—")
        self.lbl_behind = QLabel("—")
        summary_layout.addWidget(self.lbl_clean)
        summary_layout.addWidget(self.lbl_dirty)
        summary_layout.addWidget(self.lbl_behind)
        btn_analyze = QPushButton(get_icon("repos"),
                                  "  Analizar estado ahora")
        btn_analyze.clicked.connect(lambda: self.ctx.navigate("repos"))
        summary_layout.addWidget(btn_analyze)
        summary_layout.addStretch(1)
        grid.addWidget(group_summary, 0, 1)

        # -------------------------------------- repos que piden atención
        self.list_attention = QListWidget()
        self.list_attention.itemDoubleClicked.connect(
            lambda _item: self.ctx.navigate("repos"))
        grid.addWidget(self._boxed(
            "Repositorios que necesitan atención (doble clic → Repositorios)",
            self.list_attention), 1, 0)

        # ------------------------------------------- operaciones recientes
        self.list_ops = QListWidget()
        grid.addWidget(self._boxed("Operaciones recientes", self.list_ops),
                       1, 1)

        self.refresh()

    @staticmethod
    def _boxed(title: str, widget: QWidget) -> QGroupBox:
        box = QGroupBox(title)
        layout = QHBoxLayout(box)
        layout.addWidget(widget)
        return box

    # ------------------------------------------------------------- refresh
    def refresh(self) -> None:
        statuses = self.ctx.last_statuses
        if statuses:
            clean = sum(1 for s in statuses if s.status == STATUS_CLEAN)
            behind = sum(1 for s in statuses if s.behind > 0)
            self.lbl_clean.setText(f"Sincronizados: {clean}")
            self.lbl_dirty.setText(f"Con cambios: {len(statuses) - clean}")
            self.lbl_behind.setText(f"Detrás de origin: {behind}")
        else:
            self.lbl_clean.setText("Aún no se ha analizado el estado.")
            self.lbl_dirty.setText("")
            self.lbl_behind.setText("")

        self.list_attention.clear()
        for repo in statuses:
            if repo.status == STATUS_CLEAN:
                continue
            item = QListWidgetItem(
                get_icon("repos"),
                f"{repo.name}  ·  {repo.status}  ·  {repo.changes_summary()}")
            item.setData(Qt.UserRole, repo.name)
            self.list_attention.addItem(item)
        if statuses and self.list_attention.count() == 0:
            self.list_attention.addItem("Todos los repos están sincronizados ✓")

        self.list_ops.clear()
        for op in self.ctx.history.recent_operations(12):
            self.list_ops.addItem(
                f"{op['when']}  ·  [{op['module']}]  {op['description']}")
        if self.list_ops.count() == 0:
            self.list_ops.addItem("Sin operaciones todavía.")
