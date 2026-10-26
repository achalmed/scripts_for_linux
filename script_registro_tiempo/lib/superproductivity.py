"""script_registro_tiempo/lib/superproductivity.py — lo que Super Productivity registró, leído de su archivo de sync.

Solo lectura. La sincronización por archivo local (Ajustes → Sync) escribe `sync-data.json`: en la versión 18 es
`pf_<banderas>__<carga>`, donde la bandera C indica gzip + base64 y la E, cifrado (que aquí no se lee); sin prefijo
es JSON plano. El estado es NgRx (`task.entities`, `project.entities`, `tag.entities`) y el archivo reciente de
tareas va en `archiveYoung`/`archiveOld`. Se cuentan solo tareas hoja (sin subtareas) para no sumar dos veces el
tiempo de una madre y sus hijas, y se excluye el proyecto donde el plugin escribe el tiempo de fuera de SP.
"""
from __future__ import annotations

import base64
import gzip
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

RE_PREFIJO = re.compile(r"^pf_([A-Z0-9]*)__")


class Cifrado(ValueError):
    """El archivo de sync está cifrado: no se puede leer sin la clave."""


def decodificar(texto: str) -> dict:
    m = RE_PREFIJO.match(texto)
    if not m:
        return json.loads(texto)
    banderas, carga = m.group(1), texto[m.end():]
    if "E" in banderas:
        raise Cifrado("sync-data.json está cifrado")
    if "C" in banderas:
        carga = gzip.decompress(base64.b64decode(carga)).decode("utf-8")
    return json.loads(carga)


def _tareas(datos: dict) -> list[dict]:
    estado = datos.get("state", datos)
    tareas = list(estado.get("task", {}).get("entities", {}).values())
    for clave in ("archiveYoung", "archiveOld"):
        archivo = datos.get(clave) or estado.get(clave) or {}
        tareas += list(archivo.get("task", {}).get("entities", {}).values())
    return tareas


def leer(ruta: Path, desde: str, excluir_proyecto: str) -> dict[str, dict]:
    """{dia: {"proyectos": {p: min}, "etiquetas": {t: min}, "hechas": [titulos], "total_min": n}}."""
    if not ruta.is_file():
        return {}
    datos = decodificar(ruta.read_text(encoding="utf-8"))
    estado = datos.get("state", datos)
    proyectos = {k: v.get("title", k) for k, v in estado.get("project", {}).get("entities", {}).items()}
    etiquetas = {k: v.get("title", k) for k, v in estado.get("tag", {}).get("entities", {}).items()}
    dias: dict[str, dict] = defaultdict(lambda: {"proyectos": {}, "etiquetas": {}, "hechas": [], "total_min": 0.0})
    vistos: set[str] = set()
    for t in _tareas(datos):
        if t.get("id") in vistos:
            continue
        vistos.add(t.get("id"))
        proyecto = proyectos.get(t.get("projectId"), "Sin proyecto")
        if proyecto == excluir_proyecto:
            continue
        if t.get("isDone") and t.get("doneOn"):
            dia_hecha = datetime.fromtimestamp(t["doneOn"] / 1000).date().isoformat()
            if dia_hecha >= desde:
                dias[dia_hecha]["hechas"].append(t.get("title", ""))
        if t.get("subTaskIds"):
            continue
        for dia, ms in (t.get("timeSpentOnDay") or {}).items():
            if dia < desde or not ms:
                continue
            minutos = ms / 60000
            d = dias[dia]
            d["proyectos"][proyecto] = round(d["proyectos"].get(proyecto, 0) + minutos, 1)
            for tid in t.get("tagIds", []):
                if tid == "TODAY":   # etiqueta del sistema («Hoy»), no una categoría del autor
                    continue
                nombre = etiquetas.get(tid, tid)
                d["etiquetas"][nombre] = round(d["etiquetas"].get(nombre, 0) + minutos, 1)
            d["total_min"] = round(d["total_min"] + minutos, 1)
    return dict(dias)
