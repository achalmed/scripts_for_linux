"""Renombrados que sí hace el script: extensiones equivocadas y nombres
decodificables.

Dos correcciones en un solo pase:
1. Extensión que miente sobre el formato real (p.ej. WebP guardado como .jpg):
   exiftool se niega a escribir metadatos ahí, así que se corrige la extensión.
2. Nombres con fecha decodificable pero en otro formato, que se llevan al
   estándar de la colección: fb_<epoch-ms> -> AAAAMMDD_HHMMSS,
   IMG/VID-AAAAMMDD-WAnnnn -> AAAAMMDD_wannnn, IMG_/Screenshot_/pixiz/chatgpt
   -> AAAAMMDD_HHMMSS.
3. Renombrado desde el EXIF (el EXIF manda cuando es ANTERIOR al nombre o
   cuando el nombre no trae fecha): archivos sin fecha en el nombre pero con
   fecha de captura en los metadatos, y archivos estándar cuyo EXIF es
   anterior a la fecha del nombre (el nombre vino de una exportación, p.ej.
   iPhone '_0500'; la captura real es la del EXIF).

Los cambios de mayúsculas/minúsculas NO se tocan (eso lo hace el usuario con
otra herramienta). Cada renombrado queda registrado en _fix_log.csv.
"""
from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path

from config import Settings
from lib import audit

# Patrones (ver lib/audit._PATTERNS) cuyo nombre se normaliza al estándar.
_RENAMEABLE = {"facebook-epoch", "whatsapp-original", "IMG_", "captura",
               "pixiz", "chatgpt"}
_WA_ORIGINAL = re.compile(r"^(?:IMG|VID)-(\d{8})-WA(\d+)", re.I)


def _decoded_name(name: str) -> str | None:
    """Nombre estándar derivado del actual, o None si no hay que renombrar."""
    pattern, stamp, _precision = audit.parse_name_date(name)
    if pattern not in _RENAMEABLE or stamp is None:
        return None
    extension = Path(name).suffix
    if pattern == "whatsapp-original":
        match = _WA_ORIGINAL.match(name)
        return f"{match.group(1)}_wa{match.group(2)}{extension}"
    return f"{stamp:%Y%m%d_%H%M%S}{extension}"


def _exif_based_name(name: str, meta: dict, settings: Settings) -> str | None:
    """Nombre estándar desde el EXIF cuando el EXIF manda, o None.

    El EXIF manda en dos casos: el nombre no trae fecha alguna, o el nombre
    es estándar pero el EXIF es ANTERIOR (el nombre vino de una exportación;
    una captura no puede ser posterior al nombre, ver metadata.py para el
    caso inverso). Solo con `rename_from_metadata` activado.
    """
    if not settings.rename_from_metadata:
        return None
    meta_dt = audit.primary_meta_date(meta)
    if meta_dt is None:
        return None
    pattern, name_dt, precision = audit.parse_name_date(name)
    exif_wins = (name_dt is None
                 or (pattern == "estándar" and precision == "segundos"
                     and (name_dt - meta_dt).total_seconds()
                     > settings.audit_tolerance_seconds))
    if not exif_wins:
        return None
    return f"{meta_dt:%Y%m%d_%H%M%S}{Path(name).suffix}"


def build_fixes(folder: Path, settings: Settings) -> list[tuple[str, str]]:
    """Pares (nombre_actual, nombre_corregido) de toda la carpeta."""
    known = (set(settings.image_extensions) | set(settings.video_extensions)
             | set(settings.extra_audit_extensions))
    fixes = []
    for meta in audit.read_metadata(folder, settings):
        name = meta.get("FileName", "")
        if Path(name).suffix.lower() not in known:
            continue
        target = (_decoded_name(name) or _exif_based_name(name, meta, settings)
                  or name)
        fixed_ext = audit.correct_extension(target, meta.get("FileType", ""))
        if fixed_ext:
            target = Path(target).stem + fixed_ext
        if target != name:
            fixes.append((name, target))
    return sorted(fixes)


def apply_fixes(folder: Path, fixes: list[tuple[str, str]], settings: Settings,
                execute: bool) -> list[tuple[str, str]]:
    """Aplica los renombrados con sufijo _N ante colisiones; devuelve los pares.

    Con execute=False solo calcula (simulación). Los aplicados se anotan en
    _fix_log.csv (se añade al final, nunca se sobreescribe).
    """
    taken = {entry.name for entry in folder.iterdir()}
    taken -= {old for old, _new in fixes}
    done = []
    for old, new in fixes:
        candidate, counter = new, 0
        while candidate in taken:
            counter += 1
            candidate = f"{Path(new).stem}_{counter}{Path(new).suffix}"
        taken.add(candidate)
        if execute:
            (folder / old).rename(folder / candidate)
        done.append((old, candidate))
    if execute and done:
        _append_log(folder / settings.fix_log_name, done)
    return done


def _append_log(destination: Path, pairs: list[tuple[str, str]]) -> None:
    """Registra los renombrados aplicados (para poder rastrear/revertir)."""
    new_file = not destination.exists()
    with destination.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(["fecha", "anterior", "nuevo"])
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for old, new in pairs:
            writer.writerow([stamp, old, new])
