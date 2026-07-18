"""Auditoría de fechas: compara el nombre de cada archivo con sus metadatos.

Solo lectura: no modifica ninguna imagen ni los archivos de digiKam. Para cada
archivo se extrae la fecha codificada en el nombre (patrones conocidos: cámara,
WhatsApp, IMG_, capturas, Facebook) y se contrasta con DateTimeOriginal /
CreateDate leídos en un solo pase de exiftool. El resultado es un CSV por
archivo y un resumen por estado.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import Settings
from lib.errors import DependencyError

# Patrones de nombre conocidos, en orden de prioridad. Cada entrada define la
# etiqueta del patrón, la regex que captura la fecha y la precisión con la que
# tiene sentido comparar (WhatsApp solo codifica el día, no la hora).
_PATTERNS: tuple = (
    ("estándar", re.compile(r"^(\d{8})_(\d{6})"), "segundos"),
    ("whatsapp", re.compile(r"^(\d{8})_wa\d+", re.I), "día"),
    ("IMG_", re.compile(r"^IMG_(\d{8})_(\d{6})", re.I), "segundos"),
    ("whatsapp-original", re.compile(r"^IMG-(\d{8})-WA\d+", re.I), "día"),
    ("captura", re.compile(r"^Screenshot_(\d{8})-(\d{6})", re.I), "segundos"),
    ("facebook-epoch", re.compile(r"^fb_(\d{13})(?:\D|$)"), "segundos"),
    ("fecha-parcial", re.compile(r"^(\d{8})[_-]"), "día"),
)
# Descargas de Facebook/Instagram: '<id>_<id>_<id>_n.jpg' (sin fecha alguna).
_FACEBOOK_NAME = re.compile(r"_n\.(jpe?g|png|webp)$", re.I)


@dataclass
class AuditRow:
    """Resultado de auditar un archivo (una fila del CSV)."""

    name: str
    pattern: str          # patrón de nombre detectado
    name_date: str        # fecha derivada del nombre ('' si no hay)
    meta_date: str        # DateTimeOriginal o CreateDate ('' si no hay)
    file_date: str        # FileModifyDate (referencia, poco confiable)
    status: str           # OK / HORA_DISTINTA / FECHA_DISTINTA / ...
    suggestion: str       # acción recomendada


def parse_name_date(name: str) -> tuple[str, datetime | None, str]:
    """Devuelve (patrón, fecha, precisión) según el nombre del archivo."""
    for label, regex, precision in _PATTERNS:
        match = regex.match(name)
        if not match:
            continue
        try:
            if label == "facebook-epoch":
                return label, datetime.fromtimestamp(int(match.group(1)) / 1000), precision
            digits = "".join(match.groups())
            fmt = "%Y%m%d%H%M%S" if precision == "segundos" else "%Y%m%d"
            return label, datetime.strptime(digits[:14], fmt), precision
        except (ValueError, OSError, OverflowError):
            return label, None, precision
    if _FACEBOOK_NAME.search(name):
        return "facebook", None, "día"
    return "sin-patrón", None, "día"


def _parse_meta(value: str | None) -> datetime | None:
    """Convierte una fecha de exiftool; ignora vacíos y '0000:...'."""
    if not value or value.startswith("0000"):
        return None
    try:
        return datetime.strptime(value.strip()[:19], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def read_metadata(folder: Path, settings: Settings) -> list[dict]:
    """Lee las fechas de todos los archivos de la carpeta en un pase de exiftool."""
    command = [settings.exiftool_binary, "-j", "-q", "-fast2",
               "-d", "%Y-%m-%d %H:%M:%S",
               "-FileName", "-DateTimeOriginal", "-CreateDate", "-FileModifyDate",
               str(folder)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if not result.stdout.strip():
        raise DependencyError(f"exiftool no devolvió datos: {result.stderr.strip()}")
    return json.loads(result.stdout)


def _classify(name: str, meta: dict, expected_year: int | None,
              tolerance: int) -> AuditRow:
    """Compara la fecha del nombre con los metadatos y decide el estado."""
    pattern, name_dt, precision = parse_name_date(name)
    meta_dt = (_parse_meta(meta.get("DateTimeOriginal"))
               or _parse_meta(meta.get("CreateDate")))
    row = AuditRow(name=name, pattern=pattern,
                   name_date=str(name_dt or ""), meta_date=str(meta_dt or ""),
                   file_date=meta.get("FileModifyDate", ""), status="", suggestion="")
    if name_dt is None:
        row.status = "SIN_FECHA_NOMBRE"
        row.suggestion = ("renombrar usando metadatos" if meta_dt
                          else "revisar a mano (sin fecha en nombre ni metadatos)")
    elif meta_dt is None:
        row.status = "SIN_METADATOS"
        row.suggestion = "embed-date (escribir fecha del nombre en EXIF)"
    elif precision == "segundos" and abs((meta_dt - name_dt).total_seconds()) <= tolerance:
        row.status = "OK"
    elif meta_dt.date() == name_dt.date():
        row.status = "OK" if precision == "día" else "HORA_DISTINTA"
        if row.status == "HORA_DISTINTA":
            row.suggestion = "revisar cuál hora es la correcta"
    else:
        row.status = "FECHA_DISTINTA"
        row.suggestion = "revisar cuál fecha es la correcta"
    # El año del nombre manda para detectar archivos en la carpeta equivocada.
    year = name_dt.year if name_dt else (meta_dt.year if meta_dt else None)
    if expected_year and year and year != expected_year:
        row.status = "AÑO_INTRUSO"
        row.suggestion = f"mover a la carpeta {year}"
    return row


def audit_folder(folder: Path, settings: Settings,
                 expected_year: int | None) -> list[AuditRow]:
    """Audita todos los archivos de la carpeta (no recursivo, solo lectura)."""
    known = set(settings.image_extensions) | set(settings.video_extensions) \
        | set(settings.extra_audit_extensions)
    rows = []
    for meta in read_metadata(folder, settings):
        name = meta.get("FileName", "")
        if Path(name).suffix.lower() not in known:
            continue
        rows.append(_classify(name, meta, expected_year,
                              settings.audit_tolerance_seconds))
    return sorted(rows, key=lambda row: (row.status, row.name))


def write_audit_csv(rows: list[AuditRow], destination: Path) -> None:
    """Escribe el detalle por archivo, ordenado por estado."""
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["archivo", "patrón", "fecha_nombre", "fecha_metadatos",
                         "fecha_archivo", "estado", "sugerencia"])
        for row in rows:
            writer.writerow([row.name, row.pattern, row.name_date, row.meta_date,
                             row.file_date, row.status, row.suggestion])


def summarize(rows: list[AuditRow]) -> Counter:
    """Cuenta archivos por estado para el resumen del log."""
    return Counter(row.status for row in rows)
