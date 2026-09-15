"""scripts_filesystem_studio/backend/script_hardlinks-creator/lib/logger.py — envoltorio (FS2, 2026-09-07): el logger vive en core/py-common/logger.py."""
from __future__ import annotations

import importlib.util
import pathlib

_p = pathlib.Path(__file__).resolve()
while _p != _p.parent and not (_p / "core" / "py-common" / "logger.py").exists():
    _p = _p.parent
_s = importlib.util.spec_from_file_location("core_logger", _p / "core" / "py-common" / "logger.py")
_core = importlib.util.module_from_spec(_s)
_s.loader.exec_module(_core)

# constantes de color que importan los demás módulos de la suite (se vacían con disable_colors)
_COLORS = {"RESET": "\033[0m", "BOLD": "\033[1m", "GRAY": "\033[90m", "RED": "\033[91m", "GREEN": "\033[92m",
           "YELLOW": "\033[93m", "BLUE": "\033[94m", "CYAN": "\033[96m"}
RESET, BOLD, GRAY, RED, GREEN, YELLOW, BLUE, CYAN = (_COLORS[k] for k in ("RESET", "BOLD", "GRAY", "RED", "GREEN", "YELLOW", "BLUE", "CYAN"))


def disable_colors() -> None:
    import lib.logger as _self
    for key in _COLORS:
        setattr(_self, key, "")


def get_logger(name: str = "hardlinks-creator", verbose: bool = False, log_file: str | None = None):
    colores = {"DEBUG": _COLORS["GRAY"], "INFO": _COLORS["CYAN"], "WARN": _COLORS["YELLOW"], "ERROR": _COLORS["RED"]}
    return _core.configurar(name, verbose, log_file, colores=colores, reset=_COLORS["RESET"])
