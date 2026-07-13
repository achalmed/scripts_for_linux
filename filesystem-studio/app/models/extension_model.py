"""
models/extension_model.py — Modelo de tabla para estadísticas por extensión.

QAbstractTableModel con roles de ordenación numérica (Qt.UserRole) para
que el proxy ordene por valor real y no alfabéticamente.
"""

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
)

from app.services.scanner_service import ExtensionEntry
from app.utils.format import format_size

HEADERS = ["Extensión", "Cantidad", "Tamaño", "% archivos"]


class ExtensionTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._entries: list[ExtensionEntry] = []
        self._total_files = 0

    def set_entries(self, entries: list[ExtensionEntry],
                    total_files: int) -> None:
        self.beginResetModel()
        self._entries = entries
        self._total_files = max(total_files, 1)
        self.endResetModel()

    # ----------------------------------------------------------- overrides
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._entries)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return HEADERS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        entry = self._entries[index.row()]
        col = index.column()
        percent = entry.count * 100 / self._total_files

        if role == Qt.DisplayRole:
            return [f".{entry.extension}", f"{entry.count:,}",
                    format_size(entry.size), f"{percent:.1f} %"][col]
        if role == Qt.UserRole:  # valor crudo para ordenar
            return [entry.extension, entry.count, entry.size, percent][col]
        if role == Qt.TextAlignmentRole and col > 0:
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None

    # ------------------------------------------------------------- helpers
    def entry_at(self, row: int) -> ExtensionEntry | None:
        return self._entries[row] if 0 <= row < len(self._entries) else None

    def export_rows(self) -> list[list]:
        return [[f".{e.extension}", e.count, e.size,
                 round(e.count * 100 / self._total_files, 2)]
                for e in self._entries]


def make_proxy(model: ExtensionTableModel) -> QSortFilterProxyModel:
    proxy = QSortFilterProxyModel()
    proxy.setSourceModel(model)
    proxy.setSortRole(Qt.UserRole)
    proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
    proxy.setFilterKeyColumn(0)
    return proxy
