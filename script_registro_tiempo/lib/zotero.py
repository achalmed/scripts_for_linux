"""script_registro_tiempo/lib/zotero.py — tiempo de lectura en Zotero por diferencia entre instantáneas.

El plugin Ethereal Style guarda, por ítem, el tiempo acumulado por página en una nota con
`{"readingTime":{"page":N,"data":{"<página>":segundos}}}` (formato verificado en
`scripts-biblioteca/lectura/lib/sync_zotero_lectura.py`, que lo lleva a Calibre). Es un acumulado sin fechas: el
tiempo de un día es lo que creció desde la instantánea anterior, y se atribuye al día en que se observa. Por eso
la primera pasada solo fija la línea base, y conviene que el timer corra varias veces al día.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

RE_CLAVE = re.compile(r'znv1"[^>]*>\s*([A-Z0-9]{8})')

CONSULTA_NOTAS = (
    "SELECT n.note FROM itemNotes n JOIN items i ON i.itemID = n.itemID "
    "WHERE n.note LIKE '%\"readingTime\"%' AND i.itemID NOT IN (SELECT itemID FROM deletedItems)"
)
CONSULTA_TITULO = (
    "SELECT v.value FROM items i JOIN itemData d ON d.itemID = i.itemID "
    "JOIN fields f ON f.fieldID = d.fieldID JOIN itemDataValues v ON v.valueID = d.valueID "
    "WHERE i.key = ? AND f.fieldName = 'title'"
)


def acumulados(ruta: Path) -> dict[str, dict]:
    """{clave_item: {"seg": total, "titulo": t}} con el máximo por ítem si hay varias notas."""
    if not ruta.is_file():
        return {}
    con = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)
    try:
        resultado: dict[str, dict] = {}
        for (nota,) in con.execute(CONSULTA_NOTAS):
            m = RE_CLAVE.search(nota or "")
            ini, fin = (nota or "").find("{"), (nota or "").rfind("}")
            if not m or ini < 0 or fin <= ini:
                continue
            try:
                datos = json.loads(nota[ini:fin + 1]).get("readingTime", {}).get("data", {})
                seg = sum(int(v) for v in datos.values())
            except (ValueError, TypeError, AttributeError):
                continue
            clave = m.group(1)
            if seg > resultado.get(clave, {}).get("seg", -1):
                fila = con.execute(CONSULTA_TITULO, (clave,)).fetchone()
                resultado[clave] = {"seg": seg, "titulo": fila[0] if fila else clave}
        return resultado
    finally:
        con.close()


def diferencia(anterior: dict, actual: dict) -> dict[str, float]:
    """{titulo: minutos} que crecieron desde la instantánea anterior (un ítem nuevo cuenta entero solo si ya
    había línea base: sin ella, la primera pasada no inventa tiempo)."""
    if not anterior:
        return {}
    previos = anterior.get("items", {})
    crecido: dict[str, float] = {}
    for clave, dato in actual.items():
        delta = dato["seg"] - previos.get(clave, {}).get("seg", 0)
        if delta > 0:
            crecido[dato["titulo"]] = round(crecido.get(dato["titulo"], 0) + delta / 60, 1)
    return crecido


def leer_instantanea(ruta: Path) -> dict:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
