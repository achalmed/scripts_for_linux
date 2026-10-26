"""script_registro_tiempo/lib/registro.py — el historial por mes, la instantánea de Zotero y el archivo para SP.

Historial: `<TASKS_DIR>/registro/datos/AAAA-MM.json`, `{"version": 1, "dias": {dia: registro}}`; vive en el vault
para que el espejo diario lo respalde (KOReader, ActivityWatch y SP se recalculan de su fuente; Zotero no, porque su
fuente es un acumulado: lo que se perdiera de él no vuelve). Cada pasada reescribe los días recalculados y conserva
los demás. `para-sp.json` (estado, fuera de ~/Documents) se deriva del historial y lo lee el plugin.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import config

VERSION = 1


def _archivo_mes(carpeta: Path, dia: str) -> Path:
    return carpeta / f"{dia[:7]}.json"


def cargar_mes(carpeta: Path, dia: str) -> dict:
    try:
        datos = json.loads(_archivo_mes(carpeta, dia).read_text(encoding="utf-8"))
        return datos if isinstance(datos.get("dias"), dict) else {"version": VERSION, "dias": {}}
    except (OSError, ValueError):
        return {"version": VERSION, "dias": {}}


def fusionar(carpeta: Path, nuevos: dict[str, dict]) -> dict[Path, dict]:
    """{archivo_mes: contenido} con los días nuevos encima de los guardados (sin escribir todavía)."""
    meses: dict[Path, dict] = {}
    for dia, registro in sorted(nuevos.items()):
        ruta = _archivo_mes(carpeta, dia)
        if ruta not in meses:
            meses[ruta] = cargar_mes(carpeta, dia)
        meses[ruta]["dias"][dia] = registro
    return meses


def identidad(ruta: Path, que: str) -> str:
    """La clave `_` que la normativa 1.1 pide a todo JSON propio del vault (ruta relativa a ~/Documents y qué es)."""
    partes = ruta.parts
    relativa = "/".join(partes[partes.index("tareas"):]) if "tareas" in partes else ruta.name
    return f"{relativa} — {que}; GENERADO por scripts-linux/script_registro_tiempo; no editar"


def escribir_json(ruta: Path, datos: dict, que: str = "") -> None:
    if que:
        datos = {"_": identidad(ruta, que), **{k: v for k, v in datos.items() if k != "_"}}
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    temporal.write_text(json.dumps(datos, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    temporal.replace(ruta)   # atómico: un corte a media escritura no deja el historial a medias


def historial(carpeta: Path, dias: int, hoy: date) -> dict[str, dict]:
    """Los últimos `dias` días del historial guardado, del más viejo al de hoy."""
    resultado: dict[str, dict] = {}
    for i in range(dias - 1, -1, -1):
        dia = (hoy - timedelta(days=i)).isoformat()
        registro = cargar_mes(carpeta, dia)["dias"].get(dia)
        if registro:
            resultado[dia] = registro
    return resultado


def para_sp(hist: dict[str, dict], usuario: dict) -> dict:
    """Las tareas del proyecto «Registro automático» con su tiempo por día (ms), según `a_sp` del usuario."""
    tareas: dict[str, dict[str, int]] = {}

    def sumar(titulo: str, dia: str, minutos: float) -> None:
        if titulo and minutos >= config.MINIMO_MIN:
            tareas.setdefault(titulo, {})[dia] = tareas.get(titulo, {}).get(dia, 0) + int(minutos * 60000)

    fuentes = usuario.get("fuentes_a_sp", {})
    categorias = usuario.get("categorias", {})
    for dia, reg in hist.items():
        sumar(fuentes.get("koreader", ""), dia, reg.get("koreader", {}).get("total_min", 0))
        sumar(fuentes.get("zotero", ""), dia, reg.get("zotero", {}).get("total_min", 0))
        for cat, minutos in reg.get("aw", {}).get("categorias", {}).items():
            regla = categorias.get(cat, {})
            if regla.get("a_sp"):
                sumar(regla.get("tarea_sp") or cat, dia, minutos)
    estructura = usuario.get("estructura_sp", {})
    huella = hashlib.sha1(json.dumps(estructura, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    return {"version": VERSION, "generado": datetime.now().astimezone().isoformat(timespec="seconds"),
            "proyecto": config.PROYECTO_SP, "tareas": tareas, "estructura": estructura,
            # el plugin aplica sola una estructura con `aplicar: true`, una vez por huella (si cambia, otra vez)
            "estructura_id": huella, "aplicar_estructura": bool(estructura.get("aplicar"))}
