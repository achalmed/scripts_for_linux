"""
services/folder_service.py — Creación masiva de carpetas.

Port fiel de script_create_folders_batch: conserva el saneo de
lib/reader.sh (\\r de Windows, trim), las reglas de seguridad de
lib/validator.sh (rechazar rutas absolutas y componentes "..") y los
contadores de lib/creator.sh (creada / existía / rechazada / error).

Añade lo que la GUI exige: importación desde TXT, CSV y Markdown,
plan previo estructurado (vista previa), y diario de deshacer.
"""

import csv
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from app.workers.function_worker import OperationCancelled

# Estados de cada carpeta del plan / resultado
ST_OK = "ok"            # se crearía / se creó
ST_EXISTS = "existe"
ST_REJECTED = "rechazada"
ST_FAILED = "error"

_MD_LIST_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+)")


@dataclass
class FolderItem:
    name: str
    status: str
    note: str = ""


@dataclass
class FolderResult:
    base_dir: str
    dry_run: bool
    items: list[FolderItem] = field(default_factory=list)
    created_paths: list[str] = field(default_factory=list)

    def count(self, status: str) -> int:
        return sum(1 for item in self.items if item.status == status)


# ------------------------------------------------------------- saneo/reglas

def sanitize_name(raw: str) -> str:
    """Port de sanitize_folder_name(): quita \\r y espacios extremos."""
    return raw.replace("\r", "").strip()


def is_safe_name(name: str) -> bool:
    """Port de is_safe_folder_name(): nunca escribir fuera del directorio
    base (sin rutas absolutas ni componentes '..')."""
    if name.startswith("/"):
        return False
    parts = name.split("/")
    return ".." not in parts


# ------------------------------------------------------------- importación

def parse_lines(text: str) -> list[str]:
    """Texto plano/manual: una carpeta por línea; ignora vacías y '#'."""
    names = []
    for line in text.splitlines():
        name = sanitize_name(line)
        if not name or name.startswith("#"):
            continue
        names.append(name)
    return names


def read_names_from_file(path: str) -> list[str]:
    """Importa nombres desde TXT, CSV (primera columna) o Markdown
    (elementos de lista; se ignoran encabezados y prosa)."""
    suffix = Path(path).suffix.lower()
    text = Path(path).read_text(encoding="utf-8", errors="replace")

    if suffix == ".csv":
        names = []
        for row in csv.reader(text.splitlines()):
            if not row:
                continue
            name = sanitize_name(row[0])
            if name and not name.startswith("#"):
                names.append(name)
        return names

    if suffix in (".md", ".markdown"):
        names = []
        for line in text.splitlines():
            if _MD_LIST_RE.match(line):
                name = sanitize_name(_MD_LIST_RE.sub("", line, count=1))
                if name:
                    names.append(name.strip("`"))
        return names

    return parse_lines(text)


# ------------------------------------------------------------ plan/creación

def plan_folders(base_dir: str, names: list[str]) -> list[FolderItem]:
    """Vista previa sin tocar el disco: clasifica cada nombre."""
    items = []
    for name in names:
        if not is_safe_name(name):
            items.append(FolderItem(name, ST_REJECTED, "ruta insegura"))
        elif os.path.isdir(os.path.join(base_dir, name)):
            items.append(FolderItem(name, ST_EXISTS))
        else:
            items.append(FolderItem(name, ST_OK))
    return items


def create_folders(base_dir: str, names: list[str], dry_run: bool = False,
                   progress_cb=None, cancel_cb=None,
                   message_cb=None) -> FolderResult:
    """Crea las carpetas (o simula). Registra las rutas realmente creadas
    para poder deshacer la operación."""
    result = FolderResult(base_dir=base_dir, dry_run=dry_run)
    total = len(names) or 1

    for index, name in enumerate(names, start=1):
        if cancel_cb and cancel_cb():
            raise OperationCancelled()
        if progress_cb:
            progress_cb(int(index * 100 / total), name)

        if not is_safe_name(name):
            result.items.append(FolderItem(name, ST_REJECTED, "ruta insegura"))
            if message_cb:
                message_cb("warn", f"Rechazada (ruta insegura): {name}")
            continue

        full_path = os.path.join(base_dir, name)
        if os.path.isdir(full_path):
            result.items.append(FolderItem(name, ST_EXISTS))
            continue

        if dry_run:
            result.items.append(FolderItem(name, ST_OK, "simulación"))
            if message_cb:
                message_cb("info", f"[SIMULACIÓN] Se crearía: {name}")
            continue

        try:
            # Registrar los intermedios inexistentes para el deshacer
            missing = _missing_components(base_dir, name)
            os.makedirs(full_path)
            result.items.append(FolderItem(name, ST_OK))
            result.created_paths.extend(missing)
            if message_cb:
                message_cb("ok", f"Creada: {name}")
        except OSError as exc:
            result.items.append(FolderItem(name, ST_FAILED, str(exc)))
            if message_cb:
                message_cb("error", f"Error al crear '{name}': {exc}")

    return result


def _missing_components(base_dir: str, name: str) -> list[str]:
    """Rutas intermedias que aún no existen, de la más corta a la más larga."""
    missing = []
    current = base_dir
    for part in name.split("/"):
        current = os.path.join(current, part)
        if not os.path.isdir(current):
            missing.append(current)
    return missing


def undo_created(paths: list[str],
                 progress_cb=None, cancel_cb=None,
                 message_cb=None) -> tuple[int, list[str]]:
    """Deshace una creación: elimina (rmdir) las carpetas registradas,
    de la más profunda a la más superficial, SOLO si están vacías.

    Devuelve (eliminadas, no_eliminables)."""
    removed = 0
    kept: list[str] = []
    for path in sorted(paths, key=len, reverse=True):
        if cancel_cb and cancel_cb():
            raise OperationCancelled()
        try:
            os.rmdir(path)
            removed += 1
            if message_cb:
                message_cb("ok", f"Eliminada: {path}")
        except OSError:
            kept.append(path)
            if message_cb:
                message_cb("warn", f"No se eliminó (no vacía o inexistente): {path}")
    return removed, kept
