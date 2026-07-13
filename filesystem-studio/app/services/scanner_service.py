"""
services/scanner_service.py — Recorrido recursivo único del filesystem.

Migración a Python del escaneo de script_count_files_by_extension
(lib/scanner.sh): una sola pasada, agrupación por extensión con conteo
y bytes, y la misma regla de dotfiles (".bashrc" cuenta como
"sin_extension"). Añade lo que la GUI necesita y el Bash no daba:
datos estructurados, progreso y cancelación.
"""

import fnmatch
import os
from dataclasses import dataclass, field

from app.workers.function_worker import OperationCancelled

NO_EXTENSION_LABEL = "sin_extension"
_PROGRESS_EVERY = 200  # emitir progreso cada N archivos


@dataclass
class ExtensionEntry:
    extension: str
    count: int = 0
    size: int = 0


@dataclass
class ScanResult:
    directory: str
    total_files: int = 0
    total_dirs: int = 0
    total_size: int = 0
    extensions: dict[str, ExtensionEntry] = field(default_factory=dict)

    def sorted_entries(self) -> list[ExtensionEntry]:
        return sorted(self.extensions.values(),
                      key=lambda e: (-e.count, e.extension))


def extract_extension(filename: str) -> str:
    """Regla portada de lib/scanner.sh: minúsculas; dotfiles y archivos
    sin punto se agrupan bajo NO_EXTENSION_LABEL."""
    name = filename.lower()
    base = name[1:] if name.startswith(".") else name
    if "." not in base:
        return NO_EXTENSION_LABEL
    return name.rsplit(".", 1)[-1]


def _is_excluded_dir(name: str, exclude_dirs: list[str]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in exclude_dirs)


def scan_extensions(directory: str,
                    exclude_dirs: list[str] | None = None,
                    progress_cb=None, cancel_cb=None,
                    message_cb=None) -> ScanResult:
    """Escanea `directory` y agrupa archivos por extensión.

    exclude_dirs: nombres/globs de carpetas a podar (como `tree -I`).
    """
    exclude_dirs = exclude_dirs or []
    result = ScanResult(directory=directory)

    for root, dirs, files in os.walk(directory, topdown=True, onerror=None):
        if cancel_cb and cancel_cb():
            raise OperationCancelled()

        dirs[:] = [d for d in dirs if not _is_excluded_dir(d, exclude_dirs)]
        result.total_dirs += len(dirs)

        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                size = os.lstat(filepath).st_size
            except OSError:
                continue

            ext = extract_extension(filename)
            entry = result.extensions.setdefault(ext, ExtensionEntry(ext))
            entry.count += 1
            entry.size += size
            result.total_files += 1
            result.total_size += size

            if progress_cb and result.total_files % _PROGRESS_EVERY == 0:
                progress_cb(-1, f"{result.total_files} archivos — {root}")

    if progress_cb:
        progress_cb(100, f"{result.total_files} archivos analizados")
    return result
