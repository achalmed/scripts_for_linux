"""script_registro_tiempo/lib/koreader.py — minutos de lectura por día y por libro desde statistics.sqlite3.

KOReader guarda una fila por página leída (`page_stat_data`: libro, inicio en segundos Unix, duración en
segundos). El día es el local de la máquina. Solo lectura (`mode=ro`): seguro con KOReader abierto.
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path

CONSULTA = (
    "SELECT date(p.start_time, 'unixepoch', 'localtime') AS dia, b.title, SUM(p.duration) "
    "FROM page_stat_data p JOIN book b ON b.id = p.id_book "
    "WHERE p.start_time >= strftime('%s', ?, 'utc') "
    "GROUP BY dia, b.title"
)


def leer(ruta: Path, desde: str) -> dict[str, dict]:
    """{dia: {"total_min": n, "libros": {titulo: min}}} desde la fecha `desde` (AAAA-MM-DD, inclusive)."""
    if not ruta.is_file():
        return {}
    con = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
    try:
        filas = con.execute(CONSULTA, (desde,)).fetchall()
    finally:
        con.close()
    dias: dict[str, dict] = defaultdict(lambda: {"total_min": 0.0, "libros": {}})
    for dia, titulo, seg in filas:
        minutos = round((seg or 0) / 60, 1)
        if minutos <= 0:
            continue
        dias[dia]["libros"][titulo or "(sin título)"] = minutos
        dias[dia]["total_min"] = round(dias[dia]["total_min"] + minutos, 1)
    return dict(dias)
