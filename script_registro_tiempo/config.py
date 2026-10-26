"""script_registro_tiempo/config.py — valores editables del registro de tiempo.

Lo que cambia por persona (categorías, metas, estructura propuesta para Super Productivity) no vive aquí:
vive en el archivo del usuario `<TASKS_DIR>/registro-tiempo.yml`, que se respalda con el vault.
"""
from __future__ import annotations

APP_NAME = "registro-tiempo"
VERSION = "1.0.0"

# --- Códigos de salida (126/127 los reserva el shell) ---
EXIT_OK = 0
EXIT_GENERAL = 1
EXIT_USO = 2
EXIT_NO_ENCONTRADO = 3

# --- Dónde vive cada cosa, relativo a TASKS_DIR (core/env) ---
ARCHIVO_USUARIO = "registro-tiempo.yml"        # categorías, metas y estructura propuesta (lo edita el autor)
CARPETA_REGISTRO = "registro"                  # informes semanales generados (Markdown)
CARPETA_DATOS = "registro/datos"               # historial por mes (JSON) e instantánea de Zotero
INSTANTANEA_ZOTERO = "zotero-instantanea.json"
SYNC_SP = "sync-data.json"                     # la sincronización por archivo local de Super Productivity

# --- Estado derivado, fuera de ~/Documents: se regenera del historial en cada pasada ---
CARPETA_ESTADO = "registro-tiempo"             # bajo $XDG_STATE_HOME (por defecto ~/.local/state)
ARCHIVO_PARA_SP = "para-sp.json"               # lo que lee el plugin de Super Productivity
NOMBRE_ZIP_PLUGIN = "registro-tiempo-sp.zip"

# --- Recolección ---
DIAS_POR_DEFECTO = 7                           # días hacia atrás que se recalculan en cada pasada
DIAS_PARA_SP = 35                              # días que se ofrecen al plugin (cubre un mes de revisión)
AW_URL = "http://localhost:5600/api/0"         # servidor de ActivityWatch (aw-server o awatcher)
AW_TIMEOUT_S = 5
MINIMO_MIN = 1                                 # por debajo de un minuto, una entrada no se lista en el informe
TOP_INFORME = 8                                # filas por tabla en el informe semanal

# --- Super Productivity ---
PROYECTO_SP = "Registro automático"            # proyecto donde el plugin escribe el tiempo de fuera de SP

USE_COLOR = None                               # None = automático según la terminal (core/py-common/logger.py)
