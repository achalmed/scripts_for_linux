"""
models/repo_status_model.py — Modelo de tabla de repositorios.

QAbstractTableModel sobre la lista de RepoStatus que produce
status_service. Colorea la columna Estado con la misma semántica que
status_color_for() del reporte CLI (rojo/amarillo/cian/verde).
"""

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QBrush, QColor

from app.services.status_service import (
    STATUS_BEHIND,
    STATUS_CLEAN,
    STATUS_DIVERGED,
    STATUS_UNCOMMITTED,
    STATUS_UNPUSHED,
    RepoStatus,
)

_HEADERS = ["Repositorio", "Rama", "Estado", "Cambios", "Último commit"]

# Port de status_color_for(): mismos colores semánticos que la CLI
_STATUS_COLORS = {
    STATUS_UNCOMMITTED: "#f7768e",   # rojo
    STATUS_DIVERGED: "#f7768e",      # rojo
    STATUS_UNPUSHED: "#e0af68",      # amarillo
    STATUS_BEHIND: "#7dcfff",        # cian
    STATUS_CLEAN: "#9ece6a",         # verde
}


class RepoStatusModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: list[RepoStatus] = []

    # ------------------------------------------------------------------ API
    def set_statuses(self, rows: list[RepoStatus]) -> None:
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def status_at(self, row: int) -> RepoStatus | None:
        return self._rows[row] if 0 <= row < len(self._rows) else None

    def statuses(self) -> list[RepoStatus]:
        return list(self._rows)

    # ------------------------------------------------------------ Qt model
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(_HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return _HEADERS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        repo = self._rows[index.row()]
        column = index.column()

        if role == Qt.DisplayRole:
            return [repo.name, repo.branch, repo.status,
                    repo.changes_summary(), repo.last_commit][column]

        if role == Qt.ForegroundRole and column == 2:
            color = _STATUS_COLORS.get(repo.status)
            if color:
                return QBrush(QColor(color))

        if role == Qt.ToolTipRole:
            return (f"{repo.path}\n"
                    f"Sin commit: {repo.uncommitted} · "
                    f"Sin push: {repo.ahead} · "
                    f"Pull pendiente: {repo.behind}")
        return None
