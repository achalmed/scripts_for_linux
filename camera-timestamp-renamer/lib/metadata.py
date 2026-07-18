"""Escribe la fecha de captura en los metadatos, derivada del nombre del archivo.

Usa exiftool. En fotos escribe las fechas EXIF (DateTimeOriginal, CreateDate,
ModifyDate); en videos, las fechas QuickTime. Así apps como digiKam agrupan por
la fecha real de captura en vez de por una fecha del sistema de archivos.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from config import Settings

# Solo se tocan archivos cuyo nombre empieza por AAAAMMDD_HHMMSS.
_NAME_CONDITION = r"$filename =~ /^\d{8}_\d{6}/"
_SUMMARY = re.compile(r"\d+ (?:image|video)? ?files? (?:updated|unchanged)")


def _tag_assignments(tags: tuple, expr: str) -> list[str]:
    """Construye los argumentos '-Tag<EXPRESIÓN' para cada etiqueta de fecha."""
    return [f"-{tag}<{expr}" for tag in tags]


def _ext_flags(extensions: tuple) -> list[str]:
    """Traduce las extensiones a flags '-ext EXT' de exiftool."""
    flags: list[str] = []
    for extension in extensions:
        flags += ["-ext", extension.lstrip(".")]
    return flags


def _run(folder: Path, tags: tuple, extensions: tuple, settings: Settings,
         extra: list[str] | None = None) -> subprocess.CompletedProcess:
    """Ejecuta exiftool sobre la carpeta (no recursivo) con las etiquetas dadas."""
    command = [settings.exiftool_binary, "-overwrite_original",
               "-if", _NAME_CONDITION]
    command += extra or []
    command += _ext_flags(extensions)
    command += _tag_assignments(tags, settings.filename_date_expr)
    command.append(str(folder))
    return subprocess.run(command, capture_output=True, text=True, check=False)


def embed_image_dates(folder: Path, settings: Settings
                      ) -> subprocess.CompletedProcess:
    """Escribe las fechas EXIF de las fotos desde su nombre."""
    return _run(folder, settings.image_date_tags, settings.image_extensions, settings)


def embed_video_dates(folder: Path, settings: Settings
                      ) -> subprocess.CompletedProcess:
    """Escribe las fechas QuickTime de los videos desde su nombre.

    QuickTimeUTC=0 guarda la hora local tal cual (sin conversión a UTC).
    """
    return _run(folder, settings.video_date_tags, settings.video_extensions,
                settings, extra=["-api", "QuickTimeUTC=0"])


def embed_file_modify_date(folder: Path, settings: Settings, extensions: tuple
                           ) -> subprocess.CompletedProcess:
    """Fija FileModifyDate (fecha del sistema) desde el nombre.

    Es una operación de sistema de archivos: funciona en cualquier formato,
    incluso los que no admiten metadatos embebidos (p.ej. M2TS).
    """
    return _run(folder, ("FileModifyDate",), extensions, settings)


def summarize(result: subprocess.CompletedProcess) -> str:
    """Extrae la línea de resumen de exiftool ('N files updated')."""
    text = f"{result.stdout}\n{result.stderr}"
    matches = _SUMMARY.findall(text)
    if matches:
        return "; ".join(matches)
    return "sin cambios"
