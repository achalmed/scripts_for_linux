#!/usr/bin/env python3
"""lib/lista_viva.py — Ventana para cerrar apps, con la RAM al día.

La abre lib/cierre.sh con el Python del sistema (PyQt6). Cada segundo lee
/proc/meminfo y cada --cada-apps segundos corre la fuente (main.sh apps), que
devuelve «MB|unidades|nombre» por app: la regla de qué es una app y cuáles se
excluyen vive solo en lib/memoria.sh.

La ventana no cierra nada: al pulsar «Cerrar las marcadas» escribe en stdout
una línea «unidades|nombre» por app y cierre.sh, que la está leyendo, la
detiene. La ventana sigue abierta y se ve bajar la RAM. Sale con 0 al cerrarla.
"""
from __future__ import annotations

import argparse
import os
import sys
import time

from PyQt6.QtCore import QProcess, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLabel, QProgressBar, QPushButton,
                             QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

# Colores por nivel (mismo criterio que NIVELES de config.sh: aviso desde --umbral, lista desde --cierre).
COLOR_NORMAL = "#2e9e5b"
COLOR_AVISO = "#e08a00"
COLOR_CRITICO = "#d83b3b"

COL_APP, COL_RAM, COL_PCT, COL_CAMBIO = range(4)


def leer_meminfo() -> dict[str, int]:
    """Valores de /proc/meminfo en kB."""
    datos = {}
    with open("/proc/meminfo", encoding="ascii") as f:
        for linea in f:
            clave, _, resto = linea.partition(":")
            datos[clave] = int(resto.split()[0])
    return datos


def gb(mb: float) -> str:
    return f"{mb / 1024:.1f} GB".replace(".", ",")


def cambio_txt(mb: int) -> str:
    if abs(mb) < 20:
        return "="
    signo = "▲ +" if mb > 0 else "▼ −"
    return f"{signo}{gb(abs(mb))}" if abs(mb) >= 1024 else f"{signo}{abs(mb)} MB"


class ListaViva(QWidget):
    def __init__(self, args: argparse.Namespace):
        super().__init__()
        self.args = args
        self.inicial: dict[str, int] = {}      # nombre → MB al abrir (para «Desde que se abrió»)
        self.cerrando: dict[str, float] = {}   # nombre → cuándo se pidió cerrarla
        self.previo_pct: int | None = None
        self.usada_mb = 0
        self.ultima_lectura = 0.0
        self.proceso: QProcess | None = None
        self.padre = os.getppid()              # cierre.sh, que lee lo que se manda cerrar
        self._armar()
        self._medir_ram()
        self._pedir_apps()
        self.reloj_ram = QTimer(self, interval=1000, timeout=self._medir_ram)
        self.reloj_ram.start()
        self.reloj_apps = QTimer(self, interval=int(args.cada_apps * 1000), timeout=self._pedir_apps)
        self.reloj_apps.start()

    # --- interfaz -------------------------------------------------------
    def _armar(self) -> None:
        self.setWindowTitle(f"{self.args.titulo}: RAM")
        self.resize(520, 460)
        caja = QVBoxLayout(self)

        fila = QHBoxLayout()
        self.lbl_pct = QLabel("–")
        fuente = QFont(self.font())
        fuente.setPointSizeF(fuente.pointSizeF() * 2.4)
        fuente.setBold(True)
        self.lbl_pct.setFont(fuente)
        fila.addWidget(self.lbl_pct)
        detalle = QVBoxLayout()
        self.lbl_uso = QLabel()
        self.lbl_tendencia = QLabel()
        detalle.addWidget(self.lbl_uso)
        detalle.addWidget(self.lbl_tendencia)
        fila.addLayout(detalle, 1)
        caja.addLayout(fila)

        self.barra = QProgressBar(maximum=100, textVisible=False)
        self.barra.setFixedHeight(10)
        caja.addWidget(self.barra)
        self.lbl_swap = QLabel()
        self.lbl_swap.setEnabled(False)
        caja.addWidget(self.lbl_swap)

        caja.addWidget(QLabel("Marca las apps que quieres cerrar. La lista se actualiza sola."))
        self.tabla = QTreeWidget(rootIsDecorated=False, uniformRowHeights=True, alternatingRowColors=True)
        self.tabla.setHeaderLabels(["App", "RAM", "% de la RAM", "Desde que se abrió"])
        cab = self.tabla.header()
        cab.setSectionResizeMode(COL_APP, QHeaderView.ResizeMode.Stretch)
        for col in (COL_RAM, COL_PCT, COL_CAMBIO):
            cab.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            self.tabla.headerItem().setTextAlignment(col, Qt.AlignmentFlag.AlignRight)
        self.tabla.itemChanged.connect(self._al_marcar)
        self.tabla.itemClicked.connect(self._alternar)
        caja.addWidget(self.tabla, 1)

        pie = QHBoxLayout()
        self.lbl_estado = QLabel()
        self.lbl_estado.setEnabled(False)
        pie.addWidget(self.lbl_estado, 1)
        self.btn_cerrar = QPushButton("Cerrar las marcadas")
        self.btn_cerrar.setEnabled(False)
        self.btn_cerrar.clicked.connect(self._cerrar_marcadas)
        pie.addWidget(self.btn_cerrar)
        listo = QPushButton("Listo")
        listo.clicked.connect(self.close)
        pie.addWidget(listo)
        caja.addLayout(pie)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, activated=self.close)

    # --- RAM ------------------------------------------------------------
    def _medir_ram(self) -> None:
        if os.getppid() != self.padre:          # murió cierre.sh: ya nadie cerraría lo marcado
            self.close()
            return
        # mismo cálculo que ram_pct() de lib/memoria.sh: usada = MemTotal − MemAvailable
        m = leer_meminfo()
        total, usada = m["MemTotal"], m["MemTotal"] - m["MemAvailable"]
        pct = usada * 100 // total
        self.usada_mb = usada // 1024
        color = COLOR_CRITICO if pct >= self.args.cierre else COLOR_AVISO if pct >= self.args.umbral else COLOR_NORMAL
        self.setWindowTitle(f"{self.args.titulo}: RAM al {pct}%")
        self.lbl_pct.setText(f"{pct} %")
        self.lbl_pct.setStyleSheet(f"color: {color}")
        self.barra.setValue(pct)
        self.barra.setStyleSheet(f"QProgressBar::chunk {{ background: {color}; }}")
        self.lbl_uso.setText(f"{gb(usada / 1024)} usados de {gb(total / 1024)}")
        if self.previo_pct is not None and pct != self.previo_pct:
            flecha = "▲ sube" if pct > self.previo_pct else "▼ baja"
            self.lbl_tendencia.setText(f"{flecha} ({self.previo_pct} % → {pct} %)")
            self.lbl_tendencia.setStyleSheet(f"color: {COLOR_CRITICO if pct > self.previo_pct else COLOR_NORMAL}")
        elif self.previo_pct is not None:
            self.lbl_tendencia.setText("estable")
            self.lbl_tendencia.setStyleSheet("")
        self.previo_pct = pct
        if m.get("SwapTotal"):
            swap = (m["SwapTotal"] - m["SwapFree"]) / 1024
            self.lbl_swap.setText(f"Swap: {gb(swap)} usados de {gb(m['SwapTotal'] / 1024)}")
        if self.ultima_lectura:
            self.lbl_estado.setText(f"apps al día hace {int(time.monotonic() - self.ultima_lectura)} s")

    # --- apps -------------------------------------------------------------
    def _pedir_apps(self) -> None:
        if self.proceso is not None:            # la lectura anterior aún no termina: no se apilan
            return
        self.proceso = QProcess(self)
        self.proceso.finished.connect(self._leer_apps)
        self.proceso.start(self.args.fuente[0], self.args.fuente[1:])

    def _leer_apps(self) -> None:
        salida = bytes(self.proceso.readAllStandardOutput()).decode("utf-8", "replace")
        self.proceso.deleteLater()
        self.proceso = None
        apps = []
        for linea in salida.splitlines():
            partes = linea.split("|", 2)
            if len(partes) == 3 and partes[0].isdigit():
                apps.append((int(partes[0]), partes[1], partes[2]))
        self.ultima_lectura = time.monotonic()
        self._pintar(apps)

    def _pintar(self, apps: list[tuple[int, str, str]]) -> None:
        marcadas = {it.text(COL_APP) for it in self._filas() if it.checkState(COL_APP) == Qt.CheckState.Checked}
        total_mb = leer_meminfo()["MemTotal"] / 1024
        ahora = time.monotonic()
        presentes = {nombre for _, _, nombre in apps}
        # una app que se pidió cerrar y sigue tras 20 s (no atendió SIGTERM) vuelve a poder marcarse
        self.cerrando = {n: t for n, t in self.cerrando.items() if n in presentes and ahora - t < 20}

        self.tabla.blockSignals(True)
        self.tabla.clear()
        suma = 0
        for mb, unidades, nombre in apps:
            suma += mb
            self.inicial.setdefault(nombre, mb)
            it = QTreeWidgetItem([nombre, gb(mb), f"{mb * 100 / total_mb:.0f} %", cambio_txt(mb - self.inicial[nombre])])
            it.setData(COL_APP, Qt.ItemDataRole.UserRole, unidades)
            it.setData(COL_RAM, Qt.ItemDataRole.UserRole, mb)
            for col in (COL_RAM, COL_PCT, COL_CAMBIO):
                it.setTextAlignment(col, Qt.AlignmentFlag.AlignRight)
            if mb - self.inicial[nombre] >= 20:
                it.setForeground(COL_CAMBIO, QColor(COLOR_CRITICO))
            elif mb - self.inicial[nombre] <= -20:
                it.setForeground(COL_CAMBIO, QColor(COLOR_NORMAL))
            if nombre in self.cerrando:
                it.setText(COL_APP, f"{nombre} (cerrando…)")
                it.setDisabled(True)
            else:
                it.setFlags(it.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                it.setCheckState(COL_APP, Qt.CheckState.Checked if nombre in marcadas else Qt.CheckState.Unchecked)
            self.tabla.addTopLevelItem(it)
        fuera = self.usada_mb - suma
        if fuera > 512:
            it = QTreeWidgetItem(["fuera de tus apps", gb(fuera), f"{fuera * 100 / total_mb:.0f} %", ""])
            it.setToolTip(COL_APP, "Sistema, servicios y contenedores: no se cierran desde aquí.")
            it.setDisabled(True)
            for col in (COL_RAM, COL_PCT):
                it.setTextAlignment(col, Qt.AlignmentFlag.AlignRight)
            self.tabla.addTopLevelItem(it)
        self.tabla.blockSignals(False)
        self._al_marcar()
        self.lbl_estado.setText("apps al día" if apps else "no hay apps tuyas abiertas")

    # --- marcar y cerrar ------------------------------------------------
    def _filas(self) -> list[QTreeWidgetItem]:
        return [self.tabla.topLevelItem(i) for i in range(self.tabla.topLevelItemCount())]

    def _marcadas(self) -> list[QTreeWidgetItem]:
        return [it for it in self._filas() if it.checkState(COL_APP) == Qt.CheckState.Checked and not it.isDisabled()]

    def _alternar(self, it: QTreeWidgetItem, col: int) -> None:
        # un clic en cualquier parte de la fila la marca o desmarca (no solo en la casilla)
        if col != COL_APP and it.flags() & Qt.ItemFlag.ItemIsUserCheckable and not it.isDisabled():
            nuevo = Qt.CheckState.Unchecked if it.checkState(COL_APP) == Qt.CheckState.Checked else Qt.CheckState.Checked
            it.setCheckState(COL_APP, nuevo)

    def _al_marcar(self, *_: object) -> None:
        marcadas = self._marcadas()
        mb = sum(it.data(COL_RAM, Qt.ItemDataRole.UserRole) for it in marcadas)
        self.btn_cerrar.setEnabled(bool(marcadas))
        self.btn_cerrar.setText(f"Cerrar {len(marcadas)} ({gb(mb)})" if marcadas else "Cerrar las marcadas")

    def _cerrar_marcadas(self) -> None:
        ahora = time.monotonic()
        for it in self._marcadas():
            nombre = it.text(COL_APP)
            print(f"{it.data(COL_APP, Qt.ItemDataRole.UserRole)}|{nombre}", flush=True)
            self.cerrando[nombre] = ahora
            it.setCheckState(COL_APP, Qt.CheckState.Unchecked)
            it.setText(COL_APP, f"{nombre} (cerrando…)")
            it.setDisabled(True)
        self._al_marcar()
        self.lbl_estado.setText("cerrando…")
        QTimer.singleShot(500, self._pedir_apps)


def main() -> int:
    p = argparse.ArgumentParser(description="Ventana para cerrar apps con la RAM al día (la abre lib/cierre.sh).")
    p.add_argument("--titulo", required=True, help="prefijo del título; kwin/encima.js.in lo busca")
    p.add_argument("--clase", default="alerta-ram", help="id de la app en Wayland (resourceClass en KWin)")
    p.add_argument("--umbral", type=int, default=90, help="%% desde el que la RAM se pinta como aviso")
    p.add_argument("--cierre", type=int, default=92, help="%% desde el que se pinta como crítica")
    p.add_argument("--cada-apps", type=float, default=2.0, help="segundos entre lecturas de las apps")
    p.add_argument("fuente", nargs="+", help="orden que imprime «MB|unidades|nombre» por app (tras --)")
    args = p.parse_args()

    # sin .desktop para el id, el portal de Plasma avisa en cada apertura; no afecta a la ventana
    os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.services.warning=false")
    app = QApplication(sys.argv[:1])
    app.setDesktopFileName(args.clase)
    app.setApplicationName(args.clase)
    ventana = ListaViva(args)
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
