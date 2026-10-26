"""script_registro_tiempo/lib/rutina.py — la rutina del autor como tareas del día en Super Productivity.

Super Productivity 18.10 no deja crear tareas recurrentes ni por la API REST ni desde un plugin (las acciones que un
plugin puede despachar son de interfaz). Por eso la rutina vive en `registro-tiempo.yml` (`rutina:`, bloques con días,
hora y duración) y esta orden crea cada día sus tareas, con hora, proyecto, etiquetas y estimación. No repite: lo que
ya creó para un día queda anotado en el estado y no se vuelve a crear aunque el autor lo borre.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from lib import plan

DIAS = ("lun", "mar", "mie", "jue", "vie", "sab", "dom")
ALIAS = {"mié": "mie", "sáb": "sab", "laborables": "lun mar mie jue vie", "fin_de_semana": "sab dom",
         "todos": "lun mar mie jue vie sab dom"}


def _dias(valor) -> set[str]:
    nombres: set[str] = set()
    for v in ([valor] if isinstance(valor, str) else valor or []):
        nombres.update(ALIAS.get(v, v).split())
    return nombres


def _hora(valor) -> str:
    """«06:30». PyYAML lee 06:30 sin comillas como sexagesimal (390): se acepta y se convierte."""
    if isinstance(valor, int):
        return f"{valor // 60:02d}:{valor % 60:02d}"
    return str(valor or "").strip().zfill(5) if valor else ""


def bloques(rutina: list[dict], dia: date) -> list[plan.Tarea]:
    """Las tareas de un día, en orden de hora."""
    clave = DIAS[dia.weekday()]
    tareas = []
    for b in sorted(rutina or [], key=lambda b: _hora(b.get("hora"))):
        if clave not in _dias(b.get("dias", "todos")):
            continue
        t = plan.Tarea(titulo=b["titulo"], proyecto=b.get("proyecto", ""), etiquetas=list(b.get("etiquetas", [])),
                       estimado_ms=int(b.get("min", 0)) * 60000, dia=dia.isoformat(), hora=_hora(b.get("hora")))
        t.subtareas = [plan.Tarea(titulo=s) for s in b.get("subtareas", [])]
        tareas.append(t)
    return tareas


def ya_paso(t: plan.Tarea, ahora: datetime) -> bool:
    """Un bloque de hoy cuyo final ya pasó no se crea: llenaría el día de vencidas."""
    if not t.hora or t.dia != ahora.date().isoformat():
        return False
    fin = datetime.fromisoformat(f"{t.dia}T{t.hora}") + timedelta(milliseconds=t.estimado_ms)
    return fin < ahora


def clave(t: plan.Tarea) -> str:
    return f"{t.dia}|{t.hora}|{t.titulo}"


def creadas(ruta: Path) -> set[str]:
    try:
        return set(json.loads(ruta.read_text(encoding="utf-8")).get("creadas", []))
    except (OSError, ValueError):
        return set()


def guardar(ruta: Path, claves: set[str], hoy: date) -> None:
    """Conserva solo las últimas cinco semanas: lo anterior ya no puede volver a crearse."""
    limite = (hoy - timedelta(days=35)).isoformat()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"creadas": sorted(c for c in claves if c[:10] >= limite)}, ensure_ascii=False, indent=1)
                    + "\n", encoding="utf-8")
