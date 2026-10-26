"""script_registro_tiempo/lib/entorno.py — rutas del ecosistema por core/env.py y las propias de la suite."""
from __future__ import annotations

import importlib.util
import os
import pathlib

import config

_d = pathlib.Path(__file__).resolve()
while _d != _d.parent and not (_d / "core" / "env.py").exists():
    _d = _d.parent
_s = importlib.util.spec_from_file_location("core_env", _d / "core" / "env.py")
env = importlib.util.module_from_spec(_s)
_s.loader.exec_module(env)


def raiz() -> pathlib.Path:
    return pathlib.Path(env.DOCS_ROOT)


def tareas() -> pathlib.Path:
    return pathlib.Path(env.TASKS_DIR)


def archivo_usuario() -> pathlib.Path:
    return tareas() / config.ARCHIVO_USUARIO


def carpeta_registro() -> pathlib.Path:
    return tareas() / config.CARPETA_REGISTRO


def carpeta_datos() -> pathlib.Path:
    return tareas() / config.CARPETA_DATOS


def sync_sp() -> pathlib.Path:
    return tareas() / config.SYNC_SP


def koreader_stats() -> pathlib.Path:
    return pathlib.Path(env.KOREADER_STATS)


def zotero_db() -> pathlib.Path:
    return pathlib.Path(env.ZOTERO_DB)


def carpeta_estado() -> pathlib.Path:
    base = os.environ.get("XDG_STATE_HOME") or str(pathlib.Path.home() / ".local" / "state")
    return pathlib.Path(base) / config.CARPETA_ESTADO
